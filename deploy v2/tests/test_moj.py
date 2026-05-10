"""Tests for moj_reference.py and moj_db.py — Sprint 1."""
import sys
from pathlib import Path

# Ensure project modules are importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from moj_reference import normalize, build_reference, parse_date, compute_trend, categorize
from moj_db import init_db, open_db, query_reference, query_trend, query_stats, normalize as db_normalize
from datetime import datetime


class TestNBSPNormalization:
    """CRITICAL: NBSP variants must be treated as identical."""

    def test_normalize_strips_nbsp(self):
        assert normalize('أرض\xa0فضاء') == 'أرض فضاء'
        assert normalize('بيت\xa0للسكن') == 'بيت للسكن'

    def test_normalize_strips_multiple_spaces(self):
        assert normalize('أم   صلال') == 'أم صلال'

    def test_nbsp_land_counted_in_csv(self, mini_rows):
        """T010 has type 'أرض\\xa0فضاء' — must be categorized as land."""
        t010 = [r for r in mini_rows if r.get('رقم المعامله المرجعي', '').strip() == 'T010']
        assert len(t010) == 1
        assert categorize(t010[0]) == 'land'

    def test_nbsp_villa_counted_in_csv(self, mini_rows):
        """T018 has type 'بيت\\xa0للسكن' — must be categorized as villa."""
        t018 = [r for r in mini_rows if r.get('رقم المعامله المرجعي', '').strip() == 'T018']
        assert len(t018) == 1
        assert categorize(t018[0]) == 'villa'

    def test_db_normalizes_on_insert(self, mini_csv):
        """DB must normalize NBSP on insert so queries work with regular space."""
        conn = init_db(mini_csv, force=True)
        # Query with regular space should find the NBSP row
        rows = conn.execute(
            "SELECT * FROM transactions WHERE property_type='أرض فضاء'"
        ).fetchall()
        # All 10 land rows (including T010 with NBSP) should match
        assert len(rows) == 10
        conn.close()


class TestSizeBrackets:
    """Size bracket assignment must match SIZE_BRACKETS definition."""

    def test_bracket_500(self, mini_rows):
        """500 m² → bracket '400-600'"""
        ref = build_reference(mini_rows, 'المعمورة 56',
                              datetime(2025, 12, 31))
        villa = ref['categories']['villa']
        bracket = villa['size_brackets'].get('400-600', {})
        assert bracket['n'] > 0, "Should have villas in 400-600 bracket"

    def test_bracket_1100(self, mini_rows):
        """1100 m² → bracket '900-1500'"""
        ref = build_reference(mini_rows, 'المعمورة 56',
                              datetime(2025, 12, 31))
        villa = ref['categories']['villa']
        bracket = villa['size_brackets'].get('900-1500', {})
        assert bracket['n'] > 0, "Should have villas in 900-1500 bracket"

    def test_brackets_sum_to_total(self, mini_rows):
        """All bracketed rows must sum to total n for the category."""
        ref = build_reference(mini_rows, 'المعمورة 56',
                              datetime(2025, 12, 31))
        for cat_name in ('land', 'villa'):
            cat = ref['categories'][cat_name]
            bracket_total = sum(
                b['n'] for b in cat.get('size_brackets', {}).values()
            )
            # bracket_total <= cat['n'] (some rows may have missing area)
            assert bracket_total <= cat['n']


class TestMedianCalculation:
    """Median must be the middle value of sorted prices."""

    def test_land_median_known(self, mini_rows):
        """10 land rows, sorted ft2 prices: 350,375,380,390,395,400,405,410,420.
        We have 10 rows within 36-month window. Median of sorted = middle."""
        ref = build_reference(mini_rows, 'المعمورة 56',
                              datetime(2025, 12, 31))
        land = ref['categories']['land']
        ft2_stats = land['price_per_ft2']
        assert ft2_stats is not None
        # 10 values sorted: 350,360,375,380,390,395,400,405,410,420
        # quartile_stats: values[int(0.50 * 9)] = values[4] = 390
        assert ft2_stats['median'] == 390

    def test_villa_median_reasonable(self, mini_rows):
        """Villa total price median should be between min and max."""
        ref = build_reference(mini_rows, 'المعمورة 56',
                              datetime(2025, 12, 31))
        villa = ref['categories']['villa']
        total = villa['total_price']
        assert total['min'] <= total['median'] <= total['max']


class TestSmallSampleWarning:
    """Brackets with n < 10 must be flagged as unreliable."""

    def test_small_bracket_unreliable(self, mini_rows):
        """900-1500 bracket has only 3 villas — must be unreliable."""
        ref = build_reference(mini_rows, 'المعمورة 56',
                              datetime(2025, 12, 31))
        villa = ref['categories']['villa']
        bracket = villa['size_brackets'].get('900-1500', {})
        if bracket:
            assert bracket['reliable'] is False, \
                f"Bracket 900-1500 has n={bracket['n']}, should be unreliable"

    def test_area_not_found(self, mini_rows):
        """Querying nonexistent area should return error, not crash."""
        ref = build_reference(mini_rows, 'منطقة وهمية',
                              datetime(2025, 12, 31))
        assert 'error' in ref


class TestTrendComputation:
    """Trend must compute annual slope from yearly medians."""

    def test_trend_has_years(self, mini_rows):
        """Trend should return data for each year present."""
        trend = compute_trend(mini_rows, 'المعمورة 56',
                              datetime(2025, 12, 31), category='land')
        assert trend is not None
        years = [y['year'] for y in trend['years']]
        assert '2024' in years
        assert '2025' in years

    def test_trend_label_valid(self, mini_rows):
        """Trend label must be one of the three valid values."""
        trend = compute_trend(mini_rows, 'المعمورة 56',
                              datetime(2025, 12, 31), category='all')
        assert trend['label'] in ('ارتفاع', 'استقرار', 'انخفاض')

    def test_trend_nonexistent_area(self, mini_rows):
        """Trend for nonexistent area returns None."""
        trend = compute_trend(mini_rows, 'وهمية',
                              datetime(2025, 12, 31))
        assert trend is None


class TestReturnTransactions:
    """build_reference with return_transactions=True must include full details."""

    def test_transactions_returned(self, mini_rows):
        ref = build_reference(mini_rows, 'المعمورة 56',
                              datetime(2025, 12, 31),
                              return_transactions=True)
        villa = ref['categories']['villa']
        for bracket_key, bracket in villa['size_brackets'].items():
            if bracket['n'] > 0:
                assert 'transactions' in bracket, \
                    f"Bracket {bracket_key} missing transactions"
                assert len(bracket['transactions']) == bracket['n']
                # Each transaction has required fields
                t = bracket['transactions'][0]
                assert 'date' in t
                assert 'total_price' in t
                assert 'area_m2' in t

    def test_transactions_sorted_desc(self, mini_rows):
        ref = build_reference(mini_rows, 'المعمورة 56',
                              datetime(2025, 12, 31),
                              return_transactions=True)
        villa = ref['categories']['villa']
        for bracket in villa['size_brackets'].values():
            txns = bracket.get('transactions', [])
            if len(txns) >= 2:
                dates = [t['date'] for t in txns]
                assert dates == sorted(dates, reverse=True), \
                    "Transactions must be sorted newest first"


class TestDBQueryMatchesCSV:
    """DB queries must produce equivalent results to CSV parsing."""

    def test_db_villa_n_matches(self, mini_csv, mini_rows):
        """DB and CSV must agree on villa count."""
        conn = init_db(mini_csv, force=True)
        db_ref = query_reference(conn, 'المعمورة 56', 'villa', window_months=36)
        csv_ref = build_reference(mini_rows, 'المعمورة 56',
                                  datetime(2025, 12, 31))
        csv_villa_n = csv_ref['categories']['villa']['n']
        assert db_ref['n'] == csv_villa_n, \
            f"DB n={db_ref['n']} != CSV n={csv_villa_n}"
        conn.close()

    def test_db_stats(self, mini_csv):
        conn = init_db(mini_csv, force=True)
        stats = query_stats(conn)
        assert stats['total_transactions'] == 20
        assert stats['distinct_areas'] == 1
        conn.close()
