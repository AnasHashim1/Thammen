"""
tests/test_sprint_2p18p1_parallel_bfs.py
========================================
Sprint 2.18.1 — Parallel BFS upfront-prefetch in qatar_gis._expand_extent.

Run: python tests/test_sprint_2p18p1_parallel_bfs.py

What this Sprint ships (and what these tests cover):
  - _expand_extent() pre-fetches all `eligible` plot polygons in parallel via
    ThreadPoolExecutor(max_workers=min(N, 20)) before the BFS loop runs.
  - The BFS loop body is byte-identical to pre-2.18.1 (cache-hit only).
  - Failed individual fetches are non-fatal: cached_polygons[pin]=None,
    note appended, BFS skips that PIN (existing contract).
  - Final included set is mathematically identical to the pre-2.18.1 serial
    version (reachability is invariant under fetch order).

What these tests do NOT exercise (out of scope by design):
  - Real GIS network calls (we monkey-patch get_plot + get_plots_in_bbox —
    Rule #40 production verification comes from the post-deploy audit
    comparison on 51/835/17 / multi_qars_56 / safe_villa_52).
  - Latency improvement on real network (measured post-deploy by
    audit_a6_latency.py, NOT by unit tests).

Rule #40 production verification: the QatarGIS class imported and exercised
below IS the production class — no replica. We monkey-patch get_plot and
get_plots_in_bbox on the instance to inject synthetic topologies with
controlled boundary-sharing, so we can assert the BFS produces the
mathematically-correct included set without network calls.
"""
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import qatar_gis                                                # noqa: E402
from qatar_gis import (                                         # noqa: E402
    QatarGIS, PlotInfo, PolygonShape, AssetType, AssetClassification,
)

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
# Synthetic plot builders
# ====================================================================

def _square_4326(cx, cy, half_deg):
    """Square ring in lon/lat 4326 (CCW)."""
    return [
        [cx - half_deg, cy - half_deg],
        [cx + half_deg, cy - half_deg],
        [cx + half_deg, cy + half_deg],
        [cx - half_deg, cy + half_deg],
        [cx - half_deg, cy - half_deg],
    ]


def _square_2932(cx_m, cy_m, half_m):
    """Square ring in projected 2932 metres (CCW). Used by _polygons_share_boundary."""
    return [
        [cx_m - half_m, cy_m - half_m],
        [cx_m + half_m, cy_m - half_m],
        [cx_m + half_m, cy_m + half_m],
        [cx_m - half_m, cy_m + half_m],
        [cx_m - half_m, cy_m - half_m],
    ]


def _make_plot(pin, cx_m, cy_m, half_m, pd_no='0', pdarea=None):
    """Build a synthetic PlotInfo at (cx_m, cy_m) with half-side `half_m`.

    PlotInfo's polygon_2932 is what _polygons_share_boundary actually compares.
    The 4326 coords are unused by BFS; we still fill them with placeholders so
    `bbox_4326` is non-degenerate downstream (combined_bbox computation).
    """
    poly_2932 = _square_2932(cx_m, cy_m, half_m)
    # Use a tiny 4326 placeholder so combined_bbox computation succeeds.
    poly_4326 = _square_4326(51.5 + cx_m * 1e-6, 25.3 + cy_m * 1e-6, half_m * 1e-6)
    lons = [p[0] for p in poly_4326]
    lats = [p[1] for p in poly_4326]
    bbox = (min(lons), min(lats), max(lons), max(lats))
    return PlotInfo(
        pin=pin,
        pdarea=pdarea if pdarea is not None else (2 * half_m) ** 2,
        pd_no=str(pd_no),
        cdst_key=pin,
        ref_number=None,
        polygon_4326=poly_4326,
        polygon_2932=poly_2932,
        bbox_4326=bbox,
        is_unsubdivided=(str(pd_no) == '0'),
        shape=PolygonShape(vertex_count=4, is_rectangular=True, is_irregular=False,
                           convex_hull_ratio=1.0, aspect_ratio=1.0,
                           irregularity_warning=None),
    )


def _patch_gis(gis, plots_by_pin, candidates_in_bbox, fetch_delay=0.0,
               fail_pins=None, raise_pins=None):
    """Monkey-patch get_plot + get_plots_in_bbox on a real QatarGIS instance.

    - plots_by_pin: dict {pin: PlotInfo}
    - candidates_in_bbox: list of {'pin', 'pdarea', 'pd_no'} dicts returned by
      get_plots_in_bbox (BFS calls this twice — wide + tight). We return the
      same list both times (the BFS will dedupe by PIN anyway).
    - fetch_delay: per-call sleep in seconds (proves concurrency in T7).
    - fail_pins: PINs for which get_plot returns None (graceful failure).
    - raise_pins: PINs for which get_plot raises (caught by the prefetch).
    """
    fail_pins = set(fail_pins or [])
    raise_pins = set(raise_pins or [])

    def fake_get_plot(pin):
        if fetch_delay:
            time.sleep(fetch_delay)
        if pin in raise_pins:
            raise RuntimeError(f'synthetic fetch error for PIN={pin}')
        if pin in fail_pins:
            return None
        return plots_by_pin.get(pin)

    def fake_get_plots_in_bbox(min_lon, min_lat, max_lon, max_lat, min_area=0):
        return [c for c in candidates_in_bbox if c['pdarea'] >= min_area]

    gis.get_plot = fake_get_plot
    gis.get_plots_in_bbox = fake_get_plots_in_bbox


def _run_expand(gis, seed, asset_type=AssetType.COMPOUND_SMALL):
    """Drive _expand_extent against a patched gis instance."""
    from qatar_gis import EXTENT_CONFIG
    config = EXTENT_CONFIG[asset_type]
    notes = []
    return gis._expand_extent(seed, asset_type, config, notes, 'medium')


# ====================================================================
# T1 — Synthetic compound: prefetch produces mathematically correct included set
# ====================================================================

def test_01_prefetch_matches_expected_on_synthetic_compound():
    """5-parcel synthetic compound: seed + 4 neighbours, all sharing boundaries.

    Topology (metres, centres):
        N1(0,200)
    W4(-200,0)  S(0,0)  E2(200,0)
        N3(0,-200)
    All four neighbours touch seed (1m gap < 10m threshold). Expected:
    included == {seed, N1, E2, N3, W4}, total 5.
    """
    gis = QatarGIS.__new__(QatarGIS)  # bypass __init__ (no cache_dir needed)
    seed = _make_plot(pin=1000, cx_m=0, cy_m=0, half_m=99, pd_no='0', pdarea=10000)
    n1 = _make_plot(pin=1001, cx_m=0, cy_m=200, half_m=99, pd_no='0', pdarea=10000)
    e2 = _make_plot(pin=1002, cx_m=200, cy_m=0, half_m=99, pd_no='0', pdarea=10000)
    n3 = _make_plot(pin=1003, cx_m=0, cy_m=-200, half_m=99, pd_no='0', pdarea=10000)
    w4 = _make_plot(pin=1004, cx_m=-200, cy_m=0, half_m=99, pd_no='0', pdarea=10000)
    plots = {1001: n1, 1002: e2, 1003: n3, 1004: w4}
    cand_list = [
        {'pin': 1001, 'pdarea': 10000, 'pd_no': '0'},
        {'pin': 1002, 'pdarea': 10000, 'pd_no': '0'},
        {'pin': 1003, 'pdarea': 10000, 'pd_no': '0'},
        {'pin': 1004, 'pdarea': 10000, 'pd_no': '0'},
    ]
    _patch_gis(gis, plots, cand_list)
    extent = _run_expand(gis, seed)
    pins = set(extent.included_pins)
    check(f"T1: 5 parcels included — got {sorted(pins)}",
          pins == {1000, 1001, 1002, 1003, 1004})
    check(f"T1: total_area_m2 ~= 50000 -- got {extent.total_area_m2}",
          abs(extent.total_area_m2 - 50000) < 1)


# ====================================================================
# T2 — Empty eligible list → BFS exits cleanly with seed only
# ====================================================================

def test_02_empty_eligible_list():
    """No candidates in bbox → eligible=[] → BFS loop runs 0 iterations,
    included = {seed}."""
    gis = QatarGIS.__new__(QatarGIS)
    seed = _make_plot(pin=2000, cx_m=0, cy_m=0, half_m=99, pdarea=10000)
    _patch_gis(gis, plots_by_pin={}, candidates_in_bbox=[])
    extent = _run_expand(gis, seed)
    check(f"T2: only seed included — got {extent.included_pins}",
          list(extent.included_pins) == [2000])
    check(f"T2: total area = seed area ({seed.pdarea}) — got {extent.total_area_m2}",
          extent.total_area_m2 == seed.pdarea)


# ====================================================================
# T3 — Single eligible candidate (max_workers effectively = 1)
# ====================================================================

def test_03_single_eligible_candidate():
    """One adjacent parcel → max_workers=min(1,20)=1. Must still complete."""
    gis = QatarGIS.__new__(QatarGIS)
    seed = _make_plot(pin=3000, cx_m=0, cy_m=0, half_m=99, pdarea=10000)
    nb = _make_plot(pin=3001, cx_m=200, cy_m=0, half_m=99, pdarea=10000)
    _patch_gis(gis, {3001: nb},
               [{'pin': 3001, 'pdarea': 10000, 'pd_no': '0'}])
    extent = _run_expand(gis, seed)
    check(f"T3: two parcels included — got {sorted(extent.included_pins)}",
          set(extent.included_pins) == {3000, 3001})


# ====================================================================
# T4 — One prefetch returns None → BFS skips it gracefully
# ====================================================================

def test_04_one_prefetch_returns_none():
    """Two candidates; PIN 4002 fetch returns None.
    BFS must still include the other candidate."""
    gis = QatarGIS.__new__(QatarGIS)
    seed = _make_plot(pin=4000, cx_m=0, cy_m=0, half_m=99, pdarea=10000)
    nb_ok = _make_plot(pin=4001, cx_m=200, cy_m=0, half_m=99, pdarea=10000)
    _patch_gis(gis, {4001: nb_ok},  # 4002 not in dict → fake returns None
               [{'pin': 4001, 'pdarea': 10000, 'pd_no': '0'},
                {'pin': 4002, 'pdarea': 10000, 'pd_no': '0'}],
               fail_pins=[4002])
    extent = _run_expand(gis, seed)
    check(f"T4: 4001 included, 4002 skipped — got {sorted(extent.included_pins)}",
          set(extent.included_pins) == {4000, 4001})


# ====================================================================
# T5 — One prefetch RAISES exception → BFS marks pin None, continues
# ====================================================================

def test_05_one_prefetch_raises_exception():
    """get_plot raises for PIN 5002. The futures-prefetch try/except must catch
    it, mark cached_polygons[5002]=None, append a note, and BFS proceeds with
    the remaining candidate."""
    gis = QatarGIS.__new__(QatarGIS)
    seed = _make_plot(pin=5000, cx_m=0, cy_m=0, half_m=99, pdarea=10000)
    nb_ok = _make_plot(pin=5001, cx_m=200, cy_m=0, half_m=99, pdarea=10000)
    _patch_gis(gis, {5001: nb_ok},
               [{'pin': 5001, 'pdarea': 10000, 'pd_no': '0'},
                {'pin': 5002, 'pdarea': 10000, 'pd_no': '0'}],
               raise_pins=[5002])
    extent = _run_expand(gis, seed)
    check(f"T5a: 5001 included, 5002 errored-skipped — got {sorted(extent.included_pins)}",
          set(extent.included_pins) == {5000, 5001})
    has_failure_note = any('BFS prefetch failed for PIN=5002' in n
                           for n in extent.notes)
    check(f"T5b: failure note recorded in extent.notes (audit trail)",
          has_failure_note)


# ====================================================================
# T6 — Determinism: two runs on same input produce IDENTICAL output
# ====================================================================

def test_06_deterministic_output_via_sorted():
    """`sorted(included.keys(), key=str)` makes the output PIN list deterministic
    regardless of which thread completed first. Run twice and compare."""
    def _build_gis():
        gis = QatarGIS.__new__(QatarGIS)
        seed = _make_plot(pin=6000, cx_m=0, cy_m=0, half_m=99, pdarea=10000)
        nbs = {pin: _make_plot(pin=pin, cx_m=200, cy_m=(i - 1) * 200,
                                half_m=99, pdarea=10000)
               for i, pin in enumerate([6001, 6002, 6003])}
        _patch_gis(gis, nbs,
                   [{'pin': p, 'pdarea': 10000, 'pd_no': '0'} for p in nbs])
        return gis, seed
    gis_a, seed_a = _build_gis()
    extent_a = _run_expand(gis_a, seed_a)
    gis_b, seed_b = _build_gis()
    extent_b = _run_expand(gis_b, seed_b)
    check(f"T6a: included_pins identical across runs — A={extent_a.included_pins}  B={extent_b.included_pins}",
          extent_a.included_pins == extent_b.included_pins)
    check(f"T6b: total_area identical across runs — A={extent_a.total_area_m2}  B={extent_b.total_area_m2}",
          extent_a.total_area_m2 == extent_b.total_area_m2)


# ====================================================================
# T7 — max_workers capped at 20 (not equal to eligible count when N > 20)
# ====================================================================

def test_07_max_workers_capped_at_20():
    """When len(eligible) > 20, ThreadPoolExecutor must be constructed with
    max_workers=20 (not the full eligible count). We capture max_workers via
    monkey-patching ThreadPoolExecutor."""
    captured = {}
    orig_pool = qatar_gis.ThreadPoolExecutor

    class _SpyPool(orig_pool):
        def __init__(self, *args, max_workers=None, **kwargs):
            captured['max_workers'] = max_workers
            super().__init__(*args, max_workers=max_workers, **kwargs)

    qatar_gis.ThreadPoolExecutor = _SpyPool
    try:
        gis = QatarGIS.__new__(QatarGIS)
        seed = _make_plot(pin=7000, cx_m=0, cy_m=0, half_m=99, pdarea=10000)
        # Build 30 candidates (all far from seed; boundary tests will fail —
        # but that doesn't matter, we only assert max_workers from the spy).
        plots = {}
        cands = []
        for i in range(30):
            pin = 7001 + i
            plots[pin] = _make_plot(pin=pin, cx_m=10000 + i * 500, cy_m=0,
                                    half_m=99, pdarea=10000)
            cands.append({'pin': pin, 'pdarea': 10000, 'pd_no': '0'})
        _patch_gis(gis, plots, cands)
        _run_expand(gis, seed)
    finally:
        qatar_gis.ThreadPoolExecutor = orig_pool

    check(f"T7: max_workers capped at 20 when N=30 — got {captured.get('max_workers')}",
          captured.get('max_workers') == 20)


# ====================================================================
# T8 — Concurrency proof: with per-fetch delay, total wall-clock < serial
# ====================================================================

def test_08_actually_runs_in_parallel():
    """20 candidates × 100ms delay each. Serial would be ~2000ms; parallel
    (max_workers=20) is ~100ms + overhead. Threshold = 800ms = 5× speedup."""
    gis = QatarGIS.__new__(QatarGIS)
    seed = _make_plot(pin=8000, cx_m=0, cy_m=0, half_m=99, pdarea=10000)
    plots = {}
    cands = []
    for i in range(20):
        pin = 8001 + i
        # Place neighbours adjacent to seed in a chain so boundary tests
        # mostly succeed and the included set ends up non-trivial.
        plots[pin] = _make_plot(pin=pin, cx_m=200 * (i + 1), cy_m=0,
                                half_m=99, pdarea=10000)
        cands.append({'pin': pin, 'pdarea': 10000, 'pd_no': '0'})
    _patch_gis(gis, plots, cands, fetch_delay=0.10)
    t0 = time.perf_counter()
    _run_expand(gis, seed)
    dt = time.perf_counter() - t0
    check(f"T8: wall clock {dt*1000:.0f}ms < 800ms (parallel; serial ~= 2000ms)",
          dt < 0.80)


# ====================================================================
# Runner
# ====================================================================

def main():
    print("\n=== Sprint 2.18.1 — Parallel BFS upfront-prefetch ===\n")
    for fn in [
        test_01_prefetch_matches_expected_on_synthetic_compound,
        test_02_empty_eligible_list,
        test_03_single_eligible_candidate,
        test_04_one_prefetch_returns_none,
        test_05_one_prefetch_raises_exception,
        test_06_deterministic_output_via_sorted,
        test_07_max_workers_capped_at_20,
        test_08_actually_runs_in_parallel,
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
