#!/usr/bin/env python3
# Sprint 2.22.0a.12 (A2) — isolated test for the PRODUCTION built_type classifier.
# Run: PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a12_builttype.py
import sys
from built_type import built_type, matches_category

def row(t):
    return {'نوع العقار': t}

CASES = [
    # (نوع العقار, expected built_type, desc)
    ('أرض فضاء',                       'LAND',             'vacant land'),
    ('فيلا',                           'STANDALONE_VILLA', 'single villa'),
    ('فيلا من طابقين وملحق',           'STANDALONE_VILLA', '2-story villa + annex'),
    ('فيلا دور أرضي وملحق',            'STANDALONE_VILLA', 'ground-floor villa + annex'),
    ('فيلا من طابقين وملحق + بنت هاوس', 'STANDALONE_VILLA', 'villa + penthouse -> folded (LOCK2)'),
    ('بنت هاوس',                       'STANDALONE_VILLA', 'bare penthouse -> villa stratum (LOCK2)'),
    ('بيت للسكن',                      'HOUSE',            'house (بيت) (LOCK4)'),
    ('مسكن',                           'HOUSE',            'مسكن -> HOUSE (resolves split, LOCK4)'),
    ('مسكن شعبي',                      'HOUSE',            'popular house -> HOUSE'),
    ('فيلتان متلاصقتان',               None,               'فيلتان -> EXCLUDED (LOCK1)'),
    ('فيلتان منفصلتان وملحقان',        None,               'فيلتان variant -> EXCLUDED (LOCK1)'),
    ('مجمع فلل',                       None,               'compound -> EXCLUDED (LOCK3)'),
    ('ثلاث فلل وملاحق',                None,               'count-word compound -> EXCLUDED (LOCK3)'),
    ('أربعة فلل من دورين',             None,               'count-word compound -> EXCLUDED (LOCK3)'),
    ('قصر',                            None,               'palace -> EXCLUDED'),
    ('عمارة سكنية',                    None,               'apartment building -> EXCLUDED'),
    ('برج سكني',                       None,               'tower -> EXCLUDED'),
    ('محل تجاري',                      None,               'shop -> EXCLUDED'),
    ('  فيلا  ',                       'STANDALONE_VILLA', 'spaces -> normalized'),
    ('فيلا\xa0من\xa0طابقين',           'STANDALONE_VILLA', 'NBSP villa -> normalized'),
    ('',                               None,               'blank -> None'),
]

fails = 0
for t, expected, desc in CASES:
    got = built_type(row(t))
    ok = (got == expected)
    fails += (0 if ok else 1)
    print(f'  [{"PASS" if ok else "FAIL"}] {desc}: got={got!r} expected={expected!r}')

# matches_category mapping: villa->STANDALONE_VILLA, land->LAND, non-stratified->True (defer)
checks = [
    (matches_category(row('فيلا'), 'villa') is True, "villa row matches 'villa'"),
    (matches_category(row('بيت للسكن'), 'villa') is False, "house row does NOT match 'villa'"),
    (matches_category(row('فيلتان متلاصقتان'), 'villa') is False, "فيلتان does NOT match 'villa'"),
    (matches_category(row('بنت هاوس'), 'villa') is True, "penthouse matches 'villa' (folded)"),
    (matches_category(row('أرض فضاء'), 'land') is True, "land row matches 'land'"),
    (matches_category(row('فيلا'), 'land') is False, "villa row does NOT match 'land'"),
    (matches_category(row('فيلا'), 'palace') is True, "non-stratified category -> defer True"),
]
for ok, desc in checks:
    fails += (0 if ok else 1)
    print(f'  [{"PASS" if ok else "FAIL"}] {desc}')

total = len(CASES) + len(checks)
print(f'\n{total - fails}/{total} passed')
sys.exit(1 if fails else 0)
