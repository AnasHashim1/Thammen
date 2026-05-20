# Security Audit — Pre-Sprint 2.16.17 Scouting (v2 — empirical-first)

> **Status:** Scouting / pre-Sprint reconnaissance. **No code modified. No deploy.**
> **Date:** 2026-05-19 evening (after Sprint 2.16.15 deployed; before Confirmed-Sales Sprint 2.16.16 on Thursday).
> **Auditor:** Claude session.
> **Product context:** `thammen.qa` is a **public real-estate AVM**, NOT fintech, no user accounts, no PII stored, no payments, no cookies. Threat model is biased toward **bot reconnaissance + scraping + amplification**, not credential theft.
> **What changed from v1:** Replaced theoretical OWASP-style audit with measurements taken from production today. Vulnerabilities now ranked by **Thammen-specific severity**, not generic web-app severity. Sprint plan filtered to only fixes meeting one of three explicit criteria.

---

## Probe Re-Run 2026-05-19 evening — External IP verification

> Second round of probes after the v2 audit was written. Run from Anas's Windows machine (real external IPv6, public Cloudflare-fronted path — **not** from the Heroku dyno). 20-minute time cap. Captures what an external attacker sees today.

| # | Test | Command essence | Result | Interpretation |
|---|---|---|---|---|
| 1 | 25× sequential `GET /api/health` | `for i in {1..25}; do curl ... ; done \| sort \| uniq -c` | **25 × 200** | Re-confirms V4: zero rate limiting on `/api/health`, neither at app nor Cloudflare layer |
| 2 | 10× parallel `POST /api/evaluate` (payload `{"zone":52,"street":903,"building":90}`, address chosen A6-safe per CLAUDE.md §22) | `seq 1 10 \| xargs -P 10 -I{} curl ... -X POST ...` | **8 × 200** (latencies 4.6s → 29.1s, growing linearly = queue building) + **2 × 503** (Heroku router 30s timeout) | **🔴 DoS surface CONFIRMED**: 10 concurrent POSTs from a single IP are enough to (a) saturate the single web.1 dyno's request queue and (b) cause 20% of subsequent requests to fail with 503. **No 429 was emitted** by either slowapi (10/min limit allows the burst — limit is per-minute, not per-burst) or Cloudflare. A user attempting to evaluate during the burst window experienced real failure. Test STOPPED before escalation to 20-parallel per agreed safety rule. |
| 3 | `git log --all --full-history -- '*.env' '.env*'` | (same) | Only `c9c3226` ("Sprint 1: CORS, rate limit, env vars, logging, MoJ cache") touched `.env.example` (the *template*, not a real secret file). `git log --all --diff-filter=A -- '.env'` returns empty. Currently tracked: `.env.example` only. | **✅ Clean.** No real `.env` ever committed to any branch. No secret rotation needed. |
| 4 | `heroku logs --num=5000` | (same) | Heroku capped output at **1500 real log lines**, spanning **2026-05-18T08:42:51 UTC → 2026-05-19T18:28:15 UTC = ~33.75 hours**. **0 × 429** anywhere in this window. | Earlier v2 audit claimed "0 × 429 in 5,000 lines" — correction: the actual window is **1,500 lines / 33.75 hours**, not 5,000 / arbitrary span. Conclusion (slowapi rate limit on `/api/evaluate*` has never fired in the most-recent ~34 hours) still holds, but with a smaller evidence base than v2 stated. |

### 🔴 Action Required TONIGHT (Anas — manual, 5 min)

**V18 (DoS surface) confirmed empirically** — 10 POSTs من IP واحد أسقطوا dyno لـ ~30s. **Cloudflare Rate Limiting Rule = mitigation فوري لا ينتظر Sprint 2.16.17.**

Cloudflare dashboard → **Security → Rate Limiting Rules → Create rule**:

- **Match:** `http.request.uri.path eq "/api/evaluate"` AND `http.request.method eq "POST"`
- **Threshold:** 5 requests / 1 minute / per IP
- **Action:** Block for 60 seconds
- **Status:** ⏳ Pending — يُحدَّث إلى ✅ بعد إنشاء القاعدة

> رمز **"Defense in depth"**: هذه طبقة edge (Cloudflare يمتص قبل ما يصل dyno). بند #6 في Sprint 2.16.17 أدناه = طبقة app احتياطية (slowapi per-burst limit) — تشتغل لو DNS misroute أو لو احد وصل origin مباشرة عبر `*.herokuapp.com`.

### Implications for the Sprint plan

1. **Item 2 widened.** `/docs` lockdown must cover `/openapi.json` and `/redoc` too — all three are exposed today. Same env-var flag, same middleware. Updated below.
2. **Item 4 retained.** No 429 appeared from Cloudflare during the bursts, so the app-side rate limit on `/api/health` (V4) is still the only realistic defence. The §5 Cloudflare rate-limiting rule remains a manual prerequisite.
3. **New item 5 added.** `.env` git-history is empirically clean; this becomes a documented checkpoint in the Sprint (not an action — just a recorded verification).
4. **DoS surface (V18) addressed in two layers.** Surfaced only by the burst probe. Mitigation: **(a)** Cloudflare Rate Limiting Rule TONIGHT (manual, §5.2 #7 below, 5-min toggle) absorbs at edge before traffic reaches the dyno; **(b)** slowapi per-burst limit in **Sprint 2.16.17 item #6** below (1–2 lines) as app-side defense-in-depth (catches direct-to-origin requests bypassing Cloudflare). Larger architectural fix (scaling to 2× web dynos = recurring $$$) explicitly deferred — single-purpose Sprint discipline.

---

## 0. Empirical baseline — measured 2026-05-19 evening

> Per [Project_Instructions §5](docs/Project_Instructions.md) and the marathon §21.6 rule: **measure before proposing**. Everything below is real data from production today, not assumption.

### 0.1 Probe: 25× sequential `GET /api/health` from external IP

```
$ for i in $(seq 1 25); do curl -s -o /dev/null -w "%{http_code} " \
    --max-time 10 https://thammen.qa/api/health; done

200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200
```

**25 / 25 = HTTP 200. Zero rate limiting fired.** Neither Cloudflare nor the application limits this endpoint. This empirically confirms vulnerability **V4** below (was theoretical **S6** in v1 of this audit).

### 0.2 Probe: response headers on `GET /` and `GET /api/health`

```
$ curl -s -D- -o /dev/null https://thammen.qa/api/health | \
    grep -iE "strict|frame|content-type-options|content-security|referrer|permissions"
(no matches)

$ curl -s -D- -o /dev/null https://thammen.qa/ | \
    grep -iE "strict|frame|content-type-options|content-security|referrer|permissions"
(no matches)
```

Other headers present (informational):
```
Server: cloudflare              ← Cloudflare proxy confirmed
via: 2.0 heroku-router          ← origin = Heroku (minor info disclosure)
CF-RAY: 9fe518...-DOH           ← Cloudflare edge in Doha
nel: {...heroku-nel...}         ← Network Error Logging (heroku-managed)
```

**Zero security headers from either Cloudflare OR application.** Confirms vulnerability **V2** empirically. The Cloudflare HSTS toggle (§5 below) is OFF.

### 0.3 Probe: API documentation lockdown

```
$ curl -s -o /dev/null -w "HTTP %{http_code}\n" https://thammen.qa/docs
HTTP 200

$ curl -s https://thammen.qa/docs | head -3
<!DOCTYPE html>
<html>

$ curl -s https://thammen.qa/openapi.json | wc -c
6758
```

**`/docs` returns full Swagger UI. `/openapi.json` dumps 6.7 KB of schema** — including the Sprint 2.16.10 tower-input split, the Sprint 2.16.7 numeric bounds, audience whitelist, and every internal field name. Empirically confirms vulnerability **V3**.

### 0.4 Probe: bot-attractive paths

```
/admin            → 404
/.git/config      → 404
/wp-admin         → 404
/server-status    → 404
/actuator/health  → 404
/env              → 404
/config.json      → 404
```

**No leaked admin paths.** FastAPI's default 404 returns no body content, no version strings. ✅ Clean.

### 0.5 Production logs grep — last 5,000 lines

```
$ heroku logs -n 5000 -a thammen-app-123 | \
    grep -ciE "429|rate.?limit|blocked|attack|suspicious|denied"
23
```

22 of the 23 matches are **configuration announcements at startup** (the literal string `"Rate limit configured: 10/minute for /api/evaluate*"` emitted by [api.py:109](deploy v2/api.py:109) on every dyno start). They prove the slowapi config loads cleanly. They do NOT indicate the limit ever fired.

**One genuine attack signature found:**

```
2026-05-19T00:27:55.047429+00:00 app[web.1]:
  INFO:     16.176.153.134:0 - "GET /prod/.env HTTP/1.1" 404 Not Found
```

A bot from `16.176.153.134` probed `/prod/.env` — classic recon for AWS/Heroku secrets. Returned 404 (no such path). **The attack failed because we don't have a /.env route, not because of any defense.** This is the empirical justification for the **dependency pinning + /docs lockdown** items below: bots ARE scanning thammen.qa, and the next probe will be against `/docs` and `/openapi.json` which we serve happily.

### 0.6 Summary of empirical findings

| What was theoretical in v1 | Reality measured today |
|---|---|
| "Rate limiting on `/api/health` is missing" | ✅ Confirmed: 25/25 hits returned 200 |
| "No security headers" | ✅ Confirmed: zero headers, neither app nor Cloudflare |
| "`/docs` exposed" | ✅ Confirmed: HTTP 200, full Swagger UI |
| "Slowapi rate-limit fires on abuse" | ❓ Cannot confirm: no 429 in 5,000 lines of logs (no abuse evidence in window OR limit broken — likely former) |
| "Bots are scanning" | ✅ Confirmed: `/prod/.env` recon attempt 2026-05-19 00:27 UTC |
| "Cloudflare in front" | ✅ Confirmed: `Server: cloudflare` + `CF-RAY` |

---

## 1. Current state — what is in `api.py` today

### 1.1 Rate limiting

| Location | Endpoint | Limit |
|---|---|---|
| [api.py:724](deploy v2/api.py:724) | `POST /api/evaluate` | `RATE_LIMIT` env, default `10/minute` per IP |
| [api.py:766](deploy v2/api.py:766) | `POST /api/evaluate/details` | same |
| Everything else | (no decorator) | unlimited |

`Limiter(key_func=get_remote_address, default_limits=[])` at [api.py:106](deploy v2/api.py:106). The `default_limits=[]` means each endpoint must opt in — **6 GET endpoints are currently uncovered**.

### 1.2 CORS ([api.py:119-125](deploy v2/api.py:119))

Locked to `https://thammen.qa,https://www.thammen.qa` by default. `allow_credentials=True` with explicit origins is correct. ✅ No change needed.

### 1.3 Debug / production mode

- `FastAPI(...)` at [api.py:97](deploy v2/api.py:97) has no `debug=` flag (defaults False). ✅
- Procfile: `web: uvicorn api:app --host 0.0.0.0 --port $PORT` (no `--reload`). ✅
- `LOG_LEVEL=INFO` default ([api.py:33](deploy v2/api.py:33)). ✅
- BUT `docs_url`, `redoc_url`, `openapi_url` NOT overridden — `/docs`, `/redoc`, `/openapi.json` all live (§0.3 confirmed). ❌

### 1.4 Security headers in application

Grep result across all of `deploy v2/`:

```
$ grep -rE "Strict-Transport-Security|Content-Security-Policy|X-Frame-Options|\
X-Content-Type-Options|Referrer-Policy|Permissions-Policy" deploy v2/
(no matches)
```

Zero. ❌

### 1.5 Dependencies ([requirements.txt](deploy v2/requirements.txt))

```
requests
beautifulsoup4
tabulate
fastapi
uvicorn
slowapi
```

Six packages, **zero version pins**, no `secure`, no `starlette-security`. Heroku resolves on every build → silent drift / supply-chain exposure.

---

## 2. Vulnerabilities — ranked by **Thammen-specific** severity

Severity columns:

- **Severity for THIS product** = real impact for a public AVM with no PII, no auth, no payments, Cloudflare-fronted.
- **OWASP generic severity** = what a generic web-security checklist would say (for reference only).
- **Skip — overkill?** = explicit yes/no with one-line reason.

### 🟠 Sprint 2.16.17 candidates

| ID | Issue | Where | OWASP generic | **THIS product** | Skip? |
|---|---|---|---|---|---|
| **V1** | `HTTPException(detail=str(e))` leaks raw exception text to client | [api.py:762](deploy v2/api.py:762), [api.py:871](deploy v2/api.py:871) | High (info disclosure) | **Medium**: in worst case leaks file paths like `/app/moj_weekly.csv`. No secrets/keys in code, so not catastrophic, but trivial to fix. | **NO** — standard, ~10 lines, no downside |
| **V2** | No HSTS / X-Frame-Options / X-Content-Type-Options / Referrer-Policy emitted | application-wide | High (clickjacking, MIME sniffing, downgrade) | **Medium**: Cloudflare provides TLS but isn't injecting these. If a future direct-to-Heroku probe bypasses Cloudflare (or DNS misroute), defense vanishes. Also: Cloudflare HSTS toggle (§5) needs origin-app HSTS to mark domain as preload-eligible. | **NO** — required by standard practice; ~15 lines hand-rolled middleware |
| **V3** | `/docs`, `/redoc`, `/openapi.json` publicly accessible | FastAPI defaults; no override at [api.py:97](deploy v2/api.py:97) | Medium (info disclosure) | **Medium**: bots already scanning (§0.5 `/prod/.env` probe). Next scan picks up `/openapi.json` and we hand them every field name, type, and constraint. Free reconnaissance. | **NO** — empirically justified, 4-line fix |
| **V4** | `/api/health` calls `khazna.gisqatar.org.qa` synchronously and is unrate-limited | [api.py:545-547](deploy v2/api.py:545), confirmed §0.1 | Medium (amplification, DoS-of-third-party) | **Medium-High**: a botnet hammering `/api/health` makes Thammen a low-rate amplification vector against GIS Qatar. The GIS team relationship matters for [Project_Instructions §12](docs/Project_Instructions.md). | **NO** — one-line `@limiter.limit("30/minute")` |

### 🟡 Defer to Sprint 2.16.18 or backlog

| ID | Issue | Where | OWASP generic | **THIS product** | Skip in 2.16.17? |
|---|---|---|---|---|---|
| **V5** | Unpinned dependencies in `requirements.txt` | [requirements.txt](deploy v2/requirements.txt) | High (supply chain) | **Medium**: real risk (any future build could pull a compromised version), but separate concern from boundary security. Best handled with `pip-compile` + lockfile + `pip-audit` CI step. | **YES** — split into Sprint 2.16.18; out of scope here |
| **V6** | Probe errors include external URLs via `str(e)[:200]` | [api.py:603](deploy v2/api.py:603), [api.py:607](deploy v2/api.py:607) | Low | **Low**: leaks Khazna URL strings via `/api/health`. The URL is already documented in CLAUDE.md so the leak is symbolic. Truncated to 200 chars. | **YES** — bundle with V1 incidentally if cheap, otherwise defer |
| **V7** | `extra='forbid'` pattern not enforced as a *project rule* | [api.py:240, 269](deploy v2/api.py:240) | N/A | **Low**: Sprint 2.16.15 fixed the two existing models. Future models could regress. Better handled by a `test_no_extra_ignore.py` regression test. | **YES** — backlog, not a hardening Sprint concern |

### 🟢 Explicitly **skip** — overkill for Thammen

| ID | Generic "security best practice" | Why we're skipping |
|---|---|---|
| **V8** | Content-Security-Policy (CSP) | [index.html](deploy v2/index.html) is static, has inline `<style>`, loads only `fonts.googleapis.com` + `fonts.gstatic.com`. No user-generated HTML rendered. Real XSS attack surface ≈ zero. A non-trivial CSP would block our own fonts on first deploy. **High break-risk, near-zero security value.** Revisit if Thammen ever renders user content. |
| **V9** | HSTS preload (`includeSubDomains; preload`) | Preloading is **hard to undo** (browsers cache the entry for ~1 year). Cloudflare's HSTS toggle handles preload candidacy when needed. We emit basic HSTS (`max-age=31536000`) — sufficient. |
| **V10** | `secure` library / `starlette-security` dependency | Adds a 7th unpinned dep on top of an already-unpinned `requirements.txt`. ~15 lines of hand-rolled middleware achieves the same coverage with no new attack surface. **Don't add deps you can avoid.** |
| **V11** | Permissions-Policy header | Thammen doesn't use camera, mic, geolocation, payment — but the browser default is "ask, then deny." Adding the header is 1 line but **gives bots a fingerprint of which APIs you care about disabling**. Truly negligible value. |
| **V12** | CSRF tokens on POST endpoints | No sessions, no cookies, no auth state → CSRF surface = 0. Standard FastAPI + CORS-locked is enough. |
| **V13** | 2FA / SSO / API keys for `/api/evaluate*` | No user accounts. Rate-limit handles abuse. Adding auth = new attack surface for zero security gain on a public AVM. |
| **V14** | Rate limit `<` 5 requests/minute | Anas does normal evaluations interactively; aggressive limits would block himself. Current `10/min` is fine. |
| **V15** | Audit logging of every request | No PII, no privacy obligation. Heroku already logs request lines (§0.5). Adding structured audit log = noise + storage cost. |
| **V16** | Secret rotation / vault | No secrets exist in code. `.env` only has CORS list and rate-limit string. Nothing to rotate. |
| **V17** | mTLS / Cloudflare Authenticated Origin Pulls | Free Cloudflare tier doesn't expose origin-cert config simply, and the threat (someone hits Heroku directly bypassing Cloudflare) requires them to first discover the Heroku app name `thammen-app-123`. Not zero risk but not 2.16.17-grade. |

---

## 3. Search results — what was looked for, what was found

| Query | Result |
|---|---|
| Endpoints accepting input without Pydantic | None. POST `/api/evaluate*` use Pydantic + `extra='forbid'` (Sprint 2.16.15). GETs take no body. |
| Stack trace into response body | **V1** (two sites). `log.error(..., exc_info=True)` server-side only — safe. |
| SQL string formatting / f-strings on user input | One f-string at [listing_db.py:209](deploy v2/listing_db.py:209) — verified safe (dynamic portion is hardcoded condition keys, values use `?` placeholders). |
| `DEBUG=True` | None. ✅ |
| Hardcoded secrets / API keys | None. `.env.example` only has CORS origins / rate-limit / paths / log level. ✅ |
| `pickle.loads`, `eval(`, `exec(`, `shell=True` on user input | None on user-input paths. ✅ |
| Server admin paths leaked | None (§0.4 — all 7 probes returned 404). ✅ |
| TLS version floor | Cloudflare-controlled; verified via §5 dashboard checklist not via code. |

---

## 4. Proposed Sprint 2.16.17 — single-purpose, three-criterion plan

**Each item must satisfy at least one of:**

1. **Documented in Heroku logs** (real attack evidence or measurement), OR
2. **Cost ≤ 30 lines of code**, OR
3. **Required by an explicit external standard** (e.g. Cloudflare HSTS pre-flight, RICS audit response, browser policy).

If none → defer. Result: **4 items in, V5/V6/V7 deferred, V8–V17 explicitly skipped.**

| # | Item | Criterion met | Lines | Why |
|---|---|---|---|---|
| 1 | **`SecurityHeadersMiddleware`** — hand-rolled, emits HSTS + X-Frame-Options + X-Content-Type-Options + Referrer-Policy | (2) ~15 lines, (3) HSTS pre-req for Cloudflare preload | ~15 | §0.2 confirms zero headers today; §5 Cloudflare HSTS toggle requires origin-app HSTS for preload candidacy |
| 2 | **Lock `/docs` + `/openapi.json` + `/redoc`** behind `THAMMEN_ENABLE_DOCS` env var (default off). 3 endpoints, same flag, same middleware. | (1) bot recon `/prod/.env` 2026-05-19 = `/openapi.json` next; (2) ~6 lines | ~6 | §0.3 + §0.5 + Probe Re-Run #2 widened scope |
| 3 | **Safe error responses** — replace `HTTPException(detail=str(e))` with `detail=f"خطأ داخلي. الرقم المرجعي: {uuid12}"`, log real error server-side | (2) ~10 lines | ~10 | V1 standard practice |
| 4 | **Rate-limit `/api/health`** to `30/minute` per IP | (2) 1 line, (3) third-party-courtesy to GIS Qatar | ~1 | V4 — prevents amplification. **Probe Re-Run #1 confirmed no 429 fires today**, so this remains the only realistic defence. |
| 5 | **`.env` git-history clean checkpoint** — verified, no action needed in this Sprint | (1) Probe Re-Run #3 confirmed | ~0 | Documents the verification in the Sprint changelog so future audits don't have to re-run the check. If a future commit ever adds a real `.env`, this checkpoint flips to a *blocker* and triggers cleanup (`git filter-repo` + secret rotation + `.gitignore` update). |
| 6 | **slowapi per-burst limit** on `/api/evaluate*` — `@limiter.limit(["10/minute", "3/10second"])` | (1) Probe Re-Run #2 empirical V18; (2) 1–2 lines; surgical not architectural — defense-in-depth behind Cloudflare edge rule | ~1–2 | **Verified syntax:** slowapi 0.1.9 deployed (`heroku run pip show slowapi`) → list form supported. The `3/10second` clamp catches the exact burst pattern measured (10 POSTs in <1s would be denied at request 4). App-layer fallback for the Cloudflare rule above. |

**Total: 6 items, ~32 lines net new in `api.py`.** (v1 was 5 items / ~30 lines; +2 for widened item 2 covering all 3 OpenAPI endpoints; +1–2 for item 6 burst limit. Items 5 is a doc checkpoint, not code.)

### 4.1 What this Sprint MODIFIES

- `api.py` only.
- `ENGINE_VERSION` in [evaluate_unified.py:42](deploy v2/evaluate_unified.py:42) bumped to `thammen-sprint2p16p17-security-hardening` (Sprint convention per CLAUDE.md).
- `index.html` untouched.
- `requirements.txt` untouched (V10: no new dep; V5: separate Sprint).

### 4.2 What this Sprint LEAVES ALONE

- CSP, Permissions-Policy, HSTS preload, secure library (V8–V11 — overkill).
- Dependency pinning (V5 — Sprint 2.16.18, own concern).
- Probe error truncation (V6 — bundle if zero-cost, else defer).
- Audit logging, secret rotation, mTLS, auth (V12–V17 — not applicable to Thammen).

### 4.3 Tests — `test_sprint_2p16p17_security.py` (new isolated file)

Per [Project_Instructions §5](docs/Project_Instructions.md) pre-deploy item #5 (≥5 cases including fallback):

1. `Strict-Transport-Security: max-age=31536000` present on every response.
2. `X-Frame-Options: DENY` present.
3. `X-Content-Type-Options: nosniff` present.
4. `Referrer-Policy: strict-origin-when-cross-origin` present.
5. `GET /docs` returns 404 when `THAMMEN_ENABLE_DOCS=0`.
6. `GET /docs` returns 200 when `THAMMEN_ENABLE_DOCS=1` (fallback for local dev).
7. Forced 500 from engine → response body does NOT contain `KeyError`, `FileNotFoundError`, or absolute paths; DOES contain a 12-char hex correlation ID.
8. 31 rapid hits on `/api/health` → request #31 returns 429.
9. **Regression:** legal `POST /api/evaluate` payload still works end-to-end with Sprint 2.16.15 `extra='forbid'` intact.

### 4.4 Post-deploy verification (per CLAUDE.md cmd-syntax convention)

```cmd
cd /d "C:\Thammen\deploy v2"
curl -s -D- -o NUL https://thammen.qa/ | findstr /I /C:"Strict-Transport-Security"
curl -s -D- -o NUL https://thammen.qa/ | findstr /I /C:"X-Frame-Options"
curl -s -D- -o NUL https://thammen.qa/ | findstr /I /C:"X-Content-Type-Options"
curl -s -o NUL -w "%%{http_code}" https://thammen.qa/docs
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":52,\"street\":903,\"building\":90}" > legal.json
findstr /C:"thammen-sprint2p16p17-security-hardening" legal.json
```

Smoke on 3 diverse addresses post-deploy (per Project_Instructions §5 #6):
- `52/903/90` (villa, A6-safe baseline per CLAUDE.md §22)
- `69/305/201` (Lusail tower — confirms Sprint 2.16.10 path still works)
- `61/875/20` (Public Works — confirms Bug A11 flag still emits)

---

## 5. Cloudflare manual checklist — Anas does these in the dashboard

> §0.2 confirmed Cloudflare is in front of `thammen.qa`. Most of these are toggle-and-go; the rate-limiting rule is the only one needing rule-editor work.

### 5.1 SSL/TLS — must be set BEFORE the Sprint deploy (otherwise app HSTS could lock users into a broken cert)

| # | Setting | Path | Target |
|---|---|---|---|
| 1 | SSL/TLS encryption mode | SSL/TLS → Overview | **Full (strict)** — confirm before flipping; Heroku origin must have valid TLS |
| 2 | Always Use HTTPS | SSL/TLS → Edge Certificates | **ON** |
| 3 | Minimum TLS Version | SSL/TLS → Edge Certificates | **TLS 1.2** |
| 4 | TLS 1.3 | SSL/TLS → Edge Certificates | **ON** |
| 5 | HSTS at the edge | SSL/TLS → Edge Certificates → HSTS | **Enable** with `max-age=15552000` (6 months), Include subdomains: ON, **Preload: only after the Sprint 2.16.17 app-side HSTS is live for ≥7 days without issues** |
| 6 | Automatic HTTPS Rewrites | SSL/TLS → Edge Certificates | **ON** |

### 5.2 Security

| # | Setting | Path | Target |
|---|---|---|---|
| 7 | 🔴 **URGENT TONIGHT — Rate-Limiting Rule** (the only one that's rule-editor work, not a toggle) | Rules → Rate Limiting Rules → Create rule | Per the "Action Required TONIGHT" block above: `http.request.uri.path eq "/api/evaluate"` AND `http.request.method eq "POST"` → threshold `5 / 1 minute / per IP` → action `Block 60s`. Empirically justified by Probe Re-Run #2 (V18 confirmed). |
| 8 | Bot Fight Mode | Security → Bots | **ON** (free; blocks known-bad bots like the `/prod/.env` scanner from §0.5) |
| 9 | Security Level | Security → Settings | **High** |
| 10 | Browser Integrity Check | Security → Settings | **ON** |
| 11 | Challenge Passage | Security → Settings | **30 minutes** |
| 12 | WAF Managed Rules → Cloudflare Managed Ruleset | Security → WAF | **Enabled** (free baseline) |
| 13 | Page Rule for `/api/health` | Rules → Page Rules (or Configuration Rules) | Cache Level: **Bypass**, Security Level: **Medium**. Health probes shouldn't be cached or aggressively challenged. |

### 5.3 Network / hygiene

| # | Setting | Path | Target |
|---|---|---|---|
| 14 | DNS proxying for `thammen.qa` / `www.thammen.qa` | DNS | **Orange cloud (Proxied)** — confirm both records, hides Heroku origin IP |
| 15 | WebSockets | Network | **OFF** (Thammen doesn't use them) |
| 16 | IPv6 Compatibility | Network | **ON** |

### 5.4 What to NOT touch

- Email Obfuscation, Hotlink Protection, Cache Rules, Workers — out of scope; defaults are fine.
- Spectrum, Argo, Magic Transit — paid features; defer.

### 5.5 Verification command (run from your laptop after the toggles)

```cmd
curl -s -D- -o NUL https://thammen.qa/ | findstr /I "strict-transport"
```

After step 5 (HSTS toggle), the response should include `Strict-Transport-Security: max-age=...` even **before** the Sprint deploys.

---

## 6. `verify_cloudflare.py` — proposed spec (not yet written)

A read-only smoke that **runs from Heroku via `heroku run`** — same pattern as [smoke_mthamen_v2.py](deploy v2/smoke_mthamen_v2.py) per [Project_Instructions §21.6](docs/Project_Instructions.md). Heroku-side execution matters because:

- Cloudflare may behave differently for traffic originating outside Qatar.
- Running from a known dyno IP keeps the Cloudflare access logs clean and attributable.
- Reproducible: anyone on the team can run `heroku run python verify_cloudflare.py` to get the same baseline.

### 6.1 Inputs

- None. Defaults to `https://thammen.qa`. `THAMMEN_URL` env override (set via `heroku config:set` if needed for staging).

### 6.2 Test address

**`52/903/90`** for the POST probe — A6-safe per [CLAUDE.md §22](docs/Project_Instructions.md). **Never `51/835/17`** (Bug A6 catalogued latency outlier).

### 6.3 Checks (sequential, ~15 seconds total — well under Heroku one-off dyno startup overhead)

| # | Check | Pass condition | Why |
|---|---|---|---|
| 1 | Fire 20× `POST /api/evaluate` with address `52/903/90` | ≥ 1 response is `429` (from slowapi OR Cloudflare) AND ≥ 10 are `200` | Confirms rate limit alive; today's logs show 0 firings in 5,000 lines, so this is the **regression guard** post-Sprint |
| 2a | `GET /` → header `Strict-Transport-Security` | contains `max-age=` and `includeSubDomains` | V2 fix landed |
| 2b | `GET /` → header `X-Frame-Options` | == `DENY` | V2 fix landed |
| 2c | `GET /` → header `X-Content-Type-Options` | == `nosniff` | V2 fix landed |
| 2d | `GET /` → header `Referrer-Policy` | non-empty | V2 fix landed |
| 2e | `GET /` → header `CF-RAY` | present | Confirms Cloudflare proxy is still in front (DNS hijack guard) |
| 3a | `GET /docs` | == `404` | V3 fix landed (with default `THAMMEN_ENABLE_DOCS=0`) |
| 3b | `GET /openapi.json` | == `404` | V3 fix landed |
| 4 | Fire 35× `GET /api/health` rapidly | request #31 or later is `429` | V4 fix landed |
| 5 | Force a 500 (e.g. `POST /api/evaluate` with `{"zone":-99999,"street":-99999,"building":-99999}`) | response body is JSON, does NOT contain `KeyError`, `FileNotFoundError`, `Traceback`, or `/app/`; DOES contain 12-char hex | V1 fix landed |
| 6 | `OPTIONS /api/evaluate` with `Origin: https://attacker.example` | `Access-Control-Allow-Origin` is absent OR != `https://attacker.example` | CORS regression guard from Sprint 1 hardening |

### 6.4 Output format

ASCII table — each row `PASS / FAIL` + one-line evidence. Exit code 0 if all pass, 1 otherwise. Example:

```
THAMMEN SECURITY VERIFICATION — 2026-05-22 09:00 Doha
URL: https://thammen.qa

  #   CHECK                                        STATUS    EVIDENCE
  --  -------------------------------------------  ------    ----------------
  1   Rate limit fires on /api/evaluate (20×)      PASS      429 at request 11
  2a  Strict-Transport-Security present            PASS      max-age=31536000
  2b  X-Frame-Options                              PASS      DENY
  2c  X-Content-Type-Options                       PASS      nosniff
  2d  Referrer-Policy                              PASS      strict-origin-when-cross-origin
  2e  CF-RAY (Cloudflare proxy alive)              PASS      9fe51...-DOH
  3a  /docs locked                                 PASS      404
  3b  /openapi.json locked                         PASS      404
  4   /api/health rate-limited                     PASS      429 at request 31
  5   500 response does not leak internals         PASS      detail contains hex ID
  6   CORS rejects attacker origin                 PASS      header absent

  RESULT: 11/11 PASS
```

### 6.5 When to run

- Once **immediately after Sprint 2.16.17 deploys** (verifies the Sprint landed).
- Weekly automated cron via `heroku scheduler` (~$0/month on free tier) — adds **regression detection** for the most likely security regressions (someone disables the middleware, env var flips, Cloudflare DNS proxy is turned off by mistake).
- **Manual run** every time CLAUDE.md is updated or the Sprint workflow changes.

---

## 7. Risk acceptance — if Sprint 2.16.17 is **not** done

Realistic worst-case ranked by probability (highest first):

| # | Scenario | Probability | Impact | Mitigated by |
|---|---|---|---|---|
| 1 | Bot scans `/openapi.json`, dumps full API schema, posts on a Discord channel | High (recon already happening §0.5) | Low (reputational, no immediate exploit) | V3 (4-line fix) |
| 2 | `/api/health` looped by bot → Thammen DDoS-amplifies against GIS Qatar (§0.1 confirms zero limit) | Medium | Medium-High (relationship with GIS team — see Project_Instructions §12) | V4 (1-line fix) |
| 3 | Mobile browser caches a non-HTTPS render once, downgrade attack possible until cache expires | Low | Low | V2 (HSTS) |
| 4 | A 500 leaks `/app/moj_weekly.csv` in a screenshot that ends up on Twitter | Low | Low (reputational only — no secret revealed) | V1 |
| 5 | Cloudflare config drift over months → DNS unproxied accidentally | Low | High | Verify_cloudflare.py cron (§6.5) |

None are critical. The cluster is small enough to fix in one ~30-line Sprint.

---

## 8. Open questions for Anas

1. **Sprint sequencing** — Confirmed Sales (2.16.16) lands Thursday 2026-05-21. Do you want **2.16.17 immediately after** (Friday morning while waiting on Confirmed Sales validation) or save it for Saturday? Recommended: Friday — Cloudflare dashboard work (§5) can happen Thursday evening as prep, code Sprint Friday AM.
2. **HSTS preload** — Confirm SKIP per V9 (Cloudflare's HSTS toggle is enough; preload is irreversible).
3. **`THAMMEN_ENABLE_DOCS`** for staging/dev — do you want a persistent staging Heroku app with `=1`, or use local dev only? Cheapest = local-only.
4. **`verify_cloudflare.py` cron** — set up `heroku scheduler` weekly, or run manually after each Sprint? Recommended: weekly cron, $0 cost.

---

*Scouting v2 complete. Empirical baseline measured 2026-05-19 18:16 Doha time. No file in `deploy v2/` source code modified. Only artifact: this document.*
