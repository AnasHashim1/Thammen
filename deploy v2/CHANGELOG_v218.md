# CHANGELOG v218 — Sprint 2.22.0b.147 «دور شاشة النتيجة» (the result screen's role)

**Engine:** `thammen-sprint2p22p0b147-result-screen-role` · **SPRINT_TAG** `2.22.0b.147`
**Date:** 2026-07-26 · **Files:** `index.html` (+137/−111) · `evaluate_unified.py` (2 version lines) ·
`test_sprint_2_22_0b147.py` (new) · 8 sibling test re-points
**Class:** 🟢 FRONTEND-ONLY / **VALUE-NEUTRAL** — `api.py` git-confirmed UNTOUCHED; no valuation logic;
the amount is PRESENTED, never recomputed.
**Gate-2:** PO-signed **«أ+ب»** after a measured review of live b146.

---

## 1. Why this matters

The PO observed: *«بعد شاشة الادخال، هناك تفاصيل العقار تظهر — ثم يتم تكرارها في التقرير الموسع»*, and
asked whether the site had reached ideal leanness.

**Measured on live b146** (villa 54/541/6, 812px viewport):

| surface | visible | expanded | verdict |
|---|---|---|---|
| short report | 1.6 screens | 5.9 | lean ✅ |
| **full report** | 12.9 | **13.7** | correct by design (RICS artifact) ✅ |
| **result screen** | 7.1 | **16.3** | **LONGER than the «detailed» report** ✗ |

The result screen's «تحليل إضافيّ (التفاصيل والمقارنات)» fold held **11 blocks / 5,127 chars** — a second
copy of most of the full report. Char counts were near-equal (11,879 vs 11,301): the result screen was
not a summary of the report, it *was* the report, re-titled.

**Root cause:** the result screen had no defined ROLE. Fifteen lean sprints (b103·b129·b131·b141…)
trimmed *within* each surface; none removed the overlap *between* surfaces.

## 2. What this patch does

**(أ) The «تحليل إضافيّ» fold is REMOVED.** The result screen becomes a DECISION surface; the full report
stays the complete artifact, one tap away in the sticky bar.

**(ب) «حدود هذا التقدير» folds CLOSED by default** behind its own «عدم اليقين: {level}» chip — the b52
precedent (the VPGA-10 clause FOLDS, never deleted).

**The measured gap this also closes:** the "full" report was **not complete**. Four blocks existed ONLY
inside the removed fold. They are moved via a new shared builder **`_autoFindingsHtml(d,v,hasValuation)`**:

| moved block | why it had to move, not be deleted |
|---|---|
| range-expansion explanation | valuation explanation, absent from the report |
| the trend card | carries the **SIGNED a3/T1.2** suppressed-slope framing («اتجاه تاريخي»), which b141 recorded as living **only here** |
| geometric findings | corner/street evidence, landmarks, verified cadastre area |
| location features | R1 · quiet street · near mosque/school/clinic · permitted height |

**Kept on the result screen (deliberately, against a naive delete):**
* the **map button** — an ACTION, not a document detail, and it exists ONLY here (the report has no map).
* the **«يفترض بناءً نموذجياً» honesty nudge** — PROMOTED out of the fold into the visible flow beside
  the «حسّن التقييم» CTA. It is decision-relevant, so burying it was wrong.

**Dropped without a move (verified redundant):**
* the property-BASICS rows (address · district · plot · type · zoning · PIN/electricity/water/age-floor)
  → they render again, in full, in the report's «بيانات العقار الأساسية» card. **These are exactly the
  «تفاصيل العقار» the PO flagged.**
* the «المخاطر والإشارات» card — measured content on our fixtures: *«لا يوجد إعلان مرتبط بهذا التقييم»*,
  an EMPTY-STATE card the report already folds by the signed D8/b14 decision.

**REFUSAL path preserved byte-for-byte:** `_autoFindingsHtml` is still built into the `h` scratch at its
original position, so `flat+=h` is unchanged in content *and order*. Proven with a synthetic refusal
payload carrying `location_features` + `trend`.

## 3. Verification — empirical evidence

**Measured before → after** (villa 54/541/6, 812px):

| | before (b146) | after (b147) |
|---|---|---|
| result screen, visible | 7.1 screens | **4.1** |
| result screen, expanded | 16.3 screens | **6.7** (−59%) |
| result screen chars | 11,879 | ~3,900 |
| full report | 17 blocks | **19** (gained geo + location; lost none) |

* isolated `test_sprint_2_22_0b147.py` — **41/41**
* DoD aggregator **ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45**
* **broad regression walk 199/199 ALL FILES GREEN** (231s)
* `python -m py_compile` OK · `node --check` on all 3 inline scripts OK
* **R14 real-Chromium**, 5 fixtures × AR+EN (10 renders): amount rendered byte-identical · fold gone ·
  basics gone from the result yet present in the report · report carries the moved blocks · map action
  present · compliance (MUC + RICS + «ليس تقييماً معتمداً») intact on every render · **no horizontal
  overflow** · **0 console errors**
* refusal path: unchanged (2.2 screens, flat, no fold, no nudge)

**Sibling re-points (8, all R6/Lesson-2 — structural pins on the removed fold; ZERO value, security,
compliance or methodology assertion weakened):** b9 · b15 · b31 · b32 · b34 · b52 · b83 · b125 · b134 ·
b141. Each was re-pointed to the *preserved intent* (e.g. b9's property-basis panel still surfaces — on
the confirm screen basis-only and in FULL in the report; b52's MUC clause still built and one click away).

## 4. Personas (standing PO directive)

* **Lawyer — APPROVE.** No claim, disclaimer or attribution text was authored or altered; only placement.
  Always-visible on the result screen: the MUC level chip, «ليس تقييماً معتمداً», the freshness caveat and
  the disclaimer. The full VPGA-10 clause is built and one click away (the signed b52 pattern, and (ب) was
  PO-signed explicitly). The CC BY 4.0 MoJ attribution is untouched. The full report gained content.
* **Linguist — APPROVE, nothing to review.** No new user-facing string was written; two internal code
  comments were reworded only so that explanatory prose could not satisfy a test assertion.

## 5. Deployment

```
git push origin master
git subtree push --prefix "deploy v2" heroku master
```

## 6. Post-deploy verification

```
curl -s --compressed -A "Mozilla/5.0 ..." https://thammen.qa/api/health
# expect: 3.1.0-sprint2.22.0b.147
# then the 5-fixture value byte-gate must be byte-identical to v310:
#   54/541/6 2,400,000 cost_led · 56/647/6 3,800,000 geo_full · 55/296/13 2,600,000 e25_capped
#   56/565/21 2,400,000 matched · 52/903/90 refusal
```

## 7. What's NOT in this patch

* **No EN work.** The measured Arabic-in-English leaks (the refusal `next_steps` body, the short-report
  `window_used`, the report's `الاتجاه العام` label and Arabic date, the refine `١٢٣` numerals) are the
  separate **b148** slice.
* **No change to the full report's length.** «المفصّل يبقى مفصّلاً» — it is the RICS artifact and it grew
  by two blocks here, correctly.
* **No engine/valuation change.** The 5-fixture value gate is untouched by construction.
* The Terms modal still renders the Arabic §1–§7 above the English mirror in EN mode — a signed-text
  ordering question left to the PO.
