# CHANGELOG v39 — Sprint 2.20.0: Land Comparable Adjustments Grid (Time-only v1)

**Engine version:** `thammen-sprint2p20p0-time-adjustment-grid`
**Date:** 2026-05-20
**Baseline:** Sprint 2.19.1 (`thammen-sprint2p19p1-polish-and-fixes`, Heroku v78)
**Type:** New RICS Market-Comparison transparency section — **complement, not replace**.

**Files changed:**
- `adjustment_grid.py` — **new** — Adjustment/Comparable/AdjustmentGrid + `build_land_grid` + `weighted_median` (E8)
- `property_geo.py` — **new** — `detect_corner()` direction-aware, **UNWIRED** (future)
- `evaluate_unified.py` — wire land grid (safe-fail) + ENGINE_VERSION/SPRINT_TAG → 2.20.0
- `output_briefs.py` — `build_comparable_grid_section()` (Arabic, audience-aware, E10)
- `index.html` — `case 'comparable_grid'` renderer (mobile card-per-comparable)
- `docs/Empirical_Findings.md` — E8/E9/E10/E11/E12(BLOCKED) + CoV≡|t| note
- `docs/Operational_Rules.md` — Rule #45 (verify data-linking before batch)
- `docs/Project_Instructions.md` — §11 (Sprint 2.20.0)
- `tests/test_sprint_2p20_grid.py` — **new** (≥6 isolated checks)
- audit infra committed: `probe_arady_*.py`, `audit_size_stability.py`, `audit_c_land_coverage.py`

---

## Why this matters

The engine reported a stratified MoJ median for land but never showed the RICS
**comparable adjustments** behind it, and never time-normalised individual sales
to the valuation date. Sprint 2.20 adds an explicit **comparable grid** (a core
RICS Market-Comparison artifact) — transparency the engineer/manager can audit.

This scope is the product of two pre-build audits that each killed a richer plan
**before** any code (§5 discipline):
1. **Villa attributes** — arady `number_of_roads` is flat=1 for villas,
   `land_front_direction` null → no villa adjustment signal → **villa deferred to
   2.20.1**, order flipped to **land-first**.
2. **MoJ self-calibration for corner** — MoJ sales are **not geocoded** (opaque
   `PN…` ref, 0/26,719 numeric) → `detect_corner` can't tag them → corner premium
   has no T1 source → **corner deferred** (E12 BLOCKED).
3. **Size adjustment** — §8 stability scan: within-bracket size→price/m² is too
   weak (median R²≈0.046; 28.4% stable < 40% gate) → **size deferred to 2.20.1**.

Net v1 = **Time adjustment only**, T1 (MoJ), zero methodology caveats.

---

## What this patch does

### Framework (`adjustment_grid.py`)
- `Adjustment` (factor/pct/source/tier/tier_weight/n/confidence/rationale_ar),
  `Comparable` (raw → adjusted via Π(1+pct)), `AdjustmentGrid` (+ `to_dict`).
- `weighted_median` (**E8**; reduces to plain median at a single tier).
- `build_land_grid(comparables, valuation_date, annual_trend_pct, …)`: time-
  normalises each MoJ land comparable to the valuation date using the area's
  annual trend; **E11** gating (reliable n≥20 / indicative 10–19 / <10 → fallback,
  no grid); **E10** sources attribution. **Size/corner supported structurally but
  NOT emitted in v1.**

### Engine (`evaluate_unified.py`)
- For `asset_type ∈ {land, raw_land}`, builds the grid from
  `geo_v2_result['primary']['transactions']` (already resolved; no extra crawl) +
  `moj_reference.compute_trend(..., 'land')`. Attaches `output['comparable_grid']`
  and appends a brief section. **Safe-fail**: any error leaves the response
  exactly as before; the **headline value is never touched**. Latency-neutral
  (no per-request GIS).

### Display (`output_briefs.py` + `index.html`)
- `build_comparable_grid_section`: Arabic; **§16 audience** — valuer/investor =
  full per-comparable detail, buyer/seller = summary, secretary-like = hidden;
  **E10** sources line; UX footer: «علاوة الزاوية والحجم ستُضاف لاحقاً عند توفّر
  بيانات مرتبطة جغرافياً». Frontend renders **mobile card-per-comparable** (no
  horizontal grid; Sprint 2.16.4 lesson).

### Saved-for-future
- `property_geo.detect_corner()` (4/4 validated) committed **unwired**; its 10/10
  gate is **not** required for 2.20. Activates with a PIN-keyed sale source (E12).

---

## Decisions made (logged per Operational_Rules #39)

1. **Corner deferred** — no T1 source (MoJ ungeocoded); arady-only would be T2
   sentiment and bend E1. Revisit under E12 when Confirmed Sales / MME geocoding
   arrives.
2. **Size deferred to 2.20.1** — §8 scan 28.4% stable < 40% (criterion (c)
   CoV<0.5 ≡ (a) |t|>2; (b) R² worse at 8.1%). Robust under all three.
3. **No Rule #44** — subtree-push divergence folded into #43 (anti-sprawl,
   Anas-confirmed); new process rule is **#45** (verify data-linking before batch).
4. **CHANGELOG numbering** — this is **v39** (v38 = Sprint 2.19.1, never reused).

---

## Verification — empirical evidence

- **Coverage:** 100/339 MoJ land cells n≥10 (49 reliable ≥20, 51 indicative) → the
  grid is grid-ready in ~30% of land cells; the rest fall back to stratification.
- **Size-stability scan:** 74 cells n≥15; stable 28.4% (CoV/|t|) / 8.1% (R²);
  median R²≈0.046 → size deferred.
- `py_compile` clean (all modified + new modules). Full standalone suite green.
- New `tests/test_sprint_2p20_grid.py`: time-adjustment correctness, E11 gating,
  fallback, framework-supports-size, E8 weighted_median, audience hiding, and a
  two-layer check exercising the real `evaluate_unified` land path (Rule #40).
- ⚠️ `node --check` could NOT run (Node not installed); index.html JS edit is a
  localized `switch` case + one icon entry, reviewed by hand → **browser-verify on
  a land address (e.g. الوكير) post-deploy** before sign-off.

---

## Deployment

> **Not deployed in this session.** Awaiting explicit consent (Operational_Rules
> #32). When approved, from `C:\Thammen` per #43:

```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

Rollback target (2.19.1) on Heroku = the v78 ref.

## Verification curl

```
curl -s https://thammen.qa/api/health | findstr /C:"sprint2p20p0"
```
Smoke 5 diverse LAND addresses (NOT 51/835/17 — A6); confirm `comparable_grid`
appears with `confidence` + time-normalised comparables, headline unchanged.

## What's NOT in this patch

- Size adjustment (2.20.1) · Corner (E12, future) · Villa/Apartment/Commercial
  grids (2.20.1 / 2.20.2+2.29 / 2.20.3) · arady corner sentiment panel (future
  micro-Sprint) · Mthamen (§20.8).
