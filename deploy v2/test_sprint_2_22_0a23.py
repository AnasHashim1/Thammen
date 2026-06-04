#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isolated logic tests — Sprint 2.22.0a.23 (R15): stock_strata land-median is a18-aware.

`stock_strata.compute_land_median` now pools areas with the a18 key (`moj_reference.area_match_key`
— strip trailing zone-number + hamza-fold), EXACTLY as `moj_reference.build_reference` and the B-1
value_floor do — instead of `_norm` exact, which dropped zone-number siblings (a narrower, ~+2-7%
HIGHER pool than the floor). Display-only / E4-classification; the HEADLINE value + the B-1
value_floor are untouched (value_floor reads moj_reference directly).

Per Rule #40 / E14: exercises the PRODUCTION `compute_land_median` + `area_match_key` on controlled
fixtures (so the a18 pooling is provable without GIS/network).

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0a23.py
"""
import sys

from stock_strata import compute_land_median
from moj_reference import area_match_key

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


DATE = '2025-12-01'
DCOL = 'تاريخ التثبيت'


def land(area, ppm2, am=500):
    return {'نوع العقار': 'أرض فضاء', 'اسم المنطقة': area,
            'سعر المتر المربع': str(ppm2), 'المساحة بالمتر المربع': str(am), DCOL: DATE}


# Fixture: a parent + its zone-number sibling (LOWER-priced) + a hamza variant + a non-sibling area.
ROWS = (
    [land('مريخ', p) for p in (3000, 3100, 3200)] +          # bare parent (higher)
    [land('مريخ 54', p) for p in (2600, 2700, 2650)] +       # zone-number sibling (lower) — was DROPPED
    [land('ام بشر', 4000), land('أم بشر', 4100), land('أم بشر', 4050)] +  # hamza variants (n>=3 floor)
    [land('الوكرة', p) for p in (9000, 9100, 9200, 9050, 9150)]  # unrelated area (must NOT pool)
)

# ── 1. a18 pools the zone-number sibling (the R15 fix) ──
r = compute_land_median(ROWS, {'مريخ'}, DCOL, plot_area_m2=500)
check('compute_land_median returns a dict', isinstance(r, dict) and r.get('median_per_m2'))
check('pooled n = 6 (parent 3 + sibling «مريخ 54» 3 — sibling no longer dropped)', r.get('n') == 6)
# median of [2600,2650,2700,3000,3100,3200] = (2700+3000)/2 = 2850
check('pooled median reflects the LOWER sibling (not the parent-only 3100)', r.get('median_per_m2') == 2850)
# legacy _norm-exact would have been n=3, median 3100 (parent only) → prove the move:
check('a18 pool is LOWER than the old parent-only pool (sibling-drop removed)',
      r.get('median_per_m2') < 3100)

# ── 2. hamza-fold pools «ام بشر» ↔ «أم بشر» ──
rh = compute_land_median(ROWS, {'أم بشر'}, DCOL, plot_area_m2=500)
check('hamza variants pool (n=3, median 4050)', rh and rh.get('n') == 3 and rh.get('median_per_m2') == 4050)
check('area_match_key folds hamza', area_match_key('أم بشر') == area_match_key('ام بشر'))
check('area_match_key strips trailing zone-number', area_match_key('مريخ 54') == area_match_key('مريخ'))

# ── 3. a NON-sibling area is NOT pooled (no over-merge) ──
rw = compute_land_median(ROWS, {'الوكرة'}, DCOL, plot_area_m2=500)
check('unrelated area stays isolated (n=5, median 9100)', rw and rw.get('n') == 5 and rw.get('median_per_m2') == 9100)
check('querying «مريخ» does NOT pull «الوكرة»', r.get('median_per_m2') < 5000)

# ── 4. matches moj_reference pooling key (consistency with the value_floor basis) ──
check('compute_land_median area key == moj_reference area_match_key',
      area_match_key('مريخ 54') == area_match_key('مريخ') == 'مريخ')

# ── 5. graceful: empty / unknown area → None (unchanged contract) ──
check('unknown area → None', compute_land_median(ROWS, {'منطقة غير موجودة'}, DCOL, plot_area_m2=500) is None)
check('no rows → None', compute_land_median([], {'مريخ'}, DCOL, plot_area_m2=500) is None)

print()
print(f'Sprint 2.22.0a.23 isolated: {_passed} passed, {_failed} failed')
sys.exit(0 if _failed == 0 else 1)
