# CHANGELOG v166 — Sprint 2.22.0b.85 «توائم الإنجليزية لتصنيف المخزون» (EN twins — the stock-stratification card)

**Engine:** `thammen-sprint2p22p0b85-en-strata-twins` · **SPRINT_TAG** `2.22.0b.85` · **api-health** `3.1.0-sprint2.22.0b.85`
**Files:** `stock_strata.py` (additive `*_en` keys + 2 EN maps) · `evaluate_unified.py` (the version bump) · `test_sprint_2_22_0b85.py` (NEW)
**Class:** 🟢 BACKEND-ONLY / **VALUE-INVARIANT** — additive `*_en` dict keys alongside the untouched `*_ar`; EN dormant (the frontend reads them via `pick()` only when `LANG==='en'`, b77, `EN_ENABLED=false`). `api.py` + `index.html` UNTOUCHED → **R14 N/A by construction** (the b83 strata `pick()` reads shipped + R14-verified; served AR render is a proven no-op). AR output byte-identical.

## 1. Why this matters

Second unit of the backend-`_en`-twins track (after b84 value-decomposition). The **stock-stratification card** (`_strataHtml`, the «تصنيف المخزون» tile in the result-screen «التفاصيل الكاملة» accordion + the report) rendered its every note in Arabic only — so in EN mode its eight `pick()` reads fell back to Arabic.

## 2. Root cause

`stock_strata.py` emitted the per-stratum + card labels/notes with no `_en` sibling: `STRATUM_LABELS_AR`/`STRATUM_DESC_AR` (no EN maps), per-stratum `label_ar`/`description_ar`/`reliability_label_ar` (compute_strata), subject `classification_label_ar`/`guidance_ar` (classify_subject_property), and the card `methodology_ar` / dominant `label_ar`+`note_ar` / `sprint_scope_caveat_ar` (build_stock_strata_result).

## 3. What this patch does

Adds the EN twins for exactly the eight fields `_strataHtml` reads via `pick()`:
- `STRATUM_LABELS_EN` + `STRATUM_DESC_EN` (4 entries each) → feed `label_en`, `description_en`, `classification_label_en`, dominant `label_en`.
- `compute_strata`: per-stratum `label_en`, `description_en`, `reliability_label_en` (mirror of the شواهد-tier dynamic: reliable→"Sufficient evidence (n≥10)" / n≥3→"Limited evidence (n=…)" / else→"Insufficient evidence").
- `classify_subject_property`: `classification_label_en`, `guidance_en`.
- `build_stock_strata_result`: `methodology_en`, dominant `note_en`, `sprint_scope_caveat_en`.
- The land-reference `source_ar` is NOT rendered via `pick()` (the `_strataHtml` label is a `t()` literal) → intentionally no `source_en` (kept minimal). No `_ar` value changed; no median / n / share / estimated_total changed — additive keys only.

**Personas (PO standing directive).** Linguist: professional English, register-consistent with the b78–b84 catalog + the EV_RATING evidence-tier wording («Sufficient/Limited/Insufficient evidence»). Lawyer: pure stratification-methodology copy — no valuation claim, no disclaimer; the conservative-blended-median framing is preserved.

## 4. Verification — empirical evidence

- Isolated `test_sprint_2_22_0b85.py` **16/16** — exercises the REAL `compute_strata` (aging dominant n=12 → reliable; luxury n=4 → limited) + `classify_subject_property` (aging), asserting each `_en` present + correct, **AR byte-identical**, and value-math untouched (n / median / estimated_total); + the three card-level static EN twins returned by `build_stock_strata_result`; + the frontend `pick()` wiring intact.
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · broad walk **141/141 ALL GREEN** (140→141; **zero re-points**).
- **R14 N/A by construction** — `index.html` git-confirmed UNTOUCHED; the strata `pick()` reads shipped + R14-verified in b83.

## 5. Deployment

```
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy)

```
curl --compressed -s https://thammen.qa/api/health    # engine = …b85
```
+ the 5-fixture value byte-gate byte-identical to v256 (54/541/6 2,400,000 · 56/647/6 3,800,000 · 55/296/13 2,600,000 · 56/565/21 2,400,000 · 52/903/90 None). (The strata `_en` fields render only when a villa has a stock-strata block + LANG='en'; the AR path is byte-identical.)

## 7. What's NOT in this patch (carried forward, Rule #42)

- Remaining backend `_en` twins: the audience-brief sections (output_briefs.py: `cap_rate_label`/`description`/`role`/`footer`/`body`/`recommendation`/`plausibility`/`caveat`/`rent_source`/`title` where missing), the cost-stack `assumptions`/`unavailable_reason`, the substantiality `rationale`/`methodology_note`, scope `requires_user_input`/`guidance`/`requires`, scenarios `delta_label`, tier-breakdown `role`/`source`, freshness `caveat` — each its own bounded value-invariant sprint.
- The **reveal** (`EN_ENABLED=true`) stays gated on the PO wording sign-off.
- No methodology / value / security change — additive i18n copy only.
