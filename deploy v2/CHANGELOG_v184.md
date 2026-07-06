# CHANGELOG v184 — Sprint 2.22.0b.103 «شاشة نتيجة التقييم: البطاقة المختصرة» (R1 — the card landing)

**Engine:** `thammen-sprint2p22p0b103-short-report-card-landing` · **SPRINT_TAG** `2.22.0b.103`
**Date:** 2026-07-06 · **Files:** `index.html` (showShortReport landing + CSS + printShortReport), `evaluate_unified.py` (version) (+ `test_sprint_2_22_0b103.py`; R6 re-points in `test_sprint_2_22_0b29.py` / `test_sprint_2_22_0b80.py` / `test_sprint_2_22_0b90.py`)
**Class:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT (presentation/layering of the broadcast figures; amount/low/high/method/rule untouched — the 5-fixture villa byte-gate holds by construction).

---

## 2. Why (the PO's loudest pain)

«بعد التثمين تظهر صفحة طويييييلة من 10 صفحات — غير محبَّذ». **Root cause (verified in code):** the post-valuation
landing rendered the b90 5-second face + ONE collapsed «عرض التفاصيل» fold ✓ — **but then a 4-button row + the
ENTIRE page-2 «ملحق المختصّين» UNFOLDED by default** (§٦ scenarios + §٧ investor + §٨ evidence + §٩ full legal +
QR line). The default scroll = face + open specialist appendix ≈ many screens. This is an ARCHITECTURE
(layering) problem, not a deletion one — a brand-director output for the owner, a RICS-complete artifact for
the specialist, on different layers.

Governed by a 5-seat persona re-study (brand director + RICS valuer roles; أم خالد + bank officer + skeptic
archetypes) that Gemini r10 concurred with.

## 3. What this patch does (`index.html`)

- **Page-2 «ملحق المختصّين» now FOLDS by default** — a new collapsed `<details class="thmr-fold" id="srFold2">`
  wraps §٦–٩ + the QR/fingerprint line (the exact b90/srFold pattern). Its `<summary>` carries the plain title
  «ملحق المختصّين» + a content-hint line («للبنك والمثمّن والمحامي — السيناريوهات والأدلة والإطار القانوني»).
  **Nothing deleted** — every section is one tap away.
- **The 4-button row → 2 buttons + compact links:** PRIMARY «حفظ / مشاركة PDF» (PO-picked — the owner's instinct
  after seeing the number) + SECONDARY «حسّن التقييم» (feeds accuracy + the S7 flywheel); «التقرير الكامل» +
  «التفاصيل الكاملة» demoted to a `.thmr-links` text-link row. The old scroll-to-appendix button removed (the
  srFold2 summary is the opener).
- **The always-visible compliance line stays OUTSIDE all folds** (the istirshadi pill «تقدير استرشادي — وليس
  تقييماً معتمداً» + the compressed legal line on page-1) — the b52 precedent (the clause may fold; the line stays).
- **Print parity:** `printShortReport` now force-opens ALL `#srOut details` (srFold + srFold2 + fin-toggle) and
  restores each — the full two-page report still prints.
- **CSS:** `.thmr-links` + `.fnote` (the summary hint) + **`.thmr-fold:not([open])>*:not(summary){display:none}`**
  — the measured Chromium `<details>` quirk (author CSS computes closed children as `block`; the b46 precedent).
  Scoped to `.thmr-fold` so no other `<details>` is affected. **This also cures the latent b90 srFold bug.**

## 4. VALUE-INVARIANT

Layering only. `v.amount*` math = the three DISCLOSED conventions (×0.90 / ×1.10 / ×1.30) unchanged; the
scenario table / income view / evidence / legal / QR content preserved verbatim inside the fold. `api.py` +
the engine untouched (2 version lines). The 5-fixture villa byte-gate is byte-identical by construction.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b103.py` **23/23** · `node --check` on the extracted inline JS OK · py_compile OK.
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **158/158 ALL
  GREEN** — **3 R6/Lesson-2 re-points** (b29 4-button-row pins → the b103 2-button+links architecture · b80
  «الملحق المتخصص ↓» pin → the srFold2 «ملحق المختصّين» summary · b90 srFold-only print pin → the all-folds loop;
  intent preserved, zero value/security/methodology assertion weakened).
- **R14 real preview 375×812** (DOM-measured, the authoritative channel): landing scrollHeight **1242px** (was a
  multi-screen scroll; fold-open jumps to 2847px → content shows) · srFold + srFold2 both closed by default ·
  scenario table hidden when closed / visible when open · buttons [حفظ/مشاركة PDF · حسّن التقييم] + links
  [التقرير الكامل · التفاصيل الكاملة] · the istirshadi pill visible outside all folds · **EN mode**: [Save / share
  PDF · Refine the valuation] + `dir=ltr` + EN fold summary · **0 console errors** · **no horizontal overflow**
  (scrollW 375==375).

## 6. Deployment

- `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112 lesson).

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.103`.
- served `index.html` carries `id="srFold2"` + `حفظ / مشاركة PDF` + `.thmr-fold:not([open])`.
- the 5-fixture villa byte-gate byte-identical to v275 (browser-UA #61): 54/541/6 2.4M · 56/647/6 3.8M ·
  55/296/13 2.6M · 56/565/21 2.4M · 52/903/90 refusal.

## 8. What's NOT in this patch

- The Layer-2 question-form fold titles + the keystone-comparables reuse + the §٨ owner-plain rewrite + the §٧
  investor reframe = **R2 (b104)** — the next sprint.
- The register/language lock (r11 flip-list) = **R3 (b105)**, deliberately after R1/R2 (sweep the FINAL copy).
- The RICS disclosure gaps (basis of value, data-date, time-adjustment) = **S1 (b106)**.
