# Phase 0 — QARS reachability probe report

> **Sprint:** 2.22.0a.1 Phase 0 scouting (R-protocol)
> **Date:** 2026-05-27
> **Time-box:** 45 min hard cap (Rule #37 deep-audit tier)
> **Discipline:** Rule #33 (empirical-first), #34 (file-based probes), #36 (cite sample + window), #45 (verify, don't trust prior claims), #46 (audit new path end-to-end)
> **Engine version verified:** `thammen-sprint2p22p0a-content-and-refusal-templates` (Heroku v130 after probe deploy; symptom captured on v???? per Step 0)
> **Anchor PIN:** 52/903/90 (Sprint 2.16.15 timing baseline — **not** 51/835/17 per Bug A6)
> **NO code change in this phase.** Anas signs off the chosen fix path in claude.ai before any qatar_gis.py / api.py / evaluate_unified.py touch.

-----

## Step 0 — Symptom reproduction (production /api/health)

**Sample:** 1 curl GET to `https://thammen.qa/api/health`
**Window:** captured `2026-05-27T15:38:22Z` (single point)

Raw response (verbatim):

```json
{
  "status": "ok",
  "version": "3.1.0-sprint2.22.0a",
  "engine": "unified",
  "engine_version": "thammen-sprint2p22p0a-content-and-refusal-templates",
  "moj_db": {"available": true, "size_mb": 8.2},
  "moj_freshness": {"latest_record": "2025-12-31", "days_old": 147, "tier": "stale", "record_count": 25673},
  "calibration_freshness": {"available": true, "total_cells": 125, "by_confidence": {"fallback": 122, "indicative": 2, "reliable": 1}, "last_updated": "2026-05-20T11:59:25+00:00", "days_old": 7, "stale": false, "outliers_rejected_total": null, "calibratable_listings_seen": null, "outlier_rejection_rate": null},
  "qars_endpoint": {
    "primary_url": "https://khazna.gisqatar.org.qa/fed/rest/services/QARS/QARS_Point/FeatureServer/0/query",
    "primary_count": 0,
    "primary_alive": false,
    "legacy_count": 162201,
    "status": "degraded"
  },
  "modules": {"evaluate_property_v2": true, "evaluate_unified_v3": true},
  "security": {"cors_locked": true, "rate_limit": "10/minute"},
  "timestamp": "2026-05-27T15:38:22.302955"
}
```

**Verdict:** ENGINE_VERSION matches expected `thammen-sprint2p22p0a-content-and-refusal-templates` → dyno is current, not stale. Symptom reproduced as briefed: `primary_alive=false, primary_count=0, legacy_count=162201, status=degraded`.

-----

## Step 1 — Heroku dyno egress IP (single point estimate)

**Probe:** `probe_heroku_egress.py` (calls `api.ipify.org`)
**Sample:** 1 dyno run, 2026-05-27 (post v130 deploy)
**Result:**

```
34.229.166.195
```

**Notes:**
- Owner: AWS us-east-1 (Heroku Common Runtime). Resolves consistently with the Heroku Common Runtime egress pool.
- **Caveat:** this is a single point estimate. Heroku one-off dynos and web dynos do not share a stable allowlist key — IPs rotate per dyno restart, deploy, and scaling event. Treat as "today, this dyno saw IP X"; **do not pass to khazna admins as 'whitelist this IP'**.

-----

## Step 2 — Direct khazna reachability from inside dyno

**Probe:** `smoke_qars_heroku.py`
**Target URL:**
```
https://khazna.gisqatar.org.qa/fed/rest/services/QARS/QARS_Point/FeatureServer/0/query
  ?where=ZONE_NO=52 AND STREET_NO=903 AND BUILDING_NO=90
  &outFields=*&f=json
```
**Sample:** 1 GET, anchor PIN 52/903/90, dyno run 2026-05-27 post v130

**Result (verbatim):**

```
status: 200 elapsed: 0.95 len: 111
sample: b'{"error":{"code":503,"message":"User couldn\'t access this resource \'qars/qars_point.mapserver\'.","details":[]}}'
```

**Verdict — this does NOT match any single row of the decision matrix cleanly:**

| Matrix expectation | Observed |
|---|---|
| 200 + valid JSON <3s → path (c) health-check wrong | HTTP=200, latency=0.95s ✓ |
| 403 / 401 → path (a) + (b) | Network 200, but… |
| timeout / TCP reset → path (a) + (b) | No timeout (0.95s) |
| intermittent → path (c) + (b) | Single sample — not intermittent (yet) |

**Key observation:** the **transport** succeeded (HTTP 200 in <1s — IP not network-blocked), but the **ArcGIS application layer** returned an error envelope:

```json
{"error": {"code": 503, "message": "User couldn't access this resource 'qars/qars_point.mapserver'.", "details": []}}
```

Two diagnostic signals embedded in that message:

1. **Authorization, not absence.** `"User couldn't access this resource"` is ArcGIS-speak for permission denial. The service exists; the requester (this IP / no token) is refused. This is the application-layer analogue of a 403 — but it ships inside an HTTP 200 envelope, which is why our current health-check (presumably status-code-only) reports `primary_alive=false` (correctly) but the system cannot distinguish "ACL revoked" from "endpoint moved" from "transient outage".
2. **`.mapserver` vs `FeatureServer`.** Our URL hits `QARS_Point/FeatureServer/0`; the error references `qars/qars_point.mapserver`. This strongly suggests khazna may have **republished** the service as MapServer (deprecating the FeatureServer slug), OR the ACL was applied to the FeatureServer slug specifically. A separate probe to `/QARS/QARS_Point/MapServer/0/query` would disambiguate — **not run** in this Phase 0 (out of time-box; flag for Phase 1).

**Implication for the decision matrix:** the matrix assumed the failure mode would be network-layer (timeout/4xx). It's actually application-layer (ArcGIS-error-in-200). This matters because:
- A status-code-only health-check sees 200 and could falsely report "alive" if it weren't also counting `features[]`. The current "alive=false" verdict survives only because `primary_count=0` (the existing check is implicitly content-aware via feature count). Good defensive design — but the underlying upstream is genuinely broken, not just mis-checked.

-----

## Step 3 — Legacy endpoint subtype field check

**Probe:** `smoke_qars_legacy_subtype.py`
**Target URL:**
```
https://services.gisqatar.org.qa/server/rest/services/Vector/QARS_Search/MapServer/0/query
  ?where=ZONE_NO=52 AND STREET_NO=903 AND BUILDING_NO=90
  &outFields=*&f=json
```
**Sample:** 1 GET, anchor PIN 52/903/90, dyno run 2026-05-27 post v130

**Result (verbatim):**

```
status: 200 elapsed: 0.98 len: 2493
feature_count: 1
field_names: ['BUILDING_NO', 'BUILDING_NO_SUBTYPE', 'BUILDING_NO_SUFFIX', 'COORD_X',
              'COORD_Y', 'DATE_LUPD', 'ELECTRICITY_NO', 'GLOBALID', 'OBJECTID', 'PIN',
              'PLOT_NO_OLD', 'PLOT_NO_OLD_SUFFIX', 'QARS', 'QTEL_ID', 'STREET_NO',
              'SURVEYED_DATE', 'WATER_NO', 'ZONE_NO']
subtype_like_keys: ['BUILDING_NO_SUBTYPE']
  BUILDING_NO_SUBTYPE = 6
```

**Verdict — Rule #45 vindicated:**

- `BUILDING_NO_SUBTYPE` is **present** on the legacy `services.gisqatar.org.qa` endpoint, full name `BUILDING_NO_SUBTYPE` (no synonym needed).
- Value for 52/903/90 = **6** ("Building with Flats" per Operational_Rules #19).
- All 18 standard QARS fields available, including `SURVEYED_DATE`, `DATE_LUPD`, `PIN`, `QARS` — the schema is identical to what khazna would return.
- Latency = 0.98s (comparable to khazna's 0.95s for the application response).

**Implication:** the 2.22.0a Gate 3 report's claim that legacy lacks `BUILDING_NO_SUBTYPE` is **factually wrong**. The original Sprint 2.16.5 justification for migrating to khazna was *bonus field availability*. That justification was for a window of time when legacy may not have exposed it; legacy now exposes it. **Fallback to legacy retains BUILDING_NO_SUBTYPE** — Sprint 2.16.6 Branch 0 classifier (subtype-aware) does NOT degrade behind a legacy fallback.

-----

## Recommendation

**Combined path (b) + path (a) — path (c) is necessary but not sufficient.**

**Path (b) — fallback to legacy as primary, immediately (Phase 1 candidate):**
Justification:
1. Legacy reachable in ≤1s from Heroku Common Runtime IP (Step 3).
2. Legacy carries `BUILDING_NO_SUBTYPE` (Step 3) — Sprint 2.16.6 classifier behaviour fully preserved.
3. Legacy carries 162,201 features per /api/health — current production proof of stability.
4. No coordination required, no external dependency, no schedule risk. Single-purpose Sprint (Rule #38).

**Path (a) — coordinate with khazna admin (parallel, lower urgency):**
Justification:
1. The Step 2 error message references `qars/qars_point.mapserver` — suggests the service may have been republished or the FeatureServer slug ACL revoked. Needs a human at MoJ/GIS Qatar to confirm.
2. Diagnostic time investment (sending a support ticket, reading reply) is days-to-weeks, not hours; not on critical path while path (b) restores primary capability.
3. Outcome controls our future: if khazna confirms FeatureServer permanent removal, our primary URL constant needs updating; if it's a transient ACL bug, we keep both endpoints and prefer khazna again later.

**Path (c) — health-check correctness (small follow-up, Phase 1 or 1.1):**
Justification:
1. The current health-check works by accident: it counts `features[]` and falls back when count=0. Robust against this specific failure (HTTP 200 + ArcGIS error envelope), but a future-Claude reading the code might miss the implicit content-awareness.
2. Honest fix: parse the response and explicitly check for `data.get('error')` before counting features, so the `status` field can carry a more informative tier (e.g. `upstream_authz_error` vs `upstream_empty`).
3. Necessary but not sufficient — even a perfectly accurate health-check doesn't restore primary capability. **path (b) is the load-bearing fix; path (c) is a small follow-up.**

**Combination ordering (recommended Sprint shape, subject to Anas sign-off in claude.ai):**

| Sprint | Path | Scope | Single-purpose? |
|---|---|---|---|
| 2.22.0a.1 (Phase 1) | (b) | Make legacy the de facto primary; demote khazna to opportunistic / health-only | Yes (one change, one Rule #38-compliant patch) |
| 2.22.0a.2 (follow-up) | (c) | Teach `/api/health` to distinguish upstream error from empty result; emit `upstream_authz_error` tier | Yes |
| 2.22.0a.3 (external) | (a) | Open ticket to khazna admin; defer until reply | Not a code Sprint — operational |

-----

## Sample sizes + windows summary (Rule #36)

| Probe | Sample size | Window | Caveats |
|---|---|---|---|
| Step 0 | 1 curl | 2026-05-27 15:38:22Z | Single point; no time-of-day or load variance captured |
| Step 1 | 1 dyno run | 2026-05-27 post v130 | Single dyno; IP rotates across dyno lifecycle |
| Step 2 | 1 GET / 1 PIN | 2026-05-27 post v130 | Single PIN; intermittency not measured; only FeatureServer slug tested, MapServer slug NOT tested |
| Step 3 | 1 GET / 1 PIN | 2026-05-27 post v130 | Single PIN; legacy schema confirmed for ONE record |

**What was NOT measured (flag for Phase 1 if needed):**
- Intermittency over time (single sample per endpoint)
- `/QARS/QARS_Point/MapServer/0/query` (the slug referenced in the error message)
- Legacy endpoint behaviour under load (162K-feature `where=1=1` count check would stress it)
- Cohort diversity — only one PIN tested; matrix of (PIN type × endpoint) not built
- TLS handshake or DNS resolution timing (not separately measured)

-----

## Probe scripts

Committed in `17885d5` for execution; **to be `git rm`'d in the closing commit of this report** per Rule #38 (throwaway, not production code):

- `probe_heroku_egress.py`
- `smoke_qars_heroku.py`
- `smoke_qars_legacy_subtype.py`

-----

*End of Phase 0. NO code change. Awaiting Anas sign-off on combined-path recommendation in claude.ai before Phase 1.*
