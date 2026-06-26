# CHANGELOG v153 — Sprint 2.22.0b.72 «وضوح القيم المتباعدة» (value-clarity: divergent cost vs market)

**Engine:** `thammen-sprint2p22p0b72-value-clarity-divergence` · **SPRINT_TAG** `2.22.0b.72` · **Date:** 2026-06-27
**Files:** `index.html` (cost-led note + e25 on-screen + DEF-12 bridge) · `evaluate_unified.py` (LEAD_COST_NOTE_AR + LEAD_E25_NOTE_AR de-jargon + 2 version lines) · `test_sprint_2_22_0b72.py` (new) · `test_sprint_2_22_0b20.py` (R6 re-point) · `CHANGELOG_v153.md` · `docs/Session_Log.md`
**Class:** 🟢 FRONTEND + small engine copy / **VALUE-INVARIANT** (every number + the chosen leader UNCHANGED; the 5-fixture byte-gate identical). First sprint of the overnight launch-readiness queue.

## 1. Why this matters (PO concern)
When an old property's COST (DRC) and MARKET median diverge — e.g. cost 9M / market 3M — the ordinary owner could be confused which is "their value." A read-only audit confirmed three real confusion points: the cost-led headline note used appraiser jargon («حوض المقارنات لم يجتز اختبار الموثوقيّة»); the e25_capped cost-divergence (cost > market) was hidden in the collapsed «كيف وصلنا» fold; and the report's three values had no plain-language bridge.

## 2. What this patch does (plain فصحى مبسّطة; lawyer + linguist personas APPROVE)
- **(1) De-jargon the cost-led basis note** (TIER-1): «اعتمدنا كلفةَ البناء (الأرض + المبنى بعد خصم الإهلاك) لأنّ الصفقات المماثلة القريبة كانت قليلة؛ وقد بِيعت بيوتٌ في منطقتك بنحو {market} ر.ق، وهو معروضٌ كحدٍّ أعلى للنطاق.»
- **(2) Surface the e25_capped cost-divergence ON-SCREEN** (TIER-1, was only in the fold): «كلفةُ إعادة بناء بيتك ({cost}) أعلى من سعر بيعه الحاليّ في السوق؛ والمباني تُباع بسعر السوق لا بكلفة بنائها.» Gated on `leader==='market' && rule==='e25_capped'`; reads the broadcast `value_stack.cost`.
- **(3) DEF-12 three-value bridge** (report): «ثلاثة أرقام: تقديرُنا لقيمة بيتك · كلفةُ إعادة بنائه · وتقديرٌ عند البيع السريع.»
- **(4) De-jargon the engine leadership notes** `LEAD_COST_NOTE_AR` + `LEAD_E25_NOTE_AR` (the «كيف وصلنا» fold + the report cluster) — plain owner language; the `.format` placeholders (`{n}/{d}/{cost}/{comp}`), the signed «لا رقم مركزيّ مُخترَع» line, and the E25 cost-is-a-floor-not-a-ceiling rail are all preserved.
- **NOT done (FLAGGED for the PO):** renaming the cost-led headline «التقييم السوقي»→«مرتكز التكلفة» — a b54 terminology-lock / brand decision; the number IS our market-value estimate derived via cost, so the safer default is to KEEP the label + clarify the method.

## 3. Verification
- isolated `test_sprint_2_22_0b72.py` **19/19** (de-jargon + e25 on-screen + DEF-12 bridge + engine notes' placeholders + the signed line + the locked hero label preserved).
- DoD: aggregator **395 MATCH** · security **16/16** · surface **45/45** · broad walk **128/128** (127→128; `test_sprint_2_22_0b20.py` **69/69** — 2 R6/Lesson-2 re-points: the terminology pins on the de-jargoned notes → the methodology assertions [n+dispersion+no-invented-central; cost-is-a-floor] preserved in the plain wording).
- **R14 real-Chromium 390×844** (live cost-led 54/541/6 + e25 55/296/13 payloads): the de-jargoned cost-led note renders; the e25 on-screen divergence renders with the live cost **٣٬٧٤١٬٥٧٠ > market ٢٬٦٠٠٬٠٠٠** (the PO's exact case); the DEF-12 bridge + three rows render; **0 console errors**; no overflow (390==390). Value byte-identical on the headline.

## 4. Deployment
```
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b72.py" "deploy v2/test_sprint_2_22_0b20.py" "deploy v2/CHANGELOG_v153.md" "deploy v2/docs/Session_Log.md"
git commit -m "Sprint 2.22.0b.72: value-clarity for divergent cost/market (de-jargon + e25 on-screen + DEF-12 bridge); value-invariant"
git subtree push --prefix "deploy v2" heroku master   # from C:/Thammen toplevel
git push origin master
```

## 5. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health   # → engine thammen-sprint2p22p0b72-value-clarity-divergence
# 5-fixture value byte-gate identical; 55/296/13 leadership.note_ar de-jargoned (no «سقفاً مضاداً»).
```

## 6. What's NOT in this patch
- The cost-led headline rename (PO brand decision). No methodology/value change. The EN twins of the de-jargoned notes are handled in the EN-localization sprints (b77+).
