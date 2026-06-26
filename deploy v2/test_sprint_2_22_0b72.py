#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isolated test — Sprint 2.22.0b.72: value-clarity for divergent cost vs market.

When an old property's COST (DRC) and MARKET median diverge (e.g. cost 9M / market 3M), the
ordinary owner could be confused which is "their value". b72 (VALUE-INVARIANT — every number +
the chosen leader UNCHANGED) makes the screen clear in plain فصحى مبسّطة:
  (1) the cost-led basis note is de-jargoned (drop «حوض المقارنات لم يجتز اختبار الموثوقيّة»),
  (2) the e25_capped cost-divergence is surfaced ON-SCREEN (was only in the collapsed fold),
  (3) a one-sentence bridge labels the report's three values,
  (4) the engine LEAD_COST_NOTE_AR / LEAD_E25_NOTE_AR are de-jargoned (placeholders kept).
The locked b54 headline label «التقييم السوقي» is NOT renamed (a PO brand decision).

Per E14 this reads the REAL index.html + evaluate_unified.py.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b72.py
"""
import re
import sys
from pathlib import Path

import evaluate_unified as eu

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


html = Path(__file__).parent.joinpath('index.html').read_text(encoding='utf-8')

# ── 1. cost-led basis note (TIER-1) de-jargoned, market value still shown ──
check('cost-led note: jargon «حوض المقارنات لم يجتز» removed', 'حوض المقارنات لم يجتز' not in html)
check('cost-led note: plain «الصفقات المماثلة القريبة كانت قليلة»', 'الصفقات المماثلة القريبة كانت قليلة' in html)
check('cost-led note: «بِيعت بيوتٌ في منطقتك بنحو» + the market value fmt(_clMkt)',
      'بِيعت بيوتٌ في منطقتك بنحو' in html and "fmt(_clMkt)" in html)
check('cost-led note: still gated on leader===cost (value-invariant placement)',
      "v.leadership.leader==='cost'" in html)

# ── 2. e25_capped cost-divergence surfaced ON-SCREEN (TIER-1) ──
check('e25 on-screen block gated leader===market && rule===e25_capped',
      "v.leadership.leader==='market'&&v.leadership.rule==='e25_capped'" in html)
check('e25 on-screen: «كلفةُ إعادة بناء بيتك» + «أعلى من سعر بيعه الحاليّ»',
      'كلفةُ إعادة بناء بيتك' in html and 'أعلى من سعر بيعه الحاليّ' in html)
check('e25 on-screen: plain «المباني تُباع بسعر السوق لا بكلفة بنائها»',
      'المباني تُباع بسعر السوق لا بكلفة بنائها' in html)
check('e25 on-screen: reads the broadcast value_stack.cost.value (display-only)',
      "v.value_stack.cost.value" in html)

# ── 3. report DEF-12 three-value bridge sentence ──
check('DEF-12 bridge: «ثلاثة أرقام: تقديرُنا لقيمة بيتك · كلفةُ إعادة بنائه · وتقديرٌ عند البيع السريع»',
      'ثلاثة أرقام: تقديرُنا لقيمة بيتك · كلفةُ إعادة بنائه · وتقديرٌ عند البيع السريع.' in html)
check('DEF-12 bridge sits ABOVE the rep-def12 block',
      html.find('ثلاثة أرقام: تقديرُنا لقيمة بيتك') < html.find("h+='<div class=\"rep-def12\">';"))
# the three labeled rows + the forced-sale basis line are UNCHANGED (value-invariant)
check('DEF-12 forced-sale «ليست تصفية معتمدة» row preserved (value-invariant)', 'ليست تصفية معتمدة' in html)

# ── 4. engine leadership notes de-jargoned, placeholders + signed line intact ──
check('LEAD_E25_NOTE_AR: jargon «سقفاً مضاداً للتضخيم» removed', 'سقفاً مضاداً' not in eu.LEAD_E25_NOTE_AR)
check('LEAD_E25_NOTE_AR: plain «المباني تُباع بسعر السوق لا بكلفة بنائها»',
      'المباني تُباع بسعر السوق لا بكلفة بنائها' in eu.LEAD_E25_NOTE_AR)
check('LEAD_E25_NOTE_AR: {cost}+{comp} placeholders intact + .format works',
      '{cost}' in eu.LEAD_E25_NOTE_AR and '{comp}' in eu.LEAD_E25_NOTE_AR
      and '9,000,000' in eu.LEAD_E25_NOTE_AR.format(cost='9,000,000', comp='3,000,000'))
check('LEAD_COST_NOTE_AR: jargon «حوض المقارنات لم يجتز» removed', 'حوض المقارنات لم يجتز' not in eu.LEAD_COST_NOTE_AR)
check('LEAD_COST_NOTE_AR: {n}{d}{cost}{comp} intact + .format works',
      all(p in eu.LEAD_COST_NOTE_AR for p in ('{n}', '{d}', '{cost}', '{comp}'))
      and '2,378,094' in eu.LEAD_COST_NOTE_AR.format(n=8, d=0.62, cost='2,378,094', comp='5,400,000'))
check('LEAD_COST_NOTE_AR: the SIGNED «لا رقم مركزيّ مُخترَع» line kept (b20 honesty)',
      'لا رقم مركزيّ مُخترَع' in eu.LEAD_COST_NOTE_AR)

# ── 5. the b54-locked hero label «التقييم السوقي» is NOT renamed (PO brand decision) ──
#     (the hero `.lbl` span carries it; we clarify the METHOD, we do not relabel the headline).
check('locked hero label «التقييم السوقي» preserved (headline not renamed)',
      'التقييم السوقي' in html)

# ── 6. version format (version-agnostic — R6) ──
check('ENGINE_VERSION has the valid sprint format',
      re.match(r'thammen-sprint\d+p\d+p\d+', eu.ENGINE_VERSION) is not None)

print()
print(f'Sprint 2.22.0b.72 isolated: {_passed} passed, {_failed} failed')
sys.exit(0 if _failed == 0 else 1)
