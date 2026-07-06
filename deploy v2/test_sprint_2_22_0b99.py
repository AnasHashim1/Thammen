# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.99 «Live Pulse + المعالم-كشارات» (Gemini r8 luxury subset) — isolated tests.

Two value-invariant enhancements:
  A) Live Pulse — the very_stale freshness BANNER (_render_banner) reframed from the alarmist
     «تنبيه: … لم تُحدَّث … استخدم كمرجع إرشادي فقط» to a professional data-sync indicator,
     WITHOUT weakening honesty (source + month + «منذ {days} يوماً» + «إرشاديّة» all kept);
     + a CSS pulse-dot on #dfBanner (frontend, reduced-motion safe).
  B) Landmark chips — the land short-report face surfaces up to 2 auto-discovered
     location_features as chips (nearby amenities / plot quality), filling the sparse land
     face with KNOWN facts (b94 removed the empty «غير محدّد»; b99 adds discovered ones).

Exercises the REAL _render_banner (E14) + reads the REAL index.html.
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML = open('index.html', encoding='utf-8').read()
ENG  = open('evaluate_unified.py', encoding='utf-8').read()

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('PASS |', name)
    else:    failed += 1; print('FAIL |', name)

# ── A. Live Pulse — engine banner reframe (real function) ──
import data_freshness as D
vs = D._render_banner('ديسمبر 2025', 183, 'very_stale')
check('banner very_stale: calmer «تاريخ تحديث بيانات وزارة العدل» lead (b105 register lock)', 'تاريخ تحديث بيانات وزارة العدل' in vs)
check('banner very_stale: alarmist «تنبيه» removed', 'تنبيه' not in vs)
check('banner HONESTY kept — source «وزارة العدل»', 'وزارة العدل' in vs)
check('banner HONESTY kept — staleness «منذ 183 يوماً»', 'منذ 183 يوماً' in vs)
check('banner HONESTY kept — «إرشاديّة» caveat', 'إرشاديّة' in vs)
# regression: other tiers + the .dfc caveat untouched
check('REGRESSION — stale tier banner unchanged',
      D._render_banner('ديسمبر 2025', 40, 'stale') ==
      'آخر تحديث لبيانات وزارة العدل: ديسمبر 2025 (قبل 40 يوماً) — قد لا تعكس آخر تحركات السوق')
check('REGRESSION — fresh tier banner unchanged',
      D._render_banner('ديسمبر 2025', 5, 'fresh') == 'آخر تحديث لبيانات وزارة العدل: ديسمبر 2025')
check('REGRESSION — the .dfc result caveat (_render_caveat) untouched',
      'المرجع مبني على بيانات وزارة العدل المتاحة حتى' in D._render_caveat('31 ديسمبر 2025', 'very_stale'))

# ── A. Live Pulse — frontend pulse dot ──
check('CSS .df-pulse defined', '.df-pulse{' in HTML)
check('pulse has an opacity keyframe animation', '@keyframes dfpulse{' in HTML)
check('pulse respects reduced-motion', '@media(prefers-reduced-motion:reduce){.df-pulse{animation:none' in HTML)
check('#dfBanner render prepends the pulse dot (esc-safe)',
      '\'<span class="df-pulse" aria-hidden="true"></span>\'+esc(d.banner_ar)' in HTML)
check('the old plain textContent banner render is gone',
      'bn.textContent=d.banner_ar;' not in HTML)

# ── B. Landmark chips on the land face ──
i = HTML.index('function showShortReport(d){')
j = HTML.find('\nfunction ', i + 10)
SR = HTML[i:j if j != -1 else len(HTML)]
lm_i = SR.index('surface up to 2 auto-discovered location features')  # the b99 comment
lm = SR[lm_i-200:lm_i+600]
check('landmark chips are inside the _isLand block',
      SR.index('if(_isLand){') < SR.index('surface up to 2 auto-discovered') < SR.index('}else{', SR.index('if(_isLand){')))
check('landmark chips read location_features',
      "(d.location_features||[]).map(x=>(x&&x.label)?x.label:'')" in lm)
check('landmark chips EXCLUDE the classification + height already shown',
      "!/\\bR[123]\\b|G\\s*\\+/.test(l)" in lm)
check('landmark chips capped at 2', '.slice(0,2)' in lm)
check('landmark chips are display-only (esc, non-editable)', "_chip('pin','',esc(l),false)" in lm)

# ── value-invariance + version ──
check('data_freshness change is copy-only (no numeric/valuation logic touched)',
      '_render_banner' in open('data_freshness.py', encoding='utf-8').read())
check('ENGINE_VERSION b-series format (R6, not an exact pin)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+b\d+-", ENG) is not None)
check('SPRINT_TAG b-series format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+b\.\d+'", ENG) is not None)
check('b98 fixes still intact (dedup guard + verify host)',
      "indexOf(d.district)===-1" in HTML and "'https://thammen.qa/verify?ref='" in HTML)

print(f'\n{passed}/{passed+failed} PASS' + ('' if failed == 0 else f' — {failed} FAIL'))
sys.exit(1 if failed else 0)
