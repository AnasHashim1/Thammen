# CHANGELOG v97 — Sprint 2.22.0b.14 — Decomposition coherence + report-voice (ISS-A07)

**Engine:** `thammen-sprint2p22p0b14-decomposition-coherence` · **api/health** `3.1.0-sprint2.22.0b.14`
**Date:** 2026-06-10 · **Gate-2:** SIGNED by delegation (D-6, «افعل الأصوب») · **Gate-1:** deploy-on-green
**Files:** `evaluate_unified.py` · `material_uncertainty.py` · `output_briefs.py` · `index.html` · `test_sprint_2_22_0b14.py`
**Brief:** `docs/BRIEF_Sprint2p22p0b14_decomposition_coherence_SIGNED.md` · **Recon:** `docs/PHASE0_2p22p0b14_coherence.md`

## 1 — Why this matters
The buyer report **contradicted itself** (live, Marikh 54/541/6): the value-decomposition said building = **65.7%** «يتسق مع بناء جديد أو فاخر», while the same page's 10-Year/stratum panel showed a **17-year** property in a pool **dominated by «فاخر / حديث البناء» (51.7%)** and the location features marked «✗ بناء قديم نسبياً». The high implied-building share is a **POOL artifact** (the R7 over-anchor made visible), NOT real building value — but the narrative *rationalized* it as new/luxury. One report must speak with **one voice**. Plus 3 copy leaks.

## 2 — Root cause
- **Narrative:** `_decompose_value` (`evaluate_unified.py:1452`) selects the `building_dominant` (≥35%) line «يتسق مع بناء جديد أو فاخر» purely on the residual %, blind to age / dominant stratum / user inputs.
- **Leak #1:** `material_uncertainty.py:372` appends a *strata* service-charge factor («رسوم الخدمات … لهذا المبنى») on a **standalone villa** (no service charges).
- **Leak #2:** `output_briefs.py:167` claims «لنفس المنطقة والشريحة» while the rate is **borrowed** from the 400-600 bracket (subject 600-900) — the authoritative `cap_rate_provenance.method_ar` already discloses the borrow; the brief body leaked.
- **Leak #3:** `index.html:1790` shows «… في وصف الإعلان (لم يُقدَّم وصف)» on an **address** evaluation (there is no ad).

## 3 — What this patch does (VALUE-INVARIANT — TEXT ONLY)
- **New `evaluate_unified._reconcile_decomposition_narrative(output)`** — a pure post-pass called in `evaluate_thammen` **after** `value_decomposition` is attached (and `stock_strata` + `property_basis` are present). When the implied-building is `building_dominant` on a **villa/house**, it selects per BRIEF §2:
  - **Case A** (old/vintage_capped + dominant ∈ {luxury_new, modern_stock} + no user luxury/new/renovated): rewrites the narrative to state the high share reflects a **premium-dominated pool, not real building value for a property this age**, cross-references the 10-Year rule, and invites «اختر «بناء فاخر»» if genuinely premium. Also rides a **reverse cross-line** onto the dominant-stratum note.
  - **Case B** (user new/luxury/renovated, or genuinely-new sys-age<5 non-vintage): keeps the existing «بناء جديد أو فاخر» line.
  - **Case C** (otherwise): honest «حدّ أعلى استدلاليّ» framing.
  - Rewrites **ONLY** `interpretation_ar` (+ the stratum note); never amount/range/method/floor/**% **/strata numbers. try/except — never breaks the response.
- **Leak #1** (`material_uncertainty.py`): for villa/house, the service-charge factor → «مصاريف تشغيل تقديريّة ضمن الفحص الدخليّ» (score unchanged → **MUC level value-invariant**); strata assets keep the original.
- **Leak #2** (`output_briefs.py`): when `provenance.bracket_borrowed`, the cap-rate body discloses the borrow («مُستعار من الشريحة 400-600 … شريحة العقار 600-900 بلا عيّنة كافية»), matching `cap_rate_provenance`; same-bracket → byte-identical.
- **Leak #3** (`index.html`): the ad-empty-state → «لا يوجد إعلان مرتبط بهذا التقييم — التحليل على العنوان مباشرةً.».
- **Phase-0 premise CORRECTION (recon):** the brief's «5.3M vs 5.4M basis divergence» does **NOT** exist live — `1,851,260 + 3,548,740 = 5,400,000` = the headline (the brief's `3,448,740` was a 100k typo). The basis-unification sub-fix is a confirmed **NO-OP**; `as_pct_of_total` stays **65.7 byte-identical** (the % is in the must-not-change set).

## 4 — Verification (EXECUTED)
- `py_compile` ✓ (3 .py) · isolated `test_sprint_2_22_0b14.py` **34/34** (A/B/C table + Marikh→Case-A verbatim + the §4 byte-identity contract + leaks #1/#2).
- DoD: aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface-honesty **45/45** · broad auto-walk **83/83** (177.9s, b13 82 + new test).
- **Local E2E (real engine, live GIS) — VALUE-INVARIANT 5/5:** 56/565/21 **2,400,000** · 54/541/6 **5,400,000** · 55/296/13 **2,600,000** · 52/903/90 **None** · 56/647/6 **3,800,000** — all byte-identical to b13; **Marikh narrative = Case A verbatim** (land 1,851,260 / bldg 3,548,740 / 65.7% unchanged); V001 also Case A (old-premium pool); the bracket/land-anchored/refusal paths unaffected (narrative_case None).
- **R14 real-Chromium 390×844:** `show`/`fmt`/`go` defined (whole-file JS parses), **0 console errors**, new ad-empty-state copy present (old gone), Case-A narrative + reverse cross-line wrap with **no overflow** (scrollW 390).

## 5 — Deployment
```
heroku auth:whoami            # §20.45 — if unauthorized, hand the subtree push to Anas
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6 — Verification curl (post-deploy, browser-UA — Rule #61)
```
curl -s -m 45 -A "Mozilla/5.0 … Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"
# expect amount 5,400,000 (byte-identical) + value_decomposition.building_implied.narrative_case == "A"
```

## 7 — What's NOT in this patch (§7)
Any value / method change (the R7 central stays — that is B-2's job) · the two-values display (DEF-12, screen-5) · strata thresholds · apartment surfaces.
