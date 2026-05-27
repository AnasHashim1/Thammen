# CHANGELOG v53 — Sprint 2.16.17: Security Hardening

**Sprint:** 2.16.17
**Engine version:** `thammen-sprint2p16p17-security-hardening`
**Sprint tag:** `2.16.17`
**Files touched:** `api.py`, `evaluate_unified.py` (lines 44-45),
`test_sprint_2p16p17_security.py` (new), `CHANGELOG_v53.md` (this),
plus three Phase 0 probes (`check_version.py`,
`probe_burst_baseline.py`, `probe_docs_exposure.py`) and a one-block
brittle-pin relax in `test_sprint_2p22p0a1_qars_envelope_fallback.py`
(documented in §Regression note below — same anti-pattern Sprint 2.19.1
corrected in 4 files; necessary to keep the regression sweep green
under any post-2.22.0a Sprint).
**Push status:** STOP — push consent reserved for Anas (Rule #32).

---

## Why this Sprint

Sprint 2.16.17 was scouted across multiple sessions starting
2026-05-19 evening (Operational_Rules #32-#37 reference it). Two
production surface issues stood unfixed:

1. **slowapi rate limiting is theatre.** `api.py:106` set
   `Limiter(key_func=get_remote_address, …)` but `Procfile` runs
   uvicorn **without `--proxy-headers`**, so `request.client.host`
   resolves to Heroku's router IP, not the real client. Phase 0
   verified empirically: 20 concurrent POST /api/evaluate from one
   browser-UA IP yielded **8×200 + 12×503 + 0×429**. The 10/minute
   limit never fired. An attacker can sustain >10/min from any IP.
2. **FastAPI auto-docs exposed in production.** `/docs` +
   `/openapi.json` + `/redoc` all returned **HTTP 200** to a normal
   browser-UA HEAD request. Full schema (every route, every Pydantic
   model with example payloads) was a single curl away.

---

## Phase 0 baseline (Rule #36 format)

**Versions on Heroku v136** (slug rebuilt 2026-05-27 evening for the
probe deploy): python 3.10.11 · slowapi 0.1.9 · fastapi 0.136.1 ·
pydantic 2.13.4 · uvicorn 0.46.0. List-form `["x","y","z"]`
**rejected** by slowapi 0.1.9 (Rule #35 caught: kickoff §1 syntax was
wrong; ";"-joined string is the right form for this version — see
§Implementation gotcha below).

**Docs exposure BEFORE** (sandbox IP, browser UA, n=3 HEAD,
2026-05-27T19:31:43Z → 19:31:45Z, base=https://thammen.qa):
- `/docs` → 200 EXPOSED (text/html, 1.13s)
- `/openapi.json` → 200 EXPOSED (application/json, 0.45s)
- `/redoc` → 200 EXPOSED (text/html, 0.41s)

**Burst BEFORE** (sandbox IP, browser UA, n=20 concurrent POST
/api/evaluate at 52/903/90, 2026-05-27T19:31:57Z → 19:32:28Z,
wall=31.6s):
- result: **8×200 + 12×503 + 0×429**
- latency: min 6.0s · P50 30.6s · P95 31.0s · max 31.0s
- 503s are Heroku 30s router timeouts (single uvicorn worker
  serializing the 20-deep queue under load — Sprint 2.16.17 does
  NOT fix this; that's dyno-tier territory, out of scope).

**Phase 0 deviation (Rule #39).** Kickoff §2 said "All probes from
Heroku, not sandbox." Running `heroku run python probe_*.py`
returned HTTP 403 in 30-50ms for every method/path because
Cloudflare blocks the dyno → Cloudflare → dyno loop at the edge
(verified live). Switched to sandbox-IP with a real browser UA,
which is also exactly the path a legit user takes — strictly a
*better* threat-model probe than the kickoff anticipated. (As a
bonus: Cloudflare also rejected `Python-urllib/3.x` UA from
sandbox until headers were filled in.)

---

## What this Sprint ships

### Change 1 — `cf_remote_address` key function (api.py:121-142)

Replaces `get_remote_address` (slowapi default) with a Cloudflare-
aware resolver:

```python
def cf_remote_address(request: Request) -> str:
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",", 1)[0].strip()
    return get_remote_address(request)
```

Cloudflare always sets `CF-Connecting-IP` on real traffic.
Direct `*.herokuapp.com` bypasses (no Cloudflare) carry
`X-Forwarded-For` from Heroku's router and fall back through that.
Final fallback is the legacy `request.client.host` (covers local
testing without any proxy).

### Change 2 — Burst caps via ";"-separated rate-limit string (api.py:147-156, 923, 971)

```python
_RATE_LIMIT_DEFAULT = "5/second,30/minute,200/hour"
RATE_LIMIT = os.getenv("RATE_LIMIT", _RATE_LIMIT_DEFAULT)
RATE_LIMIT_LIST = [s.strip() for s in RATE_LIMIT.split(",") if s.strip()]

limiter = Limiter(key_func=cf_remote_address, default_limits=[])
…
@limiter.limit(";".join(RATE_LIMIT_LIST))   # 5/second;30/minute;200/hour
```

- 5/second — burst cap (anti-script)
- 30/minute — sustained cap (one user evaluating many properties)
- 200/hour — daily envelope (single legit user cap)

`RATE_LIMIT` env var is still respected as a comma-separated list
for tuning post-deploy without a redeploy.

### Change 3 — `THAMMEN_DEV_MODE` docs lockdown (api.py:99-117)

```python
THAMMEN_DEV_MODE = os.getenv("THAMMEN_DEV_MODE", "") == "1"
_docs_kwargs = ({} if THAMMEN_DEV_MODE
                else {"docs_url": None, "redoc_url": None, "openapi_url": None})
app = FastAPI(..., **_docs_kwargs)
```

**Fail-closed default**: unset env var = locked. Only the literal
string `"1"` opens them (not `"yes"`, `"true"`, `"0"` — single
explicit opt-in). Implemented via `FastAPI(...)` kwargs, NOT
middleware — no per-request overhead, the routes are simply not
registered.

### Change 4 — `/api/health` surfaces the new security shape (api.py:656-661)

```json
"security": {
    "cors_locked":     true,
    "rate_limits":     ["5/second", "30/minute", "200/hour"],
    "rate_limit_key":  "cf-connecting-ip",
    "docs_locked":     true
}
```

Lets future audits read the active configuration without
shell-into-dyno.

---

## Implementation gotcha — Rule #35 verified version, NOT just syntax

Kickoff §1 specified `@limiter.limit(["5/second","30/minute","200/hour"])`.
Phase 0 verified slowapi 0.1.9 is installed (matching kickoff
assumption), and my replica `test_slowapi_list_form_parses` initially
confirmed `limiter.limit([…])` returns a callable.

Then the **first run of the production-app verification tests**
caught a `Failed to configure throttling for api.evaluate_quick
(couldn't parse rate limit string '['5/second', '30/minute',
'200/hour']')` ERROR in the import log. The list got `str()`-coerced;
slowapi 0.1.9's parser only accepts a single rate string OR a
semicolon-separated string (`"5/second;30/minute;200/hour"`).

**Silent failure shape**: callable returns OK, decorator binds OK,
but at startup slowapi logs ERROR and the route serves with **no
limit at all**. Exact Bug A2 / silent-boundary-failure pattern.

**Fix**: `";".join(RATE_LIMIT_LIST)` at the decorator. Added two
regression tests that capture slowapi's logger during decorator
binding to catch any future re-introduction:

- `test_slowapi_semicolon_form_parses` — asserts no "Failed to
  configure throttling" ERROR is logged when binding the semicolon
  form.
- `test_slowapi_list_form_is_rejected` — asserts the ERROR IS
  logged when binding the list form. If slowapi ever starts
  supporting lists, this test fails loudly and a maintainer can
  switch back.

This is Operational_Rules #35 in action: requirements.txt told us
"slowapi" (unpinned), Heroku resolved to 0.1.9, but ONLY the
end-to-end "does it actually rate limit at runtime" test caught the
real behaviour.

---

## Tests

`test_sprint_2p16p17_security.py` — 15/15 PASS (was 14/14 + the
2 slowapi regression tests):

| # | Test | Layer |
|---|---|---|
| 1 | cf_remote_address — CF header wins | replica |
| 2 | cf_remote_address — XFF first hop | replica |
| 3 | cf_remote_address — XFF single | replica |
| 4 | cf_remote_address — fallback to client.host | replica |
| 5 | cf_remote_address — CF beats XFF | replica |
| 6 | slowapi semicolon form does NOT log error | replica + logger capture |
| 7 | slowapi list form DOES log error | regression sentinel |
| 8 | RATE_LIMIT_LIST default triplet | subprocess (clean env) |
| 9 | RATE_LIMIT env override | subprocess (clean env) |
| 10 | THAMMEN_DEV_MODE unset → openapi_url None | subprocess (production app) |
| 11 | THAMMEN_DEV_MODE=0 → still locked | subprocess (production app) |
| 12 | THAMMEN_DEV_MODE=yes → still locked | subprocess (production app) |
| 13 | THAMMEN_DEV_MODE=1 → docs restored | subprocess (production app) |
| 14 | In-process: app.openapi_url is None | **Rule #40 production verify** |
| 15 | In-process: limiter.key_func is cf_remote_address | **Rule #40 production verify** |

Run with `PYTHONIOENCODING=utf-8 python test_sprint_2p16p17_security.py`.

Regression: full standalone suite must still exit 0 across the prior
baseline.

### Regression note — brittle-pin relax in test_sprint_2p22p0a1_qars_envelope_fallback.py

Pre-change sweep: **29/30 PASS, 1 FAIL.** The single failure was 2
brittle assertions in `test_sprint_2p22p0a1_qars_envelope_fallback.py`
(section [6], lines 414-418 pre-change):

- `'sprint2p22p0a' in ENGINE_VERSION` — pinned the literal Sprint
  2.22.0a substring.
- `SPRINT_TAG.startswith('2.22.0a')` — same pin shape.

Both fail under any post-2.22.0a Sprint tag. This is the **same
anti-pattern Sprint 2.19.1 corrected** for 4 files
(`test_sprint_2p16p{8,10,11,12}`); the 2.22.0a.2 relax in this file
left these two pins behind. Sprint 2.16.17 relaxes them to a format
check:

```python
_check(ENGINE_VERSION.startswith('thammen-sprint'), ...)
_check(SPRINT_TAG and '.' in SPRINT_TAG, ...)
```

The functional QARS-envelope-fallback regression guard (sections
[1]-[5] above the version stamp) is untouched and continues to
defend the actual Sprint 2.22.0a.1 behavior.

Post-change sweep: **30/30 PASS.**

---

## Smoke plan (post-deploy — Gates 2/3/4)

Three diverse anchors (NOT 51/835/17 — Bug A6 latency):
- 52/903/90 (apartment_building, اللقطة) → expect HTTP 200
- 69/255/75 (apartment_building, لوسيل 69 — Sprint 2.21.4 H1 anchor)
  → expect HTTP 200
- 69/329/20 (apartment_building, غار ثعيلب — Sprint 2.21.3 H11 anchor)
  → expect HTTP 200

Negative tests:
- 6-request burst at /api/evaluate from one IP → expect 5×200 then
  1×429 (the new 5/second cap firing). Re-uses
  `probe_burst_baseline.py` (modified to n=6, single IP).
- HEAD /docs, /openapi.json, /redoc → expect **404** on all three.
- /api/health.security → expect `rate_limits=[...]`,
  `rate_limit_key=cf-connecting-ip`, `docs_locked=true`.

---

## What's NOT in this Sprint (scope discipline, Rule #38)

- **Cloudflare Rate Limiting Rule** (kickoff §1 explicit). Anas's
  manual step post-deploy.
- **Single-dyno burst 503** (single uvicorn worker queuing 20
  concurrent → router 30s timeout). Different problem class
  (concurrency / dyno tier), not rate limiting.
- **Bug A7** (`rics_compliant always false`). Open Medium bug,
  separate Sprint.
- **Authentication of any kind.**
- **Throttling of `/api/calibration`, `/api/health`, `/api/freshness`,
  `/api/about`, `/api/disclaimer`, `/api/scope`.**

---

## Rollback

If post-deploy verification fails:

- Heroku CLI: `heroku rollback v136 --app thammen-app-123` (v136
  is the probe-only deploy, engine identical to v135 = Sprint
  2.22.0a.2 closeout).
- Engine version to restore: `thammen-sprint2p22p0a2-arabic-surface-content-fixes`

If the issue is solely the new rate limits being too tight (e.g.,
legit users hitting 429), set `heroku config:set RATE_LIMIT="10/minute"`
without rolling back — the env-var override takes effect on next
dyno restart.

If the issue is solely docs needing temporary access for a
developer, `heroku config:set THAMMEN_DEV_MODE=1` (and unset when
done).

---

## Rule references

- **#11** Defensive endpoint design (kill-switch via env var = the
  RATE_LIMIT override + THAMMEN_DEV_MODE escape hatch).
- **#32** Push & commit discipline (push consent reserved).
- **#33** Empirical-first audits (Phase 0 measured before any code).
- **#34** File-based scripts (3 probes are file-based).
- **#35** Library version verification (caught list-vs-string
  silent failure).
- **#36** Observed-vs-expected reporting (Phase 0 cites n=20, 31.6s
  window, "8×200 + 12×503" failure modes).
- **#38** Single-purpose Sprint (security hardening is one outcome;
  key + caps + lockdown are co-load-bearing for that one outcome).
- **#39** Deviation justification protocol (sandbox-vs-Heroku probe
  origin).
- **#40** Replica + production verification (tests 14 + 15 hit live
  app object).
- **#43** Heroku deploy via `git subtree push --prefix "deploy v2"`.
- **#51** Audit-driven Sprint pattern (Phase 0 baseline before
  patch; post-deploy comparison before close).
- **E14** Validation scripts must exercise production logic — the
  slowapi-list-form-rejected test exercises slowapi's actual parser,
  not just an attribute check.
