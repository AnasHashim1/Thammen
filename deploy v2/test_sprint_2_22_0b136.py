# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.136 «الوصوليّة: حبس التركيز» (S10, redesign v2) — isolated test (E14).

🟢 FRONTEND-ONLY / VALUE-NEUTRAL — focus management only, no copy/value/methodology change.

Measured before building (R-B/#58): all four modals ALREADY carry role=dialog + aria-modal +
aria-label + Escape (betaGate/scope/terms via b70/a24, the map via b107). The ONLY remaining
a11y gap = focus management (no initial-focus, no Tab-trap, no restore). So b136 = a reusable
_trapFocus helper (WAI-ARIA APG dialog pattern) wired into the four modals.

Verifies: the helper (initial-focus + Tab/Shift+Tab cycle + restore-on-close, reduced-motion-safe),
its wiring into scope/terms/map/betaGate, the map's 3 close paths unified through _mapClose (so focus
restores), and — critically — that NO compliance / value / methodology assertion was weakened:
the b70 Escape handler still covers only scope+terms (betaGate stays NOT Escape-closable by design),
the b107 map ARIA is intact, all four dialogs keep role/aria-modal/aria-label, and the trap helper
carries no user-facing Arabic copy (focus logic only) and no amount/low/high mutation.
"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
ENG = open(os.path.join(HERE, 'evaluate_unified.py'), encoding='utf-8').read()

_p = _f = 0
def check(label, cond):
    global _p, _f
    if cond:
        _p += 1; print('  PASS  ' + label)
    else:
        _f += 1; print('  FAIL  ' + label)

def _slice(src, start, end):
    i = src.find(start); j = src.find(end, i + 1)
    return src[i:j] if (i >= 0 and j > i) else ''

# regions we touched
TRAP       = _slice(HTML, 'function _focusables(', 'function openScope(')
OPENSCOPE  = _slice(HTML, 'function openScope(', 'function closeScope(')
CLOSESCOPE = _slice(HTML, 'function closeScope(', 'function openTerms(')
OPENTERMS  = _slice(HTML, 'function openTerms(', 'function closeTerms(')
CLOSETERMS = _slice(HTML, 'function closeTerms(', '// Sprint 2.22.0b.70')
B70        = _slice(HTML, '// Sprint 2.22.0b.70 (a11y): Escape', 'function ackBeta(')
ACKBETA    = _slice(HTML, 'function ackBeta(', 'async function chk(')
MAP        = _slice(HTML, 'function openMapPicker(', 'function copyResult(')

print('\n== version bump ==')
check("ENGINE_VERSION -> b13x prefix (R6/Lesson-2: version-agnostic)", "thammen-sprint2p22p0b" in ENG)
check("SPRINT_TAG -> 2.22.0b prefix", "SPRINT_TAG = '2.22.0b." in ENG)

print('\n== reusable focus-trap helper ==')
check("_focusables(root) defined", "function _focusables(root){" in TRAP)
check("_focusables filters to visible (offsetParent!==null)", "offsetParent!==null" in TRAP)
check("_focusables selector covers a/button/input/select/textarea/[tabindex]",
      "a[href]" in TRAP and "button:not([disabled])" in TRAP and '[tabindex]:not([tabindex="-1"])' in TRAP)
check("_trapFocus(modal) defined", "function _trapFocus(modal){" in TRAP)
check("captures previously-focused element (restore target)", "var prev=document.activeElement" in TRAP)
check("initial-focus into the modal ((f[0]||modal).focus)", "(f[0]||modal).focus(" in TRAP)
check("Tab handler gate (if(e.key!=='Tab')return)", "if(e.key!=='Tab')return" in TRAP)
check("Shift+Tab wraps to last, Tab wraps to first",
      "e.shiftKey" in TRAP and "last.focus()" in TRAP and "first.focus()" in TRAP)
check("returns teardown that removes listener + restores focus",
      "modal.removeEventListener('keydown',onKey)" in TRAP and "prev&&prev.focus&&prev.focus" in TRAP)
check("reduced-motion-safe focus (preventScroll:true)", "preventScroll:true" in TRAP)
check("teardown handles declared (_scopeTrap/_termsTrap/_gateTrap)",
      "var _scopeTrap=null,_termsTrap=null,_gateTrap=null;" in TRAP)
check("helper carries NO user-facing Arabic copy (focus logic only)",
      not re.search(r'[؀-ۿ]', TRAP))

print('\n== scope modal wiring ==')
check("openScope traps focus (_scopeTrap=_trapFocus(sm))", "_scopeTrap=_trapFocus(sm)" in OPENSCOPE)
check("closeScope releases trap + restores focus (_scopeTrap())", "_scopeTrap();" in CLOSESCOPE)

print('\n== terms modal wiring ==')
check("openTerms traps focus (_termsTrap=_trapFocus(tm))", "_termsTrap=_trapFocus(tm)" in OPENTERMS)
check("closeTerms releases trap + restores focus (_termsTrap())", "_termsTrap();" in CLOSETERMS)

print('\n== map modal: unified close + trap ==')
check("_mapClose unified close defined", "const _mapClose=" in MAP)
check("_mapClose restores focus via trap teardown (if(_mapTrap)_mapTrap())", "if(_mapTrap)_mapTrap()" in MAP)
check("Escape routes through _mapClose", "if(e.key==='Escape')_mapClose()" in MAP)
check("backdrop click routes through _mapClose", "if(e.target===m)_mapClose()" in MAP)
check("close button: inline .remove() removed", 'map-modal-close" onclick' not in MAP)
check("close button wired to _mapClose", ".map-modal-close').onclick=_mapClose" in MAP)
check("map is focus-trapped (_mapTrap=_trapFocus(m))", "_mapTrap=_trapFocus(m)" in MAP)

print('\n== betaGate wiring ==')
check("gate trap init on DOMContentLoaded (only if the gate is shown)",
      "getComputedStyle(g).display!=='none')_gateTrap=_trapFocus(g)" in ACKBETA)
check("ackBeta releases the gate trap on consent (_gateTrap())", "if(_gateTrap){_gateTrap()" in ACKBETA)

print('\n== compliance / ARIA intact (nothing weakened) ==')
check("betaGate keeps role=dialog + aria-modal", 'id="betaGate" role="dialog" aria-modal="true"' in HTML)
check("scopeModal keeps role=dialog + aria-modal + aria-label",
      'id="scopeModal" role="dialog" aria-modal="true" aria-label=' in HTML)
check("termsModal keeps role=dialog + aria-modal + aria-label",
      'id="termsModal" role="dialog" aria-modal="true" aria-label=' in HTML)
check("map keeps b107 ARIA (role + aria-modal + aria-label setAttribute)",
      "m.setAttribute('role','dialog')" in MAP and "m.setAttribute('aria-modal','true')" in MAP
      and "m.setAttribute('aria-label'" in MAP)
_ESC_HANDLER = _slice(B70, "document.addEventListener('keydown',function(e){", "});")
check("b70 Escape handler still covers scope + terms",
      "closeScope()" in _ESC_HANDLER and "closeTerms()" in _ESC_HANDLER)
check("betaGate stays NOT Escape-closable (absent from the Escape handler BODY)",
      "betaGate" not in _ESC_HANDLER)

print('\n== value-neutral ==')
check("no amount/low/high mutation in the trap helper", not re.search(r'v\.(amount|low|high)\s*=[^=]', TRAP))
check("no amount/low/high mutation in the map builder", not re.search(r'v\.(amount|low|high)\s*=[^=]', MAP))
check("no amount/low/high mutation in ackBeta/gate-init", not re.search(r'v\.(amount|low|high)\s*=[^=]', ACKBETA))
check("api.py untouched: no new limiter/route added by b136 (helper is client-side only)",
      "_trapFocus" not in open(os.path.join(HERE, 'api.py'), encoding='utf-8').read())

print('\n---------------------------------------------')
print('  b136 result: %d passed, %d failed' % (_p, _f))
print('---------------------------------------------')
sys.exit(1 if _f else 0)
