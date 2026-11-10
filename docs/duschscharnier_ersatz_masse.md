# Shower Hinge Replacement - Dimension Documentation

This first version is a reinforced fit test for the existing gray bearing
insert. The values come from the photos using calipers or the 5-mm grid and are
set as parameters in the generator `scripts/duschscharnier_ersatz.py` for the
final ASA version.

| Feature | Dimension (mm) | Source | Status |
| --- | ---: | --- | --- |
| Overall length | 82.53 | designed | 82.33 + 0.2 due to the thicker teardrop outer wall |
| Bearing head width | 38.4 | designed | Original 38.0 + 2 x 0.2 wall increase outward; unchanged on the inside |
| Bearing head length | 43 | user measurement | measured |
| Overall thickness | 12.5 | user measurement | measured (without guide rails) |
| Mounting arm width | 20 | user measurement | measured |
| Mounting arm length | 45 | user measurement 16.08. | 43 + 2.0; the 2 mm is between the teardrop and first hole (original 42.83 vs. print 40.87) |
| Mounting hole diameter | 4 (model 4.4) | user measurement | target dimension 4.0; +0.4 print compensation in the generator so the printed hole measures 4 mm |
| Mounting hole countersink | ⌀8.5 x 5 deep | user measurement | measured |
| Mounting hole centers | 12.4 / 31.7 from the outer edge of the mounting arm toward the bearing head | user measurement | measured |
| Gray insert, width | 33.9 | user measurement | measured |
| Gray insert, length | 38,3 | user measurement | measured |
| Gray insert, thickness | 7.85 | user measurement | measured |
| Insert seating clearance | 0.20 | FDM-Sliding-Fit | deliberately specified; fit confirmed, pocket dimensions frozen as of 16.08. |
| Bearing pocket and arm floor | 2.0 | user measurement | measured; continuous through the head and arm |
| Lower outer edge radius | 0.8 | cast reference | radius around the closed outer surface |
| Cross-ribs and cast pads, height above floor | 2.4 | user measurement | 2.4 raised above the 2.0 floor, top at 4.4 from the outer surface |
| Cross-rib engagement into wall | 1.6 | reinforcement 16.08. | all four rib ends extend 1.6 mm into the wall instead of stopping short |
| Shell wall thickness (teardrop) | 2.05 | reinforcement 16.08. | 1.85 + 0.2, exclusively outward; pocket contour unchanged |
| Arm wall thickness | 2.0 | user measurement | measured |
| Outer fillet at arm-to-teardrop transition | 8.0 | reinforcement 16.08. | cove instead of sharp inside corner at the waist (x = +-10, y = -0.37) |
| Insert guide, projection / length / width | 2.0 / 20.0 / 8.1 | side view with calipers | derived; protrudes at the top |
| Guide rails in arm, overhang / projection / length | 5.3 / 2.0 / 22.5 | user measurement + photos 202910/201653 (top view) and 202902 (side view) | pair of longitudinal rails on both inner arm walls; they start at the chamber floor and extend 5.3 mm above the wall edge (top at z = 17.8) |
| Guide slot between rails | 12.0 | top views 201653/202910, scaled to arm width 20 | derived |
| Guide rail position in Y | 7.0 .. 29.5 | comparison photo 104653 (print on original) | arm-side end unchanged, extended 2.5 toward the teardrop |
| Teardrop head radius / tip radius, outer | 19.2 / 11.05 | derived from width 38 and length 43, + 0.2 wall increase | set |
| Teardrop head radius / tip radius, pocket | 17.15 / 9.0 | insert dimensions + seating clearance | unchanged, fit confirmed |
| Teardrop flank radius, outer / pocket | 34.2 / 32.15 | contour match to photo 201713 | replaces the straight tangents of the previous hull; arc centers for outer contour and pocket are identical |
| Center opening in insert | 17.9 | user measurement | not part of the replacement body |

Image index: `model-sources/archiv/duschscharnier_ersatz-referenzfotos-index.png`
(numbered contact sheet of all reference photos) and
`model-sources/archiv/duschscharnier_ersatz-analyse-index.png` (caliper
overlays, STL renders, video stills). The raw images were removed after the
model was completed; the tile-to-file mapping is in
`model-sources/archiv/README.md`. The source references above give the timestamp
portion of the original filename, e.g. `202902` = tile 16.

## Reinforcement

The original break is in the narrow connection between the arm and bearing head.
The replacement reproduces the cast construction shown in the reference video:
a circular bearing head with a teardrop-shaped insert pocket (head and tip radii
connected by tangent flank arcs, with no straight sections), cross-ribs and four
cast pads in the shell floor (raised 2.4 mm above the floor, with their tops
4.4 mm from the outer surface), a chamber arm with a continuous center wall,
fused screw bosses with conical countersinks (transitioning without a step into
the 4-mm hole), and two guide rails on the inner arm walls, extending from the
chamber floor to 5.3 mm above the wall edge. The solid rails and continuous
floor plate make the break area much stiffer than the thin original web.

Further reinforced as of 16.08., after the waist was identified as the next
weak point:

- The teardrop outer wall is 0.2 mm thicker (1.85 -> 2.05). Since all three arc
  centers are shared with the pocket, the wall grows exclusively outward; the
  pocket contour remains mathematically and volumetrically identical, so the
  gray insert still fits unchanged.
- A sharp re-entrant corner was present at the arm-to-teardrop transition, where
  the straight arm flank intersects the head circle. It has been replaced by an
  R 8 cove: this removes the stress concentration and increases the waist
  cross-section by about 9.5 mm2.
- The cross-ribs in the shell floor ended freely before the wall (0.5 mm gap at
  the arm end of the longitudinal rib, 0.2 mm on each side of the transverse
  rib), so they could not transfer load into the wall. Now all four rib ends
  extend 1.6 mm into the wall. The ribs still support the insert only from
  below; the pocket contour remains unchanged.

## Printing Instructions

1. First print a PLA fit test and insert the gray insert.
2. Use ASA for installation: at least 5 perimeters, 50-60 % gyroid infill,
   0.2 mm layer height, and print with the bearing recess facing up.
3. Hang the door only after a successful static hand check. An FDM part is not a
   substitute for a safety-certified fitting; discontinue use if cracks or
   looseness appear.