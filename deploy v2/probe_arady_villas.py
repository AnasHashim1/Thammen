"""
probe_arady_villas.py — Sprint 2.20 pre-audit probe (NOT deployed permanently).

Question this answers (audit checklist items 1 + 2):
  - Is arady reachable, and which /listings/<slug> serves villas?
  - For a sample of VILLA detail pages, what is the presence rate of the
    attributes Sprint 2.20 wants to turn into adjustment coefficients:
      number_of_roads (corner), land_front_direction (orientation),
      completion_status (off-plan filter), size_in_meters, price_per_meter,
      and location granularity (zone/district vs street/building).

Reuses the proven Sprint 2.13 Next.js streaming decode (backtest/seed_from_arady.py).
Pure stdlib. Polite (sleeps between fetches). Samples a small N.

Run locally:   python probe_arady_villas.py
Run on Heroku: heroku run python probe_arady_villas.py   (the §21.6 gate)
"""
import json
import re
import sys
import time
import urllib.request
from collections import Counter

UA = {'User-Agent': 'Mozilla/5.0 (research-collection)'}
SAMPLE_N = 30
TARGET_FIELDS = [
    'number_of_roads', 'land_front_direction', 'completion_status',
    'size_in_meters', 'price_per_meter', 'price', 'type', 'description',
    'road_width', 'furnishing', 'beds', 'baths',
]
# Candidate index slugs for villas (lands is the known-good one from 2.13).
INDEX_CANDIDATES = [
    'https://arady.qa/listings/villas',
    'https://arady.qa/listings/houses',
    'https://arady.qa/listings/residential',
    'https://arady.qa/listings/villa',
    'https://arady.qa/listings/properties',
]


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode('utf-8', errors='replace')


def decode_chunks(html):
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
    out = []
    for c in chunks:
        if not c:
            continue
        try:
            out.append(json.loads('"' + c + '"'))
        except Exception:
            pass
    return ''.join(out)


def find_listing_object(decoded_text, prop_id):
    i = decoded_text.find(f'"id":{prop_id}')
    if i < 0:
        return None
    depth = 0
    start = i
    for j in range(i, max(0, i - 6000), -1):
        ch = decoded_text[j]
        if ch == '}':
            depth += 1
        elif ch == '{':
            if depth == 0:
                start = j
                break
            depth -= 1
    depth = 0
    end = i
    for j in range(start, min(len(decoded_text), start + 12000)):
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


def harvest(index_url):
    status, html = fetch(index_url)
    ids = sorted(set(int(m) for m in re.findall(r'/property/(\d+)', html)))
    return status, ids


def main():
    print("=" * 68)
    print("arady VILLA field-coverage probe (Sprint 2.20 pre-audit)")
    print("=" * 68)

    chosen_url, ids = None, []
    for url in INDEX_CANDIDATES:
        try:
            status, found = harvest(url)
            print(f"[index] {url} -> HTTP {status}, {len(found)} property ids")
            if found and len(found) > len(ids):
                chosen_url, ids = url, found
        except Exception as e:
            print(f"[index] {url} -> ERROR {type(e).__name__}: {str(e)[:120]}")
        time.sleep(0.5)

    if not ids:
        print("\nNO villa listings harvested from any candidate slug.")
        print("VERDICT: cannot probe villa fields — slug unknown or arady unreachable.")
        return 1

    print(f"\n[chosen] {chosen_url} ({len(ids)} ids, page-1 only)")
    sample = ids[:SAMPLE_N]
    print(f"[sample] probing {len(sample)} detail pages\n")

    present = Counter()
    type_counter = Counter()
    roads_dist = Counter()
    zone_dist = Counter()
    parsed = 0
    first_obj_keys = None
    examples = []

    for k, pid in enumerate(sample, 1):
        try:
            _, html = fetch(f'https://arady.qa/property/{pid}')
            obj = find_listing_object(decode_chunks(html), pid)
        except Exception as e:
            print(f"  [{k:2d}] property/{pid}: fetch/parse ERROR {str(e)[:80]}")
            time.sleep(0.6)
            continue
        if not obj:
            print(f"  [{k:2d}] property/{pid}: object not found in payload")
            time.sleep(0.6)
            continue
        parsed += 1
        if first_obj_keys is None:
            first_obj_keys = sorted(obj.keys())
        type_counter[obj.get('type')] += 1
        roads_dist[str(obj.get('number_of_roads'))] += 1
        for f in TARGET_FIELDS:
            if obj.get(f) not in (None, '', []):
                present[f] += 1
        loc = obj.get('location') or {}
        zone_dist[str(loc.get('zone'))] += 1
        examples.append({
            'id': pid, 'type': obj.get('type'),
            'number_of_roads': obj.get('number_of_roads'),
            'land_front_direction': obj.get('land_front_direction'),
            'completion_status': obj.get('completion_status'),
            'has_street': bool(loc.get('street') or loc.get('street_no')),
            'zone': loc.get('zone'), 'district': loc.get('district_name_en'),
        })
        print(f"  [{k:2d}] property/{pid}: type={obj.get('type')} "
              f"roads={obj.get('number_of_roads')} "
              f"dir={obj.get('land_front_direction')} "
              f"status={obj.get('completion_status')}")
        time.sleep(0.6)

    print("\n" + "-" * 68)
    print(f"parsed {parsed}/{len(sample)} listing objects")
    print(f"type distribution: {dict(type_counter)}")
    print("\nfield presence rate (of parsed objects):")
    for f in TARGET_FIELDS:
        rate = (present[f] / parsed * 100) if parsed else 0
        print(f"  {f:24s} {present[f]:2d}/{parsed}  ({rate:4.0f}%)")
    print(f"\nnumber_of_roads distribution: {dict(roads_dist)}")
    print(f"zone distribution (n villas per zone): {dict(zone_dist)}")
    if first_obj_keys:
        print(f"\nfull key set of first parsed object:\n  {first_obj_keys}")
    print("\nexamples (location granularity check):")
    for ex in examples[:6]:
        print(f"  {ex}")
    print("=" * 68)
    return 0


if __name__ == '__main__':
    sys.exit(main())
