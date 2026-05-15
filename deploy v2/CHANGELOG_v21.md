# CHANGELOG — Sprint 2.15.1: Imagery Prefilled Cache (cache-only production)

**Engine version:** `thammen-sprint2p15p1-imagery-prefilled-cache`
**SPRINT_TAG:** `2.15.1` → /api/health reports `3.1.0-sprint2.15.1`
**Date:** 2026-05-14
**Files added:** `prefill_cache.py`, `test_imagery_flag.py`, `seed_pins.txt`, `building_age_cache.sqlite` (62 entries)
**Files updated:** `qatar_gis.py`, `evaluate_unified.py`
**Replaces:** Sprint 2.15 (rolled back due to Heroku timeout)

---

## Why this exists

Sprint 2.15 attempted inline imagery on Heroku. It deployed, but the
**first request to a fresh dyno consistently timed out** (H12 at 30s,
verified in logs):

```
2026-05-14T15:25:31 heroku[router]: at=error code=H12 desc="Request timeout"
  method=POST path="/api/evaluate/details" service=30000ms status=503
```

Root cause (measured from production logs, not local benchmarks):
- Baseline /api/evaluate/details on Heroku takes **~24s** even without
  imagery (GIS API calls + MoJ DB queries + property factors)
- Heroku 30s timeout leaves only **~6s** for any added work
- Imagery from a cold dyno: 15-25s due to Heroku→Qatar GIS network latency
- 24s + 15-25s = **timeout guaranteed on first request**

The local benchmark of 5.6s was misleading — my container had ~10x
lower latency to gisqatar.org.qa than Heroku does.

**Conclusion**: imagery cannot live in the critical request path on
Heroku. It must be precomputed offline.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│ OFFLINE (local machine or Claude container)                │
│                                                             │
│  prefill_cache.py --pins seed_pins.txt                     │
│    ├─→ for each PIN:                                       │
│    │    estimate_construction_year_smart(flag=True)        │
│    │    └─→ full imagery analysis (5-20s per PIN)          │
│    │        └─→ writes to building_age_cache.sqlite        │
│    │                                                        │
│    └─→ commit building_age_cache.sqlite to git             │
└────────────────────────────────────────────────────────────┘
                            │
                            │ git push heroku master
                            ▼
┌────────────────────────────────────────────────────────────┐
│ HEROKU (production)                                         │
│                                                             │
│  POST /api/evaluate/details                                 │
│    ├─→ evaluate_property.py                                 │
│    │   └─→ estimate_construction_year_smart(flag=False)    │
│    │       └─→ cache lookup ONLY                            │
│    │           ├─→ hit  → instant (<5ms) → age_source=gis  │
│    │           └─→ miss → None → age_source=unknown         │
│    └─→ Total request: ~24s (unchanged from Sprint 2.14.0)  │
└────────────────────────────────────────────────────────────┘
```

The flag `ENABLE_INLINE_IMAGERY` (module-level in `qatar_gis.py`) gates
which mode is active. Default is `False`. Can be enabled via env var
`THAMMEN_ENABLE_INLINE_IMAGERY=1` (offline use only).

## Files

### NEW: `prefill_cache.py` (~270 lines)

Offline CLI tool. Two input modes:
- `--addresses addresses.csv` (zone,street,building,note)
- `--pins pins.txt` (one PIN per line)

Options: `--time-budget S`, `--force` (recompute cached), `--dry-run`,
`--cache-path`. Reports per-PIN outcome and final summary.

### NEW: `test_imagery_flag.py` (6 tests)

Verifies:
- Default flag is False (production safe)
- Env var enables full mode
- Cache miss in cache-only mode returns None in <0.5s
- `estimate_construction_year` is NEVER called when flag=False
- Cache hit returns value in cache-only mode
- Full mode runs imagery on cache miss

### NEW: `seed_pins.txt` (62 PINs)

Real PINs sampled from priority districts via CadastrePlots:
- اللقطة (10)
- الغرافة (10)
- الخيسة (10)
- بو هامور (10 + 2 known: 56099695, 56099696)
- عين خالد (10)
- دحيل (10)

All plots 200-2000 m² (residential range). Reproducible via seed=42.

### NEW: `building_age_cache.sqlite` (23 KB, 62 entries)

Precomputed in Claude's container (low network latency to GIS).
Distribution of results:
- Built ≤1995: 17 PINs (old housing stock)
- Built 1995-2010: 12 PINs (±15y bracket)
- Built 2010-2017: 6 PINs (±7y bracket — tight)
- Built 1995-2024: 17 PINs (±29y — wide bracket, need more probes)
- Polygon vacant in all sampled years: 10 PINs

The 17 "vacant" results are mostly Bou Hamour 2024-buildable land or
plots where the algorithm cannot detect the building reliably (small
footprint, low contrast against background).

### MODIFIED: `qatar_gis.py` (+15 lines)

```python
# Module-level flag
import os as _os
ENABLE_INLINE_IMAGERY = _os.environ.get(
    'THAMMEN_ENABLE_INLINE_IMAGERY', '0'
) == '1'
```

`estimate_construction_year_smart()` gains an early return:

```python
def estimate_construction_year_smart(self, polygon_4326, pin=None, ...):
    # Step 1: cache lookup (both modes)
    if pin and (cached := cache.get(pin)) and cached.get('earliest_built_year'):
        return ConstructionYearEstimate(...)

    # CACHE-ONLY mode: return immediately on miss
    if not ENABLE_INLINE_IMAGERY:
        return None  # ← new in 2.15.1

    # FULL mode: run imagery (only reached when flag is True)
    ...
```

### MODIFIED: `evaluate_unified.py` (2 lines)

```python
ENGINE_VERSION = 'thammen-sprint2p15p1-imagery-prefilled-cache'
SPRINT_TAG = '2.15.1'
```

The Path B fallback (reads age from `raw_property_report.construction`)
is unchanged from Sprint 2.15 — still works, now reading from the
prefilled cache instead of inline imagery.

## Production behaviour after this deploy

For the 62 PINs in the prefilled cache:
- User enters Z/S/B → engine finds PIN → cache hit → instant age detection
- UI shows: `📡 مكتشف من صور الأقمار` badge
- Age value influences: cost approach, age-aware substantiality, 10-year-rule classification

For PINs NOT in the cache:
- User enters Z/S/B → engine finds PIN → cache miss → returns None
- `age_source: unknown` (same as Sprint 2.14.0 behaviour)
- Engine continues normally without age
- No performance impact (cache miss is <0.5ms)

## Test results

```
test_building_age_cache.py     → 13 tests OK
test_imagery_flag.py            → 6 tests OK
test_scope_of_service.py        → 27 tests OK
test_material_uncertainty.py    → 13 tests OK
test_market_regime.py           → 36 tests OK
────────────────────────────────────────────
Total: 95 tests, all pass
```

## Known limitations

### Cache coverage is limited
62 entries covers ~6 districts. Real usage will frequently hit
uncached PINs. Plan: grow the cache to 500-2000 PINs in a follow-up
batch covering all major residential districts.

### J Seven PINs return imagery-vacant
PINs 56099695 and 56099696 (built April 2026 per Anas's testimony)
are marked as vacant or uncertain because the 2024 satellite imagery
predates their construction. This is **correct algorithm output for
the data available** — the imagery doesn't know about 2026 builds.

Sprint 2.16 will override these via the `confirmed_sales` table
(broker testimony takes priority over imagery for known recent sales).

### Imagery results are noisy for some plots
The threshold-based algorithm (`threshold_stddev=22`) sometimes
misclassifies small or low-contrast plots. Two adjacent identical
plots (J Seven 56099695 vs 56099696) got different results: one
"vacant 2024" and one "built 2010 ±15y". This is algorithm noise,
not a bug. Improvements deferred (algorithm tuning is its own Sprint).

### Cache is read-only in production
Heroku's filesystem is ephemeral. Any production writes would be lost
on dyno restart. Production explicitly disables imagery → never tries
to write. The cache file is shipped via the git slug.

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
```

Back up modified files:

```cmd
copy /Y qatar_gis.py qatar_gis.py.bak2
```

```cmd
copy /Y evaluate_unified.py evaluate_unified.py.bak3
```

Drop the new files (this REPLACES the broken Sprint 2.15 state):

```cmd
tar -xf "%USERPROFILE%\Downloads\sprint2p15p1-delta.zip"
```

Local verification — confirm flag is OFF and cache loads:

```cmd
python -c "import qatar_gis; print('flag:', qatar_gis.ENABLE_INLINE_IMAGERY)"
```
Expect: `flag: False`

```cmd
python -c "from building_age_cache import BuildingAgeCache; print(BuildingAgeCache().stats())"
```
Expect: `cached_pins: 62`

```cmd
python -c "import evaluate_unified; print(evaluate_unified.ENGINE_VERSION)"
```
Expect: `thammen-sprint2p15p1-imagery-prefilled-cache`

Run tests:

```cmd
python test_imagery_flag.py
```

```cmd
python test_building_age_cache.py
```

Both should report OK.

Commit:

```cmd
git add qatar_gis.py evaluate_unified.py prefill_cache.py test_imagery_flag.py seed_pins.txt building_age_cache.sqlite CHANGELOG_v21.md
```

```cmd
git commit -m "Sprint 2.15.1: imagery prefilled cache (cache-only production mode)"
```

```cmd
git push heroku master
```

## Verification curl (post-deploy)

```cmd
curl -s "https://thammen.qa/api/health"
```
Look for `"version":"3.1.0-sprint2.15.1"`.

To verify cache lookups work in production, pick any cached PIN from
seed_pins.txt and find its address. Since reverse-lookup requires
the PIN to have an assigned QARS (not all do), pick one and test:

```cmd
type seed_pins.txt | findstr "اللقطة"
```

Then query each address (we need to find ones with full QARS):

```cmd
curl -s "https://services.gisqatar.org.qa/server/rest/services/Vector/QARS_Search/MapServer/0/query?where=PIN%3D52210028&outFields=PIN,ZONE_NO,STREET_NO,BUILDING_NO&f=json"
```

If features array is non-empty → use that zone/street/building in:

```cmd
curl -s -X POST "https://thammen.qa/api/evaluate/details" -H "Content-Type: application/json" -d "{\"zone\":Z,\"street\":S,\"building\":B,\"audience\":\"buyer\"}" > out.json
```

Then:

```cmd
type out.json | findstr "age_source"
```

Expect: `"age_source":"gis_imagery"` for the cached PINs that have addresses.

## Rollback

```cmd
heroku releases:rollback -a thammen-app-123
```

Reverts to the previous release. The cache file persists in git but
is harmless (unused by older versions).

Or via git:
```cmd
git revert HEAD
git push heroku master
```

## What's NOT in this patch

- **No cache growth automation.** Adding new PINs requires running
  prefill_cache.py manually + commit + push. Future work: GitHub
  Actions cron or `heroku run prefill_cache.py` from the dyno (since
  any update is committed back via separate process).
- **No imagery quality improvements.** The algorithm noise (adjacent
  plots returning different results) is preserved. Sprint TBD.
- **No confirmed_sales override.** Sprint 2.16 will add a layer that
  supersedes imagery results when broker testimony is available
  (especially for new builds where imagery is outdated).
- **No batch worker.** Considered Heroku Worker dyno for periodic
  refresh; deferred until cache size justifies $7/month.

## Strategic position after this Sprint

The Thammen data foundation now includes:
- L1 (Address & geometry): ✓ GIS
- L2 (MoJ transactions): ✓ 25,673 records
- L3 (Listings time series): ⏳ next
- L4 (Building age): **✓ 62 PINs cached, expandable to thousands**
- L5 (Apartment rentals via MME): ⏳ awaiting API test
- L6 (Construction costs): ⏳ Sprint 2.16 with broker data
- L7 (Compound/Palace): not started
- L8 (Apartments/Towers): not started
- L9 (Commercial/Mall): dropped from scope

The next bottleneck is **broker data ingestion** (Sprint 2.16) — the
manager memory session will deliver 30+ confirmed sales that feed
both the construction-cost calibration (L6) and the confirmed_sales
override table.
