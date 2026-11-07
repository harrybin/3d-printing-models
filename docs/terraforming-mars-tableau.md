# Terraforming Mars tableau: laminate-aligned 179 mm revision

The current integrated deliverable is
[`terraforming-mars-tableau-179mm-laminate-centered-blocks.3mf`](../models/terraforming-mars-tableau-179mm-laminate-centered-blocks.3mf).
It is derived from the previously coupon-fitted
[`terraforming-mars-tableau-179mm-loch1-zapfen3.3mf`](../models/terraforming-mars-tableau-179mm-loch1-zapfen3.3mf),
with a frozen intermediate baseline archived at
`model-sources/terraforming-mars-tableau/terraforming-mars-tableau-179mm-laminate-slider-cubes.3mf`
(SHA-256 `713571a0d9b614d4bd900dc8f501f84246de4cee3cda14080bddcf42440f57ad`).
The original user-supplied scaled project and fit coupons remain archived
unchanged under `model-sources/terraforming-mars-tableau/`.

The original model author and license are unknown; the repository MIT license
does not apply to model contents. Fit dimensions are based on the user's
physical coupon selection and the measured coupon meshes: socket Ø3.000 mm,
pin shaft Ø2.600 mm.

## Integrated layout

The final panel envelope is `238.401 x 179.000 mm`, around the user-measured
`227 x 168 mm` outer sealed-laminate outline. This leaves 5.701 mm on each long
side and 5.500 mm on each short side. The existing eight pin/socket joints are
preserved; no additional clips or laminate cuts were introduced. The
laminate's physical thickness/compression and the full assembly remain
untested.

All six resource windows, the central slider, the 65 cube openings and their
end positions use the established common photo registration. The slider is
centered; the lower-right rows retain the requested `+2.000 mm` shift. The
three additionally centered blocks use whole-block horizontal translations:
upper-left `-1.500 mm`, lower-left `-1.000 mm`, and upper-right `+0.500 mm`.
Relative to the marked screenshot's target centers, their centroid errors are
`+1.365 -> -0.135 mm`, `+0.855 -> -0.145 mm`, and `-0.001 -> +0.499 mm`,
respectively. The photo alignment uncertainty is about 1 mm, so these are
image-guided adjustments, not precision physical measurements.

Every standard aperture remains `8.640 mm` for an `8.500 mm` cube: only
`0.140 mm` nominal diametral clearance (`0.070 mm` per side) before print
variation. The 9.160 mm pocket pitch leaves 0.520 mm webs, while the printed
field pitch is 8.500 mm. Consequently, individual cells cannot all be centered
simultaneously; after the block translations, the maximum center residuals
are 3.145 mm upper-left, 2.645 mm lower-left, and 2.145 mm upper-right; the
other three groups remain within 1.646 mm. The three broad end positions
measure approximately `17.796 x 8.638 mm`. Aperture clearance is CAD-only:
cube insertion, elephant-foot effects and slicer extrusion have not been
tested.

The middle slider is now `109.898 x 8.640 mm`; its top edge is retained and
the opening extends `1.840 mm` farther downward than the previous 6.8 mm
slot. The CAD opening is cube-sized for the nominal 8.5 mm cube, but insertion
and slider operation have not been physically tested. The divider between
resource windows 5 and 6 has a `13.57°` ramp through the 2.5 mm front. Its
front-face transfer opening measures `8.640 mm`; the exported-mesh probe does
not prove a cube can transfer through the whole thickness or under print
tolerances.

Mounting fit remains eight Ø3.000 mm blind sockets and eight Ø2.600 mm pins.
Sockets are 2.000 mm deep with 0.500 mm floors; pin projection is 1.600 mm,
leaving 0.400 mm nominal axial clearance. The insertion sweep found no
unintended CAD intersection. All three original plates, object placements,
build transforms and unrelated material/process settings are preserved.

## Transparent-front test profile

The transparent front uses the previously approved dedicated filament slot:
0.10 mm layers; 20 mm/s configured wall, infill, gap and top speeds; two walls;
100% aligned single-direction infill; one 0.10 mm top shell layer with top
ironing; 220 °C normal and first-layer nozzle temperature (within the preset's
190–240 °C range); 20% part fan; 0% auxiliary fan; and calibrated 0.98 flow.
The bottom shell remains at zero. These surface changes are isolated to the
transparent front object; other filament slots, the rear, bed settings and
native filament routines are unchanged. The top layer and ironing are a
testable attempt to smooth the long exposed surface, not a proven optical or
surface-quality improvement.

The referenced “How to Print Glass” guide's core recipe already matches these
settings, so no additional settings were adopted. This is a profile comparison,
not proof of effective G-code speeds, optical transparency or print quality.

## Validation and limitations

The final exported meshes were re-imported and checked for expected envelope,
all 65 openings and end slots, socket/pin dimensions, blind floors, insertion
clearance and preservation of plate transforms. The 3MF ZIP archive passes CRC
validation. Targeted regression tests pass (5 tests), and catalog verification
passes on the staged PR tree (16 models / 33 outputs). The generic
`mesh_tool.py validate` command combines all three 3MF plates into one
aggregate and reports an oversized footprint; the project inspector confirms
three separate plates, and the generator validates the exported meshes
individually. The final image comparison uses one global photo transform
without local warping; its approximately 1 mm registration uncertainty and
the remaining per-field pitch drift are disclosed in the
[photo-validation report](terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-validation.json).

The exact updated 3MF was attempted with OrcaSlicer's `--slice=0` CLI command.
It exited `-18` before generating G-code because the saved
`retraction_distances_when_cut=0` is outside `[10,18]`. Earlier attempts on
the preceding layout also reported a missing referenced process preset;
AnycubicSlicerNext 2.0.0.3 crashed before producing G-code. No user/global
profile was changed. The saved global support setting remains
`enable_support=0`; this is not support-free validation. Print time, material
use, support paths and effective toolpath speeds are unknown. No physical cube
insertion, slider transfer, laminate fit, retention, surface-quality or
full-tableau assembly test has been performed.

## Reproducible files and evidence

- Generator: [`scripts/revise_terraforming_mars_tableau.py`](../scripts/revise_terraforming_mars_tableau.py)
- Photo comparison: [`scripts/compare_terraforming_mars_tableau_laminate.py`](../scripts/compare_terraforming_mars_tableau_laminate.py)
- Regression tests: [`tests/test_terraforming_mars_tableau_revision.py`](../tests/test_terraforming_mars_tableau_revision.py)
- [Exported-mesh and settings validation](terraforming-mars-tableau-179mm-laminate-centered-blocks-validation.json)
- [Photo registration report](terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-validation.json)
- [Three-plate 3MF preview](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-preview.png)
- [Before/after photo overlay](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-before-after.png)
- Closeups: [upper-left block](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-upper-left-5-closeup.png), [lower-left block](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-lower-left-zero-closeup.png), [upper-right block](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-upper-right-zero-closeup.png), [slider](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-slider-closeup.png), and [window 5-to-6 ramp](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-window5-to6-ramp-closeup.png)
