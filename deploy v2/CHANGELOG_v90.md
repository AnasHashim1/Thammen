# CHANGELOG v90 — Sprint 2.22.0b.9 (QARS property-basis panel)

**Engine:** `thammen-sprint2p22p0b9-qars-basis-panel` · SPRINT_TAG `2.22.0b.9` · api/health `3.1.0-sprint2.22.0b.9`
**Date:** 2026-06-08
**Files:** `qatar_gis.py` · `evaluate_property.py` · `evaluate_unified.py` · `index.html` · `test_sprint_2_22_0b9.py` (new) · `docs/PHASE0_2p22p0b9_qars_basis_panel.md` (recon)
**Class:** value-invariant surfacing (DISPLAY-ONLY). **NOT Gate-2** (no valuation/output-value change). Push = Gate-1.

## 1. Why this matters

A real licensed-valuer bank report (شركة المنارة → بنك قطر الدولي الإسلامي, **TD 93317**, property **56/647/6**)
prominently shows three traceability fields Thammen did not surface: **الرقم المساحي (PIN)**, **رقم الكهرباء**,
**عمر البناء**. The PO asked to add these (+ any others) to every evaluation, to make Thammen's output read like
a professional bank valuation.

## 2. Root cause / recon (the decisive finding + a self-correction)

A live QARS_Point probe (`outFields='*'` — the field set `find_property` already requests) over 5 anchors:
all three are **already auto-fetchable from the SAME QARS call we already make** — zero new GIS round-trips.

- `PIN` — already in `PropertyLocation`, not surfaced. 56/647/6 → **56101583 == the report's الرقم المساحي**.
- **`ELECTRICITY_NO`** — already captured by `find_property`, not surfaced; **5/5 populated**. 56/647/6 →
  **140502 == the report's رقم الكهرباء** (exact). *(A prior assessment wrongly said electricity "has no
  source / breaks E17" — the evidence overturned it; Rule #36.)*
- `WATER_NO` — bonus, 4/5.
- `SURVEYED_DATE` — **not captured** (1 field + 1 line). 56/647/6 surveyed 2009 → **≥17y ≈ the report's "18 سنة"**.

The imagery age-detector (`building_age_cache.py`) is slow + coarse (measured 62-PIN cache: first-time median
11s / up to 23s; precise ±5y only 27%; that's why Sprint 2.15 live was rolled back). `SURVEYED_DATE` gives an
**instant, reliable age FLOOR** (the QARS address point is surveyed at/after completion, Op. Rule #10) — enough
for the practical "old villa?" question without the detector.

## 3. What this patch does

- **qatar_gis.py:** `PropertyLocation += surveyed_date: Optional[int] = None` (default None → PIN-path / legacy /
  mock constructions unaffected); `find_property` captures `a.get('SURVEYED_DATE')`.
- **evaluate_property.py:** `raw_report` (the serialized property report) += `electricity_no` / `water_no` /
  `surveyed_date` from `report.location`.
- **evaluate_unified.py:** new pure helpers `_building_age_estimate(surveyed_date)` (epoch-ms → age FLOOR, honest
  `≥` framing, None on missing/bad/future) + `_build_property_basis(pin, electricity_no, water_no, surveyed_date)`
  → `{pin, electricity_no, water_no, building_age_estimate|None}`. Injected at the main path
  (`_build_unified_output`, beside the gps-from-rpr block) **and** the 5 fast-path builders (via the shared
  `_enrich_fast_context`). ENGINE_VERSION/SPRINT_TAG → b9.
- **index.html:** `pbRows(pb)` helper (reuses the proven `ri()`/`.rg` rows) rendered in BOTH the b2.3
  `showConfirm` basis-review card and the results report card (so valuer + refusal paths, which skip confirm,
  still get it). `api.py` UNTOUCHED.

### 🔴 Value-invariance boundary (the one hard rule)
The displayed age is a SEPARATE display-only key `building_age_estimate`. It is **NEVER** written into
`user_inputs.building_age_years` (the user-supplied input that drives the b4 condition/age levers + age-rent —
touching it would be a Gate-2 valuation change). The 4 standard anchors stay byte-identical → display-only.

## 4. Verification — empirical evidence

- py_compile 3/3. Isolated `test_sprint_2_22_0b9.py` **29/29** (production helpers per E14; age-floor math; None
  handling; **value-invariance contract: the block never carries `building_age_years`/`age_source`/`amount`**;
  `PropertyLocation.surveyed_date` present + defaults None; `find_property` captures SURVEYED_DATE via a stubbed
  `_qars_query`; index.html wiring).
- DoD: aggregator **392** (ALL COUNTS MATCH) · security **15/15** · surface-honesty **45/45** · broad walk
  **78/78** (77→78 = the new test, clean, 255s, no flake).
- **Local E2E (real engine, live GIS) — value-invariant + correct data:**
  | PIN | amount | vs b8 | property_basis |
  |---|---|---|---|
  | 56/565/21 | 2,400,000 | byte-identical | pin 56090294 · elec 1120583 · age ≥15y |
  | 54/541/6 | 5,400,000 | byte-identical | pin 54360025 · elec 161418 · age ≥17y |
  | 55/296/13 | 2,600,000 | byte-identical | pin 55744587 · elec 138640 · age ≥17y |
  | 52/903/90 | None (refusal) | byte-identical | pin 52200100 · elec 76787 · age ≥17y |
  | **56/647/6** | 3,800,000 | byte-identical | **pin 56101583 · elec 140502 · age ≥17y (= the bank report)** |

  `user_inputs.building_age_years=None` on all → the age estimate did NOT leak into the valuation input.
- **R14 (real Chromium, node absent):** 0 console errors; `pbRows` defined + graceful on null/partial;
  `showConfirm` + `show` render the basis rows (pin/elec/age visible); **no overflow at 390×844**
  (docScrollW=390, widest value cell right=331<390).

## 5. Deployment (Gate-1 — explicit «go» required)

```
cd /d "C:\Thammen\deploy v2"
git add qatar_gis.py evaluate_property.py evaluate_unified.py index.html test_sprint_2_22_0b9.py docs/PHASE0_2p22p0b9_qars_basis_panel.md CHANGELOG_v90.md
git commit -m "Sprint 2.22.0b.9 (QARS property-basis panel): surface PIN + رقم الكهرباء + water + building-age floor (from SURVEYED_DATE) — value-invariant, 4 anchors byte-identical"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy, browser-UA per #61)

```
curl -s https://thammen.qa/api/health
curl -s -X POST https://thammen.qa/api/evaluate -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":647,\"building\":6}"
# expect: valuation.amount 3,800,000 (unchanged) + property_basis {pin 56101583, electricity_no 140502, building_age_estimate ≥17y}
```

## 7. What's NOT in this patch (deferred — Rule #42)

- **Wiring `SURVEYED_DATE` age → valuation** (depreciation / 10-Year-Rule / age-rent) — a separate **Gate-2**
  sprint; it unblocks the E22 inert age levers + feeds the §20.9 cost-triangulation.
- **Exact construction year via imagery** — slow (11-23s) + coarse (27% precise); best **pre-computed offline
  for the invite-only beta cohort**, then served instant (<10ms, permanent).
- `QTEL_ID` (sparse 2/5) — omitted. Electricity-number is shown but NOT verified beyond GIS.
