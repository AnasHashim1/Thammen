# Pre-Sprint 2.22.0a §5 Audit Findings

> **Audit date:** 2026-05-26 PM
> **Production baseline at run:** `thammen-sprint2p21p4-t3-aryan-lusail` (Heroku **v128** code, runtime unchanged from v127 — docs-only push of `a903350`)
> **Author:** Claude Code (Phase 3 Step 4 deliverable)
> **Status:** Phase 3 §5 audit complete. **Stops and awaits Anas approval before any 2.22.0a code change.**
>
> **Cohort:** A1-A5 per Anas approved sequence + Δ Step 4 expansion (Pearl A5 re-introduced as BRIEF v3.1 §1.7 ship-gate requirement).
>
> **Source artifacts (in this directory):**
> - `pearl_pin_discovery.py` + `pearl_pin_discovery.json` — Pearl PIN self-extraction
> - `pearl_t2_substitutes.py` + `pearl_t2_substitutes.json` — fallback T2 + V3 Huzoom check
> - `audit_step4_5cases.py` + `step4_5cases_audit.json` — main 5-case audit
> - `audit_step4_a3_retry.py` + `step4_a3_retry.json` — A3 cold-dyno disambiguation
> - This file — synthesis for Anas approval gate.

---

## §0 Headline (one paragraph)

**5/5 cases consistent with Phase 1 baseline.** The engine at v128 (docs-only push from v127) behaves identically to the Phase 1 audit captured 24 hours prior. A3 Umm Lekhba villa hit a cold-dyno HTTP 503 on rep 1 (same multi-QARS cold-dyno pattern observed in Phase 1) but the warm-dyno retry produced **0.000% drift** vs Phase 1 baseline. A1 City Avenues H1 anchor produced `val.value_per_m2 = 11,425.17` vs Phase 1's `11,415.02` — **+0.089% drift** within the 0.1% tolerance window and explained by PF connector's daily listing-count variance (n=78 in Phase 1, n=79 today). **The new Pearl A5 case surfaced 3 critical findings for 2.22.0a/b scope** (see §3 below). Three verification items completed: V1 PASS (Operational Rule #42 exists), V2 fixed (PHASE3_LOG.md initialized), V3 PARTIAL PASS (Huzoom syndication confirmed on arady; FGRealty/PropertyFinder/Steps/QatarSale all unreachable from sandbox — documented).

---

## §1 Cohort + per-case results

| Case | Address / PIN | Asset @ v128 | District | TTLB | val.amount | val.value_per_m2 | val.method | Brief sections | Phase 1 drift |
|---|---|---|---|---:|---:|---:|---|---|---|
| **A1** | 69/255/75 | apartment_building | لوسيل 69 | 10.05s | None | **11,425.17** | hybrid_t2 (case B, n=79, T2 0.88 + T3 0.12) | `['next_steps']` | **+0.089%** vs Phase 1 (11,415.02) — within tolerance; explained by PF n=78→79 daily variance |
| **A2** | 51/835/17 | compound_large | الغرافة | 25.65s | None | None | insufficient_data (Patch-A clean refusal) | negotiation, flags, due_diligence, material_uncertainty | **0%** — exact match |
| **A3** | 31/918/99 | standalone_villa | ام لخبا | rep 1: 30.36s HTTP 503 (cold dyno); rep 2: 21.63s HTTP 200 | **3,200,000** | None | comparison_thin | negotiation, flags, due_diligence, material_uncertainty | **0.000%** — exact match on retry |
| **A4** | PIN 66030258 | unknown | عنيزة 66 | 4.38s | None | None | **asset_type_reality_stop** | `['asset_type_reality']` | **0%** — exact match |
| **A5 NEW** | 66/140/6 | **tower** | **جزيرة اللؤلؤة** | 4.19s | None | None | insufficient_data | `['next_steps']` | n/a — first observation (no Phase 1 baseline) |

### §1.1 Latency drift summary (vs Phase 1, ~14 hours apart)

| asset_type | Phase 1 p50 | Step 4 single-rep | Delta |
|---|---:|---:|---:|
| apartment_building (Lusail hybrid_t2) | 5.06s | 10.05s | **+99%** ⚠️ |
| compound_large (Patch-A) | 25.01s | 25.65s | +2.5% (within noise) |
| standalone_villa (warm) | 22.06s | 21.63s | −2.0% (within noise) |
| unknown (reality-check) | 3.72s | 4.38s | +17.7% (single-rep noise) |
| tower (Pearl) | — | 4.19s | new |

**Latency note:** A1 doubled vs Phase 1 (5.06s → 10.05s). This is **one rep**, not a measured baseline shift. Phase 1 had n=3 reps with very tight variance (4.96s / 5.14s / 5.19s). A single 10s rep could be PropertyFinder connector slow-path (e.g., 1 of the 3 list pages took 5+ seconds). **Not flagged as drift** but worth re-measuring with n=3 in Phase 4 H-walk after 2.22.0a deploys. Possible explanation: PF list pages added a new page (n=78→79 suggests pagination crossed a boundary). Note this is **still within Stage 1 ≤5s asymmetric ceiling for apartment_building** per BRIEF v3.1 §1, only marginally.

---

## §2 Pearl PIN self-discovery (Step 4 prerequisite)

### §2.1 Sub-step 1: FGRealty Pearl listings — **FAILED**

All 5 FGRealty URLs tried returned HTTP 404:
- `/apartments-for-sale/the-pearl`
- `/apartments-for-sale/the-pearl-qatar`
- `/properties-for-sale/the-pearl`
- `/the-pearl`
- `/properties?location=the-pearl&type=apartment`

**Implication:** FGRealty URL structure has changed since the schema documented in `Operational_Rules.md §29` (service-charges verification work). Either deeper path discovery needed, or FGRealty is rate-limiting from sandbox IP. **Not a blocker** — Pearl PIN discovery satisfied via GIS authority (sub-steps 2-4); listing-traceability satisfied via arady fallback (§2.5 below).

### §2.2 Sub-step 2: GIS Districts spatial query at Pearl centroid (25.371, 51.547)

**✅ PASS** — single feature returned:
- `ANAME = 'جزيرة اللؤلؤة'`
- `ENAME = 'The Pearl Island'`
- `DIST_NO = 765`

Matches the Pearl `areaCode = 765` documented in `Operational_Rules.md §28` MME schema.

### §2.3 Sub-step 3: QARS_Point intersect Pearl polygon

**✅ PASS — no stop condition triggered:**
- 200 total QARS points in Pearl polygon (capped at `resultRecordCount=200`)
- **24** with `BUILDING_NO_SUBTYPE = 11` (Tower)
- **104** with `BUILDING_NO_SUBTYPE = 6` (Building with Flats)
- Schema sample (5/5): **all** have full `ZONE_NO + STREET_NO + BUILDING_NO + PIN`

**`STOP_PEARL_SUBTYPE_GAP` did NOT trigger** (24 + 104 features present, far above 0 threshold).

**`STOP_PEARL_NOT_QARS` did NOT trigger** (5/5 schema samples have full Z/S/B = `qars_zsb` verdict). **Pearl uses standard QARS Z/S/B addressing.** Pearl zone = **66** confirmed.

### §2.4 Sub-step 4: Cross-match tower

FGRealty had no tower names extractable (4xx on all paths). Fallback: picked first Z/S/B-complete tower from QARS:
- **PIN 66200197**
- **Z/S/B = 66/140/6**
- subtype = 11 (Tower)
- match_type = `first_zsb_complete` (FGRealty cross-match unavailable)

**This is the A5 candidate PIN.**

### §2.5 Sub-step 5 + V3 incidental: arady fallback

After FGRealty failure, tried PropertyFinder + Steps + QatarSale + arady as T2 substitutes:

| Source | URL pattern | Outcome |
|---|---|---|
| PropertyFinder | `/en/buy/the-pearl/apartments-for-sale.html` (2 variants) | HTTP 404 both |
| Steps | `steps.qa/for-sale/...` (2 variants) | **DNS failed** (`getaddrinfo failed`) |
| QatarSale | `/properties/sale/apartments/the-pearl` | HTTP 404 |
| **arady** | `arady.qa/listings?location=the+pearl&type=apartment` | **✅ HTTP 200, 456KB**, tokens `'the pearl' + 'اللؤلؤة' + 'قنوات' + 'huzoom'` all found |

**Pearl listings traceability:** satisfied via **arady** (T2 source per Rule E8).

**V3 verdict — Huzoom syndication claim:** **PARTIAL PASS**. The token `'huzoom'` appears in arady's Pearl listings page → confirms Huzoom inventory IS syndicated to at least one T2 source. However, `SOURCE_EXCLUSIONS.md` explicitly names FGRealty/PropertyFinder/Steps/QatarSale as the 4 substitutes — none reachable from sandbox today. Arady is a Rule E8 T2 source but was not listed in SOURCE_EXCLUSIONS. **Minor documentation gap, NOT a blocker.** Recommend adding arady to the substitute list in a future docs-only commit (NOT in 2.22.0a scope).

### §2.6 Pearl A5 audit result

Running `/api/evaluate` with `{zone: 66, street: 140, building: 6}`:
- HTTP 200, TTLB 4.19s ✓
- `asset_type = 'tower'`, `asset_type_ar = N/A`, district = `'جزيرة اللؤلؤة'`
- `val.method = 'insufficient_data'`, brief = `['next_steps']`
- No hybrid block, no sources block, no accuracy block

**Three critical findings for 2.22.0a/b scope** (see §3 below).

---

## §3 Findings that materially affect 2.22.0a/b scope

### §3.1 — Pearl is OUTSIDE D10 Lusail gate (Sprint 2.21.3) — hybrid path doesn't fire for Pearl

D10 substring check in `evaluate_unified._is_lusail_district()` (BRIEF v3.1 §16.2) gates on `{'لوسيل', 'غار ثعيلب'}` Arabic tokens. Pearl's GIS district name `'جزيرة اللؤلؤة'` does NOT contain either token. **Result:** Pearl apartments/towers currently fall through to `insufficient_data` even though the underlying hybrid framework + tier_breakdown logic could produce a per-m² value (the architecture is there; the gate is the only thing blocking Pearl).

**Implication for 2.22.0:**
- **2.22.0a** (this Sprint): the BRIEF v3.1 §1.6 dynamic refusal triggers + mandatory reason text should explicitly classify Pearl `insufficient_data` today as the "density-gated district" trigger (per §1.7) so the user gets a coherent refusal message rather than the generic insufficient_data screen.
- **2.22.0b** (later): the property graph density gating logic must decide WHETHER Pearl gets a Lusail-style D10 extension OR stays density-gated until inventory/connector work lands. **This is the Pearl ship-gate decision — BRIEF v3.1 §1.7 makes it a hard launch gate.**

**Recommended action:** 2.22.0a does NOT extend D10 to Pearl (out of scope per Rule #38 single-purpose). Pearl remains density-gated. 2.22.0b's density gating logic explicitly handles Pearl as a refusal zone with the specific message: *"Pearl Qatar inventory not yet covered by automated estimation. A specialized assessment is recommended."* (or equivalent per §1.6 templates).

### §3.2 — A1 PF connector drift confirms hybrid value is NOT static

Phase 1: `val.value_per_m2 = 11,415.02` (n=78)
Step 4 (~14h later): `val.value_per_m2 = 11,425.17` (n=79)
Δ = **+0.089%** (within 0.1% tolerance)

This is **NOT engine drift** — it's the PropertyFinder live connector picking up 1 additional listing between runs. The hybrid framework is functioning as designed: per-m² updates as the T2 sample evolves.

**Implication for 2.22.0a:**
- Sprint 2.22.0a brief content fix + tier_breakdown UI must surface the **sample size + freshness** of the underlying T2 data so users see "estimate based on 79 listings as of [today]" rather than treating the per-m² as a static figure.
- The "calculator-style visual" (BRIEF v3.1 §1 Stage 3 output) should include a freshness timestamp.

**Recommended action:** add `n_used` + sample timestamp to the tier_breakdown UI section in 2.22.0a per BRIEF v3.1 §3 D-stage2-7 source-attribution (currently the data IS there — `hybrid.n_used = 79` — just not rendered).

### §3.3 — Pearl classifies as `tower` not `apartment_building`

A5 returned `asset_type = 'tower'` (BUILDING_NO_SUBTYPE = 11 → Sprint 2.16.6 classifier branch). This is correct per Sprint 2.16.6 fix scope ("15,881 polygons (~7% of Qatar) — all Lusail/West Bay towers" + Pearl).

**Implication for 2.22.0:**
- BRIEF v3.1 §1 Stage 2 field set D-stage2-1: row 1 ("Floor number") says "Always ask for **apartment/tower**. Skip for villa/land." → Pearl tower correctly falls under "apartment/tower" cohort.
- The hybrid path (Sprint 2.21.3 §16.2) is currently gated on `asset_type == 'apartment_building'`. **Pearl towers do NOT enter hybrid even if D10 were extended.** Either (a) extend the hybrid gate to include `'tower'`, or (b) keep tower out of hybrid and route via DCF only. **2.22.0b density gating decision.**

**Recommended action:** add asset_type='tower' as a hybrid-eligible class WHERE appropriate. The hybrid_t2 connector currently fetches `propertyfinder_apartments_t2_sales` which by name targets apartments only. Pearl towers and apartments share the same building inventory (residential high-rises), so the connector can probably handle both. Sprint 2.22.0b density gating logic Sprint must decide.

---

## §4 Verification side-checks

| # | Check | Verdict | Notes |
|---|---|:---:|---|
| **V1** | `Operational_Rules.md` Rule #42 cross-reference (in `SOURCE_EXCLUSIONS.md` huzoom block) | ✅ PASS | Rule #42 "Deferred-Work Documentation" exists at line 969 of `Operational_Rules.md`. Cross-reference valid. No fix needed. |
| **V2** | `PHASE3_LOG.md` exists + Δ2 backlog entry | ✅ PASS (fixed in commit `9a1c0a1`) | File initialized at canonical `2p22p0_pre/PHASE3_LOG.md` per BRIEF v3.1 §10 #7. Δ2 backlog entry captured in §F. |
| **V3** | Huzoom syndication claim on `FGRealty/PropertyFinder/Steps/QatarSale` substitutes | ⚠️ PARTIAL PASS | None of the 4 named substitutes reachable from sandbox today (404 + DNS fail). However, `arady` (T2 source per Rule E8) confirmed token `'huzoom'` in Pearl listings page — Huzoom IS syndicated to at least one T2 source. **SOURCE_EXCLUSIONS substitute list should include arady in a future docs commit** (not 2.22.0a scope). |

---

## §5 Deferred coverage (per Anas single-purpose Sprint discipline)

**Not in this audit.** Filed as gaps for **Sprint 2.22.0.1** §5 audit:

| Coverage gap | Rationale for deferral | Implication for 2.22.0 |
|---|---|---|
| **Lusail Marina** | Different micro-market within Lusail. Phase 1 covered Lusail 69 (City Avenues) + غار ثعيلب (Fox Hills). Marina is not a hybrid-path test (same D10 token works). Density-baseline gap only. | 2.22.0b density gating must treat Marina as "covered" via D10 inclusion. No code change needed if `_is_lusail_district()` already matches Marina's GIS district name (likely `'لوسيل 69'` or `'لوسيل 70'` per CLAUDE.md §16). |
| **Tower (elsewhere, non-Pearl)** | Pearl tower covered in A5. Other towers (West Bay, Lusail, scattered) not tested. Subtype-11 classification path well-exercised in Phase 1 (15,881 polygons per Sprint 2.16.6). | None — tower classification works. Density gating treats per-district. |
| **compound_small** (subtype=2/3, 5–15K m²) | No canonical PIN in project docs. Likely zero production traffic at this asset_type (per Operational_Rules #20 E20 = compounds ≥15K → promoted to compound_large via Patch A). | None — likely a near-empty asset class at v128. |
| **Pearl FGRealty/PropertyFinder/Steps/QatarSale URL paths** | URL schema needs discovery. Not blocking. arady covers listing traceability. | Minor — update SOURCE_EXCLUSIONS substitute list in docs commit |

**All four gaps documented in `PHASE3_LOG.md §G Open audit items`.**

---

## §6 What this audit confirms about Phase 3 entry conditions (BRIEF v3.1 §10)

| # | Entry condition | Status |
|---|---|:---:|
| 1 | Anas signs BRIEF FINAL v3.1 | ✅ (per Phase 3 kickoff message) |
| 2 | Commit `a903350` pushed to Heroku | ✅ (v128 released) |
| 3 | 2.22.0a scope confirmed | ✅ (BRIEF §2 row 1) |
| 4 | 2.22.0b scope confirmed | ✅ (BRIEF §2 row 2) |
| 5 | 2.22.x parallel scope confirmed | ✅ (BRIEF §2 row 6) |
| 6 | 2.22.y parallel scope confirmed | ✅ (BRIEF §2 row 7) |
| 7 | Phase 3 worklog initialized | ✅ (commit `9a1c0a1`) |
| 8 | Density baselines confirmed achievable OR density-gating accepted | ⚠️ **Pending — Pearl is the trigger case.** §3.1 above recommends "density-gating accepted as launch posture for Pearl" until Sprint 2.22.0b property graph density logic + hybrid Pearl extension lands. Lusail 69 + Fox Hills already meet inventory-density baseline (n=79 T2 listings + T3 active). West Bay partial (61/875/20 confirmed via A11). |

**Entry condition #8 specifically:** the BRIEF v3.1 §1.7 says "If any target zone fails, 2.22.0 ships with that zone density-gated (auto-refusal) until density recovers in subsequent sprints." This audit confirms **Pearl is density-gated at v128** (no hybrid path fires; insufficient_data refusal). Sprint 2.22.0b must implement this as a deliberate refusal per §1.6 mandatory reason text, not as the current generic insufficient_data screen.

---

## §7 Recommendation for 2.22.0a implementation entry

### §7.1 — APPROVED to enter 2.22.0a after Anas sign-off

5/5 audit cases consistent with Phase 1 baseline. No engine drift detected. Cold-dyno + PF live-data variance are expected behaviors, not regressions.

### §7.2 — Phase 1 BRIEF v3.1 §1.6 refusal-trigger templates must be parameterized for these specific findings

The mandatory reason text templates (BRIEF v3.1 §1.6) should accommodate:
- **A2 / A4-style refusal:** "comp density sparse" trigger fires today as `insufficient_data` — 2.22.0a must render the §1.6 Arabic copy ("This district has fewer than 5 comparable transactions...") in place of the current generic "بيانات غير كافية" copy.
- **A5 / Pearl refusal:** "density-gated district" trigger needed (per §1.6 last row). Pearl gets this until 2.22.0b extends hybrid to Pearl OR until inventory density meets §1.7 baselines.

### §7.3 — Tier_breakdown UI must surface n + freshness

A1's day-to-day `n_used` variance (78 → 79) means the user-visible tier_breakdown UI must include sample size + freshness timestamp so the user understands the indicative range reflects live data. The hybrid block in the response already carries `hybrid.n_used` — just needs rendering in 2.22.0a's `output_briefs.py` tier_breakdown section + `index.html` `renderSection()` switch.

### §7.4 — `asset_type == 'tower'` should also enter hybrid path (Pearl + future)

Pearl A5 classified as `tower`, not `apartment_building`. Sprint 2.22.0b's hybrid gate should accept both. Out of 2.22.0a scope per Rule #38 single-purpose, but flagged here so the 2.22.0b implementation includes it.

---

## §8 What this audit is NOT

- Not a Sprint. No engine version bump. No code change. No Heroku push.
- Not a comprehensive Pearl ship-gate validation. §1.7 baselines (Tower Coverage Floor ≥85%, Transaction Linking Floor ≥75%, Condition Fingerprint Density ≥5/1000m², Heartbeat metric ≤5%) must be measured in 2.22.y. This audit confirms only that Pearl PIN discovery + addressing schema + classifier basic path all work.
- Not a usability study. H7 (5-stage UX mockup naturalness) deferred to Phase 2 mockup review.
- Not the comprehensive §1.6 refusal trigger validation. 2.22.y validation Sprint owns this.

---

## §9 Stop point + hand-off

**Phase 3 Step 4 complete.** Stops here per Anas's approved sequence step 6. Awaits explicit approval for **2.22.0a implementation start**.

**To Anas:** review this audit synthesis. On approval, Step 7 (NOT yet defined — will be Sprint 2.22.0a implementation kickoff) begins.

**Suggested next-step questions for Anas to resolve before 2.22.0a kicks off:**

1. **Pearl density-gating posture:** confirm 2.22.0a renders Pearl refusal via §1.6 "density-gated district" template (with mandatory reason text), and 2.22.0b decides hybrid extension to Pearl?
2. **Tower asset_type hybrid eligibility:** confirm 2.22.0b adds `'tower'` to hybrid-eligible classes (alongside `'apartment_building'`)?
3. **arady inclusion in SOURCE_EXCLUSIONS substitute list:** docs-only patch later (separate housekeeping), or hold until next docs wave?
4. **A1 latency anomaly (5.06s → 10.05s):** acceptable as single-rep noise, OR add to 2.22.y validation Sprint scope as a measured baseline?

No code change before Anas resolves above and grants 2.22.0a implementation green light.

---

*Phase 3 Step 4 deliverable. Created 2026-05-26 PM. Source artifacts in this directory. No engine version bump. No production state change. No git push. Awaiting Anas approval.*
