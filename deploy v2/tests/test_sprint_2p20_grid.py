"""
tests/test_sprint_2p20_grid.py — Sprint 2.20.0 isolated tests (standalone runner).

Run: python tests/test_sprint_2p20_grid.py

Covers the Land Comparable Adjustments Grid (time-only v1):
  - time adjustment math (normalise to valuation date)
  - E11 confidence gating (reliable>=20 / indicative 10-19 / <10 fallback)
  - fallback path (no grid below 10)
  - framework structurally supports a 'size' factor (composes) — v1 never emits one
  - E8 weighted_median
  - output_briefs grid section: audience full/summary/hidden + footer
  - Layer-2 (Rule #40): real adjustment_grid -> real output_briefs chain + version bump
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import adjustment_grid as ag        # noqa: E402
import output_briefs as ob          # noqa: E402

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  ok  {name}")
    else:
        _failed += 1
        print(f"  XX  {name}")


def _comps(n, start_price=4000, step=40):
    # dates spread across 2025; all within a 24m window of a 2026 valuation date
    return [{'date': f'2025-{(i % 12) + 1:02d}-15',
             'price_m2': start_price + i * step, 'area_m2': 700 + i}
            for i in range(n)]


def test_time_adjustment_math():
    # one comparable exactly 2 years before valuation, +10%/yr trend
    g = ag.build_land_grid(
        [{'date': '2024-05-20', 'price_m2': 1000.0, 'area_m2': 700}] + _comps(11),
        valuation_date='2026-05-20', annual_trend_pct=10.0)
    c0 = next(c for c in g.comparables if c.date == '2024-05-20')
    # years = 730/365.25 = 1.99863 -> time_pct = 0.199863 -> adjusted ~1199.86
    check("time-adjusted value normalised forward (+10%/yr, 2y)",
          abs(c0.adjusted_price_per_m2 - 1199.86) < 1.0)
    check("time adjustment is a T1 moj factor",
          c0.adjustments and c0.adjustments[0].factor == 'time'
          and c0.adjustments[0].source == 'moj' and c0.adjustments[0].tier == 1)


def test_zero_trend_no_adjustment():
    g = ag.build_land_grid(_comps(12), valuation_date='2026-05-20', annual_trend_pct=0.0)
    c = g.comparables[0]
    check("zero trend -> no time adjustment", not c.adjustments
          and abs(c.adjusted_price_per_m2 - c.price_per_m2_raw) < 1e-9)


def test_confidence_gating():
    g_rel = ag.build_land_grid(_comps(20), valuation_date='2026-05-20', annual_trend_pct=-2.0)
    g_ind = ag.build_land_grid(_comps(12), valuation_date='2026-05-20', annual_trend_pct=-2.0)
    g_fb = ag.build_land_grid(_comps(9), valuation_date='2026-05-20', annual_trend_pct=-2.0)
    check("n=20 -> reliable", g_rel.confidence == 'reliable' and not g_rel.fallback_used)
    check("n=12 -> indicative", g_ind.confidence == 'indicative' and not g_ind.fallback_used)
    check("n=9 -> fallback (no grid)",
          g_fb.confidence == 'fallback' and g_fb.fallback_used
          and g_fb.adjusted_median_per_m2 is None and g_fb.comparables == [])


def test_framework_supports_size_factor():
    # v1 never emits 'size', but the math must compose if a size Adjustment exists.
    c = ag.Comparable(price_per_m2_raw=1000.0, date='2025-01-01', size_m2=700, adjustments=[
        ag.Adjustment(factor='time', pct=0.10, source='moj', tier=1),
        ag.Adjustment(factor='size', pct=-0.05, source='moj', tier=1),
    ])
    # 1000 * 1.10 * 0.95 = 1045
    check("size+time compose multiplicatively", abs(c.adjusted_price_per_m2 - 1045.0) < 1e-6)
    check("tier_weight from E8 map", ag.Adjustment('size', 0, 'arady', 2).tier_weight == 0.7)


def test_weighted_median_E8():
    check("equal weights == plain median",
          ag.weighted_median([(10, 1), (20, 1), (30, 1)]) == 20)
    check("weight shifts the median",
          ag.weighted_median([(10, 5), (20, 1), (30, 1)]) == 10)
    check("empty -> None", ag.weighted_median([]) is None)


def test_grid_section_audience():
    g = ag.build_land_grid(_comps(22), valuation_date='2026-05-20',
                           annual_trend_pct=-3.0, subject={'area': 'الوكير'}).to_dict()
    full = ob.build_comparable_grid_section(g, audience='valuer')
    summ = ob.build_comparable_grid_section(g, audience='buyer')
    hidden = ob.build_comparable_grid_section(g, audience='secretary')
    check("valuer -> full detail", full and full['content']['detail'] == 'full')
    check("buyer -> summary detail", summ and summ['content']['detail'] == 'summary')
    check("secretary -> hidden (None)", hidden is None)
    check("section id + Arabic title",
          full['id'] == 'comparable_grid' and 'المقارنات' in full['title_ar'])
    check("E10 sources present (moj T1)",
          full['content']['sources'] and full['content']['sources'][0]['tier'] == 1)
    check("UX footer present (deferred features)",
          'geographically-keyed' in full['content']['footer_ar'])
    check("confidence translated to Arabic",
          full['content']['confidence_ar'] == 'موثوقة')


def test_grid_section_fallback_hidden():
    g_fb = ag.build_land_grid(_comps(5)).to_dict()
    check("fallback grid -> no section", ob.build_comparable_grid_section(g_fb) is None)


def test_layer2_production_chain():
    # Rule #40: exercise the REAL production functions the engine calls.
    import evaluate_unified as eu
    check("ENGINE_VERSION bumped to 2.20.0",
          eu.ENGINE_VERSION == 'thammen-sprint2p20p0-time-adjustment-grid'
          and eu.SPRINT_TAG == '2.20.0')
    # the exact symbol evaluate_unified imports at runtime
    from output_briefs import build_comparable_grid_section as real_builder
    g = ag.build_land_grid(_comps(18), valuation_date='2026-05-20', annual_trend_pct=-2.5).to_dict()
    sec = real_builder(g, audience='investor')
    check("real chain: grid -> section renders comparables",
          sec and len(sec['content']['comparables']) == 18
          and sec['content']['adjusted_median_per_m2'] is not None)


if __name__ == "__main__":
    print("Sprint 2.20.0 — Land Adjustment Grid isolated tests")
    print("=" * 70)
    test_time_adjustment_math()
    test_zero_trend_no_adjustment()
    test_confidence_gating()
    test_framework_supports_size_factor()
    test_weighted_median_E8()
    test_grid_section_audience()
    test_grid_section_fallback_hidden()
    test_layer2_production_chain()
    print("=" * 70)
    print(f"Sprint 2.20.0 tests: {_passed} passed, {_failed} failed")
    sys.exit(0 if _failed == 0 else 1)
