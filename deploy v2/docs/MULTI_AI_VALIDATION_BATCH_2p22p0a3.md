# Rule #54 Multi-AI Validation Batch — Sprint 2.22.0a.3

**Sprint:** 2.22.0a.3 (Arabic Surface Honesty Pass)
**Drafted:** 2026-05-28
**Owner:** Anas — runs GPT-5 + Gemini, pastes responses verbatim below
**Status:** Drafted by CC, pending Anas's validation runs **before push**

---

## Why this batch

Sprint 2.22.0a.3 reframes 6 user-visible Arabic surfaces for epistemic
honesty (drop fabricated condition claims, gate trend numeric on MUC
level, drop ranges with no calibration study, reframe internal-jargon
labels). Per Operational_Rules #54, copy changes that touch
regulatory/methodology framing must be independently validated by two
AI systems before push.

The kickoff (Appendix A) drafted 5 prompts (A–E). Amendment B requires
augmenting Question E with the "preserve C4 verbatim wording"
guardrail. Both augmentations are reflected below.

The 5 prompts target the substantive copy changes only:
- **A** = T1.1 (drop `بحالة جيدة`)
- **B** = T1.2 (conditional gate of numeric trend)
- **C** = T1.4 (10-Year-Rule reframe)
- **D** = T2.5 (±20-40% → qualitative)
- **E** = T2.8 (disclaimer consolidation 4→2) — **NOTE: T2.8 is DEFERRED
  to Sprint 2.22.0a.4 in this Sprint's scope**, but Question E is
  retained here so the answer informs the 2.22.0a.4 design upfront.

Items NOT validated (because they don't change regulatory/methodology
framing): T1.3 (UI label "تقييم كامل" → "تحليل آلي" — vocabulary
choice, not methodology); T2.7 (additive enrichment — adding gaps,
not asserting facts).

---

## Decision-binding policy

- **Both AIs agree** → ship as drafted.
- **One AI flags a concrete defect** → CC reviews; if defect is
  load-bearing, revise Sprint copy before push.
- **Both AIs flag the same defect** → revise mandatorily before push.
- **Divergence (one approves, one objects)** → Anas adjudicates;
  if unresolved, defer the relevant item.

---

## The 5 prompts

> **Paste the prompt below into BOTH GPT-5 and Gemini, identically.**
> Identity of the AI determines which response section to fill in below.
> Do not edit the prompts unless flagging a typo (note any change in
> the "amendments" section at the bottom).

---

### Prompt (paste once per AI)

> You are auditing copy from an automated property-valuation tool in
> Qatar (RICS/IVS-framed, not a formal valuation). For each proposed
> change, answer:
> (1) does it correctly resolve an over-claim without introducing a new
>     error;
> (2) is the regulatory framing accurate as of the RICS Red Book
>     effective 31 January 2025 (VPGA 10, VPS 6) and IVS 106;
> (3) any defensibility risk.
>
> **A.** Tool currently asserts a building is `بحالة جيدة` (good
> condition) with no inspection and no user-supplied condition.
> Proposal: remove the claim entirely. Correct, or is there a
> defensible weaker phrasing?
>
> **B.** When the tool flags Material Valuation Uncertainty (insufficient
> data), it still prints a numeric market trend (e.g. "stability,
> 1.9%/yr"). Proposal: when MUC level is `critical` or `high` (data
> shortfall / methodology breakdown), show only a qualitative trend
> label, suppress the decimal; keep the numeric when MUC is `low` or
> `moderate` (where `moderate` is the ambient desktop default for
> "no field inspection"). Is conditional suppression on the
> `critical`/`high` subset the right resolution, or should the numeric
> be removed in all cases / on a wider MUC subset?
>
> **C.** Tool cites a "10-Year Rule in Qatar" (old properties trade
> near land value). No formal rule exists. Proposal: reframe as
> observation ("in some older categories in the Qatari market,
> transaction price approaches land value; the building is treated
> more as architectural burden than value-add"), drop "Rule."
> Adequate, or still over-stated?
>
> **D.** Tool states the valuation "may vary ±20–40%" when building
> details aren't provided, with no calibration study behind the
> range. Proposal: replace with qualitative uncertainty language
> ("may differ noticeably" / "الفرق قد يكون ملحوظاً"). Agree, or is
> a disclosed-assumption range preferable to none?
>
> **E.** Proposal: consolidate 4 overlapping disclaimers into 2 (MUC
> reservation + RICS/IVS "not a formal valuation"), **without
> reversing recently-locked reframed wording** (specifically: the
> descriptive-provenance phrasing
> `"ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS"`
> shipped in Sprint 2.22.0a.2 Pattern C4 must be preserved verbatim
> wherever the RICS/IVS layer is kept). Does collapsing to 2 lose any
> legally/professionally necessary distinction? (NB: T2.8 is deferred
> from Sprint 2.22.0a.3 to 2.22.0a.4 — this answer informs the
> 2.22.0a.4 design upfront.)

---

## GPT-5 response (paste verbatim)

```
[PASTE GPT-5 RESPONSE HERE — VERBATIM, NO EDITS]
```

---

## Gemini response (paste verbatim)

```
[PASTE GEMINI RESPONSE HERE — VERBATIM, NO EDITS]
```

---

## CC consensus reading

> To be filled by CC after Anas pastes both responses. Notes:
> - Which items both AIs approve.
> - Which items earn revision (and what the revision is).
> - Which items earn deferral (e.g. if both AIs say a numeric trend
>   should be removed even at MUC=low, T1.2 gate widens).

```
[CC FILLS THIS AFTER VALIDATION RUNS]
```

---

## Amendments / typo log

(If you have to edit any of the 5 prompts before sending, note the
edit here with the timestamp.)

```
None as of drafting.
```
