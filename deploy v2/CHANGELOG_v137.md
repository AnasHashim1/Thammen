# CHANGELOG v137 — Sprint 2.22.0b.56 «تشذيب اللغة والواجهة» (language + interface polish)

> Engine `thammen-sprint2p22p0b56-language-interface-polish` · SPRINT_TAG `2.22.0b.56` · api-health
> `3.1.0-sprint2.22.0b.56`. **🟢 FRONTEND-ONLY / VALUE-INVARIANT** — `index.html` copy + structure only;
> engine = the 2 version-string lines; `api.py` + the valuation engine UNTOUCHED.
> **Files changed:** `index.html` · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b56.py`
> (new) · `test_sprint_2_22_0b25.py` · `test_sprint_2_22_0b17.py` · `test_sprint_2_22_0b19.py` ·
> `test_sprint_2_22_0b26.py` · `test_sprint_2_22_0b50.py` · `test_sprint_2_22_0b54.py` (R6 re-points) ·
> this CHANGELOG. Date: 2026-06-18.

## 1. Why this matters

After the lawyer/أديب/لغوي + 10-persona language review and the PO's gate/«العدل» screenshots, the PO
directed: «نفذ الاصلاحات على التقرير المختصر والمفصل وعلى الواجهة ثم انشر». b56 implements the agreed,
value-invariant FRONTEND fixes across the three surfaces:

- **الواجهة (interface):** the consent gate's heaviest framing (the beta sub-line + the «اعرف المزيد عن
  النسخة التجريبية» fold of 5 cards) overwhelmed the first frame; and the home page repeated «العدل» so
  often it read «كأننا نمثلهم» (as if we represent the MoJ).
- **التقرير المختصر (short report):** colloquial/loose register (الزبدة · سعر عادل · وش لو · شيت · «لك
  وعليك») read informal for a credibility document.
- **التقرير المفصّل (detailed report):** the forced-sale label used Latin «×0.90» and an unguarded label.

## 2. What this patch does (frontend, value-invariant)

**GATE (`index.html`)** — removed the beta sub-line «نسخة تجريبية مجّانيّة بالدعوة — نطوّرها بملاحظاتك…»
and the entire `<details class="bg-more">` «اعرف المزيد» fold (the 5 cards). The first frame is now: title
→ consent note «… وليست تقييماً معتمداً. التفاصيل الكاملة وحدود الخدمة في «الشروط»…» → the affirmation →
the CTA → the Terms link → the (unchanged) English fold. `role="dialog"` + affirmative consent unchanged.
**The moved disclosures are PRESERVED in Terms §2 (AR + EN), not lost:** «وثمّن خدمة مستقلّة غير منتسبة
لوزارة العدل؛ تستخدم بياناتها المفتوحة فقط. ويغطّي الفلل والأراضي فقط … ولا يأخذ بعدُ حالة العقار الداخلية
وتشطيباته — لذلك قد ينخفض السعر الفعليّ نحو قيمة الأرض … أو يتجاوز التقدير …» + the EN twin.

**HOME (`index.html`)** — «العدل» reduced from 4 mentions to **2** (within the PO's «مرة أو مرتين بالكثير»):
the redundant `hsub` («مبنيّ على بيانات وزارة العدل المفتوحة» → «تقييم سوقيّ آليّ للفلل والأراضي في قطر»)
and trust-step 2 («نحلّل صفقات العدل» → «نحلّل الصفقات المسجّلة») dropped it; the two legitimate credits
KEPT — the `hcred` trust line «من صفقات وزارة العدل المسجّلة — لا أسعار إعلانات.» + the engine recency line.

**SHORT REPORT (`showShortReport`)** — formal register (value-invariant copy): الزبدة→**الخلاصة** (head +
§3 + the legal caveat) · «سعر عادل لبيتك اليوم»→**«التقدير المركزي لبيتك اليوم»** · «وش لو؟»→**«ماذا لو؟»** ·
«بناء أخذ نصيبه من العمر»→**«بناءٌ مُهلَكٌ بحسب عمره»** + «— لك وعليك» **deleted** («غير عادلة»→«غير منصِفة»)
· «شيتات موثَّقة … كل شيت جديد»→**«كشوف تقييم موثَّقة … كلّ كشفٍ جديد»**.

**DETAILED REPORT (`showReport`)** — the DEF-12 forced-sale row → a **guarded label** «قيمة البيع الجبريّ
الإرشاديّة (×٠٫٩٠ — ليست تصفية معتمدة)» + the note in Arabic-Indic «عُرفٌ سوقيٌّ ×٠٫٩٠ … الأساس: القيمة
التقديريّة المركزيّة × ٠٫٩٠.» (was the Latin «×0.90» in `<span dir="ltr">`). «ليست تقييم تصفية معتمداً» kept.

**`evaluate_unified.py`** — `ENGINE_VERSION`/`SPRINT_TAG` → b56 (the 2 lines only).

## 3. Value-invariance contract

The ×0.90 forced-sale math (`Math.round((v.amount||0)*0.90)`) and every figure are byte-identical; only
copy/labels/structure changed. The b55 note-clusters are untouched (verified). `api.py` + the engine
untouched → the 5-fixture value-invariance gate is byte-identical to v227 by construction.

## 4. Verification — empirical evidence

- **Isolated** `test_sprint_2_22_0b56.py` — **30/30** (gate trim + Terms-preservation + home «العدل»≤2 +
  short-report register + forced-sale guarded label/Arabic-Indic + value-invariance + CC-BY kept + b55
  no-regression + engine format).
- **R6/Lesson-2 re-points (test-only, intent preserved):** b25 **77/77** (الزبدة→الخلاصة · شيت→كشف · وش
  لو→ماذا لو · «لك وعليك» dropped) · b17 **33/33** + b19 **25/25** + b26 **33/33** (forced-sale guarded
  label + تشكيل) · b50 **32/32** (gate sub-line removed; «غير منتسبة» relocated to Terms) · b54 **44/44**
  (gate fold removed; terminology lock «تقييم» still holds, old «تقدير» absent; condition-limit moved to
  Terms). **Zero value/security/methodology assertion weakened.**
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **ALL COUNTS MATCH** · security
  `test_sprint_2p16p17_security.py` **15/15** · surface `test_sprint_2p22p0a3_surface_honesty.py` **45/45**
  · broad walk `2p22p0_pre/run_regression_2p22p0a.py` **115/115 ALL GREEN** (114→115, +b56; 138.2s).
- **R14 live Chromium 390×844** (served `index.html` + real `.basket/f_marikh.json` cost-led payload):
  **GATE** → bg-more fold + beta sub-line GONE; consent note + ack + CTA (bottom 565 ≤ 844, above the fold)
  + Terms link KEPT; card scrollHeight 495 ≤ 92vh (fits). **HOME** → hsub/step-2 cleaned, hcred kept,
  «العدل» count = **2**, no overflow. **SHORT** → all 6 register fixes verified, «ليس تقييماً معتمداً»
  kept, value **٢٬٤٠٠٬٠٠٠** byte-identical, no overflow. **DETAILED** → guarded forced-sale label + «×٠٫٩٠»
  Arabic-Indic, old Latin «(×0.90)» gone, «ليست تقييم تصفية معتمداً» + CC BY 4.0 kept, the b55 clusters
  «حول الرقم/العقار/البيانات» intact, value byte-identical, no overflow. **0 console errors/warnings.**

## 5. Deployment

```
cd /d "C:\Thammen"
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/CHANGELOG_v137.md" "deploy v2/test_sprint_2_22_0b56.py" "deploy v2/test_sprint_2_22_0b25.py" "deploy v2/test_sprint_2_22_0b17.py" "deploy v2/test_sprint_2_22_0b19.py" "deploy v2/test_sprint_2_22_0b26.py" "deploy v2/test_sprint_2_22_0b50.py" "deploy v2/test_sprint_2_22_0b54.py"
git commit -m "Sprint 2.22.0b.56: language + interface polish (gate trim · home العدل · short/detailed register) (value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy, browser-UA — Rule #61)

```
curl -s https://thammen.qa/api/health | findstr /C:"2.22.0b.56"
curl -s https://thammen.qa/ | findstr /C:"اعرف المزيد"   (expect: NOT present)
```
Plus the live 5-fixture value-invariance gate (browser-UA POST): 54/541/6 2.4M cost_led · 56/647/6 3.8M
geo_full · 55/296/13 2.6M e25 · 56/565/21 2.4M matched · 52/903/90 refusal — all byte-identical to v227.

## 7. What's NOT in this patch (deferred)

- **Engine-emitted string polish (b57 candidate):** the لغوي review also flagged ENGINE-emitted strings
  (e.g. «مُخترَع» phrasing, broad Arabic-Indic number-unification of computed figures, grammar
  «غير معروفة»→«غير معلوم», engine effective-date تعريب). These live in `evaluate_unified.py` / engine
  modules, need their own value-byte-gate, and are a separate single-purpose pass (#38). b56 is
  frontend-only by design.
- **No engine / value / methodology change** — `api.py` + the engine untouched; value-invariant.
- **CC BY 4.0 MoJ attribution on the results page is UNTOUCHED** (legally mandatory, a25/R13).
