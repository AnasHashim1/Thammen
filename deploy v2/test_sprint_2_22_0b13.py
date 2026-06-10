# Sprint 2.22.0b.13 (§20.9 GATED slice — Lever 1 convergent-TRIM + D-1 floor + ladder + cliff-flag).
# Exercises the PRODUCTION functions (E14 / Rule #40). Lever 2 (lift) DROPPED by the Phase-0 recon.
import sys, io, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import evaluate_unified as E
from evaluate_unified import (_cost_retention, _cost_approach_value, _cost_trim, _building_age_estimate,
                              COST_CONDITION_PENALTY, COST_DEFAULT_PENALTY, COST_RESIDUAL_FLOOR,
                              COST_RESIDUAL_FLOOR_LUX, COST_TRIM_NOTE_AR, COST_TRIM_NOTE_EN)

P = F = 0
def ck(c, n):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}")

V001_LAND, V001_FP = 2_456_736, 391     # recon-measured (GIS-stable)

# ── D-1 finish-keyed residual floor ──
ck(abs(_cost_retention(80, 'ordinary') - 0.27) < 1e-9, "floor: ordinary @80y -> 0.27")
ck(abs(_cost_retention(80, 'luxury') - 0.31) < 1e-9, "floor: luxury @80y -> 0.31 (D-1)")
ck(abs(_cost_retention(80, 'high') - 0.31) < 1e-9, "floor: high @80y -> 0.31 (D-1)")
ck(abs(_cost_retention(80, 'good') - 0.27) < 1e-9, "floor: good @80y -> 0.27 (good is NOT premium)")
ck(abs(_cost_retention(80) - 0.27) < 1e-9, "floor: default finish None @80y -> 0.27 (b11/b12 byte-identical)")
ck(abs(_cost_retention(25, 'luxury') - 0.50) < 1e-9, "lux floor does NOT bite at age 25 (ret 0.50 > 0.31)")
ck(_cost_retention(None) is None, "no age -> None")

# ── condition ladder (b13 §4.2) ──
ck(COST_CONDITION_PENALTY['excellent'] == -2, "ladder: excellent -2")
ck(COST_CONDITION_PENALTY['renovated'] == -3, "ladder: renovated -3")
ck(COST_CONDITION_PENALTY['new'] == 0, "ladder: new 0")
ck(COST_CONDITION_PENALTY['good'] == 5, "ladder: good +5 (unchanged)")
ck(COST_DEFAULT_PENALTY == 8, "ladder: default (average) +8 (no-condition flows byte-identical)")

# ── _cost_approach_value: ladder + finish applied (V001 actual-age, the trim cost) ──
c = _cost_approach_value(V001_LAND, V001_FP, 2, 'luxury', 25, 'excellent')
ck(c['effective_age'] == 23, f"V001 age25+excellent -> eff_age 23 (25-2) (got {c['effective_age']})")
ck(abs(c['retention'] - 0.54) < 1e-9, f"V001 eff23 -> retention 0.54 (got {c['retention']})")
ck(3_500_000 <= c['value'] <= 3_700_000, f"V001 +age25+lux+exc DRC ~3.6M valuer band (got {c['value']})")
# dilapidated-luxury floor BITES (eff_age high -> retention floored at 0.31 not 0.27)
cdl = _cost_approach_value(V001_LAND, V001_FP, 2, 'luxury', 40, 'poor')
ck(abs(cdl['retention'] - 0.31) < 1e-9, f"dilapidated-luxury (eff65) -> floor 0.31 (D-1) (got {cdl['retention']})")
cdo = _cost_approach_value(V001_LAND, V001_FP, 2, 'ordinary', 40, 'poor')
ck(abs(cdo['retention'] - 0.27) < 1e-9, f"dilapidated-ordinary (eff65) -> floor 0.27 (got {cdo['retention']})")

# ── _cost_trim predicate matrix ──
mkt = {'value': 3_700_000, 'method': 'comparison_widened', 'high': 3_700_000}
t = _cost_trim(mkt, c, V001_LAND, 'standalone_villa', False, 23)
ck(t and t['mode'] == 'cost_trim_convergent', "TRIM fires: old over-anchored widened, cost<market<=30%")
ck(t and t['amount'] == c['value'], "TRIM: the ACTUAL-age cost LEADS (amount == cost)")
ck(t and t['low'] == max(V001_LAND, c['value']) and t['high'] == 3_700_000, "TRIM range [max(land,cost) .. market]")
ck(t and 0 < t['undercut_pct'] <= 30, f"TRIM undercut in (0,30] (got {t and t['undercut_pct']})")
ck(_cost_trim({'value':3_700_000,'method':'comparison_bracket'}, c, V001_LAND, 'standalone_villa', False, 23) is None,
   "TRIM excluded: clean bracket")
ck(_cost_trim(mkt, c, V001_LAND, 'standalone_villa', True, 23) is None, "TRIM excluded: dispersion-gated")
ck(_cost_trim(mkt, c, 3_900_000, 'standalone_villa', False, 23) is None, "TRIM excluded: land-anchored (land>=market)")
ck(_cost_trim(mkt, c, V001_LAND, 'standalone_villa', False, 8) is None, "TRIM excluded: not old (eff_age<10)")
ck(_cost_trim(mkt, c, V001_LAND, 'apartment_building', False, 23) is None, "TRIM excluded: non-villa")
ck(_cost_trim(mkt, None, V001_LAND, 'standalone_villa', False, 23) is None, "TRIM fail-safe: cost None")
ck(_cost_trim(None, c, V001_LAND, 'standalone_villa', False, 23) is None, "TRIM fail-safe: primary None")
# cost ABOVE market -> not a trim (would be the dropped lift's zone)
cab = _cost_approach_value(V001_LAND, V001_FP, 3, 'luxury', 5, 'new')   # tall+new+luxury -> high cost
ck(_cost_trim({'value':2_000_000,'method':'comparison_thin'}, cab, V001_LAND, 'standalone_villa', False, 12) is None,
   "TRIM excluded: cost >= market (not a down-trim)")

# ── disjointness with cost_reanchor_down at exactly 30% ──
# cost = 1,000,000, market = 1,300,000 -> undercut EXACTLY 30% -> TRIM fires (<=30); reanchor is >30 only.
c30 = {'value': 1_000_000}
ck(_cost_trim({'value':1_300_000,'method':'comparison_thin'}, c30, 800_000, 'standalone_villa', False, 20) is not None,
   "disjoint @30%: undercut==30% -> TRIM fires (reanchor owns >30%)")
c31 = {'value': 1_000_000}
ck(_cost_trim({'value':1_310_000,'method':'comparison_thin'}, c31, 800_000, 'standalone_villa', False, 20) is None,
   "disjoint @31%: undercut>30% -> TRIM yields (that is cost_reanchor_down)")

# ── notes format ──
ck('سنة' in COST_TRIM_NOTE_AR.format(age=25, land='1', cost='2', comp='3'), "TRIM note AR formats")
ck('actual age' in COST_TRIM_NOTE_EN.format(age=25, land='1', cost='2', comp='3'), "TRIM note EN formats")

# ── cliff-flag R3 (value-invariant disclosure) ──
def ms(year): return (datetime.datetime(year, 6, 1) - datetime.datetime(1970, 1, 1)).total_seconds() * 1000.0
e09 = _building_age_estimate(ms(2009))
ck(e09 and e09['age_basis'] == 'vintage_capped' and e09.get('vintage_note_ar'), "cliff: 2009 survey (floor~17) -> vintage_capped + note")
e26 = _building_age_estimate(ms(2026))
ck(e26 and e26['age_basis'] == 'vintage_capped', "cliff: 2026 re-survey (floor<2) -> vintage_capped (inverse flag)")
e18 = _building_age_estimate(ms(2018))
ck(e18 and e18['age_basis'] == 'survey' and not e18.get('vintage_note_ar'), "cliff: 2018 survey (floor 8) -> 'survey', no note")
ck(_building_age_estimate(None) is None, "cliff: no surveyed_date -> None")

print(f"\n=== Sprint 2.22.0b.13 isolated: {P} passed, {F} failed ===")
sys.exit(1 if F else 0)
