# CHANGELOG v132 — Sprint 2.22.0b.50 «تصحيح النسخ: صدق المصدر + التناقض + قناة التواصل + إزالة المصطلح الداخليّ»

**Engine:** `thammen-sprint2p22p0b50-copy-honesty-source-contact` · **SPRINT_TAG** `2.22.0b.50`
**Date:** 2026-06-16 · **Files:** index.html, api.py, evaluate_unified.py, material_uncertainty.py, data_freshness.py, test_sprint_2_22_0b50.py (new) + 4 sibling test re-points (a20, a8, b17, b25)

## 1. Why this matters
Two studies — the 100-persona panel (`docs/PERSONA_PANEL_100_b49_v222.md`) + the per-phrase copy sweep (`docs/COPY_AUDIT_persona_sweep_b49.md`) — flagged copy that erodes trust or risks a **CC BY 4.0 / no-implied-affiliation** breach. PO signed Gate-2 («طبّق الإصلاحات … افعل الأصوب») + Gate-1 «go», with one explicit decision: **drop the WhatsApp number entirely; use `info@thammen.qa`**.

## 2. Root cause (the offending copy, measured in source)
- **Source-affiliation lean (🔴 CC BY + regulatory):** prominent lines implied official/affiliated MoJ status — home «بيانات وزارة العدل **الفعلية**» (index 502), disc credit «بيانات وزارة العدل **القطرية**» (701), api subtitle «… القطرية **الرسمية**» (api 822). The precise no-endorsement clause existed only in the footer src-credit (a25), not the prominent lines.
- **Self-reference contradiction (🔴):** the results disclaimer called the product «هذا **التقييم** إرشادي» (697) while the whole product insists «ليس **تقييماً**». Our output is a **تقدير**.
- **Personal contact channel (🔴 privacy):** Terms + GT hooks routed feedback «مباشرةً إلى **أنس** عبر واتساب +974 70177761» (3163/3171/3183/3191) + the report/short-report hooks (1799/1983) — a personal name + personal number on a public service.
- **Internal roadmap jargon (🟡):** «بانتظار مراجعة مُقيِّم مُرخّص **(المرحلة الخامسة)**» / «(Stage 5)» (material_uncertainty 78/79; evaluate_unified rics_methodology_note 6503/6513) — meaningless to users.
- **Trust-eroding gate framing (🟡):** «هدفها **قياس دقّة** التقدير» (456) + «نتيجة **بحثية** للدعم» (468) read as "we don't know if it's accurate / you're a test subject".
- **Backend emoji remnants (🟡):** the de-emoji sweep (b48) was frontend-only; `data_freshness._render_banner/_render_caveat` still emitted 📅/⚠️ (260-268, 279).

## 3. What this patch does (VALUE-INVARIANT — text/display only; amount/low/high/method/rule untouched)
**index.html (12 edits):** home sub `الفعلية`→`المفتوحة` · disc «التقييم إرشادي»→«التقدير إرشاديّ» · disc credit → «يستخدم بيانات وزارة العدل المفتوحة (CC BY 4.0)» · gate «ما ليس هذا؟» += «وثمّن خدمة مستقلّة غير منتسبة لوزارة العدل؛ تستخدم بياناتها المفتوحة فقط» · gate sub → «نطوّرها بملاحظاتك» · gate note → «معلومة استرشاديّة لدعم القرار» · report GT hook + short-report GT hook → email + «اختياريّ» framing · Terms AR/EN feedback + contact (4 lines) → «فريق ثمّن / Thammen team» + `info@thammen.qa`. **WhatsApp number `70177761` now appears ZERO times site-wide; `info@thammen.qa` ×6.**
**api.py:** subtitle_ar «القطرية الرسمية» → «المفتوحة (CC BY 4.0)».
**evaluate_unified.py:** rics_methodology_note AR/EN drop «(المرحلة الخامسة)»/«(Stage 5)» + ENGINE_VERSION/SPRINT_TAG → b50.
**material_uncertainty.py:** RICS_COMPLIANT_STATUS_PENDING_AR/EN drop the roadmap tag.
**data_freshness.py:** strip 📅/⚠️ from the 4 banner tiers + the caveat (the de-emoji نسق now reaches the backend freshness strings).

## 4. Self-correction recorded (Rule #36)
The «والآراضي» typo flagged in the persona-panel turn was a **misread** of a low-res Arabic glyph in a screenshot — the source (index 455) is correctly «والأراضي». No such typo; not changed.

## 5. Verification — empirical
- py_compile OK (api, evaluate_unified, material_uncertainty, data_freshness, test_b50).
- Isolated `test_sprint_2_22_0b50.py` **32/32** (reads real files + calls the real `data_freshness` / `material_uncertainty` — E14: every fix present, every offender absent).
- **4 sibling re-points (R6/Lesson-2, intent preserved):** a20 20/20 (status string minus tag), a8 43/43 (AVM-disclosure check minus the «المرحلة الخامسة» conjunct), b17 33/33 (GT hook → email), b25 77/77 (short-report GT hook → email).
- **DoD:** aggregator **ALL COUNTS MATCH (395)** · security **15/15** · surface-honesty **45/45** · broad walk **111/111 ALL GREEN** (110→111, +b50; 119.4s).
- **R14 real-Chromium 390×844:** gate sub «نطوّرها بملاحظاتك» + note «معلومة استرشاديّة» + «غير منتسبة لوزارة العدل» render · home sub «مبنيّ على بيانات وزارة العدل المفتوحة» · `info@thammen.qa` ×6 · `70177761` absent · «الفعلية» absent · **0 console errors** (JS parses clean) · **no overflow** (375==375).

## 6. Deployment
`git subtree push --prefix "deploy v2" heroku master` + `git push origin master`.

## 7. Verification curl (post-deploy)
`curl -s https://thammen.qa/ | findstr "info@thammen.qa"` (present) · `curl -s https://thammen.qa/ | findstr "70177761"` (absent) · `/api/health` → engine `…b50…`. 5-anchor value byte-gate must be identical to v222.

## 8. What's NOT in this patch (deferred)
- «تحفظ مادي» → plain-language rename + standards behind ⓘ (RICS-term; needs a design call).
- Full terminology lock (تقدير/تقييم/تثمين + سوقي/سوقيّ shadda) beyond the strings edited here.
- `evaluate_unified` deeper brief text «المصادر الحكومية والإعلانات النشطة» (mild officialness + a listings-vs-«لا أسعار إعلانات» consistency nuance) + `comparable_adjustments` «(RICS Material Uncertainty)» Latin-in-Arabic.
- A full backend-emoji sweep across all engine strings (only the surfaced freshness banner done here).
- The «نبّهني عند الدعم» apartment-waitlist capture (a feature, not copy).
