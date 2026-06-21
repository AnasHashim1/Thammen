# CHANGELOG v143 — Sprint 2.22.0b.62 «رشاقة المختصر» (real short-report page-1 leanness)

**Engine:** `thammen-sprint2p22p0b62-short-report-lean` · **SPRINT_TAG** `2.22.0b.62`
**Date:** 2026-06-21
**Files:** `index.html` (showShortReport §5 + §3 + comment) + `evaluate_unified.py` (2 version lines)
· `test_sprint_2_22_0b25.py` (R6 re-points — contract amended) · new `test_sprint_2_22_0b62.py` · this CHANGELOG.
**Class:** 🟢 FRONTEND-ONLY / **VALUE-INVARIANT** (display copy/structure; no valuation logic; `api.py` UNTOUCHED).

## 1. Why this matters
PO «أريد رشاقة حقيقيّة، خاصّة في المختصر» + **«لا بأس عدّل العقد الذي وقّعته»** (authorizing an
amendment to the b28 signed PDF print contract) + «افعل الأصوب». The persona review measured the
short-report page-1 «الخلاصة» at **2216px ≈ 2.6 mobile screens** (the densest, cost-led). The full
report stays untouched (already lean — b51 dedup + b55 3-clusters; long-by-design «المفصّل يبقى مفصّلاً»).

## 2. Root cause
(a) §٥ «أشياء قد ترفع الرقم» (cost-led) rendered a **full card** (header + renovated/luxury rows +
rent row + micro) whose figures **duplicate §٦** «جدول السيناريوهات — ماذا لو؟» on page-2. (b) §٣
«الخلاصة العملية» carried two verbose advice paragraphs.

## 3. What this patch does (the «أصوب», contract amended)
- **§٥ cost: full card → a one-line teaser** «◆ قد يرتفع الرقم: بالتجديد الكامل أو التشطيب الفاخر …
  والإيجار أقوى معلومة … التفاصيل في جدول «ماذا لو؟» بالأسفل؛ أدخلها من زر «حسّن التقييم» في الموقع.»
  The full upside table stays in §٦ (page-2) → page-1 drops the duplicate figures. KEEPS the GT invite
  («حسّن التقييم») + the rent-is-strongest nudge («الإيجار أقوى معلومة»). The market/income/land §٥
  variants are untouched (their content is unique, not on page-2).
- **§٣ advice bars compressed** to two tight lines — **KEEPING the SIGNED hard ceilings (×1.10 / ×1.30,
  «سقف +10%» / «فوق +30%»)**, the realistic-close nuance, and the buyer due-diligence («اطلب بيان وزارة
  العدل» + «العمر الحقيقيّ لا قول البائع»).
- **Contract amended (per PO):** the b28 PDF wording for §٣/§٥ is superseded by this leaner rendered
  form; `test_sprint_2_22_0b25.py` §٣/§٥ assertions re-pointed (R6/Lesson-2) — the SIGNED ceilings +
  «حسّن التقييم» + «الإيجار أقوى معلومة» + no-sweep-figures invariants preserved.

## 4. Verification — empirical evidence
- isolated `test_sprint_2_22_0b62.py` **22/22** (E14: §3 compressed + ceilings/×1.10/×1.30/«بيان وزارة
  العدل» kept · §5 teaser + old card gone + «الإيجار أقوى معلومة»/«حسّن التقييم» kept + §6 table present +
  orphan `_scnBy` dropped · compliance kept · full-report clusters intact · version format).
- siblings re-verified: **b25 77/77** (re-pointed) · **b54 44/44** · **b56 30/30** (untouched).
- **R14 real-Chromium 390×844** (live Marikh cost-led): page-1 **2216 → 2009px** (2.6 → 2.38 screens,
  **−207px = one full card removed**); 5 cards → 4; §5 teaser «◆ قد يرتفع الرقم», old rows gone; §3
  «◆ بائعاً/مشترياً» (old gone), ceilings + «بيان وزارة العدل» + «حسّن التقييم» kept; §٦ «جدول
  السيناريوهات» still on page-2 (upside preserved, not lost); **0 console errors**; no overflow (370<390).
- DoD: aggregator **395/395** · security **15/15** · surface **45/45** · broad walk **121/121**.

## 5. Honest note
A real reduction (−207px, one card), but page-1 remains ~2.4 screens because the **owner-core** (navy
hero + §١ «لماذا» + §٢ الأرقام الثلاثة + §٣ advice + §٤ source + footer) is inherently ~2 screens on
mobile. Going below that means moving the owner's §٣ advice / §١ «why» off page-1 — a content trade-off
left for a PO decision (NOT done here).

## 6. Deployment
```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health                  # engine = …b62
curl -s https://thammen.qa/ | grep -c "أشياء قد ترفع الرقم — أخبرنا بها"   # expect 0
# 5-fixture value byte-gate identical to v233.
```

## 8. What's NOT in this patch
- The full report (untouched — already lean by design).
- Moving §٣ advice / §١ to page-2 (PO content trade-off).
- The page-1 footer (left as-is — terminology-locked b54).
- No valuation logic / figures / thresholds touched.
