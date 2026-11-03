# Ghoul’s Grip – Assembly Instructions

These instructions guide you through assembling the **42 printed parts**
in `models/ghouls-grip-print.3mf`. The gold candy dish is optional; without it,
41 printed parts are assembled. Four additional pieces of Ø1.75 mm (±0.02 mm)
PLA filament are required for the hinge and cross-pins.

**Status:** digitally verified functional prototype; not a physically tested kit.
Fit, axial retention, and sustained operation under load must be tested on the
actual print. No springs, rubber bands, cables, or adhesive are required for
the moving connections.

## 1. Overview and Orientation

[![Exploded view with numbered subassemblies](images/ghouls-grip-explosionszeichnung.png)](images/ghouls-grip-explosionszeichnung.png)

[Open the full-resolution exploded view](images/ghouls-grip-explosionszeichnung.png).
Image numbers 1–8 identify **subassemblies**, not the work steps below. The
dashed arrows show presentation axes, not insertion paths. In particular, the
lift yoke and lid require the offsets described below. Filament pins are not
shown in the image.

Place the chest with its opening facing up and the skull bore toward you.
“Front” is the knob side (−Y); “rear” is the hinge side (+Y). Viewed from the
front, +X points right and −X points left; +Z points upward. The hinge runs
across the chest from left to right. These directions remain chest-relative
even when the lid is turned over.

### How to Read the Step Illustrations

Each section, from parts preparation through the dry run, has its own model
illustrations. **A** shows the new parts separately; **B** shows them in their
installed positions. For the dry run, A and B instead show the retracted and
deployed states. The turquoise numbers refer to the legend directly below each
image, not to the subassembly numbers in the exploded view.

Parts already assigned to the assembly are gray; new parts retain their material
colors. The chest is hidden in the marked detail views so the bearings, gear
trains, and pins remain visible. Spacing in the illustrations is enlarged for
clarity: **insertion directions and actual offsets are given in the text**.
Filament pins are not shown. Click any image to open it at full resolution.

[Overview of all twelve step illustrations](images/ghouls-grip-montage-bildfolge.png).

## 2. Prepare the Parts and Work Area

[![Parts preparation: separate original components and target assembly](images/ghouls-grip-montage-02.png)](images/ghouls-grip-montage-02.png)

Lay out the parts on a soft surface. Useful tools include side cutters, small
pliers, tweezers, calipers, and fine deburring tools. Cut filament and remove
support material away from fingers and eyes; keep hands clear of the scissors,
gears, and hinges during testing.

| Subassembly in image | Parts to prepare |
| --- | --- |
| 1 – Enclosure | 1 black chest |
| 2 – Slider | 1 natural-white slider (closed box frame with crossbars, rack, and reinforced cam track) |
| 3 – Main drive | 1 pinion with D-shaft, 1 gold skull knob |
| 4 – Lid drive | 1 follower rack, 2 transfer gears with slotted clip journals, 1 follower press pin |
| 5 – Scissors | 4 arms, 1 scissor input gear; matching pivot pins |
| 6 – Lift yoke | 1 platform, 3 idler gears, 1 output gear with D-shaft; matching pivot pins |
| 7 – Arm and hand | 1 forearm, 1 palm, 5 different fingers; optionally 1 gold dish |
| 8 – Lid | 1 black lid, 1 lid crank, 1 crank spacer |

Remove supports and loose burrs, especially from tooth gaps, slider guides,
snap-pin slots, D-hubs, and cross-holes. Do not cut notches into bone transitions:
the finger joints are intentionally **solid and immobile**. Do not routinely
ream or sand mating surfaces. If a connection binds, first check for support
residue, orientation, and the correct pin variant.

### Cut the Filament Pins

Use straight Ø1.75 mm (±0.02 mm) PLA filament and deburr the cut ends. All
cross-holes for filament pins in the mechanism, knob, forearm, and hand parts
are designed in CAD at **Ø 2.30 mm (`r = 1.15 mm`)** to compensate for inward
hole shrinkage with 5 walls and 100% infill. The two small lid transfer gears
no longer need filament pins because their bearing journals have slotted snap
clips (like the pivot pins).

| Quantity | Length each | Use |
| ---: | ---: | --- |
| 1 | 198 mm | Lid hinge, through chest, lid, crank, and spacer |
| 1 | 14 mm | Cross-secure knob and main drive shaft (Ø2.30 mm hole) |
| 1 | 10 mm | Cross-secure forearm output shaft on the outside (Ø2.30 mm hole) |
| 1 | 16 mm | Cross-secure wrist (Ø2.30 mm hole) |

### Sort the Printed Pins (4 Visually Distinct Length Groups + 1 Press Pin)

There are **14 printed pins** in total: **13 slotted snap pins (cotter pins)**
with locking barbs and **1 solid, unslotted press pin** (`pivot-pin-follower`).
When you lay the **13 slotted pins** side by side, you can distinguish **four
length groups** by eye (**3 very short**, **2 short**, **5 long**, **3 very long**):

| Visual group on the table | Quantity | Overall length (clamping length) | Project identifier | Where does this pin go? |
| --- | ---: | --- | --- | --- |
| **1. Three very short** (slotted) | **3×** | **10.0 mm** (6.8 mm) | `pivot-pin-short` (`fixed-0`, `slot-0`, `slot-1`) | **Section 8 (lift yoke in scissors):** the **3 upper joints without gears**—1× upper front fixed point (`−Y`) and 2× upper front/rear slot points (`−Y` and `+Y`) |
| **2. Two short** (slotted) | **2×** | **11.6 mm** (8.4 mm) | `pivot-pin-centre` (`centre-0`, `centre-1`) | **Section 5 (scissor layers):** the **2 center scissor crossings** (one each at the front and rear of the X) |
| **3. Five long** (slotted, visually almost the same length) | **5×** | **2× 14.4 mm** (11.2 mm)<br>**3× 14.6 mm** (11.4 mm) | `pivot-pin-slider` (2×)<br>`pivot-pin-idler` (3×) | **Section 5:** **2× (14.4 mm)** moving at the bottom on the **slider** (front/rear)<br>**Section 7:** **3× (14.6 mm)** for the **3 idler gears** on the lift yoke *(0.2 mm difference is within the axial clearance)* |
| **4. Three very long** (slotted) | **3×** | **2× 21.6 mm** (18.4 mm)<br>**1× 19.6 mm** (16.4 mm) | `pivot-pin-floor` (2×)<br>`pivot-pin-gear` / `fixed-1` (1×) | **Section 5:** the **2 longest (21.6 mm)** fixed at the bottom in the chest **floor bearings** (from inside outward)<br>**Section 8:** the **1 slightly shorter pin (19.6 mm)** at the upper rear (`+Y`) through the **lift yoke, scissors, and input gear** |
| **Special pin without slot** (solid, with crush ribs) | **1×** | **13.1 mm** (press fit, shaft 11.5 mm) | `pivot-pin-follower` | **Section 4 (lid follower):** passes through the follower rack and the slider's reinforced cam track almost to the chest's inner wall (`y = 57.5 mm`, 0.5 mm from the wall at `y = 58.0 mm`; not a pivot pin!) |

Always insert snap pins from the head side through the aligned holes until the
slotted barb engages behind the opposing surface. Do not hammer them in. The
head must not clamp the joint.

## 3. Assemble the Slider and Main Drive

**Image groups 1–3 · original assembly steps 1–4**

[![Step 3a: slider before installation and on the floor guides](images/ghouls-grip-montage-03a.png)](images/ghouls-grip-montage-03a.png)

Place the slider vertically onto the floor guides with a slight rightward offset
(`+X`, about 5.5 mm in front of the chest's rear guide rib). Press only on
sturdy frame areas until both integrated snap fingers engage in the groove, then
slide it left (`−X`) into its starting position. The two rear crossbars make
the slider a closed box frame that cannot bow under load. Carefully move it
through its travel by hand: it should remain guided and slide without binding.

[![Step 3b: main drive pinion and skull shown separately and installed](images/ghouls-grip-montage-03b.png)](images/ghouls-grip-montage-03b.png)

Insert the main drive pinion axially through the front-wall hole **from the
inside**. Its teeth must engage the slider rack. Move the slider to its closed
starting position without forcing it against a stop. Fit the skull onto the
D-shaft from outside, with its face vertical; secure the aligned cross-holes
with the **14-mm filament pin**.

**Intermediate check:** A small turn of the knob moves the slider without the
teeth skipping. The knob is a rotary drive, not a push button.

## 4. Install the Lid Follower and Transfer Gears

**Image group 4 · original assembly steps 5–6**

[![Step 4: follower and both transfer gears before and after installation](images/ghouls-grip-montage-04.png)](images/ghouls-grip-montage-04.png)

Lower the follower rack into its guide channel. From the inside, press the
**single solid follower press pin (13.1 mm overall length, no longitudinal slot,
with crush ribs)** through the follower and into the slider's reinforced cam
slot. The extended pin fully spans the cam guide, widened to 6.0 mm, and
reaches to within 0.5 mm of the chest's inner wall (`y = 57.5 mm`), so it cannot
slip inward out of the guide under load. Do not confuse it with the slotted
scissor pins. The ribs on this pin provide the intended press fit.

Slide both transfer gears (`Transfer 1` and `Transfer 2`) axially in **−X**
through their bearing blocks until the shoulder seats inside and the
**integrated slotted barb (clip, like the pivot pins)** audibly or perceptibly
engages behind the bearing block on the outside. A short 5-mm piece of filament
is **no longer** needed here (filament cannot bend around and would work its way
out of the small journal). The two gears transmit motion to the lid crank,
which is installed later.

**Intermediate check:** When the slider is moved carefully, the follower first
rises and then stays on the upper section of the cam track. It must not jump
out of the guide or bind.

## 5. Assemble Both Scissor Layers

**Image group 5 · original assembly step 7**

[![Step 5: two scissor pairs and lower pivot pins at 18 degrees](images/ghouls-grip-montage-05.png)](images/ghouls-grip-montage-05.png)

Arrange two arms as a crossed pair in each of the two lateral scissor layers.
At the bottom, the arms connect to one fixed floor point and one moving slider
point; at the top, they connect to a fixed point and a slotted point on the
lift yoke. The hole countersinks should face outward.

Start with the scissors in the flat position (**18°**). Install **6 pins from
three different length groups** here:

1. **Fixed at the bottom of the chest (`pivot-pin-floor`, 2× from the “three very long” group, 21.6 mm—the two longest pins):** Install first while the center is still easily accessible—insert **from the inside of the chest outward** through both cheeks of the floor bearing, never through the closed outer wall.
2. **Moving at the bottom on the slider (`pivot-pin-slider`, 2× from the “five long” group, 14.4 mm):** Insert from inside outward through the lower moving scissor eye and slider mount.
3. **Scissor center (`pivot-pin-centre`, both “two short” pins, 11.6 mm):** Insert from inside outward through the center crossing point of the two scissor arms in each layer.

Leave the four upper scissor pivot points open until installing the lift yoke (Section 8).

**Intermediate check:** Both pairs must move together without sideways
distortion. Support loose parts while doing so. If the holes are misaligned, do
not lever them into position with the pin.

## 6. Install the Scissor Input Gear Before the Lift Yoke

**Image group 5 · original assembly step 8**

[![Step 6: install the scissor input gear at 48 degrees before the lift yoke](images/ghouls-grip-montage-06.png)](images/ghouls-grip-montage-06.png)

For this step, move the supported scissors to the **48° position**. Slide the
input gear onto the upper arm eye from **+Y**, align its locating pin with the
arm hole, and seat it. This gear must be installed **before** the platform;
access for insertion is restricted afterward. The upper joints are secured
finally when the lift yoke is installed.

**Intermediate check:** The locating pin is seated in the intended arm hole.
The gear must not simply rest loose on the arm surface.

## 7. Preassemble the Lift Yoke and Forearm Outside the Chest

**Image groups 6–7 · original assembly step 9**

[![Step 7: lift yoke, forearm, D-shaft, and idler gears shown separately and preassembled](images/ghouls-grip-montage-07.png)](images/ghouls-grip-montage-07.png)

Set the platform aside outside the chest. Place the forearm between the bearing
ears. Pass the D-shaft of the forearm output gear axially through the bearings
and the matching D-hub in the forearm. Secure the shaft on the outside with the
**10-mm filament pin**.

Install the three idler gears on their bearing points and secure them with the
**remaining 3 pins from the “five long” group (`pivot-pin-idler`,
14.6 mm)**. Their heads sit in the shallow countersinks in the idler gears.
Together with the scissor input gear and forearm output gear, they form the
five-gear train.

**Intermediate check:** The three idler gears and the output gear share a
common meshing plane. The shaft is secured, and the forearm can move with the
output gear.

## 8. Install the Lift Yoke in the Scissors

**Image group 6 · continuation of original assembly step 9**

[![Step 8: lift-yoke assembly above the deployed scissors and engaged](images/ghouls-grip-montage-08.png)](images/ghouls-grip-montage-08.png)

Move the supported scissors to the deployed position (**78°**). First offset
the preassembled platform **3 mm away from the scissor input gear**, toward the
first idler gear. Lower it in this offset position. Only then slide it into
engagement along the line connecting the gear axes.

**Do not simply press it vertically into the gear teeth:** the axis connection
is at 64° to vertical; lowering it straight down would make tooth tips collide.
After alignment, close the four upper joints with the **last 4 remaining pins**:

- **1× the last “very long” pin (`pivot-pin-gear` / `fixed-1`, 19.6 mm):** At the upper rear (**+Y**), through the lift-yoke bearing, upper scissor eye, **and** scissor input gear.
- **All “three very short” pins (`pivot-pin-short`, 3× 10.0 mm):** In the remaining three upper joints without gears—**1×** upper fixed point at the front (**−Y**, `fixed-0`) and **2×** upper slot points at front and rear (**−Y** `slot-0` and **+Y** `slot-1`).

**Intermediate check:** Both scissors support the yoke. The upper moving points
travel in their slots; all five gears mesh. If you feel resistance, disengage
the assembly and check the gear alignment.

## 9. Assemble the Palm, Fingers, and Optional Dish

**Image group 7 · original assembly step 10**

[![Step 9: palm, five fingers, and optional dish shown separately and assembled](images/ghouls-grip-montage-09.png)](images/ghouls-grip-montage-09.png)

Leave the mechanism deployed and supported. Orient the palm as in the view
project: **rolled −75°** relative to the forearm datum. Slide the hub onto the
forearm pin until the cross-holes align, then insert the **16-mm filament pin**
crosswise.

Fit each finger individually onto its matching angled MCP pin. Order:
**index finger → middle finger → ring finger → little finger → thumb**. Slide
each hub from the free end of its pin along the pin axis toward the palm. Do not
press the fingers vertically onto all the pins, and do not bend the finger
joints. The collars seat flush against
the exposed metacarpal heads.

Optional: Align the three asymmetrically positioned underside pins on the gold
dish with the three flush blind holes in the palm. Insert the dish from above
along its opening normal without using the fingers or bones as leverage.

**Intermediate check:** The wrist is cross-secured, all five fingers are in the
correct positions, and the dish is installed without stress. The fingers and
dish are removable plug-in parts and are **not locked**; hold them in place
when tilting or disassembling.

## 10. Preassemble the Lid Crank and Spacer on the Loose Lid

**Image group 8 · original assembly step 11**

[![Step 10: underside of lid with separate crank and spacer, and their installed positions](images/ghouls-grip-montage-10.png)](images/ghouls-grip-montage-10.png)

Place the lid upside down on a soft surface. Insert the lid crank from below
and slide it **5.6 mm in +X** into its drive pocket. Place the spacer from
below in the service channel between the crank and lid eye. Hold the loose parts
in position when turning the assembly over.

**Why are the lid crank and spacer separate parts instead of one?** The closed
protective hood under the lid has an opening only **25.0 mm wide**
(`x = −43.0 .. −18.0 mm`), while the crank (**11.0 mm**) and spacer
(**15.8 mm**) have a combined length of **26.8 mm**. In addition, the crank
driver must slide sideways (**5.6 mm in +X**) into the closed pocket in the
hood wall. A one-piece part therefore cannot be installed in the hood: only
after the short crank has been slid right (+X) into the pocket does the 15.8-mm
space behind it (−X) become available. The spacer is inserted from below into
that space to positively prevent the crank from sliding back.

**Filament-hole note:** The crank and spacer are printed upright (hole vertical
in Z, with 5 walls and 100% infill), so their CAD holes are enlarged to
**Ø 2.30 mm** (`r = 1.15 mm`) to let the 1.75-mm filament slide through as
easily as it does through the horizontally printed lid hinge eyes. If you have
an older print with Ø 2.00 mm holes, ream both parts by hand with a
**2.0-mm drill bit**.

**Important:** Attach the lid to the chest only after this step. With the lid
installed, the service channel is closed and the crank can no longer be inserted
from below.

**Intermediate check:** The crank driver is seated in the pocket; the crank,
spacer, and hinge eyes share the same axis.

## 11. Fit the Lid and Insert the Hinge Pin

**Image group 8 · original assembly step 12**

[![Step 11: open lid assembly before fitting and in hinge position](images/ghouls-grip-montage-11.png)](images/ghouls-grip-montage-11.png)

Carefully move the mechanism to the **48° scissor position**; the lid drive is
open in this position. Hold the lid assembly about **108° open** and offset it
initially **3 mm to the rear (+Y)**. Lower it, then slide it forward to engage
with the transfer idler gear until the hinge eyes align.

Slide the **198-mm hinge filament in from the end** through the chest, lid,
crank, and spacer. Support the lid while doing this. If there is resistance,
align the eyes; do not force the assemblies together with the long filament pin.
The spacer keeps the crank axially engaged.

**Intermediate check:** The pin is fully inserted, the spacer is in place, and
the lid crank is connected to the lid. The lid is guided by the gear train; do
not open or close it independently against the drive.

## 12. Dry Run and Acceptance Check

[![Step 12: complete assembly retracted and deployed for the dry run](images/ghouls-grip-montage-12.png)](images/ghouls-grip-montage-12.png)

First test **without candy and without a load**. Slowly turn only the skull
through its intended travel of approximately 114°, then turn it exactly back.
Do not rotate past the end positions.

- [ ] The lid opens early and clears the hand's range of motion.
- [ ] Both scissors lift evenly; no arm rubs against the chest wall.
- [ ] The forearm unfolds as the mechanism lifts and folds back during return.
- [ ] The hand, including the optional dish, fits fully inside when retracted.
- [ ] No teeth skip, no pin works its way out, and no snap joint binds.
- [ ] The lid closes without being pushed by hand; loose fingers and dish remain seated.

**Stop immediately if you hear cracking, feel strong resistance, or notice
teeth skipping.** Release the mechanism and fix the cause instead of applying
more force to the knob. Passing the digital checks does not replace this
inspection of the printed part. No payload capacity or PLA fatigue life has
been confirmed; do not leave it loaded unattended.

Use only packaged candy or a food-safe insert. Unprotected FDM PLA is not
certified as food-safe. Do not fill above the free height available when closed.

## 13. Common Assembly Problems and Disassembly

| Problem | Check first |
| --- | --- |
| Slider binds | Support residue in the guide, both snap fingers correctly engaged in the groove, frame not skewed |
| Snap pin does not engage | Correct clamping length, aligned holes, clear slot halves; do not force a shorter pin |
| Lift yoke cannot be installed | 78° position, input gear already installed, 3-mm offset before engagement |
| Lid crank cannot be installed | Remove the lid again; crank and spacer must be preassembled on the loose lid |
| Lid drive skips | Transfer gears secured, crank driver in pocket, spacer installed |
| Hand or fingers do not fit | Correct D-shaft/pin orientation, finger assignment, and cleared support residue; do not bend bones |
| Pin moves axially | Stop operation and check retention; especially for older printed floor pins |

Before disassembly, unload the mechanism and support the lid and hand. Remove
the dish, pull out the filament pins, and disassemble in reverse order. Release
snap pins from the barb side by squeezing the slotted halves together; do not
force them out by pulling on the heads.

**Older print versions:** The dimensional document describes earlier floor
pins without the newer locking feature. The current BOM uses snap pins; do not
assume these versions are interchangeable based on color alone. If the print
version is unknown, first compare the parts with the print project actually used.

## Sources and Limitations

Dimensions, insertion directions, and sequence are taken from the
[dimensions and design documentation](ghouls-grip-masse-und-bauanleitung.md#assembly-steps).
Scissor positions specified for individual operations are from the
[assembly audit, Sections 5–6](ghouls-grip-montage-audit.md).
The angles are **scissor angles**, not knob angles. The
[view project](../models/ghouls-grip-view.3mf) includes the 18°, 48°, and 78°
positions as a spatial reference. The exploded view shows unchanged original
meshes but is not a scale assembly jig. These instructions change neither the
geometry nor the [print/profile status](ghouls-grip-druckvalidierung.md).

### Reproducing the Step Illustrations

`scripts/render_ghouls_grip_assembly.py` reads only the existing 42 bodies in
the three positions in the view 3MF. Blender renders twelve image pairs;
Pillow adds German legends and the overview. Only presentation offsets are
applied; no print bodies are changed or exported. The illustration sequence is
not sliced again.

```powershell
.\.venv\Scripts\python.exe scripts\render_ghouls_grip_assembly.py
```

The images are in `docs/images/ghouls-grip-montage-02.png` through
`docs/images/ghouls-grip-montage-12.png` (Section 3 uses `03a` and `03b`).
The overview is
`docs/images/ghouls-grip-montage-bildfolge.png`. Raw images and camera
projections remain under `build/ghouls-grip-assembly/`. The renderer checks
complete part assignment, camera bounds, nonempty images, and unchanged SHA-256
values for the three Ghoul’s-Grip model files.
