# CHANGELOG — Sprint 2.16.9: MUC Frontend Display (Read from Root)

**Engine version:** `thammen-sprint2p16p9-muc-frontend-display`
**SPRINT_TAG:** `2.16.9` → /api/health reports `3.1.0-sprint2.16.9`
**Date:** 2026-05-18
**Files updated:** `evaluate_unified.py` (version bump only), `index.html`
**Severity:** 🟠 Display fix — completes the chain started by Sprint 2.16.8

---

## Why this matters

Sprint 2.16.8 deployed and the post-deploy curl confirmed: tower
responses now carry the full RICS VPS 5 MUC clause in
`d.material_uncertainty.muc_clause_ar`. The audit user then printed a
PDF of a tower valuation (4.62M ر.ق, full income approach) and the MUC
clause was **not on the page**.

Diagnosis took 5 minutes:

- `index.html:524-530` reads MUC only from `d.brief.sections` (looking
  for a section with `id='material_uncertainty'`)
- Villa responses contain that section because they pass through
  `output_briefs.py:185-200` which builds it
- Tower responses build their brief inline in `evaluate_unified.py`
  (`_build_fast_listing_only_response`, `_build_fast_income_only_response`)
  with only `implied_rent` + `next_steps` sections — no MU section
- Result: tower MUC clause exists in the JSON but the frontend never
  finds it

This display gap predates Sprint 2.16.8 — it was hidden until 2.16.8
because `muc_clause_ar` was `None` everywhere on the tower path. Once
2.16.8 populated the field, the gap surfaced immediately.

---

## What this patch does

### Change 1: `index.html` — read MUC from root, fall back to brief sections

```diff
   let muc_ar=null, muc_basis=null, muc_review=null;
-  if(d.brief&&Array.isArray(d.brief.sections)){
+  const mu=d.material_uncertainty;
+  if(mu&&mu.muc_clause_ar){
+    muc_ar=mu.muc_clause_ar;
+    muc_basis=mu.muc_basis_ar;
+    muc_review=mu.muc_review_recommendation_ar;
+  }
+  if(!muc_ar&&d.brief&&Array.isArray(d.brief.sections)){
     const muSec=d.brief.sections.find(s=>s.id==='material_uncertainty');
     if(muSec&&muSec.content){
       muc_ar=muSec.content.muc_clause_ar;
       muc_basis=muSec.content.muc_basis_ar;
       muc_review=muSec.content.muc_review_recommendation_ar;
     }
   }
```

**Lookup priority** (a deliberate ordering, not arbitrary):

1. **`d.material_uncertainty.muc_clause_ar`** (canonical root location).
   Sprint 2.16.8 ensures every fast-path response writes here. This is
   the location that should win going forward.
2. **`d.brief.sections[id=material_uncertainty].content.muc_clause_ar`**
   (legacy location). The villa path through `output_briefs.py` writes
   here. We keep this as a fallback so any code path that hasn't been
   migrated to the canonical structure still renders correctly.

The rest of the rendering block (banner card, basis line, review line)
is unchanged — only the lookup is.

### Change 2: `evaluate_unified.py` — version bump

```diff
-ENGINE_VERSION = 'thammen-sprint2p16p8-tower-ux-muc-clause'
-SPRINT_TAG = '2.16.8'
+ENGINE_VERSION = 'thammen-sprint2p16p9-muc-frontend-display'
+SPRINT_TAG = '2.16.9'
```

No engine logic changes. The version bump exists purely so
`/api/health` reports the correct Sprint after deploy — useful for
post-deploy verification (`curl https://thammen.qa/api/health | findstr
sprint2p16p9`).

---

## Empirical verification (pre-deploy, this container)

### Pre-Sprint audit confirmed the structure

Live calls to production (Sprint 2.16.8 state) probed both paths:

```
VILLA 56/565/10:
  material_uncertainty.muc_clause_ar present: True
  brief.sections[material_uncertainty] present: True   ← legacy too
  content.muc_clause_ar present: True

TOWER 69/305/201:
  material_uncertainty.muc_clause_ar present: True   ← Sprint 2.16.8
  brief.sections[material_uncertainty] present: False  ← gap
  brief section ids: ['implied_rent', 'next_steps']
```

So the root location works for both; the brief-section location works
only for villa. Hence the new code prefers root.

### Lookup simulation tests (5/5 passed)

A Python mirror of the new JS logic was executed against five payload
scenarios:

```
  ✓ tower: reads MUC from root
  ✓ villa: root wins over brief (canonical preference)
  ✓ legacy: falls back to brief.sections when root is empty
  ✓ normal regime: returns None (no display, correct behaviour)
  ✓ no brief: still reads from root
```

### Lesson 1 — `node --check` on inline JS

```
Extracted 1 inline script blocks (51182 chars)
✓ inline JS valid
```

Particularly important here because the change is inline JS only. If
the new lookup block had a stray `const` collision or a syntax slip,
the entire site would go silent (Sprint 2.16.1 lesson).

### Lesson 2 — mobile viewport

Not applicable. No CSS, no form, no layout change. Pure data-source
swap in a JS lookup block.

---

## Backward compatibility

- **Villa display:** unchanged. Villa responses populate MUC in both
  the root **and** the brief section. The root wins now, but the text
  content is identical (both come from the same `regime_muc()` source),
  so the rendered output is byte-for-byte the same as before.
- **Tower display:** previously the MUC card was simply absent. Now it
  appears between the freshness banner and the result card, matching
  the villa layout.
- **Out-of-scope responses:** same — MUC card now appears.
- **Large compounds:** same — MUC card now appears.
- **Any future path** that writes MUC to either location will render
  correctly.
- **Normal market regime** (if it ever returns): `regime_muc()` returns
  all-None and the helper writes nothing, so `mu.muc_clause_ar` is
  falsy, the brief fallback also fails to populate it, and the entire
  card is hidden. Correct.

---

## What this patch does NOT do

- **No engine logic changes.** Engine math, classification, MoJ
  pipeline, GIS calls all untouched.
- **No new fields.** The four MUC fields already exist in the response
  since 2.16.8; this Sprint only changes how the frontend reads them.
- **No removal of the brief-section path.** Output briefs still build
  a `material_uncertainty` section for villa reports. We don't remove
  it because (a) some downstream consumer might depend on it, and
  (b) it's now the documented fallback.
- **No PDF-specific layout work.** The MUC card is part of the rendered
  result HTML, and "Print → Save as PDF" captures whatever the browser
  shows. So once the card renders for towers, it appears in the PDF
  too. No separate PDF template to update.
- **Bug A8 (comparable adjustments grid)** — still deferred to Sprint
  2.20+. This Sprint doesn't touch valuation accuracy.

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y index.html index.html.bak_2p16p8
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p8
tar -xf "%USERPROFILE%\Downloads\sprint2p16p9-muc-frontend-display.zip"
findstr /C:"sprint2p16p9" evaluate_unified.py
findstr /C:"Sprint 2.16.9" index.html
git add index.html evaluate_unified.py CHANGELOG_v31.md
git commit -m "Sprint 2.16.9: MUC display — read from root, fallback to brief"
git push heroku master
```

## Post-deploy verification

1. **Health check:**
   ```
   curl https://thammen.qa/api/health
   ```
   Expected: `"version": "3.1.0-sprint2.16.9"`

2. **Tower MUC display — the main test (browser):**
   - Open https://thammen.qa
   - Enter Zone=69, Street=305, Building=201, ask = 5,000,000
   - Submit → result page should now show a **red-bordered card at the
     top** with the heading "⚠️ تحفظ مادي وفق RICS VPS 5" and the full
     clause text below
   - Click "🖨️ طباعة / حفظ PDF" → the card should be in the PDF too

3. **Villa MUC display — regression check (browser):**
   - Enter Zone=56, Street=565, Building=10
   - Submit → result page should show the **same** MUC card (was
     working before this Sprint, must still work)

4. **Compare PDFs:**
   - The tower PDF you printed before deploy: no MUC card
   - The tower PDF you print after deploy: MUC card present
   - The villa PDF: identical before/after

---

## Files in this patch

```
sprint2p16p9-muc-frontend-display.zip
├── index.html                  (MODIFIED: ~14 line diff — lookup block)
├── evaluate_unified.py         (MODIFIED: 2 line diff — version bump)
└── CHANGELOG_v31.md            (NEW: this file)
```

No new test file — the change is too small and the logic is exercised
by manual browser verification.

---

## Sprint 2.16.x recap (3 days, 10 deploys)

| Sprint | What | Date |
|---|---|---|
| 2.16.0 | Stock Stratification exposure | 2026-05-17 |
| 2.16.1 | Hotfix — JS `const` collision | 2026-05-17 |
| 2.16.2 | Stratum-aware negotiation | 2026-05-17 |
| 2.16.3 | Mobile header overlap | 2026-05-17 |
| 2.16.4 | Mobile form clipping | 2026-05-17 |
| 2.16.5 | QARS endpoint → khazna | 2026-05-17 |
| 2.16.6 | Classifier v2 (subtype-aware) | 2026-05-18 |
| 2.16.7 | Housekeeping (A3+A4+B2+A10) | 2026-05-18 |
| 2.16.8 | Tower UX + MUC backend | 2026-05-18 |
| **2.16.9** | **MUC frontend display** | **2026-05-18** |

Bugs closed in this run: A1, A3, A4, A10, B2, plus 3 audit-discovered
issues (tower dead-end, MUC missing, MUC display gap). 7 catalogued
bugs still open, all 🔴 critical resolved.

---

_Last updated: 2026-05-18 (Monday) — tower flow now complete from address → classification → income approach → MUC clause on screen and in PDF. Next decision: rest, or 2.17 QARS snapshot, or await Thursday's confirmed sales._
