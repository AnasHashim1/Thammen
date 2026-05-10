#!/usr/bin/env python3
"""
material_uncertainty.py — RICS VPS 4 §3.2 Material Uncertainty declarations.

When any data source has insufficient sample size, the valuation must carry
an explicit Material Uncertainty banner — not buried in footnotes.

This module generates the appropriate caveat based on the weakest link
in the data chain.

Usage:
    from material_uncertainty import assess_uncertainty, UncertaintyLevel

    level = assess_uncertainty(
        moj_n=4,
        rent_n=25000,
        trend_n_years=3,
        has_field_inspection=False,
        building_condition_known=False,
    )
    print(level.banner_ar)        # الشعار بالعربي
    print(level.level)            # 'high' | 'moderate' | 'low'
    print(level.rics_compliant)   # False — needs field inspection
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class UncertaintyLevel:
    """Material uncertainty assessment for a valuation."""
    level: str                    # 'high' | 'moderate' | 'low' | 'critical'
    banner_ar: str                # Arabic banner text
    banner_en: str                # English banner text
    factors: List[str]            # contributing factors
    rics_compliant: bool          # whether RICS Red Book would accept this
    known_unknowns: List[str]     # what we explicitly don't know
    recommendations: List[str]    # what should be done to reduce uncertainty


def assess_uncertainty(
    moj_n: Optional[int] = None,
    rent_n: Optional[int] = None,
    trend_n_years: Optional[int] = None,
    has_field_inspection: bool = False,
    building_condition_known: bool = False,
    building_age_known: bool = False,
    service_charge_confidence: str = 'estimated',
    property_type_known: bool = True,
    bua_known: bool = False,
) -> UncertaintyLevel:
    """
    Assess material uncertainty across all data sources.

    The final level is the WORST (highest uncertainty) among all inputs.
    """
    factors = []
    unknowns = []
    recommendations = []
    scores = []  # higher = more uncertain

    # ── MoJ sample size ──
    if moj_n is None or moj_n == 0:
        factors.append(f'لا توجد صفقات مقارنة في وزارة العدل')
        scores.append(4)
        recommendations.append('ابحث في مناطق مجاورة أو وسّع النافذة الزمنية')
    elif moj_n < 5:
        factors.append(f'عينة وزارة العدل صغيرة جداً (n={moj_n}) — لا يمكن إنتاج وسيط موثوق')
        scores.append(3)
        recommendations.append('أضف مناطق مجاورة أو وسّع النافذة لـ 36 شهر')
    elif moj_n < 10:
        factors.append(f'عينة وزارة العدل محدودة (n={moj_n}) — الوسيط إرشادي فقط')
        scores.append(2)
    elif moj_n < 20:
        factors.append(f'عينة وزارة العدل معقولة لكنها تحت الحد المثالي (n={moj_n})')
        scores.append(1)

    # ── Rental data ──
    if rent_n is None or rent_n == 0:
        factors.append('لا توجد بيانات إيجار — منهج الدخل غير مطبَّق')
        scores.append(2)
    elif rent_n < 20:
        factors.append(f'بيانات الإيجار محدودة (n={rent_n})')
        scores.append(1)

    # ── Trend ──
    if trend_n_years is None or trend_n_years < 2:
        factors.append('لا يوجد اتجاه زمني كافٍ — التعديل الزمني غير مطبَّق')
        scores.append(1)

    # ── Physical inspection ──
    if not has_field_inspection:
        factors.append('لم يتم فحص العقار ميدانياً — تقييم مكتبي فقط')
        unknowns.append('حالة المبنى الفعلية من الداخل')
        unknowns.append('التشطيبات والإطلالة والضوضاء')
        scores.append(2)
        recommendations.append('معاينة ميدانية قبل اتخاذ قرار شراء/بيع')

    # ── Building condition ──
    if not building_condition_known:
        unknowns.append('حالة المبنى (MoJ لا تفصل بين جديد ومتهالك)')

    if not building_age_known:
        unknowns.append('عمر البناء الدقيق')

    if not bua_known:
        unknowns.append('المساحة المبنية الفعلية (BUA)')
        factors.append('المساحة المبنية غير معروفة — تقدير بنسبة من القطعة')
        scores.append(1)

    # ── Service charges ──
    if service_charge_confidence == 'estimated':
        factors.append('رسوم الخدمات تقديرية — ليست مُتحقَّقة لهذا المبنى')
        scores.append(1)
    elif service_charge_confidence == 'reported':
        factors.append('رسوم الخدمات مُبلَّغة (ليست مُتحقَّقة من مصدر أصلي)')

    # ── Determine overall level ──
    max_score = max(scores) if scores else 0

    if max_score >= 4:
        level = 'critical'
        banner_ar = ('⛔ تحفظ مادي جوهري — '
                     'البيانات المتاحة غير كافية لإنتاج تقييم موثوق. '
                     'النتائج للاسترشاد الأوّلي فقط ولا تصلح لاتخاذ قرار.')
        banner_en = ('⛔ CRITICAL Material Uncertainty — '
                     'Insufficient data for a reliable valuation. '
                     'Results are for preliminary guidance only.')
    elif max_score >= 3:
        level = 'high'
        banner_ar = ('⚠️ تحفظ مادي عالٍ — '
                     'عينة المقارنات صغيرة جداً و/أو معلومات أساسية مفقودة. '
                     'يُنصح باستشارة مُقيِّم معتمد.')
        banner_en = ('⚠️ HIGH Material Uncertainty — '
                     'Very small comparable sample and/or critical information gaps. '
                     'Certified valuer consultation recommended.')
    elif max_score >= 2:
        level = 'moderate'
        banner_ar = ('ℹ️ تحفظ مادي متوسط — '
                     'تقييم مكتبي بدون فحص ميداني. '
                     'النتائج معقولة لكنها لا تحل محل معاينة ميدانية.')
        banner_en = ('ℹ️ MODERATE Material Uncertainty — '
                     'Desktop valuation without physical inspection. '
                     'Results are reasonable but do not replace site inspection.')
    else:
        level = 'low'
        banner_ar = ('✅ مستوى اليقين جيد — '
                     'عينة كافية من الصفقات الفعلية. '
                     'التقييم مبني على بيانات موثوقة مع التحفظات المذكورة.')
        banner_en = ('✅ LOW Material Uncertainty — '
                     'Sufficient comparable transactions. '
                     'Valuation based on reliable data with noted caveats.')

    rics_compliant = (max_score <= 1 and has_field_inspection
                      and building_condition_known and bua_known)

    if not rics_compliant:
        recommendations.append(
            'للتوافق مع معايير RICS Red Book: يلزم فحص ميداني + '
            'تعديل فردي للمقارنات + توثيق حالة المبنى + Terms of Engagement.'
        )

    return UncertaintyLevel(
        level=level,
        banner_ar=banner_ar,
        banner_en=banner_en,
        factors=factors,
        rics_compliant=rics_compliant,
        known_unknowns=unknowns,
        recommendations=recommendations,
    )
