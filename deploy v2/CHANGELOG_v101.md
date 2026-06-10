# CHANGELOG v101 — Sprint 2.22.0b.18: AGE-BASIS directive + LUXURY-EXIT fix + TD-93317 recalibration

**Engine:** `thammen-sprint2p22p0b18-age-basis-finish-delta` · **Date:** 2026-06-10 ·
**Files:** `evaluate_unified.py` (+~95/−45) · `index.html` (+4) · `test_sprint_2_22_0b18.py` (new, 26) ·
`test_sprint_2_22_0b14.py` (1 pin → the signed reword) · `docs/PHASE0_b18.md`.
**🔴 Gate-2 VALUE-AFFECTING — SIGNED (Anas, 2026-06-10).** Gate-1: deploy-on-green inside the §D HALT bands.

## 1 — Why this matters
Two live honesty defects: (a) a user-claimed building age **led** the headline (b13 trim) although the
certified-valuer practice (TD-93317) leads on the **SYSTEM/CGIS-documented** age — claims are not evidence;
(b) declaring a luxury finish on an old stratum-mismatched villa **reverted the central to the raw median**
(Marikh 3.4M→5.4M, Phase-0-verified) — rewarding the declaration with the very over-anchor b16 removed.

## 2 — Root cause
(a) the b13 `elif _ct_trim:` branch put the ACTUAL-age cost in the lead; the a9 widened elasticity also let
the user-supplied `building_age` factor move the geo headline (invisible until the trim demotion exposed it).
(b) `_old_stock_reanchor(user_premium=is_luxury or …)` ABSTAINED on luxury → fell through to b11/raw median —
finish was priced by **pool-switching** instead of through the replacement coefficient.

## 3 — What this patch does
- **A1 (AGE BASIS):** the trim branch is REMOVED from the lead chain; `_ct_trim` (computed unchanged) now
  attaches `valuation.age_sensitivity` — «حساسية العمر: لو كان العمر الفعلي {N} سنة ≈ {value} ر.ق» — headline/
  range/MUC untouched. The a9 widened elasticity excludes the `building_age` slice when `age_source=='user'`
  (`_age_quality_adj(exclude_user_age)`; gis_imagery/system ages keep it). b11 system floor + E24 cliff-flag
  unchanged. b4's explicit new+luxury lever unchanged.
- **A2/C(ii) (LUXURY-EXIT):** `is_luxury` no longer abstains the OSR — the plain re-anchor base gets a
  **FINISH-DELTA** = (RCN_finish − RCN_ord) × retention(**RAW system age**) × BUA, with the hard monotonicity
  rail plain ≤ finish lead ≤ raw thin median; delta incomputable → conservative abstain (pre-b18 behavior);
  new/renovated still abstain (logged #42). Disclosure suffix on the OSR note.
- **§B:** TD-93317 reproduced **+0.35%** (raw system age 18, finish=high, RCN 3,000 × 0.64) — V001 re-tiers
  LUXURY→HIGH; land basis = the engine's MoJ floor (matches the bank to +0.016%). Mechanism (i) (pure lux-DRC
  lead) measured 2.96M < plain 3.41M → **monotonicity violation → rejected**; (ii) wins (PHASE0_b18 §3).
- Copy: the b14 Case-A CTA + the 10-Year disclosure re-worded to promise the delta pricing, not the jump.
  `index.html`: the sensitivity line renders on screen-4 TIER-1 + the b17 report.

## 4 — Verification — empirical evidence
Isolated **26/26** · siblings b13 **37/37** / b16 **38/38** / b14 **34/34** (pin→signed reword) / a9 **28/28**
/ b11 **52/52** · aggregator **392 MATCH** · security **15/15** · surface **45/45** · **broad 87/87** ·
**local E2E = the §D table 15/15:** Marikh plain **3,400,000** byte-identical · Marikh+lux **3,800,000**
(delta 410,982, OSR-led, monotonic) ∈ [3.4M, 4.2M] · V001 bare **3,800,000** · V001+25+lux+exc headline
**UNCHANGED 3,800,000** + sensitivity **3,600,000** verbatim · 56/565/21 / 55/296/13 / 52/903/90
byte-identical · R14 Chromium 390×844: sensitivity TIER-1 visible (right 350<390) + report, **0 console
errors, no overflow**.

## 5 — Deployment
`git subtree push --prefix "deploy v2" heroku master` (after `heroku auth:whoami`) + `git push origin master`.

## 6 — Verification curl
`curl -s -X POST https://thammen.qa/api/evaluate/details -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6,\"is_luxury\":true}"` → amount ∈ [3.4M,4.2M] + `old_stock_reanchor.finish_delta`.

## 7 — What's NOT in this patch
new/renovated finish-delta (still abstains — #42) · B-2-proper (under-anchor, n≥20) · the b11 low>high
inversion micro-fix · any change to b4's explicit levers or the b11 down-re-anchor.

## 8 — Honest residual
The sensitivity line renders only where the would-be trim computes (old + over-anchored + undercut ≤30%);
elsewhere a user age simply doesn't move anything (correct per A1, no line). The finish-delta is calibrated
on ONE certified appraisal's coefficients (TD-93317) + the PO RCN ladder — n=1, disclosed; the GT kit (D-3)
is the tightening channel. E26 candidate recorded: «الأساس العمري للقيادة = الموثَّق في النظام (CGIS)؛
والمُدَّعى حساسيّة مُفصَحة» — VALUER-VALIDATED.
