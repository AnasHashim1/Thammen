"""
Sprint 2.16.15 — Bug A2 fix: Pydantic extra='forbid'.

Before this patch, EvaluateRequest and EvaluateDetailsRequest used Pydantic's
default `extra='ignore'`. A user POSTing `{"zone":51,"street":835,"building":17,
"rental_inome":30000}` (note the typo) had `rental_inome` silently dropped, and
the engine ran with rental_income=None — producing an "insufficient data" fast
path while the user believed their input was honored.

After this patch, unknown fields raise HTTP 422 at the API boundary.

These tests reconstruct minimal copies of the two models against the same
Pydantic version (2.13+) the production api.py uses. We avoid importing api.py
directly because it pulls FastAPI + the full engine.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows console: ensure UTF-8 output so ✓/✗ render in cmd/PowerShell.
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, ValidationError


# Replicate the constants used by api.py (Sprint 2.16.7) so the test models
# behave identically to production at the field level.
_ASKING_PRICE_MAX = 500_000_000.0
_RENTAL_INCOME_MAX = 5_000_000.0
_UNIT_COUNT_MAX = 500
_PER_UNIT_RENT_MAX = 500_000.0


class _EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    zone: int
    street: int
    building: int
    audience: Optional[str] = 'buyer'
    asking_price: Optional[float] = Field(default=None, gt=0, lt=_ASKING_PRICE_MAX)
    rental_income: Optional[float] = Field(default=None, ge=0, lt=_RENTAL_INCOME_MAX)
    unit_count: Optional[int] = Field(default=None, gt=0, le=_UNIT_COUNT_MAX)
    avg_monthly_rent_per_unit: Optional[float] = Field(default=None, gt=0, lt=_PER_UNIT_RENT_MAX)


class _EvaluateDetailsRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

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
    unit_count: Optional[int] = Field(default=None, gt=0, le=_UNIT_COUNT_MAX)
    avg_monthly_rent_per_unit: Optional[float] = Field(default=None, gt=0, lt=_PER_UNIT_RENT_MAX)
    basement: Optional[bool] = None
    footprint_m2: Optional[float] = None
    external_majlis: Optional[bool] = None
    building_age_years: Optional[int] = None
    is_luxury: Optional[bool] = None


_passed = 0
_failed = 0


def _accept(model_cls, payload, label):
    global _passed, _failed
    try:
        model_cls(**payload)
        print(f"  ✓ {label}")
        _passed += 1
    except ValidationError as e:
        print(f"  ✗ {label} (got ValidationError: {e})")
        _failed += 1


def _reject(model_cls, payload, label, bad_field):
    global _passed, _failed
    try:
        model_cls(**payload)
        print(f"  ✗ {label} (was accepted — A2 still open)")
        _failed += 1
    except ValidationError as e:
        # Pydantic v2 emits {"type":"extra_forbidden","loc":["bad_field"], ...}
        # for forbidden fields. Confirm the rejection cites the unknown key
        # by name (so a typo error message actually points the user at the typo).
        errs = e.errors()
        types = [er.get('type') for er in errs]
        locs = [er.get('loc')[-1] if er.get('loc') else None for er in errs]
        if 'extra_forbidden' in types and bad_field in locs:
            print(f"  ✓ {label}")
            _passed += 1
        else:
            print(f"  ✗ {label} (rejected, but not as extra_forbidden on {bad_field!r}: types={types} locs={locs})")
            _failed += 1


def test_a2_evaluate_request():
    print("A2 / EvaluateRequest — legal fields must still be accepted:")
    _accept(_EvaluateRequest,
            {'zone': 51, 'street': 835, 'building': 17},
            "minimal: zone+street+building")
    _accept(_EvaluateRequest,
            {'zone': 51, 'street': 835, 'building': 17,
             'asking_price': 3_500_000, 'rental_income': 15_000},
            "with asking_price + rental_income")
    _accept(_EvaluateRequest,
            {'zone': 70, 'street': 903, 'building': 90,
             'unit_count': 80, 'avg_monthly_rent_per_unit': 12_000},
            "with unit_count + per_unit (Sprint 2.16.10 tower path)")
    _accept(_EvaluateRequest,
            {'zone': 51, 'street': 835, 'building': 17, 'audience': 'investor'},
            "with audience=investor")

    print()
    print("A2 / EvaluateRequest — unknown fields must be rejected (HTTP 422):")
    # The canonical typo from the bug report
    _reject(_EvaluateRequest,
            {'zone': 51, 'street': 835, 'building': 17, 'rental_inome': 15_000},
            "typo: rental_inome (the catalogued A2 case)",
            'rental_inome')
    # English drift between UI and API
    _reject(_EvaluateRequest,
            {'zone': 51, 'street': 835, 'building': 17, 'listing_price': 3_500_000},
            "drift: listing_price (UI name) vs asking_price (API name)",
            'listing_price')
    # Arabic field name accidentally sent
    _reject(_EvaluateRequest,
            {'zone': 51, 'street': 835, 'building': 17, 'الإيجار': 15_000},
            "Arabic field name leak: الإيجار",
            'الإيجار')
    # Out-of-scope field that belongs to /api/evaluate/details
    _reject(_EvaluateRequest,
            {'zone': 51, 'street': 835, 'building': 17, 'floors': 2},
            "wrong endpoint: floors on /api/evaluate (belongs to /details)",
            'floors')
    # Valid + invalid mixed — the legal fields are not enough to pass
    _reject(_EvaluateRequest,
            {'zone': 51, 'street': 835, 'building': 17,
             'asking_price': 3_500_000, 'extra_param': 'x'},
            "mixed: legal fields + 1 extra → still rejected",
            'extra_param')


def test_a2_evaluate_details_request():
    print()
    print("A2 / EvaluateDetailsRequest — legal fields must still be accepted:")
    _accept(_EvaluateDetailsRequest,
            {'zone': 51, 'street': 835, 'building': 17,
             'floors': 2, 'condition': 'good', 'annexes': 1,
             'basement': True, 'building_age_years': 8, 'is_luxury': False},
            "full villa input (Sprint 2.2/2.3)")
    _accept(_EvaluateDetailsRequest,
            {'zone': 61, 'street': 875, 'building': 20,
             'unit_count': 80, 'avg_monthly_rent_per_unit': 12_000,
             'audience': 'investor'},
            "tower input (Sprint 2.16.10)")

    print()
    print("A2 / EvaluateDetailsRequest — unknown fields must be rejected:")
    _reject(_EvaluateDetailsRequest,
            {'zone': 51, 'street': 835, 'building': 17, 'rental_inome': 15_000},
            "same typo on /details endpoint",
            'rental_inome')
    _reject(_EvaluateDetailsRequest,
            {'zone': 51, 'street': 835, 'building': 17,
             'floors': 2, 'random_param': True},
            "unknown random_param on /details",
            'random_param')


def test_a2_error_message_quality():
    """The rejection must name the bad field so users can correct the typo.

    Without this, a user sees "validation error" with no hint of which field
    they got wrong — defeating most of A2's value.
    """
    print()
    print("A2 / Error message must name the unknown field:")
    try:
        _EvaluateRequest(zone=51, street=835, building=17, rental_inome=15_000)
        global _failed
        _failed += 1
        print("  ✗ expected ValidationError, got accepted")
        return
    except ValidationError as e:
        msg = str(e)
        global _passed
        if 'rental_inome' in msg:
            print(f"  ✓ ValidationError message names 'rental_inome'")
            _passed += 1
        else:
            print(f"  ✗ ValidationError does NOT name the bad field. msg={msg!r}")
            _failed += 1


if __name__ == '__main__':
    print("Sprint 2.16.15 — Bug A2 (Pydantic extra='forbid') isolated tests")
    print("=" * 70)
    test_a2_evaluate_request()
    test_a2_evaluate_details_request()
    test_a2_error_message_quality()
    print("=" * 70)
    print(f"Sprint 2.16.15 A2 tests: {_passed} passed, {_failed} failed")
    sys.exit(0 if _failed == 0 else 1)
