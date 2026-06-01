# Phase-1 Reconnaissance — Sprint 2.22.0a.13 (thin-cell / window-fallback credibility)

> **Status:** Phase-1 recon ACCEPTED by Anas as the measured basis (2026-06-01); it overturned the
> prior (v4-draft) P1 cross-pool design in favour of P2 (shrink toward the cell's OWN 36mo). Gate-2
> design LOCKED (see `BRIEF_2p22p0a13_thincell_credibility.md`). Read-only recon — no engine change
> was made in Phase 1. All numbers are from production filters (`built_type`, `usage_filter`) on
> `moj_weekly.csv` (maxd 2025-12-31), cross-validated across 4 independent measurements
> (3 anchor scripts + workflow M1/M3 + a self-run M2 shrinkage sim).

## Ground-truth handshake (Rule #57) — clean
engine `thammen-sprint2p22p0a12-builttype-stratification` · api-health `3.1.0-sprint2.22.0a.12` ·
MoJ 152d stale (MUC active) · qars healthy · HEAD `fa5ad1b` / engine `9fa375c` · branch master ·
origin 0/0. Measured == expected on every axis.

## A. Decision loci (exact, quoted)
- **Bracket producer** `moj_reference.build_reference`: window chosen **once per CATEGORY** at
  `moj_reference.py:89` (`use, window = (in24,24) if len(in24)>=MIN_N else (in36,36)`, MIN_N=20);
  brackets sub-sampled from `use` (`:103-106`); empty → `{'n':0,'reliable':False}` (`:90-92`);
  per-bracket reliable `len(sub)>=10` (`:117`). **A thin bracket inside a healthy category never
  independently widens.**
- **Bracket selection site** `evaluate_property.apply_moj_strategy` (`:547`): picks the subject's
  `bracket_key = _bracket_for_area(plot)`, reads bracket `total_price_median` → `moj_median_total`
  → `valuation`; range from bracket `total_price_p25/p75`. Called at `:1528` with
  `build_reference` output (`:1504`). `area_name_in_moj` resolved once via `resolve_moj_area_name`
  (`:1491`) — **exact name, no alias expansion** (this is the A16 surface).
- **Headline consumer** `evaluate_unified._select_primary_comparison` (`:1000`), thresholds
  `MIN_N_RELIABLE=20 / MIN_N_INDICATIVE=10 / MIN_N_BOUND_ONLY=5`: Case 1 `comparison_bracket`
  (bracket_n≥20) → Case 2/3 widened → Case 4 `comparison_thin` (≥5) → Case 5 `comparison_preliminary`
  (≥3) → **`return None` = true refuse (`:1102`)**.
- **Geo/widened** `geo_reference_v2.build_reference_geo_v2`: **24mo only** (`:505`;
  `FALLBACK_WINDOW_DAYS` defined but unused there), escalates by adjacent-district annexation gated
  on `n_primary>=3` (`:590`); `confidence='insufficient'` when primary+adjacent<`N_REFUSE=5` (`:743`).
- **a10 dispersion gate** `evaluate_unified._stage1_dispersion_gate` (`:4121`, `STAGE1_DISPERSION_T=0.30`)
  — widened paths only, **presentation-only** (`range_is_headline`; median unchanged), structurally
  independent of any window/shrinkage change.

### Two reframes the data forced (measured-wins, Rule #58)
1. The brief's "never falls back to 36mo / strict-24mo baseline" is **imprecise**: production already
   runs a per-CATEGORY 36mo fallback — **76/109 villa areas sit at 36mo today**. The proposed lever
   is per-CELL; its gain is **+10 reliable over today's production (27→37)**, not over strict-24mo (25).
2. "No unbounded FULL window" — **confirmed**; 36mo is the last stop on both paths.

## B. Measured thin-cell census + staleness (villa comp pool = STANDALONE_VILLA + residential)

| View | cells | reliable ≥20 | indic 10-19 | context 5-9 | insuff <5 |
|---|--:|--:|--:|--:|--:|
| Production today (per-category window) | 296 | **27 (9%)** | 38 | 57 | 174 (59%) |
| (i) Per-cell 36mo fallback | 301 | **37 (12%)** | 36 | 59 | 169 |
| (iii) A16 alias-merge (24mo) | 208 | 26 | 31 | 42 | 109 |
| *anchor strict-24mo / 36mo / all-time* | 254 / 301 / 353 | *25 / 37 / 71* | | | |

- **(i) per-cell 36mo is the dominant lever:** +10 reliable over production, 27 cells move up a tier,
  0 regress, exactly 12 reliable-only-via-36mo (anchor-exact).
- **(iii) A16 alias-merge is minor: +1 reliable.** Only 14/109 areas merge; thinness is mostly REAL
  scarcity, not name-fragmentation. (It is, however, the only Marikh lever — see D.)
- 24mo bands: of 254 cells, **229 thin** (32 @10-19, 43 @5-9, 154 @<5).

**Staleness (positive = recent window richer → widening biases DOWNWARD):** 400-600 +7.3%/+4.9%;
600-900 +11.1%/+6.2%; 1500+ +14.4%/+5.1%; 900-1500 +0.3%/+0.3% (24-vs-all-time / 36-vs-all-time).
**36mo captures ~half-to-two-thirds of the drift** (recon F confirmed). The **12 cells rescued by 36mo
move ~0.0% on the total-price headline median** (p25 −6.9%, worst العب −21.1%); ppf −4.9% median.
**Cap at 36mo supported:** 36→all-time adds 3-4× rows but keeps ~5% downward drift per leg (no plateau).

## C. Shrinkage simulation (self-run M2; the workflow's M2 agent failed to emit structured output)
229 thin cells (1≤n24<20). `blended = w·m24 + (1−w)·prior`, `w = n24/(n24+k)`.
- **P2 (prior = same cell's own 36mo): gentle** — median |move| **0.0%**, p75 2.6–4.4%, only 40–55/229
  cells move >5%. A *continuous* form of the per-cell 36mo fallback (no n=20 cliff). = the kickoff's
  "36mo-cap + light shrinkage."
- **P1 (prior = area all-bracket): measured-BAD** — median |move| 7–18%; **size-confounded** (inflates
  Abu Hamour +8% on total, crushes Marikh 600-900 −20%). **DROPPED.**
- Reference cells (k=10, P2): Abu Hamour 400-600 n24=28 → 2,365,000 → **2,368,947 (+0.17%)**;
  Marikh aliases 600-900 n24=13 → 5,100,000 → **5,100,000 (0%, m36≈m24)**.

## D. Gate-2 determination + reference-PIN expectations
- Any value-moving lever (per-cell 36mo / shrinkage / alias-merge) is **Hard Gate 2** — it changes the
  comp pool → the bracket TOTAL-PRICE median and/or the Case selected.
- The one presentation-only lever is extending the a10 honest-range to thin bracket cells (E23) —
  same pool, same median; deferred as a fast-follow.
- **Abu Hamour 56/565/21** → 400-600 n24=28 reliable → UNCHANGED, stays **2.4M**.
- **Marikh 54/541/6** → offline exact `مريخ` 400-600 n=23 + 600-900 n=13 (production fixed brackets
  split its plot); live `bracket_n~1` is the **A16 area-name resolution gap** → geo-routed, **NOT on
  the bracket-shrink path** → UNCHANGED ≈ 4.5M. Only the A16 lever moves Marikh (needs a live trace).
- **55/296/13** (`comparison_thin n=8`) = the EFFECT case (gentle move toward its own 36mo; upgrades
  tier iff its 36mo n≥20 — measured in Phase-2 verification).
- **52/903/90** apartment → `moj_cat=None` → unchanged refusal.

## Workflow note (Rule #36 / #59)
4-agent read-only workflow (`wf_81e21f2b-8e0`, ~655k subagent tokens). M1 (bracket+A16) and M3
(staleness) reconciled to anchors exactly; M2 (shrinkage) failed to emit StructuredOutput → **re-run
by hand** (numbers above are mine, not an agent's). Prevention: simpler measure-agent schemas / split
heavy agents.

*Authored 2026-06-01 (Phase-1 close). Supersedes the Claude.ai v4 brief draft's prior-design section.*
