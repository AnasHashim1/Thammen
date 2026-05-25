# developer_inventory — Sprint 2.21.4 operator README

> **For:** anyone capturing developer-direct inventory rows into
> `developer_inventory.sqlite` (the T3 tier of Thammen's hybrid
> valuation framework).
>
> **Read these first if you need architectural context:**
> - [`../BRIEF_2p21p4_FINAL.md`](../BRIEF_2p21p4_FINAL.md) — D1–D12
>   decisions, H1–H11 hypotheses, scope statement.
> - [`../CHANGELOG_v49.md`](../CHANGELOG_v49.md) — what landed in
>   Sprint 2.21.4 and why.

---

## 1. What this is

`developer_inventory.sqlite` is a CSV-driven SQLite table that holds
**T3-tier** asking-side evidence — units listed directly by a developer
or their authorised broker, captured manually by Thammen staff. The
engine reads it via `connectors/developer_inventory_t3.py` and passes
the rows into `hybrid_valuation_v1()` as `t3_values=...` alongside the
T2 PropertyFinder listings from Sprint 2.21.3.

Tier semantics in one line:

> **T1** = registered transactions (MoJ / MME) — ground truth.
> **T2** = vetted public listings (PropertyFinder, arady, FGRealty).
> **T3** = developer-direct inventory (this file). One informed party.
> **T5** = excluded (bayut, mzadqatar).

T3 is **single-source** by definition — see the caveat below.

---

## 2. Single-source caveat (verbatim per BRIEF §2 D11)

> **Single-source caveat.** Rows in `developer_inventory.sqlite` come
> from one developer at a time. n rows from one developer do NOT
> constitute an n-sample market signal — they are one informed party's
> price-setting. The T3 tier weight cap (0.15) and the
> `T3_evidence_strength_full_cap_at_n=5` parameter reflect this in the
> math. Treat T3 as informational evidence, not a market sample. UI
> surfaces this caveat to the end user via the tier_breakdown row's
> `role_ar` and tooltip.

Practical consequences for the operator:

- Adding the 6th, 7th, …, 20th row from the same developer does NOT
  improve the engine's confidence past the n=5 saturation point.
- T3 alone never produces a valuation — `hybrid_valuation_v1` refuses
  (Case C per Rule E3 Constraint 8) and returns `value_per_m2: None`.
  T3 must accompany T2 (or T1) to contribute.
- Effective T3 weight ceiling with the current 4 Aryan / City Avenues
  rows = `0.15 × (4/5) = 0.12`. With 5 or more rows from one developer
  it caps at 0.15. There is no row count that lifts T3 above 0.15.

---

## 3. Workflow — BRIEF §7 amended ordering (2026-05-25)

Heroku's slug filesystem is ephemeral. A write performed by
`heroku run python scripts/import_developer_inventory.py …` would land
on a dyno-local FS that gets wiped on the next restart. **The importer
runs LOCALLY and the populated `.sqlite` is committed to git** before
deploy. Same architectural pattern as `building_age_cache.sqlite`
(Sprint 2.15.1 — 62 PINs of imagery analysis cached in the repo).

### Step-by-step (numbered per BRIEF §7 amended)

| # | Action | Who | Where |
|---|---|---|---|
| 14 | GIS verification of the project centroid → canonical district ANAME → update CSV's `district` column | Anas (or Claude Code with PIN) | local |
| 15 | Sign-off on the CSV + CHANGELOG | Anas | local |
| 16 | `python scripts/import_developer_inventory.py <your.csv>` | Anas (or whoever holds sign-off) | local |
| 17 | `git add developer_inventory.sqlite <your.csv> [CHANGELOG]` → single Sprint commit | local | git |
| 18 | `git subtree push --prefix "deploy v2" heroku master` | Anas (Rule #32 — explicit consent) | Heroku |
| 19 | Post-deploy H1–H11 verification walk against deployed slug | Anas + Claude Code | thammen.qa |
| 20 | Memory hygiene checkpoint (Sprint closes) | Anas + Claude Code | local docs |

### Why the importer runs locally, not on Heroku

Three reinforcing reasons:

1. **Ephemeral filesystem.** Heroku dynos restart at least daily; any
   `.sqlite` written by a one-off `heroku run` is gone on next restart.
   Data must be in the slug, not in the runtime FS.
2. **Auditability.** Git tracks every change to
   `developer_inventory.sqlite`. The commit history is the data
   change log.
3. **Precedent.** `building_age_cache.sqlite` follows this exact
   pattern (Sprint 2.15.1). The migration runner + importer for T3
   mirror that pattern.

---

## 4. District placeholder warning ⚠

The shipped template (`scripts/developer_inventory_template.csv`)
uses `district=لوسيل` as a **placeholder**. It exists so the file
parses cleanly and the auto-compute pipeline (price_qar / area_m2)
can be verified in dry-run.

**For production import, Step 14 GIS verification is mandatory:**

1. Determine the GPS centroid of the project (City Avenues, Scala
   Qetaifan, whichever).
2. Spatially query `Vector/Districts/MapServer/0` at that centroid
   (per `Project_Instructions.md` §12).
3. Read the canonical `ANAME` returned by GIS.
4. **Replace `لوسيل` in every row of your CSV with whatever GIS
   returns** (verbatim — do not substitute marketing names).

Decision tree on GIS result:

- GIS returns `لوسيل` (or another known Lusail sub-district per the
  Sprint 2.21.3 D10 token set: `'لوسيل'`, `'غار ثعيلب'`) → import
  proceeds normally; **H1** is the active post-deploy hypothesis.
- GIS returns a non-Lusail district (e.g. `الدفنة`, `جزيرة اللؤلؤة`,
  …) → import still proceeds with the GIS-canonical district BUT the
  rows will not activate in current valuation pathways (2.21.3's T2
  connector is Lusail-only; hybrid Case C refusal applies). **H1'
  contingency** activates: insert one synthetic Lusail row by direct
  INSERT (NOT importer) for the H1 verification, DELETE after test,
  and document the contingency in CHANGELOG_v49 §13.

---

## 5. Example commands (copy-paste)

Examples below assume `cwd = C:\Thammen\deploy v2`. Native shells:
**Windows `cmd`** (Anas's environment) and **bash** (cross-platform).
Python path module accepts either separator; the commands are
functionally identical.

### 5.1 Apply / verify schema (idempotent)

Windows cmd:
```
cd /d "C:\Thammen\deploy v2"
python scripts\migrate_developer_inventory.py
```

bash:
```
cd "/c/Thammen/deploy v2"
python scripts/migrate_developer_inventory.py
```

Expected on a fresh DB:
```
[migrate] Phase 1: executescript completed (idempotent)
[migrate] Phase 2: schema verify OK
[migrate] Phase 3: stamped developer_inventory_schema_version=1, …
[migrate] DONE: schema_version='1', last_migration_run_at=…
```

Expected on subsequent runs (true no-op):
```
[migrate] Phase 2: schema verify OK
[migrate] Phase 3: version already at 1 — no write (true no-op)
[migrate] DONE: schema_version='1', last_migration_run_at=<unchanged>
```

### 5.2 Import the shipped template (sanity)

```
python scripts\import_developer_inventory.py scripts\developer_inventory_template.csv
```

Expected:
```
[import] rows seen:   1
[import] inserted:    1
[import] updated:     0
[import] rejected:    0
[import] OK: all 1 rows imported (inserted=1, updated=0).
```

### 5.3 Import a real inventory CSV (dry-run first)

Dry-run validates every row without writing:
```
python scripts\import_developer_inventory.py inventory.csv --dry-run
```

If dry-run is clean, apply for real:
```
python scripts\import_developer_inventory.py inventory.csv
```

### 5.4 Capture structured rejections to a file

When a real CSV has rejections, write them to JSON for inspection:
```
python scripts\import_developer_inventory.py inventory.csv --rejections-log rejections.json
```

The JSON contains one entry per rejected row with `row_num`, `field`,
`reason`, `error_type`, `raw_row`, and `all_errors`. Fix the source
CSV using those entries and re-run. Exit code is `1` whenever any
rejection occurred — the operator must explicitly re-run to clear.

### 5.5 Use a non-default DB path (for tests / scratch)

```
python scripts\migrate_developer_inventory.py --db-path C:\tmp\scratch.sqlite
python scripts\import_developer_inventory.py inventory.csv --db-path C:\tmp\scratch.sqlite
```

---

## 6. Schema column reference (16 columns)

Trace each column back to its BRIEF §2 D-decision without re-reading
the BRIEF:

| # | Column | Type | Status | D-ref | Note |
|---:|---|---|---|---|---|
| 1 | `developer` | TEXT | **required** | D4 | Free-text. Tier classification is T3 regardless of identity. |
| 2 | `district` | TEXT | **required** | D4 | Canonical GIS ANAME from Step 14 verification. NOT a marketing name. |
| 3 | `unit_type` | TEXT enum | **required** | D4 amended | Must be one of `studio | 1BR | 2BR | 3BR | 4BR | penthouse`. Maid-room variants go in `notes_ar`. |
| 4 | `area_m2` | REAL | **required** | D4 | BUA for apartments. Sanity band `[20, 5000]` enforced by importer. |
| 5 | `price_qar` | INTEGER | **required** | D4 | Headline price. Sanity band `[100K, 1B]` enforced by importer. |
| 6 | `status` | TEXT enum | **required** | D4 + D6 | Must be one of `off_plan | under_construction | ready`. Drives the discount routing — see §7 status taxonomy. |
| 7 | `captured_at` | TEXT (ISO date) | **required** | D4 | First-capture date. NEVER updated on upsert. |
| 8 | `project` | TEXT | optional | D5 | Project name. Empty / NULL → sentinel `(unspecified)` via importer (D8 NULL-aware UNIQUE fix). |
| 9 | `sub_area` | TEXT | optional | D5 | Marketing sub-area within the district (e.g. "Marina District"). |
| 10 | `completion_year` | INTEGER | optional | D5 | Expected handover for off_plan / under_construction. NULL when ready or unknown. Range `[2020, 2050]`. |
| 11 | `payment_plan_summary` | TEXT | optional | D5 | Short human-readable plan ("أقساط حتى 7 سنوات" / "cash only"). |
| 12 | `source_url` | TEXT | optional | D5 | Public URL if any. NULL for private/internal sources (Aryan). |
| 13 | `captured_by` | TEXT | optional | D5 | anas / secretary / consultant name. Audit trail. |
| 14 | `last_verified_at` | TEXT (ISO date) | optional | D5 + D7 | 90-day freshness TTL applied at connector. Stale rows get `freshness_status='stale'` + 0.5× evidence weight. |
| 15 | `notes_ar` | TEXT | optional | D5 | Arabic free-text. Substring `مساحة مقدرة` is the audit anchor for back-derived areas. |
| 16 | `value_per_m2` | REAL | **auto-computed** | D5 +1 | Leave blank in CSV; importer sets `round(price_qar / area_m2, 2)` via pydantic `model_validator(mode='after')`. |

D8 composite uniqueness: `UNIQUE (developer, project, unit_type, area_m2)`
— `price_qar` deliberately excluded so a price revision upserts the
existing row rather than creating a duplicate.

---

## 7. Status taxonomy (D6)

The `status` column drives per-row discount in `hybrid_valuation_v1`.
Tier classification stays T3 in all three cases — tier reflects
source independence, not occupiability.

| status | Discount (D6) | When to use | Inferred from |
|---|---:|---|---|
| `off_plan` | `−17.5%` | Project sold before construction begins; long handover horizon. Includes the off-plan-to-resale gap. | Long installment horizon (e.g. payments through 2034); pre-handover marketing; no visible construction; sales centre / brochure only. |
| `under_construction` | `−17.5%` | Construction visibly underway but units not yet handover-eligible. Same discount as off_plan — partial completion does not eliminate delivery risk. | Visible construction on-site; phased payment plans tied to milestones; partial completion percentage published. |
| `ready` | `−10%` | Units handover-eligible; no delivery risk. Only the negotiation component of the discount applies (no off-plan-to-resale gap). | Handover already happening; "last unit remaining" or "few units left" inventory patterns; short installment horizon compressed vs off-plan signature; key-ready visits offered. |

**Edge case — first-of-its-kind project**: when in doubt and the
developer hasn't stated explicitly, lean toward the more cautious
discount (`off_plan` or `under_construction` → −17.5%). The 0.15 ×
evidence_strength cap means the effect of mis-status is bounded;
worst-case mis-classification (ready → off_plan) costs ≈ 0.9% of
final value per BRIEF §11.2 Assumption 2.

---

## 8. BOM handling

Template ships with UTF-8 BOM for Excel autodetect on Arabic columns.
Importer uses `utf-8-sig` for robust decoding either way.

---

*Sprint 2.21.4. Maintainer: Anas / Claude Code. Last updated 2026-05-25.*
