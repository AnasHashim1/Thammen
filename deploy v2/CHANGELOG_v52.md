# CHANGELOG v52 — Sprint 2.22.0a.2: Arabic Surface Content Fixes

**Sprint:** 2.22.0a.2
**Engine version:** `thammen-sprint2p22p0a2-arabic-surface-content-fixes`
**Sprint tag:** `2.22.0a.2`
**Local commits:** 9e6c981 .. (Phase 1 closeout)
**Push status:** STOP — push consent reserved for Anas (Rule #32)

---

## Why this Sprint

Phase 0 audit (`docs/PHASE0_ARABIC_SURFACE_AUDIT.md`) probed 4 production
anchors against `thammen.qa/api/evaluate` and surfaced one bug class:
**user-visible Arabic copy correctness in production brief surface**.

Seven independent patterns were identified, validated via GPT-5 + Gemini
two-AI consensus (Rule #54) where copy changes were substantive, and
shipped as 9 atomic commits per Rule #38.

---

## What this Sprint ships (commits 6 → 14)

### Pattern A — LRM bidi wrap (commit 7c525fb)
Wrap Latin/digit tokens with U+200E (LRM) at 4 user-visible
Arabic-with-Latin string sites (`material_uncertainty.py x2`,
`output_briefs.py:584`, `index.html:738`). Prevents bidi reversal
under `dir="rtl"` rendering per Operational_Rules #25.
**Tests:** `test_sprint_2p22p0a2_lrm_bidi.py` 5/5 PASS.

### Pattern C2 — internal-doc leak (commits 9dafb73 + 990067a)
- 9dafb73 (mechanical): drop `(Project Instructions §3)` parenthetical
  from `stock_strata.STRATUM_DESC_AR['land_priced']`.
- 990067a (validated): rewrite `sprint_scope_caveat_ar` removing
  Sprint version self-reference, English/Arabic code-switching
  (`الـ stratification` / `الـ stratum`), and forward-looking-statement
  promise.
**Tests:** `test_sprint_2p22p0a2_c2_mechanical.py` 3/3 PASS.

### Pattern C1 — geopolitical neutralization (commit b3dfba9)
Reframe VPGA 10 §6 cause-of-uncertainty paragraph in `muc_clause_ar` /
`muc_clause_en` from naming specific shock layers (regional war, Hormuz
closure, population outflow, transaction-volume collapse) to naming the
verifiable data-evidence cause (constrained market evidence + MoJ
data-freshness gap + low recent transaction volume).
- `material_uncertainty.py:163-208` — clause body reframed
- `market_regime.py:307-318` — defensive companion site (`lag_warning`)
  reframed
- `ShockLayer.name_ar` data model UNTOUCHED (internal audit trail preserved)
- Calibration math UNCHANGED (buyer_ceiling_multiplier_default = 1.00 etc.)

**Tests:** `test_sprint_2p22p0a2_c1_geopolitical_neutralization.py` 7/7 PASS;
upstream `test_material_uncertainty.py` 39/39 PASS after 4 assertions
reframed to match new VPGA-10-compliant language.

### Pattern C3 — شواهد tier badge relabel (commit f69e837)
Anas-locked override per resume KICKOFF: GPT-5 preferred شواهد (native
valuation domain term — "evidence/witnesses") over CC's original تغطية
draft.

Taxonomy:
- `reliable`   → `شواهد كافية`        (was `موثوق`)
- `indicative` → `شواهد محدودة`        (was `إرشادي`)
- `fallback`   → `شواهد غير كافية`     (was `احتياطي` / `عينة محدودة`)

Applied at 7 Category A tier-badge sites + 7 Category B prose references.
Category C generic-adjective sites (e.g., `إنتاج تقييم موثوق`) explicitly
LEFT UNTOUCHED per scope discipline.

**Tests:** `test_sprint_2p22p0a2_c3_shawahid_tier_badges.py` 8/8 PASS;
upstream `tests/test_sprint_2p19p1_polish.py` 41/41 + `tests/test_sprint_2p20_grid.py` 21/21 + `test_stock_strata.py` 6/6 PASS.

### Pattern C4 — IVS/RICS disclaimer reframe (commit 1703aeb)
9 sites reframed from defensive negation (`ليس تقييماً معتمداً وفق RICS/IVS`)
to descriptive provenance (`ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص
وفق معايير RICS/IVS`):
- Long form (3 sites): `api.py:783`, `evaluate_v3.py:356`,
  `evaluate_property.py:474`
- Short form (5 sites): `evaluate_unified.py` 1960, 2404, 2618, 2724, 2857
- List-item form (1 site): `api.py:843` `what_thammen_does_not[0]`

**Tests:** `test_sprint_2p22p0a2_c4_disclaimer_reframe.py` 8/8 PASS.

### Pattern C5 — DELETE user-visible negotiation section (commit 154cf56)
Anas-locked override per resume KICKOFF: DELETE, not reframe. GPT-5
caught that even descriptive reframing of imperatives still anchors
negotiation behavior via a specific 10% number that doesn't generalize.
- `output_briefs.py:509-521` (fair_range builder + sections.append) REMOVED
- `evaluate_unified.py:1329-1363` (dead post-processor + _negotiation_anchor)
  REMOVED
- ENGINE INTERNAL CODE PRESERVED: `evaluate_property.above_buyer_ceiling`
  flag, `market_regime.buyer_ceiling_multiplier_default` / `opening_offer_*`.

**Tests:** `test_sprint_2p22p0a2_c5_delete_negotiation.py` 5/5 PASS.

### Pattern B — classifier_failure refusal trigger (commit 3328926)
Per Anas-locked architecture (resume KICKOFF §7 ACCEPT): 7th template
+ new dispatcher row 2.
- `refusal_templates.REFUSAL_TEMPLATES` += `classifier_failure`
  (Gemini-approved Arabic + English copy)
- `evaluate_unified._compute_refusal_reason()` precedence chain inserts
  new row 2: `if asset_type == 'unknown' and method != 'asset_type_reality_stop'`
  → `classifier_failure`. Subsequent rows renumber.
- Fixes the Phase-0 70/300/25 misroute (was `comp_density_sparse`, now
  truthful `classifier_failure` CTA).

**Tests:** `test_sprint_2p22p0a2_b_classifier_failure.py` 11/11 PASS;
upstream `test_sprint_2p22p0a_refusal_reason.py` 115/115 PASS after
count assertions flipped from 6 to 7.

### §9 polish — مشابهة/مماثلة precision pass (commit 97168da)
Reframed 4 user-visible MoJ-comparable-language sites in
`evaluate_unified.py` from overclaiming property-level similarity
(`صفقة مماثلة` / `لعقارات مشابهة بنفس الحجم` / `الصفقات المشابهة`)
to honest comparable scope (`قريبة في النوع والمساحة ضمن نفس المنطقة`).
Scope-disciplined: `geo_reference_v2.py` decision_labels (area-adjacency)
and `market_position.py` user-prompts about listings LEFT UNTOUCHED.

**Tests:** `test_sprint_2p22p0a2_p9_precision_pass.py` 5/5 PASS.

### Strategic deferral capture (commit 9730cdd)
`docs/DESIGN_2p23_VALIDATOR_FEEDBACK.md` captures GPT-5's §§4/6/7/10/11
strategic observations (RICS citation density, value decomposition
framing, villa 4% cap rate, report length / progressive disclosure,
three-output-modes architecture) as input for a future 2.23.x design
Sprint. None actioned in 2.22.0a.2.

---

## Test posture

```
ROOT  test_*.py             : 23/23 + 5 new Sprint 2.22.0a.2 files
TESTS tests/test_*.py       : 16/17  (test_v2_modules.py still pytest-blocked,
                                       Session_Log §11.3, pre-existing)

NEW Sprint 2.22.0a.2 isolated test files:
  test_sprint_2p22p0a2_lrm_bidi.py                   5/5 PASS
  test_sprint_2p22p0a2_c2_mechanical.py              3/3 PASS
  test_sprint_2p22p0a2_c1_geopolitical_neutralization.py   7/7 PASS
  test_sprint_2p22p0a2_c3_shawahid_tier_badges.py    8/8 PASS
  test_sprint_2p22p0a2_c4_disclaimer_reframe.py      8/8 PASS
  test_sprint_2p22p0a2_c5_delete_negotiation.py      5/5 PASS
  test_sprint_2p22p0a2_b_classifier_failure.py      11/11 PASS
  test_sprint_2p22p0a2_p9_precision_pass.py          5/5 PASS
  TOTAL                                            52/52 PASS

UPSTREAM tests UPDATED to match new copy (test intent preserved):
  test_material_uncertainty.py      39/39 PASS  (4 assertions reframed)
  tests/test_sprint_2p19p1_polish.py 41/41 PASS  (3 assertions flipped)
  tests/test_sprint_2p20_grid.py    21/21 PASS  (1 assertion flipped)
  test_sprint_2p22p0a_refusal_reason.py 115/115 PASS  (template count
                                                       flipped 6 → 7)

UPSTREAM regression PRESERVED:
  test_market_regime.py             36/36 PASS  (C1 doesn't touch
                                                  calibration math)
  test_stock_strata.py               6/6 PASS  (C2 + C3 applied cleanly)
  tests/test_sprint_2p18p1p1_compound_misroute.py 19/19 PASS  (compound
                                                                flow unaffected)
```

---

## Multi-AI validation log

Per Rule #54 two-AI consensus requirement for substantive copy changes:

- **C1**: Gemini approved verbatim per
  `docs/MULTI_AI_VALIDATION_BATCH_2p22p0a2.md` §1. GPT-5 raised §§4
  citation density as orthogonal observation → captured for 2.23.x.
- **C2 rewrite**: both Gemini and GPT-5 approved.
- **C3**: both approved direction (input-claim vs output-claim); GPT-5
  preferred شواهد over تغطية; Anas locked شواهد.
- **C4**: both approved verbatim per §4.
- **C5**: GPT-5 caught that even descriptive reframing still anchors
  via the specific 10% number; Anas locked DELETE.
- **B (classifier_failure copy)**: Gemini approved; GPT-5 silent
  (treated as non-flag per resume KICKOFF reconciliation).
- **§9 precision pass**: new polish item from validation runs (not in
  original KICKOFF); Anas locked the contextual paraphrase approach.

Architecture decisions (NOT multi-AI):
- **§7 B2/B3 architecture**: Anas marked **ACCEPT** — keep
  classifier_failure and density_gated_district separate. New 7th
  template + new dispatcher row.

---

## What's NOT in this Sprint

- ENGINE behavior on `comparison_bracket` / value-producing paths
  UNCHANGED.
- MoJ data, GIS data, calibration math UNCHANGED.
- Frontend `index.html` rendering pipeline UNCHANGED beyond the single
  Pattern A LRM-wrap at line 738.
- 5 strategic items (§§4/6/7/10/11) DEFERRED to Sprint 2.23.x design
  Sprint per `docs/DESIGN_2p23_VALIDATOR_FEEDBACK.md`.
- Mobile viewport 390×844 visual check (Anas's job before push).

---

## Deployment

Per Operational_Rules #43 the deploy command (when Anas approves push) is:

```
git subtree push --prefix "deploy v2" heroku master
```

If split commits have diverged, the named-temp-branch + force-push
procedure documented in #43 expansion applies.

Post-deploy Gate 2 smoke plan: see
`docs/SPRINT_2p22p0a2_READY_FOR_PUSH.md`.

---

*Authored 2026-05-27 at Phase 1 closeout. Sprint 2.22.0a.2 is feature-
complete and Gate 1 ready. Pushes pending Anas's explicit consent.*
