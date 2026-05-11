#!/usr/bin/env python3
"""
gis_preload.py — تحميل بيانات GIS قطر مرة واحدة عند الإقلاع.

Sprint 1 Task 7: بدلاً من استدعاء GIS قطر لكل تقييم (10-30 طلب شبكة)،
نحمّل البيانات الثابتة من ملف JSON محلي عند الإقلاع.

البيانات المخزّنة:
    - أسماء كل المناطق (789 منطقة)
    - مراكز كل منطقة (centroid lat/lon)
    - bounding box لكل منطقة (للفلترة المكانية السريعة)

ما يبقى dynamic (يُستعلم من GIS لحظياً):
    - عنوان عقار محدد (find_property)
    - تفاصيل قطعة (get_plot)
    - معالم قريبة (landmarks)
    - تصنيف zoning محدد

الاستخدام:
    from gis_preload import load_districts, find_district_at_point, get_district_centroid

    # عند الإقلاع
    districts = load_districts()

    # خلال الطلب
    centroid = get_district_centroid(78)  # فوري، بدون طلب شبكة
    nearby = find_districts_within_radius(25.27, 51.47, radius_km=2)
"""

import json
import logging
import math
import os
from pathlib import Path
from typing import Optional, List, Tuple, Dict

log = logging.getLogger("thammen.gis_preload")


# ============================================================
# IN-MEMORY STORE
# ============================================================

_DISTRICTS: List[Dict] = []
_BY_NUMBER: Dict[int, Dict] = {}
_BY_ANAME: Dict[str, Dict] = {}


def load_districts(path: Optional[str] = None) -> List[Dict]:
    """تحميل قاعدة بيانات المناطق من ملف JSON.

    Args:
        path: مسار الملف. الافتراضي: qatar_districts.json في المجلد الحالي.

    Returns:
        قائمة المناطق المحمّلة (مكاش global أيضاً).
    """
    global _DISTRICTS, _BY_NUMBER, _BY_ANAME

    if path is None:
        # Try multiple locations
        candidates = [
            os.getenv("GIS_DISTRICTS_PATH"),
            "qatar_districts.json",
            "/app/qatar_districts.json",
        ]
        for c in candidates:
            if c and Path(c).exists():
                path = c
                break

    if not path or not Path(path).exists():
        log.warning(f"GIS districts file not found at {path}")
        return []

    log.info(f"Loading GIS districts from {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    _DISTRICTS = data.get('districts', [])
    _BY_NUMBER = {d['dist_no']: d for d in _DISTRICTS if d.get('dist_no')}
    _BY_ANAME = {d['aname']: d for d in _DISTRICTS if d.get('aname')}

    log.info(f"Loaded {len(_DISTRICTS)} districts into memory")
    return _DISTRICTS


# ============================================================
# QUERY FUNCTIONS (all in-memory, no network)
# ============================================================

def get_district_by_number(dist_no: int) -> Optional[Dict]:
    """احصل على منطقة بـ DIST_NO."""
    return _BY_NUMBER.get(dist_no)


def get_district_by_name(aname: str) -> Optional[Dict]:
    """احصل على منطقة بالاسم العربي."""
    return _BY_ANAME.get(aname.strip())


def get_district_centroid(dist_no: int) -> Optional[Tuple[float, float]]:
    """احصل على مركز المنطقة (lat, lon) — فوري بدون شبكة."""
    d = _BY_NUMBER.get(dist_no)
    if d and d.get('centroid'):
        return tuple(d['centroid'])  # (lat, lon)
    return None


def haversine_distance_m(lat1: float, lon1: float,
                          lat2: float, lon2: float) -> float:
    """المسافة بالأمتار بين نقطتين GPS."""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_districts_within_radius(
    lat: float, lon: float, radius_m: int = 2000
) -> List[Dict]:
    """ابحث عن كل المناطق ضمن نصف قطر معين — فوري بدون شبكة.

    Args:
        lat, lon: نقطة البحث
        radius_m: نصف القطر بالأمتار (default 2000 = 2 كم)

    Returns:
        قائمة المناطق مع مسافة كل منها من نقطة البحث (مرتبة بالأقرب).
    """
    if not _DISTRICTS:
        log.warning("Districts not loaded — call load_districts() first")
        return []

    results = []
    # Bbox-based pre-filter (much faster than haversine for everything)
    # Convert radius to rough lat/lon delta (1 deg ≈ 111 km)
    delta_deg = radius_m / 111000 * 1.5  # 1.5x for safety margin

    for d in _DISTRICTS:
        centroid = d.get('centroid')
        if not centroid:
            continue
        c_lat, c_lon = centroid
        # Quick bbox filter
        if abs(c_lat - lat) > delta_deg or abs(c_lon - lon) > delta_deg:
            continue
        # Precise distance
        dist = haversine_distance_m(lat, lon, c_lat, c_lon)
        if dist <= radius_m:
            results.append({**d, 'distance_m': dist})

    return sorted(results, key=lambda r: r['distance_m'])


def find_nearest_district(lat: float, lon: float) -> Optional[Dict]:
    """أقرب منطقة لنقطة GPS (يستخدم centroid كتقريب).

    ملاحظة: هذا تقريبي. للدقة الكاملة، استخدم get_district_at_point()
    في qatar_gis.py الذي يستعلم GIS مباشرة.
    """
    candidates = find_districts_within_radius(lat, lon, radius_m=10000)
    return candidates[0] if candidates else None


def get_all_districts() -> List[Dict]:
    """احصل على كل المناطق المحمّلة."""
    return list(_DISTRICTS)


def is_loaded() -> bool:
    """هل تم تحميل البيانات؟"""
    return len(_DISTRICTS) > 0


# ============================================================
# CLI
# ============================================================

def main():
    import sys
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--path', default='qatar_districts.json')
    p.add_argument('--lat', type=float, help='Test radius query at this point')
    p.add_argument('--lon', type=float, help='Test radius query at this point')
    p.add_argument('--radius', type=int, default=2000)
    p.add_argument('--name', help='Lookup district by Arabic name')
    args = p.parse_args()

    districts = load_districts(args.path)
    print(f"Loaded {len(districts)} districts")

    if args.name:
        d = get_district_by_name(args.name)
        if d:
            print(f"\nDistrict: {d['aname']} ({d['ename']})")
            print(f"  DIST_NO: {d['dist_no']}")
            print(f"  Centroid: {d['centroid']}")
            print(f"  Bbox: {d['bbox']}")

    if args.lat and args.lon:
        print(f"\nDistricts within {args.radius}m of ({args.lat}, {args.lon}):")
        nearby = find_districts_within_radius(args.lat, args.lon, args.radius)
        for d in nearby[:10]:
            print(f"  {d['aname']:>25s} | {d['distance_m']:>5.0f}m")


if __name__ == '__main__':
    main()
