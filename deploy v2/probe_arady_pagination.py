"""
probe_arady_pagination.py — resolve the pagination discrepancy (Sprint 2.20 audit).

Anas observed 30 UNIQUE listings per page across pages 1/5/10/20/40 (curl).
The earlier probe only hit the bare /listings/lands (no ?page=) and the 2.13
comment claimed "pages 2+ unreachable". This tests ?page=N directly via
urllib and reports whether IDs differ across pages (i.e. is the reachable
land sample 30, or hundreds?).

Pure stdlib. Polite. Run locally: python probe_arady_pagination.py
"""
import re
import sys
import time
import urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (research-collection)'}
BASE = 'https://arady.qa/listings/lands'
PAGES = [1, 2, 3, 5, 10, 20, 40]


def harvest(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        html = r.read().decode('utf-8', errors='replace')
    return r.status, sorted(set(int(m) for m in re.findall(r'/property/(\d+)', html)))


def main():
    print("=" * 64)
    print("arady /listings/lands pagination test")
    print("=" * 64)
    per_page = {}
    for p in PAGES:
        url = BASE if p == 1 else f"{BASE}?page={p}"
        try:
            status, ids = harvest(url)
            per_page[p] = set(ids)
            print(f"  page {p:2d}: HTTP {status}, {len(ids)} ids, "
                  f"sample={sorted(ids)[:3]}")
        except Exception as e:
            print(f"  page {p:2d}: ERROR {type(e).__name__}: {str(e)[:100]}")
        time.sleep(0.6)

    if not per_page:
        print("no pages harvested.")
        return 1

    union = set().union(*per_page.values())
    print("-" * 64)
    print(f"distinct ids across all tested pages: {len(union)}")
    # Pairwise overlap of page1 vs each other page
    p1 = per_page.get(1, set())
    for p in PAGES:
        if p == 1 or p not in per_page:
            continue
        inter = len(p1 & per_page[p])
        print(f"  page1 ∩ page{p}: {inter} shared / "
              f"{len(per_page[p])} on page{p} "
              f"({'IDENTICAL' if per_page[p] == p1 else 'DIFFERENT'})")
    print("=" * 64)
    if len(union) <= 35:
        print("VERDICT: pagination does NOT expand the sample (~30 total).")
    else:
        print(f"VERDICT: pagination WORKS — reachable land sample ≈ {len(union)}+ "
              f"(coefficient derivation feasible).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
