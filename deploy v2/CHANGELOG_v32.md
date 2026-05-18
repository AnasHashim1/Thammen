# CHANGELOG — Sprint 2.16.10: Tower Rental Split (Resolves Input Ambiguity)

**Engine version:** `thammen-sprint2p16p10-tower-rental-split`
**SPRINT_TAG:** `2.16.10` → /api/health reports `3.1.0-sprint2.16.10`
**Date:** 2026-05-18
**Files updated:** `api.py`, `evaluate_unified.py`, `index.html`
**Severity:** 🔴 Methodological correctness — fixes the input ambiguity that
produced today's 32× valuation error on Lusail B201.

---

## Why this matters — the bug

Earlier today the user printed a tower valuation PDF showing **4,620,000 ر.ق**
for Lusail B201 (a ~20-floor residential tower). The actual market value
is well over 100M ر.ق. The reverse-calculation of the engine output:

```
rental_income (user)  = 30,000 ر.ق
× 12                  = 360,000 annual
× (1 - 23% opex)      = 277,200 NOI
÷ 6% cap_rate         = 4,620,000 ر.ق ← printed valuation
```

The math was correct. **The input was the bug.** 30,000 ر.ق/month is what
one Lusail apartment rents for — not what the entire 80-unit tower
collectively generates. A user typing "30,000" into a field labelled
"الإيجار الشهري الحالي" could mean:

- The whole tower's monthly gross rent (engine's assumption)
- One apartment's monthly rent
- An average apartment's rent
- Their own apartment's rent

Four meanings, one field. The engine cannot disambiguate.

### Why didn't service_scope save us?

The response already included `service_scope.requires_user_input_ar:
"الإيجار السنوي الإجمالي للبرج"` — but this string appeared as a small
warning line in the UI, contradicted by the form's actual label
"الإيجار الشهري الحالي". The user obeyed the form, not the buried hint.

---

## What this patch does

### Change 1: Two new optional inputs

Both `EvaluateRequest` and `EvaluateDetailsRequest` get:

```python
unit_count: Optional[int] = Field(default=None, gt=0, le=500)
avg_monthly_rent_per_unit: Optional[float] = Field(default=None, gt=0, lt=500_000)
```

**Bounds rationale:**
- 500 unit ceiling covers Lusail's largest residential towers (typical is
  60-200 units; Pearl Marina towers cap around 300)
- 500K QAR/month per unit ceiling covers Pearl Qatar / Lusail Marina
  premium apartments (typical Lusail is 10-15K, Pearl premium is 25-35K)

Backward compat: both fields are `Optional`. Existing callers that don't
send them get identical behaviour. The legacy `rental_income` field is
unchanged.

### Change 2: Engine derivation (priority: pair wins)

In `evaluate_unified.py`, between input sanity (GATE 2) and the DCF fast
paths, a new block computes `_rent_source`:

```python
if unit_count and avg_monthly_rent_per_unit:
    _derived_total = unit_count * avg_monthly_rent_per_unit
    _rent_source = {
        'kind': 'derived_from_units',
        'unit_count': unit_count,
        'avg_per_unit': avg_monthly_rent_per_unit,
        'derived_monthly_total': _derived_total,
        'note_ar': f'محسوب من {unit_count} وحدة × {avg:,} = {total:,} ر.ق/شهر إجمالي',
    }
    rental_income = _derived_total
elif rental_income:
    _rent_source = {'kind': 'user_total', 'monthly_total': rental_income, ...}
```

**Priority rule:** if both `(unit_count, avg_monthly_rent_per_unit)` are
provided **and** a bare `rental_income`, the pair wins. The pair is
unambiguous; the bare field isn't. If only the pair is incomplete
(e.g. unit_count without avg), we fall back to `rental_income`.

### Change 3: Provenance attached to response

`_build_fast_income_only_response` now accepts a `rent_source_ar` keyword
(default keeps old behaviour) and uses it in the `yield.content.rent_source_ar`
field of the brief. The full response also carries a top-level `rent_source`
object with the structured provenance (kind, unit_count, avg_per_unit,
derived_monthly_total, note_ar) so any consumer (UI, PDF, downstream
analytics) can inspect *how* the rent figure was determined, not just
*what* it was.

### Change 4: Frontend — tower-only fields + dynamic label

`index.html` form now contains a collapsible "tower-only" block
(`<div id="towerRentSection">`) holding the two new fields. The
`applyAssetToForm(assetType)` helper toggles visibility:

- `asset_type === 'tower' || 'compound_large' || 'apartment_building'`
  → show the pair, **and** update the rental_income label from
  "الإيجار الشهري الحالي" to "إجمالي الإيجار الشهري للبرج (ر.ق)"
- Otherwise → hide the pair, restore the legacy label

The helper runs from `goForm()` (the CTA path coming back from a
result page) and reads `window._lastResult.asset_type`, so the form
adapts to whatever the user just evaluated.

### Change 5: Submit logic

The new fields are sent only when **both** are filled:

```js
if(uc && apu){
  bd.unit_count = +uc;
  bd.avg_monthly_rent_per_unit = +apu;
}
```

A single half-filled field is treated as "user didn't intend the pair"
and ignored — the form silently falls back to `rental_income` if that
was also filled.

### Change 6: Version bump

```diff
-ENGINE_VERSION = 'thammen-sprint2p16p9-muc-frontend-display'
-SPRINT_TAG = '2.16.9'
+ENGINE_VERSION = 'thammen-sprint2p16p10-tower-rental-split'
+SPRINT_TAG = '2.16.10'
```

---

## Empirical verification (pre-deploy, this container)

### Pydantic validator tests (16/16 passed)

```
unit_count validators:
  ✓ unit_count=0 -> 422
  ✓ unit_count=-5 -> 422
  ✓ unit_count=501 (over ceiling) -> 422
  ✓ unit_count=1 (minimum, positive)
  ✓ unit_count=80 (typical Lusail)
  ✓ unit_count=500 (ceiling)

avg_monthly_rent_per_unit validators:
  ✓ avg=0 -> 422
  ✓ avg=-100 -> 422
  ✓ avg=500K (at ceiling) -> 422
  ✓ avg=1 (positive)
  ✓ avg=12K (typical Lusail)
  ✓ avg=25K (Pearl premium)

Backward compat:
  ✓ no rental fields at all
  ✓ only rental_income (legacy)
  ✓ only the new pair
  ✓ all three together
```

### Derivation logic (5/5 passed) — the proof of fix

```
✓ yesterday's bug: 30K rental_income -> 4.62M (user_total path)
✓ the fix:       80 units × 12K -> 147.84M (derived path)
✓ pair wins over rental_income when both present
✓ incomplete pair (only unit_count) -> rental_income wins
✓ no inputs -> None (insufficient_data path triggered)

Reference (typical Lusail towers):
  60 units × 12K/month  -> 110,880,000 QAR
  100 units × 15K/month -> 231,000,000 QAR
  120 units × 18K/month -> 332,640,000 QAR
```

All three reference values match the "100M+" range the user reported as
realistic.

### Sync check

```
✓ api.py + evaluate_unified.py carry Sprint 2.16.10 code
```

Reads both files and asserts the constants, fields, derivation block,
and rent_source_ar parameter passing are all in place. If a future
Sprint un-wires any of them, this test fails.

### Regression suite (46/46 passed)

```
test_stock_strata.py ............................... PASS
test_scope_of_service.py ........................... PASS
test_material_uncertainty.py ....................... PASS
46 passed in 0.09s
```

### Lesson 1 — `node --check` on inline JS

```
Extracted 1 inline blocks (52550 chars)
✓ inline JS valid
```

The form-shape changes (new fields) and `applyAssetToForm` helper add
~25 lines of JS. Per Sprint 2.16.1 lesson, all inline JS is extracted
and node-checked before deploy.

### Lesson 2 — mobile viewport

The new `towerRentSection` uses the existing `.fr2` row container, which
is already responsive. Its `display: none` initial state means it
contributes zero height when irrelevant. When shown, the section
collapses to one column on mobile (default `.fr2` behaviour). No new
CSS rules were added.

---

## Backward compatibility

- **Villa users**: see no UI change. The `towerRentSection` stays hidden
  for `standalone_villa` / `raw_land` / `compound_small` / etc. The
  `rentalIncomeLabel` stays "الإيجار الشهري الحالي".
- **Old API callers** (existing scripts, Postman, etc.): unchanged. The
  new fields are `Optional`, default `None`, so any old request body
  still produces the same response shape it always did.
- **Existing tower flow** (user provides only `rental_income`): unchanged.
  The engine takes the value as before. The brief now carries
  `rent_source_ar = 'إفادة العميل: X ر.ق/شهر إجمالي'` instead of the
  generic `'إفادة العميل (الإيجار الفعلي)'`, but the math and value
  are identical.
- **New tower flow** (user provides the pair): the pair takes precedence,
  the derived monthly total flows into the same income approach, and
  the brief shows the calculation provenance.

---

## What this patch does NOT do

- **No change to Cap Rate** (still 6.0% for towers). The cap rate is the
  next thing to calibrate once we have confirmed-sales data on Thursday.
- **No new asset type**. Towers still classify the same way (Sprint 2.16.6
  subtype-aware).
- **No floor count or visual building assessment**. The user's earlier
  question about pulling Street View imagery + auto-counting floors is
  deferred to a hypothetical Sprint 2.22+. This Sprint solves the input
  ambiguity directly, which is the actual cause of today's error.
- **No removal of `rental_income`**. The legacy field stays as a fallback
  for users who genuinely know the aggregate (some building owners do).
- **No retroactive recalculation of past valuations**. Previous PDFs the
  user generated showing 4.62M are unchanged.
- **No client-side validation of "unit_count > 0 AND avg > 0"**. The form
  submits the pair only when both are filled; otherwise it silently
  ignores them. We rely on Pydantic 422 errors for invalid values.

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y api.py api.py.bak_2p16p9
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p9
copy /Y index.html index.html.bak_2p16p9
tar -xf "%USERPROFILE%\Downloads\sprint2p16p10-tower-rental-split.zip"
findstr /C:"sprint2p16p10" evaluate_unified.py
findstr /C:"unit_count" api.py
findstr /C:"towerRentSection" index.html
git add api.py evaluate_unified.py index.html CHANGELOG_v32.md test_sprint_2p16p10_tower_split.py
git commit -m "Sprint 2.16.10: tower rental split (resolves input ambiguity bug)"
git push heroku master
```

## Post-deploy verification

1. **Health check:**
   ```
   curl https://thammen.qa/api/health
   ```
   Expected: `"version": "3.1.0-sprint2.16.10"`

2. **The actual fix — Lusail B201 with the pair:**
   ```
   curl -X POST https://thammen.qa/api/evaluate/details ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201,\"unit_count\":80,\"avg_monthly_rent_per_unit\":12000}"
   ```
   Expected:
   - `valuation.amount` ≈ 147,840,000 ر.ق (was 4,620,000 yesterday)
   - `rent_source.kind` = "derived_from_units"
   - `rent_source.note_ar` = "محسوب من 80 وحدة × 12,000 ر.ق/شهر = 960,000 ر.ق/شهر إجمالي"
   - `income_approach.monthly_rent` = 960000

3. **Backward compat — old request still works:**
   ```
   curl -X POST https://thammen.qa/api/evaluate/details ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201,\"rental_income\":30000}"
   ```
   Expected:
   - `valuation.amount` = 4,620,000 ر.ق (same as yesterday — legacy path)
   - `rent_source.kind` = "user_total"
   - This proves we didn't break old callers; the new fix is opt-in.

4. **Pydantic — invalid unit_count is rejected:**
   ```
   curl -X POST https://thammen.qa/api/evaluate ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201,\"unit_count\":0,\"avg_monthly_rent_per_unit\":12000}"
   ```
   Expected: HTTP 422 with body containing `"greater_than"`.

5. **Browser end-to-end (the actual UX test):**
   - Open https://thammen.qa, search 69/305/201
   - On the tower result, click the CTA "→ أدخل: الإيجار السنوي الإجمالي للبرج"
   - **The form should now show two extra fields** under the rental
     income line, in a bronze-bordered box, with the title "للأبراج
     والمجمعات الكبيرة" and inputs for unit count + per-unit rent
   - **The rental_income label should now read** "إجمالي الإيجار الشهري للبرج"
   - Fill unit_count = 80, avg = 12000 (leave rental_income empty)
   - Submit → result should be ~148M ر.ق (not 4.62M)
   - The yield section should show `rent_source_ar:
     "محسوب من 80 وحدة × 12,000 ر.ق/شهر = 960,000 ر.ق/شهر إجمالي"`

6. **Villa regression — towerRentSection stays hidden:**
   - Search 56/565/10 (J Seven villa)
   - Open the form: the new section should NOT appear
   - The rental label should be "الإيجار الشهري الحالي" (legacy)

---

## Files in this patch

```
sprint2p16p10-tower-rental-split.zip
├── api.py                                  (MODIFIED: +13 lines)
├── evaluate_unified.py                     (MODIFIED: +35 lines)
├── index.html                              (MODIFIED: +40 lines)
├── test_sprint_2p16p10_tower_split.py      (NEW: 21 isolated checks)
└── CHANGELOG_v32.md                        (NEW: this file)
```

---

## Bug catalogue update

| ID | Severity | Status |
|---|---|---|
| **Tower input ambiguity** | 🔴 | ✓ **closed (this Sprint, was the today bug)** |
| A2 | 🟡 | open (Pydantic extra=ignore) |
| A5 | 🟡 | open (asset_type: unknown UX) |
| A6 | 🟠 | open — Sprint 2.18 latency |
| A7 | 🟡 | open (rics_compliant tier) |
| A8 | 🟠 | open — Sprint 2.20 comparables |
| B1 | 🟠 | open — Sprint 2.18 housekeeping |
| B3 | 🟡 | open (audience='hacker') |

8 bugs / discovered-issues closed in 3 days. The tower flow is now
end-to-end correct: classification (2.16.6) → CTA (2.16.8) → income
approach (already worked) → MUC clause in API (2.16.8) → MUC on screen
(2.16.9) → **unambiguous rental input (this Sprint)** → realistic
valuation.

---

_Last updated: 2026-05-18 (Monday, 5th deploy today) — Tower flow complete
end-to-end. Next: rest, or Sprint 2.17 QARS snapshot, or wait Thursday
for secretary's confirmed sales._
