"""Tests for Thammen v2 new modules."""

import pytest
from service_charge_db import lookup, ServiceChargeRecord, describe_ar
from market_position import compute_position, MarketPosition
from reasoning_trace import (
    ReasoningTrace, ReasoningStep, SourceCitation, add_standard_unknowns,
)


class TestServiceChargeDB:
    """قاعدة بيانات رسوم الخدمات."""

    def test_pearl_porto_arabia_verified(self):
        """اللؤلؤة Porto Arabia يجب أن يكون verified بـ 15 ر.ق/م²/شهر."""
        rec = lookup(area='اللؤلؤة', precinct='Porto Arabia', asset_type='apartment')
        assert rec.confidence == 'verified'
        assert rec.monthly_per_m2 == 15.0
        assert rec.annual_per_m2 == 180.0
        assert 'FGRealty' in rec.source

    def test_pearl_qanat_quartier(self):
        rec = lookup(area='اللؤلؤة', precinct='Qanat Quartier', asset_type='apartment')
        assert rec.confidence == 'verified'
        assert rec.monthly_per_m2 == 14.0

    def test_lusail_fox_hills(self):
        rec = lookup(area='لوسيل', precinct='Fox Hills', asset_type='apartment')
        assert rec.confidence == 'verified'
        assert rec.monthly_per_m2 == 10.0

    def test_pearl_unknown_precinct_falls_back_to_area_avg(self):
        rec = lookup(area='اللؤلؤة', precinct='Unknown Precinct', asset_type='apartment')
        # falls back to Pearl area average
        assert rec.area == 'اللؤلؤة'
        assert rec.precinct is None
        assert rec.confidence == 'reported'

    def test_unknown_area_returns_estimated_range(self):
        rec = lookup(area='منطقة غير معروفة', asset_type='apartment')
        # falls back to global apartment fallback
        assert rec.confidence == 'estimated'
        assert rec.monthly_per_m2_range is not None

    def test_villa_standalone_zero_charges(self):
        rec = lookup(asset_type='villa_standalone')
        assert rec.monthly_per_m2 == 0.0

    def test_annual_total_calculation(self):
        rec = lookup(area='اللؤلؤة', precinct='Porto Arabia', asset_type='apartment')
        # 145 m² × 15 QAR/m²/month × 12 = 26,100
        assert rec.annual_total(145) == 26_100

    def test_describe_ar_mentions_source(self):
        rec = lookup(area='اللؤلؤة', precinct='Porto Arabia', asset_type='apartment')
        desc = describe_ar(rec)
        assert 'ر.ق' in desc
        assert 'verified' in desc
        assert 'FGRealty' in desc


class TestMarketPosition:
    """موضع السعر — يجب ألا يحتوي توصيات شرائية."""

    def test_at_market_within_normal_band(self):
        pos = compute_position(
            listing_price=1_000_000,
            benchmark_price=1_000_000,
            benchmark_source='test',
        )
        assert pos.position_label == 'at_market'
        assert pos.gap_pct == 0.0

    def test_above_market_classification(self):
        pos = compute_position(
            listing_price=1_200_000,
            benchmark_price=1_000_000,
            benchmark_source='test',
        )
        assert pos.position_label == 'above_market'
        assert pos.gap_pct == 20.0

    def test_far_above_market_at_50pct(self):
        pos = compute_position(
            listing_price=1_500_000,
            benchmark_price=1_000_000,
            benchmark_source='test',
        )
        assert pos.position_label == 'far_above_market'

    def test_far_below_market_triggers_caution_note(self):
        pos = compute_position(
            listing_price=600_000,
            benchmark_price=1_000_000,
            benchmark_source='test',
        )
        assert pos.position_label == 'far_below_market'
        # يجب أن يحتوي وصف عن أسباب الفرق الكبير
        assert 'تنازل' in pos.description_ar or 'مشاكل قانونية' in pos.description_ar

    def test_no_buy_sell_words_in_description(self):
        """لا توجد كلمات أمر شرائية في الوصف."""
        for listing in [800_000, 1_000_000, 1_200_000, 1_500_000]:
            pos = compute_position(
                listing_price=listing,
                benchmark_price=1_000_000,
                benchmark_source='test',
            )
            forbidden = ['اشترِ', 'لا تشترِ', 'BUY', 'SELL', 'BARGAIN', 'REJECT', 'لقطة فعلية', 'مرفوض']
            for word in forbidden:
                assert word not in pos.description_ar, \
                    f'Forbidden word "{word}" found in: {pos.description_ar}'

    def test_no_benchmark_returns_no_benchmark_label(self):
        pos = compute_position(listing_price=1_000_000)
        assert pos.position_label == 'no_benchmark'

    def test_caveats_propagate(self):
        pos = compute_position(
            listing_price=600_000,
            benchmark_price=1_000_000,
            benchmark_source='test',
            listing_caveats=['تنازل', 'أقساط متبقية'],
        )
        assert 'تنازل' in pos.caveats
        assert 'أقساط متبقية' in pos.caveats


class TestReasoningTrace:
    """سلسلة المنطق — يجب أن يكون كل شيء له مصدر."""

    def test_empty_trace_has_disclaimer(self):
        trace = ReasoningTrace()
        d = trace.to_dict()
        assert d['disclaimer']
        assert 'RICS' in d['disclaimer']  # mentions it's NOT RICS
        assert 'وزارة العدل' in d['disclaimer']

    def test_step_chaining(self):
        trace = (ReasoningTrace()
                 .add('step1', 'fact1', 'src1', '2026-05')
                 .add('step2', 'fact2', 'src2', '2026-05'))
        assert len(trace.steps) == 2
        assert trace.steps[0].step_number == 1
        assert trace.steps[1].step_number == 2

    def test_data_freshness_tracks_latest(self):
        trace = ReasoningTrace()
        trace.add('a', 'f1', 'src1', '2026-05-01')
        trace.add('b', 'f2', 'src1', '2026-05-08')  # newer
        trace.add('c', 'f3', 'src1', '2026-05-03')  # older — should not overwrite
        assert trace.data_freshness['src1'] == '2026-05-08'

    def test_unique_sources_no_duplicates(self):
        trace = ReasoningTrace()
        trace.add_source('data.gov.qa', record_count=100)
        trace.add_source('data.gov.qa', record_count=200)  # dedupe
        assert len(trace.sources_consulted) == 1

    def test_known_unknowns_tracked(self):
        trace = ReasoningTrace()
        trace.add_unknown('حالة العقار')
        trace.add_unknown('حالة العقار')  # dedupe
        trace.add_unknown('الإطلالة')
        assert len(trace.known_unknowns) == 2

    def test_standard_unknowns_for_apartment(self):
        trace = ReasoningTrace()
        add_standard_unknowns(trace, asset_type='apartment')
        assert len(trace.known_unknowns) >= 4
        # apartment-specific should include floor/view
        assert any('طابق' in u or 'إطلال' in u for u in trace.known_unknowns)

    def test_human_readable_includes_disclaimer(self):
        trace = ReasoningTrace()
        trace.add('test', 'fact', 'src')
        text = trace.to_human_readable_ar()
        assert 'إخلاء مسؤولية' in text
        assert 'RICS' in text

    def test_to_dict_serializable(self):
        """يجب أن يكون قابلاً للتسلسل JSON."""
        import json
        trace = ReasoningTrace(valuation_id='TEST-001')
        trace.add('id', 'fact', 'src', '2026-05')
        trace.add_source('test_src')
        trace.add_unknown('unknown_thing')

        # يجب ألا يفشل
        json_str = json.dumps(trace.to_dict(), ensure_ascii=False)
        assert 'TEST-001' in json_str
