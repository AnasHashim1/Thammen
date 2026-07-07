# CHANGELOG v196 — Sprint 2.22.0b.116 «ذاكرة استجابة GIS: إزالة النداءات المكرّرة» (GIS-response dedup cache)

**Engine:** `thammen-sprint2p22p0b116-gis-response-cache` · **SPRINT_TAG** `2.22.0b.116`
**Date:** 2026-07-07 · **Files:** `gis_cache.py` (NEW) + the cache wiring in `qatar_gis.py` · `property_factors.py` · `geometric_factors.py` · `geo_reference_v2.py` (+ the 2 version lines) (+ `test_sprint_2_22_0b116.py`)
**Class:** 🟢 **VALUE-INVARIANT** — a cache that returns the identical response for a repeated URL (same URL → same bytes). The 5-fixture villa byte-gate holds. `api.py` + `index.html` untouched. **The measured actual-latency lever** (b114 removed the compute hotspot; b115 the perceived wait; this removes redundant network round-trips).

---

## 2. Why (the audit — after the parallelization premise was falsified)

The «backend parallelization» sprint's premise was **falsified by the code** (`docs/AUDIT_backend_gis_parallelization.md`): the enrichment trio (`geometric_factors` + `geo_v2` + `listings`) is **already parallel** (`evaluate_unified.py:4473`, "Sprint A.3+"), and `property_factors` (2.18.0) + `_expand_extent` BFS (2.18.1) + `geometric_factors` internals (A14) were already done. There was no safe top-level parallelization left to build.

A URL-spy on one villa eval found the **real** lever: **~10 of 35 GIS calls are EXACT duplicates** — the same QARS_Point / Zoning / Districts / CadastrePlots / Geometry / Commercial query fired 2–3× because `classify` + `property_factors` + `geometric_factors` + `geo_v2` each independently re-query the same layer for the same location. **~29% of the network is redundant.** GIS layer data is static over minutes, so returning the cached response for a repeated URL is **value-invariant** and removes the redundant serial round-trips.

## 3. What this patch does

- **New `gis_cache.py`** — a small, thread-safe, short-TTL (120s) cache keyed on the full request URL (`make_key(url, params)`). It stores the raw response **TEXT**; each cache HIT re-parses it (`json.loads`) into a **FRESH object**, so a caller that mutates its result can never corrupt the cache or another caller → **byte-identical + mutation-safe**. Only successful (non-empty) responses are cached (a transient GIS flake is retried, not stuck). Global (module-level) → dedupes both **in-request across the concurrent enrichment threads** AND **same-area repeats across requests**. Env kill-switch `THAMMEN_GIS_CACHE=0`.
- **Wired into the 4 GIS-fetch sites** (check-cache → return fresh parse on hit; fetch → store text → parse on miss): `qatar_gis._http_get_json` (both the GET + the SSL-fallback return), `property_factors._query_gis`, `geometric_factors._http_get_json`, and `geo_reference_v2`'s 3 district/zoning fetches.

## 4. VALUE-INVARIANT

The cache returns the identical bytes for a repeated URL (GIS layer data is deterministic per URL over the TTL window); each hit is a fresh parse (mutation-safe). No figure/method/rule/leadership touched; `api.py` + `index.html` untouched. The 5-fixture villa byte-gate is byte-identical.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b116.py` **14/14** (`gis_cache`: make_key determinism + param-awareness · put/get roundtrip · miss→None · empties/failures NOT cached · **mutation-safety** (mutating one hit never corrupts the next) · TTL eviction · kill-switch · the 4 modules wired · **the 5-fixture villa byte-gate byte-identical with the cache ON**).
- **Dedup measured (URL-spy, one villa eval):** repeated fetches **10 → 1** (only a single unwired raw-urllib `MapServer/0/query` remains); total GIS network calls **35 → 29**; value **2,400,000 unchanged** (byte-identical cold + warm).
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **170/170 ALL GREEN** · py_compile OK (5 files). **1 R6/Lesson-2 re-point:** `test_sprint_2p22p0a5_request_budget.py` shares one URL across its budget sub-tests, so an earlier success now serves the later ones from cache (a cache hit CORRECTLY bypasses the budget — a free lookup isn't budget-gated) → added a `gis_cache.clear()` in the test's mock-install so each budget sub-test exercises the network/budget path = 17/17. Zero assertion weakened; the production behavior is the intended one.
- **R14 N/A by construction** — `index.html` + `api.py` untouched (backend-only; the served output renders identically — the §20.18 precedent).

## 6. Deployment

- Ritual: `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112). Value-invariant → deploy-on-green after the live 5-fixture byte-gate.

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.116`.
- the 5-fixture villa byte-gate **byte-identical to v278** (value-invariant).
- warm/same-area responses observably lower (the redundant fetches removed; the cache also warms across same-area requests within the TTL).

## 8. What's NOT in this patch

- **The last ~1 in-request dupe** (a raw-urllib `MapServer/0/query` in `qatar_gis` 885/1743 or `property_geo`) — diminishing returns; a follow-up can wire it if measured worth it.
- Cross-request cache tuning (the TTL / max-entries are conservative defaults; a longer TTL would help same-area traffic more but widens the theoretical staleness window — GIS is static, but keep it short).
- The irreducible serial identity chain (find the property before valuing it) + cold-dyno start — inherent to live-GIS valuation; b115's skeleton softens the perceived side.
