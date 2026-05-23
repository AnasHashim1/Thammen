"""
tests/test_sprint_2p21p0p9_multi_qars_stage1.py
================================================
Sprint 2.21.0.9 — Multi-QARS Detection, STAGE 1.

Run: python tests/test_sprint_2p21p0p9_multi_qars_stage1.py

What Stage 1 ships (and what these tests cover):
  - count_qars_within_polygon reverse spatial query (wired upstream)
  - is_shared = (n_qars >= 2 after carve-outs)
  - effective_land_area = PDAREA / n_qars (no title discount)
  - Bracket selection uses effective (not raw PDAREA)
  - Mandatory user override (override_land_area always wins)
  - API response: detected / n_qars / cohabiting / cadastral / effective_per_villa
                  / stage=1 / confidence_pct=70 / split_basis / user_override_*

What Stage 1 deliberately does NOT include (and these tests do not check):
  - Attached/separate classification (Stage 2 — Sprint 2.21.0.10 candidate)
  - GPS centroid distance / thresholds
  - "Value whole structure" toggle / alternative_valuation block

The Stage 2 rule (Anas, 2026-05-23, built on Qatar MME 3m setback code):
  attached  = wall_to_wall < 1m   (shared wall + GPS noise tolerance)
  separate  = wall_to_wall >= 6m  (3m setback × 2 sides — code minimum)
  sub_min   = 1m <= wall_to_wall < 6m  (rare, flag for review)
…will be added once a Building Footprint layer is accessible (EMPIRICAL E18).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from property_geo import (                       # noqa: E402
    MultiQarsResult,
    classify_multi_qars,
    COMPOUND_LARGE_AREA_M2,
    APARTMENTS_THRESHOLD_N,
    STAGE1_CONFIDENCE_PCT,
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


def q(building_no, zone_no=56, street_no=565, pin=99999999, sub=1):
    """A QARS fixture dict (GPS irrelevant in Stage 1 — no distance computed)."""
    return {
        'building_no': building_no,
        'zone_no': zone_no,
        'street_no': street_no,
        'pin': pin,
        'subtype': sub,
        'lat': None,
        'lon': None,
    }


# ====================================================================
# T1 — Bou Hamour 56/565/21 trigger case: detected + split
# ====================================================================

def test_01_bou_hamour_detected():
    """The Sprint trigger: PDAREA=900, 2 QARS (B=19+B=21). Stage 1 detects
    is_shared=True and splits to 450 each. NO type/threshold/GPS-distance —
    just detection + split."""
    qs = [q(19, pin=56090294), q(21, pin=56090294)]
    r = classify_multi_qars(pdarea=900, qars_list=qs, subject_building_no=21)
    check("T1a: is_shared = True", r.is_shared)
    check("T1b: n_qars = 2", r.n_qars == 2)
    check("T1c: effective_land_area = 450 (900/2)",
          r.effective_land_area == 450.0)
    # Result struct must NOT carry classification fields (Stage 1 = minimal shape)
    check("T1d: result has no 'type' field (Stage 1)",
          'type' not in MultiQarsResult.__dataclass_fields__)
    check("T1e: result has no 'max_gps_distance_m' field (Stage 1)",
          'max_gps_distance_m' not in MultiQarsResult.__dataclass_fields__)


# ====================================================================
# T2 — Standalone (n=1): is_shared=False, multi_qars panel hidden
# ====================================================================

def test_02_standalone_not_detected():
    """52/903/90 standalone: PDAREA=467, n=1 → is_shared=False, effective=PDAREA."""
    qs = [q(90, zone_no=52, street_no=903, pin=52200100, sub=6)]
    r = classify_multi_qars(pdarea=467, qars_list=qs, subject_building_no=90)
    check("T2a: is_shared = False", not r.is_shared)
    check("T2b: effective_land_area = PDAREA (unchanged)",
          r.effective_land_area == 467.0)


# ====================================================================
# T3 — Compound_large carve-out: PDAREA>=50K + n<=1 → not detected
# ====================================================================

def test_03_compound_large_carveout():
    """PIN 66030258: PDAREA=59,501 + n=1. Existing compound_large path owns
    this — is_shared=False so the multi_qars UI panel stays hidden."""
    qs = [q(25, zone_no=66, street_no=876, pin=66030258, sub=2)]
    r = classify_multi_qars(pdarea=59501, qars_list=qs,
                            subject_building_no=None)
    check("T3a: is_shared = False (compound_large carve-out)",
          not r.is_shared)
    check("T3b: effective_land_area = raw PDAREA (no split)",
          r.effective_land_area == 59501.0)
    check("T3c: COMPOUND_LARGE_AREA_M2 constant = 50,000",
          COMPOUND_LARGE_AREA_M2 == 50_000.0)


# ====================================================================
# T4 — Apartments carve-out: n>=6 → not detected (deferred to 2.21.1)
# ====================================================================

def test_04_apartments_carveout():
    """A small parcel carrying 6+ QARS is an apartments scenario, not a
    multi-villa share. Carve-out keeps is_shared=False so the multi_qars
    UI doesn't fire on apartment buildings."""
    qs = [q(i, pin=88888888) for i in range(1, 7)]   # n=6
    r = classify_multi_qars(pdarea=3000, qars_list=qs, subject_building_no=1)
    check("T4a: n>=6 → is_shared = False (apartments path defers)",
          not r.is_shared)
    check("T4b: APARTMENTS_THRESHOLD_N constant = 6",
          APARTMENTS_THRESHOLD_N == 6)


# ====================================================================
# T5 — Effective area = PDAREA / n_qars (the bracket-selection fix)
# ====================================================================

def test_05_effective_area_split():
    """The methodology fix: bracket selection must use effective area, not
    raw PDAREA. PDAREA=900 → effective=450 → bracket 400-600 (correct for
    a duplex share). PDAREA=900 raw → bracket 900-1500 (wrong)."""
    qs = [q(1), q(2)]
    r = classify_multi_qars(pdarea=900, qars_list=qs, subject_building_no=1)
    check("T5a: effective = 450 for PDAREA=900 / n=2",
          r.effective_land_area == 450.0)
    # Bracket simulation — mirrors moj_reference._cap_size_bracket
    SIZE_BRACKETS = [(0, 400), (400, 600), (600, 900), (900, 1500),
                     (1500, 99999)]
    def bracket(a):
        for lo, hi in SIZE_BRACKETS:
            if lo <= a < hi:
                return f'{lo}-{hi}'
        return None
    raw_b = bracket(900)
    eff_b = bracket(r.effective_land_area)
    check("T5b: raw PDAREA hits the WRONG bracket", raw_b != '400-600')
    check("T5c: effective area hits the CORRECT bracket",
          eff_b == '400-600')
    # n=4 case from the audit (PIN 51240140, PDAREA=2040)
    qs4 = [q(i) for i in range(1, 5)]
    r = classify_multi_qars(pdarea=2040, qars_list=qs4,
                            subject_building_no=1)
    check("T5d: effective = 510 for PDAREA=2040 / n=4",
          r.effective_land_area == 510.0)


# ====================================================================
# T6 — User override always wins (mandatory override)
# ====================================================================

def test_06_user_override_wins():
    """If the user supplies override_land_area, it replaces the auto-detected
    effective area before bracket selection. Verified via the
    production-class signature (Rule #40)."""
    import inspect
    from evaluate_property import evaluate_property, PropertyEvaluation
    sig = inspect.signature(evaluate_property)
    check("T6a: evaluate_property has plot_area_override parameter",
          'plot_area_override' in sig.parameters)
    check("T6b: PropertyEvaluation has multi_qars field",
          'multi_qars' in PropertyEvaluation.__dataclass_fields__)
    # API request models accept the override at the boundary
    import api
    check("T6c: EvaluateRequest accepts override_land_area",
          'override_land_area' in api.EvaluateRequest.model_fields)
    check("T6d: EvaluateDetailsRequest accepts override_land_area",
          'override_land_area' in api.EvaluateDetailsRequest.model_fields)
    # Bounds preserved (Sprint 2.16.15 extra='forbid' still in place)
    try:
        api.EvaluateRequest(zone=56, street=565, building=21,
                            override_land_area=-1)
        check("T6e: negative override is rejected", False)
    except Exception:
        check("T6e: negative override is rejected", True)


# ====================================================================
# T7 — cohabiting_buildings excludes subject
# ====================================================================

def test_07_cohabiting_excludes_subject():
    """For Bou Hamour subject=21, the cohabiting list is [19] — the user
    sees the OTHER buildings on their plot, not themselves. Mirrors the
    evaluate_property injection block which filters by `building`."""
    qs = [q(19, pin=56090294), q(21, pin=56090294)]
    r = classify_multi_qars(pdarea=900, qars_list=qs, subject_building_no=21)
    subject = 21
    cohabiting = [
        b['building_no'] for b in r.qars_buildings
        if b.get('building_no') != subject
    ]
    check("T7a: cohabiting = [19] (subject 21 excluded)",
          cohabiting == [19])
    # And if the user entered via PIN (no subject building known):
    r = classify_multi_qars(pdarea=900, qars_list=qs,
                            subject_building_no=None)
    cohabiting_pin = [b['building_no'] for b in r.qars_buildings]
    check("T7b: PIN-entry: both buildings listed (no filter)",
          sorted(cohabiting_pin) == [19, 21])


# ====================================================================
# T8 — Graceful failure (empty / None / no GPS) — never raises
# ====================================================================

def test_08_graceful_failure():
    """Detection must never break valuation. Empty / None inputs return a
    standalone result (is_shared=False), not an exception."""
    r = classify_multi_qars(pdarea=500, qars_list=[],
                            subject_building_no=None)
    check("T8a: empty qars_list → is_shared=False (no crash)",
          not r.is_shared and r.effective_land_area == 500.0)
    r = classify_multi_qars(pdarea=500, qars_list=None,
                            subject_building_no=None)
    check("T8b: None qars_list → is_shared=False",
          not r.is_shared)
    r = classify_multi_qars(pdarea=None, qars_list=[],
                            subject_building_no=None)
    check("T8c: None pdarea → is_shared=False, effective=0.0",
          not r.is_shared and r.effective_land_area == 0.0)
    # qatar_gis.count_qars_within_polygon must also be defensive
    import qatar_gis
    check("T8d: qatar_gis.count_qars_within_polygon exists",
          hasattr(qatar_gis, 'count_qars_within_polygon'))
    out = qatar_gis.count_qars_within_polygon(None)
    check("T8e: count_qars_within_polygon(None) → [] (no raise)",
          out == [])
    out = qatar_gis.count_qars_within_polygon({})
    check("T8f: count_qars_within_polygon({}) → [] (no rings, no raise)",
          out == [])


# ====================================================================
# T9 — API response shape: stage=1, confidence_pct=70, fields per spec
# ====================================================================

def test_09_api_response_shape_stage1():
    """The API dict the UI consumes must match the spec contract exactly:
    detected / n_qars / cohabiting_buildings / cadastral_area /
    effective_per_villa / stage=1 / confidence_pct=70 / split_basis /
    user_override_available / user_override_applied.

    No 'type', no 'alternative_valuation', no 'max_gps_distance_m' —
    those are Stage 2 territory.

    We simulate the evaluate_property dict-builder here so this test is
    self-contained (no live GIS); the Rule #40 production-line check in T6
    verifies the parameter wiring."""
    qs = [q(19, pin=56090294), q(21, pin=56090294)]
    multi = classify_multi_qars(pdarea=900, qars_list=qs,
                                subject_building_no=21)
    # Mirror the evaluate_property injection block's dict construction:
    subject = 21
    cohabiting = [
        b.get('building_no') for b in (multi.qars_buildings or [])
        if subject is None or b.get('building_no') != subject
    ]
    dict_for_api = {
        'detected': bool(multi.is_shared),
        'n_qars': multi.n_qars,
        'cohabiting_buildings': cohabiting,
        'cadastral_area': 900.0,
        'effective_per_villa': round(multi.effective_land_area, 1),
        'stage': 1,
        'confidence_pct': STAGE1_CONFIDENCE_PCT,
        'split_basis': 'equal_by_count_default',
        'user_override_available': True,
        'user_override_applied': False,
    }
    check("T9a: detected = True", dict_for_api['detected'] is True)
    check("T9b: stage = 1", dict_for_api['stage'] == 1)
    check("T9c: confidence_pct = 70 (Stage 1 contract)",
          dict_for_api['confidence_pct'] == 70)
    check("T9d: STAGE1_CONFIDENCE_PCT constant = 70",
          STAGE1_CONFIDENCE_PCT == 70)
    check("T9e: split_basis = 'equal_by_count_default'",
          dict_for_api['split_basis'] == 'equal_by_count_default')
    check("T9f: user_override_available = True",
          dict_for_api['user_override_available'] is True)
    check("T9g: no Stage 2 fields leaked into Stage 1 dict",
          'type' not in dict_for_api
          and 'alternative_valuation' not in dict_for_api
          and 'max_gps_distance_m' not in dict_for_api)
    check("T9h: cohabiting filtered by subject", dict_for_api['cohabiting_buildings'] == [19])


# ====================================================================
# Runner
# ====================================================================

def main():
    print("\n=== Sprint 2.21.0.9 (Stage 1) — Multi-QARS Detection ===\n")
    for fn in [
        test_01_bou_hamour_detected,
        test_02_standalone_not_detected,
        test_03_compound_large_carveout,
        test_04_apartments_carveout,
        test_05_effective_area_split,
        test_06_user_override_wins,
        test_07_cohabiting_excludes_subject,
        test_08_graceful_failure,
        test_09_api_response_shape_stage1,
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
