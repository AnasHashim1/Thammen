# CHANGELOG v102 — Sprint 2.22.0b.20: EVIDENCE-CONDITIONAL LEADERSHIP + three-value stack

**Engine:** `thammen-sprint2p22p0b20-conditional-leadership` · **SPRINT_TAG** `2.22.0b.20`
**Date:** 2026-06-11 · **Files:** `evaluate_unified.py` · `moj_reference.py` · `index.html` ·
`test_sprint_2_22_0b20.py` (new) · `test_sprint_2_22_0b16.py` + `test_sprint_2_22_0b18.py` (4 wiring
pins re-pointed) · this CHANGELOG.
**Status:** 🔴 Gate-2 VALUE-AFFECTING — **SIGNED** (Anas F6, `docs/SESSION_CLOSE_2026-06-11_F6_SIGNED.md`
§1; normative spec `docs/BRIEF_conditional_leadership_SIGNED.md`). **⏸ HELD AT GATE-1 — NOT DEPLOYED.**

## 1. Why this matters

The headline was market-led by path history; cost (DRC) led/floored only narrow slices (b11/b13/b16).
A thin or dispersed or stratum-mismatched median could still anchor the headline. The signed doctrine:
**the median is TESTED per case** (E23 — «الوسيط لا يُؤتمن بقرار ولا يُعدم بقرار»); when it fails, the
disclosed-indicative DRC leads. Measured on the Phase-0 cohort: **7/13 valued villas = 54% cost-led**,
incl. امريخ 3.4M → 2,378,094 (its geo-full pool n=51 disperses at **0.620**).

## 2. Root cause

`evaluate_unified.py` b4-region elif chain (`income_led → elif _ct and not _osr → elif _osr → elif
widen_down`) decided leadership by which special-case branch fired, not by pool quality; the DRC was
computed for every valued villa at `:4727` then **discarded** unless a branch fired (Phase-0 G1); the
dispersion numeric never reached the JSON (G2).

## 3. What this patch does

**Backend (`evaluate_unified.py`):**
- New pure fns + signed constants after `_old_stock_reanchor`: `_e26_subject_band` (E26 band; F2=B
  re-survey → untestable) · `_matched_stratum_n` · `_bracket_disp36` · `_muc_one_notch` ·
  **`_leadership_gate`** (RULE 1 matched n≥10/disp36<0.30/match · RULE 2 geo-full n≥20/disp<0.30 →
  disclosure+MUC+1+cost floor · else COST leads F3(b) [cost…market-muted] · **E25 rail**: cost≥market →
  market caps + divergence + MUC≥high · cost-unavailable → market + disclosure + MUC≥high).
- The elif chain **REWIRED**: income_led keeps absolute precedence; the gate replaces the b11/b16/b6
  branch deciders (their pure calculators KEPT as superseded references — isolated suites stay green);
  the `_tri` widen_down mode ignored (subsumed). b13/b18 age-sensitivity + b4 teardown/luxury untouched.
- **Emission:** `valuation.leadership` (leader/rule/matched_n/**dispersion_36**/geo_full_n/
  geo_full_dispersion/stratum_match/band/resurvey/cost_value/market_value/thresholds + signed notes)
  + `valuation.value_stack` (market{median,n,dispersion,strata} + cost{b19-signed label, value,
  breakdown, assumptions} or unavailable-reason). Cost-led runs the ISS-A07 recompute (decomposition +
  B-1 floor + b14 narrative). raw_land emits the one-liner `cost_note_ar` (DRC ≡ land).
- ENGINE_VERSION/SPRINT_TAG → b20.

**`moj_reference.py`:** `subject_geo_full_ppm2` += `ppm2_p25_full`/`ppm2_p75_full`/`dispersion_full`
(additive; existing keys byte-stable — b16 consumers unaffected).

**Frontend (`index.html`):** TIER-1 + report render `leadership.note_ar` (warn-styled on cost-led/E25)
+ age-honesty + re-survey lines + the cost stack line (verbatim «قيمة التكلفة (أرض + بناء مُهلَك) — نهج
DRC» + V001 sub) + the market dispersion line (G2 visible).

## 4. Verification — empirical evidence

- Isolated `test_sprint_2_22_0b20.py` **69/69** (band/matrix/notch/RULE1/RULE2/F3(b)/E25+double-weak/
  cost-unavailable/scope guards/**135-point invariant grid**/verbatim copy/terminology/real-CSV geo-full
  [امريخ 51/0.620 · V001 22/0.203]/wiring pins).
- Siblings: b6 23/23 · b7 22/22 · b8 19/19 · b11 52/52 · b13 37/37 · b14 34/34 · **b16 38/38** ·
  **b18 26/26** (4 superseded wiring pins re-pointed per the §3.1 map — incl. the V001 TD-93317 ±1%
  sheet reproduction, green on its pinned raw basis).
- DoD: aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface-honesty **45/45** ·
  broad walk **ALL FILES GREEN (0 failed, 168.5s)**.
- **Local E2E `.b20_e2e.py` on the 22-case cohort vs the SIGNED §2.7 table** (live GIS): see §5.
- R14 real-Chromium 390×844: Marikh cost-led + V001 geo-full TIER-1 + report render all b20 lines,
  DEF-12 intact, **0 console errors**, no overflow (390==390 mobile · 610==610 desktop).

## 5. The signed expected-moves table (verified locally)

| case | before (b18) | b20 (local) |
|---|---|---|
| امريخ 54/541/6 | OSR 3.4M | **cost-led 2.4M** [2.4M…5.4M-muted], cost 2,378,094, geo-full 51/0.620 in JSON |
| V001 56/647/6 | widened 3.8M [2.5…3.8] | **3.8M [3.1M…3.8M]** geo-full rescue (22/0.203) + MUC notch |
| V002/V003 56/565/10·12 | bracket 2.5M/2.4M | unchanged amounts + geo-full disclosure + cost floor 2.3M + re-survey note |
| المعراض 55/296/13 | thin 2.6M | **2.6M E25-capped** + divergence + MUC high |
| أبو هامور 56/565/21 + 19 | bracket 2.4M | **byte-identical** + stack/dispersion emitted |
| 51/825/22 · 51/833/37 · 53/736/4 (F4) | a14 honest-range 2.8/4.1/3.0M | **cost-led** ≈2.8/3.0/2.5M |
| 54/788/10 · 55/1056/60 · 55/1044/63 (F5) | thin/prelim 3.0/2.7/2.7M | **cost-led 1.1/1.7/2.1M** |
| land PIN 74328443 | 1.2M | 1.2M + «DRC ≡ قيمة الأرض» |
| refusals + hybrid (8) | refusal/None | **unchanged, no gate keys** |

## 6. Deployment

**⏸ NOT DEPLOYED — Gate-1 reserved for Anas's separate explicit consent (SESSION_CLOSE §8.5).**
When granted: `git subtree push --prefix "deploy v2" heroku master` + two-lane live smoke on the
22-cohort + the post-ship re-snapshot (Phase-0 §4.2: fresh engineering fixtures, NOT methodology truth).

## 7. Verification curl (post-Gate-1)

`curl -s -X POST https://thammen.qa/api/evaluate -A "Mozilla/5.0…" -d '{"zone":54,"street":541,"building":6}'`
→ expect `valuation.amount=2400000`, `leadership.rule="cost_led"`, `leadership.geo_full_dispersion=0.62`.

## 8. What's NOT in this patch

b19 (the three-value REPORT display slice — separate signed track; the land one-liner + stack lines here
are the engine contract, b19 owns the report composition) · compounds/towers RCN (no basis — G3) ·
soil «معامل الإحلال» (v2 GIS) · threshold re-tuning · the post-ship re-snapshot (after Gate-1) ·
new/renovated finish-delta (still abstains, #42).
