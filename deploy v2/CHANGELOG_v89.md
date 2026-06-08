# CHANGELOG v89 — Sprint 2.22.0b.8 (§6 v2: income OPEX alignment)

**Engine:** `thammen-sprint2p22p0b8-income-opex-align` · **SPRINT_TAG** `2.22.0b.8` ·
**api/health** `3.1.0-sprint2.22.0b.8` · **Date:** 2026-06-08
**Files changed:** `evaluate_unified.py` (3 surgical edits + version bump) ·
`test_sprint_2_22_0b8.py` (NEW, 19 checks) · `CHANGELOG_v89.md` (this).
**`api.py` + `index.html` UNTOUCHED.**
**Gate-2** (the alignment changes the villa-calibrated income value — income_led headline + the
displayed cross-check) — delegated via PO «افعل الأصوب، بعد استبعاد البيتا» (the §20.18/§20.41
precedent: «افعل الأصوب» on a methodology decision = Gate-2 sign-off by delegation). **Second slice
of §6 v2** (the deferred opex 0.20 correctness pass from §20.40/§20.41).

---

## 1. Why this matters (user-visible problem)

§6 (b6/v173 + b7/v174) lets the villa headline **income-LEAD** on a grounded subject rent ÷ a
*calibrated* villa cap rate. But the engine computed NOI with a **flat opex 0.23** while the villa
cap rate is calibrated **net of opex 0.20** — so every villa-calibrated income was **under-stated by
0.77 / 0.80 = −3.75%**. The very first beta subject rent on a villa-calibrated cell would have
produced an income_led value ~3.75% too low; the displayed income cross-check on calibrated
surfaces (even no-rent) carried the same understatement. A uniform correctness pass closes it.

## 2. Root cause

`cap_rate_calibrator.OPEX_RATIO['villa'] = 0.20` (+ villa `service_charge = 0`, `cap_rate_calibrator.py:108`
→ exactly 0.20) is the basis of **every stored villa `net_yield` / `cap_rate`**. The engine fed a
single flat constant:

```
evaluate_unified.py:360  OPEX_RATIO_RESIDENTIAL = 0.23
evaluate_unified.py:1628 noi = annual_rent * (1 - OPEX_RATIO_RESIDENTIAL)   # 0.23
evaluate_unified.py:1629 income_value = noi / cap_rate                       # cap@0.20 for villa
```

→ pairing NOI@0.23 with a villa cap rate calibrated@0.20 ⇒ income × 0.77/0.80 = **−3.75%**.
`income_led` reads this `income['value']` (`_income_triangulation:4758`), so the bias entered the
headline whenever income leads. **Compound is 0.23 on both sides (already consistent).** The other
three opex sites — `_build_investor_sections_fallback` (1893/1901), `_build_fast_listing_only_response`
(2633), `_build_fast_income_only_response` (2781) — pair a **hardcoded** cap rate with opex 0.23 →
internally consistent, no mismatch → out of scope.

## 3. What this patch does (backend only — `evaluate_unified.py`)

1. **`_CALIB_OPEX_BY_ASSET`** (new constant by `OPEX_RATIO_RESIDENTIAL`) — `{villa, standalone_villa,
   house: 0.20; compound_small, compound_large: 0.23}`, **mirroring `cap_rate_calibrator.OPEX_RATIO`**
   (a sync-guard test pins the mirror).
2. **`_build_income_crosscheck`** — opex = the calibration opex **ONLY when the rate is calibrated**
   (`cap_rate_provenance['source'] == 'calibrated'`); a hardcoded/fallback rate's implied opex is
   unknown → keep **0.23** (byte-identical). `noi = annual_rent * (1 - opex_ratio)`.
3. The exported **`opex_ratio`** field now reflects the value actually used.

So: villa-calibrated → 0.20 (the fix); compound-calibrated → 0.23 (unchanged); any
hardcoded/fallback → 0.23 (byte-identical).

## 4. Scope boundary (measured, not assumed)

The fix touches the **single mismatched site** (`_build_income_crosscheck`). Recon confirmed the
other three opex sites use hardcoded caps + 0.23 (internally consistent) — **not touched**.

## 5. Verification — empirical evidence (measured before/after on the live engine, local GIS)

**Isolated** `test_sprint_2_22_0b8.py` — **19/19** (E14, the production `_build_income_crosscheck`):
sync-guard vs the calibrator · villa-calibrated→0.20 · compound-calibrated→0.23 · fallback→0.23
byte-identical · the 0.80/0.77 ratio · house→None · **real-DB** امريخ الجنوبي cell→0.20.

**DoD** (re-measured, `PYTHONIOENCODING=utf-8`): aggregator **392/392** · security **15/15** ·
surface-honesty **45/45** · broad auto-walk **77/77** (76→77, +b8 test; 142.5s, zero regression).

**Blast-radius (before → after, real engine):**

| case | before | after | verdict |
|---|---|---|---|
| A1 56/565/21 no-rent (fallback villa) | income 2,772,000 | **2,772,000** | byte-identical (source≠calibrated) |
| A2 54/541/6 no-rent (calibrated cross-check) | income 2,150,921, noi 110880, net 2.04% | **2,234,724, noi 115200, net 2.12%** | cross-check corrected +3.9%; **headline 5.4M byte-identical** (income doesn't lead) |
| A3 55/296/13 / A4 52/903/90 | — | **byte-identical** | no income / refusal |
| K 54/541/6 +rent 15k (income_led) | amount **2.7M** (2,688,652) low 2.3M high 3.0M | amount **2.8M** (2,793,404) low 2.4M high 3.1M | the intended Gate-2 correction |
| K2 @400-600 +rent 15k (income_led, no borrow) | 2.7M | **2.8M** | same |

**Honest note:** the 4 anchor **headlines** stay byte-identical (income_led needs a subject rent; no
no-rent anchor leads), but the A2 `income_approach` **block** is NOT byte-identical — it was a wrong
(understated) number, now correct.

## 6. Deployment

```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy, browser-UA — Rule #61)

```
curl -s https://thammen.qa/api/health                              # -> 3.1.0-sprint2.22.0b.8
curl -s -A "Mozilla/5.0 ... Chrome/126 Safari/537.36" -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" \
  -d "{\"zone\":54,\"street\":541,\"building\":6,\"rental_income\":15000}"   # -> income_led 2,800,000
# 4 no-rent anchors -> 2.4M / 5.4M / 2.6M / refusal headlines byte-identical
```

## 8. What's NOT in this patch (scope)

- The other 3 opex sites (investor-fallback / fast-listing / fast-income) — hardcoded cap + 0.23,
  internally consistent, **not touched**.
- **Remaining §6 v2:** Fork C (a18/override-aware `_lookup_calibrated_cap_rate` — works today GIS↔GIS,
  robustness not a live bug) · (ii) age-adjusted rent (gated on auto-age reliability, E22).
- **Live payoff stays BETA-GATED:** income_led needs a subject rent → live no-rent traffic is
  headline-unaffected; only the displayed income cross-check on villa-calibrated surfaces moves. The
  durable no-rent gap-narrower remains **B-2** (condition axis, PARKED n≥20).
