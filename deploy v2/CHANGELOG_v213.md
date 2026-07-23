# CHANGELOG v213 — Sprint 2.22.0b.142 «توائم _en لمصفوفات التحذيرات والفحص» (EN twins for the caveat/checklist arrays)

**Engine:** `thammen-sprint2p22p0b142-en-caveat-checklist-arrays` · **api-health** `3.1.0-sprint2.22.0b.142`
**Date:** 2026-07-23 · **Files:** `en_localize.py` (+26 CATALOG entries + an `attach_en` array rule), `index.html` (a `pickArr` helper + 3 array-read swaps), `evaluate_unified.py` (2 version-string lines only), `test_sprint_2_22_0b142.py` (new), + 1 R6/Lesson-2 sibling re-point (b141 report read + its own version pin).
**Class:** 🟢 BACKEND-COPY + small FRONTEND / VALUE-NEUTRAL — `api.py` + the valuation engine UNTOUCHED (only the 2 version lines); additive `{key}_en` array twins; AR mode byte-identical (`pickArr` returns the AR array); amount/method/rule never touched → the 5-fixture value byte-gate is byte-identical.

## 1. Why this matters
**Sprint B, slice 1** (of the PO-approved A→ترشيق→B sequence). The b140 review measured the remaining EN residue: on the result screen (in EN mode) **32 Arabic strings still leaked**. The single biggest coherent group (**14 of the 32**) was two constant-Arabic **ARRAYS** that had no `_en` structure at all: `reasoning_trace.known_unknowns` (the "what we don't see yet" caveats) and the brief `due_diligence.content` (the buyer checklist «اطلب بيان عقاري…»). These leaked because the `en_localize` catalog only fills `{base}_ar`→`{base}_en` string keys — a plain array of Arabic strings has no key to attach to.

## 2. Root cause
`known_unknowns` (`reasoning_trace.py:177`, a `List[str]`) and the due-diligence `content` (`output_briefs.py:632`, a list of `_dd_questions`) are emitted as raw Arabic string arrays. `attach_en` skipped them (they aren't `_ar`-suffixed). The frontend read them raw (`d.reasoning_trace.known_unknowns` @index.html:2621/2839, `sec.content` @4383).

## 3. What this patch does (one mechanism)
- **`en_localize.py`**: added the **26 distinct constant strings** (15 known-unknowns across villa/apartment/raw_land + 11 due-diligence across villa/land) to `CATALOG` with the locked termbase (MoJ = "Ministry of Justice", "geotechnical survey", "occupancy certificate", …). Added an **`attach_en` array rule**: for the keys `known_unknowns` / `content`, when the value is a **list of strings with ≥1 cataloged item**, emit an index-aligned `{key}_en = [CATALOG.get(norm(x), x) for x in value]` (uncataloged items fall back to the Arabic item — graceful; a dict `content` [e.g. the yield section] or an all-uncataloged array gets no `_en` — list-only, self-limiting).
- **`index.html`**: a `pickArr(o, base)` helper (returns `o[base+'_en']` in EN mode if it's an array, else the AR array) + the **3 reads swapped**: `_s4bLimits` (result LIMITS), the report `_rtrR` known-unknowns, and the `due_diligence` renderer (`pickArr(sec,'content')`).

## 4. Verification — empirical
- Isolated `test_sprint_2_22_0b142.py` **17/17** — incl. the **COVERAGE guard** (every string the real engine puts into `add_standard_unknowns` [all asset types] + the ast-extracted `_dd_questions` literals is in CATALOG → 15 + 11, 0 missing; guards future drift) + additive/index-aligned + `_ar` untouched + the list-only rule (dict `content` gets no `content_en`; all-uncataloged array gets no twin) + the frontend `pickArr` + swaps.
- **R14 real-Chromium 390×844** on the live villa payload enriched by the real `attach_en`: **EN mode** → all 9 known-unknowns + all 5 due-diligence render in **English** (Arabic forms gone); **AR mode** → both render in Arabic with **no English leak** (value-invariant); value **٢٬٤٠٠٬٠٠٠ / 2,400,000 byte-identical**; **no overflow** (maxRight 374<390); **0 console errors**. Result-screen EN leaks **32 → 17** (the 15 remaining = the scattered structured fields / location features / methodology → b143).
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45** (T1.2 untouched) · broad walk **194/194 ALL FILES GREEN** (**1 R6/Lesson-2 re-point**: b141's report known-unknowns read now goes through `pickArr` + its own exact-version pin → version-agnostic; **zero value/security/methodology/compliance assertion weakened**).
- py_compile OK · `node --check` on all 3 inline scripts OK.
- Personas: **lawyer APPROVE** (the "what we don't see / what to verify" caveats + the buyer checklist are translated faithfully — no new claim, no value/methodology assertion; raises transparency for EN users) · **linguist APPROVE** (register-consistent فصحى→English on the locked termbase; MoJ / municipality / geotechnical / occupancy-certificate).

## 5. Deployment
`git push origin master` (backup first) → `git subtree push --prefix "deploy v2" heroku master` (from the repo toplevel `C:/Thammen`, Rule #43).

## 6. Verification curl (post-deploy, browser-UA #61)
`curl -s -A "Mozilla/5.0" https://thammen.qa/api/health` → `3.1.0-sprint2.22.0b.142`; the served `index.html` carries `function pickArr(` + `pickArr(d.reasoning_trace,'known_unknowns')` + `pickArr(sec,'content')`; a live `/api/evaluate` villa response carries `reasoning_trace.known_unknowns_en` + the `due_diligence` section's `content_en`; the 5-fixture value byte-gate byte-identical to v305.

## 7. What's NOT in this patch (→ b143, Sprint B slice 2)
The **17 remaining result-screen EN leaks** — all scattered single fields, not arrays: `service_scope.disclaimer` (a `pick()` reader exists; the catalog value has a window-text mismatch), `valuation.source` (interpolated `n=`), the MUC `factors` («لم يتم فحص…» / «المساحة المبنية…» / «مصاريف تشغيل…»), the interpolated corner `evidence`, the **location features** + zoning + geometry note (several already in CATALOG — need only a frontend `pick`), the permitted-height line, and the methodology footer. Each is its own consumption-recon slice per §20.113. The proper noun («امريخ الجنوبي») stays Arabic by design.
