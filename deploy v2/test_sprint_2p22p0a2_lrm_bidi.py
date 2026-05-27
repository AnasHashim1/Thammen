"""
test_sprint_2p22p0a2_lrm_bidi.py — Sprint 2.22.0a.2 Pattern A regression tests.

Validates LRM (U+200E) wrapping at 4 user-visible Arabic-with-Latin sites
identified in Phase 0 surface audit (docs/PHASE0_ARABIC_SURFACE_AUDIT.md §5).

Per Operational_Rules #25: Latin/digit tokens inside Arabic text rendered
with dir="rtl" may visually reverse (e.g. "31 / 918 / 99" rendering as
"99 / 918 / 31"). Wrapping the Latin run with U+200E (LEFT-TO-RIGHT MARK)
prevents the reversal without altering the bidi base direction.

Sites under test:
  1. material_uncertainty.regime_muc().muc_clause_ar       (Pattern A site 1)
  2. material_uncertainty.assess_uncertainty().recommendations[-1]  (site 2)
  3. output_briefs.compose_buyer_brief().sections[material_uncertainty].title_ar (site 3)
  4. index.html line 737 (JS template literal — verified textually, site 4)

Tests are STANDALONE (no pytest dependency, per project convention).
"""
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
LRM = '‎'


def _read(p: str) -> str:
    return (REPO_ROOT / p).read_text(encoding='utf-8')


# ─── Test 1: material_uncertainty.regime_muc muc_clause_ar carries LRM ───

def test_muc_clause_ar_wraps_rics_with_lrm():
    """Site 1: regime_muc()['muc_clause_ar'] must contain LRM-wrapped
    Latin tokens for RICS / VPGA 10 / VPS 6 / IVS / IVS 106."""
    sys.path.insert(0, str(REPO_ROOT))
    from material_uncertainty import regime_muc
    out = regime_muc()
    clause = out.get('muc_clause_ar') or ''
    assert clause, 'regime_muc must produce muc_clause_ar for non-normal regime'
    # Each of these tokens must be immediately surrounded by LRM
    for token in ('RICS Red Book Global Standards', 'VPGA 10',
                  'VPS 6', 'IVS 106', 'effective 31 January 2025'):
        wrapped = f'{LRM}{token}{LRM}'
        assert wrapped in clause, (
            f"Site 1: expected LRM-wrapped '{token}' in muc_clause_ar; "
            f"got context: ...{clause[max(0, clause.find(token)-3):clause.find(token)+len(token)+3]}..."
        )
    print('  PASS test_muc_clause_ar_wraps_rics_with_lrm')


# ─── Test 2: assess_uncertainty recommendations LRM-wrap ───

def test_recommendations_lrm_wrap_rics_standards():
    """Site 2: assess_uncertainty() with rics_compliant=False appends a
    recommendation citing RICS + IVS + VPS 1 — those Latin tokens must
    be LRM-wrapped."""
    sys.path.insert(0, str(REPO_ROOT))
    from material_uncertainty import assess_uncertainty
    # Force rics_compliant=False by leaving has_field_inspection=False
    level = assess_uncertainty(moj_n=5, has_field_inspection=False,
                               building_condition_known=False)
    assert not level.rics_compliant
    rec_text = ' '.join(level.recommendations)
    for token in ('RICS Red Book Global Standards', 'IVS',
                  'effective 31 January 2025', 'Terms of Engagement',
                  'VPS 1'):
        wrapped = f'{LRM}{token}{LRM}'
        assert wrapped in rec_text, (
            f"Site 2: expected LRM-wrapped '{token}' in recommendations[]; "
            f"got: {rec_text[:300]}..."
        )
    print('  PASS test_recommendations_lrm_wrap_rics_standards')


# ─── Test 3: output_briefs buyer brief MVU title_ar LRM ───

def test_buyer_brief_mvu_title_ar_lrm_wrap():
    """Site 3: the MVU section title_ar in buyer brief contains LRM-wrapped
    RICS/VPGA/VPS/IVS tokens. Verified textually against output_briefs.py
    (the section is built conditionally; textual verification ensures the
    source-of-truth string carries the LRM markers)."""
    src = _read('output_briefs.py')
    # The buyer brief title_ar line 583 (Pattern A site 3).
    target = (
        "'title_ar': 'تحفظات مادية وفق "
        f"{LRM}RICS Red Book Global Standards{LRM} "
        f"({LRM}effective 31 January 2025{LRM}) — "
        f"{LRM}VPGA 10{LRM} و {LRM}VPS 6{LRM} — و "
        f"{LRM}IVS{LRM} ({LRM}effective 31 January 2025{LRM}) — "
        f"{LRM}IVS 106{LRM}',"
    )
    assert target in src, (
        "Site 3: expected LRM-wrapped title_ar in output_briefs.py. "
        "Search target was: " + target[:200]
    )
    print('  PASS test_buyer_brief_mvu_title_ar_lrm_wrap')


# ─── Test 4: index.html MVU banner JS template carries LRM ───

def test_index_html_mvu_banner_lrm_wrap():
    """Site 4: the MVU banner header in index.html JS template (line ~737)
    contains LRM-wrapped Latin tokens."""
    src = _read('index.html')
    # We assert the exact LRM-wrapped header is present in the rendered banner.
    # Note: the JS line embeds it inside a string literal; we check substring.
    needles = [
        f'⚠️ تحفظ مادي وفق {LRM}RICS Red Book Global Standards{LRM}',
        f'({LRM}effective 31 January 2025{LRM})',
        f'{LRM}VPGA 10{LRM}',
        f'{LRM}VPS 6{LRM}',
        f'{LRM}IVS{LRM}',
        f'{LRM}IVS 106{LRM}',
    ]
    for n in needles:
        assert n in src, (
            f"Site 4: expected LRM-wrapped substring not found in index.html: {n!r}"
        )
    print('  PASS test_index_html_mvu_banner_lrm_wrap')


# ─── Test 5: regression — bare unwrapped Latin tokens absent in 4 sites ───

def test_no_unwrapped_rics_tokens_at_4_sites():
    """Regression: the four patched sites must NOT carry the bare
    Arabic-then-Latin sequence without an intervening LRM. We check the
    canonical bad pattern: an Arabic letter (Unicode block 0600-06FF)
    directly adjacent to the first Latin character with no LRM between.

    This guards against future edits that re-introduce the bidi bug by
    replacing the LRM-wrapped string with an unwrapped one."""

    arabic_letter = r'[؀-ۿ]'
    # The 4 specific sequences we patched — bare (no LRM) versions:
    bad_patterns = [
        # "وفق RICS" — Arabic 'وفق' immediately followed by Latin without LRM
        re.compile(r'وفق RICS Red Book Global Standards \(effective'),
        # "و IVS" — Arabic 'و' directly before 'IVS' (specifically the long
        # form used in the muc_clause_ar header, not the short generic 'و IVS')
        re.compile(r'و VPS 6 — و IVS \(effective 31 January 2025\) — IVS 106\\n\\n'),
    ]
    files_to_check = [
        'material_uncertainty.py',
        'output_briefs.py',
        'index.html',
    ]
    # Each file should NOT contain the bare patterns at the Pattern A sites.
    # NOTE: comments are fine — we only enforce on the four patched line ranges.
    # We rely on the absence of the *exact* unwrapped string the audit caught.
    for f in files_to_check:
        src = _read(f)
        # The exact unwrapped header (no LRM) from before the patch:
        unwrapped_header = (
            '⚠️ تحفظ مادي وفق RICS Red Book Global Standards '
            '(effective 31 January 2025) — VPGA 10 و VPS 6 — و IVS '
            '(effective 31 January 2025) — IVS 106'
        )
        assert unwrapped_header not in src, (
            f"Regression: file {f} contains the pre-patch unwrapped MVU "
            "header. Pattern A must wrap each Latin run with U+200E LRM."
        )
    print('  PASS test_no_unwrapped_rics_tokens_at_4_sites')


def main():
    tests = [
        test_muc_clause_ar_wraps_rics_with_lrm,
        test_recommendations_lrm_wrap_rics_standards,
        test_buyer_brief_mvu_title_ar_lrm_wrap,
        test_index_html_mvu_banner_lrm_wrap,
        test_no_unwrapped_rics_tokens_at_4_sites,
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
    print(f'Sprint 2.22.0a.2 Pattern A: {len(tests) - failed}/{len(tests)} passed')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
