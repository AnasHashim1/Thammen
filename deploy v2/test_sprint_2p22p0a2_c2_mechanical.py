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


def test_sprint_scope_caveat_replaced_post_validation():
    """Post-C2 commit 7 (Sprint 2.22.0a.2): the sprint_scope_caveat_ar
    field now carries the Gemini-approved neutral copy. The Sprint 2.16.0
    self-reference and English/Arabic jargon (stratification/stratum) are
    gone. This test was a forward guard in the mechanical commit and
    flipped at the validation-landing commit."""
    # Import the function that builds the stock_strata response block.
    # The caveat lives inside the dict returned by analyze_stock_strata().
    # Since the field is plain-string interpolation, we can grep the
    # source directly without instantiating the full engine.
    src = (REPO_ROOT / 'stock_strata.py').read_text(encoding='utf-8')

    # Negative assertions: forbidden tokens are gone
    assert "Sprint 2.16.0 (الإصدار الحالي)" not in src, (
        'Forbidden Sprint version self-reference still present in '
        'stock_strata.py — C2 commit 7 was supposed to remove it.'
    )
    # English jargon "stratification" / "stratum" should no longer
    # appear inside the user-visible sprint_scope_caveat_ar block.
    # (They can still appear in code comments / function names — we
    # only enforce on the caveat field's value range.)
    caveat_start = src.find("'sprint_scope_caveat_ar':")
    assert caveat_start > 0, "sprint_scope_caveat_ar key missing"
    # The value spans the next ~6 lines after the key
    caveat_block = src[caveat_start:caveat_start + 800]
    # Find the closing paren of the string-builder tuple
    block_end = caveat_block.find('),', 30)  # skip the opening (
    caveat_value = caveat_block[:block_end] if block_end > 0 else caveat_block
    assert 'stratification' not in caveat_value, (
        f'User-visible code-switching jargon "stratification" still in '
        f'sprint_scope_caveat_ar value: {caveat_value!r}'
    )
    assert 'stratum' not in caveat_value, (
        f'User-visible code-switching jargon "stratum" still in '
        f'sprint_scope_caveat_ar value: {caveat_value!r}'
    )

    # Positive assertion: the new neutral copy is present
    assert 'هذه الطبقات مقدّمة كشفافية إضافية' in src, (
        'C2 commit 7: the Gemini-approved neutral sprint_scope_caveat_ar '
        'copy is missing — commit 7 was supposed to land it.'
    )
    print('  PASS test_sprint_scope_caveat_replaced_post_validation')


def main():
    tests = [
        test_land_priced_description_no_internal_doc_reference,
        test_other_strata_descriptions_unchanged,
        test_sprint_scope_caveat_replaced_post_validation,
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
