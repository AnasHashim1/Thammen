# CHANGELOG v103 — Sprint 2.22.0b.19: the THREE-VALUE report display + the D-3 GT-sheet kit

**Engine:** `thammen-sprint2p22p0b19-three-value-report` · **SPRINT_TAG** `2.22.0b.19`
**Date:** 2026-06-11 · **Files:** `index.html` (+15/−1) · `evaluate_unified.py` (the 2 version-string
lines ONLY) · `validate_gt_sheet.py` (new tool) · `test_sprint_2_22_0b19.py` (new) · this CHANGELOG.
**Status:** 🟢 DISPLAY-ONLY on the b20 contract — Gate-2 signed («نذكر هذا وذاك في التقرير», the
SESSION_CLOSE §2.2 independent track); deploy-on-green per the standing display-slice authorization.
**Naming note:** b19 ships AFTER b20 by design — the slot was reserved for this signed slice
(precedent: 2.18.0 after 2.21.0.9); `/api/health` numerically reads b19 < b20, the docs carry the order.

## 1. Why this matters

The report's DEF-12 block (b17) showed two values (MV + forced-sale ×0.90) while the b20 engine now
emits the full three-value stack. The signed slice: the report presents **السوقية / قيمة التكلفة /
الجبري ×0.90** together — the cost line under its b19-verbatim label + the V001 calibration sub-line,
and the forced-sale carries an explicit basis-disclosure line.

## 2. Root cause

`showReport`'s DEF-12 block predated the b20 `valuation.value_stack` emission; the cost figure appeared
only as a footnote `.rn` line, not as a value row in the values block.

## 3. What this patch does

**`index.html` (showReport, the rep-def12 block) — display-only, value_stack = the SOLE source:**
- A cost ROW between MV and forced-sale: label + value verbatim from `value_stack.cost.label_ar/value`
  («قيمة التكلفة (أرض + بناء مُهلَك) — نهج DRC») + the `sub_ar` calibration line («استرشادي، مُعايَر على
  تقييم معتمد واحد (V001)»). No hardcoded label, no arithmetic on the cost.
- The three branches: value → `unavailable_reason_ar` line → raw_land's unified `cost_note_ar`
  («DRC ≡ قيمة الأرض»). Refusal/hybrid never reach the block (hasValuation-gated, unchanged).
- The forced-sale basis-disclosure appended to the b17 convention line:
  «الأساس: القيمة السوقية المركزية (الوسيط) × 0.90».
**`evaluate_unified.py`:** ENGINE_VERSION/SPRINT_TAG only (the b20 contract needed NO additive field).

**`validate_gt_sheet.py` (the D-3 kit, delivered with the sprint):** CLI takes (zone/street/building +
the documented sheet MV + the sheet's raw age + finish [+ --sheet-land/--floors/--bua/--ref/--dry-run]) →
pulls the live `value_stack.cost` basis (land floor + BUA, browser-UA curl #61) → recomputes the DRC on
the SHEET basis via the PRODUCTION curve (`_cost_retention` + `COST_RCN_BY_FINISH`, raw age penalty-0 =
the E26/V001 basis) → prints the deviation → appends a row to `docs/validation/VALIDATION_LOG.md`
(the tracked path — the directive's `docs/VALIDATION_LOG.md` does not exist; #39 flagged). The intake
document-rule is stated in the tool + the log section header. **Self-check on the V001 standing gate:
+0.35% WITHIN ±1%** (live land 2,456,736 + BUA 602 from the v188 value_stack — the contract feeds the tool).

## 4. Verification — empirical evidence

- Isolated `test_sprint_2_22_0b19.py` **25/25** (rows + order + sole-source + the three branches +
  display-purity [no new math; exactly the one existing ×0.90] + the basis line + a8 calc-block guard +
  engine-untouched pins + the D-3 kit pins).
- **R14 real-Chromium 390×844 (fresh v188 captures as payloads):** Marikh cost-led → 3 rows
  (٢٬٤٠٠٬٠٠٠ / ٢٬٣٧٨٬٠٩٤ / ٢٬١٦٠٬٠٠٠ — the forced-sale = central×0.90 ON a range-as-headline case ✓) +
  V001 sub + basis line · المعراض E25 → cost ٣٬٧٤١٬٥٧٠ rendered honestly above MV · land → 2 rows +
  «لا مكوّن بناء لقطعة فضاء» · synthetic cost-unavailable → the reason line · refusal → **0** def12
  blocks · **0 console errors · no overflow (390==390)**.
- DoD: aggregator **392 ALL COUNTS MATCH** · security **15/15** · broad walk (see the run record in
  Session_Log §20.54).
- **The display-only gate:** `git diff --stat` = `index.html` +15/−1 and `evaluate_unified.py` 2+2
  version lines — values structurally cannot move; the `.b20_live_fixtures.json` byte-gate re-verified
  on the post-deploy 4-case smoke.

## 5. Deployment

`git subtree push --prefix "deploy v2" heroku master` on green (the standing display-slice
authorization) → post-deploy: `/api/health` = b19 + the 4-case live smoke (امريخ / V001 / المعراض /
أرض) vs the fixtures byte-identical + the served HTML carries the three-value block.

## 6. Verification curl (post-deploy)

`curl -s https://thammen.qa/ -A "Mozilla/5.0…" | grep -c "الأساس: القيمة السوقية المركزية"` → 1.

## 7. What's NOT in this patch

Any value/leadership logic (b20 owns it) · screen-4 changes (report-only) · compounds/towers (no stack)
· the forced-sale convention itself (b17's, unchanged — only the basis line added) · GT-log backfill
(the tool appends going forward; V001's historical entry stands).
