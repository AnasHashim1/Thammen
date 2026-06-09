# BRIEF — §20.9 Cost-Triangulation (the durable R7 fix) — DRAFT for PO sign-off

**Date:** 2026-06-09 · **Lane:** Claude Code (drafted from the live recon + the bank report) · **Status:** 🔴 **Gate-2 DRAFT — awaiting Anas sign-off** (MOVES the headline on thin-pool over-anchors) · **Gate-1:** push awaits a separate explicit «go» · **Recon:** `docs/PHASE0_2p22p0_cost_triangulation_recon.md` (§1–§9) · **Design:** `docs/METHODOLOGY_cost_triangulation_v1.md` (multi-AI validated 2026-05-31).

> **One line.** Add an INDEPENDENT Cost-Approach value (land + depreciated building) as a SECONDARY method that triangulates the market headline: **confirm** it when convergent, **re-anchor it DOWN** only when the market is a thin-pool / dilapidated over-anchor. It is **subject-intrinsic (b9 age + b10 footprint) → fixes the live default no-rent over-anchor (Marikh) WITHOUT a user rent** — the decisive advantage over §6 income.

---

## 1. Why (R7, the middle case the levers miss)
The market comparison is blind to built-type / finish / condition / BUA. b4 handles the OPT-IN extremes (teardown ↓, new-luxury ↑); the **MIDDLE** has no lever — a thin-pool or worn villa over-anchors with nothing to move it. Live: **Marikh 54/541/6 = 5.4M** (thin-pool penthouse-median artifact; defensible ~3.0–3.4M). This is Anas's recurring «لماذا لا تتحرّك القيمة مع العمر/الحالة/البناء؟».

## 2. The calibrated cost model (PHYSICAL — satisfies §3.1; NOT the stale market-residual `construction_costs.json`)

**Cost value = `land_floor` + `BUA × building_rate`**
- **`land_floor`** = the shipped a21 `_villa_value_floor` — calibrated, **validated EXACT vs the bank** (engine 3,768/m² = bank 350/ft²=3,767/m²).
- **`BUA`** = `footprint × floors`. footprint ← b10 `max_buildable_footprint_m2` (or user/effective); floors ← user, **default G+1 = 2**.
- **`building_rate` = `RCN_new(finish) × retention(effective_age)`** — physical replacement cost × straight-line depreciation:

  | finish tier | RCN_new (QAR/m²) — PO ladder |
  |---|---:|
  | shell عظم | 1,200 |
  | ordinary | 2,200 |
  | good | 2,500 |
  | high | 3,000 |
  | luxury | 3,500 |

  `retention = clamp(1 − effective_age / ECONOMIC_LIFE, RESIDUAL_FLOOR, 0.98)`
  - `ECONOMIC_LIFE = 50y` · `RESIDUAL_FLOOR = 0.27` (shell-standing).
  - `effective_age = chronological_age + condition_penalty`: excellent/renovated **0** · good/very-good **+5** · average (default no-input) **+8** · fair **+15** · poor/dilapidated [cracks/settlement] **+25**.

**🎯 Calibration check vs the bank (V001 56/647/6):** luxury 3,500 × retention(age ~22–24, excellent → penalty 0) = 3,500 × (0.52–0.56) = **1,820–1,960 ≈ the bank's 1,900** ✓. The bank's single composite rate ≈ straight-line/50y with **no condition penalty (because EXCELLENT)** — and Anas's «متهالك → أقل بكثير» = the +25 penalty → ~0.27 floor → ~950 (luxury) / ~600 (ordinary). The model reproduces both ends.

## 3. Triangulation logic (mirror the shipped `_income_triangulation`; pure fn, no mutation)
Compute cost value, compare to the market comparison (`primary['value']`):
- **CONVERGENT** (|cost − market|/market ≤ ~20%) → **CONFIRM**: keep the market headline, raise confidence, narrow the range. *(V001: cost 3.6M vs market 3.8M = 5% → confirm. The bank report PROVED V001 must NOT be dropped.)*
- **COST UNDERCUTS** (market > cost by **> ~30%**) **AND** market path ∈ {thin, widened, preliminary} (NOT a clean reliable bracket) → **RE-ANCHOR DOWN**: present the honest reconciled range `[max(land_floor, cost) … market-muted]` with **cost as the informed lower anchor** (replacing §6 widen_down's raw land floor), `range_is_headline`, **MUC high**, + the §5 disclosure. *(Marikh: cost ~2.4M vs market 5.4M = +120% → re-anchor down.)*
- **Liquidity caveat (separate)** for old-premium thin-pool stock: achievable may be **10–15% below** fair MV (V001 unsold 5–6y; the bank's own forced-sale 3.24M) — a marketing/negotiation disclosure, distinct from the cost reconciliation.

**The >30% threshold is the safety rail:** it separates Marikh's **+120%** (fires) from V001's worst-case default-ordinary mis-estimate **+23%** (does NOT fire) — so the no-input default-finish assumption can never wrongly drop a luxury villa. The user's finish/condition input then refines cost UP toward convergence.

## 4. What MOVES (🔴 Gate-2 — NOT value-invariant on the default flow)
| subject | market | cost (model) | result |
|---|---:|---:|---|
| **54/541/6 Marikh** (thin, ordinary) | 5.4M | ~2.4M | **DROPS → honest range [~2.4M … 5.4M↓], MUC high** — the live un-anchoring, **no rent needed** |
| **56/647/6 V001** (widened, luxury-excellent) | 3.8M | ~3.6M (luxury input) / ~3.1M (default) | **CONFIRMED** (convergent) — NOT dropped; + liquidity caveat |
| **56/565/21 Abu Hamour** (clean reliable bracket) | 2.4M | — | **UNCHANGED** (clean bracket excluded) |
| **52/903/90** (apartment) | refusal | — | unchanged |

This is the **first default-flow headline fix that needs no user rent** (cost is subject-intrinsic). Live payoff is **NOT beta-gated** (vs all of §6).

> **⚠️ REFINEMENT — V001 treatment + the forced-sale rule (Anas, 2026-06-09; LOCKED; see recon §9):** the **forced-sale (جبري) is NOT a value signal — it is fair MV × 0.90, a convention** (`3.6M − 10% = 3.24M`; the bank employee quoted the rule before the file arrived). So the cost-triangulation **anchors on FAIR MV** (the valuer's `3.6M`, GT-1 inspected), **never on the forced figure**; any illiquidity discount comes from actual market BEHAVIOUR, disclosed separately. With no confirmed sale, V001's defensible value = a **RANGE ~3.2–3.6M** (best ~3.6M valuer; low ~3.2M illiquidity) → **V001 is a MILD convergent TRIM (engine 3.8M → ~3.6M), NOT a drop to 3.2M.** The big fixes stay **Marikh (5.4M → ~2.9M, thin-pool) + V002/V003 (2.4M → ~4.0M, new-premium)**.

## 5. RICS framing + §3.1 discipline (locked, from the design doc + multi-AI)
Market **PRIMARY**, Cost **SECONDARY-INDEPENDENT**, **reconcile NOT blend**. RCN = PHYSICAL (PO domain figures, the documented source §8 #3 needed) — independent of the MoJ median (§3.1). Disclosed-INDICATIVE (assumptions unverified, VPS 2/IVS 102), MUC high (VPGA 10), **Stage-5 sign-off** (VPS 5/IVS 105). Ships on the **b4 precedent** (a cost value on n=2 with wide-MUC + limited-sample disclosure) → does not strictly require n≥20.

## 6. LOCKED params (bank-calibrated)
RCN ladder (§2) · ECONOMIC_LIFE 50 · RESIDUAL_FLOOR 0.27 · the building-rate formula · land_floor = a21 (unchanged) · BUA = b10 × floors.

## 7. OPEN — PO decisions (recommendation in **bold**; multi-AI #54 checkpoint on the depreciation framing)
1. **Down-re-anchor threshold** — **>30%** (the V001/Marikh separator). Tunable.
2. **Re-anchor presentation** — **range-with-cost-as-informed-floor** (v1, honest, no invented point) vs pinning a central. *(Avoids the §3.1 "segment market premium over cost for ordinary stock" question — deferred to v2.)*
3. **Default no-input finish/condition** — **ordinary + average** (conservative; user refines). Confirm.
4. **Dilapidated 2nd anchor** — the +25 penalty → ~0.27 floor (≈950 luxury / ≈600 ordinary). Confirm the floor.
5. **condition_penalty bands** (§2) — confirm the +0/+5/+8/+15/+25 ladder.
6. **multi-AI #54** — route the depreciation-curve framing (straight-line/50y/residual + effective-age) to GPT/Gemini before build? *(Recommend: yes — it is a methodology-framing call; Claude.ai lane.)*

## 8. Implementation + validation (post sign-off)

> **Grounded by `docs/METHODOLOGY_DRC_qatar_v1.md`** (web research + RICS + the valuer-calibration proof: the model reproduces TD 93317 to ~1%). Two requirements folded in: **(i)** the report displays BOTH **القيمة السوقية (MV)** and **القيمة الجبرية = MV × 0.90** at the end (labelled a CONVENTION, not a signal — Anas 2026-06-09); **(ii)** the DRC BUA = the **actual/confirmed** built-up area (user-entered, or a typical built-ratio), **NOT** the b10 max-buildable footprint (a legal CEILING that over-states the building — the §7 caveat). Soil/geotech (sabkha/karst foundation premium) = a v2 GIS factor; default = Simsima-rock baseline (the land value already prices most of the soil effect).
- New pure `_cost_triangulation(primary, cost_value, land_floor, asset_type, dispersion_gated, market_path)` mirroring `_income_triangulation`; new `_cost_approach_value(...)` building the cost from b9 age + b10 footprint + the §2 model; wired in the b4 region (mutually exclusive with teardown/luxury/income_led). `api.py`/`index.html` notes only.
- **Validation (E14, real engine):** V001 → confirmed ~3.6–3.8M; Marikh → range-headline [~2.4M…5.4M↓]; 56/565/21 → 2.4M unchanged; 52/903/90 refusal. Isolated tests (the §2 model + the §3 trigger + the V001-convergent guard) + DoD + R14 + live two-lane smoke (#61).
- **Gates:** 🔴 Gate-2 = this brief signed; 🔴 Gate-1 = explicit «go» before the `git subtree push`.
