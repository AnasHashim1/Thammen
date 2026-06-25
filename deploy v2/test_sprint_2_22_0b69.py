#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isolated test — Sprint 2.22.0b.69 (T0-2 completeness): income_led leadership + value_stack.

b67 closed the COHERENCE half of T0-2 (recompute value_decomposition/value_floor on the income
amount). b69 closes the COMPLETENESS half: the income_led branch now ALSO emits a minimal
`leadership{leader='income', rule='income_led', note_ar, ...}` + a `value_stack{market, cost,
income_available}` so the FULL report renders the leader verdict note + the DEF-12 cost row on
income_led (previously OMITTED — weaker than every other leader path).

HEADLINE VALUE-INVARIANT: the emission is ADDITIVE, inside the `if _tri['mode']=='income_led':`
block (before the `else:`) → the 5 no-rent fixtures never enter; amount/low/high/method/rule
untouched. leader='income' keeps b64 #4's cost-basis hero line OFF (it keys on 'cost').

income_led needs live khazna for a full-path run (dev host geo-restricted), so this test is
STRUCTURAL on the REAL evaluate_unified.py source + the constants it reuses (E14: the actual
production block) — the full-path coherence is proven by the post-deploy live E2E + R14 (§20.98).

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b69.py
"""
import re
import sys
from pathlib import Path

import evaluate_unified as E

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


src = Path(__file__).parent.joinpath('evaluate_unified.py').read_text(encoding='utf-8')
i_if = src.find("if _tri and _tri['mode'] == 'income_led':")
i_else = src.find("\n                    else:", i_if)
check('income_led if-block found', i_if != -1)
check('income_led else found after it', i_else != -1 and i_else > i_if)
block = src[i_if:i_else]

# ── 1. The b69 leadership emission (income leader) ──
check('b69 emits leadership on income_led',
      "output['valuation']['leadership'] = {" in block)
check("leadership leader='income' + rule='income_led'",
      "'leader': 'income', 'rule': 'income_led'" in block)
check('leadership note REUSES the built income note (_note_ar/_note_en, zero new copy)',
      "'note_ar': _note_ar," in block and "'note_en': _note_en," in block)
check('leadership market_value = the demoted comparison (_tri comparison_value)',
      "'market_value': _tri['comparison_value']," in block)

# ── 2. The income leadership OMITS the market-evidence fields (it is NOT a market verdict) ──
#       (those — matched_n / dispersion_36 / band / geo_full / thresholds — justify a MARKET lead;
#        surfacing them on an income leader would falsely imply the pool decided the number)
_lead_seg = block[block.find("output['valuation']['leadership'] = {"):]
for _k in ["'matched_n'", "'dispersion_36'", "'band'", "'geo_full_n'", "'thresholds'", "'stratum_match'"]:
    check(f'income leadership OMITS market-evidence key {_k}', _k not in _lead_seg)

# ── 3. The b69 value_stack ──
check('b69 emits value_stack on income_led',
      "output['valuation']['value_stack'] = {" in block and "'income_available': True," in block)
check('value_stack.market.median = the demoted comparison',
      "'median': _tri['comparison_value']," in block)
check('value_stack.cost reuses the COST_STACK builder + _cost_av',
      'COST_STACK_LABEL_AR' in block and "'value': _cost_av['value']," in block)
# the income value_stack.market has NO dispersion_36 (so the report's market-dispersion line stays off)
_vs_seg = block[block.find("output['valuation']['value_stack'] = {"):
                block.find("output['valuation']['leadership'] = {")]
check('income value_stack.market has NO dispersion_36 (no market-evidence claim)',
      'dispersion_36' not in _vs_seg)

# ── 4. The b67 coherence recompute is STILL present (b69 is additive, above the else) ──
check('b67 recompute still in the income_led block (value_decomposition + value_floor)',
      '_decompose_value(' in block and "output['valuation']['value_decomposition']" in block
      and '_villa_value_floor(' in block and "output['valuation']['value_floor']" in block)
check('b69 marker present', 'Sprint 2.22.0b.69' in block)

# ── 5. The emission is income-branch-local (does NOT leak into the else / b20 _lead20 path) ──
else_block = src[i_else:]
check("b69 income leadership does NOT leak into the else (else keeps _lead20)",
      "'leader': 'income', 'rule': 'income_led'" not in else_block and '_lead20' in else_block)

# ── 6. Constants the emission reuses are defined (E14 — real module) ──
for _c in ('COST_STACK_LABEL_AR', 'COST_STACK_LABEL_EN', 'COST_STACK_SUB_AR', 'COST_STACK_SUB_EN'):
    check(f'constant {_c} defined', isinstance(getattr(E, _c, None), str))

# ── 7. Version format (version-agnostic — R6: no exact-version pins) ──
check('ENGINE_VERSION has the valid sprint format',
      re.search(r"ENGINE_VERSION\s*=\s*'thammen-sprint\d+p\d+p\d+", src) is not None)

print()
print(f'Sprint 2.22.0b.69 isolated: {_passed} passed, {_failed} failed')
sys.exit(0 if _failed == 0 else 1)
