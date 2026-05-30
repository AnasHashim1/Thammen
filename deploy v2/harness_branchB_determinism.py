#!/usr/bin/env python3
"""
harness_branchB_determinism.py — Branch B (Bug A14 real-fix) determinism harness.

TASK STEP 3 (write the harness FIRST, before any refactor).

Lever 1 (locked scope, BRIEF §8.3): overlap `geometric_factors` (~9s) with the
valuation; leave `geo_v2` sequential. The overlap launches `geometric_factors`
BEFORE the valuation computes the `zoning_code` hint that `geometric` currently
reads from `ev.valuation.factors_detail` (evaluate_unified.py:3524-3535).

BRIEF §8.3 (load-bearing, Anas): that hint is NOT guaranteed equal to a
self-fetched zoning, so the parity test must DIRECTLY assert
    analyze_geometric_factors(with-hint) == analyze_geometric_factors(no-hint)
and NOT merely rely on the 4 anchors happening to match — "a passing anchor set
is insufficient; it can mask a hint-vs-self-zoning divergence on other inputs."

DECISION GATE (task step 3): if the two paths diverge for ANY reachable input,
the naive overlap is a behaviour change → Gate 2 → STOP for Anas sign-off; do
NOT proceed to the refactor (step 4).

Layered per Rule #40 (replica + production):
  - Layer 1 (offline, deterministic): mock the 4 GIS sub-calls so we control the
    HBU outcome and ISOLATE the hint's effect on the output.
  - Layer 2 (live, network-gated): call the REAL analyze_geometric_factors on the
    4 anchors with real zoning vs None, if Qatar GIS is reachable from here.

NOTE: the serial-vs-parallel byte-identical anchor test (SC3) can only run AFTER
the refactor exists; it is intentionally NOT in this file, which is the
pre-refactor GATE. If the gate below fails, the refactor is not reached.
"""
from __future__ import annotations
import copy
import json
import sys

import geometric_factors as gf

ANCHORS = [
    # (label, pin, lat, lon, real_zoning_code_hint)  — the 4 SC3 determinism anchors
    ("villa 56/565/21 (Bou Hamour, multi-QARS)", 56090294, 25.2503, 51.4499, "R1"),
    ("apartment 52/903/90 (اللقطة)",             None,     None,    None,    "R3"),
    ("Lusail 69/329/20 (Fox Hills, T2-only)",    None,     None,    None,    "R3"),
    ("Lusail 69/255/75 (City Avenues, H1)",      None,     None,    None,    "R3"),
]

# ── consumer replica: the ONLY user-facing consumer of geometric['hbu'] ──
# evaluate_unified.py:4428-4438. Returns the hbu_analysis dict the user sees, or
# None when the gate `if hbu.get('hbu_potential') or hbu.get('industrial_adjacency')`
# is False. This is the surface the Gate-2 test ("would the JSON the user sees
# differ?") cares about.
def user_facing_hbu_analysis(geometric: dict):
    hbu = geometric.get('hbu', {}) or {}
    if hbu.get('hbu_potential') or hbu.get('industrial_adjacency'):
        return {
            'potential': hbu.get('hbu_potential', False),
            'industrial_adjacency': hbu.get('industrial_adjacency', False),
            'potential_pct': hbu.get('potential_pct', 0),
            'evidence_ar': hbu.get('evidence_ar'),
            'adjacent_zones': hbu.get('adjacent_zones', []),
        }
    return None


# ── Layer 1 — deterministic offline stubs for the 4 GIS sub-calls ──
_FIXED_POLYGON = {
    'rings': [[[51.5, 25.3], [51.5009, 25.3], [51.5009, 25.3009],
               [51.5, 25.3009], [51.5, 25.3]]],
    'centroid': (25.30045, 51.50045),
    'plot_area_m2': 900.0,
    'pd_no': '0',
}
_FIXED_CORNER = {
    'is_corner': False, 'main_road_adjacent': False,
    'main_streets': [], 'local_streets': [],
    'confidence': 'medium', 'evidence_ar': 'stub-corner',
}
_FIXED_LANDMARKS = {'malls': [], 'metros': [], 'mixed_use_venues': []}

_HBU_POSITIVE = {
    'hbu_potential': True, 'potential_pct': 0.25,
    'evidence_ar': '⚠ تجاري مجاور (C) — إمكانية تعديل رخصة',
    'adjacent_zones': ['C', 'R1'], 'trigger': 'تجاري مجاور (C)',
}
_HBU_NEGATIVE = {
    'hbu_potential': False,
    'evidence_ar': 'القطع المجاورة من نفس التصنيف (R1) — لا إمكانية واضحة',
    'adjacent_zones': ['R1'],
}

_orig = {}
def _install_stubs(hbu_return):
    """Patch the module-level GIS callables analyze_geometric_factors resolves at
    call-time. analyze_adjacent_zoning is only invoked on the WITH-hint path
    (line 611 gates it on `if current_zoning_code:`) — exactly the asymmetry under
    test."""
    if not _orig:
        _orig['fetch_plot_polygon'] = gf.fetch_plot_polygon
        _orig['detect_corner'] = gf.detect_corner
        _orig['find_named_landmarks'] = gf.find_named_landmarks
        _orig['analyze_adjacent_zoning'] = gf.analyze_adjacent_zoning
    gf.fetch_plot_polygon     = lambda pin: copy.deepcopy(_FIXED_POLYGON)
    gf.detect_corner          = lambda polygon, **kw: copy.deepcopy(_FIXED_CORNER)
    gf.find_named_landmarks   = lambda lat, lon, **kw: copy.deepcopy(_FIXED_LANDMARKS)
    gf.analyze_adjacent_zoning = lambda lat, lon, code, **kw: copy.deepcopy(hbu_return)

def _restore_stubs():
    for k, v in _orig.items():
        setattr(gf, k, v)


def _canon(d):
    return json.dumps(d, ensure_ascii=False, sort_keys=True)


def layer1_case(title, hbu_return, hint="R1"):
    _install_stubs(hbu_return)
    try:
        with_hint = gf.analyze_geometric_factors(1, 25.30045, 51.50045, hint)
        no_hint   = gf.analyze_geometric_factors(1, 25.30045, 51.50045, None)
    finally:
        _restore_stubs()

    raw_equal = _canon(with_hint) == _canon(no_hint)
    uf_with = user_facing_hbu_analysis(with_hint)
    uf_no   = user_facing_hbu_analysis(no_hint)
    uf_equal = _canon(uf_with) == _canon(uf_no)

    print(f"\n── Layer 1 · {title} ──")
    print(f"   with-hint('{hint}') has 'hbu' key : {'hbu' in with_hint}")
    print(f"   no-hint(None)   has 'hbu' key      : {'hbu' in no_hint}")
    print(f"   RAW geometric dict identical       : {raw_equal}")
    print(f"   user-facing hbu_analysis (with)    : {('present' if uf_with else 'absent')}")
    print(f"   user-facing hbu_analysis (no-hint) : {('present' if uf_no else 'absent')}")
    print(f"   USER-FACING output identical       : {uf_equal}")
    return raw_equal, uf_equal


def layer2_live():
    print("\n── Layer 2 · LIVE production calls on the 4 anchors (network-gated) ──")
    reachable = None
    for (label, pin, lat, lon, hint) in ANCHORS:
        if pin is None or lat is None or lon is None:
            print(f"   [skip] {label}: pin/lat/lon not pinned in this harness "
                  f"(needs a GIS address→pin resolve; not required for the gate)")
            continue
        try:
            with_hint = gf.analyze_geometric_factors(int(pin), float(lat), float(lon), hint)
            no_hint   = gf.analyze_geometric_factors(int(pin), float(lat), float(lon), None)
            reachable = True
        except Exception as e:
            print(f"   [net-fail] {label}: {e}")
            reachable = False
            continue
        raw_equal = _canon(with_hint) == _canon(no_hint)
        uf_equal = _canon(user_facing_hbu_analysis(with_hint)) == _canon(user_facing_hbu_analysis(no_hint))
        print(f"   {label}")
        print(f"      RAW identical={raw_equal}  user-facing identical={uf_equal}  "
              f"(with-hint hbu key={'hbu' in with_hint}, no-hint hbu key={'hbu' in no_hint})")
    if reachable is None:
        print("   [note] no anchor had pin/lat/lon pinned → Layer 2 not exercised "
              "(Rule #36: live production confirmation NOT obtained this run).")
    elif reachable is False:
        print("   [note] Qatar GIS not reachable from this host → Layer 2 inconclusive "
              "(Rule #36). Layer 1 stands on its own: it isolates the hint's effect.")


def main():
    print("=" * 72)
    print("Branch B determinism harness — hint-removal GATE (task step 3)")
    print("Assertion under test: analyze_geometric_factors(with-hint) == (no-hint)")
    print("=" * 72)

    # Case A: HBU-POSITIVE property (adjacent commercial). This is the case the
    # 4 R1-in-R1 anchors do NOT cover — the brief's "anchors insufficient" point.
    rawA, ufA = layer1_case("HBU-POSITIVE (adjacent commercial 'C')", _HBU_POSITIVE)

    # Case B: HBU-NEGATIVE property (R1 surrounded by R1 — like the anchors).
    rawB, ufB = layer1_case("HBU-NEGATIVE (R1-in-R1, like the anchors)", _HBU_NEGATIVE)

    layer2_live()

    print("\n" + "=" * 72)
    print("VERDICT")
    print("=" * 72)
    print(f"  RAW geometric dict invariant to hint  : "
          f"{'YES' if (rawA and rawB) else 'NO — diverges'}")
    print(f"  USER-FACING output invariant to hint  : "
          f"{'YES' if (ufA and ufB) else 'NO — diverges on HBU-positive'}")
    print(f"  Anchors (HBU-negative) coincidentally  user-facing-match : {ufB}")
    gate_pass = rawA and rawB and ufA and ufB
    print()
    if gate_pass:
        print("  GATE: PASS — hint removal is perf-only. Proceed to refactor (step 4).")
        return 0
    print("  GATE: FAIL — removing the hint changes geometric's output.")
    print("        Naive lever-1 overlap (geometric launched before the valuation")
    print("        produces the zoning_code hint) = behaviour change → 🔴 Gate 2.")
    print("        STOP. Do NOT refactor. Return to Anas sign-off (task step 3).")
    print("        Note: Case B shows the 4 R1-in-R1 anchors coincidentally match")
    print("        at the user-facing surface — exactly why anchors alone are")
    print("        insufficient (BRIEF §8.3).")
    return 1


if __name__ == '__main__':
    sys.exit(main())
