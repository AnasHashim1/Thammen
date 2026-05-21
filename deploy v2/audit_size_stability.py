"""
audit_size_stability.py — Sprint 2.20 §8 pre-build gate (Decision #3).

Question: for the LAND grid, is the within-bracket size -> price/m2 relationship
stable enough to justify a size adjustment? If <40% of grid-ready cells are
stable, ship time-only and defer size to 2.20.1.

Reuses the PRODUCTION comparable set: moj_reference.build_reference(
return_transactions=True) -> the exact land transactions the engine would
compare against, per (MoJ area name x size bracket), 24m window (36m fallback).

For each land cell with n>=15 we fit OLS price/m2 = slope*size + intercept and
compute THREE candidate stability criteria so we can pick empirically:
  (a) p<0.05 proxy: |t| = |slope|/stderr(slope) >= 2.0
  (b) R^2 > 0.30
  (c) CoV(slope) = stderr(slope)/|slope| < 0.50   (Anas-recommended)

Pure stdlib. Read-only. Run: python audit_size_stability.py
"""
import csv
import math
import sys
from collections import Counter

import moj_reference as mr

N_GATE = 15            # Anas: size adjustment only considered at n>=15
T_THRESHOLD = 2.0      # |t| proxy for p<0.05 (df>=13 -> t_crit ~2.0-2.16)
R2_THRESHOLD = 0.30
COV_THRESHOLD = 0.50


def ols(xs, ys):
    """Return dict(slope, intercept, r2, se_slope, t, cov) or None if degenerate."""
    n = len(xs)
    if n < 3:
        return None
    sx = sum(xs); sy = sum(ys)
    xbar = sx / n; ybar = sy / n
    sxx = sum((x - xbar) ** 2 for x in xs)
    if sxx <= 0:
        return None  # all sizes identical -> no size signal
    sxy = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    syy = sum((y - ybar) ** 2 for y in ys)
    slope = sxy / sxx
    intercept = ybar - slope * xbar
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / syy if syy > 0 else 0.0
    if n - 2 <= 0:
        return None
    se_slope = math.sqrt((ss_res / (n - 2)) / sxx) if sxx > 0 else float('inf')
    t = slope / se_slope if se_slope > 0 else float('inf')
    cov = (se_slope / abs(slope)) if slope != 0 else float('inf')
    return {'n': n, 'slope': slope, 'r2': r2, 'se_slope': se_slope,
            't': t, 'cov': cov}


def main():
    with open('moj_weekly.csv', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    dates = [d for d in (mr.parse_date(r[mr.DATE_COL]) for r in rows) if d]
    max_d = max(dates)
    areas = sorted({mr.normalize(r.get('اسم المنطقة', '')) for r in rows if r.get('اسم المنطقة')})
    print("=" * 70)
    print(f"Sprint 2.20 §8 — LAND size-stability scan ({len(areas)} MoJ areas)")
    print(f"criteria: (a) |t|>= {T_THRESHOLD}  (b) R2> {R2_THRESHOLD}  (c) CoV< {COV_THRESHOLD}")
    print("=" * 70)

    cells = []   # (area, bracket, fit)
    for area in areas:
        ref = mr.build_reference(rows, area, max_d, return_transactions=True)
        land = (ref.get('categories', {}).get('land', {}).get('size_brackets', {}) or {})
        for bkey, bdata in land.items():
            txns = bdata.get('transactions') or []
            pairs = [(t['area_m2'], t['price_per_m2']) for t in txns
                     if t.get('area_m2') and t.get('price_per_m2')]
            if len(pairs) < N_GATE:
                continue
            xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
            fit = ols(xs, ys)
            if fit:
                cells.append((area, bkey, fit))

    total = len(cells)
    if not total:
        print("No land cells with n>=15. Size adjustment not feasible.")
        return 1

    stable_a = sum(1 for _, _, f in cells if abs(f['t']) >= T_THRESHOLD)
    stable_b = sum(1 for _, _, f in cells if f['r2'] > R2_THRESHOLD)
    stable_c = sum(1 for _, _, f in cells if f['cov'] < COV_THRESHOLD)
    print(f"land cells with n>=15: {total}\n")
    for name, cnt in (("(a) |t|>=2.0  (p<0.05 proxy)", stable_a),
                      ("(b) R2 > 0.30", stable_b),
                      ("(c) CoV(slope) < 0.50", stable_c)):
        print(f"  stable under {name:32s}: {cnt:3d}/{total}  ({cnt/total*100:4.1f}%)")

    # Agreement between criteria
    set_a = {(a, b) for a, b, f in cells if abs(f['t']) >= T_THRESHOLD}
    set_b = {(a, b) for a, b, f in cells if f['r2'] > R2_THRESHOLD}
    set_c = {(a, b) for a, b, f in cells if f['cov'] < COV_THRESHOLD}
    print(f"\n  agreement a∩c: {len(set_a & set_c)}   b∩c: {len(set_b & set_c)}   a∩b: {len(set_a & set_b)}")
    print(f"  a∩b∩c (all three agree stable): {len(set_a & set_b & set_c)}")

    # Slope sign distribution (expect mostly negative: bigger plot -> lower price/m2)
    signs = Counter('neg' if f['slope'] < 0 else 'pos' if f['slope'] > 0 else 'zero'
                    for _, _, f in cells)
    print(f"\n  slope sign distribution: {dict(signs)}")

    # Median R2 / CoV for context
    r2s = sorted(f['r2'] for _, _, f in cells)
    covs = sorted(f['cov'] for _, _, f in cells if f['cov'] != float('inf'))
    print(f"  median R2 across cells:  {r2s[len(r2s)//2]:.3f}")
    if covs:
        print(f"  median CoV across cells: {covs[len(covs)//2]:.3f}")

    print("\n  sample cells (area, bracket, n, slope, R2, CoV):")
    for area, bkey, f in cells[:12]:
        print(f"    {area[:16]:16s} {bkey:14s} n={f['n']:3d} "
              f"slope={f['slope']:+8.3f} R2={f['r2']:.2f} CoV={f['cov']:.2f}")

    print("=" * 70)
    pct_c = stable_c / total * 100
    verdict = "PROCEED with size adjustment" if pct_c >= 40 else "SHIP TIME-ONLY, defer size to 2.20.1"
    print(f"VERDICT (criterion c, threshold 40%): {pct_c:.1f}% stable -> {verdict}")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    sys.exit(main())
