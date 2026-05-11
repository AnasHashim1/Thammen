#!/usr/bin/env python3
"""
evaluate_unified.py — Thammen AVM orchestrator (Sprint 1.b)

Methodology name (RICS-aligned):
    "Sales Comparison-led AVM with Three-Approach Reconciliation"

    Primary value source: Sales Comparison Approach (RICS VPS 4)
        - Bracket comparison when bracket_n >= 20
        - Geographic widening adjustment when bracket_n < 20 (VPS 4 §7)
    Cross-checks (NOT weighted into primary):
        - Cost Approach (sanity check for old buildings)
        - Income Approach (sentiment check for asset class)
    Reconciliation: explicit agreement/divergence indicator

Important departure from Sprint 1.a:
    Sprint 1.a wrongly blended three approaches with equal weights for a
    residential villa. This produced 2.9M for Marikh when truth was ~4.5M.
    Sprint 1.b keeps comparison as primary (correct for residential per
    IVS 105) and uses cost/income only for reconciliation transparency.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Dict

try:
    from evaluate_property import evaluate_property, PropertyEvaluation, BuaBreakdown
    _V2_OK = True
except ImportError as e:
    _V2_OK = False
    print(f"FATAL: evaluate_property not loadable: {e}", file=sys.stderr)

try:
    from evaluate_v3 import evaluate_v3
    _V3_OK = True
except ImportError as e:
    _V3_OK = False
    print(f"Warning: evaluate_v3 not loadable: {e}", file=sys.stderr)

try:
    from geo_reference_v2 import build_reference_geo_v2
    _GEO_OK = True
except ImportError:
    _GEO_OK = False

try:
    from listings_db import fetch_active_listings, weighted_listings_median
    _LISTINGS_OK = True
except ImportError:
    _LISTINGS_OK = False

try:
    from geometric_factors import analyze_geometric_factors
    _GEOMETRIC_OK = True
except ImportError as e:
    _GEOMETRIC_OK = False
    print(f"Warning: geometric_factors not loadable: {e}", file=sys.stderr)


# ============================================================
# Constants — RICS-aligned for Qatar market
# ============================================================

# Cap rates by asset type (Qatar empirical, RICS Income Approach)
# Source: convergence of FGREALTY data, market norms, and asset class theory
CAP_RATES_BY_ASSET = {
    # Owner-occupied / residential — lower yield because location/lifestyle dominate
    'standalone_villa':   0.040,   # 4.0%
    'villa':              0.040,
    'palace':             0.035,   # luxury — even lower
    # Investment-grade — higher yield required to compensate for management
    'compound_small':     0.060,   # 6.0%
    'compound_large':     0.075,   # 7.5%
    'apartment_building': 0.065,
    'tower':              0.060,
    # Commercial — higher yield (more volatile, depreciation risk)
    'commercial':         0.080,
    'industrial':         0.085,
    # Land — income approach not applicable
    'raw_land':           None,
    'land':               None,
    'agricultural':       None,
}

# Sample size thresholds (RICS VPS 4 §3.2 — reliability tiers)
MIN_N_RELIABLE   = 20  # full confidence
MIN_N_INDICATIVE = 10  # use with caveat
MIN_N_BOUND_ONLY = 5   # bounds only

# Operating expense ratio (Qatar typical for residential)
OPEX_RATIO_RESIDENTIAL = 0.23   # maintenance + vacancy + management


# ============================================================
# Caches
# ============================================================

_MOJ_CACHE: Dict[str, list] = {}
_RENT_REF_CACHE: Dict[str, dict] = {}


def _get_moj_rows(csv_path: str) -> list:
    key = str(Path(csv_path).resolve())
    if key in _MOJ_CACHE:
        return _MOJ_CACHE[key]
    import csv
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    _MOJ_CACHE[key] = rows
    return rows


def _get_rent_ref(json_path: Optional[str]) -> Optional[dict]:
    if not json_path:
        return None
    if json_path in _RENT_REF_CACHE:
        return _RENT_REF_CACHE[json_path]
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ref = data.get('reference', data) if isinstance(data, dict) else data
        _RENT_REF_CACHE[json_path] = ref
        return ref
    except Exception as e:
        print(f"[rent_ref] load failed: {e}", file=sys.stderr)
        return None


# ============================================================
# Helpers
# ============================================================

def _condition_to_reno(condition: Optional[str]) -> tuple:
    mapping = {
        'new':         (True, True),
        'renovated':   (True, True),
        'excellent':   (True, True),
        'good':        (True, False),
        'maintenance': (False, False),
        'fair':        (False, False),
        'poor':        (False, False),
    }
    return mapping.get(condition or 'good', (False, False))


def _build_simple_bua(floors: int, annexes: int) -> Optional['BuaBreakdown']:
    if not _V2_OK or not floors:
        return None
    return BuaBreakdown(
        main_footprint_m2=300,
        basement_m2=0,
        upper_floors_m2=300 * 0.85 * (floors - 1) if floors >= 2 else 0,
        upper_floor_count=max(0, floors - 1),
        annexes_m2=annexes * 50 if annexes else 0,
        annex_count=annexes,
        external_m2=0,
    )


def _r100k(n):
    if n is None:
        return None
    return round(n / 100000) * 100000


# ============================================================
# Geo widening (the primary RICS adjustment when bracket is thin)
# ============================================================

def _run_geo_v2(ev, moj_csv_path: str):
    lat = lon = None
    try:
        from qatar_gis import QatarGIS
        gis = QatarGIS(verbose=False)
        parts = ev.address.split('/')
        loc = gis.find_property(int(parts[0]), int(parts[1]), int(parts[2]))
        if loc:
            lat = loc.lat
            lon = loc.lon
    except Exception:
        return None
    if not lat or not lon:
        return None

    asset_to_cat = {
        'standalone_villa': 'villa', 'villa': 'villa',
        'palace': 'palace',
        'raw_land': 'land', 'land': 'land',
        'compound_small': 'compound', 'compound_large': 'compound',
    }
    cat = asset_to_cat.get(ev.asset_type, 'villa')

    try:
        rows = _get_moj_rows(moj_csv_path)
        import signal
        def _handler(signum, frame):
            raise TimeoutError('geo_v2 timeout')
        old = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(15)
        try:
            return build_reference_geo_v2(
                rows=rows, lat=lat, lon=lon,
                category=cat,
                plot_area_m2=ev.plot_area_m2,
                target_zoning=None,
            )
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
    except Exception as e:
        print(f"[geo_v2] failed: {e}", file=sys.stderr)
        return None


# ============================================================
# Primary value selection (Sales Comparison Approach)
# ============================================================

def _select_primary_comparison(ev, geo_v2) -> Optional[dict]:
    """
    Choose the primary comparison value following RICS VPS 4.

    Priority:
        1. Bracket median if bracket_n >= 20 (most specific, most reliable)
        2. Geographic widening if it adds substantial samples (RICS VPS 4 §7)
        3. Bracket median with low-confidence caveat
    """
    bracket_n = (ev.valuation.bracket_n or 0) if ev.valuation else 0
    bracket_value = None
    if ev.valuation:
        bracket_value = ev.valuation.fair_price_total or ev.valuation.moj_median_total

    geo_n = (geo_v2.get('total_n') or 0) if geo_v2 else 0
    geo_value = geo_v2.get('estimated_value') if geo_v2 else None

    # Case 1: Bracket has strong sample
    if bracket_n >= MIN_N_RELIABLE and bracket_value:
        return {
            'value': bracket_value,
            'low':   ev.valuation.estimated_value_low,
            'high':  ev.valuation.estimated_value_high,
            'method': 'comparison_bracket',
            'method_label_ar': f'مقارنة شريحية مباشرة (RICS VPS 4)',
            'n': bracket_n,
            'source_ar': f'وسيط {bracket_n} معاملة في نفس الشريحة والمنطقة',
        }

    # Case 2: Bracket weak but widening succeeded
    if geo_n >= MIN_N_RELIABLE and geo_value and geo_n >= max(bracket_n * 3, 15):
        return {
            'value': geo_value,
            'low':   geo_v2.get('range_low'),
            'high':  geo_v2.get('range_high'),
            'method': 'comparison_widened',
            'method_label_ar': 'مقارنة بتوسيع جغرافي (RICS VPS 4 §7)',
            'n': geo_n,
            'source_ar': f'وسيط {geo_n} معاملة بعد توسيع للمناطق المجاورة مع تسوية موقع',
        }

    # Case 3: Use widening even if not as large (when bracket is too thin)
    if geo_n >= MIN_N_INDICATIVE and geo_value and bracket_n < MIN_N_INDICATIVE:
        return {
            'value': geo_value,
            'low':   geo_v2.get('range_low'),
            'high':  geo_v2.get('range_high'),
            'method': 'comparison_widened_indicative',
            'method_label_ar': 'مقارنة بتوسيع جغرافي — إرشادي (RICS VPS 4 §7)',
            'n': geo_n,
            'source_ar': f'وسيط {geo_n} معاملة بعد توسيع — إرشادي بسبب عينة محدودة',
        }

    # Case 4: Fallback — bracket only with low-confidence flag
    if bracket_value and bracket_n >= MIN_N_BOUND_ONLY:
        return {
            'value': bracket_value,
            'low':   ev.valuation.estimated_value_low,
            'high':  ev.valuation.estimated_value_high,
            'method': 'comparison_thin',
            'method_label_ar': f'مقارنة شريحية ضعيفة (n={bracket_n})',
            'n': bracket_n,
            'source_ar': f'عينة ضعيفة جداً (n={bracket_n}) — اعتبر هذا تقديراً مبدئياً',
        }

    return None


# ============================================================
# Cross-check approaches (not weighted into primary)
# ============================================================

def _build_cost_crosscheck(ev) -> Optional[dict]:
    rc = getattr(ev, 'replacement_cost', None)
    if not rc:
        return None
    return {
        'value': rc.total_replacement_value,
        'land_value': getattr(rc, 'land_value', None),
        'building_value_new': getattr(rc, 'building_value_new', None),
        'building_value_depreciated': getattr(rc, 'building_value_depreciated', None),
        'building_age_years': getattr(rc, 'building_age_years', None),
        'depreciation_rate_pct': getattr(rc, 'depreciation_rate_pct', None),
        'bua_m2': getattr(rc, 'bua_m2', None),
        'tier': getattr(rc, 'construction_tier', None),
        'method_label_ar': 'طريقة التكلفة الإحلالية (RICS Cost Approach)',
        'role_ar': 'تأكيد منهجي — لا تدخل في القيمة النهائية لعقار سكني',
    }


def _build_income_crosscheck(rental_income, v3_rent_data, asset_type, primary_value) -> Optional[dict]:
    """
    Build income approach using:
      1. User's actual rent (priority)
      2. rent_reference median as fallback
    Cap rate selected by asset type.
    """
    cap_rate = CAP_RATES_BY_ASSET.get((asset_type or '').lower())
    if not cap_rate:
        return None  # not applicable (land, etc.)

    annual_rent = None
    rent_source = None
    rent_caveats = []

    if rental_income and rental_income > 0:
        annual_rent = rental_income * 12
        rent_source = 'actual_provided'
        rent_source_ar = 'إفادة العميل (الإيجار الفعلي)'
    elif v3_rent_data and v3_rent_data.get('annual_median'):
        annual_rent = v3_rent_data['annual_median']
        rent_source = 'rent_reference_municipality'
        rent_source_ar = f"وسيط البلدية (n={v3_rent_data.get('n')})"
        rent_caveats.append(
            'الإيجار من وسيط البلدية — قد يختلف للمنطقة الفرعية بـ ±30%'
        )
    else:
        return None

    noi = annual_rent * (1 - OPEX_RATIO_RESIDENTIAL)
    income_value = noi / cap_rate

    # Yields (descriptive)
    gross_yield = annual_rent / primary_value if primary_value else None
    net_yield   = noi / primary_value if primary_value else None

    yield_flag = None
    if net_yield is not None:
        if net_yield < 0.025:
            yield_flag = 'العائد الصافي منخفض جداً (<2.5%) — السوق سكني نقي، لا استثماري'
        elif net_yield > 0.07:
            yield_flag = 'العائد الصافي مرتفع (>7%) — مؤشر استثماري قوي'

    return {
        'value': round(income_value),
        'annual_rent': annual_rent,
        'monthly_rent': round(annual_rent / 12),
        'rent_source': rent_source,
        'rent_source_ar': rent_source_ar,
        'opex_ratio': OPEX_RATIO_RESIDENTIAL,
        'noi': round(noi),
        'cap_rate': cap_rate,
        'cap_rate_label_ar': f'معدل رسملة {cap_rate*100:.1f}% (نموذجي لـ {asset_type})',
        'gross_yield': round(gross_yield, 4) if gross_yield else None,
        'net_yield':   round(net_yield, 4) if net_yield else None,
        'yield_flag_ar': yield_flag,
        'caveats': rent_caveats,
        'method_label_ar': 'طريقة الدخل (RICS Income Approach)',
        'role_ar': 'تأكيد منهجي — لا تدخل في القيمة النهائية لعقار سكني',
    }


# ============================================================
# Reconciliation
# ============================================================

def _analyze_reconciliation(primary, cost, income) -> dict:
    """Compare approaches and produce reconciliation statement (RICS Red Book)."""
    if not primary:
        return {'status': 'no_primary', 'message_ar': 'لا توجد قيمة مقارنة — عينة غير كافية'}

    p_val = primary['value']
    methods = [('comparison', p_val)]
    if cost and cost.get('value'):
        methods.append(('cost', cost['value']))
    if income and income.get('value'):
        methods.append(('income', income['value']))

    if len(methods) < 2:
        return {'status': 'comparison_only', 'methods_count': 1}

    values = [v for _, v in methods]
    min_v, max_v = min(values), max(values)
    spread_pct = (max_v - min_v) / min_v * 100 if min_v > 0 else 100

    # Individual gaps from primary
    gaps = {}
    for name, v in methods:
        if name != 'comparison':
            gaps[name] = round((v - p_val) / p_val * 100, 1)

    if spread_pct < 15:
        return {
            'status': 'strong_convergence',
            'label_ar': 'تقارب قوي بين الطرق ✓',
            'message_ar': 'الطرق الثلاث تتقارب — ثقة عالية في القيمة',
            'spread_pct': round(spread_pct, 1),
            'gaps_pct': gaps,
        }
    if spread_pct < 30:
        return {
            'status': 'moderate_convergence',
            'label_ar': 'تقارب معقول',
            'message_ar': 'تباين متوسط بين الطرق — قد يعكس خصوصية العقار (عمر، إيجار، حالة)',
            'spread_pct': round(spread_pct, 1),
            'gaps_pct': gaps,
        }
    return {
        'status': 'divergence',
        'label_ar': 'تباين كبير ⚠️',
        'message_ar': 'تباين جوهري بين الطرق — يلزم فحص ميداني أو إعادة تقييم البيانات',
        'spread_pct': round(spread_pct, 1),
        'gaps_pct': gaps,
    }


# ============================================================
# Unified entry point
# ============================================================

def evaluate_thammen(
    zone: int,
    street: int,
    building: int,
    moj_csv_path: str = 'moj_weekly.csv',
    rent_ref_path: Optional[str] = 'rent_reference.json',
    listing_price: Optional[float] = None,
    rental_income: Optional[float] = None,
    floors: Optional[int] = None,
    condition: Optional[str] = None,
    annexes: int = 0,
    bua_breakdown: Optional['BuaBreakdown'] = None,
    audience: str = 'buyer',
    use_listings: bool = True,
    use_geo_v2: bool = True,
) -> Dict:
    if not _V2_OK:
        return {'status': 'engine_unavailable', 'error': 'evaluate_property not loaded'}

    # ── Step 1: v2 baseline ──
    has_reno, full_reno = _condition_to_reno(condition)
    if bua_breakdown is None and floors:
        bua_breakdown = _build_simple_bua(floors, annexes)

    try:
        ev = evaluate_property(
            zone=zone, street=street, building=building,
            moj_csv_path=Path(moj_csv_path),
            listing_price=listing_price,
            bua_breakdown=bua_breakdown,
            has_renovation=has_reno,
            full_renovation=full_reno,
            rental_income=rental_income,
            include_age=True,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'status': 'evaluation_failed', 'error': str(e)}

    eval_dict = asdict(ev) if hasattr(ev, '__dataclass_fields__') else ev.__dict__

    # ── Step 1.5: Sprint 2 — Geometric factors (corner, HBU, named landmarks) ──
    geometric = None
    if _GEOMETRIC_OK:
        try:
            # Extract PIN and GPS from raw_property_report dict
            pin = None
            lat = lon = None
            rpr = getattr(ev, 'raw_property_report', None)
            if isinstance(rpr, dict):
                pin = rpr.get('pin')
                gps = rpr.get('gps')
                if gps and isinstance(gps, (list, tuple)) and len(gps) >= 2:
                    # GPS stored as [lon, lat] per qatar_gis convention
                    lon, lat = gps[0], gps[1]

            # Extract zoning code from factors_detail
            zoning_code = None
            if ev.valuation and ev.valuation.factors_detail:
                for f in ev.valuation.factors_detail:
                    if f.get('code') == 'zoning':
                        ev_str = (f.get('evidence', '') or '') + ' ' + (f.get('label_ar', '') or '')
                        for code in ['R1', 'R2', 'R3', 'C1', 'C2', 'C', 'MU']:
                            if code in ev_str:
                                zoning_code = code
                                break
                        break

            if pin and lat and lon:
                import signal
                def _handler(signum, frame):
                    raise TimeoutError('geometric timeout')
                old = signal.signal(signal.SIGALRM, _handler)
                signal.alarm(20)
                try:
                    geometric = analyze_geometric_factors(int(pin), float(lat), float(lon), zoning_code)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old)
        except Exception as e:
            print(f"[geometric] failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)

    # ── Step 2: Geographic widening (the RICS VPS 4 §7 adjustment) ──
    geo_v2_result = _run_geo_v2(ev, moj_csv_path) if (use_geo_v2 and _GEO_OK) else None

    # ── Step 3: Select PRIMARY comparison value ──
    primary = _select_primary_comparison(ev, geo_v2_result)

    # ── Step 4: v3 layer — for income data, material uncertainty, brief ──
    # (NOT for blending — its blend_3way is ignored)
    v3_result = None
    if _V3_OK:
        rent_ref = _get_rent_ref(rent_ref_path)
        muni_hint = (
            getattr(ev, 'gis_municipality_aname', None)
            or getattr(ev, 'gis_municipality', None)
        )
        try:
            v3_result = evaluate_v3(
                zone=zone, street=street, building=building,
                rent_ref=rent_ref,
                audience=audience,
                listing_price=listing_price,
                v2_result=eval_dict,
                area_name=getattr(ev, 'gis_district_aname', None) or getattr(ev, 'moj_area_name', None),
                municipality=muni_hint,
            )
        except Exception as e:
            print(f"[v3] failed: {e}", file=sys.stderr)

    # ── Step 5: Build cross-checks (cost + income) — REBUILD income with user rent + correct cap ──
    cost = _build_cost_crosscheck(ev)

    v3_rent = v3_result.get('rent_reference') if v3_result else None
    income = _build_income_crosscheck(
        rental_income=rental_income,
        v3_rent_data=v3_rent,
        asset_type=ev.asset_type,
        primary_value=primary['value'] if primary else None,
    )

    # ── Step 6: Reconciliation ──
    reconciliation = _analyze_reconciliation(primary, cost, income)

    # ── Step 7: Active listings — separate market sentiment ──
    listings_result = None
    if use_listings and _LISTINGS_OK and ev.gis_district_aname:
        try:
            district = ev.gis_district_aname
            min_a = ev.plot_area_m2 * 0.80 if ev.plot_area_m2 else None
            max_a = ev.plot_area_m2 * 1.20 if ev.plot_area_m2 else None
            listings = fetch_active_listings(
                area=district,
                property_type='villa' if ev.asset_type in ('villa', 'standalone_villa') else 'all',
                min_area=min_a, max_area=max_a,
            )
            if listings:
                listings_result = weighted_listings_median(listings)
                listings_result['sample'] = [
                    {'location': l.get('location'), 'area_m2': l.get('area_m2'),
                     'price_m2': round(l.get('price_m2', 0)),
                     'age_days': l.get('age_days'), 'url': l.get('url')}
                    for l in listings[:5]
                ]
        except Exception as e:
            print(f"[listings] failed: {e}", file=sys.stderr)

    # ── Step 8: Build unified output ──
    return _build_unified_output(
        ev=ev,
        primary=primary,
        cost=cost,
        income=income,
        reconciliation=reconciliation,
        v3_result=v3_result,
        geo_v2_result=geo_v2_result,
        listings_result=listings_result,
        geometric=geometric,
        audience=audience,
        user_inputs={
            'listing_price': listing_price,
            'rental_income': rental_income,
            'floors': floors,
            'condition': condition,
            'annexes': annexes,
        },
    )


# ============================================================
# Output builder (backward-compatible + new RICS fields)
# ============================================================

def _build_unified_output(ev, primary, cost, income, reconciliation, v3_result,
                          geo_v2_result, listings_result, geometric, audience, user_inputs) -> Dict:
    output = {
        'status': 'ok',
        'engine_version': 'thammen-sprint2p1-geometric',
        'methodology_ar': 'AVM مبني على Sales Comparison Approach مع توفيق ثلاثي الطرق',
        'methodology_disclaimer_ar': (
            'تقدير آلي (Automated Valuation Model) وفق RICS VPS 4. '
            'لا يحلّ محل التقييم المعتمد من مُقيِّم مُرخّص للأغراض الرسمية '
            '(قروض بنكية، نزاعات قضائية، تقارير محاسبية).'
        ),
        'address': getattr(ev, 'address', None),
        'valuation_date': getattr(ev, 'valuation_date', None),
        'district': getattr(ev, 'gis_district_aname', None),
        'plot_area_m2': getattr(ev, 'plot_area_m2', None),
        'asset_type': getattr(ev, 'asset_type', None),
        'audience': audience,
        'user_inputs': user_inputs,
    }

    # ── Primary valuation (from comparison approach only) ──
    if primary:
        output['valuation'] = {
            'amount':       _r100k(primary['value']),
            'low':          _r100k(primary.get('low')),
            'high':         _r100k(primary.get('high')),
            'method':       primary['method'],
            'method_label_ar': primary['method_label_ar'],
            'source_ar':    primary['source_ar'],
            'n_transactions': primary['n'],
        }
    else:
        output['valuation'] = {
            'amount': None,
            'method': 'insufficient_data',
            'method_label_ar': 'بيانات غير كافية للتقييم',
            'source_ar': 'لم نجد عينة كافية من معاملات المقارنة',
        }

    # ── Frontend compatibility: keep moj_sample_size field ──
    output['moj_sample_size'] = primary['n'] if primary else 0

    # ── Cross-checks (explicitly labeled as such, NOT in valuation) ──
    if cost:
        output['cost_approach'] = {
            'total_replacement_value': cost['value'],
            'land_value': cost.get('land_value'),
            'building_value_new': cost.get('building_value_new'),
            'building_value_depreciated': cost.get('building_value_depreciated'),
            'building_age_years': cost.get('building_age_years'),
            'depreciation_rate_pct': cost.get('depreciation_rate_pct'),
            'bua_m2': cost.get('bua_m2'),
            'tier': cost.get('tier'),
            'method_label_ar': cost['method_label_ar'],
            'role_ar': cost['role_ar'],
        }
    if income:
        output['income_approach'] = {
            'income_value': income['value'],
            'annual_rent': income['annual_rent'],
            'monthly_rent': income['monthly_rent'],
            'rent_source': income['rent_source'],
            'rent_source_ar': income['rent_source_ar'],
            'noi': income['noi'],
            'cap_rate': income['cap_rate'],
            'cap_rate_label_ar': income['cap_rate_label_ar'],
            'gross_yield': income['gross_yield'],
            'net_yield': income['net_yield'],
            'yield_flag_ar': income['yield_flag_ar'],
            'caveats': income.get('caveats', []),
            'method_label_ar': income['method_label_ar'],
            'role_ar': income['role_ar'],
        }

    # ── Reconciliation statement (RICS Red Book) ──
    output['reconciliation'] = reconciliation

    # ── Accuracy (driven by data quality) ──
    n = output.get('moj_sample_size', 0) or 0
    if primary and primary['method'] == 'comparison_bracket' and n >= 20:
        output['accuracy'] = {'score': 85, 'label': 'ثقة عالية 🟢'}
    elif primary and primary['method'] in ('comparison_bracket', 'comparison_widened') and n >= 20:
        output['accuracy'] = {'score': 78, 'label': 'ثقة عالية 🟢'}
    elif primary and n >= 10:
        output['accuracy'] = {'score': 60, 'label': 'ثقة متوسطة 🟡'}
    elif primary:
        output['accuracy'] = {'score': 35, 'label': 'ثقة محدودة 🟠'}
    else:
        output['accuracy'] = {'score': 0, 'label': 'بيانات غير كافية ❌'}

    # ── Trend (only if sample sizes support it — RICS data quality standard) ──
    if getattr(ev, 'trend', None):
        slope_pct = (ev.trend.get('slope_annual_pct') or 0) * 100
        years = ev.trend.get('years', [])
        # Sprint 1.c fix: hide trend if any year has n<5 or total n<10
        # Statistical floor — fewer than this can't support a trend line
        annual_ns = [y.get('n', 0) for y in years]
        total_n = sum(annual_ns)
        min_year_n = min(annual_ns) if annual_ns else 0
        trend_supportable = (
            len(years) >= 2
            and min_year_n >= 5      # each year has enough samples
            and total_n >= 10        # total observations meaningful
        )
        if trend_supportable:
            output['trend'] = {
                'label': ev.trend.get('label'),
                'slope_pct': slope_pct,
                'years': years,
            }
            if abs(slope_pct) > 8:
                output['trend']['warning'] = (
                    f'⚠️ اتجاه استثنائي ({slope_pct:+.1f}%/سنة) — '
                    f'لا يُستخدم للاستقراء. النمو المستدام في قطر 2-4%/سنة.'
                )
        else:
            # Show "volatile / undeterminable" indicator instead of a misleading line
            output['trend'] = {
                'label': 'غير محدد',
                'reason_ar': (
                    f'العينة السنوية صغيرة جداً لاستخراج اتجاه موثوق '
                    f'(أصغر عينة سنوية: {min_year_n}، الإجمالي: {total_n}). '
                    f'السوق في هذه المنطقة قد يكون متذبذباً.'
                ),
                'years_observed': len(years),
                'min_year_n': min_year_n,
                'total_n': total_n,
                'undeterminable': True,
            }

    # ── Location features ──
    LABEL_FIXES = {
        'تزوير R1': 'منطقة سكنية خاصة (R1)',
        'تزوير R2': 'منطقة سكنية (R2)',
        'تزوير R3': 'منطقة سكنية مكثفة (R3)',
        'تزوير C':  'منطقة تجارية (C)',
        'تنظيم R1': 'منطقة سكنية خاصة (R1)',
        'تنظيم R2': 'منطقة سكنية (R2)',
        'تنظيم R3': 'منطقة سكنية مكثفة (R3)',
        'تنظيم C':  'منطقة تجارية (C)',
    }
    HEIGHT_FIXES = {
        'G+1+P': 'أرضي + أول + سطح',
        'G+2+P': 'أرضي + طابقين + سطح',
        'G+P':   'أرضي + سطح',
        'G+1':   'أرضي + أول',
        'G+2':   'أرضي + طابقين',
    }
    output['location_features'] = []
    if ev.valuation and ev.valuation.factors_detail:
        for f in ev.valuation.factors_detail:
            label = f.get('label_ar', '')
            for old, new in LABEL_FIXES.items():
                label = label.replace(old, new)
            for old, new in HEIGHT_FIXES.items():
                if old in label:
                    label = label.replace(old, new)
            code = f.get('code', '')
            direction = f.get('direction', 'neutral')
            is_positive = direction == 'positive'
            if code == 'plot_shape':
                if 'منتظم' in label and 'غير' not in label:
                    is_positive = True
                elif 'غير منتظم' in label:
                    is_positive = False
            output['location_features'].append({'label': label, 'positive': is_positive})

    # ── NEW Sprint 2: Geometric findings (corner, HBU, named landmarks) ──
    # Disclosure-only by default — these may already be captured in comparables.
    # HBU is the exception: it's typically NOT in comparables (R1 surrounded by R1).
    if geometric:
        geo_section = {
            'polygon_available': geometric.get('polygon_available', False),
            'plot_area_m2_verified': geometric.get('plot_area_m2'),
            'pd_no': geometric.get('pd_no'),
        }

        # Corner & main road frontage (disclosure)
        corner = geometric.get('corner', {})
        if corner.get('confidence') != 'low':
            geo_section['corner_analysis'] = {
                'is_corner': corner.get('is_corner', False),
                'main_road_adjacent': corner.get('main_road_adjacent', False),
                'main_streets': corner.get('main_streets', []),
                'local_streets': corner.get('local_streets', []),
                'evidence_ar': corner.get('evidence_ar'),
                'confidence': corner.get('confidence'),
                'note_ar': (
                    'هذه الخصائص قد تَفرض علاوة سوقية. النقطة المركزية '
                    'محافظة (وسيط المقارنات) — الحد الأعلى للنطاق يَعكس الاحتمال.'
                ),
            }

        # HBU
        hbu = geometric.get('hbu', {})
        if hbu.get('hbu_potential') or hbu.get('industrial_adjacency'):
            geo_section['hbu_analysis'] = {
                'potential': hbu.get('hbu_potential', False),
                'industrial_adjacency': hbu.get('industrial_adjacency', False),
                'potential_pct': hbu.get('potential_pct', 0),
                'evidence_ar': hbu.get('evidence_ar'),
                'adjacent_zones': hbu.get('adjacent_zones', []),
                'rics_reference': 'RICS VPS 4 §3.4 — Highest and Best Use',
            }

        # Named landmarks
        nl = geometric.get('named_landmarks', {})
        if nl.get('malls') or nl.get('metros'):
            geo_section['named_landmarks'] = {
                'malls': nl.get('malls', []),
                'metros': nl.get('metros', []),
                'closest_mall_m': nl.get('closest_mall_m'),
                'closest_metro_m': nl.get('closest_metro_m'),
                'walkable_mall': any(m.get('walkable') for m in nl.get('malls', [])),
                'walkable_metro': any(m.get('walkable') for m in nl.get('metros', [])),
            }

        if geo_section.get('polygon_available'):
            output['geometric_factors'] = geo_section

        # ── Range expansion based on geometric features (RICS Range Reporting) ──
        upper_expansion_pct = 0.0
        upper_expansion_reasons = []

        if corner.get('is_corner'):
            upper_expansion_pct += 0.10
            upper_expansion_reasons.append('زاوية (+10%)')
        if corner.get('main_road_adjacent'):
            upper_expansion_pct += 0.08
            upper_expansion_reasons.append('شارع رئيسي (+8%)')
        # Check walkable mall (within 500m)
        walking_mall = next((m for m in nl.get('malls', []) if m.get('walkable')), None)
        if walking_mall:
            upper_expansion_pct += 0.10
            upper_expansion_reasons.append(f'{walking_mall["name_ar"]} يُمشى (+10%)')
        # Check walkable metro
        walking_metro = next((m for m in nl.get('metros', []) if m.get('walkable')), None)
        if walking_metro:
            upper_expansion_pct += 0.08
            upper_expansion_reasons.append('مترو يُمشى (+8%)')

        upper_expansion_pct = min(upper_expansion_pct, 0.35)

        hbu_central_uplift_pct = 0.0
        if hbu.get('hbu_potential'):
            hbu_central_uplift_pct = hbu.get('potential_pct', 0) * 0.5
        elif hbu.get('industrial_adjacency'):
            hbu_central_uplift_pct = hbu.get('potential_pct', 0)

        if output.get('valuation') and output['valuation'].get('amount'):
            base_amount = output['valuation']['amount']
            base_low = output['valuation'].get('low') or base_amount * 0.85
            base_high = output['valuation'].get('high') or base_amount * 1.15

            new_amount = base_amount * (1 + hbu_central_uplift_pct)
            new_high = max(base_high, base_amount * (1 + upper_expansion_pct)) * (1 + hbu_central_uplift_pct)
            new_low = base_low * (1 + min(0, hbu_central_uplift_pct))

            output['valuation']['amount'] = _r100k(new_amount)
            output['valuation']['low'] = _r100k(new_low)
            output['valuation']['high'] = _r100k(new_high)

            output['valuation']['range_expansion'] = {
                'upper_bound_expanded_pct': round(upper_expansion_pct * 100, 1),
                'central_value_hbu_adjustment_pct': round(hbu_central_uplift_pct * 100, 1),
                'reasons_for_upper_expansion': upper_expansion_reasons,
                'methodology_note_ar': (
                    'النقطة المركزية تَستخدم وسيط المقارنات (محافظ). الحد الأعلى '
                    'يَتسع لِيَعكس الخصائص الفريدة المُكتشَفة. '
                    'HBU (إن وُجد) يُؤثر على النقطة المركزية لأنه قيمة-إضافية '
                    'غير مُتضمَّنة في عقارات المقارنة.'
                ),
            }

    # ── Material Uncertainty (RICS VPN 13) ──
    # Sprint 1.c fix: ensure MU reflects the n actually USED in primary value
    # (not the thin bracket n that geo widening already bypassed)
    if v3_result and v3_result.get('material_uncertainty'):
        mu = dict(v3_result['material_uncertainty'])  # shallow copy
        effective_n = primary['n'] if primary else 0
        # Replace any "n=1" or "n=X (thin bracket)" misleading factors with the truth
        if mu.get('factors'):
            new_factors = []
            for f in mu['factors']:
                # The factor that says "n=1 — لا يمكن إنتاج وسيط موثوق" is misleading
                # when we actually used n=42 from widening
                if 'صغيرة جداً' in f and 'لا يمكن إنتاج' in f and effective_n >= 20:
                    new_factors.append(
                        f'الشريحة المباشرة ضعيفة (n=1) — تم التعويض بالتوسيع الجغرافي '
                        f'(n={effective_n} معاملة بعد التوسيع، RICS VPS 4 §7)'
                    )
                else:
                    new_factors.append(f)
            mu['factors'] = new_factors

        # Recompute level based on effective n
        if effective_n >= 20 and primary and primary['method'] in ('comparison_bracket', 'comparison_widened'):
            # Strong primary evidence reduces MU from "high" to "moderate"
            if mu.get('level') == 'high':
                mu['level'] = 'moderate'
                mu['banner_ar'] = (
                    '⚠️ تحفّظ مادي متوسط — عينة المقارنات معقولة (n=' + str(effective_n)
                    + ') لكن لا يوجد فحص ميداني أو بيانات بناء كاملة. '
                    + 'يبقى الفحص الميداني موصى به للقرارات الكبرى.'
                )
                mu['banner_en'] = (
                    '⚠️ MODERATE Material Uncertainty — Reasonable comparable sample '
                    '(n=' + str(effective_n) + ') but no field inspection or full building data. '
                    'Field inspection recommended for major decisions.'
                )
        output['material_uncertainty'] = mu

    # ── Audience-specific brief ──
    if v3_result and v3_result.get('brief'):
        brief = dict(v3_result['brief'])
        # Sprint 1.c fix: filter out duplicate income/yield sections that use stale v3 cap_rate (6.5%)
        # contradicting the corrected primary income_approach (4% for residential).
        # These sections will be regenerated cleanly in Sprint 1.d with consistent data.
        STALE_SECTION_IDS = {'yield', 'income_value', 'sensitivity', 'rent_reference'}
        if brief.get('sections'):
            brief['sections'] = [
                s for s in brief['sections']
                if s.get('id') not in STALE_SECTION_IDS
            ]
            # If we removed all sections, add a placeholder pointer to the main income_approach
            if not brief['sections']:
                brief['sections'] = [{
                    'id': 'income_pointer',
                    'title_ar': 'تحليل الدخل والعائد',
                    'content': {
                        'note_ar': (
                            'انظر قسم "طريقة الدخل" أعلاه — يحوي القيمة الصحيحة، '
                            'مصدر الإيجار، Cap Rate المناسب لنوع الأصل، وصافي العائد.'
                        ),
                    },
                }]
        # Also fix the brief's top-level valuation_total to match the primary value (was using v3 blend)
        if primary and primary.get('value'):
            brief['valuation_total'] = _r100k(primary['value'])
            brief['valuation_low'] = _r100k(primary.get('low'))
            brief['valuation_high'] = _r100k(primary.get('high'))
        output['brief'] = brief

    # ── Disclaimer ──
    output['disclaimer'] = getattr(ev, 'disclaimer', None)
    output['valuation_id'] = getattr(ev, 'valuation_id', None)

    if getattr(ev, 'reasoning_trace', None):
        output['reasoning_trace'] = ev.reasoning_trace

    # ── Listings as separate sentiment context (RICS GN 13) ──
    if listings_result:
        output['active_listings'] = {
            'note': 'إعلانات نشطة — سياق سوقي، ليست في معادلة التقييم (RICS GN 13)',
            'n': listings_result.get('n'),
            'weighted_median_m2': listings_result.get('weighted_median_m2'),
            'oldest_days': listings_result.get('oldest_days'),
            'sample': listings_result.get('sample', []),
        }
    elif _LISTINGS_OK:
        output['active_listings'] = {'available': False,
                                      'reason': 'لا توجد إعلانات نشطة مطابقة'}

    return output


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('zone', type=int)
    p.add_argument('street', type=int)
    p.add_argument('building', type=int)
    p.add_argument('--moj', default='moj_weekly.csv')
    p.add_argument('--rent', default='rent_reference.json')
    p.add_argument('--asking', type=float)
    p.add_argument('--rental', type=float)
    p.add_argument('--floors', type=int)
    p.add_argument('--condition', choices=['new', 'good', 'renovated', 'maintenance',
                                           'excellent', 'fair', 'poor'])
    p.add_argument('--annexes', type=int, default=0)
    p.add_argument('--audience', choices=['buyer', 'seller', 'investor', 'valuer'],
                   default='buyer')
    p.add_argument('--no-listings', action='store_true')
    p.add_argument('--no-geo-v2', action='store_true')
    args = p.parse_args()

    result = evaluate_thammen(
        zone=args.zone, street=args.street, building=args.building,
        moj_csv_path=args.moj,
        rent_ref_path=args.rent,
        listing_price=args.asking,
        rental_income=args.rental,
        floors=args.floors,
        condition=args.condition,
        annexes=args.annexes,
        audience=args.audience,
        use_listings=not args.no_listings,
        use_geo_v2=not args.no_geo_v2,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
