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


# ════════════════════════════════════════════════════════════════════════
# Sprint 2.21.0.9 — Multi-QARS detection (one PIN, multiple addressed buildings)
# ════════════════════════════════════════════════════════════════════════
# Pure-logic classifier (no GIS calls — caller supplies the qars_list from
# qatar_gis.count_qars_within_polygon). Discovered via the Bou Hamour
# 56/565/21 case where a single cadastral PIN (PDAREA=900) carried two
# QARS-addressed villas (B=19 + B=21), causing MoJ bracket-selection to
# look up 600-900 instead of the correct 400-600 → ~30-40% over-valuation.
#
# Threshold 18m (NOT spec's 15m): Phase 1 empirical audit (2026-05-23)
# found two unrelated cases at exactly 15.2m, which looks like a QARS_Point
# GPS-labeling artifact. Bumping to 18m absorbs that cluster while still
# leaving the 18-30m ambiguous band for genuinely uncertain cases. Bracket
# selection identical either way (PDAREA/n=2); the only behavioural
# difference is the UI "value whole structure" toggle visibility.

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class MultiQarsResult:
    """Outcome of classifying how a cadastral polygon's QARS points cluster.

    `type` semantics:
      - 'standalone'             → n_qars <= 1; effective = pdarea
      - 'attached'               → n=2, max_dist < THRESHOLD_ATTACHED_M (duplex)
      - 'separate'               → n=2 & max_dist > THRESHOLD_SEPARATE_M, OR 3<=n<=5
      - 'ambiguous'              → n=2 & THRESHOLD_ATTACHED_M <= max_dist <= THRESHOLD_SEPARATE_M
      - 'handled_by_classifier'  → PDAREA>=50K (compound_large) OR n>=6 (apartments path)
    """
    is_shared: bool
    n_qars: int
    qars_buildings: list  # list of dicts with building_no/zone/street/subtype/lat/lon
    subject_building_no: Optional[int]
    type: str             # see semantics above
    effective_land_area: float
    max_gps_distance_m: float
    confidence: str       # 'high' | 'medium' | 'low'

    def to_dict(self) -> dict:
        d = asdict(self)
        # Round noisy floats
        d['effective_land_area'] = round(self.effective_land_area, 1)
        d['max_gps_distance_m'] = round(self.max_gps_distance_m, 1)
        return d


# Phase 1 audit cluster sat at exactly 15.2m → 18m absorbs the artifact.
THRESHOLD_ATTACHED_M: float = 18.0
THRESHOLD_SEPARATE_M: float = 30.0
# PIN/polygon area at-or-above this → compound_large path already owns it.
COMPOUND_LARGE_AREA_M2: float = 50_000.0
# n_qars at-or-above this → apartments path will own it (deferred — Sprint 2.21.1).
APARTMENTS_THRESHOLD_N: int = 6


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_008.8  # IUGG mean Earth radius (metres)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def _max_pairwise_distance_m(qars_list: list) -> float:
    """Largest haversine distance between any two QARS points in the list."""
    if not qars_list or len(qars_list) < 2:
        return 0.0
    max_d = 0.0
    for i in range(len(qars_list)):
        a = qars_list[i]
        a_lat, a_lon = a.get('lat'), a.get('lon')
        if a_lat is None or a_lon is None:
            continue
        for j in range(i + 1, len(qars_list)):
            b = qars_list[j]
            b_lat, b_lon = b.get('lat'), b.get('lon')
            if b_lat is None or b_lon is None:
                continue
            d = _haversine_m(a_lat, a_lon, b_lat, b_lon)
            if d > max_d:
                max_d = d
    return max_d


def classify_multi_qars(
    pdarea: Optional[float],
    qars_list: list,
    subject_building_no: Optional[int] = None,
    threshold_attached_m: float = THRESHOLD_ATTACHED_M,
    threshold_separate_m: float = THRESHOLD_SEPARATE_M,
) -> MultiQarsResult:
    """
    Classify how a cadastral polygon's QARS points cluster.

    Args:
      pdarea:                cadastral PDAREA (m²). None → treated as 0 for split arithmetic.
      qars_list:             list of dicts (from qatar_gis.count_qars_within_polygon)
                             with keys building_no, zone_no, street_no, pin, subtype, lat, lon.
      subject_building_no:   the user's specific building (None if PIN-only entry).
      threshold_attached_m:  default 18m (Phase 1 audit calibration — see header).
      threshold_separate_m:  default 30m (above this → clearly separate).

    Decision rules (Sprint 2.21.0.9 spec + 18m calibration):
      PDAREA >= 50,000 AND n_qars <= 1     → handled_by_classifier (compound_large)
      n_qars >= 6                          → handled_by_classifier (apartments path)
      n_qars <= 1                          → standalone
      n_qars == 2 & dist < 18m             → attached      (Type A — duplex)
      n_qars == 2 & 18 <= dist <= 30       → ambiguous     (default behaviour: separate)
      n_qars == 2 & dist > 30m             → separate
      3 <= n_qars <= 5                     → separate

    effective_land_area:
      standalone OR handled_by_classifier  → pdarea (unchanged)
      attached / separate / ambiguous      → pdarea / n_qars (no title discount)

    Confidence:
      attached + dist < threshold_attached_m - 3        → high (well below boundary)
      separate + dist > threshold_separate_m + 5        → high
      ambiguous                                         → medium
      handled_by_classifier / standalone                → high
    """
    n = len(qars_list) if qars_list else 0
    max_dist = _max_pairwise_distance_m(qars_list)
    safe_pdarea = float(pdarea) if pdarea else 0.0

    # Carve-outs (existing paths own these — do not double-classify)
    if safe_pdarea >= COMPOUND_LARGE_AREA_M2 and n <= 1:
        return MultiQarsResult(
            is_shared=False, n_qars=n, qars_buildings=list(qars_list or []),
            subject_building_no=subject_building_no,
            type='handled_by_classifier',
            effective_land_area=safe_pdarea, max_gps_distance_m=max_dist,
            confidence='high',
        )
    if n >= APARTMENTS_THRESHOLD_N:
        return MultiQarsResult(
            is_shared=True, n_qars=n, qars_buildings=list(qars_list or []),
            subject_building_no=subject_building_no,
            type='handled_by_classifier',
            effective_land_area=safe_pdarea, max_gps_distance_m=max_dist,
            confidence='medium',
        )

    if n <= 1:
        return MultiQarsResult(
            is_shared=False, n_qars=n, qars_buildings=list(qars_list or []),
            subject_building_no=subject_building_no,
            type='standalone',
            effective_land_area=safe_pdarea, max_gps_distance_m=max_dist,
            confidence='high',
        )

    # n >= 2 with a small parcel → multi-villa
    effective = safe_pdarea / n if n > 0 else safe_pdarea
    if n == 2:
        if max_dist < threshold_attached_m:
            confidence = 'high' if max_dist < (threshold_attached_m - 3) else 'medium'
            return MultiQarsResult(
                is_shared=True, n_qars=n, qars_buildings=list(qars_list),
                subject_building_no=subject_building_no,
                type='attached',
                effective_land_area=effective, max_gps_distance_m=max_dist,
                confidence=confidence,
            )
        if max_dist > threshold_separate_m:
            return MultiQarsResult(
                is_shared=True, n_qars=n, qars_buildings=list(qars_list),
                subject_building_no=subject_building_no,
                type='separate',
                effective_land_area=effective, max_gps_distance_m=max_dist,
                confidence='high',
            )
        # 18m <= dist <= 30m → ambiguous (default behaviour: separate)
        return MultiQarsResult(
            is_shared=True, n_qars=n, qars_buildings=list(qars_list),
            subject_building_no=subject_building_no,
            type='ambiguous',
            effective_land_area=effective, max_gps_distance_m=max_dist,
            confidence='medium',
        )

    # 3 <= n <= 5 → clean small cluster, treat as separate
    return MultiQarsResult(
        is_shared=True, n_qars=n, qars_buildings=list(qars_list),
        subject_building_no=subject_building_no,
        type='separate',
        effective_land_area=effective, max_gps_distance_m=max_dist,
        confidence='high',
    )


if __name__ == '__main__':
    import sys
    print(json.dumps(detect_corner(int(sys.argv[1])), ensure_ascii=False, indent=2))
