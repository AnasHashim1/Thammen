# CHANGELOG — Sprint 2.4d + 2.5: PDF Print + Auto-Age Detection

**Engine version:** `thammen-sprint2p5-auto-age`
**Date:** 2026-05-13
**Files changed:** `evaluate_unified.py`, `index.html`
**Builds on:** Sprint 2.4c

---

## Sprint 2.4d — PDF / Print Support (frontend only)

### Why
The UI had placeholder text mentioning "تقرير PDF كامل" but no actual
PDF export existed. This patch closes that promise using the browser's
native Save-as-PDF (via window.print() + print-optimized CSS).

### What
1. **New button:** "🖨️ طباعة / حفظ PDF" next to "📋 نسخ النتيجة"
2. **`printReport()` function:** adds `printing` class to body, fires
   `window.print()`, removes class after dialog closes
3. **`@media print` styles** in CSS:
   - Hides: form, audience selector, copy/print buttons, hero, logo,
     loading/error elements, map buttons, sanity warnings
   - Cleans: white background, dark text, no shadows, no colored chips
   - Optimizes: page-break-inside avoid for cards, page-break-after
     avoid for headings, compressed reasoning trace font

### User experience
1. User clicks "🖨️ طباعة / حفظ PDF"
2. Browser print dialog appears
3. User chooses "Save as PDF" (or any PDF printer)
4. Clean report is saved — no UI clutter, no input form, no buttons

Works on: Chrome, Edge, Safari, Firefox, mobile browsers — all
support native Save-as-PDF without dependencies.

---

## Sprint 2.5 — Auto-Detect Building Age from GIS Imagery

### Why
The system was ALREADY detecting building age from historical satellite
imagery (in `evaluate_property.py` via `report.construction.earliest_built_year`).
That detected age was being used internally for the cost approach
depreciation, but it was NOT:

1. Surfaced to the user
2. Passed to Sprint 2.3's age-aware substantiality multiplier
3. Used to auto-trigger the Qatar 10-Year Rule

Result: users who didn't know their building's age missed the automatic
correction even though the system had a perfectly good estimate.

### What

**In `evaluate_thammen()` after `evaluate_property()` returns:**

```python
age_source = 'user' if building_age_years is not None else 'unknown'
age_confidence_years = None
if building_age_years is None:
    rc = getattr(ev, 'replacement_cost', None)
    if rc:
        auto_age = getattr(rc, 'building_age_years', None)
        if auto_age and auto_age > 0:
            building_age_years = int(auto_age)
            age_source = 'gis_imagery'
            # Extract confidence from construction report
            ...age_confidence_years = constr.confidence_years
```

The auto-detected age is now:
- Used as the input to the Sprint 2.3 age multiplier (Qatar 10-Year Rule)
- Echoed in `user_inputs.building_age_years` and `user_inputs.age_source`
- Reflected in `building_substantiality.age_source` and `.age_confidence_years`
- Mentioned in `methodology_note_ar` with the source explanation

### Output schema additions

`valuation.building_substantiality`:
- `age_source`: `'user' | 'gis_imagery' | 'unknown'`
- `age_confidence_years`: ± years confidence from satellite imagery (when applicable)

`user_inputs`:
- `age_source`: same enum

### UI changes

1. **Form placeholder updated:**
   `"اختياري — سيُكتشف تلقائياً من صور الأقمار إن تُرك فارغاً"`

2. **Auto-detection badge in substantiality card:**
   `📡 مكتشف من صور الأقمار الصناعية (±N سنة)`
   shown next to the age when source = 'gis_imagery'

3. **Methodology note appends GIS source explanation:**
   `📡 ملاحظة: عمر البناء (30 سنة) تم استخراجه تلقائياً من تحليل صور الأقمار...`

### Concrete impact

**Before Sprint 2.5 (Luqta property, user leaves age field empty):**
- substantiality.age_regime: `unknown_age` (default treatment)
- adjustment_pct: based on full Sprint 2.2 (could over-value old building)
- User unaware system knew the age

**After Sprint 2.5 (same scenario):**
- substantiality.age_regime: `qatar_10_year_rule` (auto-triggered)
- adjustment_pct: 0% (correct for old non-luxury)
- UI shows: "📡 مكتشف من صور الأقمار" badge
- User sees explanation in methodology note

---

## Verification curl after deploy

**Test 1 — User omits age, system should auto-detect:**
```bash
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":52,"street":903,"building":90,"audience":"buyer",
       "floors":2,"condition":"renovated","is_luxury":false}'
```

Expected:
- `user_inputs.age_source: "gis_imagery"`
- `user_inputs.building_age_years: ~30` (from imagery)
- `valuation.building_substantiality.age_source: "gis_imagery"`
- `valuation.building_substantiality.age_regime: "qatar_10_year_rule"`
- `methodology_note_ar` includes "📡 ملاحظة: عمر البناء"

**Test 2 — User provides age, should be respected:**
```bash
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":52,"street":903,"building":90,"audience":"buyer",
       "floors":2,"condition":"renovated","building_age_years":15,"is_luxury":false}'
```

Expected:
- `user_inputs.age_source: "user"`
- `user_inputs.building_age_years: 15`
- `valuation.building_substantiality.age_regime: "qatar_10_year_rule"` (still — 15 > 10)
- No GIS auto-detection note in methodology

---

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak6 && copy /Y index.html index.html.bak6
tar -xf "%USERPROFILE%\Downloads\sprint2p5-auto-age.zip"
findstr /C:"sprint2p5-auto-age" evaluate_unified.py
git add evaluate_unified.py index.html CHANGELOG_v10.md
git commit -m "Sprint 2.4d+2.5: PDF print support + GIS auto-age detection"
git push heroku master
```

## Visual test in browser

1. Open https://thammen.qa
2. Enter: 52 / 903 / 90 with floors=2, condition=مُرمّم
3. **Leave عمر البناء field empty**
4. Click ثمّن
5. Expected: substantiality card shows age 30 + 📡 badge
6. Click 🖨️ طباعة / حفظ PDF → choose "Save as PDF" → clean report saved

---

## What's NOT in this patch (deliberate)

- Backend-generated PDF (would need weasyprint/reportlab dependency).
  window.print() approach gives users full control over PDF output
  via their browser's built-in PDF printer.
- Echoing auto-detected age into the form input field. The age field
  stays empty when user didn't provide one; the auto-detected age is
  surfaced in the substantiality card and methodology note instead.
  Rationale: avoid the impression that the system "filled in" data
  the user didn't enter.
