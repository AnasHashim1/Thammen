# CHANGELOG v98 — Sprint 2.22.0b.15 — Screen 4: the polished result (progressive disclosure)

**Engine:** `thammen-sprint2p22p0b15-screen4-polished-result` · **SPRINT_TAG** `2.22.0b.15` ·
**api/health** `3.1.0-sprint2.22.0b.15` · **Files:** `index.html`, `evaluate_unified.py` (2 version-string
lines only), `test_sprint_2_22_0b15.py` (new) · **Baseline:** b14 / Heroku v183 · **Date:** 2026-06-10

---

## 1. Why this matters

The owner journey's screens 1–3 (identify → confirm → improve) shipped (b2.1/b2.2/b2.3); b14 made the
result's *voice* coherent. But screen 4 — the result the owner actually reads — was a long, undifferentiated
stack of ~27 panels: the big red Material-Uncertainty card came FIRST (before the number), the basic-info
card and methodology line sat between the top and the figure, and every analytical panel (decomposition,
strata, 10-Year, trend, geometric findings, cap-rate, …) rendered fully-expanded in one scroll. The v4
owner-journey principle is the opposite: **the number arrives as a range that refines, the drama attaches to
evidence quality (never the figure), and detail is available but not overwhelming.**

This sprint restructures the results card (`show()`) into a **3-tier progressive disclosure** without
deleting a single panel and without changing a single value.

## 2. What this patch does (FRONTEND-ONLY, value-invariant)

Restructured `show()` in `index.html` from a single top-to-bottom string build into **tier buffers**
assembled in order. No engine/methodology change — `evaluate_unified.py` diff = the 2 version-string lines;
`api.py` UNTOUCHED. The numeric contract (amounts/ranges/methods/floors) is byte-identical by construction.

- **TIER-1 (always visible, the figure):** the calc-block valuation card leads — tier badge + a NEW **MUC
  level chip** «⚠️ تحفظ مادي: منخفض/متوسط/مرتفع/حرج» + the range-as-lead headline (b3) + muted median marker
  + the headline honesty notes (a17/a19 condition · b4 teardown/luxury · B-1 value_floor · b12 hbu) + the
  moj sample-size (cite-n) + a NEW **«📌 تقدير سوقيّ آليّ — ليس تقييماً معتمداً»** line (a20 status appended
  when present) + a NEW **evidence one-row** (the b2.2 four-axis verdict as one compact row) + the a4
  methodology bare line.
- **Always-visible right after TIER-1 (compliance):** the FULL Material-Uncertainty (MVU) clause card — moved
  from FIRST to directly under the figure, **never collapsed** (the chip in TIER-1 is the first-glance
  signpost; the full RICS/VPGA-10/VPS-6/IVS-106 clause stays open).
- **TIER-2 (collapsed `<details>` accordions, nothing lost):** «🏠 بيانات العقار الأساسية» · «📊 جودة الأدلّة
  (تفصيل)» (the full b2.2 panel) · «📄 {brief title}» (all brief sections incl. cap-rate) · «🔎 التفاصيل
  الكاملة (التحليل والمقارنات)» (decomposition · 10-Year/substantiality · geometry · range-expansion · trend ·
  geometric findings · location features · stock strata · known-unknowns · the a8 RICS/IVS note).
- **TIER-3 (actions):** «✏️ حسّن التقدير — أضف تفاصيل مبناك» → `go('refine')` (the b13 age nudge lives on the
  refine screen) + «📄 التقرير الكامل / حفظ PDF» → `printReport()` (b17 rewires this to screen 5).
- **Always-visible foot (compliance):** data-freshness caveat (Sprint 2.7 staleness commitment) + disclaimer
  + verification footer. The static `.disc` footer (إرشادي + Terms a24 + CC BY 4.0 attribution a25) is
  OUTSIDE `#rOut` → untouched, always visible.
- **Alerts (qualifiers) render ABOVE the number** (A11 subtype/zoning mismatch · asset-type reality check ·
  multi-QARS shared-plot flag + its override action · service-scope badge · sanity warnings) — they qualify
  whether to trust the figure, so they precede it.
- **Refusal path (e.g. 52/903/90) is byte-equivalent to pre-b15:** all tier-2 wrapping is gated on
  `hasValuation`; the insufficient-data card + the non-gated panels render FLAT, in the same order, with the
  compliance surfaces (MVU, freshness, disclaimer) intact.

New infrastructure: `_acc(title,inner,open)` (native `<details class="t2acc">` wrapper — zero new JS
libraries, keyboard/touch accessible; returns '' on empty so no empty accordion ships), `_evOneRow(d)`
(reuses `_evidenceRatings`/`_evPill` verbatim — derive-don't-author §2c), `MUC_LEVEL_AR` chip map, and the
`.t2acc`/`.ev1row`/`.t3block` CSS (theme variables only). `printReport()` now **force-opens** every results
accordion before print and restores the on-screen collapsed state after (F1 — print parity; a closed
`<details>` does not print its content).

## 3. Root cause / structure

`show()` previously appended every panel to one `h` string top-to-bottom, so visual priority == source
order. The fix introduces buffers (`head`, `alerts`, `muc`, `a8acc`, `t1`, `t2`, `t3`, `flat`, `foot`) and a
scratch reuse of `h` for the deep-detail blocks (sliced into one accordion), then assembles:
`valued = head+alerts+t1+muc+t2+t3+foot` · `refusal = head+muc+a8acc+alerts+flat+foot`. Each panel's inner
HTML is preserved verbatim — only its sink changed.

## 4. Verification — empirical evidence

- **py_compile** `evaluate_unified.py` OK; **node** absent (project precedent a8/a21 — R14 Chromium is the JS gate).
- **Isolated** `test_sprint_2_22_0b15.py` **49/49** (tier mapping · no-panel-lost · disclosure-stays-tier-1 ·
  buffers-once · assembly order · printReport force-open/restore · value-invariance: no `v.amount/low/high`
  mutation).
- **DoD:** aggregator **392/392 (ALL COUNTS MATCH)** · security **15/15** · surface-honesty **45/45** · broad
  auto-walk **84/84** (83→84, +the new test).
- **R14 real Chromium 390×844 (EXECUTED):** all 13 b15-touched functions defined; **0 console logs/errors**
  across all 5 anchors; tier order confirmed in the DOM (TIER-1 figure @2538 → full MVU clause @4961 → … →
  TIER-3 @22539); 4 accordions collapsed-by-default, toggle opens body, printReport force-opens all + restores;
  the «التفاصيل الكاملة» accordion contains decomposition + strata + 10-Year + the a8 note (no panel lost);
  refusal (52/903/90) renders **0 accordions + flat insuf card**; MUC chip + full clause + «ليس تقييماً
  معتمداً» + evidence one-row + freshness-in-foot + static compliance footer all present; **no overflow**
  (maxRight 370<390 mobile; scrollW 1265<1280 desktop).
- **Local E2E / value-invariance (real engine, live payloads, browser-UA #61):** 5 anchors numeric-identical
  to b14 — 56/565/21 **2,400,000** (bracket) · 54/541/6 **5,400,000** (thin) · 55/296/13 **2,600,000** (thin) ·
  52/903/90 **None** (refusal) · 56/647/6 **3,800,000** (widened). show() only re-orders + wraps display; it
  never touches the value.

## 5. Deployment

```
heroku auth:whoami
git add index.html evaluate_unified.py test_sprint_2_22_0b15.py docs/PHASE0_b15.md CHANGELOG_v98.md
git commit -m "Sprint 2.22.0b.15: screen-4 polished result (3-tier progressive disclosure, VALUE-INVARIANT)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health
curl -s -A "Mozilla/5.0 ... Chrome/120 Safari/537.36" -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
```
Expect: health `3.1.0-sprint2.22.0b.15`; 4 anchors byte-identical (2.4M/5.4M/2.6M/refusal); served
`index.html` carries `class="t2acc"` + `_evOneRow` + the «ليس تقييماً معتمداً» line.

## 7. What's NOT in this patch (scope boundary)

Any value/method change · B-2 / B-2-early-slice (b16) · the full report / DEF-12 two-values (screen 5 = b17) ·
server-side PDF generation · email/sharing infrastructure · apartment surfaces · screen 1–3 redesign. The
report CTA points at the existing `printReport()` until b17 rewires it to the dedicated report screen.
