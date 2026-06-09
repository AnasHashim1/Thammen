# METHODOLOGY — Qatar Cost-Approach (DRC) + the complete valuation stack (v1, research-grounded)

**Date:** 2026-06-09 · **Lane:** Claude Code (web-researched + due diligence, per Anas «افعل الأصوب») · **Status:** 🔴 Gate-2 DRAFT — settled methodology for PO sign-off · **Validation:** reproduces the certified-valuer report TD 93317 to ~1% (§7) · **Feeds:** `BRIEF_cost_triangulation_R7.md`, `METHODOLOGY_cost_triangulation_v1.md` (the 2026-05-31 multi-AI design — this doc grounds its §3 cost parameters).

> **Settles the §20.9 question:** how to compute a **replacement-cost factor (معامل الإحلال) for Qatar** — accounting for construction cost, **soil/geotechnical** conditions, and depreciation — within the RICS DRC framework, and how it sits in the complete three-method stack.

---

## 1. Where the Cost Approach (DRC) fits — RICS is explicit (it is NOT the villa headline)

**RICS / IVS rule (researched, primary): the cost approach / DRC is the "method of last resort" — it is NOT to be used as the primary basis where there is an active market with comparable sales.** Qatar villas trade actively (MoJ registry) → **Market Comparison stays PRIMARY**; DRC enters only as a **SECONDARY cross-check / triangulation** (a sanity bracket + a blindness-detector for built-type/condition/BUA the market median can't see). This is exactly the `METHODOLOGY_cost_triangulation_v1.md` §2 design (market primary, cost secondary-independent, reconcile-NOT-blend), now confirmed against the standard.

**The complete Thammen stack:**
1. **Market Comparison (PRIMARY)** — MoJ comparables, built-type-stratified (a12) + area-reconciled (a18) + dispersion-gated honest-range (a10/a14). The headline for traded villas/land.
2. **Income (for let assets)** — DCF/yield (existing; §6 triangulation).
3. **Cost Approach / DRC (SECONDARY)** — this doc. A second independent estimate that brackets + triangulates the headline.

## 2. The DRC formula (RICS/IVS, researched)

```
DRC value = Land value (market, present use) + [ RCN − Depreciation ]
```
- **Land** = market value of the plot (we already have it: a21 `_villa_value_floor`, GIS↔MoJ, validated EXACT vs the valuer — §7).
- **RCN** = Replacement Cost New of the **MODERN EQUIVALENT** asset (substitution: a buyer pays no more than the cost to acquire an equal-utility modern property) — NOT the cost to replicate the exact old building. Includes construction + soft costs (fees/permits) + site/foundation works.
- **Depreciation** = three kinds (RICS): **(a) physical deterioration** (wear; condition-driven), **(b) functional/technical obsolescence** (dated layout/systems), **(c) economic/external obsolescence** (market doesn't pay for old premium / location decline). DRC writes the RCN DOWN by all three.

## 3. Qatar RCN — the construction-cost ladder (PO figures, web-validated)

PO (Anas, builds/brokers) turnkey-all-in build cost, QAR/m² of BUA, **validated** against 2025 sources + back-calculated from the valuer (§7):

| finish tier | RCN_new (QAR/m², turnkey all-in) |
|---|---:|
| عظم (structural shell only) | ~1,200 |
| ordinary | ~2,200 |
| good | ~2,500 |
| high | ~3,000 |
| **luxury** | **~3,500** |

**Web cross-check (2025):** Qatar villa turnkey mid-range **QAR 2,500–3,500/m²**, high-end/bespoke 5,000–8,000 (the bespoke/developer-margin end, ABOVE the modern-equivalent RCN we need); basic ~QAR 1,676 ($460). The **Turner & Townsend Doha all-asset average US$2,631/m² (~9,580 QAR)** is **NOT villa** — it is weighted by towers/hotels/institutional and must NOT be used for a villa RCN. The PO ladder = the **contractor cost-to-build**, the correct DRC "modern equivalent" basis; it sits below the inflated quotes and is **confirmed by the valuer's implied RCN** (§7). Soft costs (design/engineering/permits, +7–12%) are treated as **already embedded** in the turnkey ladder (owner all-in basis) — do NOT double-add.

## 4. The soil / geotechnical replacement factor (معامل الإحلال — the Qatar-specific element)

**Researched Qatar geotechnics:**
- **Simsima Limestone** is the **main founding stratum across almost all of Qatar** (surface-hardened chalky/dolomitic limestone) — generally **good bearing → standard shallow/raft foundations** for villas. BUT complex weathering + **karst dissolution cavities** (limestone+gypsum dissolved by acidic groundwater → sinkholes, voids at depth) + the underlying **Midra Shale / gypsum** (low-strength, heterogeneous) → localized risk.
- **Sabkha** (coastal salt flats): weak, collapses when wet, **salt-aggressive** to concrete; needs **soil replacement (إحلال التربة)** + stabilization (cement/lime) / micro-piling + sulphate-resistant concrete → a **real foundation-cost premium**.

**Correct DRC treatment (avoids double-count):**
1. **Soil's effect on LAND is already captured by the market land value** (a21) — a sabkha / karst-risk plot sells for LESS than good-rock land in the same area; the MoJ land median embeds buildability.
2. **Soil's effect on the BUILDING is the foundation component of the RCN** — a villa on sabkha costs MORE to build (soil replacement + special foundations) than one on Simsima rock. These are INDEPENDENT (land down AND build-cost up); both legitimately apply.
3. **Practical AVM rule:**
   - **DEFAULT = the typical Qatar founding case (Simsima rock, standard foundations) → baseline RCN, soil factor = 0.** Correct for the large majority of inland Doha residential (incl. المعمورة / V001 — the valuer used a standard basis).
   - **A SOIL/ZONE factor** (a future GIS refinement, v2): for mapped **sabkha / coastal / karst** zones, add a foundation premium to the RCN (order **+5–15% on the building**, or a fixed QAR/m²-of-plot soil-replacement allowance) — but since the LAND value already discounts those plots, this is a **second-order** adjustment, NOT a v1 blocker. Flag it; do not invent a per-plot geotech survey Thammen cannot run.

→ **معامل الإحلال = a foundation/site multiplier on the RCN, default 1.0 (Simsima rock), raised only for sabkha/karst zones.** The dominant soil signal for value already lives in the land price.

## 5. Depreciation — economic life + condition-driven effective age

**Researched economic life:** RC (reinforced-concrete) residential ≈ **40–47 years** in practice (up to 60 for top-quality); MEP components ~20y; **GCC harsh climate (heat/salt/humidity) shortens durability** vs temperate; no comprehensive GCC dataset → practitioners adjust CIBSE/BOMA tables.

**Model (physical depreciation, straight-line, condition-modulated — reproduces the valuer, §7):**
```
retention = clamp( 1 − effective_age / ECONOMIC_LIFE , RESIDUAL_FLOOR , 0.98 )
building_rate = RCN_new(finish) × retention
effective_age = chronological_age + condition_penalty
```
- **ECONOMIC_LIFE = 50y** (calibrated: it reproduces the valuer's 1,900 — §7; within the 40–60 researched band, GCC-tempered toward the middle by the residual floor). PO decision: 45 vs 50.
- **RESIDUAL_FLOOR = 0.27** (a sound shell retains value even when very old).
- **condition_penalty** (effective age vs chronological — Anas's «الحالة الإنشائية» axis): excellent/renovated **0** · good/very-good **+5** · average (default no-input) **+8** · fair **+15** · poor/dilapidated [cracks / settlement / concrete subsidence] **+25** (→ drives toward the residual floor — Anas's «أقل بكثير»).
- **Functional + economic obsolescence** (the other two RICS depreciations) = the **old-premium market discount** — the gap between replacement-cost-fair and what old premium actually clears at. This is **market-derived (H-A), calibrated at n≥20**; until then it is disclosed as a RANGE, not a coefficient (see §6).

## 6. Reconciliation + the report's two values (RICS reconcile-not-blend)

**Headline = Market Comparison (primary).** The DRC value triangulates it:
- **cost ≪ market** (thin-pool artifact — Marikh: cost ~2.3M vs market 5.4M) → **re-anchor DOWN** to a `[cost-floor … plain-comp]` honest range, MUC high.
- **cost ≫ market** (new-premium under-anchor — V002/V003: cost ~4.0M vs market 2.4M) → **lift** toward cost.
- **cost ≈ market** (V001: cost 3.6M vs market 3.8M) → **confirm / mild trim** toward the cost/valuer (~3.6M); the **old-premium illiquidity** (it clears lower, ~3.2M in a slow market) is the functional/economic obsolescence — **disclosed as a behaviour-based caveat / range LOW**, NOT a coefficient (n≥20).

**🆕 Report output (Anas, 2026-06-09): present BOTH values at the END of the report**, exactly like the certified valuer:
- **القيمة السوقية (Market Value)** — the headline estimate.
- **القيمة الجبرية (Forced-sale Value) = Market Value × 0.90** — labelled as a **convention (a standard ~10% quick-sale haircut), NOT an independent estimate**. (The bank's own 10%-off rule; do not treat it as a market signal — §RULE below.)

**🔴 RULE (locked):** the cost-triangulation anchors on **fair Market Value** (the cost/valuer figure); **the forced-sale value is NEVER a market-value signal** (it is MV × ~0.90 by convention); any illiquidity discount comes from actual market **behaviour**, disclosed separately.

## 7. Calibration proof — the model REPRODUCES the certified valuer (TD 93317, V001) to ~1%

| component | our model | certified valuer | match |
|---|---:|---:|---|
| Land | 652 m² × 3,767/m² = 2,456,345 | 652 m² × 350/ft² = 2,456,345 | **EXACT** |
| RCN new (luxury) | 602 m² × 3,500 = 2,107,000 | (implicit) | — |
| retention (eff age ~22 / life 50) | 56% → building **1,180,000** | building **1,143,800** (= 602 × 1,900) | **+3.1%** |
| **DRC total (fair MV)** | **3,636,000** | **3,600,145** | **+1.0%** ✓ |
| forced-sale (×0.90) | 3,272,000 | 3,240,145 | +1.0% |

⟹ **CONSISTENCY CHECK, not validation (downgraded per the Claude.ai review, §11):** the model matches the valuer ONLY at an effective age ~22–24 — but **b9 in PRODUCTION reads the SYSTEM age (CGIS ~18), while the actual is ~25** (the valuer also used the system 18). The match was **bought by age-fitting on under-defined parameters** (1,900 is equally hit by RCN 3,800, or life 55, or an excellent penalty −2). At the production system age (18) → rate 2,240 → DRC **~3,805 (+5.7% total)**, not 3,600. ⟹ it **confirms plausibility + reproduces a licensed valuer's net figure, but does NOT validate the depreciation curve** (one point) and is **not reproduced by the production line as-is**. **Fix (§11): run DRC depreciation on ACTUAL/input age (b9 system age = a floor); defining the curve needs the dilapidated anchor + n≥20 at actual ages.** (The valuer's composite 1,900/m² = 3,500 × 0.543 — RCN × retention; implied effective age ~23.)

**Footprint→BUA caveat:** the valuer's BUA = **602 m²** (G+1, footprint ~301). Our b10 surfaces the **max-buildable** footprint (V001 → cov-cap 391, a legal CEILING) — **actual BUA < max-buildable**. So the DRC must use **actual/confirmed BUA** (user-entered in the §6-v2 staged flow, or a typical built-ratio), NOT the b10 legal max, or it over-states the building. (This is the one real gap between b10 and a usable cost BUA — flag for the build.)

## 8. Worked example — Marikh 54/541/6 (the thin-pool over-anchor)

Land ~1.85M + [BUA ~475 (footprint ~238 × G+1) × ordinary 2,200 × retention(eff age 28 / 50 = 44%) = ~460,000] ≈ **cost ~2.31M** vs **market 5.4M** (penthouse-median thin-pool artifact) → cost ≪ market → **re-anchor DOWN**; the defensible plain-villa value (~3.0–3.4M comps) sits between the cost floor and the artifact → honest range `[~2.3M … ~3.4M]`, MUC high. (The big §20.9 win.)

## 9. Open / PO decisions + n≥20 items
1. ECONOMIC_LIFE 45 vs **50** (50 reproduces the valuer). 2. RESIDUAL_FLOOR 0.27. 3. condition_penalty ladder (§5). 4. default finish for no-input = **ordinary** + average condition. 5. soil/zone factor = **v2 GIS refinement** (sabkha/karst premium). 6. **functional/economic obsolescence (old-premium discount) = market-derived, n≥20** (the H-A; v1 discloses a range). 7. BUA source = **actual/confirmed**, not b10 max (the §7 caveat). 8. forced-sale display = MV × 0.90, labelled convention. **multi-AI #54** on the depreciation-curve + soil-factor framing (recommended before build).

## 10. Sources (web, 2026-06-09)
- Turner & Townsend — *Global Construction Market Intelligence 2025*, Qatar/Middle East (Doha all-asset US$2,631/m²; +1.0% escalation): turnerandtownsend.com · marketintelligence.turnerandtownsend.com/qatar-mi-2025
- Arcadis — *International Construction Costs 2025*: arcadis.com/en/insights/perspectives/global/international-construction-costs-2025
- Qatar villa build cost (turnkey tiers, 2025): buildersnirvana.com/home-construction-costs-in-qatar-explained · arabmls.org/how-much-does-it-cost-to-build-a-house-in-qatar · globalpropertyguide.com/middle-east/qatar/square-meter-prices
- Doha geotechnics (Simsima Limestone founding stratum, karst/cavities, Midra Shale/gypsum): *Geology and geotechnical evaluation of Doha rock formations* (ICE/Emerald, researchgate.net/publication/311161761) · *Geotechnical Characterization of the Simsima Limestone (Doha, Qatar)* (ASCE)
- Sabkha foundations (salt-aggressive, soil stabilization/replacement): scholarsmine.mst.edu (Foundations Over Salt-Encrusted Flats) · geplus.co.uk (Building on unstable sabkha soils, 2025) · bardawil-qatar.com/services/geotechnical-works
- RICS DRC method (cost approach, last-resort, modern-equivalent, 3 depreciations, not-where-comparables): rics.org — *Depreciated replacement cost method of valuation for financial reporting* · isurv.com/downloads/2219 · valuations.crecos.gr/en/method-drc.php
- Economic life (RC residential 40–47y; GCC climate reduction; MEP 20y): linkedin.com (DRC and the Economic Life of Buildings in the UAE, N. Witty MRICS) · solomonappraisal.com/remaining-economic-life · pwc viewpoint (IFRS real-estate depreciation)

---

## 11. Claude.ai multi-AI review v1 — INCORPORATED (2026-06-09; full text: `RESPONSE_cost_triangulation_claudeai.md`)

The analyst lane (GPT-5 + Gemini + Claude) reviewed the 4 questions. #54-refinement: the GT-1 valuer rules FOR us on Q1 (straight-line/effective-age) + Q4 (ship the forced-sale, isolated, + RICS descriptor), and is silent on the re-anchor mechanism / curve shape / lift. **Verdicts: Q1 ✓ (but excellent penalty −2 at the actual age, not 0); Q2 ✓ (down-re-anchor gated on comp reliability; lift = range-with-cost-ceiling + MUC, bounded by the Market/DRC ratio); Q3 ✓ (no double-count, Simsima=0, sabkha v2); Q4 ✓ (ship, + RICS descriptor).**

**🔴 Decisive catch — the system-vs-actual AGE bias (§7):** the valuer used system age ~18, not actual ~25 → the "1%" is downgraded to a consistency-check; the DRC must run depreciation on **ACTUAL/input age, b9 system = a floor**.

**§9 parameter updates (incorporated):** ECONOMIC_LIFE 50 ✓ · RESIDUAL_FLOOR 0.27 (ordinary ≈ PO 600; **PO TO PROVIDE the dilapidated-luxury floor ~1,000–1,200 ⇒ ~0.31, or finish-dependent**) · condition ladder **excellent/renovated 0 → −2/−3** + (+5/+8/+15/+25) · default ordinary+average ✓ (ordinary↓ and system-age↑ partly cancel → conservative) · **AGE = actual/confirmed, system = floor** (first-order, like BUA) · soil/zone v2 · economic obsolescence n≥20.

**Three must-do-before-build (portable):** **(A)** the recon §8 "~32% @ 25y" ↔ §9 ~54% contradiction → **FIXED** (recon §8 corrected). **(B)** gate the DOWN-re-anchor on age (OLD stock only) — closes the free new-luxury mis-launch. **(C)** declare + calibrate the **built-ratio ~0.77** (V001 602/782); verify a ±20% error doesn't flip the 30% threshold (realistic/slightly-higher = safer).

**🎯 Gate-2 SPLIT (the key architectural recommendation):**
- **🟢 SHIP-NOW = the down-re-anchor (Marikh)** — **immune to the age bias** (system-age only RAISES the cost floor → conservative; dampens lighter cases, never over-drops) → the headline payoff is sound. Ship with the **downgraded calibration claim (honesty, must-do)** + (A) + disclosed-indicative + MUC high (b4 precedent).
- **🟡 GATE-TO-NEXT = convergent-confirm + the up-lift** — here system-age cost OVER-states (V001 "confirms" 3.8M vs the valuer's 3.6M, and fails to trim down) → gate on **age-handling (actual-not-system) + a measure-recon of the CGIS-vs-actual age gap** (this case 18 vs 25 = 7y; likely systematic — re-registration zeros the date).

**Binding Gate-2 signature = Anas** (reserved). Recommendation: sign the SHIP-NOW slice once the claim-downgrade + (A) land; gate the convergent/lift slice on the age-recon + age-handling.
