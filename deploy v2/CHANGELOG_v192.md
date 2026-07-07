# CHANGELOG v192 — Sprint 2.22.0b.112 «تحسينات الإفصاح (استشارة جيميناي A1+A2)» (Gemini disclosure refinements)

**Engine:** `thammen-sprint2p22p0b112-gemini-disclosure-refine` · **SPRINT_TAG** `2.22.0b.112`
**Date:** 2026-07-06 · **Files:** `index.html` (2 lines), `evaluate_unified.py` (the 2 version lines) (+ `test_sprint_2_22_0b112.py`; 2 R6 re-points b106/b108)
**Class:** 🟢 FRONTEND copy / VALUE-INVARIANT — two disclosure refinements the Gemini RICS/UX consult
recommended (BOTH runs concurred; CC-adjudicated per Rule #54); no value/method/rule change (the 5-fixture
villa byte-gate holds). `api.py` untouched. R14 confirms amount 2,400,000 unchanged.

---

## 2. Why (Gemini r-consult on the S1/S3 disclosures — two runs, both concurred)

The PO ran the S1–S7 review prompt past Gemini (two independent runs). Both flagged the same two refinements
to the disclosures I had just built. CC adjudicated (#54) and accepted both:

**A1 — over-invoked material uncertainty.** My S1 (b106) R-3 line tied the data-age to «عدم اليقين الجوهري»
(RICS VPGA 10 «Material Valuation Uncertainty»). Both runs: VPGA 10 material uncertainty is a **crisis-condition
term** (COVID-era / market disruption), and invoking it for **routine** 24-month data staleness both alarms the
ordinary owner AND slightly misstates the standard. The FACT (no time adjustment) must stay; the scary tie
should go.

**A2 — the exact RCN ladder exposed the model.** My S3 (b108) assumptions register revealed the full
replacement-cost ladder by exact coefficient (shell 1,200 · ordinary 2,200 · good 2,500 · high 3,000 · luxury
3,500 QAR/m²). Both runs: **VPS 2 requires the METHODOLOGY + source of the assumptions, not the exact
coefficients** — revealing all five turns the report into a contractor-cost debate + exposes the model's
calibration (IP) + adds cognitive load, with no credibility gain.

## 3. What this patch does (2 copy lines)

**A1 — the R-3 data-age line softened** (`cData`, the «حول البيانات» cluster): keeps «دون تعديلٍ زمنيّ صريح
على الوسيط» (the fact) + states the honest consequence «لذا قد تتأثّر الدقّة بتقلّبات السوق الأخيرة»; drops
the «سببٌ مُعلَن لعدم اليقين الجوهري» tie. The genuine MUC clause (thin/dispersed evidence) is untouched
where it truly applies.

**A2 — the RCN register line trimmed** (the cost-led assumptions): «تُقدَّر وفق متوسّط أسعار البناء المحليّة
السائدة، بسُلَّمٍ يتدرّج من التشطيب العاديّ إلى الفاخر» + the **applied** finish level (kept). The **exact
5-level ladder is removed.** **The per-property APPLIED rate is KEPT** (the DEF-12 cost-breakdown arithmetic
`BUA × rcn × retention` — this property's own number, the transparency the PO asked for on the 56/565/21 case;
distinct from the model's full calibration ladder).

Both bilingual (`t()`).

## 4. VALUE-INVARIANT

Two copy lines; no figure/method/rule touched; `api.py` + engine logic untouched (only the 2 version lines).
R14: Marikh amount **2,400,000** unchanged; the per-property cost arithmetic (BUA 479 × applied rate ×
retention) still renders; S1 basis-of-value + C-4 + C-7 + the rest of the S3 register (50-yr depreciation,
floors-default, E26, calibration) untouched.

## 5. Verification (measured)

- Isolated `test_sprint_2_22_0b112.py` **13/13** (A1 softened + fact kept + scary tie gone + window/raw_land
  scope intact · A2 methodology+range + exact ladder gone + applied finish kept + per-property arithmetic kept
  · S1/register otherwise intact) · py_compile OK · `node --check` OK.
- **2 R6/Lesson-2 re-points** (intent preserved): `test_sprint_2_22_0b106.py` (R-3 line re-pointed to the
  softened wording; still asserts «no time adjustment» disclosed + the scary tie GONE) = 22/22 ·
  `test_sprint_2_22_0b108.py` (C-2 re-pointed to the methodology wording; still asserts RCN method + applied
  finish + the exact ladder GONE) = 20/20. Zero assertion weakened.
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface-honesty **45/45** · broad walk **166/166
  ALL GREEN**.
- **R14 real preview 390×844** (DOM-measured, AR + EN): the softened A1 line renders (fact kept, consequence
  stated, VPGA-10 tie gone); the A2 methodology line renders (exact ladder gone, applied finish «عاديّ» kept,
  per-property `BUA 479 × rate × retention` arithmetic kept); amount **٢٬٤٠٠٬٠٠٠** unchanged; basis-of-value
  kept; EN twins render, amount kept; **0 console errors**; no overflow.
- **Personas:** lawyer APPROVE (softening the VPGA-10 invocation for routine staleness raises defensibility —
  over-invoking it is itself a misstatement; methodology+range still satisfies VPS 2 while protecting the
  calibration) · linguist APPROVE (register-consistent; accurate EN twins).

## 6. Deployment

- `git push origin master` FIRST, then `git subtree push --prefix "deploy v2" heroku master` (§20.112).
- **NOT yet deployed** — local build (PO: «أكمل البناء محلياً»).

## 7. Verification curl (post-deploy)

- `/api/health` → `3.1.0-sprint2.22.0b.112`.
- served `index.html`: «قد تتأثّر الدقّة بتقلّبات السوق الأخيرة» present · «سببٌ مُعلَن لعدم اليقين الجوهري»
  absent · «تُقدَّر وفق متوسّط أسعار البناء المحليّة السائدة» present · «شِلّ ١٬٢٠٠» absent.
- the 5-fixture villa byte-gate byte-identical to v275.

## 8. What's NOT in this patch

- The remaining Gemini-accepted items fold into the **S7 draft brief** (not built): C1 (a user-stated
  condition is an ordinary Assumption + limitation-of-inspection, NOT a «Special Assumption» — CC precision
  over both runs) · C2 (inspection-consequence friction copy) · **C3 (price-position labels not «حديثة» —
  align to b100, the terminology catch)** · C4 (ship indicative — NOT «تجريبيّة»/beta, per the live-not-beta
  directive). The S4 land-filter also gains a pre-deploy verification (geo widens to nearby residential land
  before refusing — Gemini B2 run-2). Both are recorded for the PO's sign-off, not built here.
