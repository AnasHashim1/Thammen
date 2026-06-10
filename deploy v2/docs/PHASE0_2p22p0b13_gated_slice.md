# PHASE-0 RECON — Sprint 2.22.0b.13 (§20.9 GATED slice) — 🔴 STANDING HALT (a premise overturned)

> **READ-ONLY. No engine change, no deploy. Engine stays b12 / Heroku v181.** Mandated by
> `BRIEF_Sprint2p22p0b13_gated_slice_SIGNED.md` §5 (recon FIRST; **STANDING HALT** on premise break).
> **Outcome:** **Lever 1 (TRIM) = SOUND ✓; Lever 2 (UP-lift) = PREMISE BROKEN 🔴 — HALT-and-report.**
> Method: traced all 8 cases through the **real b12 engine** (`.b13_recon.py`) + computed the brief's lever
> predicates by hand using the engine's measured land_floor / geometry / system-age. Facts **measured✓**.

## §1 — The 8-case trace (measured✓, b12 / v181, live GIS)

| case | market | method | sys_age | land_floor | maxfp | DRC cost @system | DRC cost @actual | brief lever |
|---|---|---|---|---|---|---|---|---|
| AbuHamour 56/565/21 (anchor) | 2,400,000 | **bracket** | 15 | 1,700,100 | 270* | 2,194,070 (ord) | — | none (bracket-excluded; no user age) |
| Marikh 54/541/6 (anchor) | 5,400,000 | thin | 17 | 1,851,260 | 311 | 2,378,094 (ord) | — | **cost_reanchor_down (b11, 128%)** — unchanged |
| Maraad 55/296/13 (anchor) | 2,600,000 | thin | 17 | **2,674,350** | 630 | 3,741,570 (ord) | — | none (**land-anchored** land>market; old) |
| Apt 52/903/90 (anchor) | None | refusal | — | — | — | — | — | none (not villa) |
| V001 56/647/6 BARE | 3,800,000 | widened | 17 | 2,456,736 | 391 | 3,119,090 (ord) | — | none (**no user age** → trim withheld) |
| **V001 +age25+lux+exc** | 3,700,000 | widened | 17 | 2,456,736 | 391 | 3,847,679 | **3,510,481** | **TRIM (under 5.4%) → leads ~3.51M ✓** |
| **V002 56/565/10 BARE** | 2,500,000 | **bracket** | 0 | 1,700,100 | 198* | 2,263,592 (ord) | — | **none — lift does NOT fire** |
| **V003 56/565/12 BARE** | 2,400,000 | **bracket** | 0 | 1,700,100 | 198* | 2,263,592 (ord) | — | **none — lift does NOT fire** |

*maxfp is the per-villa share on a shared 2-villa parcel (b10.2).

## §2 — Lever 1 (convergent-TRIM) — **SOUND ✓, build it**

- **V001 + user `building_age_years=25` + `is_luxury` + `condition=excellent` → actual-age DRC = 3,510,481**
  (bua 602, rcn 3500, eff_age 25, retention 0.50), market 3.70M → undercut **5.4% ≤ 30%** → TRIM leads
  **~3.51M** — inside the valuer's 3.6M band (TD 93317; brief §2 "±band"). ✓
- **Anchors protected (byte-identical), three independent guards each verified:**
  - **user-age gate** (`age_source == 'user'`, measured at `evaluate_unified.py:3922`): bare evals never trim.
    ⚠️ **Refinement (not a break):** `building_age_years` can be **auto-derived from imagery** (`:3924-3970`,
    `age_source='gis_imagery'`) — so the gate MUST key on `age_source=='user'`, NOT on `building_age_years is not None`.
  - **clean-bracket exclusion** — AbuHamour/V002/V003 are `comparison_bracket` → trim never eligible (the
    bracket cost being 9-10% under market is irrelevant; the path is excluded).
  - **land-anchored exclusion** — Maraad land 2.674M > market 2.6M → excluded.
- **TWO costs needed:** `cost_reanchor_down` keeps the **system-age** cost (b11 immunity — §20.45); the TRIM
  needs an **actual-age** cost at `max(user_actual, system)`. Both go through `_cost_approach_value`; the
  wiring (`:4624`) currently computes only the system-age cost → the build adds the actual-age cost when
  `age_source=='user'`. Bands are disjoint at 30% (reanchor `>0.30`, trim `≤0.30`; both `cost<market`).
- **finish:** the wiring derives finish from `is_luxury` only → `luxury`(3500) reaches the V001 band; a
  distinct `'high'`(3000) input does **not** exist (no api.py field — brief says api.py UNTOUCHED). `is_luxury`
  + the ladder + the actual age reach ~3.5–3.6M, so **no finish input is required** (brief "finish high" ≈ `is_luxury`).

## §3 — Lever 2 (UP-lift) — 🔴 **PREMISE BROKEN — DO NOT BUILD**

**The brief (§1 row 2 / §3 / §5.2) expects the DRC cost to lift V002/V003 toward their realized ~4.0M.
Measured, it cannot:**

- **V002/V003 DRC cost = 2.26M (ordinary) / 2.6M (luxury)** — *below* the 4.0M sale and ≈ the 2.5M market.
  The lift fires only when `cost > market by >30%`; here cost is **−10% to +4%** of market → **the lift never fires.**
- Even forced, the lift's ceiling = the cost (~2.6M; ~3.46M at a generous doubled footprint) — **never 4.0M.**
  A 305 m²-BUA villa has a replacement cost of ~2.6M; the **4.0M sale is a market premium** (premium-new
  scarcity in Abu Hamour 565) the cost approach does **not** model.
- ⇒ The new-premium under-anchor (engine 2.5M vs sold 4.0M, −40%) is a **comparable-pool / GT-calibration
  problem — the same `luxury_new` E4 stratum that is n=0 locally (§20.27, B-2 Lever-1, PARKED on n≥20).**
  The cost approach is the **wrong tool**: its value (~2.6M) is *below* both the market and the sale.
- **Knife-edge danger:** the lift predicate also matches **Maraad** (old thin: cost 3.74M > market 2.6M by
  **44%**) — saved *only* by the new-stock gate. The lift is structurally one gate away from moving an old,
  land-anchored anchor. Fragile.

## §4 — The other parameters (D-1 floor / ladder / cliff-flag) — sound, support Lever 1

- **0.31 finish-floor (D-1):** byte-identical on all anchors (Marikh retention 0.50 ≫ 0.31; default finish
  ordinary → 0.27). Bites only on dilapidated-luxury (eff_age > ~34) — a tail; keep, keyed on finish.
- **Ladder (excellent −2 / renovated −3):** default condition = average (penalty 8) → no-condition flows
  byte-identical. Keep.
- **Cliff-flag R3 (value-invariant disclosure):** sys_age 15-17 / survey 2009-2011 fires on AbuHamour/Marikh/
  Maraad/V001; sys 0 (2026 re-survey) fires the inverse on V002/V003 → **62% of villas** get the "enter actual
  age" nudge (matches E24 / recon). Independent of the levers. Keep. **Frontend → R14.**

## §5 — Structural checks (brief §5.3/§5.4, measured✓)

- `_cost_retention(effective_age)` is shared (b11 + levers via `_cost_approach_value`); making it finish-keyed
  is byte-identical on default finish (ordinary → 0.27). ✓
- refineScreen age input → `bd.building_age_years` (`index.html:894`); `#refineScreen` (`:424`) is the R3 nudge home. ✓
- band disjointness at exactly 30%: reanchor `>0.30`, trim `≤0.30`, both `cost<market`; lift `cost>market` —
  disjoint. ✓ (but lift is misfounded per §3.)

## §6 — RECOMMENDATION (for PO — Gate-2 reshape)

**Ship a RESHAPED b13 = Lever 1 (convergent-TRIM) + the 0.31 finish-floor + the condition-ladder + the
cliff-flag R3 disclosure.** **DROP Lever 2 (UP-lift)** — measurement shows the DRC cost is *below* the
V002/V003 sale, so a cost-lift cannot reach it; the new-premium under-anchor belongs to **B-2 GT-corpus
calibration (PARKED n≥20)**, not the cost approach. This keeps every sound, measured lever and removes the one
the data overturns. Reshaped b13 is **value-affecting on V001-class widened/thin villas WITH a user actual age
only** (the 4 anchors stay byte-identical); honest residual = the trim is dormant on no-age traffic (E24 / the
R3 nudge is the activation surface).

**HALT per the brief's STANDING HALT — awaiting PO confirmation of the reshaped scope (Lever-1-only b13)
before building (HARD GATE 2: dropping a signed lever is a methodology change).**

---
*Recon 2026-06-10. READ-ONLY (`.b13_recon.py`, regenerable). Engine UNCHANGED b12/v181. Owner: Anas.*
