# CHANGELOG v212 — Sprint 2.22.0b.141 «ترشيق شاشة النتيجة» (result-screen declutter)

**Engine:** `thammen-sprint2p22p0b141-result-screen-declutter` · **api-health** `3.1.0-sprint2.22.0b.141`
**Date:** 2026-07-23 · **Files:** `index.html` (result-screen `show()` + short-report nav), `evaluate_unified.py` (2 version-string lines only), `test_sprint_2_22_0b141.py` (new), + 6 R6/Lesson-2 sibling re-points.
**Class:** 🟢 FRONTEND-ONLY / VALUE-NEUTRAL — `api.py` + the valuation engine UNTOUCHED; the 5-fixture value byte-gate is byte-identical by construction (amount/low/high/method/rule never touched; presentation-only de-duplication + copy).

## 1. Why this matters
The PO's full-site review flagged the screen a user meets first — «تفاصيل مكرّرة» (duplicated details): as soon as property data is entered they land on the **result screen** («not the short report, not the full report — details»), and that screen showed the same content twice. Measured: the **known-unknowns list rendered twice** (the always-visible LIMITS section + again inside the «تحليل» fold), and the fold's label «التفاصيل الكاملة» **collided** with the deepest artifact «التقرير الكامل» AND with two short-report nav buttons that also read «التفاصيل الكاملة» but actually navigate **back** to the result. The naming made the hierarchy unreadable.

## 2. Root cause
- **Known-unknowns ×2:** `_s4bLimits` (always-visible LIMITS) rendered `d.reasoning_trace.known_unknowns` **capped at 6** (`ku.slice(0,6)`); the show() `h` scratch (folded into «التفاصيل الكاملة») re-rendered the SAME array in full (`rtr.known_unknowns.forEach(...)`). The user saw the first 6 up top and all N again in the fold.
- **Naming collision:** the result-screen fold was «التفاصيل الكاملة (التحليل والمقارنات)»; the short-report compact link (@3347, `go('results')`) and the short-report wrapper button (@1354, `go('results')`) were BOTH labelled «التفاصيل الكاملة» — but they navigate **to the result screen**, not deeper. Three different «التفاصيل الكاملة» meaning three different things, one of them colliding with «التقرير الكامل».
- **B1:** the market-pulse band (`_loadPulse`) was gated only on `d.district && d.asset_type` — it could inject under a refusal card (no valuation).

## 3. What this patch does
- **Known-unknowns render ONCE.** `_s4bLimits` is **uncapped** (`ku.forEach` — the full list, always visible, in the LIMITS section where a reader expects it); the **duplicate fold card is removed** from show()'s `h` scratch (nothing lost). The full report keeps its own known-unknowns (`_rtrR.known_unknowns`, untouched).
- **Naming collision resolved.** The result-screen fold → «تحليل إضافيّ (التفاصيل والمقارنات)» / "Deeper analysis (details & comparables)". The two short-report **nav-to-results** labels → «النتيجة» / «→ النتيجة» / "Result" (they navigate back to the result screen — the accurate label). So «التقرير الكامل» / "Full report" is now unambiguously the single deepest artifact.
- **B1** — the pulse band is gated on `hasValuation && d.district && d.asset_type` (it must not render under a refusal card).
- **Deferred (documented):** the trend renders on the result screen twice — the EVIDENCE `_s4bTrendSpark` sparkline **and** the «تحليل إضافيّ» fold bar-chart. Deduping it is **held for a signed honesty review**: the fold bar-chart is the only site carrying the signed **a3/T1.2 «اتجاه تاريخي»** suppressed-slope reframe (when the engine suppresses `slope_pct` on stale/high-MUC data, the headline must NOT present it as a current market rate). Removing it would drop that signed honesty framing → HARD GATE 2. So b141 leaves the trend as-is.

## 4. Verification — empirical
- Isolated `test_sprint_2_22_0b141.py` **22/22**.
- **R14 real-Chromium 390×844** on the live b139 Marikh payload: **known-unknowns dedup PERFECT** (each of the 9 appears EXACTLY ONCE; all 9 shown = uncapped) · fold renamed «تحليل إضافيّ» (old title gone) · value **٢٬٤٠٠٬٠٠٠ byte-identical** · **no overflow** (maxRight 374<390) · **0 console errors** · pulse band renders (valued) · **EN**: fold → "Deeper analysis", dir=ltr, 2,400,000, no overflow, LIMITS → "What we don't see yet" · **AR restore byte-identical**.
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45** (the T1.2 «اتجاه تاريخي» gate GREEN — the trend reframe is retained) · broad walk **ALL FILES GREEN** (**6 R6/Lesson-2 re-points** — b15 fold-title rename · b103 + b29 + b88 short-report nav label «التفاصيل الكاملة»→«النتيجة» · b134 pulse gate +hasValuation · b140 own version pin → version-agnostic; **zero value/security/methodology/compliance assertion weakened** — every rename is a nav label, both targets still `go('results')`; the known-unknowns dedup keeps the full list).
- py_compile OK · `node --check` on all 3 inline scripts OK.
- Personas: **lawyer APPROVE** (nav-label copy only; no claim/disclaimer touched; the known-unknowns list is now shown IN FULL, not truncated — raises transparency) · **linguist APPROVE** («تحليل إضافيّ» / «النتيجة» register-consistent; "Deeper analysis" / "Result" the natural EN).

## 5. Deployment
`git push origin master` (backup first) → `git subtree push --prefix "deploy v2" heroku master` (from the repo toplevel `C:/Thammen`, Rule #43).

## 6. Verification curl (post-deploy, browser-UA #61)
`curl -s -A "Mozilla/5.0" https://thammen.qa/api/health` → `3.1.0-sprint2.22.0b.141`; served `index.html` carries `t('تحليل إضافيّ (التفاصيل والمقارنات)','Deeper analysis (details &amp; comparables)')` + `ku.forEach` + `if(hasValuation&&d.district&&d.asset_type)`; the 5-fixture value byte-gate byte-identical to v304.

## 7. What's NOT in this patch
- The **trend ×2 dedup** (deferred — signed a3/T1.2 honesty review; §3 above).
- The **dead confirm-gate deletion** (`showConfirm`/`confirmScreen`, dormant since b127) — its own sprint (touches ~10 test files with substantive assertions: b32/b133/b9/b3/b2p3/b29/b127/b27/b82/b24).
- **Sprint B** — the backend `_en` twins for the engine note-body arrays (known-unknowns, due-diligence questions, MUC basis, scope-disclaimer catalog, corner evidence, etc.) — next per the approved A → declutter → B sequence.
