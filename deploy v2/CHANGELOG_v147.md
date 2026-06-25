# CHANGELOG v147 — Sprint 2.22.0b.66 «تحصين الـAPI» (API hardening) — DEBUG T0-3 + T0-4

**Engine:** `thammen-sprint2p22p0b66-api-hardening` · **SPRINT_TAG** `2.22.0b.66` · **Date:** 2026-06-25
**Files:** `api.py` (6 GET routes → `@limiter.limit` + `request: Request`) · `evaluate_unified.py` (cap_rate /0 guard + income dict None-guard + 2 version lines) · `test_sprint_2p16p17_security.py` (+1 test: GET routes rate-limited)
**Class:** 🟢 reversible / backend-only / **VALUE-INVARIANT** (no `index.html`; amount/low/high/method/leadership untouched; the cap_rate guard is DEFENSIVE — not live-reachable per the audit below). First sprint of the approved launch-readiness plan (`deep-crafting-pixel.md`).

## 1. Why this matters
The launch-readiness DEBUG plan flagged two security/crash-safety items for the imminent invited launch:
- **T0-3 — unrated GET endpoints (DoS / khazna-depletion).** The 6 read GET routes (`/api/health`, `/api/freshness`, `/api/calibration`, `/api/disclaimer`, `/api/about`, `/api/scope`) carried **no** `@limiter.limit`. `/api/health` probes GIS (khazna) and `/api/calibration` scans `cap_rates.sqlite` → an unrated flood is a cheap amplification vector against our upstreams. The POST evaluate routes + `/verify` were already rate-limited; the GETs were the gap.
- **T0-4 — `income_value = noi / cap_rate` unguarded.** A `cap_rate` of 0 would raise `ZeroDivisionError` and 500 the eval.

## 2. Root cause
- T0-3: [api.py](api.py) — the 6 GET handlers had `@app.get(...)` then `async def X():` with no limiter decorator and no `request: Request` param (slowapi requires the param to key the limit).
- T0-4: [evaluate_unified.py:1947](evaluate_unified.py:1947) — bare division.

## 3. What this patch does
- **T0-3:** each of the 6 GET routes now carries `@limiter.limit(";".join(RATE_LIMIT_LIST))` (the same `5/second;30/minute;200/hour` burst-cap triplet as the POST routes) + a `request: Request` param. Static routes (`/`, `/logo.png`, `/qrcode.local.js`, `/fonts/{f}`) stay intentionally unrated. Defense-in-depth behind Cloudflare.
- **T0-4:** `income_value = (noi / cap_rate) if (cap_rate and cap_rate > 0) else None`, plus a None-guard on the income dict's `'value': round(income_value) if income_value else None` (line ~1967, mirroring the existing `gross_yield`/`net_yield` guards). `None` flows gracefully: the income cross-check shows no value, and `_income_triangulation` gates on `income.get('value')` truthiness → income_led simply won't fire (no crash, no wrong number).

## 4. The cap_rate guard is DEFENSIVE (live audit)
`cap_rates.sqlite` = 200 rows; **82** have `cap_rate ≤ 0 / NULL` but **every one of them is `confidence='fallback'`** — and a fallback row is **never returned** by `_lookup_calibrated_cap_rate` (it only serves reliable/indicative cells). All **16 usable cells** (6 reliable + 10 indicative) have `cap_rate > 0`. So the /0 is **not live-reachable today**; the guard hardens the path against a future bad/hand-set row. Documented inline at the call site.

## 5. Verification — empirical evidence
- `py_compile` on `api.py` + `evaluate_unified.py` — clean.
- `import api` — app builds; **14 routes**; `app.state.limiter` present.
- `test_sprint_2p16p17_security.py` — **16/16** (15 prior + the new `test_get_routes_are_rate_limited` source-structural check: every one of the 6 GET routes carries `@limiter.limit` + `request: Request`; static routes not asserted).
- DoD: aggregator ALL-MATCH · surface 45/45 · broad walk all-green (see Session_Log §20.95).
- Live smoke (browser-UA #61): `/api/health` → engine `…b66-api-hardening`, still **200**; a >30-in-a-minute GET burst returns **429** (rate-limit live); the 5-fixture value byte-gate identical to v237.

## 6. Deployment
```
git add "deploy v2/api.py" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2p16p17_security.py" "deploy v2/CHANGELOG_v147.md" "deploy v2/docs/Session_Log.md"
git commit -m "Sprint 2.22.0b.66: API hardening (T0-3 GET rate-limits + T0-4 cap_rate /0 guard); value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl
```
curl -s https://thammen.qa/api/health   # → engine_version thammen-sprint2p22p0b66-api-hardening, status 200
for i in $(seq 1 35); do curl -s -o /dev/null -w "%{http_code} " https://thammen.qa/api/health; done  # → trailing 429s after ~30
```

## 8. What's NOT in this patch
- The income_led decomposition/value_floor coherence (T0-2) — the next sprint (Gate-2).
- The a24 privacy-notice truthfulness (T0-1) — needs the PO/counsel word.
- The cap_rate guard does NOT change any live value (defensive). `/api/health`'s ceiling stays the standard 30/min — a monitoring cron at <1/min is unaffected; if a sub-2s monitor is ever added, raise its ceiling then.
