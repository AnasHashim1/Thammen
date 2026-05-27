"""
refusal_templates.py — Sprint 2.22.0a/5 refusal trigger registry.

Centralised dict of refusal-reason templates emitted by the engine on
every refusal-path response. Companion to _compute_refusal_reason()
in evaluate_unified.py which dispatches by precedence chain per
BRIEF v3.1 §5.3 + KICKOFF §5.3 (with 6th trigger added in Sprint
2.22.0a per Anas Q1 (d) decision 2026-05-26).

================================================================
TEMPLATE PARTITION (per Anas Q1 decision, /5 commit message):

  • 5 BRIEF v3.1 §1.6 TEMPLATES (methodology-driven refusals — the
    engine TRIED to value and hit a methodological wall):
        1. comp_density_sparse       — MoJ sample too thin
        2. spatial_ambiguity         — can't link to a single parcel
        3. regime_shift              — district in transition
        4. asset_scale_extreme       — exceeds comparable scale (E20)
        5. density_gated_district    — district uncovered (Pearl in
                                        2.22.0a per §1.7 ship-gate)

  • 1 SPRINT 2.22.0a ENGINE-CAPABILITY TEMPLATE (the engine refuses
    to attempt valuation because the asset class is outside Sprint 1's
    methodology scope):
        6. asset_class_out_of_scope  — commercial / industrial /
                                        agricultural (existing out_of_
                                        scope_v1 builder path since
                                        Sprint 2.21.0.7 era; formally
                                        templated in 2.22.0a/5)

  KICKOFF F5 ("5 active triggers") to be amended to "6 active" in
  sub-sprint 2.22.0a/12 final consistency pass alongside C1+C2+§4.1
  line 96 cosmetic items (4 accumulating).

================================================================
Sprint 2.22.0a.2 Pattern B added the 7th template:

  7. classifier_failure  — engine could not classify the property at
                            all (asset_type='unknown' from upstream
                            QARS coverage gap). Distinct from
                            spatial_ambiguity (#2 — fires only when
                            asset_type_reality_stop STOPS after a
                            successful classification) and from
                            comp_density_sparse (#6 — fires only when
                            asset_type is known but MoJ comparables
                            are sparse).

================================================================
NOTE: asset_uniqueness (3σ outlier check) deferred to Sprint 2.22.y
per KICKOFF §2.3 — single logical unit with 3σ compute logic, both
ship together or not at all. NOT registered in REFUSAL_TEMPLATES
(negative test in /5 test file guards against accidental addition).
"""

from typing import Any, Dict, Optional


# ─────────────────────────────────────────────────────────────────────
# 6 active refusal templates (5 §1.6 + 1 §1.6-extended-2.22.0a)
# ─────────────────────────────────────────────────────────────────────
REFUSAL_TEMPLATES: Dict[str, Dict[str, str]] = {

    'comp_density_sparse': {
        'message_ar': (
            'هذه المنطقة فيها أقل من 5 صفقات بيع مقارنة خلال آخر 6 أشهر '
            'لعقارات بهذا الحجم والنوع. التقدير الآلي لا يصل إلى مستوى '
            'الموثوقية المطلوب.'
        ),
        'message_en': (
            'This district has fewer than 5 comparable transactions in the '
            'past 6 months for properties of this size and type. An automated '
            'estimate cannot reach reliable confidence.'
        ),
        'recommendation_ar': 'نوصي بتقييم متخصص لعقارك من خلال مُقيِّم معتمد.',
    },

    'spatial_ambiguity': {
        'message_ar': (
            'تعذّر ربط عقارك بمبنى أو قطعة وحيدة في نظامنا. لإصدار تقدير '
            'موثوق، نوصي بتقييم متخصص مع تحقّق ميداني.'
        ),
        'message_en': (
            'Your property could not be uniquely linked to a single building '
            'or parcel in our system. To produce a confident valuation, '
            'we recommend a specialized assessment with on-site verification.'
        ),
        'recommendation_ar': 'تقييم متخصص مع تحقّق ميداني موصى به.',
    },

    'regime_shift': {
        'message_ar': (
            'هذه المنطقة شهدت تغيّرات سوقية كبيرة خلال آخر 90 يوماً{event_name}. '
            'الصفقات المقارنة في فترة انتقالية. نوصي بتقييم متخصص حتى يستقرّ السوق.'
        ),
        'message_en': (
            'This district has experienced significant market changes in the '
            'past 90 days{event_name}. Comparable transactions are in transition. '
            'A specialized assessment is recommended until the market stabilizes.'
        ),
        'recommendation_ar': 'تقييم متخصص موصى به حتى استقرار السوق.',
    },

    'asset_scale_extreme': {
        'message_ar': (
            'حجم عقارك يتجاوز أي صفقة مقارنة في قاعدة بياناتنا. التقدير الآلي '
            'لا يستطيع التعميم بأمان. تقييم متخصص مطلوب لأصل بهذا الحجم.'
        ),
        'message_en': (
            "This property's scale exceeds any comparable transaction in our "
            'database. An automated estimate cannot extrapolate reliably. '
            'A specialized assessment is required for an asset of this magnitude.'
        ),
        'recommendation_ar': 'تقييم متخصص مطلوب.',
    },

    # NEW per Finding §3.1 (Phase 3 audit) + Pearl A5 self-discovery
    'density_gated_district': {
        'message_ar': (
            'بيانات هذه المنطقة في طور الاكتمال. لا نوفّر حالياً تقديراً آلياً '
            'لعقارات في هذا الموقع. نوصي بتقييم متخصص.'
        ),
        'message_en': (
            "This district's data coverage is still being completed. "
            'We currently cannot provide an automated estimate for properties '
            'in this location. A specialized assessment is recommended.'
        ),
        'recommendation_ar': 'نوصي بتقييم متخصص أثناء عملنا على توسيع التغطية.',
    },

    # Sprint 2.22.0a.2 Pattern B (7th template): classifier_failure fires
    # when the upstream QARS service yields 0 features for the submitted
    # address and asset_type falls back to 'unknown'. Distinct semantic
    # from spatial_ambiguity (asset_type_reality_stop after a SUCCESSFUL
    # classification) and from comp_density_sparse (known asset_type +
    # sparse MoJ comparables). Gemini-approved verbatim per
    # docs/MULTI_AI_VALIDATION_BATCH_2p22p0a2.md §6.
    'classifier_failure': {
        'message_ar': (
            'لم نتمكّن من تحديد نوع العقار من البيانات الحكومية المتاحة. '
            'قد يكون العنوان غير مفهرس حالياً في قاعدة QARS أو خارج نطاق '
            'التغطية. نوصي بالتحقّق من بيانات العنوان أو التواصل معنا إذا '
            'كانت المُدخَلات صحيحة.'
        ),
        'message_en': (
            'We could not classify this property from available government '
            'data. The address may not yet be indexed in QARS, or may fall '
            'outside current coverage. Please verify the address details, '
            'or contact us if the entered values are correct.'
        ),
        'recommendation_ar': 'تحقّق من بيانات العنوان أو تواصل معنا.',
    },

    # NEW for Sprint 2.22.0a per Anas Q1 (d) decision — distinct semantic
    # from the 5 §1.6 triggers above (engine-capability vs methodology-walls)
    'asset_class_out_of_scope': {
        'message_ar': (
            'نوع هذا العقار خارج نطاق الإصدار الحالي من ثمّن. التقدير الآلي '
            'للأصول التجارية / الصناعية / الزراعية يحتاج منهجية متخصصة.'
        ),
        'message_en': (
            "This property's asset class is outside the current scope of "
            'Thammen. Automated valuation for commercial / industrial / '
            'agricultural assets requires specialized methodology.'
        ),
        'recommendation_ar': 'نوصي بتقييم متخصص مع مُقيِّم خبير في هذه الفئة.',
    },
}


# Trigger ids that explicitly support context substitution via .format()
# (Sprint 2.22.0a/2 KICKOFF amendment §5.1 footer note documents the
# `event_name` placeholder for regime_shift; other triggers have no
# placeholders today but could acquire them in 2.22.0b — keep helper
# resilient to absent placeholders).
_TEMPLATES_WITH_SUBSTITUTION = frozenset({'regime_shift'})


def get_refusal_template(trigger_id: str, **context: Any) -> Dict[str, Any]:
    """Return the refusal_reason dict for `trigger_id`.

    Shape: {trigger_id, message_ar, message_en, recommendation_ar, context}.

    For `regime_shift` only: applies .format() substitution with the
    `event_name` keyword. Default event_name='' handles the empty-registry
    case (Sprint 2.22.0a — `district_regimes.json` is `{"events": []}`)
    without breaking template substitution. When events populate in 2.22.0b,
    pass `event_name=" — <event description>"` (with leading separator).

    Raises ValueError on unknown trigger_id — explicit guard per Anas
    decision (no silent default — registry IS source of truth).

    Standard context fields (Q3 (ii) decision) emitted in returned
    refusal_reason.context when supplied by caller: asset_type, district_ar,
    plot_area_m2 (compound paths). Caller decides which to pass.
    """
    if trigger_id not in REFUSAL_TEMPLATES:
        raise ValueError(
            f"Unknown refusal trigger_id: {trigger_id!r}. "
            f"Registered triggers: {sorted(REFUSAL_TEMPLATES.keys())}"
        )

    tpl = REFUSAL_TEMPLATES[trigger_id]
    message_ar = tpl['message_ar']
    message_en = tpl['message_en']

    if trigger_id in _TEMPLATES_WITH_SUBSTITUTION:
        # Apply .format() substitution; default empty event_name for
        # empty-registry case (Sprint 2.22.0a regime_shift never fires
        # so this branch only runs in 2.22.0b+).
        event_name = context.get('event_name', '')
        message_ar = message_ar.format(event_name=event_name)
        message_en = message_en.format(event_name=event_name)

    # Build context dict from caller-supplied kwargs (Q3 (ii) standard
    # signals — caller is responsible for what to populate). Strip None
    # values to keep payload clean.
    out_context = {k: v for k, v in context.items() if v is not None}

    return {
        'trigger_id': trigger_id,
        'message_ar': message_ar,
        'message_en': message_en,
        'recommendation_ar': tpl['recommendation_ar'],
        'context': out_context,
    }


def is_registered(trigger_id: str) -> bool:
    """Helper: returns True if trigger_id is in REFUSAL_TEMPLATES.

    Used by tests + defensive callers to avoid ValueError on unknown ids
    (e.g., when reading user-supplied or migration data).
    """
    return trigger_id in REFUSAL_TEMPLATES
