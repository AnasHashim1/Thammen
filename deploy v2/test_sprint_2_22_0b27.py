# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.27 — م4 «هوية الشاشات الأولى» (the first-screens thm-report identity).

Isolated checks against the REAL index.html (Rule #40 / E14):
  1. The thmr identity applied to the five journey screens (home/gate/form/confirm/refine).
  2. The refine screen regrouped into the THREE v3-contract groups, each TAGGED by its
     real effect (يحرّك التقدير / يدقّق مرتكز التكلفة / اختياري للإثراء); group ١ open
     by default; EVERY field id unchanged; towerRentSection UNGROUPED (the 2.16.10/b22
     tower flow preserved); the focus helper opens a closed <details> ancestor.
  3. The setbacks equation (E15: أمامي 5 · جانبي 3 · خلفي 3 · سقف 60%) under the
     building area — the refine hint + the confirm basis row (setback-envelope only).

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b27.py
"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  PASS  {name}')
    else:
        FAIL += 1
        print(f'  FAIL  {name}  {detail}')


with open('index.html', encoding='utf-8') as f:
    HTML = f.read()
_m = re.search(r'<div class="screen thmr" id="refineScreen">.*?</div>\s*<!-- CONFIRM', HTML, re.S)
REF = _m.group(0) if _m else ''

print('\n[1] the thmr identity on the five journey screens')
for tag in ('class="home screen active thmr" id="homeScreen"',
            'class="bgate thmr" id="betaGate"',
            'class="screen thmr" id="formScreen"',
            'class="screen thmr" id="confirmScreen"',
            'class="screen thmr" id="refineScreen"'):
    check(f'thmr on {tag.split("id=")[1]}', tag in HTML)
check('the results screen NOT re-skinned (out of the signed 1-5 scope)',
      'class="screen thmr" id="resultsScreen"' not in HTML)

print('\n[2] the three tagged groups (the v3 contract)')
check('refine block extracted', len(REF) > 500)
check('exactly THREE thmr-grp groups', REF.count('<details class="thmr-grp"') == 3)
check('group ١ الهندسة OPEN by default + tagged «يحرّك التقدير»',
      '<details class="thmr-grp" open>' in REF
      and 'الهندسة <span class="tagfx move">يحرّك التقدير</span>' in REF)
check('group ٢ العمر والحالة tagged «يدقّق مرتكز التكلفة»',
      'العمر والحالة <span class="tagfx tune">يدقّق مرتكز التكلفة</span>' in REF)
check('group ٣ معلومات مالية tagged «اختياري للإثراء»',
      'معلومات مالية <span class="tagfx opt">اختياري للإثراء</span>' in REF)
_ids = ('floors', 'basement', 'penthouse', 'annexes', 'externalMajlis', 'footprintM2',
        'buildingAge', 'condition', 'isLuxury', 'rentalIncome', 'potentialRental',
        'askingPrice', 'unitCount', 'avgRentPerUnit', 'rentalIncomeLabel', 'fpHint')
check('EVERY refine field id unchanged (the re-eval reads by id)',
      all(f'id="{i}"' in REF for i in _ids),
      str([i for i in _ids if f'id="{i}"' not in REF]))
check('group assignment: geometry in ١ / age+condition in ٢ / financial in ٣',
      REF.find('id="floors"') < REF.find('العمر والحالة')
      and REF.find('العمر والحالة') < REF.find('id="buildingAge"')
      and REF.find('id="buildingAge"') < REF.find('معلومات مالية')
      and REF.find('معلومات مالية') < REF.find('id="rentalIncome"'))
check('towerRentSection UNGROUPED (before the first <details> — the b22 flow holds)',
      0 <= REF.find('id="towerRentSection"') < REF.find('<details class="thmr-grp"'))
check('the income-lead hint on the actual rent (the v3 gold hint)',
      'قد يقود الدخلُ التقدير' in REF)
check('the E1 «لا يؤثّر» micro on the asking price',
      'لا يؤثّر على التقدير' in REF and 'الأسعار المعلنة ليست أدلّة' in REF)
check('the focus helper opens a closed <details> ancestor (the b13 nudge path)',
      'if(dts&&!dts.open)dts.open=true;' in HTML)
check('the thmr-grp CSS family defined',
      '.thmr-grp summary' in HTML and '.tagfx.move' in HTML and '.tagfx.tune' in HTML
      and '.tagfx.opt' in HTML)

print('\n[3] the setbacks equation (E15) under the building area')
check('refine hint carries the equation (setback-envelope gated)',
      "footprint_method==='setback_envelope'?' بعد الارتدادات القانونية (أمامي 5 · جانبي 3 · خلفي 3) وضمن سقف تغطية 60%'" in HTML)
check('confirm basis row carries the equation',
      'بعد الارتدادات القانونية: أمامي 5 · جانبي 3 · خلفي 3، وضمن سقف تغطية 60%' in HTML)
check('cov-cap/shared paths NOT given a setbacks claim (honest gating)',
      'حصة الوحدة في قطعة مشتركة' in HTML)

print('\n[4] version format (R6 / Lesson 2)')
with open('evaluate_unified.py', encoding='utf-8') as fh:
    ENG = fh.read()
check('ENGINE_VERSION format', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)

print(f'\n=== {PASS} passed, {FAIL} failed ===')
sys.exit(1 if FAIL else 0)
