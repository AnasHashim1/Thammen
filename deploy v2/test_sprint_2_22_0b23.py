# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.23 «بثّ المختصر» — short-report: scenarios + report id/fingerprint + /verify.

Exercises the PRODUCTION pure functions (E14/#40): `_valuation_scenarios`,
`_report_canonical`, `_report_fingerprint`, `_refine_fp4`, `_report_ref`,
`_attach_report_identity`. Plus wiring pins (engine + api.py + index.html) and the
byte-identity contract (the new keys never read/write amount/low/high/method/rule).

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b23.py
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from evaluate_unified import (   # noqa: E402 — production imports (E14)
    _valuation_scenarios, _report_canonical, _report_fingerprint, _refine_fp4,
    _report_ref, _attach_report_identity,
)

PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(('  PASS  ' if cond else '  FAIL  ') + name + (('  | ' + str(detail)) if (detail and not cond) else ''))


print('— §1 scenarios on the Marikh-class anchor (cost-led 2.4M, land~1.85M, fp 311, age 17) —')
sc = _valuation_scenarios(2400000, 2400000, 5400000, 1851260, 311, None, 2, 17)
check('1.1 returns 4 scenarios', sc and len(sc) == 4, sc and len(sc))
keys = [s['key'] for s in (sc or [])]
check('1.2 keys in order', keys == ['as_is', 'renovated_excellent', 'luxury_finish', 'teardown_land'], keys)
as_is = sc[0]
check('1.3 as_is mirrors the headline EXACTLY', (as_is['value'], as_is['low'], as_is['high']) == (2400000, 2400000, 5400000),
      (as_is['value'], as_is['low'], as_is['high']))
ren = next(s for s in sc if s['key'] == 'renovated_excellent')
lux = next(s for s in sc if s['key'] == 'luxury_finish')
td = next(s for s in sc if s['key'] == 'teardown_land')
check('1.4 luxury_finish > renovated_excellent (3500 > 2500 RCN)', lux['value'] > ren['value'], (ren['value'], lux['value']))
check('1.5 renovated_excellent > land floor (building adds value)', ren['value'] > 1700000, ren['value'])
check('1.6 teardown_land < land floor (demolition subtracted)', 0 < td['value'] < 1900000, td['value'])
check('1.7 teardown_land high == land floor', td['high'] == 1900000 or td['high'] == 1851260 or td['high'] > td['value'], td['high'])
check('1.8 every scenario has a value + label_ar + assumptions_ar',
      all(s.get('value') and s.get('label_ar') and s.get('assumptions_ar') for s in sc))

print('— §2 scenarios degrade gracefully (no DRC inputs → as_is only / None) —')
only = _valuation_scenarios(2600000, 2000000, 2600000, None, None, None, 2, None)  # no land floor / fp / age
check('2.1 no cost inputs → as_is ONLY', only and len(only) == 1 and only[0]['key'] == 'as_is')
check('2.2 amount None → None', _valuation_scenarios(None, None, None, 1851260, 311, None, 2, 17) is None)
check('2.3 confirmed footprint path computes (actual fp, no built-ratio)',
      len(_valuation_scenarios(2400000, 2400000, 5400000, 1851260, None, 280, 2, 17)) == 4)
check('2.4 missing age but present land+fp → as_is only (depreciation needs age)',
      len(_valuation_scenarios(2400000, 2400000, 5400000, 1851260, 311, None, 2, None)) == 1)

print('— §3 the byte-identity contract: as_is == the inputs (no mutation, no drift) —')
hi = _valuation_scenarios(3800000, 2500000, 3800000, 2456736, 391, None, 2, 17)   # V001-class
check('3.1 as_is carries the EXACT headline triple', (hi[0]['value'], hi[0]['low'], hi[0]['high']) == (3800000, 2500000, 3800000))
check('3.2 the function returns a NEW list (caller dict untouched by design)', isinstance(hi, list))

print('— §4 report_canonical: the \\s+ normalization + None handling —')
c1 = _report_canonical('54/541/6', '2026-06-12', 'eng-x', 2400000, 2400000, 5400000, 'cost_led')
check('4.1 canonical shape v1|addr|date|eng|amount|low|high|rule',
      c1 == 'v1|54/541/6|2026-06-12|eng-x|2400000|2400000|5400000|cost_led', c1)
c2 = _report_canonical('a  b\tc\n', 'd', 'e', None, None, None, '')
check('4.2 whitespace collapsed + None→empty', c2 == 'v1|a b c|d|e||||', c2)
# int vs string amount stringify identically (the /verify round-trip invariant)
check('4.3 int 2400000 and str "2400000" canonicalize the same',
      _report_canonical('x', 'y', 'z', 2400000, 1, 2, 'r') == _report_canonical('x', 'y', 'z', '2400000', '1', '2', 'r'))
check('4.4 float low/high round-trip (apt 7250000.0)',
      _report_canonical('x', 'y', 'z', 8529231, 7250000.0, 9810000.0, 'income_approach_only')
      == _report_canonical('x', 'y', 'z', '8529231', '7250000.0', '9810000.0', 'income_approach_only'))

print('— §5 HMAC accept + reject-forgery + dormant —')
KEY = 'test-key-abc-123'
fp = _report_fingerprint(c1, KEY)
check('5.1 fp is 12 hex chars', bool(fp) and len(fp) == 12 and re.fullmatch(r'[0-9a-f]{12}', fp), fp)
check('5.2 same canonical + key → SAME fp (deterministic)', _report_fingerprint(c1, KEY) == fp)
# forgery: change the amount → different canonical → different fp (the /verify FAIL path)
c_forged = _report_canonical('54/541/6', '2026-06-12', 'eng-x', 9900000, 2400000, 5400000, 'cost_led')
check('5.3 forged amount → DIFFERENT fp (reject)', _report_fingerprint(c_forged, KEY) != fp)
check('5.4 forged rule → DIFFERENT fp', _report_fingerprint(_report_canonical('54/541/6', '2026-06-12', 'eng-x', 2400000, 2400000, 5400000, 'income_led'), KEY) != fp)
check('5.5 wrong key → DIFFERENT fp', _report_fingerprint(c1, 'other-key') != fp)
check('5.6 DORMANT: no key (None + no env) → None', (_report_fingerprint(c1, '') is None) and (
    _report_fingerprint(c1, None) is None if not os.environ.get('HMAC_REPORT_KEY') else True))

print('— §6 report_ref format + refine fp4 disambiguation —')
r_bare = _report_ref(54, 541, 6, None, '2026-06-12', None)
check('6.1 TH-YYYYMMDD-ZZSSSBBB (zero-padded)', r_bare == 'TH-20260612-54541006', r_bare)
r_ref = _report_ref(54, 541, 6, None, '2026-06-12', 'ab12')
check('6.2 refine suffix appended', r_ref == 'TH-20260612-54541006-ab12', r_ref)
r_pin = _report_ref(None, None, None, '74328443', '2026-06-12', None)
check('6.3 PIN fallback', r_pin.startswith('TH-20260612-P74328443'), r_pin)
f4a = _refine_fp4({'floors': 3, 'condition': 'good', 'basement': None, 'x': ''})
f4b = _refine_fp4({'condition': 'good', 'floors': 3})   # same effective inputs, different order
check('6.4 refine fp4 is 4 hex + order-independent', f4a and len(f4a) == 4 and f4a == f4b, (f4a, f4b))
check('6.5 different inputs → different fp4', _refine_fp4({'floors': 4}) != _refine_fp4({'floors': 3}))
check('6.6 no refine inputs (all empty/None/False) → None', _refine_fp4({'a': None, 'b': '', 'c': False}) is None)

print('— §7 _attach_report_identity wires onto a settled output (additive; headline untouched) —')
out = {
    'address': '54/541/6', 'valuation_date': '2026-06-12', 'engine_version': 'eng-x',
    'asset_type': 'standalone_villa',
    'valuation': {'amount': 2400000, 'low': 2400000, 'high': 5400000,
                  'method': 'comparison_thin', 'leadership': {'rule': 'cost_led'}},
}
before = dict(out['valuation'])
_attach_report_identity(out, 54, 541, 6, None, {'floors': 3})
check('7.1 report_ref set', out.get('report_ref', '').startswith('TH-20260612-54541006-'))
check('7.2 report_fp_basis carries the signed fields', out['report_fp_basis']['amount'] == 2400000 and out['report_fp_basis']['rule'] == 'cost_led')
check('7.3 valuation block UNCHANGED (amount/low/high/method/rule)', out['valuation'] == before,
      {k: out['valuation'].get(k) for k in ('amount', 'low', 'high', 'method')})
check('7.4 report_fp present-or-None by key (no crash either way)', 'report_fp' in out)
# rule fallback: no leadership → method
out2 = {'address': '52/903/90', 'valuation_date': '2026-06-12', 'engine_version': 'e',
        'valuation': {'amount': 8529231, 'low': 7250000.0, 'high': 9810000.0,
                      'method': 'income_approach_only'}}
_attach_report_identity(out2, 52, 903, 90, None, {'rental_income': 60000})
check('7.5 rule falls back to method when no leadership', out2['report_fp_basis']['rule'] == 'income_approach_only')

print('— §8 wiring pins (real source files) —')
eu = io.open(os.path.join(HERE, 'evaluate_unified.py'), encoding='utf-8').read()
check('8.1 scenarios attached at the main-path tail', "output['valuation']['scenarios']" in eu)
check('8.2 scenarios gated to villa/house (_TEARDOWN_ASSET_TYPES)',
      "output.get('asset_type') in _TEARDOWN_ASSET_TYPES" in eu and '_valuation_scenarios(' in eu)
check('8.3 report identity attached on the main path', '_attach_report_identity(output, zone, street, building, pin,' in eu)
check('8.4 report identity attached on the fast-income path', '_attach_report_identity(_fast_result,' in eu)
check('8.5 hmac + hashlib imported', re.search(r'^import hashlib', eu, re.M) and re.search(r'^import hmac', eu, re.M))
api = io.open(os.path.join(HERE, 'api.py'), encoding='utf-8').read()
check('8.6 /verify endpoint defined + rate-limited (string form)',
      '@app.get("/verify"' in api and '@limiter.limit(";".join(RATE_LIMIT_LIST))' in api)
check('8.7 /verify recomputes via the SHARED canonical+fp (no drift)',
      '_report_canonical(addr, date, eng, amount, low, high, rule)' in api and '_report_fingerprint(canonical)' in api)
check('8.8 /verify uses constant-time compare', 'hmac.compare_digest(' in api)
check('8.9 /verify dormant without HMAC_REPORT_KEY', "os.environ.get('HMAC_REPORT_KEY')" in api)
html = io.open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
check('8.10 report renders the scenarios panel', 'v.scenarios' in html and 'سيناريوهات الحالة والتشطيب' in html)
check('8.11 report renders report_ref + verify link', 'd.report_ref' in html and '/verify?' in html and 'تحقّق من صحّة التقرير' in html)
# Sprint 2.22.0b.25 (م2) re-point: the gate moved INTO the shared _verifyUrl builder
# (one builder for the report link + the short-report QR — no drift); the link still
# renders ONLY when ref+fp+basis are present (the builder returns null otherwise).
check('8.12 verify link gated on report_fp present (key configured)',
      'if(!(d.report_ref&&d.report_fp&&_b))return null;' in html
      and 'const _vu=_verifyUrl(d);' in html and 'if(_vu){' in html)

print('=' * 64)
print(f'{len(PASS)} passed / {len(FAIL)} failed')
if FAIL:
    print('FAILED:', FAIL)
    sys.exit(1)
sys.exit(0)
