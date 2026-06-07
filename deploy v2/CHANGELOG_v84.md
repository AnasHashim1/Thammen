# CHANGELOG v84 — Sprint 2.22.0b.3 (range-as-lead, §2b authority/finality dial-down)

**Engine:** `thammen-sprint2p22p0b3-range-as-lead` · **SPRINT_TAG** `2.22.0b.3` ·
**api/health** `3.1.0-sprint2.22.0b.3` · **Date:** 2026-06-07
**Files changed:** `index.html` (results headline swap) · `evaluate_unified.py` (version strings only) ·
`test_sprint_2_22_0b3.py` (new, 15 checks) · `docs/PHASE0_range_as_lead_recon.md` (recon, committed `3c7b124`) · `CHANGELOG_v84.md`
**Class:** FRONTEND-ONLY · **value-invariant** (engine diff = the 2 version-string lines) · Gate-2 (user-facing
presentation) signed by Anas («GO» after the §5 recon — same pattern as b2.2/§20.33) · **thin-flow step 2**
of the v4 owner-journey.

---

## 1. Why this matters

The results card led with the **point** (`القيمة التقديرية`, big `.rv hl`) and demoted the range to a
secondary two-box. On a stale-MoJ AVM with bidirectional condition-blindness (R7), a bold single number reads
as more authority/precision than the evidence supports. Step 2 of the v4 «thinnest-flow» dials that down: the
**market RANGE becomes the headline**, the median a muted central-estimate marker — the suspense-reveal arc's
authority/finality reduction (DESIGN_2p2x v4 §2b).

## 2. Root cause / motivation (PHASE0 recon — `docs/PHASE0_range_as_lead_recon.md`)

Read-only recon measured the live engine before this was drafted, and **re-shaped the snapshot's wording**:
- **F1 — the range is structurally ASYMMETRIC on thin paths.** Measured (live `/api/evaluate`): 56/565/21
  bracket = ±0.0% symmetric; 54/541/6 thin ASYM −7.4%; **55/296/13 thin: amount == high exactly** (upper gap
  0, all-downside `[2.0M…2.6M]`). The median is deliberately capped at the median on thin/widened. ⟹ a literal
  **"symmetric ± bar"** (the snapshot's phrasing) would, on 55/296/13, draw ±300K → invent a 2.9M upside the
  engine explicitly refuses — the "authority-overstate" failure this arc avoids. **Resolution: surface the
  engine's TRUE (asymmetric-allowed) low/high + a median marker in its true position — NOT a forced symmetric ±.**
- **F2 — `range_is_headline` (a10/a14) was set by the backend but NEVER consumed by `index.html`** (grep: 0
  matches). The honest-range intent never reached the screen. Step 2 closes that gap by leading with the range.
- **F3 — the approved prototype already ships:** `showConfirm` (b2.3/v169, R14-passed) already renders
  range-headline + muted median marker with the raw (lopsided) low/high. This sprint applies that pattern to
  the results valuation card.

## 3. What this patch does

**`index.html` — `show()` results headline (the `:1189↔:1190` swap):**
- When `v.low!=null && v.high!=null` (asymmetry-safe gate, matches showConfirm): the **range** becomes the big
  `.rv hl` 1.5rem headline — `«النطاق التقديري السوقي» → fmt(v.low) – fmt(v.high) ر.ق` — and the median drops
  to a **muted `.rn` marker**: `«الوسيط (التقدير المركزي) ≈ <strong>fmt(v.amount)</strong> ر.ق»`.
- Else (no range, e.g. some refusals): **point fallback** retained (`«القيمة التقديرية» fmt(v.amount)`).
- The old secondary two-box `.rg` («الحد الأدنى»/«الحد الأعلى») is **removed** (the range is now the headline;
  no duplication).
- Everything downstream UNTOUCHED: condition note (a17/a19), **value_floor / B-1 stays SECONDARY** (confirms
  the "NOT land-to-median" half of the decision), evidence panel (b2.2), brief, decomposition, trend.

**`evaluate_unified.py`:** ENGINE_VERSION / SPRINT_TAG → b3 (value-invariant; `/api/health` auto-derives).
**`api.py` UNTOUCHED.**

## 4. Verification — empirical evidence

- **py_compile** `evaluate_unified.py` OK.
- **Isolated** `test_sprint_2_22_0b3.py` **15/15** (reads the REAL index.html — E14: range headline label +
  true low–high + `.rv hl 1.5rem` + muted `.rn` median marker + asymmetry-safe gate + point fallback + old
  two-box removed + neighbours untouched [condition/value_floor/evidence/showConfirm] + version bump + R6
  format).
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **PASS (392)** · security **15/15** · surface-honesty
  **45/45** · broad `2p22p0_pre/run_regression_2p22p0a.py` **72/72** (71→72, +1 the new test).
- **R14 — real Chromium 390×844 (node absent; EXECUTED, not reasoned):**
  - all 9 frontend fns defined (whole-file JS parses); **0 console errors**.
  - 56/565/21 (bracket symmetric): headline `.rv hl` = «٢٬٢٠٠٬٠٠٠ – ٢٬٦٠٠٬٠٠٠ ر.ق» (range is the lead),
    marker «الوسيط (التقدير المركزي) ≈ ٢٬٤٠٠٬٠٠٠ ر.ق»; old two-box gone; evidence panel + value_floor present.
  - **55/296/13 (thin ALL-DOWNSIDE — the F1 stress case):** headline = «٢٬٠٠٠٬٠٠٠ – ٢٬٦٠٠٬٠٠٠ ر.ق», marker
    «الوسيط ≈ ٢٬٦٠٠٬٠٠٠» **at the high edge** — **no invented upside** (proves true-range, not symmetric ±).
  - 390×844: no horizontal overflow (docScrollW==clientW==390; resultsScreen no overflow; headline right-edge
    336 < 390). Screenshot confirms the range-as-lead card + muted median + secondary value_floor.

## 5. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add index.html evaluate_unified.py test_sprint_2_22_0b3.py CHANGELOG_v84.md docs/PHASE0_range_as_lead_recon.md
git commit -m "Sprint 2.22.0b.3: range-as-lead (§2b dial-down) [BUILT, DoD-green, R14-pass, HELD at Gate-1]"
git push origin master
git subtree push --prefix "deploy v2" heroku master    # Gate-1 — explicit Anas consent ONLY
```

## 6. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health    # expect 3.1.0-sprint2.22.0b.3
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
# expect: valuation.amount=2,400,000, low=2,200,000, high=2,600,000 (BYTE-IDENTICAL to b2.3 — value-invariant)
# served index.html carries «النطاق التقديري السوقي» + «الوسيط (التقدير المركزي)»; «الحد الأدنى» absent
```

## 7. What's NOT in this patch (scope boundary)

- **No engine / valuation logic change** — every headline + the B-1 value_floor byte-identical (4-anchor smoke).
- **No symmetric ±** — the surfaced range is the engine's true (asymmetric-allowed) low/high (F1).
- **No graphical bar** — text range + median marker only (a visual ± bar over the same data is a future additive).
- **value_floor stays secondary** — "NOT land-to-median" preserved.
- **raw_land NOT verified live this session** — carries a range too; confirm on a valid land PIN if a land-
  specific surface is wanted (recon §5).
- **multi-AI (#54) not run** — the framing was decided by the measured data (F1), not an evolving-standard /
  numbering question; Anas/Claude.ai may request a round before Gate-1 (flag-and-proceed, Soft Gate 3).
- **`api.py` untouched.**
