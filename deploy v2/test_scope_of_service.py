"""Tests for scope_of_service.py — Sprint 2.14.0

Run as:  python test_scope_of_service.py
"""

import unittest

from scope_of_service import (
    classify_asset_scope,
    scope_to_dict,
    service_scope_summary,
    SERVICE_LEVEL_AR,
    SERVICE_LEVEL_EN,
)


class TestSupportedAssets(unittest.TestCase):
    """Assets we claim full Sales Comparison support for."""

    def test_standalone_villa_is_supported(self):
        s = classify_asset_scope('standalone_villa')
        self.assertEqual(s.tier, 'supported')
        self.assertIn('فلة', s.label_ar)
        self.assertIn('Sales Comparison', s.methodology_ar)

    def test_land_is_supported(self):
        s = classify_asset_scope('land')
        self.assertEqual(s.tier, 'supported')
        self.assertIn('أرض', s.label_ar)

    def test_compound_small_is_supported(self):
        s = classify_asset_scope('compound_small')
        self.assertEqual(s.tier, 'supported')

    def test_supported_assets_dont_require_user_input(self):
        for at in ('standalone_villa', 'land', 'compound_small'):
            s = classify_asset_scope(at)
            self.assertIsNone(s.requires_user_input_ar)


class TestLimitedAssets(unittest.TestCase):
    """Assets supported only with user-provided inputs (income, listing price)."""

    def test_compound_large_is_limited(self):
        s = classify_asset_scope('compound_large')
        self.assertEqual(s.tier, 'limited')
        self.assertIsNotNone(s.requires_user_input_ar)
        self.assertIn('إيجار', s.requires_user_input_ar)

    def test_tower_is_limited(self):
        s = classify_asset_scope('tower')
        self.assertEqual(s.tier, 'limited')

    def test_apartment_building_is_limited(self):
        s = classify_asset_scope('apartment_building')
        self.assertEqual(s.tier, 'limited')

    def test_palace_is_limited(self):
        s = classify_asset_scope('palace')
        self.assertEqual(s.tier, 'limited')
        # Palace explicitly mentions weak MoJ sample
        self.assertIn('n=5', s.reason_ar)


class TestUnsupportedAssets(unittest.TestCase):
    """Assets explicitly out of scope."""

    def test_commercial_is_unsupported(self):
        s = classify_asset_scope('commercial')
        self.assertEqual(s.tier, 'unsupported')

    def test_industrial_is_unsupported(self):
        s = classify_asset_scope('industrial')
        self.assertEqual(s.tier, 'unsupported')

    def test_agricultural_is_unsupported(self):
        s = classify_asset_scope('agricultural')
        self.assertEqual(s.tier, 'unsupported')

    def test_unsupported_methodology_is_not_applicable(self):
        for at in ('commercial', 'industrial', 'agricultural'):
            s = classify_asset_scope(at)
            self.assertIn('غير مطبَّق', s.methodology_ar)


class TestUnknownAsset(unittest.TestCase):
    """Unknown asset types default to unsupported."""

    def test_unknown_string_defaults_unsupported(self):
        s = classify_asset_scope('flying_saucer')
        self.assertEqual(s.tier, 'unsupported')
        self.assertIn('غير معروف', s.label_ar)

    def test_none_defaults_unsupported(self):
        s = classify_asset_scope(None)
        self.assertEqual(s.tier, 'unsupported')

    def test_empty_string_defaults_unsupported(self):
        s = classify_asset_scope('')
        self.assertEqual(s.tier, 'unsupported')


class TestSerialization(unittest.TestCase):
    """API-shape dict must contain all required keys."""

    def test_scope_to_dict_has_required_keys(self):
        s = classify_asset_scope('standalone_villa')
        d = scope_to_dict(s)
        for key in ('asset_type', 'tier', 'label_ar', 'methodology_ar',
                    'methodology_en', 'requires_user_input_ar',
                    'disclaimer_ar', 'reason_ar'):
            self.assertIn(key, d)

    def test_serialization_is_json_safe(self):
        import json
        s = classify_asset_scope('palace')
        d = scope_to_dict(s)
        # Should serialise without error
        json_str = json.dumps(d, ensure_ascii=False)
        parsed = json.loads(json_str)
        self.assertEqual(parsed['tier'], 'limited')


class TestServiceLevel(unittest.TestCase):
    """Service-level declaration must clearly state Thammen is NOT a
    formal Valuation Report."""

    def test_service_level_ar_mentions_calculation_of_value(self):
        self.assertIn('حساب قيمة', SERVICE_LEVEL_AR)

    def test_service_level_ar_mentions_other_advice(self):
        self.assertIn('Other Advice', SERVICE_LEVEL_AR)

    def test_service_level_ar_disclaims_valuation_report(self):
        self.assertIn('وليس', SERVICE_LEVEL_AR)
        self.assertIn('Valuation Report', SERVICE_LEVEL_AR)

    def test_service_level_ar_mentions_official_purposes(self):
        # Must mention mortgage / court / etc to direct users elsewhere
        self.assertIn('قروض', SERVICE_LEVEL_AR)

    def test_service_level_en_disclaims_valuation_report(self):
        self.assertIn('NOT', SERVICE_LEVEL_EN)
        self.assertIn('Valuation Report', SERVICE_LEVEL_EN)


class TestServiceScopeSummary(unittest.TestCase):
    """Homepage scope summary structure."""

    def setUp(self):
        self.summary = service_scope_summary()

    def test_has_three_tiers(self):
        self.assertIn('supported', self.summary)
        self.assertIn('limited', self.summary)
        self.assertIn('unsupported', self.summary)

    def test_supported_count_nonzero(self):
        # At minimum: villas, land, small compound
        self.assertGreaterEqual(len(self.summary['supported']), 3)

    def test_unsupported_count_nonzero(self):
        # We MUST declare some things unsupported (otherwise we're lying)
        self.assertGreaterEqual(len(self.summary['unsupported']), 3)

    def test_summary_text_arabic(self):
        # Sanity check the summary string is Arabic
        self.assertIn('ثمّن', self.summary['summary_ar'])

    def test_includes_service_level(self):
        self.assertIn('service_level_ar', self.summary)
        self.assertIn('service_level_en', self.summary)


if __name__ == '__main__':
    unittest.main(verbosity=2)
