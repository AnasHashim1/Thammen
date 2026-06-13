# CHANGELOG v114 — Sprint 2.22.0b.31 «طيّ TIER-1 للمالك» (DEF-UX11)

> Engine `thammen-sprint2p22p0b31-tier1-howfold` · SPRINT_TAG `2.22.0b.31` · api-health
> `3.1.0-sprint2.22.0b.31`. **🟢 FRONTEND-ONLY / VALUE-INVARIANT** (engine diff = the 2 version-string
> lines; the value `v.amount/low/high` is byte-identical — مبدأ b24 «الرقم واحد للجميع»).
> Files changed: `index.html` (the `show()` results renderer) + `evaluate_unified.py` (version strings) +
> `test_sprint_2_22_0b31.py` (new) + `test_sprint_2_22_0b15.py` (2 stale-pin re-points). Gate-2 = signed by
> delegation (the study `docs/STUDY_persona_simplicity_and_entry_v1.md` + `ISSUES_LOG §4ب-2`, value-invariant
> by construction); Gate-1 = deploy-on-green.

## 1. ما الذي تغيّر
شاشة النتيجة (`show()`): **«موكب التسعة ملاحظات»** + **لوحة الأدلّة الكاملة** → أكورديون واحد **«🔍 كيف وصلنا لهذا
الرقم؟»** (مطويّ افتراضياً، أول أكورديون بعد الرقم). TIER-1 (الرقم) = **النواة:** النطاق + الوسيط + «ليس تقييماً
معتمداً» + سطر جودة-الأدلّة (pill) + زرّ الأكورديون. (تبقى على TIER-1 أيضاً: ملاحظة الحالة + هدم/فخامة + حساسية العمر +
عدد الصفقات + رقاقة tier + رقاقة MUC + سطر المنهجية — قرارية/امتثالية/مشروطة، خارج «التسعة» المسمّاة.)

## 2. لماذا يهمّ (المشكلة المرئية)
الدراسة قاست TIER-1 ≈ **٢١ عنصراً** قبل أن يصل المالك للجواب، و«موكب التسعة» (value-floor · HBU · old-stock ·
cost-triangulation · leadership · age-honesty · resurvey · cost-value-line · market-dispersion) **يدفن الرقم**
ويُسبّب شلل القرار. المالك البسيط يريد **الإجابة**، لا منهجية المحرّك. الموكب + لوحة الأدلّة = الكتلة المهيمنة للحِمل
(الدراسة §0): طيّها خلف نقرة واحدة يخفض الحِمل المرئيّ ~٨٠٪ للجميع دون فقدان أيّ معلومة.

## 3. الجذر (الكود)
`index.html` — كتلة TIER-1 في `show()` كانت تبني الملاحظات التسع كـ`t1+=` (الأسطر ~2203–2224)، ولوحة الأدلّة كانت
أكورديون TIER-2 منفصل «📊 جودة الأدلّة (تفصيل)» (~2244). الـpill (`_evOneRow`) كان أصلاً في TIER-1 منذ b15.

## 4. ما يفعله هذا التعديل
- **frontend (`show()`):** الملاحظات التسع تُبنى الآن في buffer جديد `let how=''` (تبديل بادئة فقط: `t1+=` → `how+=`،
  كل شرط + كل سلسلة HTML **حرفيّ** → القيمة byte-identical). أكورديون واحد
  `_acc('🔍 كيف وصلنا لهذا الرقم؟', how+evidencePanelHtml(d,acc))` يُبنى **أوّلاً** في `t2` (بعد الرقم + بند MUC).
  أُزيل الأكورديون المنفصل «📊 جودة الأدلّة (تفصيل)» (لوحته الكاملة الآن داخل «كيف وصلنا»). `<summary>` المطويّ = العنصر
  الخامس (الزرّ). **لا لوحة مفقودة** — كل ملاحظة + اللوحة قابلة للوصول بنقرة.
- **الحدود (Rule #38، خارج «التسعة»):** ملاحظة الحالة / الهدم / الفخامة (قرارية، مشروطة) + حساسية العمر (b18 §A1،
  مشروطة) + عدد الصفقات (cite-n) + «ليس معتمداً» (امتثال) + الـpill + سطر المنهجية = تبقى على TIER-1.
- **backend:** `evaluate_unified.py` = سطرا الإصدار فقط. `api.py` لم يُمسّ. ترتيب التجميع
  `h=head+alerts+t1+muc+t2+t3+foot` لم يتغيّر (الأكورديون يركب `t2`). مسار الرفض داخل `if(hasValuation)` → byte-identical.

## 5. التحقّق — الدليل التجريبيّ
- **معزولة** `test_sprint_2_22_0b31.py` **36/36** (الـ`how` buffer + الأكورديون الواحد + التسعة في `how` لا `t1` +
  لا تكرار في `t1` + النواة الخمسية باقية + condition/teardown/luxury/age-sensitivity/moj-n باقية + لوحة الأدلّة
  لم تُحذف [showConfirm/showReport] + لا تعديل على v.amount/low/high + ترتيب التجميع).
- **re-points** `test_sprint_2_22_0b15.py` **50/50** (السطر 72: الأكورديون المنفصل → الطيّة الموحّدة؛ السطر 98:
  condition تبقى t1 / value_floor+hbu → how — R6/الدرس-2: pins بنيويّة أبطلها DEF-UX11 عمداً).
- **الإخوة بلا re-points:** b16 38/38 · b18 26/26 (حساسية العمر باقية t1) · b20 69/69 · b2.2 26/26 · b26 33/33 ·
  b29 32/32.
- **DoD** (PYTHONIOENCODING=utf-8): aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface-honesty
  **45/45** · broad walk **99/99 ALL GREEN** (198.5s).
- **R14 — Chromium حقيقيّ 390×844 على حمولة امريخ cost-led الحيّة (`.basket/f_marikh.json`):** الرقم في TIER-1 =
  النطاق ٢٬٤٠٠٬٠٠٠–٥٬٤٠٠٬٠٠٠ + الوسيط + «ليس معتمداً» + الـpill + الزرّ + الحالة + عدد الصفقات؛ **الموكب غائب عن الرقم**
  (لا dispersion/cost-value/⚖️ في الـcalc-block)؛ أكورديون «كيف وصلنا» = **أوّل**، **مطويّ افتراضياً**، جسمه (1081 حرف)
  يحمل الموكب كاملاً (⚖️ leadership · 🕰️ age-honesty · 🏗️ cost-value · 📊 dispersion · مكوّن الأرض) + لوحة «جودة الأدلّة»
  + شرح المقارنات؛ **صفر console errors/warnings**؛ **بلا overflow** (scrollW 390==clientW 390، maxRight 370<390
  مطويّاً ومفتوحاً)؛ القيمة byte-identical (2.4M / 2.4M–5.4M).

## 6. النشر
```
git add index.html evaluate_unified.py test_sprint_2_22_0b31.py test_sprint_2_22_0b15.py CHANGELOG_v114.md docs
git commit -m "Sprint 2.22.0b.31 (DEF-UX11): TIER-1 9-note fold into «كيف وصلنا» accordion"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. تحقّق ما بعد النشر (curl، Rule #61 — browser-UA)
```
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" https://thammen.qa/api/health        # → b31 / v202
curl -s -A "..." -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"
# امريخ → 2,400,000 cost-led byte-identical؛ + GET / يحمل «كيف وصلنا لهذا الرقم؟» + let how=''
```

## 8. ما ليس في هذا التعديل (حدّ النطاق)
- **«التسعة المسمّاة + لوحة الأدلّة» فقط** طُويت. الطيّة الكاملة للدراسة §3 (21→5) — نقل **رقاقة tier** لرأس الأكورديون،
  إخفاء **كلمة MUC** غير-الحرجة، طيّ **عدد الصفقات/المنهجية** — = micro لاحق (يمسّ pins امتثال b15 42/99 → re-points
  إضافية؛ خارج النطاق المسمّى). الموكب = الكتلة المهيمنة، وقد طُوي.
- **DEF-UX12** (الكثافة المقودة بالدور — بثّ `audience` يحكم حالة الطيّ مالك→مطويّ / متخصّص→مفتوح) = المفصل التالي
  (يحتاج تعديل خادم additive). اليوم: الأكورديون مطويّ للجميع.
- تنبيهات فوق الرقم (multi-QARS / subtype-zoning / tower-pair) لم تُمسّ (qualifiers، مسار مختلف). مسار الرفض byte-identical.
- لا تغيير محرّك / منهجيّ. القيمة ثابتة عبر كل الأدوار (b24).
