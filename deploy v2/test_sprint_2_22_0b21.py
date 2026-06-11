# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.21 — the INV-3 back-door close: `_age_neutral_rail_cost`
(micro Gate-2 SIGNED 2026-06-11; #39 measured deviation — the age-NEUTRALIZED v3
ceiling, not the literal `_cost_av`, reproduces the signed «الحصر الكامل»).

Production functions (E14). Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b21.py
"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')

from evaluate_unified import _age_neutral_rail_cost, _income_triangulation

PASS = FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  PASS {name}')
    else:
        FAIL += 1
        print(f'  FAIL {name}')

# the MEASURED fp450 breach pair (PHASE0 sweep): @40 value 2,538,795; new−dep restores the
# age-0 figure (land + external works unchanged inside 'value').
V3_40 = {'value': 2_538_795, 'building_value_new': 1_015_706,
         'building_value_depreciated': 203_141, 'land_value': 1_851_260}

print('— §1 the pure fn —')
out = _age_neutral_rail_cost(V3_40, 'user')
check('user age -> un-depreciated ceiling (value − dep + new)',
      out['value'] == 2_538_795 - 203_141 + 1_015_706)
check('input NOT mutated', V3_40['value'] == 2_538_795)
check('other keys carried', out['land_value'] == 1_851_260)
check('age_source unknown -> unchanged object', _age_neutral_rail_cost(V3_40, 'unknown') is V3_40)
check('age_source gis_imagery -> unchanged', _age_neutral_rail_cost(V3_40, 'gis_imagery') is V3_40)
check('cost None -> None', _age_neutral_rail_cost(None, 'user') is None)
check('missing new-key -> unchanged', _age_neutral_rail_cost(
    {'value': 1, 'building_value_depreciated': 1}, 'user') == {'value': 1, 'building_value_depreciated': 1})
check('missing dep-key -> unchanged', _age_neutral_rail_cost(
    {'value': 1, 'building_value_new': 1}, 'user') == {'value': 1, 'building_value_new': 1})
check('value falsy -> unchanged', _age_neutral_rail_cost(
    {'value': 0, 'building_value_new': 1, 'building_value_depreciated': 1}, 'user')['value'] == 0)
check('non-dict -> passthrough', _age_neutral_rail_cost(123, 'user') == 123)

print('— §2 the rail cure replicated through the PRODUCTION _income_triangulation —')
# the measured breach: income 2,793,404 · v3 ceil @40 = 2,538,795 → ×1.05 = 2,665,735 BLOCKS;
# the neutralized ceiling 3,351,360 → ×1.05 = 3,518,928 PASSES (the fp450 group numbers).
PRIMARY = {'value': 5_400_000, 'method': 'comparison_thin', 'high': 5_500_000}
INCOME = {'value': 2_793_404, 'rent_source': 'actual_provided',
          'cap_rate_provenance': {'source': 'calibrated', 'confidence': 'reliable'},
          'cap_rate': 0.0516, 'net_yield_pct': 5.16, 'sample_size': 46}
LAND = 1_851_260
blocked = _income_triangulation(PRIMARY, INCOME, {'value': 2_538_795}, LAND, 'standalone_villa')
check('the breach reproduced: age-40 v3 ceiling blocks income_led',
      not (blocked and blocked.get('mode') == 'income_led'))
cured_cost = _age_neutral_rail_cost(
    {'value': 2_538_795, 'building_value_new': 1_015_706,
     'building_value_depreciated': 203_141}, 'user')
cured = _income_triangulation(PRIMARY, INCOME, cured_cost, LAND, 'standalone_villa')
check('the cure: the neutralized ceiling re-admits income_led',
      cured is not None and cured.get('mode') == 'income_led'
      and cured.get('amount') == 2_793_404)
inert = _income_triangulation(PRIMARY, INCOME, None, LAND, 'standalone_villa')
check('no-fp rows untouched (ceil None stays inert -> income_led)',
      inert is not None and inert.get('mode') == 'income_led')

print('— §3 wiring + version —')
src = io.open('evaluate_unified.py', encoding='utf-8').read()
check('the rail call site passes the neutralized cost',
      '_age_neutral_rail_cost(cost, age_source)' in src)
check('exactly ONE rail call site rewired (def + 1 call = 2 occurrences)',
      src.count('_age_neutral_rail_cost(cost, age_source)') == 2)
check('#39 measured-deviation note in the fn doc',
      'الحركات المتوقعة (الحصر الكامل)' in src and '_cost_av' in src.split('def _age_neutral_rail_cost')[1][:2000])
import evaluate_unified as EU
import re as _re
check('version format (no exact pin — R6)',
      EU.ENGINE_VERSION.startswith('thammen-sprint')
      and _re.match(r'^\d+\.\d+\.\d+', EU.SPRINT_TAG) is not None)

print(f'\n{PASS} passed, {FAIL} failed')
sys.exit(1 if FAIL else 0)
