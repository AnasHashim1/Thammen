# BRIEF — Sprint 2.22.0b.13 — §20.9 GATED slice: the COMPLETE methodological fix
## (convergent-TRIM + UP-lift + finish-dependent floors + condition-ladder correction + age-honesty disclosure)

> **🔴 Gate-2 — VALUE-AFFECTING (villa/house headlines move on defined paths) — SIGNED BY DELEGATION**
> («افعل الأصوب», Anas, 2026-06-10 — incl. **D-1: dilapidated-luxury residual floor = 0.31**).
> **Gate-1:** deploy-on-green under the same delegation. **STANDING HALT:** Phase-0 overturns any premise → stop, report, wait.
> **Authority chain:** `METHODOLOGY_DRC_qatar_v1.md` §11 (the Gate-2 SPLIT — "GATE-TO-NEXT = convergent-confirm + up-lift")
> + `PHASE0_age_gap_recon.md` (rules R1/R2/R3 + §5, measured✓ n=737) + Session_Log §20.45/§20.46 + this delegation.
> **Engine baseline:** b12 / Heroku v181. **Reuse, don't fork:** `_cost_retention` / `_cost_approach_value` /
> `_cost_triangulation` (b11). `api.py` expected UNTOUCHED.

---

## §1 — The problem this sprint closes (R7's remaining halves)

b11 shipped the DOWN-re-anchor (cost as an informed *floor* on old over-anchored thin villas — Marikh floor 1.9M→2.4M). What remains of the §20.9 durable R7 fix:

| Gap | Measured evidence | This sprint's lever |
|---|---|---|
| **Convergent under-trim** — an old over-anchored villa whose cost sits *below* market but within the 30% band keeps its inflated central | V001 56/647/6: production system-age cost ≈ 3,805 (+5.7%) → **no trim**; the certified valuer (TD 93317) = **3.6M** at actual age 25 | **Lever 1 (TRIM)** |
| **Under-anchor on new premium stock** — the engine returns ~60% of the realized price | V002/V003 56/565/10+12: **SOLD 4.0M** each; engine 2.4–2.5M (**−37/−40%**) — the project's only GT-2 confirmed sales | **Lever 2 (LIFT)** |
| **Over-depreciation of premium builds** | RCN luxury 3,500 ر.ق/م² floored at the same 0.27 as ordinary | **Finish-dependent floor (D-1 = 0.31)** |
| **Condition ladder mis-set at the top** | §11 multi-AI verdict Q1: excellent/renovated should be **−2/−3**, not 0 | **Ladder correction** |
| **Age dishonesty** — 62% of villas sit at the 2009-survey cliff; their displayed basis implies a known age | recon §2: hard ceiling 17.0y, 65% surveyed 2009-10; `SURVEYED_DATE` = survey vintage, NOT construction date | **Cliff-flag disclosure (R3) + age-input nudge** |

---

## §2 — Lever 1: convergent-TRIM (down; USER-ACTUAL-AGE-GATED — recon R1/R2)

**Fires iff ALL hold:**
- villa/house; comparison path ∈ {thin, widened, widened_indicative, preliminary} (NOT clean bracket, NOT dispersion-gated a10/a14, NOT land-anchored);
- **a user-supplied `building_age_years` exists** (`/details` — plumbing already threaded since b4; recon R1);
- effective age basis = **max(user_actual, system)** (system stays a floor — a user input *younger* than system must never raise retention; recon §3 "sys ≤ actual always");
- OLD stock: effective age ≥ 10 (the b11 age-gate, same constant);
- over-anchored: `land_floor < market central`;
- the ACTUAL-age cost sits **below** the market central with undercut **≤ 30%** — i.e. `0 < (market − cost)/cost ≤ 0.30` (the > 30% zone stays b11's `cost_reanchor_down`, untouched).

**Treatment (methodology §6 — reconcile-not-blend; brief-§7#2 of b11 — no invented midpoint):** the **actual-age cost becomes the leading reconciled figure**; the market median is retained **muted inside the range** `[max(land_floor, cost_actual) … market]`; `range_is_headline`; **MUC high**; the §5 cost disclosure names the basis: «منهج التكلفة على العمر الفعلي المُدخَل (X سنة)». Status label e.g. `cost_trim_convergent`.
**Expected:** V001 + `building_age=25` (+ finish `high`) → leads **~3.6M** (the valuer's figure, ±band). Default V001 (no age input) → **byte-identical to b12** (trim withheld per recon R2 row 3 — cost stays a disclosed floor only).

## §3 — Lever 2: UP-lift (new stock; SYSTEM-AGE-SAFE — recon R2 row 2)

**Fires iff ALL hold:**
- villa/house; NOT clean reliable bracket with the subject *inside* its band — Phase-0 must define the under-anchor signal precisely (candidate: thin/widened paths, OR a bracket path whose pool is tight but the cost exceeds it materially — V002/V003's actual live path is the calibration target);
- **genuinely-new stock:** `sys_age < ~5y` (recon: retention error bounded ≤ ~0.04 here) — OR an explicit user `building_age_years < 5` / `condition=new`;
- the cost **EXCEEDS** the market central by **> 30%** (mirror threshold — Phase-0 verifies the constant against V002/V003 and the anchors);
- mutually exclusive with b4 `teardown`/luxury-new levers and with `income_led`.

**Treatment (multi-AI Q2 verdict, verbatim rail):** **range widens UP with the cost as the CEILING** — `[market(muted) … cost]`, `range_is_headline`, **MUC high**, «معايَر على صفقات محدودة (n=2)» label, **NO invented point**; bounded by the Market/DRC ratio; the `[land_floor, cost]` rail stays universal.
**Expected:** V002/V003 → range reaching **~4.0M** (their realized sales). The 4 standard anchors (old/refusal stock) → **byte-identical**.
**Precedence (full chain):** `income_led > cost_reanchor_down ≈ cost_trim_convergent (disjoint bands) > cost_lift_up > widen_down` — Phase-0 confirms disjointness; any overlap → HALT.

## §4 — Signed parameters (D-1 incorporated)

1. **Finish-dependent residual floor** in `_cost_retention`: ordinary/good → **0.27** (unchanged); `high`/`luxury` → **0.31** (D-1; recon §5 — bites only on the trim of old premium stock with a supplied actual age; does NOT touch the b11 down-half which keeps the locked 0.27 on system age... Phase-0 check: if `_cost_retention` is shared, the floor must key on finish so the b11 path with default finish stays byte-identical).
2. **Condition ladder** (eff-age penalty): excellent **−2** · renovated **−3** · good **+5** · average **+8** (default, unchanged) · fair **+15** · poor **+25** (§11 Q1). Default flows (no condition input) → byte-identical.
3. **AGE precedence:** levers 1–2 use `max(user_actual, system)`; b11 down-half stays **pure system age — UNTOUCHED** (its immunity is measured✓).
4. **Built-ratio 0.77** with the ±20% sensitivity guard: **no lever may flip across the band** (isolated test mandatory; b11 precedent: V001 worst-case margin 8pt).
5. **Cliff-flag R3 (disclosure, value-invariant):** `sys_age ≥ 15 AND survey-year ∈ {2009..2012}` → `age_basis = "vintage_capped"` + note «العمر المسجَّل في النظام حدٌّ أدنى (مسح 2009-2012) — العمر الفعلي قد يكون أكبر؛ أدخِل العمر الفعلي في «حسّن التقدير» لدقّة أعلى». Inverse flag: `sys_age < 2` on subtype-1 resale stock → same "age is a floor" framing. Renders muted `.rn` near the property-basis panel (b9) + a one-line nudge on `refineScreen` next to the existing age input. **Frontend → R14 mandatory.**

## §5 — Phase-0 recon FIRST (may reshape — standing pattern; HALT-and-report on premise break)

1. Trace **locally on the real engine**: the 4 anchors (bare) · V001 bare + V001+`age=25,finish=high` · V002/V003 bare — through the b12 triangulation; record which lever (if any) each path hits under this brief's predicates **before writing code**.
2. Verify Lever-2's firing surface: list **every** live-path class that moves (expected: V002/V003-class only; the 4 anchors must not). If any standard anchor moves → HALT.
3. Verify `_cost_retention` sharing (the §4.1 finish-keyed floor isolation) and the trim/reanchor band disjointness at exactly 30%.
4. Confirm the refineScreen age-input field id/flow for the R3 nudge (b2.1 relocated optional details).
Deliverable: `PHASE0_2p22p0b13_gated_slice.md` (measured✓) → then build.

## §6 — Verification & DoD (all EXECUTED — R14 discipline; Rule #52 live==local)

py_compile · **isolated ≥ 24 cases**: both levers' full predicate matrices + `max(user,system)` guard + 0.31-keyed-on-finish (b11-path isolation proven) + ladder top (−2/−3) + ±20% built-ratio non-flip + band disjointness at 30% + cliff-flag matrix (2009-2012 / re-survey / clean) + all exclusions + malformed fail-safes · DoD aggregator + security 15 + surface 45 + **broad walk** (b12 baseline 81) · **local E2E (real engine):** 4 anchors **byte-identical** · V001 bare byte-identical · V001+age25+high → trim ~3.6M-band · V002/V003 → lift range→~4.0M · cliff-note fires on a 2009-surveyed anchor (value-invariant) · **R14 Chromium 390×844** (cliff note + nudge render, 0 console errors, no overflow) · **live smoke v18x** same matrix (browser-UA, Rule #61) · `heroku auth:whoami` before subtree push (§20.45) · `git push origin` pairs the deploy · CHANGELOG_v96 · Session_Log §20.47 · ENGINE_VERSION → `2.22.0b.13`.

## §7 — HONEST RESIDUALS (state verbatim in the close-out)

1. **Calibration n=2** (V001-trim against one bank report; V002/V003-lift against two sales) → everything ships **disclosed-as-indicative** (§0.4): MUC high + «معايَر على صفقات محدودة» + rails; tightened as GT grows.
2. **The trim is DORMANT on live no-age traffic** (62% vintage-capped; recon R2): until owners supply actual age via refine — the R3 nudge is the activation surface, GT collection (D-3) is the flow source. Honest parallel to §6-income's beta-gated payoff.
3. No automatic actual-age above the 2009 cliff (imagery detector = a future separate sprint, recon §6).

## §8 — Explicitly NOT in this sprint

The report **two-values display** (MV + forced-sale MV×0.90 — DEF-12, §11 Q4 "ship" verdict stands, scheduled with the screen-5 report build) · soil/geotech factor (DEF-13, v2 GIS) · imagery age-band detector · B-2 elicitation mechanism (PARKED n≥20 — this sprint's levers are its cost-side complement, not its replacement) · any apartment scope.

---
*Brief authored by the Claude.ai analyst lane 2026-06-10; Gate-2 + D-1 signed by delegation («افعل الأصوب»). Persist per Rule #63 as `docs/BRIEF_Sprint2p22p0b13_gated_slice_SIGNED.md`.*
