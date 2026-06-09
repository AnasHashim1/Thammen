# PHASE 0 — Geometric-footprint sprint (2.22.0b.10) §5 recon

> **Read-only. No engine change.** Live GIS run (`.b10_recon.py`, this session) on 5 real plots.
> Answers the brief `docs/BRIEF_geometric_footprint.md` §5 mandatory recon. Engine stays b9 / Heroku v176.
> Verdict: **BUILD-READY** — the mechanism is proven, the value-invariance is clean, and the orientation
> problem is dissolvable without street detection. One framing decision needs Anas's Gate-2 signature (§6).

## 0. Measured data (live, read-only)

| Plot | pdarea | verts | is_rect | edge-pairing W×D | shoelace | bbox | cov-cap 0.60 | envelope 5/3/3 (o1/o2) | binding |
|---|---|---|---|---|---|---|---|---|---|
| **54/541/6** Marikh (motivating) | 613 | 4 | ✅ | **35.0×17.5** | 613 ✓ | 39.1×30.2 (=1182) | 368 | **311** / 276 | envelope |
| **56/565/21** Abu Hamour (anchor) | 900 | 4 | ✅ | 30.0×30.0 | 900 ✓ | 41.5×41.5 (=1723) | 540 | **528** / 528 | envelope |
| **56/647/6** Maamoura V001 (bank report) | 652 | **5** | ❌ | — (skip) | 652 ✓ | 31.9×37.2 | **391** | — | cov-cap |
| **55/296/13** thin anchor | 1050 | 4 | ✅ | 30.0×35.0 | 1050 ✓ | 43.6×40.9 | **630** | 638 / 648 | cov-cap |
| **51500109** Gharafa compound (irregular) | 67536 | **13** | ❌ | — (skip) | 67536 ✓ | 330.9×387.4 | 40522 | — | cov-cap |

## 1. Q1 — edge extraction + graceful degradation → SOLVED

- **Edge-pairing on the 4-vertex ring is EXACT.** `shoelace_area == pdarea` to the integer on **all 5** plots.
  The clean dims fall straight out of consecutive-vertex distances: 35.0×17.5 (=613), 30×30 (=900), 30×35 (=1050).
- **The bounding box is WRONG — do NOT use it.** Qatar rectangles are arbitrarily **rotated** vs the 2932 grid, so
  the axis-aligned bbox nearly doubles the area (54/541/6: bbox 1182 vs true 613). The brief's hand-computed
  "35.0×17.5" was edge-pairing; a bbox model would have shipped garbage.
- **`plot.shape.is_rectangular` is a clean gate** (already computed inside `get_plot` → `analyze_polygon_shape`):
  the 3 true rectangles → True/4-verts; the 5-vert Maamoura + 13-vert compound → False. Gate the W×D model on it
  (or `len(edges)==4`); non-rectangular → fall back to the orientation-free coverage-cap. **Degrades gracefully** —
  the two non-rect plots both produced a sane coverage-cap (391, 40522) with no crash.
- **🔴 Note:** the **other** motivating villa, **Maamoura V001 (56/647/6), is a 5-vertex convex plot** (hull=1.0 —
  a rectangle with one angled/clipped corner, NOT irregular). So its auto-footprint = coverage-cap 391, not a
  setback-envelope. Acceptable for v1; a future refinement (min-area bounding rectangle / rotating calipers) could
  recover 5-vert near-rectangles, but coverage-cap is the safe fallback now. ~5-vert plots are common.

## 2. Q2 — street-edge / orientation → DISSOLVED (no detection needed)

- **The binding constraint genuinely varies** (refines the brief §3 claim that cov-cap "is often the binding"):
  the legal **setback-envelope is TIGHTER** in 2 of 3 rectangles (54/541/6 311<368, 56/565/21 528<540); the
  cov-cap binds for the larger/squarer 55/296/13 (630<648). So neither is universally binding.
- **Orientation matters most for elongated plots.** 54/541/6 (35×17.5): front-on-short-edge → 311 vs
  front-on-long-edge → 276 (a 13% spread). The square 56/565/21: both orientations = 528 (no spread).
- **Street detection EXISTS but is not needed.** `geometric_factors.detect_corner` (line 155) already probes each
  edge's midpoint vs `ROADFlowlnA` main/local roads within a 15 m buffer (parallelized, A14) and emits
  `edge_evidence` per edge → the road-abutting edge IS identifiable. BUT: it costs up to 6×2 GIS round-trips,
  uses a single midpoint sample (not robust), and on a corner plot ≥2 edges abut a road (no unique "front").
- **Resolution (orientation-free OUTCOME):** since the auto number is explicitly a **CEILING the user corrects
  DOWN** (brief §4), take the **larger** orientation envelope (the legal max across orientations) and bound it by
  the coverage cap — no street detection required:
  ```
  footprint_max = min( 0.60 × pdarea ,  max_over_orientations( (D−8)×(W−6) , (W−8)×(D−6) ) )   # 4-vert rect
  footprint_max = 0.60 × pdarea                                                                 # non-rect fallback
  ```
  (setbacks legal R1: front 5 + rear 3 = 8 on the depth axis; side 3 + side 3 = 6 on the width axis — E15 corrected.)
  Measured outcomes: 54/541/6 → **311**, 56/565/21 → **528**, 55/296/13 → **630** (cap), 56/647/6 → **391** (cap),
  compound → cov-cap. Uses the plot dims + setbacks (Anas's idea), needs zero orientation detection, always
  computable. The setback-envelope refinement keyed to a *detected* front edge stays a possible later upgrade.

## 3. Q3 — value-invariance → CLEAN (the §6 split holds)

- The **4 anchors carry no building input** → `bua_breakdown is None` → the substantiality block
  (`evaluate_unified.py:4113`) is **skipped** → today's `_suggested_fp`/`_eff_fp` never touch `valuation.amount`
  on them. So they are byte-identical regardless of the footprint formula. ✓
- **The ONE value-bearing consumer of the *assumed* footprint** is the **floors-only-no-footprint** path: there
  `_fp_confirmed=False → _eff_fp = _suggested_fp →` `_build_smart_bua → _building_substantiality →` a (capped,
  age-modulated) headline bump (`:4142`). If the geometry footprint *replaced* `_suggested_fp`, a floors-only
  input's headline would MOVE → that is a Gate-2 value change, **beyond "value-invariant."**
- **Recommended design (D1 — the §6-compliant split):** the geometry footprint is a **NEW display/confirm field**
  (`geometry.max_buildable_footprint_m2` + `plot_dims_m` + the basis method), and the **value path
  (`_suggested_fp`/`_eff_fp`) is left FROZEN at b9.** Result: byte-identical on the 4 anchors AND on floors-only
  inputs. When the user **confirms/corrects** the footprint, b2's **existing confirmed-footprint path** feeds it
  into the headline exactly as today (unchanged mechanism). The footprint→BUA→headline *auto*-wiring (so an
  un-confirmed plot's value reflects geometry) is the **§20.9 cost-triangulation Gate-2**, NOT this sprint.
  - Alternative **D2** (geometry footprint also replaces the assumed substantiality fallback) → more "one number"
    consistency but **moves floors-only headlines** → Gate-2. The brief §6 says value-invariant → **D1**.

## 4. Q4 — confirm-area UI → mostly assembly (b2 surfaces exist)

- `index.html` already has, on the always-visible **`#refineScreen`**: `floors` select (`:435`) + `footprintM2`
  input (`:445`); `thammenReEvalGeometry` reads them and re-POSTs `/api/evaluate/details` (`:866-881`); the
  results geometry card (`:1348-1378`) renders `suggested_footprint_m2` / `effective_footprint_m2` + the
  assumed/confirmed basis + the F3 cap disclosure + the F4 basement line.
- **b10 UI work = a reflow + copy, not new plumbing:** (a) **floors-first → then show the auto area** ordering;
  (b) display the **plot dims (W×D) + max-buildable footprint** with the honest **«الحدّ الأقصى المسموح — عدّله
  لواقع مبناك»** framing (brief §4 — never imply the auto number IS the building); (c) the user's correction flows
  through the **existing `footprintM2` confirmed path** (value-bearing, unchanged). Non-rectangular plots show the
  coverage-cap with a softer "تقديري من حدّ التغطية" label (no W×D claim).

## 5. Framing decisions for Anas (Gate-2 — light, this sprint is value-invariant)

| # | Decision | Recommendation (الأصوب) |
|---|---|---|
| **F-1** | Computation | **Setback-envelope from plot dims, bounded by the 60% coverage cap** (the §2 formula) — uses dims+setbacks (Anas's idea), orientation-free outcome, cov-cap fallback for non-rect. *(vs plain coverage-cap = simpler but ignores dims/setbacks ≈ what b1 already does.)* |
| **F-2** | Value scope | **D1 — display/confirm only; the headline math frozen at b9** (4 anchors + floors-only byte-identical). The auto-footprint→headline wiring is the **§20.9 Gate-2**, not here. |
| **F-3** | Setbacks | **Legal R1 front 5 / side 3 / rear 3, coverage 60%** (E15 corrected this session). The auto number is the **legal MAX**; the user corrects DOWN to actual. |
| **F-4** | Copy | **«الحدّ الأقصى المسموح للبناء — عدّله لواقع مبناك»** (never «مساحة بنائك»). |

## 6. Build outline (next unit, on «go» + F-1..F-4 signed)

1. `qatar_gis` (or a small helper in `evaluate_unified`): `_geometry_footprint(plot)` → `{plot_dims_m:[W,D],
   max_buildable_footprint_m2, basis:'setback_envelope'|'coverage_cap'}` from `polygon_2932` edge-pairing +
   `is_rectangular` gate + the §2 formula. Pure, no new GIS (reuses the already-fetched plot polygon).
2. `evaluate_unified` `_build_unified_output`: add the fields to `valuation.geometry` (additive); **do NOT touch
   `_suggested_fp`/`_eff_fp`/substantiality** (D1).
3. `index.html`: floors-first→area-confirm reflow on `#refineScreen` + the dims/max-buildable display + the §4 copy;
   correction → the existing `footprintM2` path.
4. Verify: isolated test (edge-pairing, non-rect fallback, the formula, **value never touches `amount`**); DoD
   392/15/45/broad; local E2E **4 anchors byte-identical + a floors-only case byte-identical** + 54/541/6 →
   max-buildable ≈ 311 (dims 35.0×17.5 shown); R14 real-Chromium (floors→area flow, 390×844 no overflow).
5. Gate-1 push on «go» + browser-UA curl smoke (#61).
