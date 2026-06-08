# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.9 — QARS property-basis panel (display-only / value-invariant).

Exercises the PRODUCTION helpers (E14 / Rule #40) — not replicas — plus the
PropertyLocation/find_property capture and the index.html wiring. The load-bearing
invariant: the building-age estimate is DISPLAY-ONLY and NEVER leaks into the
valuation input `building_age_years` (that would be Gate-2).
"""
import io, sys, re, os
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from evaluate_unified import _build_property_basis, _building_age_estimate
import qatar_gis
from qatar_gis import PropertyLocation

NOW = datetime.now(tz=timezone.utc).year
P = F = 0
def ok(name, cond):
    global P, F
    if cond: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name)

def ms(y, m=6, d=15):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)

print('=== _building_age_estimate ===')
a = _building_age_estimate(ms(2009))
ok('2009 survey -> surveyed_year 2009', a and a['surveyed_year'] == 2009)
ok('floor = now - 2009', a and a['age_floor_years'] == NOW - 2009)
ok('basis = qars_survey', a and a['basis'] == 'qars_survey')
ok('note_ar is a floor (حدّ أدنى)', a and 'حدّ أدنى' in a['note_ar'])
ok('note_ar carries >= years', a and ('≥' in a['note_ar']))
ok('None when surveyed_date missing', _building_age_estimate(None) is None)
ok('None when surveyed_date is 0', _building_age_estimate(0) is None)
ok('None when surveyed_date is a string', _building_age_estimate('2009-08-09') is None)
# future survey date -> floor negative -> None (defensive)
ok('None when survey year in the future', _building_age_estimate(ms(NOW + 5)) is None)

print('=== _build_property_basis ===')
b = _build_property_basis(pin=56101583, electricity_no=140502, water_no=104503, surveyed_date=ms(2009))
ok('pin surfaced', b and b['pin'] == 56101583)
ok('electricity_no surfaced (the bank-report field)', b and b['electricity_no'] == 140502)
ok('water_no surfaced', b and b['water_no'] == 104503)
ok('building_age_estimate nested', b and b.get('building_age_estimate', {}).get('age_floor_years') == NOW - 2009)
# 🔴 VALUE-INVARIANCE CONTRACT: the basis block must NEVER carry the valuation input key.
ok('NO building_age_years key (value-invariance)', b and 'building_age_years' not in b)
ok('NO age_source key (value-invariance)', b and 'age_source' not in b)
ok('NO valuation/amount key', b and 'amount' not in b and 'valuation' not in b)
# graceful degradation
ok('all-None inputs -> None block', _build_property_basis() is None)
ok('PIN-only (land path, no QARS utils) still surfaces', _build_property_basis(pin=74328443) is not None)
ok('electricity-only surfaces', (_build_property_basis(electricity_no=999) or {}).get('electricity_no') == 999)
# never raises
try:
    _build_property_basis(pin=1, surveyed_date='bad'); _building_age_estimate('bad'); ok('never raises on bad input', True)
except Exception:
    ok('never raises on bad input', False)

print('=== PropertyLocation / find_property capture ===')
ok('PropertyLocation has surveyed_date field',
   'surveyed_date' in getattr(PropertyLocation, '__dataclass_fields__', {}))
# surveyed_date default None so PIN-path/legacy/mocks are unaffected
_pl = PropertyLocation(zone=1, street=2, building=3, pin=4, qars='', plot_no_old=None,
                       lon=0.0, lat=0.0, electricity_no=None, water_no=None, qtel_id=None,
                       building_subtype=None)
ok('surveyed_date defaults to None (back-compat)', _pl.surveyed_date is None)

# find_property captures SURVEYED_DATE — exercise the REAL method with a stubbed _qars_query
_FAKE = {'features': [{
    'attributes': {'PIN': 56101583, 'QARS': 'X', 'PLOT_NO_OLD': None,
                   'ELECTRICITY_NO': 140502, 'WATER_NO': 104503, 'QTEL_ID': None,
                   'BUILDING_NO_SUBTYPE': 1, 'SURVEYED_DATE': ms(2009)},
    'geometry': {'x': 51.49, 'y': 25.24}}]}
_orig = qatar_gis._qars_query
try:
    qatar_gis._qars_query = lambda params, **kw: _FAKE
    g = qatar_gis.QatarGIS(verbose=False)
    loc = g.find_property(56, 647, 6)
    ok('find_property captures SURVEYED_DATE', loc is not None and loc.surveyed_date == ms(2009))
    ok('find_property still captures electricity_no', loc is not None and loc.electricity_no == 140502)
finally:
    qatar_gis._qars_query = _orig

print('=== index.html wiring ===')
html = open(os.path.join(os.path.dirname(__file__), 'index.html'), encoding='utf-8').read()
ok('pbRows helper defined', 'function pbRows(' in html)
ok('pbRows called in showConfirm/results', html.count('pbRows(d.property_basis)') >= 2)
ok('renders الرقم المساحي', 'الرقم المساحي' in html)
ok('renders رقم الكهرباء', 'رقم الكهرباء' in html)
ok('renders عمر البناء التقديري', 'عمر البناء التقديري' in html)

print(f'\n{"="*40}\n2.22.0b.9: {P} passed, {F} failed')
sys.exit(1 if F else 0)
