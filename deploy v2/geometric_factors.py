#!/usr/bin/env python3
"""
geometric_factors.py — Sprint 2 Phase 1

Polygon-based property analysis going beyond point-based queries:
    1. Corner detection (polygon adjacent to 2+ road segments)
    2. Main road frontage (polygon edge along main road, not just point near road)
    3. HBU — adjacent zoning analysis (R1 near C/MU = rezoning option value)
    4. Named landmark whitelist (large malls, metros, corniche by name)

These factors operate on the PLOT POLYGON (from CadastrePlots) rather than just
the address point, giving more accurate detection than the existing point-based
factors in property_factors.py.
"""

from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import List, Optional, Tuple

GIS_BASE = "https://services.gisqatar.org.qa/server/rest/services"

LAYER_URLS = {
    'cadastre':     f'{GIS_BASE}/Vector/CadastrePlots/MapServer/0/query',
    'zoning':       f'{GIS_BASE}/Vector/Zoning/MapServer/0/query',
    'main_roads':   f'{GIS_BASE}/Vector/ROADFlowlnA/MapServer/2/query',
    'local_roads':  f'{GIS_BASE}/Vector/ROADFlowlnA/MapServer/1/query',
    'landmarks':    f'{GIS_BASE}/Vector/Landmarks/MapServer/0/query',
}

TIMEOUT = 8


# ── Qatar Major Mall Whitelist ──
# Known major malls/landmarks by GPS — these merit specific landmark premium
# Coordinates verified via Qatar GIS Landmarks layer search
# Distance thresholds: walking (<500m), short drive (<2km), area benefit (<5km)
QATAR_MAJOR_MALLS = {
    'دار السلام (فندق + سوق)': (25.2447, 51.4917, 'Dar Al Salam (Maamoura area)'),
    'فستيفال سيتي':         (25.378, 51.522, 'Doha Festival City'),
    'فيلاجيو':              (25.262, 51.451, 'Villaggio Mall'),
    'لاند مارك':            (25.327, 51.523, 'Landmark Mall'),
    'سيتي سنتر':            (25.323, 51.530, 'City Center Doha'),
    'بليس فاندوم':          (25.382, 51.512, 'Place Vendôme'),
    'هيات بلازا':           (25.290, 51.467, 'Hyatt Plaza'),
    'الحزم مول':            (25.350, 51.493, 'Al Hazm'),
    'تواصيل بلازا':         (25.346, 51.534, 'Tawar Mall'),
    'ايزدان مول':           (25.244, 51.486, 'Ezdan Mall'),
    'مول قطر':              (25.276, 51.439, 'Mall of Qatar'),
    'لولو هايبر ماركت سلوى': (25.290, 51.475, 'LuLu Hypermarket Salwa'),
}

QATAR_METRO_STATIONS = {
    # Red Line (north-south)
    'محطة الجديدة':           (25.276, 51.519),
    'محطة المطار':            (25.265, 51.566),
    'محطة لوسيل':             (25.435, 51.487),
    'محطة قطر الوطنية':       (25.328, 51.527),
    'محطة مشيرب':             (25.291, 51.530),
    'محطة سوق واقف':          (25.288, 51.534),
    'محطة الكورنيش':          (25.297, 51.534),
    'محطة الدفنة':            (25.331, 51.532),
    'محطة وادي السيل':        (25.224, 51.494),
    # Gold Line (east-west)
    'محطة الواجبة':           (25.270, 51.452),
    'محطة جامعة قطر':         (25.378, 51.487),
    'محطة الريان':            (25.291, 51.471),
    # Add stations as needed
}


# ── HTTP helper ──

def _http_get_json(url: str, params: dict) -> Optional[dict]:
    try:
        full = url + '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(full, headers={'User-Agent': 'thammen-avm/2.0'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"[geometric_factors] HTTP error: {e}")
        return None


# ── Geometric primitives ──

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in meters between two GPS points (WGS84)."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def _polygon_edges(rings: List[List[List[float]]]) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """Extract edges from an ESRI polygon rings structure.

    Each ring is a list of [x, y] points (in WGS84 here we use lon, lat).
    Returns list of ((lat1, lon1), (lat2, lon2)) edges.
    """
    edges = []
    if not rings:
        return edges
    for ring in rings:
        if not ring or len(ring) < 2:
            continue
        # ESRI uses [lon, lat] ordering
        for i in range(len(ring) - 1):
            p1 = (ring[i][1], ring[i][0])      # (lat, lon)
            p2 = (ring[i+1][1], ring[i+1][0])
            edges.append((p1, p2))
    return edges


def _edge_midpoint(edge) -> Tuple[float, float]:
    """Midpoint of an edge in (lat, lon)."""
    (lat1, lon1), (lat2, lon2) = edge
    return ((lat1 + lat2) / 2, (lon1 + lon2) / 2)


def _edge_length_m(edge) -> float:
    """Length of edge in meters."""
    (lat1, lon1), (lat2, lon2) = edge
    return _haversine_m(lat1, lon1, lat2, lon2)


def _bbox_around_point(lat: float, lon: float, radius_m: float) -> dict:
    """Build an ESRI envelope bbox around a point."""
    # ~111111 meters per degree latitude; longitude scales with latitude
    dlat = radius_m / 111111
    dlon = radius_m / (111111 * math.cos(math.radians(lat)))
    return {
        'xmin': lon - dlon, 'ymin': lat - dlat,
        'xmax': lon + dlon, 'ymax': lat + dlat,
        'spatialReference': {'wkid': 4326},
    }


# ── Polygon fetch helper ──

def fetch_plot_polygon(pin: int) -> Optional[dict]:
    """Fetch plot polygon by PIN. Returns dict with 'rings' (WGS84) and 'centroid'."""
    if not pin:
        return None
    data = _http_get_json(LAYER_URLS['cadastre'], {
        'where': f'PIN={pin}',
        'outFields': 'PIN,PDAREA,PD_NO',
        'returnGeometry': 'true',
        'outSR': '4326',
        'f': 'json',
    })
    if not data or not data.get('features'):
        return None
    feat = data['features'][0]
    geom = feat.get('geometry', {})
    rings = geom.get('rings', [])
    if not rings:
        return None
    # Compute centroid (approx: average of first ring's points)
    points = rings[0]
    if not points:
        return None
    lat_c = sum(p[1] for p in points) / len(points)
    lon_c = sum(p[0] for p in points) / len(points)
    return {
        'rings': rings,
        'centroid': (lat_c, lon_c),
        'pin': pin,
        'plot_area_m2': feat.get('attributes', {}).get('PDAREA'),
        'pd_no': feat.get('attributes', {}).get('PD_NO'),
    }


# ── Factor 1: Polygon-based corner detection ──

def detect_corner(polygon: dict, road_search_buffer_m: float = 15.0) -> dict:
    """
    Detect if plot is a corner property by checking how many distinct road
    segments are adjacent to the plot edges.

    Method:
        For each edge of the polygon, sample multiple points (start, mid, end),
        check if a road segment runs along it (within `road_search_buffer_m`).
        Count distinct roads (by OBJECTID).
        Buffer 15m chosen empirically: typical Qatar plot-to-road offset is
        2-12m due to sidewalk + setback. 8m was too tight, 25m gives false
        positives from across-street roads.

    Returns:
        {
            'is_corner': bool,
            'distinct_roads_adjacent': int,
            'main_road_adjacent': bool,
            'edges_with_road': int,
            'total_edges': int,
            'evidence_ar': str,
            'confidence': 'high' | 'medium' | 'low',
        }
    """
    if not polygon or not polygon.get('rings'):
        return {'is_corner': False, 'confidence': 'low', 'evidence_ar': 'لا polygon متاح'}

    edges = _polygon_edges(polygon['rings'])
    if not edges:
        return {'is_corner': False, 'confidence': 'low', 'evidence_ar': 'لا حواف'}

    # Only consider edges > 5m (skip tiny corner-cut segments)
    significant_edges = [e for e in edges if _edge_length_m(e) >= 5.0]
    if not significant_edges:
        return {'is_corner': False, 'confidence': 'low', 'evidence_ar': 'حواف صغيرة جداً'}

    # For each significant edge, query for adjacent roads
    # Track STREET_NO (not OBJECTID) to distinguish true corners from split segments
    main_streets = set()      # set of (STREET_NO, ZONE_NO) tuples
    local_streets = set()
    edges_with_road = 0
    edges_with_main_road = 0
    edge_evidence = []

    for edge in significant_edges:
        # Sample 3 points along the edge: 25%, 50%, 75% to catch roads at corners
        (lat1, lon1), (lat2, lon2) = edge
        sample_points = [
            (lat1 + (lat2-lat1)*0.25, lon1 + (lon2-lon1)*0.25),
            (lat1 + (lat2-lat1)*0.50, lon1 + (lon2-lon1)*0.50),
            (lat1 + (lat2-lat1)*0.75, lon1 + (lon2-lon1)*0.75),
        ]

        edge_main_streets = set()
        edge_local_streets = set()

        for sp_lat, sp_lon in sample_points:
            bbox = _bbox_around_point(sp_lat, sp_lon, road_search_buffer_m)
            params = {
                'geometry': json.dumps(bbox),
                'geometryType': 'esriGeometryEnvelope',
                'inSR': '4326',
                'spatialRel': 'esriSpatialRelIntersects',
                'outFields': 'OBJECTID,STREET_NO,ZONE_NO,ROAD_CLASS',
                'returnGeometry': 'false',
                'f': 'json',
            }
            main = _http_get_json(LAYER_URLS['main_roads'], params)
            if main and main.get('features'):
                for f in main['features']:
                    a = f.get('attributes', {})
                    sn = a.get('STREET_NO')
                    zn = a.get('ZONE_NO')
                    if sn is not None:
                        edge_main_streets.add((zn, sn))

            local = _http_get_json(LAYER_URLS['local_roads'], params)
            if local and local.get('features'):
                for f in local['features']:
                    a = f.get('attributes', {})
                    sn = a.get('STREET_NO')
                    zn = a.get('ZONE_NO')
                    if sn is not None:
                        edge_local_streets.add((zn, sn))

        main_streets.update(edge_main_streets)
        local_streets.update(edge_local_streets)

        if edge_main_streets or edge_local_streets:
            edges_with_road += 1
            if edge_main_streets:
                edges_with_main_road += 1
            edge_evidence.append({
                'edge_length_m': round(_edge_length_m(edge), 1),
                'main_streets': [s[1] for s in edge_main_streets],
                'local_streets': [s[1] for s in edge_local_streets],
            })

    distinct_streets = len(main_streets) + len(local_streets)
    # True corner: at least 2 different STREET_NOs on at least 2 edges
    is_corner = distinct_streets >= 2 and edges_with_road >= 2
    main_road_adjacent = len(main_streets) > 0

    # Confidence
    if edges_with_road >= 2 and distinct_streets >= 2:
        confidence = 'high'
    elif edges_with_road >= 1:
        confidence = 'medium'
    else:
        confidence = 'low'

    # Evidence string (Arabic)
    main_st_numbers = sorted({s[1] for s in main_streets})
    local_st_numbers = sorted({s[1] for s in local_streets})
    all_street_label = []
    if main_st_numbers:
        all_street_label.append(f'شوارع رئيسية: {main_st_numbers}')
    if local_st_numbers:
        all_street_label.append(f'شوارع داخلية: {local_st_numbers}')
    street_list_str = '، '.join(all_street_label)

    if is_corner and main_road_adjacent:
        evidence = f'زاوية مع شارع رئيسي ({street_list_str})'
    elif is_corner:
        evidence = f'زاوية على شوارع داخلية متعددة ({street_list_str})'
    elif main_road_adjacent:
        evidence = f'مطل على شارع رئيسي ({street_list_str})'
    elif edges_with_road >= 1:
        evidence = f'مطل على شارع داخلي ({street_list_str})'
    else:
        evidence = 'لم يُكتشف شارع مجاور — قطعة داخلية محتملة'

    return {
        'is_corner': is_corner,
        'distinct_streets_adjacent': distinct_streets,
        'main_road_adjacent': main_road_adjacent,
        'main_streets': sorted(main_st_numbers),
        'local_streets': sorted(local_st_numbers),
        'main_road_count': len(main_streets),
        'local_road_count': len(local_streets),
        'edges_with_road': edges_with_road,
        'edges_with_main_road': edges_with_main_road,
        'total_edges': len(significant_edges),
        'evidence_ar': evidence,
        'confidence': confidence,
        'edge_details': edge_evidence[:10],
    }


# ── Factor 2: HBU — Adjacent zoning ──

def analyze_adjacent_zoning(centroid_lat: float, centroid_lon: float,
                            current_zoning_code: str,
                            radius_m: float = 150) -> dict:
    """
    Highest and Best Use analysis: detect if a residential property is adjacent
    to commercial or mixed-use zones, suggesting future rezoning potential.

    Args:
        centroid_lat, centroid_lon: property centroid in WGS84
        current_zoning_code: subject's current zone code (e.g., 'R1', 'R2', 'R3', 'C')
        radius_m: search radius for neighboring plots

    Returns:
        {
            'hbu_potential': bool,
            'potential_pct': float (estimated upside, e.g., 0.20 = +20%),
            'evidence_ar': str,
            'adjacent_zones': list of unique adjacent zone codes,
        }
    """
    # If subject is already commercial, HBU doesn't apply
    if current_zoning_code and 'C' in (current_zoning_code or '').upper() and 'R' not in (current_zoning_code or '').upper():
        return {
            'hbu_potential': False,
            'evidence_ar': 'العقار تجاري بالفعل — HBU لا تنطبق',
        }

    bbox = _bbox_around_point(centroid_lat, centroid_lon, radius_m)
    params = {
        'geometry': json.dumps(bbox),
        'geometryType': 'esriGeometryEnvelope',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'ZONING,CODE',
        'returnGeometry': 'false',
        'f': 'json',
    }
    data = _http_get_json(LAYER_URLS['zoning'], params)
    if not data or not data.get('features'):
        return {
            'hbu_potential': False,
            'evidence_ar': 'لا بيانات تصنيف للقطع المجاورة',
        }

    # Collect unique zone strings
    adjacent_codes = set()
    for f in data['features']:
        attrs = f.get('attributes', {})
        zoning = (attrs.get('ZONING') or '').strip().upper()
        if zoning:
            adjacent_codes.add(zoning)

    # Detect HBU-triggering adjacencies — only TRUE commercial codes
    # Qatar zoning codes:
    #   R1, R2, R3, RH, RM = residential variants
    #   C, C1, C2, CC, MU = commercial / mixed-use (rezoning targets)
    #   CF = Civic Facility (NOT commercial — schools, mosques, gov)
    #   TU = Transport/Utility (NOT commercial)
    #   SD = Special District (varies, conservative: not commercial)
    #   IND, I = Industrial (negative, not positive)
    TRUE_COMMERCIAL_CODES = {'C', 'C1', 'C2', 'CC', 'CR', 'MU', 'M-U'}
    INDUSTRIAL_CODES = {'IND', 'I', 'I1', 'I2'}

    has_commercial = any(c in TRUE_COMMERCIAL_CODES for c in adjacent_codes)
    has_mixed_use = any(c in {'MU', 'M-U'} for c in adjacent_codes)
    has_industrial = any(c in INDUSTRIAL_CODES for c in adjacent_codes)
    has_higher_density = False
    current_density = 0
    if current_zoning_code and current_zoning_code.upper().startswith('R'):
        try:
            current_density = int(''.join(c for c in current_zoning_code if c.isdigit()) or '1')
        except ValueError:
            current_density = 1
        for c in adjacent_codes:
            if c.startswith('R') and c not in {current_zoning_code.upper()}:
                try:
                    n = int(''.join(ch for ch in c if ch.isdigit()) or '0')
                    if n > current_density:
                        has_higher_density = True
                        break
                except ValueError:
                    pass

    if has_industrial:
        # Industrial adjacency is NEGATIVE, not positive
        return {
            'hbu_potential': False,
            'industrial_adjacency': True,
            'potential_pct': -0.10,
            'evidence_ar': f'⚠ تصنيف صناعي مجاور ({", ".join(c for c in adjacent_codes if c in INDUSTRIAL_CODES)}) — قد يَخفض القيمة',
            'adjacent_zones': sorted(adjacent_codes),
        }

    if not (has_commercial or has_higher_density):
        # Adjacent zones might include CF, TU, SD — these are not value-altering
        return {
            'hbu_potential': False,
            'evidence_ar': f'القطع المجاورة من نفس التصنيف ({", ".join(sorted(adjacent_codes))}) — لا إمكانية تعديل رخصة تجاري واضحة',
            'adjacent_zones': sorted(adjacent_codes),
        }

    # Estimate potential
    if has_mixed_use:
        potential_pct = 0.20
        flag = 'استخدام مختلط مجاور (MU)'
    elif has_commercial:
        potential_pct = 0.25
        flag = f'تجاري مجاور ({", ".join(c for c in adjacent_codes if c in TRUE_COMMERCIAL_CODES)})'
    else:
        potential_pct = 0.10
        flag = 'تصنيف كثافة أعلى مجاور'

    evidence = (
        f'⚠ إمكانية تعديل رخصة: {flag} ({", ".join(sorted(adjacent_codes))}). '
        f'القيمة قد ترتفع بـ +{int(potential_pct*100)}% '
        f'إذا تم اعتماد التعديل (RICS HBU — VPS 4 §3.4).'
    )

    return {
        'hbu_potential': True,
        'potential_pct': potential_pct,
        'evidence_ar': evidence,
        'adjacent_zones': sorted(adjacent_codes),
        'trigger': flag,
    }


# ── Factor 3: Named landmark whitelist ──

def find_named_landmarks(lat: float, lon: float, max_distance_m: float = 2000) -> dict:
    """
    Find named major landmarks (malls, metros) within distance using whitelist.

    Returns dict with lists of malls and metros sorted by distance.
    """
    malls_nearby = []
    for ar_name, (m_lat, m_lon, en_name) in QATAR_MAJOR_MALLS.items():
        d = _haversine_m(lat, lon, m_lat, m_lon)
        if d <= max_distance_m:
            malls_nearby.append({
                'name_ar': ar_name,
                'name_en': en_name,
                'distance_m': round(d, 0),
                'walkable': d <= 500,   # 500m = ~6 min walk
            })
    malls_nearby.sort(key=lambda x: x['distance_m'])

    metros_nearby = []
    for ar_name, (m_lat, m_lon) in QATAR_METRO_STATIONS.items():
        d = _haversine_m(lat, lon, m_lat, m_lon)
        if d <= max_distance_m:
            metros_nearby.append({
                'name_ar': ar_name,
                'distance_m': round(d, 0),
                'walkable': d <= 500,
            })
    metros_nearby.sort(key=lambda x: x['distance_m'])

    return {
        'malls': malls_nearby,
        'metros': metros_nearby,
        'closest_mall_m': malls_nearby[0]['distance_m'] if malls_nearby else None,
        'closest_metro_m': metros_nearby[0]['distance_m'] if metros_nearby else None,
    }


# ── Combined analysis ──

def analyze_geometric_factors(pin: int, lat: float, lon: float,
                              current_zoning_code: Optional[str] = None) -> dict:
    """
    Run all polygon-based geometric analyses.

    Returns combined dict with corner, HBU, and named landmarks information.
    """
    result = {
        'pin': pin,
        'centroid': (lat, lon),
    }

    # Fetch polygon
    polygon = fetch_plot_polygon(pin)
    if polygon:
        result['polygon_available'] = True
        result['plot_area_m2'] = polygon.get('plot_area_m2')
        result['pd_no'] = polygon.get('pd_no')

        # Use polygon centroid (more accurate than QARS point)
        if polygon.get('centroid'):
            lat, lon = polygon['centroid']
            result['centroid'] = (lat, lon)

        # Corner detection
        result['corner'] = detect_corner(polygon)
    else:
        result['polygon_available'] = False
        result['corner'] = {
            'is_corner': False,
            'confidence': 'low',
            'evidence_ar': 'لا توجد بيانات polygon',
        }

    # HBU (uses centroid)
    if current_zoning_code:
        result['hbu'] = analyze_adjacent_zoning(lat, lon, current_zoning_code)

    # Named landmarks
    result['named_landmarks'] = find_named_landmarks(lat, lon)

    return result


# ── CLI test ──

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 4:
        print("Usage: geometric_factors.py <pin> <lat> <lon> [zoning_code]")
        sys.exit(1)
    pin = int(sys.argv[1])
    lat = float(sys.argv[2])
    lon = float(sys.argv[3])
    zoning = sys.argv[4] if len(sys.argv) > 4 else None
    result = analyze_geometric_factors(pin, lat, lon, zoning)
    print(json.dumps(result, ensure_ascii=False, indent=2))
