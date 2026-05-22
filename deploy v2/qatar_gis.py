#!/usr/bin/env python3
"""
qatar_gis.py v2 — Generic Qatari property classifier and GIS wrapper.

Replaces v1's compound-centric logic with a typed asset taxonomy.
Classifies any property into one of 10 categories, then applies
type-appropriate extent-detection and reporting.

Asset taxonomy:
    TOWER             — high-rise residential/commercial (800-5000 m²)
    APARTMENT_BUILDING — low/mid-rise (400-2000 m²)
    COMPOUND_LARGE    — residential compound, 50K+ m²
    COMPOUND_SMALL    — residential compound, 10K-50K m²
    STANDALONE_VILLA  — single villa lot (300-1500 m²)
    PALACE            — luxury single estate (3K-15K m²)
    RAW_LAND          — vacant parcel of any size
    COMMERCIAL        — mall/office/mixed-use
    INDUSTRIAL        — warehouse/factory in industrial zones
    AGRICULTURAL      — farm (مزرعة)
    UNKNOWN           — when classification confidence is too low

Endpoints (unchanged from v1):
  - https://services.gisqatar.org.qa/server/rest/services/Vector/QARS_Search/MapServer/0
  - https://services.gisqatar.org.qa/server/rest/services/Vector/CadastrePlots/MapServer/0
  - https://services.gisqatar.org.qa/server/rest/services/Imagery/...
  - https://services.gisqatar.org.qa/server/rest/services/Utilities/Geometry/GeometryServer

CLI:
    python3 qatar_gis.py classify <zone> <street> <building>     # classify only
    python3 qatar_gis.py find <zone> <street> <building>         # raw lookup
    python3 qatar_gis.py plot <pin>                              # plot info
    python3 qatar_gis.py extent <pin>                            # detect full extent
    python3 qatar_gis.py report <zone> <street> <building>       # full end-to-end
    python3 qatar_gis.py imagery <pin> --years 1995,2003,...
"""

import argparse
import json
import math
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


# ============================================================
# 1. CONSTANTS
# ============================================================

GIS_BASE = "https://services.gisqatar.org.qa/server/rest/services"

# Sprint 2.16.5: GIS Qatar deprecated the public `services.gisqatar.org.qa/.../QARS_Search/MapServer`
# endpoint (reduced from ~24M records to 14 bookkeeping rows during a 2026-05-17 ETL migration).
# The active address layer is now on `khazna.gisqatar.org.qa/fed/rest/services/QARS/QARS_Point/FeatureServer/0`,
# which is what the official `gisqatar.org.qa/qarssearch/` portal uses today.
#
# We verified via direct service info that QARS_Point has the IDENTICAL schema we depend on
# (ZONE_NO, STREET_NO, BUILDING_NO, PIN, QARS, BUILDING_NO_SUBTYPE) and supports the same
# query parameters (where, outFields, f, returnGeometry, outSR with datum transformation).
#
# Heroku can reach `khazna.gisqatar.org.qa` (public DNS, IP 89.211.33.46).
KHAZNA_BASE = "https://khazna.gisqatar.org.qa/fed/rest/services"

# ─── Sprint 2.15.1: Feature flag for inline imagery ───────────────────────
# When False (default): smart() only reads from SQLite cache, never runs
# imagery analysis inline. This protects the Heroku 30s request budget.
# The cache is populated OFFLINE by prefill_cache.py and committed to git.
#
# When True: smart() runs full imagery analysis on cache miss.
# Used ONLY by:
#   - prefill_cache.py (offline batch population)
#   - CLI tools / local development
#
# This flag can also be enabled via env var: THAMMEN_ENABLE_INLINE_IMAGERY=1
# Production Heroku app should NEVER set this env var.
import os as _os
ENABLE_INLINE_IMAGERY = _os.environ.get(
    'THAMMEN_ENABLE_INLINE_IMAGERY', '0'
) == '1'

ENDPOINTS = {
    # Sprint 2.16.5: switched from services.gisqatar.org.qa/Vector/QARS_Search/MapServer
    # to khazna.gisqatar.org.qa/fed/rest/services/QARS/QARS_Point/FeatureServer/0.
    # Same schema (ZONE_NO/STREET_NO/BUILDING_NO/PIN/QARS); FeatureServer supports
    # the exact attribute query patterns this module already issues.
    'qars': f'{KHAZNA_BASE}/QARS/QARS_Point/FeatureServer/0/query',
    # Kept for diagnostics; current behavior is "depleted to 14 records".
    'qars_legacy': f'{GIS_BASE}/Vector/QARS_Search/MapServer/0/query',
    'cadastre': f'{GIS_BASE}/Vector/CadastrePlots/MapServer/0/query',
    'districts': f'{GIS_BASE}/Vector/Districts/MapServer/0/query',
    'geometry': f'{GIS_BASE}/Utilities/Geometry/GeometryServer/project',
    # Sprint 2.21.0.7: official land-use class (RULEID) + permitted BUILDING_HEIGHT.
    'landuse': f'{GIS_BASE}/Vector/General_Landuse/MapServer/0/query',
}

IMAGERY_SERVICES = {
    1995: 'QatarOrtho_1995',
    2003: 'QatarSatelitte_2003',
    2004: 'QatarOrtho_2004',
    2010: 'QatarSatelitte_2010',
    2012: 'QatarSatelitte_2012',
    2017: 'QatarSatelitte_2017',
    2019: 'QatarSatelitte_2019',
    2021: 'QatarSatelitte_2021',
    2024: 'QatarSatelitte2024',
}

_SERVICE_INFO_CACHE = {}

TILE_SIZE = 512
DEFAULT_TARGET_RES = 0.265

# Asset-type classification thresholds (m²)
# These are STARTING POINTS based on Qatar market norms; classifier
# combines them with shape, PD_NO, and zone evidence.
TYPICAL_AREAS = {
    'TINY':              (0,       300),    # too small for any real asset
    'STANDALONE_VILLA':  (300,     1500),
    'APARTMENT_BUILDING':(400,     2000),
    'TOWER':             (800,     5000),
    'PALACE':            (3000,    15000),
    'COMPOUND_SMALL':    (10000,   50000),
    'COMPOUND_LARGE':    (50000,   500000),
    'AGRICULTURAL':      (10000,   500000),
}


# ============================================================
# 2. DATA CLASSES
# ============================================================

class AssetType(str, Enum):
    TOWER = 'tower'
    APARTMENT_BUILDING = 'apartment_building'
    COMPOUND_LARGE = 'compound_large'
    COMPOUND_SMALL = 'compound_small'
    STANDALONE_VILLA = 'standalone_villa'
    PALACE = 'palace'
    RAW_LAND = 'raw_land'
    COMMERCIAL = 'commercial'
    INDUSTRIAL = 'industrial'
    AGRICULTURAL = 'agricultural'
    UNKNOWN = 'unknown'


@dataclass
class PropertyLocation:
    zone: int
    street: int
    building: int
    pin: int
    qars: str
    plot_no_old: Optional[int]
    lon: float
    lat: float
    electricity_no: Optional[int]
    water_no: Optional[int]
    qtel_id: Optional[int]
    building_subtype: Optional[int]


@dataclass
class PolygonShape:
    """Geometric analysis of a parcel polygon."""
    vertex_count: int                  # outer ring vertices (last == first)
    is_rectangular: bool               # 4 vertices, mostly orthogonal
    is_irregular: bool                 # >5 vertices OR non-convex
    convex_hull_ratio: float           # actual area / convex hull area; 1.0 = convex
    aspect_ratio: float                # min/max bounding box dimension; near 1.0 = square-ish
    irregularity_warning: Optional[str]


@dataclass
class PlotInfo:
    pin: int
    pdarea: float
    pd_no: str
    cdst_key: int
    ref_number: Optional[str]
    polygon_4326: list
    polygon_2932: list
    bbox_4326: tuple
    is_unsubdivided: bool
    shape: PolygonShape


@dataclass
class AssetClassification:
    """Result of classifying a single plot into an asset type."""
    asset_type: AssetType
    confidence: str                    # 'high' | 'medium' | 'low'
    reasons: list                      # evidence for this classification
    flags: list                        # warnings or caveats
    alternative_types: list            # other plausible classifications, ranked


@dataclass
class AssetExtent:
    """The full physical extent of an asset (may span multiple parcels)."""
    primary_pin: int
    included_pins: list
    plots: list                        # list of PlotInfo
    total_area_m2: float
    combined_bbox_4326: tuple
    asset_type: AssetType
    detection_confidence: str          # 'high' | 'medium' | 'low'
    notes: list


@dataclass
class ConstructionYearEstimate:
    earliest_built_year: int
    latest_vacant_year: int
    confidence_years: int
    summary: str


@dataclass
class DistrictInfo:
    """Administrative district from GIS — the sole source of truth for area name."""
    dist_no: int
    aname: str                         # Arabic name (GIS authoritative)
    ename: str                         # English name
    code: Optional[str]


@dataclass
class PropertyReport:
    location: PropertyLocation
    plot: PlotInfo
    classification: AssetClassification
    extent: AssetExtent
    construction: Optional[ConstructionYearEstimate]
    district: Optional[DistrictInfo]
    flags: list


# ============================================================
# 3. HELPERS
# ============================================================

def _http_get_json(url, params=None, timeout=30):
    # Sprint 2.21.0.7: GET by default, but fall back to POST when the query
    # string would overflow the URL length limit (HTTP 414). Large ESRI
    # geometries — projecting a many-vertex polygon (Pearl/Lusail master plots)
    # or a future QARS-in-polygon query — exceed GET limits; ESRI /query and the
    # Geometry server accept the same params via form-encoded POST. Small queries
    # stay GET → zero behaviour change. (Audit-driven defensive fix; Anas-approved.)
    headers = {'User-Agent': 'qatar-gis-py/2.0'}
    if params:
        _encoded = urllib.parse.urlencode(params)
        _get_url = f'{url}?{_encoded}'
        if len(_get_url) > 2000:
            req = urllib.request.Request(
                url, data=_encoded.encode('utf-8'), headers=headers)  # data => POST
        else:
            req = urllib.request.Request(_get_url, headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            if raw[:3] == b'\xef\xbb\xbf':
                raw = raw[3:]
            return json.loads(raw.decode('utf-8'))
        except urllib.error.URLError as e:
            last_err = e
            # Handle SSL cert "not yet valid" (system clock skew) with fallback
            if 'CERTIFICATE_VERIFY_FAILED' in str(e):
                import ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                try:
                    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                        raw = resp.read()
                    if raw[:3] == b'\xef\xbb\xbf':
                        raw = raw[3:]
                    return json.loads(raw.decode('utf-8'))
                except Exception as e2:
                    last_err = e2
            import time
            time.sleep(2 ** attempt)
    raise last_err


def _project_2932_to_4326(points_2932):
    if not points_2932:
        return []
    geoms = {
        'geometryType': 'esriGeometryPoint',
        'geometries': [{'x': p[0], 'y': p[1]} for p in points_2932],
    }
    res = _http_get_json(ENDPOINTS['geometry'], {
        'inSR': 2932, 'outSR': 4326, 'f': 'json',
        'geometries': json.dumps(geoms),
    })
    return [[g['x'], g['y']] for g in res.get('geometries', [])]


def _project_4326_to_2932(points_4326):
    if not points_4326:
        return []
    geoms = {
        'geometryType': 'esriGeometryPoint',
        'geometries': [{'x': p[0], 'y': p[1]} for p in points_4326],
    }
    res = _http_get_json(ENDPOINTS['geometry'], {
        'inSR': 4326, 'outSR': 2932, 'f': 'json',
        'geometries': json.dumps(geoms),
    })
    return [[g['x'], g['y']] for g in res.get('geometries', [])]


def _service_info(year):
    if year in _SERVICE_INFO_CACHE:
        return _SERVICE_INFO_CACHE[year]
    slug = IMAGERY_SERVICES.get(year)
    if not slug:
        raise ValueError(f'No imagery service for year {year}')
    url = f'{GIS_BASE}/Imagery/{slug}/MapServer'
    data = _http_get_json(url, {'f': 'json'})
    ti = data.get('tileInfo', {})
    origin = ti.get('origin', {})
    info = {
        'origin_x': origin.get('x'),
        'origin_y': origin.get('y'),
        'tile_size': ti.get('rows', TILE_SIZE),
        'lods': {lod['level']: lod['resolution'] for lod in ti.get('lods', [])},
    }
    _SERVICE_INFO_CACHE[year] = info
    return info


def _best_lod(year, target_res=DEFAULT_TARGET_RES):
    info = _service_info(year)
    lods = info['lods']
    if not lods:
        return None
    eligible = [(lvl, res) for lvl, res in lods.items() if res <= target_res * 1.5]
    if not eligible:
        return max(lods, key=lambda l: -lods[l])
    return min(eligible, key=lambda lr: abs(lr[1] - target_res))[0]


def _tile_coord(x_2932, y_2932, lod, year):
    info = _service_info(year)
    res = info['lods'].get(lod)
    if res is None:
        raise ValueError(f'LOD {lod} not available for year {year}')
    ox, oy = info['origin_x'], info['origin_y']
    tile_size_meters = res * TILE_SIZE
    col = int((x_2932 - ox) / tile_size_meters)
    row = int((oy - y_2932) / tile_size_meters)
    return col, row


# ============================================================
# 4. SHAPE ANALYSIS
# ============================================================

def _polygon_area_2932(points):
    """Shoelace formula. Returns absolute area in m²."""
    n = len(points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def _convex_hull_2932(points):
    """Andrew's monotone chain convex hull. Returns hull points in CCW order."""
    pts = sorted(set((round(p[0], 2), round(p[1], 2)) for p in points))
    if len(pts) < 3:
        return list(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def _bbox_aspect_ratio(points):
    """Min/max ratio of bounding box. Near 1.0 = square-ish."""
    if not points:
        return 1.0
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    if w == 0 or h == 0:
        return 0.0
    return min(w, h) / max(w, h)


def analyze_polygon_shape(polygon_2932) -> PolygonShape:
    """
    Analyze geometric properties of a parcel polygon.

    Returns a PolygonShape with vertex count, rectangularity check,
    convex-hull ratio (1.0 = perfectly convex), and aspect ratio.

    The irregularity warning is the most actionable output: it tells
    a user to look harder for missing neighbor parcels.
    """
    # ESRI returns polygons with last point == first; strip duplicate
    pts = polygon_2932[:-1] if len(polygon_2932) > 3 and polygon_2932[0] == polygon_2932[-1] else list(polygon_2932)
    n = len(pts)

    # Hull-ratio check: hull_area should equal polygon_area for a convex shape
    poly_area = _polygon_area_2932(pts)
    hull_pts = _convex_hull_2932(pts)
    hull_area = _polygon_area_2932(hull_pts)
    hull_ratio = poly_area / hull_area if hull_area > 0 else 1.0
    aspect = _bbox_aspect_ratio(pts)

    is_rectangular = (n == 4) and (hull_ratio > 0.97)
    is_irregular = (n > 5) or (hull_ratio < 0.92)

    warning = None
    if is_irregular:
        if hull_ratio < 0.85:
            warning = (
                f'Polygon is significantly non-convex (hull ratio={hull_ratio:.2f}). '
                f'Qatar plots are typically rectangular. The seed may have an adjacent '
                f'parcel that completes its shape — search for small neighboring plots.'
            )
        elif n > 5:
            warning = (
                f'Polygon has {n} vertices (rectangular plots have 4). '
                f'This suggests either a complex original boundary or a missing '
                f'neighbor parcel. Visual verification recommended.'
            )

    return PolygonShape(
        vertex_count=n,
        is_rectangular=is_rectangular,
        is_irregular=is_irregular,
        convex_hull_ratio=round(hull_ratio, 3),
        aspect_ratio=round(aspect, 3),
        irregularity_warning=warning,
    )


# ============================================================
# 5. ASSET CLASSIFIER
# ============================================================

# ─── Sprint 2.16.14: Bug A11 — Zoning cross-check helpers ───
# Empirical context (2026-05-19 audit, 22 government/business landmarks):
#   - 9.1% of GOVERNMENT-category landmarks have a residential-looking
#     BUILDING_NO_SUBTYPE in QARS_Point (last surveyed 2010-2012) but
#     sit in a clearly commercial zone today. Example: PIN 61050014
#     (61/875/20, Public Works Authority) → subtype=6 (Flats) yet
#     Zoning=CCC (Central Commercial Core).
#   - 0% of BUSINESS or FINANCE landmarks had this issue.
#   - Fix: emit a non-blocking flag downstream when a residential
#     subtype (1/6/11) sits inside a clearly non-residential zone.
#     We do NOT change asset_type — the user (or a domain expert)
#     decides whether to re-evaluate as commercial.
RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK = frozenset({1, 6, 11})  # Villa, ApartBldg, Tower
_NON_RES_ZONING_TOKENS = frozenset({'CCC', 'COM', 'CF', 'SCZ', 'TU', 'LFR', 'LInd', 'IND'})


# ── Sprint 2.21.0.7: General_Landuse RULEID coded-value domain ──────────────
# Authoritative map fetched from the layer's own coded-value domain
# (probe_ruleid_domain.py) — NOT guessed. Each code → (en_label, ar_label).
# Used on the PIN/land path to sanity-check the user's "this is land" hint
# against the parcel's official land-use class.
RULEID_LABELS = {
    1:  ('Single-Family Residential', 'سكني — فلل/بيوت'),
    2:  ('Multi-Family Residential',  'سكني — عمارات/مجمعات'),
    3:  ('Retail / Commercial',       'تجاري — محلات تجزئة'),
    4:  ('Services / Offices',        'خدمات / مكاتب'),
    5:  ('Wholesale',                 'تجارة جملة'),
    6:  ('Light Industry',            'صناعة خفيفة'),
    7:  ('Medium Industry',           'صناعة متوسطة'),
    8:  ('Heavy Industry',            'صناعة ثقيلة'),
    9:  ('Extractive Industry',       'صناعة استخراجية'),
    10: ('Educational',               'تعليمي'),
    11: ('Health',                    'صحي'),
    12: ('Governmental',              'حكومي'),
    13: ('Community / Cultural',      'مجتمعي / ثقافي'),
    14: ('Religious',                 'ديني'),
    15: ('Open Space / Recreation',   'مساحات مفتوحة / ترفيهي'),
    16: ('Sports',                    'رياضي'),
    17: ('Transportation',            'نقل ومواصلات'),
    18: ('Utilities',                 'مرافق / بنية تحتية'),
    19: ('Agricultural',              'زراعي'),
    20: ('Vacant Land',               'أرض فضاء'),
    21: ('Special Use',               'استخدام خاص'),
    22: ('Tourism',                   'سياحي'),
    23: ('Mixed Use',                 'استخدام مختلط'),
    24: ('Unknown',                   'غير محدد'),
    -1: ('Free Representation',       'تمثيل حر'),
}
# Residential land-use classes → proceed with the raw_land valuation path.
RULEID_RESIDENTIAL = frozenset({1, 2, 20})
# Mixed-use → master-planned developments, not individual market lots → reject
# (Sprint 2.21.0.7 DECISION 2).
RULEID_MIXED_USE = frozenset({23})
# Agricultural → existing AssetType.AGRICULTURAL (handled by V1_OUT_OF_SCOPE).
RULEID_AGRICULTURAL = frozenset({19})
# Non-residential classes that DO have a tradable land value → value with a bold
# disclaimer (Sprint 2.21.0.7 DECISION 1, "accept with warning").
RULEID_WARN = frozenset({3, 4, 22})
# Non-residential classes with no meaningful residential comparable → hard reject
# (Sprint 2.21.0.7 DECISION 1, "reject"). 5-18 + 21.
RULEID_REJECT = frozenset({5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 21})
# No-signal codes (and None) → fall through to the geometric guard, no flag.
RULEID_NO_SIGNAL = frozenset({24, -1})


def _qars_count_in_polygon(ring, timeout: float = 8.0):
    """Count QARS_Point features INSIDE a parcel polygon (tight polygon-intersect,
    not bbox). >0 ⇒ a surveyed building exists ON the plot ⇒ it is NOT bare land.

    Returns int count, or None when the call fails (caller treats None as
    "unknown" → does not block). Large many-vertex rings overflow the GET URL
    limit, so `_http_get_json` transparently switches to POST (Rule #48).
    """
    if not ring:
        return None
    try:
        geom = json.dumps({'rings': [ring], 'spatialReference': {'wkid': 4326}})
        res = _http_get_json(ENDPOINTS['qars'], {
            'geometry': geom, 'geometryType': 'esriGeometryPolygon',
            'inSR': '4326', 'spatialRel': 'esriSpatialRelIntersects',
            'returnCountOnly': 'true', 'f': 'json',
        }, timeout=timeout)
        c = res.get('count')
        return int(c) if c is not None else None
    except Exception:
        return None


def _landuse_at(lon, lat, timeout: float = 6.0):
    """Land-use class + permitted building height at a point, from
    Vector/General_Landuse/MapServer/0.

    Returns (ruleid:int|None, building_height:str|None). On no coverage or any
    failure → (None, None) so the caller falls back to geometry gracefully.
    """
    if lon is None or lat is None:
        return None, None
    try:
        geom = json.dumps({'x': lon, 'y': lat, 'spatialReference': {'wkid': 4326}})
        res = _http_get_json(ENDPOINTS['landuse'], {
            'geometry': geom, 'geometryType': 'esriGeometryPoint',
            'inSR': '4326', 'spatialRel': 'esriSpatialRelIntersects',
            'outFields': 'RULEID,BUILDING_HEIGHT', 'returnGeometry': 'false',
            'f': 'json',
        }, timeout=timeout)
        feats = res.get('features') or []
        if feats:
            attrs = feats[0].get('attributes') or {}
            rid = attrs.get('RULEID')
            bh = attrs.get('BUILDING_HEIGHT')
            return (int(rid) if rid is not None else None), (str(bh) if bh not in (None, '') else None)
    except Exception:
        pass
    return None, None


def _nonres_category_ar(ruleid):
    """Sprint 2.21.0.7.1: short Arabic category word for the 'consult a specialist
    valuer for {category} properties' line in the built-non-residential reject."""
    if ruleid in (3, 4, 5, 22):
        return 'التجارية'
    if ruleid in (6, 7, 8, 9):
        return 'الصناعية'
    if ruleid == 23:
        return 'المختلطة الاستخدام'
    if ruleid == 21:
        return 'الخاصة'
    if ruleid == 19:
        return 'الزراعية'
    return 'المتخصصة'


def _reality_flag(action, reason, ruleid, rid_en, rid_ar, qcount, bheight, area, message_ar):
    """Sprint 2.21.0.7: encode an asset-type reality-check result as a single
    flag string (prefix + JSON payload), mirroring the A11 `subtype_zoning_mismatch:`
    convention. evaluate_unified parses it into a structured response field.

    action: 'stop' (built parcel) | 'reject' (out of scope) | 'warn' (value + disclaimer)
    """
    payload = {
        'kind': 'asset_type_reality',
        'action': action,
        'reason': reason,
        'ruleid': ruleid,
        'ruleid_label_en': rid_en,
        'ruleid_label_ar': rid_ar,
        'qars_in_polygon': qcount,
        'building_height': bheight,
        'area_m2': round(area, 1) if area is not None else None,
        'message_ar': message_ar,
    }
    return 'asset_type_reality:' + json.dumps(payload, ensure_ascii=False)


def _is_non_residential_zone(zoning) -> bool:
    """Detect zoning codes that contradict a residential subtype.

    Confirmed non-residential single-token codes:
        CCC  Central Commercial Core
        COM  Commercial
        CF   Community Facility
        SCZ  Special Commercial Zone
        TU   Tourism Use
        LFR  Light Front Retail
        LInd Light Industrial
        IND  Industrial
    Mixed-Use codes (`MU1 G+2`, `MU2 G+5`, `MU3 G+3`, etc.) lean commercial.
    """
    if not zoning:
        return False
    z = str(zoning).strip()
    if z in _NON_RES_ZONING_TOKENS:
        return True
    if z.startswith('MU'):
        return True
    return False


def _fetch_zoning_at_point(lat, lon, timeout: float = 4.0):
    """Lightweight spatial query to Vector/Zoning/MapServer/0.

    Returns the ZONING code (e.g. 'CCC', 'R1', 'MU2 G+5') or None.
    Used as a defensive fallback inside classify_asset when callers
    haven't pre-fetched the zoning. Safe to fail silently — the
    cross-check just becomes a no-op when this returns None.
    """
    try:
        import urllib.request, urllib.parse, json as _json
        geom = _json.dumps({
            'x': lon, 'y': lat,
            'spatialReference': {'wkid': 4326},
        })
        params = {
            'geometry': geom,
            'geometryType': 'esriGeometryPoint',
            'inSR': '4326',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': 'ZONING',
            'f': 'json',
        }
        url = (
            'https://services.gisqatar.org.qa/server/rest/services/'
            'Vector/Zoning/MapServer/0/query?' + urllib.parse.urlencode(params)
        )
        req = urllib.request.Request(url, headers={'User-Agent': 'Thammen/2.16.14'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = _json.loads(r.read().decode('utf-8', errors='replace'))
            feats = data.get('features') or []
            if feats:
                return (feats[0].get('attributes') or {}).get('ZONING')
    except Exception:
        pass
    return None


def classify_asset(plot: PlotInfo, location_metadata=None,
                   input_mode=None) -> AssetClassification:
    """
    Classify a plot into an AssetType based on geometric and metadata
    evidence. Imagery is NOT used here (it would require fetching tiles
    and analyzing them — handled separately).

    The output includes alternative classifications when confidence is low,
    so downstream code can ask the user to confirm.

    location_metadata: optional dict with extra context.
    Sprint 2.16.6: now consumes `building_subtype` (from QARS_Point) as the
    primary classification signal when available. Falls back to the legacy
    area-based heuristic when subtype is missing or unknown.

    Sprint 2.21.0: `input_mode='land'` is the explicit "this is a bare land
    parcel" signal (set when the user enters a PIN via the land tab). Geometry
    cannot distinguish bare land from a villa lot, so this hint is honoured for
    typical land sizes — BUT geometry still OVERRIDES when conclusive (an
    oversized parcel is a compound, not raw land). The hint runs only when no
    mapped QARS subtype is present; `input_mode=None` (every legacy caller)
    leaves all existing behaviour byte-for-byte unchanged.
    """
    area = plot.pdarea
    pd_no = plot.pd_no
    is_unsubdivided = plot.is_unsubdivided
    shape = plot.shape

    reasons = []
    flags = []
    alternatives = []

    # === Branch 0 (Sprint 2.16.6): BUILDING_NO_SUBTYPE from QARS_Point ===
    # The new khazna QARS_Point service exposes the official building-type
    # classification per QARS point. This is authoritative when present —
    # it replaces the area-based heuristic that miscategorized ~15,881
    # Qatar polygons (3K-10K m² → "palace") including all Lusail/West Bay
    # towers and shopping complexes.
    subtype = (location_metadata or {}).get('building_subtype')
    if subtype is not None and subtype != 0:
        # Map known subtype codes to AssetType. Subtypes not mapped here fall
        # through to the area heuristic (defensive — never wrong-classify).
        SUBTYPE_LABEL = {
            1: "Villa/House", 2: "Compound with Villas",
            3: "Compound with Villas and Flats", 4: "Shopping Complex",
            5: "Building Under Construction", 6: "Building with Flats",
            8: "Sports Club", 9: "Health Centre/Hospital", 10: "Masjid",
            11: "Tower", 12: "Park", 13: "Commercial",
            14: "IZBA", 15: "FARM", 16: "Desert House", 17: "Chalet",
            18: "Stone Crusher", 19: "Metro", 99: "Others",
        }
        SUBTYPE_TO_ASSET = {
            1:  AssetType.STANDALONE_VILLA,    # Villa/House
            2:  AssetType.COMPOUND_SMALL,       # Compound w/ Villas — extent detection
                                                # later can promote to COMPOUND_LARGE
            3:  AssetType.COMPOUND_SMALL,       # Compound w/ Villas+Flats
            4:  AssetType.COMMERCIAL,           # Shopping Complex
            6:  AssetType.APARTMENT_BUILDING,   # Building with Flats
            11: AssetType.TOWER,                # Tower (the A1 fix)
            13: AssetType.COMMERCIAL,           # Commercial
        }
        asset_type = SUBTYPE_TO_ASSET.get(subtype)
        if asset_type is not None:
            label = SUBTYPE_LABEL.get(subtype, f'subtype={subtype}')

            # ─── Sprint 2.16.14: Bug A11 — Zoning cross-check ───
            # QARS_Point's BUILDING_NO_SUBTYPE was last surveyed 2010-2012
            # for most parcels. When a building has been converted to
            # commercial/government use since then (example: PIN 61050014
            # = Public Works Authority, subtype=6 "Flats", Zoning=CCC),
            # the residential subtype is stale and misleading. We surface
            # this as a non-blocking flag so the user can confirm.
            _zon_flags = []
            _meta_dict = location_metadata or {}
            if subtype in RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK:
                zoning_val = _meta_dict.get('zoning')
                if zoning_val is None:
                    # Caller didn't pre-fetch zoning — try a lightweight
                    # spatial query as a defensive fallback. Skipped silently
                    # if lat/lon missing or the GIS call fails.
                    _lat = _meta_dict.get('lat')
                    _lon = _meta_dict.get('lon')
                    if _lat is not None and _lon is not None:
                        zoning_val = _fetch_zoning_at_point(_lat, _lon)
                if _is_non_residential_zone(zoning_val):
                    _zon_flags.append(
                        f'subtype_zoning_mismatch: QARS subtype={subtype} ({label}) '
                        f'يقترح استخداماً سكنياً، لكن المنطقة منظَّمة كـ "{zoning_val}" '
                        f'(غير سكني). بيانات QARS قديمة (آخر مسح غالباً 2010-2012). '
                        f'تحقق من الاستخدام الفعلي قبل الاعتماد على هذا التصنيف.'
                    )

            return AssetClassification(
                asset_type=asset_type,
                # Downgrade confidence when there is a contradiction —
                # downstream code can use this to pick the right brief.
                confidence='medium' if _zon_flags else 'high',
                reasons=[
                    f'BUILDING_NO_SUBTYPE={subtype} ({label}) from QARS_Point',
                    f'PDAREA {area:,.0f} m² recorded for reference',
                ],
                flags=_zon_flags,
                alternative_types=[
                    AssetType.COMMERCIAL.value,
                ] if _zon_flags else [],
            )
        # Subtype is known but not in the mapping (e.g. 5=Under Construction,
        # 8=Sports Club, 14=IZBA, 15=FARM, 16=Desert House, 17=Chalet,
        # 18=Stone Crusher, 19=Metro, 99=Others). Falling through to the
        # area heuristic for these — they're rare and don't change the
        # 99% case. May be enhanced in a future Sprint.


    # === Sprint 2.21.0: explicit land input (PIN / land tab) ===
    # Reached only when no mapped QARS subtype was found above. The user has
    # declared this is bare land; honour it for typical sizes, but let geometry
    # override when the parcel is clearly a compound.
    #
    # === Sprint 2.21.0.7: Asset Type Reality Check ===
    # The user's "this is land" hint is wrong often enough to matter (a PIN may
    # already have a building on it, or be governmental/commercial/special-use).
    # Before trusting the hint, consult two authoritative GIS signals we already
    # own. Precedence (DECISION 4): (1) QARS-in-polygon building check >
    # (2) RULEID land-use class > (3) geometric guard (legacy, last resort).
    # All signals are defensive — a failed/empty GIS call returns None and we
    # fall through to the legacy geometric guard with no flag (graceful, e.g.
    # parcels with no General_Landuse coverage).
    if input_mode == 'land':
        # Pre-compute the polygon centroid (for the point land-use query).
        _ring = plot.polygon_4326 or []
        _cx = sum(p[0] for p in _ring) / len(_ring) if _ring else None
        _cy = sum(p[1] for p in _ring) / len(_ring) if _ring else None

        # Allow callers to pre-supply the signals (tests / batch); else fetch.
        _md = location_metadata or {}
        _qcount = _md.get('qars_in_polygon')
        if _qcount is None:
            _qcount = _qars_count_in_polygon(_ring)
        _ruleid = _md.get('landuse_ruleid')
        _bheight = _md.get('building_height')
        if _ruleid is None:
            _ruleid, _bheight = _landuse_at(_cx, _cy)
        _rid_en, _rid_ar = RULEID_LABELS.get(_ruleid, ('Unknown', 'غير محدد'))

        # ── P1: a surveyed building exists ON the plot → it is NOT bare land.
        #    Sprint 2.21.0.7.1 (DECISION Q1): split by land-use.
        #    - residential / vacant / unknown RULEID → STOP "use address tab"
        #      (the address/villa flow can value the building) — DECISION 5.
        #    - CONFIRMED non-residential RULEID → REJECT immediately, because the
        #      address tab is a dead-end (it also rejects non-residential), so
        #      "use address tab" would just waste the user's time.
        if isinstance(_qcount, int) and _qcount > 0:
            _disc = (
                f'\n\nالمعلومات المكتشفة:\n'
                f'- المساحة: {area:,.0f} م²\n'
                f'- التصنيف: {_rid_ar}\n'
                f'- الارتفاع المسموح: {_bheight or "غير متاح"}\n'
                f'- البناء: موجود ✓'
            )
            _nonres_confirmed = (_ruleid in RULEID_REJECT or _ruleid in RULEID_WARN
                                 or _ruleid in RULEID_MIXED_USE or _ruleid in RULEID_AGRICULTURAL)
            if _nonres_confirmed:
                _cat = _nonres_category_ar(_ruleid)
                _msg = (
                    f'⚠ هذه القطعة (PIN {plot.pin}) عليها مبنى + مصنّفة {_rid_ar} '
                    f'(RULEID={_ruleid}).\n'
                    f'العقارات {_rid_ar} خارج نطاق Thammen حالياً.\n'
                    f'استشر مُقيِّم متخصّص للعقارات {_cat}.'
                    + _disc
                )
                return AssetClassification(
                    asset_type=AssetType.UNKNOWN, confidence='high',
                    reasons=[f'QARS-in-polygon={_qcount} + RULEID={_ruleid} ({_rid_en}) — '
                             f'non-residential building, out of scope'],
                    flags=[_reality_flag('reject', 'non_residential_built', _ruleid, _rid_en,
                                         _rid_ar, _qcount, _bheight, area, _msg)],
                    alternative_types=[],
                )
            # residential / vacant {20} / unknown {24,-1,None} → stop, not reject
            # (these are NOT confirmed non-residential — the building may be a
            # villa/apartment the address flow can value).
            _msg = (
                f'⚠ هذه القطعة (PIN {plot.pin}) عليها مبنى — ليست أرض فضاء.'
                + _disc
                + f"\n\nلتقييم العقار المبني عليها:\n"
                  f"استخدم تبويب 'العنوان' مع Zone/Street/Building.\n\n"
                  f'النظام لا يحوّل تلقائياً لضمان وعي المستخدم بالاكتشاف.'
            )
            return AssetClassification(
                asset_type=AssetType.UNKNOWN, confidence='high',
                reasons=[f'QARS-in-polygon={_qcount} — a surveyed building exists on PIN {plot.pin}',
                         f'RULEID={_ruleid} ({_rid_en}); PDAREA {area:,.0f} m²'],
                flags=[_reality_flag('stop', 'building_present', _ruleid, _rid_en, _rid_ar,
                                     _qcount, _bheight, area, _msg)],
                alternative_types=[],
            )

        # ── P2: land-use class (RULEID). Non-residential overrides the geometric
        #    guard (DECISION 4) so a large governmental/commercial parcel is NOT
        #    silently classified as a residential compound.
        if _ruleid in RULEID_REJECT:
            _msg = (f'هذه الأرض مصنّفة {_rid_ar} — خارج النطاق الحالي لـ Thammen. '
                    f'استشر مُقيِّم متخصّص.')
            return AssetClassification(
                asset_type=AssetType.UNKNOWN, confidence='high',
                reasons=[f'RULEID={_ruleid} ({_rid_en}) — non-residential, no residential comparable'],
                flags=[_reality_flag('reject', 'non_residential', _ruleid, _rid_en, _rid_ar,
                                     _qcount, _bheight, area, _msg)],
                alternative_types=[],
            )
        if _ruleid in RULEID_MIXED_USE:
            _msg = ('هذه قطعة ضمن تطوير عقاري مختلط. هذه الفئة لا تباع في السوق '
                    'المفتوح كأرض فردية. خارج نطاق التقييم.')
            return AssetClassification(
                asset_type=AssetType.UNKNOWN, confidence='high',
                reasons=[f'RULEID={_ruleid} ({_rid_en}) — mixed-use master-planned development'],
                flags=[_reality_flag('reject', 'mixed_use', _ruleid, _rid_en, _rid_ar,
                                     _qcount, _bheight, area, _msg)],
                alternative_types=[],
            )
        if _ruleid in RULEID_AGRICULTURAL:
            return AssetClassification(
                asset_type=AssetType.AGRICULTURAL, confidence='high',
                reasons=[f'RULEID={_ruleid} ({_rid_en}) — agricultural land-use'],
                flags=flags, alternative_types=[AssetType.RAW_LAND],
            )
        if _ruleid in RULEID_WARN:
            # Tradable land value exists but residential comparables are a rough
            # proxy → value WITH a bold disclaimer (DECISION 1, "accept with
            # warning"). RULEID overrode the geometric guard, so return raw_land.
            _msg = (f'⚠ هذه الأرض مصنّفة {_rid_ar}. التقدير يستخدم مقارنات عامة. '
                    f'السعر الفعلي قد يختلف 2-5 أضعاف حسب: الموقع على الشارع، '
                    f'مسافة الواجهة، التطوير المسموح. '
                    f'يُنصح بـ مُقيِّم متخصّص للقرارات النهائية.')
            return AssetClassification(
                asset_type=AssetType.RAW_LAND, confidence='medium',
                reasons=[f'RULEID={_ruleid} ({_rid_en}) — non-residential but tradable land',
                         f'PDAREA {area:,.0f} m²; valued with disclaimer'],
                flags=[_reality_flag('warn', 'non_residential', _ruleid, _rid_en, _rid_ar,
                                     _qcount, _bheight, area, _msg)],
                alternative_types=[],
            )

        # RULEID ∈ {1,2,20}, no-signal {24,-1}, or None (no coverage) → trust the
        # land hint and use the legacy geometric guard (residential context).
        if area >= 50000:
            return AssetClassification(
                asset_type=AssetType.COMPOUND_LARGE, confidence='high',
                reasons=[f'PDAREA {area:,.0f} m² ≥ 50,000 — too large for raw land; '
                         f'treated as large compound (geometric guard overrides land hint)',
                         f'RULEID={_ruleid} ({_rid_en})'],
                flags=flags,
                alternative_types=[AssetType.AGRICULTURAL] if area > 100000 else [],
            )
        if area >= 15000:
            return AssetClassification(
                asset_type=AssetType.COMPOUND_SMALL, confidence='medium',
                reasons=[f'PDAREA {area:,.0f} m² ≥ 15,000 — likely a compound, not a single '
                         f'raw-land plot (geometric guard overrides land hint)',
                         f'RULEID={_ruleid} ({_rid_en})'],
                flags=flags,
                alternative_types=[AssetType.RAW_LAND],
            )
        return AssetClassification(
            asset_type=AssetType.RAW_LAND,
            confidence='high' if shape.is_rectangular else 'medium',
            reasons=[f'PDAREA {area:,.0f} m² accepted as raw land (explicit land/PIN input)',
                     f'RULEID={_ruleid} ({_rid_en}); PD_NO={pd_no}'],
            flags=flags,
            alternative_types=[AssetType.STANDALONE_VILLA],
        )

    # === Branch 1: very small plot ===
    if area < 200:
        return AssetClassification(
            asset_type=AssetType.UNKNOWN,
            confidence='low',
            reasons=[f'Area {area:,.0f} m² is too small for any standard asset type'],
            flags=['May be a survey artifact or right-of-way strip'],
            alternative_types=[],
        )

    # === Branch 2: huge unsubdivided plot ===
    # Strong signal for COMPOUND_LARGE
    if area >= 50000 and is_unsubdivided:
        reasons.append(f'PDAREA {area:,.0f} m² ≥ 50,000 and PD_NO=0 (unsubdivided)')
        reasons.append('Strong signature of a large compound parcel')
        if shape.irregularity_warning:
            flags.append(shape.irregularity_warning)
            flags.append('Compound may extend further — check adjacent small parcels')
        return AssetClassification(
            asset_type=AssetType.COMPOUND_LARGE,
            confidence='high',
            reasons=reasons, flags=flags,
            alternative_types=[AssetType.AGRICULTURAL] if area > 100000 else [],
        )

    # === Branch 3: medium unsubdivided plot ===
    if 10000 <= area < 50000 and is_unsubdivided:
        reasons.append(f'PDAREA {area:,.0f} m² in 10K-50K range and PD_NO=0')
        reasons.append('Likely a small-medium compound')
        if shape.irregularity_warning:
            flags.append(shape.irregularity_warning)
        return AssetClassification(
            asset_type=AssetType.COMPOUND_SMALL,
            confidence='medium',
            reasons=reasons, flags=flags,
            alternative_types=[AssetType.AGRICULTURAL, AssetType.PALACE],
        )

    # === Branch 4: large subdivided plot — likely already-fragmented ===
    if area >= 10000 and not is_unsubdivided:
        reasons.append(f'PDAREA {area:,.0f} m² but PD_NO={pd_no} (subdivided)')
        reasons.append(
            'A subdivided large parcel typically means commercial, industrial, '
            'or a previously-divided estate'
        )
        flags.append(
            'Large subdivided plots can be ambiguous. Imagery and zoning lookup recommended.'
        )
        return AssetClassification(
            asset_type=AssetType.COMMERCIAL,
            confidence='low',
            reasons=reasons, flags=flags,
            alternative_types=[AssetType.AGRICULTURAL, AssetType.INDUSTRIAL, AssetType.PALACE],
        )

    # === Branch 5: palace size (3K-10K, single subdivided plot) ===
    if 3000 <= area < 10000:
        reasons.append(f'PDAREA {area:,.0f} m² in palace/large-villa range')
        if shape.is_rectangular:
            reasons.append('Rectangular shape — typical of single estate')
        return AssetClassification(
            asset_type=AssetType.PALACE,
            confidence='medium',
            reasons=reasons, flags=flags,
            alternative_types=[AssetType.COMMERCIAL, AssetType.COMPOUND_SMALL],
        )

    # === Branch 6: standalone villa (300-1500 m²) — checked FIRST in this range ===
    # Most plots in this size are villas, especially when subdivided + rectangular
    if 300 <= area < 1500:
        reasons.append(f'PDAREA {area:,.0f} m² in standard villa range')
        confidence = 'medium'
        if shape.is_rectangular:
            reasons.append('Rectangular shape — typical of villa lot')
            confidence = 'high'
        if not is_unsubdivided:
            reasons.append(f'PD_NO={pd_no} indicates a properly subdivided lot')
            confidence = 'high'
        return AssetClassification(
            asset_type=AssetType.STANDALONE_VILLA,
            confidence=confidence,
            reasons=reasons, flags=flags,
            alternative_types=[AssetType.APARTMENT_BUILDING] if area > 800 else [],
        )

    # === Branch 7: tower / large apartment (1500-3000 m²) ===
    if 1500 <= area < 3000:
        reasons.append(f'PDAREA {area:,.0f} m² in tower/large-apartment range')
        reasons.append(
            'Cannot distinguish tower from apartment building from PDAREA alone — '
            'imagery shadow analysis or zone metadata required'
        )
        flags.append('Use estimate_construction_year + imagery to verify building type')
        return AssetClassification(
            asset_type=AssetType.TOWER,
            confidence='low',
            reasons=reasons, flags=flags,
            alternative_types=[AssetType.APARTMENT_BUILDING, AssetType.COMMERCIAL, AssetType.PALACE],
        )

    # === Fallback ===
    return AssetClassification(
        asset_type=AssetType.UNKNOWN,
        confidence='low',
        reasons=[f'Area {area:,.0f} m² + PD_NO={pd_no} does not match any standard pattern'],
        flags=['Manual classification needed; check imagery and zoning'],
        alternative_types=[],
    )


# ============================================================
# 6. EXTENT DETECTION (type-aware)
# ============================================================

# Configuration per asset type. Controls how detect_extent expands the search.
EXTENT_CONFIG = {
    AssetType.COMPOUND_LARGE: {
        'expand': True,
        'search_radius_m': 500,
        'min_neighbor_area_m2': 200,
    },
    AssetType.COMPOUND_SMALL: {
        'expand': True,
        'search_radius_m': 300,
        'min_neighbor_area_m2': 200,
    },
    AssetType.PALACE: {
        # Palaces sometimes have a smaller adjacent parcel (servant quarters)
        'expand': True,
        'search_radius_m': 100,
        'min_neighbor_area_m2': 200,
        'pd_no_must_match': True,
    },
    AssetType.TOWER: {
        # Some towers have an adjacent dedicated parking parcel
        'expand': True,
        'search_radius_m': 50,
        'min_neighbor_area_m2': 500,
    },
    # Single-parcel asset types — no expansion
    AssetType.STANDALONE_VILLA: {'expand': False},
    AssetType.APARTMENT_BUILDING: {'expand': False},
    AssetType.RAW_LAND: {'expand': False},
    AssetType.COMMERCIAL: {'expand': False},
    AssetType.INDUSTRIAL: {'expand': False},
    AssetType.AGRICULTURAL: {'expand': False},
    AssetType.UNKNOWN: {'expand': False},
}


# ============================================================
# 7. MAIN CLASS
# ============================================================

class QatarGIS:
    """Public API for Qatar GIS lookups, classification, and imagery."""

    def __init__(self, cache_dir=None, verbose=False):
        if cache_dir is None:
            cache_dir = Path.home() / '.qatar_gis_cache'
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose

    def _log(self, msg):
        if self.verbose:
            print(f'[gis] {msg}', file=sys.stderr)

    # ----- Tier 1: lookups -----

    def find_property(self, zone, street, building) -> Optional[PropertyLocation]:
        params = {
            'where': f'ZONE_NO={zone} AND STREET_NO={street} AND BUILDING_NO={building}',
            'outFields': '*', 'f': 'json',
            'returnGeometry': 'true', 'outSR': 4326,
        }
        # Sprint 2.16.5: try the new khazna endpoint first; fall back to legacy
        # only if the request itself errors out (network/HTTP/JSON failure).
        # NOTE: we do NOT fall back on "0 features" — that's a legitimate
        # "address not found" answer and the legacy endpoint is depleted anyway.
        try:
            res = _http_get_json(ENDPOINTS['qars'], params)
        except Exception as e:
            self._log(f'qars primary failed ({e}); trying legacy endpoint')
            try:
                res = _http_get_json(ENDPOINTS['qars_legacy'], params)
            except Exception as e2:
                self._log(f'qars legacy also failed ({e2})')
                return None
        feats = res.get('features', [])
        if not feats:
            return None
        f = feats[0]
        a = f['attributes']
        g = f['geometry']
        return PropertyLocation(
            zone=zone, street=street, building=building,
            pin=a.get('PIN'),
            qars=a.get('QARS') or '',
            plot_no_old=a.get('PLOT_NO_OLD'),
            lon=g['x'], lat=g['y'],
            electricity_no=a.get('ELECTRICITY_NO'),
            water_no=a.get('WATER_NO'),
            qtel_id=a.get('QTEL_ID'),
            building_subtype=a.get('BUILDING_NO_SUBTYPE'),
        )

    def get_plot(self, pin) -> Optional[PlotInfo]:
        """Fetch full plot info including shape analysis."""
        params = {
            'where': f'PIN={pin}',
            'outFields': '*', 'f': 'json',
            'returnGeometry': 'true', 'outSR': 4326,
        }
        res = _http_get_json(ENDPOINTS['cadastre'], params)
        feats = res.get('features', [])
        if not feats:
            return None
        f = feats[0]
        a = f['attributes']
        g = f['geometry']
        ring_4326 = g['rings'][0] if g.get('rings') else []
        ring_2932 = _project_4326_to_2932(ring_4326) if ring_4326 else []
        lons = [p[0] for p in ring_4326]
        lats = [p[1] for p in ring_4326]
        bbox = (min(lons), min(lats), max(lons), max(lats)) if lons else (0, 0, 0, 0)
        pd_no = str(a.get('PD_NO') or '0')
        shape = analyze_polygon_shape(ring_2932) if ring_2932 else PolygonShape(0, False, False, 1.0, 1.0, None)
        return PlotInfo(
            pin=pin,
            pdarea=float(a.get('PDAREA') or 0),
            pd_no=pd_no,
            cdst_key=a.get('CDST_KEY'),
            ref_number=a.get('REF_NUMBER'),
            polygon_4326=ring_4326,
            polygon_2932=ring_2932,
            bbox_4326=bbox,
            is_unsubdivided=(pd_no == '0'),
            shape=shape,
        )

    def get_plots_in_bbox(self, min_lon, min_lat, max_lon, max_lat,
                          min_area=0) -> list:
        params = {
            'geometry': f'{min_lon},{min_lat},{max_lon},{max_lat}',
            'geometryType': 'esriGeometryEnvelope',
            'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
            'outFields': 'PIN,PDAREA,PD_NO,CDST_KEY',
            'returnGeometry': 'false', 'f': 'json',
        }
        res = _http_get_json(ENDPOINTS['cadastre'], params)
        results = []
        for f in res.get('features', []):
            a = f['attributes']
            area = float(a.get('PDAREA') or 0)
            if area >= min_area:
                results.append({
                    'pin': a.get('PIN'),
                    'pdarea': area,
                    'pd_no': str(a.get('PD_NO') or '0'),
                    'cdst_key': a.get('CDST_KEY'),
                })
        return results

    # ----- Tier 1.5: districts -----

    def get_district_at_point(self, lon, lat) -> Optional[DistrictInfo]:
        """
        Find the administrative district containing a given GPS point.

        Uses Vector/Districts/MapServer/0 — the official GIS boundary layer.
        This is the sole authority for area name. Market and MoJ may use
        different names colloquially, but GIS is what we follow.
        """
        geom = json.dumps({
            'x': lon, 'y': lat,
            'spatialReference': {'wkid': 4326},
        })
        params = {
            'geometry': geom,
            'geometryType': 'esriGeometryPoint',
            'inSR': 4326,
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': 'DIST_NO,ANAME,ENAME,CODE',
            'returnGeometry': 'false',
            'f': 'json',
        }
        res = _http_get_json(ENDPOINTS['districts'], params)
        feats = res.get('features', [])
        if not feats:
            return None
        a = feats[0]['attributes']
        return DistrictInfo(
            dist_no=a.get('DIST_NO'),
            aname=a.get('ANAME') or '',
            ename=a.get('ENAME') or '',
            code=a.get('CODE'),
        )

    def get_district(self, zone, street, building) -> Optional[DistrictInfo]:
        """Convenience: address → district lookup."""
        loc = self.find_property(zone, street, building)
        if loc is None:
            return None
        return self.get_district_at_point(loc.lon, loc.lat)

    # ----- Tier 2: classify and detect extent -----

    def classify(self, pin) -> Optional[AssetClassification]:
        """Classify a plot by PIN. Convenience wrapper."""
        plot = self.get_plot(pin)
        if plot is None:
            return None
        return classify_asset(plot)

    def detect_extent(self, seed_pin, force_type=None) -> Optional[AssetExtent]:
        """
        Find the full extent of an asset starting from one PIN.

        First classifies the asset, then applies type-specific expansion logic.
        For single-parcel asset types (villa, raw land), returns just the seed.
        For multi-parcel types (compound, palace), expands via boundary-sharing.

        force_type: override classification with a specific AssetType (advanced use).
        """
        seed = self.get_plot(seed_pin)
        if seed is None:
            return None

        classification = classify_asset(seed)
        asset_type = force_type or classification.asset_type
        config = EXTENT_CONFIG.get(asset_type, {'expand': False})
        notes = list(classification.reasons)
        notes.extend(classification.flags)

        # Single-parcel types: return seed only
        if not config.get('expand'):
            notes.append(f'Asset type {asset_type.value} is single-parcel — no expansion needed')
            return AssetExtent(
                primary_pin=seed_pin,
                included_pins=[seed_pin],
                plots=[seed],
                total_area_m2=seed.pdarea,
                combined_bbox_4326=seed.bbox_4326,
                asset_type=asset_type,
                detection_confidence=classification.confidence,
                notes=notes,
            )

        # Multi-parcel types: expand via boundary search
        return self._expand_extent(seed, asset_type, config, notes, classification.confidence)

    def _expand_extent(self, seed, asset_type, config, notes, base_confidence):
        """BFS expansion, type-aware filtering."""
        radius_m = config.get('search_radius_m', 300)
        min_neighbor_area = config.get('min_neighbor_area_m2', 200)

        # OPTIMIZATION: Use TWO search boxes:
        # - Wide box for LARGE candidates (≥10K m²) — these are clearly compound sections
        # - Tight box (just around seed bbox + small buffer) for SMALL candidates
        #   (compound annexes are physically attached, no need to search far)
        # This dramatically cuts the candidate pool for small plots.

        min_lon, min_lat, max_lon, max_lat = seed.bbox_4326

        # Wide search for large plots
        delta_wide = (radius_m / 111000) * 1.4
        wide_box = (min_lon - delta_wide, min_lat - delta_wide,
                    max_lon + delta_wide, max_lat + delta_wide)
        wide_candidates = self.get_plots_in_bbox(*wide_box, min_area=10000)

        # Tight search for small plots — only ~50m around seed bbox
        delta_tight = (50 / 111000) * 1.4
        tight_box = (min_lon - delta_tight, min_lat - delta_tight,
                     max_lon + delta_tight, max_lat + delta_tight)
        tight_candidates = self.get_plots_in_bbox(*tight_box, min_area=min_neighbor_area)
        # Keep only the small ones (large ones already covered by wide search)
        tight_small = [c for c in tight_candidates if c['pdarea'] < 10000]

        # Merge, deduplicate
        seen_pins = set()
        candidates = []
        for c in wide_candidates + tight_small:
            if c['pin'] not in seen_pins:
                seen_pins.add(c['pin'])
                candidates.append(c)

        notes.append(
            f'Stage 1: {len(wide_candidates)} large + {len(tight_small)} small candidates'
        )

        # Type-aware metadata filter
        eligible = [
            c for c in candidates
            if c['pin'] != seed.pin and self._should_include(seed, c, asset_type, config)
        ]
        notes.append(f'Stage 2: {len(eligible)} eligible by area/PD_NO rules')

        # BFS expand: fetch polygons and test boundary sharing
        included = {seed.pin: seed}
        frontier = [seed]
        cached_polygons = {}

        while frontier:
            current = frontier.pop()
            for cand in eligible:
                if cand['pin'] in included:
                    continue
                if cand['pin'] not in cached_polygons:
                    cand_plot = self.get_plot(cand['pin'])
                    cached_polygons[cand['pin']] = cand_plot
                else:
                    cand_plot = cached_polygons[cand['pin']]
                if cand_plot is None:
                    continue
                if self._polygons_share_boundary(current.polygon_2932, cand_plot.polygon_2932):
                    included[cand['pin']] = cand_plot
                    frontier.append(cand_plot)

        notes.append(f'Stage 3: {len(included)} parcels share boundary')

        plots_list = list(included.values())
        all_lons = []
        all_lats = []
        for p in plots_list:
            all_lons.extend([pt[0] for pt in p.polygon_4326])
            all_lats.extend([pt[1] for pt in p.polygon_4326])
        combined_bbox = (min(all_lons), min(all_lats), max(all_lons), max(all_lats))
        total_area = sum(p.pdarea for p in plots_list)

        if len(included) == 1:
            confidence = 'medium'
            notes.append(
                f'Only seed parcel detected. Asset is likely single-parcel; '
                f'visual verification recommended.'
            )
        else:
            confidence = 'medium'
            notes.append(
                f'Detected {len(included)} parcels totaling {total_area:,.0f} m². '
                'Visual verification via render_overlay() strongly recommended.'
            )

        if seed.shape.irregularity_warning:
            notes.append(f'Seed shape warning: {seed.shape.irregularity_warning}')

        return AssetExtent(
            primary_pin=seed.pin,
            # Sprint 2.21.0.7.1 (DECISION Q2): defensive — PIN keys may be a mix
            # of int (seed) and str (GIS attribute values), which raises
            # "TypeError: '<' not supported between int and str". key=str sorts
            # safely regardless of type. No behaviour change for uniform keys.
            included_pins=sorted(included.keys(), key=str),
            plots=plots_list,
            total_area_m2=total_area,
            combined_bbox_4326=combined_bbox,
            asset_type=asset_type,
            detection_confidence=confidence,
            notes=notes,
        )

    @staticmethod
    def _should_include(seed, cand, asset_type, config):
        """
        Type-aware inclusion rule.

        For compounds, the realistic compound-annex range is 2K-10K m².
        Plots smaller than 2K m² are nearly always individual residential
        lots (even when PD_NO=0, which is common for villa lots in Qatar).
        """
        cand_area = cand['pdarea']
        cand_unsubdivided = (cand['pd_no'] == '0')

        if asset_type in (AssetType.COMPOUND_LARGE, AssetType.COMPOUND_SMALL):
            # 1. Large parcel (≥10K m²) — likely compound section
            if cand_area >= 10000:
                return True
            # 2. Medium unsubdivided parcel (2K-10K m²) — likely compound annex
            if cand_unsubdivided and 2000 <= cand_area < 10000:
                return True
            # Exclude: small subdivided lots, far parcels, individual villa lots
            return False

        if asset_type == AssetType.PALACE:
            if config.get('pd_no_must_match') and cand_unsubdivided != seed.is_unsubdivided:
                return False
            if 0.1 <= cand_area / seed.pdarea <= 2.0:
                return True
            return False

        if asset_type == AssetType.TOWER:
            if cand_area >= 500 and cand_unsubdivided:
                return True
            return False

        return False

    @staticmethod
    def _polygons_share_boundary(poly_a_2932, poly_b_2932, threshold_m=10):
        if not poly_a_2932 or not poly_b_2932:
            return False
        nearby = 0
        for a in poly_a_2932:
            for b in poly_b_2932:
                if math.hypot(a[0] - b[0], a[1] - b[1]) <= threshold_m:
                    nearby += 1
                    if nearby >= 2:
                        return True
        return False

    # ----- Tier 3: imagery -----

    def get_tile(self, year, x_2932, y_2932, target_res=DEFAULT_TARGET_RES):
        if year not in IMAGERY_SERVICES:
            raise ValueError(f'No imagery service for year {year}')
        lod = _best_lod(year, target_res)
        if lod is None:
            raise ValueError(f'No LOD available for year {year}')
        col, row = _tile_coord(x_2932, y_2932, lod, year)
        cache_key = f'{IMAGERY_SERVICES[year]}_{lod}_{row}_{col}.jpg'
        cache_path = self.cache_dir / cache_key
        if cache_path.exists():
            return cache_path.read_bytes(), lod
        url = f'{GIS_BASE}/Imagery/{IMAGERY_SERVICES[year]}/MapServer/tile/{lod}/{row}/{col}'
        req = urllib.request.Request(url, headers={'User-Agent': 'qatar-gis-py/2.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        cache_path.write_bytes(raw)
        return raw, lod

    def render_overlay(self, polygons_4326, output_path,
                       year=2024, target_res=DEFAULT_TARGET_RES, padding_tiles=2,
                       polygon_colors=None, point=None):
        try:
            from PIL import Image, ImageDraw
            from io import BytesIO
        except ImportError:
            raise RuntimeError('render_overlay requires Pillow: pip install Pillow')

        lod = _best_lod(year, target_res)
        if lod is None:
            raise ValueError(f'No LOD available for year {year}')
        info = _service_info(year)
        ox, oy = info['origin_x'], info['origin_y']
        res_actual = info['lods'][lod]

        all_pts_2932 = []
        polys_2932 = []
        for poly in polygons_4326:
            poly_2932 = _project_4326_to_2932(poly)
            polys_2932.append(poly_2932)
            all_pts_2932.extend(poly_2932)

        point_2932 = None
        if point:
            point_2932 = _project_4326_to_2932([[point[0], point[1]]])[0]
            all_pts_2932.append(point_2932)

        if not all_pts_2932:
            raise ValueError('No geometry to render')

        cols = [_tile_coord(p[0], p[1], lod, year)[0] for p in all_pts_2932]
        rows = [_tile_coord(p[0], p[1], lod, year)[1] for p in all_pts_2932]
        col_min, col_max = min(cols) - padding_tiles, max(cols) + padding_tiles
        row_min, row_max = min(rows) - padding_tiles, max(rows) + padding_tiles
        n_cols = col_max - col_min + 1
        n_rows = row_max - row_min + 1

        mosaic = Image.new('RGB', (n_cols * TILE_SIZE, n_rows * TILE_SIZE), (200, 200, 200))
        tile_size_meters = res_actual * TILE_SIZE

        for ic, c in enumerate(range(col_min, col_max + 1)):
            for ir, r in enumerate(range(row_min, row_max + 1)):
                tcx = ox + (c + 0.5) * tile_size_meters
                tcy = oy - (r + 0.5) * tile_size_meters
                try:
                    raw, _ = self.get_tile(year, tcx, tcy, target_res)
                    tile = Image.open(BytesIO(raw))
                    mosaic.paste(tile, (ic * TILE_SIZE, ir * TILE_SIZE))
                except Exception as e:
                    self._log(f'tile fetch fail at ({c},{r}): {e}')

        mosaic_tlx = ox + col_min * TILE_SIZE * res_actual
        mosaic_tly = oy - row_min * TILE_SIZE * res_actual

        def to_pixel(x, y):
            return ((x - mosaic_tlx) / res_actual, (mosaic_tly - y) / res_actual)

        draw = ImageDraw.Draw(mosaic, 'RGBA')
        default_colors = [
            (255, 255, 0), (255, 128, 0), (0, 255, 128),
            (255, 0, 255), (255, 0, 0), (0, 200, 255),
            (128, 255, 0), (255, 128, 192),
        ]
        for i, poly in enumerate(polys_2932):
            color = polygon_colors[i] if (polygon_colors and i < len(polygon_colors)) else default_colors[i % len(default_colors)]
            poly_px = [to_pixel(p[0], p[1]) for p in poly]
            draw.polygon(poly_px, outline=color + (255,), fill=color + (40,), width=4)

        if point_2932:
            px, py = to_pixel(point_2932[0], point_2932[1])
            draw.ellipse([px-12, py-12, px+12, py+12],
                         fill=(255, 0, 0, 255), outline=(255, 255, 255, 255), width=3)

        margin = 80
        if all_pts_2932:
            xs_px, ys_px = zip(*[to_pixel(p[0], p[1]) for p in all_pts_2932])
            x0 = max(0, int(min(xs_px) - margin))
            y0 = max(0, int(min(ys_px) - margin))
            x1 = min(mosaic.width, int(max(xs_px) + margin))
            y1 = min(mosaic.height, int(max(ys_px) + margin))
            mosaic = mosaic.crop((x0, y0, x1, y1))

        output_path = Path(output_path)
        mosaic.save(output_path, quality=88)
        return output_path

    def estimate_construction_year(self, polygon_4326, threshold_stddev=22,
                                   years=None) -> Optional[ConstructionYearEstimate]:
        try:
            from PIL import Image, ImageDraw
            import numpy as np
            from io import BytesIO
        except ImportError:
            raise RuntimeError('estimate_construction_year requires Pillow + numpy')

        if years is None:
            years = sorted(IMAGERY_SERVICES.keys())
        else:
            years = sorted(years)

        poly_2932 = _project_4326_to_2932(polygon_4326)
        if not poly_2932:
            return None

        results = []
        for year in years:
            try:
                xs = [p[0] for p in poly_2932]
                ys = [p[1] for p in poly_2932]
                target_res = 0.529
                lod_for_year = _best_lod(year, target_res)
                if lod_for_year is None:
                    continue
                info = _service_info(year)
                ox, oy = info['origin_x'], info['origin_y']
                res_actual = info['lods'][lod_for_year]
                col_min, _ = _tile_coord(min(xs), max(ys), lod_for_year, year)
                col_max, _ = _tile_coord(max(xs), min(ys), lod_for_year, year)
                _, row_min = _tile_coord(max(xs), max(ys), lod_for_year, year)
                _, row_max = _tile_coord(min(xs), min(ys), lod_for_year, year)
                col_min -= 1; col_max += 1; row_min -= 1; row_max += 1
                n_cols = col_max - col_min + 1
                n_rows = row_max - row_min + 1
                if n_cols * n_rows > 36:
                    continue

                mosaic = Image.new('RGB', (n_cols * TILE_SIZE, n_rows * TILE_SIZE), (128, 128, 128))
                ok_count = 0
                tile_size_meters = res_actual * TILE_SIZE
                for ic, c in enumerate(range(col_min, col_max + 1)):
                    for ir, r in enumerate(range(row_min, row_max + 1)):
                        tx = ox + (c + 0.5) * tile_size_meters
                        ty = oy - (r + 0.5) * tile_size_meters
                        try:
                            raw, _ = self.get_tile(year, tx, ty, target_res)
                            tile = Image.open(BytesIO(raw))
                            mosaic.paste(tile, (ic * TILE_SIZE, ir * TILE_SIZE))
                            ok_count += 1
                        except Exception:
                            pass
                if ok_count == 0:
                    continue

                mosaic_tlx = ox + col_min * TILE_SIZE * res_actual
                mosaic_tly = oy - row_min * TILE_SIZE * res_actual
                def to_px(x, y):
                    return ((x - mosaic_tlx) / res_actual, (mosaic_tly - y) / res_actual)
                poly_px = [to_px(p[0], p[1]) for p in poly_2932]
                mask = Image.new('L', mosaic.size, 0)
                ImageDraw.Draw(mask).polygon(poly_px, fill=255)
                arr = np.asarray(mosaic.convert('L'))
                mask_arr = np.asarray(mask)
                inside = arr[mask_arr > 0]
                if len(inside) < 100:
                    continue
                stddev = float(inside.std())
                results.append({'year': year, 'stddev': stddev, 'built': stddev >= threshold_stddev})
            except Exception as e:
                self._log(f'year {year} failed: {e}')

        if not results:
            return None

        results.sort(key=lambda r: r['year'])
        first_built = next((r['year'] for r in results if r['built']), None)
        if first_built is None:
            return ConstructionYearEstimate(
                earliest_built_year=results[-1]['year'] + 5,
                latest_vacant_year=results[-1]['year'],
                confidence_years=99,
                summary='Polygon appears vacant in all sampled years',
            )
        latest_vacant = max(
            (r['year'] for r in results if not r['built'] and r['year'] < first_built),
            default=None,
        )
        if latest_vacant is None:
            return ConstructionYearEstimate(
                earliest_built_year=first_built,
                latest_vacant_year=first_built - 5,
                confidence_years=5,
                summary=f'Built in or before {first_built} (no vacant baseline available)',
            )
        gap = first_built - latest_vacant
        return ConstructionYearEstimate(
            earliest_built_year=first_built,
            latest_vacant_year=latest_vacant,
            confidence_years=gap,
            summary=f'Built between {latest_vacant} and {first_built} (±{gap} years)',
        )

    def estimate_construction_year_smart(self, polygon_4326, pin=None,
                                          time_budget_s=20.0,
                                          threshold_stddev=22):
        """Sprint 2.15 (L4) — smart, time-budgeted, cached variant.

        Sprint 2.15.1 update: respects ENABLE_INLINE_IMAGERY module flag.

        Two operating modes:
          1. CACHE-ONLY (production default, flag=False):
             Only reads from the SQLite cache. Returns None on miss. Never
             runs imagery analysis. This guarantees the function completes
             in <10ms regardless of network conditions, protecting Heroku's
             30s request budget.

          2. FULL (prefill / CLI, flag=True):
             Cache miss → runs fast probe (1995 + 2024) → optionally refines
             with 2010 + 2017 → caches the result for next time.

        Args:
            polygon_4326: list of [lon, lat] points (the plot polygon)
            pin: cadastral PIN (used as cache key — required for caching)
            time_budget_s: maximum wall-clock seconds (FULL mode only)
            threshold_stddev: pixel stddev cutoff (FULL mode only)

        Returns:
            ConstructionYearEstimate, or None on cache miss in CACHE-ONLY mode,
            or None on computation failure in FULL mode.

        Cache write-through is best-effort; cache errors never raise.
        """
        import time
        from building_age_cache import get_default_cache

        # ── Step 1: cache lookup (both modes) ──
        cache = None
        if pin is not None:
            try:
                cache = get_default_cache()
                cached = cache.get(pin)
                if cached and cached.get('earliest_built_year') is not None:
                    return ConstructionYearEstimate(
                        earliest_built_year=cached['earliest_built_year'],
                        latest_vacant_year=cached['latest_vacant_year'],
                        confidence_years=cached['confidence_years'],
                        summary=cached['summary'] or '',
                    )
            except Exception:
                # Cache failure must not break valuation
                cache = None

        # ── CACHE-ONLY mode: return immediately on miss ──
        # This is the production path on Heroku — no imagery analysis inline.
        if not ENABLE_INLINE_IMAGERY:
            return None

        # ── FULL mode (prefill / CLI): run imagery analysis ──
        t_start = time.time()

        # Step 2: fast probe — 1995 + 2024
        try:
            result = self.estimate_construction_year(
                polygon_4326,
                threshold_stddev=threshold_stddev,
                years=[1995, 2024],
            )
        except Exception:
            return None
        method = 'fast_probe'

        # Step 3: refine if bracket is wide AND budget allows
        if result is not None and result.confidence_years > 7:
            elapsed = time.time() - t_start
            remaining = time_budget_s - elapsed
            if remaining > 12:
                try:
                    refined = self.estimate_construction_year(
                        polygon_4326,
                        threshold_stddev=threshold_stddev,
                        years=[1995, 2010, 2017, 2024],
                    )
                    if refined is not None and \
                       refined.confidence_years < result.confidence_years:
                        result = refined
                        method = 'binary_search_4y'
                except Exception:
                    pass

        # Step 4: write-through cache
        if cache is not None and result is not None:
            try:
                cache.set(
                    pin=pin,
                    earliest_built_year=result.earliest_built_year,
                    latest_vacant_year=result.latest_vacant_year,
                    confidence_years=result.confidence_years,
                    summary=result.summary,
                    method=method,
                    source_data={
                        'elapsed_s': round(time.time() - t_start, 1),
                        'threshold_stddev': threshold_stddev,
                    },
                )
            except Exception:
                pass

        return result

    # ----- Tier 4: composite -----

    def full_property_lookup(self, zone=None, street=None, building=None,
                             include_imagery=True, output_dir=None,
                             pin=None, input_mode=None) -> Optional[PropertyReport]:
        # Sprint 2.21.0: PIN entry path. Bare lands have a Cadastre PIN but no
        # QARS address, so when `pin` is given we skip find_property entirely,
        # resolve the polygon straight from CadastrePlots, and synthesise a
        # minimal location (centroid for the Districts lookup). `input_mode`
        # ('land') is threaded to classify_asset so the parcel is typed as land
        # rather than mis-typed as a villa by the area heuristic.
        if pin:
            plot = self.get_plot(pin)
            if plot is None:
                return None
            ring = plot.polygon_4326 or []
            if ring:
                cx = sum(p[0] for p in ring) / len(ring)
                cy = sum(p[1] for p in ring) / len(ring)
            else:
                cx = cy = None
            loc = PropertyLocation(
                zone=zone, street=street, building=building, pin=pin,
                qars='', plot_no_old=None, lon=cx, lat=cy,
                electricity_no=None, water_no=None, qtel_id=None,
                building_subtype=None,
            )
        else:
            loc = self.find_property(zone, street, building)
            if loc is None:
                return None

        # District is cheap and useful even if cadastre/plot lookup fails.
        try:
            district = (self.get_district_at_point(loc.lon, loc.lat)
                        if (loc.lon and loc.lat) else None)
        except Exception:
            district = None

        if not pin:
            plot = self.get_plot(loc.pin)
            if plot is None:
                return PropertyReport(
                    location=loc, plot=None,
                    classification=AssetClassification(
                        AssetType.UNKNOWN, 'low', ['No cadastre plot found'], [], []
                    ),
                    extent=None, construction=None,
                    district=district,
                    flags=['Property location found, but no cadastre plot. May be unsurveyed.'],
                )

        # Subtype is only available from QARS (address path); the land/PIN path
        # has none, so the input_mode='land' hint drives classification.
        _meta = None
        if getattr(loc, 'building_subtype', None) is not None:
            _meta = {'building_subtype': loc.building_subtype,
                     'lat': loc.lat, 'lon': loc.lon}
        classification = classify_asset(plot, location_metadata=_meta, input_mode=input_mode)
        extent = self.detect_extent(plot.pin)

        construction = None
        if include_imagery and classification.asset_type not in (AssetType.RAW_LAND, AssetType.UNKNOWN):
            try:
                construction = self.estimate_construction_year(plot.polygon_4326)
            except Exception as e:
                pass

        flags = list(classification.flags)
        if plot.shape.irregularity_warning:
            flags.append(plot.shape.irregularity_warning)
        if plot.is_unsubdivided and classification.asset_type == AssetType.STANDALONE_VILLA:
            flags.append(
                'PD_NO=0 detected on what looks like a villa-sized plot. '
                'May actually be part of a larger compound — check neighbors.'
            )

        if include_imagery and output_dir and extent:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            try:
                polys = [p.polygon_4326 for p in extent.plots]
                out = output_dir / f'{classification.asset_type.value}_{loc.pin}.jpg'
                self.render_overlay(polys, out, point=(loc.lon, loc.lat, f'B{building}'))
                flags.append(f'Imagery saved to: {out}')
            except Exception as e:
                flags.append(f'Imagery render failed: {e}')

        return PropertyReport(
            location=loc, plot=plot,
            classification=classification, extent=extent,
            construction=construction, district=district, flags=flags,
        )


# ============================================================
# 8. CLI
# ============================================================

def _print_classification(c):
    print(f'  Asset type:   {c.asset_type.value.upper()}')
    print(f'  Confidence:   {c.confidence}')
    print(f'  Reasons:')
    for r in c.reasons:
        print(f'    • {r}')
    if c.flags:
        print(f'  Flags:')
        for f in c.flags:
            print(f'    ⚠ {f}')
    if c.alternative_types:
        alts = ', '.join(t.value for t in c.alternative_types)
        print(f'  Alternative classifications: {alts}')


def _print_extent(e):
    print(f'  Asset type:           {e.asset_type.value}')
    print(f'  Detection confidence: {e.detection_confidence}')
    print(f'  Parcels ({len(e.included_pins)}): {e.included_pins}')
    print(f'  Total area:           {e.total_area_m2:,.0f} m²')
    if e.notes:
        print(f'  Notes:')
        for n in e.notes:
            print(f'    • {n}')


def _print_property_report(report):
    if report is None:
        print('Property not found.')
        return
    loc = report.location
    plot = report.plot
    print(f'\n{"="*70}')
    print(f'  {loc.zone} / {loc.street} / {loc.building}    PIN {loc.pin}')
    print(f'{"="*70}')
    print(f'  GPS:        {loc.lat:.6f}° N, {loc.lon:.6f}° E')
    print(f'  QARS code:  {loc.qars}')
    if plot:
        print(f'  Plot area:  {plot.pdarea:,.0f} m² (PD_NO={plot.pd_no})')
        print(f'  Shape:      {plot.shape.vertex_count} vertices, '
              f'{"rect" if plot.shape.is_rectangular else "irreg" if plot.shape.is_irregular else "ok"}, '
              f'hull-ratio {plot.shape.convex_hull_ratio}')
    if getattr(report, 'district', None):
        d = report.district
        print(f'  District:   {d.aname} ({d.ename}, DIST_NO={d.dist_no})')

    print(f'\n[Classification]')
    _print_classification(report.classification)
    if report.extent:
        print(f'\n[Asset Extent]')
        _print_extent(report.extent)
    if report.construction:
        print(f'\n[Construction]')
        print(f'  {report.construction.summary}')
    if report.flags:
        print(f'\n[Flags]')
        for f in report.flags:
            print(f'  ⚠ {f}')


def main():
    p = argparse.ArgumentParser(description='Qatar GIS classifier and lookup CLI')
    sub = p.add_subparsers(dest='cmd', required=True)

    sp = sub.add_parser('find', help='Find property by address')
    sp.add_argument('zone', type=int); sp.add_argument('street', type=int); sp.add_argument('building', type=int)

    sp = sub.add_parser('plot', help='Get plot info by PIN')
    sp.add_argument('pin', type=int)

    sp = sub.add_parser('classify', help='Classify a plot by PIN')
    sp.add_argument('pin', type=int)

    sp = sub.add_parser('extent', help='Detect full asset extent by PIN')
    sp.add_argument('pin', type=int)
    sp.add_argument('--force-type', help='Override classification (e.g. compound_large)')

    sp = sub.add_parser('report', help='Full end-to-end report by address')
    sp.add_argument('zone', type=int); sp.add_argument('street', type=int); sp.add_argument('building', type=int)
    sp.add_argument('--no-imagery', action='store_true')
    sp.add_argument('--output-dir', type=Path, default=Path('./gis_output'))

    sp = sub.add_parser('imagery', help='Render imagery for a PIN')
    sp.add_argument('pin', type=int)
    sp.add_argument('--years', default='1995,2003,2010,2024')
    sp.add_argument('--output-dir', type=Path, default=Path('./gis_output'))

    sp = sub.add_parser('construction', help='Estimate construction year for a PIN')
    sp.add_argument('pin', type=int)

    sp = sub.add_parser('district', help='Resolve administrative district for an address')
    sp.add_argument('zone', type=int); sp.add_argument('street', type=int); sp.add_argument('building', type=int)

    p.add_argument('--verbose', '-v', action='store_true')
    args = p.parse_args()
    gis = QatarGIS(verbose=args.verbose)

    if args.cmd == 'find':
        loc = gis.find_property(args.zone, args.street, args.building)
        print(json.dumps(asdict(loc) if loc else None, ensure_ascii=False, indent=2))

    elif args.cmd == 'plot':
        plot = gis.get_plot(args.pin)
        if plot is None:
            print('Not found.'); sys.exit(1)
        d = asdict(plot)
        d['polygon_4326'] = f'<{len(d["polygon_4326"])} points>'
        d['polygon_2932'] = f'<{len(d["polygon_2932"])} points>'
        print(json.dumps(d, ensure_ascii=False, indent=2, default=str))

    elif args.cmd == 'classify':
        plot = gis.get_plot(args.pin)
        if plot is None:
            print('Not found.'); sys.exit(1)
        c = classify_asset(plot)
        print(f'PIN {args.pin}: area={plot.pdarea:,.0f} m², PD_NO={plot.pd_no}')
        _print_classification(c)

    elif args.cmd == 'extent':
        force_type = AssetType(args.force_type) if args.force_type else None
        ext = gis.detect_extent(args.pin, force_type=force_type)
        if ext is None:
            print('Not found.'); sys.exit(1)
        _print_extent(ext)

    elif args.cmd == 'report':
        report = gis.full_property_lookup(
            args.zone, args.street, args.building,
            include_imagery=not args.no_imagery,
            output_dir=args.output_dir if not args.no_imagery else None,
        )
        _print_property_report(report)

    elif args.cmd == 'imagery':
        plot = gis.get_plot(args.pin)
        if plot is None:
            print('Not found.'); sys.exit(1)
        years = [int(y.strip()) for y in args.years.split(',')]
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for y in years:
            out = args.output_dir / f'pin_{args.pin}_{y}.jpg'
            gis.render_overlay([plot.polygon_4326], out, year=y)
            print(f'  Saved: {out}')

    elif args.cmd == 'construction':
        plot = gis.get_plot(args.pin)
        if plot is None:
            print('Not found.'); sys.exit(1)
        est = gis.estimate_construction_year(plot.polygon_4326)
        if est:
            print(json.dumps(asdict(est), indent=2))
        else:
            print('Could not estimate.')

    elif args.cmd == 'district':
        d = gis.get_district(args.zone, args.street, args.building)
        if d is None:
            print('No district found at this address.'); sys.exit(1)
        print(f'GIS district:    {d.aname} ({d.ename})')
        print(f'DIST_NO:         {d.dist_no}')


if __name__ == '__main__':
    main()
