# CHANGELOG v59 — Sprint A14 · villa cold-503 latency (lever 2: geometric parallelization)

> **Engine:** `thammen-sprint2p22p0a7-villa-geometric-parallel` · **SPRINT_TAG** `2.22.0a.7`
> **Date:** 2026-05-30 · **Type:** performance (Bug A14), **LEVER 2 ONLY** (measure-gated).
> **Files:** `geometric_factors.py` (parallelization), `evaluate_unified.py` (version bump),
> `test_sprint_2p22p0a5_request_budget.py` (R6 pin fix),
> `test_sprint_2p22p0a7_geometric_determinism.py` (new permanent determinism test),
> `CHANGELOG_v59.md`.
> **Status:** committed, **NOT pushed** — held at 🔴 Gate 1 (Rule #32). Production stays
> Heroku v145 (`…a6-seed-getplot-dedup`) until Gate-1 approval.
> **Frozen scope:** BRIEF_BranchB_villa_GIS_latency_v2.md §8 (commit eded5e4).

## 1. Why this matters
A14: the heavy multi-QARS villa path warm-success ≈ **21-22 s** sits just under the Heroku
30 s router wall; cold first-try tips over → **503** (reproduced this sprint: 56/565/21
attempt1 503 @31.1 s; retry 200 @20.7 s). The fix must cut GIS **work**.

## 2. Root cause (measured, §5 recon)
`geometric_factors.analyze_geometric_factors` made ~11 GIS round-trips **serially** (~9 s on
Heroku — the phase-C long pole): `fetch_plot_polygon` → `detect_corner` (a serial loop of up
to 6 edges × {main_roads + local_roads} = up to 12 calls) → `analyze_adjacent_zoning` (HBU) →
`find_named_landmarks`. Only `fetch_plot_polygon` is a true dependency (provides the edges +
centroid); the rest are independent.

## 3. What this patch does — LEVER 2 (perf-only)
`geometric_factors.py`, two levels of parallelism, **same calls / same results / reordered**:
- **Round 0:** `fetch_plot_polygon` (provides edges + centroid).
- **Round 1 (parallel):** `detect_corner` ∥ `analyze_adjacent_zoning` ∥ `find_named_landmarks`
  (3-worker pool); and INSIDE `detect_corner`, the per-edge road probes run concurrently
  (one worker per significant edge).
- Determinism preserved: street aggregation uses sets (union order-independent); `edge_evidence`
  is rebuilt in the ORIGINAL `significant_edges` order; the `'hbu'` key is still set ONLY when
  a zoning hint is present; `copy_context()` carries the request-deadline contextvar into each
  worker (A14 v141 pattern — parallelism can only REDUCE timeout likelihood, never add a drop).

### Lever 1 (overlap geometric with the valuation) — DEFERRED (measure-gate)
H_A held airtight (early-fetched zoning == current `factors_detail` parse across 26 live
points incl. HBU-positive + the E7/A11 stale-subtype anchor; `_factor_zoning` is the sole,
unmutated source — E7 injects a separate response flag, never the factor). Lever 1 is
**cleared as perf-only** but **deferred**: lever 2 projects cold first-try ≈ **24-25 s**
(margin ≈ 5.5 s ≥ the ~5 s bar). Lever 1 stays ready; it ships immediately as the next sprint
**iff** the BINDING post-deploy H_lat shows margin < 5 s or any first-try 503.

### R6 (bundled)
`test_sprint_2p22p0a5_request_budget.py`: the two brittle EXACT-version-pin assertions
(`ENGINE_VERSION == '…2p22p0a5…'` / `SPRINT_TAG == '2.22.0a.5'`) → version-agnostic FORMAT
checks against the live source. Unbreaks the 48/49 (the Sprint-2.19.1 anti-pattern;
RISK_REGISTER R6).

### New permanent regression test
`test_sprint_2p22p0a7_geometric_determinism.py` (promoted from the H_A gate harness): asserts
early-fetched zoning == current parse; **retains an HBU-positive AND an E7/A11 anchor** (per
Anas — HBU-negative R1-in-R1 anchors are blind to the HBU defect). Offline-safe: SKIP (exit 0)
when GIS unreachable, FAIL (exit 1) only on a real divergence.

## 4. Verification — empirical
- **H_det (perf-only proof):** geometric output **byte-identical** serial-vs-parallel
  (self-timing `corner.time_taken_s` excluded — it necessarily differs and is NOT in the
  /api/evaluate response) on villa 56/565/21, compound 51500109, HBU-positive R2. **True**.
- **Collapse (in-process; ratio transfers to Heroku):** geometric serial ~2.0-2.5 s →
  parallel ~0.7 s (×2.5-3.7). Heroku §8 serial ~9 s → projected ~2-3 s (~6-7 s saved).
- **Regression (DoD matrix, `PYTHONIOENCODING=utf-8`):** aggregator **392/392** · security
  **15/15** · surface-honesty **45/45** · broad **50/50** (was 48/49: R6 fix + the new test).
  `test_v2_modules.py` formally excluded (pytest not in requirements / `SKIP_FILES`).
- `py_compile` clean on all modified Python.

## 5. BINDING post-deploy gate (H_lat — do NOT skip; after Gate-1 deploy)
Run cold villa first-try **×2** on 56/565/21 (+ 56/647/6):
- **200 under 30 s, margin ≥ 5 s, ×2 → A14 CLOSED**; lever 1 stays deferred.
- margin < 5 s OR any first-try 503 → **lever 1 ships immediately** (next sprint): implement
  the overlap, run H_det **≥3×** (race-detection), confirm geometric reads the early-resolved
  zoning (never Phase-A-mutated `factors_detail`), `copy_context()` deadline.

## 6. Deployment (Rule #43 — NOT executed; awaiting Gate-1 consent)
```
git subtree push --prefix "deploy v2" heroku master
```
Then the origin backup push is routine (Rule #43). Rollback (#11): redeploy v145 / `releases:rollback`.

## 7. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health   # expect "3.1.0-sprint2.22.0a.7" + engine "…a7-villa-geometric-parallel"
# then the H_lat cold villa x2 (§5 above)
```

## 8. What's NOT in this patch (scope boundary, #38)
- **Lever 1** (overlap) — deferred (measure-gate); H_A-cleared + ready.
- **silent-HBU-drop graceful disclosure** (Bug A15) — separate correctness sprint (Gate 2).
- **~12 ".py" "VPS 4" method-labels** — separate RICS-label pass (Gate 2).
- **No methodology / user-facing output change.** Geometric substance byte-identical; only
  redundant serial wall-time removed.
