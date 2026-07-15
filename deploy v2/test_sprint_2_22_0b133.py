# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.133 — «التحسين» (S6 split 2/2; input was b132) redesign v2: the REFINE screen
(#refineScreen) v2 pass — 🟢 FRONTEND / VALUE-NEUTRAL (api.py + valuation engine untouched; only the
2 version lines bumped).

Two things ship: (1) the honesty adds — the qualitative range promise (ANSWERS #13: «±8%» never
existed; the numeric range appears only AFTER recompute, from the real field) + a closing
indicative-estimate line; (2) the v2 visual elevation (the refine card → .ent-card).

R-B / R-E landmines (the handoff's own traps): the mock shows a 3-chip condition + an age SLIDER.
- condition MUST keep all 5 engine values (new/good/renovated/maintenance/**teardown** «آيل للسقوط»,
  pinned by b4) — dropping any changes the value (teardown → land-floor).
- buildingAge MUST stay an OPTIONAL input, never a slider (a slider always has a position → it would
  fabricate an age, breaking «اترك ما لا تعرفه فارغاً»).
Both are the honest AND the pinned-required choice. This test FAILS if either regresses, or if any
pinned refine structure (the 3 tagged groups, towerRentSection, the b113 friction note, «المرحلة 2»,
thammenReEvalGeometry) is weakened.

E14: reads the REAL index.html + evaluate_unified.py."""
import io, re
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
passed = failed = 0
def check(name, cond, msg=''):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name, ('[' + msg + ']') if msg else '')

# ── isolate the REFINE screen (#refineScreen → #confirmScreen) ──
_rs = HTML.find('id="refineScreen"')
_re = HTML.find('id="confirmScreen"')
REF = HTML[_rs:_re] if (_rs >= 0 and _re > _rs) else ''
check('#refineScreen region isolated', bool(REF))

# ═══ (1) honesty adds — the qualitative promise + the closing line ═══
check('qualitative range promise strip (.ent-promise) present', 'class="ent-promise"' in REF)
check('promise copy (ANSWERS #13) VERBATIM',
      'كلّما أضفت تفصيلاً، ضاق النطاق وارتفعت الثقة. النطاق المحدَّث يظهر بعد إعادة الحساب.' in REF)
check('promise bilingual', 'data-en="Every detail you add narrows the range' in REF)
check('closing indicative-estimate line (.ent-fine) present', 'class="ent-fine"' in REF)
check('closing line VERBATIM',
      'تبقى النتيجة تقديراً استرشاديّاً — التفاصيل تحسّن دقّته لا تجعله تقييماً معتمداً.' in REF)
check('closing line bilingual', 'data-en="The result stays an indicative estimate' in REF)
# no invented number (the whole point of ANSWERS #13) — check VISIBLE content: the design-rationale
# comment legitimately names «±8%» to record that it was never shipped, so strip HTML comments first.
_vis = re.sub(r'<!--.*?-->', '', REF, flags=re.S)
check('NO invented «±8%» / «٨٪» in the refine screen (visible content)',
      '٨٪' not in _vis and '±8' not in _vis and '8%' not in _vis)

# ═══ (2) R-B/R-E landmine 1 — condition keeps ALL 5 engine values ═══
for val in ['new', 'good', 'renovated', 'maintenance', 'teardown']:
    check('condition value kept: ' + val, ('value="%s"' % val) in REF)
check('condition teardown label «آيل للسقوط» kept (b4-pinned, value-relevant)', 'آيل للسقوط' in REF)
check('condition is still the 5-option <select id="condition"> (not collapsed to chips)',
      re.search(r'<select id="condition">', REF) is not None)

# ═══ (3) R-B/R-E landmine 2 — buildingAge stays an OPTIONAL input, never a slider ═══
check('buildingAge is an optional number input', 'type="number" id="buildingAge"' in REF)
check('buildingAge is NOT a slider (no type=range anywhere in refine)', 'type="range"' not in REF)
check('buildingAge «حدٌّ أدنى» honesty note kept',
      'العمر المسجَّل في النظام حدٌّ أدنى' in REF)

# ═══ (4) PINNED STRUCTURE preserved (b27 / b54 / b113 / b29 / b2p1) ═══
check('3 tagged thmr-grp groups kept', REF.count('class="thmr-grp"') + REF.count('thmr-grp" open') >= 3)
for tag in ['يحرّك التقييم', 'يدقّق مرتكز التكلفة', 'اختياري للإثراء']:
    check('group tag kept: ' + tag, tag in REF)
check('towerRentSection kept (outside the groups)', 'id="towerRentSection"' in REF)
check('b113 friction note «حالتك تُغيّر الرقم» VERBATIM', 'حالتك تُغيّر الرقم' in REF)
check('ftitle «المرحلة 2» kept (b54)', 'المرحلة 2' in REF)
check('re-eval handler kept (thammenReEvalGeometry / refineBtn)',
      'thammenReEvalGeometry()' in REF and 'id="refineBtn"' in REF)
for fid in ['floors', 'basement', 'penthouse', 'annexes', 'externalMajlis', 'footprintM2',
            'buildingAge', 'condition', 'isLuxury', 'rentalIncome', 'potentialRental',
            'askingPrice', 'unitCount', 'avgRentPerUnit']:
    check('refine field id kept: ' + fid, ('id="%s"' % fid) in REF)

# ═══ (5) v2 elevation + scoped CSS ═══
check('refine card elevated to .ent-card', 'class="ent-card"' in REF)
check('.ent-promise + .ent-fine CSS defined', '.ent-promise{' in HTML and '.ent-fine{' in HTML)

# ═══ (6) VALUE-NEUTRALITY — refine screen computes nothing; engine/api untouched ═══
check('refine markup assigns no value', 'v.amount=' not in REF and 'v.low=' not in REF)
# b134: version-pin relaxed to the b129/b130 prefix convention (superseded when b134 bumped SPRINT_TAG;
# the b133 refine guards above are what this test protects — the version string is just the deploy tag).
check('ENGINE_VERSION present (thammen-sprint…)', 'thammen-sprint2p22p0b' in ENG)
check('SPRINT_TAG present (2.22.0b.…)', "SPRINT_TAG = '2.22.0b." in ENG)

print('\n%d passed, %d failed' % (passed, failed))
import sys; sys.exit(1 if failed else 0)
