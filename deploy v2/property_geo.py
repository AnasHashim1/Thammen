"""
property_geo.py — direction-aware corner detection for Qatar parcels.

⚠️ SAVED FOR FUTURE — NOT WIRED INTO THE VALUATION FLOW (Sprint 2.20.0).
`detect_corner()` is validated 4/4 on Anas's hand-checked parcels but is NOT
called by evaluate_unified. It becomes useful only once a **PIN-keyed sale
source** exists (Confirmed Sales, or verified MME geocoding) so a corner premium
can be derived T1-T1 (Empirical_Findings E12, currently BLOCKED — the MoJ weekly
bulletin is not geocoded). Until then this lives here for future Sprint 2.20.x
corner integration and for ad-hoc analysis tools.

Algorithm (direction-aware parallelism check): a street is "frontage" to a
parcel edge only when it runs roughly PARALLEL to that edge AND stays close
along the edge — which excludes perpendicular T-junction streets that merely end
near a corner vertex (the false-positive the older vertex-proximity logic hit).

Constants are empirical (4 validated cases) and MUST pass a 10/10 validation gate
before any wiring (run from Heroku — the GIS layers are unreachable from the
Claude container).

Pure stdlib (urllib + math). GIS queries: CadastrePlots + Vector/ROADFlowlnA.
"""
import json
import math
import urllib.parse
import urllib.request

GIS_BASE = "https://services.gisqatar.org.qa/server/rest/services"
CADASTRE_URL = f"{GIS_BASE}/CadastrePlots/MapServer/0/query"
ROADS_URL = f"{GIS_BASE}/Vector/ROADFlowlnA/MapServer/0/query"

# Empirical constants (4 validated cases; subject to the 10/10 gate before wiring)
BUFFER_DEG = 0.0005        # ~55m envelope for the road query
MAX_DIST_M = 15            # parcel-edge ↔ road frontage threshold
MIN_ALIGNMENT = 0.7        # |cos θ| ≥ 0.7 ≈ within ~45° → parallel enough
MIN_CLOSE_SAMPLES = 3      # ≥3 of 11 sampled edge points within MAX_DIST_M
MIN_EDGE_LENGTH_M = 5      # skip tiny edges (rounding artifacts)
EDGE_SAMPLES = 11

_M_PER_DEG_LAT = 111_320.0


def _m_per_deg_lon(lat):
    return 111_320.0 * math.cos(math.radians(lat))


def _to_m(p, p0):
    """(lon,lat) -> local meters relative to p0=(lon0,lat0)."""
    return ((p[0] - p0[0]) * _m_per_deg_lon(p0[1]),
            (p[1] - p0[1]) * _M_PER_DEG_LAT)


def _fetch(url, params, timeout=15):
    q = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(q, headers={"User-Agent": "Thammen/property_geo"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def fetch_polygon(pin):
    """Return the parcel's outer ring as [(lon,lat), ...] or None."""
    data = _fetch(CADASTRE_URL, {
        "where": f"PIN={int(pin)}", "outFields": "PIN",
        "returnGeometry": "true", "outSR": "4326", "f": "json",
    })
    feats = data.get("features") or []
    if not feats:
        return None
    rings = (feats[0].get("geometry") or {}).get("rings") or []
    return [tuple(pt) for pt in rings[0]] if rings else None


def fetch_nearby_roads(polygon, buffer_deg=BUFFER_DEG):
    """Return road segments near the polygon: list of (street_no, [(lon,lat)...])."""
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    env = {
        "xmin": min(xs) - buffer_deg, "ymin": min(ys) - buffer_deg,
        "xmax": max(xs) + buffer_deg, "ymax": max(ys) + buffer_deg,
        "spatialReference": {"wkid": 4326},
    }
    data = _fetch(ROADS_URL, {
        "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope",
        "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
        "outFields": "STREET_NO,ROAD_CLASS", "returnGeometry": "true",
        "outSR": "4326", "f": "json",
    })
    out = []
    for f in data.get("features") or []:
        attr = f.get("attributes") or {}
        street = attr.get("STREET_NO")
        for path in (f.get("geometry") or {}).get("paths") or []:
            out.append((street, [tuple(pt) for pt in path]))
    return out


def _seg_dir_unit(a, b, p0):
    ax, ay = _to_m(a, p0)
    bx, by = _to_m(b, p0)
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    return (dx / L, dy / L, L) if L > 0 else (0.0, 0.0, 0.0)


def _point_seg_dist_m(p, a, b, p0):
    px, py = _to_m(p, p0)
    ax, ay = _to_m(a, p0)
    bx, by = _to_m(b, p0)
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _edge_has_frontage(edge_a, edge_b, road_path, p0):
    e_ux, e_uy, e_len = _seg_dir_unit(edge_a, edge_b, p0)
    if e_len < MIN_EDGE_LENGTH_M:
        return False
    # sample points along the edge (in degrees, then measured in meters)
    samples = [(edge_a[0] + (edge_b[0] - edge_a[0]) * i / (EDGE_SAMPLES - 1),
                edge_a[1] + (edge_b[1] - edge_a[1]) * i / (EDGE_SAMPLES - 1))
               for i in range(EDGE_SAMPLES)]
    for ra, rb in zip(road_path, road_path[1:]):
        r_ux, r_uy, r_len = _seg_dir_unit(ra, rb, p0)
        if r_len <= 0:
            continue
        if abs(e_ux * r_ux + e_uy * r_uy) < MIN_ALIGNMENT:
            continue  # not parallel enough (excludes perpendicular T-junctions)
        close = sum(1 for s in samples
                    if _point_seg_dist_m(s, ra, rb, p0) <= MAX_DIST_M)
        if close >= MIN_CLOSE_SAMPLES:
            return True
    return False


def detect_corner(pin):
    """Classify a parcel by distinct fronting streets.

    Returns {'is_corner', 'frontage_streets', 'detection_method', 'tier',
             'confidence'} or {'error': ...} on failure. NOT wired into valuation.
    """
    try:
        polygon = fetch_polygon(pin)
        if not polygon or len(polygon) < 4:
            return {'error': 'no_polygon', 'pin': pin}
        p0 = polygon[0]
        roads = fetch_nearby_roads(polygon)
        frontage = set()
        for ea, eb in zip(polygon, polygon[1:]):
            for street, path in roads:
                if len(path) < 2:
                    continue
                if _edge_has_frontage(ea, eb, path, p0):
                    if street is not None:
                        frontage.add(street)
        streets = sorted(frontage)
        if len(streets) >= 2:
            klass = 'corner'
        elif len(streets) == 1:
            klass = 'non-corner'
        else:
            klass = 'isolated'   # very rare — caller should WARN
        return {
            'is_corner': klass == 'corner',
            'classification': klass,
            'frontage_streets': streets,
            'detection_method': 'direction_aware_v1',
            'tier': 1,
            'confidence': 'high' if klass != 'isolated' else 'low',
        }
    except Exception as e:
        return {'error': f'{type(e).__name__}: {str(e)[:120]}', 'pin': pin}


if __name__ == '__main__':
    import sys
    print(json.dumps(detect_corner(int(sys.argv[1])), ensure_ascii=False, indent=2))
