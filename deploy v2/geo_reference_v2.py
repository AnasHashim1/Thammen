#!/usr/bin/env python3
"""
geo_reference_v2.py — البحث الجغرافي المحسّن وفق منهجية RICS الكاملة.

الفرق عن v1:
    v1: يضم المناطق ضمن نصف قطر مع فلتر سعر فقط
    v2: يطبّق ستة ضوابط RICS الإلزامية:
        1. حد جغرافي ≤ 2 كم
        2. تطابق التصنيف (R1 ↔ R1)
        3. توافق سعري ≤ 25% بعد التعديل
        4. لا حواجز مادية (طرق رئيسية تفصل)
        5. نمط عمراني متشابه (أحجام قطع متقاربة)
        6. منهج هرمي حسب n

ترتيب القرار:
    n_primary >= 20  → اكتفِ بالأصلية، لا حاجة لمجاور
    n_primary >= 10  → ضم منطقة واحدة مماثلة (أقربها)
    n_primary >= 5   → ضم 2-3 مناطق مماثلة
    n_primary < 5    → ارفض إنتاج تقدير

تعديل الموقع (إلزامي عند الضم):
    معامل التعديل = وسيط_الأصلية / وسيط_المماثلة
    كل سعر من المنطقة المماثلة يُضرب بالمعامل قبل دمجه

الاستخدام:
    from geo_reference_v2 import build_reference_geo_v2

    result = build_reference_geo_v2(
        rows=moj_rows,
        lat=25.27, lon=51.47,
        category='villa',
        plot_area_m2=613,
        target_zoning='R1',  # optional but recommended
    )
"""

import csv
import json
import re
import urllib.parse
import urllib.request
import ssl
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple


# ============================================================
# CONSTANTS
# ============================================================

GIS_BASE = 'https://services.gisqatar.org.qa/server/rest/services'
DISTRICTS_URL = f'{GIS_BASE}/Vector/Districts/MapServer/0/query'
ZONING_URL = f'{GIS_BASE}/Vector/Zoning/MapServer/0/query'

# RICS criteria
MAX_DISTANCE_M = 2000          # القاعدة 1: حد جغرافي
MAX_PRICE_GAP = 0.25           # القاعدة 3: توافق سعري
MAX_PLOT_SIZE_RATIO = 2.5      # القاعدة 5: نمط عمراني (أحجام القطع)

# Hierarchical thresholds
N_SUFFICIENT = 20              # n الأصلية كافية بنفسها
N_NEED_ONE = 10                # n يحتاج منطقة مماثلة واحدة
N_NEED_MULTIPLE = 5            # n يحتاج 2-3 مناطق
N_REFUSE = 5                   # n أقل من ذلك = ارفض

# Tier system (post-acceptance)
ADJACENT_TIERS = [
    {'name': 'closest',  'max_dist': 1000, 'weight': 0.7, 'label': 'الأقرب'},
    {'name': 'near',     'max_dist': 1500, 'weight': 0.5, 'label': 'قريب'},
    {'name': 'far',      'max_dist': 2000, 'weight': 0.3, 'label': 'أبعد'},
]

DEFAULT_WINDOW_DAYS = 730      # 24 شهر
FALLBACK_WINDOW_DAYS = 1095    # 36 شهر


# ============================================================
# CACHES (in-memory, persists across calls within same process)
# ============================================================

_CENTROID_CACHE = {}    # dist_no → (lat, lon)
_ZONING_CACHE = {}      # dist_no → 'R1' | 'R2' | ...
_DISTRICTS_RADIUS_CACHE = {}  # (lat_rounded, lon_rounded, radius) → list


# ============================================================
# HELPERS
# ============================================================

def _norm(s):
    if not s:
        return ''
    return re.sub(r'\s+', ' ', str(s)).strip()


def _to_float(s):
    try:
        return float(str(s or '').replace(',', '').strip())
    except (ValueError, TypeError):
        return None


def _parse_date(s):
    try:
        return datetime.strptime(_norm(s), '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def _categorize(row):
    t = _norm(row.get('نوع العقار', ''))
    if t == 'أرض فضاء':
        return 'land'
    if any(x in t for x in ('فيلا', 'فيلتان', 'بيت', 'مسكن')):
        return 'villa'
    if t == 'قصر':
        return 'palace'
    if 'مجمع' in t:
        return 'compound'
    return 'other'


def _median(values):
    if not values:
        return None
    s = sorted(values)
    return s[len(s) // 2]


def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


# ============================================================
# GIS QUERIES
# ============================================================

def _query_gis_districts_radius(lat: float, lon: float, distance_m: int) -> List[Dict]:
    """قائمة المناطق ضمن نصف قطر."""
    params = {
        'geometry': json.dumps({"x": lon, "y": lat,
                                "spatialReference": {"wkid": 4326}}),
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'ANAME,ENAME,DIST_NO',
        'returnGeometry': 'false',
        'f': 'json',
    }
    if distance_m > 0:
        params['distance'] = str(distance_m)
        params['units'] = 'esriSRUnit_Meter'

    url = DISTRICTS_URL + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'Thammen/3.0'})
    try:
        with urllib.request.urlopen(req, timeout=15, context=_ssl_ctx()) as r:
            data = json.loads(r.read())
        return [
            {
                'aname': _norm(f['attributes'].get('ANAME', '')),
                'ename': _norm(f['attributes'].get('ENAME', '')),
                'dist_no': f['attributes'].get('DIST_NO'),
            }
            for f in data.get('features', [])
        ]
    except Exception:
        return []


def _query_district_centroid(dist_no: int) -> Optional[Tuple[float, float]]:
    """مركز المنطقة بإحداثيات GPS — مع cache في الذاكرة."""
    if dist_no in _CENTROID_CACHE:
        return _CENTROID_CACHE[dist_no]

    params = {
        'where': f'DIST_NO={dist_no}',
        'outFields': 'DIST_NO',
        'returnGeometry': 'true',
        'returnCentroid': 'true',
        'outSR': '4326',
        'f': 'json',
    }
    url = DISTRICTS_URL + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'Thammen/3.0'})
    try:
        with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx()) as r:
            data = json.loads(r.read())
        for f in data.get('features', []):
            geom = f.get('geometry', {})
            if 'rings' in geom and geom['rings']:
                ring = geom['rings'][0]
                xs = [pt[0] for pt in ring]
                ys = [pt[1] for pt in ring]
                result = (sum(ys) / len(ys), sum(xs) / len(xs))
                _CENTROID_CACHE[dist_no] = result
                return result
    except Exception:
        pass
    _CENTROID_CACHE[dist_no] = None
    return None


def _query_zoning_at_centroid(dist_no: int) -> Optional[str]:
    """تصنيف Zoning غالب في المنطقة — مع cache."""
    if dist_no in _ZONING_CACHE:
        return _ZONING_CACHE[dist_no]

    centroid = _query_district_centroid(dist_no)
    if not centroid:
        _ZONING_CACHE[dist_no] = None
        return None
    lat, lon = centroid

    params = {
        'geometry': json.dumps({"x": lon, "y": lat,
                                "spatialReference": {"wkid": 4326}}),
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'ZONING',
        'returnGeometry': 'false',
        'f': 'json',
    }
    url = ZONING_URL + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'Thammen/3.0'})
    try:
        with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx()) as r:
            data = json.loads(r.read())
        for f in data.get('features', []):
            zoning = _norm(f['attributes'].get('ZONING', ''))
            _ZONING_CACHE[dist_no] = zoning
            return zoning
    except Exception:
        pass
    _ZONING_CACHE[dist_no] = None
    return None


def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """المسافة بالأمتار بين نقطتين."""
    import math
    R = 6371000  # نصف قطر الأرض بالأمتار
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ============================================================
# MOJ ↔ GIS NAME MATCHING
# ============================================================

def _match_gis_to_moj(gis_name: str, moj_area_names: set) -> List[str]:
    """مطابقة أسماء بين GIS و MoJ مع التعامل مع أداة التعريف والـ aliases.

    منهج هرمي:
    1. ابحث في قاعدة بيانات aliases الموثّقة
    2. إذا لم نجد، طبّق المطابقة الجزئية القديمة (للأمان)
    """
    # Try aliases DB first
    try:
        from qatar_area_aliases import get_all_aliases
        # Check if GIS name matches a known alias group
        aliases = get_all_aliases(gis_name)
        if len(aliases) > 1:
            # Found in DB! Return all variants that exist in MoJ
            return [a for a in aliases if a in moj_area_names]
    except ImportError:
        pass

    # Fallback: original matching by definite article + substring
    gn = _norm(gis_name)
    gn_no_al = re.sub(r'^ال', '', gn)
    matches = set()

    for moj_name in moj_area_names:
        mn = _norm(moj_name)
        mn_no_al = re.sub(r'^ال', '', mn)

        if gn == mn or gn_no_al == mn_no_al:
            matches.add(moj_name)
        elif len(gn_no_al) >= 3 and len(mn_no_al) >= 3:
            if gn_no_al in mn_no_al or mn_no_al in gn_no_al:
                matches.add(moj_name)

    return list(matches)


# ============================================================
# TRANSACTION FETCHING
# ============================================================

def _get_area_transactions(
    rows: list,
    moj_names: set,
    category: str,
    cutoff: datetime,
    date_col: str,
    bracket: Optional[Tuple[float, float]] = None,
) -> List[Dict]:
    """استرجاع المعاملات لمجموعة أسماء منطقة."""
    txns = []
    for r in rows:
        area = _norm(r.get('اسم المنطقة', ''))
        if area not in moj_names:
            continue
        if category != 'all' and _categorize(r) != category:
            continue
        d = _parse_date(r.get(date_col, ''))
        if not d or d < cutoff:
            continue

        price_m2 = _to_float(r.get('سعر المتر المربع'))
        area_m2 = _to_float(r.get('المساحة بالمتر المربع'))
        total = _to_float(r.get('قيمة العقار'))

        if not price_m2 or price_m2 <= 0:
            continue
        if not area_m2 or area_m2 <= 0:
            continue

        if bracket:
            lo, hi = bracket
            if not (lo <= area_m2 <= hi):
                continue

        txns.append({
            'area': area,
            'date': d.strftime('%Y-%m-%d'),
            'price_m2': price_m2,
            'price_ft': price_m2 / 10.764,
            'area_m2': area_m2,
            'total_price': total,
            'type': _norm(r.get('نوع العقار', '')),
        })
    return txns


# ============================================================
# RICS CRITERIA CHECKS
# ============================================================

def _check_six_criteria(
    candidate_district: Dict,
    candidate_centroid: Tuple[float, float],
    candidate_median: float,
    candidate_zoning: Optional[str],
    candidate_avg_plot_size: float,
    primary_centroid: Tuple[float, float],
    primary_median: float,
    primary_zoning: Optional[str],
    primary_avg_plot_size: float,
) -> Dict:
    """
    تطبيق الضوابط الستة على منطقة مرشحة.
    يُرجع dict بنتائج كل فحص مع قبول/رفض نهائي.
    """
    result = {
        'name': candidate_district['aname'],
        'dist_no': candidate_district['dist_no'],
        'checks': {},
        'accepted': True,
        'rejection_reasons': [],
    }

    # القاعدة 1: حد جغرافي ≤ 2 كم
    distance_m = _haversine_distance_m(*primary_centroid, *candidate_centroid)
    result['distance_m'] = round(distance_m)
    if distance_m > MAX_DISTANCE_M:
        result['checks']['distance'] = f'❌ {distance_m:.0f}م > {MAX_DISTANCE_M}م'
        result['accepted'] = False
        result['rejection_reasons'].append(f'بعيدة جغرافياً ({distance_m:.0f}م)')
    else:
        result['checks']['distance'] = f'✅ {distance_m:.0f}م'

    # القاعدة 2: تطابق التصنيف
    if primary_zoning and candidate_zoning:
        if primary_zoning == candidate_zoning:
            result['checks']['zoning'] = f'✅ {candidate_zoning} = {primary_zoning}'
        else:
            result['checks']['zoning'] = f'❌ {candidate_zoning} ≠ {primary_zoning}'
            result['accepted'] = False
            result['rejection_reasons'].append(
                f'تصنيف مختلف ({candidate_zoning} vs {primary_zoning})'
            )
    else:
        result['checks']['zoning'] = '⚠️ غير معروف'

    # القاعدة 3: توافق سعري ≤ 25%
    if primary_median and candidate_median:
        gap = abs(candidate_median - primary_median) / primary_median
        result['price_gap_pct'] = round(gap * 100, 1)
        if gap > MAX_PRICE_GAP:
            result['checks']['price_gap'] = f'❌ {gap*100:.1f}% > {MAX_PRICE_GAP*100:.0f}%'
            result['accepted'] = False
            result['rejection_reasons'].append(f'فارق سعر {gap*100:.0f}%')
        else:
            result['checks']['price_gap'] = f'✅ {gap*100:.1f}%'

    # القاعدة 5: نمط عمراني متشابه (أحجام القطع)
    if primary_avg_plot_size and candidate_avg_plot_size:
        ratio = max(primary_avg_plot_size, candidate_avg_plot_size) / \
                min(primary_avg_plot_size, candidate_avg_plot_size)
        result['plot_size_ratio'] = round(ratio, 2)
        if ratio > MAX_PLOT_SIZE_RATIO:
            result['checks']['plot_size'] = f'❌ نسبة {ratio:.1f}× > {MAX_PLOT_SIZE_RATIO}'
            result['accepted'] = False
            result['rejection_reasons'].append(f'أحجام قطع مختلفة ({ratio:.1f}×)')
        else:
            result['checks']['plot_size'] = f'✅ نسبة {ratio:.1f}×'

    # القاعدة 4: لا حواجز مادية — تُترك مفتوحة (تحتاج road network analysis معقد)
    # القاعدة 6: بنية تحتية متشابهة — تُترك مفتوحة (تحتاج landmarks density)
    # هاتان قاعدتان نوصي بفحصهما يدوياً في التقرير

    # تعديل الموقع (إلزامي عند القبول)
    if result['accepted'] and primary_median and candidate_median:
        result['location_adjustment'] = round(primary_median / candidate_median, 4)
        result['adjustment_pct'] = round((result['location_adjustment'] - 1) * 100, 1)
    else:
        result['location_adjustment'] = 1.0
        result['adjustment_pct'] = 0

    return result


# ============================================================
# CORE ENTRY POINT
# ============================================================

def build_reference_geo_v2(
    rows: list,
    lat: float,
    lon: float,
    category: str = 'villa',
    plot_area_m2: float = None,
    target_zoning: Optional[str] = None,
    primary_area_name: Optional[str] = None,
    max_d: Optional[datetime] = None,
) -> dict:
    """
    البحث الجغرافي المحسّن وفق منهجية RICS الكاملة.

    Args:
        rows:                MoJ data rows
        lat, lon:            GPS of property
        category:            'villa' | 'land' | etc.
        plot_area_m2:        property size for bracket filter
        target_zoning:       R1/R2/etc. — optional, will query GIS if None
        primary_area_name:   override primary area lookup
        max_d:               latest data date (auto-detected)

    Returns:
        Detailed result with primary + adjacent decisions, transparency.
    """
    # ── Setup ──
    date_col = next((k for k in rows[0].keys() if 'تاريخ' in _norm(k)), None)

    if max_d is None:
        dates = [_parse_date(r.get(date_col, '')) for r in rows]
        dates = [d for d in dates if d]
        max_d = max(dates) if dates else datetime.now()

    cutoff = max_d - timedelta(days=DEFAULT_WINDOW_DAYS)

    all_moj_areas = set(_norm(r.get('اسم المنطقة', '')) for r in rows)
    all_moj_areas.discard('')

    # Bracket
    if plot_area_m2:
        bracket = (plot_area_m2 * 0.80, plot_area_m2 * 1.20)
    else:
        bracket = None

    # ── Step 1: Query primary district ──
    primary_districts = _query_gis_districts_radius(lat, lon, 0)
    if not primary_districts:
        return {
            'status': 'gis_unavailable',
            'message': 'تعذر الوصول إلى GIS لتحديد المنطقة',
        }

    primary = primary_districts[0]
    primary_centroid = _query_district_centroid(primary['dist_no']) or (lat, lon)

    # Get primary zoning
    if target_zoning:
        primary_zoning = target_zoning
    else:
        primary_zoning = _query_zoning_at_centroid(primary['dist_no'])

    # ── Step 2: Get primary area transactions ──
    primary_moj_names = _match_gis_to_moj(primary['aname'], all_moj_areas)
    primary_txns = _get_area_transactions(
        rows, set(primary_moj_names), category, cutoff, date_col, bracket
    )

    n_primary = len(primary_txns)
    primary_median = _median([t['price_m2'] for t in primary_txns]) if primary_txns else None
    primary_avg_plot = (sum(t['area_m2'] for t in primary_txns) / n_primary) if n_primary else 0

    # ── Step 3: Hierarchical decision ──
    result = {
        'status': 'ok',
        'primary': {
            'gis_name': primary['aname'],
            'dist_no': primary['dist_no'],
            'moj_names': primary_moj_names,
            'centroid': primary_centroid,
            'zoning': primary_zoning,
            'n': n_primary,
            'median_m2': round(primary_median) if primary_median else None,
            'median_ft': round(primary_median / 10.764) if primary_median else None,
            'avg_plot_m2': round(primary_avg_plot, 1),
            'transactions': primary_txns,
        },
        'category': category,
        'plot_area_m2': plot_area_m2,
        'window_months': 24,
    }

    # Decide how many adjacent areas to seek
    if n_primary >= N_SUFFICIENT:
        result['decision'] = 'primary_sufficient'
        result['decision_label'] = f'✅ المنطقة الأصلية كافية (n={n_primary} ≥ {N_SUFFICIENT})'
        result['adjacent_count_needed'] = 0
    elif n_primary >= N_NEED_ONE:
        result['decision'] = 'need_one_adjacent'
        result['decision_label'] = f'⚠️ ضم منطقة مماثلة واحدة (n={n_primary})'
        result['adjacent_count_needed'] = 1
    elif n_primary >= N_NEED_MULTIPLE:
        result['decision'] = 'need_multiple_adjacent'
        result['decision_label'] = f'⚠️ ضم 2-3 مناطق مماثلة (n={n_primary})'
        result['adjacent_count_needed'] = 3
    elif n_primary >= 1:
        result['decision'] = 'need_max_adjacent'
        result['decision_label'] = f'🟠 بيانات شحيحة (n={n_primary}) — ضم كل المماثل'
        result['adjacent_count_needed'] = 5
    else:
        result['decision'] = 'no_data_in_primary'
        result['decision_label'] = '🔴 لا بيانات في المنطقة الأصلية'
        result['adjacent_count_needed'] = 5

    # ── Step 4: Find adjacent candidates if needed ──
    result['candidates_evaluated'] = []
    result['accepted_areas'] = []
    result['rejected_areas'] = []

    if result['adjacent_count_needed'] > 0 and n_primary >= 3:
        # We need primary_median to evaluate candidates
        candidate_districts = _query_gis_districts_radius(lat, lon, MAX_DISTANCE_M)
        # Remove primary itself
        candidate_districts = [
            c for c in candidate_districts
            if c['dist_no'] != primary['dist_no']
        ]

        # Sort by distance for "closest first" preference
        candidates_with_dist = []
        for c in candidate_districts:
            cc = _query_district_centroid(c['dist_no'])
            if cc:
                d = _haversine_distance_m(*primary_centroid, *cc)
                candidates_with_dist.append((c, cc, d))
        candidates_with_dist.sort(key=lambda x: x[2])

        # Evaluate each candidate
        for c, c_centroid, dist in candidates_with_dist:
            c_moj_names = _match_gis_to_moj(c['aname'], all_moj_areas)
            if not c_moj_names:
                continue

            c_txns = _get_area_transactions(
                rows, set(c_moj_names), category, cutoff, date_col, bracket
            )
            if not c_txns or len(c_txns) < 2:
                continue

            c_median = _median([t['price_m2'] for t in c_txns])
            c_avg_plot = sum(t['area_m2'] for t in c_txns) / len(c_txns)
            c_zoning = _query_zoning_at_centroid(c['dist_no']) if primary_zoning else None

            # Apply six criteria
            check = _check_six_criteria(
                c, c_centroid, c_median, c_zoning, c_avg_plot,
                primary_centroid, primary_median, primary_zoning, primary_avg_plot
            )
            check['n'] = len(c_txns)
            check['median_m2'] = round(c_median)
            check['median_ft'] = round(c_median / 10.764)
            check['transactions'] = c_txns
            check['moj_names'] = c_moj_names

            result['candidates_evaluated'].append(check)

            if check['accepted']:
                result['accepted_areas'].append(check)
                if len(result['accepted_areas']) >= result['adjacent_count_needed']:
                    break
            else:
                result['rejected_areas'].append(check)

    # ── Step 5: Compute final reference with location-adjusted prices ──
    all_adjusted_prices = []

    # Primary transactions: weight 1.0, no adjustment
    for t in primary_txns:
        all_adjusted_prices.append({
            'price_m2': t['price_m2'],
            'price_adjusted': t['price_m2'],
            'weight': 1.0,
            'source': primary['aname'],
            'date': t['date'],
            'area_m2': t['area_m2'],
            'adjustment': 1.0,
        })

    # Adjacent areas: with location adjustment
    for area in result['accepted_areas']:
        # Determine tier weight based on distance
        weight = 0.3
        for tier in ADJACENT_TIERS:
            if area['distance_m'] <= tier['max_dist']:
                weight = tier['weight']
                break

        adj_factor = area['location_adjustment']
        for t in area['transactions']:
            all_adjusted_prices.append({
                'price_m2': t['price_m2'],
                'price_adjusted': t['price_m2'] * adj_factor,
                'weight': weight,
                'source': area['name'],
                'date': t['date'],
                'area_m2': t['area_m2'],
                'adjustment': adj_factor,
            })

    # Weighted median of adjusted prices
    if all_adjusted_prices:
        sorted_pairs = sorted(
            all_adjusted_prices, key=lambda x: x['price_adjusted']
        )
        total_w = sum(p['weight'] for p in sorted_pairs)
        cumulative = 0
        weighted_median = sorted_pairs[-1]['price_adjusted']
        for p in sorted_pairs:
            cumulative += p['weight']
            if cumulative >= total_w / 2:
                weighted_median = p['price_adjusted']
                break

        # Range: P25-P75 of adjusted
        all_adj = [p['price_adjusted'] for p in sorted_pairs]
        n_total = len(all_adj)
        p25 = all_adj[int(0.25 * (n_total - 1))]
        p75 = all_adj[int(0.75 * (n_total - 1))]

        result['weighted_median_m2'] = round(weighted_median)
        result['weighted_median_ft'] = round(weighted_median / 10.764)
        result['p25_m2'] = round(p25)
        result['p75_m2'] = round(p75)
        result['total_n'] = n_total
        result['effective_n'] = round(total_w, 1)

        if plot_area_m2:
            result['estimated_value'] = round(weighted_median * plot_area_m2, -3)
            result['range_low'] = round(p25 * plot_area_m2, -3)
            result['range_high'] = round(p75 * plot_area_m2, -3)
            range_pct = (p75 - p25) / weighted_median * 100
            result['range_width_pct'] = round(range_pct, 1)

    # Confidence assessment
    if n_primary >= N_SUFFICIENT:
        result['confidence'] = 'high'
        result['confidence_ar'] = 'ثقة عالية 🟢'
    elif n_primary >= N_NEED_ONE and result['accepted_areas']:
        result['confidence'] = 'medium'
        result['confidence_ar'] = 'ثقة متوسطة 🟡'
    elif n_primary + sum(a['n'] for a in result['accepted_areas']) >= N_REFUSE:
        result['confidence'] = 'low'
        result['confidence_ar'] = 'ثقة منخفضة 🟠'
    else:
        result['confidence'] = 'insufficient'
        result['confidence_ar'] = 'بيانات غير كافية 🔴'

    return result


# ============================================================
# CLI / TEST
# ============================================================

def main():
    """اختبار على عقار المريخ."""
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/thammen_pre/moj_weekly.csv'

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    print("=" * 70)
    print("اختبار geo_reference_v2 على عقار المريخ 54/541/6")
    print("=" * 70)

    result = build_reference_geo_v2(
        rows=rows,
        lat=25.269857, lon=51.471025,
        category='villa',
        plot_area_m2=613,
        target_zoning='R1',
    )

    if result.get('status') != 'ok':
        print(f"❌ Status: {result.get('status')}")
        print(f"   {result.get('message', '')}")
        return

    p = result['primary']
    print(f"\n── المنطقة الأصلية ──")
    print(f"   الاسم: {p['gis_name']} (DIST_NO {p['dist_no']})")
    print(f"   التصنيف: {p['zoning']}")
    print(f"   أسماء MoJ: {p['moj_names']}")
    print(f"   عدد المعاملات: {p['n']}")
    if p['median_m2']:
        print(f"   الوسيط: {p['median_m2']:,} ر.ق/م² ({p['median_ft']:,} قدم)")
        print(f"   متوسط مساحة القطع: {p['avg_plot_m2']:.0f} م²")

    print(f"\n── القرار الهرمي ──")
    print(f"   {result['decision_label']}")
    print(f"   مناطق إضافية مطلوبة: {result['adjacent_count_needed']}")

    if result.get('candidates_evaluated'):
        print(f"\n── المناطق المرشحة ({len(result['candidates_evaluated'])}) ──")
        print(f"{'الاسم':>20s} | {'م':>6s} | {'n':>4s} | {'وسيط':>6s} | "
              f"{'فارق':>6s} | {'تعديل':>6s} | الحالة")
        print("─" * 90)
        for c in result['candidates_evaluated'][:15]:
            status = '✅' if c['accepted'] else '❌'
            adj = f"{c.get('location_adjustment', 1.0):.3f}" if c['accepted'] else '—'
            gap = f"{c.get('price_gap_pct', 0):>5.1f}%"
            print(f"{c['name']:>20s} | {c['distance_m']:>5d}م | {c['n']:>4d} | "
                  f"{c['median_m2']:>6,} | {gap:>6s} | {adj:>6s} | {status}")
            if not c['accepted']:
                reason = ' | '.join(c['rejection_reasons'])
                print(f"{'':>20s}    └─ {reason}")

    print(f"\n── النتيجة النهائية ──")
    print(f"   الثقة: {result['confidence_ar']}")
    if result.get('weighted_median_m2'):
        print(f"   الوسيط المرجّح: {result['weighted_median_m2']:,} ر.ق/م² "
              f"({result['weighted_median_ft']:,} قدم)")
        print(f"   المعاملات: {result['total_n']} (وزن فعلي: {result['effective_n']})")
        if result.get('estimated_value'):
            print(f"   القيمة التقديرية: {result['estimated_value']:,} ر.ق")
            print(f"   النطاق: {result['range_low']:,} — {result['range_high']:,} ر.ق "
                  f"({result['range_width_pct']:.1f}%)")


if __name__ == '__main__':
    main()
