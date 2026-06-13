# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.39 — DEF-UX1.1 geo-led keystone comparables — isolated logic tests.

Extends b38 (matched-bracket keystone) to the GEO-LED market path (comparison_widened /
_widened_indicative): the subject's PRIMARY-area raw transactions within the geo-widened pool
(`geo_v2['primary']['transactions']`), surfaced ONLY when leader=='market'. The full pool also
includes location-adjusted NEIGHBOUR rows → the frontend discloses the widening and never claims
«these decided your number» for the geo case. DISPLAY-ONLY / VALUE-INVARIANT / privacy-safe (E12).

Exercises the PRODUCTION functions (Rule #40 / E14):
  - evaluate_unified._keystone_comparables  (basis + pool_n + price_m2 fallback + newest-first)
  + structural pins on evaluate_unified.py (Cases 2-3 geo stash + the broadened b4-region gate)
  + structural pins on index.html (the _kcGeo branch + the widening disclosure)

Run:  set PYTHONIOENCODING=utf-8  &&  python test_sprint_2_22_0b39.py
"""
import sys
from evaluate_unified import _keystone_comparables

_fails = []
def check(name, cond, detail=''):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  — {detail}" if detail and not cond else ''))
    if not cond:
        _fails.append(name)


# geo rows (the _get_area_transactions shape): ppm² key is `price_m2`, NOT `price_per_m2`; row-order (unsorted)
def _geo(area, m2, total, ppm2, date):
    return {'area': area, 'date': date, 'price_m2': ppm2, 'price_ft': ppm2 / 10.764,
            'area_m2': m2, 'total_price': total, 'type': 'فيلا'}

GEO = [
    _geo('معمورة', 640, 3_350_000, 5234, '2025-06-15'),
    _geo('معمورة', 600, 3_000_000, 5000, '2025-09-01'),   # newer than row0 → must sort first
    _geo('معمورة', 700, 3_800_000, 5428, '2025-02-01'),
]

print("── A. _keystone_comparables(basis='geo_widened') — geo key fallback + pool_n + newest-first ──")
blk = _keystone_comparables(GEO, n=34, window_used=None, basis='geo_widened', pool_n=34)
check("A1 basis carried as 'geo_widened'", isinstance(blk, dict) and blk.get('basis') == 'geo_widened')
check("A2 pool_n carried (full geo pool size for the disclosure)", blk.get('pool_n') == 34)
check("A3 ppm² read from the geo `price_m2` key (not price_per_m2)",
      blk['rows'][0].get('price_per_m2') is not None, str(blk['rows'][0]))
check("A4 newest-first sort applied to the (unsorted) geo pool",
      [r['date'] for r in blk['rows']] == sorted([r['date'] for r in blk['rows']], reverse=True)
      and blk['rows'][0]['date'] == '2025-09-01')
# A5 — geo display rows still anonymized to exactly {date, area_m2, total_price, price_per_m2} (no area/type/ft²)
_dk = set(blk['rows'][0].keys())
check("A5 geo display row keys == {date, area_m2, total_price, price_per_m2} (E12 anonymity)",
      _dk == {'date', 'area_m2', 'total_price', 'price_per_m2'}, str(_dk))
check("A6 source_ar cites «CC BY 4.0»", 'CC BY 4.0' in (blk.get('source_ar') or ''))

print("\n── B. b38 matched_bracket path STILL DEFAULT (no regression from the new params) ──")
BR = [{'date': '2025-12-17', 'area_m2': 444, 'total_price': 2_300_000, 'price_per_m2': 5180},
      {'date': '2025-08-12', 'area_m2': 450, 'total_price': 2_150_000, 'price_per_m2': 4778}]
b = _keystone_comparables(BR, n=37, window_used=None)   # defaults → matched_bracket, pool_n None
check("B1 default basis == 'matched_bracket'", b.get('basis') == 'matched_bracket')
check("B2 bracket ppm² still read from price_per_m2", b['rows'][0].get('price_per_m2') == 5180)
check("B3 None/empty → None (unchanged)", _keystone_comparables(None, 5, None) is None
      and _keystone_comparables([], 5, None) is None)

print("\n── C. value-invariance: the block carries NO headline keys (display-only) ──")
check("C1 keystone block has no amount/low/high/method/rule keys",
      not ({'amount', 'low', 'high', 'method', 'rule'} & set(blk.keys())))

print("\n── D. evaluate_unified.py structural (geo stash + broadened market-led gate) ──")
_eu = open('evaluate_unified.py', encoding='utf-8').read()
check("D1 Cases 2-3 stash geo comparables from geo_v2['primary']['transactions']",
      _eu.count("(geo_v2.get('primary') or {}).get('transactions')") >= 2)
check("D2 b4-region gate broadened to the widened methods (still leader=='market')",
      "_gate['leader'] == 'market'" in _eu
      and "'comparison_widened'" in _eu and "'comparison_widened_indicative'" in _eu
      and "_kc_method in (" in _eu)
check("D3 basis derived from method (matched_bracket vs geo_widened) + pool_n passed",
      "_kc_basis = ('matched_bracket' if _kc_method == 'comparison_bracket'" in _eu
      and "basis=_kc_basis" in _eu and "pool_n=output['valuation'].get('n_transactions')" in _eu)
check("D4 comparison_thin / preliminary returns still carry NO comparables",
      "'comparables'" not in _eu.split("'method': 'comparison_thin'", 1)[1].split('\ndef ', 1)[0])

print("\n── E. index.html render (structural — E14 reads the REAL file) ──")
_html = open('index.html', encoding='utf-8').read()
_seg = _html.split('if(v.comparables', 1)[1].split('// Sprint 2.22.0b.18', 1)[0]
check("E1 per-basis branch on geo_widened", "_kcGeo=(_kc.basis==='geo_widened')" in _seg)
check("E2 geo header «صفقات في منطقتك ضمن حوض المقارنة الموسَّع»", 'حوض المقارنة الموسَّع جغرافياً' in _seg)
check("E3 geo widening disclosure (location-adjusted neighbours) + pool_n", 'وُسِّع الحوض لمناطق مجاورة' in _seg
      and 'مُعدَّلة الموقع' in _seg and '_kc.pool_n' in _seg)
check("E4 bracket header «هي ما قرّر رقمك» retained (b38)", 'هي ما قرّر رقمك' in _seg)
check("E5 rows still in a dir=ltr table + CC BY source + lives in `how` (value-invariant)",
      'direction:ltr' in _seg and '_kc.source_ar' in _seg and 'how+=' in _seg and 't1+=' not in _seg)

print(f"\n{'='*60}")
if _fails:
    print(f"RESULT: {len(_fails)} FAILED → {_fails}")
    sys.exit(1)
print("RESULT: ALL PASS")
