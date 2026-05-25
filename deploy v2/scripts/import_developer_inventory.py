#!/usr/bin/env python3
"""
scripts/import_developer_inventory.py — Sprint 2.21.4 Step 4

Strict-pydantic CSV importer for `developer_inventory.sqlite`. Single
canonical write path into the T3 table; the engine never writes (it
reads only via the connector in Step 7).

WORKFLOW (BRIEF §7 amended ordering 2026-05-25)
  Step 14   GIS verification of City Avenues centroid (~2 min, manual)
  Step 15   Anas sign-off
  Step 16   ← THIS SCRIPT: import CSV into developer_inventory.sqlite locally
  Step 17   git add developer_inventory.sqlite + commit
  Step 18   git subtree push --prefix "deploy v2" heroku master
  Step 19   post-deploy H1-H11 walk against deployed slug

Heroku slug filesystem is ephemeral → importer cannot run post-deploy
with persistence. Pattern mirrors building_age_cache.sqlite (Sprint 2.15.1).

DESIGN PRINCIPLES
  - Rule #31: pydantic `extra='forbid'`. Unknown CSV columns are
    structured errors, not silent drops.
  - Rule #39: per-row try/except boundary. One bad row does NOT abort
    the batch. Every rejection collected as a structured dict with
    field name + reason for the operator to fix.
  - Rule #40: top-level importable symbols (InventoryRow, import_csv,
    make_rejection, PROJECT_SENTINEL_UNSPECIFIED, UPSERT_SQL) so tests
    exercise production logic, not replicas.
  - D8 amended (Step 2 soft flag): NULL/empty `project` → sentinel
    string `(unspecified)`. Prevents SQLite NULL-aware UNIQUE bypass.
    Documented in CHANGELOG_v49 §5 when this Step lands.

USAGE
  python scripts/import_developer_inventory.py path/to/inventory.csv
  python scripts/import_developer_inventory.py rows.csv --dry-run
  python scripts/import_developer_inventory.py rows.csv --rejections-log rej.json
  python scripts/import_developer_inventory.py rows.csv --db-path /tmp/test.sqlite

EXIT CODES
  0  all rows imported successfully (zero rejections)
  1  at least one row rejected (count + per-row details on stderr)
  2  CSV unreadable / empty / missing
  3  SQLite open / write error
"""

from __future__ import annotations
import argparse
import csv
import json
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
    ValidationError,
)


# ─────────────────────────────────────────────────────────────────────────
# Constants — mirror DDL (Step 2) and CHANGELOG_v49 §1 D-decisions
# ─────────────────────────────────────────────────────────────────────────

# D8 soft-flag fix: NULL/empty project → sentinel. Without this, SQLite
# treats multiple NULLs as distinct under UNIQUE, bypassing duplicate
# prevention for rows that legitimately lack a project name.
PROJECT_SENTINEL_UNSPECIFIED = "(unspecified)"

# Enums (must match Step 2 DDL CHECK constraints)
ALLOWED_UNIT_TYPES = frozenset({"studio", "1BR", "2BR", "3BR", "4BR", "penthouse"})
ALLOWED_STATUSES = frozenset({"off_plan", "under_construction", "ready"})

# Sales-band sanity (matches connector floor in Sprint 2.21.3)
MIN_PRICE_QAR = 100_000
MAX_PRICE_QAR = 1_000_000_000
MIN_AREA_M2 = 20.0
MAX_AREA_M2 = 5_000.0

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "developer_inventory.sqlite"


# ─────────────────────────────────────────────────────────────────────────
# Pydantic model — strict (Rule #31)
# ─────────────────────────────────────────────────────────────────────────

class InventoryRow(BaseModel):
    """One CSV row → one upsert into developer_inventory.

    Strict by `extra='forbid'`: unknown columns trigger a structured
    rejection with `loc[-1]` = the offending column name.

    Whitespace trimmed automatically on all string fields via
    `str_strip_whitespace=True` (Pydantic 2.x feature). Empty strings
    are converted to None by the CSV layer before construction.
    """
    model_config = ConfigDict(
        extra='forbid',
        str_strip_whitespace=True,
    )

    # ── Required (D4 amended) ──
    developer:   str = Field(min_length=1)
    district:    str = Field(min_length=1)
    unit_type:   str
    area_m2:     float = Field(gt=0)
    price_qar:   int = Field(gt=0)
    status:      str
    captured_at: str = Field(min_length=10)   # ISO YYYY-MM-DD at minimum

    # ── Optional (D5) ──
    project:              Optional[str] = None
    sub_area:             Optional[str] = None
    completion_year:      Optional[int] = None
    payment_plan_summary: Optional[str] = None
    source_url:           Optional[str] = None
    captured_by:          Optional[str] = None
    last_verified_at:     Optional[str] = None
    notes_ar:             Optional[str] = None

    # ── Auto-computed (D5 +1) ──
    value_per_m2: Optional[float] = None   # set by model_validator after fields

    # ── Validators ──

    @field_validator('unit_type')
    @classmethod
    def _validate_unit_type(cls, v: str) -> str:
        if v not in ALLOWED_UNIT_TYPES:
            raise ValueError(
                f"unit_type must be one of {sorted(ALLOWED_UNIT_TYPES)}, got {v!r}"
            )
        return v

    @field_validator('status')
    @classmethod
    def _validate_status(cls, v: str) -> str:
        if v not in ALLOWED_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(ALLOWED_STATUSES)}, got {v!r}"
            )
        return v

    @field_validator('area_m2')
    @classmethod
    def _validate_area_band(cls, v: float) -> float:
        if not (MIN_AREA_M2 <= v <= MAX_AREA_M2):
            raise ValueError(
                f"area_m2={v} outside sanity band [{MIN_AREA_M2}, {MAX_AREA_M2}]"
            )
        return v

    @field_validator('price_qar')
    @classmethod
    def _validate_price_band(cls, v: int) -> int:
        if not (MIN_PRICE_QAR <= v <= MAX_PRICE_QAR):
            raise ValueError(
                f"price_qar={v} outside sales-band [{MIN_PRICE_QAR:,}, {MAX_PRICE_QAR:,}]"
            )
        return v

    @field_validator('completion_year')
    @classmethod
    def _validate_completion_year(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return None
        if not (2020 <= v <= 2050):
            raise ValueError(f"completion_year={v} outside [2020, 2050]")
        return v

    @field_validator('project', mode='before')
    @classmethod
    def _normalize_project_sentinel(cls, v: Any) -> str:
        """D8 soft-flag fix — empty/whitespace/None project → sentinel.

        Runs in mode='before' so the normalization happens prior to
        Pydantic's type coercion. After this, `project` is always a
        non-empty string. Rationale lives in CHANGELOG_v49 §5
        (documented when Step 4 lands).
        """
        if v is None:
            return PROJECT_SENTINEL_UNSPECIFIED
        if isinstance(v, str) and not v.strip():
            return PROJECT_SENTINEL_UNSPECIFIED
        return v

    @model_validator(mode='after')
    def _compute_value_per_m2(self) -> 'InventoryRow':
        """D5 +1 — auto-compute value_per_m2 = price_qar / area_m2.

        Runs after field validation so both inputs are guaranteed
        positive. Stored redundantly per D5; connector reads this
        instead of recomputing.
        """
        self.value_per_m2 = round(self.price_qar / self.area_m2, 2)
        return self


# ─────────────────────────────────────────────────────────────────────────
# Rejection structure
# ─────────────────────────────────────────────────────────────────────────

def make_rejection(row_num: int, raw_row: dict[str, Any],
                   error: Exception) -> dict[str, Any]:
    """Build a structured rejection dict for one bad CSV row.

    Shape:
      {
        'row_num':    int      # 1-indexed source-line number (header=1)
        'field':      str      # the offending column name
        'reason':     str      # pydantic-emitted msg or other reason
        'error_type': str      # e.g. 'extra_forbidden' / 'type_error.float'
        'raw_row':    dict     # the CSV row exactly as received
        'all_errors': list     # full pydantic error list (for multi-field issues)
      }

    The bad field name lives in `field` (Rule #31 contract — mirrors the
    Sprint 2.16.15 Pydantic A2 fix pattern). When the cause is not a
    ValidationError (e.g. sqlite3.IntegrityError on insert), field
    defaults to 'unknown' and reason carries the exception text.
    """
    if isinstance(error, ValidationError):
        errors = error.errors()
        primary = errors[0] if errors else {}
        loc = primary.get('loc', ())
        field_name = str(loc[-1]) if loc else 'unknown'
        return {
            'row_num': row_num,
            'field': field_name,
            'reason': primary.get('msg', 'validation error'),
            'error_type': primary.get('type', 'unknown'),
            'raw_row': dict(raw_row),
            'all_errors': errors,
        }
    return {
        'row_num': row_num,
        'field': 'unknown',
        'reason': str(error),
        'error_type': type(error).__name__,
        'raw_row': dict(raw_row),
        'all_errors': [],
    }


# ─────────────────────────────────────────────────────────────────────────
# Upsert SQL (D8 amended composite key)
# ─────────────────────────────────────────────────────────────────────────

UPSERT_SQL = """
INSERT INTO developer_inventory (
    developer, district, unit_type, area_m2, price_qar, status, captured_at,
    project, sub_area, completion_year, payment_plan_summary, source_url,
    captured_by, last_verified_at, notes_ar, value_per_m2
) VALUES (
    :developer, :district, :unit_type, :area_m2, :price_qar, :status, :captured_at,
    :project, :sub_area, :completion_year, :payment_plan_summary, :source_url,
    :captured_by, :last_verified_at, :notes_ar, :value_per_m2
)
ON CONFLICT (developer, project, unit_type, area_m2) DO UPDATE SET
    -- ALWAYS overwrite (the point of revision upsert per D8 rationale):
    price_qar        = excluded.price_qar,
    value_per_m2     = excluded.value_per_m2,
    status           = excluded.status,
    last_verified_at = excluded.last_verified_at,

    -- PRESERVE existing when new row has NULL, else update:
    sub_area             = COALESCE(excluded.sub_area, sub_area),
    completion_year      = COALESCE(excluded.completion_year, completion_year),
    payment_plan_summary = COALESCE(excluded.payment_plan_summary, payment_plan_summary),
    source_url           = COALESCE(excluded.source_url, source_url),
    captured_by          = COALESCE(excluded.captured_by, captured_by),
    notes_ar             = COALESCE(excluded.notes_ar, notes_ar)

    -- DELIBERATELY NOT updated on conflict:
    --   captured_at   — preserves first-import semantics
    --   district      — preserves the GIS-canonical value from initial capture
"""

# Pre-existence probe — used to classify the upsert outcome as
# 'inserted' vs 'updated' for the report. SQLite UPSERT returns no
# distinction natively; we look up the row first.
EXISTS_SQL = (
    "SELECT 1 FROM developer_inventory "
    "WHERE developer = :developer AND project = :project "
    "AND unit_type = :unit_type AND area_m2 = :area_m2 "
    "LIMIT 1"
)


def upsert_row(con: sqlite3.Connection, row: InventoryRow) -> str:
    """Upsert one validated row. Returns 'inserted' or 'updated'."""
    payload = row.model_dump()
    existed = con.execute(EXISTS_SQL, payload).fetchone() is not None
    con.execute(UPSERT_SQL, payload)
    return 'updated' if existed else 'inserted'


# ─────────────────────────────────────────────────────────────────────────
# Main importer
# ─────────────────────────────────────────────────────────────────────────

def import_csv(csv_path: Path, db_path: Path = DEFAULT_DB_PATH,
               dry_run: bool = False) -> dict[str, Any]:
    """Import a CSV. Returns a report dict.

    Report shape:
      {
        'rows_seen':  int,
        'inserted':   int,
        'updated':    int,
        'rejected':   int,
        'rejections': list[dict],     # structured per-row errors
        'mode':       'apply' | 'dry-run',
      }

    On CSV-level failure (file missing, no header, etc.) the dict
    contains an `'error'` key instead.
    """
    if not csv_path.exists():
        return {'error': f'CSV file not found: {csv_path}',
                'rows_seen': 0, 'rejections': []}

    rejections: list[dict[str, Any]] = []
    inserts = 0
    updates = 0
    rows_seen = 0

    try:
        with closing(sqlite3.connect(db_path)) as con, \
             open(csv_path, encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return {'error': 'CSV has no header row',
                        'rows_seen': 0, 'rejections': []}

            for row_num, raw_row in enumerate(reader, start=2):
                # row 1 is header; first data row is row 2
                rows_seen += 1

                # Convert empty strings to None so Optional fields parse
                # cleanly. Note: this preserves whitespace-only strings,
                # which pydantic's str_strip_whitespace then trims; the
                # `_normalize_project_sentinel` validator handles the
                # whitespace-only project edge case.
                cleaned: dict[str, Any] = {
                    k: (v if (v is not None and v != '') else None)
                    for k, v in raw_row.items()
                }

                try:
                    model = InventoryRow(**cleaned)
                except ValidationError as e:
                    rejections.append(make_rejection(row_num, raw_row, e))
                    continue
                except Exception as e:
                    rejections.append(make_rejection(row_num, raw_row, e))
                    continue

                if dry_run:
                    inserts += 1   # report what would have happened
                    continue

                try:
                    with con:
                        action = upsert_row(con, model)
                    if action == 'inserted':
                        inserts += 1
                    else:
                        updates += 1
                except sqlite3.IntegrityError as e:
                    rejections.append(make_rejection(row_num, raw_row, e))
                except sqlite3.DatabaseError as e:
                    rejections.append(make_rejection(row_num, raw_row, e))

        return {
            'rows_seen': rows_seen,
            'inserted': inserts,
            'updated': updates,
            'rejected': len(rejections),
            'rejections': rejections,
            'mode': 'dry-run' if dry_run else 'apply',
        }

    except sqlite3.DatabaseError as e:
        return {'error': f'SQLite open/write failure: {e}',
                'rows_seen': rows_seen, 'rejections': rejections}
    except OSError as e:
        return {'error': f'filesystem failure: {e}',
                'rows_seen': rows_seen, 'rejections': rejections}


# ─────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────

def _print_summary(report: dict[str, Any], csv_path: Path,
                   db_path: Path, dry_run: bool) -> None:
    print(f"[import] CSV:      {csv_path}")
    print(f"[import] DB:       {db_path}")
    print(f"[import] mode:     {'DRY-RUN (no DB writes)' if dry_run else 'APPLY'}")
    if 'error' in report:
        print(f"[import] ERROR: {report['error']}", file=sys.stderr)
        return
    print(f"[import] rows seen:   {report['rows_seen']}")
    print(f"[import] inserted:    {report.get('inserted', 0)}")
    print(f"[import] updated:     {report.get('updated', 0)}")
    print(f"[import] rejected:    {report['rejected']}")


def _print_rejections(rejections: list[dict[str, Any]]) -> None:
    for r in rejections:
        print(
            f"[import] REJECT row {r['row_num']}: "
            f"field={r['field']!r} type={r['error_type']!r} "
            f"reason={r['reason']!r}",
            file=sys.stderr,
        )


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Import developer-inventory CSV into developer_inventory.sqlite "
                    "(Sprint 2.21.4 Step 16, BRIEF amended ordering).",
    )
    ap.add_argument('csv_path', type=Path, help='CSV file to import')
    ap.add_argument('--db-path', type=Path, default=DEFAULT_DB_PATH,
                    help=f'SQLite DB path (default: {DEFAULT_DB_PATH})')
    ap.add_argument('--dry-run', action='store_true',
                    help='Validate only; no DB writes.')
    ap.add_argument('--rejections-log', type=Path,
                    help='Write structured rejections to this JSON file.')
    args = ap.parse_args(argv)

    report = import_csv(args.csv_path, args.db_path, dry_run=args.dry_run)
    _print_summary(report, args.csv_path, args.db_path, args.dry_run)

    if 'error' in report:
        return 2 if 'not found' in report['error'] or 'header' in report['error'] else 3

    _print_rejections(report['rejections'])

    if args.rejections_log:
        args.rejections_log.write_text(
            json.dumps(report['rejections'], ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        print(f"[import] rejections JSON written to: {args.rejections_log}")

    if report['rejected'] > 0:
        print(
            f"[import] FAIL: {report['rejected']} row(s) rejected. "
            f"Fix the CSV and re-run (rule #31 strict — no silent drops).",
            file=sys.stderr,
        )
        return 1

    print(f"[import] OK: all {report['rows_seen']} rows imported "
          f"(inserted={report.get('inserted', 0)}, "
          f"updated={report.get('updated', 0)}).")
    return 0


if __name__ == '__main__':                       # pragma: no cover
    sys.exit(main())
