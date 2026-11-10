# Gothic Chest: Relief Sources, Licenses, and Print Validation

Status: sculpting pass for "organic, photorealistic" reliefs.
Betrifft `scripts/gothic_chest.py`, `scripts/blender_chest_reliefs.py`,
`assets/gothic-chest-reliefs/*.npz`.

## 1. Asset Research and License Decision

**Result: no suitable, license-verified asset found — sculpted procedurally in
Blender.**

The search looked for suitable flat reliefs (Gothic ornament, skull, dragon,
snake) under a clear license permitting derivatives and redistribution:

| Source | Result | Reason for rejection |
| --- | --- | --- |
| Sketchfab CC0 collections | matches, but full sculptures | Full 3D scans, not bas-reliefs; conversion to `z = f(x, y)` would amount to remodeling |
| Smithsonian Open Access | inaccessible | API/download blocked with HTTP 403 |
| Scan the World / MyMiniFactory | matches | predominantly CC-BY-NC or unclear licensing, with no verified permission for derivatives/redistribution |
| Thingiverse (CC0 filter) | matches | license information inconsistent with the actual upload and unverifiable |
| Wikimedia Commons `Category:STL files` | few matches | no Gothic creature reliefs in usable quality |
| awesome-cc0 / public CC0 lists | no matches | no suitable motif |

Accordingly, **no third-party asset is used and no attribution is required**.
All geometry was created by this repository and is subject to the repository
license.

### Derived Asset in the Repository

`assets/gothic-chest-reliefs/{front,rear,side,lid}.npz` + `manifest.json` are
cached height fields normalized to 0..1 (panel grid approx. 0.58–0.65 mm). They
can be reproduced with:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
    --background --python scripts\blender_chest_reliefs.py
```

The cache exists only so that the chest generator can run without Blender.

## 2. Pipeline

1. **Blender 5.2 headless** (`scripts/blender_chest_reliefs.py`): motifs from
   Metaball chains (`ball`/`blob`/`chain`/`membrane`), noise displacement,
   smooth shading → organic, fused masses instead of stacked primitives.
2. **Height-field extraction** via BVH raycast from above; cavities (eye sockets,
   nose opening, temple depressions) are lowered in 2D in the height field.
   *Not* with Blender Boolean: the EXACT solver flips interior/exterior parity
   with dozens of overlapping ellipsoids and destroyed the relief (24 269 →
   3 957 faces).
3. **Solid generation** in `gothic_chest.py` (`_heightfield_solid`):
   binomial smoothing, boundary clamped to 0, closed grid prism with a 0.4 mm
   backing plate.
4. **Placement**: 45° shear `y += z` → each bas-relief `z = f(x, y)` is
   geometrically guaranteed to have no overhang > 45° afterward.

## 3. Motif Inventory

| Location | Motifs | Raised / recessed | Depth | Remaining material |
| --- | --- | --- | --- | --- |
| Front wall | 2 skulls with snakes, vines, 4 volutes | raised, sheared | up to 2.43 mm above the wall | wall untouched |
| Rear wall | central rib cage, 2 facing wyverns (head, horns, teeth, claws, wings), volutes, vines | raised, sheared | up to 2.37 mm | wall untouched |
| Side walls (2×) | skull with snake, volutes, vine | raised, sheared | up to 2.77 mm | wall untouched |
| Lid | winged skull cartouche with snakes and volutes | raised, sheared | up to 3.0 mm | lid untouched |
| Pilasters (8 outer faces, 3 flutes each) | Gothic fluting | **recessed** | 1.2 mm | 5.0 mm stock → **3.8 mm**, above the 1.8-mm minimum |

The flutes are vertical capsules with spherical ends: no horizontal ceiling, no
sharp undercut — therefore no supports are needed.

The 2.0-mm wall panels themselves are **not** engraved: with the shell tuned
for minimal material, less than 1.8 mm of material would remain there.

## 4. Validation

```powershell
.\.venv\Scripts\python.exe scripts\gothic_chest.py
# chest  faces  74750 watertight True bodies 1 euler -8  extents [209.0, 130.5, 98.0]
# lid    faces  27796 watertight True bodies 1 extents [206.0, 129.786, 28.2]

.\.venv\Scripts\python.exe scripts\mesh_tool.py validate model-sources\ghouls-grip\reference\_chest.stl
# PASS - watertight, manifold, euler_number -8, ready to slice
.\.venv\Scripts\python.exe scripts\mesh_tool.py validate model-sources\ghouls-grip\reference\_lid.stl
# PASS - watertight, manifold, euler_number -58, ready to slice

.\.venv\Scripts\python.exe -m unittest tests.test_gothic_chest_reliefs
# Ran 6 tests - OK
```

(The `WARN not centered` message is intentional: the chest is positioned by
the exporter.)

## 5. Support Gate (decisive)

`scripts/audit_chest_support.py` creates **identical**
OrcaSlicer projects for the control and decorated versions — same process,
machine, and support settings (automatic tree supports enabled); geometry is
the only difference. The path count and sum of positive E deltas are then
counted in the G-code under `;TYPE:Support` /
`;TYPE:Support interface`.

| Variant | Support paths | Support E | Filament |
| --- | --- | --- | --- |
| `build_chest(include_decoration=False)` (control) | 71 | 82.376 | 188.61 g |
| sculpted chest | **71** | **82.376** | 196.51 g |

**PASS — exactly support-neutral.** All support is generated at the hinge and
lid supports, not on the relief. For comparison, the previously measured
fully recessed design: 245 paths / 569.21 E.

Artifacts: `build/ornament-audit/audit-control.3mf`,
`audit-sculpted.3mf`, `audit-*-slice/plate_1.gcode`, `audit-*-slice.log`.

## 6. Evaluation Renders

- `build/ornament-audit/render-chest-front.png`
- `build/ornament-audit/render-chest-rear.png`
- `build/ornament-audit/render-chest-side.png`
- `build/ornament-audit/render-chest-hero.png`
- `build/ornament-audit/render-lid-top.png`
- `build/ornament-audit/render-lid-raking.png`
- Height-field/hillshade previews: `height-*.png`, `shade-*.png`

## 7. Remaining Risks

- The wyverns are the weakest motif: the head, horns, and wings read clearly,
  but the claws are borderline fine at a 0.6 mm nozzle width.
- Relief peaks are 2.4–3.0 mm high; increasing their depth would require
  repeating the support gate.
- The `.npz` cache must be regenerated after every Blender change; otherwise,
  the script and geometry will diverge.
- The local 28,2-mm lid height comes from the closed protective cover over the
  yoke and lid crank, not from a globally thickened lid shell. The cover has a
  2,0-mm roof skin and an installation cavity open only to the inside.
