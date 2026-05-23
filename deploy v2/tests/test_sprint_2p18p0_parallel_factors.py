"""
tests/test_sprint_2p18p0_parallel_factors.py
============================================
Sprint 2.18.0 — Parallel property_factors fan-out.

Run: python tests/test_sprint_2p18p0_parallel_factors.py

What this Sprint ships (and what these tests cover):
  - analyze_property() runs its 5 GIS helpers in parallel via
    ThreadPoolExecutor(max_workers=5).
  - The merge order of the resulting `factors` list is byte-identical to
    the pre-2.18.0 serial code (so brief rendering, raw_adjustment sum,
    and `factors[0]` semantics are unchanged).
  - Helpers that return None / [] are merged gracefully.

What these tests do NOT exercise (out of scope by design):
  - Real GIS network calls (we stub the 5 helpers — Rule #40 also covers
    a production-line check via the existing test suite which imports the
    real module).
  - Latency improvement (that's measured by audit_a6_latency.py post-deploy,
    not by unit tests — wall-clock measurement under a stubbed scheduler is
    not informative).

Rule #40 production verification: the analyze_property function imported and
exercised below IS the production function — no replica. The 5 _factor_*
helpers are monkey-patched to deterministic stubs so we can assert merge
order without making network calls.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import property_factors                                  # noqa: E402
from property_factors import Factor, analyze_property    # noqa: E402

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


# ====================================================================
# Stub builders — deterministic Factor objects with unique names so the
# merge-order assertions are unambiguous.
# ====================================================================

def _mk_factor(name, weight=0.01):
    return Factor(name=name, label_ar=f'AR:{name}', source=f'src/{name}',
                  direction='positive' if weight > 0 else 'negative',
                  weight=weight, detail='stub')


# Stubs that return one factor each (or a list, for landmarks)
def _stub_zoning(lat, lon, purpose):       return _mk_factor('z_stub', +0.01)
def _stub_commercial(lat, lon, purpose):   return _mk_factor('c_stub', -0.005)
def _stub_road(lat, lon, purpose):         return _mk_factor('r_stub', -0.01)
def _stub_landmarks(lat, lon, purpose):    return [_mk_factor('l1_stub', +0.01),
                                                   _mk_factor('l2_stub', +0.005)]
def _stub_height(lat, lon):                return _mk_factor('h_stub', +0.015)


def _install_stubs(stubs):
    """Patch property_factors._factor_* names with stubs.
    Returns a callable to restore original."""
    orig = {
        'zoning':     property_factors._factor_zoning,
        'commercial': property_factors._factor_commercial_street,
        'road':       property_factors._factor_main_road,
        'landmarks':  property_factors._factor_landmarks,
        'height':     property_factors._factor_permitted_height,
    }
    for key, fn in stubs.items():
        if key == 'zoning':     property_factors._factor_zoning = fn
        if key == 'commercial': property_factors._factor_commercial_street = fn
        if key == 'road':       property_factors._factor_main_road = fn
        if key == 'landmarks':  property_factors._factor_landmarks = fn
        if key == 'height':     property_factors._factor_permitted_height = fn

    def restore():
        property_factors._factor_zoning             = orig['zoning']
        property_factors._factor_commercial_street  = orig['commercial']
        property_factors._factor_main_road          = orig['road']
        property_factors._factor_landmarks          = orig['landmarks']
        property_factors._factor_permitted_height   = orig['height']
    return restore


# ====================================================================
# T1 — Functional equivalence: parallel version produces the SAME factors
#       list (in the SAME order, with the SAME contents) as the serial code.
# ====================================================================

def test_01_parallel_returns_same_factors_as_serial():
    """Stub all 5 helpers with delay-free returns. The parallel
    analyze_property must produce the exact same `factors` list, in the
    exact same order, as the pre-2.18.0 serial version would have."""
    restore = _install_stubs({
        'zoning':     _stub_zoning,
        'commercial': _stub_commercial,
        'road':       _stub_road,
        'landmarks':  _stub_landmarks,
        'height':     _stub_height,
    })
    try:
        result = analyze_property(lat=25.0, lon=51.5, purpose='residential')
    finally:
        restore()

    # Expected order, byte-for-byte, per the pre-2.18.0 serial code:
    #   1. zoning  → 'z_stub'
    #   2. commercial → 'c_stub'
    #   3. road    → 'r_stub'
    #   4. landmarks (a list — extended) → ['l1_stub', 'l2_stub']
    #   5. height  → 'h_stub'
    expected = ['z_stub', 'c_stub', 'r_stub', 'l1_stub', 'l2_stub', 'h_stub']
    got = [f.name for f in result.factors]
    check("T1a: factor count = 6", len(got) == 6)
    check(f"T1b: factor order is byte-identical to serial — got {got}",
          got == expected)
    # Raw adjustment should be the sum of stub weights:
    # +0.01 + -0.005 + -0.01 + +0.01 + +0.005 + +0.015 = +0.025
    expected_raw = +0.025
    check(f"T1c: raw_adjustment = {expected_raw} (got {result.raw_adjustment})",
          abs(result.raw_adjustment - expected_raw) < 1e-6)
    # ±10% cap not hit (0.025 < 0.10) → adjustment == raw
    check(f"T1d: adjustment == raw_adjustment (no cap hit)",
          result.adjustment == result.raw_adjustment)
    # No notes (zoning returned a Factor, so the 'لم يُعثر على تصنيف' note must NOT fire)
    check("T1e: no missing-zoning note", all('زوننج' not in n for n in result.notes))


# ====================================================================
# T2 — Graceful merge when individual helpers return None / [].
# ====================================================================

def test_02_parallel_handles_one_helper_returning_None():
    """Mix of None / empty / valid returns. The merge logic must:
      - append the missing-zoning note when zoning returns None
      - skip None returns from commercial / road / height (no factor, no note)
      - .extend with an empty list from landmarks (no factor)
      - still produce a deterministic factor list with only the valid ones."""
    restore = _install_stubs({
        'zoning':     lambda lat, lon, purpose: None,    # → triggers note
        'commercial': lambda lat, lon, purpose: None,    # → silently skipped
        'road':       _stub_road,                         # → 'r_stub'
        'landmarks':  lambda lat, lon, purpose: [],      # → no entries
        'height':     lambda lat, lon: None,             # → silently skipped
    })
    try:
        result = analyze_property(lat=25.0, lon=51.5, purpose='residential')
    finally:
        restore()

    got = [f.name for f in result.factors]
    check(f"T2a: only road factor present — got {got}", got == ['r_stub'])
    check("T2b: missing-zoning note was appended",
          any('زوننج' in n for n in result.notes))
    check(f"T2c: raw_adjustment = -0.01 (just the road), got {result.raw_adjustment}",
          abs(result.raw_adjustment - (-0.01)) < 1e-6)
    check(f"T2d: adjustment also -0.01 (no cap)",
          abs(result.adjustment - (-0.01)) < 1e-6)


# ====================================================================
# T3 — Bonus: prove parallelization actually happens (helpers run concurrently)
#       by giving each helper a measurable sleep and verifying wall-clock
#       wins. This is a soft sanity check, not a latency benchmark.
# ====================================================================

def test_03_helpers_actually_run_concurrently():
    """If each of the 5 helpers sleeps 200ms, serial = 1000ms, parallel ~200ms.
    We assert wall-clock < 700ms (4× margin over the ideal 200ms; loose enough
    to survive slow CI but tight enough to catch accidental serialization)."""
    def slow_factor(name, weight):
        def _fn(*args, **kwargs):
            time.sleep(0.2)
            return _mk_factor(name, weight)
        return _fn

    def slow_landmarks(*args, **kwargs):
        time.sleep(0.2)
        return [_mk_factor('l_slow', +0.01)]

    restore = _install_stubs({
        'zoning':     slow_factor('z_slow', +0.01),
        'commercial': slow_factor('c_slow', -0.005),
        'road':       slow_factor('r_slow', -0.01),
        'landmarks':  slow_landmarks,
        'height':     slow_factor('h_slow', +0.015) if False else
                      (lambda lat, lon: (time.sleep(0.2)
                                         or _mk_factor('h_slow', +0.015))),
    })
    t0 = time.perf_counter()
    try:
        result = analyze_property(lat=25.0, lon=51.5, purpose='residential')
    finally:
        restore()
    dt = time.perf_counter() - t0

    check(f"T3a: wall clock {dt*1000:.0f}ms < 700ms (parallel proof — serial would be ~1000ms)",
          dt < 0.70)
    # Count factors (should be 5: 4 single + 1 from landmarks list)
    got = [f.name for f in result.factors]
    check(f"T3b: all 5 factors present — got {got}",
          set(got) == {'z_slow', 'c_slow', 'r_slow', 'l_slow', 'h_slow'})


# ====================================================================
# Runner
# ====================================================================

def main():
    print("\n=== Sprint 2.18.0 — Parallel property_factors fan-out ===\n")
    for fn in [
        test_01_parallel_returns_same_factors_as_serial,
        test_02_parallel_handles_one_helper_returning_None,
        test_03_helpers_actually_run_concurrently,
    ]:
        print(f"\n-- {fn.__name__} --")
        try:
            fn()
        except Exception as e:
            global _failed
            _failed += 1
            print(f"  XX  {fn.__name__} raised {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    print(f"\n=== {_passed} passed / {_failed} failed ===")
    sys.exit(0 if _failed == 0 else 1)


if __name__ == '__main__':
    main()
