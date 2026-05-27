"""
test_sprint_2p22p0a1_qars_envelope_fallback.py — Sprint 2.22.0a.1 tests.

Goal: prove the ArcGIS-error-envelope detection + primary→legacy fallback
restores production address lookups after khazna's QARS_Point service
became inaccessible (HTTP 200 + `{"error": {"code":503, "message":
"User couldn't access this resource 'qars/qars_point.mapserver'"}}`).

Test plan:
  1. _arcgis_envelope_to_exception
     1a. raises _GISServerError on the real khazna envelope
     1b. no-op on a healthy ArcGIS response (features list)
     1c. no-op on count-only response
     1d. no-op on non-dict input (defensive)
     1e. error message carries code + source URL for debuggability
  2. _qars_query primary-first / legacy-fallback
     2a. returns primary response when primary healthy
     2b. falls back to legacy on primary envelope error
     2c. falls back to legacy on primary Python exception
     2d. raises when BOTH primary AND legacy fail (with envelope)
     2e. raises when BOTH primary AND legacy fail (with exception)
     2f. logger is invoked exactly once when fallback fires
     2g. logger=None is accepted silently
  3. _qars_query integration with the production GISClient.find_property
     3a. find_property returns a PropertyLocation when legacy succeeds
     3b. find_property returns None when both endpoints fail
     3c. find_property returns None on legitimate "address not found"
         (legacy succeeded but returned features=[])
  4. _qars_count_in_polygon falls back on envelope error
  5. count_qars_within_polygon falls back on envelope error
  6. Engine version + sprint tag bumped correctly

Standalone runner per CLAUDE.md convention (no pytest dependency).
Run: python test_sprint_2p22p0a1_qars_envelope_fallback.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _test_helpers import Reporter, set_stdout_utf8

set_stdout_utf8()

import qatar_gis
from qatar_gis import (
    _GISServerError,
    _arcgis_envelope_to_exception,
    _qars_query,
    ENDPOINTS,
)

_REPORTER = Reporter()
_check = _REPORTER.check


# Real envelope captured by Phase 0 probe smoke_qars_heroku.py on 2026-05-27:
KHAZNA_ENVELOPE = {
    "error": {
        "code": 503,
        "message": "User couldn't access this resource 'qars/qars_point.mapserver'.",
        "details": [],
    }
}

HEALTHY_FEATURE_RESPONSE = {
    "features": [
        {
            "attributes": {
                "ZONE_NO": 52, "STREET_NO": 903, "BUILDING_NO": 90,
                "PIN": 52090177, "QARS": "52/903/90",
                "BUILDING_NO_SUBTYPE": 1,
                "PLOT_NO_OLD": None,
                "ELECTRICITY_NO": None, "WATER_NO": None, "QTEL_ID": None,
            },
            "geometry": {"x": 51.530, "y": 25.330},
        }
    ]
}

HEALTHY_COUNT_RESPONSE = {"count": 1}

ADDRESS_NOT_FOUND_RESPONSE = {"features": []}


# ─────────────────────────────────────────────────────────────────────
# 1. _arcgis_envelope_to_exception
# ─────────────────────────────────────────────────────────────────────
print("\n[1] _arcgis_envelope_to_exception")

# 1a. raises on real khazna envelope
try:
    _arcgis_envelope_to_exception(KHAZNA_ENVELOPE)
    _check(False, "1a envelope raises", "expected _GISServerError, none raised")
except _GISServerError as e:
    _check('503' in str(e), "1a envelope raises with code in msg", f'got: {e}')
except Exception as e:
    _check(False, "1a envelope raises", f'wrong type: {type(e).__name__}: {e}')

# 1b. no-op on healthy feature response
try:
    _arcgis_envelope_to_exception(HEALTHY_FEATURE_RESPONSE)
    _check(True, "1b healthy features no-op", "")
except Exception as e:
    _check(False, "1b healthy features no-op", f'unexpected raise: {e}')

# 1c. no-op on count-only response
try:
    _arcgis_envelope_to_exception(HEALTHY_COUNT_RESPONSE)
    _check(True, "1c count-only no-op", "")
except Exception as e:
    _check(False, "1c count-only no-op", f'unexpected raise: {e}')

# 1d. defensive on non-dict input
for bad in [None, [], "", 42, "not a dict"]:
    try:
        _arcgis_envelope_to_exception(bad)
        _check(True, f"1d non-dict no-op ({type(bad).__name__})", "")
    except Exception as e:
        _check(False, f"1d non-dict no-op ({type(bad).__name__})", f'raised: {e}')

# 1e. error message carries source URL
try:
    _arcgis_envelope_to_exception(KHAZNA_ENVELOPE, 'https://khazna.example/q')
    _check(False, "1e source url in msg", "expected raise")
except _GISServerError as e:
    msg = str(e)
    _check('khazna.example' in msg, "1e source url in msg", f'msg={msg}')


# ─────────────────────────────────────────────────────────────────────
# 2. _qars_query primary-first / legacy-fallback
# ─────────────────────────────────────────────────────────────────────
print("\n[2] _qars_query primary-first / legacy-fallback")


class _CallRecorder:
    """Capture all _http_get_json calls and serve a scripted response."""
    def __init__(self, script):
        # script: list of (url_substring, response_or_exception) tuples
        # consumed in order; matched by substring presence in url.
        self.script = list(script)
        self.calls = []  # list of urls in call order

    def __call__(self, url, params=None, timeout=30):
        self.calls.append(url)
        # Find first matching scripted response
        for i, (url_match, response) in enumerate(self.script):
            if url_match in url:
                self.script.pop(i)
                if isinstance(response, Exception):
                    raise response
                return response
        raise AssertionError(
            f'No scripted response for {url}; remaining: {self.script}'
        )


def _with_mock(mock):
    """Context manager-ish: swap _http_get_json for `mock` and restore."""
    saved = qatar_gis._http_get_json
    qatar_gis._http_get_json = mock
    return saved


def _restore(saved):
    qatar_gis._http_get_json = saved


# 2a. primary healthy → returns primary response, no legacy call
mock = _CallRecorder([('khazna', HEALTHY_FEATURE_RESPONSE)])
saved = _with_mock(mock)
try:
    res = _qars_query({'where': 'ZONE_NO=52'})
    _check(res is HEALTHY_FEATURE_RESPONSE,
           "2a primary healthy returns primary", "")
    _check(len(mock.calls) == 1, "2a no fallback call", f'calls={mock.calls}')
    _check('khazna' in mock.calls[0],
           "2a primary url hit", f'url={mock.calls[0]}')
finally:
    _restore(saved)

# 2b. primary envelope → legacy returns healthy
mock = _CallRecorder([
    ('khazna', KHAZNA_ENVELOPE),
    ('services.gisqatar.org.qa', HEALTHY_FEATURE_RESPONSE),
])
saved = _with_mock(mock)
try:
    res = _qars_query({'where': 'ZONE_NO=52'})
    _check(res is HEALTHY_FEATURE_RESPONSE,
           "2b envelope falls back to legacy", "")
    _check(len(mock.calls) == 2, "2b two calls (primary+legacy)",
           f'calls={mock.calls}')
    _check('khazna' in mock.calls[0] and 'services.gisqatar.org.qa' in mock.calls[1],
           "2b call order primary then legacy",
           f'calls={mock.calls}')
finally:
    _restore(saved)

# 2c. primary network exception → legacy returns healthy
import socket
mock = _CallRecorder([
    ('khazna', socket.timeout('simulated timeout')),
    ('services.gisqatar.org.qa', HEALTHY_FEATURE_RESPONSE),
])
saved = _with_mock(mock)
try:
    res = _qars_query({'where': 'ZONE_NO=52'})
    _check(res is HEALTHY_FEATURE_RESPONSE,
           "2c network exception falls back to legacy", "")
    _check(len(mock.calls) == 2, "2c two calls", f'calls={mock.calls}')
finally:
    _restore(saved)

# 2d. both fail with envelopes → raise
LEGACY_ENVELOPE = {"error": {"code": 401, "message": "legacy unauthorized"}}
mock = _CallRecorder([
    ('khazna', KHAZNA_ENVELOPE),
    ('services.gisqatar.org.qa', LEGACY_ENVELOPE),
])
saved = _with_mock(mock)
try:
    raised = None
    try:
        _qars_query({'where': 'ZONE_NO=52'})
    except _GISServerError as e:
        raised = e
    _check(raised is not None, "2d both envelopes raise", "")
    _check('401' in str(raised) or 'legacy' in str(raised),
           "2d raises with legacy error info", f'msg={raised}')
finally:
    _restore(saved)

# 2e. both fail with exceptions → raise the legacy exception
mock = _CallRecorder([
    ('khazna', socket.timeout('primary timeout')),
    ('services.gisqatar.org.qa', socket.timeout('legacy timeout')),
])
saved = _with_mock(mock)
try:
    raised = None
    try:
        _qars_query({'where': 'ZONE_NO=52'})
    except Exception as e:
        raised = e
    _check(raised is not None, "2e both exceptions raise", "")
    _check('legacy' in str(raised),
           "2e raises legacy exception (not primary)",
           f'msg={raised}')
finally:
    _restore(saved)

# 2f. logger invoked once when fallback fires
log_messages = []
mock = _CallRecorder([
    ('khazna', KHAZNA_ENVELOPE),
    ('services.gisqatar.org.qa', HEALTHY_FEATURE_RESPONSE),
])
saved = _with_mock(mock)
try:
    _qars_query({'where': 'ZONE_NO=52'}, logger=log_messages.append)
    _check(len(log_messages) == 1, "2f logger called exactly once",
           f'msgs={log_messages}')
    _check('primary failed' in log_messages[0] if log_messages else False,
           "2f logger message describes primary failure",
           f'msg={log_messages}')
finally:
    _restore(saved)

# 2g. logger=None accepted
mock = _CallRecorder([
    ('khazna', KHAZNA_ENVELOPE),
    ('services.gisqatar.org.qa', HEALTHY_FEATURE_RESPONSE),
])
saved = _with_mock(mock)
try:
    res = _qars_query({'where': 'ZONE_NO=52'}, logger=None)
    _check(res is HEALTHY_FEATURE_RESPONSE, "2g logger=None OK", "")
finally:
    _restore(saved)


# ─────────────────────────────────────────────────────────────────────
# 3. find_property integration
# ─────────────────────────────────────────────────────────────────────
print("\n[3] find_property integration with _qars_query")

from qatar_gis import QatarGIS

# 3a. envelope on primary → legacy success → PropertyLocation returned
mock = _CallRecorder([
    ('khazna', KHAZNA_ENVELOPE),
    ('services.gisqatar.org.qa', HEALTHY_FEATURE_RESPONSE),
])
saved = _with_mock(mock)
try:
    client = QatarGIS()
    loc = client.find_property(52, 903, 90)
    _check(loc is not None, "3a fallback yields PropertyLocation",
           f'got={loc}')
    if loc is not None:
        _check(loc.zone == 52, "3a zone preserved", f'zone={loc.zone}')
        _check(loc.qars == '52/903/90', "3a qars preserved", f'qars={loc.qars}')
        _check(loc.building_subtype == 1, "3a subtype preserved",
               f'subtype={loc.building_subtype}')
finally:
    _restore(saved)

# 3b. both fail → None (not raise; existing contract)
mock = _CallRecorder([
    ('khazna', KHAZNA_ENVELOPE),
    ('services.gisqatar.org.qa', socket.timeout('legacy down')),
])
saved = _with_mock(mock)
try:
    client = QatarGIS()
    loc = client.find_property(99, 99, 99)
    _check(loc is None, "3b both fail returns None", f'got={loc}')
finally:
    _restore(saved)

# 3c. legitimate "not found" → None, no second call to legacy
mock = _CallRecorder([
    ('khazna', ADDRESS_NOT_FOUND_RESPONSE),
])
saved = _with_mock(mock)
try:
    client = QatarGIS()
    loc = client.find_property(99, 99, 99)
    _check(loc is None, "3c not-found returns None", f'got={loc}')
    _check(len(mock.calls) == 1, "3c no fallback on empty features",
           f'calls={mock.calls}')
finally:
    _restore(saved)


# ─────────────────────────────────────────────────────────────────────
# 4. _qars_count_in_polygon falls back on envelope
# ─────────────────────────────────────────────────────────────────────
print("\n[4] _qars_count_in_polygon")

from qatar_gis import _qars_count_in_polygon

mock = _CallRecorder([
    ('khazna', KHAZNA_ENVELOPE),
    ('services.gisqatar.org.qa', {"count": 3}),
])
saved = _with_mock(mock)
try:
    ring = [[51.530, 25.330], [51.535, 25.330], [51.535, 25.335],
            [51.530, 25.335], [51.530, 25.330]]
    count = _qars_count_in_polygon(ring, timeout=10)
    _check(count == 3, "4 envelope fallback yields legacy count",
           f'got={count}')
finally:
    _restore(saved)


# ─────────────────────────────────────────────────────────────────────
# 5. count_qars_within_polygon falls back on envelope
# ─────────────────────────────────────────────────────────────────────
print("\n[5] count_qars_within_polygon")

from qatar_gis import count_qars_within_polygon

LEGACY_POLY_RESPONSE = {
    "features": [
        {
            "attributes": {
                "BUILDING_NO": 90, "ZONE_NO": 52, "STREET_NO": 903,
                "PIN": 52090177, "BUILDING_NO_SUBTYPE": 1,
            },
            "geometry": {"x": 51.530, "y": 25.330},
        }
    ]
}

mock = _CallRecorder([
    ('khazna', KHAZNA_ENVELOPE),
    ('services.gisqatar.org.qa', LEGACY_POLY_RESPONSE),
])
saved = _with_mock(mock)
try:
    polygon = {'rings': [[[51.530, 25.330], [51.535, 25.330],
                          [51.535, 25.335], [51.530, 25.335],
                          [51.530, 25.330]]]}
    feats = count_qars_within_polygon(polygon, timeout=10)
    _check(isinstance(feats, list), "5 returns list", f'type={type(feats)}')
    _check(len(feats) == 1, "5 single feature from legacy", f'feats={feats}')
    if feats:
        _check(feats[0]['subtype'] == 1, "5 BUILDING_NO_SUBTYPE preserved",
               f'feat={feats[0]}')
finally:
    _restore(saved)


# ─────────────────────────────────────────────────────────────────────
# 6. Engine version + sprint tag
# ─────────────────────────────────────────────────────────────────────
print("\n[6] Engine version + sprint tag")

from evaluate_unified import ENGINE_VERSION, SPRINT_TAG

_check(ENGINE_VERSION == 'thammen-sprint2p22p0a1-qars-envelope-fallback',
       "6 ENGINE_VERSION bumped", f'got={ENGINE_VERSION}')
_check(SPRINT_TAG == '2.22.0a.1',
       "6 SPRINT_TAG bumped", f'got={SPRINT_TAG}')


sys.exit(_REPORTER.report())
