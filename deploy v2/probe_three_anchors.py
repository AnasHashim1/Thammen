"""Probe — confirm legacy QARS has features for the three smoke anchors.

Goal: distinguish "fix broken" vs "address legitimately not in legacy DB".
"""
import urllib.request, urllib.parse, json, time

BASE = ('https://services.gisqatar.org.qa/server/rest/services/'
        'Vector/QARS_Search/MapServer/0/query')

for (z, s, b) in [(52, 903, 90), (70, 300, 25), (53, 240, 12)]:
    where = f'ZONE_NO={z} AND STREET_NO={s} AND BUILDING_NO={b}'
    url = BASE + '?' + urllib.parse.urlencode({
        'where': where, 'outFields': '*', 'f': 'json',
    })
    t0 = time.time()
    try:
        r = urllib.request.urlopen(url, timeout=10)
        body = r.read()
        elapsed = round(time.time() - t0, 2)
        data = json.loads(body)
        feats = data.get('features', [])
        print(f'{z}/{s}/{b}: status=200 elapsed={elapsed}s n_features={len(feats)}')
        if feats:
            a = feats[0].get('attributes', {})
            print(f'  PIN={a.get("PIN")} QARS={a.get("QARS")} subtype={a.get("BUILDING_NO_SUBTYPE")}')
        else:
            err = data.get('error')
            if err:
                print(f'  envelope error: {err}')
    except Exception as e:
        print(f'{z}/{s}/{b}: ERROR {type(e).__name__}: {e}')
