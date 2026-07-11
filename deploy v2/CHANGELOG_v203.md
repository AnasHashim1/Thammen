# CHANGELOG v203 — Sprint 2.22.0b.125 «أدلّة النتيجة» (S4b, redesign v2 — the result-evidence sections)

**Engine:** `thammen-sprint2p22p0b125-redesign-result-evidence` · **api-health:** `3.1.0-sprint2.22.0b.125`
**Date:** 2026-07-11 · **Files:** `index.html` (the `show()` lower half + `.rs-*` CSS + `printReport`), `evaluate_unified.py` (the 2 version lines), `test_sprint_2_22_0b125.py` (NEW), 13 sibling test re-points.
**Class:** 🟢 FRONTEND-ONLY / **VALUE-NEUTRAL** — `api.py` + the valuation engine UNTOUCHED (except the 2 version-string lines); the amount is PRESENTED, never recomputed. The 5-fixture value byte-gate is byte-identical.

---

## 1. Why this matters

S4a (b124) rebuilt the result HERO (the white value card + count-up + confidence meter). S4b rebuilds the **lower half** of the result screen — the evidence, the reconciliation, the scenarios, the limits — from the legacy **collapsed accordions** into the redesign-v2 language of **flat, scroll-revealed sections** (the designer model `design_handoff_thammen/ثمّن - شاشة النتيجة.dc.html`, lines 94→232). The accordions buried the answer behind clicks; the ordinary owner scrolls, and each section reveals itself in place. Every compliance line is preserved verbatim from a broadcast field, so the redesign is honesty-neutral.

## 2. Root cause

The result screen's lower half was a stack of `_acc(...)` accordions built into the `t2` buffer (the «كيف وصلنا» fold, «بيانات العقار الأساسية», «جودة الأدلّة», «التفاصيل الكاملة»), assembled `h=head+alerts+t1+_mucFold+t2+t3+foot;` — a design that predates redesign-v2 and does not match the S0/S1/S4a scroll-reveal language.

## 3. What this patch does

**Frontend (`index.html`, the valued path of `show()` only):**
- Six pure builders inserted between `_repTrend` and `showReport`:
  - **`_s4bTrendSpark(d)`** / **`_s4bViz(d,v,rows,considered)`** — the evidence viz (a comparable-price bar + the subject's position, all from broadcast fields).
  - **`_s4bEvidence(d,v)`** — the comparables/considered evidence table. Leader-aware frame from broadcast fields ONLY: matched → «قرّرت رقمك»; geo → «نطاق المقارنة الموسَّع جغرافياً» + `pool_n`; cost-led considered → «اطّلعنا على صفقات السوق … لكنّها لم تقُد الرقم» + the «فشل حدّ الموثوقيّة … منهجُ الكلفة» why-line (never «قرّرت رقمك» on cost-led). Rows in a `dir=ltr` `.rs-ctab` + the CC BY 4.0 source line.
  - **`_s4bHow(d,v,acc,how,dense)`** — the reconciliation chip (from `d.reconciliation`: `strong_convergence` → `spread_pct`%; `divergence` → «تباعد المنهجين» label only, no number; else omitted), the 3-value stack (market / cost / income, `.lead` on `leadership.leader`), the **visible** leadership verdict narrative (`pick(v.leadership,'note')`), and a **«تفاصيل منهجيّة للمختصّ»** fold = `how + evidencePanelHtml(d,acc)` (density-open for investor/valuer per b34's `dense`).
  - **`_s4bScenarios(v)`** — the 4 what-if cards + the «تصنيفٌ استدلالاً بالسعر المسجَّل، لا معاينةً» honesty line (b100/b113).
  - **`_s4bLimits(d,muc)`** — the FULL MUC clause (`muc`, verbatim broadcast, never collapsed away) + `reasoning_trace.known_unknowns` + the static due-diligence questions + «… دون تسويةٍ زمنيّة …» + the RICS line («عدم اليقين الجوهريّ وفق RICS Red Book (VPGA 10 / VPS 6) و IVS 106», the b105 term-lock).
- **Assembly:** `h=head+alerts+t1+secEv+secHow+secScn+secLim+secFull+foot+t3;` — the analytical scratch `h`, `_info` (basic-info), and the brief sections fold into **`secFull`** (`<details class="rs-full">` «التفاصيل الكاملة (التحليل والمقارنات)»); nothing lost. `_revealOnScroll('#rOut .rs-sec.rv')` wires the reveal.
- **TIER-3 → sticky action bar** (`.rs-bar`, `position:sticky;bottom:0`): «القيمة التقديريّة: {amount}» + «حسّن التقييم» (go('refine'), gated off for `raw_land` per b97) + short report + full report.
- **Refusal branch UNCHANGED:** `h=head+muc+a8acc+alerts+flat+foot;` (0 `.rs-sec`, no sticky bar).
- **~130 lines of `.rs-*` CSS** before `</style>` (sections/rule/viz/ctab/trend/chip/stack/scard/narr/mfold/scenarios/honesty/limits/full/bar), a `@media(max-width:560px)` grid-collapse, and `body.lang-en #rOut … {direction:ltr}` for the LTR evidence rows.
- **Print parity (F1):** `printReport()` now force-opens EVERY `#rOut details` (the flat folds are `.rs-mfold/.rs-full/.rs-lim`, not the removed `.t2acc`), and a `@media print` rule forces the unrevealed `.rv` sections visible + drops the sticky bar + `page-break-inside:avoid` on `.rs-sec`.

**Engine:** `ENGINE_VERSION`/`SPRINT_TAG` → b125. `api.py` UNTOUCHED.

## 4. Compliance preservation (verbatim, from broadcast fields)

- «ليس تقييماً معتمداً» (TIER-1, always visible) · the FULL MUC clause (`_mucCardHtml`, built as `muc`, rendered verbatim inside `_s4bLimits`) · CC BY 4.0 on every evidence table · «قرّرت رقمك» (matched) / «لم تقُد الرقم» + «فشل حدّ الموثوقيّة» (cost-led considered) · «دون تسويةٍ زمنيّة» · «استدلالاً بالسعر … لا معاينةً» (b100/b113) · the RICS/IVS line uses «عدم اليقين الجوهريّ» (b105 term-lock — NOT «تحفظ مادي»).
- Every rendered figure is a broadcast field (amount, `value_stack.*`, `comparables/considered`, `scenarios`, `reconciliation.spread_pct`, `trend`); no result-screen JS mutates `v.amount/v.low/v.high`.

## 5. Verification — empirical evidence

- **Isolated:** `test_sprint_2_22_0b125.py` **63/63** (builders exist · flat assembly · accordions gone · compliance preserved · reconciliation honesty [spread only on `strong_convergence`; `divergence` → label only] · value-neutrality · refusal unchanged · sticky bar · CSS · version).
- **Sibling re-points (all R6/Lesson-2, zero compliance/value/methodology weakened):** b15 **50/50** · b20 **69/0** · b31 **36/36** · b32 **29/29** · b34/35/37/38/39/40/41/52/54/57/83/91/97/105 all PASS.
- **DoD:** aggregator **395/395 (MATCH)** · security **16/16** · surface honesty **45/45** · **broad walk 177/177 ALL GREEN** (142.8s).
- **py_compile** (evaluate_unified.py + api.py) OK · **node --check** — all 3 inline scripts parse OK.
- **R14 real-Chromium 390×844** (served static, live+synthesized payloads): **marikh cost-led** → value ٢٬٤٠٠٬٠٠٠, identity «التقييم السوقي», «ليس معتمداً», full MUC clause verbatim, 5 sections, 0 console, docScrollW 390==clientW 390, rOutMaxRight 374<390 · **v001 geo** (synth comparables+neighbours) → «نطاق المقارنة الموسَّع», pool 34, CC BY 4.0, `.rs-ctab` LTR, no overflow, 0 console · **cost-led considered** (synth) → «لم تقُد الرقم» + «فشل حدّ الموثوقيّة» + «منهجُ الكلفة» + CC BY, **no «قرّرت رقمك» overclaim**, no overflow, 0 console · **refusal (apt)** → unchanged flat path (0 `.rs-sec`, no sticky bar), no value, no overflow, 0 console.
- **Note:** the `.basket` value-invariance fixtures carry a pre-b105/b76 broadcast `muc_clause_ar` («⚠️ تحفظ مادي») — the display renders the broadcast clause verbatim (compliance requirement); the LIVE b105+ engine emits «عدم اليقين الجوهري» (confirmed post-deploy).

## 6. Deployment

```
git add index.html evaluate_unified.py test_sprint_2_22_0b125.py test_sprint_2_22_0b15.py test_sprint_2_22_0b20.py test_sprint_2_22_0b31.py test_sprint_2_22_0b32.py test_sprint_2_22_0b34.py test_sprint_2_22_0b35.py test_sprint_2_22_0b37.py test_sprint_2_22_0b38.py test_sprint_2_22_0b39.py test_sprint_2_22_0b40.py test_sprint_2_22_0b41.py test_sprint_2_22_0b52.py test_sprint_2_22_0b54.py test_sprint_2_22_0b57.py test_sprint_2_22_0b83.py test_sprint_2_22_0b91.py test_sprint_2_22_0b97.py test_sprint_2_22_0b105.py CHANGELOG_v203.md
git commit -m "Sprint 2.22.0b.125 (S4b, redesign v2): result-evidence sections — flat scroll-reveal (value-neutral)"
git push origin master
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
```

## 7. Verification curl (post-deploy)

```
curl -s -A "Mozilla/5.0" https://thammen.qa/api/health | grep -o '"version":"[^"]*"'   # → 3.1.0-sprint2.22.0b.125
# 5-fixture value byte-gate: 54/541/6=2.4M cost_led · 56/647/6=3.8M geo_full · 55/296/13=2.6M e25 · 56/565/21=2.4M matched · 52/903/90=refusal
```

## 8. What's NOT in this patch

- The engine + `api.py` (untouched; value-neutral by construction).
- The result HERO (S4a / b124 — already redesigned; not touched here).
- The full report `showReport` / short report `showShortReport` (a separate S-slice; the geo NEIGHBOUR rows + the «لم تُبَع بالرقم المُعدَّل» disclosure live there, reachable via «عرض الكل في التقرير ›»).
- The confirm/refine/landing screens (S1/S2/S3 slices).
