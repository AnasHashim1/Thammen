#!/usr/bin/env python3
"""
evaluate_v3.py — Thammen v3 evaluation layer.

Wraps evaluate_property.py (v2) and adds:
    1. Income approach via rent_reference.py (360K rental transactions)
    2. Individual comparable adjustments (RICS VPS 4 §7)
    3. Material Valuation Uncertainty declaration (RICS Red Book Global Standards, effective 31 January 2025 — VPGA 10 + VPS 6; IVS, effective 31 January 2025 — IVS 106)
    4. 3-way blended valuation (comparison + cost + income)
    5. Four audience-specific output briefs

Usage:
    python3 evaluate_v3.py 56 784 2 \\
        --moj-csv moj_weekly.csv \\
        --rent-dir /path/to/rental/xlsx \\
        --audience buyer \\
        [--listing-price 5000000]

    # programmatic
    from evaluate_v3 import evaluate_v3
    result = evaluate_v3(
        zone=56, street=784, building=2,
        moj_csv='moj_weekly.csv',
        rent_dir='/path/to/rental/xlsx',
        audience='investor',
        listing_price=5000000,
    )
"""

import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

# ── v2 engine ──
try:
    from evaluate_property import evaluate_property, PropertyEvaluation
    _V2_AVAILABLE = True
except ImportError:
    _V2_AVAILABLE = False

# ── v3 new modules ──
try:
    from rent_reference import (
        build_rent_reference, query_rent, estimate_annual_rent,
        estimate_villa_rent, income_approach_value, load_all_rental_xlsx,
    )
    _RENT_AVAILABLE = True
except ImportError:
    _RENT_AVAILABLE = False

try:
    from comparable_adjustments import adjust_comparables, AdjustedResult
    _ADJ_AVAILABLE = True
except ImportError:
    _ADJ_AVAILABLE = False

try:
    from material_uncertainty import assess_uncertainty, UncertaintyLevel
    _UNC_AVAILABLE = True
except ImportError:
    _UNC_AVAILABLE = False

try:
    from output_briefs import generate_brief
    _BRIEFS_AVAILABLE = True
except ImportError:
    _BRIEFS_AVAILABLE = False

# Sprint 2.16.12 (B1) — removed dead import block:
#     try:
#         from sales_merge import load_all_sales_xlsx, compute_trend_from_xlsx
#         _SALES_AVAILABLE = True
#     except ImportError:
#         _SALES_AVAILABLE = False
# Neither imported function nor _SALES_AVAILABLE was referenced anywhere
# in the codebase. sales_merge.py is left on disk for potential future
# use, but the unused try/except is no longer pulled into the import path.


# ============================================================
# AREA → MUNICIPALITY MAPPING (for rental lookup)
# ============================================================

AREA_TO_MUNICIPALITY = {
    # From system prompt §4 + GIS verified
    'الخيسة': 'الظعاين',
    'لوسيل': 'الظعاين', 'لوسيل 69': 'الظعاين',
    'الوكير': 'الوكرة', 'الوكرة': 'الوكرة',
    'الدحيل': 'الدوحة', 'دحيل': 'الدوحة',
    'عين خالد': 'الريان',
    'الثمامة': 'الدوحة', 'الثمامة 46': 'الدوحة', 'الثمامة 50': 'الدوحة',
    'ام صلال علي': 'أم صلال', 'أم صلال علي': 'أم صلال',
    'الخريطيات': 'أم صلال',
    'المعمورة 56': 'الريان', 'المعمورة 43': 'الريان',
    'الغرافة': 'الريان',
    'ازغوى 51': 'الريان', 'ازغوى 71': 'الريان',
    'اللؤلؤة': 'الدوحة',
    'الخرايج': 'الدوحة',
    'المطار العتيق': 'الدوحة',
    'معيذر 53': 'الريان', 'معيذر 55': 'الريان',
    'الصخامة': 'الظعاين',
    'العب': 'الظعاين',
    'ام قرن': 'الظعاين',
    'المشاف': 'الوكرة',
    'بو هامور': 'الدوحة',
    'جبل ثعيلب': 'الوكرة',
    # Sprint 1 additions — Marikh + other common Doha areas
    'امريخ الجنوبي': 'الدوحة', 'المريخ': 'الدوحة', 'مريخ': 'الدوحة',
    'النصر': 'الدوحة', 'بني هاجر': 'الريان', 'الريان القديم': 'الريان',
    'النعيجة': 'الدوحة', 'نعيجة': 'الدوحة', 'نعيجة 44': 'الدوحة',
    'الشحانية': 'الشيحانية',
    'الخور': 'الخور والذخيرة', 'الذخيرة': 'الخور والذخيرة',
}


def get_municipality(area_name: str, gis_municipality: str = None) -> str:
    """Resolve municipality from area name or GIS result."""
    if gis_municipality:
        return gis_municipality
    return AREA_TO_MUNICIPALITY.get(area_name, '')


# ============================================================
# ASSET TYPE → RENTAL UNIT TYPE MAPPING
# ============================================================

def asset_to_rental_type(asset_type: str) -> str:
    """Map property asset type to rental unit type for income approach."""
    if not asset_type:
        return 'villa'
    # Normalize case — evaluate_property returns lowercase, but constants here are uppercase
    at = asset_type.upper()
    mapping = {
        'STANDALONE_VILLA': 'villa',
        'VILLA': 'villa',
        'PALACE': 'villa',
        'COMPOUND_SMALL': 'villa',
        'COMPOUND_LARGE': 'villa',
        'APARTMENT_BUILDING': 'apartment',
        'TOWER': 'apartment',
        'COMMERCIAL': 'retail',
        'OFFICE': 'office',
    }
    return mapping.get(at, 'villa')


def estimate_bedrooms(asset_type: str, plot_area_m2: float) -> int:
    """Estimate bedroom count from asset type and plot area."""
    if asset_type in ('APARTMENT_BUILDING', 'TOWER'):
        return 2  # typical unit
    # Villa: rough estimate from plot size
    if plot_area_m2 < 400:
        return 4
    elif plot_area_m2 < 700:
        return 5
    elif plot_area_m2 < 1000:
        return 6
    else:
        return 7


# ============================================================
# 3-WAY BLENDED VALUATION
# ============================================================

def blend_three_way(
    moj_value: Optional[float],
    replacement_value: Optional[float],
    income_value: Optional[float],
    asset_type: str,
    moj_n: int = 0,
    income_confidence: str = 'estimated',
) -> dict:
    """
    Blend three valuation approaches with weights based on asset type.

    Weight allocation philosophy:
        - Residential villa (owner-occupied): comparison dominant
        - Investment apartment: income dominant
        - Land: comparison only
        - Compound: income only (no comparable)
        - Mixed: even split with quality adjustments
    """
    available = {}
    if moj_value and moj_value > 0:
        available['comparison'] = moj_value
    if replacement_value and replacement_value > 0:
        available['cost'] = replacement_value
    if income_value and income_value > 0:
        available['income'] = income_value

    if not available:
        return {'blended_value': None, 'method': 'none', 'weights': {}}

    # Base weights by asset type
    if asset_type in ('RAW_LAND',):
        base_w = {'comparison': 1.0, 'cost': 0.0, 'income': 0.0}
    elif asset_type in ('STANDALONE_VILLA', 'PALACE'):
        base_w = {'comparison': 0.60, 'cost': 0.25, 'income': 0.15}
    elif asset_type in ('APARTMENT_BUILDING', 'TOWER'):
        base_w = {'comparison': 0.30, 'cost': 0.15, 'income': 0.55}
    elif asset_type in ('COMPOUND_SMALL',):
        base_w = {'comparison': 0.30, 'cost': 0.20, 'income': 0.50}
    elif asset_type in ('COMPOUND_LARGE',):
        base_w = {'comparison': 0.0, 'cost': 0.15, 'income': 0.85}
    elif asset_type in ('COMMERCIAL', 'INDUSTRIAL'):
        base_w = {'comparison': 0.20, 'cost': 0.10, 'income': 0.70}
    else:
        base_w = {'comparison': 0.50, 'cost': 0.25, 'income': 0.25}

    # Adjust for data quality
    if moj_n < 10:
        # Weak MoJ → shift weight to cost and income
        shift = base_w['comparison'] * 0.3
        base_w['comparison'] -= shift
        base_w['cost'] += shift * 0.4
        base_w['income'] += shift * 0.6

    if income_confidence in ('estimated', 'bound_only'):
        # Weak rental data → shift income weight to comparison/cost
        shift = base_w['income'] * 0.3
        base_w['income'] -= shift
        base_w['comparison'] += shift * 0.6
        base_w['cost'] += shift * 0.4

    # Zero out unavailable methods and renormalize
    for method in list(base_w.keys()):
        if method not in available:
            base_w[method] = 0.0

    total_w = sum(base_w.values())
    if total_w <= 0:
        return {'blended_value': None, 'method': 'none', 'weights': {}}

    weights = {k: round(v / total_w, 3) for k, v in base_w.items()}

    blended = sum(available.get(k, 0) * weights.get(k, 0) for k in weights)

    # Range: span of available methods with 5% buffer
    all_vals = list(available.values())
    low = round(min(all_vals) * 0.95)
    high = round(max(all_vals) * 1.05)

    # Divergence warning
    notes = []
    if len(all_vals) >= 2:
        spread = (max(all_vals) - min(all_vals)) / min(all_vals)
        if spread > 0.30:
            notes.append(
                f'المناهج تتباعد بـ {spread*100:.0f}%. '
                f'الفحص الميداني ضروري لحسم التباين.'
            )

    reason_parts = []
    for method, w in sorted(weights.items(), key=lambda x: -x[1]):
        if w > 0:
            val = available.get(method)
            name_ar = {'comparison': 'المقارنة', 'cost': 'التكلفة', 'income': 'الدخل'}.get(method, method)
            reason_parts.append(f'{name_ar} {w*100:.0f}% ({val:,.0f} ر.ق)' if val else f'{name_ar} {w*100:.0f}%')

    return {
        'blended_value': round(blended),
        'blended_low': low,
        'blended_high': high,
        'weights': weights,
        'method_values': available,
        'blend_reason': ' + '.join(reason_parts),
        'notes': notes,
        'asset_type': asset_type,
    }


# ============================================================
# MAIN EVALUATION v3
# ============================================================

# Global rent reference cache
_RENT_REF_CACHE = {}

def _get_rent_ref(rent_dir: str) -> dict:
    if rent_dir not in _RENT_REF_CACHE:
        _RENT_REF_CACHE[rent_dir] = build_rent_reference(rent_dir)
    return _RENT_REF_CACHE[rent_dir]


def evaluate_v3(
    zone: int = None,
    street: int = None,
    building: int = None,
    moj_csv: str = None,
    rent_dir: str = None,
    rent_ref: dict = None,
    sales_dir: str = None,
    audience: str = 'buyer',
    listing_price: float = None,
    listing_area_m2: float = None,
    listing_description: str = None,
    bedrooms: int = None,
    area_name: str = None,
    municipality: str = None,
    asset_type: str = None,
    plot_area_m2: float = None,
    # v2 evaluation result (if already computed)
    v2_result: dict = None,
) -> dict:
    """
    Full v3 evaluation pipeline.

    1. Run v2 evaluation (comparison + cost)
    2. Add income approach via rent_reference
    3. Compute 3-way blend
    4. Run comparable adjustments
    5. Assess material uncertainty
    6. Generate audience brief

    Returns:
        dict containing full evaluation + brief for the requested audience
    """

    # ── Step 1: v2 evaluation ──
    if v2_result is not None:
        eval_dict = v2_result if isinstance(v2_result, dict) else asdict(v2_result)
    elif _V2_AVAILABLE and moj_csv:
        # NOTE: evaluate_property expects moj_csv_path (Path), not moj_csv (str)
        # and does NOT accept area_name / listing_area_m2 / listing_description here.
        # Bug fix: only pass the parameters evaluate_property actually accepts.
        from pathlib import Path as _P
        eval_obj = evaluate_property(
            zone=zone, street=street, building=building,
            moj_csv_path=_P(moj_csv),
            listing_price=listing_price,
        )
        eval_dict = asdict(eval_obj) if hasattr(eval_obj, '__dataclass_fields__') else eval_obj.__dict__
    else:
        # Minimal evaluation without v2 engine
        eval_dict = {
            'address': f'{zone}/{street}/{building}' if zone else '—',
            'asset_type': asset_type or 'STANDALONE_VILLA',
            'plot_area_m2': plot_area_m2,
            'gis_district_aname': area_name,
            'moj_area_name': area_name,
            'valuation': None,
            'replacement_cost': None,
            'blended': None,
            'listing_comparison': None,
            'listing_flags': None,
            'trend': None,
            'rental_analysis': None,
            'market_position': None,
            'reasoning_trace': None,
            'disclaimer': (
                'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. '
                'هذا تحليل معلوماتي للقرار، وليس تقييماً عقارياً معتمداً وفق RICS/IVS. '
                'للأغراض الرسمية (قروض، محاكم، تقارير محاسبية) يلزم مُقيِّم معتمد.'
            ),
        }

    # Extract key values
    at = eval_dict.get('asset_type', asset_type or 'STANDALONE_VILLA')
    pa = eval_dict.get('plot_area_m2', plot_area_m2)
    area = eval_dict.get('moj_area_name', area_name)
    muni = municipality or get_municipality(area or '', eval_dict.get('gis_municipality'))

    # MoJ values from v2
    val = eval_dict.get('valuation') or {}
    moj_value = val.get('moj_median_total') or val.get('fair_price_total')
    moj_n = val.get('bracket_n', 0)
    repl = eval_dict.get('replacement_cost') or {}
    repl_value = repl.get('total_replacement_value')

    # ── Step 2: Income approach ──
    rent_data = None
    income_val = None

    if _RENT_AVAILABLE:
        if rent_ref is None and rent_dir:
            rent_ref = _get_rent_ref(rent_dir)

        if rent_ref:
            rental_type = asset_to_rental_type(at)
            br = bedrooms or estimate_bedrooms(at, pa or 500)
            rent_data = estimate_annual_rent(rent_ref, muni, rental_type, rooms=br)

            if rent_data and rent_data.get('annual_median'):
                # Get service charge if available
                sc_annual = 0
                sc_conf = 'estimated'
                ra = eval_dict.get('rental_analysis') or {}
                cb = ra.get('cost_breakdown') or {}
                if cb.get('service_charge_annual'):
                    sc_annual = cb['service_charge_annual']
                    sc_conf = cb.get('service_charge_confidence', 'estimated')

                income_val = income_approach_value(
                    annual_rent=rent_data['annual_median'],
                    cap_rate=0.065,  # Qatar market default
                    service_charge_annual=sc_annual,
                    vacancy_pct=0.085,
                    maintenance_pct=0.005,
                    management_pct=0.0,
                )

    # ── Step 3: 3-way blend ──
    blend = blend_three_way(
        moj_value=moj_value,
        replacement_value=repl_value,
        income_value=income_val.get('income_value') if income_val else None,
        asset_type=at,
        moj_n=moj_n or 0,
        income_confidence=rent_data.get('confidence', 'estimated') if rent_data else 'estimated',
    )
    eval_dict['blended_v3'] = blend

    # ── Step 4: Comparable adjustments ──
    adj_result = None
    if _ADJ_AVAILABLE and val.get('transactions'):
        trend = eval_dict.get('trend') or {}
        slope = trend.get('slope', 0) if isinstance(trend, dict) else 0

        adj_result = adjust_comparables(
            transactions=val['transactions'],
            target_area_m2=pa or 500,
            trend_slope_annual=slope,
        )
        if adj_result:
            eval_dict['adjusted_comparables'] = {
                'raw_median_per_m2': adj_result.raw_median_per_m2,
                'adjusted_median_per_m2': adj_result.adjusted_median_per_m2,
                'adjusted_median_total': adj_result.adjusted_median_total,
                'n': adj_result.n,
                'method_note': adj_result.method_note,
                'caveats': adj_result.caveats,
            }

    # ── Step 5: Material uncertainty ──
    uncertainty = None
    if _UNC_AVAILABLE:
        _trend = eval_dict.get('trend') if isinstance(eval_dict.get('trend'), dict) else None
        uncertainty = assess_uncertainty(
            moj_n=moj_n,
            rent_n=rent_data.get('n') if rent_data else None,
            trend_n_years=len(_trend.get('years', [])) if _trend else None,
            has_field_inspection=False,
            building_condition_known=False,
            building_age_known=False,
            service_charge_confidence='estimated',
            bua_known=eval_dict.get('replacement_cost') is not None,
            asset_type=eval_dict.get('asset_type'),   # Sprint 2.21.0.5: land-aware
        )
        eval_dict['material_uncertainty'] = {
            'level': uncertainty.level,
            'banner_ar': uncertainty.banner_ar,
            'banner_en': uncertainty.banner_en,
            'factors': uncertainty.factors,
            'known_unknowns': uncertainty.known_unknowns,
            'recommendations': uncertainty.recommendations,
            'rics_compliant': uncertainty.rics_compliant,
            # Sprint 2.14.0 hotfix — propagate Material Valuation Uncertainty (MVU) clause fields
            # (citation updated Sprint 2.22.0a/12 Phase 1.5b: now VPGA 10 + VPS 6 + IVS 106, effective 31 January 2025)
            'muc_clause_ar': uncertainty.muc_clause_ar,
            'muc_clause_en': uncertainty.muc_clause_en,
            'muc_basis_ar': uncertainty.muc_basis_ar,
            'muc_review_recommendation_ar': uncertainty.muc_review_recommendation_ar,
        }

    # ── Step 6: Generate brief ──
    brief = None
    if _BRIEFS_AVAILABLE:
        brief = generate_brief(
            evaluation=eval_dict,
            audience=audience,
            rent_data=rent_data,
            adjustments=adj_result,
            uncertainty=uncertainty,
            income_value=income_val,
        )

    # ── Assemble final result ──
    result = {
        'v3': True,
        'evaluation': eval_dict,
        'income_approach': income_val,
        'rent_reference': rent_data,
        'blend_3way': blend,
        'material_uncertainty': eval_dict.get('material_uncertainty'),
        'brief': brief,
        'audience': audience,
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }

    return result


# ============================================================
# CLI
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Thammen v3 Evaluation')
    parser.add_argument('zone', type=int, nargs='?')
    parser.add_argument('street', type=int, nargs='?')
    parser.add_argument('building', type=int, nargs='?')
    parser.add_argument('--moj-csv', default='moj_weekly.csv')
    parser.add_argument('--rent-dir', default=None)
    parser.add_argument('--sales-dir', default=None)
    parser.add_argument('--audience', default='buyer', choices=['buyer', 'seller', 'investor', 'valuer'])
    parser.add_argument('--listing-price', type=float, default=None)
    parser.add_argument('--area-name', default=None)
    parser.add_argument('--output', default=None)

    args = parser.parse_args()

    result = evaluate_v3(
        zone=args.zone,
        street=args.street,
        building=args.building,
        moj_csv=args.moj_csv,
        rent_dir=args.rent_dir,
        sales_dir=args.sales_dir,
        audience=args.audience,
        listing_price=args.listing_price,
        area_name=args.area_name,
    )

    output = args.output or f'{args.zone}_{args.street}_{args.building}_v3.json'
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    # Print summary
    blend = result.get('blend_3way', {})
    unc = result.get('material_uncertainty', {})
    brief = result.get('brief', {})

    print(f"\n{'='*60}")
    print(f"  Thammen v3 — {brief.get('title_ar', args.audience)}")
    print(f"{'='*60}")

    if unc:
        print(f"\n  {unc.get('banner_ar', '')}")

    if blend.get('blended_value'):
        print(f"\n  القيمة المُدمَجة: {blend['blended_value']:,} ر.ق")
        print(f"  النطاق: {blend.get('blended_low', 0):,} — {blend.get('blended_high', 0):,}")
        print(f"  الأوزان: {blend.get('blend_reason', '')}")

    income = result.get('income_approach')
    if income:
        print(f"\n  منهج الدخل: {income['income_value']:,} ر.ق")
        print(f"  العائد الصافي: {income.get('net_yield_pct')}%")

    print(f"\n  Saved to {output}")


if __name__ == '__main__':
    main()
