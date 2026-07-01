# CHANGELOG v173 — Sprint 2.22.0b.92 «حاضنة النطاق + الصدق + n<5» (range-display overhaul)

**Engine:** `thammen-sprint2p22p0b92-range-tiers-honest` · **SPRINT_TAG** `2.22.0b.92` · api-health `3.1.0-sprint2.22.0b.92`
**Date:** 2026-07-02 · **Files:** `index.html` (`showShortReport` hero + `.thmr-tiers` CSS) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b92.py` (new)
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (`api.py` + the valuation engine UNTOUCHED; presentation of the broadcast figures — amount/low/high/method/rule never recomputed). **Gate-2** signed: PO «go» 2026-07-02 on the Gemini-r7-adjudicated package (`docs/CONSULT_gemini_r7_report_critique.md`).

## 1. Why this matters
The b90 face range-bar put the median dot at the **track edge** in both live villa leaders (cost-led → amount==low → far-left; geo-led → amount==high → far-right). A naked dot at the edge of a slider reads as a **broken control / outlier**, not confidence (Gemini r7: «جريمة UX»). And the SIGNED §3 n<5 behavior (hide the central figure, range-only) had never been built (b90 always showed the central).

## 2. What this patch does (`showShortReport` hero)
- **Tiered bracket (Gemini r7 #1):** when the median position is skewed (`_hpct<20 || >80`) the line+dot is replaced by the **«الحاضنة السعرية المدرّجة»** — a LABELED gold value chip («القيمة التقديرية») with a stem over a 3-block track, endpoint labels **«الأرضية السعرية»** (+low) / **«السقف السوقي»** (+high). Chip position clamped 18–82% (never clipped). The **central-dot facebar is KEPT verbatim** for the non-skewed case (the b90 pin survives — zero re-points).
- **Honest anchors legend (#54 adjudication):** for cost/geo_full leaders only — «الأرضية = مرتكز الكلفة (أرض + بناء مُهلَك) · السقف = وسيط صفقات السوق» (TRUE on both paths: cost-led low==DRC anchor, geo low==cost floor; high==market median). **REJECTED as dishonest:** Gemini's floor label «(بناءً على الصفقات)» (our floor is cost, not transactions) and the fabricated wide-range reason «الفروقات الهندسية للواجهات وعرض الشوارع» (our width is measured dispersion + cost-vs-market divergence).
- **SIGNED §3 n<5 range-only face:** `_confN<5` + a valid range → the hero label becomes **«القيمة المتوقّعة بين»** + low و high (the central figure is hidden from the face; everything in the fold/§٢ unchanged — تدرّج لا حذف); no value chip on the tiers (the range IS the message); the b90 scarcity guidance retained.
- EN twins authored inline (`t()`), legend `dir="auto"`.

## 3. Value-invariance
`amount/low/high/method/rule` untouched; the only `v.amount` multiplications remain the 3 disclosed conventions (×0.90 / ×1.10 / ×1.30) — pinned by the isolated test. The 5-fixture value byte-gate is byte-identical by construction (display-only).

## 4. Verification — empirical
- Isolated `test_sprint_2_22_0b92.py` **22/22** (tiers markup + skew gate + honest legend + BOTH rejected Gemini wordings absent from rendered strings + scarce branch renders low/high NOT amount + facebar verbatim + value-math pin + version format).
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · **broad walk 148/148 ALL GREEN** (147→148, **zero re-points**).
- **R14 real-Chromium 375×812** (preview, live fixtures; the screenshot tool timed out — §20.34 — DOM measurements are the channel): cost-led (f_marikh ٢٬٤٠٠٬٠٠٠) → tiers + chip clamped 18% **inside** the track + honest legend rendered; geo-led (f_v001 ٣٬٨٠٠٬٠٠٠) → tiers at 82% + legend; synthetic n=3 → «القيمة المتوقّعة بين ٣٬١٠٠٬٠٠٠ و ٣٬٨٠٠٬٠٠٠» + scarcity note + no chip; synthetic central case → the b90 facebar (not tiers); **EN** "Price floor / Market ceiling / Estimated value / Floor = the cost anchor…" with no AR leak; **no doc overflow (375==375)**; **0 console errors/warnings**; `node --check` both inline blocks OK.

## 5. Deployment
`git push origin master` (backup FIRST — the §20.112 lesson) → `git subtree push --prefix "deploy v2" heroku master` (Rule #43; backgrounded).

## 6. Verification curl (post-deploy)
`/api/health` → engine b92. Served `index.html`: `thmr-tiers` + «الأرضية السعرية» + «السقف السوقي» present; «بناءً على الصفقات» absent from rendered strings. 5-fixture value byte-gate byte-identical to v263 (b91).

## 7. What's NOT in this patch
- The **result-screen `.rhero` range-bar** (b48) still uses the line+dot — same edge-pinning exists there; carried forward (candidate to fold into b93's hero pass or its own micro-slice).
- The luxury polish (b93: cadastral watermark + champagne hairline) and the unknown-chips cleanup (b94) — next sprints of the signed package.
- Confidence-ladder numeric thresholds unchanged (E4 20/10/5 — the SIGNED wording only).
