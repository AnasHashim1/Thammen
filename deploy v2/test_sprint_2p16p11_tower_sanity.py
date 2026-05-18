"""
Sprint 2.16.11 — Isolated tests for the BUA-aware sanity warning carve-out.

Verifies that the rent/m² sanity check in `_check_input_sanity`:
- no longer fires false positives on towers (the bug we saw with Lusail B201)
- still catches the original cases it was designed for (single-unit-rent
  mistakes on compounds, extreme rents on apartment buildings)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def extract_sanity_function():
    """Pull `_check_input_sanity` out of evaluate_unified.py into our namespace
    without importing the whole module (which has heavy dependencies)."""
    with open('evaluate_unified.py', encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'(def _check_input_sanity\(.*?\n    return \{.*?\})', src, re.DOTALL)
    if not m:
        return None, src
    ns = {}
    exec(m.group(1), ns)
    return ns['_check_input_sanity'], src


def main():
    fn, src = extract_sanity_function()
    if fn is None:
        print("\u2717 _check_input_sanity not found")
        return 1

    def warns(asset_type, rental, plot):
        return fn(asset_type, None, rental, plot)['warnings_ar']

    passed = 0
    failed = 0

    def check(cond, label):
        nonlocal passed, failed
        if cond:
            print(f"  \u2713 {label}")
            passed += 1
        else:
            print(f"  \u2717 {label}")
            failed += 1

    print("Carve-out scenarios:")

    # The exact bug we saw today on Lusail B201
    ws = warns('tower', 1_000_000, 3378)
    check(not any('مرتفع جداً لأصل' in w for w in ws),
          "tower @ 1M/mo, plot 3378 m²: no false high-rent warning")

    # The new flow's typical case (Sprint 2.16.10 pair: 80×12K)
    ws = warns('tower', 960_000, 3378)
    check(not any('مرتفع جداً لأصل' in w for w in ws),
          "tower @ 960K/mo (80×12K): no false warning")

    # Negative side too — tower with absurdly low rent shouldn't be flagged
    # via this check either, since the check is skipped for towers
    ws = warns('tower', 5_000, 3378)
    check(not any('م² سنوياً للأرض' in w for w in ws),
          "tower @ 5K/mo: no rent/m² warning either way (skipped entirely)")

    # Compounds still get warnings when warranted
    ws = warns('compound_large', 5_000_000, 50_000)
    check(any('مرتفع جداً لأصل' in w for w in ws),
          "compound_large @ 1200 QAR/m²: still warns (regression preserved)")

    ws = warns('compound_small', 30_000, 8000)
    check(any('منخفض جداً' in w for w in ws),
          "compound_small @ 45 QAR/m²: still catches single-unit mistake")

    # apartment_building keeps the check (low-rise: plot ≈ BUA)
    ws = warns('apartment_building', 50_000, 600)
    check(any('مرتفع جداً لأصل' in w for w in ws),
          "apartment_building @ 1000 QAR/m²: still warns")

    # Villa never in the check
    ws = warns('standalone_villa', 15_000, 450)
    check(not any('م² سنوياً للأرض' in w for w in ws),
          "standalone_villa: never affected by rent/m² check")

    print()
    print("Source verification:")

    has_correct_list = "'compound_large', 'compound_small', 'apartment_building'" in src
    has_no_tower_in_list = ("'tower'" not in re.search(
        r"asset_type in \([^)]+\)\s+and rental_income",
        src
    ).group(0)) if re.search(r"asset_type in \([^)]+\)\s+and rental_income", src) else False

    check(has_correct_list, "source: tuple lists exactly compound_large/compound_small/apartment_building")
    check(has_no_tower_in_list, "source: 'tower' is NOT in the asset-type tuple")
    check("Sprint 2.16.11" in src, "source: Sprint 2.16.11 carve-out comment present")
    check("SPRINT_TAG = '2.16.11'" in src, "source: SPRINT_TAG bumped to 2.16.11")
    check("sprint2p16p11" in src, "source: ENGINE_VERSION bumped")

    print()
    print(f"Results: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
