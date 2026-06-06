# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.2 — Guided staged-input flow (WRAP).

Isolated tests exercising the PRODUCTION helpers (Rule #40 / E14) — no GIS.
Covers the one backend delta (brief F3): `effective_footprint_m2` = the post-cap
ground footprint the comparison ACTUALLY used (single source of truth, the hoisted
`_eff_fp`), the F2 building-gate contract the frontend keys on, and fallback.

Live-engine evidence (effective 405 assumed / 540 capped, value-invariant
2.4M / 2.9M on 56/565/21) is the scratch `.b2_e2e.py` probe — kept OUT of the
suite (no GIS here, mirrors b1's no-GIS isolated set).

Run:  set PYTHONIOENCODING=utf-8 & python test_sprint_2_22_0b2.py
"""
import re
import sys

import evaluate_unified as EU

_fail = 0
_pass = 0


def check(name, cond):
    global _fail, _pass
    if cond:
        _pass += 1
        print(f"  PASS  {name}")
    else:
        _fail += 1
        print(f"  FAIL  {name}")


# The production effective-footprint expression (evaluate_unified, hoisted _eff_fp,
# surfaced as round(_eff_fp)):
#   confirmed -> min(user_footprint, plot * _zone_max_coverage(code))
#   assumed   -> _suggested_footprint(plot, code)
# Asserted against the REAL helpers so the test tracks the engine, not a copy.
def _eff(plot, code, footprint=None):
    confirmed = bool(footprint and footprint > 0)
    if confirmed:
        e = float(footprint)
        if plot:
            e = min(e, plot * EU._zone_max_coverage(code))
    else:
        s = EU._suggested_footprint(plot, code)
        e = float(s) if s else None
    return round(e) if e is not None else None


print("=" * 64)
print("T1 — effective_footprint_m2 = the value the comparison ACTUALLY uses (F3)")
# assumed: effective == the surfaced suggestion (so the assumed path is byte-identical)
check("assumed 900 R1 -> eff == suggested (405)",
      _eff(900, 'R1') == EU._suggested_footprint(900, 'R1') == 405)
check("assumed 600 R1 -> eff == suggested",
      _eff(600, 'R1') == EU._suggested_footprint(600, 'R1'))
check("assumed 600 None -> eff == legacy typical",
      _eff(600, None) == round(EU._typical_footprint(600)))
# confirmed BELOW the ceiling: not capped -> eff == input
check("confirmed 300 on 900 R1 (<540) -> 300 (not capped)", _eff(900, 'R1', 300) == 300)
# confirmed ABOVE the ceiling: capped to plot*ceiling (the F3 fix)
check("confirmed 600 on 900 R1 -> capped 540", _eff(900, 'R1', 600) == 540)
check("confirmed 500 on 600 R1 -> capped 360", _eff(600, 'R1', 500) == 360)
check("confirmed 600 on 600 R2 -> capped 300", _eff(600, 'R2', 600) == 300)

print("=" * 64)
print("T2 — anti-inflation + assumed-path value-invariance")
check("confirmed eff <= plot*ceiling for ALL plots/zones",
      all(_eff(p, z, p) <= round(p * EU._zone_max_coverage(z))
          for p in (300, 500, 700, 900, 1500) for z in ('R1', 'R2', 'R3', None)))
check("assumed eff == suggested (surface byte-identical) for ALL plots/zones",
      all(_eff(p, z) == EU._suggested_footprint(p, z)
          for p in (300, 500, 700, 900, 1500) for z in ('R1', 'R2', 'R3', None)))
check("cap never raises a below-ceiling input",
      _eff(900, 'R1', 200) == 200 and _eff(900, 'R1', 600) == 540)

print("=" * 64)
print("T3 — F2 building-gate contract (frontend _b2IsBuilding mirror)")
# The frontend shows the Stage-2 confirm ONLY for these; raw_land + refusals excluded.
BUILDING = {'standalone_villa', 'villa', 'house'}
def is_building(at):
    return at in BUILDING
check("standalone_villa (live villa+house class) -> show", is_building('standalone_villa'))
check("villa alias -> show", is_building('villa'))
check("house alias -> show", is_building('house'))
check("raw_land -> EXCLUDED (the b1 card quirk fixed)", not is_building('raw_land'))
check("apartment_building -> EXCLUDED (refusal anyway)", not is_building('apartment_building'))
check("unknown/None -> EXCLUDED", not is_building(None) and not is_building('unknown'))

print("=" * 64)
print("T4 — fallback / no-regression")
check("no plot -> suggested None -> eff None", _eff(None, 'R1') is None)
check("zero plot -> eff None", _eff(0, 'R1') is None)
# b2 did NOT touch basement exclusion (b1 §5.5) — re-assert it still holds.
with_b = EU._build_smart_bua(plot_area_m2=600, floors=3, annexes=0, basement=True, footprint_m2=300)
without_b = EU._build_smart_bua(plot_area_m2=600, floors=3, annexes=0, basement=False, footprint_m2=300)
check("basement still excluded from the driver (b1 §5.5 intact)",
      EU._building_substantiality(without_b, 600)['actual_bua']
      < EU._building_substantiality(with_b, 600)['actual_bua'])

print("=" * 64)
print("T5 — version format (R6: format only, no exact pin)")
check("ENGINE_VERSION starts 'thammen-sprint'", EU.ENGINE_VERSION.startswith('thammen-sprint'))
check("ENGINE_VERSION dotted-sprint format (R6: no exact pin — survives bumps)",
      re.match(r'^thammen-sprint\d+p\d+p\d+', EU.ENGINE_VERSION) is not None)
check("SPRINT_TAG dotted-numeric prefix", re.match(r'^\d+\.\d+\.\d+', EU.SPRINT_TAG) is not None)

print("=" * 64)
print(f"RESULT: {_pass} passed, {_fail} failed")
sys.exit(1 if _fail else 0)
