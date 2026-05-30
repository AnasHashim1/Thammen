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

# LIVE HBU-positive point found via probe_find_hbu_positive.py (2026-05-30): an R2
# parcel adjacent to higher-density R3 → analyze_adjacent_zoning returns
# hbu_potential=True on LIVE Qatar GIS. Closes the Session_Log §20.4 CAVEAT (the
# Phase-0 HBU-positive case was synthetic). services.gisqatar.org.qa, central Doha.
LIVE_HBU_POSITIVE = (25.320057, 51.483856, "R2")   # (lat, lon, subject_zone)

# Lever-3 (Sprint 2.22.0a.6 seed get_plot dedup) determinism PINs: a single-parcel
# villa (no expansion) + a multi-parcel compound (real BFS). The gate asserts
#   detect_extent(pin)  [old: re-fetches its own seed]
#     == detect_extent(pin, seed_plot=get_plot(pin))  [new: reuses prefetched]
LEVER3_PINS = [
    ("villa seed · single-parcel", 56090294),
    ("compound seed · multi-parcel BFS", 51500109),
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


def live_hbu_positive_confirm():
    """Closes the §20.4 CAVEAT: confirm the with-hint vs no-hint divergence on a
    REAL HBU-positive Qatar-GIS point (not a mock). lat/lon from
    probe_find_hbu_positive.py."""
    lat, lon, subj = LIVE_HBU_POSITIVE
    print("\n── LIVE HBU-positive (real GIS) · confirms lever-1 finding on real data ──")
    try:
        wh = gf.analyze_geometric_factors(1, lat, lon, subj)
        nh = gf.analyze_geometric_factors(1, lat, lon, None)
    except Exception as e:
        print(f"   [net-fail] {lat},{lon}: {e}")
        print("   [note] live HBU-positive NOT confirmed this run (Rule #36); "
              "Layer 1 synthetic proof + the structural line-611 gate still stand.")
        return None
    raw_equal = _canon(wh) == _canon(nh)
    uf_equal = _canon(user_facing_hbu_analysis(wh)) == _canon(user_facing_hbu_analysis(nh))
    print(f"   point=({lat},{lon}) subject_zone='{subj}'  "
          f"hbu_potential(with-hint)={wh.get('hbu', {}).get('hbu_potential')}")
    print(f"   RAW identical={raw_equal}  user-facing hbu_analysis identical={uf_equal}  "
          f"(with-hint hbu key={'hbu' in wh}, no-hint hbu key={'hbu' in nh})")
    if not uf_equal:
        print("   ⟹ LIVE proof: the hint-removal drops user-facing hbu_analysis on a "
              "REAL HBU-positive property. §20.4 CAVEAT closed.")
    return uf_equal


def _canon_extent(extent):
    """Canonical JSON of an AssetExtent (dataclass → dict; enums/objects → str)."""
    if extent is None:
        return "None"
    from dataclasses import asdict, is_dataclass
    obj = asdict(extent) if is_dataclass(extent) else extent
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)


def layer3_lever3_dedup():
    """ACTIVE SPRINT GATE (2.22.0a.6): prove the seed get_plot dedup is byte-identical.
    detect_extent(pin) [old: re-fetches seed] must equal
    detect_extent(pin, seed_plot=get_plot(pin)) [new: reuses prefetched]."""
    print("\n" + "=" * 72)
    print("LEVER-3 GATE (seed get_plot dedup) — ACTIVE this sprint (2.22.0a.6)")
    print("=" * 72)
    try:
        from qatar_gis import QatarGIS
        gis = QatarGIS(verbose=False)
    except Exception as e:
        print(f"   [import-fail] {e}")
        return None
    results = []
    for label, pin in LEVER3_PINS:
        try:
            plot = gis.get_plot(pin)
            if plot is None:
                print(f"   [skip] {label} (PIN {pin}): get_plot → None")
                continue
            # determinism floor: is get_plot itself stable for this pin?
            plot2 = gis.get_plot(pin)
            getplot_stable = _canon_extent(plot) == _canon_extent(plot2)
            old = gis.detect_extent(pin)                     # OLD path (re-fetch seed)
            new = gis.detect_extent(pin, seed_plot=plot)     # NEW path (reuse prefetched)
        except Exception as e:
            print(f"   [net-fail] {label} (PIN {pin}): {type(e).__name__}: {e}")
            continue
        equal = _canon_extent(old) == _canon_extent(new)
        results.append(equal)
        at = getattr(getattr(old, 'asset_type', None), 'value', None)
        npins = len(getattr(old, 'included_pins', []) or [])
        print(f"   {label} (PIN {pin}): byte-identical={equal}  "
              f"[asset_type={at}, included_pins={npins}, get_plot_stable={getplot_stable}]")
        if not equal:
            print(f"      ⚠ DIVERGENCE — old vs new detect_extent differ. If "
                  f"get_plot_stable=False this is pre-existing GIS nondeterminism, "
                  f"NOT the dedup; else investigate the dedup.")
    if not results:
        print("   [note] no PIN exercised (GIS unreachable) → lever-3 gate INCONCLUSIVE "
              "(Rule #36).")
        return None
    return all(results)


def main():
    print("=" * 72)
    print("Branch B determinism harness")
    print("  Gate 1 (lever-1, geometric overlap): DOCUMENTED Gate-2 finding (§20.4)")
    print("  Gate 2 (lever-3, seed get_plot dedup): ACTIVE sprint 2.22.0a.6")
    print("=" * 72)

    # ── LEVER-1 hint-removal (documented Gate-2 finding; NOT implemented this sprint) ──
    print("\n#### LEVER-1 hint-removal (informational — geometric overlap is Gate-2) ####")
    rawA, ufA = layer1_case("HBU-POSITIVE (synthetic stub)", _HBU_POSITIVE)
    rawB, ufB = layer1_case("HBU-NEGATIVE (R1-in-R1, like the anchors)", _HBU_NEGATIVE)
    layer2_live()
    live_uf = live_hbu_positive_confirm()
    lever1_invariant = bool(rawA and rawB and ufA and ufB)

    # ── LEVER-3 dedup (the gate that governs THIS sprint's commit) ──
    lever3 = layer3_lever3_dedup()

    print("\n" + "=" * 72)
    print("VERDICT")
    print("=" * 72)
    print(f"  LEVER-1 (geometric overlap) hint-invariant : "
          f"{'YES' if lever1_invariant else 'NO — diverges on HBU-positive (Gate-2, §20.4)'}")
    if live_uf is False:
        print("      └ confirmed LIVE on a real HBU-positive property (CAVEAT closed)")
    elif live_uf is None:
        print("      └ live HBU-positive NOT confirmed this run (synthetic proof stands)")
    print(f"  LEVER-3 (seed dedup) byte-identical        : "
          f"{'YES' if lever3 else ('INCONCLUSIVE' if lever3 is None else 'NO — DIVERGES')}")

    print()
    # Exit code is governed by the ACTIVE sprint gate (lever 3). Lever-1's
    # divergence is the already-documented Gate-2 finding, not a sprint blocker.
    if lever3 is True:
        print("  ACTIVE GATE (lever-3): PASS — seed dedup is byte-identical. "
              "Proceed to regression + commit.")
        return 0
    if lever3 is None:
        print("  ACTIVE GATE (lever-3): INCONCLUSIVE — GIS unreachable. Re-run where "
              "GIS is reachable before commit (Rule #36).")
        return 2
    print("  ACTIVE GATE (lever-3): FAIL — seed dedup changed detect_extent output. "
          "ROLLBACK the dedup (Rule #11). Do NOT commit.")
    return 1


if __name__ == '__main__':
    sys.exit(main())
