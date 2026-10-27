# Butterfly Knife (`butterfly-messer`): Dimensions, Joints & Kinematic Verification

## 1. Dimensions and Specifications (`research-part-specs`)

Reference image: [`model-sources/archiv/butterfly-messer-referenzfotos-index.png`](../model-sources/archiv/butterfly-messer-referenzfotos-index.png) (tile `00`: classic skeletonized stainless-steel butterfly knife, shown closed and open with T-latch).

| Feature / parameter | Value | Origin & source | Confidence (`Confidence`) |
| --- | ---: | --- | --- |
| Total open length (including T-latch) | `243.45 mm` (`220.0 mm` without latch) | Standard Balisong geometry (Benchmade 42: `9.4 in / 238.8 mm` open) + proportions from tile `00` | High (published standard dimension + photo comparison) |
| Handle length (`U = -6.0 .. +119.0 mm`) | `125.00 mm` | Classic 5-inch Balisong handle (`4.92–5.00 in / 125 mm`), tile `00` | High (published standard dimension) |
| Exposed blade length from pivot (`X = -95.0 .. 0.0 mm`) | `95.00 mm` | Sized to the `125 mm` handle length so that at `180°` the blade tip remains `> 10 mm` clear of the rear spacer inside the handle channel | High (kinematically verified) |
| Blade width / height (`Y`) | `16.80 mm` | Proportions from tile `00` (spear/clip point with pronounced swedge and choil) | Medium–high (photo-calibrated) |
| Blade spine thickness (`Z`) | `3.60 mm` | FDM-optimized blade thickness for a torsionally rigid PLA putty blade in the `4.20 mm`-high handle channel | High (user interview & FDM design) |
| Putty/scraper edge (`R_EDGE_BLUNT` / bevel) | `0.40 mm` leading edge, `45°` on both sides (`1.60 mm` deep) | Mechanically usable scraping/putty edge requested by the user during the interview; printable flat without supports | Confirmed (user decision) |
| Handle channel inner height (`Z_CHANNEL_MIN .. MAX`) | `3.20 .. 7.40 mm` (`4.20 mm` clearance) | `3.60 mm` blade + `2 × 0.30 mm` axial clearance (`0.30 mm` below, `0.30 mm` above) | Confirmed (user interview: `0.30 mm` joint clearance) |
| Lower / upper handle-scale wall thickness | `3.20 mm` (`Z = 0..3.2` and `8.4..11.6 mm`) | Robust sandwich scales for `1.6 mm` wall thickness (4 wall loops) and `55%` gyroid infill | Confirmed (user interview) |
| Pivot spacing (`±Y_PIVOT`) | `±10.20 mm` (`20.40 mm` center-to-center) | Symmetric spacing of the two main handle axes; gives a `0.50 mm` gap between the Safe and Bite handles at `0°` and `180°` | High (kinematically verified) |
| Integrated Zen-pin stop (`X_ZEN`, `±Y_ZEN`, `R_ZEN`) | `X = 0.00 mm`, `Y = ±10.20 mm` (local `u = 10.20 mm`), `Ø 5.20 mm` | Stop post integrated into the lower handle scales; engages exactly with the four semicircular tang recesses (`R = 2.85 mm`) at the blade root at `0°` (open) and `180°` (closed) | High (proven analytically and with manifold sweeps) |
| Handle skeleton hole pattern | 5 large countersunk holes (`Ø 6.80 mm`) + 6 pairs of small holes (`Ø 2.50 mm`) | Matches tile `00` exactly (5 large center holes alternating with 6 pairs of rivet/pin holes along both handle halves) | High (direct evidence in tile `00`) |
| Pivot and D-hole clearance (`R_BOLT_SHAFT`, `D_FLAT_BOLT`) | `0.86 mm` total clearance (`Ø 5.30 mm × 4.80 mm` D-hole over `Ø 4.44 mm × 3.94 mm` bolt shaft) | Slimmed bolt shaft with lead-in chamfer (`Z = 11.35 .. 11.60 mm`) after test printing for smooth insertion | Confirmed (test-print adjustment) |
| U-clip ring-groove clearance (`X_NOTCH_HALF`, `U_CLIP_SLOT_HALF`) | `2.30 mm` bolt land width in `3.32 mm` clip jaw width (`1.65 mm` groove width for `1.00 mm` clip) | Recessed and widened ring groove (`Z = 9.25 .. 10.90 mm`), also compatible with clips already printed | Confirmed (test-print adjustment) |

---

## 2. Tool-Free, Removable FDM Joints (`reversible-fdm-joints`)

To print the knife completely **without glue**, **without metal screws**, and with **0.00 g support**, while still allowing disassembly and maintenance at any time, the following interlocking joints were designed:

1. **4× anti-rotation D-bolts (`butterfly-messer-bolzen-*`):**
   - Slimmed shaft diameter `Ø 4.44 mm` (`R = 2.22 mm`) with a continuous flat at `y_local = -1.72 mm` (`3.94 mm` D-height) and a top lead-in chamfer (`Z = 11.35 .. 11.60 mm`).
   - This lets the bolt lie completely flat on its D-flat while printing (`Z_print = 0.00 mm`) — the layers run **along the bolt axis**, providing maximum shear and bending strength across the joint!
   - The transition from the countersunk head (`R = 3.25 mm`, `Ø 6.50 mm`) to the shaft uses a self-supporting **45° chamfer**, matching the 45° countersink in the lower handle scales.
2. **4× interlocking U-retaining clips (`butterfly-messer-clip-*`):**
   - Engage laterally (`±X`) with a `3.32 mm` jaw width (`±1.66 mm`) in the recessed three-sided ring groove (`x_local = ±1.15 mm` = `2.30 mm` land width, `Z = 9.25 .. 10.90 mm` = `1.65 mm` groove width) at the upper end of the bolt, and sit recessed in the pockets of the upper handle scales (`Z = 9.45 .. 10.65 mm`).
3. **Integrated locating pins between lower and upper scales:**
   - Each lower handle scale (`griff-*-unten`) has one locating pin (`Ø 3.10 mm`, `Z = 8.40 .. 9.65 mm`) at the Zen pin (`u = 10.20 mm`) and at the rear spacer (`u = 99.00 mm`). Each pin engages a matching pocket (`Ø 3.40 mm` with a self-supporting **45° conical roof**) in the upper handle scale (`griff-*-oben`).
4. **Pivoting T-latch (`butterfly-messer-riegel`):**
   - Sits on the rear D-bolt of the Bite handle (`u = 108.50 mm`, `y = -10.20 mm`) and, when closed (`180°`), locks positively into the latch recess at the end of the Safe handle at `phi_latch = 90°`.

---

## 3. Assembly Order & Linear Insertion Sweeps (0.000 mm³ Collision)

All 12 moving or inserted parts were checked in [`scripts/butterfly_messer.py`](../scripts/butterfly_messer.py) for manifold intersection volume against all previously assembled parts over **21 steps** (`0.0 mm .. 28.0 mm`) along their assembly vectors:

| Step | Part | Insertion direction | Obstacles checked (already assembled) | Max. intersection volume (`mm³`) | Status |
| ---: | --- | :---: | --- | ---: | :---: |
| 1 | `griff-safe-unten` & `griff-bite-unten` | Base on table | — | `0.000000` | **PASS** |
| 2 | `butterfly-messer-klinge` | `-Z` `(0, 0, -1)` | `griff-safe-unten`, `griff-bite-unten` | `0.000000` | **PASS** |
| 3 | `butterfly-messer-riegel` | `-Z` `(0, 0, -1)` | `griff-safe-unten`, `griff-bite-unten`, `klinge` | `0.000000` | **PASS** |
| 4 | `griff-safe-oben` | `-Z` `(0, 0, -1)` | `griff-safe-unten`, `klinge`, `riegel` | `0.000000` | **PASS** |
| 5 | `griff-bite-oben` | `-Z` `(0, 0, -1)` | `griff-bite-unten`, `klinge`, `riegel` | `0.000000` | **PASS** |
| 6 | `bolzen-safe-vorn` | `+Z` `(0, 0, +1)` | `griff-safe-unten`, `griff-safe-oben`, `klinge` | `0.000000` | **PASS** |
| 7 | `bolzen-bite-vorn` | `+Z` `(0, 0, +1)` | `griff-bite-unten`, `griff-bite-oben`, `klinge` | `0.000000` | **PASS** |
| 8 | `bolzen-safe-hinten` | `+Z` `(0, 0, +1)` | `griff-safe-unten`, `griff-safe-oben` | `0.000000` | **PASS** |
| 9 | `bolzen-bite-hinten` | `+Z` `(0, 0, +1)` | `griff-bite-unten`, `griff-bite-oben`, `riegel` | `0.000000` | **PASS** |
| 10 | `clip-safe-vorn` & `clip-bite-vorn` | `+X` `(+1, 0, 0)` | Corresponding handle scales + D-bolts | `0.000000` | **PASS** |
| 11 | `clip-safe-hinten` & `clip-bite-hinten` | `-X` `(-1, 0, 0)` | Corresponding handle scales + D-bolts | `0.000000` | **PASS** |

![Explosionszeichnung Butterfly-Messer](images/butterfly-messer-explosion.png)

---

## 4. Kinematic Verification Across the Full Swing Range (`0° .. 180°`)

- **Handle rotation (`theta_safe`, `theta_bite` from `0°` to `180°` in `5°` steps = 37 states):**
  - The Safe handle rotates about `(0.0, +10.20 mm)` around `+Y` from `0°` (open) to `+180°` (closed).
  - The Bite handle rotates about `(0.0, -10.20 mm)` around `-Y` from `0°` (open) to `-180°` (closed).
  - **Result:** Across all 37 angular positions, pairwise manifold intersection volume between the blade, Safe-handle assembly, Bite-handle assembly, and T-latch is exactly **`0.000000 mm³`** (`PASS`).
- **T-latch swing range when closed (`theta = 180°`, `phi_latch` from `0°` to `90°` in `5°` steps = 19 states):**
  - The T-latch rotates freely about the rear Bite bolt `(-108.50 mm, -10.20 mm)` from the open longitudinal position (`0°`) to the locked transverse position (`90°`) over the Safe handle.
  - **Result:** Maximum intersection volume across all 19 latch angles: **`0.000000 mm³`** (`PASS`).
- **End-position verification:**
  - **Open (`0°`):** The Zen pins sit with defined clearance in the front tang recesses; the two handles are parallel with a `0.50 mm` gap; the blade extends `95.0 mm`.
  - **Closed & locked (`180°`, `phi_latch = 90°`):** The putty edge is fully protected inside the Bite-handle channel; the Zen pins bear against the rear tang recesses; the T-latch positively wraps around the rear end of the Safe handle.
