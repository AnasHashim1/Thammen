"""
test_sprint_2p22p0a2_p9_precision_pass.py — Sprint 2.22.0a.2 §9 polish.

The "مشابهة" / "مماثلة" precision pass.

Asserts:
  - In user-visible MoJ comparable-language strings, "مشابهة" /
    "مماثلة" no longer appears.
  - The 4 patched sites now emit the precision phrase
    "قريبة في النوع والمساحة".
  - Scope discipline: docstrings/comments + non-MoJ-comparable contexts
    (geo_reference_v2.py decision_label, market_position.py user-prompts)
    are UNTOUCHED per the §9 scope limit.

Standalone test, no pytest dependency.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))


PRECISION_PHRASE = 'قريبة في النوع والمساحة'

# Pre-patch substrings that MUST NOT appear in evaluate_unified.py
# user-visible MoJ comparable strings.
FORBIDDEN_MOJ_COMPARABLE_FRAGMENTS = [
    'صفقة مماثلة في وزارة العدل',          # _ten_year_rule_disclosure_ar
    'لعقارات مشابهة بنفس الحجم',           # accuracy n>=20 explanation
    'الصفقات المشابهة',                    # accuracy widened explanation
    'لعقارات مشابهة في وزارة العدل',       # accuracy refusal explanation
]


def test_no_old_mojcomparable_phrases_in_evaluate_unified():
    """The 4 patched user-visible MoJ-comparable strings no longer use
    'مشابهة' or 'مماثلة'."""
    src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
    for frag in FORBIDDEN_MOJ_COMPARABLE_FRAGMENTS:
        assert frag not in src, (
            f"§9 regression: pre-patch fragment {frag!r} still in "
            f"evaluate_unified.py user-visible MoJ-comparable string."
        )
    print('  PASS test_no_old_mojcomparable_phrases_in_evaluate_unified')


def test_new_precision_phrase_present():
    """The new 'قريبة في النوع والمساحة' phrase appears at all 4 patched sites."""
    src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
    count = src.count(PRECISION_PHRASE)
    assert count >= 4, (
        f"§9: expected at least 4 occurrences of {PRECISION_PHRASE!r} in "
        f"evaluate_unified.py (one per patched site), found {count}"
    )
    print(f'  PASS test_new_precision_phrase_present (count={count})')


def test_specific_patched_strings_render_correctly():
    """Each of the 4 patched user-visible strings carries the precision
    phrase + the surrounding semantic content."""
    src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

    # Site 1: _ten_year_rule_disclosure_ar
    assert 'صفقة قريبة في النوع والمساحة من نفس المنطقة' in src, (
        "§9 site 1 (10-Year-Rule disclosure) not updated"
    )

    # Site 2: accuracy n>=20 comparison_bracket explanation
    assert 'لعقارات قريبة في النوع والمساحة ضمن نفس المنطقة' in src, (
        "§9 site 2 (accuracy n>=20 bracket) not updated"
    )

    # Site 3: accuracy widened explanation
    assert 'الصفقات القريبة في النوع والمساحة' in src, (
        "§9 site 3 (accuracy widened) not updated"
    )

    # Site 4: accuracy refusal explanation
    assert (
        'لا توجد صفقات بيع كافية لعقارات قريبة في النوع والمساحة'
        in src
    ), "§9 site 4 (accuracy refusal) not updated"

    print('  PASS test_specific_patched_strings_render_correctly')


def test_geo_reference_v2_decision_labels_unchanged():
    """Per §9 scope discipline: geo_reference_v2.py decision_labels
    describe area-adjacency (different semantic from MoJ comparables)
    and are UNTOUCHED."""
    src = (REPO_ROOT / 'geo_reference_v2.py').read_text(encoding='utf-8')
    # These should STILL be present (i.e., the precision pass did NOT
    # accidentally sweep over them)
    assert 'ضم منطقة مماثلة واحدة' in src, (
        "§9 over-reach: geo_reference_v2 decision_label was changed but "
        "should be left alone (different semantic — area adjacency, not "
        "MoJ comparable transactions)"
    )
    assert 'ضم 2-3 مناطق مماثلة' in src, "§9 over-reach"
    print('  PASS test_geo_reference_v2_decision_labels_unchanged')


def test_market_position_listings_prompts_unchanged():
    """Per §9 scope discipline: market_position.py user prompts about
    LISTINGS (not MoJ) use 'إعلانات مماثلة' which is a user prompt
    ("check listings like these"), NOT a Thammen claim about
    transactions. Left alone."""
    src = (REPO_ROOT / 'market_position.py').read_text(encoding='utf-8')
    assert 'إعلانات مماثلة' in src, (
        "§9 over-reach: market_position user-prompt about listings was "
        "changed but should be left alone (user-prompt context, not "
        "Thammen MoJ comparable claim)"
    )
    print('  PASS test_market_position_listings_prompts_unchanged')


def main():
    tests = [
        test_no_old_mojcomparable_phrases_in_evaluate_unified,
        test_new_precision_phrase_present,
        test_specific_patched_strings_render_correctly,
        test_geo_reference_v2_decision_labels_unchanged,
        test_market_position_listings_prompts_unchanged,
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
    print(f'Sprint 2.22.0a.2 §9 (precision pass): '
          f'{len(tests) - failed}/{len(tests)} passed')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
