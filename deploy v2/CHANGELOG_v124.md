# CHANGELOG v124 — Sprint 2.22.0b.41 «الكَيستون: صفوف الجيران الجغرافيّة» (DEF-UX1.1b)

> Engine `thammen-sprint2p22p0b41-keystone-geo-neighbours` / SPRINT_TAG `2.22.0b.41` /
> api-health `3.1.0-sprint2.22.0b.41`. **🟢 ENGINE-ADDITIVE / DISPLAY-ONLY / VALUE-INVARIANT**
> (`api.py` UNTOUCHED; amount/low/high/method/rule/leadership byte-identical). Files changed:
> `evaluate_unified.py` (new `_keystone_neighbours` + the geo-branch nested attach + version lines),
> `index.html` (the neighbour sub-table render), `test_sprint_2_22_0b41.py` (new). Date 2026-06-14.
> Recon `docs/PHASE0_DEF_UX1.2_keystone_enrichment_recon.md` §3 (Slice B). The b38 (matched_bracket)
> → b39 (geo primary) → b40 (cost-led considered) → **b41 (geo neighbours)** keystone series.

## 1. Why this matters

On a **geo-led** villa (e.g. V001 56/647/6) the headline median pools the subject's PRIMARY-area
rows (the b39 panel, weight 1.0) PLUS accepted-**neighbour** rows that are location-adjusted into the
subject's area. b39 surfaced only the primary subset + disclosed the pool SIZE («إجمالي {pool_n}
صفقة»). The neighbour rows that actually entered the pool — and the location adjustment applied to
each — were invisible. b41 surfaces them: each neighbour row with its source-area NAME + the ×adjustment
+ the location-adjusted ppm² — the §20.70 «full geo pool» deferral.

## 2. Root cause

`geo_v2_result['accepted_areas']` (retained in-engine, `geo_reference_v2.py:655-656`) carries each
accepted neighbour area `{name, location_adjustment, transactions, …}`, but nothing surfaced it to the
response. The engine's per-row location-adjusted ppm² lives only in `all_adjusted_prices`
(`geo_reference_v2.py:663-696`) — a Step-5 **throwaway local** discarded after the weighted median.

## 3. What this patch does

### Backend (`evaluate_unified.py`, additive)
- New pure **`_keystone_neighbours(accepted_areas, cap=8)`** — flattens the accepted-neighbour
  transactions, newest-first, capped; each row = `{date, area_m2, total_price, price_per_m2_raw,
  price_per_m2_adjusted, source_area, adjustment_factor}`.
  - **Adjusted ppm² is DERIVED in the builder** = `round(DISPLAYED raw × DISPLAYED factor)` (the
    rounded display raw × the 4-dp display factor) → the panel's arithmetic is **self-consistent** (a
    reader can verify `raw × ×factor = adjusted` — b14 display-coherence). It is purely illustrative of
    the location adjustment and **never feeds the value** → value-invariant by construction. The
    engine's own `all_adjusted_prices` is NOT read.
  - **E12-safe:** a row carries the source AREA NAME (a public GIS aggregate label) + a ratio only —
    never PIN / address / coords / the raw `area`/`type`/`price_ft` keys.
- **Attach (geo-only):** inside the b39 geo keystone branch, right after
  `output['valuation']['comparables'] = _kc`, when `_kc_basis == 'geo_widened'` build the neighbours
  from `geo_v2_result['accepted_areas']` and nest them as **`comparables.neighbours`** (NOT a 3rd
  top-level key). `None` when no accepted neighbours → exact b39 behaviour. matched_bracket (b38) has
  no neighbours; cost-led `considered_comparables` (b40) is untouched.

### Frontend (`index.html`, display-only → the `how` / «كيف وصلنا» accordion, b34 density-open)
- In the geo branch of the keystone render (`_kcGeo`), after the b39 pool disclosure, a neighbour
  sub-table when `_kc.neighbours` exists: header «الصفقات المجاورة المُعدَّلة الموقع (دخلت الحوض)» + per
  row a **2-line layout** — line 1 «📍 {source_area}» (RTL) with «×{factor}» (LTR island); line 2
  `{date} · {م²} · {raw} → {adjusted} ر.ق/م²` (`direction:ltr`, Rule #25 bidi-safe) — showing BOTH the
  raw sale ppm² and the DERIVED adjusted ppm² (rates, never a «sold-for» price) + «عرض X من N صفقة
  مجاورة» + the honest «السعر المعروض هو سعر البيع الفعليّ في منطقة الجار؛ ×التعديل يُحوّله إلى مستوى
  موقعك (لم تُبَع بالرقم المُعدَّل)» disclosure. The b39 «إجمالي {pool_n} صفقة» line coexists (summary →
  detail). Coexists with the bronze-border geo block; matched_bracket / cost-led blocks unchanged.

## 4. Verification — empirical evidence

- **Isolated `test_sprint_2_22_0b41.py` 30/30** (E14 — calls the production `_keystone_neighbours`):
  source_area + ×factor + the DERIVED adjusted (`round(raw×factor)`) + a <1 factor lowers adjusted +
  E12 row-keys + cap + graceful-None + no-input-mutation + **A12 self-consistency on a fractional ppm²**
  (the E2E-caught b14-class bug) + the b38 builder untouched (no `neighbours` bleed) + structural pins
  (geo-only attach, nested key, b39/b40 gates intact, the derive in the builder).
- **Siblings green WITHOUT re-points:** b38 25/25 · b39 19/19 · b40 18/18.
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **392 ALL COUNTS MATCH** · security
  `test_sprint_2p16p17_security.py` **15/15** · surface `test_sprint_2p22p0a3_surface_honesty.py`
  **45/45** · broad `2p22p0_pre/run_regression_2p22p0a.py` **109/109 ALL GREEN** (108→109, +b41).
- **Local E2E (live GIS, `.b41_e2e.py`) — value byte-identical to v211:** V001 56/647/6 →
  **comparison_widened 3,800,000, comparables basis=geo_widened n=34, neighbours PRESENT (areas_n=2,
  total_n=29, shown=8)**, derive-all=True (e.g. بو هامور ×0.9517 · 3871→3684, round(3871×0.9517)=3684),
  E12 clean (area name + ratio only) · Abu Hamour 56/565/21 matched 2,400,000 → comparables
  (matched_bracket), **neighbours absent** · Marikh 54/541/6 cost-led 2,400,000 → considered,
  **neighbours absent** · Maraad 55/296/13 2,600,000 / Apt 52/903/90 refusal → neither. Neighbours
  fire ONLY on the geo block (scope check passed).
- **R14 real-Chromium 390×844 (V001 geo payload, audience=investor):** the neighbour sub-table renders
  in the OPEN «كيف وصلنا» — header + 5 primary rows (b39) + «إجمالي 34 صفقة» + «📍 بو هامور ×0.9517» +
  «٣٬٨٧١ → ٣٬٦٨٤ ر.ق/م²» (arithmetic closes) + «📍 المعمورة 43 ×1» + the «لم تُبَع بالرقم المُعدَّل»
  disclosure + CC BY 4.0; **headline ٣٬١٠٠٬٠٠٠ – ٣٬٨٠٠٬٠٠٠ unchanged**; **no overflow** (docScrollW 390 ==
  clientW 390, panel right 355 < 390, neighbour rows ≤ 338); **0 console errors/warnings**. (screenshot
  timed out — the known §20.34 capture hiccup; DOM measurements are the evidence channel.)

## 5. Deployment

```
git add evaluate_unified.py index.html test_sprint_2_22_0b41.py CHANGELOG_v124.md
git commit -m "Sprint 2.22.0b.41 (DEF-UX1.1b): geo neighbour rows on the geo-led keystone"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health   ::  version 3.1.0-sprint2.22.0b.41
curl -s -A "Mozilla/5.0 ... Chrome/... Safari/537.36" -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":647,\"building\":6}"
  ::  valuation.amount == 3800000, comparables.basis == "geo_widened",
      comparables.neighbours.shown > 0   (V001 geo-led → neighbours present)
```

5-anchor value byte-gate must match v211: امريخ 2.4M cost-led (+considered) · أبو هامور 2.4M matched
(+comparables, no neighbours) · V001 3.8M geo (+comparables **+neighbours**) · المعراض 2.6M · شقق refusal.

## 7. What's NOT in this patch

- **Cost-led / matched_bracket neighbours** — only `geo_widened` gets neighbours (matched has none;
  cost-led keeps b40's `considered_comparables`, no neighbour rows — its full geo-pool rows are the
  deferred Option B). Single-purpose (Rule #38).
- The **exact cost-led n=51 geo-full pool rows** (recon §2 Option B, engine-additive) — deferred.
- **Time-normalisation** of the displayed rows (the spec's «مُطبَّعة زمنياً») — deferred, as b38/b39/b40.
- The headline / leadership / value path — **untouched**.
