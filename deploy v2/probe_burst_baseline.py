"""probe_burst_baseline.py — Sprint 2.16.17 Phase 0 baseline

Fires 20 concurrent POSTs at /api/evaluate using safe address 52/903/90
and records: HTTP status distribution, latency P50/P95/Max, 429s, 503s.

Why: establishes the BEFORE picture. After Sprint 2.16.17 lands the
burst caps (5/s + 30/m + 200/h), this same script becomes the negative
smoke and should show 5x200 then 1x429 on a 6-req burst.

Rule #36 — output MUST report:
    - actual sample size (n=20, not "approximately N")
    - actual time window (UTC start → UTC end)
    - actual failure modes (e.g. 18x200 + 2x503)

Rule #34 — file-based, not inline `heroku run python -c`.
Address 52/903/90: Sprint 2.16.15 anchor (Bug A6 SAFE, ~5s avg).
"""

import concurrent.futures
import json
import statistics
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone


URL = "https://thammen.qa/api/evaluate"
PAYLOAD = json.dumps({"zone": 52, "street": 903, "building": 90}).encode("utf-8")
HEADERS = {"Content-Type": "application/json"}
N_REQUESTS = 20
TIMEOUT = 40  # Heroku router caps at 30s; allow a small buffer


def one_request(req_id: int) -> dict:
    t0 = time.perf_counter()
    req = urllib.request.Request(URL, data=PAYLOAD, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
            return {
                "id": req_id,
                "status": resp.status,
                "latency_s": time.perf_counter() - t0,
                "body_len": len(body),
                "error": None,
            }
    except urllib.error.HTTPError as e:
        return {
            "id": req_id,
            "status": e.code,
            "latency_s": time.perf_counter() - t0,
            "body_len": 0,
            "error": f"HTTPError {e.code}",
        }
    except Exception as e:
        return {
            "id": req_id,
            "status": -1,
            "latency_s": time.perf_counter() - t0,
            "body_len": 0,
            "error": f"{type(e).__name__}: {e}",
        }


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    print(f"=== probe_burst_baseline.py ===")
    print(f"url:              {URL}")
    print(f"payload:          52/903/90 (Bug A6 safe anchor)")
    print(f"n_requests:       {N_REQUESTS}")
    print(f"timeout_per_req:  {TIMEOUT}s")
    print(f"started_utc:      {started}")
    print()

    t_wall_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=N_REQUESTS) as ex:
        results = list(ex.map(one_request, range(N_REQUESTS)))
    t_wall_end = time.perf_counter()
    ended = datetime.now(timezone.utc).isoformat()

    status_dist = {}
    for r in results:
        key = str(r["status"])
        status_dist[key] = status_dist.get(key, 0) + 1

    latencies = sorted([r["latency_s"] for r in results])
    n = len(latencies)
    p50 = statistics.median(latencies)
    p95 = latencies[max(0, int(n * 0.95) - 1)]
    mx = latencies[-1]
    mn = latencies[0]
    wall = t_wall_end - t_wall_start

    print(f"ended_utc:        {ended}")
    print(f"wall_seconds:     {wall:.3f}")
    print()
    print(f"--- status distribution (n={n}) ---")
    for status, count in sorted(status_dist.items()):
        print(f"  HTTP {status}: {count}")
    print()
    print(f"--- latency (seconds) ---")
    print(f"  min:  {mn:.3f}")
    print(f"  P50:  {p50:.3f}")
    print(f"  P95:  {p95:.3f}")
    print(f"  max:  {mx:.3f}")
    print()
    print(f"--- per-request detail ---")
    for r in results:
        err = f" err={r['error']}" if r["error"] else ""
        print(f"  #{r['id']:02d}  status={r['status']}  "
              f"latency={r['latency_s']:.3f}s  body={r['body_len']}B{err}")

    # Rule #36 summary line — easy to grep for in deploy notes
    print()
    print("--- summary (Rule #36 format) ---")
    parts = [f"{c}x{s}" for s, c in sorted(status_dist.items())]
    print(f"  result:  {' + '.join(parts)}")
    print(f"  window:  {started}  →  {ended}")
    print(f"  sample:  n={n} concurrent POST /api/evaluate (52/903/90)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
