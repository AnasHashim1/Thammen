#!/usr/bin/env python3
"""
moj_db.py — SQLite database for Qatar Ministry of Justice real estate transactions.

Replaces CSV parsing with indexed database queries. ~10× faster for evaluations.

Usage:
    python3 moj_db.py init   moj_weekly.csv              # First time: CSV → SQLite
    python3 moj_db.py update moj_weekly.csv               # Add new rows only
    python3 moj_db.py stats                               # Show DB statistics
    python3 moj_db.py query  "المعمورة 56" villa 24       # Quick reference query

The DB file is stored alongside the CSV: moj_weekly.db
"""

import csv
import json
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ============================================================
# CONSTANTS
# ============================================================

DB_VERSION = 1
SIZE_BRACKETS = [(0, 400), (400, 600), (600, 900), (900, 1500), (1500, 99999)]

# Column name mapping: CSV header (with possible NBSP) → clean DB column
CSV_TO_DB = {
    'رقم المعامله المرجعي':  'ref_no',
    'رقم العقار المرجعي':    'property_ref',
    'تاريخ التثبيت':         'date',          # may have NBSP
    'اسم البلدية':           'municipality',
    'اسم المنطقة':           'area',
    'نوع العقار':            'property_type',
    'الاستخدام':             'usage',
    'المساحة بالمتر المربع': 'area_m2',
    'مساحة الحصص المباعة':   'sold_area',
    'سعر القدم المربع':      'price_ft2',
    'سعر المتر المربع':      'price_m2',
    'عدد الحصص المباعة':     'shares_sold',
    'قيمة الحصص المباعة':    'shares_value',
    'قيمة العقار':           'total_price',
}

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ref_no          TEXT UNIQUE,
    property_ref    TEXT,
    date            TEXT,        -- YYYY-MM-DD
    year            INTEGER,
    municipality    TEXT,
    area            TEXT,
    property_type   TEXT,
    usage           TEXT,
    area_m2         REAL,
    sold_area       REAL,
    price_ft2       REAL,
    price_m2        REAL,
    shares_sold     REAL,
    shares_value    REAL,
    total_price     REAL,
    -- Derived fields
    category        TEXT,        -- land | villa | palace | dwelling | other
    size_bracket    TEXT         -- "0-400" | "400-600" | ...
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_area ON transactions(area);",
    "CREATE INDEX IF NOT EXISTS idx_area_cat ON transactions(area, category);",
    "CREATE INDEX IF NOT EXISTS idx_area_cat_date ON transactions(area, category, date);",
    "CREATE INDEX IF NOT EXISTS idx_municipality ON transactions(municipality);",
    "CREATE INDEX IF NOT EXISTS idx_date ON transactions(date);",
    "CREATE INDEX IF NOT EXISTS idx_ref_no ON transactions(ref_no);",
]

CREATE_META = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


# ============================================================
# HELPERS
# ============================================================

def normalize(s: str) -> str:
    """Replace all whitespace variants (including NBSP \\xa0) with regular space."""
    return re.sub(r'\s+', ' ', s or '').strip()


def to_float(s) -> Optional[float]:
    try:
        return float(str(s or '').replace(',', '').strip())
    except (ValueError, TypeError):
        return None


def categorize_type(raw: str) -> str:
    """Categorize Arabic property type into standard categories."""
    t = normalize(raw)
    if t == 'أرض فضاء':
        return 'land'
    if t.startswith(('فيلا', 'فيلتان', 'فيلتين')) or t.startswith('بيت'):
        return 'villa'
    if 'مجمع فلل' in t:
        return 'villa_compound'
    if t == 'قصر':
        return 'palace'
    if t in ('مسكن', 'مسكن شعبي'):
        return 'dwelling'
    if any(x in t for x in ('عمارة', 'برج', 'شقة')):
        return 'apartment_building'
    if t == 'مزرعة':
        return 'farm'
    return 'other'


def size_bracket(area_m2: Optional[float]) -> Optional[str]:
    if area_m2 is None or area_m2 <= 0:
        return None
    for lo, hi in SIZE_BRACKETS:
        if lo <= area_m2 < hi:
            return f'{lo}-{hi}'
    return None


def resolve_csv_column(headers: list, target: str) -> Optional[str]:
    """Find the actual CSV header matching a target (handles NBSP variants)."""
    target_norm = normalize(target)
    for h in headers:
        if normalize(h) == target_norm:
            return h
    return None


# ============================================================
# DATABASE OPERATIONS
# ============================================================

def get_db_path(csv_path: Path) -> Path:
    return csv_path.with_suffix('.db')


def init_db(csv_path: Path, force: bool = False) -> sqlite3.Connection:
    """Create SQLite DB from MoJ CSV. Returns connection."""
    db_path = get_db_path(csv_path)
    if db_path.exists() and not force:
        print(f"DB already exists: {db_path}. Use 'update' or pass force=True.")
        return sqlite3.connect(str(db_path))

    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(CREATE_TABLE)
    conn.execute(CREATE_META)
    conn.commit()

    # Load CSV
    inserted, skipped, normalized_count = _load_csv_into_db(conn, csv_path)

    # Create indexes
    for idx_sql in CREATE_INDEXES:
        conn.execute(idx_sql)

    # Store metadata
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('version', ?)", (str(DB_VERSION),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('source_csv', ?)", (str(csv_path),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('created_at', ?)", (datetime.now().isoformat(),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('total_rows', ?)", (str(inserted),))
    conn.commit()

    print(f"✅ Created {db_path}")
    print(f"   Inserted: {inserted:,}")
    print(f"   Skipped (duplicate ref_no): {skipped:,}")
    print(f"   NBSP normalizations: {normalized_count:,}")

    return conn


def _load_csv_into_db(conn: sqlite3.Connection, csv_path: Path) -> tuple:
    """Load CSV rows into DB. Returns (inserted, skipped, normalized_count)."""
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        # Build column resolver
        col_map = {}
        for ar_name, db_col in CSV_TO_DB.items():
            actual = resolve_csv_column(headers, ar_name)
            if actual:
                col_map[db_col] = actual

        inserted = 0
        skipped = 0
        normalized_count = 0
        batch = []

        for row in reader:
            # Extract and normalize
            values = {}
            for db_col, csv_col in col_map.items():
                raw = row.get(csv_col, '')
                normed = normalize(raw)
                if normed != raw.strip():
                    normalized_count += 1
                values[db_col] = normed

            # Parse specific fields
            ref_no = values.get('ref_no', '')
            date_str = values.get('date', '')
            year = None
            if date_str and len(date_str) >= 4:
                try:
                    year = int(date_str[:4])
                except ValueError:
                    pass

            area_m2_val = to_float(values.get('area_m2'))
            cat = categorize_type(values.get('property_type', ''))
            bracket = size_bracket(area_m2_val)

            batch.append((
                ref_no,
                values.get('property_ref'),
                date_str,
                year,
                values.get('municipality'),
                values.get('area'),
                values.get('property_type'),
                values.get('usage'),
                area_m2_val,
                to_float(values.get('sold_area')),
                to_float(values.get('price_ft2')),
                to_float(values.get('price_m2')),
                to_float(values.get('shares_sold')),
                to_float(values.get('shares_value')),
                to_float(values.get('total_price')),
                cat,
                bracket,
            ))

            if len(batch) >= 5000:
                ins, skip = _insert_batch(conn, batch)
                inserted += ins
                skipped += skip
                batch = []

        if batch:
            ins, skip = _insert_batch(conn, batch)
            inserted += ins
            skipped += skip

    return inserted, skipped, normalized_count


def _insert_batch(conn, batch):
    """Insert a batch with INSERT OR IGNORE (skip duplicates by ref_no)."""
    inserted = 0
    skipped = 0
    for row in batch:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO transactions
                (ref_no, property_ref, date, year, municipality, area,
                 property_type, usage, area_m2, sold_area, price_ft2, price_m2,
                 shares_sold, shares_value, total_price, category, size_bracket)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, row)
            if conn.total_changes:
                inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    conn.commit()
    # Recount properly
    return len(batch) - skipped, skipped


def update_db(csv_path: Path) -> tuple:
    """Add new rows from CSV to existing DB. Returns (new_rows, total_rows)."""
    db_path = get_db_path(csv_path)
    if not db_path.exists():
        print("DB not found. Running init instead.")
        conn = init_db(csv_path)
        total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        conn.close()
        return total, total

    conn = sqlite3.connect(str(db_path))
    before = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    inserted, skipped, norm_count = _load_csv_into_db(conn, csv_path)

    # Update metadata
    after = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    new_rows = after - before
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('last_update', ?)",
                 (datetime.now().isoformat(),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('total_rows', ?)", (str(after),))
    conn.commit()
    conn.close()

    print(f"✅ Updated {db_path}")
    print(f"   New rows: {new_rows:,}")
    print(f"   Total: {after:,}")
    return new_rows, after


# ============================================================
# QUERY ENGINE
# ============================================================

def open_db(csv_or_db_path: Path) -> sqlite3.Connection:
    """Open DB from either a .db path or a .csv path (derives .db)."""
    p = Path(csv_or_db_path)
    if p.suffix == '.csv':
        p = p.with_suffix('.db')
    if not p.exists():
        raise FileNotFoundError(f"Database not found: {p}. Run 'moj_db.py init <csv>' first.")
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


def _median(values: list) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    return s[n // 2]


def _weighted_median(values_with_weights: list) -> Optional[float]:
    """Weighted median: recent transactions count more."""
    if not values_with_weights:
        return None
    # Sort by value
    sw = sorted(values_with_weights, key=lambda x: x[0])
    total_w = sum(w for _, w in sw)
    if total_w <= 0:
        return _median([v for v, _ in sw])
    cumulative = 0
    for val, weight in sw:
        cumulative += weight
        if cumulative >= total_w / 2:
            return val
    return sw[-1][0]


def _time_weight(txn_date_str: str, ref_date: datetime = None) -> float:
    """Weight by recency: recent = 1.0, old = 0.3."""
    ref = ref_date or datetime.now()
    try:
        txn = datetime.strptime(txn_date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return 0.5
    months = (ref - txn).days / 30.44
    if months <= 3:  return 1.00
    if months <= 6:  return 0.90
    if months <= 12: return 0.75
    if months <= 18: return 0.60
    if months <= 24: return 0.45
    return 0.30


def _quartile_stats(values: list) -> Optional[dict]:
    values = sorted(v for v in values if v is not None and v > 0)
    if not values:
        return None
    n = len(values)
    p = lambda q: values[int(q * (n - 1))]
    return {
        'n': n,
        'min': round(values[0]),
        'p25': round(p(0.25)),
        'median': round(p(0.50)),
        'p75': round(p(0.75)),
        'max': round(values[-1]),
    }


def query_reference(conn: sqlite3.Connection, area: str,
                    category: str = 'villa',
                    window_months: int = 24,
                    fallback_months: int = 36,
                    min_n: int = 20,
                    return_transactions: bool = True) -> dict:
    """
    Build a MoJ reference for an area + category from the database.

    Equivalent to moj_reference.build_reference() but ~10× faster.
    """
    area_norm = normalize(area)
    now_str = datetime.now().strftime('%Y-%m-%d')

    # Compute cutoff dates
    cutoff_24 = (datetime.now() - timedelta(days=window_months * 30.44)).strftime('%Y-%m-%d')
    cutoff_36 = (datetime.now() - timedelta(days=fallback_months * 30.44)).strftime('%Y-%m-%d')

    # Count in 24-month window
    n_24 = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE area=? AND category=? AND date>=?",
        (area_norm, category, cutoff_24)
    ).fetchone()[0]

    # Pick window
    if n_24 >= min_n:
        cutoff = cutoff_24
        window = window_months
    else:
        cutoff = cutoff_36
        window = fallback_months

    rows = conn.execute("""
        SELECT date, area_m2, total_price, price_m2, price_ft2,
               property_type, size_bracket
        FROM transactions
        WHERE area=? AND category=? AND date>=?
        ORDER BY date DESC
    """, (area_norm, category, cutoff)).fetchall()

    n = len(rows)
    if n == 0:
        return {
            'area': area, 'category': category,
            'n': 0, 'reliable': False,
            'window_months': window,
        }

    # Overall stats
    result = {
        'area': area,
        'category': category,
        'n': n,
        'window_months': window,
        'reliable': n >= min_n,
        'valuation_date': datetime.now().strftime('%Y-%m-%d'),
        'data_through': rows[0]['date'] if rows else None,
        'price_per_m2': _quartile_stats([r['price_m2'] for r in rows]),
        'price_per_ft2': _quartile_stats([r['price_ft2'] for r in rows]),
        'plot_area_m2': _quartile_stats([r['area_m2'] for r in rows]),
        'total_price': _quartile_stats([r['total_price'] for r in rows]),
        # Time-weighted medians (recent transactions weighted more)
        'weighted_median_per_m2': _weighted_median(
            [(r['price_m2'], _time_weight(r['date'])) for r in rows if r['price_m2']]
        ),
        'weighted_median_total': _weighted_median(
            [(r['total_price'], _time_weight(r['date'])) for r in rows if r['total_price']]
        ),
        'size_brackets': {},
    }

    # Per-bracket stats
    for lo, hi in SIZE_BRACKETS:
        bracket_key = f'{lo}-{hi}'
        bracket_rows = [r for r in rows if r['size_bracket'] == bracket_key]
        if not bracket_rows:
            continue
        ppm2 = _quartile_stats([r['price_m2'] for r in bracket_rows])
        tot = _quartile_stats([r['total_price'] for r in bracket_rows])
        bracket_data = {
            'n': len(bracket_rows),
            'reliable': len(bracket_rows) >= 10,
            'price_per_m2': ppm2,
            'total_price': tot,
        }
        # Include transactions if requested
        if return_transactions:
            bracket_data['transactions'] = [
                {
                    'date': r['date'],
                    'area_m2': r['area_m2'],
                    'total_price': r['total_price'],
                    'price_per_m2': r['price_m2'],
                    'price_per_ft2': r['price_ft2'],
                    'type_ar': r['property_type'],
                }
                for r in bracket_rows
            ]
        result['size_brackets'][bracket_key] = bracket_data

    # Overall transactions
    if return_transactions:
        result['transactions'] = [
            {
                'date': r['date'],
                'area_m2': r['area_m2'],
                'total_price': r['total_price'],
                'price_per_m2': r['price_m2'],
                'price_per_ft2': r['price_ft2'],
                'type_ar': r['property_type'],
            }
            for r in rows
        ]

    return result


def query_trend(conn: sqlite3.Connection, area: str,
                category: str = 'all') -> Optional[dict]:
    """
    Compute annual price-per-foot trend from DB.
    Equivalent to moj_reference.compute_trend() but faster.
    """
    area_norm = normalize(area)

    if category == 'all':
        rows = conn.execute("""
            SELECT year, price_ft2, price_m2 FROM transactions
            WHERE area=? AND price_ft2 > 0 AND year IS NOT NULL
            ORDER BY year
        """, (area_norm,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT year, price_ft2, price_m2 FROM transactions
            WHERE area=? AND category=? AND price_ft2 > 0 AND year IS NOT NULL
            ORDER BY year
        """, (area_norm, category)).fetchall()

    if not rows:
        return None

    # Group by year
    from collections import defaultdict
    yearly = defaultdict(list)
    for r in rows:
        yearly[r['year']].append((r['price_ft2'], r['price_m2']))

    years_data = []
    for year in sorted(yearly.keys()):
        vals = yearly[year]
        ft_vals = sorted(v[0] for v in vals)
        m2_vals = sorted(v[1] for v in vals if v[1])
        n = len(ft_vals)
        years_data.append({
            'year': str(year),
            'n': n,
            'median_ft': round(ft_vals[n // 2]),
            'median_m2': round(m2_vals[n // 2]) if m2_vals else None,
        })

    # Linear regression
    if len(years_data) >= 2:
        xs = list(range(len(years_data)))
        ys = [y['median_ft'] for y in years_data]
        n = len(xs)
        x_mean = sum(xs) / n
        y_mean = sum(ys) / n
        num = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
        den = sum((xs[i] - x_mean) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0
        slope_pct = slope / y_mean if y_mean != 0 else 0
    else:
        slope_pct = 0

    if slope_pct > 0.03:
        label = 'ارتفاع'
    elif slope_pct < -0.03:
        label = 'انخفاض'
    else:
        label = 'استقرار'

    peak = max(y['median_ft'] for y in years_data)
    latest = years_data[-1]['median_ft']

    return {
        'area': area,
        'category': category,
        'years': years_data,
        'slope_annual_pct': round(slope_pct, 4),
        'label': label,
        'latest_vs_peak_pct': round((latest - peak) / peak, 3) if peak > 0 else 0,
    }


def query_stats(conn: sqlite3.Connection) -> dict:
    """Return DB statistics."""
    total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    date_range = conn.execute(
        "SELECT MIN(date), MAX(date) FROM transactions WHERE date IS NOT NULL"
    ).fetchone()
    areas = conn.execute(
        "SELECT COUNT(DISTINCT area) FROM transactions"
    ).fetchone()[0]
    munis = conn.execute(
        "SELECT municipality, COUNT(*) as c FROM transactions GROUP BY municipality ORDER BY c DESC"
    ).fetchall()

    return {
        'total_transactions': total,
        'date_range': f"{date_range[0]} → {date_range[1]}",
        'distinct_areas': areas,
        'municipalities': {r['municipality']: r['c'] for r in munis},
    }


# ============================================================
# CLI
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 moj_db.py init   <csv_path>           # Create DB from CSV")
        print("  python3 moj_db.py update <csv_path>           # Add new rows")
        print("  python3 moj_db.py stats  [csv_or_db_path]     # Show statistics")
        print("  python3 moj_db.py query  <area> [category] [months]  # Quick query")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'init':
        csv_path = Path(sys.argv[2])
        init_db(csv_path, force=True)

    elif cmd == 'update':
        csv_path = Path(sys.argv[2])
        update_db(csv_path)

    elif cmd == 'stats':
        path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('moj_weekly.csv')
        conn = open_db(path)
        stats = query_stats(conn)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        conn.close()

    elif cmd == 'query':
        area = sys.argv[2] if len(sys.argv) > 2 else 'المعمورة 56'
        category = sys.argv[3] if len(sys.argv) > 3 else 'villa'
        months = int(sys.argv[4]) if len(sys.argv) > 4 else 24
        path = Path(sys.argv[5]) if len(sys.argv) > 5 else Path('moj_weekly.csv')

        conn = open_db(path)
        ref = query_reference(conn, area, category, months)
        print(json.dumps(ref, ensure_ascii=False, indent=2))

        trend = query_trend(conn, area, category)
        if trend:
            print("\n--- Trend ---")
            print(json.dumps(trend, ensure_ascii=False, indent=2))
        conn.close()

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()
