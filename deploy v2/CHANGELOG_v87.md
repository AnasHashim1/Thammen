# CHANGELOG v87 — Sprint 2.22.0b.6 (§6 R7 income-triangulation)

**Engine:** `thammen-sprint2p22p0b6-income-triangulation` · **SPRINT_TAG** `2.22.0b.6` ·
api/health `3.1.0-sprint2.22.0b.6` · **Date:** 2026-06-07
**Files:** `evaluate_unified.py` (new `_income_triangulation` + b4-region wiring + notes + version),
`test_sprint_2_22_0b6.py` (new, 23/23). `api.py` + `index.html` UNTOUCHED.
**Gate:** 🔴 Gate-2 (changes the villa headline value) — PO-signed «go» on brief `BRIEF_income_triangulation_R7.md`
(B1 income LEADS · B2 opex 0.20 [deferred] · B3 v1 = i+iii). Recon `PHASE0_income_triangulation_recon.md`.

## 2. Why this matters
The villa headline was Sales Comparison ALONE — condition-BLIND (R7). A thin pool can pin an
unjustified high GUESS as a confident value (Marikh 54/541/6 = 5.4M; defensible ~3.0–3.4M; land floor
~1.85M). PO decision (أ): stop pinning condition-blind guesses; let a GROUNDED income read MOVE the
villa headline toward reality, and honestly WIDEN the no-rent thin guesses DOWN so they no longer assert
a confident high number.

## 3. Root cause
`_build_unified_output` set `valuation.amount = primary['value']` (Sales Comparison) in 100% of villa
cases; `_analyze_reconciliation` is status-only (income never reached the headline). The comparison
median is condition-blind at source.

## 4. What this patch does (villa/house only; pure decision fn + b4-region wiring)
- **`_income_triangulation(primary, income, cost, land_floor, asset_type, dispersion_gated)`** — pure,
  returns a decision or None. Two modes:
  - **income_led ((i)/أ):** a GROUNDED **subject** rent (`rent_source == 'actual_provided'`) + a
    **calibrated** reliable/indicative cap-rate cell + income WITHIN the rails `[land_floor, cost×1.05]`
    → income LEADS: `amount = income value`, range = income band, comparison DEMOTED to a disclosed
    sibling, MUC = high if |spread|≥30% else moderate. **Circularity guard:** only a subject-specific
    rent can lead — the area-median rent ÷ area-yield reconstructs the comparison (a no-op); a
    municipality area-rent does NOT lead.
  - **widen_down ((iii)):** a no-rent condition-blind **THIN/widened/preliminary** villa with
    `land_floor < comparison` (i.e. OVER-anchored) → widen the range DOWN to the land floor +
    `range_is_headline` (muted median) + condition-widen note + MUC high. **EXCLUDES** clean reliable
    `comparison_bracket` (the good case — would over-state uncertainty) AND dispersion-gated pools
    (a10/a14 own those) AND land-anchored villas (`floor ≥ value` — not over-anchored).
- Wiring in the b4 region (post-`_build_unified_output`), **mutually exclusive** with the b4 teardown +
  luxury-new overrides; reuses `_villa_value_floor` (land floor) + `_stage1_dispersion_gate` (defer
  dispersed); swallows errors so an edge can never break evaluate.
- 4 user-facing notes (AR+EN): `income_triangulation.note_*`, `condition_widen_note_*`.

## 5. Verification — empirical
- py_compile OK. Isolated `test_sprint_2_22_0b6.py` **23/23** (production fn — E14: led/not-led on
  rent-source + calibration + rails; widen on over-anchored thin; clean-bracket excluded; gated
  excluded; land-anchored excluded; non-villa None; MUC high/moderate; house alias).
- **Local E2E on the real engine (GIS):**
  - 56/565/21 (clean bracket) → **2,400,000 UNCHANGED** (no triangulation) ✓
  - 54/541/6 (thin, over-anchored) → **widen_down**: range **1.9M–5.5M** (low = land floor),
    range_is_headline, condition_widen_note, MUC high (central 5.4M muted) ✓
  - 54/541/6 @400-600 + rent 15k → **income_led**: amount 2.7M (income 2.69M leads, comparison 2.97M
    demoted), MUC moderate ✓
  - 55/296/13 (thin, **land-anchored** floor 2.67M ≥ value 2.6M) → **no widen** (correctly — not
    over-anchored) ✓
  - 52/903/90 (apartment) → refusal, no triangulation ✓
- **DoD:** aggregator **392** (ALL COUNTS MATCH) · security **15/15** · surface **45/45** · broad walk
  **75/75** (74→75, +b6; zero regression — the 54/541/6 amount stays 5.4M + the a19 condition_note
  still present, only low/range/MUC changed).

## 6. Deployment
```
git add evaluate_unified.py test_sprint_2_22_0b6.py CHANGELOG_v87.md docs/...
git commit -m "Sprint 2.22.0b.6 (§6 R7): income-triangulation — income LEADS villa headline / honest-widen"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
(Rule #43 — subtree push; Gate-1 explicit «go» required before the Heroku push.)

## 7. Verification curl (post-deploy, browser-UA #61)
```
curl -s https://thammen.qa/api/health   # engine ...b6, 3.1.0-sprint2.22.0b.6
# 54/541/6 → range_is_headline true + condition_widen_note + MUC high (was point 5.4M)
# 56/565/21 → 2,400,000 unchanged
```

## 8. What's NOT in this patch (deferred — flagged)
- **Fork C** (a18/override-aware `_lookup_calibrated_cap_rate`) — DEFERRED v2; GIS↔GIS works today
  (§11), token already strips zone-numbers → robustness, not a blocker.
- **opex 0.20** (B2) — DEFERRED v2; v1 uses `income['value']` as-is (opex 0.23) for display↔headline
  consistency; the ~3.75% refinement lands later.
- **(ii) age-adjusted rent** (no-input grounded estimate) — DEFERRED fast-follow (B3); needs auto-age
  reliability measured before shipping as a value-setter.
- **income_led reach is bracket-gated:** fires only where a calibrated cell exists (mostly 400-600);
  600-900 villas (Marikh/villa-6 live) can only **widen_down**, not income-lead, until 600-900 yield
  cells are calibrated (more PF depth). §6 un-anchors them; grounding them needs the 600-900 cell.
- The widen_down range (land-floor → comparison) can be WIDE; tuning the low (e.g. a softer
  comparison×k) is a presentation fast-follow if the PO wants it narrower.
