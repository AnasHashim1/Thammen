"""
Sprint 2.21.0.9 — Phase 4 post-deploy smoke test.

Run from Heroku slug:
  heroku run --app thammen-app-123 python smoke_sprint2p21p0p9.py

Verifies:
  /api/health      -> new engine_version + sprint_tag
  56/565/21        -> multi_qars.detected=true, type=attached, effective=450
                      (the trigger case — Bou Hamour duplex)
  PIN 66030258     -> multi_qars block ABSENT (compound_large fallthrough)
                      AND asset_type is compound_large in production
  52/903/90        -> multi_qars block ABSENT (standalone, n=1)
                      AND engine_version stamped on the response

File-based per Rule #34 — avoids Windows-cmd quoting hell with `heroku run -c`.
"""
import json
import urllib.request

BASE = 'https://thammen.qa'


def hit(path, body=None):
    if body is None:
        req = urllib.request.Request(BASE + path)
    else:
        req = urllib.request.Request(
            BASE + path,
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))


def main():
    print('=' * 60)
    print('Sprint 2.21.0.9 — Phase 4 smoke')
    print('=' * 60)

    # ---- /api/health
    print('\n[1] GET /api/health')
    try:
        st, d = hit('/api/health')
        print(f'    status={st}')
        print(f'    engine_version = {d.get("engine_version")}')
        print(f'    version        = {d.get("version")}')
        ok = (d.get('engine_version') or '').startswith('thammen-sprint2p21p0p9')
        print(f'    PASS' if ok else f'    FAIL — expected sprint2p21p0p9')
    except Exception as e:
        print(f'    FAIL — {type(e).__name__}: {e}')

    # ---- 56/565/21 — the trigger case
    print('\n[2] POST /api/evaluate {zone:56,street:565,building:21}')
    try:
        st, d = hit('/api/evaluate',
                    {'zone': 56, 'street': 565, 'building': 21})
        mq = d.get('multi_qars')
        print(f'    status={st}  engine={d.get("engine_version", "?")}')
        if mq:
            print(f'    multi_qars.detected = {mq.get("detected")}')
            print(f'    multi_qars.type     = {mq.get("type")}')
            print(f'    cadastral_area      = {mq.get("cadastral_area")}')
            print(f'    effective_per_villa = {mq.get("effective_per_villa")}')
            print(f'    n_qars              = {mq.get("n_qars")}')
            print(f'    max_gps_distance_m  = {mq.get("max_gps_distance_m")}')
            print(f'    cohabiting_buildings = {mq.get("cohabiting_buildings")}')
            print(f'    alternative_valuation = {mq.get("alternative_valuation")}')
            attached = mq.get('type') == 'attached'
            split_ok = mq.get('effective_per_villa') in (450, 450.0)
            print(f'    {"PASS" if attached and split_ok else "FAIL"} — '
                  f'expected attached + effective=450')
        else:
            print('    FAIL — multi_qars block ABSENT (detection did not fire)')
    except Exception as e:
        print(f'    FAIL — {type(e).__name__}: {e}')

    # ---- PIN 66030258 — compound_large regression
    print('\n[3] POST /api/evaluate {pin:"66030258"}')
    try:
        st, d = hit('/api/evaluate', {'pin': '66030258'})
        at = d.get('asset_type')
        mq = d.get('multi_qars')
        print(f'    status={st}  asset_type={at}')
        print(f'    multi_qars block present: {mq is not None}')
        if mq:
            print(f'    multi_qars.detected = {mq.get("detected")}')
            print(f'    multi_qars.type     = {mq.get("type")}')
        # multi_qars block should be absent OR detected=False for compound_large
        compound = at == 'compound_large'
        mq_safe = (mq is None) or (not mq.get('detected'))
        print(f'    {"PASS" if compound and mq_safe else "FAIL"} — '
              f'expected compound_large + no multi_qars panel')
    except Exception as e:
        print(f'    FAIL — {type(e).__name__}: {e}')

    # ---- 52/903/90 — standalone negative + timing baseline
    print('\n[4] POST /api/evaluate {zone:52,street:903,building:90}')
    try:
        st, d = hit('/api/evaluate',
                    {'zone': 52, 'street': 903, 'building': 90})
        mq = d.get('multi_qars')
        print(f'    status={st}  engine={d.get("engine_version", "?")}')
        print(f'    asset_type        = {d.get("asset_type")}')
        print(f'    multi_qars block  = {"absent" if mq is None else mq.get("type")}')
        eng_ok = (d.get('engine_version') or '').startswith('thammen-sprint2p21p0p9')
        # For standalone (n=1), multi_qars should be absent OR detected=False
        mq_safe = (mq is None) or (not mq.get('detected'))
        print(f'    {"PASS" if eng_ok and mq_safe else "FAIL"} — '
              f'expected sprint2p21p0p9 stamped + no multi_qars panel')
    except Exception as e:
        print(f'    FAIL — {type(e).__name__}: {e}')

    print('\nDONE.')


if __name__ == '__main__':
    main()
