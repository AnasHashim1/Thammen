# Phase-0 recon — §6 income-triangulation (the NEXT R7 step)

**Date:** 2026-06-07 · **Author:** Claude Code (read-only recon) · **Status:** **READ-ONLY — no
engine change, no push, NO GATE CROSSED.** Engine stays **b5 / Heroku v172** (byte-identical).
**Purpose:** the measured code-wiring map + the design forks that the Claude.ai **§6 brief** (Gate-2)
must resolve, so the brief is grounded in the real engine — not a premise that turns out false on
build (the §20.26/§20.29/§20.32 pattern). Feeds `DECISION_income_crosscheck_villa_R7.md` §6/§11.

This is the **§6-specific CODE recon**; the §5 **DATA**-feasibility audit is already done (§8 of the
DECISION: rent FEASIBLE, yield now strong-enough at 16 usable cells / 6 reliable, shipped v172).

---

## 1. The current flow (measured, with line refs — `evaluate_unified.py`)

The headline today is **Sales Comparison alone**; income + cost are **downstream, descriptive,
value-invariant**. The engine's own comment says it (4636–4645): *"valuation = primary['value'] =
Sales Comparison alone in 100% of cases; cost/income are convergence checks only, never blended into
the headline number."*

```
Step 4  primary = _select_primary_comparison(...)        # the Sales-Comparison headline value
Step 5  cost   = _build_cost_crosscheck(ev)              # :3928
        income = _build_income_crosscheck(               # :3931
                   rental_income, v3_rent, asset_type,
                   primary_value = primary['value'],     # :3935  ← income is told the comparison value
                   area_name, plot_area_m2, stock_class)
Step 6  reconciliation = _analyze_reconciliation(primary, cost, income)   # :3943  STATUS ONLY
Step 8  output = _build_unified_output(...)              # :3948
            output['valuation']['amount'] = _r100k(primary['value'])      # :4715  ← THE HEADLINE
```

- **`_analyze_reconciliation` (:1967)** returns only a status dict (`strong_convergence` /
  `moderate_convergence` / `divergence`) + `spread_pct` + `gaps_pct`. It **never returns a value** →
  this is exactly why the headline is value-invariant.
- **`_build_income_crosscheck` (:1548)** computes `income_value = NOI / cap_rate`, NOI =
  `annual_rent × (1 − OPEX_RATIO_RESIDENTIAL)` with `OPEX_RATIO_RESIDENTIAL = 0.23` (:360). Its
  declared role is literally `'تأكيد منهجي — لا تدخل في القيمة النهائية لعقار سكني'` (:1643) — the
  line §6 changes.
- The calibrated yield arrives via **`_lookup_calibrated_cap_rate` (:399)**; the villa fallback is
  `CAP_RATES_BY_ASSET['villa'] = 0.040` (:338, 4% by design, Fix#3).

**The §6 hook point is unambiguous:** between Step 6 and Step 8, a triangulation step must produce a
**triangulated amount** that replaces `primary['value']` at the **:4715** headline (and the low/high
+ method_label/source_ar around it). Everything upstream (`primary`) and the reconciliation status
stay; the change is *which number reaches :4715*.

---

## 2. 🔴 THE CRUX FORK — where does the income pillar's RENT come from?

This is the single most important thing the brief must decide, and it is **non-obvious**. The
income value only carries **new signal vs the comparison** when the **rent is the SUBJECT's**, not the
area median that built the yield.

**Why (the circularity, derived):** the calibrated yield is `net_yield = (area_rent_median ×
(1−opex)) ÷ MoJ_sale_median`. If §6 fed the **area rent median ÷ the area yield** back as the income
value:

```
income_value = (area_rent_median × (1−opex)) / net_yield  ≈  MoJ_sale_median  ≈  the comparison value
```

→ a **circular no-op**: income "sets" the same number comparison already gives. A §6 brief that
naively says *"use the calibrated yield to set the headline"* would ship exactly this no-op.

**The decision's mechanism REQUIRES a subject-specific rent** (§2.3 / §3 walk-through): *"rent
reflects age/condition, so it catches the comparison's over/under-anchor."* The walk-through used a
**human-adjusted subject rent (15–17k for villa-6: large+pool but old, unfurnished)** ÷ the area
yield → 3.0–4.1M. The yield's job is to **convert the subject's rent into a value**; the *signal*
lives in the subject rent, not the yield.

**Today** `_build_income_crosscheck` already prefers a subject rent: (1) `rental_income` (user) →
independent ✓; (2) `v3_rent_data['annual_median']` (municipality reference) → independent of MoJ
sales but area-level, condition-blind; else **returns None** (no income block — villa-6's live case).

### Fork A — the brief MUST pick the rent basis for "income SETS the headline":
- **A1 (rent-input-gated):** income SETS / co-determines the headline **only when a subject rent is
  available** (user Stage-2 input, or a condition-adjusted estimate). Otherwise comparison stands and
  income stays a cross-check. *Honest, matches the walk-through, non-circular — but reach is limited
  to inputs that exist.* The walk-through implies this is the v1 shape.
- **A2 (auto area-rent table):** ship a per-area×bracket **villa-rent-median table** (sibling to the
  yield table) as the auto rent; income fires whenever a rent×yield cell exists. *Broader reach, but
  the area median is condition-blind → tends back toward comparison (≈ circular) unless rent-median
  and sale-median genuinely diverge.* Risks the no-op above; would need a real condition adjustment
  to add signal.

**Recommendation for the brief:** A1 for v1 (subject rent → calibrated yield → income pillar), with
A2's area rent only as a labelled, condition-blind *fallback cross-check*, never as the value-setter.
This is the only shape that delivers the decision's stated benefit (catching the R7 over/under-anchor)
without a circular headline. **The brief should state which rent reaches the value, explicitly.**

---

## 3. Fork B — the triangulation decision logic (Gate-2 methodology)

`_analyze_reconciliation` already computes the spread + per-pillar gaps; §6 must turn that from a
*status* into a *value rule*. The brief must specify:

- **When does income SET vs blend vs cross-check?** Options: income overrides comparison when the
  subject rent is real and the gap is material; or a weighted reconciliation (RICS VPS 3 / IVS 103
  reconciliation — value = the judged convergence of the pillars); or income only *bounds* comparison
  (cap/floor) without replacing it.
- **Divergence → MUC.** Reuse the existing `spread_pct` thresholds (<15 strong, <30 moderate, ≥30
  divergence, :1992–2014) to drive a **VPGA 10 material-uncertainty** widen + a high-MUC label when
  the pillars disagree. The honest range (a10/a14 machinery) is the natural surface.
- **Bounds.** The 4 pillars give natural rails: **land floor ≤ value ≤ cost/DRC ceiling**, with
  income + comparison reconciled between them (DECISION §2). The brief should state the clamp.
- **Pillar precedence on conflict** (e.g. income says 3.2M, comparison 3.8M, land floor 2.46M, cost
  4.0M) — the walk-through resolved to ~3.6–3.8M (income@5% ≈ comparison, both < cost, > teardown).
  The brief must encode that judgement, not leave it to ad-hoc.

---

## 4. Fork C — the a18 / override-aware lookup (confirmed gap, robustness)

`_lookup_calibrated_cap_rate` (:399) keys on **`_cap_area_token` (:387)**, which differs from the
valuation's a18 key:

| | `_cap_area_token` (cap-rate lookup) | `area_match_key` (moj_reference.py:36, the valuation pool) |
|---|---|---|
| whitespace/NBSP collapse | ✓ | ✓ |
| hamza fold أ/إ/آ→ا | ✓ | ✓ |
| ى→ي, ة→ه, strip diacritics | ✓ | ✗ |
| strip trailing zone-number | ✓ | ✓ |
| drop leading «ال» | ✓ | ✗ |
| **GIS→MoJ override map** (امريخ الجنوبي→مريخ) | **✗** | **✗** (lives in `resolve_moj_area_name`) |

**Not broken today** (per DECISION §11): the calibrator stores `district_aname` = the **GIS** aname,
and the lookup matches GIS-token↔GIS-token, so override areas resolve (both sides raw GIS). The §6
robustness fix = make the lookup resolve the subject through the **same `resolve_moj_area_name`**
(override map + sibling-pooling) the comparison uses, so the yield cell is keyed **identically to the
comparison pool** — important once income co-determines the value (the two pillars must agree on
*which area*). Low-risk, well-scoped.

---

## 5. Consistency item (confirm in the brief, not a blocker)

The engine's NOI uses **`OPEX_RATIO_RESIDENTIAL = 0.23`** (:360, 1608), while the calibrator's stored
**net yield uses opex 0.20** (DECISION §9). When income merely *cross-checks*, a small opex
inconsistency is cosmetic; when income **SETS the value**, the NOI-opex and the yield's embedded opex
should be the **same basis** (and the brief should confirm whether the stored `cap_rate` column is the
**net** yield, since `income_value = NOI / cap_rate`). Flag — verify, align, or document.

---

## 6. Scope boundaries (carry into the brief)

- **Villa/house only** (`_CALIBRATABLE_ASSETS = {'villa','compound_small'}`; the decision is villa).
  Towers/compounds keep the existing DCF; land has no income.
- **Bracket-gating persists** unless §6 adds the auto-rent table (Fork A2) — most usable yield cells
  are 400-600; 600-900 anchors (Marikh) and villa-6 (المعمورة, no auto rent) won't fire on A1 without
  a subject rent. §6's whole point is to *overcome* the income-block trigger, so Fork A is load-bearing.
- **B-2 (condition elicitation) stays PARKED** (n≥20 confirmed-sales). §6 sidesteps it by routing the
  condition signal through the **subject rent** instead of confirmed-sale coefficients — but that only
  works if the subject rent is real (Fork A1) → the brief should say where the subject rent comes from
  in the flow (Stage-2 input? the b2.x refine screen already collects `rental_income`).
- **Value-invariance ends here:** §6 is a **🔴 Gate-2 headline change** (the first since the b.4
  opt-in levers). It needs the **signed brief + explicit «go»**, and a live smoke that *expects* the
  villa headline to MOVE on the rent-bearing path (not the byte-identical-4-anchors pattern of the
  value-invariant sprints — the anchors without a subject rent stay put, but a rent-bearing villa
  should shift).

---

## 7. Recommended brief structure (for Claude.ai)

1. **Mechanism** — income pillar = `subject_rent × (1−opex) / calibrated_area_net_yield`; resolve
   **Fork A** (where the subject rent comes from — recommend A1).
2. **Triangulation rule** — **Fork B**: SET/blend/bound + the land-floor ≤ value ≤ cost-ceiling clamp
   + divergence→VPGA 10 MUC reusing the `spread_pct` thresholds.
3. **Lookup** — **Fork C**: route `_lookup_calibrated_cap_rate` through `resolve_moj_area_name`
   (a18 + override) so the yield cell matches the comparison pool's area key.
4. **Consistency** — opex basis (0.23 vs 0.20) + confirm `cap_rate` column = net yield.
5. **Scope** — villa/house only; rent-bearing path moves, anchors without rent stay; MUC on divergence.
6. **Verification plan** — a live villa WITH a subject rent (expect the headline to move + converge);
   the 4 standard anchors (expect unchanged when no rent given); a divergence case (expect MUC high).
   Smoke = browser-UA curl (#61).

---

## 8. Gates (unchanged)

- **🔴 Gate-2 (methodology/output):** §6 changes the villa headline → signed Claude.ai brief BEFORE
  build.
- **🔴 Gate-1 (push):** explicit Anas «go» before any `git subtree push heroku`.
- This recon crosses **neither** — read-only, no edits, no push.
