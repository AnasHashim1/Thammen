"""
audit_pre_2p22p0.py — Pre-Sprint 2.22.0 audit (3-stage architecture exploration)

Runs locally against public thammen.qa/api. Read-only. No side effects.

Per BRIEF section4: 7 addresses × 3 reps = 21 requests. Per-rep capture:
    HTTP status, TTFB (approx), TTLB, full response JSON, brief sections,
    per-field speed classification.

Per BRIEF section6: scores 5 falsifiable predictions H1–H5.

Usage (Windows cmd):
    cd /d "C:\\Thammen\\deploy v2\\2p22p0_pre"
    python audit_pre_2p22p0.py

Exits 0 on success (ledger printed). Exit 1 on connectivity blocker.

DEVIATIONS FROM BRIEF (Rule #39):

  1. Brief section4 calls for 30 s spacing "to avoid Heroku throttling". CLAUDE.md
     section14 establishes 7 s as the audit-safe interval (10 req/min Heroku rate
     limit). I interleave the reps (rep 1 of all 7 → 7 s between → rep 2 of
     all 7 → rep 3 of all 7), so any single address sees >= ~60 s between its
     own reps while total wall time stays ~5 min instead of ~11 min. This
     preserves the 30-s-per-address intent without spending budget on
     idle sleep. (What user needs to know: if Heroku still throttles, the
     audit's 503-rate measurement will surface it.)

  2. Cases 6 + 7 left as TODO placeholders (BRIEF row 6: Lusail apartment
     Z/S/B; row 7: commercial address). Anas substitutes; without them,
     H5 is tested partially using case 1 (52/903/90 is apartment_building
     per recent verification) but the Lusail-specific dimension is missing.
"""

import json
import statistics
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict

# Windows cmd default is cp1252 which can't render Unicode arrows / math symbols.
# Reconfigure stdout to utf-8 so the predictions ledger doesn't crash mid-print.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

API_BASE = "https://thammen.qa/api"
REQUEST_TIMEOUT_S = 45
INTER_REQUEST_SLEEP_S = 7      # CLAUDE.md section14: audit-safe interval
REPS_PER_ADDRESS = 3

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "thammen-pre-2p22p0-audit/1.0",
}

# Per BRIEF section4 — 7 addresses, 5 active + 2 TODO
CASES = [
    {
        "id": "c1_apt_52_903_90",
        "body": {"zone": 52, "street": 903, "building": 90},
        "expected_asset_type": "apartment_building",
        "label": "Fast baseline — apartment_building DCF refusal",
    },
    {
        "id": "c2_compound_51_835_17",
        "body": {"zone": 51, "street": 835, "building": 17},
        "expected_asset_type": "compound_large",
        "label": "Slow baseline (A6 case) — compound_large refusal",
    },
    {
        "id": "c3_villa_56_565_21",
        "body": {"zone": 56, "street": 565, "building": 21},
        "expected_asset_type": "standalone_villa",
        "label": "Bou Hamour reference — standalone_villa (multi-QARS path)",
    },
    {
        "id": "c4_rawland_pin_74328443",
        "body": {"pin": "74328443"},
        "expected_asset_type": "raw_land",
        "label": "الخور — raw_land (post-2.21.0.5 polish)",
    },
    {
        "id": "c5_built_pin_90040668",
        "body": {"pin": "90040668"},
        "expected_asset_type": "reject",
        "label": "Built non-residential PIN — reality-check reject",
    },
    # {
    #     "id": "c6_lusail_apartment_TODO",
    #     "body": {"zone": "TODO", "street": "TODO", "building": "TODO"},
    #     "expected_asset_type": "apartment_building",
    #     "label": "Lusail apartment — motivating use case (H5 target)",
    # },
    # {
    #     "id": "c7_commercial_TODO",
    #     "body": {"zone": "TODO", "street": "TODO", "building": "TODO"},
    #     "expected_asset_type": "commercial",
    #     "label": "Commercial address — edge case",
    # },
]


# -----------------------------------------------------------------------------
# Field-speed classification (heuristic — for H2)
# -----------------------------------------------------------------------------
# Fast fields = no GIS/MoJ/DCF call needed once basic classification is done.
# Slow fields = require GIS spatial query, MoJ comparable lookup, DCF, etc.
# Heuristic only — final ground-truth requires profiling production code paths,
# but external view suffices for H2's 30% threshold.

FAST_FIELD_PREFIXES = {
    "asset_type", "asset_type_ar",
    "engine_version", "version",
    "address", "pin", "zone", "street", "building",
    "district", "district_ar", "district_en",
    "scope", "scope_id",
    "classification_confidence",
    "input_mode",
    "subtype_zoning_mismatch",  # already computed in classifier
    "is_shared",                # multi-QARS stage 1 — classifier-level
    "n_qars",
}

SLOW_FIELD_PREFIXES = {
    "valuation_amount", "valuation_method",
    "material_uncertainty",
    "comparable_grid", "comparables",
    "cap_rate_provenance", "cap_rate",
    "decomposition", "land_value", "building_value",
    "negotiation_range", "negotiation",
    "brief",
    "rics_compliant",
    "stock_strata", "stratification",
    "outliers", "outliers_rejected",
    "moj_reference", "moj",
}


def classify_field_speed(key):
    """Return 'fast', 'slow', or 'unknown' for a top-level response key."""
    kl = key.lower()
    for pref in FAST_FIELD_PREFIXES:
        if kl == pref or kl.startswith(pref + "_") or kl.startswith(pref + "."):
            return "fast"
    for pref in SLOW_FIELD_PREFIXES:
        if kl == pref or kl.startswith(pref + "_") or kl.startswith(pref + "."):
            return "slow"
    return "unknown"


# -----------------------------------------------------------------------------
# HTTP
# -----------------------------------------------------------------------------

def post_evaluate(body, timeout=REQUEST_TIMEOUT_S):
    """Returns dict: {status, body_json, body_text, ttfb_s, ttlb_s, error}."""
    data = json.dumps(body).encode("utf-8")
    url = f"{API_BASE}/evaluate"
    t0 = time.time()
    try:
        req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
        resp = urllib.request.urlopen(req, timeout=timeout)
        ttfb = time.time() - t0  # approx — after urlopen returns, headers/status are available
        raw = resp.read().decode("utf-8", errors="replace")
        ttlb = time.time() - t0
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        return {
            "status": resp.status,
            "body_json": parsed,
            "body_text": raw,
            "ttfb_s": ttfb,
            "ttlb_s": ttlb,
            "error": None,
        }
    except urllib.error.HTTPError as e:
        ttlb = time.time() - t0
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        return {
            "status": e.code,
            "body_json": parsed,
            "body_text": raw,
            "ttfb_s": ttlb,  # for HTTPError we only know total
            "ttlb_s": ttlb,
            "error": f"HTTPError {e.code}",
        }
    except urllib.error.URLError as e:
        return {"status": None, "body_json": None, "body_text": None,
                "ttfb_s": time.time() - t0, "ttlb_s": time.time() - t0,
                "error": f"URLError: {e.reason}"}
    except Exception as e:
        return {"status": None, "body_json": None, "body_text": None,
                "ttfb_s": time.time() - t0, "ttlb_s": time.time() - t0,
                "error": f"{type(e).__name__}: {e}"}


def health():
    """Return engine_version string or None."""
    try:
        req = urllib.request.Request(f"{API_BASE}/health", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            parsed = json.loads(resp.read().decode("utf-8", errors="replace"))
            return parsed.get("engine_version") or parsed.get("version"), parsed
    except Exception as e:
        return None, {"error": str(e)}


# -----------------------------------------------------------------------------
# Run audit (interleaved reps)
# -----------------------------------------------------------------------------

def run_audit():
    print("=" * 80)
    print("PRE-SPRINT 2.22.0 AUDIT — 3-stage architecture exploration")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target:  {API_BASE}")
    print(f"Cases:   {len(CASES)} active (BRIEF section4 lists 7; 2 are TODO placeholders)")
    print(f"Reps:    {REPS_PER_ADDRESS} per address = {len(CASES) * REPS_PER_ADDRESS} total")
    print(f"Sleep:   {INTER_REQUEST_SLEEP_S}s between any two requests (Heroku rate-limit safety)")
    print("=" * 80)

    # Health check
    engine, hbody = health()
    print(f"\n  /api/health engine_version: {engine!r}")
    print(f"  freshness age_days: {(hbody or {}).get('data_freshness', {}).get('age_days')!r}")
    if not engine:
        print("  *** health unreachable — aborting ***")
        return None, engine
    print()

    results = []  # list of dicts: case_id, rep, result
    total_reqs = len(CASES) * REPS_PER_ADDRESS
    req_n = 0

    # Interleaved: rep 1 of all → sleep → rep 2 of all → sleep → rep 3 of all
    for rep in range(1, REPS_PER_ADDRESS + 1):
        print(f"\n----- REP {rep} of {REPS_PER_ADDRESS} -----")
        for case in CASES:
            req_n += 1
            # skip TODO
            if any(v == "TODO" for v in (case["body"].values() if isinstance(case["body"], dict) else [])):
                print(f"  [{req_n}/{total_reqs}] {case['id']}  SKIP (TODO placeholder)")
                continue
            print(f"  [{req_n}/{total_reqs}] {case['id']}", end="  ", flush=True)
            res = post_evaluate(case["body"])
            status = res["status"]
            ttlb = res["ttlb_s"]
            asset = (res["body_json"] or {}).get("asset_type")
            val = (res["body_json"] or {}).get("valuation_amount")
            err = res["error"]
            print(f"HTTP {status}  ttlb={ttlb:.2f}s  asset={asset!r}  val={val!r}"
                  f"{'  ERR:' + err if err else ''}")
            results.append({
                "case_id": case["id"],
                "expected_asset_type": case["expected_asset_type"],
                "rep": rep,
                "result": res,
            })
            if req_n < total_reqs:
                time.sleep(INTER_REQUEST_SLEEP_S)

    print(f"\nTotal requests: {req_n}")
    return results, engine


# -----------------------------------------------------------------------------
# Analyze + predictions
# -----------------------------------------------------------------------------

def percentile(values, p):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    if f + 1 < len(s):
        return s[f] + (s[f + 1] - s[f]) * (k - f)
    return s[f]


def analyze(results):
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    # 3.1 Per-address summary
    print("\n### 3.1 Per-address summary\n")
    by_case = defaultdict(list)
    for r in results:
        by_case[r["case_id"]].append(r)

    print(f"{'case_id':<32} {'asset_type':<22} {'reps':<4} {'min/med/max ttlb (s)':<26} {'val=None':<10}")
    print("-" * 100)
    rows_for_h1 = {}
    for cid, runs in by_case.items():
        latencies = [r["result"]["ttlb_s"] for r in runs if r["result"]["error"] is None]
        statuses = [r["result"]["status"] for r in runs]
        # Use first SUCCESSFUL rep for asset_type (a 503 rep has no body)
        first_ok = next((r for r in runs if r["result"]["body_json"]), None)
        actual_asset = (first_ok["result"]["body_json"] or {}).get("asset_type") if first_ok else "<no-json>"
        val_none_count = sum(1 for r in runs
                             if r["result"]["body_json"] and r["result"]["body_json"].get("valuation_amount") is None)
        if latencies:
            mn, md, mx = min(latencies), statistics.median(latencies), max(latencies)
            latency_str = f"{mn:.2f}/{md:.2f}/{mx:.2f}"
        else:
            mn = md = mx = None
            latency_str = "ERR"
        print(f"{cid:<32} {str(actual_asset):<22} {len(runs):<4} {latency_str:<26} {val_none_count}/{len(runs):<10}")
        rows_for_h1[actual_asset or cid] = {
            "latencies": latencies, "statuses": statuses, "case_id": cid,
            "val_none_count": val_none_count, "n_reps": len(runs),
        }

    # 3.2 Per-asset_type p50 + p95
    print("\n### 3.2 Per-asset_type latency (across reps within case)\n")
    print(f"{'asset_type':<24} {'n':<3} {'p50':<8} {'p95':<8} {'>5s?':<6} {'>25s?':<6}")
    print("-" * 60)
    h1_count = 0      # asset_types with p95 > 5s
    h3_under_5s = False
    for asset, info in rows_for_h1.items():
        lats = info["latencies"]
        if not lats:
            print(f"{asset:<24} 0   -        -        -      -")
            continue
        p50 = percentile(lats, 50)
        p95 = percentile(lats, 95)
        over_5 = p95 > 5.0
        over_25 = p95 > 25.0
        if over_5:
            h1_count += 1
        if p50 <= 5.0:
            h3_under_5s = True
        print(f"{str(asset):<24} {len(lats):<3} {p50:<8.2f} {p95:<8.2f} {'YES' if over_5 else 'no':<6} {'YES' if over_25 else 'no':<6}")

    # 3.3 Field-speed classification (for H2)
    print("\n### 3.3 Field-speed classification per case (heuristic)\n")
    print(f"{'case_id':<32} {'fast':<6} {'slow':<6} {'unkn':<6} {'%fast':<8}")
    print("-" * 60)
    pct_fast_per_case = []
    for cid, runs in by_case.items():
        # use the first successful rep
        rep_with_body = next((r for r in runs if r["result"]["body_json"]), None)
        if not rep_with_body:
            print(f"{cid:<32} -      -      -      no JSON")
            continue
        body = rep_with_body["result"]["body_json"]
        keys = list(body.keys())
        fast = sum(1 for k in keys if classify_field_speed(k) == "fast")
        slow = sum(1 for k in keys if classify_field_speed(k) == "slow")
        unkn = sum(1 for k in keys if classify_field_speed(k) == "unknown")
        total = len(keys)
        pct = 100.0 * fast / total if total else 0.0
        pct_fast_per_case.append(pct)
        print(f"{cid:<32} {fast:<6} {slow:<6} {unkn:<6} {pct:<8.1f}")

    # 3.4 Brief structural seams (H4)
    print("\n### 3.4 Brief sections per case (for H4 — structural-seams check)\n")
    h4_seamed_count = 0
    for cid, runs in by_case.items():
        rep_with_body = next((r for r in runs if r["result"]["body_json"]), None)
        if not rep_with_body:
            print(f"{cid:<32} no JSON")
            continue
        body = rep_with_body["result"]["body_json"]
        brief = body.get("brief")
        if isinstance(brief, dict) and isinstance(brief.get("sections"), list):
            sec_ids = [s.get("id") if isinstance(s, dict) else "<non-dict>"
                       for s in brief["sections"]]
            print(f"{cid:<32} {len(sec_ids)} sections: {sec_ids[:8]}")
            if len(sec_ids) >= 3:
                h4_seamed_count += 1
        elif isinstance(brief, dict):
            print(f"{cid:<32} brief is dict but no .sections[]; keys={list(brief.keys())[:8]}")
        elif isinstance(brief, str):
            print(f"{cid:<32} brief is a single string (len={len(brief)}) — monolithic")
        else:
            print(f"{cid:<32} no brief field")

    # ---- Predictions ----
    print("\n" + "=" * 80)
    print("PREDICTIONS LEDGER (H1–H5)")
    print("=" * 80)

    # H1: >=3 of 7 asset_types have p95 > 5s
    # Note: with 5 active cases (2 TODOs skipped), "3 of 7" interpreted as "3 of N tested".
    n_tested = sum(1 for v in rows_for_h1.values() if v["latencies"])
    h1_result = "TRUE" if h1_count >= 3 else "FALSE"
    print(f"H1 (p95 >5s for >=3 of tested asset_types): {h1_result}  "
          f"({h1_count} of {n_tested} tested asset_types had p95>5s)")

    # H2: >=30% of response fields are Stage-1-fast (avg across cases)
    if pct_fast_per_case:
        avg_pct_fast = sum(pct_fast_per_case) / len(pct_fast_per_case)
        h2_result = "TRUE" if avg_pct_fast >= 30.0 else "FALSE"
        print(f"H2 (>=30% fast fields): {h2_result}  "
              f"(avg {avg_pct_fast:.1f}% fast across {len(pct_fast_per_case)} cases)")
    else:
        h2_result = "UNDETERMINED"
        print(f"H2: UNDETERMINED (no responses to classify)")

    # H3: >=1 asset_type with p50 <= 5s
    h3_result = "TRUE" if h3_under_5s else "FALSE"
    print(f"H3 (>=1 asset_type <=5s): {h3_result}")

    # H4: brief has >=3 structural seams
    h4_result = "TRUE" if h4_seamed_count >= 1 else "FALSE"
    print(f"H4 (brief has structural seams): {h4_result}  "
          f"({h4_seamed_count} cases had >=3 sections)")

    # H5: apartment failures timeout-driven (not data-driven)
    # Apartment failure = apartment_building case + (HTTP 5xx OR valuation_amount=None)
    # Timeout-driven = ttlb > 25s OR HTTP 503
    # Data-driven = HTTP 200 + valuation_amount=None + ttlb << 25s
    apt_runs = [r for r in results
                if (r["result"]["body_json"] or {}).get("asset_type") == "apartment_building"]
    apt_failures = []
    apt_timeout_driven = 0
    apt_data_driven = 0
    for r in apt_runs:
        res = r["result"]
        body = res["body_json"] or {}
        val = body.get("valuation_amount")
        if val is None or res["status"] != 200:
            apt_failures.append(r)
            if res["ttlb_s"] > 25.0 or res["status"] == 503:
                apt_timeout_driven += 1
            else:
                apt_data_driven += 1
    if not apt_failures:
        h5_result = "UNDETERMINED — no apartment failures observed"
        print(f"H5 (apt failures timeout-driven): {h5_result}")
    elif apt_timeout_driven > apt_data_driven:
        h5_result = "TRUE"
        print(f"H5 (apt failures timeout-driven): TRUE  "
              f"({apt_timeout_driven} timeout-driven vs {apt_data_driven} data-driven)")
    else:
        h5_result = "FALSE"
        print(f"H5 (apt failures timeout-driven): **FALSE**  "
              f"({apt_data_driven} data-driven vs {apt_timeout_driven} timeout-driven)")
        print(f"     -> Apartment failures are DATA-driven. 3-stage does not solve this.")
        print(f"     -> Reactivate BRIEF_2p21p2 per section8 decision tree.")

    # section8 decision-tree branch
    print("\n" + "=" * 80)
    print("section8 DECISION-TREE BRANCH INDICATED")
    print("=" * 80)
    if h5_result == "FALSE":
        branch = ("H5 FALSE → STRONG signal 3-stage doesn't solve apartments. "
                  "Reactivate BRIEF_2p21p2 (hybrid foundation). "
                  "3-stage stays as future architectural improvement, not blocker for apartments.")
    elif h5_result.startswith("UNDETERMINED"):
        branch = ("H5 UNDETERMINED — no apartment failures captured. "
                  "Need Lusail apartment Z/S/B (case 6) OR a Pearl apartment to test failure mode. "
                  "Decision deferred until case 6 is supplied.")
    else:  # H5 TRUE
        if h1_result == "TRUE" and h4_result == "TRUE":
            branch = "H5 TRUE + H1 TRUE + H4 TRUE → Sprint 2.22.0 viable as planned. Draft brief."
        elif h1_result == "TRUE" and h4_result == "FALSE":
            branch = ("H5 TRUE + H1 TRUE + H4 FALSE → Sprint 2.22.0 scope expands to include "
                      "brief-template refactor. Re-estimate effort.")
        else:  # H1 FALSE
            branch = ("H5 TRUE + H1 FALSE → 3-stage backend over-engineering. "
                      "Build progressive disclosure UI on existing synchronous backend. "
                      "Smaller Sprint, faster.")
    if h2_result == "FALSE":
        branch += " | H2 FALSE → Stage 1 cannot return meaningfully fast — needs preliminary refactor first."
    if h3_result == "FALSE":
        branch += " | H3 FALSE → Stage 1 <=5s budget unrealistic — raise to <=10s (weaker UX) OR include performance Sprint."

    print(branch)
    print()

    return {
        "h1_result": h1_result, "h2_result": h2_result, "h3_result": h3_result,
        "h4_result": h4_result, "h5_result": h5_result,
        "branch": branch,
        "h1_over_count": h1_count, "h1_tested": n_tested,
        "h2_avg_pct_fast": (sum(pct_fast_per_case) / len(pct_fast_per_case)) if pct_fast_per_case else None,
        "h4_seamed_count": h4_seamed_count,
        "apt_timeout_driven": apt_timeout_driven if apt_runs else None,
        "apt_data_driven": apt_data_driven if apt_runs else None,
    }


def main():
    t0 = time.time()
    results, engine = run_audit()
    if results is None:
        return 1
    summary = analyze(results)
    print(f"\nTotal wall time: {time.time() - t0:.1f}s")
    print(f"engine_version live: {engine!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
