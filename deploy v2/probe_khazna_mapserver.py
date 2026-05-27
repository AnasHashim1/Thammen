"""Probe — try the khazna MapServer slug referenced in the error message.

The Phase 0 Step 2 error said 'qars/qars_point.mapserver'. Maybe khazna
republished the service as MapServer instead of FeatureServer. If this
works, the fix is a 2-line URL constant swap.
"""
import urllib.request, time, json

URLS = [
    ('khazna MapServer/0 (with featureserver in path)',
     'https://khazna.gisqatar.org.qa/fed/rest/services/QARS/QARS_Point/MapServer/0/query'),
    ('khazna /QARS service listing',
     'https://khazna.gisqatar.org.qa/fed/rest/services/QARS?f=json'),
    ('khazna /QARS/QARS_Point service metadata',
     'https://khazna.gisqatar.org.qa/fed/rest/services/QARS/QARS_Point?f=json'),
]
QS = ('?where=ZONE_NO%3D52+AND+STREET_NO%3D903+AND+BUILDING_NO%3D90'
      '&outFields=*&f=json')

for label, base in URLS:
    url = base + (QS if '?' not in base else '')
    if '?' in base and 'where' not in base:
        url = base
    t0 = time.time()
    try:
        r = urllib.request.urlopen(url, timeout=10)
        body = r.read()
        elapsed = round(time.time() - t0, 2)
        print('---', label, '---')
        print('url:', url[:120])
        print('status:', r.status, 'elapsed:', elapsed, 'len:', len(body))
        print('sample:', body[:300])
        print()
    except Exception as e:
        print('---', label, '--- ERROR:', type(e).__name__, str(e)[:200])
        print()
