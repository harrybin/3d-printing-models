# Dimensions and Source Documentation: Ohnezahn / Toothless Dragon Figure (`drache`)

## 1. Reference Object Identification

- **Motif / character**: **Ohnezahn (Toothless / Nachtschatten / Night Fury)** from *Drachenzähmen leicht gemacht* (*How to Train Your Dragon*).
- **Figure reference**: Spray-painted/cast miniature collectible figure (Spin Master *Dragons* mini figure, approx. 3-inch / ~78 mm class).
- **Important user requirement**: **Omit** the production/copyright code (`41204AFS`) printed on the underside of the tail.
- **Reference index sheet**: `model-sources/drache_frames/_index.png` (25 extracted video frames, tiles `#00` through `#24`).

### Color Regions / Material Semantics from the Reference Images

| Region | Color / appearance | Reference tiles (`_index.png`) |
| --- | --- | --- |
| Main body, legs, head, wings, back spines, right tail fin | **Black (matte)** with a slightly textured scale surface on the legs and back | `#00`–`#24` (`frame_03_f0064.jpg`, `frame_13_f0384.jpg`, `frame_19_f0576.jpg`) |
| Eyes (left & right) | **Light green / lime green** with vertical **black slit pupils** | `#02` (`frame_03_f0064.jpg`), `#16` (`frame_17_f0512.jpg`), `#18` (`frame_19_f0576.jpg`), `#23` (`frame_24_f0736.jpg`) |
| Left tail-fin prosthesis | **Red** | `#02` (`frame_03_f0064.jpg`), `#07` (`frame_08_f0224.jpg`), `#18` (`frame_19_f0576.jpg`), `#23` (`frame_24_f0736.jpg`) |
| Emblem on the left red tail fin | **White** (stylized Viking/skull symbol on the upper surface) | `#02` (`frame_03_f0064.jpg`), `#18` (`frame_19_f0576.jpg`), `#23` (`frame_24_f0736.jpg`) |

---

## 2. Scale Reference & Photogrammetric Measurement

A **2-euro coin** lies directly beside the figure on the same cardboard plane and serves as the scale reference.

### Official Standard Dimensions of the 2-Euro Coin (European Central Bank)

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Coin diameter (`D_coin`) | **25,75 mm** | ECB / Official Journal of the European Union | **Verified (standard dimension)** |
| Coin thickness (`H_coin`) | **2,20 mm** | ECB / Official Journal of the European Union | **Verified (standard dimension)** |

### Derived Figure Dimensions (1:1 Scale Calibrated Using the 2-Euro Coin)

From tiles `#02` (`frame_03_f0064.jpg`, right-side view), `#07` (`frame_08_f0224.jpg`, rear view with coin at the same depth plane `y ≈ 1045 px`, `180 px = 25,75 mm` → `0,1431 mm/px`), `#12` (`frame_13_f0384.jpg`, left-side view), `#18` (`frame_19_f0576.jpg`, front view with coin `196 px = 25,75 mm` → `0,1314 mm/px`), and `#23` (`frame_24_f0736.jpg`, angled view):

| Dimension / feature | Value (mm) | Derivation / tile reference | Status |
| --- | --- | --- | --- |
| **Overall length (X)** (snout tip to rear tail-fin tip) | **78,0 mm** (`± 2,0 mm`) | Tile `#02`: `674 px` with depth correction `0,1125 mm/px` and yaw angle `~12°` (`3,03 × D_coin`) | Photo-derived (calibrated using the 2-euro coin) |
| **Overall width (Y)** (left wingtip to right wingtip) | **45,5 mm** (`± 1,5 mm`) | Tile `#07`: `317 px × 0,1431 mm/px = 45,35 mm` (`1,76 × D_coin`) | Photo-derived (calibrated using the 2-euro coin) |
| **Overall height (Z)** (base surface to tip of red tail fin) | **60,5 mm** (`± 2,0 mm`) | Tiles `#02` & `#23`: `540 px × 0,1125 mm/px = 60,75 mm` (`2,35 × D_coin`) | Photo-derived (calibrated using the 2-euro coin) |
| **Wingtip height (Z)** (base surface to top edge of main wing) | **50,0 mm** (`± 1,5 mm`) | Tile `#02` (`50,9 mm`) & tile `#07` (`49,5 mm`) | Photo-derived |
| **Hind-leg stance width (Y)** (outer edge of left to right hind paw) | **40,0 mm** (`± 1,0 mm`) | Tile `#07`: `280 px × 0,1431 mm/px = 40,06 mm` | Photo-derived |
| **Span of secondary wings / hip fins (Y)** | **36,8 mm** (`± 1,0 mm`) | Tile `#07`: `257 px × 0,1431 mm/px = 36,77 mm` | Photo-derived |
| **Body width at hips (Y)** | **25,5 mm** (`± 1,0 mm`) | Tile `#07`: `178 px × 0,1431 mm/px = 25,46 mm` (`≈ 1,0 × D_coin`) | Photo-derived |
| **Head width (Y)** (cheek to cheek without / with lateral protrusions) | **28,0 mm / 31,5 mm** | Tiles `#18` & `#02` | Photo-derived |
| **Head length (X)** (snout to back of head / including long head spikes) | **25,0 mm / 35,0 mm** | Tiles `#02` & `#12`: `221 px` and `311 px × 0,1125 mm/px`, respectively | Photo-derived |
| **Head height (Z)** (chin to top of skull) | **22,5 mm** | Tile `#02`: `200 px × 0,1125 mm/px` | Photo-derived |
| **Shoulder/back height (Z)** (base surface to back line between the wings) | **30,5 mm** | Tiles `#02` & `#12`: `270 px × 0,1125 mm/px` | Photo-derived |
| **Back and tail bumps (4 large bumps on back/tail)** | **Ø 3,6–4,2 mm, height 3,5–4,5 mm** | Tiles `#02`, `#12`, `#23`: characteristic rounded attachment/back bumps ahead of the smaller tail spikes | Photo-derived |
| **Tail-fin span (across the tail axis)** | **22,0 mm** | Tiles `#02`, `#18`, `#23`: asymmetrical V profile (red with a white symbol on the left, black on the right) | Photo-derived |

---

## 3. Reusable 3D Asset Research (`research-reusable-3d-assets`)

Before modeling, existing 3D models of *Toothless / Night Fury* were searched for:

1. **Printables / MakerWorld / MyMiniFactory (*Toothless – Night Fury* by José Pedro / marjers, Becca_3D / Kaijumon)**:
   - License: `CC BY-NC-SA 4.0` or *Standard Digital File License (Personal Use Only)*.
   - Classification: **Visual reference only (`reference-only`)**, due to restrictive NC licenses and different poses.
2. **Sketchfab (*Night Fury Toothless* by BenAissa_Karim, *Toothless night fury* by LunaEagle)**:
   - License: `CC-BY` according to metadata, but behind a login wall and depicting flying/standing poses that do not match the compact crouched toy figure with its characteristic back bumps, paired short wings, and raised S-shaped tail.
3. **Decision (`asset_strategy = rebuild` in Blender + Python)**:
   - Complete, license-free original reconstruction of the exact figure in **Blender 5.2** (organic sculpting from subsurface/metaball/voxel-remesh geometry with precisely formed color bodies), combined with **Python (`trimesh` / `manifold3d`)** for exact dimensional calibration, flat base surfaces on all four paws, boolean color-region separation, mesh validation, and OrcaSlicer 3MF packaging.
