# PHASE-0 §5 recon — §20.9 Cost-Triangulation (the durable R7 fix)

**Date:** 2026-06-09 · **Lane:** Claude Code (read-only, no engine change, no push) · **Engine at recon:** `thammen-sprint2p22p0b10p2-multiqars-footprint` / Heroku v179 · **Trigger:** PO «ابدأ recon §20.9» (session-open routing).

> **One-line verdict.** Most of the cost-approach machinery **already exists**, and the two missing INPUTS (BUA, effective age) were **just shipped** (b10 footprint ✓ + b9 age floor ✓). What is genuinely unbuilt is the **headline mechanism** — a `_cost_triangulation` that lets a materially-divergent INDEPENDENT cost value re-anchor an over-anchored market median **DOWN** (the V001/Marikh middle-case, = Anas's recurring «لماذا لا تتحرّك القيمة مع العمر/الحالة؟»). That is **🔴 Gate-2** + needs a **signed brief** on the §8 parameters + obeys the **§3.1 calibration discipline**. The existing `construction_costs.json` is a **stale anti-pattern** (market-residual) and must NOT be reused.

---

## 1. What we are trying to fix (R7, the middle case)

The market comparison returns a pool central-tendency blind to built-type / condition / BUA. **Extremes are already handled** (b4, opt-in): `teardown` → land − demolition (DOWN); `new`+`is_luxury` → DRC (UP). **The GAP = the MIDDLE**: an OLD ordinary/good villa where the comparison over-anchors with **no lever to move it** — the §20.36 honest residual, live on:

| subject | market headline | defensible | land floor (a21 ✓) | nature of over-anchor |
|---|---:|---|---:|---|
| **54/541/6 Marikh** (plain ~20y, thin pool) | **5.4M** | ~3.0–3.4M | ~1.85M | **WILD** — thin-pool penthouse-median artifact |
| **V001 56/647/6 المعمورة** (premium ~25y, sticky ask) | 3.8M | 2.63–3.2M (analyst) | 2.46M | **MILD** — old-stock economic obsolescence |

This is the literal thread of §20.43/§20.44 (the villa-6 episode) + the §20.36 b4 carry-forward («the 10-Year-Rule DOWN re-anchor fires ONLY on explicit `teardown`, not old-age+good-condition → that is the next R7 step»).

---

## 2. EXISTING infrastructure (the big finding — much is built, inputs just shipped)

| piece | where | state | relevance |
|---|---|---|---|
| **land component** | `_villa_value_floor` `evaluate_unified.py:1553` (a21) | ✓ shipped, **calibrated, validated 0.016% vs the Al Manara bank report** (§20.43) | the Land half of `Land + Depreciated Building` is **DONE** |
| **BUA input — footprint** | `_geometry_footprint` `:769` (b10) | ✓ shipped (max-buildable; multi-QARS-aware b10.2) | the missing BUA driver — **now available** (the §20.9 enabler) |
| **effective-age input** | `_building_age_estimate` `:2216` (b9, QARS `SURVEYED_DATE` floor) | ✓ shipped, NEVER fed to `building_age_years` | the depreciation driver — **now available** (a FLOOR; reliability = E22 caveat) |
| **cost cross-check (DRC)** | `_build_cost_crosscheck` `:1630` ← `ev.replacement_cost` | exists but **`role_ar` = «تأكيد منهجي — لا يدخل في القيمة النهائية»**; **BUA-gated** (None on the default no-building-input path) | the §20.9 delta = flip this from "display-only" → "secondary that CAN triangulate" + auto-construct it on the default path |
| **DRC UP lever** | b4 luxury-new `:4540–4583`, const `:4897–4914` (`LUXURY_CONSTRUCTION_QAR_PER_M2=3500`, `PENTHOUSE×2.5`) | ✓ shipped, **opt-in**, calibrated n=2 (V002/V003), wide MUC + limited-sample disclosure | proves a cost value CAN ship the headline on **n=2** when **opt-in + disclosed** — the precedent for the middle case |
| **DRC DOWN lever** | b4 teardown `:4505–4538`, const `:4872–4895` (`DEMO 240/m²`, floor 100k, cap 150k) | ✓ shipped, **opt-in** (`condition=teardown` only) | the down-anchor exists but **only for teardown**, not old-good |
| **triangulation TEMPLATE** | `_income_triangulation` `:4963` (b6/b7/b8) | ✓ shipped — already takes a `cost` arg, uses `cost.value` as the **upper rail** (`×1.05`); modes `income_led` + `widen_down` | the cost-triangulation should **mirror this** (a `cost_led` / cost-anchored widen-down) — pure fn, no mutation |

**No `_cost_triangulation` / `cost_led` exists** (grep clean) — the headline mechanism is genuinely unbuilt.

---

## 3. The DATA / GOVERNANCE blockers (honest)

### 3a. §3.1 calibration discipline — the existing `construction_costs.json` is the WRONG method
`construction_costs.json` (root, **tracked, stale 2026-05-08, pre-dates the 2026-05-31 design doc**) is built by `calibrate_construction_cost.py:156–172`: `building_value = villa_price − (plot × MoJ land median)` → `cost_per_bua = building/(plot×0.6)`. **This is exactly the trap `METHODOLOGY_cost_triangulation_v1.md` §3.1 forbids** (both GPT + Gemini flagged it): a market-residual cost (a) **kills independence** (cost = market − land → no diagnostic power) and (b) **imports the comparison's blindness** (luxury-skewed districts inflate the "average" cost). → **Do NOT reuse this table.** The DRC must be a **PURE physical estimate** (RCN − market-derived depreciation), with the Market/DRC ratio observed **separately, by segment**.

### 3b. Open Decision #4 (design doc §8) — the curated ground-truth sample = BLOCKER-as-written
The doc says «cost-approach implementation is **BLOCKED** until [the curated GT sample is] resolved». Current corpus = **n=2 GT-2 + 1 GT-3** (`calibration/gt_corpus.local.json`) → **MOTIVATES, does NOT calibrate** (the same n≥20 wall as B-2 / §20.27). **BUT** the **b4 precedent breaks the strict reading**: the luxury-new DRC shipped on **n=2** as **opt-in + wide-MUC + «معايَر على صفقات محدودة» disclosure**. So a **disclosed-indicative** cost-triangulation is a PO-callable ship path that does not strictly require n≥20 — see §5.

### 3c. PO parameter decisions (design doc §8 #2/#3) — Gate-2, unresolved
Construction rate **source + cadence** (PO domain: ordinary **2,000–2,500**, luxury 3,500–4,000 QAR/m²; «pending documented source + annual review»); **depreciation-curve shape** (market-derived effective age — NOT a flat `Age>10⇒building=0`); the **Market/DRC segment-ratio** method; the **trigger** (divergence threshold) + **re-anchor target** (cost value vs a land-floor band).

---

## 4. Empirical feasibility — hand-proof on the two live over-anchors

DRC value ≈ `land_floor (a21 ✓) + BUA × ordinary_rate × (1 − depreciation)`. BUA ≈ b10 footprint × floors (G+1 = 2).

- **Marikh 54/541/6** (the WILD artifact): land ~1.85M + building [~475 BUA × ~1,500 depreciated ≈ ~0.7M] ≈ **~2.55–3.0M** vs market **5.4M** → **DECISIVE down-triangulation** (matches §20.44's hand-proof «~2.8–3.0M vs blind 5.4M» + the analyst 3.0–3.4M). **This is the case cost-triangulation nails.**
- **V001 المعمورة 56/647/6** (the MILD sticky case): the bank's DRC = land 2.46M + depreciated building 1.14M = **3.60M** ≈ market 3.8M (**CONVERGENT**) — yet the analyst clearing is **2.63–3.2M**. ⇒ for OLD-PREMIUM stock the **DRC over-states** (economic obsolescence / sluggish market) → a naive cost-vs-market triangulation does NOT fix V001; it needs the **§3.1 Market/DRC segment ratio < 1** OR composes with the **B-2 land-floor finish-band** (the residual-report Lever-2 sim → 2.95M, in-band). **Honest: cost-triangulation alone is necessary-not-sufficient for V001.**

**Verdict:** cost-triangulation is the right GENERAL mechanism and is **decisive for the thin-pool wild over-anchor** (the most common + most visible failure); for old-premium sticky asks it must be paired with a segment ratio or B-2.

---

## 5. Recommended path (for the brief)

A pure `_cost_triangulation(primary, cost, land_floor, asset_type, ...)`, mirroring `_income_triangulation`:
1. **Auto-construct the cost value on the default path** — BUA = b10 footprint × assumed floors (G+1) × ordinary rate × depreciation(b9 age floor). (Today `cost=None` without building input → no triangulation fires.)
2. **`cost_led` / cost-anchored widen-down**: when the market method is THIN/widened/uncertain (not a clean reliable bracket) **and** the cost value materially undercuts it (over-anchor), re-anchor the headline DOWN toward a reconciled `[land_floor … cost]` band + **range_is_headline** + **MUC high** + the §5 disclosures (assumptions unverified, indicative, Stage-5 sign-off). Mutually exclusive with b4 teardown/luxury + income_led.
3. **Reconcile, do NOT blend** (design §2): present market + cost + spread + range; convergence→confidence, divergence→widen+flag.
4. Ship with the **b4 disclosure discipline** (wide MUC + limited-sample + «معايَر على صفقات محدودة») → a PO-callable disclosed-indicative ship that doesn't strictly require n≥20.

**This is 🔴 Gate-2 (the headline MOVES) + needs a SIGNED Claude.ai brief** resolving §8 (#2 ordinary rate + source, #3 depreciation curve + divergence trigger + re-anchor target, the Market/DRC ratio for old-premium). The **inputs + template + land floor are all shipped** → once the brief lands the build is bounded (mirror `_income_triangulation`).

---

## 6. Housekeeping flags (non-blocking)
- **Stale worktrees** `competent-ishizaka-ac9063` + `pensive-elgamal-dba8b2` (`0f34a6f` = "Sprint 2.16.15", **2026-05-19, 275 behind master, abandoned**) — recommend `git worktree remove` (no active parallel work; the cost-cost files in them are just the committed `017a259` copies).
- **`construction_costs.json` + `calibrate_construction_cost.py`** — stale market-residual artifacts (§3a); either delete or RE-AUTHOR per §3.1 (pure RCN) before any cost build references them.
- The `.td93317_text.txt` OCR is **empty** (page markers only); the bank numbers live in §20.43 (land 2,456,345 / depreciated building 1,143,800 / total 3,600,145).

---

## 7. Carried forward
- **Ball = Claude.ai drafts the §20.9 cost-triangulation brief** (resolves design-doc §8 #2/#3 + the Market/DRC segment ratio; multi-AI #54 on the depreciation-curve framing). Then CC builds (bounded — mirror `_income_triangulation`), 🔴 Gate-2 sign-off + Gate-1 push.
- **Live payoff is NOT beta-gated** (unlike income work) — cost is subject-intrinsic (b9 age + b10 footprint), needs no user rent → the default no-rent Marikh/villa-6 over-anchors get fixed live. **This is the §20.9 advantage over §6.**
- B-2 (condition axis) composes with this for the old-premium V001 case (land-floor finish band). Still PARKED n≥20 as a *coefficient* fit; the cost track ships disclosed-indicative on the b4 precedent.

---

## 8. PO PARAMETER UPDATE (2026-06-09) — construction-cost ladder (resolves §8 #3 rate + source)

Anas (PO, builds/brokers) stated the Qatar villa construction-cost ladder — **a PHYSICAL RCN estimate, independent of the MoJ median → SATISFIES §3.1** (the documented source the methodology doc §8 #3 required; the stale market-residual `construction_costs.json` is now superseded):

| finish tier | RCN new (QAR/m²) |
|---|---:|
| **عظم (structural shell, unfinished)** | **~1,200** (baseline) |
| ordinary turnkey | ~2,200 |
| good | ~2,500 |
| high | ~3,000 |
| **luxury** | **~3,500** |

(CC reading: figures are **turnkey totals** by finish quality, shell = the low end; pending PO confirm of the shell-vs-total framing.) **Reconciles with the shipped b4 `LUXURY_CONSTRUCTION_QAR_PER_M2 = 3500`** ✓ and the design-doc ordinary 2,000–2,500 / luxury 3,500–4,000.

**Illustrative hand-proof (depreciation % = CC assumption, the remaining unknown):**
- **Marikh 54/541/6** (ordinary ~20y): land 1.85M + [BUA ~450 × (2,200 × ~0.65 dep) ≈ 644k] ≈ **~2.5M** vs market **5.4M** → cost-triangulation **decisive** (in the 2.5–3.0M defensible band).
- **V001 56/647/6** (luxury ~25y renovated): land 2.46M + [BUA ~500 × (3,500 × ~0.72 dep ≈ 2,520 ≈ the bank's ~2,380) ≈ 1.26M] ≈ **3.7M ≈ market 3.8M** → **CONVERGENT** → confirms §4: old-premium DRC over-states (economic obsolescence) → needs the Market/DRC segment ratio (or B-2 land-floor band).

**Still open for the brief (the remaining physical + reconciliation params):**
1. **Depreciation curve** — building value vs *effective* age (market-derived; NOT a flat Age>10⇒0). The bank's V001 ≈ 32% at ~25y is one anchor point.
2. **Default finish tier** for the no-input default flow (ordinary ~2,200? or the shell 1,200 as a conservative floor?).
3. **Divergence trigger + re-anchor target + the Market/DRC segment ratio** for old-premium.

---

## 9. CERTIFIED-VALUER REPORT CALIBRATION (TD 93317, AUTHORITATIVE — read 2026-06-09)

> **Framing correction (Anas, 2026-06-09):** this is **NOT "the bank's" number** — it is a report by a **certified valuer (مثمن معتمد), Al Manara Real Estate W.L.L, accredited to Qatar International Islamic Bank**. ⟹ it is a **GT-1 (valuer-signed, Stage-5) authority** — the project's FIRST GT-1 datapoint (was logged GT-3 asking; this UPGRADES it).

Read the certified-valuer report (شهادة تثمين 93317, commissioned by QIIB, 2026-06-07) for **56/647/6 = V001**. The Cost-Approach table (p02–p03; p04 deed = bought 2002 → ~24y; p08–p13 = photos confirming excellent/luxury):

| component | bank figure |
|---|---|
| plot | 652 m² (7,018 ft²) |
| land rate | 350 ر.ق/ft² = **3,767/m²** (= engine land floor **3,768** ✓ EXACT) |
| land value | 2,456,345 |
| **BUA (estimated)** | **602 m²** (G+1 = دورين; conf. my ~587 inference) |
| **building rate** | **1,900 ر.ق/m²** — a SINGLE composite rate; depreciation+condition **embedded** (no separate dep line) |
| building value | 1,143,800 |
| **total FAIR** | **3,600,145** · **forced-sale (90%): 3,240,145** |
| age / condition | «حوالي 18 سنة» / **«ممتاز»** (excellent), regular maintenance |

**Depreciation anchor (authoritative):** an **~18–24y EXCELLENT-condition LUXURY** villa → building **1,900/m²** ≈ **54% of luxury-new 3,500**. The bank uses a **condition-and-age-adjusted building rate directly** (NOT RCN×depreciation%). PO: a متهالك villa (cracks/settlement/irregular maintenance) → **"much lower"** (~1,000–1,200, a 2nd anchor the brief still needs).

**🔴 RE-EXAMINED & LOCKED — fair MV vs forced-sale (Anas, 2026-06-09); read settled after two refinements (Rule #36 — I oscillated; this is the stable position):**
- **The forced-sale (جبري) 3,240,145 is NOT an independent signal — it is `fair MV × 0.90`, a market CONVENTION (عرف سائد).** The bank employee quoted the flat 10% BEFORE the file arrived; `3,600,145 − 360,000 = 3,240,145` confirms the mechanical haircut. ⟹ the earlier «my ~3.2M ≈ the forced-sale = verified convergence» leaned on a **mechanical artifact, not market evidence — WITHDRAWN.**
- **The authoritative value = the certified valuer's FAIR MV `3.6M`** (GT-1, licensed, **INSPECTED** — the report carries interior/exterior photos; land 2.46M + depreciated building 1.14M). **This is the cost-triangulation anchor.**
- The project's prior **~3.0–3.2M** desktop read (sticky 5–6y ask, buyer-pull-to-land) is a **behaviour-based illiquidity CAUTION (GT-3-ish, weaker than the GT-1)** — it survives as the **LOW of the range, NOT a target**.
- **No confirmed sale (GT-2) → defensible value = a RANGE ~3.2–3.6M; best point ~3.6M (valuer), low ~3.2M (illiquidity, disclosed separately).** The engine's **3.8M is ~5% high** (= the rejected ask).
- ⟹ **V001 = a MILD convergent TRIM (3.8M → ~3.6M, toward the valuer/cost), NOT the big drop to 3.2M** the prior pass claimed. The BIG §20.9 fixes stay **Marikh 5.4M → ~2.8–3.0M** (thin-pool, cost ≪ market) + **V002/V003 2.4M → ~4.0M** (new-premium, cost ≫ market).

→ **Brief RULE (NEW, locked):** the cost-triangulation anchors on **FAIR MV** (the valuer / cost-approach number); **forced-sale is NEVER a value signal** (it is fair × ~0.90 by convention); any **illiquidity discount comes from actual market BEHAVIOUR, disclosed separately**, never from the forced figure. Physical depreciation model unchanged = condition×age building-rate on the valuer's **1,900** + new-luxury **3,500** + dilapidated floor **~1,000–1,200**.
