# Sprint 2.23.x design input — GPT-5 strategic feedback (deferred from 2.22.0a.2)

**Source:** Multi-AI validation runs on
`docs/MULTI_AI_VALIDATION_BATCH_2p22p0a2.md` (Sprint 2.22.0a.2,
2026-05-27). GPT-5 raised five strategic observations beyond the
Pattern-A/B/C-direct scope; Anas's reconciliation marked them
**DEFER to a future 2.23.x design Sprint**.

This file captures GPT-5's verbatim §§4/6/7/10/11 feedback so the
2.23.x BRIEF author has the raw observations on hand. None of the
items are actioned in 2.22.0a.2 — they are explicit design questions
for a separate Sprint cycle.

---

## §4 — RICS citation density

GPT-5 observed that the MUC clause header (`muc_clause_ar` /
`muc_clause_en`) interpolates a dense citation:

> RICS Red Book Global Standards (effective 31 January 2025) — VPGA 10
> (Material Valuation Uncertainty) and VPS 6 (Valuation Reports) — and
> IVS (effective 31 January 2025) — IVS 106 (Documentation and Reporting)

Across **every** valuation report, every refusal screen, every brief
section, and the global MUC banner. **Five+ separate Latin tokens** per
header, repeated at every site where the MUC fires.

GPT-5 observation: "The citation density may overwhelm non-expert readers
and dilute the regulatory-disclosure intent. Consider: a single canonical
short-form citation (e.g., 'وفق معايير RICS/IVS 2025') for inline use,
and a dedicated 'Methodology & Standards' footer page that renders the
full citation chain once per report."

**Design question for 2.23.x:**
- Is the inline-everywhere full-citation pattern serving the user?
- Would a single 'Methodology & Standards' page (linked from every brief)
  reduce visual noise without losing the regulatory disclosure?
- If yes, what is the canonical short-form (and does it satisfy VPGA 10
  §6 + IVS 106 disclosure tests on its own)?

**Why deferred from 2.22.0a.2:**
This is an information-architecture redesign question affecting many
files (every site that interpolates the MUC clause header), and the
right answer depends on a UX research pass that 2.22.0a.2 doesn't have.
Pattern A LRM-wrapping is the immediate correctness fix; full
restructure is a separate Sprint.

---

## §6 — Value decomposition framing

GPT-5 reviewed the value-decomposition surface (the `decomposition` block
that splits a property valuation into `land_value` + `building_value`
implied components, with land confidence label, status flag, and
interpretation prose).

GPT-5 observation: "The decomposition presents two precise numbers
(land_value, building_implied) that are derived by subtraction, not by
direct measurement. The user may read them as 'this house is worth X for
the land, Y for the building' — a precision claim Thammen cannot defend
because BUA is unknown and building condition is uninspected. Consider
reframing the decomposition as a *range plausibility check* rather than
two precise quantities."

**Design question for 2.23.x:**
- Replace the two-number decomposition with a single 'land-vs-built
  plausibility band' indicator?
- Or: surface the land per-m² from MoJ + the BUA assumption + the
  resulting building $/m² so the user sees the chain, not just the
  output?
- Either way: avoid presenting `building_implied` as if it were a
  measured value.

**Why deferred from 2.22.0a.2:**
The current decomposition is correct (Sprint 2.18.1.1 closed the silent
negative-building bug via Patch C). The framing question is a UX shift,
not a correctness fix. Belongs in a UX-redesign Sprint.

---

## §7 — Cap rate for villas (4.0%)

GPT-5 flagged the long-standing villa cap-rate at 4.0% (set in
`hybrid_valuation.HYBRID_TIER_CONFIG` and `evaluate_unified` cap-rate
table) for review.

GPT-5 observation: "A 4.0% gross cap rate for villas is below the global
benchmark band (5-6% net for residential). Thammen's own documentation
(Project_Instructions §3 Net yield benchmarks) cites 5-6% as normal,
>6% as bargain. The 4.0% villa cap was rationalized in Sprint 2.19.1
Fix #3 on grounds that villas are owner-occupied and Income Approach
serves only as a cross-check. But the value is internally inconsistent
with §3, and may surface as a methodological inconsistency in a
brokerage audit."

**Design question for 2.23.x:**
- Is the 4.0% villa cap defensible, or should it be raised toward the
  5-6% net range (which would require also defining service-charge +
  vacancy assumptions for villa-owner self-occupation)?
- Is the right answer to remove Income-Approach calculation for villas
  entirely (relying on MoJ-only for that asset class)?
- If the cap stays at 4.0%, the rationale needs to be documented in
  the user-visible methodology footer (per §4 above).

**Why deferred from 2.22.0a.2:**
This is a methodology question that touches calibration constants and
the cap-rate calibration database. Sprint 2.19 set up the calibration
infrastructure; revising the villa cap requires either new empirical
data or a documented methodology decision. Out of 2.22.0a.2 scope.

---

## §10 — Report length / progressive disclosure

GPT-5 observed the default villa brief renders many sections
simultaneously: MVU banner, methodology, accuracy, stock_strata, sources,
reasoning_trace, geometric_factors, location_features, due_diligence,
disclaimer (and pre-2.22.0a.2 also negotiation, which C5 removed).

GPT-5 observation: "A non-expert user scrolling a one-page report with
all this content may miss the high-importance items (MVU banner,
accuracy tier) buried in the noise of geometric_factors and
reasoning_trace. Consider progressive disclosure: a top-level summary
card (value, range, tier, top 2 red-flag items if any), with sections
expandable on demand for valuer-audience users who need the audit trail."

**Design question for 2.23.x:**
- What's the right disclosure hierarchy for buyer/seller/investor/valuer
  audiences?
- Should each audience see a different *length* of report, or just
  different *sections* of the same content?
- How does this interact with the existing four `_buyer_brief`,
  `_seller_brief`, `_investor_brief`, `_valuer_brief` builders?

**Why deferred from 2.22.0a.2:**
Major UX redesign across `output_briefs.py` (4 builder functions) and
`index.html` (rendering pipeline). Sprint 2.22.0a.2 is a content-fix
Sprint, not a UX-architecture Sprint.

---

## §11 — Three output modes (audience architecture)

GPT-5 noted that the existing 4-audience model (buyer / seller /
investor / valuer) routes through 4 separate brief-builder functions
with overlapping content but different audience-specific framing. The
overlap is high and the differences are sometimes superficial (different
section ordering, slightly different prose).

GPT-5 observation: "Consider collapsing the four audiences to three
output modes:
  - **Summary mode**: short, decision-oriented card. Single value +
    range + tier badge + ≤3 high-importance flags.
  - **Standard mode**: the current 'buyer/seller/investor' content.
  - **Audit mode**: the current 'valuer' content (full reasoning_trace,
    methodology footers, RICS citation chain).

Each user picks their preferred mode once; audience-specific framing
becomes a thin presentation-layer adapter rather than 4 separate
builders."

**Design question for 2.23.x:**
- Is the audience-as-three-modes architecture cleaner than the current
  audience-as-four-builders?
- Migration path: can the 4 builders be refactored to 3 modes without
  breaking API contracts (frontend depends on
  `audience='buyer'` etc.)?
- Does the secretary-audience whitelist (Sprint 2.16.12 B3) survive
  unchanged, or does it need new modeling?

**Why deferred from 2.22.0a.2:**
Architecture refactor touching every brief-builder function + frontend
audience selector. Independently scoped Sprint.

---

## How to use this file

- Each §X above is an input to 2.23.x design discussion, not a
  ticket-ready spec.
- Anas's reconciliation already marked these DEFER (per Sprint
  2.22.0a.2 resume KICKOFF). Re-opening any of them requires the
  standard §5 pre-Sprint audit + multi-AI validation cycle.
- This file is **read-only forward of 2.22.0a.2** — do NOT amend
  to add new strategic observations from later Sprints; create a
  separate `DESIGN_<sprint>_VALIDATOR_FEEDBACK.md` file per Sprint
  if needed.

---

*Captured by Sprint 2.22.0a.2 Phase 1 closeout, 2026-05-27.*
