# PHASE-0 RECON — DEF-UX1.2 «إثراء الكَيستون» (cost-led considered pool + geo neighbour rows)

> Read-only recon. Engine UNCHANGED (live = b39 / Heroku v210, `master==origin @9a0f67c`). Method:
> 4-agent parallel read (workflow `wf_04e9db96-a45`) cross-verified against direct reads of the
> attach gate, `_keystone_comparables`, `_select_primary_comparison`, and `geo_reference_v2` Step 5.
> Continues the b38 (DEF-UX1, matched_bracket) → b39 (DEF-UX1.1, geo_widened primary) keystone series.
> The §20.70 "carried forward" deferral: «the cost-led «considered-but-didn't-lead» pool (Marikh) + the
> full geo pool (the location-adjusted neighbour rows with source-area + adjustment)».

## 0. The two slices (both 🟢 display-only / value-invariant by construction)

| Slice | What | Risk profile |
|---|---|---|
| **A — cost-led «considered»** | On a COST-LED villa (e.g. Marikh 54/541/6) surface the market rows that were *considered but did not lead the number* (the cost/DRC led), with an honest "why it didn't lead" disclosure. | display-only; the rows are already in scope at the attach site |
| **B — geo neighbours** | On a GEO-LED villa (e.g. V001 56/647/6) extend the b39 panel from primary-area-only to ALSO show the accepted **neighbour** rows with their source-area + location adjustment. | display-only (reconstruct from retained `accepted_areas`) |

Recommended sequencing (Rule #38 single-purpose): **b40 = Slice A first** (bigger gap — cost-led villas
today show NO comparables at all), **b41 = Slice B** (more delicate: adjusted-price framing + the 4-column
bidi layout + a fresh R14).

## 1. The attach gate today (`evaluate_unified.py:5123-5137`)

```
_kc_method = output['valuation'].get('method')
if (_gate['leader'] == 'market'
        and _kc_method in ('comparison_bracket','comparison_widened','comparison_widened_indicative')):
    _kc_basis = 'matched_bracket' if _kc_method=='comparison_bracket' else 'geo_widened'
    _kc = _keystone_comparables(primary.get('comparables'), n, window, basis=_kc_basis, pool_n=n)
    if _kc: output['valuation']['comparables'] = _kc
```

Fires ONLY for `leader=='market'`. Cost-led / income-led / e25_capped / cost_unavailable → skipped (correct
for b38/b39; the gap b40 closes).

## 2. Slice A — cost-led «considered» pool

### Available now (no engine change)
- **`geo_v2_result['primary']['transactions']`** — the subject's PRIMARY-AREA (same-district) rows,
  computed unconditionally (`evaluate_unified.py:4281`), **in scope at the attach site (5124)**. Row shape
  (`geo_reference_v2.py:368-376`): `{area, date, price_m2, price_ft, area_m2, total_price, type}`. ✅ the
  robust source for the considered panel — these are *real, unadjusted sales in the subject's own area* that
  the engine examined.
- **`value_stack.market` + `leadership`** carry the "why it didn't lead" scalars already broadcast:
  `geo_full_n` (≈51 for Marikh), `geo_full_dispersion` (≈0.620), threshold `LEAD_DISPERSION_T=0.30`,
  `cost_value`, `market_value`.

### Discarded (would need an additive channel — Option B)
- The **exact full geo-full pool rows** (the n=51 that produced dispersion 0.620 → RULE-2 fail).
  `moj_reference.subject_geo_full_ppm2` (`moj_reference.py:82-125`) keeps a bare `vals` ppm² float list →
  returns aggregates only (`ppm2_median_full, n_full, value_full, bracket, ppm2_p25_full, ppm2_p75_full,
  dispersion_full`). The rows behind n=51 are gone.

### Correction to the session's prior reading
- `primary['comparables']` is **ABSENT on the Marikh cost-led path** — Marikh's primary method is
  `comparison_thin` (Case 4, n=15), and Cases 4/5 do NOT stash `comparables` (only Case 1 / Cases 2-3 do).
  So Slice A must read **`geo_v2['primary']['transactions']` directly**, NOT `primary['comparables']`.
- ⚠️ **OPEN (build-time verify):** confirm `geo_v2['primary']['transactions']` is non-empty for a thin-bracket
  cost-led villa (امريخ الجنوبي has rows → expected yes; a local E2E on `.basket/f_marikh.json` confirms).

### Design options
- **A (recommended) — display-only:** new attach branch `elif _gate['leader'] in ('cost','e25_capped') and
  geo primary rows exist` → `_keystone_comparables(geo_primary_rows, n, window, basis='cost_considered',
  pool_n=geo_full_n)` → attach as a **NEW key `valuation.considered_comparables`** (NOT `comparables` — keep
  the b38/b39 «هي ما قرّر رقمك» renderer from firing). Shows the same-area real rows + discloses the full
  pool (n=51) failed reliability. Cheapest, privacy-clean, no engine touch.
- **B — engine-additive:** add `return_transactions` to `subject_geo_full_ppm2` (b38 pattern; additive, the 7
  existing keys byte-stable so the b16/b20 RULE-2 consumers are unaffected) → surface the exact n=51 pool
  (incl. cross-district neighbour rows). Matches the verdict's n exactly but needs a signed engine slice.

## 3. Slice B — geo neighbour rows

### Available now (retained in-engine, not in the response)
- **`geo_v2_result['accepted_areas'][i]`** (`geo_reference_v2.py:655-656`) — each accepted neighbour area:
  `name` (GIS area-name, E12-safe), `location_adjustment` (multiplier = primary_median/candidate_median),
  `adjustment_pct`, `distance_m`, `n`, `transactions` (raw rows `{area, date, price_m2, price_ft, area_m2,
  total_price, type}`). In scope at the attach site (geo_v2 is the same dict the gate already has).
- Per-row **adjusted ppm²** = `raw_price_m2 × location_adjustment` — DERIVED display-side (the engine's
  `all_adjusted_prices` that holds it natively is a Step-5 throwaway local, `geo_reference_v2.py:663-696`,
  discarded after the weighted median). Deriving it in the display builder, NOT re-running any median, keeps
  it strictly value-invariant.

### Builder
- `_keystone_comparables` strips to exactly 4 keys `{date, area_m2, total_price, price_per_m2}` → it CANNOT
  carry `source_area`/`adjustment_factor`. Slice B needs a **separate small `_keystone_neighbours(...)`
  builder** (or an optional passthrough) emitting `{date, area_m2, total_price, price_per_m2_raw,
  price_per_m2_adjusted, source_area, adjustment_factor}`. E12-safe: area NAME + a ratio; never PIN/coords.

### Frontend
- The keystone renders at `index.html:2352-2367` in the `how` buffer (b31 «كيف وصلنا» accordion, b34
  density-open), branching on `_kc.basis`. Slice B extends the geo branch with an expandable neighbour
  sub-table.
- ⚠️ **Rule #25 / overflow:** the current row is a 3-column `dir=ltr` flex (date | م² | ر.ق), R14 right-edge
  ~355<390 at 390×844. Adding an **Arabic area-name column** inside a dir=ltr row risks bidi reversal +
  overflow → the area name needs its own RTL island, possibly a stacked/2-line layout or smaller font, and a
  **fresh R14 390×844**.

## 4. Value-invariance + E12 (both slices)

- Headline fields (`amount/low/high/method/rule/leadership`) are all written BEFORE the keystone attach
  (cost-led branch writes amount/low/high at ~5042-5044; leadership at 5109). The attach only ADDS a sibling
  display key. `_keystone_comparables` does `rows = sorted(rows,...)` → a NEW list (no in-place mutation); the
  source lists are fresh-built exports the median/quartile code never reads back. → **value-invariant by
  construction**, mirroring the b38/b39 contract.
- **b40/b41 test** mirrors `test_sprint_2_22_0b38.py` C4 (amount/low/high/method/rule byte-identical with vs
  without the new block) + F1 (E12 anonymity: row keys carry no PIN/ref/address; for Slice B, `source_area` =
  area name only, `adjustment_factor` = ratio).

## 5. Gate-2 decisions for the PO

1. **Sequencing** — b40 (cost-led) then b41 (geo neighbours) [recommended], vs one bundled sprint, vs geo-first.
2. **Slice A source** — Option A (same-area primary rows, display-only, available now; the n=51/0.620 "why"
   disclosed from the already-broadcast scalars) [recommended] vs Option B (the exact n=51 pool, engine-additive).
3. **Cost-led copy (the delicate one)** — must NOT claim the rows decided the number. Proposed:
   - header: «🔍 صفقات السوق في منطقتك — اطّلعنا عليها ولم تقُد الرقم»
   - why-line: «الحوض الجغرافيّ فشل حدّ الموثوقيّة (تشتّت {disp} > 0.30، n={pool_n}) — قاد التقديرَ منهجُ
     الكلفة (DRC)».
   - rows: the existing dir=ltr `date · م² · ر.ق` table + the CC BY 4.0 source line.
4. **(b41) geo neighbour framing** — show source-area + ×adjustment, labelled «مُعدَّلة الموقع»; show BOTH the
   raw sale price AND the adjusted figure (never imply the neighbour sold for the adjusted number); decide
   whether the b39 «إجمالي {pool_n} صفقة» disclosure coexists with or is superseded by the table.

## 6. Out of scope / not changed
- The matched_bracket panel (b38) — keeps `basis='matched_bracket'`, no neighbours.
- The headline / leadership / value path — untouched.
- Income-led / thin-without-geo / land (own `comparable_grid`) / refusals — no considered panel.
- Time-normalisation of the displayed rows (the spec's «مُطبَّعة زمنياً») — deferred, as in b38/b39.
