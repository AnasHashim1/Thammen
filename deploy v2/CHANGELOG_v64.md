# CHANGELOG v64 — Sprint 2.22.0a.12 — Built-type stratification of the villa comparable pool (A2)

**Engine:** `thammen-sprint2p22p0a12-builttype-stratification` · **api/health:** `3.1.0-sprint2.22.0a.12`
**Date:** 2026-05-31 · **Type:** methodology (villa comparable-pool construction) — Gate 2, signed.
**Files changed:**
- `built_type.py` — **NEW** shared built-type classifier (`built_type` + `matches_category`).
- `moj_reference.py` — bracket-path villa/land selector now uses `built_type` (composes with A1 usage).
- `geo_reference_v2.py` — geo/widened-path villa/land selector now uses `built_type`.
- `evaluate_unified.py` — `ENGINE_VERSION` / `SPRINT_TAG` → a12.
- `test_sprint_2p22p0a12_builttype.py` — **NEW** isolated test (28 cases).
- `CHANGELOG_v64.md` — this file.

---

## 1. Why this matters
Phase-1 validated **LAND < HOUSE < STANDALONE_VILLA** as distinct price levels (10/10 districts). But the
two live comp selectors stratified **inconsistently** and **both contaminated the villa pool with cheaper
house rows** (and فيلتان / compound leakage):
- bracket (`moj_reference.categorize`): `بيت`→villa, `مسكن`→dwelling (split), `فيلا/فيلتان`→villa.
- geo (`geo_reference_v2._categorize`): `فيلا/فيلتان/بيت/مسكن`→villa (all lumped).

A villa subject's comp pool therefore carried house rows (median **350** QAR/ft²) dragging the villa median
down. A1 removed *usage* contamination; **A2 removes *built-type* contamination** and reconciles the `مسكن`
split.

## 2. What this patch does
New shared `built_type(row)` → `'LAND' | 'HOUSE' | 'STANDALONE_VILLA' | None`, applied at **both** comp
selectors (villa→STANDALONE_VILLA pool, land→LAND), **composing with A1's residential-usage filter** (a row
must pass BOTH). LOCKED decisions (recon + multi-AI):
1. **فيلتان / فيلتين → None (EXCLUDE)** — measured −6 to −10% discount vs single villa (distinct product).
2. **بنت هاوس → STANDALONE_VILLA (FOLD)** — villa-range (+18% over villa; far from apartment ~827/ft²).
3. **مجمع / فلل / count-words → None (EXCLUDE)** — compound, LABEL-based (E20's 15K-m² area boundary
   stays SUBJECT-side in `qatar_gis`, untouched — it never filtered comp rows).
4. **بيت / مسكن → HOUSE** — removed from the villa pool (resolves the `مسكن` split across both selectors).
5. **Subject-side classification UNCHANGED** (`qatar_gis` subtype mapping untouched). A house *subject* still
   classifies `standalone_villa` (QARS subtype 1 = "Villa/House" — house and villa share one code).
   ⟹ **A2 is comp-side stratification only; house-SUBJECT pooling defers to B (2.22.0b).**

**Scope guards (Rule #39):** `categorize`/`_categorize` are NOT deleted — they still serve `compute_trend`
(trend chart, out of A2 scope) and the geo non-villa/land categories (palace/compound). Only the two
**villa/land comp-gathering** sites switched to `built_type`. No window-fallback / shrinkage added here
(§5b measured first; any enhancement is a separate measured follow-up).

## 3. Verification — empirical evidence (local, read-only)
- **Isolated** `test_sprint_2p22p0a12_builttype.py`: **28/28** (every branch + NBSP variants + فيلتان-excluded
  + penthouse-folded + compound/count-word/palace/apartment excluded + `matches_category` mapping).
- **DoD regression (PYTHONIOENCODING=utf-8):** aggregator **392/392** · security **15/15** ·
  surface-honesty **45/45** · broad **55/55 files** — all green.
- **5a — pooled villa-median shift (A1→A2, residential-usage):** FULL **+9.73%** (401→440 ft², n 9638→5643),
  24mo **+11.56%** (424→473). Direction = **UP, confirms H1** (removed 3995 rows / 41.5% of the A1 pool:
  3405 HOUSE + 590 فيلتان/compound; removed median **350** vs kept **440**). Per bracket FULL: 0-400 +7.3%,
  400-600 +2.0%, 600-900 +14.9%, 900-1500 +13.8%, 1500+ +3.9%. **This is a LARGE methodology move** — the
  villa median is now a *pure-villa* median; it more than offsets A1's −4.75% (different contamination: A1
  removed pricier non-residential → down; A2 removes cheaper house → up).
- **5c — reference PINs end-to-end (before/after, real engine):**
  - **56/565/21 Abu Hamour:** 2,400,000 → **2,400,000 (unchanged)**. Bracket path; the 400-600 **total-price
    median = 2,350,000 in BOTH** (the 6 removed house rows weren't at the median position) → robust headline,
    no move. (ppm2 did rise 5180→5289.)
  - **54/541/6 Marikh:** 4,500,000 → **4,500,000 (unchanged)**. Widened path; total-median stable.
  - **52/903/90, 69/255/75, 69/329/20:** apartment/hybrid → None, unchanged (orthogonal).
  - **NOTE / Rule #36:** the brief expected these to move UP; measured, they don't — the *pooled* median
    moves strongly (+9.7%) but these two specific PINs sit on robust total-price medians the house rows
    didn't occupy. No unexplained reversal; H4 holds (no move ≠ wrong direction).
- **5b — thin-cell behavior (existing mechanisms, A1→A2), villa area×bracket:**
  stratification thins cells (expected — the pool shrinks 41.5%). Via engine thresholds (24mo, MIN_N=20 →
  36mo fallback): reliable(≥20) **20%→12%**, insufficient(<5) **48%→56%**; cells resolved only at 36mo
  7%→4%; a10 dispersion-gate share among n≥4 24mo cells 37%→39%. **Verdict in §5 below.**
- **Mobile 390×844 / index.html:** no UI change — pooling change only; card renders unchanged.

## 4. Deployment (Windows cmd — one command per line, subtree push per Operational #43)
```
cd /d "C:\Thammen\deploy v2"
git add built_type.py moj_reference.py geo_reference_v2.py evaluate_unified.py CHANGELOG_v64.md test_sprint_2p22p0a12_builttype.py
git commit -m "Sprint 2.22.0a.12: built-type stratification of the villa comparable pool (A2)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 5. Post-deploy verification (curl)
```
curl -s https://thammen.qa/api/health
:: expect engine_version thammen-sprint2p22p0a12-builttype-stratification + version 3.1.0-sprint2.22.0a.12
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"
```
Smoke 3+ from Heroku incl. the reference PINs **+ a house-type subject** + tier/n check (#52).

## 6. What's NOT in this patch
- **Subject-side house identification** → B (2.22.0b condition axis) — house subjects still pool as villa.
- **Within-type condition / finish / age** adjustment → B.
- **Window-fallback enhancement (cap 36mo) / shrinkage** → measured here (§5b); decided as a follow-up.
- **`compute_trend`** villa selection (trend chart) — unchanged (still `categorize`).
- **Land-usage filter** (A1 did villa-usage) — deferred.
