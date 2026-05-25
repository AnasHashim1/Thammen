"""
connectors/developer_inventory_t3.py — Sprint 2.21.4 — T3 read-only connector

Read-only fetcher for `developer_inventory.sqlite` (populated locally by
`scripts/import_developer_inventory.py`, shipped in the slug via Step 17
commit). Returns rows in the exact dict_new shape that
`hybrid_valuation_v1._process_t3_input` expects (Sprint 2.21.4 Step 8 in
the BRIEF ordering — built AFTER hybrid Step 7 per conversation drift).

DESIGN
  - Module-scoped lazy connection (single SQLite handle for process lifetime).
  - Read-only via `file:...?mode=ro` SQLite URI (defensive — no accidental
    writes from the engine path; CSV importer is the only canonical writer).
  - atexit cleanup of the connection handle.
  - check_same_thread=False so the engine's ThreadPoolExecutor paths can call
    safely; SQLite serialises reads internally.
  - Defensive on every failure mode: missing DB, corrupt DB, schema drift,
    invalid rows. Logs at WARN/ERROR; returns None so the engine's
    apartment evaluation never crashes on T3 problems (Rule #11 spirit —
    T3 absence is a valid result, not an exception).

NON-RESPONSIBILITIES (per BRIEF §3.1 + Step 8 spec §9):
  - No writes. The CSV importer is the single write path.
  - No caching layer beyond the SQLite handle (SQLite + OS page cache suffice).
  - No cross-district fallback. Geo filter is strict (per H9).

PUBLIC API
  fetch_for_district(district, asset_type, status_filter, max_age_days,
                     db_path=..., today=...) -> list[dict] | None

INVARIANTS
  - asset_type must be one of `SUPPORTED_ASSET_TYPES` ({'apartment',
    'apartment_building'}) or the function returns None immediately
    (BRIEF §12 single-purpose — apartments only for Sprint 2.21.4).
  - Empty result set → None (NOT []). Hybrid treats None and empty
    list both as "absent" but `None` is the more honest signal that
    no data was found.
  - Every returned dict has EXACTLY 8 fields matching the
    `hybrid_valuation_v1` dict_new shape contract.
"""

from __future__ import annotations
import atexit
import logging
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

# Single source of truth for the DB path (Rule #40). scripts/ is now a
# Python package thanks to its __init__.py (Sprint 2.21.4 Step 8).
try:
    from scripts.migrate_developer_inventory import DEFAULT_DB_PATH
except ImportError:                               # pragma: no cover
    # Defensive fallback for environments where scripts/ isn't reachable
    # via sys.path. Path resolves to the same file by construction.
    DEFAULT_DB_PATH = (
        Path(__file__).resolve().parent.parent / "developer_inventory.sqlite"
    )

logger = logging.getLogger("t3.developer_inventory")

# ─────────────────────────────────────────────────────────────────────────
# Constants — exposed at top-level for Step 10 test imports (Rule #40)
# ─────────────────────────────────────────────────────────────────────────

DEFAULT_TTL_DAYS = 90      # D7: 90-day freshness window. Stale beyond → 0.5×

# BRIEF §12 single-purpose discipline — Sprint 2.21.4 covers apartments only.
# Other asset classes (villas, lands, compounds) get None at the fetch gate
# even if rows exist. Future Sprints expand this set.
SUPPORTED_ASSET_TYPES: frozenset[str] = frozenset({
    "apartment",          # Generic alias
    "apartment_building", # Sprint 2.21.3 classifier canonical
})

# The 9 columns selected from developer_inventory for engine consumption.
# Order matches the SELECT in `fetch_for_district`.
_SELECT_COLUMNS: tuple[str, ...] = (
    "developer", "project", "district", "unit_type",
    "area_m2", "price_qar", "value_per_m2", "status", "last_verified_at",
)


# ─────────────────────────────────────────────────────────────────────────
# Module-scoped connection lifecycle
# ─────────────────────────────────────────────────────────────────────────

_DB_CONN: Optional[sqlite3.Connection] = None
_DB_PATH_USED: Optional[Path] = None
_ATEXIT_REGISTERED: bool = False


def _close_db_connection() -> None:
    """atexit handler — release the SQLite handle on process exit.

    Idempotent. Also callable from test teardown to reset the cached
    connection (e.g. when switching db_path between test cases).
    """
    global _DB_CONN, _DB_PATH_USED
    if _DB_CONN is not None:
        try:
            _DB_CONN.close()
        except Exception:                         # pragma: no cover
            pass
        _DB_CONN = None
        _DB_PATH_USED = None


def _open_db_connection(db_path: Optional[Path] = None) -> Optional[sqlite3.Connection]:
    """Lazy open. Returns the cached connection or None if unreachable.

    Tests may pass `db_path=` to override the default; if the override
    differs from the cached path the old connection is closed and a new
    one is opened.

    Failure modes (all return None, all log):
      - File does not exist → WARN
      - sqlite3.DatabaseError on connect (corrupt / locked / bad URI) → ERROR
      - OSError on FS access → ERROR

    The engine path tolerates a `None` return — no T3 data means
    `t3_values=None` to `hybrid_valuation_v1` → no T3 row in
    tier_breakdown → identical to 2.21.3 baseline.
    """
    global _DB_CONN, _DB_PATH_USED, _ATEXIT_REGISTERED
    target = Path(db_path) if db_path is not None else Path(DEFAULT_DB_PATH)

    # Reopen if test injected a different path
    if _DB_CONN is not None and _DB_PATH_USED != target:
        _close_db_connection()

    if _DB_CONN is not None:
        return _DB_CONN

    if not target.exists():
        logger.warning(
            "developer_inventory DB not found at %s — fetch_for_district "
            "will return None. (Pre-import or empty deploy?)",
            target,
        )
        return None

    try:
        # Read-only URI mode. `as_posix()` for Windows compatibility.
        uri = f"file:{target.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _DB_CONN = conn
        _DB_PATH_USED = target
        if not _ATEXIT_REGISTERED:
            atexit.register(_close_db_connection)
            _ATEXIT_REGISTERED = True
        return _DB_CONN
    except sqlite3.DatabaseError as e:
        logger.error("Failed to open developer_inventory at %s: %s", target, e)
        return None
    except OSError as e:                          # pragma: no cover
        logger.error("Filesystem error opening %s: %s", target, e)
        return None


# ─────────────────────────────────────────────────────────────────────────
# Freshness computation
# ─────────────────────────────────────────────────────────────────────────

def _compute_freshness(
    last_verified_at: Optional[str],
    today: Optional[date] = None,
    ttl_days: int = DEFAULT_TTL_DAYS,
) -> str:
    """Map `last_verified_at` (ISO date) to 'fresh' or 'stale' against the 90-day TTL.

    - None / empty / unparseable → 'stale' (defensive — if we can't verify,
      treat as stale and let hybrid apply the 0.5× evidence multiplier).
    - `today` is injectable for tests so freshness can be exercised
      deterministically.

    Accepts both `YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SS` shapes — takes the
    first 10 chars and parses as date.
    """
    if not last_verified_at:
        return "stale"
    try:
        verified = date.fromisoformat(str(last_verified_at)[:10])
    except (ValueError, TypeError):
        return "stale"
    now = today if today is not None else date.today()
    age_days = (now - verified).days
    return "stale" if age_days > ttl_days else "fresh"


# ─────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────

def fetch_for_district(
    district: str,
    asset_type: str,
    status_filter: tuple[str, ...] = ("off_plan", "under_construction", "ready"),
    max_age_days: Optional[int] = None,
    db_path: Optional[Path] = None,
    today: Optional[date] = None,
) -> Optional[list[dict[str, Any]]]:
    """Fetch T3 developer-inventory rows for one district + asset_type.

    Returns either:
      - `None` — no DB, no matching rows, query error, or asset_type
        outside `SUPPORTED_ASSET_TYPES`.
      - `list[dict]` — one dict per row, EXACTLY 8 fields matching the
        `hybrid_valuation_v1` dict_new shape:
          value_per_m2_raw, status, last_verified_at, freshness_status,
          developer, project, unit_type, area_m2.

    Parameters:
      district:        canonical GIS ANAME — exact-match WHERE clause.
                       No marketing names; no fuzzy match. (BRIEF §11.3 +
                       Sprint 2.21.4 Step 14 GIS verification.)
      asset_type:      must be in SUPPORTED_ASSET_TYPES. Other types →
                       None (BRIEF §12 single-purpose).
      status_filter:   IN-clause subset of `('off_plan',
                       'under_construction', 'ready')`. Empty tuple → None.
      max_age_days:    None (default per D9) — no fetch-layer filter;
                       stale rows pass through with freshness_status='stale'
                       and hybrid applies the 0.5× multiplier.
                       Integer N — server-side filter excludes rows older
                       than N days. Reserved for future callers; the
                       Sprint 2.21.4 Step 9 integration passes None.
      db_path / today: test injection points (Rule #40 + deterministic
                       freshness exercise).

    Never raises. All failures return None + log.
    """
    if asset_type not in SUPPORTED_ASSET_TYPES:
        logger.info(
            "T3 fetch declined: asset_type=%r outside SUPPORTED_ASSET_TYPES",
            asset_type,
        )
        return None
    if not status_filter:
        logger.info("T3 fetch declined: empty status_filter")
        return None

    con = _open_db_connection(db_path)
    if con is None:
        # Failure already logged by _open_db_connection
        return None

    # Build parameterised query. status_filter expands to a placeholder list.
    status_placeholders = ",".join("?" * len(status_filter))
    where_parts = [
        "district = ?",
        f"status IN ({status_placeholders})",
    ]
    params: list[Any] = [district, *status_filter]

    if max_age_days is not None:
        cutoff = (today or date.today()) - timedelta(days=max_age_days)
        # NULL last_verified_at → excluded by the strict server-side filter.
        # (When max_age_days is None — the default — stale rows DO pass
        # through; see docstring.)
        where_parts.append("last_verified_at >= ?")
        params.append(cutoff.isoformat())

    sql = (
        f"SELECT {', '.join(_SELECT_COLUMNS)} "
        f"FROM developer_inventory "
        f"WHERE {' AND '.join(where_parts)}"
    )

    try:
        rows = con.execute(sql, params).fetchall()
    except sqlite3.DatabaseError as e:
        # Schema drift, corrupt page, locked DB, etc. — engine continues
        # without T3 data.
        logger.error(
            "T3 query failed (district=%r asset_type=%r status=%r): %s",
            district, asset_type, status_filter, e,
        )
        return None

    if not rows:
        return None

    out: list[dict[str, Any]] = []
    for r in rows:
        # value_per_m2_raw: prefer the stored auto-computed value (D5 +1);
        # fall back to price_qar / area_m2 if NULL or non-positive. Skip
        # the row only if both paths fail.
        v_raw = r["value_per_m2"]
        if v_raw is None or not isinstance(v_raw, (int, float)) or v_raw <= 0:
            try:
                area = float(r["area_m2"])
                price = float(r["price_qar"])
                if area <= 0:
                    raise ValueError(f"non-positive area_m2={area}")
                v_raw = price / area
            except (TypeError, ValueError, ZeroDivisionError) as e:
                logger.warning(
                    "T3 row dev=%r proj=%r unit=%r area=%r price=%r — "
                    "invalid value_per_m2 derivation (%s); skipped",
                    r["developer"], r["project"], r["unit_type"],
                    r["area_m2"], r["price_qar"], e,
                )
                continue

        out.append({
            "value_per_m2_raw": float(v_raw),
            "status": r["status"],
            "last_verified_at": r["last_verified_at"],
            "freshness_status": _compute_freshness(r["last_verified_at"], today=today),
            "developer": r["developer"],
            "project": r["project"],
            "unit_type": r["unit_type"],
            "area_m2": float(r["area_m2"]),
        })

    return out if out else None


# ─────────────────────────────────────────────────────────────────────────
# Top-level exports for Step 10 tests (Rule #40)
# ─────────────────────────────────────────────────────────────────────────

__all__ = [
    "fetch_for_district",
    "_compute_freshness",
    "_open_db_connection",
    "_close_db_connection",
    "DEFAULT_TTL_DAYS",
    "DEFAULT_DB_PATH",
    "SUPPORTED_ASSET_TYPES",
]
