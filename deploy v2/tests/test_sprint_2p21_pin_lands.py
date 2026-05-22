"""
tests/test_sprint_2p21_pin_lands.py — Sprint 2.21.0 isolated tests (standalone runner).

Run: python tests/test_sprint_2p21_pin_lands.py

Covers PIN-input-for-lands activation:
  - classify_asset(input_mode='land'): typical sizes -> raw_land; geometric guards
    (>=15000 compound_small, >=50000 compound_large) override the hint
  - input_mode=None -> existing area heuristic UNCHANGED (regression guard)
  - QARS subtype still wins over the land hint
  - API EvaluateRequest/EvaluateDetailsRequest: address XOR pin (422 Arabic)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qatar_gis import classify_asset, AssetType   # noqa: E402

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  ok  {name}")
    else:
        _failed += 1
        print(f"  XX  {name}")


class _Shape:
    def __init__(self, is_rectangular=True, irregularity_warning=None):
        self.is_rectangular = is_rectangular
        self.irregularity_warning = irregularity_warning


class _Plot:
    """Duck-typed PlotInfo (classify_asset only reads these attributes)."""
    def __init__(self, pdarea, pd_no='PD/1/2020', is_unsubdivided=False, rect=True):
        self.pdarea = pdarea
        self.pd_no = pd_no
        self.is_unsubdivided = is_unsubdivided
        self.shape = _Shape(is_rectangular=rect)
        self.polygon_4326 = []


def _at(plot, **kw):
    return classify_asset(plot, **kw).asset_type


# ---- classifier land branch ----

def test_land_hint_typical_sizes():
    for area in (490, 502, 972, 991, 1299):
        check(f"{area} m² + input_mode='land' -> raw_land",
              _at(_Plot(area), input_mode='land') == AssetType.RAW_LAND)


def test_geometric_guards_override_hint():
    check("16,000 m² + land hint -> compound_small (guard)",
          _at(_Plot(16000, is_unsubdivided=True), input_mode='land') == AssetType.COMPOUND_SMALL)
    check("60,000 m² + land hint -> compound_large (guard)",
          _at(_Plot(60000, is_unsubdivided=True), input_mode='land') == AssetType.COMPOUND_LARGE)
    check("14,999 m² + land hint -> raw_land (just below guard)",
          _at(_Plot(14999), input_mode='land') == AssetType.RAW_LAND)


def test_input_mode_none_unchanged():
    # Regression: villa-size parcel with NO hint must still be STANDALONE_VILLA.
    check("502 m² + input_mode=None -> standalone_villa (unchanged)",
          _at(_Plot(502), input_mode=None) == AssetType.STANDALONE_VILLA)
    check("1299 m² + no input_mode arg -> standalone_villa (unchanged)",
          _at(_Plot(1299)) == AssetType.STANDALONE_VILLA)


def test_subtype_wins_over_hint():
    # A mapped QARS subtype must win even if the user used the land tab.
    meta = {'building_subtype': 11}  # Tower
    check("subtype=11 (tower) + land hint -> tower (subtype wins)",
          _at(_Plot(2500), location_metadata=meta, input_mode='land') == AssetType.TOWER)


# ---- API XOR validation ----

def test_api_xor_validation():
    from pydantic import ValidationError
    from api import EvaluateRequest as ER, EvaluateDetailsRequest as EDR
    for Model in (ER, EDR):
        nm = Model.__name__
        check(f"{nm}: pin-only ok", Model(pin='90040668').pin == '90040668')
        check(f"{nm}: address ok", Model(zone=52, street=903, building=90).zone == 52)
        # both -> rejected with Arabic message
        try:
            Model(zone=52, street=903, building=90, pin='90040668')
            check(f"{nm}: both rejected", False)
        except ValidationError as e:
            check(f"{nm}: both rejected (Arabic)", 'العنوان' in str(e.errors()[0]['msg']))
        # neither -> rejected
        try:
            Model()
            check(f"{nm}: neither rejected", False)
        except ValidationError as e:
            check(f"{nm}: neither rejected (Arabic)", 'إما' in str(e.errors()[0]['msg']))
        # bad pin format -> rejected
        try:
            Model(pin='12')
            check(f"{nm}: bad pin rejected", False)
        except ValidationError:
            check(f"{nm}: bad pin format rejected", True)


if __name__ == "__main__":
    print("Sprint 2.21.0 — PIN input for lands isolated tests")
    print("=" * 70)
    test_land_hint_typical_sizes()
    test_geometric_guards_override_hint()
    test_input_mode_none_unchanged()
    test_subtype_wins_over_hint()
    test_api_xor_validation()
    print("=" * 70)
    print(f"Sprint 2.21.0 tests: {_passed} passed, {_failed} failed")
    sys.exit(0 if _failed == 0 else 1)
