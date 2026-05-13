# CHANGELOG — Sprint 2.3: Qatar 10-Year Rule (Age-Aware Adjustment)

**Engine version:** `thammen-sprint2p3-age-aware`
**Date:** 2026-05-12
**Files changed:** `evaluate_unified.py`, `api.py`, `index.html`
**Builds on:** Sprint 2.2 (BUA-aware)

---

## Why this exists

Sprint 2.2 added a BUA-based "substantiality" adjustment that increased
the valuation by up to +25% for properties with basement / multiple floors /
annexes / external majlis. This was a real improvement for new big villas
but had a methodological gap: **it applied the same uplift regardless of
building age.**

The Qatar real estate market does not behave this way. Empirically observable
in MoJ data: villas older than ~10 years trade close to bare-land value
regardless of how much built-up area they contain, because the dominant
buyer behaviour is **demolish-and-rebuild rather than renovate**. This is
the "Qatar 10-Year Rule" identified in the May 2026 strategic analysis
document (section 4).

## What this patch does

Adds two new inputs to the API and form:
- `building_age_years` — estimated building age in years (optional)
- `is_luxury` — declared luxury finishing flag (optional, default False)

Then modulates the Sprint 2.2 substantiality adjustment by an
**age-aware multiplier**:

| Age | Luxury | Multiplier | Regime label |
|---|---|---|---|
| < 5 | any | 1.00 | `new_building` (full adjustment) |
| 5–10 | any | 0.85 | `mid_age_building` (mild dampening) |
| ≥ 10 | yes | 0.50 | `old_luxury_building` (partial — luxury exception) |
| ≥ 10 | no | 0.00 | `qatar_10_year_rule` (suppress — market trades at land value) |
| unknown | — | 1.00 | `unknown_age` (default + MU warning) |

## Concrete impact (Bou Hamour 56/565/21, 900m² plot, basement+2fl+2anx+ext)

| Scenario | Sprint 2.2 | Sprint 2.3 | Why |
|---|---|---|---|
| No age provided | 4,900,000 | 4,900,000 | Same (defaults to full) but MU warning |
| Age=3 (new) | 4,900,000 | 4,900,000 | New building → full uplift justified |
| Age=7 (mid) | 4,900,000 | 4,800,000 | Mild dampening (×0.85) |
| Age=25 luxury | 4,900,000 | 4,500,000 | Luxury exception (×0.50) |
| Age=25 not luxury | 4,900,000 | 4,100,000 | 10-Year Rule: suppress entirely |
| Age=35 not luxury | 4,900,000 | 4,100,000 | 10-Year Rule: suppress entirely |

For the actual Bou Hamour property (described as old inherited family villa,
externally renovated only — clearly old + non-luxury): the system now
correctly returns 4.1M as the market-behaviour valuation, with explicit
disclosure that older buildings in Qatar trade near land value.

## API changes

`EvaluateDetailsRequest` gains two optional fields:
```python
building_age_years: Optional[int] = None
is_luxury: Optional[bool] = None
```

Both default to None and are forwarded to `evaluate_thammen()`.

## Output schema additions

`valuation.building_substantiality` now contains:
- `raw_adjustment_pct` — what Sprint 2.2 would have applied
- `age_multiplier` — the multiplier from Sprint 2.3
- `adjustment_pct` — the final applied adjustment (= raw × multiplier)
- `age_regime` — one of: `new_building`, `mid_age_building`,
  `old_luxury_building`, `qatar_10_year_rule`, `unknown_age`
- `age_regime_label_ar` — Arabic label for UI
- `building_age_years`, `is_luxury` — echoed back for trace
- `methodology_note_ar` — regime-specific user-facing explanation

Existing keys preserved: `index`, `typical_bua_m2`, `actual_bua_m2`,
`rationale_ar`.

## Frontend changes

Two new form fields:
- `عمر البناء التقديري (سنوات)` — number input
- `تشطيب فاخر (للمباني القديمة)` — select (لا / نعم)

The substantiality display card now:
- Shows age and luxury status when provided
- Changes colour by regime: orange for 10-Year Rule, purple for luxury, green for new
- Shows the raw × multiplier breakdown when the multiplier ≠ 1.0
- Displays the regime-specific methodology note

## Backward compatibility

- All new fields default to `None` — existing API clients work unchanged
- When `building_age_years` is `None`, behaviour is identical to Sprint 2.2
  except a warning is added to MU about unknown age
- Output schema only adds new keys, no removals

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
tar -xf "%USERPROFILE%\Downloads\sprint2p3-age-aware.zip"
findstr /C:"sprint2p3-age-aware" evaluate_unified.py
git add evaluate_unified.py api.py index.html CHANGELOG_v6.md
git commit -m "Sprint 2.3: Qatar 10-Year Rule (age-aware adjustment)"
git push heroku master
curl -s https://thammen.qa/api/health
```

## Verification curls after deploy

**Test 1 — Old non-luxury Bou Hamour (should return 4.1M, 10-Year Rule active):**
```bash
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":56,"street":565,"building":21,"audience":"buyer",
       "floors":2,"basement":true,"annexes":2,"external_majlis":true,
       "condition":"renovated","building_age_years":30,"is_luxury":false}'
```
Expected: `amount=4100000`, `age_regime="qatar_10_year_rule"`, `adjustment_pct=0.0`

**Test 2 — Same property but flagged luxury (should return 4.5M, partial):**
```bash
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":56,"street":565,"building":21,"audience":"buyer",
       "floors":2,"basement":true,"annexes":2,"external_majlis":true,
       "condition":"renovated","building_age_years":30,"is_luxury":true}'
```
Expected: `amount=4500000`, `age_regime="old_luxury_building"`, `adjustment_pct=10.0`

**Test 3 — New villa same specs (should return 4.9M, full uplift):**
```bash
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":56,"street":565,"building":21,"audience":"buyer",
       "floors":2,"basement":true,"annexes":2,"external_majlis":true,
       "condition":"new","building_age_years":3}'
```
Expected: `amount=4900000`, `age_regime="new_building"`, `adjustment_pct=20.0`

## What's NOT in this patch (deliberate)

- **GIS-based automatic age detection** — Phase 2 of strategic doc, requires
  satellite imagery analysis pipeline. Now we rely on user-provided age.
- **Land vs building value separation** — Phase 1 of strategic doc, requires
  `land_median` per zone with n≥10 land-only transactions. Sprint 2.4.
- **Calibrated depreciation curve per area** — Phase 5, requires both above.
