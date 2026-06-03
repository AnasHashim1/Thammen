# Sprint 2.19 — Cap Rate Calibration v1
## Brief for Claude Code

**Prepared by:** Claude (web session, 2026-05-20)
**Baseline:** Sprint 2.16.15 (CHANGELOG_v36, `thammen-sprint2p16p15-extra-forbid`)
**Target:** Sprint 2.19 (`thammen-sprint2p19p0-cap-rate-calibration`)
**Sprint type:** Feature (not housekeeping). Justifies major number.

---

## 1. Context & motivation

Current DCF engine uses **hardcoded cap rates** (lands 4%, villas 6.5%, compound_small 6%, compound_large 7.5%, apartments 6.5%, tower 6%, commercial 8%). Source: best-guess from FGRealty + market norms + asset class theory. **Never empirically validated.**

**Secretary's confirmed sales delayed indefinitely** (originally Thursday 2026-05-21, now unknown). Cannot wait for that data to start improving. PropertyFinder rentals provide a parallel path that does **not** violate Rule E1.

**RICS gap closed by this Sprint:** Income approach parameters become empirically grounded instead of assumed. This is the largest self-improvement lever available without confirmed sales.

---

## 2. Methodology constraints (NON-NEGOTIABLE)

Read these sections of the docs before any code:
- `docs/Empirical_Findings.md` §2 (Rules E1, E3, E4)
- `docs/Project_Instructions.md` §4 (statistical discipline + reliability gates)
- `docs/Project_Instructions.md` §7 (GIS area names are authoritative)

### Rule E1 (CRITICAL)
🚫 Listings **NEVER** adjust MoJ sale medians. This Sprint operates on **rentals only** and outputs **cap rate parameters** for the DCF engine. The MoJ sale comparison path is untouched.

### Rule E3 (refined for this Sprint)
Listings are normally "sentiment only" and must not enter calculation. **This Sprint defines a controlled exception**: rental listings (not sales) feed into **cap rate parameters** (a DCF input, not a price). The reason this is acceptable while Rule E1 still holds:
- Qatar rental market is more transparent (registered contracts, active market)
- We calibrate a *parameter* (cap rate), not a *price*
- The output flows into DCF, not into MoJ-comparison

### Rule E4 (apply during stratification)
When computing cap rates for villas, stratify by stock class first (`land_priced`, `aging_stock`, `modern_stock`, `luxury_new`). Do not pool stocks.

### Statistical discipline
- **Median, not mean** (rentals have outliers)
- **Reliability gate: n ≥ 10** per (district × asset_type × bracket). Below 10 → fall back to hardcoded cap rate, log the gap.
- 24-month window if rental data has timestamps; else current snapshot
- Always store `sample_size` and `last_updated` with each rate

### GIS authoritative for district
PropertyFinder's `location.full_name` ("Rawdat Al Khail, Rawdat Al Khail, Doha") is **not** authoritative. For each listing:
1. Extract GPS from `property.location.coordinates`
2. Spatial query on `Vector/Districts/MapServer/0` to get DIST_NO + ANAME
3. Use GIS ANAME as the canonical district
4. Log mismatches between PropertyFinder name and GIS name (for future debugging)

---

## 3. Smoke test results (PropertyFinder, 2026-05-20)

Already executed from web Claude's container. Heroku verification optional given PropertyFinder is a commercial international site (not subject to F5/WAF like sak.gov.qa).

| URL pattern | Status | Total | Pages |
|---|---|---|---|
| `/en/rent/properties-for-rent.html` | 200 | 31,109 | 1,244 |
| `/en/rent/apartments-for-rent.html` | 200 | 25,541 | 1,022 |
| `/en/rent/villas-for-rent.html` | 200 | (smaller) | — |
| `/en/buy/properties-for-sale.html` | 200 | 9,525 | 381 |
| `/en/buy/villas-for-sale.html` | 200 | 1,521 | 61 |
| `/en/buy/apartments-for-sale.html` | 200 | (smaller) | — |

**Key technical findings:**
- Schema: Next.js `<script id="__NEXT_DATA__">` JSON, fully SSR
- Per-page: 25 listings (despite `meta.per_page=25`, sometimes returns 27)
- Pagination: `?page=N` works without JS
- Rate limit: 5 requests with 2.0s delay → all HTTP 200, latency improves with CDN cache (0.55s → 0.15s)
- GPS coverage: 10/10 listings have valid Qatar coordinates
- Avg latency: 0.85s per page

**Listing data path:**
`__NEXT_DATA__.props.pageProps.searchResult.listings[i].property`

**Key fields per listing:**
```
property.id                                 → listing identifier
property.price.value / price.period         → monthly rent in QAR
property.size.value / size.unit             → size in sqm
property.location.coordinates.lat/lon       → GPS (Qatar bounds verified)
property.location.full_name                 → PropertyFinder name (NOT authoritative)
property.property_type                      → "Apartment", "Villa", "Hotel Apartments", etc.
property.bedrooms / bathrooms               → integers as strings
property.furnished                          → "YES"/"NO"
property.completion_status                  → "" / "Off-Plan" / etc.
property.listed_date                        → ISO 8601
property.is_new_construction                → bool
```

`smoke_propertyfinder.py` is already in the deploy directory (failed Heroku push today due to git structure issue — fix or use locally; see §8 below).

---

## 4. Sprint deliverables

### Files to create

| File | Purpose | Approx LOC |
|---|---|---|
| `propertyfinder_client.py` | Clean wrapper: fetch + parse `__NEXT_DATA__` → list of normalized dicts. Stateless. | ~150 |
| `cap_rate_calibrator.py` | Orchestrator: scrape → cross-ref GIS → stratify → compute net yield → write SQLite | ~300 |
| `cap_rates.sqlite` | Storage. Schema below. | — |
| `run_calibration.py` | Heroku scheduler entry point. Idempotent. Logs to stdout. | ~50 |
| `tests/test_cap_rate_calibrator.py` | Unit tests, target ≥12 cases | ~250 |

### `cap_rates.sqlite` schema

```sql
CREATE TABLE cap_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_aname TEXT NOT NULL,           -- GIS ANAME (authoritative)
    district_dist_no INTEGER NOT NULL,      -- GIS DIST_NO
    asset_type TEXT NOT NULL,               -- apartment_building, villa, tower, compound_small, compound_large
    bedrooms INTEGER,                       -- NULL for non-residential (lands, compounds)
    size_bracket TEXT NOT NULL,             -- '0-400', '400-600', '600-900', '900-1500', '1500+'
    stock_class TEXT,                       -- For villas: land_priced / aging_stock / modern_stock / luxury_new. NULL for others.
    median_monthly_rent_qar REAL NOT NULL,
    median_rent_per_sqm REAL NOT NULL,
    sample_size INTEGER NOT NULL,
    gross_yield REAL,                       -- annual_rent / median_sale_price (from MoJ for same cell)
    service_charge_qar_sqm_year REAL,
    net_yield REAL,                         -- gross - service_charges - vacancy - mgmt - maintenance
    cap_rate REAL,                          -- = net_yield (this is the DCF input)
    confidence TEXT NOT NULL,               -- 'reliable' (n≥20), 'indicative' (10-19), 'fallback' (<10, use hardcoded)
    last_updated TEXT NOT NULL,             -- ISO 8601
    notes TEXT
);
CREATE INDEX idx_lookup ON cap_rates(district_aname, asset_type, size_bracket, stock_class);
```

### Files to modify

| File | Change |
|---|---|
| `evaluate_unified.py` | DCF code path queries `cap_rates.sqlite` first; falls back to hardcoded if `confidence='fallback'` or row absent. Log which path was used. Bump `ENGINE_VERSION` and `SPRINT_TAG`. |
| `output_briefs.py` | Add `cap_rate_provenance` field to brief: shows `cap_rate=X.X%`, `sample_size=N`, `confidence=Y`, `last_updated=Z`. Mirror Sprint 2.16.9 MUC display pattern (canonical root > brief). |
| `api.py` | Bump health endpoint to report calibration freshness. Add new field `calibration_freshness` next to existing `data_freshness`. |
| `requirements.txt` | No new deps. Use only stdlib (`urllib`, `sqlite3`, `json`, `re`). |
| `Procfile` or scheduler config | Add `release` or scheduler entry for `run_calibration.py` — recommend Heroku Scheduler add-on, daily 02:00 Doha (23:00 UTC). |

---

## 5. Calibration algorithm

```
for each (district, asset_type, size_bracket) in scope:
    # 1. Fetch rentals
    listings = propertyfinder_client.fetch_rentals(
        asset_type=asset_type,
        target_n=200,        # cap on listings per cell
        max_pages=8,         # 8 × 25 = 200
        delay_sec=2.0
    )

    # 2. GIS cross-reference (mandatory)
    for L in listings:
        L.gis_district = query_gis_districts(L.gps_lat, L.gps_lon)  # ANAME from DIST_NO
        if L.gis_district != district:
            continue  # skip — PropertyFinder mislabeled

    # 3. Size filter
    listings = [L for L in listings if L.size_sqm in bracket_range(size_bracket)]

    # 4. Stratification (villas only)
    if asset_type == 'villa':
        listings = stratify_by_stock(listings, moj_land_median(district, size_bracket))
        for stock_class in listings:
            compute_and_store(district, asset_type, size_bracket, stock_class, listings[stock_class])
    else:
        compute_and_store(district, asset_type, size_bracket, None, listings)


def compute_and_store(district, asset_type, size_bracket, stock_class, listings):
    n = len(listings)
    if n < 10:
        confidence = 'fallback'
        # still record the gap so it's visible
    elif n < 20:
        confidence = 'indicative'
    else:
        confidence = 'reliable'

    median_rent = median([L.monthly_rent for L in listings])
    median_rent_per_sqm = median([L.monthly_rent / L.size_sqm for L in listings])

    moj_sale_median_per_sqm = moj_reference(district, asset_type, size_bracket, stock_class)
    if moj_sale_median_per_sqm is None:
        # no MoJ comparable → cannot compute yield
        confidence = 'fallback'
        cap_rate = None
    else:
        annual_rent_per_sqm = median_rent_per_sqm * 12
        gross_yield = annual_rent_per_sqm / moj_sale_median_per_sqm
        service_charge = lookup_service_charge(district, asset_type)  # see §6
        vacancy = 0.05
        mgmt = 0.05
        maintenance = 0.10
        net_yield = gross_yield - service_charge/moj_sale_median_per_sqm - vacancy - mgmt - maintenance
        cap_rate = net_yield  # in DCF context, these are equivalent

    write_to_sqlite(...)
```

---

## 6. Service charge constants

From Project Instructions §4 + verified FGRealty data:

```python
SERVICE_CHARGE_QAR_SQM_YEAR = {
    # apartment_building:
    'pearl':         174,   # 14.5 × 12 (FGRealty range 14-15)
    'lusail':        144,   # 12 × 12 (FGRealty range 10-14)
    'west_bay':      120,   # estimate
    'msheireb':      168,
    # default per asset class
    'apartment_building_default': 96,   # 8 × 12
    # villas and lands: no service charge
    'villa':         0,
    'land':          0,
    'compound_large': 60,   # gated community fees
    'compound_small': 30,
}
```

Lookup by district name first; fallback to asset class default.

---

## 7. Scope (in this Sprint)

**IN scope:**
- Top 10 districts by MoJ transaction volume (Doha=الدوحة, الريان, الظعاين, الوكرة, أم صلال, الخور, الشمال, الشيحانية, +2 more from MoJ §15)
- Asset types: `apartment_building`, `villa`, `compound_small`, `compound_large`, `tower`
- Size brackets: per Project Instructions §4 (0-400, 400-600, 600-900, 900-1500, 1500+)
- Daily scheduler refresh (Heroku Scheduler add-on)

**OUT of scope (explicit, declare in CHANGELOG):**
- Sales listings (Rule E1 — never use for MoJ adjustment)
- Sales listings for any purpose (this Sprint is rentals only; sales scraping is a separate decision)
- Confidence calibration (needs confirmed sales — deferred to post-secretary)
- Sprint 2.20 Comparable Adjustments Grid (separate Sprint)
- Visual verification (Sprint 2.17 or later)
- arady.qa / bayut.qa / mzadqatar / FGRealty scraping (supplementary, not needed for v1)
- Per-unit rentals in mixed-use towers (use building-level median)

---

## 8. Git structure issue (must resolve first)

Earlier today (2026-05-20), `git push heroku master` from `C:\Thammen\deploy v2` failed because Heroku saw `deploy v2/` as subdirectory and no `requirements.txt` at root. **However** Sprint 2.16.15 pushed successfully yesterday evening by Claude Code, so the push mechanism works for Claude Code.

**Action required from Claude Code:**
1. Run `git rev-parse --show-toplevel` from `C:\Thammen\deploy v2`
2. Run `git status` and `git log --oneline -5`
3. Identify the push mechanism that worked yesterday (subtree push? specific subdirectory setup?)
4. Document it in `docs/Operational_Rules.md` so it doesn't fail again
5. Ensure `smoke_propertyfinder.py` (already pushed today to wrong location) is cleaned up if needed

Don't proceed with Sprint 2.19 deploy until this is resolved.

---

## 9. Pre-deploy 6-item checklist (Project Instructions §5)

1. `py_compile` on every modified Python file
2. `node --check` on extracted inline JS from `index.html` — **N/A** for this Sprint (no JS changes)
3. Mobile viewport test 390×844 — verify `cap_rate_provenance` displays correctly if added to brief
4. **81/81 regression tests pass** (current baseline from Sprint 2.16.15)
5. **≥12 isolated logic tests** for `cap_rate_calibrator.py`:
   - Test net yield formula
   - Test reliability gate (n<10, 10-19, ≥20)
   - Test stratification routing (villa only)
   - Test GIS mismatch handling
   - Test fallback to hardcoded when SQLite row absent
   - Test SQLite schema enforcement
   - Test PropertyFinder client URL building
   - Test `__NEXT_DATA__` parsing with malformed input
   - Test pagination bounds
   - Test stale row detection (`last_updated > 30 days`)
   - Test asset_type filter mapping (Apartment → apartment_building, Hotel Apartments → apartment_building, Villa → villa, etc.)
   - Test GPS-out-of-Qatar rejection
6. Smoke test 3 diverse addresses from Heroku after deploy (e.g., Pearl apartment + Al Kheesa villa + Lusail tower)

---

## 10. CHANGELOG_v37 required structure

Mirror CHANGELOG_v33, v34, v35, v36 style. Required sections:

```markdown
# CHANGELOG v37 — Sprint 2.19: Cap Rate Calibration v1
Engine version: thammen-sprint2p19p0-cap-rate-calibration
Date: 2026-05-XX
Files changed: evaluate_unified.py, output_briefs.py, api.py + new (propertyfinder_client.py, cap_rate_calibrator.py, run_calibration.py)

## Why this matters
[Concrete user-visible problem: DCF cap rates were best-guess; now empirically grounded]

## Root cause
[Current hardcoded values + their source + why they're insufficient]

## What this patch does
### Backend
### Schema
### Calibration pipeline
### Fallback behavior

## Verification — empirical evidence
[Actual numbers from first calibration run: how many cells reached n≥20, n=10-19, n<10; comparison of new vs old cap rates per asset type]

## Deployment
[Exact prompt command for Anas, including running first calibration before deploy]

## Verification curl
[One-liner: /api/health should show calibration_freshness; /api/evaluate on test address should show cap_rate_provenance]

## What's NOT in this patch
[Reproduce §7 OUT scope as scope boundary]
```

---

## 11. Self-correction triggers (Project Instructions §22)

While implementing, if any of these come up, STOP:

- Considering using PropertyFinder *sale* listings to validate or adjust MoJ sale medians → Rule E1, never
- Treating PropertyFinder's `location.full_name` as authoritative without GIS cross-check → §2 GIS rule
- Storing a cap rate row with n<10 marked as anything other than `fallback` → reliability gate
- Pooling villa listings without stratification → Rule E4
- Computing gross yield without converting to net → §4 net yield benchmarks
- Skipping the smoke test on the new code path before deploy → §5 checklist item 6
- Bumping Sprint to 2.16.16 instead of 2.19 → see §1, this is a feature not housekeeping

---

## 12. Success criteria

This Sprint is "done" when:
1. `cap_rates.sqlite` is populated with at least one row marked `reliable` (n≥20) per top-3 districts
2. Production `/api/evaluate` on a Pearl apartment returns a cap rate sourced from `cap_rates.sqlite` (not hardcoded) and the brief shows `sample_size + last_updated`
3. Heroku Scheduler is configured and the first scheduled run succeeds
4. CHANGELOG_v37 is committed
5. ENGINE_VERSION updated to `thammen-sprint2p19p0-cap-rate-calibration`
6. 81/81 + ≥12 new tests passing
7. Bug catalogue in `docs/Project_Instructions.md` §18 unchanged (this Sprint doesn't close existing bugs, it adds a feature)

---

## 13. Open questions you can decide

Without further input from Anas:
- Exact list of top 10 districts (use MoJ §15 distribution: الدوحة 6,811, الريان 6,543, الظعاين 4,899, الوكرة 3,013, أم صلال 2,623, الخور 1,528, الشمال 1,229, الشيحانية 73 + 2 from sub-districts)
- Heroku Scheduler vs `release` task — your call based on Heroku plan
- Whether to expose new SQLite via `/api/calibration` endpoint (recommend YES, read-only)
- Where to log calibration warnings (recommend stdout + a `calibration_log.json` rolled weekly)

If unsure, document the decision in CHANGELOG_v37 §"Decisions made" and proceed.

---

## 14. Required input from Anas

Only if blocking:
- Heroku Scheduler add-on subscription confirmation (free tier should suffice)
- Approval of Sprint 2.19 numbering (not 2.16.16) — see §1 reasoning

If neither blocks, proceed and deliver complete Sprint.

---

*End of brief. Total LOC budget: ~750 (new) + ~80 (modifications). Estimated build: 4-6 hours of focused work. Test + deploy: 1 hour.*
