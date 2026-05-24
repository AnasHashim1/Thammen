"""
t2_listings_cache.py — Sprint 2.21.3 — SQLite cache for T2 asking-tier listings

24-hour TTL cache per BRIEF_2p21p3 D4. Pattern follows building_age_cache.py
(threading.Lock + closing() context manager + try/except no-op on failure).

Schema:
    listings(source, district, size_bracket, fetched_at, payload_json)
        PRIMARY KEY (source, district, size_bracket)
    payload_json is a JSON-serialised list[dict] of connector output rows.

Why district + size_bracket as part of the key:
    The connector's logical query is "Lusail apartments-for-sale in size
    bracket B"; different brackets fetch different list-page subsets. A
    single key per source would over-cache.

Why no per-listing cache:
    The hybrid framework consumes the LIST as a unit (n + median). Caching
    per listing would mean re-fetching list pages every time to recover
    that aggregate. List-level cache matches the consumer's access pattern.

24-hour TTL rationale (D4):
    Listings churn weekly at most for individual price changes; 24h
    balances freshness vs Heroku request cost. Aligns with the daily
    deploy cadence — first request of the day pays the network cost,
    rest are instant.
"""

from __future__ import annotations
import json
import sqlite3
import threading
import time
from contextlib import closing
from pathlib import Path
from typing import Any, Optional

DEFAULT_CACHE_PATH = Path(__file__).parent / "t2_listings_cache.sqlite"
DEFAULT_TTL_SECONDS = 24 * 60 * 60   # D4 — 24 hours
SCHEMA_VERSION = 1


class T2ListingsCache:
    """Thread-safe SQLite cache for T2 listing payloads with TTL.

    Use:
        cache = T2ListingsCache()
        hit = cache.get("propertyfinder", "Lusail", "100-150")
        if hit is None:
            listings = ... # fetch from network
            cache.set("propertyfinder", "Lusail", "100-150", listings)
    """

    def __init__(self, db_path: Optional[Path] = None,
                 ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.db_path = Path(db_path) if db_path else DEFAULT_CACHE_PATH
        self.ttl_seconds = int(ttl_seconds)
        self._lock = threading.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        try:
            with self._lock, closing(sqlite3.connect(self.db_path)) as conn:
                with conn:
                    conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS listings (
                            source        TEXT NOT NULL,
                            district      TEXT NOT NULL,
                            size_bracket  TEXT NOT NULL,
                            fetched_at    REAL NOT NULL,
                            payload_json  TEXT NOT NULL,
                            PRIMARY KEY (source, district, size_bracket)
                        )
                        """
                    )
                    conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS meta (
                            key   TEXT PRIMARY KEY,
                            value TEXT
                        )
                        """
                    )
                    conn.execute(
                        "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
                        ("schema_version", str(SCHEMA_VERSION)),
                    )
        except sqlite3.DatabaseError:
            # Read-only fs or corrupt file — silently disable caching.
            # Every subsequent get/set is also try-wrapped (D6 spirit).
            pass

    def get(self, source: str, district: str,
            size_bracket: str) -> Optional[list[dict[str, Any]]]:
        """Return cached listings if fresh; None on miss / stale / error."""
        try:
            with self._lock, closing(sqlite3.connect(self.db_path)) as conn:
                row = conn.execute(
                    "SELECT fetched_at, payload_json FROM listings "
                    "WHERE source = ? AND district = ? AND size_bracket = ?",
                    (source, district, size_bracket),
                ).fetchone()
        except sqlite3.DatabaseError:
            return None
        if not row:
            return None
        fetched_at, payload_json = row
        if (time.time() - float(fetched_at)) > self.ttl_seconds:
            return None  # stale — treat as miss; caller refetches
        try:
            return json.loads(payload_json)
        except (TypeError, ValueError):
            return None

    def set(self, source: str, district: str, size_bracket: str,
            payload: list[dict[str, Any]]) -> None:
        """Persist listings with the current timestamp."""
        try:
            blob = json.dumps(payload, ensure_ascii=False)
        except (TypeError, ValueError):
            return
        try:
            with self._lock, closing(sqlite3.connect(self.db_path)) as conn:
                with conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO listings "
                        "(source, district, size_bracket, fetched_at, payload_json) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (source, district, size_bracket, time.time(), blob),
                    )
        except sqlite3.DatabaseError:
            pass  # best-effort cache; engine continues regardless

    def purge_expired(self) -> int:
        """Delete rows older than TTL. Returns rows deleted (or 0 on error)."""
        cutoff = time.time() - self.ttl_seconds
        try:
            with self._lock, closing(sqlite3.connect(self.db_path)) as conn:
                with conn:
                    cur = conn.execute(
                        "DELETE FROM listings WHERE fetched_at < ?",
                        (cutoff,),
                    )
                    return int(cur.rowcount or 0)
        except sqlite3.DatabaseError:
            return 0
