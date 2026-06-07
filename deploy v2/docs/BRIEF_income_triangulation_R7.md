# Brief — Sprint §6 Income-Triangulation (R7 villa headline)

**Date:** 2026-06-07 · **Status:** **DRAFT — awaiting Anas Gate-2 sign-off.** Authored by CC under
«افعل الأصوب» (PO delegated the no-rent shape) + the live PO decision **(أ)** = income MOVES the
villa headline down toward grounded reality. **Grounded in:** `PHASE0_income_triangulation_recon.md`
(the measured wiring map) + `DECISION_income_crosscheck_villa_R7.md` (§1–§11). **Gates:** 🔴 Gate-2
(this brief — it changes the villa headline value) → then build as its own unit → 🔴 Gate-1 «go»
before any `git subtree push heroku`. Multi-AI #54 = **OPTIONAL** (standard RICS VPS 3/IVS 103
reconciliation + VPGA 10 MUC — no evolving-standard / numbering question).

---

## 1. Goal (PO decision أ)

Stop pinning condition-blind comparison **guesses** (e.g. Marikh 54/541/6 = 5.4M, defensible
~3.0–3.4M) as confident headline values. When a **grounded income** read exists, it **SETS/leads**
the villa headline → the value actually moves down to reality (Marikh 5.4M → ~3.2M). Income is "THE
binding check" (DECISION §2.3): rent reflects age/condition, so it catches the comparison's
over/under-anchor. This is a **🔴 Gate-2 headline change** — the first non-opt-in value move since b.4.

---

## 2. Mechanism + rent source (the synthesis الأصوب — أ + i + ii + iii)

```
income_value = subject_rent_annual × (1 − OPEX) / calibrated_area_net_yield
```

**🔴 Circularity guard (the recon's key finding — non-negotiable):** NEVER feed the raw **area-median
rent ÷ area-yield** as a SET — it reconstructs the comparison (`area_rent/yield ≈ area_sale_median`),
a no-op. The subject rent MUST be **subject-specific / condition-reflecting** to carry new signal.
Rent source priority:

1. **(i) Subject rent — user/broker** (the spine). The refine screen (b2.x) already collects
   `rental_income`; the beta feeds it. Strongest, grounded. → income SETS the headline.
2. **(ii) Age-adjusted area rent** (no-input grounded attempt) — when GIS auto-age is present
   (Sprint 2.15.1 imagery cache), discount the area rent median by an age factor so an old villa's
   estimated rent falls below the area (younger-stock) median → breaks the circularity downward.
   **Honest limit:** auto-age is frequently `None` on the default path (E22) and age ≠ full condition
   → (ii) fires opportunistically, not universally. When it fires + the result is plausible → income
   SETS (with wider MUC, flagged "rent estimated from age").
3. **(iii) Honest-widen safety net** (no grounded income) — when neither (i) nor (ii) yields a
   usable subject rent, do NOT pin the high comparison guess: keep comparison as the central marker
   BUT **widen the range DOWN toward the land floor** + force **MUC high** + the condition-blind
   disclosure. The value isn't grounded-moved, but it stops asserting a narrow confident high band.

**Honest reach (state plainly, #36):** the LEVEL truly moves down grounded only via (i) — and for
Marikh/villa-6 today there is no user rent, so (ii)/(iii) govern them until a rent flows in. (ii) is
thin (age detection). So **(iii) is the de-facto no-rent behavior**, and the durable universal fix
for no-rent condition correction still wants either subject rents (Stage-2/beta) or B-2 (confirmed
sales n≥20, parked). §6 does NOT close R7 for rent-less villas — it un-anchors them honestly (iii)
and grounds them when a rent exists (i).

---

## 3. Triangulation rule (Fork B — the Gate-2 core)

Four pillars (DECISION §2): **land floor** (MoJ land × plot, n≥20 — hard FLOOR) · **comparison**
(area median — condition-BLIND) · **income** (the binding check) · **cost/DRC** (b4 — CEILING).

**Clamp (always):** `land_floor ≤ headline ≤ cost_ceiling` (market ≤ replacement; ≥ land).

**Decision (proposed v1 — CC judgment, flagged for sign-off):**
- **Grounded income exists** (path i, or ii when it fires) **AND** income is RELIABLE (yield cell
  reliable/indicative + rent passes the existing `YIELD_FLAG_MIN/MAX` sanity 2–12%) →
  **headline = clamp(income_value)**; comparison demoted to a **disclosed sibling cross-check**; the
  **range spans the pillars** (≈ min(income,land-ish) … comparison) so the divergence is visible;
  **MUC scales with spread** (reuse `_analyze_reconciliation` thresholds <15 / <30 / ≥30 →
  moderate/high MUC). This delivers Marikh 5.4M→~3.2M and leaves villa-6 ~3.6–3.8M (where income ≈
  comparison they converge — small move, that's correct).
- **No grounded income** (path iii) → **headline = comparison** (unchanged central) BUT **range
  widens down toward land_floor + MUC high** + condition-blind disclosure (the a10/a14 honest-range
  machinery is the natural surface).
- **Income present but UNreliable** (thin yield / rent fails sanity) → treat as no grounded income →
  path iii. Never let a flaky rent×yield SET the headline.

**Divergence → VPGA 10 MUC** on every path (reuse the existing spread/status reporter — now it also
drives the range width + MUC level, not just a label).

**Why income-LEADS-when-grounded (not a timid blend):** the decision endorses income as the backbone
(«منهجية قوية أستند عليها») and the PO chose (أ) = the value MOVES. A weighted blend that keeps
comparison's weight high would re-pin the guess. The reliability-gate + the [land_floor, cost_ceiling]
clamp + MUC-on-spread are the safety rails. **PO sign-off item B1:** confirm income-LEADS (vs a
spread-weighted blend) when grounded+reliable.

---

## 4. Lookup fix (Fork C — a18/override-aware)

Make `_lookup_calibrated_cap_rate` resolve the subject's area through the **same**
`moj_reference.resolve_moj_area_name` (a18 sibling-pooling + the GIS→MoJ override map, e.g.
امريخ الجنوبي→مريخ) that the **comparison pool** uses — so the yield cell is keyed identically to the
comparison's area (the two leading pillars must agree on *which area*). Not broken today (GIS↔GIS on
`district_aname`), but required once income co-determines the value. Low-risk, well-scoped.

## 5. Opex consistency (confirm, not optional once income leads)

Engine NOI uses `OPEX_RATIO_RESIDENTIAL = 0.23`; the calibrator's stored net yield uses opex 0.20
(DECISION §9). When income only cross-checked this was cosmetic; **when income SETS the value the two
must share one basis.** Confirm the stored `cap_rate` column = **net** yield (since
`income_value = NOI/cap_rate`), then align the opex (use one constant end-to-end). **Decide:** adopt
0.20 (RICS villa opex norm, matches the calibrator) end-to-end, or re-derive. CC default: **0.20**,
aligned both sides.

## 6. Scope

Villa/house only (`_CALIBRATABLE_ASSETS = {'villa','compound_small'}`; the decision is villa). Towers/
compounds keep the existing DCF; land has no income. B-2 (confirmed-sales condition coefficients)
stays PARKED — §6 routes condition through rent, sidestepping the n≥20 blocker (DECISION §4), and is
honestly bounded by the rent-availability reach (§2).

## 7. Verification plan (NOTE: NOT byte-identical — that's the point)

- **Villa WITH a subject rent** (the SET path) → headline **moves** + the pillars reconcile;
  **Marikh 54/541/6 + its rent (~15–16k/mo)** → expect **~3.0–3.4M** (5.4M un-anchored). The proof.
- **Villa-6 56/647/6 + rent** → ~3.6–3.8M (income ≈ comparison → small move; correct).
- **4 standard anchors WITHOUT a rent** → path iii (range widens down + MUC high) — expect the
  headline central marker unchanged but the **range + MUC** changed (NOT the value-invariant
  byte-identical pattern; document the new range/MUC explicitly).
- **A divergence case** → MUC high, range spans pillars.
- Reliability-gate: a bad rent / thin-yield villa → does NOT SET (stays path iii).
- Smoke = **browser-UA curl (#61)**; isolated tests on the real triangulation fn (E14); DoD matrix.

## 8. Build sequencing (Rule #38 — one sprint, internal phases)

§6 is one triangulation sprint but sizable. Prerequisites that can land first to de-risk (both
near-value-invariant): **Fork C lookup** + **§5 opex alignment**. Then the core (§3 rule + §2 rent
synthesis). Optional internal split if the build proves large: §6a (C+opex, prep) → §6b (core SET +
iii). CC will flag at build time if a split is the أصوب.

## 9. Gate-2 sign-off items (the only PO-level calls — rest is CC judgment)

- **B1** — income **LEADS** when grounded+reliable+clamped (vs a spread-weighted blend). *CC rec: LEADS.*
- **B2** — opex basis end-to-end = **0.20** (matches calibrator). *CC rec: 0.20.*
- **B3** — ship **(ii) age-adjusted rent** in v1 (opportunistic, wide MUC), or defer (ii) and ship
  **(i)+(iii)** only first? *CC rec: ship (i)+(iii) in v1 (the honest spine + safety net); add (ii)
  as a fast-follow once age-detection reliability is measured — keeps v1 single-purpose + avoids
  shipping a thin age-estimate as a value-setter before it's measured.*

**On your sign-off of B1–B3 (+ a build «go»), CC builds §6 as its own focused unit, then asks for the
Gate-1 push «go» with tests measured.**
