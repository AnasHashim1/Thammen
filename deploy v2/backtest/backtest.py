"""
Thammen Backtest Harness — Sprint 2.12

Runs golden_set.csv against the live Thammen API, computes accuracy stats,
and emits a CSV + Markdown report.

Usage (Windows):
    cd /d "C:\\Thammen\\deploy v2\\backtest"
    python backtest.py

Usage (override API endpoint):
    set THAMMEN_API=http://localhost:8000
    python backtest.py

The script never writes outside backtest/reports/. Safe to re-run.

Two modes coexist in golden_set.csv:
    - "pipeline" rows (no sale_price_qar): measure reliability only
      (did the pipeline crash? right asset_type? right district? latency?)
    - "accuracy" rows (sale_price_qar populated): measure prediction error
      against a known actual price. The goal we're driving toward.

Report metrics:
    - Pipeline:  success_rate, mean/p95 latency, type_match_rate
    - Accuracy:  MAE (QAR), MAPE (%), median |error|, %within±10%, %within±20%,
                 actual_within_predicted_range
"""

from __future__ import annotations

import csv
import json
import os
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuration ─────────────────────────────────────────────────────────
API_BASE = os.environ.get('THAMMEN_API', 'https://thammen.qa').rstrip('/')
ENDPOINT = '/api/evaluate/details'   # matches what the frontend calls
TIMEOUT_S = 90
RETRIES_ON_ERROR = 1
THROTTLE_S = 0.5                      # be polite to the rate limiter

ROOT = Path(__file__).parent.resolve()
GOLDEN_CSV = ROOT / 'golden_set.csv'
REPORTS_DIR = ROOT / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)

ctx = ssl.create_default_context()


# ─── HTTP ──────────────────────────────────────────────────────────────────
def call_thammen(zone: int, street: int, building: int, **extras) -> dict:
    """POST to /api/evaluate/details. Returns {'ok', 'response', 'elapsed_s'} or
    {'ok': False, 'error', 'elapsed_s'}."""
    payload = {'zone': zone, 'street': street, 'building': building,
               'audience': 'buyer'}
    # Only include non-empty extras (rental_income, listing_price, etc.)
    for k, v in extras.items():
        if v not in (None, '', 0):
            payload[k] = v
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f'{API_BASE}{ENDPOINT}',
        data=body,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Thammen-Backtest/2.12',
            'Accept': 'application/json',
        },
        method='POST',
    )
    last_err = None
    for attempt in range(RETRIES_ON_ERROR + 1):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S, context=ctx) as r:
                data = json.loads(r.read())
            return {'ok': True, 'response': data,
                    'elapsed_s': round(time.time() - t0, 2)}
        except urllib.error.HTTPError as e:
            last_err = f'HTTP {e.code}: {e.reason}'
        except Exception as e:
            last_err = str(e)[:200]
        if attempt < RETRIES_ON_ERROR:
            time.sleep(2)
    return {'ok': False, 'error': last_err,
            'elapsed_s': round(time.time() - t0, 2)}


# ─── Row processing ───────────────────────────────────────────────────────
def parse_optional_float(s):
    try:
        return float(s) if s not in (None, '', 'None') else None
    except (TypeError, ValueError):
        return None


def parse_optional_int(s):
    try:
        return int(s) if s not in (None, '', 'None') else None
    except (TypeError, ValueError):
        return None


def process_row(row: dict) -> dict:
    """Call the API for one golden_set row and compute per-row metrics."""
    zone = int(row['zone'])
    street = int(row['street'])
    building = int(row['building'])
    actual_price = parse_optional_float(row.get('sale_price_qar'))
    expected_asset = (row.get('actual_asset_type') or '').strip() or None

    # Optional extras
    extras = {
        'rental_income': parse_optional_float(row.get('rental_income')),
        'asking_price': parse_optional_float(row.get('asking_price')),
        'floors': parse_optional_int(row.get('floors')),
        'building_age_years': parse_optional_int(row.get('building_age_years')),
        'basement': True if row.get('basement', '').strip().lower() in
                    ('1', 'true', 'yes') else None,
    }

    r = call_thammen(zone, street, building, **extras)
    out = dict(row)
    out['elapsed_s'] = r['elapsed_s']

    if not r['ok']:
        out['status'] = 'error'
        out['error'] = r['error']
        return out

    d = r['response']
    v = d.get('valuation') or {}
    predicted = v.get('amount')
    predicted_low = v.get('low')
    predicted_high = v.get('high')

    out.update({
        'status': 'ok',
        'engine_version': d.get('engine_version'),
        'asset_type_returned': d.get('asset_type'),
        'district_returned': d.get('district'),
        'method': v.get('method'),
        'predicted_amount': predicted,
        'predicted_low': predicted_low,
        'predicted_high': predicted_high,
        'moj_sample_size': d.get('moj_sample_size'),
        'mat_unc_level': (d.get('material_uncertainty') or {}).get('level'),
        'rics_compliant': (d.get('material_uncertainty') or {}).get('rics_compliant'),
        'sanity_warnings_count': len(d.get('sanity_warnings') or []),
    })

    # Pipeline checks (no actual price needed)
    out['type_match'] = (
        d.get('asset_type') == expected_asset if expected_asset else None
    )

    # Accuracy checks (need actual_price + predicted)
    if actual_price and predicted:
        abs_err = abs(predicted - actual_price)
        pct_err = abs_err / actual_price
        out['abs_error_qar'] = round(abs_err, 0)
        out['pct_error'] = round(pct_err, 4)
        out['within_10pct'] = pct_err <= 0.10
        out['within_20pct'] = pct_err <= 0.20
        if predicted_low and predicted_high:
            out['actual_within_range'] = predicted_low <= actual_price <= predicted_high
    return out


# ─── Aggregation ──────────────────────────────────────────────────────────
def aggregate(results: list[dict]) -> dict:
    """Compute summary metrics across all results."""
    n = len(results)
    n_ok = sum(1 for r in results if r.get('status') == 'ok')
    n_err = n - n_ok

    durs = [r['elapsed_s'] for r in results if r.get('elapsed_s') is not None]
    n_valued = sum(1 for r in results
                   if r.get('status') == 'ok' and r.get('predicted_amount'))

    n_with_actual = sum(1 for r in results if parse_optional_float(r.get('sale_price_qar')))
    n_with_actual_predicted = sum(
        1 for r in results
        if parse_optional_float(r.get('sale_price_qar')) and r.get('predicted_amount')
    )

    abs_errors = [r['abs_error_qar'] for r in results if r.get('abs_error_qar') is not None]
    pct_errors = [r['pct_error'] for r in results if r.get('pct_error') is not None]

    type_matches = [r['type_match'] for r in results if r.get('type_match') is not None]

    within_10 = [r['within_10pct'] for r in results if r.get('within_10pct') is not None]
    within_20 = [r['within_20pct'] for r in results if r.get('within_20pct') is not None]
    within_range = [r['actual_within_range'] for r in results
                    if r.get('actual_within_range') is not None]

    agg = {
        'total': n,
        'success_rate': round(n_ok / n, 3) if n else 0,
        'error_count': n_err,
        'with_valuation_count': n_valued,
        'no_valuation_count': n_ok - n_valued,
        'latency_mean_s': round(statistics.mean(durs), 2) if durs else None,
        'latency_p95_s': round(statistics.quantiles(durs, n=20)[-1], 2)
                         if len(durs) >= 20 else (max(durs) if durs else None),
        'type_match_rate': round(sum(type_matches) / len(type_matches), 3)
                           if type_matches else None,
        # Accuracy block
        'accuracy_n': n_with_actual_predicted,
        'mae_qar': round(statistics.mean(abs_errors), 0) if abs_errors else None,
        'median_abs_error_qar': round(statistics.median(abs_errors), 0)
                                if abs_errors else None,
        'mape': round(statistics.mean(pct_errors), 4) if pct_errors else None,
        'within_10pct_rate': round(sum(within_10) / len(within_10), 3)
                             if within_10 else None,
        'within_20pct_rate': round(sum(within_20) / len(within_20), 3)
                             if within_20 else None,
        'within_range_rate': round(sum(within_range) / len(within_range), 3)
                             if within_range else None,
    }
    return agg


def stratify(results: list[dict], key: str) -> dict:
    """Break results down by a key (e.g. asset_type_returned, district_returned)."""
    buckets = {}
    for r in results:
        k = r.get(key) or '∅'
        buckets.setdefault(k, []).append(r)
    return {k: aggregate(v) for k, v in buckets.items()}


# ─── Report rendering ─────────────────────────────────────────────────────
def render_markdown(results: list[dict], agg: dict, ts: str) -> str:
    L = []
    L += [
        f'# Thammen Backtest Report — {ts}',
        '',
        f'**API:** `{API_BASE}{ENDPOINT}`  ',
        f'**Records tested:** {agg["total"]}  ',
        f'**Engine version observed:** '
        f'{next((r.get("engine_version") for r in results if r.get("engine_version")), "—")}  ',
        '',
        '## Pipeline reliability',
        '',
        '| Metric | Value |',
        '|---|---|',
        f'| Records succeeded | {agg["total"] - agg["error_count"]} / {agg["total"]} '
        f'({agg["success_rate"]*100:.1f}%) |',
        f'| Returned valuation | {agg["with_valuation_count"]} |',
        f'| No valuation (fast/out_of_scope) | {agg["no_valuation_count"]} |',
        f'| Mean latency | {agg["latency_mean_s"]}s |',
        f'| P95 latency | {agg["latency_p95_s"]}s |',
        f'| Asset-type match rate | '
        f'{(agg["type_match_rate"] or 0)*100:.1f}% '
        f'(of records with `actual_asset_type` set) |',
        '',
    ]

    if agg['accuracy_n']:
        L += [
            '## Accuracy (records with `sale_price_qar` populated)',
            '',
            f'Sample size: **n={agg["accuracy_n"]}** (statistical reliability needs n≥30; '
            'add real sales to `golden_set.csv` to grow this)',
            '',
            '| Metric | Value | Target |',
            '|---|---|---|',
            f'| MAE (Mean Absolute Error) | {agg["mae_qar"]:,.0f} QAR | lower is better |',
            f'| Median absolute error | {agg["median_abs_error_qar"]:,.0f} QAR | robust to outliers |',
            f'| MAPE (Mean Abs % Error) | {agg["mape"]*100:.2f}% | <10% is RICS-aligned |',
            f'| % within ±10% | {agg["within_10pct_rate"]*100:.1f}% | >70% |',
            f'| % within ±20% | {agg["within_20pct_rate"]*100:.1f}% | >90% |',
            f'| Actual within predicted range | {agg["within_range_rate"]*100:.1f}% | >80% |',
            '',
        ]
    else:
        L += [
            '## Accuracy',
            '',
            '_No records with `sale_price_qar` yet. Populate `golden_set.csv` with '
            'real sale records to unlock accuracy metrics._',
            '',
        ]

    # Stratify by asset_type
    by_asset = stratify(results, 'asset_type_returned')
    L += ['## By asset type', '']
    L += ['| Asset type | N | Valued | Latency p95 | Type match |',
          '|---|---|---|---|---|']
    for k, v in sorted(by_asset.items(), key=lambda x: -x[1]['total']):
        L.append(
            f'| {k} | {v["total"]} | {v["with_valuation_count"]} | '
            f'{v["latency_p95_s"]}s | '
            f'{((v["type_match_rate"] or 0)*100):.0f}% |'
        )
    L += ['']

    # Stratify by district
    by_dist = stratify(results, 'district_returned')
    L += ['## By district', '']
    L += ['| District | N | Valued | Latency p95 |',
          '|---|---|---|---|']
    for k, v in sorted(by_dist.items(), key=lambda x: -x[1]['total']):
        L.append(
            f'| {k} | {v["total"]} | {v["with_valuation_count"]} | '
            f'{v["latency_p95_s"]}s |'
        )
    L += ['']

    # Outliers — worst pct_error
    with_err = [r for r in results if r.get('pct_error') is not None]
    if with_err:
        L += ['## Worst-error outliers', '', '| Address | Actual | Predicted | Error % |',
              '|---|---|---|---|']
        for r in sorted(with_err, key=lambda x: -x['pct_error'])[:5]:
            addr = f'{r["zone"]}/{r["street"]}/{r["building"]}'
            actual = parse_optional_float(r['sale_price_qar'])
            pred = r['predicted_amount']
            L.append(f'| {addr} | {actual:,.0f} | {pred:,.0f} | '
                     f'{r["pct_error"]*100:.1f}% |')
        L += ['']

    # Per-row detail
    L += ['## Per-record detail', '',
          '| # | Address | Asset (got) | District (got) | Predicted | Actual | Err% | Latency |',
          '|---|---|---|---|---|---|---|---|']
    for i, r in enumerate(results, 1):
        addr = f'{r["zone"]}/{r["street"]}/{r["building"]}'
        a = r.get('asset_type_returned') or '∅'
        dist = r.get('district_returned') or '∅'
        p = r.get('predicted_amount')
        actual = parse_optional_float(r.get('sale_price_qar'))
        pct = r.get('pct_error')
        L.append(
            f'| {i} | {addr} | {a} | {dist} | '
            f'{(f"{p:,.0f}" if p else "—")} | '
            f'{(f"{actual:,.0f}" if actual else "—")} | '
            f'{(f"{pct*100:.1f}%" if pct is not None else "—")} | '
            f'{r["elapsed_s"]}s |'
        )
    L += ['']

    L += ['---', '_Generated by `backtest.py` (Sprint 2.12)._']
    return '\n'.join(L)


# ─── Main ─────────────────────────────────────────────────────────────────
def main():
    if not GOLDEN_CSV.exists():
        print(f'❌ Golden set not found: {GOLDEN_CSV}', file=sys.stderr)
        return 1

    with open(GOLDEN_CSV, encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f) if r.get('zone', '').strip()]

    if not rows:
        print('❌ golden_set.csv is empty (no data rows)', file=sys.stderr)
        return 1

    print(f'Loaded {len(rows)} entries from {GOLDEN_CSV.name}')
    print(f'API: {API_BASE}{ENDPOINT}')
    print('-' * 78)

    results = []
    t_total = time.time()
    for i, row in enumerate(rows, 1):
        addr = f'{row["zone"]}/{row["street"]}/{row["building"]}'
        print(f'[{i:2d}/{len(rows)}] {addr:14s}', end=' ', flush=True)
        out = process_row(row)
        results.append(out)

        if out.get('status') == 'error':
            print(f'❌ {out.get("error","?")[:50]}  ({out["elapsed_s"]}s)')
        else:
            p = out.get('predicted_amount')
            tag = (f'pred={p:,.0f}' if p else f'no_val ({out.get("method","?")})')
            actual = parse_optional_float(out.get('sale_price_qar'))
            if actual and p:
                tag += f' actual={actual:,.0f} err={out["pct_error"]*100:.1f}%'
            print(f'✓ [{out.get("asset_type_returned","?")}] {tag}  '
                  f'({out["elapsed_s"]}s)')
        time.sleep(THROTTLE_S)

    print('-' * 78)
    print(f'Total runtime: {time.time() - t_total:.1f}s')

    agg = aggregate(results)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

    # Save raw CSV
    out_csv = REPORTS_DIR / f'backtest_{ts}.csv'
    keys = sorted({k for r in results for k in r.keys()})
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(results)
    print(f'✅ saved {out_csv}')

    # Save Markdown report
    md = render_markdown(results, agg, ts)
    out_md = REPORTS_DIR / f'backtest_{ts}.md'
    out_md.write_text(md, encoding='utf-8')
    print(f'✅ saved {out_md}')

    # Print summary
    print('\n' + '=' * 78)
    print('SUMMARY')
    print('=' * 78)
    print(f'Records:     {agg["total"]} (success: {agg["total"]-agg["error_count"]}, '
          f'errors: {agg["error_count"]})')
    print(f'Valuations:  {agg["with_valuation_count"]} returned, '
          f'{agg["no_valuation_count"]} no-value (fast/oos)')
    print(f'Latency:     mean={agg["latency_mean_s"]}s  p95={agg["latency_p95_s"]}s')
    if agg.get('type_match_rate') is not None:
        print(f'Type match:  {agg["type_match_rate"]*100:.1f}%')
    if agg['accuracy_n']:
        print(f'Accuracy:    n={agg["accuracy_n"]}  '
              f'MAPE={agg["mape"]*100:.2f}%  '
              f'within10={agg["within_10pct_rate"]*100:.1f}%  '
              f'within20={agg["within_20pct_rate"]*100:.1f}%')
    else:
        print('Accuracy:    no real-sale records yet — add to golden_set.csv')
    print('=' * 78)
    return 0


if __name__ == '__main__':
    sys.exit(main())
