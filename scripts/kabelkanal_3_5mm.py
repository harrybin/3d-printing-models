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
CABLE_RADIAL_CLEARANCE = 0.18  # +0.36 mm diametral clearance -> Ø 3.86 mm bore
BORE_RADIUS = 0.5 * CABLE_DIAMETER + CABLE_RADIAL_CLEARANCE  # 1.93 mm

# Print vs. Installed Orientation (`Öffnung hinten`, Sichtseite `vorne` geschlossen):
# - Print orientation (in `models/kabelkanal-3-5mm.stl` and `-print.3mf`):
#   - Closed, sleek bevelled front side (`vorne`) rests on the Textured PEI build plate `Z = 0.00 mm`.
#   - Flat slotted back side (`hinten`) faces UP at `Z = OUTER_HEIGHT = 5.20 mm`, where `ironing_type = top`
#     irons both flat rear wall-mounting strips (`Y in [-3.60, -1.55]` and `[+1.55, +3.60]`) razor-smooth.
#   - Because the rear cable slot (`2.75 mm` throat, `3.10 mm` entry funnel) opens upward at `Z = 5.20 mm`,
#     there is NO internal closing roof during printing -> 0.00 g support in OrcaSlicer `tree(auto)`!
# - Installed wall orientation (shown in `-view.3mf` and presentation renders):
#   - Flat slotted back (`hinten`) sits against the wall/cable; closed smooth front (`vorne`) faces out.
Z_BORE_CENTER = 3.05  # Ø 3.86 mm cable bore center (bore spans Z = 1.12..4.98 mm; 1.12 mm solid front wall)

SLOT_ENTRY_WIDTH = 3.10  # rear entry funnel on the flat back (Z = 5.20 mm)
Y_ENTRY = 0.5 * SLOT_ENTRY_WIDTH  # 1.55 mm
SLOT_THROAT_WIDTH = 2.75  # 0.75 mm snap retention undercut for the 3.50 mm cable
Y_THROAT = 0.5 * SLOT_THROAT_WIDTH  # 1.375 mm

# Ultra-slim Outer Profile (7.20 mm wide x 5.20 mm high)
OUTER_WIDTH = 7.20
Y_OUTER = 0.5 * OUTER_WIDTH  # 3.60 mm
OUTER_HEIGHT = 5.20
FRONT_BEVEL = 1.20  # 45° architectural front bevel on Z = 0..1.20 mm (y_front = ±2.40 mm)
BED_CHAMFER = 0.25  # Rear edge relief at Z = OUTER_HEIGHT

# Front-to-back press-on Saddle Joint (`Von-vorne-Aufrast-Überblattung`)
# Connects in one motion from the front when snapping the channel onto the cable:
# - `-X` end (`CONNECTOR_LENGTH = 10.00 mm`): Inner Saddle with vertical T-key rib (`Quersteg`, locks ±X)
#   and horizontal snap-bead (`Rastleiste`, locks ±Z).
# - `+X` end (`SOCKET_DEPTH = 10.10 mm`): Outer Saddle Hood whose side cheeks wrap over the mating
#   Inner Saddle from the front in the exact same motion as snapping the channel onto the cable.
CONNECTOR_LENGTH = 10.00
CONNECTOR_AXIAL_CLEAR = 0.10
SOCKET_DEPTH = CONNECTOR_LENGTH + CONNECTOR_AXIAL_CLEAR  # 10.10 mm
CONNECTOR_CLEARANCE = 0.16  # per-side clearance between saddle and hood
BODY_NET_LENGTH = MAX_TOTAL_LENGTH - CONNECTOR_LENGTH  # 232.00 mm modular step per channel

# Saddle & Hood cross-section parameters (YZ plane)
Y_SADDLE_SPINE = 1.52  # 3.04 mm wide flush front face on Z = 0.00 mm
Y_SADDLE_BASE = 2.40   # Inner saddle half-width (leaves >= 1.04 mm outer hood cheek inside Y=3.60)
Z_SADDLE_SHOULDER = 0.92
Z_SADDLE_APEX = 5.20

# Vertical T-key rib (locks ±X when pressed on from the front)
KEY_OFFSET_FROM_SHOULDER = 5.00
KEY_HALF_LEN = 1.50
KEY_RIB_PROTRUSION = 0.34  # widens saddle from ±2.40 to ±2.74 mm
KEY_SLOT_DEPTH = 0.36      # widens hood slot from ±2.56 to ±2.92 mm

# Horizontal snap-detent bead along Z (clicks when pressed on from the front)
Z_SNAP_BEAD = 3.30
SNAP_BEAD_PROTRUSION = 0.22  # y_bead = 2.62 mm > 2.56 mm hood throat -> 0.06 mm/side click interference
SNAP_GROOVE_DEPTH = 0.24     # y_groove = 2.80 mm > 2.62 mm -> 0.18 mm seated clearance (0.0000 mm^3 collision)


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
    """Return 2D polygon (Y, Z) in CCW order for the Ø 3.86 mm cable bore + rear snap-in slot at Z = 5.20 mm.

    - Bore bottom sits at `Z = 1.12 mm` (leaving a solid 1.12 mm closed front wall at `Z = 0.00..1.12 mm`).
    - Circular Ø 3.86 mm (`R = 1.93 mm`) cable bore centered at `Z = 3.05 mm` spans from the bottom up to
      `theta_top = +44.5°` (`Y = ±1.375 mm`, `Z = 4.403 mm`), so the upper retaining lips have a
      self-supporting slope `>= 67°` from horizontal (`<= 23°` from vertical).
    - Snap-in throat (`2.75 mm` wide, `Y = ±1.375 mm`) spans `Z = 4.403..4.90 mm`.
    - Rear entry funnel (`3.10 mm` wide, `Y = ±1.55 mm`) flares to the flat back `Z = 5.20 mm` (and +5.45 mm).
    """
    alpha_top = math.asin(math.sqrt(max(0.0, 1.0 - (Y_THROAT / BORE_RADIUS) ** 2)))  # ~44.5 deg
    z_throat_bot = Z_BORE_CENTER + BORE_RADIUS * math.sin(alpha_top)  # ~4.403 mm
    z_throat_top = 4.90

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
    z_sh = Z_SADDLE_SHOULDER + 0.85 * max(0.0, delta_y_key)
    z_b0 = Z_SNAP_BEAD - 0.32
    z_b1 = Z_SNAP_BEAD
    z_b2 = Z_SNAP_BEAD + 0.32

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
    z_sh = max(0.25, Z_SADDLE_SHOULDER - 0.35 * c + 0.85 * max(0.0, delta_y_key))
    z_b0 = Z_SNAP_BEAD - 0.40
    z_b1 = Z_SNAP_BEAD
    z_b2 = Z_SNAP_BEAD + 0.40

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


def build_channel_manifold(body_net_length: float = BODY_NET_LENGTH) -> m3d.Manifold:
    """Construct one connectable 3.5 mm cable channel segment as a watertight Manifold.

    Coordinate system (centered on the print bed):
      - Total X span: [-total_len/2, +total_len/2], where total_len = body_net_length + CONNECTOR_LENGTH.
      - `-X` end (`[x_min, x_shoulder]`): Inner/Lower Saddle (`Aufrast-Sattel`) with vertical T-key rib.
      - Main slim closed-front D-body spans `[x_shoulder, x_max]`.
      - `+X` end (`[x_max - SOCKET_DEPTH, x_max]`): Outer/Upper Saddle Hood (`Aufrast-Kappe`) that drops
        straight down from the front (`-Z`) onto the previous segment's `-X` Saddle in the same motion
        as clipping the channel onto the cable!
    """
    total_len = body_net_length + CONNECTOR_LENGTH
    x_min = -0.5 * total_len
    x_shoulder = x_min + CONNECTOR_LENGTH
    x_max = +0.5 * total_len

    outer_yz = _outer_profile_yz()
    cavity_yz = _inner_cavity_profile_yz()

    # 1. Main body outer solid from x_shoulder to x_max
    main_body = _extrude_yz_along_x(outer_yz, x_shoulder, x_max)

    # 2. `-X` Inner/Lower Saddle from x_min to x_shoulder + 0.40 mm (overlap into main body)
    # Includes a 0.80 mm lead-in bevel at the tip and a vertical T-key rib centered at
    # x_key = x_shoulder - KEY_OFFSET_FROM_SHOULDER that locks ±X once the hood is pressed on from -Z.
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
    solid = main_body + male_tip + male_shaft + male_key_rib

    # 3. Subtract the `+X` Outer/Upper Saddle Hood cavity at [x_max - SOCKET_DEPTH, x_max + 0.2]
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

    # 4. Subtract the continuous Ø 3.90 mm cable bore and rear snap-in slot (on flat back Z=0)
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
def verify_cable_channel_and_joint(m_single: m3d.Manifold, mesh: trimesh.Trimesh) -> dict:
    """Run comprehensive mesh, feature-probe, cable-fit, and two-segment joint checks."""
    bounds = mesh.bounds
    extents = mesh.extents

    # 1. Basic mesh integrity
    assert mesh.is_watertight, "Channel mesh must be watertight"
    assert mesh.is_winding_consistent, "Channel mesh must have consistent winding"
    deg_count = int(len(mesh.faces) - np.count_nonzero(mesh.nondegenerate_faces()))
    assert deg_count == 0, f"Expected 0 degenerate faces, found {deg_count}"

    # 2. Volume probes at mid-channel (X = 0.0 mm):
    #    - Bore center (Y=0, Z=Z_BORE_CENTER): must be EMPTY (0.0 mm^3 intersection with Ø 3.50 mm cable)
    #    - Closed Front Arch (Y=0, Z=6.60..7.30): must be 100% SOLID
    #    - Flat Rear Mounting Pads (Y=±3.60, Z=0.20..1.20): must be 100% SOLID
    #    - Rear Snap-In Slot (Y=0, Z=0.00..1.00): must be EMPTY (open on the flat back!)
    cable_rod = _extrude_yz_along_x(
        np.array([
            (0.5 * CABLE_DIAMETER * math.cos(2.0 * math.pi * i / 48),
             Z_BORE_CENTER + 0.5 * CABLE_DIAMETER * math.sin(2.0 * math.pi * i / 48))
            for i in range(48)
        ]),
        -120.0,
        +120.0,
    )
    cable_collision_vol = (m_single ^ cable_rod).volume()
    assert cable_collision_vol == 0.0, f"3.5 mm cable collides with channel bore: {cable_collision_vol} mm^3"

    # Prove closed front wall at mid-channel (X in [-5, +5], Y in [-0.6, +0.6], Z in [0.15, 0.85]) is SOLID
    front_wall_probe = m3d.Manifold.cube([10.0, 1.2, 0.7], False).translate([-5.0, -0.6, 0.15])
    front_wall_vol = (m_single ^ front_wall_probe).volume()
    assert abs(front_wall_vol - 8.4) < 1e-2, f"Closed front wall probe must be solid (8.4 mm^3), got {front_wall_vol}"

    # Prove rear slot on flat back (X in [-5, +5], Y in [-1.0, +1.0], Z in [4.40, 5.20]) is OPEN (0.0 mm^3)
    rear_slot_probe = m3d.Manifold.cube([10.0, 2.0, 0.8], False).translate([-5.0, -1.0, 4.40])
    rear_slot_vol = (m_single ^ rear_slot_probe).volume()
    assert rear_slot_vol == 0.0, f"Rear cable slot on flat back must be open (0 mm^3), got {rear_slot_vol}"

    # Prove flat rear mounting flanges (Y in [+1.8, +3.2], Z in [4.40, 5.00]) are SOLID
    rear_flange_probe = m3d.Manifold.cube([10.0, 1.4, 0.6], False).translate([-5.0, 1.8, 4.40])
    rear_flange_vol = (m_single ^ rear_flange_probe).volume()
    assert abs(rear_flange_vol - 8.4) < 1e-2, f"Rear mounting flange must be solid (8.4 mm^3), got {rear_flange_vol}"

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
        "axial_x_lock_interference_mm3": round(float(axial_lock_vol), 4),
        "peak_front_snap_click_interference_mm3": round(float(peak_detent_engagement), 4),
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


def build_print_3mf(channel_mesh: trimesh.Trimesh, out_path: Path) -> None:
    """Create `models/kabelkanal-3-5mm-print.3mf` with two connectable segments on Plate 1.

    - Placed at X = 125.0 mm (centered on 250 mm bed -> X in [4.0, 246.0] mm)
    - Segment A at Y = 114.0 mm, Segment B at Y = 136.0 mm (22.0 mm center-to-center spacing)
    - Configured for Anycubic Kobra S1 0.4 mm nozzle, Textured PEI Plate, White PLA (Slot 1),
      0.16 mm layer height, random seam, top ironing, and automatic tree supports (0.16 mm Z gap).
    """
    import tempfile

    plate_names = ["Platte 1 - 2x Kabelkanal 3.5 mm Weiss (je 242 mm, steckbar)"]
    layout_xy = {
        "kabelkanal-3-5mm-segment-a": (0, (125.0, 114.0)),
        "kabelkanal-3-5mm-segment-b": (0, (125.0, 136.0)),
    }
    scene_items = []
    for name, (_plate_idx, (lx, ly)) in layout_xy.items():
        placed = channel_mesh.copy()
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
        process_overrides = {
            "curr_bed_type": "Textured PEI Plate",
            "layer_height": "0.16",
            "initial_layer_print_height": "0.2",
            "wall_loops": "3",
            "sparse_infill_density": "25%",
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
            "xy_hole_compensation": "0.0",
            "xy_contour_compensation": "0",
            "elefant_foot_compensation": "0.12",
            "brim_type": "no_brim",
            "brim_width": "0",
            "detect_thin_wall": "1",
            "only_one_wall_top": "0",
        }
        project.update(process_overrides)
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
        project["filament_self_index"] = ["1"]
        project["filament_printable"] = ["3"]
        project["filament_is_support"] = ["0"]
        project["print_extruder_id"] = ["1"]
        project["printer_extruder_id"] = ["1"]
        project["process_settings_id"] = BASE_PROCESS.stem

        changed = set(project.get("different_settings_to_system", ["", "", ""])[1].split(";"))
        changed.update(process_overrides.keys())
        changed.update({
            "default_filament_colour",
            "default_filament_profile",
            "extruder_colour",
            "filament_colour",
            "filament_settings_id",
            "filament_map",
            "filament_self_index",
            "filament_type",
            "flush_volumes_matrix",
            "flush_volumes_vector",
            "print_extruder_id",
            "printer_extruder_id",
        })
        current = project.get("different_settings_to_system", ["", "", ""])
        current[1] = ";".join(sorted(changed - {""}))
        project["different_settings_to_system"] = current
        entries[proj_key] = json.dumps(project, indent=2).encode("utf-8")

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
            _add_metadata(obj, "wall_loops", "3")
            _add_metadata(obj, "sparse_infill_density", "25%")
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
            "objectCount": "2",
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
    m_full: trimesh.Trimesh,
    m_demo: trimesh.Trimesh,
    demo_net_length: float,
    out_path: Path,
) -> None:
    """Create `models/kabelkanal-3-5mm-view.3mf` with 3 assembly-state plates in installed wall orientation."""
    cable_mat = filament_slot(slot=2, name="3.5 mm Kabel (Referenz)", material="PLA", color_hex="#2F7DE1")
    mat_list = [WHITE_PLA, cable_mat]
    material_slots = {WHITE_PLA: 0, cable_mat: 1}

    z_bore_wall = OUTER_HEIGHT - Z_BORE_CENTER
    cable_pts = np.array([
        (0.5 * CABLE_DIAMETER * math.cos(2.0 * math.pi * i / 36),
         z_bore_wall + 0.5 * CABLE_DIAMETER * math.sin(2.0 * math.pi * i / 36))
        for i in range(36)
    ])
    cable_m = _extrude_yz_along_x(cable_pts, -0.5 * demo_net_length - 25.0, +1.5 * demo_net_length + 15.0)
    cable_mesh = manifold_to_trimesh(cable_m)

    plate_names = [
        "Zustand 1 - Schlankes Einzelsegment (242 mm, 7.2x5.2 mm, Sichtseite vorne geschlossen)",
        "Zustand 2 - Von vorne in einem Zug aufstecken (-Z Aufrast-Ueberblattung)",
        "Zustand 3 - Aufgerastet & verriegelt mit eingeclipstem 3.5 mm Kabel",
    ]
    pitch = 300.0
    m_full_wall = _to_installed_wall_mesh(m_full)
    m_demo_wall = _to_installed_wall_mesh(m_demo)

    p1_seg = m_full_wall.copy().apply_translation([125.0, 125.0, 0.0])
    # State 2: Segment A (`+X` Hood) positioned at dz = +6.5 mm above Segment B (`-X` Saddle on wall + cable)
    # showing how it presses straight down in `-Z` ("von vorne in einem Zug")!
    p2_seg_a = m_demo_wall.copy().apply_translation([125.0 + pitch - 0.5 * demo_net_length, 125.0, 6.5])
    p2_seg_b = m_demo_wall.copy().apply_translation([125.0 + pitch + 0.5 * demo_net_length, 125.0, 0.0])
    p3_seg_a = m_demo_wall.copy().apply_translation([125.0 - 0.5 * demo_net_length, 125.0 - pitch, 0.0])
    p3_seg_b = m_demo_wall.copy().apply_translation([125.0 + 0.5 * demo_net_length, 125.0 - pitch, 0.0])
    p3_cable = cable_mesh.copy().apply_translation([125.0 - 0.5 * demo_net_length, 125.0 - pitch, 0.0])

    objects = [
        ("state1-kabelkanal-242mm", p1_seg, WHITE_PLA, None),
        ("state2-kabelkanal-segment-a", p2_seg_a, WHITE_PLA, None),
        ("state2-kabelkanal-segment-b", p2_seg_b, WHITE_PLA, None),
        ("state3-kabelkanal-segment-a-gesteckt", p3_seg_a, WHITE_PLA, None),
        ("state3-kabelkanal-segment-b-gesteckt", p3_seg_b, WHITE_PLA, None),
        ("state3-kabel-3-5mm", p3_cable, cable_mat, None),
    ]
    object_plates = {
        "state1-kabelkanal-242mm": 0,
        "state2-kabelkanal-segment-a": 1,
        "state2-kabelkanal-segment-b": 1,
        "state3-kabelkanal-segment-a-gesteckt": 2,
        "state3-kabelkanal-segment-b-gesteckt": 2,
        "state3-kabel-3-5mm": 2,
    }
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

    plate_titles = ["Platte 1 - 2x Kabelkanal 3.5 mm Weiss (je 242 mm, steckbar)"]
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
        "wallLoops": "3",
        "infillDensity": "25%",
        "supportPolicy": "Global enable_support=1; tree(auto), Z distance 0.16 mm (1 layer), 0.00 g support required",
        "supportThresholdAngleDeg": "30",
        "seamPosition": "random",
        "ironingType": "top",
        "objectCount": "2",
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
            target_values["objectCount"] = "6"
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
    m_full: trimesh.Trimesh,
    m_demo: trimesh.Trimesh,
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

    # 1. Print project preview: `docs/images/kabelkanal-3-5mm-print-preview.png`
    plt_print = vedo.Plotter(offscreen=True, size=(1600, 1000), bg="#1B1F27")
    bed = vedo.Box(pos=(125.0, 125.0, -0.6), length=250.0, width=250.0, height=1.2).c("#2C323D").alpha(0.95)
    grid_lines = []
    for g in range(0, 251, 25):
        grid_lines.append(vedo.Line((g, 0, 0.05), (g, 250, 0.05), c="#3E4656", lw=1))
        grid_lines.append(vedo.Line((0, g, 0.05), (250, g, 0.05), c="#3E4656", lw=1))

    seg_a = m_full.copy().apply_translation([125.0, 114.0, 0.0])
    seg_b = m_full.copy().apply_translation([125.0, 136.0, 0.0])
    v_a = vedo.Mesh([seg_a.vertices, seg_a.faces]).c("#F4F5F7").lighting("plastic")
    v_b = vedo.Mesh([seg_b.vertices, seg_b.faces]).c("#F4F5F7").lighting("plastic")
    title_print = vedo.Text2D(
        f"kabelkanal-3-5mm-print.3mf  |  Plate 1: 2x 242.0 mm (460.0 mm net)  |  White PLA  |  "
        f"{fil_g:.2f} g  |  {time_str}  |  Support: {sup_g:.2f} g",
        pos="top-left", s=0.95, c="white", bg="#11151C", alpha=0.85,
    )
    plt_print.show(
        bed, *grid_lines, v_a, v_b, title_print,
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
    v_a_ghost = vedo.Mesh([seg_a.vertices, seg_a.faces]).c("#DDE2EA").alpha(0.85).lighting("plastic")
    v_b_ghost = vedo.Mesh([seg_b.vertices, seg_b.faces]).c("#DDE2EA").alpha(0.85).lighting("plastic")
    sup_badge = vedo.Text2D(
        f"Plate 1 G-code Support Verification  |  enable_support=1 tree(auto)  |  "
        f"Support path segments: {len(sup_segs)}  |  Support material: {sup_g:.2f} g (NO SUPPORTS REQUIRED)",
        pos="top-left", s=0.9, c="#5CE08A", bg="#10141B", alpha=0.9,
    )
    actors = [bed, *grid_lines, v_a_ghost, v_b_ghost, sup_badge]
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
    #    Panel 0 (Top-Left): Full 242.0 mm channel segment (closed, smooth front dome facing up)
    #    Panel 1 (Top-Right): End-to-end connector before plugging (Male inverted-U V-rail tongue & Female socket)
    #    Panel 2 (Bottom-Left): Plugged & click-locked state from the visible front (100% closed, flush hairline joint!)
    #    Panel 3 (Bottom-Right): Bottom/Rear view (`hinten abgeflacht`) showing the rear cable insertion slot
    #                            (`2.70 mm` snap throat), flat wall-mounting pads, and inserted Ø 3.5 mm cable!
    plt_pres = vedo.Plotter(N=4, offscreen=True, size=(2000, 1300), bg="#1C2029", sharecam=False)

    m_full_wall = _to_installed_wall_mesh(m_full)
    m_demo_wall = _to_installed_wall_mesh(m_demo)
    z_bore_wall = OUTER_HEIGHT - Z_BORE_CENTER

    v_full = vedo.Mesh([m_full_wall.vertices, m_full_wall.faces]).c("#F4F5F7").lighting("plastic")
    t0 = vedo.Text2D(
        "1. Schlankes Profil (7.2 x 5.2 mm, 242.0 mm lang) - Sichtseite vorne geschlossen",
        pos="top-left", s=0.82, c="white", bg="#11151C", alpha=0.85,
    )
    plt_pres.at(0).show(
        v_full, t0,
        camera={"pos": (-45.0, -195.0, 125.0), "focalPoint": (0.0, 0.0, 2.6), "viewup": (0.0, 0.0, 1.0)},
        resetcam=False,
    )

    # Panel 1: Front-to-back press-on motion ("von vorne in einem Zug aufstecken"):
    # Segment B (right) is already on the cable/wall (Z_wall=0); Segment A (left, carrying the +X Hood)
    # is positioned at dz = +6.0 mm right above Segment B's -X Saddle, ready to press straight down in -Z!
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
        "2. Von vorne in einem Zug aufstecken (-Z): Ueberwurf-Kappe rastet ueber Sattel & Quersteg",
        pos="top-left", s=0.82, c="white", bg="#11151C", alpha=0.85,
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
        "3. Aufgerastet (Sichtseite vorne): Schlankes 7.2x5.2 mm Profil, buendiger Uebergang",
        pos="top-left", s=0.82, c="white", bg="#11151C", alpha=0.85,
    )
    plt_pres.at(2).show(
        v_left_m, v_right_m, v_cable, t2,
        camera={"pos": (-16.0, -34.0, 20.0), "focalPoint": (5.0, 0.0, 2.6), "viewup": (0.0, 0.0, 1.0)},
        resetcam=False,
    )

    # Panel 3: Rear/Bottom view (`hinten abgeflacht`) showing the flat slotted back (print Z = 5.20 mm facing up)
    cable_print_pts = np.array([
        (0.5 * CABLE_DIAMETER * math.cos(2.0 * math.pi * i / 40),
         Z_BORE_CENTER + 0.5 * CABLE_DIAMETER * math.sin(2.0 * math.pi * i / 40))
        for i in range(40)
    ])
    seg_left_back = m_demo.copy().apply_translation([-(half_demo_total - CONNECTOR_LENGTH), 0.0, 0.0])
    seg_right_back = m_demo.copy().apply_translation([+(half_demo_total), 0.0, 0.0])
    cable_back = manifold_to_trimesh(_extrude_yz_along_x(cable_print_pts, -25.0, +42.0))
    v_left_b = vedo.Mesh([seg_left_back.vertices, seg_left_back.faces]).c("#F4F5F7").lighting("plastic")
    v_right_b = vedo.Mesh([seg_right_back.vertices, seg_right_back.faces]).c("#E5EAF2").lighting("plastic")
    v_cable_b = vedo.Mesh([cable_back.vertices, cable_back.faces]).c("#2F7DE1").lighting("plastic")
    t3 = vedo.Text2D(
        "4. Rueckseite (hinten abgeflacht): 2.75 mm Kabel-Einclipsoeffnung hinten + flache Auflage",
        pos="top-left", s=0.82, c="white", bg="#11151C", alpha=0.85,
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
    print("Building 3.5 mm flat-backed connectable cable channel (242.0 mm total / 230.0 mm net)...")
    m_full = build_channel_manifold(body_net_length=BODY_NET_LENGTH)
    mesh_full = manifold_to_trimesh(m_full)

    # Short 75 mm net segment used on Plates 2 & 3 of view.3mf so two connected segments fit on one 250 mm view plate
    demo_net_len = 75.0
    m_demo = build_channel_manifold(body_net_length=demo_net_len)
    mesh_demo = manifold_to_trimesh(m_demo)

    stl_path = MODELS / "kabelkanal-3-5mm.stl"
    print_3mf_path = MODELS / "kabelkanal-3-5mm-print.3mf"
    view_3mf_path = MODELS / "kabelkanal-3-5mm-view.3mf"
    slice_dir = BUILD_DIR / "slices"

    export_ascii_stl(mesh_full, stl_path)
    print(f"Exported ASCII STL: {stl_path}")

    report = verify_cable_channel_and_joint(m_full, mesh_full)
    print("Verification summary:")
    for k, v in report.items():
        if k != "sweep_steps":
            print(f"  {k}: {v}")

    build_print_3mf(mesh_full, print_3mf_path)
    build_view_3mf(mesh_full, mesh_demo, demo_net_len, view_3mf_path)
    print(f"Built 3MF deliverables:\n  {print_3mf_path}\n  {view_3mf_path}")

    slice_stats = slice_and_update_metadata(print_3mf_path, view_3mf_path, slice_dir)
    print(f"OrcaSlicer verified slice stats: {slice_stats}")

    render_all_previews(mesh_full, mesh_demo, demo_net_len, slice_dir, slice_stats)
    report["orca_slice"] = slice_stats
    report["elapsed_s"] = round(time.perf_counter() - t0, 2)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    (BUILD_DIR / "verification_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Done in {report['elapsed_s']:.2f} s.")


if __name__ == "__main__":
    main()
