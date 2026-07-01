# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.87 — EN twins for the COST/SCENARIO `assumptions` lines (evaluate_unified.py).
E14: exercises the REAL _valuation_scenarios + asserts the value_stack cost assumptions_en source.
BACKEND-ONLY / VALUE-INVARIANT — additive `*_en` keys alongside the untouched `*_ar`; EN dormant
(frontend reads via pick(it,'assumptions') / pick(_vc,'assumptions') when LANG=='en', b77).
index.html UNTOUCHED (the b37/b23 pick() reads shipped; R14 N/A by construction). AR byte-identical."""
import io
import evaluate_unified as eu

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

SRC = io.open('evaluate_unified.py', encoding='utf-8').read()

# ── (1) _valuation_scenarios — real call, all 4 scenarios carry assumptions_en ──
s = eu._valuation_scenarios(2400000, 2400000, 5400000, 1851260, 311, None, 2, 20)
check('scenarios: 4 returned', s and len(s) == 4)
by = {x['key']: x for x in s}
check('as_is: assumptions_en = adopted estimate; AR unchanged',
      by['as_is']['assumptions_en'] == 'The adopted estimate, as shown above.'
      and by['as_is']['assumptions_ar'] == 'التقدير المعتمد كما هو أعلاه.')
check('renovated_excellent: assumptions_en cost-approach + carries finish/bua; AR unchanged',
      'Cost approach: finish good' in by['renovated_excellent']['assumptions_en']
      and 'built-up area' in by['renovated_excellent']['assumptions_en']
      and by['renovated_excellent']['assumptions_ar'].startswith('منهج التكلفة: تشطيب'))
check('luxury_finish: assumptions_en cost-approach finish luxury',
      'Cost approach: finish luxury' in by['luxury_finish']['assumptions_en'])
check('teardown_land: assumptions_en land − demolition; AR unchanged',
      'Land value (' in by['teardown_land']['assumptions_en']
      and 'the building is a cost, not value.' in by['teardown_land']['assumptions_en']
      and by['teardown_land']['assumptions_ar'].startswith('قيمة الأرض ('))
check('scenarios: value-math untouched (as_is mirrors headline)',
      by['as_is']['value'] == 2400000 and by['as_is']['low'] == 2400000 and by['as_is']['high'] == 5400000)

# ── (2) value_stack cost assumptions_en (variant A, E26) — source (built inside income/cost-led branches) ──
check('value_stack cost assumptions_en (E26) authored',
      "'assumptions_en': ('Assumptions: finish {f} · retention factor {r} · '" in SRC
      and 'system (CGIS) age is the basis (E26)' in SRC)
check('value_stack cost assumptions_ar (E26) UNCHANGED',
      "'assumptions_ar': ('افتراضات: تشطيب {f} · معامل احتفاظ {r} · '" in SRC
      and 'عمر النظام (CGIS) أساس الاحتساب (E26)' in SRC)

# ── (3) frontend reads these via pick (unchanged from b23/b37) ──
HTML = io.open('index.html', encoding='utf-8').read()
check("frontend reads pick(it,'assumptions') + pick(_vc,'assumptions')",
      "pick(it,'assumptions')" in HTML and "pick(_vc,'assumptions')" in HTML)

# ── (4) engine bump ──
check('engine is a valid b-series tag',
      eu.SPRINT_TAG.startswith('2.22.0b.') and eu.ENGINE_VERSION.startswith('thammen-sprint2p22p0b'))

print('\nb87:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
