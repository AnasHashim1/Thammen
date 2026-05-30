# CHANGELOG v57 — Sprint 2.22.0a.6 · Branch B lever 3 (seed `get_plot` dedup)

> **Engine:** `thammen-sprint2p22p0a6-seed-getplot-dedup` · **SPRINT_TAG** `2.22.0a.6`
> **Date:** 2026-05-30 · **Type:** performance refactor (network-call elimination), **perf-only / byte-identical**
> **Files changed:** `qatar_gis.py` (dedup), `evaluate_unified.py` (version bump),
> `harness_branchB_determinism.py` (lever-3 gate + live HBU-positive), `CHANGELOG_v57.md`,
> `docs/Session_Log.md` (§20.6).
> **Status:** committed, **NOT pushed** — held at 🔴 Gate 1 for Anas PR sign-off.
> **Slug note:** slug corrected 2026-05-30 (Anas) from `…-geometric-seed-dedup` to
> `…-seed-getplot-dedup` — the change is the **seed `get_plot` dedup in the GIS lookup
> path** (`qatar_gis`), a Branch B *lever 3* sub-step, NOT a change to `geometric_factors`.
> SPRINT_TAG `2.22.0a.6` unchanged.

---

## 1. Why this matters

Branch B (Bug A14, villa cold-503) is GIS-**network**-bound (Session_Log §20.1–20.2):
the villa main path makes ~20 sequential GIS round-trips (~830 ms each, Heroku→Qatar),
and cold the chain exceeds the 30 s router wall → first-try 503. The fix must **reduce
GIS work**.

The Phase-0 §5 recon found the engine fetches the **same seed plot twice** on every
address/PIN evaluation: once in `full_property_lookup`, then again inside
`detect_extent`. Each `get_plot` is a CadastrePlots fetch **plus** an ESRI geometry-server
projection round-trip (`_project_4326_to_2932`) — ~1.5 s of pure redundant network on the
critical path. Lever 3 eliminates the second fetch.

## 2. Root cause

`qatar_gis.py`:
- `full_property_lookup` fetches the seed: `plot = self.get_plot(loc.pin)` (~L2066), then
- calls `extent = self.detect_extent(plot.pin)` (~L2085), and
- `detect_extent` **re-fetches the identical pin**: `seed = self.get_plot(seed_pin)` (~L1489).

`get_plot(pin)` = `_http_get_json(cadastre, where=PIN={pin})` + `_project_4326_to_2932(ring)`
(an ESRI geometry-server round-trip). The second call returns byte-identical data
(`get_plot` is deterministic for a given pin — verified live, `get_plot_stable=True`), so
the round-trip is pure waste.

## 3. What this patch does

`detect_extent(self, seed_pin, force_type=None, seed_plot=None)` — **new optional
`seed_plot` param**. When supplied, `detect_extent` reuses it instead of re-fetching:

```python
seed = seed_plot if seed_plot is not None else self.get_plot(seed_pin)
```

`full_property_lookup` passes the plot it already fetched:

```python
extent = self.detect_extent(plot.pin, seed_plot=plot)
```

`seed_plot=None` (the CLI caller at ~L2287, any other caller) keeps **legacy behaviour
byte-for-byte**. Additive, backward-compatible.

### Scope deviation (Rule #39) — `classify_asset` is **NOT** deduped

The signed commit message said "dedup … seed get_plot **+ classify_asset**". The §5 recon
**refuted** the classify_asset half as perf-only:

- `full_property_lookup` calls `classify_asset(plot, location_metadata=_meta, input_mode=…)`
  (subtype-aware Branch 0 + land hint).
- `detect_extent` calls `classify_asset(seed)` — **no metadata, no input_mode** (area
  heuristic).

These can legitimately **diverge** (tower subtypes, land/PIN paths) and drive
`extent.asset_type` / `detection_confidence` / `notes`. Reusing FPL's classification inside
`detect_extent` would be an **output change**, not a perf-only dedup. And re-classifying is
**pure CPU (no network)** — zero perf reason to touch it. ⟹ get_plot dedup only.
*What's lost:* one in-process `classify_asset` call (microseconds). *What Anas needs to
know:* the network win (the get_plot round-trip) is fully captured; the dropped half had no
network cost.

## 4. Verification — empirical evidence

**Determinism gate** (`harness_branchB_determinism.py`, live Qatar GIS):

| PIN | path | byte-identical (old vs new `detect_extent`) | asset_type | included_pins | get_plot_stable |
|---|---|---|---|---|---|
| 56090294 (villa) | single-parcel, no expansion | **True** | standalone_villa | 1 | True |
| 51500109 (compound) | multi-parcel BFS expansion | **True** | compound_large | 5 | True |

`detect_extent(pin)` (old, re-fetches seed) ≡ `detect_extent(pin, seed_plot=get_plot(pin))`
(new, reuses) — byte-identical on both the single-parcel and the multi-parcel-BFS path.
`get_plot_stable=True` confirms `get_plot` is deterministic, so the comparison is clean.

**Regression (all green):**
- aggregator `run_sprint_2p22p0a_suite.py`: **392/392** (MATCH)
- security `test_sprint_2p16p17_security.py`: **15/15**
- `test_sprint_2p22p0a3_surface_honesty.py`: **45/45**
- broad `2p22p0_pre/run_regression_2p22p0a.py`: **49/49 files** (incl. every GIS/extent/
  classify path: 2p18p1 parallel-BFS, 2p18p1p1 compound-misroute, 2p21p0p7 reality-check,
  2p21p0p9 multi-QARS). Baseline was 47/48 files — coverage **grew**, zero failures.

**Compile:** `py_compile qatar_gis.py` + `harness_branchB_determinism.py` OK.

## 5. Expected latency effect (NOT yet measured live)

Eliminates one `get_plot(seed)` per address/PIN evaluation that reaches `detect_extent` =
one CadastrePlots fetch + one ESRI projection round-trip ≈ **~1.5 s** on the villa main
path. **Cross-platform:** benefits every evaluation that classifies+expands, not just the
A14 villa. This is **one lever** — it does not by itself close A14's cold-503 (lever 1, the
`geometric_factors` overlap, is Gate-2-blocked — §8). Post-deploy timing comparison per
Rule #51 is owed once pushed.

## 6. Deployment (Rule #43 — NOT executed; awaiting Gate-1 sign-off)

```
git subtree push --prefix "deploy v2" heroku master
```

Held per 🔴 Gate 1. Rollback target (#11): current prod = Heroku **v144** (≡ v142 behaviour).

## 7. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health
# expect "version":"3.1.0-sprint2.22.0a.6" and engine_version
#        "thammen-sprint2p22p0a6-seed-getplot-dedup"
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" ^
  -d "{\"zone\":56,\"street\":565,\"building\":21}" > out.json
# expect standalone_villa, بو هامور, value unchanged vs v140/v144 (byte-identical engine)
```

## 8. What's NOT in this patch (scope boundary)

- **Lever 1** (overlap `geometric_factors` with the valuation) — **Gate-2-blocked**: it
  drops the HBU `hbu_analysis` for HBU-positive properties (Session_Log §20.4, confirmed
  LIVE). Not touched here.
- **`classify_asset` dedup** — refuted as perf-only (§3 deviation). Not done.
- **Levers 2 / 3-internal** (parallelise `geometric_factors`' 11 serial calls; parallelise
  the multi-QARS `get_plot` rounds) — stretch, deferred.
- **Bug A15** (HBU silently dropped when the zoning hint is absent — reachable today under
  QARS degradation) — separate later sprint; graceful-disclosure fix is **Gate 2**
  (Session_Log §20.5).
- **No methodology / user-facing output change.** Engine output is byte-identical; only
  redundant network is removed.
