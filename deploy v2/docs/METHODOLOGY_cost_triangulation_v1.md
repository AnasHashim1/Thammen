# Methodology Design Record — Cost-Triangulation Track (v1)

**Date:** 2026-05-31 · **Status:** Direction approved (PO); pending parameter decisions + empirical calibration · **Author lane:** Claude.ai (analyst) · **Validation:** Multi-AI (GPT + Gemini), Rule #54

> Single source of truth for the methodology track addressing **R7 (built-type/condition blindness)**. Read before any cost-approach or stratification implementation. Supersedes ad-hoc notes; parameters in §8 are PO decisions.

---

## 1. Problem (R7)

The engine's market-comparison method returns a pool central-tendency (weighted median over size-bracket × area × 24mo) that is **blind to where the subject sits inside the comparable distribution** — blind to built-type, condition, finish, and built-up area (BUA). The error is **bidirectional**:

- **Over-anchors** below-average subjects. Evidence: **54/541/6 Marikh** — plain 2-story+annex, ordinary finish, ~20yr — valued at the penthouse-tier median (682/ft² ≈ 4.5M); defensible ≈ 3.0–3.4M.
- **Under-anchors** above-average subjects. Evidence: **56/565/21 Abu Hamour** — excellent G+1, secure govt lease — valued ≈ 2.5M; defensible ≈ 2.5–2.8M.

**Root cause:** MoJ records plot area + price + a built-type label, but **NO BUA, condition, or finish**. Market comparison needs a field shared by subject and comparables; built-type IS shared, but condition and BUA are not. (Shipped mitigation: Sprint 2.22.0a.10 Stage-1 honest range — dispersion gate, indicative range when the pool is wide. This is the *real* fix.)

---

## 2. Solution — Triangulation (market primary + cost secondary-independent)

- **Market Comparison = PRIMARY.** RICS-preferred for actively-traded assets; Qatar villas trade actively. Refined with built-type stratification + credibility shrinkage (§4).
- **Income = for let assets** (existing, unchanged).
- **Cost Approach (DRC) = SECONDARY, INDEPENDENT valuation approach** — NOT a mere "cross-check". Per GPT, a legitimate secondary approach contributing **independent evidence**. It observes the variables the market method is blind to (BUA, finish, effective age) via **subject-intrinsic** data — so it needs **no comparables' BUA** (which don't exist). This is precisely why it escapes the BUA dead-end.
- **Reconciliation — NOT blending.** Present: Market figure + Cost figure + diagnostic spread + interpretation + a reconciled RANGE. Convergence → higher confidence; material divergence → flag subject as atypical, widen the range, route to manual review. **Never silently average two divergent methods.**
- **No hard valuation ceiling.** District P95 = a soft warning / confidence-reduction / review trigger, **not** an absolute cap (a hard cap would suppress genuine market value; triangulation handles outliers). [Resolves GPT↔Gemini divergence — §7.]

---

## 3. Cost Approach (DRC) design — post multi-AI

**Structure:** `Value ≈ Land + Depreciated Building` (reconciled to market via a segment relationship, §3.1).

- **Land:** from MoJ market land prices, as a **SURFACE** — NOT a single district average. Beware contamination: teardown transactions (implicit demolition cost) and unrecorded zoning premiums. A flawed land input collapses the entire DRC stack.
- **Building:** subject `BUA × construction-cost-per-m²`. Qatar build costs (PO domain figures — pending documented source + annual review): ordinary villa ≈ **2,000–2,500 QAR/m²**; high-spec/luxury ≈ **3,500–4,000** (≈3,500 typical).
- **Depreciation:** **market-derived, effective-age** (not chronological). The Qatar **10-Year Rule is an EMERGENT pattern, not a governing axiom** — it already *is* ratio-triggered (the `land_priced` stratum, transaction ratio < 1.15, i.e. the market itself shows the building adds little), which satisfies the RICS "market support" requirement. Do **NOT** impose a flat `Age>10 ⇒ building=0` gate. Add a **functional-obsolescence input** (modern vs traditional layout) to adjust effective age beyond physical/chronological age.

### 3.1 CRITICAL — calibration discipline (both AIs flagged this independently)

**Do NOT calibrate the cost model so that "average villas reproduce the MoJ median."** Two distinct failure mechanisms:

- **(GPT)** It kills the cost method's **independence** — trains it to mimic the market model → no diagnostic power ("market + market-mimic").
- **(Gemini)** It **imports the blindness** — if a district's MoJ transactions skew to luxury builds recorded only as plot size, the median is high; calibrating "average" cost to it inflates baseline costs.

**Instead:**
1. Build DRC as a **pure physical estimate** (RCN − market-derived depreciation), independent of the market median.
2. **Separately** observe the **Market/DRC ratio BY SEGMENT** (district, age, prestige). The premium is **not a single global factor** — it varies, and can be **negative** (economic obsolescence in a sluggish market); tie it to market-velocity indicators. Cost-route market value = `DRC × segment Market/DRC ratio`.
3. The subject's deviation from the segment-typical Market/DRC ratio is the **diagnostic**.
4. Any calibration uses an **isolated, curated ground-truth dataset** (known BUA, age, finish), **never** the raw MoJ median. → **Open decision #4: source of this ground-truth sample.** (Cost-approach implementation is BLOCKED until resolved.)

---

## 4. Market stratification design — validated empirically 2026-05-31

Built-type stratification is a **second dimension on top of size brackets** (applied within-bracket, within-district). Magnitudes are district-specific; the tier structure is universal.

**Validated strata** (indicative test, 18,631 MoJ villa transactions, 2020–2025):

| Stratum | Status | Treatment |
|---|---|---|
| **LAND** (أرض فضاء) | Distinct floor | Floor reference |
| **HOUSE** (بيت / مسكن / شعبي) | Distinct, ~15–25% below villa; noisier | Lower tier + shrinkage |
| **STANDALONE VILLA** (فيلا + 2-story + annex/majlis **MERGED**) | Main tier | The big merge — validated |
| **PENTHOUSE** (بنت هاوس) | Distinct but **very thin** (n=76 total; most districts 0–6) | Heavy shrinkage / cost-approach territory |
| **COMPOUND** (multi-villa) | Separate | Excluded for now |
| Palace, other | Excluded | Too few / heterogeneous |

**Evidence:**
- Built-type effect within plot brackets: **Kruskal-Wallis p ≈ 7e-29** (400–600 m²), **2e-69** (600–900 m²) — highly significant.
- "فيلا" (basic) vs "فيلا من طابقين+ملحق" (2-story) **NOT economically distinct**: Mann-Whitney non-significant in **3 of 4 brackets**; the one significant bracket (400–600, +7.7%) is in the **counterintuitive direction** (basic higher) = residual plot-size confound → **MERGE** into "standalone villa".
- Tier ladder **land < villa persists in 8 of 8** top districts.
- **Raw built-type medians are confounded by plot size** (basic villa appeared > 2-story overall purely from plot-size mix) → stratification **MUST** be within size brackets.

**Credibility weighting:** continuous **w = n/(n+k)** (NOT discrete zones — avoids the cliff effect). Stratify when same-stratum n is adequate; shrink toward the broader pool as n thins; fall back to the broad pool + Stage-1 honest range (a10, shipped) when too thin. Most district × stratum × bracket cells are thin (especially penthouse) → shrinkage is essential, not optional. → **Open decision #1: k.**

> **Caveat:** indicative result (raw MoJ, not the engine pipeline). **CC must re-run authoritatively** with engine normalization (NBSP, spatial `Districts/MapServer` matching, مريخ alias A16) for final magnitudes + strata. Direction (merge / ladder / penthouse-thinness) is robust and unlikely to flip.

---

## 5. Confidence, disclosure & governance (RICS)

- User-reported inputs (built-type, condition, age, BUA) are **assumptions** until broker (Stage 4) / valuer (Stage 5) verified → **disclose explicitly**; output is "indicative based on assumed characteristics". (VPS 2 / IVS 102.)
- **Confidence DECLINES** as reliance on unverified inputs increases.
- **Material valuation uncertainty (VPGA 10)** requires SPECIFIC explanatory commentary (e.g. "confidence reduced because only heterogeneous evidence is available and subject characteristics remain unverified") — NOT a generic wide range.
- **Model governance (VPS 5 / IVS 105):** back-testing, validation, monitoring, override policy, the calibration-dataset discipline (§3.1). AVM output is a "written valuation" only with valuer professional judgement → **Stage-5 sign-off**.
- **Restrict to advisory/indicative use**; not for lending / third-party reliance until verified.

---

## 6. Verified RICS / IVS citations (from source, 2026-05-31)

**RICS Red Book Global Standards (effective 31 Jan 2025):**
- VPS 1 Terms of engagement · **VPS 2 Bases of value, assumptions & special assumptions** (was VPS 4) · **VPS 3 Valuation approaches & methods** (was VPS 5) · VPS 4 Inspections, investigations & records (was VPS 2) · **VPS 5 Valuation models (NEW)** · VPS 6 Valuation reports (was VPS 3) · VPGA 10 Material valuation uncertainty · VPGA 11 Relationship with auditors (new).

**IVS (effective 31 Jan 2025):**
- IVS 102 Bases of Value · **IVS 103 Valuation Approaches** (was IVS 105) · **IVS 104 Data and Inputs (NEW)** · **IVS 105 Valuation Models (NEW)** · IVS 106 Documentation and Reporting · IVS 400 Real Property Interests.

> **Correction:** earlier internal citations of "VPS 4 / VPS 5" for bases/approaches reflected the OLD (pre-2025) numbering. Use the above. Bases = VPS 2 / IVS 102; Approaches = VPS 3 / IVS 103; Models = VPS 5 / IVS 105.

---

## 7. Multi-AI validation summary (Rule #54)

- **GPT:** soundness 8.5/10, RICS alignment 8/10, improvement-over-current 9/10.
- **Both GPT and Gemini endorsed:** market-primary + cost-secondary; the triangulation / blindness-detector framing as the strongest element; do not blend divergent methods.
- **Both independently flagged the calibration trap** (§3.1) — high-confidence correction (it overturned the analyst's original calibration plan).
- **Divergence:** the district-P95 ceiling — GPT against a hard cap, Gemini for it. Resolved → soft trigger (§2).
- The empirical stratification test (§4) was run **after** AI validation and confirmed the "merge non-distinct categories" guidance both AIs gave.

---

## 8. Open decisions (PO / Anas)

1. **k** for the credibility weight w = n/(n+k).
2. **Condition** bands + caps (discrete, evidence-based, ≤ a bounded share of net adjustment) + documented evidence basis (paired-sales or cost-to-cure) + annual review.
3. **Cost-approach parameters:** construction-cost source + review cadence; depreciation-curve shape; the Market/DRC segment-ratio method.
4. **Curated ground-truth calibration sample** — the critical prerequisite for the cost track. Source TBD (the data-building question). **Cost-approach implementation is BLOCKED until resolved.**
5. **Role:** market primary + cost secondary-independent — confirmed by both AIs; PO agreed.

---

## 9. Sequencing

**Shared foundation:** Stage-2 elicitation (built-type, condition, age, BUA, floors, layout toggle) = **2.22.0b** — built first; feeds BOTH tracks.

Then: **(A)** market stratification track (CC authoritative re-run of §4 → implement strata × shrinkage); **(B)** cost track (after #4: back-test / calibrate on the curated sample).

Empirical first step **done**: indicative stratification test (§4). **Next:** CC authoritative re-run + PO parameter decisions (§8).
