# CHANGELOG v141 — Sprint 2.22.0b.60 «شرح تعذّر التصنيف» (A5: explain asset_type='unknown')

> Engine `thammen-sprint2p22p0b60-a5-unknown-explanation` · SPRINT_TAG `2.22.0b.60` ·
> api-health `3.1.0-sprint2.22.0b.60`. **🟢 FRONTEND + small refusal-copy / VALUE-INVARIANT**
> (`index.html` refusal-branch only + `refusal_templates.py` one template; `api.py` UNTOUCHED;
> `evaluate_unified.py` = the 2 version-string lines). 🔴 Gate-2 by class (user-facing copy on
> the refusal screen) — before/after presented; Gate-1 «go». **Closes Bug A5 (the last open
> Medium).** Files: `index.html` + `refusal_templates.py` + `evaluate_unified.py` (version) +
> `test_sprint_2_22_0b60.py` (new).

## 1. Why this matters
A5 (open Medium since the 2026-05 marathon): when the engine cannot classify a property it
returns `asset_type='unknown'` with no on-screen explanation. The user is left confused.

## 2. Root cause / recon (Rule #58 — measured live v230)
The §5 «in JSON ≠ on screen» trap. A `classifier_failure` 'unknown' case (70/300/25, 53/240/12)
**already carries** the specific explanation at top-level `d.refusal_reason.message_ar` +
`recommendation_ar` (the 2.22.0a.2 template, added AFTER A5 was catalogued). BUT the result-screen
refusal card (`show()`, `if(!hasValuation)`) read only `v.reason_ar` (= **None** for
classifier_failure) → fell back to the GENERIC «لا تتوفر بيانات كافية لتقييم هذا العقار حالياً.»
AND showed a MISLEADING «→ أضف الإيجار أو سعر الإعلان» CTA (rent/price cannot classify an
unindexed address). The specific `d.refusal_reason` was never rendered on the result screen
(the `case 'refusal_reason'` brief renderer doesn't fire — `unknown` returns early with no
refusal_reason brief section). The reality-stop 'unknown' sub-path was already explained
(`v.reason_ar` + the `asset_type_reality` panel); the gap was the `classifier_failure` sub-path.

## 3. What this patch does (display-only, value-invariant)
- **`index.html` (refusal branch, `if(!hasValuation)` only):** the refusal reason now PREFERS
  `d.refusal_reason.message_ar` (the specific WHY) over the generic fallback; for an
  unclassifiable address the title is the honest «تعذّر تحديد نوع العقار» (not the misleading
  «التقييم يحتاج بيانات إضافية»); the `recommendation_ar` is surfaced on its own «التوصية:» line
  (reusing the existing `.rr-recommendation` style); and the misleading «add rent/price» CTA is
  **suppressed for `asset_type==='unknown'`** (the same honesty class as b36). **Known-type
  refusals (compound «أدخل الإيجار», apartment/tower b36) are UNCHANGED.** The valued path is
  untouched (the edits live entirely inside the refusal-only block).
- **`refusal_templates.py` (`classifier_failure`, per the b60 linguist-persona review):** the
  trailing «نوصي بالتحقّق…» action sentence is trimmed out of `message_ar` (it duplicated
  `recommendation_ar`, now rendered on its own line) → `message_ar` = the WHY only,
  `recommendation_ar` = the action; the bare technical «QARS» is clarified to «سجلّ العناوين
  الحكوميّ (QARS)» for the ordinary user. (Supersedes the 2.22.0a.2 Gemini-verbatim wording per
  the standing persona review; the a2.b phrase-contract test stays green.)

## 4. Verification — empirical
- py_compile OK · isolated `test_sprint_2_22_0b60.py` **21/21** (reason precedence · honest
  title · recommendation surfaced + rent-CTA suppressed for unknown · known-type CTA preserved
  in the else-if · no headline mutation · the template source exists · linguist de-dup +
  QARS-clarified · the a2.b phrase contract) + sibling `test_sprint_2p22p0a2_b_classifier_failure.py`
  **11/11** (no re-point — phrase-check survives the copy refinement).
- DoD: aggregator **395/395 MATCH** · security **15/15** · surface honesty **45/45** · broad walk
  **119/119 ALL GREEN** (118→119, **zero re-points**).
- **R14 real-Chromium 390×844 (EXECUTED):** (a) unknown 70/300/25 → h2 «تعذّر تحديد نوع العقار»
  + the specific WHY («سجلّ العناوين الحكوميّ (QARS)…», no action duplicate) + «التوصية: تحقّق
  من بيانات العنوان أو تواصل معنا.» + **NO rent CTA**, no overflow (maxRight 345<390); (b)
  compound_large 51/835/17 → CTA «→ أدخل: الإيجار السنوي الإجمالي للمجمع» **KEPT**, h2 unchanged;
  (c) apartment 52/903/90 → b36 «الشقق غير مدعومة بعد» **unchanged**; **0 console errors** across all.
- **Value-invariance:** the edits are inside the refusal-only path + a refusal-copy template →
  the 5-fixture valued gate is byte-identical by construction (re-confirmed post-deploy).
- **Persona review (PO standing directive — lawyer + linguist):** lawyer **APPROVE** (removing the
  misleading CTA RAISES defensibility; «تعذّر تحديد نوع العقار» is accurate; QARS disclosure
  low-risk; no new claim/disclaimer; non-blocking note: the «تواصل معنا» reply policy must stay
  within «ليس معتمداً» — a policy note, not code). linguist **APPROVE-WITH-NOTES → both notes
  ADDRESSED + re-verified on-screen** (🔴 the message/recommendation redundancy → trimmed; 🟡 the
  bare «QARS» → «سجلّ العناوين الحكوميّ (QARS)»).

## 5. Deployment (HELD for the Gate-1 «go»)
```
git add "deploy v2/index.html" "deploy v2/refusal_templates.py" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b60.py" "deploy v2/CHANGELOG_v141.md"
git commit -m "Sprint 2.22.0b.60: A5 — explain asset_type='unknown' on the refusal screen (value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy, browser-UA #61)
`/api/health` = b60; 70/300/25 + 53/240/12 → `asset_type:'unknown'` + `refusal_reason.message_ar`
clarified (de-duped, «سجلّ العناوين الحكوميّ (QARS)»); the 5-fixture valued gate byte-identical to v231.

## 7. What's NOT in this patch
- No valuation/headline change (refusal-only path + refusal copy); the income_led/b13-trim
  decomposition-recompute gap (the OTHER item-2 sub-task) is a separate sprint.
- No EN-localization of the result screen (DEF-UX5); `message_en` only got the QARS clarification.
- No change to the reality-stop / known-type refusal copy or CTAs.

## 8. Bug-catalogue
**A5 → CLOSED** (the last open Medium). Open mediums now = none.
