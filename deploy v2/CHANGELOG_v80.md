# CHANGELOG v80 — Sprint 2.22.0b.2 — Guided staged-input flow (WRAP)

**Engine:** `thammen-sprint2p22p0b2-staged-input-flow` · SPRINT_TAG `2.22.0b.2` ·
api-health `3.1.0-sprint2.22.0b.2`
**Date:** 2026-06-06
**Files changed:** `evaluate_unified.py` (backend: `effective_footprint_m2` + hoisted `_eff_fp`
single-source + version bump) · `index.html` (frontend: Stage-2 geometry-confirm card +
`thammenReEvalGeometry` + `_b2IsBuilding`) · `test_sprint_2_22_0b2.py` (new, 22) ·
`test_sprint_2_22_0b1.py` (R6 version-pin relax) · `docs/BRIEF_Sprint2p22p0b2_staged_input_flow_SIGNED.md`
· `docs/PHASE0_2p22p0b2_input_flow_recon.md` · docs-close.
**`api.py` UNTOUCHED** (the geometry block lives in the engine output builder; version auto-derives
from `SPRINT_TAG`). **Brief:** Gate-2 SIGNED (Rule #63). **§5 recon:** `PHASE0_2p22p0b2`.

---

## 1. What this is
Turns b1's zoning-driven footprint-confirm into an **explicit, revisable Stage-2** (E16) by **wrapping**
the existing single-screen form — no wizard rebuild (§5 verdict: WRAP). The first result reads as a
preliminary Stage-1 estimate carrying a **«حسّن التقدير (المرحلة 2)»** affordance (footprint / floors /
basement) that re-POSTs `/api/evaluate/details` via the proven `window._lastSubmit` re-eval loop. Plus
the one backend honesty-completion of b1 (brief F3): surface the **effective** (post-cap) footprint the
comparison actually used.

## 2. Why this matters (user-visible)
- **The b1 geometry-confirm was passive.** It surfaced only inside the optional-details toggle / a static
  results card; nothing framed the bare result as *preliminary* or invited a refine. b2 makes the
  Stage-1→Stage-2 recompute explicit and self-contained on the results card (DESIGN_2p23 §2b: early
  stages should feel revisable).
- **The cap was silent (the real gap, brief F3).** b1 caps a confirmed footprint to the zone ceiling
  (e.g. user 600 → 540 = plot×0.60 on R1) and the estimate moves — but the JSON exposed only
  `suggested_footprint_m2` (the **405** assumption), never the **540** the engine used. A faithful
  "you confirmed X م²" had no honest number to show. b2 surfaces `effective_footprint_m2` and discloses
  the zoning cap when it bit (derive-don't-author, DESIGN_2p23 §2c).
- **The b1 card mis-rendered on bare land.** It showed a "ground building footprint" on `raw_land`
  (no building). b2 gates the confirm to building (villa/house) subjects only (brief F2).

## 3. Root cause / mechanism
- `evaluate_unified.py:~3999` — the effective footprint `_eff_fp = min(footprint_m2, plot×_zone_ceiling)`
  (confirmed) / `_suggested_fp` (assumed) was computed **inside** the substantiality try-block and used
  only for `_build_smart_bua`; the geometry surface (`:~4105`) emitted only `suggested_footprint_m2`.
- `index.html` — the geometry card (b1) rendered for any `v.geometry` (incl. `raw_land`, `zone=None`),
  with no staging framing and no effective/cap surface.

## 4. What this patch does
**Backend (`evaluate_unified.py`, value-invariant):**
- **Hoisted `_eff_fp`** to a single source of truth right after `_fp_confirmed` (computed once, reused by
  the substantiality stage AND the geometry surface) so the surfaced effective value can **never drift**
  from the value the engine used (brief F3 — no duplicate cap logic). Byte-equivalent: the same `_eff_fp`
  still reaches `_build_smart_bua`.
- Added **`effective_footprint_m2`** (= `round(_eff_fp)`) to the `valuation.geometry` block — additive;
  old clients ignoring it keep working.

**Frontend (`index.html`):**
- The geometry card → the **Stage-2 confirm surface**, gated to building asset-types via new
  `_b2IsBuilding(at)` = `{standalone_villa, villa, house}` (brief F2 — excludes `raw_land` + refusals).
  - **Assumed (Stage-1):** «📐 حسّن التقدير (المرحلة 2)» + «هذا تقدير مبدئي يفترض بناءً نموذجياً (المقترح
    {suggested} م² · حدّ التغطية النظامي (R1) 60%)» + inline inputs (floors / footprint / basement) +
    «احسب التقدير المُحسَّن».
  - **Confirmed (Stage-2):** «📐 مساحة البناء الأرضي (مؤكَّد ✓)» + «اعتُمدت مساحة البناء الأرضية:
    {effective} م²» + (when `effective < input`) the cap disclosure «حُدِّدت مساحة البناء إلى {effective}م²
    — أقصى تغطية أرضية مسموحة للقسيمة وفق اشتراطات المنطقة (R1 60%)».
  - The F4 basement line «السرداب (إن وُجد) يُعرض ويُلتقَط لكنه لا يُحرّك تقدير المقارنة.» kept **verbatim**.
- New `thammenReEvalGeometry()` — mirrors `thammenReEvalOverride`: copies `window._lastSubmit.body`, sets
  `footprint_m2`/`floors`/`basement`, re-POSTs `/details`, re-renders `show(data)`.
- **Rule #39 deviation:** the Stage-2 inputs are realised **inline on the results card** (self-contained
  UX) rather than scrolling back to the `dSec` form — same intent, same endpoint + `window._lastSubmit`
  pattern, gated F2. The full `dSec` form is unchanged (additive second path).

## 5. Verification — empirical evidence
- **py_compile** `evaluate_unified.py` OK. **`api.py` 0-diff** (R14 N/A for it).
- **Isolated** `test_sprint_2_22_0b2.py` **22/22** (production helpers, E14): effective = suggested when
  assumed; capped to plot×ceiling when confirmed (600/900 R1 → 540, 500/600 R1 → 360, 600/600 R2 → 300);
  below-ceiling input not capped; anti-inflation + assumed byte-identical for all plots/zones; F2 gate
  contract; fallback (no/zero plot → None); basement still excluded (b1 §5.5 intact).
- **R6:** relaxed the brittle `'b1'+'geometry'` ENGINE_VERSION pin in `test_sprint_2_22_0b1.py` to a
  `^thammen-sprint\d+p\d+p\d+` format check (same class as the a5/a8 relaxations; test-only).
- **DoD matrix:** aggregator `run_sprint_2p22p0a_suite.py` coverage-gate **PASS (392)** · security
  **15/15** · surface-honesty **45/45** · broad auto-walk **68/68 GREEN** (164.4s, 0 fail, no flake;
  b1 34/34).
- **Local E2E on the REAL engine (GIS reachable)** `.b2_e2e.py` on 56/565/21 — **value-invariant**:
  bare = **2,400,000** (suggested 405 = effective 405, assumed); floors3+fp600 = **2,900,000**
  (effective **540** capped, basis confirmed); +basement = **2,900,000** (identical → basement excluded).
- **R14 real-Chromium (node absent)** at **390×844**: **0 console errors**; `show`/`thammenReEvalGeometry`/
  `_b2IsBuilding` all defined; gate `standalone_villa`→show, `raw_land`→**excluded**; confirmed card
  renders «اعتُمدت … ٥٤٠ م²» + cap disclosure + button + basement line; assumed card renders «حسّن التقدير
  (المرحلة 2)» + «هذا تقدير مبدئي» + suggested + button (no cap); **no overflow** (page scrollW 390 =
  innerW; card scrollW 349 = clientW, right edge 370 < 390).

## 6. Deployment (Gate-1 — requires Anas's explicit in-session consent BEFORE push)
```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Post-deploy verification curl (browser-UA, Rule #61)
```
curl -s https://thammen.qa/api/health                     ^  (expect 3.1.0-sprint2.22.0b.2)
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate/details ^
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21,\"floors\":3,\"footprint_m2\":600}"
  -> expect valuation.amount 2,900,000 + valuation.geometry.effective_footprint_m2 = 540 (basis confirmed)
4-anchor value-invariance: 56/565/21=2.4M · 54/541/6=5.4M · 55/296/13=2.6M · 52/903/90=refusal
F2 gate live: raw_land PIN + apartment refusal do NOT carry the building-footprint confirm card.
```

## 8. What's NOT in this patch (scope boundary)
- **NO B (DESIGN_2p23 §2b authority/finality dial-down)** — the results-card range/point + the
  `🟢 شواهد كافية` badge are **untouched** → deferred to a separate **b.3** (multi-AI, Rule #54).
- **NO B-2 (R7 built-type/condition mechanism)** — Gate-2 SIGNED but **PARKED** on GT-2 n≥20 — untouched.
- **NO valuation-logic change** — every headline + the B-1 `value_floor` byte-identical (anchors
  2.4M / 5.4M / 2.6M / refusal). Only the additive `effective_footprint_m2` + the staged UI changed.
- **NO replace/wizard** — WRAP only.
- **NO multi-QARS footprint-basis change** (the suggestion still uses the full `pdarea`, not the
  per-villa effective — pre-existing b1 quirk, out of scope, Rule #38).
- Live Heroku post-deploy smoke (§7) runs **after** the Gate-1 push.
