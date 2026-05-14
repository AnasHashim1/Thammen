"""
Tests for market_regime.py — Sprint 2.14

Run as:  python test_market_regime.py
Or:      pytest test_market_regime.py -v
"""

import unittest
from datetime import date

from market_regime import (
    CURRENT_REGIME,
    NORMAL_REGIME,
    current_regime,
    regime_recommendation,
    regime_to_dict,
    recommendation_to_dict,
)


class TestCurrentRegimeShape(unittest.TestCase):
    """The active regime must have specific properties for Sprint 2.14."""

    def test_active_regime_is_post_disruption(self):
        self.assertEqual(current_regime.label_en, 'post_disruption_recession')

    def test_active_since_matches_war_start(self):
        self.assertEqual(current_regime.active_since, date(2026, 2, 28))

    def test_moj_data_predates_regime(self):
        self.assertTrue(current_regime.moj_data_predates_regime)
        self.assertLess(
            current_regime.moj_last_known_date,
            current_regime.active_since,
            'MoJ snapshot must predate regime start by definition',
        )

    def test_shock_layers_present(self):
        # We expect at least: post-WC, war/Hormuz, population, volume
        self.assertGreaterEqual(len(current_regime.shock_layers), 4)
        layer_types = {s.type for s in current_regime.shock_layers}
        self.assertIn('structural', layer_types)
        self.assertIn('demographic', layer_types)
        self.assertIn('cyclical', layer_types)

    def test_war_layer_has_expected_duration(self):
        war_layer = next(
            s for s in current_regime.shock_layers if s.type == 'structural'
        )
        # QatarEnergy estimated 5 years for LNG capacity restoration
        self.assertIsNotNone(war_layer.expected_duration_ar)
        self.assertIn('5', war_layer.expected_duration_ar)


class TestCalibrationConstants(unittest.TestCase):
    """Adjustments must follow the derivation in the module docstring."""

    def test_current_default_ceiling_below_normal(self):
        """Regime ceiling for new property = MoJ × 1.00 (was 1.10 pre-war)."""
        self.assertEqual(
            CURRENT_REGIME.buyer_ceiling_multiplier_default, 1.00
        )
        self.assertEqual(
            NORMAL_REGIME.buyer_ceiling_multiplier_default, 1.10
        )

    def test_old_property_ceiling_below_default(self):
        """Old properties take additional hit per user testimony."""
        self.assertLess(
            CURRENT_REGIME.buyer_ceiling_multiplier_old,
            CURRENT_REGIME.buyer_ceiling_multiplier_default,
        )

    def test_opening_offer_leaves_negotiation_room(self):
        """Opening offer must be lower than the ceiling, both for default
        and old properties."""
        self.assertLess(
            CURRENT_REGIME.opening_offer_multiplier_default,
            CURRENT_REGIME.buyer_ceiling_multiplier_default,
        )
        self.assertLess(
            CURRENT_REGIME.opening_offer_multiplier_old,
            CURRENT_REGIME.buyer_ceiling_multiplier_old,
        )

    def test_old_age_threshold_matches_section_10yr_rule(self):
        """Project Instructions Section 4: 'villas > 10 years and not luxury
        → market price ≈ land value + 0–10%'."""
        self.assertEqual(CURRENT_REGIME.old_property_age_threshold, 10)


class TestRecommendationForNewVilla(unittest.TestCase):
    """Property < 10 years old, current regime."""

    def setUp(self):
        self.rec = regime_recommendation(
            moj_median_per_m2=3000,
            plot_area_m2=600,
            building_age_years=5,
        )

    def test_ceiling_is_moj_times_1_00(self):
        # 3000 × 600 × 1.00 = 1,800,000
        self.assertEqual(self.rec.buyer_ceiling_qar, 1_800_000)

    def test_opening_is_moj_times_0_90(self):
        # 3000 × 600 × 0.90 = 1,620,000
        self.assertEqual(self.rec.opening_offer_qar, 1_620_000)

    def test_negotiation_room_is_difference(self):
        self.assertEqual(
            self.rec.negotiation_room_qar,
            self.rec.buyer_ceiling_qar - self.rec.opening_offer_qar,
        )

    def test_not_classified_as_old(self):
        self.assertFalse(self.rec.is_old_property)

    def test_includes_moj_lag_warning(self):
        self.assertIsNotNone(self.rec.moj_lag_warning_ar)
        self.assertIn('2025', self.rec.moj_lag_warning_ar)


class TestRecommendationForOldProperty(unittest.TestCase):
    """Property ≥ 10 years old — gets the additional 5pp drop."""

    def setUp(self):
        self.rec = regime_recommendation(
            moj_median_per_m2=3000,
            plot_area_m2=600,
            building_age_years=15,
        )

    def test_ceiling_is_moj_times_0_95(self):
        # 3000 × 600 × 0.95 = 1,710,000
        self.assertEqual(self.rec.buyer_ceiling_qar, 1_710_000)

    def test_opening_is_moj_times_0_85(self):
        # 3000 × 600 × 0.85 = 1,530,000
        self.assertEqual(self.rec.opening_offer_qar, 1_530_000)

    def test_classified_as_old(self):
        self.assertTrue(self.rec.is_old_property)

    def test_adjustments_mention_age(self):
        joined = ' '.join(self.rec.adjustments_applied_ar)
        self.assertIn('15', joined)
        self.assertIn('عمر المبنى', joined)


class TestBoundaryAge(unittest.TestCase):
    """Exactly at the threshold (10 years) classifies as old."""

    def test_exactly_10_years_is_old(self):
        rec = regime_recommendation(
            moj_median_per_m2=3000,
            plot_area_m2=600,
            building_age_years=10,
        )
        self.assertTrue(rec.is_old_property)

    def test_9_years_is_not_old(self):
        rec = regime_recommendation(
            moj_median_per_m2=3000,
            plot_area_m2=600,
            building_age_years=9,
        )
        self.assertFalse(rec.is_old_property)


class TestRawLandNoAge(unittest.TestCase):
    """When building_age_years is None (raw land), use default multipliers."""

    def setUp(self):
        self.rec = regime_recommendation(
            moj_median_per_m2=3500,
            plot_area_m2=800,
            building_age_years=None,
        )

    def test_uses_default_multipliers(self):
        self.assertEqual(self.rec.buyer_ceiling_qar, 2_800_000)
        self.assertEqual(self.rec.opening_offer_qar, 2_520_000)

    def test_not_classified_as_old(self):
        self.assertFalse(self.rec.is_old_property)

    def test_warns_about_unknown_age(self):
        joined = ' '.join(self.rec.adjustments_applied_ar)
        self.assertIn('غير محدد', joined)


class TestNormalRegimeFallback(unittest.TestCase):
    """When NORMAL_REGIME is active (future state), adjustments revert."""

    def test_normal_ceiling_for_new_property(self):
        rec = regime_recommendation(
            moj_median_per_m2=3000, plot_area_m2=600,
            building_age_years=5, regime=NORMAL_REGIME,
        )
        # 3000 × 600 × 1.10 = 1,980,000
        self.assertEqual(rec.buyer_ceiling_qar, 1_980_000)

    def test_normal_has_no_moj_lag_warning(self):
        rec = regime_recommendation(
            moj_median_per_m2=3000, plot_area_m2=600,
            building_age_years=5, regime=NORMAL_REGIME,
        )
        self.assertIsNone(rec.moj_lag_warning_ar)

    def test_normal_has_empty_shock_layers(self):
        self.assertEqual(NORMAL_REGIME.shock_layers, ())


class TestInputValidation(unittest.TestCase):
    """Reject pathological inputs."""

    def test_zero_moj_median_raises(self):
        with self.assertRaises(ValueError):
            regime_recommendation(moj_median_per_m2=0, plot_area_m2=600)

    def test_negative_moj_median_raises(self):
        with self.assertRaises(ValueError):
            regime_recommendation(moj_median_per_m2=-100, plot_area_m2=600)

    def test_zero_plot_area_raises(self):
        with self.assertRaises(ValueError):
            regime_recommendation(moj_median_per_m2=3000, plot_area_m2=0)

    def test_none_moj_raises_with_clear_message(self):
        with self.assertRaises(ValueError) as ctx:
            regime_recommendation(moj_median_per_m2=None, plot_area_m2=600)
        self.assertIn('insufficient', str(ctx.exception))


class TestSerialization(unittest.TestCase):
    """API-shape dicts must contain expected keys for frontend rendering."""

    def test_regime_dict_keys(self):
        d = regime_to_dict()
        for key in ('label_en', 'label_ar', 'active_since',
                    'moj_data_predates_regime', 'moj_last_known_date',
                    'shock_layers', 'calibration'):
            self.assertIn(key, d)

    def test_regime_dict_shock_layers_have_evidence(self):
        d = regime_to_dict()
        for layer in d['shock_layers']:
            self.assertIn('name_ar', layer)
            self.assertIn('evidence_ar', layer)
            self.assertIn('type', layer)
            self.assertTrue(len(layer['evidence_ar']) > 30,
                            'evidence should be substantive')

    def test_regime_dict_serializes_dates_as_iso(self):
        d = regime_to_dict()
        # Should parse back successfully
        date.fromisoformat(d['active_since'])
        date.fromisoformat(d['moj_last_known_date'])
        for layer in d['shock_layers']:
            date.fromisoformat(layer['active_since'])

    def test_recommendation_dict_keys(self):
        rec = regime_recommendation(
            moj_median_per_m2=3000, plot_area_m2=600, building_age_years=15
        )
        d = recommendation_to_dict(rec)
        for key in ('buyer_ceiling_qar', 'opening_offer_qar',
                    'negotiation_room_qar', 'regime_label_ar',
                    'is_old_property', 'adjustments_applied_ar',
                    'shock_layer_names_ar', 'moj_lag_warning_ar'):
            self.assertIn(key, d)


class TestRealWorldScenarios(unittest.TestCase):
    """Sanity checks against the worked examples in our discussion with Anas."""

    def test_anas_3M_listing_old_property(self):
        """Anas's testimony: 3M listing → 2.75M transact for old property.

        That implies MoJ × 1.10 ≈ 2.75M, so MoJ × plot ≈ 2.50M.
        With our current-regime old-property ceiling (MoJ × 0.95),
        the same property should now ceiling at 2.50M × 0.95 = 2.375M.
        Opening offer should be 2.50M × 0.85 = 2.125M.
        """
        # Reverse-engineer: assume MoJ × plot = 2,500,000
        # (3000 QAR/m² × 833 m² ≈ 2.5M)
        rec = regime_recommendation(
            moj_median_per_m2=3000,
            plot_area_m2=833,
            building_age_years=15,
        )
        # Ceiling should be 2,500,000 × 0.95 = 2,375,000 (rounded to 1000)
        self.assertAlmostEqual(
            rec.buyer_ceiling_qar, 2_375_000, delta=2_000
        )
        # Opening should be 2,500,000 × 0.85 = 2,125,000
        self.assertAlmostEqual(
            rec.opening_offer_qar, 2_125_000, delta=2_000
        )
        # Compared to the 3M asking, ceiling is ~21% below asking.
        # That's more aggressive than Anas's 8.3% example because:
        # (a) regime adjustment (-10pp from pre-war 1.10)
        # (b) old-property adjustment (-5pp additional)
        # Verifies that our calibration matches the doc-header derivation.

    def test_negotiation_room_is_meaningful(self):
        """For any non-pathological input, negotiation room should be
        at least 5% of the ceiling."""
        rec = regime_recommendation(
            moj_median_per_m2=3000, plot_area_m2=600, building_age_years=5
        )
        ratio = rec.negotiation_room_qar / rec.buyer_ceiling_qar
        self.assertGreaterEqual(ratio, 0.05)


if __name__ == '__main__':
    unittest.main(verbosity=2)
