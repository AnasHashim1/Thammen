# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.94 «تنظيف الشارات + ترقية الدقّة» — isolated tests (E14: reads the REAL files).

Gemini r7 #2: the 5-second face shows ONLY algorithm-known chips; unknown specs
(«غير محدّد» ×3) MOVE off the face into the «ترقية دقّة المؤشّر» block (below the
legal line, before the fold) — an accuracy-upgrade invitation into the EXISTING
refine screen (no future-feature promise — the lawyer/linguist adjudication).
VALUE-INVARIANT (chip gating + one display block).
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML = open('index.html', encoding='utf-8').read()
ENG  = open('evaluate_unified.py', encoding='utf-8').read()

i = HTML.index('function showShortReport(d){')
j = HTML.find('\nfunction ', i + 10)
SR = HTML[i:j if j != -1 else len(HTML)]
_nc = '\n'.join(l for l in SR.splitlines() if not l.strip().startswith('//'))

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('PASS |', name)
    else:    failed += 1; print('FAIL |', name)

# ── chips: known-only on the face ──
check('unknown-spec chips REMOVED from the rendered face (no «غير محدّد» chip values)',
      "t('غير محدّد','not set')" not in _nc and "t('غير محدّدة','not set')" not in _nc)
check('BUA chip gated on cost.bua_m2', 'if(cost.bua_m2)chips+=_chip(' in SR)
check('age chip gated on _ageY (b73 floor-tooltip preserved)',
      'if(_ageY)chips+=_chip(' in SR and 'قد يكون أقدم' in SR)
check('finish chip gated on a KNOWN finish', 'if(_ui.is_luxury||_ui.condition)chips+=_chip(' in SR)
check('annexes chip gated on known annexes', 'if(_anx.length)chips+=_chip(' in SR)

# ── the upgrade block ──
check('_srMiss collector declared', 'const _srMiss=[];' in SR)
check('each unknown pushes into _srMiss', SR.count('_srMiss.push(') == 4)
check('upgrade block «ترقية دقّة المؤشّر» rendered, gated on missing',
      'if(_srMiss.length){' in SR and "t('ترقية دقّة المؤشّر'" in SR)
check('honest copy — «لم تدخل في هذا الرقم الآلي» (no feature promise)',
      "t('مواصفات لم تدخل في هذا الرقم الآلي: '" in SR and 'قريباً' not in _nc and 'التصحيح الذاتي' not in _nc)
check('CTA opens the EXISTING refine screen', 'class="upg-btn" onclick="go(\\\'refine\\\')"' in SR)
check('placement: after the legal line, before the fold',
      SR.index('thmr-legalz') < SR.index('thmr-upg') < SR.index('id="srFold"'))
check('.thmr-upg CSS present', '.thmr-upg{' in HTML and '.thmr-upg .upg-btn{' in HTML)

# ── value-invariance ──
mults = re.findall(r'v\.amount\s*\*\s*([0-9.]+)', SR)
check('value-math still = ONLY the 3 disclosed conventions', sorted(set(mults)) == ['0.90', '1.10', '1.30'])
check('no assignment into v.amount/low/high', not re.search(r'v\.(amount|low|high)\s*=[^=]', SR))

# ── version ──
check('ENGINE_VERSION b-series format (R6)', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+b\d+-", ENG) is not None)

print(f'\n{passed}/{passed+failed} PASS' + ('' if failed == 0 else f' — {failed} FAIL'))
sys.exit(1 if failed else 0)
