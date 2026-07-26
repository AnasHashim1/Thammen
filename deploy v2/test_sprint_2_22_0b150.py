# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.150 — «فرع الرجوع في الفلل» (villa size-aware fallback)

🔴 Gate-2 VALUE-AFFECTING, PO-signed BIDIRECTIONAL.

b149 fixed the size-blind empty-bracket fallback for LAND. b150 extends the SAME fix
to the VILLA pool after measuring the blast radius the villa deferral was waiting on:
95 affected (area,bracket) cells — 81 UP (median 2.67x, max 7.07x), 14 DOWN
(median 0.69x, min 0.06x).

WHY BIDIRECTIONAL: the defect is a size-blind SALE-PRICE median. It UNDER-states a big
plot in a small-plot pool AND OVER-states a small plot in a big-plot pool — one error,
two directions. The downward cases are corrections: جليعة carried a 61,800,000 category
total median (from ONE sale) applied to a 750 m² villa -> the size-aware basis is 3,776,250.

DOWNWARD EXPOSURE IS THIN (measured): 0 of the 14 reach cat_n >= 20 (so none becomes a
confident Case-1 headline); only 3 reach n >= 5 (روضة الحمامة 15 · لوسيل 69 12 ·
مدينة الشمال 7), where the headline is already comparison_thin/preliminary + caveated.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b150.py
"""
import csv, re, sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))

import moj_reference as MR
from evaluate_property import apply_moj_strategy
from evaluate_unified import (_select_primary_comparison, _leadership_gate,
                              ENGINE_VERSION, SPRINT_TAG)

PASS = FAIL = 0
def ck(cond, label, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f'  [PASS] {label}')
    else:
        FAIL += 1; print(f'  [FAIL] {label}' + (f'  -> {detail}' if detail else ''))

def mk_ref(cat, cat_n, cat_ppm2, cat_total, brackets):
    return {'area': 'T', 'categories': {cat: {
        'n': cat_n,
        'price_per_m2': {'p25': cat_ppm2 * 0.9, 'median': cat_ppm2, 'p75': cat_ppm2 * 1.1},
        'total_price':  {'p25': cat_total * 0.9, 'median': cat_total, 'p75': cat_total * 1.1},
        'size_brackets': brackets,
    }}}

# a populated SMALL bracket only -> a 2000 m² subject hits the empty-bracket fallback
SMALL_ONLY = {'400-600': {'n': 22, 'price_per_m2_median': 5000, 'total_price_median': 2_500_000,
                          'price_per_m2_p25': 4500, 'price_per_m2_p75': 5500,
                          'total_price_p25': 2_200_000, 'total_price_p75': 2_800_000}}

print('\n=== A. VILLA, empty bracket, UPWARD (small-plot pool, big subject) ===')
# category ppm2 5,040 x 2000 m² = 10,080,000 vs a size-blind 2,154,544 (the ام صلال محمد shape)
up_ref = mk_ref('villa', 20, 5040.0, 2_154_544.0, SMALL_ONLY)
vu = apply_moj_strategy('standalone_villa', 2000.0, up_ref)
ck(vu.bracket_fallback is True, 'A1 fallback flag set for the villa path')
ck(abs(vu.moj_median_total - 2000.0 * 5040.0) < 1,
   'A2 villa total is now size-AWARE (b150 — was blind under b149)', f'got {vu.moj_median_total}')
ck(abs(vu.moj_median_total - vu.estimated_value_median) < 1,
   'A3 basis unified with the range (total == est_median)')
ck(vu.estimated_value_low <= vu.moj_median_total <= vu.estimated_value_high,
   'A4 headline inside its own range without the b59 clamp')
ck(any('b150' in n or 'b149' in n for n in vu.notes), 'A5 the basis change is disclosed in notes')

print('\n=== B. VILLA, empty bracket, DOWNWARD (big-plot pool, small subject) ===')
# the جليعة shape: a 61.8M category total median (ONE sale) applied to a 750 m² villa
dn_ref = mk_ref('villa', 1, 5035.0, 61_800_000.0,
                {'1500-99999': {'n': 12, 'price_per_m2_median': 4000, 'total_price_median': 9_000_000,
                                'price_per_m2_p25': 3600, 'price_per_m2_p75': 4400,
                                'total_price_p25': 8_000_000, 'total_price_p75': 10_000_000}})
vd = apply_moj_strategy('standalone_villa', 750.0, dn_ref)
ck(vd.bracket_fallback is True, 'B1 fallback flag set on the downward shape')
ck(abs(vd.moj_median_total - 750.0 * 5035.0) < 1,
   'B2 the size-blind 61,800,000-on-a-750m2-villa is CORRECTED downward',
   f'got {vd.moj_median_total}')
ck(vd.moj_median_total < 61_800_000.0,
   'B3 downward IS expected here — the fix is bidirectional by design')
ck(abs(vd.moj_median_total - vd.estimated_value_median) < 1,
   'B4 downward case is basis-unified too')

print('\n=== C. LAND unchanged by b150 (b149 behaviour preserved) ===')
land_ref = mk_ref('land', 26, 3121.0, 1_515_002.0, SMALL_ONLY)
vl = apply_moj_strategy('raw_land', 1500.0, land_ref)
ck(abs(vl.moj_median_total - 1500.0 * 3121.0) < 1 and vl.bracket_fallback is True,
   'C1 land still size-aware (b149 intact)', f'got {vl.moj_median_total}')

print('\n=== D. populated bracket — byte-identical for BOTH categories ===')
POP = dict(SMALL_ONLY, **{'1500-99999': {'n': 24, 'price_per_m2_median': 4000,
                                         'total_price_median': 7_600_000,
                                         'price_per_m2_p25': 3600, 'price_per_m2_p75': 4400,
                                         'total_price_p25': 7_000_000, 'total_price_p75': 8_400_000}})
for cat, at in [('villa', 'standalone_villa'), ('land', 'raw_land')]:
    vpop = apply_moj_strategy(at, 2000.0, mk_ref(cat, 30, 4000.0, 5_000_000.0, POP))
    ck(vpop.bracket_fallback is False and abs(vpop.moj_median_total - 7_600_000) < 1,
       f'D1 {cat}: populated bracket untouched', f'got {vpop.moj_median_total}')

print('\n=== E. leadership consequences (the PURE b20 gate) ===')
COST = 3_400_000.0
def gate(amount, cost_value=COST, geo=None, matched=None):
    return _leadership_gate(amount=amount, asset_type='standalone_villa',
                            matched_n=matched, disp36=(0.20 if matched else 0.9),
                            stratum_match=bool(matched), band=None, resurvey=False,
                            geo_full=geo or {'n_full': 5, 'dispersion_full': 0.9},
                            cost={'value': cost_value} if cost_value else {},
                            land_floor=1_000_000)
def headline(d):
    return d['market_value'] if d['leader'] == 'market' else d['cost_value']

# E1 the leader CHOICE never depends on the market value (n + dispersion only)
d_lo, d_hi = gate(2_300_000.0), gate(10_080_000.0)
ck(gate(2_300_000.0, matched=15)['rule'] == gate(10_080_000.0, matched=15)['rule'] == 'matched',
   'E1 RULE 1 decision is value-independent (gates on n + dispersion)')
# E2 market-led -> the headline follows the corrected market figure
ck(headline(gate(10_080_000.0, matched=15)) > headline(gate(2_300_000.0, matched=15)),
   'E2 market-led: the corrected (higher) median raises the headline')
# E3 cost_led stays byte-identical while the market rises (only the muted high moves)
d_cl0, d_cl1 = gate(2_300_000.0, cost_value=1_800_000.0), gate(10_080_000.0, cost_value=1_800_000.0)
ck(d_cl0['rule'] == d_cl1['rule'] == 'cost_led' and abs(headline(d_cl0) - headline(d_cl1)) < 1,
   'E3 cost_led headline byte-identical when the market rises', f'{headline(d_cl0)} / {headline(d_cl1)}')
ck(d_cl1['high'] > d_cl0['high'], 'E4 ... only the muted market ceiling moves')
# E5 the e25 flip is REAL and must be disclosed: market rising above cost flips e25 -> cost_led
ck(gate(2_300_000.0)['rule'] == 'e25_capped' and gate(10_080_000.0)['rule'] == 'cost_led',
   'E5 e25_capped -> cost_led when the corrected market exceeds the cost')
ck(headline(gate(10_080_000.0)) == COST,
   'E6 ... and the headline is then the COST (never the raw market) — the E25 rail holds')
# E7 the DOWNWARD direction can flip cost_led -> e25_capped (headline drops to the market)
d_dn0 = gate(10_000_000.0, cost_value=6_000_000.0)      # cost < market -> cost_led
d_dn1 = gate(5_823_000.0, cost_value=6_000_000.0)       # corrected market < cost -> e25
ck(d_dn0['rule'] == 'cost_led' and d_dn1['rule'] == 'e25_capped',
   'E7 downward correction can flip cost_led -> e25_capped (measured, disclosed)')
ck(headline(d_dn1) < headline(d_dn0),
   'E8 ... and that flip LOWERS the headline — the honest direction of a downward correction')
ck(d_dn1.get('divergence') is True and d_dn1.get('muc_min_high') is True,
   'E9 ... the e25 path still carries divergence + MUC>=high (disclosure intact)')

print('\n=== F. real MoJ data (E14) — fixtures byte-identical, affected cells move ===')
csv_path = Path(__file__).parent / 'moj_weekly.csv'
if csv_path.exists():
    rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig')))
    maxd = max(d for d in (MR.parse_date(r[MR.DATE_COL]) for r in rows) if d)
    for area, plot, tot in [('مريخ', 613.0, 5_100_000), ('المعمورة', 652.0, 3_741_176),
                            ('المعراض', 900.0, 2_432_778), ('بو هامور', 450.0, 2_357_895)]:
        rr = MR.build_reference(rows, area, maxd)
        vf = apply_moj_strategy('standalone_villa', plot, rr)
        ck(vf.bracket_fallback is False and abs(vf.moj_median_total - tot) < 1,
           f'F1 VILLA FIXTURE {area}/{plot:.0f} byte-identical', f'got {vf.moj_median_total}')
    # an upward affected cell (cat_n >= 20 -> can become a Case-1 headline)
    r_mt = MR.build_reference(rows, 'المطار العتيق', maxd)
    v_mt = apply_moj_strategy('standalone_villa', 2000.0, r_mt)
    ck(v_mt.bracket_fallback is True and v_mt.moj_median_total > 5_000_000,
       'F2 المطار العتيق/2000 (n=50) corrected upward', f'got {v_mt.moj_median_total:,.0f}')
    # the land side still works (b149 regression guard on real data)
    r_sm = MR.build_reference(rows, 'سميسمة', maxd)
    v_sm = apply_moj_strategy('raw_land', 1500.0, r_sm)
    ck(v_sm.bracket_fallback is True and v_sm.moj_median_total > 4_000_000,
       'F3 b149 land case still corrected (no regression)', f'got {v_sm.moj_median_total:,.0f}')
else:
    print('  [SKIP] moj_weekly.csv not present')

print('\n=== G. scope + version ===')
src = Path('evaluate_property.py').read_text(encoding='utf-8')
ck("if moj_cat == 'land' and per_m2" not in src,
   'G1 the land-only gate is gone (b150 covers both pools)')
ck('total_median = plot_area_m2 * per_m2' in src, 'G2 the size-aware assignment is present')
ck('b150' in src, 'G3 the b150 rationale is documented at the site')
ck(Path('api.py').read_text(encoding='utf-8').find('b150') == -1, 'G4 api.py UNTOUCHED')
ck(Path('index.html').read_text(encoding='utf-8').find('b150') == -1, 'G5 index.html UNTOUCHED')
ck(ENGINE_VERSION.startswith('thammen-sprint2p22p0b1') and re.match(r'^\d+\.\d+\.\d+', SPRINT_TAG),
   'G6 version format (version-agnostic per Lesson-2)', f'{ENGINE_VERSION} / {SPRINT_TAG}')

print(f'\n{"=" * 60}\n  b150: {PASS} passed, {FAIL} failed\n{"=" * 60}')
sys.exit(1 if FAIL else 0)
