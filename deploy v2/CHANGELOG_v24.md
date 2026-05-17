# CHANGELOG — Sprint 2.16.2: Stratum-Aware Negotiation + Mobile Placeholder Fix

**Engine version:** `thammen-sprint2p16p2-stratum-aware-negotiation`
**SPRINT_TAG:** `2.16.2` → /api/health reports `3.1.0-sprint2.16.2`
**Date:** 2026-05-17
**Files updated:** `evaluate_unified.py`, `index.html`
**Builds on:** Sprint 2.16.1 (hotfix) + 2.16.0 (Stock Stratification exposure)

---

## Why this matters — two issues, one Sprint

### Issue 1: Internal contradiction in the same report

The Sprint 2.16.0 PDF report (verified 2026-05-17 in production with asking
price 5,000,000 QAR for property 51/955/49) contained two mutually
contradictory messages about the same property:

| Section | Reference | Verdict on asking 5M |
|---|---|---|
| Page 1 — "تنبيهات مهمة" | Blended median 3,270,500 | "أعلى بـ 61% — السوق يرفض" |
| Page 3 — "نطاق التفاوض" | Anchor 3,100,000 | floor 2.9M, ceiling 3.4M |
| Page 7 — "Stock Strata" | luxury_new 4,687,500 | "+6.7% — متّسق مع الفئة" |

The strata card identified the property as `luxury_new` (ratio 2.48), and
the luxury_new stratum median was 4.69M — making the asking 5M only +6.7%
premium (well within RICS buyer ceiling of +10%). But the top of the report
told the user the price was "rejected by the market".

The user reading top-to-bottom would conclude "too expensive" and stop. Only
a careful reader making it to page 7 would discover that the stratification
contradicts the headline warning.

This was a Sprint 2.16.0 known limitation (called out in its CHANGELOG §"What
is NOT in this patch"). It's now resolved.

### Issue 2: Mobile placeholder truncation

User report (2026-05-17, iPhone, viewport ~390px): "I see thammen completely
on desktop but truncated on mobile." Verified by inspecting the live HTML:

```html
<input id="footprintM2" placeholder="اختياري — تقدير الـ footprint">
<input id="buildingAge" placeholder="اختياري — يكفي تقدير ±5 سنوات (مهم للعقارات القديمة)">
```

The CSS `input { direction:ltr; text-align:right }` (line 44) combined with
mixed Arabic+Latin placeholder text causes the placeholder to overflow and
truncate mid-word on narrow viewports. The 47-character `buildingAge`
placeholder was displaying as fragmentary "ي — يكفي تقدير ±5 سنوات (مهم..."
with the meaningful start cut off.

Not caused by Sprint 2.16.0/2.16.1 — pre-existing UX issue.

---

## What this patch does

### Change 1: Stratum-aware sanity warning (`evaluate_unified.py:_check_output_sanity`)

When all of:
- The subject property was classified into a stock stratum (via `stock_strata`)
- The stratum is one of `land_priced` / `aging_stock` / `modern_stock` / `luxury_new`
- The stratum is reliable (n ≥ 10)

→ Use `stratum.estimated_total` as the listing-vs-benchmark reference instead
of the blended `valuation.amount`. The warning text now reads:

> السعر المطلوب (5,000,000) أعلى بـ 7% من **وسيط فئة "فاخر / حديث البناء"** —
> السوق غالباً يرفض السعر بهذا المستوى.

(Or, in the 5M vs luxury_new=4.69M case, the warning is *suppressed entirely*
because the 6.7% gap is below the overpriced threshold.)

**Fallback semantics.** If the stratum is unreliable (n<10) OR no subject
classification exists OR `asking_price` was not provided, the original
blended-median behavior is preserved. No silent regression on unclassified
properties.

### Change 2: Stratum-aware negotiation override (`evaluate_unified.py:_rewrite_brief_anchored_sections`)

Same gate as Change 1. When the stratum is classified and reliable, the
buyer's negotiation range is computed from `stratum.estimated_total`
instead of `final_amount`:

```
floor          = anchor × 0.95
opening_offer  = anchor × 0.90
ceiling        = anchor × 1.10
```

For the test case (Al-Gharafa luxury_new, anchor=4,687,500):

| | Pre-2.16.2 (blended) | Post-2.16.2 (stratum-aware) |
|---|---|---|
| opening_offer | 2,800,000 | **4,200,000** |
| floor | 2,900,000 | **4,500,000** |
| ceiling | 3,400,000 | **5,200,000** |

The new range is realistic for a luxury_new villa in Al-Gharafa. A buyer
following the OLD ceiling (3.4M) would never close on this property at the
asking 5M; a buyer following the NEW ceiling (5.2M) has a viable range.

New fields added to the negotiation content:
- `anchor_used` — the reference value used (for transparency)
- `is_stratum_aware` — bool, controls UI badge
- `stratum_note_ar` — explanation when stratum-aware

### Change 3: Negotiation UI badge + note (`index.html`)

When `c.is_stratum_aware === true`, render a green badge above the negotiation
table:

> 📊 نطاق مُحدَّث حسب فئة عقارك

And below the table, the stratum_note_ar in italic explains why the range
is different from the headline.

When `is_stratum_aware === false` (or absent), no badge appears — preserves
pre-2.16.2 visuals for unclassified properties.

### Change 4: Mobile placeholder fix (`index.html`)

Two specific placeholders shortened:

| Field | Before (47 chars) | After (18 chars) |
|---|---|---|
| `footprintM2` | "اختياري — تقدير الـ footprint" | "اختياري" |
| `buildingAge` | "اختياري — يكفي تقدير ±5 سنوات (مهم للعقارات القديمة)" | "اختياري — مثال: 12" |

The detailed guidance ("يكفي تقدير ±5 سنوات, مهم للعقارات القديمة") was
already covered by the input label and surrounding context.

### Change 5: Mobile placeholder defensive CSS

Added a 480px media query that shrinks placeholder font + reduces input
padding, so any FUTURE long placeholder won't break mobile layout silently:

```css
@media(max-width:480px){
  input::placeholder{font-size:.85rem}
  input,select{padding:11px 10px}
}
```

---

## Verification — pre-deploy

### Python compile

```
$ python -c "import py_compile; py_compile.compile('evaluate_unified.py', doraise=True); ..."
✓ Python OK
```

### JS parse (the Sprint 2.16.1 lesson)

```
$ python -c "<extract scripts>" && node --check /tmp/c.js
✓ JS parses cleanly
```

This is now a mandatory step before every HTML/JS deploy.

### Unit tests

`test_stock_strata.py` (regression):
```
6/6 tests passed.
```

Sprint 2.16.2 new logic (5 tests, run inline):
- ✓ Stratum-aware warning when subject classified
- ✓ Fallback to blended when no classification
- ✓ Fallback when stratum unreliable (n<10)
- ✓ Stratum-aware negotiation anchor when classified
- ✓ Fallback negotiation anchor when no stock_strata

### Backtest expected behavior post-deploy

`backtest.py` canonical 6 should show:
- Same predictions for properties without `asking_price` (no stratum
  classification → fallback to blended) ✓ no regression
- Same predictions for non-villa types (Sprint 2.16.0 only applies to
  villas anyway) ✓ no regression

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p1
copy /Y index.html index.html.bak_2p16p1
tar -xf "%USERPROFILE%\Downloads\sprint2p16p2-stratum-aware.zip"
findstr /C:"sprint2p16p2" evaluate_unified.py
python test_stock_strata.py
git add evaluate_unified.py index.html CHANGELOG_v24.md
git commit -m "Sprint 2.16.2: stratum-aware negotiation + mobile placeholder fix"
git push heroku master
```

## Verification curl (post-deploy, ~60 seconds for dyno restart)

```
curl https://thammen.qa/api/health
```
Should report `"version": "3.1.0-sprint2.16.2"`.

```
curl -X POST https://thammen.qa/api/evaluate/details ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":51,\"street\":955,\"building\":49,\"audience\":\"buyer\",\"asking_price\":5000000}"
```

Expected change in response (key fields):
- `valuation.amount` = **3,100,000** (unchanged — Sprint 2.16.0 contract holds)
- `sanity_warnings` = **[]** (asking 5M is +6.7% over luxury_new median, below
  the warning threshold)
- `brief.sections[id=negotiation].content`:
  - `anchor_used` ≈ 4,700,000
  - `opening_offer` ≈ 4,200,000
  - `floor` ≈ 4,500,000
  - `ceiling` ≈ 5,200,000
  - `is_stratum_aware` = **true**
  - `stratum_note_ar` = "النطاق محسوب بناء على فئة 'فاخر / حديث البناء'..."

## Manual visual verification (the Sprint 2.16.1 lesson)

1. Open `https://thammen.qa/` on mobile and desktop
2. Verify the form placeholders are not truncated on mobile
3. Submit an evaluation for 51/955/49 with asking 5,000,000
4. In the report, verify:
   - "نطاق التفاوض" section shows green badge "📊 نطاق مُحدَّث حسب فئة عقارك"
   - Floor/ceiling are around 4.5M / 5.2M (NOT 2.9M / 3.4M)
   - The italic note explains why
5. Submit an evaluation WITHOUT asking_price for the same property
   - Verify no badge appears, ranges revert to blended (2.9M / 3.4M)

---

## What is NOT in this patch (scope boundary)

1. **Headline value adjustment** — `valuation.amount` STILL unchanged.
   The exposure-only contract from Sprint 2.16.0 still holds for the
   PRIMARY number. Only secondary computations (warnings, negotiation)
   are now stratum-aware.

2. **Subject classification UI input** — users still indicate their tier
   indirectly via `asking_price`. A future Sprint may add explicit stratum
   selection (age + finish → tier).

3. **Apartment stratification** — Sprint 2.29 territory.

4. **Confirmed sales DB** — still needs the secretary's data (Thursday-ish).

---

## Process improvements applied (Sprint 2.16.1 lessons)

This Sprint validated the new pre-deploy workflow:

1. ✓ Python `py_compile` on all .py files modified
2. ✓ Node `--check` on extracted inline JS
3. ✓ Regression: `test_stock_strata.py` still 6/6
4. ✓ Isolated logic tests for new code paths

The Sprint 2.16.1 regression (JS identifier collision) would have been
caught at step 2.

---

## Files in this patch

```
sprint2p16p2-stratum-aware.zip
├── evaluate_unified.py     (MODIFIED, +~70 lines, version bump + 2 logic blocks)
├── index.html              (MODIFIED, +~10 lines: badge, mobile CSS, placeholders)
└── CHANGELOG_v24.md         (NEW, this file)
```

---

_Last updated: 2026-05-17 — Sprint 2.16.2 resolves the Sprint 2.16.0 report contradiction + mobile UX issue._
