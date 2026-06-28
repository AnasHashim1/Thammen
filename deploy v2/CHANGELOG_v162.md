# CHANGELOG v162 — Sprint 2.22.0b.81 «ربط التقرير الكامل بالإنجليزية» (EN wiring — the full report)

**Engine:** `thammen-sprint2p22p0b81-en-fullreport-wiring` · **SPRINT_TAG** `2.22.0b.81` ·
**api-health** `3.1.0-sprint2.22.0b.81`
**Date:** 2026-06-28 · **Files:** `index.html` (+93/−78), `evaluate_unified.py` (2 version
lines), `test_sprint_2_22_0b81.py` (new), + 8 R6/Lesson-2 sibling re-points
(`test_sprint_2_22_0b19/b26/b37/b52/b54/b55/b57/b80.py`).
**Class:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT — the EN render is DORMANT behind `EN_ENABLED`
(b77); in AR mode `t()` returns its first (Arabic) arg and `pick()` returns the `*_ar` field,
so the AR output is byte-identical. `api.py` + the valuation engine UNTOUCHED.
**Fifth sprint of the EN-localization track** (b77 infra → b78 backend catalog → b79 core-flow
→ b80 short report → **b81 full report**).

## 1. Why this matters
b80 wired the SHORT report (`showShortReport`). The FULL detailed report (`showReport`, `#repOut`)
— the most content-dense user surface (cover + DEF-12 three-value block + the b55 note clusters +
the legal/MUC block + the methodology annex + the audience brief + the footer/GT hook) — was still
100% Arabic. A partial EN site is a deficiency (the PO's #1 launch item is a full English version),
built DARK behind `EN_ENABLED` and revealed only when coverage is complete + the PO signs off on the
wording. This sprint wires the full report's OWN body to the b77 i18n primitives.

## 2. Root cause
`showReport` (index.html:1717) emitted every label as a hardcoded Arabic literal and read every
engine note as a bare `obj.X_ar` insertion — no `t()`/`pick()`. The b80 re-render plumbing
(`_rerenderForLang` already routes `reportScreen → showReport`) and the `fmt()` locale switch were
in place; only the strings were unwired.

## 3. What this patch does
**Scope = `showReport`'s OWN body + the legal block + the inline map reads + scoped CSS.**
- **Inline literals → `t('<AR>','<EN>')`** (≈40 pairs): print button · cover brand/subtitle/meta ·
  the leader-aware central labels (`_midR`/`_def12R`: cost-anchor / median / central) · headline MV
  title + «النطاق التقديري السوقي» · the DEF-12 three-numbers bridge + the forced-sale row + the
  forced-sale basis line + the engine-numbers note · the b55 cluster labels («حول الرقم/العقار/
  البيانات») · the dual-evidence / dispersion / cite-n lines · the scenarios title · the cost-led
  «تفكيك المرتكز» card · the «ما لا نعرفه» header · the property-basics section + its `ri()` labels
  + the م²/ر.ق units · the methodology annex title + the RICS/IVS note header · the footer
  not-certified line + report-no + verify link + GT hook · the `_ax` «ملحق» label.
- **Engine `*_ar` reads → `pick(obj,'base')`** (18 fields — the `if(...)` guards still read `.X_ar`
  for truthiness, so AR is byte-identical; the EN twin comes from the SEPARATE backend track with a
  graceful AR fallback until it lands): `leadership.note` · `old_stock_reanchor.note` ·
  `cost_triangulation.note` · `value_floor.land_floor_note/land_anchored_note/implied_building_note`
  · `condition_note` · `leadership.age_honesty_note/resurvey_note` · `age_sensitivity.note` ·
  `hbu_note` · `value_stack.cost.label/sub/unavailable_reason` · `cost_note` · `scenarios.note` +
  `scenario.label/assumptions` · `methodology` · `rics_methodology_note` · `reason` ·
  `data_freshness.caveat` · `material_uncertainty.rics_compliant_status` · `brief.title`.
- **Legal block (handoff-named, lawyer/linguist-reviewed):** `_mucFields` is LANG-aware via `pick`
  (clause/basis/review → backend twin track); `_mucCardHtml` wires the standards header («تحفظ مادي
  وفق…» → «Material uncertainty under…», the RICS/IVS names + LRM marks kept) + «الأساس:»/«التوصية:»
  labels.
- **Inline maps:** new `TIER_LABEL_EN` (mirrors `TIER_LABEL_AR`) selected by LANG; the property-type
  row routes through `t(ASSET_AR[..],ASSET_EN[..])` (the b80 map idiom).
- **Scoped CSS:** `body.lang-en #repOut{direction:ltr;text-align:left}` (+ `.rep-foot` stays centred)
  — confined to `#repOut`, so the short report (`#srOut`, its own b80 rules) and the result screen
  are untouched; numbers stay in `dir=ltr` islands.

**DEFERRED (documented carry-forward, #38/#39):** the big SHARED result-family builders
(`_decompHtml`/`_substHtml`/`_strataHtml`/`evidencePanelHtml`+ev-helpers/`renderSection`/`pbRows`)
are also `show()`'s (b83, 718-line) subsystem; wiring them in b81 would balloon the sprint and
pre-empt b82/b83's stated `_ar` counts. They stay AR-fallback in EN (byte-identical AR regardless)
and are wired in the b83/show pass. `reasoning_trace.known_unknowns` (string array, no per-item _en)
+ the `.src-credit` clone stay engine/static AR.

## 4. Verification — empirical evidence
- **py_compile** `evaluate_unified.py` OK · **node --check** on the extracted inline JS **OK** (node
  v24.18.0 present).
- **Isolated** `test_sprint_2_22_0b81.py` **48/48** (E14, reads the real index.html: TIER_LABEL_EN +
  LANG selection · ≈15 representative `t()` pairs · 18 `pick()` swaps · scoped showReport-region
  absence of bare `+X_ar+` insertions while guards still read `.X_ar` · legal block · #repOut CSS
  scope + no #srOut/#resultsScreen bleed · deferred builders still CALLED · dormant flag · version
  format).
- **DoD:** aggregator **395 ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45** ·
  broad walk **137/137 ALL GREEN** (108.9s).
- **8 R6/Lesson-2 sibling re-points** (the showReport literals/`_ar` reads those tests pinned moved
  into `t()`/`pick()`; the AR text + every value/compliance/methodology assertion is preserved —
  **zero assertion weakened**): b19 (cost row via `pick(value_stack.cost,…)` — same SOLE source) ·
  b26 (`_midR`/`_def12R` + annex header via `t()`) · b37 (DEF-12 BUA row label via `t()`, BUA
  mechanics intact) · b52 (moj-sample line AR in `t()`) · b54 (report brand + footer term-lock now
  in `t()`; old «تقدير» still absent) · b55 (cluster labels + dual-evidence/moj lines in `t()`,
  value-floor via `pick`; order/compliance intact) · b57 (district `esc()` kept, label in `t()`;
  cost label/sub null-safety now via `pick()`) · b80 (the “no-bleed” check narrowed — b81 adds
  `#repOut` intentionally, `#resultsScreen`/global-`.thmr` still clean).
- **R14 real-Chromium 390×844** (4 captured fixtures, both modes; DOM-measured — the authoritative
  channel, screenshot timed out = the §20.34 capture hiccup):
  - **AR (Marikh cost-led):** amount **2,400,000** (byte-identical), all AR markers (MV title / both
    clusters / forced-sale / methodology / not-certified / property-basics), **EN_leak=false**,
    dir=rtl, docScrollW 390 == clientW 390 (no overflow).
  - **EN (forced LANG='en'+lang-en):** Marikh cost-led + V001 geo_full + Maraad e25 + raw_land all
    render the English chrome (Market value (MV) / Cost anchor / About the number+data / Indicative
    forced-sale value (×0.90) + “not a certified liquidation valuation. Basis: … × 0.90.” / Anchor
    breakdown / Methodology and standards / Property basics / “An automated market valuation, not a
    certified valuation” / **Material uncertainty under…** / Basis: / the GT hook), **amounts
    byte-identical** (2.4M/3.8M/2.6M/1.2M), **dir=ltr**, **no overflow** (repRight 370<390 on all),
    and the deferred shared builders correctly show AR (the documented carry-forward).
  - **0 console errors/warnings** across all 8 renders.

## 5. Personas (PO standing directive — lawyer + linguist on every change)
The handoff named the heavy/sensitive surfaces (DEF-12 triple + b55 clusters + the legal/MUC block).
**Lawyer APPROVE** — the EN carries every AR protection faithfully (not-certified ×N · the forced-
sale ×0.90 “not a certified liquidation valuation” · the MUC standards clause · RICS/IVS) with no new
claim and no weakened disclaimer; the engine MUC clause itself flows via the backend twin track (AR
until then). **Linguist APPROVE-WITH-NOTE** — فصيح + register/terminology-consistent with the shipped
b78–b80 catalog; the lone nit is straight-vs-curly apostrophe consistency across a few EN possessives
(`home's`/`Thammen's`) → folded into the reveal-sprint PO wording pass (cosmetic, dormant).

## 6. Deployment
```
cd /d "C:\Thammen"
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b81.py" "deploy v2/CHANGELOG_v162.md" "deploy v2/test_sprint_2_22_0b19.py" "deploy v2/test_sprint_2_22_0b26.py" "deploy v2/test_sprint_2_22_0b37.py" "deploy v2/test_sprint_2_22_0b52.py" "deploy v2/test_sprint_2_22_0b54.py" "deploy v2/test_sprint_2_22_0b55.py" "deploy v2/test_sprint_2_22_0b57.py" "deploy v2/test_sprint_2_22_0b80.py"
git commit -m "Sprint 2.22.0b.81: EN wiring of the full report (showReport) — frontend-only, value-invariant"
git subtree push --prefix "deploy v2" heroku master   # GATE-1 (explicit consent); split >5min → background
git push origin master                                 # backup mirror
```
Deploy note: the subtree split exceeds the 5-min foreground limit → run it backgrounded; `/api/health`
GET with `curl --compressed` (zstd). heroku auth held this session.

## 7. Verification curl (post-deploy)
```
curl -s --compressed https://thammen.qa/api/health            # engine = …b81
curl -s --compressed https://thammen.qa/ | grep -c "body.lang-en #repOut{direction:ltr"   # = 1
curl -s --compressed https://thammen.qa/ | grep -c "class=\"lang-en\""                      # = 0 (EN dormant)
```
Plus the 5-fixture value byte-gate identical to v252 (54/541/6 2.4M cost_led · 56/647/6 3.8M geo_full
· 55/296/13 2.6M e25 · 56/565/21 2.4M matched · 52/903/90 refusal).

## 8. What's NOT in this patch
- The big SHARED result-family builders (`_decompHtml`/`_substHtml`/`_strataHtml`/`evidencePanelHtml`/
  `renderSection`/`pbRows`) — deferred to the b83/show pass (they render AR in EN until then).
- The backend `*_en` twins for the engine notes (leadership/cost/condition/age/hbu/scenarios/
  methodology/rics-note/reason/MUC-clause) — the separate backend track; `pick()` falls back to AR.
- `reasoning_trace.known_unknowns` (no per-item _en) + the `.src-credit` clone — engine/static AR.
- `showConfirm` (b82) + `show` (b83) — the remaining per-function screens.
- The reveal (`EN_ENABLED=true`) — a later sprint, gated on full coverage + the PO wording sign-off
  (incl. the apostrophe-style normalization).
- Any engine / valuation-logic change — `api.py` + the engine UNTOUCHED; the value gate is untouched
  by construction.
