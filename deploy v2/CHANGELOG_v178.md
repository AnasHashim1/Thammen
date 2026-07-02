# CHANGELOG v178 — Sprint 2.22.0b.97 «وعي-النوع للأرض» (raw-land awareness)

**Engine:** `thammen-sprint2p22p0b97-raw-land-awareness` · **SPRINT_TAG** `2.22.0b.97` · api-health `3.1.0-sprint2.22.0b.97`
**Date:** 2026-07-02 · **Files:** `index.html` (5 land branches/gates) · `reasoning_trace.py` (raw_land known_unknowns) · `evaluate_property.py` (raw_land unknowns mapping) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b97.py` (new)
**Class:** 🟢 FRONTEND + engine-copy / **VALUE-INVARIANT** (the valuation engine — amount/low/high/method/rule — is UNTOUCHED; only display copy + asset-type gating + the display-only `known_unknowns` list change). **Gate-2** (user-facing copy) — signed «نعم» + lawyer/linguist personas.

## 1. Why this matters
ثمّن كان **يعامل الأرض الفضاء معاملة الفيلا**: آلة «حسّن التقييم» وكل نسخها بُنيت فيلا-أوّلاً ولم تُفرَّع للأرض. جردٌ **مُقاس بالعرض الفعليّ** لأرض الوعب (PIN 55010236، ٧٫١م) أظهر ٦ تسرّبات مفهوم-مبنى تظهر فعلاً على الأرض:
1. شاشة النتيجة — زرّ «حسّن التقييم — **أضف تفاصيل مبناك**».
2. شاشة النتيجة — إشعار «**التقييم يفترض بناءً نموذجياً**» + «الحالة/التشطيبات» (يناقض تسعير الأرض بالمتر).
3. النتيجة + الشامل — «ما لا نعرفه»: **حالة العقار الداخلية (تشطيبات/صيانة/تكييف)** · **تاريخ آخر تجديد (سباكة/كهرباء)** · **الطابق** (المحرّك كان يسقط للأرض إلى فرع `apartment` الافتراضيّ).
4. المختصر §٣ «الخلاصة العملية» — «**بيتك · تجديد كامل · دخل إيجار · العمر الحقيقيّ**».
5. المختصر §٢ — «التقدير المركزي **لبيتك**».
6. الشامل DEF-12 — سطر تقديم «ثلاثة أرقام: قيمة **بيتك** · كلفةُ **إعادة بنائه**» — يناقض صفّه الأرضيّ «≡ قيمة الأرض — لا مكوّن بناء».

## 2. Root cause
- **Frontend:** الزرّ (1) + إشعار «نقص التفاصيل» (2 — `!v.building_substantiality` بلا بوّابة نوع) + §٣ (4) + §٢ (5) + DEF-12 intro (6) كانت غير مُقيَّدة بنوع الأصل. (بطاقة الهندسة الأخرى مُقيَّدة أصلاً بـ`_b2IsBuilding` — ليست التسرّب.)
- **Engine:** `evaluate_property.py:2020-2025` يربط asset_type → `unknown_asset_type` لكن بلا فرع `raw_land` → يسقط للافتراضيّ `'apartment'` → `reasoning_trace.add_standard_unknowns` يعطيه مجاهيل الشقق (داخليّة + طابق/إطلالة).

## 3. What this patch does
- **(1) `index.html` show():** زرّ TIER-3 «أضف تفاصيل مبناك» مُغلَق بـ`if(d.asset_type!=='raw_land')` — الأرض ليس لها ما يُحسَّن في شاشة تحسين كلّها حقول مبانٍ (الخيار أ الموقَّع). «التقرير المختصر / PDF» يبقى.
- **(2) `index.html` show():** إشعار «يفترض بناءً نموذجياً» مُغلَق بإضافة `&&d.asset_type!=='raw_land'`.
- **(3) `reasoning_trace.py`:** فرع `raw_land` مبكّر في `add_standard_unknowns` → ٥ مجاهيل أرض (تربة/جيوتقنيّ · التزامات قانونية · خدمات ومرافق · إمكان الفرز وموافقة التخطيط · ارتفاقات/قيود) بلا أيّ مفهوم مبنى؛ + `evaluate_property.py` يربط `RAW_LAND/raw_land → 'raw_land'`.
- **(4) `index.html` showShortReport():** §٣ بفرع `cs==='land'` — نصيحة بائع/مشترٍ بمحرّكات الأرض (زاوية/واجهة/إمكان فرز · «أرضك» · «تأكّد من حدود القطعة وتصنيفها ومساحتها المسجّلة»)؛ تُسقط تجديد/دخل إيجار/العمر؛ تُبقي سقوف ×1.10/×1.30 + «بيان وزارة العدل».
- **(5) `index.html` showShortReport():** §٢ «التقدير المركزي **لأرضك** اليوم» عند `cs==='land'`.
- **(6) `index.html` showReport():** DEF-12 intro بفرع أرض — «رقمان لأرضك: القيمة السوقية التقديرية · وتقديرٌ عند البيع السريع (×٠٫٩٠). ولأنها أرض فضاء، فقيمة الكلفة هي قيمة الأرض نفسها — لا مكوّن بناء.» → يتّسق مع صفّ التكلفة الأرضيّ (التناقض زال).

**أذرع الفيلا/المباني UNCHANGED** في كلّ موضع (regression-safe): الزرّ + الإشعار + §٣ villa + §٢ «لبيتك» + DEF-12 «ثلاثة أرقام… بيتك» تبقى كما كانت لغير الأرض.

## 4. Personas (توجيه المالك الدائم)
- **المحامي — APPROVE:** إسقاط ادّعاءات المبنى على الأرض يرفع الدفاعية (ادّعاء مبنى على أرض = تضليل)؛ مجاهيل الأرض الجديدة (تربة/فرز/ارتفاقات/خدمات) تحفّظات صادقة تُقلّل المسؤولية؛ «إرشادية — القرار قرارك» + السقوف + «بيان العدل» مُبقاة؛ لا ادّعاء جديد ولا إخلاء مسؤولية مُضعَّف.
- **اللغويّ — APPROVE:** فصحى مبسّطة متّسقة («لأرضك» · «إمكان الفرز» · «صرف صحّي» · «ارتفاقات» · دوال «رقمان»)؛ لا عامّية/ركّة.

## 5. Verification — empirical
- **Isolated `test_sprint_2_22_0b97.py`: 29/29** — المحرّك (real `add_standard_unknowns`: land 0-building-leak · villa/apt regression) + `evaluate_property` mapping + قراءة index.html الفعليّ (الزرّ مُغلَق · الإشعار مُغلَق · §٣ فرع أرض بلا مبنى + أذرع الفيلا سليمة · §٢ «لأرضك» · DEF-12 فرع أرض) + value-invariance (لا حساب على v.amount عدا ×0.90/1.10/1.30؛ لا إسناد إلى amount/low/high).
- **DoD:** aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · **broad walk 153/153 ALL GREEN** (152→153, **صفر re-points**).
- **py_compile** 3/3 · **node --check** على الـinline JS OK.
- **R14 real-Chromium 390×844** (على الحمولة الحيّة، + محاكاة مجاهيل b97): الأرض (نتيجة + مختصر + شامل) = **صفر تسرّب مبنى**؛ DEF-12 «رقمان لأرضك» يتّسق مع صفّ «≡ قيمة الأرض»؛ §٣ «تتميّز أرضك (زاوية/واجهة/فرز)»؛ الفيلا (Marikh) = زرّ + نصيحة + DEF-12 «بيتك» سليمة (لا انحدار)؛ **0 console errors**.
- **VALUE-INVARIANT:** كود التقييم UNTOUCHED (عدا سطرَي الإصدار)؛ بوّابة البايت الخماسية byte-identical بالبناء.

## 6. Deployment
`git push origin master` (backup FIRST) → `git subtree push --prefix "deploy v2" heroku master` (Rule #43; backgrounded).

## 7. Verification curl (post-deploy)
`/api/health` → engine b97. Live land smoke (PIN "55010236"): `reasoning_trace.known_unknowns` = land-specific (0 building terms) · served `index.html` carries `d.asset_type!=='raw_land'` on the CTA + notice · «رقمان لأرضك» + §٣ «تتميّز أرضك». 5-fixture value byte-gate byte-identical to v177.

## 8. What's NOT in this patch (deferred / flagged earlier)
- **الموضع ب (شاشة تحسين خاصّة بالأرض):** لم يُبنَ — الخيار (أ) أخفى المدخل. لو أراد المالك تصحيح المساحة/السعر/الواجهة للأرض لاحقاً = سبرنت منفصل.
- **بطاقة إمكان-التطوير (max-buildable) للأرض:** أُخفيت مع الإشعار؛ إعادة تأطيرها كـ«الحدّ الأقصى المسموح للبناء — إمكان تطوير» (بلا «يفترض») = خيار لاحق.
- **تكرار سطر العقار** «أرض فضاء · أرض في الوعب — PIN … · الوعب» (أرض×2/الوعب×2) — نقطة تجميل منفصلة.
- **مضيف الـQR/التحقّق** = `herokuapp.com` بدل `thammen.qa` (النصّ يقول thammen.qa؛ الخادم يوفّر `verification_url` مُعلّماً) — إصلاح علامة منفصل.
- **شارة الفرز (b95)** تبقى صامتة على هذه القطعة (`plot_dims_m=None`) — يفتحها اشتقاق الواجهة الهندسيّ المؤجَّل (م٢).
- الشامل الرقيق للأرض الثين (n=8 < عتبة الشبكة E11) بلا جدول أدلّة — سلوك E11 المقصود.
