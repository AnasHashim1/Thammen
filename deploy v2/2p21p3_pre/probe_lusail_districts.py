"""
probe_lusail_districts.py — Sprint 2.21.3 fix audit

Post-deploy verification on 2026-05-24 revealed D10 gate string-match bug:
  PIN 69/329/20 (Lusail apt, confirmed by Anas) returns
  district='غار ثعيلب' from Vector/Districts/MapServer/0 ANAME.
  Current gate `'لوسيل' in district_ar` rejects it.

To fix without guessing, this probe queries Districts layer via spatial
intersect with a Lusail-municipality bbox + 6 known Lusail lat/lon
anchor points, and extracts every distinct (ANAME, ENAME) pair within.

The captured list will populate `LUSAIL_DISTRICTS_AR` in evaluate_unified.py
(Rule E13 — coded-value domains are authoritative; pull them, never guess).

Output: stdout markdown bracketed by ===LUSAIL_DISTRICTS_BEGIN===/...END===.
"""

from __future__ import annotations
import json
import sys
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DISTRICTS_URL = (
    "https://services.gisqatar.org.qa/server/rest/services/Vector/Districts/MapServer/0/query"
)
TIMEOUT = 20
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"

# Lusail municipality bounding box (approximate envelope, WGS84).
# Covers Marina, Fox Hills, Energy City, Waterfront, Madinat Lusail.
LUSAIL_BBOX = {
    "xmin": 51.45,
    "ymin": 25.36,
    "xmax": 51.55,
    "ymax": 25.50,
    "spatialReference": {"wkid": 4326},
}

# Anchor points to cross-check the bbox sweep (in case the envelope misses
# pockets). One known reference: PIN 69/329/20 → 'غار ثعيلب'.
LUSAIL_ANCHORS = [
    ("Fox Hills (known: 69/329/20)", 25.41,  51.50),
    ("Lusail Marina north",           25.435, 51.49),
    ("Lusail Energy City",            25.42,  51.485),
    ("Waterfront District",           25.40,  51.51),
    ("Madinat Lusail central",        25.45,  51.51),
    ("Qetaifan Islands",              25.46,  51.54),
]


def _post(url, params):
    body = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": UA,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return None, str(e)


def query_bbox():
    print("\n=== STAGE 1: Districts within Lusail bbox ===")
    params = {
        "f": "json",
        "where": "1=1",
        "geometry": json.dumps(LUSAIL_BBOX),
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "ANAME,ENAME,DIST_NO",
        "returnGeometry": "false",
    }
    s, body = _post(DISTRICTS_URL, params)
    print(f"HTTP {s}, body len={len(body)}")
    if s != 200:
        return []
    try:
        data = json.loads(body)
    except Exception as e:
        print(f"JSON decode failed: {e}")
        return []
    feats = data.get("features", [])
    out = []
    for f in feats:
        a = f.get("attributes", {})
        out.append({
            "ANAME": a.get("ANAME"),
            "ENAME": a.get("ENAME"),
            "DIST_NO": a.get("DIST_NO"),
            "source": "bbox",
        })
    print(f"bbox features: {len(out)}")
    for o in out:
        print(f"  - DIST_NO={o['DIST_NO']:4}  ANAME={o['ANAME']!r:30}  ENAME={o['ENAME']!r}")
    return out


def query_point(name, lat, lon):
    geom = json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}})
    params = {
        "f": "json",
        "where": "1=1",
        "geometry": geom,
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "ANAME,ENAME,DIST_NO",
        "returnGeometry": "false",
    }
    s, body = _post(DISTRICTS_URL, params)
    if s != 200:
        return None
    try:
        feats = json.loads(body).get("features", [])
    except Exception:
        return None
    if not feats:
        return None
    a = feats[0].get("attributes", {})
    return {
        "ANAME": a.get("ANAME"),
        "ENAME": a.get("ENAME"),
        "DIST_NO": a.get("DIST_NO"),
        "source": f"anchor:{name}",
    }


def query_anchors():
    print("\n=== STAGE 2: Anchor-point cross-check ===")
    out = []
    for name, lat, lon in LUSAIL_ANCHORS:
        r = query_point(name, lat, lon)
        if r:
            print(f"  ({lat},{lon}) {name}: ANAME={r['ANAME']!r}")
            out.append(r)
        else:
            print(f"  ({lat},{lon}) {name}: NO HIT")
    return out


def emit_summary(all_rows):
    """Dedupe by (ANAME, DIST_NO), emit markdown."""
    seen = {}
    for r in all_rows:
        key = (r.get("ANAME"), r.get("DIST_NO"))
        if key not in seen:
            seen[key] = r
    unique = sorted(seen.values(), key=lambda r: (r.get("ANAME") or ""))
    print("\n===LUSAIL_DISTRICTS_BEGIN===")
    print(f"# Lusail Districts — empirical capture {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("")
    print("| DIST_NO | ANAME (Arabic) | ENAME (English) | source |")
    print("|---:|---|---|---|")
    for r in unique:
        print(f"| {r.get('DIST_NO', '?')} | "
              f"`{r.get('ANAME') or ''}` | "
              f"`{r.get('ENAME') or ''}` | "
              f"{r.get('source', '?')} |")
    print("")
    print("```python")
    print("LUSAIL_DISTRICTS_AR = frozenset({")
    for r in unique:
        if r.get("ANAME"):
            print(f"    {r['ANAME']!r},")
    print("})")
    print("LUSAIL_DISTRICTS_EN_LOWER = frozenset({")
    for r in unique:
        if r.get("ENAME"):
            print(f"    {r['ENAME'].lower()!r},")
    print("})")
    print("```")
    print("===LUSAIL_DISTRICTS_END===")


def main():
    print("Sprint 2.21.3 D10-fix audit — Lusail Districts discovery")
    print(f"Started {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    rows = []
    rows.extend(query_bbox())
    rows.extend(query_anchors())
    emit_summary(rows)
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
