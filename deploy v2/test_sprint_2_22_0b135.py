# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.135 «الموبايل + condition_led» (S9, redesign v2) — isolated test (E14).

🟢 FRONTEND-ONLY / VALUE-NEUTRAL. Two halves:
  (A) condition_led leadership CARD on the RESULT screen (b113/S7 honesty ported from the short report):
      - _s4bHow renders a «بطاقة القيادة بالحالة المُصرَّحة» when leadership.leader==='condition_stratum'
      - _s4bEvidence stops MISSTATING the basis: a condition_led number is NOT «قاد التقديرَ منهجُ الكلفة»
      - the genuine cost-led frame «قاد التقديرَ منهجُ الكلفة» is PRESERVED (compliance/methodology intact)
      - the engine's signed honesty note_ar STILL renders (.rs-narr, b125:2504)
  (B) mobile hardening: comparable deals TABLE → CARDS at <=560px + >=44px touch targets.

Verifies the frontend↔engine field contract (engine emits X, frontend reads X — self-contained, no live
fixture needed), value-neutrality (no assignment to amount/low/high in the added JS), unchanged builder
signatures (so the b125 call-site pins hold), and the b125 mobile-grid pin preservation.
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

# region of the two result-screen builders we touched
HOW = _slice(HTML, 'function _s4bHow(', 'function _s4bScenarios(')
EVID = _slice(HTML, 'function _s4bEvidence(', 'function _s4bHow(')

print('\n== version bump ==')
check("ENGINE_VERSION -> b135", "thammen-sprint2p22p0b135-mobile-condition-led" in ENG)
check("SPRINT_TAG -> 2.22.0b.135", "SPRINT_TAG = '2.22.0b.135'" in ENG)

print('\n== (A) condition_led leadership card in _s4bHow ==')
check("condLead gate on leader==='condition_stratum'", "const condLead=(leader==='condition_stratum')" in HOW)
check("card is gated (if(condLead){)", "if(condLead){" in HOW)
check("renders the .rs-cond verdict card", 'class="rs-cond"' in HOW)
check("«حالة مُصرَّحة» flag", "حالة مُصرَّحة" in HOW and "'Declared condition'" in HOW)
check("«الأساس المعتمد» basis tag", "الأساس المعتمد" in HOW)
check("presents the BROADCAST amount (fmt(v.amount)) — value-neutral", "<div class=\"cv\">'+fmt(v.amount)" in HOW)
check("before/after uses ld.cost_floor", "ld.cost_floor!=null" in HOW and "قبل: " in HOW)
check("«بعد تصريح» / declared condition word", "بعد تصريح " in HOW and "بعد إقرارك بالحالة" in HOW)
check("stratum strip «مبنيٌّ على حالتك المُصرَّحة»", "حالتك المُصرَّحة" in HOW and "مبنيٌّ على " in HOW)
check("stratum strip reads pick(ld,'stratum_label') + ld.stratum_n", "pick(ld,'stratum_label')" in HOW and "ld.stratum_n" in HOW)
check("condition word map covers the S7 positive set (good/renovated/new)", all(k in HOW for k in ('good:', 'renovated:', "'new':")))

print('\n== (A) _s4bEvidence honest reframe (R-B) ==')
check("_cl gate on rule==='condition_stratum_led'", "const _cl=(v.leadership||{}).rule==='condition_stratum_led'" in EVID)
check("condition branch BEFORE the cost-led branch (if(considered&&_cl))", "if(considered&&_cl){" in EVID)
# the honest condition frame + it must NOT claim the cost approach led
cond_frame = _slice(EVID, "if(considered&&_cl){", "}else if(considered){")
check("condition frame = honest «لم تقُد رقمَك مباشرةً»", "لم تقُد رقمَك مباشرةً" in cond_frame)
check("condition frame discloses «إقرارك بحالة العقار» + «لم يُعايَن ميدانياً»", "إقرارك بحالة العقار" in cond_frame and "لم يُعايَن ميدانياً" in cond_frame)
check("condition frame does NOT claim «قاد التقديرَ منهجُ الكلفة» (no misstatement)", "قاد التقديرَ منهجُ الكلفة" not in cond_frame)

print('\n== compliance / methodology PRESERVED (zero weakened) ==')
check("genuine cost-led frame «قاد التقديرَ منهجُ الكلفة (DRC)» kept", "قاد التقديرَ منهجُ الكلفة (DRC)" in EVID)
check("b125 pin «لم تقُد الرقم» (cost-led considered) kept", "لم تقُد الرقم" in EVID)
check("cost-led «فشل حدّ الموثوقيّة» dispersion why kept", "فشل حدّ الموثوقيّة" in EVID)
check("signed honesty note_ar still renders (.rs-narr, b125:2504)", "if(ld.note_ar)h+='<div class=\"rs-narr\">" in HOW)
check("market-led «قرّر رقمك» frame kept", "قرّرت رقمك" in EVID or "قرّر رقمك" in EVID)

print('\n== frontend<->engine field contract ==')
check("engine emits rule='condition_stratum_led'", "_lead20['rule'] = 'condition_stratum_led'" in ENG)
check("engine emits leader='condition_stratum'", "_lead20['leader'] = 'condition_stratum'" in ENG)
check("engine emits stratum_label_ar (read via pick 'stratum_label')", "_lead20['stratum_label_ar']" in ENG)
check("engine emits stratum_n", "_lead20['stratum_n']" in ENG)
check("engine emits cost_floor", "_lead20['cost_floor']" in ENG)
check("engine emits note_ar", "_lead20['note_ar']" in ENG)

print('\n== builder signatures UNCHANGED (b125 call-site pins hold) ==')
check("_s4bEvidence(d,v) def unchanged", "function _s4bEvidence(d,v){" in HTML)
check("_s4bHow(d,v,acc,how,dense) def unchanged", "function _s4bHow(d,v,acc,how,dense){" in HTML)
check("call site secEv+=_s4bEvidence(d,v)", "secEv+=_s4bEvidence(d,v)" in HTML)
check("call site secHow+=_s4bHow(d,v,acc,how,_dense)", "secHow+=_s4bHow(d,v,acc,how,_dense)" in HTML)

print('\n== (B) mobile hardening ==')
mob = _slice(HTML, '@media(max-width:560px){', '\nbody.lang-en #rOut .rs-viz')
check("comparables head hidden on mobile", ".rs-ctab .head{display:none}" in mob)
check("body row -> 2x2 card (grid-template-areas 'd p'/'a m')", "grid-template-areas:'d p' 'a m'" in mob)
check("date+area grid-areas d/a", ".rs-ctab .body .d{grid-area:d" in mob and ".rs-ctab .body .a{grid-area:a" in mob)
check("price+ppm2 grid-areas p/m", ".rs-ctab .body .p{grid-area:p" in mob and ".rs-ctab .body .m{grid-area:m" in mob)
check(">=44px touch: sticky-bar buttons", "min-height:44px" in mob and ".rs-bar button{" in mob)
check(">=44px touch: methodology-fold summary", ".rs-mfold>summary{min-height:44px" in mob)
check("condition card sized down on mobile", ".rs-cond .cv{font-size:1.6rem}" in mob)
check("old squeezed-grid override REMOVED", "grid-template-columns:1.1fr .8fr 1.1fr .9fr" not in HTML)
check("b125 pin preserved: .rs-stack{grid-template-columns:1fr", ".rs-stack{grid-template-columns:1fr" in HTML and "max-width:560px" in HTML)

print('\n== condition-led card CSS ==')
check(".rs-cond{ card style present", ".rs-cond{" in HTML)
check(".rs-cond flag = navy/gold chip (tokens)", ".rs-cond .ch .flag{" in HTML and "color:var(--gold)" in HTML)
check(".rs-cond .cstrip navy leadership strip", ".rs-cond .cstrip{" in HTML and "background:var(--primary)" in HTML)
check("uses tokens only (no raw #16324F navy literal in .rs-cond)", "#16324F" not in _slice(HTML, '.rs-cond{', '.rs-mfold{'))

print('\n== value-neutral / EN twins ==')
check("no assignment to v.amount/low/high in _s4bHow", not re.search(r'v\.(amount|low|high)\s*=', HOW))
check("no assignment to v.amount/low/high in _s4bEvidence", not re.search(r'v\.(amount|low|high)\s*=', EVID))
check("new condition card strings are bilingual (t(ar,en))", "t('حالة مُصرَّحة','Declared condition')" in HOW)
check("new evidence frame is bilingual", "t('هذه صفقاتُ السوق في منطقتك — لم تقُد رقمَك مباشرةً؛" in EVID)

print('\n---------------------------------------------')
print('  b135 result: %d passed, %d failed' % (_p, _f))
print('---------------------------------------------')
sys.exit(1 if _f else 0)
