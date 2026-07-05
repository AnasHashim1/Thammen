#!/usr/bin/env python3
# Sprint 2.22.0b.101 (land-usage purity) — isolated test, E14 (real production functions).
# Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b101_land_usage.py
import csv, re, statistics, sys
from datetime import timedelta
from moj_reference import build_reference, parse_date, DATE_COL, DEFAULT_WINDOW_DAYS, to_float
from evaluate_property import apply_moj_strategy
from built_type import built_type
from usage_filter import _is_residential_usage, _RESIDENTIAL_USAGES

fails = 0
def check(desc, ok):
    global fails
    fails += (0 if ok else 1)
    print(f'  [{"PASS" if ok else "FAIL"}] {desc}')

rows = list(csv.DictReader(open('moj_weekly.csv', encoding='utf-8-sig')))
maxd = max(d for d in (parse_date(r.get(DATE_COL, '')) for r in rows) if d)
c24 = maxd - timedelta(days=DEFAULT_WINDOW_DAYS)
def med(v): return int(round(statistics.median(v))) if v else None

print('1) _is_residential_usage LAND partition (the filter now covers land):')
def row(u): return {'الاستخدام': u, 'نوع العقار': 'أرض فضاء'}
for u, exp in [('فلل او بيوت سكنية', True), ('', True), ('مسكن', True),
               ('مساكن كبار الموظفين', True), ('عمارات او مجمعات سكنية', False),
               ('اراض تجارية متعددة الأستخدام', False), ('مكاتب تجارية', False),
               ('مزارع', False), ('تجاري', False)]:
    check(f'usage={u!r} -> keep={exp}', _is_residential_usage(row(u)) == exp)
check('whitelist unchanged', _RESIDENTIAL_USAGES == {'فلل او بيوت سكنية', 'مسكن', 'مساكن كبار الموظفين'})

print('\n2) build_reference LAND category is now residential-filtered (contamination removed):')
ref_w = build_reference(rows, 'الوعب', maxd)
land_w = (ref_w.get('categories') or {}).get('land') or {}
# manual: the Al-Waab land pool WITHOUT the filter (any usage), 24mo, to prove NEW < mixed
mixed = [to_float(r.get('سعر المتر المربع')) for r in rows
         if built_type(r) == 'LAND'
         and (d := parse_date(r.get(DATE_COL, ''))) and d >= c24
         and (a := to_float(r.get('المساحة بالمتر المربع'))) and a > 0
         and re.sub(r'\s+', ' ', str(r.get('اسم المنطقة', '') or '')).strip().startswith('الوعب')
         and to_float(r.get('سعر المتر المربع'))]
res = [p for r in rows if built_type(r) == 'LAND' and _is_residential_usage(r)
       and (d := parse_date(r.get(DATE_COL, ''))) and d >= c24
       and (a := to_float(r.get('المساحة بالمتر المربع'))) and a > 0
       and re.sub(r'\s+', ' ', str(r.get('اسم المنطقة', '') or '')).strip().startswith('الوعب')
       and (p := to_float(r.get('سعر المتر المربع'))) and p > 0]
check(f'Al-Waab residential land median ({med(res)}) < mixed ({med(mixed)}) — contamination removed',
      med(res) is not None and med(mixed) is not None and med(res) < med(mixed))
check('land category still present + reliable (not refused)', land_w.get('n', 0) > 0)

print('\n3) VILLA is byte-identical by construction (filter expression unchanged for villa):')
# The villa category must equal a manual _is_residential_usage-filtered villa pool (== old behaviour).
ref_bh = build_reference(rows, 'بو هامور', maxd)
villa_prod = ((ref_bh.get('categories') or {}).get('villa') or {}).get('price_per_m2', {}).get('median')
vman = [p for r in rows
        if built_type(r) == 'STANDALONE_VILLA' and _is_residential_usage(r)
        and (d := parse_date(r.get(DATE_COL, ''))) and d >= c24
        and re.sub(r'\s+', ' ', str(r.get('اسم المنطقة', '') or '')).strip() in ('بو هامور',)
        and (p := to_float(r.get('سعر المتر المربع'))) and p > 0]
check(f'production villa median ({villa_prod}) == manual residential-filtered villa ({med(vman)})',
      villa_prod == med(vman))

print('\n4) Companion: a thin filtered LAND bracket widens to its OWN 36mo window (n recovers):')
v = apply_moj_strategy('raw_land', 1219.0, ref_w)   # Al-Waab 1219 m2 -> 900-1500, thin in 24mo
note_join = ' '.join(v.notes or [])
check('companion fired (36mo widen note present)', 'وُسِّعت الشريحة إلى نافذة 36 شهراً' in note_join)
check('value not refused', v.estimated_value_median is not None)
check('residential band (< the mixed 7.1M live; > land floor 4M)',
      v.estimated_value_median is not None and 4_000_000 < v.estimated_value_median < 7_100_000)
lo, m2, hi = v.estimated_value_low, v.estimated_value_median, v.estimated_value_high
check('range NOT inverted (low <= median <= high)',
      None not in (lo, m2, hi) and lo <= m2 <= hi)

print('\n5) No new bare refusals (empty filtered bracket falls back to overall category):')
none_ct = 0
for area in ('الوعب', 'لوسيل', 'الخرايج', 'المطار العتيق', 'معيذر'):
    ref = build_reference(rows, area, maxd)
    for plot in (500, 900, 1500, 2500):
        if apply_moj_strategy('raw_land', float(plot), ref).estimated_value_median is None:
            none_ct += 1
check('0 refusals across 20 land cells', none_ct == 0)

total = 9 + 1 + 2 + 1 + 4 + 1
print(f'\n{total - fails}/{total} passed')
sys.exit(1 if fails else 0)
