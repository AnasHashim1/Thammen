"""
audit_a6_latency.py — Sprint 2.18 Phase 1 (A6 Latency Investigation)
====================================================================

Profile end-to-end /api/evaluate latency with a per-phase breakdown so we can
identify what to fix in Phase 2. **No engine code change.** This is a
measurement instrument.

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
# 3. THREAD-LOCAL TRACE BUFFER
# ============================================================

_trace = threading.local()

def _trace_reset():
    _trace.events = []

def _trace_record(phase: str, dt_ms: float, ok: bool):
    if not getattr(_trace, 'events', None):
        _trace.events = []
    _trace.events.append({'phase': phase, 't_ms': round(dt_ms, 1), 'ok': ok})

def _trace_events():
    return list(getattr(_trace, 'events', None) or [])


# ============================================================
# 4. MONKEY-PATCH HTTP WRAPPERS
# ============================================================

def patch_qatar_gis_wrapper():
    """Wrap qatar_gis._http_get_json so each call is timed + phase-tagged."""
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
        dt_ms = (time.perf_counter() - t0) * 1000.0
        _trace_record(phase, dt_ms, ok)
        return res

    qatar_gis._http_get_json = patched
    return orig


def patch_property_factors_wrapper():
    """Wrap property_factors._query_gis (separate HTTP path: landmarks,
    zoning, roads, commercial-streets)."""
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
        dt_ms = (time.perf_counter() - t0) * 1000.0
        _trace_record(phase, dt_ms, ok)
        return res

    property_factors._query_gis = patched
    return orig


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
    print('\n[setup] patching HTTP wrappers (qatar_gis + property_factors)...')
    try:
        patch_qatar_gis_wrapper()
        patch_property_factors_wrapper()
        print('  ok')
    except Exception as e:
        print(f'  FAIL: {type(e).__name__}: {e}')
        return 1

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
            'sprint': '2.18 Phase 1',
            'engine_version_assumption': 'thammen-sprint2p21p0p9-multi-qars-stage1',
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
            status = (f' {r["total_ms"]:7.0f} ms  asset={r["asset_type"]:<22s}'
                      f' events={r["event_count"]:3d}')
            if not r['ok']:
                status += f'  ERR={r["err"]}'
            print(status)
            time.sleep(INPROC_INTERREQ_DELAY_S)

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
