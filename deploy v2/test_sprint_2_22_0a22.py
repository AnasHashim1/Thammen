#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isolated logic tests — Sprint 2.22.0a.22 (B-1.1): multi-AI-validated framing tweaks.

VALUE-INVARIANT, COPY-ONLY. Refines three a21 disclosure strings per the LOCKED multi-AI
adjudication (`docs/MULTI_AI_VALIDATION_BATCH_SprintB1.md`):
  - land floor → "indicative land component" on an HBU *premise* (not a determination)
  - implied building → "contribution / mathematical allocation" (not a "value")
  - widened method_label → names the recognised approach (Sales Comparison, geographically widened)
The RICS/IVS **citation tokens are UNCHANGED** (the models' renumbering "fixes" were rejected by
primary-source adjudication). This test GUARDS exactly that contract: framing changed, citations
byte-identical, headline value untouched.

Per Rule #40 / E14 these import + exercise the PRODUCTION constants/functions.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0a22.py
"""
import re
import sys

from evaluate_unified import (
    _villa_value_floor,
    LAND_FLOOR_NOTE_AR, LAND_FLOOR_NOTE_EN,
    IMPLIED_BLDG_NOTE_AR, IMPLIED_BLDG_NOTE_EN,
    _VALUE_FLOOR_CITATION_AR, _VALUE_FLOOR_CITATION_EN,
)

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


DECOMP_647 = {'land': {'estimated_qar': 2456736, 'per_m2_qar': 3768,
                       'n_transactions': 20, 'window_months': 24, 'reliable': True}}
b = _villa_value_floor(3800000, 652, None, DECOMP_647)

# ── 1. CITATIONS UNCHANGED (the load-bearing B-1.1 contract) ──
check('citation_ar tokens byte-identical (VPS 3 / IVS 103 / VPS 2 / IVS 102)',
      'VPS 3' in _VALUE_FLOOR_CITATION_AR and 'IVS 103' in _VALUE_FLOOR_CITATION_AR
      and 'VPS 2' in _VALUE_FLOOR_CITATION_AR and 'IVS 102' in _VALUE_FLOOR_CITATION_AR)
check('citation_en tokens byte-identical (VPS 3 / IVS 103 / VPS 2 / IVS 102)',
      _VALUE_FLOOR_CITATION_EN ==
      'Sales Comparison approach (VPS 3 / IVS 103); land value reflects Highest-and-Best-Use (VPS 2 / IVS 102)')
check('block citation_ar carried through unchanged', b['citation_ar'] == _VALUE_FLOOR_CITATION_AR)
# the rejected renumberings must NOT have leaked in
check('NO rejected renumbering (VPS 4 / VPS 5 / IVS 104 / IVS 105) in the floor citation',
      not any(t in _VALUE_FLOOR_CITATION_AR + _VALUE_FLOOR_CITATION_EN
              for t in ('VPS 4', 'VPS 5', 'IVS 104', 'IVS 105')))

# ── 2. FRAMING CHANGED to the new wording (verbatim) ──
check('land-floor AR = indicative land component on an HBU premise',
      'مكوّن الأرض الاسترشادي' in LAND_FLOOR_NOTE_AR
      and 'على أساس افتراض أعلى وأفضل استخدام؛ وليس تقييماً مستقلاً للأرض' in LAND_FLOOR_NOTE_AR)
check('land-floor EN = indicative land component on an HBU premise',
      'indicative land component' in LAND_FLOOR_NOTE_EN
      and 'on a highest-and-best-use premise' in LAND_FLOOR_NOTE_EN
      and 'not a standalone valuation of the land' in LAND_FLOOR_NOTE_EN)
check('implied AR = building contribution / mathematical allocation',
      'مساهمة البناء الضمنية (ناتج حسابي متبقٍّ: التقدير ناقص الأرض)' in IMPLIED_BLDG_NOTE_AR
      and 'تخصيص حسابي، غير مُتحقَّق ميدانياً' in IMPLIED_BLDG_NOTE_AR)
check('implied EN = building contribution / mathematical allocation',
      'Implied building contribution (computational residual: estimate minus land)' in IMPLIED_BLDG_NOTE_EN
      and 'a mathematical allocation, not field-verified' in IMPLIED_BLDG_NOTE_EN)
# old wording must be gone
check('old "land value"/"قيمة سوقية مستقلة" framing removed',
      'قيمة سوقية مستقلة' not in LAND_FLOOR_NOTE_AR and 'land value: ~' not in LAND_FLOOR_NOTE_EN)

# ── 3. value-invariance preserved (helper still pure-derive) + LRM + no-Latin ──
check('floor block unchanged value (no amount key; floor exact)',
      'amount' not in b and b['land_floor'] == 2456736 and b['implied_building_value'] == 1343264)
check('AR notes LRM-wrap the number', '‎' in b['land_floor_note_ar'] and '‎' in b['implied_building_note_ar'])
for lbl, note in [('land_floor', b['land_floor_note_ar']), ('implied', b['implied_building_note_ar'])]:
    check(f'AR note "{lbl}" has no Latin letters', re.search(r'[A-Za-z]', note) is None)

# ── 4. widened method_label names the recognised approach (source guard) ──
src = open('evaluate_unified.py', encoding='utf-8').read()
check('widened method_label = "منهج المقارنة بالمبيعات (مجموعة موسَّعة جغرافياً)"',
      'منهج المقارنة بالمبيعات (مجموعة موسَّعة جغرافياً) (‎RICS VPS 3 / IVS 103‎)' in src
      and 'منهج المقارنة بالمبيعات (مجموعة موسَّعة جغرافياً) — شواهد محدودة (‎RICS VPS 3 / IVS 103‎)' in src)
check('old "مقارنة بتوسيع جغرافي" label removed', 'مقارنة بتوسيع جغرافي' not in src)

print()
print(f'Sprint 2.22.0a.22 isolated: {_passed} passed, {_failed} failed')
sys.exit(0 if _failed == 0 else 1)
