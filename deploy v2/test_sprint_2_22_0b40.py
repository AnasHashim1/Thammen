# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.40 — DEF-UX1.2a cost-led «considered» comparables — isolated logic tests.

On a COST-LED villa (rule=='cost_led', e.g. Marikh 54/541/6) the market pool was CONSIDERED but
did NOT lead the number (it failed its reliability bar — geo-full dispersion > 0.30 / thinness).
The engine surfaces the subject's PRIMARY-area raw rows under a NEW key `considered_comparables`
(basis='cost_considered'), with the honest «اطّلعنا عليها ولم تقُد الرقم» frame — NEVER the b38
«هي ما قرّر رقمك» overclaim (the DRC decided the number). DISPLAY-ONLY / VALUE-INVARIANT /
privacy-safe (E12). Reuses the b38/b39 _keystone_comparables builder unchanged (basis passthrough).

Exercises the PRODUCTION function (Rule #40 / E14):
  - evaluate_unified._keystone_comparables  (basis='cost_considered' passthrough + geo price_m2 + E12)
  + structural pins on evaluate_unified.py (the rule=='cost_led' attach + DISTINCT key + market gate intact)
  + structural pins on index.html (the considered block: honest header, no overclaim, dir=ltr, in `how`)

Run:  set PYTHONIOENCODING=utf-8  &&  python test_sprint_2_22_0b40.py
"""
import sys
from evaluate_unified import _keystone_comparables

_fails = []
def check(name, cond, detail=''):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  — {detail}" if detail and not cond else ''))
    if not cond:
        _fails.append(name)


# the considered pool = the geo primary-area rows (the _get_area_transactions shape): ppm² key = `price_m2`
def _geo(area, m2, total, ppm2, date):
    return {'area': area, 'date': date, 'price_m2': ppm2, 'price_ft': ppm2 / 10.764,
            'area_m2': m2, 'total_price': total, 'type': 'فيلا'}

CONSIDERED = [
    _geo('امريخ الجنوبي', 540, 2_900_000, 5370, '2025-03-10'),
    _geo('امريخ الجنوبي', 600, 3_400_000, 5666, '2025-11-02'),   # newest → must sort first
    _geo('امريخ الجنوبي', 500, 2_500_000, 5000, '2025-07-18'),
]

print("── A. _keystone_comparables(basis='cost_considered') — passthrough + geo key + newest-first ──")
blk = _keystone_comparables(CONSIDERED, n=3, window_used=None, basis='cost_considered', pool_n=51)
check("A1 basis carried as 'cost_considered'", isinstance(blk, dict) and blk.get('basis') == 'cost_considered')
check("A2 pool_n carried (the full geo pool size that failed reliability)", blk.get('pool_n') == 51)
check("A3 ppm² read from the geo `price_m2` key", blk['rows'][0].get('price_per_m2') is not None, str(blk['rows'][0]))
check("A4 newest-first sort applied", blk['rows'][0]['date'] == '2025-11-02')
_dk = set(blk['rows'][0].keys())
check("A5 display row keys == {date, area_m2, total_price, price_per_m2} (E12 anonymity — no area/pin/type)",
      _dk == {'date', 'area_m2', 'total_price', 'price_per_m2'}, str(_dk))
check("A6 source_ar cites «CC BY 4.0»", 'CC BY 4.0' in (blk.get('source_ar') or ''))
check("A7 None/empty rows → None (graceful — no considered panel when no geo primary rows)",
      _keystone_comparables(None, 0, None, basis='cost_considered') is None
      and _keystone_comparables([], 0, None, basis='cost_considered') is None)

print("\n── B. value-invariance: the block carries NO headline keys (display-only) ──")
check("B1 considered block has no amount/low/high/method/rule/leadership keys",
      not ({'amount', 'low', 'high', 'method', 'rule', 'leadership'} & set(blk.keys())))

print("\n── C. evaluate_unified.py structural (cost_led attach + DISTINCT key + market gate intact) ──")
_eu = open('evaluate_unified.py', encoding='utf-8').read()
check("C1 a cost-led considered attach gated on rule=='cost_led' reading geo primary transactions",
      "if _gate['rule'] == 'cost_led':" in _eu
      and "((geo_v2_result or {}).get('primary') or {}).get('transactions')" in _eu
      and "basis='cost_considered'" in _eu)
check("C2 attached under the DISTINCT key `considered_comparables` (NOT `comparables`)",
      "output['valuation']['considered_comparables'] = _cc" in _eu)
check("C3 the b38/b39 market-led keystone gate is UNCHANGED (still leader=='market')",
      "_gate['leader'] == 'market'" in _eu and "output['valuation']['comparables'] = _kc" in _eu)
check("C4 the why-scalar geo_full_dispersion rides the block (for the honest «لم يقُد» disclosure)",
      "_cc['dispersion'] = _gate.get('geo_full_dispersion')" in _eu)
check("C5 pool_n = the considered geo-full pool size", "pool_n=_gate.get('geo_full_n')" in _eu)

print("\n── D. index.html render — b125 R6: the cost-led «considered» pool moved into the flat _s4bEvidence")
print("      table; the honest «لم تقُد الرقم» framing + the «why» disclosure are preserved. ──")
_html = open('index.html', encoding='utf-8').read()
_seg = _html[_html.index('function _s4bEvidence(d,v){'):_html.index('function _s4bHow(d,v,acc')]
check("D1 honest cost-led frame «لم تقُد الرقم»",
      'اطّلعنا على صفقات السوق في منطقتك لكنّها لم تقُد الرقم' in _seg)
check("D2 the considered branch is separate from the matched «قرّرت رقمك» branch (no overclaim when cost led)",
      "if(considered){" in _seg and 'لم تقُد الرقم' in _seg)
check("D3 the «why it didn't lead» disclosure (reliability bar failed + DRC led)",
      'فشل حدّ الموثوقيّة' in _seg and 'منهجُ الكلفة' in _seg)
check("D4 rows in a dir=ltr table + CC BY source + lives in the section builder (value-invariant; never t1)",
      'dir="ltr"' in _seg and 'CC BY 4.0' in _seg and 't1+=' not in _seg)
check("D5 the honest «لم تقُد الرقم» + «فشل حدّ الموثوقيّة» framing distinguishes «considered» from «decided»",
      'لم تقُد الرقم' in _seg and 'فشل حدّ الموثوقيّة' in _seg)

print(f"\n{'='*60}")
if _fails:
    print(f"RESULT: {len(_fails)} FAILED → {_fails}")
    sys.exit(1)
print("RESULT: ALL PASS")
