"""Sample brief invocations for Sprint 2.22.0a/5 STOP report.

Demonstrates _compute_refusal_reason() dispatch across the 6 §5.3
precedence chain paths Anas requested:
  (1) Pearl (insufficient_data + density_gated_district)
  (2) compound_large 51/835/17 (asset_scale_extreme)
  (3) villa value-producing (no refusal — tier_label='analytical_range')
  (4) Type-A else fallback (comp_density_sparse)
  (5) PIN 66030258 (asset_type_reality_stop → spatial_ambiguity)
  (6) out_of_scope_v1 (commercial asset → asset_class_out_of_scope)

File-based probe per Rule #34. Read-only — no engine state mutation.
"""
import sys
import json

sys.path.insert(0, '.')

from evaluate_unified import _compute_refusal_reason, _tier_label_for


def show(label: str, method: str, **ctx) -> None:
    """Print a one-sample summary."""
    tier = _tier_label_for(method)
    rr = _compute_refusal_reason(method=method, **ctx)
    print('-' * 72)
    print(f'  CASE: {label}')
    print(f'  method                = {method!r}')
    print(f'  asset_type            = {ctx.get("asset_type")!r}')
    print(f'  district_ar           = {ctx.get("district_ar")!r}')
    if ctx.get('plot_area_m2') is not None:
        print(f'  plot_area_m2          = {ctx["plot_area_m2"]}')
    print(f'  tier_label (/2)       = {tier!r}')
    if rr is None:
        print(f'  refusal_reason        = None  (mutual-exclusion with tier_label)')
    else:
        print(f'  refusal_reason.trigger_id      = {rr["trigger_id"]!r}')
        print(f'  refusal_reason.message_ar      = {rr["message_ar"][:90]}{"…" if len(rr["message_ar"])>90 else ""}')
        print(f'  refusal_reason.recommendation_ar = {rr["recommendation_ar"][:90]}{"…" if len(rr["recommendation_ar"])>90 else ""}')
        print(f'  refusal_reason.context         = {json.dumps(rr["context"], ensure_ascii=False)}')


def main() -> int:
    print('=' * 72)
    print('  Sprint 2.22.0a/5 — sample brief invocations (6 cases)')
    print('=' * 72)

    # (1) Pearl insufficient_data — density_gated_district fires
    show(
        '(1) Pearl insufficient_data',
        method='insufficient_data',
        asset_type='apartment_building',
        district_ar='جزيرة اللؤلؤة',
        district_en='The Pearl',
        plot_area_m2=None,
    )

    # (2) compound_large 51/835/17 — extent=67,536 m² → asset_scale_extreme
    show(
        '(2) compound_large 51/835/17 (extent=67,536 m²)',
        method='insufficient_data',
        asset_type='compound_large',
        district_ar='الدفنة',
        plot_area_m2=67536,
    )

    # (3) villa value-producing — no refusal, tier_label='analytical_range'
    show(
        '(3) villa standalone (comparison_bracket value-producing)',
        method='comparison_bracket',
        asset_type='standalone_villa',
        district_ar='الغرافة',
        plot_area_m2=750,
    )

    # (4) Type-A else fallback — comp_density_sparse (default)
    show(
        '(4) Type-A else fallback (non-Pearl, non-compound_large)',
        method='insufficient_data',
        asset_type='apartment_building',
        district_ar='الخيسة',
        plot_area_m2=None,
    )

    # (5) PIN 66030258 — asset_type_reality_stop → spatial_ambiguity
    show(
        '(5) PIN 66030258 (asset_type_reality_stop)',
        method='asset_type_reality_stop',
        asset_type='compound_large',
        district_ar='عين خالد',
    )

    # (6) out_of_scope_v1 (commercial asset) → asset_class_out_of_scope
    show(
        '(6) out_of_scope_v1 (commercial asset)',
        method='out_of_scope_v1',
        asset_type='commercial',
        district_ar='الدفنة',
    )

    # NEGATIVE — exactly 15K m² boundary check (>= per E20)
    show(
        '(7) NEGATIVE — compound_large exactly 15,000 m² (>= boundary)',
        method='insufficient_data',
        asset_type='compound_large',
        district_ar='الدفنة',
        plot_area_m2=15000,
    )

    # NEGATIVE — compound_large just under 15K → comp_density_sparse
    show(
        '(8) NEGATIVE — compound_large at 14,999 m² (< boundary)',
        method='insufficient_data',
        asset_type='compound_large',
        district_ar='الدفنة',
        plot_area_m2=14999,
    )

    print('=' * 72)
    print('  All 8 sample invocations rendered.')
    print('=' * 72)
    return 0


if __name__ == '__main__':
    sys.exit(main())
