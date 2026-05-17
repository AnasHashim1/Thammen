# CHANGELOG — Sprint 2.16.0: Stock Stratification (EMPIRICAL_FINDINGS Rule E4)

**Engine version:** `thammen-sprint2p16p0-stock-stratification`
**SPRINT_TAG:** `2.16.0` → /api/health reports `3.1.0-sprint2.16.0`
**Date:** 2026-05-17
**Files added:** `stock_strata.py`, `test_stock_strata.py`
**Files updated:** `evaluate_unified.py`, `index.html`
**Builds on:** Sprint 2.15.1 (cache-only imagery) + EMPIRICAL_FINDINGS 2026-05-13

---

## Why this matters (empirical evidence first)

This Sprint addresses a methodology gap that **systematically under-values modern
and luxury villas by 30-40%**. The gap was diagnosed empirically against three
real sale prices on 2026-05-17:

| Property | thammen (pre-2.16) | Confirmed sale | Error |
|---|---|---|---|
| 56/565/10 — J Seven Bou Hamour A | 2,500,000 | 4,000,000 | **−37.5%** |
| 56/565/12 — J Seven Bou Hamour B | 2,400,000 | 4,000,000 | **−40.0%** |
| 51/955/49 — Al-Gharafa modern villa (PIN 51708152) | 3,100,000 | 4,450,000 | **−30.3%** |

Monotonic, consistent magnitude, three areas. Not noise — methodology bias.

**Why the bias exists.** Pre-2.16, thammen computed a single bracket median
(e.g. "Bou Hamour 400-600 m², n=29, median 5,201 QAR/m²") and treated it as
representative for any villa in that bracket. But the bracket contains a mix
of stock classes — old buildings sold for land value (10-Year Rule),
mature buildings, modern resale, luxury new — and the median is dominated
by the most-frequent class (aging stock). Modern and luxury properties were
priced against the aging-dominant median.

This is precisely the failure mode EMPIRICAL_FINDINGS Rule E4 (2026-05-13)
diagnosed in advance:

> Villa MoJ medians within a single bracket are **blended** (mix of new +
> aging + old buildings). Never reference a bracket median without classifying
> stock first. (EMPIRICAL_FINDINGS §4 Rule E4)

The 2026-05-17 probes confirmed the diagnosis with live sales data.

---

## Root cause

**File:** `evaluate_unified.py` (and the helpers it calls)
**Issue:** `valuation.amount` is computed from `primary['value']` which is the
median of `geo_v2_result['primary']['transactions']` — a single number with
no stratification. Per-stratum information is never computed and never
surfaced to the user.

**File:** `evaluate_v3.py:415` does call `comparable_adjustments.py` but its
output is discarded by `evaluate_unified.py:2391` (`"blend_3way is ignored"`).
And even if it were used, `comparable_adjustments` adjusts for
time/size/location — not for stock class.

---

## What this patch does

Three layers of change, all backward-compatible:

### 1. New module — `stock_strata.py` (NEW, ~280 lines)

Pure-Python classification module. For each villa transaction in an area:

```python
ratio = villa.price_per_m2 / land_median_per_m2_same_area_same_bracket

ratio  <  1.15  → land_priced     # Qatar 10-Year-Rule territory
1.15 ≤ ratio < 1.50 → aging_stock   # mature buildings, 10+ years
1.50 ≤ ratio < 2.20 → modern_stock  # 2-10 years, good finish
ratio  ≥  2.20  → luxury_new      # luxury / brand-new construction
```

Thresholds source: EMPIRICAL_FINDINGS 2026-05-13 (paired audit, 5 areas × 4
brackets, n=149+ MoJ + n=18 asking).

Per Rule E4, the land reference is **bracket-matched** to the villa plot
size (smaller plots have higher per-m² land prices, so an unbracketed
reference would systematically over-classify large-plot villas as
`luxury_new` and under-classify small-plot villas as `land_priced`).

Public API:
```python
build_stock_strata_result(moj_rows, moj_area_names, villa_transactions,
                          plot_area_m2, listing_price, date_col)
    → dict | None
```

### 2. Pipeline wiring — `evaluate_unified.py` (~30 lines)

After Step 3 (primary value selection) and before Step 4 (v3 layer), the
engine now computes the stratification for villa-type assets:

```python
# Step 3.5 (Sprint 2.16.0): Stock Stratification
stock_strata = None
if _STRATA_OK and ev.asset_type in ('standalone_villa', 'villa'):
    villa_txns = geo_v2_result['primary']['transactions']
    moj_names  = set(geo_v2_result['primary']['moj_names'])
    stock_strata = build_stock_strata_result(
        moj_rows=_get_moj_rows(moj_csv_path),
        moj_area_names=moj_names,
        villa_transactions=villa_txns,
        plot_area_m2=ev.plot_area_m2,
        listing_price=listing_price,
        date_col=date_col,
    )
```

Output is attached to the response right before `reconciliation`:
```python
if stock_strata:
    output['stock_strata'] = stock_strata
```

**No new network calls.** Reuses the cached MoJ rows (`_MOJ_CACHE`). Pure
in-memory compute. Expected overhead: <100 ms.

### 3. Frontend rendering — `index.html` (~90 lines)

A new card under "Location features" / before "Known unknowns":
- Land reference (median/n/window/bracket)
- Subject property classification (when `listing_price` was provided)
- 4 strata as color-coded cards with reliability flags (n≥10 = reliable,
  n=3-9 = indicative, n<3 = empty)
- Dominant-stratum note
- Sprint scope caveat (italic): "Sprint 2.16.0 is exposure-only, headline
  value unchanged"

Color scheme uses existing CSS variables only — no hardcoded colors:
- `land_priced` → `var(--warn-bg)` (risk of value=land)
- `aging_stock` → `var(--alt)` (neutral)
- `modern_stock` → `var(--ok-bg)` (positive)
- `luxury_new` → `var(--bronze)` (premium)

---

## Verification — empirical evidence

Tested locally against the same three confirmed sales (`test_stock_strata.py`):

### Al-Gharafa 51708152 (600m², actual sale 4,450,000)

```
Land ref: 3,355 QAR/m²  n=95  bracket=600-900  bracket_match=True
Subject:  ratio=2.21  → luxury_new

  land_priced    n=13  med= 3,425/m²  total=2,055,000  vs sale: -53.8%
  aging_stock    n=11  med= 4,178/m²  total=2,506,800  vs sale: -43.7%
  modern_stock   n=16  med= 6,180/m²  total=3,708,000  vs sale: -16.7%
  luxury_new     n= 8  med= 7,744/m²  total=4,646,400  vs sale: +4.4%  ← subject
```

**Improvement:** −30.3% → **+4.4%**. Within RICS buyer-ceiling (±10%).

### J Seven Bou Hamour A/B (450m², actual sale ~4,000,000)

```
Land ref: 3,875 QAR/m²  n=20  bracket=400-600  bracket_match=True
Subject:  ratio=2.29  → luxury_new

  land_priced    n= 7  med= 4,319/m²  total=1,943,550  vs sale: -51.4%
  aging_stock    n=20  med= 5,201/m²  total=2,340,450  vs sale: -41.5%
  modern_stock   n= 7  med= 6,106/m²  total=2,747,700  vs sale: -31.3%
  luxury_new     n= 1  med=15,794/m²  total=7,107,300  vs sale: +77.7%  ← subject
                       (reliability_label: "إرشادي (n=1)")
```

**Status:** The system correctly classifies J Seven as `luxury_new` AND
correctly flags the `luxury_new` cluster as having n=1 (insufficient sample,
labeled "إرشادي"). The user is told: "your property is luxury_new, but we
have only 1 prior transaction in this area — out-of-distribution warning."

This is the right answer. J Seven is the FIRST luxury project of its kind in
Bou Hamour; their April 2026 sales are creating a new price tier. MoJ data
ends 2025-12-31. **Stratification cannot conjure data that doesn't exist** —
but it can honestly say so, instead of confidently reporting 2.5M.

Resolving J Seven-like cases fully requires Sprint 2.16.1+ (confirmed_sales DB).

### Test suite

```
$ python test_stock_strata.py

Classifier:
  ✓ thresholds match Rule E4
Partitioning:
  ✓ compute_strata partitions correctly
  ✓ band labels are formatted as expected
Subject classification:
  ✓ subject ratio computation + classification
Edge cases:
  ✓ empty / invalid inputs return gracefully
Integration:
  ✓ Al-Gharafa probe reproduces within 15%

6/6 tests passed.
```

### Backtest harness expected behavior

Running `backtest/backtest.py` post-deploy should:
- Show same predictions on canonical 6 (Sprint 2.16.0 is exposure-only)
- Show new `stock_strata` field in JSON for the 3 villa rows
- Latency unchanged (no new network calls)

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p15p1
copy /Y index.html index.html.bak_2p15p1
tar -xf "%USERPROFILE%\Downloads\sprint2p16p0-stock-stratification.zip"
findstr /C:"sprint2p16p0" evaluate_unified.py
python test_stock_strata.py
git add stock_strata.py test_stock_strata.py evaluate_unified.py index.html CHANGELOG_v22.md
git commit -m "Sprint 2.16.0: Stock Stratification (EMPIRICAL_FINDINGS Rule E4)"
git push heroku master
```

After the push, wait ~60 seconds for the dyno to restart, then verify:

```
curl https://thammen.qa/api/health
```

Should report `"version": "3.1.0-sprint2.16.0"` and
`"engine_version": "thammen-sprint2p16p0-stock-stratification"`.

---

## Verification curl

Post-deploy probe of the Al-Gharafa case (should now show the new field):

```
curl -X POST https://thammen.qa/api/evaluate/details ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":51,\"street\":955,\"building\":49,\"audience\":\"buyer\",\"listing_price\":4450000}"
```

Expected: response JSON now contains a `stock_strata` field with `applied:true`,
`land_reference.bracket_match:true`, and the subject classified into a stratum.
The headline `valuation.amount` remains 3,100,000 (unchanged — exposure-only).

---

## What is NOT in this patch (Sprint 2.16.0 scope boundary)

This Sprint is **exposure-only**. Out of scope:

1. **Headline value adjustment.** `valuation.amount` is unchanged. The
   median-based primary continues to be the rounded headline. Sprint 2.16.1+
   will consider letting user inputs (age, finish, view) drive the headline
   to the appropriate stratum.

2. **Apartment stratification.** Rule E4 uses villa/land ratio, which has no
   analogue for apartments (no separable land component). Apartments need
   a different classifier (view, floor, building age, amenities). Sprint 2.29
   (MME integration) will start that work.

3. **Confirmed-sales database.** For new-tier projects like J Seven where
   MoJ has no comparable transactions, stratification can only flag the gap,
   not fill it. Filling requires Sprint 2.16.1+ (confirmed_sales DB seeded
   from the secretary's templates).

4. **Cost calibration cross-check.** `calibrate_construction_cost.py` and
   `construction_costs.json` exist locally but remain wired only to the v2
   fallback engine. Sprint 2.17 candidate.

5. **comparable_adjustments table exposure.** `comparable_adjustments.py`
   is still computed (via evaluate_v3) and still ignored. That was the
   original Sprint 2.16-A1 plan (audit 2026-05-17); it was superseded by
   stratification because the probes showed stratification has 5× higher
   impact (−36% → +4.4% vs the smaller adjustment-table effects).

6. **Engine method labels.** `valuation.method` continues to report
   `comparison_bracket` or `comparison_widened` — it does not change to
   reflect stratification. This avoids breaking downstream consumers that
   pattern-match on method names.

7. **Backtest accuracy mode.** Only n=3 confirmed sales available; MAPE on
   n=3 is statistical theatre, not measurement. Sprint will rely on the
   audit-based validation in §"Verification". Real backtest accuracy mode
   activates when the secretary's templates arrive (Thursday-ish) and n≥20.

---

## Methodology compliance

- **Section 3 (Hard rules):** median not mean ✓ ; n thresholds respected
  (`reliable: n≥10`, `indicative: 3≤n<10`, no median for n<3) ✓ ; 24-month
  window with 36-month fallback ✓ ; size brackets exact ✓.
- **Section 4 (Honesty):** stratum reliability flagged in every output ✓ ;
  J Seven `luxury_new` n=1 flagged as "إرشادي (n=1)" not as a confident
  estimate ✓ ; sprint scope caveat surfaced ✓.
- **Section 5 (UI-First audit):** completed 2026-05-17 against production
  (probes against 3 confirmed sales + analysis of bracket distribution).
  Findings: −36% systematic bias confirmed; pivot from original Sprint
  2.16-A1 plan (adjustments exposure) to Stock Stratification justified.
- **Section 7 (GIS area names):** uses `geo_v2_result['primary']['moj_names']`
  which is derived from authoritative GIS Districts layer ✓.
- **EMPIRICAL_FINDINGS Rule E4:** thresholds + bracket-matched land ✓ ;
  Rule E5 acknowledged (J Seven flagged as out-of-distribution rather than
  pretending stratification fully resolves it) ✓.

---

## Files in this patch

```
sprint2p16p0-stock-stratification.zip
├── stock_strata.py              (NEW, ~280 lines)
├── test_stock_strata.py          (NEW, ~180 lines)
├── evaluate_unified.py           (MODIFIED, +~50 lines, version bump)
├── index.html                    (MODIFIED, +~90 lines, render card)
└── CHANGELOG_v22.md              (NEW, this file)
```

---

_Last updated: 2026-05-17 — after probe validation against 3 confirmed sales._
_Audit chain: probes → distribution analysis → EMPIRICAL_FINDINGS Rule E4 → this Sprint._
