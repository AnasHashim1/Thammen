# CHANGELOG v121 — Sprint 2.22.0b.38 «الكَيستون: كشف الصفقات المقارِنة للفيلا» (DEF-UX1)

**Engine:** `thammen-sprint2p22p0b38-keystone-comparables` · **SPRINT_TAG** `2.22.0b.38` · **Date:** 2026-06-13
**Files:** `evaluate_property.py` · `evaluate_unified.py` · `index.html` · `test_sprint_2_22_0b38.py` (new) · `test_sprint_2_22_0b37.py` (R6 re-point)
**Class:** 🟢 engine-additive **display-only / VALUE-INVARIANT** · Gate-2 **SIGNED BY DELEGATION** («اكمل وافعل الأصوب», 2026-06-13) · Gate-1 = explicit deploy go.
**Recon basis:** `docs/PHASE0_DEF_UX1_keystone_comparables_recon.md`.

## 1. Why this matters

The §4ب persona LIVE review ranked **DEF-UX1 the highest-value item (7/10 personas** — البنك·المثمّن·السمسار·المستثمر·المالك·الصحفي·المشترية): the user is shown a number but **not the actual MoJ transactions that produced it** — the keystone trust gap. A villa response carried only `source_ar` («وسيط N معاملة في نفس الشريحة والمنطقة») + `n_transactions`; lands have surfaced their comparable rows since Sprint 2.20 (`comparable_grid`), villas never did. b38 closes the asymmetry for the case where comparables genuinely drove the number.

## 2. Root cause / the gap (the «مبنيّ-مجاناً» falsification, measured in the recon)

The driving rows ARE computed but **discarded on the live villa path**: `evaluate_property.py:1576` called `build_reference(rows, area, max_d)` **without `return_transactions=True`**, so the subject-bracket `bracket['transactions']` (moj_reference.py:206-217) were built then dropped. So «built-free» was false (no rows in the response), but surfacing them is **modest + value-invariant + privacy-safe** (the rows carry no PIN/address — E12 — and CC BY 4.0 public).

## 3. What this patch does

**Engine (additive, value-invariant — the median already drives the number):**
- `evaluate_property.py`: `MoJValuation += bracket_transactions` (mirrors the a13/a14 `bracket_ppm2_dispersion`/`bracket_window_used` channel); `build_reference(...return_transactions=True)` at :1576 (ADDITIVE — only adds `bracket['transactions']`; every aggregate output byte-identical); `apply_moj_strategy` captures the subject bracket's rows into `bracket_transactions`.
- `evaluate_unified.py`: a pure `_keystone_comparables(rows, n, window_used, cap=8)` builder (anonymizes to `{date, area_m2, total_price, price_per_m2}`, caps at 8, newest-first, never raises); `_select_primary_comparison` **Case 1** (`comparison_bracket`) stashes the rows on `primary['comparables']`; the **b4-region** attaches `valuation.comparables` **ONLY when `leader=='market'` AND `method=='comparison_bracket'`** — i.e. the displayed median IS the subject-bracket median. This **excludes** cost-led (number is DRC), income-led, geo-led (RULE 2 — deferred to UX1.1), thin/preliminary, **land** (its own `comparable_grid`; the gate is in the villa/house-only `if _gate:` block → land never reaches it), and refusals.

**Frontend (`index.html`, display-only → appends to `how`, value byte-identical):** a keystone panel inside the b31 «🔍 كيف وصلنا لهذا الرقم؟» accordion (**density-gated b34** — open for investor/valuer, one click for owner/buyer/seller): «🔑 {n} صفقة في شريحتك ومنطقتك — هي ما قرّر رقمك» + a `direction:ltr` table of `date · {size} م² · {total} ر.ق` (Rule #25) + a «عرض X من N (الأحدث)» disclosure + the CC BY 4.0 source line «بيانات وزارة العدل القطرية (CC BY 4.0) — مجموعة عامّة بلا عنوان أو ترقيم فرديّ». Placed right after the b20 «حوض المقارنات» dispersion line so the pool→rows story reads together.

**Privacy (E12):** the surfaced rows carry **no PIN / address / coordinates** — the source export strips the PN-hash; only date/size/price. CC BY 4.0 public (attribution already live since a25).

## 4. The leadership-aware gate (the recon's core decision)

The honest gate is **`leader=='market'` (b20) AND `method=='comparison_bracket'`** — not just the method string — so a cost-led villa (number = DRC) never shows «these N transactions decided your number». Geo-led (RULE 2) and cost-led's «considered-but-didn't-lead» pool are deferred (UX1.1 / #42).

## 5. Verification — empirical evidence

- py_compile OK; node absent → **R14 Chromium is the JS gate** (a8/a21 precedent).
- Isolated `test_sprint_2_22_0b38.py` **25/25** — incl. **value-invariance** (A2: `build_reference` aggregate outputs byte-identical with/without the flag; C4: `apply_moj_strategy` value identical) + **E12 anonymity** (A4/A5/B4/F1: row keys == `{date,area_m2,total_price,price_per_m2}`, no PIN/ref/address) + cap-at-8 + newest-first + the structural gates (Case-1-only stash, `leader=='market' && comparison_bracket` attach) + the index.html render (gated, dir=ltr, CC BY, lives in `how`).
- **R6 re-point:** `test_sprint_2_22_0b37.py` exact-version pins → version-agnostic format checks (the project's own «no exact version pins» rule) → **22/22**.
- DoD: aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface **45/45** · broad auto-walk **106/106 ALL GREEN** (105→106; siblings b31 36/36 · b34 15/15 · b35 17/17 · b36 22/22 green WITHOUT re-points).
- **Local E2E (live GIS):** **Abu Hamour 56/565/21** → 2,400,000 comparison_bracket · market · matched → **comparables PRESENT n=37 shown=8** (real anonymous rows); **Marikh 54/541/6** → 2,400,000 · **cost-led** → absent; **V001 56/647/6** → 3,800,000 · geo_full → absent; **Apt 52/903/90** → refusal → absent. **Value byte-identical to v208 on all 4.**
- **R14 real-Chromium 390×844** (the captured Abu Hamour payload, audience=investor): the keystone renders inside the OPEN «كيف وصلنا» accordion — 8 rows, first = `2025-12-17 · ٤٤٤ م² · ٢٬٣٠٠٬٠٠٠ ر.ق` (correct dir=ltr Arabic-Indic) + CC BY 4.0 source; headline **٢٬٤٠٠٬٠٠٠ unchanged**; **no overflow** (docScrollW 390 == clientW 390, block 35→355); **0 console errors**.

## 6. Deployment

```
git add evaluate_property.py evaluate_unified.py index.html test_sprint_2_22_0b38.py test_sprint_2_22_0b37.py CHANGELOG_v121.md
git commit -m "Sprint 2.22.0b.38 (DEF-UX1): keystone comparables ..."
git subtree push --prefix "deploy v2" heroku master      # Gate-1 — on explicit deploy go
git push origin master                                    # backup
```

## 7. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health           # → 3.1.0-sprint2.22.0b.38
# value byte-gate (browser-UA, Rule #61) + comparables presence on the matched anchor:
curl -s -A "Mozilla/5.0 ... Chrome/124 Safari/537.36" -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"   # 2.4M + valuation.comparables n=37
```

## 8. What's NOT in this patch (deferred — Rule #42)

- **Geo-led keystone** (RULE 2 — the `geo_v2` pool rows for widened/geo-full-led villas, e.g. V001) → **UX1.1**.
- **Cost-led «considered, did not lead» pool** (the dispersed market pool on a cost-led villa, e.g. Marikh) → a separate, more delicate copy slice.
- **Time-normalization** (the spec's «مُطبَّعة زمنياً») — b38 shows **raw rows + visible dates** (honest, no synthetic adjustment; the recon §7 recommendation).
- Bringing the land `comparable_grid` to the result screen (parity, out of scope).
- The «التقدير السوقي» term remains PROVISIONAL.
