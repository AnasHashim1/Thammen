# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.134 — «نبض السوق» (S2, redesign v2): the contextual recent-deals band on the
RESULT screen + the GET /api/pulse endpoint it reads. 🟡 api.py TOUCHED (the sanctioned exception:
/logo_t.png + /api/pulse) — but VALUE-NEUTRAL: the endpoint is read-only, the valuation engine is
untouched, and nothing renders a computed number.

Honesty (ANSWERS Q11): the band is CONTEXTUAL — the frontend passes the user's OWN district +
asset_type (ev.gis_district_aname / ev.asset_type), so it shows deals from the pool behind their
number. Anonymised — date · area_m2 · price_m2 · total_price ONLY (no ref_no, no address; MoJ open
data CC BY 4.0). Empty/sparse: count 0 → band stays hidden (NEVER fabricated deals); <3 → single
count line; >=3 → cards.

E14: reads the REAL api.py + index.html + evaluate_unified.py + the security-suite source."""
import io, re
API  = io.open('api.py', encoding='utf-8').read()
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
SEC  = io.open('test_sprint_2p16p17_security.py', encoding='utf-8').read()
passed = failed = 0
def check(name, cond, msg=''):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name, ('[' + msg + ']') if msg else '')

# ── isolate the /api/pulse handler (decorator → next @app.get) ──
_ps = API.find('@app.get("/api/pulse")')
_pe = API.find('@app.get(', _ps + 10)
PULSE = API[_ps:_pe] if (_ps >= 0 and _pe > _ps) else ''
check('/api/pulse endpoint present', bool(PULSE))

# ═══ (1) backend — rate-limited GET (b66) + read-only + anonymised + value-neutral ═══
check('rate-limited (@limiter.limit)', '@limiter.limit' in PULSE)
check('carries request: Request (b66)', 'request: Request' in PULSE)
check('read-only DB open (mode=ro)', 'mode=ro' in PULSE)
check('anonymised SELECT — date/area_m2/price_m2/total_price ONLY',
      'SELECT date, area_m2, price_m2, total_price FROM transactions' in PULSE)
check('anonymised — no ref_no / municipality leaked', 'ref_no' not in PULSE and 'municipality' not in PULSE)
check('contextual key = normalize(area) + category (same pool the engine matched)',
      'normalize(area)' in PULSE and 'category' in PULSE)
check('in-memory TTL cache (_PULSE_CACHE + _PULSE_TTL)', '_PULSE_CACHE' in API and '_PULSE_TTL' in API)
check('VALUE-NEUTRAL — pulse never evaluates/computes a value',
      'evaluate' not in PULSE and 'amount' not in PULSE)
check('moj_db.normalize imported (read-only helper; engine/moj_db logic untouched)',
      'init_db, normalize' in API)

# ═══ (2) security — /api/pulse joins the rate-limited GET surface (b66 hardening) ═══
check('/api/pulse added to the security GET_ROUTES', '"/api/pulse"' in SEC)

# ═══ (3) frontend — the navy band CSS + animations (reduced-motion safe) ═══
check('.pulse-band CSS (navy result-screen band)', '.pulse-band{background:var(--primary)' in HTML)
check('gold top-border rule on the band', '.pulse-band::before' in HTML and 'linear-gradient(90deg,transparent,var(--gold)' in HTML)
check('thPulse (green dot) + thRise (card stagger) keyframes', '@keyframes thPulse' in HTML and '@keyframes thRise' in HTML)
check('animations honour reduced-motion', '.pulse-dot{animation:none}' in HTML and '.pulse-card{animation:none}' in HTML)
check('EN LTR override for the band', 'body.lang-en #rOut .pulse-band{direction:ltr}' in HTML)

# ═══ (4) frontend — _loadPulse: contextual, honest, value-neutral ═══
_ls = HTML.find('function _loadPulse(')
LP = HTML[_ls:_ls + 2600] if _ls >= 0 else ''
check('_loadPulse present', bool(LP))
check('fetches /api/pulse with area + type', "fetch('/api/pulse?area='" in LP and "'&type='" in LP)
check('contextual: called with d.district + d.asset_type', '_loadPulse(d.district,d.asset_type)' in HTML)
# b141 R6: the gate was TIGHTENED to also require hasValuation (the band must not render under a
# refusal card). Contextual district+asset_type still required; DOM-inject (not the assembly string).
check('band injected (DOM) only when hasValuation + district + asset_type exist',
      "_pb.id='pulseBand'" in HTML and 'if(hasValuation&&d.district&&d.asset_type)' in HTML
      and 'h=head+alerts+t1+secEv+secHow+secScn+secLim+_info+secNudge+foot+t3;' in HTML)
check('ANSWERS Q11: count 0 → band stays hidden (never fabricate)', 'if(!p||!p.count||p.count<1)return' in LP)
check('ANSWERS Q11: sparse (<3) → single count line, no cards', 'p.deals.length<3' in LP and 'pulse-line' in LP)
check('ANSWERS Q11: >=3 → cards grid', 'pulse-grid' in LP and 'pulse-card' in LP)
check('footer «صفقة مسجّلة في هذا الحيّ» computed from the response', 'صفقة مسجّلة في هذا الحيّ' in LP)
check('CC BY 4.0 + Ministry of Justice attribution', 'CC BY 4.0' in LP and 'وزارة العدل' in LP)
check('cards show ONLY the 4 anonymous fields (date/total/m²/m²-price)',
      'total_price' in LP and 'area_m2' in LP and 'price_m2' in LP and '_pulseDate(' in LP)
check('VALUE-NEUTRAL — _loadPulse assigns no v.amount/low/high', 'v.amount=' not in LP and 'v.low=' not in LP)
check('bilingual t() twins on the band strings',
      "t('نبض السوق','Market pulse')" in LP and "t('أحدث الصفقات المسجّلة','Latest registered deals')" in LP)

# ═══ (5) engine untouched + version marker (prefix convention) ═══
check('valuation engine untouched (no /api/pulse logic in the engine)', '/api/pulse' not in ENG and '_loadPulse' not in ENG)
check('ENGINE_VERSION present (thammen-sprint…)', 'thammen-sprint2p22p0b' in ENG)
check('SPRINT_TAG present (2.22.0b.…)', "SPRINT_TAG = '2.22.0b." in ENG)

print('\n%d passed, %d failed' % (passed, failed))
import sys; sys.exit(1 if failed else 0)
