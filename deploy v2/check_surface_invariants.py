# -*- coding: utf-8 -*-
"""check_surface_invariants.py — the 8-invariant checker over a surface-sweep CSV
(companion to sweep_surface.py; Phase-0 kit, 2026-06-11).

⚠ PROVENANCE: the directive referenced «الثوابت الثمانية المرفقة في رسالة أنس» — the
attachment did NOT arrive; the eight below are DERIVED from the SIGNED corpus, each
cited (#39 flagged). If Anas's list differs, re-run this checker on the same CSV.

  INV-1  §4-a (BRIEF_conditional_leadership_SIGNED §4-a): the headline lies within
         [min(cost,market) … max(cost,market)] ±100k — gate rows (leader market/cost).
  INV-2  E25 rail (LOCKED): never leader=='cost' with cost>=market; cost>=market on a
         failed pool ⇒ rule e25_capped + divergence + MUC>=high.
  INV-3  E26 / b18 §A1: a USER age NEVER moves the headline — amount constant across
         the age axis within each (lux,cond,rent,fp,basement,floors) group; age moves
         only the sensitivity line.
  INV-4  b18 §A2 monotonicity: amount(is_luxury) >= amount(plain) within each
         (age,cond,rent,fp,basement,floors) group.
  INV-5  income precedence + the circularity guard (§20.40): income_led ⇒ a subject
         rent was provided; no rent ⇒ never income_led.
  INV-6  MUC discipline (signed §3): leader=='cost' ⇒ MUC∈{high,critical};
         rule∈{e25_capped,cost_unavailable} ⇒ MUC∈{high,critical}.
  INV-7  range sanity (the b11-inversion class): low <= amount <= high, low <= high.
  INV-8  explicit-lever supremacy (b4, signed §3 'unchanged'): teardown ⇒ the teardown
         lever fired + the gate block-guarded out; new+luxury ⇒ the luxury-new lever
         allowed to fire + the gate block-guarded out when it does.

Usage: PYTHONIOENCODING=utf-8 python check_surface_invariants.py [.marikh_surface_sweep.csv]
"""
import csv
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')
PATH = sys.argv[1] if len(sys.argv) > 1 else '.marikh_surface_sweep.csv'


def num(x):
    try:
        return float(x) if x not in ('', 'None', None) else None
    except Exception:
        return None


def b(x):
    return str(x) == 'True'


rows = []
with open(PATH, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        for _ax in ('age','lux','cond','rent','fp','basement','floors'):
            if r.get(_ax) == '':
                r[_ax] = 'None'
        r['amount_n'] = num(r['amount'])
        r['low_n'] = num(r['low'])
        r['high_n'] = num(r['high'])
        r['cost_n'] = num(r['cost_value'])
        r['mkt_n'] = num(r['market_value'])
        rows.append(r)
errs = [r for r in rows if r.get('error')]
print(f'rows: {len(rows)} ({len(errs)} errors)')
if errs:
    for r in errs[:5]:
        print('  ERROR row', r['i'], r['error'][:100])

breaches = defaultdict(list)

# group key = everything but age
def gkey(r):
    return (r['lux'], r['cond'], r['rent'], r['fp'], r['basement'], r['floors'])

# INV-1 §4-a
for r in rows:
    if r['leader'] in ('market', 'cost') and r['cost_n'] and r['mkt_n'] and r['amount_n']:
        lo, hi = min(r['cost_n'], r['mkt_n']), max(r['cost_n'], r['mkt_n'])
        if not (lo - 100_000 <= r['amount_n'] <= hi + 100_000):
            breaches['INV-1'].append((r['i'], r['amount_n'], lo, hi))

# INV-2 E25
for r in rows:
    if r['leader'] == 'cost' and r['cost_n'] and r['mkt_n'] and r['cost_n'] >= r['mkt_n']:
        breaches['INV-2'].append((r['i'], 'cost led upward'))
    if (r['leader'] and r['cost_n'] and r['mkt_n'] and r['cost_n'] >= r['mkt_n']
            and r['rule'] not in ('matched', 'geo_full', '')):
        if r['rule'] != 'e25_capped' or not b(r['divergence']) or r['muc'] not in ('high', 'critical'):
            breaches['INV-2'].append((r['i'], f"rule={r['rule']} div={r['divergence']} muc={r['muc']}"))

# INV-3 E26/A1 — amount constant across ages within a group
groups = defaultdict(list)
for r in rows:
    if not r.get('error'):
        groups[gkey(r)].append(r)
for k, g in groups.items():
    amts = {r['amount'] for r in g}
    if len(amts) > 1:
        breaches['INV-3'].append((k, sorted(amts)))

# INV-4 finish monotonicity — pair plain/lux within (age,cond,rent,fp,basement,floors)
pair = defaultdict(dict)
for r in rows:
    if not r.get('error'):
        pair[(r['age'], r['cond'], r['rent'], r['fp'], r['basement'], r['floors'])][r['lux']] = r
for k, d in pair.items():
    p, l = d.get('False'), d.get('True')
    if p and l and p['amount_n'] and l['amount_n'] and l['amount_n'] < p['amount_n']:
        breaches['INV-4'].append((k, p['amount_n'], l['amount_n']))

# INV-5 income
for r in rows:
    if r['income_mode'] == 'income_led' and r['rent'] in ('', 'None', None):
        breaches['INV-5'].append((r['i'], 'income_led without rent'))
    if r['rent'] not in ('', 'None', None) and r['income_mode'] == 'income_led' and r['rule']:
        breaches['INV-5'].append((r['i'], 'gate fired alongside income_led'))

# INV-6 MUC
for r in rows:
    if r['leader'] == 'cost' and r['muc'] not in ('high', 'critical'):
        breaches['INV-6'].append((r['i'], f"cost-led muc={r['muc']}"))
    if r['rule'] in ('e25_capped', 'cost_unavailable') and r['muc'] not in ('high', 'critical'):
        breaches['INV-6'].append((r['i'], f"{r['rule']} muc={r['muc']}"))

# INV-7 range sanity
for r in rows:
    a, lo, hi = r['amount_n'], r['low_n'], r['high_n']
    if a and lo and hi and not (lo <= a <= hi and lo <= hi):
        breaches['INV-7'].append((r['i'], lo, a, hi))

# INV-8 explicit levers
for r in rows:
    if r['cond'] == 'teardown':
        if not b(r['teardown_fired']) or r['rule']:
            breaches['INV-8'].append((r['i'], f"teardown fired={r['teardown_fired']} rule={r['rule']}"))
    if b(r['luxury_new_fired']) and r['rule']:
        breaches['INV-8'].append((r['i'], 'gate fired alongside luxury_new'))

print('\n— the 8 invariants (target: ZERO breaches) —')
total = 0
for k in ['INV-1', 'INV-2', 'INV-3', 'INV-4', 'INV-5', 'INV-6', 'INV-7', 'INV-8']:
    n = len(breaches[k])
    total += n
    print(f'  {k}: {n} breach(es)')
    for x in breaches[k][:4]:
        print('      ', x)
print(f'TOTAL breaches: {total}')

# ── 2. the input→effect map (baseline slice: others at default) ──
print('\n— input→effect map (axis swept at default-others; amount range + what moves) —')
BASE = dict(lux='False', cond='None', rent='None', fp='None', basement='None', floors='None')
def base_match(r, skip):
    return all(str(r[k]) == v for k, v in BASE.items() if k != skip) and (
        skip == 'age' or str(r['age']) == 'None')
for axis in ['age', 'lux', 'cond', 'rent', 'fp']:
    sl = [r for r in rows if base_match(r, axis)]
    amts = sorted({r['amount_n'] for r in sl if r['amount_n']})
    sens = sorted({num(r['age_sens_value']) for r in sl if num(r['age_sens_value'])})
    moves = ('HEADLINE' if len(amts) > 1 else
             ('SENSITIVITY-ONLY' if len(sens) > 1 or (axis == 'age' and sens) else 'NO EFFECT'))
    print(f'  {axis:5s}: n={len(sl):3d} | amount [{amts[0]:,.0f} … {amts[-1]:,.0f}]'
          f' | distinct={len(amts)} | sens={len(sens)} → {moves}')

# ── 3. top-5 adjacent jumps (cliff detection) ──
print('\n— top-5 adjacent jumps —')
ORDERS = {'age': ['None', '10', '15', '20', '25', '30', '40', '50'],
          'cond': ['None', 'excellent', 'renovated', 'good', 'average', 'fair', 'poor', 'teardown'],
          'rent': ['None', '10000', '15000', '25000'],
          'fp': ['None', '200', '450']}
jumps = []
for axis, order in ORDERS.items():
    others = [k for k in ['age', 'lux', 'cond', 'rent', 'fp', 'basement', 'floors'] if k != axis]
    by = defaultdict(dict)
    for r in rows:
        if r['amount_n']:
            by[tuple(str(r[k]) for k in others)][str(r[axis])] = r['amount_n']
    for k, d in by.items():
        for a, bb in zip(order, order[1:]):
            if a in d and bb in d:
                jumps.append((abs(d[bb] - d[a]), axis, a, bb, d[a], d[bb], k))
jumps.sort(reverse=True)
for j in jumps[:5]:
    print(f'  Δ{j[0]:>12,.0f} | {j[1]}: {j[2]}→{j[3]} | {j[4]:,.0f}→{j[5]:,.0f} | ctx {j[6]}')

# ── 4. leadership distribution ──
print('\n— leadership distribution over the surface —')
dist = Counter()
for r in rows:
    if r.get('error'):
        dist['error'] += 1
    elif b(r['teardown_fired']):
        dist['teardown lever (b4)'] += 1
    elif b(r['luxury_new_fired']):
        dist['luxury-new lever (b4)'] += 1
    elif r['income_mode'] == 'income_led':
        dist['income_led'] += 1
    elif r['rule']:
        dist[f"gate:{r['rule']}"] += 1
    else:
        dist['no-gate (other)'] += 1
n = len(rows)
for k, v in dist.most_common():
    print(f'  {k:28s} {v:4d}  ({100*v/n:.1f}%)')
sys.exit(1 if total else 0)
