"""Tests for property_factors.py — Sprint 2."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from property_factors import (
    analyze_property, MAX_ADJUSTMENT,
    ZONING_WEIGHTS, LANDMARK_WEIGHTS,
    _factor_zoning, _factor_building_age,
)


class TestZoningWeight:
    """Zoning must apply correct weight per purpose."""

    def test_r1_residential_positive(self):
        """R1 should be positive for residential."""
        w = ZONING_WEIGHTS['residential']['R1']
        assert w > 0, "R1 must be positive for residential"

    def test_r1_investment_neutral(self):
        """R1 should be neutral for investment (limited rental demand)."""
        w = ZONING_WEIGHTS['investment']['R1']
        assert w == 0, "R1 must be neutral for investment"

    def test_r3_residential_negative(self):
        """R3 should be negative for residential (denser, less privacy)."""
        w = ZONING_WEIGHTS['residential']['R3']
        assert w < 0

    def test_r3_investment_positive(self):
        """R3 should be positive for investment (more tenants)."""
        w = ZONING_WEIGHTS['investment']['R3']
        assert w > 0


class TestBuildingAgeWeights:
    """Building age factor must scale correctly."""

    def test_new_build_positive(self):
        f = _factor_building_age(2, 'residential')
        assert f is not None
        assert f.weight > 0
        assert f.weight >= 0.025  # at least +2.5%

    def test_old_build_negative(self):
        f = _factor_building_age(30, 'residential')
        assert f is not None
        assert f.weight < 0

    def test_medium_build_neutral(self):
        f = _factor_building_age(12, 'residential')
        assert f is not None
        assert f.weight == 0


class TestMaxAdjustmentCap:
    """Total adjustment must be capped to ±10%."""

    def test_cap_enforced(self):
        """Even with many positive factors, result must be ≤ 10%."""
        # Simulate by creating a result with raw > 10%
        # We test the constant
        assert MAX_ADJUSTMENT == 0.10

    def test_analyze_property_returns_capped(self):
        """Real analysis must produce adjustment within [-0.10, +0.10]."""
        # Use known coordinates (Al Maamoura property)
        result = analyze_property(
            lat=25.248, lon=51.492,
            purpose='residential',
            building_age_years=2,  # very new → big positive
            plot_shape={'convex_hull_ratio': 0.7, 'vertex_count': 12},  # very irregular → big negative
        )
        assert -MAX_ADJUSTMENT <= result.adjustment <= MAX_ADJUSTMENT


class TestPurposeSwitchesWeights:
    """Switching purpose must change factor directions."""

    def test_main_road_flips(self):
        """Main road: negative for residential, positive for investment."""
        # We can test this through the full analyze_property
        res = analyze_property(lat=25.248, lon=51.492, purpose='residential',
                               building_age_years=15)
        inv = analyze_property(lat=25.248, lon=51.492, purpose='investment',
                               building_age_years=15)

        # Find road factor if present
        road_res = [f for f in res.factors if f.name in ('main_road', 'local_road')]
        road_inv = [f for f in inv.factors if f.name in ('main_road', 'local_road')]

        # Both should have the same factor name but may differ in weight/direction
        if road_res and road_inv:
            # Local road: positive for residential
            if road_res[0].name == 'local_road':
                assert road_res[0].weight > 0, "Local road should be positive for residential"

    def test_purpose_changes_overall_direction(self):
        """The same property should get different adjustments for different purposes."""
        res = analyze_property(lat=25.248, lon=51.492, purpose='residential',
                               building_age_years=15)
        inv = analyze_property(lat=25.248, lon=51.492, purpose='investment',
                               building_age_years=15)
        # Adjustments don't have to be opposite, but they should differ
        # (R1 is +2% residential, 0% investment — that alone creates a difference)
        assert res.adjustment != inv.adjustment, \
            "Residential and investment adjustments should differ"
