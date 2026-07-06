# CHANGELOG v187 — Sprint 2.22.0b.106 «استكمال متطلبات معايير RICS في نموذج التقرير» (S1 — RICS disclosures)

**Engine:** `thammen-sprint2p22p0b106-rics-report-disclosures` · **SPRINT_TAG** `2.22.0b.106`
**Date:** 2026-07-06 · **Files:** `index.html`, `evaluate_unified.py` (the 2 version lines) (+ `test_sprint_2_22_0b106.py`)
**Class:** 🟢 FRONTEND copy / VALUE-INVARIANT — additive disclosure lines in `showReport` + the short-report §٩; no value/method/rule change (the 5-fixture villa byte-gate holds by construction). `api.py` untouched.

---

## 2. Why (RICS valuer-lens: the report output had 3 REJECT-RISK transparency gaps)

The 4th audit (the RICS valuer lens) found the engine methodology RICS-grade but the **report OUTPUT** missing
three disclosures a professional reader (bank/valuer/lawyer) would reject over — none of which changes the
number, all of which are honest statements of what the code already does. PO decision (b): **honest disclosure
now; the real time-adjustment is a later Gate-2.** S1 closes the 3 reject-risks + 2 cheap credibility items.

## 3. What this patch does (5 additive disclosures)

**R-1 — Basis of value (RICS VPS 2 / IVS 102), stated WITH the reported value.** RICS requires the basis of
value to be reported alongside the figure. On the **full report** a Market-Value definition line renders
directly under the «القيمة السوقية (MV)» headline (after the tier badge, before the range) — the IVS Market
Value wording verbatim in intent («المبلغ المُقدَّر لتبادُل العقار في تاريخ التقييم بين بائعٍ وشارٍ راغبَين …
دون إكراه»), keeping «ليس تقييماً معتمداً» adjacent (no new/elevated claim). A **compact** basis line is
added to the **short report §٩** before the IFRS-13 legal disclaimer.

**R-2 — Latest MoJ record date + age (VPS 6 report-data disclosure).** In the «حول البيانات» cluster:
«أحدث سجلّ صفقات لدى وزارة العدل: {latest_record_ar} (منذ {days_old} يوماً)» — threaded from the
already-broadcast `data_freshness.latest_record_ar` / `days_old` (**no new API call**).

**R-3 — Honest time-adjustment posture (code-truthful, PO decision b).** In «حول البيانات»: «النافذة الزمنيّة
للأدلّة تمتدّ حتى ٢٤ شهراً (وتتّسع إلى ٣٦ عند قلّة العيّنة)؛ ولا يُطبَّق تعديلٌ زمنيّ صريح على الوسيط — وقِدَمُ
البيانات سببٌ مُعلَن لعدم اليقين الجوهري.» **Scoped OUT for `raw_land`** (fact #2: the villa/house median is a
plain percentile — NOT time-normalised; the land grid IS time-normalised and discloses that in its own panel,
so the "no time adjustment" claim would be false on the land path).

**C-4 — Evidence hierarchy (VPS 3 / IVS 103).** One line in «حول البيانات»: «طبيعة الأدلّة: صفقاتٌ فعليّة
مسجَّلة لدى وزارة العدل — لا أسعار إعلاناتٍ ولا عروض.» (applies to land too — kept unscoped).

**C-7 — The range as the quantitative uncertainty expression (the bank officer's re-study ask).** Right after
the MUC clause: «النطاق المعروض ({low} – {high} ر.ق) هو التعبير الكمّي عن عدم اليقين في هذا التقييم؛ والقيمة
المركزيّة هي التقدير الأرجح ضمنه.» — declares the FUNCTION of the range that already exists (no new math).

Every AR line carries an EN twin (`t(...)`); every RICS/IVS token is LRM-wrapped; the register matches the
b105 lock («عدم اليقين الجوهري», not «تحفظ مادي»).

## 4. VALUE-INVARIANT

All five are additive `h+=` / `cData+=` disclosure lines; no figure/method/rule touched; `api.py` +
`evaluate_unified.py`-logic untouched (only the 2 version lines). The 5-fixture villa byte-gate holds by
construction. R14: Marikh amount **2,400,000** unchanged; raw_land **1,200,000** unchanged.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b106.py` **22/22** (R-1 full + short + placement · R-2 fields threaded · R-3
  wording + 24/36 window + raw_land scope-out + MU tie-in · C-4 · C-7 after MUC + range-gated) · py_compile OK
  · `node --check` OK (2 script blocks).
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **161/161
  ALL GREEN** (b103–b106 all in the set; **ZERO re-points** — additive disclosures pin no prior string).
- **R14 real preview 390×844** (DOM-measured, AR + EN):
  - **AR full report (Marikh cost-led):** all 5 disclosures render (R-1 basis + «ليس معتمداً» kept · R-2 «31 ديسمبر 2025 (منذ 163 يوماً)» · R-3 no-time-adjustment · C-4 · C-7 range 2.4M–5.4M); amount **٢٬٤٠٠٬٠٠٠** unchanged; def12 «مرتكز التكلفة»; **0 console errors**; no overflow (390==390).
  - **raw_land (الوعب):** R-3 correctly **ABSENT** (land grid time-normalises separately); C-4 + basis **present**; amount **1,200,000** unchanged.
  - **short report:** compact basis line renders in §٩ before IFRS 13.
  - **EN:** all 5 EN twins render, no AR leak, `dir=ltr`, no overflow, amount 2,400,000 kept.
- **Personas:** lawyer APPROVE (every line raises defensibility; no elevated claim; «ليس معتمداً» kept
  adjacent to the basis) · linguist APPROVE (register-consistent with the b105 lock; RICS/IVS tokens precise).

## 6. Deployment

- `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112).
- **NOT yet deployed** — local build (PO: «أكمل البناء محلياً»).

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.106`.
- served `index.html`: «أساس القيمة: القيمة السوقية (&lrm;RICS VPS 2 / IVS 102&lrm;)» present ·
  «أحدث سجلّ صفقات لدى وزارة العدل» present · «لا يُطبَّق تعديلٌ زمنيّ صريح على الوسيط» present.
- the 5-fixture villa byte-gate byte-identical to v275 (browser-UA #61).

## 8. What's NOT in this patch

- The REAL villa time-adjustment (the R-3 second half — PO decision b: its own future Gate-2, reusing the 2.20
  AdjustmentGrid time-normalisation). The MUC ±% numeric range (needs a methodology basis — deferred). The
  assumptions register (built-ratio 0.77, floors-default, 50-yr depreciation) = **S3 (b108)**. The 3 UI bug
  fixes (dead §٤ rows · EN loading steps · map-modal aria) = **S2 (b107)** — next.
