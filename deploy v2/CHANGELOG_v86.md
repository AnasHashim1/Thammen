# CHANGELOG v86 — Sprint 2.22.0b.5 (R7 villa-yield calibration data ship)

**Engine:** `thammen-sprint2p22p0b5-villa-yield-calibration` · **SPRINT_TAG** `2.22.0b.5`
**Date:** 2026-06-07 · **Heroku:** v172 (pending push) · **Prior:** v171 / `thammen-sprint2p22p0b4-condition-value-axis`
**Gate:** 🔴 Gate-1 (Heroku push) + 🔴 Gate-2 (user-visible income cross-check changes for villas) — both on explicit Anas «go».
**Files changed:**
- `cap_rates.sqlite` — swapped to the per-area rebuilt DB (Sprint 2.19.2 R7; built + verified in `ba47835`, was the gitignored `cap_rates.new.sqlite`).
- `evaluate_unified.py` — ENGINE_VERSION + SPRINT_TAG only (lines 44-45). **No logic change.**
- `tests/test_sprint_2p19p1_polish.py` — stale-mock repair (see §3b). **Test-only.**
- `CHANGELOG_v86.md` — this file.

> The R7 connector + calibrator code (`cap_rate_calibrator.py`, `propertyfinder_client.py`, `tests/test_cap_rate_calibrator*.py`)
> was already committed at `ba47835`/`85d6922` (value-invariant build-time tools, not in the runtime path). This ship **swaps the DB
> they produced** + bumps the version + repairs one stale 2.19.1 test that the R7 refactor broke.

---

## 1. Why this matters

The villa **income cross-check** (`_build_income_crosscheck`, shown whenever a villa eval has rent — user-supplied OR an auto-fetched
municipality rent reference) used a flat **4.0% hardcoded** cap rate for almost every villa, because the committed `cap_rates.sqlite`
(Sprint 2.19, 2026-05-20) had only **1 reliable + 2 indicative** villa cells. A flat 4% understates real Qatar villa yields (≈4.7–7%
gross) and produces an income value that does **not** flag the condition-blind comparison's R7 over-anchor.

This ship replaces that DB with the **per-area (PropertyFinder `?l=<locationId>`) rebuilt calibration** — **16 usable villa cells
(6 reliable + 10 indicative)**, a18-reconciled denominator, furnished-consistent rent medians, standalone-villa-only pool — so the
income cross-check, when shown, uses the **area's real per-stratum yield**. This is the data half (Dependency #2, §9/§10 of
`docs/DECISION_income_crosscheck_villa_R7.md`); the §6 step (income SETS the headline + an a18/override-aware lookup) is separate, later.

## 2. What this patch does

**Data (the swap).** `cap_rates.sqlite`: 125→200 rows; **villa {reliable 1→6, indicative 2→10, fallback 106→171}**; +`calibration_meta`
(outlier counters). Reliable now includes the two R7-critical areas — **المعمورة 56 400-600 (6.04% gross / 4.83% net, villa-6's area)**
and **امريخ الجنوبي 400-600 (6.44% / 5.16% net — the Marikh over-anchor area)** — plus العب / عين خالد / المطار العتيق / ام صلال علي.
Every usable cell carries a non-None `stock_class` (no Rule E4 / Fix#4 breach; the old live `الغرافة 0-400` stock=None breach is gone).

**Lookup is correct as-is (no §6 code needed).** `evaluate_unified._lookup_calibrated_cap_rate` maps `standalone_villa→'villa'`, brackets
by plot, and matches `_cap_area_token(subject GIS aname) == _cap_area_token(stored district_aname)`. The calibrator stores the **GIS aname**
in `district_aname` (e.g. «امريخ الجنوبي», not the a18 key «مريخ»), so the match is **GIS↔GIS** and resolves without the §6 override fix.
`_cap_area_token` strips the trailing zone-number + «ال» + folds hamza, so sub-zone subjects («المعمورة 56» ↔ «المعمورة») resolve too.

**Value-invariant on the headline.** `_build_income_crosscheck` receives `primary_value=primary['value']` (the headline is computed FIRST
and passed IN); income feeds only (a) the income cross-check display and (b) `_analyze_reconciliation`, which is a **pure status reporter**
(returns a convergence/divergence label, never a value). So swapping the cap-rate DB **cannot move any headline**.

**Engine version only** in `evaluate_unified.py` (b4→b5). `api.py` UNTOUCHED.

### 3b. Stale-test repair (Soft Gate 3, Rule #39 — test-only)

`tests/test_sprint_2p19p1_polish.py` was **red at `ba47835`** (latent — the R7 prep ran only the calibrator suites, never the 74-file broad
walk). Root cause: the R7 calibrator refactor changed the `MojSaleIndex` interface to `resolve_key()` + `medians_for_key()` and added a
standalone-villa gate (`property_type_raw`), but this older 2.19.1 file still injected the removed `villa_and_land_median()` and a mock
listing with no `property_type_raw` → `calibrate()` produced **0 rows** → 5 failures incl. a crash. Repaired the mock to the **real**
interface (so it exercises the production `calibrate()` path — Rule #40 / E14) + added `property_type_raw="Villa"` to `_listing`. This
**restores** coverage of the Fix#4 (Rule E4: no-land-median villa → fallback) + Fix#5 (outlier counter) invariants — it does not weaken them;
the invariants are still enforced in the calibrator (lines 666-668). Not caused by this ship (the test uses a temp DB, not the swapped one).

## 3. Root cause (data thinness)

§9 measured it: the national `villas-for-rent` PropertyFinder feed serves ~50 pages (~1214 villa rentals over 158 cells ≈ 8/cell), so only
the biggest areas reached n≥20. The §5-audited per-area connector (`villas-for-rent.html?l=<community_id>`, community ids harvested from each
listing's `location_tree`) fetches **per community** → 3458 calibratable listings, lifting usable villa cells 3→16. Full audit:
`docs/PHASE0_R7_perarea_connector.md`.

## 4. Verification — empirical evidence (measured 2026-06-07, `PYTHONIOENCODING=utf-8`)

**DoD (re-measured, not trusted from docs — Rule #58):**
- aggregator `run_sprint_2p22p0a_suite.py` = **392/392 (MATCH)**
- security `test_sprint_2p16p17_security.py` = **15/15**
- surface-honesty `test_sprint_2p22p0a3_surface_honesty.py` = **45/45**
- broad `2p22p0_pre/run_regression_2p22p0a.py` = **74/74 files, 0 failed** (193.3s; +1 vs b4's 73 = the R7 calibrator test now in the walk)
- `tests/test_cap_rate_calibrator.py` = **59/59** · `tests/test_cap_rate_calibrator_r7.py` = **42/42**
- `tests/test_sprint_2p19p1_polish.py` = **41/41** (after the §3b repair; was 36/41 + crash before)

**DB swap verified:** schema-compat (live SELECT cols all present) PASS; villa {reliable 6, indicative 10}; `district_aname` = GIS aname;
no stock_class=None among usable cells.

**Mechanism (real functions, GIS-free):** `_lookup_calibrated_cap_rate('standalone_villa', 'امريخ الجنوبي', 500)` → **0.05155 net,
calibrated, reliable, n=46**; المعمورة 56 → 0.04833 n=69; العب → 0.047 n=114; عين خالد → 0.05465 n=50; control بو هامور → None (fallback);
المعمورة 56 @700m² (600-900) → None (bracket granularity). `_build_income_crosscheck(rent=16000, area='امريخ الجنوبي')` → income_value
**2,867,895** @ calibrated 5.16% (vs 4% hardcoded for an unknown area); `rent=None` → income block **None** (no-rent flow unaffected).

**`/api/health` reader on the new DB:** `total_cells 200`, `{reliable 6, indicative 10, fallback 184}`, `outliers_rejected_total 27`,
`calibratable_listings_seen 3458`, `rate 0.78%` — no crash (the additive `calibration_meta` populates the previously-null counters).

**Headline value-invariance (live baseline + code):** live deployed b4 anchors confirmed 2.4M / **5.4M (54/541/6, district «امريخ الجنوبي»,
income 4.0% hardcoded)** / 2.6M / refusal. Post-swap, only the income cross-check + reconciliation label move; headlines hold (income is
downstream of `primary['value']`; reconciliation is status-only).

## 5. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add cap_rates.sqlite evaluate_unified.py tests/test_sprint_2p19p1_polish.py CHANGELOG_v86.md
git commit -m "Sprint 2.22.0b.5 (R7): ship per-area villa-yield calibration DB (3->16 usable cells); income cross-check uses real per-area yields; headline value-invariant; +stale 2.19.1 mock repair"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
(If the subtree push is rejected for divergence, use the named-temp-branch force procedure — Operational #43.)

## 6. Verification curl (post-deploy, browser-UA per Rule #61)

```
curl -s -A "Mozilla/5.0 ... Chrome/120.0.0.0 Safari/537.36" https://thammen.qa/api/health
  → engine_version thammen-sprint2p22p0b5-villa-yield-calibration; calibration total_cells 200, reliable 6
curl -s -A "Mozilla/..." -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"
  → "amount":5400000 (UNCHANGED) + income cap_rate_label «معدل رسملة معايَر 5.2% (… reliable)» (was 4.0% نموذجي)  ← the B effect
curl ... 56/565/21 → 2,400,000 byte-identical · 55/296/13 → 2,600,000 byte-identical · 52/903/90 → refusal byte-identical
```

## 7. What's NOT in this patch (scope boundary)

- **§6 headline-triangulation** — income SETTING the villa headline + an a18/override-aware `_lookup_calibrated_cap_rate`. Separate, later
  Gate-2 (needs a signed Claude.ai brief). This ship is **data + cross-check only**; the headline is untouched.
- **No `api.py` / `index.html` / valuation-logic change.** No new input fields.
- **The income cross-check still requires rent** (user-supplied or municipality reference) to appear — unchanged behavior.
- **MoJ sale-side depth** (the remaining tail — e.g. المعمورة 600-900 villa n=7) is a different source, out of scope.
