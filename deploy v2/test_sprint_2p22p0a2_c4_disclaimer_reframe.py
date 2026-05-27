"""
test_sprint_2p22p0a2_c4_disclaimer_reframe.py — Sprint 2.22.0a.2 C4.

Asserts:
  - All 8+ disclaimer sites carry the new reframed phrasing:
    "ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS"
  - None of the old defensive-negation phrasings remain:
    "وليس تقييماً عقارياً معتمداً وفق RICS/IVS" (long)
    "وليس تقييماً معتمداً وفق RICS/IVS" (short)
    "لا يُصدر تقييماً عقارياً معتمداً (RICS/IVS)" (list)

Standalone test, no pytest dependency.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))


NEW_LONG = 'ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS'
NEW_SHORT_SUBSTR = 'لا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص'
NEW_LIST_ITEM = 'لا يُصدر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS'

OLD_LONG_VARIANTS = [
    'وليس تقييماً عقارياً معتمداً وفق RICS/IVS',          # original short
    'وليس تقييماً عقارياً معتمداً وفق معايير RICS أو IVS', # api.py original variant
]
OLD_SHORT = 'وليس تقييماً معتمداً وفق RICS/IVS'
OLD_LIST = 'لا يُصدر تقييماً عقارياً معتمداً (RICS/IVS)'

PRODUCTION_FILES = [
    'api.py',
    'evaluate_unified.py',
    'evaluate_v3.py',
    'evaluate_property.py',
]


def test_no_old_long_form_phrasings_in_production():
    for fn in PRODUCTION_FILES:
        src = (REPO_ROOT / fn).read_text(encoding='utf-8')
        for old in OLD_LONG_VARIANTS:
            assert old not in src, (
                f"C4 regression: old long-form phrasing {old!r} still in "
                f"production file {fn}"
            )
    print('  PASS test_no_old_long_form_phrasings_in_production')


def test_no_old_short_form_in_evaluate_unified():
    src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
    assert OLD_SHORT not in src, (
        f"C4 regression: old short-form phrasing {OLD_SHORT!r} still in "
        f"evaluate_unified.py — 5 sites were supposed to be updated."
    )
    print('  PASS test_no_old_short_form_in_evaluate_unified')


def test_no_old_list_item_form_in_api():
    src = (REPO_ROOT / 'api.py').read_text(encoding='utf-8')
    assert OLD_LIST not in src, (
        f"C4 regression: old list-item form {OLD_LIST!r} still in api.py."
    )
    print('  PASS test_no_old_list_item_form_in_api')


def test_new_long_form_in_api_long_disclaimer():
    src = (REPO_ROOT / 'api.py').read_text(encoding='utf-8')
    assert NEW_SHORT_SUBSTR in src, (
        f"C4: new disclaimer substring {NEW_SHORT_SUBSTR!r} missing from "
        f"api.py (key phrase must be kept on one source line for substring "
        f"search to find it across Python string-concat boundaries)."
    )
    print('  PASS test_new_long_form_in_api_long_disclaimer')


def test_new_short_form_in_evaluate_unified():
    src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
    # Count occurrences — should be exactly 5 (the 5 short-form sites)
    count = src.count(
        'هذا تحليل معلوماتي، ولا يُعتبر تقرير تثمين رسمي صادر عن '
        'مثمّن مرخّص وفق معايير RICS/IVS.'
    )
    assert count == 5, (
        f"C4: expected exactly 5 short-form disclaimer sites in "
        f"evaluate_unified.py, found {count}. Each fast-path or refusal "
        f"flow should emit the new disclaimer."
    )
    print('  PASS test_new_short_form_in_evaluate_unified  (5 sites)')


def test_new_list_item_form_in_api():
    src = (REPO_ROOT / 'api.py').read_text(encoding='utf-8')
    assert NEW_LIST_ITEM in src, (
        f"C4: new list-item form missing from api.py what_thammen_does_not"
    )
    print('  PASS test_new_list_item_form_in_api')


def test_new_long_form_in_evaluate_v3():
    src = (REPO_ROOT / 'evaluate_v3.py').read_text(encoding='utf-8')
    assert NEW_SHORT_SUBSTR in src, "C4: evaluate_v3.py disclaimer not updated"
    print('  PASS test_new_long_form_in_evaluate_v3')


def test_new_long_form_in_evaluate_property():
    src = (REPO_ROOT / 'evaluate_property.py').read_text(encoding='utf-8')
    assert NEW_SHORT_SUBSTR in src, "C4: evaluate_property.py disclaimer not updated"
    print('  PASS test_new_long_form_in_evaluate_property')


def main():
    tests = [
        test_no_old_long_form_phrasings_in_production,
        test_no_old_short_form_in_evaluate_unified,
        test_no_old_list_item_form_in_api,
        test_new_long_form_in_api_long_disclaimer,
        test_new_short_form_in_evaluate_unified,
        test_new_list_item_form_in_api,
        test_new_long_form_in_evaluate_v3,
        test_new_long_form_in_evaluate_property,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f'  FAIL {t.__name__}: {e}')
            failed += 1
        except Exception as e:
            print(f'  ERROR {t.__name__}: {type(e).__name__}: {e}')
            failed += 1
    print()
    print(f'Sprint 2.22.0a.2 C4 (disclaimer reframe): '
          f'{len(tests) - failed}/{len(tests)} passed')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
