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

The two front-panel build items are turned 180° in the XY plane around build Z
to match the requested top/bottom presentation. This is an in-plane rotation,
not a face flip: front faces and bed-contact sides are unchanged. Only the
front panels on plates 1 and 3 are rotated; the rear panel on plate 2, its
transform, plate order, and all object geometry remain unchanged. The embedded
front-plate preview images are rotated to match the updated build transforms.

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

The six large windows are now all `43.000 mm` high. The upper-left window is
`86.000 mm` wide, expanded to the left while retaining its right edge. Window 4
is `69.779 mm` wide and already exceeds the requested 69 mm minimum; window 6
is `69.000 mm` wide, expanded to the right while retaining its left edge. The
nearest window-to-window web is `1.720 mm`, between windows 5 and 6, and the
minimum window-to-cube clearance is `2.663 mm`. These are exported-CAD
clearances; the photo-to-model registration is estimated at approximately
1 mm, and printed clearances have not been tested.

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
and slider operation have not been physically tested. The transition ramp is
now aligned to the printed-front reference: in that view window 5 is left of
window 6, and the ramp rises in the 5-to-6 direction. Earlier diagrams used
the mirrored model-X orientation and showed the slope backwards. The solid
ramp spans the complete `42.754 mm` length of the divider and has an
`8.640 mm` horizontal run from window 5 to window 6. This is wider than the
measured `4.1769 mm` web between windows 4 and 5, as explicitly approved to
make the slope shallower. It extends through the full `2.500 mm` panel
thickness at `16.14°`; it is solid material, not a cutout. Exported-mesh
sections confirm a monotonic rise through the full thickness, with no upper
shelf; probes confirm material below and free space above the slope at eleven
positions along the run and three positions along the divider. A continuous
CAD swept-volume check of an 8.5 mm cube found no intersection at three
positions across the divider and three offsets above the ramp. This verifies
only the modeled path, not physical cube transfer, sliding force, structural
strength, or physical fit.
[The XZ profile](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-ramp-section.png)
and [mesh-derived divider cross-section](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-window5-to6-web-closeup.png)
show the corrected slope direction and full-length ramp.

## Victory-point window and 10-cube arrow ledges

The small victory-point window is now `18.248 x 13.610 mm`, with exported
bounds `X [-100.176, -81.928]`, `Y [3.425, 17.035] mm`. Relative to the
preceding layout it moves `2.000 mm` right, loses `6.000 mm` from its left
edge, and is shortened `1.000 mm` at both top and bottom. Its interior remains
solid; no additional inner opening is present in the source geometry.

The web between this window and the adjacent zero-cube field is `3.712 mm`
wide by `8.640 mm` high. The front is recessed `1.500 mm`, leaving a
`1.000 mm` rear layer. This means the window and zero-cube field join through
the front recess; the rear layer is the remaining connection. This thin web
was verified in CAD, not by a physical strength test.

All six 10-cube end slots retain their `17.796 x 8.638 mm` front openings.
The 8.5 mm cube aperture remains clear through the full front thickness.
Behind each 10-cube field, the original arrow-shaped rear opening is retained,
leaving a rear-flush `1.000 mm` support floor that is recessed `1.500 mm` from
the front. Exported-mesh probes found zero cube intersection in all six
10-cube fields and `60.4–61.5 mm²` CAD contact area for the neighboring
overrun cube. These probes establish geometry only; they do not prove that the
thin ledges will survive handling or printing.

Mounting fit remains eight Ø3.000 mm blind sockets and eight Ø2.600 mm pins.
Sockets are 2.000 mm deep with 0.500 mm floors; pin projection is 1.600 mm,
leaving 0.400 mm nominal axial clearance. The insertion sweep found no
unintended CAD intersection. All three original plates, object placements,
build transforms and unrelated material/process settings are preserved.

## Transparent-front test profile and evidence

The transparent front has its own filament slot and object overrides. The
current profile keeps 0.10 mm layers, two walls, 100% aligned single-direction
infill, and configured 20 mm/s wall/infill/gap/top speeds. To target the
reported roughness on long runs, both object infill directions are now 90°:
on the 238.401 × 179.000 mm panel this changes the nominal straight raster path
from the 238.401 mm long axis to the 179.000 mm short axis (about 25% shorter).
The top-facing surface uses two 0.10 mm shell layers (0.20 mm total) and
top-only ironing. Those changes apply only to transparent-front object 6;
they do not edit CAD geometry, hole/ramp walls, pins, or the rear/material
profiles. The Cool Plate selection and its transparent-slot temperature change
are described below; other filament slots and their bed-temperature values
remain unchanged.

The reported parallel bands look consistent with the 100% aligned extrusion
paths being visible through the translucent panel; appearance alone cannot
prove whether they are raised ridges, refractive bead boundaries, or gaps.
The print reported in progress already combines the smooth Cool Plate and
ironing; its result was not available for this revision and cannot isolate
either effect. The plate can improve only its bed-contact face, not the
opposite top face or internal paths.

For the next controlled test, transparent filament slot 1 is set to 230 °C
for both normal and first layers, one 10 °C step above the former 220 °C and
inside the imported 190–240 °C range. This is a test candidate, not a proven
improvement or a claim that the unknown spool is rated for every temperature
in the imported range. The 20% part fan, 0% auxiliary fan, and calibrated
0.98 flow ratio remain unchanged so temperature is the only new filament
variable. A blanket +5% flow would make the ratio 1.029; it is not applied
because there is no spool-specific evidence of under-extrusion, over-extrusion
can build up on top surfaces, and the 8.64 mm apertures have only 0.14 mm
nominal diametral clearance to 8.5 mm cubes. There is no broad, isolated
no-slope region where higher flow can be safely confined without affecting
the fit-critical openings and thin webs.

The object explicitly overrides both shell layer count and shell thickness
at 2 layers / 0.20 mm; this prevents the imported process profile's larger
global minimum shell thickness from silently increasing the top skin beyond
the intended two layers. Top ironing affects the topmost planar skin, not the
internal aligned tracks or vertical aperture/ramp walls. The source material
identity is still the imported “PLA Transparent” profile; its brand and
drying state are unknown.

### User-selected smooth cool plate

The transparent-front plate uses OrcaSlicer's `Cool Plate` bed type and sets
transparent PLA slot 1 to `35 °C` for both the first and subsequent layers.
The user-selected UniTak3D Energy-Saving Kobra S1/Kobra X/Kobra 4 double-sided
plate listing (ASIN B0G48ZZTD8; [Amazon listing](https://www.amazon.com/dp/B0G48ZZTD8))
describes the glossy side as suitable for PLA at `30–50 °C`, with strong
adhesion and release after cooling. `35 °C` matches the existing Cool Plate
PLA profile and lies inside that manufacturer-stated interval; it has not been
independently tested on this plate/model.
Use the smooth/glossy face, not the textured/matte face, for this surface
finish goal; let the plate cool before removing the print and re-check bed
level/Z offset after installing the replacement sheet.

The global printer bed type remains `Textured PEI Plate` for the other plates.
Plate 3, which contains only the transparent front, has its own persisted
`bed_type=Cool Plate` override in that plate's metadata. Transparent PLA
slot 1 has Cool Plate first/normal temperatures of `35 °C`; other filament
slots and their bed-temperature values remain unchanged. The per-plate
override is necessary because setting the project-level bed type instead
would also change the global printer selector and other plates.

For the transparent front only, the first-layer wall/sparse speed is reduced
from the inherited `40 mm/s` to `20 mm/s` to encourage consistent contact on
the large, smooth-surface panel. This object has zero bottom-shell layers, so
the first-layer fill is sparse infill and follows this `initial_layer_speed`;
the separate `60 mm/s` solid-infill speed remains unchanged and is not used
for this object’s first-layer fill. First-layer flow remains `1.0`, line width
`0.50 mm`, and print sequence value `0`; the plate contains one object, so no
object-order adjustment is useful. Other objects retain their inherited
first-layer speeds. No extrusion-flow compensation or sequence change is
inferred from the seller's plate claims.

This remains a translucency test profile, not a claim of glass-like clarity.
PLA FFF can transmit light, but strand interfaces and the 2.5 mm optical path
scatter light; it should not be confused with clear acrylic or glass.
Two top skins plus ironing affect the top-facing plane, while the smooth plate
forms the bed-contact face. Neither can remove internal line structure.
The 90° aligned raster shortens the nominal straight run to 179 mm, about 25%
shorter than the long axis, but tracks remain visible by design. Raising
temperature may improve fusion, but it can also reduce dimensional accuracy;
the model geometry is unchanged and the printed 8.5 mm fit remains untested.

The controlled translucency study used only 1 mm coupons, so it does not
establish optical clarity for this 2.5 mm panel or centimeter-thick blocks.
The user's referenced videos may demonstrate bulk clarity, but their URLs,
material and settings were not supplied for independent verification:

- Vochozka et al. ran a controlled PLA study with 32 combinations and ten
  50 × 25 × 1 mm samples per combination on a Prusa MK4. They found significant
  effects from orientation, layer height, nozzle temperature, fan, extrusion
  multiplier and speed; their best combined condition was 0.30 mm, 240 °C,
  100% fan, 0.75 flow and 40 mm/s, with 23% more measured transmission than
  their default. The best setting is not a transferable recipe: it used a
  different PLA and printer, a 1 mm sample, and lower flow—not +5% flow.
  Their result supports testing temperature as one variable; it does not prove
  that 230 °C improves this unknown spool, 2.5 mm panel, fit or visible line
  texture. [Full paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11511128/)
  ([DOI](https://doi.org/10.3390/polym16202862)).
- Snapmaker's clear-filament guide recommends 100% aligned rectilinear infill,
  slow extrusion, hotter material-specific settings, and surface finishing;
  it distinguishes solid internal void control from smoothing the outer
  surface. These are general recommendations, not controlled evidence for this
  filament. QIDI's guide likewise recommends one-direction solid infill and
  slow paths, but is specifically about transparent PETG, not this PLA.
- The 3D Matterials video
  [“How To Get Clearer 3D Prints Using Translucent Materials”](https://www.youtube.com/watch?v=MKyC1qbvAyI)
  explicitly compares ironing at 05:08, but its available description does
  not report the outcome or establish a thick-PLA result. It is not treated as
  proof that ironing improves transparency.
- FormFutura's transparent-PLA guidance says printing toward a material's
  recommended upper temperature range can improve layer fusion and reduce
  visible boundaries, but also warns excessive temperature may reduce
  dimensional accuracy. It gives product-specific settings for its own
  Transparent PLA, not the unidentified “PLA Transparent” spool here.
  [Guide](https://b2b.formfutura.com/blog/blogs-1/transparent-pla-the-complete-guide-to-clear-light-diffusing-3d-printing-98).
- Prusa's extrusion-multiplier calibration guide says flow is filament- and
  spool-dependent; excess flow causes material buildup/scarring, while too
  little can leave gaps. It recommends adjusting in 1–2% calibration steps
  based on a test print, rather than applying a generic increase.
  [Guide](https://help.prusa3d.com/article/extrusion-multiplier-calibration_2257).
- A smooth plate transfers its finish only to the face in contact with it;
  it cannot smooth the opposite skin or buried extrusion paths. Ironing is
  likewise limited to the configured top surface. No new pattern or face flip
  is applied: the panel's fit-critical apertures, webs and ramp make an
  untested orientation or alternate infill pattern a potentially poor trade.
- The [OrcaSlicer top/bottom shell reference](https://www.orcaslicer.com/wiki/print_settings/strength/strength_settings_top_bottom_shells)
  documents that shell thickness can increase the layer count when it exceeds
  the thickness from the layer-count setting. The project therefore saves an
  explicit object-level 0.20 mm shell thickness as well as two shell layers.
- The user's referenced videos of centimeter-thick glass-like blocks are
  plausible demonstrations of bulk-solid clarity and are not dismissed as
  thin-wall examples. Their URLs/material/settings were not provided here, so
  their method cannot be independently attributed or reproduced from the
  current evidence.

Compare the reported smooth-Cool-Plate-and-ironing print before attributing
any surface change to either setting; record which face was against the plate
and which face shows the bands. The next 230 °C project
changes only the transparent filament's nozzle temperature relative to the
220 °C baseline. Use identical lighting and board/text readability checks,
and verify cube insertion before adopting it for the complete board. If flow
is ever retuned, use a sacrificial calibration print and small steps; do not
transfer the paper's 0.75 flow or 240 °C combined recipe to the fit-critical
part without spool-specific tests. No optical improvement or fit is claimed
from saved settings alone.
No successful slicer run exists for this 3MF, so saved settings are not
verified effective G-code values.

## Validation and limitations

The final exported meshes were re-imported and checked for expected envelope,
all 65 standard apertures at the rear layer, six arrow ledges, the small-window
web, socket/pin dimensions, blind floors, insertion clearance and preservation
of plate transforms. The 3MF ZIP archive passes CRC validation. The full
repository suite passes (85 tests), and catalog verification passes on the
PR tree (22 models / 39 outputs). Historical imported 3MFs preserve their
user-saved 0.20 mm object settings through narrowly scoped catalog exceptions;
the current generated deliverable uses its explicit 0.10 mm front override.
The generic
`mesh_tool.py validate` command combines all three 3MF plates into one
aggregate and reports an oversized footprint; the project inspector confirms
three separate plates, and the generator validates the exported meshes
individually. The final image comparison uses one global photo transform
without local warping; its approximately 1 mm registration uncertainty and
the remaining per-field pitch drift are disclosed in the
[photo-validation report](terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-validation.json).

The updated `--slice=0` OrcaSlicer CLI attempt exited `-18` before generating
G-code because the saved `retraction_distances_when_cut=0` is outside
`[10,18]`. This is the same pre-existing project-setting blocker seen in the
preceding integrated revision; it is not caused by the 230 °C test candidate.
Earlier attempts also reported a missing referenced process preset;
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
- [Small-window and arrow-ledge CAD close-up](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-local-reliefs.png)
- [Window 5-to-6 passage and retained-web close-up](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-window5-to6-web-closeup.png)
- [Before/after photo overlay](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-before-after.png)
- Closeups: [upper-left block](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-upper-left-5-closeup.png), [lower-left block](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-lower-left-zero-closeup.png), [upper-right block](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-upper-right-zero-closeup.png), [slider](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-slider-closeup.png), and [window 5-to-6 ramp](images/terraforming-mars-tableau-179mm-laminate-centered-blocks-photo-window5-to6-ramp-closeup.png)
