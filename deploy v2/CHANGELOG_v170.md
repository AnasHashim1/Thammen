# CHANGELOG v170 — Sprint 2.22.0b.89 «توحيد الجمهور» (Option A: remove the «من أنت؟» role selector)

**Engine:** `thammen-sprint2p22p0b89-audience-unify` · **SPRINT_TAG** `2.22.0b.89` · api-health `3.1.0-sprint2.22.0b.89`
**Date:** 2026-07-01 · **Files:** `index.html` (selector removal + financing un-gate + CSS) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b89.py` (new) · re-points `test_sprint_2_22_0b24/b35/b63/b79/b83.py`
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (`api.py` + the valuation engine UNTOUCHED; the number is audience-invariant by construction). **Gate-2** (flow/presentation) — Option A SIGNED by the PO (2026-07-01) after a multi-AI consult (Gemini r6 + Claude concur).

## 1. Why this matters
The identification screen asked **«من أنت؟»** (owner/buyer/seller/investor/valuer, default owner) before showing the result. But **the number is identical for every role** (b24 doctrine — «الرقم واحد للجميع»); the selector only tailored *presentation*. After b88 neutralized the hero label («القيمة السوقية التقديرية»), the upfront role step became **pure friction** that implies to the user the number will change by role — and when it doesn't, it reads as a data-collection trick, hurting credibility (Gemini r6: the «Value-Invariant Paradox»). Removing it speeds the 5-second glance **and** reinforces the neutral-independent positioning.

## 2. Root cause / decision
Multi-AI consult (Rule #54): **Gemini r6 recommended Option A** (remove → one neutral entry), and **the PO confirmed A** + «financing = a collapsed toggle». The audience selector drove 4 presentation-only differences (buyer financing calc · investor/valuer evidence-density-open · valuer detailed-landing · role-tailored briefs). None requires an upfront gate: the useful bits become optional for all; specialists reach «كيف وصلنا» (folded, one click) + «التقرير الكامل».

## 3. What this patch does
- **Removed the 5-role «من أنت؟» selector** (`index.html` ~597-610) → one neutral entry. `audience` stays **'owner'** by default (the engine `_normalize_audience` maps owner→buyer → **value-invariant**). `selAud` + the `.aud-*` CSS are now inert (kept; no user path reaches them). The address/PIN input tab (`selTab`) is UNTOUCHED.
- **Financing calculator un-gated → an OPTIONAL collapsed toggle for EVERYONE** (was `audience==='buyer'`, b35/b63): a `<details class="fin-toggle">` «حاسبة التمويل الاسترشاديّة» (default folded) on BOTH the result screen (`show()`) and the short report (`showShortReport()`), for valued villa/house (excludes `raw_land`). Reuses `_srPayment` (DRY); the bc*/sr* ids + the b28 defaults (20% · 25y · 4.5%) + «استشر بنكك» kept verbatim.
- **Routing/density work automatically** with `audience='owner'`: the valuer no longer skips to the detailed screen (`audience!=='valuer'` guard intact → everyone lands on the short report + «التقرير الكامل» one click); the «كيف وصلنا» evidence accordion folds by default for all (b34 `_dense` → owner).
- **CSS:** `.fin-toggle summary` marker-hide (the un-gated toggle on both surfaces).

## 4. Value-invariance
`amount / low / high / method / rule` are UNTOUCHED (the engine is untouched except the 2 version lines; the frontend renders the broadcast `v.amount`). The financing payment is DERIVED from `v.amount` (display-only). The 5-fixture value byte-gate is byte-identical to v260 (b88).

## 5. Verification — empirical
- **b89 isolated `test_sprint_2_22_0b89.py`: 29/29** (E14 — reads the real index.html + evaluate_unified.py: selector removed · financing un-gated + fin-toggle on both surfaces · bc*/sr* ids + defaults + «استشر بنكك» preserved · value-invariance guard · version b89).
- **Re-points (R6/Lesson-2 — the buyer-gate/selector pins the removal invalidates; zero value/security/methodology assertion weakened):** b35 **17/17** · b63 **14/14** · b24 **58/58** (the [3] selector block → the removal reality) · b79 **19/19** (audience data-en spans gone) · b83 **39/39** (financing wired for all).
- **DoD:** aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · **broad walk 145/145 ALL GREEN** (183.5s).
- **R14 real-Chromium 390×844** (served index.html + live fixtures, AR + EN): JS parses (all functions defined) · **0 console** · **value byte-identical** (Marikh cost-led ٢٬٤٠٠٬٠٠٠ · land ١٬٢٠٠٬٠٠٠) · financing = a collapsed toggle «حاسبة التمويل الاسترشاديّة» on result + short report for villas, **ABSENT for raw_land** (correct) · القسط ١٠٬٦٧٢ (DRY) · the form has **no audience role buttons** (only the 2 input tabs) · no overflow (390/390) on result/short/form.

## 6. Deployment
`git push origin master` (backup) → `git subtree push --prefix "deploy v2" heroku master` (Rule #43; backgrounded).

## 7. Verification curl (post-deploy)
`curl -s --compressed -A "Mozilla/5.0 …" https://thammen.qa/api/health` → engine b89. Served `index.html`: `selAud(this,'owner')`=0 · `fin-toggle`≥2 · «حاسبة التمويل الاسترشاديّة» present · «من أنت؟» role-grid absent. 5-fixture value byte-gate byte-identical to v260.

## 8. What's NOT in this patch
- The **short-report «one-glance face»** redesign (م١/b90) — its own sprint (SIGNED §5.1 ready: hero price-per-ft² + ft²-range + LTR range-bar + confidence ladder + 5 chips + one fold). This b89 clears the flow so b90 builds simpler.
- The engine is untouched; `selAud` + `.aud-*` CSS are inert (a later tidy pass may remove them).
- Session_Log §20.115 + the CLAUDE.md production-snapshot refresh = a deferred docs pass (the giant run-on lines exceed the edit token limit — §20.93 precedent; authoritative state = `/api/health` + this CHANGELOG + the commit hash).
