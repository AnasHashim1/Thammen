# -*- coding: utf-8 -*-
# Sprint 2.22.0b.37 — DEF-UX9: surface the DRC cost MECHANICS (BUA / RCN / retention) on the result screen.
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only). Reads the REAL index.html
# (E14 / Rule #40 for the frontend lane) + asserts the engine version bump.
#
# What this verifies (ISSUES_LOG §4ب-2 DEF-UX9 «كشف BUA/RCN/معامل الاحتفاظ» — المهندس·المثمّن):
#   The engine ALREADY broadcasts value_stack.cost.{bua_m2, rcn_qar_per_m2, retention, building_value,
#   land_floor, assumptions_ar} (measured live on 54/541/6). They were displayed ONLY on the full/short
#   report (showReport / showShortReport), NOT on the result screen. b37 adds ONE appraiser-detail line
#   inside the «🔍 كيف وصلنا لهذا الرقم؟» accordion (the `how` buffer — b34 density-open for investor/
#   valuer): «🔧 آليّة الكلفة (نهج DRC): … BUA × كلفة الإحلال × معامل الاحتفاظ → البناء المُهلَك + الأرض»
#   + the broadcast assumptions_ar. Numbers in dir=ltr islands (Rule #25). Display-only → value-invariant.
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# isolate show() so the result-screen assertions are scoped to the results renderer (not the report builders).
_sh_start = HTML.index('function show(d){')
_sh_end = HTML.index('\nfunction pctFmt(', _sh_start)
SHOW = HTML[_sh_start:_sh_end]

# isolate the new DEF-UX9 block (the cost-mechanics line) — it lives right after the cost-VALUE line.
_b37_idx = SHOW.find('Sprint 2.22.0b.37 (DEF-UX9)')
B37 = SHOW[_b37_idx:_b37_idx + 1400] if _b37_idx >= 0 else ''

# ── 0. engine version bump (frontend-only → version strings are the only engine diff) ──
check('ENGINE_VERSION → b37-cost-mechanics-display', "thammen-sprint2p22p0b37-cost-mechanics-display" in ENG)
check('SPRINT_TAG → 2.22.0b.37', "'2.22.0b.37'" in ENG)
check('no stale b36 engine tag left', "sprint2p22p0b36-honest-apt-refusal" not in ENG)

# ── 1. the DEF-UX9 block exists and is gated on the three broadcast fields being present ──
check('b37 cost-mechanics block present in show()', _b37_idx >= 0)
check('gated on bua_m2 && rcn_qar_per_m2 && retention!=null (only when DRC computed them)',
      re.search(r"if\(_vc\.bua_m2&&_vc\.rcn_qar_per_m2&&_vc\.retention!=null\)\{", SHOW) is not None)
check('reads the cost block once via _vc = v.value_stack.cost (DRY)',
      "const _vc=v.value_stack.cost;" in SHOW)

# ── 2. the line composes the three mechanics + depreciated building + land, from broadcast fields ──
check('line header «🔧 آليّة الكلفة (نهج DRC)»', '🔧 آليّة الكلفة (نهج DRC):' in B37)
check('surfaces BUA (مساحة البناء BUA … _vc.bua_m2)', 'مساحة البناء BUA' in B37 and "'+_vc.bua_m2+'" in B37)
check('surfaces RCN (كلفة الإحلال … fmt(_vc.rcn_qar_per_m2))', 'كلفة الإحلال' in B37 and "fmt(_vc.rcn_qar_per_m2)" in B37)
check('surfaces retention (معامل الاحتفاظ … _vc.retention)', 'معامل الاحتفاظ' in B37 and "'+_vc.retention+'" in B37)
check('surfaces depreciated building (البناء المُهلَك … fmt(_vc.building_value))',
      'البناء المُهلَك' in B37 and "fmt(_vc.building_value)" in B37)
check('surfaces land (الأرض … fmt(_vc.land_floor))', 'الأرض' in B37 and "fmt(_vc.land_floor)" in B37)
check('appends the BROADCAST assumptions_ar (no authored copy)',
      "if(_vc.assumptions_ar)how+=" in B37 and "_vc.assumptions_ar" in B37)

# ── 3. bidi: the Latin/decimal tokens (bua, retention) are wrapped in dir=ltr islands (Rule #25) ──
check('bua_m2 in a dir=ltr island', re.search(r'<span dir="ltr">\'\+_vc\.bua_m2\+\'</span>', B37) is not None)
check('retention in a dir=ltr island (the 0.5 decimal that bidi-reverses)',
      re.search(r'<span dir="ltr">\'\+_vc\.retention\+\'</span>', B37) is not None)

# ── 4. placement — inside the «كيف وصلنا» accordion (the `how` buffer), NOT TIER-1 ──
check('the new line appends to the `how` buffer (the «كيف وصلنا» accordion), not t1',
      "how+='<div class=\"rn\" style=\"margin-top:4px;font-size:.72rem;color:var(--muted)\">🔧 آليّة الكلفة" in SHOW)
# the cost-VALUE line that precedes it is preserved (the 🏗️ label line)
check('the original cost-value 🏗️ line is preserved',
      "🏗️ '+_vc.label_ar+': '+fmt(_vc.value)+' ر.ق — '+_vc.sub_ar" in SHOW)
# the unavailable-reason else-branch still chains
check('the cost-unavailable else-branch still chains (else if … unavailable_reason_ar)',
      "else if(v.value_stack&&v.value_stack.cost&&v.value_stack.cost.unavailable_reason_ar)" in SHOW)

# ── 5. value-invariance + frontend-only guards ──
check('no v.amount / low / high mutation in show()', not re.search(r'v\.(amount|low|high)\s*=[^=]', SHOW))
check('reads broadcast value_stack.cost only — no new engine field invented',
      "_vc.bua_m2" in SHOW and "_vc.rcn_qar_per_m2" in SHOW and "_vc.retention" in SHOW)
# the report + short-report BUA rows (the DRY siblings) are UNTOUCHED — still present in the file
check('report DEF-12 depreciated-building BUA row still present (showReport untouched)',
      re.search(r"البناء المُهلَك'\+\(\(_cR\.bua_m2&&_cR\.rcn_qar_per_m2&&_cR\.retention!=null\)", HTML) is not None)
check('short-report «البناء بعد العمر» BUA row still present (showShortReport untouched)',
      'البناء بعد العمر' in HTML and "cost.bua_m2&&cost.rcn_qar_per_m2&&cost.retention!=null" in HTML)

# ── summary ──
passed = sum(1 for _, ok in results if ok)
total = len(results)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, total))
raise SystemExit(0 if passed == total else 1)
