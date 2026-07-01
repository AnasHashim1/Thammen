# CHANGELOG v175 — Sprint 2.22.0b.94 «تنظيف الشارات + ترقية الدقّة» (known-only chips + the accuracy-upgrade block)

**Engine:** `thammen-sprint2p22p0b94-chips-known-upgrade-block` · **SPRINT_TAG** `2.22.0b.94` · api-health `3.1.0-sprint2.22.0b.94`
**Date:** 2026-07-02 · **Files:** `index.html` (villa chips gating + the `.thmr-upg` block + CSS) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b94.py` (new)
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT**. **Gate-2** signed: the PO «go» 2026-07-02 package (Gemini r7 #2, adjudicated).

## 1. Why this matters
The b90 face rendered «غير محدّد/غير محدّدة» on up to 3 of the 5 villa chips (finish · annexes · sometimes BUA/age) — reading as a SYSTEM gap («كيف تقيّم وأنت لا تعرف؟»), not an invitation (Gemini r7: it «يهدم الثقة»).

## 2. What this patch does (`showShortReport`, villa chips branch)
- **Known-only face:** each chip is now GATED on its datum (BUA on `cost.bua_m2` · age on the registered floor [the b73 «قد يكون أقدم» tooltip preserved] · finish on `is_luxury||condition` · annexes on the user inputs). No «غير محدّد» chip ever renders.
- **The «ترقية دقّة المؤشّر» block** (below the legal line, before the «عرض التفاصيل» fold): unknowns collect into `_srMiss` and render as an accuracy-upgrade invitation — «مواصفات لم تدخل في هذا الرقم الآلي: {التشطيب · الملاحق}» + a «حسّن التقييم» button opening the **EXISTING** refine screen. **Adjudicated (#54/lawyer):** Gemini's «سيتم تفعيل ميزة التصحيح الذاتي قريباً» future-promise was REPLACED — refine exists and works today; no feature promise, no «قريباً».
- Land branch untouched (its chips were already presence-gated → no upgrade block).

## 3. Value-invariance
Chip gating + one display block; the only `v.amount` multiplications remain the 3 disclosed conventions (pinned). The 5-fixture value byte-gate is byte-identical by construction.

## 4. Verification — empirical
- Isolated `test_sprint_2_22_0b94.py` **15/15** (no unknown chip values rendered · all 4 gates · `_srMiss` ×4 · the honest copy + no «قريباً»/«التصحيح الذاتي» · CTA→refine · placement legal→upg→fold · CSS · value-math pin · R6 version format).
- Siblings b90 **29/29** · b92 **22/22** · b93 **15/15** — zero re-points. DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · **broad walk 150/150 ALL GREEN** (149→150).
- **R14 real-Chromium 375×812** (preview, live fixtures; DOM-measured — the screenshot channel down §20.34): cost-led villa (f_marikh ٢٬٤٠٠٬٠٠٠) → face = 3 KNOWN chips (البناء ≈٤٧٩ · العمر فوق 17 · الأرض ٦١٣), **0 «غير محدّد»**, the upgrade block «التشطيب · الملاحق» + the «حسّن التقييم» button, order legal→upg→fold; land (f_land ١٬٢٠٠٬٠٠٠) → no upgrade block; **EN** "Upgrade the indicator's accuracy — … the finish · the annexes / Refine the valuation" no AR leak; **no doc overflow (375==375)**; **0 console errors**.

## 5. Deployment
`git push origin master` (backup FIRST) → `git subtree push --prefix "deploy v2" heroku master` (backgrounded).

## 6. Verification curl (post-deploy)
`/api/health` → engine b94. Served `index.html`: `thmr-upg` + «ترقية دقّة المؤشّر» present; the unknown-chip `t('غير محدّد','not set')` literals absent from `showShortReport`. 5-fixture byte-gate identical.

## 7. What's NOT in this patch
- The interactive chip re-eval (Claim Your Home) stays DEFERRED (Gemini r7 concurs: interactivity that cannot move the number yet = a trap) — unblocks with the B-2 condition-axis data (b71).
- م٢ (subdivision engine) + م٣ (bank PDF) — next in the queue.
