#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isolated logic tests — Sprint 2.22.0a.21 (B-1): land-floor / HBU decomposition surface.

PRESENTATION ONLY — value-invariant. Surfaces the land-value floor + implied-building
decomposition next to the a17/a19 condition caveat for villa/house comparison outputs.
F1: recomputes the floor INDEPENDENTLY of _decompose_value's Patch-C suppression so it
surfaces for the land-priced cohort (land >= value), with implied building clamped to 0
(never negative) + a land-anchored disclosure.

Per Rule #40 / E14 these tests import and exercise the PRODUCTION functions
(`evaluate_unified._villa_value_floor`, `_condition_note_applies`,
`_stage1_dispersion_gate`) + the LOCKED multi-AI copy constants — not replicas.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0a21.py
"""
import re
import sys

from evaluate_unified import (
    _villa_value_floor,
    _condition_note_applies,
    _stage1_dispersion_gate,
    LAND_FLOOR_NOTE_AR, LAND_FLOOR_NOTE_EN,
    IMPLIED_BLDG_NOTE_AR, IMPLIED_BLDG_NOTE_EN,
    LAND_ANCHORED_NOTE_AR, LAND_ANCHORED_NOTE_EN,
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


# Fixtures (mirror the Phase-0 live anchors) ----------------------------------
DECOMP_647 = {'land': {'estimated_qar': 2456736, 'per_m2_qar': 3768,
                       'n_transactions': 20, 'window_months': 24, 'reliable': True}}
MOJ_MERAIDH = {'categories': {'land': {'price_per_m2': {'median': 2547},
                                       'n': 25, 'window_months': 36, 'reliable': True}}}
MOJ_650 = {'categories': {'land': {'price_per_m2': {'median': 3768},
                                   'n': 20, 'window_months': 24, 'reliable': True}}}

# ── 1. F2 — bracket/widened villa, land < value: floor present, implied > 0 ──
b1 = _villa_value_floor(3800000, 652, None, DECOMP_647)
check('F2 56/647/6 floor present', bool(b1) and b1['land_floor'] == 2456736)
check('F2 implied building > 0', b1['implied_building_value'] == 1343264)
check('F2 land_anchored False', b1['land_anchored'] is False)
check('F2 no anchored note', 'land_anchored_note_ar' not in b1)

# ── 2. F1 land-priced (decomp None, moj_ref land > value) [LOAD-BEARING] ──
b2 = _villa_value_floor(2600000, 1050, MOJ_MERAIDH, None)
check('F1 55/296/13 floor present (Patch-C independent)', bool(b2) and b2['land_floor'] == 2674350)
check('F1 implied building == 0 (NEVER negative)', b2['implied_building_value'] == 0)
check('F1 land_anchored True', b2['land_anchored'] is True)
check('F1 land_anchored_note present', 'land_anchored_note_ar' in b2)

# ── 3. F1 floor < value (modern/positive building) ──
b3 = _villa_value_floor(3300000, 375, MOJ_650, None)
check('F1 56/650/4 floor present', bool(b3) and b3['land_floor'] == 1413000)
check('F1 56/650/4 implied building > 0', b3['implied_building_value'] == 1887000 and b3['land_anchored'] is False)

# ── 4. F2-prefer over F1: with decomp present, use decomp even if moj_ref differs ──
b4 = _villa_value_floor(3800000, 652, MOJ_650, DECOMP_647)  # moj_ref would give 3768*652, decomp says 2456736
check('F2 prefers existing decomp over recompute', b4['land_floor'] == 2456736)

# ── 5. Guards: amount None / plot None / n<3 / no land → None ──
check('amount None -> None', _villa_value_floor(None, 652, MOJ_650, None) is None)
check('plot None -> None', _villa_value_floor(2600000, None, MOJ_650, None) is None)
check('land n<3 -> None', _villa_value_floor(2600000, 1050,
      {'categories': {'land': {'price_per_m2': {'median': 2547}, 'n': 2}}}, None) is None)
check('no moj land + no decomp -> None', _villa_value_floor(2600000, 1050, None, None) is None)

# ── 6. VALUE-INVARIANCE: helper is pure-derive, never emits/changes an amount ──
check('block has no amount key', 'amount' not in b1 and 'value' not in b1)
check('implied = amount - floor (exact, no rounding drift on headline)',
      b1['implied_building_value'] == 3800000 - b1['land_floor'])

# ── 7. Gate (a) = _condition_note_applies scope (the value_floor rides this) ──
check('gate villa+thin (gate None) -> fires',
      _condition_note_applies({'method': 'comparison_thin'}, None, 'standalone_villa', 2600000) is True)
check('gate villa+bracket (not gated) -> fires',
      _condition_note_applies({'method': 'comparison_bracket'},
                              {'gated': False}, 'standalone_villa', 2400000) is True)
check('gate dispersed-widened (gated) -> excluded',
      _condition_note_applies({'method': 'comparison_widened'},
                              {'gated': True}, 'standalone_villa', 4000000) is False)
check('gate apartment -> excluded',
      _condition_note_applies({'method': 'insufficient_data'}, None, 'apartment_building', None) is False)
check('gate land -> excluded',
      _condition_note_applies({'method': 'comparison_bracket'}, None, 'raw_land', 1000000) is False)
check('gate house alias -> fires',
      _condition_note_applies({'method': 'comparison_thin'}, None, 'house', 2600000) is True)
# dispersion gate is the same object the value_floor consults; thin -> None
check('_stage1_dispersion_gate(thin) is None', _stage1_dispersion_gate({'method': 'comparison_thin'}, None) is None)

# ── 8. Verbatim LOCKED copy (multi-AI) — fail loudly on drift ──
check('AR land-floor copy verbatim',
      'تفكيك تحليلي ضمن نموذج المقارنة' in LAND_FLOOR_NOTE_AR
      and 'يعكس الاستخدام الأمثل للأرض، وليس قيمة سوقية مستقلة' in LAND_FLOOR_NOTE_AR)
check('AR implied-building copy verbatim',
      'القيمة الضمنية للمبنى (ناتج حسابي: التقدير ناقص الأرض)' in IMPLIED_BLDG_NOTE_AR
      and 'غير مُتحقَّقة ميدانياً' in IMPLIED_BLDG_NOTE_AR)
check('AR land-anchored copy verbatim',
      'لا تتجاوز قيمة الأرض المجردة' in LAND_ANCHORED_NOTE_AR
      and 'القيمة الضمنية للمبنى ≈ صفر' in LAND_ANCHORED_NOTE_AR)
check('EN strings present', bool(LAND_FLOOR_NOTE_EN and IMPLIED_BLDG_NOTE_EN and LAND_ANCHORED_NOTE_EN))

# ── 9. No bare Latin in the 3 AR notes (numbers are LRM-wrapped, no Latin words) ──
for _label, _note in [('land_floor', b1['land_floor_note_ar']),
                      ('implied', b3['implied_building_note_ar']),
                      ('anchored', b2['land_anchored_note_ar'])]:
    check(f'AR note "{_label}" has no Latin letters', re.search(r'[A-Za-z]', _note) is None)
check('AR land-floor note LRM-wraps the number', '‎' in b1['land_floor_note_ar'])

# ── 10. Citation tag present (HBU / Sales Comparison) ──
check('citation_ar present', 'VPS 3' in b1['citation_ar'] and 'VPS 2' in b1['citation_ar'])

print()
print(f'Sprint 2.22.0a.21 isolated: {_passed} passed, {_failed} failed')
sys.exit(0 if _failed == 0 else 1)
