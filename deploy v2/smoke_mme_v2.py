"""
smoke_mme_v2.py — MME smoke v2: resolve unknowns from v1

v1 results (2026-05-24 11:10 UTC):
    P1=TRUE   (flow-trigger 200 in 0.88s — Heroku reaches MME)
    P2=TRUE   (JWT held across 12 kpi29 calls, no 401)
    P3=FALSE  (Pearl  n=0)   <-- but JWT was role=null, may be auth issue
    P4=FALSE  (Lusail n=0)   <-- same
    P5=UNDETERMINED  (no rows)
    P6=UNDETERMINED  (kpi30/31/32 = 404 — wrong path?)
    P7=UNDETERMINED  (no rent rows)
    P8=TRUE   (areaCode alone returned 200 — but 0 rows; weak signal)

The JWT had {"role": null, "app_access": false, "admin_access": false,
"iss": "directus"} — an anonymous Directus token. 0 records could be a
permission artifact, NOT a genuine "no apartment sales in Pearl/Lusail".

v2 targets, in order of decisiveness:

    A. Dump RAW response body for one kpi29 call (find where records hide,
       if anywhere; confirm 0 is genuinely 0 or just our extractor missing them).
    B. Try rent paths with /transactions suffix (sell uses
       /sell/kpi29/transactions; rent may need same pattern).
    C. Vary propertyTypeList ([5], [1], [6], [], omitted) to see if 5
       (apartments) returns nothing while others return something.
    D. Decode JWT claims completely (header + payload + signature length).
    E. Print all response headers (Content-Type, rate limits, custom MME tags).
    F. Try mimicking browser request (Origin, Referer, X-Requested-With) —
       sometimes a CORS/Origin check filters API responses by header.

Run from Heroku:
    heroku run python smoke_mme_v2.py

Read-only. No writes. Exit 0 on auth success, 1 on auth fail.
"""

import base64
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

AUTH_TOKEN = "412A3B92-16F9-437D-AAFC-BBE5E25ED9F5"
AUTH_URL = f"https://qrepcms.aqarat.gov.qa/flows/trigger/{AUTH_TOKEN}"
KPI_BASE = "https://qrepbe.aqarat.gov.qa/mme-services/kpi"
SALES_URL = f"{KPI_BASE}/sell/kpi29/transactions"

TIMEOUT_S = 30
HEADERS_BASE = {
    "User-Agent": "thammen-mme-smoke-v2/1.0",
    "Accept": "application/json",
}
# Browser-mimic variant for Step F
HEADERS_BROWSER = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ar-QA,ar;q=0.9,en;q=0.8",
    "Origin": "https://www.mme.gov.qa",
    "Referer": "https://www.mme.gov.qa/",
    "X-Requested-With": "XMLHttpRequest",
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _b64_decode(s):
    s = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s.encode("ascii"))


def jwt_decode(jwt):
    parts = jwt.split(".")
    if len(parts) != 3:
        return None, None, len(jwt), "not 3-part"
    try:
        header = json.loads(_b64_decode(parts[0]))
    except Exception as e:
        header = f"<decode err: {e}>"
    try:
        payload = json.loads(_b64_decode(parts[1]))
    except Exception as e:
        payload = f"<decode err: {e}>"
    sig_len = len(parts[2])
    return header, payload, sig_len, None


def http_call(method, url, body=None, headers=None, timeout=TIMEOUT_S, label=""):
    """Returns dict: {status, body_text, body_json, headers, latency_s, error}"""
    t0 = time.time()
    h = dict(HEADERS_BASE)
    if headers:
        h.update(headers)
    if body is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    else:
        data = None

    if label:
        print(f"  >> {label}")
    print(f"     {method} {url}")
    if body is not None:
        print(f"     body: {json.dumps(body, ensure_ascii=False)}")
    if "Origin" in h:
        print(f"     headers: Origin={h.get('Origin')}, Referer={h.get('Referer')}")

    try:
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            latency = time.time() - t0
            resp_headers = dict(resp.headers)
            print(f"     HTTP {resp.status}  ({latency:.2f}s)  body_len={len(raw)}")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
            return {
                "status": resp.status, "body_text": raw, "body_json": parsed,
                "headers": resp_headers, "latency": latency, "error": None,
            }
    except urllib.error.HTTPError as e:
        latency = time.time() - t0
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        resp_headers = dict(e.headers) if hasattr(e, 'headers') and e.headers else {}
        print(f"     HTTP {e.code}  ({latency:.2f}s)  body_len={len(raw)}  ERR")
        return {
            "status": e.code, "body_text": raw, "body_json": None,
            "headers": resp_headers, "latency": latency, "error": f"HTTPError {e.code}",
        }
    except urllib.error.URLError as e:
        latency = time.time() - t0
        print(f"     URLError: {e.reason}")
        return {"status": None, "body_text": None, "body_json": None,
                "headers": {}, "latency": latency, "error": f"URLError: {e.reason}"}
    except Exception as e:
        latency = time.time() - t0
        print(f"     {type(e).__name__}: {e}")
        return {"status": None, "body_text": None, "body_json": None,
                "headers": {}, "latency": latency, "error": f"{type(e).__name__}: {e}"}


def find_jwt(parsed):
    """Find JWT-shaped string in JSON. Returns (jwt, source_path)."""
    found = []

    def scan(o, path=""):
        if isinstance(o, str) and o.count(".") == 2 and len(o) > 40:
            try:
                _b64_decode(o.split(".")[0])  # header decodes?
                found.append((o, path))
            except Exception:
                pass
        elif isinstance(o, dict):
            for k, v in o.items():
                scan(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                scan(v, f"{path}[{i}]")

    if isinstance(parsed, str) and parsed.count(".") == 2 and len(parsed) > 40:
        return parsed, "root (string)"
    scan(parsed)
    if found:
        return found[0]
    return None, None


# -----------------------------------------------------------------------------
# Step A: Auth + full JWT decode
# -----------------------------------------------------------------------------

def step_auth():
    print("=" * 78)
    print("STEP A: AUTH + FULL JWT DECODE")
    print("=" * 78)

    res = http_call("GET", AUTH_URL, label="flow-trigger")
    if res["status"] != 200 or res["body_text"] is None:
        print(f"  AUTH FAIL")
        return None, None

    print()
    print(f"  Raw response body (first 1500 chars):")
    print(f"  {res['body_text'][:1500]}")
    print()
    print(f"  Response headers:")
    for k, v in sorted(res["headers"].items()):
        print(f"    {k}: {v}")
    print()

    # Try to find JWT
    parsed = res["body_json"]
    if isinstance(parsed, dict) or isinstance(parsed, list):
        jwt, src = find_jwt(parsed)
    elif isinstance(parsed, str):
        jwt, src = (parsed, "root (string)") if parsed.count(".") == 2 else (None, None)
    else:
        # body may be a bare JWT string with quotes
        text = res["body_text"].strip().strip('"')
        if text.count(".") == 2 and len(text) > 40:
            jwt = text
            src = "bare string body"
        else:
            jwt = None
            src = None

    if not jwt:
        print("  *** NO JWT FOUND in auth response ***")
        return None, parsed

    print(f"  JWT location: {src}")
    print(f"  JWT length:   {len(jwt)}")

    header, payload, sig_len, err = jwt_decode(jwt)
    print(f"  JWT header:   {json.dumps(header, ensure_ascii=False)}")
    print(f"  JWT payload:  {json.dumps(payload, ensure_ascii=False)}")
    print(f"  JWT sig len:  {sig_len}")
    if err:
        print(f"  decode warning: {err}")

    if isinstance(payload, dict):
        # Highlight permission-relevant claims
        perm_keys = [k for k in payload.keys() if any(t in k.lower() for t in
                     ("role", "perm", "access", "scope", "admin", "user", "id"))]
        if perm_keys:
            print(f"  permission-relevant claims: {perm_keys}")
        iat = payload.get("iat")
        exp = payload.get("exp")
        if iat:
            print(f"  issued at:  {datetime.utcfromtimestamp(iat).isoformat()}Z")
        if exp:
            ttl_s = exp - int(time.time())
            print(f"  expires at: {datetime.utcfromtimestamp(exp).isoformat()}Z (TTL ~{ttl_s}s)")
        else:
            print(f"  no exp claim — token has no expiry (or unbounded)")

    return jwt, parsed


# -----------------------------------------------------------------------------
# Step B: One kpi29 call — DUMP RAW BODY to find records
# -----------------------------------------------------------------------------

def step_dump_kpi29(jwt):
    print()
    print("=" * 78)
    print("STEP B: kpi29 RAW BODY DUMP (Pearl 2025 full year)")
    print("=" * 78)

    body = {
        "issueDateYear": 2025, "StartMonth": 1, "EndMonth": 12,
        "areaCode": 765, "propertyTypeList": [5],
    }
    headers = {"Authorization": f"Bearer {jwt}"}
    res = http_call("POST", SALES_URL, body=body, headers=headers, label="kpi29 (apartments, Pearl 2025)")

    print()
    print(f"  Response headers:")
    for k, v in sorted(res["headers"].items()):
        print(f"    {k}: {v}")

    print()
    print(f"  RAW body (first 3000 chars):")
    print(f"  {res['body_text'][:3000] if res['body_text'] else '<empty>'}")
    print()
    print(f"  body_json type: {type(res['body_json']).__name__}")
    if isinstance(res["body_json"], dict):
        print(f"  body_json TOP keys: {list(res['body_json'].keys())}")
        # Look deeper for any list
        def find_lists(o, path="", depth=0):
            if depth > 3:
                return
            if isinstance(o, list):
                print(f"    list at {path}: len={len(o)}" +
                      (f", sample={json.dumps(o[0], ensure_ascii=False)[:200]}" if o and len(o) > 0 else ""))
            elif isinstance(o, dict):
                for k, v in o.items():
                    find_lists(v, f"{path}.{k}", depth + 1)
        find_lists(res["body_json"])
    elif isinstance(res["body_json"], list):
        print(f"  body_json IS a list: len={len(res['body_json'])}")
    return res


# -----------------------------------------------------------------------------
# Step C: propertyTypeList variants
# -----------------------------------------------------------------------------

def step_propertytype_variants(jwt):
    print()
    print("=" * 78)
    print("STEP C: propertyTypeList VARIANTS (find a type that returns rows)")
    print("=" * 78)

    headers = {"Authorization": f"Bearer {jwt}"}
    base_body = {"issueDateYear": 2025, "StartMonth": 1, "EndMonth": 12, "areaCode": 765}

    variants = [
        ("apartments [5]",      {**base_body, "propertyTypeList": [5]}),
        ("villas [1]",          {**base_body, "propertyTypeList": [1]}),
        ("land [6]",            {**base_body, "propertyTypeList": [6]}),
        ("all [1,5,6]",         {**base_body, "propertyTypeList": [1, 5, 6]}),
        ("empty []",            {**base_body, "propertyTypeList": []}),
        ("field omitted",       dict(base_body)),
    ]

    for label, body in variants:
        res = http_call("POST", SALES_URL, body=body, headers=headers, label=label)
        # quick row count
        n = _count_anything_listy(res["body_json"])
        print(f"     -> body_json type={type(res['body_json']).__name__}  any-list-found_n={n}")
        if res["body_text"] and len(res["body_text"]) < 600:
            print(f"     full body: {res['body_text']}")
        time.sleep(1)


def _count_anything_listy(parsed):
    """Find the largest list anywhere in the structure."""
    if isinstance(parsed, list):
        return len(parsed)
    if isinstance(parsed, dict):
        biggest = 0
        def walk(o, depth=0):
            nonlocal biggest
            if depth > 4:
                return
            if isinstance(o, list):
                if len(o) > biggest:
                    biggest = len(o)
            elif isinstance(o, dict):
                for v in o.values():
                    walk(v, depth + 1)
        walk(parsed)
        return biggest
    return 0


# -----------------------------------------------------------------------------
# Step D: Rent path variants (resolve P6 404)
# -----------------------------------------------------------------------------

def step_rent_paths(jwt):
    print()
    print("=" * 78)
    print("STEP D: RENT PATH VARIANTS (kpi30/31/32 returned 404 in v1)")
    print("=" * 78)

    headers = {"Authorization": f"Bearer {jwt}"}
    body = {
        "issueDateYear": 2025, "StartMonth": 1, "EndMonth": 12,
        "areaCode": 765, "propertyTypeList": [5],
    }

    paths = [
        f"{KPI_BASE}/rent/kpi30",                  # v1 form (404)
        f"{KPI_BASE}/rent/kpi30/transactions",     # mirror sell shape
        f"{KPI_BASE}/rent/kpi30/list",
        f"{KPI_BASE}/rent/kpi30/data",
        f"{KPI_BASE}/rents/kpi30/transactions",    # plural rents
        f"{KPI_BASE}/lease/kpi30/transactions",    # different verb
        f"{KPI_BASE}/rental/kpi30/transactions",
    ]
    for url in paths:
        res = http_call("POST", url, body=body, headers=headers, label=f"probe {url.split('/mme-services/')[-1]}")
        if res["body_text"] and len(res["body_text"]) < 400:
            print(f"     body: {res['body_text']}")
        time.sleep(1)

    # Also try GET on a directory-style URL (some APIs list children)
    res = http_call("GET", f"{KPI_BASE}/rent", headers=headers, label="GET /rent (directory list?)")
    if res["body_text"] and len(res["body_text"]) < 400:
        print(f"     body: {res['body_text']}")


# -----------------------------------------------------------------------------
# Step E: Browser-mimic on kpi29 (Origin/Referer/X-Requested-With)
# -----------------------------------------------------------------------------

def step_browser_mimic(jwt):
    print()
    print("=" * 78)
    print("STEP E: BROWSER-MIMIC headers on kpi29 (CORS / Origin filter check)")
    print("=" * 78)

    body = {
        "issueDateYear": 2025, "StartMonth": 1, "EndMonth": 12,
        "areaCode": 765, "propertyTypeList": [5],
    }
    headers = dict(HEADERS_BROWSER)
    headers["Authorization"] = f"Bearer {jwt}"

    res = http_call("POST", SALES_URL, body=body, headers=headers,
                    label="kpi29 with Mozilla UA + Origin + Referer + X-Requested-With")
    n = _count_anything_listy(res["body_json"])
    print(f"     -> any-list-found_n={n}")
    if res["body_text"] and len(res["body_text"]) < 1200:
        print(f"     body: {res['body_text']}")


# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------

def main():
    t0 = time.time()
    print("MME SMOKE v2 — UNKNOWN RESOLUTION")
    print(f"Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    jwt, _ = step_auth()
    if not jwt:
        print("\n*** Step A FAILED — cannot proceed. ***")
        return 1

    step_dump_kpi29(jwt)
    step_propertytype_variants(jwt)
    step_rent_paths(jwt)
    step_browser_mimic(jwt)

    print()
    print("=" * 78)
    print(f"FINISHED in {time.time() - t0:.1f}s")
    print("Findings to interpret:")
    print("  1. JWT claims (Step A): are role/app_access non-null? Token expiry?")
    print("  2. kpi29 raw body (Step B): is the records array somewhere we missed?")
    print("  3. propertyType variants (Step C): does any value return rows?")
    print("  4. Rent path (Step D): which suffix returns non-404?")
    print("  5. Browser-mimic (Step E): does Origin/Referer flip the empty result?")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
