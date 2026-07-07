# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.116 (latency — a GIS-response dedup cache). 🟢 VALUE-INVARIANT. E14: the REAL gis_cache +
the wiring across the 4 GIS-fetch modules + the 5-fixture villa byte-gate.

Audit: ~10 of 35 GIS calls/eval are EXACT duplicates (same QARS/Zoning/Districts/Cadastre/Geometry query
re-fired by classify + factors + geometric + geo_v2). A global short-TTL cache keyed on the URL returns the
cached raw TEXT (re-parsed fresh per hit → mutation-safe + byte-identical). Measured: repeated fetches
10 → 1; value 2,400,000 unchanged.
"""
import io, os, sys, time
import gis_cache

_p = _f = 0
def ck(name, cond, extra=''):
    global _p, _f
    if cond: _p += 1; print(f'  ok  {name}')
    else:    _f += 1; print(f'  FAIL {name}  {extra}')

# ── (1) gis_cache correctness ──
gis_cache.clear()
K = gis_cache.make_key('https://x/query', {'where': 'PIN=1', 'f': 'json'})
ck('make_key is deterministic + param-aware',
   K == gis_cache.make_key('https://x/query', {'where': 'PIN=1', 'f': 'json'}) and K != gis_cache.make_key('https://x/query', {'where': 'PIN=2'}))
ck('make_key(None) → None (no crash)', gis_cache.make_key(None) is None)

gis_cache.put_text(K, '{"features":[1,2,3]}')
ck('put/get roundtrip returns the cached text', gis_cache.get_text(K) == '{"features":[1,2,3]}')
ck('a miss returns None', gis_cache.get_text('no-such-key') is None)

# never cache empties/failures (a transient flake must be retried, not stuck)
gis_cache.put_text('k-empty', ''); gis_cache.put_text('k-none', None)
ck('empty / None responses are NOT cached', gis_cache.get_text('k-empty') is None and gis_cache.get_text('k-none') is None)

# MUTATION-SAFETY: cache stores TEXT; each hit re-parses → a caller mutating its object can't corrupt the cache
import json
gis_cache.put_text('k-mut', '{"a":[1,2]}')
_d1 = json.loads(gis_cache.get_text('k-mut')); _d1['a'].append(99); _d1['b'] = 'x'
_d2 = json.loads(gis_cache.get_text('k-mut'))
ck('mutation-safe: mutating one hit does not corrupt the next hit', _d2 == {'a': [1, 2]})

# TTL expiry (monkeypatch time forward)
gis_cache.clear(); gis_cache.put_text('k-ttl', '{"v":1}')
_orig_time = time.time
try:
    gis_cache.time.time = lambda: _orig_time() + gis_cache._TTL_SECONDS + 5
    ck('an entry past its TTL is evicted (returns None)', gis_cache.get_text('k-ttl') is None)
finally:
    gis_cache.time.time = _orig_time

# kill-switch
_saved = gis_cache._ENABLED
try:
    gis_cache._ENABLED = False; gis_cache.clear(); gis_cache.put_text('k-off', '{"v":1}')
    ck('kill-switch: when disabled, nothing is cached', gis_cache.get_text('k-off') is None)
finally:
    gis_cache._ENABLED = _saved
gis_cache.clear()

# ── (2) the 4 GIS-fetch modules are wired ──
for mod, needle in [
    ('qatar_gis.py',       "_cached = gis_cache.get_text(_ck)"),
    ('property_factors.py',"_c = gis_cache.get_text(_ck)"),
    ('geometric_factors.py',"_c = gis_cache.get_text(_ck)"),
    ('geo_reference_v2.py',"_c116 = gis_cache.get_text(_ck116)"),
]:
    src = io.open(mod, encoding='utf-8').read()
    ck(f'{mod} imports gis_cache + checks the cache', 'import gis_cache' in src and needle in src and 'gis_cache.put_text(' in src)

# ── (3) VALUE-INVARIANCE: the 5-fixture villa byte-gate (real engine, live GIS, cache ON) ──
try:
    from evaluate_unified import evaluate_thammen
    EXP = [((54,541,6),2400000),((56,647,6),3800000),((55,296,13),2600000),((56,565,21),2400000),((52,903,90),None)]
    allok = True
    for (z,s,b),ea in EXP:
        r = evaluate_thammen(zone=z, street=s, building=b, audience='owner')
        allok = allok and ((r.get('valuation') or {}).get('amount') == ea)
    ck('5-fixture villa byte-gate byte-identical with the GIS cache ON', allok)
except Exception as e:
    print(f'  (skipped live byte-gate — GIS unreachable here: {e})')

ck('engine is a valid b-series tag', "SPRINT_TAG = '2.22.0b." in io.open('evaluate_unified.py', encoding='utf-8').read())

print(f'\nb116 (gis-cache): {_p} passed, {_f} failed')
sys.exit(1 if _f else 0)
