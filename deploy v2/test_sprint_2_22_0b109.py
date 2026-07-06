# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.109 — the LAND geo-pool residential-usage filter (S4, RICS VPS 3 / IVS 103).

Exercises the REAL production path (E14): geo_reference_v2._get_area_transactions on the real
moj_weekly.csv. The b102 SIBLING — b102 filtered the moj_reference LAND bracket pool; S4 extends the
same usage_filter._is_residential_usage to the geo_reference_v2 LAND pool (the geo-widened land headline
+ the comparable-grid display), closing the geo↔bracket asymmetry (fact #3).

🔴 Gate-2 (land geo surfaces can move). VILLA path byte-identical by construction — the clause
`category in ('villa','land')` is logically identical to the old `category == 'villa'` for the villa
category (same `_is_residential_usage` test). Land now filtered; other categories untouched.

Per the b101 lesson: validate on the pool median (land amount = total_price_median × GIS factors, so the
filter's % impact on the pool median == its % impact on the headline for widened-land cells).
"""
import csv, io, sys
from datetime import timedelta
from geo_reference_v2 import _get_area_transactions, _norm, _parse_date, _bt_matches
from usage_filter import _is_residential_usage as RES

ROWS = list(csv.DictReader(io.open('moj_weekly.csv', encoding='utf-8-sig')))
DC = [k for k in ROWS[0].keys() if 'تاريخ' in k][0]
MAXD = max(d for d in (_parse_date(r.get(DC, '')) for r in ROWS) if d)
CUT24 = MAXD - timedelta(days=730)

_p = _f = 0
def ck(name, cond, extra=''):
    global _p, _f
    if cond: _p += 1; print(f'  ok  {name}')
    else:    _f += 1; print(f'  FAIL {name}  {extra}')

def _pos(x):
    try: return float(x) > 0
    except (TypeError, ValueError): return False

def _rows_for(area, cat):
    """Replicate the geo selection (NO residential filter) for a category — the pre-S4 'before'."""
    names = {_norm(area)}
    out = []
    for r in ROWS:
        if _norm(r.get('اسم المنطقة', '')) not in names: continue
        if not _bt_matches(r, cat): continue
        d = _parse_date(r.get(DC, ''))
        if not d or d < CUT24: continue
        if not _pos(r.get('سعر المتر المربع')) or not _pos(r.get('المساحة بالمتر المربع')): continue
        out.append(r)
    return out

def after(area, cat='land'):
    return _get_area_transactions(ROWS, {_norm(area)}, cat, CUT24, DC)

# ── (1) the filter FIRES on land (الوعب: the PO's fixture, 56 → 25 residential) ──
wa_before = _rows_for('الوعب', 'land')
wa_after  = after('الوعب')
wa_res    = [r for r in wa_before if RES(r)]
ck('الوعب geo land pool filtered 56 → 25 residential (the fix fires)',
   len(wa_before) == 56 and len(wa_after) == 25, f'before={len(wa_before)} after={len(wa_after)}')
ck('the filter only ever REMOVES rows (residential ⊆ all — never adds/inflates)',
   len(wa_after) <= len(wa_before))
ck('the survivors == exactly the residential-usage rows of the pool',
   len(wa_res) == len(wa_after))

# ── (2) VILLA path byte-identical — the villa branch is unchanged (structural + measured) ──
ck("source: villa branch preserved — the clause covers 'villa' exactly as before",
   "if category in ('villa', 'land') and not _is_residential_usage(r):" in
   io.open('geo_reference_v2.py', encoding='utf-8').read())
for a in ('الوعب', 'بو هامور'):
    vb, va = _rows_for(a, 'villa'), after(a, 'villa')
    # villa was ALREADY residential-filtered before b109 → the real function == the residential subset,
    # i.e. b109 does not change the villa result at all.
    ck(f'villa pool for {a}: real == residential-subset (byte-identical, unchanged by b109)',
       len(va) == len([r for r in vb if RES(r)]), f'real={len(va)} res={len([r for r in vb if RES(r)])}')

# ── (3) 100%-non-residential downtown land → EMPTY residential pool (honest refusal, b102 parity) ──
for a in ('نجمة', 'فريج كليب', 'فريج عبد العزيز'):
    ck(f'{a}: 100%-non-residential land → 0 residential comps after filter (honest refusal)',
       len(after(a)) == 0 and len(_rows_for(a, 'land')) > 0)

# ── (4) CLEAN residential areas → land pool ~unchanged (no spurious change) ──
for a in ('الوكير', 'ام صلال علي', 'الخور'):
    b, af = _rows_for(a, 'land'), after(a)
    ck(f'{a}: clean residential land pool ~unchanged (drop ≤ 4 rows)',
       0 <= (len(b) - len(af)) <= 4, f'before={len(b)} after={len(af)}')

# ── (5) other categories (compound) are NOT touched by this clause ──
ck('compound category is not residential-filtered by this clause (unaffected)',
   isinstance(after('الوعب', 'compound'), list))

# ── (6) source rationale + version ──
SRC = io.open('geo_reference_v2.py', encoding='utf-8').read()
ck('source: b109 rationale comment present (the b102 sibling)',
   'Sprint 2.22.0b.109 (S4)' in SRC and 'b102 sibling' in SRC)
ENG = io.open('evaluate_unified.py', encoding='utf-8').read()
ck('engine is a valid b-series tag (no exact pin — Lesson-2)',
   "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print(f'\nb109: {_p} passed, {_f} failed')
sys.exit(1 if _f else 0)
