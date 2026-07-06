# CHANGELOG v185 — Sprint 2.22.0b.104 «تفاصيل تُفتح بنقرة + لغة أوضح» (R2 — the skeptic's proof + clarity)

**Engine:** `thammen-sprint2p22p0b104-short-report-proof-and-clarity` · **SPRINT_TAG** `2.22.0b.104`
**Date:** 2026-07-06 · **Files:** `index.html` (showShortReport §١/§٧/§٨ + hero + `_srCountUp` + CSS), `evaluate_unified.py` (version) (+ `test_sprint_2_22_0b104.py`; R6 re-points in `test_sprint_2_22_0b80.py` / `test_sprint_2_22_0b103.py`)
**Class:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT (display-only; amount/low/high/method/rule untouched — the 5-fixture villa byte-gate holds by construction).

---

## 2. Why (the 5-seat persona re-study, R2 half)

The card-landing (b103) folded the appendix; b104 makes the **owner-facing details** worth opening — driven
by the persona re-study (Gemini r10 concurred):
- **THE SKEPTIC** («من أين جئتم بالرقم؟»): the actual MoJ transactions behind the median (the b38–b41
  keystone rows) rendered ONLY on the old result screen — the proof was two taps away.
- **RICS valuer / lawyer**: §٧ «للمستثمر» carried a directive tail (excitement-vs-scrutiny) — a valuer
  ESTIMATES, never ADVISES.
- **linguist**: §٨ header «شفافية الدليل — بلا تجميل» — «بلا تجميل» is a marketing/colloquial tail.
- **brand director**: the reveal is the product's emotional peak — deserves one restrained animation.

## 3. What this patch does (`index.html`, inside «عرض التفاصيل»)

- **(1) The skeptic's proof** — a new block right after §١ renders the anonymized MoJ comparable rows
  (`v.comparables` / `v.considered_comparables` — the SAME broadcast the engine already gates, reused, not
  recomputed) in a compact `.thmr-ptab` (date · area · price, newest-first, capped 6) with a leader-aware
  header (market-led «صفقاتٌ مسجّلة مثل بيتك — هي مرجع الرقم» / cost-led «اطّلعنا عليها — ولم تقُد الرقم»)
  + the MoJ + CC BY 4.0 source line. **Graceful-absent** when no rows (verified live on Marikh cost-led).
- **(2) §٧ investor reframe** — the FACTUAL net-yield 5–6% benchmark KEPT; the directive tail neutralized to
  benchmark language; **«مقاييس سوقية استرشاديّة، وليست توصيةً استثماريّة»** added (lawyer persona).
- **(3) §٨ register fix** — «شفافية الدليل — بلا تجميل» → **«شفافية الأدلّة»** (linguist).
- **(4) Micro-delight** — `_srCountUp()`: the hero value counts up ~800ms on reveal (easeOutCubic), invoked
  after the QR render; **reduced-motion → no-op**; **ends on `fmt(amount)`** exactly (value-invariant).
  The scarce (n<5) range-only hero keeps its two static figures (no count-up on a range).

## 4. VALUE-INVARIANT

Display-only. The count-up animates display digits toward `data-countup` then sets `fmt(target)` — the DOM
ends on the true amount (verified live: settles on ٢٬٤٠٠٬٠٠٠ / 2,400,000). `v.amount*` math = the three
DISCLOSED conventions (×0.90 / ×1.10 / ×1.30) unchanged. `api.py` + engine untouched (2 version lines).

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b104.py` **19/19** · `node --check` OK · py_compile OK.
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **159/159
  ALL GREEN** — **2 R6/Lesson-2 re-points** (b80 + b103 §٨ header pins «شفافية الدليل — بلا تجميل» → «شفافية
  الأدلّة»; intent preserved — the §٨ section still exists, register-fixed; zero assertion weakened).
- **R14 real preview 375×812** (DOM-measured): market-led (56/565/21) → proof table 6 rows, header «صفقاتٌ
  مسجّلة مثل بيتك — هي مرجع الرقم», §٨ «شفافية الأدلّة», §٧ «وليست توصيةً استثماريّة», count-up settles on
  ٢٬٤٠٠٬٠٠٠ · cost-led (Marikh) → proof **gracefully absent** (no rows), count-up settles on ٢٬٤٠٠٬٠٠٠ ·
  **EN mode**: proof header «Registered sales like yours — the reference behind the number» + «not an
  investment recommendation» + hero 2,400,000 · **0 console errors** · **no horizontal overflow** (375==375).

## 6. Deployment

- `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112).

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.104`.
- served `index.html` carries `thmr-proof` + `شفافية الأدلّة` + `وليست توصيةً استثماريّة` + `_srCountUp`.
- the 5-fixture villa byte-gate byte-identical to v275 (browser-UA #61).

## 8. What's NOT in this patch

- The Layer-2 question-form fold TITLES + the neighborhood price-position line + the refine-screen copy pass
  are DEFERRED: the price-position line needs its own recon (the subject's position isn't cleanly emitted for
  a market-led case), and the refine-copy pass folds into **R3 (b105)** the register lock (sweep the FINAL
  copy). The interstitial + sticky value-bar were scoped out (the count-up is the highest-value, lowest-risk
  micro-delight).
- The register/language lock (r11 flip-list) = **R3 (b105)** · the RICS disclosures = **S1 (b106)**.
