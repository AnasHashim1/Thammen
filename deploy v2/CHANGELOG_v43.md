# CHANGELOG v43 — Sprint 2.21.0.9: Multi-QARS Detection & Effective Land Area

**Engine version:** `thammen-sprint2p21p0p9-multi-qars-detection`
**Date:** 2026-05-23
**Baseline:** Sprint 2.21.0.7.1 (`thammen-sprint2p21p0p7p1-hotfix-removed`, Heroku v91)
**Type:** Methodology fix — bracket selection now uses **effective land area** (PDAREA / n_QARS) for cadastral parcels carrying multiple QARS-addressed villas. **All new logic gated on `asset_type == 'standalone_villa'`** → compound_large / tower / apartment_building / raw_land / agricultural paths byte-for-byte unchanged (regression-safe).

**Files changed (Phase 1 audit + Phase 2 implementation):**
- `audit_multi_qars.py` — new (Phase 1 standalone probe; Heroku v92 deploy artifact, no engine change)
- `audit_multi_qars_2026-05-23.md` — new (Phase 1 findings)
- `property_geo.py` — `MultiQarsResult` dataclass + `classify_multi_qars()` (pure logic, additive)
- `qatar_gis.py` — `count_qars_within_polygon()` (reverse spatial QARS-in-polygon with full attributes; companion to existing `_qars_count_in_polygon`)
- `evaluate_property.py` — `plot_area_override` parameter, multi-QARS detection injection at the single bracket-selection-feeder line (`plot_area = report.plot.pdarea`), `multi_qars` field on `PropertyEvaluation`
- `evaluate_unified.py` — `override_land_area` parameter threaded to `evaluate_property`; surfaces `output['multi_qars']` at the canonical response root; ENGINE_VERSION bump
- `api.py` — `override_land_area` on both `EvaluateRequest` + `EvaluateDetailsRequest` (Pydantic `gt=0, lt=10_000`, `extra='forbid'` still in place); threaded into both `evaluate_thammen` call sites
- `index.html` — yellow card UI (attached/separate/ambiguous), "قيّم المبنى كاملاً" toggle (attached only), manual override field; `_lastSubmit` + `thammenReEvalOverride` re-eval plumbing
- `tests/test_sprint_2p21p0p9_multi_qars.py` — new (48 isolated checks)
- `CHANGELOG_v43.md` — new

---

## 1. Why this matters

User-submitted address **56/565/21 (Bou Hamour)** had been silently mis-valued for weeks (it was actually a Sprint 2.19.1 smoke address). PIN 56090294 carries **two QARS-addressed villas** (B=19 + B=21) on a single cadastral parcel (PDAREA=900 m²). Pre-Sprint, MoJ bracket-selection used PDAREA=900 → bucket **900-1500** (per `lo <= a < hi`). The correct stratum for one half of a duplex is **400-600**. Wrong stratum → ~30-40% over-valuation of the land component.

**Phase 1 empirical audit (Heroku v92, 10-case cohort):**

| pattern | count | examples |
|---|---:|---|
| ambiguous (15.2m boundary) | 3 | 56/565/21, 56/565/19, 71/739/17 |
| attached (clean duplex) | 3 | PIN 56092231 (9.3m), PIN 56090355 (14.0m) |
| separate | 1 | PIN 51240140 (n=4, 53.6m) |
| standalone | 1 | 52/903/90 |
| handled_by_classifier | 1 | PIN 66030258 (compound_large, PDAREA=59,501) |
| QARS lookup empty (graceful) | 1 | 53/240/12 |

Five of nine distinct polygons carried 2+ QARS → estimated **5-10% prevalence in Doha old-district villas**, magnitude ~30-40% over-valuation per affected parcel.

## 2. Root cause

`evaluate_property.py:1333` binds `plot_area = report.plot.pdarea`. Every downstream MoJ bracket / cap-rate / footprint-estimate / sanity-check call reads `plot_area`. No logic between `full_property_lookup` and bracket selection considered that a single cadastral PIN can host multiple addressed villas.

## 3. What this patch does (precedence: user_override > auto-detected effective > raw PDAREA)

- **`qatar_gis.count_qars_within_polygon`** — reverse spatial QARS-in-polygon (`spatialRel=esriSpatialRelIntersects` to match the production helper at `qatar_gis.py:549`; POST fallback via Rule #48 for many-vertex parcel rings). Returns list of dicts with building_no / zone / street / pin / subtype / lat / lon. Empty list on failure (never raises).
- **`property_geo.classify_multi_qars`** — pure-logic classifier. Decision rules (Anas-approved 2026-05-23, threshold = **18m** not spec's 15m — see §6):
  ```
  PDAREA >= 50,000 AND n_qars <= 1   -> handled_by_classifier (compound_large)
  n_qars >= 6                        -> handled_by_classifier (apartments path)
  n_qars <= 1                        -> standalone
  n_qars == 2 & dist < 18m           -> attached
  n_qars == 2 & 18 <= dist <= 30     -> ambiguous (default: separate)
  n_qars == 2 & dist > 30m           -> separate
  3 <= n_qars <= 5                   -> separate
  ```
  `effective_land_area = pdarea / n_qars` for attached/separate/ambiguous; **no title discount** (Anas, 2026-05-23: "السوق لا يميّز").
- **`evaluate_property.py` injection** at line ~1335 (between `full_property_lookup` and any bracket-selection consumer): gated on `asset_type == 'standalone_villa'`. User override wins → else auto-detected effective area for attached/separate/ambiguous → else raw PDAREA unchanged (standalone / handled_by_classifier). Stores raw PDAREA in `cadastral_plot_area` for API display.
- **API response surface:** `output['multi_qars']` block at canonical root with `detected / type / n_qars / cadastral_area / effective_per_villa / max_gps_distance_m / cohabiting_buildings / split_basis / user_override_applied / user_override_available`. For `type='attached'` only, also `alternative_valuation: {available, scope:'value_whole_structure', would_use_pdarea}` (the "value whole structure" toggle the UI renders).
- **UI** (`index.html`): yellow warning card above valuation; for attached duplexes, a "قيّم المبنى كاملاً ({cadastral_area} م²)" button re-submits with `override_land_area=cadastral_area`; for all types, a manual override field + "إعادة التقييم" button. JS uses `window._lastSubmit` to remember the prior request body for clean re-eval.
- **Structured log line** on every detection: `[multi_qars] pin=… pdarea=… n=… dist=…m type=… effective=… override=False/True`. For later A:B-ratio learning across production traffic — Anas asked this be logged "to tune the 18m threshold against real-world prevalence."

## 4. Decisions baked in (Anas, 2026-05-23)

1. **Threshold = 18m**, not spec's 15m. Phase 1 audit found two unrelated cases (56/565/21 + 71/739/17) at exactly 15.2m → very likely a QARS_Point GPS-labelling artifact. Bumping to 18m absorbs the artifact while preserving the 18-30m ambiguous band.
2. **No title discount.** "السوق لا يميّز" — for buyers, two duplex halves transact at the same per-m² as a same-stratum standalone. Equal-by-count split (PDAREA / n_qars) is the only adjustment.
3. **Case #10 not retried.** 53/240/12 returned 0 QARS_Point features (graceful). Cohort already had 1 clean standalone (52/903/90); extra negative redundancy not worth the heroku run.
4. **PIN 66030258 production curl deferred to Phase 4 smoke.** Audit data (PDAREA=59,501 + n_qars=1 + subtype=2) is sufficient evidence for the carve-out; Phase 4 smoke verifies the live classification path.
5. **Gated on `standalone_villa` only.** Tower / compound_large / apartment_building / raw_land / agricultural paths untouched (Rule #38 single-purpose). Future Sprint can extend to commercial_building if the pattern shows there.
6. **Detection runs inside `evaluate_property` (full pipeline), not in fast paths.** Fast paths trigger for DCF-only assets (tower/compound) or insufficient MoJ data — multi_qars doesn't apply (towers) or isn't urgent (insufficient data → already imprecise). Future v1 follow-up may surface fast-path multi_qars for diagnostic UX.
7. **Deviation from plan: `spatialRel=esriSpatialRelIntersects` not `Contains`.** Matches the production helper `_qars_count_in_polygon` at `qatar_gis.py:549`; same semantic outcome for point-in-polygon queries (Rule #39 deviation documented in `audit_multi_qars.py` docstring).

## 5. Verification — empirical evidence

### Phase 1 audit (Heroku v92, 9 of 10 cases returned useful data)

```
#   PIN          PDAREA   n  maxDistM type                       effM2
1   56090294        900   2     15.2  ambiguous(spec)→attached(18m)  450
2   56090294        900   2     15.2  same as #1                     450
3   56092231        600   2      9.3  attached                       300
4   56092231        600   2      9.3  same as #3                     300
5   56090355        900   2     14.0  attached                       450
6   51240140       2040   4     53.6  separate                       510
7   71380039        692   2     15.2  ambiguous(spec)→attached(18m)  346
8   52200100        467   1      0.0  standalone                     467
9   66030258      59501   1      0.0  handled_by_classifier        59501
10  (53/240/12)     —     —      —    QARS lookup empty (graceful)    —
```

### Phase 3 — Isolated tests (offline, ground-truth-derived)

```
tests/test_sprint_2p21p0p9_multi_qars.py — Sprint 2.21.0.9
  C1*  Bou Hamour 56/565/21 trigger case @15.2m  ............ 6/6 ok
  C2*  PIN 56092231 attached clean @9.3m         ............ 3/3 ok
  C3*  PIN 56090355 attached @14.0m              ............ 3/3 ok
  C4*  PIN 51240140 n=4 separate @53.6m          ............ 3/3 ok
  C5*  PIN 71380039 attached @15.2m              ............ 2/2 ok
  C6*  PIN 66030258 compound_large fallthrough   ............ 2/2 ok
  C7*  52/903/90 standalone negative             ............ 3/3 ok
  C8*  Bracket selection uses effective not pdarea ......... 3/3 ok
  C9*  User override classifier behaviour       ............ 1/1 ok
  C10* Graceful empty/None qars_list             ............ 4/4 ok
  C11* GPS threshold edges (17.9 / 18.1 / 30.5)  ............ 5/5 ok
  C12* attached → alternative_valuation contract ............ 1/1 ok
  C13* separate/ambiguous → no alternative       ............ 2/2 ok
  C14* Rule #40 production-line + Pydantic bounds ........... 10/10 ok
                                                            === 48/48 ===
```

### Full standalone test suite (all sprints, after this patch)

| File | Pass |
|---|---:|
| test_cap_rate_calibrator | 59 |
| test_sprint_2p19p1_polish | 41 |
| test_sprint_2p20_grid | 21 |
| test_sprint_2p21_pin_lands | 21 |
| test_sprint_2p21p0p5_land_polish | 21 |
| test_sprint_2p21p0p7_reality_check | 69 (baseline preserved) |
| **test_sprint_2p21p0p9_multi_qars (NEW)** | **48** |
| **TOTAL** | **280** |

`test_v2_modules.py` requires pytest (not installed) → skipped per CLAUDE.md ongoing convention. `py_compile` clean on all 5 modified backend modules. `node --check`: Node not installed locally → **browser-verify gate post-deploy** (same as Sprint 2.21.0.7).

## 6. Threshold calibration — why 18m

Phase 1 audit had two unrelated cases (Bou Hamour 56/565/21 and Z=71 71/739/17) come out at *exactly* 15.2m. Suspicious for a real measurement; very suggestive of a QARS_Point GPS-labelling convention (each point placed by surveyor at a default offset from parcel centroid).

| threshold | 56/565/21 (15.2m) | 71/739/17 (15.2m) | "value whole structure" toggle |
|---|---|---|---|
| `<15m` (spec as-written) | ambiguous | ambiguous | NO (UX dead-end) |
| **`<18m` (this Sprint)** | **attached** | **attached** | **YES — duplex semantic preserved** |
| `<20m` | attached | attached | yes (same UX as 18m) |

Bracket selection is identical at 18m vs 15m for these PDAREAs (split-by-n is the formula either way). The only behavioural difference is the UI toggle visibility — at 18m the duplex semantic is preserved (user can opt to value the whole structure); at 15m the duplex toggle would be hidden for these cases.

## 7. Deployment

> Awaiting explicit consent (#32). From `C:\Thammen` per #43:
```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

**Rollback target:** Heroku v91 = `thammen-sprint2p21p0p7p1-hotfix-removed` (commit `d2c62fa` is the audit-only push; pre-Sprint code base is `9ed0913` / `395b6b5`). `heroku rollback` to v91 if needed.

**Pre-deploy 6-item checklist (per CLAUDE.md §3):**
1. ✅ `py_compile` clean on all 5 backend modules
2. ⚠️ `node --check`: Node not installed → browser-verify gate post-deploy
3. ⚠️ Mobile viewport 390×844: deferred to browser verify (yellow card uses inline styles only, same pattern as Sprint 2.16.9 / 2.21.0.7 MUC panels which were mobile-verified)
4. ✅ Regression tests: 280/280 standalone suite green
5. ✅ Isolated tests: 48/48 new (covers attached / separate / ambiguous / standalone / handled_by_classifier / threshold edges / graceful failure / production-line)
6. ⏭️ Smoke test 3 diverse addresses from Heroku post-deploy (Phase 4 — Bou Hamour 56/565/21, PIN 66030258, 52/903/90 baseline)

## 8. Verification curl (post-deploy)

```
:: 1. Trigger case — expect multi_qars.detected=true, type=attached, effective_per_villa=450
curl -s -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":56,\"street\":565,\"building\":21}" > out_bh.json
findstr /C:"multi_qars" out_bh.json

:: 2. Compound_large regression — expect multi_qars block ABSENT (handled_by_classifier)
curl -s -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"pin\":\"66030258\"}" > out_cl.json
findstr /C:"compound_large" out_cl.json

:: 3. Standalone negative — expect multi_qars block ABSENT (n=1)
curl -s -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":52,\"street\":903,\"building\":90}" > out_st.json
findstr /C:"sprint2p21p0p9" out_st.json
```

## 9. What's NOT in this patch (explicit scope boundary)

- **Footprint-ratio splitting** — for unequal-size duplexes (one villa 60% of plot, other 40%). Spec deferred to a future Sprint when we have footprint estimates per QARS point.
- **ملحق (annex) detection** — distinguishing a main villa + annex/maid's quarters from a duplex. Spec deferred (subtype=1+1 vs subtype=1+annex needs a separate signal).
- **Title discount deliberately NOT applied** — Anas decision 2026-05-23: "السوق لا يميّز" (market does not distinguish shared-title duplex vs same-stratum standalone). Equal split by count, no further discount.
- **n>=6 → apartments path** — currently emits `handled_by_classifier` but doesn't enrich the apartments flow. Sprint 2.21.1 (MME apartments) owns this.
- **P3 MoJ lstkhdm usage filter** — still parked at Sprint 2.21.0.8 (deferred per CHANGELOG_v42).
- **Fast-path multi_qars surfacing** — when an asset routes through a fast path (DCF-only or insufficient MoJ), the multi_qars panel does NOT render. Acceptable for v1: standalone_villa with sufficient MoJ goes through the full pipeline (the trigger case lives there).
- **Distribution-logging dashboard** — Anas asked we log every detection for later A:B ratio learning. The structured `[multi_qars]` log line is in place; a downstream aggregator/dashboard is a separate effort.

## 10. Distribution logging note

Every detection emits one structured log line at INFO equivalent (raw `print(...)` to stdout, captured by Heroku log drains):

```
[multi_qars] pin=56090294 pdarea=900 n=2 dist=15.2m type=attached effective=450 override=False
```

Fields are positional/colon-separated for easy `grep` + `awk` aggregation. After ~2 weeks of production traffic we should have enough volume to (a) confirm 5-10% prevalence in Doha old districts, (b) compute the real A:B (attached vs separate) ratio for tuning the 18m threshold, and (c) identify any 5th pattern the cohort didn't surface. The 18m threshold itself can then be revisited as a calibration choice rather than an audit-derived guess.
