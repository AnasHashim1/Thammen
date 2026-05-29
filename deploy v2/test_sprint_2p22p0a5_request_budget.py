"""
test_sprint_2p22p0a5_request_budget.py — Bug A14 (villa cold-dyno first-try 503).

Verifies the request-level I/O budget that bounds GIS calls under the Heroku 30s
wall WITHOUT changing success-path output. Exercises the REAL production functions
(Rule #40): qatar_gis._http_get_json / _remaining_budget / set_request_deadline,
and property_factors.analyze_property (contextvar propagation into worker threads).

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a5_request_budget.py
"""
import json
import time
import contextvars
import urllib.request

import qatar_gis
import property_factors

_passed = 0
_failed = 0


def check(label, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  PASS  {label}")
    else:
        _failed += 1
        print(f"  FAIL  {label}")


# ── fake urlopen plumbing ─────────────────────────────────────────────────
class _FakeResp:
    def __init__(self, payload):
        self._p = payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._p


_REAL_URLOPEN = urllib.request.urlopen


def install_fake(behaviour):
    """behaviour(timeout) -> bytes, or raises. Records timeouts in .timeouts."""
    rec = {'timeouts': [], 'calls': 0}

    def fake(req, timeout=None, context=None):
        rec['calls'] += 1
        rec['timeouts'].append(timeout)
        return _FakeResp(behaviour(timeout))

    urllib.request.urlopen = fake
    return rec


def restore():
    urllib.request.urlopen = _REAL_URLOPEN


def ok_features(timeout):
    return json.dumps({"features": [{"attributes": {"PIN": 1}, "geometry": {"x": 51.0, "y": 25.0}}]}).encode()


def always_urlerror(timeout):
    raise urllib.error.URLError("boom")


def run():
    URL = qatar_gis.ENDPOINTS['cadastre']
    PARAMS = {'where': 'PIN=1', 'outFields': '*', 'f': 'json'}

    # 1) helpers: unarmed → None; armed → ~budget; cleared → None
    check("unarmed _remaining_budget() is None", qatar_gis._remaining_budget() is None)
    tok = qatar_gis.set_request_deadline(10.0)
    rem = qatar_gis._remaining_budget()
    check("armed budget ~10s", rem is not None and 9.0 < rem <= 10.0)
    qatar_gis.clear_request_deadline(tok)
    check("cleared → None again", qatar_gis._remaining_budget() is None)

    # 2) no deadline → full timeout passed to urlopen (zero behaviour change)
    def no_deadline_case():
        rec = install_fake(ok_features)
        try:
            qatar_gis._http_get_json(URL, PARAMS, timeout=30)
        finally:
            restore()
        return rec
    rec = contextvars.copy_context().run(no_deadline_case)
    check("no-deadline uses full timeout=30", rec['timeouts'] == [30])

    # 3) armed → effective timeout = min(call_ceiling, remaining)
    def armed_case():
        t = qatar_gis.set_request_deadline(5.0)
        rec = install_fake(ok_features)
        try:
            qatar_gis._http_get_json(URL, PARAMS, timeout=30)
        finally:
            restore()
            qatar_gis.clear_request_deadline(t)
        return rec
    rec = contextvars.copy_context().run(armed_case)
    check("armed caps timeout to remaining (<=5, >3)",
          len(rec['timeouts']) == 1 and 3.0 < rec['timeouts'][0] <= 5.0)

    # 4) budget exhausted → fail fast, urlopen NEVER called
    def exhausted_case():
        t = qatar_gis.set_request_deadline(0.0)  # already at deadline
        time.sleep(0.01)
        rec = install_fake(ok_features)
        raised = False
        try:
            qatar_gis._http_get_json(URL, PARAMS, timeout=30)
        except Exception:
            raised = True
        finally:
            restore()
            qatar_gis.clear_request_deadline(t)
        return rec, raised
    rec, raised = contextvars.copy_context().run(exhausted_case)
    check("exhausted budget raises", raised)
    check("exhausted budget skips urlopen entirely", rec['calls'] == 0)

    # 5) retries respect budget: URLError storm under a 4s budget must finish
    #    well under the legacy ~3x30s+7s; proves the amplifier is bounded.
    def retry_storm_case():
        t = qatar_gis.set_request_deadline(4.0)
        rec = install_fake(always_urlerror)
        t0 = time.monotonic()
        raised = False
        try:
            qatar_gis._http_get_json(URL, PARAMS, timeout=30)
        except Exception:
            raised = True
        finally:
            restore()
            qatar_gis.clear_request_deadline(t)
        return time.monotonic() - t0, raised
    elapsed, raised = contextvars.copy_context().run(retry_storm_case)
    check("retry storm raises", raised)
    check(f"retry storm bounded by budget (elapsed={elapsed:.2f}s < 6s)", elapsed < 6.0)

    # 6) property_factors._query_gis: exhausted budget → [] (fail-soft), no urlopen
    def pf_query_exhausted():
        t = qatar_gis.set_request_deadline(0.0)
        time.sleep(0.01)
        rec = install_fake(ok_features)
        try:
            out = property_factors._query_gis(URL, dict(PARAMS), timeout=12)
        finally:
            restore()
            qatar_gis.clear_request_deadline(t)
        return out, rec
    out, rec = contextvars.copy_context().run(pf_query_exhausted)
    check("_query_gis exhausted → [] fail-soft", out == [])
    check("_query_gis exhausted → no urlopen", rec['calls'] == 0)

    # 7) copy_context propagation: analyze_property under expired budget → the
    #    worker threads see the budget (==0) and short-circuit (0 urlopen calls).
    #    Proves the deadline crosses the ThreadPoolExecutor boundary.
    def analyze_under_expired():
        t = qatar_gis.set_request_deadline(0.0)
        time.sleep(0.01)
        rec = install_fake(ok_features)
        err = None
        result = None
        try:
            result = property_factors.analyze_property(lat=25.0, lon=51.5, purpose='residential')
        except Exception as e:
            err = e
        finally:
            restore()
            qatar_gis.clear_request_deadline(t)
        return result, rec, err
    result, rec, err = contextvars.copy_context().run(analyze_under_expired)
    check("analyze_property under expired budget returns (no crash)", err is None and result is not None)
    check("analyze_property workers honoured budget (0 urlopen across 5 threads)", rec['calls'] == 0)

    # 8) sanity: analyze_property with NO budget still runs all 5 layers (uses fake)
    def analyze_unarmed():
        rec = install_fake(lambda to: json.dumps({"features": []}).encode())
        err = None
        try:
            property_factors.analyze_property(lat=25.0, lon=51.5, purpose='residential')
        except Exception as e:
            err = e
        finally:
            restore()
        return rec, err
    rec, err = contextvars.copy_context().run(analyze_unarmed)
    # No budget armed → workers must NOT short-circuit; they actually query GIS.
    # (Exact call count varies by factor; the regression guard is "> 0".)
    check(f"unarmed analyze_property still queries GIS (calls={rec['calls']}>0)",
          err is None and rec['calls'] > 0)

    # 9) version bump landed
    import evaluate_unified as eu
    check("ENGINE_VERSION bumped to 2p22p0a5",
          eu.ENGINE_VERSION == 'thammen-sprint2p22p0a5-villa-cold503-budget')
    check("SPRINT_TAG bumped to 2.22.0a.5", eu.SPRINT_TAG == '2.22.0a.5')

    # 10) no contextvar leak after all tests
    check("no deadline leaked into test thread", qatar_gis._remaining_budget() is None)


if __name__ == "__main__":
    print("Sprint 2.22.0a.5 — request I/O budget (Bug A14)")
    try:
        run()
    finally:
        restore()
    print(f"\n{_passed} passed, {_failed} failed")
    raise SystemExit(1 if _failed else 0)
