"""Probe — does legacy QARS_Search/MapServer/0 support polygon spatial queries?

The Sprint 2.21.0.7 reality check sends rings as geometry to ENDPOINTS['qars']
with no fallback. If legacy supports the same query shape, we can extend the
fallback transparently. Otherwise, the polygon-spatial code path needs a
different approach.
"""
import urllib.request, urllib.parse, time, json

# Small rectangular ring around a known built plot (52/903/90 vicinity).
# Coordinates from a working MapServer query earlier:
# COORD_X / COORD_Y on legacy come back as Qatar National Grid (EPSG:2932)
# so for a polygon test we use a small WGS84 ring around 25.346, 51.454
# (a roughly-arbitrary Doha-area sample to exercise the spatial pipe).
ring = [
    [51.530, 25.330],
    [51.535, 25.330],
    [51.535, 25.335],
    [51.530, 25.335],
    [51.530, 25.330],
]
geom = json.dumps({'rings': [ring], 'spatialReference': {'wkid': 4326}})
params = {
    'geometry': geom,
    'geometryType': 'esriGeometryPolygon',
    'inSR': '4326',
    'spatialRel': 'esriSpatialRelIntersects',
    'returnCountOnly': 'true',
    'f': 'json',
}
url = ('https://services.gisqatar.org.qa/server/rest/services/'
       'Vector/QARS_Search/MapServer/0/query?' + urllib.parse.urlencode(params))

t0 = time.time()
try:
    r = urllib.request.urlopen(url, timeout=15)
    body = r.read()
    elapsed = round(time.time() - t0, 2)
    print('status:', r.status, 'elapsed:', elapsed, 'len:', len(body))
    print('body:', body[:500])
except Exception as e:
    print('ERROR', type(e).__name__, str(e))
