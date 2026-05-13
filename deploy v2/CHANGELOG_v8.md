# CHANGELOG — Sprint 2.4b: Audience Fixes

**Engine version:** `thammen-sprint2p4b-audience-fixes`
**Date:** 2026-05-13
**Files changed:** `evaluate_unified.py`
**Builds on:** Sprint 2.4a (methodology fixes)

---

## Bugs this patch closes

### Bug #1 — Valuator audience returned buyer content
The brief generator's `generators` dict uses the key `'valuer'`, but the
API accepted `audience='valuator'` and silently fell back to `_buyer_brief`
when the key didn't match. The actual frontend sends `'valuer'` and worked,
but the API was fragile.

### Bug #2 — Investor brief had only 1 section when no rent data
`_build_investor_sections` was only called when `income` cross-check
existed (requires user-provided rental or rent_reference for the area).
For sparse areas (e.g. Luqta), neither was available → all 4 useful
sections were filtered out but nothing rebuilt → only generic
`market_context` (1 section) remained. The "تقرير المستثمر" was
effectively a placeholder.

### Bug #3 — Trend slope displayed as raw decimal
`slope_annual_pct` was stored as `-0.0207` (raw fraction meaning
-2.07%/year) but the UI rendered it directly as text. Users saw
"-0.02%" instead of "-2.07%".

---

## What this patch does

### 1. Audience normalization (`_normalize_audience`)

New helper at evaluate_thammen entry point. Maps aliases to canonical:

| Input | Output |
|---|---|
| `buyer`, `مشتري` | `buyer` |
| `seller`, `بائع` | `seller` |
| `investor`, `مستثمر` | `investor` |
| `valuer`, `valuator`, `مثمن`, `مثمّن`, `مقيم`, `مقيّم` | `valuer` |
| anything else / empty | `buyer` (safe default) |

### 2. Investor fallback brief (`_build_investor_sections_fallback`)

When `income` is None (no rental input, no rent_reference data),
build a meaningful investor analysis from:
- Default Qatar cap rate per asset type (villa 4%, palace 3.5%,
  compound_small 6%, compound_large 7.5%, apartment_building 6.5%)
- Implied rent from cap rate × valuation × OPEX gross-up
- Three sections: yield_estimated, investment_scenarios, sensitivity
- Explicit caveat that figures are estimates, not measured rent

This means the investor brief is never empty — even for areas with
zero rent transaction data, the user gets a structured analysis with
±10% acquisition scenarios and Cap Rate sensitivity bands.

### 3. Trend slope normalization in `_rewrite_brief_anchored_sections`

When rewriting the seller brief, detect `slope_annual_pct` stored as
a raw decimal (`abs(value) < 1.0`) and multiply by 100. Same for
`latest_vs_peak_pct`. Result: UI consumers always get percentage form.

---

## Verified outcomes (local tests)

### All 4 audiences work for the same Luqta property:

| Audience | Brief title | Sections | All anchored on 1.9M? |
|---|---|---|---|
| `buyer` | تقرير المشتري | verdict, negotiation, flags, due_diligence | ✓ |
| `seller` | تقرير البائع | valuation, pricing, trend, tips | ✓ |
| `investor` | تقرير المستثمر | yield_estimated, investment_scenarios, sensitivity, market_context | ✓ |
| `valuator` → `valuer` | **تقرير المُقيِّم** ✓ | methodology, sources, material_uncertainty, reasoning_trace, gaps | ✓ |

### Investor brief now shows real numbers (was hollow before):

```
• [yield_estimated] تحليل العائد التقديري
    gross_yield_pct: 5.22%
    net_yield_pct: 4.02%
    cap_rate_pct: 4.02%
    estimated_monthly_rent: 8,400 QAR

• [investment_scenarios] سيناريوهات الاستثمار (5 scenarios ±10%)
    صفقة خاصة (-10%): 1,737,000 → 4.47%
    صفقة خاصة (-5%):  1,833,500 → 4.23%
    القيمة المُقدَّرة:    1,930,000 → 4.02%
    دفع علاوة (+5%):  ...
    دفع علاوة (+10%): ...

• [sensitivity] تحليل الحساسية — Cap Rate (±1%)
• [market_context] السياق السوقي
```

### Trend slope correct format:
```
Before: slope_annual_pct: -0.0207   (decimal — looks like 0%)
After:  slope_annual_pct: -2.07     (percentage — clearly -2.07%/yr)
```

### Valuer brief sections (RICS-grade):
```
• [methodology]         المنهجية المطبقة
• [sources]             مصادر البيانات
• [material_uncertainty] تحفظات مادية (RICS VPS 4 §3.2)
• [reasoning_trace]     سلسلة المنطق (Audit Trail)
• [gaps]                فجوات البيانات
```

---

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak4
tar -xf "%USERPROFILE%\Downloads\sprint2p4b-audience-fixes.zip"
findstr /C:"sprint2p4b-audience-fixes" evaluate_unified.py
git add evaluate_unified.py CHANGELOG_v8.md
git commit -m "Sprint 2.4b: audience fixes (valuator routing, investor fallback, trend slope)"
git push heroku master
curl -s https://thammen.qa/api/health
```

## Verification curl after deploy

**Valuator brief should now work:**
```bash
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":52,"street":903,"building":90,"audience":"valuer",
       "floors":2,"condition":"renovated","building_age_years":30,
       "is_luxury":false,"asking_price":2000000}'
```

Expected `brief.audience: "valuer"`, `brief.title_ar: "تقرير المُقيِّم"`,
sections include `methodology`, `material_uncertainty`, `reasoning_trace`.

**Investor brief should have multiple sections:**
```bash
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":52,"street":903,"building":90,"audience":"investor",
       "floors":2,"condition":"renovated","building_age_years":30,
       "is_luxury":false,"asking_price":2000000}'
```

Expected: at least 4 sections including `yield_estimated`,
`investment_scenarios`, `sensitivity`.

---

## What's NOT in this patch (deliberate)

- Frontend display updates for new investor sections (the data is there,
  the UI may need a small update to render yield_estimated, scenarios,
  sensitivity — this is index.html work for next iteration)
- Frontend display for new valuer sections (methodology, gaps, etc.)
- Localised text for some `note_ar` fields that could be richer
