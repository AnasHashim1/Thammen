#!/usr/bin/env python3
"""
Isolated logic tests — Sprint 2.22.0a.13 (thin-cell credibility).

Exercises the REAL production apply_moj_strategy (Rule #40 / E14) with hand-built
moj_reference dicts shaped exactly like moj_reference.build_reference output.

Mechanism under test (LOCKED): villa-only, per-cell 36mo-capped fallback as continuous
P2 shrinkage of the TOTAL-PRICE median toward the cell's OWN 36mo median, w=n24/(n24+10),
applied iff n24 >= 5 (refusal floor); tier on the 36mo fallback count; ppm² untouched;
range from the raw 24mo quartiles (gate-before-shrink).

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a13_thincell_credibility.py
"""
import sys
from evaluate_property import apply_moj_strategy, ASSET_TYPE_TO_MOJ_CATEGORY, _THINCELL_K, _THINCELL_FLOOR

VILLA_AT = next(k for k, v in ASSET_TYPE_TO_MOJ_CATEGORY.items() if v == 'villa')
LAND_AT = next((k for k, v in ASSET_TYPE_TO_MOJ_CATEGORY.items() if v == 'land'), None)
PLOT = 500.0          # -> bracket '400-600'
BK = '400-600'

_pass = 0
_fail = 0
def check(name, cond, detail=''):
    global _pass, _fail
    if cond:
        _pass += 1
        print(f'  PASS  {name}')
    else:
        _fail += 1
        print(f'  FAIL  {name}  {detail}')


def villa_ref(bracket_fields, cat_n=80):
    """Build a minimal moj_reference dict with one villa bracket."""
    return {
        'categories': {
            'villa': {
                'n': cat_n,
                'price_per_m2': {'median': 5000, 'p25': 4500, 'p75': 5500},
                'total_price': {'median': 2500000, 'p25': 2200000, 'p75': 2800000},
                'size_brackets': {BK: bracket_fields},
            }
        }
    }


def bracket(n, tpm, *, n24=None, n36=None, m24=None, m36=None,
            tp25=2200000, tp75=2800000, tp25_24=None, tp75_24=None):
    d = {
        'n': n,
        'price_per_m2_median': 5000, 'price_per_m2_p25': 4500, 'price_per_m2_p75': 5500,
        'total_price_median': tpm, 'total_price_p25': tp25, 'total_price_p75': tp75,
        'reliable': n >= 10,
    }
    if n24 is not None: d['n_24'] = n24
    if n36 is not None: d['n_36'] = n36
    if m24 is not None: d['total_price_median_24'] = m24
    if m36 is not None: d['total_price_median_36'] = m36
    if tp25_24 is not None: d['total_price_p25_24'] = tp25_24
    if tp75_24 is not None: d['total_price_p75_24'] = tp75_24
    return d


def has_cred(v):
    return any('thin-cell credibility' in s for s in (v.notes or []))


# ── Case 1: reliable cell (n24>=20) — blend applied, tier on n36, GENTLE move ──
ref = villa_ref(bracket(28, 2365000, n24=28, n36=37, m24=2365000, m36=2380000,
                        tp25_24=2200000, tp75_24=2500000))
v = apply_moj_strategy(VILLA_AT, PLOT, ref)
w = 28 / (28 + _THINCELL_K)
exp = round(w * 2365000 + (1 - w) * 2380000)
move = abs(v.moj_median_total - 2365000) / 2365000 * 100
check('C1 reliable: blended median', v.moj_median_total == exp, f'got {v.moj_median_total} exp {exp}')
check('C1 reliable: tier on n36', v.bracket_n == 37 and v.bracket_reliable is True, f'n={v.bracket_n} rel={v.bracket_reliable}')
check('C1 reliable: GENTLE move <1%', move < 1.0, f'move={move:.3f}%')
check('C1 reliable: cred note present', has_cred(v))

# ── Case 2: thin (5<=n24<20) with n36>=20 -> tier UPGRADES to reliable ──
ref = villa_ref(bracket(22, 1900000, n24=8, n36=22, m24=2000000, m36=1900000,
                        tp25_24=1800000, tp75_24=2200000))
v = apply_moj_strategy(VILLA_AT, PLOT, ref)
w = 8 / (8 + _THINCELL_K)
exp = round(w * 2000000 + (1 - w) * 1900000)
check('C2 thin->reliable: blended', v.moj_median_total == exp, f'got {v.moj_median_total} exp {exp}')
check('C2 thin->reliable: n36 tier + reliable', v.bracket_n == 22 and v.bracket_reliable is True)

# ── Case 3: thin with n36<20 -> blended, NOT reliable, n=n36 ──
ref = villa_ref(bracket(12, 2800000, n24=6, n36=12, m24=3000000, m36=2800000))
v = apply_moj_strategy(VILLA_AT, PLOT, ref)
w = 6 / (6 + _THINCELL_K)
exp = round(w * 3000000 + (1 - w) * 2800000)
check('C3 thin/n36<20: blended', v.moj_median_total == exp, f'got {v.moj_median_total} exp {exp}')
check('C3 thin/n36<20: n=n36, not reliable', v.bracket_n == 12 and v.bracket_reliable is False)

# ── Case 4: <5 FLOOR -> NO rescue (behaves as today; total_median unchanged) ──
ref = villa_ref(bracket(10, 4000000, n24=3, n36=10, m24=5000000, m36=4000000))
v = apply_moj_strategy(VILLA_AT, PLOT, ref)
check('C4 floor n24<5: NO blend (total_median = raw per-category)', v.moj_median_total == 4000000,
      f'got {v.moj_median_total}')
check('C4 floor n24<5: NO cred note', not has_cred(v))

# ── Case 5: non-villa (land) -> never shrunk ──
if LAND_AT:
    ref_land = {'categories': {'land': {'n': 80, 'price_per_m2': {'median': 3000, 'p25': 2700, 'p75': 3300},
                'total_price': {'median': 1500000, 'p25': 1300000, 'p75': 1700000},
                'size_brackets': {BK: bracket(15, 1500000, n24=15, n36=25, m24=1600000, m36=1400000)}}}}
    v = apply_moj_strategy(LAND_AT, PLOT, ref_land)
    check('C5 land: NO blend', v.moj_median_total == 1500000 and not has_cred(v), f'got {v.moj_median_total}')
else:
    check('C5 land mapping present', False, 'no land asset_type in ASSET_TYPE_TO_MOJ_CATEGORY')

# ── Case 6: villa but 36mo median missing -> defensive skip ──
ref = villa_ref(bracket(12, 2600000, n24=12, n36=0, m24=2600000, m36=None))
v = apply_moj_strategy(VILLA_AT, PLOT, ref)
check('C6 m36 missing: NO blend', v.moj_median_total == 2600000 and not has_cred(v), f'got {v.moj_median_total}')

# ── Case 7: backward-compat — bracket lacks the new fields entirely ──
ref = villa_ref(bracket(14, 2700000))   # no n_24/n_36/m24/m36
v = apply_moj_strategy(VILLA_AT, PLOT, ref)
check('C7 legacy dict: NO blend, byte-stable', v.moj_median_total == 2700000 and not has_cred(v),
      f'got {v.moj_median_total}')

# ── Case 8: range uses RAW 24mo quartiles when cred applied (gate-before-shrink) ──
ref = villa_ref(bracket(22, 1900000, n24=8, n36=22, m24=2000000, m36=1900000,
                        tp25=1750000, tp75=2300000, tp25_24=1800000, tp75_24=2200000))
v = apply_moj_strategy(VILLA_AT, PLOT, ref)
check('C8 range low = 24mo p25', v.estimated_value_low == 1800000, f'low={v.estimated_value_low}')
check('C8 range high = 24mo p75', v.estimated_value_high == 2200000, f'high={v.estimated_value_high}')
check('C8 median = blended (between low/high)',
      v.estimated_value_low <= v.estimated_value_median <= v.estimated_value_high,
      f'low={v.estimated_value_low} med={v.estimated_value_median} high={v.estimated_value_high}')

print(f'\n=== Sprint 2.22.0a.13 isolated: {_pass} passed, {_fail} failed (k={_THINCELL_K}, floor={_THINCELL_FLOOR}) ===')
sys.exit(1 if _fail else 0)
