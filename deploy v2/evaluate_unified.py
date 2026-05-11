#!/usr/bin/env python3
"""
evaluate_unified.py — طبقة الدمج النهائية لثمّن.

تجمع بين:
    1. evaluate_v3.py الحالي (التقييم الثلاثي + RICS compliance)
    2. geo_reference_v2.py الجديد (المنهج الهرمي + الضوابط الستة)
    3. listings_db.py الجديد (إعلانات السوق النشطة بأوزان)

نقطة الدخل الموحدة:
    evaluate_thammen(zone, street, building, ...)

تُرجع نتيجة شاملة جاهزة للعرض في الواجهة.
"""

import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

log = logging.getLogger("thammen.unified")

# ── Existing v2/v3 engine ──
try:
    from evaluate_property import evaluate_property, BuaBreakdown
    _V2_OK = True
except ImportError:
    _V2_OK = False
    print("Warning: evaluate_property not available", file=sys.stderr)

# ── New modules (this PR) ──
try:
    from geo_reference_v2 import build_reference_geo_v2
    _GEO_OK = True
except ImportError:
    _GEO_OK = False
    print("Warning: geo_reference_v2 not available", file=sys.stderr)

try:
    from listings_db import fetch_active_listings, weighted_listings_median
    _LISTINGS_OK = True
except ImportError:
    _LISTINGS_OK = False
    print("Warning: listings_db not available", file=sys.stderr)


# ============================================================
# IN-MEMORY MOJ CACHE (Sprint 1)
# ============================================================
# Read CSV once at first request, reuse for all requests.
# Cache keyed by (path, mtime) so file updates are detected automatically.

_MOJ_CACHE: Dict[tuple, list] = {}


def _get_moj_rows(csv_path: str) -> list:
    """Get MoJ rows from cache or load from CSV."""
    path = Path(csv_path)
    if not path.exists():
        log.error(f"MoJ CSV not found at {csv_path}")
        return []

    mtime = path.stat().st_mtime
    cache_key = (str(path.absolute()), mtime)

    if cache_key in _MOJ_CACHE:
        return _MOJ_CACHE[cache_key]

    log.info(f"Loading MoJ CSV into memory: {csv_path}")
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    # Clear stale entries for same path
    for old_key in list(_MOJ_CACHE.keys()):
        if old_key[0] == str(path.absolute()):
            del _MOJ_CACHE[old_key]

    _MOJ_CACHE[cache_key] = rows
    log.info(f"MoJ cache loaded: {len(rows)} rows from {csv_path}")
    return rows


# ============================================================
# UNIFIED ENTRY POINT
# ============================================================

def evaluate_thammen(
    zone: int,
    street: int,
    building: int,
    moj_csv_path: str = 'moj_weekly.csv',
    listing_price: Optional[float] = None,
    rental_income: Optional[float] = None,
    floors: Optional[int] = None,
    condition: Optional[str] = None,
    annexes: int = 0,
    use_listings: bool = True,
    use_geo_v2: bool = True,
) -> Dict:
    """
    التقييم الشامل لعقار قطري.

    Args:
        zone, street, building:    عنوان عنواني
        moj_csv_path:              مسار ملف MoJ
        listing_price:             السعر المطلوب (إن وُجد)
        rental_income:             الإيجار الفعلي
        floors:                    عدد الطوابق (1, 2, 3, ...)
        condition:                 'excellent' | 'good' | 'fair' | 'poor'
        annexes:                   عدد الملاحق
        use_listings:              هل نستخدم إعلانات السوق النشطة
        use_geo_v2:                هل نستخدم البحث الجغرافي المحسّن

    Returns:
        نتيجة شاملة بالتنسيق الموحد للواجهة
    """
    if not _V2_OK:
        return {'status': 'engine_unavailable', 'error': 'evaluate_property not loaded'}

    # ── Step 1: v2 baseline evaluation ──
    has_reno, full_reno = _condition_to_reno(condition)

    bua_breakdown = None
    if floors:
        # Will be computed inside v2 if possible
        bua_breakdown = _build_simple_bua(floors, annexes)

    try:
        ev = evaluate_property(
            zone=zone,
            street=street,
            building=building,
            moj_csv_path=moj_csv_path,
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

    # ── Step 2: Get GPS for downstream modules ──
    # evaluate_property doesn't expose lat/lon directly, so query GIS
    lat = None
    lon = None
    try:
        from qatar_gis import QatarGIS
        gis = QatarGIS(verbose=False)
        loc = gis.find_property(zone, street, building)
        if loc:
            lat = loc.lat
            lon = loc.lon
    except Exception as e:
        print(f"GIS lookup for coords failed: {e}", file=sys.stderr)

    # ── Step 3: Enhanced geo reference (v2) ──
    # NOTE: Hard timeout of 18 seconds to stay within Heroku's 30s limit
    # (v2 takes ~15s, leaving 12-15s for geo_v2 + listings)
    import time
    geo_v2_start = time.time()
    GEO_V2_TIMEOUT_S = 18

    geo_v2_result = None
    geo_v2_error = None
    if use_geo_v2 and _GEO_OK and lat and lon:
        try:
            # Sprint 1: use cached MoJ rows
            rows = _get_moj_rows(moj_csv_path)
            print(f"[geo_v2] CSV cached: {len(rows)} rows, lat={lat}, lon={lon}", file=sys.stderr)

            zoning = None
            if ev.valuation and ev.valuation.factors_detail:
                for f_factor in ev.valuation.factors_detail:
                    code = f_factor.get('code', '')
                    if code.startswith('zoning'):
                        label = f_factor.get('label_ar', '')
                        for z in ['R1', 'R2', 'R3', 'C', 'IND']:
                            if z in label or z in code:
                                zoning = z
                                break
                        break
            print(f"[geo_v2] zoning detected: {zoning}", file=sys.stderr)

            # Map asset_type to geo_v2 category
            asset_type_to_category = {
                'standalone_villa': 'villa',
                'villa': 'villa',
                'palace': 'palace',
                'raw_land': 'land',
                'land': 'land',
                'compound_small': 'compound',
                'compound_large': 'compound',
            }
            geo_category = asset_type_to_category.get(
                ev.asset_type, 'villa'
            )
            print(f"[geo_v2] asset_type={ev.asset_type} → category={geo_category}",
                  file=sys.stderr)

            # Use signal-based timeout (Unix only — Heroku is Linux)
            import signal

            def _timeout_handler(signum, frame):
                raise TimeoutError(f'geo_v2 exceeded {GEO_V2_TIMEOUT_S}s limit')

            # Set alarm
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(GEO_V2_TIMEOUT_S)

            try:
                geo_v2_result = build_reference_geo_v2(
                    rows=rows,
                    lat=lat, lon=lon,
                    category=geo_category,
                    plot_area_m2=ev.plot_area_m2,
                    target_zoning=zoning,
                )
            finally:
                signal.alarm(0)  # cancel alarm
                signal.signal(signal.SIGALRM, old_handler)

            elapsed = time.time() - geo_v2_start
            # Diagnostic logging
            if geo_v2_result:
                p = geo_v2_result.get('primary', {})
                print(f"[geo_v2] result: primary_n={p.get('n')}, "
                      f"moj_names={p.get('moj_names')}, "
                      f"decision={geo_v2_result.get('decision')}, "
                      f"elapsed={elapsed:.1f}s",
                      file=sys.stderr)

                # Log candidate evaluation outcomes
                accepted = geo_v2_result.get('accepted_areas', [])
                rejected = geo_v2_result.get('rejected_areas', [])
                if accepted:
                    print(f"[geo_v2] accepted: " +
                          ", ".join(f"{a['name']}({a['n']},{a['distance_m']}m)"
                                    for a in accepted),
                          file=sys.stderr)
                if rejected:
                    print(f"[geo_v2] rejected: " +
                          ", ".join(f"{r['name']}({r['reasons'] if 'reasons' in r else r.get('rejection_reasons',[])})"
                                    for r in rejected[:5]),
                          file=sys.stderr)
                # Final weighted result
                print(f"[geo_v2] final: total_n={geo_v2_result.get('total_n')}, "
                      f"value={geo_v2_result.get('estimated_value')}, "
                      f"confidence={geo_v2_result.get('confidence')}",
                      file=sys.stderr)
        except TimeoutError as te:
            geo_v2_error = str(te)
            elapsed = time.time() - geo_v2_start
            print(f"[geo_v2] TIMEOUT after {elapsed:.1f}s — falling back to v2", file=sys.stderr)
            geo_v2_result = None
        except Exception as e:
            geo_v2_error = str(e)
            import traceback
            print(f"[geo_v2] FAILED: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    else:
        print(f"[geo_v2] SKIPPED: use_geo_v2={use_geo_v2}, "
              f"_GEO_OK={_GEO_OK}, lat={lat}, lon={lon}", file=sys.stderr)

    # ── Step 4: Active listings cross-reference ──
    # Check remaining time budget — Heroku timeout is 30s, evaluate_property takes ~15s
    elapsed_so_far = time.time() - geo_v2_start
    REMAINING_BUDGET_S = 8  # leave at least 8s for listings + response

    listings_result = None
    if use_listings and _LISTINGS_OK and ev.gis_district_aname and elapsed_so_far < REMAINING_BUDGET_S:
        try:
            district = ev.gis_district_aname
            min_a = ev.plot_area_m2 * 0.80 if ev.plot_area_m2 else None
            max_a = ev.plot_area_m2 * 1.20 if ev.plot_area_m2 else None

            listings = fetch_active_listings(
                area=district,
                property_type='villa' if ev.asset_type == 'villa' else 'all',
                min_area=min_a, max_area=max_a,
            )
            if listings:
                listings_result = weighted_listings_median(listings)
                listings_result['raw_listings'] = [
                    {
                        'location': l.get('location'),
                        'area_m2': l.get('area_m2'),
                        'price_m2': round(l.get('price_m2', 0)),
                        'age_days': l.get('age_days'),
                        'weight': l.get('weight'),
                        'url': l.get('url'),
                    }
                    for l in listings[:10]
                ]
        except Exception as e:
            print(f"listings failed: {e}", file=sys.stderr)
    elif elapsed_so_far >= REMAINING_BUDGET_S:
        print(f"[listings] SKIPPED: time budget exceeded "
              f"({elapsed_so_far:.1f}s used)", file=sys.stderr)

    # ── Step 5: Build unified output ──
    output = _build_unified_output(ev, geo_v2_result, listings_result)
    return output


# ============================================================
# HELPERS
# ============================================================

def _condition_to_reno(condition: Optional[str]) -> tuple:
    """Map condition label to renovation flags."""
    mapping = {
        'excellent': (True, True),
        'good':      (True, False),
        'fair':      (False, False),
        'poor':      (False, False),
    }
    return mapping.get(condition or 'good', (False, False))


def _build_simple_bua(floors: int, annexes: int) -> Optional['BuaBreakdown']:
    """Simple BUA breakdown — placeholder. Real one in api.py uses GIS."""
    if not _V2_OK:
        return None
    # Default rough estimate; api.py builds a better one from GIS footprint
    annex_m2 = annexes * 50 if annexes else 0
    return BuaBreakdown(
        main_footprint_m2=300,  # placeholder
        basement_m2=0,
        upper_floors_m2=300 * 0.85 * (floors - 1) if floors >= 2 else 0,
        upper_floor_count=max(0, floors - 1),
        annexes_m2=annex_m2,
        annex_count=annexes,
        external_m2=0,
    )


def _build_unified_output(ev, geo_v2, listings) -> Dict:
    """Build the unified API response combining all three sources."""
    # Start with v2 baseline (preserves existing api.py compatibility)
    output = {
        'status': 'ok',
        'engine_version': 'thammen-v3.1-unified',
        'address': getattr(ev, 'address', None),
        'valuation_date': getattr(ev, 'valuation_date', None),
        'district': getattr(ev, 'gis_district_aname', None),
        'plot_area_m2': getattr(ev, 'plot_area_m2', None),
        'asset_type': getattr(ev, 'asset_type', None),
    }

    # ── Primary valuation (from v2 engine) ──
    if getattr(ev, 'blended', None):
        b = ev.blended
        output['valuation'] = {
            'amount': _r100k(b.blended_value),
            'low': _r100k(b.blended_low),
            'high': _r100k(b.blended_high),
            'method': 'blended_3way',
        }
    elif ev.valuation and ev.valuation.moj_median_total:
        v = ev.valuation
        val = v.fair_price_total or v.moj_median_total
        output['valuation'] = {
            'amount': _r100k(val),
            'low': _r100k(v.estimated_value_low),
            'high': _r100k(v.estimated_value_high),
            'method': 'moj_only',
        }

    # ── MoJ details (set FIRST so geo_v2 can override) ──
    if ev.valuation:
        output['moj_sample_size'] = ev.valuation.bracket_n

    # ── NEW v3.1: Use geo_v2 valuation when it has good confidence ──
    # geo_v2 applies RICS methodology — prefer it whenever confidence allows
    v2_n = output.get('moj_sample_size', 0) or 0
    geo_n = (geo_v2.get('total_n', 0) if geo_v2 else 0) or 0
    geo_conf = geo_v2.get('confidence') if geo_v2 else None

    # Override v2 valuation with geo_v2 when ANY of:
    #   - geo_v2 has high confidence (n >= 20)
    #   - geo_v2 has medium confidence and at least equal n
    #   - geo_v2 has 3x more data than v2 (catches NBSP/naming issues)
    should_override = (
        geo_v2 and geo_v2.get('status') == 'ok'
        and geo_v2.get('estimated_value')
        and (
            geo_conf == 'high'
            or (geo_conf == 'medium' and geo_n >= v2_n)
            or geo_n >= max(5, v2_n * 3)
        )
    )

    if should_override:
        output['valuation'] = {
            'amount': _r100k(geo_v2['estimated_value']),
            'low': _r100k(geo_v2.get('range_low')),
            'high': _r100k(geo_v2.get('range_high')),
            'method': 'geo_v2_hierarchical',
            'n_transactions': geo_n,
            'override_reason': (
                f'البحث الجغرافي المحسّن أعطى {geo_n} معاملة بثقة {geo_conf}'
            ),
        }
        output['moj_sample_size'] = geo_n

    # ── Confidence ──
    output['accuracy'] = {
        'score': getattr(ev, 'confidence_score', None),
        'label': getattr(ev, 'confidence_label', None),
    }

    # NEW v3.1: Override accuracy when geo_v2 provided better data
    if geo_v2 and geo_v2.get('confidence') == 'high':
        output['accuracy'] = {
            'score': 85,
            'label': 'ثقة عالية 🟢',
        }
    elif geo_v2 and geo_v2.get('confidence') == 'medium':
        output['accuracy'] = {
            'score': 65,
            'label': 'ثقة متوسطة 🟡',
        }

    # ── Trend ──
    if getattr(ev, 'trend', None):
        output['trend'] = {
            'label': ev.trend.get('label'),
            'slope_pct': ev.trend.get('slope_annual_pct', 0) * 100,
            'years': ev.trend.get('years', []),
        }
        # NEW v3.1: cap unrealistic trend slopes
        # Real estate trends > 8%/year are extreme and shouldn't drive decisions
        if abs(output['trend']['slope_pct']) > 8:
            output['trend']['warning'] = (
                f'⚠️ اتجاه استثنائي ({output["trend"]["slope_pct"]:.1f}%/سنة) — '
                f'لا يُستخدم للاستقراء المستقبلي. النمو المستدام في قطر 2-4%/سنة.'
            )

    # ── Location features ──
    LABEL_FIXES = {
        'تزوير R1': 'منطقة سكنية خاصة (R1)',
        'تزوير R2': 'منطقة سكنية (R2)',
        'تزوير R3': 'منطقة سكنية مكثفة (R3)',
        'تزوير C': 'منطقة تجارية (C)',
        'تنظيم R1': 'منطقة سكنية خاصة (R1)',
        'تنظيم R2': 'منطقة سكنية (R2)',
        'تنظيم R3': 'منطقة سكنية مكثفة (R3)',
        'تنظيم C': 'منطقة تجارية (C)',
    }
    HEIGHT_FIXES = {
        'G+1+P': 'أرضي + أول + سطح',
        'G+2+P': 'أرضي + طابقين + سطح',
        'G+P': 'أرضي + سطح',
        'G+1': 'أرضي + أول',
        'G+2': 'أرضي + طابقين',
    }

    output['location_features'] = []
    if ev.valuation and ev.valuation.factors_detail:
        for f in ev.valuation.factors_detail:
            label = f.get('label_ar', '')
            # Apply label fixes
            for old, new in LABEL_FIXES.items():
                label = label.replace(old, new)
            for old, new in HEIGHT_FIXES.items():
                if old in label:
                    label = label.replace(old, new)

            # Fix plot_shape direction: regular shape = positive, irregular = negative
            code = f.get('code', '')
            direction = f.get('direction', 'neutral')
            is_positive = direction == 'positive'
            if code == 'plot_shape':
                # If label says "منتظمة" (regular), it's positive
                if 'منتظم' in label and 'غير' not in label:
                    is_positive = True
                elif 'غير منتظم' in label:
                    is_positive = False

            output['location_features'].append({
                'label': label,
                'positive': is_positive,
            })

    # ── Disclaimer & ID ──
    output['disclaimer'] = getattr(ev, 'disclaimer', None)
    output['valuation_id'] = getattr(ev, 'valuation_id', None)

    # ── Reasoning trace ──
    if getattr(ev, 'reasoning_trace', None):
        output['reasoning_trace'] = ev.reasoning_trace

    # ─── NEW v3.1 SECTIONS ───

    # ── Enhanced geo reference (RICS six criteria) ──
    if geo_v2:
        output['geo_reference_v2'] = {
            'available': True,
            'decision': geo_v2.get('decision'),
            'decision_label': geo_v2.get('decision_label'),
            'confidence': geo_v2.get('confidence'),
            'confidence_ar': geo_v2.get('confidence_ar'),
            'primary': {
                'name': geo_v2.get('primary', {}).get('gis_name'),
                'zoning': geo_v2.get('primary', {}).get('zoning'),
                'n': geo_v2.get('primary', {}).get('n'),
                'median_m2': geo_v2.get('primary', {}).get('median_m2'),
                'median_ft': geo_v2.get('primary', {}).get('median_ft'),
            },
            'accepted_areas': [
                {
                    'name': a['name'],
                    'distance_m': a['distance_m'],
                    'n': a['n'],
                    'median_m2': a['median_m2'],
                    'price_gap_pct': a.get('price_gap_pct'),
                    'location_adjustment': a.get('location_adjustment'),
                }
                for a in geo_v2.get('accepted_areas', [])
            ],
            'rejected_areas': [
                {
                    'name': r['name'],
                    'distance_m': r['distance_m'],
                    'reasons': r['rejection_reasons'],
                }
                for r in geo_v2.get('rejected_areas', [])[:5]
            ],
            'weighted_median_m2': geo_v2.get('weighted_median_m2'),
            'estimated_value': geo_v2.get('estimated_value'),
            'range_low': geo_v2.get('range_low'),
            'range_high': geo_v2.get('range_high'),
            'range_width_pct': geo_v2.get('range_width_pct'),
            'total_n': geo_v2.get('total_n'),
        }

    # ── Active listings (market sentiment) ──
    if listings:
        output['active_listings'] = {
            'available': True,
            'n': listings.get('n'),
            'effective_n': listings.get('effective_n'),
            'weighted_median_m2': listings.get('weighted_median_m2'),
            'estimated_market_m2': listings.get('estimated_market_m2'),
            'discount_applied_pct': round(listings.get('discount_applied', 0) * 100, 1),
            'oldest_days': listings.get('oldest_days'),
            'newest_days': listings.get('newest_days'),
            'tier_breakdown': listings.get('tier_breakdown'),
            'sample': listings.get('raw_listings', [])[:5],
        }
    elif _LISTINGS_OK:
        output['active_listings'] = {
            'available': False,
            'reason': 'لا توجد إعلانات نشطة مطابقة في هذه المنطقة',
        }

    # ── Cross-method consistency check (NEW) ──
    output['consistency_check'] = _check_consistency(output)

    return output


def _check_consistency(output: Dict) -> Dict:
    """Compare values from different methods and report consistency."""
    v_main = output.get('valuation', {}).get('amount')
    v_geo = output.get('geo_reference_v2', {}).get('estimated_value')
    listings_m2 = output.get('active_listings', {}).get('estimated_market_m2')
    plot = output.get('plot_area_m2')

    methods = []
    if v_main:
        methods.append(('blended_v2', v_main))
    if v_geo:
        methods.append(('geo_v2', v_geo))
    if listings_m2 and plot:
        methods.append(('listings', listings_m2 * plot))

    if len(methods) < 2:
        return {'status': 'insufficient_methods'}

    values = [v for _, v in methods]
    spread = (max(values) - min(values)) / min(values) * 100

    if spread < 15:
        status = 'consistent'
        label_ar = 'الطرق متسقة ✅'
    elif spread < 30:
        status = 'moderate_divergence'
        label_ar = 'تباين متوسط ⚠️'
    else:
        status = 'high_divergence'
        label_ar = 'تباين كبير 🔴 — يحتاج فحص'

    return {
        'status': status,
        'label_ar': label_ar,
        'spread_pct': round(spread, 1),
        'methods': [{'name': n, 'value': v} for n, v in methods],
    }


def _r100k(n):
    if n is None:
        return None
    return round(n / 100000) * 100000


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
    p.add_argument('--asking', type=float)
    p.add_argument('--rent', type=float)
    p.add_argument('--floors', type=int)
    p.add_argument('--condition', choices=['excellent', 'good', 'fair', 'poor'])
    p.add_argument('--annexes', type=int, default=0)
    p.add_argument('--no-listings', action='store_true')
    p.add_argument('--no-geo-v2', action='store_true')
    args = p.parse_args()

    result = evaluate_thammen(
        zone=args.zone,
        street=args.street,
        building=args.building,
        moj_csv_path=args.moj,
        listing_price=args.asking,
        rental_income=args.rent,
        floors=args.floors,
        condition=args.condition,
        annexes=args.annexes,
        use_listings=not args.no_listings,
        use_geo_v2=not args.no_geo_v2,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
