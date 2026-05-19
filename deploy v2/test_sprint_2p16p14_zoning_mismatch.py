"""
Sprint 2.16.14 — Zoning/Subtype contradiction tests (Bug A11)
==============================================================

Verifies that classify_asset() now surfaces a non-blocking flag when a
residential BUILDING_NO_SUBTYPE (1=Villa, 6=Flats, 11=Tower) sits inside
a clearly non-residential zone (CCC, COM, CF, SCZ, MU*, etc.).

Reference case: PIN 61050014 (61/875/20) — Public Works Authority
    QARS_Point.BUILDING_NO_SUBTYPE = 6 (Building with Flats)
    QARS_Point.SURVEYED_DATE       = 2010-01-26 (16 years stale)
    Zoning.ZONING                  = CCC (Central Commercial Core)
    Landmarks within 100m          = GOVERNMENT × 2 + FINANCE + SERVICES

Empirical scope (2026-05-19 audit, 22 landmarks):
    Total mismatch rate: 9.1% (2/22) — all in GOVERNMENT category
    BUSINESS:  0/6 (0%)
    FINANCE:   0/8 (0%)
    GOVERNMENT: 2/8 (25%)

Test layout: pure unit tests with no network. Heavy spatial-query tests
live in audit scripts, not regression suite.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qatar_gis import (
    _is_non_residential_zone,
    RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK,
    classify_asset,
    PlotInfo,
    PolygonShape,
    AssetType,
)


# ─────────────────────────────────────────────────────────────────
# Helper: minimal PlotInfo for classifier tests
# ─────────────────────────────────────────────────────────────────

def _make_plot(area: float, pd_no: str = 'PD/890/1997'):
    """Build a PlotInfo with the minimum fields classify_asset reads."""
    shape = PolygonShape(
        vertex_count=4, is_rectangular=True, is_irregular=False,
        convex_hull_ratio=1.0, aspect_ratio=1.0, irregularity_warning=None,
    )
    return PlotInfo(
        pin=61050014, pdarea=area, pd_no=pd_no,
        cdst_key=0, ref_number=None,
        polygon_4326=[], polygon_2932=[],
        bbox_4326=(0.0, 0.0, 0.0, 0.0),
        is_unsubdivided=(pd_no == '0' or pd_no == 0),
        shape=shape,
    )


# ─────────────────────────────────────────────────────────────────
# 1. _is_non_residential_zone helper
# ─────────────────────────────────────────────────────────────────

def test_zoning_helper_recognizes_ccc():
    """CCC = Central Commercial Core → non-residential."""
    assert _is_non_residential_zone('CCC') is True


def test_zoning_helper_recognizes_com():
    """COM = Commercial → non-residential."""
    assert _is_non_residential_zone('COM') is True


def test_zoning_helper_recognizes_cf_scz_tu():
    """CF, SCZ, TU → all non-residential."""
    assert _is_non_residential_zone('CF') is True
    assert _is_non_residential_zone('SCZ') is True
    assert _is_non_residential_zone('TU') is True


def test_zoning_helper_recognizes_mu_prefix():
    """Mixed-Use codes (MU1 G+2, MU2 G+5, MU3 G+3) all lean commercial."""
    assert _is_non_residential_zone('MU1 G+2') is True
    assert _is_non_residential_zone('MU2 G+5') is True
    assert _is_non_residential_zone('MU3 G+3') is True


def test_zoning_helper_rejects_residential():
    """R1, R1-TYP, R2, R3, R5 → all residential (no mismatch)."""
    assert _is_non_residential_zone('R1') is False
    assert _is_non_residential_zone('R1-TYP') is False
    assert _is_non_residential_zone('R2') is False
    assert _is_non_residential_zone('R3') is False
    assert _is_non_residential_zone('R5') is False


def test_zoning_helper_handles_none_and_empty():
    """Defensive: None and empty string never trigger a contradiction."""
    assert _is_non_residential_zone(None) is False
    assert _is_non_residential_zone('') is False
    assert _is_non_residential_zone('   ') is False


def test_zoning_helper_strips_whitespace():
    """Real-world data can have trailing whitespace."""
    assert _is_non_residential_zone(' CCC ') is True


# ─────────────────────────────────────────────────────────────────
# 2. classify_asset — contradiction detection (the actual bug fix)
# ─────────────────────────────────────────────────────────────────

def test_apartment_in_ccc_zone_flags_mismatch():
    """The reference case: أشغال 61/875/20.

    Plot 4,461 m², subtype=6 (Building with Flats), Zoning=CCC.
    Classifier must surface the contradiction without changing asset_type.
    """
    plot = _make_plot(area=4461.0)
    meta = {'building_subtype': 6, 'zoning': 'CCC'}
    result = classify_asset(plot, meta)

    # asset_type stays as apartment_building — we're flagging, not overriding
    assert result.asset_type == AssetType.APARTMENT_BUILDING
    # confidence downgraded
    assert result.confidence == 'medium'
    # flag present with the expected prefix
    assert any('subtype_zoning_mismatch:' in f for f in result.flags), \
        f"Expected mismatch flag, got: {result.flags}"
    # COMMERCIAL surfaced as alternative
    assert AssetType.COMMERCIAL.value in result.alternative_types


def test_villa_in_ccc_zone_flags_mismatch():
    """Subtype=1 (Villa) + Zoning=CCC → also a contradiction."""
    plot = _make_plot(area=600.0)
    meta = {'building_subtype': 1, 'zoning': 'CCC'}
    result = classify_asset(plot, meta)
    assert result.asset_type == AssetType.STANDALONE_VILLA
    assert result.confidence == 'medium'
    assert any('subtype_zoning_mismatch:' in f for f in result.flags)


def test_tower_in_ccc_zone_flags_mismatch():
    """Subtype=11 (Tower) in CCC: common in West Bay government towers.

    Tower in CCC could be either residential luxury (Lusail) or commercial
    (West Bay government). The flag asks the user to confirm.
    """
    plot = _make_plot(area=3378.0)
    meta = {'building_subtype': 11, 'zoning': 'CCC'}
    result = classify_asset(plot, meta)
    assert result.asset_type == AssetType.TOWER
    assert result.confidence == 'medium'
    assert any('subtype_zoning_mismatch:' in f for f in result.flags)


def test_villa_in_r1_zone_no_mismatch():
    """Subtype=1 (Villa) + Zoning=R1 → consistent, no flag."""
    plot = _make_plot(area=600.0)
    meta = {'building_subtype': 1, 'zoning': 'R1'}
    result = classify_asset(plot, meta)
    assert result.asset_type == AssetType.STANDALONE_VILLA
    assert result.confidence == 'high'
    assert not any('subtype_zoning_mismatch:' in f for f in result.flags)
    assert result.alternative_types == []


def test_apartment_in_r1_zone_no_mismatch():
    """Subtype=6 (Flats) + Zoning=R1 → both residential, consistent."""
    plot = _make_plot(area=1200.0)
    meta = {'building_subtype': 6, 'zoning': 'R1'}
    result = classify_asset(plot, meta)
    assert result.asset_type == AssetType.APARTMENT_BUILDING
    assert result.confidence == 'high'
    assert not any('subtype_zoning_mismatch:' in f for f in result.flags)


def test_commercial_subtype_no_check():
    """Subtype=13 (Commercial) is NOT in the residential check set,
    so even in CCC there's no contradiction — the subtype is already
    consistent with the commercial zone."""
    plot = _make_plot(area=2000.0)
    meta = {'building_subtype': 13, 'zoning': 'CCC'}
    result = classify_asset(plot, meta)
    assert result.asset_type == AssetType.COMMERCIAL
    assert result.confidence == 'high'
    assert not any('subtype_zoning_mismatch:' in f for f in result.flags)


def test_shopping_subtype_no_check():
    """Subtype=4 (Shopping Complex) + Zoning=CCC → consistent."""
    plot = _make_plot(area=8000.0)
    meta = {'building_subtype': 4, 'zoning': 'CCC'}
    result = classify_asset(plot, meta)
    assert result.asset_type == AssetType.COMMERCIAL
    assert result.confidence == 'high'
    assert not any('subtype_zoning_mismatch:' in f for f in result.flags)


def test_no_zoning_no_mismatch():
    """When zoning is missing from metadata and lat/lon not provided,
    classifier should not crash and not emit a false-positive flag."""
    plot = _make_plot(area=4461.0)
    meta = {'building_subtype': 6}  # no zoning, no lat/lon
    result = classify_asset(plot, meta)
    # asset_type still gets assigned from subtype
    assert result.asset_type == AssetType.APARTMENT_BUILDING
    # No flag because zoning unknown (we cannot detect mismatch)
    assert not any('subtype_zoning_mismatch:' in f for f in result.flags)


def test_mu_zone_with_apartment_flags_mismatch():
    """MU2 G+5 (Mixed-Use, high-rise) + subtype=6 → leans commercial,
    should flag mismatch."""
    plot = _make_plot(area=2500.0)
    meta = {'building_subtype': 6, 'zoning': 'MU2 G+5'}
    result = classify_asset(plot, meta)
    assert result.asset_type == AssetType.APARTMENT_BUILDING
    assert result.confidence == 'medium'
    assert any('subtype_zoning_mismatch:' in f for f in result.flags)


# ─────────────────────────────────────────────────────────────────
# 3. Backward compat: legacy path (no subtype) unchanged
# ─────────────────────────────────────────────────────────────────

def test_no_subtype_falls_through_to_area_heuristic():
    """When subtype is None (no QARS_Point data), the area-based
    classification still works (legacy behavior preserved)."""
    plot = _make_plot(area=600.0)
    meta = None  # no metadata at all
    result = classify_asset(plot, meta)
    # area-based: 600 m² typical villa, no subtype-induced flag
    assert not any('subtype_zoning_mismatch:' in f for f in result.flags)


def test_subtype_zero_falls_through_to_area_heuristic():
    """subtype=0 means 'unknown' in QARS_Point — also falls through."""
    plot = _make_plot(area=600.0)
    meta = {'building_subtype': 0}
    result = classify_asset(plot, meta)
    assert not any('subtype_zoning_mismatch:' in f for f in result.flags)


# ─────────────────────────────────────────────────────────────────
# 4. RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK constant integrity
# ─────────────────────────────────────────────────────────────────

def test_residential_subtypes_constant_is_frozenset():
    """The constant should be immutable to prevent accidental mutation."""
    assert isinstance(RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK, frozenset)


def test_residential_subtypes_contains_expected_codes():
    """Must include: Villa(1), Building with Flats(6), Tower(11)."""
    assert 1 in RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK
    assert 6 in RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK
    assert 11 in RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK


def test_residential_subtypes_excludes_commercial():
    """Must NOT include: Shopping(4), Commercial(13), Others(99)."""
    assert 4 not in RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK
    assert 13 not in RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK
    assert 99 not in RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK


# ─────────────────────────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    tests = [(name, fn) for name, fn in globals().items()
             if name.startswith('test_') and callable(fn)]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f'  ✓ {name}')
            passed += 1
        except AssertionError as e:
            print(f'  ✗ {name}: {e}')
            failed += 1
        except Exception as e:
            print(f'  ✗ {name}: {type(e).__name__}: {e}')
            failed += 1
    print(f'\n{passed}/{passed+failed} passed')
    sys.exit(0 if failed == 0 else 1)
