# BRIEF — Sprint 2.22.0b.X (B-2a): teardown / demolition down-anchor

> **Status: CC-DRAFTED 2026-06-07 · Gate-2 PENDING Anas signature.** A **methodology change that MOVES the
> headline value** (a teardown villa drops from the comparison median toward land − demolition). Does NOT
> build until signed. Phase-0 recon = §20.36-pending (this brief); build recon (exact injection point) =
> after signature. Engine live = **2.22.0b.3 / Heroku v170**.
>
> **Why this brief exists:** the 56/565/21 sensitivity matrix (live v170, 20 combinations) proved the engine
> is **blind to condition** and **over-values the dilapidated case by ~+35%** — a real valuation error, not a
> missing-feature nicety. Anas proposed a «يجب هدمه» (must-be-demolished) option; this scopes it.

---

## 1. Motivation (MEASURED — 56/565/21, live v170)

| case | engine value | reality |
|---|---|---|
| age30 + maintenance + 1 floor (≈ dilapidated) | **2.30M** | land floor ≈ **1.70M**, minus demolition → **~1.5M** as-is |
| condition new = good = maintenance = renovated | **2.40M each** | engine is **100% blind to condition** |
| luxury vs plain | **2.40M each** | blind to finish (regime flips, value frozen) |

The engine assigns a dilapidated villa an **implied building value of ~+0.6M** when the building is in fact a
**negative** asset (demolition cost). Root: the Qatar 10-Year Rule (`_age_aware_substantiality_multiplier`,
`evaluate_unified.py:906`) **suppresses the BUA uplift** (adj→0) for any villa ≥10y, but it **never SUBTRACTS
toward land** — the value stays pinned at the comparison median (which assumes a sound standing building). A
teardown subject needs a **downward re-anchor**, which no path currently does.

## 2. Scope — **teardown ONLY** (deliberately carved out of the PARKED full Lever-2 + Lever-1)

This sprint is the **clear extreme tip** of B-2's DOWN lever, NOT the full calibrated lever:

| item | what | data | status |
|---|---|---|---|
| **B-2a (THIS brief)** | binary «teardown» → value = **land floor − demolition** | land floor `_villa_value_floor` n=20–33 ✅ + a demolition constant | **data-ready NOW** (no corpus) |
| Lever-2 full (calibrated) | ordinary old non-luxury villa → gradual re-anchor (floor +0–10% band) | needs GT-2 corpus to calibrate the band | **PARKED n≥20** (§20.27) |
| Lever-1 (UP) | luxury/new-build finish premium on comp ppm² | local `luxury_new` stratum n=0 → corpus-only | **PARKED n≥20** (§20.27) |

**Why B-2a can ship before n≥20 while the rest waits:** the teardown value = `land_floor − demolition` needs
**no calibration coefficient** — the land floor is already robust (n≥20), and demolition is a published
constant. There is no «+0–10% band» to calibrate here (that's the *ordinary* old villa, Lever-2 full). The
teardown extreme is **definitional** (building is a liability), not statistical. This is the §20.27 «Lever-2
data-ready» finding made shippable.

## 3. Mechanism (proposed)

1. **Trigger:** a new `condition='teardown'` value (Fork A) on `/api/evaluate/details` + the CLI choices.
2. **Compute:** reuse `_villa_value_floor` (already returns `land_floor`, n, reliability) →
   `teardown_value = land_floor − demolition_cost`.
3. **Demolition constant:** `demolition_cost = DEMO_QAR_PER_M2 × footprint_or_BUA` (Fork B). Qatar villa
   demolition ≈ **30–60 QAR/m²** (broker-grounded; to be pinned in the brief like D5/D6).
4. **Re-anchor:** set `valuation.amount = teardown_value` (Gate-2 — this MOVES the headline), with a **wide
   downward range** [land_floor − demolition_high, land_floor] and a high MUC.
5. **Disclosure:** «التقييم على أساس الأرض مطروحاً منها تكلفة الهدم — المبنى الحالي يُعدّ عبئاً (HBU = إعادة
   تطوير)» + the value_floor block (already shipped) becomes the *primary* basis on this path.
6. **Scope gate:** villa/house only; skip raw_land (no building to demolish), apartments/compounds (refusal).

## 4. Decisions for signature (Forks)

- **Fork A — the input value.** (a) add `teardown` as a distinct condition; (b) repurpose the existing CLI
  `poor` as the teardown trigger; (c) add BOTH `poor` (sound-but-bad → caveat only) AND `teardown` (must
  demolish → re-anchor). **CC recommends (c)** — `poor`≠`teardown` (a poor villa is still habitable; a
  teardown is a liability). Clear AR labels: «حالة سيّئة» vs «**آيل للسقوط / يجب هدمه**».
- **Fork B — demolition cost.** Constant per m² (30/45/60 QAR/m²?) × which area (footprint vs full BUA?).
  **CC recommends** a midpoint **~45 QAR/m² × BUA**, tagged `provisional, broker-grounded` (same discipline
  as D5/D6), with the MUC absorbing the uncertainty. **Anas to pin the number** (you know the real demolition
  market).
- **Fork C — anchor target.** (a) `land_floor − demolition` (full); (b) `land_floor` only (conservative — no
  demolition subtraction); (c) range `[land_floor − demolition, land_floor]` as headline. **CC recommends (a)
  with a range** — the demolition subtraction is the honest reality; the range carries the estimate
  uncertainty.
- **Fork D — separate-ship vs wait.** Ship B-2a now (data-ready) OR fold into the PARKED B-2. **CC recommends
  SHIP NOW** — it fixes a measured error with no corpus dependency; the calibrated Lever-2 band + Lever-1 stay
  parked. (This is the substance of the «go».)
- **Fork E — `poor`/`fair` middle.** Whether `poor`/`fair` get a *partial* down-anchor now, or stay
  caveat-only until the calibrated Lever-2. **CC recommends caveat-only now** (partial re-anchor IS the
  calibrated band → needs n≥20). B-2a = the binary teardown extreme only.

## 5. Relationship to §20.27 PARK (the discipline check)

§20.27 signed **Fork#2 = WAIT-for-n≥20** and **Fork#1 = MODERATE (floor +0–10%, provisional till n≥20)**.
B-2a does **not** violate that: the «+0–10% band» and the luxury exception are the *ordinary-villa* calibrated
re-anchor (still parked). B-2a ships only the **definitional teardown extreme** (building = liability → land −
demolition), which §20.27's own §5 audit flagged as **data-ready**. The brief explicitly **keeps Lever-1 and
the calibrated Lever-2 band PARKED**; it carves out only the uncalibratable extreme. **This carve-out is
itself a Gate-2 decision (Fork D) — Anas signs it.**

## 6. RICS framing (§20.27 web-check carries; multi-AI #54 OPTIONAL)

A «must-demolish» subject is valued on its **Highest-and-Best-Use = redevelopment** (VPS 2 / IVS 102 HBU): the
land at development value, the building as a demolition liability. Per the §20.27 Rule-#54 web-check, a
**stated** condition is an **assumption + MVU, NOT a Special Assumption** (it describes the as-is reality at
the valuation date, not a hypothetical future change). So teardown = as-is HBU on a stated assumption → carries
MVU, consistent with §20.27. **multi-AI #54 is optional** here (framing, not evolving-standard numbering) —
recommend a round only on the **demolition-disclosure wording** if Anas wants it.

## 7. Verification plan (at build, after signature)

- Isolated test (real engine): teardown → amount == `land_floor − demolition` (down-moved), within range; the
  4 non-teardown anchors **byte-identical** (the new path fires ONLY on `condition='teardown'`); scope gate
  (raw_land/apartment skip); `poor`/`good`/etc. unchanged.
- **Before/after on 56/565/21:** age30+teardown → **~1.5M** (was 2.3M); all other 19 matrix cells unchanged.
- DoD 392/15/45/broad +1 · **R14 real-Chromium** (the teardown disclosure + downward range render, 390×844).
- Live smoke: the **4 standard anchors byte-identical** (teardown is opt-in) + one teardown hit showing the
  re-anchor.

## 8. What's NOT in scope

- The **calibrated** Lever-2 band (ordinary old villa +0–10%) — PARKED n≥20.
- **Lever-1** luxury/finish premium (UP) — PARKED n≥20.
- Auto-detecting teardown from imagery/age — this is a **user-stated** condition only (E17: broker states,
  engine values).
- Any change to the 4 existing condition values' behavior, or to non-villa paths.

---

*CC-drafted Phase-0 brief. Gate-2 PENDING Anas signature (Forks A–E, esp. Fork B demolition number + Fork D
ship-now). On signature: build recon (exact injection point — where `valuation.amount` is finalized on the
bracket path vs the `_villa_value_floor` site at `evaluate_unified.py:4255`) → build → Gate-1. Saved per Rule
#63.*
