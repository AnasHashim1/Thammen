"""
probe_lstkhdm_audit.py — Sprint 2.21.0.7 audit P3 (MoJ lstkhdm usage filter).

Reads the LOCAL moj_weekly.csv and prints the distribution of the الاستخدام
("lstkhdm" / usage) column, restricted to أرض فضاء (vacant-land) rows, so we can
design the P3 usage filter: when classifying a bare-land PIN, which MoJ
comparables share the *same intended use* as the subject parcel.

Why a file (not inline python -c): Arabic string literals get mangled when passed
through the shell (Operational_Rules #34). Run locally — no GIS needed.

    python probe_lstkhdm_audit.py
"""
import csv
import re
from collections import Counter

CSV = "moj_weekly.csv"


def norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def main():
    rows = []
    with open(CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    print("=" * 72)
    print(f"moj_weekly.csv — total rows: {len(rows):,}")
    cols = rows[0].keys() if rows else []
    print("columns:", list(cols))

    # locate type + usage columns by content (NBSP-safe)
    type_col = next((c for c in cols if "نوع" in c), None)
    use_col = next((c for c in cols if "استخدام" in c.replace("آ", "ا")), None)
    print(f"type col = {type_col!r}   usage col = {use_col!r}")
    print("=" * 72)

    land = [r for r in rows if norm(r.get(type_col)) == norm("أرض فضاء")]
    print(f"أرض فضاء (vacant-land) rows: {len(land):,}")

    use = Counter(norm(r.get(use_col)) for r in land)
    empty = use.get("", 0)
    print(f"empty usage: {empty:,} ({empty/len(land)*100:.1f}%)")
    print("-" * 72)
    print("الاستخدام distribution on أرض فضاء (normalized):")
    for val, n in use.most_common():
        label = val if val else "(empty)"
        print(f"  {n:>6,}  {label}")
    print("=" * 72)

    # also: full-corpus usage distribution (all property types) for context
    print("الاستخدام distribution — ALL rows (top 25):")
    use_all = Counter(norm(r.get(use_col)) for r in rows)
    for val, n in use_all.most_common(25):
        label = val if val else "(empty)"
        print(f"  {n:>6,}  {label}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
