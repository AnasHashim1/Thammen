# CHANGELOG v163 — Sprint 2.22.0b.82 «ربط شاشة التأكيد بالإنجليزية» (EN wiring — the confirmation screen)

**Engine:** `thammen-sprint2p22p0b82-en-confirm-wiring` · **SPRINT_TAG** `2.22.0b.82` ·
**api-health** `3.1.0-sprint2.22.0b.82`
**Date:** 2026-06-30 · **Files:** `index.html` (showConfirm body + 1 scoped CSS rule),
`evaluate_unified.py` (2 version lines), `test_sprint_2_22_0b82.py` (new),
+ 1 R6/Lesson-2 sibling re-point (`test_sprint_2_22_0b32.py`).
**Class:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT — the EN render is DORMANT behind `EN_ENABLED`
(b77); in AR mode `t()` returns its first (Arabic) arg and `pick()` returns the `*_ar` field,
so the AR output is byte-identical. `api.py` + the valuation engine UNTOUCHED.
**Sixth sprint of the EN-localization track** (b77 infra → b78 backend catalog → b79 core-flow
→ b80 short report → b81 full report → **b82 confirmation screen**).

## 1. Why this matters
b79–b81 wired the gate/home/form/top-bars/scope + the short and full reports. The **confirmation
screen** (Screen 2, `showConfirm`, `#cgOut`) — the owner's review step between identification and
the result (muted preliminary range + leadership-aware central label + the read-only GIS basis
review + the footprint tooltip + the confirm/escape CTAs) — was still 100% Arabic. A partial EN
site is a deficiency (the PO's #1 launch item is a full English version), built DARK behind
`EN_ENABLED` and revealed only when coverage is complete + the PO signs off on the wording.

## 2. Root cause
`showConfirm` (index.html:1152) emitted every label as a hardcoded Arabic literal and read its one
engine note (`d.asset_type_ar`) as a bare ternary — no `t()`/`pick()`. The b80 re-render plumbing
(`_rerenderForLang` already routes `confirmScreen → showConfirm`) and the `fmt()` locale switch
were in place; only the strings were unwired.

## 3. What this patch does
**Scope = `showConfirm`'s OWN body + 1 scoped CSS rule.** (Per the per-function discipline, the
SHARED builder `pbRows` is LEFT AR — it is owned by the b83/show pass; the evidence panel was
already dropped from the confirm screen by b32, so `evidencePanelHtml` is correctly absent here.)
- **Inline literals → `t('<AR>','<EN>')`** (≈22 pairs): the preliminary-range label + sub-line ·
  the QAR currency unit (×3) + the م² unit (×2) · the leader-aware central labels (`_midLbl`:
  cost-basis / median / central — the b24/m0 logic) · the cost-led dual-evidence line (matched /
  geographic) · the review-card title + the GIS sub-note · the `ri()` basis labels (address /
  property-type / district / zoning / plot-area-verified-vs-cadastral) · the footprint setbacks
  tooltip (both methods: setback-envelope + shared-parcel) + the max-buildable row label + the
  «عدّله في خطوة التحسين» refine CTA · the confirm button + the full-report escape link (the «◂»
  arrow flips to «▸» for the LTR reading direction).
- **The single engine `*_ar` read → `t(...)`**: the property-type label is routed through
  `t(ASSET_AR[at]||d.asset_type_ar||at, ASSET_EN[at]||d.asset_type_ar||at)` — **preserving the
  exact confirm fallback chain in BOTH args** so the AR output is byte-identical for every asset
  type (not just the ones in `ASSET_AR`); the `unknown` branch keeps the backend AR label, mirroring
  b81. `ASSET_EN` is the b80 map (already in scope).
- **CSS:** one scoped rule `body.lang-en #cgOut{direction:ltr;text-align:left}` — **load-bearing**
  (the parent `confirmScreen` pins `direction:rtl`, so the global `body.lang-en` flip alone does
  NOT reach `#cgOut`; the scoped rule does the flip — verified live: `confirmScreen`=rtl while
  `#cgOut`=ltr). No leakage to `#srOut` / `#repOut` / the result screen (each has its own rule or
  none). Centered sub-blocks (`.cg-est`, `.cg-link`) keep `text-align:center` by their own rules.

## 4. Backend / frontend / schema
- **frontend (`index.html`):** `showConfirm` strings + the `#cgOut` CSS rule. No structural change,
  no value math, no new field.
- **backend:** `evaluate_unified.py` = the 2 version-string lines only. `api.py` + the engine
  UNTOUCHED → the 5-fixture VALUE gate is untouched by construction.

## 5. Verification — empirical evidence
- **py_compile** `evaluate_unified.py` OK · **`node --check`** on both extracted inline scripts OK
  (the 200 KB app script parses clean; node v24.18.0).
- **Isolated** `test_sprint_2_22_0b82.py` **24/24** (E14, reads the real index.html: every literal
  `t()`-wrapped with the AR arg verbatim · the asset-type fallback chain preserved in both args ·
  the no-bare-insertion scoped check · `pbRows` still called · `evidencePanelHtml` correctly absent
  · the `#cgOut` scoped CSS · `_rerenderForLang` routing · dormant flag · version-agnostic tag).
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **395/395 MATCH** · security **16/16** ·
  surface-honesty **45/45** · broad walk `2p22p0_pre/run_regression_2p22p0a.py` **138/138 ALL GREEN**
  (137→138, +b82 test; **1 R6/Lesson-2 re-point:** `test_sprint_2_22_0b32.py` pinned three bare
  confirm literals — `ri('العنوان'`, `ri('المنطقة'`, `+' م²'` — that b82 `t()`-wrapped; re-pointed to
  the wrapped form, the «row/number stays» intent preserved, AR strings unchanged → b32 29/29; **no
  value/security/methodology assertion weakened**).
- **R14 real-Chromium 390×844** (live fixtures `.basket/f_marikh.json` [cost-led 2.4M] +
  `.basket/f_v001.json` [market-led, geo_widened, 3.8M], DOM-measured):
  - **AR (live mode):** `#cgOut` renders byte-identical AR — all markers (preliminary range, the
    cost-basis label / the «الوسيط» median label, the dual-evidence line, the review title, the
    footprint tooltip, the confirm button, the «◂» escape) · **0 English leakage** · `dir=rtl` ·
    `valuation.amount` 2,400,000 / 3,800,000 **untouched** · no overflow (`scrollW 390 == clientW 390`,
    cgMaxRight 370 < 390).
  - **EN (dormant, forced `LANG='en'`+`lang-en`):** full EN chrome (Preliminary estimate (range) /
    Cost basis (land + depreciated building) / Median / Market evidence: matched / Review property
    data / Geographic Information System (GIS) / Standalone villa / Address / Plot area / From the
    plot dimensions / Ground building area (max estimate) / adjust it in the refine step / Continue
    with this data / **Full report now ▸** [arrow flipped, no «◂»] / QAR / m²) · **0 Arabic-chrome
    leak** · `#cgOut` `direction:ltr` + `text-align:left` (via the load-bearing scoped rule) · value
    byte-identical · no overflow.
  - **0 console errors/warnings** across the whole session (page load + 4 renders).

## 6. Deployment
```
git -C "C:/Thammen" add "deploy v2/index.html" "deploy v2/evaluate_unified.py" \
  "deploy v2/test_sprint_2_22_0b82.py" "deploy v2/test_sprint_2_22_0b32.py" \
  "deploy v2/CHANGELOG_v163.md"
git -C "C:/Thammen" commit -m "Sprint 2.22.0b.82: EN wiring of the confirmation screen (showConfirm) — frontend-only, value-invariant"
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master   # backgrounded (split >5min)
git -C "C:/Thammen" push origin master                                 # backup
```
**Gate-1: pending an explicit deploy word** (the subtree split exceeds the 5-min foreground limit →
backgrounded; `heroku auth` valid).

## 7. Verification curl (post-deploy)
```
curl --compressed -s "https://thammen.qa/api/health" -A "Mozilla/5.0 ... Chrome/120 Safari/537.36"
  # expect engine_version thammen-sprint2p22p0b82-en-confirm-wiring
# served index.html carries:  body.lang-en #cgOut{direction:ltr   +   t('تابِع بهذه البيانات','Continue with this data')
# 5-fixture VALUE byte-gate identical to v253 (54/541/6 2.4M cost_led · 56/647/6 3.8M geo_full ·
#   55/296/13 2.6M e25 · 56/565/21 2.4M matched · 52/903/90 refusal) — frontend-only.
# class="lang-en" rendered = 0 (EN dormant).
```

## 8. What's NOT in this patch
- The `run()` loading-step strings + the `run()`/`thammenReEval*` error messages (form-flow JS,
  separate functions) — not in the confirm-screen scope; carried to a later form-path slice.
- The SHARED result-family builders (`pbRows` here; `_decompHtml`/`_substHtml`/`_strataHtml`/
  `evidencePanelHtml`/`renderSection`) — DEFERRED to the **b83/show** pass (they render AR until then).
- The backend `_en` twins for the number-bearing notes (leadership / cost / condition / age / hbu /
  scenarios / methodology / rics-note / reason / MUC-clause / freshness) — the separate backend
  track; `pick()` falls back to AR until they land.
- The **reveal** (`EN_ENABLED=true`) — held until coverage is complete + a full dual-language R14 +
  the PO's wording sign-off (incl. the straight-vs-curly apostrophe normalization noted by the
  linguist persona in b80/b81).
- Any engine / value / methodology change — none. AR live render byte-identical.

**⏭️ NEXT = b83 — wire `show` (the result screen, ~718 lines)**, which OWNS and wires the big SHARED
result-family builders that b80/b81/b82 deferred (`_decompHtml`/`_substHtml`/`_strataHtml`/
`evidencePanelHtml`/`renderSection`/`pbRows`), with lawyer + linguist personas on the MUC/evidence/
cost blocks → then the backend `_en` twins → then the **reveal**.
