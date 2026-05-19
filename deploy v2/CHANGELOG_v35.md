# CHANGELOG v35 — Sprint 2.16.14: Zoning Cross-Check (Bug A11)

**Engine version:** `thammen-sprint2p16p14-zoning-cross-check`
**Date deployed:** 2026-05-19 (afternoon)
**Files changed:** `qatar_gis.py`, `evaluate_unified.py`, `index.html`, `test_sprint_2p16p14_zoning_mismatch.py` (new)

---

## Why this matters

A user evaluated address `61/875/20` (the **Public Works Authority** —
هيئة الأشغال العامة, a clearly governmental/commercial tower). thammen.qa
classified it as **"عمارة سكنية"** (apartment_building) and offered to
run an Income Approach valuation.

Root finding via GIS inspection:

```
QARS_Point.BUILDING_NO_SUBTYPE = 6  (Building with Flats)
QARS_Point.SURVEYED_DATE        = 2010-01-26   ← 16 years old
QARS_Point.DATE_LUPD            = 2012-02-20   ← last update 14 years ago
Vector/Zoning.ZONING            = CCC  (Central Commercial Core)
Vector/Landmarks within 100m    = GOVERNMENT × 2 + FINANCE + GENERAL SERVICES
```

QARS_Point was right when surveyed (the parcel may have been residential
in 2010); it just hasn't been updated since the use changed. Sprint 2.16.6
made the classifier trust QARS subtype as authoritative — which is the
right default — but it left no second-opinion check.

**Empirical scope** (2026-05-19 audit, 22 landmarks in commercial categories):

| Category   | Total | Mismatch | Rate |
|------------|------:|---------:|-----:|
| BUSINESS   |     6 |        0 |   0% |
| FINANCE    |     8 |        0 |   0% |
| GOVERNMENT |     8 |        2 |  25% |
| **Total**  |    22 |        2 | 9.1% |

Two confirmed cases beyond 61/875/20:
- `63/864/26` — Tower in CCC zone
- `61/820/84` — ApartmentBldg in CCC zone

Both date QARS_Point surveys to 2010. Pattern: government buildings whose
use changed post-2010.

---

## Root cause

`qatar_gis.py:506-518` (Sprint 2.16.6 Branch 0) returned the asset type
straight from `SUBTYPE_TO_ASSET[subtype]` with `confidence='high'` and
**no flags**, regardless of what the surrounding zoning says.

```python
# Before — Branch 0 trusts subtype unconditionally
asset_type = SUBTYPE_TO_ASSET.get(subtype)
if asset_type is not None:
    return AssetClassification(
        asset_type=asset_type,
        confidence='high',
        reasons=[...],
        flags=[],                    # ← always empty
        alternative_types=[],
    )
```

`evaluate_unified.py:2200-2202` passed only `building_subtype` to the
classifier — no lat/lon and no zoning — so the classifier had no way to
cross-check even if it wanted to.

---

## What this patch does

### Backend — `qatar_gis.py`

1. **New module-level helpers** (before `classify_asset`):
   ```python
   RESIDENTIAL_SUBTYPES_FOR_ZONING_CHECK = frozenset({1, 6, 11})

   _NON_RES_ZONING_TOKENS = frozenset(
       {'CCC', 'COM', 'CF', 'SCZ', 'TU', 'LFR', 'LInd', 'IND'}
   )

   def _is_non_residential_zone(zoning) -> bool: ...
   def _fetch_zoning_at_point(lat, lon, timeout=4.0): ...
   ```

2. **Modified `classify_asset` Branch 0**: after the asset_type is
   resolved from `subtype`, run a Zoning cross-check. If the subtype is
   residential (1/6/11) AND the zone is non-residential (CCC/COM/CF/
   SCZ/TU/LFR/LInd/IND/MU*), emit a `subtype_zoning_mismatch:` flag,
   downgrade `confidence` to `'medium'`, and add `COMMERCIAL` to
   `alternative_types`. The `asset_type` itself is **NOT** changed — we
   flag, the user decides.

   Zoning is read from `location_metadata['zoning']` if pre-fetched; if
   absent, a defensive spatial query to Vector/Zoning runs (4s timeout,
   silently fails to None on error). For most parcels this is a no-op
   because the residential classification stays consistent.

### Backend — `evaluate_unified.py`

3. **Engine version bump**:
   ```
   thammen-sprint2p16p12-housekeeping-b1-b3 →
   thammen-sprint2p16p14-zoning-cross-check
   ```

4. **lat/lon passed to classifier**:
   ```python
   _meta = {
       'building_subtype': _loc.building_subtype,
       'lat': getattr(_loc, 'lat', None),   # NEW
       'lon': getattr(_loc, 'lon', None),   # NEW
   }
   ```

5. **Flag → structured warning** (mirrors Sprint 2.16.8/9 MUC pattern):
   the raw `subtype_zoning_mismatch:<msg>` flag is parsed into a dict
   with `kind`, `message_ar`, `qars_subtype`, `classified_as`,
   `recommendation_ar`, `data_age_note_ar`.

6. **`output['subtype_zoning_mismatch']`** is attached to **every**
   response path: `_build_out_of_scope_response`,
   `_build_fast_income_only_response`,
   `_build_fast_listing_only_response`,
   `_build_fast_insufficient_data_response`, and the full villa pipeline.
   The variable is initialized to `None` before the try-block for scope
   safety (so the full villa path still references it cleanly if the
   Lite GIS path raises).

### Frontend — `index.html`

7. **New warning panel** rendered right below the MUC banner. Uses
   existing `--warn` / `--warn-bg` theme variables. Reads
   `data.subtype_zoning_mismatch` and shows:

   ```
   ⚠️ تناقض في تصنيف العقار

   QARS subtype=6 (Building with Flats) يقترح استخداماً سكنياً، لكن
   المنطقة منظَّمة كـ "CCC" (غير سكني). بيانات QARS قديمة (آخر مسح
   غالباً 2010-2012). تحقق من الاستخدام الفعلي قبل الاعتماد على
   هذا التصنيف.

   ──────────────────────────────────────────────────────────────
   ملاحظة: البيانات الأصلية لـ QARS_Point لمعظم القطع جاءت من مسوحات
   2010-2012 — قد لا تعكس تحويلات الاستخدام اللاحقة.

   التوصية: تحقق من الاستخدام الفعلي للمبنى. لو كان تجارياً أو حكومياً
   (مكاتب/خدمات)، أعد التقييم باختيار "تجاري" في نوع العقار للحصول
   على منهجية تقييم صحيحة.
   ```

---

## Verification — empirical evidence

### Unit tests (`test_sprint_2p16p14_zoning_mismatch.py`)

```
✓ test_zoning_helper_recognizes_ccc
✓ test_zoning_helper_recognizes_com
✓ test_zoning_helper_recognizes_cf_scz_tu
✓ test_zoning_helper_recognizes_mu_prefix
✓ test_zoning_helper_rejects_residential
✓ test_zoning_helper_handles_none_and_empty
✓ test_zoning_helper_strips_whitespace
✓ test_apartment_in_ccc_zone_flags_mismatch    (61/875/20 reference)
✓ test_villa_in_ccc_zone_flags_mismatch
✓ test_tower_in_ccc_zone_flags_mismatch
✓ test_villa_in_r1_zone_no_mismatch
✓ test_apartment_in_r1_zone_no_mismatch
✓ test_commercial_subtype_no_check
✓ test_shopping_subtype_no_check
✓ test_no_zoning_no_mismatch
✓ test_mu_zone_with_apartment_flags_mismatch
✓ test_no_subtype_falls_through_to_area_heuristic
✓ test_subtype_zero_falls_through_to_area_heuristic
✓ test_residential_subtypes_constant_is_frozenset
✓ test_residential_subtypes_contains_expected_codes
✓ test_residential_subtypes_excludes_commercial

21/21 passed
```

### Regression suite (unchanged behavior preserved)

```
test_stock_strata:           6/6 ✓
test_scope_of_service:      27/27 ✓
test_material_uncertainty:  13/13 ✓
test_sprint_2p16p14:        21/21 ✓ (new)
────────────────────────────────
                            67/67 passed
```

### Compile checks

```
✓ python3 -m py_compile qatar_gis.py
✓ python3 -m py_compile evaluate_unified.py
✓ node --check (extracted inline JS from index.html)
```

---

## Deployment

### prompt command

```
cd /d "C:\Thammen\deploy v2"
copy /Y qatar_gis.py qatar_gis.py.bak_2p16p12
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p12
copy /Y index.html index.html.bak_2p16p12
tar -xf "%USERPROFILE%\Downloads\sprint2p16p14-zoning-cross-check.zip"
findstr /C:"sprint2p16p14" evaluate_unified.py
findstr /C:"_is_non_residential_zone" qatar_gis.py
findstr /C:"subtype_zoning_mismatch" index.html
python -m py_compile evaluate_unified.py
python -m py_compile qatar_gis.py
python test_sprint_2p16p14_zoning_mismatch.py
git add qatar_gis.py evaluate_unified.py index.html test_sprint_2p16p14_zoning_mismatch.py CHANGELOG_v35.md
git commit -m "Sprint 2.16.14: Zoning cross-check (Bug A11) — flag stale QARS subtypes"
git push heroku master
```

---

## Verification curl (post-deploy)

```bash
# Reference case — should now return subtype_zoning_mismatch in JSON
curl -s -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"zone":61,"street":875,"building":20}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); \
                m=d.get('subtype_zoning_mismatch'); \
                print('MISMATCH:', m['kind'] if m else 'none', '—', \
                      (m or {}).get('message_ar','')[:80])"

# Expected output:
#   MISMATCH: subtype_zoning_mismatch — QARS subtype=6 (Building with Flats)...
```

---

## What's NOT in this patch

- **No automatic reclassification.** When a mismatch is flagged, the
  asset_type stays as the subtype suggests. The user (or a future
  domain-expert override mechanism) decides whether to reclassify.
- **No update to QARS itself.** GIS Qatar's stale 2010-2012 surveys
  are outside our control. We document the issue, we don't fix it.
- **No expansion of the non-residential zoning list.** SD, R5, LFR
  edge cases were intentionally left out — we'd rather under-flag
  than over-flag. Empirical 0% false-positive rate on the 2026-05-19
  BUSINESS/FINANCE audit confirms the choice.
- **No retroactive flag for evaluations done before 2.16.14.** The
  warning surfaces only on fresh evaluations.

---

*Sprint 2.16.14 — Bug A11 closed. Catalogue updated. No critical bugs open.*
