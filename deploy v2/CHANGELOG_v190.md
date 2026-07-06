# CHANGELOG v190 — Sprint 2.22.0b.109 «توحيد معايير النطاق الجغرافي لصفقات الأراضي» (S4 — the land geo residential-filter)

**Engine:** `thammen-sprint2p22p0b109-land-geo-residential-filter` · **SPRINT_TAG** `2.22.0b.109`
**Date:** 2026-07-06 · **Files:** `geo_reference_v2.py` (one clause), `evaluate_unified.py` (the 2 version lines) (+ `test_sprint_2_22_0b109.py`, `docs/GATE2_b109_land_geo_filter_blast_radius.md`)
**Class:** 🔴 **Gate-2 — VALUE-AFFECTING on the LAND geo path** (the geo-widened land headline can move; the
comparable-grid display gets cleaned). **VILLA byte-identical.** `api.py` + `index.html` untouched → R14 N/A
by construction (§20.18 precedent). **DEPLOY GATED on the PO signing the before/after table below.**

---

## 2. Why (the geo↔bracket asymmetry — fact #3)

b102 filtered the `moj_reference` LAND bracket pool residential-only (a residential-land subject must be
compared with residential land; apartment-development/commercial land has a different highest-and-best-use +
buyer pool — RICS VPS 3 / IVS 103 comparability + IVS 104 data selection). But `geo_reference_v2`'s
`_get_area_transactions` applied the same `usage_filter._is_residential_usage` to the VILLA pool **only**
(`:348`) — the geo LAND pool (the geo-widened land headline + the comparable-grid display) still mixed
apartment-development/commercial land. S4 closes that asymmetry with the **exact b102 sibling** clause.

## 3. What this patch does (one clause)

`geo_reference_v2._get_area_transactions:348` — `if category == 'villa'` → **`if category in ('villa', 'land')`**
`and not _is_residential_usage(r): continue`. Now the geo LAND pool is residential-only, mirroring
`moj_reference` (already b102-filtered on both). Thin residential cells (n<10) fall to the existing
indicative tier (reliability disclosed). 100%-non-residential downtown land → 0 residential comps → honest
refusal (also classifier-rejected). VILLA byte-identical (the villa branch of the clause is logically
unchanged: for `category=='villa'`, `'villa' in ('villa','land')` == the old `'villa'=='villa'`, same
`_is_residential_usage` test).

## 4. Gate-2 before/after (the PO's sign-off artifact)

MoJ 24-month window (latest 2025-12-31). Metric = the land POOL **ppm² median** (per the b101 lesson, the %
change in the pool median == the % change in the headline for a geo-widened-land subject; for a subject whose
PRIMARY bracket is sufficient, b102 already governs the headline and S4 only cleans the comparable-grid display).

**36 of 115 land areas** carry a non-residential-contaminated geo pool. Direction is **always de-inflating or
neutral** (residential ⊆ all — the filter only ever removes non-comparable land). Headline movers (geo-widened
land only):

| area | n_all → n_res | pool ppm² before → after | Δ | after-tier |
|---|---|---|---|---|
| الوعب (the PO's fixture) | 56 → 25 | 8,205 → 4,643 | **−43.4%** | reliable (n=25) |
| مدينة خليفة الجنوبية | 12 → 7 | 4,404 → 3,889 | −11.7% | THIN |
| نعيجة 43 | 13 → 12 | 3,476 → 3,338 | −4.0% | reliable |
| المطار العتيق | 45 → 30 | 3,881 → 3,750 | −3.4% | reliable |
| نجمة / فريج كليب / فريج عبد العزيز / … | → 0 | (100% non-residential) | REFUSE | honest refusal |
| الخور / الوكير / ام صلال علي / غرافة الريان | ~unchanged | ~0% | ~0% | reliable |

Full 36-row table: `docs/GATE2_b109_land_geo_filter_blast_radius.md`. الوعب's −43% confirms the b102-measured
contamination (b102 moved its primary-bracket headline 7.1M → 5.7M; the geo pool is even more contaminated).
Every move REMOVES non-comparable land — the RICS-correct direction.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b109.py` **15/15** (E14, the REAL `_get_area_transactions`: the filter fires on
  land [الوعب 56→25] · removes-only · survivors == residential subset · **villa byte-identical** [real ==
  residential-subset, unchanged] · downtown → 0 → refuse · clean areas ~unchanged · compound untouched) ·
  py_compile OK.
- **b102 sibling** `test_sprint_2_22_0b102_land_residential.py` **20/20** (the villa/bracket path stays green).
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **164/164
  ALL GREEN** — **ZERO re-points** (the clause change pins no prior test string).
- **Villa 5-fixture byte-gate: byte-identical BY CONSTRUCTION** (the villa branch is unchanged; the change
  adds land only). A live two-lane smoke re-confirms it at deploy time (held).
- **R14 N/A** — `index.html` + `api.py` git-confirmed untouched (§20.18 backend-only precedent).

## 6. Deployment — 🔴 GATED

- **This is Gate-2 value-affecting on the land path. It is committed LOCALLY only. Deploy is GATED on the PO
  signing the §4 before/after table.** On sign-off: `git push origin master` FIRST, then
  `git subtree push --prefix "deploy v2" heroku master` (§20.112), then a two-lane live smoke = the 5-fixture
  villa byte-gate byte-identical + a live الوعب land before/after (7.1M-class → the residential figure).

## 7. Verification curl (post-deploy, after sign-off)

- `/api/health` → `3.1.0-sprint2.22.0b.109`.
- the 5-fixture villa byte-gate byte-identical to v275 (browser-UA #61).
- a land subject in a contaminated area (e.g. الوعب) → the geo/grid land comps are residential-only.

## 8. What's NOT in this patch

- No villa change (byte-identical). No `moj_reference` change (b102 already filtered the bracket pool). The
  trend filter (compute_trend still includes 'dwelling') = **S5 (b110)**. The condition modal = **S7 (b111)**.
