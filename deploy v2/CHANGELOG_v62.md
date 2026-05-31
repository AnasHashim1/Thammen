# CHANGELOG v62 — Sprint 2.22.0a.10 — Stage-1 Honest Range under Built-Type/Condition Uncertainty

**Date:** 2026-05-31
**Type:** Methodology + **USER-VISIBLE** (gated widened villas: tier → indicative, MVU widened,
AR/EN disclosure; the P25–P75 range is the honest headline, the point is retained as the central
indicative estimate) — single-purpose (Rule #38).
**Deploy posture:** LOCAL isolated commit + tests + smoke. **NO Heroku/origin push without Anas's
go (Hard Gate 1).** Engine-version bump deferred to deploy-prep (see §8).
**Files changed:**
- `evaluate_unified.py` — `_stage1_dispersion_gate()` helper + a gated override block at the end of
  `_build_unified_output` (tier / MVU / disclosure).
- `test_sprint_2p22p0a10_honest_range.py` — new isolated test (16 checks).
- `CHANGELOG_v62.md` — this file.

Brief: `BRIEF_2p22p0a10` (Anas-signed, Rule #32). Builds on the read-only recon that RE-OPENED
54/541/6 (RISK_REGISTER **R7**, Session_Log §20.10.1).

---

## 1. Why this matters (user-visible correctness)

The widened (`geo_value`) villa path returns a **built-type- AND condition-blind**, size-bracketed
weighted median (`geo_reference_v2._categorize` lumps basic / 2-story+annex / +penthouse / مسكن /
مجلس into one `'villa'`; condition is not an input — R7) and presented it as a **precise point at
normal confidence**. For a Stage-1 subject (built-type + condition always unconfirmed) whose comp
pool is built-type-heterogeneous, that is **false precision** — exactly what RICS VPS 3 / IVS require
disclosed under thin/heterogeneous evidence. 54/541/6 (Marikh) → 681/ft² → 4.5M presented as a precise
point; the pool actually spans P25–P75 = 3.3M–5.4M.

## 2. Root cause

`build_reference_geo_v2` → `weighted_median_ft` over [villa-category + size-bracket 0.80–1.20× + 24mo],
SAME area (no geographic widening — "comparison_widened" is a misnomer). Built-type blind +
condition-blind → the median can sit anywhere in a wide pool. The honest signal is already present:
geo_v2 emits `p25_m2` / `p75_m2` / `weighted_median_m2`, and the engine already surfaces the range as
`valuation.low` / `valuation.high`.

## 3. What this patch does (backend only)

- **Dispersion gate** `_stage1_dispersion_gate(primary, geo_v2_result)`: fires on the widened
  (`comparison_widened` + `comparison_widened_indicative`) paths when
  `dispersion = (p75_m2 − p25_m2) / weighted_median_m2 ≥ STAGE1_DISPERSION_T` (**T = 0.30**). Bracket /
  thin / preliminary are excluded by method; missing/degenerate data → no gate.
- **When gated** (one override block at the end of `_build_unified_output`, wrapped in try/except):
  - **Tier → indicative** (`🟡 شواهد محدودة`, score 50) with an explanation that the comparables
    differ in built type/condition and the subject's are unconfirmed.
  - **MVU → widened** (`level='high'`, not downgraded) with AR + EN banners stating the spread is real;
    a factor is appended; `stage1_dispersion_gated=True`.
  - **Disclosure (AR + EN)** added to `valuation.range_disclosure_ar/en`; plus `range_is_headline=True`,
    `central_estimate` (= the retained point), `pool_dispersion`.
- **Backward compatible:** `valuation.amount` is unchanged (the point is retained as the central
  estimate); the range is already in `valuation.low/high`; the user-visible honesty rides on the
  **already-rendered** accuracy badge + MVU banner (no `index.html` change → mobile layout unaffected).
  Old clients ignoring the new fields keep working.

**Not changed:** the median computation; the bracket path (validated clean **for average-condition
subjects only** — see §9); built-type
stratification (the later Gate-2 fix); any inputs.

## 4. Verification

**Live local smoke (real GIS) — the three signed PINs:**

| PIN | method | central | range (P25–P75) | tier | MVU | gated |
|---|---|---|---|---|---|---|
| 54/541/6 Marikh | `comparison_widened` | 4,500,000 | 3,300,000 – 5,400,000 | 🟡 indicative | high + disclosure | ✅ disp 0.469 |
| 56/647/6 Maamoura | `comparison_widened` | 3,800,000 | 2,900,000 – 4,400,000 | 🟡 indicative | high + disclosure | ✅ disp 0.406 |
| 56/565/21 Abu Hamour | `comparison_bracket` | 2,500,000 | 2,200,000 – 2,600,000 | 🟢 sufficient | moderate | — (unchanged) |

**Isolated** `test_sprint_2p22p0a10_honest_range.py` — **16/16 PASS** (gating decision, T boundary at
0.30, method exclusion, missing-data guards, real Marikh/Maamoura anchors).

**Regression (DoD matrix, `PYTHONIOENCODING=utf-8`):** aggregator **392/392** · security **15/15** ·
surface-honesty **45/45** · broad **53/53 files** (auto-includes the new test).

## 5. Hypotheses

- **H1** 54/541/6 default → range 3.3M–5.4M, indicative, central 4.5M, + disclosure — ✅ (was precise
  4.5M / normal confidence).
- **H2** 56/565/21 (Abu Hamour, bracket) — ✅ UNCHANGED.
- **H3 (CORRECTED)** 56/647/6 (Maamoura) — **fires.** The brief's "tight pool" premise used the +8%
  median-lever, not dispersion (analyst error); measured dispersion is **0.406** (range 2.9M–4.4M), so
  the honest range is correct there too. (Option A signed.)
- **H4** 2nd high-dispersion area — **satisfied by Maamoura** (no clean 2nd-area guess PIN; others were
  `insufficient_data`). Systemic claim holds.

## 6. Calibration note

**T = 0.30** is a **tunable default**, calibrated on **n = 2** widened villas (Marikh 0.469, Maamoura
0.406 — both fire; bracket excluded by method). Revisit as the widened-villa sample grows. Lives as
`STAGE1_DISPERSION_T` in `evaluate_unified.py`.

## 7. What is NOT in this patch (scope boundary)

Built-type stratification (Gate-2 (c)); broker/condition input; the MoJ-bracket alias under-matching
(separate bug A16); re-baselining 54/541/6 as a point (we de-point via the range); any a9 changes; any
`index.html` change.

## 8. Deploy-prep deferred from this commit (do at Gate-1 GO)

1. Bump `ENGINE_VERSION` → `thammen-sprint2p22p0a10-stage1-honest-range` + `SPRINT_TAG` → `2.22.0a.10`
   (`/api/health` auto-derives). Omitted here to keep the commit the pure methodology change.
2. Re-run the four DoD suites (the a8 citation test is format/regex-pinned since a9 — the bump is safe).
3. `git subtree push --prefix "deploy v2" heroku master`; post-deploy live smoke (Rule #52) on
   54/541/6 + 56/647/6 + 56/565/21; `git push origin master` backup.

## 9. Addendum (2026-05-31) — a10 is necessary, NOT sufficient; the blindness is bidirectional

Post-a10 re-examination (Session_Log §20.10.2; RISK_REGISTER **R7** generalised): the built-type +
condition blindness is **bidirectional** and affects **both** comparison paths — the engine returns the
comp pool's central tendency, blind to where the subject sits.
- **Over-anchors** below-average-condition subjects (54/541/6, widened) — a10's dispersion gate catches
  this (dispersed pool).
- **Under-anchors** above-average-condition subjects (**56/565/21** Abu Hamour, **bracket**: excellent
  G+1 + secure govt lease → engine 2.5M ≈ P68 **under-anchors ~10%**; defensible **~2.5–2.8M**, market +
  income basis). The pool is TIGHT (dispersion 0.211 → correctly NOT gated by a10), so **a10 does NOT
  catch this case.**

Therefore: the §4 "56/565/21 UNCHANGED" row and the §3 "bracket path (validated clean)" note hold **only
for average-condition subjects** and as a9/a10 regression invariants (those sprints don't touch the bracket
path) — **not** as a claim that 2.5M is this property's validated value. **a10 = necessary, not sufficient;
the real fix is Gate-2 (c) built-type/condition stratification (BOTH directions, ALL areas), input via
2.22.0b Stage-2 Q&A, not blocked on broker data sourcing.**
