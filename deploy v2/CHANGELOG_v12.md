# CHANGELOG — Sprint 2.6: Land vs Building Value Separation (Phase 1)

**Engine version:** `thammen-sprint2p6-land-building-split`
**Date:** 2026-05-13
**Files changed:** `evaluate_unified.py`, `evaluate_property.py`, `index.html`
**Builds on:** Sprint 2.5b

---

## Why this matters

RICS Red Book methodology distinguishes land value from building value.
MoJ records the TOTAL price of villa sales — not the split. But MoJ
also records pure-LAND transactions when villas are demolished or
empty plots are sold. Sprint 2.6 uses the area's land-only median to
estimate land value, then derives the implied building value as
residual (total − land).

This empirically validates the Qatar 10-Year Rule:
- For 30-year-old non-luxury villa in Luqta: building contributes
  only **4.8%** of total value — confirming the rule in real numbers
- For new luxury villa (same plot): building contributes **21.3%**
- For 30-year-old large BUA in Bou Hamour: building contributes **15.0%**
  (still modest because of age, despite extra floors/basement/annexes)

## What this patch does

### Backend (`evaluate_property.py`)
- Adds `moj_reference` field to `PropertyEvaluation` dataclass
- Populates it from `moj_ref_dict` so downstream consumers can access
  the MoJ land categories without re-fetching

### Backend (`evaluate_unified.py`)

New function `_decompose_value()`:
- Input: valuation amount, plot area, BUA, MoJ reference
- Output: `{land: {...}, building_implied: {...}, methodology_note_ar}`
- Logic:
  1. Read `moj_ref.categories.land.price_per_m2.median` (already extracted)
  2. Compute land_value = plot_area × land_per_m2
  3. building_implied = valuation.amount − land_value
  4. Classify by building % of total:
     - `< 0`        → `land_exceeds_value` (red flag, unusual)
     - `< 5%`       → `land_dominant` (10-Year Rule confirmed)
     - `< 15%`      → `building_modest` (old/depreciated)
     - `< 35%`      → `normal` (typical good-condition building)
     - `≥ 35%`      → `building_dominant` (new/luxury/big BUA)
- Confidence labels by land_n: ≥20 = reliable, ≥10 = indicative, ≥3 = thin
- Returns None when land_n < 3 (refuses to mislead)

Called in `evaluate_thammen` after substantiality but before brief
sync. Result written to `output.valuation.value_decomposition`.

### Output schema additions

```json
"valuation": {
  ...
  "value_decomposition": {
    "land": {
      "per_m2_qar": 3875,
      "n_transactions": 11,
      "window_months": 24,
      "confidence": "indicative",
      "confidence_ar": "إرشادي",
      "estimated_qar": 1809625,
      "plot_area_m2": 467,
      "source_ar": "وسيط معاملات بيع الأراضي في نفس المنطقة..."
    },
    "building_implied": {
      "qar": 90375,
      "qar_per_m2_bua": 190,
      "bua_m2": 475,
      "as_pct_of_total": 4.8,
      "interpretation_ar": "البناء يساهم بنسبة ضئيلة...",
      "status": "land_dominant"
    },
    "methodology_note_ar": "يفصل ثمّن قيمة الأرض..."
  }
}
```

### Frontend (`index.html`)

New "💎 تفكيك القيمة (أرض + بناء)" card with:

1. **Visual bar:** proportional split land/building widths with bronze
   (أرض) and green (بناء) gradients
2. **Two-column grid:**
   - 🏞️ قيمة الأرض: total QAR + per-m² + plot area + n + confidence
   - 🏠 قيمة البناء: total QAR + per-m²-BUA + % of total
3. **Color-coded interpretation banner:**
   - Orange (land_dominant): 10-Year Rule confirmed
   - Yellow (building_modest): old building
   - Green (normal): typical
   - Blue (building_dominant): new/luxury
   - Red (land_exceeds_value): warning

The card appears BEFORE the substantiality card so users see the
fundamental land/building breakdown before the adjustment details.

---

## Verification — concrete numbers (local tested)

### Luqta 52/903/90 (467 m² plot, 30yo NOT luxury)
```
valuation.amount: 1,900,000
🏞️ LAND:     1,809,625 (3,875/m² × 467 m²)  n=11, إرشادي
🏠 BUILDING:    90,375  (4.8% of total)  status=land_dominant
   → "البناء يساهم بنسبة ضئيلة جداً (4.8%) — يتسق مع قاعدة الـ 10 سنوات..."
```

### Luqta 52/903/90 (same plot, 5yo NEW luxury, with basement)
```
valuation.amount: 2,300,000
🏞️ LAND:     1,809,625 (3,875/m² × 467 m²)  n=11, إرشادي
🏠 BUILDING:   490,375  (21.3% of total)  status=normal
   → "البناء يساهم بنسبة 21.3% — مساهمة طبيعية لبناء بحالة جيدة..."
```

### Bou Hamour 56/565/21 (900 m² plot, 30yo NOT luxury, big BUA)
```
valuation.amount: 4,000,000
🏞️ LAND:     3,400,200 (3,778/m² × 900 m²)  n=33, موثوق
🏠 BUILDING:   599,800  (15.0% of total)  status=building_modest
   → "البناء يساهم بنسبة محدودة (15.0%) — يتسق مع بناء قديم..."
```

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak8 && copy /Y evaluate_property.py evaluate_property.py.bak8 && copy /Y index.html index.html.bak8
tar -xf "%USERPROFILE%\Downloads\sprint2p6-land-building-split.zip"
findstr /C:"sprint2p6-land-building-split" evaluate_unified.py
git add evaluate_unified.py evaluate_property.py index.html CHANGELOG_v12.md
git commit -m "Sprint 2.6: Land vs Building value decomposition (Phase 1)"
git push heroku master
```

## Verification curl

```bash
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":52,"street":903,"building":90,"audience":"buyer",
       "floors":2,"condition":"renovated","building_age_years":30,
       "is_luxury":false,"asking_price":2000000}'
```

Expected in response:
- `valuation.value_decomposition.land.estimated_qar` ≈ 1,809,625
- `valuation.value_decomposition.building_implied.qar` ≈ 90,375
- `valuation.value_decomposition.building_implied.as_pct_of_total` ≈ 4.8
- `valuation.value_decomposition.building_implied.status` = "land_dominant"

## What's NOT in this patch (intentional Sprint 2.6 scope)

- Audience-specific brief sections mentioning the decomposition
  (could be added — Sprint 2.6b if requested)
- Per-municipality calibrated land medians (current uses area-level)
- Time-series tracking of land vs building separately
- Calibrated depreciation curve from MoJ data (Phase 5 — Sprint 2.8)
