# CHANGELOG v91 — Sprint 2.22.0b.10 (geometric footprint)

**Engine:** `thammen-sprint2p22p0b10-geometric-footprint` · **SPRINT_TAG** `2.22.0b.10` ·
api/health `3.1.0-sprint2.22.0b.10` · **2026-06-09**
**Files:** `evaluate_unified.py` (new `_geometry_footprint` + geometry-surface fields + version bump) ·
`index.html` (fpHint hint field + populate in `show()` + results-card assumed branch) ·
`test_sprint_2_22_0b10.py` (new, 24) · `docs/PHASE0_2p22p0b10_geometric_footprint.md` (recon) · this file.
**`api.py` UNTOUCHED.** Class: **DISPLAY/CONFIRM-only — VALUE-INVARIANT** (Gate-2 framing F-1..F-4 signed by Anas).

## 1. Why this matters

Anas's idea (born from the Al Manara bank Cost-Approach report, TD 93317): instead of a flat
plot-proportional footprint guess (b1), compute the **max-buildable ground footprint from the plot's actual
dimensions − the legal R1 setbacks**, and show it for the owner to **confirm or correct DOWN** to the real
building (E17 — Thammen estimates, the user corrects). This is the foundation the **§20.9 cost-triangulation**
(the durable R7 over-anchor fix, e.g. Marikh 54/541/6 5.4M → ~2.9M) needs: it requires a BUA, and BUA = a
confirmed footprint × floors. This sprint surfaces+confirms the footprint; the value-wiring is the separate
§20.9 Gate-2.

## 2. Motivation / root cause

b1's `_suggested_footprint` is plot-proportional (`plot × 0.8 × zone_ceiling`) — it never uses the plot's
real shape. The bank report values via land + depreciated building, and the missing ingredient was the
building area. The §5 recon (`PHASE0_2p22p0b10`, live GIS, 5 plots) proved the mechanism:
- **Edge-pairing on the 4-vertex ring is EXACT** (`shoelace == pdarea` on all 5 plots); the **bbox is wrong**
  (Qatar rectangles are rotated vs the 2932 grid → bbox nearly doubles the area).
- `plot.shape.is_rectangular` (already computed in `get_plot`) is a clean gate; non-rectangular → coverage-cap.
- The **setback-envelope is often TIGHTER than the coverage cap** (binds on 2 of 3 rectangles), so it is the
  right "Anas's-idea" computation, not the flat cap.

## 3. What this patch does

**Backend (`evaluate_unified.py`) — pure, display-only:**
- New `_geometry_footprint(polygon_2932, pdarea, is_rectangular, zone_coverage)` →
  `{plot_dims_m:[W,D], max_buildable_footprint_m2, method}` or None. For a 4-vertex rectangle: edge-PAIRING
  for the dims (rotation-safe), then `min( zone_coverage×pdarea , max-over-orientations( (D−8)×(W−6) ,
  (W−8)×(D−6) ) )` — legal R1 setbacks front 5 / side 3 / rear 3 (E15 corrected), orientation-free OUTCOME
  (take the larger legal max → no street detection). Non-rectangular → orientation-free coverage cap. Reuses
  the already-fetched plot polygon → **zero new GIS**.
- The `valuation.geometry` surface gains 3 additive DISPLAY fields: `plot_dims_m`,
  `max_buildable_footprint_m2`, `footprint_method`, plus the «الحدّ الأقصى المسموح — عدّله لواقع مبناك» note.
- 🔴 **VALUE-INVARIANT (recon D1):** the geometry footprint feeds ONLY the display surface. `_suggested_fp` /
  `_eff_fp` / `_build_smart_bua` / `_building_substantiality` / `valuation.amount` are **UNTOUCHED**. The
  footprint→BUA→headline auto-wiring is the §20.9 Gate-2, NOT here.

**Frontend (`index.html`):**
- `#fpHint` helper line under the `footprintM2` field on `#refineScreen`, set-or-cleared every `show()` to the
  geometry max-buildable («💡 الحدّ الأقصى المُقدَّر من أبعاد قطعتك (35 × 17.5 م) ≈ ٣١١ م² — عدّله لواقع مبناك»).
- The results geometry card (assumed branch) shows the plot dims + max-buildable with the «max — correct it»
  framing (setback_envelope) or a softer coverage-cap line (non-rectangular), falling back to the b1 default.
- No auto-prefill of the input (keeps "assumed" honest, b2 decision); the user's correction flows through the
  EXISTING confirmed-`footprintM2` path.

## 4. Verification — empirical evidence

- **py_compile** evaluate_unified.py OK.
- **Isolated** `test_sprint_2_22_0b10.py` **24/24** (production `_geometry_footprint`, E14): rotation-safe
  edge-pairing (rotated 36×18 → dims [36.0,18.0], fp 336); 30×30 → 528; 30×35 cov-cap → 630; non-rect →
  coverage_cap dims None; 3-pt ring → coverage_cap; pdarea None/0 → None; R2 cap binds → 324; tiny plot
  env≤0 → cov_cap no-negative; **value-invariance contract** (return keys ⊆ display, no amount/value/low/high);
  ceiling ≤ coverage cap.
- **DoD:** aggregator **392** (ALL COUNTS MATCH) · security **15/15** · surface-honesty **45/45** · broad
  auto-walk **79/79** (78→79, +b10 test, clean, 225.6s, no flake).
- **Local E2E (live GIS) — ALL PASS:** 5 anchors **byte-identical** (56/565/21 2.4M · 54/541/6 5.4M ·
  55/296/13 2.6M · 52/903/90 None · 56/647/6 3.8M); geometry surface live: **54/541/6 → setback_envelope,
  dims [35.0,17.5], max_buildable 311** · 56/565/21 → 528 · 55/296/13 → 630 · **56/647/6 (V001, 5-vertex) →
  coverage_cap, dims None, 391**; **floors-only value-invariance: 56/565/21 floors=3 → 2.8M (== b9),
  building_age_years=None** (value path untouched, no age leak).
- **R14 real Chromium** (served index.html + real b10 payload, `node` absent): all 7 fns defined (whole-file
  JS parses), **0 console errors** (load + full flow); geometry card renders «قطعتك ≈ 35 × 17.5 م، والحدّ
  الأقصى المسموح للبناء ≈ ٣١١ م² … البناء الفعلي عادةً أصغر»; #fpHint populated + visible on refine; **390×844
  no horizontal overflow** (results scrollW 390, maxRight 370<390; refine scrollW 390).

## 5. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add evaluate_unified.py index.html test_sprint_2_22_0b10.py CHANGELOG_v91.md docs\PHASE0_2p22p0b10_geometric_footprint.md docs\BRIEF_geometric_footprint.md
git commit -m "Sprint 2.22.0b.10 (geometric footprint): max-buildable from plot dims - legal R1 setbacks (DISPLAY/CONFIRM only, value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy, browser-UA per #61)

```
curl -s https://thammen.qa/api/health
curl -s -X POST https://thammen.qa/api/evaluate -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36" -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"
```
Expect: health `3.1.0-sprint2.22.0b.10`; 54/541/6 → amount **5,400,000** (byte-identical) +
`valuation.geometry.max_buildable_footprint_m2` ≈ **311** + `plot_dims_m` [35.0,17.5] + `footprint_method`
`setback_envelope`.

## 7. What's NOT in this patch (scope boundary)

- **No value change** — the footprint→BUA→headline auto-wiring is the **§20.9 cost-triangulation Gate-2**
  (BUA × depreciated build rate + land → the ~2.9M durable R7 fix), a separate sprint with its own §5 audit +
  Gate-2 sign-off.
- **No street/front-edge detection** — `detect_corner.edge_evidence` could pick the front edge but costs GIS
  calls + is not robust on corners; the orientation-free coverage-cap-bounded max envelope dissolves the need.
- **5-vertex near-rectangles** (e.g. V001 56/647/6) use the coverage-cap fallback — a min-area-bounding-
  rectangle refinement could recover them later.
- **No new GIS, no `api.py` change, no DB change.**
