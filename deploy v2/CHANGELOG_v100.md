# CHANGELOG v100 — Sprint 2.22.0b.17 — Screen 5: the full report + DEF-12 (two-values display)

**Engine:** `thammen-sprint2p22p0b17-screen5-full-report-def12` · **SPRINT_TAG** `2.22.0b.17` ·
**api/health** `3.1.0-sprint2.22.0b.17` · **Files:** `index.html`, `evaluate_unified.py` (2 version-string
lines only), `test_sprint_2_22_0b17.py` (new) · **Baseline:** b16 / Heroku v185 · **Date:** 2026-06-10 ·
**FRONTEND-ONLY — VALUE-INVARIANT** (Gate-2 signed by delegation, the screens-4/5 brief; Gate-1
deploy-on-green). **Slice 3 of the PO execution order (b15 ✓ → b16 ✓ → b17) — renumbered from the screens
brief's internal "b16" slot (the B-2 early slice took b16).**

---

## 1. Why this matters

The owner journey's fifth screen — the **shareable report** — didn't exist: «التقرير الكامل» printed the
raw screen-4 stack (the Marikh-PDF artifacts: card splits, no A4 sizing). Screen 5 is also the **D-3
instrument**: the artifact Anas hands valuers/brokers to collect GT. And per the execution order it lands
AFTER b16 so the report prints the **re-anchored central** (Marikh 3.4M, not the 5.4M raw thin median).

## 2. What this patch does (FRONTEND-ONLY)

- **NEW `#reportScreen` (screen 5)** + `openReport()`/`showReport(d)` — rendered from the SAME response
  (`window._lastResult`, the b2.3 no-second-fetch pattern). The b15 TIER-3 «📄 التقرير الكامل» CTA rewires
  from `printReport()` to `openReport()` (exactly the rewire b15 documented).
- **The §3 report structure (print + share):** cover (brand + address/PIN + date + staleness banner) →
  the FULL MVU/RICS clause + the a8 standards note (all OPEN — no accordions in a report) → headline range
  + tier badge + the figure's honesty notes (condition · b16 OSR · b11/b13 cost · B-1 floor · b12 hbu ·
  cite-n) → **DEF-12** → evidence-quality panel → decomposition + 10-Year + strata → known-unknowns →
  property basis (b9) + footprint (b10) → methodology (a4 bare line) + **the a25 CC BY 4.0 attribution
  CLONED AT RUNTIME from the live `.src-credit` node** (zero copy duplication) → the audience brief
  sections → footer: «📌 تقدير سوقي آلي وليس تقييماً معتمداً» (+ the a20 status) + engine version +
  timestamp + **the GT hook** («هل لديك سعر بيع فعليّ لهذا العقار أو تقييم معتمد؟ شاركه لتحسين الدقّة —
  واتساب ‎+974 70177761‎» — the Terms' own signed channel, PHASE0_b17 §3; feeds the D-3 kit targets).
- **DEF-12 — two-values display (the §11 Q4 multi-AI «ship» verdict):** Market Value (the live range +
  median) + **Forced-Sale indication = central × 0.90**, labelled verbatim «قيمة بيع جبري إرشادية (عُرف
  سوقي ×0.90) — ليست تقييم تصفية معتمداً». **Report-only (NOT screen 4); pure display math on the existing
  amount — no engine change.** (Marikh: MV 3,400,000 → forced-sale indication 3,060,000.)
- **ONE b14-coherent voice across screens 4 + 5:** the MUC clause + decomposition + 10-Year/substantiality
  + strata blocks were EXTRACTED VERBATIM from `show()` into shared builders (`_mucFields`/`_mucCardHtml`/
  `_decompHtml`/`_substHtml`/`_strataHtml`) — both screens render the same sections from the same code
  (the b14 Case-A narrative + cross-lines ride along automatically). Screen 4's output is unchanged (the
  builders carry the original inner HTML; the report's MV card deliberately uses plain `.rc`, NOT
  `calc-block` — the a8 contract pins that visual to the screen-4 valuation card exactly once).
- **A4 print path:** `@page { size: A4; margin: 12mm }` + a dedicated `printing-report` body class
  (`printReportA4()`) that prints the report screen alone; DEF-12/cover/footer page-break protected.
  The screen-4 print path (`printReport()` + accordion force-open) is unchanged.
- **Refusal path:** the report prints the engine's own `reason_ar` + the MVU clause — no value, no DEF-12.

## 3. Verification — empirical evidence

- py_compile OK (node absent → R14 Chromium = the JS gate); inline-JS brace/paren/bracket balance 0/0/0;
  all 9 b17 functions defined once.
- **Isolated `test_sprint_2_22_0b17.py` 33/33** (screen + entry + CTA rewire · shared-builders defined +
  used by show() + inner content intact · the §3 structure ORDER · DEF-12 math/label/report-only ·
  attribution clone · footer/GT-hook/staleness · A4 print path). Siblings: b15 **49/49** (2 checks updated
  to the b17-anticipated rewire + the shared-MUC refactor) · b16 **38/38** · b3 **14/14** · b2.2 **26/26** ·
  calc-visual **62/62** (the report card dropped `calc-block` to preserve the exactly-once contract).
- DoD: aggregator **392/392 (ALL COUNTS MATCH)** · security **15/15** · surface-honesty **45/45** · broad
  auto-walk **86/86** (85→86, + the new test).
- **Local E2E (real engine, live GIS):** the b16 expected-moves table EXACT under the b17 tree — Marikh
  3.4M [2.4M…5.4M] + decomposition coherent; V001 3.8M / 2.4M / 2.6M / refusal byte-identical.
- **R14 Chromium (EXECUTED):** results→report flow 0 console errors; the report renders cover + full MVU +
  range headline + **DEF-12 (3,400,000 / 3,060,000 + the verbatim label)** + OSR note + evidence +
  decomposition + strata + basis + the attribution clone + not-certified + GT hook; **no accordions in the
  report**; screen 4 post-extraction still carries decomposition/strata in its detail accordion (+
  `_substHtml` proven on a synthetic 10-Year payload — absent from bare payloads by design); refusal
  report = honest reason, no DEF-12; print-class mechanics proven; no overflow (mobile maxRight 370<390;
  desktop 1265<1280).

## 4. Deployment

```
heroku auth:whoami
git add index.html evaluate_unified.py test_sprint_2_22_0b17.py test_sprint_2_22_0b15.py CHANGELOG_v100.md
git commit -m "Sprint 2.22.0b.17: screen-5 full report + DEF-12 (VALUE-INVARIANT)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 5. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health
curl -s -A "Mozilla/5.0 ... Chrome/120" -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"
```
Expect: health b17; Marikh **3.4M** + old_stock_reanchor (b16 unchanged); 4 anchors byte-identical; the
served `index.html` carries `reportScreen` + `showReport` + «قيمة البيع الجبري الإرشادية».

## 6. What's NOT in this patch (scope boundary)

Any value/method change · server-side PDF generation · email/sharing infrastructure · apartment surfaces ·
screens 1–3 redesign · DEF-12 on screen 4 (report-only by design) · the b11 low>high inversion micro-fix
(deferred, §20.50).
