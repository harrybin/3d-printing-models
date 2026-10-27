# Butterfly Knife (`butterfly-messer`): OrcaSlicer Print Validation

## 1. Project and Profile Overview (`orcaslicer-print-validation`)

- **Druckprojekt:** [`models/butterfly-messer-print.3mf`](../models/butterfly-messer-print.3mf)
- **View project (3 states):** [`models/butterfly-messer-view.3mf`](../models/butterfly-messer-view.3mf) (`0°` Open, `90°` flipping motion, `180°` closed & locked)
- **Individual and preview STLs:** [`models/butterfly-messer.stl`](../models/butterfly-messer.stl) and 14 print-oriented individual-part STLs `models/butterfly-messer-*.stl`
- **OrcaSlicer-Version:** OrcaSlicer CLI `2.3.2` (`C:\Program Files\OrcaSlicer\orca-slicer.exe`)
- **Druckerprofil:** `Anycubic Kobra S1 0.4 nozzle`
- **Build plate:** `Textured PEI Plate` (`250 × 250 mm`)
- **Process profile:** `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle` (`layer_height = 0.2 mm`, `first_layer_height = 0.2 mm`)
- **Filament profile (2 ACE Pro slots):** `Anycubic PLA @Anycubic Kobra S1 0.4 nozzle`
  - Slot 1: **Silver-gray PLA** (`#C0C7D0`) — blade & T-latch (plate 1)
  - Slot 2: **Anthracite PLA** (`#2D333B`) — 4 handle scales (`Safe` & `Bite`, lower/upper each), 4 D-bolts & 4 U-clips (plate 2)
- **Verified global project standards:**
  - `seam_position = random`
  - `ironing_type = top`
  - `enable_support = 1` (`support_type = normal(auto)`, `support_threshold_angle = 30`, `support_on_build_plate_only = 1`, `support_critical_regions_only = 1`)
  - `xy_hole_compensation = 0.05 mm`, `elefant_foot_compensation = 0.12 mm`

---

## 2. Object Overrides for Function, Swing Weight & Strength

| Part group | Objects | Wall loops (`wall_loops`) | Infill (`sparse_infill_density`) | Infill pattern | Special settings |
| --- | ---: | ---: | ---: | --- | --- |
| Blade (`butterfly-messer-klinge`) | 1 | `4` (`1.6 mm`) | `60%` | `rectilinear` | Double-sided 45° putty-blade bevel, laid flat without supports |
| T-latch (`butterfly-messer-riegel`) | 1 | `4` (`1.6 mm`) | `100%` | `rectilinear` | Solid infill for high tensile and bending strength |
| Handle scales (`griff-safe/bite-unten/oben`) | 4 | `4` (`1.6 mm`) | `55%` | `gyroid` | High swing weight for realistic flipping inertia |
| D-bolts & U-clips (`bolzen-*`, `clip-*`) | 8 | `5` (`2.0 mm`) | `100%` | `rectilinear` | `brim_type = outer_only` (`2 mm`), printed with the handle scales on plate 2 in anthracite PLA |

---

## 3. Verified Slicing Results per Build Plate (0.00 g Support!)

Both build plates were sliced with automatic supports enabled (`enable_support = 1`) using the OrcaSlicer CLI. Thanks to the self-supporting design (45° countersink cones in the lower handle scales; upper handle scales printed on their flat inner face at `Z = 8.40 mm` with 45° conical roofs over the pin pockets; and D-bolts printed on their continuous flat with a 45° head transition and three-sided clip groove), **no plate requires support material**:

| Plate | Name / ACE Pro color | Included parts (14 total) | Print time | Filament (total) | Support | Support preview |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| **1** | `Silver-gray - blade & T-latch` (`#C0C7D0`) | `klinge`, `riegel` (2 parts) | `16m 35s` (`995 s`) | `4.30 g` (`1442.53 mm` / `3470 mm³`) | **`0.00 g`** (`0.00 mm`) | [`butterfly-messer-print-plate-1-supports.png`](images/butterfly-messer-print-plate-1-supports.png) |
| **2** | `Anthracite - 4 handle scales, 4 D-bolts & 4 U-clips` (`#2D333B`) | 4× `griff-*`, 4× `bolzen-*`, 4× `clip-*` (12 parts) | `1h 28m 52s` (`5332 s`) | `20.60 g` (`6905.86 mm` / `16610 mm³`) | **`0.00 g`** (`0.00 mm`) | [`butterfly-messer-print-plate-2-supports.png`](images/butterfly-messer-print-plate-2-supports.png) |
| **Total** | **2 single-color plates (no color-change purge)** | **14 parts** | **`1h 45m 27s` (`6327 s`)** | **`24.90 g` (`8348.39 mm` / `20080 mm³`)** | **`0.00 g`** | **Status: `verified`** |

---

## 4. Preview and Support Evidence Images

- **Full view-project preview (`-view.3mf`, 3 states):** [`docs/images/butterfly-messer-view-preview.png`](images/butterfly-messer-view-preview.png)
- **Full print-project preview (`-print.3mf`, 3 plates):** [`docs/images/butterfly-messer-print-preview.png`](images/butterfly-messer-print-preview.png)
- **Combined presentation overview:** [`docs/images/butterfly-messer-presentation.png`](images/butterfly-messer-presentation.png)

![Butterfly knife presentation overview](images/butterfly-messer-presentation.png)

## 5. Remaining Practical Notes for the First Print

- **U-clip snap fit (`0.15 mm` clearance):** The 4 U-clips on plate 3 are designed to snap into the bolt grooves without play. If the PLA used expands more, `CLIP_CLEARANCE` in [`scripts/butterfly_messer.py`](../scripts/butterfly_messer.py) can be increased from `0.15 mm` to `0.20 mm`.
- **Free pivot movement (`0.30 mm` radial and axial clearance):** After the printed parts cool, carefully remove any brim residue from the D-bolts so the blade and T-latch rotate freely on the bolt shafts.
