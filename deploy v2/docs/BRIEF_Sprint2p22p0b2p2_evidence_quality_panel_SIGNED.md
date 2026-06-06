# BRIEF — Sprint 2.22.0b.2.2 (RE-DRAFTED) — Evidence-quality diagnosis panel (STANDALONE, fork-independent) — SIGNED

> **Status:** Gate-2 **SIGNED** by Anas (this session: «GO» after the §5 recon). Saved per Rule #63.
> Gate-1 (Heroku push) = separate explicit consent.
> **Supersedes** the withdrawn b.2.2 value-decomposition draft (which misapplied §3 — promoted the land/build
> VALUE split onto the results screen = the §2.1 "unsupported decomposition" failure mode). This re-draft
> implements §3 correctly: a CONFIDENCE/EVIDENCE-quality panel, NOT a value decomposition.
> **Authority:** `docs/DESIGN_2p2x_suspense_reveal.md` §1 + §3 (SIGNED) + `DESIGN_2p23` §3 (badge recalibration).
> **Fork-independent (like b.2.1):** scoped to the §3 panel only — robust to the `DESIGN_2p23` §4 outcome.

**Engine baseline (CC-verified live):** b2.1 `thammen-sprint2p22p0b2p1-separate-input-screens` / Heroku v167 /
api-health `3.1.0-sprint2.22.0b.2.1`.
**Target:** tag `thammen-sprint2p22p0b2p2-evidence-quality-panel` / api-health `3.1.0-sprint2.22.0b.2.2` /
CHANGELOG_v82 / Session_Log §20.33.
**Backend:** NONE — every component rating DERIVED from a field the engine already emits (§2c). FRONTEND-ONLY
(`index.html`); engine logic UNTOUCHED. **value-invariant.**

## 1. Objective
Replace the single binary confidence indicator (`🟢 شواهد كافية` / lone tier badge) on `resultsScreen` with an
honest **four-component evidence-quality panel**, each rated **قوي / متوسط / محدود**:
1. **اكتمال بيانات العقار** · 2. **جودة المقارنات** · 3. **حداثة بيانات السوق** · 4. **جودة توصيف المبنى**.
The «الشرح ≠ ثقة» guard is STRUCTURAL: a component improves ONLY on a real input that reduces uncertainty on
THAT axis. Explanation (GIS, decomposition, classification, trend) moves NO component. Condition (unverified)
does NOT strengthen characterization — stays «محدودة» until B-2 (PARKED, n≥20).

## 2. Scope IN (frontend only; every rating derived from an existing field — §2c)
1. The four-component panel REPLACING the single confidence badge/tier display on `resultsScreen`.
2. Each rating **derived** from its governing field (mapping fixed by CC §5 recon — see addendum).
3. «الشرح ≠ ثقة» enforced by construction (the panel consumes ONLY uncertainty-reducing fields).

## 3. Scope OUT (the corrections + the deferrals)
- **NO value decomposition on the panel** — land-floor + implied-building stay in their existing position
  («why this range» / Chapter-4 = later b.2.3), «تحليلي غير متحقّق». (Precise fix vs the withdrawn draft.)
- **NO condition=sensitivity range-shift** → follow-on b.2.2.1 (touches PARKED B-2).
- **NO chapter restructure / audience-split / full-arc commitment** → `DESIGN_2p23` §4 fork (Anas) + later phases.
- **NO confidence assertion not derivable from a field** (§2c). **NO backend / valuation change** — 4 anchors
  byte-identical; tier/MUC/`rics_compliant_status_ar` (a20) emitted UNCHANGED.

## 4. Acceptance / DoD (CC, at build)
1. 6-item checklist (py_compile; node — R14 Chromium substitute; mobile 390×844; regression per the CLAUDE.md
   DoD matrix; 5+ isolated; 3-address Heroku smoke).
2. Value-invariance: 4 anchors byte-identical; 56/565/21 refine fp600 = 2.9M + effective_footprint_m2 540.
   Engine diff = version-string only.
3. R14 real-Chromium on `resultsScreen` (preliminary + refined) at 390×844 + desktop: panel renders, no
   overflow, 0 console errors; old single badge gone.
4. «explanation ≠ confidence» proof: explanatory content leaves every rating unchanged; a rating moves ONLY
   when its governing input changes. tier/MUC/a20 IDENTICAL to v167 on the 4 anchors.
5. §2c derive proof: each rating reads from its engine field (sentinel asserts against the rendered surface).
6. SPRINT_TAG → b2p2; CHANGELOG_v82 (8-section); docs-close = CLAUDE.md #65a + Session_Log §20.33 + this brief.

## 5. Deploy (Gate-1 — separate consent)
- `git subtree push --prefix "deploy v2" heroku master` (Rule #43) · `git push origin master`
- Verify: /api/health (`…b2p2`) + /api/evaluate 56/565/21 (2.4M unchanged + 4 panel components, single badge absent).

## 6. Multi-AI
NOT required (UX framing; قوي/متوسط/محدود make no RICS/IVS claim).

---

## CC §5-recon addendum (the fixed mapping + 2 clarifications — measured on live v167, AS BUILT)

**Badge replaced =** `accuracy.{label,score,tier,explanation_ar}` (`index.html` result-card header + the
tier-coloured «ما معنى ذلك؟» block). Both removed; `explanation_ar` kept as a **neutral footer** in the panel.

**Field → rating (derived, §2c):**
| Component | Field(s) | قوي | متوسط | محدود |
|---|---|---|---|---|
| اكتمال بيانات العقار | `geometry.footprint_basis` + `user_inputs.condition` | confirmed + condition | confirmed | assumed |
| جودة المقارنات | `n_transactions` + `method` | bracket & n≥20 | n≥10 | <10 / insufficient |
| حداثة بيانات السوق | `data_freshness.tier` | fresh/current | non-stale | stale |
| جودة توصيف المبنى | `footprint_basis` + condition (building only) | (never — condition unverified, B-2 PARKED) | confirmed | assumed · **N/A raw_land** |

**Clarification 1 (CONFIRMED OK):** recency is **market-wide** — MoJ 157d stale → «محدود» for ALL properties
today; honest + §1-aligned (surfaces staleness); becomes property-discriminating when MoJ refreshes.

**Clarification 2 (the §4.3 correction — CONFIRMED):** the panel shows for **ALL valued results** (`hasValuation`),
NOT building-only; component 4 adapts to «غير منطبق — أرض» for raw_land (gating the whole panel to buildings would
strip raw_land's confidence display — a regression, since the replaced badge showed for land too).

**As-built verification:** isolated 26/26 · DoD 392/15/45/70 · R14 Chromium (bare/refine/land, 390×844 + desktop,
0 console errors, no overflow) — «explanation≠confidence» proven LIVE (refine fp600+condition raised اكتمال
محدود→قوي + توصيف محدود→متوسط while مقارنات/حداثة held). Value-invariant (engine diff = version-string only).
