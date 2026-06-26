"""
condition_calibrator.py
=======================

Sprint 2.22.0b.71 — Condition-axis calibration (B-2 adaptable infrastructure).

Builds ``condition_adjustments.sqlite`` — the READ-ONLY, swappable source of the
per-grade effective-age PENALTIES the DRC engine reads
(``evaluate_unified._lookup_condition_penalty``). THE MECHANISM lives in the engine
and never changes; this offline tool produces the NUMBERS. This is the cap_rates.sqlite
precedent (Operational_Rules #43): a committed read-only snapshot, rebuilt offline, that
the engine safe-falls away from to a hardcoded fallback.

The PO's binding directive («الرقم يتغيّر لا الكود»): when the GT-2 confirmed-sale corpus
reaches n>=20 per (area, stratum, condition) cell, ``calibrate_from_corpus`` re-fits the
numbers and DROP+recreates the DB; the engine reads the new DB with ZERO code change.

The b16/E25 discipline: at n=1 we SEED from the single certified bank appraisal
(V001 / TD 93317) — i.e. the existing b13 condition ladder RE-SOURCED, disclosed as
INDICATIVE — never an invented coefficient, never chasing asking prices (E1/E25).

VALUE-INVARIANCE CONTRACT: ``_SEED_PENALTIES`` MUST equal
``evaluate_unified.COST_CONDITION_PENALTY`` (the sync-guard test
``test_sprint_2_22_0b71.py`` enforces it), so seeding is a value NO-OP — the engine
produces byte-identical results whether the DB is present (seed) or absent (hardcoded
fallback). A grade absent from the DB resolves to the engine's
``COST_DEFAULT_PENALTY`` (8) — so the baseline (average, +8) is intentionally NOT seeded
as a grade row.

Pure stdlib (sqlite3 + json + statistics). No network. Run:  python condition_calibrator.py
"""

import json
import os
import sqlite3
import statistics
from collections import defaultdict
from datetime import datetime, timezone

_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'condition_adjustments.sqlite')

# ── The n=1 SEED ladder — MUST mirror evaluate_unified.COST_CONDITION_PENALTY ──
# (the sync-guard test asserts equality so the two can never drift). These are the b13
# condition penalties (effective-age deltas) re-sourced from V001. The no-input baseline
# (average → +8, evaluate_unified.COST_DEFAULT_PENALTY) is the engine-side fallback and is
# deliberately NOT a grade row (a condition absent from the DB → engine .get(..., 8)).
_SEED_PENALTIES = {
    'excellent': -2, 'renovated': -3, 'new': 0,
    'good': 5, 'very-good': 5, 'very_good': 5,
    'fair': 15,
    'poor': 25, 'dilapidated': 25, 'teardown': 25,
}

# Sample-size gates (docs/Empirical_Findings.md §3 / Rule E4): n>=20 reliable, 10-19
# indicative, <10 → not credible (the seed stands).
_CONF_RELIABLE_N = 20
_CONF_INDICATIVE_N = 10

_SCHEMA = """
CREATE TABLE condition_adjustments (
    area_match_key     TEXT,            -- NULL = global (any area)
    built_type_stratum TEXT,            -- NULL = any stratum (Rule E4)
    condition          TEXT NOT NULL,   -- grade key (lowercase)
    penalty_years      REAL NOT NULL,   -- effective-age delta the engine reads
    sample_size        INTEGER,         -- n (1 for the V001 seed)
    confidence         TEXT,            -- reliable (n>=20) / indicative / fallback
    source             TEXT,            -- 'v001_seed' now; 'gt_corpus' later
    last_updated       TEXT,
    notes              TEXT
);
"""


def _now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _fresh_db(path):
    """DROP + recreate (the schema is fixed; the calibrator owns the file)."""
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    return conn


def _insert_seed(conn, ts, note):
    for cond, pen in _SEED_PENALTIES.items():
        conn.execute(
            "INSERT INTO condition_adjustments VALUES (?,?,?,?,?,?,?,?,?)",
            (None, None, cond, float(pen), 1, 'indicative', 'v001_seed', ts, note),
        )


def build_seed_db(path=_DB):
    """n=1 seed: GLOBAL rows (NULL area, NULL stratum) from the V001 ladder, disclosed
    INDICATIVE (n=1 is NOT 'reliable'). Seed == COST_CONDITION_PENALTY → value no-op."""
    conn = _fresh_db(path)
    with conn:
        _insert_seed(
            conn, _now(),
            'seed = the b13 condition ladder re-sourced from the V001 / TD-93317 certified '
            'appraisal (n=1, indicative — never empirically calibrated until GT-2 n>=20)',
        )
    conn.close()
    return path


def calibrate_from_corpus(corpus, path=_DB):
    """Re-fit penalties from the GT-2 confirmed-sale corpus, then DROP+recreate the DB.

    Each observation supplies an effective-age PENALTY per (area_match_key,
    built_type_stratum, condition) — derived offline from the DOCUMENTED sale's residual
    vs the DRC curve (the b19 / validate_gt_sheet kit; intake rule: no observation without
    a document, E1/E25). We bin by cell, take the MEDIAN penalty, gate confidence on n,
    and keep the GLOBAL seed as the always-present base (so an un-calibrated grade still
    resolves). The engine code is UNCHANGED — only this DB swaps.

    ``corpus`` = a list of dicts (or a path to a JSON list) with at least:
        {condition, penalty_years_observed, area_match_key?, built_type_stratum?}
    Returns (path, n_calibrated_cells)."""
    rows = (json.load(open(corpus, encoding='utf-8'))
            if isinstance(corpus, str) else list(corpus))
    cells = defaultdict(list)
    for r in rows:
        cond = (r.get('condition') or '').strip().lower()
        obs = r.get('penalty_years_observed')
        if not cond or obs is None:
            continue
        cells[(r.get('area_match_key'), r.get('built_type_stratum'), cond)].append(float(obs))

    conn = _fresh_db(path)
    ts = _now()
    n_calibrated = 0
    with conn:
        _insert_seed(conn, ts, 'global seed base (retained under per-cell calibration)')
        for (area, stratum, cond), obs in sorted(cells.items(), key=lambda kv: str(kv[0])):
            n = len(obs)
            if n < _CONF_INDICATIVE_N:
                continue  # <10 → not credible → the seed stands for this cell
            conf = 'reliable' if n >= _CONF_RELIABLE_N else 'indicative'
            conn.execute(
                "INSERT INTO condition_adjustments VALUES (?,?,?,?,?,?,?,?,?)",
                (area, stratum, cond, round(statistics.median(obs), 2), n, conf,
                 'gt_corpus', ts, f'calibrated from {n} documented GT-2 sales'),
            )
            n_calibrated += 1
    conn.close()
    return path, n_calibrated


if __name__ == '__main__':
    p = build_seed_db()
    print(f'Seeded condition_adjustments.sqlite (n=1, V001 ladder) -> {p}')
    c = sqlite3.connect(p)
    try:
        for row in c.execute("SELECT condition, penalty_years, confidence, source "
                             "FROM condition_adjustments ORDER BY penalty_years"):
            print('   ', row)
    finally:
        c.close()
