#!/usr/bin/env python3
"""
listing_parsers.py — Parse downloaded listing pages into structured data.

All 3 Qatar listing sources (Mzad, PropertyFinder, arady) use JavaScript
rendering. This module parses their output AFTER download:

Method 1 (Recommended):
    Open the page in Chrome → Ctrl+S → Save as Complete HTML
    → python3 listing_parsers.py parse mzad saved_page.html

Method 2:
    Use browser DevTools → Network → find the API/JSON response
    → python3 listing_parsers.py parse mzad api_response.json

Method 3:
    Export to CSV manually from each site → listing_db.py import

Usage:
    python3 listing_parsers.py parse mzad    <file>  [--area "المعمورة"]
    python3 listing_parsers.py parse pf      <file>  [--area "المعمورة"]
    python3 listing_parsers.py parse arady   <file>  [--area "المعمورة"]
    python3 listing_parsers.py template                # Generate CSV template
"""

import csv
import json
import re
import sys
from pathlib import Path
from typing import Optional


def normalize(s): return re.sub(r'\s+', ' ', s or '').strip()


# ============================================================
# MZAD QATAR PARSER
# ============================================================

def parse_mzad(content: str, area_override: str = None) -> list:
    """
    Parse Mzad Qatar listings from saved HTML or JSON.

    Mzad embeds product data in __NEXT_DATA__ or returns it via API.
    The structured fields include 'Price per Foot' and 'Land Area'.
    """
    listings = []

    # Try JSON first (API response)
    try:
        data = json.loads(content)
        products = _extract_mzad_products(data)
        if products:
            for p in products:
                listing = _mzad_product_to_listing(p, area_override)
                if listing:
                    listings.append(listing)
            return listings
    except json.JSONDecodeError:
        pass

    # Try HTML with __NEXT_DATA__
    m = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', content, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            products = _extract_mzad_products(data)
            for p in products:
                listing = _mzad_product_to_listing(p, area_override)
                if listing:
                    listings.append(listing)
            return listings
        except json.JSONDecodeError:
            pass

    # Try HTML card extraction (fallback)
    cards = re.findall(
        r'<a[^>]*href="(/ar/[^"]*real-estate[^"]*)"[^>]*>.*?'
        r'([\d,]+)\s*(?:ر\.ق|QAR).*?'
        r'([\d,]+)\s*(?:م²|متر)',
        content, re.DOTALL
    )
    for url, price, area in cards:
        listings.append({
            'source': 'mzad',
            'source_id': url.split('/')[-1],
            'url': f'https://www.mzadqatar.com{url}',
            'area_name': area_override or '',
            'property_type': 'land' if 'land' in url or 'أرض' in url else 'villa',
            'price': float(price.replace(',', '')),
            'area_m2': float(area.replace(',', '')),
        })

    return listings


def _extract_mzad_products(data: dict) -> list:
    """Walk through Mzad's nested JSON to find products array."""
    if isinstance(data, list):
        return data

    # Try known paths
    for path in [
        ('props', 'pageProps', 'getCategoryData', 'products'),
        ('props', 'pageProps', 'categoryData', 'products'),
        ('props', 'pageProps', 'data', 'products'),
        ('data', 'products'),
        ('products',),
    ]:
        node = data
        for key in path:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                node = None
                break
        if isinstance(node, list) and node:
            return node
    return []


def _mzad_product_to_listing(p: dict, area_override: str = None) -> Optional[dict]:
    """Convert a single Mzad product to our listing format."""
    props = {normalize(prop.get('name', '')): normalize(prop.get('value', ''))
             for prop in p.get('properties', [])}

    price = p.get('price')
    if isinstance(price, str):
        price = float(price.replace(',', '').replace('QAR', '').strip())

    # Extract structured fields
    area_m2 = None
    price_per_ft = None
    for key, val in props.items():
        if 'مساحة' in key or 'area' in key.lower():
            try:
                area_m2 = float(val.replace(',', '').replace('م²', '').strip())
            except ValueError:
                pass
        if 'فوت' in key or 'foot' in key.lower():
            try:
                price_per_ft = float(val.replace(',', '').strip())
            except ValueError:
                pass

    return {
        'source': 'mzad',
        'source_id': str(p.get('id', '')),
        'url': p.get('url', ''),
        'title': normalize(p.get('title', '')),
        'description': normalize(p.get('description', '')),
        'area_name': area_override or '',
        'property_type': _guess_property_type(p.get('title', '') + ' ' + p.get('category', '')),
        'price': price,
        'area_m2': area_m2,
        'price_per_ft2': price_per_ft,
        'raw_data': p,
    }


# ============================================================
# PROPERTYFINDER PARSER
# ============================================================

def parse_propertyfinder(content: str, area_override: str = None) -> list:
    """Parse PropertyFinder Qatar listings from saved HTML."""
    listings = []

    # PropertyFinder embeds listing data in JSON-LD
    ld_blocks = re.findall(r'application/ld\+json[^>]*>(.*?)</script>', content, re.DOTALL)
    for block in ld_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, list):
                for item in data:
                    l = _pf_item_to_listing(item, area_override)
                    if l:
                        listings.append(l)
            elif isinstance(data, dict) and data.get('@type') == 'Product':
                l = _pf_item_to_listing(data, area_override)
                if l:
                    listings.append(l)
        except json.JSONDecodeError:
            pass

    # Fallback: parse HTML cards
    if not listings:
        cards = re.findall(
            r'data-testid="property-card".*?'
            r'href="([^"]*)".*?'
            r'([\d,]+)\s*(?:QAR|ر\.ق).*?'
            r'([\d,]+)\s*(?:sqm|م²)',
            content, re.DOTALL | re.IGNORECASE
        )
        for url, price, area in cards:
            listings.append({
                'source': 'propertyfinder',
                'source_id': url.split('/')[-1].split('.')[0],
                'url': f'https://www.propertyfinder.qa{url}' if not url.startswith('http') else url,
                'area_name': area_override or '',
                'property_type': 'villa' if 'villa' in url else 'land',
                'price': float(price.replace(',', '')),
                'area_m2': float(area.replace(',', '')),
            })

    return listings


def _pf_item_to_listing(item: dict, area_override: str = None) -> Optional[dict]:
    """Convert a PropertyFinder JSON-LD item to our listing format."""
    offers = item.get('offers', {})
    price = offers.get('price')
    if price:
        try:
            price = float(str(price).replace(',', ''))
        except ValueError:
            price = None

    return {
        'source': 'propertyfinder',
        'source_id': str(item.get('sku', '')),
        'url': item.get('url', ''),
        'title': normalize(item.get('name', '')),
        'description': normalize(item.get('description', '')),
        'area_name': area_override or '',
        'property_type': _guess_property_type(item.get('name', '')),
        'price': price,
        'raw_data': item,
    }


# ============================================================
# ARADY.QA PARSER
# ============================================================

def parse_arady(content: str, area_override: str = None) -> list:
    """Parse arady.qa listings from saved HTML or API response."""
    listings = []

    # Try JSON (API response)
    try:
        data = json.loads(content)
        items = data if isinstance(data, list) else data.get('data', data.get('properties', []))
        for item in items:
            l = _arady_item_to_listing(item, area_override)
            if l:
                listings.append(l)
        return listings
    except json.JSONDecodeError:
        pass

    # Try __NEXT_DATA__
    m = re.search(r'__NEXT_DATA__[^>]*>(.*?)</script>', content, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            # Navigate to properties
            props = data.get('props', {}).get('pageProps', {})
            items = props.get('properties', props.get('listings', []))
            for item in items:
                l = _arady_item_to_listing(item, area_override)
                if l:
                    listings.append(l)
        except json.JSONDecodeError:
            pass

    # Fallback: extract from HTML
    if not listings:
        cards = re.findall(
            r'href="(/ar/property/(\d+)[^"]*)".*?'
            r'([\d,]+)\s*(?:ر\.ق|QAR)',
            content, re.DOTALL
        )
        for url, pid, price in cards:
            listings.append({
                'source': 'arady',
                'source_id': pid,
                'url': f'https://arady.qa{url}',
                'area_name': area_override or '',
                'property_type': 'villa',
                'price': float(price.replace(',', '')),
            })

    return listings


def _arady_item_to_listing(item: dict, area_override: str = None) -> Optional[dict]:
    """Convert an arady.qa item to our listing format."""
    price = item.get('price')
    if isinstance(price, str):
        try:
            price = float(price.replace(',', ''))
        except ValueError:
            price = None

    area_m2 = item.get('area') or item.get('plotArea') or item.get('landArea')
    if isinstance(area_m2, str):
        try:
            area_m2 = float(area_m2.replace(',', '').replace('م²', '').strip())
        except ValueError:
            area_m2 = None

    # Extract foot price from description
    desc = item.get('description', '')
    foot_price = None
    m = re.search(r'(?:الفوت|القدم)\s*[:=]?\s*([\d,]+)', desc)
    if m:
        try:
            foot_price = float(m.group(1).replace(',', ''))
        except ValueError:
            pass

    return {
        'source': 'arady',
        'source_id': str(item.get('id', '')),
        'url': item.get('url', ''),
        'title': normalize(item.get('title', '')),
        'description': normalize(desc),
        'area_name': area_override or normalize(item.get('area', item.get('location', ''))),
        'property_type': _guess_property_type(
            item.get('type', '') + ' ' + item.get('title', '')
        ),
        'price': price,
        'area_m2': area_m2,
        'price_per_ft2': foot_price,
        'bedrooms': item.get('bedrooms'),
        'bathrooms': item.get('bathrooms'),
        'raw_data': item,
    }


# ============================================================
# HELPERS
# ============================================================

def _guess_property_type(text: str) -> str:
    """Guess property type from title/category text."""
    t = normalize(text).lower()
    if any(w in t for w in ['أرض', 'land', 'أراضي']):
        return 'land'
    if any(w in t for w in ['فيلا', 'villa', 'بيت', 'house']):
        return 'villa'
    if any(w in t for w in ['شقة', 'apartment', 'flat']):
        return 'apartment'
    if any(w in t for w in ['كومباوند', 'compound', 'مجمع']):
        return 'compound'
    return 'other'


def generate_csv_template(path: Path = None):
    """Generate an empty CSV template for manual listing import."""
    path = path or Path('listings_template.csv')
    headers = [
        'source', 'source_id', 'area_name', 'property_type', 'price',
        'area_m2', 'bua_m2', 'price_per_ft2', 'bedrooms', 'bathrooms',
        'title', 'description', 'url', 'date_listed',
    ]
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        # Example row
        writer.writerow([
            'manual', '1', 'المعمورة 56', 'villa', '5000000',
            '967', '1210', '480', '5', '4',
            'فيلا 3 طوابق مع ملاحق', 'فيلا مقابل دار السلام مول...', '', '2025-04-01',
        ])
    print(f"✅ Template saved → {path}")


# ============================================================
# CLI
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 listing_parsers.py parse <source> <file> [--area <name>]")
        print("  python3 listing_parsers.py template")
        print()
        print("Sources: mzad, pf (propertyfinder), arady")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'template':
        generate_csv_template()
        return

    if cmd == 'parse':
        source = sys.argv[2]
        file_path = Path(sys.argv[3])
        area = None
        if '--area' in sys.argv:
            area = sys.argv[sys.argv.index('--area') + 1]

        content = file_path.read_text(encoding='utf-8')

        parser = {
            'mzad': parse_mzad,
            'pf': parse_propertyfinder,
            'propertyfinder': parse_propertyfinder,
            'arady': parse_arady,
        }.get(source)

        if not parser:
            print(f"Unknown source: {source}")
            sys.exit(1)

        listings = parser(content, area_override=area)
        print(f"Parsed {len(listings)} listings from {source}")

        if listings:
            # Auto-import into listing_db
            from listing_db import init_db, insert_listing
            conn = init_db()
            inserted = sum(1 for l in listings if insert_listing(conn, l))
            conn.close()
            print(f"Imported {inserted} new listings into {DB_NAME}")

        # Also print summary
        for l in listings[:5]:
            price = l.get('price', 0) or 0
            area_m2 = l.get('area_m2', 0) or 0
            print(f"  {l.get('source_id','?'):>8s}  {price:>12,.0f} QAR  {area_m2:>6,.0f}م²  {l.get('title','')[:40]}")


if __name__ == '__main__':
    main()
