"""
test_sprint_2p22p0a2_c1_geopolitical_neutralization.py — Sprint 2.22.0a.2 C1.

Validates that geopolitical narration (الحرب الإقليمية / هرمز /
نزوح سكاني / انهيار حجم المعاملات) no longer appears in user-visible
MUC clause output, while:
  - the RICS/IVS regulatory framing is preserved (VPGA 10 + VPS 6 +
    IVS 106 citation kept intact);
  - the neutral cause-of-uncertainty paragraph is rendered (VPGA 10 §6
    requirement to identify the cause);
  - the ShockLayer data model in market_regime.py is UNTOUCHED (internal
    audit trail of calibration choices preserved);
  - the calibration math (buyer ceiling multipliers etc.) is UNCHANGED.

Standalone test, no pytest dependency.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))


# Each forbidden substring is something that MUST NOT appear in
# user-rendered MUC clause text after C1 neutralization.
FORBIDDEN_AR = [
    'الحرب الإقليمية',
    'إغلاق هرمز',
    'نزوح سكاني',
    'انهيار حجم المعاملات',
    'تصحيح ما بعد المونديال',
    'صدمات الحرب',
]
FORBIDDEN_EN = [
    'regional war',
    'Hormuz Strait closure',
    'population outflow',
    'transaction-volume collapse',
    'post-World-Cup correction',
]


def test_muc_clause_ar_carries_neutral_cause_paragraph():
    """muc_clause_ar must include the neutral VPGA 10 §6 cause-of-
    uncertainty paragraph (data freshness + sparse recent transactions)."""
    from material_uncertainty import regime_muc
    out = regime_muc()
    clause = out.get('muc_clause_ar') or ''
    assert clause, 'regime_muc must produce muc_clause_ar for non-normal regime'

    # The neutral cause-of-uncertainty paragraph (per VPGA 10 §6)
    expected_neutral = (
        'قيوداً جوهرية على شواهد السوق المتاحة، '
        'في ظل فجوة طويلة في تحديث بيانات وزارة العدل'
    )
    assert expected_neutral in clause, (
        f"C1: neutral VPGA 10 cause-of-uncertainty paragraph not found "
        f"in muc_clause_ar. Got: {clause[:400]!r}..."
    )
    print('  PASS test_muc_clause_ar_carries_neutral_cause_paragraph')


def test_muc_clause_ar_no_geopolitical_strings():
    """No forbidden geopolitical Arabic strings in muc_clause_ar."""
    from material_uncertainty import regime_muc
    out = regime_muc()
    clause = out.get('muc_clause_ar') or ''
    for forbidden in FORBIDDEN_AR:
        assert forbidden not in clause, (
            f"C1 regression: forbidden Arabic string {forbidden!r} "
            f"still appears in muc_clause_ar. Context: ..."
            f"{clause[max(0, clause.find(forbidden)-30):clause.find(forbidden)+len(forbidden)+30]}..."
        )
    print('  PASS test_muc_clause_ar_no_geopolitical_strings')


def test_muc_clause_en_no_geopolitical_strings():
    """No forbidden geopolitical English strings in muc_clause_en."""
    from material_uncertainty import regime_muc
    out = regime_muc()
    clause = out.get('muc_clause_en') or ''
    assert clause, 'regime_muc must produce muc_clause_en'
    for forbidden in FORBIDDEN_EN:
        assert forbidden not in clause, (
            f"C1 regression: forbidden English string {forbidden!r} "
            f"still appears in muc_clause_en."
        )
    # Positive check: the neutral English paragraph is present
    expected_en_neutral = (
        'material constraints on available market evidence, '
        'given an extended gap in the publication of Ministry of Justice '
        'transaction data and a low volume of recently published transactions'
    )
    assert expected_en_neutral in clause, (
        f"C1: neutral English VPGA 10 cause paragraph not found "
        f"in muc_clause_en. Got: {clause[:400]!r}..."
    )
    print('  PASS test_muc_clause_en_no_geopolitical_strings')


def test_rics_ivs_citation_preserved():
    """The RICS Red Book + IVS citation header is preserved exactly
    (with LRM-wrapping from Pattern A). C1 must not regress Pattern A."""
    LRM = '‎'
    from material_uncertainty import regime_muc
    out = regime_muc()
    ar = out.get('muc_clause_ar') or ''
    en = out.get('muc_clause_en') or ''
    # Pattern A LRM-wrapped tokens still present in Arabic
    for token in ('RICS Red Book Global Standards', 'VPGA 10', 'VPS 6',
                  'IVS 106'):
        wrapped = f'{LRM}{token}{LRM}'
        assert wrapped in ar, (
            f"C1 regression: Pattern A LRM-wrapped {token!r} no longer "
            f"in muc_clause_ar"
        )
    # English citation unchanged
    assert 'RICS Red Book Global Standards' in en
    assert 'VPGA 10 (Material Valuation Uncertainty)' in en
    assert 'IVS 106 (Documentation and Reporting)' in en
    print('  PASS test_rics_ivs_citation_preserved')


def test_market_regime_data_model_untouched():
    """ShockLayer instances + their name_ar fields in market_regime.py
    are PRESERVED per KICKOFF directive (internal audit trail of why
    calibration multipliers drop). The data model stays; only the
    rendering layer changes."""
    from market_regime import (
        CURRENT_REGIME, _SHOCK_WAR_HORMUZ, _SHOCK_POPULATION,
        _SHOCK_VOLUME_COLLAPSE, _SHOCK_POST_WC,
    )
    assert _SHOCK_WAR_HORMUZ.name_ar == 'الحرب الإقليمية وإغلاق هرمز'
    assert _SHOCK_POPULATION.name_ar == 'نزوح سكاني'
    assert _SHOCK_VOLUME_COLLAPSE.name_ar == 'انهيار حجم المعاملات'
    assert _SHOCK_POST_WC.name_ar == 'تصحيح ما بعد المونديال'
    assert len(CURRENT_REGIME.shock_layers) == 4
    print('  PASS test_market_regime_data_model_untouched')


def test_calibration_math_unchanged():
    """Buyer ceiling + opening offer multipliers in CURRENT_REGIME are
    UNCHANGED. C1 reframes the prose only — the calibration constants
    that drive the buyer-side recommendations stay exactly as they were."""
    from market_regime import CURRENT_REGIME
    assert CURRENT_REGIME.buyer_ceiling_multiplier_default == 1.00
    assert CURRENT_REGIME.buyer_ceiling_multiplier_old == 0.95
    assert CURRENT_REGIME.opening_offer_multiplier_default == 0.90
    assert CURRENT_REGIME.opening_offer_multiplier_old == 0.85
    print('  PASS test_calibration_math_unchanged')


def test_market_regime_lag_warning_neutralized():
    """The defensive companion site at market_regime.py:lag_warning
    no longer names 'الحرب' / 'هرمز' / 'النزوح السكاني'. Neutral
    prose about data-freshness gap is used instead."""
    from market_regime import regime_recommendation
    rec = regime_recommendation(
        moj_median_per_m2=3000, plot_area_m2=600, building_age_years=5
    )
    lag = rec.moj_lag_warning_ar or ''
    assert lag, 'lag_warning should fire for non-normal regime'
    for forbidden in ('الحرب', 'هرمز', 'النزوح السكاني', 'صدمات'):
        assert forbidden not in lag, (
            f"C1 defensive companion regression: forbidden {forbidden!r} "
            f"still in market_regime lag_warning. Got: {lag!r}"
        )
    # Positive check: the neutral phrase is present
    assert 'تطوّرات السوق منذ آخر تحديث منشور' in lag, (
        f"Neutral lag-warning prose missing. Got: {lag!r}"
    )
    print('  PASS test_market_regime_lag_warning_neutralized')


def main():
    tests = [
        test_muc_clause_ar_carries_neutral_cause_paragraph,
        test_muc_clause_ar_no_geopolitical_strings,
        test_muc_clause_en_no_geopolitical_strings,
        test_rics_ivs_citation_preserved,
        test_market_regime_data_model_untouched,
        test_calibration_math_unchanged,
        test_market_regime_lag_warning_neutralized,
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
    print(f'Sprint 2.22.0a.2 C1 (geopolitical neutralization): '
          f'{len(tests) - failed}/{len(tests)} passed')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
