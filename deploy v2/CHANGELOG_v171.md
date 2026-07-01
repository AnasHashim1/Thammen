# CHANGELOG v171 — Sprint 2.22.0b.90 «وجه المختصر» (short-report 5-second face)

**Engine:** `thammen-sprint2p22p0b90-short-report-face` · **SPRINT_TAG** `2.22.0b.90` · api-health `3.1.0-sprint2.22.0b.90`
**Date:** 2026-07-01 · **Files:** `index.html` (`showShortReport` page-1 restructure + `printShortReport` + CSS) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b90.py` (new) · re-points `test_sprint_2_22_0b25/b54/b73/b80/b89.py`
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (`api.py` + the valuation engine UNTOUCHED; the face PRESENTS the broadcast figures — amount/low/high/method/rule never recomputed). **Gate-2** (presentation) — the SIGNED report-redesign (`docs/SIGNED_report_redesign_v1.md` §5.1) after the Gemini r5 + r6 consults; the hero label was PO-decided (unified neutral, 2026-07-01).

## 1. Why this matters
A trusted customer found the report buried the number under compliance layers («الناس لا يقرؤون»). The short report (the owner's default landing, b29) opened with a property strip + a navy hero, then a wall of §١-٩ — the answer was not glanceable. b90 restructures **page-1** into the Progressive-Disclosure **«5-second face»**: the number, its confidence, and the property in one screen; everything else folds under a single «عرض التفاصيل». (Page-2 «ملحق المختصّين» is unchanged — it was already a separate, folded surface.)

## 2. What this patch does (`showShortReport`, page-1)
- **Identity strip decluttered** → asset + address + district only (plot/age → chips, date → hero).
- **Hero (navy band):** neutral label **«القيمة السوقية التقديرية»** (unified for all audiences — the b89 audience-unification + the PO decision) + the number + **price-per-ft²** (`round((amount/plot_area)/10.7639)`) + the «تقدير استرشادي» pill + a **LTR range-bar** (Gemini r5 #13: the median dot at `_hpct=(amount−low)/(high−low)`, low-left → high-right, only the two endpoints labelled) + the **per-ft² range** (#5: `~{low_ft} — ~{high_ft}`) + **«تاريخ التقييم: {today}»** (#REJECTED «تحديث آلي» — the data is months-stale, so «تاريخ التقييم» is the honest label). The old cost-vs-market bar is dropped (§١ + §٢ already carry that story).
- **Confidence pill (E4 ladder 20/10/5):** «ثقة عالية / متوسطة / محدودة»; **n<5 → «بيانات محدودة جداً»** + the scarcity guidance «لقلّة الصفقات المسجّلة في هذه الشريحة، اعتمد على النطاق السعريّ أدناه كدليل استرشاديّ» (Gemini r5 #8 — scarcity, not «تذبذب»).
- **5 property chips:** villa → مساحة البناء (BUA, ✎) · عمر البناء (✎, floor-note tooltip «قد يكون أقدم» — b73 honesty preserved) · التشطيب (✎) · الملاحق (✎) · مساحة الأرض; land → المساحة · الشوارع/«أرض زاوية» (`corner_analysis`) · الحي (+Zone) · التصنيف (R1/2/3, best-effort from `location_features`) · الارتفاع (best-effort). ✎ chips deep-link to `go('refine')` (Claim-Your-Home; static in b90, the interactive re-eval binding is م٢).
- **Compressed legal line** (ic-alert): counsel-safe («مؤشّر سعريّ استرشاديّ … ليس تقييماً عقارياً معتمداً ولا حجّة رسمية»). The FULL §٩ legal block (IFRS 13, القانون 28/2023 framing) is untouched on page-2.
- **ONE «عرض التفاصيل» fold** (`<details id="srFold">`, closed by default) wraps the financing calculator + §١-٥ + the page-1 footer — **each string verbatim** (b31/b52 buffer-swap discipline); the `basisLn` leader-story line is relocated into the fold's intro. `printShortReport()` force-opens the fold (print parity, b52).

## 3. Value-invariance
`amount/low/high/method/rule` are UNTOUCHED. price/ft² + `_hpct` + the per-ft² range are DISPLAY derivations (division/subtraction of the broadcast figures); the only *multiplications* of `v.amount` remain the three DISCLOSED conventions (×0.90 forced-sale · ×1.10 / ×1.30 hard ceilings). The 5-fixture value byte-gate is byte-identical to v260 (b88/b89).

## 4. Verification — empirical
- **b90 isolated `test_sprint_2_22_0b90.py`: 29/29** (E14 — reads the real index.html: hero label/price-ft²/range-bar/ft²-range/date · E4 confidence + n<5 scarcity · villa+land chips + ✎→refine · compressed legal + §٩ intact · the fold wraps financing+§١-٥+footer + printShortReport force-open · value-math = the 3 conventions · de-emoji ic-* · EN t()).
- **Re-points (R6/Lesson-2 — intent preserved, zero value/security/methodology assertion weakened):** b25 **(hero label «القيمة السوقية التقديرية»)** · b54 (short-report value term stays «تقديريّ») · b73 (age-floor «قد يكون أقدم» preserved on the age-chip tooltip) · b80 (AR literal → the neutral label) · b89 (exact-version pins → version-agnostic).
- **DoD:** aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · **broad walk 146/146 ALL GREEN**.
- **R14 real-Chromium 390×844** (served index.html + live fixtures, AR + EN): **0 console errors**; **value byte-identical** — cost-led villa (f_marikh) ٢٬٤٠٠٬٠٠٠, land (f_land) ١٬٢٠٠٬٠٠٠; price/ft² ٣٦٤, range-bar dot at the floor, ft²-range ~٣٦٤—~٨١٨, confidence «متوسطة (n=15)»; 5 villa chips / 3 graceful land chips (zoning+height auto-skipped when absent); financing folded + DRY (القسط ١٠٬٦٧٢) for the villa, **absent for raw_land**; fold **closed by default**; age-chip floor tooltip carries «قد يكون أقدم»; **EN** renders "Estimated market value / 2,400,000 QAR / 364 QAR·ft² / Moderate confidence… / Show the details" with **no AR-chrome leak**; **no overflow (390==390)** on both.

## 5. Deployment
`git push origin master` (backup) → `git subtree push --prefix "deploy v2" heroku master` (Rule #43; backgrounded).

## 6. Verification curl (post-deploy)
`curl -s --compressed -A "Mozilla/5.0 …" https://thammen.qa/api/health` → engine b90. Served `index.html`: `thmr-facebar`·`thmr-conf`·`thmr-chips`·`thmr-legalz`·`id="srFold"` present; «القيمة السوقية التقديرية» present, «قيمة بيتك التقديرية اليوم» absent. 5-fixture value byte-gate byte-identical to v260.

## 7. What's NOT in this patch
- The **result screen `show()`** face (b91-candidate) — b90 is scoped to the short report (`showShortReport`), the customer's complained-about surface (#38).
- The **full report `showReport`** proof-first reorder + table-unit «م²» + adjustment dir=ltr islands (م٣, its own next sprint per the plan).
- **Interactive** chip re-eval + frontage/subdivision (م٢); the n<5 central-hide (b91-deferred; b90 always shows the central = value-invariant).
- Session_Log §20.115 + the CLAUDE.md production-snapshot refresh = a deferred docs pass (the giant run-on lines exceed the edit token limit — §20.93 precedent).
