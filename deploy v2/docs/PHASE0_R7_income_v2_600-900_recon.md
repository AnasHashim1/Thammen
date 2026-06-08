# Phase-0 Recon — §6 v2 keystone: are 600-900 villa YIELD cells calibratable?

**Date:** 2026-06-08 · **Type:** read-only recon (NO engine change, NO deploy; engine stays
b6/v173). · **Probes:** `.r7v2_recon.py` + `.r7v2_sale.py` (real engine `build_reference` +
`resolve_moj_area_name` + the live `cap_rates.sqlite`; E14). · **Trigger:** §6 v2's headline
deferred item — "600-900 yield cells so Marikh/villa-6 income-LEAD not just widen" (Session_Log
§20.40, brief §2/§9). The keystone that decides whether §6 v2 can ground the two flagship
over-anchored villas or whether they stay `widen_down`.

---

## Verdict (go/no-go): 🔴 600-900 villa yield cells = **NO-GO (data-infeasible)**

**Universal:** of **187** villa cells in the live `cap_rates.sqlite`, **ZERO** reach usable
(reliable/indicative) at 600-900. Usable cells exist only at **400-600 (13)** and **900-1500 (3)**.
The §20.38 per-area deep crawl (3458 listings) already tried and produced **no** usable 600-900
cell anywhere. The 600-900 villa bracket is systematically thin on BOTH sides (large villas rent
thinly / owner-occupied; MoJ 600-900 sales sparse).

**Per flagship (the two motivating cases), measured:**

| area (GIS → MoJ via override) | 600-900 SALE (MoJ, a18+override) | 600-900 RENT (PF, DB cell) | binding block |
|---|---|---|---|
| **المعمورة** (villa-6 56/647/6) | **n=7** (24mo) / 9 (36mo), med 3.8M | n=11 (`المعمورة 56`, fallback) | **SALE** < 10 floor — MoJ frozen 159d → won't grow → **hard block** |
| **امريخ الجنوبي → مريخ** (54/541/6) | n=13 (24mo) / **15** (36mo), med 5.1M | **0** (no DB cell at 600-900) | **RENT** — 0 PF villa rentals; deep crawl already failed → **effective block** |

(امريخ الجنوبي 400-600 **reliable n=46 net 5.16%** ✓; المعمورة 56 400-600 **reliable n=69 net 4.83%** ✓ — both areas HAVE a usable cell, just not at 600-900.)

---

## The decisive engine finding (reframes §6 v2)

`_lookup_calibrated_cap_rate` (evaluate_unified.py:399) queries **strictly at the subject's bracket**
(`size_bracket = _cap_size_bracket(plot)`) with **no cross-bracket borrowing**. And
`_income_triangulation`'s **income_led** gate (4726) requires
`prov.source=='calibrated' AND confidence in ('reliable','indicative')`.

⟹ A 600-900 subject (Marikh / villa-6) → lookup at 600-900 → no usable cell → `(None,None)` →
income computed with the **4% hardcoded fallback** → `calibrated=False` → **income_led CANNOT fire
at 600-900 even WITH a subject rent.** It falls to `widen_down`.

**So the real blocker to grounding Marikh/villa-6 is neither "no 600-900 cells" nor "no rent" alone —
it is that the lookup won't BORROW the area's usable 400-600 yield for a 600-900 subject.**

---

## §6 v2 — RESHAPED (recon overturns the signed deferred plan, like الثمامة-46 §20.18)

- 🔴 **DROP** "calibrate 600-900 cells" — data-infeasible (above).
- 🟢 **ADD** **cross-bracket yield-borrowing** in `_lookup_calibrated_cap_rate`: when the subject's
  bracket has no usable cell, fall back to the **area's best usable cell (any bracket)** as the
  yield, with a provenance disclosure ("yield borrowed from the area's 400-600 cell") + a wider MUC.
  **Data-feasible TODAY** (امريخ الجنوبي 400-600 5.16%; المعمورة 400-600 4.83%). This is the lever
  that lets Marikh/villa-6 **income-LEAD (~3.2M)** once a rent exists. *Soundness:* net yields are
  bracket-stable WITHIN an area (≪ the cross-area spread) → borrowing an adjacent bracket is
  RICS-defensible with the disclosure + MUC. (v2 build should empirically confirm the within-area
  cross-bracket yield spread before locking it.)
- 🟢 **KEEP** Fork C (a18/override-aware lookup) — *robustness/consistency*, NOT a live bug:
  `_cap_area_token` already GIS↔GIS-matches both flagship cells (§20.39); align it to the
  comparison's `resolve_moj_area_name` so the two leading pillars agree on area.
- 🟢 **KEEP** opex **0.20** end-to-end (brief §5) + **(ii)** age-rent (opportunistic, wide MUC).

---

## Strategic implication (the routing insight) — §6 v2's payoff is **beta-gated**

`income_led` requires a **subject rent** (`rent_source=='actual_provided'`). On **live no-rent
traffic**, Marikh/villa-6 stay `widen_down` **regardless of any v2 lever**. So cross-bracket
borrowing + Fork C + opex are **pre-positioning** that becomes live-useful **the moment the beta
feeds subject rents (path i)** — buildable + offline-verifiable NOW (force a rent like the b6 smoke),
but **inert on live traffic until the beta (gate #6) opens.**

⟹ The beta is **upstream** of §6 v2's real-world value. The reshaped §6 v2 is "ready-when-rents-flow."

---

## Recommendation

1. **Re-sign the reshape** (600-900 cells → cross-bracket borrowing) — a Gate-2 methodology change
   overturning the signed deferred plan → HALT-and-re-sign per #20.18 before building.
2. Two sound paths (Anas's strategic call, made sharper by the beta-dependence):
   - **(A) Build the reshaped §6 v2 slice now** (borrowing + Fork C + opex 0.20), verify offline
     (force Marikh+rent → expect ~3.2M income-LEAD at 600-900 via the borrowed 400-600 yield), ship
     Gate-1. The grounding machinery is then ready the instant the beta opens. (Inert on live traffic
     until rents flow.)
   - **(B) Pivot to the beta (gate #6) first** — the upstream unlock + the binding launch constraint —
     then ship reshaped §6 v2 immediately after, verified on real rent traffic.

*CC lean:* the recon makes the binding value-unlock the **beta**; §6 v2 is the ready-when-you-are
follow-on. If the goal this cycle is engine progress, **(A)** is sound + low-regret (right fix,
verifiable now). If the goal is launch, **(B)** is the binding constraint.

---

## Carried forward
- MoJ **sale-side** 600-900 depth (المعمورة n=7) is a frozen-MoJ tail — unfixable without new sale data.
- PF **rent-side** 600-900 villa depth is fundamentally sparse — the §20.38 deep crawl confirms it.
- The within-area cross-bracket yield-stability check = the v2 build's first empirical gate.
- Scratch probes `.r7v2_*.py` left untracked (regenerable).
