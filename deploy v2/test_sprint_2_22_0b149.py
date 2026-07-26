# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.149 — «الوسيط الأعمى عن المساحة في الأراضي» (land size-aware fallback)

🔴 Gate-2 VALUE-AFFECTING (raw_land, empty-bracket subjects only).

THE DEFECT (measured live on b147, PIN 70312306 / سميسمة, plot 1500 m²):
  when the subject's SIZE BRACKET is empty, apply_moj_strategy fell back to the
  area-wide `total_price.median` — the median SALE PRICE of the pool (dominated by
  400-900 m² plots) — and the headline read it verbatim. A 1500 m² plot was valued
  at 1,515,002 (= 93 ر.ق/قدم²) while the same pool's ppm² median implies 4,681,500
  (= 290 ر.ق/قدم²). Worse, the DISPLAYED RANGE endpoints already used the
  size-aware `plot × ppm² quartiles`, so the number sat OUTSIDE its own range and
  the b59 clamp dragged `low` onto it (masking the split basis, not fixing it).

THE FIX: in the empty-bracket fallback, LAND leads with `plot_area × ppm² median`
  → the headline shares ONE basis with its own range (and equals est_median).

SCOPE (measured, not preferred): LAND ONLY. Land is market-only (b20 emits
  DRC ≡ land value) so the fix is self-contained. The villa pool has the SAME
  defect (95 of 288 (area,bracket) probes, up to 7.07×) but a villa market median
  feeds the b20 leadership gate + the E25 rail → its own signed sprint.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b149.py
"""
import csv, re, sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))

import moj_reference as MR
from evaluate_property import apply_moj_strategy, MoJValuation
from evaluate_unified import _select_primary_comparison, ENGINE_VERSION, SPRINT_TAG

PASS = FAIL = 0
def ck(cond, label, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f'  [PASS] {label}')
    else:
        FAIL += 1; print(f'  [FAIL] {label}' + (f'  -> {detail}' if detail else ''))

FT = 10.7639

# ── synthetic references (deterministic, no CSV needed) ───────────────────────
def mk_ref(cat, cat_n, cat_ppm2, cat_total, brackets):
    """A moj_reference-shaped dict with explicit category + bracket stats."""
    return {'area': 'T', 'categories': {cat: {
        'n': cat_n,
        'price_per_m2': {'p25': cat_ppm2 * 0.9, 'median': cat_ppm2, 'p75': cat_ppm2 * 1.1},
        'total_price':  {'p25': cat_total * 0.9, 'median': cat_total, 'p75': cat_total * 1.1},
        'size_brackets': brackets,
    }}}

EMPTY_1500 = {'400-600': {'n': 20, 'price_per_m2_median': 3000, 'total_price_median': 1_500_000,
                          'price_per_m2_p25': 2700, 'price_per_m2_p75': 3300,
                          'total_price_p25': 1_350_000, 'total_price_p75': 1_650_000}}
POP_1500 = dict(EMPTY_1500, **{'1500-99999': {'n': 24, 'price_per_m2_median': 2500,
                                              'total_price_median': 3_900_000,
                                              'price_per_m2_p25': 2200, 'price_per_m2_p75': 2800,
                                              'total_price_p25': 3_400_000, 'total_price_p75': 4_400_000}})

print('\n=== A. LAND, EMPTY subject bracket — the fix fires ===')
land_ref = mk_ref('land', 26, 3121.0, 1_515_002.0, EMPTY_1500)
v = apply_moj_strategy('raw_land', 1500.0, land_ref)
ck(v.bracket_fallback is True, 'A1 bracket_fallback flag set on the empty-bracket path')
ck(abs(v.moj_median_total - 1500.0 * 3121.0) < 1,
   'A2 total = plot x category ppm2 median (size-AWARE)', f'got {v.moj_median_total}')
ck(abs(v.moj_median_total - 1_515_002.0) > 1,
   'A3 total is NOT the size-blind category total median', f'got {v.moj_median_total}')
ck(abs(v.moj_median_total - v.estimated_value_median) < 1,
   'A4 basis UNIFIED: moj_median_total == estimated_value_median',
   f'{v.moj_median_total} vs {v.estimated_value_median}')
ck(v.estimated_value_low <= v.moj_median_total <= v.estimated_value_high,
   'A5 low <= value <= high WITHOUT the b59 clamp (the split basis is gone)',
   f'{v.estimated_value_low} / {v.moj_median_total} / {v.estimated_value_high}')
ck(abs(v.moj_median_per_m2 - 3121.0) < 1e-6, 'A6 ppm2 median untouched by the fix')
_before_ft = 1_515_002.0 / 1500.0 / FT
_after_ft = v.moj_median_total / 1500.0 / FT
ck(_before_ft < 100 < _after_ft,
   'A7 the reported symptom is cured (93 -> ~290 ر.ق/قدم2)',
   f'{_before_ft:.0f} -> {_after_ft:.0f}')
ck(any('b149' in n for n in v.notes), 'A8 the basis change is disclosed in notes')

print('\n=== B. LAND, POPULATED bracket — byte-identical (no b149 effect) ===')
land_pop = mk_ref('land', 26, 3121.0, 1_515_002.0, POP_1500)
vp = apply_moj_strategy('raw_land', 1500.0, land_pop)
ck(vp.bracket_fallback is False, 'B1 flag stays False when the bracket has data')
ck(abs(vp.moj_median_total - 3_900_000) < 1,
   'B2 total = the BRACKET total median (unchanged behaviour)', f'got {vp.moj_median_total}')
ck(not any('b149' in n for n in vp.notes), 'B3 no b149 note on the untouched path')
vs = apply_moj_strategy('raw_land', 500.0, land_pop)
ck(abs(vs.moj_median_total - 1_500_000) < 1 and vs.bracket_fallback is False,
   'B4 in-bracket small plot unchanged', f'got {vs.moj_median_total}')

print('\n=== C. VILLA — same defect, DELIBERATELY out of scope (deferred) ===')
villa_ref = mk_ref('villa', 30, 4000.0, 2_300_000.0, EMPTY_1500)
vv = apply_moj_strategy('standalone_villa', 2000.0, villa_ref)
ck(vv.bracket_fallback is True, 'C1 the flag fires for villa too (honest signal)')
ck(abs(vv.moj_median_total - 2_300_000.0) < 1,
   'C2 villa total is NOT changed by b149 (land-only gate)', f'got {vv.moj_median_total}')
ck(not any('b149' in n for n in vv.notes), 'C3 no b149 note on the villa path')

print('\n=== D. guards — never crash, never invent ===')
no_ppm2 = {'area': 'T', 'categories': {'land': {
    'n': 12, 'price_per_m2': {}, 'total_price': {'median': 900_000},
    'size_brackets': {'400-600': {'n': 5, 'price_per_m2_median': 3000}}}}}
vg = apply_moj_strategy('raw_land', 1500.0, no_ppm2)
ck(abs((vg.moj_median_total or 0) - 900_000) < 1,
   'D1 no category ppm2 -> falls back to the old total (no crash, no invention)')
vz = apply_moj_strategy('raw_land', 0.0, land_ref)
ck(vz is not None, 'D2 plot_area 0 does not crash')
ck(MoJValuation.__dataclass_fields__['bracket_fallback'].default is False,
   'D3 bracket_fallback defaults False (old constructors unaffected)')
empty = apply_moj_strategy('raw_land', 1500.0, {'area': 'T', 'categories': {}})
ck(empty.moj_median_total is None and empty.bracket_fallback is False,
   'D4 empty reference still refuses cleanly')

print('\n=== E. source honesty — never claim «نفس الشريحة» for an out-of-bracket subject ===')
def primary_for(val):
    ev = SimpleNamespace(valuation=val)
    return _select_primary_comparison(ev, None)

p_fb = primary_for(v)      # land, fallback
p_ok = primary_for(vp)     # land, populated bracket
ck(p_fb is not None and 'نفس الشريحة' not in p_fb['source_ar'],
   'E1 fallback source drops the false «نفس الشريحة» claim', p_fb and p_fb['source_ar'])
ck(p_fb and 'لا صفقات مسجَّلة في شريحة مساحته' in p_fb['source_ar'],
   'E2 fallback source states the real basis (area ppm2 x the subject area)')
ck(p_ok and 'نفس الشريحة' in p_ok['source_ar'],
   'E3 the genuine same-bracket wording is PRESERVED', p_ok and p_ok['source_ar'])
ck(p_fb and abs(p_fb['value'] - v.moj_median_total) < 1,
   'E4 the headline carries the size-aware value')
ck(p_fb and p_fb['low'] <= p_fb['value'] <= p_fb['high'],
   'E5 headline sits INSIDE its own range', p_fb and (p_fb['low'], p_fb['value'], p_fb['high']))

print('\n=== F. real MoJ data (E14 — the production pool, not a fixture) ===')
csv_path = Path(__file__).parent / 'moj_weekly.csv'
if csv_path.exists():
    rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig')))
    maxd = max(d for d in (MR.parse_date(r[MR.DATE_COL]) for r in rows) if d)

    r_sm = MR.build_reference(rows, 'سميسمة', maxd)
    v_sm = apply_moj_strategy('raw_land', 1500.0, r_sm)
    ck(v_sm.bracket_fallback is True and v_sm.moj_median_total > 4_000_000,
       'F1 THE REPORTED CASE سميسمة/1500 m2 -> size-aware (was 1,515,002)',
       f'got {v_sm.moj_median_total:,.0f}')
    ck(abs(v_sm.moj_median_total - v_sm.estimated_value_median) < 1,
       'F2 real-data basis unified (total == est_median)')

    r_wb = MR.build_reference(rows, 'الوعب', maxd)
    v_wb = apply_moj_strategy('raw_land', 1219.0, r_wb)
    ck(v_wb.bracket_fallback is False and abs(v_wb.moj_median_total - 5_326_000) < 1,
       'F3 LAND FIXTURE الوعب/1219 (b118 5.7M) byte-identical', f'got {v_wb.moj_median_total:,.0f}')

    r_kh = MR.build_reference(rows, 'الخور', maxd)
    v_kh = apply_moj_strategy('raw_land', 900.0, r_kh)
    ck(v_kh.bracket_fallback is False, 'F4 LAND FIXTURE الخور/900 unaffected (populated bracket)')

    for area, plot, tot in [('مريخ', 613.0, 5_100_000), ('المعمورة', 652.0, 3_741_176),
                            ('المعراض', 900.0, 2_432_778), ('بو هامور', 450.0, 2_357_895)]:
        rr = MR.build_reference(rows, area, maxd)
        vf = apply_moj_strategy('standalone_villa', plot, rr)
        ck(vf.bracket_fallback is False and abs(vf.moj_median_total - tot) < 1,
           f'F5 VILLA FIXTURE {area}/{plot:.0f} byte-identical', f'got {vf.moj_median_total}')
else:
    print('  [SKIP] moj_weekly.csv not present')

print('\n=== G. value-invariance contract + version ===')
src_ep = Path('evaluate_property.py').read_text(encoding='utf-8')
src_eu = Path('evaluate_unified.py').read_text(encoding='utf-8')
ck("moj_cat == 'land'" in src_ep and 'total_median = plot_area_m2 * per_m2' in src_ep,
   'G1 the fix is gated on the LAND category at the fallback site')
ck('bracket_fallback=bracket_fallback' in src_ep, 'G2 the flag is threaded into MoJValuation')
ck(Path('api.py').read_text(encoding='utf-8').find('b149') == -1,
   'G3 api.py UNTOUCHED by b149')
ck('_bfb' in src_eu and 'bracket_fallback' in src_eu,
   'G4 the source line reads the flag (no strategy-string matching)')
ck(ENGINE_VERSION.startswith('thammen-sprint2p22p0b1') and re.match(r'^\d+\.\d+\.\d+', SPRINT_TAG),
   'G5 version format (version-agnostic per Lesson-2)', f'{ENGINE_VERSION} / {SPRINT_TAG}')

print(f'\n{"=" * 60}\n  b149: {PASS} passed, {FAIL} failed\n{"=" * 60}')
sys.exit(1 if FAIL else 0)
