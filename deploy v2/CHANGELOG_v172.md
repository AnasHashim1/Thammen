# CHANGELOG v172 — Sprint 2.22.0b.91 «الشامل proof-first» (full-report cold-evidence surfacing)

**Engine:** `thammen-sprint2p22p0b91-full-report-proof-first` · **SPRINT_TAG** `2.22.0b.91` · api-health `3.1.0-sprint2.22.0b.91`
**Date:** 2026-07-01 · **Files:** `index.html` (`showReport` + 3 proof helpers + `.rep-comp` CSS) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b91.py` (new) · re-point `test_sprint_2_22_0b90.py` (own version pin → agnostic)
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (`api.py` + the valuation engine UNTOUCHED; pure display of the broadcast `comparables`/`considered_comparables`/`neighbours`/`comparable_grid`/`trend`). **Gate-2** (presentation) — the SIGNED report-redesign §5.1 items 9-11 (Gemini r5).

## 1. Why this matters
The bank/valuer opens the FULL report and wants the **proof** — the actual Ministry-of-Justice sales behind the number — not the interpretation first. But the printable report (`showReport`) surfaced clusters/decomposition/methodology and **never showed the comparable transactions or the area trend** (those lived only on the result screen's «كيف وصلنا» accordion). b91 surfaces them, proof-first: the concrete sales + adjustments + trend lead **right after the number**, before the fine-print. (This complements b90's short-report face — the owner gets the glanceable face; the specialist gets the proof-first evidence.)

## 2. What this patch does (`showReport`)
Three pure display helpers, inserted right after the DEF-12 numbers, **before** the b55 fine-print clusters (proof-first reorder, item #9):
- **`_repComparables(v)`** — the b38-b41 keystone: `v.comparables` (matched/geo villa) or `v.considered_comparables` (cost-led «reviewed but did not set the number»), as a scannable `التاريخ · المساحة (م²) · السعر (ر.ق) · ر.ق/م²` table + the geo **`neighbours`** location-adjustment rows (source area · ×factor · raw→adjusted). **#10:** the unit «م²»/«ر.ق/م²» lives in the **column header**; cells are bare `fmt()` numbers. **#11:** the ×factor is a `dir=ltr` island (Rule #25, prevents ×/number bidi overlap). + CC BY 4.0 (E10).
- **`_repLandGrid(d)`** — for raw_land: the `d.comparable_grid` (79-row AdjustmentGrid) as `التاريخ · المساحة (م²) · خام ر.ق/م² · التعديل · مُعدَّل ر.ق/م²`; **#11:** the time-normalization percentage (`pct_display`, e.g. `+4.23%`) in a `dir=ltr` island. + CC BY 4.0.
- **`_repTrend(d)`** — the `d.trend` 24-month area chart (reuses the `.trend-row`/`.trend-col` markup), with the signed a3/T1.2 honesty (`suppressed_reason_ar` shown when the slope is suppressed-for-staleness).
All three **degrade gracefully** (thin cells / non-attached leaders / no grid → render nothing — the `if(!c…)return ''` guards).

## 3. Value-invariance
`amount/low/high/method/rule` UNTOUCHED. The helpers contain **no `v.amount` arithmetic** (verified) — they render broadcast rows. `showReport`'s only amount-math stays the single `(v.amount||0)*0.90` forced-sale convention. The 5-fixture value byte-gate is byte-identical to v260 (b88→b91).

## 4. Verification — empirical
- **b91 isolated `test_sprint_2_22_0b91.py`: 16/16** (E14 — helpers defined + graceful-absent guards · proof-first placement after DEF-12 before the clusters · #10 unit-in-header + bare-number cells · #11 ×factor + land-grid % in dir=ltr · trend chart + honest suppressed path · `.rep-comp` CSS · CC BY on both new tables · **no `v.amount` math in the helpers** + showReport ×0.90 unchanged · EN t() · version).
- **Re-point:** b90 (its own exact-version pin → version-agnostic, R6).
- **DoD:** aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · **broad walk ALL GREEN**.
- **R14 real-Chromium 390×844** (served index.html + the 3 fixtures with the proof data, AR + EN): **0 console errors**; **value byte-identical** — cost-led villa (`.b40_marikh`) ٢٬٤٠٠٬٠٠٠ + `considered_comparables` table (header «التاريخ · المساحة (م²) · السعر (ر.ق) · ر.ق/م²», first row `2025-09-30 · ٥٨٩ · ٣٬٢٢٦٬٢٤٢ · ٥٬٤٧٧`) + trend, **proof-first** (table before the clusters); geo villa (`.b41_v001`) ٣٬٨٠٠٬٠٠٠ + comparables + **neighbours** («بو هامور · ٦٢٠ · ٣٬٨٧١ · ×0.9517 · ٣٬٦٨٤», #11 dir=ltr); land (`f_land`) ١٬٢٠٠٬٠٠٠ + `comparable_grid` («2024-08-21 · ٥٢٥ · ٢٬٢٨٦ · +4.23% · ٢٬٣٨٣», #11 dir=ltr) + trend; **EN** headers "Date · Area (m²) · Price (QAR) · QAR/m²", trend title "Area trend", **no AR-chrome leak**; **no overflow (390==390)** on all.

## 5. Deployment
`git push origin master` (backup) → `git subtree push --prefix "deploy v2" heroku master` (Rule #43; backgrounded).

## 6. Verification curl (post-deploy)
`curl -s --compressed -A "Mozilla/5.0 …" https://thammen.qa/api/health` → engine b91. Served `index.html`: `function _repComparables`·`function _repLandGrid`·`function _repTrend`·`.rep-comp{` present. 5-fixture value byte-gate byte-identical to v260.

## 7. What's NOT in this patch
- The **landmark-proximity adjustment merge** (#11's «صيدلية·مطاعم +١٫٠٪» example) — `geometric_factors.named_landmarks` is broadcast as display-only **proximity facts** (malls/mixed_use/metros + distances), NOT value adjustments (the engine doesn't adjust villa value for landmark proximity), so there is no such adjustment row to merge. Deferred/N-A.
- Villa comparables are **conditional** on the broadcast (matched/geo/cost-led leaders); thin cells with no attached comparables render no table (graceful) — the same b38-b41 attach contract.
- Session_Log §20.115/§20.116 + the CLAUDE.md production-snapshot refresh = a deferred docs pass (the giant run-on lines exceed the edit token limit — §20.93 precedent).
