# Phase 1 Empirical Audit — Sprint 2.21.0.9 (Multi-QARS Detection)

**Date:** 2026-05-23
**Script:** `audit_multi_qars.py` (deployed Heroku v92, no engine change)
**Engine version probed:** `thammen-sprint2p21p0p7p1-hotfix-removed` (unchanged)
**Time-box:** 45 min — wrapped at ~25 min.

---

## 1. Raw results (9/10 succeeded)

| # | input | PIN | PDAREA | PD_NO | n_qars | max_dist_m | building_nos | subtypes | predicted_type | effective_m² |
|---|---|---|---:|---|---:|---:|---|---|---|---:|
| 1 | 56/565/21 (Bou Hamour) | **56090294** | 900 | 0 | 2 | **15.2** | [19, 21] | [1, 1] | **ambiguous** | 450 |
| 2 | 56/565/19 (pair of #1) | 56090294 | 900 | 0 | 2 | 15.2 | [19, 21] | [1, 1] | ambiguous | 450 |
| 3 | PIN 56092231 B=22 | 56092231 | 600 | PD/1761/2004 | 2 | **9.3** | [24, 22] | [1, 1] | **attached** | 300 |
| 4 | PIN 56092231 B=24 (pair) | 56092231 | 600 | PD/1761/2004 | 2 | 9.3 | [24, 22] | [1, 1] | attached | 300 |
| 5 | PIN 56090355 B=10 | 56090355 | 900 | PD/113/2023 | 2 | **14.0** | [10, 12] | [1, 1] | **attached** | 450 |
| 6 | PIN 51240140 51/410/107 | 51240140 | 2040 | PD/3720/2011 | 4 | **53.6** | [28, 107, 105, 30] | [1,1,2,1] | **separate** | 510 |
| 7 | PIN 71380039 71/739/17 | 71380039 | 692 | 0 | 2 | **15.2** | [17, 19] | [1, 1] | **ambiguous** | 346 |
| 8 | 52/903/90 (standalone) | 52200100 | 467 | PD/3063/2001 | 1 | 0.0 | [90] | [6] | **standalone** | 467 |
| 9 | PIN 66030258 (compound_large) | 66030258 | **59,501** | PD/1074/2007 | 1 | 0.0 | [25] | [2] | **handled_by_classifier** | 59,501 |
| 10 | 53/240/12 (Dahil) | — | — | — | — | — | — | — | **QARS lookup empty** | — |

JSON dump retained at `/tmp/audit_multi_qars_results.json` on dyno (ephemeral).

---

## 2. Decision-gate status (per Sprint 2.21.0.9 plan)

| Gate | Status | Evidence |
|---|---|---|
| Reverse spatial query returns empty for ALL multi-QARS cases | ✅ **CLEAR** | 5 of 9 cases returned multi-QARS (n≥2); query mechanism works end-to-end |
| Audit reveals a 5th pattern not in {standalone, attached, separate, compound_large} | ✅ **CLEAR** | Every successful case fits cleanly into one of the four patterns; no surprise emerged |
| PIN 66030258 doesn't classify as compound_large in current production | ⚠️ **production curl blocked from sandbox** — *audit confirms* PDAREA=59,501 + n_qars=1 + subtype=2, which is the canonical compound_large signature; the PDAREA≥50,000 carve-out in `predict_type` keeps the existing classifier owning this path. Suggest you confirm with one production curl after Phase 2 deploys. |

**Proceed: YES** (no stop triggers fired). One gate (production curl) deferred to Phase 4 smoke; rationale above.

---

## 3. Type distribution

```
ambiguous              3   (cases 1, 2, 7)
attached               3   (cases 3, 4, 5)
separate               1   (case 6)
standalone             1   (case 8)
handled_by_classifier  1   (case 9)
```

Note: cases 1+2 are the same polygon; cases 3+4 are the same polygon. Of **5 distinct polygons** with multi-QARS, the distribution is 2 ambiguous + 2 attached + 1 separate.

---

## 4. Key empirical findings

### 4a. **The trigger case (Bou Hamour 56/565/21) lands at exactly 15.2m → ambiguous**

This is the case that motivated the entire Sprint. With the spec's threshold (`<15m attached, 15-30m ambiguous`), it falls into `ambiguous` by 0.2m. Spec default behaviour for ambiguous = "separate" (no `alternative_valuation` offered) → user sees a shared-plot card with manual override, **not** a "value whole structure" toggle. Methodologically still correct (effective_area=450 either way), but the UX deviates from the duplex-semantic Anas described.

### 4b. **15.2m clustering — likely a QARS_Point GPS labeling convention**

Cases 1 and 7 both come out at **exactly 15.2m**, in unrelated areas (Bou Hamour vs Z=71 street 739). This is suspicious — looks like a default minimum GPS-point spacing in QARS_Point's labeling convention for "next-door villa pair on subdivided plot". n=2 is small, but the coincidence is striking.

**Recommendation:** Bump the attached/ambiguous threshold from **15m → 18m** so the 15.2m cluster lands as `attached`. Rationale:
- 15.2m ≈ across a shared internal wall + standard 2-3m setback → reads as duplex semantically
- 18m still excludes the case-6 `separate` cluster (53.6m clean gap)
- The "ambiguous" middle band 18–30m still exists for genuinely uncertain cases

**Bracket-selection impact: ZERO** for these specific PDAREAs (900, 600, 692). `attached` and `ambiguous` both divide by n=2. The only difference is **UI behaviour**: attached → "value whole structure" toggle visible; ambiguous → only the manual-override field. The decision is purely UX.

### 4c. **Case #6 (PIN 51240140) is a small clustered compound, not a simple multi-villa**

n_qars=4 with subtypes `[1, 1, 2, 1]` — one entry is `subtype=2` (Compound with Villas). The polygon (PDAREA=2,040) spans two streets (410 and 525). Splitting equally gives 510 m² per villa — bracket 400-600 — which is reasonable. But the mixed subtypes hint this parcel was originally a 4-unit compound that got reclassified. **The spec's equal-by-count split is fine for now**, but flag for later: a compound-style entry inside a small parcel deserves a heuristic to use the existing compound_small path instead.

### 4d. **Case #10 (53/240/12) failed → QARS_Point miss**

Not a stop trigger. The script handled gracefully (no crash). Possible reasons: stale address, wrong building number, or the parcel never received a QARS label. We already have 1 clean standalone (case 8) so coverage is sufficient. If you want extra negative-case coverage I can swap in another known villa (e.g. 70/300/25 from the Sprint 2.16.15 smoke set).

### 4e. **Subtype info is bonus data we can surface**

Every successful case carries `BUILDING_NO_SUBTYPE` per QARS point. We can show users "duplex of 2 villas (subtype=1 each)" or flag mixed subtypes ("villa + compound entry inside the same PIN") as a yellow-warning hint. Not in scope for Phase 2, but worth noting for future polish.

---

## 5. Deviation from spec (Rule #39)

**What:** Script used `esriSpatialRelIntersects` instead of the plan's `esriSpatialRelContains`.

**Why:** Production helper `_qars_count_in_polygon` (`qatar_gis.py:549`) uses Intersects. Phase 2's new `count_qars_within_polygon` will sit next to it, so matching the operator keeps the audit reflective of real production semantics.

**What is lost:** Nothing. For zero-dimensional features (points) vs a 2D polygon, Intersects and Contains return the identical set — there is no boundary nuance for points.

**What you need to know to interpret results:** The 15.2m cluster, the multi-QARS counts, and the PDAREA splits are all *production-faithful*. If a future ESRI service rejects Intersects, Contains is a trivial swap.

---

## 6. Threshold calibration question (your call before Phase 2)

The single threshold decision that changes UX outcomes for our cohort:

| Threshold for `attached` | Bou Hamour 56/565/21 (15.2m) | 71/739/17 (15.2m) | "Value whole structure" toggle for these? |
|---|---|---|---|
| `< 15m` (spec) | ambiguous | ambiguous | No |
| **`< 18m` (proposed)** | **attached** | **attached** | **Yes** |
| `< 20m` | attached | attached | Yes |

I propose **18m**. Two cases at exactly 15.2m in unrelated areas suggest a GPS-labeling artifact; an 18m threshold absorbs the artifact without erasing the ambiguous band (18-30m still exists).

---

## 7. What Phase 2 will use (assuming you approve the above)

1. **Function signature unchanged:** `count_qars_within_polygon(polygon_geometry: dict) -> list[dict]` returning the same fields the audit emitted.
2. **classify_multi_qars** with these decision rules (threshold per your decision in §6):
   - PDAREA ≥ 50,000 AND n_qars ≤ 1 → `handled_by_classifier` (compound_large owns)
   - n ≤ 1 → standalone
   - n = 2, dist < {15|18|20} → attached
   - n = 2, {15|18|20} ≤ dist ≤ 30 → ambiguous (default behaviour: separate)
   - n = 2, dist > 30 → separate
   - 3 ≤ n ≤ 5 → separate
   - n ≥ 6 → handled_by_classifier (deferred to apartments path)
3. **effective_land_area = PDAREA / n** for attached/separate/ambiguous; no title discount (per your decision, "السوق لا يميّز").
4. **API `multi_qars` block** as spec'd; `alternative_valuation` only for type='attached'.
5. **UI:** yellow card with type-conditional copy + (for attached) "قيّم المبنى كاملاً" toggle + (always) manual `override_land_area` field.

---

## 8. Checkpoint — awaiting Anas approval

Per the Sprint 2.21.0.9 plan: "After Phase 1 audit — present findings before coding."

**Three asks before I touch any production module:**

1. **Threshold:** keep 15m, bump to 18m (my recommendation), or some other number?
2. **Case #10 retry?** Swap 53/240/12 for another standalone, or proceed with 9-case coverage?
3. **PIN 66030258 production sanity check?** I can run one `heroku run` curl to confirm it still classifies as `compound_large` today — or you can verify yourself after Phase 4.

Also: nothing else triggered (no 5th pattern, no endpoint issues, no Reality Check regression risk visible). Decision-gate clean.

---

*Phase 1 wall-clock: ~25 min (under the 45 min cap).
Deploy footprint: Heroku v92 = audit script only; ENGINE_VERSION untouched.*
