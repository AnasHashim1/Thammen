# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.78 — EN localization catalog + additive post-pass.

Walks an API response dict and adds an `{base}_en` sibling for every user-facing
`{base}_ar` whose (LRM-normalized) value is in CATALOG. ADDITIVE-ONLY — never modifies
an `_ar` or any value, never clobbers an existing engine-authored `_en`. VALUE-INVARIANT:
the AR-default frontend ignores the new keys, and amount/method/rule are untouched (those
are not `_ar` fields). Keyed by NORMALIZED Arabic (LRM/RLM/zero-width stripped + whitespace
collapsed) so the catalog keys are robust against the engine's bidi-mark formatting.

The catalog covers only TRULY-CONSTANT strings (fixed labels / clauses / disclaimers /
reasons / methodology). Number-interpolated strings (notes/source/assumptions with embedded
amounts/n/%/days) get site-level `_en` twins in a later slice; they simply have no `_en`
here and fall back to `_ar` in EN mode until then.
"""
import re

_MARKS = dict.fromkeys(map(ord, '‎‏​‌‍﻿'), None)
_WS = re.compile(r'\s+')


def _norm(s):
    """Normalize an Arabic string for catalog matching (strip bidi/zero-width marks,
    collapse whitespace). Non-strings pass through unchanged."""
    if not isinstance(s, str):
        return s
    return _WS.sub(' ', s.translate(_MARKS)).strip()


# AR(normalized) -> EN. Authored Sprint 2.22.0b.78 against the locked termbase
# (product = "Automated Market Valuation"; «ليس تقييماً معتمداً» = "not a certified
# valuation"). Keys are the normalized Arabic; a live coverage test guards drift.
CATALOG = {
    "31 ديسمبر 2025": "31 December 2025",
    "MoJ لا تسجل وحدات الشقق فردياً": "The Ministry of Justice does not register individual apartment units",
    "أرض سكنية": "Residential land",
    "أرض فضاء": "Vacant land",
    "أسئلة يجب طرحها قبل الشراء": "Questions to ask before buying",
    "أساس التقدير هو منهج المقارنة بالمبيعات.": "The basis of the estimate is the sales-comparison approach.",
    "إفادة العميل (الإيجار الفعلي)": "Client statement (actual rent)",
    "ارتفاع مسموح: G+1+P": "Permitted height: G+1+P",
    "استرشادي، مُعايَر على تقييم معتمد واحد (V001)": "Indicative, calibrated against a single certified valuation (V001)",
    "الإيجار السنوي الإجمالي": "Gross annual rent",
    "الإيجار السنوي الإجمالي للمجمع (Gross Annual Income)": "Gross annual rent for the compound (Gross Annual Income)",
    "الخطوات المقترحة": "Suggested steps",
    "الطرق الثلاث تتقارب — ثقة عالية في القيمة": "The three approaches converge — high confidence in the value",
    "العائد الصافي منخفض جداً (<2.5%) — السوق سكني نقي، لا استثماري": "The net yield is very low (<2.5%) — the market is purely residential, not investment-driven",
    "العمر المسجَّل في النظام حدٌّ أدنى — العمر الفعلي قد يكون أكبر؛ أدخِل العمر الفعلي في «حسّن التقدير» لدقّة أعلى.": "The age recorded in the system is a lower bound — the actual age may be greater; enter the actual age under \"Refine the estimate\" for higher precision.",
    "الفيلات السكنية سكن مالكي، عائدها الإيجاري منخفض لأن الموقع ونمط الحياة يغلبان على الإيجار في تسعيرها — لذا يُستخدم معدل رسملة افتراضي منخفض (4%). منهج الدخل هنا للتأكيد فقط، ولا يدخل في القيمة النهائية لعقار سكني.": "Residential villas are owner-occupied; their rental yield is low because location and lifestyle dominate rent in their pricing — so a low default capitalization rate (4%) is used. The income approach here is for confirmation only and does not enter into the final value of a residential property.",
    "المجمعات الكبيرة لا توجد لها مقارنات مباشرة في وزارة العدل. التقييم يعتمد على منهج الدخل ويتطلب إفادة الإيجار السنوي الإجمالي. بدون هذه الإفادة، يقدّم ثمّن تصنيفاً فقط دون رقم.": "Large compounds have no direct comparables in the Ministry of Justice records. The valuation relies on the income approach and requires a statement of the gross annual income. Without this statement, Thammen provides a classification only, with no figure.",
    "المخاطر والإشارات": "Risks and signals",
    "المرجع مبني على بيانات حتى 31 ديسمبر 2025. للحالات الحساسة، تحقق من السوق الحالي قبل اتخاذ القرار.": "The reference is based on data up to 31 December 2025. For sensitive cases, verify the current market before making a decision.",
    "المرجع مبني على بيانات وزارة العدل المتاحة حتى 31 ديسمبر 2025. الحكومة لم تنشر بيانات أحدث. النتائج إرشادية ولا تعكس بالضرورة الأسعار الحالية.": "The reference is based on the Ministry of Justice data available up to 31 December 2025. The government has not published newer data. The results are indicative and do not necessarily reflect current prices.",
    "النقطة المركزية تَستخدم وسيط المقارنات (محافظ). الحد الأعلى يَتسع لِيَعكس الخصائص الفريدة المُكتشَفة. HBU (إن وُجد) يُؤثر على النقطة المركزية لأنه قيمة-إضافية غير مُتضمَّنة في عقارات المقارنة.": "The central point uses the median of the comparables (conservative). The upper bound widens to reflect the unique features detected. HBU (highest and best use), where present, affects the central point because it is added value not embedded in the comparable properties.",
    "بانتظار مراجعة مُقيِّم مُرخّص": "Pending review by a licensed valuer",
    "بتشطيب فاخر": "With luxury finish",
    "برج سكني": "Residential tower",
    "برج كامل": "Whole tower",
    "بسعر الأرض": "At land value",
    "بعد ترميم كامل — حالة ممتازة": "After full renovation — excellent condition",
    "بناء حديث جيد": "Good modern build",
    "بناء متوسط العمر": "Mid-age build",
    "بيانات غير كافية للتقييم": "Insufficient data for valuation",
    "بيانات وزارة العدل قديمة (≥ 91 يوماً) — لا تدعم رقماً سنوياً دقيقاً اليوم.": "The Ministry of Justice data is stale (≥ 91 days) — it does not support an accurate annual figure today.",
    "تأكيد منهجي — لا تدخل في القيمة النهائية لعقار سكني": "Methodological cross-check — does not enter the final value of a residential property",
    "تباين جوهري بين الطرق — يلزم فحص ميداني أو إعادة تقييم البيانات": "Material divergence between the approaches — a field inspection or re-assessment of the data is required",
    "تباين كبير": "Large divergence",
    "تجاري": "Commercial",
    "تحفظ مادي جوهري — البيانات المتاحة غير كافية لإنتاج تقييم موثوق. النتائج للاسترشاد الأوّلي فقط ولا تصلح لاتخاذ قرار.": "Significant material uncertainty — the available data is insufficient to produce a reliable valuation. The results are for preliminary guidance only and are not suitable for decision-making.",
    "تحفظ مادي حرج: لا توجد بيانات بيع مقارنة لهذه الفئة": "Critical material uncertainty: there is no comparable sales data for this category",
    "تحفظ مادي متوسط — تقييم مكتبي بدون فحص ميداني. النتائج معقولة لكنها لا تحل محل معاينة ميدانية.": "Moderate material uncertainty — a desktop valuation without a field inspection. The results are reasonable but do not replace a field inspection.",
    "تحفظ مادي وفق RICS Red Book Global Standards (effective 31 January 2025) — VPGA 10 (Material Valuation Uncertainty) و VPS 6 (Valuation Reports) — و IVS (effective 31 January 2025) — IVS 106 (Documentation and Reporting) تعتمد شواهد السوق المتاحة في تاريخ هذا التقدير على بيانات وزارة العدل المسجَّلة حتى 2025-12-31، في ظل فجوة طويلة في تحديث البيانات وضعف في حجم المعاملات الحديثة المنشورة — وهو ما يفرض قيوداً جوهرية على شواهد السوق. نطاق التحفّظ: يشمل القيمة التقديرية المُعلنة، النطاق المُعلَن (الأدنى/الأعلى)، ومدى انطباق منهجية المقارنة السوقية على ظروف السوق الحالية. بناءً عليه — ووفق المعايير المذكورة أعلاه — يجب اعتبار درجة اليقين في هذا التقدير أقل من المعتاد، وتطبيق درجة حذر أعلى عند الاعتماد عليه. يُوصى بمراجعة هذا التقدير على فترات متقاربة.": "Material uncertainty under the RICS Red Book Global Standards (effective 31 January 2025) — VPGA 10 (Material Valuation Uncertainty) and VPS 6 (Valuation Reports) — and IVS (effective 31 January 2025) — IVS 106 (Documentation and Reporting)\n\nThe market evidence available at the date of this estimate relies on Ministry of Justice records up to 2025-12-31, amid a prolonged gap in data updates and a limited volume of recently published transactions — which imposes material limitations on the market evidence.\n\nScope of the material uncertainty: it covers the stated estimated value, the stated range (low/high), and the extent to which the sales-comparison methodology applies to current market conditions.\n\nAccordingly — and in line with the standards cited above — the degree of certainty in this estimate should be regarded as lower than usual, and a higher degree of caution applied when relying on it. It is recommended that this estimate be reviewed at close intervals.",
    "تحفظات مادية وفق RICS Red Book Global Standards (effective 31 January 2025) — VPGA 10 و VPS 6 — و IVS (effective 31 January 2025) — IVS 106": "Material uncertainties under the RICS Red Book Global Standards (effective 31 January 2025) — VPGA 10 and VPS 6 — and IVS (effective 31 January 2025) — IVS 106",
    "تحقّق من بيانات العنوان أو تواصل معنا.": "Verify the address details or contact us.",
    "تصنيف سريع مبني على بيانات GIS — لا توجد مقارنة MoJ مباشرة لفئة \"عمارة سكنية\" في قطر": "Quick classification based on GIS data — there is no direct Ministry of Justice comparison for the \"residential apartment building\" category in Qatar",
    "تصنيف غير مطابق لأي فئة مدعومة": "Classification does not match any supported category",
    "تصنيف فقط — التقييم يحتاج إفادة الإيجار أو سعر الإعلان": "Classification only — the valuation requires a statement of the rent or the listing price",
    "تعليمي": "Educational",
    "تغطية MoJ كافية في 10+ مناطق سكنية رئيسية": "Ministry of Justice coverage is sufficient in 10+ major residential areas",
    "تغطية MoJ كافية وأسعار الأرض مستقرة نسبياً": "Ministry of Justice coverage is sufficient and land prices are relatively stable",
    "تقارب قوي بين الطرق": "Strong convergence between the approaches",
    "تقدير الأصول من هذه الفئة يحتاج منهج الدخل (Income Approach) أو سعر إعلان قابل للمقارنة. يرجى إعادة الطلب مع إفادة بالإيجار الشهري أو سعر الإعلان للحصول على تحليل آلي.": "Estimating assets in this category requires the income approach (Income Approach) or a comparable listing price. Please resubmit the request with a statement of the monthly rent or the listing price to obtain an automated analysis.",
    "تقدير الإهلاك يزداد ذاتيةً مع التقادم؛ معايرتنا على شيت مثمّن وأرضية السوق تخففه.": "The depreciation estimate becomes more subjective with age; our calibration against a valuer's worksheet and the market floor mitigates this.",
    "تقرير المشتري": "Buyer's report",
    "تقرير عمارة سكنية — تحتاج بيانات إضافية": "Residential apartment building report — additional data required",
    "تقييم الأراضي السكنية يستخدم مقارنة مع صفقات الأراضي الفضاء في نفس المنطقة والشريحة. خصائص خاصة كالقرب من شارع رئيسي، الزاوية، أو الإطلالة قد ترفع السعر الفعلي 10-30% فوق هذا التقدير.": "The valuation of residential land uses comparison with vacant-land transactions in the same area and size bracket. Special features such as proximity to a main street, a corner location, or a view may raise the actual price by 10–30% above this estimate.",
    "تقييم الفلل المستقلة يستخدم مقارنة مع صفقات وزارة العدل في نفس المنطقة والشريحة (نافذة 24 شهراً). لا يدخل في التقييم تأثير حالة المبنى الداخلية، التشطيبات، أو الإطلالة.": "The valuation of standalone villas uses comparison with Ministry of Justice transactions in the same area and size bracket (24-month window). The effect of the building's internal condition, finishes, or view is not taken into account in the valuation.",
    "تقييم متخصص مطلوب.": "A specialist valuation is required.",
    "تنظيم R1": "R1 zoning",
    "تنظيم R1-TYP": "R1-TYP zoning",
    "ثمّن يدعم 3 فئات بالكامل، 4 فئات بمنهج الدخل (تتطلب إفادة الإيجار)، و 3 فئات خارج النطاق.": "Thammen fully supports 3 categories, 4 categories via the income approach (requiring a rent statement), and 3 categories out of scope.",
    "ثمّن يُنتج \"حساب قيمة\" (Calculation of Value) + \"نصيحة استشارية\" (Other Advice) وفق المنهجية المعيارية لـ RICS VPS 3 — وليس \"تقريراً تقييمياً معتمداً\" (Valuation Report). للأغراض الرسمية (قروض، نزاعات قضائية، تقارير محاسبية، تأمين)، يلزم تقييم معتمد من مُقيِّم مُرخّص.": "Thammen produces a \"Calculation of Value\" + \"Other Advice\" in line with the standard RICS VPS 3 methodology — not a certified \"Valuation Report\". For official purposes (loans, litigation, accounting reports, insurance), a certified valuation by a licensed valuer is required.",
    "حجم عقارك يتجاوز أي صفقة مقارنة في قاعدة بياناتنا. التقدير الآلي لا يستطيع التعميم بأمان. تقييم متخصص مطلوب لأصل بهذا الحجم.": "The size of your property exceeds any comparable transaction in our database. The automated estimate cannot extrapolate safely. A specialist valuation is required for an asset of this size.",
    "حكومي": "Government",
    "خارج نطاق الإصدار الحالي": "Outside the scope of the current release",
    "خدمات عامة": "Public services",
    "رياضي": "Sports",
    "سجلات \"مجمع فلل\" متوفرة لمجمعات حتى 15K م²": "\"Villa compound\" records are available for compounds up to 15K m²",
    "شارع داخلي هادئ": "Quiet internal street",
    "شبكة المقارنات المعدّلة": "Adjusted comparables grid",
    "شبكة مقارنات RICS: كل صفقة طُبِّعت زمنياً إلى تاريخ التقييم. لا تُغيّر القيمة الرئيسية — عرض شفاف للمقارنات.": "RICS comparables grid: each transaction has been time-normalized to the valuation date. It does not change the headline value — a transparent display of the comparables.",
    "شواهد غير كافية": "Insufficient evidence",
    "شواهد غير كافية — استُخدم معدل افتراضي": "Insufficient evidence — a default rate was used",
    "شواهد كافية": "Sufficient evidence",
    "شواهد كافية (n≥10)": "Sufficient evidence (n≥10)",
    "صحي": "Health",
    "صفقات بيع وزارة العدل (الحقيقة السوقية)": "Ministry of Justice sale transactions (market truth)",
    "صناعي": "Industrial",
    "عقار تجاري": "Commercial property",
    "عقار صناعي": "Industrial property",
    "علاوة الزاوية والحجم ستُضاف لاحقاً عند توفّر بيانات مرتبطة جغرافياً (geographically-keyed).": "A corner and size premium will be added later, once geographically-keyed data becomes available.",
    "عمارات الشقق تُقيَّم بمنهج الدخل. وزارة العدل لا تسجل وحدات الشقق فردياً بشكل قابل للمقارنة. الإيجار السنوي مطلوب.": "Residential apartment buildings are valued using the income approach. The Ministry of Justice does not register individual apartment units in a comparable manner. The annual rent is required.",
    "عمارة سكنية": "Residential apartment building",
    "عمارة شقق": "Apartment building",
    "عينة MoJ قصور ضعيفة جداً (n=5 شركاء فقط)": "The Ministry of Justice palace sample is very weak (only n=5 partners)",
    "غير محدد": "Unspecified",
    "غير مطبَّق": "Not applied",
    "فاخر / حديث البناء": "Luxury / newly built",
    "فلل جديدة (1-3 سنوات) مع تشطيب فاخر، أو مشاريع طور التطوير. في بعض المناطق تكون عينة هذه الفئة ضعيفة (n<5) فلا يُعتمد على وسيطها مباشرة.": "New villas (1–3 years) with luxury finish, or under-development projects. In some areas the sample for this category is weak (n<5), so its median is not relied upon directly.",
    "فلل عمرها 10+ سنوات بتشطيب متوسط أو تجديد جزئي. الفئة الأكثر تكراراً في معظم مناطق قطر، وتميل إلى أن تكون مهيمنة على الوسيط المدمج.": "Villas 10+ years old with average finish or partial renovation. The most frequent category in most areas of Qatar, and it tends to dominate the blended median.",
    "فلل عمرها 2-10 سنوات، تشطيب جيد، حالة جاهزة للسكن بدون ترميم. كثيراً ما تكون قيمتها الحقيقية أعلى من الوسيط المدمج بنسبة 20-40%.": "Villas 2–10 years old, good finish, move-in ready without renovation. Their true value is often 20–40% above the blended median.",
    "فندقي": "Hospitality",
    "فيلا منفردة": "Standalone villa",
    "قرب حضانة": "Near a nursery",
    "قرب عيادة/مركز صحي": "Near a clinic/health centre",
    "قرب مدرسة": "Near a school",
    "قرب مسجد": "Near a mosque",
    "قصر": "Palace",
    "قطعة منتظمة الشكل": "Regularly shaped plot",
    "قيمة التكلفة (أرض + بناء مُهلَك) — نهج DRC": "Cost value (land + depreciated building) — DRC",
    "قيمة التكلفة (نهج DRC) ≡ قيمة الأرض — لا مكوّن بناء لقطعة فضاء.": "Cost value (DRC approach) ≡ the land value — there is no building component for a vacant plot.",
    "كل معاملة فيلا تُصنَّف بنسبة سعرها إلى وسيط أراضي المنطقة. هذه النسبة تفصل بين فئات العمر والتشطيب: فيلا قديمة تُباع بسعر الأرض تقريباً (نسبة ~1.0)، فيلا حديثة جيدة (نسبة ~1.7)، فيلا فاخرة جديدة (نسبة ~2.3+). القيمة الرئيسية المعروضة في الأعلى تستخدم الوسيط المدمج لكل الفئات وهذا محافظ. التصنيف بحسب الفئات في الأسفل شفافية إضافية للمستخدم.": "Each villa transaction is classified by the ratio of its price to the area's land median. This ratio separates the age and finish categories: an old villa sells at roughly land value (ratio ~1.0), a good modern villa (ratio ~1.7), a new luxury villa (ratio ~2.3+). The headline value shown above uses the blended median across all categories, which is conservative. The category-by-category breakdown below is additional transparency for the user.",
    "كما هي (التقدير الحالي)": "As-is (current estimate)",
    "لا توجد بيانات تجارية عامة في قطر": "There is no public commercial data in Qatar",
    "لا توجد قيمة مقارنة — عينة غير كافية": "No comparable value — insufficient sample",
    "لا توجد مقارنات MoJ سعر/م² للأبراج": "There are no Ministry of Justice price/m² comparables for towers",
    "لا توجد مقارنات MoJ لأصول ≥50K م²، المنهج المعياري هو الدخل": "There are no Ministry of Justice comparables for assets ≥50K m²; the standard approach is income",
    "لم تُؤخذ حالة العقار (تجديد أو تهالك) في الحسبان. عقار في حالة أفضل من المتوسط قد يقع أعلى هذه النقطة، وعقار في حالة أدنى قد يقع تحتها.": "The property's condition (renovation or deterioration) has not been taken into account. A property in better-than-average condition may fall above this point, and one in poorer condition may fall below it.",
    "لم نتمكن من تصنيف هذا العقار. التصنيف الصحيح للأصل ضروري لتطبيق المنهجية المناسبة. يرجى مراجعة العنوان المُدخَل.": "We were unable to classify this property. The correct classification of the asset is essential to apply the appropriate methodology. Please review the address entered.",
    "لم نتمكّن من تحديد نوع العقار من البيانات الحكوميّة المتاحة. قد يكون العنوان غير مُفهرَس حالياً في سجلّ العناوين الحكوميّ (QARS) أو خارج نطاق التغطية.": "We were unable to determine the property type from the available government data. The address may not currently be indexed in the government address registry (QARS) or may be outside the coverage area.",
    "مجمع صغير (≤15K م²)": "Small compound (≤15K m²)",
    "مجمع فلل صغير": "Small villa compound",
    "مجمع فلل كبير": "Large villa compound",
    "مجمع كبير (≥50K م²)": "Large compound (≥50K m²)",
    "مزرعة": "Farm",
    "مزرعة / أرض زراعية": "Farm / agricultural land",
    "مصدر معدل الرسملة": "Capitalization-rate source",
    "معدل رسملة معايَر من إيجارات السوق ÷ وسيط بيع وزارة العدل (Sprint 2.19) — معدل مُستعار من شريحة 400-600 م² للمنطقة نفسها (شريحة العقار 600-900 م² بلا عيّنة كافية؛ العائد الصافي مستقر عبر شرائح المنطقة الواحدة).": "Capitalization rate calibrated from market rents ÷ the Ministry of Justice sale median (Sprint 2.19) — a rate borrowed from the 400–600 m² bracket of the same area (the property's 600–900 m² bracket has no sufficient sample; the net yield is stable across the brackets of a single area).",
    "مقارنة المبيعات (Sales Comparison) من سجلات وزارة العدل": "Sales comparison from Ministry of Justice records",
    "مقارنة شريحية مباشرة (RICS VPS 3 / IVS 103)": "Direct bracket comparison (RICS VPS 3 / IVS 103)",
    "منهج الدخل (Income Approach)": "Income approach",
    "منهج الدخل (Income Approach) — معدّل الرسملة على إيجار سنوي": "Income approach — capitalization rate applied to annual rent",
    "منهج الدخل (RICS Income Approach)": "Income approach (RICS Income Approach)",
    "منهج المقارنة بالمبيعات (VPS 3 / IVS 103)؛ قيمة الأرض تعكس الاستخدام الأمثل (VPS 2 / IVS 102)": "Sales-comparison approach (VPS 3 / IVS 103); the land value reflects the highest and best use (VPS 2 / IVS 102)",
    "منهج المقارنة بالمبيعات (مجموعة موسَّعة جغرافياً) (RICS VPS 3 / IVS 103)": "Sales-comparison approach (geographically extended set) (RICS VPS 3 / IVS 103)",
    "نافذة 2020–2025": "2020–2025 window",
    "نمط سوقي: غلبة قيمة الأرض في العقارات القديمة": "Market pattern: predominance of land value in older properties",
    "نوصي بتقييم متخصص لعقارك من خلال مُقيِّم معتمد.": "We recommend a specialist valuation of your property by a certified valuer.",
    "نوع غير معروف": "Unknown type",
    "هدم وإعادة تطوير (قيمة الأرض − الهدم)": "Teardown & redevelopment (land value − demolition)",
    "هذا الأصل من نوع \"عمارة سكنية\" — لا توجد عينة مقارنة في سجلات وزارة العدل لهذه الفئة (الكومباوندات الكبيرة والأبراج تُسجَّل بأرقام مرجعية موحَّدة بدلاً من مقارنات سعر/م²). لتقييم دقيق، أضف الإيجار الشهري الفعلي أو سعر الإعلان وأعد الطلب.": "This asset is of the \"residential apartment building\" type — there is no comparable sample in the Ministry of Justice records for this category (large compounds and towers are registered under unified reference numbers rather than price/m² comparables). For an accurate valuation, add the actual monthly rent or the listing price and resubmit the request.",
    "هذا التقدير يجب أن يُراجَع عند: (أ) استئناف نشر بيانات وزارة العدل، أو (ب) ظهور صفقات حقيقية مؤكَّدة من قطاع الوساطة في نفس الفئة، أيهما أسبق.": "This estimate should be reviewed upon: (a) the resumption of Ministry of Justice data publication, or (b) the appearance of real confirmed transactions from the brokerage sector in the same category, whichever comes first.",
    "هذه الطبقات مقدّمة كشفافية إضافية — القيمة الرئيسية أعلاه لم تتأثّر. اختيار الفئة المناسبة لعقارك حسب العمر والتشطيب يبقى قرار المستخدم.": "These layers are provided as additional transparency — the headline value above is unaffected. Selecting the appropriate category for your property by age and finish remains the user's decision.",
    "هذه المنطقة فيها أقل من 5 صفقات بيع مقارنة خلال آخر 6 أشهر لعقارات بهذا الحجم والنوع. التقدير الآلي لا يصل إلى مستوى الموثوقية المطلوب.": "This area has fewer than 5 comparable sale transactions over the last 6 months for properties of this size and type. The automated estimate does not reach the required level of reliability.",
    "هذه قطعة أرض فضاء — التقييم على قيمة الأرض المنفصلة فقط. لا توجد قيمة بناء يحسبها هذا التقييم.": "This is a vacant plot — the valuation is on the standalone land value only. There is no building value calculated by this valuation.",
    "وسيط البلدية (n=1344)": "Municipality median (n=1344)",
    "يستند هذا التقدير إلى منهج المقارنة بالمبيعات (VPS 3 / IVS 103)، ضمن RICS Red Book Global Standards (effective 31 January 2025) بما في ذلك معيار نماذج التقييم (VPS 5 / IVS 105)، مع الإفصاح عن عدم اليقين الجوهري (VPGA 10) في التقرير (VPS 6 / IVS 106). النموذج الآلي (AVM) أداة مساعدة ولا يُنتج بمفرده تقييماً نهائياً مطابقاً للمعايير دون مراجعة مُقيِّم مُرخّص.": "This estimate is based on the sales-comparison approach (VPS 3 / IVS 103), within the RICS Red Book Global Standards (effective 31 January 2025), including the valuation-models standard (VPS 5 / IVS 105), with disclosure of material uncertainty (VPGA 10) in the report (VPS 6 / IVS 106). The automated model (AVM) is a support tool and does not by itself produce a final standards-compliant valuation without review by a licensed valuer.",
    "يشير النموذج إلى أن القيمة المقارنة لا تتجاوز قيمة الأرض المجردة؛ القيمة الضمنية للمبنى ≈ صفر (قد يُعتبر عقاراً للتطوير).": "The model indicates that the comparable value does not exceed the bare land value; the implied building value ≈ zero (it may be regarded as a development property).",
    "يفصل ثمّن قيمة الأرض (من معاملات بيع أراضٍ نقية في نفس المنطقة) عن قيمة البناء الضمنية (الفرق بين القيمة الكلية وقيمة الأرض). هذا الفصل يكشف للمستخدم نسبة مساهمة كل عنصر — حسب RICS Red Book.": "Thammen separates the land value (from pure land-sale transactions in the same district) from the implied building value (the difference between the total value and the land value). This separation reveals to the user the contribution share of each component — in accordance with the RICS Red Book.",
}


def attach_en(obj, _depth=0):
    """Recursively add `{base}_en` siblings from CATALOG. Best-effort / additive /
    never raises. Returns the same object (mutated in place)."""
    try:
        if _depth > 40:
            return obj
        if isinstance(obj, dict):
            for k in list(obj.keys()):          # snapshot: we add keys during the walk
                v = obj[k]
                if isinstance(v, str) and k.endswith('_ar'):
                    enk = k[:-3] + '_en'
                    if enk not in obj:          # never clobber an engine-authored _en
                        en = CATALOG.get(_norm(v))
                        if en is not None:
                            obj[enk] = en
                else:
                    attach_en(v, _depth + 1)
        elif isinstance(obj, list):
            for it in obj:
                attach_en(it, _depth + 1)
    except Exception:
        pass
    return obj
