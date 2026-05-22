"""
probe_landuse.py — Sprint 2.21.0.7 pre-Sprint audit (Priorities 1 + 2).

VERIFY-BEFORE-BUILD (Rule #33/#45/#46, §21.6). Two unverified premises:
  P1: a SPATIAL QARS_Point query at a PIN's polygon detects building presence
      (so a villa PIN entered via the land tab is NOT mis-typed raw_land).
  P2: General_Landuse RULEID at the plot centroid + the proposed code map
      (1/2 residential, 3/4 commercial, 19 agricultural, 20 vacant, 22 tourism,
      23 mixed). General_Landuse is NOT yet in qatar_gis ENDPOINTS → new layer.

For each input PIN (and optionally a resolved villa z/s/b), reports:
  - PDAREA, centroid
  - QARS_Point count intersecting the plot bbox  (building present?)
  - General_Landuse attributes at centroid (RULEID + all fields, to confirm the
    field name and observed value)

⚠️ Run on HEROKU (GIS unreachable from the Claude container):
    heroku run python probe_landuse.py 90040668 74328443 ... [--villa Z S B]
"""
import json
import sys
import urllib.parse
import urllib.request

GIS_BASE = "https://services.gisqatar.org.qa/server/rest/services"
LANDUSE_URL = f"{GIS_BASE}/Vector/General_Landuse/MapServer/0/query"
UA = {"User-Agent": "Thammen/probe_landuse"}


def _get(url, params, timeout=20):
    q = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(q, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def landuse_at(lon, lat):
    geom = json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}})
    try:
        data = _get(LANDUSE_URL, {
            "geometry": geom, "geometryType": "esriGeometryPoint", "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects", "outFields": "*",
            "returnGeometry": "false", "f": "json",
        })
        feats = data.get("features") or []
        if not feats:
            return {"_note": "no General_Landuse feature at point"}
        return feats[0].get("attributes", {})
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {str(e)[:120]}"}


def qars_buildings_in_bbox(gis, bbox):
    """Count QARS_Point features intersecting the plot bbox (building present?)."""
    from qatar_gis import ENDPOINTS
    xmin, ymin, xmax, ymax = bbox
    env = {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax,
           "spatialReference": {"wkid": 4326}}
    try:
        data = _get(ENDPOINTS["qars"], {
            "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope",
            "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
            "returnCountOnly": "true", "f": "json",
        })
        return data.get("count")
    except Exception as e:
        return f"ERR {str(e)[:80]}"


def main(pins, villa_zsb=None):
    import qatar_gis as qg
    gis = qg.QatarGIS(verbose=False)

    # Optionally resolve a known villa address -> PIN (tests P1 building detection).
    if villa_zsb:
        z, s, b = villa_zsb
        loc = gis.find_property(z, s, b)
        if loc and loc.pin:
            print(f"[villa] {z}/{s}/{b} -> PIN {loc.pin} (QARS building exists by definition)")
            pins = [str(loc.pin)] + list(pins)

    print("=" * 72)
    print("Sprint 2.21.0.7 audit — QARS-spatial (P1) + General_Landuse RULEID (P2)")
    print("=" * 72)
    for pin in pins:
        plot = gis.get_plot(pin)
        if not plot:
            print(f"PIN {pin}: NOT FOUND")
            continue
        ring = plot.polygon_4326 or []
        cx = sum(p[0] for p in ring) / len(ring) if ring else None
        cy = sum(p[1] for p in ring) / len(ring) if ring else None
        bbox = plot.bbox_4326
        qcount = qars_buildings_in_bbox(gis, bbox) if bbox else "no-bbox"
        lu = landuse_at(cx, cy) if cx else {"_note": "no centroid"}
        ruleid = lu.get("RULEID", lu.get("ruleid", "<no RULEID field>"))
        print(f"\nPIN {pin}: PDAREA={plot.pdarea:,.0f} centroid=({cx:.5f},{cy:.5f})")
        print(f"   QARS in bbox = {qcount}  (>0 ⇒ building present ⇒ NOT raw land)")
        print(f"   General_Landuse RULEID = {ruleid}")
        print(f"   landuse attrs = { {k: lu[k] for k in list(lu)[:10]} }")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    villa = None
    if "--villa" in args:
        i = args.index("--villa")
        villa = tuple(int(x) for x in args[i + 1:i + 4])
        args = args[:i]
    pins = [a.strip() for a in args if a.strip()]
    if not pins and not villa:
        print("usage: python probe_landuse.py <PIN> [...] [--villa ZONE STREET BUILDING]")
        sys.exit(2)
    sys.exit(main(pins, villa_zsb=villa))
