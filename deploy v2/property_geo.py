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
# Sprint 2.21.0.9 — Multi-QARS Detection — STAGE 1
# ════════════════════════════════════════════════════════════════════════
# Pure-logic detector (no GIS calls — caller supplies the qars_list from
# qatar_gis.count_qars_within_polygon).
#
# WHY: Bou Hamour 56/565/21 (a 2.19.1 smoke address) was silently mis-valued
# ~30-40% on the land component because PDAREA=900 was used without checking
# how many QARS-addressed villas occupy that polygon. PDAREA=900 → MoJ bucket
# 900-1500; the correct stratum for one share of two villas is 400-600.
#
# WHAT THIS MODULE DOES (Stage 1, intentionally minimal):
#   - Detection: is_shared = n_qars >= 2 (after carve-outs).
#   - Split: effective_land_area = PDAREA / n_qars. No title discount (market
#     does not distinguish — Anas confirmed 2026-05-23).
#   - That's it. There is NO attached/separate classification, NO GPS distance
#     threshold, NO confidence-tier ladder, NO "value whole structure" toggle.
#
# WHY NOT MORE: GPS centroid distance alone cannot distinguish attached
# (shared wall) from separate (with code-min courtyards) in the 10-20m range
# (Anas, 2026-05-23: 56/565/21 + 19 measure 15.2m centroid-to-centroid yet
# are physically separate with full setbacks/courtyards). True A/B
# discrimination requires Building Footprint geometry — wall-to-wall distance
# vs Qatar MME 3m setback code → 6m gap separates "duplex" from "neighbours".
# See EMPIRICAL_FINDINGS.md E15 (setback code), E18 (the Stage 2 rule).
#
# STAGE 2 (deferred to a Sprint 2.21.0.10 candidate, conditional on Building
# Footprint layer probe): wall_to_wall < 1m → attached; >= 6m → separate;
# 1-6m → sub_minimum (flag for review). This is the FINAL rule per Anas
# 2026-05-23 — maps directly to Qatar building code, no threshold tuning needed.
#
# STAGE 3 (further future): user-on-site corrections override Stage 2.
#
# The staged-valuation pattern (Stage 1 always returns a number in <=5s with
# ~70% confidence; Stage 2 refines to ~90%; Stage 3 to ~95%+) is the platform-
# wide strategy per Anas 2026-05-23. See EMPIRICAL_FINDINGS.md E16.

from dataclasses import dataclass, asdict
from typing import Optional


# PIN/polygon area at-or-above this → compound_large path already owns it.
COMPOUND_LARGE_AREA_M2: float = 50_000.0
# n_qars at-or-above this → apartments path will own it (deferred — Sprint 2.21.1).
APARTMENTS_THRESHOLD_N: int = 6
# Stage 1 confidence — Anas decision 2026-05-23 (staged-valuation pattern).
STAGE1_CONFIDENCE_PCT: int = 70


@dataclass
class MultiQarsResult:
    """Stage 1 detection outcome — minimal shape (no classification).

    `is_shared` is the SINGLE detection signal:
      - True  → 2+ QARS share this cadastral polygon and neither carve-out
                (compound_large / apartments) applies → the UI surfaces the
                multi-QARS flag + manual override; the engine uses
                effective_land_area for bracket selection.
      - False → standalone OR carve-out fired → behaviour byte-for-byte
                unchanged from pre-Sprint.
    """
    is_shared: bool
    n_qars: int
    qars_buildings: list           # list of dicts: building_no/zone/street/subtype/lat/lon
    subject_building_no: Optional[int]
    effective_land_area: float     # PDAREA/n_qars if is_shared, else PDAREA

    def to_dict(self) -> dict:
        d = asdict(self)
        d['effective_land_area'] = round(self.effective_land_area, 1)
        return d


def classify_multi_qars(
    pdarea: Optional[float],
    qars_list: list,
    subject_building_no: Optional[int] = None,
) -> MultiQarsResult:
    """Stage 1 multi-QARS detector.

    Carve-outs (existing engine paths already handle these — we MUST NOT
    double-classify; is_shared=False to keep the multi_qars panel hidden):
      - PDAREA >= 50,000 AND n_qars <= 1 → compound_large path owns it.
      - n_qars >= 6                      → apartments path will own it
                                           (deferred to Sprint 2.21.1).

    Otherwise:
      - n_qars <= 1 → standalone (is_shared=False, effective = PDAREA).
      - n_qars >= 2 → shared (is_shared=True,  effective = PDAREA / n_qars).

    No type/threshold/GPS-distance logic — that's Stage 2 (Sprint 2.21.0.10
    candidate, requires Building Footprint layer access).

    Defensive on shape: empty/None qars_list → standalone; None pdarea → 0.
    """
    n = len(qars_list) if qars_list else 0
    safe_pdarea = float(pdarea) if pdarea else 0.0
    safe_list = list(qars_list) if qars_list else []

    # Carve-out 1: compound_large
    if safe_pdarea >= COMPOUND_LARGE_AREA_M2 and n <= 1:
        return MultiQarsResult(
            is_shared=False, n_qars=n, qars_buildings=safe_list,
            subject_building_no=subject_building_no,
            effective_land_area=safe_pdarea,
        )
    # Carve-out 2: apartments path (deferred)
    if n >= APARTMENTS_THRESHOLD_N:
        return MultiQarsResult(
            is_shared=False, n_qars=n, qars_buildings=safe_list,
            subject_building_no=subject_building_no,
            effective_land_area=safe_pdarea,
        )
    # Standalone
    if n <= 1:
        return MultiQarsResult(
            is_shared=False, n_qars=n, qars_buildings=safe_list,
            subject_building_no=subject_building_no,
            effective_land_area=safe_pdarea,
        )
    # Shared — 2 <= n <= 5
    effective = safe_pdarea / n if n > 0 else safe_pdarea
    return MultiQarsResult(
        is_shared=True, n_qars=n, qars_buildings=safe_list,
        subject_building_no=subject_building_no,
        effective_land_area=effective,
    )


if __name__ == '__main__':
    import sys
    print(json.dumps(detect_corner(int(sys.argv[1])), ensure_ascii=False, indent=2))
