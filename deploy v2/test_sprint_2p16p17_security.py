"""test_sprint_2p16p17_security.py

Isolated tests for Sprint 2.16.17 Security Hardening:
    1. cf_remote_address key function — 4 cases (CF / XFF chain / XFF
       single / fallback).
    2. slowapi list-form decorator parse — 1 case.
    3. THAMMEN_DEV_MODE docs lockdown — 4 cases (3 paths × 2 modes,
       plus production-app attribute verification, via subprocess so
       each instantiation gets a fresh env read).
    4. RATE_LIMIT env-var parsing — 2 cases (default / custom list).
    5. Production verification (Rule #40) — at least one assertion
       against the live api.app object, not just a replica.

Run with: PYTHONIOENCODING=utf-8 python test_sprint_2p16p17_security.py
Expected exit code 0; non-zero on any failure (so this counts cleanly
in the regression sweep).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from types import SimpleNamespace


# ════════════════════════════════════════════════════════════════════
# Section 1 — cf_remote_address (replica + production)
# ════════════════════════════════════════════════════════════════════


def _fake_request(headers: dict, client_host: str = "10.0.0.99"):
    """Build a minimal Request-shaped object slowapi's key func sees."""
    # Header dict lookup mimics starlette.datastructures.Headers
    # (case-insensitive). Both .get('cf-connecting-ip') and .get('CF-Connecting-IP')
    # must resolve the same value.
    class _CIHeaders:
        def __init__(self, d):
            self._d = {k.lower(): v for k, v in d.items()}

        def get(self, k, default=None):
            return self._d.get(k.lower(), default)

    return SimpleNamespace(
        headers=_CIHeaders(headers),
        client=SimpleNamespace(host=client_host),
    )


def test_cf_remote_address_cf_header_present():
    from api import cf_remote_address
    req = _fake_request({"CF-Connecting-IP": "203.0.113.5"}, client_host="10.0.0.99")
    assert cf_remote_address(req) == "203.0.113.5", \
        "CF-Connecting-IP must win over fallbacks"


def test_cf_remote_address_xff_chain():
    from api import cf_remote_address
    req = _fake_request(
        {"X-Forwarded-For": "198.51.100.7, 172.16.0.1, 10.0.0.1"},
        client_host="10.0.0.99",
    )
    assert cf_remote_address(req) == "198.51.100.7", \
        "X-Forwarded-For must use first hop, not last"


def test_cf_remote_address_xff_single():
    from api import cf_remote_address
    req = _fake_request({"X-Forwarded-For": "192.0.2.42"}, client_host="10.0.0.99")
    assert cf_remote_address(req) == "192.0.2.42"


def test_cf_remote_address_fallback():
    from api import cf_remote_address
    req = _fake_request({}, client_host="10.0.0.99")
    # No CF, no XFF -> falls back to slowapi.util.get_remote_address(request),
    # which returns request.client.host.
    assert cf_remote_address(req) == "10.0.0.99"


def test_cf_remote_address_cf_wins_over_xff():
    """Belt-and-braces: when BOTH headers are set, CF-Connecting-IP wins."""
    from api import cf_remote_address
    req = _fake_request(
        {
            "CF-Connecting-IP": "203.0.113.5",
            "X-Forwarded-For": "198.51.100.7, 10.0.0.1",
        },
        client_host="10.0.0.99",
    )
    assert cf_remote_address(req) == "203.0.113.5", \
        "CF-Connecting-IP must override X-Forwarded-For"


# ════════════════════════════════════════════════════════════════════
# Section 2 — slowapi list-form decorator parse
# ════════════════════════════════════════════════════════════════════


def test_slowapi_semicolon_form_parses():
    """slowapi 0.1.9 expects a STRING (single or ';'-separated), not a
    Python list. Phase 0 verified list-form silently ERRORs and leaves
    the route un-rate-limited. This test enforces the correct syntax
    by capturing the slowapi logger during decorator binding: if
    'Failed to configure throttling' shows up, the test fails."""
    import io
    import logging

    from fastapi import Request
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    slowapi_log = logging.getLogger("slowapi")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.ERROR)
    slowapi_log.addHandler(handler)
    try:
        limiter = Limiter(key_func=get_remote_address, default_limits=[])

        @limiter.limit("5/second;30/minute;200/hour")
        def _probe(request: Request):
            pass

        @limiter.limit("3/second")
        def _probe2(request: Request):
            pass
    finally:
        slowapi_log.removeHandler(handler)

    captured = stream.getvalue()
    assert "Failed to configure throttling" not in captured, \
        f"slowapi rejected the rate-limit syntax (silent failure): {captured!r}"


def test_slowapi_list_form_is_rejected():
    """Belt-and-braces: confirm the kickoff's original list-form would
    silently break. If a future slowapi version starts supporting lists,
    delete this test and switch the decorator back."""
    import io
    import logging

    from fastapi import Request
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    slowapi_log = logging.getLogger("slowapi")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.ERROR)
    slowapi_log.addHandler(handler)
    try:
        limiter = Limiter(key_func=get_remote_address, default_limits=[])

        @limiter.limit(["5/second", "30/minute", "200/hour"])
        def _probe(request: Request):
            pass
    finally:
        slowapi_log.removeHandler(handler)

    captured = stream.getvalue()
    assert "Failed to configure throttling" in captured, \
        ("slowapi accepted list-form unexpectedly; delete this test and "
         "switch api.py back to RATE_LIMIT_LIST. Captured: %r" % captured)


# ════════════════════════════════════════════════════════════════════
# Section 3 — RATE_LIMIT env-var parsing
# ════════════════════════════════════════════════════════════════════


def test_rate_limit_default_triplet():
    """RATE_LIMIT_LIST defaults to the burst-cap triplet."""
    # api.py reads env at import. Sub-process this for a clean read.
    code = (
        "import os; os.environ.pop('RATE_LIMIT', None); "
        "from api import RATE_LIMIT_LIST; "
        "print(RATE_LIMIT_LIST)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        check=False, capture_output=True, text=True, encoding="utf-8",
    )
    assert out.returncode == 0, f"subprocess failed: {out.stderr}"
    assert "5/second" in out.stdout, f"default missing 5/second: {out.stdout!r}"
    assert "30/minute" in out.stdout, f"default missing 30/minute: {out.stdout!r}"
    assert "200/hour" in out.stdout, f"default missing 200/hour: {out.stdout!r}"


def test_rate_limit_env_override():
    """RATE_LIMIT env var parses as comma-separated list."""
    env = dict(os.environ, RATE_LIMIT="1/second, 7/minute")
    code = (
        "from api import RATE_LIMIT_LIST; print('|'.join(RATE_LIMIT_LIST))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        check=False, capture_output=True, text=True, env=env, encoding="utf-8",
    )
    assert out.returncode == 0, f"subprocess failed: {out.stderr}"
    parsed = out.stdout.strip().split("|")
    assert parsed == ["1/second", "7/minute"], f"got {parsed!r}"


# ════════════════════════════════════════════════════════════════════
# Section 4 — Docs lockdown (THAMMEN_DEV_MODE)
# ════════════════════════════════════════════════════════════════════
# Subprocess-based because FastAPI(**kwargs) runs at module import. To
# test both modes we need two clean Python processes with different env.


def _docs_check(dev_mode: str | None) -> dict:
    env = dict(os.environ)
    if dev_mode is None:
        env.pop("THAMMEN_DEV_MODE", None)
    else:
        env["THAMMEN_DEV_MODE"] = dev_mode
    code = (
        "import json; from api import app; "
        "print(json.dumps({"
        "'openapi_url': app.openapi_url, "
        "'docs_url':    app.docs_url, "
        "'redoc_url':   app.redoc_url}))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        check=False, capture_output=True, text=True, env=env, encoding="utf-8",
    )
    assert out.returncode == 0, f"subprocess failed: {out.stderr}\nstdout: {out.stdout}"
    # Heroku startup log lines may print before the JSON; grab the JSON line.
    lines = [ln for ln in out.stdout.splitlines() if ln.strip().startswith("{")]
    assert lines, f"no JSON in subprocess stdout: {out.stdout!r}"
    return json.loads(lines[-1])


def test_docs_locked_when_env_unset():
    """THAMMEN_DEV_MODE unset -> all three doc routes return None
    (i.e., not registered, FastAPI returns 404 for them)."""
    info = _docs_check(dev_mode=None)
    assert info["openapi_url"] is None, info
    assert info["docs_url"] is None, info
    assert info["redoc_url"] is None, info


def test_docs_locked_when_env_zero():
    """Anything other than '1' must lock down. Fail-closed default."""
    info = _docs_check(dev_mode="0")
    assert info["openapi_url"] is None, info


def test_docs_locked_when_env_yes_string():
    """'yes' / 'true' must NOT enable docs (only the literal '1' opts in)."""
    info = _docs_check(dev_mode="yes")
    assert info["openapi_url"] is None, info


def test_docs_open_when_env_one():
    """THAMMEN_DEV_MODE=1 restores FastAPI defaults."""
    info = _docs_check(dev_mode="1")
    assert info["openapi_url"] == "/openapi.json", info
    assert info["docs_url"] == "/docs", info
    assert info["redoc_url"] == "/redoc", info


# ════════════════════════════════════════════════════════════════════
# Section 5 — Production verification (Rule #40)
# ════════════════════════════════════════════════════════════════════
# At least one test exercises the LIVE production app object, not a
# replica, asserting the wiring made it through module import end-to-end.


def test_production_app_lockdown_default():
    """In-process import: confirm app.openapi_url is None when env unset."""
    os.environ.pop("THAMMEN_DEV_MODE", None)
    # Force a fresh import — api may already be loaded by earlier tests.
    sys.modules.pop("api", None)
    from api import app  # type: ignore[import-not-found]
    assert app.openapi_url is None, \
        f"production app.openapi_url should be None when THAMMEN_DEV_MODE unset, got {app.openapi_url!r}"


def test_production_app_limiter_uses_cf_key():
    """In-process import: confirm app.state.limiter has our key func."""
    sys.modules.pop("api", None)
    from api import app, cf_remote_address  # type: ignore[import-not-found]
    assert hasattr(app.state, "limiter"), "app.state.limiter must exist"
    # slowapi 0.1.9 stores key_func directly on Limiter
    key_func = getattr(app.state.limiter, "_key_func", None) or \
               getattr(app.state.limiter, "key_func", None)
    assert key_func is cf_remote_address, \
        f"limiter key_func should be cf_remote_address, got {key_func!r}"


# ════════════════════════════════════════════════════════════════════
# Runner
# ════════════════════════════════════════════════════════════════════


TESTS = [
    test_cf_remote_address_cf_header_present,
    test_cf_remote_address_xff_chain,
    test_cf_remote_address_xff_single,
    test_cf_remote_address_fallback,
    test_cf_remote_address_cf_wins_over_xff,
    test_slowapi_semicolon_form_parses,
    test_slowapi_list_form_is_rejected,
    test_rate_limit_default_triplet,
    test_rate_limit_env_override,
    test_docs_locked_when_env_unset,
    test_docs_locked_when_env_zero,
    test_docs_locked_when_env_yes_string,
    test_docs_open_when_env_one,
    test_production_app_lockdown_default,
    test_production_app_limiter_uses_cf_key,
]


def main() -> int:
    passed, failed = 0, []
    for t in TESTS:
        try:
            t()
        except AssertionError as e:
            failed.append((t.__name__, str(e)))
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            failed.append((t.__name__, f"{type(e).__name__}: {e}"))
            print(f"  ERR   {t.__name__}: {type(e).__name__}: {e}")
        else:
            passed += 1
            print(f"  ok    {t.__name__}")

    print(f"\n=== test_sprint_2p16p17_security ===")
    print(f"  passed:  {passed}/{len(TESTS)}")
    print(f"  failed:  {len(failed)}/{len(TESTS)}")
    if failed:
        print()
        for name, err in failed:
            print(f"  - {name}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
