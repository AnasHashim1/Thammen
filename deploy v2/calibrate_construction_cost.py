#!/usr/bin/env python3
"""
calibrate_construction_cost.py — Reverse-engineer construction cost/m² from MoJ data.

Logic:
    For each villa transaction in MoJ:
        land_value = plot_area × MoJ_land_median_per_m2 (same area)
        building_value = villa_price - land_value
        implicit_cost_per_plot_m2 = building_value / plot_area

    This gives "how much the building adds per m² of plot" — which is
    directly comparable across properties WITHOUT needing to know BUA.

    When BUA is known, we can also estimate cost_per_bua_m2 using
    a configurable BUA/plot ratio assumption.

Output:
    construction_costs.json — per-municipality calibrated costs

Usage:
    python3 calibrate_construction_cost.py moj_weekly.csv
    python3 calibrate_construction_cost.py moj_weekly.db    # from SQLite
"""

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def normalize(s): return re.sub(r'\s+', ' ', s or '').strip()
def to_float(s):
    try: return float(str(s or '').replace(',', '').strip())
    except: return None


DATE_COL = 'تاريخ\xa0التثبيت'
WINDOW_DAYS = 1095  # 3 years for calibration (more data = better)

# Minimum thresholds
MIN_BUILDING_VALUE_RATIO = 0.10  # building must be ≥10% of total price
MIN_TRANSACTIONS_PER_MUNICIPALITY = 5
BUA_PLOT_RATIO_ASSUMPTION = 0.60  # for estimating cost_per_bua_m2


def categorize(type_str):
    t = normalize(type_str)
    if t == 'أرض فضاء': return 'land'
    if t.startswith(('فيلا', 'فيلتان', 'فيلتين')) or t.startswith('بيت'): return 'villa'
    return 'other'


def median_of(values):
    s = sorted(v for v in values if v is not None)
    if not s: return None
    return s[len(s) // 2]


def quartiles(values):
    s = sorted(v for v in values if v is not None)
    if not s: return None
    n = len(s)
    p = lambda q: s[int(q * (n-1))]
    return {
        'n': n,
        'p25': round(p(0.25)),
        'median': round(p(0.50)),
        'p75': round(p(0.75)),
        'min': round(s[0]),
        'max': round(s[-1]),
    }


def calibrate_from_csv(csv_path: Path, window_days: int = WINDOW_DAYS) -> dict:
    """Run calibration from CSV file."""
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    # Normalize all text fields
    for r in rows:
        for k in list(r.keys()):
            if isinstance(r[k], str):
                nk = normalize(k)
                r[nk] = normalize(r[k])

    # Find date range
    dates = []
    for r in rows:
        try:
            d = datetime.strptime(r.get(normalize(DATE_COL), r.get(DATE_COL, '')), '%Y-%m-%d')
            dates.append(d)
        except: pass
    if not dates:
        return {'error': 'No valid dates found'}

    max_d = max(dates)
    cutoff = max_d - timedelta(days=window_days)

    # Step 1: Compute land price medians per area
    land_by_area = defaultdict(list)
    for r in rows:
        try:
            d = datetime.strptime(r.get(normalize(DATE_COL), r.get(DATE_COL, '')), '%Y-%m-%d')
        except: continue
        if d < cutoff: continue

        ptype = normalize(r.get('نوع العقار', r.get(normalize('نوع العقار'), '')))
        if categorize(ptype) != 'land': continue

        area_name = normalize(r.get('اسم المنطقة', r.get(normalize('اسم المنطقة'), '')))
        pm2 = to_float(r.get('سعر المتر المربع', r.get(normalize('سعر المتر المربع'), '')))
        if area_name and pm2 and pm2 > 0:
            muni = normalize(r.get('اسم البلدية', r.get(normalize('اسم البلدية'), '')))
            land_by_area[area_name].append((pm2, muni))

    area_land_median = {}
    area_municipality = {}
    for area, vals in land_by_area.items():
        prices = [v[0] for v in vals]
        area_land_median[area] = median_of(prices)
        # Most common municipality
        munis = [v[1] for v in vals]
        area_municipality[area] = max(set(munis), key=munis.count)

    # Step 2: For each villa transaction, compute implicit building cost
    building_costs_by_muni = defaultdict(list)
    excluded = {'negative_building': 0, 'low_ratio': 0, 'no_land_ref': 0, 'no_area': 0}

    for r in rows:
        try:
            d = datetime.strptime(r.get(normalize(DATE_COL), r.get(DATE_COL, '')), '%Y-%m-%d')
        except: continue
        if d < cutoff: continue

        ptype = normalize(r.get('نوع العقار', r.get(normalize('نوع العقار'), '')))
        if categorize(ptype) != 'villa': continue

        area_name = normalize(r.get('اسم المنطقة', r.get(normalize('اسم المنطقة'), '')))
        total_price = to_float(r.get('قيمة العقار', r.get(normalize('قيمة العقار'), '')))
        plot_m2 = to_float(r.get('المساحة بالمتر المربع', r.get(normalize('المساحة بالمتر المربع'), '')))
        muni = normalize(r.get('اسم البلدية', r.get(normalize('اسم البلدية'), '')))

        if not area_name or not total_price or not plot_m2 or plot_m2 <= 0:
            excluded['no_area'] += 1
            continue

        land_pm2 = area_land_median.get(area_name)
        if land_pm2 is None:
            excluded['no_land_ref'] += 1
            continue

        land_value = plot_m2 * land_pm2
        building_value = total_price - land_value

        if building_value <= 0:
            excluded['negative_building'] += 1
            continue

        ratio = building_value / total_price
        if ratio < MIN_BUILDING_VALUE_RATIO:
            excluded['low_ratio'] += 1
            continue

        # Implicit cost per plot m²
        cost_per_plot_m2 = building_value / plot_m2
        # Estimated cost per BUA m² (assuming BUA = plot × ratio)
        est_bua = plot_m2 * BUA_PLOT_RATIO_ASSUMPTION
        cost_per_bua_m2 = building_value / est_bua

        building_costs_by_muni[muni].append({
            'cost_per_plot_m2': cost_per_plot_m2,
            'cost_per_bua_m2': cost_per_bua_m2,
            'building_value': building_value,
            'total_price': total_price,
            'plot_m2': plot_m2,
            'area': area_name,
        })

    # Step 3: Aggregate by municipality
    result = {
        'calibration_date': datetime.now().strftime('%Y-%m-%d'),
        'window_months': window_days // 30,
        'date_range': f'{cutoff.date()} → {max_d.date()}',
        'bua_plot_ratio_assumption': BUA_PLOT_RATIO_ASSUMPTION,
        'exclusions': excluded,
        'municipalities': {},
    }

    total_used = 0
    for muni, costs in sorted(building_costs_by_muni.items(),
                               key=lambda x: -len(x[1])):
        if len(costs) < MIN_TRANSACTIONS_PER_MUNICIPALITY:
            continue

        plot_costs = [c['cost_per_plot_m2'] for c in costs]
        bua_costs = [c['cost_per_bua_m2'] for c in costs]

        entry = {
            'cost_per_plot_m2': quartiles(plot_costs),
            'cost_per_bua_m2_estimated': quartiles(bua_costs),
            'n_transactions': len(costs),
        }
        result['municipalities'][muni] = entry
        total_used += len(costs)

    result['total_transactions_used'] = total_used

    return result


def calibrate_from_db(db_path: Path) -> dict:
    """Run calibration from SQLite database."""
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    cutoff = (datetime.now() - timedelta(days=WINDOW_DAYS)).strftime('%Y-%m-%d')

    # Step 1: Land medians per area
    land_rows = conn.execute("""
        SELECT area, municipality, price_m2
        FROM transactions
        WHERE category='land' AND date>=? AND price_m2 > 0
    """, (cutoff,)).fetchall()

    area_land = defaultdict(list)
    for r in land_rows:
        area_land[r['area']].append(r['price_m2'])

    area_land_median = {a: median_of(v) for a, v in area_land.items()}

    # Step 2: Villa transactions
    villa_rows = conn.execute("""
        SELECT area, municipality, total_price, area_m2
        FROM transactions
        WHERE category='villa' AND date>=? AND total_price > 0 AND area_m2 > 0
    """, (cutoff,)).fetchall()

    building_costs_by_muni = defaultdict(list)
    excluded = {'negative_building': 0, 'low_ratio': 0, 'no_land_ref': 0}

    for r in villa_rows:
        land_pm2 = area_land_median.get(r['area'])
        if land_pm2 is None:
            excluded['no_land_ref'] += 1
            continue

        land_value = r['area_m2'] * land_pm2
        building_value = r['total_price'] - land_value

        if building_value <= 0:
            excluded['negative_building'] += 1
            continue
        if building_value / r['total_price'] < MIN_BUILDING_VALUE_RATIO:
            excluded['low_ratio'] += 1
            continue

        cost_per_plot_m2 = building_value / r['area_m2']
        cost_per_bua_m2 = building_value / (r['area_m2'] * BUA_PLOT_RATIO_ASSUMPTION)

        building_costs_by_muni[r['municipality']].append({
            'cost_per_plot_m2': cost_per_plot_m2,
            'cost_per_bua_m2': cost_per_bua_m2,
        })

    conn.close()

    # Step 3: Aggregate
    result = {
        'calibration_date': datetime.now().strftime('%Y-%m-%d'),
        'window_months': WINDOW_DAYS // 30,
        'bua_plot_ratio_assumption': BUA_PLOT_RATIO_ASSUMPTION,
        'exclusions': excluded,
        'municipalities': {},
    }

    total_used = 0
    for muni, costs in sorted(building_costs_by_muni.items(), key=lambda x: -len(x[1])):
        if len(costs) < MIN_TRANSACTIONS_PER_MUNICIPALITY:
            continue
        plot_costs = [c['cost_per_plot_m2'] for c in costs]
        bua_costs = [c['cost_per_bua_m2'] for c in costs]
        result['municipalities'][muni] = {
            'cost_per_plot_m2': quartiles(plot_costs),
            'cost_per_bua_m2_estimated': quartiles(bua_costs),
            'n_transactions': len(costs),
        }
        total_used += len(costs)

    result['total_transactions_used'] = total_used
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 calibrate_construction_cost.py <csv_or_db_path>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if path.suffix == '.db':
        result = calibrate_from_db(path)
    else:
        result = calibrate_from_csv(path)

    out_path = path.parent / 'construction_costs.json'
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n✅ Saved → {out_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
