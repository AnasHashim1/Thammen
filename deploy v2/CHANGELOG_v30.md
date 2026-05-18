# CHANGELOG — Sprint 2.16.8: Tower UX + MUC Clause Recovery

**Engine version:** `thammen-sprint2p16p8-tower-ux-muc-clause`
**SPRINT_TAG:** `2.16.8` → /api/health reports `3.1.0-sprint2.16.8`
**Date:** 2026-05-18
**Files updated:** `evaluate_unified.py`, `index.html`
**Severity:** 🟠 High-leverage — completes the tower flow opened by Sprint 2.16.6, restores RICS VPS 5 MUC compliance on fast-path responses

---

## Why this matters

Sprint 2.16.6 (yesterday) made towers classify correctly. Sprint 2.16.7
(this morning) made `/api/evaluate` accept `asking_price`. Post-deploy
verification this morning revealed a side discovery:

> **The tower engine already works perfectly when given `rental_income` —
> 4,620,000 ر.ق valuation, full income approach, NOI/cap rate/yield —
> but the UI never asks for the rental, and the formal RICS VPS 5
> Material Uncertainty Clause is missing entirely from fast-path responses.**

Two gaps to close, both surfaced by the same audit.

### Gap 1 — MUC clause missing from fast-path responses

The audit ran Lusail B201 (zone 69/305/201, classified as `tower` after
Sprint 2.16.6) through `/api/evaluate/details`:

```
asset_type            : tower
valuation.amount      : 4620000        (with rental_income=30000)
income_approach       : full           (NOI=277200, cap_rate=6%)
material_uncertainty  : level=high
  has muc_clause_ar?  : False          ← MISSING
  rics_compliant      : False
```

Cross-checked against a standard villa (56/565/10, standalone_villa):

```
material_uncertainty keys: ['banner_ar', 'banner_en', 'factors',
'known_unknowns', 'level', 'muc_basis_ar', 'muc_clause_ar',
'muc_clause_en', 'muc_review_recommendation_ar', 'recommendations',
'rics_compliant']
```

Villas get the full RICS VPS 5 clause. Towers / large compounds / 
out-of-scope responses don't. Why?

**Root cause:** `material_uncertainty.py:regime_muc()` (defined in 
Sprint 2.14, ~3 months ago) generates the formal MUC clause. But
`grep -rn "regime_muc"` returns **zero call sites** in 
`evaluate_unified.py`. The function is **defined and used nowhere**.

The four `_build_fast_*` response builders in `evaluate_unified.py`:

- `_build_fast_insufficient_data_response` (line 1452 in v2.16.7)
- `_build_fast_listing_only_response` (line 1574)
- `_build_fast_income_only_response` (line 1813)
- `_build_out_of_scope_response` (line 1902)

…each construct `material_uncertainty` as an inline dict literal, with
no call to `regime_muc()`. Villas escape this only because they take a
different path (`evaluate_v3.py:448-461`) that does populate MUC fields.

Per Project Instructions §6: "منذ 2026-02-28: تحفظ مادي وفق RICS VPS 5
… كل تقدير يحمل الـ MUC clause". This was not happening for 
non-villa assets.

### Gap 2 — Tower UX dead-end

The audit also confirmed: when a tower returns `valuation.amount: null`
because the user only supplied `asking_price`, the UI shows a generic CTA:

> "→ أضف الإيجار أو سعر الإعلان"

The user has already supplied the asking price. The CTA gives them no
indication that **the rental** specifically is what unlocks the
valuation. Meanwhile the API response carries a precise instruction:

```
service_scope.requires_user_input_ar: "الإيجار السنوي الإجمالي للبرج"
```

…which is rendered in a small `--warn`-coloured line buried below the
service-scope card. Easy to miss.

---

## What this patch does

### Change 1: `evaluate_unified.py` — new helper `_enrich_material_uncertainty`

Inserted just before the first `_build_fast_*` function. It takes the
inline `mu` dict and merges in the four RICS VPS 5 fields from
`regime_muc()`:

```python
def _enrich_material_uncertainty(mu: dict) -> dict:
    try:
        from material_uncertainty import regime_muc
        muc = regime_muc()
        out = dict(mu)
        for k, v in muc.items():
            if v is not None and k not in out:
                out[k] = v
        return out
    except Exception:
        return mu  # safety: never fail a request on MUC enrichment
```

**Design properties:**
- **Non-destructive:** if the caller already set `muc_clause_ar`, that
  value wins. We only fill in missing keys.
- **Returns a copy:** doesn't mutate the caller's dict.
- **Fail-safe:** any exception → return the input unchanged.
- **Regime-aware:** on `normal` regime (no active disruption),
  `regime_muc()` returns all-None and the helper injects nothing. This
  is the correct behaviour — RICS VPS 5 MUC is only required when the
  market is in disruption.

### Change 2: `evaluate_unified.py` — 4 fast-path wraps

Each fast-path builder's `'material_uncertainty': { ... }` dict literal
is wrapped through the helper:

```diff
-    'material_uncertainty': {
+    'material_uncertainty': _enrich_material_uncertainty({
         'level': 'high',
         'banner_ar': '...',
         ...
         'rics_compliant': False,
-    },
+    }),
```

Done in all four locations identified by `grep`: 1482, 1604, 1843, 1932 
(post-patch line numbers, helper-shifted from original 1452/1574/1813/1902).

### Change 3: `evaluate_unified.py` — version bump

```diff
-ENGINE_VERSION = 'thammen-sprint2p16p7-housekeeping-validators'
-SPRINT_TAG = '2.16.7'
+ENGINE_VERSION = 'thammen-sprint2p16p8-tower-ux-muc-clause'
+SPRINT_TAG = '2.16.8'
```

### Change 4: `index.html` — dynamic CTA + `goForm()` helper

The insufficient-data CTA now reads `service_scope.requires_user_input_ar`
and uses it verbatim, so the user sees exactly what input unlocks the
valuation:

```diff
-    h+='<button class="insuf-cta" onclick="go(\'form\')">→ أضف الإيجار أو سعر الإعلان</button>';
+    var ssReq=(d.service_scope&&d.service_scope.requires_user_input_ar)||null;
+    var ctaText=ssReq?('→ أدخل: '+ssReq):'→ أضف الإيجار أو سعر الإعلان';
+    var focusTarget=(d.asset_type==='tower'||d.asset_type==='compound_large'||(ssReq&&ssReq.indexOf('إيجار')>=0))?'rentalIncome':'askingPrice';
+    h+='<button class="insuf-cta" onclick="goForm(\''+focusTarget+'\')">'+ctaText+'</button>';
```

Towers and large compounds now get a CTA reading literally:
> "→ أدخل: الإيجار السنوي الإجمالي للبرج"

And the click lands the user directly on the `rentalIncome` field
(opened, focused, highlighted with a 2.5-second warn outline) rather
than dumping them in the form to figure it out.

The new `goForm(focusId)` helper:

```js
function goForm(focusId){
  go('form');
  if(!focusId)return;
  setTimeout(function(){
    var el=document.getElementById(focusId);
    if(!el)return;
    var det=el.closest&&el.closest('.det');
    if(det&&!det.classList.contains('open')){
      var hdr=det.querySelector('.det-h');
      if(hdr)hdr.click();
    }
    try{el.focus({preventScroll:false});el.scrollIntoView({block:'center',behavior:'smooth'});}catch(e){el.focus();}
    el.style.outline='2px solid var(--warn)';
    el.style.outlineOffset='2px';
    setTimeout(function(){el.style.outline='';el.style.outlineOffset='';},2500);
  },50);
}
```

The 50ms timeout lets the screen swap complete before we try to focus
inside the just-activated form. The `.det.open` check ensures the
collapsible building-details section is open (the rentalIncome field
lives inside it). Uses CSS variable `--warn` for the highlight so the
visual theme stays consistent.

---

## Empirical verification (pre-deploy, this container)

### Helper unit tests (6/6 passed)

```
\u2713 _enrich_material_uncertainty extracted from evaluate_unified.py
\u2713 version bumped to 2.16.8
\u2713 all 4 fast-path builders wrap material_uncertainty through helper

  \u2713 T1: 4 MUC fields injected on tower-style mu
  \u2713 T2: original mu keys preserved
  \u2713 T3: muc_clause_ar contains 'VPS 5'
  \u2713 T4: existing muc_clause_ar preserved (no overwrite)
  \u2713 T5: caller's dict not mutated
  \u2713 T6: exception safety — returns input on ImportError
```

The `verify_wraps()` step reads `evaluate_unified.py` and confirms all
four functions `_build_fast_insufficient_data_response`,
`_build_fast_listing_only_response`, `_build_fast_income_only_response`,
and `_build_out_of_scope_response` wrap their material_uncertainty
through the helper. If any future Sprint un-wraps one, this test fails.

### Regression suite (46/46 passed)

```
test_stock_strata.py ............................... PASS
test_scope_of_service.py ........................... PASS
test_material_uncertainty.py ....................... PASS
46 passed in 0.10s
```

### Lesson 1 — `node --check` on inline JS

```
Extracted 1 inline script blocks (50745 chars)
\u2713 inline JS syntactically valid
```

Particularly important for this Sprint — the new `goForm()` function 
and the dynamic CTA logic both go into the inline `<script>` block.
Sprint 2.16.1 taught us: a single duplicate `const` makes the entire
site silent.

### Lesson 2 — mobile viewport

The new CTA text could be longer than the old one
("→ أدخل: الإيجار السنوي الإجمالي للبرج" is ~36 chars vs ~28 for the
old). The button uses `class="insuf-cta"` which is already responsive
(checked: full-width on mobile). No further CSS changes needed.

---

## Backward compatibility

- **Villas, raw land, small compounds:** unchanged. They take the v3
  path which already populates MUC fields. The helper isn't reached.
- **Towers / large compounds / out-of-scope assets:** material_uncertainty
  now includes 4 additional keys (`muc_clause_ar`, `muc_clause_en`,
  `muc_basis_ar`, `muc_review_recommendation_ar`). Existing consumers
  that don't look for these keys are unaffected.
- **Frontend CTA:** if `service_scope.requires_user_input_ar` is absent
  (older or simpler responses), the CTA reverts to the old text exactly.
- **`go('form')`:** still works for callers that don't pass a focusId.
  `goForm` is a superset of `go('form')`.
- **Normal market regime:** if the regime ever flips back to `normal`,
  `regime_muc()` returns all-None and the helper injects nothing — 
  exactly the correct behaviour per RICS VPS 5.

---

## What this patch does NOT do

- **No new endpoint.** /api/evaluate/details unchanged; the engine
  already produces the income_approach response for towers when
  rental_income is provided.
- **No engine logic changes.** Cap rate (6.0% for towers) unchanged,
  OPEX ratio (23%) unchanged, NOI calculation unchanged.
- **No per-asset MUC content.** All assets get the same regime-level
  MUC clause from `regime_muc()`. Asset-specific MUC text (e.g.
  "tower-specific reliability concerns") would be a Sprint 2.19+ idea.
- **No retrofitting of villa path.** Villas already get the MUC clause
  via the v3 path; this Sprint doesn't touch that.
- **No new input field.** The `rentalIncome` field already existed in
  the form; this Sprint just makes the CTA point to it directly.
- **No fix for `rics_compliant=false` on towers.** The boolean stays
  false because `level='high'` triggers a hard non-compliance flag
  upstream. That's a separate decision: should a high-uncertainty
  income-approach be rics_compliant? Punt to Sprint 2.19+.

---

## Deployment

```
prompt command
cd /d "C:\Thammen\deploy v2"
copy /Y evaluate_unified.py evaluate_unified.py.bak_2p16p7
copy /Y index.html index.html.bak_2p16p7
tar -xf "%USERPROFILE%\Downloads\sprint2p16p8-tower-ux-muc.zip"
findstr /C:"sprint2p16p8" evaluate_unified.py
findstr /C:"_enrich_material_uncertainty" evaluate_unified.py
findstr /C:"goForm" index.html
git add evaluate_unified.py index.html CHANGELOG_v30.md test_sprint_2p16p8_muc_enrichment.py
git commit -m "Sprint 2.16.8: tower UX (dynamic CTA + focus) + MUC clause recovery"
git push heroku master
```

## Post-deploy verification

1. **Health check:**
   ```
   curl https://thammen.qa/api/health
   ```
   Expected: `"version": "3.1.0-sprint2.16.8"`

2. **MUC clause on tower (the main fix):**
   ```
   curl -X POST https://thammen.qa/api/evaluate/details ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201,\"rental_income\":30000}"
   ```
   Look in the response for:
   - `material_uncertainty.muc_clause_ar` → should be a long Arabic string
     starting with "⚠️ تحفظ مادي وفق RICS VPS 5"
   - `material_uncertainty.muc_clause_en` → English equivalent
   - `material_uncertainty.muc_basis_ar` → cites MoJ data lag
   - `material_uncertainty.muc_review_recommendation_ar` → review guidance

3. **MUC clause on listing-only path (no rental):**
   ```
   curl -X POST https://thammen.qa/api/evaluate ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":69,\"street\":305,\"building\":201,\"asking_price\":5000000}"
   ```
   Same 4 MUC fields should now be present in `material_uncertainty`.

4. **Villa regression — must STILL have MUC clause (via v3 path):**
   ```
   curl -X POST https://thammen.qa/api/evaluate ^
     -H "Content-Type: application/json" ^
     -d "{\"zone\":56,\"street\":565,\"building\":10}"
   ```
   Same 4 MUC fields. (This confirms we didn't break the v3 path.)

5. **Frontend tower UX (manual browser test):**
   - Open https://thammen.qa
   - Enter Zone=69, Street=305, Building=201, click "تقييم سريع"
   - Expected result page:
     - asset_type = برج سكني
     - Insufficient-data card visible
     - **CTA reads: "→ أدخل: الإيجار السنوي الإجمالي للبرج"** (not the old "→ أضف الإيجار أو سعر الإعلان")
   - Click the CTA → form opens, the rentalIncome field is focused 
     and outlined in orange for ~2.5 seconds
   - Fill rentalIncome = 30000, submit → income_approach valuation appears
     (value ≈ 4,620,000 ر.ق)

---

## Files in this patch

```
sprint2p16p8-tower-ux-muc.zip
├── evaluate_unified.py                       (MODIFIED: +30 line helper, 4 wraps, version bump)
├── index.html                                (MODIFIED: ~25 line diff — dynamic CTA + goForm)
├── test_sprint_2p16p8_muc_enrichment.py      (NEW: helper unit tests + sync check)
└── CHANGELOG_v30.md                          (NEW: this file)
```

---

## Bug catalogue after Sprint 2.16.8

| ID | Severity | Status |
|---|---|---|
| A1 | 🔴 | ✓ closed (2.16.6) |
| A3 | 🔴 | ✓ closed (2.16.7) |
| B2 | 🔴 | ✓ closed (2.16.7) |
| A4 | 🟠 | ✓ closed (2.16.7) |
| A10 | 🟢 | ✓ closed (2.16.7) |
| **Tower MUC missing** | 🟠 | ✓ **closed (this Sprint, was uncatalogued)** |
| **Tower dead-end UX** | 🟠 | ✓ **closed (this Sprint, was uncatalogued)** |
| A2 | 🟡 | open (Pydantic extra=ignore) |
| A5 | 🟡 | open (asset_type: unknown UX) |
| A6 | 🟠 | open — Sprint 2.18 latency |
| A7 | 🟡 | open (rics_compliant tier) |
| A8 | 🟠 | open — Sprint 2.20 comparables |
| B1 | 🟠 | open — Sprint 2.18 housekeeping |
| B3 | 🟡 | open (audience='hacker') |

5 originally catalogued bugs closed in 24 hours (A1+A3+A4+A10+B2), plus
2 audit-discovered tower issues closed today.

---

_Last updated: 2026-05-18 — Tower flow now complete from classification → income approach → MUC clause → UX. Next: 2.17 QARS snapshot OR await secretary's confirmed sales data (Thursday)._
