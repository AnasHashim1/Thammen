# CHANGELOG v63 — Sprint 2.22.0a.11 — Residential-usage filter on the villa comparable pool (A1)

**Engine:** `thammen-sprint2p22p0a11-usage-filter` · **api/health:** `3.1.0-sprint2.22.0a.11`
**Date:** 2026-05-31 · **Type:** methodology (villa comparable-pool selection) — Gate 2, signed.
**Files changed:**
- `usage_filter.py` — **NEW** shared helper (`_RESIDENTIAL_USAGES` + `_is_residential_usage`).
- `moj_reference.py` — bracket-path villa selector: residential-usage filter (villa only).
- `geo_reference_v2.py` — geo_value/widened-path villa selector: residential-usage filter (villa only).
- `evaluate_unified.py` — `ENGINE_VERSION` / `SPRINT_TAG` → a11.
- `test_sprint_2p22p0a11_usage_filter.py` — **NEW** isolated test (13 cases).
- `CHANGELOG_v63.md` — this file.

---

## 1. Why this matters

The villa comparable pool was selected by `نوع العقار` (property TYPE) only, with **no filter on
`الاستخدام` (USAGE)**. As a result the pool carried non-residential-usage rows — `عمارات او مجمعات
سكنية` (apartment/complex), `تجاري`, `مزارع`, `مكاتب تجارية`, schools/mosques — **priced ≈ +101%
above the residential median** (801 vs 399 QAR/ft²). That contamination **inflated the villa median
≈ 5%** (Phase-1b / RISK_REGISTER **R8**), pushing comparison headlines up across the board.

## 2. Root cause

Two live villa selectors, **both type-only, neither usage-aware**:
- `moj_reference.build_reference` (villa loop, ~lines 75-83) → bracket headline (`fair_price_total`,
  via `evaluate_property.py:1504`).
- `geo_reference_v2._get_area_transactions` (line ~336) → geo_value headline (widened Cases 2 & 3).

Blank-usage rows (9.4 % of the pool) were measured to price **like residential** (419 vs 399, +5 %),
**not** like the +101 % contamination → they are KEPT.

## 3. What this patch does

New shared `usage_filter._is_residential_usage(row)` — a **WHITELIST** (robust to the ~40 spelling
variants of the usage labels), applied to the **VILLA pool only** (land untouched — out of A1 scope):
```python
_RESIDENTIAL_USAGES = {'فلل او بيوت سكنية', 'مسكن', 'مساكن كبار الموظفين'}
def _is_residential_usage(row) -> bool:
    u = re.sub(r'\s+', ' ', str(row.get('الاستخدام', '') or '')).strip()
    return u == '' or u in _RESIDENTIAL_USAGES        # KEEP blank + whitelist; exclude all else
```
- `moj_reference.build_reference`: villa comprehensions gain `and (cat != 'villa' or _is_residential_usage(r))`.
- `geo_reference_v2._get_area_transactions`: gains `if category == 'villa' and not _is_residential_usage(r): continue`.

**Out of scope (unchanged):** the TYPE categorizers (`categorize` / `_categorize`) — incl. the `مسكن`
type divergence (that is A2); land-usage filtering; `compute_trend`'s villa selection (trend chart, not
the headline median).

## 4. Verification — empirical evidence (local, read-only)

- **Isolated** `test_sprint_2p22p0a11_usage_filter.py`: **13/13** (whitelist keep, blank keep, NBSP-variant
  keep, apartment/truncated/commercial/farm/office exclude, missing-key keep).
- **DoD regression (PYTHONIOENCODING=utf-8):** aggregator **392/392** · security **15/15** ·
  surface-honesty **45/45** · broad **54/54 files** — all green.
- **Pooled villa-median delta (final filter, keep-blank + whitelist):** FULL **−4.75 %** (421→401 ft²),
  24mo **−5.20 %** (442→419 ft²).
- **Per-PIN — END-TO-END engine, before/after via filter toggle (authoritative):**
  - **54/541/6 Marikh:** **4,500,000 → 4,500,000 (0.00 %, unchanged)** — orthogonal (geo comp 703→703;
    its villa pool is all-residential-usage; R8 predicted this).
  - **56/565/21 Abu Hamour:** **2,500,000 → 2,400,000 (−4.00 %)** — DOWN, correct removal of a
    non-residential row inflating the Abu Hamour villa bracket; consistent with the −4.75 % pooled delta.
    **NOTE:** independent of R7 / §20.10.2's *condition* under-anchor (which points UP, ~2.5-2.8M via the
    future Gate-2 (c) stratification) — a11 fixes pool **contamination**, not condition. The two compose.
  - **52/903/90** apartment_building **None → None**; **69/255/75 / 69/329/20** hybrid (T2-T3) —
    villa-filter-orthogonal, unchanged.
  (A comp-pool proxy on `بو هامور` 400-600 understated this at −0.83 %; the end-to-end engine is authoritative — Rule #58.)
- **Mobile 390×844 / index.html:** no UI change — the filter alters which MoJ rows feed the median, not
  the output schema; the valuation card renders unchanged.

## 5. Deployment (Windows cmd — one command per line, subtree push per Operational #43)

```
cd /d "C:\Thammen\deploy v2"
git add usage_filter.py moj_reference.py geo_reference_v2.py evaluate_unified.py CHANGELOG_v63.md test_sprint_2p22p0a11_usage_filter.py
git commit -m "Sprint 2.22.0a.11: residential-usage filter on villa comparable pool (A1)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
(If the subtree push is rejected for divergence, use the split + force per Operational #43.)

## 6. Post-deploy verification (curl)

```
curl -s https://thammen.qa/api/health
:: expect "engine_version":"thammen-sprint2p22p0a11-usage-filter" + "version":"3.1.0-sprint2.22.0a.11"
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"
```
Smoke 3 diverse addresses from Heroku post-deploy (§5 / Rule #52) — incl. an apartment PIN to confirm the
villa-only filter left it untouched.

## 7. What's NOT in this patch

- **Land-usage filtering** — out of A1 scope (villa pool only). Candidate for a later sprint.
- **`مسكن` TYPE categorizer divergence** (geo_v2 counts `مسكن` as villa; bracket path calls it `dwelling`)
  — that is **A2**, a separate type-categorizer reconciliation.
- **`compute_trend` villa selection** (trend chart) — not the headline median; left unfiltered for now.
- **Window-widening (24→36→FULL) + dispersion pairing** (R8/E23) — separate Phase-2 brief.
