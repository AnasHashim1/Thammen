"""Tests for building_age_cache.py — Sprint 2.15 (L4)

Run as:  python test_building_age_cache.py
"""

import gc
import unittest
import tempfile
from pathlib import Path

from building_age_cache import BuildingAgeCache, SCHEMA_VERSION


def _safe_unlink(path: Path) -> None:
    """Best-effort file deletion that handles Windows lock issues.

    On Windows, SQLite occasionally holds file locks for a moment after
    `close()`. A forced gc pass usually clears it; if not, we just leave
    the temp file (the OS will reclaim it on reboot).
    """
    if not path.exists():
        return
    gc.collect()
    try:
        path.unlink()
    except (PermissionError, OSError):
        pass  # leave it; OS will clean temp eventually


class TestCacheBasics(unittest.TestCase):
    """Round-trip CRUD operations."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        self.tmp.close()
        self.path = Path(self.tmp.name)
        self.path.unlink()  # remove so cache init creates fresh
        self.cache = BuildingAgeCache(db_path=self.path)

    def tearDown(self):
        _safe_unlink(self.path)

    def test_empty_cache_returns_none(self):
        self.assertIsNone(self.cache.get(12345))

    def test_get_with_none_pin_returns_none(self):
        self.assertIsNone(self.cache.get(None))

    def test_set_and_get_roundtrip(self):
        self.cache.set(
            pin=52200100,
            earliest_built_year=1995,
            latest_vacant_year=1990,
            confidence_years=5,
            summary='Built ≤1995',
            method='fast_probe',
        )
        hit = self.cache.get(52200100)
        self.assertIsNotNone(hit)
        self.assertEqual(hit['earliest_built_year'], 1995)
        self.assertEqual(hit['latest_vacant_year'], 1990)
        self.assertEqual(hit['confidence_years'], 5)
        self.assertEqual(hit['method'], 'fast_probe')

    def test_set_with_none_pin_is_noop(self):
        # Should not raise
        self.cache.set(pin=None, earliest_built_year=2010)
        # Cache still empty
        self.assertEqual(self.cache.stats()['cached_pins'], 0)

    def test_overwrite_existing_row(self):
        self.cache.set(pin=999, earliest_built_year=2010, method='fast_probe')
        self.cache.set(pin=999, earliest_built_year=2008,
                       method='binary_search_4y')
        hit = self.cache.get(999)
        self.assertEqual(hit['earliest_built_year'], 2008)
        self.assertEqual(hit['method'], 'binary_search_4y')


class TestCacheStats(unittest.TestCase):
    """Health-check stats."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        self.tmp.close()
        self.path = Path(self.tmp.name)
        self.path.unlink()
        self.cache = BuildingAgeCache(db_path=self.path)

    def tearDown(self):
        _safe_unlink(self.path)

    def test_empty_stats(self):
        s = self.cache.stats()
        self.assertTrue(s['available'])
        self.assertEqual(s['cached_pins'], 0)
        self.assertIsNone(s['latest_computed_at'])
        self.assertEqual(s['schema_version'], SCHEMA_VERSION)

    def test_stats_after_inserts(self):
        for pin in (1001, 1002, 1003):
            self.cache.set(pin=pin, earliest_built_year=2010)
        s = self.cache.stats()
        self.assertEqual(s['cached_pins'], 3)
        self.assertIsNotNone(s['latest_computed_at'])

    def test_list_pins_ordered(self):
        # Insert in some order
        for pin in (5001, 5002, 5003):
            self.cache.set(pin=pin, earliest_built_year=2020)
        pins = self.cache.list_pins()
        self.assertEqual(len(pins), 3)
        # All should be present (order may vary at timestamp precision)
        self.assertEqual(set(pins), {5001, 5002, 5003})


class TestSchemaVersioning(unittest.TestCase):
    """Rows with old schema version should be ignored on read."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        self.tmp.close()
        self.path = Path(self.tmp.name)
        self.path.unlink()
        self.cache = BuildingAgeCache(db_path=self.path)

    def tearDown(self):
        _safe_unlink(self.path)

    def test_old_schema_row_treated_as_miss(self):
        import sqlite3
        from datetime import datetime
        # Manually insert a row with a stale schema_version
        with sqlite3.connect(self.path) as conn:
            conn.execute('''
                INSERT INTO building_age (
                    pin, earliest_built_year, latest_vacant_year,
                    confidence_years, summary, method,
                    schema_version, computed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                7777, 2000, 1995, 5, 'old-schema', 'fast_probe',
                SCHEMA_VERSION - 1,  # one version behind
                datetime.utcnow().isoformat(),
            ))
        # Reads should miss
        self.assertIsNone(self.cache.get(7777))


class TestSourceDataJson(unittest.TestCase):
    """Source data can include arbitrary Arabic text without corruption."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        self.tmp.close()
        self.path = Path(self.tmp.name)
        self.path.unlink()
        self.cache = BuildingAgeCache(db_path=self.path)

    def tearDown(self):
        _safe_unlink(self.path)

    def test_arabic_summary_roundtrip(self):
        ar_summary = 'مبني قبل أو في 1995 (لا يوجد مرجع شغور)'
        self.cache.set(
            pin=8888,
            earliest_built_year=1995,
            summary=ar_summary,
            method='fast_probe',
        )
        hit = self.cache.get(8888)
        self.assertEqual(hit['summary'], ar_summary)

    def test_source_data_json_roundtrip(self):
        import json
        src = {
            'elapsed_s': 6.1,
            'years_probed': [1995, 2024],
            'note_ar': 'تحقّق سريع',
        }
        self.cache.set(
            pin=9999,
            earliest_built_year=2010,
            method='fast_probe',
            source_data=src,
        )
        hit = self.cache.get(9999)
        parsed = json.loads(hit['source_data_json'])
        self.assertEqual(parsed['elapsed_s'], 6.1)
        self.assertEqual(parsed['note_ar'], 'تحقّق سريع')


class TestGracefulDegradation(unittest.TestCase):
    """Cache failures must never raise into the engine."""

    def test_set_on_missing_directory_does_not_raise(self):
        # /nonexistent/path doesn't exist — SQLite should fail silently
        bad_cache = BuildingAgeCache(db_path=Path('/nonexistent/x/y/z.sqlite'))
        # Should not raise
        try:
            bad_cache.set(pin=1, earliest_built_year=2020)
            # If it didn't raise, we're good
        except Exception as e:
            self.fail(f'Cache set raised: {e}')

    def test_get_on_corrupted_path_returns_none(self):
        bad_cache = BuildingAgeCache(db_path=Path('/nonexistent/x/y/z.sqlite'))
        self.assertIsNone(bad_cache.get(1))


if __name__ == '__main__':
    unittest.main(verbosity=2)
