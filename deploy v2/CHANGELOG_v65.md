# CHANGELOG v65 — Sprint 2.22.0a.13 (thin-cell credibility)

**Engine:** `thammen-sprint2p22p0a13-thincell-credibility` · api-health `3.1.0-sprint2.22.0a.13`
**Date:** 2026-06-01 · **Gate-2 (methodology) — Anas-signed (Rule #32).**
**Files:** `moj_reference.py` (additive), `evaluate_property.py` (credibility blend), `evaluate_unified.py`
(version bump), `test_sprint_2p22p0a13_thincell_credibility.py` (new, 16 cases). Docs: committed in
`18f0a4a` (`docs/PHASE1_RECON_2p22p0a13_thincell.md`, `docs/BRIEF_2p22p0a13_thincell_credibility.md`,
RISK_REGISTER R9, Session_Log consult addendum). **Third sprint of the A→B built-type track**
(A1 usage → A2 built-type → **A.13 window/credibility** → B condition).

## 1. Why this matters
After A2 correctly purified the villa comp pool, it is THIN: only **25/254 (10%)** of district×bracket
24mo villa cells reach n≥20; **229/254 are thin**. Today a thin BRACKET inside a healthy CATEGORY never
widens (window is decided per-category at `moj_reference.py:89`), so thin cells route to the
dispersion-prone widened path (R7/E23 over-anchor territory) or to `comparison_thin/preliminary/None`.

## 2. Root cause
`build_reference` picks ONE window per villa category (`use,window = (in24,24) if len(in24)>=20 else
(in36,36)`); size brackets are sub-sampled from `use`. A thin bracket cannot independently borrow the
36mo data its own area already holds.

## 3. What this patch does (backend only, villa-only, total-price median only)
Per-cell 36mo-capped fallback **implemented as continuous P2 credibility shrinkage** of the surfaced
TOTAL-PRICE median toward the cell's **OWN 36mo** median (A2 lesson: shrink the robust total-price
median, NOT ppm²):
- `moj_reference.build_reference` — **additive** per-bracket fields `n_24`, `n_36`,
  `total_price_median_24/36`, `total_price_p25_24/p75_24` (from the already-present `in24`/`in36`).
  Existing fields unchanged → `cap_rate_calibrator` / `moj_db` / tests unaffected.
- `evaluate_property.apply_moj_strategy` (the comp-selection site) — for `moj_cat=='villa'` when
  `n24 ≥ 5`: `total_median = round(w·m24 + (1−w)·m36)`, `w = n24/(n24+10)`; tier on `n36`
  (`bracket_n=n36`, `reliable = n36≥20`); range (low/high) from the **raw 24mo** quartiles
  (gate-before-shrink); trace note (window/n24/n36/w/raw24/prior36/blended). `n24<5` → no rescue
  (refusal floor preserved; also drops n24=1 single-point A16 artifacts). Land + all other categories
  unchanged.
- `_THINCELL_K=10`, `_THINCELL_FLOOR=5`. **The a10 dispersion gate is widened-path-only and reads
  `geo_v2` — untouched; shrinkage never feeds it (decision 4).**

## 4. Locked decisions honoured (8)
(1) per-cell 36mo as continuous P2 shrink, k=10, total-price only · (2) `<5` refusal floor preserved ·
(3) cap at 36mo (no all-time) · (4) gate-before-shrink (range from raw 24mo; a10 untouched) ·
(5) P1 cross-pool prior DROPPED · (6) A16 alias-merge = own later sprint (R9) · (7) (vi) honest-range =
fast-follow, NOT folded (extending a10 to the bracket path is non-trivial — new dispersion inputs +
copy) · (8) no fresh multi-AI.

## 5. Verification — empirical evidence (local, read-only; production filters, E14)
- **Isolated** `test_sprint_2p22p0a13_thincell_credibility.py`: **16/16** (reliable gentle, thin→reliable
  upgrade, n36<20 case, `<5` floor, land skip, m36-missing skip, legacy-dict byte-stable, range=24mo).
- **Reliable-cell move guard** (25 cells, blended vs raw 24mo): median **+0.00%**, mean −0.17%,
  p95abs 1.68%, **max |move| 2.20%, #>5% = 0 → PASS** (no reliable cell moves materially).
- **Effect band** (5≤n24<20, 75 cells): median |move| **0.56%**, **10 tier-upgrades** (= the +10 reliable
  over production from Phase-1 M1). `<5` floor: **154 cells, no rescue**.
- **Anchors (real `build_reference`+`apply_moj_strategy`):** Abu Hamour 56/565/21 → 2,350,000 →
  2,357,895 (+0.34%), bracket_n=37 reliable → **headline 2.4M UNCHANGED**. Marikh 54/541/6 →
  geo-routed (A16-starved bracket_n) → my change touches neither `geo_reference_v2` nor
  `_select_primary_comparison` → **4.5M UNCHANGED by construction** (the `مريخ`-exact bracket
  counterfactual −1.43% is informational; it would only apply once the separate A16 sprint fixes the
  area-name resolution). 52/903/90 apartment → `moj_cat=None` → **unchanged refusal**.
- **DoD regression:** aggregator **392/392** · security **15/15** · surface **45/45** · broad
  **56/56 files** (was 55; +1 = the new test). py_compile 3/3.

## 6. Deployment (Gate-1 — pending explicit Anas approval)
```
cd /d "C:\Thammen\deploy v2"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Post-deploy verification (the items NOT confirmable locally — POST is 403 from the dev container)
- Live smoke (Heroku/Anas env): 56/565/21 = **2.4M** (unchanged); 54/541/6 ≈ **4.5M** (unchanged,
  geo-routed); **55/296/13 = the EFFECT case** — confirm gentle move toward its own 36mo + tier-upgrade
  iff its 36mo n≥20 (its PIN→area is GIS-resolved, measurable only post-deploy); 52/903/90 = unchanged
  refusal. `/api/health` engine = `…-thincell-credibility`.

## 8. What's NOT in this patch (Rule #38 scope guards)
A16 alias-merge (own sprint, after a LIVE Marikh trace; R9) · (vi) honest-range / E23 thin-cell
dispersion (fast-follow, not trivial) · R7 built-type/**condition** axis (Branch B / 2.22.0b) · Cost
approach (BLOCKED) · the ~12-file VPS-4 label pass · **LAND** bracket path (villa-only — land was not in
the measured recon scope; deferrable fast-follow, Rule #39 noted).
