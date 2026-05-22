"""
probe_landuse_hunt.py — Sprint 2.21.0.7 audit #2 (rebuild verified baseline).

Two jobs:
  A. RE-TEST the original 5 PINs with QARS *polygon-intersect* (not bbox) to
     resolve the QARS discrepancy (bbox catches a NEIGHBOUR's building → false
     positive). Polygon-intersect = "is a QARS building inside THIS plot?".
  B. HUNT PINs across RULEID classes in known commercial/mixed/industrial/public
     areas → fixtures for RULEID 2/3/4/19/23 (currently only 1 and 12 are seen).

Per plot reports: PIN · PDAREA · RULEID · BUILDING_HEIGHT · QARS-in-polygon.
QARS-in-polygon > 0 ⇒ a building exists ON the plot ⇒ NOT raw land.

⚠️ Run on HEROKU (GIS unreachable from container):
    heroku run python probe_landuse_hunt.py
"""
import json
import urllib.parse
import urllib.request

GIS_BASE = "https://services.gisqatar.org.qa/server/rest/services"
LANDUSE_URL = f"{GIS_BASE}/Vector/General_Landuse/MapServer/0/query"
UA = {"User-Agent": "Thammen/probe_landuse_hunt"}

RETEST_PINS = ["90040668", "74328443", "74430180", "90421755", "52060090"]
# (name, lat, lon) — Anas-provided candidate areas for RULEID diversity.
HUNT_AREAS = [
    ("Lusail commercial",  25.42,   51.50),
    ("Pearl mixed-use",    25.367,  51.546),
    ("West Bay commercial", 25.32,  51.527),
    ("Industrial Doha",    25.215,  51.494),
    ("Education City",     25.317,  51.443),
]
PINS_PER_AREA = 3


def _get(url, params, timeout=20):
    # POST (not GET) so large polygon geometries don't blow the URL length
    # limit (HTTP 414 — hit on the Pearl plot's many-vertex polygon). ESRI
    # /query accepts form-encoded POST. Audit-only; production qatar_gis is
    # untouched (the POST migration there, if needed for P1, goes in the brief).
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=UA)  # data => POST
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def landuse_at(lon, lat):
    geom = json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}})
    try:
        d = _get(LANDUSE_URL, {"geometry": geom, "geometryType": "esriGeometryPoint",
                               "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
                               "outFields": "*", "returnGeometry": "false", "f": "json"})
        f = (d.get("features") or [{}])[0].get("attributes", {})
        return f.get("RULEID", "?"), f.get("BUILDING_HEIGHT", "?")
    except Exception as e:
        return f"ERR:{str(e)[:40]}", "?"


def qars_in_polygon(ring):
    """Count QARS_Point features INSIDE the plot polygon (tight; not bbox)."""
    from qatar_gis import ENDPOINTS
    geom = json.dumps({"rings": [ring], "spatialReference": {"wkid": 4326}})
    try:
        d = _get(ENDPOINTS["qars"], {"geometry": geom, "geometryType": "esriGeometryPolygon",
                                     "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
                                     "returnCountOnly": "true", "f": "json"})
        return d.get("count")
    except Exception as e:
        return f"ERR:{str(e)[:40]}"


def _report(gis, pin, tag=""):
    plot = gis.get_plot(pin)
    if not plot or not plot.polygon_4326:
        print(f"  PIN {pin}{tag}: NOT FOUND / no polygon")
        return
    ring = plot.polygon_4326
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    ruleid, height = landuse_at(cx, cy)
    q = qars_in_polygon(ring)
    print(f"  PIN {pin}{tag}: PDAREA={plot.pdarea:,.0f} RULEID={ruleid} "
          f"height={height} QARS-in-poly={q} "
          f"-> {'BUILT' if isinstance(q,int) and q>0 else 'BARE' if q==0 else '?'}")


def _cadastre_pins_near(lon, lat, half=0.0008, limit=PINS_PER_AREA):
    from qatar_gis import ENDPOINTS
    env = {"xmin": lon - half, "ymin": lat - half, "xmax": lon + half,
           "ymax": lat + half, "spatialReference": {"wkid": 4326}}
    try:
        d = _get(ENDPOINTS["cadastre"], {
            "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope",
            "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
            "outFields": "PIN", "returnGeometry": "false", "f": "json"})
        pins = [str(f["attributes"].get("PIN")) for f in (d.get("features") or [])
                if f.get("attributes", {}).get("PIN")]
        return pins[:limit]
    except Exception as e:
        return [f"ERR:{str(e)[:40]}"]


def main():
    import qatar_gis as qg
    gis = qg.QatarGIS(verbose=False)
    print("=" * 74)
    print("A. RE-TEST original 5 PINs — QARS polygon-intersect (resolves bbox discrepancy)")
    print("=" * 74)
    for pin in RETEST_PINS:
        _report(gis, pin)

    print("\n" + "=" * 74)
    print("B. HUNT PINs across RULEID classes (commercial / mixed / industrial / public)")
    print("=" * 74)
    for name, lat, lon in HUNT_AREAS:
        print(f"\n[{name}] ~({lat},{lon})")
        pins = _cadastre_pins_near(lon, lat)
        if not pins:
            print("  (no plots found near this point)")
        for pin in pins:
            if pin.startswith("ERR"):
                print(f"  {pin}")
                continue
            _report(gis, pin)
    print("=" * 74)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
