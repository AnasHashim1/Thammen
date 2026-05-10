"""Tests for evaluate_property.py — Sprint 2."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluate_property import (
    analyze_listing_description,
    BuaBreakdown, compute_replacement_cost,
    blend_valuations, MoJValuation,
    compute_confidence, compute_rental_analysis,
    PropertyEvaluation, ReplacementCostValuation,
    COMPONENT_COST_MULTIPLIERS,
)


class TestRedFlagExclusion:
    """Red flags must be detected and trigger exclusion."""

    def test_tanazul_excluded(self):
        flags = analyze_listing_description('فيلا للبيع تنازل عن المالك')
        assert flags.has_excluding_red_flag is True

    def test_installments_excluded(self):
        flags = analyze_listing_description('أقساط متبقية على العقار')
        assert flags.has_excluding_red_flag is True

    def test_demolition_excluded(self):
        flags = analyze_listing_description('بيت قديم للهدم')
        assert flags.has_excluding_red_flag is True

    def test_clean_description_passes(self):
        flags = analyze_listing_description('فيلا حديثة البناء مع مسبح ومجلس')
        assert flags.has_excluding_red_flag is False


class TestGreenFlagDetection:
    """Green flags must be detected correctly."""

    def test_owner_direct(self):
        flags = analyze_listing_description('للبيع مباشر من المالك')
        found = [g['label'] for g in flags.green_flags]
        assert any('مباشر' in l for l in found)

    def test_new_build(self):
        flags = analyze_listing_description('فيلا حديث البناء لم تسكن')
        assert len(flags.green_flags) >= 1

    def test_corner_plot(self):
        flags = analyze_listing_description('فيلا على شارعين زاوية')
        found = [g['label'] for g in flags.green_flags]
        assert any('شارعين' in l or 'زاوية' in l for l in found)


class TestBuaBreakdownCosting:
    """Component-level costing must use correct multipliers."""

    def test_basement_costs_more(self):
        bd = BuaBreakdown(
            main_footprint_m2=300,
            basement_m2=300,
            upper_floors_m2=0, upper_floor_count=0,
            annexes_m2=0, annex_count=0, external_m2=0,
        )
        rc = compute_replacement_cost(
            plot_area_m2=500, moj_land_median_per_m2=4000,
            bua_breakdown=bd, construction_tier='mid',
        )
        # Find basement and ground costs
        costs = {c['component']: c for c in rc.component_costs}
        basement_per_m2 = costs['سرداب (basement)']['cost_per_m2']
        ground_per_m2 = costs['أرضي (ground)']['cost_per_m2']
        assert basement_per_m2 > ground_per_m2, \
            "Basement must cost more than ground floor"
        assert basement_per_m2 == round(3000 * COMPONENT_COST_MULTIPLIERS['basement'])

    def test_annexes_cost_less(self):
        bd = BuaBreakdown(
            main_footprint_m2=300,
            basement_m2=0,
            upper_floors_m2=0, upper_floor_count=0,
            annexes_m2=150, annex_count=3,
            external_m2=0,
        )
        rc = compute_replacement_cost(
            plot_area_m2=500, moj_land_median_per_m2=4000,
            bua_breakdown=bd, construction_tier='mid',
        )
        costs = {c['component']: c for c in rc.component_costs}
        annex_per_m2 = [c for k, c in costs.items() if 'ملاحق' in k][0]['cost_per_m2']
        ground_per_m2 = costs['أرضي (ground)']['cost_per_m2']
        assert annex_per_m2 < ground_per_m2, \
            "Annexes (single-story, simple) must cost less than ground floor"

    def test_total_bua_correct(self):
        bd = BuaBreakdown(
            main_footprint_m2=350, basement_m2=350,
            upper_floors_m2=300, upper_floor_count=1,
            annexes_m2=150, annex_count=3,
            external_m2=60,
        )
        assert bd.total_bua == 1210


class TestBlendingWeights:
    """Blending MoJ + replacement cost must use correct weights."""

    def test_high_bua_weak_n(self):
        """BUA ratio > 1.0 + n < 10 → 80% replacement."""
        moj = MoJValuation(
            strategy='test', moj_category='villa', size_bracket='900-1500', bracket_n=4, bracket_reliable=False,
            moj_median_total=5000000, moj_median_per_m2=5000,
            estimated_value_low=4000000, estimated_value_median=5000000, estimated_value_high=5500000,
        )
        rc = ReplacementCostValuation(
            land_value=4000000, land_price_per_m2=4000,
            bua_m2=1200, bua_breakdown=None, bua_plot_ratio=1.25,
            component_costs=None, construction_cost_new=3600000,
            building_age_years=25, depreciation_pct=0.5,
            renovation_recovery_pct=0.12, depreciated_building_value=2200000,
            total_replacement_value=6200000,
        )
        blended = blend_valuations(moj, rc, bua_plot_ratio=1.25, bracket_n=4)
        assert blended.replacement_weight == 0.80
        assert blended.moj_weight == 0.20

    def test_normal_bua_strong_n(self):
        """BUA ratio < 1.0 + n ≥ 10 → 80% MoJ."""
        moj = MoJValuation(
            strategy='test', moj_category='villa', size_bracket='400-600', bracket_n=25, bracket_reliable=True,
            moj_median_total=2500000, moj_median_per_m2=5000,
            estimated_value_low=None, estimated_value_median=None, estimated_value_high=None,
        )
        rc = ReplacementCostValuation(
            land_value=2000000, land_price_per_m2=4000,
            bua_m2=300, bua_breakdown=None, bua_plot_ratio=0.6,
            component_costs=None, construction_cost_new=900000,
            building_age_years=10, depreciation_pct=0.2,
            renovation_recovery_pct=0, depreciated_building_value=720000,
            total_replacement_value=2720000,
        )
        blended = blend_valuations(moj, rc, bua_plot_ratio=0.6, bracket_n=25)
        assert blended.moj_weight == 0.80
        assert blended.replacement_weight == 0.20


class TestReplacementCostDepreciation:
    """Depreciation and renovation recovery must compute correctly."""

    def test_25yr_partial_renovation(self):
        rc = compute_replacement_cost(
            plot_area_m2=1000, moj_land_median_per_m2=4000,
            bua_m2=800, building_age_years=25,
            has_renovation=True, construction_tier='mid',
        )
        # New curve: 25yr = 0.15 + (25-10)*0.02 + extra = 0.35 + 0.15 = 0.50
        # Recovery: 15% (updated from 12%)
        # Net: 50% - 15% = 35%
        assert rc.depreciation_pct == 0.5
        assert rc.renovation_recovery_pct == 0.15
        building_new = 800 * 3000
        expected_depr = round(building_new * (1 - 0.35))
        assert rc.depreciated_building_value == expected_depr

    def test_depreciation_caps_at_80(self):
        rc = compute_replacement_cost(
            plot_area_m2=500, moj_land_median_per_m2=4000,
            bua_m2=400, building_age_years=50,
            construction_tier='mid',
        )
        # 50yr with accelerating curve → capped at 80%
        assert rc.depreciation_pct == 0.8


class TestConfidenceScore:
    """Confidence score must reflect data quality accurately."""

    def test_full_data_high_confidence(self):
        """All data available + strong sample → score ≥ 75."""
        e = PropertyEvaluation(
            address='test', asset_type='standalone_villa',
            classification_confidence='high', plot_area_m2=500,
            extent_total_m2=500,
        )
        e.valuation = MoJValuation(
            strategy='test', moj_category='villa', size_bracket='400-600', bracket_n=25, bracket_reliable=True,
            moj_median_total=3000000, moj_median_per_m2=6000,
            estimated_value_low=2500000, estimated_value_median=3000000, estimated_value_high=3500000,
            factors_adjustment=0.03, fair_price_total=3090000,
        )
        e.replacement_cost = ReplacementCostValuation(
            land_value=2000000, land_price_per_m2=4000,
            bua_m2=600, bua_breakdown=BuaBreakdown(main_footprint_m2=300, basement_m2=300),
            bua_plot_ratio=1.2, component_costs=[],
            construction_cost_new=1800000, building_age_years=10,
            depreciation_pct=0.2, renovation_recovery_pct=0,
            depreciated_building_value=1440000, total_replacement_value=3440000,
        )
        e.trend = {'years': [{'year': '2022'}, {'year': '2023'}, {'year': '2024'}]}
        e.listing_flags = True  # truthy
        e.listing_comparison = True  # truthy

        score, label, breakdown = compute_confidence(e)
        assert score >= 75, f"Full data should give ≥75, got {score}"
        assert '🟢' in label or '🟡' in label

    def test_minimal_data_low_confidence(self):
        """n=3, no BUA, no factors → score < 30."""
        e = PropertyEvaluation(
            address='test', asset_type='standalone_villa',
            classification_confidence='high', plot_area_m2=500,
            extent_total_m2=500,
        )
        e.valuation = MoJValuation(
            strategy='test', moj_category='villa', size_bracket='400-600', bracket_n=3, bracket_reliable=False,
            moj_median_total=3000000, moj_median_per_m2=6000,
            estimated_value_low=None, estimated_value_median=None, estimated_value_high=None,
        )
        score, label, breakdown = compute_confidence(e)
        assert score < 30, f"Minimal data should give <30, got {score}"
        assert '🔴' in label


class TestRentalAnalysis:
    """Rental yield calculations must be mathematically correct.

    v2 changes:
      - Tests pass opex_ratio explicitly to maintain old flat-cost behavior
        (since v2 uses itemized costs by default which give different numbers).
      - test_verdict_categories now checks position descriptions, not verdicts.
    """

    def test_basic_yield(self):
        # v2: pass opex_ratio explicitly to keep the legacy 23% behavior for this test
        result = compute_rental_analysis(
            rental_income_monthly=7500,
            property_value=5000000,
            opex_ratio=0.23,  # legacy mode
        )
        # Gross: 7500×12/5000000 = 1.8%
        assert result['on_valuation']['gross_yield_pct'] == 1.8
        # Net: 7500×12×0.77/5000000 = 1.386%
        assert abs(result['on_valuation']['net_yield_pct'] - 1.39) < 0.05

    def test_listing_vs_valuation_yield(self):
        result = compute_rental_analysis(
            rental_income_monthly=10000,
            property_value=4000000,
            listing_price=5000000,
            opex_ratio=0.23,
        )
        # Yield on valuation should be higher than on listing price
        val_yield = result['on_valuation']['net_yield_pct']
        list_yield = result['on_listing_price']['net_yield_pct']
        assert val_yield > list_yield, \
            "Yield on lower valuation must be higher than on higher listing"

    def test_yield_position_categories(self):
        """v2: descriptive position labels (not decisional verdicts)."""
        # Above market: net > 6%
        r = compute_rental_analysis(15000, 2000000, opex_ratio=0.23)
        # 15000*12*0.77 / 2_000_000 = 6.93% net
        assert r['yield_position'] == 'above_market'
        assert 'فوق متوسط السوق' in r['yield_position_ar']

        # At market lower: net 4-5%
        r = compute_rental_analysis(10000, 2200000, opex_ratio=0.23)
        # 10000*12*0.77 / 2_200_000 = 4.20%
        assert r['yield_position'] == 'at_market_lower'

        # Far below market: net < 2%
        r = compute_rental_analysis(3000, 5000000, opex_ratio=0.23)
        # 3000*12*0.77 / 5_000_000 = 0.55%
        assert r['yield_position'] == 'far_below_market'

    def test_potential_rental(self):
        result = compute_rental_analysis(
            rental_income_monthly=7500,
            property_value=5000000,
            potential_monthly=14500,
            opex_ratio=0.23,
        )
        assert 'potential' in result
        assert result['potential']['monthly'] == 14500
        assert result['potential']['net_yield_pct'] > result['on_valuation']['net_yield_pct']

    def test_v2_itemized_costs(self):
        """v2: when bua_m2 + area provided, use service_charge_db, not flat opex."""
        result = compute_rental_analysis(
            rental_income_monthly=11000,
            property_value=1_891_670,
            bua_m2=145,
            area='اللؤلؤة',
            precinct='Porto Arabia',
            asset_type='apartment',
        )
        # Should have detailed cost breakdown, not flat opex
        assert 'cost_breakdown' in result
        cb = result['cost_breakdown']
        # Service charge should be ~26,100 (15 QAR/m²/month × 145m² × 12)
        assert 25_000 <= cb['service_charge_annual'] <= 27_000
        assert cb['service_charge_confidence'] == 'verified'
        # FGRealty source should be cited
        assert 'FGRealty' in cb['service_charge_source']

    def test_v2_disclaimer_present(self):
        """v2: every rental analysis carries the descriptive position."""
        r = compute_rental_analysis(10000, 2000000, opex_ratio=0.23)
        assert 'yield_position' in r
        assert 'yield_position_ar' in r
        # No buy/sell verdict words in v2
        assert 'اشترِ' not in r['yield_position_ar']
        assert 'لا تشترِ' not in r['yield_position_ar']
