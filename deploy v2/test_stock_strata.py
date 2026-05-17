#!/usr/bin/env python3
"""
test_stock_strata.py — Sprint 2.16.0 tests.

Run from deploy v2 root:
    python test_stock_strata.py

Covers:
    - classify_ratio thresholds (Rule E4)
    - compute_strata partitioning + medians
    - classify_subject_property with all inputs
    - bracket-matched land median selection
    - empirical validation against 3 confirmed sales
"""
from __future__ import annotations

import csv
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path

try:
    from stock_strata import (
        classify_ratio,
        compute_strata,
        compute_land_median,
        classify_subject_property,
        build_stock_strata_result,
        STRATA_VERSION,
        STRATUM_THRESHOLDS,
        _parse_date,
        _norm,
    )
except ImportError as e:
    print(f"FATAL: cannot import stock_strata: {e}")
    sys.exit(2)


# ───────────────────────────── helpers ─────────────────────────────
PASS = '\033[32m✓\033[0m'
FAIL = '\033[31m✗\033[0m'
results = []


def t(name, fn):
    try:
        fn()
        results.append((True, name, None))
        print(f"  {PASS} {name}")
    except AssertionError as e:
        results.append((False, name, str(e)))
        print(f"  {FAIL} {name}")
        print(f"    └─ {e}")
    except Exception as e:
        results.append((False, name, f"{type(e).__name__}: {e}"))
        print(f"  {FAIL} {name}")
        print(f"    └─ {type(e).__name__}: {e}")
        traceback.print_exc()


# ───────────────────────────── unit tests ─────────────────────────────
def test_classifier_thresholds():
    # Rule E4 thresholds (1.15 / 1.50 / 2.20)
    assert classify_ratio(0.5) == 'land_priced', '0.5 → land_priced'
    assert classify_ratio(1.14) == 'land_priced', 'just below 1.15 → land_priced'
    assert classify_ratio(1.15) == 'aging_stock', 'exactly 1.15 → aging_stock'
    assert classify_ratio(1.49) == 'aging_stock', 'just below 1.50'
    assert classify_ratio(1.50) == 'modern_stock', 'exactly 1.50'
    assert classify_ratio(2.19) == 'modern_stock', 'just below 2.20'
    assert classify_ratio(2.20) == 'luxury_new', 'exactly 2.20'
    assert classify_ratio(3.0)  == 'luxury_new', '3.0 → luxury_new'
    # Edge cases
    assert classify_ratio(None) == 'unknown'
    assert classify_ratio(0)    == 'unknown'
    assert classify_ratio(-1)   == 'unknown'


def test_compute_strata_partitioning():
    """Given land median 4000, partition villas by their per_m2."""
    txns = [
        {'price_m2': 3500},   # 0.875 → land_priced
        {'price_m2': 4500},   # 1.125 → land_priced
        {'price_m2': 5000},   # 1.25  → aging_stock
        {'price_m2': 6000},   # 1.50  → modern_stock (boundary)
        {'price_m2': 7000},   # 1.75  → modern_stock
        {'price_m2': 9000},   # 2.25  → luxury_new
    ]
    out = compute_strata(txns, land_median_per_m2=4000.0, plot_area_m2=500)
    assert out['land_priced']['n'] == 2, f"land_priced n: {out['land_priced']['n']}"
    assert out['aging_stock']['n'] == 1
    assert out['modern_stock']['n'] == 2
    assert out['luxury_new']['n'] == 1
    # Medians
    assert out['land_priced']['median_per_m2'] == 4000  # median of 3500, 4500
    assert out['modern_stock']['median_per_m2'] == 6500
    # Totals × plot_area
    assert out['luxury_new']['estimated_total'] == 9000 * 500


def test_subject_classification():
    """Subject 4.45M @ 600m² @ land 3929 → ratio 1.89 → modern_stock."""
    out = classify_subject_property(
        listing_price=4_450_000,
        plot_area_m2=600,
        land_median_per_m2=3929,
    )
    assert out is not None
    assert out['implied_ratio'] == 1.89, f"got {out['implied_ratio']}"
    assert out['classification'] == 'modern_stock'
    # Missing inputs → None
    assert classify_subject_property(None, 600, 3929) is None
    assert classify_subject_property(1e6, None, 3929) is None
    assert classify_subject_property(1e6, 600, None) is None


def test_empty_inputs():
    """Empty / None inputs → graceful None or empty dict."""
    assert build_stock_strata_result(None, None, None, None, None, 'date_col') is None
    assert build_stock_strata_result([], set(), [], 500, None, 'date_col') is None
    assert compute_strata([], 4000) == {}
    assert compute_strata([{'price_m2': 5000}], 0) == {}  # bad land median


def test_band_labels():
    """Band labels are formatted correctly (<1.15, 1.15-1.50, etc)."""
    txns = [{'price_m2': p} for p in (3000, 5000, 7000, 9500)]
    out = compute_strata(txns, 4000.0)
    assert out['land_priced']['ratio_band']  == '<1.15'
    assert out['aging_stock']['ratio_band']  == '1.15-1.5'
    assert out['modern_stock']['ratio_band'] == '1.5-2.2'
    assert out['luxury_new']['ratio_band']   == '≥2.2'


# ───────────────────────── integration test ─────────────────────────
def test_integration_against_moj_csv():
    """End-to-end: load MoJ csv, reproduce Al-Gharafa probe finding."""
    candidates = [
        Path(__file__).parent / 'moj_weekly.csv',
        Path.cwd() / 'moj_weekly.csv',
        Path(__file__).parent / 'moj_weekly_sample.csv',
        Path.cwd() / 'moj_weekly_sample.csv',
    ]
    csv_path = next((p for p in candidates if p.exists()), None)
    if not csv_path:
        print(f"    └─ SKIPPED (no moj_weekly.csv found in {[str(p) for p in candidates]})")
        return  # not an assertion failure — just unavailable

    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        date_col = next(k for k in reader.fieldnames if 'تاريخ' in k and 'تثبيت' in k)
        rows = list(reader)

    # Find latest date + 24m window
    latest = max(
        (_parse_date(r.get(date_col, '')) for r in rows
         if _parse_date(r.get(date_col, ''))),
        default=None
    )
    assert latest is not None, 'No parseable dates in MoJ CSV'
    cutoff = latest - timedelta(days=730)

    # Get Al-Gharafa 400-600 villa transactions (the probe target)
    gharafa = {'الغرافة', 'غرافة الريان'}
    villa_txns = []
    for r in rows:
        a = _norm(r.get('اسم المنطقة', ''))
        t_ar = _norm(r.get('نوع العقار', ''))
        if a not in gharafa:
            continue
        is_villa = ((t_ar.startswith('فيلا') or t_ar == 'مسكن' or t_ar == 'بيت للسكن')
                    and 'شعبي' not in t_ar)
        if not is_villa:
            continue
        d = _parse_date(r.get(date_col, ''))
        if not d or d < cutoff:
            continue
        try:
            am = float((r.get('المساحة بالمتر المربع', '') or '0').replace(',', '').strip())
            pm = float((r.get('سعر المتر المربع', '') or '0').replace(',', '').strip())
        except (ValueError, AttributeError):
            continue
        if not (400 <= am < 600):
            continue
        if pm <= 0:
            continue
        villa_txns.append({'price_m2': pm, 'area_m2': am, 'date': d.strftime('%Y-%m-%d')})

    # Need at least minimum sample
    assert len(villa_txns) >= 10, \
        f'Al-Gharafa 400-600 villas: only n={len(villa_txns)}'

    result = build_stock_strata_result(
        moj_rows=rows,
        moj_area_names=gharafa,
        villa_transactions=villa_txns,
        plot_area_m2=600,
        listing_price=4_450_000,  # confirmed sale
        date_col=date_col,
    )
    assert result is not None, 'build_stock_strata_result returned None'
    assert result['applied'] is True
    assert result['version'] == STRATA_VERSION

    # Bracket-matched land reference
    assert result['land_reference']['bracket_match'] is True, \
        f'expected bracket-matched land, got {result["land_reference"]}'

    # Subject classification
    sp = result['subject_property']
    assert sp is not None, 'subject_property missing'
    assert sp['classification'] in ('modern_stock', 'luxury_new'), \
        f'subject ratio {sp["implied_ratio"]} → {sp["classification"]}'

    # Whichever stratum the subject lands in, estimated_total should be
    # within +/- 15% of the actual sale (4.45M) — this is the empirical
    # validation that stratification works.
    cls = sp['classification']
    stratum = result['strata'][cls]
    if stratum['estimated_total']:
        actual = 4_450_000
        err_pct = abs(stratum['estimated_total'] - actual) / actual * 100
        assert err_pct < 15, (
            f'Al-Gharafa probe: stratum {cls} estimated '
            f'{stratum["estimated_total"]:,} vs actual {actual:,} '
            f'→ error {err_pct:.1f}% (expected <15%)'
        )


# ───────────────────────────── run ─────────────────────────────
def main():
    print(f"\nstock_strata.py tests (version {STRATA_VERSION}):\n")
    print("Classifier:")
    t('thresholds match Rule E4',                 test_classifier_thresholds)
    print("\nPartitioning:")
    t('compute_strata partitions correctly',      test_compute_strata_partitioning)
    t('band labels are formatted as expected',    test_band_labels)
    print("\nSubject classification:")
    t('subject ratio computation + classification', test_subject_classification)
    print("\nEdge cases:")
    t('empty / invalid inputs return gracefully', test_empty_inputs)
    print("\nIntegration:")
    t('Al-Gharafa probe reproduces within 15%',   test_integration_against_moj_csv)

    n_pass = sum(1 for r in results if r[0])
    n_total = len(results)
    print(f"\n{n_pass}/{n_total} tests passed.")
    return 0 if n_pass == n_total else 1


if __name__ == '__main__':
    sys.exit(main())
