# PHASE 0 / brief — Sprint 2.22.0b.9 — QARS property-basis panel

> **Status:** recon complete, build authorized by Anas «go — افعل الأصوب» (2026-06-08).
> **Class:** value-invariant surfacing (display-only). **NOT Gate-2** (no valuation/output-value
> change). Push = Gate-1 (explicit «go»).
> **Engine:** `thammen-sprint2p22p0b9-qars-basis-panel` / SPRINT_TAG `2.22.0b.9`.

## 1. Motivation — a real bank valuation

Anas supplied a real licensed-valuer report (شركة المنارة → بنك قطر الدولي الإسلامي, **TD 93317**,
property **56/647/6** بو هامور, the V001 reference villa). It is a **Cost Approach (DRC)** report:
land (652 m² = 7,018 ft² × **350 QAR/ft²** = **2,456,345**) + depreciated building (**1,143,800**) =
**3,600,145** fair / 3,240,145 forced-sale. Its land component matches our B-1 `value_floor`
(2,456,736) to **0.016%** — strong external validation.

The report prominently shows three traceability fields we do not surface: **الرقم المساحي (PIN)**,
**رقم الكهرباء**, **عمر البناء**. Anas asked to add these (+ any others) to every evaluation.

## 2. Recon — the decisive finding (and a self-correction)

A live probe of QARS_Point (`outFields='*'`, the field set `find_property` already requests) for
5 anchor properties:

| field | source | sample coverage | 56/647/6 value vs report |
|---|---|---|---|
| PIN | `PIN` | 5/5 | **56101583 == report 56101583** ✓ |
| **رقم الكهرباء** | **`ELECTRICITY_NO`** | **5/5** | **140502 == report 140502** ✓ |
| water | `WATER_NO` | 4/5 | 104503 (bonus) |
| age floor | `SURVEYED_DATE` | 5/5 | survey 2009 → ≥17y ≈ report "18 سنة" ✓ |

**Self-correction (Rule #36 / re-examine on evidence):** an earlier assessment claimed رقم الكهرباء
"has no source, breaks E17, user-entered only." **WRONG** — `ELECTRICITY_NO` is a QARS_Point field,
already fetched, 5/5 populated, exact-matches the bank report. All three asks are **auto-fetchable
from the SAME QARS call we already make → zero new GIS round-trips, zero latency.**

`PropertyLocation` **already captures** `electricity_no`/`water_no`/`qtel_id`/`pin` (qatar_gis.py:172,
find_property:1365-1367) but they are **not surfaced** in the response. `SURVEYED_DATE` is **not
captured** (1 field + 1 line to add).

## 3. Building age — the cheap path beats the slow detector

The imagery age-detector (`qatar_gis.estimate_construction_year_smart` + `building_age_cache.py`) is
**slow and coarse** — measured on the 62-PIN cache: first-time **median 11s, up to 23s** (naive scan
30-60s — why Sprint 2.15 live was rolled back), and **precise (±5y) only 27%**, undetermined **42%**.

`SURVEYED_DATE` gives an **instant, reliable FLOOR** ("building existed by survey ≈ construction era",
Rule #10: a QARS number is assigned after completion). All 5 anchors surveyed 2009-2011 → all >10y →
the 10-Year-Rule question ("old villa?") is answered for free. The exact construction year (imagery)
remains a future luxury, best **pre-computed offline for the invite-only beta cohort**.

## 4. 🔴 Value-invariance boundary (the one hard rule of this sprint)

The displayed age is a **separate display-only key** `building_age_estimate` derived from `SURVEYED_DATE`.
It **MUST NOT** populate `user_inputs.building_age_years` (the user-supplied input that feeds the b4
condition/age levers + age-rent — touching it = Gate-2 valuation change). Keeping them separate keeps
the 4 anchor headlines **byte-identical** → this sprint stays value-invariant / display-only.

## 5. Injection map (DRY)

- **qatar_gis.py:** `PropertyLocation += surveyed_date`; `find_property` captures
  `a.get('SURVEYED_DATE')`; the 2 PIN-path constructions (full_property_lookup, evaluate_unified) set
  `surveyed_date=None`.
- **evaluate_property.py:** `raw_report` (:1804) += `electricity_no`/`water_no`/`surveyed_date` from
  `report.location`.
- **evaluate_unified.py:** new pure helper `_build_property_basis(pin, electricity_no, water_no,
  surveyed_date)` → `{pin, electricity_no, water_no, building_age_estimate|None}`. Injected at:
  - main path `_build_unified_output` (:4919-4924, beside the gps-from-rpr block);
  - fast paths via `_enrich_fast_context(loc, plot)` return + a `_ctx`-pick in the 5 fast builders.
- **index.html:** render `property_basis` in the b2.3 `showConfirm` basis-review panel (the
  "review the GIS-fetched basis" surface) + the results basis.

## 6. Verification plan

- Isolated `test_sprint_2_22_0b9.py`: `_build_property_basis` (age floor math, None handling,
  value-invariance: never emits `building_age_years`); `PropertyLocation.surveyed_date` present;
  find_property captures it (mock).
- DoD: aggregator 392 / security 15 / surface 45 / broad walk.
- Local E2E: 56/647/6 → `property_basis` {pin 56101583, electricity 140502, age_floor ≥17}; **4 anchors
  valuation byte-identical** (value-invariant proof).
- R14 (node absent → real Chromium): panel renders, 390×844 no overflow, 0 console errors.
- Live two-lane smoke (browser-UA curl, #61) after Gate-1 «go».

## 7. Deferred (Rule #42)

- Wiring `SURVEYED_DATE` age → valuation (depreciation / 10-Year-Rule / age-rent) = a **separate
  Gate-2 sprint** (it unblocks the E22 inert levers + feeds the §20.9 cost-triangulation).
- Exact construction year via imagery, pre-computed offline for the beta cohort.
- `QTEL_ID` sparse (2/5) → omitted.
