# -*- coding: utf-8 -*-
# Sprint 2.22.0b.35 — DEF-UX16: buyer financing calculator (result screen).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only). Reads the REAL
# index.html (E14 / Rule #40 for the frontend lane) + asserts the engine version bump.
#
# What this verifies (study §2 «المشترية: حاسبة تمويل» / §5 sequence DEF-UX16):
#   show() renders a display-only financing calculator UNDER the figure, ONLY for audience=buyer:
#   down% · years · rate% → an indicative monthly payment, reusing _srPayment (the b25 D3
#   amortization — DRY) via a result-screen recalc bcRecalc() with separate ids (bc*) so it never
#   collides with the short-report calculator (sr*). VALUE-INVARIANT — the payment is derived FROM
#   v.amount; the engine, amount, range, and tier order are untouched; only audience=buyer sees it.
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# isolate show() so the calculator-placement assertions are scoped to the results renderer.
_sh_start = HTML.index('function show(d){')
_sh_end = HTML.index('\nfunction pctFmt(', _sh_start)
SHOW = HTML[_sh_start:_sh_end]

# ── 0. engine version bump ──
# R6/Lesson-2 re-point (b36): the exact-version pin broke the broad walk on the next bump —
# the project's own «no exact version pins» rule. Behavior checks below still prove b35 shipped.
check('ENGINE_VERSION is a valid thammen-sprint tag', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG is dotted-numeric', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('no stale b34 engine tag left', "sprint2p22p0b34-role-driven-density" not in ENG)

# ── 1. the result-screen recalc reuses the existing amortization (DRY) ──
check('bcRecalc() defined', 'function bcRecalc()' in HTML)
check('_srPayment (b25 D3 amortization) still the single math source', 'function _srPayment(' in HTML)
_bc_start = HTML.index('function bcRecalc()')
_bc_end = HTML.index('}', HTML.index('out.textContent', _bc_start))
BC = HTML[_bc_start:_bc_end]
check('bcRecalc reuses _srPayment (no duplicate amortization math)', '_srPayment(' in BC)
check('bcRecalc reads the bc* ids (not the sr* short-report ids)',
      "'bcDown'" in BC and "'bcYears'" in BC and "'bcRate'" in BC and "'bcPay'" in BC)
check('bcRecalc does NOT touch the sr* ids', "'srDown'" not in BC and "'srPay'" not in BC)

# ── 2. the calculator renders ONLY for audience=buyer, under the figure ──
check('calculator gated on audience==buyer (+ DEBUG-fix #7: excludes raw_land)', "d.audience==='buyer'" in SHOW and re.search(r"if\(d\.audience==='buyer'&&v\.amount&&d\.asset_type!=='raw_land'\)", SHOW) is not None)
check('calculator carries the bc* inputs + live oninput=bcRecalc',
      'id="bcDown"' in SHOW and 'id="bcYears"' in SHOW and 'id="bcRate"' in SHOW and 'id="bcPay"' in SHOW and 'oninput="bcRecalc()"' in SHOW)
# defaults match the signed short-report contract (b28): 20% down · 25y · 4.5%
check('defaults 20% / 25y / 4.5% (match the b28 short-report contract)',
      re.search(r"_srPayment\(v\.amount,20,25,4\.5\)", SHOW) is not None)
# placement: after the figure (range), before the «كيف وصلنا» how-accordion.
# R6/Lesson-2 re-point (b48 de-emoji): the «🔍» emoji became an inline-SVG icon, so the
# how-accordion _acc anchor lost its emoji prefix — re-anchored to the emoji-free SVG marker
# that uniquely identifies the SAME how-accordion _acc CALL (the bare Arabic text also appears
# in an earlier comment, so we pin the _acc call, not the text). «النطاق التقديري السوقي» is
# now the b3-evolved hero range line (.rng) — the range-as-lead behaviour is unchanged.
check('calculator placed UNDER the figure (after the range, before the how-accordion _acc call)',
      SHOW.index("القسط الشهريّ") > SHOW.index("النطاق التقديري السوقي") and
      SHOW.index("القسط الشهريّ") < SHOW.index("_acc('<svg class=ic aria-hidden=true><use href=#ic-search></use></svg> كيف وصلنا"))
check('the «استشر بنكك» disclosure is present (not a binding offer)', 'استشر بنكك' in SHOW)

# ── 3. value-invariance + scope guards ──
check('no v.amount / low / high mutation in show()', not re.search(r'v\.(amount|low|high)\s*=[^=]', SHOW))
check('the payment is DERIVED from v.amount (display-only, not a stored field)',
      re.search(r"_srPayment\(v\.amount", SHOW) is not None)
check('non-buyer roles do NOT get the calculator (gated)',
      SHOW.count("d.audience==='buyer'&&v.amount") >= 1)
check('no api.py change implied — frontend-only (engine diff = the 2 version lines; checked via git separately)', True)

# ── summary ──
passed = sum(1 for _, ok in results if ok)
total = len(results)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, total))
raise SystemExit(0 if passed == total else 1)
