# CHANGELOG v94 — Sprint 2.22.0b.11 (§20.9 Cost-Approach DRC down-re-anchor, SHIP-NOW slice)

**Engine:** `thammen-sprint2p22p0b11-cost-drc-reanchor` · **SPRINT_TAG:** `2.22.0b.11` · **api/health:** `3.1.0-sprint2.22.0b.11`
**Date:** 2026-06-09 · **Heroku:** **v180** (released; commit `6e93d16` → subtree split `f7c3990`, `90a4efb..f7c3990`; origin in sync `743742d..6e93d16`) · **Files:** `evaluate_unified.py` (+218/−2) · `test_sprint_2_22_0b11.py` (new, 52) · this CHANGELOG.
**Deploy note:** the first two `git subtree push` attempts failed on Heroku git auth (CC-side heroku CLI unauthenticated this session → `could not read Username`; then a username+password dialog → Heroku rejected it [token-only]). Fixed by Anas `heroku login` (browser/token) + the push from his terminal → Released v180.
**Gate-2:** SIGNED (Anas «وقّع وانشر الآن», 2026-06-09) · **Gate-1:** «go» same message. **`api.py` + `index.html` UNTOUCHED** (backend-only; R14 node/mobile N/A by construction).
**Brief:** `docs/BRIEF_cost_triangulation_R7.md` (SIGNED) · **Methodology:** `docs/METHODOLOGY_DRC_qatar_v1.md` §11 Gate-2 SPLIT · **Review:** `docs/RESPONSE_cost_triangulation_claudeai.md`.

---

## 1. Why this matters (R7 — the middle case the b4 levers miss)

The market-comparison headline is blind to built-type / finish / condition / BUA (RISK_REGISTER **R7**). b4 handles the OPT-IN extremes (teardown ↓, new-luxury ↑); the **MIDDLE** — a thin-pool or worn villa over-anchored with nothing to move it — had no lever. Live anchor: **Marikh 54/541/6 = 5.4M** (a thin-pool penthouse-median artifact; defensible ~3.0–3.4M). §6 income un-anchored it (b6 widen_down) but only to the **bare land floor** (1.9M) and only ever grounds on a *user rent* (beta-gated). The Cost Approach is **subject-intrinsic** (b9 age + b10 footprint) → it fixes the live default no-rent over-anchor **without a user rent**.

## 2. Root cause + the model (METHODOLOGY_DRC_qatar_v1 §2/§3/§5)

`cost = land_floor + (RCN_new(finish) × retention(effective_age)) × BUA` — an INDEPENDENT RICS DRC, SECONDARY to Market (cost is last-resort for traded assets), used only to TRIANGULATE.
- **land_floor** = the shipped a21 `_villa_value_floor` (validated EXACT vs the bank, engine 3,768/m² = bank 350/ft²).
- **BUA** = `max_buildable_footprint (b10) × BUILT_RATIO 0.77 × floors` (default G+1) — the b10 footprint is a legal CEILING, so the **built-ratio gives the ACTUAL BUA** (V001 602/782 = 0.77 — calibrates exactly; §7 caveat).
- **building_rate** = RCN ladder (shell 1200 / ordinary 2200 / good 2500 / high 3000 / luxury 3500, PO web-validated §3) × `retention = clamp(1 − effective_age/50, 0.27, 0.98)`; `effective_age = chronological + condition_penalty` (excellent 0 / good +5 / average +8 / fair +15 / poor +25).
- **AGE = the b9 SYSTEM age (a floor)** — see §4 immunity.

## 3. What this patch does (`evaluate_unified.py`, backend-only)

New PURE `_cost_retention` + `_cost_approach_value(...)` + `_cost_triangulation(...)` + the RCN/curve constants + `COST_REANCHOR_NOTE_AR/EN`, placed in the §6 triangulation family. Wired in the b4 region (mutually exclusive with teardown/luxury), precedence **income_led > cost_reanchor_down > §6 widen_down**:

- **SHIP-NOW = the DOWN-re-anchor ONLY** (the §11 Gate-2 SPLIT). Fires when a villa/house on a thin/widened (NOT clean bracket, NOT dispersion-gated a10/a14) market is **OLD** (age-gate ≥10y, closes the new-luxury mis-launch), **over-anchored** (land < market), AND the cost **UNDERCUTS** the market by **>30%** ((market−cost)/cost). Result: reconciled range `[max(land_floor, cost) … market(muted)]`, `range_is_headline`, central muted (NO invented point), **MUC high**, + the §5 cost disclosure (replaces §6's bare condition-widen note). The **cost replaces §6 widen_down's bare-land floor** as the informed lower anchor.
- **GATED-to-next:** the convergent-CONFIRM + the UP-lift (they bias on age-handling — system age there OVER-states cost; need actual-not-system age + the CGIS age-gap recon, §11 (ج)). NOT in this slice.

## 4. 🔴 The system-vs-actual age IMMUNITY (why ship-now is safe)

b9 surfaces the SYSTEM (CGIS) age — typically LOWER than the actual (re-registration zeros the survey date). Lower age → higher retention → higher cost → a HIGHER cost floor → the down-move is LESS aggressive (never over-drops) AND the >30% undercut is HARDER to reach (it PROTECTS convergent cases). **Measured:** V001 56/647/6 at the b9 age 17 → cost ~3.12M → undercut +22% < 30% → does NOT fire (correct); at the ACTUAL ~25 → ~2.91M → +30.6% → would WRONGLY fire. So this slice runs depreciation on the b9 SYSTEM age (a FLOOR) — deliberately conservative. Actual-age handling is the GATED slice's job.

## 5. Verification — empirical evidence

- py_compile ✓ · isolated `test_sprint_2_22_0b11.py` **52/52** (the §2 model on the live anchors; the >30% V001/Marikh separator; the **system-age immunity** [17 no-fire / 25 would-fire]; the **±20% built-ratio sensitivity** [recon C — does NOT flip V001's no-fire]; the age-gate; clean-bracket / dispersion-gated / not-over-anchored / asset-type / no-age exclusions).
- DoD (PYTHONIOENCODING=utf-8): aggregator `run_sprint_2p22p0a_suite.py` **392 ALL COUNTS MATCH** · security **15/15** · surface-honesty **45/45** · broad `2p22p0_pre/run_regression_2p22p0a.py` **80/80** (79→80, +b11; the broad walk caught a real precision-pass regression — the note had reused the forbidden «الصفقات المشابهة» (Sprint 2.22.0a.2.p9) → reworded to «القريبة في النوع والمساحة»; re-run clean).
- **Local E2E (real engine, GIS reachable):**

  | villa | live b10.2 (before) | b11 (after) | Δ |
  |---|---|---|---|
  | Marikh 54/541/6 | thin 5.4M, range [1.9M…5.5M] (bare-land widen_down) | thin 5.4M, range **[2.4M…5.5M]** `cost_reanchor_down` (cost 2,378,094, undercut 128%, BUA 479, retention 0.50) | **floor 1.9M→2.4M** (cost-informed); central/high unchanged |
  | V001 56/647/6 | widened 3.8M [2.5M…3.8M] | **byte-identical** (cost +22%<30% → no fire) | none |
  | Abu Hamour 56/565/21 | bracket 2.4M [2.2M…2.6M] | **byte-identical** | none |
  | Apartment 52/903/90 | refusal | **byte-identical** | none |

- **Live post-deploy smoke v180 (browser-UA curl, Rule #61) = byte-identical to the local E2E:** `/api/health` engine b11 / 3.1.0-sprint2.22.0b.11 / reliable 6 / qars healthy; Marikh `cost_reanchor_down` low **2,400,000** (cost 2,378,094, undercut 128%, bua 479); V001 widened 3.8M [2.5M…3.8M] no-fire; Abu Hamour bracket 2.4M; Apartment refusal. Rule #52 closed MEASURED (live == local).

## 6. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add evaluate_unified.py test_sprint_2_22_0b11.py CHANGELOG_v94.md docs\BRIEF_cost_triangulation_R7.md docs\METHODOLOGY_DRC_qatar_v1.md
git commit -m "Sprint 2.22.0b.11 (§20.9): cost-approach DRC down-re-anchor (ship-now slice)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Post-deploy verification curl (browser-UA, Rule #61)

```
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -H "Content-Type: application/json" ^
  -X POST https://thammen.qa/api/evaluate -d "{\"zone\":54,\"street\":541,\"building\":6}"
```
Expect: `valuation.cost_triangulation.mode = cost_reanchor_down`, `valuation.low ≈ 2,400,000` (was 1,900,000), `amount 5,400,000` (unchanged). 56/565/21 = 2.4M, 56/647/6 = 3.8M, 52/903/90 = refusal — byte-identical.

## 8. What's NOT in this patch (scope boundary)

- **The convergent-CONFIRM + the UP-lift** (V001 → ~3.6M trim, V002/V003 → ~4.0M lift) — GATED-to-next (need actual-not-system age + the CGIS age-gap recon, §11 (ج)).
- **The central-drop to a plain-comp point** — ship-now keeps the central MUTED (no invented number, brief §7#2); the cost is the informed FLOOR only.
- **The dilapidated-luxury finish-dependent floor** (~0.31) — PO-pending v2 refinement; does NOT affect the ship-now anchors (Marikh retention 0.50 ≫ the locked 0.27 floor); shipped with `RESIDUAL_FLOOR=0.27`.
- **The report's two-values display** (MV + forced-sale = MV×0.90, a CONVENTION) — an `index.html`/report change (this slice is backend-only).
- **The soil/geotech factor** (sabkha/karst foundation premium) — v2 GIS refinement; default Simsima-rock = 1.0.
