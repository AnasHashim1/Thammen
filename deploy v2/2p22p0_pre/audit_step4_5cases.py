"""
audit_step4_5cases.py — Step 4 of Phase 3 (Sprint 2.22.0a §5 audit)

5-case confirmatory audit against v128 baseline. Verifies that the engine
behavior hasn't drifted since Phase 1 audit (commit a903350, 2026-05-25) +
adds A5 Pearl as ship-gate (BRIEF v3.1 sec 1.7).

Cases (per Anas approved cohort + Delta Step 4):
  A1: 69/255/75 — City Avenues Lusail (H1 anchor — hybrid_t2, T2+T3)
  A2: 51/835/17 — Gharaffa compound_large (Patch-A refusal)
  A3: 31/918/99 — Umm Lekhba villa (standalone_villa with valuation)
  A4: PIN 66030258 — reality-check unknown (asset_type_reality_stop)
  A5: 66/140/6  — Pearl tower (NEW from pearl_pin_discovery, ship-gate)

Capture per case: HTTP status, TTLB, asset_type, asset_type_ar, district,
val.amount, val.value_per_m2, val.method, brief.sections IDs, hybrid block,
sources block, accuracy block, subtype_zoning_mismatch presence,
asset_type_reality presence.

Cross-reference with Phase 1 latency_profile_2p22p0_v2.json (~14 hours
earlier) for drift detection.

Read-only against https://thammen.qa/api/evaluate. 7s spacing.
"""

import json
import sys
import time
import urllib.request
import urllib.error

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

API_BASE = "https://thammen.qa/api"
TIMEOUT = 45
SLEEP_S = 7
UA = "thammen-pre-2p22p0a-step4-audit/1.0"

CASES = [
    {
        "id": "A1_lusail_apt_69_255_75_cityAvenues_H1",
        "body": {"zone": 69, "street": 255, "building": 75},
        "expected_asset_type": "apartment_building",
        "expected_method": "hybrid_t2",
        "phase1_value_per_m2": 11415.02,
        "label": "Lusail City Avenues H1 anchor",
    },
    {
        "id": "A2_compoundL_51_835_17_A6",
        "body": {"zone": 51, "street": 835, "building": 17},
        "expected_asset_type": "compound_large",
        "expected_method": "insufficient_data",
        "phase1_value_per_m2": None,
        "label": "Gharaffa compound_large Patch-A",
    },
    {
        "id": "A3_villa_31_918_99_ummLekhba",
        "body": {"zone": 31, "street": 918, "building": 99},
        "expected_asset_type": "standalone_villa",
        "expected_method": "comparison_thin",
        "phase1_val_amount": 3200000,
        "label": "Umm Lekhba villa",
    },
    {
        "id": "A4_compoundL_pin_66030258",
        "body": {"pin": "66030258"},
        "expected_asset_type": "unknown",
        "expected_method": "asset_type_reality_stop",
        "phase1_value_per_m2": None,
        "label": "Reality-check unknown PIN 66030258",
    },
    {
        "id": "A5_pearl_66_140_6_NEW",
        "body": {"zone": 66, "street": 140, "building": 6},
        "expected_asset_type": None,   # unknown — first probe
        "expected_method": None,
        "phase1_value_per_m2": None,
        "label": "Pearl tower 66/140/6 (NEW from pearl_pin_discovery, ship-gate)",
    },
]


def post_evaluate(body):
    data = json.dumps(body).encode("utf-8")
    url = f"{API_BASE}/evaluate"
    t0 = time.time()
    try:
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json",
                     "User-Agent": UA},
            method="POST")
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        raw = resp.read().decode("utf-8", errors="replace")
        ttlb = time.time() - t0
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        return {"status": resp.status, "body_json": parsed, "ttlb_s": ttlb, "error": None}
    except urllib.error.HTTPError as e:
        ttlb = time.time() - t0
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = None
        return {"status": e.code, "body_json": parsed, "ttlb_s": ttlb,
                "error": f"HTTPError {e.code}"}
    except Exception as e:
        return {"status": None, "body_json": None, "ttlb_s": time.time() - t0,
                "error": f"{type(e).__name__}: {e}"}


def health():
    try:
        req = urllib.request.Request(f"{API_BASE}/health",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode("utf-8", errors="replace"))
            return d.get("engine_version") or d.get("version"), d
    except Exception as e:
        return None, {"error": str(e)}


def extract(body_json):
    """Pull the audit fields we care about from a response body."""
    if not body_json:
        return {}
    val = body_json.get("valuation") or {}
    hybrid = body_json.get("hybrid")
    brief = body_json.get("brief") or {}
    sections = brief.get("sections") or []
    return {
        "asset_type": body_json.get("asset_type"),
        "asset_type_ar": body_json.get("asset_type_ar"),
        "district": body_json.get("district"),
        "val.amount": val.get("amount") if isinstance(val, dict) else None,
        "val.value_per_m2": val.get("value_per_m2") if isinstance(val, dict) else None,
        "val.value_per_m2_low": val.get("value_per_m2_low") if isinstance(val, dict) else None,
        "val.value_per_m2_high": val.get("value_per_m2_high") if isinstance(val, dict) else None,
        "val.method": val.get("method") if isinstance(val, dict) else None,
        "val.low": val.get("low") if isinstance(val, dict) else None,
        "val.high": val.get("high") if isinstance(val, dict) else None,
        "brief.sections": [s.get("id") for s in sections if isinstance(s, dict)],
        "hybrid.case": (hybrid or {}).get("case") if hybrid else None,
        "hybrid.confidence": (hybrid or {}).get("confidence") if hybrid else None,
        "hybrid.n_used": (hybrid or {}).get("n_used") if hybrid else None,
        "hybrid.muc_range_pct": (hybrid or {}).get("muc_range_pct") if hybrid else None,
        "hybrid.tier_breakdown": (hybrid or {}).get("tier_breakdown") if hybrid else None,
        "sources_tiers": [s.get("tier") for s in (body_json.get("sources") or [])],
        "accuracy.score": (body_json.get("accuracy") or {}).get("score"),
        "accuracy.label": (body_json.get("accuracy") or {}).get("label"),
        "has_subtype_zoning_mismatch": "subtype_zoning_mismatch" in body_json,
        "has_asset_type_reality": "asset_type_reality" in body_json,
        "has_multi_qars": "multi_qars" in body_json,
        "engine_version": body_json.get("engine_version"),
    }


def drift_check(case, extracted):
    """Compare extracted fields against Phase 1 expectations."""
    issues = []
    exp_at = case.get("expected_asset_type")
    act_at = extracted.get("asset_type")
    if exp_at is not None and act_at != exp_at:
        issues.append(f"asset_type drift: expected={exp_at!r} actual={act_at!r}")
    exp_m = case.get("expected_method")
    act_m = extracted.get("val.method")
    if exp_m is not None and act_m != exp_m:
        issues.append(f"val.method drift: expected={exp_m!r} actual={act_m!r}")
    exp_vpm = case.get("phase1_value_per_m2")
    act_vpm = extracted.get("val.value_per_m2")
    if exp_vpm is not None and act_vpm is not None:
        # Within 0.1% drift acceptable (no change expected since docs-only deploy)
        if abs(act_vpm - exp_vpm) / max(1e-6, abs(exp_vpm)) > 0.001:
            issues.append(f"val.value_per_m2 drift: phase1={exp_vpm} actual={act_vpm}")
    exp_amt = case.get("phase1_val_amount")
    act_amt = extracted.get("val.amount")
    if exp_amt is not None and act_amt is not None:
        if abs(act_amt - exp_amt) / max(1e-6, abs(exp_amt)) > 0.001:
            issues.append(f"val.amount drift: phase1={exp_amt} actual={act_amt}")
    return issues


def main():
    print("#" * 80)
    print(f"STEP 4 §5 AUDIT — 5 cases against v128 baseline")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("#" * 80)

    engine, hbody = health()
    print(f"  /api/health engine_version: {engine!r}")
    if not engine:
        print(f"  *** health unreachable — abort ***")
        return 1
    print()

    runs = []
    for i, case in enumerate(CASES, 1):
        print(f"--- [{i}/{len(CASES)}] {case['id']} ({case['label']})")
        print(f"    body: {case['body']}")
        res = post_evaluate(case["body"])
        ex = extract(res["body_json"])
        issues = drift_check(case, ex)
        runs.append({
            "case_id": case["id"],
            "label": case["label"],
            "body": case["body"],
            "expected": {
                "asset_type": case.get("expected_asset_type"),
                "method": case.get("expected_method"),
                "value_per_m2": case.get("phase1_value_per_m2"),
                "val_amount": case.get("phase1_val_amount"),
            },
            "http_status": res["status"],
            "ttlb_s": res["ttlb_s"],
            "error": res["error"],
            "extracted": ex,
            "drift_issues": issues,
            "body_json": res["body_json"],
        })
        print(f"    HTTP {res['status']} ttlb={res['ttlb_s']:.2f}s")
        print(f"    asset_type={ex.get('asset_type')!r} district={ex.get('district')!r}")
        print(f"    val.amount={ex.get('val.amount')!r} "
              f"val.value_per_m2={ex.get('val.value_per_m2')!r} "
              f"method={ex.get('val.method')!r}")
        print(f"    brief.sections={ex.get('brief.sections')}")
        if ex.get("hybrid.case"):
            print(f"    hybrid: case={ex['hybrid.case']} n_used={ex['hybrid.n_used']} "
                  f"confidence={ex['hybrid.confidence']} muc={ex['hybrid.muc_range_pct']}")
        if issues:
            print(f"    !!! DRIFT: {issues}")
        else:
            print(f"    OK — no drift vs Phase 1")
        if i < len(CASES):
            time.sleep(SLEEP_S)

    print()
    print("=" * 80)
    print("STEP 4 §5 AUDIT SUMMARY")
    print("=" * 80)
    print(f"engine_version live: {engine!r}")
    total_drift = sum(1 for r in runs if r["drift_issues"])
    print(f"Cases run: {len(runs)} · cases with drift: {total_drift}")
    for r in runs:
        verdict = "DRIFT" if r["drift_issues"] else "OK"
        print(f"  {r['case_id']}: HTTP {r['http_status']} {r['ttlb_s']:.2f}s "
              f"asset={r['extracted'].get('asset_type')!r} [{verdict}]")
        if r["drift_issues"]:
            for d in r["drift_issues"]:
                print(f"    - {d}")

    out = {
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine_version": engine,
        "freshness": (hbody or {}).get("data_freshness"),
        "cases_total": len(runs),
        "cases_with_drift": total_drift,
        "runs": runs,
    }
    with open("step4_5cases_audit.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print()
    print(f"Wrote: step4_5cases_audit.json")
    return 0 if total_drift == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
