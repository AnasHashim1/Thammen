"""
Sprint 2.14 — market_regime.py

Encodes Thammen's awareness of the current Qatar market regime
(post-disruption recession, May 2026) and translates it into concrete
adjustments to the buyer-side recommendations produced by the engine.

WHY THIS MODULE EXISTS:
  MoJ's last published transaction is 2025-12-31. The Iran-Israel war
  began 2026-02-28 with direct strikes on Qatar (Ras Laffan LNG hub).
  The Strait of Hormuz has been effectively closed since the same date.
  Qatar's population dropped by 36,000 in March alone (expat outflow).
  March 2026 saw only 154 residential sales nationwide (1 in Doha).

  Every valuation Thammen produces today is built on data from a market
  regime that ended two months before the data's freshness gap began.
  Sprint 2.7 surfaces "data is 133 days stale". This module says WHY
  that matters: the staleness coincides with the largest structural
  shock to Qatar's real estate fundamentals in a decade.

WHAT IT DOES:
  Given (moj_median_per_m2, plot_area, optional building_age_years),
  returns regime-adjusted buyer recommendations:
    - buyer_ceiling     : maximum reasonable price to pay today
    - opening_offer     : where to start negotiating
    - negotiation_room  : ceiling − opening
  Plus a transparent breakdown of every adjustment applied and why.

DESIGN PRINCIPLES:
  1. Honest over precise. Every adjustment cites its evidence source.
  2. Auditable. shock_layers list every macro factor with date + source.
  3. Reversible. When MoJ resumes publishing post-war transactions and
     they reflect the new pricing, switch regime back to NORMAL and
     adjustments go to zero — Thammen heals naturally.
  4. No engine input changes. This module produces ADDITIONS to the
     response. Existing fields (valuation.amount, etc.) untouched.

SOURCES BACKING CURRENT REGIME CALIBRATION:
  - MECouncil 2026-05-05: "structural rather than cyclical"
  - Oxford Economics: GCC growth −4.6pp 2026, Qatar even sharper
  - QatarEnergy: full LNG capacity restoration could take 5 years
  - Aqarat (Qatar Real Estate Regulatory Authority): 154 March sales
  - Qatar Planning & Statistics Authority: 36,000 population drop
  - Mordor Intelligence: -10% Doha residential since 2022, -20% rents
  - User testimony (Anas, Qatari, May 2026): "10% negotiation
    achievable, especially for older properties"

CALIBRATION DERIVATION:
  Pre-war buyer hard ceiling per Section 4 Project Instructions:
    ceiling = MoJ × 1.10
  Asking premium per EMPIRICAL_FINDINGS (May 2026 measurement):
    asking ≈ MoJ × 1.14
  Pre-war typical negotiation:
    asking → ceiling = ~4% off

  Current regime negotiation per user testimony:
    new property:  ~10% off asking → MoJ × 1.14 × 0.90 ≈ MoJ × 1.03
    old property:  ~15% off asking → MoJ × 1.14 × 0.85 ≈ MoJ × 0.97

  Therefore current regime-adjusted ceilings:
    new property:  MoJ × 1.00  (was MoJ × 1.10, drop of 10 percentage points)
    old property:  MoJ × 0.95  (additional 5pp drop for stagnant stock)

  Opening offer floor (to leave negotiation room):
    new property:  MoJ × 0.90
    old property:  MoJ × 0.85

USAGE:
    from market_regime import current_regime, regime_recommendation
    rec = regime_recommendation(
        moj_median_per_m2=3000,
        plot_area_m2=600,
        building_age_years=15,
    )
    rec.buyer_ceiling_qar         # 1,710,000
    rec.opening_offer_qar         # 1,530,000
    rec.adjustments_applied_ar    # list of human-readable explanations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ─── Domain types ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ShockLayer:
    """One macro factor active in the current regime."""
    name_ar: str
    type: str                    # 'cyclical' | 'structural' | 'demographic'
    active_since: date
    evidence_ar: str
    captured_in_moj: str         # 'no' | 'partial' | 'yes'
    expected_duration_ar: Optional[str] = None


@dataclass(frozen=True)
class MarketRegime:
    """Snapshot of the current regime + its calibrated adjustments."""
    label_en: str
    label_ar: str
    active_since: date
    shock_layers: tuple[ShockLayer, ...]

    # Calibration constants — adjustments off the pre-war baseline (MoJ × 1.10).
    # Each is a multiplier applied to MoJ_median × plot_area.
    buyer_ceiling_multiplier_default: float    # for newer / unknown-age properties
    buyer_ceiling_multiplier_old: float        # for properties ≥ old_property_age_threshold
    opening_offer_multiplier_default: float
    opening_offer_multiplier_old: float
    old_property_age_threshold: int            # years

    moj_data_predates_regime: bool             # is MoJ snapshot from before this regime?
    moj_last_known_date: date                  # what we believe MoJ covers


@dataclass
class RegimeRecommendation:
    """Output of regime_recommendation()."""
    buyer_ceiling_qar: int
    opening_offer_qar: int
    negotiation_room_qar: int
    regime_label_ar: str
    is_old_property: bool
    adjustments_applied_ar: list[str] = field(default_factory=list)
    shock_layer_names_ar: list[str] = field(default_factory=list)
    moj_lag_warning_ar: Optional[str] = None


# ─── Current regime definition ───────────────────────────────────────────
#
# To switch back to a normal market (e.g. when MoJ resumes publishing post-war
# transactions and they reflect actual current prices), replace CURRENT_REGIME
# below with NORMAL_REGIME. Engine downstream will automatically zero out
# adjustments. No other code changes required.

_SHOCK_POST_WC = ShockLayer(
    name_ar='تصحيح ما بعد المونديال',
    type='cyclical',
    active_since=date(2023, 1, 1),
    evidence_ar=('Knight Frank / Mordor Intelligence: انخفاض القيم السكنية '
                 'في الدوحة 10% منذ 2022، تراجع الإيجارات الممتازة 20%'),
    captured_in_moj='partial',
)

_SHOCK_WAR_HORMUZ = ShockLayer(
    name_ar='الحرب الإقليمية وإغلاق هرمز',
    type='structural',
    active_since=date(2026, 2, 28),
    evidence_ar=('بدأت 28 فبراير 2026 بضربات أمريكية-إسرائيلية على إيران. '
                 'إيران ردّت بضربات صاروخية على قطر والإمارات والبحرين. '
                 'مضيق هرمز مغلق (شحن أقل من 5% من المستوى الطبيعي). '
                 'محطتا LNG في رأس لفان تضرّرتا (19 مارس 2026). '
                 'QatarEnergy: استعادة الطاقة الكاملة قد تصل 5 سنوات. '
                 'Oxford Economics: خفض نمو الخليج 4.6 نقطة لـ 2026'),
    captured_in_moj='no',
    expected_duration_ar='سنوات (تقدير QatarEnergy 5 سنوات لاستعادة LNG الكاملة)',
)

_SHOCK_POPULATION = ShockLayer(
    name_ar='نزوح سكاني',
    type='demographic',
    active_since=date(2026, 3, 1),
    evidence_ar=('هيئة التخطيط والإحصاء: 3,406,760 (فبراير) → '
                 '3,370,611 (مارس) = انخفاض 36,149 نسمة في شهر واحد. '
                 'قطر 88% وافدون، حسّاسة لقلق الأمان'),
    captured_in_moj='no',
)

_SHOCK_VOLUME_COLLAPSE = ShockLayer(
    name_ar='انهيار حجم المعاملات',
    type='cyclical',
    active_since=date(2026, 3, 1),
    evidence_ar=('Aqarat / AGBI: 154 صفقة سكنية في مارس 2026 لعموم البلاد '
                 '(عقار واحد بيع في الدوحة في مارس). Q1 2026: 675 وحدة فقط'),
    captured_in_moj='no',
)


CURRENT_REGIME = MarketRegime(
    label_en='post_disruption_recession',
    label_ar='ركود ما بعد الاضطراب الإقليمي',
    active_since=date(2026, 2, 28),
    shock_layers=(_SHOCK_POST_WC, _SHOCK_WAR_HORMUZ,
                  _SHOCK_POPULATION, _SHOCK_VOLUME_COLLAPSE),
    # Calibration from doc-header derivation:
    buyer_ceiling_multiplier_default=1.00,    # was MoJ × 1.10 pre-war
    buyer_ceiling_multiplier_old=0.95,        # additional 5pp drop for ≥10yr
    opening_offer_multiplier_default=0.90,
    opening_offer_multiplier_old=0.85,
    old_property_age_threshold=10,            # Section 10-Year Rule alignment
    moj_data_predates_regime=True,
    moj_last_known_date=date(2025, 12, 31),
)


# Reserved for future: when MoJ resumes + post-war data starts arriving.
NORMAL_REGIME = MarketRegime(
    label_en='normal',
    label_ar='سوق طبيعي',
    active_since=date(2025, 1, 1),
    shock_layers=(),
    buyer_ceiling_multiplier_default=1.10,    # Section 4 pre-war hard ceiling
    buyer_ceiling_multiplier_old=1.00,
    opening_offer_multiplier_default=0.95,
    opening_offer_multiplier_old=0.90,
    old_property_age_threshold=10,
    moj_data_predates_regime=False,
    moj_last_known_date=date(2026, 1, 1),     # placeholder
)


# Active regime — change this single binding to switch market regimes.
current_regime = CURRENT_REGIME


# ─── Core recommendation function ────────────────────────────────────────

def regime_recommendation(
    moj_median_per_m2: float,
    plot_area_m2: float,
    building_age_years: Optional[float] = None,
    regime: MarketRegime = current_regime,
) -> RegimeRecommendation:
    """Compute regime-adjusted buyer recommendations.

    Args:
        moj_median_per_m2: Engine's MoJ-derived per-m² median for this
            address/bracket. None or 0 means insufficient data — caller
            should not invoke this function in that case.
        plot_area_m2: Plot area in square meters (PDAREA from CadastrePlots).
        building_age_years: Optional. If provided and ≥ regime threshold,
            applies the older-property adjustment. Pass None for raw land.
        regime: Defaults to the currently active regime. Tests can pass
            NORMAL_REGIME or a custom MarketRegime.

    Returns:
        RegimeRecommendation with buyer_ceiling_qar, opening_offer_qar,
        and transparent adjustment breakdown.
    """
    if moj_median_per_m2 is None or moj_median_per_m2 <= 0:
        raise ValueError(
            'moj_median_per_m2 must be positive — '
            'do not call regime_recommendation when MoJ data is insufficient'
        )
    if plot_area_m2 is None or plot_area_m2 <= 0:
        raise ValueError('plot_area_m2 must be positive')

    base_total = moj_median_per_m2 * plot_area_m2

    is_old = (
        building_age_years is not None
        and building_age_years >= regime.old_property_age_threshold
    )
    if is_old:
        ceiling_mult = regime.buyer_ceiling_multiplier_old
        opening_mult = regime.opening_offer_multiplier_old
    else:
        ceiling_mult = regime.buyer_ceiling_multiplier_default
        opening_mult = regime.opening_offer_multiplier_default

    ceiling = int(round(base_total * ceiling_mult, -3))   # round to nearest 1,000
    opening = int(round(base_total * opening_mult, -3))
    room = ceiling - opening

    # Build human-readable adjustments list
    adjustments = []
    if regime.label_en == 'normal':
        adjustments.append(
            f'الوضع: سوق طبيعي. السقف = وسيط وزارة العدل × {ceiling_mult:.2f}'
        )
    else:
        # Base regime drop = the drop applied even to NEW properties
        regime_pp_drop = (
            NORMAL_REGIME.buyer_ceiling_multiplier_default
            - regime.buyer_ceiling_multiplier_default
        ) * 100
        adjustments.append(
            f'تطبيق وضع "{regime.label_ar}": تخفيض السقف '
            f'بـ {regime_pp_drop:.0f} نقطة مئوية من قاعدة ما قبل الحرب '
            f'(MoJ × {NORMAL_REGIME.buyer_ceiling_multiplier_default:.2f} → '
            f'MoJ × {regime.buyer_ceiling_multiplier_default:.2f})'
        )
    if is_old:
        old_extra_pp = (
            regime.buyer_ceiling_multiplier_default
            - regime.buyer_ceiling_multiplier_old
        ) * 100
        adjustments.append(
            f'عمر المبنى {int(building_age_years)} سنة '
            f'(≥{regime.old_property_age_threshold}): '
            f'تخفيض إضافي {old_extra_pp:.0f} نقطة مئوية '
            f'(MoJ × {regime.buyer_ceiling_multiplier_default:.2f} → '
            f'MoJ × {regime.buyer_ceiling_multiplier_old:.2f}). '
            f'السوق الراكد يضغط على الأصول القديمة أكثر'
        )
    elif building_age_years is None:
        adjustments.append(
            'عمر المبنى غير محدد — تطبيق السقف الافتراضي. '
            f'لو ≥{regime.old_property_age_threshold} سنة فالسقف الفعلي أقل'
        )

    # MoJ lag warning
    # Sprint 2.22.0a.2 C1 defensive companion: the lag-warning prose is
    # surfaced through RegimeRecommendation.moj_lag_warning_ar (currently
    # not rendered through the live API path but defensively neutralized
    # for the same reason as the muc_clause: never name specific political
    # events in user-visible copy). Calibration math (buyer ceiling × 1.00
    # etc.) is unchanged — only the prose explaining the lag is reframed.
    lag_warning = None
    if regime.moj_data_predates_regime:
        lag_days = (regime.active_since - regime.moj_last_known_date).days
        lag_warning = (
            f'⚠️ آخر معاملة في وزارة العدل: '
            f'{regime.moj_last_known_date.isoformat()}. '
            f'مرّ على هذا التاريخ {lag_days} يوماً. '
            f'البيانات الأساسية لا تعكس تطوّرات السوق منذ آخر تحديث منشور.'
        )

    return RegimeRecommendation(
        buyer_ceiling_qar=ceiling,
        opening_offer_qar=opening,
        negotiation_room_qar=room,
        regime_label_ar=regime.label_ar,
        is_old_property=is_old,
        adjustments_applied_ar=adjustments,
        shock_layer_names_ar=[s.name_ar for s in regime.shock_layers],
        moj_lag_warning_ar=lag_warning,
    )


# ─── Serialization helper for API responses ─────────────────────────────

def regime_to_dict(regime: MarketRegime = current_regime) -> dict:
    """Serialize the regime metadata for inclusion in /api/evaluate responses.

    The engine should embed this under response['market_regime'] alongside
    the recommendation block. Frontend renders both.
    """
    return {
        'label_en': regime.label_en,
        'label_ar': regime.label_ar,
        'active_since': regime.active_since.isoformat(),
        'moj_data_predates_regime': regime.moj_data_predates_regime,
        'moj_last_known_date': regime.moj_last_known_date.isoformat(),
        'shock_layers': [
            {
                'name_ar': s.name_ar,
                'type': s.type,
                'active_since': s.active_since.isoformat(),
                'evidence_ar': s.evidence_ar,
                'captured_in_moj': s.captured_in_moj,
                'expected_duration_ar': s.expected_duration_ar,
            }
            for s in regime.shock_layers
        ],
        'calibration': {
            'buyer_ceiling_multiplier_default':
                regime.buyer_ceiling_multiplier_default,
            'buyer_ceiling_multiplier_old':
                regime.buyer_ceiling_multiplier_old,
            'opening_offer_multiplier_default':
                regime.opening_offer_multiplier_default,
            'opening_offer_multiplier_old':
                regime.opening_offer_multiplier_old,
            'old_property_age_threshold':
                regime.old_property_age_threshold,
        },
    }


def recommendation_to_dict(rec: RegimeRecommendation) -> dict:
    """Serialize a recommendation block for inclusion in API responses."""
    return {
        'buyer_ceiling_qar': rec.buyer_ceiling_qar,
        'opening_offer_qar': rec.opening_offer_qar,
        'negotiation_room_qar': rec.negotiation_room_qar,
        'regime_label_ar': rec.regime_label_ar,
        'is_old_property': rec.is_old_property,
        'adjustments_applied_ar': rec.adjustments_applied_ar,
        'shock_layer_names_ar': rec.shock_layer_names_ar,
        'moj_lag_warning_ar': rec.moj_lag_warning_ar,
    }


# ─── Quick self-test (run as: python market_regime.py) ──────────────────

if __name__ == '__main__':
    # Three scenarios spanning the meaningful cases
    scenarios = [
        ('New villa (5y) — Al-Luqta-like',
         {'moj_median_per_m2': 3875, 'plot_area_m2': 600, 'building_age_years': 5}),
        ('Old villa (15y) — same area',
         {'moj_median_per_m2': 3875, 'plot_area_m2': 600, 'building_age_years': 15}),
        ('Raw land (no building)',
         {'moj_median_per_m2': 3500, 'plot_area_m2': 800, 'building_age_years': None}),
    ]
    print(f'Current regime: {current_regime.label_ar}')
    print(f'Active since: {current_regime.active_since}')
    print(f'Shock layers: {len(current_regime.shock_layers)}')
    print('=' * 78)
    for label, kwargs in scenarios:
        rec = regime_recommendation(**kwargs)
        print(f'\n— {label} —')
        print(f'   inputs: {kwargs}')
        print(f'   buyer_ceiling: {rec.buyer_ceiling_qar:,} QAR')
        print(f'   opening_offer: {rec.opening_offer_qar:,} QAR')
        print(f'   negotiation_room: {rec.negotiation_room_qar:,} QAR')
        print(f'   is_old: {rec.is_old_property}')
        for adj in rec.adjustments_applied_ar:
            print(f'   • {adj}')
