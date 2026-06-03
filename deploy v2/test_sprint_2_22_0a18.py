# -*- coding: utf-8 -*-
"""
Sprint 2.22.0a.18 — bracket-path area-name reconciliation (R9) — isolated logic tests.

Exercises the PRODUCTION functions (Rule #40 / E14 — real engine, not a replica):
  - moj_reference.area_match_key       (aggregate pooling key: hamza-fold + zone-sibling strip)
  - moj_reference.build_reference      (pools district + zone-number siblings)
  - moj_reference.categorize           (type path MUST stay UNFOLDED — 'أرض فضاء')
  - evaluate_property.resolve_moj_area_name / _candidate_moj_names / GIS_TO_MOJ_NAME_OVERRIDES

Design: pooling re-architected from highest-count-wins (which regressed rich
sub-zones — see Session_Log §20.18) to SIBLING AGGREGATION. «معيذر», «معيذر 53»,
«معيذر 55» pool into one district (the zone-number is an addressing artifact; MoJ
files recent txns under the sub-zone label and older ones under the bare parent,
so the aggregate recovers BOTH). Valuation logic downstream of resolution is
unchanged; the dispersion gate (a14) still fires on the aggregate.

Run:  set PYTHONIOENCODING=utf-8  &&  python test_sprint_2_22_0a18.py
"""
import os
import sys

from moj_reference import area_match_key, build_reference, categorize, parse_date
from evaluate_property import (
    resolve_moj_area_name,
    _candidate_moj_names,
    GIS_TO_MOJ_NAME_OVERRIDES,
)

_fails = []
def check(name, cond, detail=''):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  — {detail}" if detail and not cond else ''))
    if not cond:
        _fails.append(name)


def _row(area, area_m2, total, ppm2, date='2025-08-01', typ='فيلا', use='فلل او بيوت سكنية'):
    return {
        'اسم المنطقة': area, 'نوع العقار': typ, 'الاستخدام': use,
        'المساحة بالمتر المربع': str(area_m2), 'قيمة العقار': str(total),
        'سعر المتر المربع': str(ppm2), 'سعر القدم المربع': str(round(ppm2 / 10.7639)),
        'تاريخ\xa0التثبيت': date, 'اسم البلدية': 'الدوحة',
    }


# ── 1. area_match_key: zone-sibling aggregation + hamza fold + NBSP, type-safe ──
print("1. area_match_key (aggregate pooling key)")
check("zone siblings collapse to one key",
      area_match_key('معيذر 53') == area_match_key('معيذر') == area_match_key('معيذر 55') == 'معيذر',
      f"{area_match_key('معيذر 53')!r}")
check("hamza folds (أ/إ/آ → ا)", area_match_key('أم بشر') == area_match_key('ام بشر') == 'ام بشر')
check("NBSP / whitespace collapses", area_match_key('بو\xa0هامور') == 'بو هامور')
check("distinct districts do NOT merge", area_match_key('معيذر 53') != area_match_key('نعيجة 44'))
check("multi-digit & multi-word stems", area_match_key('فريج بن محمود 22') == 'فريج بن محمود')
check("empty / None safe", area_match_key('') == '' and area_match_key(None) == '')


# ── 2. _candidate_moj_names: verbatim + ال drop/add + override (no stray stem) ──
print("2._candidate_moj_names")
c = _candidate_moj_names('امريخ الجنوبي')
check("override candidate present (امريخ الجنوبي→مريخ)", 'مريخ' in c)
check("verbatim present", 'امريخ الجنوبي' in c)
check("empty input → []", _candidate_moj_names('') == [])
cc = _candidate_moj_names('الغرافة')
check("ال-drop variant present", 'الغرافة' in cc and 'غرافة' in cc)


# ── 3. SIBLING AGGREGATION via build_reference + resolve (synthetic, deterministic) ──
print("3. sibling aggregation (build_reference + resolve)")
agg_rows = (
    [_row('حيّان', 500, 2_000_000, 4000) for _ in range(5)]       # bare parent (older-ish)
    + [_row('حيّان 53', 520, 2_200_000, 4200) for _ in range(4)]   # zone sibling
    + [_row('حيّان 55', 480, 1_900_000, 3900) for _ in range(3)]   # zone sibling
)
res = resolve_moj_area_name(agg_rows, 'حيّان 53')
check("resolve(sub-zone) → district stem key", res is not None and res[0] == 'حيّان', f"{res}")
check("resolve count = AGGREGATE (5+4+3=12), not the single label (4)",
      res is not None and res[1] == 12, f"{res}")
br = build_reference(agg_rows, 'حيّان', max(d for d in (parse_date(r['تاريخ\xa0التثبيت']) for r in agg_rows) if d))
n_400_600 = (br.get('categories', {}).get('villa', {}).get('size_brackets', {}).get('400-600', {}) or {}).get('n')
check("build_reference pools all siblings (n=12 in 400-600)", n_400_600 == 12, f"n={n_400_600}")
# calling build_reference with a sibling label yields the SAME aggregate
br2 = build_reference(agg_rows, 'حيّان 55', max(d for d in (parse_date(r['تاريخ\xa0التثبيت']) for r in agg_rows) if d))
n2 = (br2.get('categories', {}).get('villa', {}).get('size_brackets', {}).get('400-600', {}) or {}).get('n')
check("build_reference(sibling) == same aggregate pool", n2 == 12, f"n={n2}")


# ── 4. OVERRIDE routing (A16 + preserved originals) ──
print("4. overrides")
ov_rows = [_row('مريخ', 700, 5_000_000, 7000) for _ in range(6)] + [_row('امريخ الجنوبي', 700, 4_000_000, 5700) for _ in range(2)]
r_marikh = resolve_moj_area_name(ov_rows, 'امريخ الجنوبي')
check("A16: GIS «امريخ الجنوبي» resolves to «مريخ»", r_marikh is not None and r_marikh[0] == 'مريخ', f"{r_marikh}")
bh_rows = [_row('بو هامور', 450, 2_400_000, 5300) for _ in range(7)]
r_bh = resolve_moj_area_name(bh_rows, 'أبو هامور')
check("original override preserved (أبو هامور→بو هامور)", r_bh is not None and r_bh[0] == 'بو هامور', f"{r_bh}")
check("override dict keeps A16 + drops inert المطار العتيق",
      GIS_TO_MOJ_NAME_OVERRIDES.get('امريخ الجنوبي') == 'مريخ' and 'المطار العتيق' not in GIS_TO_MOJ_NAME_OVERRIDES)


# ── 5. NEGATIVE ASSERT — لجميل (Lejmail) must NEVER resolve to لجميليه ──
print("5. negative assert (لجميل ≠ لجميليه)")
check("area_match_key keeps لجميل / لجميليه distinct", area_match_key('لجميل') != area_match_key('لجميليه'))
lj_rows = [_row('لجميليه', 700, 1_200_000, 1700) for _ in range(4)] + [_row('لجميل', 700, 3_000_000, 4300) for _ in range(3)]
r_lj = resolve_moj_area_name(lj_rows, 'لجميل')
check("resolve('لجميل') does NOT return لجميليه", r_lj is None or r_lj[0] != 'لجميليه', f"{r_lj}")
check("override لجمليه→لجميليه does not touch لجميل", GIS_TO_MOJ_NAME_OVERRIDES.get('لجميل') is None)


# ── 6. NO-REGRESSION (no siblings) + fallback ──
print("6. no-regression + fallback")
solo = [_row('سدرة', 450, 2_500_000, 5500) for _ in range(6)]
r_solo = resolve_moj_area_name(solo, 'سدرة')
check("solo district (no siblings) resolves to itself, exact count", r_solo == ('سدرة', 6), f"{r_solo}")
check("unknown area → None", resolve_moj_area_name(solo, 'لا_يوجد_هذا') is None)


# ── 7. categorize stays UNFOLDED (type path must not hamza-fold 'أرض فضاء') ──
print("7. categorize type-path unfolded")
check("categorize 'أرض فضاء' → land (NOT folded)", categorize({'نوع العقار': 'أرض فضاء'}) == 'land')
check("categorize 'فيلا' → villa", categorize({'نوع العقار': 'فيلا'}) == 'villa')


# ── 8. dispersion gate (a14) still fires on the aggregate where dispersed ──
print("8. dispersion gate on aggregate")
disp_rows = (
    [_row('متبعثر', 700, 3_000_000, 3000) for _ in range(3)]
    + [_row('متبعثر 9', 700, 7_000_000, 7000) for _ in range(3)]   # wide ppm² spread across siblings
    + [_row('متبعثر', 700, 5_000_000, 5000) for _ in range(3)]
)
md = max(d for d in (parse_date(r['تاريخ\xa0التثبيت']) for r in disp_rows) if d)
bd = build_reference(disp_rows, 'متبعثر', md)
cell = (bd.get('categories', {}).get('villa', {}).get('size_brackets', {}).get('600-900', {}) or {})
disp = cell.get('ppm2_dispersion_36')
check("aggregate bracket exposes ppm2_dispersion_36", disp is not None, f"{cell}")
check("dispersed aggregate gates (disp ≥ 0.30)", disp is not None and disp >= 0.30, f"disp={disp}")


# ── 9. REAL MoJ data (guarded) — aggregate ≥ any single label; Abu Hamour unchanged ──
print("9. real moj_weekly.csv (guarded)")
if os.path.exists('moj_weekly.csv'):
    import csv
    rows = list(csv.DictReader(open('moj_weekly.csv', encoding='utf-8-sig')))
    r_mz = resolve_moj_area_name(rows, 'معيذر 53')
    check("REAL: معيذر 53 → معيذر aggregate (n≥700)", r_mz is not None and r_mz[0] == 'معيذر' and r_mz[1] >= 700, f"{r_mz}")
    r_abu = resolve_moj_area_name(rows, 'بو هامور')
    check("REAL: بو هامور unchanged (no siblings, n=353)", r_abu == ('بو هامور', 353), f"{r_abu}")
    r_neg = resolve_moj_area_name(rows, 'لجميل')
    check("REAL: لجميل (Lejmail) → None (not in MoJ)", r_neg is None, f"{r_neg}")
else:
    print("  [SKIP] moj_weekly.csv not present")


print()
if _fails:
    print(f"❌ {len(_fails)} FAILED: {_fails}")
    sys.exit(1)
print("✅ ALL PASS (Sprint 2.22.0a.18 area-name reconciliation — sibling aggregation)")
sys.exit(0)
