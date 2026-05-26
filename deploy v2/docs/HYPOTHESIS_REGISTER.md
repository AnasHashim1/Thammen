# Hypothesis Register — Pre-Rule Empirical Observations

> **Purpose:** record observations with n=1 (or sub-threshold) evidence that *could* become Empirical_Findings Rules or Operational_Rules, but have not yet passed the sample-size gate required for promotion.
>
> **Promotion gate** (per Project_Instructions §3 sample-size discipline + §10.3 honesty + §16 audience calibration): a hypothesis becomes a Rule only after a structured audit with **n ≥ 10 verified cases** (n ≥ 20 if the claim is quantitative — false-positive rates, premium magnitudes, lifecycle durations). Until then, the hypothesis is **descriptive, not prescriptive** — it informs design exploration but never drives a production code path.
>
> **Status semantics:**
> - `n=1 (anecdotal)` — single case observed, mechanism plausible but unvalidated
> - `n=2-9 (sub-threshold)` — pattern emerging, still insufficient for promotion
> - `n≥10 audit pending` — sample size adequate, audit script not yet executed
> - `n≥10 audit complete, REFUTED` — hypothesis tested and falsified; kept as a negative result
> - `PROMOTED → Rule E<N> | #<N>` — passed gate, moved to canonical doc
>
> **Anti-pattern this register prevents:** the marathon-2026-05-18 failure mode of treating a single field case as authoritative ("Lusail B201 says X → ship X"). Rule E14 + Operational #33 + #36 all converge on the same discipline: measure before promote.

-----

## H_huzoom_1 — listing-text claims warrant GIS verification before applying premium

**Status:** n=1 (anecdotal)
**First observed:** 2026-05-26, Claude.ai Huzoom Lusail learning session (PIN 69052748)
**Mechanism (hypothesized):** broker listings carry descriptor claims (`corner` / `garden` / `view` / `newly renovated` / `ready to move`) that the AVM may currently take at face value when applying premium adjustments. Verified false-positive rates may be material — if so, the right architectural move is **verify before adjust** (GIS / age-cache / footprint cross-check) rather than trust-and-discount.

**Evidence (single case):**
- PIN **69052748** (Huzoom Lusail). Listing claimed `corner`. GIS verification (CadastrePlots + ROADFlowlnA buffer) showed the parcel is **mid-block** — adjacent to 1 road segment only, no intersection within 5m buffer. False positive confirmed.

**Five descriptors in scope:**
1. `corner` — verifiable via ROADFlowlnA segment count (see Δ2 backlog entry, PHASE3_LOG.md)
2. `garden` — verifiable via footprint-vs-plot ratio (CadastrePlots PDAREA − Building_Footprint area)
3. `view` — partially verifiable (orientation + nearby landmarks); often unfalsifiable in advance
4. `newly renovated` — verifiable via imagery/age-cache (Sprint 2.15.1 cache shows last construction event)
5. `ready to move` — verifiable via QARS BUILDING_NO_SUBTYPE presence + completion certificate where available

**Audit needed to promote:**
- Sample: ≥20 listings drawn across the 5 descriptors (≥4 per descriptor)
- Method: manual GIS verification per claim type using authoritative layer
- Output: per-descriptor false-positive rate + 95% CI; promotion threshold = any descriptor with FP rate ≥10% becomes a verify-before-adjust requirement (engine code path change)
- Owner: TBD methodology research track
- Time-box: ~1-2 weeks of audit work; ~8-12 listings/day verifiable at GIS-query rate

**What this hypothesis would gate (if promoted):**
- Stage 2 Q&A flow (BRIEF v3.1 D-stage2-1 fields 4 = primary view): if H_huzoom_1 promotes, the "view" Q&A answer would NOT directly apply a premium — instead it would set a flag that triggers a GIS verification step before the adjustment fires.
- Adjustment ledger entries currently take user/listing claims at face value (per BRIEF v3.1 §1 D-stage2-7 bounded caps). H_huzoom_1 promoted would add a verify-or-cap-at-zero rule for the 5 descriptors.

**Why not Rule status yet:** **n=1** — a single corner-claim false positive is suggestive, not measured. Promotion before audit would violate Operational #36 (observed-vs-expected reporting) and Rule E14 (validation must exercise production logic, not echo input).

-----

## H_huzoom_2 — sovereign-backed freehold projects pass through 4 lifecycle stages, each requiring different reference-selection logic

**Status:** n=1 (anecdotal)
**First observed:** 2026-05-26, Claude.ai Huzoom Lusail learning session
**Mechanism (hypothesized):** sovereign-developer freehold projects (Qatari Diar, UDC, Qetaifan Projects, Msheireb Properties, etc.) follow a predictable 4-stage lifecycle that the AVM should distinguish, because the right reference-source differs by stage:

| Stage | Description | Active reference | Inactive reference |
|---|---|---|---|
| **A — Primary active** | Developer still selling launch inventory | Developer pricelist (T3 hybrid) | MoJ comps thin/absent |
| **B — Primary cleared** | Developer launch inventory exhausted; no resale yet | Developer historical clearing price (T3 stale) | MoJ comps still thin |
| **C — Active secondary speculation** | Brokerage listings begin appearing; few transactions yet | T2 listings tier-weighted, with stale-T3 floor | MoJ comps emerging but n<10 |
| **D — Mature secondary** | Resale market established | MoJ comps T1 dominant | T2/T3 discount factors apply per Rule E3 |

**Evidence (single case):**
- Huzoom Lusail observed in **Stage C** (sovereign-backed freehold by Qatari Diar; primary clearing complete; active brokerage listings; sparse MoJ secondary transactions).

**Audit needed to promote:**
- Sample: ≥5 sovereign-backed freehold projects with traceable lifecycles
  - Qetaifan Island North + Island South (Qetaifan Projects)
  - The Pearl phases (Porto Arabia, Qanat Quartier, Viva Bahriya, Floresta, Marsa Malaz, Abraj Quartier)
  - Msheireb Downtown districts (Msheireb Properties)
  - Huzoom Lusail (Qatari Diar)
  - Lusail Marina District (Qatari Diar / UDC joint)
- Method: per-project — date of first sale, date of primary cleared, date of first secondary listing, date of first MoJ secondary transaction, current stage
- Output: validation that the 4-stage framework generalizes; per-stage reference-selection rules
- Owner: TBD methodology research track
- Time-box: 2-3 weeks (requires historical sales data, developer announcements, regulatory filings)

**What this hypothesis would gate (if promoted):**
- Hybrid valuation logic (`hybrid_valuation.py` + Sprint 2.21.3+2.21.4 path) currently treats T2/T3 weights as static (0.40/0.15 caps per Rule E3). H_huzoom_2 promoted would add a **lifecycle stage** dimension: project-level metadata determines which tier gets weight floor/ceiling.
- Developer inventory loader (Sprint 2.21.4 `developer_inventory.sqlite`) would gain a `stage` column.
- Stage detection itself would need a separate ruleset: how does the engine know if a project is in Stage A vs C? (Possible signals: MoJ transaction count, developer-announced clearing date, broker listing density.)

**Why not Rule status yet:** **n=1** — Huzoom Lusail is the trigger case. The 4-stage framework is a *plausible generalization* but has not been traced across other sovereign projects. Promoting before tracing Pearl/Qetaifan/Msheireb would risk overfitting to Huzoom's specific dynamics.

-----

## H_huzoom_3 — broker listings below developer clearing price (post-primary-cleared) skew toward stale / bait / distressed

**Status:** n=1 (anecdotal)
**First observed:** 2026-05-26, Claude.ai Huzoom Lusail learning session
**Mechanism (hypothesized):** once a sovereign developer completes primary clearing (Stage B → C transition per H_huzoom_2), broker listings *below* the historical clearing price are statistically rare in legitimate inventory — most below-clearing listings are stale data, bait-and-switch tactics, or genuinely distressed sales (motivated seller, divorce, debt). If true, this means the AVM should *down-weight* below-clearing listings in the T2 median rather than treat them as honest market signal.

**Evidence (single case):**
- Listing **LS-000221-5161** (Huzoom Lusail, broker source) at **1.79 M QAR**, vs Qatari Diar historical clearing price ~2.0 M QAR for comparable unit. ~10.5% below clearing.
- One anomaly. Outcome (sold? withdrawn? renegotiated up?) unknown — would need outcome tracking to confirm hypothesis.

**Audit needed to promote:**
- Sample: ≥10 below-clearing-price listings identified across ≥3 sovereign-backed freehold projects (Pearl, Lusail, Qetaifan) over 3-6 months
- Method: snapshot listing at observation date; track every 2 weeks via re-fetch; classify final outcome — `withdrawn` / `sold_at_listing` / `sold_above_listing` / `sold_below_listing` / `still_active_>90_days` / `price_raised` / `price_lowered`
- Output: per-outcome distribution; if `sold_below_listing` + `still_active_>90_days` + `withdrawn` together exceed 70%, hypothesis promotes (stale/bait/distressed dominates)
- Owner: TBD methodology research track
- Time-box: 3-6 months observation window (intentionally long — outcome data needs time to accumulate)

**What this hypothesis would gate (if promoted):**
- Hybrid T2 connector (`connectors/propertyfinder_apartments_t2_sales.py` and friends) currently treats all in-bracket listings equally before median aggregation. H_huzoom_3 promoted would add a **below-clearing filter** as either (a) exclusion or (b) reduced weight (e.g., 0.3× instead of 1.0×) for listings below the project's documented clearing price.
- Requires a project-level `clearing_price_qar_per_m2` field in the developer inventory or a new metadata source.
- Note this hypothesis is **dependent on H_huzoom_2** — without a way to identify "post-Stage-B" projects, the "below clearing" concept is ill-defined.

**Why not Rule status yet:** **n=1 outcome unknown** — the listing was *observed* below clearing, but we don't know if it sold at that price, was withdrawn, or was a bait listing. Without outcome data, the mechanism is speculation. Outcome tracking requires patience (months, not days).

-----

## How to add a new hypothesis

1. Pick a hypothesis ID: `H_<topic>_<n>` where topic is a short noun (huzoom, density, stratification, etc.) and n is the next available integer for that topic.
2. Fill in: First observed (date + source session) · Mechanism (plain language, ≤3 sentences) · Evidence (every observed case with PIN/address/timestamp) · Audit needed (sample size + method + output + owner + time-box) · What this hypothesis would gate (concrete code path or doc impact if promoted)
3. Status starts as `n=1 (anecdotal)` unless multiple cases already observed.
4. Do not assign engineering work to the hypothesis directly. If a methodology change is needed before the audit runs, that's a **separate decision** filed in `PHASE3_LOG.md` (current sprint) or as a backlog entry in `Project_Instructions.md §11 Deferred Sprints` — NOT in this register.

## Review cadence

- **Per Sprint kickoff:** review register for hypotheses ready to audit (sample size now adequate, or audit owner free)
- **Quarterly:** prune n=1 hypotheses that have been static for >6 months without new evidence (move to `H_archive_<topic>_<n>` with REFUTED-by-silence note)
- **On rule promotion:** move the hypothesis section to `Empirical_Findings.md` (or `Operational_Rules.md` for procedural rules) under its new E#/#-number, leaving a short stub here pointing to the promoted location

-----

*Created 2026-05-26 as docs-only housekeeping during Phase 3 kickoff of Sprint 2.22.0. Source: Claude.ai Huzoom Lusail learning session. Three n=1 hypotheses logged for future audit; none gate any 2.22.0 code path.*
