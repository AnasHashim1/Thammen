"""
Sprint 2.16.7 — Isolated logic tests for new Pydantic validators.

Self-contained: redefines the Request models with the exact same Field
constraints as api.py, then exercises them. The sync_check() function
reads api.py and asserts the constraints there match this file, so this
test will catch drift if api.py is edited without updating the test.
"""
import sys
from typing import Optional
from pydantic import BaseModel, Field, ValidationError


# ── Mirror of api.py constants and models (Sprint 2.16.7) ──
_ASKING_PRICE_MAX = 500_000_000.0
_RENTAL_INCOME_MAX = 10_000_000.0


class EvaluateRequest(BaseModel):
    zone: int
    street: int
    building: int
    audience: Optional[str] = 'buyer'
    asking_price: Optional[float] = Field(default=None, gt=0, lt=_ASKING_PRICE_MAX)
    rental_income: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)


class EvaluateDetailsRequest(BaseModel):
    zone: int
    street: int
    building: int
    audience: Optional[str] = 'buyer'
    floors: Optional[int] = None
    annexes: Optional[int] = None
    condition: Optional[str] = None
    asking_price: Optional[float] = Field(default=None, gt=0, lt=_ASKING_PRICE_MAX)
    rental_income: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)
    potential_rental: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)
    basement: Optional[bool] = None
    footprint_m2: Optional[float] = None
    external_majlis: Optional[bool] = None
    building_age_years: Optional[int] = None
    is_luxury: Optional[bool] = None


def verify_against_source():
    """Read api.py and confirm Field constraints + B2 wiring match this test."""
    import re
    with open('api.py', encoding='utf-8') as f:
        src = f.read()

    expected = [
        "asking_price: Optional[float] = Field(default=None, gt=0, lt=_ASKING_PRICE_MAX)",
        "rental_income: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)",
        "potential_rental: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)",
        "_ASKING_PRICE_MAX = 500_000_000.0",
        "_RENTAL_INCOME_MAX = 10_000_000.0",
    ]
    missing = [e for e in expected if e not in src]
    if missing:
        print("\u2717 SYNC FAILED:")
        for m in missing:
            print(f"  missing: {m}")
        return False

    er_block = re.search(r'class EvaluateRequest\(BaseModel\):(.*?)(?=class |\Z)', src, re.DOTALL)
    if not er_block or 'asking_price' not in er_block.group(1) or 'rental_income' not in er_block.group(1):
        print("\u2717 B2 not applied: EvaluateRequest missing asking_price/rental_income")
        return False

    print("\u2713 api.py source matches test definitions (B2 wiring + validators)")
    return True


def test_models():
    passed = 0
    failed = 0

    def expect_reject(model_cls, payload, label):
        nonlocal passed, failed
        try:
            model_cls(**payload)
            print(f"  \u2717 {label}: should have rejected, was accepted")
            failed += 1
        except ValidationError:
            print(f"  \u2713 {label}")
            passed += 1

    def expect_accept(model_cls, payload, label):
        nonlocal passed, failed
        try:
            model_cls(**payload)
            print(f"  \u2713 {label}")
            passed += 1
        except ValidationError as e:
            print(f"  \u2717 {label}: should have accepted, got {e}")
            failed += 1

    base = {"zone": 69, "street": 305, "building": 201}

    print("=" * 70)
    print("Bug A3: /api/evaluate/details asking_price validation")
    print("=" * 70)
    expect_reject(EvaluateDetailsRequest, {**base, "asking_price": 0}, "asking_price=0 -> 422")
    expect_reject(EvaluateDetailsRequest, {**base, "asking_price": -1_000_000}, "asking_price=-1M -> 422")
    expect_reject(EvaluateDetailsRequest, {**base, "asking_price": 500_000_000}, "asking_price=500M (at ceiling) -> 422")
    expect_reject(EvaluateDetailsRequest, {**base, "asking_price": 600_000_000}, "asking_price=600M -> 422")
    expect_accept(EvaluateDetailsRequest, {**base, "asking_price": 1}, "asking_price=1 (positive)")
    expect_accept(EvaluateDetailsRequest, {**base, "asking_price": 4_500_000}, "asking_price=4.5M (typical villa)")
    expect_accept(EvaluateDetailsRequest, {**base, "asking_price": 280_000_000}, "asking_price=280M (Com-31 tower)")
    expect_accept(EvaluateDetailsRequest, {**base}, "asking_price missing (Optional)")

    print()
    print("=" * 70)
    print("Bug A4: rental_income validation")
    print("=" * 70)
    expect_reject(EvaluateDetailsRequest, {**base, "rental_income": -1000}, "rental_income=-1000 -> 422")
    expect_reject(EvaluateDetailsRequest, {**base, "rental_income": 10_000_000}, "rental_income=10M (at ceiling) -> 422")
    expect_accept(EvaluateDetailsRequest, {**base, "rental_income": 0}, "rental_income=0 (vacant)")
    expect_accept(EvaluateDetailsRequest, {**base, "rental_income": 15_000}, "rental_income=15K (typical villa)")
    expect_accept(EvaluateDetailsRequest, {**base, "rental_income": 1_500_000}, "rental_income=1.5M (large compound)")

    print()
    print("=" * 70)
    print("Bug A4: potential_rental validation")
    print("=" * 70)
    expect_reject(EvaluateDetailsRequest, {**base, "potential_rental": -500}, "potential_rental=-500 -> 422")
    expect_accept(EvaluateDetailsRequest, {**base, "potential_rental": 0}, "potential_rental=0")
    expect_accept(EvaluateDetailsRequest, {**base, "potential_rental": 18_000}, "potential_rental=18K")

    print()
    print("=" * 70)
    print("Bug B2: /api/evaluate accepts asking_price + rental_income")
    print("=" * 70)
    expect_accept(EvaluateRequest, {**base, "asking_price": 5_000_000}, "EvaluateRequest w/ asking_price=5M")
    expect_accept(EvaluateRequest, {**base, "rental_income": 30_000}, "EvaluateRequest w/ rental_income=30K")
    expect_accept(EvaluateRequest, {**base, "asking_price": 5_000_000, "rental_income": 30_000}, "EvaluateRequest w/ both")
    expect_accept(EvaluateRequest, {**base}, "EvaluateRequest w/ neither (backward compat)")
    expect_reject(EvaluateRequest, {**base, "asking_price": -1}, "EvaluateRequest w/ asking_price=-1 -> 422")
    expect_reject(EvaluateRequest, {**base, "asking_price": 0}, "EvaluateRequest w/ asking_price=0 -> 422")

    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    print()
    sync_ok = verify_against_source()
    print()
    test_ok = test_models()
    sys.exit(0 if (sync_ok and test_ok) else 1)
