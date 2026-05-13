# CHANGELOG — Sprint 2.4c: UI Alignment with Backend Changes

**Engine version unchanged:** `thammen-sprint2p4b-audience-fixes` (backend not touched)
**Date:** 2026-05-13
**Files changed:** `index.html` only
**Builds on:** Sprint 2.4a + 2.4b

---

## Why this exists

Sprint 2.4b fixed methodology and audience routing on the backend. The
new and changed response fields needed corresponding UI updates so the
user actually SEES the new content. Without this patch:

- Trend slope would render as **-207%** instead of -2.07% (double *100)
- New investor sections `yield_estimated` and `investment_scenarios`
  would fall through to a generic key-value dump (ugly)
- `tips` and `due_diligence` lists would render the "متاحة في PDF" placeholder
  instead of the actual list items

This is purely a frontend patch — no backend changes.

---

## Bugs this patch closes

### Bug #UI-1 — Trend slope double-multiplication
The renderer at line 735 did `pctFmt(c.slope_annual_pct*100)`. When
backend (Sprint 2.4b) started sending the value already in percent form
(`-2.07`), the frontend multiplied again → displayed `-207.00%`.

**Fix:** Tolerant conversion — only multiply by 100 when the value
is clearly still in decimal form (`abs < 1`):

```javascript
const slopeAsPct = (slope!=null && Math.abs(slope) < 1 && slope !== 0)
                   ? slope*100 : slope;
```

This handles both:
- Sprint 2.4b backend (`-2.07`) → displayed `-2.07%` ✓
- Pre-Sprint 2.4b backend (`-0.0207`) → displayed `-2.07%` ✓
- Edge cases (0, null, large values) all correct

### Bug #UI-2 — `yield_estimated` section had no renderer
New section from Sprint 2.4b. Added dedicated case with:
- Value basis, estimated monthly rent (highlighted)
- Annual gross rent and NOI
- Gross/net yield with color (green ≥6%, red <4%)
- Cap rate
- Rent source note
- Caveat banner (warns about estimate basis)

### Bug #UI-3 — `investment_scenarios` section had no renderer
New section from Sprint 2.4b. Added dedicated case showing the 5
scenarios as a horizontal grid using existing `.br-sens` styling
(reused from sensitivity tables for visual consistency).

### Bug #UI-4 — `tips` and `due_diligence` lists not displaying
Both renderers expected nested keys (`c.tips_ar`, `c.questions_ar`)
but backend stores the array directly as `content`. Added tolerance:

```javascript
const items = Array.isArray(c) ? c : (c.tips_ar || []);
```

So lists render correctly whether the backend puts them in a sub-key
or as the content itself.

---

## What the user will see (after deploy)

### Buyer report
- Negotiation card now shows the correct floor/opening/ceiling
- **Due diligence list visible** (was empty placeholder)
- Verdict + negotiation are visually consistent

### Seller report
- Pricing card shows correct realistic/aggressive/quick-sale figures
- **Trend slope reads "-2.07%/سنة"** instead of "-207%/سنة"
- **Tips list visible** (was empty placeholder)

### Investor report
- Real yield card: gross 5.22% / net 4.02% / cap 4.02%
- Investment scenarios grid (5 acquisition prices ±10%)
- Sensitivity table (5 cap rate levels)
- Market context summary

### Valuator report
- Methodology card (MoJ 80% / Cost 20% breakdown + reason)
- Material uncertainty section
- Reasoning trace audit
- Data gaps

---

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
copy /Y index.html index.html.bak5
tar -xf "%USERPROFILE%\Downloads\sprint2p4c-ui-alignment.zip"
git add index.html CHANGELOG_v9.md
git commit -m "Sprint 2.4c: UI alignment for new sections + trend slope fix"
git push heroku master
```

No backend changes → engine_version stays as `thammen-sprint2p4b-audience-fixes`.

## Verification (browser test)

1. Open https://thammen.qa
2. Enter: zone 52 / street 903 / building 90
3. Open details, set: عدد الطوابق 2، الحالة مُرمّم، عمر البناء 30، تشطيب فاخر "لا"
4. Try each audience button (مشتري، بائع، مستثمر، مثمّن)
5. Expected:
   - **مشتري:** verdict at-market, negotiation 1.7M-2.1M, due-diligence list shows 5 items
   - **بائع:** valuation 1.9M, pricing 2.0M realistic, trend shows "-2.07%/سنة", 5 tips visible
   - **مستثمر:** 4 sections including yield card and scenarios grid
   - **مثمّن:** methodology + uncertainty + reasoning + gaps
