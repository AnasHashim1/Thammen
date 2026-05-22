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
    # Sprint 2.14.0 — formal RICS VPS 5 Material Uncertainty Clause text.
    # Set by regime_muc() when the market regime is non-normal. None means
    # no market-wide MUC applies (normal market conditions).
    muc_clause_ar: Optional[str] = None
    muc_clause_en: Optional[str] = None
    muc_basis_ar: Optional[str] = None    # what makes the MUC applicable
    muc_review_recommendation_ar: Optional[str] = None


def regime_muc(regime=None) -> dict:
    """Generate the RICS VPS 5 Material Uncertainty Clause for the
    current market regime.

    RICS Red Book VPS 5 requires a formal MUC declaration when market
    conditions during the valuation period are materially disrupted. The
    declaration must:
      1. Identify the cause of uncertainty
      2. State that less certainty applies — and higher caution is needed
      3. Recommend frequent review of the valuation

    The wording below follows the recognised VPS 5 format (as used by
    Cushman & Wakefield, Knight Frank, JLL during the COVID-19 outbreak
    and other regional crises). We do not copy any single firm's exact
    text; the structure and key phrases are the RICS-recognised standard.

    Args:
        regime: a MarketRegime instance. If None, imports the active one
            from market_regime.current_regime.

    Returns:
        dict with muc_clause_ar/en, muc_basis_ar, muc_review_recommendation_ar.
        For NORMAL_REGIME, returns all-None (no MUC needed).
    """
    if regime is None:
        try:
            from market_regime import current_regime as regime
        except ImportError:
            return {
                'muc_clause_ar': None,
                'muc_clause_en': None,
                'muc_basis_ar': None,
                'muc_review_recommendation_ar': None,
            }

    # Normal regime → no MUC
    if getattr(regime, 'label_en', None) == 'normal':
        return {
            'muc_clause_ar': None,
            'muc_clause_en': None,
            'muc_basis_ar': None,
            'muc_review_recommendation_ar': None,
        }

    # Build the formal MUC text
    shock_summary_ar = '، '.join(
        s.name_ar for s in getattr(regime, 'shock_layers', ())
    )
    active_since = getattr(regime, 'active_since', None)
    moj_last = getattr(regime, 'moj_last_known_date', None)

    muc_clause_ar = (
        f'⚠️ تحفظ مادي وفق RICS VPS 5 (Material Uncertainty Clause)\n\n'
        f'تواجه السوق العقاري القطري في تاريخ هذا التقدير '
        f'({active_since.isoformat() if active_since else "؟"} وما بعده) '
        f'اضطراباً جوهرياً نشطاً: {shock_summary_ar}.\n\n'
        f'بناءً عليه — ووفق المعيار المعترف به في RICS VPS 5 — '
        f'يجب اعتبار درجة اليقين في هذا التقدير أقل من المعتاد، '
        f'وتطبيق درجة حذر أعلى عند الاعتماد عليه. '
        f'يُوصى بمراجعة هذا التقدير على فترات متقاربة.'
    )

    muc_clause_en = (
        f'⚠️ Material Valuation Uncertainty (RICS VPS 5)\n\n'
        f'The Qatari real estate market is experiencing material disruption '
        f'at the valuation date '
        f'({active_since.isoformat() if active_since else "?"} onwards). '
        f'Accordingly — and in line with RICS VPS 5 — less certainty, and '
        f'a consequently higher degree of caution, should be attached to '
        f'this estimate than would normally be the case. The valuation '
        f'should be kept under frequent review.'
    )

    # MoJ lag specifically — explain WHY the uncertainty bites
    muc_basis_ar = (
        f'بيانات وزارة العدل المسجَّلة تنتهي عند '
        f'{moj_last.isoformat() if moj_last else "؟"}'
        + (
            f' — أي قبل بدء الاضطراب الحالي بـ '
            f'{(active_since - moj_last).days if active_since and moj_last else "؟"} يوماً. '
            if active_since and moj_last else '. '
        )
        + 'بالتالي لا تعكس البيانات الأساسية أثر الأحداث الراهنة على الأسعار.'
    )

    muc_review_recommendation_ar = (
        'هذا التقدير يجب أن يُراجَع عند: (أ) استئناف نشر بيانات وزارة العدل، '
        'أو (ب) ظهور صفقات حقيقية مؤكَّدة من قطاع الوساطة في نفس الفئة، '
        'أيهما أسبق.'
    )

    return {
        'muc_clause_ar': muc_clause_ar,
        'muc_clause_en': muc_clause_en,
        'muc_basis_ar': muc_basis_ar,
        'muc_review_recommendation_ar': muc_review_recommendation_ar,
    }


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
    asset_type: Optional[str] = None,
) -> UncertaintyLevel:
    """
    Assess material uncertainty across all data sources.

    The final level is the WORST (highest uncertainty) among all inputs.

    Sprint 2.21.0.5 (Issues 4+5): when `asset_type` is bare land (raw_land/land),
    building-specific factors and known-unknowns (BUA, building condition/age,
    service charges, interior/finishes) are irrelevant and are replaced with
    land-specific unknowns. Non-land assets are unaffected (regression-safe).
    """
    _is_land = (asset_type or '').lower() in ('raw_land', 'land')
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
        scores.append(2)
        if _is_land:
            # Land-specific: no interior/finishes to inspect; check site & deed.
            unknowns.append('منسوب الأرض ومتطلبات الإعداد (ردم/حفر)')
            unknowns.append('مدى توفّر الخدمات والبنية التحتية للموقع')
            recommendations.append('معاينة الموقع + بيان عقاري قبل قرار الشراء/البيع')
        else:
            unknowns.append('حالة المبنى الفعلية من الداخل')
            unknowns.append('التشطيبات والإطلالة والضوضاء')
            recommendations.append('معاينة ميدانية قبل اتخاذ قرار شراء/بيع')

    if _is_land:
        # Bare land has no building → skip all building/BUA/service-charge gaps;
        # surface land-relevant unknowns instead.
        unknowns.append('تصنيف المنطقة وارتفاع البناء المسموح')
        unknowns.append('أي قيود قانونية أو حصص غير مفروزة')
    else:
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

    # Sprint 2.14.0 — automatically attach RICS VPS 5 MUC if active regime
    # is non-normal. This is INDEPENDENT of per-property uncertainty above:
    # even a well-supported valuation (low per-property uncertainty) carries
    # market-wide MUC during the current regime.
    muc = regime_muc()

    return UncertaintyLevel(
        level=level,
        banner_ar=banner_ar,
        banner_en=banner_en,
        factors=factors,
        rics_compliant=rics_compliant,
        known_unknowns=unknowns,
        recommendations=recommendations,
        muc_clause_ar=muc['muc_clause_ar'],
        muc_clause_en=muc['muc_clause_en'],
        muc_basis_ar=muc['muc_basis_ar'],
        muc_review_recommendation_ar=muc['muc_review_recommendation_ar'],
    )
