#!/usr/bin/env python3
"""
moj_reference.py — Build MoJ-based price reference for any Qatari area.

Usage:
    python3 moj_reference.py <csv_path> <area_name_in_moj>
    python3 moj_reference.py moj_weekly.csv الخيسة
    python3 moj_reference.py moj_weekly.csv all          # all areas

CSV downloaded from:
  https://www.data.gov.qa/api/explore/v2.1/catalog/datasets/weekly-real-estates-sales-bulletin/exports/csv?lang=ar&timezone=Asia/Qatar&use_labels=true&delimiter=,
"""
import csv, json, re, sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

DATE_COL = 'تاريخ\xa0التثبيت'  # has non-breaking space
DEFAULT_WINDOW_DAYS = 730   # 24 months
FALLBACK_WINDOW_DAYS = 1095  # 36 months — used when 24m sample < MIN_N
MIN_N = 20
SIZE_BRACKETS = [(0,400),(400,600),(600,900),(900,1500),(1500,99999)]

def normalize(s): return re.sub(r'\s+', ' ', s or '').strip()
def to_float(s):
    try: return float(str(s or '').replace(',', '').strip())
    except: return None
def parse_date(s):
    try: return datetime.strptime(s, '%Y-%m-%d')
    except: return None

def time_weight(txn_date, ref_date):
    """Weight a transaction by recency. Recent = higher weight."""
    if not txn_date or not ref_date:
        return 0.5
    months = (ref_date - txn_date).days / 30.44
    if months <= 3:  return 1.00
    if months <= 6:  return 0.90
    if months <= 12: return 0.75
    if months <= 18: return 0.60
    if months <= 24: return 0.45
    return 0.30

def categorize(r):
    t = normalize(r['نوع العقار'])
    if t == 'أرض فضاء': return 'land'
    if t.startswith(('فيلا','فيلتان')) or t.startswith('بيت'): return 'villa'
    if t == 'قصر': return 'palace'
    if t in ('مسكن', 'مسكن شعبي'): return 'dwelling'
    return 'other'

def quartile_stats(values):
    values = sorted(v for v in values if v is not None and v > 0)
    if not values: return None
    n = len(values); p = lambda q: values[int(q * (n-1))]
    return {'n': n, 'min': round(values[0]),
            'p25': round(p(0.25)), 'median': round(p(0.50)),
            'p75': round(p(0.75)), 'max': round(values[-1])}

def build_reference(rows, area, max_d, return_transactions=False):
    """Build a single area's reference. Auto-fallback to 36m if sample too small."""
    area_norm = normalize(area)
    area_rows = [r for r in rows if normalize(r.get('اسم المنطقة', '')) == area_norm]
    if not area_rows:
        return {'area': area, 'error': 'area_not_found_in_moj'}

    cutoff_24 = max_d - timedelta(days=DEFAULT_WINDOW_DAYS)
    cutoff_36 = max_d - timedelta(days=FALLBACK_WINDOW_DAYS)

    out = {'area': area, 'total_alltime': len(area_rows), 'categories': {}}
    munis = Counter(normalize(r.get('اسم البلدية', '')) for r in area_rows)
    out['municipality'] = munis.most_common(1)[0][0]

    for cat in ('land', 'villa'):
        in24 = [r for r in area_rows
                if (d := parse_date(r[DATE_COL])) and d >= cutoff_24
                and categorize(r) == cat]
        in36 = [r for r in area_rows
                if (d := parse_date(r[DATE_COL])) and d >= cutoff_36
                and categorize(r) == cat]
        # Pick window
        use, window = (in24, 24) if len(in24) >= MIN_N else (in36, 36)
        if not use:
            out['categories'][cat] = {'n': 0, 'reliable': False}
            continue

        cat_data = {
            'n': len(use), 'window_months': window,
            'reliable': len(use) >= MIN_N,
            'price_per_m2': quartile_stats([to_float(r['سعر المتر المربع']) for r in use]),
            'price_per_ft2': quartile_stats([to_float(r['سعر القدم المربع']) for r in use]),
            'plot_area_m2':  quartile_stats([to_float(r['المساحة بالمتر المربع']) for r in use]),
            'total_price':   quartile_stats([to_float(r['قيمة العقار']) for r in use]),
            'size_brackets': {}
        }
        for lo, hi in SIZE_BRACKETS:
            sub = [r for r in use
                   if (a := to_float(r['المساحة بالمتر المربع'])) and lo <= a < hi]
            if not sub: continue
            ppm2 = quartile_stats([to_float(r['سعر المتر المربع']) for r in sub])
            tot  = quartile_stats([to_float(r['قيمة العقار']) for r in sub])
            bracket_data = {
                'n': len(sub),
                'price_per_m2_p25':    ppm2.get('p25')    if ppm2 else None,
                'price_per_m2_median': ppm2.get('median') if ppm2 else None,
                'price_per_m2_p75':    ppm2.get('p75')    if ppm2 else None,
                'total_price_p25':     tot.get('p25')     if tot  else None,
                'total_price_median':  tot.get('median')  if tot  else None,
                'total_price_p75':     tot.get('p75')     if tot  else None,
                'reliable': len(sub) >= 10,
            }
            if return_transactions:
                bracket_data['transactions'] = [
                    {
                        'date': r.get(DATE_COL, ''),
                        'area_m2': to_float(r['المساحة بالمتر المربع']),
                        'total_price': to_float(r['قيمة العقار']),
                        'price_per_m2': to_float(r['سعر المتر المربع']),
                        'price_per_ft2': to_float(r['سعر القدم المربع']),
                        'type_ar': normalize(r.get('نوع العقار', '')),
                    }
                    for r in sorted(sub, key=lambda x: x.get(DATE_COL, ''), reverse=True)
                ]
            cat_data['size_brackets'][f'{lo}-{hi}'] = bracket_data
        out['categories'][cat] = cat_data
    return out


def compute_trend(rows, area, max_d, category='all'):
    """
    Compute annual price-per-foot trend for an area.

    Returns:
        {
          'area': str,
          'category': str,            # 'land' | 'villa' | 'all'
          'years': [
            {'year': '2020', 'n': 14, 'median_ft': 425, 'median_m2': 4575},
            ...
          ],
          'slope_annual_pct': float,   # linear regression slope as annual %
          'label': str,               # 'ارتفاع' | 'استقرار' | 'انخفاض'
          'latest_vs_peak_pct': float, # how far current is from peak
        }
    """
    area_norm = normalize(area)
    area_rows = [r for r in rows if normalize(r.get('اسم المنطقة', '')) == area_norm]
    if not area_rows:
        return None

    # Filter by category
    if category == 'land':
        filtered = [r for r in area_rows if categorize(r) == 'land']
    elif category == 'villa':
        filtered = [r for r in area_rows if categorize(r) in ('villa', 'dwelling')]
    else:
        filtered = area_rows

    # Group by year
    from collections import defaultdict
    yearly = defaultdict(list)
    for r in filtered:
        d = parse_date(r.get(DATE_COL, ''))
        if not d:
            continue
        pf = to_float(r.get('سعر القدم المربع') or r.get('سعر\xa0القدم\xa0المربع'))
        pm = to_float(r.get('سعر المتر المربع') or r.get('سعر\xa0المتر\xa0المربع'))
        if pf and pf > 0:
            yearly[str(d.year)].append((pf, pm or pf * 10.764))

    if not yearly:
        return None

    years_data = []
    for year in sorted(yearly.keys()):
        vals = yearly[year]
        ft_vals = sorted(v[0] for v in vals)
        m2_vals = sorted(v[1] for v in vals)
        n = len(ft_vals)
        med_ft = ft_vals[n // 2]
        med_m2 = m2_vals[n // 2]
        years_data.append({
            'year': year,
            'n': n,
            'median_ft': round(med_ft),
            'median_m2': round(med_m2),
        })

    # Linear regression on median_ft over years
    if len(years_data) >= 2:
        xs = list(range(len(years_data)))
        ys = [y['median_ft'] for y in years_data]
        n = len(xs)
        x_mean = sum(xs) / n
        y_mean = sum(ys) / n
        num = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
        den = sum((xs[i] - x_mean) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0
        slope_pct = slope / y_mean if y_mean != 0 else 0
    else:
        slope_pct = 0

    # Classification
    if slope_pct > 0.03:
        label = 'ارتفاع'
    elif slope_pct < -0.03:
        label = 'انخفاض'
    else:
        label = 'استقرار'

    # Latest vs peak
    peak = max(y['median_ft'] for y in years_data)
    latest = years_data[-1]['median_ft']
    latest_vs_peak = (latest - peak) / peak if peak > 0 else 0

    return {
        'area': area,
        'category': category,
        'years': years_data,
        'slope_annual_pct': round(slope_pct, 4),
        'label': label,
        'latest_vs_peak_pct': round(latest_vs_peak, 3),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 moj_reference.py <csv_path> [area|all]")
        sys.exit(1)
    csv_path = Path(sys.argv[1])
    target = sys.argv[2] if len(sys.argv) > 2 else 'الخيسة'

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    dates = [d for d in (parse_date(r[DATE_COL]) for r in rows) if d]
    max_d = max(dates)
    min_d = min(dates)

    meta = {
        'source': 'data.gov.qa weekly-real-estates-sales-bulletin',
        'csv_total_rows': len(rows),
        'date_range': f'{min_d.date()} → {max_d.date()}',
        'reference_window_default': '24 months',
        'fallback_window': '36 months when 24m sample < 20',
    }

    if target == 'all':
        # Top 30 areas by 24m volume
        cutoff = max_d - timedelta(days=730)
        recent = [r for r in rows if (d := parse_date(r[DATE_COL])) and d >= cutoff]
        top = Counter(normalize(r.get('اسم المنطقة', '')) for r in recent).most_common(30)
        result = {'meta': meta, 'top_areas_24m': dict(top), 'references': {}}
        for area, _ in top:
            result['references'][area] = build_reference(rows, area, max_d)
    else:
        result = {'meta': meta, 'reference': build_reference(rows, target, max_d)}

    out_path = csv_path.parent / f'reference_{target.replace(" ","_")}.json'
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nSaved → {out_path}", file=sys.stderr)

if __name__ == '__main__':
    main()
