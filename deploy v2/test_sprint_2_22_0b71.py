#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isolated test — Sprint 2.22.0b.71: condition-axis adaptable calibration infra (B-2).

The condition penalty (effective-age delta) is now read from a swappable read-only DB
(condition_adjustments.sqlite, built by condition_calibrator.py) instead of the hardcoded
COST_CONDITION_PENALTY dict — the cap_rates.sqlite precedent (Operational_Rules #43). At
n=1 the DB is SEEDED from the V001 ladder (seed == COST_CONDITION_PENALTY), so it is a
VALUE NO-OP; when the GT-2 corpus reaches n>=20 the calibrator re-fits the numbers and the
engine reads them with ZERO code change («الرقم يتغيّر لا الكود»).

VALUE-INVARIANT — the engine produces byte-identical DRC dicts whether the DB is present
(seed) or absent (hardcoded fallback). Per E14 this exercises the REAL production functions
+ the REAL calibrator.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b71.py
"""
import os
import re
import sys
import tempfile

import evaluate_unified as eu
import condition_calibrator as cc

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f'  PASS  {name}')
    else:
        _failed += 1
        print(f'  FAIL  {name}')


# ── 1. SYNC-GUARD: the seed ladder == the engine's hardcoded ladder (kills drift) ──
check('seed _SEED_PENALTIES == engine COST_CONDITION_PENALTY (the value-invariance guard)',
      cc._SEED_PENALTIES == eu.COST_CONDITION_PENALTY)

# ── 2. committed seed DB present + lookup(grade) == the dict for EVERY grade ──
check('condition_adjustments.sqlite committed + present', os.path.exists(eu._COND_ADJ_DB))
_all_match = True
for grade, expected in eu.COST_CONDITION_PENALTY.items():
    pen, _ = eu._lookup_condition_penalty(grade)
    if pen != expected:
        _all_match = False
        print(f'        grade {grade!r}: lookup {pen} != dict {expected}')
check('lookup(grade) == COST_CONDITION_PENALTY[grade] for EVERY grade (seed == hardcoded)',
      _all_match)

# ── 3. negative trims + new=0 honored (is-not-None, not truthiness); int-typed seed ──
check('lookup(excellent) == -2 (negative trim returned)', eu._lookup_condition_penalty('excellent')[0] == -2)
check('lookup(renovated) == -3', eu._lookup_condition_penalty('renovated')[0] == -3)
check('lookup(new) == 0 (zero, not falsy-dropped)', eu._lookup_condition_penalty('new')[0] == 0)
check('integer seed returns int (byte-identical emit)', isinstance(eu._lookup_condition_penalty('poor')[0], int))
check('provenance: source=v001_seed + confidence=indicative (n=1 disclosed)',
      eu._lookup_condition_penalty('poor')[1].get('source') == 'v001_seed'
      and eu._lookup_condition_penalty('poor')[1].get('confidence') == 'indicative')

# ── 4. unknown / empty condition → (None, None) → engine fallback to default ──
check('lookup(unknown grade) -> (None, None)', eu._lookup_condition_penalty('xyz') == (None, None))
check('lookup(empty) -> (None, None)', eu._lookup_condition_penalty('') == (None, None))

# ── 5. SAFE-FAIL: a missing DB -> (None, None) -> engine uses the hardcoded fallback ──
_real = eu._COND_ADJ_DB
try:
    eu._COND_ADJ_DB = os.path.join(tempfile.gettempdir(), 'NO_SUCH_condition_db_xyz.sqlite')
    check('missing DB -> lookup safe-fails (None, None)',
          eu._lookup_condition_penalty('poor') == (None, None))
finally:
    eu._COND_ADJ_DB = _real

# ── 6. VALUE-INVARIANCE: _cost_approach_value byte-identical DB-present vs DB-absent ──
#     (seed == hardcoded → the penalty is identical whichever path is taken).
_args = dict(land_floor=1_851_260, footprint_max_m2=400, floors=2, age_years=20)
_inv = True
for cond in ('poor', 'excellent', 'new', 'good', 'fair', None, 'average', 'teardown', 'renovated'):
    v_present = eu._cost_approach_value(finish='ordinary', condition=cond, **_args)
    _saved = eu._COND_ADJ_DB
    try:
        eu._COND_ADJ_DB = os.path.join(tempfile.gettempdir(), 'NO_SUCH_condition_db_xyz.sqlite')
        v_absent = eu._cost_approach_value(finish='ordinary', condition=cond, **_args)
    finally:
        eu._COND_ADJ_DB = _saved
    if v_present != v_absent:
        _inv = False
        print(f'        condition={cond!r}: present {v_present} != absent {v_absent}')
check('_cost_approach_value byte-identical with DB present (seed) vs absent (fallback) — VALUE NO-OP',
      _inv)

# ── 7. new=0 distinct from the no-input default (+8): the seam honors a 0 penalty ──
v_new = eu._cost_approach_value(finish='ordinary', condition='new', **_args)
v_default = eu._cost_approach_value(finish='ordinary', condition=None, **_args)
check('condition=new -> penalty 0 (eff_age 20); no-input -> default +8 (eff_age 28)',
      v_new['condition_penalty'] == 0 and v_new['effective_age'] == 20
      and v_default['condition_penalty'] == 8 and v_default['effective_age'] == 28)

# ── 8. CALIBRATOR ROUND-TRIP: a synthetic n>=20 corpus -> 'reliable' row -> the engine
#     reads the NEW numbers with ZERO code change («الرقم يتغيّر لا الكود»). Temp DB only;
#     the committed seed DB is never touched. ──
_tmp = os.path.join(tempfile.gettempdir(), 'b71_roundtrip_condition.sqlite')
try:
    corpus = ([{'condition': 'poor', 'area_match_key': 'مريخ', 'built_type_stratum': 'aging_stock',
                'penalty_years_observed': 30} for _ in range(22)]
              + [{'condition': 'good', 'area_match_key': 'مريخ', 'built_type_stratum': 'aging_stock',
                  'penalty_years_observed': 4} for _ in range(5)])  # n=5 < 10 → gated out
    _, n_cells = cc.calibrate_from_corpus(corpus, path=_tmp)
    check('calibrate_from_corpus emits exactly 1 reliable cell (poor n=22; good n=5 gated out)',
          n_cells == 1)
    _saved = eu._COND_ADJ_DB
    try:
        eu._COND_ADJ_DB = _tmp
        pen_poor, prov_poor = eu._lookup_condition_penalty('poor', 'مريخ', 'aging_stock')
        pen_good, _ = eu._lookup_condition_penalty('good', 'مريخ', 'aging_stock')
        check('engine reads the CALIBRATED poor penalty (30, reliable, gt_corpus) — zero code change',
              pen_poor == 30 and prov_poor.get('confidence') == 'reliable'
              and prov_poor.get('source') == 'gt_corpus')
        check('un-calibrated good (n=5) falls back to the retained global seed (5)', pen_good == 5)
    finally:
        eu._COND_ADJ_DB = _saved
finally:
    if os.path.exists(_tmp):
        os.remove(_tmp)

# ── 9. the committed seed DB is INDICATIVE-only (n=1 is not 'reliable') ──
import sqlite3
_c = sqlite3.connect(f"file:{eu._COND_ADJ_DB}?mode=ro", uri=True)
try:
    _confs = {r[0] for r in _c.execute("SELECT DISTINCT confidence FROM condition_adjustments")}
    _srcs = {r[0] for r in _c.execute("SELECT DISTINCT source FROM condition_adjustments")}
finally:
    _c.close()
check('committed seed DB is indicative-only + source v001_seed (n=1 disclosed, never reliable)',
      _confs == {'indicative'} and _srcs == {'v001_seed'})

# ── 10. version format (version-agnostic — R6) ──
check('ENGINE_VERSION has the valid sprint format',
      re.match(r'thammen-sprint\d+p\d+p\d+', eu.ENGINE_VERSION) is not None)

print()
print(f'Sprint 2.22.0b.71 isolated: {_passed} passed, {_failed} failed')
sys.exit(0 if _failed == 0 else 1)
