# -*- coding: utf-8 -*-
"""sweep_surface.py — READ-ONLY full input-surface sweep of ONE property on the REAL
local engine (Phase-0 kit, 2026-06-11). Fetches the GIS context ONCE (a thread-safe
memo-cache on urllib.request.urlopen — record-once/replay), then sweeps the user-input
matrix and writes one CSV row per case. ZERO engine edits; the patch lives in this
harness only.

Default subject: امريخ 54/541/6. Matrix (pruned to the REACHABLE input surface):
  age      : None, 10, 15, 20, 25, 30, 40, 50          (building_age_years → age_source='user')
  finish   : default(ordinary) / is_luxury=True         (the 5-tier RCN ladder is INTERNAL —
                                                         shell/good/high are NOT user inputs; #39)
  condition: None, new, excellent, renovated, good, average, fair, poor, teardown
             ('new' added beyond the brief list — completes the b4 luxury-new lever; #39)
  rent     : None, 10000, 15000, 25000 (monthly)
  footprint: default / 200 / 450 m² (sub-grid) + basement on/off (sub-sample)

Usage: PYTHONIOENCODING=utf-8 python sweep_surface.py  → .marikh_surface_sweep.csv
"""
import csv
import io
import json
import sys
import threading
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

# ── the record-once / replay-forever HTTP cache (thread-safe; fetch context ONCE) ──
_ORIG_URLOPEN = urllib.request.urlopen
_HTTP_CACHE = {}
_LOCK = threading.Lock()
_STATS = {'miss': 0, 'hit': 0}


class _CachedResp(io.BytesIO):
    def __init__(self, body, code=200):
        super().__init__(body)
        self.code = code
        self.status = code
        self.headers = {}

    def getcode(self):
        return self.code

    def info(self):
        return self.headers

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _key(url, data):
    full = url.full_url if hasattr(url, 'full_url') else str(url)
    d = data if data is not None else (getattr(url, 'data', None))
    return (full, bytes(d) if d else None)


def _cached_urlopen(url, data=None, timeout=None, *a, **kw):
    k = _key(url, data)
    with _LOCK:
        body = _HTTP_CACHE.get(k)
    if body is None:
        r = _ORIG_URLOPEN(url, data=data, timeout=timeout, *a, **kw)
        body = r.read()
        with _LOCK:
            _HTTP_CACHE[k] = body
            _STATS['miss'] += 1
    else:
        with _LOCK:
            _STATS['hit'] += 1
    return _CachedResp(body)


urllib.request.urlopen = _cached_urlopen

sys.path.insert(0, '.')
from evaluate_unified import evaluate_thammen  # noqa: E402  (after the patch)

ZONE, STREET, BLDG = 54, 541, 6
OUT = '.marikh_surface_sweep.csv'

AGES = [None, 10, 15, 20, 25, 30, 40, 50]
LUX = [False, True]
CONDS = [None, 'new', 'excellent', 'renovated', 'good', 'average', 'fair', 'poor', 'teardown']
RENTS = [None, 10000, 15000, 25000]

cases = []
# main cross (fp/basement default): 8 × 2 × 9 × 4 = 576
for age in AGES:
    for lux in LUX:
        for cond in CONDS:
            for rent in RENTS:
                cases.append(dict(age=age, lux=lux, cond=cond, rent=rent,
                                  fp=None, basement=None, floors=None))
# footprint sub-grid: 2 × 3 × 2 × 2 × 2 = 48
for fp in (200, 450):
    for age in (None, 20, 40):
        for lux in LUX:
            for cond in (None, 'good'):
                for rent in (None, 15000):
                    cases.append(dict(age=age, lux=lux, cond=cond, rent=rent,
                                      fp=fp, basement=None, floors=None))
# basement sub-sample: 8
for fp in (None, 450):
    for age in (None, 20):
        for fl in (None, 3):
            cases.append(dict(age=age, lux=False, cond=None, rent=None,
                              fp=fp, basement=True, floors=fl))

print(f'matrix: {len(cases)} cases (576 main + 48 footprint + {len(cases)-624} basement)')

FIELDS = ['i', 'age', 'lux', 'cond', 'rent', 'fp', 'basement', 'floors',
          'amount', 'low', 'high', 'method', 'rih', 'n_tx',
          'leader', 'rule', 'cost_value', 'market_value', 'matched_n', 'disp36',
          'geo_n', 'geo_disp', 'stratum_match', 'resurvey',
          'retention', 'effective_age', 'stack_finish', 'stack_cost',
          'muc', 'age_sens_value', 'income_mode', 'teardown_fired', 'luxury_new_fired',
          'lead_note', 'age_honesty', 'divergence', 'elapsed_s', 'error']


def run_case(c):
    t0 = time.time()
    row = {k: c.get(k) for k in ('age', 'lux', 'cond', 'rent', 'fp', 'basement', 'floors')}
    try:
        r = evaluate_thammen(
            zone=ZONE, street=STREET, building=BLDG, audience='buyer',
            building_age_years=c['age'], is_luxury=(True if c['lux'] else None),
            condition=c['cond'], rental_income=c['rent'],
            footprint_m2=c['fp'], basement=c['basement'], floors=c['floors'],
            use_listings=True, use_geo_v2=True)
        v = r.get('valuation') or {}
        L = v.get('leadership') or {}
        vs = (v.get('value_stack') or {})
        sc = vs.get('cost') or {}
        it = v.get('income_triangulation') or {}
        row.update(
            amount=v.get('amount'), low=v.get('low'), high=v.get('high'),
            method=v.get('method'), rih=v.get('range_is_headline'),
            n_tx=v.get('n_transactions'),
            leader=L.get('leader'), rule=L.get('rule'),
            cost_value=L.get('cost_value'), market_value=L.get('market_value'),
            matched_n=L.get('matched_n'), disp36=L.get('dispersion_36'),
            geo_n=L.get('geo_full_n'), geo_disp=L.get('geo_full_dispersion'),
            stratum_match=L.get('stratum_match'), resurvey=L.get('resurvey'),
            retention=sc.get('retention'), effective_age=sc.get('effective_age'),
            stack_finish=sc.get('finish'), stack_cost=sc.get('value'),
            muc=(r.get('material_uncertainty') or {}).get('level'),
            age_sens_value=(v.get('age_sensitivity') or {}).get('value'),
            income_mode=it.get('mode'),
            teardown_fired=bool(v.get('teardown')),
            luxury_new_fired=bool(v.get('luxury_new_premium')),
            lead_note=bool(L.get('note_ar')),
            age_honesty=bool(L.get('age_honesty_note_ar')),
            divergence=bool(L.get('divergence')),
            elapsed_s=round(time.time() - t0, 2), error='')
    except Exception as e:
        row.update(error=f'{type(e).__name__}: {e}', elapsed_s=round(time.time() - t0, 2))
    return row


t_all = time.time()
with open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    for i, c in enumerate(cases):
        row = run_case(c)
        row['i'] = i
        w.writerow(row)
        if i % 25 == 0 or i == len(cases) - 1:
            print(f'[{i+1}/{len(cases)}] age={c["age"]} lux={c["lux"]} cond={c["cond"]} '
                  f'rent={c["rent"]} fp={c["fp"]} -> {row.get("amount")} '
                  f'{row.get("rule")} ({row.get("elapsed_s")}s) '
                  f'http miss/hit={_STATS["miss"]}/{_STATS["hit"]}', flush=True)

print(f'DONE {len(cases)} cases in {time.time()-t_all:.0f}s -> {OUT} '
      f'(http miss={_STATS["miss"]} hit={_STATS["hit"]})')
