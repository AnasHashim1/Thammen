"""probe_docs_exposure.py — Sprint 2.16.17 Phase 0 baseline

Confirms current exposure of FastAPI's auto-generated docs from the
dyno's own egress perspective. After Sprint 2.16.17 lands, the three
endpoints must return HTTP 404 when THAMMEN_DEV_MODE is unset and 200
when it is set to "1".

Why: the kickoff §1 lists /docs, /openapi.json, /redoc as production
information leaks (full FastAPI schema, all routes, all Pydantic models,
example payloads). We want before-after evidence both endpoints respond
as expected.

Rule #34 — file-based, not inline.
"""

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


PATHS = ["/docs", "/openapi.json", "/redoc"]
BASE = "https://thammen.qa"


def probe(path: str) -> dict:
    url = BASE + path
    t0 = time.perf_counter()
    try:
        # HEAD is cleaner than GET; FastAPI/uvicorn answers HEAD on these.
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {
                "path": path,
                "status": resp.status,
                "latency_s": time.perf_counter() - t0,
                "content_type": resp.headers.get("Content-Type", ""),
                "error": None,
            }
    except urllib.error.HTTPError as e:
        return {
            "path": path,
            "status": e.code,
            "latency_s": time.perf_counter() - t0,
            "content_type": e.headers.get("Content-Type", "") if e.headers else "",
            "error": f"HTTPError {e.code}",
        }
    except Exception as e:
        return {
            "path": path,
            "status": -1,
            "latency_s": time.perf_counter() - t0,
            "content_type": "",
            "error": f"{type(e).__name__}: {e}",
        }


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    print(f"=== probe_docs_exposure.py ===")
    print(f"base:        {BASE}")
    print(f"paths:       {PATHS}")
    print(f"started_utc: {started}")
    print()

    results = [probe(p) for p in PATHS]

    print(f"--- per-path result ---")
    for r in results:
        err = f" err={r['error']}" if r["error"] else ""
        print(f"  {r['path']:<18s}  status={r['status']}  "
              f"latency={r['latency_s']:.3f}s  ct={r['content_type']!r}{err}")

    ended = datetime.now(timezone.utc).isoformat()
    print()
    print("--- summary (Rule #36 format) ---")
    for r in results:
        verdict = (
            "EXPOSED" if r["status"] == 200
            else f"BLOCKED ({r['status']})" if r["status"] in (401, 403, 404)
            else f"UNKNOWN ({r['status']})"
        )
        print(f"  {r['path']:<18s}  {verdict}")
    print(f"  window:     {started}  →  {ended}")
    print(f"  sample:     n={len(PATHS)} HEAD requests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
