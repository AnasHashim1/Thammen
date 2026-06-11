# CHANGELOG v104 — Sprint 2.22.0b.21: the INV-3 back-door close (the income rail's ceiling goes age-neutral)

**Engine:** `thammen-sprint2p22p0b21-inv3-rail-age-neutral` · **SPRINT_TAG** `2.22.0b.21`
**Date:** 2026-06-11 · **Files:** `evaluate_unified.py` (+1 pure fn, 1 call-site arg, version) ·
`test_sprint_2_22_0b21.py` (new) · `test_sprint_2_22_0b19.py` (1 version pin relaxed — R6) · this CHANGELOG.
**Status:** 🔴 micro Gate-2 — SIGNED (Anas 2026-06-11, the INV-3 directive); Gate-1 deploy-on-green
**conditioned on the byte-identical 22-case fixtures** (else STOP).

## 1. Why this matters

The Marikh 632-case surface sweep (the Phase-0 kit) caught the ONLY breach of the 8 invariants:
**INV-3 (E26/b18-A1 — a user-claimed age never moves the headline) breached 3×** through a back door
the b18 enumeration never listed: the b6 income-eligibility rail (`income ≤ ceiling×1.05`) consumes the
**v3 replacement-cost ceiling, which depreciates on the USER age**. With footprint+rent combos, age=40
shrank the ceiling (3,351,360 → 2,538,795) below income 2,793,404 → income_led killed → the headline
fell 2.8M→2.4M (and 2.8M→2.7M on the lux group) — **a user age moving the headline**, violating E26.

## 2. Root cause

`_income_triangulation(primary, income, cost, …)` at `:4720` receives the v3 `ReplacementCostValuation`
dict whose `value` embeds the user-age depreciation curve (`evaluate_property.py:858-879`). The rail is
inert without a footprint (the v3 cost computes only with a BUA → `ceil=None`), which is why the breach
lived ONLY on fp+rent combos.

## 3. What this patch does

New pure `_age_neutral_rail_cost(cost, age_source)`: when `age_source=='user'`, the rail's ceiling is
restored to its **age-0 figure** — `value − building_value_depreciated + building_value_new` (land +
external works unchanged) — exactly the number the rail uses when no age is supplied. Single call-site
arg swap at `:4720`. All other consumers of the v3 cost (the reconciliation status reporter, the
land-value fallback) untouched; no-fp rows untouched (ceil stays None-inert).

**#39 MEASURED DEVIATION (prominent):** the signed directive named the literal **`_cost_av`** (the
system-age DRC) as the new ceiling. Measured BEFORE building: `_cost_av`×1.05 ≈ 2,497,999 < income
2,793,404 → the literal vehicle **BLOCKS the with-rent baseline surface** (incl. every no-footprint row,
where the rail springs from inert to blocking; rent-25k rows 4.7M→2.4M) — **breaching the signed
«الحركات المتوقعة (الحصر الكامل)»**. The age-NEUTRALIZED v3 ceiling reproduces the signed enumeration
EXACTLY (measured table in the session record): only the three breach groups return to income_led;
everything else byte-identical. What is lost: single-cost-basis purism — the rail keeps the (generous)
v3 replacement bound as its plausibility ceiling; whether income should instead be capped by the
system DRC is a SEPARATE methodology question, logged deferred (#42).

## 4. Verification — empirical evidence

- Isolated `test_sprint_2_22_0b21.py` **17/17** (the pure-fn matrix + the breach REPRODUCED then CURED
  through the production `_income_triangulation` on the measured numbers + no-fp inert + wiring pins).
- The 7 decisive local cases (cached-GIS real engine): fp450@15k age None/40 → **2.8M income_led both**
  ✓ · fp200+lux@15k age None/40 → **2.8M both** ✓ · Marikh bare **2.4M cost_led** byte-stable ·
  V001 bare **3.8M geo_full** byte-stable · no-fp age40+rent **2.8M income_led** (rail still inert) ✓.
- DoD: aggregator **392 ALL COUNTS MATCH** · security **15/15** · **broad walk ALL FILES GREEN**.
- **The full 632-case sweep re-run + the 8-invariant checker → 8/8 ZERO breaches** (see §20.55).
- b19's exact-version pin relaxed to a format check (R6/Lesson-2 — caught proactively this time).

## 5. Deployment

`git subtree push --prefix "deploy v2" heroku master` on green; post-deploy: `/api/health` = b21 +
the 4-case fixtures smoke (امريخ/V001/المعراض/أرض) **byte-identical to `.b20_live_fixtures.json`**
(else STOP per the signed condition) + the live breach-pair check via `/api/evaluate/details`.

## 6. Verification curl (post-deploy)

`POST /api/evaluate/details {"zone":54,"street":541,"building":6,"rental_income":15000,"footprint_m2":450,"building_age_years":40}`
→ expect `amount=2800000`, `income_triangulation.mode="income_led"` (was 2,400,000 cost_led).

## 7. What's NOT in this patch

The doctrinal question «هل يُسقَّف الدخل بكلفة النظام؟» (the literal-`_cost_av` ceiling = a sweeping
income-subordination decision — deferred, #42) · the v3 cost's own displayed fields (unchanged; the
reconciliation status still reads the as-computed v3 cost) · any gate/leadership logic (b20 untouched).
