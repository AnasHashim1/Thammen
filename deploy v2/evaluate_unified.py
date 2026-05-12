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
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
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
# Sprint A.3: v1 scope and sanity check thresholds
# ============================================================

# v1 supports: villas, lands, palaces, small compounds + DCF fallback for large income assets.
# Politely refuses: commercial / industrial / agricultural (no usable data in MoJ).
V1_IN_SCOPE_FULL = {
    'standalone_villa', 'villa', 'raw_land', 'land',
    'palace', 'compound_small',
}
V1_IN_SCOPE_DCF_ONLY = {
    'compound_large', 'tower', 'apartment_building',
}
V1_OUT_OF_SCOPE = {
    'commercial', 'industrial', 'agricultural',
}

# Yield sanity ranges (RICS-aligned Qatar empirical norms)
# Below 3% net = property way overpriced relative to its rent
# Above 10% net = either underpriced, distressed, or rent is wrong
YIELD_NORMAL_MIN = 0.03   # 3%
YIELD_NORMAL_MAX = 0.10   # 10%
YIELD_FLAG_MIN   = 0.02   # < 2% → "very weak"
YIELD_FLAG_MAX   = 0.12   # > 12% → "implausible, check rent"

# Listing price vs reference gap thresholds (% above/below)
LISTING_GAP_OVERPRICED_WARN = 0.30   # +30% = market ceiling
LISTING_GAP_UNDERPRICED_WARN = -0.30 # -30% = check for issues

# Asset type → MoJ "نوع العقار" categories for sample availability check
# (some categories appear with NBSP \xa0 vs regular space — handled by normalize)
ASSET_TO_MOJ_CATEGORIES = {
    'standalone_villa':  ('فيلا', 'فيلا من طابقين وملحق', 'فيلتان متلاصقتان', 'فيلا واحدة'),
    'villa':             ('فيلا', 'فيلا من طابقين وملحق', 'فيلتان متلاصقتان', 'فيلا واحدة'),
    'raw_land':          ('أرض فضاء', 'ارض فضاء'),
    'land':              ('أرض فضاء', 'ارض فضاء'),
    'palace':            ('قصر',),
    'compound_small':    ('مجمع فلل', 'مجمع فلل وملحقاتها'),
}
MIN_MOJ_SAMPLES_FOR_FULL_PIPELINE = 1  # below this → use fast paths instead
# (only blocks when ZERO direct comparables exist — full pipeline can still
# widen the search to find indirect samples for n>=1 cases)


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


def _count_moj_comparables(csv_path: str, district_ar: Optional[str],
                           asset_type: str) -> int:
    """Sprint A.3+: Fast count of MoJ comparables for this asset+district.

    Used before launching the full pipeline (19+ seconds) to detect cases
    where the pipeline would just produce insufficient_data anyway. If this
    returns 0 or very few samples, route to fast paths instead.

    Returns: count of MoJ transactions matching this asset class in this district.
    """
    import re
    categories = ASSET_TO_MOJ_CATEGORIES.get(asset_type)
    if not categories or not district_ar:
        return 999  # unknown asset or district → don't block full pipeline
    try:
        rows = _get_moj_rows(csv_path)
    except Exception:
        return 999  # CSV missing → defensive, let full pipeline handle it

    def norm(s):
        return re.sub(r'\s+', ' ', s or '').strip()

    district_norm = norm(district_ar)
    cat_set = {norm(c) for c in categories}
    # Match by district + asset category. Match district prefix (e.g., 'الدفنة 61'
    # should match 'الدفنة' rows). Use prefix or exact match.
    count = 0
    for r in rows:
        d = norm(r.get('اسم المنطقة', ''))
        if d != district_norm and not (d.startswith(district_norm + ' ')
                                       or district_norm.startswith(d + ' ')):
            continue
        nt = norm(r.get('نوع العقار', ''))
        if nt in cat_set:
            count += 1
    return count


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

    # Note: signal.SIGALRM was used here but breaks in worker threads.
    # Timeout is now enforced by the outer ThreadPoolExecutor in evaluate_thammen.
    try:
        rows = _get_moj_rows(moj_csv_path)
        return build_reference_geo_v2(
            rows=rows, lat=lat, lon=lon,
            category=cat,
            plot_area_m2=ev.plot_area_m2,
            target_zoning=None,
        )
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

def _build_investor_sections(income, v3_rent, primary):
    """Build the 4 investor-specific brief sections from corrected income data.

    Sources used (all consistent with the primary valuation):
      - `income`: corrected income cross-check (cap_rate matches asset type)
      - `v3_rent`: rent reference (n, monthly_median, confidence) — if available
      - `primary`: comparison-led valuation (used for sensitivity baseline)
    """
    sections = []

    # ── Section 1: تحليل العائد ──
    sections.append({
        'id': 'yield',
        'title_ar': 'تحليل العائد',
        'content': {
            'gross_yield_pct': round((income.get('gross_yield') or 0) * 100, 2),
            'net_yield_pct': round((income.get('net_yield') or 0) * 100, 2),
            'noi_annual': income.get('noi'),
            'annual_rent_gross': income.get('annual_rent'),
            'cap_rate_pct': round((income.get('cap_rate') or 0) * 100, 2),
            'cap_rate_label_ar': income.get('cap_rate_label_ar'),
            'rent_source_ar': income.get('rent_source_ar'),
        },
    })

    # ── Section 2: القيمة بمنهج الدخل ──
    sections.append({
        'id': 'income_value',
        'title_ar': 'القيمة بمنهج الدخل',
        'content': {
            # income.value is what _build_income_crosscheck stores (line 358);
            # income_value is the same field name used in api.py output
            'income_value': income.get('value') or income.get('income_value'),
            'cap_rate_used': income.get('cap_rate'),
            'noi': income.get('noi'),
            'role_ar': income.get('role_ar'),
            'method_label_ar': income.get('method_label_ar'),
        },
    })

    # ── Section 3: تحليل الحساسية ──
    # Cap rate ±0.5%, ±1% sensitivity on the income value
    noi = income.get('noi') or 0
    base_cap = income.get('cap_rate') or 0
    if noi > 0 and base_cap > 0:
        sensitivity = []
        for delta_pct in (-1.0, -0.5, 0, 0.5, 1.0):
            cap = base_cap + (delta_pct / 100.0)
            if cap > 0:
                sensitivity.append({
                    'cap_rate_pct': round(cap * 100, 2),
                    'income_value': round(noi / cap, -3),
                    'delta_label_ar': (
                        'الأساس' if delta_pct == 0
                        else f'{"+" if delta_pct > 0 else ""}{delta_pct}%'
                    ),
                })
        sections.append({
            'id': 'sensitivity',
            'title_ar': 'تحليل الحساسية — Cap Rate',
            'content': {
                'base_cap_rate_pct': round(base_cap * 100, 2),
                'base_noi': noi,
                'scenarios': sensitivity,
                'note_ar': 'حساسية القيمة لتغير Cap Rate ±1% — لأن المعدل يبقى تقديرياً.',
            },
        })

    # ── Section 4: مرجع الإيجار ──
    if v3_rent:
        sections.append({
            'id': 'rent_reference',
            'title_ar': 'مرجع الإيجار',
            'content': {
                'monthly_median': v3_rent.get('monthly_median'),
                'annual_low': v3_rent.get('annual_low'),
                'annual_high': v3_rent.get('annual_high'),
                'n': v3_rent.get('n'),
                'confidence': v3_rent.get('confidence'),
                'source_ar': v3_rent.get('source_ar', 'qrep.aqarat.gov.qa'),
                'caveats_ar': v3_rent.get('caveats', []),
            },
        })

    return sections


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
# Sprint A.1: Fast short-circuit for DCF-only assets
# ============================================================

ASSET_TYPE_AR = {
    'standalone_villa':   'فيلا منفردة',
    'compound_small':     'مجمع فلل صغير',
    'compound_large':     'مجمع فلل كبير',
    'apartment_building': 'عمارة سكنية',
    'tower':              'برج سكني',
    'palace':             'قصر',
    'raw_land':           'أرض فضاء',
    'commercial':         'تجاري',
    'industrial':         'صناعي',
    'agricultural':       'مزرعة',
    'unknown':            'غير محدد',
}


def _build_fast_insufficient_data_response(zone, street, building, loc, plot, asset_type, audience):
    """Fast response for DCF-only assets when user provided no inputs.

    The full pipeline would take 30-90s on these (compound extent detection,
    GIS factor analysis, v3 enrichment) but always produces insufficient_data
    because there's no MoJ comparable for the asset class. Returns the
    classification facts in ~1s so the user can resubmit with rental_income
    or listing_price.
    """
    from datetime import datetime
    asset_label_ar = ASSET_TYPE_AR.get(asset_type, asset_type)
    return {
        'status': 'ok',
        'engine_version': 'thammen-sprint-a1-fast-classify',
        'methodology_ar': (
            'تصنيف سريع مبني على بيانات GIS — لا توجد مقارنة MoJ '
            f'مباشرة لفئة "{asset_label_ar}" في قطر'
        ),
        'methodology_disclaimer_ar': (
            'تقدير الأصول من هذه الفئة يحتاج طريقة الدخل (Income Approach) أو سعر '
            'إعلان قابل للمقارنة. يرجى إعادة الطلب مع إفادة بالإيجار الشهري أو سعر '
            'الإعلان للحصول على تقييم كامل.'
        ),
        'address': f'{zone}/{street}/{building}',
        'valuation_date': datetime.now().strftime('%Y-%m-%d'),
        'district': None,
        'plot_area_m2': plot.pdarea,
        'gps': {'lat': loc.lat, 'lon': loc.lon} if loc else None,
        'asset_type': asset_type,
        'asset_type_ar': asset_label_ar,
        'audience': audience,
        'user_inputs': {
            'listing_price': None,
            'rental_income': None,
        },
        'valuation': {
            'amount': None,
            'low': None,
            'high': None,
            'method': 'insufficient_data',
            'reason_ar': (
                f'هذا الأصل من نوع "{asset_label_ar}" — لا توجد عينة مقارنة في سجلات '
                'وزارة العدل لهذه الفئة (الكومباوندات الكبيرة والأبراج تُسجَّل بأرقام '
                'مرجعية موحَّدة بدلاً من مقارنات سعر/م²). '
                'لتقييم دقيق، أضف الإيجار الشهري الفعلي أو سعر الإعلان وأعد الطلب.'
            ),
        },
        'moj_sample_size': 0,
        'cost_approach': None,
        'income_approach': None,
        'reconciliation': {
            'status': 'no_primary',
            'message_ar': 'تصنيف فقط — التقييم يحتاج إفادة الإيجار أو سعر الإعلان',
        },
        'accuracy': {
            'score': 0,
            'label': '⚠️ بيانات غير كافية',
        },
        'trend': None,
        'location_features': None,
        'geometric_factors': None,
        'material_uncertainty': {
            'level': 'critical',
            'banner_ar': 'تحفظ مادي حرج: لا توجد بيانات بيع مقارنة لهذه الفئة',
            'known_unknowns_ar': [
                'الإيجار الشهري للوحدات',
                'حالة المبنى والعمر',
                'مساحة البناء الإجمالية',
                'عدد الوحدات الفعلي',
            ],
            'rics_compliant': False,
        },
        'brief': {
            'audience': audience,
            'title_ar': f'تقرير {asset_label_ar} — تحتاج بيانات إضافية',
            'sections': [{
                'id': 'next_steps',
                'title_ar': 'الخطوات المقترحة',
                'content': {
                    'note_ar': (
                        f'العنوان {zone}/{street}/{building} تابع لمساحة {plot.pdarea:,.0f} م² '
                        f'مُصنَّف كـ "{asset_label_ar}". لتقييم كامل يرجى تزويدنا بأحد التاليين:'
                    ),
                    'options_ar': [
                        'إفادة الإيجار الشهري الفعلي (لتقييم بطريقة الدخل)',
                        'سعر الإعلان أو سعر المالك (لمقارنة سوقية)',
                    ],
                },
            }],
        },
        'disclaimer': (
            'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. '
            'هذا تحليل معلوماتي، وليس تقييماً معتمداً وفق RICS/IVS.'
        ),
        'active_listings': {
            'available': False,
            'reason': 'تصنيف سريع — لم يُجرَ بحث إعلانات',
        },
    }


def _build_fast_listing_only_response(zone, street, building, loc, plot, asset_type,
                                       audience, listing_price):
    """Sprint A.3 fix: Fast response for DCF asset with listing_price but no rental.

    The full pipeline would burn 30-40s on GIS extent detection that produces no
    usable comparison (no MoJ comparable for compound_large/tower/etc.). Instead,
    we reverse-engineer: at typical Cap Rate, what rent would this listing price
    require? Returns in ~1s with an actionable question for the user.
    """
    from datetime import datetime
    asset_label_ar = ASSET_TYPE_AR.get(asset_type, asset_type)

    # Reverse-engineer implied rent from listing price
    cap_rate = CAP_RATES_BY_ASSET.get(asset_type) or 0.075
    opex_ratio = OPEX_RATIO_RESIDENTIAL
    implied_annual_noi = listing_price * cap_rate
    implied_annual_rent = implied_annual_noi / (1 - opex_ratio)
    implied_monthly_rent = implied_annual_rent / 12

    # Sanity context: implied rent per m² of plot
    rent_per_m2_year = implied_annual_rent / plot.pdarea if plot.pdarea else 0

    plausibility_ar = (
        'في النطاق المعقول' if 60 <= rent_per_m2_year <= 400
        else 'مرتفع — السعر قد يكون مبالغاً فيه' if rent_per_m2_year > 400
        else 'منخفض — السعر قد يكون رخيصاً'
    )

    return {
        'status': 'ok',
        'engine_version': 'thammen-sprint-a3-implied-rent',
        'methodology_ar': (
            f'تحليل سعر الإعلان لـ "{asset_label_ar}" — تقدير الإيجار الضمني المطلوب '
            'لجعل السعر منطقياً وفق Cap Rate نموذجي.'
        ),
        'methodology_disclaimer_ar': (
            'هذا ليس تقييماً نهائياً، بل أداة فحص: نحسب الإيجار الذي يجب أن يُنتجه '
            'العقار لتبرير السعر المطلوب. إذا كان الإيجار الفعلي أقل بكثير من '
            'المُقدَّر، السعر مرتفع. للتقييم الكامل، أعد الطلب مع الإيجار الشهري الفعلي.'
        ),
        'address': f'{zone}/{street}/{building}',
        'valuation_date': datetime.now().strftime('%Y-%m-%d'),
        'district': None,
        'plot_area_m2': plot.pdarea,
        'gps': {'lat': loc.lat, 'lon': loc.lon} if loc else None,
        'asset_type': asset_type,
        'asset_type_ar': asset_label_ar,
        'audience': audience,
        'user_inputs': {
            'listing_price': listing_price,
            'rental_income': None,
        },
        'valuation': {
            'amount': None,
            'low': None,
            'high': None,
            'method': 'listing_only_implied_rent',
            'reason_ar': (
                f'لا توجد مقارنة MoJ مباشرة لـ "{asset_label_ar}". '
                f'بدلاً من تقييم بدون مرجع، نحسب الإيجار الضمني: '
                f'لتبرير سعر {listing_price:,.0f} ر.ق، يجب أن يُنتج هذا العقار '
                f'~{implied_monthly_rent:,.0f} ر.ق شهرياً. '
                'قارن هذا بالإيجار الفعلي للحكم على معقولية السعر.'
            ),
        },
        'moj_sample_size': 0,
        'cost_approach': None,
        'income_approach': None,
        'reconciliation': {
            'status': 'implied_rent_check',
            'message_ar': 'فحص ضمني — أعد الطلب مع الإيجار الفعلي للتقييم الكامل',
        },
        'accuracy': {
            'score': 30,
            'label': '⚠️ فحص ضمني فقط',
        },
        'trend': None,
        'location_features': None,
        'geometric_factors': None,
        'material_uncertainty': {
            'level': 'high',
            'banner_ar': 'لا يوجد تقييم حقيقي — فقط فحص ضمني للسعر المطلوب',
            'known_unknowns_ar': [
                'الإيجار الشهري الفعلي للعقار',
                'مستوى الإشغال الحقيقي',
                'حالة المبنى والصيانة',
            ],
            'rics_compliant': False,
        },
        'brief': {
            'audience': audience,
            'title_ar': f'فحص ضمني — {asset_label_ar}',
            'sections': [
                {
                    'id': 'implied_rent',
                    'title_ar': 'الإيجار الضمني المطلوب',
                    'content': {
                        'listing_price': listing_price,
                        'implied_monthly_rent': round(implied_monthly_rent),
                        'implied_annual_rent': round(implied_annual_rent),
                        'implied_noi': round(implied_annual_noi),
                        'cap_rate_used_pct': round(cap_rate * 100, 2),
                        'rent_per_m2_year': round(rent_per_m2_year, 1),
                        'plausibility_ar': plausibility_ar,
                        'note_ar': (
                            f'لجعل سعر {listing_price:,.0f} ر.ق منطقياً وفق Cap Rate '
                            f'نموذجي ({cap_rate*100:.1f}% لـ {asset_label_ar})، يجب أن '
                            f'يُنتج هذا العقار إيجاراً شهرياً قدره '
                            f'~{implied_monthly_rent:,.0f} ر.ق.'
                        ),
                    },
                },
                {
                    'id': 'next_steps',
                    'title_ar': 'الخطوات المقترحة',
                    'content': {
                        'note_ar': 'لتقييم نهائي وموثوق:',
                        'options_ar': [
                            f'أكّد أو انفِ: هل الإيجار الفعلي قريب من {implied_monthly_rent:,.0f} ر.ق/شهر؟',
                            'إذا كان الإيجار الفعلي أقل بكثير → السعر مرتفع',
                            'إذا كان الإيجار الفعلي أعلى أو مساوياً → السعر منطقي',
                            'أعد الطلب مع الإيجار الشهري للتقييم الكامل',
                        ],
                    },
                },
            ],
        },
        'sanity_warnings': [],
        'disclaimer': (
            'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. '
            'هذا تحليل معلوماتي، وليس تقييماً معتمداً وفق RICS/IVS.'
        ),
        'active_listings': {
            'available': False,
            'reason': 'فحص ضمني — لم يُجرَ بحث إعلانات',
        },
    }


def _build_fast_income_only_response(zone, street, building, loc, plot, asset_type,
                                      audience, rental_income, listing_price):
    """Sprint A.2: Fast income-only valuation for DCF-only assets.

    For compound_large / tower / commercial / apartment_building with rental_income,
    the full pipeline takes 30-90s producing comparison data that has no MoJ
    comparable anyway. The Income Approach is the ONLY valid method for these
    assets, and it needs just 4 inputs: rental, OPEX ratio, cap rate, asset size.
    All available in ~1s without GIS extent detection or geometric factors.

    The valuation produced is RICS-compliant Income Approach output. Comparison
    and Cost approaches are explicitly absent (correctly).
    """
    from datetime import datetime
    asset_label_ar = ASSET_TYPE_AR.get(asset_type, asset_type)

    # ── Income Approach computation ──
    annual_rent = (rental_income or 0) * 12
    opex_ratio = OPEX_RATIO_RESIDENTIAL
    noi = annual_rent * (1 - opex_ratio)
    cap_rate = CAP_RATES_BY_ASSET.get(asset_type) or 0.075
    income_value = round(noi / cap_rate) if cap_rate > 0 else None
    gross_yield = (annual_rent / income_value) if income_value else None
    net_yield = (noi / income_value) if income_value else None

    # Range: ±15% reflecting Cap Rate uncertainty
    value_low = round(income_value * 0.85, -4) if income_value else None
    value_high = round(income_value * 1.15, -4) if income_value else None

    # ── Listing comparison if provided ──
    listing_gap_pct = None
    if listing_price and income_value:
        listing_gap_pct = (listing_price - income_value) / income_value

    # ── Sensitivity scenarios ──
    sensitivity = []
    for delta in (-1.0, -0.5, 0, 0.5, 1.0):
        c = cap_rate + (delta / 100.0)
        if c > 0:
            sensitivity.append({
                'cap_rate_pct': round(c * 100, 2),
                'income_value': round(noi / c, -3),
                'delta_label_ar': 'الأساس' if delta == 0 else ('+' if delta > 0 else '') + f'{delta}%',
            })

    # ── Investor brief sections (rebuilt locally) ──
    sections = [
        {
            'id': 'yield',
            'title_ar': 'تحليل العائد',
            'content': {
                'gross_yield_pct': round((gross_yield or 0) * 100, 2),
                'net_yield_pct': round((net_yield or 0) * 100, 2),
                'noi_annual': noi,
                'annual_rent_gross': annual_rent,
                'cap_rate_pct': round(cap_rate * 100, 2),
                'cap_rate_label_ar': f'معدل رسملة {cap_rate*100:.1f}% (نموذجي لـ {asset_label_ar})',
                'rent_source_ar': 'إفادة العميل (الإيجار الفعلي)',
            },
        },
        {
            'id': 'income_value',
            'title_ar': 'القيمة بمنهج الدخل',
            'content': {
                'income_value': income_value,
                'cap_rate_used': cap_rate,
                'noi': noi,
                'role_ar': (
                    f'القيمة الأساسية المعتمدة لـ "{asset_label_ar}" (طريقة الدخل '
                    'هي الطريقة الأنسب لهذه الفئة وفق RICS Income Approach)'
                ),
                'method_label_ar': 'طريقة الدخل (RICS Income Approach)',
            },
        },
        {
            'id': 'sensitivity',
            'title_ar': 'تحليل الحساسية — Cap Rate',
            'content': {
                'base_cap_rate_pct': round(cap_rate * 100, 2),
                'base_noi': noi,
                'scenarios': sensitivity,
                'note_ar': 'حساسية القيمة لتغير Cap Rate ±1% — لأن المعدل تقديري ويتأثر بحالة السوق.',
            },
        },
        {
            'id': 'market_context',
            'title_ar': 'السياق السوقي',
            'content': {
                'qatar_benchmark': f'7-8% Cap Rate للكومباوندات الكبيرة في قطر = طبيعي',
                'above_6_net': 'صافي عائد > 6% = جذاب للمستثمرين',
                'below_4_net': 'صافي عائد < 4% = ضعيف، أعد التفاوض',
            },
        },
    ]

    # If listing_price provided, add comparison section
    if listing_price and income_value:
        gap_pct = listing_gap_pct * 100
        position_ar = (
            'أقل من قيمة الدخل' if gap_pct < -5
            else 'أعلى من قيمة الدخل' if gap_pct > 5
            else 'مطابق لقيمة الدخل'
        )
        sections.insert(0, {
            'id': 'verdict',
            'title_ar': 'مقارنة السعر بقيمة الدخل',
            'content': {
                'listing_price': listing_price,
                'benchmark': income_value,
                'gap_pct': listing_gap_pct,
                'position': 'above_market' if gap_pct > 5 else 'below_market' if gap_pct < -5 else 'at_market',
                'description_ar': f'السعر {position_ar} بـ {abs(gap_pct):.1f}%. القيمة محسوبة من الإيجار المُقدَّم بطريقة الدخل.',
            },
        })

    return {
        'status': 'ok',
        'engine_version': 'thammen-sprint-a2-fast-income',
        'methodology_ar': (
            f'تقدير سريع بطريقة الدخل (RICS Income Approach) لـ "{asset_label_ar}". '
            'لا توجد مقارنة MoJ مباشرة لهذه الفئة في قطر — الدخل هو الطريقة المعيارية.'
        ),
        'methodology_disclaimer_ar': (
            'تقدير آلي مبني على الإيجار المُقدَّم من العميل و Cap Rate نموذجي للفئة. '
            'للأغراض الرسمية يلزم تقييم من مُقيِّم معتمد بعد فحص ميداني وتحقق من الإيجار '
            'الفعلي عبر فترة طويلة.'
        ),
        'address': f'{zone}/{street}/{building}',
        'valuation_date': datetime.now().strftime('%Y-%m-%d'),
        'district': None,
        'plot_area_m2': plot.pdarea,
        'gps': {'lat': loc.lat, 'lon': loc.lon} if loc else None,
        'asset_type': asset_type,
        'asset_type_ar': asset_label_ar,
        'audience': audience,
        'user_inputs': {
            'listing_price': listing_price,
            'rental_income': rental_income,
        },
        'valuation': {
            'amount': income_value,
            'low': value_low,
            'high': value_high,
            'method': 'income_approach_only',
            'method_ar': 'طريقة الدخل (الطريقة المعيارية لهذه الفئة)',
        },
        'moj_sample_size': 0,
        'cost_approach': None,
        'income_approach': {
            'income_value': income_value,
            'annual_rent': annual_rent,
            'monthly_rent': rental_income,
            'rent_source_ar': 'إفادة العميل',
            'noi': noi,
            'opex_ratio': opex_ratio,
            'cap_rate': cap_rate,
            'cap_rate_label_ar': f'معدل رسملة {cap_rate*100:.1f}% (نموذجي لـ {asset_label_ar})',
            'gross_yield': gross_yield,
            'net_yield': net_yield,
            'method_label_ar': 'طريقة الدخل (RICS Income Approach)',
            'role_ar': 'القيمة الأساسية المعتمدة',
        },
        'reconciliation': {
            'status': 'income_only',
            'message_ar': (
                f'طريقة واحدة معتمدة: الدخل. للأصول من فئة "{asset_label_ar}" '
                'لا توجد مقارنة MoJ كافية، ومنهج التكلفة لا يعكس قيمة الاستثمار.'
            ),
        },
        'accuracy': {
            'score': 55,
            'label': '⚠️ تقدير بطريقة واحدة',
        },
        'trend': None,
        'location_features': None,
        'geometric_factors': None,
        'material_uncertainty': {
            'level': 'high',
            'banner_ar': (
                'تحفظ مادي مرتفع: التقدير مبني على Cap Rate نموذجي + إيجار مُقدَّم من '
                'العميل. للقرارات الكبيرة، يُنصح بفحص ميداني وتحقق من الإيجار التاريخي.'
            ),
            'known_unknowns_ar': [
                'مدى استقرار الإيجار التاريخي (هل الرقم المُقدَّم ثابت أم متذبذب؟)',
                'تكاليف التشغيل الفعلية (قد تختلف عن 23% النموذجي)',
                'حالة المباني والإنشاءات (تؤثر على Cap Rate الفعلي)',
                'مستوى الإشغال الفعلي',
            ],
            'rics_compliant': False,
        },
        'brief': {
            'audience': audience,
            'title_ar': (
                f'تقرير المستثمر — {asset_label_ar}' if audience == 'investor'
                else f'تقدير {asset_label_ar} بطريقة الدخل'
            ),
            'sections': sections,
        },
        'disclaimer': (
            'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. '
            'هذا تحليل معلوماتي، وليس تقييماً معتمداً وفق RICS/IVS.'
        ),
        'active_listings': {
            'available': False,
            'reason': 'تقدير سريع بطريقة الدخل — لم يُجرَ بحث إعلانات',
        },
    }


def _build_out_of_scope_response(zone, street, building, loc, plot, asset_type, audience):
    """Sprint A.3: Polite rejection for asset types outside v1 scope.

    v1 supports: villas, lands, small compounds, palaces (full pipeline) +
    DCF fallback for large income-producing assets. v1 does NOT support:
    individual apartments, commercial shops, offices, industrial, agricultural.

    The reason: MoJ data and our rent reference don't cover these classes with
    enough density to produce defensible valuations. Better to refuse cleanly
    than to produce confidently-wrong numbers.
    """
    from datetime import datetime
    asset_label_ar = ASSET_TYPE_AR.get(asset_type, asset_type)
    suggestions = {
        'commercial': 'للمحلات التجارية، يُوصى بمُقيِّم متخصص في العقارات التجارية.',
        'industrial': 'للعقارات الصناعية، يُوصى بمُقيِّم متخصص ومسح ميداني للمنطقة الصناعية.',
        'agricultural': 'للمزارع، يلزم تقييم مخصص يشمل الرخصة الزراعية وموارد الماء.',
    }
    return {
        'status': 'ok',
        'engine_version': 'thammen-sprint-a3-scope-filter',
        'methodology_ar': f'الإصدار الأول من ثمّن لا يدعم فئة "{asset_label_ar}"',
        'methodology_disclaimer_ar': (
            'ثمّن في إصداره الأول مُصمَّم خصيصاً للفلل والأراضي والقصور والكومباوندات. '
            'هذه الفئات تملك بيانات MoJ كافية لإنتاج تقييم موثوق. '
            'فئات أخرى (تجاري، صناعي، مزرعة، شقق فردية) تحتاج بيانات ومنهجية مختلفة، '
            'وسيتم دعمها في إصدارات لاحقة.'
        ),
        'address': f'{zone}/{street}/{building}',
        'valuation_date': datetime.now().strftime('%Y-%m-%d'),
        'district': None,
        'plot_area_m2': plot.pdarea if plot else None,
        'gps': {'lat': loc.lat, 'lon': loc.lon} if loc else None,
        'asset_type': asset_type,
        'asset_type_ar': asset_label_ar,
        'audience': audience,
        'user_inputs': {},
        'valuation': {
            'amount': None, 'low': None, 'high': None,
            'method': 'out_of_scope_v1',
            'reason_ar': (
                f'هذا العقار من فئة "{asset_label_ar}" — خارج نطاق ثمّن الإصدار الأول. '
                + suggestions.get(asset_type, 'يُوصى بمُقيِّم متخصص في هذه الفئة.')
            ),
        },
        'moj_sample_size': 0,
        'cost_approach': None,
        'income_approach': None,
        'reconciliation': {
            'status': 'out_of_scope',
            'message_ar': 'فئة العقار خارج نطاق الإصدار الحالي',
        },
        'accuracy': {'score': 0, 'label': '— خارج النطاق'},
        'trend': None, 'location_features': None, 'geometric_factors': None,
        'material_uncertainty': {
            'level': 'critical',
            'banner_ar': 'لا يمكن إنتاج تقييم موثوق لهذه الفئة في الإصدار الحالي',
            'known_unknowns_ar': [
                'بيانات بيع MoJ شحيحة لهذه الفئة',
                'مرجع إيجار غير كافٍ',
                'منهجية متخصصة مطلوبة',
            ],
            'rics_compliant': False,
        },
        'brief': {
            'audience': audience,
            'title_ar': f'تقرير {asset_label_ar} — خارج النطاق',
            'sections': [{
                'id': 'out_of_scope',
                'title_ar': 'الإصدار الأول من ثمّن لا يدعم هذه الفئة',
                'content': {
                    'note_ar': (
                        f'العنوان {zone}/{street}/{building} تابع لـ "{asset_label_ar}" '
                        f'بمساحة {plot.pdarea if plot else "—"} م². '
                        'ثمّن مُصمَّم حالياً للفلل والأراضي والقصور والكومباوندات. '
                        + suggestions.get(asset_type, '')
                    ),
                    'options_ar': [
                        'استشارة مُقيِّم متخصص في هذه الفئة',
                        'العودة إلى ثمّن لاحقاً بعد إصدار النسخة الموسّعة',
                        'البحث عن عقار من الفئات المدعومة حالياً',
                    ],
                },
            }],
        },
        'sanity_warnings': [],
        'disclaimer': (
            'ثمّن يجمع البيانات السوقية من المصادر الحكومية والإعلانات النشطة. '
            'هذا تحليل معلوماتي، وليس تقييماً معتمداً وفق RICS/IVS.'
        ),
        'active_listings': {'available': False, 'reason': 'خارج نطاق الإصدار'},
    }


def _check_input_sanity(asset_type, listing_price, rental_income, plot_area):
    """Sprint A.3: Pre-evaluation input validation.

    Returns dict with:
        - warnings_ar: list of human-readable warning strings
        - rental_income_adjusted: rental to use (may be cleared if nonsensical)

    Does NOT block evaluation — only adds warnings. Out-of-scope rejection
    is handled separately via _build_out_of_scope_response.
    """
    warnings = []
    rental_use = rental_income

    # Raw land: no rent is possible (vacant land doesn't produce income)
    if asset_type in ('raw_land', 'land') and rental_income:
        warnings.append(
            f'تم تجاهل الإيجار المُدخَل ({rental_income:,.0f} ر.ق) — الأراضي '
            'الفضاء لا تُنتج دخلاً إيجارياً. التقييم على أساس قيمة الأرض من MoJ فقط.'
        )
        rental_use = None

    # Palace: rental approach is unusual but not impossible
    if asset_type == 'palace' and rental_income:
        warnings.append(
            'القصور نادراً ما تُؤجَّر — تحقق أن الإيجار المُقدَّم واقعي '
            'لأصل بهذه القيمة.'
        )

    # Sanity: zero or negative inputs
    if listing_price is not None and listing_price <= 0:
        warnings.append('سعر الإعلان يجب أن يكون أكبر من صفر.')
    if rental_income is not None and rental_income <= 0:
        warnings.append('الإيجار الشهري يجب أن يكون أكبر من صفر.')

    # Wild ranges (catch typos like 5,000,000 instead of 5,000)
    if rental_income and rental_income > 5_000_000:
        warnings.append(
            f'الإيجار الشهري {rental_income:,.0f} ر.ق مرتفع جداً — '
            'تأكد من العدد (هل أدخلت بدون فواصل، أو سنوي بدل شهري؟).'
        )
    if listing_price and listing_price > 5_000_000_000:
        warnings.append(
            f'سعر الإعلان {listing_price:,.0f} ر.ق مرتفع جداً — '
            'تأكد من العدد.'
        )

    # For DCF assets with rental: rent/m² sanity vs plot area
    if (asset_type in ('compound_large', 'compound_small', 'tower', 'apartment_building')
            and rental_income and plot_area and plot_area > 0):
        rent_per_m2 = (rental_income * 12) / plot_area  # annual rent per m² of plot
        # Typical compound: 80-400 QAR/m²/year. Below 60 = likely partial/single-unit rent.
        # Above 800 = unrealistic for plot of that size (probably wrong input).
        if rent_per_m2 < 60:
            warnings.append(
                f'الإيجار يعادل ~{rent_per_m2:.0f} ر.ق/م² سنوياً للأرض ({plot_area:,.0f} م²) — '
                'منخفض جداً لكومباوند بهذا الحجم. '
                'هل أدخلت إيجار وحدة واحدة بدل المجمع كاملاً؟ '
                'الإيجار المتوقع لأصل بهذا الحجم: 100-300 ر.ق/م² سنوياً.'
            )
        elif rent_per_m2 > 800:
            warnings.append(
                f'الإيجار يعادل ~{rent_per_m2:.0f} ر.ق/م² سنوياً للأرض ({plot_area:,.0f} م²) — '
                'مرتفع جداً لأصل بهذا الحجم. تحقق من الرقم.'
            )

    return {'warnings_ar': warnings, 'rental_income_adjusted': rental_use}


def _check_output_sanity(result, listing_price):
    """Sprint A.3: Post-valuation cross-checks.

    Looks at the produced valuation and yields, warns on implausible results.
    Modifies result in-place by appending to sanity_warnings.

    Yield norms differ by asset class:
      - Residential (villa, palace): 2-5% net is typical
        (location/lifestyle dominate, low yield is normal)
      - Investment-grade (compound, tower, commercial): 5-10% net is typical
        (yield must compensate for management + depreciation)
    """
    warnings = result.get('sanity_warnings', [])
    asset_type = result.get('asset_type', '')

    # Yield bounds by asset class
    if asset_type in ('standalone_villa', 'villa', 'palace'):
        y_normal_min, y_normal_max = 0.02, 0.05
        y_flag_min, y_flag_max = 0.01, 0.08
    else:  # investment-grade
        y_normal_min, y_normal_max = 0.05, 0.10
        y_flag_min, y_flag_max = 0.03, 0.12

    # Net yield sanity (from income_approach if present)
    inc = result.get('income_approach') or {}
    ny = inc.get('net_yield')
    if ny is not None:
        if ny < y_flag_min:
            warnings.append(
                f'صافي العائد ({ny*100:.1f}%) منخفض جداً — أقل من '
                f'{y_flag_min*100:.0f}%. تأكد من الإيجار المُدخَل أو راجع السعر.'
            )
        elif ny > y_flag_max:
            warnings.append(
                f'صافي العائد ({ny*100:.1f}%) مرتفع جداً — أعلى من '
                f'{y_flag_max*100:.0f}%. الإيجار قد يكون مبالغاً فيه، '
                'أو القيمة منخفضة بشدة.'
            )
        elif ny > y_normal_max:
            warnings.append(
                f'صافي العائد ({ny*100:.1f}%) أعلى من النطاق الطبيعي لهذه الفئة '
                f'({y_normal_min*100:.0f}%-{y_normal_max*100:.0f}%) — '
                'فرصة تستحق الفحص.'
            )
        # NOTE: yields just below y_normal_min are common for residential and
        # don't warrant a warning (would just create alert fatigue).

    # Listing vs benchmark gap
    val = result.get('valuation') or {}
    benchmark = val.get('amount')
    if listing_price and benchmark:
        gap = (listing_price - benchmark) / benchmark
        if gap > LISTING_GAP_OVERPRICED_WARN:
            warnings.append(
                f'السعر المطلوب ({listing_price:,.0f}) أعلى بـ {gap*100:.0f}% '
                'من المرجع — السوق غالباً يرفض السعر بهذا المستوى.'
            )
        elif gap < LISTING_GAP_UNDERPRICED_WARN:
            warnings.append(
                f'السعر المطلوب ({listing_price:,.0f}) أقل بـ {abs(gap)*100:.0f}% '
                'من المرجع — تحقق من السبب (تنازل، أقساط، خلاف، حالة المبنى).'
            )

    result['sanity_warnings'] = warnings


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

    # ── Sprint A.1/A.2/A.3: Fast pre-classification + scope filter + sanity checks ──
    # 1. Quick GIS lookup classifies the asset (~0.7s)
    # 2. Sprint A.3: if asset is out of v1 scope → polite rejection
    # 3. Sprint A.3: input sanity checks (rental for land? wild numbers?)
    # 4. DCF-only assets get fast paths (A.1 with no inputs, A.2 with rental)
    # 5. In-scope assets continue to full pipeline below
    DCF_ONLY = {'compound_large', 'tower', 'apartment_building'}
    _qtype = None
    _plot = None
    _loc = None
    _sanity_warnings = []

    try:
        from qatar_gis import QatarGIS, classify_asset
        _gis_lite = QatarGIS(verbose=False)
        _loc = _gis_lite.find_property(zone, street, building)
        if _loc:
            _plot = _gis_lite.get_plot(_loc.pin)
            if _plot:
                _quick = classify_asset(_plot, None)
                _qtype = _quick.asset_type.value

                # ── Sprint A.3 GATE 1: out-of-scope rejection ──
                if _qtype in V1_OUT_OF_SCOPE:
                    return _build_out_of_scope_response(
                        zone, street, building, _loc, _plot, _qtype, audience,
                    )

                # ── Sprint A.3 GATE 2: input sanity (modifies rental_income if needed) ──
                _sanity = _check_input_sanity(_qtype, listing_price, rental_income,
                                              _plot.pdarea if _plot else None)
                _sanity_warnings = _sanity['warnings_ar']
                rental_income = _sanity['rental_income_adjusted']

                # ── Sprint A.1/A.2/A.3: DCF fast paths ──
                if _qtype in DCF_ONLY:
                    if rental_income:
                        # Sprint A.2: income-only valuation (fast)
                        result = _build_fast_income_only_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                            rental_income, listing_price,
                        )
                        # Apply post-valuation sanity + accumulate pre-warnings
                        result['sanity_warnings'] = _sanity_warnings + (result.get('sanity_warnings') or [])
                        _check_output_sanity(result, listing_price)
                        return result
                    elif listing_price:
                        # Sprint A.3 fix: reverse-engineer implied rent (fast)
                        result = _build_fast_listing_only_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                            listing_price,
                        )
                        result['sanity_warnings'] = _sanity_warnings + (result.get('sanity_warnings') or [])
                        return result
                    else:
                        # Sprint A.1: classification only (no inputs)
                        result = _build_fast_insufficient_data_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                        )
                        result['sanity_warnings'] = _sanity_warnings + (result.get('sanity_warnings') or [])
                        return result

                # ── Sprint A.3+ GATE 3: MoJ data-availability check ──
                # Even for in-scope assets (villa, palace, land, compound_small),
                # if MoJ has no comparable in this district, the full 19s pipeline
                # would just produce insufficient_data. This catches edge cases:
                #   - Misclassified towers (as palace) in West Bay → no MoJ palaces there
                #   - Real palaces in remote districts → no MoJ comparable
                #   - Any asset in a district MoJ doesn't cover well
                # Routes to fast paths instead, saving 15-25 seconds.
                try:
                    _dist_obj = _gis_lite.get_district_at_point(_loc.lon, _loc.lat)
                    _district_ar = _dist_obj.aname if _dist_obj else None
                except Exception:
                    _district_ar = None

                _moj_n = _count_moj_comparables(moj_csv_path, _district_ar, _qtype)
                if _moj_n < MIN_MOJ_SAMPLES_FOR_FULL_PIPELINE:
                    # No useful MoJ data → route to fast paths
                    if rental_income:
                        result = _build_fast_income_only_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                            rental_income, listing_price,
                        )
                    elif listing_price:
                        result = _build_fast_listing_only_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                            listing_price,
                        )
                    else:
                        result = _build_fast_insufficient_data_response(
                            zone, street, building, _loc, _plot, _qtype, audience,
                        )
                    # Add a warning explaining the routing decision
                    _sanity_warnings.append(
                        f'لا توجد مقارنة كافية في وزارة العدل لـ "{ASSET_TYPE_AR.get(_qtype, _qtype)}" '
                        f'في {_district_ar or "هذه المنطقة"} (عدد المعاملات المتاحة: {_moj_n}). '
                        'استُخدم المسار السريع بدلاً من المسار الكامل لتفادي الانتظار الطويل دون فائدة. '
                        'قد يكون تصنيف العقار غير دقيق — تحقق من نوع العقار في النتيجة.'
                    )
                    result['sanity_warnings'] = _sanity_warnings + (result.get('sanity_warnings') or [])
                    if rental_income or listing_price:
                        _check_output_sanity(result, listing_price)
                    return result
    except Exception as e:
        # Lite path failed — fall through to full pipeline (defensive)
        print(f"[fast-classify] failed: {e}", file=sys.stderr)

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

    # ── Steps 1.5 + 2 + 7 — Parallelize 3 independent I/O-bound steps ──
    # All three consume `ev` but don't modify it or depend on each other:
    #   - geometric_factors: GIS landmark/HBU analysis (~3s network)
    #   - geo_v2:            geographic widening (~1.5s)
    #   - listings:          active listings fetch (~1.5s network)
    # Sequential total: ~6s. Parallel total: ~3s. Saves ~3 seconds.
    #
    # Sprint A.3+ optimization: critical for staying under Heroku's 30s timeout
    # on cold dyno + network overhead.

    def _run_geometric():
        if not _GEOMETRIC_OK:
            return None
        try:
            pin = None
            lat = lon = None
            rpr = getattr(ev, 'raw_property_report', None)
            if isinstance(rpr, dict):
                pin = rpr.get('pin')
                gps = rpr.get('gps')
                if gps and isinstance(gps, (list, tuple)) and len(gps) >= 2:
                    lon, lat = gps[0], gps[1]
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
                return analyze_geometric_factors(int(pin), float(lat), float(lon), zoning_code)
        except Exception as e:
            print(f"[geometric] failed: {e}", file=sys.stderr)
        return None

    def _run_geo_widening():
        if not (use_geo_v2 and _GEO_OK):
            return None
        try:
            return _run_geo_v2(ev, moj_csv_path)
        except Exception as e:
            print(f"[geo_v2] failed: {e}", file=sys.stderr)
            return None

    def _run_listings_fetch():
        if not (use_listings and _LISTINGS_OK and ev.gis_district_aname):
            return None
        try:
            district = ev.gis_district_aname
            min_a = ev.plot_area_m2 * 0.80 if ev.plot_area_m2 else None
            max_a = ev.plot_area_m2 * 1.20 if ev.plot_area_m2 else None
            listings = fetch_active_listings(
                area=district,
                property_type='villa' if ev.asset_type in ('villa', 'standalone_villa') else 'all',
                min_area=min_a, max_area=max_a,
            )
            if not listings:
                return None
            res = weighted_listings_median(listings)
            res['sample'] = [
                {'location': l.get('location'), 'area_m2': l.get('area_m2'),
                 'price_m2': round(l.get('price_m2', 0)),
                 'age_days': l.get('age_days'), 'url': l.get('url')}
                for l in listings[:5]
            ]
            return res
        except Exception as e:
            print(f"[listings] failed: {e}", file=sys.stderr)
            return None

    # Fire all three in parallel
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_geometric = pool.submit(_run_geometric)
        f_geo_v2 = pool.submit(_run_geo_widening)
        f_listings = pool.submit(_run_listings_fetch)
        try:
            geometric = f_geometric.result(timeout=18)
        except FutureTimeoutError:
            geometric = None
        try:
            geo_v2_result = f_geo_v2.result(timeout=18)
        except FutureTimeoutError:
            geo_v2_result = None
        try:
            listings_result = f_listings.result(timeout=18)
        except FutureTimeoutError:
            listings_result = None

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

    # ── Step 7: Active listings — fetched in parallel block above ──

    # ── Step 8: Build unified output ──
    output = _build_unified_output(
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

    # ── Sprint A.3: append accumulated sanity warnings + post-valuation checks ──
    output['sanity_warnings'] = _sanity_warnings + (output.get('sanity_warnings') or [])
    _check_output_sanity(output, listing_price)
    return output


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

    # ── GPS coordinates (for map links) ──
    rpr = getattr(ev, 'raw_property_report', None)
    if isinstance(rpr, dict):
        gps = rpr.get('gps')
        if gps and isinstance(gps, (list, tuple)) and len(gps) >= 2:
            # GPS stored as [lon, lat] per qatar_gis convention
            output['gps'] = {'lon': gps[0], 'lat': gps[1]}

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

    # ── Accuracy (data-quality tier with customer-friendly labels) ──
    # Labels avoid jargon like "ثقة عالية" alone — instead explain what the
    # number means in concrete terms a non-technical customer understands.
    n = output.get('moj_sample_size', 0) or 0
    if primary and primary['method'] == 'comparison_bracket' and n >= 20:
        output['accuracy'] = {
            'score': 85,
            'label': '🟢 تقدير موثوق',
            'tier': 'high',
            'explanation_ar': f'مبني على {n} صفقة بيع فعلية مسجلة في وزارة العدل لعقارات مشابهة بنفس الحجم.',
        }
    elif primary and primary['method'] in ('comparison_bracket', 'comparison_widened') and n >= 20:
        output['accuracy'] = {
            'score': 78,
            'label': '🟢 تقدير موثوق',
            'tier': 'high',
            'explanation_ar': f'مبني على {n} صفقة بيع فعلية مسجلة (مع توسيع النطاق الجغرافي للعثور على عدد كافٍ من الصفقات المشابهة).',
        }
    elif primary and n >= 10:
        output['accuracy'] = {
            'score': 60,
            'label': '🟡 تقدير إرشادي',
            'tier': 'medium',
            'explanation_ar': f'مبني على {n} صفقة فقط — أقل من المعدل الإحصائي المثالي (20). النتيجة قد تنحرف ±10-15% عن السعر الفعلي. يُفضّل التحقق ميدانياً.',
        }
    elif primary:
        output['accuracy'] = {
            'score': 35,
            'label': '🟠 تقدير تقريبي',
            'tier': 'low',
            'explanation_ar': f'مبني على {n} صفقة فقط — عينة صغيرة جداً. النتيجة تقريبية، لا تعتمد عليها لقرار شراء/بيع بدون فحص ميداني أو مُقيِّم معتمد.',
        }
    else:
        output['accuracy'] = {
            'score': 0,
            'label': '❌ بيانات غير كافية',
            'tier': 'none',
            'explanation_ar': 'لا توجد صفقات بيع كافية لعقارات مشابهة في وزارة العدل. لم يتم إنتاج تقييم.',
        }

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

        # Named landmarks (from GIS dynamic query — no hardcoded whitelist)
        nl = geometric.get('named_landmarks', {})
        if nl.get('malls') or nl.get('metros') or nl.get('mixed_use_venues'):
            geo_section['named_landmarks'] = {
                'malls': nl.get('malls', []),
                'mixed_use_venues': nl.get('mixed_use_venues', []),
                'metros': nl.get('metros', []),
                'closest_mall_m': nl.get('closest_mall_m'),
                'closest_mixed_use_m': nl.get('closest_mixed_use_m'),
                'closest_metro_m': nl.get('closest_metro_m'),
                'walkable_mall': any(m.get('walkable') for m in nl.get('malls', [])),
                'walkable_mixed_use': any(m.get('walkable') for m in nl.get('mixed_use_venues', [])),
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
        # Check walkable mall (within 500m) — separate from mixed-use
        walking_mall = next((m for m in nl.get('malls', []) if m.get('walkable')), None)
        if walking_mall:
            upper_expansion_pct += 0.10
            upper_expansion_reasons.append(f'{walking_mall["name_ar"]} يُمشى (+10%)')
        # Walkable mixed-use venue (e.g. Dar Al Salam with shopping access) — smaller premium
        walking_mixed = next((m for m in nl.get('mixed_use_venues', []) if m.get('walkable')), None)
        if walking_mixed and not walking_mall:  # avoid double-counting if both present
            upper_expansion_pct += 0.07
            upper_expansion_reasons.append(f'{walking_mixed["name_ar"]} يُمشى (+7%)')
        # Walkable metro
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
    v3_rent = v3_result.get('rent_reference') if v3_result else None
    if v3_result and v3_result.get('brief'):
        brief = dict(v3_result['brief'])
        # Sprint A fix: the v3 yield/income/sensitivity sections use stale cap_rate (6.5%)
        # contradicting the corrected primary income_approach (4% for residential).
        # Strategy: filter the stale sections, then rebuild them from `income` (correct).
        STALE_SECTION_IDS = {'yield', 'income_value', 'sensitivity', 'rent_reference'}
        if brief.get('sections'):
            brief['sections'] = [
                s for s in brief['sections']
                if s.get('id') not in STALE_SECTION_IDS
            ]
            # Rebuild investor sections from the corrected `income` cross-check
            if audience == 'investor' and income:
                rebuilt = _build_investor_sections(income, v3_rent, primary)
                # Insert rebuilt sections BEFORE any existing ones (e.g. market_context)
                brief['sections'] = rebuilt + brief['sections']
            # If still no sections (e.g. non-investor), add a placeholder pointer
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
