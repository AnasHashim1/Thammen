#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isolated logic tests — Sprint 2.22.0b.67 (T0-2): income_led decomposition/value_floor coherence.

When a user enters a grounded rent and the income_led branch leads the villa/house headline
(evaluate_unified.py:5002+), the branch overrode the central via a NON-comparison method but
left value_decomposition + value_floor anchored to the PRE-income COMPARISON figure (built
4797-4822) → the FULL report rendered a land/building split + a value-floor disclosure that
sum to the discarded comparison amount UNDER the income headline (internal incoherence; the
documented §20.50/§20.53/§20.88 income_led decomposition-recompute gap).

b67 recomputes BOTH on the income amount — the VERBATIM proven cost_led recompute
(5138-5153, the b16 ISS-A07 pattern). Value-invariant on amount/low/high (additive, inside
the income_led if-block → the 5 no-rent fixtures never enter).

Per Rule #40 / E14 these tests import + exercise the PRODUCTION helper
(`evaluate_unified._villa_value_floor`, `_decompose_value`) — not replicas — and assert the
recompute is WIRED into the real income_led source block (after the amount-set, on the income
amount), which is the decisive coherence guarantee.

NOTE (scope, Rule #38/#39): b67 ships the COHERENCE half of T0-2 (recompute the stale figures).
The COMPLETENESS half (emit leadership{leader='income'} + value_stack on income_led so the FULL
report leadership verdict + DEF-12 cost row also render) is DEFERRED to b68 — it is net-new
emitted structure needing its own R14 + persona review; no regression by deferring (those
surfaces are OMITTED today, not incoherent).

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b67.py
"""
import re
import sys
from pathlib import Path

from evaluate_unified import _villa_value_floor, _decompose_value

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


# Mirror the a21 fixtures (the live V001 land floor) ---------------------------
DECOMP_647 = {'land': {'estimated_qar': 2456736, 'per_m2_qar': 3768,
                       'n_transactions': 20, 'window_months': 24, 'reliable': True}}
MOJ_650 = {'categories': {'land': {'price_per_m2': {'median': 3768},
                                   'n': 20, 'window_months': 24, 'reliable': True}}}

INCOME_AMT = 2_800_000      # the §20.41 keystone: 54/541/6 + rent → income_led ~2.8M
COMPARISON_AMT = 5_400_000  # the pre-income comparison figure that was STALE-anchored

# ── 1. _villa_value_floor is AMOUNT-anchored → recomputing on the income amount
#       yields income figures, NOT the stale comparison floor (the core b67 claim) ──
vf_income = _villa_value_floor(INCOME_AMT, 652, None, DECOMP_647)
vf_comp = _villa_value_floor(COMPARISON_AMT, 652, None, DECOMP_647)
check('floor present on income amount', bool(vf_income) and vf_income['land_floor'] == 2456736)
check('income implied building == amount - floor (income-coherent)',
      vf_income['implied_building_value'] == INCOME_AMT - 2456736)        # 343,264
check('comparison implied building == comparison - floor (the STALE value)',
      vf_comp['implied_building_value'] == COMPARISON_AMT - 2456736)      # 2,943,264
check('income floor DIFFERS from comparison floor (recompute is NOT a no-op)',
      vf_income['implied_building_value'] != vf_comp['implied_building_value'])
check('income implied < comparison implied (lower headline → lower implied building)',
      vf_income['implied_building_value'] < vf_comp['implied_building_value'])

# ── 2. _decompose_value is AMOUNT-anchored too (the value_decomposition recompute) ──
dec_income = _decompose_value(valuation_amount=INCOME_AMT, plot_area_m2=652,
                              bua_m2=400, moj_ref_dict=MOJ_650)
dec_comp = _decompose_value(valuation_amount=COMPARISON_AMT, plot_area_m2=652,
                            bua_m2=400, moj_ref_dict=MOJ_650)
check('decompose returns a decomposition on the income amount', bool(dec_income))
check('decompose land component is amount-independent (same plot/median)',
      dec_income['land']['estimated_qar'] == 2456736)
check('decompose income building == income - land (income-coherent split)',
      dec_income['building_implied']['qar'] == INCOME_AMT - 2456736)
check('decompose income split SUMS to the income amount (not the comparison)',
      dec_income['land']['estimated_qar'] + dec_income['building_implied']['qar'] == INCOME_AMT)
check('decompose differs at the two amounts (amount-anchored)', dec_income != dec_comp)

# ── 3. Patch-C suppression still surfaces the floor (F1) when income < land ──
#       a low income on a premium plot → land > amount → decompose None, floor land_anchored.
vf_anchored = _villa_value_floor(2_000_000, 652, MOJ_650, None)
check('income < land → floor still surfaces (F1, land_anchored)',
      bool(vf_anchored) and vf_anchored['land_anchored'] is True
      and vf_anchored['implied_building_value'] == 0)

# ── 4. STRUCTURAL (E14): the recompute is WIRED into the REAL income_led block,
#       AFTER the amount-set, reading output['valuation']['amount'] (the income figure) ──
src = Path(__file__).parent.joinpath('evaluate_unified.py').read_text(encoding='utf-8')
mark_if = "if _tri and _tri['mode'] == 'income_led':"
mark_else = "\n                    else:"   # the 20-space else that closes the income branch
i_if = src.find(mark_if)
i_else = src.find(mark_else, i_if)
check('income_led if-block found', i_if != -1)
check('income_led else found after it', i_else != -1 and i_else > i_if)
block = src[i_if:i_else]
check('block recomputes value_decomposition via _decompose_value',
      '_decompose_value(' in block and "output['valuation']['value_decomposition']" in block)
check('block recomputes value_floor via _villa_value_floor',
      '_villa_value_floor(' in block and "output['valuation']['value_floor']" in block)
check('block re-runs the b14 narrative + brief inject',
      '_reconcile_decomposition_narrative(output)' in block
      and '_inject_value_floor_into_brief(' in block)
# the recompute reads output['valuation']['amount'] (the income figure), set EARLIER in the block
i_amt_set = block.find("output['valuation']['amount'] = _r100k(_tri['amount'])")
i_decomp = block.find('_decompose_value(')
check('amount is set before the recompute (recompute reads the INCOME amount)',
      i_amt_set != -1 and i_decomp != -1 and i_amt_set < i_decomp)
check('recompute is the b67 ISS-A07 block', 'Sprint 2.22.0b.67' in block and 'ISS-A07' in block)

# ── 5. VALUE-INVARIANCE (structural): the recompute is INSIDE the income_led if-block
#       (before the else) → the no-rent / market / cost path (else) is UNTOUCHED ──
else_block = src[i_else:]
# the cost_led recompute (the pattern we copied) still lives in the else, unchanged
# (_decomp20/_vf20 are the else-branch names; income uses _decompI/_vfI)
check('else-branch still has its own cost_led recompute (not moved/duplicated by b67)',
      '_decomp20' in else_block and '_vf20' in else_block)
# the b67 income recompute does NOT leak into the else (the edit is income-branch-local)
check('b67 income recompute (_decompI) does NOT appear in the else-branch',
      '_decompI' not in else_block and 'Sprint 2.22.0b.67' not in else_block)

# ── 6. Version format (version-agnostic — R6: no exact-version pins; the b67 landing
#       is proven by the 'Sprint 2.22.0b.67' comment marker in the recompute block above) ──
check('ENGINE_VERSION has the valid sprint format',
      re.search(r"ENGINE_VERSION\s*=\s*'thammen-sprint\d+p\d+p\d+", src) is not None)

print()
print(f'Sprint 2.22.0b.67 isolated: {_passed} passed, {_failed} failed')
sys.exit(0 if _failed == 0 else 1)
