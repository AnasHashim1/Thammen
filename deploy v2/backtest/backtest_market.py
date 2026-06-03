"""
Sprint 2.13 — backtest_market.py

Measures the asking premium of current arady land listings vs MoJ
registered transactions, bucketed against the bands established in
EMPIRICAL_FINDINGS.md (2026-05).

This tool does NOT call the Thammen API. It reads:
  - arady_lands_*.csv  (latest file in current dir from seed_from_arady.py)
  - moj_weekly.csv     (the MoJ transactions file already in deploy v2)

Why this design (after Sprint 2.12 pivot):
  Anas does not have confirmed sale prices. Villa asking prices are
  contaminated by non-economic premiums (proximity to family, sentimental
  value) — EMPIRICAL_FINDINGS quantified this at +70% asking premium for
  villas vs +13.6% for clean land. Land is fungible — no one pays a premium
  to own a specific vacant plot. So land listings ARE a valid truth source
  with a documented, narrow premium band.

This complies with EMPIRICAL_FINDINGS Rule E3: listings remain sentiment
data. We do NOT feed them into the engine. We MEASURE the engine's
foundations (MoJ medians) against the market.

What it does:
  For each arady land listing:
    1. Match its city to a MoJ district (with normalization)
    2. Compute MoJ median price/m² for the matched district + size bracket
       over the last 24 months
    3. Compute asking premium = (arady_per_m² / MoJ_median) − 1
    4. Bucket against EMPIRICAL_FINDINGS bands:
         premium  -∞ to  0%  → 🟦 below MoJ        (motivated seller? declining area?)
         premium    0% to 20% → ✅ normal           (within global asking-premium norm)
         premium   20% to 25% → ⚠️  investigate    (Rule E5 amber zone)
         premium    >25%      → 🔴 red flag        (stock mismatch / new-build / outlier)

Outputs:
  reports/market_YYYYMMDD_HHMMSS.md   (human-readable report)
  reports/market_YYYYMMDD_HHMMSS.csv  (raw per-listing data)

Usage (Windows):
    cd /d "C:\\Thammen\\deploy v2\\backtest"
    python backtest_market.py

Optional CLI:
    python backtest_market.py --moj ..\\moj_weekly.csv  --arady arady_lands_2026-05-13.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


# ─── Configuration ────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.resolve()
DEFAULT_MOJ_CSV = ROOT.parent / 'moj_weekly.csv'   # deploy v2 root
REPORTS_DIR = ROOT / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)

WINDOW_MONTHS = 24
WINDOW_DAYS = WINDOW_MONTHS * 30

LAND_TYPE_VALUES = {'أرض فضاء', 'ارض فضاء'}   # nw_l_qr — variations seen in MoJ

# Section 3 (Project Instructions) sample-size discipline. Hotfix 2026-05-13:
# the first run of backtest_market.py computed medians from n=1 — clear
# violation. Now enforced:
#   n ≥ MIN_MOJ_N_RELIABLE → 'reliable'
#   MIN_MOJ_N ≤ n < MIN_MOJ_N_INDICATIVE → 'indicative'  (premium computed, flagged)
#   n < MIN_MOJ_N → 'insufficient'  (no median produced)
MIN_MOJ_N = 5                # below this: do not produce a median
MIN_MOJ_N_INDICATIVE = 10    # below this: indicative tier
MIN_MOJ_N_RELIABLE = 20      # at/above this: reliable tier

# Size brackets (Section 3 of Project Instructions)
BRACKETS = [(0, 400), (400, 600), (600, 900), (900, 1500), (1500, float('inf'))]


def bracket_label(area):
    for lo, hi in BRACKETS:
        if lo <= area < hi:
            return f'{lo}-{int(hi) if hi != float("inf") else "+"}'
    return 'unknown'


def bracket_bounds(area):
    for lo, hi in BRACKETS:
        if lo <= area < hi:
            return lo, hi
    return None, None


# District name normalization — applies to BOTH arady city_ar AND MoJ sm_lmntq
# (Section 7 of Project Instructions plus EMPIRICAL_FINDINGS Section 5).
# Both sides get normalized through this map, then matched directly.
DISTRICT_NORMALIZE = {
    # arady_or_moj_raw : canonical
    'الدحيل': 'دحيل',
    'دحيل': 'دحيل',
    'أبو هامور': 'بو هامور',
    'بو هامور': 'بو هامور',
    'ابو هامور': 'بو هامور',
    'أم قرن': 'ام قرن',
    'ام قرن': 'ام قرن',
    'الغرافة': 'الغرافة',
    'غرافة الريان': 'الغرافة',
    'غرافة\xa0الريان': 'الغرافة',
    'عين\xa0خالد': 'عين خالد',
    'عين خالد': 'عين خالد',
    # No-op self-map entries make the table easier to scan.
}


def normalize_district(s):
    """Apply NBSP cleanup + the normalization map. Returns canonical form."""
    if not s:
        return None
    s2 = re.sub(r'\s+', ' ', s).strip()
    return DISTRICT_NORMALIZE.get(s2, s2)


# ─── MoJ ingestion ────────────────────────────────────────────────────────
def parse_date(s):
    """Try a few common MoJ formats — registration_date may be ISO or local."""
    if not s:
        return None
    s = s.strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def parse_float(s):
    try:
        return float(s.replace(',', '')) if s else None
    except (ValueError, AttributeError):
        return None


def load_moj_land_records(csv_path):
    """Yield normalized records for raw-land transactions only."""
    today = date.today()
    cutoff = today - timedelta(days=WINDOW_DAYS)

    # Auto-detect encoding (UTF-8 with optional BOM, fallback windows-1256)
    encodings = ['utf-8-sig', 'utf-8', 'windows-1256']
    fh = None
    used_enc = None
    for enc in encodings:
        try:
            fh = open(csv_path, encoding=enc)
            fh.readline()
            fh.seek(0)
            used_enc = enc
            break
        except (UnicodeDecodeError, LookupError):
            fh and fh.close()
            fh = None
    if fh is None:
        raise RuntimeError(f'Could not decode {csv_path} with any common encoding')

    reader = csv.reader(fh)
    raw_headers = next(reader)

    # NBSP-normalize headers (column "تاريخ التثبيت" contains NBSP)
    headers = [re.sub(r'\s+', ' ', h).strip() for h in raw_headers]

    def col(*candidates):
        """Return the first header that matches any of the candidates."""
        for c in candidates:
            for i, h in enumerate(headers):
                if c in h:
                    return i
        return None

    # Locate columns. Arabic labels (use_labels=true in data.gov.qa export)
    # are the production schema; we also accept ID names (use_labels=false)
    # as fallback for ad-hoc downloads. Candidates use substring matching,
    # so be specific enough to discriminate:
    #   'سعر المتر' matches 'سعر المتر المربع' but NOT 'سعر القدم المربع'
    #   'قيمة العقار' matches 'قيمة العقار' but NOT 'قيمة الحصص المباعة'
    i_date     = col('تاريخ التثبيت', 'registration_date')
    i_district = col('اسم المنطقة', 'sm_lmntq')
    i_district_en = col('district_name', 'municipality_name')
    i_type     = col('نوع العقار', 'nw_l_qr', 'property_type_ar')
    i_area     = col('المساحة بالمتر', 'area_square_meters')
    i_price_m2 = col('سعر المتر', 'price_per_square_meter')   # NOT 'السعر بالمتر' — wrong word
    i_value    = col('قيمة العقار', 'property_value')

    if None in (i_date, i_district, i_type, i_area, i_price_m2):
        raise RuntimeError(
            f'MoJ CSV missing required columns. Found headers: {headers[:20]}'
        )

    out, total, kept, by_year = [], 0, 0, defaultdict(int)
    for row in reader:
        if not row or len(row) <= max(filter(None, [i_date, i_district, i_type,
                                                     i_area, i_price_m2])):
            continue
        total += 1
        type_val = re.sub(r'\s+', ' ', row[i_type]).strip()
        if type_val not in LAND_TYPE_VALUES:
            continue
        d = parse_date(row[i_date])
        if not d or d < cutoff:
            continue
        area = parse_float(row[i_area])
        price_m2 = parse_float(row[i_price_m2])
        if not area or not price_m2 or area <= 0 or price_m2 <= 0:
            continue
        district_raw = row[i_district]
        out.append({
            'date': d,
            'district_raw': district_raw,
            'district_norm': normalize_district(district_raw),
            'district_en': row[i_district_en] if i_district_en else None,
            'area_m2': area,
            'price_per_m2_qar': price_m2,
            'value_qar': parse_float(row[i_value]) if i_value else None,
        })
        kept += 1
        by_year[d.year] += 1

    print(f'MoJ load: read {total} rows, kept {kept} land records '
          f'in the last {WINDOW_MONTHS} months (encoding={used_enc})')
    print(f'  by year: {dict(by_year)}')
    return out


def build_moj_index(records):
    """Group records by (district_norm, bracket_label)."""
    idx = defaultdict(list)
    for r in records:
        idx[(r['district_norm'], bracket_label(r['area_m2']))].append(
            r['price_per_m2_qar']
        )
    return idx


def moj_median(index, district_norm, area):
    """Return (median, n, reliability) for the given district + bracket.

    Per Section 3 of Project Instructions:
      n ≥ 20 → 'reliable'
      n ∈ [10, 19] → 'indicative'
      n ∈ [5, 9]  → 'indicative' (context only — median is informational, not authoritative)
      n < 5       → 'insufficient' — NO MEDIAN PRODUCED, returns (None, n, ...)
    """
    key = (district_norm, bracket_label(area))
    samples = index.get(key, [])
    n = len(samples)
    if n < MIN_MOJ_N:
        return None, n, 'insufficient'
    median = round(statistics.median(samples), 0)
    if n >= MIN_MOJ_N_RELIABLE:
        tier = 'reliable'
    else:
        tier = 'indicative'
    return median, n, tier


# ─── arady ingestion ──────────────────────────────────────────────────────
def find_latest_arady_csv():
    candidates = sorted(ROOT.glob('arady_lands_*.csv'),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def load_arady(csv_path):
    """Load arady listings with two filters applied:

    1. Non-residential land (category_type != 'residential_land') is DROPPED
       and counted separately. The previous version of this function silently
       included commercial land — see the فريج كليب case in the 2026-05-13
       first run that produced a meaningless +54% premium vs residential MoJ.

    2. Duplicates on (district_norm, size_m2, asking_per_m2) — same plot
       posted twice by different brokers, or the same broker re-posting.
       First occurrence kept; rest dropped and counted.
    """
    raw = []
    skipped_nonres = 0
    skipped_invalid = 0
    with open(csv_path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try:
                size = float(r.get('size_m2') or 0)
                ppm = float(r.get('price_per_m2_qar') or 0)
            except ValueError:
                skipped_invalid += 1
                continue
            if size <= 0 or ppm <= 0:
                skipped_invalid += 1
                continue
            # Hotfix 1: actually drop non-residential land (previous version
            # only commented "Note but skip" without skipping).
            cat = (r.get('category_type') or '').strip()
            if cat and cat != 'residential_land':
                skipped_nonres += 1
                continue
            r['size_m2_f'] = size
            r['asking_per_m2'] = ppm
            r['district_norm'] = normalize_district(r.get('city_ar'))
            raw.append(r)

    # Hotfix 3: dedup. Two listings with identical (district, size, price)
    # are almost certainly the same plot posted twice — keep one.
    rows = []
    seen = set()
    skipped_dup = 0
    for r in raw:
        key = (r['district_norm'], int(round(r['size_m2_f'])),
               int(round(r['asking_per_m2'])))
        if key in seen:
            skipped_dup += 1
            continue
        seen.add(key)
        rows.append(r)

    print(f'arady load: {len(rows)} unique residential land listings')
    if skipped_nonres or skipped_dup or skipped_invalid:
        print(f'  skipped: {skipped_nonres} non-residential, '
              f'{skipped_dup} duplicates, {skipped_invalid} invalid rows')
    return rows


# ─── Comparison + bucketing ───────────────────────────────────────────────
def bucket(premium_pct):
    """EMPIRICAL_FINDINGS-aligned bands."""
    if premium_pct is None:
        return ('insufficient_moj', '⚪')
    if premium_pct < 0:
        return ('below_moj', '🟦')
    if premium_pct <= 20:
        return ('normal', '✅')
    if premium_pct <= 25:
        return ('investigate', '⚠️')
    return ('red_flag', '🔴')


def compare(arady_rows, moj_index):
    out = []
    for r in arady_rows:
        median, n, reliability = moj_median(moj_index, r['district_norm'],
                                            r['size_m2_f'])
        if median:
            premium = (r['asking_per_m2'] / median - 1) * 100
        else:
            premium = None
        cat, emoji = bucket(premium)
        out.append({
            **r,
            'moj_median_per_m2': median,
            'moj_n': n,
            'moj_reliability': reliability,
            'bracket': bracket_label(r['size_m2_f']),
            'premium_pct': round(premium, 1) if premium is not None else None,
            'bucket': cat,
            'emoji': emoji,
        })
    return out


# ─── Report rendering ─────────────────────────────────────────────────────
def render(results, agg, ts):
    L = []
    L += [
        f'# Thammen Market Report — {ts}',
        '',
        f'Compares **{len(results)} current arady.qa land listings** against MoJ ',
        f'registered land transactions in the last {WINDOW_MONTHS} months.',
        '',
        '**Methodology source:** EMPIRICAL_FINDINGS (2026-05). Bands derived ',
        'from paired audit of 5 areas × 4 brackets, n=149+ MoJ + n=18 asking.',
        '',
        '> Rule E3 reminder: this report SHOWS market sentiment vs MoJ. It ',
        '> does NOT feed listings into any valuation. Asking premium is a ',
        '> diagnostic, never an input.',
        '',
        '## Summary',
        '',
        '| Bucket | Band | Count | Median premium |',
        '|---|---|---|---|',
    ]
    for b in ('normal', 'investigate', 'red_flag', 'below_moj', 'insufficient_moj'):
        bs = agg.get(b, {})
        L.append(
            f'| {bs.get("emoji","")} {b.replace("_"," ")} | '
            f'{bs.get("band","—")} | {bs.get("count",0)} | '
            f'{bs.get("median_premium","—")} |'
        )
    L += ['']

    if agg.get('overall_median') is not None:
        L += [
            f'**Overall median asking premium:** {agg["overall_median"]:.1f}% ',
            f'(EMPIRICAL_FINDINGS baseline: +13.6% global land norm)',
            '',
        ]

    # Stratification by district
    by_district = defaultdict(list)
    for r in results:
        by_district[r['district_norm']].append(r)
    L += ['## By district', '',
          '| District | N | Premium median | EMPIRICAL_FINDINGS reference |',
          '|---|---|---|---|']
    EMP_REF = {
        'الغرافة': '+4.5% (n=44 reliable)',
        'الخيسة': '+19.7% (n=6)',
        'دحيل': '+4.6% (n=9)',
        'عين خالد': 'no asking sample',
    }
    for d, rows in sorted(by_district.items(),
                          key=lambda x: -len(x[1])):
        prems = [r['premium_pct'] for r in rows if r['premium_pct'] is not None]
        med = (f'{statistics.median(prems):.1f}%' if prems else '—')
        L.append(f'| {d} | {len(rows)} | {med} | '
                 f'{EMP_REF.get(d, "(not in audit)")} |')
    L += ['']

    # Red-flag detail
    red = [r for r in results if r['bucket'] == 'red_flag']
    if red:
        L += ['## 🔴 Red flags (premium > 25%)', '',
              'Per Rule E5, investigate before treating as comparable. Common ',
              'causes: new-build pricing, corner/zaweya plot, off-plan, or ',
              'a small-n MoJ window giving a noisy median.',
              '',
              '| Listing | District | Size | Asking/m² | MoJ med/m² (n) | Premium |',
              '|---|---|---|---|---|---|']
        for r in red:
            L.append(
                f'| [{r["property_id"]}]({r["source_url"]}) | '
                f'{r["district_norm"]} | {int(r["size_m2_f"])} | '
                f'{int(r["asking_per_m2"]):,} | '
                f'{int(r["moj_median_per_m2"]):,} (n={r["moj_n"]}) | '
                f'**+{r["premium_pct"]:.1f}%** |'
            )
        L += ['']

    # Below-MoJ detail
    below = [r for r in results if r['bucket'] == 'below_moj']
    if below:
        L += ['## 🟦 Below-MoJ listings (premium < 0%)', '',
              'Asking below registered-transaction median — unusual. Could be ',
              'motivated seller, declining sub-area, mislabeled district, or ',
              'small-n MoJ noise. Worth a manual look.',
              '',
              '| Listing | District | Size | Asking/m² | MoJ med/m² (n) | Premium |',
              '|---|---|---|---|---|---|']
        for r in below:
            L.append(
                f'| [{r["property_id"]}]({r["source_url"]}) | '
                f'{r["district_norm"]} | {int(r["size_m2_f"])} | '
                f'{int(r["asking_per_m2"]):,} | '
                f'{int(r["moj_median_per_m2"]):,} (n={r["moj_n"]}) | '
                f'{r["premium_pct"]:.1f}% |'
            )
        L += ['']

    # Insufficient MoJ
    ins = [r for r in results if r['bucket'] == 'insufficient_moj']
    if ins:
        L += ['## ⚪ Insufficient MoJ data', '',
              f'{len(ins)} listings could not be measured (no matching MoJ ',
              'records for that district + bracket in the 24-month window). ',
              'These reveal coverage gaps in the data Thammen relies on.',
              '',
              '| Listing | District (arady → MoJ) | Bracket | Asking/m² |',
              '|---|---|---|---|']
        for r in ins:
            L.append(
                f'| [{r["property_id"]}]({r["source_url"]}) | '
                f'{r.get("city_ar","?")} → {r["district_norm"]} | '
                f'{r["bracket"]} | {int(r["asking_per_m2"]):,} |'
            )
        L += ['']

    # Full per-row detail
    L += ['## Per-listing detail', '',
          '| # | Listing | District | Size | Bracket | Asking/m² | MoJ med (n, tier) | Premium | Bucket |',
          '|---|---|---|---|---|---|---|---|---|']
    for i, r in enumerate(results, 1):
        prem = (f'{r["premium_pct"]:+.1f}%' if r['premium_pct'] is not None
                else '—')
        rel_short = {'reliable': '✓', 'indicative': '~', 'insufficient': '!'}.get(
            r['moj_reliability'], '?')
        moj = (f'{int(r["moj_median_per_m2"]):,} (n={r["moj_n"]} {rel_short})'
               if r['moj_median_per_m2']
               else f'— (n={r["moj_n"]} {rel_short})')
        L.append(
            f'| {i} | [{r["property_id"]}]({r["source_url"]}) | '
            f'{r["district_norm"]} | {int(r["size_m2_f"])} | {r["bracket"]} | '
            f'{int(r["asking_per_m2"]):,} | {moj} | {prem} | '
            f'{r["emoji"]} {r["bucket"]} |'
        )
    L += ['',
          '_Tier legend: ✓ reliable (n≥20)  ·  ~ indicative (5≤n<20)  ·  '
          '! insufficient (n<5, no median produced per Section 3)_',
          '',
          '---',
          '_Generated by `backtest_market.py` (Sprint 2.13 + 2026-05-13 hotfix). '
          'Bands per EMPIRICAL_FINDINGS 2026-05. Rule E3 honored: listings ',
          'are diagnostic, never engine input._']
    return '\n'.join(L)


def aggregate(results):
    agg = {}
    bands = {
        'normal': ('0–20%', '✅'), 'investigate': ('20–25%', '⚠️'),
        'red_flag': ('>25%', '🔴'), 'below_moj': ('<0%', '🟦'),
        'insufficient_moj': ('—', '⚪'),
    }
    by_bucket = defaultdict(list)
    for r in results:
        by_bucket[r['bucket']].append(r)
    for k, (band, emoji) in bands.items():
        rows = by_bucket.get(k, [])
        prems = [x['premium_pct'] for x in rows if x['premium_pct'] is not None]
        agg[k] = {
            'count': len(rows), 'band': band, 'emoji': emoji,
            'median_premium': (f'{statistics.median(prems):+.1f}%'
                               if prems else '—'),
        }
    all_prems = [r['premium_pct'] for r in results
                 if r['premium_pct'] is not None]
    agg['overall_median'] = (statistics.median(all_prems)
                             if all_prems else None)
    return agg


# ─── Main ─────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--moj', type=Path, default=DEFAULT_MOJ_CSV,
                    help=f'MoJ CSV (default: {DEFAULT_MOJ_CSV})')
    ap.add_argument('--arady', type=Path, default=None,
                    help='arady_lands_*.csv (default: latest in this dir)')
    args = ap.parse_args()

    arady_csv = args.arady or find_latest_arady_csv()
    if not arady_csv or not arady_csv.exists():
        print('❌ No arady_lands_*.csv found in current directory.')
        print('   Run seed_from_arady.py first to fetch live listings.')
        return 1
    if not args.moj.exists():
        print(f'❌ MoJ CSV not found: {args.moj}')
        print('   Pass --moj <path> to point at your moj_weekly.csv')
        return 1

    print(f'arady source: {arady_csv.name}')
    print(f'MoJ source:   {args.moj}')
    print('-' * 78)

    moj_records = load_moj_land_records(args.moj)
    moj_index = build_moj_index(moj_records)
    print(f'MoJ index: {len(moj_index)} unique (district, bracket) keys')

    arady_rows = load_arady(arady_csv)
    print(f'arady listings: {len(arady_rows)}')
    print('-' * 78)

    results = compare(arady_rows, moj_index)
    agg = aggregate(results)

    # Console summary
    for k in ('normal', 'investigate', 'red_flag', 'below_moj', 'insufficient_moj'):
        info = agg[k]
        print(f'  {info["emoji"]} {k.replace("_"," "):20s} '
              f'{info["count"]:3d} listings, band={info["band"]}, '
              f'median premium={info["median_premium"]}')
    if agg.get('overall_median') is not None:
        print(f'\n  Overall median premium: {agg["overall_median"]:+.1f}%'
              f'    (EMPIRICAL_FINDINGS baseline: +13.6%)')

    # Save outputs
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    out_csv = REPORTS_DIR / f'market_{ts}.csv'
    out_md = REPORTS_DIR / f'market_{ts}.md'

    if results:
        # Coerce datetime/Path objects to str for CSV
        keys = [k for k in results[0].keys() if k != 'date']
        with open(out_csv, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            w.writeheader()
            w.writerows(results)
        out_md.write_text(render(results, agg, ts), encoding='utf-8')
        print(f'\n✅ saved {out_csv}')
        print(f'✅ saved {out_md}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
