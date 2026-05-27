"""Phase 0 probe — legacy QARS endpoint subtype field check.

Verify whether BUILDING_NO_SUBTYPE is absent on services.gisqatar.org.qa
or just under a different field name. Same anchor PIN as smoke_qars_heroku.py.
Do not trust prior 2.22.0a Gate 3 claims — verify directly (Rule #45).
"""
import urllib.request, time, json

URL = ('https://services.gisqatar.org.qa/server/rest/services/'
       'Vector/QARS_Search/MapServer/0/query?'
       'where=ZONE_NO%3D52+AND+STREET_NO%3D903+AND+BUILDING_NO%3D90'
       '&outFields=*&f=json')

t0 = time.time()
try:
    r = urllib.request.urlopen(URL, timeout=15)
    body = r.read()
    elapsed = round(time.time() - t0, 2)
    print('status:', r.status, 'elapsed:', elapsed, 'len:', len(body))
    try:
        data = json.loads(body)
        feats = data.get('features', [])
        print('feature_count:', len(feats))
        if feats:
            attrs = feats[0].get('attributes', {})
            print('field_names:', sorted(attrs.keys()))
            subtype_keys = [k for k in attrs.keys() if 'SUBTYPE' in k.upper()]
            print('subtype_like_keys:', subtype_keys)
            for k in subtype_keys:
                print(f'  {k} =', attrs[k])
        else:
            fields_meta = data.get('fields', [])
            print('fields_metadata_names:', [f.get('name') for f in fields_meta])
    except Exception as parse_err:
        print('PARSE_ERROR', type(parse_err).__name__, str(parse_err))
        print('raw_sample:', body[:400])
except Exception as e:
    print('ERROR', type(e).__name__, str(e),
          'elapsed:', round(time.time() - t0, 2))
