#!/usr/bin/env python3
"""
Isolated tests — Sprint 2.22.0a.16: pre-activation privacy hardening of the
a15 capture (supersedes test_sprint_2p22p0a15_eval_capture_feedback.py — the
a15 schema it pinned no longer exists).

Exercises the REAL `instrumentation` module + the REAL `api.FeedbackRequest`
(Rule #40 / E14). NO real Postgres — DB I/O verified via a fake connection
injected over instrumentation._connect; encryption round-trip is conditional
on the `cryptography` package (the no-key guarantee is always tested).

Covers the signed design:
  Q1  UUID `id` = sole key; NO valuation_id stored anywhere; capture_prediction
      RETURNS the UUID (active) / None (dormant); feedback FK'd via prediction_id.
  Q2  zone PLAINTEXT; street/building ENCRYPTED + gated on CAPTURE_ENC_KEY
      (None — never plaintext — without a key).
  Q3  created_at + 180d expires_at; aggregate_and_purge_expired collapses to
      prediction_zone_agg + drops the per-record rows; erase_prediction row-level.
  Q4  free-text `note` removed (schema + api.FeedbackRequest -> 422).
  H3  dormancy: flag-off / no-DB / DB-but-flag-off -> zero writes, _connect never called.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a16_precapture_hardening.py
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
    def __init__(self, sink): self._sink = sink; self.rowcount = 1
    def execute(self, sql, params=None): self._sink.append((sql, params))
    def close(self): pass

class _FakeConn:
    def __init__(self): self.executed = []
    def cursor(self): return _FakeCursor(self.executed)
    def commit(self): pass
    def close(self): pass

def _sql(conn, verb, table):
    return [(s, p) for (s, p) in conn.executed
            if verb in s.upper() and table in s]

SUCCESS = {
    'valuation_id': 'THM-20260601-073531-5656521',   # display-only; MUST NOT be stored
    'valuation': {'amount': 2400000, 'low': 2200000, 'high': 2600000, 'method': 'comparison_bracket'},
    'accuracy': {'score': 85, 'tier': 'high'},
    'material_uncertainty': {'level': 'moderate'},
}
INPUTS = {'zone': 56, 'street': 565, 'building': 21}
REFUSAL = {
    'valuation': {'amount': None, 'low': None, 'high': None, 'method': 'insufficient_data'},
    'accuracy': {'score': 0}, 'material_uncertainty': {'level': 'critical'},
}

def _set_env(enabled, db, key=None):
    for k, v in (('EVAL_CAPTURE_ENABLED', enabled), ('DATABASE_URL', db), ('CAPTURE_ENC_KEY', key)):
        if v is None: os.environ.pop(k, None)
        else: os.environ[k] = v

_orig_connect = I._connect


# ── (Q1/Q4) prediction record: UUID-only, NO valuation_id, NO note, NO IP ──
rec = I.build_prediction_record(SUCCESS, INPUTS)
EXPECT = {'id', 'zone', 'street_enc', 'building_enc', 'value', 'range_low',
          'range_high', 'method', 'tier', 'muc', 'created_at', 'expires_at'}
check('Q1.1 prediction record keys == hardened set (no valuation_id / no note / no IP)',
      set(rec.keys()) == EXPECT, str(set(rec.keys()) ^ EXPECT))
check('Q1.2 NO valuation_id, NO plaintext street/building anywhere in the record',
      'valuation_id' not in rec and 'street' not in rec and 'building' not in rec, str(list(rec.keys())))
check('Q1.3 id is a UUID (sole key) + value/method mapped',
      isinstance(rec['id'], str) and len(rec['id']) >= 32
      and rec['value'] == 2400000 and rec['method'] == 'comparison_bracket', str(rec)[:160])
check('Q1.4 no client-IP field', not any(k.lower() == 'ip' for k in rec.keys()))

# ── (Q2) zone plaintext; street/building encrypted + gated on key ──
check('Q2.1 zone PLAINTEXT (== input)', rec['zone'] == 56)
check('Q2.2 NO key -> street/building NOT stored in plaintext (None)',
      rec['street_enc'] is None and rec['building_enc'] is None, str(rec))
try:
    from cryptography.fernet import Fernet
    k = Fernet.generate_key().decode()
    _set_env(None, None, k)
    rk = I.build_prediction_record(SUCCESS, INPUTS)
    dec = Fernet(k.encode()).decrypt(rk['street_enc'].encode()).decode()
    check('Q2.3 WITH key -> street encrypted (ciphertext != plaintext, decrypts back)',
          rk['street_enc'] not in (None, '565') and dec == '565', str(rk['street_enc'])[:40])
    _set_env(None, None, None)
except ImportError:
    check('Q2.3 (skipped — cryptography not installed locally; no-key guarantee holds)', True)

# ── (Q3) retention fields present ──
check('Q3.1 created_at + expires_at present',
      bool(rec['created_at']) and bool(rec['expires_at']) and rec['expires_at'] > rec['created_at'], str(rec)[:120])

# ── (§8.4) refusal maps cleanly ──
rr = I.build_prediction_record(REFUSAL, {'zone': 52, 'street': 903, 'building': 90})
check('R.1 refusal: value None + method insufficient_data + tier None',
      rr['value'] is None and rr['method'] == 'insufficient_data' and rr['tier'] is None, str(rr)[:120])

# ── (Q1/Q4) feedback record: prediction_id FK, NO valuation_id, NO note ──
fr = I.build_feedback_record({'prediction_id': 'uuid-x', 'outcome': 'transacted', 'transacted_price': 2500000})
check('Q4.1 feedback keys == {id, prediction_id, outcome, transacted_price, created_at} (no note / no valuation_id)',
      set(fr.keys()) == {'id', 'prediction_id', 'outcome', 'transacted_price', 'created_at'}, str(set(fr.keys())))
check('Q1.5 feedback FK = prediction_id (the UUID), own id distinct',
      fr['prediction_id'] == 'uuid-x' and fr['id'] != 'uuid-x', str(fr)[:120])

# ── (H3) dormancy: zero writes, _connect NEVER called ──
_calls = {'n': 0}
def _boom():
    _calls['n'] += 1; raise AssertionError('_connect must NOT be called while dormant')
I._connect = _boom
try:
    _set_env(None, None);    check('H3.1 no flag+no DB -> not active', I.is_active() is False)
    check('H3.2 dormant capture_prediction -> None, no _connect',
          I.capture_prediction(SUCCESS, INPUTS) is None and _calls['n'] == 0)
    _set_env('true', None);  check('H3.3 flag-on, no DB -> dormant',
          I.is_active() is False and I.capture_prediction(SUCCESS, INPUTS) is None and _calls['n'] == 0)
    _set_env(None, 'postgres://fake');  check('H3.4 DB set, flag-off -> dormant',
          I.is_active() is False and I.capture_feedback({'prediction_id': 'x'}) is False
          and I.aggregate_and_purge_expired() == 0 and I.erase_prediction('x') is False and _calls['n'] == 0)
finally:
    I._connect = _orig_connect; _set_env(None, None)

# ── (Q1) active capture_prediction -> RETURNS UUID + one INSERT; no mutation ──
_set_env('true', 'postgres://fake')
fk = _FakeConn(); I._connect = lambda: fk
try:
    before = copy.deepcopy(SUCCESS)
    cid = I.capture_prediction(SUCCESS, INPUTS)
    ins = _sql(fk, 'INSERT', 'prediction')
    check('Q1.6 active capture_prediction RETURNS a UUID id', isinstance(cid, str) and len(cid) >= 32)
    check('Q1.7 exactly one INSERT INTO prediction (12 hardened cols, no valuation_id col)',
          len(ins) == 1 and 'street_enc' in ins[0][0] and 'valuation_id' not in ins[0][0], str(ins[:1])[:200])
    check('Q1.8 capture_prediction does NOT mutate result', SUCCESS == before)
finally:
    I._connect = _orig_connect; _set_env(None, None)

# ── (Q3) aggregate_and_purge: agg INSERT + per-record DELETE; erase: row DELETE ──
_set_env('true', 'postgres://fake')
fk2 = _FakeConn(); I._connect = lambda: fk2
try:
    purged = I.aggregate_and_purge_expired(period='2026-06')
    agg = _sql(fk2, 'INSERT', 'prediction_zone_agg')
    dele = _sql(fk2, 'DELETE', 'prediction')
    check('Q3.2 purge: collapses to prediction_zone_agg (zone-level INSERT)', len(agg) == 1, str(agg[:1])[:160])
    check('Q3.3 purge: DROPS per-record rows (DELETE FROM prediction WHERE expires_at)',
          any('expires_at' in s for s, _ in dele), str(dele)[:160])
    check('Q3.4 purge returns the rowcount', purged == 1)
    fk3 = _FakeConn(); I._connect = lambda: fk3
    ok = I.erase_prediction('uuid-victim')
    er = _sql(fk3, 'DELETE', 'prediction')
    check('Q3.5 erase_prediction: row-level DELETE by id (+ cascade), returns True',
          ok is True and any('id' in s for s, _ in er) and er[0][1] == ('uuid-victim',), str(er[:1])[:160])
finally:
    I._connect = _orig_connect; _set_env(None, None)

# ── (Q4) REAL api.FeedbackRequest: prediction_id required; note + valuation_id rejected ──
try:
    from api import FeedbackRequest
    ok = FeedbackRequest(prediction_id='uuid-x', outcome='accurate')
    check('Q4.2 FeedbackRequest accepts {prediction_id, outcome}', ok.prediction_id == 'uuid-x')
    for badfield, label in (({'prediction_id': 'x', 'outcome': 'y', 'note': 'hi'}, 'note'),
                            ({'prediction_id': 'x', 'outcome': 'y', 'valuation_id': 'z'}, 'valuation_id')):
        try:
            FeedbackRequest(**badfield); check(f'Q4.3 `{label}` rejected', False, 'no error')
        except Exception as e:
            t = (getattr(e, 'errors', lambda: [{}])()[0] or {}).get('type', '')
            check(f'Q4.3 `{label}` rejected (extra_forbidden)', t == 'extra_forbidden', str(t))
    try:
        FeedbackRequest(outcome='accurate'); check('Q4.4 prediction_id required', False, 'no error')
    except Exception:
        check('Q4.4 prediction_id required', True)
except Exception as e:
    check('Q4.x import api.FeedbackRequest', False, f'import failed: {e}')

print(f'\n=== Sprint 2.22.0a.16 precapture-privacy-hardening isolated: {_pass} passed, {_fail} failed ===')
sys.exit(1 if _fail else 0)
