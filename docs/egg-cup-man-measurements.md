# Egg-Cup Man – Measurement Documentation

Source of body dimensions: `model-sources/egg-cup-man-original.stl` (original
build-plate file supplied by the user, containing the body, 2 arms, and 2 legs).
All body values were read numerically from the mesh, not estimated. The arms and
legs have since been freely remodeled parametrically (humanoid, with elbows and
knees) and are no longer derived from the original.

Generator: [`scripts/egg_cup_man_body.py`](../scripts/egg_cup_man_body.py)
Output: `models/egg-cup-man-body.stl` – **one** watertight seated figure
(body + arms + legs as a Boolean union).

## Pose

The egg-cup man **is seated**: the cup rests on the table on its rounded bottom,
both legs extend forward (−Y) with bent knees, and the feet point vertically
upward at the front. The arms hang down at the sides (±X) with bent elbows; the
forearms descend nearly vertically so the hands support the figure on the table.

## Body (Cup)

| Feature | Dimension (mm) | Source | Confidence |
| --- | ---: | --- | --- |
| Max. outer diameter | 46.48 (r = 23.24) | STL mesh, radial section | high |
| Total cup height | 22.07 | STL mesh, Z extent | high |
| Egg cavity: radial semi-axis `a` | 21.10 | Ellipsoid fit to inner contour | high |
| Egg cavity: vertical semi-axis `b` | 23.30 | Ellipsoid fit to inner contour | high |
| Egg cavity: ellipsoid center `z` | 21.60 | Ellipsoid fit to inner contour | high |
| Egg cavity: flat floor | z = 2.60 | STL mesh | high |
| Floor thickness beneath cavity | 2.60 | derived | high |
| Rim bead radius | 1.07 | Semicircle fit, center (r 22.17, z 21.00) | high |
| Wall thickness at rim | 2.14 | derived (23.24 − 21.10) | high |
| Min. wall thickness at belly | approx. 3.7 | derived from outer/inner contours | high |

The ellipsoid fit of the cavity deviates from the measured mesh by < 0.25 mm
over the entire height.

## Modified Cup Height and Cavity Shape (User Request)

Two intentional deviations from the original dimensions above. The table above
remains the measurements of the original; this section describes how the
generator modifies them.

| Feature | Original | New | Source |
| --- | ---: | ---: | --- |
| Total cup height `CUP_TOP_Z` | 22.07 | 26.00 | User specification |
| Rim bead start `RIM_Z` | 21.00 | 24.93 | derived (`CUP_TOP_Z − 1.07`) |
| Cavity: center `CAV_ZC` | 21.60 | 25.53 | derived (`RIM_Z + 0.60`) |
| Cavity: semi-axis `b` `CAV_B` | 23.30 | 23.917 | solved from `CAV_FLOOR_R` |
| Cavity: flat floor `CAV_FLOOR_R` | 12.21 (Ø 24.4) | 6.00 (Ø 12.0) | User specification |
| Cavity: floor height `CAV_FLOOR_Z` | 2.60 | 2.60 | unchanged |
| Arm lift `ARM_LIFT` | – | +3.93 | derived (`RIM_Z − 21.00`) |

* The additional 3.93 mm are **straight cup wall**. The rounded bottom
  (`BELLY_TOP_Z`, `FOOT_R`, max. wall overhang 46.5°) remains exactly as before.
* The cavity floor stays at z = 2.60, so the cavity becomes **deeper**. `CAV_B`
  is solved from `CAV_FLOOR_R` (`b = (CAV_ZC − CAV_FLOOR_Z) / sqrt(1 −
  (CAV_FLOOR_R/CAV_A)²)`), shrinking the flat floor to half its diameter and
  allowing the curvature to enclose a real egg more closely.
* The cavity rim remains at r ≈ 21.09, so wall thickness at the rim remains 2.14 mm.
* Arms: the root, collar, shoulder, and elbow move upward by `ARM_LIFT`, while
  the wrist (z 3.60) and palm (z 2.45) stay in place — the forearm therefore
  becomes **longer** by the same amount, and the hands continue to rest flat on
  the table (0.35 mm sink depth, unchanged).

## Modified Bottom (Spherical Rounding)

The original had a straight cylindrical wall with an R3 chamfer at the bottom.
The new design curves the outer wall **inward** below z = 14 mm, tangent to the
straight wall so there is no edge and **no outward bulge**:

    r(z) = 23.24 * sqrt(1 - ((14.00 - z) / 20.53)^2)

| Feature | Dimension (mm) | Source | Confidence |
| --- | ---: | --- | --- |
| Rounding start `BELLY_TOP_Z` | 14.00 | Design decision | – |
| Footprint radius `FOOT_R` | 17.00 (Ø 34.0) | Design decision, limited by overhang | – |
| Ellipse semi-axis `b` (calculated) | 20.53 | from `BELLY_TOP_Z` and `FOOT_R` | high |
| Max. wall overhang | 46.5° from vertical | calculated by generator | high |
| Max. outer diameter | unchanged 46.48 | Constraint | high |

`FOOT_R` was deliberately chosen so the steepest overhang remains below 50° and
the figure can be printed without supports. A smaller foot looks rounder but
quickly pushes the overhang above 60°.

## Arms (Humanoid, Parametric)

The arms are no longer **copies** from the original; they are generated as a
sphere sweep. The node chain is resampled beforehand with a Catmull-Rom spline
(both position **and** radius) so the joints appear as smooth bends rather than
sharp kinks. The first node in each chain is a **transition fillet**: a larger
sphere deep inside the body whose passage through the wall forms a flowing collar.

| Node | x | y | z | Radius | Description |
| --- | ---: | ---: | ---: | ---: | --- |
| 0 | 20.6 | 0.0 | 15.2 | 5.0 | Transition fillet (deep in the cup wall) |
| 1 | 23.6 | −0.2 | 14.8 | 4.4 | Collar – wall penetration |
| 2 | 26.6 | −1.0 | 13.2 | 3.8 | Shoulder |
| 3 | 30.4 | −3.0 | 9.8 | 3.4 | **Elbow** |
| 4 | 30.2 | −5.5 | 6.0 | 3.0 | Forearm (descends nearly vertically) |
| 5 | 29.6 | −7.0 | 3.6 | 2.8 | Wrist |
| 6 | 29.2 | −8.5 | 2.45 | 3.3 | Palm (`sx` 1.10, `sz` 0.85) – rests flat |

## Ground Contact (Heels and Palms)

The heels and palms should **rest on the surface**, not touch it at a single
point. They are therefore deliberately modeled slightly **below** the table
plane, then the limb body is cut at `z = 0` using `build_ground_cutter()`. This
turns the spherical caps into actual flat surfaces.

| Dimension | Value |
| --- | ---: |
| Palm sink depth | 0.35 mm |
| Heel sink depth | 0.48 mm |
| `GROUND_SINK` (warning threshold) | 0.60 mm |
| Total contact area (4 locations) | 37.3 mm² |

The cut is applied **only to the limbs**, before union with the body. The body
already has its own flat footprint at `z = 0`; cutting the finished figure would
create coplanar surfaces there. The contact areas lie at `r ≥ 30 mm` and do not
overlap the body's Ø34 footprint, so the cut is safe.

`limb_check()` reports the sink depth for each limb and warns if a limb does
**not reach** the table at all or sinks deeper than `GROUND_SINK` (which would
make the contact area unattractively large).


The collar protrudes 4.46 mm from the cup wall. The shoulder is deliberately
kept low (z ≤ 15.2) so the fillet (see below) does not raise the cup rim.

All values are design decisions (confidence: n/a, no fit dimensions). The left
side is created by mirroring `x`.

## Legs (Humanoid, Parametric)

| Node | x | y | z | Radius | sx | sy | sz | Description |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 7.2 | −10.2 | 6.2 | 6.00 | 1.00 | 1.00 | 1.00 | Transition fillet (deep in rounded bottom) |
| 1 | 8.4 | −12.4 | 6.0 | 5.80 | 1.00 | 1.00 | 1.00 | Inner collar |
| 2 | 9.6 | −15.0 | 5.9 | 5.45 | 1.00 | 1.00 | 1.00 | Outer collar – wall penetration |
| 3 | 10.6 | −18.4 | 5.9 | 5.00 | 1.00 | 1.00 | 1.00 | Hip |
| 4 | 11.0 | −24.0 | 6.6 | 4.80 | 1.00 | 1.00 | 1.00 | Thigh |
| 5 | 11.4 | −30.5 | 7.4 | 4.60 | 1.00 | 1.00 | 1.00 | **Knee** (bent) |
| 6 | 11.5 | −37.0 | 5.3 | 4.10 | 1.00 | 1.00 | 1.00 | Shin |
| 7 | 11.5 | −41.4 | 4.3 | 3.00 | 1.00 | 0.95 | 1.00 | **Ankle** – narrow joint |
| 8 | 11.5 | −44.4 | 3.05 | 3.40 | 1.05 | 1.00 | 1.00 | **Heel** – extends below table and is cut off |
| 9 | 11.5 | −45.6 | 8.6 | 3.40 | 1.15 | 0.80 | 0.95 | Ball of foot – wide but flatter |
| 10 | 11.5 | −45.9 | 11.4 | 2.60 | 1.18 | 0.60 | 0.75 | Toes – tapered wedge |

### Foot Shape

Reference: user photo of a foot in profile (lying leg, heel on the ground).
Derived from it and implemented as a design decision:

- The foot is no longer a **vertical cylinder**, but an L-shape:
  shin → narrow ankle → heel on the ground → foot rising forward/upward
  → toes.
- The cross-section is **no longer round** from the ankle onward. The three
  scale factors `sx, sy, sz` at each node deform the sweep sphere into an
  ellipsoid: wider across the foot (`sx` up to 1.18), thinner in the direction
  of travel (`sy` down to 0.60). This gives the taper of a real foot.
- Do not confuse this with “flattening the top”: a uniformly compressed toe
  ball looks as if something fell on it. The radius must **decrease** toward the
  tip (3.40 → 2.60) for the shape to read as toes.

The collar protrudes 4.88 mm from the body wall. The radius progression
5.00 → 5.45 → 5.80 → 6.00 grows toward the body **at an accelerating rate**;
this is what creates the concave, flowing transition rather than an attached sphere.

Spline parameters: `SPLINE_SAMPLES = 8` sample points per node interval,
`SPHERE_SUBDIV = 3`. Both radii **and** scale factors are clamped to the input
range; otherwise the spline overshoots at the sharp ankle bend.

All values are design decisions. `limb_check()` in the generator reports how
far the spline extends below the table plane (must be 0, or the cup floats),
how far it protrudes into the cavity, and how far the collar projects from the wall.

## Keeping the Egg Cavity Clear

The limbs must not protrude into the egg cavity. To ensure this, a revolved
solid for the cavity (`build_cavity()`) is created and subtracted **from the
limbs** before they are united with the body.

| Parameter | Value | Purpose |
| --- | ---: | --- |
| `CAVITY_MARGIN` | 0.20 mm | Cutter oversize – prevents coplanar surfaces |
| `CAVITY_CLEAR_H` | 5.00 mm | Cutter extension beyond the rim |

The cutter is deliberately applied **only** to the limbs. Subtracting it from
the finished body creates coplanar surfaces with the existing cavity surface
and produces a non-watertight mesh (`euler_number` 37, 70 degenerate facets –
verified).

Volume probe (`intersection(limbs, cavity)`):
uncut 333.6 mm³ → after subtraction **0.0 mm³**.

## Filleting the Limb Junctions (SDF Fillet)

A Boolean union **always** leaves a hard edge at the intersection curve. No
collar or radius progression can fix this; it requires a true concave fillet,
which can only be generated implicitly.

Therefore, `scripts/sdf_blend.py` builds a signed distance field:

1. The body and cavity are revolved solids, so their SDF depends only on `(r, z)`.
   `RevolveSDF` creates a 2D table with a 0.15 mm grid and uses bilinear
   interpolation (error ≈ 0.005 mm).
2. The ≈240 capsules in each limb are combined using a **hard** `np.minimum`.
   This is critical: using `smin` between capsules in the same limb would swell
   it along its entire length by up to `BLEND_RADIUS/4`.
3. `smin` is applied exactly **once**—between the body field and the completed
   limb field. The fillet is created only there.
4. The field is eroded by `BLEND_EROSION`. Away from the junctions, the blend
   solid therefore lies just **inside** the exact mesh and contributes nothing;
   at the junctions the fillet bulges out farther and creates the rounding.
5. The cavity is subtracted again after being **expanded by the same amount**,
   so the blend can never reduce the egg cavity.
6. The field is clipped at `z = 0`; otherwise the fillet extends 0.83 mm below
   the table plane and lifts the entire figure when lowered to z = 0.

Result: `figure = union(exact mesh, blend solid)`. The cup wall, rim rounding,
and egg cavity remain exactly as modeled, while the limb junctions receive
genuine fillets.

| Parameter | Value | Purpose |
| --- | ---: | --- |
| `BLEND_RADIUS` | 4.00 mm | Fillet reach |
| `BLEND_EROSION` | 0.08 mm | keeps the blend inside the mesh away from the fillets |
| `BLEND_PITCH` | 0.30 mm | Marching Cubes grid |

An exact match between a grid point and the isosurface creates a non-manifold
pinch point, which manifold3d rejects with *“Not all meshes are volumes!”*.
`blend_solid()` therefore repeats the Marching Cubes step with a slightly
shifted level until the surface forms a clean volume. The offsets are
deliberately **non-negative only**: a positive level adds erosion (always
safe), while a negative one would expand the blend into the egg cavity—a
material intrusion of 5.6 mm³ was verified.

Volume probe against the cavity: 2.2 mm³ for the exact test body, **0.0 mm³**
for a test body shrunk by 0.05 mm—surface tolerance of the Marching Cubes mesh
only, not actual intrusion.

Additional volume from the fillets: 18 438 → 18 758 mm³ (+320 mm³).
The shoulder fillet locally raises the cup rim by 0.16 mm
(total height 26.00 → 26.16 mm).

Dependency: `scikit-image` (Marching Cubes) in `requirements.txt`.

## Validation

`python scripts/mesh_tool.py validate models/egg-cup-man-body.stl`

Current status: watertight, manifold, `euler_number` 2, 1 component,
103 576 facets, build volume 67.9 × 71.6 × 26.2 mm (fits on 250 × 250 mm).

The mesh contains 4 sliver triangles with an area of ~3·10⁻¹³ mm² from the
Marching Cubes step. They are **topologically necessary**: removing them by
area reduces the mesh to `euler_number` −33 and makes it non-watertight
(verified). `mesh_tool validate` reports PASS, and slicers are unaffected by
them—so leave them in place.

## TODO After Test Print

- [ ] Test egg fit with a real chicken egg (Ø ~42 mm)
- [ ] Check stability of the Ø34 footprint; increase `FOOT_R` if needed
- [ ] Check the underside overhang in the print (46.5°)
- [ ] Knee bend: the underside floats approx. 2.7 mm above the table—check
      support requirements during printing
