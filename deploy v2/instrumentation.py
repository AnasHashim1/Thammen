"""
instrumentation.py — Beta prediction capture + feedback (Sprint 2.22.0a.15).

DORMANT BY DEFAULT. Persists NOTHING unless BOTH are true at runtime:
  * EVAL_CAPTURE_ENABLED is truthy   (feature flag — OFF by default), AND
  * DATABASE_URL is set              (a Postgres target is configured).
When either is absent every entry point is a silent no-op -> ZERO data
footprint. This lets the code ship to production safely BEFORE the PDPPL
data policy (BRIEF §8.1) and the cross-border ruling (BRIEF §8.2) are in
place. ACTIVATION = flip the flag + provision a (counsel-cleared) Postgres;
it is NOT part of shipping this code.

NO valuation-logic dependency: capture reads ONLY the engine `result` dict
+ the request identifiers and never mutates them. Any failure is swallowed
(logged) and can NEVER alter or break a valuation response (backward-compat
rule).

Field set is data-minimized (BRIEF §3). The client IP is NOT stored. `id`
is a UUID surrogate primary key; `valuation_id` + address are kept as
separate, independently redactable fields (BRIEF §8.3) so the address can be
purged without losing the join key. Refusals are captured too (BRIEF §8.4):
they arrive as value=None / method='insufficient_data' / no valuation_id.

psycopg2 is imported LAZILY inside `_connect()` only — the module (and the
entire dormant path) imports cleanly without the driver installed.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("thammen.instrumentation")

_TRUTHY = {'1', 'true', 'yes', 'on'}


# ── activation gates ──────────────────────────────────────────────────────

def capture_enabled() -> bool:
    """Feature flag, OFF by default (mirrors the HYBRID_APARTMENTS_ENABLED /
    T3_INVENTORY_ENABLED env-flag convention, but inverted to opt-IN)."""
    return os.getenv('EVAL_CAPTURE_ENABLED', '').strip().lower() in _TRUTHY


def db_available() -> bool:
    """True only when a Postgres target is configured. No DATABASE_URL ->
    dormant (the add-on is intentionally NOT provisioned until counsel clears
    the location — BRIEF §8.2)."""
    return bool(os.getenv('DATABASE_URL', '').strip())


def is_active() -> bool:
    """Capture writes happen ONLY when both gates pass."""
    return capture_enabled() and db_available()


# ── pure record builders (no I/O — fully unit-testable) ────────────────────

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_prediction_record(result: dict, inputs: Optional[dict] = None) -> dict:
    """Map an engine `result` dict + request identifiers -> the minimized
    record. BRIEF §3 field set EXACTLY (12 fields, no more). Defensive .get()
    throughout so refusals map cleanly (value=None, method='insufficient_data',
    no valuation_id, no accuracy.tier)."""
    result = result or {}
    inputs = inputs or {}
    val = result.get('valuation') or {}
    acc = result.get('accuracy') or {}
    muc = result.get('material_uncertainty') or {}
    return {
        'id': str(uuid.uuid4()),                    # UUID surrogate PK (BRIEF §8.3)
        'valuation_id': result.get('valuation_id'),  # None on refusals
        'zone': inputs.get('zone'),                 # address kept separate from id
        'street': inputs.get('street'),
        'building': inputs.get('building'),
        'value': val.get('amount'),                 # None on refusal
        'range_low': val.get('low'),
        'range_high': val.get('high'),
        'method': val.get('method'),                # 'insufficient_data' on refusal (§8.4)
        'tier': acc.get('tier'),                    # accuracy tier (high/moderate/low); None on refusal
        'muc': muc.get('level'),                    # 'moderate' | 'high' | 'critical'
        'ts': _utc_now_iso(),
    }


def build_feedback_record(payload: dict) -> dict:
    """Map a validated feedback payload -> the minimized record, keyed on
    valuation_id with its own UUID `id`."""
    payload = payload or {}
    return {
        'id': str(uuid.uuid4()),
        'valuation_id': payload.get('valuation_id'),
        'outcome': payload.get('outcome'),
        'transacted_price': payload.get('transacted_price'),
        'note': payload.get('note'),
        'ts': _utc_now_iso(),
    }


# ── DB I/O (Postgres; lazy driver; only reached when is_active()) ──────────

_PREDICTION_COLS = ('id', 'valuation_id', 'zone', 'street', 'building',
                    'value', 'range_low', 'range_high', 'method', 'tier', 'muc', 'ts')
_FEEDBACK_COLS = ('id', 'valuation_id', 'outcome', 'transacted_price', 'note', 'ts')

_DDL = """
CREATE TABLE IF NOT EXISTS prediction (
    id            TEXT PRIMARY KEY,
    valuation_id  TEXT,
    zone          INTEGER,
    street        INTEGER,
    building      INTEGER,
    value         DOUBLE PRECISION,
    range_low     DOUBLE PRECISION,
    range_high    DOUBLE PRECISION,
    method        TEXT,
    tier          TEXT,
    muc           TEXT,
    ts            TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS feedback (
    id                TEXT PRIMARY KEY,
    valuation_id      TEXT,
    outcome           TEXT,
    transacted_price  DOUBLE PRECISION,
    note              TEXT,
    ts                TIMESTAMPTZ
);
"""


def _connect():
    """Lazy psycopg2 connection to DATABASE_URL. Imported HERE only, so the
    module and the dormant path never require the driver to be installed."""
    import psycopg2  # noqa: lazy import is intentional (dormant path needs no driver)
    return psycopg2.connect(os.environ['DATABASE_URL'])


def _ensure_schema(conn) -> None:
    cur = conn.cursor()
    cur.execute(_DDL)
    conn.commit()
    cur.close()


def _insert(table: str, cols: tuple, record: dict) -> None:
    conn = _connect()
    try:
        _ensure_schema(conn)
        placeholders = ', '.join(['%s'] * len(cols))
        sql = "INSERT INTO {t} ({c}) VALUES ({p})".format(
            t=table, c=', '.join(cols), p=placeholders)
        cur = conn.cursor()
        cur.execute(sql, tuple(record.get(c) for c in cols))
        conn.commit()
        cur.close()
    finally:
        conn.close()


# ── guarded public entry points (never raise into the caller) ──────────────

def capture_prediction(result: dict, inputs: Optional[dict] = None) -> bool:
    """Persist ONE prediction record iff active; return True iff written.
    Fully isolated: any failure is logged and swallowed — it NEVER raises into
    the evaluate path and NEVER mutates `result` (backward-compat rule)."""
    if not is_active():
        return False
    try:
        _insert('prediction', _PREDICTION_COLS, build_prediction_record(result, inputs))
        return True
    except Exception:
        log.warning("prediction capture failed (non-fatal)", exc_info=True)
        return False


def capture_feedback(payload: dict) -> bool:
    """Persist ONE feedback record iff active; return True iff written. Same
    isolation guarantee as capture_prediction."""
    if not is_active():
        return False
    try:
        _insert('feedback', _FEEDBACK_COLS, build_feedback_record(payload))
        return True
    except Exception:
        log.warning("feedback capture failed (non-fatal)", exc_info=True)
        return False
