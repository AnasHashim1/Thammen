# Pre-Sprint 2.21.4 — T3 Schema (developer_inventory) — READY FOR BRIEF

**Date opened:** 2026-05-25
**Status:** READY — Anas Q1-Q4 + Q6 answered. Q5/Q7/Q8 = BRIEF defaults
acceptable. **§5 empirical probe SKIPPED** (Q1+Q2: Aryan is private/internal
source, no public URL → nothing to probe).
**Production baseline at entry:** Heroku v124 (code v121, engine
`thammen-sprint2p21p3-t2-apartments-lusail`)
**Predecessor:** Sprint 2.21.3 SHIPPED — Lusail apartments via PF T2 hybrid
**Lane:** This file is Claude Code (methodology gathering). BRIEF itself
lives in Claude.ai's lane.

---

## 1. Audit goal (per Rule #51 audit-driven Sprint pattern)

Sprint 2.21.4 introduces the **T3 tier** to the hybrid valuation framework
— developer-direct off-plan / single-developer inventory. Unlike Sprint
2.21.3 (live network connector for an established public listings source),
Sprint 2.21.4 is **schema + workflow + first manual entry** for a tier
that does not have a single canonical scraping target.

The audit serves two purposes:

1. **Inventory what's already in place** — confirm the foundation
   (`hybrid_valuation.py` T3 plumbing) is null-safe so 2.21.4 can ship
   atomically against it. ✅ Confirmed (see §2).
2. **Enumerate the open decisions** Claude.ai needs to make for the BRIEF
   — schema fields, manual-entry workflow, geo scope, developer set,
   off-plan-vs-ready handling.

Light empirical component: probe Aryan + selected Qatar developers for
public reachability + any structured catalog (rather than a heavy multi-
source scrape audit like 2.21.3).

---

## 2. Known facts about T3 in the existing framework

From `hybrid_valuation.py` + Empirical_Findings Rule E3 + CHANGELOG_v47:

### 2.1 Configuration already in `HYBRID_TIER_CONFIG`

```python
# T3 (developer-direct off-plan) — D4 + D6
"T3_weight_cap": 0.15,
"T3_discount_midpoint": -0.175,
"T3_discount_range": (-0.20, -0.15),
"T3_evidence_strength_full_cap_at_n": 5,    # smaller — T3 is single-developer
```

The −17.5% midpoint is decomposed in CHANGELOG_v47 §1 as:
≈ 10% negotiation component + ≈ 7.5% off-plan-to-resale equivalent.

### 2.2 Function behaviour (Rule E3 Constraint 8)

`hybrid_valuation_v1` already routes:
- T1 present + T3 present → Case A (T3 contributes up to 0.15)
- T1 absent + T2 present + T3 present → Case B (T3 contributes up to 0.15)
- T1 absent + T2 absent + T3 present → **Case C — refused** (returns
  `value_per_m2: None`, `confidence: fallback`, message "T3 alone
  insufficient")

So a T3-only Sprint that supplies T3 dicts without ever activating Case A
or B will simply not fire — `_try_hybrid_apartments_response` only invokes
the function with `t3_values=None` today.

### 2.3 Sprint 2.21.4 surface area (per CLAUDE.md roadmap + v47 docstring)

- New module: `connectors/developer_inventory_t3.py` (or equivalent path)
- New persistence: `developer_inventory.sqlite`
- New manual-entry pipeline (CLI? CSV import? Admin endpoint?)
- Engine integration: extend `_try_hybrid_apartments_response` to pass
  `t3_values=...` alongside the existing `t2_values`
- First seed: "Aryan" (per roadmap line — context to be confirmed by Anas)

### 2.4 Two roadmap entries depend on this Sprint's schema

- **Sprint 2.21.5** — UI tier breakdown + MUC surfacing (needs T3 column
  in the rendered tier_breakdown table)
- **Sprint 2.16.16** — Confirmed Sales DB integration path (a) says
  "consolidate with Sprint 2.21.4 T3 schema (developer_inventory.sqlite
  extended to brokerage closings)". So schema choices here affect a
  potential downstream merge of brokerage-closed transactions into the
  same SQLite.

---

## 3. Schema candidates (DRAFT — Claude.ai to finalise in BRIEF)

Open for review. Listed as starting-point columns; field naming +
required-vs-optional is a BRIEF decision.

### 3.1 Minimal schema (per-unit listing row)

```sql
CREATE TABLE developer_inventory (
    listing_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    developer            TEXT    NOT NULL,    -- "Aryan", "UDC", "Qetaifan", ...
    project              TEXT,                -- "Lusail Marina Tower 3"
    district             TEXT    NOT NULL,    -- "Lusail" (canonical GIS ANAME or sub-area)
    sub_area             TEXT,                -- "Marina District" / "Fox Hills" / ...
    unit_type            TEXT,                -- "1BR" | "2BR" | "3BR" | "studio" | "penthouse"
    area_m2              REAL    NOT NULL,
    price_qar            INTEGER NOT NULL,
    value_per_m2         REAL,                -- computed; redundant but useful for query/cache
    status               TEXT    NOT NULL,    -- "off_plan" | "ready" | "under_construction"
    completion_year      INTEGER,             -- expected handover (for off_plan)
    payment_plan_summary TEXT,                -- e.g. "30% down + 70% on handover"
    source_url           TEXT,                -- broker brochure / developer page
    captured_at          TEXT    NOT NULL,    -- ISO date of manual entry
    captured_by          TEXT,                -- "anas" / "secretary" / ...
    last_verified_at     TEXT,                -- refresh date if re-checked
    notes_ar             TEXT,
    UNIQUE (developer, project, unit_type, area_m2, price_qar)
);
```

### 3.2 Cross-cutting decisions (for D-numbered BRIEF entries)

- **DA**: row granularity — per unit / per unit-type-aggregate / per project? Default proposal: per unit listing (line above)
- **DB**: which fields are required vs optional? Default proposal: developer + district + area_m2 + price_qar + status + captured_at are required; the rest optional
- **DC**: status taxonomy — 3 values (off_plan / under_construction / ready) or 2 (off_plan / ready)? Default proposal: 3
- **DD**: discount handling — does the −17.5% T3_discount_midpoint apply uniformly across status values, or only to `off_plan`? Default proposal: midpoint applies to off_plan; ready listings get only the −10% negotiation (-0.10) portion, signalling that `ready` rows are closer to T2 than T3 semantically
- **DE**: how long is a row considered "fresh"? TTL on `last_verified_at`? Default proposal: 90 days; older rows downgrade to `fallback` weight at hybrid layer
- **DF**: manual-entry interface — CLI script with prompts, JSON import, CSV upload, or admin web form? Default proposal: CSV import with strict pydantic-validated schema (mirrors Bug A2 fix discipline — Rule #31)
- **DG**: how does the connector interact with `T2ListingsCache`? Default proposal: T3 is local-only persistent SQLite (no TTL — manual data doesn't expire by network freshness)
- **DH**: where in `evaluate_unified.py` does T3 plug in? Default proposal: same `_try_hybrid_apartments_response` helper (Sprint 2.21.3), now passing `t3_values=...` from a new `connectors/developer_inventory_t3.py` reader
- **DI**: geo scope first cut — Lusail-only (consistent with 2.21.3), or wider? Default proposal: Lusail-only with schema-level field `district` so wider expansion is just data-entry not code-change
- **DJ**: "Aryan" specifics — who, what, where? **NEEDS ANAS INPUT** (see §4)

---

## 4. Anas-answered + BRIEF-pending decisions

### 4.1 Anas-answered (2026-05-25)

| # | Question | Answer | Sprint impact |
|---|---|---|---|
| **Q1+Q2** | Aryan identity + URL | **Private/internal source**, no public URL | §5 probe SKIPPED. Manual entry workflow only. No connector to external developer site in 2.21.4. |
| **Q3** | First-seed scope | **Aryan-only in 2.21.4.** Expansion = data-only Sprints later (2.21.4.1, .2, ...) | Single-purpose Sprint per Rule #38. Schema must support adding developers without code change (DH default holds). |
| **Q4** | Manual-entry interface | **CSV import + strict pydantic validation** | Rule #31 applies (`extra='forbid'` on the import schema). CLI script reads CSV → validates per-row → inserts. Bad rows → HTTP-422-style structured rejection with field name + reason. |
| **Q6** | 2.16.16 schema fold-in | **Defer the decision.** Build 2.21.4 as T3-only schema. | DO NOT pre-add `transaction_type` discriminator. DO NOT design with brokerage closings in mind. When 2.16.16 arrives (6-18 months), assess actual brokerage data shape and either extend or create separate table. |

### 4.2 BRIEF-pending decisions (Claude.ai default OK; Anas may override)

| # | Question | Default proposal for BRIEF |
|---|---|---|
| Q5 | Off-plan headline-price skepticism beyond D6 −7.5%? | NO additional skepticism. D6 −17.5% midpoint (≈10% nego + ≈7.5% off-plan-to-resale) was calibrated assuming developer headline. Adding a stack-on would double-count. If real-world Aryan rows show systematic over-promise, recalibrate D6 (separate Sprint). |
| Q7 | UI surfacing of developer/project name | Show in `tier_breakdown` block under T3 row (Rule E10 transparency: source + tier + n + role_ar). Default proposal: `role_ar = "مخزون مطوّر — {developer_name}"`. Internal-source nature (Q1) means Anas may want to redact; BRIEF can flip to aggregate. |
| Q8 | First test PIN for H1 verification | 69/329/20 (the Lusail Fox Hills apt that already produces hybrid_t2 via Sprint 2.21.3 with n=79 T2). Adding T3 listings for that micro-market lets H1 verify the case-B-with-T3 routing in `hybrid_valuation_v1` end-to-end. |

---

## 5. Empirical probe scope — **SKIPPED**

Per Anas answer to Q1+Q2 (§4.1): Aryan is a private/internal source with
no public URL. There is nothing to probe.

Sprint 2.21.4 is therefore a **pure schema + workflow Sprint** with no
external endpoint dependency. This is a meaningful simplification vs
Sprint 2.21.3 (which had Pre-Sprint smoke at v108 + schema audit at
v110-v113 + list-page probe at v120).

**No Heroku push for probes in Pre-Sprint 2.21.4.** The next Heroku push
happens when Claude Code ships the Sprint itself, after Claude.ai signs
the BRIEF.

---

## 6. Inputs for BRIEF_2p21p4 hand-off (READY)

This section gives Claude.ai everything needed to draft BRIEF_2p21p4.

### 6.1 Sprint scope (Anas-confirmed)

- **What this Sprint ships**: SQLite schema + CSV-import CLI + engine
  integration so `_try_hybrid_apartments_response` (Sprint 2.21.3) can
  pass `t3_values=...` to `hybrid_valuation_v1` when developer inventory
  exists for the queried micro-market.
- **First-seed developer**: Aryan (private internal source, manual entry).
- **Geo first cut**: Lusail-only (mirror 2.21.3). Schema field `district`
  permits wider expansion via data-entry, no code change.
- **Status taxonomy**: `off_plan` | `under_construction` | `ready` (3-value).

### 6.2 Decisions ready for D1-Dn numbering in BRIEF

| Ref | Decision | Default for BRIEF |
|---|---|---|
| D1 | Sprint number | `2.21.4` |
| D2 | Schema table name | `developer_inventory` in `developer_inventory.sqlite` |
| D3 | Row granularity | per unit listing (one row = one offered unit) |
| D4 | Required fields | developer, district, area_m2, price_qar, status, captured_at |
| D5 | Optional fields | project, sub_area, unit_type, completion_year, payment_plan_summary, source_url, captured_by, last_verified_at, notes_ar |
| D6 | Status discount handling | `off_plan` + `under_construction` → full D6 −17.5%. `ready` → only −10% negotiation (D5 T2 discount path) since "ready" is closer to T2 semantically. **OR**: keep all status values at −17.5% to avoid complexity. BRIEF decides. |
| D7 | Row freshness TTL | 90 days `last_verified_at`. Stale rows → downgrade to evidence_strength 0.5 multiplier in hybrid (not full exclusion). |
| D8 | Manual-entry workflow | CSV import via CLI script `scripts/import_developer_inventory.py`. Strict pydantic validation (Rule #31). Per-row reject with reason. Idempotent: upsert by UNIQUE(developer, project, unit_type, area_m2, price_qar). |
| D9 | Engine integration | Extend `_try_hybrid_apartments_response` (evaluate_unified.py:~1700) to read `developer_inventory.sqlite` for the current district + asset_type. Pass non-None `t3_values` to `hybrid_valuation_v1` alongside existing `t2_values`. Rest of helper unchanged. |
| D10 | Feature flag | `T3_INVENTORY_ENABLED` env var (default `true` after deploy; emergency disable via `heroku config:set` without code revert). Mirrors HYBRID_APARTMENTS_ENABLED. |
| D11 | CSV template + sample | Ship `scripts/developer_inventory_template.csv` with one example Aryan row in Lusail. README in `2p21p4_brief/`. |
| D12 | Test scope | ≥20 isolated tests: schema migration idempotent, CSV import success/failure cases, per-row validation, engine T3 plug-in (case A + B + transition to B-with-T3), feature flag, geo filter, status discount routing. |

### 6.3 Engine integration shape (BRIEF §4 spec)

```python
# In _try_hybrid_apartments_response, after T2 fetch:
if os.getenv('T3_INVENTORY_ENABLED', 'true').lower() != 'false':
    t3_rows = developer_inventory_t3.fetch_for_district(
        district=district_ar,
        asset_type=asset_type,
        status_filter=('off_plan', 'under_construction', 'ready'),
        max_age_days=90,
    )
else:
    t3_rows = None

hybrid = hybrid_valuation_v1(
    t1_values=None, t1_n_total=0,
    t2_values=t2_listings,
    t3_values=t3_rows,    # was None in 2.21.3
)
```

### 6.4 Hypotheses for post-deploy verification (BRIEF §6 spec)

| # | Hypothesis | Falsified by |
|---|---|---|
| H1 | 69/329/20 evaluation now returns `tier_breakdown` containing BOTH T2 (PF) and T3 (Aryan) rows when developer_inventory has ≥1 Aryan unit in Fox Hills | tier_breakdown missing T3 row OR T3 row has wrong discount applied |
| H2 | 69/329/20 with `T3_INVENTORY_ENABLED=false` returns identical response to current Sprint 2.21.3 baseline (no T3 row in tier_breakdown) | T3 row leaks despite flag off |
| H3 | Empty developer_inventory.sqlite (post-fresh-deploy, no rows imported) does NOT crash any apartment evaluation; engine just emits T2-only response | NameError, crash, or 500 on any apt eval when table is empty |
| H4 | CSV import of a clean Aryan-style row (off_plan, Lusail Marina, 2BR, 120 m², 2.5M QAR) succeeds; the next /api/evaluate for a Lusail apt picks it up in tier_breakdown | Row not picked up OR engine doesn't see the new data |
| H5 | CSV import of a malformed row (missing required field, unknown column, wrong type) is REJECTED with a structured per-row error containing the bad field name | Silent acceptance OR generic error |
| H6 | All existing 28-file regression PASS (Sprint 2.21.3 hybrid Lusail flow unchanged when T3 data absent) | Any regression failure |
| H7 | New test suite ≥20 functions covering D12 axes — all PASS | Coverage gap |
| H8 | Stale row (last_verified_at > 90 days ago) downgrades to 0.5× evidence_strength multiplier in hybrid; row still appears in tier_breakdown but with `freshness_status: 'stale'` annotation | Stale rows treated as fresh OR excluded silently |
| H9 | Geo filter works: a Pearl apt evaluation does NOT pick up Lusail T3 rows | T3 rows leak across districts |
| H10 | Anas's visual verification on thammen.qa for 69/329/20: response shows clearly which discount was applied to which T3 row + which developer | UI shows generic "T3" without developer-name transparency (Rule E10 breach) |

### 6.5 Rollback plan (mirrors Sprint 2.21.3 protocol)

- Code rollback: `heroku rollback v<previous>` (one command)
- Feature flag rollback (no redeploy): `heroku config:set T3_INVENTORY_ENABLED=false`
- Data-only rollback: `DELETE FROM developer_inventory` (last resort — SQLite is part of slug)

---

## 7. Hygiene

- This file lives in `2p21p4_pre/` per Pre-Sprint pattern.
- No production code touched.
- No Heroku push at any point during Pre-Sprint 2.21.4 (no probes
  needed — Anas Q1+Q2 answered).
- Engine version unchanged (v124 production, code v121).
- Tasks tracked in Claude Code session: #12 audit ✓, #13 outline ✓,
  #14 Anas input ✓, #15 probe SKIPPED, #16 hand-off ready.

---

*— Claude Code, 2026-05-25. Pre-Sprint 2.21.4 ready for Claude.ai
BRIEF draft. Hand-off content in §6.*
