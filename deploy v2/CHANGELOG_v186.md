# CHANGELOG v186 — Sprint 2.22.0b.105 «توحيد وتثبيت لغة التطبيق» (R3 — the register lock, Gemini r11)

**Engine:** `thammen-sprint2p22p0b105-language-register-lock` · **SPRINT_TAG** `2.22.0b.105`
**Date:** 2026-07-06 · **Files:** `index.html`, `evaluate_unified.py`, `material_uncertainty.py`, `data_freshness.py`, `scope_of_service.py` (+ `test_sprint_2_22_0b105.py`; 14 R6 re-points)
**Class:** 🟢 COPY/REGISTER-ONLY / VALUE-INVARIANT (amount/low/high/method/rule untouched — the 5-fixture villa byte-gate holds by construction). PO-signed Gate-2 copy (the two amendments to earlier signed strings signed explicitly this session).

---

## 2. Why (PO: «هل سنتخلص من الألفاظ العامية والعبارات غير الاحترافية؟» — نعم)

A PO-signed, deterministic term-flip across the user-facing surfaces (the b54 term-lock pattern applied to
REGISTER). The candidate list went to Gemini (round r11, PO paste-lane) and was **adjudicated per Rule #54**:
14 accept · 8 accept-modified · 5 reject. Recorded in `docs/CONSULT_gemini_r11_terms.md`.

## 3. What this patch does

**SIGNED (PO signed the two amendments to earlier signed copy this session):**
- **«تحفظ مادي» / «التحفظ المادي» → «عدم اليقين الجوهري»** — the RICS VPGA 10 «Material Valuation
  Uncertainty» rendered as financial stinginess to the ordinary owner. Applied to the MUC banner
  (material_uncertainty.py — 3 levels, unified to حرج/مرتفع/متوسط, previously جوهري/عالٍ inconsistently),
  the formal clause (the English standard name «Material Valuation Uncertainty» rides it), the chip +
  the fold title (index.html), and 7 engine note bodies (evaluate_unified.py). The EN twin «Material
  uncertainty» is unchanged.
- **«البناء المُهلَك / مُهلَكاً» SOFTENED on the OWNER short-report** («قيمة البناء بعد الإهلاك» /
  «بعد إنقاص استهلاكه» — the owner read «مُهلَك» as «آيل للسقوط») — the DRC **professional basis** line
  (the full report + the result screen + the DRC mechanics) **KEEPS «مُهلَك»** (the register split the PO
  signed: owner plain, specialist precise).

**ACCEPTED replaces:** «معامل الاحتفاظ» → «نسبة القيمة المتبقية للبناء» · «حوض المقارنة الموسَّع» → «نطاق
المقارنة الموسَّع» · «مؤشّر مزامنة البيانات» → «تاريخ تحديث بيانات وزارة العدل» (no double «وزارة العدل») ·
«الاستخدام الأمثل» → «أعلى وأفضل استخدام» (RICS Highest-and-Best-Use) · «نافذة N شهراً» → «صفقات آخر N
شهراً» (engine + scope).

**REJECTED (locks held, #54):** «شريحة»→«فئة» (locked lexicon: size brackets + the b100 strata) · «الجبريّ»
→«القسري» (b56-signed) · «سجلّ»→«نظام» العناوين · the cap-rate gloss (OURS keeps «صافي» + Qatar 5–6%, b61) ·
«بصمة المحتوى»→«الرمز الأمني» (Gemini's is misleading — it is tamper-evidence, not a secret code).

## 4. VALUE-INVARIANT

Copy/register only; no value/method/rule change. `api.py` untouched. Verified live: the MUC chip renders
«عدم اليقين الجوهري:» while the amount stays 2,400,000 (Marikh); the register split confirmed (result
screen keeps «البناء المُهلَك», owner short report shows «قيمة البناء بعد الإهلاك»).

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b105.py` **21/21** (the flip applied + the rejected renames NOT applied +
  the register split + the locks held) · py_compile 4/4 · `node --check` OK.
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **161/161
  ALL GREEN** — **14 R6/Lesson-2 re-points** (a14/a21/a22/b15/b37/b39/b52/b56/b76/b83/b92/b99 +
  test_material_uncertainty; each pinned a term the register lock intentionally changed; the underlying
  element persists — **zero value/security/methodology assertion weakened**).
- **R14 real preview 375×812** (DOM-measured, AR + EN): result screen MUC chip «عدم اليقين الجوهري:» /
  EN «Material uncertainty:»; DRC mechanics «نسبة القيمة المتبقية للبناء»; «البناء المُهلَك» kept on the
  specialist result screen; owner short report softened («قيمة البناء بعد الإهلاك»); «مرتكز» kept; amount
  2,400,000 unchanged; **0 console errors**; no horizontal overflow.

## 6. Deployment

- `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112).

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.105`.
- served `index.html`: «عدم اليقين الجوهري:» present · «تحفظ مادي» absent (live rendered strings) ·
  «نسبة القيمة المتبقية للبناء» present.
- `/api/freshness` `banner_ar` → «تاريخ تحديث بيانات وزارة العدل: آخر سجلّ رسميّ — …».
- the 5-fixture villa byte-gate byte-identical to v275 (browser-UA #61).

## 8. What's NOT in this patch

- The Layer-2 question-form fold titles + the neighborhood price-position line + the interstitial/sticky-bar
  (deferred from R2). The remaining EN backend `_en` twins (§20.113 residue). The RICS disclosures = **S1
  (b106)** — next.
