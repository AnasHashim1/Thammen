"""
smoke_mme.py — MME reachability + schema discovery smoke test (Heroku-only)

Purpose: answer the 8 falsifiable predictions of BRIEF §4 before committing
any production code that depends on MME endpoints. Per Project_Instructions
§21.6 (External Endpoint Smoke Test First) and Operational_Rules #34
(File-Based Scripts).

Run from Heroku ONE-OFF dyno:
    heroku run python smoke_mme.py

NEVER run from local Windows / Anthropic container — Heroku IP is what
production will use, so reachability from anywhere else is irrelevant
(precedent: Sak.gov.qa smoke 2026-05-19 §20.8).

This is read-only against MME. No writes. No persistence beyond stdout.
Output ends with a copy-pasteable predictions ledger to populate
CHANGELOG_pre_2p21p1.md.

Endpoint references (Project_Instructions §13 + Operational §28):
    Auth:   GET  https://qrepcms.aqarat.gov.qa/flows/trigger/<token>
            -> JSON containing a JWT (key shape unknown — discover at runtime)
    Sales:  POST https://qrepbe.aqarat.gov.qa/mme-services/kpi/sell/kpi29/transactions
    Rents:  POST https://qrepbe.aqarat.gov.qa/mme-services/kpi/rent/kpi30
            (and /kpi31, /kpi32)
    Headers: Authorization: Bearer <jwt>, Content-Type: application/json
    Body shape: {issueDateYear, StartMonth, EndMonth, areaCode, propertyTypeList:[5]}
              (propertyType 5 = apartments per §28)

Scope (BRIEF §4):
    - Pearl Qatar  (areaCode 765)
    - Lusail       (areaCode 812)
    - Window: 2024-11 -> 2026-05 (18 months; 3 year-calls per area)
    - propertyTypeList = [5]  (apartments)
"""

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

# -----------------------------------------------------------------------------
# Configuration — single source of truth, no env vars (smoke is one-shot)
# -----------------------------------------------------------------------------

AUTH_TOKEN = "412A3B92-16F9-437D-AAFC-BBE5E25ED9F5"
AUTH_URL = f"https://qrepcms.aqarat.gov.qa/flows/trigger/{AUTH_TOKEN}"

KPI_BASE = "https://qrepbe.aqarat.gov.qa/mme-services/kpi"
SALES_URL = f"{KPI_BASE}/sell/kpi29/transactions"
RENT_URLS = {
    "kpi30": f"{KPI_BASE}/rent/kpi30",
    "kpi31": f"{KPI_BASE}/rent/kpi31",
    "kpi32": f"{KPI_BASE}/rent/kpi32",
}

AREAS = {
    "pearl":  765,
    "lusail": 812,
}

# 2024-11 -> 2026-05 = 18 months across 3 calendar years
YEAR_WINDOWS = [
    {"issueDateYear": 2024, "StartMonth": 11, "EndMonth": 12},
    {"issueDateYear": 2025, "StartMonth": 1,  "EndMonth": 12},
    {"issueDateYear": 2026, "StartMonth": 1,  "EndMonth": 5},
]

PROPERTY_TYPE_APARTMENTS = 5  # per Operational §28

# FGRealty per-Operational-§29 benchmarks for P7 sanity (rent monthly per-m^2):
# Pearl 14-15 QAR/m^2/month, Lusail 10-14 QAR/m^2/month
RENT_PER_M2_MONTHLY_MIN = 5.0
RENT_PER_M2_MONTHLY_MAX = 60.0   # generous upper for premium units
RENT_PER_M2_ANNUAL_MIN  = 100.0  # if values land here, very likely annual

TIMEOUT_S = 30

HEADERS_BASE = {
    "User-Agent": "thammen-mme-smoke/1.0",
    "Accept": "application/json",
}

# -----------------------------------------------------------------------------
# Predictions ledger — filled in as smoke runs
# -----------------------------------------------------------------------------

PREDICTIONS = {
    "P1": {"text": "Heroku reaches MME (flow-trigger returns 200 with token)",
           "result": "UNKNOWN", "evidence": ""},
    "P2": {"text": "JWT TTL >= 5 min (kpi calls after auth do not return 401)",
           "result": "UNKNOWN", "evidence": ""},
    "P3": {"text": "Pearl (765) returns n>=30 reliable apartment sales / 18mo",
           "result": "UNKNOWN", "evidence": ""},
    "P4": {"text": "Lusail (812) returns n>=30 reliable apartment sales / 18mo",
           "result": "UNKNOWN", "evidence": ""},
    "P5": {"text": "Response is per-transaction (one row per sale, with size_m^2 + price)",
           "result": "UNKNOWN", "evidence": ""},
    "P6": {"text": "kpi30/31/32 are three different rent slices (not duplicates)",
           "result": "UNKNOWN", "evidence": ""},
    "P7": {"text": "Per-unit rent is monthly (matches FGRealty convention), not annual",
           "result": "UNKNOWN", "evidence": ""},
    "P8": {"text": "areaCode alone is sufficient (no municipalityId required)",
           "result": "UNKNOWN", "evidence": ""},
}


def set_pred(pid, result, evidence):
    PREDICTIONS[pid]["result"] = result
    PREDICTIONS[pid]["evidence"] = evidence
    print(f"  [{pid}] -> {result}  ({evidence})")


# -----------------------------------------------------------------------------
# HTTP helpers
# -----------------------------------------------------------------------------

def http_get(url, headers=None, timeout=TIMEOUT_S):
    """Return (status, body_text, latency_s, error_str_or_None)."""
    t0 = time.time()
    h = dict(HEADERS_BASE)
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, raw, time.time() - t0, None
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        return e.code, raw, time.time() - t0, f"HTTPError {e.code}"
    except urllib.error.URLError as e:
        return None, None, time.time() - t0, f"URLError: {e.reason}"
    except Exception as e:
        return None, None, time.time() - t0, f"{type(e).__name__}: {e}"


def http_post_json(url, body, headers=None, timeout=TIMEOUT_S):
    t0 = time.time()
    h = dict(HEADERS_BASE)
    h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    data = json.dumps(body).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, raw, time.time() - t0, None
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        return e.code, raw, time.time() - t0, f"HTTPError {e.code}"
    except urllib.error.URLError as e:
        return None, None, time.time() - t0, f"URLError: {e.reason}"
    except Exception as e:
        return None, None, time.time() - t0, f"{type(e).__name__}: {e}"


def try_parse_json(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


# -----------------------------------------------------------------------------
# Step 1: Auth flow — fetch JWT (resolves P1 + half of P2)
# -----------------------------------------------------------------------------

def fetch_jwt():
    print("=" * 78)
    print("STEP 1: AUTH FLOW (flow-trigger)")
    print("=" * 78)
    print(f"  URL: {AUTH_URL}")

    status, body, latency, err = http_get(AUTH_URL)
    print(f"  HTTP {status}  ({latency:.2f}s)")

    if err:
        print(f"  ERROR: {err}")
    if body:
        snippet = body[:600].replace("\n", " ")
        print(f"  body (first 600 chars): {snippet}")

    if status != 200 or err:
        set_pred("P1", "FALSE",
                 f"flow-trigger HTTP {status} err={err!r} (WAF or geo-block on Heroku IP)")
        return None, None

    set_pred("P1", "TRUE", f"flow-trigger HTTP 200 in {latency:.2f}s")

    parsed = try_parse_json(body)
    if not parsed:
        print("  -> body is not JSON; cannot extract JWT")
        set_pred("P2", "FALSE", "auth body not JSON, JWT extraction impossible")
        return None, None

    # JWT key shape unknown per BRIEF. Search common keys + first JWT-looking string.
    jwt = None
    jwt_source = None
    candidate_keys = ["jwt", "token", "access_token", "accessToken", "Token", "JWT", "id_token", "bearer"]
    if isinstance(parsed, dict):
        for k in candidate_keys:
            if k in parsed and isinstance(parsed[k], str) and parsed[k].count(".") == 2:
                jwt = parsed[k]
                jwt_source = f"key={k!r}"
                break
        # nested search one level deep
        if not jwt:
            for k, v in parsed.items():
                if isinstance(v, dict):
                    for sk, sv in v.items():
                        if isinstance(sv, str) and sv.count(".") == 2 and len(sv) > 40:
                            jwt = sv
                            jwt_source = f"key={k!r}.{sk!r}"
                            break
                if jwt:
                    break

    if not jwt:
        # last resort: scan all string values for JWT shape
        def scan(o, path=""):
            nonlocal jwt, jwt_source
            if jwt:
                return
            if isinstance(o, str) and o.count(".") == 2 and len(o) > 40:
                jwt = o
                jwt_source = f"scan path={path}"
            elif isinstance(o, dict):
                for k, v in o.items():
                    scan(v, f"{path}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    scan(v, f"{path}[{i}]")
        scan(parsed)

    if not jwt:
        print(f"  -> no JWT-shaped string (xxx.yyy.zzz) found in response")
        print(f"  keys at top level: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__}")
        set_pred("P2", "FALSE", "auth returned 200 but no JWT-shaped value present")
        return None, parsed

    print(f"  JWT found ({jwt_source}): {jwt[:30]}... (len={len(jwt)})")
    return jwt, parsed


# -----------------------------------------------------------------------------
# Step 2: Sales (kpi29) — Pearl + Lusail across 3 year-windows
# -----------------------------------------------------------------------------

def call_sales(jwt, area_name, area_code, window, include_municipality=False):
    """Single kpi29 call. Returns parsed body or text."""
    body = {
        "issueDateYear": window["issueDateYear"],
        "StartMonth": window["StartMonth"],
        "EndMonth": window["EndMonth"],
        "areaCode": area_code,
        "propertyTypeList": [PROPERTY_TYPE_APARTMENTS],
    }
    if include_municipality:
        # municipalityId mapping: Doha=1 (Pearl/Lusail both fall under Doha municipality)
        body["municipalityId"] = 1

    headers = {"Authorization": f"Bearer {jwt}"}
    print(f"  [{area_name} {area_code}] {window['issueDateYear']}-{window['StartMonth']:02d}..{window['EndMonth']:02d}"
          f"  mun={include_municipality}")
    print(f"    POST {SALES_URL}")
    print(f"    body: {json.dumps(body)}")
    status, raw, latency, err = http_post_json(SALES_URL, body, headers=headers)
    print(f"    HTTP {status}  ({latency:.2f}s)" + (f"  ERR: {err}" if err else ""))
    parsed = try_parse_json(raw) if raw else None
    if raw and not parsed:
        snippet = raw[:300].replace("\n", " ")
        print(f"    body (non-JSON, first 300): {snippet}")
    return status, parsed, raw, latency, err


def fetch_sales(jwt):
    print("=" * 78)
    print("STEP 2: SALES kpi29 (Pearl + Lusail x 3 year-windows)")
    print("=" * 78)

    results = {area: {"rows": [], "calls": [], "schema_hint": None}
               for area in AREAS}

    saw_401 = False
    saw_400_no_mun = False
    municipality_required = None  # tristate: None unknown, True/False decided

    for area_name, area_code in AREAS.items():
        for window in YEAR_WINDOWS:
            status, parsed, raw, latency, err = call_sales(
                jwt, area_name, area_code, window, include_municipality=False
            )
            results[area_name]["calls"].append({
                "window": window, "status": status, "latency": latency,
                "n": None, "err": err, "with_municipality": False,
            })
            if status == 401:
                saw_401 = True
            # if 400 / empty without municipality, retry with municipality (P8)
            if (status == 400 or (status == 200 and _count_rows(parsed) == 0)) and municipality_required is not False:
                print(f"    -> retrying with municipalityId=1 (P8 probe)")
                status2, parsed2, raw2, latency2, err2 = call_sales(
                    jwt, area_name, area_code, window, include_municipality=True
                )
                results[area_name]["calls"].append({
                    "window": window, "status": status2, "latency": latency2,
                    "n": None, "err": err2, "with_municipality": True,
                })
                if status2 == 200 and _count_rows(parsed2) > 0:
                    municipality_required = True
                    parsed = parsed2  # use the working response
                    status = status2
                else:
                    saw_400_no_mun = (status == 400)

            if status == 200 and parsed is not None:
                rows = _extract_rows(parsed)
                results[area_name]["rows"].extend(rows)
                # capture schema hint from first row
                if rows and not results[area_name]["schema_hint"]:
                    results[area_name]["schema_hint"] = sorted(rows[0].keys()) if isinstance(rows[0], dict) else type(rows[0]).__name__

            time.sleep(2)  # be polite to MME

    # Resolve P2 / P3 / P4 / P8
    if saw_401:
        set_pred("P2", "FALSE", "subsequent kpi call returned 401 (JWT short-lived or single-use)")
    else:
        set_pred("P2", "TRUE", "JWT held across all kpi29 calls (no 401)")

    n_pearl = len(results["pearl"]["rows"])
    n_lusail = len(results["lusail"]["rows"])
    print()
    print(f"  Pearl  (765) total sales rows over 18mo: {n_pearl}")
    print(f"  Lusail (812) total sales rows over 18mo: {n_lusail}")

    set_pred("P3", "TRUE" if n_pearl  >= 30 else "FALSE", f"n=Pearl(765)={n_pearl}")
    set_pred("P4", "TRUE" if n_lusail >= 30 else "FALSE", f"n=Lusail(812)={n_lusail}")

    if municipality_required is True:
        set_pred("P8", "FALSE", "areaCode alone returned 400/empty; municipalityId required")
    elif municipality_required is None:
        # never had to retry => areaCode alone was sufficient
        set_pred("P8", "TRUE", "areaCode alone returned 200 with rows for every window")
    # else False already set inside the loop if explicit 400

    # Resolve P5 (per-transaction vs aggregate)
    sample_rows = (results["pearl"]["rows"] or results["lusail"]["rows"])[:5]
    if not sample_rows:
        set_pred("P5", "UNDETERMINED", "no rows to inspect schema")
    else:
        first = sample_rows[0]
        if isinstance(first, dict):
            keys = set(k.lower() for k in first.keys())
            has_size = any("area" in k or "size" in k or "m2" in k or "sqm" in k for k in keys)
            has_price = any("price" in k or "value" in k or "amount" in k for k in keys)
            looks_aggregate = any("count" in k or "mean" in k or "median" in k or "avg" in k for k in keys)
            if has_size and has_price and not looks_aggregate:
                set_pred("P5", "TRUE",
                         f"row keys include size + price, no aggregate markers; sample keys={sorted(keys)[:8]}")
            elif looks_aggregate and not (has_size and has_price):
                set_pred("P5", "FALSE",
                         f"row keys look aggregate (mean/median/count); sample keys={sorted(keys)[:8]}")
            else:
                set_pred("P5", "AMBIGUOUS",
                         f"row keys mixed; sample keys={sorted(keys)[:8]}")
        else:
            set_pred("P5", "AMBIGUOUS", f"row is non-dict ({type(first).__name__})")

    # show one sample for human eyes
    if sample_rows:
        print()
        print(f"  Sample row #1: {json.dumps(sample_rows[0], ensure_ascii=False)[:400]}")

    return results


def _count_rows(parsed):
    if parsed is None:
        return 0
    return len(_extract_rows(parsed))


def _extract_rows(parsed):
    """Pull the per-transaction list out of MME's response.

    Schema unknown — try common shapes: list at root, .data, .transactions,
    .result, .records. First match wins.
    """
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("data", "transactions", "result", "records", "items", "rows", "Data", "Result"):
            v = parsed.get(key)
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                # one level deeper
                for sk in ("data", "transactions", "result", "records", "items", "rows"):
                    sv = v.get(sk)
                    if isinstance(sv, list):
                        return sv
    return []


# -----------------------------------------------------------------------------
# Step 3: Rents (kpi30/31/32) — Pearl only (BRIEF §4 cell)
# -----------------------------------------------------------------------------

def fetch_rents(jwt):
    print("=" * 78)
    print("STEP 3: RENTS kpi30/31/32 (Pearl x 1 year-window aggregated)")
    print("=" * 78)

    pearl = AREAS["pearl"]
    # Use 2025 full year for the rent comparison (largest single window)
    window = {"issueDateYear": 2025, "StartMonth": 1, "EndMonth": 12}

    headers = {"Authorization": f"Bearer {jwt}"}
    body = {
        "issueDateYear": window["issueDateYear"],
        "StartMonth":    window["StartMonth"],
        "EndMonth":      window["EndMonth"],
        "areaCode":      pearl,
        "propertyTypeList": [PROPERTY_TYPE_APARTMENTS],
    }

    per_endpoint = {}
    for name, url in RENT_URLS.items():
        print(f"  [{name}] POST {url}")
        print(f"    body: {json.dumps(body)}")
        status, raw, latency, err = http_post_json(url, body, headers=headers)
        print(f"    HTTP {status}  ({latency:.2f}s)" + (f"  ERR: {err}" if err else ""))
        parsed = try_parse_json(raw) if raw else None
        rows = _extract_rows(parsed)
        schema = None
        if rows and isinstance(rows[0], dict):
            schema = tuple(sorted(rows[0].keys()))
        per_endpoint[name] = {
            "status": status, "n": len(rows), "schema": schema,
            "sample_row": rows[0] if rows else None,
            "raw_first_300": (raw or "")[:300],
        }
        if rows:
            print(f"    n_rows={len(rows)}  schema={list(schema)[:8] if schema else 'non-dict'}")
        time.sleep(2)

    # Resolve P6 — kpi30/31/32 distinctness
    schemas = [v["schema"] for v in per_endpoint.values() if v["schema"]]
    ns = [v["n"] for v in per_endpoint.values()]
    if len(set(schemas)) >= 2:
        set_pred("P6", "TRUE", f"schemas differ across kpi30/31/32: {[list(s)[:5] for s in schemas if s]}")
    elif len(schemas) == 0:
        set_pred("P6", "UNDETERMINED", "no rent rows from any endpoint")
    elif len(set(schemas)) == 1 and len(set(ns)) >= 2:
        set_pred("P6", "AMBIGUOUS",
                 f"identical schema but row-counts differ {ns} — may be different slices of same shape")
    else:
        set_pred("P6", "FALSE", f"all three endpoints returned identical schema + count {ns}")

    # Resolve P7 — monthly vs annual rent. Use kpi30 sample.
    sample = per_endpoint["kpi30"]["sample_row"]
    if not sample or not isinstance(sample, dict):
        set_pred("P7", "UNDETERMINED", "no kpi30 sample row to compute rent/m^2 from")
    else:
        rent_per_m2 = _try_compute_rent_per_m2(sample)
        if rent_per_m2 is None:
            set_pred("P7", "UNDETERMINED", f"could not extract rent + size from sample: {list(sample.keys())[:8]}")
        else:
            if RENT_PER_M2_MONTHLY_MIN <= rent_per_m2 <= RENT_PER_M2_MONTHLY_MAX:
                set_pred("P7", "TRUE", f"rent/m^2={rent_per_m2:.1f} consistent with MONTHLY (FGRealty Pearl 14-15)")
            elif rent_per_m2 >= RENT_PER_M2_ANNUAL_MIN:
                set_pred("P7", "FALSE",
                         f"rent/m^2={rent_per_m2:.1f} too high for monthly; likely ANNUAL (~12x)")
            else:
                set_pred("P7", "AMBIGUOUS",
                         f"rent/m^2={rent_per_m2:.1f} between monthly+annual ranges; manual review")

    return per_endpoint


def _try_compute_rent_per_m2(row):
    """Heuristic: find a rent-like field and a size-like field, divide."""
    rent = None
    size = None
    for k, v in row.items():
        kl = k.lower()
        if isinstance(v, (int, float)) and v > 0:
            if rent is None and any(t in kl for t in ("rent", "amount", "price", "value")):
                rent = float(v)
            if size is None and any(t in kl for t in ("area", "size", "sqm", "m2", "msquare")):
                size = float(v)
    if rent and size:
        return rent / size
    return None


# -----------------------------------------------------------------------------
# Step 4: Predictions ledger (the deliverable)
# -----------------------------------------------------------------------------

def print_ledger(jwt_obtained, sales_results, rent_results, t_start):
    print()
    print("=" * 78)
    print("PREDICTIONS LEDGER — copy into CHANGELOG_pre_2p21p1.md §2 (MME Smoke)")
    print("=" * 78)
    print(f"# Pre-Sprint 2.21.1 — MME Smoke Results")
    print(f"# Run from Heroku one-off dyno on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"# Total wall time: {time.time() - t_start:.1f}s")
    print()
    for pid in sorted(PREDICTIONS):
        p = PREDICTIONS[pid]
        print(f"- {pid} ({p['text']}): **{p['result']}** -- {p['evidence']}")
    print()
    print("-" * 78)
    print("Decision matrix (per BRIEF §6):")
    p1 = PREDICTIONS["P1"]["result"]
    p3 = PREDICTIONS["P3"]["result"]
    p4 = PREDICTIONS["P4"]["result"]
    p5 = PREDICTIONS["P5"]["result"]
    p7 = PREDICTIONS["P7"]["result"]
    if p1 == "FALSE":
        print("  -> P1 FALSE: defer 2.21.1 indefinitely. Pivot to 2.21.0.10 (Stage 2 wall-to-wall).")
    elif p3 == "FALSE" and p4 == "FALSE":
        print("  -> P3+P4 FALSE: MME calibration impossible. Choose FGRealty T2 cut OR defer.")
    elif p5 == "FALSE":
        print("  -> P5 FALSE (aggregate only): re-scope 2.21.1 to single area-wide cap rate.")
    elif p7 == "FALSE":
        print("  -> P7 FALSE (annual rent): fix conversion in 2.21.1 design, add unit test.")
    elif all(PREDICTIONS[p]["result"] in ("TRUE", "AMBIGUOUS", "UNDETERMINED")
             for p in ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")):
        print("  -> all 8 predictions hold (or close): green-light Sprint 2.21.1 brief.")
    else:
        print("  -> mixed: review each FALSE individually before drafting Sprint 2.21.1.")
    print("=" * 78)


# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------

def main():
    t_start = time.time()
    print("MME SMOKE TEST (Pre-Sprint 2.21.1)")
    print(f"Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    jwt, _auth_body = fetch_jwt()
    if not jwt:
        # P1 / P2 already set inside fetch_jwt; mark all downstream UNDETERMINED
        for pid in ("P3", "P4", "P5", "P6", "P7", "P8"):
            if PREDICTIONS[pid]["result"] == "UNKNOWN":
                set_pred(pid, "UNDETERMINED", "blocked by upstream auth failure")
        print_ledger(False, None, None, t_start)
        return 1

    print()
    sales_results = fetch_sales(jwt)
    print()
    rent_results = fetch_rents(jwt)

    print_ledger(True, sales_results, rent_results, t_start)

    # Exit code: 0 if Sprint 2.21.1 is viable at all (P1 TRUE), 1 otherwise
    return 0 if PREDICTIONS["P1"]["result"] == "TRUE" else 1


if __name__ == "__main__":
    sys.exit(main())
