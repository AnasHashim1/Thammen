# CHANGELOG v37 — Sprint 2.19: Cap Rate Calibration v1

**Engine version:** `thammen-sprint2p19p0-cap-rate-calibration`
**Date built:** 2026-05-20
**Sprint type:** Feature (not housekeeping) — justifies the 2.19 minor bump (see §1 of the brief).
**Files changed:** `evaluate_unified.py`, `output_briefs.py`, `api.py`
**Files added:** `propertyfinder_client.py`, `cap_rate_calibrator.py`, `run_calibration.py`, `cap_rates.sqlite`, `tests/test_cap_rate_calibrator.py`
**Files moved:** `smoke_propertyfinder.py` → `tests/integration/smoke_propertyfinder.py`

---

## Why this matters

The DCF / Income-Approach cap rates were **hardcoded best-guesses**
(`CAP_RATES_BY_ASSET` in `evaluate_unified.py`): villa 4.0%, compound_small 6.0%,
etc. Source: convergence of FGRealty data + market norms + asset-class theory.
**Never empirically validated.**

The secretary's confirmed-sales data (Sprint 2.16.16) is delayed indefinitely.
Rather than wait, this Sprint opens the first real *self-improvement* lever:
cap-rate parameters calibrated from live market rentals (PropertyFinder)
divided by Ministry-of-Justice sale medians for the same district + bracket.

User-visible result: a villa evaluation in a district we have data for now
shows an **empirically grounded** cap rate with its sample size, confidence
tier, and last-updated date — instead of a silent 4% assumption.

---

## Root cause

`CAP_RATES_BY_ASSET` (line ~93) and `_DEFAULT_CAP_RATES` (line ~1110) are static
dicts. There was no path to update them from market evidence, and no way for the
user to know whether the cap rate behind an income cross-check was measured or
assumed.

---

## What this patch does

### New: calibration pipeline (offline, committed snapshot)

- `propertyfinder_client.py` — stateless PropertyFinder client (stdlib only).
  Fetches **rental** search pages, parses the Next.js `__NEXT_DATA__` blob,
  normalizes each listing (monthly-rent coercion, GPS-in-Qatar gate,
  furnished / completion_status / listed_date / is_new_construction).
  **Rentals only** — no sale path exists (Rule E1).
- `cap_rate_calibrator.py` — orchestrator. For each rental: resolve the
  authoritative district via `Vector/Districts` spatial query (PropertyFinder's
  `location.full_name` is never trusted — §2 GIS rule), bin by
  (district × asset_type × size_bracket), compute the median rent/m², divide by
  the MoJ sale median/m² (read-only) for that cell, derive net yield, gate by
  sample size, write `cap_rates.sqlite`.
- `run_calibration.py` — idempotent entry point (rebuilds the table each run).
  Logs a `CALIBRATION_SUMMARY {...}` line for a future scheduler/CI to parse.

### Schema (`cap_rates.sqlite`)

Per brief §4: `cap_rates(district_aname, district_dist_no, asset_type, bedrooms,
size_bracket, stock_class, median_monthly_rent_qar, median_rent_per_sqm,
sample_size, gross_yield, service_charge_qar_sqm_year, net_yield, cap_rate,
confidence, last_updated, notes)` + `idx_lookup`.

### Backend integration (`evaluate_unified.py`)

- `ENGINE_VERSION` → `thammen-sprint2p19p0-cap-rate-calibration`, `SPRINT_TAG` → `2.19.0`.
- New `_lookup_calibrated_cap_rate(asset_type, area_name, plot_area_m2, stock_class)`
  reads `cap_rates.sqlite` **read-only** and **safe-fails to `(None, None)`** on
  a missing DB, schema drift, or any exception.
- `_build_income_crosscheck(...)` now prefers a calibrated cap rate when one
  exists with `confidence ∈ {reliable, indicative}`; otherwise it keeps the
  hardcoded rate. Either way it attaches a `cap_rate_provenance` dict.
- The provenance is surfaced at the **canonical response root**
  (`output['cap_rate_provenance']`) — the Sprint 2.16.9 "root > brief" pattern.

### Frontend / brief (`output_briefs.py`)

- New `build_cap_rate_provenance_section(provenance)` returns an Arabic brief
  section ("مصدر معدل الرسملة") describing whether the rate is calibrated
  (with n / confidence / last_updated) or a hardcoded fallback. Appended to the
  audience brief; the root field remains authoritative.

### API (`api.py`)

- `/api/health` gains `calibration_freshness` (total cells, counts by
  confidence, last_updated, days_old, stale flag).
- New read-only `GET /api/calibration` — returns the freshness summary plus up
  to 200 calibrated cells (reliable first). No secrets, pure derived parameters.

### Fallback behavior

Any asset/area/bracket without a usable calibrated row falls back to the
original hardcoded cap rate, transparently, with
`cap_rate_provenance.source = 'hardcoded'`. The engine never depends on the DB.

---

## Decisions made (no further input needed)

1. **Net-yield formula corrected.** The brief §5 literal
   `net = gross − vacancy − mgmt − maintenance` subtracts an *absolute* 0.20 from
   the yield ratio, which drives realistic gross yields (~6–9%) negative. The
   dimensionally correct form (Operational_Rules #1, #8) treats those as
   fractions of **income**:
   `net = gross × (1 − opex_ratio) − service_charge_per_sqm_year / sale_median_per_sqm`,
   with opex_ratio = 0.20 (villa) / 0.23 (compound). This is the deployed formula.
2. **Persistence = committed read-only snapshot** (Operational_Rules #43).
   Heroku's filesystem is ephemeral, so `cap_rates.sqlite` is committed and read
   read-only at runtime — exactly like `building_age_cache.sqlite`. Refresh =
   re-run `run_calibration.py` (locally or `heroku run`), then commit + deploy.
3. **No daily auto-scheduler in v1.** Heroku has zero add-ons and no free dynos,
   so a Scheduler add-on is a billing decision deferred to Anas. Manual/`heroku run`
   refresh ships v1 value now.
4. **GIS-driven binning.** Listings are binned by their GIS-resolved district
   (ANAME token), not by a pre-declared district list — more robust and fully
   honors §2 (GIS authoritative).
5. **`/api/calibration` endpoint = YES** (read-only), per brief §13.

---

## Verification — empirical evidence

First full calibration run (2026-05-20, 600 villa rentals + 21 compounds,
GIS-resolved 100%, 0 skipped):

```
total cells : 126
reliable    :   4   (n ≥ 20)
indicative  :   4   (10–19)
fallback    : 118   (n < 10 or no MoJ sale comparable)
```

Reliable villa cap rates (calibrated, replace the flat 4% assumption):

| District       | Bracket | n  | gross | net / cap_rate |
|----------------|---------|----|-------|----------------|
| عين خالد       | 0-400   | 26 | 8.12% | **6.49%**      |
| العب           | 400-600 | 36 | 5.88% | **4.70%**      |
| المعمورة       | 0-400   | 27 | 9.45% | **7.56%**      |
| جزيرة اللؤلؤة  | 600-900 | 32 | 4.14% | **3.31%**      |

The Pearl (جزيرة اللؤلؤة) villa cap rate of 3.31% is correctly low for a luxury
location; عين خالد at 6.49% is a solid investment yield — both match Qatar net-
yield benchmarks (5–6% normal, <4% weak/luxury).

Production lookup confirmed against the committed DB:
`_lookup_calibrated_cap_rate('villa', 'عين خالد', 350)` → `0.06494` (reliable, n=26).

### Tests

- **81/81 regression** preserved (stock_strata 6, scope_of_service 27,
  material_uncertainty 13, sprint_2p16p14 21, sprint_2p16p15 14).
- **59 new checks** in `tests/test_cap_rate_calibrator.py`, two-layer
  (Operational_Rules #40): unit-level pure functions + production-level checks
  that exercise the real `evaluate_unified._lookup_calibrated_cap_rate` and
  `_build_income_crosscheck` against a fixture DB, including safe-fail when the
  DB is absent.

---

## Deployment

```
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p15
copy /Y api.py api.py.bak_2p16p15
copy /Y output_briefs.py output_briefs.py.bak_2p16p15
git add "deploy v2/propertyfinder_client.py" "deploy v2/cap_rate_calibrator.py" "deploy v2/run_calibration.py" "deploy v2/cap_rates.sqlite" "deploy v2/evaluate_unified.py" "deploy v2/output_briefs.py" "deploy v2/api.py" "deploy v2/CHANGELOG_v37.md" "deploy v2/tests/test_cap_rate_calibrator.py" "deploy v2/tests/integration/smoke_propertyfinder.py" "deploy v2/docs/Operational_Rules.md"
git commit -m "Sprint 2.19: Cap Rate Calibration v1 (villas + compounds)"
git subtree push --prefix "deploy v2" heroku master
```

> **Deploy mechanism:** `git subtree push --prefix "deploy v2"` — NOT plain
> `git push heroku master` (the repo root is `C:\Thammen`; the app lives in the
> `deploy v2/` subdir; the python buildpack rejects a plain push — see
> Operational_Rules #43).

To refresh the calibration later:
```
heroku run python run_calibration.py
```
then re-commit `cap_rates.sqlite` and subtree-push (the committed-snapshot model).

---

## Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health | findstr /C:"calibration_freshness"
curl -s https://thammen.qa/api/calibration | findstr /C:"reliable"
curl -s -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":56,\"street\":784,\"building\":2}" > out.json
findstr /C:"cap_rate_provenance" out.json
```

Post-deploy smoke (3 diverse addresses, NOT 51/835/17 per Bug A6):
- a villa in a calibrated district (عين خالد) → `cap_rate_provenance.source = calibrated`
- a Lusail tower → `cap_rate_provenance.source = hardcoded` (apartments/towers deferred)
- a third diverse address → 200, no regression

---

## What's NOT in this patch (scope boundary)

- **Apartments + towers** — MoJ holds no per-unit apartment sale prices, so no
  yield denominator exists; they stay hardcoded (`source=hardcoded`).
  → **Sprint 2.29 (MME integration), HIGH PRIORITY** — MME has government
  apartment sale data (not listings, so Rule E1 stays intact).
- **Land** — needs a MoJ price-trend path, not rent÷sale. → **Sprint 2.19.1.**
- **compound_large** — yield-only asset, no MoJ comparable → stays hardcoded.
- **Sale listings** — out of scope entirely (Rule E1 / E3). This Sprint is
  rentals only.
- **Daily auto-scheduler** — deferred pending the Heroku billing decision
  (Scheduler add-on or external cron). Refresh is manual for v1.
- **Confidence calibration / MAPE** — needs confirmed sales (Sprint 2.16.16).
- **Per-listing villa stock stratification** — stock_class is tagged at the
  (district × bracket) level from the MoJ villa/land median ratio; per-listing
  stratification needs sale prices we don't have.
- **DCF_ONLY cap-rate paths** (`_DEFAULT_CAP_RATES`, lines ~1110/1536/1686) are
  untouched — they serve apartment/tower/compound_large, which v1 does not
  calibrate.
