# CHANGELOG v154 — Sprint 2.22.0b.73 «تباين النصّ + توضيح العمر» (a11y contrast + age-clarity)

**Engine:** `thammen-sprint2p22p0b73-a11y-contrast-age-clarity` · **SPRINT_TAG** `2.22.0b.73` · **Date:** 2026-06-27
**Files:** `index.html` (5 contrast swaps + 1 age-clarity) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b73.py` (new) · `CHANGELOG_v154.md` · `docs/Session_Log.md`
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (CSS color tokens + one copy clarification; engine = the 2 version lines; the 5-fixture byte-gate identical to v243). Second sprint of the overnight launch-readiness queue.

## 1. Why this matters
The brand-tint brown helper/title text (`#8b6e44` ≈ 4.4:1, `#a87000`) sat just under WCAG AA on small text — a launch-readiness a11y gap. And the short-report property strip showed «عمر البناء: فوق N سنة (سجل رسمي)» — the parenthetical attributed the source but didn't tell the owner the registered age is a documented **floor** (the actual building may be older — the E24 survey-vintage cliff).

## 2. What this patch does (frontend-only; lawyer + linguist personas APPROVE)
- **(1–5) Contrast → AA tokens:** the five sub-AA brown helper/title sites move to existing AA tokens — helper text `#8b6e44`→`var(--muted)` (#6B7280 ≈ 4.5:1: the footprint hint, the rental note, the cap-fired note) and titles `#8b6e44`/`#a87000`→`var(--primary)` (#16324F: the footprint-card title, the «التقييم يفترض بناءً نموذجياً» title). **DECORATIVE `#8b6e44` PRESERVED** (the bronze gradient + the bold 1.05rem land-value figure — large/bold ≥ the 3:1 large-text bar).
- **(6) Age-clarity:** the short-report age attribution «(سجل رسمي)» → «(سجل رسميّ — قد يكون أقدم)» — plain فصحى مبسّطة making the FLOOR explicit (the registered age is a documented minimum; the property may be older). No new line added (surgical inline edit, consistent with the b62/b63 declutter direction).

## 3. Verification
- isolated `test_sprint_2_22_0b73.py` **14/14** (the 5 sites moved to AA tokens · exactly the 2 decorative `#8b6e44` remain + the gradient preserved · 0 `#a87000` left · the age-clarity floor wording · b54 hero label + forced-sale honesty + b72 value-clarity copy untouched · engine bumped to b73).
- DoD: aggregator **395 MATCH** · security **16/16** · surface **45/45** · broad walk **129/129 ALL GREEN** (128→129; **zero re-points** — no sibling test pinned a color token or the age string).
- **R14 real-Chromium 390×844** (live cost-led 54/541/6 payload): the footprint title computes `rgb(22,50,79)` = `--primary`; the `#fpHint` helper computes `rgb(107,114,128)` = `--muted`; the short-report renders «(سجل رسميّ — قد يكون أقدم)» (old «(سجل رسمي)» gone); **0 console errors**; no overflow (`scrollW==clientW==390`); 0 `#a87000` in the rendered DOM.

## 4. Deployment
```
git subtree push --prefix "deploy v2" heroku master   # from C:/Thammen toplevel
git push origin master
```

## 5. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health   # → engine thammen-sprint2p22p0b73-a11y-contrast-age-clarity
# 5-fixture value byte-gate identical (frontend-only).
```

## 6. What's NOT in this patch (flagged for follow-up)
- The tiny decorative `#888`/`#999` GRAY sub-notes in the value-floor decomposition (`n=`, `per-m²`, confidence) sit ~3:1–3.5:1 on small text — a separate, lower-severity GRAY-contrast sweep (out of b73's brown-text scope; flagged for a supervised follow-up, not a launch blocker). The keyboard-nav a11y (b82) + focus-trap (b80) are later queue items.
