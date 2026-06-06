# BRIEF — Sprint 2.22.0b.2.1 — Separate input screens (structural; STANDALONE) — SIGNED

> **Status:** Gate-2 **SIGNED** by Anas (this session: «go — وقّعت (Gate-2). نفّذ كما وصفتَ…»). Saved to
> `docs/` per Rule #63. Gate-1 (Heroku push) remains a separate, explicit in-session consent.
> **Lane:** brief authored by the Claude.ai lane; CC ran the §5 recon (which RESHAPED the first draft — the
> staged-reveal Phase-1 version that depended on the unsaved `DESIGN_2p2x_suspense_reveal.md` was withdrawn in
> favour of this self-contained structural brief) and implemented.

**SELF-CONTAINED + FORK-INDEPENDENT.** This brief IS its own signed artifact (a structural sprint needs no
separate strategic design). It does NOT depend on the unsaved `DESIGN_2p2x_suspense_reveal.md`, and it does
NOT touch the §2b authority/finality dial-down (range-as-lead, badge) — that remains the open strategic fork
(`docs/DESIGN_2p23_stage_authority_boundary.md` §4), Anas's deliberate decision, OUT of scope here.

**Engine baseline:** b2 `thammen-sprint2p22p0b2-staged-input-flow` / Heroku v166 / api-health
`3.1.0-sprint2.22.0b.2`.

**§5 grounding (CC-verified live v166):** `go(n)`@498 (screen-switcher); `homeScreen`@337 / `formScreen`@366 /
`resultsScreen`@457; `dSec`@410 inside `formScreen`; staging card ~1204–1231 + `thammenReEvalGeometry`@742;
`_b2IsBuilding`@736 (F2 gate, confirmed shipped in b2); `effective_footprint_m2`@1209. All accurate.

**Target:** tag `thammen-sprint2p22p0b2p1-separate-input-screens` / api-health `3.1.0-sprint2.22.0b.2.1` /
CHANGELOG_v81 / Session_Log §20.32.

**Backend:** NONE — `effective_footprint_m2` (F3) already live. FRONTEND-ONLY; engine logic UNTOUCHED
(version-string bump only).

## 1. Objective
The optional property details currently sit on the SAME page as identification (`dSec` inside `formScreen`).
Move the INPUTS onto SEPARATE screens — identification on one, geometry/condition details on another — so each
input step is its own screen. Results/report content is UNCHANGED.

## 2. Scope IN (frontend only)
1. `formScreen` → **identification ONLY** (address tabs / PIN + audience + «ثمّن»). REMOVE the inline `dSec`
   block from `formScreen`.
2. NEW screen **`refineScreen`** (a 4th `.screen` via `go('refine')`) housing the relocated `dSec` inputs
   (geometry/condition: floors · footprint · basement · condition · age · luxury-finish · annexes · majlis;
   financial: asking · rent, as a clearly-secondary group).
3. Flow: identification → bare `/api/evaluate` → `resultsScreen` (FULL report) → optional «حسّن التقدير»
   = `go('refine')` → reuse `thammenReEvalGeometry()` → refined `resultsScreen` (with the live
   `effective_footprint_m2` + F3 cap disclosure + verbatim F4 basement copy).
4. Retire the in-`results` staging card (~1204–1231): its INPUTS move to `refineScreen`; its DISPLAY logic
   (effective_footprint, basement copy) stays on the refined results; the «حسّن التقدير» affordance now
   navigates to `refineScreen` instead of expanding in-card.
5. Quick path preserved natively: a user who doesn't open `refine` gets the full report from the bare eval.

## 3. Scope OUT (explicit)
- **NO authority/finality dial-down** (range-as-lead, badge recalibration) → the open §2b fork
  (`DESIGN_2p23` §4), deferred to Anas's deliberate decision.
- **NO** permanent-frame / component-diagnosis / decision-framed acts / uncertainty-staging → those belong to
  the (deferred) staged-reveal vision, not this structural sprint.
- **NO** backend / valuation change — anchors byte-identical. NO results-content change (the report is
  unchanged; only the INPUT location moves).

## 4. Acceptance / DoD (CC, at build)
1. 6-item checklist (py_compile [version bump]; node --check on extracted inline JS — the new screen + nav is
   the highest-risk item; mobile 390×844; regression per the CLAUDE.md DoD matrix; 5+ isolated tests for the
   new screen + nav/state; 3-address Heroku smoke).
2. Value-invariance smoke: 4 anchors byte-identical (2.4M/5.4M/2.6M/refusal); 56/565/21 `refine` fp600 still =
   2.9M + `effective_footprint_m2`=540.
3. R14 real-Chromium on each screen at 390×844 + desktop — `formScreen`, `refineScreen`, `resultsScreen`
   (preliminary + refined): no overflow, 0 console errors.
4. Nav: identification → results; «حسّن التقدير» → refine → refined results; back/forward preserves entered
   values (`window._lastSubmit`); skipping refine yields the full report.
5. F2 gate preserved: `refine` offered only for building asset-types (villa/house `comparison_*`), not
   raw_land / refusal — inherits `_b2IsBuilding`@736.
6. SPRINT_TAG → b2p1; CHANGELOG_v81 (8-section); docs-close = CLAUDE.md #65a + Session_Log §20.32 + this signed
   brief in `docs/`.

## 5. Deploy (Gate-1 — Anas's separate in-session consent before push)
- `git subtree push --prefix "deploy v2" heroku master`   (Rule #43)
- `git push origin master`   (backup)
- Verify curl: /api/health (expect `…b2p1`) + /api/evaluate/details on 56/565/21 fp600 (expect 2.9M +
  effective_footprint_m2:540 — unchanged).

## 6. Multi-AI
NOT required (structural UX, no RICS/IVS citation change, no contested copy).

---

## CC implementation note (recorded at build, Rule #39 deviation flag)
**Tower/apartment rent path preserved (out-of-literal-brief, flagged-and-proceeded).** `dSec` served TWO
flows: villa/house geometry/condition AND the tower/apartment rent split (`towerRentSection`, reached by the
insufficient-data CTA `goForm()`). The brief lists only the villa/house fields and gates `refine` to
villa/house (F2). To avoid stranding the tower-rent UI when `dSec` moved off the form, the WHOLE optional-
details block (incl. `towerRentSection` + `potentialRental` + the unit-pair) was relocated to `refineScreen`,
and the tower CTA `goForm()` was redirected `go('form')` → `go('refine')`. F2 still gates only the villa/house
geometry **card/button** on results (tower/apartment reach `refine` via their own CTA, as before). Net: every
pre-existing flow preserved; verified live in the R14 pass (goForm→refine reveals `towerRentSection` with the
tower-mode rental label). Reversible (single redeploy); nothing user-facing changed for tower/apartment except
the inputs now live one screen over.
