"""
Sprint 2.16.10 — Isolated tests for tower rental split.

Covers:
- Pydantic validators on unit_count + avg_monthly_rent_per_unit
- Derivation logic mirror (Python simulation of the engine path)
- Sync check: confirms api.py + evaluate_unified.py carry the right code
"""
import sys
import os
import re
from typing import Optional
from pydantic import BaseModel, Field, ValidationError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── Mirror of api.py constants and models (Sprint 2.16.10) ──
_ASKING_PRICE_MAX = 500_000_000.0
_RENTAL_INCOME_MAX = 10_000_000.0
_UNIT_COUNT_MAX = 500
_PER_UNIT_RENT_MAX = 500_000.0


class EvaluateRequest(BaseModel):
    zone: int
    street: int
    building: int
    audience: Optional[str] = 'buyer'
    asking_price: Optional[float] = Field(default=None, gt=0, lt=_ASKING_PRICE_MAX)
    rental_income: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)
    unit_count: Optional[int] = Field(default=None, gt=0, le=_UNIT_COUNT_MAX)
    avg_monthly_rent_per_unit: Optional[float] = Field(default=None, gt=0, lt=_PER_UNIT_RENT_MAX)


# ── Engine derivation logic mirror ──
OPEX_RATIO = 0.23
CAP_RATE_TOWER = 0.06


def derive_rent(unit_count=None, avg_per_unit=None, rental_income=None):
    """Mirror of evaluate_unified.py:_rent_source block."""
    if unit_count and avg_per_unit:
        derived = unit_count * avg_per_unit
        return derived, 'derived_from_units'
    elif rental_income:
        return rental_income, 'user_total'
    return None, None


def income_value(monthly_rent):
    if not monthly_rent:
        return None
    annual = monthly_rent * 12
    noi = annual * (1 - OPEX_RATIO)
    return round(noi / CAP_RATE_TOWER)


def verify_sync():
    """Verify api.py and evaluate_unified.py carry the Sprint 2.16.10 code."""
    failures = []

    with open('api.py', encoding='utf-8') as f:
        api_src = f.read()
    for expected in [
        '_UNIT_COUNT_MAX = 500',
        '_PER_UNIT_RENT_MAX = 500_000.0',
        'unit_count: Optional[int] = Field(default=None, gt=0, le=_UNIT_COUNT_MAX)',
        'avg_monthly_rent_per_unit: Optional[float] = Field(default=None, gt=0, lt=_PER_UNIT_RENT_MAX)',
        'unit_count=req.unit_count',
        'avg_monthly_rent_per_unit=req.avg_monthly_rent_per_unit',
    ]:
        if expected not in api_src:
            failures.append(f"  api.py: missing {expected}")

    with open('evaluate_unified.py', encoding='utf-8') as f:
        eu_src = f.read()
    for expected in [
        "SPRINT_TAG = '2.16.10'",
        'sprint2p16p10',
        'unit_count: Optional[int] = None',
        'avg_monthly_rent_per_unit: Optional[float] = None',
        '_rent_source = None',
        'derived_from_units',
        'rent_source_ar=_rs_label',
    ]:
        if expected not in eu_src:
            failures.append(f"  evaluate_unified.py: missing {expected}")

    if failures:
        print("\u2717 SYNC FAILED:")
        for f in failures:
            print(f)
        return False
    print("\u2713 api.py + evaluate_unified.py carry Sprint 2.16.10 code")
    return True


def test_pydantic():
    passed = 0
    failed = 0

    def expect_reject(payload, label):
        nonlocal passed, failed
        try:
            EvaluateRequest(**payload)
            print(f"  \u2717 {label}: accepted (should reject)")
            failed += 1
        except ValidationError:
            print(f"  \u2713 {label}")
            passed += 1

    def expect_accept(payload, label):
        nonlocal passed, failed
        try:
            EvaluateRequest(**payload)
            print(f"  \u2713 {label}")
            passed += 1
        except ValidationError as e:
            print(f"  \u2717 {label}: rejected ({e})")
            failed += 1

    base = {"zone": 69, "street": 305, "building": 201}

    print("Pydantic validators on unit_count:")
    expect_reject({**base, "unit_count": 0}, "unit_count=0 -> 422")
    expect_reject({**base, "unit_count": -5}, "unit_count=-5 -> 422")
    expect_reject({**base, "unit_count": 501}, "unit_count=501 (over ceiling) -> 422")
    expect_accept({**base, "unit_count": 1}, "unit_count=1 (minimum)")
    expect_accept({**base, "unit_count": 80}, "unit_count=80 (typical Lusail)")
    expect_accept({**base, "unit_count": 500}, "unit_count=500 (ceiling)")

    print()
    print("Pydantic validators on avg_monthly_rent_per_unit:")
    expect_reject({**base, "avg_monthly_rent_per_unit": 0}, "avg=0 -> 422")
    expect_reject({**base, "avg_monthly_rent_per_unit": -100}, "avg=-100 -> 422")
    expect_reject({**base, "avg_monthly_rent_per_unit": 500_000}, "avg=500K (at ceiling) -> 422")
    expect_accept({**base, "avg_monthly_rent_per_unit": 1}, "avg=1 (positive)")
    expect_accept({**base, "avg_monthly_rent_per_unit": 12_000}, "avg=12K (typical)")
    expect_accept({**base, "avg_monthly_rent_per_unit": 25_000}, "avg=25K (Pearl premium)")

    print()
    print("Pydantic — backward compat (omitted fields):")
    expect_accept({**base}, "no rental fields at all")
    expect_accept({**base, "rental_income": 30_000}, "only rental_income (legacy)")
    expect_accept({**base, "unit_count": 80, "avg_monthly_rent_per_unit": 12_000}, "only the new pair")
    expect_accept({**base, "rental_income": 30_000, "unit_count": 80, "avg_monthly_rent_per_unit": 12_000}, "all three together")

    return passed, failed


def test_derivation():
    passed = 0
    failed = 0

    print("Derivation logic (matches engine):")

    # The bug being fixed
    rent, src = derive_rent(rental_income=30_000)
    v = income_value(rent)
    if v == 4_620_000 and src == 'user_total':
        print(f"  \u2713 yesterday's bug: 30K rental_income -> 4.62M (user_total path)")
        passed += 1
    else:
        print(f"  \u2717 unexpected: rental_income=30K gave {v}, src={src}")
        failed += 1

    # The fix
    rent, src = derive_rent(unit_count=80, avg_per_unit=12_000)
    v = income_value(rent)
    if v == 147_840_000 and src == 'derived_from_units':
        print(f"  \u2713 the fix: 80 units * 12K -> 147.84M (derived path)")
        passed += 1
    else:
        print(f"  \u2717 unexpected: pair gave {v}, src={src}")
        failed += 1

    # Pair wins over rental_income
    rent, src = derive_rent(unit_count=80, avg_per_unit=12_000, rental_income=999)
    if rent == 960_000 and src == 'derived_from_units':
        print(f"  \u2713 pair wins over rental_income when both present")
        passed += 1
    else:
        print(f"  \u2717 pair didn't win: got {rent}, {src}")
        failed += 1

    # Incomplete pair falls back to rental_income
    rent, src = derive_rent(unit_count=80, rental_income=20_000)
    if rent == 20_000 and src == 'user_total':
        print(f"  \u2713 incomplete pair (only unit_count) -> rental_income wins")
        passed += 1
    else:
        print(f"  \u2717 fallback failed: got {rent}, {src}")
        failed += 1

    # Empty -> None
    rent, src = derive_rent()
    if rent is None and src is None:
        print(f"  \u2713 no inputs -> None (insufficient_data path triggered)")
        passed += 1
    else:
        failed += 1

    # Bounds sanity: typical Lusail tower valuation range
    for uc, apu in [(60, 12_000), (100, 15_000), (120, 18_000)]:
        v = income_value(derive_rent(unit_count=uc, avg_per_unit=apu)[0])
        print(f"      [reference] {uc} units × {apu:,}/month -> {v:,} QAR")

    return passed, failed


if __name__ == "__main__":
    print()
    ok_sync = verify_sync()
    print()
    print("=" * 70)
    p1, f1 = test_pydantic()
    print()
    print("=" * 70)
    p2, f2 = test_derivation()
    print()
    print("=" * 70)
    total_pass = p1 + p2
    total_fail = f1 + f2
    print(f"Pydantic: {p1} passed, {f1} failed")
    print(f"Derivation: {p2} passed, {f2} failed")
    print(f"Sync: {'pass' if ok_sync else 'FAIL'}")
    print(f"Total: {total_pass} passed, {total_fail} failed")
    sys.exit(0 if (total_fail == 0 and ok_sync) else 1)
