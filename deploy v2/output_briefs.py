#!/usr/bin/env python3
"""
output_briefs.py — Four audience-specific output formats.

Same underlying data, different emphasis:
    1. Buyer Brief:    Is the price fair? What to negotiate?
    2. Seller Brief:   What's my property worth? How to price it?
    3. Investor Brief: What's the yield? Sensitivity analysis?
    4. Valuer Brief:   Full comparables, adjustments, method weights (RICS-style)

Usage:
    from output_briefs import generate_brief

    brief = generate_brief(
        evaluation=eval_result,           # PropertyEvaluation
        audience='buyer',                 # 'buyer' | 'seller' | 'investor' | 'valuer'
        rent_data=rent_estimate,          # from rent_reference
        adjustments=adj_result,           # from comparable_adjustments
        uncertainty=uncertainty_level,    # from material_uncertainty
    )
    print(brief['title_ar'])
    print(brief['sections'])
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
from datetime import datetime


def _fmt(n):
    """Format number with commas."""
    if n is None:
        return '—'
    return f'{round(n):,}'


def _pct(n):
    if n is None:
        return '—'
    return f'{n:+.1f}%' if n >= 0 else f'{n:.1f}%'


def generate_brief(
    evaluation: dict,
    audience: str = 'buyer',
    rent_data: dict = None,
    adjustments: dict = None,
    uncertainty: dict = None,
    income_value: dict = None,
) -> dict:
    """
    Generate audience-specific brief from evaluation data.

    Args:
        evaluation: PropertyEvaluation as dict (or object with to_dict)
        audience: 'buyer' | 'seller' | 'investor' | 'valuer'
        rent_data: output of estimate_annual_rent()
        adjustments: output of adjust_comparables() as dict
        uncertainty: UncertaintyLevel as dict
        income_value: output of income_approach_value()

    Returns:
        dict with title_ar, title_en, sections (list of dicts),
        material_uncertainty_banner, disclaimer
    """
    if hasattr(evaluation, 'to_dict'):
        evaluation = evaluation.to_dict()
    elif hasattr(evaluation, '__dict__'):
        evaluation = asdict(evaluation) if hasattr(evaluation, '__dataclass_fields__') else evaluation.__dict__

    generators = {
        'buyer': _buyer_brief,
        'seller': _seller_brief,
        'investor': _investor_brief,
        'valuer': _valuer_brief,
    }

    gen = generators.get(audience, _buyer_brief)
    return gen(evaluation, rent_data, adjustments, uncertainty, income_value)


def _base_brief(evaluation, uncertainty):
    """Common elements for all briefs."""
    address = evaluation.get('address', '—')
    asset_type = evaluation.get('asset_type', '—')
    plot_area = evaluation.get('plot_area_m2')
    district = evaluation.get('gis_district_aname', '—')

    # Extract valuation figures
    blended = evaluation.get('blended') or {}
    val_total = blended.get('blended_value')
    val_low = blended.get('blended_low')
    val_high = blended.get('blended_high')

    banner = ''
    if uncertainty:
        banner = uncertainty.get('banner_ar', '') if isinstance(uncertainty, dict) else getattr(uncertainty, 'banner_ar', '')

    return {
        'address': address,
        'asset_type': asset_type,
        'plot_area_m2': plot_area,
        'district': district,
        'valuation_total': val_total,
        'valuation_low': val_low,
        'valuation_high': val_high,
        'material_uncertainty_banner': banner,
        'disclaimer': evaluation.get('disclaimer', ''),
        'valuation_date': evaluation.get('valuation_date', datetime.now().strftime('%Y-%m-%d')),
    }


def _buyer_brief(evaluation, rent_data, adjustments, uncertainty, income_value):
    """Buyer-focused: Is the price fair? What to negotiate?"""
    base = _base_brief(evaluation, uncertainty)

    # Listing comparison
    listing = evaluation.get('listing_comparison') or {}
    market_pos = evaluation.get('market_position') or {}

    sections = []

    # Section 1: VERDICT — only meaningful when user provided a listing_price.
    # Without it, there's no benchmark to evaluate. Skip the section entirely
    # rather than rendering "position: no_benchmark" raw text.
    if listing.get('listing_price'):
        sections.append({
            'id': 'verdict',
            'title_ar': 'هل السعر معقول؟',
            'content': {
                'listing_price': listing.get('listing_price'),
                'benchmark': listing.get('benchmark_total') or base['valuation_total'],
                'gap_pct': listing.get('gap_pct'),
                'position': market_pos.get('position_label', 'at_market'),
                'description_ar': market_pos.get('description_ar', ''),
            },
        })

    # Section 2: NEGOTIATION RANGE
    buyer_ceiling = round(base['valuation_total'] * 1.10) if base['valuation_total'] else None
    fair_range = {
        'floor': base['valuation_low'],
        'ceiling': buyer_ceiling,
        'opening_offer': round(base['valuation_total'] * 0.90) if base['valuation_total'] else None,
        'note': 'لا تدفع أكثر من وسيط MoJ + 10%. ابدأ بعرض أقل 10% من التقييم.',
    }
    sections.append({
        'id': 'negotiation',
        'title_ar': 'نطاق التفاوض المقترح',
        'content': fair_range,
    })

    # Section 3: RED FLAGS
    flags = evaluation.get('listing_flags') or {}
    sections.append({
        'id': 'flags',
        'title_ar': 'المخاطر والإشارات',
        'content': {
            'red_flags': flags.get('red_flags', []),
            'green_flags': flags.get('green_flags', []),
            'has_excluding': flags.get('has_excluding_red_flag', False),
        },
    })

    # Section 4: WHAT TO ASK
    sections.append({
        'id': 'due_diligence',
        'title_ar': 'أسئلة يجب طرحها قبل الشراء',
        'content': [
            'اطلب بيان عقاري من وزارة العدل (يكشف الرهونات والخلافات)',
            'اسأل عن عمر البناء الحقيقي (ليس ما يقوله البائع)',
            'تحقق من تصنيف المنطقة (R1/R2/R3) — يحدد ما يمكنك بناؤه',
            'اطلب فواتير الخدمات (كهرباء/ماء) لآخر سنة',
            'إن كان مؤجراً: اطلب عقود الإيجار الحالية',
        ],
    })

    # Section 5: MATERIAL UNCERTAINTY (Sprint 2.14.0)
    # Adds the RICS VPS 5 MUC clause and per-property uncertainty.
    # Was previously only in valuer brief — now in buyer brief too because
    # the index.html MUC banner reads from this section.
    if uncertainty:
        unc = uncertainty if isinstance(uncertainty, dict) else asdict(uncertainty)
        sections.append({
            'id': 'material_uncertainty',
            'title_ar': 'تحفظات مادية وفق RICS VPS 4/5',
            'title_en': 'Material Uncertainty Declaration (RICS VPS 4 §3.2 + VPS 5)',
            'content': {
                'level': unc.get('level'),
                'factors': unc.get('factors', []),
                'known_unknowns': unc.get('known_unknowns', []),
                'recommendations': unc.get('recommendations', []),
                'rics_compliant': unc.get('rics_compliant', False),
                # RICS VPS 5 MUC fields — market-wide uncertainty
                'muc_clause_ar': unc.get('muc_clause_ar'),
                'muc_clause_en': unc.get('muc_clause_en'),
                'muc_basis_ar': unc.get('muc_basis_ar'),
                'muc_review_recommendation_ar': unc.get('muc_review_recommendation_ar'),
            },
        })

    return {
        'audience': 'buyer',
        'title_ar': 'تقرير المشتري',
        'title_en': 'Buyer Brief',
        **base,
        'sections': sections,
    }


def _seller_brief(evaluation, rent_data, adjustments, uncertainty, income_value):
    """Seller-focused: What's my property worth? How to price it?"""
    base = _base_brief(evaluation, uncertainty)
    sections = []

    # Section 1: YOUR PROPERTY VALUE
    sections.append({
        'id': 'valuation',
        'title_ar': 'قيمة عقارك',
        'content': {
            'estimated_value': base['valuation_total'],
            'range_low': base['valuation_low'],
            'range_high': base['valuation_high'],
            'note': 'مبني على صفقات بيع فعلية مسجلة في وزارة العدل — ليس أسعار إعلانات.',
        },
    })

    # Section 2: PRICING STRATEGY
    if base['valuation_total']:
        val = base['valuation_total']
        sections.append({
            'id': 'pricing',
            'title_ar': 'استراتيجية التسعير',
            'content': {
                'aggressive_price': round(val * 1.15),
                'realistic_price': round(val * 1.10),
                'quick_sale_price': round(val * 1.00),
                'market_ceiling': round(val * 1.30),
                'note': ('ابدأ بسعر وسيط MoJ + 10-15%. '
                         'لا تتجاوز +30% — السوق يرفض الإعلانات المبالغة. '
                         'حدّث الإعلان كل أسبوعين.'),
            },
        })

    # Section 3: TREND
    trend = evaluation.get('trend')
    if trend:
        sections.append({
            'id': 'trend',
            'title_ar': 'اتجاه السوق',
            'content': trend,
        })

    # Section 4: SELLING TIPS
    sections.append({
        'id': 'tips',
        'title_ar': 'نصائح للبيع',
        'content': [
            'أفرغ العقار إن أمكن — الوحدات الفارغة تُباع أسرع',
            'صوِّر 6-10 صور جودة عالية (لا لقطات شاشة)',
            'اذكر سعر القدم المربع في الإعلان (المشتري يقارن بهذا)',
            'استجب للاستفسارات خلال ساعتين',
            'لا تكشف عن سعرك الأدنى مبكراً',
        ],
    })

    return {
        'audience': 'seller',
        'title_ar': 'تقرير البائع',
        'title_en': 'Seller Brief',
        **base,
        'sections': sections,
    }


def _investor_brief(evaluation, rent_data, adjustments, uncertainty, income_value):
    """Investor-focused: Yield, payback, sensitivity."""
    base = _base_brief(evaluation, uncertainty)
    sections = []

    # Section 1: YIELD ANALYSIS
    rental = evaluation.get('rental_analysis') or {}
    yield_section = {
        'gross_yield_pct': None,
        'net_yield_pct': None,
        'payback_years': None,
        'noi': None,
    }
    if rental and 'on_valuation' in rental:
        ov = rental['on_valuation']
        yield_section.update({
            'gross_yield_pct': ov.get('gross_yield_pct'),
            'net_yield_pct': ov.get('net_yield_pct'),
            'payback_years': ov.get('payback_years'),
            'noi': rental.get('annual_net'),
        })
    elif income_value:
        yield_section.update({
            'gross_yield_pct': income_value.get('gross_yield_pct'),
            'net_yield_pct': income_value.get('net_yield_pct'),
            'noi': income_value.get('noi'),
        })

    sections.append({
        'id': 'yield',
        'title_ar': 'تحليل العائد',
        'content': yield_section,
    })

    # Section 2: INCOME VALUE
    if income_value:
        sections.append({
            'id': 'income_value',
            'title_ar': 'القيمة بمنهج الدخل',
            'content': {
                'income_value': income_value.get('income_value'),
                'cap_rate_used': income_value.get('cap_rate_used'),
                'annual_gross': income_value.get('annual_gross_rent'),
                'noi': income_value.get('noi'),
                'costs': income_value.get('costs'),
                'opex_ratio': income_value.get('opex_ratio'),
            },
        })

    # Section 3: SENSITIVITY
    if income_value and 'sensitivity' in income_value:
        sections.append({
            'id': 'sensitivity',
            'title_ar': 'تحليل الحساسية',
            'content': income_value['sensitivity'],
            'note': 'ماذا لو تغيّر Cap Rate أو رسوم الخدمات؟',
        })

    # Section 4: RENT DATA
    if rent_data:
        sections.append({
            'id': 'rent_reference',
            'title_ar': 'مرجع الإيجار',
            'content': {
                'monthly_median': rent_data.get('monthly_median'),
                'annual_range': [rent_data.get('annual_low'), rent_data.get('annual_high')],
                'n': rent_data.get('n'),
                'confidence': rent_data.get('confidence'),
                'caveats': rent_data.get('caveats', []),
            },
        })

    # Section 5: MARKET CONTEXT
    sections.append({
        'id': 'market_context',
        'title_ar': 'السياق السوقي',
        'content': {
            'qatar_benchmark': '5-6% عائد صافي للشقق السكنية = طبيعي',
            'above_6_net': 'أكثر من 6% صافي = فرصة تستحق الفحص',
            'below_4_net': 'أقل من 4% صافي = ضعيف، تجنَّب',
        },
    })

    return {
        'audience': 'investor',
        'title_ar': 'تقرير المستثمر',
        'title_en': 'Investor Brief',
        **base,
        'sections': sections,
    }


def _valuer_brief(evaluation, rent_data, adjustments, uncertainty, income_value):
    """Valuer-focused (RICS): Full comparables, adjustments, method weights."""
    base = _base_brief(evaluation, uncertainty)
    sections = []

    # Section 1: METHODOLOGY APPLIED
    blended = evaluation.get('blended') or {}
    moj_val = evaluation.get('valuation') or {}
    repl_cost = evaluation.get('replacement_cost') or {}

    methods = []
    if moj_val.get('moj_median_total'):
        methods.append({
            'name': 'Market Comparable (MoJ)',
            'value': moj_val.get('moj_median_total'),
            'weight': blended.get('moj_weight', 0),
            'n': moj_val.get('bracket_n'),
            'bracket': moj_val.get('bracket_label'),
            'window': moj_val.get('window_used'),
        })
    if repl_cost.get('total_replacement_value'):
        methods.append({
            'name': 'Replacement Cost',
            'value': repl_cost.get('total_replacement_value'),
            'weight': blended.get('replacement_weight', 0),
        })
    if income_value:
        methods.append({
            'name': 'Income Capitalization',
            'value': income_value.get('income_value'),
            'weight': 0,  # will be set when 3-way blend is implemented
            'cap_rate': income_value.get('cap_rate_used'),
            'noi': income_value.get('noi'),
        })

    sections.append({
        'id': 'methodology',
        'title_ar': 'المنهجية المطبقة',
        'title_en': 'Methodology Applied',
        'content': {
            'methods': methods,
            'blend_reason': blended.get('blend_reason', ''),
            'blended_value': blended.get('blended_value'),
            'range': [blended.get('blended_low'), blended.get('blended_high')],
        },
    })

    # Section 2: COMPARABLE ADJUSTMENTS
    if adjustments:
        adj_data = adjustments if isinstance(adjustments, dict) else asdict(adjustments)
        sections.append({
            'id': 'adjustments',
            'title_ar': 'جدول تعديل المقارنات',
            'title_en': 'Comparable Adjustments Table',
            'content': {
                'raw_median_per_m2': adj_data.get('raw_median_per_m2'),
                'adjusted_median_per_m2': adj_data.get('adjusted_median_per_m2'),
                'adjusted_median_total': adj_data.get('adjusted_median_total'),
                'method_note': adj_data.get('method_note'),
                'n': adj_data.get('n'),
                'table': adj_data.get('adjustment_table', []),
            },
        })

    # Section 3: DATA SOURCES
    sources = [
        {'name': 'وزارة العدل — صفقات بيع فعلية', 'type': 'primary', 'date': 'أسبوعي'},
        {'name': 'نظم المعلومات الجغرافية (GIS قطر)', 'type': 'primary', 'date': 'مستمر'},
    ]
    if rent_data:
        sources.append({
            'name': 'المنصة العقارية — معاملات إيجار',
            'type': 'secondary',
            'date': str(rent_data.get('window_months', 24)) + ' شهر',
        })
    sections.append({
        'id': 'sources',
        'title_ar': 'مصادر البيانات',
        'title_en': 'Data Sources Consulted',
        'content': sources,
    })

    # Section 4: MATERIAL UNCERTAINTY
    if uncertainty:
        unc = uncertainty if isinstance(uncertainty, dict) else asdict(uncertainty)
        sections.append({
            'id': 'material_uncertainty',
            'title_ar': 'تحفظات مادية',
            'title_en': 'Material Uncertainty Declaration (RICS VPS 4 §3.2 + VPS 5)',
            'content': {
                'level': unc.get('level'),
                'factors': unc.get('factors', []),
                'known_unknowns': unc.get('known_unknowns', []),
                'recommendations': unc.get('recommendations', []),
                'rics_compliant': unc.get('rics_compliant', False),
                # Sprint 2.14.0 — RICS VPS 5 MUC fields (market-wide uncertainty)
                'muc_clause_ar': unc.get('muc_clause_ar'),
                'muc_clause_en': unc.get('muc_clause_en'),
                'muc_basis_ar': unc.get('muc_basis_ar'),
                'muc_review_recommendation_ar': unc.get('muc_review_recommendation_ar'),
            },
        })

    # Section 5: REASONING TRACE
    trace = evaluation.get('reasoning_trace')
    if trace:
        sections.append({
            'id': 'reasoning_trace',
            'title_ar': 'سلسلة المنطق',
            'title_en': 'Reasoning Trace (Audit Trail)',
            'content': trace,
        })

    # Section 6: GAPS
    sections.append({
        'id': 'gaps',
        'title_ar': 'فجوات البيانات',
        'title_en': 'Data Gaps',
        'content': [
            'MoJ لا تفصل بين عقار جديد ومتهالك (حالة المبنى غير معروفة)',
            'لا فصل قيمة الأرض عن البناء في صفقات الفلل',
            'بيانات الإيجار على مستوى البلدية فقط — لا منطقة فرعية',
            'لا بيانات per-tower (نفس المبنى الفاخر والعادي يُعامَلان متشابهين)',
            'الإعلانات النشطة لا تُسحَب آلياً — سياق المنافسة مفقود',
        ],
    })

    return {
        'audience': 'valuer',
        'title_ar': 'تقرير المُقيِّم',
        'title_en': 'Valuer Brief (RICS-aligned)',
        **base,
        'sections': sections,
    }
