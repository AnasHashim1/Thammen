"""
probe_arady_lands.py — Sprint 2.20 (Land Grid) field-richness + reachability probe.

Verifies, for arady LAND listings, the attributes Sprint 2.20 wants to turn
into adjustment coefficients, and confirms reachability. Designed to run BOTH
locally and on Heroku (the §21.6 production gate — container reachability !=
Heroku reachability).

Measures across a multi-page sample:
  - reachability (HTTP status per page)
  - number_of_roads VALUE distribution (corner signal: how many != 1)
  - land_front_direction richness (the open item — null for villas; lands?)
  - land_sorting, zoning_type, completion_status distributions
  - location granularity (zone vs district vs street)

Pure stdlib. Polite. Reuses the Sprint 2.13 Next.js streaming decode.
Run:  python probe_arady_lands.py        (local)
      heroku run python probe_arady_lands.py   (§21.6 gate)
"""
import json
import re
import sys
import time
import urllib.request
from collections import Counter

UA = {'User-Agent': 'Mozilla/5.0 (research-collection)'}
BASE = 'https://arady.qa/listings/lands'
HARVEST_PAGES = [1, 2, 3, 4, 5]
SAMPLE_N = 25
FIELDS = [
    'number_of_roads', 'land_front_direction', 'land_sorting', 'zoning_type',
    'completion_status', 'size_in_meters', 'price_per_meter', 'price',
    'road_width', 'type', 'description',
]


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode('utf-8', errors='replace')


def decode_chunks(html):
    out = []
    for c in re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html):
        if c:
            try:
                out.append(json.loads('"' + c + '"'))
            except Exception:
                pass
    return ''.join(out)


def find_listing_object(text, pid):
    i = text.find(f'"id":{pid}')
    if i < 0:
        return None
    depth, start = 0, i
    for j in range(i, max(0, i - 6000), -1):
        ch = text[j]
        if ch == '}':
            depth += 1
        elif ch == '{':
            if depth == 0:
                start = j
                break
            depth -= 1
    depth, end = 0, i
    for j in range(start, min(len(text), start + 12000)):
        ch = text[j]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None


def main():
    print("=" * 66)
    print("arady LAND field-richness + reachability probe (Sprint 2.20)")
    print("=" * 66)
    ids = []
    for p in HARVEST_PAGES:
        url = BASE if p == 1 else f"{BASE}?page={p}"
        try:
            status, html = fetch(url)
            found = sorted(set(int(m) for m in re.findall(r'/property/(\d+)', html)))
            for x in found:
                if x not in ids:
                    ids.append(x)
            print(f"[index] page {p}: HTTP {status}, {len(found)} ids")
        except Exception as e:
            print(f"[index] page {p}: ERROR {type(e).__name__}: {str(e)[:100]}")
        time.sleep(0.5)

    if not ids:
        print("\nVERDICT: arady NOT reachable from this host (no ids).")
        return 1
    print(f"\nharvested {len(ids)} distinct land ids; sampling {min(SAMPLE_N, len(ids))} details\n")

    present = Counter()
    roads_dist = Counter()
    dir_dist = Counter()
    sorting_dist = Counter()
    zoning_dist = Counter()
    status_dist = Counter()
    loc_granularity = Counter()
    parsed = 0
    keyset = None
    for k, pid in enumerate(ids[:SAMPLE_N], 1):
        try:
            _, html = fetch(f'https://arady.qa/property/{pid}')
            obj = find_listing_object(decode_chunks(html), pid)
        except Exception as e:
            print(f"  [{k:2d}] {pid}: ERROR {str(e)[:70]}")
            time.sleep(0.6)
            continue
        if not obj:
            print(f"  [{k:2d}] {pid}: not parsed")
            time.sleep(0.6)
            continue
        parsed += 1
        if keyset is None:
            keyset = sorted(obj.keys())
        for f in FIELDS:
            if obj.get(f) not in (None, '', []):
                present[f] += 1
        roads_dist[str(obj.get('number_of_roads'))] += 1
        if obj.get('land_front_direction') not in (None, ''):
            dir_dist[str(obj.get('land_front_direction'))] += 1
        if obj.get('land_sorting') not in (None, ''):
            sorting_dist[str(obj.get('land_sorting'))] += 1
        if obj.get('zoning_type') not in (None, ''):
            zoning_dist[str(obj.get('zoning_type'))] += 1
        status_dist[str(obj.get('completion_status'))] += 1
        loc = obj.get('location') or {}
        loc_granularity['zone' if loc.get('zone') else 'no_zone'] += 1
        loc_granularity['district' if loc.get('district_name_en') else 'no_district'] += 1
        loc_granularity['street' if (loc.get('street') or loc.get('street_no')) else 'no_street'] += 1
        time.sleep(0.6)

    print(f"\nparsed {parsed}/{min(SAMPLE_N, len(ids))} land objects")
    print("\nfield presence rate:")
    for f in FIELDS:
        r = (present[f] / parsed * 100) if parsed else 0
        print(f"  {f:22s} {present[f]:2d}/{parsed}  ({r:4.0f}%)")
    print(f"\nnumber_of_roads VALUES: {dict(roads_dist)}")
    print(f"land_front_direction VALUES (non-null): {dict(dir_dist)}")
    print(f"land_sorting VALUES (non-null): {dict(sorting_dist)}")
    print(f"zoning_type VALUES (non-null): {dict(zoning_dist)}")
    print(f"completion_status VALUES: {dict(status_dist)}")
    print(f"location granularity: {dict(loc_granularity)}")
    if keyset:
        print(f"\nfull key set: {keyset}")

    corner = sum(v for k, v in roads_dist.items() if k not in ('1', 'None'))
    print("\n" + "-" * 66)
    print(f"corner signal: {corner}/{parsed} listings have number_of_roads != 1")
    print(f"direction signal: {len(dir_dist)} distinct directions, "
          f"{sum(dir_dist.values())}/{parsed} populated")
    print("=" * 66)
    return 0


if __name__ == '__main__':
    sys.exit(main())
