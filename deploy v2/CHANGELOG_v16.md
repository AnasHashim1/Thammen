# CHANGELOG — Sprint 2.11: Context Preservation in Fast Paths

**Engine version:** `thammen-sprint2p11-context-preservation`
**Date:** 2026-05-13
**Files changed:** `evaluate_unified.py`, `index.html`
**Builds on:** Sprint 2.10 (v15)

---

## Why this matters

A field audit on 2026-05-13 ran 5 diverse properties through
`POST /api/evaluate` and compared the response against Qatar GIS
ground truth. The result:

| # | Address | GIS district | thammen district | Path |
|---|---|---|---|---|
| 1 | 52/903/90 | اللقطة | اللقطة ✅ | main (full pipeline) |
| 2 | 51/835/17 | الغرافة | **None ❌** | DCF (compound_large) |
| 3 | 70/1278/34 | روضة الحمامة | روضة الحمامة ✅ | main |
| 4 | 27/220/53 | ام غويلينة | **None ❌** | out_of_scope (commercial) |
| 5 | 69/305/201 | غار ثعيلب | **None ❌** | fast_insufficient (palace) |

**3 out of 5 (60%) lost their district name** even though GIS resolves it
correctly in every case. They also lost `geometric_factors` and
`location_features` entirely. The user — looking at the `insuf` card —
sees only: address, asset type, plot area, map. The neighborhood name
(which thammen has, for free, one GIS call away) is hidden.

Render trace (`index.html` line 444–471): the `insuf` branch shows
address + asset_type + plot_area_m2 only. The main info card at line 480
that does `if(d.district)h+=ri('المنطقة',d.district)` lives inside
`if(hasValuation){...}` and is therefore never reached for properties
without a valuation. So `district` was *fetched* upstream (line 2055 in
gate 3), then thrown away in the response, then unrenderable downstream
anyway. Three layers of negligence.

Scope evidence (Qatar GIS counts):
- Non-residential zoning (commercial CF/CCC/COM/EC/MUC + industrial
  LInd/MInd/HInd + special SD + tourist TC/TU + mixed-use MU1/MU2/MU3):
  **~30,000+ polygons of 190,214 zoned (~16%)**
- Plus in-scope assets (palace/villa/raw_land/compound_small) in
  districts where MoJ has 0 transactions for that asset class — routed
  to fast paths via gate 3 in `evaluate_unified.py:2061`
- **Overall estimate: 15–25% of Qatar addresses lose district name**

Bonus bug found in the audit: the `reason_ar` text in
`_build_fast_insufficient_data_response` was written for compound/tower
assets but the function is also reached by other in-scope assets
(palace, villa, raw_land, compound_small) when their district has no
MoJ comparable. For the palace at 69/305/201 the user saw:

> "هذا الأصل من نوع **'قصر'** — لا توجد عينة مقارنة في سجلات وزارة العدل
> لهذه الفئة (**الكومباوندات الكبيرة والأبراج** تُسجَّل بأرقام مرجعية
> موحَّدة...)"

A palace owner reading about "compounds and towers" loses trust in the
classification.

## Root cause

Four response-builder functions in `evaluate_unified.py` hardcoded
`district: None` and `geometric_factors: None` even though the calling
code has `loc` (PropertyLocation with lon/lat) and `plot` (PlotInfo
with pdarea + pd_no) right there in scope:

| Line | Function | Trigger |
|---|---|---|
| 1297 | `_build_fast_insufficient_data_response` | DCF assets w/o inputs OR in-scope w/ MoJ-empty district |
| 1415 | `_build_fast_listing_only_response` | DCF assets + listing_price (no rental) |
| 1641 | `_build_fast_income_only_response` | DCF assets + rental_income |
| 1751 | `_build_out_of_scope_response` | commercial / industrial / agricultural |

The `reason_ar` parenthetical at line 1312–1316 inside
`_build_fast_insufficient_data_response` was DCF-specific text reused
unconditionally for any asset routed to this builder.

## What this patch does

### New helper (`evaluate_unified.py:1271-1322`)

```python
def _enrich_fast_context(loc, plot):
    """Return cheap GIS context for fast-path response builders.

    Returns dict with 'district' (str|None) + 'geometric_factors' (dict|None).
    Never raises — degrades to (None, None) on any failure.
    """
    district_ar = None
    try:
        if loc is not None and loc.lon is not None and loc.lat is not None:
            from qatar_gis import QatarGIS
            _gis = QatarGIS(verbose=False)
            _d = _gis.get_district_at_point(loc.lon, loc.lat)
            district_ar = _d.aname if _d else None
    except Exception as _e:
        print(f"[sprint2.11] district lookup failed: {_e}", file=sys.stderr)

    gf = None
    if plot is not None:
        pd_display = None
        try:
            if plot.pd_no and str(plot.pd_no) != '0':
                pd_display = str(plot.pd_no)
        except Exception:
            pd_display = None
        gf = {
            'polygon_available': True,
            'plot_area_m2_verified': plot.pdarea,
            'pd_no': pd_display,
        }
    return {'district': district_ar, 'geometric_factors': gf}
```

Cost: 1 GIS call (~150–300ms) for district, 0 calls for geometric_factors
(both `plot.pdarea` and `plot.pd_no` are already in memory). Wrapped in
try/except so any GIS error degrades to the pre-2.11 `district=None`
behavior — fast path stays fast.

PD_NO=0 (the unsubdivided-parcel sentinel, common for compounds) is
suppressed from display rather than shown as the string `"0"`.

### Four builders refactored

Each replaces:
```python
'district': None,
...
'geometric_factors': None,
```
with:
```python
_ctx = _enrich_fast_context(loc, plot)
...
'district': _ctx['district'],
...
'geometric_factors': _ctx['geometric_factors'],
```

### Copy-paste fix (`evaluate_unified.py:1364-1372`)

`_build_fast_insufficient_data_response.valuation.reason_ar` now branches
on whether the asset is actually a DCF type:

```python
_DCF_ASSETS_FOR_REASON = frozenset({'compound_large', 'tower', 'apartment_building'})

_reason_paren = (
    ' (الكومباوندات الكبيرة والأبراج تُسجَّل بأرقام مرجعية موحَّدة بدلاً من مقارنات سعر/م²)'
    if asset_type in _DCF_ASSETS_FOR_REASON
    else (f' في {_ctx["district"]}' if _ctx.get('district') else '')
)
```

A palace owner now reads: *"...لهذه الفئة في غار ثعيلب."*
A compound owner still reads: *"...لهذه الفئة (الكومباوندات الكبيرة والأبراج...)."*

### Frontend (`index.html:456`)

Adds one line in the `insuf` card, right after address, before asset type:

```javascript
if(d.district)h+='<div style="margin-bottom:6px"><strong>المنطقة:</strong> '+d.district+'</div>'; // Sprint 2.11
```

No other frontend changes. The existing `geometric_factors` card
(line 670–708) already renders `plot_area_m2_verified` + `pd_no` when
`gf` is populated — it just wasn't reaching anyone because backend was
sending null. With backend now populating it, that card lights up
automatically for fast-path properties.

### Version bump (`evaluate_unified.py:38-39`)

```python
ENGINE_VERSION = 'thammen-sprint2p11-context-preservation'
SPRINT_TAG = '2.11'
```

Per Sprint 2.10, `api.py` needs no changes — both `/api/health` and
`/api/evaluate` pick up the new strings automatically.

---

## Verification — empirical evidence

### Unit test (helper, against the same 5 properties)

```
Z51/S835/B17: district='الغرافة' (expected 'الغرافة')        ✅
   geometric_factors = polygon_available=True, pdarea=67536.0, pd_no=None
Z27/S220/B53: district='ام غويلينة' (expected 'ام غويلينة')  ✅
   geometric_factors = polygon_available=True, pdarea=22163.0, pd_no='PD/3500/2003'
Z69/S305/B201: district='غار ثعيلب' (expected 'غار ثعيلب')   ✅
   geometric_factors = polygon_available=True, pdarea=3378.0, pd_no='PD/197/2014'
Z52/S903/B90: district='اللقطة' (expected 'اللقطة')          ✅
   geometric_factors = polygon_available=True, pdarea=467.0, pd_no='PD/3063/2001'
```

4/4 PASS. PD_NO=0 correctly suppressed on the compound (would have
shown the misleading string `'0'` otherwise).

### Builder smoke test (calls `_build_fast_insufficient_data_response` directly)

**Palace 69/305/201, before patch:**
```
district           : None
reason_ar          : "هذا الأصل من نوع "قصر" — لا توجد عينة مقارنة في سجلات
                     وزارة العدل لهذه الفئة (الكومباوندات الكبيرة والأبراج
                     تُسجَّل بأرقام مرجعية موحَّدة...)."
```

**Palace 69/305/201, after patch:**
```
district           : 'غار ثعيلب'
geometric_factors  : {'polygon_available': True, 'plot_area_m2_verified': 3378.0,
                     'pd_no': 'PD/197/2014'}
reason_ar          : "هذا الأصل من نوع "قصر" — لا توجد عينة مقارنة في سجلات
                     وزارة العدل لهذه الفئة في غار ثعيلب. لتقييم دقيق..."
```

**Compound 51/835/17, after patch (DCF reason text preserved):**
```
district           : 'الغرافة'
geometric_factors  : {'polygon_available': True, 'plot_area_m2_verified': 67536.0,
                     'pd_no': None}
reason_ar          : "هذا الأصل من نوع "مجمع فلل كبير" — لا توجد عينة مقارنة
                     ... (الكومباوندات الكبيرة والأبراج تُسجَّل بأرقام مرجعية
                     موحَّدة...)."
```

### Static checks

- Python syntax (`ast.parse`): clean ✅
- Hardcoded `'district': None,` occurrences in `evaluate_unified.py`: **0** (was 4)
- Hardcoded `'geometric_factors': None,` occurrences: **0** (was 4)
- Helper exported as `_enrich_fast_context`: ✅
- `index.html` district render in insuf card: ✅
- `api.py` unchanged: ✅ (Sprint 2.10 contract honored)

---

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak11
copy /Y index.html index.html.bak10
tar -xf "%USERPROFILE%\Downloads\sprint2p11-context-preservation.zip"
findstr /C:"Sprint 2.11" evaluate_unified.py
findstr /C:"_enrich_fast_context" evaluate_unified.py
findstr /C:"Sprint 2.11" index.html
git add evaluate_unified.py index.html CHANGELOG_v16.md
git commit -m "Sprint 2.11: Context preservation in fast paths (district + geometry surfaced)"
git push heroku master
```

## Verification curl

```bash
# 1. Version bump propagated to both endpoints
curl https://thammen.qa/api/health | jq '{version, engine_version}'
# Expected:
# { "version": "3.1.0-sprint2.11",
#   "engine_version": "thammen-sprint2p11-context-preservation" }

# 2. compound_large now surfaces district + geometric_factors
curl -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"zone":51,"street":835,"building":17,"audience":"buyer"}' \
  | jq '{district, geometric_factors, asset_type}'
# Expected:
# { "district": "الغرافة",
#   "geometric_factors": { "polygon_available": true,
#                          "plot_area_m2_verified": 67536, "pd_no": null },
#   "asset_type": "compound_large" }

# 3. palace (in-scope, MoJ-empty district) — reason_ar no longer mentions compounds
curl -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"zone":69,"street":305,"building":201,"audience":"buyer"}' \
  | jq '{district, "reason": .valuation.reason_ar}'
# Expected: district="غار ثعيلب", reason_ar mentions "غار ثعيلب" not "الأبراج"

# 4. commercial (out-of-scope) — district now populated
curl -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"zone":27,"street":220,"building":53,"audience":"buyer"}' \
  | jq '.district'
# Expected: "ام غويلينة"

# 5. Regression: standalone_villa main path still works the same
curl -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"zone":52,"street":903,"building":90,"audience":"buyer"}' \
  | jq '{district, "amount": .valuation.amount}'
# Expected: district="اللقطة", amount≈2000000 (unchanged from 2.10)
```

If steps 2–4 return `district: null`, the GIS lookup failed silently —
re-run, check `heroku logs --tail` for `[sprint2.11] district lookup
failed`. If the failure persists, that's a Heroku-side egress block
on `services.gisqatar.org.qa` that needs separate investigation, but
the response itself will still be valid (degrades to pre-2.11 behavior).

## What's NOT in this patch (intentional Sprint 2.11 scope)

- **`location_features` is still `None` in fast/out-of-scope paths.**
  Populating it would require adding zoning + landmark + road lookups
  to `qatar_gis.py` (new endpoint methods). That's a separate Sprint
  (~2.13 candidate). The existing geometric_factors card now lights up
  with `plot_area_m2_verified` + `pd_no`, which is the cheapest meaningful
  win.

- **Asset classification accuracy.** Property 69/305/201 in Lusail
  is classified as "palace" — that's almost certainly a misclassification
  (Lusail B201 is most likely an apartment tower). The classifier
  in `qatar_gis.py:classify_asset` uses plot size + shape only, no
  building context. That deserves its own audit Sprint.

- **`property_info.zoning` populated in fast paths.** The frontend has
  `if(pi.zoning)h+=ri('التصنيف',pi.zoning)` at line 484 but it lives
  inside `if(hasValuation)` so it wouldn't render for fast paths anyway.
  Requires a frontend rearrangement to expose. Defer.

- **`named_landmarks` (malls, metros, mixed-use venues).** Same as
  location_features — requires new GIS endpoints. Higher-value addition,
  separate Sprint.

## Methodological note

This Sprint followed the audit discipline in Section 5 of
`__Thammen__thammen.qa____Project_Instructions`:

1. ✅ Picked 5 diverse properties covering different zones, ages,
   asset types
2. ✅ Pulled ground truth from Qatar GIS (PIN, polygon, district,
   zoning) for each
3. ✅ Hit `POST /api/evaluate` and parsed each response
4. ✅ Compared field-by-field (district, plot_area_m2, asset_type)
5. ✅ Opened `index.html` and grep'd for `district` — confirmed the
   bug renders to the user (only address+asset_type+plot_area in the
   insuf card; district populated nowhere in that branch)
6. ✅ Quantified scope via GIS counts (16% by zoning alone, +5–10%
   by MoJ-empty districts)
7. ✅ Only then wrote this Sprint

No old-audit recycling. No claims based on memory. The 3/5 evidence
came from live calls today.
