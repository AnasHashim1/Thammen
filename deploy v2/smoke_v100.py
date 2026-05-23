"""Sprint 2.18.1 post-deploy smoke test — 3 cases, 1 rep each.
Run locally (Windows) against production. Adds UA header to bypass Cloudflare 1010."""
import json
import time
import urllib.error
import urllib.request


URL = 'https://thammen.qa/api/evaluate'
UA = 'Mozilla/5.0 (Thammen-Smoke-2.18.1) ans_hashim@hotmail.com'

CASES = [
    ('safe_villa_52  ', {'zone': 52, 'street': 903, 'building': 90}, '~4s expected'),
    ('multi_qars_56  ', {'zone': 56, 'street': 565, 'building': 21}, '~23s expected (was 503x1+200x2)'),
    ('a6_trigger_51  ', {'zone': 51, 'street': 835, 'building': 17}, '~25s predicted (was 503x3 — THE WIN)'),
]

for label, body, note in CASES:
    t0 = time.time()
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(
        URL, data=data,
        headers={'Content-Type': 'application/json', 'User-Agent': UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            ms = (time.time() - t0) * 1000
            d = json.loads(resp.read())
            ev = d.get('engine_version', '?')
            at = d.get('asset_type', '?')
            print(f'{label}  HTTP {resp.status:3}  {ms:7.0f}ms  asset={at:20}  engine={ev}')
    except urllib.error.HTTPError as e:
        ms = (time.time() - t0) * 1000
        body_excerpt = e.read()[:150].decode('utf-8', errors='replace')
        print(f'{label}  HTTP {e.code:3}  {ms:7.0f}ms  ERR body={body_excerpt}')
    except Exception as e:
        ms = (time.time() - t0) * 1000
        print(f'{label}  ----- {ms:7.0f}ms  {type(e).__name__}: {e}')
    print(f'                                                                 ({note})')
    time.sleep(7)  # respect 10/min rate limit
