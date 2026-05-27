# Sprint 2.22.0a.2 — READY FOR PUSH

**Status:** Gate 1 CLEARED. Awaiting Anas's explicit push consent (Rule #32).
**Engine version:** `thammen-sprint2p22p0a2-arabic-surface-content-fixes`
**Sprint tag:** `2.22.0a.2`
**CHANGELOG:** [CHANGELOG_v52.md](../CHANGELOG_v52.md)
**Multi-AI validation log:** [docs/MULTI_AI_VALIDATION_BATCH_2p22p0a2.md](MULTI_AI_VALIDATION_BATCH_2p22p0a2.md)
**Date:** 2026-05-27

---

## Commit chain (14 atomic commits, latest at top)

```
<pending v52 commit>  Phase 1 closeout: ENGINE_VERSION bump + CHANGELOG_v52.md + this file
9730cdd                Strategic deferral capture (docs/DESIGN_2p23_VALIDATOR_FEEDBACK.md)
97168da                §9 polish — مشابهة/مماثلة precision pass
3328926                B classifier_failure refusal trigger (7th template)
154cf56                C5 DELETE user-visible negotiation section
1703aeb                C4 IVS/RICS disclaimer reframe (9 sites)
f69e837                C3 شواهد tier badge relabel (Anas-locked override)
62a759d                Batch packet enrichment (C3 inventory + C5 locator)
db506fc                Batch packet §7 Anas marks ACCEPT (B2/B3 architecture)
ac5fcc6                Mid-Phase-1 STOP report at validation gate
1c7ce8b                Multi-AI batch packet
9dafb73                C2 mechanical drop (stock_strata.py:93)
7c525fb                Pattern A LRM bidi wrap (4 sites)
9e6c981                Phase 0 audit + probes
```

---

## Test totals

```
Regression baseline preserved:
  Root test_*.py        29 files   29/29 PASS  (was 23/23 in pre-2.22.0a.2;
                                                 6 new Sprint 2.22.0a.2 isolated
                                                 tests added)
  tests/test_*.py       17 files   16/17 PASS
    (1 fail = test_v2_modules.py pytest-import block, Session_Log §11.3
     PRE-EXISTING, NOT introduced by this Sprint)

  COMBINED              46 files   45/46 PASS

New Sprint 2.22.0a.2 isolated tests (all PASS):
  test_sprint_2p22p0a2_lrm_bidi.py                          5/5
  test_sprint_2p22p0a2_c2_mechanical.py                     3/3
  test_sprint_2p22p0a2_c1_geopolitical_neutralization.py    7/7
  test_sprint_2p22p0a2_c3_shawahid_tier_badges.py           8/8
  test_sprint_2p22p0a2_c4_disclaimer_reframe.py             8/8
  test_sprint_2p22p0a2_c5_delete_negotiation.py             5/5
  test_sprint_2p22p0a2_b_classifier_failure.py             11/11
  test_sprint_2p22p0a2_p9_precision_pass.py                 5/5
  Sprint 2.22.0a.2 NEW TOTAL                               52/52

Upstream tests updated to match new copy (intent preserved, brittle pins
relaxed):
  test_material_uncertainty.py            39/39 PASS
  tests/test_sprint_2p19p1_polish.py      41/41 PASS
  tests/test_sprint_2p20_grid.py          21/21 PASS
  test_sprint_2p22p0a_refusal_reason.py  115/115 PASS
  test_sprint_2p22p0a1_qars_envelope_fallback.py  38/38 PASS
                                                  (brittle-pin relax per
                                                   Sprint 2.19.1 anti-pattern)
```

---

## Gate 1 checklist

- [x] **py_compile** on every modified Python file (api.py,
      evaluate_unified.py, evaluate_v3.py, evaluate_property.py,
      material_uncertainty.py, market_regime.py, output_briefs.py,
      stock_strata.py, refusal_templates.py) — clean.
- [x] **node --check on index.html JS** — N/A by tool inventory; LRM
      markers in JS string literals don't break JS syntax (Pattern A
      tests confirm the rendered banner header contains the LRM
      wrapping).
- [ ] **Mobile viewport 390×844 visual check** — RESERVED FOR ANAS.
      The Sprint touches user-visible Arabic strings only; the dominant
      bidi-correctness risk is the muc_clause_ar banner header (Pattern
      A) and the C1-reframed cause-of-uncertainty paragraph. Anas should
      verify rendering on a phone before push.
- [x] **45/46 regression files PASS** (post-2.22.0a.1 baseline; the 1
      fail is the pre-existing pytest-block on test_v2_modules.py).
- [x] **Multi-AI validation log complete** for every pattern-C change
      ([docs/MULTI_AI_VALIDATION_BATCH_2p22p0a2.md](MULTI_AI_VALIDATION_BATCH_2p22p0a2.md)
      §§1, 2, 4, 6 Gemini-approved; §3 + §5 + §7 Anas-locked overrides
      documented).
- [x] **CHANGELOG_v52.md drafted**, single-purpose, names Sprint 2.22.0a.2,
      enumerates commits 6–13, links to multi-AI validation log.
- [x] **ENGINE_VERSION + SPRINT_TAG bumped** in evaluate_unified.py:44-45 to
      `thammen-sprint2p22p0a2-arabic-surface-content-fixes` / `2.22.0a.2`.

---

## Push command (Operational_Rules #43)

```
git subtree push --prefix "deploy v2" heroku master
```

If split-commit divergence: use the named-temp-branch + force-push
procedure documented in #43 expansion:

```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

---

## Gate 2 — Post-deploy smoke plan (CC runs after push)

**Target anchors** (the same Phase 0 set + 2 supplements):

1. `52/903/90` (apartment_building) — should fire `comp_density_sparse`
   with the C3 شواهد taxonomy + C4 disclaimer reframe. Validates known-
   asset-type sparse-MoJ refusal path unchanged.
2. `56/565/21` (Bou Hamour villa) — full brief renders. Validates:
   - Pattern A LRM in muc_clause_ar banner
   - C1 neutral cause-of-uncertainty paragraph
   - C2 stock_strata caveat rewrite
   - C3 شواهد at land_priced.reliability_label_ar + accuracy.label
   - C4 disclaimer reframe
   - C5 'negotiation' section NOT present in brief.sections[].id
   - §9 precision phrase in accuracy.explanation_ar
3. `69/255/75` (Lusail T2/T3 anchor — H1) — apt_bldg refusal path.
   Validates same as #1.
4. `70/300/25` (asset_type=unknown) — should fire **classifier_failure**
   (was `comp_density_sparse` pre-Sprint). Validates Pattern B routing.
5. **B1 case (compound_large >= 15K)** — pick `51/835/17` (Sprint 2.18.1.1
   E20 boundary) — should fire `asset_scale_extreme`. Validates Pattern B
   did NOT regress this row.
6. **density_gated_district case** — pick a Pearl Qatar address if Anas
   has one. Should fire `density_gated_district`. Validates Pattern B
   did NOT regress this row.

**Smoke checks per anchor:**
- HTTP 200 (or 200 with refusal_reason emitted, depending on path)
- `engine_version` reads `thammen-sprint2p22p0a2-arabic-surface-content-fixes`
- grep response body for forbidden substrings (C1: `الحرب`/`هرمز`/`نزوح`;
  C2: `Sprint 2.16.0`/`Project Instructions §3`; C3: `موثوق` as tier
  badge; C4 old phrasings; C5: `لا تدفع أكثر من وسيط MoJ`; §9 old
  `لعقارات مشابهة بنفس الحجم`)
- Heroku logs first 50 requests show zero 5xx

**Smoke tool:** file-based per Rule #34. Will reuse the
`probe_phase0_anchors.py` shape with the 6-anchor list above.

---

## Gate 3 — Anas's visual review (post-Gate-2)

CC writes `docs/SPRINT_2p22p0a2_GATE3_REPORT.md` with:
- Smoke test results from Gate 2 (per-anchor pass/fail)
- Production screenshots if requested
- Any unexpected observations

Anas reviews and either approves or rolls back. Rollback target:
Heroku v132 (`heroku rollback`) = Sprint 2.22.0a.1 engine.

---

## Known carry-forward items (unchanged)

- ENGINE behavior on `comparison_bracket` value-producing paths
  preserved.
- MoJ data, GIS data, market_regime calibration math preserved.
- Frontend `index.html` rendering pipeline preserved beyond the single
  Pattern A LRM-wrap at line 738.
- 5 strategic items (§§4/6/7/10/11) DEFERRED to Sprint 2.23.x design
  Sprint — see `docs/DESIGN_2p23_VALIDATOR_FEEDBACK.md`.

---

## Sprint metadata

| | |
|---|---|
| Patterns shipped     | A + B + C1 + C2 + C3 + C4 + C5 + §9 polish (8 total) |
| Atomic commits       | 14 (counting Phase 0 audit + Multi-AI batch packet) |
| Files modified       | api.py, evaluate_unified.py, evaluate_v3.py, evaluate_property.py, material_uncertainty.py, market_regime.py, output_briefs.py, stock_strata.py, refusal_templates.py, index.html (10 prod files) |
| Files created (tests)| 8 new test files |
| Files created (docs) | 4 (Phase 0 audit, batch packet, STATUS, READY_FOR_PUSH) + 1 (DESIGN_2p23) + CHANGELOG_v52 |
| Multi-AI validations | 5 (C1 + C2-rewrite + C3 + C4 + B copy); C5 architecture decision (DELETE not reframe) post-validation |
| Anas-locked overrides| C3 (شواهد over تغطية), C5 (DELETE not reframe), B2/B3 ACCEPT (separate triggers) |
| Lines added          | ~1500 (mix of prod code, tests, docs) |
| Lines removed        | ~50 (C5 deletions + dead-code cleanup) |

---

**Sprint 2.22.0a.2 is feature-complete and Gate 1 ready.**

When Anas approves push, run the subtree-push command above, then CC
proceeds to Gate 2 smoke. Until then, nothing else lands on master.

---

*Authored by Claude Code 2026-05-27 at Phase 1 closeout.*
