# 3.5 mm Cable Channel (Slim Profile, Rear Slot, Front Press-On, White) — Dimensions and Design Documentation

## 1. Requirements and Constraints

- **Part**: A maximum-length, slim, white cable channel (`kabelkanal-3-5mm`) for a round cable with **Ø 3.50 mm**. The back is flat and has a **rear cable snap-in opening**, the visible front is **fully closed**, and the part must print **without supports (`0.00 g` support with `enable_support=1, tree(auto)`)** on the Anycubic Kobra S1 Combo + ACE Pro.
- **Joint ("press on from the front in one motion")**: A slim **front press-on saddle/hood joint (`Saddle-Hood-Joint`)** without a double-wall coaxial sleeve. Once Segment 1 is installed on the wall/cable, Segment 2 is pressed onto the cable and over Segment 1's saddle pin **from the front in one motion (`-Z` in the installed orientation)**. A vertical T-shaped cross-rib (`KEY_RIB_PROTRUSION = 0.34 mm`) positively locks the channels against axial separation (`±X`), while a horizontal snap bead (`SNAP_BEAD_PROTRUSION = 0.22 mm`) prevents lifting toward the front (`+Z`).
- **Build-plate limit and five modular variants (two 3MF files only: `-print.3mf` and `-view.3mf`; no individual STLs)**: Anycubic Kobra S1 (`250.0 mm × 250.0 mm`). All **five print variants** are embedded as objects directly on **Plate 1** of `models/kabelkanal-3-5mm-print.3mf` (`Y = 89 / 107 / 125 / 143 / 161 mm`, `18.0 mm` center spacing = `11.2 mm` clearance) and in the three assembly states in `models/kabelkanal-3-5mm-view.3mf` (no separate `models/*.stl` files):
  1. `kabelkanal-3-5mm-mitte-beidseitig`: **242.00 mm center channel** with a connector at the left (`-X` snap-on saddle) and right (`+X` hood cap); `232.00 mm` net grid spacing.
  2. `kabelkanal-3-5mm-abschluss-links`: **242.00 mm left-end channel**; smooth, unstepped end at left (`-X`) with the cable bore and rear slot continuing through it, and a hood cap at right (`+X`).
  3. `kabelkanal-3-5mm-abschluss-rechts`: **242.00 mm right-end channel**; a snap-on saddle at left (`-X`) and a smooth end at right (`+X`) without a hood-cap recess (`232.00 mm` visible profile + `10.00 mm` saddle).
  4. `kabelkanal-3-5mm-einzeln-ohne-verbindung`: **242.00 mm single/short channel without connectors**, with smooth ends at both left (`-X`) and right (`+X`), using the full build-plate length.
  5. `kabelkanal-3-5mm-10cm-rechts`: **100.00 mm (10 cm) fitting/end piece**; smooth, unconnected end at left (`-X`) and a hood cap at right (`+X`).

## 2. Reusable 3D Asset Research (`research-reusable-3d-assets`)

- **Finding**: This is a functional, parametric engineering part with no organic or sculptural motif. Standard cable channels are too wide/high (`>= 10 × 10 mm`) for a single `3.5 mm` cable and do not provide a one-piece front press-on saddle/hood joint.
- **Decision**: Fully parametric original design in Python (`scripts/kabelkanal_3_5mm.py`) following `create-ascii-stl`, `reversible-fdm-joints`, and `orcaslicer-support-minimization`. License/provenance: original repository design (`MIT`).

## 3. Dimension and Tolerance Table (`research-part-specs`) — Revision v2 After a Physical Print Test

After the first physical print, the user reported that the `3.5 mm` cable could not be pressed into the channel ("das Kabel läss sich nicht reindrücken das ist zu massiv") and that more room might also be needed inside the channel ("ggf. inner auch etwas mehr als nur die 3.5mm plaz lassen"). Revision v2 therefore specifically changed the **inner bore, slot throat, entry funnel, snap-lip height, spring-arm wall thickness, and slicer wall count**:

| Parameter | Script symbol | Previous (v1) [mm] | Updated (v2) [mm] | Source / rationale | Confidence |
| --- | --- | ---: | ---: | --- | --- |
| Nominal cable diameter | `CABLE_DIAMETER` | `3,50` | `3,50` | User requirement ("für ein Kabel der Stärke 3,5mm") | Confirmed (user) |
| Radial / diametral bore clearance | `CABLE_RADIAL_CLEARANCE` | `0,18` (`+0,36` Ø) | **`0,40` (`+0,80` Ø)** | Generous internal clearance for cable tolerances, jacket waviness, and FDM bore shrinkage | Design estimate (test print recommended) |
| Cable-channel bore | `2 * BORE_RADIUS` | `Ø 3,86` (`R = 1,93`) | **`Ø 4,30` (`R = 2,15`)** | Center at `Z_print = 3,10 mm` (`Z ∈ [0,95, 5,25] mm`); even a `Ø 4,10 mm` test pin passes with `0,0000 mm³` collision volume; closed visible front wall is `0,95 mm` (6 layers) | Derived (CAD-verified; real cable still to be tested) |
| Slim outer profile (`width × height`) | `OUTER_WIDTH × OUTER_HEIGHT` | `7,20 × 5,20` | **`6,80 × 5,40`** | Narrower outer width (`6,80 mm`) intentionally reduces the side wall next to the `Ø 4,30 mm` bore to flexible **`1,25 mm` spring arms** | User requirement ("zu massiv" -> flexible) |
| Side spring-arm wall thickness (at bore centerline) | `Y_OUTER - BORE_RADIUS` | `1,67` (3 walls = rigid) | **`1,25` (2 walls)** | Bending stiffness $\propto (1,25 / 1,67)^3 = \mathbf{0,419}$ (**58% softer**); more compliant with `wall_loops = 2` and `xy_hole_compensation = 0,08 mm` | Elasticity calculation / estimate |
| Rear cable snap-in slot throat | `SLOT_THROAT_WIDTH` | `2,75` (`0,75` undercut) | **`3,20` (`0,30` undercut)** | Requires only **`0,15 mm` deflection per side** (instead of `0,375 mm`) while still positively retaining the `3,50 mm` cable (`3,20 mm < 3,50 mm`) | Design estimate (physical cable test remains open) |
| Rear snap-in slot chamfer (entry funnel) | `SLOT_ENTRY_WIDTH` | `3,10` (`< 3,50` cable!) | **`3,90` (`±1,95`, `0,58` deep)** | The funnel opening (`3,90 mm`) is now **wider than the `3,50 mm` cable**, allowing the cable to self-center in the slot before pressing it in | Functional dimension |
| Vertical snap-lip web height at the throat | `Z_THROAT_TOP - z_throat_bot` | `0,497` | **`0,284`** | Short, rounded snap nose (`Z = 4,54 .. 4,82 mm`); calculated insertion force falls to **`16,8%` (~6× easier)** and insertion work to **`6,7%` (~15× easier)** vs. v1 | Mechanical model calculation |
| Visible front (`Z_print = 0,00 mm`) | `FRONT_BEVEL` | `1,20 × 45°` | **`1,10 × 45°`** | Closed, smooth visible front (`4,60 mm` end-face + `1,10 mm × 45°` chamfers on both sides, `0,00 mm²` critical overhang) | Support-free proof |
| Flattened rear (`Z_print = 5,40 mm`) | `Y_OUTER - Y_ENTRY` | `2 × 2,05` | **`2 × 1,45`** | Two flat wall-contact strips (`Y ∈ [-3,40, -1,95]` and `[+1,95, +3,40]`), smoothed during printing with `ironing_type=top` | Design dimension |
| Lengths of five print variants (+ test piece) | `VARIANT_SPECS` | `4 × 242,00` | **`4 × 242,00` + `1 × 100,00` (+ `35,00`)** | Four maximum-length pieces (`242,00 mm`: left, center, right, single) plus one **`100,00 mm` (`10 cm`) piece with a right-only (`+X`) connector**, all on Plate 1 | User requirement |
| Saddle / hood-cap overlap length | `CONNECTOR_LENGTH` / `SOCKET_DEPTH` | `10,00` / `10,10` | **`10,00` / `10,10`** | Inner `-X` snap-on saddle (`10,00 mm`, `Y_SADDLE_SPINE = 1,15 mm`, `Z_SADDLE_SHOULDER = 1,68 mm` for a support-free chamfer of `>= 51°`); outer `+X` hood cap (`10,10 mm` with `1,03 mm`-wide first-layer contact strips on `Z = 0,00 mm`) | FDM fit and 100% support-free |
| Saddle width / hood-cap arm thickness | `2 * Y_SADDLE_BASE` | `4,80` (`±2,40`) | **`5,00` (`±2,50`)** | `0,35 mm` saddle wall around the `Ø 4,30 mm` bore plus a `0,78 mm` outer hood-cap arm (`0,12 mm` flank clearance per side) | FDM fit |
| Vertical T-shaped cross-rib (`±X` positive lock) | `KEY_RIB_PROTRUSION` / `KEY_SLOT_DEPTH` | `0,34` / `0,36` | **`0,20` / `0,22`** | Prevents axial separation with `5,00 mm` ahead of the shoulder (`0,5222 mm³` positive-lock engagement) | Functional dimension |
| Horizontal snap bead (`±Z` click-lock) | `SNAP_BEAD_PROTRUSION` / `SNAP_GROOVE_DEPTH` | `0,22` / `0,24` | **`0,16` / `0,18`** | At `Z_print = 3,35 mm` (`±0,42 / ±0,48 mm` ramps, `>= 69°` slope), it snaps into place when pressed on from the front (`0,0527 mm³` snap-through, `0,0000 mm³` collision in the final position) | Functional dimension |

> **Physical fit-risk note (`research-part-specs`)**: The updated dimensions (`Ø 4,30 mm` bore, `3,20 mm` throat, `3,90 mm` entry funnel, `1,25 mm` spring arms with two wall lines, and `xy_hole_compensation = 0,08 mm`) are calculated and volume-probe-checked for an approximately 6× lower insertion force. Until another physical test print is tried with the user's actual `3.5 mm` cable (for example, using `models/kabelkanal-3-5mm-teststueck-35mm.stl`), these dimensions remain **design estimates**.

## 4. Print Orientation and OrcaSlicer Evidence (`0,00 g` Support)

- **Print orientation (`models/kabelkanal-3-5mm.stl`, `models/kabelkanal-3-5mm-print.3mf`)**:
  The closed visible front rests on the Textured PEI build plate (`Z_print = 0,00 mm`), while the flattened, slotted rear and hood-cap pocket open upward (`+Z_print = 5,20 mm`) and are smoothed with `ironing_type = top`. This avoids **a closed tunnel ceiling above an open bottom slot**, so OrcaSlicer `2.3.1`, with `enable_support=1` and `support_type=tree(auto)`, generates exactly **`0,00 g` support (`0` support paths)**.
- **Installed orientation (`models/kabelkanal-3-5mm-view.3mf`, `docs/images/kabelkanal-3-5mm-presentation.png`)**:
  Rotated `180°` around the X axis (`_to_installed_wall_mesh`) so the flat, slotted rear rests against the wall (`Z_wall = 0,00 mm`), the closed visible front faces the viewer (`Z_wall = +5,20 mm`), and the next segment is pressed onto the cable and saddle pin from the front in one motion (`-Z_wall`).
