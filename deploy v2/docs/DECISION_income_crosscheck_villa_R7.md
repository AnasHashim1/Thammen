# Decision — Income Cross-Check Triangulation as the R7 Villa-Valuation Mechanism

**Date:** 2026-06-07 · **Status:** **PO-ENDORSED (direction)** — NOT yet built.
**Gate:** Hard Gate 2 (methodology) — requires a §5 data-feasibility audit + signed brief +
yield calibration **before it lands**. **Supersedes the FRAMING of:** the b.4 teardown-only
switch and the parked B-2 condition-elicitation as the *sole* R7 path.

## 1. The decision (Anas, 2026-06-07)
After a live valuation walk-through of villa **56/647/6** (V001, المعمورة — the "villa 6"
photos), Anas endorsed the **income cross-check** as the methodology backbone for villa
valuation — over owner-aspiration, over a condition-blind comparison median, and over the
crude teardown switch. PO words: «هذه المنهجية أفضل بكثير … لا يهمني طموح المالك … ما دام
لدي منهجية قوية أستند عليها».

## 2. Why it is strong (RICS triangulation — 4 pillars cross-check; value = convergence, divergence → MUC)
1. **Land floor** — MoJ land median × plot (n≥20). Hard floor.
2. **Sales comparison** — area villa median. Market signal, but **condition/age-BLIND (R7)**.
3. **Income cross-check** — realistic rent ÷ villa cap rate. **THE binding check:** rent
   reflects age/condition, so it automatically catches the comparison's over/under-anchor
   (old → lower rent → lower value; new → higher). Continuous, not a switch.
4. **Cost / DRC** — depreciated replacement. Ceiling (market ≤ replacement) + teardown floor.

## 3. The walk-through that proved it (villa 6 / V001, 652 m², ~25 yr, very good, pool)
- Land floor **2.46M**; condition-blind comparison **3.8M**; DRC **~4.0–4.5M**.
- **Income (live PropertyFinder, المعمورة):** standard unfurnished villas **13–16.5k**/mo;
  **19–20k only for NEW furnished luxury**. Villa 6 ≈ **15–17k** (large + pool, but old, unfurnished).
- 15–17k ÷ yield: **@6% (investor)** ~3.0–3.4M · **@5% (owner-occupier — our §11.3 4–4.7%)** ~3.6–4.1M.
- **Converged Market Value ≈ 3.6–3.8M** (income@5% ≈ comparison; both < cost ceiling, > teardown floor).
  The income check correctly **capped below cost** AND **lifted above the 2.9M teardown estimate**.

## 4. Why this beats the prior R7 plans
- **vs b.4 teardown switch:** binary/extremes-only → over-anchored the good/very-good middle
  (live: 56/647/6 `good`/`renovated` → 3.7–3.8M unchanged). Income is **continuous**.
- **vs B-2 condition-elicitation (parked on confirmed-sales n≥20):** shifts the data
  dependency from *confirmed sales* (no feed — **blocked**) to *villa rent medians* (available
  via PF) + a yield → **more feasible; sidesteps the n≥20 blocker.**

## 5. Dependencies to make it production-strong (the honest gaps)
1. **Villa rent data per area** — extend the PF connector to villa rentals per district
   (المعمورة had 93 listings; verify thinner areas). Need median + n + age/condition split.
2. **Villa yield (cap rate) calibration** — **THE swing factor** (5% vs 6% = ±~20% on value).
   Per-area / per-stratum. `cap_rates.sqlite` (Sprint 2.19) is the seed but thin (Al-Ebb 4.7%).
   **An uncalibrated yield = an unreliable headline (#10).**
3. **Age/condition rent adjustment** — rent comps must reflect the subject's age/condition
   (or be adjusted). This is where the photos / Stage-2 input feed in.

## 6. Path (Gate-2)
§5 data-feasibility audit (villa rent availability + yield per area, via a PF/Heroku smoke) →
**signed brief** → build the villa income cross-check (reuse `cap_rates.sqlite` + the DCF/yield
machinery already live for towers/compounds) → triangulate the 4 pillars → MUC on divergence →
live smoke. **Do NOT land a headline value without the yield calibration.**

## 7. Status of the engine today (for the record)
Live = **Heroku v171 / b.4** (teardown ↓ + luxury-new DRC ↑ + penthouse — EXTREMES-ONLY; the
good/very-good middle still over-anchors at the widened value). This decision defines the
**next** R7 step; b.4 stays live and unchanged until the income cross-check is audited, briefed,
calibrated, and signed.

## 8. §5 data-feasibility audit (2026-06-07) — VERDICT
**Dependency #1 — villa rent data (PropertyFinder): FEASIBLE ✓.** Live PF villa-rent listing counts:
المعمورة **93** · أبو هامور **121** · الغرافة **142** · عين خالد **284**. Plentiful for a median
(needs standalone / furnished / size stratification). Standard unfurnished villa rents cluster
**9–16.5k/mo**; **19–20k ONLY for NEW furnished luxury** → confirms an old villa cannot justify 19k.

**Dependency #2 — yield calibration: THE BOTTLENECK, currently UNRELIABLE 🔴.** Existing
`cap_rates.sqlite` (Sprint 2.19): 109 villa cells but **only 1 reliable + 2 indicative; 106 fallback**.
Computed gross yields span **4.1% (اللؤلؤة 600-900) → 11.5% (مريخ 0-400)** — a **3× spread**. At that
spread villa 6's income value ranges **~1.7M–4.8M** (unusable as a point). Structure DOES exist
(premium/large → ~4–5%; small/cheap → ~8–11%), so a stratified well-sampled calibration is viable —
but the current one is far too thin. **المعمورة (villa 6's own area) villa yield is NOT calibrated**
(gross=None — rent didn't match sale). Gross + net both in schema (opex ~20%).

**Conclusion.** The income cross-check is data-FEASIBLE (rent [PF] + sale [MoJ] both exist per area →
gross yield = PF-rent-median ÷ MoJ-sale-median is directly computable) but **NOT yet "strong"** — the
**yield is the make-or-break and is currently unreliable**. **First build task = a proper stratified
yield calibration** (extend Sprint 2.19: standalone-villa filter + size×stock strata + more PF rent
pulls + a18 area-name reconciliation), THEN the triangulation formula. This also explains the
point-estimate sensitivity: the value swings because the yield genuinely isn't pinned (measured 4–11%).

**Villa 6 income read (honest, uncalibrated):** gross rent ~16k/mo ÷ a plausible ~5.5–6.5% gross yield
(larger suburban villa) ≈ **~3.0–3.5M** (centre ~3.2M) — below the condition-blind comparison (3.8M),
which is the income check doing its job; pin precisely once المعمورة 600-900 villa yield is calibrated.

## 9. Yield-calibration v1 — BUILT + locally validated (2026-06-07) — HELD at Gate-1/Gate-2

**Status:** the stratified villa-yield calibration (Dependency #2, "THE bottleneck") was **built and
validated LOCALLY** this session. **NOT shipped** — the rebuilt DB is held at **🔴 Gate-1 (Heroku push)**
+ **🔴 Gate-2 (it changes the user-visible income cross-check)**, both pending an explicit Anas «go».
Engine UNTOUCHED (`evaluate_unified.py` value-invariant); committed `cap_rates.sqlite` UNTOUCHED; the new
DB lives as a gitignored `cap_rates.new.sqlite`.

**Disposition (Anas «افعل الأصوب», 2026-06-07).** The narrow 3-cell DB is NOT worth a standalone Gate-2
deploy; the «الأصوب» path = **preserve the work + ship the yield-data WITH broader coverage and/or the §6
triangulation mechanism, not before**. So this session: the **value-invariant CODE** (`cap_rate_calibrator.py`
+ `propertyfinder_client.py` deep-crawl robustness + `tests/test_cap_rate_calibrator_r7.py` + `.gitignore` +
this doc) is committed to **origin ONLY** — a backup; **Heroku NOT deployed, `cap_rates.sqlite` NOT swapped**
(the calibrator is a build-time tool not in the runtime path, so the committed code is provably value-invariant
until the DB is swapped + deployed). The **DB swap + deploy stay HELD**. **NEXT unit = per-area PF depth**
(locationId search, §8 lever) — own §5 audit; then ship yield-data + §6 wiring together.

**What was built (data-only, reversible — `cap_rate_calibrator.py` + `propertyfinder_client.py`):**
- **(d) a18 reconciliation** — the calibrator now reuses the ENGINE's `resolve_moj_area_name` +
  `build_reference` (Sprint 2.22.0a.18) for the yield DENOMINATOR, so it is **identical to the valuation
  denominator** (zone-sibling pooling + overrides, e.g. امريخ الجنوبي→مريخ). Replaces the bespoke
  `area_token`/`_zone_num` double-normalization.
- **(a) standalone-villa filter** — villa-yield pool restricted to PropertyFinder `Villa` (townhouse
  excluded), matching the A2 sale-side STANDALONE_VILLA stratification. (No-op on this crawl: the
  villas-for-rent feed is already pure-Villa — a correct guard, 0 excluded.)
- **(c) deep crawl + dedupe** — national feed crawled to PF's real serving cap with **dedupe by listing
  id**: **1254 → 1214 unique villa rentals (≈3× the Sprint-2.19 ~400)**. Connector hardened: PF
  over-reports `page_count=139` but **404s beyond ~page 50**; `fetch_rentals` now breaks gracefully on a
  per-page 404 (was crashing the whole crawl).
- **(e) furnished-consistent rent median** — the rent numerator now excludes fully-FURNISHED listings
  (basis-consistent with the unfurnished MoJ sale denominator), with the furnished split recorded per cell.
  Material: المعمورة 400-600 median rent 16.5k→12.5k (a ~24% furnished premium removed). gross/net (villa
  opex 0.20) unchanged in form.

**Validation (real engine fns + real moj_weekly.csv — E14):** isolated `test_cap_rate_calibrator.py`
**59/59** + new `test_cap_rate_calibrator_r7.py` **29/29**. Live rebuild (281s): 158 cells, **villa
reliable 2 · indicative 1 · fallback 142** (was reliable 1 · indic 2). The 3 usable cells are now all
CORRECT (a18 denominator, furnished-consistent, **no Fix#4 stock=None violation** — the old الغرافة 0-400
"indicative" was such a violation, now correctly fallback):

| cell | committed (v2.19) | new (v2.19.2) |
|---|---|---|
| العب 400-600 | 5.88% gross / reliable n=35 | 5.88% / **reliable n=52** |
| **المعمورة 56 400-600** | 7.37% / indicative n=13 (furnished-inflated) | **6.04% gross / 4.83% net / reliable n=24** |
| عين خالد 400-600 | fallback n=4 | **6.72% gross / indicative n=15** (a18+stock rescued) |
| الغرافة 0-400 | 11.7% / indicative · stock=None (Fix#4 breach) | fallback (correct) |

**Villa-6 (المعمورة, 652 m² → 600-900):** its exact bracket is still thin (n=3, gross 5.29% → fallback),
**but** المعمورة 400-600 is now **reliable at 6.04% gross / 4.83% net** and the thin 600-900 (5.29%) is
consistent → a **~5.3–6% gross** band ⟹ **villa-6 income value ≈ 3.2–3.6M** (was the unusable 1.7–4.8M of
§8). Converges with §8 (~3.2M) + the human read (2.9–3.2M); below the condition-blind comparison (3.8M) —
the income check doing its job.

**Honest residual (#36).** The usable-cell COUNT is still only **3** — the deep crawl lifted only the
BIG areas across n≥20 (العب, المعمورة). The binding constraint that remains is **per-cell rental depth**
(PF caps the national feed at ~50 pages → ~1214 spread over 158 cells ≈ 8/cell) **+ missing MoJ land
medians** (no land median → stock=None → Fix#4 fallback). **Next lever = per-area PF search by locationId**
(the §8 method that found 93–284 listings/area) to deepen thin districts — a separate connector sprint
(national-feed slugs `…-in-<area>.html` 404; needs the `?l=<locationId>` discovery).

**Gate-2 lookup flag (for the wiring step, NOT changed here).** The engine's calibrated-rate lookup
`evaluate_unified._cap_area_token` strips «ال»+zone+folds but is **NOT override-aware** — a subject in GIS
«امريخ الجنوبي» would not match a cell stored under «مريخ». Mitigated for now by storing the GIS aname (not
the a18 key) as `district_aname`, so GIS↔GIS matching holds incl. override areas; the durable fix
(make `_lookup_calibrated_cap_rate` a18/override-aware) belongs to the Gate-2 income-triangulation wiring.

**The two gates (need an explicit «go»):**
1. **Gate-1 (push)** — commit `cap_rate_calibrator.py` + `propertyfinder_client.py` + the new test +
   `.gitignore`, **replace `cap_rates.sqlite` with the rebuilt DB**, `git subtree push heroku` + origin.
2. **Gate-2 (methodology/output)** — the rebuilt DB changes the user-visible income cross-check for the
   affected areas (المعمورة 7.37%→6.04%, عين خالد new indicative, الغرافة demoted). This is the
   yield-data correction; the **headline-triangulation wiring** (income setting the villa headline) is a
   LATER, separate Gate-2 step (§6) and is NOT in this build.

## 10. Per-area depth (the §9 "NEXT unit") — BUILT + measured (2026-06-07) — HELD at Gate-1/Gate-2

**Status:** the §9 NEXT unit ("per-area PF depth, locationId search, own §5 audit") is **done**.
§5 audit COMPLETE + CLEAN, connector BUILT + tested, the deepened DB measured. **Engine UNCHANGED
(b4/v171); live `cap_rates.sqlite` UNTOUCHED** (git-confirmed); the rebuilt DB is the gitignored
`cap_rates.new.sqlite`. Both gates **HELD** pending an explicit «go». Full audit:
`docs/PHASE0_R7_perarea_connector.md`.

**§5 audit (Phases A–D, 4 read-only probes):** PropertyFinder filters a villa-rent search to one
COMMUNITY via the scalar **`villas-for-rent.html?l=<community_id>`** (the ONLY honored form —
bracket/array/slug-path forms are ignored or 404). Community ids are harvested from each listing's
`location_tree` (level-1) — **no new endpoint**. `?l=68` verified = Al Maamoura (27/27 tree + GPS).
Per-area depths: اللؤلؤة 325 · عين خالد 260 · الوعب 259 · الخيسة 248 · أبو هامور 187 · المعمورة 103
· الغرافة 89 — vs ~8/cell nationally; pagination retrieves the full area (المعمورة 103/103).

**Build (value-invariant; national path byte-for-byte preserved):** `propertyfinder_client.py`
(+`location_id` param on `fetch_rentals` → `?l=`; +`community_map`/`community_nodes`;
+`_fetch_raw_listings`) · `cap_rate_calibrator.py` (+`collect_rentals_per_area`; +`per_area` switch
on `calibrate`, default False = national unchanged) · `tests/test_cap_rate_calibrator_r7.py` (+13 →
**42/42**; base suite **59/59**). These are build-time tools — NOT imported by `api.py`/runtime.

**Measured coverage gain (per_area=True → cap_rates.new.sqlite):** usable villa cells **3 → 16**
(reliable **2 → 6**, indicative **1 → 10**); 3458 calibratable listings (vs ~1214); 60 communities;
0.8% outlier rejection. Reliable now incl. **المعمورة 56 400-600 (6.04%/4.83%)** and **امريخ الجنوبي
400-600 (6.44%)** (the Marikh over-anchor area). Villa-6 المعمورة 600-900 stays fallback — but now
sale-side-limited (MoJ villa n=7), not rent-side; 400-600 reliable + 600-900 rent-consistent ⟹
income band ~5.3–6% ⟹ ~3.2–3.6M (converges with §8/§9, below the 3.8M condition-blind comparison).

**Honest residual:** the remaining tail is per-bracket **MoJ sale** depth (a different source), not
PF rent depth — Dependency #2 (yield) is now strong enough for the §6 triangulation. Long-tail tiny
communities beyond PF's serving cap aren't enumerated (too few listings to form a reliable cell).

**NEXT (still gated):** ship the deepened yield-data **with** the §6 income-triangulation wiring
(income → villa headline + an a18/override-aware `_lookup_calibrated_cap_rate`) as ONE Gate-2 step —
the §9 disposition ("ship yield-data + §6 wiring together"). Until «go»: DB-swap + Heroku deploy HELD;
the value-invariant code is committed origin-only as a backup (§9 precedent).

## 11. SHIPPED — yield-data STANDALONE (the §9/§10 "broader-coverage" branch) — Heroku v172 (2026-06-07)

**Status:** the deepened per-area yield-data is **LIVE** (Sprint 2.22.0b.5, Heroku **v172**, commit `0015600`
split `148ef34`, CHANGELOG_v86, Session_Log §20.39). On Anas's «go», the §10 "ship together with §6" plan was
**revised to STANDALONE** — per-area (§10) delivered exactly the **broader coverage** §9's disposition allowed
(«ship WITH broader coverage **and/or** §6»), so §9's own «and/or-broader» branch became satisfiable without §6.
Clean #38 split: ship the value-invariant **data** correction now; §6 (the headline-wiring) is the separate next
Gate-2.

**What's live.** `cap_rates.sqlite` swapped → **16 usable villa cells** (6 reliable + 10 indicative). The villa
**income cross-check** now uses calibrated per-area net yields (vs the flat 4% fallback) **when income fires + a
usable (area, bracket) cell matches**. **HEADLINE value-invariant** (income is downstream of `primary['value']`;
`_analyze_reconciliation` is status-only) — live smoke 4 anchors byte-identical [2.4M/5.4M/2.6M/refusal].

**🔴 Bracket-gated (the honest footprint, Rule #36).** Most usable cells are **400-600**; a villa sees the
calibrated rate only if its (area, plot-bracket) hits a usable cell. Standard anchors in 600-900 (e.g. Marikh
54/541/6) correctly STAY 4% fallback; villa-6 56/647/6 (المعمورة) shows no income block at all (no auto rent
reference). **B confirmed LIVE** via Marikh forced to 400-600 (`override_land_area=500`) → «معدل رسملة معايَر
5.2% (عينة n=46، reliable)» source=calibrated. This bracket-gating is precisely what **§6 overcomes** (income
drives the headline regardless of the income-block trigger).

**The §6 lookup fix is NOT a blocker for the standalone ship** (recon): `_lookup_calibrated_cap_rate` matches
GIS↔GIS on the stored `district_aname` (= the GIS aname, not the a18 key), so override areas resolve already.
The a18/override-aware lookup is a §6 robustness item.

**Soft Gate 3.** The broad DoD walk caught a pre-existing red (`test_sprint_2p19p1_polish.py`, latent at `ba47835`
— the R7 calibrator-interface refactor broke its stale mock; the R7 prep never ran the broad walk). Repaired the
mock to the real `resolve_key`/`medians_for_key` interface + `property_type_raw` (test-only; restores Fix#4/Fix#5
coverage).

**NEXT = §6 income-triangulation (the ball, Claude.ai).** Income SETS the villa headline + the a18/override-aware
lookup + MUC on divergence, as ONE Gate-2 — **needs a signed brief**. The deepened yield-data is now the
strong-enough Dependency #2 it needs (§8/§9/§10). The «التقدير السوقي» term remains PROVISIONAL.
