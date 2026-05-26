"""A3 retry — confirm cold-dyno hypothesis vs Phase 1 villa baseline."""
import json, sys, time, urllib.request, urllib.error

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

UA = "thammen-pre-2p22p0a-step4-a3-retry/1.0"

def post():
    body = {"zone": 31, "street": 918, "building": 99}
    data = json.dumps(body).encode("utf-8")
    t0 = time.time()
    try:
        req = urllib.request.Request(
            "https://thammen.qa/api/evaluate",
            data=data,
            headers={"Content-Type": "application/json",
                     "Accept": "application/json", "User-Agent": UA},
            method="POST")
        resp = urllib.request.urlopen(req, timeout=45)
        raw = resp.read().decode("utf-8", errors="replace")
        ttlb = time.time() - t0
        return resp.status, json.loads(raw), ttlb, None
    except urllib.error.HTTPError as e:
        return e.code, None, time.time() - t0, f"HTTPError {e.code}"
    except Exception as e:
        return None, None, time.time() - t0, f"{type(e).__name__}: {e}"

print(f"A3 retry — Umm Lekhba villa 31/918/99")
print(f"  started: {time.strftime('%H:%M:%S UTC', time.gmtime())}")
status, body, ttlb, err = post()
print(f"  HTTP {status}  ttlb={ttlb:.2f}s  err={err!r}")
if body:
    val = body.get("valuation") or {}
    print(f"  asset_type={body.get('asset_type')!r}  district={body.get('district')!r}")
    print(f"  val.amount={val.get('amount')!r}  val.method={val.get('method')!r}")
    print(f"  brief.sections={[s.get('id') for s in (body.get('brief') or {}).get('sections') or []]}")
    expected = 3200000
    actual = val.get("amount")
    if actual:
        drift_pct = abs(actual - expected) / expected * 100
        print(f"  drift vs Phase 1 (val.amount=3,200,000): {drift_pct:.3f}%")
        verdict = "OK" if drift_pct < 0.1 else f"DRIFT {drift_pct:.2f}%"
        print(f"  VERDICT: {verdict}")
    else:
        print(f"  VERDICT: still no val.amount (cold dyno persists OR true drift)")
with open("step4_a3_retry.json", "w", encoding="utf-8") as f:
    json.dump({"status": status, "body_json": body, "ttlb_s": ttlb, "error": err},
              f, ensure_ascii=False, indent=2, default=str)
print(f"  wrote: step4_a3_retry.json")
