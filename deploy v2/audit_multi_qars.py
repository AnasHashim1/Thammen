"""
Sprint 2.21.0.9 — Phase 1 Empirical Audit
==========================================
Reverse spatial query: for each input PIN/address, find ALL QARS_Point features
within the cadastral polygon, measure pairwise GPS distances, predict the
multi-QARS type {standalone | attached | separate | ambiguous | handled_by_classifier}.

MUST run from Heroku (khazna geo-restricted to QA / Heroku slug).
Standalone — does NOT modify any engine module (Rule #34 file-based).

Reuses qatar_gis._http_get_json so the POST fallback (Rule #48) covers
many-vertex parcel rings transparently.

DEVIATION FROM PLAN (Rule #39 — 3-sentence justification):
- Plan specified `spatialRel=esriSpatialRelContains`.
- This script uses `esriSpatialRelIntersects` to match the production helper
  `_qars_count_in_polygon` (qatar_gis.py:549). Why: production-proven on
  exactly this endpoint; same semantic outcome for point-in-polygon (a QARS
  point either intersects or it doesn't — there is no boundary nuance for
  zero-dimensional features). What is lost: nothing (identical result set).
  What Anas needs to know: this matches the helper Sprint 2.21.0.9 Phase 2
  will extend, so the audit reflects real production behaviour.
"""

import json
import math
import sys
import time

# Reuse the engine's HTTP helper + endpoint registry (Rule #48 POST fallback
# is baked in; no need to reimplement urllib).
from qatar_gis import ENDPOINTS, _http_get_json


# ----------------------------------------------------------------------
# 10-case cohort (per Sprint 2.21.0.9 plan — confirmed by Anas)
# ----------------------------------------------------------------------
# Each entry: (label, kind, params, expected_note)
#   kind = 'address' → resolve via QARS_Point first to get PIN
#   kind = 'pin'     → CadastrePlots directly
COHORT = [
    ('1. 56/565/21 (Bou Hamour)',
     'address', {'zone': 56, 'street': 565, 'building': 21},
     'expect n>=2, shares polygon with B=19'),

    ('2. 56/565/19 (Bou Hamour pair)',
     'address', {'zone': 56, 'street': 565, 'building': 19},
     'expect same polygon as case #1'),

    ('3. PIN 56092231 B=22',
     'pin',     {'pin': 56092231, 'subject_b': 22},
     'expect n=2 with 24, max_dist <15m (attached)'),

    ('4. PIN 56092231 B=24',
     'pin',     {'pin': 56092231, 'subject_b': 24},
     'expect same polygon as case #3'),

    ('5. PIN 56090355 B=10',
     'pin',     {'pin': 56090355, 'subject_b': 10},
     'expect n=2 with 12, max_dist <15m (attached)'),

    ('6. PIN 51240140 51/410/107',
     'pin',     {'pin': 51240140, 'subject_b': 107},
     'expect n=4 (105/107/525-28/525-30), max_dist >20m (separate)'),

    ('7. PIN 71380039 71/739/17',
     'pin',     {'pin': 71380039, 'subject_b': 17},
     'expect n=2 with 19, distance to be measured'),

    ('8. 52/903/90 (negative standalone)',
     'address', {'zone': 52, 'street': 903, 'building': 90},
     'expect n=1 standalone (timing baseline)'),

    ('9. PIN 66030258 (compound_large)',
     'pin',     {'pin': 66030258, 'subject_b': None},
     'expect PDAREA=59,501 -> falls through to compound_large (handled_by_classifier)'),

    # Case #10: a known-good Doha-area standalone villa, NOT 51/835/17 (Bug A6).
    # 53/240/12 was used as a Sprint 2.16.15 smoke address (Session_Log §1.8).
    ('10. 53/240/12 (Dahil standalone)',
     'address', {'zone': 53, 'street': 240, 'building': 12},
     'expect n=1 standalone (negative control)'),
]


# ----------------------------------------------------------------------
# GIS helpers
# ----------------------------------------------------------------------

def fetch_qars_by_address(zone, street, building):
    """Address -> single QARS_Point feature (with PIN). None on miss."""
    params = {
        'where': f'ZONE_NO={zone} AND STREET_NO={street} AND BUILDING_NO={building}',
        'outFields': '*',
        'returnGeometry': 'true',
        'outSR': '4326',
        'f': 'json',
    }
    res = _http_get_json(ENDPOINTS['qars'], params) or {}
    feats = res.get('features') or []
    if not feats:
        res = _http_get_json(ENDPOINTS['qars_legacy'], params) or {}
        feats = res.get('features') or []
    return feats[0] if feats else None


def fetch_plot_by_pin(pin):
    """PIN -> CadastrePlots feature (polygon + PDAREA + PD_NO). None on miss."""
    params = {
        'where': f'PIN={pin}',
        'outFields': 'PIN,PDAREA,PD_NO',
        'returnGeometry': 'true',
        'outSR': '4326',
        'f': 'json',
    }
    res = _http_get_json(ENDPOINTS['cadastre'], params) or {}
    feats = res.get('features') or []
    return feats[0] if feats else None


def reverse_spatial_qars(polygon_geometry, timeout=10):
    """
    Find ALL QARS_Point features within a cadastral polygon.

    polygon_geometry: the 'geometry' object returned by CadastrePlots
                      (has 'rings' list-of-rings already in WKID 4326).

    Returns: list of dicts {building_no, zone_no, street_no, pin, subtype, lat, lon}.
             Empty list on failure (defensive — never raises).
    """
    rings = polygon_geometry.get('rings') if polygon_geometry else None
    if not rings:
        return []
    geom_payload = json.dumps({
        'rings': rings,
        'spatialReference': {'wkid': 4326},
    })
    params = {
        'geometry': geom_payload,
        'geometryType': 'esriGeometryPolygon',
        'inSR': '4326',
        # Intersects, not Contains — see DEVIATION JUSTIFICATION at top.
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'BUILDING_NO,ZONE_NO,STREET_NO,PIN,BUILDING_NO_SUBTYPE',
        'returnGeometry': 'true',
        'outSR': '4326',
        'f': 'json',
    }
    try:
        res = _http_get_json(ENDPOINTS['qars'], params, timeout=timeout) or {}
    except Exception as e:
        print(f'   [reverse_spatial_qars] exception: {type(e).__name__}: {e}')
        return []
    feats = res.get('features') or []
    out = []
    for f in feats:
        a = f.get('attributes') or {}
        g = f.get('geometry') or {}
        out.append({
            'building_no': a.get('BUILDING_NO'),
            'zone_no': a.get('ZONE_NO'),
            'street_no': a.get('STREET_NO'),
            'pin': a.get('PIN'),
            'subtype': a.get('BUILDING_NO_SUBTYPE'),
            'lat': g.get('y'),
            'lon': g.get('x'),
        })
    return out


def haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres."""
    R = 6371008.8  # IUGG mean Earth radius
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def max_pairwise_distance_m(qars_list):
    """Largest pairwise haversine distance across all QARS in the list."""
    if len(qars_list) < 2:
        return 0.0
    max_d = 0.0
    for i in range(len(qars_list)):
        for j in range(i + 1, len(qars_list)):
            a, b = qars_list[i], qars_list[j]
            if None in (a['lat'], a['lon'], b['lat'], b['lon']):
                continue
            d = haversine_m(a['lat'], a['lon'], b['lat'], b['lon'])
            if d > max_d:
                max_d = d
    return max_d


def predict_type(n_qars, max_dist_m, pdarea=None):
    """
    Sprint 2.21.0.9 decision rules (Anas-confirmed):
        n <= 1                          -> standalone
        n == 2  &  dist < 15            -> attached    (Type A)
        n == 2  &  dist > 30            -> separate    (Type B)
        n == 2  &  15 <= dist <= 30     -> ambiguous   (default: separate behaviour)
        3 <= n <= 5                     -> separate
        n >= 6                          -> handled_by_classifier (defer)

    PDAREA carve-out: parcels >= 50,000 m^2 with QARS<=1 fall through to the
    existing compound_large path. Surface this as 'handled_by_classifier'
    so we don't double-classify in Phase 2.
    """
    if pdarea is not None and pdarea >= 50000 and n_qars <= 1:
        return 'handled_by_classifier'  # compound_large path owns this
    if n_qars <= 1:
        return 'standalone'
    if n_qars == 2:
        if max_dist_m < 15:
            return 'attached'
        if max_dist_m > 30:
            return 'separate'
        return 'ambiguous'
    if 3 <= n_qars <= 5:
        return 'separate'
    return 'handled_by_classifier'


# ----------------------------------------------------------------------
# Per-case driver
# ----------------------------------------------------------------------

def audit_case(label, kind, params, expected):
    print(f'\n=== {label} ===')
    print(f'    expected: {expected}')

    pin = None
    subject_b = None
    if kind == 'address':
        qars = fetch_qars_by_address(
            params['zone'], params['street'], params['building'])
        if not qars:
            print('    FAIL: QARS_Point lookup returned 0 features')
            return None
        attrs = qars.get('attributes') or {}
        pin = attrs.get('PIN')
        subject_b = params['building']
        if not pin:
            print('    FAIL: QARS_Point has no PIN attribute')
            return None
        print(f'    address -> PIN={pin} (QARS_Point subtype={attrs.get("BUILDING_NO_SUBTYPE")})')
    else:
        pin = params['pin']
        subject_b = params.get('subject_b')

    plot = fetch_plot_by_pin(pin)
    if not plot:
        print(f'    FAIL: CadastrePlots returned 0 features for PIN {pin}')
        return None
    pattrs = plot.get('attributes') or {}
    pdarea = pattrs.get('PDAREA')
    pd_no = pattrs.get('PD_NO')
    polygon = plot.get('geometry')

    print(f'    PIN={pin}  PDAREA={pdarea}  PD_NO={pd_no}  rings={len(polygon.get("rings") or []) if polygon else 0}')

    qars_list = reverse_spatial_qars(polygon)
    n = len(qars_list)
    max_d = max_pairwise_distance_m(qars_list)
    ptype = predict_type(n, max_d, pdarea=pdarea)

    # Effective land area per Sprint 2.21.0.9 spec
    if ptype in ('attached', 'separate', 'ambiguous') and n > 0:
        effective = (pdarea or 0) / n
    else:
        effective = pdarea or 0

    print(f'    n_qars={n}  max_pairwise_dist_m={max_d:.1f}')
    print(f'    building_nos={[q["building_no"] for q in qars_list]}')
    print(f'    zone_street_pairs={[(q["zone_no"], q["street_no"]) for q in qars_list]}')
    print(f'    subtypes={[q["subtype"] for q in qars_list]}')
    print(f'    predicted_type={ptype}')
    print(f'    effective_land_area_m2={effective:.1f}  (raw_pdarea={pdarea})')
    if subject_b is not None:
        matched = [q for q in qars_list if q['building_no'] == subject_b]
        print(f'    subject_b={subject_b}  matched_in_polygon={"yes" if matched else "no"}')

    return {
        'label': label,
        'pin': pin,
        'pdarea': pdarea,
        'pd_no': pd_no,
        'subject_b': subject_b,
        'n_qars': n,
        'max_pairwise_dist_m': round(max_d, 1),
        'building_nos': [q['building_no'] for q in qars_list],
        'zone_nos': [q['zone_no'] for q in qars_list],
        'street_nos': [q['street_no'] for q in qars_list],
        'subtypes': [q['subtype'] for q in qars_list],
        'gps': [(q['lat'], q['lon']) for q in qars_list],
        'predicted_type': ptype,
        'effective_land_area_m2': round(effective, 1),
        'expected': expected,
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    print('========================================================')
    print('Sprint 2.21.0.9 — Phase 1 Empirical Audit')
    print('========================================================')
    print(f'Endpoint qars     : {ENDPOINTS["qars"]}')
    print(f'Endpoint cadastre : {ENDPOINTS["cadastre"]}')
    print(f'Cohort size       : {len(COHORT)} cases')

    results = []
    for label, kind, params, expected in COHORT:
        try:
            r = audit_case(label, kind, params, expected)
            if r:
                results.append(r)
        except Exception as e:
            print(f'    EXCEPTION ({type(e).__name__}): {e}')
        time.sleep(2)  # courteous spacing (khazna not known to rate-limit)

    print('\n========================================================')
    print('SUMMARY TABLE')
    print('========================================================')
    header = (f'{"#":<3} {"PIN":<10} {"PDAREA":>8} {"n":>3} '
              f'{"maxDistM":>9} {"type":<22} {"effM2":>9} {"buildings"}')
    print(header)
    print('-' * len(header))
    for i, r in enumerate(results, 1):
        pdarea_s = f'{(r["pdarea"] or 0):.0f}'
        eff_s = f'{r["effective_land_area_m2"]:.0f}'
        print(f'{i:<3} {str(r["pin"]):<10} {pdarea_s:>8} {r["n_qars"]:>3} '
              f'{r["max_pairwise_dist_m"]:>9.1f} {r["predicted_type"]:<22} '
              f'{eff_s:>9} {r["building_nos"]}')

    # Per-type tally
    print('\nType distribution:')
    tally = {}
    for r in results:
        tally[r['predicted_type']] = tally.get(r['predicted_type'], 0) + 1
    for t, c in sorted(tally.items()):
        print(f'    {t:<24} {c}')

    # Persist machine-readable
    out_path = '/tmp/audit_multi_qars_results.json'
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f'\nJSON results written to: {out_path}')
    except Exception as e:
        print(f'\nJSON write failed: {e}  (continuing — table above is canonical)')

    print('\nDONE. Phase 1 audit complete.')


if __name__ == '__main__':
    main()
