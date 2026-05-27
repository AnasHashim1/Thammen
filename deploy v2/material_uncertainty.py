#!/usr/bin/env python3
"""
material_uncertainty.py — Material Valuation Uncertainty (MVU) declarations.

Canonical standards (Sprint 2.22.0a/9 audit — RICS Red Book Global Standards
2024 + IVS 2024, both effective 31 January 2024):

  - RICS Red Book Global Standards 2024 — VPGA 10 (Material Valuation
    Uncertainty) + VPS 3 (Valuation Reports — reporting requirements).
  - IVS 2024 — IVS 103 (Reporting).

VPGA 10 is the canonical RICS guidance on Material Valuation Uncertainty;
VPS 3 carries the reporting obligations. The earlier "RICS VPS 5"
references that appeared in this module (Sprint 2.14.0 era) reflected
2014-edition / COVID-19-era informal industry usage. VPS 5 in the 2024
edition is "Valuation Approaches and Methods" — a different topic — so
the citation has been corrected throughout.

When any data source has insufficient sample size, OR the active market
regime is materially disrupted, the valuation must carry an explicit
Material Valuation Uncertainty banner — not buried in footnotes. This
module generates the appropriate caveat based on the weakest link in
the data chain and the active regime.

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
    # Sprint 2.14.0 — formal Material Valuation Uncertainty (MVU) clause text.
    # Sprint 2.22.0a/9 — citation corrected to RICS VPGA 10 + VPS 3 (Red Book
    # Global Standards 2024) and IVS 103 (IVS 2024). Set by regime_muc()
    # when the market regime is non-normal. None means no market-wide MVU
    # applies (normal market conditions).
    muc_clause_ar: Optional[str] = None
    muc_clause_en: Optional[str] = None
    muc_basis_ar: Optional[str] = None    # what makes the MVU applicable
    muc_review_recommendation_ar: Optional[str] = None


# Sprint 2.22.0a/9 — Arabic → English mapping for the 4 known ShockLayer
# instances defined in `market_regime.py`. Used by regime_muc() to render
# `shock_summary_en` in the English MVU clause (RICS VPGA 10 §6 requires
# the cause of uncertainty to be identified — Sprint 2.22.0a/9 R3 element 2).
# Future shock layers added to market_regime.py without an English mapping
# here fall back to the Arabic name_ar (graceful degradation — emission
# never raises). Lives in this module so the audit-trail surface stays
# self-contained; market_regime.py is unmodified in /9 (strict scope).
_SHOCK_LAYER_NAME_EN_BY_AR = {
    'تصحيح ما بعد المونديال':       'post-World-Cup correction',
    'الحرب الإقليمية وإغلاق هرمز':  'regional war and Hormuz Strait closure',
    'نزوح سكاني':                    'population outflow',
    'انهيار حجم المعاملات':          'transaction-volume collapse',
}


def _shock_layer_name_en(layer) -> str:
    """Render a ShockLayer's name in English for the MVU clause.

    Falls back to `name_ar` (the Arabic name) when no English mapping is
    registered for this layer — keeps the English clause well-formed even
    when a new shock layer ships before its English name reaches this dict.
    """
    return _SHOCK_LAYER_NAME_EN_BY_AR.get(
        getattr(layer, 'name_ar', '') or '',
        getattr(layer, 'name_ar', '') or '',
    )


def regime_muc(regime=None) -> dict:
    """Generate the Material Valuation Uncertainty (MVU) clause for the
    current market regime.

    Canonical standards (Sprint 2.22.0a/9 citation audit):
      - RICS Red Book Global Standards 2024 — VPGA 10 (Material Valuation
        Uncertainty, the canonical RICS guidance) + VPS 3 (Valuation Reports —
        reporting requirements).
      - IVS 2024 — IVS 103 (Reporting).
      The earlier "RICS VPS 5" citation that appeared in this module
      (Sprint 2.14.0 era) reflected 2014-edition / COVID-19-era informal
      industry usage. VPS 5 in the 2024 edition is "Valuation Approaches
      and Methods" — a different topic — so the citation has been
      corrected throughout.

    The MVU declaration follows the four structural elements required by
    RICS VPGA 10 + IVS 103:
      1. Statement of material valuation uncertainty (with edition citation)
      2. Cause of uncertainty (regime + shock layers identified by name)
      3. Scope of uncertainty (Sprint 2.22.0a/9 R3 strengthening — what
         is affected: value, range, methodology applicability)
      4. Recommendation that less reliance be placed + frequent review

    The wording follows the RICS-recognised template (widely used during the
    COVID-19 outbreak by Cushman & Wakefield, Knight Frank, JLL etc.). We
    do not copy any single firm's exact text; the structure and key phrases
    ("less certainty / higher caution / kept under frequent review") are
    the RICS-recognised standard from VPGA 10's recommended wording.

    Args:
        regime: a MarketRegime instance. If None, imports the active one
            from market_regime.current_regime.

    Returns:
        dict with muc_clause_ar/en, muc_basis_ar, muc_review_recommendation_ar.
        For NORMAL_REGIME, returns all-None (no MVU needed).
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

    # Normal regime → no MVU
    if getattr(regime, 'label_en', None) == 'normal':
        return {
            'muc_clause_ar': None,
            'muc_clause_en': None,
            'muc_basis_ar': None,
            'muc_review_recommendation_ar': None,
        }

    # Build the formal MVU text — Sprint 2.22.0a/9 verified per Anas 2026-05-26
    # (citation corrected from "VPS 5" → "VPGA 10 + VPS 3 + IVS 103"; scope-of-
    # uncertainty paragraph added per R3 element 3 strengthening).
    layers = getattr(regime, 'shock_layers', ())
    shock_summary_ar = '، '.join(s.name_ar for s in layers)
    shock_summary_en = ', '.join(_shock_layer_name_en(s) for s in layers)
    active_since = getattr(regime, 'active_since', None)
    moj_last = getattr(regime, 'moj_last_known_date', None)
    _since_iso_ar = active_since.isoformat() if active_since else '؟'
    _since_iso_en = active_since.isoformat() if active_since else '?'

    muc_clause_ar = (
        f'⚠️ تحفظ مادي وفق RICS Red Book Global Standards 2024 '
        f'(VPGA 10 — Material Valuation Uncertainty، و VPS 3 — Valuation Reports) '
        f'و IVS 2024 (IVS 103 — Reporting)\n\n'
        f'تواجه السوق العقاري القطري في تاريخ هذا التقدير '
        f'({_since_iso_ar} وما بعده) '
        f'اضطراباً جوهرياً نشطاً: {shock_summary_ar}.\n\n'
        f'نطاق التحفّظ: يشمل القيمة التقديرية المُعلنة، النطاق المُعلَن '
        f'(الأدنى/الأعلى)، ومدى انطباق منهجية المقارنة السوقية على ظروف '
        f'السوق الحالية.\n\n'
        f'بناءً عليه — ووفق المعايير المذكورة أعلاه — '
        f'يجب اعتبار درجة اليقين في هذا التقدير أقل من المعتاد، '
        f'وتطبيق درجة حذر أعلى عند الاعتماد عليه. '
        f'يُوصى بمراجعة هذا التقدير على فترات متقاربة.'
    )

    muc_clause_en = (
        f'⚠️ Material Valuation Uncertainty per RICS Red Book Global '
        f'Standards 2024 (VPGA 10 — Material Valuation Uncertainty; '
        f'VPS 3 — Valuation Reports) and IVS 2024 (IVS 103 — Reporting)\n\n'
        f'The Qatari real estate market is experiencing material disruption '
        f'at the valuation date '
        f'({_since_iso_en} onwards): {shock_summary_en}.\n\n'
        f'Scope of uncertainty: this affects the reported value, the '
        f'disclosed range (low/high), and the applicability of the Sales '
        f'Comparison approach under current market conditions.\n\n'
        f'Accordingly — and in line with the standards cited above — less '
        f'certainty, and a consequently higher degree of caution, should '
        f'be attached to this estimate than would normally be the case. '
        f'The valuation should be kept under frequent review.'
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
            'للتوافق مع معايير RICS Red Book Global Standards 2024 '
            'و IVS 2024: يلزم فحص ميداني + تعديل فردي للمقارنات + '
            'توثيق حالة المبنى + Terms of Engagement (VPS 1).'
        )

    # Sprint 2.14.0 — automatically attach the market-wide Material Valuation
    # Uncertainty (MVU) clause if active regime is non-normal. This is
    # INDEPENDENT of per-property uncertainty above: even a well-supported
    # valuation (low per-property uncertainty) carries market-wide MVU during
    # the current regime.
    # Sprint 2.22.0a/9 — citation corrected from "RICS VPS 5" to the canonical
    # 2024-edition references (VPGA 10 + VPS 3 + IVS 103). See regime_muc()
    # docstring for the standards audit trail.
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
