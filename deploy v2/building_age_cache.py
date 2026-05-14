#!/usr/bin/env python3
"""
building_age_cache.py — Sprint 2.15 (L4)

Persistent SQLite cache for building age estimates derived from GIS
historical satellite imagery.

WHY THIS EXISTS:
  `qatar_gis.QatarGIS.estimate_construction_year()` takes ~30-60s to
  iterate all 9 historical imagery services (1995, 2003, 2004, 2010,
  2012, 2017, 2019, 2021, 2024). On Heroku's 30s request budget this
  is impossible inline.

  However: the result for a given parcel NEVER CHANGES.
  - The plot polygon is fixed (cadastral PINs are permanent identifiers)
  - Historical satellite imagery doesn't change retroactively
  - Once computed, the answer is permanent

  This module provides a SQLite-backed cache keyed by PIN. The cache
  file (`building_age_cache.sqlite`) is committed to the repo and
  survives Heroku restarts because it's part of the deployed slug.

  On cache hit: instant lookup (<10ms).
  On cache miss: the caller runs imagery analysis (slow, ~10-20s with
  smart probing — see `estimate_construction_year_smart()` in
  qatar_gis.py), then writes the result here for future requests.

USAGE:
  from building_age_cache import BuildingAgeCache

  cache = BuildingAgeCache()    # default location alongside moj_weekly.csv
  hit = cache.get(pin=52200100)
  if hit:
      year = hit['earliest_built_year']
  else:
      # run imagery analysis, then:
      cache.set(pin=52200100, earliest_built_year=1995, ...)

CACHE GROWTH:
  After deploy, the cache fills organically as users evaluate addresses.
  After ~6 months of production traffic, the most-queried addresses are
  cached and instant. Cache file size: ~200 bytes per PIN → 100K PINs =
  ~20MB, easily committable.
"""

from __future__ import annotations
import sqlite3
import json
import threading
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Optional


# Default cache location: next to moj_weekly.csv in the project root
DEFAULT_CACHE_PATH = Path(__file__).parent / 'building_age_cache.sqlite'

# Schema version — bump if we change column structure (forces rebuild)
SCHEMA_VERSION = 1


class BuildingAgeCache:
    """Thread-safe SQLite cache for building age estimates by PIN.

    The cache is intentionally simple: one row per PIN, no expiry. Because
    the underlying truth (historical satellite imagery) doesn't change,
    cached values are valid forever — until we improve the algorithm and
    invalidate by bumping SCHEMA_VERSION.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_CACHE_PATH
        # SQLite connections aren't thread-safe by default; lock writes.
        # Heroku free dynos are single-process so contention is low.
        self._lock = threading.Lock()
        self._init_schema()

    def _init_schema(self):
        """Create the cache table if it doesn't exist.

        Wrapped in try/except: if the cache path is unreachable (e.g. a
        read-only filesystem in tests, or a misconfigured Heroku slug),
        we silently fail at init. Every subsequent get/set will also be
        try-wrapped, so the engine continues without caching.

        Uses `closing()` to guarantee connection close on every code path
        — critical on Windows where SQLite holds an exclusive file lock
        until the connection object is explicitly closed (not just GC'd).
        """
        try:
            with self._lock, closing(sqlite3.connect(self.db_path)) as conn:
                with conn:  # transaction context (commit on exit)
                    conn.execute('''
                        CREATE TABLE IF NOT EXISTS building_age (
                            pin                   INTEGER PRIMARY KEY,
                            earliest_built_year   INTEGER,
                            latest_vacant_year    INTEGER,
                            confidence_years      INTEGER,
                            summary               TEXT,
                            method                TEXT,
                            schema_version        INTEGER NOT NULL DEFAULT 1,
                            computed_at           TEXT NOT NULL,
                            source_data_json      TEXT
                        )
                    ''')
                    conn.execute('''
                        CREATE INDEX IF NOT EXISTS idx_schema_version
                        ON building_age(schema_version)
                    ''')
        except sqlite3.Error:
            # Cache unavailable — engine continues without caching.
            pass

    def get(self, pin: int) -> Optional[dict]:
        """Return cached estimate for the given PIN, or None on miss.

        Only returns rows matching the current SCHEMA_VERSION — older
        rows are treated as misses so they get re-computed with the
        latest algorithm.
        """
        if pin is None:
            return None
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    'SELECT * FROM building_age '
                    'WHERE pin = ? AND schema_version = ?',
                    (int(pin), SCHEMA_VERSION),
                ).fetchone()
                if row is None:
                    return None
                return dict(row)
        except sqlite3.Error:
            # Cache corruption should never break the engine — return miss
            return None

    def set(
        self,
        pin: int,
        earliest_built_year: Optional[int] = None,
        latest_vacant_year: Optional[int] = None,
        confidence_years: Optional[int] = None,
        summary: Optional[str] = None,
        method: str = 'unknown',
        source_data: Optional[dict] = None,
    ) -> None:
        """Save an estimate to the cache. Overwrites any existing row."""
        if pin is None:
            return
        source_json = json.dumps(source_data, ensure_ascii=False) if source_data else None
        try:
            with self._lock, closing(sqlite3.connect(self.db_path)) as conn:
                with conn:  # transaction context
                    conn.execute('''
                        INSERT OR REPLACE INTO building_age (
                            pin, earliest_built_year, latest_vacant_year,
                            confidence_years, summary, method,
                            schema_version, computed_at, source_data_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        int(pin),
                        earliest_built_year,
                        latest_vacant_year,
                        confidence_years,
                        summary,
                        method,
                        SCHEMA_VERSION,
                        datetime.utcnow().isoformat(),
                        source_json,
                    ))
        except sqlite3.Error:
            # Cache failure should never break the engine — log and move on
            import sys
            print(f'[building_age_cache] write failed for PIN {pin}', file=sys.stderr)

    def stats(self) -> dict:
        """Cache statistics for /api/health monitoring."""
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                total = conn.execute(
                    'SELECT COUNT(*) FROM building_age '
                    'WHERE schema_version = ?',
                    (SCHEMA_VERSION,),
                ).fetchone()[0]
                latest = conn.execute(
                    'SELECT MAX(computed_at) FROM building_age '
                    'WHERE schema_version = ?',
                    (SCHEMA_VERSION,),
                ).fetchone()[0]
                size_mb = round(self.db_path.stat().st_size / 1024 / 1024, 3) \
                    if self.db_path.exists() else 0
                return {
                    'available': True,
                    'cached_pins': total,
                    'latest_computed_at': latest,
                    'size_mb': size_mb,
                    'schema_version': SCHEMA_VERSION,
                }
        except sqlite3.Error:
            return {'available': False}

    def list_pins(self, limit: int = 100) -> list:
        """Return list of cached PINs, ordered by most-recently-computed.

        Useful for batch refresh operations (e.g. recompute popular PINs
        when the algorithm improves).
        """
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                rows = conn.execute(
                    'SELECT pin FROM building_age '
                    'WHERE schema_version = ? '
                    'ORDER BY computed_at DESC LIMIT ?',
                    (SCHEMA_VERSION, limit),
                ).fetchall()
                return [r[0] for r in rows]
        except sqlite3.Error:
            return []


# ─── Module-level singleton — Heroku-friendly ─────────────────────────────
# A single shared cache instance avoids reopening SQLite for every request.

_default_cache_instance: Optional[BuildingAgeCache] = None
_default_cache_lock = threading.Lock()


def get_default_cache() -> BuildingAgeCache:
    """Return the shared module-level cache instance."""
    global _default_cache_instance
    if _default_cache_instance is None:
        with _default_cache_lock:
            if _default_cache_instance is None:
                _default_cache_instance = BuildingAgeCache()
    return _default_cache_instance


# ─── CLI self-test ────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    cache = BuildingAgeCache(db_path=Path('/tmp/test_building_age.sqlite'))
    if Path('/tmp/test_building_age.sqlite').exists():
        Path('/tmp/test_building_age.sqlite').unlink()
    cache = BuildingAgeCache(db_path=Path('/tmp/test_building_age.sqlite'))

    print('=== Empty cache ===')
    print(cache.stats())
    print('Miss for PIN 999:', cache.get(999))

    print('\n=== Save + retrieve ===')
    cache.set(
        pin=52200100,
        earliest_built_year=1995,
        latest_vacant_year=1990,
        confidence_years=5,
        summary='Built in or before 1995',
        method='fast_probe',
        source_data={'years_checked': [1995, 2024]},
    )
    hit = cache.get(52200100)
    print(f'Hit: pin={hit["pin"]}, year={hit["earliest_built_year"]}, '
          f'method={hit["method"]}')

    print('\n=== Stats after one entry ===')
    print(cache.stats())

    print('\n=== Overwrite (idempotent set) ===')
    cache.set(pin=52200100, earliest_built_year=1990, summary='Updated',
              method='binary_search')
    hit = cache.get(52200100)
    print(f'Updated: year={hit["earliest_built_year"]}, '
          f'summary={hit["summary"]}, method={hit["method"]}')

    print('\n=== list_pins ===')
    print(cache.list_pins())

    Path('/tmp/test_building_age.sqlite').unlink()
    print('\nAll self-tests passed.')
