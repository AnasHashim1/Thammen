# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.38 — DEF-UX1 keystone comparables — isolated logic tests.

Exercises the PRODUCTION functions (Rule #40 / E14 — real engine, not a replica):
  - evaluate_unified._keystone_comparables   (the display-block builder + anonymization + cap)
  - moj_reference.build_reference(..., return_transactions=True)   (the subject-bracket rows)
  - evaluate_property.apply_moj_strategy      (carries MoJValuation.bracket_transactions)
  - evaluate_property.MoJValuation            (the additive field)
  + structural pins on evaluate_unified.py (Case 1 stash + the b4-region market-led gate)
  + structural pins on index.html (the render block, dir=ltr, CC BY source, lives in `how`)

CONTRACT: surfacing the comparables is DISPLAY-ONLY / VALUE-INVARIANT (the median already
drives the number) and PRIVACY-SAFE (E12 — the rows carry NO PIN / address / coordinates;
the PN-hash is stripped from the export). The keystone panel is attached/shown ONLY when the
MARKET led via the matched bracket (leader=='market' AND method=='comparison_bracket').

Run:  set PYTHONIOENCODING=utf-8  &&  python test_sprint_2_22_0b38.py
"""
import os
import sys
from datetime import datetime, timedelta

from moj_reference import build_reference, parse_date, DATE_COL
from evaluate_property import apply_moj_strategy, MoJValuation
from evaluate_unified import _keystone_comparables

_fails = []
def check(name, cond, detail=''):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  — {detail}" if detail and not cond else ''))
    if not cond:
        _fails.append(name)


def _row(area, area_m2, total, ppm2, date, ppft2=None, typ='فيلا', use='فلل او بيوت سكنية',
         muni='الريان'):
    return {
        'اسم المنطقة': area, 'اسم البلدية': muni, 'نوع العقار': typ, 'الاستخدام': use,
        'المساحة بالمتر المربع': str(area_m2), 'قيمة العقار': str(total),
        'سعر المتر المربع': str(ppm2), 'سعر القدم المربع': str(ppft2 if ppft2 else round(ppm2/10.7639, 2)),
        DATE_COL: date,
    }


# ── build a reliable villa bracket (n>=20, 400-600 m²) with spread dates/prices ──
AREA = 'حيّان'
_base = datetime(2025, 11, 1)
_rows = []
for i in range(25):
    d = (_base - timedelta(days=i * 20)).strftime('%Y-%m-%d')   # newest first by construction
    a = 450 + (i % 5) * 20          # all within 400-600
    ppm2 = 5000 + (i % 7) * 40
    tot = round(a * ppm2)
    _rows.append(_row(AREA, a, tot, ppm2, d))
# a couple of OTHER-bracket villa rows (900-1500) to prove bracket isolation
_rows.append(_row(AREA, 1000, 4_500_000, 4500, '2025-10-01'))
_rows.append(_row(AREA, 1100, 4_950_000, 4500, '2025-09-01'))
_max_d = max(d for d in (parse_date(r[DATE_COL]) for r in _rows) if d)

ref_tx = build_reference(_rows, AREA, _max_d, return_transactions=True)
ref_notx = build_reference(_rows, AREA, _max_d)   # default False
_vb = ref_tx['categories']['villa']['size_brackets']['400-600']
_vb_notx = ref_notx['categories']['villa']['size_brackets']['400-600']

print("\n── A. build_reference(return_transactions=True): subject-bracket rows + VALUE-INVARIANCE ──")
check("A1 subject bracket carries a 'transactions' list", isinstance(_vb.get('transactions'), list)
      and len(_vb['transactions']) >= 20, f"n={len(_vb.get('transactions') or [])}")
# A2 — VALUE-INVARIANT: every aggregate key is byte-identical with/without the flag
_agg_keys = ['n', 'total_price_median', 'price_per_m2_median', 'total_price_p25', 'total_price_p75',
             'price_per_m2_p25', 'price_per_m2_p75', 'n_24', 'n_36', 'total_price_median_24',
             'total_price_median_36', 'ppm2_dispersion_36', 'reliable']
_agg_same = all(_vb.get(k) == _vb_notx.get(k) for k in _agg_keys)
check("A2 aggregate outputs byte-identical with/without return_transactions (VALUE-INVARIANT)",
      _agg_same, str({k: (_vb.get(k), _vb_notx.get(k)) for k in _agg_keys if _vb.get(k) != _vb_notx.get(k)}))
check("A3 default (return_transactions=False) carries NO 'transactions' key",
      'transactions' not in _vb_notx)
# A4 — anonymity of the raw export: row keys carry no PIN/ref/address/coords
_rowkeys = set(_vb['transactions'][0].keys())
check("A4 raw row is ANONYMOUS (no PIN/property_ref/address/coords)",
      _rowkeys == {'date', 'area_m2', 'total_price', 'price_per_m2', 'price_per_ft2', 'type_ar'},
      str(_rowkeys))
check("A5 raw export carries no 'رقم العقار المرجعي' / property_ref / pin",
      not (_rowkeys & {'رقم العقار المرجعي', 'property_ref', 'pin', 'ref', 'lat', 'lon', 'address'}))
# A6 — newest-first
_dates = [t['date'] for t in _vb['transactions']]
check("A6 rows are newest-first (date desc)", _dates == sorted(_dates, reverse=True))

print("\n── B. _keystone_comparables (the display-block builder) ──")
check("B1 None/empty/non-list → None",
      _keystone_comparables(None, 5, None) is None
      and _keystone_comparables([], 5, None) is None
      and _keystone_comparables('x', 5, None) is None)
_blk = _keystone_comparables(_vb['transactions'], _vb['n'], None)
check("B2 returns a block with basis/n/shown/rows/source_ar", isinstance(_blk, dict)
      and _blk.get('basis') == 'matched_bracket' and _blk.get('n') == _vb['n']
      and isinstance(_blk.get('rows'), list) and _blk.get('source_ar'))
check("B3 caps at 8 (shown==8 when >8 rows)", _blk['shown'] == 8 and len(_blk['rows']) == 8)
# B4 — display rows anonymized to exactly {date, area_m2, total_price, price_per_m2}
_dk = set(_blk['rows'][0].keys())
check("B4 display row keys == {date, area_m2, total_price, price_per_m2} (no ft²/type/PIN)",
      _dk == {'date', 'area_m2', 'total_price', 'price_per_m2'}, str(_dk))
check("B5 source_ar cites «CC BY 4.0» + «وزارة العدل»",
      'CC BY 4.0' in _blk['source_ar'] and 'وزارة العدل' in _blk['source_ar'])
check("B6 date truncated to [:10]", all(len(r['date']) <= 10 for r in _blk['rows']))
check("B7 drops rows missing total or area",
      _keystone_comparables([{'date': '2025-01-01', 'area_m2': None, 'total_price': 1},
                             {'date': '2025-01-02', 'area_m2': 400, 'total_price': None}], 2, None) is None)
check("B8 window_label threaded through", _keystone_comparables(
      _vb['transactions'], 21, '21 معاملة، منها 14 خلال 24 شهراً')['window_label']
      == '21 معاملة، منها 14 خلال 24 شهراً')
check("B9 newest-first preserved in display rows",
      [r['date'] for r in _blk['rows']] == sorted([r['date'] for r in _blk['rows']], reverse=True))

print("\n── C. MoJValuation.bracket_transactions + apply_moj_strategy ──")
check("C1 MoJValuation has the additive bracket_transactions field",
      'bracket_transactions' in MoJValuation.__dataclass_fields__)
_mv_tx = apply_moj_strategy('standalone_villa', 500.0, ref_tx)
_mv_notx = apply_moj_strategy('standalone_villa', 500.0, ref_notx)
check("C2 apply_moj_strategy carries the subject-bracket rows (return_transactions path)",
      isinstance(_mv_tx.bracket_transactions, list) and len(_mv_tx.bracket_transactions) >= 20)
check("C3 apply_moj_strategy → bracket_transactions None when no rows broadcast (default path)",
      _mv_notx.bracket_transactions is None)
check("C4 apply_moj_strategy value byte-identical with/without the rows (VALUE-INVARIANT)",
      (_mv_tx.estimated_value_median == _mv_notx.estimated_value_median
       and _mv_tx.bracket_n == _mv_notx.bracket_n
       and _mv_tx.estimated_value_low == _mv_notx.estimated_value_low
       and _mv_tx.estimated_value_high == _mv_notx.estimated_value_high),
      f"med {_mv_tx.estimated_value_median} vs {_mv_notx.estimated_value_median}")

print("\n── D. evaluate_unified.py structural gating (the leader=='market' && comparison_bracket gate) ──")
_eu = open('evaluate_unified.py', encoding='utf-8').read()
check("D1 Case 1 stashes comparables from ev.valuation.bracket_transactions",
      "'comparables': getattr(ev.valuation, 'bracket_transactions', None)" in _eu)
# D2 — re-pointed at b39: the gate STILL requires leader=='market' and STILL includes comparison_bracket,
# but b39 broadened the method check to a set (comparison_bracket / _widened / _widened_indicative).
check("D2 b4-region attach gated on leader=='market' (comparison_bracket among the gated methods)",
      "_gate['leader'] == 'market'" in _eu
      and "'comparison_bracket'" in _eu
      and "output['valuation']['comparables'] = _kc" in _eu)
# D3 — re-pointed at b39: comparables now stashed in Case 1 (bracket) AND Cases 2-3 (geo widened),
# but NEVER in the thin/preliminary returns (Cases 4-5 — those never produced the market-led keystone).
_thin_seg = _eu.split("'method': 'comparison_thin'", 1)[1].split('\ndef ', 1)[0]
check("D3 comparables NOT stashed in the thin/preliminary returns (Cases 4-5)",
      "'comparables'" not in _thin_seg)
check("D4 the attach reads primary.get('comparables') (the stashed rows)",
      "primary.get('comparables')" in _eu and "_keystone_comparables(" in _eu)

print("\n── E. index.html render (structural — E14 reads the REAL file) ──")
_html = open('index.html', encoding='utf-8').read()
check("E1 render block gated on v.comparables.rows.length",
      'if(v.comparables&&v.comparables.rows&&v.comparables.rows.length){' in _html)
check("E2 keystone header «هي ما قرّر رقمك»", 'هي ما قرّر رقمك' in _html)
check("E3 numeric rows in a dir=ltr table (Rule #25)",
      'direction:ltr' in _html.split('if(v.comparables', 1)[1].split('// Sprint 2.22.0b.18', 1)[0])
check("E4 renders the CC BY 4.0 source line (_kc.source_ar)",
      '_kc.source_ar' in _html)
# E5 — lives in `how` (the b31 accordion) → density-gated + value-invariant (NOT t1).
# Scope to the keystone block only (it ends right before the b18 age-sensitivity line).
_seg = _html.split('if(v.comparables', 1)[1].split('// Sprint 2.22.0b.18', 1)[0]
check("E5 appends to `how` (b31 accordion), not t1 (value-invariant, density-gated)",
      'how+=' in _seg and 't1+=' not in _seg)
check("E6 window_label surfaced when present", '_kc.window_label' in _html)
check("E7 'shown of n' disclosure when capped", '_kc.shown' in _html and '_kc.n' in _html)

print("\n── F. privacy contract (E12) — end-to-end anonymity ──")
_e2e = _keystone_comparables(_mv_tx.bracket_transactions, _mv_tx.bracket_n, None)
_e2e_keys = set().union(*[set(r.keys()) for r in _e2e['rows']])
check("F1 end-to-end display rows carry NO identifying keys",
      _e2e_keys == {'date', 'area_m2', 'total_price', 'price_per_m2'}
      and not (_e2e_keys & {'pin', 'property_ref', 'رقم العقار المرجعي', 'address', 'lat', 'lon'}),
      str(_e2e_keys))

print(f"\n{'='*60}")
if _fails:
    print(f"RESULT: {len(_fails)} FAILED → {_fails}")
    sys.exit(1)
print("RESULT: ALL PASS")
