"""
audit_a6_latency.py — Sprint 2.18 Phase 1 → extended for Branch B §3.1
=====================================================================

Profile end-to-end /api/evaluate latency with a per-phase breakdown so we can
identify what to fix. **No engine code change.** This is a measurement
instrument.

Branch B §3.1 extension (2026-05-29, A14 real-fix audit) — closes the
worker-thread blind spot that made the original capture a FLOOR (§0.3 of
BRIEF_BranchB_villa_GIS_latency_v2.md):
  * GLOBAL thread-safe trace buffer (was threading.local) → captures the
    ThreadPoolExecutor worker threads: property_factors 5-way fan-out
    ('factors_*') AND _expand_extent BFS prefetch ('bfs_prefetch_*').
  * NEW wrapper on qatar_gis._fetch_zoning_at_point — the raw-urllib A11
    zoning cross-check that bypasses _http_get_json (tagged gis.zoning_xcheck).
  * Per-event (thread, t0, t1) capture → wall-clock UNION (overlap-merged) so
    the phase table reconciles to ~total instead of over-counting parallel
    work; a per-thread split exposes what is ALREADY parallel (§3.2 prep).
  * FAITHFUL PASS (2026-05-29, after the first run exposed a ~9.2s villa
    'cpu' that was actually uncaptured secondary-module network): now ALSO
    captures geo_reference_v2's 3 raw-urllib district/zoning fallbacks
    (georef_*), geometric_factors._http_get_json (geom.*, redundant with
    property_factors), property_geo._fetch (pgeo.*), and QatarGIS.get_tile
    (gis.imagery_tile). AND loads gis_preload at setup so in-process district
    lookups are memory-served exactly as production — removing the
    in-process-only district artifact. With ~all engine network captured,
    'compute_ms' finally reflects TRUE production compute.
  * STILL not traced: the hybrid PropertyFinder connector (requests-based,
    apartments only — the villa target makes no such call). Any residual
    untraced network still lands in 'compute_ms' (total − gis_wallclock).

Two measurements per (address × rep):

  (A) IN-PROCESS — call `evaluate_thammen(...)` directly inside the dyno.
      HTTP wrappers are monkey-patched so each GIS call is timed and tagged
      by phase. Measures pure engine + outbound GIS network.

  (B) HTTP — POST to https://thammen.qa/api/evaluate. Measures the full
      user-visible latency stack (Cloudflare + WAF + Heroku router + dyno
      queue + the engine itself). The difference (B) − (A) is "non-engine
      overhead" — useful to know whether to optimize the engine vs. the edge.

Cohort = 7 diverse addresses (Bug A6 trigger, multi-QARS, compound_large,
        raw-land PIN, governmental-zoning x-check, Lusail apt [discovered],
        safe villa baseline). Reps = 3 per address (cold/warm/peak).

Rate limit: production API enforces 10/minute, so HTTP requests are spaced
7s apart. In-process runs bypass the limiter (they don't touch api.py).

Per CLAUDE.md Rule #34 (file-based scripts for multi-step probes) and Rule
#33 (empirical-first audits — measure before code).

Run from Heroku one-off dyno:
  heroku run --app thammen-app-123 python audit_a6_latency.py

Output:
  - Human-readable progress lines to stdout (tagged for grep)
  - Full JSON to stdout between BEGIN/END markers (captured by heroku run)
  - Side-effect file /tmp/audit_a6_results.json (ephemeral on dyno)
"""
import json
import sys
import time
import threading
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime


# ============================================================
# 1. CONFIG
# ============================================================

THAMMEN_BASE = 'https://thammen.qa'
UA = 'Thammen-A6-Audit/Sprint2.18-Phase1'

# 7-address cohort. Slot 5 (lusail_apt) is filled by discover_lusail_apt()
# at runtime — we don't hard-code an address we haven't verified exists.
COHORT_BASE = [
    {'id': 'safe_villa_52',  'label': '52/903/90 Bou Hamour villa (safe baseline)',
     'mode': 'address', 'body': {'zone': 52, 'street': 903, 'building': 90}},

    {'id': 'a6_trigger_51',  'label': '51/835/17 (KNOWN A6 ~31s timeout)',
     'mode': 'address', 'body': {'zone': 51, 'street': 835, 'building': 17}},

    {'id': 'multi_qars_56',  'label': '56/565/21 Bou Hamour multi-QARS trigger',
     'mode': 'address', 'body': {'zone': 56, 'street': 565, 'building': 21}},

    {'id': 'compound_large', 'label': 'PIN 66030258 compound_large',
     'mode': 'pin',     'body': {'pin': '66030258'}},

    {'id': 'lusail_apt',     'label': 'Lusail apartment_building (discovered at runtime)',
     'mode': 'address', 'body': None, 'discover': 'lusail_apt'},

    {'id': 'khor_land',      'label': 'PIN 74328443 الخور raw_land (CHANGELOG_v42 fixture)',
     'mode': 'pin',     'body': {'pin': '74328443'}},

    {'id': 'works_a11',      'label': '61/875/20 أشغال (A11 zoning x-check)',
     'mode': 'address', 'body': {'zone': 61, 'street': 875, 'building': 20}},
]

REPS = 3
HTTP_INTERREQ_DELAY_S = 7.0    # respect rate-limit 10/min
HTTP_TIMEOUT_S = 60.0          # we WANT to see 30s+ rather than masking
INPROC_INTERREQ_DELAY_S = 1.0  # short breather between in-process reps


# ============================================================
# 2. PHASE CLASSIFIER (URL → phase tag)
# ============================================================

def classify_phase(url: str) -> str:
    # qatar_gis ENDPOINTS
    if '/QARS/QARS_Point/' in url:               return 'gis.qars_primary'
    if '/Vector/QARS_Search/' in url:            return 'gis.qars_legacy'
    if '/Vector/CadastrePlots/' in url:          return 'gis.cadastre'
    if '/Vector/Districts/' in url:              return 'gis.districts'
    if '/Vector/General_Landuse/' in url:        return 'gis.landuse'
    if '/Utilities/Geometry/' in url:            return 'gis.geometry_project'
    # property_factors LAYER_URLS
    if '/Vector/Zoning/' in url:                 return 'gis.zoning'
    if '/Vector/Commercial_StreetsA/' in url:    return 'gis.commercial_streets'
    if '/Vector/Landmarks/' in url:              return 'gis.landmarks'
    if '/Vector/ROADFlowlnA/MapServer/1' in url: return 'gis.local_roads'
    if '/Vector/ROADFlowlnA/MapServer/2' in url: return 'gis.main_roads'
    # khazna other (e.g. spatial queries via QARS for multi_qars detection)
    if 'khazna.gisqatar.org.qa' in url:          return 'gis.khazna_other'
    if 'gisqatar.org.qa' in url:                 return 'gis.other'
    return 'other'


# ============================================================
# 3. GLOBAL THREAD-SAFE TRACE BUFFER  (Branch B §3.1)
# ============================================================
# Was threading.local() — which silently dropped every event recorded on a
# ThreadPoolExecutor worker ('factors_*' + 'bfs_prefetch_*'), making the
# original capture a FLOOR (BRIEF §0.3). One shared, lock-guarded buffer + a
# per-rep epoch lets us reconcile the whole timeline (main + all workers) and
# compute wall-clock overlap. Lock is held only for the microsecond append, so
# contention is negligible against ~hundreds-of-ms network calls.

class _Tracer:
    def __init__(self):
        self._lock = threading.Lock()
        self.events = []
        self.epoch = None

    def reset(self):
        with self._lock:
            self.events = []
            self.epoch = time.perf_counter()

    def record(self, phase, t_start, t_end, ok):
        th = threading.current_thread().name
        with self._lock:
            ep = self.epoch if self.epoch is not None else t_start
            self.events.append({
                'phase':  phase,
                't_ms':   round((t_end - t_start) * 1000.0, 1),
                't0_ms':  round((t_start - ep) * 1000.0, 1),
                't1_ms':  round((t_end - ep) * 1000.0, 1),
                'thread': th,
                'ok':     ok,
            })

    def snapshot(self):
        with self._lock:
            return list(self.events)

_tracer = _Tracer()

def _trace_reset():
    _tracer.reset()

def _trace_events():
    return _tracer.snapshot()


# ============================================================
# 4. MONKEY-PATCH HTTP WRAPPERS
# ============================================================
# All three wrappers record (phase, t_start, t_end, ok) into the global
# tracer. Behaviour is otherwise byte-identical to the originals (same args,
# same return value, same exception-swallowing) — the audit must not change
# what the engine does, only observe it.

def patch_qatar_gis_wrapper():
    """Wrap qatar_gis._http_get_json so each call is timed + phase-tagged.
    Covers QARS (incl. multi-QARS spatial via _qars_query), cadastre,
    districts, landuse, and the ESRI geometry-project round-trip. Fires on the
    main thread AND on 'bfs_prefetch_*' workers (_expand_extent prefetch)."""
    import qatar_gis
    orig = qatar_gis._http_get_json

    def patched(url, params=None, timeout=30):
        # Tag by the OUTGOING URL (post-encoding) so POST-fallback paths
        # (Rule #48) are also categorized by their target layer.
        full = url + ('?' + urllib.parse.urlencode(params, safe='/:,') if params else '')
        phase = classify_phase(full)
        t0 = time.perf_counter()
        ok = True
        try:
            res = orig(url, params=params, timeout=timeout)
            if res is None:
                ok = False
        except Exception:
            res = None
            ok = False
        _tracer.record(phase, t0, time.perf_counter(), ok)
        return res

    qatar_gis._http_get_json = patched
    return orig


def patch_property_factors_wrapper():
    """Wrap property_factors._query_gis (separate raw-urllib path: landmarks,
    zoning, roads, commercial-streets). Runs on the 'factors_*' worker threads
    of the 5-way fan-out — now captured via the global tracer."""
    import property_factors
    orig = property_factors._query_gis
    timeout_default = getattr(property_factors, 'TIMEOUT', 10)

    def patched(layer_url, params, timeout=timeout_default):
        phase = classify_phase(layer_url)
        t0 = time.perf_counter()
        ok = True
        try:
            res = orig(layer_url, params, timeout=timeout)
        except Exception:
            res = []
            ok = False
        _tracer.record(phase, t0, time.perf_counter(), ok)
        return res

    property_factors._query_gis = patched
    return orig


def patch_zoning_xcheck_wrapper():
    """Wrap qatar_gis._fetch_zoning_at_point — the A11 zoning cross-check that
    issues its OWN raw urllib request (bypassing _http_get_json), so it was
    invisible to both wrappers above even on the main thread. Tagged distinctly
    as gis.zoning_xcheck to separate it from the property_factors zoning factor
    (gis.zoning). The function already swallows its own exceptions, so 'ok' is
    effectively always True here; the duration is the signal we want."""
    import qatar_gis
    orig = qatar_gis._fetch_zoning_at_point

    def patched(lat, lon, timeout=4.0):
        t0 = time.perf_counter()
        ok = True
        try:
            res = orig(lat, lon, timeout=timeout)
        except Exception:
            res = None
            ok = False
        _tracer.record('gis.zoning_xcheck', t0, time.perf_counter(), ok)
        return res

    qatar_gis._fetch_zoning_at_point = patched
    return orig


# --- Branch B §3.1 faithful pass: capture the secondary-module raw-urllib ---
# These three modules each roll their OWN urllib (NOT qatar_gis._http_get_json /
# property_factors._query_gis), so the first run dumped them into 'cpu_ms'. They
# only fire on the residential-comparison path (villa/land/compound) that the
# apartment fast-path skips — the structural reason villa cpu >> apt cpu.

def patch_geo_reference_wrapper():
    """Wrap geo_reference_v2's three raw-urllib district/zoning fallbacks. With
    gis_preload loaded (main setup), district radius/centroid take the in-memory
    fast path (~0ms) and only zoning-at-centroid still networks — exactly as in
    production. Tagged georef_* to stay distinct from qatar_gis's gis.districts.
    (build_reference_geo_v2 calls these by module-global name, so rebinding the
    module attrs patches the calls made inside it; the nested centroid inside
    zoning is also patched and, with preload, is ~0ms.)"""
    import geo_reference_v2 as _g

    def _mk(orig, tag):
        def patched(*a, **kw):
            t0 = time.perf_counter()
            ok = True
            try:
                res = orig(*a, **kw)
            except Exception:
                res = None
                ok = False
            _tracer.record(tag, t0, time.perf_counter(), ok)
            return res
        return patched

    _g._query_gis_districts_radius = _mk(_g._query_gis_districts_radius, 'gis.georef_districts')
    _g._query_district_centroid    = _mk(_g._query_district_centroid,    'gis.georef_centroid')
    _g._query_zoning_at_centroid   = _mk(_g._query_zoning_at_centroid,   'gis.georef_zoning')


def patch_geometric_factors_wrapper():
    """Wrap geometric_factors._http_get_json — its OWN raw-urllib helper
    (separate from qatar_gis). Tagged geom.* so the redundancy with
    property_factors (which already fetched roads/landmarks/zoning, captured)
    is visible in the phase table."""
    import geometric_factors as _gf
    orig = _gf._http_get_json

    def patched(url, params):
        full = url + ('?' + urllib.parse.urlencode(params, safe='/:,') if params else '')
        tag = 'geom.' + classify_phase(full).split('.')[-1]
        t0 = time.perf_counter()
        ok = True
        try:
            res = orig(url, params)
            if res is None:
                ok = False
        except Exception:
            res = None
            ok = False
        _tracer.record(tag, t0, time.perf_counter(), ok)
        return res

    _gf._http_get_json = patched


def patch_property_geo_wrapper():
    """Wrap property_geo._fetch — its OWN raw-urllib helper. 0 calls here
    confirms the corner/road-frontage module is not on the villa eval path."""
    import property_geo as _pg
    orig = _pg._fetch

    def patched(url, params, timeout=15):
        full = url + ('?' + urllib.parse.urlencode(params, safe='/:,') if params else '')
        tag = 'pgeo.' + classify_phase(full).split('.')[-1]
        t0 = time.perf_counter()
        ok = True
        try:
            res = orig(url, params, timeout=timeout)
        except Exception:
            res = None
            ok = False
        _tracer.record(tag, t0, time.perf_counter(), ok)
        return res

    _pg._fetch = patched


def patch_imagery_wrapper():
    """Wrap QatarGIS.get_tile (raw-urllib imagery tile fetch for building-age).
    0 calls confirms building-age does NOT hit the network on the eval path.
    Behaviour-preserving (re-raises on error)."""
    import qatar_gis
    orig = qatar_gis.QatarGIS.get_tile

    def patched(self, *a, **kw):
        t0 = time.perf_counter()
        ok = True
        try:
            return orig(self, *a, **kw)
        except Exception:
            ok = False
            raise
        finally:
            _tracer.record('gis.imagery_tile', t0, time.perf_counter(), ok)

    qatar_gis.QatarGIS.get_tile = patched


# ============================================================
# 5. DISCOVERY — Lusail apartment_building
# ============================================================

def discover_lusail_apt():
    """Query QARS_Point for ZONE_NO=69 (Lusail) AND BUILDING_NO_SUBTYPE=6
    (Building with Flats, per CLAUDE.md §8 → apartment_building). Returns
    the first record's (zone, street, building) so we exercise the tower-
    family code path with a known-real address."""
    import qatar_gis
    url = qatar_gis.ENDPOINTS['qars']
    params = {
        'where': 'ZONE_NO=69 AND BUILDING_NO_SUBTYPE=6',
        'outFields': 'ZONE_NO,STREET_NO,BUILDING_NO,PIN',
        'returnGeometry': 'false',
        'resultRecordCount': 5,
        'f': 'json',
    }
    res = qatar_gis._http_get_json(url, params)
    if not res or not res.get('features'):
        return None
    a = res['features'][0]['attributes']
    z, s, b = a.get('ZONE_NO'), a.get('STREET_NO'), a.get('BUILDING_NO')
    if z is None or s is None or b is None:
        return None
    return {'zone': z, 'street': s, 'building': b}


# ============================================================
# 6. RUNNERS
# ============================================================

def _aggregate(events):
    """Aggregate raw events into per-phase summary."""
    agg = {}
    for e in events:
        p = e['phase']
        if p not in agg:
            agg[p] = {'count': 0, 'total_ms': 0.0, 'min_ms': 1e9,
                      'max_ms': 0.0, 'failures': 0}
        agg[p]['count'] += 1
        agg[p]['total_ms'] += e['t_ms']
        agg[p]['min_ms'] = min(agg[p]['min_ms'], e['t_ms'])
        agg[p]['max_ms'] = max(agg[p]['max_ms'], e['t_ms'])
        if not e['ok']:
            agg[p]['failures'] += 1
    for p, v in agg.items():
        v['total_ms'] = round(v['total_ms'], 1)
        v['min_ms']   = round(v['min_ms'], 1) if v['min_ms'] < 1e9 else 0.0
        v['max_ms']   = round(v['max_ms'], 1)
    return agg


def _wallclock_union_ms(intervals):
    """Merge [t0,t1] ms intervals (across all threads) and return the length
    of their union — the real wall-clock footprint of GIS, with overlapping
    (parallel) calls counted once. This is what lets the phase table reconcile
    to ~total instead of a sum that double-counts the parallel fan-outs."""
    iv = sorted((a, b) for a, b in intervals if b >= a)
    if not iv:
        return 0.0
    union = 0.0
    lo, hi = iv[0]
    for a, b in iv[1:]:
        if a <= hi:
            hi = max(hi, b)
        else:
            union += hi - lo
            lo, hi = a, b
    union += hi - lo
    return round(union, 1)


def _analyze(total_ms, events):
    """Timeline reconciliation + per-thread split (Branch B §3.1 core output).

      gis_work_ms       = sum of every GIS call duration (over-counts parallel)
      gis_wallclock_ms  = union of GIS intervals (true timeline footprint)
      gis_overlap_ms    = work - wallclock (latency ALREADY hidden by parallelism)
      compute_ms        = total - wallclock (non-GIS; incl. any untraced network)
      by_thread         = per-thread {count, work_ms, span_ms}; 'MainThread' is
                          the serial critical path, 'factors_*'/'bfs_prefetch_*'
                          are already-parallel (do NOT re-parallelize, §2 T2 caveat)
    """
    work_ms  = round(sum(e['t_ms'] for e in events), 1)
    union_ms = _wallclock_union_ms([(e['t0_ms'], e['t1_ms']) for e in events])
    by_thread = {}
    for e in events:
        d = by_thread.setdefault(e['thread'],
                                 {'count': 0, 'work_ms': 0.0, '_t0': 1e9, '_t1': 0.0})
        d['count']   += 1
        d['work_ms'] += e['t_ms']
        d['_t0'] = min(d['_t0'], e['t0_ms'])
        d['_t1'] = max(d['_t1'], e['t1_ms'])
    for d in by_thread.values():
        d['work_ms'] = round(d['work_ms'], 1)
        d['span_ms'] = round(d['_t1'] - d['_t0'], 1) if d['_t0'] < 1e9 else 0.0
        d.pop('_t0'); d.pop('_t1')
    return {
        'gis_work_ms':      work_ms,
        'gis_wallclock_ms': union_ms,
        'gis_overlap_ms':   round(max(0.0, work_ms - union_ms), 1),
        'compute_ms':       round(max(0.0, total_ms - union_ms), 1),
        'by_thread':        by_thread,
    }


def run_inproc(case):
    """Call evaluate_thammen() directly with patched HTTP wrappers."""
    from evaluate_unified import evaluate_thammen
    _trace_reset()
    t0 = time.perf_counter()
    err = None
    asset_type = None
    payload_keys = None
    try:
        body = dict(case['body'])
        # api.py routes pin → input_mode='land' for the PIN tab; mirror that.
        if 'pin' in body and body['pin']:
            body.setdefault('input_mode', 'land')
        res = evaluate_thammen(**body)
        if isinstance(res, dict):
            asset_type = res.get('asset_type')
            payload_keys = sorted(list(res.keys()))[:30]
        ok = True
    except Exception as e:
        ok = False
        err = f'{type(e).__name__}: {str(e)[:300]}'
    total_ms = (time.perf_counter() - t0) * 1000.0
    events = _trace_events()
    return {
        'ok': ok,
        'err': err,
        'total_ms': round(total_ms, 1),
        'asset_type': asset_type,
        'payload_keys_sample': payload_keys,
        'event_count': len(events),
        'phase_events': events,
        'phase_aggregate': _aggregate(events),
        'timeline': _analyze(total_ms, events),
    }


def run_http(case):
    """POST /api/evaluate via thammen.qa — full user-visible latency."""
    url = f'{THAMMEN_BASE}/api/evaluate'
    body = json.dumps(case['body']).encode('utf-8')
    req = urllib.request.Request(
        url, data=body,
        headers={'Content-Type': 'application/json', 'User-Agent': UA},
        method='POST',
    )
    t0 = time.perf_counter()
    status = None
    err = None
    asset_type = None
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            status = resp.status
            payload = json.loads(resp.read().decode('utf-8'))
            asset_type = payload.get('asset_type')
        ok = True
    except urllib.error.HTTPError as e:
        status = e.code
        ok = False
        err = f'HTTPError {e.code}'
    except Exception as e:
        ok = False
        err = f'{type(e).__name__}: {str(e)[:300]}'
    total_ms = (time.perf_counter() - t0) * 1000.0
    return {
        'ok': ok,
        'err': err,
        'status': status,
        'total_ms': round(total_ms, 1),
        'asset_type': asset_type,
    }


def _print_inproc_summary(inproc):
    """Compact, grep-friendly timeline decomposition (Branch B §3.1). Full
    per-rep detail is in the JSON; this is the at-a-glance reconciliation:
    total = gis_wallclock (overlap-merged) + compute (non-GIS, incl. untraced).
    Then a phase-work table + per-thread split for the villa target."""
    by_case = {}
    for r in inproc:
        by_case.setdefault(r['case_id'], []).append(r)

    print('\n[summary] in-process timeline decomposition (mean over reps)')
    print('-' * 72)
    print(f'  {"case":18s} {"total":>7s} {"giswall":>8s} {"cpu":>7s}'
          f' {"overlap":>8s} {"ev":>4s}')
    for cid, rows in by_case.items():
        use = [r for r in rows if r.get('ok')] or rows
        n = len(use) or 1
        def _m(key):
            return sum((r.get('timeline') or {}).get(key, 0.0) for r in use) / n
        mt = sum(r['total_ms'] for r in use) / n
        print(f'  {cid:18s} {mt:7.0f} {_m("gis_wallclock_ms"):8.0f}'
              f' {_m("compute_ms"):7.0f} {_m("gis_overlap_ms"):8.0f}'
              f' {sum(r["event_count"] for r in use) // n:4d}')

    target = 'multi_qars_56'
    rows = [r for r in inproc if r['case_id'] == target and r.get('ok')]
    if rows:
        print(f'\n  [phase work, {target}] summed across {len(rows)} ok rep(s):')
        agg = {}
        for r in rows:
            for p, v in (r.get('phase_aggregate') or {}).items():
                a = agg.setdefault(p, {'count': 0, 'total_ms': 0.0})
                a['count'] += v['count']
                a['total_ms'] += v['total_ms']
        for p in sorted(agg, key=lambda k: -agg[k]['total_ms']):
            a = agg[p]
            print(f'    {p:26s} n={a["count"]:3d}  work={a["total_ms"]:8.0f} ms')
        tl = (rows[-1].get('timeline') or {}).get('by_thread', {})
        print(f'  [threads, {target} last rep] (MainThread = serial critical path):')
        for th in sorted(tl, key=lambda k: -tl[k]['work_ms']):
            d = tl[th]
            print(f'    {th:18s} n={d["count"]:3d}  work={d["work_ms"]:8.0f} ms'
                  f'  span={d["span_ms"]:8.0f} ms')


# ============================================================
# 7. MAIN
# ============================================================

def main():
    print('=' * 72)
    print('audit_a6_latency.py — Sprint 2.18 Phase 1')
    print(f'  start (UTC):     {datetime.utcnow().isoformat()}Z')
    print(f'  cohort size:     {len(COHORT_BASE)} addresses')
    print(f'  reps:            {REPS} per address')
    print(f'  http delay:      {HTTP_INTERREQ_DELAY_S}s between reps (rate=10/min)')
    print(f'  http timeout:    {HTTP_TIMEOUT_S}s')
    print('=' * 72)

    # 1. Patch HTTP wrappers BEFORE importing evaluate_thammen.
    print('\n[setup] patching HTTP/GIS wrappers (full network capture for Branch B §3.1)...')
    for _name, _fn in [
        ('qatar_gis._http_get_json',         patch_qatar_gis_wrapper),
        ('property_factors._query_gis',      patch_property_factors_wrapper),
        ('qatar_gis._fetch_zoning_at_point', patch_zoning_xcheck_wrapper),
        ('geo_reference_v2 (3 fallbacks)',   patch_geo_reference_wrapper),
        ('geometric_factors._http_get_json', patch_geometric_factors_wrapper),
        ('property_geo._fetch',              patch_property_geo_wrapper),
        ('QatarGIS.get_tile (imagery)',      patch_imagery_wrapper),
    ]:
        try:
            _fn()
            print(f'  patched {_name}')
        except Exception as e:
            print(f'  WARN: patch {_name} failed: {type(e).__name__}: {e}')

    # Branch B §3.1 faithful pass: load gis_preload so in-process district
    # lookups are memory-served exactly as on the web dyno (api.py boot). Removes
    # the in-process-only district fallback artifact; only genuinely-networked
    # calls remain, so cpu_ms reflects TRUE production compute.
    print('\n[setup] loading gis_preload (mirror production web-dyno boot)...')
    try:
        import gis_preload
        _n = len(gis_preload.load_districts())
        print(f'  gis_preload: {_n} districts in-memory (is_loaded={gis_preload.is_loaded()})')
    except Exception as e:
        print(f'  WARN: gis_preload load failed ({type(e).__name__}: {e}) — district artifact remains')

    # 2. Discover Lusail apartment_building dynamically (skip slot if not found).
    print('\n[discover] Lusail apartment_building (ZONE=69, SUBTYPE=6)...')
    try:
        lusail = discover_lusail_apt()
        if lusail is None:
            print('  no record found (will skip lusail_apt slot)')
        else:
            print(f'  found: {lusail["zone"]}/{lusail["street"]}/{lusail["building"]}')
    except Exception as e:
        lusail = None
        print(f'  FAIL: {type(e).__name__}: {e}')

    # 3. Build final cohort (drop discovered slot if discovery failed).
    cohort = []
    for c in COHORT_BASE:
        if c.get('discover') == 'lusail_apt':
            if lusail is None:
                print(f'  skipping {c["id"]} (no discovery result)')
                continue
            c = dict(c)
            c['body'] = lusail
            c.pop('discover', None)
        cohort.append(c)

    results = {
        'meta': {
            'sprint': 'Branch B §3.1 faithful pass (full network capture + gis_preload) — A14 real-fix',
            'engine_version_assumption': 'thammen-sprint2p22p0a5-villa-cold503-budget (v143 slug, v142 behaviour)',
            'start_utc': datetime.utcnow().isoformat() + 'Z',
            'cohort_size': len(cohort),
            'reps_per_address': REPS,
            'http_interreq_delay_s': HTTP_INTERREQ_DELAY_S,
            'http_timeout_s': HTTP_TIMEOUT_S,
            'cohort': [{'id': c['id'], 'label': c['label'], 'mode': c['mode'],
                        'body': c['body']} for c in cohort],
        },
        'in_process': [],
        'http': [],
    }

    # 4. In-process runs (sequential, no rate-limit concern).
    print('\n[in-process] evaluate_thammen() with patched HTTP wrappers')
    print('-' * 72)
    for case in cohort:
        for rep in range(1, REPS + 1):
            tag = f'{case["id"]:18s} rep#{rep}'
            print(f'  {tag} ...', end='', flush=True)
            r = run_inproc(case)
            r['case_id'] = case['id']
            r['rep'] = rep
            r['label'] = case['label']
            results['in_process'].append(r)
            tl = r.get('timeline') or {}
            status = (f' {r["total_ms"]:7.0f} ms  '
                      f'wall={tl.get("gis_wallclock_ms", 0):6.0f}  '
                      f'cpu={tl.get("compute_ms", 0):6.0f}  '
                      f'asset={str(r["asset_type"]):<18s} '
                      f'ev={r["event_count"]:3d}')
            if not r['ok']:
                status += f'  ERR={r["err"]}'
            print(status)
            time.sleep(INPROC_INTERREQ_DELAY_S)

    _print_inproc_summary(results['in_process'])

    # 5. HTTP runs (rate-limited).
    print('\n[http] POST https://thammen.qa/api/evaluate (7s spacing)')
    print('-' * 72)
    for case in cohort:
        for rep in range(1, REPS + 1):
            tag = f'{case["id"]:18s} rep#{rep}'
            print(f'  {tag} ...', end='', flush=True)
            r = run_http(case)
            r['case_id'] = case['id']
            r['rep'] = rep
            r['label'] = case['label']
            results['http'].append(r)
            status = f' HTTP {r["status"]}  {r["total_ms"]:7.0f} ms'
            if r['err']:
                status += f'  err={r["err"]}'
            print(status)
            time.sleep(HTTP_INTERREQ_DELAY_S)

    results['meta']['end_utc'] = datetime.utcnow().isoformat() + 'Z'

    # 6. Persist to /tmp (dyno-ephemeral but useful if heroku run output truncates)
    out_path = '/tmp/audit_a6_results.json'
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f'\n[done] wrote {out_path}')
    except Exception as e:
        print(f'\n[done] could not write {out_path}: {e}')

    # 7. Emit full JSON on stdout between markers (heroku run captures this).
    print('\n===== BEGIN JSON =====')
    print(json.dumps(results, ensure_ascii=False))
    print('===== END JSON =====')

    return 0


if __name__ == '__main__':
    sys.exit(main())
