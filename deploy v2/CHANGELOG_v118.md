# CHANGELOG v118 — Sprint 2.22.0b.35 (DEF-UX16): buyer financing calculator

**Engine:** `thammen-sprint2p22p0b35-buyer-financing-calc` · **SPRINT_TAG** `2.22.0b.35` · api-health `3.1.0-sprint2.22.0b.35`
**Date:** 2026-06-13 · **Files changed:** `index.html` (the `bcRecalc()` recalc + the buyer calculator in `show()`), `evaluate_unified.py` (the 2 version-string lines), `test_sprint_2_22_0b35.py` (new), `test_sprint_2_22_0b34.py` (R6 format re-point, test-only)
**Class:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT (`api.py` UNTOUCHED; value byte-identical across all roles — مبدأ b24).
**Gate-2:** signed by delegation (study §5: the density/display sprints are value-invariant). **Gate-1:** deploy-on-green (PO «CONTINUE»).

---

## 1. Why this matters

The study §2 «المشترية» persona (أم خالد) lands on the figure and immediately asks the real question: *what's the monthly payment?* Today she has to leave the result, mentally compute an amortization, or open the full short report. DEF-UX16 brings an **illustrative financing calculator** directly under the figure — for the buyer only — so the headline becomes actionable at a glance.

## 2. Root cause + the DRY recon

Recon found the amortization math **already exists**: the b25/b28 short report has `_srPayment(P, downPct, years, ratePct)` (the D3 «ONE allowed value-math» — an indicative amortized monthly payment) + `srRecalcPay()`, live-proven as «القسط ١٠٬٦٧٢» on the امريخ fixture. So UX16 is **DRY** — it reuses `_srPayment` with a result-screen recalc; no new amortization math, no engine change.

## 3. What this patch does (frontend, value-invariant)

- New `bcRecalc()` (beside `srRecalcPay`) — the result-screen calculator's live recalc, reusing `_srPayment` with **separate ids** (`bcDown`/`bcYears`/`bcRate`/`bcPay`) so it never collides with the short-report calculator's `sr*` ids (a different screen).
- In `show()` TIER-1, **under the figure** (after the range/median + the condition/teardown/luxury notes, before the «كيف وصلنا» accordion), **gated on `d.audience==='buyer'`**:
  > «🏦 حاسبة التمويل التقريبية: [20]% دفعة أولى · [25] سنة · [4.5]% فائدة → القسط الشهريّ ≈ **{payment}** — تقديريّ، استشر بنكك»

  Three live inputs (`oninput="bcRecalc()"`); defaults **20% down · 25y · 4.5%** match the signed b28 short-report contract. The «استشر بنكك» disclosure keeps it illustrative, not a binding offer.
- **Only `audience=buyer` sees it** (owner/seller/investor/valuer render exactly as before).

**Value-invariance (structural):** the payment is derived FROM `v.amount` (display-only); `amount`/`low`/`high`/`method`/copy/tier-order are untouched. The engine never sees a financing input.

## 4. Backend / frontend / schema

- **Backend:** ENGINE_VERSION + SPRINT_TAG bump only. `api.py` UNTOUCHED.
- **Frontend:** `bcRecalc()` (reuses `_srPayment`) + the buyer-gated calculator block in `show()`.
- **Schema:** none.

## 5. Verification — empirical evidence

- **py_compile** OK.
- **Isolated** `test_sprint_2_22_0b35.py` **17/17** (E14: `bcRecalc` reuses `_srPayment` [no duplicate math] + reads `bc*` not `sr*`; the calculator gated on `audience==buyer`; defaults 20/25/4.5 [b28 contract]; placed under the figure before the how-accordion `_acc` call; «استشر بنكك» disclosure; no value mutation; payment derived from `v.amount`).
- **Sibling R6 re-point (test-only):** `test_sprint_2_22_0b34.py` pinned `ENGINE_VERSION == b34` literally → format check. b34 = **15/15** after.
- **DoD:** aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface **45/45** · broad auto-walk **103/103 ALL GREEN** (102→103).
- **R14 real-Chromium 390×844** on the live امريخ fixture (`.basket/f_marikh.json`, amount 2,400,000): **buyer → calculator present, القسط ١٠٬٦٧٢ ر.ق/شهر** (= the short-report figure, DRY confirmed) · **owner/investor → NO calculator** (buyer-gated) · **value byte-identical across roles** (2.4M/2.4M/5.4M) · **interactivity** proven (20%/25y → 10,672 · 50%/25y → 6,670 · 50%/15y → 9,180 — correct amortization) · **no overflow** (docScrollW 390 == clientW 390, maxRight 370<390) · **0 console errors/warnings**.
- **api.py untouched** — `git diff --name-only` = index.html + evaluate_unified.py + the 2 test files only.

## 6. Deployment

```
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health         # engine: thammen-sprint2p22p0b35-buyer-financing-calc
curl -s https://thammen.qa/ | findstr /C:"bcRecalc"   # the calculator in the served HTML
```
Plus the 5-anchor value byte-gate (browser-UA curl, #61) — value identical to v205 (frontend/value-invariant).

## 8. What's NOT in this patch

- The affordability guards (DEF-UX8: LTV≤80–90% caps · payment>30%-of-income warning · cost-led alert) — they need an income input; this slice is the calculator only.
- The calculator is buyer-only; other roles' delta content (yield badge for the investor, etc.) are their own slices.
- **NEXT (study §5):** DEF-UX15 (autocomplete entry) · then the §4ب persona features (UX1 keystone comparables [Gate-2+recon] · UX3 apartment refusal · UX9 BUA/RCN · UX8 the affordability guards on top of this calculator).
