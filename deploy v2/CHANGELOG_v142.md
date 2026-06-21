# CHANGELOG v142 — Sprint 2.22.0b.61 «تنقية اللغة» (full-site language purge)

**Engine:** `thammen-sprint2p22p0b61-language-purge` · **SPRINT_TAG** `2.22.0b.61`
· api-health `3.1.0-sprint2.22.0b.61`
**Date:** 2026-06-21
**Files changed:** `index.html` · `evaluate_unified.py` · `stock_strata.py`
· `material_uncertainty.py` · `output_briefs.py` (+ 2 version lines)
· new `test_sprint_2_22_0b61.py` · this CHANGELOG.
**Class:** 🟢 FRONTEND + engine-emitted copy / **VALUE-INVARIANT** (text/display only;
no valuation logic, no `amount/low/high/method/rule` touched; `api.py` UNTOUCHED).

---

## 1. Why this matters

A full-site tour by the **المثمِّن (valuer)** + **اللغويّ (linguist)** personas (PO-directed:
«اتفقوا على الأفضل ونفّذ») found the hand-authored frontend فصيح-clean (b54/b56/b58/b60 held),
but the **engine-emitted** Arabic carried real defects — least-reviewed historically:

- 🔴 **عامية (colloquial):** `stock_strata` methodology read «**هذي** النسبة» (Gulf demonstrative)
  on the rendered strata card.
- 🔴 **Latin-in-Arabic:** «**median** المدمج» (×3) in the strata descriptions + dominant-stratum
  note — while «الوسيط» is the standard Arabic used everywhere else (the Sprint 2.22.0a.2-C2
  fix had cleaned only the `methodology_ar` field, leaving the descriptions).
- 🟡 **«Cap Rate» Latin term** rendered as a user label (×14 engine + ×5 frontend) while the
  standard Arabic **«معدّل الرسملة»** is already used — and the PO flagged it as opaque even to
  him, let alone the ordinary owner.
- 🟡 minor: «MoJ» Latin (seller-strategy note), «غير معروفة»→«غير معلومة», «جاري»→«جارٍ»,
  dual «طابقين/ملحقين»→«طابقان/ملحقان», awkward «نسبة لـ الأرض» / «سعرها لـ وسيط».
- The PO also asked about the home credit-line «من صفقات وزارة العدل المسجّلة — لا أسعار إعلانات»
  (crowding the button) and whether «معدّل الرسملة» should change or be explained.

## 2. Root cause

Engine `*_ar` strings are auto-generated and were never swept the way `index.html` was. The
strata «median»/«هذي» survived the a2-C2 partial fix; «Cap Rate» was carried as a foreign term
across the income sections + the frontend `renderSection` row labels.

## 3. What this patch does

**Decisions agreed by the two personas (PO-delegated):**
- The home credit-line **stays** (it is the #1 honesty signal «لا أسعار إعلانات», not redundant) —
  the problem was spacing → added `.hcred{margin-top:18px}`.
- **«معدّل الرسملة» stays** (the correct standard Arabic; the valuer needs it precise) — but a
  **brief plain gloss** is added on its primary appearance for the general audience.

**Edits:**
- `stock_strata.py`: «هذي»→«هذه» · «median المدمج»→«الوسيط المدمج» (×3) · «median لها»→«وسيطها»
  · «بنسبة سعرها لـ وسيط الأراضي»→«بنسبة سعرها إلى وسيط أراضي المنطقة». (a2-C2 invariant kept:
  meth_block still has «الوسيط المدمج» + «التصنيف بحسب الفئات»; «median» now 0 file-wide.)
- `evaluate_unified.py`: all user-facing «Cap Rate»→«معدّل الرسملة» (Arabic lines only — the 2
  English code comments left intentionally) · «7-8% Cap Rate…»→«معدّل رسملة 7-8%…» (word order)
  · «عمر غير معروف»→«عمر غير معلوم».
- `material_uncertainty.py`: «المساحة المبنية غير معروفة»→«غير معلومة».
- `output_briefs.py`: «وسيط MoJ + 10-15%»→«وسيط وزارة العدل + 10-15%» · «تغيّر Cap Rate»→«تغيّر
  معدّل الرسملة».
- `index.html`: «Cap Rate»→«معدّل الرسملة» (5 renderSection labels/notes) **+ a plain gloss**
  «معدّل الرسملة: نسبة صافي الدخل السنويّ إلى قيمة العقار (الطبيعيّ في قطر 5–6%).» · «جاري الاتصال»→
  «جارٍ الاتصال» · dual «طابقان»/«ملحقان» · «نسبة لـ الأرض»→«نسبتها إلى الأرض» · `.hcred` top-margin.

**DEFERRED (flagged, Rule #39):** the «طريقة»→«منهج» approach-term synonym-unification
(«طريقة الدخل»/«طريقة التكلفة الإحلالية»→«منهج…»). Both forms are correct فصيح (not a defect);
it is the widest-blast item (≈20 prose edits + gender-agreement rewrites + the lone a4 test
re-point) on specialist/refused surfaces. Held as the immediate next micro-pass to keep this
ship clean. The **emoji sweep** of engine banners (⚠️/⛔/✓) likewise remains its own backlog item.

## 4. Verification — empirical evidence

- **py_compile** OK on all 4 engine files.
- **Isolated** `test_sprint_2_22_0b61.py` **33/33** (reads the real files — E14: every defect
  token absent, every replacement present, a2-C2 invariant intact, value-invariance spot-checks,
  version-format).
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **395/395 MATCH** · security **15/15** ·
  surface-honesty **45/45** · broad walk `run_regression_2p22p0a.py` **120/120 ALL GREEN**
  (119→120, **ZERO re-points** — a2-C2/a2-C5/a4/material_uncertainty/scope/b25 all unchanged).
- **R14 real-Chromium 390×844:** all 10 render functions defined (JS parsed) · **0 console errors**
  · home credit-line `margin-top` = **18px** · refine duals «طابقان»/«ملحقان» · statusBar «جارٍ الاتصال»
  · `renderSection('yield')` → «معدّل الرسملة المستخدم» + the gloss, **no «Cap Rate»** · `_strataHtml`
  → «الوسيط المدمج» + «هذه النسبة», **no «median»/«هذي»** · no horizontal overflow (390==390).

## 5. Value-invariance

Copy-only by construction: no change to any valuation/decomposition/leadership code or to
`amount/low/high/method/rule`; `api.py` UNTOUCHED. The post-deploy 5-fixture value byte-gate is
expected byte-identical to v232.

## 6. Deployment

```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health            # engine = …b61
curl -s https://thammen.qa/ | grep -c "Cap Rate" # expect 0
# 5-fixture value byte-gate (browser-UA, Rule #61) identical to v232.
```

## 8. What's NOT in this patch

- «طريقة»→«منهج» synonym-unification (deferred, §3 above).
- Engine-emitted emoji sweep (⚠️/⛔/✓) — separate backlog.
- The `property_factors.py` `__main__` demo `print("…وسيط MoJ…")` — dev-only self-test, not
  user-facing (left).
- No valuation logic, thresholds, or methodology touched.
