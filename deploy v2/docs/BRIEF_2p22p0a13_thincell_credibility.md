# BRIEF — Sprint 2.22.0a.13 — Thin-cell credibility (per-cell 36mo-capped fallback as continuous P2 shrinkage)

> **Gate-2 methodology — LOCKED by Anas 2026-06-01** (Rule #32 sign-off). Supersedes the Claude.ai v4
> brief draft's prior-design (P1 cross-pool) section; the measured basis is
> `PHASE1_RECON_2p22p0a13_thincell.md`. **Third sprint of the A→B built-type track**
> (A1 usage filter → A2 built-type → **A.13 thin-cell window/credibility** → B condition axis).

## 1. Problem (measured)
The villa bracket comp pool is thin: only **25/254 (10%)** of district×bracket 24mo villa cells reach
n≥20; **229/254 are thin** (after A2's correct pool-purification). Today a thin BRACKET inside a
healthy CATEGORY never widens (window is per-category at `moj_reference.py:89`), so thin cells route to
the dispersion-prone widened path or to `comparison_thin/preliminary/None`. Per-cell 36mo + light
shrinkage is the measured dominant remedy (+10 reliable over production), and widening biases the
median only **~0% on the total-price headline** (~5% downward on ppf, which is NOT the headline series).

## 2. Locked mechanism (the 8 decisions)
1. **Core remedy = per-CELL 36mo-capped fallback, implemented as continuous P2 shrinkage:** blend the
   cell's 24mo TOTAL-PRICE median toward its **OWN 36mo** median, `w = n24/(n24+k)`, **k=10**. Applied
   to the **surfaced robust total-price median only** (A2 lesson) — **NOT ppm²**.
2. **Refusal floor preserved:** apply only when `n24 ≥ N_REFUSE (5)`; below 5 → no rescue (behave as
   today). This also filters the n24=1 single-point A16 artifacts the recon flagged.
3. **Cap at 36mo** — the prior is the cell's own 36mo; never all-time/FULL (recon: ~5% downward per
   leg, no plateau past 36mo).
4. **Gate-before-shrink:** dispersion/range read from the **raw 24mo** pool; the shrunk value is the
   central estimate only and **never feeds the a10 gate's input** (the a10 gate is widened-path-only
   and reads `geo_v2`, structurally untouched here).
5. **DROP P1** (area all-bracket prior) — measured size-confounding (+8% Abu Hamour / −20% Marikh).
6. **A16 alias-merge = its OWN later sprint** (Rule #38), after a LIVE Marikh trace. R9 (the trace
   narrating the A16-starved bracket attempt vs the geo headline) folds into that A16 work.
7. **(vi) honest-range / E23 thin-cell dispersion = FAST-FOLLOW** (separate), UNLESS trivial reuse of
   the a10 presentation logic with no new copy. **Assessed: NOT trivial** (the a10 gate is
   widened-method-only; extending it to the bracket path needs new dispersion inputs + new
   presentation/copy) → **OUT, flagged as fast-follow.**
8. **No fresh multi-AI** — already over-validated.

## 3. Implementation (surgical, two files)
- **`moj_reference.build_reference` (additive only — existing fields untouched; other consumers
  `cap_rate_calibrator`/`moj_db`/tests unaffected):** per size-bracket, expose
  `n_24`, `n_36`, `total_price_median_24`, `total_price_median_36`, `total_price_p25_24`,
  `total_price_p75_24` (computed from the already-present category `in24`/`in36` lists).
- **`evaluate_property.apply_moj_strategy` (the comp-selection site):** for **villa only**
  (`moj_cat == 'villa'`), when `n_24 ≥ 5` and both medians present:
  `total_median = round(w·m24 + (1−w)·m36)`, `w = n24/(n24+10)`; tier on **n36** (bracket_n=n36,
  reliable=n36≥20); range (low/high) from the **raw 24mo** quartiles; append a trace note
  (`window 24→36 shrink, bracket, n24, n36, w, raw24, prior36, blended`). When `n24 < 5` → no change.
  Land + all other categories → unchanged.
- **Version:** `ENGINE_VERSION = thammen-sprint2p22p0a13-thincell-credibility`,
  `SPRINT_TAG = 2.22.0a.13` (health `3.1.0-sprint{SPRINT_TAG}` auto-derives). CHANGELOG_v65.

## 4. Scope guards (Rule #38 — explicitly OUT)
A16 alias-merge (own sprint, after live trace) · (vi) honest-range / E23 (fast-follow, not trivial) ·
R7 built-type/**condition** axis (Branch B / 2.22.0b) · Cost approach (BLOCKED) · the ~12-file VPS-4
label pass. **Villa-only** (land bracket path unchanged — land was not in the recon's measured scope;
deferrable fast-follow if wanted, Rule #39 deviation noted).

## 5. Verification (TASK 3 — local, STOP at Gate 1)
- **Anchors (offline via the real `build_reference` + `apply_moj_strategy`, E14):**
  Abu Hamour 56/565/21 = **2.4M UNCHANGED** (reliable, ~0% move); Marikh 54/541/6 ≈ **4.5M UNCHANGED**
  (geo-routed / A16-starved, bracket_n<5 → no shrink); 55/296/13 = the EFFECT case (gentle move toward
  own 36mo; tier upgrade iff 36mo n≥20 — measure it); 52/903/90 = unchanged refusal.
- **Distribution guard:** measure the move across ALL reliable villa cells — expect ~1% (per the M2
  sim). **If any reliable cell moves materially, OR any n<5 cell presents a value → STOP (hypothesis
  fail).**
- Isolated logic test (≥5 cases incl. fallback + the <5 floor). py_compile. DoD regression
  (392 / 15 / 45 / 55). Then present; **HARD GATE 1 — no push without Anas's explicit approval.**

*Authored 2026-06-01. Owner: Anas (PO, Gate-2 sign-off received). Implementer: Claude Code.*
