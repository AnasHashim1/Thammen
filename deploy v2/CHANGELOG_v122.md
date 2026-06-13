# CHANGELOG v122 — Sprint 2.22.0b.39 «الكَيستون الجغرافيّ» (DEF-UX1.1)

**Engine:** `thammen-sprint2p22p0b39-keystone-geo` · **SPRINT_TAG** `2.22.0b.39` · **Date:** 2026-06-13
**Files:** `evaluate_unified.py` · `index.html` · `test_sprint_2_22_0b39.py` (new) · `test_sprint_2_22_0b38.py` (R6 re-point)
**Class:** 🟢 engine-additive **display-only / VALUE-INVARIANT** · Gate-2 SIGNED BY DELEGATION («افعل الأصوب ولنكمل») · Gate-1 = explicit deploy go.

## 1. Why this matters

b38 shipped the keystone for **matched-bracket** villas (the subject's size-bracket rows that produced the median). The **geo-led market villas** (`comparison_widened` / `_widened_indicative`, e.g. V001) still showed no comparable rows — the highest-value §4ب feature was half-covered. b39 extends the keystone to the geo path, the carried-forward UX1.1 deferral from b38.

## 2. What this patch does

**Engine (additive, value-invariant — `evaluate_unified.py`):**
- `_keystone_comparables(rows, n, window_used, cap=8, basis='matched_bracket', pool_n=None)` — extended: a `basis` tag, a `pool_n` (the full geo-pool size for the disclosure), a **`price_m2` fallback** (the geo `_get_area_transactions` rows key ppm² as `price_m2`, the bracket rows as `price_per_m2`), and a **newest-first sort** (the bracket path is pre-sorted; the geo pool is row-order — the sort is idempotent on sorted input).
- `_select_primary_comparison` **Cases 2 & 3** (`comparison_widened` / `_widened_indicative`) stash `'comparables': (geo_v2.get('primary') or {}).get('transactions')` — the subject's **PRIMARY-area raw transactions** within the geo-widened pool (real, unadjusted, same-area).
- The **b4-region** attach gate broadened: `leader=='market' AND method in (comparison_bracket, comparison_widened, comparison_widened_indicative)`; `basis` derived from the method (`matched_bracket` vs `geo_widened`), `pool_n` passed. Still excludes cost-led / income-led / thin / preliminary / land / refusal.

**The honesty design (the core decision).** The geo-led value is a weighted median of **primary (unadjusted, weight 1.0) + accepted-neighbour (location-adjusted) transactions** (geo_reference_v2.py:663-696). The panel surfaces **only the primary-area RAW rows** (every shown number is a real, unadjusted, same-area transaction — no synthetic figures) and the frontend **discloses** that the full pool also pooled location-adjusted neighbour rows. The geo header is «🔑 صفقات في منطقتك ضمن حوض المقارنة الموسَّع جغرافياً» (NOT the bracket «هي ما قرّر رقمك» — the geo case never overclaims that these alone decided the number).

**Frontend (`index.html`, display-only → appends to `how`):** a per-basis branch — `matched_bracket` keeps the b38 header + «عرض X من N»; `geo_widened` shows the geo header + the disclosure «وُسِّع الحوض لمناطق مجاورة (مُعدَّلة الموقع في الحساب) لاكتمال العيّنة — إجمالي {pool_n} صفقة». Same `date · م² · ر.ق` dir=ltr table + CC BY 4.0 source.

**Privacy (E12):** the geo rows carry no PIN/address/coords — only date/size/price (the export strips the PN-hash). CC BY 4.0 public.

## 3. Verification — empirical evidence

- py_compile OK; node absent → R14 Chromium is the JS gate.
- Isolated `test_sprint_2_22_0b39.py` **19/19** (E14: the geo `price_m2` fallback + pool_n + basis + the newest-first sort + E12 anonymity + value-invariance [no headline keys] + the b38 matched_bracket default unchanged + the structural geo stash + the broadened market-led gate + the index.html per-basis render/disclosure).
- **R6 re-point:** `test_sprint_2_22_0b38.py` (D2 gate now a method-set, D3 comparables now in Cases 1-3 not just Case 1, E3 window) → **25/25**.
- DoD aggregator **392 ALL COUNTS MATCH** · security **15/15** · surface **45/45** · broad auto-walk **107/107 ALL GREEN** (106→107).
- **Local E2E (live GIS):** Abu Hamour 56/565/21 → **basis=matched_bracket** n=37 (b38 unchanged); **V001 56/647/6 → basis=geo_widened, 5 primary rows, pool_n=34** (ppm² from the price_m2 fallback); Marikh 54/541/6 cost-led → absent; apt 52/903/90 refusal → absent. **Value byte-identical** (2.4M/3.8M/2.4M/None).
- **R14 real-Chromium 390×844** (captured V001 geo payload, audience=investor): the geo keystone in the OPEN «كيف وصلنا» — geo header + the widening disclosure + «إجمالي 34 صفقة» + first row `2025-06-15 · ٦٤٠ م² · ٣٬٣٥٠٬٠٠٠ ر.ق` (newest-first, dir=ltr) + CC BY 4.0; **no bracket-style overclaim**; headline **٣٬٨٠٠٬٠٠٠ unchanged**; no overflow (35→355 within 390); **0 console errors**.

## 4. Deployment

```
git add evaluate_unified.py index.html test_sprint_2_22_0b39.py test_sprint_2_22_0b38.py CHANGELOG_v122.md
git commit -m "Sprint 2.22.0b.39 (DEF-UX1.1): geo-led keystone ..."
git subtree push --prefix "deploy v2" heroku master      # Gate-1 — on explicit deploy go
git push origin master                                    # backup
```

## 5. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health           # → 3.1.0-sprint2.22.0b.39
# V001 geo keystone + value byte-gate (browser-UA, Rule #61):
curl -s -A "Mozilla/5.0 ... Chrome/124 Safari/537.36" -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":647,\"building\":6}"   # 3.8M + comparables.basis=geo_widened
```

## 6. What's NOT in this patch (deferred — Rule #42)

- **The full geo pool** (primary + the location-adjusted neighbour rows) — b39 shows the primary-area subset + discloses the widening; surfacing the neighbour rows with their source-area + adjustment is a richer slice.
- **The cost-led «considered-but-didn't-lead» pool** (the dispersed market pool on a cost-led villa, e.g. Marikh) — a more delicate copy slice.
- Time-normalization (raw rows + visible dates retained) · bringing the land `comparable_grid` to the result screen. The «التقدير السوقي» term remains PROVISIONAL.
