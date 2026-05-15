#!/usr/bin/env python3
"""
prefill_cache.py — Sprint 2.15.1 (L4 offline)

Populate building_age_cache.sqlite with construction-year estimates by
running historical imagery analysis OFFLINE. The resulting cache file is
committed to git and deployed with the slug, giving production instant
(<1ms) age lookups for any pre-computed PIN.

WHY THIS IS OFFLINE:
  On Heroku, the baseline /api/evaluate/details request already takes
  ~24s (GIS + MoJ + factors). The 30s timeout leaves only ~6s budget for
  imagery — too tight to be reliable. Running imagery offline (where
  there is no 30s ceiling and the network is faster) decouples cache
  population from production latency.

USAGE:
  # 1. Prefill from a list of (zone, street, building) tuples:
  python prefill_cache.py --addresses addresses.csv

  # 2. Prefill from a list of PINs:
  python prefill_cache.py --pins pins.txt

  # 3. Prefill by sampling N parcels from a district polygon:
  python prefill_cache.py --district الغرافة --count 50

  # 4. Recompute specific PINs (force refresh, ignore existing cache):
  python prefill_cache.py --pins pins.txt --force

INPUT FORMATS:

  addresses.csv:
    zone,street,building,note
    52,903,90,Al-Luqta test villa
    56,815,12,Bou Hamour
    ...

  pins.txt:
    52200100
    56099695
    56099696
    ...

OUTPUT:
  building_age_cache.sqlite (in the project root, alongside moj_weekly.csv)

CONFIGURATION:
  --time-budget S      max seconds per PIN (default 25; well above the
                       18s typical fresh-compute time)
  --threads N          parallel workers (default 1; GIS rate limits
                       might trigger on higher concurrency)
  --resume             skip PINs already in the cache
  --force              ignore cache, recompute everything
  --dry-run            list what would be computed, don't run imagery
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Optional, Iterable, Iterator

# CRITICAL: enable inline imagery BEFORE importing qatar_gis
# The module-level flag is consulted on import of estimate_construction_year_smart.
import os
os.environ['THAMMEN_ENABLE_INLINE_IMAGERY'] = '1'

import qatar_gis
qatar_gis.ENABLE_INLINE_IMAGERY = True  # belt-and-suspenders

from qatar_gis import QatarGIS
from building_age_cache import BuildingAgeCache


# ─── Input readers ─────────────────────────────────────────────────────────


def read_pins(path: Path) -> Iterator[tuple]:
    """Yield (pin, note) tuples from a flat PIN list file.

    Format: one PIN per line, optional `# comment`, blank lines ignored.
    Note becomes empty string for PIN-only files.
    """
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Allow inline comments: "52200100  # Al-Luqta"
            if '#' in line:
                pin_str, note = line.split('#', 1)
                pin_str = pin_str.strip()
                note = note.strip()
            else:
                pin_str = line
                note = ''
            try:
                yield (int(pin_str), note)
            except ValueError:
                print(f'[skip] invalid PIN: {line!r}', file=sys.stderr)


def read_addresses(path: Path) -> Iterator[tuple]:
    """Yield (zone, street, building, note) tuples from a CSV file."""
    with path.open('r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                z = int(row['zone'])
                s = int(row['street'])
                b = int(row['building'])
                note = row.get('note', '').strip()
                yield (z, s, b, note)
            except (KeyError, ValueError) as e:
                print(f'[skip] bad row: {row} ({e})', file=sys.stderr)


# ─── Single-PIN worker ────────────────────────────────────────────────────


def process_pin(gis: QatarGIS,
                cache: BuildingAgeCache,
                pin: int,
                polygon_4326: list,
                note: str = '',
                time_budget_s: float = 25.0,
                force: bool = False) -> dict:
    """Compute and cache the age estimate for one PIN.

    Returns a status dict with timing and outcome information for the
    progress reporter.
    """
    t0 = time.time()
    status = {
        'pin': pin,
        'note': note,
        'elapsed_s': 0.0,
        'outcome': 'unknown',
    }

    # Skip if already cached (unless --force)
    if not force:
        cached = cache.get(pin)
        if cached and cached.get('earliest_built_year') is not None:
            status['outcome'] = 'cached_skip'
            status['year'] = cached['earliest_built_year']
            status['confidence'] = cached['confidence_years']
            status['elapsed_s'] = time.time() - t0
            return status

    # Run imagery analysis (full mode)
    try:
        estimate = gis.estimate_construction_year_smart(
            polygon_4326=polygon_4326,
            pin=pin,
            time_budget_s=time_budget_s,
        )
    except Exception as e:
        status['outcome'] = 'error'
        status['error'] = str(e)[:200]
        status['elapsed_s'] = time.time() - t0
        return status

    if estimate is None:
        status['outcome'] = 'computation_failed'
        status['elapsed_s'] = time.time() - t0
        return status

    status['outcome'] = 'computed'
    status['year'] = estimate.earliest_built_year
    status['confidence'] = estimate.confidence_years
    status['elapsed_s'] = time.time() - t0
    return status


# ─── Main runner ──────────────────────────────────────────────────────────


def run_addresses(items: Iterable[tuple],
                  cache: BuildingAgeCache,
                  gis: QatarGIS,
                  time_budget_s: float,
                  force: bool,
                  dry_run: bool) -> dict:
    """Resolve each (zone, street, building, note) to a PIN, then process."""
    totals = {'computed': 0, 'cached_skip': 0, 'error': 0,
              'computation_failed': 0, 'unresolved': 0, 'total': 0}

    for item in items:
        totals['total'] += 1
        z, s, b, note = item
        addr_str = f'{z}/{s}/{b}'

        loc = gis.find_property(z, s, b)
        if loc is None or loc.pin is None:
            print(f'  [✗] {addr_str:14} → unresolved (no GIS match)')
            totals['unresolved'] += 1
            continue

        plot = gis.get_plot(loc.pin)
        if plot is None or not plot.polygon_4326:
            print(f'  [✗] {addr_str:14} (PIN {loc.pin}) → no plot polygon')
            totals['unresolved'] += 1
            continue

        if dry_run:
            print(f'  [dry] {addr_str:14} → PIN {loc.pin}, '
                  f'{plot.pdarea}m², {note}')
            continue

        status = process_pin(
            gis, cache, loc.pin, plot.polygon_4326,
            note=note, time_budget_s=time_budget_s, force=force,
        )
        totals[status['outcome']] = totals.get(status['outcome'], 0) + 1

        if status['outcome'] == 'computed':
            print(f'  [✓] {addr_str:14} (PIN {loc.pin}) → {status["year"]} '
                  f'±{status["confidence"]}y  ({status["elapsed_s"]:.1f}s)')
        elif status['outcome'] == 'cached_skip':
            print(f'  [·] {addr_str:14} (PIN {loc.pin}) → cached {status["year"]}')
        else:
            print(f'  [✗] {addr_str:14} (PIN {loc.pin}) → {status["outcome"]}')

    return totals


def run_pins(items: Iterable[tuple],
             cache: BuildingAgeCache,
             gis: QatarGIS,
             time_budget_s: float,
             force: bool,
             dry_run: bool) -> dict:
    """Process each (pin, note) directly without QARS lookup."""
    totals = {'computed': 0, 'cached_skip': 0, 'error': 0,
              'computation_failed': 0, 'unresolved': 0, 'total': 0}

    for pin, note in items:
        totals['total'] += 1

        plot = gis.get_plot(pin)
        if plot is None or not plot.polygon_4326:
            print(f'  [✗] PIN {pin} → no plot polygon')
            totals['unresolved'] += 1
            continue

        if dry_run:
            print(f'  [dry] PIN {pin} → {plot.pdarea}m², {note}')
            continue

        status = process_pin(
            gis, cache, pin, plot.polygon_4326,
            note=note, time_budget_s=time_budget_s, force=force,
        )
        totals[status['outcome']] = totals.get(status['outcome'], 0) + 1

        if status['outcome'] == 'computed':
            print(f'  [✓] PIN {pin:9} → {status["year"]} '
                  f'±{status["confidence"]}y  ({status["elapsed_s"]:.1f}s) '
                  f'{note}')
        elif status['outcome'] == 'cached_skip':
            print(f'  [·] PIN {pin:9} → cached {status["year"]}')
        else:
            print(f'  [✗] PIN {pin:9} → {status["outcome"]}')

    return totals


def main():
    parser = argparse.ArgumentParser(
        description='Prefill building_age_cache.sqlite with construction-year '
                    'estimates from GIS historical imagery.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument('--addresses', type=Path,
                     help='CSV file: zone,street,building,note')
    src.add_argument('--pins', type=Path,
                     help='Plain text file: one PIN per line')

    parser.add_argument('--cache-path', type=Path, default=None,
                        help='Override default cache file location')
    parser.add_argument('--time-budget', type=float, default=25.0,
                        help='Seconds per PIN (default: 25)')
    parser.add_argument('--force', action='store_true',
                        help='Recompute even if PIN is already cached')
    parser.add_argument('--dry-run', action='store_true',
                        help='Resolve addresses but don\'t run imagery')
    args = parser.parse_args()

    # Build cache and GIS
    cache = BuildingAgeCache(db_path=args.cache_path) if args.cache_path \
        else BuildingAgeCache()
    gis = QatarGIS()

    print(f'Cache:        {cache.db_path}')
    print(f'Time budget:  {args.time_budget}s per PIN')
    print(f'Force:        {args.force}')
    print(f'Dry run:      {args.dry_run}')
    print()
    print(f'Cache state at start: {cache.stats()}')
    print()
    print(f'─── Processing ───')

    t_overall = time.time()

    if args.addresses:
        items = read_addresses(args.addresses)
        totals = run_addresses(items, cache, gis,
                               args.time_budget, args.force, args.dry_run)
    else:
        items = read_pins(args.pins)
        totals = run_pins(items, cache, gis,
                          args.time_budget, args.force, args.dry_run)

    elapsed = time.time() - t_overall

    print()
    print(f'─── Summary ───')
    print(f'Total addresses:    {totals["total"]}')
    print(f'  Newly computed:   {totals["computed"]}')
    print(f'  Already cached:   {totals["cached_skip"]}')
    print(f'  Unresolved:       {totals["unresolved"]}')
    print(f'  Errors:           {totals["error"]}')
    print(f'  Compute failed:   {totals["computation_failed"]}')
    print(f'Overall elapsed:    {elapsed:.1f}s')
    print()
    print(f'Cache state at end: {cache.stats()}')


if __name__ == '__main__':
    main()
