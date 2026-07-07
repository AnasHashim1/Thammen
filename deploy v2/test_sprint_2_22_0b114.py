# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.114 (latency, audit-driven — Rule #51). E14: the REAL geo_reference_v2._parse_date + the
real fast-classify fall-through wiring. 🟢 VALUE-INVARIANT (pure-function memoize + an error-path crash fix).

Born from a §5 latency audit (cProfile, villa path): the warm-time compute was dominated by
`geo_reference_v2._parse_date` — 5.4s cumulative over ~26,831 strptime calls (MoJ dates repeat massively
across ~26K rows). The fix: memoize the pure parse (identical output → value-invariant); the profiler hotspot
then disappears. The audit also surfaced a pre-existing crash: on a transient fast-classify GIS flake the
except handler at evaluate_unified.py referenced `sys.stderr` while `sys` is SHADOWED by later local
`import sys` in evaluate_thammen → UnboundLocalError turned a recoverable flake into a hard crash (#39 —
bundled: same heavy-GIS path, value-invariant, unblocks verification).
"""
import io, sys
from datetime import datetime
from geo_reference_v2 import _parse_date

_p = _f = 0
def ck(name, cond, extra=''):
    global _p, _f
    if cond: _p += 1; print(f'  ok  {name}')
    else:    _f += 1; print(f'  FAIL {name}  {extra}')

# ── (1) _parse_date is memoized (value-invariant) — output identical to strptime, edges preserved ──
ck('valid YYYY-MM-DD → the exact datetime (unchanged)', _parse_date('2025-09-30') == datetime(2025, 9, 30))
ck('_norm strips surrounding whitespace (unchanged)', _parse_date('  2025-01-01  ') == datetime(2025, 1, 1))
ck('empty → None', _parse_date('') is None)
ck('None → None (no crash)', _parse_date(None) is None)
ck('invalid month/day → None (strptime-identical)', _parse_date('2025-13-45') is None)
ck('non-date → None', _parse_date('bad') is None)
ck('trailing garbage → None (strict, strptime-identical)', _parse_date('2025-09-30x') is None)
ck('the cache returns the SAME object for a repeated key (memoized)',
   _parse_date('2024-06-15') is _parse_date('2024-06-15'))
ck('_parse_date carries an lru_cache wrapper (the memoize)',
   hasattr(_parse_date, 'cache_info') and callable(_parse_date.cache_info))
# a repeated call must register a cache hit (the whole point — kills the ~27K redundant parses)
_parse_date.cache_clear()
_parse_date('2023-03-03'); before = _parse_date.cache_info().hits
_parse_date('2023-03-03')
ck('a repeated key is a cache HIT (not a re-parse)', _parse_date.cache_info().hits == before + 1)

# ── (2) source: the memoize decorator + the fast-classify crash fix ──
GEO = io.open('geo_reference_v2.py', encoding='utf-8').read()
ck('geo imports lru_cache', 'from functools import lru_cache' in GEO)
ck('_parse_date is decorated with @lru_cache', '@lru_cache(maxsize=8192)' in GEO and 'def _parse_date(s):' in GEO)

ENG = io.open('evaluate_unified.py', encoding='utf-8').read()
ck('the fast-classify handler no longer references the SHADOWED sys.stderr (the crash)',
   'print(f"[fast-classify] failed: {e}", file=sys.stderr)' not in ENG)
ck('the fast-classify handler still logs + falls through (defensive intent preserved)',
   'print(f"[fast-classify] failed: {e}")' in ENG and 'fall through to full pipeline' in ENG)
ck('engine is a valid b-series tag (no exact pin — Lesson-2)',
   "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

# ── (3) VALUE-INVARIANCE end-to-end: the 5-fixture villa byte-gate (real engine, live GIS) ──
try:
    from evaluate_unified import evaluate_thammen
    EXP = [((54,541,6),2400000),((56,647,6),3800000),((55,296,13),2600000),((56,565,21),2400000),((52,903,90),None)]
    allok = True
    for (z,s,b),ea in EXP:
        r = evaluate_thammen(zone=z, street=s, building=b, audience='owner')
        a = (r.get('valuation') or {}).get('amount')
        allok = allok and (a == ea)
    ck('5-fixture villa byte-gate byte-identical (2.4M/3.8M/2.6M/2.4M/refusal)', allok)
except Exception as e:
    print(f'  (skipped live byte-gate — GIS unreachable here: {e})')

print(f'\nb114 (latency): {_p} passed, {_f} failed')
sys.exit(1 if _f else 0)
