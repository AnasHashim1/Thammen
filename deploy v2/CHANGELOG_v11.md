# CHANGELOG — Sprint 2.5b: Honest Placeholder (Cleanup)

**Engine version:** `thammen-sprint2p5b-honest-placeholder`
**Date:** 2026-05-13
**Files changed:** `evaluate_unified.py` (version bump only), `index.html` (placeholder text)
**Builds on:** Sprint 2.5

---

## Why

Sprint 2.5 added an auto-detect age feature that turned out NOT to fire
in production because `evaluate_property.py` hard-codes `include_imagery=False`
when calling Qatar GIS (imagery analysis takes 30-60s and would exceed
Heroku's 30s timeout).

The form placeholder for the age field promised:

> "اختياري — سيُكتشف تلقائياً من صور الأقمار إن تُرك فارغاً"

This was a misleading promise — the detection never actually runs.

## What this patch does

Single change in `index.html`:

```html
<!-- Before -->
placeholder="اختياري — سيُكتشف تلقائياً من صور الأقمار إن تُرك فارغاً"

<!-- After -->
placeholder="اختياري — يكفي تقدير ±5 سنوات (مهم للعقارات القديمة)"
```

The new text is honest and informative — it tells the user that age
is important for old buildings (since it activates the Qatar 10-Year
Rule and the proper cost-approach depreciation).

## What is NOT changed (intentional)

The infrastructure from Sprint 2.5 is preserved:
- `user_inputs.age_source` field still emitted (correctly shows `'user'` or `'unknown'`)
- `valuation.building_substantiality.age_source` and `age_confidence_years` fields preserved
- The conditional badge in UI (`📡 مكتشف من صور الأقمار`) preserved — it will simply never fire under current settings
- The conditional methodology note preserved — also never fires

This means: when we eventually solve the imagery-speed problem (async
processing, caching, or selective on-demand activation), the
infrastructure is ready to surface the auto-detected age without
needing further frontend changes.

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak7 && copy /Y index.html index.html.bak7
tar -xf "%USERPROFILE%\Downloads\sprint2p5b-honest-placeholder.zip"
findstr /C:"sprint2p5b-honest-placeholder" evaluate_unified.py
git add evaluate_unified.py index.html CHANGELOG_v11.md
git commit -m "Sprint 2.5b: remove misleading auto-detect placeholder text"
git push heroku master
```

## What this restores

User trust. The product no longer promises a feature that doesn't fire.
The age field now reads as a useful guidance rather than a broken
promise. All real Sprint 2.5 work is preserved as infrastructure for
future imagery integration.
