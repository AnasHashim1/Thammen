# CHANGELOG v208 — Sprint 2.22.0b.131 «التقرير الكامل اللين» (S8, redesign v2 — the full-report lean)

**Engine:** `thammen-sprint2p22p0b131-full-report-lean` · **api-health:** `3.1.0-sprint2.22.0b.131`
**Files:** `index.html` (6 edits: 1 CSS + 5 JS in `showReport`/`printReportA4`) · `evaluate_unified.py` (the 2 version-string lines) · `test_sprint_2_22_0b131.py` (new) · `test_sprint_2_22_0b130.py` (R6/Lesson-2 re-point).
**Class:** 🟢 FRONTEND-ONLY / **VALUE-NEUTRAL** — `api.py` + the valuation engine UNTOUCHED (only the 2 version lines); the amount is PRESENTED, never recomputed → the 5-fixture value byte-gate is byte-identical to v294.
**Plan:** `temporal-honking-tiger.md` table (أ), the FULL-report lean (numbered at build per R-C = b131). The natural next sibling of b129 (the SHORT-report lean).

## 2. Why this matters

The redesign-v2 remainder had one report-family sibling left: the FULL report (`showReport`). §20.127 measured it live at ~13.7 mobile screens with **0 folds · 0 b128 link** — already ~85% leaned (b26/b51/b55/b91/b96/b106/b108), so the residual is SMALL/modest, not dramatic. The PO's «المفصّل يبقى مفصّلاً» is persona-affirmed (RICS/IVS MANDATE the disclosures — a lean specialist report would be LESS defensible), with two sharpening conditions: **print self-sufficiency** (folds print-open; the PDF must stand alone) + **de-dup ≠ de-detail** (the enemy is repetition, not detail).

## 3. What this patch does (4 measured lean items — plan line 99)

| item | change |
|---|---|
| **GUARD 3 — >5M → licensed valuer** | a conditional `if(v.amount>5000000)` `.thmr-legalz` note near the number (mirrors the b129 short-report guard, ANSWERS Q1). Shows on land 7.1M / villas > 5M; NOT the 2.4M/2.8M cases. |
| **§10 assumptions register FOLDS** | the flat, always-open `.rc` assumptions wall → a `<details class="thmr-fold rep-fold">`. «المفصّل يبقى مفصّلاً»: **every bullet VERBATIM** (condition · use · evidence-window · BUA · RCN · depreciation · age-basis · cost-calibration · cap-rate) — only the card becomes a fold. `.rep-fold` restyles `.thmr-fold` to match the surrounding `.rc` cards (surface + shadow + `.rt`-sized navy title). |
| **b128 de-dup POINTER** | a «الشروط والمنهجيّة الكاملة ›» link → `openTerms()` in the Methodology & standards annex → the b128 consolidated «الشروط والمنهجيّة» screen (methodology · assumptions · cost mechanism · evidence hierarchy · full terms). The detail above STAYS; the link only adds a jump (the b129 pattern). |
| **print self-sufficiency (F1)** | `printReportA4()` now force-opens every `#repOut details` before `window.print()` and restores after (the b125 result-screen pattern), so the folded register still prints — the PDF keeps the full detail. |

**GUARD 1 (basis of value, RICS VPS 2 / IVS 102) already present + KEPT** (2517–2520). §6 «دون تسويةٍ زمنيّة» (b106 R-3) · §9 evidence hierarchy (b106 C-4) · QR bottom-right (b96) were already shipped.

## 4. Value-neutrality / compliance

Presentation only — `amount`/`low`/`high`/`method`/`rule` untouched; `api.py` + engine logic untouched. All compliance PRESERVED: basis of value · `_mucCardHtml` MUC clause · «ليس تقييماً معتمداً» · forced-sale «×٠٫٩٠ — ليست تصفية معتمدة» · CC BY 4.0 (`.src-credit` clone) · IFRS 13 (via brief) · «لم تُعاين الحالة» (in the folded register — prints open) · the >5M guard (ADDED — strengthens). Every new string carries a `t('عربي','English')` EN twin (EN live, b88).

## 5. Verification — empirical

- py_compile `evaluate_unified.py` + `api.py` OK · `node --check` on all 3 inline `<script>` blocks OK.
- isolated `test_sprint_2_22_0b131.py` **43/43** (E14, reads the real files: the 4 lean items + every assumptions bullet retained + old flat wrapper gone + basis/MUC/forced-sale/CC-BY/QR kept + value-neutral no-assignment + short-report b129 guards untouched).
- **R6/Lesson-2 re-point:** `test_sprint_2_22_0b130.py`'s two exact-version pins → version-agnostic FORMAT checks (its 19 behaviour checks unchanged/green; **zero value/security/methodology assertion weakened**).
- DoD: aggregator **395/395 (MATCH)** · security **16/16** · surface honesty **45/45** · broad walk **183/183 ALL GREEN** (175.7s).
- **R14 real-Chromium 390×844** on the 4 fixtures + refusal + EN: cost-led 2.4M / geo 3.8M / land 7.1M / matched 2.4M — **0 console errors**, no overflow (390==390) on all; value byte-shown; the fold folds by default (body hidden when closed) + opens on click (bullets present) + prints open + restores; **the >5M guard fires on 7.1M land ONLY** (not 2.4M/3.8M); b128 link → `openTerms()`; basis/MUC/forced-sale/not-certified/CC-BY/QR all present; EN mode → fold summary + link + basis translated, dir=ltr, no overflow; refusal → no fold, no >5M, no throw, MUC kept. (The screenshot tool timed out — the §20.34 capture hiccup; DOM measurements are the channel.)

## 6. Deployment

`git push origin master` FIRST, then `git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master` (#43). HARD GATE 1 — explicit deploy consent required.

## 7. Verification curl (post-deploy)

`curl -s -A "Mozilla/5.0" https://thammen.qa/api/health` → `3.1.0-sprint2.22.0b.131`; the 5-fixture value byte-gate byte-identical to v294 (54/541/6=2.4M · 56/647/6=3.8M · 55/296/13=2.6M · 56/565/21=2.4M · 52/903/90=refusal); served `/` carries `<details class="thmr-fold rep-fold">` + `.rep-fold{background:` + `if(v.amount>5000000)` in showReport + `querySelectorAll('#repOut details')`.

## 8. What's NOT in this patch

- No `.legalfull` block for the full report — «المفصّل يبقى مفصّلاً» keeps its legal (MUC + DEF-12 + IFRS via brief) always-visible on screen; print self-sufficiency is satisfied by the fold printing open. The compressed-on-screen `.legalfull` pattern is the SHORT report's (b129).
- No engine/`api.py` change; no methodology/value change.
- The remaining redesign-v2 screens: نبض السوق (`/api/pulse`) · الموافقة (blocked — PDPPL, PO decision) · الإدخال+التحسين (drop «±8%») · الموبايل+الحديّة+`condition_led` · الوصوليّة (ARIA) · ملء الإنجليزيّة.
