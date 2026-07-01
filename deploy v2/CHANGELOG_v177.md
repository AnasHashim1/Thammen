# CHANGELOG v177 — Sprint 2.22.0b.96 «الشامل البنكيّ» (م٣, first slice — cover identity + print-visible verify QR)

**Engine:** `thammen-sprint2p22p0b96-full-report-bank-qr` · **SPRINT_TAG** `2.22.0b.96` · api-health `3.1.0-sprint2.22.0b.96`
**Date:** 2026-07-02 · **Files:** `index.html` (`showReport` cover meta + footer QR + print CSS) · `evaluate_unified.py` (2 version lines) · `test_sprint_2_22_0b96.py` (new) · re-points `test_sprint_2_22_0b17/b23/b25.py`
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT**. **Gate-2:** the SIGNED §8 م٣ (bank-grade full report) + the PO package «go» 2026-07-02.

## 1. What this patch does (`showReport`)
The full report is what a bank/valuer prints — b96 makes that artifact bank-grade **without touching the print engine** (the existing `printReportA4` A4 path stays):
- **Cover identity (page 1):** the report **reference** + the **content fingerprint** now sit in the cover meta row next to the cadastral no. / district / date — a bank sees the provenance anchors on the first page.
- **Print-visible verify QR (footer):** the b25 short-report QR pattern brought to the full report — a scannable QR (the LOCAL qrcode lib, zero CDN — the b45 lock) into `thammen.qa/verify` + the fingerprint caption, gated on the broadcast `_verifyUrl` (server HMAC key). On paper the recipient can verify the exact figures haven't been tampered (the b23 tamper-evident contract).
- **Print hardening:** `page-break-inside:avoid` extended to `.rep-qrwrap` + `.rep-comp` (the proof table) so neither splits across A4 pages.
- `_verifyUrl(d)` is called once (hoisted `_repVu`) and shared by the link + the QR — no drift.

## 2. Value-invariance
Display + print CSS; no `v.amount` arithmetic added (only the existing ×0.90 forced-sale stays); the 5-fixture value byte-gate is byte-identical.

## 3. Verification — empirical
- Isolated `test_sprint_2_22_0b96.py` **13/13** (cover ref+fp · footer QR gated on `_repVu` · «امسح للتحقّق» · local-lib post-injection render + try/catch · verify-link + GT-hook not regressed · `.rep-qrwrap` CSS · page-break list · value-math · R6 version).
- **3 R6/Lesson-2 re-points** (my edits shifted literals those tests pinned — zero assertion weakened): b17 (the page-break list grew → regex) · b23 (the report-footer `_vu`→`_repVu` rename; short report keeps `_vu`) · b25 (a bare «qrcode» token in my comment tripped the no-CDN guard → reworded «the LOCAL QR lib»). b17 **33/33** · b23 **47/47** · b25 **77/77**.
- DoD: aggregator **ALL COUNTS MATCH** · security **16/16** · surface **45/45** · **broad walk 152/152 ALL GREEN** (151→152).
- **R14 real-Chromium 375×812** (preview, `.b40_marikh` + a synthetic-fp payload; DOM-measured): cover shows «المرجع:» (+ «بصمة المحتوى:» when fp present); footer QR **rendered** (canvas) into `/verify` + the «امسح للتحقّق» caption + fingerprint; the b91 comparables proof table still renders (no double-render); **EN** "Reference: / Scan to verify this report's authenticity / Fingerprint" no AR leak; **no doc overflow (375==375)**; **0 console errors**. (The QR is absent when the fixture carries no fp — correct; live carries fp via the HMAC key.)

## 4. Deployment
`git push origin master` (backup FIRST) → `git subtree push --prefix "deploy v2" heroku master` (backgrounded).

## 5. Verification curl (post-deploy)
`/api/health` → engine b96. Served `index.html`: `rep-qrwrap` + `id="repQr"` + «امسح للتحقّق» present. 5-fixture byte-gate identical.

## 6. What's NOT in this patch
- A server-side PDF renderer (headless) — the browser A4 print path remains the share mechanism; a true server PDF is a later, heavier slice if the bank workflow needs it.
- Deeper full-report evidence sections beyond b91's proof-first tables — carried.
