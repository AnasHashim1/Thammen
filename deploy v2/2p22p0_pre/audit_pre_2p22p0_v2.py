"""
audit_pre_2p22p0_v2.py — Pre-Sprint 2.22.0 BRIEF v2 audit (5-stage architecture)

Read-only against public thammen.qa/api. Refreshes the v1 latency profile
(2026-05-24 / Heroku v106) against current production v127 (post-Sprint
2.21.4, T3 hybrid active) and broadens cohort toward the 7 asset_types
v2 BRIEF §4.1 specifies.

DEVIATIONS FROM v1 AUDIT (Rule #39):
  - v1 used 5 cases; v2 BRIEF §4.1 wants 7 asset_types × 3 PINs. Practical
    cohort: 9 cases covering 5 known asset_types fully + 2 candidate probes
    for missing types (compound_small / tower / Pearl). Gaps surfaced
    explicitly in AUDIT_FINDINGS, not silently filled.
  - 7s inter-request spacing (CLAUDE.md §14) interleaved across reps.
  - Capture full body_json per rep so §4.2 + §4.5 can reuse without re-call.

OUTPUT:
  latency_profile_2p22p0_v2.json  — full audit results (~200-500 KB)

Usage (Windows cmd):
    cd /d "C:\\Thammen\\deploy v2\\2p22p0_pre"
    python audit_pre_2p22p0_v2.py
"""
import json
import statistics
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

API_BASE = "https://thammen.qa/api"
REQUEST_TIMEOUT_S = 45
INTER_REQUEST_SLEEP_S = 7
REPS_PER_ADDRESS = 3
OUTPUT_JSON = "latency_profile_2p22p0_v2.json"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "thammen-pre-2p22p0-v2-audit/1.0",
}

# v2 BRIEF §4.1 wants: villa, compound_small, compound_large,
# apartment_building (Pearl), apartment_building (Lusail), tower, land.
# Practical cohort below — what the project has canonical PINs for, plus
# probes for the gaps. Gaps documented in AUDIT_FINDINGS §4.1 honestly.
CASES = [
    # === KNOWN: villa (multi-QARS + standalone) ===
    {"id": "villa_56_565_21_bouHamour",
     "body": {"zone": 56, "street": 565, "building": 21},
     "expected": "standalone_villa (multi-QARS shared polygon)",
     "asset_class": "villa"},
    {"id": "villa_53_240_12_dahil",
     "body": {"zone": 53, "street": 240, "building": 12},
     "expected": "standalone_villa (single QARS Dahil)",
     "asset_class": "villa"},
    {"id": "villa_31_918_99_ummLekhba",
     "body": {"zone": 31, "street": 918, "building": 99},
     "expected": "standalone_villa (Umm Lekhba — CHANGELOG_v37)",
     "asset_class": "villa"},

    # === KNOWN: apartment_building (52/903/90 misclassifies — preserved as fast-baseline) ===
    {"id": "fastbase_52_903_90",
     "body": {"zone": 52, "street": 903, "building": 90},
     "expected": "apartment_building (per 2026-05-23 audit) — BRIEF v2 §4.5 labels villa",
     "asset_class": "apt_legacy"},
    {"id": "a11_61_875_20_ashghal",
     "body": {"zone": 61, "street": 875, "building": 20},
     "expected": "apartment_building + subtype_zoning_mismatch (Bug A11)",
     "asset_class": "apt_legacy"},

    # === KNOWN: compound_large (post Patch-A) ===
    {"id": "compoundL_51_835_17_A6",
     "body": {"zone": 51, "street": 835, "building": 17},
     "expected": "compound_large (Patch-A promoted, val=None refusal)",
     "asset_class": "compound_large"},
    {"id": "compoundL_pin_66030258",
     "body": {"pin": "66030258"},
     "expected": "unknown (reality-check, PDAREA=59,501)",
     "asset_class": "compound_large"},

    # === KNOWN: apartment_building Lusail (hybrid path post-2.21.3/2.21.4) ===
    {"id": "lusail_apt_69_255_75_cityAvenues_H1",
     "body": {"zone": 69, "street": 255, "building": 75},
     "expected": "apartment_building (City Avenues — T1+T2+T3 hybrid)",
     "asset_class": "apt_lusail_t3"},
    {"id": "lusail_apt_69_329_20_foxHills_H11",
     "body": {"zone": 69, "street": 329, "building": 20},
     "expected": "apartment_building (Fox Hills — T2-only, T3 absent)",
     "asset_class": "apt_lusail_t2only"},
    {"id": "lusail_apt_69_112_36",
     "body": {"zone": 69, "street": 112, "building": 36},
     "expected": "apartment_building (Lusail — 2026-05-23 audit discovery)",
     "asset_class": "apt_lusail"},

    # === KNOWN: raw_land ===
    {"id": "rawland_pin_74328443_khor",
     "body": {"pin": "74328443"},
     "expected": "raw_land (الخور — CHANGELOG_v42 fixture)",
     "asset_class": "raw_land"},
]


# --- Field-speed heuristic (broadened for v127 keys observed in 2026-05-23 audit) ---
FAST_FIELD_PREFIXES = {
    "asset_type", "asset_type_ar", "asset_type_reality",
    "engine_version", "version",
    "address", "pin", "zone", "street", "building",
    "district", "district_ar", "district_en",
    "scope", "scope_id", "service_scope",
    "classification_confidence",
    "input_mode", "audience",
    "subtype_zoning_mismatch",
    "is_shared", "n_qars", "multi_qars",
    "gps", "valuation_date", "status",
}

SLOW_FIELD_PREFIXES = {
    "valuation", "valuation_amount", "valuation_method", "valuation_id",
    "material_uncertainty",
    "comparable_grid", "comparables",
    "cap_rate_provenance", "cap_rate",
    "decomposition", "land_value", "building_value",
    "negotiation_range", "negotiation",
    "brief", "reasoning_trace",
    "rics_compliant", "reconciliation",
    "stock_strata", "stratification",
    "outliers", "outliers_rejected",
    "moj_reference", "moj", "moj_sample_size",
    "income_approach", "cost_approach",
    "geometric_factors", "location_features",
    "trend", "active_listings", "rental_analysis",
    "tier_breakdown", "hybrid_valuation",
    "plot_area_m2", "user_inputs",
    "accuracy", "sanity_warnings", "disclaimer",
    "methodology_ar", "methodology_disclaimer_ar",
}


def classify_field_speed(key):
    kl = key.lower()
    for pref in FAST_FIELD_PREFIXES:
        if kl == pref or kl.startswith(pref + "_") or kl.startswith(pref + "."):
            return "fast"
    for pref in SLOW_FIELD_PREFIXES:
        if kl == pref or kl.startswith(pref + "_") or kl.startswith(pref + "."):
            return "slow"
    return "unknown"


def post_evaluate(body, timeout=REQUEST_TIMEOUT_S):
    data = json.dumps(body).encode("utf-8")
    url = f"{API_BASE}/evaluate"
    t0 = time.time()
    try:
        req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
        resp = urllib.request.urlopen(req, timeout=timeout)
        ttfb = time.time() - t0
        raw = resp.read().decode("utf-8", errors="replace")
        ttlb = time.time() - t0
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        return {"status": resp.status, "body_json": parsed, "body_text": raw,
                "ttfb_s": ttfb, "ttlb_s": ttlb, "error": None}
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
        return {"status": e.code, "body_json": parsed, "body_text": raw,
                "ttfb_s": ttlb, "ttlb_s": ttlb, "error": f"HTTPError {e.code}"}
    except urllib.error.URLError as e:
        return {"status": None, "body_json": None, "body_text": None,
                "ttfb_s": time.time() - t0, "ttlb_s": time.time() - t0,
                "error": f"URLError: {e.reason}"}
    except Exception as e:
        return {"status": None, "body_json": None, "body_text": None,
                "ttfb_s": time.time() - t0, "ttlb_s": time.time() - t0,
                "error": f"{type(e).__name__}: {e}"}


def health():
    try:
        req = urllib.request.Request(f"{API_BASE}/health", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            parsed = json.loads(resp.read().decode("utf-8", errors="replace"))
            return parsed.get("engine_version") or parsed.get("version"), parsed
    except Exception as e:
        return None, {"error": str(e)}


def run_audit():
    print("=" * 80)
    print("PRE-SPRINT 2.22.0 BRIEF v2 AUDIT — 5-stage architecture refresh")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"Target:  {API_BASE}")
    print(f"Cases:   {len(CASES)} · Reps: {REPS_PER_ADDRESS} · Total: {len(CASES) * REPS_PER_ADDRESS}")
    print(f"Sleep:   {INTER_REQUEST_SLEEP_S}s between any two requests")
    print("=" * 80)

    engine, hbody = health()
    print(f"\n  /api/health engine_version: {engine!r}")
    print(f"  freshness age_days: {(hbody or {}).get('data_freshness', {}).get('age_days')!r}")
    if not engine:
        print("  *** health unreachable — aborting ***")
        return None, engine, hbody
    print()

    results = []
    total_reqs = len(CASES) * REPS_PER_ADDRESS
    req_n = 0

    for rep in range(1, REPS_PER_ADDRESS + 1):
        print(f"\n----- REP {rep} of {REPS_PER_ADDRESS} -----")
        for case in CASES:
            req_n += 1
            print(f"  [{req_n}/{total_reqs}] {case['id']:<42}", end="  ", flush=True)
            res = post_evaluate(case["body"])
            status = res["status"]
            ttlb = res["ttlb_s"]
            body = res["body_json"] or {}
            asset = body.get("asset_type")
            val_block = body.get("valuation") or {}
            val_amt = val_block.get("amount") if isinstance(val_block, dict) else body.get("valuation_amount")
            err = res["error"]
            print(f"HTTP {status}  ttlb={ttlb:.2f}s  asset={asset!r:<22}  val={val_amt!r}"
                  f"{'  ERR:' + err if err else ''}")
            results.append({
                "case_id": case["id"],
                "asset_class_expected": case["asset_class"],
                "expected_note": case["expected"],
                "rep": rep,
                "result": res,
            })
            if req_n < total_reqs:
                time.sleep(INTER_REQUEST_SLEEP_S)

    print(f"\nTotal requests: {req_n}")
    return results, engine, hbody


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

    print("\n### 3.1 Per-address summary\n")
    by_case = defaultdict(list)
    for r in results:
        by_case[r["case_id"]].append(r)

    print(f"{'case_id':<42} {'asset_type':<22} {'reps':<4} {'min/med/max ttlb (s)':<26} {'val=None':<10}")
    print("-" * 110)
    rows = {}
    for cid, runs in by_case.items():
        latencies = [r["result"]["ttlb_s"] for r in runs if r["result"]["error"] is None]
        first_ok = next((r for r in runs if r["result"]["body_json"]), None)
        actual_asset = (first_ok["result"]["body_json"] or {}).get("asset_type") if first_ok else "<no-json>"
        val_none_count = 0
        for r in runs:
            body = r["result"]["body_json"] or {}
            val_block = body.get("valuation") or {}
            val_amt = val_block.get("amount") if isinstance(val_block, dict) else body.get("valuation_amount")
            if val_amt is None:
                val_none_count += 1
        if latencies:
            mn, md, mx = min(latencies), statistics.median(latencies), max(latencies)
            latency_str = f"{mn:.2f}/{md:.2f}/{mx:.2f}"
        else:
            latency_str = "ERR"
        print(f"{cid:<42} {str(actual_asset):<22} {len(runs):<4} {latency_str:<26} {val_none_count}/{len(runs):<10}")
        rows[cid] = {"latencies": latencies, "actual_asset": actual_asset,
                     "val_none_count": val_none_count, "n_reps": len(runs)}

    # Per-asset_type aggregation
    print("\n### 3.2 Per-asset_type latency (across cases)\n")
    by_asset = defaultdict(list)
    for cid, info in rows.items():
        if info["latencies"]:
            by_asset[info["actual_asset"]].extend(info["latencies"])
    print(f"{'asset_type':<24} {'n':<3} {'p50':<8} {'p95':<8} {'>5s?':<6} {'>25s?':<6}")
    print("-" * 60)
    h1_count = 0
    h3_under_5s = False
    for asset, lats in by_asset.items():
        p50 = percentile(lats, 50)
        p95 = percentile(lats, 95)
        over_5 = p95 > 5.0
        over_25 = p95 > 25.0
        if over_5:
            h1_count += 1
        if p50 <= 5.0:
            h3_under_5s = True
        print(f"{str(asset):<24} {len(lats):<3} {p50:<8.2f} {p95:<8.2f} {'YES' if over_5 else 'no':<6} {'YES' if over_25 else 'no':<6}")

    # Field-speed
    print("\n### 3.3 Field-speed classification per case\n")
    print(f"{'case_id':<42} {'fast':<6} {'slow':<6} {'unkn':<6} {'%fast':<8}")
    print("-" * 76)
    pct_fast = []
    for cid, runs in by_case.items():
        rep_with_body = next((r for r in runs if r["result"]["body_json"]), None)
        if not rep_with_body:
            print(f"{cid:<42} -      -      -      no JSON")
            continue
        body = rep_with_body["result"]["body_json"]
        keys = list(body.keys())
        fast = sum(1 for k in keys if classify_field_speed(k) == "fast")
        slow = sum(1 for k in keys if classify_field_speed(k) == "slow")
        unkn = sum(1 for k in keys if classify_field_speed(k) == "unknown")
        total = len(keys)
        pct = 100.0 * fast / total if total else 0.0
        pct_fast.append(pct)
        print(f"{cid:<42} {fast:<6} {slow:<6} {unkn:<6} {pct:<8.1f}")

    # Brief sections
    print("\n### 3.4 Brief sections per case (H4)\n")
    h4_seamed = 0
    for cid, runs in by_case.items():
        rep_with_body = next((r for r in runs if r["result"]["body_json"]), None)
        if not rep_with_body:
            print(f"{cid:<42} no JSON")
            continue
        body = rep_with_body["result"]["body_json"]
        brief = body.get("brief")
        if isinstance(brief, dict) and isinstance(brief.get("sections"), list):
            sec_ids = [s.get("id") if isinstance(s, dict) else "<non-dict>"
                       for s in brief["sections"]]
            print(f"{cid:<42} {len(sec_ids):>2} sec: {sec_ids[:8]}")
            if len(sec_ids) >= 3:
                h4_seamed += 1
        elif isinstance(brief, dict):
            print(f"{cid:<42} brief={list(brief.keys())[:8]}")
        else:
            print(f"{cid:<42} brief={type(brief).__name__}")

    # Predictions
    print("\n" + "=" * 80)
    print("PREDICTIONS H1–H8 (v2 BRIEF §6 — best-effort with measured data)")
    print("=" * 80)
    n_tested = len(by_asset)
    h1 = "TRUE" if h1_count >= 3 else "FALSE"
    print(f"H1 (p95>5s for >=3 of 7 asset_types): {h1} ({h1_count} of {n_tested} tested >5s)")

    avg_fast = sum(pct_fast) / len(pct_fast) if pct_fast else 0.0
    h2 = "TRUE" if avg_fast >= 30.0 else "FALSE"
    print(f"H2 (>=30% fast fields): {h2} (avg {avg_fast:.1f}% across {len(pct_fast)} cases)")

    h3 = "TRUE" if h3_under_5s else "FALSE"
    print(f"H3 (>=1 asset_type <=5s): {h3}")

    h4 = "TRUE" if h4_seamed >= 1 else "FALSE"
    print(f"H4 (brief has structural seams): {h4} ({h4_seamed} cases >=3 sections)")

    # H5 — refocused: post-hybrid Lusail apartment failure mode
    lusail_runs = [r for r in results
                   if r["case_id"].startswith("lusail_apt_")]
    lusail_fail_data = 0
    lusail_fail_timeout = 0
    lusail_ok = 0
    for r in lusail_runs:
        body = r["result"]["body_json"] or {}
        val_block = body.get("valuation") or {}
        val_amt = val_block.get("amount") if isinstance(val_block, dict) else body.get("valuation_amount")
        ttlb = r["result"]["ttlb_s"]
        if val_amt is not None:
            lusail_ok += 1
        elif ttlb > 25.0 or r["result"]["status"] == 503:
            lusail_fail_timeout += 1
        else:
            lusail_fail_data += 1
    print(f"H5 (post-hybrid apt failures latency-driven): "
          f"ok={lusail_ok}/timeout-fail={lusail_fail_timeout}/data-fail={lusail_fail_data} "
          f"across {len(lusail_runs)} Lusail apt reps")

    return {
        "h1": h1, "h2": h2, "h3": h3, "h4": h4,
        "h1_over_count": h1_count, "n_tested": n_tested,
        "h2_avg_fast_pct": avg_fast,
        "h4_seamed_count": h4_seamed,
        "lusail_ok": lusail_ok,
        "lusail_fail_timeout": lusail_fail_timeout,
        "lusail_fail_data": lusail_fail_data,
        "lusail_total": len(lusail_runs),
    }


def main():
    t0 = time.time()
    results, engine, hbody = run_audit()
    if results is None:
        return 1
    summary = analyze(results)
    wall_s = time.time() - t0
    print(f"\nTotal wall time: {wall_s:.1f}s ({wall_s/60:.1f} min)")
    print(f"engine_version live: {engine!r}")

    # Persist
    out = {
        "meta": {
            "audit_version": "2p22p0_v2",
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
            "ended_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "wall_s": wall_s,
            "engine_version": engine,
            "freshness": (hbody or {}).get("data_freshness"),
            "api_base": API_BASE,
            "cases": [{"id": c["id"], "body": c["body"], "expected": c["expected"],
                       "asset_class": c["asset_class"]} for c in CASES],
            "reps_per_address": REPS_PER_ADDRESS,
            "inter_request_sleep_s": INTER_REQUEST_SLEEP_S,
        },
        "summary": summary,
        "runs": [
            {
                "case_id": r["case_id"],
                "asset_class_expected": r["asset_class_expected"],
                "rep": r["rep"],
                "status": r["result"]["status"],
                "ttlb_s": r["result"]["ttlb_s"],
                "error": r["result"]["error"],
                "body_json": r["result"]["body_json"],
            } for r in results
        ],
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nWrote: {OUTPUT_JSON} ({sum(1 for _ in results)} runs, ~{int(sum(len(json.dumps(r['result']['body_json'] or {})) for r in results)/1024)} KB body data)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
