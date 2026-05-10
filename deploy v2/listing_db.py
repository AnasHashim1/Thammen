#!/usr/bin/env python3
"""
listing_db.py — Listings database and comparison engine.

Stores listings from arady.qa, PropertyFinder, and Mzad Qatar in SQLite.
Provides comparison queries against MoJ reference for any area.

Sources are JS-rendered, so data is imported via:
  1. listing_parsers.py — parse downloaded HTML/JSON files
  2. Manual CSV import — bulk import from spreadsheet
  3. Future: browser extension or headless browser

Usage:
    python3 listing_db.py init                          # Create empty DB
    python3 listing_db.py import listings.csv            # Import from CSV
    python3 listing_db.py compare "المعمورة 56" villa    # Compare vs MoJ
    python3 listing_db.py stats                          # Show statistics
"""

import csv
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_NAME = 'listings.db'

CREATE_LISTINGS = """
CREATE TABLE IF NOT EXISTS listings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,       -- 'mzad' | 'propertyfinder' | 'arady' | 'manual'
    source_id       TEXT,                -- listing ID from the source
    url             TEXT,
    area_name       TEXT NOT NULL,       -- normalized area name
    municipality    TEXT,
    property_type   TEXT,                -- 'villa' | 'land' | 'apartment' | 'compound'
    price           REAL,                -- asking price (QAR)
    area_m2         REAL,                -- plot area
    bua_m2          REAL,                -- built-up area (if available)
    price_per_m2    REAL,                -- computed: price / area_m2
    price_per_ft2   REAL,                -- from description or computed
    bedrooms        INTEGER,
    bathrooms       INTEGER,
    description     TEXT,                -- full Arabic description
    title           TEXT,
    date_scraped    TEXT,                -- ISO date
    date_listed     TEXT,                -- when the listing was posted (if available)
    listing_age_days INTEGER,            -- computed
    has_red_flag    BOOLEAN DEFAULT 0,   -- auto-detected from description
    red_flag_detail TEXT,
    has_green_flag  BOOLEAN DEFAULT 0,
    green_flag_detail TEXT,
    is_active       BOOLEAN DEFAULT 1,   -- mark inactive instead of deleting
    raw_json        TEXT,                -- original data for debugging
    UNIQUE(source, source_id)
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_list_area ON listings(area_name);",
    "CREATE INDEX IF NOT EXISTS idx_list_type ON listings(property_type);",
    "CREATE INDEX IF NOT EXISTS idx_list_area_type ON listings(area_name, property_type);",
    "CREATE INDEX IF NOT EXISTS idx_list_active ON listings(is_active);",
]


def normalize(s): return re.sub(r'\s+', ' ', s or '').strip()


def init_db(db_path: Path = None) -> sqlite3.Connection:
    """Create listings database."""
    db_path = db_path or Path(DB_NAME)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(CREATE_LISTINGS)
    for idx in CREATE_INDEXES:
        conn.execute(idx)
    conn.commit()
    return conn


def insert_listing(conn: sqlite3.Connection, listing: dict) -> bool:
    """Insert a single listing. Returns True if new, False if duplicate."""
    # Compute derived fields
    price = listing.get('price')
    area_m2 = listing.get('area_m2')
    if price and area_m2 and area_m2 > 0:
        listing.setdefault('price_per_m2', round(price / area_m2))
        listing.setdefault('price_per_ft2', round(price / area_m2 / 10.764))

    listing['date_scraped'] = listing.get('date_scraped', datetime.now().strftime('%Y-%m-%d'))
    listing['area_name'] = normalize(listing.get('area_name', ''))

    # Auto-detect flags from description
    desc = listing.get('description', '')
    if desc:
        from evaluate_property import analyze_listing_description
        flags = analyze_listing_description(desc)
        listing['has_red_flag'] = flags.has_excluding_red_flag
        if flags.red_flags:
            listing['red_flag_detail'] = '; '.join(f['label'] for f in flags.red_flags)
        if flags.green_flags:
            listing['has_green_flag'] = True
            listing['green_flag_detail'] = '; '.join(g['label'] for g in flags.green_flags)

    try:
        conn.execute("""
            INSERT OR IGNORE INTO listings
            (source, source_id, url, area_name, municipality, property_type,
             price, area_m2, bua_m2, price_per_m2, price_per_ft2,
             bedrooms, bathrooms, description, title,
             date_scraped, date_listed, listing_age_days,
             has_red_flag, red_flag_detail, has_green_flag, green_flag_detail,
             raw_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            listing.get('source', 'manual'),
            listing.get('source_id'),
            listing.get('url'),
            listing['area_name'],
            listing.get('municipality'),
            listing.get('property_type'),
            listing.get('price'),
            listing.get('area_m2'),
            listing.get('bua_m2'),
            listing.get('price_per_m2'),
            listing.get('price_per_ft2'),
            listing.get('bedrooms'),
            listing.get('bathrooms'),
            listing.get('description'),
            listing.get('title'),
            listing['date_scraped'],
            listing.get('date_listed'),
            listing.get('listing_age_days'),
            listing.get('has_red_flag', False),
            listing.get('red_flag_detail'),
            listing.get('has_green_flag', False),
            listing.get('green_flag_detail'),
            json.dumps(listing.get('raw_data'), ensure_ascii=False) if listing.get('raw_data') else None,
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def import_csv(conn: sqlite3.Connection, csv_path: Path) -> tuple:
    """
    Import listings from CSV.

    Expected columns: source, source_id, area_name, property_type, price,
                      area_m2, title, description, url, date_listed
    """
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        inserted = 0
        skipped = 0
        for row in reader:
            listing = {normalize(k): normalize(v) for k, v in row.items()}
            # Convert numeric fields
            for field in ('price', 'area_m2', 'bua_m2', 'price_per_m2', 'price_per_ft2'):
                if field in listing and listing[field]:
                    try:
                        listing[field] = float(listing[field].replace(',', ''))
                    except ValueError:
                        listing[field] = None
            for field in ('bedrooms', 'bathrooms'):
                if field in listing and listing[field]:
                    try:
                        listing[field] = int(listing[field])
                    except ValueError:
                        listing[field] = None

            if insert_listing(conn, listing):
                inserted += 1
            else:
                skipped += 1

    return inserted, skipped


def query_listings(conn: sqlite3.Connection, area: str,
                   property_type: str = None,
                   min_area: float = None, max_area: float = None,
                   max_age_days: int = 60,
                   exclude_flagged: bool = True,
                   limit: int = 20) -> list:
    """Query active listings for comparison."""
    area_norm = normalize(area)
    conditions = ["is_active = 1", "area_name = ?"]
    params = [area_norm]

    if property_type:
        conditions.append("property_type = ?")
        params.append(property_type)
    if min_area:
        conditions.append("area_m2 >= ?")
        params.append(min_area)
    if max_area:
        conditions.append("area_m2 <= ?")
        params.append(max_area)
    if exclude_flagged:
        conditions.append("has_red_flag = 0")

    where = " AND ".join(conditions)
    rows = conn.execute(f"""
        SELECT * FROM listings
        WHERE {where}
        ORDER BY date_scraped DESC
        LIMIT ?
    """, params + [limit]).fetchall()

    return [dict(r) for r in rows]


def compare_with_moj(conn: sqlite3.Connection, area: str,
                     property_type: str, moj_median_per_m2: float,
                     size_lo: float = 0, size_hi: float = 99999) -> dict:
    """
    Compare listings against MoJ median for the same area + type + size.

    Returns summary: how many below/at/above MoJ, and the gap distribution.
    """
    listings = query_listings(
        conn, area, property_type,
        min_area=size_lo, max_area=size_hi,
    )

    if not listings:
        return {'n_listings': 0, 'note': 'لا توجد إعلانات في هذه المنطقة/الشريحة'}

    below = []
    at_market = []
    above = []
    rejected = []

    for l in listings:
        pm2 = l.get('price_per_m2')
        if not pm2 or pm2 <= 0:
            continue
        gap_pct = (pm2 - moj_median_per_m2) / moj_median_per_m2

        entry = {
            'source': l['source'],
            'source_id': l['source_id'],
            'title': l['title'],
            'price': l['price'],
            'area_m2': l['area_m2'],
            'price_per_m2': pm2,
            'gap_pct': round(gap_pct * 100, 1),
            'url': l['url'],
        }

        if gap_pct <= -0.05:
            below.append(entry)
        elif gap_pct <= 0.10:
            at_market.append(entry)
        elif gap_pct <= 0.30:
            above.append(entry)
        else:
            rejected.append(entry)

    below.sort(key=lambda x: x['gap_pct'])
    above.sort(key=lambda x: x['gap_pct'])

    # Compute listing median
    all_pm2 = [l.get('price_per_m2', 0) for l in listings if l.get('price_per_m2')]
    listing_median = sorted(all_pm2)[len(all_pm2) // 2] if all_pm2 else None
    gap_listing_vs_moj = None
    if listing_median:
        gap_listing_vs_moj = round((listing_median - moj_median_per_m2) / moj_median_per_m2 * 100, 1)

    return {
        'n_listings': len(listings),
        'moj_median_per_m2': moj_median_per_m2,
        'listing_median_per_m2': listing_median,
        'gap_listing_vs_moj_pct': gap_listing_vs_moj,
        'below_moj': below,
        'at_market': at_market,
        'above_moj': above,
        'rejected': rejected,
        'summary': {
            'bargains': len(below),
            'at_market': len(at_market),
            'overpriced': len(above),
            'rejected': len(rejected),
        }
    }


def stats(conn: sqlite3.Connection) -> dict:
    """Listing database statistics."""
    total = conn.execute("SELECT COUNT(*) FROM listings WHERE is_active=1").fetchone()[0]
    by_source = conn.execute("""
        SELECT source, COUNT(*) as c FROM listings
        WHERE is_active=1 GROUP BY source ORDER BY c DESC
    """).fetchall()
    by_area = conn.execute("""
        SELECT area_name, COUNT(*) as c FROM listings
        WHERE is_active=1 GROUP BY area_name ORDER BY c DESC LIMIT 10
    """).fetchall()
    flagged = conn.execute("SELECT COUNT(*) FROM listings WHERE has_red_flag=1").fetchone()[0]

    return {
        'total_active': total,
        'flagged_excluded': flagged,
        'by_source': {r['source']: r['c'] for r in by_source},
        'top_areas': {r['area_name']: r['c'] for r in by_area},
    }


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 listing_db.py init")
        print("  python3 listing_db.py import <csv_path>")
        print("  python3 listing_db.py compare <area> <type> <moj_median_per_m2>")
        print("  python3 listing_db.py stats")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'init':
        conn = init_db()
        print(f"✅ Created {DB_NAME}")
        conn.close()

    elif cmd == 'import':
        conn = init_db()
        csv_path = Path(sys.argv[2])
        inserted, skipped = import_csv(conn, csv_path)
        print(f"✅ Imported: {inserted} new, {skipped} skipped")
        conn.close()

    elif cmd == 'compare':
        area = sys.argv[2]
        ptype = sys.argv[3] if len(sys.argv) > 3 else 'villa'
        moj_med = float(sys.argv[4]) if len(sys.argv) > 4 else 5000
        conn = init_db()
        result = compare_with_moj(conn, area, ptype, moj_med)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        conn.close()

    elif cmd == 'stats':
        conn = init_db()
        s = stats(conn)
        print(json.dumps(s, ensure_ascii=False, indent=2))
        conn.close()


if __name__ == '__main__':
    main()
