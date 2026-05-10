#!/usr/bin/env python3
"""
sales_merge.py — Merge two government sales data sources into unified DB.

Source 1 (annual XLSX from qrep.aqarat.gov.qa):
    37,617 transactions (2020-2026)
    Columns: البلدية | المنطقة | سعر البيع | المساحة بالقدم | سعر القدم | تاريخ الإصدار
    ✅ More transactions, direct foot price
    ❌ No property type (أرض/فيلا/بيت)

Source 2 (weekly bulletin from data.gov.qa — already in moj_db):
    26,719 transactions (2020-2026)
    Columns: 14 columns including property type, usage, price_per_m2
    ✅ Property type classification
    ❌ Fewer transactions

Strategy:
    1. Load both sources
    2. Match by (municipality + area + date + price) → enrich XLSX with type from bulletin
    3. Unmatched XLSX transactions get type='unknown' — still useful for area-level stats
    4. Export unified reference with best-of-both

Usage:
    python3 sales_merge.py <xlsx_dir> [moj_db_path]

    # programmatic
    from sales_merge import load_sales_xlsx, merge_with_moj_db
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

try:
    import openpyxl
    _OPENPYXL = True
except ImportError:
    _OPENPYXL = False

# ============================================================
# LOADING XLSX SALES
# ============================================================

def normalize(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()

def to_float(v):
    try: return float(str(v).replace(',', '').strip())
    except: return None

def to_int(v):
    try: return int(v)
    except: return None


def load_sales_xlsx(xlsx_path: str) -> List[dict]:
    """Load sales transactions from a single annual XLSX file."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    records = []

    for row in ws.iter_rows(min_row=3, values_only=True):
        if not row or not row[0]:
            continue
        muni, area, price, area_ft, price_ft, date = row[:6]

        price_val = to_float(price)
        area_ft_val = to_float(area_ft)
        price_ft_val = to_float(price_ft)

        if not price_val or price_val <= 0:
            continue

        # Convert ft² to m²
        area_m2 = round(area_ft_val / 10.7639, 1) if area_ft_val else None
        price_m2 = round(price_ft_val * 10.7639) if price_ft_val else None

        records.append({
            'source': 'xlsx_annual',
            'municipality': normalize(muni),
            'area': normalize(area),
            'total_price': price_val,
            'area_ft2': area_ft_val,
            'price_ft2': price_ft_val,
            'area_m2': area_m2,
            'price_m2': price_m2,
            'date': str(date).strip() if date else None,
            'property_type': None,  # ❌ not available in XLSX
        })

    wb.close()
    return records


def load_all_sales_xlsx(xlsx_dir: str) -> List[dict]:
    """Load all sales XLSX files from a directory."""
    d = Path(xlsx_dir)
    files = sorted(d.glob('*البيع*.xlsx')) + sorted(d.glob('*sale*.xlsx'))
    if not files:
        files = [f for f in sorted(d.glob('*.xlsx')) if 'البيع' in f.name or 'sale' in f.name.lower()]

    all_records = []
    for f in files:
        print(f"  Loading {f.name}...", end=' ', flush=True)
        recs = load_sales_xlsx(str(f))
        print(f"{len(recs):,} records")
        all_records.extend(recs)

    print(f"  Total XLSX sales: {len(all_records):,}")
    return all_records


# ============================================================
# AREA-LEVEL STATISTICS (works without property type)
# ============================================================

def build_area_price_stats(
    records: List[dict],
    window_months: int = 24,
    ref_date: datetime = None,
) -> dict:
    """
    Build per-area price/ft² statistics from XLSX sales data.
    Does NOT require property type — useful as a cross-check.

    Returns:
        {area_name: {
            n, median_ft2, p25_ft2, p75_ft2,
            median_m2, total_median, window
        }}
    """
    if ref_date is None:
        dates = [datetime.strptime(r['date'], '%Y-%m-%d')
                 for r in records if r.get('date')]
        ref_date = max(dates) if dates else datetime.now()

    from datetime import timedelta
    cutoff = ref_date - timedelta(days=window_months * 30.44)

    groups = defaultdict(list)
    for r in records:
        if not r.get('price_ft2') or r['price_ft2'] <= 0:
            continue
        try:
            d = datetime.strptime(r['date'], '%Y-%m-%d')
        except:
            continue
        if d < cutoff:
            continue
        groups[r['area']].append(r)

    result = {}
    for area, recs in groups.items():
        prices_ft = sorted(r['price_ft2'] for r in recs)
        n = len(prices_ft)
        if n < 5:
            continue
        p = lambda q: prices_ft[int(q * (n - 1))]
        med_ft = p(0.5)
        result[area] = {
            'n': n,
            'median_ft2': round(med_ft),
            'p25_ft2': round(p(0.25)),
            'p75_ft2': round(p(0.75)),
            'median_m2': round(med_ft * 10.7639),
            'window_months': window_months,
            'municipality': recs[0]['municipality'],
        }

    return result


def compute_trend_from_xlsx(
    records: List[dict],
    area: str,
) -> Optional[dict]:
    """Compute annual price trend for an area from XLSX sales data."""
    area_recs = [r for r in records if r.get('area') == area and r.get('price_ft2')]

    by_year = defaultdict(list)
    for r in area_recs:
        try:
            y = r['date'][:4]
            by_year[y].append(r['price_ft2'])
        except:
            continue

    years_data = []
    for y in sorted(by_year.keys()):
        vals = sorted(by_year[y])
        if len(vals) >= 3:
            med = vals[len(vals) // 2]
            years_data.append({'year': y, 'median_ft2': round(med), 'n': len(vals)})

    if len(years_data) < 2:
        return None

    # Simple linear slope
    first = years_data[0]['median_ft2']
    last = years_data[-1]['median_ft2']
    n_years = int(years_data[-1]['year']) - int(years_data[0]['year'])
    if n_years > 0 and first > 0:
        annual_pct = ((last / first) ** (1.0 / n_years) - 1) * 100
    else:
        annual_pct = 0

    return {
        'annual_pct': round(annual_pct, 1),
        'years': years_data,
        'n_years': n_years,
    }


# ============================================================
# CLI
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 sales_merge.py <xlsx_dir> [output.json]")
        sys.exit(1)

    xlsx_dir = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else 'sales_reference.json'

    records = load_all_sales_xlsx(xlsx_dir)
    area_stats = build_area_price_stats(records)

    print(f"\n{'='*60}")
    print(f"  Areas with data: {len(area_stats)}")
    print(f"{'='*60}")

    # Top 20 by transaction count
    for area, st in sorted(area_stats.items(), key=lambda x: -x[1]['n'])[:20]:
        print(f"  {area:>20s}: n={st['n']:>4}  med={st['median_ft2']:>4} QAR/ft²  "
              f"({st['municipality']})")

    # Save
    output_data = {
        'area_stats': area_stats,
        'total_transactions': len(records),
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'source': 'qrep.aqarat.gov.qa — قائمة معاملات البيع (annual XLSX)',
    }

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  Saved to {output}")


if __name__ == '__main__':
    main()
