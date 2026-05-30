#!/usr/bin/env python3
"""
test_sprint_2p22p0a7_geometric_determinism.py — Sprint A14.

DUAL ROLE:
  (1) the H_A GATE that was run BEFORE deciding lever 1 (early-fetched zoning == current
      factors_detail parse), and
  (2) PERMANENT regression test (promoted per Anas): any HBU-path / zoning-resolution change
      MUST keep this green — it deliberately retains an HBU-positive AND an E7/A11 anchor
      (HBU-negative R1-in-R1 anchors are blind to the HBU defect — Branch B finding).
Offline-safe: SKIPs (exit 0) when Qatar GIS is unreachable; FAILs (exit 1) only on a real
determinism divergence; PASSes (exit 0) when early==current across the sample.

LEVER 1 = compose geometric_factors concurrently with zoning resolution. It needs the
subject zoning code EARLY (before the valuation's factors_detail exists). H_A decides
whether that is perf-only:

  H_A: the zoning code as lever 1 would EARLY-fetch it == the zoning code currently parsed
       from `ev.valuation.factors_detail` at the same (lat,lon), for EVERY sampled property
       — INCLUDING HBU-positive cases (commercial / mixed-use neighbours). The 4 R1-in-R1
       anchors are blind to the HBU defect (Branch B finding) → the sample is built to span
       commercial / MU / higher-density zoning deliberately.

  ALL equal  -> H_A HOLDS  -> lever 1 is perf-only -> implement.
  ANY differ -> H_A FALSIFIED -> STOP lever 1 (Gate 2) -> ship lever 2 only, return to Anas.

Exercises PRODUCTION code (Rule #40 / E14 — not an echo):
  - "current" = parse the zoning Factor produced by the REAL `property_factors.analyze_property`
    fan-out (this IS what becomes factors_detail['zoning']), via the EXACT parse from
    evaluate_unified.py:3524-3533.
  - "early"   = parse `property_factors._factor_zoning(lat,lon,'residential')` called DIRECTLY
    (lever 1's intended early path), via the same parse.
Also re-runs the early fetch a 2nd time to confirm the source is deterministic for a given pin.
"""
from __future__ import annotations
import json
import sys

import geometric_factors as gf
import property_factors as pf

# evaluate_unified.py:3524-3533 — the EXACT current parse of the zoning hint.
_ZCODES = ['R1', 'R2', 'R3', 'C1', 'C2', 'C', 'MU']

def parse_zoning_code(factor_dict) -> str | None:
    if not factor_dict or factor_dict.get('code') != 'zoning':
        return None
    ev_str = (factor_dict.get('evidence', '') or '') + ' ' + (factor_dict.get('label_ar', '') or '')
    for code in _ZCODES:
        if code in ev_str:
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
    """Production 'current' path: zoning code as derived from the real analyze_property fan-out."""
    rep = pf.analyze_property(lat=lat, lon=lon, purpose='residential')
    zf = next((f for f in rep.factors if getattr(f, 'name', None) == 'zoning'), None)
    return parse_zoning_code(factor_to_dict(zf)), (zf.label_ar if zf else None)

def early_fetch(lat, lon):
    """Lever-1 early path: zoning code from a direct _factor_zoning call."""
    f = pf._factor_zoning(lat, lon, 'residential')
    return parse_zoning_code(factor_to_dict(f)), (f.label_ar if f else None)


# ── Permanent anchor points the sample MUST always retain (Anas, Sprint A14 gate) ──
# (label, lat, lon) — kept regardless of the bbox query, so the regression test always
# exercises an HBU-positive case AND an E7/A11 stale-subtype-vs-zoning case.
EXPLICIT_POINTS = [
    ('E7/A11 govt stale-subtype (61/875/20 Public Works, Zoning=CCC)', 25.32070, 51.53189),
    ('HBU-positive R2-adjacent-R3 (probe_find_hbu_positive)',          25.320057, 51.483856),
]

# ── Build a >=20-point sample spanning zoning types incl. commercial / MU (HBU-positive) ──
COMMERCIAL = {'C', 'C1', 'C2', 'CC', 'CR', 'MU', 'M-U', 'CCC', 'COM'}
# Several Doha bboxes to capture mixed R + commercial/MU zoning.
BBOXES = [
    {'xmin': 51.48, 'ymin': 25.26, 'xmax': 51.56, 'ymax': 25.33},   # central
    {'xmin': 51.52, 'ymin': 25.28, 'xmax': 51.58, 'ymax': 25.34},   # West Bay / Dafna
    {'xmin': 51.43, 'ymin': 25.23, 'xmax': 51.52, 'ymax': 25.29},   # SW
]

def _centroid(rings):
    pts = [p for ring in rings for p in ring]
    if not pts:
        return None
    return (sum(p[1] for p in pts)/len(pts), sum(p[0] for p in pts)/len(pts))  # (lat,lon)

def collect_points(target=24):
    by_zone = {}
    for bbox in BBOXES:
        bbox = {**bbox, 'spatialReference': {'wkid': 4326}}
        params = {'geometry': json.dumps(bbox), 'geometryType': 'esriGeometryEnvelope',
                  'inSR': '4326', 'spatialRel': 'esriSpatialRelIntersects', 'where': '1=1',
                  'outFields': 'ZONING', 'returnGeometry': 'true', 'outSR': '4326',
                  'resultRecordCount': '400', 'f': 'json'}
        data = gf._http_get_json(gf.LAYER_URLS['zoning'], params)
        for f in (data or {}).get('features', []):
            z = (f.get('attributes', {}).get('ZONING') or '').strip().upper()
            rings = (f.get('geometry') or {}).get('rings')
            c = _centroid(rings) if rings else None
            if not z or not c:
                continue
            by_zone.setdefault(z, [])
            if len(by_zone[z]) < 4:           # up to 4 per zone for spread
                by_zone[z].append(c)
    # Assemble: prioritise commercial/MU (HBU-positive) + a spread of R-types.
    pts = []
    for z in sorted(by_zone, key=lambda k: (k not in COMMERCIAL, k)):  # commercial first
        for c in by_zone[z]:
            pts.append((z, c[0], c[1]))
    return pts[:max(target, 20)], by_zone


def main():
    print("=" * 74)
    print("Sprint A14 · H_A GATE — early-fetched zoning == current factors_detail parse")
    print("=" * 74)
    pts, by_zone = collect_points()
    commercial_zones = [z for z in by_zone if z in COMMERCIAL]
    print(f"sample n={len(pts)} | distinct subject ZONING tokens={sorted(by_zone)}")
    print(f"HBU-positive (commercial/MU) zones present: {sorted(commercial_zones) or 'NONE'}")
    if len(pts) < 20:
        print(f"\n[WARN] only {len(pts)} points (<20) — widen bboxes (Rule #36).")
    n_commercial_pts = sum(1 for z, _, _ in pts if z in COMMERCIAL)
    print(f"of which HBU-positive subject points: {n_commercial_pts}")

    # explicit anchors (E7 + HBU-positive) ALWAYS first, then the bbox spread
    combined = [(lbl, lat, lon, True) for (lbl, lat, lon) in EXPLICIT_POINTS] \
             + [(z, lat, lon, False) for (z, lat, lon) in pts]
    mism = []
    det_fail = []
    rows = 0
    e7_held = None
    for z, lat, lon, is_anchor in combined:
        try:
            cur, cur_lbl = current_parse(lat, lon)
            e1, e1_lbl = early_fetch(lat, lon)
            e2, _ = early_fetch(lat, lon)
        except Exception as ex:
            print(f"  [net-fail] {z} ({lat:.5f},{lon:.5f}): {type(ex).__name__}")
            continue
        rows += 1
        if e1 != e2:
            det_fail.append((z, lat, lon, e1, e2))
        if cur != e1:
            mism.append((z, lat, lon, cur, e1, cur_lbl, e1_lbl))
        if is_anchor and 'E7' in z:
            e7_held = (cur == e1 and e1 == e2)
        flag = '  <<< MISMATCH' if cur != e1 else ('  <<< NONDET' if e1 != e2 else '')
        prefix = '[ANCHOR] ' if is_anchor else 'ZONING='
        print(f"  {prefix}{z}  ({lat:.5f},{lon:.5f})  current={cur!s:5s} early={e1!s:5s}{flag}")

    print("\n" + "=" * 74)
    print("VERDICT")
    print("=" * 74)
    print(f"  points exercised (live GIS) : {rows}")
    print(f"  HBU-positive points         : {n_commercial_pts}")
    print(f"  E7/A11 stale-subtype anchor : {'HELD' if e7_held else ('FAILED' if e7_held is False else 'not tested')}")
    print(f"  early-fetch non-determinism : {len(det_fail)}")
    print(f"  current-vs-early mismatches : {len(mism)}")
    if mism:
        print("\n  MISMATCH DETAIL (→ H_A FALSIFIED, lever 1 = Gate 2):")
        for z, lat, lon, cur, e, cl, el in mism:
            print(f"    {z} ({lat:.5f},{lon:.5f}): current={cur} ({cl}) vs early={e} ({el})")
    print()
    # Permanent-regression exit contract (Sprint A14 — promoted from the H_A gate):
    #   divergence (mismatch / non-determinism)        -> FAIL (exit 1)  [real defect]
    #   GIS-limited (sample<20 / no HBU / no E7 anchor) -> SKIP (exit 0)  [offline-safe]
    #   all equal incl. HBU-positive + E7              -> PASS (exit 0)
    if mism or det_fail:
        print("  FAIL — early zoning resolution diverges from the current factors_detail")
        print("         parse (determinism break on an HBU-path input). If this fires after")
        print("         a lever-1 / HBU-path change: that change is behaviour-changing (Gate 2).")
        return 1
    if rows < 20 or n_commercial_pts < 1 or e7_held is not True:
        print("  SKIPPED — GIS-limited this run (sample<20 / no HBU-positive / E7 anchor")
        print("            unreachable). Determinism NOT exercised — offline-safe, not a failure.")
        return 0
    print("  PASS — early-fetched zoning == current parse across the sample, INCLUDING the")
    print("         HBU-positive and E7/A11 anchors. The HBU-path zoning resolution is")
    print("         deterministic & mutation-free (H_A invariant holds).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
