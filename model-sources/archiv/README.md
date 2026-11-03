# Reference Image Archive

The source photos and analysis renders were removed after their corresponding
models were completed. The numbered contact sheets are retained so that the
tile numbers referenced in the measurement documents under `docs/` remain
traceable.

## duschscharnier_ersatz-referenzfotos-index.png

Contact sheet of the 25 reference photos for `models/duschscharnier_ersatz.stl`
(generator: `scripts/duschscharnier_ersatz.py`, measurements:
`docs/duschscharnier_ersatz_masse.md`).

| Tile | Original file |
| ---: | --- |
| 00 | model-sources/PXL_20260813_201653591.jpg |
| 01 | model-sources/PXL_20260813_201713762.jpg |
| 02 | model-sources/PXL_20260813_201753540.jpg |
| 03 | model-sources/PXL_20260813_201821328.jpg |
| 04 | model-sources/PXL_20260813_201929472.jpg |
| 05 | model-sources/PXL_20260813_201947062.jpg |
| 06 | model-sources/PXL_20260813_202034858.jpg |
| 07 | model-sources/PXL_20260813_202145252.jpg |
| 08 | model-sources/PXL_20260813_202209986.jpg |
| 09 | model-sources/PXL_20260813_202228705.jpg |
| 10 | model-sources/PXL_20260813_202310432.jpg |
| 11 | model-sources/PXL_20260813_202352474.jpg |
| 12 | model-sources/PXL_20260813_202415340.jpg |
| 13 | model-sources/PXL_20260813_202536941.jpg |
| 14 | model-sources/PXL_20260813_202654470.jpg |
| 15 | model-sources/PXL_20260813_202825241.jpg |
| 16 | model-sources/PXL_20260813_202902539.jpg |
| 17 | model-sources/PXL_20260813_202910703.jpg |
| 18 | model-sources/PXL_20260813_202922345.jpg |
| 19 | model-sources/PXL_20260813_204346991.jpg |
| 20 | model-sources/PXL_20260813_204404886.jpg |
| 21 | model-sources/PXL_20260813_204458880.jpg |
| 22 | model-sources/PXL_20260813_204541479.jpg |
| 23 | model-sources/PXL_20260813_204554333.jpg |
| 24 | model-sources/PXL_20260813_205449683.jpg |

## duschscharnier_ersatz-analyse-index.png

Contact sheet of analysis artifacts (caliper overlays from
`scripts/mess_hilfe.py`, STL renders, and video stills from
`scripts/render_vergleich.py`).

| Tile | Original file |
| ---: | --- |
| 00-07 | model-sources/analyse/late_00.png .. late_07.png |
| 08 | model-sources/analyse/PXL_20260813_202536941_ruler.png |
| 09 | model-sources/analyse/PXL_20260813_202654470_ruler.png |
| 10 | model-sources/analyse/PXL_20260813_204458880_ruler.png |
| 11-15 | model-sources/analyse/stl_bottom/front/iso/side/top.png |
| 16-27 | model-sources/analyse/video_00.png .. video_11.png |

## waeschespinne-reduzierring-referenzfotos-index.png

Contact sheet of the four reference photos for
`models/waeschespinne-reduzierring-67-50.2.stl` (Generator:
`scripts/waeschespinne_reduzierring.py`, measurements:
`docs/waeschespinne-reduzierring-masse.md`).

Note: The diameters read from these photos are outdated. The valid dimensions
are the newly user-confirmed 50,20 mm (pole) and 67,00 mm (sleeve) from
2026-09-27; the interim 60,00-mm sleeve assumption is also outdated.

| Tile | Original file | Evidence |
| ---: | --- | --- |
| 00 | PXL_20260916_153058161.jpg | Pole outer diameter, photo reading 43,04 mm (outdated) |
| 01 | PXL_20260916_153113313.jpg | Sleeve inner diameter, photo reading 60,48 mm (outdated) |
| 02 | PXL_20260916_153155947.jpg | Black failed print, measurement 35,85 mm |
| 03 | PXL_20260916_153218515.jpg | Black failed print, measurement 52,11 mm |

## modellauto-reifen-referenzfotos-index.png

Model-car replacement tire (`scripts/modellauto_reifen.py`,
`docs/modellauto-reifen-masse.md`). Photos from 2026-10-10.

| Tile | Original file | Evidence |
| ---: | --- | --- |
| 00 | PXL_20261010_115638099.jpg | Axial rim width 23,20 mm |
| 01 | PXL_20261010_115826962.jpg | Original tire fragment wall thickness 2,05 mm |
| 02 | PXL_20261010_115705004.jpg | Front rim ring Ø 22,54 mm |
| 03 | PXL_20261010_115723187.jpg | Overview of axle, intact tire, and rim without tire |
| 04 | PXL_20261010_115612975.jpg | Rib ring Ø 33,74 mm |
| 05 | PXL_20261010_115756377.jpg | Circumferential ring in rib ring, 2,29 mm |

Create new contact sheets with
`python scripts/make_contact_sheet.py <bildordner> --out model-sources/archiv/<modell>-index.png`.

## Ghoul's Grip

The two concept images remain under `model-sources/ghouls-grip/` during
prototyping; the numbered contact sheet is `_index.png`.

| Tile | Original file | Use |
| ---: | --- | --- |
| 00 | 01-blueprint-concept.jpg | Style, scissor motion, skull trigger |
| 01 | 02-render-concept.jpg | Material appearance, open candy hand |

## drache-referenzfotos-index.png

Contact sheet of the 25 stills extracted from the reference video (`PXL_20261014_105222309.mp4`) for `models/drache-view.3mf`, `models/drache-print.3mf`, and `models/drache.stl` (generators: `scripts/build_drache_blender.py` and `scripts/drache.py`, measurements: `docs/drache-masze.md`, verification report: `docs/drache-montage-und-kollisionspruefung.md`).

| Tile | Original file | Evidence / perspective |
| ---: | --- | --- |
| 00 | frame_01_f0000.jpg | Oblique front view from the right with 2-euro coin |
| 01 | frame_02_f0032.jpg | Front view with 2-euro coin |
| 02 | frame_03_f0064.jpg | Main front view with 2-euro coin (25,75 mm calibration reference) |
| 03 | frame_04_f0096.jpg | Oblique front-right view |
| 04 | frame_05_f0128.jpg | Right-side view |
| 05 | frame_06_f0160.jpg | Right rear-side view |
| 06 | frame_07_f0192.jpg | Rear/right-side view |
| 07 | frame_08_f0224.jpg | Rear view with red/black tail fin (omitted factory code `41204AFS`) |
| 08 | frame_09_f0256.jpg | Oblique rear-left view |
| 09 | frame_10_f0288.jpg | Oblique rear-left view, dorsal spikes |
| 10 | frame_11_f0320.jpg | Rear-left side view |
| 11 | frame_12_f0352.jpg | Left-side view |
| 12 | frame_13_f0384.jpg | Main left-side view (length and height calibration) |
| 13 | frame_14_f0416.jpg | Oblique front-left view |
| 14 | frame_15_f0448.jpg | Oblique front view from the left |
| 15 | frame_16_f0480.jpg | Front view of eyes & ear horns |
| 16 | frame_17_f0512.jpg | Oblique front/top view |
| 17 | frame_18_f0544.jpg | Oblique top view, wingspan & saddle collar |
| 18 | frame_19_f0576.jpg | Close-up of red tail-fin prosthesis with white skull emblem |
| 19 | frame_20_f0608.jpg | Close-up of tail fin & wing edge |
| 20 | frame_21_f0640.jpg | Close-up of head & green eyes |
| 21 | frame_22_f0672.jpg | Close-up of chest, front paws & claws |
| 22 | frame_23_f0704.jpg | Oblique top view with 2-euro coin |
| 23 | frame_24_f0736.jpg | Overall proportions from above with 2-euro coin |
| 24 | frame_25_f0768.jpg | Final view with 2-euro coin |

## butterfly-messer-referenzfotos-index.png

Contact sheet of the reference photo for `models/butterfly-messer-view.3mf`, `models/butterfly-messer-print.3mf`, and `models/butterfly-messer.stl` (generator: `scripts/butterfly_messer.py`, sources & licenses: `docs/butterfly-messer-quellen-und-lizenzen.md`, dimensions & mechanics: `docs/butterfly-messer-masse-und-mechanik.md`, print validation: `docs/butterfly-messer-druckvalidierung.md`).

| Tile | Original file | Evidence / perspective |
| ---: | --- | --- |
| 00 | 01-referenz-balisong.png | Classic skeletonized stainless-steel butterfly knife (closed & locked at the top on a black case, open with T-latch at the bottom) |
