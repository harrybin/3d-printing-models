# Terraforming Mars Tableau: 179 mm, selected coupon fit

The only delivered/catalogued variant is
`models/terraforming-mars-tableau-179mm-loch1-zapfen3.3mf`.
Its necessary reproduction inputs are archived unchanged under
`model-sources/terraforming-mars-tableau/`, not published as separate variants:

| Input | Purpose | SHA-256 |
| --- | --- | --- |
| `terraforming-mars-tableau-179mm.3mf` | Prior uniform 179/172 scaling, three plates | `fb017fdd8bc1ef03faac8a431af10b39c6d1fc842391db4fb9cf50e121e43c3d` |
| `terraforming-mars-tableau-fit-samples.3mf` | Physical coupon diameter evidence | `f2cd5082b5705df9b6b88963f716be752641be23a481abd9d7f663cfed2d23ef` |

These are user-provided assets. The original model author and license were
not established; the repository MIT license does not license their contents.
The prior scaled project derives from the user-saved baseline with SHA-256
`179e1cb51043f6b4dd99c27d6f166f95c03a223e313050b709b1c9c1aa0cfc84`.
The original and previous variant remain unchanged in their originating session;
they are not additional deliverables in this revision.

The prior scale is `179/172 = 1.0406976744`. Front thickness is 3.122 mm,
rear thickness is 4.579 mm. Each panel stays centered on its original
250 x 250 mm plate with its bottom at Z=0. The white front (plate 1),
dark rear (plate 2), and transparent front (plate 3) retain their material
mappings, print orientations, overrides and embedded printer settings, including
the transparent front's saved 0.2 mm object layer-height override. The
repository CI explicitly permits this exact catalogued object setting; all
other per-object layer-height overrides remain limited to 0.16 mm.

## Physical fit selection: one-notch hole / three-notch pin

The user reported that the one-notch socket coupon on the three-notch pin
coupon had slight retention, while the other tested combinations were too loose,
and explicitly selected that pairing. The exported coupon meshes and their
generator establish **socket diameter 3.000 mm and pin shaft diameter 2.600 mm**.
All three front coupon variants actually have the same 3.000 mm CAD bore;
their notches identify the paired pin samples, not three different hole sizes.
Consequently, the reported differences between the front coupons cannot be
attributed to a designed diameter difference. Print variation remains a fit risk.
The selected diameters are nominal mesh dimensions, not caliper measurements
of the physical coupons.

The new derived project is
[`terraforming-mars-tableau-179mm-loch1-zapfen3.3mf`](../models/terraforming-mars-tableau-179mm-loch1-zapfen3.3mf).
It keeps the 179/172 panel scale but applies the tested **absolute** diameters,
without scaling those fit dimensions again to 3.122/2.706 mm. Both front copies
have eight adjusted blind sockets, and the rear has eight adjusted pins.
The left-middle source pin was larger than the other seven (2.8 mm before
uniform scaling, versus 2.6 mm); all eight now have the selected 2.6 mm shaft.

| Datum | Result | Origin / confidence |
| --- | --- | --- |
| Panel envelope | 240.401162 x 179.000000 mm | Prior exported project; verified unchanged |
| Socket diameter, both fronts | 3.000 mm | One-notch coupon mesh; verified within 0.000020 mm |
| Pin shaft diameter, all eight | 2.600 mm | Three-notch coupon mesh; verified within 0.000020 mm |
| Diametral clearance | 0.400 mm nominal | Selected coupon dimensions; actual FDM clearance unverified |
| Socket depth | 2.601744 mm | Original 2.5 mm x 179/172; unchanged |
| Blind floor thickness | 0.520349 mm | Original 0.5 mm x 179/172; unchanged |
| Pin projection | 2.497674 mm | Original 2.4 mm x 179/172; unchanged |
| Axial tip-to-floor clearance | 0.104070 mm | Prior project clearance; unchanged, positive geometric reserve only |
| Socket/pin center datums | X = 0 or +/-117.182558 mm; Y = 0 or +/-86.481977 mm | Recovered from original mesh rings; eight original positions, unchanged |

Only the radial coordinates of the existing socket walls and projecting pins
are transformed by the reproducible
[`fit_terraforming_mars_tableau.py`](../scripts/fit_terraforming_mars_tableau.py).
This preserves the original mesh connectivity, pin tip profile in Z, axial
dimensions, blind floors, panel outlines and all non-fitting vertices. It does
not transplant the coupon's chamfer/fillet or shorten the original pins to the
coupon's 2.1 mm projection. This is a diameter-fit transfer, not proof that the
full-size parts reproduce the coupons' printed holding force.

All sixteen exported sockets and eight exported pins were measured after
archive re-import. All sixteen blind floors and bore cavities pass solid-volume
probes; all meshes remain watertight, consistently wound and connected without
degenerate faces. A nine-position full-panel axial insertion sweep has no
unintended intersection above the 0.001 mm3 numerical tolerance. Plate/object/
component/assembly transforms, material mappings, original plate assignments,
all project/object settings and all other archive members are byte-identical.
Both front copies remain identical. See the
[machine-readable checks and SHA-256](terraforming-mars-tableau-179mm-fit-validation.json)
and [exact exported-project preview](images/terraforming-mars-tableau-179mm-loch1-zapfen3-preview.png).

The three-plate imported-project naming is intentionally retained rather than
creating additional assembled/print projects or STL counterparts. The archived coupon and prior 179 mm inputs are preserved byte-for-byte.
The source author/license remain unspecified; no new third-party asset was used.

### Slicing and remaining fit risk

An OrcaSlicer CLI slice was attempted with the saved Kobra S1 settings, without
normalizing or overwriting them. It failed with exit `-18`:
`retraction_distances_when_cut: 0 not in range [10.000000,18.000000]`.
No G-code or support screenshots were generated, and no new print time,
material estimate or successful slicer validation is claimed. In particular,
the source's disabled supports (`enable_support=0`) and transparent front's
0.2 mm object layer-height override remain saved exceptions, not newly compliant
repository defaults. The CI exception applies only to that named object and
does not repair the incompatible retraction preset or establish a successful slice.

**The complete tableau has not been physically fit-tested.** The preserved
0.104 mm axial reserve is smaller than the saved 0.2 mm object layer height;
it proves CAD separation only, not immunity to layer/first-layer inaccuracies.
Do not infer physical retention or full print readiness from the mesh checks.
Correcting the source preset or altering pin heights is outside this
diameter-only revision.

Reproduce the geometry, targeted verification and exact output render:

```powershell
.\.venv\Scripts\python.exe scripts\fit_terraforming_mars_tableau.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_terraforming_mars_tableau_fit.py
.\.venv\Scripts\python.exe scripts\render_terraforming_mars_tableau_fit.py
.\.venv\Scripts\python.exe -m printforge verify-catalog .
```
