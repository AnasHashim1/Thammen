# BRIEF — Sprint "Branch B" · Villa GIS-chain latency (Bug A14, real fix) — v2

> **Type:** Performance refactor (network-call elimination + concurrency), diagnostic-first.
> **Channel:** Implementation → Claude Code, **fresh session** with full §5 audit — NOT a tail-of-session bolt-on (#38 / #50 / #51 / #56).
> **Status:** 🟡 DRAFT v2 — pending Anas sign-off. Gain estimate **provisional** until Phase 0 §3.1 closes the measurement gap (Rule #56).
> **Single-purpose (#38):** bring the villa main-path under the 30s router wall (cold) by reducing GIS *work*. No methodology/output change intended (see §4 parity/determinism gates).
> **Predecessor:** A14 v141 budget fix → neutralised to safe **v142** (`THAMMEN_REQUEST_BUDGET=35`). The budget was a *false lever* for an H2-bound path. prod = v142, safe; villa-cold-503 = pre-sprint baseline.
>
> **v2 folds two Phase-0 findings produced 2026-05-29 (no-deploy, local) — both correct traps in v1. See §0.2.**

---

## §0 · What is established

### §0.1 Audit (Heroku one-off, no deploy, 56/565/21, 3 reps in-process)
Villa total ≈ **21.9s**. Captured main-thread serial GIS = **11 calls, ~8.5s**:

| phase (captured) | count | ms |
|---|---|---|
| `gis.qars_primary` | 3 | ~2.45s |
| `gis.cadastre` | 3 | ~2.30s |
| `gis.geometry_project` (ESRI network round-trip) | 3 | ~2.30s |
| `gis.districts` | 2 | ~1.60s |
| **captured GIS total** | **11** | **~8.5s** |
| **uncaptured remainder** | — | **~13.4s** |

**GIS-bound, not compute-bound — dyno ruled out.** Control: apartments (52/903/90, 61/875/20, Lusail) on the **same Basic CPU** run ~4.5s with ~0.8s compute. Same processor ⟹ compute is trivial ⟹ the 21.9s is network I/O. A faster dyno would not move the bottleneck. (`audit_villa_run.txt` holds the raw run.)

### §0.2 🆕 Phase-0 findings (2026-05-29, local, no deploy) — fold into scope
- **F1 — there is NO local projection library.** `pyproj` / `shapely` are **not installed** (ModuleNotFoundError locally), **not in `requirements.txt`** (= requests, beautifulsoup4, tabulate, fastapi, uvicorn, slowapi), and **no production module imports them.** All geometry is pure-Python (`analyze_polygon_shape`); `_project_4326_to_2932` round-trips the ESRI geometry server **precisely because** no local projection exists. ⟹ **T1 is not "swap in pyproj"** (see §2-T1).
- **F2 — `plot_area_m2` is the WRONG parity target.** In `get_plot`, `plot_area_m2 = float(a.get('PDAREA'))` — area is a **cadastre attribute**, independent of the projection. The projected ring (`ring_2932`) feeds `analyze_polygon_shape` → `convex_hull_ratio` / `aspect_ratio` / `is_rectangular` / `irregularity_warning`, which flow into the **`plot_shape` geometric factor (±adjustment)** and **compound irregularity warnings (#17)**. ⟹ **the T1 parity gate checks SHAPE METRICS + the resulting plot_shape factor, not area** (corrects v1 SC2).

### §0.3 Open measurement gap (Rule #56)
The ~13.4s remainder is **inferred** "mostly uncaptured GIS" (worker-thread `property_factors` layers + raw-urllib zoning x-check + landmarks + multi-QARS spatial), **not measured** — the tracer is thread-local and misses worker threads + raw `urllib` callsites. The captured 8.5s is a **floor**. **Scope and the 22→~10-13s estimate are NOT locked until §3.1 attributes the remainder.** This is the exact A14 failure mode (scoping on an unmeasured path) → Rule #56 forbids repeating it.

---

## §1 · Problem
Villa main-path warm-success ≈ 22-25s across a stack of serial GIS round-trips (~800ms each, Heroku→Qatar). Cold exceeds the 30s router wall → first-try 503. The fix must **reduce GIS work** — neither budget/timeout (A14, false lever) nor dyno (compute isn't the bottleneck) can help.

---

## §2 · Fix targets (ranked by certainty)

**T1 — Eliminate `gis.geometry_project` as a network call (highest-value, cross-platform; risk re-rated up by F1).**
`_project_4326_to_2932` (and `_project_2932_to_4326`) round-trip the ESRI geometry server (~800ms × 3 = 2.3s on this villa, and on **every** `get_plot` platform-wide). Replace with a local WGS84→EPSG:2932 (Qatar National Grid) transform. **Two implementation paths — Phase 0 picks one:**
- **(a) Pure-python Transverse-Mercator for EPSG:2932 — RECOMMENDED.** No new dependency; matches the codebase's existing pure-python geometry style; zero Heroku build risk. Cost: implement the TM forward/inverse with the correct QND95 parameters + any datum handling, validated by the §3.3 parity test.
- **(b) Add `pyproj` to `requirements.txt`.** Simpler code, but introduces a **PROJ binary dependency** → Heroku-24 build risk + slug-size growth; must be build-verified. Fallback only if (a)'s parity proves intractable.
**Gate (revised per F2):** perf-only **iff** the local transform reproduces ESRI's **shape metrics** (`convex_hull_ratio`, `aspect_ratio`, `is_rectangular`, `irregularity_warning`) and the resulting `plot_shape` factor within a tolerance that does not move the geometric adjustment. §3.3 verifies.

**T2 — Parallelize the confirmed-independent serial fetches.**
multi-QARS fetches multiple independent plots (cadastre + geometry) serially — note the captured 3× `qars_primary` / 3× `cadastre` / 3× `geometry_project` = repeated `get_plot`. Parallelize the genuinely-independent ones (proven 2.18.0/2.18.1 BFS pattern: compound 89s→29s). **Scope = whatever §3.2 confirms is (a) independent and (b) not already parallel.**
**Caveats:** `property_factors` is **already** 5-thread parallel — do not re-parallelize. If §3.1 shows MoJ is a serial network chunk, that's cache-warming, not parallelization (separate treatment). Threads must inherit the request-deadline contextvar via `copy_context()` (the A14 v141 pattern).

**Provisional estimate (NOT a commitment):** captured 8.5s parallelized → ~3s, + T1 deletes ~2.3s (this villa) → under the wall; cross-platform T1 also trims every `get_plot`. **Real target set after §3.1.**

---

## §3 · Phase 0 — gates §2 scope (Rule #33 / #56)

- **§3.0 — DONE (2026-05-29, no-deploy):** dependency audit (F1) + projection-consumer trace (F2). Recorded above + Session_Log §19.
- **§3.1 — Decompose the ~13.4s remainder (needs deploy).** Extend the tracer to the uncaptured calls: worker-thread `property_factors` GIS layers (merge per-thread buffers), raw-urllib zoning x-check (`_fetch_zoning_at_point`), landmarks, multi-QARS spatial. Output a phase table summing to ~total. **Until attributed, scope + estimate are not locked (Rule #56).**
- **§3.2 — Independence + existing-parallelism map.** For each serial call: does it depend on a prior call's output? Already on a worker thread? Only genuinely-independent, currently-serial calls are T2 candidates.
- **§3.3 — T1 shape-metric parity test (the F2-corrected gate).** For a sample of plots spanning villa / compound / land / apartment, run `analyze_polygon_shape` on (ESRI-projected ring) vs (candidate local-projected ring); compare `convex_hull_ratio` / `aspect_ratio` / `is_rectangular` / `irregularity_warning` **and** the downstream `plot_shape` factor weight. Parity within tolerance → T1 perf-only. Divergence that moves the geometric adjustment → T1 is Gate 2, stop for sign-off.

**Exit gate:** full phase table + independence map + shape-parity result. Scope + success target chosen against these, then signed.

---

## §4 · Gate classification
- **T2 (parallelize):** perf-only — same calls, same results, different ordering → must be **byte-identical** (determinism test, A14 `copy_context` precedent). No Gate 2 if identical.
- **T1 (local projection):** perf-only **iff §3.3 shape-parity holds.** A transform that shifts shape metrics → moves the `plot_shape` factor → **Gate 2** (sign-off). NOT gated on `plot_area_m2` (F2: PDAREA-derived, unaffected).
- **Core-path concurrency:** reversible (revert = redeploy) but **high blast radius** → full §5 audit + determinism regression before push. **Gate 1 (push) unchanged.**

---

## §5 · Success criteria (provisional; finalized post-§3.1)
- **SC1:** villa 56/565/21 cold-dyno first-try < 30s with margin (target tightened from the §3.1 table, e.g. ≤15s).
- **SC2 (T1 parity, F2-corrected):** shape metrics + `plot_shape` factor weight + `irregularity_warning` identical (within tolerance) candidate-vs-ESRI across sampled villa/compound/land/apartment plots; valuation byte-identical on anchors.
- **SC3 (T2 determinism):** parallelized path byte-identical to serial on 56/565/21, 52/903/90, 69/329/20, 69/255/75.
- **SC4 (regression):** baseline confirmed live from the runner, stays green.
- **SC5 (cross-platform T1):** apartment/other paths also drop by ~the `geometry_project` cost (T1 benefits every `get_plot`).

---

## §6 · Risk & rollback
- Core-path concurrency is the real risk → fresh session + §5 audit + determinism regression, not a bolt-on.
- **Rollback (#11):** last stable = v142 (safe). T1/T2 revertable by redeploy; `THAMMEN_REQUEST_BUDGET=35` stays as the safety floor during rollout.
- **#52 watch:** a latency refactor can unmask methodology bugs (e.g. projection parity). Any output drift = separate bug, not folded in (#38).

---

## §7 · Rule #56 to crystallize (with this sprint)
**"Don't scope or size a fix on an unmeasured / inferred path — measure the dominant cost before committing scope."** Precedent: A14 scoped a budget fix on an *inferred* cause (H1/H3) and shipped a lever that couldn't move the H2-bound reality. This brief's §0.3 remainder is *inferred*; §3.1 must measure it before scope locks. Pairs with #33 (empirical-first), #51 (audit-driven perf loop), #45 (verify before batch). Add to `Operational_Rules.md` when Branch B ships.

---

## Sign-off
- [ ] Anas approves Branch B scope (T1 + T2), fresh session, §5 audit.
- [ ] T1 implementation path: (a) pure-python EPSG:2932 [recommended] vs (b) pyproj — decided after §3.3, or pre-chosen here.
- [ ] Acknowledge estimate is provisional until §3.1 decomposition.
- [ ] Confirm sprint number / tag (A14 real-fix).
