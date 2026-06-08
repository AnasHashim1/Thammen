# CHANGELOG v88 — Sprint 2.22.0b.7 (§6 v2: cross-bracket yield-borrowing)

**Engine:** `thammen-sprint2p22p0b7-income-bracket-borrow` · **SPRINT_TAG** `2.22.0b.7` ·
**api/health** `3.1.0-sprint2.22.0b.7` · **Date:** 2026-06-08
**Files changed:** `evaluate_unified.py` (3 surgical edits + version bump) ·
`test_sprint_2_22_0b7.py` (NEW, 22 checks) · `docs/PHASE0_R7_income_v2_600-900_recon.md` (NEW recon) ·
`CHANGELOG_v88.md` (this). **`api.py` + `index.html` UNTOUCHED.**
**Gate-2** (the borrowing methodology changes the income_led headline when it fires) — delegated via
PO «افعل الأصوب» (the §20.18 precedent: «افعل الأصوب» in direct response to a methodology
recommendation = Gate-2 sign-off by delegation). **First slice of §6 v2** (the deferred income-LEAD
reach fix from §20.40).

---

## 1. Why this matters (user-visible problem)

§6 (b6/v173) made the villa headline income-LEAD on a grounded subject rent — but **only at the
400-600 plot bracket**, because `_income_triangulation`'s income_led gate requires a *calibrated*
(reliable/indicative) cap-rate cell, and `_lookup_calibrated_cap_rate` queries **strictly at the
subject's plot bracket**. The two flagship over-anchored villas are both **600-900**:

- **امريخ الجنوبي 54/541/6** — condition-blind comparison guess **5.4M** (defensible ~3.0–3.4M).
- **المعمورة (villa-6) 56/647/6** — comparison ~3.8M (clears ~2.9M).

A Phase-0 recon (`docs/PHASE0_R7_income_v2_600-900_recon.md`) proved the §20.40-deferred fix
("calibrate 600-900 yield cells") is **data-infeasible**: **0 of 187** villa cells reach usable at
600-900 (المعمورة sale-side n=7, MoJ frozen; امريخ rent-side 0, the §20.38 deep crawl already
failed). So even with a beta subject rent, a 600-900 villa fell to `widen_down` — never grounded.

## 2. Root cause

`_lookup_calibrated_cap_rate` (evaluate_unified.py:399) bound the SQL to the subject bracket
(`WHERE asset_type=? AND size_bracket=?`) and returned `(None, None)` when that exact cell was thin →
income computed with the 4% hardcoded fallback → `cap_rate_provenance.source != 'calibrated'` →
`_income_triangulation`'s `calibrated` gate (4726) False → **income_led cannot fire at 600-900**.
The real blocker was never "no rent" or "no 600-900 cells" — it was that the lookup **would not
borrow the area's usable 400-600 yield** for a 600-900 subject.

## 3. What this patch does (backend only)

**Net yields are bracket-stable WITHIN an area (≪ the cross-area spread)** → the area's usable cell
is a defensible yield for an adjacent bracket, with disclosure + MUC-high.

1. **`_lookup_calibrated_cap_rate`** — pull ALL usable cells for the asset (any bracket) and filter
   to the subject's area in Python. **Prefer the subject's EXACT bracket** (byte-identical to the
   pre-v2 path); only when the exact bracket has no usable cell, **borrow the area's best usable cell
   (highest n, any bracket)**. New provenance: `bracket_borrowed`, `subject_bracket`,
   `borrowed_from_bracket`, `size_bracket`, + a `method_ar` borrow disclosure.
2. **`_income_triangulation`** — a borrowed yield **forces MUC high** even on a small income↔comparison
   spread; carries `bracket_borrowed` / `borrowed_from_bracket`.
3. **income_led note** — appends an AR+EN borrow disclosure ("yield borrowed from the area's 400-600
   bracket — net yields are stable across brackets within an area").

**Additive + value-invariant on live traffic:** borrowing fires ONLY when a subject rent exists at a
bracket with no usable cell. No live no-rent anchor is affected; the exact-bracket (400-600) path is
byte-identical.

## 4. Verification — empirical evidence (MEASURED 2026-06-08, `PYTHONIOENCODING=utf-8`)

**E2E on the real engine (local GIS) — `.b7_e2e.py`:**

| case | b7 result | vs b6 |
|---|---|---|
| **مريخ 54/541/6 DEFAULT (600-900) + rent 15k** | **income_led 2.7M** via borrow (cap 5.16% n=46 reliable, comp 5.43M demoted, MUC high, disclosure shown) | **was widen_down** → KEYSTONE ✓ |
| مريخ 54/541/6 @700 (600-900) + rent 16k | income_led 2.9M via borrow | new path ✓ |
| 56/565/21 default (no rent) | 2.4M comparison_bracket, tri=None | byte-identical ✓ |
| 54/541/6 default (no rent) | 5.4M widen_down (1.9–5.5M, range_is_headline, MUC high) | byte-identical ✓ |
| 55/296/13 default | 2.6M, tri=None (land-anchored) | byte-identical ✓ |
| 52/903/90 default | None / insufficient_data | byte-identical ✓ |
| 54/541/6 @400-600 + rent 15k (b6 regression) | income_led 2.7M, **borrowed=False**, MUC moderate | identical to b6 ✓ |

**Isolated** `test_sprint_2_22_0b7.py` **22/22** (exact byte-identity, borrow flags, token match across
zone variants, no-cell → None, MUC-high-on-borrow, no leak on the exact path). **DoD:** aggregator
**392/392** · security **15/15** · surface-honesty **45/45** · broad walk **76/76** (75→76, +b7 test,
124.5s, no flake). py_compile OK.

## 5. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add evaluate_unified.py test_sprint_2_22_0b7.py docs/PHASE0_R7_income_v2_600-900_recon.md CHANGELOG_v88.md
git commit -m "Sprint 2.22.0b.7 (§6 v2): cross-bracket yield-borrowing — 600-900 villas income-LEAD on a subject rent"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
🔴 **Gate-1 (Heroku push) requires explicit PO «go».** Smoke = browser-UA curl (#61).

## 6. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health    # expect engine ...b7 / 3.1.0-sprint2.22.0b.7
# 4 anchors must stay byte-identical (no rent → no income_led): 56/565/21=2.4M, 54/541/6=widen 5.4M,
# 55/296/13=2.6M, 52/903/90=refusal
curl -s -X POST https://thammen.qa/api/evaluate/details -A "Mozilla/5.0 ... Chrome/124 Safari/537.36" \
  -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6,\"rental_income\":15000}"
# expect income_triangulation.mode=income_led, bracket_borrowed=true, borrowed_from_bracket=400-600, ~2.7M
```

## 7. What's NOT in this patch (scope boundary, #38 + #42 deferred)

- **opex 0.20 alignment** — the engine NOI uses opex 0.23 while the calibrated yield assumes 0.20 →
  income_led understates ~3.75% (a pre-existing b6 issue on the 400-600 path too). A uniform
  correctness pass with its own blast-radius measurement. **Deferred (fast-follow).**
- **Fork C (a18/override-aware lookup)** — `_cap_area_token` already GIS↔GIS-matches both flagship
  cells (§20.39); pure robustness, **not a live bug. Deferred.**
- **(ii) age-adjusted rent** — opportunistic no-input grounding; the b6 brief already deferred it
  (B3 = ship i+iii first). Needs auto-age-reliability measured (E22). **Deferred.**
- **The live payoff is beta-gated** — income_led needs a subject rent (`actual_provided`). On live
  no-rent traffic Marikh/villa-6 stay `widen_down`; this slice is "ready-when-rents-flow" (the beta).
- **Borrow soundness** uses the corpus-wide net-yield clustering + the [land_floor, cost_ceiling]
  clamp + MUC-high + disclosure as the rails; a within-area cross-bracket spread study is data-limited
  (few areas have usable cells at 2+ brackets) and noted for a future calibration pass.
