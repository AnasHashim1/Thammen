# CHANGELOG v191 — Sprint 2.22.0b.110 «ضبط مؤشّر اتّجاه الأسعار على مبيعات الفلل الصافية» (S5 — the trend pool)

**Engine:** `thammen-sprint2p22p0b110-trend-pure-villa-land` · **SPRINT_TAG** `2.22.0b.110`
**Date:** 2026-07-06 · **Files:** `moj_reference.py` (compute_trend), `moj_db.py` (query_trend twin), `evaluate_unified.py` (the 2 version lines) (+ `test_sprint_2_22_0b110.py`)
**Class:** 🟢 ENGINE display-only / VALUE-INVARIANT — the area-trend is presentation (label + yearly medians);
it NEVER feeds amount/range/method. `api.py` + `index.html` untouched → R14 N/A by construction. The 5-fixture
villa byte-gate holds (trend is not consumed by the value).

---

## 2. Why (fact #4 — the trend panel could contradict the value's pool)

`compute_trend`'s villa category used the legacy `categorize()` → included **'dwelling'** (بيت/مسكن → HOUSE,
which the a12/`built_type` villa COMP pool excludes), and the land category was **type-only** (mixing the
non-residential land the b102/S4 comp pool now excludes). So the user-visible AREA-TREND panel was computed on
a different, broader pool than the value — a villa trend could include houses, a land trend could include
apartment-development/commercial land. An a12 leftover, display-only (evaluate_unified reads the trend only for
the panel; it never feeds the amount).

## 3. What this patch does

**Live `moj_reference.compute_trend`:** both trend categories switch to the SAME pure filter as
`build_reference` — `_bt_matches(r, 'villa'/'land') and _is_residential_usage(r)` (built_type
STANDALONE_VILLA/LAND + residential usage) — replacing `categorize(r) in ('villa','dwelling')` (villa) and
`categorize(r)=='land'` (land). Now the trend pool == the comp pool.

**#39 deviation flag (the plan named the villa category only):** S4 (just built) made the LAND comp pool
residential-only; leaving the LAND trend unfiltered would create the **exact same panel↔pool contradiction**
S5 fixes for villa (a land trend including non-residential land beside a residential-only land value). So S5
aligns BOTH categories — same value-invariant class, closes the sibling S4 introduces. Nothing lost.

**Twin `moj_db.query_trend` (b65 parity):** the CLI-demo twin (imported by api.py but never called on any live
path — the live trend is `compute_trend`) now, for villa/land, SELECTs `property_type + usage` and post-filters
with the same shared `built_type.matches_category` + `usage_filter._is_residential_usage`, instead of the
coarse DB `category` label (which lumped فيلتان/بيت into 'villa' and was usage-blind). True parity with the live
path.

## 4. VALUE-INVARIANT

The trend is a display panel only — the amount/range/method never read it. Trend labels/figures MAY change
(that is the point — they now match the pool). Measured: المعمورة 56 villa trend pool 168 → 123 rows (dwelling
+ non-residential dropped); the pure pool ⊆ the legacy pool (only ever removes). No amount/range/method change.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b110.py` **12/12** (E14, real compute_trend + query_trend on moj_weekly.csv:
  villa pool 168→123 pure · pure ⊆ legacy · valid trend on the pure pool · source villa+land both pure ·
  legacy villa+dwelling gone · **twin parity** [query_trend(villa) label == compute_trend(villa) label] · twin
  نجمة land 100%-non-res → None · twin land works · twin uses the shared filters · value-invariance) ·
  py_compile OK.
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **165/165
  ALL GREEN** — **ZERO re-points** (test_moj's trend tests are structural/label-valid, not count-pinned).
- **R14 N/A** — `index.html` + `api.py` git-confirmed untouched (§20.18 backend-only precedent).
- Villa 5-fixture byte-gate: byte-identical (the trend never feeds the value).
- **Personas:** lawyer APPROVE (the trend panel now matches the value's pool — removes an inconsistency; no
  compliance impact) · linguist N/A (no copy change — the existing ارتفاع/انخفاض/استقرار/متذبذب labels).

## 6. Deployment

- `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112).
- **NOT yet deployed** — local build (PO: «أكمل البناء محلياً»).

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.110`.
- the 5-fixture villa byte-gate byte-identical to v275 (browser-UA #61) — the trend is display-only.
- a villa in a mixed area → the area-trend panel is now computed on the same pure-villa pool as the value.

## 8. What's NOT in this patch

- No value/method/rule change (trend is display-only). The condition modal (the number adapts to condition) =
  **S7 (b111)**, Gate-2, signed brief first — the closing sprint.
