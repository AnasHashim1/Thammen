# -*- coding: utf-8 -*-
"""Sprint 2.22.0a.10 — isolated tests for the Stage-1 honest-range dispersion gate.

Run:  set PYTHONIOENCODING=utf-8  &&  python test_sprint_2p22p0a10_honest_range.py

Deterministic (no GIS): exercises the production helper `_stage1_dispersion_gate`
(gating decision, threshold, method exclusion, missing-data guards). The override
application (tier→indicative + MVU widen + AR/EN disclosure, point retained) is
verified end-to-end by the live local smoke on 54/541/6 + 56/647/6 + 56/565/21.
"""
import sys
from evaluate_unified import _stage1_dispersion_gate, STAGE1_DISPERSION_T

_results = []


def check(name, cond):
    _results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


def gate(method, p25, p75, med):
    return _stage1_dispersion_gate({'method': method},
                                   {'p25_m2': p25, 'p75_m2': p75, 'weighted_median_m2': med})


def main():
    print("test_stage1_dispersion_gate")
    check("threshold default is 0.30", STAGE1_DISPERSION_T == 0.30)

    # Real anchors — both widened villas fire (Option A, T=0.30)
    g_mar = gate('comparison_widened', 5376, 8814, 7333)
    check("Marikh dispersion ~0.469", g_mar and g_mar['dispersion'] == 0.469)
    check("Marikh gated", g_mar and g_mar['gated'] is True)
    g_maa = gate('comparison_widened', 4416, 6778, 5811)
    check("Maamoura dispersion ~0.406", g_maa and g_maa['dispersion'] == 0.406)
    check("Maamoura gated (H3 corrected — pool is dispersed)", g_maa and g_maa['gated'] is True)

    # widened_indicative also eligible
    g_ind = gate('comparison_widened_indicative', 5376, 8814, 7333)
    check("widened_indicative gated", g_ind and g_ind['gated'] is True)

    # Boundary: dispersion exactly 0.30 fires (>=)
    g_b = gate('comparison_widened', 4250, 5750, 5000)
    check("boundary disp==0.30 fires", g_b and g_b['dispersion'] == 0.3 and g_b['gated'] is True)
    # Just below threshold does NOT fire
    g_lo = gate('comparison_widened', 4260, 5740, 5000)
    check("disp 0.296 does NOT fire", g_lo and g_lo['gated'] is False)
    # Genuinely tight pool does NOT fire
    g_tight = gate('comparison_widened', 4500, 5500, 5000)
    check("tight pool disp 0.20 does NOT fire", g_tight and g_tight['gated'] is False)

    # Method exclusions → None (bracket / thin / preliminary never gate)
    check("bracket method -> None", gate('comparison_bracket', 5376, 8814, 7333) is None)
    check("thin method -> None", gate('comparison_thin', 5376, 8814, 7333) is None)
    check("preliminary method -> None", gate('comparison_preliminary', 5376, 8814, 7333) is None)

    # Missing-data / degenerate guards → None
    check("missing p25 -> None",
          _stage1_dispersion_gate({'method': 'comparison_widened'},
                                  {'p75_m2': 8814, 'weighted_median_m2': 7333}) is None)
    check("zero median -> None", gate('comparison_widened', 5376, 8814, 0) is None)
    check("None primary -> None",
          _stage1_dispersion_gate(None, {'p25_m2': 1, 'p75_m2': 2, 'weighted_median_m2': 1}) is None)
    check("None geo_v2 -> None", _stage1_dispersion_gate({'method': 'comparison_widened'}, None) is None)

    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"\n{passed}/{total} PASS")
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
