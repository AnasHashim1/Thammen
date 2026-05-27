"""Tests for material_uncertainty.py — Sprint 2.14.0 MUC extension
+ Sprint 2.22.0a/9 RICS Red Book Global Standards 2024 + IVS 2024 audit.

Run as:  python test_material_uncertainty.py
"""

import unittest

from material_uncertainty import (
    assess_uncertainty,
    regime_muc,
    UncertaintyLevel,
    _shock_layer_name_en,
    _SHOCK_LAYER_NAME_EN_BY_AR,
)
from market_regime import CURRENT_REGIME, NORMAL_REGIME


class TestRegimeMucCurrent(unittest.TestCase):
    """MUC generation with the active regime (post_disruption_recession).

    Sprint 2.22.0a/9: brittle "VPS 5" string-pin assertions replaced with
    structural assertions (Rule #36 anti-pattern lesson). Tests now assert
    the presence of canonical 2024-edition citations (VPGA 10 + VPS 3 +
    IVS 103) plus structural elements rather than pinning legacy strings.
    """

    def setUp(self):
        self.muc = regime_muc(CURRENT_REGIME)

    def test_muc_clause_is_populated(self):
        self.assertIsNotNone(self.muc['muc_clause_ar'])
        self.assertIsNotNone(self.muc['muc_clause_en'])

    def test_clause_mentions_rics(self):
        # Sprint 2.22.0a/9: looser substring 'RICS' (was pinned to 'VPS 5').
        self.assertIn('RICS', self.muc['muc_clause_ar'])
        self.assertIn('RICS', self.muc['muc_clause_en'])

    def test_clause_mentions_higher_caution(self):
        # The RICS-recognised phrase: "less certainty — and higher caution"
        self.assertIn('حذر أعلى', self.muc['muc_clause_ar'])
        self.assertIn('higher degree of caution', self.muc['muc_clause_en'])

    def test_clause_recommends_review(self):
        # VPGA 10 / VPS 3 requires "kept under frequent review"
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
        # Sprint 2.22.0a/9: looser substring 'RICS' (was pinned to 'VPS 5').
        self.assertIn('RICS', u.muc_clause_ar)

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
    """The generated MUC must follow the RICS VPGA 10 + VPS 3 + IVS 103
    recognised structure (4 required elements).

    Per RICS Red Book Global Standards 2024 — VPGA 10 (Material Valuation
    Uncertainty) and VPS 3 (Valuation Reports), plus IVS 2024 IVS 103
    (Reporting):

      1. Statement of material valuation uncertainty (titled, with
         edition-specific citation)
      2. Cause/reasons disclosure (identifies the shock layers by name)
      3. Scope of uncertainty (Sprint 2.22.0a/9 R3 strengthening — what
         specifically is uncertain: value, range, methodology applicability)
      4. Recommendation that less reliance be placed + frequent review
    """

    def setUp(self):
        self.muc = regime_muc(CURRENT_REGIME)['muc_clause_ar']

    def test_identifies_cause(self):
        # Should mention at least one shock layer by name (element 2)
        layer_names = [s.name_ar for s in CURRENT_REGIME.shock_layers]
        self.assertTrue(
            any(name in self.muc for name in layer_names),
            f'MUC should mention at least one shock layer. Layers: {layer_names}'
        )

    def test_states_less_certainty(self):
        # Element 4 — less reliance / less certainty phrasing
        self.assertIn('أقل من المعتاد', self.muc)

    def test_recommends_review(self):
        # Element 4 — frequent review recommendation
        self.assertIn('مراجعة', self.muc)


class TestRICS2024Compliance(unittest.TestCase):
    """Sprint 2.22.0a/9 — RICS Red Book Global Standards 2024 + IVS 2024
    citation compliance audit.

    Verifies that the corrected citations (VPGA 10 + VPS 3 + IVS 103)
    are present in both Arabic and English clause text, AND that the
    R3 element-3 scope-of-uncertainty paragraph is present.
    """

    def setUp(self):
        self.muc = regime_muc(CURRENT_REGIME)

    # ── Dual standard citation: RICS + IVS ───────────────────────────────
    def test_ar_clause_cites_both_rics_and_ivs(self):
        clause = self.muc['muc_clause_ar']
        self.assertIn('RICS', clause)
        self.assertIn('IVS', clause)

    def test_en_clause_cites_both_rics_and_ivs(self):
        clause = self.muc['muc_clause_en']
        self.assertIn('RICS', clause)
        self.assertIn('IVS', clause)

    # ── Edition specificity ──────────────────────────────────────────────
    def test_ar_clause_cites_2024_edition(self):
        self.assertIn('2024', self.muc['muc_clause_ar'])

    def test_en_clause_cites_2024_edition(self):
        self.assertIn('2024', self.muc['muc_clause_en'])

    # ── Canonical RICS Red Book 2024 citation: VPGA 10 + VPS 3 ───────────
    def test_ar_clause_cites_vpga_10(self):
        self.assertIn('VPGA 10', self.muc['muc_clause_ar'])

    def test_en_clause_cites_vpga_10(self):
        self.assertIn('VPGA 10', self.muc['muc_clause_en'])

    def test_ar_clause_cites_vps_3(self):
        self.assertIn('VPS 3', self.muc['muc_clause_ar'])

    def test_en_clause_cites_vps_3(self):
        self.assertIn('VPS 3', self.muc['muc_clause_en'])

    # ── Canonical IVS 2024 citation: IVS 103 ─────────────────────────────
    def test_ar_clause_cites_ivs_103(self):
        self.assertIn('IVS 103', self.muc['muc_clause_ar'])

    def test_en_clause_cites_ivs_103(self):
        self.assertIn('IVS 103', self.muc['muc_clause_en'])

    # ── Legacy citation removed ──────────────────────────────────────────
    # The 2014/COVID-era "VPS 5" reference for Material Uncertainty was
    # incorrect for the 2024 edition (where VPS 5 = "Valuation Approaches
    # and Methods" — a different topic). Confirm the corrected text no
    # longer carries it.
    def test_ar_clause_no_longer_cites_vps_5_for_mvu(self):
        self.assertNotIn('VPS 5', self.muc['muc_clause_ar'])

    def test_en_clause_no_longer_cites_vps_5_for_mvu(self):
        self.assertNotIn('VPS 5', self.muc['muc_clause_en'])

    # ── R3 element-3 scope-of-uncertainty paragraph ──────────────────────
    def test_ar_clause_has_scope_of_uncertainty_paragraph(self):
        # Arabic: نطاق التحفّظ + 3 affected aspects
        clause = self.muc['muc_clause_ar']
        self.assertIn('نطاق التحفّظ', clause)
        # Mentions value
        self.assertIn('القيمة التقديرية', clause)
        # Mentions range
        self.assertIn('النطاق', clause)
        # Mentions methodology applicability
        self.assertIn('منهجية المقارنة', clause)

    def test_en_clause_has_scope_of_uncertainty_paragraph(self):
        # English: "Scope of uncertainty:" + 3 affected aspects
        clause = self.muc['muc_clause_en']
        self.assertIn('Scope of uncertainty', clause)
        # Mentions value
        self.assertIn('reported value', clause)
        # Mentions range
        self.assertIn('range', clause)
        # Mentions methodology applicability
        self.assertIn('Sales Comparison', clause)

    # ── R3 4-element structural compliance (both languages) ──────────────
    def test_ar_clause_has_all_4_structural_elements(self):
        clause = self.muc['muc_clause_ar']
        # (1) statement of MVU — title with citation
        self.assertIn('تحفظ مادي', clause)
        # (2) cause/reasons
        self.assertIn('اضطراباً جوهرياً', clause)
        # (3) scope of uncertainty (R3 strengthening)
        self.assertIn('نطاق التحفّظ', clause)
        # (4) less reliance + review recommendation
        self.assertIn('أقل من المعتاد', clause)
        self.assertIn('مراجعة', clause)

    def test_en_clause_has_all_4_structural_elements(self):
        clause = self.muc['muc_clause_en']
        # (1) statement of MVU — title with citation
        self.assertIn('Material Valuation Uncertainty', clause)
        # (2) cause/reasons
        self.assertIn('material disruption', clause)
        # (3) scope of uncertainty (R3 strengthening)
        self.assertIn('Scope of uncertainty', clause)
        # (4) less reliance + review recommendation
        self.assertIn('less certainty', clause)
        self.assertIn('review', clause)


class TestShockLayerEnglishMapping(unittest.TestCase):
    """Sprint 2.22.0a/9 — _shock_layer_name_en helper + Arabic→English map.

    The English MVU clause renders shock layer names from a local
    translation dict. New shock layers added without English mappings
    fall back gracefully to the Arabic name (no exception, no missing text).
    """

    def test_mapping_dict_covers_all_4_known_shock_layers(self):
        layer_names_ar = {s.name_ar for s in CURRENT_REGIME.shock_layers}
        for name_ar in layer_names_ar:
            self.assertIn(
                name_ar, _SHOCK_LAYER_NAME_EN_BY_AR,
                f'ShockLayer "{name_ar}" missing English mapping in '
                f'_SHOCK_LAYER_NAME_EN_BY_AR'
            )

    def test_known_layer_returns_english_name(self):
        for layer in CURRENT_REGIME.shock_layers:
            en = _shock_layer_name_en(layer)
            # English should be different from Arabic when mapping exists
            self.assertNotEqual(en, layer.name_ar,
                                f'Layer "{layer.name_ar}" should have an English name')
            # English should not contain Arabic Unicode characters
            self.assertFalse(
                any('؀' <= c <= 'ۿ' for c in en),
                f'English name for "{layer.name_ar}" contains Arabic characters: {en!r}'
            )

    def test_unknown_layer_falls_back_to_name_ar(self):
        # Simulate an unregistered shock layer via duck-typing
        class _FakeLayer:
            name_ar = 'صدمة افتراضية للاختبار'  # not in the mapping
        result = _shock_layer_name_en(_FakeLayer())
        self.assertEqual(result, 'صدمة افتراضية للاختبار')

    def test_layer_without_name_ar_returns_empty_string(self):
        # Defensive: missing attribute → empty string, never raises
        class _BrokenLayer:
            pass
        result = _shock_layer_name_en(_BrokenLayer())
        self.assertEqual(result, '')

    def test_en_clause_contains_english_shock_names_not_arabic(self):
        # The English clause should render shock layers in English
        en_clause = regime_muc(CURRENT_REGIME)['muc_clause_en']
        # At least one known English shock name should appear
        english_names = list(_SHOCK_LAYER_NAME_EN_BY_AR.values())
        self.assertTrue(
            any(name in en_clause for name in english_names),
            f'English clause should mention at least one English shock '
            f'name. Looking for any of: {english_names}'
        )


class TestAssessUncertaintyRecommendation2024(unittest.TestCase):
    """Sprint 2.22.0a/9 — the RICS compliance recommendation should cite
    the current 2024 edition + IVS 2024."""

    def test_non_compliant_recommendation_cites_2024(self):
        # Force rics_compliant=False by withholding inspection + condition
        u = assess_uncertainty(moj_n=25, rent_n=50)
        self.assertFalse(u.rics_compliant)
        joined = '\n'.join(u.recommendations)
        self.assertIn('2024', joined)
        self.assertIn('RICS', joined)
        self.assertIn('IVS', joined)


if __name__ == '__main__':
    unittest.main(verbosity=2)
