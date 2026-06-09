# Sprint 2.22.0b.11 (§20.9) — Cost-Approach (DRC) DOWN-re-anchor isolated tests.
# Exercises the PRODUCTION functions `_cost_approach_value` + `_cost_triangulation`
# + the constants (Rule #40 / E14). Verifies: the §2/§5 DRC model (RCN ladder ×
# straight-line retention × BUA via the b10 footprint + built-ratio); the §3 DOWN-
# re-anchor trigger (the V001/Marikh >30% separator); the SYSTEM-age IMMUNITY (b9
# system age 17 protects V001; the actual ~25 would wrongly fire); the age-gate (B);
# the dispersion-gate + clean-bracket + over-anchor exclusions; the built-ratio ±20%
# sensitivity (recon C — does NOT flip V001); the residual-floor clamp; and the
# value-invariance contract (apartment/land/no-age → None; pure, no mutation).
import sys
sys.stdout.reconfigure(encoding='utf-8')
from evaluate_unified import (
    _cost_approach_value, _cost_triangulation, _cost_retention,
    COST_RCN_BY_FINISH, COST_RCN_DEFAULT, COST_ECONOMIC_LIFE_Y, COST_RESIDUAL_FLOOR,
    COST_BUILT_RATIO, COST_DEFAULT_FLOORS, COST_DEFAULT_PENALTY,
    COST_REANCHOR_UNDERCUT_T, COST_REANCHOR_MIN_AGE_Y, _COST_REANCHOR_METHODS,
)

_pass = 0
_fail = 0
def check(cond, msg):
    global _pass, _fail
    if cond:
        _pass += 1
    else:
        _fail += 1
        print(f'  FAIL: {msg}')

# Live recon anchors (from the b10.2 /api/health probe, 2026-06-09):
MARIKH = dict(land=1_851_260, fp=311, age=17, market=5_400_000, high=5_500_000)  # comparison_thin
V001   = dict(land=2_456_736, fp=391, age=17, market=3_800_000, high=3_800_000)  # comparison_widened
ABU    = dict(land=1_700_100, fp=270, age=15, market=2_400_000)                  # comparison_bracket (clean)

def cost_default(d, age=None, finish='ordinary', condition=None, floors=None):
    """DRC cost on the no-input defaults (ordinary + average), b10 footprint × built-ratio."""
    return _cost_approach_value(d['land'], d['fp'], floors, finish,
                                d['age'] if age is None else age, condition)

# ══════════════════════════════════════════════════════════════════
# 1. LOCKED params (the bank-calibrated ladder + curve)
# ══════════════════════════════════════════════════════════════════
check(COST_RCN_BY_FINISH['ordinary'] == 2200 and COST_RCN_BY_FINISH['luxury'] == 3500
      and COST_RCN_BY_FINISH['shell'] == 1200, 'RCN ladder: shell 1200 / ordinary 2200 / luxury 3500')
check(COST_RCN_DEFAULT == 2200, 'default finish RCN = ordinary 2200')
check(COST_ECONOMIC_LIFE_Y == 50, 'economic life 50y')
check(abs(COST_RESIDUAL_FLOOR - 0.27) < 1e-9, 'residual floor 0.27')
check(abs(COST_BUILT_RATIO - 0.77) < 1e-9, 'built-ratio 0.77 (V001 602/782)')
check(COST_DEFAULT_FLOORS == 2 and COST_DEFAULT_PENALTY == 8, 'defaults G+1 / average penalty +8')
check(abs(COST_REANCHOR_UNDERCUT_T - 0.30) < 1e-9, 'undercut threshold 30%')
check(COST_REANCHOR_MIN_AGE_Y == 10, 'age-gate 10y (old stock only)')

# ══════════════════════════════════════════════════════════════════
# 2. retention curve (straight-line, condition-modulated, clamped)
# ══════════════════════════════════════════════════════════════════
check(abs(_cost_retention(25) - 0.50) < 1e-9, 'eff age 25 → retention 0.50')   # Marikh/V001 default
check(abs(_cost_retention(0) - 0.98) < 1e-9, 'eff age 0 → clamped to 0.98 ceiling')
check(abs(_cost_retention(80) - 0.27) < 1e-9, 'eff age 80 → clamped to 0.27 floor')
check(_cost_retention(None) is None, 'no age → retention None')

# ══════════════════════════════════════════════════════════════════
# 3. §2/§5 DRC model — reproduces the recon hand-calc on the live anchors
# ══════════════════════════════════════════════════════════════════
cm = cost_default(MARIKH)
# land 1.851M + (311×0.77×2=479 BUA × 2200 × retention(17+8=25 → 0.50)) ≈ 2.38M
check(2_300_000 <= cm['value'] <= 2_450_000, f'Marikh DRC cost ~2.38M (got {cm["value"]})')
check(cm['bua_m2'] == round(311 * 0.77 * 2), f'Marikh BUA = 311×0.77×2 = 479 (got {cm["bua_m2"]})')
check(cm['rcn_qar_per_m2'] == 2200 and cm['effective_age'] == 25 and cm['retention'] == 0.5,
      'Marikh: ordinary 2200 / eff-age 25 / retention 0.50')
cv = cost_default(V001)
# land 2.457M + (391×0.77×2=602 BUA × 2200 × 0.50) ≈ 3.12M
check(3_050_000 <= cv['value'] <= 3_200_000, f'V001 DRC cost (default, system age) ~3.12M (got {cv["value"]})')
check(cv['bua_m2'] == round(391 * 0.77 * 2), f'V001 BUA = 391×0.77×2 = 602 (matches the valuer BUA) (got {cv["bua_m2"]})')
# the built-ratio 0.77 calibrates EXACTLY on V001: 391×2 = 782 max → ×0.77 = 602 actual
check(round(391 * 2 * COST_BUILT_RATIO) == 602, 'built-ratio 0.77 reproduces V001 actual BUA 602 from max 782')
# luxury input → higher RCN → higher cost (toward the valuer 3.6M)
cvl = cost_default(V001, finish='luxury', condition='excellent')
check(cvl['rcn_qar_per_m2'] == 3500 and cvl['effective_age'] == 17 and cvl['value'] > cv['value'],
      'V001 luxury+excellent → RCN 3500 / no penalty / cost > default-ordinary')

# ══════════════════════════════════════════════════════════════════
# 4. §3 DOWN-re-anchor — Marikh FIRES, V001 does NOT (the >30% separator)
# ══════════════════════════════════════════════════════════════════
p_marikh = {'value': MARIKH['market'], 'method': 'comparison_thin', 'high': MARIKH['high']}
ct_m = _cost_triangulation(p_marikh, cm, MARIKH['land'], 'standalone_villa', False, MARIKH['age'])
check(ct_m and ct_m['mode'] == 'cost_reanchor_down', 'Marikh: cost down-re-anchor FIRES')
check(ct_m and ct_m['undercut_pct'] > 100, f'Marikh undercut ≫ 30% (got {ct_m and ct_m.get("undercut_pct")}%)')
# the NEW floor = the cost (informed), REPLACING §6 widen_down's bare land
check(ct_m and ct_m['low'] == max(MARIKH['land'], cm['value']) == cm['value'],
      f'Marikh new floor = cost {cm["value"]} (raised from bare land {MARIKH["land"]})')
check(ct_m and ct_m['low'] > MARIKH['land'], 'Marikh floor RISES above bare land (the §20.9 contribution)')
check(ct_m and ct_m['high'] == MARIKH['high'], 'Marikh high = market (muted via range_is_headline)')

p_v001 = {'value': V001['market'], 'method': 'comparison_widened', 'high': V001['high']}
ct_v = _cost_triangulation(p_v001, cv, V001['land'], 'standalone_villa', False, V001['age'])
check(ct_v is None, 'V001: does NOT down-re-anchor (cost +22% < 30% — convergent, protected)')

# ══════════════════════════════════════════════════════════════════
# 5. 🔴 SYSTEM-AGE IMMUNITY — the decisive ship-now safety property
#    b9 system age (17) → V001 no-fire (correct); ACTUAL (25) → would WRONGLY fire.
# ══════════════════════════════════════════════════════════════════
cv_actual = cost_default(V001, age=25)   # the ACTUAL age (re-registration zeros the survey date)
check(2_850_000 <= cv_actual['value'] <= 2_960_000, f'V001 at ACTUAL age 25 → cost ~2.91M (got {cv_actual["value"]})')
ct_v_actual = _cost_triangulation(p_v001, cv_actual, V001['land'], 'standalone_villa', False, 25)
check(ct_v_actual is not None, 'V001 at the ACTUAL age 25 → undercut +30.6% > 30% → WOULD fire (the bias)')
check(ct_v is None and ct_v_actual is not None,
      'IMMUNITY: system age 17 protects V001 (no fire); actual 25 would fire → ship-now MUST use system age')
# the lower (system) age is conservative: higher cost → higher floor → less aggressive
check(cv['value'] > cv_actual['value'], 'system age → higher cost than actual age (conservative for the down-move)')

# ══════════════════════════════════════════════════════════════════
# 6. age-gate (B) — OLD stock only (closes the new-luxury mis-launch)
# ══════════════════════════════════════════════════════════════════
cm_new = cost_default(MARIKH, age=3, condition='new')
ct_new = _cost_triangulation({'value': 5_400_000, 'method': 'comparison_thin', 'high': 5_500_000},
                             cm_new, MARIKH['land'], 'standalone_villa', False, 3)
check(ct_new is None, 'age 3 (< 10) → down-re-anchor does NOT fire (age-gate)')
# at the gate boundary: 9y → no, 10y → eligible
check(_cost_triangulation(p_marikh, cm, MARIKH['land'], 'standalone_villa', False, 9) is None,
      'age 9 → below the gate → no fire')
check(_cost_triangulation(p_marikh, cm, MARIKH['land'], 'standalone_villa', False, 10) is not None,
      'age 10 → at the gate → eligible')

# ══════════════════════════════════════════════════════════════════
# 7. exclusions — clean bracket, dispersion-gated, not-over-anchored, asset type
# ══════════════════════════════════════════════════════════════════
check(_cost_triangulation({'value': 2_400_000, 'method': 'comparison_bracket', 'high': 2_600_000},
                          cost_default(ABU), ABU['land'], 'standalone_villa', False, ABU['age']) is None,
      'clean comparison_bracket → NOT in re-anchor methods → no fire (Abu Hamour untouched)')
check(_cost_triangulation(p_marikh, cm, MARIKH['land'], 'standalone_villa', True, MARIKH['age']) is None,
      'dispersion-gated (a10/a14 own it) → no fire')
check(_cost_triangulation({'value': 1_700_000, 'method': 'comparison_thin', 'high': 2_000_000},
                          cost_default(MARIKH), 1_851_260, 'standalone_villa', False, MARIKH['age']) is None,
      'land_floor ≥ market (not over-anchored) → no fire')
check(_cost_triangulation(p_marikh, cm, MARIKH['land'], 'apartment_building', False, MARIKH['age']) is None,
      'apartment → no fire (villa/house only)')
for m in _COST_REANCHOR_METHODS:
    check(m in ('comparison_thin', 'comparison_widened', 'comparison_widened_indicative', 'comparison_preliminary'),
          f're-anchor method {m} is thin/widened/preliminary (never clean bracket)')

# ══════════════════════════════════════════════════════════════════
# 8. built-ratio ±20% sensitivity (recon C) — does NOT flip V001's no-fire
# ══════════════════════════════════════════════════════════════════
for ratio, label in [(0.616, '-20%'), (0.77, 'realistic'), (0.924, '+20%')]:
    # inject the BUA via footprint_actual = max-footprint × ratio (× floors inside)
    cvr = _cost_approach_value(V001['land'], None, 2, 'ordinary', V001['age'], None,
                               footprint_actual=V001['fp'] * ratio)
    ctr = _cost_triangulation(p_v001, cvr, V001['land'], 'standalone_villa', False, V001['age'])
    check(ctr is None, f'V001 built-ratio {label} ({ratio}) → cost {cvr["value"]} → STILL does not fire (≤30%)')
# Marikh fires across the whole band (robust)
for ratio in (0.616, 0.77, 0.924):
    cmr = _cost_approach_value(MARIKH['land'], None, 2, 'ordinary', MARIKH['age'], None,
                               footprint_actual=MARIKH['fp'] * ratio)
    check(_cost_triangulation(p_marikh, cmr, MARIKH['land'], 'standalone_villa', False, MARIKH['age']) is not None,
          f'Marikh built-ratio {ratio} → fires (robust)')

# ══════════════════════════════════════════════════════════════════
# 9. value-invariance / no-input guards (pure, never fabricate)
# ══════════════════════════════════════════════════════════════════
check(_cost_approach_value(MARIKH['land'], MARIKH['fp'], None, 'ordinary', None, None) is None,
      'no age → cost None (→ no down-re-anchor; depreciation needs an age)')
check(_cost_approach_value(0, 311, None, 'ordinary', 17, None) is None, 'no land floor → None')
check(_cost_approach_value(1_851_260, None, None, 'ordinary', 17, None) is None, 'no footprint → None')
check(_cost_triangulation(p_marikh, None, MARIKH['land'], 'standalone_villa', False, 17) is None,
      'no cost dict → no fire')
# confirmed footprint path: footprint_actual = actual ground area (no built-ratio)
cc = _cost_approach_value(MARIKH['land'], 311, 2, 'ordinary', 17, None, footprint_actual=300)
check(cc and cc['bua_m2'] == 600 and cc['built_ratio'] is None,
      'confirmed footprint 300 × 2 floors = 600 BUA, built_ratio None (actual, no estimate)')
# pure: calling does not raise on odd input
check(_cost_approach_value(None, None, None, None, None, None) is None, 'all-None → None (no raise)')

print(f'\n2.22.0b.11 (§20.9 cost-DRC down-re-anchor) isolated: {_pass} passed, {_fail} failed')
sys.exit(1 if _fail else 0)
