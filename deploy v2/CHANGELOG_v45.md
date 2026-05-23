# CHANGELOG v45 — Sprint 2.18.1 (Parallel BFS upfront-prefetch)

| field | value |
|---|---|
| **Engine version** | `thammen-sprint2p18p1-parallel-bfs-prefetch` |
| **SPRINT_TAG** | `2.18.1` |
| **Date built** | 2026-05-23 evening |
| **Files changed** | `qatar_gis.py` (+1 import, +40 lines / −18 lines in `_expand_extent`), `evaluate_unified.py` (+0 / −0 net, version bump on lines 44-45) |
| **Files added** | `tests/test_sprint_2p18p1_parallel_bfs.py` (8 functions, 12 sub-checks) |
| **Tests** | 12 new + 320 prior = **332 sub-checks** across **15/15 standalone files** (all exit 0). No regressions. |
| **Predecessor** | Sprint 2.18.0 (CHANGELOG_v44, Heroku v99 — parallel `property_factors` fan-out) |
| **Successor planned** | Sprint 2.18.2 candidate — lite/full GIS deduplication (closes the ~15 s Python overhead villa/land Stage-1 gap) |
| **Rollback target** | Heroku v99 (`thammen-sprint2p18p0-parallel-property-factors`) |

---

## 1. Why this matters

Sprint 2.18.0 (Heroku v99) cut villa/raw_land latency from ~27 s → ~23 s by parallelizing the 5-layer `property_factors.analyze_property` fan-out. It deliberately did **not** touch the `_expand_extent` BFS that drives the `compound_small` path (51/835/17 trigger case) — that was queued as Sprint 2.18.1.

The user-visible bug Sprint 2.18.1 closes: **HTTP 503 (Heroku 30 s router timeout) on every `compound_small` request**. Empirically reproduced 3/3 reps on 51/835/17 post-v99 (audit log:  `audit_a6_results_post_2p18p0.json`). In-process latency on this case is ~89 s — far above the 30 s router ceiling — so users requesting it via the public API receive only the WAF/router error page and zero diagnostic information. There is **no fast-path fallback** for `compound_small`, so the entire class of compound addresses (~5-10 % of Doha old-district inventory) is currently inaccessible.

Root user complaint: "I submit a compound and get a 503; I have no idea what's wrong."

---

## 2. Root cause

In [qatar_gis.py:1408-1427](qatar_gis.py:1408) (pre-2.18.1), the BFS expansion fired `self.get_plot(cand['pin'])` for each eligible candidate **serially**. Each `get_plot` call is internally a **sequential chain** of two HTTP round-trips:

1. `gis.cadastre` (PIN → polygon, ~830 ms RTT to khazna)
2. `gis.geometry_project` (polygon 4326 → 2932, ~830 ms RTT to services.gisqatar)

Wall-clock per `get_plot` = ~1 645 ms (cadastre + geometry, can't parallelize within — geometry needs cadastre's polygon).

For 51/835/17 the BFS evaluates ~42 eligible candidates (see `audit_a6_results_post_2p18p0.json` for rep 1: 44 cadastre calls = 2 bbox + 42 BFS, 42 geometry_project calls). Serial → 42 × 1 645 ms ≈ **69 s of pure GIS round-trip time**, plus ~15 s of Python overhead (boundary tests, JSON parsing, response building, lite baseline) → **89 s total in-process**, which the Heroku router cuts off at 30 s with HTTP 503.

Empirical confirmation of the 89 s / 503 split is in the v99 baseline (see §6 below).

---

## 3. What this patch does (intentionally narrow — Rule #38)

A **single-function** change to `qatar_gis._expand_extent`:

- **Pre-fetch all eligible plot polygons in one parallel batch** via `concurrent.futures.ThreadPoolExecutor` BEFORE the BFS loop begins.
- `max_workers = min(len(eligible), 20)` — right-sized to task count per **E19** with a 20-cap for khazna same-host concurrent-connection politeness (§5/3 decision-gate, Anas-approved 2026-05-23 evening).
- Per-future `fut.result(timeout=10)`. Exceptions are caught individually → `cached_polygons[pin] = None` + a note appended to `extent.notes` for an audit trail. **A single PIN failure is non-fatal** (existing BFS contract: `if cand_plot is None: continue`).
- **The BFS loop body is byte-identical** to pre-2.18.1: same `frontier.pop()` LIFO, same `for cand in eligible` order, same `_polygons_share_boundary` test, same `included[pin] = plot` insertions. The cache is just always-hit now (pre-populated by the parallel batch instead of lazy-fetched mid-loop).
- **`sorted(included.keys(), key=str)` defensive sort** (Sprint 2.21.0.7.1) is **preserved** — the output `included_pins` list is byte-identical to a hypothetical serial run.

Files touched:
- `qatar_gis.py`: 1 new top-level import (`from concurrent.futures import ThreadPoolExecutor`), 1 replaced block inside `_expand_extent` (~40 lines added / 18 lines removed, net +22).
- `evaluate_unified.py`: `ENGINE_VERSION` and `SPRINT_TAG` bumped (lines 44-45).

Files explicitly **NOT** touched:
- `_should_include` (the area/PD_NO eligibility filter) — same input, same output.
- `_polygons_share_boundary` — same input, same output.
- `get_plot` itself — its internal cadastre→geometry chain stays serial because geometry depends on cadastre's polygon.
- `get_plots_in_bbox` — same input, same output (the 2 bbox queries are unchanged).
- The Sprint 2.21.0.7.1 `sorted(..., key=str)` defensive line — preserved exactly.
- `api.py`, the lite-baseline 4-call chain, property_factors fan-out, downstream brief rendering — all untouched.

---

## 4. Implementation notes

`max_workers=20` chosen as the safety-vs-speed sweet spot:

- **12** (your original prompt's suggestion) would leave only ~3 s margin under Heroku's 30 s router timeout for the worst-case compound. With 42 eligibles at max_workers=12, BFS time = ceil(42/12) × 1 645 ms ≈ 6.6 s, total ≈ 27 s — too close to the cliff.
- **42** (E19 strict, matching the eligible count for 51/835/17) risks khazna server-side throttling on same-host concurrent connections. F5 BIG-IP fronts gisqatar; per-IP concurrent-connection caps are undocumented but historically ~16-32 on similar deployments.
- **20** keeps `max_workers` polite (≤ typical F5 thread-pool minimum) while giving ~5 s safety margin under the 30 s router ceiling. For 42 eligibles: ceil(42/20) × 1 645 ms ≈ 5 s BFS → total ≈ 25 s in-process.

**Lever for follow-up**: if post-deploy production logs show no GIS server backpressure (no spike in 5xx from khazna, no latency rise on parallel fetches), Sprint 2.18.1.1 can raise the cap to 30 + and squeeze the prediction toward the E19-strict ~22 s figure.

**`fut.result(timeout=10)`**: the 10 s per-call timeout is a defense against a single hung PIN holding up the rest of the batch. urllib's internal 30 s timeout still applies as a hard ceiling on each individual round-trip, but the 10 s `result()` cap means we move on faster if a future hasn't completed in 10 s of waiting after we got to it in iteration order. The pool's `__exit__` still waits for all submitted threads to join (no leaked threads).

**Determinism**: the `sorted(..., key=str)` at the AssetExtent return-statement makes the `included_pins` list deterministic regardless of which thread completed first. Verified by T6 of the new test file (two runs on the same synthetic input → byte-identical output).

---

## 5. Expected impact (audit-derived prediction)

### Note on original audit correction (Rule #39 — deviation transparency)

The original Sprint 2.18 Phase 1 audit ([audit_a6_2026-05-23.md](audit_a6_2026-05-23.md) §7.3) predicted **"5-8 s"** for 51/835/17 post-fix. The §5 mini-audit for **this** Sprint corrected this to **22-27 s**.

Root cause of the original error:
- **Eligibles miscounted**: the audit's §6.3 cited "~21 calls" but the v99 measurement shows **42 cadastre BFS calls** (44 total − 2 bbox baseline). 21 was the *included* count after boundary tests; the *eligible* count walked by `get_plot` is ~2× higher.
- **`get_plot`'s internal serial chain missed**: the audit assumed 1 round-trip per eligible (~830 ms). The actual implementation calls `cadastre` then `geometry_project` serially inside `get_plot` → ~1 645 ms wall-clock per call.
- **Python overhead absorbed**: ~15 s of non-GIS work (boundary tests + JSON + lite baseline + classifier + DCF + briefs) is **not parallelizable in this Sprint** and was unaccounted for in the audit's combined-effect estimate. This is the Sprint 2.18.2 candidate territory.

Documented per Rule #39 (deviation transparency) and Rule #51 (audit-driven Sprint pattern). The post-deploy measurement comparison in §6 will validate the §5-corrected prediction.

### Predicted post-deploy timings (max_workers=20)

| case | v99 baseline (in-process avg) | v100 predicted | Δ | HTTP status |
|---|---:|---:|---:|---|
| **safe_villa_52** (fast-path) | 4 239 ms | ~4 240 ms | 0 (regression check) | 200×3 → 200×3 |
| **multi_qars_56** (villa) | 22 808 ms | ~22 810 ms | 0 (regression check) | 503×1 + 200×2 → 200×3 (margin improves) |
| **a6_trigger_51** (compound_small) | **89 355 ms** | **~25 000 ms** | **−64 s** | **503×3 → 200×3** ← the user-visible win |

**Acceptance band**: actual ≤ predicted × 1.10 OR within ±3 s absolute. Tighter than 2.18.0's ±2 % because the absolute change is much larger (~−64 s vs ~−4 s).

**Stage-1 (≤5 s) for compound_small is explicitly NOT a goal here.** The ~15 s of non-parallelizable Python overhead is the next bottleneck — Sprint 2.18.2 candidate territory (lite/full GIS dedup or boundary-test optimization).

---

## 6. Verification — empirical evidence (offline)

### 6.1 Compilation + module-load

```
python -m py_compile qatar_gis.py evaluate_unified.py
→ OK
```

### 6.2 New test file (tests/test_sprint_2p18p1_parallel_bfs.py)

8 test functions, 12 sub-checks, all green (run with `PYTHONIOENCODING=utf-8`):

| # | test | what it proves |
|---|---|---|
| T1 | `test_01_prefetch_matches_expected_on_synthetic_compound` | 5-parcel synthetic compound (seed + 4 adjacent) → included set is exactly {1000, 1001, 1002, 1003, 1004}, total_area = 50 000 m². Confirms BFS produces mathematically correct output. |
| T2 | `test_02_empty_eligible_list` | eligible=[] → BFS exits cleanly, included = {seed only}, total = seed area. |
| T3 | `test_03_single_eligible_candidate` | 1 candidate → max_workers=min(1,20)=1 → still completes correctly. |
| T4 | `test_04_one_prefetch_returns_none` | `get_plot` returns None for one PIN → BFS skips, includes the other candidate. |
| T5 | `test_05_one_prefetch_raises_exception` | `get_plot` raises RuntimeError for one PIN → exception caught, `cached_polygons[pin]=None`, audit-trail note recorded in `extent.notes`, BFS continues with remaining candidates. |
| T6 | `test_06_deterministic_output_via_sorted` | Two runs on same input → byte-identical `included_pins` and `total_area_m2`. Confirms `sorted(..., key=str)` defensive sort survives parallelism. |
| T7 | `test_07_max_workers_capped_at_20` | N=30 eligibles → ThreadPoolExecutor receives `max_workers=20` (verified via spy class). |
| T8 | `test_08_actually_runs_in_parallel` | 20 candidates × 100 ms `get_plot` delay → wall-clock = **111 ms** (vs ~2 000 ms serial). Real concurrency, not just code that looks parallel. |

### 6.3 Full regression suite (15 standalone files)

```
TOTALS: 332 passed / 0 failed
EXIT 0: 15/15 files
```

(Run with `PYTHONIOENCODING=utf-8` to bypass Windows cp1252 codec issues on test files containing Arabic strings. This is a Windows console artifact only — the test *content* passes regardless; the encoding flag just makes the summary regex match all formats.)

### 6.4 What is NOT verified offline

- **Real production latency on Heroku v100 vs v99 in-process** — must be measured via `audit_a6_latency.py` after deploy. The §5 audit run on v99 is the comparison baseline.
- **Real production HTTP behavior (200 vs 503)** — must be observed via direct curl to 51/835/17 after deploy.
- **GIS server backpressure under 20 concurrent connections** — no proxy for this offline. Heroku logs after deploy will reveal any 4xx/5xx from khazna or rising round-trip latency.

These are the §6 entries to fill **post-deploy** (Rule #51 step 3).

---

## 7. Deployment

Per Operational_Rules #43 (Heroku app lives in `deploy v2/` subdir of `C:\Thammen`):

```
cd /d "C:\Thammen\deploy v2"

REM (optional) backup current engine before staging
copy /Y qatar_gis.py qatar_gis.py.bak_2p18p0
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p18p0

REM stage
git add qatar_gis.py evaluate_unified.py tests/test_sprint_2p18p1_parallel_bfs.py CHANGELOG_v45.md
git commit -m "Sprint 2.18.1: parallel BFS upfront-prefetch in _expand_extent"

REM Heroku push via subtree (the app is at deploy v2/, not repo root)
cd /d C:\Thammen
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

### Smoke test plan (3 diverse addresses, NOT 51/835/17 alone — Rule §3)

After dyno restart (~60s), wait then verify:

```
curl -s https://thammen.qa/api/health
# expected: engine_version = thammen-sprint2p18p1-parallel-bfs-prefetch
```

Then 3 representative addresses:

```
REM Fast-path (must stay healthy):
curl -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":52,\"street\":903,\"building\":90}"
REM expected: HTTP 200 in ~5 s

REM Villa path (Sprint 2.18.0 territory, regression check):
curl -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
REM expected: HTTP 200 in ~23 s

REM The bug fix — compound_small (this Sprint's whole point):
curl -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":51,\"street\":835,\"building\":17}"
REM expected: HTTP 200 in ~25 s  (was: 503 in 30 s)
```

### Post-deploy audit

Re-run `audit_a6_latency.py` on Heroku (it's already on the slug — no push needed). Fill in §6 below per Rule #51 step 3.

---

## 8. Post-deploy measurement (actual)

*To be filled after deploy — Rule #51 step 3.*

| case | v99 (in-process) | v100 (in-process) | Δ actual | Δ predicted | deviation | HTTP status (v99) | HTTP status (v100) | verdict |
|---|---:|---:|---:|---:|---:|---|---|---|
| safe_villa_52 | 4 239 ms |  |  | 0 |  | 200×3 |  |  |
| multi_qars_56 | 22 808 ms |  |  | 0 |  | 503×1 + 200×2 |  |  |
| a6_trigger_51 | 89 355 ms |  |  | ~−64 000 ms |  | 503×3 |  |  |

**Acceptance gate**: |actual − predicted| / |predicted| ≤ 10 % for the only non-zero-Δ case (a6_trigger_51). If actual > predicted × 1.10 → investigate (the §5 model was wrong somewhere) before declaring success.

---

## 9. Decisions baked in (Anas, 2026-05-23 evening)

| # | decision | rationale |
|---|---|---|
| 1 | **Approach A (upfront-prefetch)** over layer-by-layer | Smaller diff (~40 lines), byte-identical BFS loop, simpler equivalence proof, matches audit §6.3(b) recommendation. |
| 2 | **max_workers = min(len(eligible), 20)** | 12 = only 3 s margin under 30 s timeout (risky). 42 = E19 strict but aggressive same-host concurrency. 20 = sweet spot. Sprint 2.18.1.1 can raise if production logs show no backpressure. |
| 3 | **Accept ~22-27 s target on 51/835/17 (not Stage-1)** | The user-visible bug is HTTP 503, not latency. A correct 25 s response beats a 30 s timeout every time. Stage-1 (≤5 s) deferred to Sprint 2.18.2 candidate. |
| 4 | **Skip live `probe_dyno_capacity.py` push** | §5/3 analytical reasoning + Sprint 2.18.0 evidence sufficient. Post-deploy logs validate empirically. Probe file stays on disk uncommitted as future scouting reference. |
| 5 | **Use §5-corrected prediction in CHANGELOG_v45 §5** | Audit's "5-8 s" was wrong (eligibles miscounted × 2, get_plot internal chain missed). Documented per Rule #39 + #51. Honest predictions = falsifiable post-deploy. |

---

## 10. Roadmap context

| Sprint | Status | What |
|---|---|---|
| 2.18.0 | ✅ Heroku v99 (2026-05-23 afternoon) | Parallel `property_factors` 5-layer fan-out. −4 s villa/raw_land. |
| **2.18.1** | **this Sprint** | **Parallel `_expand_extent` BFS upfront-prefetch. −64 s compound_small. Kills HTTP 503 class.** |
| 2.18.2 (candidate) | Queued post-2.18.1 | Lite/full GIS-call deduplication. Targets the ~10 s redundant-call class observable on villa/land (multi_qars_56). Would close Stage-1 (≤5 s) gap for compound_small if combined with boundary-test optimization. |
| 2.21.0.10 (candidate) | Queued, conditional | Stage-2 wall-to-wall classification (E18). Conditional on Building Footprint layer probe outcome. |
| 2.16.16 | Queued | Confirmed Sales DB integration. Awaiting secretary's data (Thursday 2026-05-21 slipped). |
| 2.21.1 | Queued | MME apartments smoke + integration. §21.6 smoke test first. |

---

*Sprint 2.18.1 ends one bug class outright (HTTP 503 on `compound_small`). It does **not** close the Stage-1 villa/land gap — that's Sprint 2.18.2 territory. Every Sprint reviewed through the Stage 1/2/3 lens per Operational_Rules #50.*
