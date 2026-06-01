"""
instrumentation.py — Beta prediction capture + feedback.
Sprint 2.22.0a.16: pre-activation PRIVACY HARDENING of the a15 capture.

DORMANT BY DEFAULT. Persists NOTHING unless BOTH are true at runtime:
  * EVAL_CAPTURE_ENABLED is truthy  (feature flag — OFF by default), AND
  * DATABASE_URL is set             (a Postgres target is configured).
Dormant => every entry point is a silent no-op => ZERO data footprint.
ACTIVATION (flag + DB [+ CAPTURE_ENC_KEY]) is counsel-gated (PDPPL §8.1 +
cross-border §8.2 + the gate-11 capture-surface security pass) — NOT part of
shipping this code.

Privacy design (Sprint 2.22.0a.16):
  * `id` (UUID) is the SOLE surrogate key AND the SOLE join target. The
    address-embedding `valuation_id` (THM-…) is NEVER stored — it stays
    display-only in the API response. In active mode `capture_prediction`
    RETURNS the UUID so the handler can echo it (`capture_id`); feedback
    carries it back as `prediction_id` (FK -> prediction.id).
  * Address: `zone` is PLAINTEXT (coarse; needed for zone-level aggregation,
    low re-id alone). `street` + `building` are ENCRYPTED (Fernet) and
    separately droppable. Encryption is gated on CAPTURE_ENC_KEY — with no key
    the precise columns are NULL (NEVER plaintext). Key/cipher go live at
    gate-11.
  * Retention (D2): created_at + 180-day expiry. The dormant aggregate+purge
    job collapses expired per-record rows to ZONE-LEVEL aggregates
    (prediction_zone_agg) and DROPS street/building + per-record
    transacted_price (feedback cascades). erase_prediction() is a row-level
    data-subject erasure (row + encrypted address + FK feedback). Backup
    erasure is an activation RUNBOOK step (short PG backup retention).
  * NO free-text `note` (D1). The client IP is NEVER stored.

Capture reads ONLY the engine `result` + request identifiers; failures are
swallowed; the valuation path is never altered or broken. psycopg2 +
cryptography are imported LAZILY (reached only when active [+ key]) so the
dormant path needs neither installed.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

log = logging.getLogger("thammen.instrumentation")

_TRUTHY = {'1', 'true', 'yes', 'on'}
_RETENTION_DAYS = 180   # D2 — per-record measurement window


# ── activation gates ──────────────────────────────────────────────────────

def capture_enabled() -> bool:
    """Feature flag, OFF by default (opt-IN; mirrors the HYBRID_APARTMENTS_ENABLED
    / T3_INVENTORY_ENABLED env-flag convention)."""
    return os.getenv('EVAL_CAPTURE_ENABLED', '').strip().lower() in _TRUTHY


def db_available() -> bool:
    """True only when a Postgres target is configured (add-on intentionally NOT
    provisioned until counsel clears the location — §8.2)."""
    return bool(os.getenv('DATABASE_URL', '').strip())


def is_active() -> bool:
    """Writes happen ONLY when both gates pass."""
    return capture_enabled() and db_available()


# ── encryption hook (Fernet; gated on CAPTURE_ENC_KEY; no-op without it) ────

def _encrypt(plaintext) -> Optional[str]:
    """Encrypt a precise re-identifier (street / building) for at-rest storage.
    Returns None when there is no key (dormant / pre-gate-11) OR no value — so
    the precise columns are NEVER written in plaintext. Cipher = Fernet
    (AES-128-CBC + HMAC, authenticated). cryptography is imported lazily."""
    key = os.getenv('CAPTURE_ENC_KEY', '').strip()
    if not key or plaintext is None:
        return None
    from cryptography.fernet import Fernet  # lazy — only when a key is set
    return Fernet(key.encode()).encrypt(str(plaintext).encode()).decode()


# ── pure record builders (no DB I/O — unit-testable) ───────────────────────

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_prediction_record(result: dict, inputs: Optional[dict] = None) -> dict:
    """Engine `result` + request identifiers -> a minimized, privacy-hardened
    record. `id` (UUID) is the sole key; NO valuation_id is stored; street /
    building are ENCRYPTED (NULL without a key); zone is plaintext. Refusals map
    cleanly (value=None, method='insufficient_data', no accuracy.tier)."""
    result = result or {}
    inputs = inputs or {}
    val = result.get('valuation') or {}
    acc = result.get('accuracy') or {}
    muc = result.get('material_uncertainty') or {}
    now = _utc_now()
    return {
        'id': str(uuid.uuid4()),                        # sole surrogate key + join target
        'zone': inputs.get('zone'),                     # PLAINTEXT (coarse; for aggregation)
        'street_enc': _encrypt(inputs.get('street')),   # ENCRYPTED (None without a key)
        'building_enc': _encrypt(inputs.get('building')),
        'value': val.get('amount'),                     # None on refusal
        'range_low': val.get('low'),
        'range_high': val.get('high'),
        'method': val.get('method'),                    # 'insufficient_data' on refusal (§8.4)
        'tier': acc.get('tier'),                        # accuracy tier; None on refusal
        'muc': muc.get('level'),                        # 'moderate' | 'high' | 'critical'
        'created_at': now.isoformat(),
        'expires_at': (now + timedelta(days=_RETENTION_DAYS)).isoformat(),
    }


def build_feedback_record(payload: dict) -> dict:
    """Validated feedback payload -> minimized record, FK'd to prediction.id via
    `prediction_id` (the UUID returned in active mode). NO free-text note (D1);
    NO valuation_id."""
    payload = payload or {}
    return {
        'id': str(uuid.uuid4()),
        'prediction_id': payload.get('prediction_id'),       # UUID FK -> prediction.id
        'outcome': payload.get('outcome'),
        'transacted_price': payload.get('transacted_price'),  # plaintext during window
        'created_at': _utc_now().isoformat(),
    }


# ── DB I/O (Postgres; lazy driver; reached only when is_active()) ──────────

_PREDICTION_COLS = ('id', 'zone', 'street_enc', 'building_enc', 'value',
                    'range_low', 'range_high', 'method', 'tier', 'muc',
                    'created_at', 'expires_at')
_FEEDBACK_COLS = ('id', 'prediction_id', 'outcome', 'transacted_price', 'created_at')

_DDL = """
CREATE TABLE IF NOT EXISTS prediction (
    id            TEXT PRIMARY KEY,
    zone          INTEGER,
    street_enc    TEXT,
    building_enc  TEXT,
    value         DOUBLE PRECISION,
    range_low     DOUBLE PRECISION,
    range_high    DOUBLE PRECISION,
    method        TEXT,
    tier          TEXT,
    muc           TEXT,
    created_at    TIMESTAMPTZ,
    expires_at    TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS feedback (
    id                TEXT PRIMARY KEY,
    prediction_id     TEXT REFERENCES prediction(id) ON DELETE CASCADE,
    outcome           TEXT,
    transacted_price  DOUBLE PRECISION,
    created_at        TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS prediction_zone_agg (
    zone          INTEGER,
    period        TEXT,
    n             INTEGER,
    value_p25     DOUBLE PRECISION,
    value_median  DOUBLE PRECISION,
    value_p75     DOUBLE PRECISION,
    created_at    TIMESTAMPTZ,
    PRIMARY KEY (zone, period)
);
"""


def _connect():
    import psycopg2  # lazy — the dormant path needs no driver
    return psycopg2.connect(os.environ['DATABASE_URL'])


def _ensure_schema(conn) -> None:
    cur = conn.cursor()
    cur.execute(_DDL)
    conn.commit()
    cur.close()


def _insert(table, cols, record) -> None:
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


# ── guarded entry points (never raise into the caller) ─────────────────────

def capture_prediction(result: dict, inputs: Optional[dict] = None) -> Optional[str]:
    """Persist ONE prediction iff active; RETURN its UUID `id` (so the handler
    can echo it as `capture_id` and feedback can FK to it), else None. Dormant
    -> None, no write, no mutation of `result`. Failures are swallowed."""
    if not is_active():
        return None
    try:
        rec = build_prediction_record(result, inputs)
        _insert('prediction', _PREDICTION_COLS, rec)
        return rec['id']
    except Exception:
        log.warning("prediction capture failed (non-fatal)", exc_info=True)
        return None


def capture_feedback(payload: dict) -> bool:
    """Persist ONE feedback record (FK'd via prediction_id) iff active; return
    True iff written. Same isolation guarantee."""
    if not is_active():
        return False
    try:
        _insert('feedback', _FEEDBACK_COLS, build_feedback_record(payload))
        return True
    except Exception:
        log.warning("feedback capture failed (non-fatal)", exc_info=True)
        return False


# ── retention: dormant aggregate+purge + data-subject erasure ──────────────

def aggregate_and_purge_expired(period: Optional[str] = None) -> int:
    """DORMANT retention job (runs ONLY when active). Collapse prediction rows
    past `expires_at` into ZONE-LEVEL aggregates (prediction_zone_agg), then
    DELETE the per-record rows — dropping street/building(+enc) and per-record
    transacted_price (feedback cascades via the FK). Returns the number of
    per-record rows purged; 0 when dormant."""
    if not is_active():
        return 0
    conn = _connect()
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        tag = period or _utc_now().strftime('%Y-%m')
        # zone-level value distribution of the expired rows -> aggregate (no identifiers)
        cur.execute(
            "INSERT INTO prediction_zone_agg "
            "(zone, period, n, value_p25, value_median, value_p75, created_at) "
            "SELECT zone, %s, COUNT(*), "
            "percentile_cont(0.25) WITHIN GROUP (ORDER BY value), "
            "percentile_cont(0.50) WITHIN GROUP (ORDER BY value), "
            "percentile_cont(0.75) WITHIN GROUP (ORDER BY value), %s "
            "FROM prediction WHERE expires_at < now() GROUP BY zone "
            "ON CONFLICT (zone, period) DO NOTHING",
            (tag, _utc_now().isoformat()))
        # drop the identifying per-record rows (feedback cascades via the FK)
        cur.execute("DELETE FROM prediction WHERE expires_at < now()")
        purged = cur.rowcount
        conn.commit()
        cur.close()
        return purged if purged is not None else 0
    finally:
        conn.close()


def erase_prediction(prediction_id: str) -> bool:
    """Data-subject erasure (dormant unless active): delete the live row — incl.
    its encrypted address columns — and cascade its feedback. Backups are erased
    via the activation RUNBOOK (short PG backup retention). Returns True iff a
    row was deleted."""
    if not is_active() or not prediction_id:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM prediction WHERE id = %s", (prediction_id,))
        deleted = (cur.rowcount or 0) > 0
        conn.commit()
        cur.close()
        return deleted
    finally:
        conn.close()
