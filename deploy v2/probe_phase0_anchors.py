"""
Sprint 2.22.0a.2 — Phase 0.1 anchor probe (throwaway, Rule #34).

Pulls 4 anchor briefs from production for Arabic surface audit.
NOT a regression test — purpose is to capture the *rendered* user-visible
strings so Phase 0.2 grep can confirm which ChatGPT-flagged phrases
actually appear in production output (vs. only in code/dead paths).

Anchors:
  villa:              56/565/21  (Bou Hamour, multi-QARS reference)
  apartment_building: 52/903/90  (Sprint 2.16.15 baseline timing anchor)
  tower (T2/T3):      69/255/75  (Sprint 2.21.4 H1 anchor, Lusail City Avenues)
  refusal case:       70/300/25  (Sprint 2.22.0a.1 smoke: legacy 0 features,
                                  asset_type=unknown — clean refusal path)

Output: docs/phase0/brief_<slug>.json for each, capturing:
  - response time
  - engine_version
  - asset_type / asset_type_ar
  - full JSON body (so we can later grep rendered Arabic strings)
"""

import json
import os
import time
import urllib.request

BASE = "https://thammen.qa/api/evaluate"
ANCHORS = [
    ("villa", "56_565_21",                  {"zone": 56, "street": 565, "building": 21}),
    ("apartment_building", "52_903_90",     {"zone": 52, "street": 903, "building": 90}),
    ("tower_t2_t3", "69_255_75",            {"zone": 69, "street": 255, "building": 75}),
    ("refusal_unknown", "70_300_25",        {"zone": 70, "street": 300, "building": 25}),
]

OUT_DIR = os.path.join("docs", "phase0")
os.makedirs(OUT_DIR, exist_ok=True)


def call(payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "thammen-phase0-probe/2.22.0a.2",
            "Accept": "application/json",
        },
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            elapsed = time.time() - t0
            body_bytes = resp.read()
            return {
                "ok": True,
                "status": resp.status,
                "elapsed_s": round(elapsed, 2),
                "body": body_bytes.decode("utf-8", errors="replace"),
            }
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        return {
            "ok": False,
            "status": e.code,
            "elapsed_s": round(elapsed, 2),
            "body": (e.read() or b"").decode("utf-8", errors="replace"),
        }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "ok": False,
            "status": None,
            "elapsed_s": round(elapsed, 2),
            "error": type(e).__name__ + ": " + str(e),
        }


def main():
    summary = []
    for label, slug, payload in ANCHORS:
        print("=" * 60)
        print(f"[{label}] POST {BASE} body={payload}")
        result = call(payload)
        print(f"  status={result.get('status')}  elapsed={result.get('elapsed_s')}s")

        record = {
            "anchor_label": label,
            "anchor_slug": slug,
            "payload": payload,
            "status": result.get("status"),
            "elapsed_s": result.get("elapsed_s"),
            "ok": result.get("ok"),
        }
        body = result.get("body", "") or ""
        try:
            parsed = json.loads(body)
            record["body_parsed"] = parsed
            record["engine_version"] = parsed.get("engine_version")
            record["asset_type"] = parsed.get("asset_type")
            record["asset_type_ar"] = parsed.get("asset_type_ar")
            record["valuation_amount"] = parsed.get("valuation_amount")
            record["decomp_status"] = (parsed.get("decomposition") or {}).get("status")
            print(f"  engine_version = {record['engine_version']}")
            print(f"  asset_type = {record['asset_type']}  asset_type_ar = {record['asset_type_ar']}")
            print(f"  valuation_amount = {record['valuation_amount']}")
        except Exception as e:
            record["body_parsed_error"] = str(e)
            record["body_raw"] = body[:4000]
            print(f"  parse_error = {e}")

        if "error" in result:
            record["error"] = result["error"]

        out_path = os.path.join(OUT_DIR, f"brief_{slug}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        print(f"  -> wrote {out_path}")

        summary.append({
            "label": label,
            "slug": slug,
            "status": result.get("status"),
            "elapsed_s": result.get("elapsed_s"),
            "engine_version": record.get("engine_version"),
            "asset_type": record.get("asset_type"),
            "asset_type_ar": record.get("asset_type_ar"),
        })
        time.sleep(2)  # polite

    summary_path = os.path.join(OUT_DIR, "anchor_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("=" * 60)
    print(f"summary -> {summary_path}")
    for row in summary:
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
