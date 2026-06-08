# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.7 (§6 v2) — cross-bracket yield-borrowing isolated tests.

Exercises the PRODUCTION functions (E14 / Rule #40 — the real engine, not replicas):
  - evaluate_unified._lookup_calibrated_cap_rate  (borrows the area's usable cell
    from an adjacent bracket when the subject's exact plot bracket has none; against
    the LIVE cap_rates.sqlite)
  - evaluate_unified._income_triangulation        (a borrowed yield forces MUC high
    + carries bracket_borrowed / borrowed_from_bracket)

Recon: PHASE0_R7_income_v2_600-900_recon — 600-900 villa yield cells are not
data-feasible (0/187 usable); borrowing the area's 400-600 usable cell is the
data-feasible lever that lets a 600-900 subject income-LEAD once a rent exists.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b7.py
"""
import sys
from evaluate_unified import (_lookup_calibrated_cap_rate as LOOK,
                              _income_triangulation as TRI)

_pass = _fail = 0
def check(name, cond):
    global _pass, _fail
    if cond:
        _pass += 1; print(f"  PASS  {name}")
    else:
        _fail += 1; print(f"  FAIL  {name}")

print("Sprint 2.22.0b.7 §6 v2 cross-bracket yield-borrowing\n")

# ── 1) EXACT bracket — byte-identical to the pre-v2 path (no borrow flag) ──
rate, prov = LOOK('standalone_villa', 'امريخ الجنوبي', 500)   # 400-600 has a reliable cell
check("1 exact 400-600 returns calibrated reliable", rate and prov['confidence'] == 'reliable')
check("1 exact path sets NO bracket_borrowed key", prov is not None and 'bracket_borrowed' not in prov)
check("1 exact cap == the area's 400-600 net yield 5.155%", rate is not None and abs(rate - 0.05155) < 1e-6)

# ── 2) BORROW — 600-900 subject borrows the area's 400-600 usable cell ──
rate2, prov2 = LOOK('standalone_villa', 'امريخ الجنوبي', 700)  # 600-900 has NO usable cell
check("2 Marikh 600-900 still returns a calibrated rate (borrowed)", rate2 is not None)
check("2 flag bracket_borrowed=True", bool(prov2 and prov2.get('bracket_borrowed')))
check("2 borrowed_from_bracket == 400-600", prov2 and prov2.get('borrowed_from_bracket') == '400-600')
check("2 subject_bracket == 600-900", prov2 and prov2.get('subject_bracket') == '600-900')
check("2 borrowed rate == the 400-600 reliable rate (same area)", rate2 is not None and abs(rate2 - 0.05155) < 1e-6)
check("2 confidence still reliable (the borrowed cell's)", prov2 and prov2.get('confidence') == 'reliable')
check("2 method_ar discloses the borrow", prov2 and 'مُستعار' in prov2.get('method_ar', ''))

# ── 3) BORROW — المعمورة (bare + zone-numbered both resolve to the 400-600 cell) ──
r3a, p3a = LOOK('standalone_villa', 'المعمورة 56', 700)
r3b, p3b = LOOK('standalone_villa', 'المعمورة', 652)
check("3 المعمورة 56 600-900 borrows 400-600", p3a and p3a.get('bracket_borrowed') and p3a.get('borrowed_from_bracket') == '400-600')
check("3 bare المعمورة 600-900 borrows the same cell (token match)", r3b is not None and abs(r3b - (r3a or 0)) < 1e-9)

# ── 4) No usable cell in the area → still None (borrowing cannot invent one) ──
r4, p4 = LOOK('standalone_villa', 'الخرايج', 700)     # area has only fallback cells
check("4 area with no usable cell -> None", r4 is None and p4 is None)
r5, p5 = LOOK('standalone_villa', 'منطقة-غير-موجودة', 700)
check("4 unknown area -> None", r5 is None and p5 is None)

# ── 5) bracket with no plot area / non-calibratable asset → None (unchanged) ──
check("5 no plot area -> None", LOOK('standalone_villa', 'امريخ الجنوبي', None) == (None, None))
check("5 non-calibratable asset (raw_land) -> None", LOOK('raw_land', 'امريخ الجنوبي', 700) == (None, None))

# ── 6) _income_triangulation: a BORROWED yield forces MUC high even on a small spread ──
def income(value, prov):
    return {'value': value, 'rent_source': 'actual_provided', 'cap_rate': 0.05155,
            'annual_rent': 190_000, 'cap_rate_provenance': prov}
P_BRACK = {'value': 2_970_000, 'method': 'comparison_bracket', 'high': 3_100_000}
prov_borrow = {'source': 'calibrated', 'confidence': 'reliable', 'net_yield_pct': 5.16,
               'sample_size': 46, 'bracket_borrowed': True, 'borrowed_from_bracket': '400-600'}
prov_exact  = {'source': 'calibrated', 'confidence': 'reliable', 'net_yield_pct': 5.16,
               'sample_size': 46}
# income 2.7M vs comp 2.97M = small spread (~9%) → would be 'moderate' if not borrowed
t_b = TRI(P_BRACK, income(2_700_000, prov_borrow), None, 1_800_000, 'standalone_villa')
check("6 borrowed income_led fires", t_b and t_b['mode'] == 'income_led')
check("6 borrowed → MUC forced high (small spread)", t_b and t_b['muc_level'] == 'high')
check("6 carries bracket_borrowed=True", t_b and t_b.get('bracket_borrowed') is True)
check("6 carries borrowed_from_bracket", t_b and t_b.get('borrowed_from_bracket') == '400-600')
# regression: an EXACT (non-borrowed) small-spread income_led stays moderate
t_e = TRI(P_BRACK, income(2_700_000, prov_exact), None, 1_800_000, 'standalone_villa')
check("6 non-borrowed small spread → MUC moderate (no leak)", t_e and t_e['muc_level'] == 'moderate')
check("6 non-borrowed carries bracket_borrowed=False", t_e and t_e.get('bracket_borrowed') is False)

print(f"\n{_pass} passed, {_fail} failed")
sys.exit(1 if _fail else 0)
