"""Assembly audit for the Ghoul's Grip mechanism.

* ``all_pairs(theta)``: boolean intersection volume of every part pair in the
  assembled scene (including hand-to-hand pairs), split into intended contacts
  and unintended collisions.
* ``play(...)``: free translation/rotation of one part against another before
  the first intersection - used for gear/rack backlash and pin/bore checks.

* ``full_audit()``: the complete montage audit (BOM, non-printed filament
  pins, collisions, pin play, pin insertion sweeps, assembly-step sweeps,
  gear backlash, snap/press-fit strain and lid load path).  Writes
  ``docs/ghouls-grip-montage-audit.md`` and exits non-zero on any FAIL.

Usage::

    python scripts/audit_ghouls_grip_assembly.py            # full audit
    python scripts/audit_ghouls_grip_assembly.py 18 48      # pairs only
"""

from __future__ import annotations

import collections
import functools
import itertools
import math
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import trimesh

import mechanism
import render_ghouls_grip as scene

ROOT = Path(__file__).resolve().parents[1]
PRINT_3MF = ROOT / "models" / "ghouls-grip-print.3mf"
REPORT = ROOT / "docs" / "ghouls-grip-montage-audit.md"

AUDIT_THETAS = (18.0, 25.0, 30.0, 36.0, 48.0, 60.0, 78.0)
COLLISION_LIMIT_MM3 = 0.5
INTENDED_LIMIT_MM3 = 5.0
FILAMENT_R = 1.75 / 2.0
SWEEP_LIMIT_MM3 = 0.05
MIN_RADIAL_PLAY = 0.2       # per side; FDM holes print ~0.1 mm undersize
MIN_AXIAL_PLAY = 0.1        # total
MIN_BACKLASH_MM = 0.1       # per direction at the pitch circle
MAX_SNAP_STRAIN = 0.02      # PLA, few assembly cycles
PLA_DENSITY = 1.24e-3       # g/mm3
PLA_MU = 0.3

# Designed contacts, not collisions: (name prefix a, name prefix b).
INTENDED_CONTACTS: tuple[tuple[str, str], ...] = (
    # Crush-rib press pin: 0.15 mm rib interference in the follower bar.
    ("pivot-pin-follower", "lid-follower-rack"),
)


def volume_intersection(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    overlap = np.minimum(a.bounds[1], b.bounds[1]) - np.maximum(
        a.bounds[0], b.bounds[0])
    if np.any(overlap <= 0.0):
        return 0.0
    hit = trimesh.boolean.intersection([a, b], engine="manifold")
    return 0.0 if hit is None else abs(float(hit.volume))


def _intersection(a, b):
    overlap = np.minimum(a.bounds[1], b.bounds[1]) - np.maximum(
        a.bounds[0], b.bounds[0])
    if np.any(overlap <= 0.0):
        return None
    hit = trimesh.boolean.intersection([a, b], engine="manifold")
    if hit is None or abs(hit.volume) < 1e-6:
        return None
    return hit


def _intended(a: str, b: str) -> bool:
    return any((a.startswith(x) and b.startswith(y))
               or (a.startswith(y) and b.startswith(x))
               for x, y in INTENDED_CONTACTS)


@functools.lru_cache(maxsize=None)
def scene_parts(theta: float) -> dict[str, trimesh.Trimesh]:
    """Assembled scene at ``theta`` (cached - treat the meshes read-only)."""
    return {name: mesh for name, mesh, _ in scene.build_scene_at(theta)}


def all_pairs(theta: float, threshold: float = 0.01) -> list[dict]:
    """Every intersecting pair above ``threshold`` mm3 at scissor angle theta."""
    from concurrent.futures import ThreadPoolExecutor

    parts = scene_parts(theta)
    candidates = [
        (a, b) for a, b in itertools.combinations(parts, 2)
        if np.all(np.minimum(parts[a].bounds[1], parts[b].bounds[1])
                  > np.maximum(parts[a].bounds[0], parts[b].bounds[0]))
    ]

    def _check_pair(pair: tuple[str, str]):
        a, b = pair
        hit = _intersection(parts[a], parts[b])
        if hit is None or abs(hit.volume) < threshold:
            return None
        return {
            "a": a, "b": b, "volume_mm3": abs(float(hit.volume)),
            "bounds": np.round(hit.bounds, 2).tolist(),
            "intended": _intended(a, b),
        }

    with ThreadPoolExecutor() as pool:
        return [res for res in pool.map(_check_pair, candidates) if res is not None]


def play(moving: trimesh.Trimesh, fixed: trimesh.Trimesh,
         transform_for, limit: float, step: float,
         threshold: float = 0.01) -> float:
    """Largest parameter s in [0, limit] with no intersection.

    ``transform_for(s)`` returns the 4x4 transform applied to ``moving``.
    Coarse march, then bisection to ``step / 32``.
    """
    def clear(s: float) -> bool:
        probe = moving.copy()
        probe.apply_transform(transform_for(s))
        return volume_intersection(probe, fixed) < threshold

    if not clear(0.0):
        return 0.0
    s = 0.0
    while s < limit:
        nxt = min(s + step, limit)
        if not clear(nxt):
            lo, hi = s, nxt
            while hi - lo > step / 32.0:
                mid = (lo + hi) / 2.0
                lo, hi = (mid, hi) if clear(mid) else (lo, mid)
            return lo
        s = nxt
    return limit


def translate(direction):
    direction = np.asarray(direction, dtype=float)
    return lambda s: trimesh.transformations.translation_matrix(direction * s)


def rotate(axis, point):
    return lambda s: trimesh.transformations.rotation_matrix(
        np.deg2rad(s), axis, point)


def backlash_report(theta: float) -> dict[str, float]:
    """Free play (both directions) of every gear mesh at ``theta``."""
    parts = scene_parts(theta)
    out = {}
    # Drive rack/pinion: rotate the pinion about the drive axis (world Y).
    for sign, tag in ((1.0, "+"), (-1.0, "-")):
        out[f"pinion-rack{tag}_deg"] = play(
            parts["drive-pinion"], parts["slider"],
            lambda s, g=sign: rotate([0, 1, 0], mechanism.DRIVE_AXIS)(g * s),
            3.0, 0.25)
        out[f"follower-transfer{tag}_mm"] = play(
            parts["lid-follower-rack"], parts["lid-transfer-input"],
            lambda s, g=sign: translate([0, 0, g])(s), 1.5, 0.1)
        out[f"transfer-idler{tag}_deg"] = play(
            parts["lid-transfer-input"], parts["lid-transfer-idler"],
            lambda s, g=sign: rotate(
                [1, 0, 0], [0, mechanism.LID_TRANSFER_Y,
                            mechanism.LID_HINGE_Z])(g * s),
            20.0, 1.0)
        out[f"idler-crank{tag}_deg"] = play(
            parts["lid-transfer-idler"], parts["lid-crank"],
            lambda s, g=sign: rotate(
                [1, 0, 0], [0, mechanism.LID_IDLER_Y,
                            mechanism.LID_HINGE_Z])(g * s),
            20.0, 1.0)
    origin = mechanism.platform_origin(theta)
    start, idlers, end = mechanism.forearm_gear_centres()
    centres = [origin + start, *(origin + c for c in idlers)]
    names = ["scissor-drive-gear", "idler-gear-0", "idler-gear-1",
             "idler-gear-2", "forearm-output-gear"]
    for index in range(len(names) - 1):
        for sign, tag in ((1.0, "+"), (-1.0, "-")):
            out[f"{names[index]}~{names[index + 1]}{tag}_deg"] = play(
                parts[names[index]], parts[names[index + 1]],
                lambda s, g=sign, c=centres[index]: rotate([0, 1, 0], c)(
                    g * s),
                15.0, 0.5)
    return out


def main(thetas) -> int:
    worst = 0.0
    for theta in thetas:
        started = time.perf_counter()
        hits = all_pairs(theta)
        bad = [h for h in hits if not h["intended"]
               and h["volume_mm3"] > COLLISION_LIMIT_MM3]
        print(f"theta {theta:5.1f}: {len(hits)} contacts, {len(bad)} "
              f"collisions > {COLLISION_LIMIT_MM3} mm3 "
              f"({time.perf_counter() - started:.0f} s)", flush=True)
        for h in sorted(hits, key=lambda h: -h["volume_mm3"]):
            tag = "ok " if h["intended"] else "BAD" if h["volume_mm3"] > \
                COLLISION_LIMIT_MM3 else "low"
            print(f"  {tag} {h['a']} x {h['b']}: {h['volume_mm3']:.3f} mm3 "
                  f"{h['bounds']}", flush=True)
            if not h["intended"]:
                worst = max(worst, h["volume_mm3"])
    print(f"worst unintended: {worst:.3f} mm3")
    return 0 if worst <= COLLISION_LIMIT_MM3 else 1


# ------------------------------------------------------------------ helpers

def _rot(deg: float, axis, point=None) -> np.ndarray:
    return trimesh.transformations.rotation_matrix(np.deg2rad(deg), axis,
                                                   point)


def _tmat(vector) -> np.ndarray:
    return trimesh.transformations.translation_matrix(
        np.asarray(vector, dtype=float))


def rod(radius: float, p0, p1, sections: int = 24) -> trimesh.Trimesh:
    return trimesh.creation.cylinder(
        radius=radius, sections=sections,
        segment=np.vstack([p0, p1]).astype(float))


def box_between(lo, hi) -> trimesh.Trimesh:
    lo = np.asarray(lo, dtype=float)
    hi = np.asarray(hi, dtype=float)
    return trimesh.creation.box(extents=hi - lo, transform=_tmat((lo + hi) / 2))


def crop(mesh: trimesh.Trimesh, lo, hi) -> trimesh.Trimesh | None:
    lo = np.maximum(np.asarray(lo, dtype=float), mesh.bounds[0] - 1.0)
    hi = np.minimum(np.asarray(hi, dtype=float), mesh.bounds[1] + 1.0)
    if np.any(hi <= lo):
        return None
    return _intersection(mesh, box_between(lo, hi))


def poses(theta: float) -> dict:
    rad = np.deg2rad(theta)
    lift = scene.ARM_L * np.sin(rad)
    plat_origin = np.array([scene.FLOOR_PIVOT[0] - scene.PLATFORM_PIN, 0.0,
                            scene.FLOOR_PIVOT[1] + lift + 8.0])
    return {
        "lift": lift,
        "slider_x": scene.FLOOR_PIVOT[0] + scene.ARM_L * np.cos(rad),
        "top": scene.FLOOR_PIVOT[1] + lift,
        "plat_origin": plat_origin,
        "hinge": plat_origin + np.array([scene.ARM_HINGE_X, 0.0,
                                         scene.ARM_HINGE_Z]),
        "tilt": mechanism.forearm_angle(theta),
        "opening": mechanism.lid_angle(theta),
        "drive": mechanism.drive_angle(theta),
        "rise": mechanism.lid_follower_rise(theta),
    }


# ------------------------------------------------- non-printed filament pins

# (name, length, hosts that must hold it, purpose)
FILAMENT_PINS = (
    ("hinge", 198.0, ("chest", "lid", "lid-crank", "crank-spacer"),
     "Lid hinge axis (chest Ø1.9, lid Ø1.98, crank/spacer Ø2.3)"),
    ("knob-cross", 14.0, ("drive-pinion", "drive-skull-knob"),
     "Skull-knob/pinion-shaft cross-pin (Ø2.3 bore)"),
    ("forearm-retainer", 10.0, ("forearm-output-gear",),
     "Forearm D-shaft axial retainer (Ø2.3 bore)"),
    ("wrist", 16.0, ("forearm", "hand-palm"),
     "Wrist cross-pin (Ø2.3 bore)"),
)


def filament_segment(name: str, theta: float) -> np.ndarray:
    """World end points of a 1.75 mm filament pin at ``theta``."""
    p = poses(theta)
    length = dict((n, l) for n, l, _, _ in FILAMENT_PINS)[name]

    def seg(centre, axis):
        centre = np.asarray(centre, dtype=float)
        axis = np.asarray(axis, dtype=float)
        axis = axis / np.linalg.norm(axis)
        return np.array([centre - axis * length / 2.0,
                         centre + axis * length / 2.0])

    if name == "hinge":
        return seg((0.0, scene.HINGE_Y, scene.HINGE_Z), (1.0, 0.0, 0.0))
    if name == "knob-cross":
        pts = seg((0.0, 0.0, mechanism.DRIVE_CROSS_PIN_Z), (0.0, 1.0, 0.0))
        matrix = (_tmat(mechanism.DRIVE_AXIS + np.array(
            [0.0, mechanism.DRIVE_GEAR_Y[0] - mechanism.DRIVE_AXIS[1], 0.0]))
            @ _rot(90.0, [1, 0, 0]) @ _rot(-p["drive"], [0, 0, 1]))
    elif name == "forearm-retainer":
        pts = seg((0.0, mechanism.FOREARM_RETAINER_Y, 0.0), (1.0, 0.0, 0.0))
        matrix = _tmat(p["hinge"]) @ _rot(p["tilt"], [0, 1, 0])
    elif name == "wrist":
        a = np.deg2rad(mechanism.HAND_PALM_ROLL + 0.5)
        pts = seg((0.0, 0.0, mechanism.FOREARM_LENGTH + 9.0),
                  (np.cos(a), np.sin(a), 0.0))
        matrix = (_tmat(p["hinge"]) @ _rot(p["tilt"], [0, 1, 0])
                  @ _tmat([0.0, 0.0, scene.FOREARM_SEAT_Z]))
    else:
        raise KeyError(name)
    return trimesh.transform_points(pts, matrix)


def filament_proxy(name: str, theta: float,
                   radius: float = FILAMENT_R) -> trimesh.Trimesh:
    p0, p1 = filament_segment(name, theta)
    return rod(radius, p0, p1)


def filament_check(thetas=(18.0, 48.0, 78.0)) -> list[dict]:
    rows = []
    for name, length, hosts, purpose in FILAMENT_PINS:
        collisions, engaged = {}, {h: True for h in hosts}
        for theta in thetas:
            parts = scene_parts(theta)
            proxy = filament_proxy(name, theta)
            shell = filament_proxy(name, theta, FILAMENT_R + 0.6)
            for part, mesh in parts.items():
                vol = volume_intersection(proxy, mesh)
                if vol > SWEEP_LIMIT_MM3:
                    collisions[part] = max(collisions.get(part, 0.0), vol)
            for host in hosts:
                if volume_intersection(shell, parts[host]) < 1.0:
                    engaged[host] = False
        rows.append({"name": name, "length": length, "purpose": purpose,
                     "hosts": hosts, "collisions": collisions,
                     "engaged": engaged,
                     "ok": not collisions and all(engaged.values())})
    return rows


# --------------------------------------------------------------------- BOM

def scene_to_print(name: str) -> str:
    if name.startswith("arm-"):
        return "scissor-arm"
    if name.startswith("lid-transfer-"):
        return "lid-transfer-gear"
    if re.fullmatch(r"idler-gear-\d+", name):
        return "idler-gear"
    if name == "pivot-pin-fixed-1":
        return "pivot-pin-gear"
    if re.match(r"pivot-pin-(fixed|slot)-", name):
        return "pivot-pin-short"
    match = re.fullmatch(r"(pivot-pin-(?:floor|slider|centre|idler))-\d+",
                         name)
    return match.group(1) if match else name


def print_bom() -> collections.Counter:
    import ghouls_grip
    with zipfile.ZipFile(PRINT_3MF) as archive:
        config = ET.fromstring(archive.read("Metadata/model_settings.config"))
    names = [obj.find("metadata[@key='name']").get("value")
             for obj in config.findall("object")]
    return collections.Counter(ghouls_grip.base_part_name(n) for n in names)


def bom_check() -> dict:
    printed = print_bom()
    needed = collections.Counter(scene_to_print(n) for n in scene_parts(48.0))
    missing = needed - printed
    extra = printed - needed
    pins = {f"pivot-pin-{v}": q for v, q in mechanism.PIN_QUANTITIES.items()}
    pin_mismatch = {k: (q, printed.get(k, 0)) for k, q in pins.items()
                    if printed.get(k, 0) != q}
    return {"printed": printed, "needed": needed, "missing": dict(missing),
            "extra": dict(extra), "pin_mismatch": pin_mismatch,
            "ok": not missing and not extra and not pin_mismatch}


# ------------------------------------------------------------ snap pins

def pin_poses(theta: float) -> dict[str, tuple]:
    """name -> (variant, x, y_head, z, direction) exactly as in the scene."""
    p = poses(theta)
    fx, fz = scene.FLOOR_PIVOT
    specs = [
        ("floor", fx, fz, 30.0),
        ("slider", p["slider_x"], fz, 36.6),
        ("centre", p["slider_x"] / 2.0, fz + p["lift"] / 2.0, 35.0),
        ("fixed", fx, p["top"], 36.6),
        ("slot", p["slider_x"], p["top"], 30.6),
    ]
    out = {}
    for plane, y in enumerate((-scene.SCISSOR_Y, scene.SCISSOR_Y)):
        side = float(np.sign(y))
        for role, x, z, u in specs:
            variant = scene.PIN_ROLE_VARIANT[role]
            if role == "fixed":
                variant = "gear" if side > 0 else "short"
            out[f"pivot-pin-{role}-{plane}"] = (variant, x, side * u, z, side)
    _, idler_local, _ = mechanism.forearm_gear_centres()
    for index, centre in enumerate(idler_local):
        world = p["plat_origin"] + centre
        out[f"pivot-pin-idler-{index}"] = (
            "idler", world[0], 53.0 - mechanism.IDLER_HEAD_CBORE_DEPTH,
            world[2], -1.0)
    out["pivot-pin-follower"] = ("follower", mechanism.FOLLOWER_X, 46.0,
                                 mechanism.FOLLOWER_PIN_Z + p["rise"], 1.0)
    return out


def pin_matrix(x, y_head, z, direction) -> np.ndarray:
    return _tmat([x, y_head, z]) @ _rot(-90.0 if direction > 0 else 90.0,
                                        [1, 0, 0])


@functools.lru_cache(maxsize=None)
def pin_tip(variant: str) -> float:
    return float(mechanism.build_pin_variant(variant=variant).bounds[1][2])


def insertion_sweep(variant: str, pose) -> trimesh.Trimesh:
    """Exact swept volume of a pin pushed in along its axis, plus finger room.

    Closed barbs (r PIN_BARB_ARC_R) sweep from outside to the tip; the head
    (and an 8 mm finger/plier envelope behind it) sweeps up to the face.
    """
    _, x, y_head, z, direction = pose
    tip = pin_tip(variant)
    closed = (mechanism.PIN_D / 2.0 if variant == "follower"
              else mechanism.PIN_BARB_ARC_R + 0.001)
    start = -(tip + 0.5)
    sweep = trimesh.boolean.union([
        rod(closed, (0, 0, start), (0, 0, tip)),
        rod(mechanism.PIN_HEAD_D / 2.0, (0, 0, start - 9.6), (0, 0, -0.02)),
    ], engine="manifold")
    sweep.apply_transform(pin_matrix(x, y_head, z, direction))
    return sweep


SUBASSEMBLY = ("platform", "forearm", "forearm-output-gear")
ASSEMBLY_ORDER = (
    (1, "Place the chest on the table with its opening facing up."),
    (2, "Press the slider vertically onto the rail until both snap fingers "
        "engage in the groove."),
    (3, "Slide the drive pinion axially through the front-wall hole from "
        "inside, engaging it with the rack."),
    (4, "Fit the skull knob onto the D-shaft and insert a Ø1.75 × 14 mm "
        "filament pin through the knob and shaft."),
    (5, "Lower the lid follower into its guide channel; press the follower pin "
        "from inside through the follower and into the cam slot."),
    (6, "Slide both lid transfer gears axially in −X into the bearing blocks; "
        "secure each journal from the outside with a Ø1.75 × 5 mm filament pin."),
    (7, "Install the scissor arms in each layer; snap in the floor, slider, "
        "and center pins from inside (pin heads inward)."),
    (8, "Place the scissor input gear from +Y onto the upper arm eye and press "
        "its locating pin into the arm hole (before installing the platform)."),
    (9, "Preassemble the platform outside the chest: place the forearm between "
        "the ears, pass through the output-gear D-shaft, add the Ø1.75 × 10 mm "
        "filament retainer, and fit three idler gears with their pins. Lower "
        "vertically with a 3 mm offset away from the scissor input gear "
        "(toward idler 0), then slide along the shaft axis to engage; snap in "
        "the upper gear, fixed, and slotted pins."),
    (10, "Fit the hand onto the forearm journal and insert a Ø1.75 × 16 mm "
         "filament cross-pin."),
    (11, "Preassemble the lid outside the chest, upside down: insert the lid "
         "crank from below and slide it in +X into the drive pocket; place the "
         "spacer from below in the service channel between the crank and lid eye."),
    (12, "Hold the lid assembly open about 108°, lower it vertically with a "
         "3 mm rearward (+Y) offset, then slide it forward to engage the idler "
         "until the hinge eyes align. Pass the Ø1.75 × 198 mm hinge filament "
         "through the chest, lid, crank, and spacer."),
)


def assembly_step(name: str) -> int:
    if name == "chest":
        return 1
    if name == "slider":
        return 2
    if name == "drive-pinion":
        return 3
    if name == "drive-skull-knob":
        return 4
    if name in ("lid-follower-rack", "pivot-pin-follower"):
        return 5
    if name.startswith("lid-transfer-"):
        return 6
    if name.startswith("arm-") or re.match(
            r"pivot-pin-(floor|slider|centre)-", name):
        return 7
    if name == "scissor-drive-gear":
        return 8
    if (name in SUBASSEMBLY or name.startswith("idler-gear-")
            or name.startswith("pivot-pin-idler-")
            or re.match(r"pivot-pin-(fixed|slot)-", name)):
        return 9
    if name.startswith("hand-"):
        return 10
    if name in ("lid", "lid-crank", "crank-spacer"):
        return 11
    return 12


def _is_pin(name: str) -> bool:
    return name.startswith("pivot-pin-")


def pin_obstacles(pin: str, names) -> list[str]:
    if pin.startswith("pivot-pin-idler-"):
        return [n for n in names
                if n in SUBASSEMBLY or n.startswith("idler-gear-")]
    step = assembly_step(pin)
    out = []
    for n in names:
        if n == pin or (pin == "pivot-pin-follower"
                        and n == "lid-follower-rack"):
            continue
        s = assembly_step(n)
        if s < step or (s == step and not _is_pin(n)):
            out.append(n)
    return out


def pin_insertion_check(thetas=(18.0, 48.0, 78.0)) -> list[dict]:
    rows = []
    for pin in pin_poses(48.0):
        per_theta = {}
        for theta in thetas:
            parts = scene_parts(theta)
            pose = pin_poses(theta)[pin]
            sweep = insertion_sweep(pose[0], pose)
            hits = {}
            for n in pin_obstacles(pin, parts):
                vol = volume_intersection(sweep, parts[n])
                if vol > SWEEP_LIMIT_MM3:
                    hits[n] = round(vol, 3)
            per_theta[theta] = hits
            if not hits:
                break
        clear = [t for t, h in per_theta.items() if not h]
        rows.append({"pin": pin, "variant": pin_poses(48.0)[pin][0],
                     "clear_at": clear, "hits": per_theta,
                     "ok": bool(clear)})
        print(f"  insert {pin}: {'ok @' + str(clear[0]) if clear else per_theta}",
              flush=True)
    return rows


def free_travel(movers, fixed, vector, limit: float, step: float) -> float:
    """Largest translation along ``vector`` before any mover hits ``fixed``."""
    vector = np.asarray(vector, dtype=float)
    pad = np.abs(vector) * (limit + 1.0) + 1.0
    lo = np.min([m.bounds[0] for m in movers], axis=0) - pad
    hi = np.max([m.bounds[1] for m in movers], axis=0) + pad
    crops = [c for c in (crop(f, lo, hi) for f in fixed) if c is not None]

    def clear(s: float) -> bool:
        for mover in movers:
            probe = mover.copy()
            probe.apply_translation(vector * s)
            if sum(volume_intersection(probe, c) for c in crops) > 0.01:
                return False
        return True

    if not clear(0.0):
        return 0.0
    s = 0.0
    while s < limit:
        nxt = min(s + step, limit)
        if not clear(nxt):
            lo_s, hi_s = s, nxt
            while hi_s - lo_s > step / 32.0:
                mid = (lo_s + hi_s) / 2.0
                lo_s, hi_s = (mid, hi_s) if clear(mid) else (lo_s, mid)
            return lo_s
        s = nxt
    return limit


def pin_play_check(theta: float = 48.0) -> list[dict]:
    parts = scene_parts(theta)
    rows = []
    for pin in pin_poses(theta):
        mesh = parts[pin]
        lo, hi = mesh.bounds[0] - 0.3, mesh.bounds[1] + 0.3
        neighbours = [n for n, m in parts.items()
                      if n != pin and not _is_pin(n)
                      and not n.startswith("hand-")
                      and np.all(m.bounds[0] <= hi) and np.all(m.bounds[1] >= lo)]
        row = {"pin": pin, "neighbours": neighbours}
        if pin == "pivot-pin-follower":
            row["press_mm3"] = volume_intersection(
                mesh, parts["lid-follower-rack"])
            neighbours = [n for n in neighbours if n != "lid-follower-rack"]
        fixed = [parts[n] for n in neighbours]
        radial = [free_travel([mesh], fixed, v, 1.5, 0.1)
                  for v in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1))]
        row["radial_min"] = min(radial)
        row["radial"] = radial
        if pin != "pivot-pin-follower":
            axial = [free_travel([mesh], fixed, v, 1.5, 0.05)
                     for v in ((0, 1, 0), (0, -1, 0))]
            row["axial_total"] = sum(axial)
            row["ok"] = (row["radial_min"] >= MIN_RADIAL_PLAY - 1e-3
                         and MIN_AXIAL_PLAY <= row["axial_total"] <= 1.0)
        else:
            row["axial_total"] = None
            row["ok"] = (row["radial_min"] >= MIN_RADIAL_PLAY - 1e-3
                         and 0.0 < row["press_mm3"] <= INTENDED_LIMIT_MM3)
        rows.append(row)
        print(f"  play {pin}: radial {row['radial_min']:.2f} axial "
              f"{row['axial_total']}", flush=True)
    return rows


# --------------------------------------------------------- assembly sweeps

def stepped_sweep(movers, obstacles: dict, legs, step: float = 1.5) -> dict:
    """Move ``movers`` along consecutive legs; report first hit per part.

    ``legs``: list of (vector, distance).  A distance of ``None`` means
    "until every mover is 2 mm above every obstacle".
    """
    hits = {}
    offset = np.zeros(3)
    for vector, distance in legs:
        vector = np.asarray(vector, dtype=float)
        if distance is None:
            top = max(m.bounds[1][2] for m in obstacles.values())
            low = min(m.bounds[0][2] for m in movers) + offset[2]
            distance = max(0.0, top - low + 2.0)
        start = offset.copy()
        end = offset + vector * distance
        lo = np.min([m.bounds[0] for m in movers], axis=0) + np.minimum(
            start, end) - 1.0
        hi = np.max([m.bounds[1] for m in movers], axis=0) + np.maximum(
            start, end) + 1.0
        crops = {n: c for n, c in ((n, crop(m, lo, hi))
                                   for n, m in obstacles.items())
                 if c is not None}
        for s in np.append(np.arange(0.0, distance, step), distance):
            shift = start + vector * s
            for mover in movers:
                probe = mover.copy()
                probe.apply_translation(shift)
                for n, c in crops.items():
                    vol = volume_intersection(probe, c)
                    if vol > SWEEP_LIMIT_MM3 and n not in hits:
                        hits[n] = (np.round(shift, 1).tolist(), round(vol, 2))
        offset = end
    return hits


def _installed_before(parts, step: int, exclude=()) -> dict:
    return {n: m for n, m in parts.items()
            if assembly_step(n) < step and n not in exclude}


def _no_snap_noses(slider: trimesh.Trimesh) -> trimesh.Trimesh:
    slabs = [box_between([-300, 56.85, -50], [300, 200, 300]),
             box_between([-300, -200, -50], [300, -56.85, 300])]
    out = trimesh.boolean.difference([slider, *slabs], engine="manifold")
    return out


def _no_transfer_barbs(gear_mesh: trimesh.Trimesh, y_center: float) -> trimesh.Trimesh:
    """Trim the compressed snap-clip overhang on the transfer journal."""
    outer = box_between([-45.0, y_center - 5.0, scene.HINGE_Z - 5.0],
                        [-33.2, y_center + 5.0, scene.HINGE_Z + 5.0])
    core = rod(1.48, [-45.0, y_center, scene.HINGE_Z],
               [-33.2, y_center, scene.HINGE_Z], sections=48)
    ring = trimesh.boolean.difference([outer, core], engine="manifold")
    return trimesh.boolean.difference([gear_mesh, ring], engine="manifold")


def assembly_sweeps() -> list[dict]:
    rows = []

    def run(label, thetas, build):
        """``build`` returns (movers, obstacles, legs or [legs, ...])."""
        results = {}
        for theta in thetas:
            parts = scene_parts(theta)
            movers, obstacles, legs = build(parts, theta)
            options = legs if isinstance(legs[0], list) else [legs]
            for index, option in enumerate(options):
                hits = stepped_sweep(movers, obstacles, option)
                key = theta if len(options) == 1 else f"{theta}/Weg{index + 1}"
                results[key] = hits
                if not hits:
                    break
            if not hits:
                break
        clear = [t for t, h in results.items() if not h]
        rows.append({"label": label, "clear_at": clear, "hits": results,
                     "ok": bool(clear)})
        print(f"  sweep {label}: {'ok @' + str(clear[0]) if clear else results}",
              flush=True)

    run("Insert slider vertically (without snap noses)", (18.0, 48.0, 78.0),
        lambda p, t: ([_no_snap_noses(p["slider"])],
                      {"chest": p["chest"]},
                      [[((1, 0, 0), 5.5), ((0, 0, 1), None)],
                       [((0, 0, 1), None)]]))
    run("Insert pinion axially from inside, then lift it out", (18.0, 48.0, 78.0),
        lambda p, t: ([p["drive-pinion"]],
                      {n: p[n] for n in ("chest", "slider")},
                      [((0, 1, 0), 32.0), ((0, 0, 1), None)]))
    run("Fit skull knob axially onto the D-shaft", (18.0,),
        lambda p, t: ([p["drive-skull-knob"]],
                      {n: p[n] for n in ("chest", "drive-pinion")},
                      [((0, -1, 0), 20.0)]))
    # Split snap-clip tip (local z -12.8) must clear the block's inner face (-6):
    # 6.8 mm + 0.7 mm margin; a longer pull would hit the chest knuckle.
    for gear, gy in (("lid-transfer-input", mechanism.LID_TRANSFER_Y),
                     ("lid-transfer-idler", mechanism.LID_IDLER_Y)):
        run(f"{gear}: insert clip journal axially into bearing, then lift out",
            (18.0, 48.0, 78.0),
            lambda p, t, g=gear, y=gy: (
                [_no_transfer_barbs(p[g], y)],
                {n: m for n, m in _installed_before(p, 7).items()
                 if n != g and not (g == "lid-transfer-input"
                                    and n == "lid-transfer-idler")},
                [((1, 0, 0), 7.5), ((0, 0, 1), None)]))
    for plane in (0, 1):
        run(f"Lower scissor-arm pair in layer {plane} vertically",
            (18.0, 48.0, 78.0),
            lambda p, t, k=plane: (
                [p[f"arm-{k}-True"], p[f"arm-{k}-False"]],
                {n: m for n, m in p.items()
                 if assembly_step(n) < 7 or (k == 1 and n.startswith("arm-0-"))},
                [((0, 0, 1), None)]))
    # Key peg engages the arm 3.5 mm (world y 41.5..45); pull 4.2 mm.
    run("Scissor input gear: withdraw locating pin from arm hole, then lift out",
        (48.0, 60.0, 78.0),
        lambda p, t: ([p["scissor-drive-gear"]],
                      {n: m for n, m in p.items() if assembly_step(n) <= 7},
                      [((0, 1, 0), 4.2), ((0, 0, 1), None)]))
    # The drive->idler-0 line of centres is 64 deg from vertical, so a
    # straight drop clashes tooth tips; lower offset, then slide into mesh.
    start, idlers, _ = mechanism.forearm_gear_centres()
    mesh_dir = np.asarray(idlers[0], float) - np.asarray(start, float)
    mesh_dir /= np.linalg.norm(mesh_dir)
    run("Lower offset platform assembly and engage radially",
        (78.0, 60.0, 48.0),
        lambda p, t: (
            [p[n] for n in p if assembly_step(n) == 9 and not _is_pin(n)
             or n.startswith("pivot-pin-idler-")],
            {n: m for n, m in p.items() if assembly_step(n) <= 8},
            [(tuple(mesh_dir), 3.0), ((0, 0, 1), None)]))

    def hand_build(p, t):
        axis = trimesh.transform_points(
            [[0, 0, 0], [0, 0, 1]], _rot(poses(t)["tilt"], [0, 1, 0]))
        axis = axis[1] - axis[0]
        return ([p[n] for n in p if n.startswith("hand-")],
                {n: m for n, m in p.items() if assembly_step(n) <= 9},
                [(axis, 25.0)])
    run("Remove hand axially from forearm journal", (78.0, 60.0), hand_build)

    def lid_under(t):
        return tuple(scene.rot(scene.lid_angle(t), [1, 0, 0])[:3, :3]
                     @ [0.0, 0.0, -1.0])
    # Sub-assembly on the loose lid: the coupling slot is open only toward
    # -x, so the crank goes in from below and slides +x; the spacer is
    # enclosed by lid and chest once mounted and must be inserted first.
    run("Fit crank to detached lid: from below, then +X into the pocket",
        (48.0, 18.0),
        lambda p, t: ([p["lid-crank"]], {"lid": p["lid"]},
                      [((-1, 0, 0), 5.6), (lid_under(t), 30.0)]))
    run("Fit spacer from below into the detached lid channel",
        (48.0, 18.0),
        lambda p, t: ([p["crank-spacer"]],
                      {"lid": p["lid"], "lid-crank": p["lid-crank"]},
                      [(lid_under(t), 30.0)]))
    # Crank/transfer-idler line of centres is horizontal (-y), so a straight
    # drop clashes tooth tips: lower 3 mm behind, then slide forward in mesh.
    run("Lower open lid assembly 3 mm rearward, then slide forward to engage",
        (48.0, 30.0, 60.0),
        lambda p, t: ([p[n] for n in p if assembly_step(n) == 11],
                      {n: m for n, m in p.items() if assembly_step(n) <= 10},
                      [((0, 1, 0), 3.0), ((0, 0, 1), None)]))
    return rows


def part_play_check(theta: float = 48.0) -> list[dict]:
    """Guide and axial play of the moving parts (with their filament pins)."""
    parts = scene_parts(theta)
    cases = [
        ("Slider in rail (transverse Y)", ["slider"], ["chest"],
         ((0, 1, 0), (0, -1, 0))),
        ("Slider in rail (Z)", ["slider"], ["chest"],
         ((0, 0, 1), (0, 0, -1))),
        ("Follower in channel (X)", ["lid-follower-rack", "pivot-pin-follower"],
         ["chest"], ((1, 0, 0), (-1, 0, 0))),
        ("Follower in channel (Y)", ["lid-follower-rack", "pivot-pin-follower"],
         ["chest"], ((0, 1, 0), (0, -1, 0))),
        ("Pinion + knob axially (Y)", ["drive-pinion", "drive-skull-knob",
                                    ("knob-cross",)],
         ["chest"], ((0, 1, 0), (0, -1, 0))),
        ("Input transfer gear axially (X, clip)",
         ["lid-transfer-input"], ["chest"],
         ((1, 0, 0), (-1, 0, 0))),
        ("Idler transfer gear axially (X, clip)",
         ["lid-transfer-idler"], ["chest"],
         ((1, 0, 0), (-1, 0, 0))),
        ("Output gear + shaft axially (Y)",
         ["forearm-output-gear", ("forearm-retainer",)],
         ["platform", "forearm"], ((0, 1, 0), (0, -1, 0))),
        ("Lid crank axially (X, spacer)", ["lid-crank"],
         ["lid", "crank-spacer"], ((1, 0, 0), (-1, 0, 0))),
        ("Spacer axially (X)", ["crank-spacer"],
         ["lid", "lid-crank"], ((1, 0, 0), (-1, 0, 0))),
    ]
    for index in range(3):
        cases.append((f"Idler gear {index} axially (Y)", [f"idler-gear-{index}"],
                      ["platform", f"pivot-pin-idler-{index}"],
                      ((0, 1, 0), (0, -1, 0))))
    rows = []
    for label, movers, fixed, dirs in cases:
        meshes = [filament_proxy(m[0], theta) if isinstance(m, tuple)
                  else parts[m] for m in movers]
        travel = [free_travel(meshes, [parts[f] for f in fixed], v, 3.0, 0.1)
                  for v in dirs]
        total = sum(travel)
        rows.append({"label": label, "travel": travel, "total": total,
                     "ok": 0.1 <= total < 2.9 and min(travel) < 2.9})
        print(f"  part play {label}: {travel}", flush=True)
    return rows


# ------------------------------------------------------------- gears

def backlash_mm(thetas=(18.0, 48.0, 78.0)) -> list[dict]:
    radii = {
        "pinion-rack": (mechanism.DRIVE_PITCH_R, 3.0),
        "transfer-idler": (mechanism.LID_SECTOR_R, 20.0),
        "idler-crank": (mechanism.LID_SECTOR_R, 20.0),
        "scissor-drive-gear~idler-gear-0": (mechanism.FOREARM_INPUT_R, 15.0),
        "idler-gear-0~idler-gear-1": (mechanism.FOREARM_IDLER_R, 15.0),
        "idler-gear-1~idler-gear-2": (mechanism.FOREARM_IDLER_R, 15.0),
        "idler-gear-2~forearm-output-gear": (mechanism.FOREARM_IDLER_R, 15.0),
    }
    rows = []
    for theta in thetas:
        report = backlash_report(theta)
        for key, (radius, limit) in radii.items():
            plus = report[f"{key}+_deg"]
            minus = report[f"{key}-_deg"]
            mm = [np.deg2rad(plus) * radius, np.deg2rad(minus) * radius]
            engaged = plus < limit - 1e-6 and minus < limit - 1e-6
            rows.append({"theta": theta, "mesh": key, "mm": mm,
                         "engaged": engaged,
                         "ok": engaged and min(mm) >= MIN_BACKLASH_MM})
        plus = report["follower-transfer+_mm"]
        minus = report["follower-transfer-_mm"]
        engaged = plus < 1.5 - 1e-6 and minus < 1.5 - 1e-6
        rows.append({"theta": theta, "mesh": "follower-rack~transfer",
                     "mm": [plus, minus], "engaged": engaged,
                     "ok": engaged and min(plus, minus) >= MIN_BACKLASH_MM})
    return rows


# --------------------------------------------------------- analytic checks

def split_pin_strain(grip: float) -> dict:
    catch = grip + mechanism.PIN_AXIAL_PLAY
    slot_from = max(catch - mechanism.PIN_SLOT_REACH, 0.8)
    length = catch - slot_from + mechanism.PIN_BARB_LAND / 2.0
    r = mechanism.PIN_D / 2.0
    half = mechanism.PIN_SLOT_W / 2.0
    xs, ys = np.meshgrid(np.linspace(half, r, 400), np.linspace(-r, r, 800))
    inside = (xs ** 2 + ys ** 2 <= r * r) & (ys >= mechanism.PIN_FLAT_Y)
    centroid = float(xs[inside].mean())
    c = max(r - centroid, centroid - half)
    delta = mechanism.PIN_BARB_OFFSET
    strain = 3.0 * delta * c / length ** 2
    return {"grip": grip, "beam_l": length, "c": c, "delta": delta,
            "strain": strain, "ok": strain <= MAX_SNAP_STRAIN}


def analytic_checks() -> dict:
    out = {}
    bore_r = mechanism.PIVOT_D / 2.0
    out["barb"] = {
        "closed_r": mechanism.PIN_BARB_ARC_R, "bore_r": bore_r,
        "insert_clear": bore_r - mechanism.PIN_BARB_ARC_R,
        "relaxed_r": mechanism.PIN_BARB_R,
        "catch_overlap": mechanism.PIN_BARB_R - bore_r,
        "cbore_clear": mechanism.PIN_CBORE_D / 2.0 - mechanism.PIN_BARB_R,
    }
    out["barb"]["ok"] = (out["barb"]["insert_clear"] >= 0.05
                         and out["barb"]["catch_overlap"] >= 0.15
                         and out["barb"]["cbore_clear"] >= 0.2)
    out["split"] = {v: split_pin_strain(g)
                    for v, g in mechanism.PIN_GRIPS.items() if v != "follower"}
    out["crush"] = {"interference": mechanism.PIN_CRUSH_R - bore_r}
    out["crush"]["ok"] = 0.05 <= out["crush"]["interference"] <= 0.25
    # Slider snap finger (build_slider): nose reaches u 59.4 into the u 58
    # cavity wall; finger 1.6 thick, load point 23.5 mm from the root.
    delta, t, length = 59.4 - 58.0, 1.6, 23.5
    out["finger"] = {"delta": delta, "t": t, "l": length,
                     "strain": 1.5 * delta * t / length ** 2}
    out["finger"]["ok"] = out["finger"]["strain"] <= MAX_SNAP_STRAIN
    return out


def lid_load() -> dict:
    lid = scene_parts(18.0)["lid"]
    volume = float(lid.volume)
    lever = abs(scene.HINGE_Y - float(lid.center_mass[1]))
    thetas = np.linspace(mechanism.THETA_MIN, mechanism.THETA_MAX, 1201)
    xs = scene.FLOOR_PIVOT[0] + scene.ARM_L * np.cos(np.deg2rad(thetas))
    rise = np.array([mechanism.lid_follower_rise(t) for t in thetas])
    slope = np.abs(np.gradient(rise, xs))
    alpha = float(np.degrees(np.arctan(slope.max())))
    phi = float(np.degrees(np.arctan(PLA_MU)))
    rows = {}
    for label, fill in (("realistisch (60 % Fuellung)", 0.6),
                        ("obere Grenze (massiv)", 1.0)):
        mass = volume * PLA_DENSITY * fill
        torque = mass / 1000.0 * 9.81 * lever / 1000.0          # N m
        rack = torque / (mechanism.LID_SECTOR_R / 1000.0) / 0.9 ** 3
        slider = rack * math.tan(math.radians(min(alpha + phi, 89.0)))
        knob_torque = slider * mechanism.DRIVE_PITCH_R / 1000.0
        teeth = max(6, int(round(2 * np.pi * mechanism.LID_SECTOR_R
                                 / mechanism.GEAR_PITCH)))
        module = 2.0 * mechanism.LID_SECTOR_R / teeth
        lewis = rack / (4.0 * module * 0.18)
        rows[label] = {"mass_g": mass, "torque_nm": torque, "rack_n": rack,
                       "slider_n": slider, "knob_nm": knob_torque,
                       "finger_n": knob_torque / 0.0195, "lewis_mpa": lewis}
    return {"volume_cm3": volume / 1000.0, "lever_mm": lever,
            "alpha_deg": alpha, "phi_deg": phi, "cases": rows,
            "jam_ok": alpha + phi < 80.0}


# ------------------------------------------------------------- report

def _flag(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def full_audit() -> int:
    started = time.perf_counter()
    lines = ["# Ghoul's Grip — Assembly and Mechanism Audit", "",
             "Automatically generated by `scripts/audit_ghouls_grip_assembly.py`."
             " All checks use the exact scene meshes "
             "(`render_ghouls_grip.build_scene_at`) with manifold Booleans.",
             "", "Tolerance assumptions (Kobra S1, 0.4 mm nozzle, 0.2 mm layer): "
             f"radial clearance >= {MIN_RADIAL_PLAY} mm per side, axial clearance "
             f">= {MIN_AXIAL_PLAY} mm, backlash >= {MIN_BACKLASH_MM} mm per "
             f"direction, snap strain <= {MAX_SNAP_STRAIN * 100:.0f} %, "
             f"collision > {COLLISION_LIMIT_MM3} mm3 = FAIL, insertion/assembly "
             f"sweeps > {SWEEP_LIMIT_MM3} mm3 = FAIL.", ""]
    verdicts = []

    print("BOM ...", flush=True)
    bom = bom_check()
    verdicts.append(("Bill of materials complete; no extra parts", bom["ok"]))
    lines += ["## 1. Printed Bill of Materials", "",
              f"**{_flag(bom['ok'])}** - {sum(bom['printed'].values())} "
              f"print objects in the project, {sum(bom['needed'].values())} "
              "parts in the assembly.", "",
              "| Part | In print project | In assembly |",
              "| --- | ---: | ---: |"]
    for name in sorted(set(bom["printed"]) | set(bom["needed"])):
        lines.append(f"| {name} | {bom['printed'].get(name, 0)} | "
                     f"{bom['needed'].get(name, 0)} |")
    lines += ["", f"Missing: {bom['missing'] or 'none'}; extra: "
              f"{bom['extra'] or 'none'}; pin quantity mismatch: "
              f"{bom['pin_mismatch'] or 'none'}.", ""]

    print("filament pins ...", flush=True)
    fil = filament_check()
    ok = all(r["ok"] for r in fil)
    verdicts.append(("Unprinted filament pins fit and remain retained", ok))
    lines += ["## 2. Unprinted Parts (1.75 mm PLA Filament)", "",
              f"**{_flag(ok)}** - Ø1.75 pin proxies in the scenes at "
              "theta 18/48/78: no collisions, and each host part has "
              "material around the pin (ring +0.6 mm > 1 mm3).", "",
              "| Pin | Length (mm) | Purpose | Hosts (retained) | Collision | "
              "Status |", "| --- | ---: | --- | --- | --- | --- |"]
    for r in fil:
        hosts = ", ".join(f"{h} ({'yes' if e else 'NO'})"
                          for h, e in r["engaged"].items())
        lines.append(f"| {r['name']} | {r['length']:.0f} | {r['purpose']} | "
                     f"{hosts} | {r['collisions'] or '-'} | "
                     f"{_flag(r['ok'])} |")
    lines.append("")

    print("collisions ...", flush=True)
    lines += ["## 3. Collisions Across the Motion Range", "",
              "| Theta | Contacts | Intended press fits | Collisions | "
              "Maximum unintended volume (mm3) |", "| ---: | ---: | --- | ---: | "
              "---: |"]
    worst_all, bad_total = 0.0, 0
    for theta in AUDIT_THETAS:
        hits = all_pairs(theta)
        intended = [h for h in hits if h["intended"]]
        bad = [h for h in hits if (not h["intended"]
                                   and h["volume_mm3"] > COLLISION_LIMIT_MM3)
               or (h["intended"] and h["volume_mm3"] > INTENDED_LIMIT_MM3)]
        worst = max([h["volume_mm3"] for h in hits if not h["intended"]],
                    default=0.0)
        worst_all = max(worst_all, worst)
        bad_total += len(bad)
        press = ", ".join(f"{h['a']}x{h['b']} {h['volume_mm3']:.2f}"
                          for h in intended) or "-"
        lines.append(f"| {theta:.0f} | {len(hits)} | {press} | {len(bad)} | "
                     f"{worst:.3f} |")
        for h in bad:
            lines.append(f"|  | FAIL {h['a']} x {h['b']} | "
                         f"{h['volume_mm3']:.2f} mm3 | {h['bounds']} | |")
        print(f"  theta {theta}: {len(bad)} bad, worst {worst:.3f}", flush=True)
    verdicts.append(("No collisions across the motion range", bad_total == 0))
    lines += ["", f"**{_flag(bad_total == 0)}** - maximum unintended "
              f"intersection {worst_all:.3f} mm3 (mesh noise/surface contact).", ""]

    print("pin play ...", flush=True)
    play_rows = pin_play_check()
    ok = all(r["ok"] for r in play_rows)
    verdicts.append(("Snap-pin radial and axial clearance", ok))
    lines += ["## 4. Snap-Pin Clearance in the Installed State (Theta 48)", "",
              f"**{_flag(ok)}** - free travel before first contact.",
              "", "| Pin | Minimum radial (mm; +x,-x,+z,-z) | Total axial (mm) | "
              "Neighbors | Status |", "| --- | --- | ---: | --- | --- |"]
    for r in play_rows:
        axial = ("Press pin, ribs " f"{r['press_mm3']:.2f} mm3"
                 if r["axial_total"] is None else f"{r['axial_total']:.2f}")
        lines.append(
            f"| {r['pin']} | {r['radial_min']:.2f} "
            f"({', '.join(f'{v:.2f}' for v in r['radial'])}) | {axial} | "
            f"{', '.join(r['neighbours'])} | {_flag(r['ok'])} |")
    lines.append("")

    print("pin insertion ...", flush=True)
    ins = pin_insertion_check()
    ok = all(r["ok"] for r in ins)
    verdicts.append(("Pins are insertable with sufficient finger/tool clearance", ok))
    lines += ["## 5. Pin Insertability", "",
              f"**{_flag(ok)}** - exact insertion envelope: closed "
              f"barb radius {mechanism.PIN_BARB_ARC_R} mm from base to tip "
              "plus head radius 3.75 mm and 8 mm finger/tool clearance, checked "
              "against all parts already installed at that assembly step.", "",
              "| Pin | Variant | Clear at theta | Intersections (if blocked) "
              "|", "| --- | --- | --- | --- |"]
    for r in ins:
        lines.append(f"| {r['pin']} | {r['variant']} | "
                     f"{r['clear_at'] or 'NIE'} | "
                     f"{'-' if r['ok'] else r['hits']} |")
    lines.append("")

    print("assembly sweeps ...", flush=True)
    sweeps = assembly_sweeps()
    ok = all(r["ok"] for r in sweeps)
    verdicts.append(("All assembly insertion paths are clear", ok))
    lines += ["## 6. Assembly Paths (Incremental Motion Envelopes, 1.5 mm)", "",
              f"**{_flag(ok)}**", "", "| Assembly step | Clear at theta | "
              "Intersections |", "| --- | --- | --- |"]
    for r in sweeps:
        lines.append(f"| {r['label']} | {r['clear_at'] or 'NIE'} | "
                     f"{'-' if r['ok'] else r['hits']} |")
    lines.append("")

    print("part play ...", flush=True)
    pplay = part_play_check()
    ok = all(r["ok"] for r in pplay)
    verdicts.append(("Guide and axial clearance of moving parts", ok))
    lines += ["## 7. Guide and Axial Clearance (Theta 48)", "",
              f"**{_flag(ok)}** - combined travel in both directions is "
              "0.1 .. 2.9 mm (3.0 = not guided).", "",
              "| Part | +/- mm | Total | Status |", "| --- | --- | ---: | --- |"]
    for r in pplay:
        lines.append(f"| {r['label']} | "
                     f"{', '.join(f'{v:.2f}' for v in r['travel'])} | "
                     f"{r['total']:.2f} | {_flag(r['ok'])} |")
    lines.append("")

    print("backlash ...", flush=True)
    bl = backlash_mm()
    ok = all(r["ok"] for r in bl)
    verdicts.append(("Gears mesh with backlash", ok))
    lines += ["## 8. Gear Backlash", "",
              f"**{_flag(ok)}** - play in each rotational direction at the "
              "pitch circle; 'engaged' means the stop occurred before the search limit.", "",
              "| Theta | Mesh pair | + mm | - mm | Engaged | Status |",
              "| ---: | --- | ---: | ---: | --- | --- |"]
    for r in bl:
        lines.append(f"| {r['theta']:.0f} | {r['mesh']} | {r['mm'][0]:.2f} | "
                     f"{r['mm'][1]:.2f} | {'yes' if r['engaged'] else 'NO'} "
                     f"| {_flag(r['ok'])} |")
    lines.append("")

    an = analytic_checks()
    split_ok = all(s["ok"] for s in an["split"].values())
    ok = an["barb"]["ok"] and split_ok and an["crush"]["ok"] and \
        an["finger"]["ok"]
    verdicts.append(("Snap noses, barbs, and crush ribs are dimensioned", ok))
    b = an["barb"]
    lines += ["## 9. Snap Noses, Barbs, and Crush Ribs", "",
              f"**{_flag(ok)}**", "",
              f"* Closed barb radius {b['closed_r']:.2f} in bore radius "
              f"{b['bore_r']:.2f}: {b['insert_clear']:.2f} mm insertion clearance; "
              f"relaxed radius {b['relaxed_r']:.2f}: {b['catch_overlap']:.2f} mm "
              f"undercut; counterbore radius 3.0: {b['cbore_clear']:.2f} mm clearance.",
              f"* Follower press pin: rib radius {mechanism.PIN_CRUSH_R} in radius "
              f"{bore_r_str()} = {an['crush']['interference']:.2f} mm interference "
              "(no barb; the ribs absorb print tolerances).",
              f"* Slider snap finger: deflection {an['finger']['delta']:.1f}"
              f" mm, thickness {an['finger']['t']} mm, length "
              f"{an['finger']['l']} mm -> strain "
              f"{an['finger']['strain'] * 100:.2f} % "
              f"({_flag(an['finger']['ok'])}).", "",
              "| Pin | Grip length (mm) | Flexure length (mm) | c (mm) | Strain (%) | "
              "Status |", "| --- | ---: | ---: | ---: | ---: | --- |"]
    for v, s in an["split"].items():
        lines.append(f"| {v} | {s['grip']} | {s['beam_l']:.2f} | "
                     f"{s['c']:.2f} | {s['strain'] * 100:.2f} | "
                     f"{_flag(s['ok'])} |")
    lines.append("")

    load = lid_load()
    verdicts.append(("Lid cam drive does not jam", load["jam_ok"]))
    lines += ["## 10. Lid Load Path (Estimate; Risk Assessment, Not Proof)", "",
              f"Lid volume {load['volume_cm3']:.0f} cm3, center of mass "
              f"{load['lever_mm']:.0f} mm ahead of the hinge axis. "
              f"Maximum cam slope {load['alpha_deg']:.1f} deg, friction angle "
              f"{load['phi_deg']:.1f} deg (mu {PLA_MU}) -> "
              f"{_flag(load['jam_ok'])} (sum < 80 deg).", "",
              "| Case | Mass (g) | Torque (Nm) | Rack (N) | Slider (N) | "
              "Knob (Nm) | Finger force at knob (N) | Tooth-root stress (MPa) "
              "(Lewis, 4 mm Rad) |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for label, c in load["cases"].items():
        lines.append(f"| {label} | {c['mass_g']:.0f} | {c['torque_nm']:.3f} | "
                     f"{c['rack_n']:.1f} | {c['slider_n']:.1f} | "
                     f"{c['knob_nm']:.2f} | {c['finger_n']:.1f} | "
                     f"{c['lewis_mpa']:.1f} |")
    lines += ["", "The small 6-tooth gears (r 3.7 mm) in the lid drive are the "
              "most highly loaded components; PLA in the layer plane is about "
              "50 MPa, giving a safety factor of about 2–3. Check for broken or "
              "skipped teeth in a test print; if needed, print a lighter lid "
              "(with less infill).", ""]

    lines += ["## 11. Assembly Order (Checked in Sections 5 and 6)", ""]
    lines += [f"{n}. {text}" for n, text in ASSEMBLY_ORDER]
    lines.append("")

    passed = all(ok for _, ok in verdicts)
    summary = ["## Result", "", f"**Overall: {_flag(passed)}** "
               f"({time.perf_counter() - started:.0f} s)", "",
               "| Check | Status |", "| --- | --- |"]
    summary += [f"| {label} | {_flag(ok)} |" for label, ok in verdicts]
    summary.append("")
    REPORT.write_text("\n".join(lines[:5] + summary + lines[5:]) + "\n",
                      encoding="utf-8")
    print("\n".join(summary))
    print(f"report -> {REPORT}")
    return 0 if passed else 1


def bore_r_str() -> str:
    return f"{mechanism.PIVOT_D / 2.0:.2f}"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(main([float(a) for a in sys.argv[1:]]))
    raise SystemExit(full_audit())
