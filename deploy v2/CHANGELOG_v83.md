# CHANGELOG v83 — Sprint 2.22.0b.2.3 (Confirmation Gate, Screen 2)

**Engine:** `thammen-sprint2p22p0b2p3-confirmation-gate` · **SPRINT_TAG** `2.22.0b.2.3` · api-health `3.1.0-sprint2.22.0b.2.3`
**Date:** 2026-06-07 · **Files:** `index.html`, `evaluate_unified.py` (version strings only), `test_sprint_2_22_0b2p3.py` (new), `docs/BRIEF_confirmation_gate_SIGNED.md` (new)
**Type:** FRONTEND-ONLY · **value-invariant** (engine diff = the 2 version lines) · Gate-2 SIGNED.
**Design:** `DESIGN_2p2x_v4_owner_journey.md` (binding) + mockup `docs/thammen_owner_flow_mockup.html`; recon `docs/PHASE0_confirmation_gate_recon.md`. First sprint of the v4 «thinnest-flow» sequence.

## 1. Why this matters
Today the owner flow goes from address/PIN entry **straight to a result** — the user never validates that the
GIS-fetched basis is correct before the engine values it, and the number arrives with no early, de-emphasised
range. Two exposures: **trust** (the value lands without the user affirming the basis) and **correctness**
(GIS `asset_type`/subtype can be stale — Rule E7 / Bug A11, ~9.1% of government buildings — silently changing
the valuation basis with no checkpoint). Screen 2 inserts that checkpoint and surfaces a muted preliminary
**range** early → authority low at the start, rising with accountability at Stage 5 (the core v4 axis).

## 2. Recon (Phase 0) — frontend-only CONFIRMED
The brief's single contingency («if the preliminary-range datum isn't in `/api/evaluate` → Soft-Gate-3») was
**CLEARED** by a live probe (56/565/21, browser-UA): `valuation.low`=2,200,000 · `valuation.high`=2,600,000 ·
`valuation.amount`=2,400,000 + `asset_type`/`district`/`plot_area_m2`/`property_info.zoning`/`geometry.*` are
ALL already in the response. Screen 2 reads only fields the client already holds → **no valuation logic, no
backend field; `api.py` + `evaluate_unified.py` logic UNTOUCHED.**

## 3. What this patch does (`index.html`)
- **New `confirmScreen`** (a `.screen` between `formScreen` and the results render), populated by `showConfirm(d)`
  from the **same** response `run()` already fetched (no second `/api/evaluate`).
- **`run()` routing intercept:** after `show(data)` (results still rendered), a valued **non-valuer** journey →
  `showConfirm(data); go('confirm')`; **valuer** → `go('results')` directly (v4 «مُقيّم → التقرير الكامل مباشرة»,
  Rule #39); **refusals** (no `valuation.amount`) → `go('results')`. Flow advances **only on explicit confirm**.
- **`showConfirm(d)`** renders: (1) a **muted** preliminary range `valuation.low–high` + muted median «الوسيط ≈»
  (signed 5.1, range-not-point); (2) a **READ-ONLY** review card (signed 5.2 — **no ✏ pencils, no «صحّح»**) using
  the existing AR labels (`ASSET_AR` → «فيلا منفردة»), with a **plot-area honesty label** «المساحة المعتمدة في
  التقدير» when the engine-used `plot_area_m2` differs from the raw cadastral (`geometric_factors.plot_area_m2_verified`),
  else «مساحة القسيمة»; (3) the **b.2.2 evidence panel reused verbatim** (`evidencePanelHtml`, explanation ≠ confidence);
  (4) an explicit **«تابِع بهذه البيانات»** CTA (→ `confirmProceed()` → refine, per v4 تأكيد→تحسين) + the permanent
  **«التقرير الكامل الآن»** escape (→ results, no re-fetch).
- **Copy (signed 5.3):** the DRAFT CTA «البيانات صحيحة — تابِع» was **CHANGED → «تابِع بهذه البيانات»** (read-only
  honesty — don't ask the user to certify data they can't fix here). 9 cg-* CSS classes (production theme vars + Tajawal).
- `evaluate_unified.py`: `ENGINE_VERSION`/`SPRINT_TAG` → b2.3 (the **only** engine change). `api.py` UNTOUCHED.

## 4. Boundaries (no regression)
B-1 `value_floor` stays OUT of Screen 2 (it's in the response but belongs to the report — the corrected b.2.2 §3
error, not regressed). RICS/IVS citations + `methodology_ar` + disclaimers UNCHANGED (report screen). No correction/
editing of fetched attributes (deferred micro-sprint). No range-headline ±-bar (next thin-flow step). No condition
sensitivity (B-2 PARKED). No capture activation (DORMANT).

## 5. Verification — empirical
- **Value-invariance at source:** `git diff` of `evaluate_unified.py` = **2 lines** (the version strings); `py_compile` OK.
- **Isolated** `test_sprint_2_22_0b2p3.py` = **32/32** (reads the REAL index.html; structure + routing-guard mirror
  [valuer/refusal/zero → results] + signed copy verbatim + rejected-CTA absent + read-only [no «صحّح»/✏] + evidence-panel
  reuse + version-format, version-agnostic per R6).
- **DoD:** aggregator **392** gate PASS · security **15/15** · surface-honesty **45/45** · broad auto-walk **71/71**
  (was 70 at b2.2; +1 = the new test; 204.8s, clean).
- **R14 real-Chromium** (node absent → Chromium is the JS gate; EXECUTED): all 9 fns defined (whole-file JS parses);
  **0 console errors** across the full flow; live `run()` (buyer, 56/565/21, mocked-real payload) → **confirmScreen**
  rendering the muted range «٢٬٢٠٠٬٠٠٠–٢٬٦٠٠٬٠٠٠ ر.ق» + median + review (فيلا منفردة · بو هامور · R1 · المساحة المعتمدة
  في التقدير ٤٥٠ م²) + evidence panel + CTA, **no pencils, no rejected CTA**; CTA → **refineScreen**, full-report →
  **resultsScreen**, **valuer → resultsScreen** (gate skipped); **no horizontal overflow at 390×844, 375, and 1265**.

## 6. Deployment
```
cd /d "C:\Thammen\deploy v2"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
(Gate-1 — STOP for Anas's explicit in-session push consent first.)

## 7. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health | findstr "2.22.0b.2.3"
curl -s -A "Mozilla/5.0 ... Chrome/124 Safari/537.36" -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}" > out.json
findstr /C:"\"amount\": 2400000" out.json
```
Expect: health = b2.3; the 4 anchors (56/565/21 · 54/541/6 · 55/296/13 · 52/903/90) byte-identical to v168; served
`index.html` carries `confirmScreen` + `showConfirm`.

## 8. What's NOT in this patch
Range-as-headline / ±-bar (next thin-flow step) · condition sensitivity (B-2 PARKED, n≥20) · decomposition in the
result/report (later step) · inline attribute correction (deferred micro-sprint) · capture activation (DORMANT) ·
any backend / engine / valuation-logic change.
