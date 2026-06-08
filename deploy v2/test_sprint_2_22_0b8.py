# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.8 (§6 v2 remainder) — income OPEX alignment isolated tests.

Exercises the PRODUCTION _build_income_crosscheck (E14 / Rule #40 — the real engine,
not a replica): the NOI opex must MATCH the opex the cap rate was calibrated on. The
villa yield is calibrated net of opex 0.20 (cap_rate_calibrator.OPEX_RATIO['villa']
=0.20 + villa service_charge=0 -> exactly 0.20); the engine NOI used a flat 0.23 ->
every villa-calibrated income was under-stated by 0.77/0.80 = -3.75%. Fix: apply the
calibration opex ONLY when the rate is calibrated (a hardcoded/fallback rate's implied
opex is unknown -> keep 0.23, byte-identical). Compound is 0.23 on both sides already.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b8.py
"""
import sys
import evaluate_unified as eu
from cap_rate_calibrator import OPEX_RATIO as CALIB_OPEX

_pass = _fail = 0
def check(name, cond):
    global _pass, _fail
    if cond: _pass += 1; print(f"  PASS  {name}")
    else:    _fail += 1; print(f"  FAIL  {name}")

RENT = 15000            # monthly
ANNUAL = RENT * 12      # 180000

print("Sprint 2.22.0b.8 §6 v2 — income OPEX alignment\n")

# ── 1) SYNC GUARD — the engine opex table MIRRORS the calibrator (the bug's root) ──
check("1 villa opex mirrors calibrator (0.20)",
      eu._CALIB_OPEX_BY_ASSET['villa'] == CALIB_OPEX['villa'] == 0.20)
check("1 standalone_villa == 0.20", eu._CALIB_OPEX_BY_ASSET['standalone_villa'] == 0.20)
check("1 compound_small mirrors calibrator (0.23)",
      eu._CALIB_OPEX_BY_ASSET['compound_small'] == CALIB_OPEX['compound_small'] == 0.23)
check("1 fallback constant still 0.23", eu.OPEX_RATIO_RESIDENTIAL == 0.23)

# ── monkeypatch the calibrated-cap lookup to ISOLATE the opex logic (no DB/GIS) ──
_orig = eu._lookup_calibrated_cap_rate
def _calibrated(rate):
    def f(asset_type, area, plot, stock=None):
        return rate, {'source': 'calibrated', 'cap_rate': rate,
                      'cap_rate_pct': round(rate * 100, 2),
                      'confidence': 'reliable', 'sample_size': 46}
    return f
def _none(*a, **k):
    return None, None

# ── 2) villa CALIBRATED -> opex 0.20 (the fix) ──
eu._lookup_calibrated_cap_rate = _calibrated(0.05155)
r = eu._build_income_crosscheck(rental_income=RENT, v3_rent_data=None,
        asset_type='standalone_villa', primary_value=3_000_000, area_name='X', plot_area_m2=500)
check("2 source calibrated", r and r['cap_rate_provenance']['source'] == 'calibrated')
check("2 villa-calibrated opex == 0.20", r and r['opex_ratio'] == 0.20)
check("2 noi == rent*12*0.80 (144000)", r and r['noi'] == round(ANNUAL * 0.80))
check("2 value == round(noi/cap)", r and r['value'] == round(r['noi'] / r['cap_rate']))

# ── 3) compound CALIBRATED -> opex 0.23 (no change; both sides 0.23) ──
r = eu._build_income_crosscheck(rental_income=RENT, v3_rent_data=None,
        asset_type='compound_small', primary_value=5_000_000, area_name='X', plot_area_m2=500)
check("3 compound-calibrated opex == 0.23", r and r['opex_ratio'] == 0.23)
check("3 compound noi == rent*12*0.77 (unchanged)", r and r['noi'] == round(ANNUAL * 0.77))

# ── 4) villa FALLBACK (hardcoded) -> opex 0.23, byte-identical to pre-fix ──
eu._lookup_calibrated_cap_rate = _none
r = eu._build_income_crosscheck(rental_income=RENT, v3_rent_data=None,
        asset_type='standalone_villa', primary_value=3_000_000, area_name='X', plot_area_m2=500)
check("4 source hardcoded (no calibrated cell)", r and r['cap_rate_provenance']['source'] == 'hardcoded')
check("4 villa-fallback opex == 0.23 (kept, not 0.20)", r and r['opex_ratio'] == 0.23)
check("4 fallback noi == rent*12*0.77 (byte-identical pre-fix)", r and r['noi'] == round(ANNUAL * 0.77))

# ── 5) the -3.75% under-statement is exactly closed on a calibrated rate ──
eu._lookup_calibrated_cap_rate = _calibrated(0.05155)
r_cal = eu._build_income_crosscheck(rental_income=RENT, v3_rent_data=None,
        asset_type='standalone_villa', primary_value=3_000_000, area_name='X', plot_area_m2=500)
old_noi = round(ANNUAL * (1 - 0.23))            # what the pre-fix flat 0.23 produced
check("5 corrected/old noi ratio == 0.80/0.77 (the +3.75%)",
      abs(r_cal['noi'] / old_noi - 0.80 / 0.77) < 1e-3)
check("5 corrected value strictly higher than the old under-stated value",
      r_cal['value'] > round(old_noi / 0.05155))

eu._lookup_calibrated_cap_rate = _orig          # restore

# ── 6) house has no cap rate -> no income crosscheck (opex never applies) ──
r = eu._build_income_crosscheck(rental_income=RENT, v3_rent_data=None,
        asset_type='house', primary_value=3_000_000, area_name='X', plot_area_m2=500)
check("6 house -> None (CAP_RATES_BY_ASSET excludes house)", r is None)

# ── 7) E14 — REAL DB: villa calibrated cell (امريخ الجنوبي 400-600) -> opex 0.20 ──
r = eu._build_income_crosscheck(rental_income=RENT, v3_rent_data=None,
        asset_type='standalone_villa', primary_value=3_000_000,
        area_name='امريخ الجنوبي', plot_area_m2=500, stock_class=None)
check("7 real DB villa cell is calibrated", r and r['cap_rate_provenance']['source'] == 'calibrated')
check("7 real DB villa opex == 0.20", r and r['opex_ratio'] == 0.20)
check("7 real DB noi == rent*12*0.80 (144000)", r and r['noi'] == round(ANNUAL * 0.80))

print(f"\n{_pass} passed, {_fail} failed")
sys.exit(1 if _fail else 0)
