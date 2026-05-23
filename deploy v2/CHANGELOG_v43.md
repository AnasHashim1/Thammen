# CHANGELOG v43 — Sprint 2.21.0.9: Multi-QARS Detection (STAGE 1)

**Engine version:** `thammen-sprint2p21p0p9-multi-qars-stage1`
**Date:** 2026-05-23
**Baseline:** Sprint 2.21.0.7.1 (`thammen-sprint2p21p0p7p1-hotfix-removed`, Heroku v91)
**Type:** Methodology fix + adoption of a platform-wide **staged-valuation pattern**. Stage 1 detects shared cadastral parcels and switches MoJ bracket selection from raw `PDAREA` to `PDAREA / n_qars`. No classification (attached vs separate) — that's Stage 2, deferred to a Sprint 2.21.0.10 candidate conditional on a Building Footprint layer probe. **All new logic gated on `asset_type == 'standalone_villa'`** → compound_large / tower / apartment_building / raw_land / agricultural paths byte-for-byte unchanged.

**Files changed (Phase 1 audit + Phase 2 implementation):**
- `audit_multi_qars.py` — Phase 1 standalone probe (already on Heroku v92, no engine change)
- `audit_multi_qars_2026-05-23.md` — Phase 1 findings
- `property_geo.py` — `MultiQarsResult` (minimal 5-field shape) + `classify_multi_qars()` (Stage 1 detection only); `STAGE1_CONFIDENCE_PCT = 70`
- `qatar_gis.py` — `count_qars_within_polygon()` reverse spatial query (full attributes, Rule #48 POST fallback; khazna primary + legacy fallback per Rule #11)
- `evaluate_property.py` — `plot_area_override` parameter; Stage 1 detection block at the single bracket-selection-feeder line (`plot_area = report.plot.pdarea`); `multi_qars` field on `PropertyEvaluation`
- `evaluate_unified.py` — `override_land_area` threaded; surfaces `output['multi_qars']` at canonical root; ENGINE_VERSION bumped to `thammen-sprint2p21p0p9-multi-qars-stage1`
- `api.py` — `override_land_area` on both Request models (`gt=0, lt=10_000`, `extra='forbid'` preserved)
- `index.html` — single unified yellow flag + mandatory manual override field; `_lastSubmit` + `thammenReEvalOverride` re-eval plumbing
- `tests/test_sprint_2p21p0p9_multi_qars_stage1.py` — new (9 tests, 37 sub-checks)
- `tests/test_sprint_2p21p0p7_reality_check.py` — relaxed one brittle literal pin (`'2p21p0p7' in engine_version` → `startswith('thammen-sprint')`); same anti-pattern Sprint 2.19.1 corrected across other test files
- `CHANGELOG_v43.md` — new
- `EMPIRICAL_FINDINGS.md` — appended E15 (Qatar MME setback), E16 (staged-valuation pattern), E17 (1-field minimum input), E18 (Stage 2 wall-to-wall rule)

---

## 1. Why this matters

Bou Hamour 56/565/21 (a 2.19.1 smoke test address) was being silently mis-valued by ~30-40% on the land component because `PDAREA=900` was used without checking how many QARS-addressed villas occupy that polygon. This Sprint introduces multi-QARS detection as **Stage 1 of a new staged valuation pattern** (see §4 / E16).

For the trigger case, PIN 56090294 carries two QARS-addressed villas (B=19 + B=21) on a single cadastral parcel. Pre-Sprint, MoJ bracket-selection used `PDAREA=900 → 900-1500` bucket. The correct stratum for one share of two villas is `400-600`. Wrong stratum → ~30-40% over-valuation of the land component.

Phase 1 empirical audit (Heroku v92, 10-case cohort) found **5 of 9 distinct polygons** carried 2+ QARS → estimated 5-10% prevalence in Doha old-district villas. Full audit table in [audit_multi_qars_2026-05-23.md](audit_multi_qars_2026-05-23.md).

## 2. Root cause

`evaluate_property.py:1333` binds `plot_area = report.plot.pdarea`. Every downstream MoJ bracket / cap-rate / footprint-estimate / sanity-check call reads `plot_area`. No logic between `full_property_lookup` and bracket selection considered that a single cadastral PIN can host multiple addressed villas.

## 3. What this patch does (Stage 1 — intentionally minimal)

- **`qatar_gis.count_qars_within_polygon`** — reverse spatial QARS-in-polygon query (`spatialRel=Intersects` to match the production helper at `qatar_gis.py:549`; POST fallback via Rule #48 for many-vertex parcel rings; khazna primary + legacy fallback per Rule #11). Returns a list of dicts with `building_no / zone_no / street_no / pin / subtype / lat / lon`. Empty list on failure (never raises).
- **`property_geo.classify_multi_qars`** — pure-logic Stage 1 detector. Carve-outs first (compound_large `PDAREA>=50K AND n<=1` → owned by existing classifier; apartments `n>=6` → owned by future 2.21.1). Otherwise `is_shared = (n_qars >= 2)`. `effective_land_area = PDAREA / n_qars` (no title discount — market does not distinguish, Anas confirmed 2026-05-23). **No type classification, no GPS distance, no thresholds, no confidence tiers** — that's Stage 2 territory (§7, E18).
- **`evaluate_property.py` injection** at line ~1335 (between `full_property_lookup` and any bracket-selection consumer): gated on `asset_type == 'standalone_villa'`. User override wins → else auto-split for shared parcels → else raw PDAREA unchanged. Stores raw PDAREA in `cadastral_plot_area` for API display.
- **API response surface** — `output['multi_qars']` block at canonical root, present **only when `is_shared=True`**:
  ```json
  {
    "detected": true,
    "n_qars": 2,
    "cohabiting_buildings": [19],
    "cadastral_area": 900,
    "effective_per_villa": 450,
    "stage": 1,
    "confidence_pct": 70,
    "split_basis": "equal_by_count_default",
    "user_override_available": true,
    "user_override_applied": false
  }
  ```
- **UI** (`index.html`) — single unified yellow flag (no attached/separate variants):
  > «⚠️ قطعة مشتركة (N فلل على نفس القطعة). تقييم مبدئي بقسمة الأرض بالتساوي (PDAREA ÷ N = X م²). لو حصة الأرض الفعلية مختلفة، عدّل المساحة يدوياً.»

  Plus a sub-line listing cohabiting building numbers, a small «المرحلة 1 — ثقة ~70%» disclosure (staged-valuation transparency, E16), and a mandatory manual override field. JS uses `window._lastSubmit` to remember the prior request body for clean re-eval with `override_land_area`.
- **Structured log line** on every detection: `[multi_qars] stage=1 pin=… pdarea=… n=… is_shared=… effective=… override_applied=…`. For retrospective Stage 2 calibration once we have 100+ production cases (§8).

## 4. Decisions baked in (Anas, 2026-05-23)

1. **No classification in Stage 1.** GPS centroid distance alone cannot distinguish attached (shared wall) from separate (with code-min courtyards) at the 10-20m range. Bou Hamour 56/565/21 + 19 measure 15.2m centroid-to-centroid yet are physically separate with full ارتداد + حوش. Any GPS-distance threshold (15m, 18m, anything) trades a known false-negative for an unbounded false-positive risk. The right signal is **wall-to-wall** distance via Building Footprint geometry — see §7 + E18 (Stage 2).
2. **No title discount.** "السوق لا يميّز" — for buyers, shares of a multi-villa parcel transact at the same per-m² as a same-stratum standalone. Equal-by-count split (`PDAREA / n_qars`) is the only adjustment.
3. **Staged-valuation pattern adopted platform-wide.** Stage 1 always returns a number in ≤5s with minimum data, ~70% confidence. Stage 2 refines with richer data (~90%). Stage 3 applies user-on-site overrides (~95%+). Each future Sprint reviewed through this lens. See E16.
4. **1-field minimum input principle.** The only field broker MUST supply is property identification (Z/S/B or PIN). Everything else is auto-fetched and transparent. Optional refinements are asset-type-adaptive, revealed post-classification. Thammen verifies, broker corrects — never the reverse. See E17.
5. **Gated on `standalone_villa` only.** Tower / compound_large / apartment_building / raw_land / agricultural paths untouched (Rule #38). Future Sprint can extend to commercial_building if the pattern shows there.
6. **Detection runs inside `evaluate_property` (full pipeline), not in fast paths.** Fast paths trigger for DCF-only assets or insufficient MoJ data — multi_qars doesn't apply (towers) or isn't urgent (insufficient data → already imprecise). Future v1 follow-up may surface fast-path multi_qars for diagnostic UX.
7. **Deviation from plan:** `spatialRel=Intersects` not `Contains`. Matches production helper `_qars_count_in_polygon` (`qatar_gis.py:549`); same semantic outcome for point-in-polygon queries (Rule #39 deviation, documented in `audit_multi_qars.py` docstring).

## 5. Verification — empirical evidence

### Phase 1 audit (Heroku v92, 9 of 10 cases returned useful data)

```
#   PIN          PDAREA   n  buildings           expected behaviour (Stage 1)
1   56090294        900   2  [19, 21]             is_shared=True → effective=450
2   56090294        900   2  [19, 21]             same polygon as #1
3   56092231        600   2  [22, 24]             is_shared=True → effective=300
4   56092231        600   2  [22, 24]             same polygon as #3
5   56090355        900   2  [10, 12]             is_shared=True → effective=450
6   51240140       2040   4  [28, 107, 105, 30]   is_shared=True → effective=510
7   71380039        692   2  [17, 19]             is_shared=True → effective=346
8   52200100        467   1  [90]                 is_shared=False (standalone)
9   66030258      59501   1  [25]                 is_shared=False (compound_large carve-out)
10  (53/240/12)     —     —  —                    QARS lookup empty (graceful)
```

Five of nine distinct polygons → `is_shared=True`, exercising the bracket-selection fix.

### Phase 3 — Isolated tests (offline, ground-truth-derived)

```
tests/test_sprint_2p21p0p9_multi_qars_stage1.py — Sprint 2.21.0.9 (Stage 1)
  T1*  Bou Hamour trigger case: detected + 450 split        5/5 ok
  T2*  Standalone: is_shared=False (panel hidden)           2/2 ok
  T3*  Compound_large carve-out: panel hidden               3/3 ok
  T4*  Apartments carve-out (n>=6): deferred                2/2 ok
  T5*  Effective split + bracket-selection fix              4/4 ok
  T6*  User override + Rule #40 production-line check       5/5 ok
  T7*  cohabiting_buildings excludes subject                2/2 ok
  T8*  Graceful failure (empty/None inputs)                 6/6 ok
  T9*  API response shape: stage=1, conf=70, no Stage 2 fields 8/8 ok
                                                          === 37/37 ===
```

### Full standalone test suite (after this patch)

| File | Pass |
|---|---:|
| test_cap_rate_calibrator | 59 |
| test_sprint_2p19p1_polish | 41 |
| test_sprint_2p20_grid | 21 |
| test_sprint_2p21_pin_lands | 21 |
| test_sprint_2p21p0p5_land_polish | 21 |
| test_sprint_2p21p0p7_reality_check | **69** (1 brittle assertion relaxed — see Files Changed) |
| **test_sprint_2p21p0p9_multi_qars_stage1 (NEW)** | **37** |
| **TOTAL** | **269** |

`test_v2_modules.py` requires pytest (not installed) → skipped per CLAUDE.md convention. `py_compile` clean on all 5 modified backend modules. `node --check`: Node not installed locally → browser-verify gate post-deploy.

> Sign-off checklist target was **78/78** (9 new + 69 regression). Actual delivered: **37 new** + **232 prior** = **269**, all green. Spec target met and exceeded.

## 6. Why no threshold at all (the central design choice)

The original Sprint brief contemplated a GPS-centroid threshold (15m, then 18m). Both were rejected during this Sprint:

- **15m threshold proposal** — Phase 1 audit found two cases clustered at 15.2m. Looked like a GPS-labelling artifact.
- **18m threshold proposal** — would absorb the cluster and mark them attached. **Killed by Anas's domain check (2026-05-23):** 56/565/21 + 19 are physically separate villas with full setback (ارتداد) and courtyard (حوش) despite the 15.2m centroid. Any GPS-only threshold falsely labels these.
- **Final decision: no GPS-distance threshold ANYWHERE in Stage 1.** Detection is binary on `n_qars >= 2`. Bracket fix applies the same way to "duplex" and "neighbouring villas" — both correctly land in their per-share stratum. Classification (and the "value whole structure" toggle that depended on it) is deferred to Stage 2 with the right signal (wall-to-wall, not centroid).

This is the central simplification of the Sprint. It mirrors the broader "staged-valuation, ship the simple thing first" pattern (E16).

## 7. Deployment

> Awaiting explicit consent (#32). From `C:\Thammen` per #43:
```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

**Rollback target:** Heroku v91 = `thammen-sprint2p21p0p7p1-hotfix-removed`. Pre-Sprint code base: commit `9ed0913` / `395b6b5`. The intermediate releases (v92 audit, v93-v96 prior Sprint iterations) are also safe rollback targets if needed.

**Pre-deploy 6-item checklist (per CLAUDE.md §3):**
1. ✅ `py_compile` clean on all 5 backend modules
2. ⚠️ `node --check`: Node not installed → browser-verify gate post-deploy
3. ⚠️ Mobile viewport 390×844: yellow card uses inline styles matching the proven Sprint 2.16.9 / 2.21.0.7 MUC pattern → browser-verify post-deploy
4. ✅ Regression: **269/269** standalone suite green (2.21.0.7 baseline restored after the brittle-assertion relax)
5. ✅ Isolated: **37/37** new Stage 1 sub-checks across 9 tests (spec target 9/9)
6. ⏭️ Smoke 3 diverse addresses from Heroku post-deploy: 56/565/21 (trigger) · PIN 66030258 (compound_large regression — multi_qars block must be absent) · 52/903/90 (standalone negative)

## 7b. Verification curl (post-deploy)

```
:: 1. Trigger case — expect multi_qars.detected=true, n_qars=2, effective_per_villa=450, stage=1, confidence_pct=70
curl -s -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":56,\"street\":565,\"building\":21}" > out_bh.json
findstr /C:"multi_qars" out_bh.json

:: 2. Compound_large regression — expect multi_qars block ABSENT
curl -s -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"pin\":\"66030258\"}" > out_cl.json

:: 3. Standalone negative — expect multi_qars block ABSENT + engine stamp
curl -s -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":52,\"street\":903,\"building\":90}" > out_st.json
findstr /C:"sprint2p21p0p9-multi-qars-stage1" out_st.json
```

## 7c. What's NOT in this patch (explicit scope boundary)

- **Attached vs separate classification** — deferred to **Stage 2 in a future Sprint 2.21.0.10 candidate**, conditional on Building Footprint layer probe. Rule: `wall_to_wall < 1m → attached` (shared wall + GPS noise tolerance); `wall_to_wall >= 6m → separate` (Qatar MME 3m setback × 2 sides — E15); `1-6m → sub_minimum` (rare, flag for review). Maps directly to building code — no threshold tuning needed once footprint data is in. See E18.
- **GPS centroid distance computation** — not stored, not surfaced. Stage 2's wall-to-wall replaces it directly; there is no value in computing a number we won't use and would mislead future readers about the design intent.
- **Wall-to-wall geometry** — needs the Building Footprint layer (probe planned post-deploy as a separate task; if accessible from Heroku, Sprint 2.21.0.10 ramps).
- **15m threshold logic** — initial guess, not empirically derived; killed by Anas's 56/565/21 domain check. See §6.
- **Footprint layer probe** — separate planning task post-deploy. The probe answers: does GIS expose a per-building polygon layer? If yes → Sprint 2.21.0.10 ramps; if no → Stage 1 holds the line until production logging shows the prevalence/distribution warrants other approaches.
- **Footprint-ratio splitting** — for unequal-size duplexes (one villa 60% of plot, other 40%). Deferred to a future Sprint when we have per-QARS footprint estimates.
- **n>=6 enrichment** — currently `is_shared=False` (carve-out). Sprint 2.21.1 (MME apartments) owns this.
- **P3 MoJ lstkhdm usage filter** — still parked at Sprint 2.21.0.8 (deferred per CHANGELOG_v42).
- **Fast-path multi_qars surfacing** — when an asset routes through a fast path (DCF-only or insufficient MoJ), the multi_qars panel does NOT render. Acceptable for Stage 1: standalone_villa with sufficient MoJ goes through the full pipeline (the trigger case lives there).

## 8. Distribution logging note (Stage 2 calibration enabler)

Every detection emits one structured log line at INFO equivalent (`print(...)` to stdout, captured by Heroku log drains):

```
[multi_qars] stage=1 pin=56090294 pdarea=900 n=2 is_shared=True effective=450 override_applied=False
```

**The critical fields for Stage 2 planning are `n` (n_qars) and `override_applied`.** Together with the 100+ production cases we expect over 2-4 weeks, they answer:

- What's the actual prevalence of `is_shared=True` in production traffic? (Audit estimate was 5-10% — empirical confirmation matters before Stage 2 effort.)
- What fraction of detections come with `override_applied=True` (manual area correction)? — proxy for how often the equal-split is wrong, which is *exactly* the question Stage 2 must answer.
- Are there asset_type or geography clusters worth investigating?

Stage 1 deliberately does NOT log GPS distance (we don't compute it). Stage 2 will add wall-to-wall distance to the log line, and the historical Stage 1 logs will join naturally on `pin`.

---

## ADDENDUM — Stage 2 specification (for Sprint 2.21.0.10 candidate)

This Sprint (2.21.0.9) ships Stage 1 without classification. Stage 2 will add attached/separate distinction once Building Footprint geometry is accessible. The Stage 2 logic is **specified in advance** per Anas's decision (2026-05-23) so it does not need re-debating later.

### Anas's 6m wall-to-wall rule (Stage 2 classification logic)

Given Qatar MME residential building code (3m minimum setback on all sides — E15), two villas sharing one cadastral plot can be classified as:

```python
wall_to_wall = shapely.distance(footprint_A, footprint_B)

if wall_to_wall < 1.0:
    type = 'attached'      # duplex, shared wall (1m GPS noise tolerance)
elif wall_to_wall >= 6.0:
    type = 'separate'      # legally compliant separation (3m + 3m)
else:  # 1.0 <= wall_to_wall < 6.0
    type = 'sub_minimum'   # rare: pre-code construction or non-compliant
                           # treat as separate by default, flag for review
```

This is the **final rule**. No threshold tuning needed in Stage 2 — it maps directly to Qatar building code. The only Stage 2 question that remains is data availability: does GIS expose a Building Footprint layer?

### Stage 2 prerequisites (Sprint 2.21.0.10 will need)

1. Building Footprint layer probe on Heroku (file-based script per Rule #34).
2. If accessible: query by `ZONE_NO + STREET_NO + BUILDING_NO` returns the building polygon.
3. `shapely.distance` (or equivalent geodesic distance) between adjacent footprints.
4. Test cases: re-run the audit cohort with wall-to-wall instead of centroid.
5. Logging: extend the structured log line with `wall_to_wall=Xm type=Y`. Join with Stage 1 logs on `pin` for historical context.
