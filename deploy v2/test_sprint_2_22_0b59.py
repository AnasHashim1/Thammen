# -*- coding: utf-8 -*-
# Sprint 2.22.0b.59 — «حارس انعكاس النطاق» (range-inversion guard).
# BACKEND-ONLY, value-invariant on all live traffic (no user-facing text; no new GIS).
#
# Recon (Rule #58, measured): the §20.50 b11 `_cost_reanchor_down` low>high inversion is in
# DEAD CODE — its producer `_cost_triangulation` was RETIRED by b20 (zero call sites), and the
# two documented cases (54/788/10, 55/1056/60) are NOT inverted live (b20's leadership gate
# routes them through the E25-safe cost_led path). b59 = the honest LIVE version: a final
# belt-and-braces clamp enforcing low <= amount <= high (so low <= high) over the SETTLED range,
# closing the geo_full low-raise theoretical residual (:5157, cost floor not checked vs high)
# + any future path. NO-OP on every current case → byte-identical headline/range.
#
# E14 / Rule #40: exercises the REAL production `_clamp_valuation_range` + the production source.
import re, pathlib
import evaluate_unified as eu

ROOT = pathlib.Path(__file__).parent
ENG  = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

def _run(amount, lo, hi, extra=None):
    """Run the production clamp on a fresh valuation dict; return it."""
    v = {'amount': amount, 'low': lo, 'high': hi, 'method': 'comparison_thin', 'rule': 'cost_led'}
    if extra:
        v.update(extra)
    eu._clamp_valuation_range(v)
    return v

# ── 1. behaviour: invariant enforced (low <= amount <= high) ──
v = _run(2400000, 2400000, 5400000)   # canonical cost_led anchor (54/541/6)
check('valid no-op (2.4M cost_led): unchanged', v['low'] == 2400000 and v['high'] == 5400000)

v = _run(3800000, 3100000, 3800000)   # geo_full anchor (V001 56/647/6)
check('valid widened no-op (V001): unchanged', v['low'] == 3100000 and v['high'] == 3800000)

v = _run(1100000, 1500000, 3000000)   # low > amount → clamp low down to amount
check('fix low>amount: low clamped to amount', v['low'] == 1100000 and v['high'] == 3000000)

v = _run(2400000, 2000000, 2200000)   # high < amount → clamp high up to amount
check('fix high<amount: high clamped to amount', v['low'] == 2000000 and v['high'] == 2400000)

v = _run(1700000, 3000000, 1000000)   # full inversion (low>high, amount between) → degenerate-valid
check('fix full inversion: low<=amount<=high holds',
      v['low'] <= v['amount'] <= v['high'] and v['low'] <= v['high'])

# the invariant ALWAYS holds after the clamp, across a grid (adversarial)
grid_ok = True
for a in (1000000, 2400000, 5000000):
    for lo in (500000, 2400000, 6000000):
        for hi in (500000, 2400000, 6000000):
            r = _run(a, lo, hi)
            if not (r['low'] <= r['amount'] <= r['high'] and r['low'] <= r['high']):
                grid_ok = False
check('invariant holds across 27-cell (amount,low,high) grid', grid_ok)

# ── 2. safety: refusals / bad inputs untouched ──
v = {'amount': None, 'low': 500, 'high': 100, 'method': 'insufficient_data'}
eu._clamp_valuation_range(v)
check('refusal (amount None): untouched', v['low'] == 500 and v['high'] == 100)

v = {'amount': 2400000, 'low': None, 'high': 5400000}
eu._clamp_valuation_range(v)
check('low None: untouched', v['low'] is None and v['high'] == 5400000)

v = {'amount': True, 'low': 1, 'high': 2}   # bool is int in py → excluded
eu._clamp_valuation_range(v)
check('bool amount excluded (isinstance(True,int)) : untouched', v['low'] == 1 and v['high'] == 2)

# None dict / non-dict → no raise
try:
    eu._clamp_valuation_range(None); eu._clamp_valuation_range(123); _noraise = True
except Exception:
    _noraise = False
check('None / non-dict input: no raise', _noraise)

# ── 3. idempotent + only low/high touched (no other key mutated) ──
v = _run(1100000, 1500000, 3000000, extra={'central_estimate': 1100000, 'range_is_headline': True})
before_keys = {k: v[k] for k in v if k not in ('low', 'high')}
eu._clamp_valuation_range(v)   # second pass
after_keys = {k: v[k] for k in v if k not in ('low', 'high')}
check('idempotent (2nd pass no change)', v['low'] == 1100000 and v['high'] == 3000000)
check('no other key mutated (method/rule/central_estimate/range_is_headline intact)',
      before_keys == after_keys)

# ── 4. wiring: called on BOTH attach paths, BEFORE _attach_report_identity, with the def present ──
check('helper defined (def _clamp_valuation_range)', 'def _clamp_valuation_range(valuation):' in ENG)
check('called on main path', '_clamp_valuation_range(output.get(\'valuation\'))' in ENG)
check('called on fast/income path', '_clamp_valuation_range(_fast_result.get(\'valuation\'))' in ENG)
# main path: the clamp call must appear BEFORE the main report-identity attach
_main_clamp = ENG.find("_clamp_valuation_range(output.get('valuation'))")
_main_attach = ENG.find('_attach_report_identity(output, zone, street, building, pin, {')
check('main: clamp BEFORE its _attach_report_identity',
      _main_clamp != -1 and _main_attach != -1 and _main_clamp < _main_attach)
# fast path: clamp before the fast attach
_fast_clamp = ENG.find("_clamp_valuation_range(_fast_result.get('valuation'))")
_fast_attach = ENG.find('_attach_report_identity(_fast_result, zone, street, building, None,')
check('fast: clamp BEFORE its _attach_report_identity',
      _fast_clamp != -1 and _fast_attach != -1 and _fast_clamp < _fast_attach)

# ── 5. value-invariance contract on the 5 engineering fixtures (clamp = NO-OP) ──
FIXTURES = [(2400000, 2400000, 5400000), (3800000, 3100000, 3800000),
            (2600000, 2000000, 2600000), (2400000, 2200000, 2600000)]
inv_ok = True
for a, lo, hi in FIXTURES:
    r = _run(a, lo, hi)
    if not (r['low'] == lo and r['high'] == hi):
        inv_ok = False
check('NO-OP on the 4 valued fixtures (byte-identical low/high)', inv_ok)

# ── 6. dead-code premise: the retired b11/b16 reanchor producers have NO call site ──
check('b11 _cost_triangulation retired (no call form)',
      ENG.count('_cost_triangulation(') == 1)   # only the def line
check('b16 _old_stock_reanchor retired (no call form)',
      ENG.count('_old_stock_reanchor(') == 1)   # only the def line

# ── 7. engine version (format only — R6 / Lesson-2: no exact pin) ──
check('ENGINE_VERSION format (thammen-sprint…)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('engine at/beyond b59 (b58 tag gone)', 'thammen-sprint2p22p0b58' not in ENG)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
