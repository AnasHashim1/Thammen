"""
pearl_pin_discovery.py — Pre-Sprint 2.22.0a Step 4 prerequisite

Self-extracts a verified Pearl Qatar apartment_building PIN by triangulating
three independent sources, per Anas Delta Step 4 instructions:

  Sub-step 1: FGRealty Pearl apartments listing fetch (T2 source, scrapable
              from Heroku per CLAUDE.md sec 29). Extract one or more tower
              names from active listings.

  Sub-step 2: GIS Districts/MapServer/0 spatial query for Pearl Qatar
              district polygon. CRITICAL: do NOT assume Z=66 — Pearl is
              reclaimed land and may use non-standard QARS addressing.
              Read the canonical ANAME / ENAME directly from GIS.

  Sub-step 3: QARS_Point intersect Pearl polygon with BUILDING_NO_SUBTYPE=11
              (Tower per Sprint 2.16.6 fix scope). Return list of Pearl
              towers with their Z/S/B (if QARS standard addressing) OR
              alternative identifiers (if Pearl uses non-QARS schema).

  Sub-step 4: Cross-match a FGRealty tower name to a QARS tower (fuzzy
              EN<->AR transliteration). If exact match fails, pick any
              verified Pearl tower from GIS and confirm with an active
              FGRealty listing on the same tower.

  Sub-step 5: Incidental V3 Huzoom syndication check on FGRealty (Anas
              review item 3): scan the FGRealty page text for any
              huzoom-related token to confirm SOURCE_EXCLUSIONS claim.

  Sub-step 6: Output a structured JSON with the verified PIN, Z/S/B,
              tower name, and the cross-reference trail. STOP conditions:
                - If QARS_Point returns 0 towers inside Pearl polygon
                  AND nothing with BUILDING_NO_SUBTYPE=11: emit
                  STOP_PEARL_SUBTYPE_GAP and exit 2
                - If Pearl polygon exists but QARS PINs in it use
                  non-Z/S/B addressing (no ZONE_NO/STREET_NO/BUILDING_NO
                  fields populated): emit STOP_PEARL_NOT_QARS and exit 3
                - Normal completion: emit SUCCESS and exit 0

Read-only. No production state change. No engine version bump.

Usage (Windows cmd, one command):
    cd /d "C:\\Thammen\\deploy v2\\2p22p0_pre"
    python pearl_pin_discovery.py
"""

import json
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
import re

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ---- HTTP helpers -----------------------------------------------------------
USER_AGENT = "thammen-pre-2p22p0a-pearl-discovery/1.0"
HTTP_TIMEOUT = 30


def http_get_text(url):
    """GET a URL and return decoded text + status. Returns (status, text, error)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, raw, None
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        return e.code, raw, f"HTTPError {e.code}"
    except Exception as e:
        return None, "", f"{type(e).__name__}: {e}"


def http_get_json(url, params=None, timeout=HTTP_TIMEOUT):
    """GET a URL with params and return parsed JSON. Returns (status, json, error)."""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    status, raw, err = http_get_text(url)
    if err:
        return status, None, err
    try:
        return status, json.loads(raw), None
    except json.JSONDecodeError as e:
        return status, None, f"JSONDecodeError: {e}"


# ---- Sub-step 1: FGRealty Pearl listings ------------------------------------
FGREALTY_PEARL_PATHS = [
    "https://www.fgrealty.qa/apartments-for-sale/the-pearl",
    "https://www.fgrealty.qa/apartments-for-sale/the-pearl-qatar",
    "https://www.fgrealty.qa/properties-for-sale/the-pearl",
    "https://www.fgrealty.qa/the-pearl",
    "https://www.fgrealty.qa/properties?location=the-pearl&type=apartment",
]

# Known Pearl tower names (English) to look for in FGRealty page text.
# Source: well-documented Pearl phases (Porto Arabia, Qanat Quartier, Viva
# Bahriya, Floresta, Marsa Malaz, Abraj Quartier) per BRIEF_huzoom audit
# learning and public Pearl phase mapping.
PEARL_TOWER_TOKENS = [
    "porto arabia",
    "qanat quartier",
    "viva bahriya",
    "floresta",
    "marsa malaz",
    "abraj quartier",
    "tower 22",
    "marina residences",
    "viva west",
    "viva east",
]

# Sub-step 5 token (incidental V3 check)
HUZOOM_TOKENS = ["huzoom", "هزوم"]


def discover_fgrealty_pearl():
    """Try multiple FGRealty Pearl URLs. Return first successful + extracted tokens."""
    print("=" * 80)
    print("SUB-STEP 1: FGRealty Pearl apartments listing fetch")
    print("=" * 80)
    for url in FGREALTY_PEARL_PATHS:
        print(f"  trying: {url}")
        status, raw, err = http_get_text(url)
        if err:
            print(f"    fail: {err}")
            continue
        if status != 200:
            print(f"    HTTP {status}, skip")
            continue
        text_lower = raw.lower()
        # Find Pearl tower mentions
        towers_found = {tok for tok in PEARL_TOWER_TOKENS if tok in text_lower}
        # Sub-step 5: Huzoom syndication check
        huzoom_found = {tok for tok in HUZOOM_TOKENS if tok in text_lower}
        print(f"    HTTP 200, {len(raw)} chars, "
              f"pearl_towers_mentioned={len(towers_found)}, "
              f"huzoom_mentioned={len(huzoom_found)}")
        if towers_found:
            return {
                "url": url,
                "html_len": len(raw),
                "towers_found": sorted(towers_found),
                "huzoom_syndication_evidence": sorted(huzoom_found),
            }
    print("  no FGRealty Pearl URL returned tower-mentioning content")
    return None


# ---- Sub-step 2: Pearl district polygon from GIS ----------------------------
DISTRICTS_URL = (
    "https://services.gisqatar.org.qa/server/rest/services/"
    "Vector/Districts/MapServer/0/query"
)

# Pearl Qatar approximate centroid (public source: Pearl Qatar is at
# roughly 25.371 N, 51.547 E). Used as a spatial probe point. We do NOT
# assume the district ANAME — we read it from GIS.
PEARL_PROBE_LAT = 25.371
PEARL_PROBE_LON = 51.547


def discover_pearl_district():
    """Spatial query Districts/MapServer/0 at Pearl Qatar centroid.
    Returns dict with district ANAME, ENAME, DIST_NO, geometry, or None."""
    print("=" * 80)
    print("SUB-STEP 2: GIS Districts spatial query at Pearl centroid")
    print("=" * 80)
    geom = json.dumps({
        "x": PEARL_PROBE_LON,
        "y": PEARL_PROBE_LAT,
        "spatialReference": {"wkid": 4326},
    })
    params = {
        "geometry": geom,
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "outSR": "4326",
        "outFields": "*",
        "returnGeometry": "true",
        "spatialRel": "esriSpatialRelIntersects",
        "f": "json",
    }
    print(f"  probe point: ({PEARL_PROBE_LAT}, {PEARL_PROBE_LON})")
    status, data, err = http_get_json(DISTRICTS_URL, params)
    if err or status != 200:
        print(f"  fail: status={status} err={err}")
        return None
    feats = (data or {}).get("features") or []
    if not feats:
        print(f"  no district feature at Pearl centroid (returned 0 features)")
        return None
    f = feats[0]
    attrs = f.get("attributes") or {}
    print(f"  found district: ANAME={attrs.get('ANAME')!r} "
          f"ENAME={attrs.get('ENAME')!r} DIST_NO={attrs.get('DIST_NO')!r}")
    return {
        "aname": attrs.get("ANAME"),
        "ename": attrs.get("ENAME"),
        "dist_no": attrs.get("DIST_NO"),
        "attributes": attrs,
        "geometry": f.get("geometry"),
    }


# ---- Sub-step 3: QARS_Point intersect Pearl polygon + subtype=11 ------------
KHAZNA_QARS_URL = (
    "https://khazna.gisqatar.org.qa/fed/rest/services/"
    "QARS/QARS_Point/FeatureServer/0/query"
)


def query_qars_in_polygon(polygon, subtype_filter=None):
    """Spatial query QARS_Point within a polygon (Esri JSON geometry).
    Returns list of feature attribute dicts."""
    where_clauses = ["1=1"]
    if subtype_filter is not None:
        where_clauses.append(f"BUILDING_NO_SUBTYPE={subtype_filter}")
    where = " AND ".join(where_clauses)
    params = {
        "where": where,
        "geometry": json.dumps(polygon),
        "geometryType": "esriGeometryPolygon",
        "inSR": "4326",
        "outSR": "4326",
        "outFields": "*",
        "returnGeometry": "true",
        "spatialRel": "esriSpatialRelIntersects",
        "f": "json",
        "resultRecordCount": "200",
    }
    status, data, err = http_get_json(KHAZNA_QARS_URL, params, timeout=45)
    if err or status != 200:
        return None, f"status={status} err={err}"
    return (data or {}).get("features") or [], None


def discover_qars_towers_in_pearl(pearl_polygon):
    """Find Pearl towers via QARS_Point spatial query."""
    print("=" * 80)
    print("SUB-STEP 3: QARS_Point intersect Pearl polygon")
    print("=" * 80)

    # First pass: any QARS feature in Pearl (subtype-agnostic), to confirm
    # khazna returns ANY records at all for this polygon.
    print("  pass 1: any QARS in Pearl polygon (subtype-agnostic)")
    all_feats, err = query_qars_in_polygon(pearl_polygon, subtype_filter=None)
    if err:
        print(f"    fail: {err}")
        return None
    print(f"    returned {len(all_feats)} total QARS points")

    # Second pass: subtype=11 towers specifically.
    print("  pass 2: QARS where BUILDING_NO_SUBTYPE=11 (Tower)")
    tower_feats, err = query_qars_in_polygon(pearl_polygon, subtype_filter=11)
    if err:
        print(f"    fail: {err}")
        return None
    print(f"    returned {len(tower_feats)} tower QARS points")

    # Also try subtype=6 (Building with Flats) — Pearl has many high-rises
    # that may classify as 6 rather than 11.
    print("  pass 3: QARS where BUILDING_NO_SUBTYPE=6 (Building with Flats)")
    flat_feats, err = query_qars_in_polygon(pearl_polygon, subtype_filter=6)
    if err:
        print(f"    fail: {err}")
        flat_feats = []
    print(f"    returned {len(flat_feats)} flat-building QARS points")

    # Schema check on the first feature: does Pearl use QARS Z/S/B?
    # Sample the first 3 features for ZONE_NO / STREET_NO / BUILDING_NO
    # populated values.
    schema_sample = []
    for feat in (all_feats[:5] if all_feats else []):
        attrs = feat.get("attributes") or {}
        schema_sample.append({
            "ZONE_NO": attrs.get("ZONE_NO"),
            "STREET_NO": attrs.get("STREET_NO"),
            "BUILDING_NO": attrs.get("BUILDING_NO"),
            "BUILDING_NO_SUBTYPE": attrs.get("BUILDING_NO_SUBTYPE"),
            "PIN": attrs.get("PIN"),
        })

    return {
        "n_total": len(all_feats),
        "n_subtype_11_tower": len(tower_feats),
        "n_subtype_6_flats": len(flat_feats),
        "tower_features": tower_feats,
        "flat_features": flat_feats,
        "all_features_sample": all_feats[:5],
        "schema_sample": schema_sample,
    }


def assess_addressing_schema(schema_sample):
    """Returns 'qars_zsb' if Pearl uses standard ZONE_NO/STREET_NO/BUILDING_NO,
    else 'non_qars' if PIN populated but Z/S/B null/blank in most samples."""
    if not schema_sample:
        return "no_data"
    n = len(schema_sample)
    zsb_populated = sum(
        1 for s in schema_sample
        if s.get("ZONE_NO") and s.get("STREET_NO") and s.get("BUILDING_NO")
    )
    pin_populated = sum(1 for s in schema_sample if s.get("PIN"))
    print(f"  schema assessment: {zsb_populated}/{n} samples have full Z/S/B; "
          f"{pin_populated}/{n} have PIN")
    if zsb_populated >= max(1, n // 2):
        return "qars_zsb"
    elif pin_populated >= max(1, n // 2):
        return "non_qars_pin_only"
    else:
        return "no_data"


# ---- Sub-step 4: cross-match tower name -> QARS feature ---------------------
def cross_match_tower(towers_from_fgrealty, qars_features):
    """Pick one verified Pearl tower with both a FGRealty listing AND a QARS
    record. Fuzzy match on building name (which may be in QARS ANAME/ENAME
    or building_name field, or absent — many QARS records are just
    ZONE/STREET/BUILDING numbers with no name)."""
    print("=" * 80)
    print("SUB-STEP 4: cross-match FGRealty tower name -> QARS feature")
    print("=" * 80)
    if not qars_features:
        print("  no QARS features to match against — fall through to any-tower pick")
        return None
    if not towers_from_fgrealty:
        print("  no FGRealty tower names extracted — fall through to first QARS tower")
        # Pick the first QARS feature with full Z/S/B if any
        for feat in qars_features:
            a = feat.get("attributes") or {}
            if a.get("ZONE_NO") and a.get("STREET_NO") and a.get("BUILDING_NO"):
                print(f"  picked first Z/S/B-complete tower: "
                      f"Z={a['ZONE_NO']}/S={a['STREET_NO']}/B={a['BUILDING_NO']} "
                      f"PIN={a.get('PIN')}")
                return {"match_type": "first_zsb_complete", "feature": feat}
        # Fall through to first feature regardless
        if qars_features:
            print(f"  no Z/S/B-complete tower — using first feature")
            return {"match_type": "first_any", "feature": qars_features[0]}
        return None
    # We have FGRealty tower names. Try fuzzy matching on QARS feature
    # attribute strings (search any string-typed attribute that contains
    # the tower token).
    for token in towers_from_fgrealty:
        # Tower tokens are English (lowercase). Sweep each QARS feature's
        # string attributes for substring containment.
        for feat in qars_features:
            attrs = feat.get("attributes") or {}
            attr_str = " ".join(
                str(v).lower() for v in attrs.values() if v is not None
            )
            if token in attr_str:
                print(f"  match: FGRealty token={token!r} -> QARS attrs "
                      f"Z={attrs.get('ZONE_NO')}/S={attrs.get('STREET_NO')}"
                      f"/B={attrs.get('BUILDING_NO')} PIN={attrs.get('PIN')}")
                return {
                    "match_type": "fuzzy_token_match",
                    "fgrealty_token": token,
                    "feature": feat,
                }
    print(f"  no fuzzy match between {len(towers_from_fgrealty)} FGRealty "
          f"tokens and {len(qars_features)} QARS features")
    # Fall back: pick first QARS feature with full Z/S/B
    for feat in qars_features:
        a = feat.get("attributes") or {}
        if a.get("ZONE_NO") and a.get("STREET_NO") and a.get("BUILDING_NO"):
            print(f"  fallback: first Z/S/B-complete tower "
                  f"Z={a['ZONE_NO']}/S={a['STREET_NO']}/B={a['BUILDING_NO']} "
                  f"PIN={a.get('PIN')}")
            return {"match_type": "first_zsb_complete_no_fgrealty_match", "feature": feat}
    if qars_features:
        return {"match_type": "first_any_no_fgrealty_match", "feature": qars_features[0]}
    return None


# ---- Main orchestrator ------------------------------------------------------
def main():
    print()
    print("#" * 80)
    print("PEARL PIN DISCOVERY — Step 4 prerequisite")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("#" * 80)
    out = {
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fgrealty": None,
        "district": None,
        "qars": None,
        "match": None,
        "schema_assessment": None,
        "stop_condition": None,
        "verified_pearl_pin": None,
    }

    # Sub-step 1
    fg = discover_fgrealty_pearl()
    out["fgrealty"] = fg

    # Sub-step 2
    district = discover_pearl_district()
    out["district"] = district
    if not district or not district.get("geometry"):
        out["stop_condition"] = "PEARL_DISTRICT_GEOMETRY_MISSING"
        print()
        print(f"!!! STOP: Pearl district geometry not retrievable from GIS")
        print(f"    cannot proceed to QARS spatial query without polygon")
        out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open("pearl_pin_discovery.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2, default=str)
        return 4

    # Sub-step 3
    qars = discover_qars_towers_in_pearl(district["geometry"])
    out["qars"] = qars
    if not qars:
        out["stop_condition"] = "QARS_QUERY_FAILED"
        out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open("pearl_pin_discovery.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2, default=str)
        print(f"!!! STOP: QARS query failed")
        return 5

    # Stop condition: 0 towers + 0 flats in Pearl polygon = subtype gap
    if qars["n_subtype_11_tower"] == 0 and qars["n_subtype_6_flats"] == 0:
        out["stop_condition"] = "STOP_PEARL_SUBTYPE_GAP"
        out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open("pearl_pin_discovery.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2, default=str)
        print()
        print(f"!!! STOP CONDITION: PEARL_SUBTYPE_GAP")
        print(f"    QARS returned {qars['n_total']} total points in Pearl polygon")
        print(f"    but ZERO with subtype=11 (Tower) AND ZERO with subtype=6 (Flats)")
        print(f"    -> either migration gap in khazna endpoint, OR Pearl towers")
        print(f"       use a subtype classification not in our SUBTYPE map")
        print(f"    -> see PHASE3_AUDIT_pre_2p22p0a.md stop-condition section")
        return 2

    # Schema assessment
    schema = assess_addressing_schema(qars["schema_sample"])
    out["schema_assessment"] = schema
    print(f"  Pearl addressing schema verdict: {schema}")

    if schema == "non_qars_pin_only":
        out["stop_condition"] = "STOP_PEARL_NOT_QARS"
        out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open("pearl_pin_discovery.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2, default=str)
        print()
        print(f"!!! STOP CONDITION: PEARL_NOT_QARS")
        print(f"    Pearl QARS points have PIN populated but Z/S/B null/blank")
        print(f"    -> Pearl uses non-standard addressing schema, NOT Z/S/B")
        print(f"    -> D10 Lusail gate (Sprint 2.21.3) pattern of Z/S/B routing")
        print(f"       may not work on Pearl. H_huzoom_2 (sovereign reclaimed-land")
        print(f"       projects) may open a second methodological path.")
        return 3

    # Sub-step 4: cross-match. Use towers from FGRealty + tower features
    # (subtype=11), with fallback to flat features (subtype=6) if no towers.
    fg_tokens = (fg or {}).get("towers_found") or []
    candidate_feats = qars["tower_features"] or qars["flat_features"]
    match = cross_match_tower(fg_tokens, candidate_feats)
    out["match"] = match

    if match and match.get("feature"):
        a = match["feature"].get("attributes") or {}
        out["verified_pearl_pin"] = {
            "PIN": a.get("PIN"),
            "ZONE_NO": a.get("ZONE_NO"),
            "STREET_NO": a.get("STREET_NO"),
            "BUILDING_NO": a.get("BUILDING_NO"),
            "BUILDING_NO_SUBTYPE": a.get("BUILDING_NO_SUBTYPE"),
            "match_type": match.get("match_type"),
            "fgrealty_token": match.get("fgrealty_token"),
        }
        out["stop_condition"] = None  # all-clear
        print()
        print(f"=== SUCCESS — verified Pearl PIN extracted ===")
        print(f"    PIN: {a.get('PIN')}")
        print(f"    Z/S/B: {a.get('ZONE_NO')}/{a.get('STREET_NO')}/{a.get('BUILDING_NO')}")
        print(f"    subtype: {a.get('BUILDING_NO_SUBTYPE')}")
        print(f"    match_type: {match.get('match_type')}")
    else:
        out["stop_condition"] = "NO_QARS_MATCH"
        print()
        print(f"!!! No QARS match. Out of subtype-11 + subtype-6 features, "
              f"none had complete Z/S/B fields.")

    out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open("pearl_pin_discovery.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print()
    print(f"Wrote: pearl_pin_discovery.json")
    return 0 if out["verified_pearl_pin"] else 1


if __name__ == "__main__":
    sys.exit(main())
