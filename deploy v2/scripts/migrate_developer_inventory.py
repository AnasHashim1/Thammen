#!/usr/bin/env python3
"""
scripts/migrate_developer_inventory.py — Sprint 2.21.4 Step 3

Apply + verify the developer_inventory schema (Step 2 DDL) against
`developer_inventory.sqlite`. Idempotent: the second and third runs are
true no-ops (no DB writes) when the schema is already at version 1.

WORKFLOW (BRIEF §7 amended ordering 2026-05-25)
  1. Anas sign-off (Step 15 in BRIEF)
  2. **This script** — applies + verifies schema locally (Step 16 prereq)
  3. CSV importer (`import_developer_inventory.py`) populates rows locally
  4. `git add developer_inventory.sqlite` + commit + subtree push (Steps 17-18)
  5. Deployed slug ships with populated DB

Heroku slug filesystem is ephemeral — running this script (or the
importer) on Heroku post-deploy would write to a dyno-local FS that
gets wiped on next restart. The commit-then-deploy pattern mirrors
`building_age_cache.sqlite` (Sprint 2.15.1).

USAGE
  python scripts/migrate_developer_inventory.py
  python scripts/migrate_developer_inventory.py --dry-run
  python scripts/migrate_developer_inventory.py --db-path /tmp/test.sqlite
  python scripts/migrate_developer_inventory.py --verbose

EXIT CODES
  0  schema applied / verified at version 1
  1  schema drift detected (live schema diverges from DDL)
  2  DDL file unreadable or corrupt
  3  database open / write error
"""

from __future__ import annotations
import argparse
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


SCHEMA_VERSION = "1"
SCHEMA_KEY = "developer_inventory_schema_version"
LAST_RUN_KEY = "developer_inventory_last_migration_run_at"

# Defaults — caller may override via --db-path / --ddl-path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "developer_inventory.sqlite"
DEFAULT_DDL_PATH = PROJECT_ROOT / "migrations" / "2p21p4_developer_inventory.sql"


# ─────────────────────────────────────────────────────────────────────────
# Expected schema spec (the canonical contract this script enforces)
# ─────────────────────────────────────────────────────────────────────────

# Format: (cid_ignored, name, type_upper, notnull_bool, pk_bool)
EXPECTED_COLUMNS_DEVELOPER_INVENTORY: tuple[tuple[str, str, bool, bool], ...] = (
    ("listing_id",           "INTEGER", False, True),
    ("developer",             "TEXT",    True,  False),
    ("district",              "TEXT",    True,  False),
    ("unit_type",             "TEXT",    True,  False),
    ("area_m2",               "REAL",    True,  False),
    ("price_qar",             "INTEGER", True,  False),
    ("status",                "TEXT",    True,  False),
    ("captured_at",           "TEXT",    True,  False),
    ("project",               "TEXT",    False, False),
    ("sub_area",              "TEXT",    False, False),
    ("completion_year",       "INTEGER", False, False),
    ("payment_plan_summary",  "TEXT",    False, False),
    ("source_url",            "TEXT",    False, False),
    ("captured_by",           "TEXT",    False, False),
    ("last_verified_at",      "TEXT",    False, False),
    ("notes_ar",              "TEXT",    False, False),
    ("value_per_m2",          "REAL",    False, False),
)

EXPECTED_COLUMNS_SCHEMA_META: tuple[tuple[str, str, bool, bool], ...] = (
    ("key",        "TEXT", False, True),
    ("value",      "TEXT", True,  False),
    ("applied_at", "TEXT", True,  False),
)

EXPECTED_TABLES = {"developer_inventory", "schema_meta"}

EXPECTED_NAMED_INDEXES = {
    "idx_developer_inventory_district_status",
    "idx_developer_inventory_last_verified",
}

# D8 amended composite — price_qar deliberately excluded
EXPECTED_UNIQUE_COLUMNS = ("developer", "project", "unit_type", "area_m2")


# ─────────────────────────────────────────────────────────────────────────
# Schema verification helpers
# ─────────────────────────────────────────────────────────────────────────

def _fetch_columns(con: sqlite3.Connection, table: str) -> list[tuple[str, str, bool, bool]]:
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return [(name, (ctype or "").upper(), bool(notnull), bool(pk))
            for _cid, name, ctype, notnull, _dflt, pk in rows]


def _fetch_table_names(con: sqlite3.Connection) -> set[str]:
    rows = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {r[0] for r in rows}


def _fetch_named_indexes(con: sqlite3.Connection) -> set[str]:
    rows = con.execute(
        "SELECT name FROM sqlite_master WHERE type='index' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {r[0] for r in rows}


def _fetch_unique_column_sets(con: sqlite3.Connection, table: str) -> list[tuple[str, ...]]:
    """Return every UNIQUE-index column tuple for the table (preserves order)."""
    out: list[tuple[str, ...]] = []
    idx_list = con.execute(f"PRAGMA index_list({table})").fetchall()
    # PRAGMA index_list columns: (seq, name, unique, origin, partial)
    for _seq, name, is_unique, _origin, _partial in idx_list:
        if not is_unique:
            continue
        info = con.execute(f"PRAGMA index_info({name})").fetchall()
        # PRAGMA index_info columns: (seqno, cid, name)
        cols = tuple(r[2] for r in sorted(info, key=lambda r: r[0]))
        out.append(cols)
    return out


def verify_schema(con: sqlite3.Connection, verbose: bool = False) -> tuple[bool, list[str]]:
    """Compare live schema to EXPECTED_*. Return (ok, drifts).

    Drift list is empty iff schema matches exactly. Otherwise each drift is
    a human-readable diagnostic line.
    """
    drifts: list[str] = []

    # 1. Tables
    tables = _fetch_table_names(con)
    missing = EXPECTED_TABLES - tables
    if missing:
        drifts.append(f"missing tables: {sorted(missing)}")
    extra = tables - EXPECTED_TABLES
    if extra:
        # Extra tables are tolerated (other Sprints may share the same DB
        # file in the future); just note them in verbose mode
        if verbose:
            drifts.append(f"NOTE extra tables present (tolerated): {sorted(extra)}")

    # Early return if main table missing — column checks would crash
    if "developer_inventory" not in tables:
        return (False, drifts)

    # 2. developer_inventory columns
    actual_cols = _fetch_columns(con, "developer_inventory")
    expected_cols = list(EXPECTED_COLUMNS_DEVELOPER_INVENTORY)
    if len(actual_cols) != len(expected_cols):
        drifts.append(
            f"developer_inventory column count: expected {len(expected_cols)}, "
            f"got {len(actual_cols)}"
        )
    for i, (exp, act) in enumerate(zip(expected_cols, actual_cols)):
        if exp != act:
            drifts.append(
                f"developer_inventory col[{i}]: expected {exp}, got {act}"
            )

    # 3. schema_meta columns
    if "schema_meta" in tables:
        actual_meta = _fetch_columns(con, "schema_meta")
        expected_meta = list(EXPECTED_COLUMNS_SCHEMA_META)
        if len(actual_meta) != len(expected_meta):
            drifts.append(
                f"schema_meta column count: expected {len(expected_meta)}, "
                f"got {len(actual_meta)}"
            )
        for i, (exp, act) in enumerate(zip(expected_meta, actual_meta)):
            if exp != act:
                drifts.append(f"schema_meta col[{i}]: expected {exp}, got {act}")

    # 4. Named indexes (the two we declared in DDL §2)
    named_idx = _fetch_named_indexes(con)
    missing_idx = EXPECTED_NAMED_INDEXES - named_idx
    if missing_idx:
        drifts.append(f"missing named indexes: {sorted(missing_idx)}")
    # Extra indexes tolerated (auto-UNIQUE indexes show up here too, but
    # sqlite_autoindex_* are filtered by the 'sqlite_%' clause in _fetch_named_indexes)
    extra_idx = named_idx - EXPECTED_NAMED_INDEXES
    if extra_idx and verbose:
        drifts.append(f"NOTE extra named indexes (tolerated): {sorted(extra_idx)}")

    # 5. UNIQUE constraint on developer_inventory (D8 amended)
    uniques = _fetch_unique_column_sets(con, "developer_inventory")
    # The expected UNIQUE column set should appear at least once. Any
    # additional UNIQUE indexes (e.g. unique single-column indexes added
    # by future Sprints) are tolerated.
    if EXPECTED_UNIQUE_COLUMNS not in uniques:
        drifts.append(
            f"D8 UNIQUE constraint missing: expected columns "
            f"{EXPECTED_UNIQUE_COLUMNS}, found UNIQUE sets {uniques}"
        )

    # Filter NOTE-only entries out of the drift-detection result
    real_drifts = [d for d in drifts if not d.startswith("NOTE ")]
    return (not real_drifts, drifts)


# ─────────────────────────────────────────────────────────────────────────
# Migration orchestration
# ─────────────────────────────────────────────────────────────────────────

def _read_ddl(ddl_path: Path) -> str:
    try:
        text = ddl_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"[migrate] ERROR: cannot read DDL at {ddl_path}: {e}", file=sys.stderr)
        sys.exit(2)
    if not text.strip():
        print(f"[migrate] ERROR: DDL file at {ddl_path} is empty", file=sys.stderr)
        sys.exit(2)
    return text


def _current_version(con: sqlite3.Connection) -> Optional[str]:
    try:
        row = con.execute(
            "SELECT value FROM schema_meta WHERE key = ?", (SCHEMA_KEY,)
        ).fetchone()
    except sqlite3.OperationalError:
        # schema_meta doesn't exist yet — first run
        return None
    return row[0] if row else None


def _stamp_version(con: sqlite3.Connection) -> None:
    """Write the version + last-run-at rows. Called only when we actually
    advanced the schema (true no-op on subsequent runs)."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with con:
        con.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value, applied_at) "
            "VALUES (?, ?, ?)",
            (SCHEMA_KEY, SCHEMA_VERSION, now),
        )
        con.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value, applied_at) "
            "VALUES (?, ?, ?)",
            (LAST_RUN_KEY, now, now),
        )


def migrate(db_path: Path, ddl_path: Path, dry_run: bool = False,
            verbose: bool = False) -> int:
    """Apply + verify schema. Returns process exit code (0=ok, 1=drift, 3=db err)."""
    print(f"[migrate] DDL:     {ddl_path}")
    print(f"[migrate] DB:      {db_path}")
    print(f"[migrate] mode:    {'DRY-RUN (read-only)' if dry_run else 'APPLY + VERIFY'}")

    ddl_text = _read_ddl(ddl_path)

    try:
        with closing(sqlite3.connect(db_path)) as con:
            # ── Phase 0: capture pre-state ──
            pre_version = _current_version(con)
            if verbose:
                print(f"[migrate]   pre-state schema version: {pre_version!r}")

            # ── Phase 1: apply DDL (idempotent via IF NOT EXISTS) ──
            if not dry_run:
                with con:
                    con.executescript(ddl_text)
                print("[migrate] Phase 1: executescript completed (idempotent)")
            else:
                print("[migrate] Phase 1: SKIPPED (dry-run)")

            # ── Phase 2: verify schema ──
            ok, drifts = verify_schema(con, verbose=verbose)
            print(f"[migrate] Phase 2: schema verify {'OK' if ok else 'DRIFT'}")
            for d in drifts:
                if d.startswith("NOTE "):
                    print(f"[migrate]   {d}")
                else:
                    print(f"[migrate]   DRIFT: {d}", file=sys.stderr)
            if not ok:
                return 1

            # ── Phase 3: version stamping (true no-op on subsequent runs) ──
            current = _current_version(con)
            if current == SCHEMA_VERSION:
                print(f"[migrate] Phase 3: version already at {SCHEMA_VERSION} "
                      f"— no write (true no-op)")
            else:
                if dry_run:
                    print(f"[migrate] Phase 3: SKIPPED (dry-run; "
                          f"would have stamped {SCHEMA_KEY}={SCHEMA_VERSION})")
                else:
                    _stamp_version(con)
                    print(f"[migrate] Phase 3: stamped {SCHEMA_KEY}={SCHEMA_VERSION}, "
                          f"{LAST_RUN_KEY}=now")

            # ── Final state ──
            final_version = _current_version(con)
            last_run = con.execute(
                "SELECT value FROM schema_meta WHERE key = ?",
                (LAST_RUN_KEY,),
            ).fetchone()
            print(f"[migrate] DONE: schema_version={final_version!r}, "
                  f"last_migration_run_at={last_run[0] if last_run else 'N/A'}")
            return 0

    except sqlite3.DatabaseError as e:
        print(f"[migrate] ERROR: SQLite failure: {e}", file=sys.stderr)
        return 3
    except OSError as e:
        print(f"[migrate] ERROR: filesystem failure: {e}", file=sys.stderr)
        return 3


# ─────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Apply + verify Sprint 2.21.4 developer_inventory schema."
    )
    ap.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH,
                    help=f"SQLite DB path (default: {DEFAULT_DB_PATH})")
    ap.add_argument("--ddl-path", type=Path, default=DEFAULT_DDL_PATH,
                    help=f"DDL .sql file path (default: {DEFAULT_DDL_PATH})")
    ap.add_argument("--dry-run", action="store_true",
                    help="Verify only; no DDL apply, no version stamping.")
    ap.add_argument("--verbose", action="store_true",
                    help="Print extra diagnostic lines (NOTE entries, pre-state).")
    args = ap.parse_args(argv)
    return migrate(args.db_path, args.ddl_path,
                   dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":                       # pragma: no cover
    sys.exit(main())
