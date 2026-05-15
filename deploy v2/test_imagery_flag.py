"""Tests for the Sprint 2.15.1 imagery feature flag and cache-only mode.

Verifies:
  - Default mode is CACHE-ONLY (production safe)
  - Cache miss in CACHE-ONLY returns None instantly
  - Toggling the flag enables full imagery (used by prefill_cache.py)
  - Environment variable THAMMEN_ENABLE_INLINE_IMAGERY=1 enables full mode

Run as: python test_imagery_flag.py
"""

import os
import time
import unittest
from unittest.mock import patch, MagicMock


class TestFeatureFlagDefault(unittest.TestCase):
    """The module-level flag defaults to False (production-safe)."""

    def test_default_is_false(self):
        # Fresh import without env var
        if 'THAMMEN_ENABLE_INLINE_IMAGERY' in os.environ:
            del os.environ['THAMMEN_ENABLE_INLINE_IMAGERY']
        # Force reimport
        import importlib
        import qatar_gis
        importlib.reload(qatar_gis)
        self.assertFalse(qatar_gis.ENABLE_INLINE_IMAGERY,
                         'Production default must be False — '
                         'inline imagery on Heroku is too slow.')

    def test_env_var_enables_full_mode(self):
        os.environ['THAMMEN_ENABLE_INLINE_IMAGERY'] = '1'
        import importlib
        import qatar_gis
        importlib.reload(qatar_gis)
        self.assertTrue(qatar_gis.ENABLE_INLINE_IMAGERY,
                        'THAMMEN_ENABLE_INLINE_IMAGERY=1 must enable.')
        # Cleanup
        del os.environ['THAMMEN_ENABLE_INLINE_IMAGERY']
        importlib.reload(qatar_gis)


class TestCacheOnlyMode(unittest.TestCase):
    """In CACHE-ONLY mode, smart() never runs imagery."""

    def setUp(self):
        import importlib
        import qatar_gis
        importlib.reload(qatar_gis)
        qatar_gis.ENABLE_INLINE_IMAGERY = False
        self.qatar_gis = qatar_gis

    def test_cache_miss_returns_none_fast(self):
        gis = self.qatar_gis.QatarGIS()
        # Use a polygon and a PIN that's not in any cache
        polygon = [[51.5, 25.3], [51.5, 25.31], [51.51, 25.31], [51.51, 25.3], [51.5, 25.3]]
        unknown_pin = 99999999
        t0 = time.time()
        r = gis.estimate_construction_year_smart(polygon, pin=unknown_pin)
        elapsed = time.time() - t0
        self.assertIsNone(r, 'Cache miss in CACHE-ONLY mode must return None')
        self.assertLess(elapsed, 0.5,
                        'Cache-only must complete instantly (<0.5s), '
                        f'got {elapsed:.2f}s')

    def test_no_imagery_calls_in_cache_only_mode(self):
        """Verify estimate_construction_year is NOT called when flag is off."""
        gis = self.qatar_gis.QatarGIS()
        polygon = [[51.5, 25.3], [51.5, 25.31], [51.51, 25.31], [51.51, 25.3], [51.5, 25.3]]

        # Mock the slow method — should never be called
        with patch.object(gis, 'estimate_construction_year') as mock_slow:
            mock_slow.side_effect = RuntimeError('IMAGERY SHOULD NOT RUN!')
            r = gis.estimate_construction_year_smart(polygon, pin=88888888)
            self.assertIsNone(r)
            mock_slow.assert_not_called()


class TestFullMode(unittest.TestCase):
    """In FULL mode (flag=True), smart() runs imagery on cache miss."""

    def setUp(self):
        import importlib
        import qatar_gis
        importlib.reload(qatar_gis)
        qatar_gis.ENABLE_INLINE_IMAGERY = True
        self.qatar_gis = qatar_gis

        # Use a tmp cache to avoid polluting the real one
        import tempfile
        from pathlib import Path
        self.tmp = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        self.tmp.close()
        self.cache_path = Path(self.tmp.name)
        self.cache_path.unlink()

        import building_age_cache
        building_age_cache._default_cache_instance = None
        self.original_default = building_age_cache.DEFAULT_CACHE_PATH
        building_age_cache.DEFAULT_CACHE_PATH = self.cache_path

    def tearDown(self):
        self.qatar_gis.ENABLE_INLINE_IMAGERY = False
        import building_age_cache
        building_age_cache.DEFAULT_CACHE_PATH = self.original_default
        building_age_cache._default_cache_instance = None
        import gc
        gc.collect()
        try:
            if self.cache_path.exists():
                self.cache_path.unlink()
        except (PermissionError, OSError):
            pass

    def test_full_mode_calls_imagery(self):
        """In FULL mode, cache miss triggers estimate_construction_year."""
        gis = self.qatar_gis.QatarGIS()
        polygon = [[51.5, 25.3], [51.5, 25.31], [51.51, 25.31], [51.51, 25.3], [51.5, 25.3]]
        with patch.object(gis, 'estimate_construction_year') as mock_slow:
            # Return a synthetic estimate
            from qatar_gis import ConstructionYearEstimate
            mock_slow.return_value = ConstructionYearEstimate(
                earliest_built_year=2015,
                latest_vacant_year=2010,
                confidence_years=5,
                summary='test',
            )
            r = gis.estimate_construction_year_smart(polygon, pin=77777777)
            self.assertIsNotNone(r)
            self.assertEqual(r.earliest_built_year, 2015)
            mock_slow.assert_called()


class TestCacheHitInCacheOnlyMode(unittest.TestCase):
    """A cached PIN still returns a value in CACHE-ONLY mode."""

    def setUp(self):
        import importlib
        import qatar_gis
        importlib.reload(qatar_gis)
        qatar_gis.ENABLE_INLINE_IMAGERY = False
        self.qatar_gis = qatar_gis

        # Pre-populate the cache with one PIN
        import tempfile
        from pathlib import Path
        self.tmp = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        self.tmp.close()
        self.cache_path = Path(self.tmp.name)
        self.cache_path.unlink()  # remove so init creates fresh

        import building_age_cache
        building_age_cache._default_cache_instance = None
        # Patch the default path to our tmp file
        self.original_default = building_age_cache.DEFAULT_CACHE_PATH
        building_age_cache.DEFAULT_CACHE_PATH = self.cache_path

        from building_age_cache import BuildingAgeCache
        cache = BuildingAgeCache(db_path=self.cache_path)
        cache.set(
            pin=12345678,
            earliest_built_year=2000,
            latest_vacant_year=1995,
            confidence_years=5,
            summary='Cached test',
            method='fast_probe',
        )

    def tearDown(self):
        import building_age_cache
        building_age_cache.DEFAULT_CACHE_PATH = self.original_default
        building_age_cache._default_cache_instance = None
        import gc
        gc.collect()
        try:
            if self.cache_path.exists():
                self.cache_path.unlink()
        except (PermissionError, OSError):
            pass

    def test_cache_hit_returns_value_in_cache_only_mode(self):
        gis = self.qatar_gis.QatarGIS()
        polygon = [[51.5, 25.3], [51.5, 25.31], [51.51, 25.31], [51.51, 25.3]]
        t0 = time.time()
        r = gis.estimate_construction_year_smart(polygon, pin=12345678)
        elapsed = time.time() - t0
        self.assertIsNotNone(r)
        self.assertEqual(r.earliest_built_year, 2000)
        self.assertLess(elapsed, 0.5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
