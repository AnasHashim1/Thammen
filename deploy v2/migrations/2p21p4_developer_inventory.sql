-- =============================================================================
-- Sprint 2.21.4 — migrations/2p21p4_developer_inventory.sql
-- DDL for the T3 developer-inventory tier (Aryan first seed, Lusail first geo).
--
-- BRIEF reference: BRIEF_2p21p4_FINAL.md §2 (D-decisions registry).
-- CHANGELOG reference: CHANGELOG_v49.md §1 (D1-D12).
--
-- Decisions encoded in this file:
--   D2  table name + file location  (developer_inventory in developer_inventory.sqlite)
--   D3  per-unit row granularity
--   D4  AMENDED required fields incl. unit_type (enum CHECK)
--   D5  RATIFIED + value_per_m2 auto-computed by importer (stored redundantly)
--   D6  status enum (off_plan | under_construction | ready) — discount handling
--       lives in hybrid_valuation.py, NOT here; this file only enforces the enum
--   D7  last_verified_at column present; freshness logic in connector + hybrid
--   D8  AMENDED UNIQUE (developer, project, unit_type, area_m2) — price_qar
--       deliberately EXCLUDED so price revisions upsert (single row, latest
--       price, refreshed last_verified_at) rather than double-count the same
--       underlying inventory unit
--
-- Idempotency (D12 axis 1): every CREATE uses IF NOT EXISTS. Running this file
-- twice produces no error and no duplicate columns. The migration runner
-- (scripts/migrate_developer_inventory.py, Step 3) verifies the live schema
-- matches the DDL after each run.
--
-- SQLite flavour notes:
--   - Date/time stored as TEXT in ISO-8601 (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS).
--   - Enums enforced via CHECK (column IN (...)). Adding a new enum value in a
--     later Sprint requires either a new CHECK migration or a SQLite-style
--     table recreate (PRAGMA writable_schema + reload).
--   - UNIQUE with a NULLable column (project): SQLite treats multiple NULLs as
--     distinct under UNIQUE — so two rows where project IS NULL but everything
--     else matches WILL coexist. Aryan's seed data has project='City Avenues'
--     (NOT NULL) so this is harmless for v1. Future Sprints that seed rows
--     without a project value should set project='' or a developer-canonical
--     default to keep the UNIQUE constraint meaningful.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Main table: developer_inventory
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS developer_inventory (
    -- Surrogate primary key (Sprint 2.21.4 convention; mirrors
    -- building_age_cache.sqlite's PIN-keyed pattern adapted for non-PIN data).
    listing_id           INTEGER PRIMARY KEY AUTOINCREMENT,

    -- =========================================================================
    -- REQUIRED FIELDS (D4 AMENDED)
    -- =========================================================================

    -- Developer / source identity. Free-text to allow any developer or broker
    -- string. Tier classification is T3 regardless of identity (Rule E3 §2).
    developer            TEXT    NOT NULL,

    -- Canonical GIS district ANAME — set by importer using the GIS verification
    -- step (BRIEF §7 step 14). Free-text because GIS Districts ANAME is
    -- arbitrary Arabic; we cannot enum it.
    district             TEXT    NOT NULL,

    -- Unit-type enum (D4 amended — maid-room variants encoded in notes_ar).
    unit_type            TEXT    NOT NULL
        CHECK (unit_type IN ('studio', '1BR', '2BR', '3BR', '4BR', 'penthouse')),

    -- Area in m² (BUA for apartments). REAL because m² values can be
    -- fractional (e.g. 91.56). Strict positive guard.
    area_m2              REAL    NOT NULL
        CHECK (area_m2 > 0),

    -- Headline price in QAR. INTEGER because we never need fractional QAR.
    -- 100K floor is enforced at the importer layer (matches connector
    -- sales-band sanity); we keep DDL-level guard at >0 to avoid blocking
    -- future test fixtures or non-apartment seeds.
    price_qar            INTEGER NOT NULL
        CHECK (price_qar > 0),

    -- Status enum (D6) — discount routing lives in hybrid_valuation.py.
    status               TEXT    NOT NULL
        CHECK (status IN ('off_plan', 'under_construction', 'ready')),

    -- ISO-8601 date (YYYY-MM-DD). When the row was first captured / imported.
    captured_at          TEXT    NOT NULL,

    -- =========================================================================
    -- OPTIONAL FIELDS (D5 RATIFIED + 1 ADDITION)
    -- =========================================================================

    -- Project / development name (e.g. "City Avenues", "Scala Qetaifan").
    -- Part of the UNIQUE composite — see bottom of CREATE statement.
    project              TEXT,

    -- Marketing sub-area within the district (e.g. "Marina District",
    -- "Fox Hills"). Free-text. Not part of UNIQUE.
    sub_area             TEXT,

    -- Expected handover year for off_plan / under_construction units.
    -- NULL when status='ready' or unknown.
    completion_year      INTEGER
        CHECK (completion_year IS NULL OR completion_year BETWEEN 2020 AND 2050),

    -- Short human-readable payment plan ("أقساط حتى 7 سنوات", "30% down",
    -- "cash only"). Free-text, Arabic OK.
    payment_plan_summary TEXT,

    -- Source URL for the listing (developer website, brochure PDF, broker
    -- portal). NULL when source is offline-only (e.g. private/internal —
    -- Aryan first seed, per Q1+Q2 answer).
    source_url           TEXT,

    -- Who captured the row (anas / secretary / consultant name).
    captured_by          TEXT,

    -- Last freshness verification — ISO-8601 date. 90-day TTL applied at the
    -- connector layer (BRIEF §7 D7); stale rows enter hybrid with
    -- freshness_status='stale' AND 0.5× evidence-strength multiplier.
    last_verified_at     TEXT,

    -- Arabic free-text notes. The "مساحة مقدرة" substring is reserved as the
    -- audit-trail anchor for back-derived areas (BRIEF §11.2 Assumption 1).
    notes_ar             TEXT,

    -- AUTO-COMPUTED at import (D5 addition): price_qar / area_m2. Stored
    -- redundantly so the connector can read value_per_m2 directly without
    -- recomputing. The importer enforces the equality:
    --   value_per_m2 = round(price_qar / area_m2, 2)
    -- Manual SQL inserts that violate this will not be flagged by the DDL —
    -- the importer is the single canonical write path (Rule #31 strict).
    value_per_m2         REAL
        CHECK (value_per_m2 IS NULL OR value_per_m2 > 0),

    -- =========================================================================
    -- COMPOSITE UNIQUENESS (D8 AMENDED)
    -- =========================================================================
    --
    -- price_qar is DELIBERATELY EXCLUDED from this composite.
    -- Rationale (BRIEF §2 D8): with price_qar in the key, a price revision on
    -- the same offered unit produces a NEW row. The old row keeps its
    -- last_verified_at, decays to stale after 90 days, but never disappears
    -- — and during the first 60-89 days BOTH rows count as fresh in the
    -- T3 median, silently double-counting the same underlying inventory.
    -- Correct semantics: revision UPSERTS the existing row, updating
    -- price_qar + last_verified_at + value_per_m2.
    --
    -- The importer uses ON CONFLICT DO UPDATE keyed on this composite.

    UNIQUE (developer, project, unit_type, area_m2)
);


-- -----------------------------------------------------------------------------
-- 2. Indexes for connector query patterns (developer_inventory_t3.fetch_for_district)
-- -----------------------------------------------------------------------------
--
-- The fetcher's primary query shape (BRIEF §3.1):
--   WHERE district = ?  AND status IN (?, ?, ?)
-- Index on (district, status) supports this directly.
--
-- Secondary query (future TTL purge / freshness sweep):
--   WHERE last_verified_at < ?
-- Single-column index on last_verified_at supports this.
--
-- Not over-indexing: 4 seed rows make any index moot at v124+1. These exist
-- so the table scales gracefully as the data-only Sprints (2.21.4.1+) grow
-- the row count.

CREATE INDEX IF NOT EXISTS idx_developer_inventory_district_status
    ON developer_inventory (district, status);

CREATE INDEX IF NOT EXISTS idx_developer_inventory_last_verified
    ON developer_inventory (last_verified_at);


-- -----------------------------------------------------------------------------
-- 3. Schema metadata table (idempotency support for the migration runner)
-- -----------------------------------------------------------------------------
--
-- The migration runner (Step 3) reads schema_meta.developer_inventory_version
-- to determine whether this DDL has been applied. The runner INSERTS the
-- version row after a successful apply; this file does NOT insert the row,
-- because the migration runner is the canonical idempotency gate (a manual
-- sqlite3 < this.sql session must still be auditable by the runner).

CREATE TABLE IF NOT EXISTS schema_meta (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    applied_at  TEXT NOT NULL
);


-- =============================================================================
-- End of 2p21p4_developer_inventory.sql
-- =============================================================================
