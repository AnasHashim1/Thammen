# -*- coding: utf-8 -*-
"""Fixture-capture tool (TRACKED — regenerability for the R14 geometric-determinism split).
On-demand live capture of the zoning GIS payloads that freeze the deterministic-logic test's
fixtures (Sprint 2.22.0a.17 flake-split, Option 2A). Retries past the fail-soft [] in _query_gis
so a transient empty is never frozen. Writes fixtures/geometric_determinism_fixtures.json
(point-query features, attributes only) — re-run from the repo root (deploy v2) to regenerate
after a GIS/zoning schema change; test_sprint_2p22p0a7_geometric_determinism_logic.py reads it.
Run: set PYTHONIOENCODING=utf-8 && python capture_geometric_determinism_fixtures.py"""
import json
import os
import time
import property_factors as pf

ZURL = pf.LAYER_URLS['zoning']


def zquery(lat, lon):
    """The EXACT zoning point query _factor_zoning makes (returnGeometry default false)."""
    return pf._query_gis(ZURL, {
        'geometry': pf._point_geom(lat, lon),
        'geometryType': 'esriGeometryPoint', 'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'ZONING',
    })


def zquery_retry(lat, lon, tries=10):
    for _ in range(tries):
        feats = zquery(lat, lon)
        if feats:
            return feats
        time.sleep(0.6)
    return []


def golden(feats):
    return (feats[0].get('attributes', {}).get('ZONING') if feats else None)


# Required anchors (exercise the determinism-relevant paths — §20.7 intent).
EXPLICIT = [
    ('e7_a11_ccc_61_875_20', 25.32070, 51.53189),    # CCC — E7/A11 stale-subtype-vs-zoning
    ('hbu_r2_adjacent_r3',   25.320057, 51.483856),   # HBU-positive (R2/R3 neighbourhood)
]

BBOXES = [
    {'xmin': 51.48, 'ymin': 25.26, 'xmax': 51.56, 'ymax': 25.33},
    {'xmin': 51.52, 'ymin': 25.28, 'xmax': 51.58, 'ymax': 25.34},
    {'xmin': 51.43, 'ymin': 25.23, 'xmax': 51.52, 'ymax': 25.29},
]


def centroid(rings):
    pts = [p for ring in rings for p in ring]
    if not pts:
        return None
    return (sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts))  # (lat,lon)


def harvest(target_distinct=6):
    """Best-effort: harvest up to N distinct-ZONING centroids for parse-branch breadth."""
    found = {}
    for bbox in BBOXES:
        bbox = {**bbox, 'spatialReference': {'wkid': 4326}}
        params = {'geometry': json.dumps(bbox), 'geometryType': 'esriGeometryEnvelope',
                  'inSR': '4326', 'spatialRel': 'esriSpatialRelIntersects', 'where': '1=1',
                  'outFields': 'ZONING', 'returnGeometry': 'true', 'outSR': '4326',
                  'resultRecordCount': '400', 'f': 'json'}
        feats = pf._query_gis(ZURL, params)
        for f in feats:
            z = (f.get('attributes', {}).get('ZONING') or '').strip().upper()
            rings = (f.get('geometry') or {}).get('rings')
            c = centroid(rings) if rings else None
            if not z or not c or z in found:
                continue
            pq = zquery_retry(c[0], c[1], tries=4)
            if pq and (golden(pq) or '').strip().upper() == z:
                found[z] = (c[0], c[1], pq)
            if len(found) >= target_distinct:
                return found
    return found


def main():
    out = {}
    for label, lat, lon in EXPLICIT:
        feats = zquery_retry(lat, lon, tries=12)
        out[label] = {'lat': lat, 'lon': lon, 'zoning_features': feats, 'golden_zoning': golden(feats)}
        print(f"{label}: golden={golden(feats)} n_feats={len(feats)}")
    for z, (lat, lon, feats) in harvest().items():
        out[f'bbox_{z}'] = {'lat': lat, 'lon': lon, 'zoning_features': feats, 'golden_zoning': z}
        print(f"bbox_{z}: golden={z} n_feats={len(feats)}")
    os.makedirs('fixtures', exist_ok=True)
    path = os.path.join('fixtures', 'geometric_determinism_fixtures.json')
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"\nwrote {path} with {len(out)} points: {list(out)}")
    bad = [k for k, v in out.items() if not v['zoning_features']]
    print(f"EMPTY (bad) points: {bad or 'NONE'}")


if __name__ == '__main__':
    main()
