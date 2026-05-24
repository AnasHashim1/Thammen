"""
audit_post_2p18p1p1.py — Local regression audit against thammen.qa/api

Runs from local Windows (or anywhere curl + python work). Hits public
production. Read-only. No side effects.

Purpose: verify the 5-release marathon (v97 -> v101 = 2.18.0 / 2.18.1 /
2.18.1.1 + Sprint 2.21.0.9) didn't regress the user-visible response on
the 4 regression-critical paths.

Per CLAUDE.md production state at audit time:
    Engine version expected: thammen-sprint2p18p1p1-compound-misroute-fix
    Heroku release v101 (2026-05-24 morning)

Pass/fail criteria per BRIEF §3:
    PASS = all active cases HTTP 200 (or documented A6 503) +
           /api/health engine tag matches +
           51/835/17 returns compound_large with valuation_amount=None
           (NOT compound_small with broken arithmetic, the pre-2.18.1.1 bug)
    FAIL = any of: regression on 51/835/17, wrong engine tag, raw_land
           template reverts, uncatalogued 5xx

Usage (Windows cmd):
    cd /d "C:\\Thammen\\deploy v2\\2p21p1_pre"
    python audit_post_2p18p1p1.py

Exits 0 on PASS, 1 on FAIL.

DEVIATIONS FROM BRIEF (Rule #39):

  1. Brief said case 2 must return "compound_large at ~218M".
     Actual post-2.18.1.1 behavior: compound_large with valuation_amount=
     None (clean Income Approach refusal). The 218M was the BROKEN land
     value pre-fix; Patch C now returns None when land > valuation.
     Source: Session_Log §15.4, post-deploy probe vs Anas's 9/9 visual.
     Fix: assert valuation_amount IS None and asset_type == compound_large.

  2. Case 3 (52/903/90 with pin=<centroid>) needs the centroid PIN, which
     isn't documented anywhere. Left as a parametrizable case with a
     TODO; defaults to skipped. The PIN-tab path is still covered by
     case 6 (bare-land الخور 74328443) at the user-flow level.

  3. Cases 4 + 5 (Pearl + Lusail apartment baselines) need real Z/S/B
     that Anas knows but aren't in the docs. Commented out by default,
     fillable. Per BRIEF "If you don't have apartment Z/S/B handy,
     comment out cases 4 and 5 — the audit will still verify the
     regression-critical cases".
"""

import json
import sys
import time
import urllib.request
import urllib.error

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

API_BASE = "https://thammen.qa/api"
EXPECTED_ENGINE_PREFIX = "thammen-sprint2p18p1p1"  # v101 = 2.18.1.1
TIMEOUT_S = 45  # P95 ceiling per BRIEF is 35s; give a small buffer for cold-dyno

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "thammen-audit-post-2p18p1p1/1.0",
    "Accept": "application/json",
}

# Active cases — these run by default.
# Cases 3, 4, 5 commented (require additional inputs Anas must supply).
CASES = [
    {
        "id": "case_1_safe_baseline_52_903_90",
        "kind": "address",
        "body": {"zone": 52, "street": 903, "building": 90},
        "purpose": "A6-safe latency baseline. CLAUDE.md mislabels this 'safe_villa_52'; "
                   "Session_Log §14.1 confirms it's actually DCF fast-path "
                   "(apartment_building, no rent -> valuation=None refusal).",
        "expect_status": 200,
        "expect_asset_type_in": ["apartment_building"],
        "expect_valuation_kind": "none",        # DCF refusal w/o rent input
        "max_latency_s": 10.0,                  # fast-path, was ~4.5s post-2.18.1.1
    },
    {
        "id": "case_2_compound_misroute_regression_51_835_17",
        "kind": "address",
        "body": {"zone": 51, "street": 835, "building": 17},
        "purpose": "Sprint 2.18.1.1 fix verification — MUST be compound_large + valuation_amount=None.",
        "expect_status": 200,
        "expect_asset_type_in": ["compound_large"],
        "expect_valuation_kind": "none",        # MUST be None (clean refusal)
        "must_not_have_negative_arithmetic": True,
        "max_latency_s": 35.0,
    },
    # {
    #     "id": "case_3_villa_centroid_pin_tab",
    #     "kind": "pin",
    #     "body": {"pin": "TODO_FILL_52_903_90_CENTROID_PIN"},
    #     "purpose": "Sprint 2.21.0.7.1 — built-on-PIN via PIN tab must REJECT.",
    #     "expect_status": 200,
    #     "expect_reality_check_outcome": "reject",
    #     "max_latency_s": 35.0,
    # },
    # {
    #     "id": "case_4_pearl_apartment_baseline",
    #     "kind": "address",
    #     "body": {"zone": "TODO", "street": "TODO", "building": "TODO"},
    #     "purpose": "Sprint 2.21.1 baseline — apartment_building today expected.",
    #     "expect_status": 200,
    #     "expect_asset_type_in": ["apartment_building"],
    #     "max_latency_s": 35.0,
    # },
    # {
    #     "id": "case_5_lusail_apartment_baseline",
    #     "kind": "address",
    #     "body": {"zone": "TODO", "street": "TODO", "building": "TODO"},
    #     "purpose": "Sprint 2.21.1 baseline — second area.",
    #     "expect_status": 200,
    #     "expect_asset_type_in": ["apartment_building"],
    #     "max_latency_s": 35.0,
    # },
    {
        "id": "case_6_bare_land_pin_alkhor_74328443",
        "kind": "pin",
        "body": {"pin": "74328443"},
        "purpose": "Sprint 2.21.0.5 polish — bare-land template must render clean.",
        "expect_status": 200,
        "expect_asset_type_in": ["raw_land"],
        "expect_no_template_leak": True,  # no 'نوع غير معروف', no 'None/None/None'
        "max_latency_s": 35.0,
    },
]

# -----------------------------------------------------------------------------
# HTTP helpers
# -----------------------------------------------------------------------------

def http_get_json(url, timeout=TIMEOUT_S):
    """Returns (status, body_dict_or_text, latency_s, error_str_or_None)."""
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            latency = time.time() - t0
            try:
                return resp.status, json.loads(raw), latency, None
            except json.JSONDecodeError:
                return resp.status, raw, latency, "non-json body"
    except urllib.error.HTTPError as e:
        latency = time.time() - t0
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        return e.code, raw, latency, f"HTTPError {e.code}"
    except urllib.error.URLError as e:
        latency = time.time() - t0
        return None, None, latency, f"URLError: {e.reason}"
    except Exception as e:
        latency = time.time() - t0
        return None, None, latency, f"{type(e).__name__}: {e}"


def http_post_json(url, body, timeout=TIMEOUT_S):
    """Returns (status, body_dict_or_text, latency_s, error_str_or_None)."""
    t0 = time.time()
    data = json.dumps(body).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            latency = time.time() - t0
            try:
                return resp.status, json.loads(raw), latency, None
            except json.JSONDecodeError:
                return resp.status, raw, latency, "non-json body"
    except urllib.error.HTTPError as e:
        latency = time.time() - t0
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        return e.code, raw, latency, f"HTTPError {e.code}"
    except urllib.error.URLError as e:
        latency = time.time() - t0
        return None, None, latency, f"URLError: {e.reason}"
    except Exception as e:
        latency = time.time() - t0
        return None, None, latency, f"{type(e).__name__}: {e}"


# -----------------------------------------------------------------------------
# Checks
# -----------------------------------------------------------------------------

def check_health():
    """Step 0: verify /api/health returns the expected engine version."""
    print("=" * 78)
    print("STEP 0: /api/health")
    print("=" * 78)
    status, body, latency, err = http_get_json(f"{API_BASE}/health", timeout=15)
    print(f"  HTTP {status}  ({latency:.2f}s)")
    if err:
        print(f"  ERROR: {err}")
        return False, None
    # api.py exposes two fields: `version` (api package ver, "3.1.0-sprint<TAG>")
    # and `engine_version` (canonical ENGINE_VERSION, "thammen-sprint...").
    # Prefer engine_version — that's the one that bumps each Sprint.
    engine = (body or {}).get("engine_version") or (body or {}).get("version")
    api_version = (body or {}).get("version")
    print(f"  engine_version: {engine!r}")
    if api_version and api_version != engine:
        print(f"  api version:    {api_version!r}")
    moj_age = (body or {}).get("data_freshness", {}).get("age_days")
    if moj_age is not None:
        print(f"  MoJ data age (days): {moj_age}")
    ok = bool(engine) and engine.startswith(EXPECTED_ENGINE_PREFIX)
    print(f"  EXPECTED prefix: {EXPECTED_ENGINE_PREFIX!r} -> {'PASS' if ok else 'FAIL'}")
    return ok, engine


def check_case(case):
    """Run one audit case. Returns (passed: bool, summary: dict)."""
    cid = case["id"]
    print("-" * 78)
    print(f"CASE {cid}")
    print(f"  {case['purpose']}")
    print(f"  body: {json.dumps(case['body'], ensure_ascii=False)}")

    # skip TODO bodies defensively (paranoia in case someone uncomments without filling)
    if any(v == "TODO" or (isinstance(v, str) and v.startswith("TODO_")) for v in case["body"].values()):
        print(f"  SKIPPED — body has TODO placeholder; fill in to enable this case.")
        return None, {"id": cid, "skipped": True}

    url = f"{API_BASE}/evaluate"
    status, body, latency, err = http_post_json(url, case["body"])

    # latency budget per case
    over_budget = latency > case.get("max_latency_s", 35.0)

    # extract fields of interest
    if isinstance(body, dict):
        asset_type = body.get("asset_type")
        valuation = body.get("valuation_amount")
        land = body.get("land_value")
        building = body.get("building_value")
        mu_level = (body.get("material_uncertainty") or {}).get("mu_level")
        engine = body.get("engine_version")
        decomp_status = (body.get("decomposition") or {}).get("status") \
            if isinstance(body.get("decomposition"), dict) else None
        scope_id = (body.get("scope") or {}).get("status_id") if isinstance(body.get("scope"), dict) else None
        # legacy fields raw_land response uses
        address_block_text = json.dumps(body, ensure_ascii=False)[:2000]
    else:
        asset_type = valuation = land = building = mu_level = engine = decomp_status = scope_id = None
        address_block_text = (body or "")[:2000] if isinstance(body, str) else ""

    print(f"  HTTP {status}  ({latency:.2f}s){'  ** OVER BUDGET **' if over_budget else ''}")
    if err:
        print(f"  ERROR: {err}")
    print(f"  engine_version: {engine!r}")
    print(f"  asset_type:     {asset_type!r}")
    print(f"  valuation_amount: {valuation!r}")
    print(f"  land_value:       {land!r}")
    print(f"  building_value:   {building!r}")
    print(f"  mu_level:         {mu_level!r}")
    if decomp_status is not None:
        print(f"  decomposition.status: {decomp_status!r}")

    # ---- evaluate pass/fail per case-specific rules ----
    fails = []

    # status
    exp_status = case.get("expect_status", 200)
    if status != exp_status:
        # A6 catalogued: 503 on slow paths is documented (no longer expected post-2.18.1, but tolerate)
        if status == 503:
            fails.append(f"HTTP 503 (A6 latency — was supposedly closed by 2.18.1; investigate)")
        else:
            fails.append(f"HTTP {status} != expected {exp_status}")

    # asset_type
    exp_types = case.get("expect_asset_type_in")
    if exp_types and asset_type not in exp_types:
        fails.append(f"asset_type {asset_type!r} not in {exp_types}")

    # valuation kind
    vk = case.get("expect_valuation_kind")
    if vk == "none":
        if valuation is not None:
            fails.append(f"valuation_amount should be None (clean refusal); got {valuation!r}")
    elif vk == "number":
        if not isinstance(valuation, (int, float)) or valuation is None or valuation <= 0:
            fails.append(f"valuation_amount should be a positive number; got {valuation!r}")

    # Patch C universal guard: land_value must NOT exceed valuation_amount (silent arithmetic bug)
    if case.get("must_not_have_negative_arithmetic"):
        if isinstance(land, (int, float)) and isinstance(valuation, (int, float)):
            if land > valuation:
                fails.append(
                    f"PATCH C FAILURE: land_value ({land}) > valuation_amount ({valuation}) — "
                    f"the exact bug 2.18.1.1 Patch C closes"
                )
        if isinstance(building, (int, float)) and building < 0:
            fails.append(
                f"PATCH C FAILURE: building_value ({building}) is negative — "
                f"the exact silent arithmetic failure pre-2.18.1.1"
            )

    # raw_land template leak check (Sprint 2.21.0.5 polish)
    if case.get("expect_no_template_leak"):
        leak_markers = [
            "نوع غير معروف",          # scope label leak (pre-2.21.0.5)
            "None/None/None",          # address leak (pre-2.21.0.5)
            '"building_value": -',     # negative building value
        ]
        for marker in leak_markers:
            if marker in address_block_text:
                fails.append(f"raw_land template leak: found {marker!r} in response")

    # over-budget latency is a soft fail unless it's a known A6 case
    if over_budget:
        fails.append(f"latency {latency:.2f}s > {case.get('max_latency_s')}s")

    if fails:
        print(f"  -> FAIL")
        for f in fails:
            print(f"     - {f}")
        return False, {"id": cid, "fails": fails, "latency": latency, "status": status}
    else:
        print(f"  -> PASS")
        return True, {"id": cid, "latency": latency, "status": status}


def main():
    print("=" * 78)
    print(f"POST-2.18.1.1 REGRESSION AUDIT")
    print(f"Target: {API_BASE}")
    print(f"Expected engine prefix: {EXPECTED_ENGINE_PREFIX}")
    print(f"Timeout per case: {TIMEOUT_S}s")
    print("=" * 78)

    overall_pass = True

    # Health check first
    health_ok, engine = check_health()
    if not health_ok:
        print("\n*** health check FAILED — aborting before per-case checks. ***")
        return 1

    # Per-case checks
    results = []
    print()
    for case in CASES:
        ok, summary = check_case(case)
        results.append((ok, summary))
        if ok is False:
            overall_pass = False
        # Heroku rate limit ~10/min during audits; brief mentions ~7s sleep
        time.sleep(7)

    # Summary
    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    passed = sum(1 for ok, _ in results if ok is True)
    failed = sum(1 for ok, _ in results if ok is False)
    skipped = sum(1 for ok, _ in results if ok is None)
    print(f"  Cases run:    {len(results)}")
    print(f"  PASS:         {passed}")
    print(f"  FAIL:         {failed}")
    print(f"  SKIPPED:      {skipped}")
    print(f"  engine_version observed: {engine!r}")
    if failed > 0:
        print()
        print("  Failing cases:")
        for ok, s in results:
            if ok is False:
                print(f"    - {s['id']}: {s.get('fails', [])}")

    if overall_pass and failed == 0:
        print()
        print("  >>> AUDIT PASS — safe to proceed to MME smoke (Step 4)")
        return 0
    else:
        print()
        print("  >>> AUDIT FAIL — STOP. Do NOT run MME smoke. File a hotfix Sprint.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
