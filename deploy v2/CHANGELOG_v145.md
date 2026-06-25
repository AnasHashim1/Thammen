# CHANGELOG v145 — Sprint 2.22.0b.64 «إصلاحات تشخيص الواجهة» (debug-session frontend fixes)

**Engine:** `thammen-sprint2p22p0b64-debug-frontend-fixes` · **SPRINT_TAG** `2.22.0b.64` · **Date:** 2026-06-25
**Files:** `index.html` (2 surgical edits) · `evaluate_unified.py` (the 2 version lines) · `test_sprint_2_22_0b35.py` (1 R6 re-point)
**Class:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT (amount/low/high/method/leadership/the locked «التقييم السوقي» label untouched).

## 1. Why this matters
From a full-site DEBUG session (PO request). Two user-facing display defects, adversarially verified against the code:
- **#4 (cost_led hero clarity):** on a cost-led result the hero shows the COST anchor as the central figure under the label «التقييم السوقي», while the true market median is shown only as the muted range-HIGH and the explanation («قيادة كلفة استرشادية…») is FOLDED by default for owner/buyer/seller (b34). The owner reads the cost figure as if it were the market value.
- **#7 (raw_land financing):** the buyer financing calculator (b35) rendered even on raw land — an illustrative monthly-mortgage calculator on a bare plot.

## 2. Root cause
- #4: the hero label is the locked product identity (b54); the leadership explanation lives only in the «كيف وصلنا» fold (`how` buffer, index.html ~2401), folded for non-investor/valuer.
- #7: the b35 gate `if(d.audience==='buyer'&&v.amount)` (index.html ~2387) had no asset-type exclusion.

## 3. What this patch does
- **#4** (index.html ~2372): ADDITIVE always-visible one-line basis note on the result hero when `leadership.leader==='cost'`: «هذا الرقم مبنيّ على الكلفة (أرض + بناء مُهلَك) لأنّ حوض المقارنات لم يجتز اختبار الموثوقيّة؛ وسيط السوق (X ر.ق) معروض مكتوماً كحدٍّ أعلى للنطاق — التفصيل في «كيف وصلنا».» PURE ADDITIVE — the locked «التقييم السوقي» label is UNCHANGED; the full leadership note stays in the fold. `cost_led` ONLY (NOT e25_capped, where the market leads).
- **#7** (index.html ~2387): added `&& d.asset_type!=='raw_land'` to the buyer-financing gate → the calculator no longer renders on raw land.

## 4. Scope boundary
Presentation only. No engine logic, value, range, method, leadership, MUC, disclaimer, or compliance copy changed. The `_srPayment`/`bcRecalc` math + the b35/b63 buyer-gate elsewhere are untouched.

## 5. Verification — empirical evidence
- **R14 (real Chromium, served index.html + the two production payloads):** JS parses (show/fmt/showShortReport/showReport/go all `function`). **VILLA cost_led (51/953/12, buyer):** value ٢٬٨٠٠٬٠٠٠ unchanged · hero label «التقييم السوقي» intact · #4 note renders ONCE with the muted market median ٤٬٣٠٠٬٠٠٠ correctly interpolated · financing calc present (القسط ١٢٬٤٥١). **LAND raw_land (55010236, buyer):** value ٧٬١٠٠٬٠٠٠ unchanged · #4 absent (no leadership) · financing calc absent (no `#bcDown` element). **0 console errors.**
- **Isolated:** `test_sprint_2_22_0b35.py` **17/17** (1 R6/Lesson-2 re-point: the gate regex now asserts the `&&d.asset_type!=='raw_land'` guard; intent preserved) · b63 14/14 · b20 69/0 · b52 17/17 · b31 36/36.
- **DoD:** aggregator ALL COUNTS MATCH · security 15/15 · surface 45/45 · broad walk **122/122 ALL GREEN**.

## 6. Deployment
```
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b35.py" "deploy v2/CHANGELOG_v145.md"
git commit -m "Sprint 2.22.0b.64: debug-session frontend fixes (cost_led hero clarity + raw_land financing guard) — value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl
```
curl -s https://thammen.qa/api/health   # → engine_version thammen-sprint2p22p0b64-debug-frontend-fixes
```
Served `index.html` carries «هذا الرقم مبنيّ على الكلفة» + the `&&d.asset_type!=='raw_land'` guard; the 5-fixture value byte-gate identical to v235.

## 8. What's NOT in this patch (DEFERRED — Gate-2, await PO signature + regression)
- **#2** BUA unify: the leading cost uses bua 474 while `cost_approach` shows 740 → two contradictory cost figures (2.81M / 4.06M) in one report. Engine output.
- **#3** age consistency: E26 (system-age-leads) applied to the leading cost only; `cost_approach`/`building_substantiality` still show the user age → three ages (2/≥3/8) in one report. Engine output.
- **#5** trend dispersion-aware label: «استقرار» on volatile data (±45% yearly swing, flat slope). Engine output ([moj_reference.py:298](moj_reference.py:298)); re-points `test_moj.py:139`.
- **#1** determinism: the muted market HIGH varied (4.3M / 4.2M) across two runs → non-reproducible `report_fp`. Needs the 2-identical-run measurement + likely a stable sort on comparable selection.
