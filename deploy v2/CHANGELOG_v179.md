# CHANGELOG v179 — Sprint 2.22.0b.98 «سطر العقار + مضيف التحقّق» (land property-line dedup + verify host)

**Engine:** `thammen-sprint2p22p0b98-landline-verify-host` · **SPRINT_TAG** `2.22.0b.98` · api-health `3.1.0-sprint2.22.0b.98`
**Date:** 2026-07-02 · **Files:** `index.html` (2 edits) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b98.py` (new) · re-points `test_sprint_2_22_0b57.py`, `test_sprint_2_22_0b97.py`
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (display only; the valuation engine is UNTOUCHED). **Gate-2** (user-facing display). The small pass approved after b97.

## 1. Why this matters
Two cosmetic defects surfaced while testing the land report (PIN 55010236):
1. **Property-strip district duplication** (short report): `أرض فضاء · أرض في الوعب — PIN 55010236 · الوعب` — «الوعب» twice (the raw_land `address` is already «أرض في {district} — PIN …», and the strip unconditionally appended « · {district}»).
2. **Verify QR/link off-brand:** the printed QR + the «thammen.qa/verify» link resolved to the raw `thammen-app-123-…herokuapp.com` (the `_verifyUrl` built on the `API` const) — off-brand on a bank-grade report, and the href didn't match the displayed «thammen.qa» text.

## 2. What this patch does (`index.html`)
- **Strip dedup (line ~2210):** append « · {district}» **only when the address does not already contain it** — `((d.district&&(d.address||'').indexOf(d.district)===-1)?(' · '+esc(d.district)):'')`. Land → «أرض فضاء · أرض في الوعب — PIN 55010236» (district once). Villa address («56/565/21») does not contain the district → still appends. `esc()` preserved (b57 XSS-safety intact).
- **Verify host (`_verifyUrl`):** build on `https://thammen.qa/verify?…` instead of the herokuapp `API` base. The query form (ref/fp/basis) is unchanged and **proven live** (GET `thammen.qa/verify?ref=…&fp=…` → «تقرير أصليّ — مطابقة»). **`API` (the /api call base) is UNTOUCHED.**

## 3. Value-invariance
Display only — `amount/low/high/method/rule` untouched; `evaluate_unified.py` = the 2 version lines. The 5-fixture value byte-gate is byte-identical to v269 (b97) by construction.

## 4. Verification — empirical
- Isolated `test_sprint_2_22_0b98.py` **11/11** (dedup guard · old unconditional append gone · `_verifyUrl` on thammen.qa · API const untouched · link-text/host match · b97 land gates still intact).
- **2 R6/Lesson-2 re-points** (behavior preserved, zero assertion weakened): `test_sprint_2_22_0b57.py` (the property-strip esc pin → the deduped form; district still `esc()`-wrapped) = 29/29; `test_sprint_2_22_0b97.py` (my own **exact-version pins** → version-agnostic format — the standing Lesson-2 rule I had violated) = 29/29.
- **DoD:** aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · **broad walk 154/154 ALL GREEN**.
- **py_compile** OK. **R14 real-Chromium 390×844** (DOM-measured; screenshot timed out — §20.34): land short-report strip «الوعب» **×1** (was ×2) · verify href host = **thammen.qa** + starts `https://thammen.qa/verify?` · **Marikh skewed cost-led (hpct 0%) renders the b92 «الحاضنة المدرّجة»** (no naked edge dot) with the honest legend «الأرضية = مرتكز الكلفة · السقف = وسيط صفقات السوق» — **0 console errors**.

## 5. Deployment
`git push origin master` (backup FIRST) → `git subtree push --prefix "deploy v2" heroku master` (Rule #43; backgrounded).

## 6. Verification curl (post-deploy)
`/api/health` → engine b98. Served `index.html`: the dedup guard `indexOf(d.district)===-1` present · `'https://thammen.qa/verify?ref='` present · `API+'/verify'` absent. 5-fixture value byte-gate byte-identical to v269.

## 7. What's NOT in this patch
- The residual «أرض»×2 (asset label «أرض فضاء» + address «أرض في…») is left — the glaring exact-word «الوعب»×2 is the one fixed; «أرض» in two different words is minor.
- The server's `verification_url` short-code form (`/verify/{code}`) is NOT used — the b23 query form is the proven-working path (the short-code was a 2.22.0a placeholder that may 404).
- Gemini's r8 luxury/enhancement ideas (Live-Pulse freshness reframe · radial-gradient/glassmorphism hero · stratification cards · landmarks-as-face-chips) — a separate Gate-2 visual pass, PO decision (see the session adjudication).

## 8. Gemini r8 note (adjudication — no code impact this sprint)
Gemini's r8 critique of the live Abu Hamour report re-derives r7 (Gemini has no memory): #1 broken range bar = already fixed b92 (verified: the skewed Marikh case renders the tiered bracket; and the Abu Hamour report is a TIGHT matched case 2.2–2.6M where the "edge dot" cannot occur) · #2 empty chips = already fixed b94 · #3 luxury = partly shipped b93 (champagne hairline + cadastral watermark). Its «الأرضية المبنية على الصفقات» wording + «سيتم تفعيل ميزة … قريباً» promise were already REJECTED in r7 (dishonest / dated-promise). Genuinely-new = a few luxury polish ideas (deferred, §7).
