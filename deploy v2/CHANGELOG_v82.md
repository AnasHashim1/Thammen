# CHANGELOG v82 — Sprint 2.22.0b.2.2 (Evidence-quality diagnosis panel)

**Engine:** `thammen-sprint2p22p0b2p2-evidence-quality-panel` · **SPRINT_TAG** `2.22.0b.2.2` ·
api-health `3.1.0-sprint2.22.0b.2.2`
**Date:** 2026-06-06
**Files changed:** `index.html` (frontend) · `evaluate_unified.py` (version-string bump ONLY) ·
`test_sprint_2_22_0b2p2.py` (new, 26 checks) · `CHANGELOG_v82.md` ·
`docs/BRIEF_Sprint2p22p0b2p2_evidence_quality_panel_SIGNED.md`
**Authority:** `docs/DESIGN_2p2x_suspense_reveal.md` §1 + §3 (Gate-2 SIGNED) — Phase 2 of the staged-reveal
arc. **Implements §3 correctly** (an evidence-quality panel, NOT the value-decomposition the withdrawn b.2.2
draft mistakenly proposed). **Frontend-only; engine logic UNTOUCHED; value-invariant.** Gate-1 push = separate
explicit consent.

---

## 1. Why this matters
The result card led with a **single binary confidence badge** (`🟢 شواهد كافية` / `🟡 شواهد محدودة`) plus a
tier-coloured «ما معنى ذلك؟» block (green-for-high). Per the signed design (§2.1): a single green badge is a
**structural high-confidence signal** that a textual caveat cannot undo — it implies more certainty than thin/
condition-blind evidence earns. This replaces it with an honest **four-component evidence-quality panel**
(قوي / متوسط / محدود each), so the user sees *where* the estimate is solid and *where* it is thin — and (the
core guard) **explanation ≠ confidence**: explaining the value never raises the rating; only a real input that
reduces uncertainty on a specific axis does.

## 2. Root cause (what's being replaced)
- The binary badge: `acc.label` rendered in the result-card header (`index.html`, the `bc`/`bt` block + the
  `<div class="rb …">` in `.rh`).
- The tier-coloured «ما معنى ذلك؟» block (`acc.tier`→green/amber/red bg) in the valuation card — another
  binary-confidence visual.

## 3. What this patch does (frontend only, `index.html`)
1. **New pure helpers** `_evidenceRatings(d)` + `_evPill(rt)` + `evidencePanelHtml(d,acc)`. Each of the four
   ratings is **DERIVED from the engine field that governs it** (§2c derive-don't-author), per the mapping CC
   fixed in the §5 recon (measured on 4 live cases):

   | Component | Field(s) | قوي | متوسط | محدود |
   |---|---|---|---|---|
   | اكتمال بيانات العقار | `geometry.footprint_basis` + `user_inputs.condition` | confirmed + condition | confirmed | assumed |
   | جودة المقارنات | `n_transactions` + `method` | bracket & n≥20 | n≥10 | <10 / insufficient |
   | حداثة بيانات السوق | `data_freshness.tier` | fresh/current | non-stale | **stale (157d → all today)** |
   | جودة توصيف المبنى | `footprint_basis` + condition (building only) | (never — condition unverified, B-2 PARKED) | confirmed | assumed · **N/A for raw_land** |

2. **Removed the binary header badge** (`bc`/`bt` + the `.rb` div) — the header now shows only «نتيجة التقدير
   السوقي».
3. **Replaced the tier-coloured «ما معنى ذلك؟» block with the panel.** The comparables explanation
   (`acc.explanation_ar`, "based on N transactions") is **kept as a NEUTRAL footer** inside the panel
   (evidence-count-forward, no longer green-for-high).
4. **«explanation ≠ confidence» enforced by construction:** the panel consumes ONLY uncertainty-reducing
   fields; explanatory content (`value_decomposition`/`value_floor`, `geometric_factors`, `trend`) is **not an
   input to any rating**. The panel shows for ALL valued results (`hasValuation`); component 4 adapts to «غير
   منطبق — أرض» for raw_land (recon clarification — it would otherwise strip land's confidence display).
5. `evaluate_unified.py`: ENGINE_VERSION/SPRINT_TAG bump only. `api.py` UNTOUCHED.

**Two §5-recon clarifications (logged):** (a) **recency is market-wide** — MoJ 157d stale → «محدود» for every
property today; honest + design-aligned (§1 surfaces staleness), becomes property-discriminating when MoJ
refreshes. (b) **value-decomposition stays in its existing position** (the «why this range» / Chapter-4 layer =
later b.2.3), framed «تحليلي غير متحقّق» — this sprint does NOT move it onto the panel (that was the withdrawn
draft's §2.1 error).

## 4. Verification — empirical evidence
- **py_compile** OK (`evaluate_unified.py`).
- **Isolated** `test_sprint_2_22_0b2p2.py` — **26/26**: (A) static — panel helpers present, binary badge
  removed, panel rendered, four labels, «explanation≠confidence» footer, tier-coloured block gone, + JS
  governing-expression pins (bind the Python mirror to the shipped JS); (B) mapping mirror — the 4 live cases +
  edges (n=18→متوسط, n<10→محدود), refine improves ONLY the user-input axes, explanatory fields move NO rating,
  freshness governs recency.
- **DoD regression** (PYTHONIOENCODING=utf-8): aggregator **392** (ALL COUNTS MATCH) · security **15/15** ·
  surface-honesty **45/45** · broad auto-walk **70/70** (209s, no flake; 69→70 with the new test).
- **Value-invariance — engine diff = the 2 version-string lines ONLY** → output byte-identical by construction;
  4 anchors live (v167-equiv engine) **2.4M / 5.4M / 2.6M / refusal** unchanged; `/details` fp600 = 2.9M +
  effective_footprint_m2 540.
- **R14 real-Chromium** (served `index.html`, real-payload same-origin mocks; Claude_Preview): all functions
  defined, **0 console errors** (load + full flow). **390×844** — bare villa → results: panel «جودة الأدلّة»
  with 4 rated components [اكتمال محدود · مقارنات قوي(n37) · حداثة محدود · توصيف محدود], **binary badge gone**
  (header = title only, `.rb` absent), «explanation≠confidence» footer present, no overflow. **Refine** (fp600 +
  condition=good) → [**اكتمال قوي · مقارنات قوي · حداثة محدود · توصيف متوسط**] — the two user-input axes rose,
  comparables/recency held → **«explanation≠confidence» proven LIVE**. **Raw-land** → [محدود · قوي(n73) · محدود ·
  **غير منطبق — أرض**] (component 4 adapts). **Desktop 1280×800** — panel renders, no overflow.

## 5. Deployment (Gate-1 — PENDING Anas's explicit in-session consent)
```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
> Not yet executed. Post-deploy live smoke recorded here only after the Gate-1 push.

## 6. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health
:: expect "version":"3.1.0-sprint2.22.0b.2.2" + engine …b2p2 + qars healthy
curl -s -X POST https://thammen.qa/api/evaluate -A "Mozilla/5.0 ... Chrome" -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
:: expect valuation.amount 2,400,000 (unchanged); served index.html carries evidencePanelHtml + the 4 component labels; no 🟢 badge
```

## 7. What's NOT in this patch (scope boundary)
- **No value decomposition on the panel** — land-floor + implied-building stay where they are (the
  «why this range» Chapter-4 layer = **b.2.3**), framed «تحليلي غير متحقّق». (This is the precise correction vs
  the withdrawn b.2.2 draft.)
- **No condition=sensitivity range-shift element** → tight follow-on **b.2.2.1** (touches PARKED B-2). The panel
  already signals condition honestly via the «محدود» characterization row.
- **No chapter restructure / audience-split** → b.2.3 / b.2.4 (governed by the `DESIGN_2p23` §4 fork, Anas).
- **No backend / valuation / report-figure change.** **No** `api.py` change. tier/MUC/`rics_compliant_status_ar`
  (a20) emitted UNCHANGED.
