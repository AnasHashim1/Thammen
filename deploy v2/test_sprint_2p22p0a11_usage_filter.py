#!/usr/bin/env python3
# Sprint 2.22.0a.11 (A1) — isolated test for the PRODUCTION helper usage_filter._is_residential_usage.
# Run: PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a11_usage_filter.py
import sys
from usage_filter import _is_residential_usage, _RESIDENTIAL_USAGES

def row(u):
    return {'الاستخدام': u, 'نوع العقار': 'فيلا'}

CASES = [
    ('فلل او بيوت سكنية',           True,  'primary residential -> keep'),
    ('',                            True,  'blank -> keep'),
    (None,                          True,  'None usage -> keep (treated as blank)'),
    ('مسكن',                        True,  'dwelling whitelist -> keep'),
    ('مساكن كبار الموظفين',         True,  'senior-staff housing whitelist -> keep'),
    ('فلل\xa0او\xa0بيوت\xa0سكنية',    True,  'NBSP-variant of primary -> keep'),
    ('  فلل او بيوت سكنية  ',        True,  'leading/trailing spaces -> keep'),
    ('عمارات او مجمعات سكنية',       False, 'apartment/complex (residential but NOT villa) -> exclude'),
    ('عمارات او مجمعات س',           False, 'truncated apartment label -> exclude'),
    ('تجاري',                       False, 'commercial -> exclude'),
    ('مزارع',                       False, 'farm -> exclude'),
    ('مكاتب تجارية',                 False, 'offices -> exclude'),
]

fails = 0
for usage, expected, desc in CASES:
    got = _is_residential_usage(row(usage))
    ok = (got == expected)
    fails += (0 if ok else 1)
    print(f'  [{"PASS" if ok else "FAIL"}] {desc}: got={got} expected={expected}')

# missing الاستخدام key entirely -> treated as blank -> keep
got = _is_residential_usage({'نوع العقار': 'فيلا'})
ok = (got is True)
fails += (0 if ok else 1)
print(f'  [{"PASS" if ok else "FAIL"}] missing الاستخدام key -> keep: got={got}')

# whitelist set sanity
assert _RESIDENTIAL_USAGES == {'فلل او بيوت سكنية', 'مسكن', 'مساكن كبار الموظفين'}, 'whitelist drifted'

total = len(CASES) + 1
print(f'\n{total - fails}/{total} passed')
sys.exit(1 if fails else 0)
