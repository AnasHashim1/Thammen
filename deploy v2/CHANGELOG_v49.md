# CHANGELOG v49 — Sprint 2.21.4 — T3 Developer-Inventory Schema (Aryan, Lusail)

**Engine version (post-deploy, target):** `thammen-sprint2p21p4-t3-aryan-lusail`
**Heroku release target:** TBD (pending Anas review per BRIEF §7 step 15)
**Date opened:** 2026-05-25
**BRIEF reference:** [`BRIEF_2p21p4_FINAL.md`](../BRIEF_2p21p4_FINAL.md) — Anas-signed; D1–D12 per BRIEF §2 (RATIFIED/AMENDED status preserved below).
**Production baseline at entry:** Heroku **v124** (code v121, engine
`thammen-sprint2p21p3-t2-apartments-lusail`, Sprint 2.21.3 — Lusail
apartments via PropertyFinder T2 hybrid).
**Pre-Sprint inputs:** [`2p21p4_pre/CHANGELOG_pre_2p21p4.md`](2p21p4_pre/CHANGELOG_pre_2p21p4.md)
(no probes — Aryan is private/internal source per Q1+Q2; pure schema +
workflow design Sprint).
**Seed data:** 4 Aryan / City Avenues rows in BRIEF §11.1.
**Parked data:** 2 Aryan / Scala Qetaifan villa rows in BRIEF §12 — NOT for this Sprint.

---

## Slot-numbering check (per Rule #39 + Rule #53 precedent)

BRIEF §7 step 1 says "`CHANGELOG_v49.md`". v49 **is** the natural next
sequential slot (v48 = Sprint 2.21.3, T2 PropertyFinder Lusail apartments
hybrid path). **No drift.** Slot-numbering discipline maintained.

---

## Scope statement (BRIEF §1, verbatim-condensed)

Sprint 2.21.4 introduces the **T3 tier** to the live hybrid valuation
pathway. Deliverables:

1. `developer_inventory.sqlite` — CSV-driven manual-entry persistence
   for developer-direct inventory (per-unit row granularity).
2. `scripts/import_developer_inventory.py` — strict-pydantic CSV importer
   (Rule #31 `extra='forbid'`).
3. Extension of `_try_hybrid_apartments_response` (Sprint 2.21.3) to
   pass `t3_values=...` into `hybrid_valuation_v1`.
4. Status-aware T3 discount inside `hybrid_valuation_v1` (off_plan /
   under_construction → −17.5%; ready → −10%).
5. New module `connectors/developer_inventory_t3.py` with
   `fetch_for_district()` API.

**First seed:** Aryan (private internal source — no public URL).
**Geo first cut:** Lusail (or whatever GIS confirms for City Avenues
centroid — see §11.3 / Step 14 in BRIEF §7).
**Status taxonomy:** `off_plan | under_construction | ready` (3-value).
**No external network connector. No public probe. No T1 / T2 path changes.
No API surface change.** Sprint 2.16.16 schema fold-in is DEFERRED —
`developer_inventory` is T3-only by design, no `transaction_type`
discriminator.

---

## 1. Decision register (D1–D12, per BRIEF §2)

Status legend: **RATIFIED** = Pre-Sprint default accepted as-is.
**AMENDED** = BRIEF modified the default. **DEFERRED** = moved out
of this Sprint.

| # | Decision | Status | Value |
|---|---|---|---|
| **D1** | Sprint number | RATIFIED | `2.21.4` |
| **D2** | Schema table name + file | RATIFIED | `developer_inventory` table in `developer_inventory.sqlite` at project root (alongside reserved `confirmed_sales.sqlite` for Sprint 2.16.16). |
| **D3** | Row granularity | RATIFIED | Per offered unit (one row = one listed unit). Per-project / per-unit-type aggregation rejected — would lose area heterogeneity needed for like-for-like comparison. |
| **D4** | Required fields | **AMENDED** | Pre-Sprint default: `developer, district, area_m2, price_qar, status, captured_at`. **Amended to:** `developer, district, unit_type, area_m2, price_qar, status, captured_at` — `unit_type` now required (without it, 120 m² @ 2.5M is ambiguous between 2BR and 1BR+study). Enum: `studio | 1BR | 2BR | 3BR | 4BR | penthouse`. Maid-room variants → free-text in `notes_ar`, NOT separate enum. |
| **D5** | Optional fields + auto-computed | RATIFIED + 1 addition | Pre-Sprint optional set, plus auto-computed `value_per_m2 = price_qar / area_m2` (stored redundantly at import for query-cache efficiency; never user-supplied). |
| **D6** | Status-aware T3 discount | RATIFIED — meaningful function change | `off_plan → −17.5%`, `under_construction → −17.5%`, `ready → −10%`. Tier stays T3 in all cases (tier is a function of source independence, not occupiability). **Implementation requires `hybrid_valuation_v1` to accept T3 rows as dicts with `status` field** and apply per-row discount, NOT a uniform scalar. New `HYBRID_TIER_CONFIG['T3_status_discount_map']` replaces scalar `T3_discount_midpoint` (legacy scalar kept as `T3_discount_default` for back-compat with non-inventory T3 callers passing bare floats). |
| **D7** | Row freshness TTL + annotation | **AMENDED** | 90-day TTL on `last_verified_at`. Stale → 0.5× evidence_strength multiplier AND each row's `tier_breakdown` entry MUST carry `freshness_status: 'stale' \| 'fresh'`. Rule E10 audit trail — without annotation, weight 0.075 (= 0.15 × 0.5) is inexplicable to future reviewers. |
| **D8** | CSV import + composite key | **AMENDED** | Pre-Sprint default: `UNIQUE(developer, project, unit_type, area_m2, price_qar)`. **Amended:** `UNIQUE(developer, project, unit_type, area_m2)` — price_qar **removed** from key. Rationale: price revision on same unit must upsert (one row, refreshed price + `last_verified_at`), NOT create a second row that double-counts the same underlying inventory in the median during the 0-89 days before the old row decays. Rest of D8 (Rule #31 strict pydantic, per-row reject with field name, idempotent upsert) ratified. |
| **D9** | Engine integration shape | **AMENDED — fetcher returns raw, hybrid applies discount** | Fetcher (`developer_inventory_t3.fetch_for_district`) returns list of dicts each with `value_per_m2_raw`, `status`, `last_verified_at`, `freshness_status`, `developer`, `project`, `unit_type`, `area_m2`. **`max_age_days=None`** at fetch — stale rows enter hybrid with annotation, hybrid applies 0.5× multiplier (preserves Rule E10 transparency vs silent omission). Status-aware discount lives inside `hybrid_valuation_v1` (single source of truth for tier math). Back-compat: legacy callers passing list-of-floats use `T3_discount_default` and `freshness='fresh'` defaults. |
| **D10** | Feature flag | RATIFIED | `T3_INVENTORY_ENABLED` env var, default `true` post-deploy. Mirrors `HYBRID_APARTMENTS_ENABLED` (Sprint 2.21.3 D11). Emergency disable: `heroku config:set T3_INVENTORY_ENABLED=false` (no redeploy). |
| **D11** | CSV template + README + verbatim single-source caveat | RATIFIED + verbatim caveat | Ship `scripts/developer_inventory_template.csv` (header + 1 sample row — City Avenues 1BR from §11.3) + README at `2p21p4_brief/README.md`. **Verbatim single-source caveat block** (BRIEF §2 D11) MUST appear in README: *"Single-source caveat. Rows in `developer_inventory.sqlite` come from one developer at a time. n rows from one developer do NOT constitute an n-sample market signal — they are one informed party's price-setting. The T3 tier weight cap (0.15) and the `T3_evidence_strength_full_cap_at_n=5` parameter reflect this in the math. Treat T3 as informational evidence, not a market sample. UI surfaces this caveat to the end user via the tier_breakdown row's role_ar and tooltip."* |
| **D12** | Test scope ≥ 20 isolated tests | RATIFIED — 20 explicit axes | Axes 1–20 enumerated in BRIEF §2 D12 (schema migration idempotency; CSV success / missing-field / unknown-column / wrong-type / invalid-enum reject; upsert-on-revision; per-status discount routing ×3; freshness ×2; geo filter; flag OFF; case A / B / C routing; tier_breakdown 7-field shape per Rule E10; empty-DB no-crash; partial-population negative test). Plus 28-file regression must remain green (covered separately in H6). |

---

## 2. Pre-Sprint §5 audit results (BRIEF §5 contingency note)

No empirical probes were run for this Sprint. Pre-Sprint 2.21.4
([`2p21p4_pre/CHANGELOG_pre_2p21p4.md`](2p21p4_pre/CHANGELOG_pre_2p21p4.md))
documented why:

- **Aryan = private/internal source** (Q1+Q2 answer). No public URL.
  Nothing to probe.
- **Schema + workflow Sprint** — not connector Sprint. No external endpoint
  reachability or shape questions to answer.
- **No Heroku push during Pre-Sprint** (mirror of Sprint 2.16.15 pattern
  where the Pre-Sprint was pure design analysis).

The audit's deliverable was 8 ratified + 4 amended D-decisions + BRIEF
§6 hand-off content, all consumed and ratified by BRIEF FINAL.

**GIS verification step (BRIEF §7 step 14) is NOT a Pre-Sprint probe** —
it is an in-Sprint gate that runs once, ~2 min, against the City Avenues
project centroid before the importer runs. It establishes the canonical
`district` ANAME for the 4 seed rows. Outcome decision tree:

- GIS returns `لوسيل` → import proceeds normally; **H1** is the active hypothesis.
- GIS returns a non-Lusail district (e.g. `الدفنة` / `مارينا`) → import still proceeds with the GIS-canonical district; rows park in DB; **H1' contingency** activates with one synthetic Lusail row + 69/329/20 anchor + post-test DELETE.

---

## 3. Files modified / created in this Sprint (planned per BRIEF §7)

**New (7 files):**

- `migrations/2p21p4_developer_inventory.sql` — DDL: CREATE TABLE + UNIQUE per D4+D5+D8.
- `scripts/migrate_developer_inventory.py` — idempotent migration runner; verifies schema matches DDL on each run.
- `scripts/import_developer_inventory.py` — strict-pydantic CSV importer per D8. Per-row try/except, structured rejection with field name. Upsert by D8 composite key. Auto-computes `value_per_m2`.
- `scripts/developer_inventory_template.csv` — header row + 1 sample row (City Avenues 1BR from BRIEF §11.3).
- `connectors/developer_inventory_t3.py` — `fetch_for_district()` per BRIEF §3.1. Module-scoped DB connection; freshness computed against 90-day TTL.
- `tests/test_sprint_2p21p4_t3_inventory.py` — ≥20 functions covering D12 axes 1–20.
- `2p21p4_brief/README.md` — workflow walkthrough; verbatim D11 single-source caveat; status taxonomy table; example commands.

**Modified (3 files):**

- `hybrid_valuation.py` — `HYBRID_TIER_CONFIG`: replace `T3_discount_midpoint` scalar with `T3_status_discount_map` dict + retain `T3_discount_default`. `hybrid_valuation_v1` body: per-row status + freshness handling (dict shape) + back-compat for legacy float shape. Tier_breakdown emission per Rule E10 (D12 axis 18).
- `evaluate_unified.py` — `_try_hybrid_apartments_response`: insert `developer_inventory_t3.fetch_for_district(...)` call between T2 fetch and `hybrid_valuation_v1` invocation; pass `t3_values=t3_rows`. **ENGINE_VERSION + SPRINT_TAG bump** (line 44-45) to `thammen-sprint2p21p4-t3-aryan-lusail` / `2.21.4`.
- This file (`CHANGELOG_v49.md`).

**Data artifact (one-time, populated PRE-DEPLOY per BRIEF amendment 2026-05-25 — ephemeral Heroku filesystem):**

- `developer_inventory.sqlite` — populated **LOCALLY** by running `scripts/import_developer_inventory.py` against the 4 City Avenues rows AFTER Anas sign-off (Step 15) AND BEFORE `git subtree push` (Step 18). The populated `.sqlite` file is committed to git as part of the Sprint commit and ships in the slug. **Heroku filesystem is ephemeral** — a post-deploy `heroku run python scripts/import_…` would write to a dyno-local FS that gets wiped on next restart. The commit-then-deploy pattern mirrors `building_age_cache.sqlite` (Sprint 2.15.1, 62 PINs imagery cache, same architectural constraint). Rows are auditable history living in git.

**Parked (NOT for this Sprint, per BRIEF §12):**

- `2p21p4_pre/aryan_parked_villas_2026-05-25.csv` — 2 Scala Qetaifan villa rows. Created in this Sprint as a parking file; NOT imported. Reason: asset class (villas, not apartments); geography (Qetaifan ≠ Lusail); methodology open (BUA vs land basis).

**Env var (new):**

- `T3_INVENTORY_ENABLED` — default `true` post-deploy via code default; explicit set on Heroku optional (matches `HYBRID_APARTMENTS_ENABLED` discipline).

**No API surface change.** No new endpoint, no new request field, no new response key beyond the `tier_breakdown` content updates (which are read-side, not request-side).

---

## 4. Pre-implementation audit — N/A

Sprint 2.21.4 has no Step 2 schema audit (Sprint 2.21.3 had one because
that was a connector Sprint with external HTML structure to probe). The
equivalent for Sprint 2.21.4 is BRIEF §11 (seed data + import-time
assumptions), already provided.

The single in-Sprint empirical step is BRIEF §7 step 14 — the GIS
verification of the City Avenues centroid (~2 min, runs once, results
captured here when executed).

---

## 5. Schema + importer implementation evidence

### 5.1 Schema (BRIEF §7 step 2 — `migrations/2p21p4_developer_inventory.sql`)

- 17-column `developer_inventory` table: 7 required NOT NULL + 8 optional + 1 auto-computed `value_per_m2`
- D4 amended: `unit_type` enum via `CHECK (unit_type IN ('studio','1BR','2BR','3BR','4BR','penthouse'))`
- D6 enum: `CHECK (status IN ('off_plan','under_construction','ready'))`
- D8 amended composite: `UNIQUE (developer, project, unit_type, area_m2)` — `price_qar` deliberately EXCLUDED (revisions upsert)
- Idempotent `CREATE IF NOT EXISTS` on all tables/indexes; smoke test ran DDL twice with no error
- 2 named indexes: `idx_developer_inventory_district_status` (fetcher hot path), `idx_developer_inventory_last_verified` (future TTL purge)
- `schema_meta` table for migration runner version tracking

### 5.2 Migration runner (BRIEF §7 step 3 — `scripts/migrate_developer_inventory.py`)

- `migrate(db_path, ddl_path, dry_run, verbose) → int` orchestrates Phase 1 (executescript) → Phase 2 (verify_schema) → Phase 3 (stamp version, no-op on subsequent runs)
- `verify_schema()` compares live schema to `EXPECTED_COLUMNS_DEVELOPER_INVENTORY` (17 cols) + `EXPECTED_UNIQUE_COLUMNS` + named indexes; returns `(ok, drifts)` for human-readable diagnostics
- True no-op verified: 3 consecutive runs produced identical `last_migration_run_at` timestamp; only Phase 1 + Phase 2 run on no-op (read-only); Phase 3 skipped because version already at 1
- Drift detection verified by injecting `ALTER TABLE ADD bogus_col` → exit code 1 + "column count: expected 17, got 18" diagnostic

### 5.3 Importer (BRIEF §7 step 4 — `scripts/import_developer_inventory.py`)

**Strict pydantic (Rule #31)**: `InventoryRow` uses `ConfigDict(extra='forbid', str_strip_whitespace=True)`. Unknown CSV columns trigger `error_type='extra_forbidden'` with the offending column name in `loc[-1]`.

**Per-row recovery**: each row wrapped in try/except; one bad row never aborts the batch (Rule #39). Structured rejection dict: `{row_num, field, reason, error_type, raw_row, all_errors}`.

**Upsert via `ON CONFLICT DO UPDATE`** on the D8 composite key. Three update strategies per column class:
- **Always overwrite**: `price_qar`, `value_per_m2`, `status`, `last_verified_at` (the purpose of a revision upsert)
- **COALESCE preserve**: `sub_area`, `completion_year`, `payment_plan_summary`, `source_url`, `captured_by`, `notes_ar` (new NULL doesn't clobber existing)
- **Never updated on conflict**: `captured_at` (first-import semantics), `district` (GIS-canonical from initial capture)

**Auto-compute `value_per_m2`** via pydantic `model_validator(mode='after')`: `round(price_qar / area_m2, 2)`. Set before insert; never user-supplied. Aryan 1BR fixture: `1,150,000 / 86 = 13,372.09` matches BRIEF §11.1 expected.

### 5.4 Sentinel choice (Step 4 carry-over #1)

**Decision**: NULL/empty/whitespace `project` is normalised to literal string `'(unspecified)'` via `field_validator(mode='before')` in `InventoryRow`. Chosen over the alternative `f"_{developer}_default"` for three reasons:

1. **Literal grep-able value** — single constant for the whole table, regardless of developer. Easier to spot in reports / SQL queries.
2. **Same UNIQUE semantics** — `(developer, '(unspecified)', unit_type, area_m2)` still gives per-developer uniqueness because `developer` is in the composite key; no cross-developer collision risk.
3. **Clean separation** of "the row's project name" from "a synthesised marker" — putting the developer name into the `project` field would conflate roles.

**Closes the Step 2 soft-flag** about SQLite NULL-aware UNIQUE bypass (multiple NULLs treated as distinct). With the sentinel, all rows have a non-NULL project string; UNIQUE works as intended.

### 5.5 Rejection count clarification (Step 4 carry-over #2)

Step 4 spec mentioned "five structured rejections" in the smoke test description. Actual smoke produced **4 rejection categories** (matching the 4 invalid-row categories explicitly listed in the spec):

1. Missing required field (`unit_type`) → `string_type`
2. Wrong type (`area_m2='not_a_number'`) → `float_parsing`
3. Invalid status enum (`status='pending'`) → `value_error`
4. Unknown column (`bogus_extra_col`) → `extra_forbidden`

Plus 1 clean insert + 1 duplicate-of-clean upsert = 6 rows in, 1 row in DB at end, 4 rejections in report. Spec "5" was an off-by-one in the count; the listed categories were always 4. Test suite Step 10 mirrors the 4-axis coverage (D12 axes 3-6).

### 5.6 Importer validation bands (Step 4 carry-over #3)

Importer enforces `field_validator` ranges for empirical sanity:

- `area_m2`: `[20.0, 5000.0]` m² (= `MIN_AREA_M2` / `MAX_AREA_M2`). Lower bound: a 20 m² studio is the smallest plausible apartment; below is likely a unit-of-comparison error (sqft instead of sqm). Upper bound: 5000 m² covers penthouses and Anas's Scala Qetaifan parked-data 462 m² with comfortable headroom; rejects whole-building areas.
- `price_qar`: `[100_000, 1_000_000_000]` QAR (= `MIN_PRICE_QAR` / `MAX_PRICE_QAR`). Lower bound: 100K filters out rent or service-fee leakage into the price column. Upper bound: 1B accommodates the most expensive Qatari real estate transactions without rejecting genuine high-end inventory.
- `completion_year`: `[2020, 2050]` — covers backlog of unreleased projects and future planning horizons.

**Empirical basis**: bands derived from Sprint 2.21.3 PropertyFinder smoke (~12,000-25,000 QAR/m² Lusail apartments × 60-300 m² range = ~720K-7.5M QAR total). Importer band is conservative belt-and-suspenders alongside the DDL `CHECK (area_m2 > 0)` / `CHECK (price_qar > 0)` constraints; DDL guards against obvious bugs (zero / negative), importer guards against unit-mismatch + data-source-mixing.

### 5.7 Template (BRIEF §7 step 5 — `scripts/developer_inventory_template.csv`)

**16 columns** (7 required + 8 optional + 1 auto-computed) — Step 5 spec said "9 optional + value_per_m2" = 17, but actual model has 8 optional fields (project, sub_area, completion_year, payment_plan_summary, source_url, captured_by, last_verified_at, notes_ar). Template matches the implemented model. Carry-over #4: off-by-one in spec count, no semantic divergence.

**UTF-8 BOM** prepended (`ef bb bf` prefix) for Excel autodetect on Arabic columns; importer's `utf-8-sig` decoder strips BOM cleanly (no leakage into `headers[0]`).

**One sample row**: Aryan / City Avenues / 1BR / 86 m² / 1.15M QAR / ready / 2026-05-25 (per BRIEF §11.3). `district='لوسيل'` is a **placeholder** pending Step 14 GIS verification.

End-to-end smoke verified: migrate → import template → 1 row inserted, value_per_m2 auto-computed = 13,372.09, Arabic strings round-trip (لوسيل / أقساط حتى 7 سنوات / بالقرب من المول التجاري).

### 5.8 BRIEF §11.2 Assumption 2 corrected pre-deploy (2026-05-25)

BRIEF §11.2 Assumption 2 inferred `status='ready'` for all 4 Aryan / City
Avenues rows from two signals (long installment horizon, "متبقية شقة واحدة
فقط" inventory note). Anas confirmed empirically pre-deploy that the
project is **under construction** with handover horizon ~Nov 2027 (visible
construction in imagery + ~1.5-year handover signal). Original `ready`
inference closed; status updated to `under_construction` in the seed CSV
(`2p21p4_brief/aryan_seed_2026-05-25.csv`) before Step 16 import.

The bounded-error analysis in BRIEF §11.2 anticipated this exact case at
worst-case ~0.9% impact on final value (T3 weight ceiling 0.12 × 7.5
percentage-point discount delta = 0.009). That bound is now avoided by
the pre-deploy correction — math is exactly right at first deploy.

**Math under correction**: D6 routes both `off_plan` and `under_construction`
to `-0.175` (same discount), so the numerical impact of the inference flip
is from `-0.10` (ready) → `-0.175` (under_construction):
- Raw cluster: 13,281–13,432 QAR/m² (median 13,382.47)
- Pre-correction expected (ready, -10%): adjusted ~12,000-12,100
- **Post-correction actual (under_construction, -17.5%): adjusted 10,957-11,082 (median 11,040.54)**

T3 weight ceiling unchanged at 0.12 (= 0.15 cap × 4/5 evidence_strength).
H1 expected value updates in §8 to reflect the new discount path.

Field `completion_year=2027` added to all 4 seed rows (optional field,
D5) — captures the handover signal explicitly for future freshness/
maturity logic and audit-trail purposes.

### 5.9 Seed CSV import — Step 16 evidence

Import command + result (2026-05-25, ~16:00 UTC):
```
$ python scripts/import_developer_inventory.py 2p21p4_brief/aryan_seed_2026-05-25.csv
[import] rows seen:   4
[import] inserted:    4
[import] updated:     0
[import] rejected:    0
[import] OK: all 4 rows imported (inserted=4, updated=0).
```

DB verification (`developer_inventory.sqlite`):

| unit | area | price | v/m2 raw | v/m2 × 0.825 (under_construction adjusted) |
|---|---:|---:|---:|---:|
| 1BR | 86 | 1,150,000 | 13,372.09 | 11,031.97 |
| 2BR | 128 | 1,700,000 | 13,281.25 | 10,957.03 |
| 2BR | 134 | 1,800,000 | 13,432.84 | 11,082.09 |
| 3BR | 168 | 2,250,000 | 13,392.86 | 11,049.11 |

**Median adjusted: 11,040.54 QAR/m²** — within ±0.2% of Anas's pre-deploy
target of ~11,022.

### 5.10 README (BRIEF §7 step 6 — `2p21p4_brief/README.md`)

271 lines, 8 sections per spec. Verbatim D11 single-source caveat (9/9 key phrases including markdown formatting). 16-row schema column reference tracing each column to its D-decision. Status taxonomy table with D6 discounts + inference signals. Operator workflow per amended BRIEF §7 ordering. District placeholder warning with H1 vs H1' decision tree.

---

## 6. Engine integration diff (hybrid_valuation.py + connector + evaluate_unified.py)

### 6.1 Step numbering drift (carry-over)

Conversation step numbers diverged from BRIEF §7 step numbers because hybrid (BRIEF step 8) was completed before connector (BRIEF step 7). Both are topologically independent; only integration (BRIEF step 9) depends on both. Net mapping:

| Conversation step | BRIEF §7 step | Artifact |
|:---:|:---:|---|
| 7 | 8 | `hybrid_valuation.py` (status-aware T3 + freshness) |
| 8 | 7 | `connectors/developer_inventory_t3.py` (read-only fetcher) |
| 9 | 9 | `evaluate_unified.py` (`_try_hybrid_apartments_response` integration) |

No defect — both orderings are valid since the artifacts are independent. Documented for the record.

### 6.2 `hybrid_valuation.py` — the meaningful function-logic change (BRIEF step 8 / conv step 7)

**Five edits, +289 / −12 lines net:**

1. Added `import logging` + module-scope `logger = logging.getLogger("hybrid_valuation")` for T3 row-level data-integrity warnings.
2. `HYBRID_TIER_CONFIG`: scalar `T3_discount_midpoint` superseded by `T3_status_discount_map` dict + `T3_discount_default` scalar + `T3_stale_evidence_multiplier=0.5`. Scalar kept as back-compat alias (see §6.4).
3. New helper `_process_t3_input()` (~180 lines) — replaces the previous uniform-discount T3 path; performs shape detection, per-row discount, freshness annotation, and per-row breakdown emission. Details in §6.3.
4. `hybrid_valuation_v1` body: T3 normalisation replaced by `_process_t3_input` call; `t3_n_effective` (float; fresh=1.0, stale=0.5) passed to `_apply_tier_caps`; T3 tier_breakdown entry carries aggregate fields PLUS `sources[]` array of per-row 7-field dicts (D12 axis 18).
5. `_apply_tier_caps` `t3_n` type widened to `float` (Python's numeric promotion makes existing int callers pass through unchanged).

### 6.3 T3 input shape taxonomy (Step 7 carry-over #1 — three-shape, not BRIEF's two-shape)

The BRIEF §3.2 anticipated "list of bare floats (legacy shape)" but the actual Sprint 2.21.2 API used dicts. Reality has **three** input shapes, all supported by `_process_t3_input`:

| Shape | Detection | Discount path | Per-row breakdown |
|---|---|---|---|
| **dict_new** (Sprint 2.21.4) | dict contains `'status'` OR `'value_per_m2_raw'` | `T3_status_discount_map[row['status']]` per-row | ✅ 7-field per row |
| **dict_legacy** (Sprint 2.21.2) | dict contains `'value_per_m2'`, no `'status'` | `T3_discount_default` uniform | ❌ aggregate only |
| **float** (BRIEF §3.2 anticipated) | first element is `int`/`float` (not bool) | `T3_discount_default` uniform | ❌ aggregate only |
| **empty** | `None` or `[]` | n/a (no T3 contribution) | n/a |

Shape detection runs once per call against `t3_values[0]` after the empty-list guard. Mid-list shape inconsistency raises `ValueError` (Constraint 7 — would indicate a caller bug).

### 6.4 `T3_discount_midpoint` alias deprecation (Step 7 carry-over #2)

`HYBRID_TIER_CONFIG['T3_discount_midpoint']` is **retained** with the same `-0.175` value as before. Reason: Sprint 2.21.2 `tests/test_sprint_2p21p2_hybrid_foundation.py::test_15_t3_discount_math` reads this key directly to assert the discount value applied to a legacy-shape row. Per Step 7 spec §7 ("none of them should need modification"), preserving the alias was the chosen back-compat path.

The alias is now **deprecated semantically** — the function applies per-row discounts via `T3_status_discount_map`, NOT this scalar. Callers asking "what discount did the function apply?" should read the row-level `discount_applied` field in `tier_breakdown.sources[]` (dict_new shape) or the aggregate `tier_breakdown[T3].discount_applied` (legacy/float shape). The alias is documented in `HYBRID_TIER_CONFIG` itself with a `Sprint 2.21.2 → 2.21.4 back-compat alias` comment.

Future Sprint that wants to remove the alias should also update test_15 in the same Sprint (single-purpose discipline, Rule #38).

### 6.5 Sanity-band `ValueError` specifics (Step 7 carry-over #3)

`_process_t3_input` raises `ValueError` (does **not** WARN-and-skip) when a row's `value_per_m2_raw` falls outside `[100, 100_000]` QAR/m² (`HYBRID_TIER_CONFIG['value_per_m2_sanity_min'/'max']`). This is **Constraint 7** of Rule E3 — a unit-of-comparison tripwire.

**Relationship to importer-layer bands** (§5.6): the importer's `[100K, 1B]` price band + `[20, 5000]` m² area band protect insert-time data integrity (catching cents-vs-QAR or sqft-vs-sqm errors at the CSV boundary). The hybrid layer's `[100, 100_000]` QAR/m² band protects math-time unit integrity (catching whole-property-QAR or QAR/sqft sneaking through if a future code path bypasses the importer). The bands differ deliberately:

| Layer | Field | Band | Failure mode |
|---|---|---|---|
| Importer | `price_qar` | 100K – 1B | per-row rejection at CSV ingest |
| Importer | `area_m2` | 20 – 5,000 | per-row rejection at CSV ingest |
| Hybrid | `value_per_m2_raw` | 100 – 100,000 | `ValueError` at math time (would indicate caller bypassed importer) |

The hybrid-layer check **raises** (not WARN-skip) because a unit mismatch corrupts the entire weighted-median calculation, not just one row. Raise-and-fail is the correct response to a contract violation.

### 6.6 Connector (BRIEF step 7 / conv step 8 — `connectors/developer_inventory_t3.py`)

Read-only fetcher. `fetch_for_district(district, asset_type, status_filter, max_age_days, db_path, today)`. Returns `None` on every failure mode (empty result, missing DB, corrupt DB, schema drift, unsupported asset_type, empty status_filter). Returns `list[dict]` of exactly 8-field dicts matching the `hybrid_valuation_v1` dict_new shape.

**Lazy module-scoped connection** via `file:?mode=ro` SQLite URI. `atexit` handler closes the handle on process exit. `check_same_thread=False` for engine `ThreadPoolExecutor` compatibility.

**SUPPORTED_ASSET_TYPES = {'apartment', 'apartment_building'}** — `apartment_building` is canonical (Sprint 2.21.3 classifier output), `apartment` is defensive alias. Other asset types (villa, land, compound) return `None` at the gate (BRIEF §12 single-purpose).

`scripts/__init__.py` added so connector can import `DEFAULT_DB_PATH` from `scripts.migrate_developer_inventory` (Rule #40 single source of truth for the DB path).

### 6.7 Engine integration (BRIEF step 9 / conv step 9 — `evaluate_unified.py`)

Single surgical edit to `_try_hybrid_apartments_response`, between T2 fetch validation (line 1868) and `hybrid_valuation_v1` invocation:

```python
if os.getenv('T3_INVENTORY_ENABLED', 'true').lower() != 'false':
    try:
        from connectors.developer_inventory_t3 import fetch_for_district
        t3_rows = fetch_for_district(
            district=district_ar,
            asset_type=asset_type,
        )
    except Exception as e:
        print(f"[hybrid-apt] T3 connector failure: {e}", file=sys.stderr)
        t3_rows = None
else:
    t3_rows = None
```

Then `t3_values=None` → `t3_values=t3_rows` in the hybrid call.

**D10 flag** `T3_INVENTORY_ENABLED` defaults to `'true'` on first deploy; flip to `'false'` via `heroku config:set` for emergency rollback without code revert (mirrors Sprint 2.21.3's `HYBRID_APARTMENTS_ENABLED`).

**Defensive design**: any exception in the T3 path (import failure, connector exception, fetch error) yields `t3_rows = None` → hybrid runs with T2-only → response byte-shape identical to Sprint 2.21.3 baseline.

Smoke verified across 6 + H6 scenarios:
- Flag ON + 4 Aryan rows match: T3 weight = **0.12** (= 0.15 × 4/5, matches BRIEF §9 architectural seal), value_per_m2 = 11,628.56
- Flag=false, district mismatch, missing DB, non-apartment asset_type, `'لوسيل 69'` vs `'لوسيل'` micro-market mismatch, empty DB: all produce identical T2-only response (value_per_m2 = **11,571.88** — Sprint 2.21.3 baseline preserved by construction)

---

## 7. Test results

### 7.1 Sprint 2.21.4 isolated test suite — `tests/test_sprint_2p21p4_t3_inventory.py`

**26 functions / 26 PASS in 3.58s** (standalone runner; bare functions are pytest-discoverable too — pytest not currently installed on this dev env per CLAUDE.md, but the file is structured so it can be).

Coverage map to D12 axes 1–20:

| Axis | Test | Verifies |
|:---:|---|---|
| 1 | `test_01` + `test_01b` | Migration idempotent (3-run timestamp invariance) + verify_schema match |
| 2 | `test_02` | CSV clean row → 1 inserted, auto-computed value_per_m2 |
| 3 | `test_03` | Missing `unit_type` → `field='unit_type'` |
| 4 | `test_04` | Unknown column → `error_type='extra_forbidden'` |
| 5 | `test_05` | `area_m2='not_a_number'` → field='area_m2' float_parsing |
| 6 | `test_06` | `status='pending'` → field='status' |
| 7 | `test_07` | Upsert on revision (1.15M → 1.175M, 1 row, refreshed timestamps + recomputed value_per_m2) |
| 8-10 | `test_08/09/10` | Per-status discount routing (-17.5% / -17.5% / -10%) |
| 11-12 | `test_11/12/12b` | Freshness boundary + 0.5× n_effective + defensive stale on missing |
| 13 | `test_13` | Geo strict (Lusail seeded, Pearl query → None) |
| 14 | `test_14` | `T3_INVENTORY_ENABLED=false` → no T3 entry |
| 15-17 | `test_15/16/17` | Case A / B / C routing — B is the primary 2.21.4 path |
| 18 | `test_18` | T3 sources EXACTLY 7 fields per Rule E10 |
| 19 | `test_19` + `test_19b` | Empty DB + missing DB → None, no crash |
| 20 | `test_20` | Partial-population: `'لوسيل 69'` vs `'لوسيل'` seed → None (H11 prep) |

Bonus tests (carry-over closure):
- `test_21_integration_end_to_end` — full chain importer → DB → connector → hybrid → engine response, verifies T3 weight = 0.12 architectural seal
- `test_22_project_sentinel_normalization` — `'(unspecified)'` sentinel via field_validator (closes Step 2 NULL-UNIQUE soft-flag)
- `test_23_t3_discount_midpoint_alias_preserved` — back-compat alias equals `T3_discount_default` (Step 7 carry-over #2)

### 7.2 Full regression — 29-file standalone suite

**29 PASS / 0 FAIL** in 35.0s (Step 11 / Step 13 item 4 re-confirmed).

This includes:
- 13 root-level standalone tests (Sprint 2.16.6 through 2.16.15 + market regime / stock strata / etc.)
- 16 tests/ directory tests (Sprint 2.18 / 2.19 / 2.20 / 2.21 series + cap rate calibrator + factors + MoJ + the new 2.21.4 file)

Notable preservation: `tests/test_sprint_2p21p2_hybrid_foundation.py` (67/67) — verified the hybrid changes maintain back-compat via the `T3_discount_midpoint` alias.

### 7.3 Pre-deploy 6-item checklist (Operational_Rules §3)

| # | Item | Status | Evidence |
|:---:|---|:---:|---|
| 1 | `py_compile` all modified Python files | ✅ | 7 files: evaluate_unified.py + hybrid_valuation.py + scripts/{migrate,import,__init__}.py + connectors/{developer_inventory_t3,__init__}.py |
| 2 | `node --check` on modified JS | N/A | No JS touched in Sprint 2.21.4 |
| 3 | Mobile viewport test 390×844 | N/A | No UI work — Sprint 2.21.5 owns `tier_breakdown` rendering |
| 4 | Regression 29/29 | ✅ | Step 11 + Step 13 item 4 both green |
| 5 | New isolated tests | ✅ | 26/26 PASS in 3.58s |
| 6 | Smoke plan for 3 diverse addresses post-deploy | Pending Step 19 | H1 anchor PIN 69/329/20 (Lusail, City Avenues row sees this OR H1' contingency); H2 flag-off control; H6 H11 H9 covered by isolated tests |

---

## 8. Predicted post-deploy behavior (BRIEF §5 hypotheses H1–H11)

| # | Hypothesis (condensed) | Falsified by |
|---|---|---|
| **H1** | **PIN 69/255/75** (City Avenues H1 anchor — see §8.1 below) → `tier_breakdown` with T3 (Aryan, n=4); per-row `status='under_construction'`, `discount_applied=-0.175`, `value_per_m2_adjusted ≈ 10,957–11,082` (cluster median 11,040.54); effective T3 weight ≤ 0.12 (= 0.15 cap × 4/5 evidence). Pre-deploy correction §5.8 — `under_construction` confirmed empirically, replacing the original `ready` inference. | Missing T3 row OR wrong discount (not -0.175) OR weight > 0.12 OR T3 absent despite imported rows. |
| **H1'** | **GIS-contingency CLOSED** — Step 14 GIS verification (2026-05-25) returned canonical district `'لوسيل 69'` (DIST_NO 812) for City Avenues centroid; H1 is active, H1' contingency NOT invoked. Documented for historical record in §13. | n/a — closed. |
| **H2** | City Avenues PIN (or 69/329/20 in H1' path) with `T3_INVENTORY_ENABLED=false` → response identical-shape to 2.21.3 baseline (no T3 row). | T3 row leaks despite flag off. |
| **H3** | Empty `developer_inventory.sqlite` table (isolated-test fixture, OR future state with schema but no matching rows for the queried micro-market) → apartment evaluation does NOT crash; T2-only response. | NameError, crash, or 500 on apt eval with empty table. |
| **H4** | CSV import of the 4 City Avenues rows succeeds **LOCALLY** (Step 16); populated `developer_inventory.sqlite` committed to git (Step 17); **all 4 rows visible in the deployed slug post-Step 18**; next `/api/evaluate` at City Avenues PIN picks them up with `discount_applied=-0.10`. | Any row rejected locally OR `.sqlite` not committed OR rows missing in deployed slug OR not picked up by engine OR wrong discount. |
| **H5** | Malformed CSV row (missing required field per D4 / unknown column / wrong type / invalid status enum) → REJECTED with structured per-row error containing field name. | Silent acceptance OR generic error without field name. |
| **H6** | 28-file regression suite PASSES unchanged (2.21.3 Lusail hybrid flow returns same output when `developer_inventory.sqlite` empty). | Any regression failure. |
| **H7** | New ≥20-function test suite (D12 axes) — all PASS. | Coverage gap on any axis. |
| **H8** | Stale row (`last_verified_at` > 90 days ago, status=`off_plan`) → `tier_breakdown` entry shows `freshness_status: 'stale'` AND contribution at 0.5× fresh-row weight. | Stale rows treated as fresh OR silently excluded OR annotation missing. |
| **H9** | Geo filter: Pearl apt evaluation does NOT pick up Lusail T3 rows. | T3 leaks across districts. |
| **H10** | Anas's visual verification on thammen.qa for H1 anchor PIN: tier_breakdown UI shows developer + project + status + discount per T3 row (Rule E10). | UI shows generic "T3" without developer / project / status disclosure. |
| **H11** | **Partial-population negative test.** Aryan has rows only in City Avenues. Lusail Marina apt PIN (or any Lusail PIN whose micro-market doesn't match City Avenues) → T2-only response; shape matches 2.21.3 baseline. | T3 row appears with zero matching units OR shape diverges from baseline. |

**Most consequential predictions:** **H1** (Sprint delivers its core value
— T3 lights up alongside T2 with correct per-row math), **H6** (no
regression to 2.21.3-and-earlier paths), **H2** (flag rollback restores
baseline cleanly).

**Failure protocol (BRIEF §6):** if H1/H6/H2 fail → `heroku config:set T3_INVENTORY_ENABLED=false` immediately (Rule #11). If schema/data corruption suspected → separate explicitly-consented investigation, NOT `DELETE FROM developer_inventory` as rollback (BRIEF §6 explicitly removed this from the rollback plan per prohibited-actions discipline).

### 8.1 H1 / H11 anchor PINs (resolved pre-deploy 2026-05-25)

| Hypothesis | Anchor PIN | Zone/Street/Building | District (GIS ANAME) | Subtype | Distance from City Avenues centroid |
|---|---|---|---|---|---|
| **H1** (T3 fires) | **69051988** | **69/255/75** | `لوسيل 69` (DIST_NO 812) | 6 (apartment_building) | 184.1 m |
| **H11** (T3 absent, partial-population negative) | 69045xxx | 69/329/20 (Fox Hills) | `غار ثعيلب` | 6 (apartment_building) | n/a — different sub-district |

**Resolution method** (Pre-Step-16, 2026-05-25): khazna QARS_Point spatial
envelope query (~200m radius) at City Avenues centroid (25.43128706407143,
51.489247481728576). Single QARS match returned; cross-verified subtype=6
= apartment_building per Sprint 2.16.6 Branch 0 classifier table.

**Why 69/329/20 is the natural H11 anchor**: City Avenues + 4 Aryan rows
are seeded under district `'لوسيل 69'`. 69/329/20 resolves to
`'غار ثعيلب'` (different Lusail sub-district per Sprint 2.21.3 D10 token
set). The T3 connector does exact string match on `district`, so a query
at 69/329/20 yields T2-only (no T3 row in tier_breakdown) — the partial-
population negative test fires naturally without needing a synthetic
fixture.

H1' GIS-contingency closed (§13 timeline).

---

## 9. Anas review gate (BRIEF §7 task list — post-amendment ordering 2026-05-25)

The BRIEF §7 step ordering was amended at review time to reflect Heroku's
ephemeral filesystem: importer runs LOCALLY → populated `.sqlite` committed
→ deploy → post-deploy walk. Five hold-points:

1. **GIS verification (BRIEF §7 step 14)** — runs in-Sprint, ~2 min; result decides H1 vs H1' routing. Surface result in §13 before Step 15. **District value baked into seed CSV** before importer runs.
2. **Anas sign-off (BRIEF §7 step 15)** — review CHANGELOG_v49.md + all build artifacts (§5 schema/importer evidence, §6 engine diff, §7 test results) before any local importer run OR git push. Rule #32 push discipline. **Default = do NOT push without explicit consent in the message thread.**
3. **Local importer run (BRIEF §7 step 16, amended)** — run `scripts/import_developer_inventory.py` against the populated CSV on local machine. Verify 4 rows in `developer_inventory.sqlite`. None rejected. Per-row error structure honoured for any rejected rows (Rule #31).
4. **Commit + deploy (BRIEF §7 steps 17-18, amended)** — `git add` populated `developer_inventory.sqlite` alongside the code changes; single Sprint commit; `git subtree push --prefix "deploy v2" heroku master`. Slug ships with the .sqlite populated. Rationale: Heroku filesystem is ephemeral; the importer cannot run post-deploy with persistence. Pattern mirrors `building_age_cache.sqlite` (Sprint 2.15.1).
5. **Post-deploy verification (BRIEF §7 step 19, renumbered)** — H1–H11 walked one by one against the deployed slug. Each result captured inline in §13. Memory hygiene checkpoint (formerly step 19) becomes step 20.

---

## 10. Single-source caveat — architectural acknowledgement (BRIEF §9)

Three mechanisms protect against single-source correlation in T3:

1. **Tier weight cap = 0.15** (`HYBRID_TIER_CONFIG.T3_weight_cap`). At most 15% of weighted-median contribution from T3 regardless of row count.
2. **Evidence-strength cap at n=5** (`T3_evidence_strength_full_cap_at_n`). Adding the 6th, 7th, …, 20th Aryan row does NOT increase T3 confidence past n=5 saturation. With Aryan's 4 City Avenues rows: evidence_strength = 4/5 = 0.8 → effective T3 weight ceiling = 0.15 × 0.8 = **0.12**.
3. **Case C refusal** (Rule E3 Constraint 8). T3 alone never produces a valuation — `hybrid_valuation_v1` returns `value_per_m2: None, confidence: fallback`.

User-facing surfacing: D11 verbatim caveat in `2p21p4_brief/README.md` +
`role_ar = "مخزون مطوّر — {developer}"` in tier_breakdown rows.

---

## 11. Practical T3 density note (BRIEF §10)

Sprint 2.21.4 ships with **4 seed rows from 1 developer (Aryan) in 1
project (City Avenues)**. This is intentional. The Sprint's deliverable
is the **infrastructure** (schema + importer + engine plug-in + tests +
UI surfacing path) — NOT market-density T3 coverage. Real T3 density
grows through subsequent data-only Sprints (2.21.4.1, 2.21.4.2, …) as
more developer-direct inventory is captured. The `developer_inventory`
table being sparse at v124+1 is **by design, not oversight**.

---

## 12. Rules cited / applied in this Sprint

- **Rule #11** rollback protocol — `T3_INVENTORY_ENABLED=false` is first-line response if H1/H6/H2 fail post-deploy.
- **Rule #31** Pydantic `extra='forbid'` — applied to CSV importer schema (D8). Per-row reject with field name in error.
- **Rule #32** push & commit discipline — no `git subtree push` without Anas's explicit consent in the message thread.
- **Rule #34** file-based scripts — `scripts/migrate_developer_inventory.py` + `scripts/import_developer_inventory.py` are standalone files. No `heroku run python -c …` inline.
- **Rule #38** single-purpose Sprint — Aryan-only (no UDC / Qetaifan / etc.). Apartments-only (Scala Qetaifan villas PARKED per BRIEF §12). Lusail-only.
- **Rule #39** deviation justification — D4/D7/D8/D9 amendments each documented above with `why necessary` + `what changes` + `what reviewer needs to know`.
- **Rule #40** replica + production verification — test suite imports real production modules; mocks scoped to SQLite + filesystem boundaries only.
- **Rule #43** Heroku deploy via `git subtree push --prefix "deploy v2"`.
- **Rule #50** staged-Sprint discipline — Sprint 2.21.4 is **Stage 1 of T3** (manual entry, single developer, single geo). Stage 2 (multi-developer / multi-geo data-only Sprints) and Stage 3 (T3-villas, future) are pre-specified in BRIEF §8 + §12.
- **Rule #51** audit-driven Sprint pattern — Pre-Sprint design analysis ([`2p21p4_pre/`](2p21p4_pre/)) fed BRIEF; post-deploy H1–H11 verifies the predictions.
- **Rule #53** closed cases stay closed — Sprint 2.16.16 referenced via §X / Rule, not re-litigated. The fold-in question (Q6) was deferred cleanly.
- **Rule E3** (8 constraints, Sprint 2.21.2) — Constraint 2 (T3 cap 0.15 + D6 discount); Constraint 4 (no T1 → indicative ceiling); Constraint 5 (mandatory MUC); Constraint 6 (source-level transparency); Constraint 7 (like-for-like unit normalization); Constraint 8 (T3-alone refused — Case C).
- **Rule E10** transparent source attribution — `tier_breakdown` T3 rows carry the 7-field shape: `developer`, `project`, `status`, `value_per_m2_raw`, `discount_applied`, `value_per_m2_adjusted`, `freshness_status` (D12 axis 18).
- **Rule E13** pull coded-value domains — applied via GIS verification step 14 (City Avenues canonical ANAME).

---

## 13. Post-deploy verification timeline

*To be filled per BRIEF §7 steps 14, 16, 17, 18, 19. Mirrors v48 §12
timeline format (Heroku release → engine/config → event).*

---

*Opened 2026-05-25 post BRIEF_2p21p4_FINAL sign-off. Will be updated as
the Sprint progresses through BRIEF §7 steps 2–19. Format mirrors v48
(Sprint 2.21.3 T2 Lusail apartments hybrid). Step 1 STOPS HERE pending
Anas review before Step 2 (DDL).*
