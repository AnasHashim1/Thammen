#!/usr/bin/env python3
"""
property_factors.py — GIS-based property factor analysis for Qatar.

Queries 6 official GIS layers to compute an objective ±10% adjustment
to the MoJ median, based on factors that MoJ data cannot capture.

Layers used:
    1. Vector/Zoning/MapServer/0              → zoning classification (R1/R2/R3/C/...)
    2. Vector/Commercial_StreetsA/MapServer/0  → commercial street proximity
    3. Vector/Landmarks/MapServer/0            → mosques, schools, parks, clinics
    4. Vector/ROADFlowlnA/MapServer/1,2       → local vs main streets
    5. Vector/General_Landuse/MapServer/0      → permitted building height
    6. Vector/CadastrePlots/MapServer/0        → plot shape (already in qatar_gis)

All data is from services.gisqatar.org.qa — no external APIs needed.

Usage:
    from property_factors import analyze_property
    result = analyze_property(lat=25.248, lon=51.492, purpose='residential')
    print(result.adjustment)       # e.g. +0.045 (= +4.5%)
    print(result.factors)          # list of individual factor details
    print(result.fair_price(5000000))  # 5,225,000
"""

import json
import math
import urllib.request
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import Optional

# ============================================================
# CONSTANTS
# ============================================================

GIS_BASE = "https://services.gisqatar.org.qa/server/rest/services"

LAYER_URLS = {
    'zoning':       f"{GIS_BASE}/Vector/Zoning/MapServer/0",
    'commercial':   f"{GIS_BASE}/Vector/Commercial_StreetsA/MapServer/0",
    'landmarks':    f"{GIS_BASE}/Vector/Landmarks/MapServer/0",
    'local_roads':  f"{GIS_BASE}/Vector/ROADFlowlnA/MapServer/1",
    'main_roads':   f"{GIS_BASE}/Vector/ROADFlowlnA/MapServer/2",
    'landuse':      f"{GIS_BASE}/Vector/General_Landuse/MapServer/0",
}

# Maximum total adjustment (absolute value)
MAX_ADJUSTMENT = 0.10  # ±10%

# Landmark categories that affect property value
# Category mapping from GIS Arabic names
LANDMARK_WEIGHTS = {
    'residential': {
        # (category_aname, subcategory_aname_contains) → (radius_m, weight, label_ar)
        ('ديني', None):         (300,  +0.010, 'قرب مسجد'),
        ('تعليمي', 'مدرسة'):    (500,  +0.010, 'قرب مدرسة'),
        ('تعليمي', 'حضانة'):    (400,  +0.005, 'قرب حضانة'),
        ('صحي', 'عيادة'):       (500,  +0.010, 'قرب عيادة/مركز صحي'),
        ('صحي', 'صيدلية'):      (400,  +0.005, 'قرب صيدلية'),
        ('صحي', 'مستشفى'):      (800,  +0.015, 'قرب مستشفى'),
        ('تجاري', 'مطاعم'):     (300,  +0.005, 'قرب مطاعم/مقاهي'),
        ('تجاري', 'مركز تجاري'):(500,  +0.010, 'قرب مركز تجاري'),
    },
    'investment': {
        ('ديني', None):         (300,  +0.005, 'قرب مسجد'),
        ('تعليمي', 'مدرسة'):    (500,  +0.015, 'قرب مدرسة — طلب إيجاري'),
        ('صحي', 'مستشفى'):      (800,  +0.020, 'قرب مستشفى — طلب إيجاري عالي'),
        ('تجاري', 'مركز تجاري'):(500,  +0.020, 'قرب مركز تجاري — طلب إيجاري'),
    },
}

# Zoning weights
ZONING_WEIGHTS = {
    'residential': {
        'R1':     +0.020,  # exclusive residential — highest privacy
        'R1-TYP': +0.020,
        'R2':      0.000,  # standard
        'R2-TYP':  0.000,
        'R3':     -0.020,  # denser, less privacy
        'R3-TYP': -0.020,
        'C':      -0.015,  # commercial zone — noise for residents
        'MU':     -0.010,  # mixed use
    },
    'investment': {
        'R1':      0.000,  # limited rental demand in exclusive zones
        'R1-TYP':  0.000,
        'R2':     +0.010,
        'R2-TYP': +0.010,
        'R3':     +0.015,  # higher density = more tenants
        'R3-TYP': +0.015,
        'C':      +0.020,  # commercial = strong rental
        'MU':     +0.015,
    },
}

# Permitted height weights (development potential)
HEIGHT_WEIGHTS = {
    'G':       0.000,
    'G+P':     0.000,
    'G+1':     0.005,
    'G+1+P':   0.005,
    'G+2':     0.010,
    'G+2+P':   0.010,
    'G+3':     0.015,
    'G+4':     0.020,
}

TIMEOUT = 12


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class Factor:
    """A single property factor."""
    name: str              # internal key
    label_ar: str          # Arabic display label
    source: str            # GIS layer used
    direction: str         # 'positive' | 'negative' | 'neutral'
    weight: float          # signed: +0.02 or -0.01
    detail: str = ''       # extra info (e.g. "R1", "3 مساجد ضمن 300م")


@dataclass
class PropertyFactors:
    """Result of property factor analysis."""
    factors: list          # list of Factor
    raw_adjustment: float  # sum of all weights (before capping)
    adjustment: float      # capped to ±MAX_ADJUSTMENT
    purpose: str           # 'residential' | 'investment'
    notes: list = field(default_factory=list)

    def fair_price(self, moj_median: float) -> float:
        """Apply adjustment to MoJ median."""
        return round(moj_median * (1 + self.adjustment))


# ============================================================
# GIS QUERY HELPERS
# ============================================================

def _query_gis(layer_url: str, params: dict, timeout: int = TIMEOUT) -> list:
    """Query a GIS layer and return features list."""
    params.setdefault('f', 'json')
    params.setdefault('returnGeometry', 'false')
    url = layer_url + '/query?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'property-factors/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        return data.get('features', [])
    except Exception as e:
        return []


def _point_geom(lat: float, lon: float) -> str:
    """Create a point geometry JSON string."""
    return json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}})


def _bbox_geom(lat: float, lon: float, radius_m: float) -> str:
    """Create a bounding box geometry JSON string from center + radius."""
    # Approximate degrees per meter at Qatar's latitude
    deg_per_m_lat = 1 / 111320
    deg_per_m_lon = 1 / (111320 * math.cos(math.radians(lat)))
    dlat = radius_m * deg_per_m_lat
    dlon = radius_m * deg_per_m_lon
    return json.dumps({
        "xmin": lon - dlon, "ymin": lat - dlat,
        "xmax": lon + dlon, "ymax": lat + dlat,
        "spatialReference": {"wkid": 4326}
    })


def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance in meters between two GPS points."""
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    return 2 * R * math.asin(math.sqrt(a))


# ============================================================
# INDIVIDUAL FACTOR ANALYZERS
# ============================================================

def _factor_zoning(lat: float, lon: float, purpose: str) -> Optional[Factor]:
    """Check zoning classification at the property location."""
    features = _query_gis(LAYER_URLS['zoning'], {
        'geometry': _point_geom(lat, lon),
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'ZONING',
    })
    if not features:
        return None

    zoning = features[0]['attributes'].get('ZONING', '')
    weights = ZONING_WEIGHTS.get(purpose, ZONING_WEIGHTS['residential'])
    weight = weights.get(zoning, 0)

    if weight == 0 and zoning not in weights:
        return Factor(
            name='zoning', label_ar=f'تزوير {zoning}',
            source='Vector/Zoning', direction='neutral',
            weight=0, detail=f'تصنيف {zoning} — لا يؤثر على التقييم'
        )

    direction = 'positive' if weight > 0 else ('negative' if weight < 0 else 'neutral')
    return Factor(
        name='zoning', label_ar=f'تزوير {zoning}',
        source='Vector/Zoning', direction=direction,
        weight=weight, detail=f'تصنيف {zoning}'
    )


def _factor_commercial_street(lat: float, lon: float, purpose: str) -> Optional[Factor]:
    """Check if property is on or near a commercial street."""
    for radius, label in [(50, 'على شارع تجاري'), (200, 'قرب شارع تجاري')]:
        features = _query_gis(LAYER_URLS['commercial'], {
            'geometry': _point_geom(lat, lon),
            'geometryType': 'esriGeometryPoint',
            'inSR': '4326',
            'spatialRel': 'esriSpatialRelIntersects',
            'distance': str(radius),
            'units': 'esriSRUnit_Meter',
            'outFields': 'OBJECTID',
            'resultRecordCount': '1',
        })
        if features:
            if purpose == 'investment':
                w = +0.025 if radius <= 50 else +0.015
                return Factor(
                    name='commercial_street', label_ar=label,
                    source='Vector/Commercial_StreetsA', direction='positive',
                    weight=w, detail=f'{label} — علاوة إيجارية'
                )
            else:
                w = -0.015 if radius <= 50 else -0.005
                return Factor(
                    name='commercial_street', label_ar=label,
                    source='Vector/Commercial_StreetsA', direction='negative',
                    weight=w, detail=f'{label} — ضوضاء وازدحام'
                )
    return None


def _factor_main_road(lat: float, lon: float, purpose: str) -> Optional[Factor]:
    """Check if property is on a main road vs local street."""
    # Check main roads first (within 50m)
    features = _query_gis(LAYER_URLS['main_roads'], {
        'geometry': _point_geom(lat, lon),
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'distance': '50',
        'units': 'esriSRUnit_Meter',
        'outFields': 'OBJECTID',
        'resultRecordCount': '1',
    })
    if features:
        if purpose == 'investment':
            return Factor(
                name='main_road', label_ar='على شارع رئيسي',
                source='Vector/ROADFlowlnA/2', direction='positive',
                weight=+0.015, detail='شارع رئيسي — رؤية وسهولة وصول'
            )
        else:
            return Factor(
                name='main_road', label_ar='على شارع رئيسي',
                source='Vector/ROADFlowlnA/2', direction='negative',
                weight=-0.010, detail='شارع رئيسي — حركة مرور وضوضاء'
            )

    # Check if on a local/internal street
    features_local = _query_gis(LAYER_URLS['local_roads'], {
        'geometry': _point_geom(lat, lon),
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'distance': '30',
        'units': 'esriSRUnit_Meter',
        'outFields': 'OBJECTID',
        'resultRecordCount': '1',
    })
    if features_local and purpose == 'residential':
        return Factor(
            name='local_road', label_ar='شارع داخلي هادئ',
            source='Vector/ROADFlowlnA/1', direction='positive',
            weight=+0.010, detail='شارع فرعي — هدوء وخصوصية'
        )
    return None


def _factor_landmarks(lat: float, lon: float, purpose: str) -> list:
    """Find nearby landmarks and compute their value impact."""
    # Query landmarks within 1km
    features = _query_gis(LAYER_URLS['landmarks'], {
        'geometry': _bbox_geom(lat, lon, 1000),
        'geometryType': 'esriGeometryEnvelope',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'ANAME,ENAME,CATEGORY_ANAME,SUBCATEGORY_ANAME',
        'outSR': '4326',
        'returnGeometry': 'true',
        'resultRecordCount': '100',
    })

    if not features:
        return []

    weights_map = LANDMARK_WEIGHTS.get(purpose, LANDMARK_WEIGHTS['residential'])
    found_factors = []
    applied_categories = set()  # avoid double-counting same category

    for (cat, subcat_contains), (radius, weight, label) in weights_map.items():
        matching = []
        for f in features:
            a = f['attributes']
            f_cat = (a.get('CATEGORY_ANAME') or '').strip()
            f_sub = (a.get('SUBCATEGORY_ANAME') or '').strip()

            if f_cat != cat:
                continue
            if subcat_contains and subcat_contains not in f_sub:
                continue

            # Compute distance
            g = f.get('geometry', {})
            if 'x' in g and 'y' in g:
                dist = _haversine(lat, lon, g['y'], g['x'])
                if dist <= radius:
                    matching.append((a.get('ANAME', '?'), dist))

        if matching and cat not in applied_categories:
            applied_categories.add(cat + (subcat_contains or ''))
            names = [m[0] for m in matching[:3]]
            closest = min(m[1] for m in matching)
            detail = f"{len(matching)}× ضمن {radius}م — أقرب: {names[0]} ({closest:.0f}م)"

            found_factors.append(Factor(
                name=f'landmark_{cat}_{subcat_contains or "any"}',
                label_ar=label,
                source='Vector/Landmarks',
                direction='positive' if weight > 0 else 'negative',
                weight=weight,
                detail=detail,
            ))

    return found_factors


def _factor_permitted_height(lat: float, lon: float) -> Optional[Factor]:
    """Check permitted building height from land use layer."""
    features = _query_gis(LAYER_URLS['landuse'], {
        'geometry': _point_geom(lat, lon),
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'BUILDING_HEIGHT,LANDUSE,SUB_LANDUSE',
    })
    if not features:
        return None

    a = features[0]['attributes']
    height = (a.get('BUILDING_HEIGHT') or '').strip()
    if not height:
        return None

    weight = HEIGHT_WEIGHTS.get(height, 0)
    if weight == 0:
        # Try partial match for higher buildings
        for key, w in HEIGHT_WEIGHTS.items():
            if key in height:
                weight = w
                break

    return Factor(
        name='permitted_height', label_ar=f'ارتفاع مسموح: {height}',
        source='Vector/General_Landuse',
        direction='positive' if weight > 0 else 'neutral',
        weight=weight,
        detail=f'الارتفاع المسموح {height} — إمكانية تطوير مستقبلية'
    )


def _factor_plot_shape(convex_hull_ratio: float = None,
                       vertex_count: int = None) -> Optional[Factor]:
    """Assess plot shape regularity (data from qatar_gis plot analysis)."""
    if convex_hull_ratio is None or vertex_count is None:
        return None

    if vertex_count <= 5 and convex_hull_ratio >= 0.95:
        return Factor(
            name='plot_shape', label_ar='قطعة منتظمة الشكل',
            source='CadastrePlots/polygon', direction='neutral',
            weight=0, detail=f'{vertex_count} رؤوس، نسبة انتظام {convex_hull_ratio:.2f}'
        )

    if convex_hull_ratio < 0.85 or vertex_count > 8:
        w = -0.020
        label = 'قطعة غير منتظمة الشكل'
    elif convex_hull_ratio < 0.92 or vertex_count > 6:
        w = -0.010
        label = 'قطعة شبه منتظمة'
    else:
        w = 0
        label = 'قطعة مقبولة الشكل'

    return Factor(
        name='plot_shape', label_ar=label,
        source='CadastrePlots/polygon',
        direction='negative' if w < 0 else 'neutral',
        weight=w,
        detail=f'{vertex_count} رؤوس، نسبة انتظام {convex_hull_ratio:.2f}'
    )


def _factor_building_age(age_years: int = None, purpose: str = 'residential') -> Optional[Factor]:
    """Assess building age impact on value."""
    if age_years is None:
        return None

    if age_years <= 3:
        return Factor(
            name='building_age', label_ar='بناء حديث جداً',
            source='Imagery/historical', direction='positive',
            weight=+0.030, detail=f'عمر البناء ~{age_years} سنوات'
        )
    elif age_years <= 7:
        return Factor(
            name='building_age', label_ar='بناء حديث',
            source='Imagery/historical', direction='positive',
            weight=+0.015, detail=f'عمر البناء ~{age_years} سنوات'
        )
    elif age_years <= 15:
        return Factor(
            name='building_age', label_ar='بناء متوسط العمر',
            source='Imagery/historical', direction='neutral',
            weight=0, detail=f'عمر البناء ~{age_years} سنوات'
        )
    elif age_years <= 25:
        return Factor(
            name='building_age', label_ar='بناء قديم نسبياً',
            source='Imagery/historical', direction='negative',
            weight=-0.020, detail=f'عمر البناء ~{age_years} سنة — صيانة متوقعة'
        )
    else:
        return Factor(
            name='building_age', label_ar='بناء قديم',
            source='Imagery/historical', direction='negative',
            weight=-0.040, detail=f'عمر البناء ~{age_years} سنة — صيانة كبيرة أو إعادة بناء'
        )


# ============================================================
# MAIN ANALYZER
# ============================================================

def analyze_property(lat: float, lon: float,
                     purpose: str = 'residential',
                     plot_shape: dict = None,
                     building_age_years: int = None,
                     verbose: bool = False) -> PropertyFactors:
    """
    Analyze property factors from GIS data.

    Args:
        lat, lon: GPS coordinates (WGS84)
        purpose: 'residential' or 'investment'
        plot_shape: dict with 'convex_hull_ratio' and 'vertex_count' (from qatar_gis)
        building_age_years: estimated building age
        verbose: print progress

    Returns:
        PropertyFactors with adjustment capped to ±10%
    """
    factors = []
    notes = []

    # 1. Zoning
    if verbose: print("  [factors] Querying zoning...")
    f = _factor_zoning(lat, lon, purpose)
    if f:
        factors.append(f)
    else:
        notes.append('لم يُعثر على تصنيف زوننج — طبقة قد تكون غير متاحة')

    # 2. Commercial street
    if verbose: print("  [factors] Querying commercial streets...")
    f = _factor_commercial_street(lat, lon, purpose)
    if f:
        factors.append(f)

    # 3. Main vs local road
    if verbose: print("  [factors] Querying road type...")
    f = _factor_main_road(lat, lon, purpose)
    if f:
        factors.append(f)

    # 4. Landmarks
    if verbose: print("  [factors] Querying landmarks...")
    landmark_factors = _factor_landmarks(lat, lon, purpose)
    factors.extend(landmark_factors)

    # 5. Permitted height
    if verbose: print("  [factors] Querying permitted height...")
    f = _factor_permitted_height(lat, lon)
    if f:
        factors.append(f)

    # 6. Plot shape (from caller, not a GIS query)
    if plot_shape:
        f = _factor_plot_shape(
            convex_hull_ratio=plot_shape.get('convex_hull_ratio'),
            vertex_count=plot_shape.get('vertex_count'),
        )
        if f:
            factors.append(f)

    # 7. Building age (from caller)
    f = _factor_building_age(building_age_years, purpose)
    if f:
        factors.append(f)

    # Compute total adjustment
    raw = sum(f.weight for f in factors)
    capped = max(-MAX_ADJUSTMENT, min(MAX_ADJUSTMENT, raw))

    if abs(raw) > MAX_ADJUSTMENT:
        notes.append(
            f'التعديل الخام {raw*100:+.1f}% تجاوز الحد ±{MAX_ADJUSTMENT*100:.0f}% '
            f'— تم تحديده عند {capped*100:+.1f}%'
        )

    if verbose:
        print(f"\n  [factors] {len(factors)} عوامل → تعديل {capped*100:+.1f}%")
        for f in factors:
            icon = '✚' if f.direction == 'positive' else ('✖' if f.direction == 'negative' else '○')
            print(f"    {icon} {f.label_ar:25s}  {f.weight*100:+5.1f}%  ({f.source})")

    return PropertyFactors(
        factors=factors,
        raw_adjustment=round(raw, 4),
        adjustment=round(capped, 4),
        purpose=purpose,
        notes=notes,
    )


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    p = argparse.ArgumentParser(description='GIS-based property factor analysis')
    p.add_argument('lat', type=float, help='Latitude (WGS84)')
    p.add_argument('lon', type=float, help='Longitude (WGS84)')
    p.add_argument('--purpose', choices=['residential', 'investment'],
                   default='residential')
    p.add_argument('--building-age', type=int, default=None)
    p.add_argument('--hull-ratio', type=float, default=None)
    p.add_argument('--vertex-count', type=int, default=None)
    p.add_argument('--json', action='store_true', help='Output as JSON')
    args = p.parse_args()

    plot_shape = None
    if args.hull_ratio is not None and args.vertex_count is not None:
        plot_shape = {
            'convex_hull_ratio': args.hull_ratio,
            'vertex_count': args.vertex_count,
        }

    result = analyze_property(
        lat=args.lat, lon=args.lon,
        purpose=args.purpose,
        plot_shape=plot_shape,
        building_age_years=args.building_age,
        verbose=not args.json,
    )

    if args.json:
        data = {
            'adjustment': result.adjustment,
            'raw_adjustment': result.raw_adjustment,
            'purpose': result.purpose,
            'factors': [asdict(f) for f in result.factors],
            'notes': result.notes,
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"  التعديل النهائي: {result.adjustment*100:+.1f}%")
        print(f"  الغرض: {'سكني' if result.purpose == 'residential' else 'إيجاري'}")
        if result.notes:
            for n in result.notes:
                print(f"  ⚠ {n}")
        print(f"{'='*50}")
        print(f"\n  مثال: وسيط MoJ = 5,000,000 → السعر العادل = {result.fair_price(5000000):,.0f}")


if __name__ == '__main__':
    main()
