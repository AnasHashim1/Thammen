# BRIEF — Sprint 2.22.0b.2 — Guided staged-input flow (WRAP)

**Status:** Gate-2 **SIGNED** — saved to `docs/` 2026-06-06 (Rule #63 signature ritual; Anas routed the brief to CC to implement). Gate-1 (Heroku push) still requires separate in-session consent (§7).
**Engine baseline:** b1 `thammen-sprint2p22p0b1-geometry-zoning-footprint` / Heroku v165 /
  api-health `3.1.0-sprint2.22.0b.1` (verified live #57, 2026-06-06; qars healthy, MoJ 157d).
**§5 recon:** `docs/PHASE0_2p22p0b2_input_flow_recon.md` (WRAP verdict; loop measured live).
**Lane:** Claude.ai brief → CC implements.  **Target:** tag `thammen-sprint2p22p0b2-staged-input-flow`
  / api-health `3.1.0-sprint2.22.0b.2` / CHANGELOG_v80 / Session_Log §20.31.

## 1. Objective
Make b1's geometry-confirm an explicit, revisable Stage-2 by staging the existing single-screen form:
a Stage-1 "تقدير مبدئي" + a "حسّن التقدير" affordance into the proven /details recompute loop (E16).
Partial realisation of DESIGN_2p23 §2b — the authority/finality dial-down is deferred (see F5).

## 2. §5 verdict: WRAP (not replace)
The staged recompute loop already exists (PHASE0 §1): `/api/evaluate` → `/api/evaluate/details`,
`window._lastSubmit` re-POST, and the b1 `v.geometry` results card. Measured live on 56/565/21:
bare 2.4M → /details(floors3,fp600) 2.9M → +basement 2.9M (identical, basement excluded ✓).
Rebuild as a wizard would reuse the same endpoints but risk regressing 8+ shipped surfaces → rejected.

## 3. Signed Gate-2 decisions
- **F1 — scope = A (WRAP, frontend staging).** Graft onto the existing form+results; reuse /details +
  the window._lastSubmit re-eval pattern + the b1 geometry card as the Stage-2 confirm surface.
- **F2 — gate the Stage-2 geometry-confirm to BUILDING asset-types.** Show iff a `comparison_*`
  building path AND subject is villa/house; exclude raw_land (zone=None) and refusals. Gate on
  asset_type EXPLICITLY — `zoning_code` is only an n=1 proxy on land, do not rely on it alone.
  Also tighten the b1 quirk: the geometry card must not render the confirm step on raw_land.
- **F3 — effective footprint = (b) + cap disclosure** (the one scope-affecting decision — see §3.1).
- **F4 — basement copy: keep verbatim.** floors3+fp600 ≡ +basement = 2.9M, so
  «السرداب يُعرض/يُلتقَط لكنه لا يُحرّك تقدير المقارنة» is accurate (b1 §5.5). Do not reword.
- **F5 — A now; defer B to a separate b.3 (multi-AI).** b2 does NOT touch the results-card
  range/point or the `🟢 شواهد كافية` badge. Avoids bundling (#38), keeps b2 clean.

### 3.1 F3 detail
b1 caps a confirmed footprint to the zone's max ground coverage (e.g. 600 → 540 =
zone_max_coverage_pct × plot) and the estimate moves — but the JSON exposes only
`suggested_footprint_m2` (the 405 assumption), never the capped value actually used.
**Decision (b):** add ONE value-invariant backend field `effective_footprint_m2` = the post-cap
footprint b1 actually used. Frontend displays it and, **when it differs from the user's input,
discloses the cap**, e.g.:
  «حُدِّدت مساحة البناء إلى {effective}م² — أقصى تغطية أرضية مسموحة للقسيمة وفق اشتراطات المنطقة»
- Not new logic — surfaces a value b1 already computes; the honest completion of b1's cap behaviour.
- REJECTED (a) echo the raw input (600): shows a number the engine did not use (derive-don't-author
  violation, DESIGN_2p23 §2c). REJECTED frontend-side recompute of the cap from
  zone_max_coverage_pct × plot: logic duplication risks divergence from b1's actual cap → display drift;
  the backend is the source of truth for the value it used.
- FALLBACK (c) — strict frontend-only, no m² echo («تم اعتماد قيمتك» + estimate only): honest about
  not asserting a number, but the frontend has no cap signal so it cannot tell the user their footprint
  was bounded (the zoning insight is lost). Use only if Anas vetoes any backend touch.

## 4. Scope IN
- **Backend** (`evaluate_unified` / `api.py`): add `effective_footprint_m2` to the `geometry` block on
  the building /details path = the post-cap footprint used. Value-invariant; wrap in try/except; old
  clients ignoring the field keep working.
- **Frontend** (`index.html`):
  - Label the bare /api/evaluate result «تقدير مبدئي» (Stage 1) + a «حسّن التقدير (المرحلة 2)» affordance.
  - Stage-2 = open the existing `dSec` geometry inputs (footprint/basement/floors), re-POST /details via
    the window._lastSubmit pattern; gated per F2.
  - On the Stage-2 result: display `effective_footprint_m2` + the F3 cap disclosure (only when
    effective ≠ input); keep the F4 basement line verbatim.

## 5. Scope OUT (boundary)
- **NO B** (results-card range-not-point + badge recalibration) → b.3, separate, multi-AI.
- **NO B-2** (R7 built-type/condition elicitation): Gate-2 SIGNED but PARKED on GT-2 n≥20 — untouched.
- **NO valuation-logic change:** every headline + B-1 value_floor byte-identical
  (anchors 2.4M / 5.4M / 2.6M / refusal).
- **NO replace/wizard** — WRAP only.

## 6. Acceptance / DoD (CC, at build)
1. Pre-deploy 6-item checklist (py_compile; node --check on extracted inline JS; mobile 390×844;
   regression per the CLAUDE.md DoD matrix [single source, Rule #58]; 5+ isolated tests for the new
   field + the F2 gate incl. fallback; 3-address Heroku smoke).
2. Value-invariance smoke: the 4 anchors byte-identical; 56/565/21 /details fp600 still = 2.9M WITH
   `effective_footprint_m2` = 540 present.
3. F2 gate verified live: raw_land PIN + apartment refusal do NOT show the building-footprint confirm.
4. F3 honest: effective figure shown; cap disclosure fires when effective < input; never echoes the
   uncapped input.
5. R14 real-Chromium: the Stage-2 affordance + confirm step re-measured at 390×844 (no overflow) +
   desktop; 0 console errors (b2 changes index.html → R14 mandatory, not assumed).
6. CHANGELOG_v80 (8-section); ENGINE_VERSION + SPRINT_TAG bumped to b2; docs-close = CLAUDE.md #65a
   NEXT-STEP + Session_Log §20.31 + this signed brief in `docs/`.

## 7. Deploy (Gate-1 — Anas's separate in-session consent before any push)
- `git subtree push --prefix "deploy v2" heroku master`   (Rule #43)
- `git push origin master`   (backup)
- Verify curl: /api/health (expect b2 tag) + /api/evaluate/details on 56/565/21 fp600
  (expect 2.9M + effective_footprint_m2:540).

## 8. Multi-AI
- b2: NOT required (no RICS/IVS citation change; the cap line is plain UX/zoning copy).
- b.3 (deferred B badge/range copy): multi-AI REQUIRED per Rule #54.
