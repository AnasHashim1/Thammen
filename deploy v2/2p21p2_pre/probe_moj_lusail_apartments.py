"""
Probe 2 of Sprint 2.21.2 §5 audit:
Is MoJ T1 truly empty for Lusail apartments?

Reads moj_weekly.csv (per Operational §13 schema), normalizes NBSP per
§14, and counts rows that could plausibly represent individual apartment
units in Lusail across all asset_type / usage combinations.

Pass criterion (BRIEF §5): n=0 across all 5 addresses, confirming MoJ
does not disaggregate individual apartments.

For this district-level probe: pass means n=0 apartment-unit rows in
Lusail OR n is so small that it doesn't constitute a usable T1 source
(threshold: <10 per BRIEF Constraint 4).
"""
import csv
import re
import sys
from collections import Counter

MOJ_CSV = r"C:\Thammen\deploy v2\moj_weekly.csv"


def norm(s):
    """Per Operational §14: NBSP → space, collapse whitespace, strip."""
    return re.sub(r"\s+", " ", s or "").strip()


# All asset_type variants that could plausibly represent apartments
APT_LIKE_TOKENS = [
    "شقة",        # apartment unit
    "شقق",        # apartments (plural)
    "وحدة سكنية", # residential unit (sometimes apartment)
    # "عمارة سكنية" is whole building, not individual unit — counted separately
    # "برج سكني" is whole tower, same
]
WHOLE_BUILDING_TOKENS = [
    "عمارة سكنية",
    "برج سكني",
]
LUSAIL_VARIANTS = [
    "لوسيل",
    "لوسيل 69",  # historic suffix per §15
]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    total_rows = 0
    lusail_rows = 0
    lusail_asset_types = Counter()
    lusail_apt_unit_rows = []
    lusail_whole_building_rows = []

    with open(MOJ_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            district = norm(row.get("اسم المنطقة", ""))
            asset_type = norm(row.get("نوع العقار", ""))
            usage = norm(row.get("الاستخدام", ""))

            is_lusail = any(v in district for v in LUSAIL_VARIANTS)
            if not is_lusail:
                continue
            lusail_rows += 1
            lusail_asset_types[asset_type] += 1

            if any(tok in asset_type for tok in APT_LIKE_TOKENS):
                lusail_apt_unit_rows.append({
                    "district": district, "asset_type": asset_type,
                    "usage": usage,
                    "date": norm(row.get("تاريخ التثبيت", "")),
                    "area_m2": norm(row.get("المساحة بالمتر المربع", "")),
                    "price_m2": norm(row.get("سعر المتر المربع", "")),
                })
            elif any(tok in asset_type for tok in WHOLE_BUILDING_TOKENS):
                lusail_whole_building_rows.append({
                    "district": district, "asset_type": asset_type,
                    "usage": usage,
                    "date": norm(row.get("تاريخ التثبيت", "")),
                    "area_m2": norm(row.get("المساحة بالمتر المربع", "")),
                    "price_m2": norm(row.get("سعر المتر المربع", "")),
                })

    print("=" * 76)
    print("Probe 2 — MoJ Lusail apartment record count")
    print("=" * 76)
    print(f"Total MoJ rows: {total_rows}")
    print(f"Lusail rows (any asset_type): {lusail_rows}")
    print()
    print("Lusail asset_type distribution (top 15):")
    for at, n in lusail_asset_types.most_common(15):
        print(f"  {n:>5}  {at!r}")
    print()
    print(f"=== Apartment-UNIT rows in Lusail (شقة/شقق/وحدة سكنية): "
          f"{len(lusail_apt_unit_rows)} ===")
    for row in lusail_apt_unit_rows[:10]:
        print(f"  {row}")
    if len(lusail_apt_unit_rows) > 10:
        print(f"  ...and {len(lusail_apt_unit_rows) - 10} more")
    print()
    print(f"=== Whole-building rows in Lusail (عمارة سكنية/برج سكني): "
          f"{len(lusail_whole_building_rows)} ===")
    for row in lusail_whole_building_rows[:10]:
        print(f"  {row}")
    if len(lusail_whole_building_rows) > 10:
        print(f"  ...and {len(lusail_whole_building_rows) - 10} more")

    print()
    print("=" * 76)
    print("INTERPRETATION (per BRIEF §5 Probe 2)")
    print("=" * 76)
    apt_n = len(lusail_apt_unit_rows)
    if apt_n == 0:
        print(f"PASS: n=0 apartment-unit rows in Lusail. T1 truly empty for "
              f"individual apartments — confirms BRIEF memory and Sprint 2.21.2 premise.")
    elif apt_n < 10:
        print(f"PARTIAL: n={apt_n} apartment-unit rows. Below Rule E3 Constraint 4 "
              f"threshold (n<10 → no T1 dominance). Still consistent with BRIEF.")
    else:
        print(f"SURPRISE: n={apt_n} apartment-unit rows in Lusail. MoJ DOES "
              f"disaggregate individual apartments. **STOP and report to Anas** — "
              f"Sprint 2.21.2 premise needs review.")


if __name__ == "__main__":
    main()
