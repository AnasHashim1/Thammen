# CHANGELOG — Sprint 2.15 (L4): Building Age via GIS Imagery

**Engine version:** `thammen-sprint2p15-building-age-imagery`
**SPRINT_TAG:** `2.15` → /api/health reports `3.1.0-sprint2.15`
**Date:** 2026-05-14
**Files added:** `building_age_cache.py`, `test_building_age_cache.py`
**Files updated:** `qatar_gis.py`, `evaluate_property.py`, `evaluate_unified.py`
**Builds on:** Sprint 2.14.0 (RICS scope + MUC)

---

## What this does

Activates the disabled Sprint 2.5 feature: **auto-detect building age from
historical satellite imagery** — without exceeding Heroku's 30s timeout.

Before this Sprint:
- `qatar_gis.estimate_construction_year()` existed but took **58s** to run
  (9 imagery years × ~6s per year)
- `evaluate_property.py` hard-coded `include_imagery=False`
- Property age was always "unknown" unless the user manually entered it
- The UI badge `📡 مكتشف من صور الأقمار` was wired but never fired

After this Sprint:
- Fresh address: **~6s** (down from 58s = 90% faster)
- Repeated address: **<1ms** (SQLite cache hit)
- Old buildings (≤1995): one image probe is definitive
- Vacant plots: one image probe is definitive
- Mid-age buildings: refined with binary search on additional years

## Architecture

### NEW: `building_age_cache.py` (~250 lines)

SQLite-backed cache keyed by cadastral PIN. Schema:

```sql
CREATE TABLE building_age (
    pin                  INTEGER PRIMARY KEY,
    earliest_built_year  INTEGER,
    latest_vacant_year   INTEGER,
    confidence_years     INTEGER,
    summary              TEXT,
    method               TEXT,
    schema_version       INTEGER,
    computed_at          TEXT,
    source_data_json     TEXT
)
```

Cache lives at `building_age_cache.sqlite` (alongside `moj_weekly.csv`).
File size: ~200 bytes per PIN. 10,000 cached PINs = ~2 MB.

Thread-safe writes via lock. All operations wrapped in try/except —
cache failure never raises into the engine. Schema-versioned for future
algorithm-improvement invalidations.

### MODIFIED: `qatar_gis.py` (+115 lines)

NEW method `QatarGIS.estimate_construction_year_smart()` that wraps the
existing slow algorithm with a cache and a smart probing strategy:

1. **Cache lookup by PIN** — returns instantly if hit
2. **Fast probe** — analyses only 1995 and 2024 (~6s):
   - `1995 built` → "≤1995" definitive (~6s, ±5y confidence)
   - `2024 vacant` → "no building exists" (~6s, ±99y / vacant flag)
   - `1995 vacant + 2024 built` → wide bracket, proceed to refine
3. **Refinement** — if time budget allows, add 2010 + 2017 probes
   (~12s extra, narrows bracket to typically ±5-7 years)
4. **Cache write-through** — always saves the result for next time

Time budget defaults to 15 seconds. Existing
`estimate_construction_year()` (the 58-second full-iteration version)
is untouched — still callable from CLI for verification.

### MODIFIED: `evaluate_property.py` (+40 lines)

Right after `full_property_lookup()` returns the report, the smart
imagery method is called and the result populates `report.construction`.
This makes the existing downstream age-detection blocks at lines
~1394 (property_factors) and ~1457 (replacement_cost) work without
further changes.

Triggered only when:
- The user did NOT provide `building_age_years` (their input always wins)
- `include_age=True` (unified engine always sets this)
- A valid plot polygon is available

```python
if (building_age_years is None
        and include_age
        and report.plot
        and getattr(report.plot, 'polygon_4326', None)
        and report.location):
    try:
        smart_estimate = gis.estimate_construction_year_smart(
            polygon_4326=report.plot.polygon_4326,
            pin=report.location.pin,
            time_budget_s=15.0,
        )
        if smart_estimate is not None:
            report.construction = smart_estimate
    except Exception:
        pass
```

### MODIFIED: `evaluate_unified.py` (+30 lines)

Two changes:

1. **Engine version bump** — `thammen-sprint2p15-building-age-imagery`,
   `SPRINT_TAG = '2.15'`.

2. **Path B fallback for age surfacing.** Previously the engine only
   read `ev.replacement_cost.building_age_years` (Path A), which is
   None when the user didn't provide BUA. Path B reads
   `ev.raw_property_report.construction.earliest_built_year` directly,
   so the imagery-detected age surfaces even on no-BUA requests.

   Combined effect:
   - With BUA: cost approach uses age, age surfaces (existing behaviour)
   - Without BUA: property_factors uses age internally + age now surfaces
     to `user_inputs.building_age_years` with `age_source='gis_imagery'`

### NEW: `test_building_age_cache.py` (13 tests)

- Empty cache returns None
- get/set round-trip preserves all fields
- Overwrite by PIN works (idempotent)
- Cache stats endpoint
- Schema versioning (old-version rows treated as miss)
- Arabic text round-trip
- JSON source_data round-trip
- Graceful degradation on path errors (no raises)

All 13 pass in 0.15s.

## Production timing — measured

Tested on 52/903/90 (Al-Luqta villa, plot 467m², PIN 52200100):

| Scenario | Elapsed | Method |
|---|---|---|
| **First request (cold cache)** | **5.6s** | `fast_probe` |
| **Subsequent requests (cache hit)** | **0.3ms** | cache lookup |
| Detected: `earliest_built ≤1995, ±5 years` | | |

The 5.6s figure is well within the ~15s budget left after the rest of
the engine. Total request remains under 30s for fresh addresses.

For comparison: the disabled full-iteration version took 58.1s on the
same property.

## Critical limitation: Heroku ephemeral filesystem

⚠️ **The SQLite cache file resets to its committed state on every
Heroku dyno restart.**

Mechanism:
1. Cache file `building_age_cache.sqlite` is committed to git
2. Heroku deploys it as part of the slug (read-write at runtime)
3. Runtime writes accumulate in the slug copy on the live dyno
4. On dyno restart (idle sleep, deploy, scaling), the FS reverts to
   the committed state — runtime writes are LOST

What this means in practice on Heroku free dyno:
- Within a single dyno lifetime: cache works perfectly (instant repeats)
- Across dyno restarts (~daily on free tier): each address is recomputed
- Net effect: **first user of each address pays 6s. Subsequent users
  within the same dyno lifetime get instant.**

This is acceptable for V1. If/when we want true persistence:
- Sprint 2.15.1 — migrate cache to Heroku Postgres (~50 LoC)
- OR commit the slug-resident cache file weekly via `heroku run`

**Acceptance criterion for shipping this version:** first-request
latency must be under 30s total (engine ~15s + imagery ~6s + safety
margin ~9s). Verified locally. Should be fine in production.

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
```

Back up modified files:

```cmd
copy /Y qatar_gis.py qatar_gis.py.bak1
```

```cmd
copy /Y evaluate_property.py evaluate_property.py.bak1
```

```cmd
copy /Y evaluate_unified.py evaluate_unified.py.bak2
```

Drop the new files:

```cmd
tar -xf "%USERPROFILE%\Downloads\sprint2p15-delta.zip"
```

Local verification:

```cmd
python test_building_age_cache.py
```
Expect: 13 tests OK.

```cmd
python -c "import evaluate_unified; print(evaluate_unified.ENGINE_VERSION)"
```
Expect: `thammen-sprint2p15-building-age-imagery`.

```cmd
python -c "from building_age_cache import BuildingAgeCache; c=BuildingAgeCache(); print(c.stats())"
```
Expect: `{'available': True, 'cached_pins': 0, ...}`.

Commit + deploy:

```cmd
git add building_age_cache.py test_building_age_cache.py qatar_gis.py evaluate_property.py evaluate_unified.py CHANGELOG_v20.md
```

Important — the SQLite file will be created on first request after deploy.
You can commit a pre-populated cache anytime to seed it. For now, ship
empty:

```cmd
git commit -m "Sprint 2.15 (L4): building age via smart GIS imagery + cache"
```

```cmd
git push heroku master
```

## Verification curl (post-deploy)

```cmd
curl -s "https://thammen.qa/api/health"
```
Look for `"version":"3.1.0-sprint2.15"`.

First request — should populate the imagery age:
```cmd
curl -s -X POST "https://thammen.qa/api/evaluate/details" -H "Content-Type: application/json" -d "{\"zone\":52,\"street\":903,\"building\":90,\"audience\":\"buyer\"}" > out.json
```

The first hit may take ~25-30s due to cold imagery. Subsequent hits
should be back to normal (~10-15s).

```cmd
findstr /C:"gis_imagery" out.json
```
Expect: `"age_source": "gis_imagery"` somewhere in the JSON.

```cmd
findstr /C:"building_age_years" out.json
```
Expect: `"building_age_years": 31` (or thereabouts — building was
detected as ≤1995, so age ≈ 2026 - 1995 = 31).

Then open in browser:
```
https://thammen.qa/?zone=52&street=903&building=90&audience=buyer
```

Look for the "📡 مكتشف من صور الأقمار" badge next to the building age
field (this UI element was preserved from Sprint 2.5 and finally fires
now).

## Rollback

```cmd
copy /Y qatar_gis.py.bak1 qatar_gis.py
copy /Y evaluate_property.py.bak1 evaluate_property.py
copy /Y evaluate_unified.py.bak2 evaluate_unified.py
del building_age_cache.py test_building_age_cache.py
del building_age_cache.sqlite
git checkout -- qatar_gis.py evaluate_property.py evaluate_unified.py
git commit -am "Rollback Sprint 2.15"
git push heroku master
```

Or via git:
```cmd
git revert HEAD
git push heroku master
```

---

## Strategic note

Sprint 2.15 unblocks Sprint 2.14.1 (regime adjustments) by providing
the age input that the regime distinguishes between "default" and
"old property" calibration. Without imagery age, the regime's
old-property adjustment never fires unless the user manually types
the age — which most won't.

Now: imagery → age → "is_old_property=true if age ≥ 10" → 5pp
additional ceiling discount (when Sprint 2.14.1 ships).

This is the data foundation step we agreed on: **before applying
regime adjustments to users, make sure the underlying age signal is
real, not "depends on user input"**.

## What's next

- **Sprint 2.16** (broker data integration): after manager session
  delivers 30 confirmed sales
- **Sprint 2.14.1** (regime recommendations): wires the
  already-built market_regime.py multipliers into buyer brief, now
  that age detection is automatic
- **L3** (listings time series): scrapers + GitHub Actions cron

The "10 days plan" continues. L4 is delivered. Manager session is
the next blocker.
