# CHANGELOG — Sprint 2.16.6: Classifier v2 (BUILDING_NO_SUBTYPE-aware)

**Engine version:** `thammen-sprint2p16p6-classifier-v2-subtype-aware`
**SPRINT_TAG:** `2.16.6` → /api/health reports `3.1.0-sprint2.16.6`
**Date:** 2026-05-18
**Files updated:** `qatar_gis.py`, `evaluate_unified.py`
**Severity:** 🟠 High-leverage fix — resolves bug A1 (catalogued in Section 12)

---

## Why this matters — bug A1, finally solvable

### The bug (catalogued 2026-05-13, ~5 months old)

`qatar_gis.py:classify_asset` Branch 5 was:

```python
if 3000 <= area < 10000:  # any plot 3K-10K m²
    return PALACE   # no zoning check, no subtype check
```

This blindly labeled every 3K-10K m² polygon as PALACE. Scope: **15,881
polygons across Qatar** (~7% of all CadastrePlots). Included:

- All Lusail towers (5K-8K m² typical footprint)
- West Bay towers
- Most shopping complexes (e.g. 27/220/53 Umm Ghuwailina)
- Several mid-sized apartment buildings

Effect: when PALACE was returned, Thammen's V1_OUT_OF_SCOPE list rejected
the asset entirely with `"تصنيف غير مطابق لأي فئة مدعومة"`. A user trying
to evaluate a Lusail tower (69/305/201 = the canonical test case) got a
useless `insufficient_data` response.

The roadmap (Section 13) had this as a "Sprint 2.15" target but Sprint
2.15 was diverted to imagery work. A1 sat unsolved.

### Why it's solvable now (and not before)

Sprint 2.16.5 migrated the address lookup endpoint to khazna's
`QARS_Point/FeatureServer/0`. That service exposes `BUILDING_NO_SUBTYPE`
— the **official Qatar Ministry of Municipality classification** of each
QARS point. Codes:

| Code | Type |
|---|---|
| 1 | Villa/House |
| 2 | Compound with Villas |
| 3 | Compound with Villas and Flats |
| 4 | Shopping Complex |
| 6 | Building with Flats |
| 11 | **Tower** ← the A1 fix |
| 13 | Commercial |
| (others) | IZBA, FARM, Chalet, Park, etc. |

Sprint 2.16.5 already fetched this value into `PropertyLocation.building_subtype`
but never used it. Sprint 2.16.6 wires it through to the classifier.

---

## What this patch does

### Change 1: New "Branch 0" in `qatar_gis.py:classify_asset`

Before any area-based branch runs, check if `location_metadata` provided
a `building_subtype`. If it's a known mapped code (1, 2, 3, 4, 6, 11, 13),
return the corresponding AssetType with `confidence='high'`.

```python
SUBTYPE_TO_ASSET = {
    1:  AssetType.STANDALONE_VILLA,
    2:  AssetType.COMPOUND_SMALL,
    3:  AssetType.COMPOUND_SMALL,
    4:  AssetType.COMMERCIAL,         # Shopping Complex
    6:  AssetType.APARTMENT_BUILDING,
    11: AssetType.TOWER,              # ← Lusail tower fix
    13: AssetType.COMMERCIAL,
}
```

**Defensive design — fallback safety:**
- `subtype is None` → falls through to area heuristic (old behavior)
- `subtype == 0` (Unknown) → falls through
- `subtype` is a code not in `SUBTYPE_TO_ASSET` (5=Under Construction,
  8=Sports Club, 9=Hospital, 10=Masjid, 12=Park, 14-19=IZBA/FARM/Desert
  House/Chalet/Stone Crusher/Metro, 99=Others) → falls through

This means: **no property can be misclassified worse than before**.
Properties WITH a clear subtype gain accurate classification; properties
without gain nothing but lose nothing.

### Change 2: Thread `building_subtype` through `evaluate_unified.py:2097`

```diff
-     _quick = classify_asset(_plot, None)
+     _meta = None
+     if _loc and getattr(_loc, 'building_subtype', None) is not None:
+         _meta = {'building_subtype': _loc.building_subtype}
+     _quick = classify_asset(_plot, _meta)
```

`_loc` is the `PropertyLocation` returned from `find_property()`, which
since Sprint 2.16.5 already includes `building_subtype` populated from
QARS_Point. We just pipe it through.

---

## Empirical verification (this container, pre-deploy)

### Logic tests (11/11 passed)

```
✓ Tower (subtype=11, area=3378)        → tower
✓ Villa (subtype=1, area=600)          → standalone_villa
✓ Commercial large (subtype=13)        → commercial
✓ Shopping Complex (subtype=4)         → commercial
✓ Compound w/ Villas (subtype=2)       → compound_small
✓ Compound w/ Villas+Flats (subtype=3) → compound_small
✓ Apartment Building (subtype=6)       → apartment_building

Fallback safety (no regression):
✓ no metadata, area=3378 → palace        (preserves old A1 behavior)
✓ subtype=0 (Unknown)    → palace        (preserves old A1 behavior)
✓ subtype=14 (IZBA)      → palace        (unmapped → fallback)
✓ no metadata, area=600  → standalone_villa  (control)
```

### Pre-Sprint 2.16.6 production audit (Section 5 mandatory, completed)

8 addresses probed against current production (Sprint 2.16.5):

| Address | PDAREA | Current `asset_type` | Expected after 2.16.6 |
|---|---|---|---|
| **69/305/201** Lusail B201 | 3,378 | `palace` ❌ | `tower` (subtype=11) |
| 27/220/53 Umm Ghuwailina | 22,163 | `commercial` ✓ | `commercial` (same — bypassed by >10K branch) |
| 51/955/49 Al-Gharafa | 600 | `standalone_villa` ✓ | `standalone_villa` (subtype=1) |
| 56/565/10 J Seven A | 450 | `standalone_villa` ✓ | `standalone_villa` (subtype=1) |
| 56/565/12 J Seven B | 450 | `standalone_villa` ✓ | `standalone_villa` (subtype=1) |
| 51/835/17 Al-Gharafa compound | 67,536 | `compound_large` ✓ | `compound_large` (>50K still wins) |
| 70/1278/34 Roudat Al Hamama | 1,152 | `standalone_villa` ✓ | `standalone_villa` (subtype=1) |
| 55/290/10 Al-Maradh | 900 | `standalone_villa` ✓ | `standalone_villa` (subtype=1) |

The 7 control cases stay unchanged. **Lusail B201 is the only address
that flips** — exactly what A1 predicted.

---

## Downstream effects

When `_qtype` becomes `'tower'` (was `'palace'` → `'out_of_scope'`):

1. **`V1_OUT_OF_SCOPE`** does NOT include `tower` (it's in `V1_IN_SCOPE_DCF_ONLY`)
2. **Engine path:** `tower` runs the DCF/Income approach (Sprint 2.4a),
   not Sales Comparison (no MoJ comparables for towers anyway)
3. **Cap rate** for `tower`: 6.0% (from `evaluate_unified.py:94`)
4. **Output:** full DCF valuation with rental yield, NOI, cap rate
   reconciliation — same shape as compound_large currently gets

This means Sprint 2.16.6 unlocks **tower evaluation** as a side effect of
fixing classification. The DCF pipeline existed already; it just was
never reached by tower addresses.

---

## What is NOT in this patch

- **No new UI.** index.html untouched. The asset_type label shown in
  reports is generated server-side from the same `asset_type` string,
  so towers will get the existing tower label/description (defined
  elsewhere in `scope_of_service.py`).
- **No MME data.** Tower DCF still uses MoJ rental data for the
  municipality average. Sprint 2.29 (MME apartment integration) would
  add per-unit rental comparables for towers.
- **No domain-specific tweaks.** Cap rate stays 6.0% for towers. That
  may need calibration once we have confirmed sales of Lusail
  apartments — but not today.
- **Sub-subtype distinction.** Subtypes 2 (Compound w/ Villas) and 3
  (Compound w/ Villas+Flats) both → COMPOUND_SMALL. The
  `detect_compound_extent` logic (Sprint earlier) can still promote
  to COMPOUND_LARGE based on area + neighbor scanning.

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y qatar_gis.py qatar_gis.py.bak_2p16p5
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p5
tar -xf "%USERPROFILE%\Downloads\sprint2p16p6-classifier-v2.zip"
findstr /C:"sprint2p16p6" evaluate_unified.py
findstr /C:"Branch 0" qatar_gis.py
git add qatar_gis.py evaluate_unified.py CHANGELOG_v28.md
git commit -m "Sprint 2.16.6: classifier v2 — subtype-aware (fixes A1 palace bug)"
git push heroku master
```

## Post-deploy verification

1. **Health check:**
   ```
   curl https://thammen.qa/api/health
   ```
   Expected: `"version": "3.1.0-sprint2.16.6"`

2. **A1 fix verification — the critical test:**
   ```
   curl -X POST https://thammen.qa/api/evaluate/details ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201}"
   ```
   Expected:
   - `asset_type`: `"tower"` (was `"palace"`)
   - `valuation.method`: NOT `"insufficient_data"`
   - `valuation.amount`: real number (income-approach derived)

3. **Regression check on control addresses:**
   - `51/955/49` should still be `standalone_villa` with the same valuation
   - `56/565/10` should still be `standalone_villa`
   - `51/835/17` should still be `compound_large`

   If ANY of these flip → investigate (might indicate subtype data drift).

---

## Files in this patch

```
sprint2p16p6-classifier-v2.zip
├── qatar_gis.py            (MODIFIED: +50 lines — Branch 0 subtype classifier)
├── evaluate_unified.py     (MODIFIED: +7 lines — version bump + threading)
└── CHANGELOG_v28.md         (NEW: this file)
```

---

_Last updated: 2026-05-18 — Bug A1 from Section 12 finally resolved._
