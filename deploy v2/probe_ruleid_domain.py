"""
probe_ruleid_domain.py — Sprint 2.21.0.7 audit #3 (authoritative RULEID map).

The proposed RULEID→usage map was guessed and is partly wrong (Pearl = 21, not
22/23) and incomplete (10, 21 unmapped; 3/19/22/6-9 unobserved). Rather than
sampling more PINs, fetch the **coded-value domain** that the General_Landuse
layer publishes in its own metadata — the authoritative {code: description} map.

Queries the layer JSON (`?f=json`), finds the RULEID (and BUILDING_HEIGHT /
LANDUSE) fields, and prints their coded-value domains. Small request (no
geometry) → no 414 risk.

⚠️ Run on HEROKU (GIS unreachable from container):
    heroku run python probe_ruleid_domain.py
"""
import json
import urllib.request

LAYER_JSON = ("https://services.gisqatar.org.qa/server/rest/services/"
              "Vector/General_Landuse/MapServer/0?f=json")
UA = {"User-Agent": "Thammen/probe_ruleid_domain"}


def main():
    req = urllib.request.Request(LAYER_JSON, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        meta = json.loads(r.read().decode("utf-8", errors="replace"))

    print("=" * 70)
    print("General_Landuse layer — coded-value domains (authoritative)")
    print(f"layer name: {meta.get('name')}")
    print("=" * 70)
    fields = meta.get("fields") or []
    print("all fields:", [f.get("name") for f in fields])
    for f in fields:
        dom = f.get("domain")
        if dom and dom.get("type") == "codedValue":
            print(f"\n--- {f.get('name')} ({f.get('alias')}) coded values ---")
            for cv in dom.get("codedValues", []):
                print(f"  {cv.get('code')!r:>6} = {cv.get('name')}")
    # Fallback: if RULEID has no domain on this layer, list candidates explicitly.
    if not any((f.get("domain") or {}).get("type") == "codedValue" for f in fields):
        print("\n(no coded-value domains on this layer — RULEID may be a plain int; "
              "check the layer's 'drawingInfo'/renderer for class labels instead)")
        print("renderer:", json.dumps(meta.get("drawingInfo", {}).get("renderer", {}),
                                       ensure_ascii=False)[:1500])
    print("=" * 70)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
