# CHANGELOG v139 — Sprint 2.22.0b.58 «إسقاط تأطير التجريبية» (drop the beta/trial framing)

> Engine `thammen-sprint2p22p0b58-drop-beta-framing` · SPRINT_TAG `2.22.0b.58` · api-health
> `3.1.0-sprint2.22.0b.58`. **🟢 FRONTEND-ONLY / VALUE-INVARIANT** — `index.html` copy only; engine = the
> 2 version-string lines; `api.py` + the engine UNTOUCHED. **Files changed:** `index.html` ·
> `evaluate_unified.py` (2 lines) · `test_sprint_2_22_0b58.py` (new) · `test_sprint_2_22_0b54.py` (R6
> re-point) · this CHANGELOG. Date: 2026-06-18.

## 1. Why this matters

**PO directive:** «لا اريد اطلاق نسخة تجريبية. الموقع يعمل بالفعل، فارجو ان تحذف من حساباتك اي ذكر لكلمة
تجريبية. حدث الذاكرة.» — Thammen (thammen.qa) is a **LIVE, working product, NOT a "beta" / «نسخة
تجريبية» / trial**. The earlier copy still framed it as «نسخة تجريبية مجانية بالدعوة … لقياس دقّة التقييم»
/ «free, invite-only accuracy beta … before public launch». b58 removes that framing from the user-facing
copy.

## 2. What this patch does (frontend, value-invariant)

Removed every **user-facing** «تجريبية / بالدعوة / beta / invite-only / before public launch / this beta»
mention, while **preserving the real cover** (which is separate from the word "beta"):

- **Gate affirmation** — «… وأوافق على **المشاركة في النسخة التجريبية** على الأساس …» → «… وأوافق على
  **الاستخدام** على الأساس …».
- **Terms/Privacy (AR)** — header «النسخة التجريبية المجانية» → «الخدمة المجانية» · §1 title «الموافقة على
  المشاركة» → «الموافقة على الاستخدام» · §1 body «هذه نسخة تجريبية مجانية بالدعوة لقياس دقّة التقييم …
  المشاركة اختيارية» → «هذه خدمة مجانية … الاستخدام اختياري» · §3 «بياناتك في هذه النسخة» → «… في هذه
  الخدمة» · §6 «في هذه النسخة» → «في هذه الخدمة».
- **Terms/Privacy (EN) + the English gate fold** — «Beta Terms of Use … (free beta)» → «Terms of Use …
  (free service)» · «A free, invite-only accuracy beta — to validate estimate accuracy before public
  launch.» → «A free automated market-estimate tool for villas & land in Qatar.» · «Free, invite-only beta
  … agree to participate. Participation is optional» → «A free service … agree to use it. Use is optional»
  · «Your data in this beta» → «Your data» · «stores no personal data in this beta» → «… no personal data».
- Two internal HTML comments «Beta Terms & Privacy» → «Terms & Privacy».

**PRESERVED (the actual regulatory + honesty cover):** «ليس تقييماً معتمداً» (×10) · the **free** framing
(«خدمة مجانية» — free-vs-paid is the Decision-28/2023 line) · the consent affirmation «أُقرّ بأنني فهمت أن
ثمّن تقييم سوقيّ آليّ للدعم وليس تقييماً معتمداً» + the consent gate + Terms modal · «مستقلّة غير منتسبة
لوزارة العدل» · the **CC BY 4.0** MoJ open-data attribution (×8, legally mandatory). **KEPT internal (not
user-visible):** the DOM id `betaGate` + the `thammen_beta_ack` storage key + `window._betaAck` (code
identifiers — renaming them is a no-user-benefit refactor with test churn).

**`evaluate_unified.py`** — `ENGINE_VERSION`/`SPRINT_TAG` → b58 (the 2 lines only).

## 3. Verification

- **Isolated** `test_sprint_2_22_0b58.py` — **27/27** (no user-facing تجريبية/بالدعوة/beta/invite-only/this
  beta in the comment-stripped visible HTML; the reworded copy present; the real cover preserved; the
  consent gate + Terms reachable; b57 esc() not regressed; value-invariance; engine-format).
- **R6 re-point (test-only):** `test_sprint_2_22_0b54.py` Terms-§1 check (the b54 terminology-lock pinned
  «بالدعوة لقياس دقّة التقييم» which b58 removes → re-pointed to the new §1 «هذه خدمة مجانية»; the lock's
  «old تقدير absent» invariant kept) — **44/44**. b56/b50 (beta-absence checks) green WITHOUT re-points.
- **DoD** (`PYTHONIOENCODING=utf-8`): aggregator **ALL COUNTS MATCH** · security **15/15** · surface
  **45/45** · broad walk **117/117 ALL GREEN** (116→117, +b58).
- **R14 live Chromium 390×844**: the gate renders with **no «تجريبية»**, the affirmation «وليس تقييماً
  معتمداً» + «وأوافق على الاستخدام» kept; the Terms modal has **no beta/بالدعوة anywhere**, «خدمة مجانية» +
  «ليس تقييماً رسمياً» + «غير منتسبة لوزارة العدل» kept, §1 reworded; **0 console errors**; no overflow.

## 4. Deployment

```
cd /d "C:\Thammen"
git add "deploy v2/index.html" "deploy v2/evaluate_unified.py" "deploy v2/CHANGELOG_v139.md" "deploy v2/test_sprint_2_22_0b58.py" "deploy v2/test_sprint_2_22_0b54.py"
git commit -m "Sprint 2.22.0b.58: drop the beta/trial framing — live product, not a beta (value-invariant)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 5. What's NOT in this patch

- The **consent gate / Terms substance is KEPT** — b58 only removes the word "beta," not the consent layer
  (the «ليس معتمداً» affirmation + free + Terms remain the regulatory/honesty cover).
- The internal `betaGate` / `thammen_beta_ack` / `window._betaAck` identifiers are unchanged (not
  user-visible).
- **No engine / value / methodology change** — `api.py` + the engine untouched; the 5-fixture value gate is
  byte-identical to v229.
