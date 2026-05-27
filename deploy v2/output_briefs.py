#!/usr/bin/env python3
"""
output_briefs.py — Four audience-specific output formats.

Same underlying data, different emphasis:
    1. Buyer Brief:    Is the price fair? What to negotiate?
    2. Seller Brief:   What's my property worth? How to price it?
    3. Investor Brief: What's the yield? Sensitivity analysis?
    4. Valuer Brief:   Full comparables, adjustments, method weights (RICS-style)

Usage:
    from output_briefs import generate_brief

    brief = generate_brief(
        evaluation=eval_result,           # PropertyEvaluation
        audience='buyer',                 # 'buyer' | 'seller' | 'investor' | 'valuer'
        rent_data=rent_estimate,          # from rent_reference
        adjustments=adj_result,           # from comparable_adjustments
        uncertainty=uncertainty_level,    # from material_uncertainty
    )
    print(brief['title_ar'])
    print(brief['sections'])
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
from datetime import datetime


def _fmt(n):
    """Format number with commas."""
    if n is None:
        return '—'
    return f'{round(n):,}'


def _pct(n):
    if n is None:
        return '—'
    return f'{n:+.1f}%' if n >= 0 else f'{n:.1f}%'


def generate_brief(
    evaluation: dict,
    audience: str = 'buyer',
    rent_data: dict = None,
    adjustments: dict = None,
    uncertainty: dict = None,
    income_value: dict = None,
) -> dict:
    """
    Generate audience-specific brief from evaluation data.

    Args:
        evaluation: PropertyEvaluation as dict (or object with to_dict)
        audience: 'buyer' | 'seller' | 'investor' | 'valuer'
        rent_data: output of estimate_annual_rent()
        adjustments: output of adjust_comparables() as dict
        uncertainty: UncertaintyLevel as dict
        income_value: output of income_approach_value()

    Returns:
        dict with title_ar, title_en, sections (list of dicts),
        material_uncertainty_banner, disclaimer
    """
    if hasattr(evaluation, 'to_dict'):
        evaluation = evaluation.to_dict()
    elif hasattr(evaluation, '__dict__'):
        evaluation = asdict(evaluation) if hasattr(evaluation, '__dataclass_fields__') else evaluation.__dict__

    generators = {
        'buyer': _buyer_brief,
        'seller': _seller_brief,
        'investor': _investor_brief,
        'valuer': _valuer_brief,
    }

    gen = generators.get(audience, _buyer_brief)
    return gen(evaluation, rent_data, adjustments, uncertainty, income_value)


def _base_brief(evaluation, uncertainty):
    """Common elements for all briefs."""
    address = evaluation.get('address', '—')
    asset_type = evaluation.get('asset_type', '—')
    plot_area = evaluation.get('plot_area_m2')
    district = evaluation.get('gis_district_aname', '—')

    # Extract valuation figures
    blended = evaluation.get('blended') or {}
    val_total = blended.get('blended_value')
    val_low = blended.get('blended_low')
    val_high = blended.get('blended_high')

    banner = ''
    if uncertainty:
        banner = uncertainty.get('banner_ar', '') if isinstance(uncertainty, dict) else getattr(uncertainty, 'banner_ar', '')

    return {
        'address': address,
        'asset_type': asset_type,
        'plot_area_m2': plot_area,
        'district': district,
        'valuation_total': val_total,
        'valuation_low': val_low,
        'valuation_high': val_high,
        'material_uncertainty_banner': banner,
        'disclaimer': evaluation.get('disclaimer', ''),
        'valuation_date': evaluation.get('valuation_date', datetime.now().strftime('%Y-%m-%d')),
        # Sprint 2.22.0a/2 — tier_label top-level surface (KICKOFF §4.3 + F1).
        # Defensive .get() — engine emits at response root via _tier_label_for();
        # None for refusal paths (insufficient_data / out_of_scope_v1 /
        # asset_type_reality_stop), 'analytical_range' for 8 value-producing methods.
        'tier_label': evaluation.get('tier_label'),
    }


# Sprint 2.19.1 (Fixes #1 + #2): Arabic display strings for provenance values.
# The SQLite snapshot and API JSON keep English machine values for backward
# compatibility; ONLY the user-facing brief renders these translations.
_PROVENANCE_SOURCE_AR = {
    'calibrated': 'مُعايَر من بيانات السوق',
    'hardcoded': 'معدل افتراضي (غير مُعايَر)',
}
# Sprint 2.22.0a.2 C3: relabel tier badges to شواهد taxonomy
# (Anas-locked override of CC's original تغطية draft per resume KICKOFF).
# Codes (reliable/indicative/fallback) unchanged.
_PROVENANCE_CONFIDENCE_AR = {
    'reliable': 'شواهد كافية',
    'indicative': 'شواهد محدودة',
    'fallback': 'شواهد غير كافية — استُخدم معدل افتراضي',
}


def build_cap_rate_provenance_section(provenance):
    """Sprint 2.19: build a brief section describing where the cap rate came from.

    `provenance` is the dict produced by evaluate_unified._lookup_calibrated_cap_rate
    (source='calibrated') or the hardcoded fallback marker (source='hardcoded').
    Returns a brief-section dict, or None when there is nothing to show.

    Mirrors the Sprint 2.16.9 MUC pattern: the canonical response root
    (`output['cap_rate_provenance']`) is authoritative; this section is a
    human-readable echo for the audience brief.

    Sprint 2.19.1 (Fixes #1 + #2): the content now carries Arabic display labels
    (`source_ar`, `confidence_ar`) so the frontend renders Arabic instead of raw
    schema field names. English `source`/`confidence` are retained for machines.
    """
    if not provenance:
        return None
    source = provenance.get('source')
    confidence = provenance.get('confidence')
    if source == 'calibrated':
        body_ar = (
            f"معدل الرسملة المستخدم ({provenance.get('cap_rate_pct')}%) "
            f"معايَر تجريبياً من إيجارات السوق الحالية (PropertyFinder) منسوبةً إلى "
            f"وسيط بيع وزارة العدل لنفس المنطقة والشريحة — "
            f"عيّنة n={provenance.get('sample_size')}، "
            f"مستوى الثقة: {provenance.get('confidence')}، "
            f"آخر تحديث: {provenance.get('last_updated')}."
        )
    else:
        body_ar = (
            f"معدل الرسملة المستخدم ({provenance.get('cap_rate_pct')}%) معدل نموذجي "
            f"(غير معايَر) — لا توجد بيانات إيجار/بيع كافية لهذه المنطقة والشريحة. "
            f"{provenance.get('reason_ar', '')}"
        ).strip()
    return {
        'id': 'cap_rate_provenance',
        'title_ar': 'مصدر معدل الرسملة',
        'content': {
            # Machine-readable (English) — kept for backward compatibility.
            'source': source,
            'confidence': confidence,
            'cap_rate_pct': provenance.get('cap_rate_pct'),
            'sample_size': provenance.get('sample_size'),
            'last_updated': provenance.get('last_updated'),
            # Arabic display strings (Sprint 2.19.1) — what the brief renders.
            'source_ar': _PROVENANCE_SOURCE_AR.get(source, source),
            'confidence_ar': _PROVENANCE_CONFIDENCE_AR.get(confidence, confidence),
            'body_ar': body_ar,
        },
    }


# Sprint 2.22.0a.2 C3: relabel adjustment-grid confidence badges.
_GRID_CONFIDENCE_AR = {
    'reliable': 'شواهد كافية',
    'indicative': 'شواهد محدودة',
    'fallback': 'شواهد غير كافية',
}


def build_comparable_grid_section(grid, audience='buyer'):
    """Sprint 2.20: RICS land comparable-adjustments grid (time-only v1).

    `grid` is AdjustmentGrid.to_dict() from adjustment_grid.build_land_grid.
    Returns a brief-section dict, or None when there is nothing to show
    (fallback used, no comparables, or a secretary audience per §16).

    Complement, not replace: this echoes the time-normalised comparables for
    transparency; the headline value is unchanged. Audience (§16): valuer/
    investor → full per-comparable coefficients; buyer/seller → summary; any
    secretary-like audience → hidden.
    """
    if not grid or grid.get('fallback_used') or not grid.get('comparables'):
        return None
    aud = (audience or '').strip().lower()
    if 'secretary' in aud or 'سكرتير' in aud:
        return None
    detail = 'full' if aud in ('valuer', 'investor', 'مقيم', 'مستثمر') else 'summary'
    conf = grid.get('confidence')
    comps = []
    for c in grid.get('comparables', []):
        t = next((a for a in c.get('adjustments', []) if a.get('factor') == 'time'), None)
        comps.append({
            'date': c.get('date'),
            'price_per_m2_raw': c.get('price_per_m2_raw'),
            'price_per_m2_adjusted': c.get('price_per_m2_adjusted'),
            'time_pct': (t or {}).get('pct_display'),
            'size_m2': c.get('size_m2'),
        })
    return {
        'id': 'comparable_grid',
        'title_ar': 'شبكة المقارنات المعدّلة',
        'content': {
            'detail': detail,
            'adjusted_median_per_m2': grid.get('adjusted_median_per_m2'),
            'n': grid.get('n'),
            'confidence': conf,
            'confidence_ar': _GRID_CONFIDENCE_AR.get(conf, conf),
            'valuation_date': grid.get('valuation_date'),
            'sources': grid.get('sources'),                 # E10 attribution
            'note_ar': grid.get('note_ar'),
            'comparables': comps,
            'footer_ar': ('علاوة الزاوية والحجم ستُضاف لاحقاً عند توفّر بيانات '
                          'مرتبطة جغرافياً (geographically-keyed).'),
        },
    }


# ─────────────────────────────────────────────────────────────────────
# Sprint 2.22.0a/3: tier_breakdown brief section (KICKOFF §1.3 + §4.3).
# Renders body.hybrid.tier_breakdown array (T2 + T3 tier rows) with
# n_used + valuation_date freshness footer. Only emitted when the engine
# response carries a `hybrid` block (currently: Lusail hybrid_t2 path
# per Sprint 2.21.3). Non-hybrid valuations (comparison_*, income, etc.)
# skip this section per Anas R5 decision 2026-05-26.
#
# Schema: pass-through of hybrid.tier_breakdown to keep backend lean —
# UI handles all formatting (discount % conversion, STATUS_AR map,
# FRESHNESS_AR map, toggle interaction for T3 sources).
# ─────────────────────────────────────────────────────────────────────
def build_tier_breakdown_section(evaluation):
    """Sprint 2.22.0a/3: render hybrid tier_breakdown for Lusail hybrid path.

    Returns a brief-section dict suitable for prepending to the audience
    brief sections list, OR None when:
      - evaluation has no `hybrid` block (non-hybrid valuations); or
      - `hybrid.tier_breakdown` is missing/empty/non-list.

    Schema (content):
      {
        'rows': [<T2 row>, <T3 row>, ...],   # passed through from hybrid
        'n_used': int,                         # bj.hybrid.n_used
        'valuation_date': str (YYYY-MM-DD),    # bj.valuation_date (top-level)
      }

    Each row carries hybrid's native keys: tier, weight, raw_value,
    discounted_value, discount_applied, n, and (T3 only) sources[] with
    per-developer detail (developer, project, status, value_per_m2_raw,
    value_per_m2_adjusted, discount_applied, freshness_status).
    UI in `index.html` renderSection('tier_breakdown') handles display
    + STATUS_AR / FRESHNESS_AR mapping + toggle for T3 sources.
    """
    if not evaluation:
        return None
    hybrid = evaluation.get('hybrid') or {}
    rows = hybrid.get('tier_breakdown')
    if not isinstance(rows, list) or len(rows) == 0:
        return None
    return {
        'id': 'tier_breakdown',
        'title_ar': 'تفصيل المصادر',
        'content': {
            'rows': rows,
            'n_used': hybrid.get('n_used'),
            'valuation_date': evaluation.get('valuation_date'),
        },
    }


# ─────────────────────────────────────────────────────────────────────
# Sprint 2.22.0a/5: refusal_reason brief section (KICKOFF §1.6 + F5).
#
# Renders the refusal_reason dict emitted by evaluate_unified
# _compute_refusal_reason() (§5.3 precedence chain dispatch) as a
# user-facing brief section. Section is PREPENDED FIRST in audience
# brief sections list — refusal_reason appearing means tier_breakdown
# + use_case_banner are also absent (gated identically), so this is
# the natural first card.
#
# Returns None when evaluation has no refusal_reason key (non-refusal
# path) — defensive symmetry with the engine-side dispatcher.
# ─────────────────────────────────────────────────────────────────────
def _refusal_reason_section(evaluation):
    """Sprint 2.22.0a/5: refusal_reason brief section.

    Returns brief-section dict from evaluation['refusal_reason'], OR
    None when:
      - evaluation is None / empty, OR
      - refusal_reason key absent or None (non-refusal path)

    Schema content mirrors refusal_templates.get_refusal_template():
      {trigger_id, message_ar, message_en, recommendation_ar, context}.
    UI's renderSection('refusal_reason') renders message_ar + recommendation_ar
    prominently; trigger_id surfaces for telemetry; context typically
    omitted from visual rendering (JSON-only for debugging).
    """
    if not evaluation:
        return None
    rr = evaluation.get('refusal_reason')
    if not rr or not isinstance(rr, dict):
        return None
    return {
        'id': 'refusal_reason',
        'title_ar': 'سبب عدم التقدير',
        'content': rr,
    }


# ─────────────────────────────────────────────────────────────────────
# Sprint 2.22.0a/4: use_case_banner brief section (KICKOFF §6.7 + F4).
#
# Renders BRIEF v3.1 §6.7 use-case segmentation table as 3 bulleted
# lists (suitable_for / not_suitable_for / stage5_required_for). Content
# is STATIC per Anas R2 decision 2026-05-26 — single dimension (use
# case → required stage), NO asset_type / audience / valuation tier
# axes. Same banner for every non-refusal response across all 4
# audience briefs.
#
# Emission gating: REUSE existing `_tier_label_for(method)` refusal
# check from evaluate_unified.py (Sprint 2.22.0a/2 helper) — when
# method is a refusal trigger (insufficient_data / out_of_scope_v1 /
# asset_type_reality_stop), _tier_label_for() returns None, and this
# section returns None too. No per-builder injection needed in
# evaluate logic per Anas architecture refinement Rule #39.
# ─────────────────────────────────────────────────────────────────────
def _use_case_banner_section(evaluation, audience=None):
    """Sprint 2.22.0a/4: use_case_banner section per BRIEF v3.1 §6.7.

    Returns a brief-section dict suitable for prepending to the audience
    brief sections list (after tier_breakdown when present), OR None when:
      - evaluation is None / empty, OR
      - valuation.method is a refusal trigger (gated via _tier_label_for
        returning None — mirrors tier_label suppression on refusal paths
        per Sprint 2.22.0a/2 F1 acceptance criterion + F4 spec).

    The `audience` parameter is accepted for API compatibility but
    NOT used — §6.7 mapping is single-dimension (no audience axis).

    Schema (content):
      {
        'suitable_for':         [<5 use cases>],
        'not_suitable_for':     [<2 use cases>],
        'stage5_required_for':  [<2 use cases>],
      }
    9 items total across 3 buckets per Q2 (b) deliberate-redundancy
    decision (Anas 2026-05-26).
    """
    if not evaluation:
        return None
    # Refusal-gating via Sprint 2.22.0a/2 helper (avoids duplicate logic)
    from evaluate_unified import _tier_label_for, USE_CASE_BANNER
    method = (evaluation.get('valuation') or {}).get('method')
    if _tier_label_for(method) is None:
        return None  # refusal path — banner suppressed (refusal_reason in /5)
    return {
        'id': 'use_case_banner',
        'title_ar': 'حالات الاستخدام',
        'content': USE_CASE_BANNER,
    }


# ─────────────────────────────────────────────────────────────────────
# Sprint 2.22.0a/8: adjustment_ledger_directional brief section placeholder
# (KICKOFF §9.1 row 8 + §1.4).
#
# Empty/informative placeholder shipped in 2.22.0a — actual directional
# adjustment ledger content (3σ inference, attribute-by-attribute deltas,
# tier-source attribution) lands in 2.22.0b when the interactive Q&A
# phase is wired up. The `placeholder: true` flag in the content payload
# is a marker for the Sprint 2.22.0a/12 final consistency pass scan.
#
# Emission gating: refusal-gated identically to use_case_banner —
# _tier_label_for(method) returning None means refusal path, in which
# case directional adjustments are meaningless (no value to adjust).
# When refusal_reason fires, the user sees the refusal explanation
# without a dangling "adjustments coming soon" card.
#
# User-facing copy (Anas Q2 refinement 2026-05-26):
#   - Pure Arabic, no Latin inline ("Stage 2 Q&A" → "مرحلة الأسئلة التفاعلية")
#   - No internal sprint nomenclature ("Sprint 2.22.0b" hidden from user)
#   - Future-tense honest ("ستظهر قريباً عند تفعيل" — not "coming next week")
# ─────────────────────────────────────────────────────────────────────
def _adjustment_ledger_directional_section(evaluation, audience=None):
    """Sprint 2.22.0a/8: directional adjustment ledger placeholder section.

    Returns a brief-section dict to be prepended at position 4 in the
    audience brief sections list (after use_case_banner), OR None when:
      - evaluation is None / empty, OR
      - valuation.method is a refusal trigger (gated via _tier_label_for
        returning None — mirrors use_case_banner + tier_breakdown
        refusal suppression).

    The `audience` parameter is accepted for API compatibility but
    NOT used — the placeholder content is identical across audiences
    (it's a "coming soon" card, not an audience-tailored insight).

    Schema (content):
      {
        'note_ar':     '<Arabic copy>',
        'note_en':     '<English copy>',
        'placeholder': True,   # marker for /12 final consistency scan
      }

    Actual directional-adjustment payload arrives in Sprint 2.22.0b
    when the interactive Q&A captures user-confirmed property attributes
    and the engine renders the 3σ inference ledger.
    """
    if not evaluation:
        return None
    # Refusal-gating via Sprint 2.22.0a/2 helper (identical pattern to /4)
    from evaluate_unified import _tier_label_for
    method = (evaluation.get('valuation') or {}).get('method')
    if _tier_label_for(method) is None:
        return None  # refusal path — placeholder suppressed
    return {
        'id': 'adjustment_ledger_directional',
        'title_ar': 'سجل التعديلات الاتجاهية',
        'content': {
            'note_ar': (
                'التعديلات التفصيلية ستظهر قريباً عند تفعيل مرحلة الأسئلة '
                'التفاعلية.'
            ),
            'note_en': (
                'Detailed adjustments will appear when the interactive '
                'Q&A phase is activated.'
            ),
            'placeholder': True,
        },
    }


def _buyer_brief(evaluation, rent_data, adjustments, uncertainty, income_value):
    """Buyer-focused: Is the price fair? What to negotiate?"""
    base = _base_brief(evaluation, uncertainty)

    # Listing comparison
    listing = evaluation.get('listing_comparison') or {}
    market_pos = evaluation.get('market_position') or {}

    sections = []

    # Sprint 2.22.0a/5 — refusal_reason FIRST when refusal path active.
    # Mutually exclusive with tier_breakdown + use_case_banner (both gate
    # via _tier_label_for() returning None too) — so when refusal_reason
    # is present, the other two are absent. Refusal_reason is the natural
    # first card per cognitive flow ("why no value" first, before anything
    # else).
    _rr = _refusal_reason_section(evaluation)
    if _rr:
        sections.append(_rr)

    # Sprint 2.22.0a/3 — tier_breakdown FIRST when hybrid path active (Lusail).
    # Renders below valuation card per Anas R5 decision (2026-05-26).
    # No-op for non-hybrid valuations (helper returns None).
    _tb = build_tier_breakdown_section(evaluation)
    if _tb:
        sections.append(_tb)

    # Sprint 2.22.0a/4 — use_case_banner AFTER tier_breakdown, before remaining
    # sections (cognitive flow per Anas: "how we got the value" → "when it
    # applies" → "verdict/details"). Suppressed on refusal paths via
    # _tier_label_for() check inside the helper.
    _ub = _use_case_banner_section(evaluation, audience='buyer')
    if _ub:
        sections.append(_ub)

    # Sprint 2.22.0a/8 — adjustment_ledger_directional placeholder AFTER
    # use_case_banner (position 4 in section order). Refusal-gated identically
    # to /4 + /3. Actual content lands in Sprint 2.22.0b when interactive
    # Q&A captures user-confirmed attributes.
    _al = _adjustment_ledger_directional_section(evaluation, audience='buyer')
    if _al:
        sections.append(_al)

    # Section 1: VERDICT — only meaningful when user provided a listing_price.
    # Without it, there's no benchmark to evaluate. Skip the section entirely
    # rather than rendering "position: no_benchmark" raw text.
    if listing.get('listing_price'):
        sections.append({
            'id': 'verdict',
            'title_ar': 'هل السعر معقول؟',
            'content': {
                'listing_price': listing.get('listing_price'),
                'benchmark': listing.get('benchmark_total') or base['valuation_total'],
                'gap_pct': listing.get('gap_pct'),
                'position': market_pos.get('position_label', 'at_market'),
                'description_ar': market_pos.get('description_ar', ''),
            },
        })

    # Section 2: NEGOTIATION RANGE
    # Sprint 2.22.0a.2 C5 DELETE: the negotiation-range section is removed
    # from the user-visible buyer brief. The descriptive reframing GPT-5
    # reviewed in the multi-AI validation batch still anchored buyer
    # behavior via a specific 10% number — but that benchmark doesn't
    # generalize across distressed / inheritance / off-market / premium /
    # low-liquidity cases. Anas locked DELETE over reframe. The numerical
    # thresholds × 1.10 / × 0.90 stay in any engine-internal sanity-check
    # code that still uses them (evaluate_property.above_buyer_ceiling
    # flag, market_regime.buyer_ceiling_multiplier_default, etc.) —
    # only the user-visible section disappears here.

    # Section 3: RED FLAGS
    flags = evaluation.get('listing_flags') or {}
    sections.append({
        'id': 'flags',
        'title_ar': 'المخاطر والإشارات',
        'content': {
            'red_flags': flags.get('red_flags', []),
            'green_flags': flags.get('green_flags', []),
            'has_excluding': flags.get('has_excluding_red_flag', False),
        },
    })

    # Section 4: WHAT TO ASK
    # Sprint 2.21.0.5 (Issue 5): bare land has no building/tenant — swap the
    # building/tenant questions for land-specific due diligence. Buildings keep
    # the original list (regression-safe).
    _dd_at = (evaluation.get('asset_type') or '').lower()
    if _dd_at in ('raw_land', 'land'):
        _dd_questions = [
            'تحقّق من تصنيف المنطقة (R1/R2/R3) من البلدية',
            'اطلب بيان عقاري من وزارة العدل (يكشف الرهونات والخلافات)',
            'تحقّق من خدمات الموقع (كهرباء، ماء، صرف)',
            'اطلب ارتفاع البناء المسموح (طوابق + نسبة بناء + setbacks)',
            'اسأل عن أي قيود قانونية (إرث، حصص غير مفروزة)',
            'افحص منسوب الأرض مقارنة بالشارع (تكلفة الردم/الحفر)',
            'تحقّق من مدى توفّر البنية التحتية (شارع مرصوف، كهرباء قريبة)',
        ]
    else:
        _dd_questions = [
            'اطلب بيان عقاري من وزارة العدل (يكشف الرهونات والخلافات)',
            'اسأل عن عمر البناء الحقيقي (ليس ما يقوله البائع)',
            'تحقق من تصنيف المنطقة (R1/R2/R3) — يحدد ما يمكنك بناؤه',
            'اطلب فواتير الخدمات (كهرباء/ماء) لآخر سنة',
            'إن كان مؤجراً: اطلب عقود الإيجار الحالية',
        ]
    sections.append({
        'id': 'due_diligence',
        'title_ar': 'أسئلة يجب طرحها قبل الشراء',
        'content': _dd_questions,
    })

    # Section 5: MATERIAL UNCERTAINTY (Sprint 2.14.0)
    # Sprint 2.22.0a/12 Phase 1.5b — citation updated (multi-AI validation
    # corrected the 2025 effective-edition transition):
    # adds the Material Valuation Uncertainty (MVU) clause per VPGA 10 +
    # VPS 6 (RICS Red Book Global Standards, effective 31 January 2025)
    # and IVS 106 (IVS, effective 31 January 2025), alongside per-property
    # uncertainty factors.
    # Was previously only in valuer brief — now in buyer brief too because
    # the index.html MUC banner reads from this section.
    if uncertainty:
        unc = uncertainty if isinstance(uncertainty, dict) else asdict(uncertainty)
        sections.append({
            'id': 'material_uncertainty',
            # Sprint 2.22.0a/12 Phase 1.5b — RICS citation updated to current
            # effective-edition canonical reference (VPGA 10 + VPS 6 + IVS 106,
            # effective 31 January 2025). Multi-AI validation caught the
            # 2025-edition transition that Sprint 2.22.0a/9 missed (VPS 3 → VPS 6
            # renumbering; IVS 103 → IVS 106). See material_uncertainty.py
            # docstring for the full standards audit trail.
            # Sprint 2.22.0a.2 Pattern A: LRM-wrap Latin tokens (Operational_Rules #25).
            'title_ar': 'تحفظات مادية وفق ‎RICS Red Book Global Standards‎ (‎effective 31 January 2025‎) — ‎VPGA 10‎ و ‎VPS 6‎ — و ‎IVS‎ (‎effective 31 January 2025‎) — ‎IVS 106‎',
            'title_en': 'Material Uncertainty Declaration per RICS Red Book Global Standards (effective 31 January 2025) — VPGA 10 (Material Valuation Uncertainty) and VPS 6 (Valuation Reports) — and IVS (effective 31 January 2025) — IVS 106 (Documentation and Reporting)',
            'content': {
                'level': unc.get('level'),
                'factors': unc.get('factors', []),
                'known_unknowns': unc.get('known_unknowns', []),
                'recommendations': unc.get('recommendations', []),
                'rics_compliant': unc.get('rics_compliant', False),
                # Sprint 2.22.0a/12 Phase 1.5b — citation reflects current effective
                # edition: Material Valuation Uncertainty clause fields per VPGA 10
                # + VPS 6 (RICS Red Book Global Standards, effective 31 January 2025)
                # and IVS 106 (IVS, effective 31 January 2025).
                'muc_clause_ar': unc.get('muc_clause_ar'),
                'muc_clause_en': unc.get('muc_clause_en'),
                'muc_basis_ar': unc.get('muc_basis_ar'),
                'muc_review_recommendation_ar': unc.get('muc_review_recommendation_ar'),
            },
        })

    return {
        'audience': 'buyer',
        'title_ar': 'تقرير المشتري',
        'title_en': 'Buyer Brief',
        **base,
        'sections': sections,
    }


def _seller_brief(evaluation, rent_data, adjustments, uncertainty, income_value):
    """Seller-focused: What's my property worth? How to price it?"""
    base = _base_brief(evaluation, uncertainty)
    sections = []

    # Sprint 2.22.0a/5 — refusal_reason FIRST when refusal path. See _buyer_brief.
    _rr = _refusal_reason_section(evaluation)
    if _rr:
        sections.append(_rr)

    # Sprint 2.22.0a/3 — tier_breakdown FIRST when hybrid (Lusail). See _buyer_brief.
    _tb = build_tier_breakdown_section(evaluation)
    if _tb:
        sections.append(_tb)

    # Sprint 2.22.0a/4 — use_case_banner AFTER tier_breakdown. See _buyer_brief.
    _ub = _use_case_banner_section(evaluation, audience='seller')
    if _ub:
        sections.append(_ub)

    # Sprint 2.22.0a/8 — adjustment_ledger_directional placeholder. See _buyer_brief.
    _al = _adjustment_ledger_directional_section(evaluation, audience='seller')
    if _al:
        sections.append(_al)

    # Section 1: YOUR PROPERTY VALUE
    sections.append({
        'id': 'valuation',
        'title_ar': 'قيمة عقارك',
        'content': {
            'estimated_value': base['valuation_total'],
            'range_low': base['valuation_low'],
            'range_high': base['valuation_high'],
            'note': 'مبني على صفقات بيع فعلية مسجلة في وزارة العدل — ليس أسعار إعلانات.',
        },
    })

    # Section 2: PRICING STRATEGY
    if base['valuation_total']:
        val = base['valuation_total']
        sections.append({
            'id': 'pricing',
            'title_ar': 'استراتيجية التسعير',
            'content': {
                'aggressive_price': round(val * 1.15),
                'realistic_price': round(val * 1.10),
                'quick_sale_price': round(val * 1.00),
                'market_ceiling': round(val * 1.30),
                'note': ('ابدأ بسعر وسيط MoJ + 10-15%. '
                         'لا تتجاوز +30% — السوق يرفض الإعلانات المبالغة. '
                         'حدّث الإعلان كل أسبوعين.'),
            },
        })

    # Section 3: TREND
    trend = evaluation.get('trend')
    if trend:
        sections.append({
            'id': 'trend',
            'title_ar': 'اتجاه السوق',
            'content': trend,
        })

    # Section 4: SELLING TIPS
    sections.append({
        'id': 'tips',
        'title_ar': 'نصائح للبيع',
        'content': [
            'أفرغ العقار إن أمكن — الوحدات الفارغة تُباع أسرع',
            'صوِّر 6-10 صور جودة عالية (لا لقطات شاشة)',
            'اذكر سعر القدم المربع في الإعلان (المشتري يقارن بهذا)',
            'استجب للاستفسارات خلال ساعتين',
            'لا تكشف عن سعرك الأدنى مبكراً',
        ],
    })

    return {
        'audience': 'seller',
        'title_ar': 'تقرير البائع',
        'title_en': 'Seller Brief',
        **base,
        'sections': sections,
    }


def _investor_brief(evaluation, rent_data, adjustments, uncertainty, income_value):
    """Investor-focused: Yield, payback, sensitivity."""
    base = _base_brief(evaluation, uncertainty)
    sections = []

    # Sprint 2.22.0a/5 — refusal_reason FIRST when refusal path. See _buyer_brief.
    _rr = _refusal_reason_section(evaluation)
    if _rr:
        sections.append(_rr)

    # Sprint 2.22.0a/3 — tier_breakdown FIRST when hybrid (Lusail). See _buyer_brief.
    _tb = build_tier_breakdown_section(evaluation)
    if _tb:
        sections.append(_tb)

    # Sprint 2.22.0a/4 — use_case_banner AFTER tier_breakdown. See _buyer_brief.
    _ub = _use_case_banner_section(evaluation, audience='investor')
    if _ub:
        sections.append(_ub)

    # Sprint 2.22.0a/8 — adjustment_ledger_directional placeholder. See _buyer_brief.
    _al = _adjustment_ledger_directional_section(evaluation, audience='investor')
    if _al:
        sections.append(_al)

    # Section 1: YIELD ANALYSIS
    rental = evaluation.get('rental_analysis') or {}
    yield_section = {
        'gross_yield_pct': None,
        'net_yield_pct': None,
        'payback_years': None,
        'noi': None,
    }
    if rental and 'on_valuation' in rental:
        ov = rental['on_valuation']
        yield_section.update({
            'gross_yield_pct': ov.get('gross_yield_pct'),
            'net_yield_pct': ov.get('net_yield_pct'),
            'payback_years': ov.get('payback_years'),
            'noi': rental.get('annual_net'),
        })
    elif income_value:
        yield_section.update({
            'gross_yield_pct': income_value.get('gross_yield_pct'),
            'net_yield_pct': income_value.get('net_yield_pct'),
            'noi': income_value.get('noi'),
        })

    sections.append({
        'id': 'yield',
        'title_ar': 'تحليل العائد',
        'content': yield_section,
    })

    # Section 2: INCOME VALUE
    if income_value:
        sections.append({
            'id': 'income_value',
            'title_ar': 'القيمة بمنهج الدخل',
            'content': {
                'income_value': income_value.get('income_value'),
                'cap_rate_used': income_value.get('cap_rate_used'),
                'annual_gross': income_value.get('annual_gross_rent'),
                'noi': income_value.get('noi'),
                'costs': income_value.get('costs'),
                'opex_ratio': income_value.get('opex_ratio'),
            },
        })

    # Section 3: SENSITIVITY
    if income_value and 'sensitivity' in income_value:
        sections.append({
            'id': 'sensitivity',
            'title_ar': 'تحليل الحساسية',
            'content': income_value['sensitivity'],
            'note': 'ماذا لو تغيّر Cap Rate أو رسوم الخدمات؟',
        })

    # Section 4: RENT DATA
    if rent_data:
        sections.append({
            'id': 'rent_reference',
            'title_ar': 'مرجع الإيجار',
            'content': {
                'monthly_median': rent_data.get('monthly_median'),
                'annual_range': [rent_data.get('annual_low'), rent_data.get('annual_high')],
                'n': rent_data.get('n'),
                'confidence': rent_data.get('confidence'),
                'caveats': rent_data.get('caveats', []),
            },
        })

    # Section 5: MARKET CONTEXT
    sections.append({
        'id': 'market_context',
        'title_ar': 'السياق السوقي',
        'content': {
            'qatar_benchmark': '5-6% عائد صافي للشقق السكنية = طبيعي',
            'above_6_net': 'أكثر من 6% صافي = فرصة تستحق الفحص',
            'below_4_net': 'أقل من 4% صافي = ضعيف، تجنَّب',
        },
    })

    return {
        'audience': 'investor',
        'title_ar': 'تقرير المستثمر',
        'title_en': 'Investor Brief',
        **base,
        'sections': sections,
    }


def _valuer_brief(evaluation, rent_data, adjustments, uncertainty, income_value):
    """Valuer-focused (RICS): Full comparables, adjustments, method weights."""
    base = _base_brief(evaluation, uncertainty)
    sections = []

    # Sprint 2.22.0a/5 — refusal_reason FIRST when refusal path. See _buyer_brief.
    _rr = _refusal_reason_section(evaluation)
    if _rr:
        sections.append(_rr)

    # Sprint 2.22.0a/3 — tier_breakdown FIRST when hybrid (Lusail). See _buyer_brief.
    # Single rendering path per Q1 Option (b) — UI toggle handles depth.
    _tb = build_tier_breakdown_section(evaluation)
    if _tb:
        sections.append(_tb)

    # Sprint 2.22.0a/4 — use_case_banner AFTER tier_breakdown. See _buyer_brief.
    _ub = _use_case_banner_section(evaluation, audience='valuer')
    if _ub:
        sections.append(_ub)

    # Sprint 2.22.0a/8 — adjustment_ledger_directional placeholder. See _buyer_brief.
    _al = _adjustment_ledger_directional_section(evaluation, audience='valuer')
    if _al:
        sections.append(_al)

    # Section 1: METHODOLOGY APPLIED
    blended = evaluation.get('blended') or {}
    moj_val = evaluation.get('valuation') or {}
    repl_cost = evaluation.get('replacement_cost') or {}

    methods = []
    if moj_val.get('moj_median_total'):
        methods.append({
            'name': 'Market Comparable (MoJ)',
            'value': moj_val.get('moj_median_total'),
            'weight': blended.get('moj_weight', 0),
            'n': moj_val.get('bracket_n'),
            'bracket': moj_val.get('bracket_label'),
            'window': moj_val.get('window_used'),
        })
    if repl_cost.get('total_replacement_value'):
        methods.append({
            'name': 'Replacement Cost',
            'value': repl_cost.get('total_replacement_value'),
            'weight': blended.get('replacement_weight', 0),
        })
    if income_value:
        methods.append({
            'name': 'Income Capitalization',
            'value': income_value.get('income_value'),
            'weight': 0,  # will be set when 3-way blend is implemented
            'cap_rate': income_value.get('cap_rate_used'),
            'noi': income_value.get('noi'),
        })

    sections.append({
        'id': 'methodology',
        'title_ar': 'المنهجية المطبقة',
        'title_en': 'Methodology Applied',
        'content': {
            'methods': methods,
            'blend_reason': blended.get('blend_reason', ''),
            'blended_value': blended.get('blended_value'),
            'range': [blended.get('blended_low'), blended.get('blended_high')],
        },
    })

    # Section 2: COMPARABLE ADJUSTMENTS
    if adjustments:
        adj_data = adjustments if isinstance(adjustments, dict) else asdict(adjustments)
        sections.append({
            'id': 'adjustments',
            'title_ar': 'جدول تعديل المقارنات',
            'title_en': 'Comparable Adjustments Table',
            'content': {
                'raw_median_per_m2': adj_data.get('raw_median_per_m2'),
                'adjusted_median_per_m2': adj_data.get('adjusted_median_per_m2'),
                'adjusted_median_total': adj_data.get('adjusted_median_total'),
                'method_note': adj_data.get('method_note'),
                'n': adj_data.get('n'),
                'table': adj_data.get('adjustment_table', []),
            },
        })

    # Section 3: DATA SOURCES
    sources = [
        {'name': 'وزارة العدل — صفقات بيع فعلية', 'type': 'primary', 'date': 'أسبوعي'},
        {'name': 'نظم المعلومات الجغرافية (GIS قطر)', 'type': 'primary', 'date': 'مستمر'},
    ]
    if rent_data:
        sources.append({
            'name': 'المنصة العقارية — معاملات إيجار',
            'type': 'secondary',
            'date': str(rent_data.get('window_months', 24)) + ' شهر',
        })
    sections.append({
        'id': 'sources',
        'title_ar': 'مصادر البيانات',
        'title_en': 'Data Sources Consulted',
        'content': sources,
    })

    # Section 4: MATERIAL UNCERTAINTY
    if uncertainty:
        unc = uncertainty if isinstance(uncertainty, dict) else asdict(uncertainty)
        sections.append({
            'id': 'material_uncertainty',
            # Sprint 2.22.0a/12 Phase 1.5b — RICS citation updated to current
            # effective-edition canonical reference (VPGA 10 + VPS 6 + IVS 106,
            # effective 31 January 2025). See sibling material_uncertainty
            # section above (line ~579) for the standards audit trail.
            # This is the _valuer_brief site.
            'title_ar': 'تحفظات مادية',
            'title_en': 'Material Uncertainty Declaration per RICS Red Book Global Standards (effective 31 January 2025) — VPGA 10 (Material Valuation Uncertainty) and VPS 6 (Valuation Reports) — and IVS (effective 31 January 2025) — IVS 106 (Documentation and Reporting)',
            'content': {
                'level': unc.get('level'),
                'factors': unc.get('factors', []),
                'known_unknowns': unc.get('known_unknowns', []),
                'recommendations': unc.get('recommendations', []),
                'rics_compliant': unc.get('rics_compliant', False),
                # Sprint 2.22.0a/12 Phase 1.5b — citation reflects current effective
                # edition: Material Valuation Uncertainty clause fields per VPGA 10
                # + VPS 6 (RICS Red Book Global Standards, effective 31 January 2025)
                # and IVS 106 (IVS, effective 31 January 2025).
                'muc_clause_ar': unc.get('muc_clause_ar'),
                'muc_clause_en': unc.get('muc_clause_en'),
                'muc_basis_ar': unc.get('muc_basis_ar'),
                'muc_review_recommendation_ar': unc.get('muc_review_recommendation_ar'),
            },
        })

    # Section 5: REASONING TRACE
    trace = evaluation.get('reasoning_trace')
    if trace:
        sections.append({
            'id': 'reasoning_trace',
            'title_ar': 'سلسلة المنطق',
            'title_en': 'Reasoning Trace (Audit Trail)',
            'content': trace,
        })

    # Section 6: GAPS
    sections.append({
        'id': 'gaps',
        'title_ar': 'فجوات البيانات',
        'title_en': 'Data Gaps',
        'content': [
            'MoJ لا تفصل بين عقار جديد ومتهالك (حالة المبنى غير معروفة)',
            'لا فصل قيمة الأرض عن البناء في صفقات الفلل',
            'بيانات الإيجار على مستوى البلدية فقط — لا منطقة فرعية',
            'لا بيانات per-tower (نفس المبنى الفاخر والعادي يُعامَلان متشابهين)',
            'الإعلانات النشطة لا تُسحَب آلياً — سياق المنافسة مفقود',
        ],
    })

    return {
        'audience': 'valuer',
        'title_ar': 'تقرير المُقيِّم',
        'title_en': 'Valuer Brief (RICS-aligned)',
        **base,
        'sections': sections,
    }
