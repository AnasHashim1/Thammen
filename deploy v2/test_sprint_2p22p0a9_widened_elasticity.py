# -*- coding: utf-8 -*-
"""Sprint 2.22.0a.9 — isolated tests for facet (a): age/quality elasticity on
the widened (geo_value) headline.

Run:  set PYTHONIOENCODING=utf-8  &&  python test_sprint_2p22p0a9_widened_elasticity.py

Proves (deterministically, no GIS):
  * _age_quality_adj sums ONLY building_age + plot_shape (location excluded),
    clamps to ±MAX_ADJUSTMENT, and returns 0.0 on missing/empty detail.
  * _select_primary_comparison applies the adj to comparison_widened +
    comparison_widened_indicative ONLY; bracket / thin / preliminary are
    byte-stable; the no-factor case is a byte-identical no-op; the adj is
    applied exactly once (no double-count).
"""
import sys
from types import SimpleNamespace

import property_factors
from evaluate_unified import (
    _age_quality_adj,
    _select_primary_comparison,
    MIN_N_RELIABLE,
    MIN_N_INDICATIVE,
    MIN_N_BOUND_ONLY,
)

CAP = property_factors.MAX_ADJUSTMENT  # ±0.10

_results = []


def check(name, cond):
    _results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


def _detail(*pairs):
    """Build a factors_detail list (list of dicts with code/weight)."""
    return [{'code': c, 'weight': w} for (c, w) in pairs]


def _val(bracket_n=0, fair=None, median=None, low=None, high=None, detail=None):
    return SimpleNamespace(
        bracket_n=bracket_n,
        fair_price_total=fair,
        moj_median_total=median,
        estimated_value_low=low,
        estimated_value_high=high,
        factors_detail=detail,
    )


# ───────────────────────── _age_quality_adj ──────────────────────────
def test_age_quality_adj():
    print("test_age_quality_adj")
    # only building_age + plot_shape count; location factors excluded
    v = _val(detail=_detail(
        ('building_age', -0.040), ('plot_shape', -0.020),
        ('zoning', +0.020), ('landmark', +0.030),
        ('main_road', +0.015), ('permitted_height', +0.020),
        ('commercial_street', -0.010),
    ))
    check("age+plot only (location excluded) == -0.06", _age_quality_adj(v) == -0.06)

    # positive age (new build), regular plot (0)
    v2 = _val(detail=_detail(('building_age', +0.030), ('plot_shape', 0.0)))
    check("new build +0.03", _age_quality_adj(v2) == 0.03)

    # clamp binds at -CAP for an (artificial) extreme age+plot sum
    v3 = _val(detail=_detail(('building_age', -0.090), ('plot_shape', -0.050)))
    check("clamp at -MAX_ADJUSTMENT", _age_quality_adj(v3) == round(-CAP, 4))

    # empty / None / missing-detail → 0.0 (no-op)
    check("empty detail -> 0.0", _age_quality_adj(_val(detail=[])) == 0.0)
    check("None detail -> 0.0", _age_quality_adj(_val(detail=None)) == 0.0)
    check("None valuation -> 0.0", _age_quality_adj(None) == 0.0)

    # missing 'weight' key is treated as 0, no crash
    v4 = SimpleNamespace(factors_detail=[{'code': 'building_age'}])
    check("missing weight -> 0.0", _age_quality_adj(v4) == 0.0)

    # location-only detail → 0.0 (nothing in the age/quality set)
    v5 = _val(detail=_detail(('zoning', +0.02), ('landmark', +0.03)))
    check("location-only -> 0.0", _age_quality_adj(v5) == 0.0)


# ─────────────────────── _select_primary_comparison ───────────────────────
def test_selection_paths():
    print("test_selection_paths")
    age45 = _detail(('building_age', -0.040), ('plot_shape', 0.0))  # aq = -0.04
    geo = {'total_n': 42, 'estimated_value': 4_500_000,
           'range_low': 3_300_000, 'range_high': 5_400_000}

    # Case 1 — bracket (n>=20): value = fair_price_total, NO aq applied
    ev = SimpleNamespace(valuation=_val(bracket_n=29, fair=2_500_000,
                                        low=2_200_000, high=2_600_000, detail=age45))
    p = _select_primary_comparison(ev, {'total_n': 0})
    check("bracket method", p['method'] == 'comparison_bracket')
    check("bracket value untouched (== fair, no aq)", p['value'] == 2_500_000)

    # Case 2 — widened (n>=20, >=3x bracket): aq applied ONCE
    ev = SimpleNamespace(valuation=_val(bracket_n=1, fair=None, median=4_400_000,
                                        detail=age45))
    p = _select_primary_comparison(ev, geo)
    expect = round(4_500_000 * (1 - 0.04), -3)  # 4,320,000
    check("widened method", p['method'] == 'comparison_widened')
    check("widened value = base*(1+aq) once", p['value'] == expect)
    check("widened value != base (moved)", p['value'] != 4_500_000)
    check("widened low scaled", p['low'] == round(3_300_000 * 0.96, -3))
    check("widened high scaled", p['high'] == round(5_400_000 * 0.96, -3))
    # no double-count: not base*(1+aq)^2
    check("no adj^2 double-count", p['value'] != round(4_500_000 * (0.96 ** 2), -3))

    # Case 3 — widened_indicative (geo_n in [10,20), bracket<10)
    geo_ind = {'total_n': 12, 'estimated_value': 4_500_000,
               'range_low': 3_300_000, 'range_high': 5_400_000}
    ev = SimpleNamespace(valuation=_val(bracket_n=1, median=4_400_000, detail=age45))
    p = _select_primary_comparison(ev, geo_ind)
    check("widened_indicative method", p['method'] == 'comparison_widened_indicative')
    check("widened_indicative value scaled", p['value'] == expect)

    # Case 4 — thin (5 <= bracket_n < 20, no usable geo): value = bracket, NO aq
    ev = SimpleNamespace(valuation=_val(bracket_n=7, fair=3_000_000, detail=age45))
    p = _select_primary_comparison(ev, {'total_n': 0})
    check("thin method", p['method'] == 'comparison_thin')
    check("thin value untouched (== fair, no aq)", p['value'] == 3_000_000)

    # Case 5 — preliminary (3 <= bracket_n < 5): value = bracket, NO aq
    ev = SimpleNamespace(valuation=_val(bracket_n=3, fair=3_000_000, detail=age45))
    p = _select_primary_comparison(ev, {'total_n': 0})
    check("preliminary method", p['method'] == 'comparison_preliminary')
    check("preliminary value untouched", p['value'] == 3_000_000)


def test_widened_noop_byte_stable():
    print("test_widened_noop_byte_stable")
    geo = {'total_n': 42, 'estimated_value': 4_500_000,
           'range_low': 3_300_000, 'range_high': 5_400_000}

    # No factor detail → aq = 0 → widened value byte-IDENTICAL to geo_value
    ev = SimpleNamespace(valuation=_val(bracket_n=1, median=4_400_000, detail=None))
    p = _select_primary_comparison(ev, geo)
    check("noop method still widened", p['method'] == 'comparison_widened')
    check("noop value == geo_value exactly", p['value'] == 4_500_000)
    check("noop value identity (is)", p['value'] is geo['estimated_value'])
    check("noop low == range_low", p['low'] == 3_300_000)
    check("noop high == range_high", p['high'] == 5_400_000)

    # location-only factors → aq = 0 → no-op as well
    loc_only = _detail(('zoning', +0.02), ('landmark', +0.03), ('main_road', +0.015))
    ev = SimpleNamespace(valuation=_val(bracket_n=1, median=4_400_000, detail=loc_only))
    p = _select_primary_comparison(ev, geo)
    check("location-only widened no-op", p['value'] == 4_500_000)


def main():
    test_age_quality_adj()
    test_selection_paths()
    test_widened_noop_byte_stable()
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"\n{passed}/{total} PASS")
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
