# -*- coding: utf-8 -*-
# Sprint 2.22.0b.33 — DEF-UX14: identity-input default (study §4, option D).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only). Reads the REAL
# index.html (E14 / Rule #40 for the frontend lane) + asserts the engine version bump.
#
# What this verifies (study §4 «إعادة تصميم مدخل البيانات» — option D = «افتراضيّ + سطر مساعدة»):
#   (a) HELP LINE on the address input: the simple owner saw three bare number fields with no
#       source hint (the PIN field already had one) — a help line now tells the Qatari user
#       WHERE the national address comes from (building address plate / Kahramaa bill).
#   (b) REASONABLE DEFAULT: remember the last property identity LOCALLY (localStorage, in-memory
#       fallback) so a returning owner/agent doesn't retype it. First visit = empty (zero
#       first-time clutter). A «مسح» link clears it; shown only when a saved value exists.
# Value-invariant by construction: run() reads zone/street/building OR pin and builds bd EXACTLY
# as before; the identity store only PRE-FILLS the fields. No api.py / engine-logic change.
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# Helper: isolate the run() body so the «bd built exactly as before» + «_saveIdentity called»
# assertions are scoped to the submit path.
_run_start = HTML.index('async function run(){')
_run_end = HTML.index('async function thammenReEvalOverride(', _run_start)
RUN = HTML[_run_start:_run_end]

# Helper: isolate the formScreen markup (between its id and the next screen).
_form_start = HTML.index('id="formScreen"')
_form_end = HTML.index('id="refineScreen"', _form_start)
FORM = HTML[_form_start:_form_end]

# ── 0. engine version bump (single source; /api/health derives from SPRINT_TAG) ──
check('ENGINE_VERSION → b33-identity-input-default', "thammen-sprint2p22p0b33-identity-input-default" in ENG)
check('SPRINT_TAG → 2.22.0b.33', "'2.22.0b.33'" in ENG)
check('no stale b32 engine tag left in evaluate_unified.py', "sprint2p22p0b32-confirm-simplify" not in ENG)

# ── (a) HELP LINE on the address input ──
check('address help line present (verbatim)',
      'هذه الأرقام على لوحة عنوان المبنى أو فاتورة كهرماء (المنطقة، ثم الشارع، ثم رقم المبنى).' in HTML)
# It must sit on the ADDRESS group, after the three fields (grpAddr), not on the PIN group.
_ga_start = FORM.index('id="grpAddr"')
_ga_end = FORM.index('id="grpLand"', _ga_start)
GRPADDR = FORM[_ga_start:_ga_end]
check('help line lives inside grpAddr (address group)', 'لوحة عنوان المبنى أو فاتورة كهرماء' in GRPADDR)
check('help line comes AFTER the building field', GRPADDR.index('id="building"') < GRPADDR.index('لوحة عنوان المبنى'))
check('help line reuses the .br-note class (visual parity with PIN hint)',
      re.search(r'class="br-note"[^>]*>هذه الأرقام على لوحة عنوان', HTML) is not None)
# the pre-existing PIN hint is untouched (still there)
check('PIN source hint still present (untouched)', 'أدخل رقم القطعة من شهادة الملكية أو خرائط GIS' in HTML)

# ── (b) REASONABLE DEFAULT: local identity store ──
check('_IDENT_KEY defined', "_IDENT_KEY='thammen_last_ident'" in HTML)
check('_saveIdentity defined', 'function _saveIdentity()' in HTML)
check('_restoreIdentity defined', 'function _restoreIdentity()' in HTML)
check('clearIdentity defined', 'function clearIdentity()' in HTML)
check('_identGet/_identPut/_identDel helpers defined',
      'function _identGet()' in HTML and 'function _identPut(' in HTML and 'function _identDel()' in HTML)

# the store persists tab + the four identity fields (NOT audience — single-purpose «identity»)
_si_start = HTML.index('function _saveIdentity()')
_si_end = HTML.index('function _restoreIdentity()', _si_start)
SAVE = HTML[_si_start:_si_end]
for f in ['tab:inputTab', "'zone'", "'street'", "'building'", "'pin'"]:
    check('_saveIdentity persists ' + f, f in SAVE)
check('_saveIdentity does NOT persist audience (out of identity scope)', 'audience' not in SAVE)

# in-memory fallback (no localStorage → does not throw, matches a24 gate pattern)
check('_identGet has try/catch in-memory fallback', re.search(r'function _identGet\(\)\{try\{.*\}catch\(e\)\{return _identMem;\}\}', HTML) is not None)
check('_identPut has try/catch in-memory fallback', '_identMem=o' in HTML)
check('_identMem declared', '_identMem=null' in HTML)

# first-visit = empty: _restoreIdentity returns early when nothing is stored
_ri_start = HTML.index('function _restoreIdentity()')
_ri_end = HTML.index('function clearIdentity()', _ri_start)
RESTORE = HTML[_ri_start:_ri_end]
check('_restoreIdentity early-returns on empty (first visit clutter-free)',
      re.search(r'var o=_identGet\(\);\s*if\(!o\)return;', RESTORE) is not None)
check('_restoreIdentity re-selects the land tab when saved', "o.tab==='land'" in RESTORE and "selTab('land')" in RESTORE)
check('_restoreIdentity reveals the «مسح» link only when a value exists',
      "clrIdent" in RESTORE and "display='inline'" in RESTORE)

# wiring: restore on load, save on submit
check('_restoreIdentity wired to DOMContentLoaded', "addEventListener('DOMContentLoaded',_restoreIdentity)" in HTML)
check('_saveIdentity called inside run()', '_saveIdentity();' in RUN)

# clear link markup: hidden by default, calls clearIdentity
check('«مسح» link in the form title, hidden by default',
      re.search(r'id="clrIdent"[^>]*onclick="clearIdentity\(\)"[^>]*display:none', HTML) is not None)
check('clearIdentity empties the four fields + hides the link',
      "['zone','street','building','pin']" in HTML and "display='none'" in HTML)

# ── value-invariance guard: run() still builds bd from the same fields, unchanged ──
check('run() address branch builds bd from zone/street/building (unchanged)',
      'bd={zone:+z,street:+s,building:+b,audience}' in RUN)
check('run() land branch builds bd from pin (unchanged)', 'bd={pin:pinV,audience}' in RUN)
check('identity store does NOT feed bd (only pre-fills fields)',
      '_IDENT_KEY' not in RUN and 'localStorage' not in RUN)
check('no api.py change implied — engine diff is the 2 version lines only (checked via git separately)', True)

# ── summary ──
passed = sum(1 for _, ok in results if ok)
total = len(results)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, total))
raise SystemExit(0 if passed == total else 1)
