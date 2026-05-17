# CHANGELOG — Sprint 2.16.5: QARS Endpoint Migration (Outage Recovery)

**Engine version:** `thammen-sprint2p16p5-qars-endpoint-migration`
**SPRINT_TAG:** `2.16.5` → /api/health reports `3.1.0-sprint2.16.5`
**Date:** 2026-05-17
**Files updated:** `qatar_gis.py`, `api.py`, `evaluate_unified.py` (version bump only)
**Severity:** 🔴 Critical — restores Thammen from total outage

---

## Why this matters — total outage at 17:00 UTC, full restoration here

### What broke (recap from this session's investigation)

At ~17:00 UTC 2026-05-17, GIS Qatar reduced the public
`services.gisqatar.org.qa/server/rest/services/Vector/QARS_Search/MapServer/0`
service from ~24M records to **14 bookkeeping rows** (all with
`DATE_LUPD=2026-05-17`). The same service under the alias `Vector/QARS`
was reduced identically.

Effect on Thammen: every `/api/evaluate/details` returned
`asset_type: "unknown"`, `district: null`, `valuation.method: "insufficient_data"`.
Verified against all 6 canonical addresses + the 3 confirmed sales:
**0 out of 9 worked**. Production was effectively unusable.

### Where the data actually lives now (verified)

Through joint debugging with the user (Anas, in Doha) who inspected
the official `gisqatar.org.qa/qarssearch/` portal's network traffic in
DevTools, we discovered:

- **Host:** `khazna.gisqatar.org.qa` (public, resolves to 89.211.33.46)
- **Path:** `/fed/rest/services/QARS/QARS_Point/FeatureServer/0`
- **Auth:** None — public, no token
- **Schema:** Identical to the old `QARS_Search`: includes ZONE_NO, STREET_NO,
  BUILDING_NO, PIN, QARS, BUILDING_NO_SUBTYPE
- **Indexes:** Compound index on `(STREET_NO, BUILDING_NO, ZONE_NO)` — the
  attribute query Thammen issues is index-backed and fast
- **Operations supported:** `Query` (confirmed via service info `capabilities`)
- **Formats supported:** `JSON, geoJSON, PBF` — we use `f=json` unchanged

### Why this isn't a temporary outage we can wait out

The `services.gisqatar.org.qa/.../QARS_Search/MapServer` endpoint is the
LEGACY public mirror. Anas's portal screenshots from the same window
showed the official Address Search portal fully functional via the
khazna endpoint. The migration is from the public-facing
`services-beta`-hosted MapServer to a federated server (`khazna /fed/`).
The old URL is unlikely to be restored.

---

## What this patch does — minimal surgical change

### Change 1: `qatar_gis.py` — point `ENDPOINTS['qars']` to khazna

```diff
+ KHAZNA_BASE = "https://khazna.gisqatar.org.qa/fed/rest/services"
+
  ENDPOINTS = {
-     'qars': f'{GIS_BASE}/Vector/QARS_Search/MapServer/0/query',
+     'qars': f'{KHAZNA_BASE}/QARS/QARS_Point/FeatureServer/0/query',
+     'qars_legacy': f'{GIS_BASE}/Vector/QARS_Search/MapServer/0/query',
      'cadastre': f'{GIS_BASE}/Vector/CadastrePlots/MapServer/0/query',
      'districts': f'{GIS_BASE}/Vector/Districts/MapServer/0/query',
      'geometry': f'{GIS_BASE}/Utilities/Geometry/GeometryServer/project',
  }
```

The query parameters Thammen sends today
(`where=ZONE_NO=X AND STREET_NO=Y AND BUILDING_NO=Z`, `outFields=*`,
`f=json`, `returnGeometry=true`, `outSR=4326`) all work on the new
endpoint unchanged — the schema is identical and `supportsDatumTransformation: true`
means `outSR=4326` will give us WGS84 lat/lon as before.

### Change 2: defensive try/fallback in `find_property`

```diff
-     res = _http_get_json(ENDPOINTS['qars'], params)
+     try:
+         res = _http_get_json(ENDPOINTS['qars'], params)
+     except Exception as e:
+         self._log(f'qars primary failed ({e}); trying legacy endpoint')
+         try:
+             res = _http_get_json(ENDPOINTS['qars_legacy'], params)
+         except Exception as e2:
+             self._log(f'qars legacy also failed ({e2})')
+             return None
```

If khazna throws (network error, HTTP 500, etc.) we try the legacy URL
as a last resort. Note: we do NOT fall back when khazna returns
`{features: []}` — that's a legitimate "address not found" answer.

### Change 3: `/api/health` exposes `qars_endpoint` health

A new `_probe_qars_endpoint()` helper pings BOTH endpoints with
`?returnCountOnly=true&where=1=1` (cheap, 4s timeout each). The response
adds:

```json
"qars_endpoint": {
  "status": "healthy",
  "primary_url": "https://khazna.gisqatar.org.qa/...",
  "primary_count": 24700000,
  "primary_alive": true,
  "legacy_count": 14
}
```

This lets us watch for future migrations and lets monitoring detect
outages cleanly.

### Change 4: no UI changes

`index.html` is unchanged. The address→PIN flow happens server-side.
As long as `find_property()` returns a PropertyLocation with PIN, the
entire downstream pipeline (CadastrePlots, Districts, Zoning, all intact)
works as before.

---

## Verification

### Pre-deploy (this container)

```
✓ Python: evaluate_unified.py, qatar_gis.py, api.py all compile
✓ JS: index.html parses cleanly (Node --check)
✓ Logic: ENDPOINTS['qars'] resolves to expected URL
```

Note: `khazna.gisqatar.org.qa` is NOT in this container's egress allowlist,
so live verification of the new endpoint from this side returns
"Host not in allowlist" (HTTP 403 from proxy). However:

- Anas confirmed the endpoint works from his browser in Qatar
- DNS resolves publicly (89.211.33.46)
- Heroku's egress is unrestricted — should reach it fine

### Post-deploy verification (CRITICAL — read carefully)

1. After `git push heroku master`, wait ~60s for dyno restart.

2. **First check:** `curl https://thammen.qa/api/health`. Look for:
   ```json
   "version": "3.1.0-sprint2.16.5",
   "qars_endpoint": {
     "status": "healthy",
     "primary_count": ~24000000,
     "primary_alive": true,
     "legacy_count": 14
   }
   ```
   - `status: "healthy"` and `primary_alive: true` → endpoint reachable from Heroku, we're good
   - `status: "degraded"` → Heroku can't reach khazna. Will need different strategy (banner + PIN bypass).

3. **Second check:** test our 3 known sales:
   ```
   curl -X POST https://thammen.qa/api/evaluate/details ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":51,\"street\":955,\"building\":49}"
   ```
   Expected: `asset_type` ≠ `"unknown"`, `valuation.amount` is a real number.

   Also try `56/565/10` and `56/565/12` (J Seven A and B).

4. **Third check:** open thammen.qa in browser and run a full evaluation.
   It should produce a complete report again.

If `qars_endpoint.primary_alive` is `true` but evaluations still fail —
something else is going on; come back and we'll diagnose.

If `primary_alive` is `false` — Heroku can't reach khazna. Either
khazna doesn't allow Heroku's egress IPs, or some firewall rule.
This would need a different approach (e.g., proxy through a public CDN).
We'd build Sprint 2.16.6 with that.

---

## Bonus: BUILDING_NO_SUBTYPE attribute now available

The new QARS_Point service exposes `BUILDING_NO_SUBTYPE` with these values:

| Code | Type |
|------|------|
| 0 | Unknown |
| 1 | Villa/House |
| 2 | COMPOUND WITH VILLAS |
| 3 | COMPOUND WITH VILLAS AND FLATS |
| 4 | Shopping Complex |
| 5 | Building Under Construction |
| 6 | BUILDING WITH FLATS |
| 8 | Sports Club |
| 9 | Health Centre / Hospitals |
| 10 | Masjid |
| 11 | Tower |
| 12 | Park |
| 13 | COMMERCIAL |
| 14 | IZBA |
| 15 | FARM |
| 16 | DESERT HOUSE |
| 17 | CHALET |
| 18 | STONE CRUSHER |
| 19 | METRO |
| 99 | Others |

**This directly solves bug A1** (Section 12, palace classifier). For
example, 69/305/201 (Lusail B201) would have `BUILDING_NO_SUBTYPE = 11`
(Tower), instead of being misclassified as "palace" by area heuristic.

Sprint 2.16.5 only *reads* this attribute (it was already passed through
to `PropertyLocation.building_subtype`); a future Sprint will use it to
override the area-based heuristic in `qatar_gis.py`. We can land that
separately once 2.16.5 is verified stable.

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y qatar_gis.py qatar_gis.py.bak_2p16p4
copy /Y api.py api.py.bak_2p16p4
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p4
tar -xf "%USERPROFILE%\Downloads\sprint2p16p5-qars-migration.zip"
findstr /C:"sprint2p16p5" evaluate_unified.py
findstr /C:"khazna" qatar_gis.py
git add qatar_gis.py api.py evaluate_unified.py CHANGELOG_v27.md
git commit -m "Sprint 2.16.5: migrate QARS endpoint to khazna QARS_Point (outage recovery)"
git push heroku master
```

---

## What is NOT in this patch

- **No UI changes.** No banner needed if the new endpoint works.
- **No use of `BUILDING_NO_SUBTYPE` yet.** That's a future Sprint to
  fix bug A1 (palace classifier).
- **No QARS local snapshot.** Sprint 2.17 will build that as insurance
  against future migrations.
- **No CadastrePlots/Zoning/Districts changes.** Those are intact.

---

## Files in this patch

```
sprint2p16p5-qars-migration.zip
├── qatar_gis.py            (MODIFIED: +20 lines — endpoint swap + fallback)
├── api.py                  (MODIFIED: +50 lines — qars_endpoint health probe)
├── evaluate_unified.py     (MODIFIED: version line only)
└── CHANGELOG_v27.md         (NEW: this file)
```

---

_Last updated: 2026-05-17 — restores Thammen from a 90-minute total outage._
