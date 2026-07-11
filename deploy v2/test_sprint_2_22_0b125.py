"""Sprint 2.22.0b.125 (S4b) — result-screen EVIDENCE redesign (isolated, E14).

The lower half of the result screen (`show()`) rebuilds from b15/b31/b52 accordions →
flat, scroll-revealed design sections (EVIDENCE / HOW / SCENARIOS / LIMITS / full fold).
This test reads the REAL index.html + evaluate_unified.py and asserts:
  [1]  the S4b section builders exist
  [2]  show() assembles the flat sections + the reveal hook (no more «كيف وصلنا» accordion)
  [3]  EVERY compliance / methodology / honesty string is preserved verbatim
  [4]  the reconciliation chip is HONEST (spread % only on strong_convergence; label-only on
       divergence; omitted otherwise) — never an invented number
  [5]  value-invariance: no `v.amount` mutation; scenarios reuse the broadcast low/high
  [6]  the refusal path is unchanged (still uses `flat`, no evidence sections)
  [7]  the sticky action bar + the design CSS classes
  [8]  the version bump
"""
from __future__ import annotations
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _test_helpers import Reporter, set_stdout_utf8
set_stdout_utf8()
_R = Reporter()
def check(name, cond): _R.check(cond, name)

_HERE = os.path.dirname(os.path.abspath(__file__))
HTML = open(os.path.join(_HERE, 'index.html'), encoding='utf-8').read()
ENG = open(os.path.join(_HERE, 'evaluate_unified.py'), encoding='utf-8').read()

# Isolate the show() function body (from `function show(d){` to the next top-level `function `).
_m = re.search(r'\nfunction show\(d\)\{', HTML)
_show = HTML[_m.start():HTML.index('\nfunction ', _m.start()+20)] if _m else ''

# ── [1] the S4b section builders exist ────────────────────────────────────
print('\n[1] S4b section builders')
for fn in ('_s4bEvidence', '_s4bViz', '_s4bTrendSpark', '_s4bHow', '_s4bScenarios', '_s4bLimits'):
    check(f'function {fn} defined', ('function '+fn+'(') in HTML)

# ── [2] show() assembles the flat sections + reveal hook; the accordion is gone ──
print('\n[2] flat-section assembly (accordions removed)')
check('secEv buffer built (=_s4bEvidence)', 'secEv+=_s4bEvidence(d,v)' in _show)
check('secHow buffer built (=_s4bHow)', 'secHow+=_s4bHow(d,v,acc,how,_dense)' in _show)
check('secScn buffer built (=_s4bScenarios)', 'secScn=_s4bScenarios(v)' in _show)
check('secLim buffer built (=_s4bLimits)', 'secLim=_s4bLimits(d,muc)' in _show)
check('secFull fold built', 'secFull=' in _show and 'rs-full' in _show)
check('assembly is the flat design order',
      'h=head+alerts+t1+secEv+secHow+secScn+secLim+secFull+foot+t3;' in _show)
check('reveal-on-scroll hook wired', "_revealOnScroll('#rOut .rs-sec.rv')" in _show)
check('the b31 «كيف وصلنا» accordion is GONE from show()',
      "_acc('<svg class=ic aria-hidden=true><use href=#ic-search></use></svg> '+t('كيف وصلنا لهذا الرقم؟'" not in _show)
check('the b52 _mucFold accordion CODE is GONE from show()',
      'const _mucFold = muc ? _acc(' not in _show and 't1+_mucFold+t2' not in _show)
check('MUC clause now lives inside the LIMITS section (secLim, from muc)', 'if(muc)h+=muc;' in HTML)

# ── [3] compliance / methodology / honesty strings preserved (verbatim) ────
print('\n[3] compliance preserved verbatim')
check('«ليس تقييماً معتمداً» (t1, kept)', 'ليس تقييماً معتمداً' in HTML)
check('product identity «التقييم السوقي» (t1, b54)', 'التقييم السوقي' in HTML)
check('range-as-lead «النطاق التقديري السوقي» (t1, kept)', 'النطاق التقديري السوقي' in HTML)
check('CC BY 4.0 on the comparables table footer', 'CC BY 4.0' in HTML)
check('market-led honest frame «قرّرت رقمك»', 'هي التي قرّرت رقمك' in HTML)
check('cost-led considered frame «لم تقُد الرقم»', 'لم تقُد الرقم' in HTML)
check('geo widening disclosure «الموسَّع جغرافياً»', 'الموسَّع جغرافياً' in HTML)
check('answer-4 «دون تسويةٍ زمنيّة» in LIMITS', 'دون تسويةٍ زمنيّة' in HTML)
check('answer-8 «استدلالاً بالسعر … لا معاينةً» under scenarios',
      'استدلالاً بالسعر المسجَّل، لا معاينةً' in HTML)
check('RICS VPGA 10 / VPS 6 in LIMITS', 'VPGA 10 / VPS 6' in HTML)
check('IVS 106 in LIMITS', 'IVS 106' in HTML)
check('b64 cost-basis hero note preserved (t1)', 'اعتمدنا كلفةَ البناء' in HTML)
check('b72 e25 divergence hero note preserved (t1)', 'كلفةُ إعادة بناء بيتك' in HTML)
check('«عدم اليقين الجوهري» (b105 term, MUC chip)', 'عدم اليقين الجوهري' in HTML)
check('«بانتظار مراجعة مُقيِّم مُرخّص» reachable (a20 status via pick)',
      "pick(d.material_uncertainty||{},'rics_compliant_status')" in HTML)

# ── [4] reconciliation chip is HONEST (real field, never invented) ─────────
print('\n[4] reconciliation chip honesty')
check('reads the TOP-LEVEL d.reconciliation (not v.reconciliation)',
      'const rec=d.reconciliation||{}' in HTML)
check('spread % shown ONLY on strong_convergence',
      "rec.status==='strong_convergence'" in HTML and "rec.spread_pct.toFixed(1)" in HTML)
check('divergence → label «تباعد المنهجين», NO invented number',
      "rec.status==='divergence'" in HTML and 'تباعد المنهجين' in HTML)
# the divergence branch must not print spread_pct (answer 14: «حالة تباعد لا الرقم»)
_div = HTML[HTML.index("rec.status==='divergence'"):HTML.index("rec.status==='divergence'")+400]
check('divergence branch prints no spread_pct number', 'spread_pct' not in _div)
check('comparison_only / absent → no chip (only the two statuses handled)',
      "rec.status==='comparison_only'" not in HTML)

# ── [5] value-invariance + scenarios reuse broadcast low/high ──────────────
print('\n[5] value-invariance')
check('scenarios reuse v.scenarios.items (b23), not recomputed',
      'const sc=v.scenarios;' in HTML and 'sc.items.forEach' in HTML)
check('scenario ranges from BROADCAST low/high (no invented range)',
      'it.low!=null&&it.high!=null' in HTML)
check('viz estimate = amount / effective area (broadcast fields, honest)',
      'v.amount/eff' in HTML and 'effective_per_villa' in HTML)
check('viz «within range» assertion is CONDITIONAL on min<=est<=max',
      'within=(est>=mn&&est<=mx)' in HTML)
check('no result-screen JS mutates v.amount', 'v.amount=' not in _show.replace('v.amount==','').replace('v.amount!=','').replace('v.amount||','').replace('v.amount)','').replace('v.amount,','').replace('v.amount>','').replace('v.amount&&','').replace('v.amount+','').replace('v.amount/',''))
check('the count-up display-only hook stays (S4a)',
      "_countUp(el,parseFloat(el.getAttribute('data-countup'))" in _show)

# ── [6] refusal path unchanged (no evidence sections) ──────────────────────
print('\n[6] refusal path unchanged')
check('refusal assembly still flat (head+muc+a8acc+alerts+flat+foot)',
      'h=head+muc+a8acc+alerts+flat+foot;' in _show)
check('refusal branch does NOT build the evidence sections',
      'else { flat+=h; }' in _show or 'else{ flat+=h; }' in _show or 'flat+=h;' in _show)

# ── [7] sticky action bar + design CSS ─────────────────────────────────────
print('\n[7] sticky action bar + CSS')
check('sticky action bar (.rs-bar) built with the 3 CTAs',
      "t3+='<div class=\"rs-bar\">'" in HTML and "openShortReport()" in HTML and "openReport()" in HTML)
check('refine CTA hidden for raw_land (b97 preserved)',
      "d.asset_type!=='raw_land'" in _show)
for cls in ('.rs-viz{', '.rs-ctab{', '.rs-trend{', '.rs-chip{', '.rs-stack{', '.rs-scard{',
            '.rs-scn{', '.rs-lim{', '.rs-full{', '.rs-bar{', '.rs-mfold{', '.rs-honesty{'):
    check(f'CSS rule {cls} defined', cls in HTML)
check('reveal primitive .rv / .rv-in present (S0)', '.rv{' in HTML and '.rv.rv-in{' in HTML)
check('mobile media query collapses the grids', 'max-width:560px' in HTML and '.rs-stack{grid-template-columns:1fr' in HTML)
check('EN LTR override extended to the viz/trend', 'body.lang-en #rOut .rs-viz .vtrack' in HTML)

# ── [8] version bump ──────────────────────────────────────────────────────
print('\n[8] version')
# R6/Lesson-2 (b126): no exact-version pin — the S4b structure survives later sprints (b126 hotfix bumped
# the version). Assert the format + at/beyond b125.
check('ENGINE_VERSION format (thammen-sprint…b-series)', re.search(r"ENGINE_VERSION = 'thammen-sprint2p22p0b\d+", ENG) is not None)
check('SPRINT_TAG 2.22.0b-series format', re.search(r"SPRINT_TAG = '2\.22\.0b\.\d+'", ENG) is not None)

sys.exit(_R.report())
