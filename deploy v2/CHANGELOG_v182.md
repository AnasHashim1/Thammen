# CHANGELOG v182 — Sprint 2.22.0b.101 «نقاء استخدام الأرض» (land-pool residential-usage purity)

**Engine:** `thammen-sprint2p22p0b101-land-usage-purity` · **SPRINT_TAG** `2.22.0b.101` · api-health `3.1.0-sprint2.22.0b.101`
**Date:** 2026-07-05 · **Files:** `moj_reference.py` (land filter + 36mo total-price quartiles) · `geo_reference_v2.py` (land filter — display grid) · `evaluate_property.py` (`apply_moj_strategy` land 36mo-window companion) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b101_land_usage.py` (new) · `docs/PHASE0_land_usage_purity.md`
**Class:** 🔴 **Gate-2 VALUE-AFFECTING (land comparable-pool only)** — Gate-2 **SIGNED BY DELEGATION** (PO «مع ما تراه الأصوب», 2026-07-05, after the recon flagged the الوعب down-move). **`api.py` + `index.html` UNTOUCHED → R14 N/A by construction** (backend-only; the b59/a11 precedent). **Gate-1 (deploy) HELD** for explicit go. The direct LAND sibling of Sprint 2.22.0a.11 (A1, which was villa-only).

## 1. Why this matters — the land pool had no usage filter (PO-surfaced)
PO «انظر الاستعمالات واسعارها في الوعب — بناءً عليه يرتفع السعر أو يقلّ». **Usage IS a ~2× price driver** (Al-Waab MoJ, per `الاستخدام`: commercial land 12–18k/m² · apartment/complex ~9.5k · residential villa/house ~7.2k). A1 (Sprint 2.22.0a.11) cleaned the **villa** pool of non-residential rows (which price ~+101%) but its docstring left **land out of scope** — so `moj_reference.build_reference` filtered `_is_residential_usage` for `cat=='villa'` only (`cat != 'villa' or _is_residential_usage(r)` → the `or` short-circuits for land). A residential land valuation therefore mixed residential land + apartment/complex + commercial land. The engine only DODGED the contamination via the 24mo recency window (fragile), flagging it honest-thin — not a usage guard.

## 2. What this patch does
- **Land pool now residential-filtered** (the A1 filter extended to LAND): `moj_reference.build_reference` (both the 24mo + 36mo comprehensions) → `and _is_residential_usage(r)` for **both** cats (villa expression is IDENTICAL to before — `cat=='villa'` already reduced to `_is_residential_usage(r)`); `geo_reference_v2` line 348 → `category in ('villa','land')` (the display comparable-grid). Keeps residential + blank (**blank ≈ residential globally, measured: both 3,014/m²**); drops apartment/complex + commercial + farm/office/school land.
- **Companion — thin filtered LAND bracket → its own 36-month window** (`apply_moj_strategy`): the filter can thin a premium land bracket in the recent 24mo window; when the (24mo) bracket is thin (n<10) and its 36mo pool has more, use the bracket's **36mo residential total-price median + quartiles** (already computed by build_reference; +2 fields `total_price_p25_36/p75_36` so the RANGE stays 36mo-consistent → no inversion). **CAPPED at 36mo** — all-time re-admits the high-priced blank/development land in premium areas (measured Al-Waab 900-1500 residential: 24mo n=4 ~5.3M · **36mo n=7 ~6.5M** · all-time n=50 ~11M). Never mutates the shared bracket dict.

## 3. Value effect (measured, real production functions)
- **Villa: byte-identical BY CONSTRUCTION** — the villa filter expression is unchanged (`cat=='villa'` already meant `_is_residential_usage(r)`). Test-verified (بو هامور villa median 5,333 == manual residential-filtered). The 5-fixture villa/apt byte-gate is untouched.
- **Land: SURGICAL de-inflation** — ~6% of served land cells move (recon `PHASE0_land_usage_purity.md` §4), ~all downward, concentrated in large-plot brackets of premium areas (Al-Waab/Lusail/Al-Kharayej). Small residential brackets (400-900) + areas with no non-residential land = unchanged.
- **The Al-Waab anchor (PIN 55010236, 1,219 m²): live pre-patch 7,100,000 (mixed) → 6,700,000 (residential 36mo, n=7, indicative), range [5.33M–12.45M], honest-thin flag, no inversion, no refusal.** A −6% honest correction toward residential-only comps (the mixed pool had lifted it ~9% above pure-residential MoJ).

## 4. Verification — empirical
- **Isolated `test_sprint_2_22_0b101_land_usage.py` 18/18** (E14, real build_reference + apply_moj_strategy): the `_is_residential_usage` land partition; land pool residential-filtered (Al-Waab residential 4,643 < mixed 8,205); **villa byte-identical by construction** (production villa median == manual residential-filtered); companion fires (36mo widen note) + value not refused + residential band + **range NOT inverted**; 0 new refusals / 20 cells.
- **DoD:** aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · **broad walk 157/157 ALL GREEN** (156→157; **ZERO re-points** — no existing land test hard-pinned a moved premium value). py_compile OK.
- **R14 N/A by construction** (`api.py` + `index.html` git-confirmed UNTOUCHED; served HTML renders identically).
- **Local E2E:** villa control byte-identical · control land (الوكير) unchanged · 0 new refusals / 28 cells · no range inversion.

## 5. Deployment (HELD — Gate-1 needs explicit go)
`git push origin master` (backup FIRST) → `git subtree push --prefix "deploy v2" heroku master` (Rule #43; backgrounded). **NOT executed** — awaiting the PO's deploy go.

## 6. Verification curl (post-deploy)
`/api/health` → engine b101. `POST /api/evaluate {"pin":"55010236"}` → amount ≈ **6,700,000** (was 7,100,000), method `comparison_thin`, source «وُسِّعت الشريحة إلى نافذة 36 شهراً». **Villa 5-fixture value byte-gate byte-identical to v272** (54/541/6 2.4M · 56/647/6 3.8M · 55/296/13 2.6M · 56/565/21 2.4M · 52/903/90 refusal). A control land area with no non-residential land = unchanged.

## 7. What's NOT in this patch
- **Subject-side usage disclosure** (a residential land subject in a premium area could disclose the residential-vs-development spread) — deferred, out of scope.
- **Path A** (condition→stratum market-stratum lead) — the parallel, **GT-gated** candidate (indicative at n=11), unchanged.
- The wide honest range on very-thin premium land (Al-Waab high 12.45M = the 36mo residential p75, n=7) is by design (honest dispersion, indicative-flagged); a tighter treatment is a future option, not this fix.
