"""
test_sprint_2p21p4_t3_inventory.py — Sprint 2.21.4 Step 10

Covers D12 axes 1–20 (BRIEF §2 D12) + one engine-integration end-to-end
test. Bare functions named `test_*` for pytest auto-discovery; standalone
runner at __main__ for the project's existing regression-runner pattern
(`python tests/test_*.py` per file, no pytest install required).

Rule #40 discipline: every test imports REAL production symbols.
- scripts.migrate_developer_inventory  → schema migration + verify
- scripts.import_developer_inventory   → InventoryRow, import_csv, helpers
- connectors.developer_inventory_t3   → fetch_for_district, _compute_freshness
- hybrid_valuation                     → hybrid_valuation_v1, HYBRID_TIER_CONFIG
- evaluate_unified                     → _try_hybrid_apartments_response

Fixtures via @contextmanager — work in both pytest and standalone modes.

Run:
  python tests/test_sprint_2p21p4_t3_inventory.py
  pytest tests/test_sprint_2p21p4_t3_inventory.py -v   (if pytest installed)
"""
from __future__ import annotations
import os
import sqlite3
import sys
import tempfile
import time
from contextlib import closing, contextmanager
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

# Make project root importable
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# ── Production imports (Rule #40) ────────────────────────────────────
from scripts.migrate_developer_inventory import (
    migrate, verify_schema,
    SCHEMA_VERSION, SCHEMA_KEY, LAST_RUN_KEY,
    EXPECTED_COLUMNS_DEVELOPER_INVENTORY, EXPECTED_UNIQUE_COLUMNS,
    DEFAULT_DDL_PATH,
)
from scripts.import_developer_inventory import (
    InventoryRow, import_csv, make_rejection, upsert_row,
    PROJECT_SENTINEL_UNSPECIFIED, UPSERT_SQL,
    ALLOWED_UNIT_TYPES, ALLOWED_STATUSES,
)
from connectors import developer_inventory_t3 as t3
from connectors.developer_inventory_t3 import (
    fetch_for_district, _compute_freshness,
    DEFAULT_TTL_DAYS, SUPPORTED_ASSET_TYPES,
)
from hybrid_valuation import hybrid_valuation_v1, HYBRID_TIER_CONFIG

import evaluate_unified


# ─────────────────────────────────────────────────────────────────────────
# Fixtures (contextmanager-based — pytest-compatible, standalone-compatible)
# ─────────────────────────────────────────────────────────────────────────

@contextmanager
def temp_db():
    """Yield a path to a freshly-migrated developer_inventory.sqlite."""
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "dev.sqlite"
        migrate(db_path, DEFAULT_DDL_PATH, dry_run=False, verbose=False)
        t3._close_db_connection()   # ensure connector picks up this DB
        try:
            yield db_path
        finally:
            t3._close_db_connection()   # release Windows file lock


@contextmanager
def temp_csv(rows: list[dict] | None = None,
             headers: tuple[str, ...] | None = None):
    """Yield a path to a temp CSV (UTF-8 BOM). rows=[dict, ...]."""
    if headers is None:
        # Default schema header
        headers = (
            "developer", "district", "unit_type", "area_m2", "price_qar",
            "status", "captured_at", "project", "sub_area", "completion_year",
            "payment_plan_summary", "source_url", "captured_by",
            "last_verified_at", "notes_ar", "value_per_m2",
        )
    rows = rows or []
    with tempfile.TemporaryDirectory() as td:
        csv_path = Path(td) / "inventory.csv"
        # Write CSV manually (BOM + simple comma-join; values assumed
        # CSV-safe — tests use only literal strings without commas).
        with open(csv_path, 'wb') as f:
            f.write(b'\xef\xbb\xbf')
            line = ','.join(headers) + '\n'
            f.write(line.encode('utf-8'))
            for r in rows:
                cells = [str(r.get(h, '')) for h in headers]
                f.write((','.join(cells) + '\n').encode('utf-8'))
        yield csv_path


def _aryan_row(unit_type='1BR', area_m2=86, price_qar=1150000,
               status='ready', last_verified_at='2026-05-25',
               district='لوسيل', project='City Avenues',
               developer='Aryan', captured_at='2026-05-25',
               captured_by='anas', notes_ar='clean'):
    """Return a complete Aryan/City Avenues row dict."""
    return {
        'developer': developer, 'district': district, 'unit_type': unit_type,
        'area_m2': area_m2, 'price_qar': price_qar, 'status': status,
        'captured_at': captured_at, 'project': project,
        'last_verified_at': last_verified_at, 'captured_by': captured_by,
        'notes_ar': notes_ar,
    }


def _seed_db_directly(db_path: Path, rows: list[dict]):
    """Insert rows via raw sqlite3 (bypass importer; for connector tests)."""
    with closing(sqlite3.connect(db_path)) as con:
        for r in rows:
            cols = ','.join(r.keys())
            ph = ','.join('?' * len(r))
            con.execute(f"INSERT INTO developer_inventory ({cols}) VALUES ({ph})",
                        list(r.values()))
        con.commit()
    t3._close_db_connection()


# ─────────────────────────────────────────────────────────────────────────
# Axis 1 — Schema migration idempotency
# ─────────────────────────────────────────────────────────────────────────

def test_01_axis1_schema_migration_idempotent():
    """Migrate fresh → stamp version. Migrate again → no DB write
    (last_migration_run_at identical). Migrate third time → still no write.
    True no-op on subsequent runs (Rule #51 + D12 axis 1)."""
    with temp_db() as db_path:
        # First migrate already ran via temp_db. Capture timestamp.
        with closing(sqlite3.connect(db_path)) as con:
            t1 = con.execute("SELECT value FROM schema_meta WHERE key=?",
                             (LAST_RUN_KEY,)).fetchone()[0]
        time.sleep(1.01)  # ensure clock would tick if we did write again
        # Second run
        migrate(db_path, DEFAULT_DDL_PATH, dry_run=False, verbose=False)
        with closing(sqlite3.connect(db_path)) as con:
            t2 = con.execute("SELECT value FROM schema_meta WHERE key=?",
                             (LAST_RUN_KEY,)).fetchone()[0]
        assert t1 == t2, f"Run 2 must be no-op (t1={t1} t2={t2})"
        time.sleep(1.01)
        # Third run
        migrate(db_path, DEFAULT_DDL_PATH, dry_run=False, verbose=False)
        with closing(sqlite3.connect(db_path)) as con:
            t3_ts = con.execute("SELECT value FROM schema_meta WHERE key=?",
                                (LAST_RUN_KEY,)).fetchone()[0]
        assert t1 == t3_ts, f"Run 3 must be no-op (t1={t1} t3={t3_ts})"


def test_01b_schema_verify_matches_after_migrate():
    """verify_schema() returns (True, []) on a freshly-migrated DB."""
    with temp_db() as db_path:
        with closing(sqlite3.connect(db_path)) as con:
            ok, drifts = verify_schema(con, verbose=False)
        assert ok is True, f"verify_schema must pass; drifts={drifts}"
        real_drifts = [d for d in drifts if not d.startswith("NOTE ")]
        assert real_drifts == [], f"No drifts expected; got {real_drifts}"


# ─────────────────────────────────────────────────────────────────────────
# Axis 2 — CSV import clean row succeeds
# ─────────────────────────────────────────────────────────────────────────

def test_02_axis2_csv_clean_row_succeeds():
    with temp_db() as db_path, temp_csv([_aryan_row()]) as csv_path:
        report = import_csv(csv_path, db_path, dry_run=False)
        assert 'error' not in report, f"Import error: {report.get('error')}"
        assert report['rows_seen'] == 1
        assert report['inserted'] == 1
        assert report['rejected'] == 0
        # Verify in DB
        with closing(sqlite3.connect(db_path)) as con:
            n = con.execute("SELECT COUNT(*) FROM developer_inventory").fetchone()[0]
            row = con.execute(
                "SELECT developer, project, unit_type, area_m2, price_qar, "
                "value_per_m2, status FROM developer_inventory"
            ).fetchone()
        assert n == 1
        assert row[0] == 'Aryan'
        assert row[1] == 'City Avenues'
        assert row[2] == '1BR'
        assert row[3] == 86.0
        assert row[4] == 1150000
        assert abs(row[5] - 13372.09) < 0.01   # auto-computed
        assert row[6] == 'ready'


# ─────────────────────────────────────────────────────────────────────────
# Axes 3-6 — CSV rejection categories (Rule #31 strict)
# ─────────────────────────────────────────────────────────────────────────

def test_03_axis3_missing_required_field_rejected():
    """Missing unit_type → rejection with field='unit_type' in error."""
    row = _aryan_row()
    row['unit_type'] = ''   # empty → None via CSV layer → required-field violation
    with temp_db() as db_path, temp_csv([row]) as csv_path:
        report = import_csv(csv_path, db_path, dry_run=False)
        assert report['rejected'] == 1
        assert report['inserted'] == 0
        rej = report['rejections'][0]
        assert rej['field'] == 'unit_type', f"field name in rejection: {rej['field']}"


def test_04_axis4_unknown_column_rejected_extra_forbidden():
    """Header has extra column → rejection with type='extra_forbidden' (Rule #31)."""
    headers = (
        "developer", "district", "unit_type", "area_m2", "price_qar",
        "status", "captured_at", "project", "bogus_extra_col",
    )
    row = _aryan_row()
    row['bogus_extra_col'] = 'trigger'
    with temp_db() as db_path, temp_csv([row], headers=headers) as csv_path:
        report = import_csv(csv_path, db_path, dry_run=False)
        assert report['rejected'] == 1
        rej = report['rejections'][0]
        assert rej['field'] == 'bogus_extra_col'
        assert rej['error_type'] == 'extra_forbidden'


def test_05_axis5_wrong_type_rejected():
    """area_m2='not_a_number' → rejection with field='area_m2'."""
    row = _aryan_row()
    row['area_m2'] = 'not_a_number'
    with temp_db() as db_path, temp_csv([row]) as csv_path:
        report = import_csv(csv_path, db_path, dry_run=False)
        assert report['rejected'] == 1
        rej = report['rejections'][0]
        assert rej['field'] == 'area_m2'
        assert 'float' in rej['error_type'] or 'type' in rej['error_type']


def test_06_axis6_invalid_status_enum_rejected():
    """status='pending' → rejection (not in ALLOWED_STATUSES)."""
    row = _aryan_row(status='pending')
    with temp_db() as db_path, temp_csv([row]) as csv_path:
        report = import_csv(csv_path, db_path, dry_run=False)
        assert report['rejected'] == 1
        rej = report['rejections'][0]
        assert rej['field'] == 'status'


# ─────────────────────────────────────────────────────────────────────────
# Axis 7 — Upsert on revision (D8 composite key, price out)
# ─────────────────────────────────────────────────────────────────────────

def test_07_axis7_upsert_on_price_revision():
    """Same (developer, project, unit_type, area_m2) twice → 1 row, latest price + refreshed last_verified_at."""
    r1 = _aryan_row(price_qar=1150000, last_verified_at='2026-05-25')
    r2 = _aryan_row(price_qar=1175000, last_verified_at='2026-06-15')
    with temp_db() as db_path, temp_csv([r1, r2]) as csv_path:
        report = import_csv(csv_path, db_path, dry_run=False)
        assert report['rejected'] == 0
        assert report['inserted'] == 1
        assert report['updated'] == 1
        with closing(sqlite3.connect(db_path)) as con:
            rows = con.execute(
                "SELECT price_qar, value_per_m2, last_verified_at "
                "FROM developer_inventory"
            ).fetchall()
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
        assert rows[0][0] == 1175000, "Price should be revised to latest"
        assert abs(rows[0][1] - 1175000 / 86) < 0.01, "value_per_m2 recomputed"
        assert rows[0][2] == '2026-06-15', "last_verified_at refreshed"


# ─────────────────────────────────────────────────────────────────────────
# Axes 8-10 — Status discount routing (per-row D6)
# ─────────────────────────────────────────────────────────────────────────

def _hybrid_t3_row(status, value=13000.0, freshness='fresh'):
    """Build a dict_new T3 row for direct hybrid_valuation_v1 testing."""
    return {
        'value_per_m2_raw': value, 'status': status,
        'freshness_status': freshness,
        'developer': 'Aryan', 'project': 'CityAvenues',
        'unit_type': '1BR', 'area_m2': 100,
    }


T2_FIXTURE = [{"value_per_m2": 14000.0}] * 10   # mimic PF Lusail T2


def _hybrid_t3_breakdown(t3_values):
    r = hybrid_valuation_v1(None, 0, T2_FIXTURE, t3_values)
    return next(t for t in r['tier_breakdown'] if t['tier'] == 'T3')


def test_08_axis8_off_plan_discount_minus_17p5():
    """status='off_plan' → discount_applied=-0.175."""
    t3_entry = _hybrid_t3_breakdown([_hybrid_t3_row('off_plan')])
    src = t3_entry['sources'][0]
    assert src['discount_applied'] == -0.175
    assert abs(src['value_per_m2_adjusted'] - 13000.0 * (1 - 0.175)) < 0.01


def test_09_axis9_under_construction_discount_minus_17p5():
    """status='under_construction' → discount_applied=-0.175 (same as off_plan, D6)."""
    t3_entry = _hybrid_t3_breakdown([_hybrid_t3_row('under_construction')])
    src = t3_entry['sources'][0]
    assert src['discount_applied'] == -0.175


def test_10_axis10_ready_discount_minus_10p0():
    """status='ready' → discount_applied=-0.10 (D6 — negotiation only, no off-plan gap)."""
    t3_entry = _hybrid_t3_breakdown([_hybrid_t3_row('ready')])
    src = t3_entry['sources'][0]
    assert src['discount_applied'] == -0.10
    assert abs(src['value_per_m2_adjusted'] - 13000.0 * 0.90) < 0.01


# ─────────────────────────────────────────────────────────────────────────
# Axes 11-12 — Freshness annotation + 0.5× evidence multiplier
# ─────────────────────────────────────────────────────────────────────────

def test_11_axis11_fresh_under_90_days():
    """_compute_freshness for <90d → 'fresh'. Connector emits freshness='fresh'."""
    today = date(2026, 5, 25)
    # 5 days ago
    assert _compute_freshness('2026-05-20', today=today) == 'fresh'
    # 89 days ago (just inside TTL)
    near = (today - timedelta(days=89)).isoformat()
    assert _compute_freshness(near, today=today) == 'fresh'
    # Exactly 90 days = boundary; spec says "> 90 days" is stale, so 90 == fresh
    boundary = (today - timedelta(days=90)).isoformat()
    assert _compute_freshness(boundary, today=today) == 'fresh'


def test_12_axis12_stale_over_90_days_half_weight():
    """_compute_freshness for >90d → 'stale'. n_effective = 0.5× per row."""
    today = date(2026, 5, 25)
    # 91 days ago (just over TTL)
    over = (today - timedelta(days=91)).isoformat()
    assert _compute_freshness(over, today=today) == 'stale'
    # 175 days ago
    very_old = (today - timedelta(days=175)).isoformat()
    assert _compute_freshness(very_old, today=today) == 'stale'
    # Verify n_effective contribution via hybrid
    t3_values = [
        _hybrid_t3_row('ready', freshness='fresh'),
        _hybrid_t3_row('ready', freshness='stale'),
    ]
    t3_entry = _hybrid_t3_breakdown(t3_values)
    assert t3_entry['n'] == 2
    assert abs(t3_entry['n_effective'] - 1.5) < 0.001, (
        f"1 fresh (1.0) + 1 stale (0.5) = 1.5; got {t3_entry['n_effective']}"
    )


def test_12b_missing_last_verified_treated_as_stale():
    """None / empty last_verified_at → defensive 'stale'."""
    assert _compute_freshness(None) == 'stale'
    assert _compute_freshness('') == 'stale'
    assert _compute_freshness('not-a-date') == 'stale'


# ─────────────────────────────────────────────────────────────────────────
# Axis 13 — Geo filter (district string-match strict)
# ─────────────────────────────────────────────────────────────────────────

def test_13_axis13_geo_filter_strict():
    """Rows in Lusail; query for Pearl → None."""
    with temp_db() as db_path:
        _seed_db_directly(db_path, [{
            'developer': 'Aryan', 'project': 'City Avenues', 'district': 'لوسيل',
            'unit_type': '1BR', 'area_m2': 86, 'price_qar': 1150000,
            'value_per_m2': 13372.09, 'status': 'ready',
            'captured_at': '2026-05-25', 'last_verified_at': '2026-05-25',
        }])
        result = fetch_for_district('جزيرة اللؤلؤة', 'apartment_building',
                                    db_path=db_path, today=date(2026, 5, 25))
        assert result is None, f"Geo mismatch must return None; got {result}"


# ─────────────────────────────────────────────────────────────────────────
# Axis 14 — Feature flag T3_INVENTORY_ENABLED=false suppresses T3
# ─────────────────────────────────────────────────────────────────────────

def test_14_axis14_flag_off_suppresses_t3():
    """T3_INVENTORY_ENABLED=false → no T3 row in tier_breakdown regardless of DB."""
    with temp_db() as db_path:
        _seed_db_directly(db_path, [{
            'developer': 'Aryan', 'project': 'City Avenues', 'district': 'لوسيل',
            'unit_type': '1BR', 'area_m2': 86, 'price_qar': 1150000,
            'value_per_m2': 13372.09, 'status': 'ready',
            'captured_at': '2026-05-25', 'last_verified_at': '2026-05-25',
        }])

        gis = MagicMock()
        gis.get_district_at_point.return_value = MagicMock(
            aname='لوسيل', ename='Lusail',
        )
        listings = [{"value_per_m2": 13000.0 + i * 50} for i in range(10)]
        fake_loc = MagicMock(lat=25.4, lon=51.5)
        fake_plot = MagicMock(pdarea=900)

        def fake_fetch(district, asset_type, **kw):
            return fetch_for_district(district=district, asset_type=asset_type,
                                       db_path=db_path, today=date(2026, 5, 25), **kw)

        with patch.dict(os.environ, {'T3_INVENTORY_ENABLED': 'false',
                                      'HYBRID_APARTMENTS_ENABLED': 'true'}), \
             patch("connectors.propertyfinder_apartments_t2_sales.get_apartment_sales_lusail",
                   return_value=listings), \
             patch("connectors.developer_inventory_t3.fetch_for_district",
                   side_effect=fake_fetch):
            result = evaluate_unified._try_hybrid_apartments_response(
                zone=69, street=329, building=20,
                loc=fake_loc, plot=fake_plot,
                asset_type='apartment_building', audience='self',
                gis_lite=gis,
            )

        assert result is not None
        t3_entry = next((t for t in result['hybrid']['tier_breakdown']
                          if t.get('tier') == 'T3'), None)
        assert t3_entry is None, f"flag=false must produce no T3 entry; got {t3_entry}"


# ─────────────────────────────────────────────────────────────────────────
# Axes 15-17 — Case A / B / C routing
# ─────────────────────────────────────────────────────────────────────────

def test_15_axis15_case_a_t1_and_t3():
    """T1 (n_total>=10) + T3 present → Case A routing."""
    r = hybrid_valuation_v1(
        t1_values=[{"value_per_m2": 13500.0}] * 12, t1_n_total=12,
        t2_values=None,
        t3_values=[_hybrid_t3_row('ready')],
    )
    assert r['case'] == 'A'
    assert r['value_per_m2'] is not None
    # T1 dominance: weight >= floor 0.45
    t1_entry = next(t for t in r['tier_breakdown'] if t['tier'] == 'T1')
    assert t1_entry['weight'] >= 0.45


def test_16_axis16_case_b_t2_and_t3():
    """T1 absent + T2 present + T3 present → Case B routing. Primary Sprint 2.21.4 path."""
    r = hybrid_valuation_v1(
        t1_values=None, t1_n_total=0,
        t2_values=T2_FIXTURE,
        t3_values=[_hybrid_t3_row('ready')] * 4,
    )
    assert r['case'] == 'B'
    assert r['confidence'] == 'indicative'   # Rule E3 §4 ceiling without T1
    assert r['muc_required'] is True         # Rule E3 §5
    t3 = next(t for t in r['tier_breakdown'] if t['tier'] == 'T3')
    assert abs(t3['weight'] - 0.12) < 0.001  # 0.15 × 4/5 (BRIEF §9)


def test_17_axis17_case_c_t3_alone_refused():
    """T3 alone (no T1, no T2) → value_per_m2=None, confidence='fallback' (E3 Constraint 8)."""
    r = hybrid_valuation_v1(
        t1_values=None, t1_n_total=0,
        t2_values=None,
        t3_values=[_hybrid_t3_row('ready')],
    )
    assert r['case'] == 'C'
    assert r['value_per_m2'] is None
    assert r['confidence'] == 'fallback'
    assert 'T3 alone' in (r['fallback_reason'] or '')


# ─────────────────────────────────────────────────────────────────────────
# Axis 18 — tier_breakdown 7-field shape (Rule E10)
# ─────────────────────────────────────────────────────────────────────────

def test_18_axis18_t3_source_seven_field_shape():
    """Each T3 source dict in tier_breakdown has EXACTLY the 7 contract fields."""
    expected_fields = {
        'developer', 'project', 'status', 'value_per_m2_raw',
        'discount_applied', 'value_per_m2_adjusted', 'freshness_status',
    }
    r = hybrid_valuation_v1(None, 0, T2_FIXTURE, [
        _hybrid_t3_row('off_plan'),
        _hybrid_t3_row('ready', freshness='stale'),
    ])
    t3 = next(t for t in r['tier_breakdown'] if t['tier'] == 'T3')
    assert 'sources' in t3
    assert len(t3['sources']) == 2
    for src in t3['sources']:
        assert set(src.keys()) == expected_fields, (
            f"7-field contract violated: got {sorted(src.keys())}"
        )


# ─────────────────────────────────────────────────────────────────────────
# Axis 19 — Empty DB does not crash apartment evaluation
# ─────────────────────────────────────────────────────────────────────────

def test_19_axis19_empty_db_no_crash():
    """Empty developer_inventory.sqlite → fetch returns None, no exception."""
    with temp_db() as db_path:
        result = fetch_for_district('لوسيل', 'apartment_building',
                                    db_path=db_path, today=date(2026, 5, 25))
        assert result is None, "Empty DB must return None, not []"


def test_19b_missing_db_file_no_crash():
    """DB file doesn't exist → None + WARN log, no exception."""
    t3._close_db_connection()
    result = fetch_for_district('لوسيل', 'apartment_building',
                                db_path=Path('/no/such/path.sqlite'),
                                today=date(2026, 5, 25))
    assert result is None


# ─────────────────────────────────────────────────────────────────────────
# Axis 20 — Partial population (district mismatch returns no T3)
# ─────────────────────────────────────────────────────────────────────────

def test_20_axis20_partial_population_district_mismatch():
    """City Avenues rows seeded in 'لوسيل'. Query for 'لوسيل 69' → None
    (BRIEF H11 negative test — partial-population doesn't leak)."""
    with temp_db() as db_path:
        _seed_db_directly(db_path, [{
            'developer': 'Aryan', 'project': 'City Avenues', 'district': 'لوسيل',
            'unit_type': '1BR', 'area_m2': 86, 'price_qar': 1150000,
            'value_per_m2': 13372.09, 'status': 'ready',
            'captured_at': '2026-05-25', 'last_verified_at': '2026-05-25',
        }])
        result = fetch_for_district('لوسيل 69', 'apartment_building',
                                    db_path=db_path, today=date(2026, 5, 25))
        assert result is None, (
            f"'لوسيل 69' != 'لوسيل' must yield None; got {result}"
        )


# ─────────────────────────────────────────────────────────────────────────
# Bonus: end-to-end integration via _try_hybrid_apartments_response
# (BRIEF requirement: "at least one test exercises the integrated path")
# ─────────────────────────────────────────────────────────────────────────

def test_21_integration_end_to_end():
    """Full path: importer → DB → connector → hybrid_valuation_v1 → engine response.
    Verifies the Sprint 2.21.4 architectural seal (BRIEF §9 — n=4 fresh ready
    Aryan rows → effective T3 weight = 0.12 = 0.15 × 4/5)."""
    aryan_rows = [
        _aryan_row(unit_type='1BR', area_m2=86,  price_qar=1150000),
        _aryan_row(unit_type='2BR', area_m2=128, price_qar=1700000),
        _aryan_row(unit_type='2BR', area_m2=134, price_qar=1800000),
        _aryan_row(unit_type='3BR', area_m2=168, price_qar=2250000),
    ]
    with temp_db() as db_path, temp_csv(aryan_rows) as csv_path:
        # Importer ingests 4 rows
        report = import_csv(csv_path, db_path, dry_run=False)
        assert report['rejected'] == 0
        assert report['inserted'] == 4

        # Engine-side mocks
        gis = MagicMock()
        gis.get_district_at_point.return_value = MagicMock(
            aname='لوسيل', ename='Lusail',
        )
        listings = [{"value_per_m2": 13000.0 + i * 50} for i in range(10)]
        fake_loc = MagicMock(lat=25.4, lon=51.5)
        fake_plot = MagicMock(pdarea=900)

        def fake_fetch(district, asset_type, **kw):
            return fetch_for_district(district=district, asset_type=asset_type,
                                       db_path=db_path, today=date(2026, 5, 25), **kw)

        with patch.dict(os.environ, {'HYBRID_APARTMENTS_ENABLED': 'true'},
                         clear=False), \
             patch("connectors.propertyfinder_apartments_t2_sales.get_apartment_sales_lusail",
                   return_value=listings), \
             patch("connectors.developer_inventory_t3.fetch_for_district",
                   side_effect=fake_fetch):
            result = evaluate_unified._try_hybrid_apartments_response(
                zone=69, street=329, building=20,
                loc=fake_loc, plot=fake_plot,
                asset_type='apartment_building', audience='self',
                gis_lite=gis,
            )

        assert result is not None
        assert result['valuation']['method'] == 'hybrid_t2'
        t3 = next(t for t in result['hybrid']['tier_breakdown']
                  if t.get('tier') == 'T3')
        assert t3['n'] == 4
        assert abs(t3['n_effective'] - 4.0) < 0.001
        assert abs(t3['weight'] - 0.12) < 0.001     # BRIEF §9 architectural seal
        assert len(t3['sources']) == 4
        assert all(s['status'] == 'ready' for s in t3['sources'])
        assert all(s['discount_applied'] == -0.10 for s in t3['sources'])


# ─────────────────────────────────────────────────────────────────────────
# Bonus: pydantic sentinel normalization (Step 4 NULL-UNIQUE soft-flag fix)
# ─────────────────────────────────────────────────────────────────────────

def test_22_project_sentinel_normalization():
    """NULL/empty/whitespace project → sentinel '(unspecified)'. Real
    project name passes through. Closes SQLite NULL-aware UNIQUE bypass."""
    common = dict(developer='X', district='Y', unit_type='1BR',
                  area_m2=100, price_qar=1000000, status='ready',
                  captured_at='2026-05-25')
    assert InventoryRow(**common, project=None).project == PROJECT_SENTINEL_UNSPECIFIED
    assert InventoryRow(**common, project='').project == PROJECT_SENTINEL_UNSPECIFIED
    assert InventoryRow(**common, project='   ').project == PROJECT_SENTINEL_UNSPECIFIED
    assert InventoryRow(**common, project='City Avenues').project == 'City Avenues'


# ─────────────────────────────────────────────────────────────────────────
# Bonus: HYBRID_TIER_CONFIG back-compat alias (Step 7 carry-over #2)
# ─────────────────────────────────────────────────────────────────────────

def test_23_t3_discount_midpoint_alias_preserved():
    """T3_discount_midpoint back-compat alias (Sprint 2.21.2 callers) = T3_discount_default."""
    assert 'T3_discount_midpoint' in HYBRID_TIER_CONFIG
    assert HYBRID_TIER_CONFIG['T3_discount_midpoint'] == HYBRID_TIER_CONFIG['T3_discount_default']
    assert HYBRID_TIER_CONFIG['T3_discount_midpoint'] == -0.175
    assert 'T3_status_discount_map' in HYBRID_TIER_CONFIG
    assert HYBRID_TIER_CONFIG['T3_status_discount_map']['ready'] == -0.10


# ─────────────────────────────────────────────────────────────────────────
# Standalone runner (regression-runner pattern; no pytest required)
# ─────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import inspect as _inspect
    import traceback as _tb
    _module = sys.modules[__name__]
    tests = [
        (name, fn) for name, fn in _inspect.getmembers(_module)
        if name.startswith('test_') and callable(fn)
    ]
    tests.sort(key=lambda kv: kv[0])
    passed = failed = 0
    t0 = time.time()
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            _tb.print_exc()
            failed += 1
    dt = time.time() - t0
    print(f"\n[Sprint 2.21.4] {passed} passed, {failed} failed of {len(tests)} "
          f"in {dt:.2f}s")
    sys.exit(0 if failed == 0 else 1)
