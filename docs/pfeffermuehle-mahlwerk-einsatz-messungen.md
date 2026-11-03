# Pepper Mill Grinder: Insert (Drive Coupling)

Generator: `scripts/pfeffermuehle_mahlwerk_einsatz.py`
Output: `models/pfeffermuehle-mahlwerk-einsatz.stl`
Reference photos: `model-sources/pfeffermuehle-mahlwerk/` (index: `_index.png`)

## Function

The grinder's pentagonal drive shaft passes through the center of the insert
(a full through-hole, explicitly confirmed by the user despite the resulting
thinner remaining wall). The insert is cylindrical. Beneath the round collar at
the top are 4 semicircular lugs (spaced 90° apart), which engage with the
four-lobed ("cloverleaf") recess in the grinder housing (visible in image tile
02, embossed "CRUSHGRIND CO"). This makes the insert turn with the pentagonal
shaft and transfer torque through the lugs to the grinder housing/burr.

## Reference Tile Mapping (Contact Sheet)

| Tile | File | Shows |
| --- | --- | --- |
| 00 | `...165635927.jpg` | Pentagonal shaft on grinder, calipers 5,75 mm (across flats) |
| 01 | `...170606863.jpg` | Hole in old (damaged) insert, calipers 7,06 mm |
| 02 | `...170541868.jpg` | Underside of old insert/housing, 4-lug cloverleaf pattern, embossed "CRUSHGRIND CO" |
| 03 | `...165523655.jpg` | Broken fragment detail, calipers 8,88 mm (uncertain attribution) |
| 04 | `...165440445.jpg` | Overall height of grinder/old part, calipers 17,01 mm |
| 05 | `...170527313.jpg` | Old insert, external dimension, calipers 12,59 mm |
| 06 | `...170742712.jpg` | Broken fragment of old insert, wall thickness 2,12 mm |

## Dimension Table

| Dimension | Value | Source | Status |
| --- | --- | --- | --- |
| Overall insert height | 17,0 mm | user statement, confirmed by tile 04 (17,01 mm) | measured/confirmed |
| Pentagonal shaft across flats | 5,75 mm | tile 00 | measured |
| Pentagonal hole in insert (target) | 6,00 mm across flats (diagonal 6,31 mm) | 5,75 mm + 0,25 mm clearance (near CrushGrind standard ~6 mm, see research) | derived |
| Old insert outer Ø (max.) | 12,59 mm | tile 05 | measured |
| Hole in damaged fragment | 7,06 mm | tile 01 | measured, but **not a design dimension** - according to the user, the old intact insert had at least 1 mm wall thickness everywhere; 7,06 mm is the opening widened by the break, not the original hole |
| Broken fragment wall thickness | 2,12 mm | tile 06 | measured (reference for minimum wall thickness) |
| Lug pattern | 4 lugs, spaced 90° apart | tile 02, confirmed by user | confirmed |
| Lug length including collar | 7,08 mm | user statement | measured/confirmed |
| Collar height | 2,0 mm | user-confirmed standard assumption | assumption |

## Design Decisions (new, not copied 1:1 from the old part)

- Shaft: Ø 9,0 mm, smooth cylindrical up to a height of 9,92 mm
- Lug zone: 4 separate round lugs, each with a radius of 1,65 mm and centers
  on the shaft radius (4,5 mm). Each lug overlaps the cylindrical shaft by
  1,65 mm, but the lugs do not touch one another. This matches the four
  separate round recesses in tile 02. The lugs are 5,08 mm high; together with
  the collar, they match the measured dimension of 7,08 mm.
  - Tip radius (through a lug): 6,15 mm (Ø 12,3 mm circumscribed circle)
  - Between the lugs, the shaft remains visible at radius 4,50 mm; the round
    lugs do not touch.
- Collar: round cap disc, Ø 12,3 mm x 2,0 mm high, flush over the lugs
- Pentagonal through-hole: 6,0 mm across flats, continuous through the full 17 mm height
- Resulting minimum wall thickness around the pentagonal hole: 1,35 mm at the
  cylindrical shaft; 3,00 mm at the lug tips/collar. This meets the 1 mm
  minimum wall thickness.

The height distribution follows the confirmed lug length including collar:
9,92 mm smooth shaft + 5,08 mm lug zone + 2,00 mm collar = 17,00 mm.

## Research

CrushGrind grinders typically use a pentagonal shaft with ~6 mm across flats as
the coupling standard (public manufacturer information, e.g.
crushgrind.ca/pages/instructions). This supports the selected 6,0-mm target
hole as a sensible, slightly oversize clearance fit for the measured
5,75-mm shaft.

## Printability

- Material: PLA/PETG, 0,4 mm nozzle
- Minimum wall thickness everywhere >= 1,35 mm (well above the 0,8 mm baseline)
- Original model (shaft down): 0,2 % unsupported
  (`mesh_tool.py overhang`), almost entirely self-supporting.
- Print-oriented file `models/pfeffermuehle-mahlwerk-einsatz-druckorientiert.stl`
  (collar down, shaft up): 33,9 % unsupported; supports are required for this
  intentionally chosen orientation.
- Seam/top surfaces (>=89°) 55,17 mm² - flat top/bottom surfaces, uncritical
- Mesh: watertight, manifold, euler_number 0 (correct for a through-hole), no
  degenerate facets
