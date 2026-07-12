# CHANGELOG v207 — Sprint 2.22.0b.130 «توضيح وجه الكلفة» (cost-led short-report face «why lower»)

**Engine:** `thammen-sprint2p22p0b130-costled-face-why` · **api-health:** `3.1.0-sprint2.22.0b.130`
**Files:** `index.html` (+11/−1), `evaluate_unified.py` (2 version lines) · tests: `test_sprint_2_22_0b130.py` (new), `test_sprint_2_22_0b92.py` + `test_sprint_2_22_0b129.py` (R6 re-points)
🟢 **FRONTEND-ONLY / VALUE-NEUTRAL** — `api.py` + the valuation engine UNTOUCHED; amount/low/high/method/rule byte-identical.

## 2. Why this matters
A **6-persona panel** (owner · buyer · seller · appraiser · lawyer · linguist) reviewed the short report. Unanimous: it is **short enough + well-structured** (a 1.6-screen face → «عرض التفاصيل» → «ملحق المختصّين»). One real gap, in ONE case: on a **cost-led property with a wide floor↔ceiling gap** (e.g. Marikh 2.4M floor vs a 5.4M market ceiling), the owner saw two very different numbers while the honest «why my number is the lower one» explanation was **folded** — leaving only a terse specialist legend («الأرضية = مرتكز الكلفة … · السقف = وسيط …») on the face. That reads as jargon to the owner AND leaves the ceiling un-qualified (mis-anchor risk: the seller over-asks; it reads as implied worth). Both angles converged on ONE fix.

## 3. Root cause
The honest explanation ALREADY EXISTS (`showShortReport` `basisLn`/`neigh`, `index.html:2870/2877`) but b129's lean moved it behind «عرض التفاصيل». The face bracket rendered only the terse `_anchorLegend` («مرتكز الكلفة»/«المُهلَك»), gated on `cs==='cost'||geo_full` (`index.html:2985`).

## 4. What this patch does
- Splits the gate: the terse `_anchorLegend` now fires for **geo_full ONLY** (its string kept verbatim → b92/b105 contract intact).
- Adds `_costFaceWhy` (cost-led ONLY) — ONE plain owner line qualifying BOTH endpoints, a **condensation of the existing `basisLn`+`neigh` vocabulary**, rendered as a `.tleg` inside the tiers block right after `_anchorLegend`:
  > «رقمُنا هو الأرضية (كلفةُ إعادة البناء)، لأنّ صفقات بيوتٍ مثل بيتك قليلة؛ والسقف شريحةٌ أعلى سعراً في منطقتك (استدلالاً بالسعر لا معاينةً) — ليس فئةَ بيتك ولا قيمةَ بيعه اليوم.»
- **b100 honesty preserved:** the ceiling is «شريحةٌ أعلى سعراً … استدلالاً بالسعر لا معاينةً» — NEVER «فاخر» asserted as fact.
- The full «لماذا» (basisLn/neigh) stays folded in «عرض التفاصيل» — nothing deleted. The endpoints labels («الأرضية السعرية»/«السقف السوقي») kept.
- **Scope (measured):** cost-led ONLY. Market-led faces (Abu Hamour, spread 1.18) render NO bracket → the new line is absent → byte-identical. This surfaces one line back onto the face, gently adjusting b129's lean, **for cost-led only.**

Personas: lawyer APPROVE (condensation of signed copy; qualifies the ceiling → raises defensibility; no new claim), linguist APPROVE (plain فصيح; «مرتكز/مُهلَك» jargon avoided).

## 5. Verification — empirical
- isolated `test_sprint_2_22_0b130.py` **21/21** · siblings b92 **22/22** · b100 **31/31** · b105 **21/21** · b129 **23/23** (2 R6 re-points: b92 gate-split; b129 dropped an accidental exact `'b129'` pin — the recurring Lesson-2).
- DoD: aggregator **ALL COUNTS MATCH (395)** · security **16/16** · surface-honesty **45/45** · broad walk **182/182 ALL FILES GREEN** (184s).
- py_compile OK · `node --check` ×3 OK.
- R14 real-Chromium (b129 live captures): COST-LED → new line present, jargon caption gone, «استدلالاً بالسعر لا معاينةً» + «ليس فئةَ بيتك» present, endpoints kept, **value ٢٬٤٠٠٬٠٠٠ / ٢٬٤٠٠٬٠٠٠ / ٥٬٤٠٠٬٠٠٠ byte-identical**; MARKET-LED → no bracket, new line ABSENT, **٢٫٤م/٢٫٢م/٢٫٦م byte-identical**; REFUSAL → no throw; **0 console errors**.

## 6. Deployment
`git push origin master` (backup, FIRST) → `git subtree push --prefix "deploy v2" heroku master` (from toplevel `C:/Thammen`).

## 7. Verification curl (post-deploy)
`curl -s -A "Mozilla/5.0" https://thammen.qa/api/health` → `3.1.0-sprint2.22.0b.130` · served `index.html` carries `_costFaceWhy` + «رقمُنا هو الأرضية» · 5-fixture value byte-gate byte-identical to v293.

## 8. What's NOT in this patch
The full report lean (assumptions-register fold + b128 link + >5M guard) is a separate slice. Market-led / income / land / refusal faces untouched. No engine/value/method/rule change.
