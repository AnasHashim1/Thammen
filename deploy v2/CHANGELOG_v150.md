# CHANGELOG v150 — Sprint 2.22.0b.69 «اكتمال قيادة الدخل» (income_led completeness) — DEBUG T0-2 (completeness half)

**Engine:** `thammen-sprint2p22p0b69-income-led-completeness` · **SPRINT_TAG** `2.22.0b.69` · **Date:** 2026-06-25
**Files:** `evaluate_unified.py` (income leadership + value_stack emission + 2 version lines) · `test_sprint_2_22_0b69.py` (new) · `CHANGELOG_v150.md` · `docs/Session_Log.md`
**Class:** 🟡 Gate-2 (net-new emitted structure on income_led → the FULL report renders new disclosures) — but the **HEADLINE is VALUE-INVARIANT** (additive inside the income_led if-block; the 5 no-rent fixtures never enter; amount/low/high/method/rule untouched). The b14/b67 coherence-display class. Plan-approved (T0-2 = «recompute + emit value_stack/leadership»; the recon edit-2, `wf_25dd1337-bef`). **Lawyer + linguist personas applied** (note_ar REUSES the existing income copy → zero new copy).

## 1. Why this matters
b67 fixed the income report's stale FIGURES (coherence). But the income_led report still LACKED the **leadership verdict note** + the **DEF-12 cost row** that every cost/market path renders (they were silently OMITTED → an income report showed a number with no machine-readable leader verdict + no three-value cost context — weaker than every other leader path). And the income reasoning (`income_triangulation.note_ar`) had **NO frontend consumer** — so the WHY of an income-led number was invisible.

## 2. What this patch does
Inside the income_led if-block, right after the b67 recompute (before the `else:`), emit two ADDITIVE blocks:
- **`valuation.leadership`** = `{leader:'income', rule:'income_led', income_value, market_value (=the demoted comparison), cost_value (=_cost_av['value'] or None), cap_rate, net_yield_pct, sample_size, confidence, note_ar, note_en}`. The note REUSES the already-built `_note_ar`/`_note_en` (5012-5023) → zero new copy, value-invariant text. It deliberately **OMITS** the market-evidence fields (matched_n / dispersion_36 / band / geo_full / thresholds / stratum_match) — those justify a MARKET verdict; surfacing them on an income leader would falsely imply the pool decided the number.
- **`valuation.value_stack`** = `{market:{median:comparison_value, n}, cost:(the DRC cost stack — the SAME 5057-5073 builder, reusing `_cost_av` + COST_STACK_* constants), income_available:True}`. `market` carries NO `dispersion_36` (so the report's market-dispersion line stays OFF — no false market-evidence claim).

No frontend change — the renderers already consume `leadership`/`value_stack` via guarded paths (they were simply omitting them when absent).

## 3. Render effects (verified pre-deploy R14)
- FULL report: the leadership-note block (the income reasoning, plain styling — `rule='income_led'` ≠ cost_led/e25_capped → no warn box) + the **DEF-12 cost row** (the DRC cost as context) now render. The **DEF-12 central stays `v.amount`** (the income headline — `fmt(v.amount)`, NOT market.median).
- Result screen: the cost-mechanics line (b37) + the leadership note now render in the «كيف وصلنا» fold.
- **b64 #4 (cost-basis hero line) stays OFF** (`leader==='cost'` ≠ 'income'). The market-dispersion line stays off (no `dispersion_36`). The b67 income-coherent decomposition still renders.

## 4. Safety / scope
The emission is in `try/except: pass` (no regression path) and is income-branch-local — the else-branch `_lead20` (b20 leadership/value_stack) is UNTOUCHED. Headline amount/low/high/method/rule never touched. **NOT in scope:** the DEF-12 income third-value (the central is the income headline; market+cost are context — a future design call); the SHORT report S4 decomposition key mismatch (`vd.land.value` vs `land.estimated_qar` — dead rows today, a separate frontend slice).

## 5. Verification — empirical evidence
- isolated `test_sprint_2_22_0b69.py` **24/24** (STRUCTURAL on the REAL income_led block: emits leadership{leader='income',rule='income_led',note_ar=_note_ar} + value_stack{market.median=comparison_value, cost reuses COST_STACK_*+_cost_av, income_available} · OMITS the market-evidence keys · market has no dispersion_36 · the b67 recompute still present · income-branch-local — the else keeps _lead20 · the 4 COST_STACK constants defined).
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · broad walk **125/125 ALL GREEN** (124→125, +b69) — **ZERO re-points** (b20 69/69 + b67 21/21 green; the income emission is a different shape in a different branch).
- **Pre-deploy R14 real-Chromium 390×844** (hand-built b69-shape payload on the b67 income capture): the FULL report renders the DEF-12 cost row «قيمة التكلفة (أرض + بناء مُهلَك) — نهج DRC ٢٬٣٧٨٬٠٩٤» + the leadership note + the b67-coherent decomposition (٩٤٨٬٧٤٠); the DEF-12 central = **٢٬٨٠٠٬٠٠٠** (income headline, NOT market-promoted); no market-dispersion line; no overflow (390==390); **0 console errors**.
- Post-deploy live E2E (see §20.98).

## 6. Deployment
```
git add "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b69.py" "deploy v2/CHANGELOG_v150.md" "deploy v2/docs/Session_Log.md"
git commit -m "Sprint 2.22.0b.69: income_led completeness (emit leadership/value_stack); headline value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health   # → engine thammen-sprint2p22p0b69-income-led-completeness
# income_led E2E: 54/541/6 + rental_income 15000 → income_led; assert valuation.leadership.leader=='income'
#   + valuation.value_stack.cost.value present + value_decomposition still sums to the income amount.
# 5-fixture value byte-gate identical to v240 (income_led never fires on the no-rent fixtures).
```

## 8. What's NOT in this patch
- The DEF-12 income third-value / leader='income' as an explicit user-facing label — a future design call (the central is already the income headline).
- The SHORT report S4 key mismatch — a separate frontend slice.
- No valuation/method/headline change (T0-2 is now FULLY closed: b67 coherence + b69 completeness).
