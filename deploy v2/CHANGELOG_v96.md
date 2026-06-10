# CHANGELOG v96 — Sprint 2.22.0b.13 (§20.9 GATED slice — Lever 1 convergent-TRIM, RESHAPED)

**Engine:** `thammen-sprint2p22p0b13-cost-trim-convergent` · **api-health:** `3.1.0-sprint2.22.0b.13`
**Date:** 2026-06-10 · **Files:** `evaluate_unified.py` (params/functions/wiring/cliff-flag/version), `index.html` (+2: cliff render + refine nudge), `test_sprint_2_22_0b13.py` (new), `test_sprint_2_22_0b11.py` (ladder assertion)
**Class:** 🔴 Gate-2 VALUE-AFFECTING (villa headlines move on the trim path) — **SIGNED BY DELEGATION** + **RESHAPED at the Phase-0 gate**. Brief `docs/BRIEF_Sprint2p22p0b13_gated_slice_SIGNED.md`; recon `docs/PHASE0_2p22p0b13_gated_slice.md`.

## 1 — Why this matters
b11 shipped the §20.9 DOWN-re-anchor (cost as a *floor* on thin over-anchored old villas). The remaining R7 gap: an **old over-anchored villa whose actual-age cost sits BELOW market within 30%** keeps its inflated central (V001 56/647/6: bare 3.8M; certified valuer TD 93317 = **3.6M** at actual age 25). Lever 1 (convergent-TRIM) closes it.

## 2 — 🔴 Phase-0 RESHAPE (the headline)
The mandated Phase-0 recon (real-engine trace, `.b13_recon.py`) **overturned Lever 2 (UP-lift)** and the PO confirmed the reshape (Lever-1-only): **measured V002/V003 DRC cost ≈ 2.6M — *below* their 4.0M sale and ≈ their 2.5M market** → a cost-lift cannot reach the sale; the new-premium under-anchor is **B-2 GT-corpus calibration (`luxury_new` stratum n=0, PARKED n≥20), NOT a cost lift.** **Lever 2 DROPPED.** Lever 1 + the finish-floor + ladder + cliff-flag SHIPPED.

## 3 — What this patch does
- **Lever 1 — `_cost_trim` (new pure fn) + `cost_trim_convergent` wiring branch** (precedence `income_led > cost_reanchor_down > cost_trim_convergent > widen_down`): fires iff villa/house · path ∈ {thin, widened, widened_indicative, preliminary} (NOT clean bracket, NOT dispersion-gated, NOT land-anchored) · **`age_source=='user'`** (recon R1 — distinct from auto-imagery `gis_imagery`) · effective age `= max(user_actual, system)` (system stays a floor) · OLD (eff_age ≥ 10) · over-anchored (land_floor < market) · the **actual-age** cost is BELOW market with **0 < undercut ≤ 30%** (DISJOINT from b11's `>30%` reanchor). Treatment: the actual-age cost **LEADS** (`amount`/central), market muted in `[max(land_floor, cost) … market]`, `range_is_headline`, MUC high, AR/EN cost-basis note.
- **D-1 finish-floor:** `_cost_retention(effective_age, finish)` — `high`/`luxury` → **0.31**; ordinary/good/None → 0.27 (b11/b12 byte-identical). Bites only on dilapidated-premium (eff_age > ~34).
- **Ladder (§4.2):** `COST_CONDITION_PENALTY` excellent **−2** / renovated **−3** (were 0); default condition = average +8 unchanged → no-condition flows byte-identical.
- **Cliff-flag R3 (value-invariant disclosure):** `_building_age_estimate` adds `age_basis='vintage_capped'` + a nudge note when survey-year ∈ 2009-2012 with floor ≥ 15 OR floor < 2 (recent re-survey) — 62% of villas (E24). `index.html`: the note renders in `pbRows` (confirm + results cards) + a one-line refineScreen hint by the age input.

## 4 — Verification (all EXECUTED)
- py_compile OK. Isolated `test_sprint_2_22_0b13.py` **37/37** (finish-floor incl. byte-identical default; ladder; `_cost_approach_value` V001 **3,594,781 ≈ valuer 3.6M** + dilapidated-luxury floor 0.31; the full `_cost_trim` matrix — fires + all exclusions + fail-safes; **disjointness at exactly 30%**; cliff-flag 2009/re-survey/mid-vintage). `test_sprint_2_22_0b11.py` **52/52** (excellent eff_age 17→**15** ladder update).
- DoD: aggregator **392** · security **15/15** · surface **45/45** · broad auto-walk **82/82** (81→82, clean, 177s, no flake).
- **Local E2E (real engine, live GIS):** 4 anchors + V001 bare **byte-identical** (2.4M/5.4M/2.6M/None/3.8M; Marikh still `cost_reanchor_down`; no trim leak; `age_basis=vintage_capped` display-only) · **V001 + `building_age_years=25, is_luxury, condition=excellent` → TRIM fired → amount 3,600,000** (valuer 3.6M), cost 3,594,781, eff_age 23, retention 0.54, undercut 3.3%, range [3.6M, 3.7M], range_is_headline.
- **R14 real-Chromium 390×844** (EXECUTED): cliff-flag `.rn` renders (right-edge 345<390, scrollW==clientW) + refineScreen nudge present, **no horizontal overflow** (390==390), **0 console errors**.

## 5 — Deployment
```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6 — Verification curl (post-deploy)
```
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
:: expect amount 2,400,000 (byte-identical) + property_basis.building_age_estimate.age_basis=vintage_capped
curl -s https://thammen.qa/api/health   :: expect 3.1.0-sprint2.22.0b.13
```

## 7 — Honest residuals
- **The TRIM is DORMANT on live no-age traffic** (62% vintage-capped; recon R2) — it fires only when an owner supplies the actual age via Refine. The cliff-flag nudge is the activation surface; GT collection (D-3) the flow source. Honest parallel to §6-income's beta-gated payoff.
- **Calibration n=2** (V001-trim vs one bank report) → ships disclosed-as-indicative (MUC high + rails); tightened as GT grows.
- **Lever 2 (new-premium under-anchor) → B-2** (GT-corpus calibration, PARKED n≥20) — NOT a cost-approach problem.

## 8 — Explicitly NOT in this sprint
Lever 2 (UP-lift, dropped) · the report two-values display (MV + forced-sale, DEF-12) · soil/geotech (DEF-13) · imagery age-band detector · B-2 elicitation (PARKED) · apartments.
