# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.18 — isolated tests (signed directive §E: >=18).
AGE-BASIS demotion (A1) + LUXURY-EXIT finish-delta (A2/C-ii) + TD-93317 recalibration (B).
Production functions + source pins (Rule #40 / E14). Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b18.py
"""
import io, re, sys
sys.stdout.reconfigure(encoding='utf-8')

from evaluate_unified import (_old_stock_reanchor, _cost_retention, _age_quality_adj,
                              _cost_approach_value, COST_RCN_BY_FINISH, COST_RCN_DEFAULT,
                              COST_BUILT_RATIO, AGE_SENSITIVITY_NOTE_AR, AGE_SENSITIVITY_NOTE_EN,
                              ENGINE_VERSION, SPRINT_TAG)

SRC = io.open('evaluate_unified.py', encoding='utf-8').read()
HTML = io.open('index.html', encoding='utf-8').read()
PASS = []
FAIL = []

def chk(name, cond):
    (PASS if cond else FAIL).append(name)
    print(('PASS  ' if cond else 'FAIL  ') + name)

# ── shared synthetic inputs (the Marikh shape, PHASE0_b18 §3) ──
PRIM = {'value': 5400000, 'method': 'comparison_thin'}
SGF = {'value_full': 3412571, 'ppm2_median_full': 5567, 'n_full': 51}
COST = {'value': 2378094}
ARGS = dict(primary=PRIM, sgf=SGF, aging_cell={}, cost=COST, land_floor=1851260,
            asset_type='standalone_villa', dispersion_gated=False, age=17,
            age_basis='vintage_capped', dom_name='luxury_new', dom_share=51.7,
            plot_area_m2=613, user_premium=False)

# 1-2: plain fire unchanged (b16 byte-behavior — no finish → no delta)
r = _old_stock_reanchor(**ARGS)
chk('1. plain OSR fires (amount == the geo-full basis 3,412,571)', r and r['amount'] == 3412571)
chk('2. plain OSR: finish_delta == 0 and finish is None', r and r['finish_delta'] == 0 and r['finish'] is None)

# 3-5: luxury finish-delta (A2 / C-ii) — delta = (3500-2200) x ret_raw(17,lux) x bua
bua = 479
ret = _cost_retention(17, 'luxury')
exp_delta = round((3500 - 2200) * ret * bua)
r = _old_stock_reanchor(**{**ARGS, 'finish': 'luxury', 'finish_age': 17, 'finish_bua': bua})
chk('3. lux lead = plain + delta', r and r['amount'] == 3412571 + exp_delta)
chk('4. finish_delta exported + finish=luxury', r and r['finish_delta'] == exp_delta and r['finish'] == 'luxury')
chk('5. monotonic: plain <= lux lead <= thin median', r and 3412571 <= r['amount'] <= 5400000)

# 6: high finish uses RCN 3000
r = _old_stock_reanchor(**{**ARGS, 'finish': 'high', 'finish_age': 17, 'finish_bua': bua})
chk('6. high-finish delta uses RCN_high 3000', r and r['finish_delta'] == round((3000 - 2200) * _cost_retention(17, 'high') * bua))

# 7: the HARD RAIL — delta clamps at the raw thin median
r = _old_stock_reanchor(**{**ARGS, 'finish': 'luxury', 'finish_age': 17, 'finish_bua': 5000})
chk('7. rail: oversized delta clamps at the thin median', r and r['amount'] == 5400000)

# 8: delta incomputable (no BUA) → conservative abstain (pre-b18 behavior)
r = _old_stock_reanchor(**{**ARGS, 'finish': 'luxury', 'finish_age': 17, 'finish_bua': None})
chk('8. luxury without a computable delta → abstain (None)', r is None)

# 9: new/renovated still abstain via user_premium
r = _old_stock_reanchor(**{**ARGS, 'user_premium': True})
chk('9. user_premium (new/renovated) still abstains', r is None)

# 10: margin gate still decided on the PLAIN candidate (converged plain → abstain even with finish)
r = _old_stock_reanchor(**{**ARGS, 'sgf': {'value_full': 4600000, 'ppm2_median_full': 1, 'n_full': 51},
                           'finish': 'luxury', 'finish_age': 17, 'finish_bua': bua})
chk('10. converged plain (margin<=20%) abstains regardless of finish', r is None)

# 11-12: D-1 floor keying + the TD-93317 retention point
chk('11. 0.31 lux/high floor keying (age 40: lux 0.31 vs default 0.27)',
    _cost_retention(40, 'luxury') == 0.31 and _cost_retention(40, None) == 0.27)
chk('12. _cost_retention(18, high) == 0.64 (TD-93317: net 1,900/3,000)', _cost_retention(18, 'high') == 0.64)

# 13: the §B sheet reproduction (mandatory): land 2,456,736 + 3000 x 0.64 x (391 x 0.77 x 2) vs 3,600,145 ±1%
sheet = 2456736 + 3000 * _cost_retention(18, 'high') * (391 * COST_BUILT_RATIO * 2)
chk('13. TD-93317 sheet reproduced within ±1% (raw system age 18, high)',
    abs(sheet - 3600145) / 3600145 <= 0.01)

# 14-15: A1 — the a9 user-age exclusion in _age_quality_adj
class _V:  # minimal valuation stub with factors_detail
    factors_detail = [{'code': 'building_age', 'weight': -0.02},
                      {'code': 'plot_shape', 'weight': 0.01},
                      {'code': 'location', 'weight': 0.05}]
chk('14. _age_quality_adj default keeps building_age (-0.02 + 0.01)', _age_quality_adj(_V()) == -0.01)
chk('15. exclude_user_age drops building_age, keeps plot_shape', _age_quality_adj(_V(), exclude_user_age=True) == 0.01)

# 16-18: source pins — the trim LEAD branch is GONE; the sensitivity attach exists; the call threads age_source
chk('16. the elif _ct_trim LEAD branch is REMOVED from the chain', "elif _ct_trim:" not in SRC)
chk('17. age_sensitivity attaches after the chain (A1 demotion)',
    "output['valuation']['age_sensitivity']" in SRC and 'AGE_SENSITIVITY_NOTE_AR.format' in SRC)
chk('18. _select_primary_comparison threads user_age=(age_source==user)',
    re.search(r"_select_primary_comparison\(ev,\s*geo_v2_result,\s*\n?\s*user_age=\(age_source == 'user'\)\)", SRC) is not None)

# 19: the verbatim sensitivity core (signed directive A1)
chk('19. sensitivity note carries the verbatim core',
    AGE_SENSITIVITY_NOTE_AR.startswith('حساسية العمر: لو كان العمر الفعلي {n} سنة ≈ {x}')
    and 'system-documented age' in AGE_SENSITIVITY_NOTE_EN)

# 20-21: Case-A + 10-Year rewords promise the delta pricing, not the pool jump
chk('20. Case-A line re-worded (delta pricing promise)',
    'اختر «بناء فاخر» — يُسعَّر التشطيب عبر فرق كلفة الإحلال' in SRC
    and 'اختر «بناء فاخر» وأعد التقدير.' not in SRC)
chk('21. 10-Year disclosure re-worded',
    'يُسعَّر التشطيب عندها عبر فرق كلفة الإحلال (مُعامل البناء)' in SRC)

# 22: the b4 new-luxury lever untouched (source pin: its wiring guard intact)
chk('22. b4 new+luxury lever wiring intact', "luxury_new_premium" in SRC and 'teardown' in SRC)

# 23-24: index.html renders the sensitivity line on screen 4 (TIER-1) + the report
chk('23. screen-4 renders age_sensitivity.note_ar (b52: in the «كيف وصلنا» fold, was TIER-1)',
    "v.age_sensitivity&&v.age_sensitivity.note_ar){how+=" in HTML)
chk('24. the report renders age_sensitivity.note_ar',
    "v.age_sensitivity&&v.age_sensitivity.note_ar)h+=" in HTML)

# 25 (SUPERSEDED by Sprint 2.22.0b.20): the OSR finish-delta emission retired with the OSR
# branch — finish now prices THROUGH the replacement coefficient (RCN luxury) inside the
# gate's cost figure (same E26/b18 doctrine, more direct). Pin = the RCN path + the pure fn kept.
chk('25. finish prices through the RCN coefficient (gate cost) + OSR calculator kept',
    "('luxury' if is_luxury else 'ordinary')" in SRC and 'def _old_stock_reanchor(' in SRC)

# 26: version format (R6 — no exact pin)
chk('26. ENGINE/SPRINT_TAG format', ENGINE_VERSION.startswith('thammen-sprint') and re.match(r'^\d+\.\d+\.\d+', SPRINT_TAG) is not None)

print(f'\n==== {len(PASS)}/{len(PASS)+len(FAIL)} PASS ====')
sys.exit(1 if FAIL else 0)
