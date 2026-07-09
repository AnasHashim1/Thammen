# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.79 — EN core-flow wiring (gate / home / form / top-bars / scope).
E14: reads the REAL index.html. FRONTEND-ONLY / VALUE-INVARIANT — the EN render is dormant
behind EN_ENABLED (b77); AR is byte-identical (the data-en attributes + .lang-en CSS are
inert until the flag flips). Runtime render = R14 Chromium (entry screens in EN, dir-flip)."""
import io
HTML = io.open('index.html', encoding='utf-8').read()

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

# ---- (1) the static-swap mechanism ----
check('_applyStaticI18n defined (captures data-ar0/data-arPh, swaps by LANG)',
      'function _applyStaticI18n()' in HTML and 'el.dataset.ar0=el.innerHTML' in HTML and
      "el.innerHTML=(LANG==='en')?el.dataset.en:el.dataset.ar0" in HTML and
      'el.dataset.arPh=el.getAttribute' in HTML)
check('setLang wires _applyStaticI18n + chk + re-render',
      '_syncLangToggle(); _applyStaticI18n(); try{chk();}catch(e){} _rerenderForLang();' in HTML)
check('hardened dark guard coerces EN->AR when flag off',
      "if(!EN_ENABLED&&l==='en')l='ar';" in HTML)

# ---- (2) gate wired (reuses the bg-en English) + a gate toggle ----
check('gate title/note/ack/button/link carry data-en',
      'id="bgTitle" data-en="Thammen — Automated Market Valuation' in HTML and
      'class="bg-note" data-en="By continuing' in HTML and
      'class="bg-ack" data-en="I acknowledge that Thammen' in HTML and
      'onclick="ackBeta()" data-en="I agree and continue"' in HTML)
check('_mountLangToggle mounts a gate toggle (#betaGate .bgate-head)',
      "document.querySelector('#betaGate .bgate-head')" in HTML and "className='gate-lang'" in HTML)

# ---- (3) home wired ----
# b119 (PO-directed 2026-07-09) removed the 3-step trust band («Enter the address» …) from the
# simplified centered hero. The surviving hero copy (title/sub/CTA/credit) keeps its bilingual
# data-en; b79's real intent (the home hero is EN-toggle-wired) holds.
check('home tag/sub/cta/cred carry data-en',
      'class="htag" data-en="Value your property in Qatar"' in HTML and
      'data-en="Automated market valuation for villas and land in Qatar"' in HTML and
      'data-en="Start the valuation"' in HTML and
      'data-en="Based on registered Ministry of Justice transactions."' in HTML)

# ---- (4) form wired (labels, placeholders, tabs, audience, submit) ----
check('form tabs + labels + placeholders carry data-en / data-en-ph',
      'data-en="Villa/building (address)"' in HTML and 'data-en="Zone no."' in HTML and
      'data-en-ph="e.g. 70"' in HTML and 'data-en="Plot number (PIN)"' in HTML)
# b89 R6 re-point: the «من أنت؟» role selector (5 buttons) was REMOVED (Option A) → the role
# data-en spans are gone with it. The submit + input-entry titles keep their data-en.
check('b89: the audience role buttons are REMOVED (no data-en role spans)',
      '<span data-en="Owner">مالك</span>' not in HTML and '<span data-en="Valuer">مثمّن</span>' not in HTML)
check('submit + entry titles carry data-en («Who are you?» removed with the selector)',
      'onclick="run()" data-en="Value it"' in HTML and
      'data-en="Property entry"' in HTML and 'data-en="Who are you?"' not in HTML)
check('all 5 static top-bar titles carry data-en',
      'data-en="Refine the valuation"' in HTML and 'data-en="Review the data"' in HTML and
      'data-en="Market valuation result"' in HTML and 'data-en="Full report"' in HTML and
      'data-en="Short report"' in HTML)

# ---- (5) JS-rendered surfaces wired via t()/pick() (not data-en) ----
check('openScope uses pick()/t() + LANG-keyed cache',
      "pick(d,'service_level')" in HTML and "pick(s,'label')" in HTML and "pick(s,'reason')" in HTML and
      "t('مدعوم بالكامل','Fully supported')" in HTML and "if(c.dataset.loaded===LANG)return;" in HTML and
      "c.dataset.loaded=LANG;" in HTML)
check('chk() status bar uses t()',
      "t('متصل','Connected')" in HTML and "t('غير متصل','Offline')" in HTML)
check('JS-driven elements are NOT data-en (no clobber): statusBar/dfSubtitle/scopeContent',
      'id="statusBar" data-en' not in HTML and 'id="dfSubtitle" data-en' not in HTML and
      'id="scopeContent" data-en' not in HTML)

# ---- (6) .lang-en dir-flip CSS (entry screens only) ----
check('lang-en flips gate/home/form to LTR (NOT result/report)',
      'body.lang-en #betaGate,body.lang-en .bgate,body.lang-en #homeScreen,body.lang-en #formScreen{direction:ltr}' in HTML and
      'body.lang-en #betaGate .bg-en{display:none}' in HTML and
      'body.lang-en #scopeModal>div{direction:ltr!important' in HTML)
check('result/report screens NOT flipped in lang-en (deferred to b80)',
      'body.lang-en #resultsScreen' not in HTML and 'body.lang-en #reportScreen' not in HTML)

# ---- (7) VALUE-INVARIANCE: b77/b78 intact, AR identity, engine = version lines ----
check('b77 i18n primitives intact; revealed b88', 'function t(ar,en)' in HTML and 'function pick(o,base)' in HTML and 'var EN_ENABLED=true;' in HTML)
check('locked AR identity untouched (التقييم السوقي)', 'التقييم السوقي' in HTML)
check('AR gate/home/form text still present (default render unchanged)',
      'ثمّن — تقييم سوقيّ آليّ للفلل والأراضي في قطر' in HTML and 'تقييم عقارك في قطر' in HTML and
      'رقم المنطقة' in HTML and 'أوافق وأكمل' in HTML)
import io as _io
ENG = _io.open('evaluate_unified.py', encoding='utf-8').read()
check('engine is a valid b-series tag (version-agnostic, R6)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb79:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
