# CHANGELOG v51 — Sprint 2.22.0a.1 — QARS Envelope Fallback (Hotfix)

**Engine version (target):** `thammen-sprint2p22p0a1-qars-envelope-fallback`
**Sprint tag:** `2.22.0a.1`
**Heroku release target:** v132 (current production = v131, code = v130)
**Date opened / closed:** 2026-05-27 (same-day hotfix)
**Pre-Sprint inputs:** [`docs/PHASE0_QARS_REACHABILITY.md`](docs/PHASE0_QARS_REACHABILITY.md)
(empirical probe trio against khazna primary, legacy QARS_Search, and Heroku egress IP).
**Production baseline at entry:** Heroku **v131** (engine
`thammen-sprint2p22p0a-content-and-refusal-templates`, Sprint 2.22.0a).
**Triggered by:** Anas's `/api/health` showing `qars_endpoint.primary_alive=false`
+ live `/api/evaluate` on 52/903/90 returning `asset_type=unknown, pin=None,
qars=None` (silent address-lookup failure across production).

-----

## 0. Slot-numbering check (Rule #39 + #53 precedent)

Slot v51 is the natural next sequential slot — v49 = Sprint 2.21.4 (T3
developer-inventory), v50 = Sprint 2.22.0a (content + refusal templates;
deployed v131). **No drift.**

-----

## 1. Why this matters (the user-visible problem)

Until this Sprint, anyone hitting `https://thammen.qa/api/evaluate` with an
address (zone/street/building) — the primary entry path for villas, lands
under address-mode, and every QARS-resolvable case — got back this:

```json
{ "asset_type": "unknown", "valuation_amount": null,
  "property": { "pin": null, "qars": null, ... } }
```

The engine ran, the HTTP 200 came back, but no PIN was ever resolved, no
QARS was ever attached, no classification could fire, no valuation could
compute. The address tab was **dead in production** — silently. The
secondary PIN tab (Sprint 2.21.0) still worked because it bypasses QARS,
but every Sprint 2.16.x flow that depended on the QARS address layer
(towers, apartment buildings, standalone villas via address) was returning
"unknown" with no diagnostic.

`/api/health` had already been reporting `qars_endpoint.status=degraded`
with `primary_alive=false, primary_count=0` since at least Sprint 2.22.0a
went live, but the existing fallback in `find_property` only triggered on
**Python exceptions**, not on the ArcGIS error envelope that khazna
started returning.

-----

## 2. Root cause

Three independent defects cooperating:

1. **khazna's `QARS_Point` service is inaccessible from our Heroku IP**
   (Phase 0 Step 2, 2026-05-27). Both the FeatureServer slug
   (`/QARS/QARS_Point/FeatureServer/0`) and the MapServer slug
   (`/QARS/QARS_Point/MapServer/0`) return:

   ```http
   HTTP/1.1 200 OK
   Content-Type: application/json
   {"error":{"code":503,"message":"User couldn't access this resource
   'qars/qars_point.mapserver'.","details":[]}}
   ```

   This is ArcGIS Server's app-layer auth refusal pattern — the transport
   succeeds, the body carries the failure. The service metadata endpoint
   (`/QARS/QARS_Point?f=json`) returns `{"error":{"code":400,"message":
   "Invalid URL"}}`, suggesting the service was either renamed or fully
   ACL'd. The service listing at `/QARS?f=json` shows only the
   `LOCATE_QARS_ADDRESS_SYM` geocoder, not the attribute-query
   `QARS_Point` service.

2. **`_http_get_json` returned the envelope as a normal dict** (not an
   exception). Callers computed `res.get('features', [])` → `[]` →
   "address not found" was returned indistinguishably from a legitimate
   not-found.

3. **`find_property`'s exception-based legacy fallback never fired**
   because no exception was raised (defect #2). The polygon-spatial
   companions `_qars_count_in_polygon` and `count_qars_within_polygon`
   (used by Sprint 2.21.0.7 Asset Type Reality Check and Sprint 2.21.0.9
   multi-QARS Stage 1) had **no fallback at all** — they ran against
   khazna only, returning `None` / `[]` on any failure.

Phase 0 Step 3 separately disproved a load-bearing assumption from the
old `qatar_gis.py:91` comment:

> "Kept for diagnostics; current behavior is 'depleted to 14 records'."

Legacy `services.gisqatar.org.qa/Vector/QARS_Search/MapServer/0` is **not
depleted** — it returns 162,201 features (matches `/api/health.legacy_count`)
and exposes the full QARS schema **including `BUILDING_NO_SUBTYPE`**
(verified on PIN 52/903/90 → `BUILDING_NO_SUBTYPE=1`, Sprint 2.16.6 Branch 0
classifier behaviour fully preserved on the fallback path).

-----

## 3. What this patch does

**One single-purpose Sprint** (Rule #38) restoring production by activating
the dormant legacy fallback and extending it to the two polygon-spatial
callsites that had never had one.

### 3.1 New helpers in `qatar_gis.py` (after `_http_get_json`)

```python
class _GISServerError(Exception):
    """Raised when an ArcGIS endpoint returns HTTP 200 + {"error": {...}}."""


def _arcgis_envelope_to_exception(res, source_url=""): ...
def _qars_query(params, timeout=30.0, logger=None): ...
```

- `_arcgis_envelope_to_exception` raises `_GISServerError` when the parsed
  response carries an `error` dict; otherwise no-op. Defensive on non-dict
  inputs.
- `_qars_query` tries `ENDPOINTS['qars']` first, applies envelope detection,
  and on either Python exception OR `_GISServerError` falls back to
  `ENDPOINTS['qars_legacy']`. Re-raises only if the legacy endpoint also
  fails. Logger callback invoked once when fallback fires (caller-supplied
  `self._log` from `QatarGIS`).

### 3.2 Refactored callsites

| Function | Change | Was | Becomes |
|---|---|---|---|
| `find_property` (line 1275) | Replace 3-call try/except cascade with one `_qars_query` call | Manual primary/legacy/no-fallback nesting | Single `_qars_query(params, logger=self._log)` call inside one try/except |
| `_qars_count_in_polygon` (line ~552) | Use `_qars_query` | Direct `_http_get_json(ENDPOINTS['qars'], ...)` — no fallback | `_qars_query(...)` — primary→legacy transparent |
| `count_qars_within_polygon` (line ~598) | Use `_qars_query` | Direct `_http_get_json(ENDPOINTS['qars'], ...)` — no fallback | `_qars_query(...)` — primary→legacy transparent |

The "0-features = legitimate not-found, no fallback" contract from Sprint
2.16.5 is preserved — `_qars_query` only treats *failures* (exception or
envelope) as fallback triggers. A successful response with empty `features`
list is still passed through unchanged.

### 3.3 Comment updates

- `qatar_gis.py:55-73` — KHAZNA_BASE preamble — rewritten to document the
  2026-05-27 access regression, the empirically-confirmed legacy
  reachability, and the `_qars_query` design rationale (auto-restores khazna
  preference when access is granted again).
- `qatar_gis.py:93-104` — ENDPOINTS dict preamble — direct ENDPOINTS['qars']
  access is still safe for `/api/health` independent probes, but new
  callers should prefer `_qars_query`.
- `find_property` inline comment — replaced the "legacy depleted anyway"
  claim (now factually wrong per Phase 0) with the post-2.22.0a.1 reality.

### 3.4 Version + tag bumps

| File | Constant | Was | Becomes |
|---|---|---|---|
| `evaluate_unified.py:44` | `ENGINE_VERSION` | `'thammen-sprint2p22p0a-content-and-refusal-templates'` | `'thammen-sprint2p22p0a1-qars-envelope-fallback'` |
| `evaluate_unified.py:45` | `SPRINT_TAG` | `'2.22.0a'` | `'2.22.0a.1'` |

`/api/health.version` (built from `SPRINT_TAG`) becomes
`"3.1.0-sprint2.22.0a.1"`.

-----

## 4. What this patch does NOT do (scope boundary, Rule #38)

- **Does not enrich the `/api/health` diagnostic.** The current health
  probe correctly reports `primary_alive=false` because `.get("count", 0)`
  on the envelope dict returns `0`. Surfacing `primary_error="ArcGIS
  code=503..."` is a debuggability improvement deferred to a separate
  follow-up (path c in Phase 0 report).
- **Does not contact khazna admins.** Path (a) is operational, not code.
- **Does not change the primary URL constant.** When khazna restores
  access, the existing `_qars_query` will prefer it again automatically —
  no code change needed. This is the design intent.
- **Does not touch `_http_get_json` globally.** Envelope-to-exception is
  applied at the QARS-specific helper, not at the central HTTP layer.
  Other endpoints (cadastre, districts, landuse, zoning, geometry) keep
  their current behaviour — if any of those ever serve envelopes, the
  caller's existing patterns handle them.

-----

## 5. Empirical evidence

Phase 0 probes (committed in `17885d5`, removed in `4c76d3c`) + Phase 1
diagnostic probes (committed in `abe834f`, removed in this Sprint's
final commit):

| Step | Sample | Window | Verdict |
|---|---|---|---|
| 0 — symptom | 1 curl to /api/health | 2026-05-27 15:38 UTC | `primary_alive=false, primary_count=0, legacy_count=162201, status=degraded` — engine v130 (Sprint 2.22.0a) |
| 1 — egress | 1 dyno run | post v130 | `34.229.166.195` (AWS us-east-1); IP rotates per dyno lifecycle |
| 2 — khazna FeatureServer | 1 GET, PIN 52/903/90 | post v130 | HTTP 200 in 0.95s + envelope `{"error":{"code":503,"message":"User couldn't access this resource 'qars/qars_point.mapserver'"}}` |
| 2.1 — khazna MapServer slug | 1 GET, same PIN | post v131 | Same envelope (no URL-fix path) |
| 2.2 — khazna service metadata | 1 GET | post v131 | `{"error":{"code":400,"message":"Invalid URL"}}` — service gone |
| 2.3 — khazna /QARS listing | 1 GET | post v131 | Only `LOCATE_QARS_ADDRESS_SYM` geocoder advertised |
| 3 — legacy attribute query | 1 GET, same PIN | post v130 | HTTP 200 in 0.98s, 1 feature with full schema incl. `BUILDING_NO_SUBTYPE=1`; **Rule #45 vindicated** vs prior Gate 3 claim |
| 4 — legacy polygon spatial | 1 GET, Doha-area rect | post v131 | HTTP 200 in 6.04s, `{"count":2}` — spatial pipe works |
| 5 — production /api/evaluate | 1 POST 52/903/90 | pre-fix | `asset_type=unknown, pin=None, qars=None` confirms silent failure |

Phase 1 isolated tests (`test_sprint_2p22p0a1_qars_envelope_fallback.py`):

```
[1] _arcgis_envelope_to_exception                        9/9
[2] _qars_query primary-first / legacy-fallback         15/15
[3] find_property integration with _qars_query           7/7
[4] _qars_count_in_polygon                               1/1
[5] count_qars_within_polygon                            3/3
[6] Engine version + sprint tag                          2/2
                                                       -------
                                                       37/37 PASS
```

Test cohort design:
- 1a-1e: helper raises on real khazna envelope, no-ops on healthy /
  count-only / non-dict, message carries source url.
- 2a-2g: primary-healthy short-circuits legacy; envelope falls back;
  network exception falls back; both-envelopes raise; both-exceptions
  raise; logger invoked once; logger=None accepted.
- 3a-3c: real `QatarGIS.find_property` constructs proper PropertyLocation
  on legacy fallback path (zone, qars, subtype preserved); returns None
  on both-fail; honours legitimate not-found contract (no second call).
- 4: `_qars_count_in_polygon` returns legacy count after primary envelope.
- 5: `count_qars_within_polygon` returns legacy features with subtype
  preserved.
- 6: ENGINE_VERSION + SPRINT_TAG bumped to the exact target strings.

Regression sweep (this patch, 2026-05-27):

| Suite | Files | Pass |
|---|---|---|
| Root-level `test_*.py` | 21 (incl. this Sprint's new file) | 21/21 ✓ |
| `tests/test_*.py` | 17 | 16/17 (pre-existing pytest block on `test_v2_modules.py`, unchanged from CLAUDE.md baseline) |
| **Total** | **38** | **37/38** (the 1 known-blocker preserved) |

The 7 root-level tests that initially appeared to fail were `charmap`
codec errors against `✓`/`✗` on Windows cp1252 stdout, caused
by the test runner not inheriting `PYTHONIOENCODING=utf-8` into bash
subshells. Confirmed clean by re-running each with the env var inline —
all pass. None of these failures were caused by this patch (the files
are not touched by this Sprint).

-----

## 6. Deployment

```cmd
git add qatar_gis.py evaluate_unified.py CHANGELOG_v51.md test_sprint_2p22p0a1_qars_envelope_fallback.py
git rm probe_khazna_mapserver.py probe_legacy_spatial.py
git commit -m "Sprint 2.22.0a.1: QARS envelope fallback (hotfix)"
git -C "C:\Thammen" subtree push --prefix "deploy v2" heroku master
```

-----

## 7. Verification curl (post-deploy)

```cmd
curl -s https://thammen.qa/api/health
```

Expected: `engine_version: "thammen-sprint2p22p0a1-qars-envelope-fallback"`,
`version: "3.1.0-sprint2.22.0a.1"`, `qars_endpoint.legacy_count > 1000`.
`primary_alive` will remain `false` until khazna access is restored —
that is the operational path (a) from Phase 0, deferred outside this code
Sprint.

```cmd
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":52,\"street\":903,\"building\":90}"
```

Expected: `asset_type != "unknown"`, `property.pin != null`,
`property.qars: "52/903/90"`. This is the canonical regression test the
patch is restoring.

-----

## 8. Rules applied this Sprint

- **Rule #33** (empirical-first): Phase 0 probed before any code reading.
- **Rule #34** (file-based scripts): every probe shipped as a `.py` file.
- **Rule #36** (cite sample + window): every empirical claim above has n + time.
- **Rule #38** (single-purpose Sprint): one patch, one purpose — restore
  production. Health-check enrichment (path c) and khazna ticket (path a)
  are explicitly out of scope.
- **Rule #39** (deviation justification): KICKOFF said "Anas signs off in
  claude.ai before Phase 1." Anas explicitly waived that: "i will not take
  claude ai openion, i trust you." The waiver is documented here.
- **Rule #43** (subtree push from repo root): used for the Phase 0 + Phase
  1 deploys.
- **Rule #45** (verify before claiming): Phase 0 Step 3 disproved the
  Gate 3 claim that legacy lacks `BUILDING_NO_SUBTYPE`.
- **Rule #52** (latency unmasks methodology / inverse): this is the
  mirror case — a *content* failure (envelope-in-200) was masked by the
  HTTP-status-only fallback contract. The fix activates the dormant
  fallback and centralizes envelope detection.

-----

*Sprint 2.22.0a.1 — hotfix for production address-lookup outage. Phase 0
report retained at `docs/PHASE0_QARS_REACHABILITY.md`. Probes removed in
this Sprint's commit per Rule #38.*
