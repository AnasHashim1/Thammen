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

---

## 3. Files modified / created in this Sprint (planned per BRIEF §2)

**New (3 connector modules + 1 cache + 1 test file):**

- `connectors/arady_apartments_t2_sales.py` (~250 lines)
- `connectors/propertyfinder_apartments_t2_sales.py` (~280 lines)
- `connectors/t2_listing_dedup.py` (~80 lines)
- `t2_listings_cache.sqlite` (24h TTL, created on first use)
- `tests/test_sprint_2p21p3_t2_connectors.py` (≥20 test functions per H6)

**Edited (3 files):**

- `evaluate_unified.py` — apartment_building branch + D10 trigger + ENGINE_VERSION bump
- `docs/Empirical_Findings.md` — Rule E3 stays at 8 constraints; new §reference noting active T2 sources for apartments
- This file (`CHANGELOG_v48.md`)

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

*To be filled at implementation start. One Lusail apartment listing per
source, document actual detail-page schema in*
`2p21p3_brief/connector_schema_audit.md`. *Stop and report if schema
differs materially from Pre-Sprint smoke expectations (CSS
`property-price`, regex `(?:QAR|AED)\s*[\d,]+`, regex
`(\d[\d,]*(?:\.\d+)?)\s*(?:sqm|m²|m2|sq\s*m)`).*

---

## 5. Connector implementation evidence

*To be filled per BRIEF §3.1–§3.3 after pre-impl audit completes.*

---

## 6. Engine integration diff

*To be filled per BRIEF §4 after connectors are stable.*

---

## 7. Test results (target: H6 ≥20 test functions, H5 27/27 regression preserved)

*To be filled after implementation.*

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
- §5 connector code (3 modules)
- §6 engine integration diff
- §7 test results (regression + new file)

Wait for Anas approval. No `git subtree push` until then (Rule #32 push
discipline + Rule #43 deploy mechanism).

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
