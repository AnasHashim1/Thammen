"""Phase 0 probe — direct khazna QARS reachability from inside Heroku dyno.

Anchor PIN: 52/903/90 (Sprint 2.16.15 timing baseline; NOT 51/835/17 per Bug A6).
"""
import urllib.request, time

URL = ('https://khazna.gisqatar.org.qa/fed/rest/services/QARS/'
       'QARS_Point/FeatureServer/0/query?'
       'where=ZONE_NO%3D52+AND+STREET_NO%3D903+AND+BUILDING_NO%3D90'
       '&outFields=*&f=json')

t0 = time.time()
try:
    r = urllib.request.urlopen(URL, timeout=15)
    body = r.read()
    print('status:', r.status, 'elapsed:', round(time.time() - t0, 2),
          'len:', len(body), 'sample:', body[:200])
except Exception as e:
    print('ERROR', type(e).__name__, str(e),
          'elapsed:', round(time.time() - t0, 2))
