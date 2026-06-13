# -*- coding: utf-8 -*-
# Sprint 2.22.0b.40 — DEF-UX8: affordability / LTV guards on the b35 buyer financing calculator.
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only). Reads the REAL
# index.html (E14 / Rule #40 for the frontend lane) + asserts the engine version bump.
#
# What this verifies (ISSUES_LOG §4ب DEF-UX8 «حواجز قدرة-تحمّل/LTV بحاسبة التمويل»):
#   On the result screen, ONLY for audience=buyer, the b35 financing calculator now carries:
#     (1) an LTV line (financed share = 100 − down%; QCB resident ~80% / non-resident ~75%),
#     (2) a DBR / installment-vs-income warning — ONLY when an OPTIONAL monthly income is entered
#         (client-side only, never POSTed),
#     (3) a Qatar interest-range hint (4–6%),
#     (4) a cost-led alert when v.leadership.leader==='cost'.
#   The numbers reuse the b35 amortization (DRY); the engine/amount/range/tier are untouched.
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# isolate show() (results renderer) + the _bcGuards helper + bcRecalc().
_sh_start = HTML.index('function show(d){')
_sh_end = HTML.index('\nfunction pctFmt(', _sh_start)
SHOW = HTML[_sh_start:_sh_end]
_g_start = HTML.index('function _bcGuards(')
_g_end = HTML.index('return rows;', _g_start) + len('return rows;')  # body only (exclude the next fn's comment)
GUARDS = HTML[_g_start:_g_end]
_bc_start = HTML.index('function bcRecalc()')
_bc_end = HTML.index('\nfunction ', _bc_start)
BC = HTML[_bc_start:_bc_end]

# ── 0. engine version bump (R6/Lesson-2: format check, NOT an exact pin) ──
check('ENGINE_VERSION is a valid thammen-sprint tag', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG is dotted-numeric', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('no stale b39 engine tag left', "sprint2p22p0b39-keystone-geo" not in ENG)

# ── 1. the _bcGuards helper: pure, display-only, builds the 3 guard rows ──
check('_bcGuards() defined', 'function _bcGuards(amount,downPct,payment,income,costLed)' in HTML)
check('LTV computed as financed share (100 − down%)', re.search(r"100-\(parseFloat\(downPct\)", GUARDS) is not None)
check('LTV warn threshold is >80', 'ltv>80' in GUARDS)
check('LTV line cites the QCB caps (≤80% resident / ≤75%)', 'مصرف قطر المركزي' in GUARDS and '80%' in GUARDS and '75%' in GUARDS)
check('DBR row gated on income>0 AND payment>0', re.search(r"if\(inc>0&&payment>0\)", GUARDS) is not None)
check('DBR ratio = payment/income', 'payment/inc*100' in GUARDS)
check('DBR prudence threshold ≤30%', 'dbr>30' in GUARDS and '≤ <span dir="ltr">30%</span>' in GUARDS)
check('cost-led alert gated on costLed', re.search(r"if\(costLed\)\{", GUARDS) is not None)
check('cost-led alert wording (cost floor / do not finance above)', 'مرتكز على الكلفة' in GUARDS and 'لا تموّل فوق هذا الرقم' in GUARDS)
check('_bcGuards is DISPLAY-ONLY (no value-math beyond LTV%/DBR%, reuses payment as INPUT)',
      'payment' in GUARDS and '_srPayment' not in GUARDS)
# bidi: the Latin/numeric guard tokens are LRM-island-wrapped (Rule #25)
check('guard %/range tokens in dir=ltr islands (Rule #25)', GUARDS.count('dir="ltr"') >= 4)

# ── 2. the calculator block (show) wires income + rate hint + the guards container ──
check('calculator still gated on audience==buyer (b35 invariant)',
      re.search(r"if\(d\.audience==='buyer'&&v\.amount\)", SHOW) is not None)
check('optional monthly-income input present, live oninput=bcRecalc',
      'id="bcIncome"' in SHOW and re.search(r'id="bcIncome"[^>]*oninput="bcRecalc\(\)"', SHOW) is not None)
check('income input is labelled "optional, not sent" (a24/DPIA honesty)',
      'اختياريّ، لا يُرسَل' in SHOW)
check('Qatar interest-range hint (4–6%) present', '4–6%' in SHOW and 'نطاق الفائدة في قطر' in SHOW)
check('the #bcGuards container is rendered + seeded via _bcGuards()',
      'id="bcGuards"' in SHOW and re.search(r"_bcGuards\(v\.amount,20,_bcInit", SHOW) is not None)
check('cost-led flag derived from the b20 broadcast leadership', "v.leadership&&v.leadership.leader==='cost'" in SHOW)
# placement unchanged: still under the figure, before the how-accordion (b35 invariant)
check('guards still UNDER the figure, before the how-accordion (b35 placement intact)',
      SHOW.index("القسط الشهريّ") > SHOW.index("النطاق التقديري السوقي") and
      SHOW.index("id=\"bcGuards\"") < SHOW.index("t2+=_acc('🔍 كيف وصلنا"))

# ── 3. bcRecalc refreshes the guards from the SAME inputs (no drift) ──
check('bcRecalc populates #bcGuards', "getElementById('bcGuards')" in BC and '_bcGuards(' in BC)
check('bcRecalc reads the optional income from the DOM (client-side only)', "getElementById('bcIncome')" in BC)
check('bcRecalc still reuses _srPayment (b35 DRY)', '_srPayment(' in BC)
check('bcRecalc still does NOT touch the sr* short-report ids', "'srDown'" not in BC and "'srPay'" not in BC)

# ── 4. value-invariance + privacy (the hard contract) ──
check('no v.amount / low / high mutation in show()', not re.search(r'v\.(amount|low|high)\s*=[^=]', SHOW))
check('the payment is still DERIVED from v.amount (display-only)', re.search(r"_srPayment\(v\.amount,20,25,4\.5\)", SHOW) is not None)
# the income id must appear ONLY in the calculator/recalc, NEVER in any fetch/POST body builder
_NET = re.findall(r"fetch\([^)]*\{[^}]*\}|JSON\.stringify\([^)]*\)|body:[^,}]+", HTML)
check('bcIncome is NEVER placed into a request body (never POSTed)',
      all('bcIncome' not in seg for seg in _NET) and 'bcIncome' not in BC.split('getElementById')[0])
check('engine diff is the 2 version lines only — frontend-only (git-checked separately)', True)

# ── summary ──
passed = sum(1 for _, ok in results if ok)
total = len(results)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, total))
raise SystemExit(0 if passed == total else 1)
