# Phase-0 §5 Audit — PropertyFinder per-area (locationId) villa-rent connector

**Date:** 2026-06-07 · **Sprint:** 2.19.2 (R7 income cross-check) — Dependency #2 depth lever.
**Status:** §5 external-endpoint audit **COMPLETE + CLEAN**; connector **BUILT + tested**;
the deepened DB (`cap_rates.new.sqlite`) is **HELD at 🔴 Gate-1 (Heroku push) + 🔴 Gate-2
(it changes the user-visible income cross-check)** — value-invariant until an explicit «go».
**Parent:** `docs/DECISION_income_crosscheck_villa_R7.md` §8/§9 (the §9 disposition named this
as the NEXT unit: "per-area PF depth (locationId search, §8 lever) — own §5 audit").

Engine UNTOUCHED (b4/v171). The calibrator + connector are **build-time tools, not in the
runtime path** (`api.py`/`evaluate_unified.py` do not import them at request time), and the
live `cap_rates.sqlite` is **not** swapped — so the committed code is provably value-invariant.

---

## 1. Why (the bottleneck this closes)

§9 measured the binding constraint: the villa **yield** is "THE make-or-break and is currently
unreliable" — only **1 reliable + 2 indicative villa cells**. Root cause (§9 honest residual):
the calibrator's national crawl (`collect_rentals`) hits PropertyFinder's **~50-page serving
cap** on the ~3.4k-listing national `villas-for-rent` feed → ~1214 unique villa rentals spread
over 158 cells ≈ **~8 listings/cell** → only the biggest areas reach the n≥20 reliable gate.
The §8 audit had observed far larger **per-area** inventories (المعمورة 93, أبو هامور 121, …),
so the lever is to fetch **per community** rather than nationally — "needs the `?l=<locationId>`
discovery." This audit found that mechanism.

## 2. §5 audit — method (file-based probes, Rule #34 / #33 / §21.6)

Four read-only probes (gitignored `probe_*.py`; PF reachable from this machine — the same host
the §9 rebuild crawled from). No DB writes, polite delays.

- **Phase A** `probe_pf_locationid.py` — dump the national page `__NEXT_DATA__` structure +
  raw listing `location` objects.
- **Phase B** `probe_pf_area_depth.py` — harvest the community map; test `filter[locations_ids][]`.
- **Phase C** `probe_pf_urlform.py` — battery of candidate per-area URL forms.
- **Phase D** `probe_pf_lockdown.py` — verify the winning form is correct + measure depths + paginate.

## 3. Findings (measured ✓)

### 3.1 The URL form — scalar `?l=<community_id>` is the ONLY honored one
Battery result for Al Maamoura (community id 68), `total_count` national = **3477**:

| candidate | result |
|---|---|
| `villas-for-rent.html?l=68` | **`total_count=103`** ✅ (area-only) |
| `?filter[locations_ids][]=68` | 3477 (ignored) |
| `?l[]=68` / `?locations_ids[]=68` / `?filter%5B…%5D=68` | 3477 (ignored) |
| `/rent/al-maamoura/villas-for-rent.html` (+ 2 slug-path forms) | 404 |
| `/en/search?c=2&t=2&l[]=68` | 404 |

So **`{villas-for-rent.html}?l=<id>`** (scalar), with `&page=N` appended for pagination. This
matches the existing connector's `_build_page_url` (`sep = "&" if "?" in base_url else "?"`).

### 3.2 Community id discovery — from `location_tree`, no separate endpoint
Every listing carries `property.location_tree` = a clean hierarchy:
`level 0 CITY (Doha=9) · level 1 COMMUNITY (Al Maamoura=68, Abu Hamour=79, …) · level 2
SUBCOMMUNITY`. The **community id** matches the `?l=` filter and is the granularity closest to
a GIS district. So the id↔name↔slug map is **harvested from the national crawl's trees** — zero
new endpoints, no autocomplete API.

### 3.3 `?l=68` IS Al Maamoura (correctness)
Phase D: of page-1 listings, **27/27 carry community 68 in their tree** and **27/27 GPS sit at
the Al Maamoura centroid**. The filter is correct; GIS-from-GPS binning stays authoritative (the
id only bounds the crawl — PF location names are never trusted, per the connector's design).

### 3.4 Depth gain (villa-rent inventory per community) — the payoff
`?l=<id>` `total_count` vs the ~8/cell the national crawl surfaces:

| community | id | per-area total | community | id | per-area total |
|---|---|---|---|---|---|
| اللؤلؤة (The Pearl) | 16 | **325** | الوعب (Al Waab) | 107 | **259** |
| عين خالد (Ain Khaled) | 24 | **260** | الخيسة (Al Kheesa) | 17 | **248** |
| أبو هامور (Abu Hamour) | 79 | **187** | المريخ (AlMuraikh) | 80 | **151** |
| المعمورة (Al Maamoura) | 68 | **103** | الغرافة (Al Gharrafa) | 47 | **89** |

### 3.5 Pagination retrieves the FULL area
Al Maamoura paginated 5 pages → **103/103 unique ids** (dedupe by id). Each community's total is
far below the ~1250 (50-page) cap, so per-area fetch reaches the area's **true n** — exactly what
the national feed truncates. **No blocker.**

## 4. What was built (value-invariant; national path preserved)

- **`propertyfinder_client.py`** (additive):
  - `_fetch_raw_listings()` (raw, pre-normalize — `fetch_listings_page` now delegates to it; DRY).
  - `fetch_rentals(..., location_id=None)` — when set, builds `?l=<id>` (back-compat: default
    `None` = national, byte-for-byte; proven by the "national path has no `?l=`" test + 59/59 base suite).
  - `community_nodes(raw_listing)` + `community_map(category, max_pages, …)` — harvest level-1
    COMMUNITY id↔name↔slug from the national feed (stops on the 404 serving cap, like `fetch_rentals`).
- **`cap_rate_calibrator.py`** (additive):
  - `collect_rentals_per_area(...)` — harvest map → deep-fetch each community by id → dedupe by
    listing id → fold in the light compound pull.
  - `calibrate(..., per_area=False)` — `per_area=True` uses the per-area collector; default
    `False` keeps the national-only path unchanged (reversible).
- **`tests/test_cap_rate_calibrator_r7.py`** — +13 tests (community_nodes / `?l=` URL form +
  back-compat / community_map + 404-break / per-area dedupe). Real functions, mocked network (E14).

**Verification:** py_compile OK · R7 **42/42** (29 prior + 13 new) · base calibrator **59/59**.

## 5. Coverage gain (per-area rebuild → `cap_rates.new.sqlite`) — measured ✓

Full live per-area crawl, 2026-06-07 (`per_area=True` → `cap_rates.new.sqlite` ONLY; the live
`cap_rates.sqlite` is untouched — git-confirmed). 60 villa communities discovered, **3458**
calibratable listings (vs ~1214 national), outlier rejection **0.8%** (clean, ≪ the 10% WARN).

| usable villa cells | national v1 (§9) | **per-area v2** |
|---|---|---|
| reliable (n≥20, eff) | 2 | **6** |
| indicative (10–19) | 1 | **10** |
| **total usable** | **3** | **16** (5.3×) |
| villa cells total | 109 | 187 |

**The 16 usable villa cells** (a18 denominator + furnished-consistent + E4-stratified):
- **reliable (6):** العب 400-600 (5.88%/4.70%, aging) · المطار العتيق 400-600 (7.12%, land_priced) ·
  **المعمورة 56 400-600 (6.04%/4.83%, aging)** · ام صلال علي 400-600 (5.14%, modern) ·
  **امريخ الجنوبي 400-600 (6.44%/5.16%, aging — the Marikh over-anchor area)** · عين خالد 400-600 (6.83%, modern).
- **indicative (10):** السلطة الجديدة · الثمامة 47 · الخيسة · العزيزية · الغرافة · ام لخبا ·
  روضة الحمامة 900-1500 (4.03%) · سميسمة · لقطيفية 900-1500 · لوسيل 69 900-1500 (4.52%, luxury_new).

Yields cluster sensibly (aging/modern 400-600 ≈ 5.1–7.7% gross; large/luxury 900-1500 ≈ 4.0–4.5%
gross) — the §8 "3× spread (4–11%)" is gone now that cells are well-sampled.

**Villa-6 (المعمورة, 56/647/6, 652 m² → 600-900):**
- المعمورة 56 **400-600 → reliable, 6.04% gross / 4.83% net** (n=69 rent, MoJ villa n=23).
- المعمورة 56 **600-900 → fallback, 5.29% gross** — now limited by the **MoJ SALE** denominator
  (only n=7 villa sales in that bracket; eff_n=7 < 10), NOT the rent (rent went thin→11). The
  binding constraint for villa-6's exact bracket has shifted from rent-depth to **sale-depth**.
- ⟹ usable villa-6 income band ≈ **5.3–6.0% gross** (400-600 reliable + 600-900 rent-consistent)
  ⟹ income value ≈ **3.2–3.6M** — converges with §8/§9 and sits below the condition-blind
  comparison (3.8M): the income check doing its job.

**Verdict:** the per-area lever closes Dependency #2 from "1 reliable cell" to a usable
**6 reliable + 10 indicative** spread across the priority villa districts — including the المعمورة
and Marikh areas the R7 walk-through hinges on. This is the strong-enough yield layer §6
(triangulation) needs. The remaining tail = per-bracket **MoJ sale** depth (a different source),
not PF rent depth.

## 6. Honest residual (Rule #36)

- **Long-tail communities** present ONLY in PF's unserved deep pages are not enumerated by
  `community_map` (it stops at the 404 cap). Those areas are tiny (too few listings to ever form a
  reliable cell) → no effect on reliable/indicative cells. Documented in `community_map`'s docstring.
- **Gate-2 lookup-flag (unchanged, §9):** `evaluate_unified._cap_area_token` is not a18/override-
  aware — the durable fix belongs to the §6 income-triangulation wiring step, not this connector.

## 7. The two gates (need an explicit «go»)

1. **Gate-1 (push):** commit the connector + calibrator + test (value-invariant, origin-only is
   fine as a backup — §9 precedent), **and separately**, when shipping: replace `cap_rates.sqlite`
   with the rebuilt DB + `git subtree push heroku` + origin.
2. **Gate-2 (methodology/output):** the rebuilt DB changes the user-visible income cross-check for
   the deepened areas. The **headline-triangulation wiring** (§6 — income setting the villa
   headline + an a18/override-aware `_lookup_calibrated_cap_rate`) is a LATER, separate Gate-2 step.
