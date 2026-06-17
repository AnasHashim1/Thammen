# CHANGELOG v135 — Sprint 2.22.0b.54 «قفل المصطلح: تقييم سوقيّ آليّ» (terminology lock: تقدير → تقييم)

> Engine `thammen-sprint2p22p0b54-tadir-to-taqyim-lock` · SPRINT_TAG `2.22.0b.54` ·
> api-health `3.1.0-sprint2.22.0b.54` · 2026-06-17.
> **Files:** `index.html` (27 user-facing copy edits) · `evaluate_unified.py` (the 2 version-string
> lines only) · `test_sprint_2_22_0b54.py` (new, 44 checks) · 9 sibling tests (R6/Lesson-2 re-points).
> 🟢 **FRONTEND-ONLY / VALUE-INVARIANT** — display copy only; `api.py` + the valuation engine
> UNTOUCHED; no number / range / method / leadership / decision change.

## 1. Why this matters

A PO due-diligence pass (this session) on the «تقدير» vs «تقييم» question established: «تقييم» is a
**generic, non-reserved** word in Qatar — the reserved professional term is **تثمين / مُثمِّن** (the
MoJ «المثمِّن العقاريّ» service; Aqarat, Emiri Resolution 28/2023; our brand ثمّن is the same root).
So the earlier b50 lean toward «تقدير» for our output was a clarity *preference*, not a legal
requirement, and «تقدير» read weak/«تخمين» to the credibility-demanding personas (bank / appraiser /
investor / journalist). **The هد­ف:** present authoritatively-but-honestly. Term-lock decision (signed
via the on-screen تصور + «نفّذ»): the **PRODUCT IDENTITY + the PROCESS = «تقييم سوقيّ آليّ»**; the
**VALUE/RANGE stays «تقديريّ»** (it is honestly an estimated value); the **certified thing + the
disclaimer stay «تقييم معتمد» / «ليس تقييماً معتمداً»**; **تثمين/مُثمِّن avoided for our output**.

## 2. The term-lock rule (the spine)

| الموضع | المعتمد |
|---|---|
| هويّة المنتج + العمليّة | «تقدير سوقي آلي» → **«تقييم سوقيّ آليّ»** · «ابدأ/حسّن/نتيجة التقدير» → «… التقييم» |
| القيمة / النطاق (يبقى) | «القيمة التقديريّة» · «النطاق التقديري السوقي» · «الوسيط (التقدير المركزي)» — **تبقى تقديريّ** |
| الفنّيّ (يبقى) | «عمر البناء التقديري» · «تقدير أقصى» · «تقدير مبدئي» · tier-label «تقدير إرشادي» — **تبقى** |
| الثابت | «ليس تقييماً معتمداً» · «تقييماً رسمياً» · «وزارة العدل» (×17) · CC BY 4.0 (×8) — **بلا مساس** |

## 3. What this patch does (`index.html`, 27 surgical copy edits)

- **22 identity/process flips** «تقدير»→«تقييم»: gate title + «ما هذا؟» + consent affirmation · home
  «تقييم عقارك في قطر» + CTA «ابدأ التقييم» · result top-bar «نتيجة التقييم السوقي» + hero label
  «التقييم السوقي» + the not-certified line «تقييم سوقيّ آليّ — ليس تقييماً معتمداً» · the home-footer
  disclaimer «هذا التقييم السوقيّ الآليّ إرشاديّ» · refine «تحسين/احسب التقييم» + «يحرّك التقييم» +
  «حسّن التقييم» (×5 rendered; 2 code comments correctly skipped) · the report/short-report brand +
  pin lines · the Terms intro + EN «automated market valuation» · the share lines.
- **5 consent-gate + Terms consistency fixes** (caught by the adversarial verify): gate «حدود» bullet
  «والتقييم لا يأخذ…» + «دورك: جرّب التقييم» · Terms §1/§4 «دقّة التقييم» · Terms §5 «التقييم لأغراض الدعم».
- **KEPT verbatim:** every value-adjective «تقديريّ», every «ليس تقييماً معتمداً» distinction, every
  «وزارة العدل» mention + the CC BY 4.0 credit. **RICS/IVS stays tiered** (the MUC fold + the a8
  methodology `<details>` + Terms) — not deleted; plain-language framing leads, the precise clause
  numbers (VPGA 10 / VPS 6 / IVS 106) stay one click away for the professional + the compliance trail.

## 4. Value invariance

`api.py` + the valuation engine are UNTOUCHED (`evaluate_unified.py` diff = the 2 version lines).
Every edit is display copy inside an existing JS/HTML literal — no number / compute path touched.

## 5. Verification — empirical evidence

- **Build via a deterministic workflow** (the term-lock encoded as an explicit flip-list + keep-list)
  → **adversarial 3-lens verify**: the completeness lens diffed the live b53 site against the local
  tree to isolate the real flips and caught **5 misses** in the gate + Terms → all fixed; the
  distinction + over-flip lenses confirmed the invariants held + no value-adjective was wrongly flipped.
- **Isolated** `test_sprint_2_22_0b54.py` **44/44** (each NEW string present + OLD «تقدير» form absent;
  KEEP-list value-adjectives present; «ليس تقييماً معتمداً» + «تقييماً رسمياً» + «وزارة العدل» + «CC BY
  4.0» present; no v.amount/low/high mutation; R6-format version checks).
- **9 sibling re-points (R6/Lesson-2, intent preserved)**: b15 · b17 · b24 · b25 · b27 · b30 · b31 ·
  b50 · b52 — each carries «# b54 R6: تقدير→تقييم (identity lock)»; zero value/security/methodology
  assertion weakened.
- **DoD:** aggregator **395/395 ALL COUNTS MATCH** · security **15/15** · surface honesty **45/45** ·
  broad walk **113/113 ALL GREEN** (173.7s).
- **R14 real-Chromium 390×844** (node absent → Chromium is the JS gate): all 7 functions parse,
  **0 console errors**; the gate renders «ثمّن — تقييم سوقيّ آليّ» + the affirmation + the protected
  «وليست تقييماً معتمداً» (visible, intact); a live villa result renders the hero «التقييم السوقي» +
  «تقييم سوقيّ آليّ — ليس تقييماً معتمداً» + the value range stays «النطاق التقديري السوقي»; **no
  overflow** (docScrollW 390 == clientW, content maxRight 370 < 390).

## 6. Deployment

```
git -C "C:\Thammen" subtree push --prefix "deploy v2" heroku master
git -C "C:\Thammen" push origin master
```
(Rule #43; HARD GATE 1 — explicit PO consent required before this.)

## 7. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health | findstr "2.22.0b.54"
curl -s "https://thammen.qa/" -A "Mozilla/5.0" > out.html
findstr /C:"تقييم سوقيّ آليّ" out.html
findstr /C:"وزارة العدل" out.html
findstr /C:"ليس تقييماً معتمداً" out.html
```
Plus the live **5-fixture value-invariance gate** (browser-UA, Rule #61) byte-identical to v225 —
54/541/6 2.4M cost_led · 56/647/6 3.8M geo_full · 55/296/13 2.6M e25 · 56/565/21 2.4M matched ·
52/903/90 refusal.

## 8. What's NOT in this patch (scope boundary)

- **No value/methodology/engine change.** **No** removal of the «وزارة العدل» attribution (a CC BY 4.0
  legal obligation + the #1 credibility asset) or the «ليس تقييماً معتمداً» disclaimer (the regulatory
  cover; the product remains a non-certified AVM — `rics_compliant=false` by design).
- **تثمين/مُثمِّن** intentionally NOT used for our output (the reserved Qatari professional term).
- **b55 (report declutter)** — the next sprint (short report → بطاقة; full report → 12 notes grouped
  into 3 clusters + consolidated legal/MUC + thin-footer metadata) — DEFERRED, per the agreed sequence.
- The borderline output-references «تحقّق من التقدير» / «تعديل جوهري في التقدير» / «المساحة المعتمدة في
  التقدير» were judged value/output references (not product identity) and left as «تقدير».
