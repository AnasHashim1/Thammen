# Thammen v2.0 — CHANGELOG

تاريخ الإصدار: 2026-05-09

## الفلسفة

ثمّن v1 كان "محرك تقييم". ثمّن v2 هو **"نظام معلومات شفّاف"** — يجمع البيانات
الحكومية والإعلانات النشطة، يعرض كل خطوة منطقية بمصدرها، ويترك القرار للعميل.

**الموقع التنافسي**: ليس مُقيِّماً معتمداً (لا يحتاج رخصة RICS)، بل أعلى مستوى
من الشفافية المعلوماتية في السوق القطري.

---

## التغييرات الرئيسية

### ١. حذف نظام `verdict` (حماية قانونية)

**قبل**: النظام يصدر أحكاماً شرائية: `BARGAIN`/`OVERPRICED`/`REJECT`/`INSPECT`.
هذه أحكام تقييمية تتطلب رخصة وتفتح الباب لمسؤولية قانونية.

**بعد**: النظام يصف الموضع: `at_market`/`above_market`/`below_market`/
`far_above_market`/`far_below_market`. وصف فقط، بلا توصية.

```python
# v1 (خطر قانونياً):
ev.verdict == 'BARGAIN'  # هذا قرار، يحتاج رخصة

# v2 (آمن):
ev.market_position['position_label'] == 'below_market'  # هذا وصف، لا قرار
ev.market_position['description_ar']  # شرح موضوعي
```

الحقل `verdict` محتفظ به فارغاً للتوافق مع الـ frontend القديم.

### ٢. تكاليف مفصّلة بدل `opex_ratio` المسطّح

**قبل**: `opex_ratio = 0.23` (افتراض ثابت 23% للجميع).

**بعد**: تكاليف منفصلة وقابلة للتحقق:
- **رسوم الخدمات**: من قاعدة `service_charge_db.py` (per-precinct)
- **الشغور**: 8.5% (شهر/سنة) — معدّل قابل للتعديل
- **الصيانة**: 0.5% من قيمة العقار (للمباني الجديدة)
- **الإدارة**: 0% (ذاتية) أو 5-8% (وكيل)

النتيجة: عائد صافٍ دقيق + تحليل حساسية يُظهر تأثير ارتفاع رسوم الخدمات أو
انخفاض الإيجار.

### ٣. ملف `service_charge_db.py` (جديد)

قاعدة بيانات per-precinct مُتحقَّقة من إعلانات FGRealty الفردية:

| المنطقة | الـ Precinct | ر.ق/م²/شهر | المصدر |
|---|---|---|---|
| اللؤلؤة | Porto Arabia | 15 | FGRealty AS-001032 + AS-003429 |
| اللؤلؤة | Qanat Quartier | 14 | FGRealty AS-000750 |
| لوسيل | Fox Hills | 10 | FGRealty AS-002329 |
| لوسيل | Marina | 14 | FGRealty AS-002710 |
| لوسيل | Al Kharayej | 14.5 | FGRealty AS-003398 |

كل سجل له: `source` (المرجع)، `source_date`، `confidence` (verified/reported/
estimated)، و `notes`.

البحث هرمي: مبنى → precinct → منطقة → fallback عام.

### ٤. ملف `market_position.py` (جديد)

استبدل `assemble_verdict`. واجهة وصفية بحتة:

```python
pos = compute_position(
    listing_price=2_400_000,
    benchmark_price=2_174_000,
    benchmark_source='MoJ الوكير 400-600م² فلل',
    benchmark_n=71,
)
# pos.position_label = 'above_market'  (وصف، لا حكم)
# pos.description_ar = 'السعر أعلى من المرجع بـ 10.4%...'
# pos.caveats = []  (تحفظات إن وُجدت)
```

### ٥. ملف `reasoning_trace.py` (جديد)

سلسلة الحقائق الكاملة لكل تقييم — أهم اكتشاف منهجي في v2:

```python
trace = ReasoningTrace(valuation_id='THM-20260509-001')
trace.add('ground_truth',
          fact='MoJ سجّلت 22 صفقة في الخيسة، الوسيط 5,048 ر.ق/م²',
          source='data.gov.qa weekly bulletin',
          source_date='2026-05-08',
          confidence='high')
```

كل خطوة لها مصدر. كل مصدر له تاريخ. كل تاريخ يكشف الحداثة.
هذا ما يميّز ثمّن قانونياً (شفافية كاملة) وتجارياً (لا أحد آخر يفعل هذا).

### ٦. حقل `disclaimer` دائم في كل استجابة API

نص قانوني واضح يوضّح أن ثمّن:
- **يجمع** البيانات الحكومية والسوقية
- **ليس** تقييماً معتمداً وفق RICS أو IVS
- للأغراض الرسمية (قروض، محاكم) يلزم مُقيِّم معتمد

### ٧. نقاط API جديدة

- `GET /api/disclaimer` — إخلاء المسؤولية الرسمي (ar + en)
- `GET /api/about` — معلومات النظام والمصادر
- `GET /api/health` — يضيف الآن حقل `version: "2.0.0"`

### ٨. تصحيح خطأ إملائي

"تزوير R1/R2/R3/C" → "تنظيم R1/R2/R3/C" في `LABEL_FIXES` (api.py).
كان خطأ مطبعي في v1.

---

## التوافقية الخلفية (Backward Compatibility)

✅ كل الـ API الحالية تعمل بدون تعديل.

✅ `verdict` يبقى موجوداً كحقل في `PropertyEvaluation` (فارغ في v2).

✅ `compute_rental_analysis(opex_ratio=0.23)` يعمل كما كان (legacy mode).
   إذا لم يُمرَّر `opex_ratio`، النظام يحسب بالتفصيل تلقائياً.

✅ `verdict_ar` في rental_analysis يبقى — لكن محتواه الآن وصفي (yield_position).

⚠️ **اختبار واحد فقط** (test_basic_yield) احتاج تمرير `opex_ratio=0.23` صراحة.
   الباقي يعمل بدون تعديل.

---

## ملخص الأرقام للؤلؤة (مثال تطبيقي)

شقة 145م² في Porto Arabia، إيجار 11,000 ر.ق/شهر، قيمة 1.89M ر.ق:

| البند | v1 (مسطّح) | v2 (مفصّل) |
|---|---|---|
| تكلفة موحَّدة | 23% × 132K = 30,360 | تكاليف منفصلة |
| رسوم خدمات | (مدمجة) | 26,100 (verified FGRealty) |
| شغور | (مدمج) | 11,220 (8.5%) |
| صيانة | (مدمجة) | 9,458 (0.5% × 1.89M) |
| إدارة | (مدمجة) | 0 (ذاتية) |
| **الإجمالي** | 30,360 | 46,778 |
| **الإيجار الصافي** | 101,640 | 85,222 |
| **العائد الصافي** | 5.37% | **4.51%** |

الفرق 86 نقطة أساس — كان مخفياً في النموذج المسطّح.

---

## الإحصائيات

| المقياس | v1 | v2 |
|---|---|---|
| إجمالي الأسطر | 5,227 | 5,950 |
| ملفات Python | 8 | 11 |
| Endpoints API | 3 | 5 |
| اختبارات | 41 | 75 |
| تكاليف مفصّلة | 1 (مسطّح) | 4 |
| Verdict words | 5 | 0 |
| Description sources | 0 | في كل تقييم |

---

## الترقية من v1

```bash
# بسيط جداً — استبدل الملفات والـ API يبقى كما هو
cp api.py evaluate_property.py /path/to/production/
cp service_charge_db.py market_position.py reasoning_trace.py /path/to/production/
# لا تغيير في deploy.sh، لا migration للـ DB
```

**لا breaking changes** للـ frontend — كل ما يقرؤه v1 يستمر يعمل،
مع إضافة حقول جديدة (`market_position`, `reasoning_trace`, `disclaimer`)
يمكن للـ frontend استخدامها تدريجياً.
