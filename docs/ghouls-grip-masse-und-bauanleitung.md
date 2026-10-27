# The Ghoul's Grip – Dimensions and Assembly

For assembly at the workbench:
**[Step-by-step assembly instructions with exploded view, pin assignments, and intermediate checks](ghouls-grip-bauanleitung.md)**.
This document provides the complementary dimensional and design specification.

![Deployed](images/ghouls-grip-deployed.png)
![Retracted](images/ghouls-grip-retracted.png)

## Status

Parametric, fully manual functional prototype for the Anycubic Kobra S1. The power train uses only rigid printed parts: **rotating skull → pinion/racks → double scissors, lid gearing, and forearm gearing**. There are no cables, rubber bands, springs, pawl, or winding spool.

The five fingers and the thumb, opposed by 55°, are generated for printing in
the curved gripping pose; no tendons, wire, or filament are needed. The PIP,
DIP, and thumb IP joints are shaped as fully closed, solid knuckle transitions
without V-notches or relief slots, and the MCP collars sit flush against the
exposed metacarpal heads. Three flush blind holes (Ø3.4 × 3.6 mm, with
> 3.5 mm of closed material toward the back of the hand) are located in the
middle, ring, and little-finger metacarpals, so the palm has no protruding
bridges when the dish is not installed. The optional gold candy dish
(`candy-dish`, 55.1 × 67.5 × 39.8 mm including short underside plug pins
Ø3.0 × 3.2 mm, contoured to widen toward the fingers, thumb, and forearm) fits
into these sockets and is recessed farther into the hand. Its opening is
horizontal at mid-lift ($\theta = 48^\circ$) and tilts by at most
$\pm 30^\circ$ over the full 60° forearm travel (at least 10.981 ml static
retention volume with 2 mm of freeboard). The chest, lid, and all 35 non-hand
components remain exactly unchanged (`docs/ghouls-grip-printed-box-contract.json`).
Automatic tree supports remain enabled for the fingers and dish and must be
carefully removed after printing.

## Geometry Sources

| Subassembly | Source |
| --- | --- |
| Chest/lid | `scripts/gothic_chest.py` |
| Rigid mechanism | `scripts/mechanism.py` |
| Skull rotary knob | `scripts/skull.py` |
| Anatomical hand | `scripts/skeleton_hand.py` |
| Candy dish & support struts | `scripts/candy_hand.py` |
| View/print projects | `scripts/ghouls_grip.py` |
| Orca projects | `scripts/export_ghouls_grip_orca_projects.py` |
| Collision verification | `scripts/verify_ghouls_grip_mechanics.py`, `scripts/verify_ghouls_grip_candy.py` |

## Dimensional Specification

| Feature | Value |
| --- | ---: |
| Closed target size | 200 × 120 × 110 mm |
| Enclosure including decoration | 209.0 × 130.5 × 98.0 mm |
| Lid including local protective hood | 206.0 × 129.8 × 28.2 mm |
| Decorative outer wall/base | 2.0 mm |
| Functional datum at rails, bearings, and guides | 3.0 mm |
| Interior | 194 × 114 × 80 mm |
| Scissor arm | 72 mm pivot spacing, 12 × 4 mm |
| Scissor bore | 3.2 mm |
| Floor-bearing double cheeks (new design estimate) | Y=±40±8 mm; 4 mm thick; outer radius 4.6 mm |
| Open arm channel / arm axial clearance | 12 mm / 1.0 mm per outer side |
| Floor-bearing bore web / root | 3.0 mm radial / 9.2 × 4.0 mm per cheek |
| Scissor angle | 18° to 78° |
| Slider travel | 53.506 mm |
| Yoke lift | 48.177 mm |
| Lid opening | 108° |
| Lid rack, new Y pitch line | 42.432 mm (previously 57.286 mm) |
| Lid transfer axes Y / Z | 46.146 and 53.573 mm / 93.000 mm |
| Transfer gears | 2 additional parts, 6 teeth, 4 mm tooth width |
| Transfer journal / bearing bore | Ø2.8 / Ø3.2 mm; 0.4 mm diametral clearance |
| Skull rotation travel | 113.544° |
| Skull knob | 48.5 × 55.1 × 27.0 mm |
| Skull shaft | Ø8 mm press fit, 0.2 mm undersize in knob |
| Palm (with 3 flush dish sockets) | 67.8 × 96.4 × 25.2 mm |
| Candy dish (`candy-dish`, design estimate) | 55.1 × 67.5 × 39.8 mm (dish height 30.8 mm + underside legs/pins, contoured toward fingers, thumb, and forearm); base 1.6 mm, wall 1.5 mm |
| Dish locating pins / flush blind holes (design estimate) | 3 × Ø3.0 × 3.2 mm on dish underside / Ø3.4 × 3.6 mm flush in metacarpals (0.4 mm clearance, > 3.5 mm closed bone floor) |
| Fingertips, deployed | 241.2 mm above build surface |

The hand is derived from an anatomical CT dataset using `HAND_SCALE = 0.72`. The palm is larger than the original 50 × 45-mm concept to preserve recognizable carpal and metacarpal bones.

### Floor Bearing Repair

The previous central post, 6–6.8 mm wide, did not fit in the 2 mm gap between
the unchanged 4-mm arms at Y=±40±3 mm. It was replaced by two short bearing
cheeks fused directly to the floor for each scissor pair, not by trimming the
arms. X=0 mm, pivot Z=8 mm, scissor spacing, all arm holes, slider travel,
lift, lid drive, and the closed-wall correction remain unchanged. This change
adds no parts; the current configuration is shown in the BOM below.

**New values are design estimates/default clearances, not measurements:**
cheek centers ±8 mm relative to the scissor plane, 4 mm thick, head radius
4.6 mm. This creates an open 12-mm channel, 1 mm clearance to the outer arm
surface, a 3 mm radial web around Ø3.2 mm, and 36.8 mm² of root area per cheek.
The feet overlap the 2-mm floor by 0.6 mm; the top of the head at Z=12.6 mm
remains 0.4 mm below the rack underside at Z=13 mm. Load path: arm → unchanged
pin → both short cheeks → floor. The double-sided bearing avoids a thin
single-sided cantilever pin. This demonstrates load-bearing **geometry**, not
an allowable payload or PLA fatigue life.

The pins actually printed have a Ø2.7 mm shaft (from the previous generator),
are 26 mm long, and have a 1.6 mm head; they do not have a Ø3.0 mm shaft as
the part name suggests. They engage the full 4 mm thickness of both cheeks,
with 0.5 mm nominal diametral clearance. The test piece confirms at least
0.2 mm radial clearance. Both floor pins are inserted **from the center of the
chest outward**; the head for the positive-Y scissor pair is mirrored inward
in the exact view. Insertion through the closed outer wall is impossible.
A 24 mm axial insertion path, vertical arm insertion, and arm envelopes
expanded by an additional 0.4 mm were checked using mesh Booleans. Install the
floor pins first while the central mechanism area is clear. The existing
printed pins do not have the new locking feature: check for axial migration;
for sustained operation, use the existing M3 connection with suitable nuts if
available, and do not leave it loaded unattended.

All four **individual** arms were checked against the decorated chest at all
61 angles from 18–78°, including 48°: 0.000 mm³ to three decimal places; the
maximum numerical mesh residual per arm at the tangential floor contact was
0.000020464 mm³, well below the documented 0.001-mm³ Boolean tolerance. The
baseline intersection of up to 554.635 mm³ is therefore eliminated. Wall fill
remains 100%. PLA fit, hole/support cleanup, axial retention, loaded travel,
and wear require a physical dry/load test.

### Rear Mechanism Cutout Correction

The previous 14 × 12 × 24-mm cutout at X=-27, Y=58, Z=75 mm has been removed
entirely. It was needed because of the deep rear crossbar on the lid rack and
the downward-facing lid-crank key. The rack now sits 14.854 mm farther inward.
Two additional identical gears transmit motion with two direction reversals
and a 1:1 ratio to the lid sector at the unchanged hinge axis. The crank key
faces inward, above the chest rim, and engages a matching underside socket in
the lid. The bearing journals stay inside the widened, closed lid hood; the
chest was not enlarged.

The positions are derived from the existing radius
`LID_SECTOR_R = 7 mm / radians(108°)`: two center distances of
`2 * LID_SECTOR_R` each. Source/confidence: existing parameterized motion
contract, mathematically exact; no dimensions estimated from screenshots.
The Ø2.8/Ø3.2-mm journals retain the existing 0.4-mm running clearance;
tooth width 4 mm, rack tooth width 1.6 mm, tooth phase 15°, and the 2-mm hood
roof and X-sidewalls are new design values, checked by mesh/motion probes but
not yet confirmed by a PLA fit test. The bearings sit on short, 4 mm thick
cantilever supports connected from the inside to the unchanged rear wall at
Z=80–84 mm; bearing heads extend from Z=82 to 96 mm. This avoids additional
tall floor posts and preserves the existing lightweight chest-volume limit of
200,000 mm³. The asymmetric hood is 29 mm wide in X and centered at X=-30.5 mm:
it extends only left/inward, not into the central hinge block. The inner
service cavity is 25 mm wide; its cutter remains inside the hood surface. The
complete roof skin was checked with a volume probe. These are design decisions,
not new measured enclosure datums.

The complete conservative translation envelope of the follower rack does not
intersect the chest. 109 active lid positions additionally check gear/rack
clearance and assembly; the coupled overall comparison includes 61 scissor
positions, including 18°, 48°, and 78°. See
[mechanism verification](ghouls-grip-mechanik-verifikation.md), including the
now-passing individual-arm/floor-bearing proof and historical baseline
comparison.

## Binding Design Decisions

- The box is fully closed in the retracted position. The slider, scissors,
  lid linkage, and forearm do not protrude from the enclosure.
- The gray skull remains the intentionally external hand-operated drive. It
  is not a push button; it rotates through approximately 114°.
- There is no spring, rubber band, tendon, pawl, or return mechanism. Reset by
  turning the skull backward.
- Fit-critical geometry, bearings, gears, rails, insertion directions, and
  collision clearances remain parametric in Python.
- Organic decorative surfaces may be created in Blender but must not alter
  functional datums. The generator uses reproducible, cached height fields
  from `assets/gothic-chest-reliefs/`.
- Thick components are not unnecessarily solid-filled: the chest and lid use
  thin shells, ribs, and open supports; mechanism parts use frames, openings,
  spokes, and locally solid functional areas.
- “Support-free” may be claimed only after slicing with support generation
  enabled. No blanket support-free claim is made for the current output.

## Ornament and Organic Modeling

The final chest combines rounded, self-supporting bas-reliefs:

- Front: two skulls, snakes, tendrils, and scrolls
- Rear: rib cage and two wyverns with horns, teeth, claws, and wings
- Sides: skull with a continuous snake
- Lid: winged skull cartouche with snakes and scrolls
- Pilasters: 1.2 mm recessed flutes with domed ends

The raised reliefs are built as smoothed height fields and sheared by 45°.
This lets them grow from the wall without sharp undersides and does not increase
support paths in the measured control slice. The wall panels, only 2.0 mm thick,
are not deeply engraved; recessed details are placed only in material thick
enough to support them.

## Operating Principle

1. The gray skull sits on the main pinion's D-shaft and is secured with a
   1.75-mm filament cross-pin.
2. A 113.5° rotation moves the slider rack by 53.5 mm.
3. The slider opens two parallel scissor pairs from 18° to 78° and raises the
   platform (lift yoke) by 48.2 mm.
4. A cam track in the slider raises the lid follower by 7 mm over the first
   6 mm of slider travel, then holds it on a dwell. The follower rack turns the
   lid crank at the hinge through two transfer gears; at a 30° scissor angle,
   the lid reaches 108° and remains positively held open. The hand does not
   cross the lid.
5. A moving five-gear train with three idler gears transfers the rotation of a
   scissor arm to the forearm (-105° → -45°).
6. Turning backward drives the power train in reverse: the forearm folds in,
   the scissors lower, and the lid closes. No return spring is needed.

## Bill of Materials

The Orca print project contains **29 part types / 42 print objects** on four
plates. In addition, there are **four unprinted filament pins** (1.75-mm PLA
±0.02 mm cut from a spool remnant), represented as Ø1.75 cylinders in collision
and meshing checks.

| Part | Quantity | Approximate dimensions | Color |
| --- | ---: | --- | --- |
| Chest | 1 | 209.0 × 130.5 × 98.0 mm | Black |
| Lid | 1 | 206.0 × 129.8 × 28.2 mm | Black |
| Scissor arm | 4 | 84 × 12 × 4 mm | Natural white |
| Slider with box-frame crossbars, rack, reinforced cam track, and snap fingers | 1 | 125.5 × 118.8 × 20.8 mm | Natural white |
| Platform (lift yoke) | 1 | 83.5 × 92.6 × 48.5 mm | Natural white |
| Main drive pinion with D-shaft | 1 | 55.8 × 55.7 × 28 mm | Natural white |
| Lid follower with rack | 1 | 91 × 12.6 × 6 mm | Natural white |
| Lid crank (sector with driver) | 1 | 9.2 × 20.6 × 11 mm, Ø2.3 bore | Natural white |
| Crank spacer (axial retention on hinge axis) | 1 | Ø5 × 15.8 mm, Ø2.3 bore | Natural white |
| Lid transfer gear with shoulder and slotted snap-clip journal | 2 | Ø9.2 × 17.0 mm | Natural white |
| Scissor input gear | 1 | 25.8 × 25.8 × 11.5 mm | Natural white |
| Idler gear | 3 | Ø16.5 × 6 mm | Natural white |
| Forearm output gear with D-shaft | 1 | 25.8 × 75 × 25.8 mm | Natural white |
| Ø4 floor snap pin (clamping length 18.4) | 2 | Ø7.5 × 21.6 mm | Natural white |
| Ø4 slider snap pin (11.2) | 2 | Ø7.5 × 14.4 mm | Natural white |
| Ø4 center snap pin (8.4) | 2 | Ø7.5 × 11.6 mm | Natural white |
| Ø4 gear snap pin (16.4) | 1 | Ø7.5 × 19.6 mm | Natural white |
| Short Ø4 snap pin (6.8) | 3 | Ø7.5 × 10.0 mm | Natural white |
| Ø4 idler snap pin (11.4) | 3 | Ø7.5 × 14.6 mm | Natural white |
| Ø4 follower press pin (crush ribs, extended almost to chest wall) | 1 | Ø7.5 × 13.1 mm | Natural white |
| Forearm with D-hub | 1 | 25.8 × 18 × 50 mm | Bone beige |
| Palm (with 3 flush blind holes) | 1 | 67.8 × 96.4 × 25.2 mm | Bone beige |
| Five curved fingers (solid joints) | 1 each | 33–59 mm | Bone beige |
| Skull rotary knob | 1 | 48.5 × 55.1 × 27.0 mm | Gold (`#D4AF37`) |
| Candy dish (`candy-dish`, optional plug-in) | 1 | 48.0 × 55.0 × 39.0 mm | Gold (`#D4AF37`) |

**Unprinted parts (Ø1.75 mm ± 0.02 mm filament, cut to length):**

| Pin | Length | Bore (CAD) | Location |
| --- | ---: | --- | --- |
| Lid hinge | 198 mm | Ø1.9 chest / Ø1.98 lid / Ø2.3 crank & spacer (vertical) | Hinge axis, through all knuckles |
| Knob cross-pin | 14 mm | Ø2.3 | Knob and pinion D-shaft |
| Output-shaft retainer | 10 mm | Ø2.3 | D-shaft at platform bearing |
| Wrist | 16 mm | Ø2.3 | Forearm pin and palm |

*(The two lid transfer gears `lid-transfer-gear-01/02` retain themselves via
their integrated slotted snap clips behind the Ø3.2 bearing blocks and no
longer need 5-mm filament pieces.)*

The former separate tendon guide, rigid main lid rack, and Ø3 pins have been removed.

## Connectors and Positive-Fit Interfaces

| Connection | Connector | Assembly method |
| --- | --- | --- |
| Scissor arms, slider, platform, gears | 13 printed Ø4 snap pins in 6 clamping lengths in Ø4.6 bores | Slotted shaft with barb; insert from the head side until the barb engages behind the opposing surface (0.25 mm undercut); 14 printed pins total including the separate follower press pin |
| Follower in cam slot | Solid Ø4 press pin with crush ribs | Press from inside through the follower into the slot |
| Slider in rail | Two integrated snap fingers | Press vertically; fingers engage in the groove |
| Forearm in platform | Output-gear D-shaft + 10 mm filament pin | Place forearm between ears, insert shaft axially, secure from outside |
| Palm on forearm | 11.6-mm pin in Ø12 hub + 16 mm filament pin | Align cross-holes and insert pin crosswise |
| Fingers on palm | 4-mm MCP pins in 4.4-mm hubs (0.4 mm diametral clearance) | Slide from free pin end along the axis toward the palm (order: index, middle, ring, little finger, thumb); the bone head is exposed from 2.0 mm over a 7.0 mm length (Ø8.6 mm or Ø11.2 mm at the thumb) so the collar seats flush |
| Candy dish on palm | 3 asymmetrical Ø3.0-mm underside pins on dish in flush Ø3.4-mm blind holes in metacarpals (0.4 mm clearance) | Optionally insert from above along the dish normal after the fingers; without the dish, the skeletal hand has no protruding bridges |
| Lid on enclosure | 198 mm filament as hinge axis | Slide in from the end through all knuckles, crank, and spacer |
| Skull on main pinion | D-shaft + 14 mm filament pin | Fit knob and insert cross-pin |
| Transfer gears | Slotted clip journal Ø2.8 (barb Ø3.6) in Ø3.2 bearing block, shoulder on inside | Insert axially in -X until the slotted barb engages behind the bearing block on the outside (no 5-mm filament pin needed) |

All plug clearances, latch strains, insertion paths, and gear backlash are
verified against print inaccuracy (±0.1–0.2 mm) in
[`ghouls-grip-montage-audit.md`](ghouls-grip-montage-audit.md).

## Assembly

### Exploded View

[![Exploded view with eight numbered subassemblies and German assembly annotations](images/ghouls-grip-explosionszeichnung.png)](images/ghouls-grip-explosionszeichnung.png)

The [full-resolution drawing (3200 × 2600 pixels)](images/ghouls-grip-explosionszeichnung.png)
shows all **42 printed bodies** from `models/ghouls-grip-view.3mf` in the
`deployed` state, arranged in eight numbered subassemblies. The numbers refer
to the assembly steps below; they are not additional part identifiers. The
palm, five fingers, forearm, and optional dish are shown separately; snap pins
and drive gears are assigned to their respective subassemblies. The four cut
filament pins are not shown; their lengths and insertion locations are listed
in the tables above and in the assembly steps.

**Illustration only; no geometry changes:** The original meshes are moved only
for the illustration; orientation, shape, STL, and 3MF files remain unchanged.
Dashed arrows indicate exploded-view axes, **not verified assembly paths**.
The platform and lid in particular are not simply lowered straight down: the
required offsets and engagement directions remain as described in steps 9 and
11–12. Do not take measurements from the illustration; it is not to scale and
does not replace a fit/collision check.

Reproducible image source: `scripts/render_ghouls_grip_exploded.py`.
The script reads the existing view project, renders its meshes with Blender,
and adds the German labels with Pillow. Blender is searched for on PATH or in
the default Windows installation directory; another path can be specified with
`--blender`. No new print files are exported.

```powershell
.\.venv\Scripts\python.exe scripts\render_ghouls_grip_exploded.py
```

Render evidence: Blender **5.2.2 LTS**, PNG rendered successfully, all 42
bodies within camera bounds, image visually checked. SHA-256 of source 3MF:
`810d8e525bf2038dc930ba21cbacf278700f29d1ddbc420faad032fe8944f012`.
The script also checks the SHA-256 values of all three Ghoul's-Grip model files
before and after rendering. Projection data and intermediate renders are stored
only under `build/ghouls-grip-exploded/`.

### Assembly Steps

1. Place the chest on the table with the opening upward.
2. Press the slider vertically onto the rail until both snap fingers engage in
   the groove. It must move freely between both end positions.
3. Slide the drive pinion axially through the front-wall hole from inside; it
   meshes with the slider rack.
4. Fit the skull knob onto the D-shaft in the closed position (face vertical)
   and secure it crosswise with a 14 mm filament pin.
5. Lower the lid follower into the guide channel; press the follower pin from
   inside through the follower into the cam slot.
6. Slide both lid transfer gears axially in -X into the bearing blocks until
   the shoulder seats inside and the slotted snap clip engages behind the
   bearing block on the outside (no filament pin required).
7. Install the scissor arms in each layer; snap in the floor, slider, and
   center pins with their heads facing inward.
8. Install the scissor input gear **before** the platform: slide it onto the
   upper arm eye from +Y, press the locating pin into the arm hole, then move it
   upward into position.
9. Preassemble the platform assembly outside the chest: forearm between the
   ears, pass the output-gear D-shaft through, insert the 10 mm filament
   retainer pin, and install the three idler gears with their pins. Lower the
   assembly vertically, offset 3 mm away from the scissor input gear (toward
   idler gear 0); then slide it into engagement along the axis connection. The
   axis connection is at 64° to vertical, so lowering straight down would make
   tooth tips collide. Snap the gear, fixed, and slot pins into the top joints.
10. Slide the palm onto the forearm pin (rolled -75°) and insert a 16 mm
    filament cross-pin. Slide each curved finger onto its matching socket from
    the free end of the MCP pin along its axis toward the palm (order: index,
    middle, ring, little finger, and finally the opposed thumb). The proximal
    finger axes align with the angled pins; the MCP collars begin at 2.4 mm and
    seat flush against the metacarpal heads exposed from 2.0 mm onward (4.0 mm
    root overlap of the pin). Optionally insert the gold candy dish
    (`candy-dish`) along its opening normal, using its three Ø3.0-mm underside
    pins in the flush Ø3.4-mm blind holes in the metacarpals. Finger and dish
    fits are removable (gravity/plug-in fit, not positively locked) and have
    not yet been confirmed by a physical load test.
11. Preassemble the lid outside the chest: turn the lid upside down, insert
    the crank from below and slide it 5.6 mm in +X into the drive pocket; place
    the crank spacer from below into the service channel between the crank and
    lid eye. (The parts are separate because their combined length of
    11.0 + 15.8 = 26.8 mm exceeds the 25.0-mm hood opening, and the crank must
    first be slid 5.6 mm sideways into the pocket; the channel is closed once
    the lid is installed. The hinge holes in both upright-printed parts have a
    Ø2.30 mm CAD diameter to compensate for vertical FDM hole shrinkage.)
12. Hold the lid assembly about 108° open, offset it 3 mm to the rear (+Y), and
    lower it vertically; then slide it forward to engage with the idler gear
    until the hinge eyes align. Slide the 198-mm hinge filament in from the end
    through the chest, lid, crank, and spacer. The spacer holds the crank
    axially engaged (clearance +0.2/−0.1 mm).
13. Test slowly without candy: turn the skull → lid opens early → scissors
    lift → forearm unfolds. Then turn it exactly backward. For candy, use only
    packaged goods or a food-safe insert in the dish (unprotected FDM PLA is
    not certified as food-safe), and do not fill above the free height of the
    closed chest.

Disassemble in reverse order: remove the candy dish, release snap pins by
squeezing the slotted halves together from the barb side, and pull out the
filament pins.
## Print Projects

- `models/ghouls-grip-view.3mf` – assembled views on three plates:
  fully deployed (78°), intermediate state (48°), and retracted (18°).
- `models/ghouls-grip-print.3mf` – one Orca project for all 42 print objects,
  with four filament/color assignments on four plates grouped by color and
  subassembly.
- `models/ghouls-grip-preview.stl` – Canvas preview.

In the closed state, the complete internal lid mechanism sits beneath a black
protective hood integrated with the lid. The assembly channel opens only toward
the inside of the box; a continuous 2.0-mm roof skin covers it from above. The
lid crank and yoke were also checked as individual collision pairs through the
full travel and intersect neither the lid nor the chest.

The preserved user project uses PLA, Anycubic Kobra S1 0.4,
0.20 mm layer height, and four embedded colors. Its actual settings are High
Temp Plate, aligned seam, no ironing, and global support off (object overrides
enable support). These settings were not reset; profile compliance remains
`not-verified`. The exact slice results are in
[`ghouls-grip-druckvalidierung.md`](ghouls-grip-druckvalidierung.md).

### Generator Defaults (Not the Preserved User Settings)

These options apply to newly created multicolor projects and are verified by
`tests/test_ghouls_grip_orca_settings.py`:

| Option | Stored value |
| --- | --- |
| Seam position | Random (`seam_position=random`) |
| Ironing | All top surfaces (`ironing_type=top`) |
| Generate supports | On (`enable_support=1`) |
| Default supports | automatic, build-plate only |
| Layer / nozzle | 0.20 mm / 0.4 mm |
| Plate | Textured PEI Plate |
| XY hole compensation | +0.10 mm |
| XY contour compensation | 0.00 mm |
| Elephant foot compensation | 0.15 mm |
| Prime tower | off, since each print plate is assigned to only one color/spool |

Black, bone, and gray use automatic tree supports. The natural-white mechanism
plates use `normal(auto)` with `snug`, which gives more reproducible support for
racks, frame openings, and connectors. Object overrides control walls, infill,
speed, and acceleration; no override disables supports.

## Safety and Remaining Risks

- Motion is directly hand-operated, not spring-driven. Still, keep hands clear of the scissors, gears, and lid hinge.
- The larger skull provides less mechanical advantage than the discarded long lever. First dry-run the mechanism without the hand and lid; remove burrs and do not force rotation.
- Before printing the complete assembly, print one arm, one small/large pin, and one gear as fit samples.
- Printed pins and 0.8-mm PLA flexures are wear parts.
- This design is not a tested children's toy.
- The separate existing `scissors_chest` collision at the original floor bearings remains unchanged. The wall correction therefore does not certify the complete mechanism for a functional print.

## Hand Geometry License

The hand is based on **“Wrist Bones Full Hand – Human Skeleton”**, NIH 3D Print Exchange, model `3DPX-016815`, uploaded by My Segmenter, **CC BY 4.0**. Only the derived dataset `model-sources/ghouls-grip/reference/hand_bones.npz` is stored in the repository. Fit-critical interfaces, flexures, bearings, gears, and enclosure are independent parametric designs.
