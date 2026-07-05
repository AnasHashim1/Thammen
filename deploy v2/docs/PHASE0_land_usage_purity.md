# PHASE-0 RECON — Land-pool residential-usage purity ("A1 for land")

**Date:** 2026-07-05 · **Live:** b100 / Heroku v272 · **Class:** 🔴 Gate-2 VALUE-AFFECTING (land comparable-pool selection) — **NOT YET SIGNED / NOT BUILT.** This is the read-only Phase-0 basis.
**Trigger:** PO «انظر الاستعمالات واسعارها في الوعب — لأن بناءً عليه يرتفع السعر أو يقلّ» (2026-07-03/05), during the recon-first session. The Al-Waab measurement re-surfaced the **deferred A1-land companion** (Sprint 2.22.0a.11 `usage_filter.py` docstring: *"Applies to the VILLA pool ONLY; land-usage filtering is out of A1 scope."*).

---

## 1. The gap (confirmed by code + live)

- **Usage IS a major price driver.** Al-Waab MoJ, per `الاستخدام` (n=308, all types): commercial multi-use land **12,500–18,500**/m² · apartment/complex land **~9,556** · residential villa/house land **~7,156** (blank all-time ~9,688). Commercial ≈ 2.5× residential; apt/complex ≈ 1.3×.
- **The engine cleans the VILLA pool (A1) but NOT the LAND pool.** `moj_reference.build_reference` filters `_is_residential_usage(r)` only for `cat=='villa'` (moj_reference.py:149,153: `cat != 'villa' or _is_residential_usage(r)` → for land the `or` short-circuits → **no usage filter**). The land bracketed pool that `apply_moj_strategy` reads (`categories['land']['size_brackets'][…]`) therefore mixes residential land + apartment/complex + commercial land.
- **In Al-Waab, A1 is a no-op** (all 33 villa-TYPE rows are already residential-usage; villa median 6,401 with/without the filter). The contamination lives entirely in the **LAND type**, which A1 never touches.

## 2. Reconciliation — the engine currently DODGES it (fragile), not guards it

Live measure, PIN 55010236 (الوعب, 1,219 m², raw_land): **amount 7,100,000 · method `comparison_thin` · n=8 · «عينة ضعيفة جداً — تقديراً مبدئياً»** → ~5,824/m². The PO confirmed ~7M is approximately right (§20.117).

- The engine's land pool = `build_reference` land category → **24-month window** → plot bracket (`_bracket_for_area(1219)` → 900-1500) → n=8.
- The **all-time** 900-1500 Al-Waab land pool = 9,420/m² (contaminated); the **24mo** pool = ~5,824 (n=8) — the recent 8 sales happened to be residential. **The engine avoided the contamination by RECENCY (the 24mo window), not by a usage guard.** On a subject/window whose thin pool catches apt/commercial land, it would over-value. The honest thin-flag is doing real work; it is not a robust guard.

## 3. The «blank» decision — MOOT in practice (measured)

A1 keeps blank-usage («blank prices like residential +5%»). The worry: in Al-Waab all-time, blank land priced like development (~10,054). **But in the 24-month window the engine actually uses, blank land is n=3 globally** (RES n=3,235 / NONRES n=155). Per-area (24mo), blank is absent or n=1 (and where present, `BLANK~RES`). **⟹ keep blank (A1-consistent); the filter targets the labelled NON-residential usages only** (apartment/complex + commercial land). P1 (drop NONRES, keep blank) ≈ P2 (drop blank too) in the blast radius below.

## 4. Blast radius — SURGICAL (faithful production-pool replication, E14)

Replicated `build_reference`'s land pool (built_type==LAND · 24mo window w/ 36mo fallback on category n<MIN_N=20 · SIZE_BRACKETS), 3 usage policies, over **156 served (area,bracket) land cells (P0 pool n≥5)**:

| policy | moved ≥5% | ≥10% | P<P0 (de-inflated) | thinned-out |
|---|---|---|---|---|
| **P1** (drop NON-res, keep blank) | **9 (6%)** | 8 | 14 | 5 |
| P2 (RES only, drop blank too) | 11 (7%) | 10 | 17 | 6 |

**Almost all movement is DOWNWARD (de-inflation), concentrated in large-plot brackets of premium areas.** Biggest P1 movers:

| area | bracket | P0 (mixed) | P1 (residential) | Δ | n |
|---|---|---|---|---|---|
| الخرايج | 1500+ | 3,608 | 807 | −78% | 11→3 |
| **الوعب** | 1500+ | 9,308 | 4,643 | −50% | 30→3 |
| لوسيل | 1500+ | 2,430 | 1,588 | −35% | 20→10 |
| **الوعب** | 900-1500 | 6,484 | 4,634 | −29% | 8→4 |
| المطار العتيق | 400-600 | 4,895 | 3,878 | −21% | 18→10 |

Small residential brackets (400-900) are already clean → unaffected. The fix is the **direct land sibling of Sprint 2.22.0a.11 (A1)** — same class (remove non-residential contamination from a same-type comparable pool), RICS like-for-like (Rule E3 #7).

## 5. 🟡 The honest tradeoff (must be in the brief)

1. **Thinning.** The fix collapses premium large-plot pools (الوعب 900-1500 n=8→4; 1500+ n=30→3). `build_reference`'s 24/36mo fallback is chosen on the **category** total (all land in the area), NOT the bracket — so after filtering, the category may stay ≥MIN_N (24mo) while the filtered **bracket** goes thin and is NOT auto-rescued. **Companion required:** widen the window (36mo / all-time) for the filtered land pool, or route to the honest-thin range. Without it the fix trades contamination for refusals in premium areas.
2. **It moves the PO's own confirmed case DOWN.** Al-Waab 1,219 m²: current 7.1M (mixed, PO-confirmed) → residential-only ≈ **5.6–6.5M** (24mo-thin 4,634 → 5.65M; all-time RES 5,330 n=26 → 6.5M). Reading: the mixed pool lifted the number ~5–14% above pure-residential MoJ. Residential-honest Al-Waab land ≈ **5,300–5,800/m²**. This is *more* correct, but it is a **downward move on a case the PO reads as ~right** → he must confirm the Al-Waab residential read (~5,300) before this ships.

## 6. Proposed design (for the eventual signed build — NOT built)

- **Filter site (one place):** extend `moj_reference.build_reference` line 149/153 so the `use` comprehension applies a **land-appropriate residential-usage filter** to `cat=='land'` too: keep `{فلل او بيوت سكنية, مسكن, مساكن كبار الموظفين}` + **blank**, drop `{عمارات أو مجمعات سكنية, اراض/أراضي تجارية…}` (and spelling variants — reuse the `usage_filter` whitelist approach). Also mirror in `geo_reference_v2` if the land path can reach the geo pool (villa filter is at geo_reference_v2.py:348).
- **Companion (mandatory, per §5.1):** for the filtered LAND category, choose the 24/36mo window on the **post-filter bracket** availability (or force 36mo/all-time when the filtered bracket < MIN_N), so premium large-plot areas keep usable n; otherwise surface the existing honest-thin range. Keep the b100 honest-floor discipline.
- **Value-invariant elsewhere:** small residential brackets + areas with no NONRES land are byte-identical (measured: 147/156 cells unchanged).
- **Scope discipline (#38):** VILLA pool + subject-side gate (RULEID/E7) UNCHANGED; this is land-comp-pool purity only.

## 7. HALT bands for the build (pre-deploy, like a11/a12)

- **Blast radius must match this recon:** ~6% of served land cells move, ~all downward; villa 5-fixture value byte-gate **byte-identical** (villa/apartment/refusal untouched — land-only).
- **No new refusals without honest-thin:** every premium large-plot cell that thins must still return an honest range (not a bare refusal).
- **Al-Waab live E2E:** 55010236 lands in the residential band (≈5.6–6.5M) with an honest-thin flag; no other value anchor moves.

## ✅ BUILT + VERIFIED (2026-07-05, Sprint 2.22.0b.101, CHANGELOG_v182) — Gate-1 deploy HELD

Filter (both sites) + the **36mo companion** shipped as designed. **Al-Waab 55010236: 7.1M (mixed) → 6.7M (residential 36mo, n=7, indicative, no inversion, no refusal), −6%.** Villa byte-identical by construction. Isolated **18/18** · DoD aggregator MATCH / security 16/16 / surface 45/45 / **broad 157/157 ZERO re-points** · R14 N/A (`api.py`+`index.html` untouched). Companion caps at **36mo** (all-time re-admits Al-Waab blank/development land: RES 24mo n=4 ~5.3M · 36mo n=7 ~6.5M · all-time n=50 ~11M). **Deploy awaiting PO go.**

## 8. Recommendation

**Directionally correct + surgical + data-ready (NOT GT-blocked, unlike Path A)** — recommend proceeding to a **signed Gate-2 build WITH the §6 36mo companion + honest-thin**. Two things the PO must weigh first (§5): (a) it moves الوعب-class premium large-plot land **down ~5–14% toward residential-honest** (incl. his own confirmed case), and (b) it needs the window companion or it trades contamination for thin-refusals. If the PO confirms the residential read + accepts the companion, this is a clean, measured, a11-class fix. If he prefers not to move his الوعب case, the alternative is **disclosure-only** (flag "land pool mixes usages" without changing the number) — weaker but zero-downside.

**Deferred / open:** whether to also address the subject-side (a residential land subject in a premium area could disclose the residential-vs-development spread) — out of scope here. The `geo_reference_v2` land reach must be confirmed at build time. Path A (condition→stratum) remains the parallel, GT-gated candidate.
