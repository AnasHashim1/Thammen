#!/usr/bin/env python3
"""
Isolated logic tests — Sprint 2.22.0a.14 (vi): bracket honest-range + window disclosure.

Exercises the REAL production functions (Rule #40 / E14):
  (a) _stage1_dispersion_gate now fires for `comparison_bracket` on the cell's 36mo ppm² dispersion.
  (a) the application of the gate is unchanged (presentation-only; tested via the gate verdict).
  (b) apply_moj_strategy threads bracket_ppm2_dispersion + bracket_window_used (villa, cred only).
  (b) _select_primary_comparison appends « (نافذة 36 شهراً) » to source_ar + carries window_used + ppm2_dispersion.
  Anchors stay CLEAN (dispersion < 0.30 → not gated). <5 floor → no threading.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a14_bracket_honest_range.py
"""
import sys
from types import SimpleNamespace
from evaluate_unified import _stage1_dispersion_gate, _select_primary_comparison, STAGE1_DISPERSION_T, MIN_N_RELIABLE
from evaluate_property import apply_moj_strategy, ASSET_TYPE_TO_MOJ_CATEGORY, MoJValuation

VILLA_AT = next(k for k, v in ASSET_TYPE_TO_MOJ_CATEGORY.items() if v == 'villa')
PLOT, BK = 500.0, '400-600'
_pass = _fail = 0
def check(name, cond, detail=''):
    global _pass, _fail
    if cond: _pass += 1; print(f'  PASS  {name}')
    else: _fail += 1; print(f'  FAIL  {name}  {detail}')

# ── (a) GATE — comparison_bracket branch ──
g = _stage1_dispersion_gate({'method': 'comparison_bracket', 'ppm2_dispersion': 0.45}, None)
check('A1 bracket dispersed 0.45 -> gated', g and g['gated'] and g['dispersion'] == 0.45, str(g))
g = _stage1_dispersion_gate({'method': 'comparison_bracket', 'ppm2_dispersion': 0.208}, None)
check('A2 bracket ANCHOR-clean 0.208 -> NOT gated', g and not g['gated'], str(g))
g = _stage1_dispersion_gate({'method': 'comparison_bracket', 'ppm2_dispersion': 0.305}, None)
check('A3 boundary 0.305 -> gated (>=0.30)', g and g['gated'], str(g))
g = _stage1_dispersion_gate({'method': 'comparison_bracket', 'ppm2_dispersion': None}, None)
check('A4 bracket no dispersion -> None (cant gate)', g is None, str(g))
g = _stage1_dispersion_gate({'method': 'comparison_thin', 'ppm2_dispersion': 0.9}, None)
check('A5 non-Case1 method -> None', g is None, str(g))
# widened path regression (still works off geo_v2)
g = _stage1_dispersion_gate({'method': 'comparison_widened'}, {'p25_m2': 400, 'p75_m2': 700, 'weighted_median_m2': 500})
check('A6 widened regression -> gated (0.6)', g and g['gated'] and g['dispersion'] == 0.6, str(g))
check('A7 threshold is 0.30', STAGE1_DISPERSION_T == 0.30)

# ── (b) apply_moj_strategy threads dispersion + window split (villa, cred) ──
def villa_ref(bd, cat_n=80):
    return {'categories': {'villa': {'n': cat_n,
            'price_per_m2': {'median': 5000, 'p25': 4500, 'p75': 5500},
            'total_price': {'median': 2500000, 'p25': 2200000, 'p75': 2800000},
            'size_brackets': {BK: bd}}}}
def bracket(n, *, n24, n36, m24, m36, disp36):
    return {'n': n, 'price_per_m2_median': 5000, 'price_per_m2_p25': 4500, 'price_per_m2_p75': 5500,
            'total_price_median': m36, 'total_price_p25': 2200000, 'total_price_p75': 2800000, 'reliable': n >= 10,
            'n_24': n24, 'n_36': n36, 'total_price_median_24': m24, 'total_price_median_36': m36,
            'total_price_p25_24': 2150000, 'total_price_p75_24': 2550000, 'ppm2_dispersion_36': disp36}

v = apply_moj_strategy(VILLA_AT, PLOT, villa_ref(bracket(22, n24=18, n36=22, m24=2000000, m36=1950000, disp36=0.45)))
check('B1 dispersion threaded', v.bracket_ppm2_dispersion == 0.45, str(v.bracket_ppm2_dispersion))
check('B2 window split string present', v.bracket_window_used and '24' in v.bracket_window_used and 'منها' in v.bracket_window_used, repr(v.bracket_window_used))
check('B3 reliable on n36', v.bracket_n == 22 and v.bracket_reliable is True)

# <5 floor → NO threading
v = apply_moj_strategy(VILLA_AT, PLOT, villa_ref(bracket(8, n24=3, n36=8, m24=2000000, m36=1950000, disp36=0.45)))
check('B4 <5 floor: NO dispersion threaded', v.bracket_ppm2_dispersion is None, str(v.bracket_ppm2_dispersion))
check('B5 <5 floor: NO window string', v.bracket_window_used is None, repr(v.bracket_window_used))

# ── (b) _select_primary_comparison: window suffix on source_ar + carries fields ──
def fake_ev(disp, win):
    mv = MoJValuation(strategy='t', moj_category='villa', size_bracket=BK, bracket_n=37, bracket_reliable=True,
                      moj_median_per_m2=5000, moj_median_total=2400000, estimated_value_low=2200000,
                      estimated_value_median=2400000, estimated_value_high=2600000,
                      bracket_ppm2_dispersion=disp, bracket_window_used=win)
    return SimpleNamespace(valuation=mv)

p = _select_primary_comparison(fake_ev(0.45, '37 معاملة، منها 28 خلال 24 شهراً'), {})
check('B6 Case1 comparison_bracket', p and p['method'] == 'comparison_bracket', str(p and p.get('method')))
check('B7 source_ar has « صفقات آخر 36 شهراً »', p and 'صفقات آخر 36 شهراً' in p['source_ar'], p and p.get('source_ar'))  # b105 R6: «نافذة»→«صفقات آخر»
check('B8 window_used carried', p and p.get('window_used') and 'منها' in p['window_used'])
check('B9 ppm2_dispersion carried (-> gate)', p and p.get('ppm2_dispersion') == 0.45)
# the carried dispersion feeds the gate end-to-end
g = _stage1_dispersion_gate(p, {})
check('B10 end-to-end: dispersed bracket gated', g and g['gated'], str(g))

# pure-24mo (window None) → NO suffix, anchor stays clean (disp 0.208)
p = _select_primary_comparison(fake_ev(0.208, None), {})
check('B11 no-window: source_ar UNCHANGED (no suffix)', p and 'نافذة' not in p['source_ar'], p and p.get('source_ar'))
check('B12 anchor clean: gate NOT fired (0.208<0.30)', not (_stage1_dispersion_gate(p, {}) or {}).get('gated'))

print(f'\n=== Sprint 2.22.0a.14 (vi) isolated: {_pass} passed, {_fail} failed ===')
sys.exit(1 if _fail else 0)
