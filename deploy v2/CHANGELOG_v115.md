# CHANGELOG v115 — Sprint 2.22.0b.32 «تبسيط شاشة التأكيد» (DEF-UX13)

**Engine:** `thammen-sprint2p22p0b32-confirm-simplify` · **SPRINT_TAG** `2.22.0b.32` ·
**api/health** `3.1.0-sprint2.22.0b.32` · **date** 2026-06-13 ·
**files:** `index.html` (4 edits) · `evaluate_unified.py` (2 version lines) ·
`test_sprint_2_22_0b32.py` (new) · 4 sibling re-points (b2p2/b2p3/b27/b31, R6/Lesson-2).
**🟢 FRONTEND-ONLY / VALUE-INVARIANT** (engine = the 2 version-string lines; `api.py` UNTOUCHED;
`v.amount/low/high/method/rule` byte-identical — مبدأ b24 «الرقم واحد للجميع»).
**Gate-2** signed by delegation (the study `docs/STUDY_persona_simplicity_and_entry_v1.md` §3 +
`ISSUES_LOG §4ب-2`). **Gate-1** deploy-on-green per the #65 handoff.

-----

## 1. Why this matters

DEF-UX11/b31 cut the RESULT screen (the «9-note parade» + the evidence panel folded into ONE
collapsed accordion). The **confirmation screen** (Screen 2, `showConfirm()`) was still the
study's §0 measured overload — ~12 elements before the owner can say «تابِع»: a full
4-component evidence panel, an inline E15 setbacks equation, and the b9 utility numbers
(electricity/water) + the survey-vintage building-age row. For the simple owner the confirm
screen is «راجع البيانات وتابِع» — none of those four belong on the default view.

## 2. Root cause

`showConfirm()` (index.html ~931) had accreted, sprint-by-sprint, surfaces meant for the
*result*: the b2.2 `evidencePanelHtml()` (v168/b2.3), the م4/b27 inline setbacks parenthetical
on the building-area row, and the full b9 `pbRows()` panel (PIN + electricity + water +
age-floor). The study §3 kill-list 17-20 names exactly these for the confirm screen.

## 3. What this patch does (study §3, items 17-20)

**`index.html` (4 edits):**
- **(18)** DROP `evidencePanelHtml(d,acc)` from `showConfirm` — the panel lives only on the
  result, inside the b31 «🔍 كيف وصلنا لهذا الرقم؟» accordion. No pill substitute (study §3
  «لا لوحة أدلّة»). The `evidencePanelHtml()` function is untouched (still used on the
  result + the report).
- **(17)** The E15 setbacks equation moves from an inline parenthetical to a hover **tooltip**
  (`<span class="cg-tip" title="…">ⓘ</span>`). The owner keeps the max-buildable NUMBER
  «≈ {N} م²» + the «عدّله في خطوة التحسين» CTA; the formula (dims + 5/3/3 + 60% cap, LRM-wrapped
  per Rule #25) is one hover away. The shared-parcel detail also tooltip-only.
- **(19)+(20)** `pbRows(pb, basisOnly)` gains a `basisOnly` flag: on the confirm screen it
  prints ONLY the cadastral id (PIN), then early-returns — the utility numbers + the
  survey-vintage age move OUT of the default view. The age message already lives at the refine
  «عمر البناء» field (index.html:588) → the move is a move, not a loss. The other call-sites
  (results 2169 / report 1641) pass NO flag → full panel, **byte-identical**.

**KEEP on the confirm screen (study §3 «يبقى»):** basis review (address / asset / district /
zoning / area + the cadastral id) + the muted preliminary range + the cost-led dual-evidence
cg-mid line (b20, part of the range, not the panel) + the «تابِع بهذه البيانات» button + the
«التقرير الكامل الآن» escape.

**`evaluate_unified.py`:** the 2 version-string lines only.

## 4. Backend / frontend / schema

Frontend-only. No backend, no schema, no API change. `api.py` UNTOUCHED. The value
(amount/low/high/method/rule/leadership) is never read or written by the changed lines.

## 5. Verification — empirical evidence

- **py_compile** `evaluate_unified.py` OK.
- **isolated** `test_sprint_2_22_0b32.py` **29/29** (reads the REAL index.html — E14: panel
  dropped from showConfirm + still on result/report · setbacks → cg-tip tooltip + old inline
  form gone + LRM · pbRows basisOnly: PIN before the early-return, utilities/age after ·
  confirm keep-list · no v.amount/low/high mutation).
- **sibling re-points (R6/Lesson-2 — stale structural pins DEF-UX13 invalidates):** b2p2
  («panel rendered» → folded on result), b2p3 («5.4 reuses panel» → DROPPED from gate), b31
  («still in showConfirm» → standalone h+= render gone), b27 («confirm carries the equation» →
  now in a cg-tip tooltip). Post-re-point: b2p2 26/26 · b2p3 32/32 · b27 23/23 · b31 36/36.
  Siblings green WITHOUT re-points: b9 29/29 · b3 14/14 · b15 50/50 · b17 33/33 · b24 58/58 ·
  b26 33/33 · b29 32/32.
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **ALL COUNTS MATCH (392)** · security
  **15/15** · surface-honesty **45/45** · broad walk **100/100 ALL GREEN** (199.9s).
- **R14 real-Chromium 390×844** on the live cost-led امريخ fixture (`.basket/f_marikh.json`):
  the confirm screen = العنوان · نوع العقار · امريخ الجنوبي · R1 · مساحة القسيمة ٦١٣ م² ·
  **الرقم المساحي 54360025** · «مساحة البناء الأرضي (تقدير أقصى) ≈ ٣١١ م² ⓘ — عدّله في خطوة
  التحسين» — the ⓘ tooltip title = «من أبعاد القطعة ‎35×17.5‎ م بعد الارتدادات القانونية (أمامي
  5 · جانبي 3 · خلفي 3) وضمن سقف تغطية 60%»; **evidence panel ABSENT · electricity/water ABSENT
  · age-estimate ABSENT · formula NOT inline**; the b20 cost-led dual-evidence line stays;
  confirm button + full-report escape present; **0 console errors/warnings**; **no overflow**
  (doc 390==390, cgOut 350<390).

## 6. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add index.html evaluate_unified.py test_sprint_2_22_0b32.py CHANGELOG_v115.md test_sprint_2_22_0b2p2.py test_sprint_2_22_0b2p3.py test_sprint_2_22_0b27.py test_sprint_2_22_0b31.py
git commit -m "Sprint 2.22.0b.32 (DEF-UX13): simplify the confirmation screen"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health
:: expect version 3.1.0-sprint2.22.0b.32 / engine …b32-confirm-simplify
:: 5-anchor value byte-gate (browser-UA curl, Rule #61) must be identical to v202:
::   امريخ 2.4M cost_led [2.4M–5.4M] · V001 3.8M geo_full · المعراض 2.6M e25_capped
::   · أبو هامور 2.4M matched · شقق refusal
:: served index.html must carry class="cg-tip" + pbRows(d.property_basis,true)
```

## 8. What's NOT in this patch

- No value/method/leadership change (value byte-identical — DEF-UX13 is presentation-only).
- DEF-UX12 (the role-driven density hinge — broadcast `audience` → fold-state) is the next
  study-§5 step and the ONLY one needing an additive server field; NOT here.
- The full study §3 «21→5» result-screen micro (tier-badge → accordion-header faint label /
  MUC-word-conditional / moj-n fold) is a deferred micro (touches b15 compliance pins).
- PIN (الرقم المساحي) stays on the confirm screen — it is NOT in the §3 kill-list (17-20);
  it is part of «مراجعة الأساس». (Rule #38 — the NAMED items only.)
