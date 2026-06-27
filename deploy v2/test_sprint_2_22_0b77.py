# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.77 — EN localization INFRASTRUCTURE (dormant i18n scaffold).
E14: reads the REAL index.html + evaluate_unified.py. Frontend-only / value-invariant.
The toggle is built DARK behind EN_ENABLED=false so the live build stays byte-identical
Arabic (no string wiring this sprint); the reveal sprint flips the flag once EN coverage
+ PO wording sign-off land. Runtime behaviour (dir/locale flip, toggle mount) = R14 Chromium."""
import io

HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond:
        passed += 1; print('  ok  ', name)
    else:
        failed += 1; print('  FAIL', name)

# ---- (1) dark-period default: EN forced OFF, AR is the guaranteed state ----
check('EN_ENABLED defaults false (dark)',
      'var EN_ENABLED=false;' in HTML)
check('LANG init forces AR while EN dark (ignores any stored choice)',
      "var LANG=(EN_ENABLED&&_langStored()==='en')?'en':'ar';" in HTML)
check('DOMContentLoaded restore gated by EN_ENABLED',
      "if(EN_ENABLED){var s=_langStored();setLang(s==='en'?'en':'ar');}" in HTML)
check('setLang dark-period guard (EN stays off until reveal)',
      "if(!EN_ENABLED&&l==='en')" in HTML and "EN_ENABLED" in HTML)
check('_mountLangToggle dormant until EN_ENABLED',
      'function _mountLangToggle(){' in HTML and 'if(!EN_ENABLED)return;' in HTML)

# ---- (2) the i18n primitives ----
check('t(ar,en) inline-literal translator with AR fallback',
      "function t(ar,en){return (LANG==='en'&&en!=null)?en:ar;}" in HTML)
check('pick(o,base) resolves _en/_ar off a backend object',
      'function pick(o,base)' in HTML and "o[base+'_en']" in HTML and "o[base+'_ar']" in HTML)
check('_loc() switches Intl locale (Arabic-Indic vs Western)',
      "function _loc(){return LANG==='en'?'en-US':'ar-QA';}" in HTML)
check('fmt() routed through _loc() (old hardcoded ar-QA fmt def gone)',
      'Number(n).toLocaleString(_loc())}' in HTML and
      "toLocaleString('ar-QA')}" not in HTML)

# ---- (3) setLang flips document direction + lang + body class ----
check('setLang sets <html dir> ltr/rtl',
      "h.setAttribute('dir',LANG==='en'?'ltr':'rtl');" in HTML)
check('setLang sets <html lang>',
      "h.setAttribute('lang',LANG);" in HTML)
check('setLang toggles body.lang-en',
      "document.body.classList.toggle('lang-en',LANG==='en');" in HTML)
check('setLang re-renders the active result screen',
      'function _rerenderForLang()' in HTML and 'function setLang(l){' in HTML)

# ---- (4) CSS scaffold (inert until an element carries the class) ----
check('body.lang-en root LTR override',
      'body.lang-en{direction:ltr;text-align:left}' in HTML)
check('.lang-toggle pill style',
      '.lang-toggle{' in HTML)
check('.home-lang slot style',
      '.home-lang{' in HTML)

# ---- (5) VALUE-INVARIANCE: AR untouched, engine = version lines only ----
check('existing local `const t` (line ~3016) intact — no global-t collision break',
      'const t=cp.time_pct' in HTML)
check('locked hero label preserved (b54 terminology lock)',
      'التقييم السوقي' in HTML)
check('forced-sale honesty preserved (b56)',
      'ليست تصفية معتمدة' in HTML)
check('b72 value-clarity copy intact (cost-led de-jargon)',
      'كلفةُ إعادة بناء بيتك' in HTML)
check('b75 synonym-unify intact (منهج الدخل)',
      'منهج الدخل' in HTML)
check('static EN mirrors preserved (gate fold + source credit)',
      'class="bg-en"' in HTML and 'src-credit' in HTML)
check('engine is a valid b-series tag (version-agnostic, R6) — b77 added no logic',
      "SPRINT_TAG = '2.22.0b." in ENG and
      'thammen-sprint2p22p0b' in ENG)

print('\nb77:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
