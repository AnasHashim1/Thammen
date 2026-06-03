# Sprint 1.b — Thammen AVM (Corrected)

## التسمية المنهجية الصحيحة

> **AVM = Automated Valuation Model**
> **Sales Comparison-led with Three-Approach Reconciliation**
> **(تقدير آلي يقوده مقارنة المبيعات، مع توفيق ثلاثي الطرق)**

هذه فئة معترف بها في RICS تحت "Insight Paper: AVMs in Property Valuation". ليست تقييماً معتمداً، لكنها أداة منهجية صالحة للأغراض الاسترشادية والاستثمارية.

## ما الذي تصلحه هذه النسخة عن Sprint 1.a

Sprint 1.a خلط ثلاث طرق بأوزان متساوية → 2.9M على المريخ (خطأ).
Sprint 1.b يطبّق المنهجية الصحيحة:

| الطريقة | الدور في النظام |
|---|---|
| المقارنة (مع توسيع جغرافي عند الحاجة) | **القيمة الأساسية** — RICS VPS 4 + VPS 4 §7 |
| التكلفة الإحلالية | **تأكيد منهجي** — لا تدخل في القيمة |
| الدخل | **تأكيد منهجي** — لا يدخل في القيمة (للسكني) |
| التوفيق (Reconciliation) | **بيان شفاف** يقارن الطرق |

## النتيجة على المريخ 54/541/6 (إيجار 14K، طابقين)

| الجانب | Sprint 1.a (خطأ) | Sprint 1.b (مُصحَّح) |
|---|---|---|
| القيمة | 2,900,000 ر.ق | **4,500,000 ر.ق** ✓ |
| الطريقة | blended_3way | comparison_widened |
| n المقارنة | 1 (شريحة فقط) | 42 (بعد توسيع جغرافي) |
| التكلفة كتأكيد | غير معروضة بدور واضح | 4.16M (فارق -7.5% فقط) |
| الدخل كتأكيد | مُرجَّح خطأً | 3.23M (فارق -28% — يعكس انخفاض العائد للسكني) |
| التوفيق | غير موجود | "تباين كبير — سكني نقي وليس استثماري" |

## الإصلاحات الجوهرية

1. **`geo_v2` يصبح الطريقة الأساسية للمقارنة عند bracket_n < 20** (ليس "supplementary")
2. **التكلفة والدخل تأكيدات منفصلة** — تُعرض، لا تُوزَن
3. **الإيجار من العميل أولاً** (14K) → fallback إلى rent_reference فقط
4. **Cap Rate حسب نوع الأصل**: سكني 4%، استثماري 7.5%، تجاري 8%
5. **بيان التوفيق صريح** يكشف الاتفاق أو الاختلاف بين الطرق
6. **التسمية في الـ Frontend "تقدير AVM"** بدل "تقييم رسمي" — صدق منهجي

## الملفات

| الملف | الحجم | الحالة |
|---|---|---|
| `evaluate_unified.py` | 24 KB | إعادة كتابة كاملة على المنهجية الصحيحة |
| `evaluate_v3.py` | 20 KB | يبقى للاستفادة من output_briefs + material_uncertainty |
| `api.py` | 23 KB | حقل `audience` |
| `index.html` | 27 KB | عرض التأكيدات + التوفيق + AVM في الـ disclaimer |

## خطوات النشر

```bash
cp evaluate_unified.py C:\Thammen\deploy v2\
cp evaluate_v3.py      C:\Thammen\deploy v2\
cp api.py              C:\Thammen\deploy v2\
cp index.html          C:\Thammen\deploy v2\

# (rent_reference.json يجب أن يكون موجوداً في مجلد النشر)

cd "C:\Thammen\deploy v2"
git add evaluate_unified.py evaluate_v3.py api.py index.html
git commit -m "Sprint 1.b: AVM with Sales Comparison-led Three-Approach Reconciliation

- Primary value: Sales Comparison with geographic widening (RICS VPS 4 §7)
  - bracket_n >= 20: bracket median
  - bracket_n < 20 + geo widening succeeded: widened median (RICS adjustment)
- Cross-checks: cost + income shown but NOT weighted into primary
- Income approach: user rent priority, asset-type cap rate (4% residential)
- Reconciliation: explicit agreement/divergence indicator
- AVM disclaimer language in frontend
- audience field wired to output_briefs for 4 distinct reports"
git push heroku master
```

## التحقق بعد النشر

اختبر:
```bash
curl -X POST https://thammen-app-123-227a7106a67a.herokuapp.com/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":54,"street":541,"building":6,"rental_income":14000,"floors":2,"condition":"good","audience":"investor"}'
```

يجب أن ترى:
- `valuation.amount = 4500000`
- `valuation.method = "comparison_widened"`
- `cost_approach.total_replacement_value ≈ 4.16M`
- `income_approach.income_value ≈ 3.23M`
- `income_approach.cap_rate = 0.04`
- `reconciliation.status = "divergence"`
- `reconciliation.spread_pct ≈ 39`
- `brief.title_ar = "تقرير المستثمر"`
- `material_uncertainty.level = "high"`
- `methodology_ar` يحتوي "AVM"

## ما يبقى لـ Sprint 2

1. **Per-Transaction Adjustments** (RICS VPS 4 §7 الكامل):
   - تشغيل `comparable_adjustments.py` على الـ 42 معاملة
   - تسوية وقت + حجم + موقع فرعي لكل واحدة
   - وسيط الصفقات المُسوَّاة كقيمة المقارنة
   - يرفع النظام من 50% إلى 70% من معيار RICS

2. **Purpose + Basis of Value** كحقلَي إدخال في الـ UI

3. **Reconciliation Narrative** كنص مكتوب (ليس فقط labels)

4. **PDF/DOCX Export** يطابق نموذج v2 الذي أعدّيناه

## مرجع المعايير المُطبَّقة

- IVS 101 (Scope) — جزئي: audience مُحدَّد، Purpose غير مُحدَّد
- IVS 104 (Bases of Value) — Market Value (افتراضي)
- IVS 105 (Approaches & Methods) — الطرق الثلاث ✓
- RICS VPS 4 (Bases) — جزئي
- RICS VPS 4 §7 (Comparable Adjustments) — جزئي (توسيع جغرافي، ليس per-transaction)
- RICS VPN 13 (Material Uncertainty) — ✓
- RICS GN 13 (Asking Prices) — ✓ (مفصولة عن المعادلة)
- RICS Insight Paper (AVMs) — التصنيف الذي ننتمي إليه

النظام الآن **AVM متوافق ⅔ تقريباً** مع متطلبات RICS للـ AVMs. الجزء المتبقي يتطلب per-transaction adjustments والـ Purpose/Basis fields.
