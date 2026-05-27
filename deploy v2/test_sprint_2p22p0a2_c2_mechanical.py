"""
test_sprint_2p22p0a2_c2_mechanical.py — Sprint 2.22.0a.2 Pattern C2 mechanical drop.

Asserts:
  - stock_strata.STRATUM_DESC_AR['land_priced'] no longer cites
    "(Project Instructions §3)" (internal-doc leak per Phase 0 audit).
  - The substantive Arabic copy (10-Year-Rule rationale) is preserved.

The 445-line sprint_scope_caveat_ar replacement is NOT in this Sprint —
its replacement copy is in the multi-AI validation batch packet (Anas's
hybrid-path decision: mechanical part now, full rewrite via multi-AI).

Standalone test, no pytest dependency.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))


def test_land_priced_description_no_internal_doc_reference():
    from stock_strata import STRATUM_DESC_AR
    desc = STRATUM_DESC_AR['land_priced']
    # Must NOT contain the internal-doc citation
    assert 'Project Instructions' not in desc, (
        f"C2 mechanical: 'Project Instructions' still present in "
        f"STRATUM_DESC_AR['land_priced']: {desc!r}"
    )
    assert '§3' not in desc, (
        f"C2 mechanical: '§3' still present: {desc!r}"
    )
    # Must STILL contain the substantive methodology hint
    assert '10-Year-Rule' in desc, (
        f"C2 mechanical: 10-Year-Rule rationale lost: {desc!r}"
    )
    assert 'البناء عبء معماري' in desc, (
        f"C2 mechanical: core insight 'البناء عبء معماري' lost: {desc!r}"
    )
    print('  PASS test_land_priced_description_no_internal_doc_reference')


def test_other_strata_descriptions_unchanged():
    """Regression: only land_priced was touched. Other strata descriptions
    must contain no 'Project Instructions' references either (Phase 0
    confirmed they didn't), but more importantly, must still carry their
    substantive copy unchanged."""
    from stock_strata import STRATUM_DESC_AR
    for stratum in ('aging_stock', 'modern_stock', 'luxury_new'):
        desc = STRATUM_DESC_AR[stratum]
        assert 'Project Instructions' not in desc
        assert desc, f'{stratum} description is empty'
    # aging_stock keeps its anchor phrase
    assert 'عمرها 10+' in STRATUM_DESC_AR['aging_stock'], \
        'aging_stock copy unexpectedly changed'
    print('  PASS test_other_strata_descriptions_unchanged')


def test_sprint_scope_caveat_still_present_for_now():
    """The 'sprint_scope_caveat_ar' field with the 'Sprint 2.16.0'
    self-reference is INTENTIONALLY still present in this Sprint —
    its replacement copy goes through multi-AI validation (Anas's
    hybrid-path decision). This test guards against accidental
    removal in the mechanical commit — when the validated replacement
    lands, this test will be flipped."""
    src = (REPO_ROOT / 'stock_strata.py').read_text(encoding='utf-8')
    assert 'sprint_scope_caveat_ar' in src, (
        'sprint_scope_caveat_ar key disappeared from stock_strata.py — '
        "but its replacement copy is supposed to land via the multi-AI "
        "validation batch, not the mechanical commit. Restore or check "
        "the batch packet."
    )
    # Marker that the multi-AI replacement has NOT YET applied:
    assert 'Sprint 2.16.0' in src, (
        "Sprint 2.16.0 self-reference unexpectedly removed before "
        "multi-AI validation landed. Flip this test when the validated "
        "replacement commits."
    )
    print('  PASS test_sprint_scope_caveat_still_present_for_now')


def main():
    tests = [
        test_land_priced_description_no_internal_doc_reference,
        test_other_strata_descriptions_unchanged,
        test_sprint_scope_caveat_still_present_for_now,
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
    print(f'Sprint 2.22.0a.2 Pattern C2 mechanical: {len(tests) - failed}/{len(tests)} passed')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
