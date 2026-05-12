# CHANGELOG — Sprint 2.2: BUA-Aware Valuation (BIB Fix)

**Engine version:** `thammen-sprint2p2-bua-aware`
**Date:** 2026-05-12
**Files changed:** `evaluate_unified.py`, `api.py`, `index.html`

---

## Problem this patch solves

Live testing of `thammen.qa` exposed two methodology bugs:

### Bug #1 — Built Improvements Blindness (PRIMARY)
Thammen valued properties based on **plot area × MoJ price/m²**, with cost
approach treated as a non-weighted cross-check. The legacy
`_build_simple_bua(floors, annexes)` hardcoded:
- `main_footprint_m2 = 300` regardless of plot size
- `basement_m2 = 0` always (no basement support — even when floors ≥ 3)

**Concrete impact:** Property in بو هامور 56/565/21 (900 m² plot, basement +
2 floors + multiple annexes + renovated; court valued at 6.5M in 2022) was
valued by Thammen at 4.1M (May 2026) — a -37% drift over 4 years that's
economically impossible in a stable-to-rising market.

### Bug #2 — Benchmark Inconsistency
`market_position` (buyer verdict) used `comparison.benchmark_total` (=
MoJ direct n=1 × GIS factors), but the unified valuation reported the
WIDENED estimate as `valuation.amount`. When a user entered listing =
Thammen's own valuation, the verdict said "50% above market reference"
— comparing the headline value to a different (often outdated) benchmark.

---

## What's fixed

### 1. Smart BUA builder (`evaluate_unified.py`)
- `_typical_footprint(plot_area)` scales with plot size:
  - <350 m² → 60% coverage
  - 350-800 m² → 55% coverage
  - >800 m² → 45% coverage
- `_typical_bua_for_plot(plot_area)` = ground + 1 upper floor
  (the Qatar R1 norm; basement / extra floors are extras above this)
- `_build_smart_bua(plot_area, floors, annexes, basement, footprint_m2, external_majlis)`
  replaces the fixed-300m² assumption. Handles user-provided footprint,
  explicit basement, external majlis.

### 2. Building substantiality adjustment
- `_building_substantiality(bua, plot)` computes index = actual_BUA /
  typical_BUA and returns a tiered upward adjustment:

  | Index | Adjustment | Example |
  |-------|------------|---------|
  | ≥ 2.00 | +25% | Large basement + 3+ floors + annexes |
  | ≥ 1.70 | +20% | Basement + 2 floors + 2 annexes + external |
  | ≥ 1.45 | +15% | Notably above typical |
  | ≥ 1.25 | +10% | Moderately above typical |
  | ≥ 1.10 | +5% | Slightly above |
  | 0.85-1.10 | 0% | Typical (no change) |

  - Applied **only upward** in unified pipeline (conservative)
  - Adjustment cascade order: comparison → HBU → substantiality → MU
  - Range expands asymmetrically (high boundary +10% extra, low only 70%)

### 3. Benchmark consistency fix
After `_build_unified_output` finalizes `valuation.amount`, the unified
pipeline now rebuilds `market_position` with the actual valuation as
the benchmark. So when a user enters listing = Thammen's valuation,
the verdict correctly says "at market".

### 4. Material Uncertainty enrichment
When user provides NO building details (`bua_breakdown is None`):
- New MU factor: "تفاصيل البناء غير مُقدَّمة — قد تختلف ±20-40%"
- New known_unknown: "مكوّنات البناء الفعلية (سرداب، طوابق، مجلس خارجي…)"
- New recommendation: "أدخل تفاصيل العقار للحصول على تقييم أدق"

### 5. Frontend (`index.html`)
- **NEW:** "سرداب (تحت الأرض)" yes/no selector
- **NEW:** "مجلس خارجي منفصل" yes/no selector
- **NEW:** "تقدير مساحة البناء الأرضي (م²)" optional override
- **RELABELED:** "عدد الطوابق" → "عدد الطوابق فوق الأرض" with clearer options
  ("طابق واحد (أرضي)", "طابقين (أرضي + أول)", etc.)
- **NEW DISPLAY:** "🏗️ تعديل البناء" card shows when substantiality adjustment > 0
  (rationale, typical vs actual BUA, methodology note)
- **NEW WARNING:** When no building details entered, banner reads
  "ℹ️ التقييم يفترض بناءً نموذجياً" with explanation

### 6. API (`api.py`)
- `EvaluateDetailsRequest` accepts:
  - `basement: Optional[bool]`
  - `footprint_m2: Optional[float]`
  - `external_majlis: Optional[bool]`
- All three are forwarded to `evaluate_thammen()` with explicit kwargs.

---

## Backward compatibility

- **`_build_simple_bua(floors, annexes)`** retained as deprecated shim
  calling `_build_smart_bua` with safe defaults. CLI and any external
  callers continue to work.
- **API:** New fields default to `None` so existing clients (without the
  new fields) keep working identically.
- **Output schema:** Adds `valuation.building_substantiality` (new key)
  but doesn't change existing keys. Frontend that doesn't know about
  the new key just ignores it.

---

## Test verification (logic tests in this commit)

```
Marikh 613m² — no inputs                       (no adjustment, banner shown)
Marikh 613m² — typical (2fl, no extras)        idx=1.00, +0.0%  ✓
Marikh 613m² — 1 floor only                    idx=0.54, -12.0% (downward NOT applied)
Bou Hamour 900m² — bsmt+2fl+2anx+ext           idx=1.78, +20.0% ✓
Bou Hamour 900m² — bsmt+3fl+2anx+ext           idx=2.24, +25.0% ✓
Bou Hamour 900m² — user FP 450 + bsmt+...      idx=1.95, +20.0% ✓
Palace 1500m² — bsmt+3fl+3anx+ext+FP650        idx=2.11, +25.0% ✓
```

**Projected impact on the two real properties used in the audit:**

| Property | Before | After | Court value (2022) | Gap closed |
|----------|--------|-------|--------------------|------------|
| Marikh 54/541/6 (no extras) | 4,500,000 | 4,500,000 | — | (no change needed; matches Arady listing within 5-15%) |
| Bou Hamour 56/565/21 (bsmt+2fl+2anx+ext+reno) | 4,100,000 | 4,920,000 | 6,500,000 | 34% of remaining gap |
| Bou Hamour 56/565/21 (with footprint=500m²) | 4,100,000 | 5,125,000 | 6,500,000 | 43% |

The remaining gap to court value reflects factors not capturable by
the AVM (specific renovation quality, plot orientation, etc.) — these
are correctly left as "material uncertainty" with recommendation to
get a licensed appraiser for high-stakes decisions.

---

## Deployment

```bash
# From your Windows machine, in C:\Thammen\deploy v2\
git checkout master
git pull
# Replace the 3 changed files with the patched versions from sprint2p2-bua-aware.zip
git add evaluate_unified.py api.py index.html CHANGELOG_v5.md
git commit -m "Sprint 2.2: BUA-aware valuation + benchmark consistency

- _build_smart_bua replaces fixed-300m² assumption (plot-aware)
- Building substantiality adjustment (idx-based tiered, upward only)
- Basement / external majlis / footprint override now supported
- market_position uses valuation.amount as benchmark (not fair_price)
- Material uncertainty flags missing building details explicitly
- Engine: thammen-sprint2p2-bua-aware"
git push heroku master
```

After deploy verify with:
```bash
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":56,"street":565,"building":21,"audience":"buyer",
       "floors":2,"basement":true,"annexes":2,"external_majlis":true,
       "condition":"renovated"}'
```
Expected: `engine_version=thammen-sprint2p2-bua-aware`,
`valuation.building_substantiality.adjustment_pct > 0`,
`valuation.amount` ≈ 4.9M-5.1M (up from 4.1M).
