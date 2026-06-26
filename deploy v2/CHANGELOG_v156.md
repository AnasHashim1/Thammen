# CHANGELOG v156 — Sprint 2.22.0b.75 «توحيد المصطلح: طريقة → منهج» (synonym-unify)

**Engine:** `thammen-sprint2p22p0b75-tariqa-to-manhaj` · **SPRINT_TAG** `2.22.0b.75` · **Date:** 2026-06-27
**Files:** `evaluate_unified.py` (19 method-label tokens + 2 version lines) · `test_sprint_2_22_0b75.py` (new) · `CHANGELOG_v156.md` · `docs/Session_Log.md`
**Class:** 🟢 ENGINE COPY-ONLY / **VALUE-INVARIANT** (`index.html` + `api.py` UNTOUCHED; only method-label/description STRINGS change — never a value/method/rule; the 5-fixture byte-gate identical to v245). The deferred b61 item. Overnight queue #4.

## 1. Why this matters
b61 unified most engine Arabic but **deferred** «طريقة»→«منهج» («widest blast + gender-agreement rewrites»). «منهج» is the RICS-standard rendering of "approach" (it's already the established term — «منهج المقارنة بالمبيعات»), while «طريقة» («method/way») was the lone inconsistent synonym left on the income/cost/refusal surfaces. This unifies them.

## 2. What this patch does (agreement-aware; linguist + lawyer personas APPROVE)
**19 «طريقة» tokens → «منهج»**, each with its adjective/demonstrative/verb flipped feminine→masculine:
- **12 global** «طريقة الدخل»→«منهج الدخل» (the مضاف إليه «الدخل» needs no flip).
- **7 targeted** agreement rewrites: «طريقة التكلفة الإحلالية»→«منهج التكلفة الإحلالية» · «هي الطريقة الأنسب»→«هو المنهج الأنسب» · «هو الطريقة المعيارية»→«هو المنهج المعياريّ» (×2) · «طريقة واحدة معتمدة»→«منهج واحد معتمد» · «بطريقة واحدة»→«بمنهج واحد».
- **1 reword** (line 1972) for the verb-agreement + to avoid a منهج/منهجيّ root-repeat: «طريقة الدخل هنا تأكيد منهجي ولا **تدخل** القيمة» → «منهج الدخل هنا للتأكيد فقط، ولا **يدخل** في القيمة».
- The «منهج الدخل» section title + its cross-reference («انظر قسم "منهج الدخل"») stay consistent. Assertion-guarded sweep (every pattern hit its exact expected count + a final 0-«طريقة» residual guard).

## 3. Verification
- isolated `test_sprint_2_22_0b75.py` **13/13** (E14: 0 «طريقة» remains · the 7 «منهج» masc forms present · the 1972 reword · the cross-ref consistency · version-agnostic version check · b72/b74 markers intact).
- DoD: aggregator **395 MATCH** · security **16/16** · surface honesty **45/45** · broad walk **131/131 ALL GREEN** (130→131) with **1 R6/Lesson-2 re-point** — `test_sprint_2p22p0a4_disclosure_framing.py` (the preserved-per-path-caveat pin «…يحتاج طريقة الدخل» → «منهج الدخل»; the caveat-survives-the-A→D-fold assertion intent preserved, only the synonym unified). **No value/security/methodology assertion weakened.**
- **R14 N/A by construction** — `index.html` git-confirmed UNCHANGED; the frontend renders the method labels identically (the b59/§20.88 precedent).
- Live: the 5-fixture value byte-gate byte-identical + a served-response method label confirmed «منهج الدخل».

## 4. Deployment
```
git subtree push --prefix "deploy v2" heroku master   # from C:/Thammen toplevel
git push origin master
```

## 5. What's NOT in this patch
- `# comment` arrows/box-drawing/`نهج الكلفة` (vs «منهج») harmonization (both فصيح) is out of scope. The EN twins are in the EN-localization sprints (b78+).
