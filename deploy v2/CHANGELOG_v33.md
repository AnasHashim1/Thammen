# CHANGELOG — Sprint 2.16.11: Tower Sanity Carve-out (BUA-aware)

**Engine version:** `thammen-sprint2p16p11-tower-sanity-carveout`
**SPRINT_TAG:** `2.16.11` → /api/health reports `3.1.0-sprint2.16.11`
**Date:** 2026-05-18
**Files updated:** `evaluate_unified.py` only
**Severity:** 🟡 Polish — removes a false-positive warning visible to users
on every successful tower valuation.

---

## Why this matters

After Sprint 2.16.10 deployed and the user typed in his actual Lusail
B201 numbers (`rental_income = 1,000,000` total monthly), the PDF
showed a yellow warning card that read:

> "⚠️ الإيجار يعادل ~3552 ر.ق/م² سنوياً للأرض (3,378 م²) — مرتفع جداً
> لأصل بهذا الحجم. تحقق من الرقم."

The valuation itself was correct (154M ر.ق) but the warning suggested
the user's rental input was suspicious. **The warning was wrong**, not
the data.

### Why the warning fires

`_check_input_sanity()` (evaluate_unified.py:1974) divides annual rent
by `plot_area_m2` to estimate rent-per-square-metre. For compounds —
the asset class the check was designed for — this is a reasonable
proxy because compounds spread horizontally (1-2 floors, BUA ≈ plot).
Typical band: **60–800 ر.ق/م²/year** of plot.

For Lusail B201:

```
annual rent   = 1,000,000 × 12 = 12,000,000 ر.ق
plot_area     = 3,378 m²
rent / plot   = 12,000,000 / 3,378 = 3,552 ر.ق/m²/year   ← warning fires
```

But the tower is **20 floors**. Its built-up area is ~67,000 m² (20 ×
3378 × 0.99 coverage), not 3,378. Rent-per-BUA is **~178 ر.ق/m²/year**
— smack in the middle of the normal band. The plot-area math is the
wrong denominator for any high-rise.

### Why it didn't fire on yesterday's bug

Yesterday's `rental_income = 30,000` gave `30K × 12 / 3,378 = 107
QAR/m²` — comfortably inside the 60-800 band. The bug producing 4.62M
slipped through this check entirely. **The check is calibrated for
low-rise; it neither catches the under-input mistake on towers nor
benignly stays silent.**

---

## What this patch does

### Single change: drop `'tower'` from the rent/m² check's asset-type tuple

```diff
- if (asset_type in ('compound_large', 'compound_small', 'tower', 'apartment_building')
+ if (asset_type in ('compound_large', 'compound_small', 'apartment_building')
        and rental_income and plot_area and plot_area > 0):
      rent_per_m2 = (rental_income * 12) / plot_area
      ...
```

Plus a comment block above the conditional explaining the carve-out
(BUA-aware reasoning, the Lusail B201 example, and why a future Sprint
with reliable floor count + footprint could re-enable a tower-specific
band).

### Asset classes still covered

- `compound_large`, `compound_small` — typically 1-2 floor villa
  compounds, plot is a fair proxy for BUA
- `apartment_building` — typically 2-4 floors, plot ≈ BUA / 3 still
  keeps the rent/m² inside the calibrated band

### Asset class explicitly skipped

- `tower` — high-rise (10+ floors), BUA can be 20× the plot. The
  rent/plot ratio carries no signal without BUA. Skipped until the
  engine has a reliable BUA estimate (Sprint 2.18+ direction:
  floors × footprint × coverage_ratio).

### Version bump

```diff
-ENGINE_VERSION = 'thammen-sprint2p16p10-tower-rental-split'
-SPRINT_TAG = '2.16.10'
+ENGINE_VERSION = 'thammen-sprint2p16p11-tower-sanity-carveout'
+SPRINT_TAG = '2.16.11'
```

---

## Empirical verification (pre-deploy, this container)

### Carve-out tests (7/7 passed)

```
✓ tower @ 1M/mo, plot 3378 m²: no false high-rent warning (the bug)
✓ tower @ 960K/mo (80×12K): no false warning (Sprint 2.16.10 case)
✓ tower @ 5K/mo: no rent/m² warning either way (skipped entirely)
✓ compound_large @ 1200 QAR/m²: still warns (regression preserved)
✓ compound_small @ 45 QAR/m²: still catches single-unit mistake
✓ apartment_building @ 1000 QAR/m²: still warns
✓ standalone_villa: never affected by rent/m² check
```

### Source verification (5/5 passed)

```
✓ source: tuple lists exactly compound_large/compound_small/apartment_building
✓ source: 'tower' is NOT in the asset-type tuple
✓ source: Sprint 2.16.11 carve-out comment present
✓ source: SPRINT_TAG bumped to 2.16.11
✓ source: ENGINE_VERSION bumped
```

### Regression suite (46/46 passed)

```
test_stock_strata.py / test_scope_of_service.py / test_material_uncertainty.py
46 passed in 0.09s
```

### Lesson 1 — `node --check` on inline JS

```
✓ inline JS valid
```

No JS changes in this Sprint, but the check runs every deploy per
Sprint 2.16.1 lesson.

### Lesson 2 — mobile viewport

Not applicable. No CSS or form-shape change.

---

## Backward compatibility

- **Compounds + apartment buildings:** unchanged. Every test that used
  to warn still warns; every test that didn't, still doesn't.
- **Towers:** the false-positive warning is gone. The valuation, MUC
  clause, brief sections, and PDF rendering are otherwise byte-for-byte
  identical to Sprint 2.16.10 output. No new fields, no removed fields.
- **API consumers:** `sanity_warnings` field on tower responses may now
  be `[]` where it previously had one entry. Existing consumers that
  iterate the list handle this correctly; consumers asserting a non-
  empty list (none exist) would break, but no such consumer is known.

---

## What this patch does NOT do

- **No BUA estimation.** A proper rent/BUA sanity check would need
  floors + footprint, which are optional inputs the user often skips.
  Building this requires a design discussion (default assumptions?
  visible to the user?). Deferred.
- **No tower-specific sanity check.** Towers now have zero rent/m²
  validation. The accuracy depends entirely on the user typing realistic
  numbers into unit_count + avg_monthly_rent_per_unit (Sprint 2.16.10
  bounds: 1-500 units, 1-500K per unit).
- **No re-calibration of the 60-800 band.** Whether 80-400 should be
  the "normal" sub-band stays as-is. Confirmed sales data Thursday will
  help calibrate this.
- **No removal of `_check_output_sanity`.** That function checks net
  yield against asset-class norms (e.g. tower normal yield 5-10%).
  For towers, net yield is mathematically equal to cap_rate (6%), so
  the check always passes. Harmless, no false positives, left alone.
- **No fix for `accuracy.score = 55`** ("⚠️ تقدير بطريقة واحدة").
  That's a correct flag — towers truly use only one method (income
  approach). Not a bug, accurate disclosure.

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p10
tar -xf "%USERPROFILE%\Downloads\sprint2p16p11-tower-sanity-carveout.zip"
findstr /C:"sprint2p16p11" evaluate_unified.py
findstr /C:"Sprint 2.16.11" evaluate_unified.py
git add evaluate_unified.py CHANGELOG_v33.md test_sprint_2p16p11_tower_sanity.py
git commit -m "Sprint 2.16.11: tower sanity carve-out (BUA-aware, no false positives)"
git push heroku master
```

## Post-deploy verification

1. **Health check:**
   ```
   curl https://thammen.qa/api/health
   ```
   Expected: `"version": "3.1.0-sprint2.16.11"`

2. **The actual fix — Lusail B201 with the same input that warned yesterday:**
   ```
   curl -X POST https://thammen.qa/api/evaluate/details ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201,\"rental_income\":1000000}"
   ```
   Expected:
   - `valuation.amount` = 154,000,000 ر.ق (same as Sprint 2.16.10)
   - `sanity_warnings` = **`[]`** (was `[".. 3552 ر.ق/م² .. مرتفع جداً .."]`)

3. **Compound regression — must still warn:**
   ```
   curl -X POST https://thammen.qa/api/evaluate/details ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":51,\"street\":835,\"building\":17,\"rental_income\":5000000}"
   ```
   (Al-Gharafa compound 67,536 m²; 5M/month → 888 QAR/m², above ceiling)
   Expected: `sanity_warnings` includes the high-rent warning. If it
   doesn't, the carve-out was too broad — revert.

4. **Browser end-to-end:**
   - Open https://thammen.qa, search 69/305/201
   - Click the tower CTA, enter unit_count=80, avg=12000
   - Submit → PDF should have **no "تنبيهات مهمة قبل قراءة النتيجة"
     section** (was present in yesterday's PDF after Sprint 2.16.10)
   - MUC clause + valuation card + yield + sensitivity all unchanged

---

## Files in this patch

```
sprint2p16p11-tower-sanity-carveout.zip
├── evaluate_unified.py                      (MODIFIED: 8-line diff in
│                                              _check_input_sanity + version bump)
├── test_sprint_2p16p11_tower_sanity.py      (NEW: 12-check isolated test)
└── CHANGELOG_v33.md                         (NEW: this file)
```

---

## Catalogue note

This Sprint closes the issue logged at the end of Sprint 2.16.10:

| Issue | Status |
|---|---|
| Sanity warning false-positive on towers (rent/plot vs rent/BUA) | ✓ **closed (this Sprint)** |

Future related work (deferred):

- 🟡 **BUA-aware sanity** — Sprint 2.18+ candidate. When floors and
  footprint are both provided, estimate BUA = floors × footprint × 0.85
  and compare rent against rent/BUA bounds (typical: 100-400 QAR/BUA
  m²/year for residential towers).
- 🟡 **Visual building assessment** — Sprint 2.22+ candidate. Google
  Street View + Claude Vision to confirm classification, count floors,
  flag mismatches between user-entered unit_count and observed scale.

---

_Last updated: 2026-05-18 (Monday, 6th deploy today) — Tower flow now
clean of all known issues. Sprint 2.16 series complete pending Thursday's
confirmed sales data._
