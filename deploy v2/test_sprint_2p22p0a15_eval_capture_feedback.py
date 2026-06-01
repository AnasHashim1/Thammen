#!/usr/bin/env python3
"""
Isolated logic tests — Sprint 2.22.0a.15: dormant beta instrumentation
(prediction capture + feedback).

Exercises the REAL production module `instrumentation` and the REAL
`api.FeedbackRequest` model (Rule #40 / E14). NO real Postgres — DB I/O is
verified by injecting a fake connection over instrumentation._connect, so
H1/H2/H3 + field-mapping + dormancy + failure-isolation are all checked
locally without provisioning anything.

BRIEF §5 hypotheses:
  H1  active + DB  -> exactly one prediction INSERT; result NOT mutated.
  H2  feedback     -> one record keyed on valuation_id; malformed body
                      rejected (extra='forbid'); a forced write failure does
                      NOT raise into the caller.
  H3  flag-off OR no DATABASE_URL -> zero writes, _connect never called (dormant).
Plus: refusal capture (§8.4); data-minimized field set, no IP (§3); UUID
surrogate id distinct from valuation_id (§8.3).

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a15_eval_capture_feedback.py
"""
import copy
import os
import sys

import instrumentation as I

_pass = _fail = 0
def check(name, cond, detail=''):
    global _pass, _fail
    if cond: _pass += 1; print(f'  PASS  {name}')
    else: _fail += 1; print(f'  FAIL  {name}  {detail}')


# ── fakes / fixtures ───────────────────────────────────────────────────────
class _FakeCursor:
    def __init__(self, sink): self._sink = sink
    def execute(self, sql, params=None): self._sink.append((sql, params))
    def close(self): pass

class _FakeConn:
    def __init__(self): self.executed = []
    def cursor(self): return _FakeCursor(self.executed)
    def commit(self): pass
    def close(self): pass

def _inserts(conn):
    return [(s, p) for (s, p) in conn.executed if s.strip().upper().startswith('INSERT')]

# Success-shaped engine result (mirrors .sm_56_565_21.json top-level keys).
SUCCESS = {
    'valuation_id': 'THM-20260601-073531-5656521',
    'valuation': {'amount': 2400000, 'low': 2200000, 'high': 2600000,
                  'method': 'comparison_bracket'},
    'accuracy': {'score': 85, 'tier': 'high', 'label': 'evidence-ok'},
    'material_uncertainty': {'level': 'moderate'},
}
INPUTS = {'zone': 56, 'street': 565, 'building': 21}

# Refusal-shaped result (mirrors .sm_52_903_90.json: NO valuation_id, value
# None, method insufficient_data, accuracy has NO 'tier').
REFUSAL = {
    'valuation': {'amount': None, 'low': None, 'high': None,
                  'method': 'insufficient_data'},
    'accuracy': {'score': 0, 'label': 'insufficient'},
    'material_uncertainty': {'level': 'critical'},
}
REFUSAL_INPUTS = {'zone': 52, 'street': 903, 'building': 90}


def _set_env(enabled, db):
    if enabled is None: os.environ.pop('EVAL_CAPTURE_ENABLED', None)
    else: os.environ['EVAL_CAPTURE_ENABLED'] = enabled
    if db is None: os.environ.pop('DATABASE_URL', None)
    else: os.environ['DATABASE_URL'] = db

_orig_connect = I._connect


# ── (1) pure record builder — field map + §3 minimization ──
rec = I.build_prediction_record(SUCCESS, INPUTS)
EXPECT_KEYS = {'id', 'valuation_id', 'zone', 'street', 'building', 'value',
               'range_low', 'range_high', 'method', 'tier', 'muc', 'ts'}
check('1.1 record has EXACTLY the 12 BRIEF-§3 fields (no extras)',
      set(rec.keys()) == EXPECT_KEYS, str(set(rec.keys()) ^ EXPECT_KEYS))
check('1.2 value/range/method mapped from valuation',
      (rec['value'], rec['range_low'], rec['range_high'], rec['method'])
      == (2400000, 2200000, 2600000, 'comparison_bracket'), str(rec))
check('1.3 tier<-accuracy.tier, muc<-material_uncertainty.level',
      rec['tier'] == 'high' and rec['muc'] == 'moderate', str(rec))
check('1.4 address kept as separate fields (§8.3)',
      (rec['zone'], rec['street'], rec['building']) == (56, 565, 21), str(rec))
check('1.5 UUID surrogate id present + DISTINCT from valuation_id (§8.3)',
      isinstance(rec['id'], str) and len(rec['id']) >= 32 and rec['id'] != rec['valuation_id'], str(rec))
check('1.6 NO client-IP field anywhere in the record (§3)',
      not any(k.lower() == 'ip' for k in rec.keys()), str(list(rec.keys())))

# ── (2) refusal capture (§8.4) ──
rrec = I.build_prediction_record(REFUSAL, REFUSAL_INPUTS)
check('2.1 refusal: value None + method insufficient_data',
      rrec['value'] is None and rrec['method'] == 'insufficient_data', str(rrec))
check('2.2 refusal: no valuation_id, no accuracy.tier -> None (defensive)',
      rrec['valuation_id'] is None and rrec['tier'] is None, str(rrec))
check('2.3 refusal: muc=critical, address still captured',
      rrec['muc'] == 'critical' and rrec['zone'] == 52, str(rrec))
check('2.4 refusal: still UUID id + same 12-field shape',
      set(rrec.keys()) == EXPECT_KEYS and bool(rrec['id']), str(set(rrec.keys())))

# ── (3) H3 dormancy: flag-off OR no DB -> zero writes, _connect NEVER called ──
_connect_calls = {'n': 0}
def _boom_connect():
    _connect_calls['n'] += 1
    raise AssertionError('._connect must NOT be called while dormant')
I._connect = _boom_connect
try:
    _set_env(None, None)
    check('H3.1 no flag + no DB -> is_active False', I.is_active() is False)
    check('H3.2 dormant: capture_prediction False + no _connect',
          I.capture_prediction(SUCCESS, INPUTS) is False and _connect_calls['n'] == 0)
    _set_env('true', None)
    check('H3.3 flag-on but NO DATABASE_URL -> still dormant',
          I.is_active() is False and I.capture_prediction(SUCCESS, INPUTS) is False and _connect_calls['n'] == 0)
    _set_env(None, 'postgres://fake/db')
    check('H3.4 DB set but flag-OFF -> still dormant',
          I.is_active() is False
          and I.capture_feedback({'valuation_id': 'x', 'outcome': 'y'}) is False
          and _connect_calls['n'] == 0)
finally:
    I._connect = _orig_connect
    _set_env(None, None)

# ── (H1) active + DB(fake): exactly one INSERT; result NOT mutated ──
_set_env('true', 'postgres://fake/db')
fake = _FakeConn()
I._connect = lambda: fake
try:
    before = copy.deepcopy(SUCCESS)
    wrote = I.capture_prediction(SUCCESS, INPUTS)
    ins = _inserts(fake)
    check('H1.1 active: capture_prediction returns True', wrote is True)
    check('H1.2 exactly ONE prediction INSERT issued', len(ins) == 1, str(ins))
    check('H1.3 INSERT targets the prediction table', bool(ins) and 'prediction' in ins[0][0], str(ins[:1]))
    check('H1.4 INSERT carries 12 params (the §3 field set)',
          bool(ins) and isinstance(ins[0][1], tuple) and len(ins[0][1]) == 12, str(ins[:1]))
    check('H1.5 params include the value + valuation_id',
          bool(ins) and 2400000 in ins[0][1] and 'THM-20260601-073531-5656521' in ins[0][1], str(ins[:1]))
    check('H1.6 result dict NOT mutated by capture (byte-identical)',
          SUCCESS == before, 'capture leaked into result')
finally:
    I._connect = _orig_connect
    _set_env(None, None)

# ── (H2) feedback: one record keyed on valuation_id + failure isolation ──
_set_env('true', 'postgres://fake/db')
ffake = _FakeConn()
I._connect = lambda: ffake
try:
    frec = I.build_feedback_record({'valuation_id': 'THM-x', 'outcome': 'transacted',
                                    'transacted_price': 2500000, 'note': 'sold'})
    check('H2.1 feedback record keyed on valuation_id + own UUID id',
          frec['valuation_id'] == 'THM-x' and bool(frec['id']) and frec['id'] != 'THM-x', str(frec))
    wrote = I.capture_feedback({'valuation_id': 'THM-x', 'outcome': 'transacted',
                                'transacted_price': 2500000, 'note': 'sold'})
    fins = _inserts(ffake)
    check('H2.2 active feedback: True + exactly one INSERT into feedback',
          wrote is True and len(fins) == 1 and 'feedback' in fins[0][0], str(fins))
finally:
    I._connect = _orig_connect
    _set_env(None, None)

_set_env('true', 'postgres://fake/db')
def _raise_connect(): raise RuntimeError('db down')
I._connect = _raise_connect
try:
    check('H2.3 write failure swallowed (returns False, no raise)',
          I.capture_prediction(SUCCESS, INPUTS) is False)
    check('H2.4 feedback write failure also swallowed',
          I.capture_feedback({'valuation_id': 'x', 'outcome': 'y'}) is False)
finally:
    I._connect = _orig_connect
    _set_env(None, None)

# ── (4) REAL api.FeedbackRequest — extra='forbid' (Rule #40 production class) ──
try:
    from api import FeedbackRequest
    ok = FeedbackRequest(valuation_id='THM-x', outcome='accurate')
    check('4.1 FeedbackRequest accepts a valid body',
          ok.valuation_id == 'THM-x' and ok.outcome == 'accurate')
    try:
        FeedbackRequest(valuation_id='THM-x', outcome='accurate', bogus_field=1)
        check('4.2 extra field rejected (extra=forbid)', False, 'no error raised')
    except Exception as e:
        errs = getattr(e, 'errors', lambda: [])()
        et = errs[0].get('type') if errs else ''
        check('4.2 extra field rejected with type extra_forbidden',
              et == 'extra_forbidden', str(errs)[:200])
    try:
        FeedbackRequest(outcome='accurate')  # missing required valuation_id
        check('4.3 missing required valuation_id rejected', False, 'no error raised')
    except Exception:
        check('4.3 missing required valuation_id rejected', True)
except Exception as e:
    check('4.x import + exercise api.FeedbackRequest', False, f'import failed: {e}')

print(f'\n=== Sprint 2.22.0a.15 eval-capture-feedback isolated: {_pass} passed, {_fail} failed ===')
sys.exit(1 if _fail else 0)
