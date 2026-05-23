# CHANGELOG v44 — Sprint 2.18.0: Parallel property_factors fan-out

**Engine version:** `thammen-sprint2p18p0-parallel-property-factors`
**Date:** 2026-05-23
**Baseline:** Sprint 2.21.0.9 (`thammen-sprint2p21p0p9-multi-qars-stage1`, Heroku v98 = same engine code as v97)
**Sprint type:** Pure performance — methodology UNCHANGED. Same factors, same
adjustment numbers, same brief output. The only thing that changes is the
**wall-clock latency** of `property_factors.analyze_property` on the villa,
raw-land, and compound paths that exercise it.

> Note on numbering. We're back-filling 2.18.0 (originally reserved in the
> roadmap for "A6 latency + async landmarks + BUA-aware sanity") with the
> first of two surgical fixes that came out of the §5 audit (audit_a6_2026-05-23.md).
> 2.18.1 (`_expand_extent` parallel BFS — kills the HTTP 503 class) follows.

**Files changed:**
- `property_factors.py` — `+ from concurrent.futures import ThreadPoolExecutor`;
  the 5 serial helper calls in `analyze_property` are replaced by a single
  `ThreadPoolExecutor(max_workers=5)` block. Merge order preserved byte-for-byte.
- `evaluate_unified.py` — `ENGINE_VERSION` + `SPRINT_TAG` bump.
- `tests/test_sprint_2p18p0_parallel_factors.py` — new (3 tests, 11 sub-checks):
  functional equivalence, None-handling, and a concurrent-execution proof.
- `CHANGELOG_v44.md` — new.
- `audit_a6_latency.py`, `audit_a6_run.log`, `audit_a6_results.json`,
  `audit_a6_run_baseline2.log`, `audit_a6_results_baseline2.json`,
  `audit_a6_2026-05-23.md` — Phase-1 audit + §5 re-baseline artifacts
  (already on Heroku v98 from the audit deploy; reference here for traceability).

---

## 1. Why this matters

The Phase-1 §5 audit ([audit_a6_2026-05-23.md](audit_a6_2026-05-23.md)) measured
21 in-process runs across 7 diverse addresses and found that **every GIS call to
GIS Qatar costs ~830 ms** (Heroku → Doha RTT + ArcGIS server time), and
`property_factors.analyze_property` issues **5 of those calls strictly serially**
for every villa / raw-land / compound-path request:

```
_factor_zoning              → ~830 ms
_factor_commercial_street   → ~830 ms (one short-circuit internally)
_factor_main_road           → ~830 ms (one short-circuit internally)
_factor_landmarks           → ~830 ms
_factor_permitted_height    → ~830 ms
                              ~~~~~~~~
                              ~4.1 s sequential
```

All five helpers query independent ArcGIS layers at the same `(lat, lon)`. They
share no mutable state (§5/2), they are pure (§5/3), and Python 3.10.11 + urllib
+ `concurrent.futures.ThreadPoolExecutor` are all thread-safe (§5/4). Running
them concurrently collapses the 4.1 s into ~830 ms + ~50 ms overhead ≈ ~880 ms.

## 2. Root cause

`property_factors.py` `analyze_property` (lines 467+) was written before any
of the slow-path latency cases existed. The 5 helper calls were laid out as
sequential `f = _factor_X(...)` then `if f: factors.append(f)` — natural and
readable, but **the only single-process speedup available** on a code path that
has to make 5 network round-trips to the same external service.

## 3. What this patch does (intentionally narrow — Rule #38)

```python
# In property_factors.analyze_property:
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5, thread_name_prefix='factors') as pool:
    fut_zoning     = pool.submit(_factor_zoning,           lat, lon, purpose)
    fut_commercial = pool.submit(_factor_commercial_street, lat, lon, purpose)
    fut_road       = pool.submit(_factor_main_road,         lat, lon, purpose)
    fut_landmarks  = pool.submit(_factor_landmarks,         lat, lon, purpose)
    fut_height     = pool.submit(_factor_permitted_height,  lat, lon)
    zoning_result, commercial_result, road_result, landmark_factors, height_result = (
        fut_zoning.result(), fut_commercial.result(), fut_road.result(),
        fut_landmarks.result(), fut_height.result(),
    )

# Then merge into `factors` in the SAME order as the pre-2.18.0 serial code:
#   zoning → commercial → road → landmarks(list extend) → height
# The missing-zoning Arabic note still fires when zoning returns None.
```

**What is preserved byte-for-byte:**
- The order of entries in the final `factors` list.
- The `raw_adjustment` value (sum is commutative, but `factors[0]` semantics
  are also preserved in case any caller relies on positional access).
- The missing-zoning Arabic note (`'لم يُعثر على تصنيف زوننج — طبقة قد تكون غير متاحة'`).
- Internal short-circuits inside `_factor_commercial_street` (50m → 200m radius
  probe) and `_factor_main_road` (main_roads → local_roads) stay serial — they
  are still data-dependent on the first call returning empty.

**What is NOT in this patch (Rule #38 — saved for follow-up Sprints):**
- `_expand_extent` BFS parallelization in `qatar_gis.py` → **Sprint 2.18.1**.
  This is the fix for the HTTP 503 class on `compound_small` (51/835/17).
- Parallel `districts` + `cadastre` in the lite-baseline path → audit §7.2
  Candidate C; deferred.
- BUA-aware sanity check; lite-vs-full GIS deduplication; caching; the 11.9 s
  landuse outlier investigation — all deferred per the §7.4 audit recommendation
  and Anas's 2026-05-23 approval.

## 4. Implementation notes (Anas-requested anchor for future readers)

**`max_workers=5` is the optimum — not 8, not 12, not "default".** Rationale,
preserved here so a future reader doesn't "bump it for headroom":

- There are exactly **5 independent top-level GIS calls** in `analyze_property`:
  `_factor_zoning`, `_factor_commercial_street`, `_factor_main_road`,
  `_factor_landmarks`, `_factor_permitted_height`. Anything above 5 is an idle
  thread allocation with zero benefit.
- Anas's original Sprint spec suggested `max_workers=8-12` based on generic
  concurrency intuition. The Sprint 2.18.0 §5 mini-audit corrected this:
  **task-count = worker-count is the optimal rule for I/O-bound parallelization
  of fixed task sets.** Worker count > task count buys nothing (Python GIL is
  not the constraint; the constraint is the count of independent network calls).
  Worker count < task count force-serializes some calls — defeats the point.
- **If a future Sprint adds a 6th or 7th independent layer to `analyze_property`,
  `max_workers` must be bumped to match the new task count.** Leave a comment
  near `pool.submit` calls so the next change is obvious.

The 5 helpers' internal calls (e.g. `_factor_commercial_street`'s 50m→200m
probe, `_factor_main_road`'s main→local probe) remain serial and intentionally
so — those are data-dependent short-circuits, not parallel candidates.

## 5. Success criteria (audit-derived; corrected per Anas, 2026-05-23)

This Sprint kills **~14 % of villa / raw-land latency** by removing 4 s of
serial GIS time. It does **NOT** kill the HTTP 503 class — that's Sprint 2.18.1's
deliverable. The 503-class fix needs `_expand_extent` BFS parallelization in
`qatar_gis.py`, which only runs for `compound_small` extent expansion (a
different code path that never enters `property_factors`).

Per-case expected delta vs Baseline-2 (§5/1 mini-audit, in-process):

| case               | path               | B2 baseline avg | expected post-2.18.0 | expected Δ |
|--------------------|--------------------|----------------:|---------------------:|-----------:|
| safe_villa_52      | DCF fast-path     |          4 205 |               4 205 |          0 |
| lusail_apt         | DCF fast-path     |          4 116 |               4 116 |          0 |
| works_a11          | DCF fast-path     |          4 142 |               4 142 |          0 |
| compound_large     | DCF fast-path     |          4 146 |               4 146 |          0 |
| **multi_qars_56**  | full villa path   |         26 760 |              ~23 000 |     ~−4 000 |
| **khor_land**      | full land path    |         25 056 |              ~21 000 |     ~−4 000 |
| **a6_trigger_51**  | compound_small expansion |  92 959 |              ~92 959 | **0 — Sprint 2.18.1's job** |

**HTTP-status criterion:** unchanged from baseline. `a6_trigger_51` will still
return HTTP 503×3 (engine time still ~93 s, well over Heroku's 30 s router
ceiling). `multi_qars_56` will likely still return 503×2 + 200×1 (engine time
drops from ~27 s to ~23 s, which is still right at the wire — one rep may now
fit, but the failure pattern isn't reliably eliminated yet). **Both classes
are killed by Sprint 2.18.1.**

This is the user-visible win:
- Villa / land requests that previously took 25-27 s now take ~21-23 s.
- Fast-path requests are unchanged (already inside ≤5 s).
- The 503 class isn't fixed yet — but no regression on the 200-class either.

## 6. Verification — empirical evidence (offline)

### 6.1 New tests (`tests/test_sprint_2p18p0_parallel_factors.py`)

```
test_01_parallel_returns_same_factors_as_serial   5 sub-checks
  - factor count = 6
  - factor order is byte-identical to pre-2.18.0 serial
  - raw_adjustment correct (sum of stub weights)
  - adjustment == raw_adjustment (cap not hit at 0.025)
  - no spurious missing-zoning note

test_02_parallel_handles_one_helper_returning_None  4 sub-checks
  - only the valid factor present (None returns skipped)
  - missing-zoning note appended when zoning returns None
  - raw_adjustment correct (negative road weight only)
  - adjustment matches raw (no cap)

test_03_helpers_actually_run_concurrently   2 sub-checks
  - wall-clock ~202 ms with 5 stubs × 200 ms sleep each (vs ~1000 ms serial)
  - all 5 factor names present in result
                                              ----
                                              11 sub-checks all pass.
```

The wall-clock proof in T3 is the load-bearing assertion: it demonstrates the
helpers DO run concurrently (not just in a re-arranged sequence).

### 6.2 Full standalone regression (PYTHONIOENCODING=utf-8 forced for Windows)

All 21 test files exit 0:

```
test_building_age_cache              13 (unittest, OK)
test_imagery_flag                     6 (unittest, OK)
test_market_regime                   36 (unittest, OK)
test_material_uncertainty            13 (unittest, OK)
test_scope_of_service                27 (unittest, OK)
test_sprint_2p16p10_tower_split      21
test_sprint_2p16p11_tower_sanity     12
test_sprint_2p16p12_b1_b3            pass (no count printed)
test_sprint_2p16p14_zoning_mismatch  21
test_sprint_2p16p15_extra_forbid     14
test_sprint_2p16p7_validators        22
test_sprint_2p16p8_muc_enrichment     6 (+ helper checks)
test_stock_strata                     6
tests/test_cap_rate_calibrator       59
tests/test_sprint_2p18p0_parallel_factors  11   ← NEW
tests/test_sprint_2p19p1_polish      41
tests/test_sprint_2p20_grid          21
tests/test_sprint_2p21_pin_lands     21
tests/test_sprint_2p21p0p5_land_polish  21
tests/test_sprint_2p21p0p7_reality_check  69
tests/test_sprint_2p21p0p9_multi_qars_stage1  37

TOTAL: 21/21 files pass, 269+ sub-checks (per CHANGELOG_v43 baseline) + 11 new = 280+, zero regressions
```

Note: `tests/test_v2_modules.py`, `tests/test_evaluate.py`, `tests/test_factors.py`,
`tests/test_moj.py` require `pytest` (not installed) → skipped per CLAUDE.md
convention.

### 6.3 Local Windows runner caveat (documentation, not an issue)

Windows `cmd.exe` cp1252 encoding fails when print()ing ✓/✗ symbols used by
several test runners. The workaround is `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`
before invoking the test files. **This is a Windows-only print issue — not a
test failure.** On Heroku (Linux, UTF-8 by default) the issue does not exist.

### 6.4 `py_compile` clean

```
property_factors.py    OK
evaluate_unified.py    OK
audit_a6_latency.py    OK
```

### 6.5 `node --check` on inline JS

⚠️ Node not installed locally. No `index.html` changes in this patch — no JS
modified — so this gate is **not applicable** for 2.18.0.

### 6.6 Mobile viewport 390×844

Not applicable. No frontend changes.

## 7. Deployment

> Awaiting explicit consent per Operational_Rules #32. From `C:\Thammen` per #43:
```
git add deploy v2/property_factors.py
git add deploy v2/evaluate_unified.py
git add deploy v2/tests/test_sprint_2p18p0_parallel_factors.py
git add deploy v2/CHANGELOG_v44.md
git commit -m "Sprint 2.18.0: parallel property_factors fan-out"
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

**Rollback target:** Heroku v98 = `thammen-sprint2p21p0p9-multi-qars-stage1`
(audit probe deploy, engine code identical to v97).
Pre-Sprint commit: `62b4e94`.

Use `heroku rollback` to revert if post-deploy audit shows regression.

### 7.1 Verification curl (post-deploy)

```cmd
:: 1. Engine stamp
curl -s -A "Thammen-Smoke" https://thammen.qa/api/health | findstr /C:"sprint2p18p0"

:: 2. Villa case (multi_qars_56) — expect ~23s in-process, multi_qars block present
curl -s -A "Thammen-Smoke" -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":56,\"street\":565,\"building\":21}" > out_villa.json
findstr /C:"multi_qars" out_villa.json

:: 3. Land case (khor_land) — expect ~21s in-process, raw_land + grid present
curl -s -A "Thammen-Smoke" -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"pin\":\"74328443\"}" > out_land.json

:: 4. Re-run the audit to compare apples-to-apples vs Baseline-2
heroku run --no-tty --app thammen-app-123 python audit_a6_latency.py
```

Expected post-deploy:
- `engine_version` = `thammen-sprint2p18p0-parallel-property-factors`
- `multi_qars_56` in-process ~23 s (vs B2 26.8 s)
- `khor_land` in-process ~21 s (vs B2 25.1 s)
- `a6_trigger_51` in-process ~93 s (unchanged — Sprint 2.18.1 territory)
- HTTP status pattern unchanged from B2 (this Sprint's success ≠ killing 503)

---

## 8. Decisions baked in (Anas, 2026-05-23)

1. **Scope = A + B as two single-purpose Sprints**, not bundled. This is the
   2.18.0 of that pair (just A); 2.18.1 ships B separately. Rule #38.
2. **`max_workers=5`, not 8-12.** Codified in §4 above so future readers don't
   "bump it for headroom".
3. **Ship 2.18 even though villa/land stays at ~22 s.** The user-visible win
   is the 4-second cut; the Stage-1 (≤5 s) compliance target is a separate
   Sprint 2.18.2 candidate (lite/full-path GIS deduplication).
4. **No threshold tuning, no caching, no algorithmic changes.** Pure
   parallelization. Same factors, same numbers, same brief.

---

## 9. Roadmap context

- **Sprint 2.18.0 (this)** — `property_factors` parallel fan-out. Wins ~4 s
  on villa/land/compound_small paths. Does NOT kill 503s.
- **Sprint 2.18.1 (next)** — `_expand_extent` parallel BFS via
  ThreadPoolExecutor. Kills the HTTP 503 class on `compound_small` addresses.
  Audit-derived target: 51/835/17 from ~93 s → ~5–8 s.
- **Sprint 2.18.2 candidate** — lite-path / full-path GIS deduplication
  (the 3 redundant calls per request). Closes the villa/land Stage-1 gap
  (~22 s → ~12 s). Separate Sprint, separate audit, separate scope.
- **Sprint 2.16.16** — Confirmed Sales DB integration (still awaits the
  secretary's data).
- **Sprint 2.21.0.10 candidate** — Building Footprint probe + Stage 2 wall-to-
  wall classification (E18). Conditional on probe outcome.
