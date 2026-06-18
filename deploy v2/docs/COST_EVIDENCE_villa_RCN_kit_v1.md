# Villa construction-cost evidence kit (toward a building-type-appropriate §20.9 RCN calibration)

> **Purpose:** build a **villa-specific** construction-cost corpus (recent, ordinary + luxury) so a
> FUTURE Gate-2 recalibration of the §20.9 DRC **RCN ladder** rests on building-type-appropriate
> evidence — the RICS valuer's stated NEXT (the Ashghal water-tank BoQ only *validated* the ladder;
> §20.89-adjacent / `docs/VALIDATION_DRC_RCN_ashghal_boq_2026.md`). **This kit is collection only —
> docs/data, value-invariant, NO engine change.** Recalibration stays Gate-2 + valuer-signed, gated on
> the discipline below. Mirrors the `GT_INTAKE_KIT_v1` pattern.

## What "appropriate-type" means (the valuer's bar)
A water-tank/road BoQ is the WRONG building type (only its structural unit rates transfer). Calibration
evidence must be a **residential villa** cost record. Two classes:

- **T1 — calibration-grade (documented):** a real villa **BoQ**, a **signed contractor turnkey quote**,
  a **QS final account / consultant cost estimate**, or a developer build-cost record. Carries a
  document (سند/عقد/شيت). Operator-supplied (as the tank BoQ was). **Only T1 can ever move the ladder.**
- **T2 — context/benchmark (published):** Qatar construction cost-consultancy reports (e.g. AECOM /
  Turner & Townsend / Arcadis Doha construction-cost guides), contractor advertised QAR/m², market
  cost articles. Web-researchable (deep-research). **Indicative band only — never calibrates; sets
  expectations + sanity-checks T1.**

## Tiers to target (the ladder rungs)
Collect for BOTH **ordinary/average** and **luxury** (and good/high if available) — recent (prefer
≤24 months; index older rates to the valuation date for escalation).

## Per-entry fields (capture these)
`source · date · evidence_type (T1/T2) · doc_reference · finish_tier (ordinary|good|luxury) · BUA_m2 ·
all_in_QAR_per_m2 · structure_QAR_per_m2 (if split) · finishes_QAR_per_m2 (if split) · MEP_QAR_per_m2
(if split) · prelims_incl? (Y/N) · location · notes`. **Always separate structure vs finishes vs MEP
where the source allows** — do not blend sources as one anchor (the §20.9 validation lesson).

## Discipline (RICS — IVS 104; locked)
1. **n ≥ 20 within a tier** of T1 evidence before any recalibration (the B-2 / GT discipline).
2. **T1 only** for calibration; **T2 = context**. No weight without a documented source.
3. **Escalation:** index every rate to a common valuation date; record the source date.
4. **Building-type-appropriate only** — villa records; reject infra/commercial unless used as a
   trade-rate cross-check (clearly tagged, like the Ashghal BoQ).
5. **value-invariant during collection** — the ladder + engine are UNTOUCHED until a Gate-2 sprint.
6. Log every T1 entry in `docs/validation/VALIDATION_LOG.md`; T2 bands in this kit / a companion sheet.

## Current ladder (the thing being cross-checked — for reference, do NOT edit on collection)
§20.9 RCN ladder (PO-experience + TD-93317 n=1 + Ashghal-BoQ validation): shell ~1,200 · ordinary
~2,200 · good ~2,500 · high ~3,000 · luxury ~3,500 QAR/m² BUA. The Ashghal QS build-up landed at
~2,500 (band 2,200–3,500) → **confirms**, does not move it.

## New-session plan (start here)
1. **T2 web sweep (deep-research):** recent (2024–2026) Qatar **villa** turnkey QAR/m² for ordinary +
   luxury, from cost-consultancy reports + contractors; produce a cited band + compare to the ladder.
2. **T1 intake:** stand up the capture (this kit's fields) for operator-supplied villa BoQs/quotes;
   ask the operator for 2–3 recent villa quotes (1 ordinary, 1 luxury) to seed T1.
3. **Present:** the T2 band + any T1 seeds vs the ladder → recommend keep/adjust (valuer-reviewed). No
   engine change without n≥20 T1 + a signed Gate-2.

## Reviewers (when it becomes a calibration sprint)
RICS valuer (lead — methodology + the n/escalation/type discipline) + QS lens (rate build-up) +
lawyer (only if a published source's data is republished to users). Collection itself = no panel.
