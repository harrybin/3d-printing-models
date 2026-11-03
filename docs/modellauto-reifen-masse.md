# Model Car Replacement Tire – Dimensions

## Completion / Archive

The user reported the model complete on 2026-10-11 and approved it for archiving.
The generator, STL, print project, presentation render, and reference index
remain in the repository at the paths listed below.
The 3MF later saved by the user is the archived project version. Its mesh data
and the print profiles listed below are unchanged from the originally sliced
OrcaSlicer project; the saved project version itself does not contain complete
slice results. The time and material estimates below therefore come from the
original slice. No specific fit or grip assessment was provided.

Reference index: `model-sources/archiv/modellauto-reifen-referenzfotos-index.png`
(see `model-sources/archiv/README.md` for the tiles).

| Feature | Dimension | Source | Confidence |
| --- | ---: | --- | --- |
| Tire outer diameter | 37,20 mm | user measurement of intact tire, 2026-10-10 | High |
| Tire width | 26,00 mm | user measurement of intact tire | High |
| Wheel rim rib ring, outer Ø (tire seat) | 33,74 mm | calipers, tile 04 | High |
| Front wheel rim ring, outer Ø | 22,54 mm | calipers, tile 02 | High |
| Axial rim width | 23,20 mm | calipers, tile 00 | High |
| Circumferential ring in rib ring, width | 2,29 mm | calipers, tile 05 (not modeled) | High |
| Original tire wall thickness | 2,05 mm | calipers on broken fragment, tile 01 | High |
| Seat fit clearance (Ø) | 0,20 mm | design choice: press fit based on printer profile | Medium – test print |
| Tire-seat inner Ø | 33,94 mm | derived: 33,74 + 0,20 | Medium |
| Radial tread thickness | 1,63 mm | derived: (37,20 − 33,94) / 2 | High |
| Front lip opening | 23,00 mm | derived: 22,54 + ≈0,45 clearance | Medium |
| Front lip thickness | 1,40 mm | derived: (26,0 − 23,2) / 2, matching original sidewall | Medium |

## Design

PLA is rigid and must not be glued (user requirement). The tire is therefore a
sleeve with a front lip: it is pushed onto the rib ring from the axle side until
the lip rests against the front of the wheel rim. It is retained by a press fit.
The rear is open (with an internal lead-in chamfer).

Print with the lip/end face on the build plate, without supports. If the tire is
too loose, reduce `FIT_CLEAR` to 0,10 mm; if it binds, increase it to 0,30 mm.

## Outputs and Slice

- `models/modellauto-reifen.stl` (generator: `scripts/modellauto_reifen.py`)
- `models/modellauto-reifen-print.3mf` (OrcaSlicer print project)
- Render: `docs/images/modellauto-reifen-render.png`

OrcaSlicer 2.4.2, printer `Anycubic Kobra S1 0.4 nozzle`, process
`0.20mm Standard @Anycubic Kobra S1 0.4 nozzle`, Filament
`Anycubic PLA @Anycubic Kobra S1 0.4 nozzle`: slice successful, 20 min 3 s,
6,28 g / 2,11 m PLA, no supports, 2 walls, 15 % infill.

Asset research: generic rotational body (sleeve with lip) without
vehicle-specific shape; designed from measurements, no third-party license.
