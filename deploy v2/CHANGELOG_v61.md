# CHANGELOG v61 — Sprint 2.22.0a.9 — Widened-path age/quality elasticity (facet a)

**Date:** 2026-05-30
**Type:** Methodology (headline value changes on two comparison paths) — single-purpose (Rule #38)
**Deploy posture:** Facet (a) shipped as isolated commit `acb1e40`; the bump + R6 pin relax +
the validation note land in the deploy-prep commit; **deployed to Heroku on Gate-1 GO (2026-05-30).**
**Engine version:** `thammen-sprint2p22p0a9-widened-elasticity` / SPRINT_TAG `2.22.0a.9`
(bumped in the deploy-prep commit; `/api/health` → `3.1.0-sprint2.22.0a.9`).
**Files changed:**
- `evaluate_unified.py` — `_age_quality_adj()` helper + Cases 2 & 3 of `_select_primary_comparison`
- `test_sprint_2p22p0a9_widened_elasticity.py` — new isolated test (28 checks)
- `CHANGELOG_v61.md` — this file

Brief: `BRIEF_2p22p0a9_widened_elasticity_v2.md` (signed, Gate 2). Supersedes the withdrawn
`BRIEF_2p22p0a9_widened_comp_path.md` (wrong implementation map — file conflation).

---

## 1. Why this matters

Operator report (PIN **54/541/6**, Marikh villa): the headline valuation does not respond to
property inputs — building age, plot shape — no matter what is entered. Investigation
(empirical-first, Rule #33; re-confirmed via a live `building_age` sweep) proved this is
**path-normal, not PIN-specific**: any property routed to the geographically-widened
comparison path inherits **zero property-elasticity** on the headline.

Measured baseline (v147, live GIS), Marikh headline across `building_age` 0 / 20 / 45:
**4,500,000 / 4,500,000 / 4,500,000** — flat. A thin-comp villa got *no* age/quality signal
precisely where the estimate is already coarsest.

## 2. Root cause (measured, not assumed)

`_select_primary_comparison` (`evaluate_unified.py:955`) selects the headline source per case:

| Case | method | value source | carries property-factor adj? |
|---|---|---|---|
| 1 | `comparison_bracket` | `bracket_value` (`fair_price_total or moj_median_total`) | ✅ full adj |
| 2 | `comparison_widened` | `geo_value` (`geo_v2['estimated_value']`) | ❌ **bypasses** |
| 3 | `comparison_widened_indicative` | `geo_value` | ❌ **bypasses** |
| 4 | `comparison_thin` | `bracket_value` | ✅ full adj |
| 5 | `comparison_preliminary` | `bracket_value` | ✅ full adj |

The bracket path multiplies the MoJ median by the property-factor adjustment
(`evaluate_property.py:1573` `fair_total = moj_median_total * (1 + adj)`), so it responds to
size **and** age/quality. The two `geo_value` paths take their headline from
`geo_reference_v2.build_reference_geo_v2` (`:460` → `:714`), which already applies
**inter-district price normalization** (`geo_reference_v2.py:447`) — it owns the *location*
dimension — but it never applies the `× (1 + adj)`. So Cases 2 & 3 had zero age/quality
elasticity. Thin/preliminary/bracket already carry the full adj and are **out of scope**.

## 3. What this patch does (backend only — Cases 2 & 3)

New helper `_age_quality_adj(valuation)` sums **only** the age/quality slice of
`valuation.factors_detail` — codes `building_age` + `plot_shape` — and clamps it to
`property_factors.MAX_ADJUSTMENT` (±0.10). Location factors (`zoning`, `commercial_street`,
`main_road`, `landmark`, `permitted_height`) are **excluded** — `geo_v2` already
inter-district-normalizes them, so re-layering would double-count (Fork 1, signed).
`corner`/`HBU` are not in this adjustment at all (separate `geometric_factors.py`).

In `_select_primary_comparison`, the widened headline and band are scaled once:
```
geo_value  = round(geo_value  * (1 + aq), -3)
geo_low    = round(geo_low    * (1 + aq), -3)
geo_high   = round(geo_high   * (1 + aq), -3)
```
applied **only** to Cases 2 & 3. When `factors_detail` is empty (factors did not run),
`aq = 0` → the block is skipped → the widened headline is **byte-identical** to v147.

**Asymmetry (signed):** bracket path = full adj; widened path = age/quality-only adj.
Intentional — `geo_v2` owns location for the widened path (Fork 1).

**Bound (signed):** reuses the existing ±0.10 clamp; the age/quality slice natural range is
≈ `[-6%, +3%]`, so the clamp essentially never binds (Fork 2).

**Scope (signed, corrected):** `comparison_widened` + `comparison_widened_indicative` only.
`comparison_thin` / `comparison_preliminary` / `comparison_bracket` are untouched / byte-stable
(Fork 3 — corrected from the first brief, which mis-grouped `comparison_thin`).

Facet (b) — accuracy-tier (`:4226`) and MVU downgrade (`:4569`) reframe — is **DROPPED**, not
deferred: the "widening-to-healthy-n = strengthened evidence" framing is the principled
RICS VPS 3 remedy for a thin bracket; reversing it would re-introduce over-stated uncertainty.

## 4. Verification — empirical evidence

**Live before/after (real GIS, this machine), Marikh `building_age` sweep + bracket control:**

| case | method | before | after | Δ | driver |
|---|---|---|---|---|---|
| control 56/565/21 | `comparison_bracket` | 2,500,000 | **2,500,000** | 0 | untouched |
| Marikh 54/541/6 age=0 | `comparison_widened` | 4,500,000 | **4,600,000** | +100k | بناء حديث جداً (+3%) |
| Marikh 54/541/6 age=20 | `comparison_widened` | 4,500,000 | **4,400,000** | −100k | بناء قديم نسبياً (−2%) |
| Marikh 54/541/6 age=45 | `comparison_widened` | 4,500,000 | **4,300,000** | −200k | بناء قديم (−4%) |
| apt 52/903/90 | `insufficient_data` | None | None | 0 | unchanged |

Headline moves are single-application (4.6 / 4.4 / 4.3 = base × (1 ± age%), no `adj²` stacking).

**Isolated test** `test_sprint_2p22p0a9_widened_elasticity.py` — **28 / 28 PASS** (deterministic,
no GIS): `_age_quality_adj` (age+plot only, location excluded, clamp, no-op cases) +
`_select_primary_comparison` (bracket/thin/preliminary byte-stable; widened/widened_indicative
scaled once; no-op identity; no double-count).

**Regression (DoD matrix, `PYTHONIOENCODING=utf-8`):**
- aggregator `run_sprint_2p22p0a_suite.py` — **392 / 392**
- security `test_sprint_2p16p17_security.py` — **15 / 15**
- surface-honesty `test_sprint_2p22p0a3_surface_honesty.py` — **45 / 45**
- broad `2p22p0_pre/run_regression_2p22p0a.py` — **52 / 52 files** (auto-includes the new test)

**External MoJ cross-check (Claude.ai lane — why a9 shipped, and why the contamination track closed):**
Ref property 54/541/6 is a **2-story villa + annex, ~20 yr**. Decomposing the MoJ 24-month data by
built type (`nw_l_qr`), the MoJ median for that **exact built type** in Marikh = **681 QAR/ft²**
(n=25, matched plot ~590 m²); the engine's widened value = **682 QAR/ft²** (4.5 M) → **MATCH**. The
widened path compared the subject to the correct built-type segment and landed right. The earlier
"luxury-contamination / Al-Waab" hypothesis is **DROPPED**: the n=22 "luxury" comps are Marikh's
**own** 2-story villas (p75 = 798, max = 867 QAR/ft²), not Al-Waab. a9's age factor correctly steps
the 20-yr villa 4.5 M → 4.4 M (right direction; the median is age-blind, so a 20-yr villa sits in
the lower half of the type range). **Backlog (not now):** whether `building_age` (−2% at 20 yr) is
strong enough for older villas — a possible future refinement tied to the 10-Year Rule.

## 5. Hypotheses

- **H1** widened headline moves with age — ✅ confirmed (4.6 / 4.4 / 4.3M).
- **H2** control 56/565/21 stays exactly 2,500,000 — ✅ (bracket untouched).
- **H3** thin / preliminary / bracket / apartment byte-stable — ✅ (isolated test + live control/apt).
- **H4** `aq` applied exactly once, no `adj²` — ✅ (test + live arithmetic).

## 6. What is NOT in this patch (scope boundary)

- **Facet (b)** — accuracy tier (`:4226`) + MVU downgrade (`:4569`) reframe — DROPPED.
- Income cross-check sanity cap (the absurd-rent finding) — separate sprint.
- Stage 2 Q&A (2.22.0b).
- No new user-facing strings; no new input fields (corner/HBU/zoning stay GIS-auto).
- `rics_compliant` field-rename — still deferred.

## 7. Deployment

**None this sprint** (Gate 1 not requested). When authorized, deploy is the standard
`git subtree push --prefix "deploy v2" heroku master` (Rule #43) — see §8 for the
required deploy-prep steps that are deliberately NOT in this commit.

## 8. Deploy-prep (done at Gate-1 GO, in the deploy-prep commit)

1. **Bumped `ENGINE_VERSION` → `thammen-sprint2p22p0a9-widened-elasticity` + `SPRINT_TAG` → `2.22.0a.9`**
   (`evaluate_unified.py:44-45`); `/api/health` auto-derives `3.1.0-sprint2.22.0a.9` (`api.py:642/644`).
2. **Relaxed the brittle version pin** in `test_sprint_2p22p0a8_rics_citation.py` (was
   `== 'thammen-sprint2p22p0a8…'` / `== '2.22.0a.8'`) to a **format/regex** assertion
   (`^thammen-sprint\d+p\d+p\d+` / `^\d+\.\d+\.\d+`) — fixes the R6 / a7 "no exact version pins"
   anti-pattern in lockstep with the bump.
3. Post-deploy live smoke (Rule #52): Marikh 54/541/6 age sweep + control 56/565/21 (= 2.5M) +
   apt 52/903/90, desktop + mobile 390×844. a9 is **backend-only** (no `index.html` change) →
   mobile layout structurally unaffected.
