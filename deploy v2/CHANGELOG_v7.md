# CHANGELOG — Sprint 2.4a: Methodology Fixes

**Engine version:** `thammen-sprint2p4a-methodology-fixes`
**Date:** 2026-05-13
**Files changed:** `evaluate_unified.py`, `evaluate_property.py`
**Builds on:** Sprint 2.3 (age-aware)

---

## Bugs this patch closes

### Bug #1 — Cost approach was ignoring user-provided building age
`evaluate_unified.py` called `evaluate_property()` WITHOUT passing
`building_age_years` even when the user provided it. Result: cost approach
always computed depreciation = 0% (treating every villa as brand new).
This inflated cost-based valuations for any property older than ~5 years.

**Concrete impact:** A 30-year-old villa in Luqta was reported with
`cost_approach.depreciation_pct: None` and `building_value_new: None`
despite the user explicitly providing `building_age_years: 30`. The
construction cost was fully recognised, no MEP/structural depreciation
applied → cost approach reported 3.34M instead of the realistic ~1.5M.

### Bug #2 — Brief used inflated cost-weighted synthesis as anchor
The brief's `negotiation` (buyer), `valuation` (seller), and `pricing`
(seller) sections were anchored on `blended.blended_value` — the
MoJ × Cost weighted synthesis. When cost approach was inflated (Bug #1)
AND given heavy weight (80% in high-BUA cases), this produced a brief
that contradicted the headline number.

**Concrete impact (Luqta 467m², seller asking 2M, MoJ says 2M):**
- `valuation.amount`: insufficient_data (silent)
- `brief.valuation_total`: 3,070,866 ← LIES to user
- `negotiation.opening`: 2,763,779 ← would lose the buyer/seller money
- The brief told the buyer to open at 2.76M for a property the seller
  was happy to sell at 2.0M.

### Bug #3 — `valuation.amount` and `brief.valuation_total` diverged
The brief was finalised in `_build_unified_output` BEFORE
substantiality (Sprint 2.2) and age-multiplier (Sprint 2.3)
adjustments ran on the unified output. Result: when those adjustments
moved the headline (e.g. +20% for big BUA), the brief still showed the
pre-adjustment number.

### Bug #4 — Cost approach output fields silently null due to field-name mismatch
`evaluate_unified.py` was reading `depreciation_rate_pct` and
`building_value_depreciated` from the `ReplacementCostValuation`
dataclass, but the actual field names are `depreciation_pct` and
`depreciated_building_value`. Silent miss → `None` → users never saw
the depreciation breakdown even when it was computed correctly.

### Bug #5 — Very thin MoJ samples (n=3-4) returned "insufficient_data"
The threshold was `MIN_N_BOUND_ONLY = 5`. For sparse areas like Luqta
(n=4 for the 400-600m² bracket over 24 months), the system refused to
produce ANY headline value, while the brief downstream still computed
inflated cost-based numbers. Two contradictory messages to the user.

---

## What this patch does

### 1. Pass building inputs into v2 baseline (`evaluate_unified.py`)

```python
ev = evaluate_property(
    ...
    building_age_years=building_age_years,    # NEW
    construction_tier='high' if is_luxury     # NEW
                      else 'mid',
    has_renovation=has_reno,
    full_renovation=full_reno,
    ...
)
```

Cost approach now applies the depreciation curve (1.5%/yr <10y,
2%/yr 10-20y, 3%/yr 20-30y, 2%/yr 30+y, capped at 80%), with
renovation recovery netted off.

### 2. Market-signal override in blended weighting (`evaluate_property.py`)

When `listing_price` is within ±10% of MoJ direct value, force MoJ to
80% weight regardless of BUA ratio. The market is confirming MoJ is
accurate for THIS property — don't override it with a generic
"high BUA → trust cost more" heuristic.

```python
if listing_price and moj_total:
    listing_vs_moj = abs(listing_price - moj_total) / moj_total
    if listing_vs_moj <= 0.10:
        moj_w, repl_w = 0.80, 0.20
        reason = 'Market signal override: listing matches MoJ within 10%...'
```

### 3. Final brief sync (`evaluate_unified.py`)

After substantiality + age-multiplier adjustments run, re-sync the
brief headline AND audience-specific anchor sections from the FINAL
`output.valuation.amount`. Adds new helper:

```python
def _rewrite_brief_anchored_sections(brief, final_amount, final_low,
                                      final_high, audience, moj_direct):
    # Rewrites buyer 'negotiation', seller 'valuation', seller 'pricing'
    # using final_amount × {0.90, 0.95, 1.05, 1.10, 1.20} multipliers.
```

### 4. Fix cost approach field name mapping (`evaluate_unified.py`)

`_build_cost_crosscheck` now reads the correct dataclass field names
with legacy fallback:

```python
dep_pct_val = (getattr(rc, 'depreciation_pct', None)
               or getattr(rc, 'depreciation_rate_pct', None))
```

### 5. Preliminary estimate for very thin brackets (`evaluate_unified.py`)

Added Case 5 in `_select_primary_comparison`: when bracket_n ∈ [3, 4]
and yields a sensible median, return a `comparison_preliminary`
verdict with explicit caveat instead of returning None.

```python
if bracket_value and bracket_n >= 3:
    return {
        'value': bracket_value,
        'method': 'comparison_preliminary',
        'method_label_ar': f'تقدير مبدئي (n={bracket_n})',
        'source_ar': f'عينة محدودة جداً (n={bracket_n}...)',
    }
```

---

## Concrete impact

### Luqta 52/903/90 (467m², 30yo NOT luxury, seller asks 2M)

| Field | Before | After |
|---|---|---|
| valuation.amount | null | **1,900,000** ✓ |
| valuation.method | insufficient_data | comparison_preliminary |
| cost_approach.depreciation_pct | null | **0.65** (65% applied) |
| cost_approach.building_value_new | null | 1,277,158 |
| cost_approach.building_value_depreciated | null | 957,869 |
| cost_approach.total_replacement | 3,336,783 | 3,017,494 |
| brief.valuation_total | 3,070,866 (lies) | **1,900,000** ✓ |
| negotiation.opening | 2,763,779 (+38%) | **1,700,000** (-15%) ✓ |
| negotiation.ceiling | 3,377,953 (+69%) | 2,100,000 (+5%) ✓ |
| verdict ↔ negotiation consistency | broken | aligned ✓ |

### Bou Hamour 56/565/21 (900m² + BUA, 30yo NOT luxury)

| Field | Before | After |
|---|---|---|
| valuation.amount | 4,100,000 | 4,000,000* |
| brief.valuation_total | 4,100,000 | **4,000,000** ✓ |
| 10-Year Rule | applied (Sprint 2.3) | applied + cost now respects age |
| cost_approach.depreciation_pct | null | **0.65** |
| cost_approach.total | 7,316,521 | 6,399,941 (more realistic) |

*Slightly lower than Sprint 2.3 (4.1M) because cost approach now passes
correct depreciation through the v2 blended logic, which marginally
adjusted the bracket reference.

---

## Test verifications (local end-to-end before deploy)

```
Test 1 — Luqta old non-lux asking 2M:
  valuation.amount: 1900000  brief.total: 1900000  ✓ match
  negotiation: floor=1800000 open=1700000 ceil=2100000

Test 2 — Bou Hamour 30yo NOT lux:
  valuation.amount: 4000000  brief.total: 4000000  ✓ match
  negotiation: floor=3800000 open=3600000 ceil=4400000

Test 3 — Bou Hamour NEW 5yo lux:
  valuation.amount: 4900000  brief.total: 4900000  ✓ match
  negotiation: floor=4700000 open=4400000 ceil=5400000

Test 4 — Marikh no details:
  valuation.amount: 4500000  brief.total: 4500000  ✓ match
  negotiation: floor=4300000 open=4000000 ceil=5000000
```

---

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak3 && copy /Y evaluate_property.py evaluate_property.py.bak3
tar -xf "%USERPROFILE%\Downloads\sprint2p4a-methodology-fixes.zip"
findstr /C:"sprint2p4a-methodology-fixes" evaluate_unified.py
git add evaluate_unified.py evaluate_property.py CHANGELOG_v7.md
git commit -m "Sprint 2.4a: methodology fixes (cost age, brief sync, thin n threshold)"
git push heroku master
curl -s https://thammen.qa/api/health
```

## Verification curl after deploy

**Luqta — should now return ~1.9M not insufficient_data:**
```bash
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":52,"street":903,"building":90,"audience":"buyer",
       "floors":2,"condition":"renovated","building_age_years":30,
       "is_luxury":false,"asking_price":2000000}'
```

Expected:
- `valuation.amount: 1900000`
- `valuation.method: "comparison_preliminary"`
- `cost_approach.depreciation_rate_pct: 0.65`
- `brief.valuation_total: 1900000`
- `brief.sections[negotiation].content.opening_offer: 1700000`

---

## What's NOT in this patch (deliberate — Sprint 2.4b)

- Investor brief proper analysis (cap rate per property, yield scenarios)
- Valuator audience bug (returns buyer content)
- Trend slope_annual_pct format (decimal vs percent)
- Frontend display updates for new comparison_preliminary method
