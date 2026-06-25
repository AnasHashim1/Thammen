# CHANGELOG v148 — Sprint 2.22.0b.67 «تماسك القيمة عند قيادة الدخل» (income_led coherence) — DEBUG T0-2 (coherence half)

**Engine:** `thammen-sprint2p22p0b67-income-led-coherence` · **SPRINT_TAG** `2.22.0b.67` · **Date:** 2026-06-25
**Files:** `evaluate_unified.py` (income_led recompute + 2 version lines) · `test_sprint_2_22_0b67.py` (new) · `CHANGELOG_v148.md` · `docs/Session_Log.md`
**Class:** 🟡 Gate-2 (value-COHERENCE) — but the **HEADLINE is VALUE-INVARIANT** (amount/low/high/method/rule unchanged; the edit is additive INSIDE the income_led if-block → the 5 no-rent fixtures never enter). The b14/ISS-A07 coherence class. Plan-approved (`deep-crafting-pixel.md` b67, the launch-readiness plan; the PO «نعم كما توصي»).

## 1. Why this matters
When a user enters their actual rent and the income_led branch leads a villa/house headline (`evaluate_unified.py:5002+`, the b6/b7 §6 income-triangulation), the branch overrode the central with the income figure via a NON-comparison method but left **value_decomposition + value_floor anchored to the PRE-income COMPARISON figure** (built 4797-4822). So the FULL report rendered a land/building split + a value-floor disclosure that **sum to the discarded comparison amount UNDER the income headline** — e.g. a split totalling ~5.4M beneath a 2.8M income headline (internal arithmetic incoherence). This is the documented **§20.50/§20.53/§20.88 income_led decomposition-recompute gap** — input-gated (dormant on no-rent traffic, real the moment a rent is entered, reachable on the invited launch — landlords/investors).

## 2. Root cause
The income_led block (5002-5040) writes only amount/low/high + income_triangulation + the MUC bump. The mutually-exclusive else-branch recomputes value_decomposition + value_floor on the settled central for the cost_led path (5138-5153, the b16 ISS-A07 pattern); income_led had **no equivalent**.

## 3. What this patch does
Inserts, immediately after the income_led MUC bump (before the `else:`), the **VERBATIM** cost_led recompute on the income amount:
```python
try:
    _decompI = _decompose_value(valuation_amount=output['valuation']['amount'],
                                plot_area_m2=ev.plot_area_m2, bua_m2=bua, moj_ref_dict=moj_ref)
    if _decompI:
        output['valuation']['value_decomposition'] = _decompI
        _reconcile_decomposition_narrative(output)
    _vfI = _villa_value_floor(output['valuation']['amount'],
                              getattr(ev, 'plot_area_m2', None), moj_ref, _decompI)
    if _vfI:
        output['valuation']['value_floor'] = _vfI
        _inject_value_floor_into_brief(output.get('brief'), _vfI)
except Exception:
    pass
```
Same helpers + the same `bua`/`moj_ref`/`ev.plot_area_m2` in scope as the cost_led block. The FULL report's `_decompHtml` + value_floor cluster + the result-screen value_floor now render figures that reconcile to the income headline. No frontend change (the renderers already consume these via guarded paths; they were rendering the stale figures).

## 4. Scope boundary (Rule #38 / #39) — the COMPLETENESS half is DEFERRED to b68
T0-2 has two halves: (a) the **stale figures** (this sprint) and (b) the **missing leadership/value_stack** on income_led (the FULL report's leadership verdict note + the DEF-12 cost row are OMITTED). b67 ships (a) — the COHERENCE fix (the highest-confidence visible defect). (b) is **DEFERRED to b68**: emitting `leadership{leader:'income'}` + `value_stack` is net-new structure that needs its own R14 + lawyer/linguist review of the income-led DEF-12 / leadership-note presentation (open questions OQ1/OQ3 in the recon). **No regression by deferring** — those surfaces are OMITTED today (not incoherent); income reports stay coherent, just less "complete" than cost/market reports.
**Discovered (OOS, logged):** the SHORT report S4 decomposition rows (`index.html:1968-1969`) read `vd.land.value` / `vd.building_implied.value`, but the engine emits `land.estimated_qar` / `building_implied.qar` → those two short rows are **DEAD today** (key mismatch) and stay dead after b67 — a separate latent frontend bug, its own slice.

## 5. Safety — there is NO regression path
The recompute is wrapped in `try/except: pass`. If it ever raised on an income_led input, the figures stay exactly as today (the stale comparison values) → no crash, no regression. Otherwise it overwrites them with the income-coherent figures. **Strictly safe: it either fixes coherence or no-ops.** The headline amount/low/high/method/rule are never touched.

## 6. Verification — empirical evidence
- `py_compile` OK.
- Isolated `test_sprint_2_22_0b67.py` **21/21**: the REAL `_villa_value_floor` + `_decompose_value` are AMOUNT-anchored (income 2.8M → implied = 2.8M − land_floor; comparison 5.4M → 5.4M − land_floor; the two DIFFER → the recompute is not a no-op; the income split SUMS to the income amount) + Patch-C F1 (income < land → floor still surfaces, land_anchored) + STRUCTURAL: the recompute is wired into the REAL income_led block, AFTER the amount-set, reading `output['valuation']['amount']` (the income figure), and does NOT leak into the else-branch (income-branch-local; the else keeps its own `_decomp20`/`_vf20` cost_led recompute unchanged).
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · broad walk **123/123 ALL GREEN** (122→123, +b67) — **ZERO sibling re-points** (b6 23/23 · b7 22/22 · b8 19/19 · b16 38/38 · b20 69/69 stay green; the edit is purely additive inside income_led).
- Post-deploy live smoke + R14 (see §20.96).

## 7. Deployment
```
git add "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b67.py" "deploy v2/CHANGELOG_v148.md" "deploy v2/docs/Session_Log.md"
git commit -m "Sprint 2.22.0b.67: income_led coherence (recompute value_decomposition/value_floor on the income amount); headline value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 8. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health   # → engine thammen-sprint2p22p0b67-income-led-coherence
# income_led E2E (browser-UA #61): 54/541/6 + a grounded rent → income_led ~2.8M; assert
# valuation.value_decomposition land+building SUMS to the income amount (NOT 5.4M) + value_floor coherent.
# 5-fixture value byte-gate identical to v238 (income_led never fires on the no-rent fixtures).
```

## 9. What's NOT in this patch
- The COMPLETENESS half (leadership/value_stack emission on income_led) → b68.
- The SHORT report S4 key mismatch (`vd.land.value` vs `land.estimated_qar`) → separate frontend slice.
- The headline value (income_led already set it in b6/b7) — untouched.
