# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.20 — EVIDENCE-CONDITIONAL LEADERSHIP (Gate-2 SIGNED 2026-06-11).

Isolated matrix for the leadership gate + helpers (PRODUCTION functions — Rule #40/E14):
RULE 1 (matched) · RULE 2 (geo-full reliable bar) · else cost-led F3(b) · the E25 rail
(المعراض inversion) + the double-weak clause · F2=B re-survey · cost-unavailable fail-open ·
the §4-a INVARIANT · verbatim signed copy · the geo-full dispersion extension on the real
CSV · wiring pins (the retired branches + the new emission + index.html renderers).

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b20.py
"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')

import evaluate_unified as EU
from evaluate_unified import (
    _e26_subject_band, _matched_stratum_n, _bracket_disp36, _muc_one_notch,
    _leadership_gate, LEAD_MATCHED_MIN_N, LEAD_GEO_FULL_MIN_N, LEAD_DISPERSION_T,
    COST_STACK_LABEL_AR, COST_STACK_SUB_AR, LEAD_RESURVEY_NOTE_AR,
    LEAD_COST_AGE_HONESTY_AR, LEAD_COST_NOTE_AR, LEAD_E25_NOTE_AR,
)

PASS = FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  PASS {name}')
    else:
        FAIL += 1
        print(f'  FAIL {name}')

GF_OK = {'n_full': 22, 'dispersion_full': 0.203}      # V001-shaped (passes RULE 2)
GF_BAD = {'n_full': 51, 'dispersion_full': 0.620}     # امريخ-shaped (fails RULE 2)
COST = {'value': 2_378_094}
LAND = 1_851_260

print('— §1 _e26_subject_band (E26 band + F2=B untestable) —')
check('vintage 17 -> old', _e26_subject_band(17, 'vintage_capped') == 'old')
check('vintage 0 -> None (re-survey)', _e26_subject_band(0, 'vintage_capped') is None)
check('vintage 1 -> None', _e26_subject_band(1, 'vintage_capped') is None)
check('survey 15 -> old', _e26_subject_band(15, 'survey') == 'old')
check('survey 6 -> modern', _e26_subject_band(6, 'survey') == 'modern')
check('survey 1 -> new', _e26_subject_band(1, 'survey') == 'new')
check('age None -> None', _e26_subject_band(None, 'survey') is None)

print('— §2 _matched_stratum_n —')
STRATA = {'land_priced': {'n': 1}, 'aging_stock': {'n': 2},
          'modern_stock': {'n': 5}, 'luxury_new': {'n': 15}}
check('old sums land+aging', _matched_stratum_n(STRATA, 'old') == 3)
check('modern', _matched_stratum_n(STRATA, 'modern') == 5)
check('new', _matched_stratum_n(STRATA, 'new') == 15)
check('band None -> None', _matched_stratum_n(STRATA, None) is None)
check('strata None -> None', _matched_stratum_n(None, 'old') is None)

print('— §3 _bracket_disp36 —')
MOJ = {'categories': {'villa': {'size_brackets': {
    '400-600': {'ppm2_dispersion_36': 0.208, 'n_36': 37},
    '600-900': {'ppm2_dispersion_36': 0.165, 'n_36': 15}}}}}
check('picks 400-600', _bracket_disp36(MOJ, 450) == (0.208, 37))
check('picks 600-900', _bracket_disp36(MOJ, 613) == (0.165, 15))
check('out of cells -> (None,None)', _bracket_disp36(MOJ, 2000) == (None, None))
check('plot None -> (None,None)', _bracket_disp36(MOJ, None) == (None, None))
check('moj None -> (None,None)', _bracket_disp36(None, 450) == (None, None))

print('— §4 _muc_one_notch —')
check('low->moderate', _muc_one_notch('low') == 'moderate')
check('moderate->high', _muc_one_notch('moderate') == 'high')
check('high->critical', _muc_one_notch('high') == 'critical')
check('critical stays', _muc_one_notch('critical') == 'critical')
check('None->high (moderate+1)', _muc_one_notch(None) == 'high')

print('— §5 RULE 1 (matched-stratum pool) —')
g = _leadership_gate(2_400_000, 'standalone_villa', 22, 0.208, True, 'old', False, GF_BAD, COST, LAND)
check('matched -> market', g['leader'] == 'market' and g['rule'] == 'matched')
g = _leadership_gate(2_400_000, 'standalone_villa', 9, 0.208, True, 'old', False, None, COST, LAND)
check('n=9 fails RULE1 -> cost', g['rule'] == 'cost_led')
g = _leadership_gate(2_400_000, 'standalone_villa', 22, 0.30, True, 'old', False, None, COST, LAND)
check('disp==0.30 fails (strict <)', g['rule'] == 'cost_led')
g = _leadership_gate(2_400_000, 'standalone_villa', 22, 0.208, False, 'old', False, None, COST, LAND)
check('mismatch fails RULE1', g['rule'] == 'cost_led')
g = _leadership_gate(2_400_000, 'standalone_villa', 22, 0.208, None, None, True, None, COST, LAND)
check('untestable band (F2=B) fails RULE1', g['rule'] == 'cost_led' and g['resurvey'] is True)

print('— §6 RULE 2 (geo-full reliable bar) —')
g = _leadership_gate(3_800_000, 'standalone_villa', 1, 0.44, False, 'old', False, GF_OK,
                     {'value': 3_119_090}, 2_456_736)
check('geo-full rescue -> market', g['leader'] == 'market' and g['rule'] == 'geo_full')
check('geo-full carries muc_notch + cost_floor',
      g.get('muc_notch') is True and g.get('cost_floor') == 3_119_090)
g = _leadership_gate(3_400_000, 'standalone_villa', 3, 0.165, False, 'old', False, GF_BAD, COST, LAND)
check('امريخ: geo disp 0.620 FAILS -> cost leads', g['leader'] == 'cost' and g['rule'] == 'cost_led')
g = _leadership_gate(2_500_000, 'standalone_villa', None, None, None, None, True,
                     {'n_full': 54, 'dispersion_full': 0.212}, {'value': 2_263_592}, 1_700_100)
check('V002-shaped: re-survey -> RULE2 rescue', g['rule'] == 'geo_full' and g['resurvey'] is True)
g = _leadership_gate(2_400_000, 'standalone_villa', 3, 0.4, False, 'old', False,
                     {'n_full': 19, 'dispersion_full': 0.1}, COST, LAND)
check('geo n=19 < 20 fails RULE2', g['rule'] == 'cost_led')

print('— §7 cost-led F3(b) shape —')
g = _leadership_gate(3_400_000, 'standalone_villa', 3, 0.165, False, 'old', False, GF_BAD, COST, LAND)
check('low = max(land, cost) = cost', g['low'] == 2_378_094)
check('high = the muted market median', g['high'] == 3_400_000)
check('muc_min_high', g.get('muc_min_high') is True)

print('— §8 the E25 RAIL (المعراض inversion) + double-weak —')
g = _leadership_gate(2_600_000, 'standalone_villa', 7, 0.492, True, 'old', False,
                     {'n_full': 22, 'dispersion_full': 0.409}, {'value': 3_741_570}, 2_674_350)
check('cost>=market -> market keeps the lead', g['leader'] == 'market' and g['rule'] == 'e25_capped')
check('double-weak: divergence + MUC>=high',
      g.get('divergence') is True and g.get('muc_min_high') is True)
g = _leadership_gate(2_600_000, 'standalone_villa', 7, 0.492, True, 'old', False, None,
                     {'value': 2_600_000}, 2_674_350)
check('cost==market boundary -> e25_capped (>=)', g['rule'] == 'e25_capped')

print('— §9 cost unavailable + scope guards —')
g = _leadership_gate(2_700_000, 'standalone_villa', 0, None, None, None, False, None, None, None)
check('no cost -> market keeps lead + cost_unavailable', g['rule'] == 'cost_unavailable'
      and g['leader'] == 'market' and g.get('muc_min_high') is True)
check('non-villa -> None', _leadership_gate(1_000_000, 'apartment_building', 22, 0.1, True,
                                            'old', False, None, COST, LAND) is None)
check('raw_land -> None', _leadership_gate(1_200_000, 'raw_land', None, None, None, None,
                                           False, None, None, None) is None)
check('amount None -> None', _leadership_gate(None, 'standalone_villa', 22, 0.1, True,
                                              'old', False, None, COST, LAND) is None)

print('— §10 the §4-a INVARIANT (headline between the two figures) —')
ok = True
import itertools
for amt, cv, mn, dp, sm in itertools.product(
        (1_500_000, 2_600_000, 4_000_000), (900_000, 2_378_094, 3_741_570),
        (0, 9, 22), (0.05, 0.35, None), (True, False, None)):
    g = _leadership_gate(amt, 'standalone_villa', mn, dp, sm, 'old', False, None,
                         {'value': cv}, 800_000)
    if g is None:
        ok = False
        break
    head = g['cost_value'] if g['leader'] == 'cost' else amt
    lo, hi = min(cv, amt), max(cv, amt)
    if head is None or not (lo <= head <= hi):
        ok = False
        print('   INVARIANT BREACH:', amt, cv, mn, dp, sm, g['rule'])
        break
check('invariant holds across the 135-point grid', ok)

print('— §11 verbatim signed copy (SESSION_CLOSE §7 / BRIEF §3-§4) —')
check('cost label b19 verbatim', COST_STACK_LABEL_AR == 'قيمة التكلفة (أرض + بناء مُهلَك) — نهج DRC')
check('cost sub V001 verbatim', COST_STACK_SUB_AR == 'استرشادي، مُعايَر على تقييم معتمد واحد (V001)')
check('resurvey F2=B verbatim', LEAD_RESURVEY_NOTE_AR == 'عمر مُعاد تسجيله — غير موثوق')
check('age-honesty verbatim core', 'تقدير الإهلاك يزداد ذاتيةً مع التقادم' in LEAD_COST_AGE_HONESTY_AR
      and 'معايرتنا على شيت مثمّن وأرضية السوق تخففه' in LEAD_COST_AGE_HONESTY_AR)
# b72 (R6/Lesson-2 re-point): the notes were de-jargoned (value-clarity) — the METHODOLOGY is intact
# (the cost-led note still carries n + dispersion + the no-invented-central line; the E25 note still
# states cost is a FLOOR not a ceiling = the anti-inflation rail), only the wording is plainer.
check('cost-led note carries n + dispersion placeholders + the no-invented-central line',
      '{n}' in LEAD_COST_NOTE_AR and '{d}' in LEAD_COST_NOTE_AR and 'لا رقم مركزيّ مُخترَع' in LEAD_COST_NOTE_AR)
check('E25 note states cost is a FLOOR not a ceiling (the anti-inflation rail, plain wording)',
      'أرضيةٌ لا سقفٌ' in LEAD_E25_NOTE_AR and '{cost}' in LEAD_E25_NOTE_AR and '{comp}' in LEAD_E25_NOTE_AR)
_b20_consts = ''.join(v for k, v in vars(EU).items()
                      if k.startswith(('LEAD_', 'COST_STACK')) and isinstance(v, str))
check('terminology: «معامل الإحلال» reserved (absent from b20 copy)', 'معامل الإحلال' not in _b20_consts)
check('terminology: «حوض» not «مجمع» in b20 copy', 'مجمع' not in _b20_consts)

print('— §12 geo-full dispersion extension (REAL CSV, production fns — E14) —')
try:
    import csv as _csv
    import moj_reference as MR
    from evaluate_property import resolve_moj_area_name
    with io.open('moj_weekly.csv', encoding='utf-8-sig') as f:
        ROWS = list(_csv.DictReader(f))
    rr = resolve_moj_area_name(ROWS, 'امريخ الجنوبي')
    g1 = MR.subject_geo_full_ppm2(ROWS, rr[0] if rr else 'مريخ', 613)
    check('امريخ geo-full n=51', g1 and g1['n_full'] == 51)
    check('امريخ geo-full median 5567 (existing key byte-stable)', g1 and g1['ppm2_median_full'] == 5567)
    check('امريخ geo-full dispersion 0.62', g1 and abs(g1['dispersion_full'] - 0.62) < 0.005)
    g2 = MR.subject_geo_full_ppm2(ROWS, 'المعمورة', 652)
    check('V001 geo-full n=22 disp 0.203', g2 and g2['n_full'] == 22
          and abs(g2['dispersion_full'] - 0.203) < 0.005)
except Exception as e:
    check(f'real-CSV geo-full extension ({e})', False)

print('— §13 wiring pins (the retired branches + the new emission) —')
src = io.open('evaluate_unified.py', encoding='utf-8').read()
check('b11 branch-decider call retired', '_ct = _cost_triangulation(' not in src)
check('b16 branch call retired', '_osr = _old_stock_reanchor(' not in src)
check('the widen_down branch retired', "elif _tri and _tri['mode'] == 'widen_down'" not in src)
check('income_led precedence intact', "if _tri and _tri['mode'] == 'income_led':" in src)
check('the gate is called', '_gate = _leadership_gate(' in src)
check('leadership emitted', "output['valuation']['leadership'] = _lead20" in src)
check('value_stack emitted', "output['valuation']['value_stack'] = {" in src)
check('age-sensitivity (b13/b18) intact', "output['valuation']['age_sensitivity'] = {" in src)
check('pure calculators KEPT (superseded)', 'def _cost_triangulation(' in src
      and 'def _old_stock_reanchor(' in src and 'def _income_triangulation(' in src)
check('land DRC one-liner emitted', "cost_note_ar" in src and 'لا مكوّن بناء لقطعة فضاء' in src)
html = io.open('index.html', encoding='utf-8').read()
check('TIER-1 + report render leadership.note_ar (x2)', html.count('v.leadership.note_ar') >= 2)
check('cost stack line rendered (x2)', html.count('v.value_stack.cost.value') >= 2)
check('dispersion rendered (G2 visible)', html.count('v.value_stack.market.dispersion_36') >= 2)
# R6/Lesson-2: NO exact version pins — b19 (the report slice) legitimately bumps after b20.
import re as _re
check('ENGINE_VERSION/SPRINT_TAG format (version-agnostic)',
      EU.ENGINE_VERSION.startswith('thammen-sprint')
      and _re.match(r'^\d+\.\d+\.\d+', EU.SPRINT_TAG) is not None)

print(f'\n{PASS} passed, {FAIL} failed')
sys.exit(1 if FAIL else 0)
