# CHANGELOG v56 — Sprint 2.22.0a.5 · Villa cold-dyno first-try 503 (Bug A14)

> **Engine:** `thammen-sprint2p22p0a5-villa-cold503-budget`
> **api/health:** `3.1.0-sprint2.22.0a.5`
> **Date:** 2026-05-29
> **Type:** Performance / reliability — **perf-only, no success-path output change**
> **Brief:** `BRIEF_2p22p0a5_villa_cold503_A14_v3.md` (Branch A, signed direction)
> **Files changed:** `qatar_gis.py`, `property_factors.py`, `api.py`,
> `evaluate_unified.py` (version bump), `test_sprint_2p22p0a5_request_budget.py` (new),
> `test_sprint_2p22p0a4_disclosure_framing.py` (brittle version-pin relaxed),
> `probe_khazna_latency.py` (new, Phase 0), `smoke_a14_cold503.py` (new).

---

## 1. Why this matters (user-visible problem)

The production **villa main-path** returned a first-try **HTTP 503 at ~22–30s on a
cold dyno**, succeeding only on retry (documented 2026-05-28 on 56/565/21:
503 @30.4s → retry 200 @22.3s). Real villa users hitting the bare-line
Sales-Comparison path shipped in 2.22.0a.4 saw a failure, then a slow success.

## 2. Root cause (measured, Phase 0)

Three hypotheses; Phase 0 (`heroku ps` + static trace + `probe_khazna_latency.py`
+ live `/api/health`) resolved them:

- **H1 — cold-dyno boot — FALSIFIED.** The dyno is **Basic** tier, which **does not
  sleep** (only Eco sleeps). The documented 503 occurred during the v140 post-deploy
  smoke (fresh dyno + cold cache), not idle-wake. ⟹ keep-warm cron was dropped — it
  would have fixed a non-existent problem.
- **H2 — cold in-memory cache — CONFIRMED.** `_MOJ_CACHE` / `_RENT_REF_CACHE`
  (`evaluate_unified.py:508-509`) are per-process dicts that reset on every dyno
  cycle/deploy. Explains the warm/cold halving (9.0s→4.6s). Not itself a 503; it is
  the condition under which H3 bites.
- **H3 — GIS timeout × retry amplification — ROOT CAUSE.** `qatar_gis._http_get_json`
  ran **3 retries at `timeout=30` each + 1/2/4s backoff** ⟹ a single slow GIS round
  ≈ **~97s**; `_qars_query` calls it twice (primary→legacy) ⟹ ≈ **~194s** worst case.
  A single transient network hiccup on **any** GIS call — even with khazna healthy
  (`primary_alive=true`, server-side ~120ms per the probe) — could blow the 30s
  router wall and 503. `property_factors._query_gis` (parallel, fail-soft, 12s) could
  add up to 12s more near the end of the path.

**khazna distribution (probe, Qatar vantage, n=30):** all valid responses
111–233ms, **0% slow-valid**, 0 hard-fails → BIMODAL. khazna has no stable
"slow-but-valid" mass; multi-second latency on Heroku is transient transport, not
server compute. ⟹ bounding the timeout does not sacrifice valid data → **no Gate 2**.

## 3. What this patch does (request-budget, not call-budget)

A single monotonic **per-request I/O deadline** caps the *whole* request's external
GIS work under the 30s wall, instead of trusting each call's own timeout.

- **`qatar_gis.py`** — `set_request_deadline()` / `clear_request_deadline()` /
  `_remaining_budget()` on a `contextvars.ContextVar`. `REQUEST_BUDGET_SECONDS=24`
  (env-tunable `THAMMEN_REQUEST_BUDGET`). `_http_get_json` now uses
  `eff = min(timeout, remaining)`, fails fast when `remaining ≤ 1.5s`, and bounds the
  retry backoff to the remaining budget. **When no deadline is armed
  (`_remaining_budget()` → None), every path behaves exactly as before** (CLI, tests,
  direct callers: identical 3×30s behaviour).
- **`property_factors.py`** — `_query_gis` honours the same budget (lazy import,
  fail-soft `[]`); the 5-way fan-out wraps each `pool.submit` in
  `contextvars.copy_context().run(...)` so the deadline crosses the
  `ThreadPoolExecutor` boundary (it does not propagate by default).
- **`api.py`** — both `/api/evaluate` and `/api/evaluate/details` arm the deadline
  around `evaluate_thammen(...)` and reset it in `finally`. Request-scoped via ASGI
  context, so `/api/health` and other endpoints are never affected.

**Why it is output-neutral on the success path:** the deadline only ever shortens a
call when the request is already heading past the 30s wall (i.e., would 503 anyway).
Early calls (QARS first) keep the full budget, so a valid khazna response that fits
the wall always completes. The legacy QARS fallback that a shortened primary may
reach sooner is the *same* fallback already reachable today whenever primary throws —
no new data source, no new output. A degraded run terminates in the **same clean
refusal that exists today**, just within the wall instead of after a 503.

## 4. Verification — empirical evidence

- **Isolated** `test_sprint_2p22p0a5_request_budget.py`: **17/17 PASS** — budget math;
  no-deadline → full `timeout=30` (unchanged); armed → `min(timeout, remaining)`;
  exhausted budget → fail-fast, urlopen never called; URLError storm under a 4s budget
  finishes in 2.5s (vs legacy ~97s); `_query_gis` fail-soft `[]`; **contextvar crosses
  into all worker threads (0 urlopen under expired budget)**; unarmed fan-out still
  issues its 7 GIS calls.
- **Determinism** `test_sprint_2p18p0_parallel_factors.py`: **11/11 PASS** — factors
  byte-identical, parallelism preserved (202ms < 700ms) after `copy_context`.
- **Full regression: 49/49 standalone test files PASS** (incl. all 2.22.0a* sprints,
  security 2.16.17, hybrid arc) with `PYTHONIOENCODING=utf-8`. The prior-sprint
  2.22.0a.4 engine-version pin was relaxed to forward-compatible (2.19.1 precedent).
- `py_compile` clean on all four modified modules.

## 5. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add qatar_gis.py property_factors.py api.py evaluate_unified.py CHANGELOG_v56.md test_sprint_2p22p0a5_request_budget.py test_sprint_2p22p0a4_disclosure_framing.py probe_khazna_latency.py smoke_a14_cold503.py CLAUDE.md
git commit -m "Sprint 2.22.0a.5: villa cold-dyno first-try 503 (A14) — per-request GIS I/O budget"
git subtree push --prefix "deploy v2" heroku master
```

## 6. Post-deploy verification (Rule #34 / #52 / brief §6)

```
heroku run python smoke_a14_cold503.py            # warm baseline + anchors
heroku ps:restart                                  # force a cold dyno
heroku run python smoke_a14_cold503.py            # first-try cold villa hit
```
SC1: zero first-try 503 on cold 56/565/21 across 3 restarts; all < 30s with margin.
SC2: degraded-QARS → clean refusal within the wall, never 503, never a synthesised
valuation. SC3: output unchanged on 56/565/21, 52/903/90, 69/329/20, 69/255/75.

## 7. What is NOT in this patch (Rule #38 / #42)

- **No keep-warm cron** (H1 falsified — Basic dyno doesn't sleep).
- **No degraded-QARS fail-soft *valuation*** — producing a value when QARS is degraded
  is a new intended output (E3: indicative + mandatory MUC) → **Gate 2**, deferred to a
  dedicated sub-sprint (brief §9), gated on this clean-fail floor being stable.
- **No warm-path optimisation** (Branch B: parallelise sequential GIS, cross-cycle
  cache, DoS ceiling) — deferred pending the Phase 0 cost table.
- **No methodology / copy / valuation change.** Perf-only; success-path output identical.
