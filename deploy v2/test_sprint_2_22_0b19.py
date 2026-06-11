# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.19 — the THREE-VALUE report display (display-only on the b20 contract)
+ the validate_gt_sheet.py D-3 kit. Static/structural pins (the behavioral render = R14).

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b19.py
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

PASS = FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  PASS {name}')
    else:
        FAIL += 1
        print(f'  FAIL {name}')

HTML = io.open('index.html', encoding='utf-8').read()
# the DEF-12 block (rep-def12 open .. close)
m = re.search(r"h\+='<div class=\"rep-def12\">';(.*?)h\+='</div>';", HTML, re.S)
check('rep-def12 block found', bool(m))
blk = m.group(1) if m else ''

print('— §1 the three-value rows (order + sources) —')
i_mv = blk.find('القيمة السوقية (الوسيط)')
i_cost = blk.find('v.value_stack.cost.label_ar')
i_fs = blk.find('قيمة البيع الجبري الإرشادية')
check('MV row present', i_mv >= 0)
check('cost row composes from value_stack.cost.label_ar (the SOLE source)', i_cost >= 0)
check('forced-sale row present', i_fs >= 0)
check('order: MV -> cost -> forced-sale', 0 <= i_mv < i_cost < i_fs)
check('V001 calibration sub-line rides value_stack.cost.sub_ar', 'v.value_stack.cost.sub_ar' in blk)
check('no hardcoded cost label duplicate (label comes from the engine contract)',
      'قيمة التكلفة (أرض + بناء مُهلَك)' not in blk)

print('— §2 the three cost branches (villa value / unavailable / raw_land) —')
check('unavailable branch', 'v.value_stack.cost.unavailable_reason_ar' in blk)
check('raw_land branch = the unified DRC≡land line (v.cost_note_ar)', 'v.cost_note_ar' in blk)
check('branch order value -> unavailable -> cost_note (else-if chain)',
      blk.find('v.value_stack.cost.value') < blk.find('unavailable_reason_ar') < blk.find('v.cost_note_ar'))

print('— §3 display-only purity (no new value math) —')
check('exactly ONE Math.round in the block (the existing x0.90 only)',
      blk.count('Math.round') == 0 and HTML.count("const _fs=Math.round((v.amount||0)*0.90);") == 1)
check('no arithmetic on the cost value (display verbatim)',
      not re.search(r"value_stack\.cost\.value\s*[*+\-/]", blk))
check('forced-sale basis line discloses the central x0.90',
      'الأساس: القيمة السوقية المركزية (الوسيط) ×' in blk)
check('forced-sale convention line intact (b17 verbatim)',
      'ليست تقييم تصفية معتمداً' in blk)
check('a8 contract: no calc-block in the report block', 'calc-block' not in blk)

print('— §4 engine untouched (version bump only) —')
import evaluate_unified as EU
check('ENGINE_VERSION = b19 slug', '2p22p0b19' in EU.ENGINE_VERSION
      and EU.ENGINE_VERSION.startswith('thammen-sprint'))
check('SPRINT_TAG = 2.22.0b.19', EU.SPRINT_TAG == '2.22.0b.19')
check('the b20 gate untouched (leadership chain intact)',
      callable(getattr(EU, '_leadership_gate', None))
      and EU.LEAD_GEO_FULL_MIN_N == 20 and EU.LEAD_DISPERSION_T == 0.30)

print('— §5 the D-3 kit (validate_gt_sheet.py) —')
GT = io.open('validate_gt_sheet.py', encoding='utf-8').read()
check('imports the PRODUCTION curve (E14)',
      'from evaluate_unified import _cost_retention, COST_RCN_BY_FINISH' in GT)
check('live basis from value_stack.cost (the b20 contract)',
      "value_stack" in GT and "land_floor" in GT and "bua_m2" in GT)
check('raw-age basis (E26: penalty 0) documented + used',
      'penalty 0' in GT and '_cost_retention(a.age, a.finish)' in GT)
check('appends to the tracked log path', "LOG = 'docs/validation/VALIDATION_LOG.md'" in GT)
check('intake document-rule stated', 'no row without' in GT or 'بمستند' in GT)
check('dry-run supported', '--dry-run' in GT)
check('browser-UA curl (Rule #61)', 'Mozilla/5.0' in GT and 'curl' in GT)

print(f'\n{PASS} passed, {FAIL} failed')
sys.exit(1 if FAIL else 0)
