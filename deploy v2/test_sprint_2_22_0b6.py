# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.6 (§6 R7) — income-triangulation isolated tests.

Exercises the PRODUCTION pure function evaluate_unified._income_triangulation
(E14 / Rule #40 — imports the real engine function, not a replica).

Two modes:
  income_led ((i)/أ) — grounded SUBJECT rent + calibrated reliable/indicative cell →
    income LEADS the villa headline (clamped to [land_floor, cost_ceiling]).
  widen_down ((iii)) — no-rent condition-blind THIN/uncertain villa (NOT a clean
    reliable bracket, NOT a dispersion-gated pool) → range widens DOWN to land_floor.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b6.py
"""
import sys
from evaluate_unified import _income_triangulation as TRI

_pass = 0
_fail = 0

def check(name, cond):
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  PASS  {name}")
    else:
        _fail += 1
        print(f"  FAIL  {name}")

# ── fixtures ──
P_THIN  = {'value': 5_400_000, 'method': 'comparison_thin', 'high': 5_500_000}
P_BRACK = {'value': 2_400_000, 'method': 'comparison_bracket', 'high': 2_600_000}
P_WIDE  = {'value': 4_000_000, 'method': 'comparison_widened', 'high': 4_400_000}
LF = 1_851_260   # Marikh land floor (a21)

def income(value, rent_source='actual_provided', source='calibrated',
           conf='reliable', cap=0.052, n=46, nyp=5.16, rent=190_000):
    return {'value': value, 'rent_source': rent_source, 'cap_rate': cap,
            'annual_rent': rent,
            'cap_rate_provenance': {'source': source, 'confidence': conf,
                                    'net_yield_pct': nyp, 'sample_size': n}}

print("Sprint 2.22.0b.6 §6 income-triangulation\n")

# 1 — income LEADS: grounded subject rent + calibrated reliable, within rails
t = TRI(P_THIN, income(2_900_000), None, LF, 'standalone_villa')
check("1 income_led fires on grounded+calibrated+within", t and t['mode'] == 'income_led')
check("1 amount = income value", t and t['amount'] == 2_900_000)
check("1 comparison demoted (disclosed, not the headline)", t and t['comparison_value'] == 5_400_000)
check("1 large spread -> MUC high", t and t['muc_level'] == 'high')

# 2 — municipality (area) rent does NOT lead (circularity guard) -> falls to widen_down
t = TRI(P_THIN, income(2_900_000, rent_source='rent_reference_municipality'), None, LF, 'standalone_villa')
check("2 municipality rent -> NOT income_led", t and t['mode'] == 'widen_down')

# 3 — hardcoded (non-calibrated) cap does NOT lead -> widen_down
t = TRI(P_THIN, income(2_900_000, source='hardcoded', conf='fallback'), None, LF, 'standalone_villa')
check("3 hardcoded cap -> NOT income_led", t and t['mode'] == 'widen_down')

# 4 — income below the land floor is implausible -> NOT income_led -> widen_down
t = TRI(P_THIN, income(1_500_000), None, LF, 'standalone_villa')
check("4 income < land_floor -> NOT income_led", t and t['mode'] == 'widen_down')

# 5 — income above cost ceiling (×1.05) is implausible -> NOT income_led
t = TRI(P_THIN, income(5_000_000), {'value': 4_000_000}, LF, 'standalone_villa')
check("5 income > cost ceiling -> NOT income_led", not (t and t['mode'] == 'income_led'))

# 6 — widen_down on a no-rent THIN villa (land floor below the median)
t = TRI(P_THIN, None, None, LF, 'standalone_villa')
check("6 widen_down fires on no-rent thin villa", t and t['mode'] == 'widen_down')
check("6 low = land_floor", t and t['low'] == LF)
check("6 high = comparison high", t and t['high'] == 5_500_000)
check("6 MUC high", t and t['muc_level'] == 'high')

# 7 — CLEAN reliable bracket is NOT widened (the good case — correctness finding)
t = TRI(P_BRACK, None, None, 1_700_000, 'standalone_villa')
check("7 clean comparison_bracket NOT widened", t is None)

# 8 — a dispersion-gated pool is left to a10/a14 (NOT widened here)
t = TRI(P_WIDE, None, None, LF, 'standalone_villa', dispersion_gated=True)
check("8 dispersion_gated -> NOT widened (a10/a14 owns)", t is None)

# 9 — no DOWN to widen when land floor >= comparison
t = TRI(P_THIN, None, None, 5_500_000, 'standalone_villa')
check("9 land_floor >= comp -> no widen", t is None)

# 10 — non-villa asset -> None (villa/house only)
check("10 apartment -> None", TRI(P_THIN, income(2_900_000), None, LF, 'apartment_building') is None)
check("10 raw_land -> None", TRI(P_THIN, None, None, LF, 'raw_land') is None)

# 11 — income_led with a small spread -> MUC moderate
t = TRI(P_THIN, income(5_000_000), None, LF, 'standalone_villa')
check("11 small spread -> MUC moderate", t and t['mode'] == 'income_led' and t['muc_level'] == 'moderate')

# 12 — income CAN lead a clean bracket too (a grounded rent overrides any method)
t = TRI(P_BRACK, income(2_000_000), None, 1_700_000, 'standalone_villa')
check("12 income_led fires on bracket WITH a grounded rent", t and t['mode'] == 'income_led')
check("12 bracket income_led amount = income value", t and t['amount'] == 2_000_000)

# 13 — guards: no primary / no value -> None
check("13 None primary -> None", TRI(None, income(2_900_000), None, LF, 'standalone_villa') is None)
check("13 primary without value -> None", TRI({'method': 'comparison_thin'}, None, None, LF, 'standalone_villa') is None)

# 14 — house alias behaves like villa
t = TRI(P_THIN, None, None, LF, 'house')
check("14 house alias -> widen_down", t and t['mode'] == 'widen_down')

print(f"\n{_pass} passed, {_fail} failed")
sys.exit(1 if _fail else 0)
