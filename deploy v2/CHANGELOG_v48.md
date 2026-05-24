# CHANGELOG v48 — Sprint 2.21.3 — T2 Sales Connectors for Apartments (Lusail)

**Engine version (post-deploy, target):** `thammen-sprint2p21p3-t2-apartments-lusail`
**Heroku release target:** TBD (pending Anas review per BRIEF §9 step 8)
**Date opened:** 2026-05-24
**BRIEF reference:** [`BRIEF_2p21p3`](../BRIEF_2p21p3.md) — Anas-signed for D1–D12 (defaults).
**Production baseline at entry:** Heroku v109 code = engine
`thammen-sprint2p21p2-hybrid-foundation` (v107 code, Sprint 2.21.2 Hybrid
Foundation; v108→v109 was Pre-Sprint 2.21.3 smoke deploy + cleanup).
**Pre-Sprint inputs:** [`2p21p3_pre/CHANGELOG_pre_2p21p3.md`](2p21p3_pre/CHANGELOG_pre_2p21p3.md)
(4 of 5 TRUE — arady `/listings` canonical search URL discovered;
PropertyFinder DOM duplicates ~6× → connector MUST deduplicate).

---

## Slot-numbering check (per Rule #39 + Rule #53 precedent)

BRIEF §9 step 1 says "`CHANGELOG_v48.md` (or next available slot — document
drift)". v48 **is** the natural next sequential slot (v47 = Sprint 2.21.2,
Empirical Findings expansion + `hybrid_valuation.py` foundation). **No
drift.** This single line satisfies the BRIEF's drift-documentation clause.

---

## Scope-narrowing vs BRIEF_2p21p2 §8 — documented per BRIEF §0.1

BRIEF_2p21p2 §8 specified Sprint 2.21.3 as
`arady_apartments_t2.py + propertyfinder_rents_t2.py`. This Sprint narrows
to **SALES only**; rents become Sprint 2.21.3.1 per D12. Four reasons in
BRIEF_2p21p3 §0.1 (Pre-Sprint smoke didn't separate sale/rent; cap rate
cross-check is enhancement, not MVP; single-purpose Rule #38; first
live-path coupling deserves minimal blast radius).

---

## Decision register (D1–D12, all Anas-signed per BRIEF §1 defaults)

| # | Decision | Value |
|---|---|---|
| **D1** | Sprint number | `2.21.3` |
| **D2** | Asset-type scope | `apartment_building` only (`BUILDING_NO_SUBTYPE = 6`). Tower/compound/commercial deferred. |
| **D3** | Geographic scope | **Lusail only**. PF location code `l=63` + classifier district filter; Pearl/West Bay/Doha deferred to `2.21.3.geo-expand`. |
| **D4** | Caching | 24-hour TTL SQLite (`t2_listings_cache.sqlite`, pattern from `building_age_cache.sqlite`). |
| **D5** | Rate-limit per source | 1 req/sec, max 3 pages per Lusail query, exponential backoff on HTTP 429/503. |
| **D6** | Network failure handling | Source unreachable → skip that source's T2 inputs (do NOT fail whole evaluation), reduce confidence proportionally, log to telemetry. |
| **D7** | HTML brittleness | Parser logs to `t2_parser_errors.log`, returns `[]` on parse failure, never crashes the request. |
| **D8** | Currency normalization | PF Qatar should always be QAR. If AED token detected, log warning + skip that listing (likely UAE leak). No automatic FX conversion. |
| **D9** | Deduplication | Stage 1 by `(source, listing_id)` from canonical URL; Stage 2 by `(price_bucket=round/10K, area_bucket=round/5, district)`. Critical per Pre-Sprint DOM ~6× finding. |
| **D10** | Engine integration trigger | Call hybrid ONLY when: `asset_type == 'apartment_building'` AND `district == 'Lusail'` AND `rental_income is None` AND `unit_count is None`. Other paths unchanged. |
| **D11** | Feature flag / rollback | Env var `HYBRID_APARTMENTS_ENABLED` (default `true` on deploy). If `false`, engine falls back to pre-2.21.3 behaviour (`insufficient_data`). Emergency rollback without code revert. |
| **D12** | Rents Sprint placement | Rents become **Sprint 2.21.3.1** (sub-Sprint after 2.21.3 stable on Heroku ≥48h). 2.21.4 stays as T3 schema. |

### D5 / D6 calibration note (delegated to BRIEF, not re-debated here)

`HYBRID_TIER_CONFIG.T2_discount_midpoint = −0.125` (Sprint 2.21.2). Sprint
2.21.3 connectors emit raw asking values; the discount is applied inside
`hybrid_valuation_v1()`, not at the connector layer (BRIEF §3.1 behavior
contract). **No change to D5/D6 numbers in this Sprint.**

**Recalibration timeline correction vs BRIEF §0.1:** the BRIEF reads
"secretary data may never arrive". The accurate state as of 2026-05-24 is
stronger — the company supplying that data is **shutting down**, so the
secretary source is **permanently closed**, not delayed. D5/D6
recalibration depends entirely on the brokerage Confirmed Sales pipeline
(Sprint 2.16.16, redefined). Estimated timeline ~6-18 months for ≥30
Lusail apartment closings depending on brokerage transaction velocity.
**Not a blocker for Sprint 2.21.3** — the hybrid framework was designed
specifically for this calibration-deficit scenario (Rule E3 Constraint 5
mandatory MUC when T1 absent + Constraint 4 indicative ceiling).

---

## 2. Pre-Sprint §5 audit results

(Pre-Sprint 2.21.3 smoke = [`2p21p3_pre/CHANGELOG_pre_2p21p3.md`](2p21p3_pre/CHANGELOG_pre_2p21p3.md);
4 of 5 TRUE. Summary embedded here so this CHANGELOG is self-contained.)

| Probe | Outcome | Implication |
|---|---|---|
| H1 PF reachable from Heroku | ✅ TRUE | No proxy/WAF mitigation needed |
| H2 PF Lusail ≥30 unique on page 1 | ❌ FALSE (24/page) | Paginate 3 pages per D5 → ~72 unique max |
| H3 arady URL pattern discovered | ✅ TRUE | `/listings` canonical search (HTTP 200, 70 hits page 1; `/sitemap.xml` available) |
| H4 Heroku ↔ sandbox parity | ✅ TRUE | Δ=0 raw matches; sandbox numbers transfer to prod |
| H5 PF detail extractable schema | ✅ TRUE | CSS class `property-price` + regex fallbacks |

**Two findings that shaped this Sprint's design:**

1. **DOM duplication ~6× in PropertyFinder** — raw 142 matches → 24 unique
   per page. D9 dedup is mandatory; naive count would inflate `n` and
   poison the median.
2. **arady `/sitemap.xml` available** — parse FIRST as URL inventory before
   building pagination logic. Saves discovery work in connector §3.1.

**No fresh §5 probes needed before implementation starts.** The smoke
results ARE the audit. Step 2 (pre-implementation audit per BRIEF §9) is
narrower: confirm detail-page schema for one Lusail listing per source.

### 2.1 Step 2 pre-implementation audit results (2 rounds)

Detailed evidence: [`2p21p3_brief/connector_schema_audit.md`](2p21p3_brief/connector_schema_audit.md).
Heroku probe cycle: v110 (probe v1) → v111 (cleanup) → v112 (probe v2) → v113 (cleanup).

| Round | Prediction | Outcome | Implication |
|---|---|:---:|---|
| 1 S1 | arady sales URL identified | ✅ TRUE | `/listings` SALE-shaped (sale=195 rent=1) |
| 1 S2 | PF SALES c/t identified | ❌ FALSE | query-style c=1/c=3 returned 404; only RENT (c=2&t=1) reachable |
| 1 S3 | arady detail extractable | ❌ FALSE | finder matched a category page, not a listing |
| 1 S4 | PF detail extractable | ✅ TRUE | Next.js SSR, but AED tokens confused price heuristic |
| 1 S5 | Neither JS-rendered | ✅ TRUE (provisional) | refined in round 2 |
| 2 V1 | arady sitemap = inventory | ❌ FALSE | only 5 category URLs; **no individual-listing inventory** |
| 2 V2 | **PF path-style SALE URL** | ✅ **TRUE** | `/en/buy/lusail/apartments-for-sale.html` works: 16 big_prices, max 7.17M QAR |
| 2 V3 | arady REAL detail extractable | ❌ FALSE | `/listings/apartments` returns scaffolding HTML only; **listing content is Next.js JS-hydrated** |
| 2 V4 | PF SALE detail extractable | ⚠️ partial | title shows "Sale in …" but plain QAR tokens absent; **real price lives in JSON-LD `<script id="plp-schema">`** |

**Net result of audit:** PF SALES is fully viable (path-style URL + JSON-LD
detail). arady SALES detail extraction is blocked without JS-rendering
support, and arady's sitemap.xml does not publish individual-listing URLs.

### 2.2 Scope shrink per BRIEF §12 contingency (Rule #39 deviation)

**Decision (Anas-approved 2026-05-24):** Sprint 2.21.3 shrinks to
**PropertyFinder-only**, exactly the contingency BRIEF §12 anticipated.

**Why this is necessary** (Rule #39 step 1):
arady detail pages on `/listings/apartments` return Next.js SSR scaffolding
but the listing content (price, area, individual listings) is JS-hydrated
from `__NEXT_DATA__` (probe v2 V3 evidence). Extracting it without JS
execution requires either: (a) parsing the `__NEXT_DATA__` JSON blob (one
more probe round, not yet done), or (b) headless browser support
(Playwright/Selenium — out of scope per BRIEF). Neither is in scope here.

**What's lost by deferring arady** (Rule #39 step 2):
Pre-Sprint smoke counted ~70 listing-pattern hits on `/listings`; if those
expand to ~30-50 unique apartments-for-sale, dual-source `n` would have
been ~80-100 per Lusail query, vs PF-only ~48 (16/page × 3 pages D5).
Single-source loses ~40-50% potential T2 evidence and removes cross-source
dedup as a robustness signal. Hybrid framework can still hit Rule E3
indicative tier (n≥10) easily with PF alone.

**What the user / future Sprint needs to know** (Rule #39 step 3):
- Sprint output will display `sources=[{tier: T2, source: propertyfinder, n}]`
  with no arady row. The tier_breakdown is single-row T2 — Rule E10
  source-level transparency still satisfied.
- arady is **deferred, not abandoned**. Two clean revival paths:
  1. **Sprint 2.21.3.2** — `__NEXT_DATA__` JSON-blob parsing probe + arady
     connector. Adds dual-source robustness without JS execution.
  2. **Future Sprint** — headless-browser infrastructure for any JS-hydrated
     source (cost: new dependency, slower per-request, dyno memory).
- Revival conditions for arady integration: either path above succeeds
  with `n ≥ 5` Lusail apartments-for-sale extractable + price/area in
  >80% of sampled listings. Without that, arady stays deferred.

### 2.3 D9 dedup recalibration for single-source

BRIEF §3.3 specified a two-stage dedup: (1) intra-source `(source, listing_id)`,
(2) cross-source `(price_bucket, area_bucket, district)`. With PF-only,
stage 2 is N/A. Stage 1 stays mandatory (PF DOM duplicates ~6× per
Pre-Sprint smoke H2 finding). The separate `t2_listing_dedup.py` module
is dropped; intra-source dedup folds into the PF connector as a small
helper.

---

## 3. Files modified / created in this Sprint (post scope-shrink)

**New (1 connector module + 1 cache + 1 test file):**

- `connectors/propertyfinder_apartments_t2_sales.py` (~320 lines —
  network + parser + JSON-LD detail extraction + intra-source dedup helper)
- `t2_listings_cache.sqlite` (24h TTL, created on first use, pattern from
  `building_age_cache.sqlite`)
- `tests/test_sprint_2p21p3_t2_connectors.py` (~15-18 test functions
  covering H6 axes adjusted for single-source: list-page parsing, JSON-LD
  detail parsing, dedup correctness, cache hit/miss, network failure D6,
  parse failure D7, AED skip D8, engine routing D10 positive + 4 negative)

**Edited (3 files):**

- `evaluate_unified.py` — apartment_building branch + D10 trigger + ENGINE_VERSION bump.
  No `ThreadPoolExecutor(max_workers=2)` fan-out needed (single source).
- `docs/Empirical_Findings.md` — Rule E3 stays at 8 constraints; new
  §reference noting PropertyFinder as the active T2 source for apartments
- This file (`CHANGELOG_v48.md`)

**Deferred from BRIEF §2** (per §2.2 scope shrink):

- `connectors/arady_apartments_t2_sales.py` — deferred to Sprint 2.21.3.2
  candidate (requires `__NEXT_DATA__` parsing probe success first)
- `connectors/t2_listing_dedup.py` — dropped (cross-source dedup N/A with
  single source; intra-source helper folds into PF connector)

**Env var:** `HYBRID_APARTMENTS_ENABLED` (default `true` after first
successful deploy; D11 emergency switch).

**Not changed:**
- `hybrid_valuation.py` (function signature stable since 2.21.2)
- `HYBRID_TIER_CONFIG` (D5 / D6 midpoints unchanged)
- Brief template / UI (deferred to 2.21.5)
- Cap rate calibration (deferred to 2.21.3.1)
- Non-apartment asset types, non-Lusail geography

---

## 4. Pre-implementation audit (BRIEF §9 step 2) — schema confirmation

Filed in [`2p21p3_brief/connector_schema_audit.md`](2p21p3_brief/connector_schema_audit.md)
(2 rounds, 239 lines). Summary table is in §2.1 above; the audit drove the
scope-shrink decision in §2.2. Cleanup discipline: probe files removed
from slug at v111 + v113 per Rule #34 (no probe code in production slug).

---

## 5. Connector implementation evidence

| File | LOC | Purpose |
|---|---:|---|
| `t2_listings_cache.py` | 147 | SQLite cache with 24h TTL (D4); threading.Lock + closing() context per building_age_cache.py pattern |
| `connectors/__init__.py` | 0 | Package marker |
| `connectors/propertyfinder_apartments_t2_sales.py` | 425 | Public `get_apartment_sales_lusail(size_bracket, use_cache)`; path-style URL `/en/buy/lusail/apartments-for-sale.html` + ?page=N (D5: max 3 pages, 1 req/sec); JSON-LD detail parser (schema.org RealEstateListing in `<script id="plp-schema">`); intra-source dedup by listing_id (D9); AED skip (D8); sub-Lusail filter; D6/D7 error containment |

**Key design choices** (Rule #39 deviation justifications):

- **No `ThreadPoolExecutor` fan-out.** BRIEF §7 referenced E19 max_workers=2 for arady+PF parallel. Single-source removes this — sequential fetches keep code simple + politeness-friendly to PF.
- **JSON-LD parser is the canonical price source**, not plain QAR regex. The audit (V4) showed plain text price tokens on PF detail pages are dominated by AED service fees; the *actual* sale price lives in the embedded `<script type="application/ld+json">`. Plain-text regex fallback was considered and rejected — it would silently produce wrong numbers.
- **Sales-band sanity floor 100K QAR** on `_price_qar_from_entity()`. Rejects rent or service charges that leak into the offers block. Constraint 7 of Rule E3 is enforced at the connector boundary in addition to hybrid_valuation_v1's own validation.
- **Sub-Lusail filter** at the listing level (not just URL). `/en/buy/lusail/` returns Lusail-adjacent areas too (probe V4 sampled a Pearl/Porto-Arabia listing); we enforce strict Lusail by checking `address.addressLocality` and body markers.

---

## 6. Engine integration diff

`evaluate_unified.py`: **+178 / -2 lines** (one file changed). Concentrated in two regions:

- **Line 44-45** — `ENGINE_VERSION` bump + `SPRINT_TAG` from `2.21.2` → `2.21.3` (Rule #50 staged-Sprint discipline — version reflects most recent shipped Sprint).
- **Line ~1700** — New helpers (~210 lines total):
  - `_t2_sample_band(n)` — maps n to `'boundary'` (5-9) / `'indicative'` (10-19) / `'strong_indicative'` (≥20) per Project_Instructions §3 sample-size discipline.
  - `_t2_band_copy(band, n, muc_range_pct)` — returns per-band wording (banner, disclaimer, level, accuracy.score, accuracy.label). **muc_range_pct stays 0.20 across all bands** (Rule E3 §5 hard constraint) and confidence stays `'indicative'` (Rule E3 §4 ceiling) — only user-facing wording + accuracy score vary so brokers can distinguish n=7 from n=27 at a glance. (Added in response to Anas review gate question — see §11 below.)
  - `_try_hybrid_apartments_response(...)` — D11 env-flag gate, D10 Lusail district check, connector call, hybrid_valuation_v1 call, response builder that starts from `_build_fast_insufficient_data_response` shell and overlays `valuation` (with `value_per_m2`), `hybrid` block (case/confidence/`sample_size_band`/`n_used`/tier_breakdown/MUC), `sources` (Rule E10), `accuracy`, `reconciliation`, and a band-adaptive `material_uncertainty`. Module-level constant `HYBRID_T2_MIN_N = 5` defines the minimum sample to fire (below → fall through to insufficient_data — more honest than indicative-with-n=2).
- **Line ~2830** — Existing `else:` branch inside the DCF_ONLY apartment path. New 12-line `if _qtype == 'apartment_building'` clause attempts the hybrid path BEFORE the existing `_build_fast_insufficient_data_response`. On hybrid miss (None) it falls through cleanly to the pre-2.21.3 path — zero regression risk by construction.

**Critical: behaviour is identical to v101 when:**
- `HYBRID_APARTMENTS_ENABLED=false` (D11 emergency rollback)
- District ≠ Lusail (D10 gate)
- Connector returns < 5 listings (HYBRID_T2_MIN_N floor)
- Any connector / hybrid_valuation_v1 exception (defensive — caught and downgraded to None)

This satisfies H5 (no regression) by construction; the regression run in §7 confirms empirically.

---

## 7. Test results (H5 + H6 verification)

**Sprint 2.21.3 isolated tests** ([`tests/test_sprint_2p21p3_t2_connectors.py`](tests/test_sprint_2p21p3_t2_connectors.py)): **26 functions / 26 PASS**.

H6 axes covered:

| Axis | Tests |
|---|---|
| Connector network success | test_01, test_16 |
| Connector network failure (D6) | test_02, test_03, test_17 |
| Parse failure (D7) | test_07, test_08 |
| Dedup correctness intra-source (D9) | test_04 |
| Cache hit/miss + TTL (D4) | test_18, test_19 |
| AED skip (D8) | test_10 |
| Engine routing under D10 (positive + 3 negatives) | test_20-test_23 |
| Schema parse + extraction primitives | test_05-test_15 |
| Sample-size band adaptation (boundary/indicative/strong) | test_24, test_25, test_26 |

Engine integration uses real `_try_hybrid_apartments_response` import (Rule #40 — production verification, not replica).

**Regression — 27 existing + 1 new = 28 files**: **28 PASS / 0 FAIL** in 56s wall.

```
PASS test_building_age_cache.py
PASS test_imagery_flag.py
PASS test_market_regime.py
PASS test_material_uncertainty.py
PASS test_scope_of_service.py
PASS test_sprint_2p16p10_tower_split.py
PASS test_sprint_2p16p11_tower_sanity.py
PASS test_sprint_2p16p12_b1_b3.py
PASS test_sprint_2p16p14_zoning_mismatch.py
PASS test_sprint_2p16p15_extra_forbid.py
PASS test_sprint_2p16p7_validators.py
PASS test_sprint_2p16p8_muc_enrichment.py
PASS test_stock_strata.py
PASS tests/test_cap_rate_calibrator.py
PASS tests/test_evaluate.py
PASS tests/test_factors.py
PASS tests/test_moj.py
PASS tests/test_sprint_2p18p0_parallel_factors.py
PASS tests/test_sprint_2p18p1_parallel_bfs.py
PASS tests/test_sprint_2p18p1p1_compound_misroute.py
PASS tests/test_sprint_2p19p1_polish.py
PASS tests/test_sprint_2p20_grid.py
PASS tests/test_sprint_2p21_pin_lands.py
PASS tests/test_sprint_2p21p0p5_land_polish.py
PASS tests/test_sprint_2p21p0p7_reality_check.py
PASS tests/test_sprint_2p21p0p9_multi_qars_stage1.py
PASS tests/test_sprint_2p21p2_hybrid_foundation.py
PASS tests/test_sprint_2p21p3_t2_connectors.py
Total: 28, PASS: 28, FAIL: 0
```

**H5 ✓ verified pre-deploy.** Sprint 2.21.2 baseline preserved across all 27 existing standalone test files.

---

## 8. Predicted post-deploy behavior (BRIEF §6 falsifiable hypotheses)

H1–H10 per BRIEF §6. The most consequential predictions are:

- **H1** Lusail apartment (e.g. `52/903/90` proxy) returns `value_per_m2 ≠ None` with `confidence=indicative` and MUC active → core Sprint value delivered.
- **H5** All 27 existing test files still pass (regression).
- **H8** Setting `HYBRID_APARTMENTS_ENABLED=false` on Heroku restores pre-2.21.3 behavior immediately (no redeploy) → rollback path verified.

**Failure protocol (BRIEF §9 step 11):** If H1 OR H5 fail post-deploy,
immediately set `HYBRID_APARTMENTS_ENABLED=false` on Heroku (no redeploy
needed per H8). Report to Anas. Do NOT auto-rollback the code — keep the
deployment, just disable the feature.

---

## 9. Anas review gate (BRIEF §9 step 8) — Plan B per 2.21.2 precedent

Before commit + push, show:
- §4 pre-implementation audit results
- §5 connector code (1 module post-scope-shrink + 1 cache)
- §6 engine integration diff (incl. §11 band-adaptation amendment)
- §7 test results (regression + new file)

Wait for Anas approval. No `git subtree push` until then (Rule #32 push
discipline + Rule #43 deploy mechanism).

---

## 11. Anas review gate — amendment (2026-05-24)

Anas question during review: *"In `_try_hybrid_apartments_response`, does the
MUC text adapt to the n band (boundary 5–9 vs indicative 10–19 vs reliable
≥20)? Or is it a fixed clause regardless of sample size?"*

**Honest answer recorded at review time:** the initial implementation
emitted a fixed clause; only the literal `n=<count>` substituted into the
banner — every other field (banner wording, level, accuracy score/label,
disclaimer) was hardcoded. A broker would see the same UX for n=5 and
n=50 except for the number.

**Amendment shipped in this Sprint (chosen Option A):**
- Added `_t2_sample_band(n)` and `_t2_band_copy(band, n, muc_range_pct)`
  helpers (per §6 entry above) — 3 bands matching Project_Instructions §3
  discipline.
- `_try_hybrid_apartments_response` now branches `banner_ar`,
  `methodology_disclaimer_ar`, `material_uncertainty.level`,
  `accuracy.score`, `accuracy.label`, and `reconciliation.message_ar` per
  band, and adds two new response fields for transparency:
  `hybrid.sample_size_band` and `hybrid.n_used`.
- **What does NOT vary across bands:**
  - `confidence` stays `'indicative'` — Rule E3 §4 ceiling without T1.
  - `muc_range_pct` stays `0.20` — Rule E3 §5 mandatory ±20% without T1.
  - Both are hard constraints; band adaptation is wording + accuracy only.
- Added test_24/test_25/test_26 in the test file (boundary / indicative /
  strong_indicative). Test count: 23 → **26 PASS**.

This is a Rule #39-style deviation from the initial implementation
(documented here instead of suppressed). The methodology gap (uniform UX
across very different sample sizes) is closed before deploy rather than
deferred to a follow-up Sprint.

---

## 10. Rules cited / applied in this Sprint

- **Rule #32** push & commit discipline — wait for Anas approval before deploy
- **Rule #34** file-based scripts (smoke + probes as standalone files)
- **Rule #38** single-purpose Sprint scope (T2 SALES only; rents/T3/UI deferred)
- **Rule #39** deviation justification (D5/D6 calibration timeline correction; secretary closure permanent not uncertain)
- **Rule #43** Heroku deploy via `git subtree push --prefix "deploy v2"`
- **Rule #50** staged-Sprint discipline (Stage 1 = ≤5s indicative apartments; Stage 2 = cap rate cross-check deferred to 2.21.3.1)
- **Rule #51** audit-driven Sprint pattern — Pre-Sprint smoke fed BRIEF, post-deploy H1–H10 verifies predictions
- **Rule #52** latency unmasks methodology — first-time live evaluations for Lusail apartments may surface latent issues; visual verification required
- **Rule #53** closed cases stay closed — Pre-Sprint 2.22.0 (3-stage UX deferral) referenced via §X / Rule, not re-litigated
- **Rule E3** (8 constraints, Sprint 2.21.2) — tier-weighted entry permitted; indicative ceiling without T1; mandatory MUC
- **Rule E19** I/O-bound parallelization — arady + PF can fan out via `ThreadPoolExecutor(max_workers=2)` per BRIEF §7 hand-off note 4

---

*Opened 2026-05-24 evening, post BRIEF_2p21p3 sign-off. Will be updated
as the Sprint progresses through BRIEF §9 steps 2–11. Format mirrors
v47 (Sprint 2.21.2 Hybrid Foundation).*
