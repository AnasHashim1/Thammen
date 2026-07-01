# CHANGELOG v168 — Sprint 2.22.0b.87 «توائم الإنجليزية لافتراضات الكلفة/السيناريوهات» (EN twins — the cost/scenario `assumptions` lines)

**Engine:** `thammen-sprint2p22p0b87-en-cost-scenario-assumptions` · **SPRINT_TAG** `2.22.0b.87` · **api-health** `3.1.0-sprint2.22.0b.87`
**Files:** `evaluate_unified.py` (additive `assumptions_en` on the value_stack cost + the b23 scenarios + version bump) · `test_sprint_2_22_0b87.py` (NEW)
**Class:** 🟢 BACKEND-ONLY / **VALUE-INVARIANT** — additive `*_en` keys alongside the untouched `*_ar`; EN dormant (`pick()` when `LANG==='en'`, b77, `EN_ENABLED=false`). `api.py` + `index.html` UNTOUCHED → **R14 N/A by construction** (the b37 cost-mechanics + b23 scenarios `pick()` reads shipped + R14-verified). AR output byte-identical.

## 1. Why this matters

Fourth unit of the backend-`_en`-twins track (b84 decomposition → b85 strata → b86 briefs → b87 cost/scenario assumptions). The `assumptions` lines — the cost-mechanics assumptions on the result-screen «كيف وصلنا» line (b37, `pick(_vc,'assumptions')`) and the 4 what-if scenario rows in the short/full report (b23, `pick(it,'assumptions')`) — rendered in Arabic only, so EN mode fell back to Arabic there.

## 2. Root cause

`evaluate_unified.py` emitted `assumptions_ar` with no `_en` sibling at 5 sites: the value_stack cost dict in the income-led + main cost-led branches (variant A, the E26 «system-age is the basis» note), and the b23 `_valuation_scenarios` as_is / renovated_excellent+luxury_finish / teardown_land rows. (The scenario/cost `label_ar`/`sub_ar` already had `_en` from b20/b23.)

## 3. What this patch does

- **value_stack cost** (both income-led + main cost-led branches): `assumptions_en` mirroring the AR `.format(finish, retention)` — "Assumptions: finish {f} · retention factor {r} · system (CGIS) age is the basis (E26)".
- **b23 `_valuation_scenarios`**: `assumptions_en` for all 4 — as_is ("The adopted estimate, as shown above."), renovated_excellent + luxury_finish ("Cost approach: finish {f} · retention factor {r} · built-up area ≈ {b} m² (adjustable)."), teardown_land ("Land value ({l} QAR) − estimated demolition ({d} QAR) — the building is a cost, not value.").
- No `_ar` value changed; no amount / value / bua / retention changed — additive keys only.

**Personas (PO standing directive).** Linguist: professional English, register-consistent with the b78–b86 catalog. Lawyer: cost-methodology assumptions — no valuation claim, no disclaimer; the E26 «system-age is the basis» honesty + the teardown «building is a cost, not value» are preserved in EN.

## 4. Verification — empirical evidence

- Isolated `test_sprint_2_22_0b87.py` **10/10** — REAL `_valuation_scenarios` (all 4 rows carry `assumptions_en` + correct content, **AR byte-identical**, value-math untouched) + the value_stack cost `assumptions_en` (E26) authored + the AR unchanged + the frontend `pick()` wiring intact.
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · broad walk **143/143 ALL GREEN** (142→143; **zero re-points**).
- **R14 N/A by construction** — `index.html` git-confirmed UNTOUCHED.

## 5. Deployment

```
git push origin master
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
```

## 6. Verification curl (post-deploy)

```
curl --compressed -s https://thammen.qa/api/health    # engine = …b87
```
+ the 5-fixture value byte-gate byte-identical to the b86 release (54/541/6 2,400,000 · 56/647/6 3,800,000 · 55/296/13 2,600,000 · 56/565/21 2,400,000 · 52/903/90 None).

## 7. What's NOT in this patch (carried forward, Rule #42) — the final backend-EN mop-up (b88)

The cost `unavailable_reason` (needs a `LEAD_COST_UNAVAILABLE_EN` + the reason-phrase EN), the substantiality `rationale`/`methodology_note` (needs a `_ten_year_rule_disclosure_en` helper + the substantiality-rationale EN source) + the `:7206` methodology_note, and the small-module scatter — `scope_of_service.py` (`requires_user_input`/`guidance`/`requires`/`classification_label`/`reliability_label`), `market_regime.py` (market-position `description`), `material_uncertainty.py` (`muc_basis`/`muc_review_recommendation`), `adjustment_grid.py` (`note`), `data_freshness.py` (`caveat`), tier-breakdown (`role`/`source`), income (`cap_rate_label`/`rent_source`). Then the backend EN twins are complete and the only remaining EN work is the **reveal** (`EN_ENABLED=true` + the PO wording sign-off). No methodology / value / security change — additive i18n copy only.
