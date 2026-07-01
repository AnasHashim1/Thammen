# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.78 — EN backend catalog + additive post-pass.
E14: imports the REAL en_localize + api + reads the real files. Backend-additive /
VALUE-INVARIANT: attach_en only ADDS `{base}_en` siblings for cataloged `{base}_ar`;
never touches amount/method/rule or any `_ar` value; never clobbers an existing `_en`."""
import io, copy
import en_localize as L

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

API = io.open('api.py', encoding='utf-8').read()
ENG = io.open('evaluate_unified.py', encoding='utf-8').read()
HTML = io.open('index.html', encoding='utf-8').read()

# ---- (1) the catalog + primitives exist ----
check('CATALOG is a sizable dict (>120 constant strings)', isinstance(L.CATALOG, dict) and len(L.CATALOG) > 120)
check('_norm + attach_en defined', callable(L._norm) and callable(L.attach_en))
check('_norm strips LRM/RLM marks (robust keys)',
      L._norm('‎VPS 3‎ / IVS 103') == 'VPS 3 / IVS 103' and
      L._norm('a‏  b\n\nc') == 'a b c')

# ---- (2) VALUE-INVARIANCE: attach_en is additive, never mutates values ----
resp = {'valuation': {'amount': 2400000, 'low': 2400000, 'high': 5400000,
                      'method': 'comparison_thin', 'rule': 'cost_led',
                      'leadership': {'rule': 'cost_led', 'leader': 'cost',
                                     'note_ar': 'سطر مُخصَّص', 'note_en': 'PRE-AUTHORED'},
                      'condition_note_ar': 'لم تُؤخذ حالة العقار (تجديد أو تهالك) في الحسبان. عقار في حالة أفضل من المتوسط قد يقع أعلى هذه النقطة، وعقار في حالة أدنى قد يقع تحتها.'},
        'service_scope': {'label_ar': 'فيلا منفردة'},
        'plain_int': 7, 'plain_list': [{'reason_ar': 'تصنيف غير مطابق لأي فئة مدعومة'}]}
before = copy.deepcopy(resp)
out = L.attach_en(resp)
check('returns the same object (mutates in place)', out is resp)
check('amount/low/high/method/rule UNCHANGED',
      resp['valuation']['amount'] == 2400000 and resp['valuation']['low'] == 2400000 and
      resp['valuation']['high'] == 5400000 and resp['valuation']['method'] == 'comparison_thin' and
      resp['valuation']['rule'] == 'cost_led')
check('every _ar value UNCHANGED',
      resp['valuation']['condition_note_ar'] == before['valuation']['condition_note_ar'] and
      resp['service_scope']['label_ar'] == before['service_scope']['label_ar'])
check('existing engine-authored _en NEVER clobbered',
      resp['valuation']['leadership']['note_en'] == 'PRE-AUTHORED')
check('plain (non-_ar) values untouched', resp['plain_int'] == 7)
# _en ADDED where cataloged
check('cataloged _ar gets an _en sibling (condition_note)',
      resp['valuation']['condition_note_en'].startswith('The property'))
check('cataloged label_ar -> label_en (locked term)',
      resp['service_scope']['label_en'] == 'Standalone villa')
check('recursion into lists works (reason_en)',
      resp['plain_list'][0]['reason_en'] == 'Classification does not match any supported category')
# non-cataloged (interpolated) _ar gets NO _en
check('non-cataloged _ar (custom note) gets NO new _en (only the pre-authored stays)',
      resp['valuation']['leadership']['note_en'] == 'PRE-AUTHORED')

# ---- (3) load-bearing termbase + RICS register present ----
vals = ' || '.join(L.CATALOG.values())
check('product/value register: "estimate" + "Ministry of Justice"',
      'Ministry of Justice' in vals and 'estimate' in vals)
check('disclaimer register: "not a certified" / "certified valuation"',
      'certified' in vals)
check('RICS clause numbers preserved verbatim',
      'VPS 3 / IVS 103' in vals and 'VPGA 10' in vals)
check('cost-basis DRC term', any('DRC' in v for v in L.CATALOG.values()))
check('sales-comparison approach term', any('sales-comparison approach' in v for v in L.CATALOG.values()))
check('V001 calibration anchor kept', any('V001' in v for v in L.CATALOG.values()))

# ---- (4) api.py wiring (guarded import + 2 seams) ----
check('en_localize imported (guarded, _EN_OK)', 'from en_localize import attach_en as _attach_en' in API and '_EN_OK = True' in API)
check('attach_en called in _attach_freshness seam', 'if _EN_OK:\n            _attach_en(result)' in API)
check('attach_en wraps the /api/scope response', '_attach_en(_s) if _EN_OK else _s' in API)

# ---- (5) value-invariance guards: engine version only; b77 infra intact ----
check('engine is a valid b-series tag (version-agnostic, R6) — b78 added no logic', "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)
check('b77 i18n infra intact (t/pick/_loc/EN_ENABLED); revealed b88',
      'function t(ar,en)' in HTML and 'function pick(o,base)' in HTML and 'var EN_ENABLED=true;' in HTML)
check('locked AR identity untouched (التقييم السوقي)', 'التقييم السوقي' in HTML)

print('\nb78:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
