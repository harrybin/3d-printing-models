# Butterfly Knife (`butterfly-messer`): Asset Research & License Decision

## 1. Search Results for Reusable 3D Assets (`research-reusable-3d-assets`)

Before modeling, existing open-source SCAD/CAD/STL models for printable Balisong/butterfly knives and trainers were searched:

| Source / repository | Author | License | Geometric suitability | Decision |
| --- | --- | --- | --- | --- |
| [ferretallicA/balisong-v2](https://github.com/ferretallicA/balisong-v2) (`balisong.scad`) | ferretallicA | No license file in repository (`All Rights Reserved` by GitHub default) | OpenSCAD Balisong with simple cylindrical pins, without the classic skeletonized hole pattern (5 large + 6×2 small holes), integrated Zen-pin stop, or tool-free D-bolt/U-clip retention | **Reference only (`reference-only`)** — no license to redistribute or modify |
| [j557/balisong](https://github.com/j557/balisong) (`main.scad`, `balisong.stl`) | j557 | No license file in repository (`All Rights Reserved` by GitHub default) | Print-in-place prototype without separate multicolor assemblies, a putty/scraper edge, or a locking T-latch | **Reference only (`reference-only`)** — unclear license and different functional architecture |

## 2. Selected Strategy (`asset_strategy = rebuild`, `modeling_route = python`)

- **Strategy:** Complete parametric rebuild (`rebuild`) in [`scripts/butterfly_messer.py`](../scripts/butterfly_messer.py), based on:
  1. the reference photo provided by the user ([`model-sources/archiv/butterfly-messer-referenzfotos-index.png`](../model-sources/archiv/butterfly-messer-referenzfotos-index.png), tile `00`),
  2. published standard Balisong dimensions (Benchmade 42 / classic 5-hole stainless-steel Balisong with T-latch), and
  3. FDM design parameters for the **Anycubic Kobra S1 Combo + ACE Pro** established during the user interview.
- **Why Python rather than Blender (`modeling_route = python`):** All 14 parts have technical, functional, tolerance-critical geometry (pivots with `0.30 mm` radial clearance, anti-rotation D-bolts, snap-fit U-clips with `0.15 mm` fit, Zen-pin stop geometry for `0°` and `180°`, and a putty/scraper blade with a double-sided 45° bevel).
