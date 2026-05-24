"""
tests/test_sprint_2p18p1p1_compound_misroute.py
================================================
Sprint 2.18.1.1 — Compound-misroute fix (Patches A + C).

Run: python tests/test_sprint_2p18p1p1_compound_misroute.py

What this Sprint ships (and what these tests cover):
  Patch A — qatar_gis.full_property_lookup: when classification.asset_type
    is COMPOUND_SMALL and extent.total_area_m2 >= 15,000 m², promote
    asset_type to COMPOUND_LARGE on both classification and extent. This
    routes downstream through ASSET_TYPE_TO_MOJ_CATEGORY['compound_large']
    = None → MoJ skipped → valuation_amount=None → clean refusal.

  Patch C — evaluate_unified._decompose_value: defensive sanity guard.
    When land_value (plot_area_m2 × land_per_m2) > valuation_amount,
    return None (refuses the decomposition). Universal — catches any
    asset_type where the decomposition would produce negative building
    value (compound misroute, premium-land teardown, MoJ outliers).

What these tests do NOT exercise:
  - Live GIS network calls (Rule #40 production verification comes from
    probe_compound_classifier_bug.py post-deploy against thammen.qa).
  - The full evaluate_unified pipeline (too coupled for isolated unit
    tests; the lite-classifier + MoJ + brief layers are exercised by the
    existing 320 prior sub-checks).

Rule #40 production verification: the QatarGIS class and _decompose_value
function imported below ARE the production functions. We monkey-patch
their GIS-touching inputs (find_property, get_plot, get_plots_in_bbox,
get_district_at_point) and the MoJ reference dict to assert the
promotion/refusal logic.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import qatar_gis                                                        # noqa: E402
from qatar_gis import (                                                 # noqa: E402
    QatarGIS, PlotInfo, PolygonShape, AssetType, AssetClassification,
    AssetExtent, PropertyLocation, DistrictInfo,
)
from evaluate_unified import _decompose_value                           # noqa: E402

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
# Helpers — synthetic plot + GIS stubs (shared with Sprint 2.18.1 tests)
# ====================================================================

def _square_2932(cx_m, cy_m, half_m):
    return [
        [cx_m - half_m, cy_m - half_m], [cx_m + half_m, cy_m - half_m],
        [cx_m + half_m, cy_m + half_m], [cx_m - half_m, cy_m + half_m],
        [cx_m - half_m, cy_m - half_m],
    ]


def _square_4326(cx, cy, half_deg):
    return [
        [cx - half_deg, cy - half_deg], [cx + half_deg, cy - half_deg],
        [cx + half_deg, cy + half_deg], [cx - half_deg, cy + half_deg],
        [cx - half_deg, cy - half_deg],
    ]


def _make_plot(pin, half_m, pd_no='0', cx_m=0, cy_m=0, pdarea=None):
    poly_2932 = _square_2932(cx_m, cy_m, half_m)
    poly_4326 = _square_4326(51.5, 25.3, half_m * 1e-6)
    lons = [p[0] for p in poly_4326]
    lats = [p[1] for p in poly_4326]
    bbox = (min(lons), min(lats), max(lons), max(lats))
    return PlotInfo(
        pin=pin, pdarea=pdarea if pdarea is not None else (2 * half_m) ** 2,
        pd_no=str(pd_no), cdst_key=pin, ref_number=None,
        polygon_4326=poly_4326, polygon_2932=poly_2932, bbox_4326=bbox,
        is_unsubdivided=(str(pd_no) == '0'),
        shape=PolygonShape(vertex_count=4, is_rectangular=True,
                           is_irregular=False, convex_hull_ratio=1.0,
                           aspect_ratio=1.0, irregularity_warning=None),
    )


def _make_gis_for_compound(seed_pin, n_parcels, parcel_area=5000):
    """Build a QatarGIS instance with synthetic compound topology.

    All parcels are uniform squares of `parcel_area` m² placed in a 1D
    chain along the +X axis. Adjacent parcels share exactly 2 corner
    vertices (distance=0 ≤ threshold 10m), so `_polygons_share_boundary`
    always succeeds for adjacent pairs. BFS discovers the chain
    iteratively from the seed.

    Args:
      seed_pin:     PIN of the seed plot at (0,0)
      n_parcels:    total parcel count (seed + neighbours). n_parcels=1
                    means seed only (no neighbours). Total area =
                    n_parcels × parcel_area.
      parcel_area:  m² per parcel; default 5000 (≥ 2000 minimum so
                    _should_include accepts unsubdivided neighbours).
    """
    gis = QatarGIS.__new__(QatarGIS)
    half = (parcel_area ** 0.5) / 2     # 35.36 m for 5000 m²
    pitch = 2 * half                    # adjacent centres exactly pitch apart
    plots = {}
    cands = []
    for i in range(n_parcels):
        pin = seed_pin + i
        cx = i * pitch                  # 0, 70.7, 141.4, ...
        plots[pin] = _make_plot(pin=pin, half_m=half, cx_m=cx, cy_m=0,
                                pdarea=parcel_area)
        if i > 0:
            # The seed is not in `get_plots_in_bbox` results (BFS doesn't
            # need to re-fetch the seed; it starts with seed already in
            # `included`). Neighbours go in the candidate list.
            cands.append({'pin': pin, 'pdarea': parcel_area, 'pd_no': '0'})
    seed = plots[seed_pin]

    # Stub the GIS methods used by full_property_lookup + detect_extent
    def fake_find_property(zone, street, building, **kwargs):
        return PropertyLocation(
            zone=zone, street=street, building=building, pin=seed_pin,
            qars='', plot_no_old=None, lon=51.5, lat=25.3,
            electricity_no=None, water_no=None, qtel_id=None,
            building_subtype=2,    # QARS subtype 2 = compound w/ villas
        )
    def fake_get_plot(pin):
        return plots.get(pin)
    def fake_get_plots_in_bbox(*args, min_area=0, **kwargs):
        return [c for c in cands if c['pdarea'] >= min_area]
    def fake_get_district_at_point(lon, lat):
        return DistrictInfo(dist_no=47, aname='الغرافة', ename='Al-Gharafa',
                            code='GHA')

    gis.find_property = fake_find_property
    gis.get_plot = fake_get_plot
    gis.get_plots_in_bbox = fake_get_plots_in_bbox
    gis.get_district_at_point = fake_get_district_at_point
    # estimate_construction_year is called only when include_imagery=True,
    # but we'll keep our calls with include_imagery=False, so no stub needed.
    return gis


# ====================================================================
# T1 — Patch A: compound_small under 15K is UNCHANGED (control)
# ====================================================================

def test_01_compound_small_under_15k_unchanged():
    """Seed=900 m² (typical compound_small QARS subtype) + 4 small neighbours
    totaling 12,000 m². Total extent = 12,900 m² < 15,000 → NO promotion.
    asset_type stays compound_small."""
    # 2 parcels × 5000 = 10,000 m² (< 15K → no promotion)
    gis = _make_gis_for_compound(seed_pin=1000, n_parcels=2, parcel_area=5000)
    report = gis.full_property_lookup(zone=51, street=835, building=17,
                                       include_imagery=False)
    extent_total = report.extent.total_area_m2
    check(f"T1a: extent total < 15K — got {extent_total:.0f}",
          extent_total < 15000)
    check(f"T1b: classification stays compound_small — got {report.classification.asset_type.value}",
          report.classification.asset_type == AssetType.COMPOUND_SMALL)
    # T1c: the no-promotion invariant is "Patch A did not mutate to
    # compound_large". (extent.asset_type may already be a non-COMPOUND value
    # from detect_extent's geometry-only classify_asset re-call — a pre-
    # existing inconsistency unrelated to this Sprint.)
    check(f"T1c: extent.asset_type was NOT promoted to compound_large — got {report.extent.asset_type.value}",
          report.extent.asset_type != AssetType.COMPOUND_LARGE)


# ====================================================================
# T2 — Patch A: compound_small 15K-50K is PROMOTED to compound_large
# ====================================================================

def test_02_compound_small_15k_to_50k_promoted():
    """Seed=900 + neighbours totaling 18,000 → extent = 18,900 ≥ 15,000.
    Must promote to COMPOUND_LARGE."""
    # 4 parcels × 5000 = 20,000 m² (in 15K-50K band → promote)
    gis = _make_gis_for_compound(seed_pin=2000, n_parcels=4, parcel_area=5000)
    report = gis.full_property_lookup(zone=51, street=835, building=17,
                                       include_imagery=False)
    extent_total = report.extent.total_area_m2
    check(f"T2a: extent total in 15K-50K band — got {extent_total:.0f}",
          15000 <= extent_total < 50000)
    check(f"T2b: classification PROMOTED to compound_large — got {report.classification.asset_type.value}",
          report.classification.asset_type == AssetType.COMPOUND_LARGE)
    check(f"T2c: extent.asset_type PROMOTED to compound_large",
          report.extent.asset_type == AssetType.COMPOUND_LARGE)
    check(f"T2d: classification.confidence downgraded to medium",
          report.classification.confidence == 'medium')
    has_promo = any('Sprint 2.18.1.1' in r for r in report.classification.reasons)
    check(f"T2e: promotion note in classification.reasons",
          has_promo)
    has_extent_note = any('Sprint 2.18.1.1' in n for n in report.extent.notes)
    check(f"T2f: promotion note in extent.notes",
          has_extent_note)


# ====================================================================
# T3 — Patch A: compound_small >50K is also PROMOTED (the 51/835/17 case)
# ====================================================================

def test_03_compound_small_over_50k_promoted():
    """Seed=900 + neighbours totaling ~67,000 → extent = ~67,900 m² (matches
    51/835/17 dimensions). Must promote to COMPOUND_LARGE."""
    # 14 parcels × 5000 = 70,000 m² (mimics 51/835/17's 67,536 m²)
    gis = _make_gis_for_compound(seed_pin=3000, n_parcels=14, parcel_area=5000)
    report = gis.full_property_lookup(zone=51, street=835, building=17,
                                       include_imagery=False)
    extent_total = report.extent.total_area_m2
    check(f"T3a: extent total >> 50K (mimics 51/835/17) — got {extent_total:.0f}",
          extent_total >= 50000)
    check(f"T3b: classification PROMOTED to compound_large",
          report.classification.asset_type == AssetType.COMPOUND_LARGE)
    check(f"T3c: extent.asset_type PROMOTED to compound_large",
          report.extent.asset_type == AssetType.COMPOUND_LARGE)


# ====================================================================
# T4 — Patch C: land > valuation → return None (the trigger pattern)
# ====================================================================

def test_04_decompose_value_land_exceeds_returns_none():
    """The exact pattern from 51/835/17 bug:
      plot=67536, land_per_m2=3229, valuation=6_800_000
      → land_value = 218,073,744 > 6,800,000 → must return None.
    Patch C catches this even if Patch A misses (belt-and-suspenders)."""
    moj_ref = {
        'categories': {
            'land': {
                'price_per_m2': {'median': 3229.0},
                'n': 80,
                'window_months': 24,
                'reliable': True,
            }
        }
    }
    result = _decompose_value(
        valuation_amount=6_800_000,
        plot_area_m2=67536.0,
        bua_m2=None,
        moj_ref_dict=moj_ref,
    )
    check(f"T4: 51/835/17 silent-failure pattern returns None — got {type(result).__name__}",
          result is None)


# ====================================================================
# T5 — Patch C control: normal villa decomposition is UNCHANGED
# ====================================================================

def test_05_decompose_value_normal_unchanged():
    """Normal villa: 600 m² plot, 3,000 QAR/m² land, 5M valuation.
      land = 600 × 3,000 = 1.8M
      valuation = 5M
      building_implied = 5M - 1.8M = 3.2M (positive)
    Must return a normal decomposition dict (not None)."""
    moj_ref = {
        'categories': {
            'land': {
                'price_per_m2': {'median': 3000.0},
                'n': 50,
                'window_months': 24,
                'reliable': True,
            }
        }
    }
    result = _decompose_value(
        valuation_amount=5_000_000,
        plot_area_m2=600.0,
        bua_m2=400.0,
        moj_ref_dict=moj_ref,
    )
    check(f"T5a: normal case returns dict (not None) — got {type(result).__name__}",
          isinstance(result, dict))
    if isinstance(result, dict):
        check(f"T5b: dict has land + building_implied keys",
              'land' in result and 'building_implied' in result)
        bld = result.get('building_implied', {})
        check(f"T5c: building_implied is positive — qar={bld.get('qar')}",
              bld.get('qar') is not None and bld.get('qar') > 0)


# ====================================================================
# T6 — Patch C universal: premium-land villa teardown candidate (Lusail
#       hypothetical per Anas's scope decision #4)
# ====================================================================

def test_06_premium_land_villa_teardown_returns_none():
    """Hypothetical: 200 m² villa on Lusail premium land (~7K QAR/m²),
    old building, as-built valuation 1.0M (the building is teardown).
      land = 200 × 7000 = 1,400,000
      valuation = 1,000,000
      → land > valuation → Patch C returns None.
    Confirms Patch C is universal (not compound-specific) per scope #4."""
    moj_ref = {
        'categories': {
            'land': {
                'price_per_m2': {'median': 7000.0},
                'n': 25,
                'window_months': 24,
                'reliable': True,
            }
        }
    }
    result = _decompose_value(
        valuation_amount=1_000_000,
        plot_area_m2=200.0,
        bua_m2=180.0,
        moj_ref_dict=moj_ref,
    )
    check(f"T6: Lusail premium-land teardown returns None (universal Patch C)",
          result is None)


# ====================================================================
# T7 — Patch C: exact-equal case (boundary condition — should NOT refuse)
# ====================================================================

def test_07_decompose_value_boundary_land_equals_valuation():
    """Boundary: land_value == valuation_amount exactly.
      bld_implied = 0 → not negative → existing logic handles it.
    Patch C uses `>` (strict), so equal case proceeds normally."""
    moj_ref = {
        'categories': {
            'land': {
                'price_per_m2': {'median': 5000.0},
                'n': 30,
                'window_months': 24,
                'reliable': True,
            }
        }
    }
    # plot 200 * 5000 = 1,000,000 = valuation exactly
    result = _decompose_value(
        valuation_amount=1_000_000,
        plot_area_m2=200.0,
        bua_m2=180.0,
        moj_ref_dict=moj_ref,
    )
    check(f"T7a: equal land == valuation does NOT trigger Patch C (returns dict)",
          isinstance(result, dict))
    if isinstance(result, dict):
        bld = result.get('building_implied', {})
        # bld_implied should be 0 → status likely 'land_dominant' (< 5%)
        check(f"T7b: building_implied is 0 — qar={bld.get('qar')}",
              bld.get('qar') == 0)


# ====================================================================
# Runner
# ====================================================================

def main():
    print("\n=== Sprint 2.18.1.1 — Compound-misroute fix (Patches A + C) ===\n")
    for fn in [
        test_01_compound_small_under_15k_unchanged,
        test_02_compound_small_15k_to_50k_promoted,
        test_03_compound_small_over_50k_promoted,
        test_04_decompose_value_land_exceeds_returns_none,
        test_05_decompose_value_normal_unchanged,
        test_06_premium_land_villa_teardown_returns_none,
        test_07_decompose_value_boundary_land_equals_valuation,
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
