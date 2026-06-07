# Decision — Income Cross-Check Triangulation as the R7 Villa-Valuation Mechanism

**Date:** 2026-06-07 · **Status:** **PO-ENDORSED (direction)** — NOT yet built.
**Gate:** Hard Gate 2 (methodology) — requires a §5 data-feasibility audit + signed brief +
yield calibration **before it lands**. **Supersedes the FRAMING of:** the b.4 teardown-only
switch and the parked B-2 condition-elicitation as the *sole* R7 path.

## 1. The decision (Anas, 2026-06-07)
After a live valuation walk-through of villa **56/647/6** (V001, المعمورة — the "villa 6"
photos), Anas endorsed the **income cross-check** as the methodology backbone for villa
valuation — over owner-aspiration, over a condition-blind comparison median, and over the
crude teardown switch. PO words: «هذه المنهجية أفضل بكثير … لا يهمني طموح المالك … ما دام
لدي منهجية قوية أستند عليها».

## 2. Why it is strong (RICS triangulation — 4 pillars cross-check; value = convergence, divergence → MUC)
1. **Land floor** — MoJ land median × plot (n≥20). Hard floor.
2. **Sales comparison** — area villa median. Market signal, but **condition/age-BLIND (R7)**.
3. **Income cross-check** — realistic rent ÷ villa cap rate. **THE binding check:** rent
   reflects age/condition, so it automatically catches the comparison's over/under-anchor
   (old → lower rent → lower value; new → higher). Continuous, not a switch.
4. **Cost / DRC** — depreciated replacement. Ceiling (market ≤ replacement) + teardown floor.

## 3. The walk-through that proved it (villa 6 / V001, 652 m², ~25 yr, very good, pool)
- Land floor **2.46M**; condition-blind comparison **3.8M**; DRC **~4.0–4.5M**.
- **Income (live PropertyFinder, المعمورة):** standard unfurnished villas **13–16.5k**/mo;
  **19–20k only for NEW furnished luxury**. Villa 6 ≈ **15–17k** (large + pool, but old, unfurnished).
- 15–17k ÷ yield: **@6% (investor)** ~3.0–3.4M · **@5% (owner-occupier — our §11.3 4–4.7%)** ~3.6–4.1M.
- **Converged Market Value ≈ 3.6–3.8M** (income@5% ≈ comparison; both < cost ceiling, > teardown floor).
  The income check correctly **capped below cost** AND **lifted above the 2.9M teardown estimate**.

## 4. Why this beats the prior R7 plans
- **vs b.4 teardown switch:** binary/extremes-only → over-anchored the good/very-good middle
  (live: 56/647/6 `good`/`renovated` → 3.7–3.8M unchanged). Income is **continuous**.
- **vs B-2 condition-elicitation (parked on confirmed-sales n≥20):** shifts the data
  dependency from *confirmed sales* (no feed — **blocked**) to *villa rent medians* (available
  via PF) + a yield → **more feasible; sidesteps the n≥20 blocker.**

## 5. Dependencies to make it production-strong (the honest gaps)
1. **Villa rent data per area** — extend the PF connector to villa rentals per district
   (المعمورة had 93 listings; verify thinner areas). Need median + n + age/condition split.
2. **Villa yield (cap rate) calibration** — **THE swing factor** (5% vs 6% = ±~20% on value).
   Per-area / per-stratum. `cap_rates.sqlite` (Sprint 2.19) is the seed but thin (Al-Ebb 4.7%).
   **An uncalibrated yield = an unreliable headline (#10).**
3. **Age/condition rent adjustment** — rent comps must reflect the subject's age/condition
   (or be adjusted). This is where the photos / Stage-2 input feed in.

## 6. Path (Gate-2)
§5 data-feasibility audit (villa rent availability + yield per area, via a PF/Heroku smoke) →
**signed brief** → build the villa income cross-check (reuse `cap_rates.sqlite` + the DCF/yield
machinery already live for towers/compounds) → triangulate the 4 pillars → MUC on divergence →
live smoke. **Do NOT land a headline value without the yield calibration.**

## 7. Status of the engine today (for the record)
Live = **Heroku v171 / b.4** (teardown ↓ + luxury-new DRC ↑ + penthouse — EXTREMES-ONLY; the
good/very-good middle still over-anchors at the widened value). This decision defines the
**next** R7 step; b.4 stays live and unchanged until the income cross-check is audited, briefed,
calibrated, and signed.

## 8. §5 data-feasibility audit (2026-06-07) — VERDICT
**Dependency #1 — villa rent data (PropertyFinder): FEASIBLE ✓.** Live PF villa-rent listing counts:
المعمورة **93** · أبو هامور **121** · الغرافة **142** · عين خالد **284**. Plentiful for a median
(needs standalone / furnished / size stratification). Standard unfurnished villa rents cluster
**9–16.5k/mo**; **19–20k ONLY for NEW furnished luxury** → confirms an old villa cannot justify 19k.

**Dependency #2 — yield calibration: THE BOTTLENECK, currently UNRELIABLE 🔴.** Existing
`cap_rates.sqlite` (Sprint 2.19): 109 villa cells but **only 1 reliable + 2 indicative; 106 fallback**.
Computed gross yields span **4.1% (اللؤلؤة 600-900) → 11.5% (مريخ 0-400)** — a **3× spread**. At that
spread villa 6's income value ranges **~1.7M–4.8M** (unusable as a point). Structure DOES exist
(premium/large → ~4–5%; small/cheap → ~8–11%), so a stratified well-sampled calibration is viable —
but the current one is far too thin. **المعمورة (villa 6's own area) villa yield is NOT calibrated**
(gross=None — rent didn't match sale). Gross + net both in schema (opex ~20%).

**Conclusion.** The income cross-check is data-FEASIBLE (rent [PF] + sale [MoJ] both exist per area →
gross yield = PF-rent-median ÷ MoJ-sale-median is directly computable) but **NOT yet "strong"** — the
**yield is the make-or-break and is currently unreliable**. **First build task = a proper stratified
yield calibration** (extend Sprint 2.19: standalone-villa filter + size×stock strata + more PF rent
pulls + a18 area-name reconciliation), THEN the triangulation formula. This also explains the
point-estimate sensitivity: the value swings because the yield genuinely isn't pinned (measured 4–11%).

**Villa 6 income read (honest, uncalibrated):** gross rent ~16k/mo ÷ a plausible ~5.5–6.5% gross yield
(larger suburban villa) ≈ **~3.0–3.5M** (centre ~3.2M) — below the condition-blind comparison (3.8M),
which is the income check doing its job; pin precisely once المعمورة 600-900 villa yield is calibrated.
