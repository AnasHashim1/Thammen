# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.113 (S7 / الجوهر — B-2 condition axis; PO-SIGNED brief). E14: the REAL
evaluate_unified._condition_stratum_lead + the real strata shape + source wiring.

🔴 Gate-2 VALUE-AFFECTING on the cost-led villa path, GUARDED: on a POSITIVE user-attested condition, a
cost-led villa leads with the matching RELIABLE market stratum (b100 price-position) instead of the
conservative cost floor — indicative + disclosed. The blind default (no attestation) keeps the cost floor
BYTE-IDENTICAL (verified live: the 5-fixture gate is byte-identical; only a positive attestation moves).

Signed guards (brief §4): positive attestation only (teardown/maintenance/None → floor); reliable stratum
(n≥10); value ≥ the informed cost floor (never below, the E25/R7 rail); cost_led only. Gemini-adjudicated
refinements (#54): C3 price-position labels (b100, not «حديثة») · C2 inspection-consequence friction ·
C1 ordinary Assumption · C4 indicative («استرشاديّ», not «beta»).
"""
import io, sys
from evaluate_unified import (_condition_stratum_lead, _S7_POSITIVE_CONDITIONS,
                              CONDITION_STRATUM_NOTE_AR, CONDITION_STRATUM_NOTE_EN)

# a realistic strata dict (Marikh shape): modern reliable n=11, luxury reliable n=15, thin land/aging.
STRATA = {'strata': {
    'land_priced':  {'n': 1,  'reliable': False, 'median_per_m2': 3670},
    'aging_stock':  {'n': 2,  'reliable': False, 'median_per_m2': 4200},
    'modern_stock': {'n': 11, 'reliable': True,  'median_per_m2': 5477},
    'luxury_new':   {'n': 15, 'reliable': True,  'median_per_m2': 8592},
}}
PLOT, FLOOR = 613.0, 2400000

_p = _f = 0
def ck(name, cond, extra=''):
    global _p, _f
    if cond: _p += 1; print(f'  ok  {name}')
    else:    _f += 1; print(f'  FAIL {name}  {extra}')

def lead(condition, is_luxury=None, plot=PLOT, strata=STRATA, floor=FLOOR):
    return _condition_stratum_lead(condition, is_luxury, plot, strata, floor)

# ── (1) BLIND / negative attestations → None (the cost floor keeps the lead, byte-identical) ──
ck('BLIND (None) → None (byte-identical floor)', lead(None) is None)
ck('teardown → None (b4 lever owns it; S7 never lifts a teardown)', lead('teardown') is None)
ck('maintenance → None (conservative — no lift without a positive signal)', lead('maintenance') is None)
ck('average/unknown → None', lead('average') is None)
ck('empty string → None', lead('') is None)

# ── (2) POSITIVE attestations → the matching RELIABLE stratum ──
r = lead('good', False)
ck('good + ordinary → modern_stock', r and r['stratum'] == 'modern_stock' and r['n'] == 11)
ck('good + ordinary value == median × plot (3,357,401)', r and r['value'] == 5477 * PLOT)
ck('good + ordinary label = the b100 PRICE-POSITION (not «حديثة»)',
   r and r['label_ar'] == 'الشريحة المتوسّطة سعراً' and r['label_en'] == 'Mid price tier')
ck('renovated + ordinary → modern_stock', (lead('renovated', False) or {}).get('stratum') == 'modern_stock')
ck('new + ordinary → modern_stock', (lead('new', False) or {}).get('stratum') == 'modern_stock')
rl = lead('good', True)
ck('good + LUXURY finish → luxury_new', rl and rl['stratum'] == 'luxury_new' and rl['n'] == 15)
ck('luxury label = «الشريحة الأعلى سعراً» / «Top price tier»',
   rl and rl['label_ar'] == 'الشريحة الأعلى سعراً' and rl['label_en'] == 'Top price tier')
ck('the positive-condition set is exactly good/renovated/new/excellent/very-good',
   _S7_POSITIVE_CONDITIONS == frozenset({'good', 'renovated', 'new', 'excellent', 'very-good', 'very_good'}))

# ── (3) GUARDS ──
ck('value < cost_floor → None (never below the informed floor — E25/R7 rail)',
   lead('good', False, floor=6000000) is None)
ck('UNRELIABLE matching stratum → None (n<10)',
   _condition_stratum_lead('good', False, PLOT,
       {'strata': {'modern_stock': {'n': 4, 'reliable': False, 'median_per_m2': 5477}}}, FLOOR) is None)
ck('missing plot → None', lead('good', False, plot=None) is None)
ck('missing/empty strata → None', lead('good', False, strata={}) is None and lead('good', False, strata=None) is None)
ck('missing cost_floor → None', lead('good', False, floor=None) is None)
ck('a stratum median of 0 → None', _condition_stratum_lead('good', False, PLOT,
       {'strata': {'modern_stock': {'n': 11, 'reliable': True, 'median_per_m2': 0}}}, FLOOR) is None)

# ── (4) the disclosed note (indicative + inspection-consequence friction + label) ──
note = CONDITION_STRATUM_NOTE_AR.format(label='الشريحة المتوسّطة سعراً', n=11, floor='2,400,000')
ck('note AR: indicative + not-inspected + friction (inspection invalidates over-claims)',
   'لم يُعايَن' in note and 'استرشادي' in note and 'غير صالحٍ عند الفحص الميدانيّ من البنوك أو المشترين' in note)
noteE = CONDITION_STRATUM_NOTE_EN.format(label='Mid price tier', n=11, floor='2,400,000')
ck('note EN twin present + friction',
   'not inspected' in noteE and 'indicative' in noteE and 'invalid under a field inspection' in noteE)

# ── (5) source wiring: the cost_led block is BRANCHED (S7 if / existing else verbatim) ──
ENG = io.open('evaluate_unified.py', encoding='utf-8').read()
ck('cost_led branches on _condition_stratum_lead',
   "_s7 = _condition_stratum_lead(" in ENG and "if _s7:" in ENG and
   "output['valuation']['low'] = _r100k(_cv20)          # cost floor = the low" in ENG)
ck('S7 sets leader/rule = condition_stratum(_led)',
   "_lead20['leader'] = 'condition_stratum'" in ENG and "_lead20['rule'] = 'condition_stratum_led'" in ENG)
ck('the EXISTING cost_led body is preserved verbatim in the else (byte-identical blind default)',
   "else:\n                                    # F3(b) — the COST leads: range [cost … market-muted], MUC high." in ENG and
   "output['valuation']['range_is_headline'] = True" in ENG)
ck('S7 recomputes the decomposition + floor on the new central (ISS-A07 coherence)',
   "_decompS7 = _decompose_value(" in ENG and "_vfS7 = _villa_value_floor(" in ENG)

# ── (6) frontend: the neutral opt-in + friction note on the refine screen ──
HTML = io.open('index.html', encoding='utf-8').read()
ck('refine friction note present (neutral opt-in, not a dark pattern)',
   '◆ حالتك تُغيّر الرقم:' in HTML and 'يبقى <strong>استرشاديّاً</strong>' in HTML and
   'غير صالحٍ عند الفحص الميدانيّ من البنوك أو المشترين' in HTML)
ck('the FULL-report leadership note renders generically (pick) — no cost-led-only gate blocks it',
   "pick(v.leadership,'note')" in HTML)

# ── (6b) the engine emits the stratum label for the short-report card basis ──
ck('leadership carries stratum_label_ar/en (b100 price-position) for the card',
   "_lead20['stratum_label_ar'] = _s7['label_ar']" in ENG and "_lead20['stratum_label_en'] = _s7['label_en']" in ENG)

# ── (6c) short-report HONESTY: a condition-led number must NOT claim a matched-sales basis ──
ck('short report: _isCondLead guard defined + reads stratum_label',
   "const _isCondLead=!!(ld&&ld.rule==='condition_stratum_led')" in HTML and "pick(ld,'stratum_label')" in HTML)
ck('short report basisLn: the S7 attestation basis OVERRIDES the market «matched sales» claim',
   "if(_isCondLead)basisLn=t('بناءً على إقرارك بحالة العقار" in HTML and
   "else if(cs==='cost')basisLn=" in HTML and                 # the original branches still present
   "else if(cs==='market')basisLn=" in HTML)
ck('short report §١ neigh: the S7 attestation paragraph OVERRIDES the «N مطابقة، وسيطها مرجعك» claim',
   "if(_isCondLead){\n    neigh=t('أقررتَ بحالة بيتك، فقِيسَ الرقم على شريحته السوقيّة" in HTML and
   "}else if(cs==='cost'){" in HTML and                        # original neigh branches intact (byte-identical for non-S7)
   "صفقات مثل بيتك كافية وواضحة: " in HTML)
ck('short report: the stale cost-led «reviewed, didn\'t lead» proof rows are suppressed on a condition-led card',
   "if(_kc&&_kc.rows&&_kc.rows.length&&!_isCondLead){" in HTML)

# ── (7) version ──
ck('engine is a valid b-series tag (no exact pin — Lesson-2)',
   "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print(f'\nb113 (S7): {_p} passed, {_f} failed')
sys.exit(1 if _f else 0)
