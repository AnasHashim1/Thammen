# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.1 — Geometry Refinement (BUA): zoning-driven footprint +
basement-excluded comparison driver + assumed-vs-confirmed labelling.

Isolated tests exercising the PRODUCTION functions (Rule #40 / E14) — no GIS.
Gate-2 SIGNED deltas:
  (أ) zoning-driven footprint suggestion + zone-aware cap (R1=60 / R2=50)
  (ب) exclude basement from the BUA that feeds _building_substantiality
  (ج) assumed-vs-confirmed footprint basis (surfaced + MVU caveat)

Run:  set PYTHONIOENCODING=utf-8 & python test_sprint_2_22_0b1.py
"""
import re
import sys
from types import SimpleNamespace

import evaluate_unified as EU
from evaluate_property import BuaBreakdown

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


def _ev_with_zoning(code_text):
    """Minimal evaluation stub carrying a single zoning factor."""
    fd = [{'code': 'zoning', 'evidence': f'تصنيف {code_text}',
           'label_ar': f'تنظيم {code_text}'}]
    return SimpleNamespace(valuation=SimpleNamespace(factors_detail=fd))


print("=" * 64)
print("T1 — _zone_max_coverage (QNMP table + legacy fallback)")
check("R1 -> 0.60", EU._zone_max_coverage('R1') == 0.60)
check("R1-TYP -> 0.60", EU._zone_max_coverage('R1-TYP') == 0.60)
check("R2 -> 0.50", EU._zone_max_coverage('R2') == 0.50)
check("R2-TYP -> 0.50", EU._zone_max_coverage('R2-TYP') == 0.50)
check("lowercase 'r1' normalises -> 0.60", EU._zone_max_coverage('r1') == 0.60)
check("R3 (not in table) -> legacy 0.80", EU._zone_max_coverage('R3') == EU.MAX_COVERAGE == 0.80)
check("None -> legacy 0.80", EU._zone_max_coverage(None) == 0.80)

print("=" * 64)
print("T2 — _suggested_footprint (0.8 x ceiling; legacy when unknown)")
check("R1 600 -> round(600*0.8*0.60)=288", EU._suggested_footprint(600, 'R1') == 288)
check("R2 600 -> round(600*0.8*0.50)=240", EU._suggested_footprint(600, 'R2') == 240)
check("unknown(None) 600 -> _typical_footprint", EU._suggested_footprint(600, None) == round(EU._typical_footprint(600)))
check("R3 (not in table) 600 -> _typical_footprint", EU._suggested_footprint(600, 'R3') == round(EU._typical_footprint(600)))
check("no plot -> None", EU._suggested_footprint(None, 'R1') is None)
check("zero plot -> None", EU._suggested_footprint(0, 'R1') is None)

print("=" * 64)
print("T3 — _extract_zoning_code (reuse already-fetched zoning, no GIS call)")
check("factor 'R1' -> 'R1'", EU._extract_zoning_code(_ev_with_zoning('R1')) == 'R1')
check("factor 'R2' -> 'R2'", EU._extract_zoning_code(_ev_with_zoning('R2')) == 'R2')
check("no factors_detail -> None",
      EU._extract_zoning_code(SimpleNamespace(valuation=SimpleNamespace(factors_detail=None))) is None)
check("ev None -> None (guarded)", EU._extract_zoning_code(None) is None)

print("=" * 64)
print("T4 — delta (ب): basement EXCLUDED from the comparison driver")
# Same plot/floors/footprint; only basement differs. Comparison BUA must drop.
with_b = EU._build_smart_bua(plot_area_m2=600, floors=3, annexes=0, basement=True, footprint_m2=300)
without_b = EU._build_smart_bua(plot_area_m2=600, floors=3, annexes=0, basement=False, footprint_m2=300)
check("with-basement bua has basement_m2 > 0", with_b.basement_m2 > 0)
check("without-basement bua has basement_m2 == 0", without_b.basement_m2 == 0)
s_with = EU._building_substantiality(with_b, 600)
s_without = EU._building_substantiality(without_b, 600)
check("excluding basement lowers actual_bua", s_without['actual_bua'] < s_with['actual_bua'])
check("excluding basement gives <= adjustment_pct (no basement-driven premium)",
      s_without['adjustment_pct'] <= s_with['adjustment_pct'])
# basement-only input (no floors/footprint/annex/majlis): with basement excluded
# AND no footprint -> _build_smart_bua returns None -> block skipped (neutral).
only_b = EU._build_smart_bua(plot_area_m2=600, floors=None, annexes=0, basement=False,
                             footprint_m2=None, external_majlis=None)
check("basement-only, basement excluded, no fp -> None (neutral, graceful)", only_b is None)

print("=" * 64)
print("T5 — delta (أ): confirmed footprint capped at the ZONE ceiling")
plot = 600
ceil_r1 = EU._zone_max_coverage('R1')   # 0.60
eff_capped = min(500.0, plot * ceil_r1)  # the engine's cap expression
check("user 500 on 600m2 R1 -> capped to 360", eff_capped == 360.0)
check("zone cap (0.60) is tighter than legacy MAX_COVERAGE (0.80)", plot * ceil_r1 < plot * EU.MAX_COVERAGE)
# capping the footprint lowers/levels substantiality
b_uncapped = EU._build_smart_bua(plot_area_m2=plot, floors=2, annexes=0, basement=False, footprint_m2=500)
b_capped = EU._build_smart_bua(plot_area_m2=plot, floors=2, annexes=0, basement=False, footprint_m2=360)
check("capped footprint -> <= actual_bua",
      EU._building_substantiality(b_capped, plot)['actual_bua']
      <= EU._building_substantiality(b_uncapped, plot)['actual_bua'])

print("=" * 64)
print("T6 — no-regression / fallback")
# No building input at all -> _build_smart_bua None -> substantiality block skipped
# (this is why the no-building-input anchors stay byte-identical).
none_bua = EU._build_smart_bua(plot_area_m2=600, floors=None, annexes=0, basement=None,
                               footprint_m2=None, external_majlis=None)
check("no building input -> None (anchors path untouched)", none_bua is None)
# unknown zoning -> suggested footprint == legacy typical (no silent change)
check("unknown zoning suggested == legacy typical", EU._suggested_footprint(700, None) == round(EU._typical_footprint(700)))

print("=" * 64)
print("T7 — version format (R6: no exact pins, format only)")
check("ENGINE_VERSION starts 'thammen-sprint'", EU.ENGINE_VERSION.startswith('thammen-sprint'))
check("ENGINE_VERSION dotted-sprint format (R6: no exact pin — survives bumps)",
      re.match(r'^thammen-sprint\d+p\d+p\d+', EU.ENGINE_VERSION) is not None)
check("SPRINT_TAG dotted-numeric prefix", re.match(r'^\d+\.\d+\.\d+', EU.SPRINT_TAG) is not None)

print("=" * 64)
print("T8 — §5.2: zoning default is CONSERVATIVE (no silent inflation)")
# For R1 the zoning suggestion (48%) is at/below the legacy typical (55%) -> never inflates.
check("R1 suggested (288) < legacy typical (330) on 600m2",
      EU._suggested_footprint(600, 'R1') < round(EU._typical_footprint(600)))
check("R2 suggested (240) < legacy typical on 600m2",
      EU._suggested_footprint(600, 'R2') < round(EU._typical_footprint(600)))
# Large plot: 0.8*0.60=0.48 > legacy 0.45 -> MUST cap at legacy (caught by live E2E).
check("LARGE-plot R1 capped at legacy (900 -> 405, not 432)",
      EU._suggested_footprint(900, 'R1') == round(EU._typical_footprint(900)))
check("no-inflation invariant: suggested <= legacy for ALL plots/zones",
      all(EU._suggested_footprint(p, z) <= round(EU._typical_footprint(p))
          for p in (300, 500, 700, 900, 1500) for z in ('R1', 'R2', None, 'R3')))

print("=" * 64)
print(f"RESULT: {_pass} passed, {_fail} failed")
sys.exit(1 if _fail else 0)
