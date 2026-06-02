#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_sprint_2p22p0a7_geometric_determinism_logic.py — DETERMINISTIC half of the A14
geometric-determinism split (Sprint 2.22.0a.17 flake-fix, Option 2A).

WHY THE SPLIT (RISK_REGISTER R14 / the a7 flake): the old combined test made ~live GIS calls
PER point; property_factors._query_gis is FAIL-SOFT (returns [] on any transient error), so
under broad-suite network contention one path's _factor_zoning could return None while the
other got the real code → a spurious cur!=early MISMATCH → rc=1 (flake; green on isolated
re-run). That conflated "is the logic deterministic" with "is the network up."

THIS test removes the network: it monkeypatches property_factors._query_gis to replay FROZEN
zoning payloads (captured once → fixtures/geometric_determinism_fixtures.json), then asserts
  (1) determinism: the zoning Factor is BYTE-IDENTICAL across repeated calls on identical input,
  (2) H_A: the PARALLEL analyze_property fan-out's zoning factor == the direct _factor_zoning
      early path (the lever-1 invariant), and
  (3) two FULL passes over all points are byte-identical (the "two runs, same frozen input"),
  (4) each point's parsed code matches its captured golden ZONING.
NO network → always runs → joins the broad suite's clean-pass set. (Live coverage of the HBU +
E7/A11 anchors is preserved by the sibling best-effort live smoke.)

Exercises PRODUCTION code (Rule #40 / E14): property_factors._factor_zoning + .analyze_property
+ the EXACT zoning parse from evaluate_unified.py:3524-3533.
"""
from __future__ import annotations
import json
import os
import sys

import property_factors as pf

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'fixtures', 'geometric_determinism_fixtures.json')

# evaluate_unified.py:3524-3533 — the EXACT current parse of the zoning hint.
_ZCODES = ['R1', 'R2', 'R3', 'C1', 'C2', 'C', 'MU']


def parse_zoning_code(factor_dict):
    if not factor_dict or factor_dict.get('code') != 'zoning':
        return None
    ev = (factor_dict.get('evidence', '') or '') + ' ' + (factor_dict.get('label_ar', '') or '')
    for code in _ZCODES:
        if code in ev:
            return code
    return None


def factor_to_dict(f):
    """Mirror evaluate_property.py:1581-1590 (Factor -> factors_detail dict)."""
    if f is None:
        return None
    return {'code': f.name, 'label_ar': f.label_ar, 'label_en': f.name,
            'direction': f.direction, 'weight': f.weight, 'distance_m': None,
            'evidence': f.detail, 'source': f.source}


def current_parse(lat, lon):
    """'current' path: zoning code from the REAL parallel analyze_property fan-out."""
    rep = pf.analyze_property(lat=lat, lon=lon, purpose='residential')
    zf = next((f for f in rep.factors if getattr(f, 'name', None) == 'zoning'), None)
    return parse_zoning_code(factor_to_dict(zf))


def early_fetch(lat, lon):
    """lever-1 early path: zoning from a direct _factor_zoning call. Returns (code, factor_dict)."""
    fd = factor_to_dict(pf._factor_zoning(lat, lon, 'residential'))
    return parse_zoning_code(fd), fd


# ── frozen-GIS mock: zoning layer → frozen features (fresh copy); every other layer → [] ──
_FROZEN = {'features': []}


def _mock_query_gis(layer_url, params, timeout=None):
    if layer_url == pf.LAYER_URLS['zoning']:
        return [dict(x) for x in _FROZEN['features']]
    return []


def _golden_code(token):
    """Parse a raw ZONING token (e.g. 'R1-TYP'/'CCC'/'OSR') through the same parser."""
    if not token:
        return None
    return parse_zoning_code({'code': 'zoning', 'evidence': '', 'label_ar': f'تنظيم {token}'})


def _full_pass(fixtures):
    """Snapshot label -> (cur, e1, e2, factordict_json) for ALL points, frozen GIS."""
    snap = {}
    for label in sorted(fixtures):
        fx = fixtures[label]
        _FROZEN['features'] = fx['zoning_features']
        cur = current_parse(fx['lat'], fx['lon'])
        e1, fd1 = early_fetch(fx['lat'], fx['lon'])
        e2, fd2 = early_fetch(fx['lat'], fx['lon'])
        snap[label] = (cur, e1, e2,
                       json.dumps(fd1, sort_keys=True, ensure_ascii=False),
                       json.dumps(fd2, sort_keys=True, ensure_ascii=False))
    return snap


def run():
    with open(FIX, encoding='utf-8') as fh:
        fixtures = json.load(fh)

    real = pf._query_gis
    pf._query_gis = _mock_query_gis
    passed = failed = 0
    bad = []
    try:
        snapA = _full_pass(fixtures)
        snapB = _full_pass(fixtures)
        for label in sorted(fixtures):
            cur, e1, e2, fd1, fd2 = snapA[label]
            golden = _golden_code(fixtures[label].get('golden_zoning'))
            det_ok = (e1 == e2) and (fd1 == fd2)          # determinism of the source
            ha_ok = (cur == e1)                            # parallel fan-out == direct early
            gold_ok = (e1 == golden)                       # fixture-vs-reality
            run2_ok = (snapA[label] == snapB[label])       # two full runs identical
            ok = det_ok and ha_ok and gold_ok and run2_ok
            print(f"  [{'PASS' if ok else 'FAIL'}] {label}: cur={cur} e1={e1} e2={e2} "
                  f"golden={fixtures[label].get('golden_zoning')}→{golden} "
                  f"(det={det_ok} H_A={ha_ok} gold={gold_ok} run2={run2_ok})")
            passed += int(ok)
            failed += int(not ok)
            if not ok:
                bad.append(label)
    finally:
        pf._query_gis = real

    print(f"\n  fixture points: {len(fixtures)} | frozen GIS (NO network) | two full passes")
    print(f"  {passed}/{passed + failed} passed, {failed} failed")
    if failed:
        print(f"  FAIL — zoning-resolution determinism / H_A broke on FROZEN input: {bad}")
        print("         (a real logic-nondeterminism — NOT a network flake; this test has no network.)")
        return 1
    print("  PASS — zoning resolution byte-identical across two runs on identical frozen GIS;")
    print("         parallel fan-out zoning factor == direct early path (H_A); every point == golden.")
    return 0


if __name__ == '__main__':
    sys.exit(run())
