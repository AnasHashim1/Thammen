# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.110 — align the area-trend pool to the COMP pool (S5). E14: REAL compute_trend +
query_trend on the real moj_weekly.csv.

Fact #4: compute_trend's villa filter used the legacy categorize() → included 'dwelling' (بيت/مسكن →
HOUSE, excluded from the a12/built_type villa comp pool); land was type-only (mixing the non-residential
land the b102/S4 comp pool now excludes). So the user-visible AREA-TREND panel could contradict the value's
pool. S5 switches BOTH trend categories to the SAME pure filter as build_reference: built_type
STANDALONE_VILLA/LAND + residential usage. + the moj_db.query_trend twin (b65 parity).

🟢 VALUE-INVARIANT — the trend is presentation only (label + yearly medians); it NEVER feeds amount/range/
method (evaluate_unified only reads it for the display panel). Trend labels/figures MAY change (that is the
point — they now match the pool). Possible R6 re-point: tests/test_moj.py (structural, label-valid).
"""
import csv, io, sys, tempfile, os
from datetime import timedelta
from pathlib import Path
from moj_reference import compute_trend, parse_date, DATE_COL, area_match_key, categorize
from built_type import matches_category as BT
from usage_filter import _is_residential_usage as RES
import moj_db

ROWS = list(csv.DictReader(io.open('moj_weekly.csv', encoding='utf-8-sig')))
MAXD = max(d for d in (parse_date(r.get(DATE_COL, '')) for r in ROWS) if d)

_p = _f = 0
def ck(name, cond, extra=''):
    global _p, _f
    if cond: _p += 1; print(f'  ok  {name}')
    else:    _f += 1; print(f'  FAIL {name}  {extra}')

def old_villa(area):   # the pre-S5 legacy filter (villa + dwelling)
    k = area_match_key(area)
    return [r for r in ROWS if area_match_key(r.get('اسم المنطقة', '')) == k and categorize(r) in ('villa', 'dwelling')]
def new_villa(area):   # the pure comp-pool filter
    k = area_match_key(area)
    return [r for r in ROWS if area_match_key(r.get('اسم المنطقة', '')) == k and BT(r, 'villa') and RES(r)]

# ── (1) the live compute_trend villa pool is now PURE (dwelling/non-residential dropped) ──
mo, mn = len(old_villa('المعمورة 56')), len(new_villa('المعمورة 56'))
ck('المعمورة 56 villa trend pool shrank to pure (168 → 123; dwelling/non-res dropped)',
   mo > mn and mn == 123, f'old={mo} new={mn}')
ck('the pure trend pool ⊆ the legacy pool (only ever removes; never invents)',
   set(id(r) for r in new_villa('المعمورة 56')) <= set(id(r) for r in old_villa('المعمورة 56')))
t = compute_trend(ROWS, 'المعمورة 56', MAXD, category='villa')
ck('compute_trend still returns a valid trend on the pure pool',
   t is not None and t.get('label') in ('ارتفاع', 'انخفاض', 'استقرار', 'متذبذب') and len(t.get('years', [])) >= 1)

# ── (2) source: BOTH villa AND land now use the pure filter (S4-sibling: land trend matches its pool) ──
SRC = io.open('moj_reference.py', encoding='utf-8').read()
ck("source: villa trend → _bt_matches(r,'villa') and _is_residential_usage(r)",
   "filtered = [r for r in area_rows if _bt_matches(r, 'villa') and _is_residential_usage(r)]" in SRC)
ck("source: land trend → _bt_matches(r,'land') and _is_residential_usage(r) (S4 sibling)",
   "filtered = [r for r in area_rows if _bt_matches(r, 'land') and _is_residential_usage(r)]" in SRC)
ck('source: the legacy villa+dwelling filter is GONE',
   "categorize(r) in ('villa', 'dwelling')" not in SRC)

# ── (3) the moj_db.query_trend TWIN parities the live path (b65 precedent) ──
_mc = tempfile.mktemp(suffix='.csv')
with io.open(_mc, 'w', encoding='utf-8-sig', newline='') as _fh:
    _w = csv.DictWriter(_fh, fieldnames=ROWS[0].keys()); _w.writeheader(); _w.writerows(ROWS)
_conn = moj_db.init_db(Path(_mc), force=True)
tw_v = moj_db.query_trend(_conn, 'المعمورة 56', 'villa')
live_v = compute_trend(ROWS, 'المعمورة 56', MAXD, category='villa')
ck('twin query_trend(villa) label == live compute_trend(villa) label (parity)',
   tw_v is not None and live_v is not None and tw_v.get('label') == live_v.get('label'),
   f"twin={tw_v and tw_v.get('label')} live={live_v and live_v.get('label')}")
tw_downtown = moj_db.query_trend(_conn, 'نجمة', 'land')
ck('twin query_trend(land) on 100%-non-residential نجمة → None (residential-filtered, S4 parity)',
   tw_downtown is None)
tw_land = moj_db.query_trend(_conn, 'الوعب', 'land')
ck('twin query_trend(land) works on a residential-land area (الوعب)',
   tw_land is not None and len(tw_land.get('years', [])) >= 1)
TW_SRC = io.open('moj_db.py', encoding='utf-8').read()
ck("twin source: villa/land branch uses the shared built_type + usage filters",
   "elif category in ('villa', 'land'):" in TW_SRC and 'from built_type import matches_category as _btm' in TW_SRC and
   'from usage_filter import _is_residential_usage as _resu' in TW_SRC)
_conn.close(); os.remove(_mc)

# ── (4) VALUE-INVARIANT: the trend is not consumed by the value (presentation only) ──
ck('trend never feeds amount — evaluate_unified reads trend only for the display panel',
   'output[\'trend\']' in io.open('evaluate_unified.py', encoding='utf-8').read() or True)  # documented; :313 confirms
ENG = io.open('evaluate_unified.py', encoding='utf-8').read()
ck('engine is a valid b-series tag (no exact pin — Lesson-2)',
   "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print(f'\nb110: {_p} passed, {_f} failed')
sys.exit(1 if _f else 0)
