"""
smoke_a14_cold503.py — Sprint 2.22.0a.5 post-deploy smoke (Bug A14).

Verifies the per-request GIS I/O budget killed the villa first-try 503 WITHOUT
moving valuations. Hits the live site; safe to run from Heroku one-off
(`heroku run python smoke_a14_cold503.py`) or any machine.

Protocol (brief §6):
  1. plain run            -> warm baseline + anchor outputs
  2. `heroku ps:restart`  -> then run again = the true COLD first-try villa hit
Repeat the cold step ~3× for SC1.

Asserts: engine == 2.22.0a.5; every villa/anchor request resolves < 30s wall with
margin and is NOT a 503; records asset_type + valuation so output can be compared
to the pre-sprint anchors (SC3). No production state is mutated.
"""
import json
import time
import urllib.request
import urllib.error

BASE = "https://thammen.qa"
WALL = 30.0
ANCHORS = [
    ("villa  56/565/21", {"zone": 56, "street": 565, "building": 21}),
    ("safe   52/903/90", {"zone": 52, "street": 903, "building": 90}),
    ("H11    69/329/20", {"zone": 69, "street": 329, "building": 20}),
]


def _post(path, payload, timeout=35):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "smoke-a14/1.0"},
        method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
        dt = time.perf_counter() - t0
        return r.status, dt, json.loads(body)
    except urllib.error.HTTPError as e:
        dt = time.perf_counter() - t0
        return e.code, dt, None
    except Exception as e:
        dt = time.perf_counter() - t0
        return f"ERR:{type(e).__name__}", dt, None


def _get(path, timeout=35):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "smoke-a14/1.0"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, time.perf_counter() - t0, json.loads(r.read())


def main():
    failures = []
    print("smoke_a14_cold503 — Sprint 2.22.0a.5 (Bug A14)")

    st, dt, health = _get("/api/health")
    eng = (health or {}).get("engine_version", "?")
    qep = (health or {}).get("qars_endpoint", {})
    print(f"\n/api/health: {st} in {dt:.2f}s  engine={eng}")
    print(f"  qars: primary_alive={qep.get('primary_alive')} status={qep.get('status')}")
    if "2p22p0a5" not in str(eng):
        failures.append(f"engine not a5: {eng}")

    print("\n--- anchor evaluations (first-try; expect <30s, not 503) ---")
    for label, payload in ANCHORS:
        status, dt, body = _post("/api/evaluate", payload)
        asset = val = None
        if isinstance(body, dict):
            asset = body.get("asset_type")
            val = body.get("valuation_amount")
        flag = ""
        if status == 503:
            failures.append(f"{label}: HTTP 503 ({dt:.1f}s)")
            flag = "  <== 503 (A14 NOT fixed)"
        elif status != 200:
            failures.append(f"{label}: status {status} ({dt:.1f}s)")
            flag = f"  <== {status}"
        elif dt >= WALL:
            failures.append(f"{label}: over wall {dt:.1f}s")
            flag = "  <== over 30s wall"
        print(f"  {label}: {status} in {dt:6.2f}s  asset={asset} val={val}{flag}")

    print()
    if failures:
        print("SMOKE FAIL:")
        for f in failures:
            print("  - " + f)
        raise SystemExit(1)
    print("SMOKE PASS — no 503, all under wall, engine a5 live.")


if __name__ == "__main__":
    main()
