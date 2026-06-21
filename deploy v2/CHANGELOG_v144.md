# CHANGELOG v144 — Sprint 2.22.0b.63 «ترشيق بداية المختصر للمالك» (short-report page-1 owner declutter)

**Engine:** `thammen-sprint2p22p0b63-shortreport-owner-declutter` · **SPRINT_TAG** `2.22.0b.63`
**Date:** 2026-06-21
**Files:** `index.html` (showShortReport page-1: financing buyer-gate + header dev-string drop)
· `evaluate_unified.py` (2 version lines) · new `test_sprint_2_22_0b63.py` · this CHANGELOG.
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (display only; no valuation logic; `api.py` UNTOUCHED).

## 1. Why this matters
PO «ما الأفضل لتقليل الازدحام البصري والبيانات الكثيرة التي ليس لها داعٍ في البداية … ما رأيك بحذف
التمويل؟» + «نعم» (sign-off after a live before/after preview). A 5-persona panel (المالك/المشترية/
المصمّم survived; المثمّن/المحامي + the auto-verifier rate-limited — their lens supplied from ground
truth) flagged the short-report PAGE-1 top as the densest "unnecessary at the start" for the default
**owner**: a mortgage calculator wedged between the headline and §١, plus a raw dev-string in the header.

## 2. Root cause
(a) The D3 financing line (`.thmr-pay` + 3 editable inputs) was rendered **unconditionally** on page-1
(index.html:1936) — so the **owner** default (and seller/investor) met a *buyer* tool right under the
number. A dedicated buyer financing calculator already exists on the result screen, gated to
`d.audience==='buyer'` (b35). (b) The page-1 header `.meta` printed the raw `engine_version`
(«thammen-sprint…-…») above المرجع — dev noise on the first frame of a printable owner report.

## 3. What this patch does
- **(1) Financing → BUYER-GATED:** the `.thmr-pay` emission is wrapped in `if((d.audience||'owner')==='buyer'){…}`
  (mirrors the b35 result-screen predicate). The owner/seller/investor no longer see it; the **buyer**
  keeps it on page-1 AND on the result screen. `_srPayment` / `srRecalcPay` stay defined (reused — DRY),
  and the PDF wording + the 3 editable assumptions (20/25/4.5 + «استشر بنكك») are unchanged in source.
- **(2) Dev-string dropped from the page-1 header:** the header `.meta` now prints المرجع `TH-…` only
  (the `<br>` + the `engine_version` span removed). Authenticity is still provable via the QR + the
  `thammen.qa/verify` link + the content fingerprint. The **FULL report** (`showReport`) keeps
  `engine_version` in its footer (b17 contract — untouched), as does the page-2 meta.

## 4. Verification — empirical evidence
- isolated `test_sprint_2_22_0b63.py` **14/14** (buyer-gate predicate wraps `.thmr-pay`; literal kept in
  source for the buyer; functions stay defined; b35 result-screen calc untouched; `engine_version` gone
  from showShortReport but kept in the full report; المرجع kept; value-math = only ×0.90/×1.10/×1.30; b62
  §3/§5 + compliance + §6 table + full-report clusters intact; version format).
- **ZERO sibling re-points** — `SR` in `test_sprint_2_22_0b25.py` is the showShortReport SOURCE text, so
  the gated literals (`id="srDown"`, «استشر بنكك», …) stay in source → b25 **77/77**; b62 **22/22** ·
  b35 **17/17** · b56 **30/30** · b17 **33/33** all green untouched.
- DoD: aggregator **395/395 MATCH** · security **15/15** · surface **45/45** · broad walk **122/122 ALL
  GREEN** (121→122, +the new b63 test).
- **R14 real-Chromium 390×844** (live Marikh cost-led, DOM-measured; screenshot timed out — §20.34):
  **OWNER** → financing ABSENT, header dev-string ABSENT (`null`), المرجع KEPT, §١ «لماذا أقل» renders
  directly after the hero, value «٢٬٤٠٠٬٠٠٠ ريال» unchanged, page-1 **1989→1910px (−79)**, no doc overflow,
  **0 console errors**; **BUYER** → financing PRESENT, القسط «١٠٬٦٧٢ ر.ق شهرياً», value unchanged.

## 5. Honest note
A targeted declutter of the *top* (the highest-attention, lowest-relevance items for the owner), not a
size overhaul: page-1 stays ~2.4 mobile screens because the owner-core (hero + §١ + §٢ + §٣ + §٤ + footer)
is inherently dense. Going further means moving §٣/§١ off page-1 — a content trade-off (re-sign), NOT done.

## 6. Deployment
```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health                              # engine = …b63
curl -s https://thammen.qa/ | grep -c "if((d.audience||'owner')==='buyer'){"   # expect 1 (financing gate)
# 5-fixture value byte-gate identical to v234.
```

## 8. What's NOT in this patch
- The buyer financing calculator on the result screen (b35) — untouched.
- The full report + page-2 meta engine_version (b17 contract) — untouched.
- The optional follow-ups (the ٥٫٤م triple-repeat → keep once; §٣ buyer-line tighten) — deferred (PO).
- No valuation logic / figures / thresholds touched.
