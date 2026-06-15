# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.41 — DEF-UX1.1b geo NEIGHBOUR rows — isolated logic tests.

On a GEO-LED villa (e.g. V001 56/647/6) the headline median pools the subject's PRIMARY-area rows
(the b39 panel, weight 1.0) PLUS accepted-NEIGHBOUR rows that are location-adjusted into the
subject's area. b39 disclosed only the pool SIZE; b41 surfaces the neighbour rows themselves —
each tagged with its source-area NAME + the location-adjustment multiplier + the DERIVED
location-adjusted ppm² (raw price_m2 × location_adjustment). Nested on the geo block as
`comparables.neighbours`. geo-led only — matched_bracket (b38) has no neighbours, cost-led (b40)
keeps its own `considered_comparables`. DISPLAY-ONLY / VALUE-INVARIANT / privacy-safe (E12).

Exercises the PRODUCTION function (Rule #40 / E14):
  - evaluate_unified._keystone_neighbours  (source_area + ×factor + DERIVED adjusted ppm² + E12 + newest-first)
  + structural pins on evaluate_unified.py (the geo-only nested attach; matched/cost-led untouched)
  + structural pins on index.html (the neighbour sub-table: header, ×factor, raw→adjusted, RTL/LTR, in `how`)

Run:  set PYTHONIOENCODING=utf-8  &&  python test_sprint_2_22_0b41.py
"""
import sys
from evaluate_unified import _keystone_neighbours, _keystone_comparables

_fails = []
def check(name, cond, detail=''):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  — {detail}" if detail and not cond else ''))
    if not cond:
        _fails.append(name)


# accepted_areas[i] shape (geo_reference_v2 _check_six_criteria + Step-4 enrichment):
#   {name, location_adjustment, transactions: [ _get_area_transactions rows ], ...}
def _geo(area, m2, total, ppm2, date):
    return {'area': area, 'date': date, 'price_m2': ppm2, 'price_ft': ppm2 / 10.764,
            'area_m2': m2, 'total_price': total, 'type': 'فيلا'}

def _area(name, adj, rows):
    return {'name': name, 'location_adjustment': adj, 'adjustment_pct': round((adj - 1) * 100, 1),
            'distance_m': 800, 'n': len(rows), 'transactions': rows}

ACCEPTED = [
    _area('معيذر', 1.12, [
        _geo('معيذر', 620, 3_100_000, 5000, '2025-05-12'),
        _geo('معيذر', 700, 3_850_000, 5500, '2025-10-30'),   # newest overall → must sort first
    ]),
    _area('المرة', 0.90, [
        _geo('المرة', 640, 2_800_000, 4375, '2025-08-01'),
    ]),
]

print("── A. _keystone_neighbours — source_area + ×factor + DERIVED adjusted ppm² + newest-first ──")
kn = _keystone_neighbours(ACCEPTED)
check("A1 returns a dict with areas_n / total_n / shown / rows", isinstance(kn, dict)
      and {'areas_n', 'total_n', 'shown', 'rows'} <= set(kn.keys()))
check("A2 areas_n = number of accepted neighbour areas with rows", kn.get('areas_n') == 2, str(kn.get('areas_n')))
check("A3 total_n = total neighbour transactions across areas", kn.get('total_n') == 3, str(kn.get('total_n')))
check("A4 newest-first across the flattened pool", kn['rows'][0]['date'] == '2025-10-30', str(kn['rows'][0]))
r0 = kn['rows'][0]
check("A5 source_area carried (E12: area NAME, a public GIS aggregate label)", r0.get('source_area') == 'معيذر')
check("A6 adjustment_factor carried (the location multiplier, rounded)", r0.get('adjustment_factor') == 1.12)
check("A7 adjusted ppm² is DERIVED = round(raw × factor) — value-invariant, no median re-run",
      r0.get('price_per_m2_adjusted') == round(5500 * 1.12)
      and r0.get('price_per_m2_raw') == 5500, str(r0))
# the discounted neighbour (×0.90) — adjusted < raw
_r_mura = next(r for r in kn['rows'] if r['source_area'] == 'المرة')
check("A8 a <1 factor lowers the adjusted ppm² below raw (المرة ×0.90)",
      _r_mura['price_per_m2_adjusted'] == round(4375 * 0.90) < _r_mura['price_per_m2_raw'])
_dk = set(r0.keys())
check("A9 row keys == {date, area_m2, total_price, price_per_m2_raw, price_per_m2_adjusted, source_area, adjustment_factor}",
      _dk == {'date', 'area_m2', 'total_price', 'price_per_m2_raw', 'price_per_m2_adjusted',
              'source_area', 'adjustment_factor'}, str(_dk))
check("A10 E12: NO raw `area`/`type`/`price_ft`/pin/address/coords leaked into display rows",
      not ({'area', 'type', 'price_ft', 'pin', 'address', 'lat', 'lon'} & _dk))
check("A11 cap respected (cap=2 → 2 rows shown, total_n still full)",
      _keystone_neighbours(ACCEPTED, cap=2)['shown'] == 2
      and _keystone_neighbours(ACCEPTED, cap=2)['total_n'] == 3)
# A12 — DISPLAY SELF-CONSISTENCY (the E2E-caught b14-class bug): a reader must be able to verify
# the shown arithmetic → adjusted == round(shown_raw × shown_factor), even for fractional raw ppm².
_frac = _keystone_neighbours([_area('فريق', 0.9523, [_geo('فريق', 620, 2_400_000, 3870.96, '2025-04-01')])])
_fr = _frac['rows'][0]
check("A12 adjusted == round(DISPLAYED raw × DISPLAYED factor) — panel arithmetic closes (fractional ppm²)",
      _fr['price_per_m2_adjusted'] == round(_fr['price_per_m2_raw'] * _fr['adjustment_factor']),
      f"raw={_fr['price_per_m2_raw']} ×{_fr['adjustment_factor']} → shown {_fr['price_per_m2_adjusted']}, "
      f"expected {round(_fr['price_per_m2_raw'] * _fr['adjustment_factor'])}")

print("\n── B. graceful None + no-mutation ──")
check("B1 None/empty/non-list → None", _keystone_neighbours(None) is None
      and _keystone_neighbours([]) is None and _keystone_neighbours('x') is None)
check("B2 areas with no transactions / missing name / missing adj → skipped → None",
      _keystone_neighbours([{'name': 'X', 'location_adjustment': 1.0, 'transactions': []},
                            {'name': 'Y', 'transactions': [_geo('Y', 600, 3_000_000, 5000, '2025-01-01')]},
                            {'location_adjustment': 1.0, 'transactions': [_geo('Z', 600, 3_000_000, 5000, '2025-01-01')]}]) is None)
_before = [dict(t) for a in ACCEPTED for t in a['transactions']]
_keystone_neighbours(ACCEPTED)
_after = [t for a in ACCEPTED for t in a['transactions']]
check("B3 input transactions NOT mutated (builder derives into NEW rows)",
      all(b == a for b, a in zip(_before, _after)) and all('price_per_m2_adjusted' not in t for t in _after))

print("\n── C. value-invariance: neighbour block carries NO headline keys ──")
check("C1 no amount/low/high/method/rule/leadership keys on the neighbour block",
      not ({'amount', 'low', 'high', 'method', 'rule', 'leadership'} & set(kn.keys())))
# the b38/b40 builder is untouched by b41 (regression guard)
_mb = _keystone_comparables([{'date': '2025-12-17', 'area_m2': 444, 'total_price': 2_300_000, 'price_per_m2': 5180}],
                            n=37, window_used=None, basis='matched_bracket', pool_n=37)
check("C2 b38 _keystone_comparables(matched_bracket) still works + carries no `neighbours` key",
      isinstance(_mb, dict) and _mb.get('basis') == 'matched_bracket' and 'neighbours' not in _mb)

print("\n── D. evaluate_unified.py structural (geo-only nested attach; matched/cost-led untouched) ──")
_eu = open('evaluate_unified.py', encoding='utf-8').read()
check("D1 the neighbour attach is GATED on geo basis only (_kc_basis == 'geo_widened')",
      "if _kc_basis == 'geo_widened':" in _eu and "_keystone_neighbours(" in _eu)
check("D2 reads geo_v2['accepted_areas'] (the retained neighbour areas)",
      "(geo_v2_result or {}).get('accepted_areas')" in _eu)
check("D3 nested on the geo block as comparables.neighbours (NOT a 3rd top-level key)",
      "_kc['neighbours'] = _kn" in _eu)
check("D4 the b39 geo keystone gate is UNCHANGED (still leader=='market' + the widened methods)",
      "_gate['leader'] == 'market'" in _eu and "comparison_widened" in _eu
      and "output['valuation']['comparables'] = _kc" in _eu)
check("D5 the b40 cost-led considered key is UNCHANGED + distinct (no neighbours bleed)",
      "output['valuation']['considered_comparables'] = _cc" in _eu)
# the derive lives in the builder, not from the engine's throwaway all_adjusted_prices
check("D6 adjusted derived from DISPLAYED raw × DISPLAYED factor in the builder (value-invariant + self-consistent)",
      "_ppm_disp * _adj_disp" in _eu and "price_per_m2_adjusted" in _eu)

print("\n── E. index.html render (structural — E14 reads the REAL file) ──")
_html = open('index.html', encoding='utf-8').read()
# the neighbour block lives inside the geo branch of the comparables render, before the b40 considered block
_seg = _html.split('if(_kcGeo&&_kc.neighbours', 1)
check("E1 the neighbour render block exists", len(_seg) == 2)
_seg = _seg[1].split('if(v.considered_comparables', 1)[0]
check("E2 header «الصفقات المجاورة المُعدَّلة الموقع»", 'الصفقات المجاورة المُعدَّلة الموقع' in _seg)
check("E3 source-area shown (ic-pin icon) + ×adjustment factor",  # b48 de-emoji: 📍 → inline SVG #ic-pin
      '#ic-pin' in _seg and '\'+g.source_area' in _seg and '×\'+(g.adjustment_factor' in _seg)
check("E4 BOTH raw and adjusted ppm² shown (raw → adjusted)", 'g.price_per_m2_raw' in _seg and 'g.price_per_m2_adjusted' in _seg and '→' in _seg)
check("E5 honest disclosure: the neighbour did NOT sell for the adjusted number",
      'لم تُبَع بالرقم المُعدَّل' in _seg)
check("E6 the numeric line is dir=ltr (Rule #25 — bidi-safe), area name in its own RTL flow",
      'direction:ltr' in _seg)
check("E7 lives in the `how` buffer (value-invariant; never t1)", 'how+=' in _seg and 't1+=' not in _seg)

print(f"\n{'='*60}")
if _fails:
    print(f"RESULT: {len(_fails)} FAILED → {_fails}")
    sys.exit(1)
print("RESULT: ALL PASS")
