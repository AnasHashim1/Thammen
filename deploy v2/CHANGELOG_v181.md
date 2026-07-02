# CHANGELOG v181 — Sprint 2.22.0b.100 «العرض الصادق: شرائح سعريّة» (honest price-position display)

**Engine:** `thammen-sprint2p22p0b100-honest-price-position-strata` · **SPRINT_TAG** `2.22.0b.100` · api-health `3.1.0-sprint2.22.0b.100`
**Date:** 2026-07-02 · **Files:** `stock_strata.py` (labels + descriptions + methodology, AR+EN) · `evaluate_unified.py` (OSR note + 2 version lines) · `index.html` (short-report §١ + §٦ row + the cost-led result subline) · `test_sprint_2_22_0b100.py` (new) · re-points b25/b56/b61/b85/a2-c2
**Class:** 🟢 FRONTEND + engine-COPY / **VALUE-INVARIANT** (amount/low/high/method/rule UNTOUCHED — proven: local b100 engine Marikh 54/541/6 = **2,400,000** byte-identical; the strata labels/descriptions never feed the valuation). **Gate-2** (methodology-adjacent user-facing copy) — the PO-signed Sprint 1 of the Gemini-r9 convergence. lawyer + linguist APPROVE.

## 1. Why this matters — the PO caught a methodological overreach
The engine is **built-type/condition BLIND (R7)** — MoJ transactions carry no finish/build-year field. Yet the copy asserted, as FACT, that the higher-priced comparable sales «كان فللاً جديدة فاخرة» (were new luxury villas) — a **price-ratio INFERENCE presented as an observed attribute**. The measured truth is only that those sales priced **≥2.2× the area land median**; a high ratio can equally come from a bigger plot, more floors, a corner, or location. A live audit (Marikh 54/541/6) confirmed the overclaim on the strata card («فاخر / حديث البناء»), the short-report §١ story, and the §٦ row — and that the cost-led headline (2.4M) is a conservative FLOOR that, for a normal villa, silently under-serves it (the market strata put a modern villa at ~3.36M). Gemini r9 (`docs/CONSULT_gemini_r9_median_vs_cost.md`) converged with our guardrails.

## 2. What this patch does (copy-only; describe the MEASURED, infer SOFTLY)
- **Strata labels → PRICE-POSITION (`stock_strata.py`, AR+EN):** «فاخر / حديث البناء»→«الشريحة الأعلى سعراً» · «بناء حديث جيد»→«الشريحة المتوسّطة سعراً» · «بناء متوسط العمر»→«قريبة من سعر الأرض» (EN: Top/Mid price tier · Near land price). The label now names only the measured ratio band (shown beside it); it asserts no finish/age.
- **Strata descriptions → soft inference, flagged «استدلالاً بالسعر / inferred from price»** (AR+EN): the age/finish reading is kept but explicitly marked an inference, not an inspection.
- **Methodology note:** «هذه النسبة تفصل بين فئات العمر والتشطيب»→«مؤشّرٌ استدلاليّ (من السعر) … لا معاينةٌ لهما» (EN twin); «فيلا فاخرة جديدة»→«الأعلى سعراً»; «فئات»→«شرائح».
- **Short-report §١ (cost-led):** «كان فللاً جديدة فاخرة»→«بيعت بأعلى بكثير من قيمة الأرض (شريحةٌ أعلى سعراً — قد تكون أحدث أو أكبر أو أرقى تشطيباً؛ استدلالاً بالسعر لا معاينةً)». The «قيمته العادلة تقترب من قيمة أرضه» claim → an honest conservative estimate «اعتمدنا تقديراً محافظاً ≈ قيمة أرضه + بناءً مُهلَكاً بحسب عمره — وقد تعلو قيمته إن كان بناؤه مُصاناً». «الفلل الجديدة»→«الشريحة الأعلى».
- **Short-report §٦ row:** «الفلل الجديدة الفاخرة حولك — فئة أخرى»→«الشريحة الأعلى سعراً حولك — فئة أعلى، غالباً ليست فئة بيتك».
- **Result-screen cost-led subline (the key under-valuation fix):** adds «وهذا الرقم حدٌّ أدنى محافظ (تعذّر تأكيد حالة البناء)؛ وفيلا مُصانة قد تعلو قيمتها — أدخل حالتها في «حسّن التقييم».» — turns the silent floor into an honest, actionable floor (bridges to the Sprint-2 neutral condition opt-in).
- **OSR note (`evaluate_unified.py`):** «مدفوع بطبقة فاخرة مسيطرة»→«مدفوع بشريحةٍ أعلى سعراً مسيطرة» (hygiene — dormant under the b20 leadership gate; verified not firing on Marikh).
- **KEPT (legit):** the user's OWN finish inputs («تشطيب فاخر» refine field, the is_luxury chip, the scenario «بتشطيب فاخر» what-if) are UNTOUCHED — those are the subject's declared/hypothetical finish, not a claim about comps.

## 3. Value-invariance
The strata labels/descriptions/methodology + the §١/§٦/subline copy do not enter the valuation. Local b100 engine: Marikh 54/541/6 amount **2,400,000** (= v271) with the new labels + the ratio thresholds (1.15/1.50/2.20) UNTOUCHED. The 5-fixture value byte-gate holds by construction (confirmed post-deploy).

## 4. Verification — empirical
- Isolated `test_sprint_2_22_0b100.py` **31/31** (price-position labels; «استدلالاً بالسعر» disclaimer; ratio thresholds intact; §١/§٦/subline honest copy; old «فاخرة»-as-fact GONE; legit subject-finish inputs kept).
- **5 R6/Lesson-2 re-points** (tests pinning the exact old copy b100 honestly changed — **no value/security/methodology assertion weakened**): b85 (strata AR+EN twins → new labels, lockstep + value-math intact), b61 (methodology reworded; language-purge invariants hold), a2-c2 (aging anchor → the b100 price-inference marker; the a2 no-internal-doc invariant holds), b25 (§١/§٦ PDF-contract copy amended, the b62 precedent), b56 (case «بناءٌ مُهلَكٌ»→«بناءً مُهلَكاً»; the «مُهلَك» intent holds).
- **DoD:** aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · **broad walk 156/156 ALL GREEN**. py_compile OK · node --check OK.
- **R14 real-Chromium (mobile 375, fresh b100 payload):** strata card «الشريحة الأعلى سعراً» (no «فاخر / حديث البناء») · §١ price-position + «استدلالاً بالسعر» · the honest floor line · value **٢٬٤٠٠٬٠٠٠** byte-identical · **0 console errors** · no horizontal overflow.

## 5. Deployment
`git push origin master` (backup FIRST) → `git subtree push --prefix "deploy v2" heroku master` (Rule #43; backgrounded).

## 6. Verification curl (post-deploy)
`/api/health` → engine b100. `/api/evaluate {54,541,6}` → amount **2,400,000** cost_led; the stock_strata `label_ar` = «الشريحة الأعلى سعراً» / «الشريحة المتوسّطة سعراً» / «قريبة من سعر الأرض» (no «فاخر / حديث البناء»); methodology carries «مؤشّرٌ استدلاليّ (من السعر)». 5-fixture value byte-gate byte-identical to v271. Served `index.html`: no «فللاً جديدة فاخرة»; «استدلالاً بالسعر لا معاينةً» + «حدٌّ أدنى محافظ» present.

## 7. What's NOT in this patch (Sprint 2 — the durable fix, Gate-2, deferred)
- **Path A / the neutral condition opt-in:** the 3-question NEUTRAL modal (age band / condition / finish — «قد يرتفع أو ينخفض», never «unlock a higher value») + leading with the matching **market stratum** when the subject's class is confirmed. Requires a (condition → stratum) mapping recon + calibration + PO sign-off; the stratum lead is «indicative» at n=11. Copy is drafted in `docs/CONSULT_gemini_r9_median_vs_cost.md`. **Honest note:** a normal villa cannot be safely auto-raised above the cost floor without a condition signal (blind raising would over-value teardowns).
- Reducing the 5.4M repetition count on the cost-led result screen (each surface now labels it honestly as the higher tier / range ceiling; a de-duplication pass is optional).
