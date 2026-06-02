#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_sprint_2p22p0a7_geometric_determinism_live_smoke.py — LIVE best-effort half of the A14
geometric-determinism split (Sprint 2.22.0a.17 flake-fix, Option 2B).

Preserves the §20.7 LIVE-coverage intent (HBU + E7/A11 anchors against real GIS) WITHOUT the
flake. property_factors._query_gis is FAIL-SOFT ([] on transient error), so:
  - a None on any side  -> transient miss -> SKIP that point (never a failure),
  - a cur!=early mismatch -> RE-CONFIRM with one re-fetch before believing it.
Contract (standalone exit-code convention, like the original test):
  - persistent, re-confirmed cur!=early or e1!=e2 (real codes both sides) -> FAIL (exit 1),
  - transient ([]/None/mismatch that clears on re-fetch)                   -> skip the point,
  - too few points resolved live / E7 anchor unreachable (GIS-limited)     -> SKIP (exit 0),
  - resolved sample holds incl. the E7/A11 anchor                          -> PASS (exit 0).
The DETERMINISM guarantee lives in the sibling ..._logic.py (frozen, always runs). This is the
canary that live GIS still agrees with the frozen reality; it must NEVER break the broad suite
on network variance — only on a genuine, reproducible divergence.
"""
from __future__ import annotations
import sys

import property_factors as pf

_ZCODES = ['R1', 'R2', 'R3', 'C1', 'C2', 'C', 'MU']


def parse_zoning_code(fd):
    if not fd or fd.get('code') != 'zoning':
        return None
    s = (fd.get('evidence', '') or '') + ' ' + (fd.get('label_ar', '') or '')
    for c in _ZCODES:
        if c in s:
            return c
    return None


def factor_to_dict(f):
    if f is None:
        return None
    return {'code': f.name, 'label_ar': f.label_ar, 'evidence': f.detail}


def current_parse(lat, lon):
    rep = pf.analyze_property(lat=lat, lon=lon, purpose='residential')
    zf = next((f for f in rep.factors if getattr(f, 'name', None) == 'zoning'), None)
    return parse_zoning_code(factor_to_dict(zf))


def early_fetch(lat, lon):
    return parse_zoning_code(factor_to_dict(pf._factor_zoning(lat, lon, 'residential')))


def confirm(lat, lon):
    """(cur, e1, e2) live — current parallel-fan-out zoning vs the direct early path (×2)."""
    return current_parse(lat, lon), early_fetch(lat, lon), early_fetch(lat, lon)


# Permanent anchors (§20.7): an HBU-positive case AND the E7/A11 stale-subtype-vs-zoning case.
POINTS = [
    ('E7/A11 CCC (61/875/20 Public Works)', 25.32070,  51.53189, True),
    ('HBU-positive R2/R3',                   25.320057, 51.483856, True),
    ('spread central',                       25.30000,  51.50000, False),
    ('spread SW',                            25.26000,  51.47000, False),
]


def main():
    print("=" * 74)
    print("A14 LIVE-GIS smoke (best-effort, skip-safe) — zoning/geometric determinism canary")
    print("=" * 74)
    resolved = 0
    e7_held = None
    real_fail = []
    for label, lat, lon, is_anchor in POINTS:
        try:
            cur, e1, e2 = confirm(lat, lon)
        except Exception as ex:
            print(f"  [net-fail]    {label}: {type(ex).__name__}")
            continue
        if None in (cur, e1, e2):
            print(f"  [skip-point]  {label}: transient empty (cur={cur} e1={e1} e2={e2})")
            continue
        if (cur != e1) or (e1 != e2):
            # re-confirm before believing a divergence (kills the fail-soft [] flake)
            try:
                cur2, r1, r2 = confirm(lat, lon)
            except Exception:
                print(f"  [skip-point]  {label}: mismatch + re-fetch net-failed")
                continue
            if None in (cur2, r1, r2):
                print(f"  [skip-point]  {label}: mismatch + re-fetch transient-empty")
                continue
            if (cur2 != r1) or (r1 != r2):
                real_fail.append((label, cur2, r1, r2))
                print(f"  [FAIL]        {label}: PERSISTENT cur={cur2} e1={r1} e2={r2}")
                continue
            print(f"  [cleared]     {label}: first read disagreed, re-fetch agrees ({r1})")
            cur, e1, e2 = cur2, r1, r2
        resolved += 1
        if is_anchor and 'E7' in label:
            e7_held = True
        print(f"  [ok]          {label}: cur={cur} e1={e1} e2={e2}")

    print("\n" + "=" * 74)
    print(f"  resolved live points : {resolved}")
    print(f"  E7/A11 anchor        : {'HELD' if e7_held else 'unreachable'}")
    print(f"  persistent real fails: {len(real_fail)}")
    if real_fail:
        print("  FAIL — live cur!=early PERSISTED across a re-fetch (real divergence, not transient).")
        return 1
    if resolved < 2 or e7_held is not True:
        print("  SKIPPED — GIS-limited this run (resolved<2 / E7 anchor unreachable). Offline-safe.")
        return 0
    print("  PASS — live GIS agrees (cur==early==stable) across the resolved sample incl. E7/A11.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
