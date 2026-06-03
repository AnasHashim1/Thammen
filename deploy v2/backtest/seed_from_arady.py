"""
Sprint 2.13 — seed_from_arady.py

Scrapes arady.qa current land listings (first page of /listings/lands) and
writes a CSV with one row per listing. The output feeds backtest_market.py.

This is a refresh-on-demand tool. Run periodically (weekly/monthly) to
re-seed the dataset. The output filename embeds today's date so multiple
snapshots can coexist.

Usage (Windows):
    cd /d "C:\Thammen\deploy v2\backtest"
    python seed_from_arady.py

Output:
    arady_lands_YYYY-MM-DD.csv     (in current directory)

LIMITATIONS:
    - arady's first-page pagination only (~20-30 listings). Pages 2+ are
      JS-rendered and unreachable without a headless browser. This is fine
      — the seed is meant to be representative, not exhaustive.
    - Listings without a `type=land` filter slip through occasionally;
      they are auto-skipped in flatten().
    - No street/building data in arady — only zone + city. Therefore the
      output cannot be fed to /api/evaluate; it is consumed by
      backtest_market.py which compares against local MoJ data directly.
"""
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

OUT_DIR = Path(__file__).parent
UA = {'User-Agent': 'Mozilla/5.0 (research-collection)'}

# Step 1: pull listing index pages and harvest property IDs
INDEX_URL = 'https://arady.qa/listings/lands'


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='replace')


def harvest_property_ids():
    """First page only — Next.js JS pagination prevents access to deeper pages."""
    html = fetch(INDEX_URL)
    ids = sorted(set(int(m) for m in re.findall(r'/property/(\d+)', html)))
    return ids


def decode_chunks(html):
    """Decode the Next.js streaming payload chunks into one big string with
    Unicode properly resolved (arady triple-encodes Arabic via JSON escapes
    inside a JSON string inside HTML)."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
    out = []
    for c in chunks:
        if not c:
            continue
        # The chunk is JSON-string-escaped. Wrap & parse to decode.
        try:
            decoded = json.loads('"' + c + '"')
            out.append(decoded)
        except Exception:
            pass
    return ''.join(out)


def find_listing_object(decoded_text, prop_id):
    """Locate the JSON object describing the listing in the decoded payload."""
    needle = f'"id":{prop_id},"type":"land"'
    i = decoded_text.find(needle)
    if i < 0:
        # Try other types — sometimes residential_land etc.
        i = decoded_text.find(f'"id":{prop_id}')
        if i < 0:
            return None
    # Walk back to find the opening brace
    depth = 0
    start = i
    for j in range(i, max(0, i - 4000), -1):
        ch = decoded_text[j]
        if ch == '}':
            depth += 1
        elif ch == '{':
            if depth == 0:
                start = j
                break
            depth -= 1
    # Walk forward to find the closing brace
    depth = 0
    end = i
    for j in range(start, min(len(decoded_text), start + 8000)):
        ch = decoded_text[j]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    try:
        return json.loads(decoded_text[start:end])
    except json.JSONDecodeError:
        return None


def fetch_listing(prop_id):
    """Fetch a single property page and parse its listing object."""
    html = fetch(f'https://arady.qa/property/{prop_id}')
    decoded = decode_chunks(html)
    obj = find_listing_object(decoded, prop_id)
    return obj


def flatten(obj):
    """Flatten the listing object to a CSV-friendly dict."""
    loc = obj.get('location') or {}
    cat = obj.get('category') or {}
    return {
        'property_id': obj.get('id'),
        'type': obj.get('type'),
        'title': obj.get('title'),
        'category_text': cat.get('text'),
        'category_type': cat.get('type'),
        'price_qar': obj.get('price'),
        'price_per_m2_qar': obj.get('price_per_meter'),
        'size_m2': obj.get('size_in_meters'),
        'zone_no': loc.get('zone'),
        'city_ar': loc.get('city_name_ar'),
        'city_en': loc.get('city_name_en'),
        'district_ar': loc.get('district_name_ar'),
        'district_en': loc.get('district_name_en'),
        'municipality': loc.get('municipality_name'),
        'views': obj.get('count_views'),
        'published': obj.get('published_at'),
        'refreshed': obj.get('refreshed_at'),
        'num_roads': obj.get('number_of_roads'),
        'road_width': obj.get('road_width'),
        'description_first_120': (obj.get('description') or '').replace('\n', ' ')[:120],
        'source_url': f'https://arady.qa/property/{obj.get("id")}',
    }


def main():
    ids = harvest_property_ids()
    print(f'Harvested {len(ids)} property IDs from arady.qa/listings/lands')
    rows = []
    for i, pid in enumerate(ids, 1):
        print(f'[{i:2d}/{len(ids)}] property/{pid}', end=' ', flush=True)
        try:
            obj = fetch_listing(pid)
        except Exception as e:
            print(f'  ❌ fetch error: {e}')
            time.sleep(1)
            continue
        if not obj:
            print('  ❌ could not parse listing object')
            time.sleep(0.5)
            continue
        if obj.get('type') != 'land':
            print(f'  ⚠ skipped (type={obj.get("type")})')
            continue
        row = flatten(obj)
        rows.append(row)
        print(f'  ✓ {row["title"][:40]:40s} {row["price_qar"]:,} @ '
              f'{row["price_per_m2_qar"]:,}/m²  zone={row["zone_no"]}')
        time.sleep(0.6)

    if not rows:
        print('No rows scraped. Aborting.')
        return 1

    out_csv = OUT_DIR / f'arady_lands_{date.today().isoformat()}.csv'
    keys = list(rows[0].keys())
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f'\n✅ saved {out_csv}  ({len(rows)} rows)')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
