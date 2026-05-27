"""
test_sprint_2p22p0a2_b_classifier_failure.py — Sprint 2.22.0a.2 Pattern B.

Validates the 7th refusal template + new dispatcher row:
  - classifier_failure template exists in refusal_templates.REFUSAL_TEMPLATES
    with correct Arabic + English copy
  - _compute_refusal_reason() routes asset_type='unknown' + method !=
    'asset_type_reality_stop' to classifier_failure (NOT comp_density_sparse)
  - All other dispatcher routes UNCHANGED:
      density_gated_district, spatial_ambiguity, asset_scale_extreme,
      asset_class_out_of_scope, comp_density_sparse

Pattern B fixes the 70/300/25 misroute observed in Phase 0
(asset_type='unknown' from QARS coverage gap → engine returned
comp_density_sparse "fewer than 5 comparable transactions" message,
which is factually misleading because the engine doesn't even know
what type of property is at the address).

Standalone test, no pytest dependency.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))


# ─── Template registration ─────────────────────────────────────────────

def test_classifier_failure_template_registered():
    """The 7th template is in REFUSAL_TEMPLATES with the right keys."""
    from refusal_templates import REFUSAL_TEMPLATES, is_registered
    assert 'classifier_failure' in REFUSAL_TEMPLATES, (
        "B: 'classifier_failure' missing from REFUSAL_TEMPLATES"
    )
    assert is_registered('classifier_failure')
    tpl = REFUSAL_TEMPLATES['classifier_failure']
    for key in ('message_ar', 'message_en', 'recommendation_ar'):
        assert key in tpl, f"classifier_failure missing key {key}"
    print('  PASS test_classifier_failure_template_registered')


def test_classifier_failure_template_arabic_content():
    """Arabic message body is the Gemini-approved verbatim text."""
    from refusal_templates import REFUSAL_TEMPLATES
    tpl = REFUSAL_TEMPLATES['classifier_failure']
    # Key phrases from §6 of validation batch
    assert 'لم نتمكّن من تحديد نوع العقار' in tpl['message_ar']
    assert 'القاعدة الحكومية' not in tpl['message_ar']  # negative: not this variant
    assert 'QARS' in tpl['message_ar']
    assert 'تحقّق من بيانات العنوان' in tpl['recommendation_ar']
    print('  PASS test_classifier_failure_template_arabic_content')


def test_classifier_failure_template_english_content():
    from refusal_templates import REFUSAL_TEMPLATES
    tpl = REFUSAL_TEMPLATES['classifier_failure']
    assert 'could not classify' in tpl['message_en']
    assert 'QARS' in tpl['message_en']
    assert 'Please verify the address details' in tpl['message_en']
    print('  PASS test_classifier_failure_template_english_content')


def test_template_count_is_seven():
    """Sprint 2.22.0a/5 shipped 6 templates; Pattern B adds the 7th."""
    from refusal_templates import REFUSAL_TEMPLATES
    assert len(REFUSAL_TEMPLATES) == 7, (
        f"Expected 7 templates after Pattern B, got {len(REFUSAL_TEMPLATES)}: "
        f"{sorted(REFUSAL_TEMPLATES.keys())}"
    )
    print('  PASS test_template_count_is_seven')


# ─── Dispatcher routing ─────────────────────────────────────────────

def test_unknown_asset_type_routes_to_classifier_failure():
    """The Phase-0 70/300/25 case (asset_type='unknown', district=null,
    method='insufficient_data') must now route to classifier_failure
    instead of comp_density_sparse."""
    from evaluate_unified import _compute_refusal_reason
    r = _compute_refusal_reason(
        method='insufficient_data',
        asset_type='unknown',
        district_ar=None,
        plot_area_m2=None,
    )
    assert r is not None, "B regression: dispatcher returned None"
    assert r['trigger_id'] == 'classifier_failure', (
        f"B: asset_type='unknown' should route to classifier_failure; "
        f"got trigger_id={r['trigger_id']!r}"
    )
    print('  PASS test_unknown_asset_type_routes_to_classifier_failure')


def test_unknown_via_reality_stop_still_routes_to_spatial_ambiguity():
    """When asset_type_reality_stop fires, the dispatcher must still pick
    spatial_ambiguity (NOT classifier_failure). The Sprint 2.21.0.7 stop
    path remains exclusive."""
    from evaluate_unified import _compute_refusal_reason
    r = _compute_refusal_reason(
        method='asset_type_reality_stop',
        asset_type='unknown',
        district_ar='الخريطيات',
        plot_area_m2=500,
    )
    assert r['trigger_id'] == 'spatial_ambiguity', (
        f"B regression: reality_stop path should still route to "
        f"spatial_ambiguity; got {r['trigger_id']!r}"
    )
    print('  PASS test_unknown_via_reality_stop_still_routes_to_spatial_ambiguity')


def test_known_asset_type_with_sparse_data_still_routes_to_comp_density_sparse():
    """The Phase-0 52/903/90 case (asset_type='apartment_building', no
    district gating, no reality stop, no compound_large) must still route
    to comp_density_sparse — Pattern B did NOT change this."""
    from evaluate_unified import _compute_refusal_reason
    r = _compute_refusal_reason(
        method='insufficient_data',
        asset_type='apartment_building',
        district_ar='اللقطة',
        plot_area_m2=467,
    )
    assert r['trigger_id'] == 'comp_density_sparse', (
        f"B regression: known asset_type + sparse MoJ should still route "
        f"to comp_density_sparse; got {r['trigger_id']!r}"
    )
    print('  PASS test_known_asset_type_with_sparse_data_still_routes_to_comp_density_sparse')


def test_density_gated_district_still_overrides_all():
    """density_gated_district remains row-1 highest precedence —
    Pearl-class addresses must still route there even with
    asset_type='unknown' (i.e., Pattern B's new row 2 must NOT
    pre-empt the deliberate engine-scope exclusion)."""
    from evaluate_unified import _compute_refusal_reason
    from evaluate_unified import _DENSITY_GATED_DISTRICTS
    # Pick any district in the gated set (verify the set is non-empty too)
    assert _DENSITY_GATED_DISTRICTS, "_DENSITY_GATED_DISTRICTS unexpectedly empty"
    gated_district = next(iter(_DENSITY_GATED_DISTRICTS))
    r = _compute_refusal_reason(
        method='insufficient_data',
        asset_type='unknown',
        district_ar=gated_district,
        plot_area_m2=None,
    )
    assert r['trigger_id'] == 'density_gated_district', (
        f"B regression: density_gated_district (row 1) must still pre-empt "
        f"classifier_failure (row 2); got {r['trigger_id']!r}"
    )
    print('  PASS test_density_gated_district_still_overrides_all')


def test_compound_large_15k_still_routes_to_asset_scale_extreme():
    """asset_scale_extreme (E20 Patch A boundary) must still fire for
    compound_large >= 15K m². Pattern B's new row 2 doesn't pre-empt
    this because compound_large is a known asset_type."""
    from evaluate_unified import _compute_refusal_reason
    r = _compute_refusal_reason(
        method='insufficient_data',
        asset_type='compound_large',
        district_ar='الدفنة',
        plot_area_m2=20_000,  # >15K
    )
    assert r['trigger_id'] == 'asset_scale_extreme', (
        f"B regression: compound_large >= 15K must still route to "
        f"asset_scale_extreme; got {r['trigger_id']!r}"
    )
    print('  PASS test_compound_large_15k_still_routes_to_asset_scale_extreme')


def test_out_of_scope_v1_still_routes_to_asset_class_out_of_scope():
    """Sprint 2.22.0a/5 row 4 trigger unchanged by Pattern B."""
    from evaluate_unified import _compute_refusal_reason
    r = _compute_refusal_reason(
        method='out_of_scope_v1',
        asset_type='commercial',
        district_ar='التجارية',
        plot_area_m2=1000,
    )
    assert r['trigger_id'] == 'asset_class_out_of_scope', (
        f"B regression: out_of_scope_v1 must still route to "
        f"asset_class_out_of_scope; got {r['trigger_id']!r}"
    )
    print('  PASS test_out_of_scope_v1_still_routes_to_asset_class_out_of_scope')


def test_value_producing_method_returns_none():
    """The defensive None for value-producing methods is preserved."""
    from evaluate_unified import _compute_refusal_reason
    r = _compute_refusal_reason(
        method='comparison_bracket',  # value-producing
        asset_type='standalone_villa',
        district_ar='الغرافة',
        plot_area_m2=600,
    )
    assert r is None, (
        f"B regression: value-producing method should return None; got {r!r}"
    )
    print('  PASS test_value_producing_method_returns_none')


def main():
    tests = [
        test_classifier_failure_template_registered,
        test_classifier_failure_template_arabic_content,
        test_classifier_failure_template_english_content,
        test_template_count_is_seven,
        test_unknown_asset_type_routes_to_classifier_failure,
        test_unknown_via_reality_stop_still_routes_to_spatial_ambiguity,
        test_known_asset_type_with_sparse_data_still_routes_to_comp_density_sparse,
        test_density_gated_district_still_overrides_all,
        test_compound_large_15k_still_routes_to_asset_scale_extreme,
        test_out_of_scope_v1_still_routes_to_asset_class_out_of_scope,
        test_value_producing_method_returns_none,
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
    print(f'Sprint 2.22.0a.2 B (classifier_failure trigger): '
          f'{len(tests) - failed}/{len(tests)} passed')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
