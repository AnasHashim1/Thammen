"""
audit_c_land_coverage.py — Sprint 2.20 (Land Grid) feasibility audit.

Question: how many (area_token x size_bracket) LAND cells have enough MoJ
transactions to populate a meaningful comparison grid? A grid needs n>=10
(indicative) per cell, ideally n>=20 (reliable) — project sample-size
discipline (§3 / Rule E4 reliability gate).

Reuses the PRODUCTION MoJ reference path (cap_rate_calibrator.MojSaleIndex ->
moj_reference.build_reference), so coverage reflects what the engine actually
sees (Operational_Rules #40). Read-only on moj_weekly.csv.

Run locally: python audit_c_land_coverage.py
"""
import sys
from collections import Counter

import cap_rate_calibrator as cal


def tier(n):
    if n >= 20:
        return "reliable(>=20)"
    if n >= 10:
        return "indicative(10-19)"
    if n >= 5:
        return "context(5-9)"
    return "insufficient(<5)"


def main():
    idx = cal.MojSaleIndex()
    # Aggregate max land n per (token, bracket) across the area's MoJ name variants.
    cell_n = {}            # (token, bracket) -> best land n
    cell_area = {}         # (token, bracket) -> moj_area giving that n
    for token, areas in idx._token_to_areas.items():
        for moj_area in areas:
            ref = idx._reference(moj_area)
            land = (ref.get("categories", {}).get("land", {})
                    .get("size_brackets", {}) or {})
            for bkey, data in land.items():
                n = (data or {}).get("n", 0) or 0
                key = (token, bkey)
                if n > cell_n.get(key, -1):
                    cell_n[key] = n
                    cell_area[key] = moj_area

    if not cell_n:
        print("No land cells found — check moj_weekly.csv / category labels.")
        return 1

    tiers = Counter(tier(n) for n in cell_n.values())
    total = len(cell_n)
    print("=" * 66)
    print("Audit C — MoJ LAND grid coverage (cells = area_token x bracket)")
    print("=" * 66)
    print(f"total land cells with any data: {total}")
    for t in ("reliable(>=20)", "indicative(10-19)", "context(5-9)", "insufficient(<5)"):
        c = tiers.get(t, 0)
        print(f"  {t:20s} {c:4d}  ({c/total*100:4.1f}%)")
    grid_ready = sum(1 for n in cell_n.values() if n >= 10)
    print(f"\nGRID-READY cells (n>=10): {grid_ready}/{total} ({grid_ready/total*100:.1f}%)")

    # Distinct area tokens that have >=1 grid-ready land cell
    ready_tokens = sorted({tok for (tok, _), n in cell_n.items() if n >= 10})
    print(f"area tokens with >=1 grid-ready land bracket: {len(ready_tokens)}")

    # Top reliable cells
    top = sorted(((n, tok, bk, cell_area[(tok, bk)])
                  for (tok, bk), n in cell_n.items() if n >= 20),
                 reverse=True)[:15]
    print(f"\ntop reliable land cells (n>=20), showing up to 15:")
    for n, tok, bk, area in top:
        print(f"  n={n:3d}  {tok:18s} {bk:12s}  (MoJ: {area})")
    print("=" * 66)
    return 0


if __name__ == '__main__':
    sys.exit(main())
