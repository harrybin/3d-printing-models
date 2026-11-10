# Toothless (Night Fury) – Assembly, Collision & Slicer Verification Report

## 1. Complete Model & Bill of Materials (BOM)

- **Overall dimensions (assembled):** `77.66 × 46.58 × 60.97 mm` (reference target from 2-euro coin calibration: `~78,0 × 45,5 × 60,5 mm`)
- **Tail underside:** Modeled smooth; the embossed factory/copyright code (`41204AFS`) was omitted entirely as requested.
- **Color strategy:** 5 precisely fitted, interlocking plug-in parts on 4 single-color build plates (`0,00 g` color-change/purge waste).

| Part | File (`models/`) | ACE Pro slot & color | Facets | Watertight | Euler number | Components | Volume (`mm³`) | Print-position dimensions (`mm`) |
| --- | --- | --- | ---: | :---: | ---: | ---: | ---: | --- |
| `drache-koerper` | `models/drache-koerper.stl` | Slot 1: Body - black PLA (`#1C1E21`) | 46288 | `True` | `2` | `1` | `21433.9` | `77.66 × 46.58 × 60.97` |
| `drache-auge-links` | `models/drache-auge-links.stl` | Slot 2: Eyes - light green PLA (`#4CC936`) | 1488 | `True` | `0` | `1` | `50.2` | `6.50 × 4.70 × 2.95` |
| `drache-auge-rechts` | `models/drache-auge-rechts.stl` | Slot 2: Eyes - light green PLA (`#4CC936`) | 1488 | `True` | `0` | `1` | `50.2` | `6.50 × 4.70 × 2.95` |
| `drache-schwanzflosse-links-rot` | `models/drache-schwanzflosse-links-rot.stl` | Slot 3: Tail fin - red PLA (`#D62828`) | 226 | `True` | `2` | `1` | `397.9` | `13.60 × 15.90 × 2.90` |
| `drache-emblem-weiss` | `models/drache-emblem-weiss.stl` | Slot 4: Viking emblem - white PLA (`#F4F5F7`) | 290 | `True` | `2` | `1` | `25.3` | `6.90 × 5.30 × 1.37` |

## 2. Collision and Insertion-Path Check (25-Step Manifold Sweep)

All plug-in joints were checked for intersection volume with `manifold3d` along their full linear insertion paths (25 evenly spaced steps from outside the body to the final stop):

| Inserted part | Target part | Insertion vector (world XYZ) | Fit clearance (`mm`) | Static intersection volume (`mm³`) | Max. sweep intersection volume (`mm³`) | Status |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| `drache-auge-links` | `drache-koerper` | `(-0.6804, -0.6004, -0.4203)` | `0.15` | `0.00000` | `0.00000` | **PASS** |
| `drache-auge-rechts` | `drache-koerper` | `(-0.6990, +0.5792, -0.4194)` | `0.15` | `0.00000` | `0.00000` | **PASS** |
| `drache-schwanzflosse-links-rot` | `drache-koerper` | `(-0.0000, -1.0000, -0.0000)` | `0.15` | `0.00000` | `0.00000` | **PASS** |
| `drache-emblem-weiss` | `drache-schwanzflosse-links-rot` | `(-0.9207, -0.0000, -0.3903)` | `0.12` | `0.00000` | `0.00000` | **PASS** |

### Assembly order
1. **Green eyes (`drache-auge-links`, `drache-auge-rechts`):** Press them into the two eye sockets of the black head from an oblique front/outside direction. The vertical slit-pupil bars integrated into the black head fit exactly through the slits in the green eye inserts.
2. **White Viking skull emblem (`drache-emblem-weiss`):** Press it from above into the interlocking recess in the left red tail-fin prosthesis (`drache-schwanzflosse-links-rot`) (`0,12 mm` press fit).
3. **Red tail-fin prosthesis (`drache-schwanzflosse-links-rot`):** Insert it from the left side along the Y-axis (`(0, -1, 0)`), with its asymmetric tongue engaging the slot at the tail tip of the black body (`0,15 mm` clearance).

## 3. Verified OrcaSlicer Print Data (`models/drache-print.3mf`)

- **Printer profile:** `Anycubic Kobra S1 0.4 nozzle`
- **Build plate:** `Textured PEI Plate`
- **Process profile:** `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle` (`seam_position=random`, `ironing_type=top`, `enable_support=1`, `support_type=tree(auto)`)
- **Total print time (all 4 plates):** `1h 29m 33s` (`5373 s`)
- **Total filament required:** `18.04 g` (`6049.03 mm`, `14550 mm³`)
- **Support filament:** `0.79 g` (`266.04 mm`, `640 mm³`)

| Plate | Description | Print time | Total filament (`g` / `mm`) | Support portion (`g` / `mm`) | Status |
| :---: | --- | ---: | ---: | ---: | :---: |
| 1 | Plate 1 - Body - black PLA | `1h 18m 04s` (`4684 s`) | `17.36 g` (`5820.09 mm`) | `0.79 g` (`266.04 mm`) | **VERIFIED** |
| 2 | Plate 2 - Eyes - light green PLA | `3m 50s` (`230 s`) | `0.15 g` (`50.60 mm`) | `0.00 g` (`0.00 mm`) | **VERIFIED** |
| 3 | Plate 3 - Tail fin - red PLA | `4m 57s` (`297 s`) | `0.48 g` (`161.46 mm`) | `0.00 g` (`0.00 mm`) | **VERIFIED** |
| 4 | Plate 4 - Viking emblem - white PLA | `2m 42s` (`162 s`) | `0.05 g` (`16.88 mm`) | `0.00 g` (`0.00 mm`) | **VERIFIED** |

### Orientation and support evidence
- **Plate 1 (`drache-koerper`):** Stands on the four flattened paw soles (`Z = 0,000 mm`). This produces only minimal tree support from the build plate (`0,79 g` beneath the chin/belly/wing tips), while the top of the head, ear horns, dorsal spikes, saddle, and tail fin remain 100% free of support contact points.
- **Plates 2, 3, and 4 (`drache-auge-links`, `drache-auge-rechts`, `drache-schwanzflosse-links-rot`, `drache-emblem-weiss`):** Each lies on its completely flat back at `Z = 0,000 mm` and requires exactly **`0,00 g` support**, despite auto-support being enabled (`enable_support=1`).
