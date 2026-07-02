# CHANGELOG v180 — Sprint 2.22.0b.99 «Live Pulse + المعالم-كشارات» (Gemini r8 luxury subset)

**Engine:** `thammen-sprint2p22p0b99-live-pulse-landmark-chips` · **SPRINT_TAG** `2.22.0b.99` · api-health `3.1.0-sprint2.22.0b.99`
**Date:** 2026-07-02 · **Files:** `data_freshness.py` (banner reframe) · `index.html` (pulse-dot CSS+render · land landmark chips) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b99.py` (new) · re-point `test_sprint_2_22_0b98.py`
**Class:** 🟢 FRONTEND + engine-copy / **VALUE-INVARIANT** (the valuation engine — amount/low/high/method/rule — is UNTOUCHED; a freshness-banner copy reframe + a CSS pulse + display of already-broadcast `location_features`). **Gate-2** (user-facing copy) — the recommended subset of Gemini r8, PO «نعم مع توصيتك» + lawyer/linguist personas.

## 1. Why this matters
Gemini's r8 luxury critique of the live report (most of it already shipped b92/b93/b94, or rejected in r7). The PO approved the **recommended subset** — the two genuinely-new, honest wins:
- **The top freshness banner read alarmist/primitive:** «تنبيه: بيانات وزارة العدل لم تُحدَّث منذ ديسمبر 2025 (183 يوماً) — استخدم النتائج كمرجع إرشادي فقط».
- **The land «5-second face» is sparse** (b94 correctly removed the empty «غير محدّد» building chips) — but the algorithm has captured rich location facts that were buried deeper.

## 2. What this patch does
- **(A) Live Pulse — banner reframe (`data_freshness._render_banner`, very_stale only):** → «مؤشّر مزامنة البيانات: آخر تحديث رسميّ من وزارة العدل — {month} (منذ {days} يوماً) · النتائج إرشاديّة حتى استئناف النشر». The alarmist «تنبيه» lead is gone; **every honest fact is preserved** — the source (وزارة العدل), the date ({month}), the staleness («منذ {days} يوماً»), and the «إرشاديّة» caveat. Only the very_stale tier changes; fresh/mild/stale banners + the `.dfc` per-result caveat (`_render_caveat`) are UNTOUCHED.
- **(A) Live Pulse — pulse dot (`index.html`):** `#dfBanner` now renders a small `.df-pulse` dot (a live-sync indicator) before the text — `bn.innerHTML='<span class="df-pulse"…></span>'+esc(d.banner_ar)` (esc per the b57 discipline). CSS: an opacity `@keyframes dfpulse` (2s), colour via `currentColor` (inherits severity), **reduced-motion-safe** (`@media(prefers-reduced-motion:reduce)`).
- **(B) Landmark chips (`showShortReport`, land face):** surface up to **2** auto-discovered `location_features` as chips (e.g. «شارع داخلي هادئ» · «قرب مدرسة»), EXCLUDING the classification (R1) + height already shown. Display-only, `esc()`-wrapped, non-editable. The land face goes from 4 → up to 6 chips (within the ≤6 discipline) — KNOWN facts instead of the removed «غير محدّد».

## 3. Value-invariance
`amount/low/high/method/rule` UNTOUCHED; `data_freshness` change is display copy only; the chips display broadcast `location_features`. The 5-fixture value byte-gate is byte-identical to v270 (b98) by construction.

## 4. Verification — empirical
- Isolated `test_sprint_2_22_0b99.py` **22/22** — real `_render_banner` (calmer lead + «تنبيه» gone + honesty [source/month/«منذ 183 يوماً»/«إرشاديّة»] preserved; stale/fresh/`.dfc` regression) + the pulse CSS/render + the land landmark chips (in `_isLand`, read location_features, exclude R1/height, cap 2, esc/non-editable).
- **1 R6/Lesson-2 re-point:** `test_sprint_2_22_0b98.py` — my own exact-version pins → version-agnostic format (the recurring Lesson-2; now fixed) = 11/11.
- **DoD:** aggregator **395/395 MATCH** · security **16/16** · surface **45/45** (the banner reframe did NOT break the compliance-honesty gate) · **broad walk 155/155 ALL GREEN**.
- **py_compile** OK. **R14 real-Chromium 390×844** (DOM-measured; screenshot timed out — §20.34): banner pulse dot renders (7×7, `dfpulse 2s`) + text calm («مؤشّر مزامنة», no «تنبيه»); land face = **6 chips** incl. the 2 new «شارع داخلي هادئ» + «قرب مدرسة»; **0 console errors**.

## 5. Deployment
`git push origin master` (backup FIRST) → `git subtree push --prefix "deploy v2" heroku master` (Rule #43; backgrounded).

## 6. Verification curl (post-deploy)
`/api/health` → engine b99. `/api/freshness` `banner_ar` → «مؤشّر مزامنة البيانات: … (منذ N يوماً) · النتائج إرشاديّة» (no «تنبيه»). Served `index.html`: `.df-pulse{` + `<span class="df-pulse"` + the landmark-chips filter present. 5-fixture value byte-gate byte-identical to v270.

## 7. What's NOT in this patch (the rest of Gemini r8, deferred)
- Radial-gradient / glassmorphism hero (beyond b93's champagne hairline + cadastral watermark) — a deeper visual pass.
- Stratification cards with gold (the strata table → horizontal tiered cards) — its own visual slice.
- Landmark chips are **land-only** (the villa face already carries building chips; adding there risks overflow). Villa-face enrichment = a later call.
- Gemini's #1/#2/#3 core critique was already shipped (b92 tiered bracket [verified: the skewed Marikh case renders it; the Abu Hamour report is a tight matched case where the "edge dot" cannot occur] / b94 chips / b93 luxury) or already rejected in r7 (the «الأرضية المبنية على الصفقات» dishonest floor label; the dated «سيتم تفعيل … قريباً» feature promise). Claim-Your-Home stays deferred (unblocks with the B-2 condition engine).
