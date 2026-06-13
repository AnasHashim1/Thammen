# CHANGELOG v123 — Sprint 2.22.0b.40 «حواجز القدرة على التحمّل / LTV» (DEF-UX8)

**Engine** `thammen-sprint2p22p0b40-affordability-guards` · **SPRINT_TAG** `2.22.0b.40` ·
api-health `3.1.0-sprint2.22.0b.40`.
**Files:** `index.html` (DEF-UX8 guards on the b35 calculator) · `evaluate_unified.py`
(the 2 version-string lines ONLY) · `test_sprint_2_22_0b40.py` (new) · `CHANGELOG_v123.md` (new).
**Class:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT (engine diff = the 2 version lines; `api.py` UNTOUCHED).
**Gate-2:** delegated — Anas «افعل الأصوب · لك كافة الصلاحيات» (the fuller income-aware option).
**Gate-1 (the production push):** **DEFERRED to Anas's terminal** — built + verified on the
development branch `claude/continuation-2tfnak`; the Claude-Code-on-the-web sandbox has no Heroku
access and `thammen.qa`/khazna are outside its egress allowlist (see §6).

---

## 1. Why this matters (user-visible problem)

DEF-UX8 (ISSUES_LOG §4ب, personas أم خالد · البنك · المهندس). The b35 buyer financing calculator
(v206) shows an indicative monthly payment, but it gives the buyer **no affordability frame**: nothing
tells them whether the implied loan exceeds the QCB lending cap, whether the instalment is a sane share
of their income, or that — on a **cost-led** valuation (an old over-anchored villa) — the headline is a
conservative DRC **floor** they should not finance *above*. A buyer can read «القسط ١٠٬٦٧٢ ر.ق/شهر» and
have no idea it is built on a 95% loan or on 60% of their income.

## 2. Root cause

The b35 block (`index.html`, `show()`, the `if(d.audience==='buyer'&&v.amount)` region) rendered the
amortization output only. The three signals the personas asked for — **LTV**, **instalment-vs-income**,
**cost-led** — were never derived, even though all the inputs were already on the client
(`v.amount`, the calculator's `down%`, the computed payment, and the b20 broadcast
`v.leadership.leader`). The one genuinely-missing input — the buyer's monthly income — needed a small
**client-side-only** field.

## 3. What this patch does

**`index.html` — 3 surgical edits (display-only):**

1. **New pure helper `_bcGuards(amount, downPct, payment, income, costLed)`** (next to `bcRecalc`) →
   returns guard rows as HTML, **no new value-math** (it reuses the b35 `payment` as an *input*):
   - **(1) LTV line** — financed share `= 100 − down%`; warn (⚠️ + `--warn`) when `> 80`. Copy:
     «نسبة التمويل ≈ {ltv}% — حدّ مصرف قطر المركزي للمقيمين عادةً ≤ 80% (≤ 75% لغير المقيمين/العقار
     الثاني)؛ راجع بنكك.» (guidance, not law — «راجع بنكك»).
   - **(2) DBR / instalment-vs-income** — **ONLY when an income is entered**: ratio `= payment/income`,
     warn when `> 30`. Copy names the prudent housing rule ≤30% and notes the QCB total-DBR ceiling is
     higher but covers all obligations.
   - **(3) cost-led alert** — when `v.leadership.leader==='cost'`: «⚠️ تقديرك مرتكز على الكلفة … لا
     تموّل فوق هذا الرقم؛ سعر السوق قد يكون أعلى بلا مبرّر بنائيّ.»
   - All Latin/numeric tokens in `dir="ltr"` islands (Rule #25).

2. **The b35 calculator block** gains an **optional monthly-income input** (`#bcIncome`, labelled
   «دخلك الشهريّ (اختياريّ، لا يُرسَل)»), a **Qatar interest-range hint** «نطاق الفائدة في قطر عادةً
   4–6%», and a `#bcGuards` container seeded with the initial guards via `_bcGuards(...)`. The cost-led
   flag is derived from the broadcast `v.leadership.leader==='cost'`.

3. **`bcRecalc()`** now also refreshes `#bcGuards` from the SAME inputs (down% + payment + the DOM
   income + cost-led), reusing `_srPayment` for the payment (DRY) exactly as before.

**Privacy (the hard contract):** the income lives ONLY in the DOM input; `bcRecalc` reads it
client-side and **never POSTs it** — consistent with a24/DPIA «we do not store the address». Value is
display-only → `v.amount/low/high/method/rule/leadership` byte-identical.

**Scope (Rule #38):** buyer-only (the b35 gate is unchanged); other roles see nothing new.
`evaluate_unified.py` = the 2 version lines; `api.py` UNTOUCHED.

## 4. Backend / frontend / schema

- Backend: **none** beyond ENGINE_VERSION/SPRINT_TAG. No new fields, no schema change, `api.py` UNTOUCHED.
- Frontend: `index.html` (the 3 edits above).
- Schema: unchanged.

## 5. Verification — empirical evidence (this sandbox)

- **py_compile** `evaluate_unified.py` → OK.
- **`node --check`** on the full extracted inline JS (165,880 chars, 2 `<script>` blocks) → **JS OK**
  (the syntax half of R14).
- **Isolated `test_sprint_2_22_0b40.py` → 29/29** (E14, reads the REAL index.html): `_bcGuards`
  defined + the 3 guard rows + LTV=100−down / warn>80 / QCB caps · DBR gated on income>0 + ≤30% ·
  cost-led gated on `leader==='cost'` · the income input + «لا يُرسَل» label + the 4–6% hint · bcRecalc
  refreshes `#bcGuards` + reads `#bcIncome` + still DRY on `_srPayment` + no sr* collision · b35 gate +
  placement intact · **no v.amount/low/high mutation** · **`bcIncome` never enters any request body**.
- **Siblings green WITHOUT re-points:** b35 17/17 · b37 22/22 · b31 36/36 · b34 15/15 · b29 32/32.
  (b39 carries no exact-version pin → no R6 re-point needed.)
- **b-series frontend sweep:** 39 green; the only 2 non-passing (b24, b25) fail at `import api` because
  **`fastapi` is not installed in this sandbox** — an environment gap, NOT a regression (those tests
  don't touch the calculator; `api.py` is untouched; they pass on the deploy host).

**DEFERRED to Anas's environment (cannot run here):** the curated aggregator (392) · security (15) ·
surface-honesty (45) · the broad auto-walk (→108, +b40) · the R14 real-Chromium 390×844
overflow/console pass · the live two-lane smoke. See §6.

## 6. Deployment

> The web sandbox cannot reach Heroku, and `thammen.qa`/khazna are off its egress allowlist, so the
> production push + the GIS-dependent DoD/E2E/live-smoke are **Anas's terminal** (Rule #43; the «Go»/
> «ادفع» word gates the production push per the b38/b39 lesson — the safety classifier blocks it on
> generic delegation).

```
cd /d "C:\Thammen\deploy v2"
python -m pytest -q            # or the project DoD runner: aggregator 392 / security 15 / surface 45 / broad 108
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

Then the live smoke (browser-UA curl, Rule #61) on the 5-anchor value byte-gate + a buyer-role render
of the guards.

## 7. Verification curl (post-deploy, Anas)

```
curl -s https://thammen.qa/api/health | grep -o '"engine_version":"[^"]*"'   # → ...b40-affordability-guards
# served HTML carries the new surfaces:
curl -s -A "Mozilla/5.0 ... Chrome/124 Safari/537.36" https://thammen.qa/ | grep -c "_bcGuards\|bcIncome\|نطاق الفائدة في قطر"
# value byte-gate (must be identical to v210): امريخ 2.4M cost-led · V001 3.8M · المعراض 2.6M · أبو هامور 2.4M · شقق refusal
```
R14 (buyer role, 390×844): the calculator shows LTV + the income field + the 4–6% hint; entering a
small income flips the DBR row to ⚠️; a low down-payment flips the LTV row to ⚠️; on a cost-led anchor
(امريخ) the cost-led alert shows; **0 console errors, no overflow**; non-buyer roles unchanged.

## 8. What's NOT in this patch (scope boundary)

- **No income is sent to the server** — DBR is computed client-side only (a24/DPIA). No instrumentation,
  no capture.
- **No value/methodology change** — the guards read existing fields; the headline is byte-identical.
- The LTV/DBR thresholds are **guidance** (QCB resident ~80% / non-resident ~75%; housing ≤30%), framed
  «راجع بنكك» — not a binding offer or a legal assertion.
- **NEXT (ISSUES_LOG §4ب remainder, all need a signed brief / product decision):** the cost-led
  «considered-but-didn't-lead» pool + the full geo pool (deferred from b38/b39) · the lighter §4ب
  display items (UX4 freshness banner + market-adj slider · UX6 improvement-delta) · **DEF-UX5** =
  Gate-2 EN-localization project · **DEF-UX15** blocked (QARS data-drain). The «التقدير السوقي» term
  remains PROVISIONAL.
