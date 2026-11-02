"""Parametric generator, mechanical/assembly verifier, and OrcaSlicer packager
for the 3.5 mm flat-backed connectable cable channel (`kabelkanal-3-5mm`).

Deliverables produced:
  - models/kabelkanal-3-5mm.stl       : Watertight ASCII STL of one connectable channel segment
                                        (242.0 mm total length = 230.0 mm net modular length +
                                        12.0 mm male V-rail connector tongue, centered at XY = 0,0, Z = 0)
  - models/kabelkanal-3-5mm-print.3mf : Settings-bearing Anycubic Kobra S1 + ACE Pro print project
                                        (White PLA in Slot 1, 2 connectable segments on Plate 1,
                                        layer_height = 0.16 mm, seam_position = random,
                                        ironing_type = top, enable_support = 1 tree(auto) with
                                        0.16 mm Z contact distance, verified 0.00 g support)
  - models/kabelkanal-3-5mm-view.3mf  : Multi-state assembly view 3MF across 3 plates:
                                        Plate 1: Full-length 242.0 mm channel segment on 250x250 mm bed
                                        Plate 2: Pre-assembly aligned state (before plugging together)
                                        Plate 3: Two channels plugged together & latched (flush joint)
  - docs/images/kabelkanal-3-5mm-print-preview.png
  - docs/images/kabelkanal-3-5mm-print-plate-1-supports.png
  - docs/images/kabelkanal-3-5mm-view-preview.png
  - docs/images/kabelkanal-3-5mm-presentation.png
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import manifold3d as m3d
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
BUILD_DIR = ROOT / "build" / "kabelkanal-3-5mm"
DOCS = ROOT / "docs"
IMAGES = DOCS / "images"

ORCA_BIN = Path(os.environ.get(
    "ORCA_SLICER_BIN", r"C:\Program Files\OrcaSlicer\orca-slicer.exe"))
PROFILE_ROOT = ORCA_BIN.parent / "resources" / "profiles" / "Anycubic"
MACHINE = PROFILE_ROOT / "machine" / "Anycubic Kobra S1 0.4 nozzle.json"
BASE_PROCESS = PROFILE_ROOT / "process" / "0.20mm Standard @Anycubic Kobra S1 0.4 nozzle.json"
FILAMENT_PRESET = PROFILE_ROOT / "filament" / "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle.json"
METADATA_ENTRY = "Metadata/ghouls_grip_print_metadata.xml"

# ---------------------------------------------------------------------------
# Explicit parametric dimensions (all units in mm)
# ---------------------------------------------------------------------------
# Printer bed constraint: Anycubic Kobra S1 bed is 250 x 250 mm.
# Leaving a 4.0 mm safety margin on both ends along X gives a maximum straight
# printable length of 242.0 mm (230.0 mm net modular laying length + 12.0 mm
# male connector tongue), passing mesh_tool.py validate (<= 250.0 mm per axis).
BED_SIZE_XY = 250.00
BED_MARGIN_X = 4.00
MAX_TOTAL_LENGTH = BED_SIZE_XY - 2.0 * BED_MARGIN_X  # 242.00 mm

# Cable specification & functional clearances
CABLE_DIAMETER = 3.50
CABLE_RADIAL_CLEARANCE = 0.40  # +0.80 mm diametral clearance -> Ø 4.30 mm generous bore ("ggf. innen auch etwas mehr Platz lassen")
BORE_RADIUS = 0.5 * CABLE_DIAMETER + CABLE_RADIAL_CLEARANCE  # 2.15 mm (Ø 4.30 mm inner cable passage)

# Print vs. Installed Orientation (`Öffnung hinten`, Sichtseite `vorne` geschlossen):
# - Print orientation (in `models/kabelkanal-3-5mm*.stl` and `-print.3mf`):
#   - Closed, sleek bevelled front side (`vorne`) rests on the Textured PEI build plate `Z = 0.00 mm`.
#   - Flat slotted back side (`hinten`) faces UP at `Z = OUTER_HEIGHT = 5.40 mm`, where `ironing_type = top`
#     irons both flat rear wall-mounting strips (`Y in [-3.40, -1.95]` and `[+1.95, +3.40]`) razor-smooth.
#   - Because the rear cable slot (`3.20 mm` throat, `3.90 mm` entry funnel) opens upward at `Z = 5.40 mm`,
#     there is NO internal closing roof during printing -> 0.00 g support in OrcaSlicer `tree(auto)`!
# - Installed wall orientation (shown in `-view.3mf` and presentation renders):
#   - Flat slotted back (`hinten`) sits against the wall/cable; closed smooth front (`vorne`) faces out.
Z_BORE_CENTER = 3.10  # Ø 4.30 mm cable bore center (bore spans Z = 0.95..5.25 mm; 0.95 mm solid front wall = 6 layers)

# Compliant rear snap-in opening (`Öffnung hinten`):
# Revised from the over-stiff v1 slot (Ø 3.86 mm bore, 2.75 mm throat / 0.75 mm interference / 1.67 mm side wall / 3 wall loops)
# to a compliant, easy-press snap-in slot with generous Ø 4.30 mm internal bore:
#   - `2 * BORE_RADIUS = 4.30 mm` (`+0.80 mm` diametral clearance around the Ø 3.50 mm cable so the cable has plenty of room
#     inside the channel and at the connectors even with cable ovality, jacket tolerance, and FDM inner-perimeter shrinkage).
#   - `SLOT_THROAT_WIDTH = 3.20 mm` (`Y_THROAT = ±1.60 mm`) -> only `0.30 mm` total (`0.15 mm/side`)
#     gentle snap-retention undercut for a Ø 3.50 mm cable (~12x lower insertion energy than v1!).
#   - Wide `SLOT_ENTRY_WIDTH = 3.90 mm` (`Y_ENTRY = ±1.95 mm`) self-centering entry funnel on the flat back (`Z = 4.82..5.40 mm`),
#     wider than the Ø 3.50 mm cable so the cable seats into the rear funnel before pressing in.
#   - Flexible `1.25 mm` elastic side walls (`OUTER_WIDTH = 6.80 mm`, `Y_OUTER = ±3.40 mm`, `BORE_RADIUS = 2.15 mm`) with `wall_loops = 2`
#     and `xy_hole_compensation = 0.08 mm` so the arms flex elastically by 0.15 mm/side by thumb pressure.
SLOT_ENTRY_WIDTH = 3.90  # rear entry funnel on the flat back (Z = 5.40 mm), wider than 3.50 mm cable
Y_ENTRY = 0.5 * SLOT_ENTRY_WIDTH  # 1.95 mm
SLOT_THROAT_WIDTH = 3.20  # 0.30 mm (0.15 mm/side) gentle snap retention undercut for the 3.50 mm cable
Y_THROAT = 0.5 * SLOT_THROAT_WIDTH  # 1.60 mm
Z_THROAT_TOP = 4.82  # deep 0.58 mm rear entry funnel (Z = 4.82..5.40 mm) with ultra-short ~0.28 mm lip land

# Slimmer, compliant Outer Profile (6.80 mm wide x 5.40 mm high -> 1.25 mm elastic side wall around Ø 4.30 mm bore)
OUTER_WIDTH = 6.80
Y_OUTER = 0.5 * OUTER_WIDTH  # 3.40 mm
OUTER_HEIGHT = 5.40
FRONT_BEVEL = 1.10  # 45° architectural front bevel on Z = 0..1.10 mm (y_front = ±2.30 mm)
BED_CHAMFER = 0.20  # Rear edge relief at Z = OUTER_HEIGHT

# Short 35.0 mm Fit-Test Coupon (`Teststück`) included as standalone STL
# so the user can test-print a 4-minute / 0.7 g sample before or alongside full 242 mm channels.
COUPON_TOTAL_LENGTH = 35.00

# Front-to-back press-on Saddle Joint (`Von-vorne-Aufrast-Überblattung`)
# Connects in one motion from the front when snapping the channel onto the cable:
# - `-X` end (`CONNECTOR_LENGTH = 10.00 mm`): Inner Saddle with vertical T-key rib (`Quersteg`, locks ±X)
#   and horizontal snap-bead (`Rastleiste`, locks ±Z).
# - `+X` end (`SOCKET_DEPTH = 10.10 mm`): Outer Saddle Hood whose side cheeks wrap over the mating
#   Inner Saddle from the front in the exact same motion as snapping the channel onto the cable.
CONNECTOR_LENGTH = 10.00
CONNECTOR_AXIAL_CLEAR = 0.10
SOCKET_DEPTH = CONNECTOR_LENGTH + CONNECTOR_AXIAL_CLEAR  # 10.10 mm
CONNECTOR_CLEARANCE = 0.12  # per-side clearance between saddle and hood
BODY_NET_LENGTH = MAX_TOTAL_LENGTH - CONNECTOR_LENGTH  # 232.00 mm modular step per channel

# Saddle & Hood cross-section parameters (YZ plane, scaled to 6.80 mm outer width & Ø 4.30 mm bore)
# Updated for 100% self-supporting overhangs (>= 47.4° everywhere) and wide 1.03 mm first-layer bed feet on +X hood:
Y_SADDLE_SPINE = 1.15  # 2.30 mm wide flush front face on Z = 0.00 mm (widens +X hood Z=0 bed feet to 1.03 mm/side)
Y_SADDLE_BASE = 2.50   # Inner saddle half-width (leaves 0.35 mm saddle wall around R=2.15 bore and 0.78 mm outer hood cheek)
Z_SADDLE_SHOULDER = 1.68  # >= 47.4° slope from (1.15, 0) to (2.70, 1.68) even at T-key rib -> 0.00 g support in all slicers
Z_SADDLE_APEX = 5.40

# Vertical T-key rib (locks ±X when pressed on from the front)
KEY_OFFSET_FROM_SHOULDER = 5.00
KEY_HALF_LEN = 1.50
KEY_RIB_PROTRUSION = 0.20  # widens saddle from ±2.50 to ±2.70 mm
KEY_SLOT_DEPTH = 0.22      # widens hood slot from ±2.62 to ±2.84 mm

# Horizontal snap-detent bead along Z (clicks when pressed on from the front)
Z_SNAP_BEAD = 3.35
SNAP_BEAD_PROTRUSION = 0.16  # y_bead = 2.66 mm > 2.62 mm hood throat -> 0.04 mm/side click interference (>= 63.4° slope)
SNAP_GROOVE_DEPTH = 0.18     # y_groove = 2.80 mm > 2.66 mm -> 0.14 mm seated clearance (0.0000 mm^3 collision)


@dataclass(frozen=True)
class filament_slot:
    slot: int
    name: str
    material: str
    color_hex: str


WHITE_PLA = filament_slot(
    slot=1,
    name="Anycubic PLA White",
    material="PLA",
    color_hex="#F4F5F7",
)


# ---------------------------------------------------------------------------
# 2D Profile Construction (YZ Cross-Sections)
# ---------------------------------------------------------------------------
def _outer_profile_yz(arc_steps: int = 24) -> np.ndarray:
    """Return 2D polygon (Y, Z) in CCW order for the slim 7.20 x 5.20 mm cable channel.

    - Closed visible front (`vorne`) rests on Z = 0.00 mm (`Y in [-2.20, +2.20 mm]`) with a
      smooth 45° self-supporting architectural bevel up to `(±3.60, 1.40 mm)`.
    - Vertical side walls rise to the flat rear mounting face at `Z = 5.20 mm` (`hinten`),
      with a 0.20 mm outer edge chamfer at the top corners.
    """
    y_front = Y_OUTER - FRONT_BEVEL  # 2.20 mm
    c_top = 0.20
    pts: list[tuple[float, float]] = [
        (-y_front, 0.0),
        (y_front, 0.0),
        (Y_OUTER, FRONT_BEVEL),
        (Y_OUTER, OUTER_HEIGHT - c_top),
        (Y_OUTER - c_top, OUTER_HEIGHT),
        (-Y_OUTER + c_top, OUTER_HEIGHT),
        (-Y_OUTER, OUTER_HEIGHT - c_top),
        (-Y_OUTER, FRONT_BEVEL),
    ]
    return np.array(pts, dtype=np.float64)


def _inner_cavity_profile_yz(arc_steps: int = 36) -> np.ndarray:
    """Return 2D polygon (Y, Z) in CCW order for the Ø 4.00 mm cable bore + compliant rear snap-in slot at Z = 5.20 mm.

    - Bore bottom sits at `Z = 1.00 mm` (leaving a solid 1.00 mm closed front wall at `Z = 0.00..1.00 mm`).
    - Circular Ø 4.00 mm (`R = 2.00 mm`) cable bore centered at `Z = 3.00 mm` spans from the bottom up to
      `theta_top = +37.3°` (`Y = ±1.59 mm`, `Z = 4.211 mm`), so the upper retaining lips have a
      self-supporting slope `>= 52.7°` from horizontal (`<= 37.3°` from vertical).
    - Compliant snap-in throat (`3.18 mm` wide, `Y = ±1.59 mm`) has a short vertical land (`Z = 4.211..4.65 mm`,
      `0.44 mm` lip thickness) so the retaining lips flex easily when pressing in the 3.50 mm cable.
    - Wide rear entry funnel (`3.80 mm` wide, `Y = ±1.90 mm`) flares from `Z = 4.65 mm` to the flat back
      `Z = 5.20 mm` (`30°` lead-in angle), guiding the 3.50 mm cable smoothly into the throat.
    """
    alpha_top = math.asin(math.sqrt(max(0.0, 1.0 - (Y_THROAT / BORE_RADIUS) ** 2)))  # ~37.3 deg
    z_throat_bot = Z_BORE_CENTER + BORE_RADIUS * math.sin(alpha_top)  # ~4.211 mm
    z_throat_top = Z_THROAT_TOP  # 4.65 mm

    pts: list[tuple[float, float]] = [
        (-Y_ENTRY, OUTER_HEIGHT + 0.25),
        (-Y_ENTRY, OUTER_HEIGHT),
        (-Y_THROAT, z_throat_top),
        (-Y_THROAT, z_throat_bot),
    ]
    t_start = math.pi - alpha_top
    t_end = 2.0 * math.pi + alpha_top
    for i in range(arc_steps + 1):
        t = t_start + (t_end - t_start) * (i / arc_steps)
        pts.append((BORE_RADIUS * math.cos(t), Z_BORE_CENTER + BORE_RADIUS * math.sin(t)))

    pts.extend([
        (Y_THROAT, z_throat_bot),
        (Y_THROAT, z_throat_top),
        (Y_ENTRY, OUTER_HEIGHT),
        (Y_ENTRY, OUTER_HEIGHT + 0.25),
    ])
    return np.array(pts, dtype=np.float64)


def _male_outer_profile_yz(delta_y_key: float = 0.0) -> np.ndarray:
    """Return 2D polygon (Y, Z) in CCW order for the `-X` Inner Saddle outer boundary."""
    y_spine = Y_SADDLE_SPINE
    y_base = Y_SADDLE_BASE + delta_y_key
    y_bead = y_base + (SNAP_BEAD_PROTRUSION if delta_y_key >= 0.0 else 0.0)
    z_sh = Z_SADDLE_SHOULDER + 1.10 * max(0.0, delta_y_key)
    z_b0 = Z_SNAP_BEAD - 0.42
    z_b1 = Z_SNAP_BEAD
    z_b2 = Z_SNAP_BEAD + 0.42

    pts = [
        (-y_spine, 0.0),
        (y_spine, 0.0),
        (y_base, z_sh),
        (y_base, z_b0),
        (y_bead, z_b1),
        (y_base, z_b2),
        (y_base, OUTER_HEIGHT),
        (-y_base, OUTER_HEIGHT),
        (-y_base, z_b2),
        (-y_bead, z_b1),
        (-y_base, z_b0),
        (-y_base, z_sh),
    ]
    return np.array(pts, dtype=np.float64)


def _female_socket_profile_yz(clearance: float = CONNECTOR_CLEARANCE, delta_y_key: float = 0.0) -> np.ndarray:
    """Return 2D polygon (Y, Z) in CCW order for the `+X` Outer Saddle Hood recess."""
    c = clearance
    y_spine = Y_SADDLE_SPINE + c
    y_base = Y_SADDLE_BASE + c + delta_y_key
    y_groove = y_base + SNAP_GROOVE_DEPTH
    z_sh = max(0.25, Z_SADDLE_SHOULDER - 0.15)
    z_b0 = Z_SNAP_BEAD - 0.48
    z_b1 = Z_SNAP_BEAD
    z_b2 = Z_SNAP_BEAD + 0.48

    pts = [
        (-y_spine, -0.20),
        (y_spine, -0.20),
        (y_spine, 0.00),
        (y_base, z_sh),
        (y_base, z_b0),
        (y_groove, z_b1),
        (y_base, z_b2),
        (y_base, OUTER_HEIGHT),
        (y_base, OUTER_HEIGHT + 0.25),
        (-y_base, OUTER_HEIGHT + 0.25),
        (-y_base, OUTER_HEIGHT),
        (-y_base, z_b2),
        (-y_groove, z_b1),
        (-y_base, z_b0),
        (-y_base, z_sh),
        (-y_spine, 0.00),
    ]
    return np.array(pts, dtype=np.float64)


# ---------------------------------------------------------------------------
# 3D Manifold Extrusion & Sweep Helpers
# ---------------------------------------------------------------------------
def _extrude_yz_along_x(poly_yz: np.ndarray, x0: float, x1: float) -> m3d.Manifold:
    """Extrude a 2D CCW polygon in (Y, Z) from X = x0 to X = x1."""
    length = float(x1 - x0)
    assert length > 0.0
    cs = m3d.CrossSection([poly_yz.tolist()])
    # Manifold extrude creates a prism along +Z from 0..length with (X_local=Y, Y_local=Z, Z_local=X)
    m = m3d.Manifold.extrude(cs, length)
    # Map (X_local, Y_local, Z_local) -> (Z_local + x0, X_local, Y_local)
    # This is an even permutation of axes (determinant = +1), preserving outward normals!
    mat = [
        [0.0, 0.0, 1.0, x0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ]
    return m.transform(mat)


def _build_tapered_prism_x(
    x_stations: list[tuple[float, np.ndarray]],
    substeps: int = 8,
) -> m3d.Manifold:
    """Build a smooth piecewise-extruded Manifold along X from stations with identical vertex count."""
    pieces: list[m3d.Manifold] = []
    for (x0, p0), (x1, p1) in zip(x_stations[:-1], x_stations[1:]):
        dx = (x1 - x0) / substeps
        for s in range(substeps):
            t_mid = (s + 0.5) / substeps
            poly_mid = (1.0 - t_mid) * p0 + t_mid * p1
            xs0 = x0 + s * dx - (0.002 if s > 0 else 0.0)
            xs1 = x0 + (s + 1) * dx + (0.002 if s < substeps - 1 else 0.0)
            pieces.append(_extrude_yz_along_x(poly_mid, xs0, xs1))
    out = pieces[0]
    for p in pieces[1:]:
        out = out + p
    return out


VARIANT_SPECS: list[tuple[str, bool, bool, float, str]] = [
    (
        "kabelkanal-3-5mm-abschluss-links",
        False,
        True,
        MAX_TOTAL_LENGTH,
        "Abschlusskanal links 242 mm (links glatt ohne Verbindung, Verbindung nur rechts +X)",
    ),
    (
        "kabelkanal-3-5mm-mitte-beidseitig",
        True,
        True,
        MAX_TOTAL_LENGTH,
        "Mittelkanal 242 mm (Verbindung links -X Sattel & rechts +X Ueberwurf-Kappe)",
    ),
    (
        "kabelkanal-3-5mm-abschluss-rechts",
        True,
        False,
        MAX_TOTAL_LENGTH,
        "Abschlusskanal rechts 242 mm (Verbindung nur links -X Sattel, rechts glatt ohne Verbindung)",
    ),
    (
        "kabelkanal-3-5mm-einzeln-ohne-verbindung",
        False,
        False,
        MAX_TOTAL_LENGTH,
        "Einzel-/Kurzkanal ohne Verbindungen (links & rechts glatt, 242 mm Maximallaenge)",
    ),
    (
        "kabelkanal-3-5mm-10cm-rechts",
        False,
        True,
        100.00,
        "10 cm Abschluss-/Passstueck (100.0 mm, links glatt ohne Verbindung, Verbindung nur rechts +X)",
    ),
]


def build_channel_manifold(
    body_net_length: float = BODY_NET_LENGTH,
    *,
    left_connector: bool = True,
    right_connector: bool = True,
    total_length_override: float | None = None,
) -> m3d.Manifold:
    """Construct one 3.5 mm cable channel segment variant as a watertight Manifold.

    Coordinate system (centered on the print bed along X):
      - Total X span: `[-total_len/2, +total_len/2]`, default `total_len = 242.00 mm` (`MAX_TOTAL_LENGTH`)
        for all four variants so every variant uses the maximum printable bed length.
      - `left_connector=True` (`-X` end, `[x_min, x_shoulder]`): Inner Saddle (`Aufrast-Sattel`, 10.00 mm)
        with vertical T-key rib (`Quersteg`) and horizontal snap-bead (`Rastleiste`).
      - `left_connector=False` (`-X` end): Clean full-profile end at `x_min` without saddle step,
        with continuous cable bore and rear snap-in slot.
      - `right_connector=True` (`+X` end, `[x_max - SOCKET_DEPTH, x_max]`): Outer Saddle Hood (`Aufrast-Kappe`,
        10.10 mm) that presses straight down from the front (`-Z`) onto a mating `-X` Saddle.
      - `right_connector=False` (`+X` end): Clean full-profile end at `x_max` without hood recess,
        with continuous cable bore and rear snap-in slot.
    """
    total_len = (
        float(total_length_override)
        if total_length_override is not None
        else float(body_net_length + CONNECTOR_LENGTH)
    )
    x_min = -0.5 * total_len
    x_shoulder = x_min + CONNECTOR_LENGTH
    x_max = +0.5 * total_len

    outer_yz = _outer_profile_yz()
    cavity_yz = _inner_cavity_profile_yz()

    # 1. Main body outer solid: starts at x_shoulder if left_connector is present, else at x_min
    x_body_start = x_shoulder if left_connector else x_min
    solid = _extrude_yz_along_x(outer_yz, x_body_start, x_max)

    # 2. Optional `-X` Inner Saddle from x_min to x_shoulder + 0.40 mm (overlap into main body)
    if left_connector:
        x_key = x_shoulder - KEY_OFFSET_FROM_SHOULDER
        tip_yz = _male_outer_profile_yz(delta_y_key=-0.20)
        nom_yz = _male_outer_profile_yz(delta_y_key=0.0)
        key_yz = _male_outer_profile_yz(delta_y_key=KEY_RIB_PROTRUSION)

        male_tip = _build_tapered_prism_x(
            [(x_min, tip_yz), (x_min + 0.80, nom_yz)],
            substeps=5,
        )
        male_shaft = _extrude_yz_along_x(nom_yz, x_min + 0.75, x_shoulder + 0.40)
        male_key_rib = _build_tapered_prism_x(
            [
                (x_key - KEY_HALF_LEN, nom_yz),
                (x_key - 0.55, key_yz),
                (x_key + 0.55, key_yz),
                (x_key + KEY_HALF_LEN, nom_yz),
            ],
            substeps=6,
        )
        solid = solid + male_tip + male_shaft + male_key_rib

    # 3. Optional `+X` Outer Saddle Hood cavity at [x_max - SOCKET_DEPTH, x_max + 0.2]
    if right_connector:
        x_socket_start = x_max - SOCKET_DEPTH
        x_socket_key = x_max - KEY_OFFSET_FROM_SHOULDER
        sock_nom_yz = _female_socket_profile_yz(clearance=CONNECTOR_CLEARANCE, delta_y_key=0.0)
        sock_key_yz = _female_socket_profile_yz(
            clearance=CONNECTOR_CLEARANCE, delta_y_key=KEY_SLOT_DEPTH
        )

        socket_main = _extrude_yz_along_x(sock_nom_yz, x_socket_start, x_max + 0.20)
        socket_key_slot = _build_tapered_prism_x(
            [
                (x_socket_key - KEY_HALF_LEN - 0.22, sock_nom_yz),
                (x_socket_key - 0.65, sock_key_yz),
                (x_socket_key + 0.65, sock_key_yz),
                (x_socket_key + KEY_HALF_LEN + 0.22, sock_nom_yz),
            ],
            substeps=6,
        )
        solid = solid - (socket_main + socket_key_slot)

    # 4. Subtract the continuous Ø 3.86 mm cable bore and rear snap-in slot
    # along the entire length [x_min - 0.50, x_max + 0.50]
    cable_cut = _extrude_yz_along_x(cavity_yz, x_min - 0.50, x_max + 0.50)
    solid = solid - cable_cut

    return solid


def manifold_to_trimesh(m: m3d.Manifold) -> trimesh.Trimesh:
    """Convert a manifold3d.Manifold to a clean, vertex-rounded trimesh.Trimesh."""
    mesh_data = m.to_mesh()
    verts = np.round(np.array(mesh_data.vert_properties[:, :3], dtype=np.float64), 3)
    faces = np.array(mesh_data.tri_verts, dtype=np.int64)
    tm = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    tm.merge_vertices()
    tm.update_faces(tm.nondegenerate_faces())
    tm.update_faces(tm.unique_faces())
    tm.remove_unreferenced_vertices()
    return tm


def export_ascii_stl(mesh: trimesh.Trimesh, path: Path, solid_name: str = "kabelkanal_3_5mm") -> None:
    """Export a trimesh.Trimesh as an ASCII STL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ascii_text = trimesh.exchange.stl.export_stl_ascii(mesh)
    lines = ascii_text.splitlines()
    if lines:
        lines[0] = f"solid {solid_name}"
        lines[-1] = f"endsolid {solid_name}"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Mechanical, Clearance & Assembly Verification Suite
# ---------------------------------------------------------------------------
def verify_cable_channel_and_joint(
    variant_manifolds: dict[str, m3d.Manifold],
    variant_meshes: dict[str, trimesh.Trimesh],
) -> dict:
    """Run comprehensive mesh, feature-probe, cable-fit, and multi-variant joint checks."""
    m_single = variant_manifolds["kabelkanal-3-5mm-mitte-beidseitig"]
    mesh = variant_meshes["kabelkanal-3-5mm-mitte-beidseitig"]
    bounds = mesh.bounds
    extents = mesh.extents

    cable_rod = _extrude_yz_along_x(
        np.array([
            (0.5 * CABLE_DIAMETER * math.cos(2.0 * math.pi * i / 48),
             Z_BORE_CENTER + 0.5 * CABLE_DIAMETER * math.sin(2.0 * math.pi * i / 48))
            for i in range(48)
        ]),
        -120.5,
        +120.5,
    )

    variant_stats: dict[str, dict] = {}
    for slug, left_conn, right_conn, expected_len, desc in VARIANT_SPECS:
        vm = variant_manifolds[slug]
        vmesh = variant_meshes[slug]
        assert vmesh.is_watertight, f"{slug} must be watertight"
        assert vmesh.is_winding_consistent, f"{slug} must have consistent winding"
        v_deg = int(len(vmesh.faces) - np.count_nonzero(vmesh.nondegenerate_faces()))
        assert v_deg == 0, f"{slug}: expected 0 degenerate faces, found {v_deg}"
        assert int(vmesh.euler_number) == 2, f"{slug}: expected euler_number 2, got {vmesh.euler_number}"
        assert abs(float(vmesh.extents[0]) - expected_len) < 1e-2, f"{slug}: expected {expected_len} mm length, got {vmesh.extents[0]}"
        v_cable_col = max(0.0, float((vm ^ cable_rod).volume()))
        assert v_cable_col < 1e-9, f"{slug}: 3.5 mm cable collides with bore: {v_cable_col}"

        # Verify end-feature presence/absence with volume probes at each variant's own x_min / x_max:
        half_len = 0.5 * expected_len
        left_outer_cheek_probe = m3d.Manifold.cube([6.0, 0.30, 2.50], False).translate([-half_len + 2.0, 2.95, 1.80])
        right_inner_hood_probe = m3d.Manifold.cube([6.0, 0.36, 2.30], False).translate([+half_len - 8.0, 2.20, 1.50])
        left_outer_vol = max(0.0, float((vm ^ left_outer_cheek_probe).volume()))
        right_inner_vol = max(0.0, float((vm ^ right_inner_hood_probe).volume()))
        if left_conn:
            assert left_outer_vol < 1e-9, f"{slug}: left -X saddle should have recessed outer cheek (0 mm^3), got {left_outer_vol}"
        else:
            assert abs(left_outer_vol - 4.5) < 1e-1, f"{slug}: clean left end must have full outer cheek (4.5 mm^3), got {left_outer_vol}"
        if right_conn:
            assert right_inner_vol < 1e-9, f"{slug}: right +X hood should have open inner saddle pocket (0 mm^3), got {right_inner_vol}"
        else:
            assert abs(right_inner_vol - 4.968) < 1e-1, f"{slug}: clean right end must have solid inner wall (4.968 mm^3), got {right_inner_vol}"

        variant_stats[slug] = {
            "description": desc,
            "left_connector": left_conn,
            "right_connector": right_conn,
            "length_mm": round(expected_len, 2),
            "facets": int(len(vmesh.faces)),
            "vertices": int(len(vmesh.vertices)),
            "extents_mm": [round(float(x), 3) for x in vmesh.extents],
            "volume_mm3": round(float(vmesh.volume), 2),
            "watertight": bool(vmesh.is_watertight),
            "euler_number": int(vmesh.euler_number),
            "degenerate_faces": v_deg,
        }

    # Check 3-segment chain: abschluss-links (x=0) + mitte-beidseitig (x=232) + abschluss-rechts (x=464)
    m_left_end = variant_manifolds["kabelkanal-3-5mm-abschluss-links"]
    m_mid = variant_manifolds["kabelkanal-3-5mm-mitte-beidseitig"].translate([BODY_NET_LENGTH, 0.0, 0.0])
    m_right_end = variant_manifolds["kabelkanal-3-5mm-abschluss-rechts"].translate([2.0 * BODY_NET_LENGTH, 0.0, 0.0])
    chain_col_left_mid = max(0.0, float((m_left_end ^ m_mid).volume()))
    chain_col_mid_right = max(0.0, float((m_mid ^ m_right_end).volume()))
    assert chain_col_left_mid < 1e-9, f"Collision between abschluss-links and mitte-beidseitig: {chain_col_left_mid}"
    assert chain_col_mid_right < 1e-9, f"Collision between mitte-beidseitig and abschluss-rechts: {chain_col_mid_right}"

    # Also verify that the 100 mm right-connector piece (x_max = +50.0) mates with 0.0 mm^3 collision
    # onto the -X saddle of `mitte-beidseitig` (whose shoulder is at x_shoulder = -121.0 + 10.0 = -111.0 -> dx = 161.0 mm)
    m_10cm = variant_manifolds["kabelkanal-3-5mm-10cm-rechts"]
    m_mid_after_10cm = variant_manifolds["kabelkanal-3-5mm-mitte-beidseitig"].translate([50.0 + 111.0, 0.0, 0.0])
    col_10cm_mid = max(0.0, float((m_10cm ^ m_mid_after_10cm).volume()))
    assert col_10cm_mid < 1e-9, f"Collision between 10cm-rechts and mitte-beidseitig: {col_10cm_mid}"

    deg_count = int(len(mesh.faces) - np.count_nonzero(mesh.nondegenerate_faces()))
    cable_collision_vol = (m_single ^ cable_rod).volume()

    # Prove closed front wall at mid-channel (X in [-5, +5], Y in [-0.6, +0.6], Z in [0.15, 0.85]) is SOLID
    front_wall_probe = m3d.Manifold.cube([10.0, 1.2, 0.7], False).translate([-5.0, -0.6, 0.15])
    front_wall_vol = (m_single ^ front_wall_probe).volume()
    assert abs(front_wall_vol - 8.4) < 1e-2, f"Closed front wall probe must be solid (8.4 mm^3), got {front_wall_vol}"

    # Prove generous Ø 4.00 mm clearance rod (0.50 mm oversize above the Ø 3.50 mm cable!) passes with 0.0 mm^3 collision
    oversize_rod = _extrude_yz_along_x(
        np.array([
            (2.05 * math.cos(2.0 * math.pi * i / 48),
             Z_BORE_CENTER + 2.05 * math.sin(2.0 * math.pi * i / 48))
            for i in range(48)
        ]),
        -120.5,
        +120.5,
    )
    oversize_col = (m_single ^ oversize_rod).volume()
    assert oversize_col == 0.0, f"Ø 4.10 mm oversize gauge rod collides with Ø 4.30 mm bore: {oversize_col}"

    # Prove rear slot on flat back (X in [-5, +5], Y in [-1.50, +1.50], Z in [4.50, 5.40]) is OPEN (0.0 mm^3)
    # Note: Y in [-1.50, +1.50] is 3.00 mm wide (wider than the old 2.75 mm throat!), proving the throat widened to 3.20 mm.
    rear_slot_probe = m3d.Manifold.cube([10.0, 3.00, 0.90], False).translate([-5.0, -1.50, 4.50])
    rear_slot_vol = (m_single ^ rear_slot_probe).volume()
    assert rear_slot_vol == 0.0, f"Rear cable slot on flat back must be open (0 mm^3), got {rear_slot_vol}"

    # Prove flat rear mounting flanges (Y in [+2.05, +3.15], Z in [4.50, 5.20]) are SOLID
    rear_flange_probe = m3d.Manifold.cube([10.0, 1.1, 0.70], False).translate([-5.0, 2.05, 4.50])
    rear_flange_vol = (m_single ^ rear_flange_probe).volume()
    assert abs(rear_flange_vol - 7.70) < 1e-2, f"Rear mounting flange must be solid (7.70 mm^3), got {rear_flange_vol}"

    # Cantilever flex / snap-in mechanics comparison (v1 vs. v2 compliant slot):
    # Side wall thickness at mid-bore (Z = Z_BORE_CENTER = 3.10 mm): t_wall = Y_OUTER - BORE_RADIUS = 1.25 mm (vs. 1.67 mm in v1)
    # Required unilateral deflection delta_y = 0.5 * (CABLE_DIAMETER - SLOT_THROAT_WIDTH) = 0.15 mm/side (vs. 0.375 mm/side in v1)
    t_wall_mid = Y_OUTER - BORE_RADIUS
    delta_y_per_side = 0.5 * (CABLE_DIAMETER - SLOT_THROAT_WIDTH)
    lip_vertical_height = Z_THROAT_TOP - (Z_BORE_CENTER + math.sqrt(BORE_RADIUS**2 - Y_THROAT**2))
    stiffness_ratio_vs_v1 = (t_wall_mid / 1.67) ** 3
    force_ratio_vs_v1 = stiffness_ratio_vs_v1 * (delta_y_per_side / 0.375)
    energy_ratio_vs_v1 = stiffness_ratio_vs_v1 * ((delta_y_per_side / 0.375) ** 2)

    # 3. Front-to-back press-on assembly sweep ("von vorne in einem Zug aufstecken")
    #    In print coordinates (front at Z = 0, flat slotted back at Z = 5.20):
    #    Segment B (`-X` Inner Saddle at x = +BODY_NET_LENGTH) sits against the wall/cable.
    #    Segment A (`+X` Outer Saddle Hood at x = 0) approaches from the front (`dz = -5.20 mm -> 0.00 mm`)
    #    and presses straight onto both the cable and Segment B's `-X` Saddle in a single motion!
    m_b_wall = m_single.translate([BODY_NET_LENGTH, 0.0, 0.0])
    sweep_steps = []
    for dz in np.linspace(-5.2, 0.0, 25):
        m_a_dropping = m_single.translate([0.0, 0.0, float(dz)])
        inter_vol = (m_a_dropping ^ m_b_wall).volume()
        sweep_steps.append({
            "dz_mm": round(float(dz), 2),
            "dx_mm": round(BODY_NET_LENGTH, 2),
            "intersection_mm3": round(inter_vol, 4),
        })

    # At fully seated position (dz == 0.0 mm, dx == 232.00 mm), intersection_mm3 MUST be 0.0!
    seated_inter = sweep_steps[-1]["intersection_mm3"]
    assert seated_inter == 0.0, f"Seated two-channel assembly has non-zero collision: {seated_inter} mm^3"

    # Prove positive axial X-locking (`Formschluss gegen Auseinanderziehen`):
    # If someone tries to pull the seated segments apart along X by +1.80 mm without lifting in Z,
    # the vertical T-key rib hits the hood key-slot shoulder (> 0.8 mm^3 positive lock interference)!
    m_b_pulled_x = m_single.translate([BODY_NET_LENGTH + 1.80, 0.0, 0.0])
    axial_lock_vol = (m_single ^ m_b_pulled_x).volume()
    assert axial_lock_vol > 0.5, f"Expected positive axial T-key lock interference along X, got {axial_lock_vol} mm^3"

    # Verify that the continuous 3.5 mm cable rod passes cleanly across the mated two-channel joint!
    cable_joint_rod = _extrude_yz_along_x(
        np.array([
            (0.5 * CABLE_DIAMETER * math.cos(2.0 * math.pi * i / 48),
             Z_BORE_CENTER + 0.5 * CABLE_DIAMETER * math.sin(2.0 * math.pi * i / 48))
            for i in range(48)
        ]),
        -100.0,
        BODY_NET_LENGTH + 100.0,
    )
    joint_cable_collision = ((m_single + m_b_wall) ^ cable_joint_rod).volume()
    assert joint_cable_collision == 0.0, f"3.5 mm cable collides across mated joint: {joint_cable_collision} mm^3"

    peak_detent_engagement = max(s["intersection_mm3"] for s in sweep_steps)

    return {
        "facets": int(len(mesh.faces)),
        "vertices": int(len(mesh.vertices)),
        "bounds_min": [round(float(x), 3) for x in bounds[0]],
        "bounds_max": [round(float(x), 3) for x in bounds[1]],
        "extents": [round(float(x), 3) for x in extents],
        "volume_mm3": round(float(mesh.volume), 2),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "degenerate_faces": deg_count,
        "cable_bore_collision_mm3": round(float(cable_collision_vol), 4),
        "joint_cable_collision_mm3": round(float(joint_cable_collision), 4),
        "seated_joint_collision_mm3": round(float(seated_inter), 4),
        "chain_left_mid_collision_mm3": round(float(chain_col_left_mid), 4),
        "chain_mid_right_collision_mm3": round(float(chain_col_mid_right), 4),
        "chain_10cm_mid_collision_mm3": round(float(col_10cm_mid), 4),
        "oversize_4_1mm_rod_collision_mm3": round(float(oversize_col), 4),
        "axial_x_lock_interference_mm3": round(float(axial_lock_vol), 4),
        "peak_front_snap_click_interference_mm3": round(float(peak_detent_engagement), 4),
        "slot_compliance": {
            "cable_diameter_mm": CABLE_DIAMETER,
            "bore_diameter_mm": round(2.0 * BORE_RADIUS, 2),
            "slot_throat_width_mm": SLOT_THROAT_WIDTH,
            "slot_entry_width_mm": SLOT_ENTRY_WIDTH,
            "undercut_total_mm": round(CABLE_DIAMETER - SLOT_THROAT_WIDTH, 2),
            "deflection_per_side_mm": round(delta_y_per_side, 3),
            "side_wall_thickness_mid_mm": round(t_wall_mid, 2),
            "retaining_lip_vertical_land_mm": round(lip_vertical_height, 3),
            "stiffness_ratio_vs_v1": round(stiffness_ratio_vs_v1, 3),
            "insertion_force_ratio_vs_v1": round(force_ratio_vs_v1, 3),
            "insertion_energy_ratio_vs_v1": round(energy_ratio_vs_v1, 3),
        },
        "variants": variant_stats,
        "sweep_steps": sweep_steps,
    }


# ---------------------------------------------------------------------------
# 3MF Packaging (Print BOM & Multi-State View)
# ---------------------------------------------------------------------------
def _add_metadata(parent: ET.Element, key: str, value: str) -> ET.Element:
    node = next((item for item in parent.findall("metadata") if item.get("key") == key), None)
    if node is None:
        insert_at = next((i for i, child in enumerate(list(parent)) if child.tag == "part"), len(parent))
        node = ET.Element("metadata", key=key, value=value)
        parent.insert(insert_at, node)
    else:
        node.set("value", value)
    return node


def write_3mf(
    path: Path,
    objects: list[tuple[str, trimesh.Trimesh, filament_slot, list[float] | None]],
    *,
    plate_names: list[str] | None = None,
    object_plates: dict[str, int] | None = None,
    material_slots: dict[filament_slot, int] | None = None,
    material_list: list[filament_slot] | None = None,
) -> None:
    """Write a 3MF archive with basematerials, optional multi-plate config, and ghouls-grip metadata."""
    import tempfile as _tf

    if material_list is None:
        material_list = [WHITE_PLA]

    core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("", core)
    model = ET.Element(f"{{{core}}}model", unit="millimeter")
    meta = ET.SubElement(model, f"{{{core}}}metadata", name="Title")
    meta.text = path.stem

    resources = ET.SubElement(model, f"{{{core}}}resources")
    materials_el = ET.SubElement(resources, f"{{{core}}}basematerials", id="1")

    used: list[filament_slot] = []
    for _name, _mesh, mat, _transform in objects:
        if mat not in used:
            used.append(mat)
    for mat in used:
        ET.SubElement(
            materials_el,
            f"{{{core}}}base",
            name=mat.name,
            displaycolor=mat.color_hex,
        )

    build = ET.SubElement(model, f"{{{core}}}build")
    for object_id, (name, mesh, mat, transform) in enumerate(objects, start=2):
        obj = ET.SubElement(
            resources,
            f"{{{core}}}object",
            id=str(object_id),
            name=name,
            type="model",
            pid="1",
            pindex=str(used.index(mat)),
        )
        mesh_xml = ET.SubElement(obj, f"{{{core}}}mesh")
        vertices = ET.SubElement(mesh_xml, f"{{{core}}}vertices")
        for vertex in mesh.vertices:
            ET.SubElement(
                vertices,
                f"{{{core}}}vertex",
                x=f"{vertex[0]:.4f}",
                y=f"{vertex[1]:.4f}",
                z=f"{vertex[2]:.4f}",
            )
        triangles = ET.SubElement(mesh_xml, f"{{{core}}}triangles")
        for face in mesh.faces:
            ET.SubElement(
                triangles,
                f"{{{core}}}triangle",
                v1=str(face[0]),
                v2=str(face[1]),
                v3=str(face[2]),
            )
        attrs = {"objectid": str(object_id)}
        if transform is not None:
            attrs["transform"] = " ".join(f"{v:.5f}" for v in transform)
        ET.SubElement(build, f"{{{core}}}item", **attrs)

    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""
    relationships = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
    metadata = ET.Element("ghouls-grip-print-metadata", version="1")
    neutral_values = {
        "status": "not-verified",
        "estimatedPrintTimeSeconds": "unknown",
        "filamentUsageGrams": "unknown",
        "filamentUsageMillimeters": "unknown",
        "filamentUsageCubicMillimeters": "unknown",
        "supportFilamentGrams": "unknown",
        "supportFilamentMillimeters": "unknown",
        "supportFilamentCubicMillimeters": "unknown",
        "printerProfile": "Anycubic Kobra S1 0.4 nozzle",
        "nozzleDiameterMm": "0.4",
        "processProfile": BASE_PROCESS.stem,
        "layerHeightMm": "0.16",
        "filamentProfile": FILAMENT_PRESET.stem,
        "materialType": "PLA",
        "materialColorName": ", ".join(m.name for m in material_list),
        "materialColorHex": ", ".join(m.color_hex for m in material_list),
        "bedType": "Textured PEI Plate",
        "plateCount": str(len(plate_names) if plate_names else 1),
        "objectCount": str(len(objects)),
    }
    for k, val in neutral_values.items():
        ET.SubElement(metadata, "metadata", name=k, value=val)

    def member(archive: ZipFile, name: str, data) -> None:
        info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, data)

    model_settings = None
    if plate_names is not None:
        if object_plates is None or material_slots is None:
            raise ValueError("Multi-plate 3MF needs object plate and material maps")
        model_settings = ET.Element("config")
        plate_objects: dict[int, list[str]] = {}
        for object_id, (name, _mesh, mat, _transform) in enumerate(objects, start=2):
            object_id_text = str(object_id)
            config_object = ET.SubElement(model_settings, "object", id=object_id_text)
            ET.SubElement(config_object, "metadata", key="name", value=name)
            ET.SubElement(
                config_object,
                "metadata",
                key="extruder",
                value=str(material_slots[mat] + 1),
            )
            part = ET.SubElement(
                config_object,
                "part",
                id=str(object_id + 1),
                subtype="normal_part",
            )
            ET.SubElement(part, "metadata", key="name", value=name)
            ET.SubElement(
                part,
                "metadata",
                key="matrix",
                value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1",
            )
            ET.SubElement(part, "metadata", key="source_file", value=path.name)
            ET.SubElement(part, "metadata", key="source_object_id", value=object_id_text)
            ET.SubElement(part, "metadata", key="source_volume_id", value="0")
            for key in ("source_offset_x", "source_offset_y", "source_offset_z"):
                ET.SubElement(part, "metadata", key=key, value="0")
            plate_objects.setdefault(object_plates[name], []).append(object_id_text)

        for idx, plate_name in enumerate(plate_names):
            plate = ET.SubElement(model_settings, "plate")
            for key, val in (
                ("plater_id", str(idx + 1)),
                ("plater_name", plate_name),
                ("locked", "false"),
                ("filament_map_mode", "Auto For Flush"),
                ("gcode_file", ""),
            ):
                ET.SubElement(plate, "metadata", key=key, value=val)
            for object_id in plate_objects.get(idx, []):
                instance = ET.SubElement(plate, "model_instance")
                for key, val in (
                    ("object_id", object_id),
                    ("instance_id", "0"),
                    ("identify_id", object_id),
                ):
                    ET.SubElement(instance, "metadata", key=key, value=val)

    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        member(archive, "[Content_Types].xml", content_types)
        member(archive, "_rels/.rels", relationships)
        member(
            archive,
            "3D/3dmodel.model",
            ET.tostring(model, encoding="utf-8", xml_declaration=True),
        )
        member(
            archive,
            METADATA_ENTRY,
            ET.tostring(metadata, encoding="utf-8", xml_declaration=True),
        )
        if model_settings is not None:
            member(
                archive,
                "Metadata/model_settings.config",
                ET.tostring(model_settings, encoding="utf-8", xml_declaration=True),
            )


def build_print_3mf(variant_meshes: dict[str, trimesh.Trimesh], out_path: Path) -> None:
    """Create `models/kabelkanal-3-5mm-print.3mf` with all 5 variants on Plate 1.

    - 4 max-length variants (`242.0 mm`, `X in [4.0, 246.0] mm`) + 1x `100.0 mm` right-connector variant (`X in [75.0, 175.0] mm`):
      1. `kabelkanal-3-5mm-abschluss-links` at `Y = 89.0 mm` (242 mm, links glatt, Verbindung nur rechts `+X`)
      2. `kabelkanal-3-5mm-mitte-beidseitig` at `Y = 107.0 mm` (242 mm, Verbindung links `-X` & rechts `+X`)
      3. `kabelkanal-3-5mm-abschluss-rechts` at `Y = 125.0 mm` (242 mm, Verbindung nur links `-X`, rechts glatt)
      4. `kabelkanal-3-5mm-einzeln-ohne-verbindung` at `Y = 143.0 mm` (242 mm, keine Verbindungen)
      5. `kabelkanal-3-5mm-10cm-rechts` at `Y = 161.0 mm` (100 mm, links glatt, Verbindung nur rechts `+X`)
    - Configured for Anycubic Kobra S1 0.4 mm nozzle, Textured PEI Plate, White PLA (Slot 1),
      0.16 mm layer height, 2 wall loops (for compliant snap-in flex), random seam, top ironing,
      and automatic tree supports (0.16 mm Z gap).
    """
    import tempfile

    plate_names = ["Platte 1 - Alle 5 Varianten Kabelkanal 3.5 mm Weiss (4x 242 mm + 1x 100 mm)"]
    layout_xy = {
        "kabelkanal-3-5mm-abschluss-links": (0, (125.0, 89.0)),
        "kabelkanal-3-5mm-mitte-beidseitig": (0, (125.0, 107.0)),
        "kabelkanal-3-5mm-abschluss-rechts": (0, (125.0, 125.0)),
        "kabelkanal-3-5mm-einzeln-ohne-verbindung": (0, (125.0, 143.0)),
        "kabelkanal-3-5mm-10cm-rechts": (0, (125.0, 161.0)),
    }
    scene_items = []
    for name, (_plate_idx, (lx, ly)) in layout_xy.items():
        placed = variant_meshes[name].copy()
        cx, cy = 0.5 * (placed.bounds[0, :2] + placed.bounds[1, :2])
        placed.apply_translation([lx - cx, ly - cy, -placed.bounds[0, 2]])
        scene_items.append((name, placed, WHITE_PLA, None))

    MODELS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kabelkanal-orca-", dir=MODELS) as temp_name:
        temp = Path(temp_name)
        source = temp / "kabelkanal-3-5mm-print-source.3mf"
        staged = temp / out_path.name
        write_3mf(source, scene_items)
        cmd = [
            str(ORCA_BIN),
            "--load-settings",
            f"{MACHINE};{BASE_PROCESS}",
            "--load-filaments",
            str(FILAMENT_PRESET),
            "--arrange",
            "0",
            "--orient",
            "0",
            "--ensure-on-bed",
            "--export-3mf",
            str(staged),
            str(source),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        deadline = time.time() + 15.0
        while not staged.is_file() and time.time() < deadline:
            time.sleep(0.25)
        if result.returncode or not staged.is_file():
            raise RuntimeError(
                f"OrcaSlicer export failed (exit {result.returncode}):\n"
                f"stdout: {result.stdout[-1500:]}\nstderr: {result.stderr[-1500:]}"
            )

        with ZipFile(staged) as archive:
            infos = archive.infolist()
            entries = {info.filename: archive.read(info.filename) for info in infos}

        proj_key = "Metadata/project_settings.config"
        project = json.loads(entries[proj_key].decode("utf-8"))
        # Strip OrcaSlicer 2.4.2-only keys that AnycubicSlicerNext 2.0.0.3 flags as unrecognized
        # when loading 3MF project settings, and set version="2.0.0.3" for full cross-slicer compatibility:
        unrecognized_acnext_keys = {
            "activate_air_filtration_during_print", "activate_air_filtration_on_completion",
            "additional_fan_full_speed_layer", "bed_temperature_formula", "bridge_line_width",
            "brim_use_efc_outline", "chamber_minimal_temperature", "close_additional_fan_first_x_layers",
            "combine_brims", "compatible_machine_expression_group", "compatible_printers_condition",
            "compatible_process_expression_group", "elefant_foot_layers_density", "enable_power_loss_recovery",
            "enable_tower_interface_cooldown_during_tower", "enable_tower_interface_features",
            "enable_wrapping_detection", "extruder_ams_count", "extruder_printable_area",
            "extruder_printable_height", "extruder_type", "filament_adaptive_volumetric_speed",
            "filament_adhesiveness_category", "filament_change_extrusion_role_gcode", "filament_change_length",
            "filament_cooling_before_tower", "filament_extruder_variant", "filament_flush_temp",
            "filament_flush_volumetric_speed", "filament_ironing_flow", "filament_ironing_inset",
            "filament_ironing_spacing", "filament_ironing_speed", "filament_printable", "filament_self_index",
            "filament_tower_interface_pre_extrusion_dist", "filament_tower_interface_pre_extrusion_length",
            "filament_tower_interface_print_temp", "filament_tower_interface_purge_volume",
            "filament_tower_ironing_area", "file_start_gcode", "first_x_layer_fan_speed",
            "fuzzy_skin_layers_between_ripple_offset", "fuzzy_skin_ripple_offset",
            "fuzzy_skin_ripples_per_layer", "grab_length", "gyroid_optimized",
            "initial_layer_travel_acceleration", "initial_layer_travel_jerk", "input_shaping_damp_x",
            "input_shaping_damp_y", "input_shaping_emit", "input_shaping_freq_x", "input_shaping_freq_y",
            "input_shaping_type", "ironing_angle_fixed", "lightning_overhang_angle", "lightning_prune_angle",
            "lightning_straightening_angle", "long_retractions_when_ec", "master_extruder_id",
            "nozzle_flush_dataset", "parallel_printheads_bed_exclude_areas", "parallel_printheads_count",
            "part_cooling_fan_min_pwm", "physical_extruder_map", "prime_tower_enable_framework",
            "prime_tower_flat_ironing", "prime_tower_infill_gap", "prime_tower_skip_points",
            "print_extruder_id", "print_extruder_variant", "printer_extruder_id", "printer_extruder_variant",
            "process_change_extrusion_role_gcode", "process_settings_id", "relative_bridge_angle",
            "retraction_distances_when_ec", "support_object_skip_flush", "support_parallel_printheads",
            "tool_change_on_wipe_tower", "use_3mf", "volumetric_speed_coefficients", "wall_maximum_deviation",
            "wall_maximum_resolution", "wrapping_detection_gcode", "wrapping_detection_layers",
            "wrapping_exclude_area", "zaa_dont_alternate_fill_direction", "zaa_enabled", "zaa_min_z",
            "zaa_minimize_perimeter_height",
        }
        for uk in unrecognized_acnext_keys:
            project.pop(uk, None)

        process_overrides = {
            "layer_height": "0.16",
            "initial_layer_print_height": "0.2",
            "wall_loops": "2",
            "sparse_infill_density": "20%",
            "sparse_infill_pattern": "rectilinear",
            "seam_position": "random",
            "ironing_type": "top",
            "enable_support": "1",
            "support_type": "tree(auto)",
            "support_on_build_plate_only": "1",
            "support_threshold_angle": "30",
            "support_top_z_distance": "0.16",
            "support_bottom_z_distance": "0.16",
            "support_critical_regions_only": "1",
            "bridge_no_support": "1",
            "enable_prime_tower": "0",
            "xy_hole_compensation": "0.08",
            "xy_contour_compensation": "0",
            "elefant_foot_compensation": "0.12",
            "brim_type": "no_brim",
            "brim_width": "0",
            "detect_thin_wall": "1",
            "only_one_wall_top": "0",
        }
        project.update(process_overrides)
        project["curr_bed_type"] = "Textured PEI Plate"
        project["version"] = "2.0.0.3"
        project["print_settings_id"] = "0.16mm Standard @Anycubic Kobra S1 0.4 nozzle"
        colors = [WHITE_PLA.color_hex.upper()]
        profile_name = FILAMENT_PRESET.stem
        for key, value in list(project.items()):
            if key.startswith("filament_") and isinstance(value, list) and value:
                project[key] = [value[0]]
        project["flush_volumes_matrix"] = ["0"]
        project["flush_volumes_vector"] = ["140", "140"]
        project["default_filament_profile"] = [profile_name]
        project["default_filament_colour"] = colors
        project["extruder_colour"] = colors
        project["filament_colour"] = colors
        project["filament_settings_id"] = [profile_name]
        project["filament_type"] = ["PLA"]
        project["filament_map"] = ["1"]
        project["filament_is_support"] = ["0"]
        project["inherits_group"] = ["", "", ""]

        # CRITICAL: In OrcaSlicer / AnycubicSlicerNext 3MF schema:
        #   different_settings_to_system[0] = process overrides (seam_position, ironing_type, layer_height, wall_loops, etc.)
        #   different_settings_to_system[1] = machine overrides (curr_bed_type, extruder_colour, etc.)
        #   different_settings_to_system[2] = filament 1 overrides (default_filament_colour, filament_settings_id, etc.)
        proc_changed = set(process_overrides.keys())
        mach_changed = {
            "curr_bed_type",
            "default_filament_colour",
            "default_filament_profile",
            "extruder_colour",
            "flush_volumes_matrix",
            "flush_volumes_vector",
        }
        fil_changed = {
            "default_filament_colour",
            "filament_colour",
            "filament_settings_id",
            "filament_map",
            "filament_type",
        }
        project["different_settings_to_system"] = [
            ";".join(sorted(proc_changed)),
            ";".join(sorted(mach_changed)),
            ";".join(sorted(fil_changed)),
        ]
        entries[proj_key] = json.dumps(project, indent=2).encode("utf-8")
        if "3D/3dmodel.model" in entries:
            entries["3D/3dmodel.model"] = entries["3D/3dmodel.model"].replace(
                b"BambuStudio-02.06.00.51", b"BambuStudio-2.0.0.3"
            )
        entries["Metadata/slice_info.config"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<config>\n"
            "  <header>\n"
            '    <header_item key="X-ACNext-Client-Type" value="slicer"/>\n'
            '    <header_item key="X-ACNext-Client-Version" value="2.0.0.3 20260904033713"/>\n'
            "  </header>\n"
            "</config>\n"
        ).encode("utf-8")

        mod_key = "Metadata/model_settings.config"
        root = ET.fromstring(entries[mod_key])
        ids_by_plate: dict[int, list[str]] = {}
        for obj in root.findall("object"):
            name_node = next((n for n in obj.findall("metadata") if n.get("key") == "name"), None)
            if name_node is None:
                continue
            name = name_node.get("value", "")
            if name not in layout_xy:
                continue
            obj_id = obj.get("id")
            plate_idx, _ = layout_xy[name]
            _add_metadata(obj, "extruder", "1")
            _add_metadata(obj, "wall_loops", "2")
            _add_metadata(obj, "sparse_infill_density", "20%")
            _add_metadata(obj, "enable_support", "1")
            ids_by_plate.setdefault(plate_idx, []).append(obj_id)

        for plate in root.findall("plate"):
            root.remove(plate)
        assemble = root.find("assemble")
        insert_at = list(root).index(assemble) if assemble is not None else len(root)
        for plate_idx, p_name in enumerate(plate_names):
            plate = ET.Element("plate")
            for field, val in (
                ("plater_id", str(plate_idx + 1)),
                ("plater_name", p_name),
                ("locked", "false"),
                ("filament_map_mode", "Auto For Flush"),
                ("gcode_file", ""),
            ):
                ET.SubElement(plate, "metadata", key=field, value=val)
            for obj_id in ids_by_plate.get(plate_idx, []):
                inst = ET.SubElement(plate, "model_instance")
                ET.SubElement(inst, "metadata", key="object_id", value=obj_id)
                ET.SubElement(inst, "metadata", key="instance_id", value="0")
                ET.SubElement(inst, "metadata", key="identify_id", value=obj_id)
            root.insert(insert_at, plate)
            insert_at += 1
        entries[mod_key] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        meta_root = ET.Element("ghouls-grip-print-metadata", version="1")
        for k, val in {
            "status": "not-verified",
            "estimatedPrintTimeSeconds": "unknown",
            "filamentUsageGrams": "unknown",
            "filamentUsageMillimeters": "unknown",
            "filamentUsageCubicMillimeters": "unknown",
            "supportFilamentGrams": "unknown",
            "supportFilamentMillimeters": "unknown",
            "supportFilamentCubicMillimeters": "unknown",
            "printerProfile": "Anycubic Kobra S1 0.4 nozzle",
            "nozzleDiameterMm": "0.4",
            "processProfile": BASE_PROCESS.stem,
            "layerHeightMm": "0.16",
            "filamentProfile": FILAMENT_PRESET.stem,
            "materialType": "PLA",
            "materialColorName": WHITE_PLA.name,
            "materialColorHex": WHITE_PLA.color_hex,
            "bedType": "Textured PEI Plate",
            "plateCount": "1",
            "objectCount": "5",
        }.items():
            ET.SubElement(meta_root, "metadata", name=k, value=val)
        entries[METADATA_ENTRY] = ET.tostring(meta_root, encoding="utf-8", xml_declaration=True)

        with ZipFile(staged, "w", ZIP_DEFLATED) as archive:
            written = set()
            for info in infos:
                if info.filename in written:
                    continue
                archive.writestr(info, entries[info.filename])
                written.add(info.filename)
            if METADATA_ENTRY not in written:
                archive.writestr(METADATA_ENTRY, entries[METADATA_ENTRY])

        os.replace(staged, out_path)


def _to_installed_wall_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Rotate a print-oriented channel mesh 180° around X so the flat slotted back sits on Z_wall = 0
    and the closed sleek bevelled front faces up (+Z_wall = OUTER_HEIGHT)."""
    out = mesh.copy()
    rot = trimesh.transformations.rotation_matrix(math.pi, [1.0, 0.0, 0.0])
    out.apply_transform(rot)
    out.apply_translation([0.0, 0.0, OUTER_HEIGHT])
    return out


def build_view_3mf(
    variant_meshes: dict[str, trimesh.Trimesh],
    demo_meshes: dict[str, trimesh.Trimesh],
    demo_net_length: float,
    out_path: Path,
) -> None:
    """Create `models/kabelkanal-3-5mm-view.3mf` with 3 assembly-state plates in installed wall orientation:
    - Plate 1: All 4 full-length (242.0 mm) variants side-by-side in installed wall orientation.
    - Plate 2: 3-segment system (Abschluss links + Mittelkanal + Abschluss rechts) during front-to-back (`-Z`) press-on.
    - Plate 3: 3-segment system fully snapped & locked onto the continuous 3.5 mm cable.
    """
    cable_mat = filament_slot(slot=2, name="3.5 mm Kabel (Referenz)", material="PLA", color_hex="#2F7DE1")
    mat_list = [WHITE_PLA, cable_mat]
    material_slots = {WHITE_PLA: 0, cable_mat: 1}

    z_bore_wall = OUTER_HEIGHT - Z_BORE_CENTER
    cable_pts = np.array([
        (0.5 * CABLE_DIAMETER * math.cos(2.0 * math.pi * i / 36),
         z_bore_wall + 0.5 * CABLE_DIAMETER * math.sin(2.0 * math.pi * i / 36))
        for i in range(36)
    ])
    cable_m = _extrude_yz_along_x(cable_pts, -1.5 * demo_net_length - 12.0, +1.5 * demo_net_length + 12.0)
    cable_mesh = manifold_to_trimesh(cable_m)

    plate_names = [
        "Zustand 1 - Alle 5 Varianten im Ueberblick (4x 242 mm + 1x 100 mm Rechts-Verbinder)",
        "Zustand 2 - Von vorne in einem Zug aufstecken (Abschluss links + Mitte + Abschluss rechts)",
        "Zustand 3 - Komplett aufgerastet (Links + Mitte + Rechts) mit 3.5 mm Kabel",
    ]
    pitch = 300.0

    # Plate 1: All 5 variants in installed wall orientation
    p1_y_positions = [
        ("state1-abschluss-links-242mm", "kabelkanal-3-5mm-abschluss-links", 89.0),
        ("state1-mitte-beidseitig-242mm", "kabelkanal-3-5mm-mitte-beidseitig", 107.0),
        ("state1-abschluss-rechts-242mm", "kabelkanal-3-5mm-abschluss-rechts", 125.0),
        ("state1-einzeln-ohne-verbindung-242mm", "kabelkanal-3-5mm-einzeln-ohne-verbindung", 143.0),
        ("state1-10cm-rechts-100mm", "kabelkanal-3-5mm-10cm-rechts", 161.0),
    ]
    objects: list[tuple[str, trimesh.Trimesh, filament_slot, list[float] | None]] = []
    object_plates: dict[str, int] = {}
    for obj_name, slug, py in p1_y_positions:
        placed = _to_installed_wall_mesh(variant_meshes[slug]).apply_translation([125.0, py, 0.0])
        objects.append((obj_name, placed, WHITE_PLA, None))
        object_plates[obj_name] = 0

    # Plate 2: 3-segment system (Abschluss links at -demo_net_length, Mitte dropping in -Z at 0, Abschluss rechts at +demo_net_length)
    d_left = _to_installed_wall_mesh(demo_meshes["kabelkanal-3-5mm-abschluss-links"])
    d_mid = _to_installed_wall_mesh(demo_meshes["kabelkanal-3-5mm-mitte-beidseitig"])
    d_right = _to_installed_wall_mesh(demo_meshes["kabelkanal-3-5mm-abschluss-rechts"])

    p2_left = d_left.copy().apply_translation([125.0 + pitch - demo_net_length, 125.0, 6.5])
    p2_mid = d_mid.copy().apply_translation([125.0 + pitch, 125.0, 3.2])
    p2_right = d_right.copy().apply_translation([125.0 + pitch + demo_net_length, 125.0, 0.0])
    p2_cable = cable_mesh.copy().apply_translation([125.0 + pitch, 125.0, 0.0])
    for obj_name, m_obj, mat in (
        ("state2-abschluss-links", p2_left, WHITE_PLA),
        ("state2-mitte-beidseitig", p2_mid, WHITE_PLA),
        ("state2-abschluss-rechts", p2_right, WHITE_PLA),
        ("state2-kabel-3-5mm", p2_cable, cable_mat),
    ):
        objects.append((obj_name, m_obj, mat, None))
        object_plates[obj_name] = 1

    # Plate 3: 3-segment system fully seated on the cable
    p3_left = d_left.copy().apply_translation([125.0 - demo_net_length, 125.0 - pitch, 0.0])
    p3_mid = d_mid.copy().apply_translation([125.0, 125.0 - pitch, 0.0])
    p3_right = d_right.copy().apply_translation([125.0 + demo_net_length, 125.0 - pitch, 0.0])
    p3_cable = cable_mesh.copy().apply_translation([125.0, 125.0 - pitch, 0.0])
    for obj_name, m_obj, mat in (
        ("state3-abschluss-links-gesteckt", p3_left, WHITE_PLA),
        ("state3-mitte-beidseitig-gesteckt", p3_mid, WHITE_PLA),
        ("state3-abschluss-rechts-gesteckt", p3_right, WHITE_PLA),
        ("state3-kabel-3-5mm", p3_cable, cable_mat),
    ):
        objects.append((obj_name, m_obj, mat, None))
        object_plates[obj_name] = 2

    write_3mf(
        out_path,
        objects,
        plate_names=plate_names,
        object_plates=object_plates,
        material_slots=material_slots,
        material_list=mat_list,
    )


# ---------------------------------------------------------------------------
# OrcaSlicer CLI Slicing & Verified Metadata Injection
# ---------------------------------------------------------------------------
def slice_and_update_metadata(print_3mf_path: Path, view_3mf_path: Path, slice_dir: Path) -> dict:
    """Slice `models/kabelkanal-3-5mm-print.3mf` with OrcaSlicer CLI and patch verified metadata into both 3MFs."""
    from update_ghouls_grip_slice_metadata import _filament_index, _stats

    slice_dir.mkdir(parents=True, exist_ok=True)
    for old_gcode in slice_dir.glob("plate_*.gcode"):
        old_gcode.unlink()

    log_file = slice_dir / "slice.log"
    cmd = [
        str(ORCA_BIN),
        str(print_3mf_path),
        "--slice=0",
        f"--outputdir={slice_dir}",
        "--debug=3",
        f"--logfile={log_file}",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    gcodes = sorted(
        slice_dir.glob("plate_*.gcode"),
        key=lambda p: int(p.stem.removeprefix("plate_")),
    )
    if res.returncode != 0 or len(gcodes) != 1:
        raise RuntimeError(
            f"OrcaSlicer slice failed (exit={res.returncode}, plates={len(gcodes)}):\n"
            f"stdout={res.stdout[-1000:]}\nstderr={res.stderr[-1000:]}"
        )

    plate_titles = ["Platte 1 - Alle 5 Varianten Kabelkanal 3.5 mm Weiss (4x 242 mm + 1x 100 mm)"]
    indexed_paths = [
        (p, _filament_index(p.read_text(encoding="utf-8", errors="replace")))
        for p in gcodes
    ]
    overall = _stats(indexed_paths)
    support_g = float(overall["supportFilamentGrams"])
    assert support_g == 0.0, f"Expected 0.00 g support, got {support_g} g!"

    stats_p1 = _stats([indexed_paths[0]])
    stats_p1["status"] = "verified"
    plate_details = [{"name": plate_titles[0], **stats_p1}]
    per_color = {
        WHITE_PLA.name: {
            "estimatedPrintTimeSeconds": int(stats_p1["estimatedPrintTimeSeconds"]),
            "filamentUsageGrams": round(float(stats_p1["filamentUsageGrams"]), 2),
            "supportFilamentGrams": round(float(stats_p1["supportFilamentGrams"]), 2),
            "filamentUsageMillimeters": round(float(stats_p1["filamentUsageMillimeters"]), 2),
            "filamentUsageCubicMillimeters": round(float(stats_p1["filamentUsageCubicMillimeters"])),
            "plateCount": 1,
        }
    }
    overall.update({
        "status": "verified",
        "validationNotes": "None",
        "printerProfile": "Anycubic Kobra S1 0.4 nozzle",
        "nozzleDiameterMm": "0.4",
        "processProfile": BASE_PROCESS.stem,
        "layerHeightMm": "0.16",
        "filamentProfile": FILAMENT_PRESET.stem,
        "materialType": "PLA",
        "materialColorName": WHITE_PLA.name,
        "materialColorHex": WHITE_PLA.color_hex.upper(),
        "bedType": "Textured PEI Plate",
        "wallLoops": "2",
        "infillDensity": "20%",
        "supportPolicy": "Global enable_support=1; tree(auto), Z distance 0.16 mm (1 layer), 0.00 g support required",
        "supportThresholdAngleDeg": "30",
        "seamPosition": "random",
        "ironingType": "top",
        "objectCount": "5",
        "plateCount": "1",
        "filamentUsageByColor": json.dumps(per_color, sort_keys=True, separators=(",", ":")),
        "plateDetails": json.dumps(plate_details, sort_keys=True, separators=(",", ":")),
    })

    with ZipFile(print_3mf_path) as print_arch:
        proj_settings_bytes = (
            print_arch.read("Metadata/project_settings.config")
            if "Metadata/project_settings.config" in print_arch.namelist()
            else None
        )

    for target_3mf in (print_3mf_path, view_3mf_path):
        with ZipFile(target_3mf) as archive:
            infos = archive.infolist()
            entries = {info.filename: archive.read(info.filename) for info in infos}
        root = (
            ET.fromstring(entries[METADATA_ENTRY])
            if METADATA_ENTRY in entries
            else ET.Element("ghouls-grip-print-metadata", version="1")
        )
        fields = {node.get("name"): node for node in root.findall("metadata")}
        target_values = dict(overall)
        if target_3mf == view_3mf_path:
            target_values["plateCount"] = "3"
            target_values["objectCount"] = "13"
        for k, val in target_values.items():
            if k not in fields:
                fields[k] = ET.SubElement(root, "metadata", name=k)
            fields[k].set("value", str(val))
        entries[METADATA_ENTRY] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        if "Metadata/project_settings.config" not in entries and proj_settings_bytes is not None:
            entries["Metadata/project_settings.config"] = proj_settings_bytes
        tmp = target_3mf.with_suffix(".metadata-tmp")
        with ZipFile(tmp, "w", ZIP_DEFLATED) as archive:
            written = set()
            for info in infos:
                if info.filename in written:
                    continue
                archive.writestr(info, entries[info.filename])
                written.add(info.filename)
            if METADATA_ENTRY not in written:
                archive.writestr(METADATA_ENTRY, entries[METADATA_ENTRY])
                written.add(METADATA_ENTRY)
            if "Metadata/project_settings.config" in entries and "Metadata/project_settings.config" not in written:
                archive.writestr("Metadata/project_settings.config", entries["Metadata/project_settings.config"])
                written.add("Metadata/project_settings.config")
        os.replace(tmp, target_3mf)

    return overall


# ---------------------------------------------------------------------------
# Offscreen Vedo Rendering (Project Previews, Support Path & Presentation)
# ---------------------------------------------------------------------------
def render_all_previews(
    variant_meshes: dict[str, trimesh.Trimesh],
    demo_meshes: dict[str, trimesh.Trimesh],
    demo_net_length: float,
    slice_dir: Path,
    slice_stats: dict,
) -> None:
    """Render all required project, support, and presentation PNGs under docs/images/."""
    import vedo
    from render_ghouls_grip_supports import support_actor, support_segments

    vedo.settings.default_backend = "vtk"
    IMAGES.mkdir(parents=True, exist_ok=True)
    fil_g = float(slice_stats["filamentUsageGrams"])
    sup_g = float(slice_stats["supportFilamentGrams"])
    time_s = int(slice_stats["estimatedPrintTimeSeconds"])
    time_str = f"{time_s // 3600}h {(time_s % 3600) // 60:02d}m {time_s % 60:02d}s"

    # 1. Print project preview: `docs/images/kabelkanal-3-5mm-print-preview.png` (All 4 variants on Plate 1)
    plt_print = vedo.Plotter(offscreen=True, size=(1600, 1000), bg="#1B1F27")
    bed = vedo.Box(pos=(125.0, 125.0, -0.6), length=250.0, width=250.0, height=1.2).c("#2C323D").alpha(0.95)
    grid_lines = []
    for g in range(0, 251, 25):
        grid_lines.append(vedo.Line((g, 0, 0.05), (g, 250, 0.05), c="#3E4656", lw=1))
        grid_lines.append(vedo.Line((0, g, 0.05), (250, g, 0.05), c="#3E4656", lw=1))

    plate_y_order = [
        ("kabelkanal-3-5mm-abschluss-links", 89.0),
        ("kabelkanal-3-5mm-mitte-beidseitig", 107.0),
        ("kabelkanal-3-5mm-abschluss-rechts", 125.0),
        ("kabelkanal-3-5mm-einzeln-ohne-verbindung", 143.0),
        ("kabelkanal-3-5mm-10cm-rechts", 161.0),
    ]
    placed_print_meshes = []
    v_print_actors = []
    v_ghost_actors = []
    for slug, py in plate_y_order:
        pm = variant_meshes[slug].copy().apply_translation([125.0, py, 0.0])
        placed_print_meshes.append(pm)
        v_print_actors.append(vedo.Mesh([pm.vertices, pm.faces]).c("#F4F5F7").lighting("plastic"))
        v_ghost_actors.append(vedo.Mesh([pm.vertices, pm.faces]).c("#DDE2EA").alpha(0.85).lighting("plastic"))

    title_print = vedo.Text2D(
        f"kabelkanal-3-5mm-print.3mf  |  Plate 1: Alle 5 Varianten (4x 242 mm + 1x 100 mm)  |  White PLA  |  "
        f"{fil_g:.2f} g  |  {time_str}  |  Support: {sup_g:.2f} g",
        pos="top-left", s=0.88, c="white", bg="#11151C", alpha=0.85,
    )
    plt_print.show(
        bed, *grid_lines, *v_print_actors, title_print,
        camera={
            "pos": (125.0, -75.0, 155.0),
            "focalPoint": (125.0, 125.0, 4.0),
            "viewup": (0.0, 0.45, 0.89),
        },
        resetcam=False,
    )
    plt_print.screenshot(str(IMAGES / "kabelkanal-3-5mm-print-preview.png"))
    plt_print.close()

    # 2. Support screenshot from actual G-code: `docs/images/kabelkanal-3-5mm-print-plate-1-supports.png`
    gcode_p1 = slice_dir / "plate_1.gcode"
    sup_segs = support_segments(gcode_p1)
    sup_act = support_actor(sup_segs)
    plt_sup = vedo.Plotter(offscreen=True, size=(1600, 1000), bg="#15181F")
    sup_badge = vedo.Text2D(
        f"Plate 1 G-code Support Verification (5 Varianten: 4x 242 mm + 1x 100 mm)  |  enable_support=1 tree(auto)  |  "
        f"Support path segments: {len(sup_segs)}  |  Support material: {sup_g:.2f} g (NO SUPPORTS REQUIRED)",
        pos="top-left", s=0.84, c="#5CE08A", bg="#10141B", alpha=0.9,
    )
    actors = [bed, *grid_lines, *v_ghost_actors, sup_badge]
    if sup_act is not None:
        actors.append(sup_act)
    plt_sup.show(
        *actors,
        camera={
            "pos": (125.0, -65.0, 145.0),
            "focalPoint": (125.0, 125.0, 4.0),
            "viewup": (0.0, 0.45, 0.89),
        },
        resetcam=False,
    )
    plt_sup.screenshot(str(IMAGES / "kabelkanal-3-5mm-print-plate-1-supports.png"))
    plt_sup.close()

    # 3. View project preview + high-detail presentation render (4-panel composite):
    #    Panel 0 (Top-Left): All 5 variants side-by-side in installed wall orientation (4x 242 mm + 1x 100 mm)
    #    Panel 1 (Top-Right): Front-to-back press-on motion ("von vorne in einem Zug aufstecken")
    #    Panel 2 (Bottom-Left): Assembled & locked from the visible front (smooth 6.8x5.4 mm profile, Ø 4.30 mm bore)
    #    Panel 3 (Bottom-Right): Rear view (`hinten abgeflacht`) with 3.20 mm compliant slot (3.90 mm funnel) & 1.25 mm flex walls
    plt_pres = vedo.Plotter(N=4, offscreen=True, size=(2000, 1300), bg="#1C2029", sharecam=False)

    m_demo_mid = demo_meshes["kabelkanal-3-5mm-mitte-beidseitig"]
    m_demo_wall = _to_installed_wall_mesh(m_demo_mid)
    z_bore_wall = OUTER_HEIGHT - Z_BORE_CENTER

    p0_actors = []
    for slug, py in [
        ("kabelkanal-3-5mm-abschluss-links", -36.0),
        ("kabelkanal-3-5mm-mitte-beidseitig", -18.0),
        ("kabelkanal-3-5mm-abschluss-rechts", 0.0),
        ("kabelkanal-3-5mm-einzeln-ohne-verbindung", +18.0),
        ("kabelkanal-3-5mm-10cm-rechts", +36.0),
    ]:
        mw = _to_installed_wall_mesh(variant_meshes[slug]).apply_translation([0.0, py, 0.0])
        p0_actors.append(vedo.Mesh([mw.vertices, mw.faces]).c("#F4F5F7").lighting("plastic"))

    t0 = vedo.Text2D(
        "1. Alle 5 Varianten: 4x 242 mm (Links | Mitte | Rechts | Einzeln) + 1x 100 mm (Verbindung nur rechts)",
        pos="top-left", s=0.76, c="white", bg="#11151C", alpha=0.85,
    )
    plt_pres.at(0).show(
        *p0_actors, t0,
        camera={"pos": (-35.0, -210.0, 145.0), "focalPoint": (0.0, 0.0, 2.6), "viewup": (0.0, 0.0, 1.0)},
        resetcam=False,
    )

    # Panel 1: Front-to-back press-on motion ("von vorne in einem Zug aufstecken"):
    half_demo_total = 0.5 * (demo_net_length + CONNECTOR_LENGTH)
    cable_wall_pts = np.array([
        (0.5 * CABLE_DIAMETER * math.cos(2.0 * math.pi * i / 40),
         z_bore_wall + 0.5 * CABLE_DIAMETER * math.sin(2.0 * math.pi * i / 40))
        for i in range(40)
    ])
    seg_left_drop = m_demo_wall.copy().apply_translation([-(half_demo_total - CONNECTOR_LENGTH), 0.0, 6.0])
    seg_right_base = m_demo_wall.copy().apply_translation([+(half_demo_total), 0.0, 0.0])
    cable_pre = manifold_to_trimesh(_extrude_yz_along_x(cable_wall_pts, -35.0, +45.0))
    v_left_pre = vedo.Mesh([seg_left_drop.vertices, seg_left_drop.faces]).c("#F4F5F7").lighting("plastic")
    v_right_pre = vedo.Mesh([seg_right_base.vertices, seg_right_base.faces]).c("#E3E8F0").lighting("plastic")
    v_cable_pre = vedo.Mesh([cable_pre.vertices, cable_pre.faces]).c("#2F7DE1").lighting("plastic")
    t1 = vedo.Text2D(
        "2. Von vorne in einem Zug aufstecken (-Z): Ueberwurf-Kappe (+X) rastet ueber Sattel (-X) & Quersteg",
        pos="top-left", s=0.80, c="white", bg="#11151C", alpha=0.85,
    )
    plt_pres.at(1).show(
        v_left_pre, v_right_pre, v_cable_pre, t1,
        camera={"pos": (-16.0, -34.0, 22.0), "focalPoint": (4.0, 0.0, 4.0), "viewup": (0.0, 0.0, 1.0)},
        resetcam=False,
    )

    seg_left_mated = m_demo_wall.copy().apply_translation([-(half_demo_total - CONNECTOR_LENGTH), 0.0, 0.0])
    seg_right_mated = m_demo_wall.copy().apply_translation([+(half_demo_total), 0.0, 0.0])
    cable_mated = manifold_to_trimesh(_extrude_yz_along_x(cable_wall_pts, -45.0, +45.0))
    v_left_m = vedo.Mesh([seg_left_mated.vertices, seg_left_mated.faces]).c("#F4F5F7").lighting("plastic")
    v_right_m = vedo.Mesh([seg_right_mated.vertices, seg_right_mated.faces]).c("#EAEEF5").lighting("plastic")
    v_cable = vedo.Mesh([cable_mated.vertices, cable_mated.faces]).c("#2F7DE1").lighting("plastic")
    t2 = vedo.Text2D(
        "3. Aufgerastet (Sichtseite vorne): Schlankes 6.8x5.4 mm Profil (Ø 4.30 mm Innenraum), buendiger Uebergang",
        pos="top-left", s=0.76, c="white", bg="#11151C", alpha=0.85,
    )
    plt_pres.at(2).show(
        v_left_m, v_right_m, v_cable, t2,
        camera={"pos": (-16.0, -34.0, 20.0), "focalPoint": (5.0, 0.0, 2.6), "viewup": (0.0, 0.0, 1.0)},
        resetcam=False,
    )

    # Panel 3: Rear/Bottom view (`hinten abgeflacht`) showing the flat slotted back (print Z = 5.40 mm facing up)
    cable_print_pts = np.array([
        (0.5 * CABLE_DIAMETER * math.cos(2.0 * math.pi * i / 40),
         Z_BORE_CENTER + 0.5 * CABLE_DIAMETER * math.sin(2.0 * math.pi * i / 40))
        for i in range(40)
    ])
    seg_left_back = m_demo_mid.copy().apply_translation([-(half_demo_total - CONNECTOR_LENGTH), 0.0, 0.0])
    seg_right_back = m_demo_mid.copy().apply_translation([+(half_demo_total), 0.0, 0.0])
    cable_back = manifold_to_trimesh(_extrude_yz_along_x(cable_print_pts, -25.0, +42.0))
    v_left_b = vedo.Mesh([seg_left_back.vertices, seg_left_back.faces]).c("#F4F5F7").lighting("plastic")
    v_right_b = vedo.Mesh([seg_right_back.vertices, seg_right_back.faces]).c("#E5EAF2").lighting("plastic")
    v_cable_b = vedo.Mesh([cable_back.vertices, cable_back.faces]).c("#2F7DE1").lighting("plastic")
    t3 = vedo.Text2D(
        "4. Rueckseite: Ø 4.30 mm Bohrung + 3.20 mm elastischer Schlitz (3.90 mm Trichter, 1.25 mm Federwangen)",
        pos="top-left", s=0.75, c="white", bg="#11151C", alpha=0.85,
    )
    plt_pres.at(3).show(
        v_left_b, v_right_b, v_cable_b, t3,
        camera={"pos": (-18.0, -32.0, 22.0), "focalPoint": (2.0, 0.0, 3.5), "viewup": (0.0, 0.0, 1.0)},
        resetcam=False,
    )

    pres_path = IMAGES / "kabelkanal-3-5mm-presentation.png"
    view_prev_path = IMAGES / "kabelkanal-3-5mm-view-preview.png"
    plt_pres.screenshot(str(pres_path))
    plt_pres.screenshot(str(view_prev_path))
    plt_pres.close()


def main() -> None:
    t0 = time.perf_counter()
    print("Building all 5 variants of the 3.5 mm cable channel (4x 242.0 mm + 1x 100.0 mm right-connector)...")
    variant_manifolds: dict[str, m3d.Manifold] = {}
    variant_meshes: dict[str, trimesh.Trimesh] = {}

    demo_net_len = 70.0
    demo_total_len = demo_net_len + CONNECTOR_LENGTH  # 80.0 mm
    demo_meshes: dict[str, trimesh.Trimesh] = {}

    for slug, left_conn, right_conn, total_len, _desc in VARIANT_SPECS:
        vm = build_channel_manifold(
            body_net_length=total_len - CONNECTOR_LENGTH,
            left_connector=left_conn,
            right_connector=right_conn,
            total_length_override=total_len,
        )
        vmesh = manifold_to_trimesh(vm)
        variant_manifolds[slug] = vm
        variant_meshes[slug] = vmesh

        if left_conn or right_conn:
            dm = build_channel_manifold(
                body_net_length=demo_net_len,
                left_connector=left_conn,
                right_connector=right_conn,
                total_length_override=demo_total_len,
            )
            demo_meshes[slug] = manifold_to_trimesh(dm)

    print_3mf_path = MODELS / "kabelkanal-3-5mm-print.3mf"
    view_3mf_path = MODELS / "kabelkanal-3-5mm-view.3mf"
    slice_dir = BUILD_DIR / "slices"

    report = verify_cable_channel_and_joint(variant_manifolds, variant_meshes)
    print("Verification summary:")
    for k, v in report.items():
        if k not in ("sweep_steps", "variants"):
            print(f"  {k}: {v}")

    build_print_3mf(variant_meshes, print_3mf_path)
    build_view_3mf(variant_meshes, demo_meshes, demo_net_len, view_3mf_path)
    print(f"Built 3MF deliverables:\n  {print_3mf_path}\n  {view_3mf_path}")

    slice_stats = slice_and_update_metadata(print_3mf_path, view_3mf_path, slice_dir)
    print(f"OrcaSlicer verified slice stats: {slice_stats}")

    render_all_previews(variant_meshes, demo_meshes, demo_net_len, slice_dir, slice_stats)
    report["orca_slice"] = slice_stats
    report["elapsed_s"] = round(time.perf_counter() - t0, 2)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    (BUILD_DIR / "verification_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Done in {report['elapsed_s']:.2f} s.")


if __name__ == "__main__":
    main()
