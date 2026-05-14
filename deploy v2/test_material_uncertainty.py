"""Tests for material_uncertainty.py — Sprint 2.14.0 MUC extension

Run as:  python test_material_uncertainty.py
"""

import unittest

from material_uncertainty import (
    assess_uncertainty,
    regime_muc,
    UncertaintyLevel,
)
from market_regime import CURRENT_REGIME, NORMAL_REGIME


class TestRegimeMucCurrent(unittest.TestCase):
    """MUC generation with the active regime (post_disruption_recession)."""

    def setUp(self):
        self.muc = regime_muc(CURRENT_REGIME)

    def test_muc_clause_is_populated(self):
        self.assertIsNotNone(self.muc['muc_clause_ar'])
        self.assertIsNotNone(self.muc['muc_clause_en'])

    def test_clause_mentions_rics_vps_5(self):
        self.assertIn('VPS 5', self.muc['muc_clause_ar'])
        self.assertIn('VPS 5', self.muc['muc_clause_en'])

    def test_clause_mentions_higher_caution(self):
        # The standard RICS phrase: "less certainty — and higher caution"
        self.assertIn('حذر أعلى', self.muc['muc_clause_ar'])
        self.assertIn('higher degree of caution', self.muc['muc_clause_en'])

    def test_clause_recommends_review(self):
        # VPS 5 requires "kept under frequent review"
        self.assertIn('مراجعة', self.muc['muc_clause_ar'])
        self.assertIn('review', self.muc['muc_clause_en'])

    def test_basis_mentions_moj_lag_in_days(self):
        # Should compute the gap between MoJ last-known and regime active_since
        self.assertIn('يوماً', self.muc['muc_basis_ar'])
        # Numeric gap should be present (59 days between 2025-12-31 and 2026-02-28)
        self.assertTrue(
            any(c.isdigit() for c in self.muc['muc_basis_ar']),
            'MUC basis should cite the lag in days',
        )

    def test_review_recommendation_present(self):
        self.assertIsNotNone(self.muc['muc_review_recommendation_ar'])
        # Must mention the conditions under which the valuation should be re-checked
        rec = self.muc['muc_review_recommendation_ar']
        self.assertIn('وزارة العدل', rec)


class TestRegimeMucNormal(unittest.TestCase):
    """MUC must be empty when market is in normal regime."""

    def test_normal_regime_returns_none_for_clause(self):
        muc = regime_muc(NORMAL_REGIME)
        self.assertIsNone(muc['muc_clause_ar'])
        self.assertIsNone(muc['muc_clause_en'])
        self.assertIsNone(muc['muc_basis_ar'])
        self.assertIsNone(muc['muc_review_recommendation_ar'])


class TestAssessUncertaintyAttachesMUC(unittest.TestCase):
    """assess_uncertainty must always attach MUC when current regime is non-normal."""

    def test_low_per_property_uncertainty_still_has_muc(self):
        """Critical: even a well-supported valuation carries market-wide MUC."""
        u = assess_uncertainty(
            moj_n=30, rent_n=100, trend_n_years=3,
            has_field_inspection=True, building_condition_known=True,
            building_age_known=True, bua_known=True,
        )
        self.assertEqual(u.level, 'low')
        self.assertIsNotNone(u.muc_clause_ar)
        self.assertIn('VPS 5', u.muc_clause_ar)

    def test_high_per_property_uncertainty_also_has_muc(self):
        """The two layers are independent — both can fire."""
        u = assess_uncertainty(
            moj_n=2,  # very low → triggers per-property high
        )
        self.assertIn(u.level, ('high', 'critical'))
        self.assertIsNotNone(u.muc_clause_ar)

    def test_zero_data_case_still_has_muc(self):
        u = assess_uncertainty()  # nothing provided
        self.assertIsNotNone(u.muc_clause_ar)


class TestMUCStructuralCompliance(unittest.TestCase):
    """The generated MUC must follow the RICS VPS 5 recognised structure.

    Structure requirements:
      1. Identifies the cause (the regime/event)
      2. States "less certainty" / "higher caution"
      3. Recommends frequent review
    """

    def setUp(self):
        self.muc = regime_muc(CURRENT_REGIME)['muc_clause_ar']

    def test_identifies_cause(self):
        # Should mention at least one shock layer by name
        layer_names = [s.name_ar for s in CURRENT_REGIME.shock_layers]
        # At least one shock label should appear
        self.assertTrue(
            any(name in self.muc for name in layer_names),
            f'MUC should mention at least one shock layer. Layers: {layer_names}'
        )

    def test_states_less_certainty(self):
        self.assertIn('أقل من المعتاد', self.muc)

    def test_recommends_review(self):
        self.assertIn('مراجعة', self.muc)


if __name__ == '__main__':
    unittest.main(verbosity=2)
