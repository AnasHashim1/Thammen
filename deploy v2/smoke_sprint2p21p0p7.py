"""
smoke_sprint2p21p0p7.py — Sprint 2.21.0.7 post-deploy smoke (Safeguard 1).

Hits the REAL public API (POST https://thammen.qa/api/evaluate {"pin": ...}) for
each fixture PIN — exercises the full stack end-to-end (Cloudflare → FastAPI →
classify_asset → live QARS-in-polygon + General_Landuse spatial queries). This is
the verification the offline unit tests cannot give: that the GIS spatial queries
actually work from Heroku for our fixtures.

⚠️ Run on HEROKU (the dyno reaches both thammen.qa and the GIS):
    heroku run python smoke_sprint2p21p0p7.py

PRECEDENCE under test (DECISION 4): QARS building-check > RULEID > geometry.
So a BUILT parcel returns `stop` REGARDLESS of its RULEID — the RULEID-based
reject/warn outcomes apply only to BARE parcels. The `expected` column below is
derived from that precedence + each PIN's probe-observed (QARS, RULEID).
"""
import json
import time
import urllib.request

API = "https://thammen.qa/api/evaluate"
UA = {"User-Agent": "Thammen/smoke_2p21p0p7", "Content-Type": "application/json"}

# (PIN, probe_RULEID, probe_QARS_in_poly, expected_kind, note)
# expected_kind derived from QARS-first precedence:
#   QARS>0 -> 'stop'  (building present, any RULEID)
#   else RULEID: {1,2,20}->'raw_land'(+grid) ; 19->'agricultural' ;
#                {3,4,22}->'warn' ; {5-18,21}->'reject' ; 23->'reject'(mixed) ;
#                None/no-coverage -> 'raw_land' (graceful geometric guard)
# Sprint 2.21.0.7.1: built + CONFIRMED non-residential -> REJECT (was stop);
# built + residential/vacant/unknown -> STOP (use address tab).
FIXTURES = [
    ("74328443", 1,  0, "raw_land",     "residential bare"),
    ("74430180", 1,  0, "raw_land",     "residential bare"),
    ("90421755", 1,  0, "raw_land",     "residential bare"),
    ("90040668", 1,  1, "stop",         "residential BUILT -> stop (unchanged)"),
    ("69050029", 2,  0, "raw_land",     "multi-family bare"),
    ("63090011", 4,  1, "reject",       "offices BUILT -> reject (2.21.0.7.1: was stop)"),
    ("56391498", 10, 0, "reject",       "educational bare"),
    ("52060090", 12, 0, "reject",       "governmental bare"),
    ("69051939", 15, 1, "reject",       "open-space BUILT -> reject (2.21.0.7.1: was stop)"),
    ("63090021", 15, 0, "reject",       "open-space bare"),
    ("66200396", 21, 1, "reject",       "special-use BUILT -> reject (2.21.0.7.1: was stop)"),
    ("66200323", 21, 1, "reject",       "special-use BUILT -> reject"),
    ("52598101", 21, 1, "reject",       "special-use BUILT -> reject"),
    ("69051981", 23, 1, "reject",       "mixed-use BUILT -> reject (2.21.0.7.1: was stop)"),
    ("63090035", None, 0, "graceful",   "no LANDUSE coverage -> graceful (no crash; compound via guard)"),
]


def classify_actual(resp):
    """Reduce an API response to a comparable 'kind' token."""
    atr = resp.get("asset_type_reality")
    if isinstance(atr, dict) and atr.get("action"):
        a = atr["action"]
        if a in ("reject", "stop"):
            return f"{a}:{atr.get('reason')}"
        if a == "warn":
            return "warn"
    at = (resp.get("asset_type") or "").lower()
    if at == "agricultural":
        return "agricultural"
    if at in ("raw_land", "land"):
        return "raw_land+grid" if resp.get("comparable_grid") else "raw_land"
    # out-of-scope without a reality flag (e.g. classified commercial elsewhere)
    rec = (resp.get("reconciliation") or {}).get("status")
    if rec == "out_of_scope":
        return f"oos:{at or '?'}"
    return at or "?"


def kind_matches(expected, actual):
    if expected == "stop":
        return actual.startswith("stop:")
    if expected == "reject":
        return actual.startswith("reject:")
    if expected == "warn":
        return actual == "warn"
    if expected == "raw_land":
        return actual in ("raw_land", "raw_land+grid")
    if expected == "agricultural":
        return actual == "agricultural"
    if expected == "graceful":
        # Just needs to NOT crash and NOT be unclassifiable.
        return not actual.startswith("ERR") and actual != "?"
    return expected == actual


def hit(pin, timeout=40):
    body = json.dumps({"pin": pin}).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers=UA)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8", errors="replace"))
        return resp, round(time.time() - t0, 1), None
    except Exception as e:
        return None, round(time.time() - t0, 1), str(e)[:80]


def main():
    print("=" * 96)
    print("Sprint 2.21.0.7 smoke — POST /api/evaluate {pin}  (precedence: QARS > RULEID > geometry)")
    print("=" * 96)
    print(f"{'PIN':>10} {'RID':>4} {'Q':>2} | {'expected':<10} | {'actual':<22} {'sec':>5} | {'P/F':<4} note")
    print("-" * 96)
    npass = nfail = 0
    for pin, rid, q, expected, note in FIXTURES:
        resp, secs, err = hit(pin)
        if err:
            actual = f"ERR:{err}"
            ok = False
        else:
            actual = classify_actual(resp)
            ok = kind_matches(expected, actual)
        npass += 1 if ok else 0
        nfail += 0 if ok else 1
        rids = str(rid) if rid is not None else "—"
        print(f"{pin:>10} {rids:>4} {q:>2} | {expected:<10} | {actual:<22} {secs:>5} | "
              f"{'PASS' if ok else 'FAIL':<4} {note}")
        time.sleep(7)  # Heroku rate-limit courtesy
    print("-" * 96)
    print(f"RESULT: {npass} PASS / {nfail} FAIL  of {len(FIXTURES)}")
    print("=" * 96)
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
