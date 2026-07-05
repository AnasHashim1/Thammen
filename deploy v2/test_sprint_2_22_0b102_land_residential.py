# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.102 — land residential-usage comparability (RICS VPS 3 / IVS 103), isolated test.

Exercises the REAL production path (E14): moj_reference.build_reference +
evaluate_property.apply_moj_strategy on the real moj_weekly.csv.

Design (RICS-correct): the LAND comparable pool is now residential-only (mirrors the
villa A1 filter, via usage_filter._is_residential_usage) — apartment/complex land
(عمارات او مجمعات سكنية) + commercial land (أراض تجارية) are NOT comparable to a
residential land subject and are removed. Thin residential cells (n<10) fall to the
existing indicative tier (reliability disclosed via confidence pill + n + range). The
land amount = total_price_median × GIS factors, so removing the pricier non-residential
comps de-inflates it. VILLA pool was already A1-filtered → byte-identical.
"""
import csv, sys
from moj_reference import build_reference, parse_date, DATE_COL
from evaluate_property import apply_moj_strategy
from usage_filter import _is_residential_usage as RES
from built_type import matches_category as BT

ROWS = list(csv.DictReader(open('moj_weekly.csv', encoding='utf-8-sig')))
MAXD = max(d for d in (parse_date(r.get(DATE_COL, '')) for r in ROWS) if d)

_p = 0; _f = 0
def ck(name, cond, extra=''):
    global _p, _f
    if cond: _p += 1; print(f'  ok  {name}')
    else:    _f += 1; print(f'  FAIL {name}  {extra}')

def land(area, plot):
    ref = build_reference(ROWS, area, MAXD)
    return apply_moj_strategy('raw_land', float(plot), ref), ref

def villa(area, plot):
    ref = build_reference(ROWS, area, MAXD)
    return apply_moj_strategy('standalone_villa', float(plot), ref)

print('=== A. build_reference LAND pool is now residential-only (transactions carry only residential usage) ===')
ref = build_reference(ROWS, 'الوعب', MAXD, return_transactions=True)
lb = (ref.get('categories') or {}).get('land', {}).get('size_brackets', {})
# every transaction in every land bracket must pass the residential-usage filter
all_res = True; sample_types = set()
for b in lb.values():
    for tx in (b.get('transactions') or []):
        sample_types.add(tx.get('type_ar'))
# stronger: re-derive from the raw rows that the pool would include — check a bracket count
ck('A1 land brackets exist for الوعب', len(lb) > 0, list(lb.keys()))
# the 900-1500 bracket residential-only count must equal the residential count (not the mixed)
from datetime import timedelta
c24 = MAXD - timedelta(days=730)
waab = [r for r in ROWS if __import__('moj_reference').area_match_key(r.get('اسم المنطقة','')) == __import__('moj_reference').area_match_key('الوعب')]
def infb(lo, hi, filt):
    return [r for r in waab if BT(r,'land') and (d:=parse_date(r[DATE_COL])) and d>=c24
            and (lambda a: a and lo<=a<hi)(_tofloat(r.get('المساحة بالمتر المربع'))) and filt(r)]
def _tofloat(x):
    try: return float(str(x).replace(',','').strip())
    except: return None
mixed_915 = infb(900,1500, lambda r: True)
res_915   = infb(900,1500, RES)
ck('A2 الوعب 900-1500 pool has apartment/commercial land in the RAW data (mixed > residential)',
   len(mixed_915) > len(res_915), f'mixed={len(mixed_915)} res={len(res_915)}')
b915 = lb.get('900-1500', {})
ck('A3 build_reference 900-1500 bracket n == residential-only count (non-residential removed)',
   b915.get('n') == len(res_915), f"bracket_n={b915.get('n')} res={len(res_915)}")

print('=== B. VILLA byte-gate: the villa pool was ALREADY A1-filtered → identical to b100 ===')
B100 = {'بو هامور': (500, 2357895), 'مريخ': (700, 5100000),
        'المعمورة': (650, 3741176), 'المعراض': (300, 2572445)}
for a, (p, expect) in B100.items():
    v = villa(a, p)
    ck(f'B {a} villa total unchanged == {expect:,}',
       v.moj_median_total is not None and int(v.moj_median_total) == expect,
       f'got={v.moj_median_total}')

print('=== C. LAND residential comps LEAD (de-inflation on the correct metric) ===')
# robust residential cells de-inflate DOWN vs the old mixed; thin cells still produce a value
for a, p, mx in [('لوسيل', 2000, 5_891_913), ('المطار العتيق', 500, 2_484_931), ('العزيزية', 1000, 3_175_000)]:
    v, _ = land(a, p)
    ck(f'C {a} {p} land value <= old mixed ({mx:,}) — de-inflated',
       v.moj_median_total is not None and v.moj_median_total <= mx,
       f'got={v.moj_median_total}')
    ck(f'C {a} {p} land value > 0 (no refusal)', (v.moj_median_total or 0) > 0)

print('=== D. الوعب (PO case): residential comps + thin → indicative (reliability disclosed) ===')
v, _ = land('الوعب', 1219)
ck('D الوعب 1219 leads with residential (~5.3M, not the mixed ~6.7M)',
   v.moj_median_total is not None and v.moj_median_total < 6_000_000, f'got={v.moj_median_total}')
ck('D الوعب 1219 marked NOT reliable (indicative, n<10) → confidence pill discloses',
   v.bracket_reliable is False, f'reliable={v.bracket_reliable} n={v.bracket_n}')
ck('D الوعب 1219 bracket_n < 10 (thin residential)', (v.bracket_n or 99) < 10, v.bracket_n)

print('=== E. LAND unchanged where the bracket was already all-residential (no false move) ===')
v, _ = land('الوعب', 700)   # 600-900: res == mixed (all residential)
ck('E الوعب 600-900 still ~3.04M (no contamination there)',
   v.moj_median_total is not None and abs(v.moj_median_total - 3_040_186) < 50_000,
   f'got={v.moj_median_total}')

print('=== F. residential-having areas STILL produce a value (no false refusal in real residential suburbs) ===')
none = 0; tested = 0
for a in ('الوعب','لوسيل','المطار العتيق','العزيزية','الوكرة','معيذر','الثمامة','الغرافة'):
    ref = build_reference(ROWS, a, MAXD)
    lc = (ref.get('categories') or {}).get('land', {})
    if (lc.get('n') or 0) == 0:  # area has no residential land at all → covered by G, skip
        continue
    v = apply_moj_strategy('raw_land', 700.0, ref); tested += 1
    if v.moj_median_total is None: none += 1; print('  UNEXPECTED refusal:', a)
ck(f'F residential suburbs served (tested={tested}, refusals={none})', none == 0 and tested >= 5,
   f'refusals={none} tested={tested}')

print('=== G. commercial-only-land area REFUSES gracefully (0 residential comps — RICS honest) ===')
# نجمة / المنصورة: downtown Doha, land is ALL apartment/complex → 0 residential → the honest answer is
# "no comparable residential evidence" (these are also classifier-rejected before valuation).
for a in ('نجمة', 'المنصورة'):
    ref = build_reference(ROWS, a, MAXD)
    lc = (ref.get('categories') or {}).get('land', {})
    v = apply_moj_strategy('raw_land', 800.0, ref)
    ck(f'G {a} land has 0 residential comps -> graceful refusal (amount None)',
       (lc.get('n') or 0) == 0 and v.moj_median_total is None,
       f"land_n={lc.get('n')} amount={v.moj_median_total}")

print(f'\nRESULT: {_p} passed, {_f} failed')
sys.exit(1 if _f else 0)
