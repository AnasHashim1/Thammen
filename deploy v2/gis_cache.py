# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.116 — a small, thread-safe, short-TTL cache for GIS layer responses.

A URL-spy audit (docs/AUDIT_backend_gis_parallelization.md) found ~10 of 35 GIS calls per property eval are
EXACT duplicates: the same QARS / Zoning / Districts / Cadastre / Geometry query fired 2-3× because
`classify` + `property_factors` + `geometric_factors` + `geo_v2` each independently re-query the same layer
for the same location. GIS layer data is static over minutes, so returning the cached response for a
repeated URL is VALUE-INVARIANT (same URL → same bytes) and removes the redundant serial network round-trips.

Design:
- Keyed on the full request URL (+ encoded params). Global (module-level) + thread-safe → dedupes both
  in-request across the concurrent enrichment threads AND same-area repeats across requests.
- Stores the raw response TEXT; each cache HIT re-parses it (`json.loads`) into a FRESH object, so a caller
  that mutates its result can never corrupt the cache or another caller → byte-identical + mutation-safe.
- Only successful (non-None, non-empty) responses are cached; failures are never cached (a transient GIS
  flake is retried, not stuck).
- A short TTL bounds any theoretical staleness; an env kill-switch (`THAMMEN_GIS_CACHE=0`) disables it.
"""
import os
import time
import threading

_TTL_SECONDS = 120.0
_MAX_ENTRIES = 512
_CACHE = {}                       # key -> (expires_at, raw_text)
_LOCK = threading.Lock()
_ENABLED = str(os.environ.get('THAMMEN_GIS_CACHE', '')).strip().lower() not in ('0', 'false', 'off', 'no')


def make_key(url, params=None):
    """Canonical request identity — independent of GET-vs-POST (a large-geometry POST and its GET form share it)."""
    if not url:
        return None
    try:
        if params:
            import urllib.parse
            return url + '?' + urllib.parse.urlencode(params)
        return url
    except Exception:
        return None


def get_text(key):
    """Return the cached raw response TEXT for `key`, or None. Caller re-parses (fresh object per hit)."""
    if not _ENABLED or not key:
        return None
    now = time.time()
    with _LOCK:
        ent = _CACHE.get(key)
        if ent is not None:
            if ent[0] > now:
                return ent[1]
            _CACHE.pop(key, None)
    return None


def put_text(key, text):
    """Cache the raw response TEXT (str). No-op on falsy key/text (never cache empties/failures)."""
    if not _ENABLED or not key or not text:
        return
    now = time.time()
    with _LOCK:
        if len(_CACHE) >= _MAX_ENTRIES:
            for k in [k for k, (exp, _) in list(_CACHE.items()) if exp <= now][:64]:
                _CACHE.pop(k, None)
            while len(_CACHE) >= _MAX_ENTRIES:
                try:
                    _CACHE.pop(next(iter(_CACHE)))
                except StopIteration:
                    break
        _CACHE[key] = (now + _TTL_SECONDS, text)


def clear():
    with _LOCK:
        _CACHE.clear()


def stats():
    with _LOCK:
        return {'enabled': _ENABLED, 'size': len(_CACHE), 'ttl_s': _TTL_SECONDS}
