# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.130 — cost-led short-report FACE «لماذا الرقم الأدنى» (persona-panel surgical fix).
E14: reads the REAL index.html + evaluate_unified.py.
🟢 FRONTEND / VALUE-NEUTRAL — on a COST-LED face the floor↔ceiling gap is wide (amount==floor;
e.g. 2.4M vs a 5.4M market ceiling). The terse specialist legend («الأرضية = مرتكز الكلفة … · السقف =
وسيط …») read as jargon to the owner AND left the ceiling un-qualified (mis-anchor risk). The fix
surfaces ONE plain owner line qualifying BOTH endpoints, cost-led ONLY; the terse legend now fires
for geo_full ONLY; the full «لماذا» (basisLn/neigh) stays folded in «عرض التفاصيل». Ceiling framed
price-inferred, NOT «فاخر» as fact (b100 honesty). amount/low/high/method/rule untouched; api.py untouched."""
import io, re
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
passed = failed = 0
def check(name, cond, msg=''):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name, ('[' + msg + ']') if msg else '')

# isolate showShortReport()
_ss = HTML.find('function showShortReport(d){')
_se = HTML.find('function _srCountUp(')
if _se < 0: _se = HTML.find('function _countUp(')
SR = HTML[_ss:_se] if (_ss >= 0 and _se > _ss) else ''
check('showShortReport() region isolated', bool(SR))

# 1) the cost-led gate + the new const
check('_costLead = (cs===\'cost\')', "const _costLead=(cs==='cost');" in SR)
check('_costFaceWhy const defined + gated on _costLead', "const _costFaceWhy=_costLead?t(" in SR)

# 2) the terse legend now fires for geo_full ONLY (cost-led dropped from its gate)
check('_anchorLegend gate = geo_full only (cost removed)',
      "const _anchorLegend=(ld&&ld.rule==='geo_full')?t(" in SR)
check('_anchorLegend no longer gated on cost-led',
      "_anchorLegend=(cs==='cost'||(ld&&ld.rule==='geo_full'))" not in SR)

# 3) the jargon endpoints legend string is KEPT (now for geo_full) — b92/b105 contract intact
check('terse cost-anchor legend string still present (geo_full)',
      "t('الأرضية = مرتكز الكلفة (أرض + قيمة البناء بعد الإهلاك) · السقف = وسيط صفقات السوق'" in SR)

# 4) the new plain owner line — verbatim key phrases (AR)
check('new AR line: floor = rebuild cost',
      'رقمُنا هو الأرضية (كلفةُ إعادة البناء)، لأنّ صفقات بيوتٍ مثل بيتك قليلة' in SR)
check('new AR line: ceiling = higher-priced tier',
      'والسقف شريحةٌ أعلى سعراً في منطقتك' in SR)

# 5) b100 honesty — price-inferred, NOT «فاخر» as fact
check('b100 honesty: «استدلالاً بالسعر لا معاينةً» in the new line',
      '(استدلالاً بالسعر لا معاينةً)' in SR)
check('no «فاخر»/«حديث» asserted as fact in the new line',
      'شريحةٌ أعلى سعراً في منطقتك (استدلالاً بالسعر لا معاينةً)' in SR)

# 6) the ceiling qualifier (the personas' key ask)
check('ceiling qualified: «ليس فئةَ بيتك ولا قيمةَ بيعه اليوم»',
      'ليس فئةَ بيتك ولا قيمةَ بيعه اليوم' in SR)

# 7) the EN twin
check('EN twin present (rebuild cost / higher-priced tier)',
      'the rebuild cost' in SR and 'a higher-priced tier in your area' in SR and
      'inferred from price, not inspection' in SR)

# 8) the render — the new line renders as a .tleg inside the tiers block, AFTER _anchorLegend
_rl = "if(_anchorLegend)h+='<div class=\"tleg\" dir=\"auto\">'+_anchorLegend+'</div>';"
_nl = "if(_costFaceWhy)h+='<div class=\"tleg\" dir=\"auto\">'+_costFaceWhy+'</div>';"
check('_costFaceWhy rendered as .tleg', _nl in SR)
check('_costFaceWhy rendered right after _anchorLegend', (_rl + "\n") in SR and _nl in SR
      and SR.find(_nl) > SR.find(_rl) and (SR.find(_nl) - SR.find(_rl)) < 200)

# 9) VALUE-NEUTRAL — the new code is display-only (no assignment to amount/low/high)
_seg_s = SR.find('const _costFaceWhy=')
_seg = SR[_seg_s:_seg_s+700]
check('new const does not mutate v.amount/low/high',
      ('v.amount=' not in _seg) and ('v.low=' not in _seg) and ('v.high=' not in _seg))

# 10) the FULL «لماذا» (basisLn / neigh) is NOT deleted — it stays (folded in «عرض التفاصيل»)
check('full basisLn cost explanation retained',
      'محسوبة من قيمة الأرض + قيمة البناء بعد عمره، لأن صفقات بيوتٍ مثل بيتك في المنطقة قليلة' in SR)
check('full neigh «مقارنةٌ غير منصِفة» retained',
      'ومقارنة بيتك بأسعار الشريحة الأعلى مقارنةٌ غير منصِفة' in SR)

# 11) scope: the endpoints labels stay (bracket unchanged)
check('endpoints «الأرضية السعرية»/«السقف السوقي» kept',
      "t('الأرضية السعرية','Price floor')" in SR and "t('السقف السوقي','Market ceiling')" in SR)

# 12) version bump (R6/Lesson-2: version-agnostic FORMAT checks — b131 bumped past b130)
check('ENGINE_VERSION format valid', bool(re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG)))
check('SPRINT_TAG format valid', bool(re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG)))

# 13) api.py untouched contract (this sprint touches only index.html + 2 version lines)
check('the fix is frontend-only (comment marks it)',
      "Sprint 2.22.0b.130 (persona-panel surgical fix)" in SR)

print('\n%d passed, %d failed' % (passed, failed))
import sys; sys.exit(1 if failed else 0)
