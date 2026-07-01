# CHANGELOG v167 — Sprint 2.22.0b.86 «توائم الإنجليزية لأقسام التقرير» (EN twins — the audience-brief sections)

**Engine:** `thammen-sprint2p22p0b86-en-brief-sections` · **SPRINT_TAG** `2.22.0b.86` · **api-health** `3.1.0-sprint2.22.0b.86`
**Files:** `output_briefs.py` (18 section `title_en` + cap-rate-provenance + comparable-grid `_en` + 3 EN maps) · `evaluate_unified.py` (version bump) · `test_sprint_2_22_0b86.py` (NEW)
**Class:** 🟢 BACKEND-ONLY / **VALUE-INVARIANT** — additive `*_en` keys alongside the untouched `*_ar`; EN dormant (`pick()` when `LANG==='en'`, b77, `EN_ENABLED=false`). `api.py` + `index.html` UNTOUCHED → **R14 N/A by construction** (renderSection's `pick()` reads shipped + R14-verified in b83). AR output byte-identical.

## 1. Why this matters

Third unit of the backend-`_en`-twins track (b84 decomposition → b85 strata → b86 briefs). The **audience-brief sections** (`renderSection`) rendered their section HEADERS (`pick(sec,'title')`) and much of their content in Arabic only — so in EN mode the section headers + the cap-rate / grid content fell back to Arabic.

## 2. Root cause

18 audience-brief sections in `output_briefs.py` had a `title_ar` with no `title_en`; and the two output_briefs-authored content blocks (`build_cap_rate_provenance_section`, `build_comparable_grid_section`) emitted `source_ar`/`confidence_ar`/`body_ar` (+ maps `_PROVENANCE_SOURCE_AR`/`_PROVENANCE_CONFIDENCE_AR`) and `confidence_ar`/`footer_ar` (+ `_GRID_CONFIDENCE_AR`) with no `_en` sibling.

## 3. What this patch does

- **18 section `title_en`** added (Cap-rate source / Adjusted comparables grid / Source breakdown / Why the valuation was withheld / Use cases / Trend-adjustment log / Is the price reasonable? / Risks and signals / Questions to ask before buying / Your property value / Pricing strategy / Market trend / Selling tips / Yield analysis / Income-approach value / Sensitivity analysis / Rent reference / Market context). Applied via an assertion-guarded transform (each `title_ar` matched exactly once, no partial write).
- **cap-rate-provenance**: `_PROVENANCE_SOURCE_EN` + `_PROVENANCE_CONFIDENCE_EN` maps; `source_en`/`confidence_en`/`body_en` (both the calibrated branch — incl. the b7 borrow-scope disclosure — and the hardcoded branch, mirroring the AR f-strings).
- **comparable-grid**: `_GRID_CONFIDENCE_EN` map; `confidence_en`/`footer_en`; `note_en` passthrough (`grid.get('note_en')` — the adjustment_grid EN lands in b87; graceful AR fallback until then).
- No `_ar` value changed; no median / n / cap-rate / date changed — additive keys only.

**Personas (PO standing directive).** Linguist: professional English, register-consistent with the b78–b85 catalog + the شواهد evidence-tier wording («Sufficient/Limited/Insufficient evidence»). Lawyer: methodology/provenance copy — no valuation claim, no disclaimer; the "not calibrated / typical rate" honesty of the hardcoded branch is preserved in EN.

## 4. Verification — empirical evidence

- Isolated `test_sprint_2_22_0b86.py` **12/12** — the 18 `title_en` present + the 18 `title_ar` still present (AR untouched); REAL `build_cap_rate_provenance_section` (calibrated + borrowed + hardcoded) + `build_comparable_grid_section` → `_en` present + correct, **AR byte-identical**, value-math untouched; the EN maps defined; the renderSection `pick()` wiring intact.
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · broad walk **142/142 ALL GREEN** (141→142; **zero re-points**).
- **R14 N/A by construction** — `index.html` git-confirmed UNTOUCHED.

## 5. Deployment

```
git push origin master
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
```

## 6. Verification curl (post-deploy)

```
curl --compressed -s https://thammen.qa/api/health    # engine = …b86
```
+ the 5-fixture value byte-gate byte-identical to v257 (54/541/6 2,400,000 · 56/647/6 3,800,000 · 55/296/13 2,600,000 · 56/565/21 2,400,000 · 52/903/90 None).

## 7. What's NOT in this patch (carried forward, Rule #42) — the final backend-EN mop-up (b87)

The scattered content fields that pass through from OTHER modules: market-position `description` (market_regime.py), grid `note` (adjustment_grid.py), `muc_basis`/`muc_review_recommendation` (material_uncertainty.py), the cost-stack `assumptions`/`unavailable_reason` + substantiality `rationale`/`methodology_note` (evaluate_unified), scope `requires_user_input`/`guidance`/`requires` (scope_of_service.py), scenarios `delta_label`, tier-breakdown `role`/`source`, income `cap_rate_label`/`rent_source`, `data_freshness.py` `caveat`. Then the backend EN twins are complete and the only remaining EN work is the **reveal** (`EN_ENABLED=true` + the PO wording sign-off). No methodology / value / security change — additive i18n copy only.
