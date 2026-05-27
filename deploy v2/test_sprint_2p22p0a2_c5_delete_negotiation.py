"""
test_sprint_2p22p0a2_c5_delete_negotiation.py — Sprint 2.22.0a.2 C5.

Asserts:
  - The 'negotiation' section is NO LONGER appended in
    output_briefs.compose_buyer_brief (the buyer-side fair_range builder
    was deleted entirely).
  - The dead post-processor in evaluate_unified that consumed the
    'negotiation' section (and computed _negotiation_anchor) is also
    deleted (the if sid == 'negotiation' branch + its upstream
    _negotiation_anchor stratum-aware logic).
  - The forbidden user-prescriptive Arabic phrasings
    ('لا تدفع أكثر من وسيط MoJ + 10%', 'ابدأ بعرض أقل 10% من التقييم')
    are no longer present in production code.

ENGINE INTERNAL SANITY-CHECK CODE preserved (per KICKOFF):
  - evaluate_property.py 'above_buyer_ceiling' flag (internal red-flag check)
  - market_regime.py buyer_ceiling_multiplier_default / opening_offer_*
    (dataclass attributes + recommendation calculations)

Standalone test, no pytest dependency.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))


def test_output_briefs_no_longer_appends_negotiation_section():
    """compose_buyer_brief no longer builds the 'negotiation' section."""
    src = (REPO_ROOT / 'output_briefs.py').read_text(encoding='utf-8')
    # The negotiation section had these distinctive markers — none must remain
    assert "fair_range = {" not in src, (
        "C5 regression: 'fair_range = {' still present in output_briefs.py"
    )
    assert "'id': 'negotiation'" not in src, (
        "C5 regression: 'negotiation' section ID still appended"
    )
    assert "'title_ar': 'نطاق التفاوض المقترح'" not in src, (
        "C5 regression: negotiation title_ar still present"
    )
    print('  PASS test_output_briefs_no_longer_appends_negotiation_section')


def test_no_buyer_prescriptive_phrases_in_production():
    """The two forbidden imperative phrases must not appear anywhere
    in production code."""
    for fn in ('output_briefs.py', 'evaluate_unified.py', 'evaluate_v3.py',
               'evaluate_property.py', 'api.py'):
        src = (REPO_ROOT / fn).read_text(encoding='utf-8')
        # Note: لا تدفع أكثر appears in code comments inside other modules
        # (e.g., market_regime.py docstring). The user-rendered string was
        # only ever output_briefs.py:515 — strictly enforce on production
        # output files.
        assert 'لا تدفع أكثر من وسيط MoJ + 10%' not in src, (
            f"C5 regression: 'لا تدفع أكثر من وسيط MoJ + 10%' still in {fn}"
        )
        assert 'ابدأ بعرض أقل 10% من التقييم' not in src, (
            f"C5 regression: 'ابدأ بعرض أقل 10% من التقييم' still in {fn}"
        )
    print('  PASS test_no_buyer_prescriptive_phrases_in_production')


def test_dead_negotiation_postprocessor_removed():
    """The post-processor in evaluate_unified that consumed the
    'negotiation' section is removed (both the upstream
    _negotiation_anchor computation + the if branch)."""
    src = (REPO_ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
    # The _negotiation_anchor variable should no longer be assigned
    assert '_negotiation_anchor = final_amount' not in src, (
        "C5 regression: dead _negotiation_anchor assignment still present"
    )
    # The if-branch that consumed 'negotiation' should be gone
    assert "if sid == 'negotiation'" not in src, (
        "C5 regression: post-processor 'if sid == \"negotiation\"' branch "
        "still present in evaluate_unified.py"
    )
    print('  PASS test_dead_negotiation_postprocessor_removed')


def test_engine_internal_sanity_checks_preserved():
    """Per KICKOFF: 'The numerical thresholds (× 1.10 buyer ceiling,
    × 0.90 opening offer) STAY in any engine internal sanity-check
    code that uses them.'

    Verify the kept-internal sites still exist:
      - evaluate_property.PropertyEvaluation.above_buyer_ceiling field
        (internal red-flag computation, never user-facing)
      - market_regime.MarketRegime calibration constants
    """
    ep_src = (REPO_ROOT / 'evaluate_property.py').read_text(encoding='utf-8')
    mr_src = (REPO_ROOT / 'market_regime.py').read_text(encoding='utf-8')

    # evaluate_property internal red-flag flag
    assert 'above_buyer_ceiling' in ep_src, (
        "Engine internal red-flag 'above_buyer_ceiling' was removed — "
        "but the KICKOFF said engine internals stay. Restore."
    )

    # market_regime calibration constants
    assert 'buyer_ceiling_multiplier_default' in mr_src, (
        "market_regime.buyer_ceiling_multiplier_default missing — "
        "engine calibration was supposed to stay."
    )
    assert 'opening_offer_multiplier_default' in mr_src, (
        "market_regime.opening_offer_multiplier_default missing — "
        "engine calibration was supposed to stay."
    )
    print('  PASS test_engine_internal_sanity_checks_preserved')


def test_buyer_brief_section_ids_no_longer_include_negotiation():
    """_buyer_brief produces sections that do NOT include 'negotiation'."""
    import output_briefs
    # Minimal fake evaluation — only the fields _buyer_brief reads
    # explicitly via _base_brief() need to be present. Anything else can
    # be missing (the function tolerates None for optional sections).
    fake_evaluation = {
        'valuation_total': 1_000_000,
        'valuation_low': 900_000,
        'valuation_high': 1_100_000,
        'address': 'TEST/1/1',
        'district': 'TEST',
        'plot_area_m2': 600.0,
        'asset_type': 'standalone_villa',
        'asset_type_ar': 'فيلا مستقلة',
        'valuation_date': '2026-05-27',
        'listing_flags': {},
        'methodology_ar': 'TEST',
        'methodology_disclaimer_ar': 'TEST',
        'engine_version': 'test',
        'tier_label': None,
        'valuation': {'method': 'comparison_bracket'},
    }
    try:
        brief = output_briefs._buyer_brief(
            evaluation=fake_evaluation,
            rent_data=None,
            adjustments=None,
            uncertainty=None,
            income_value=None,
        )
    except Exception as e:
        raise AssertionError(
            f'_buyer_brief raised after C5 deletion: '
            f'{type(e).__name__}: {e}'
        )
    if brief is None:
        raise AssertionError('_buyer_brief returned None')

    section_ids = [s.get('id') for s in brief.get('sections', [])]
    assert 'negotiation' not in section_ids, (
        f"C5 regression: 'negotiation' still in rendered buyer brief: "
        f"{section_ids}"
    )
    print(f'  PASS test_buyer_brief_section_ids_no_longer_include_negotiation '
          f'(sections: {section_ids})')


def main():
    tests = [
        test_output_briefs_no_longer_appends_negotiation_section,
        test_no_buyer_prescriptive_phrases_in_production,
        test_dead_negotiation_postprocessor_removed,
        test_engine_internal_sanity_checks_preserved,
        test_buyer_brief_section_ids_no_longer_include_negotiation,
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
    print(f'Sprint 2.22.0a.2 C5 (DELETE negotiation section): '
          f'{len(tests) - failed}/{len(tests)} passed')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
