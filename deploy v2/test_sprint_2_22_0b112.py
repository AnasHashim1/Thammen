# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.112 — Gemini r-consult A1+A2 disclosure refinements. E14: reads the REAL index.html.
🟢 FRONTEND copy / VALUE-INVARIANT — two copy refinements the Gemini RICS/UX consult recommended (both runs
concurred, CC-adjudicated #54); no value/method/rule change; api.py untouched.
  A1: soften the S1 R-3 data-age line — «عدم اليقين الجوهري» (VPGA 10 material uncertainty) is a crisis
      term, over-invoked for routine staleness; keep the FACT (no explicit time adjustment), drop the scary
      tie, state the honest consequence («قد تتأثّر الدقّة بتقلّبات السوق الأخيرة»).
  A2: trim the S3 assumptions-register RCN LADDER (the 5 exact QAR coefficients = the model's calibration/IP)
      → methodology + source + range («من العاديّ إلى الفاخر»); VPS 2 requires the METHOD, not the exact
      coefficients. The per-property APPLIED rate (the cost-breakdown arithmetic) is KEPT (the PO's 56/565/21
      transparency ask)."""
import io
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
_s = HTML.find('function showReport(d){'); _e = HTML.find('function printReportA4(')
if _e < 0: _e = HTML.find('function showShortReport(d){')
REP = HTML[_s:_e] if (_s >= 0 and _e > _s) else ''
passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

check('showReport() isolated', bool(REP))

# ── A1: the softened R-3 data-age line ──
check('A1 softened R-3 present AR + EN (no time adjustment kept)',
      'دون تعديلٍ زمنيّ صريح على الوسيط' in REP and
      'without an explicit time adjustment to the median' in REP)
check('A1 honest consequence stated (recent market movements)',
      'قد تتأثّر الدقّة بتقلّبات السوق الأخيرة' in REP and
      'accuracy may be affected by recent market movements' in REP)
check('A1 the over-scary VPGA-10 tie is GONE from this line',
      'سببٌ مُعلَن لعدم اليقين الجوهري' not in REP and 'a stated reason for material uncertainty' not in REP)
check('A1 still states the 24/36-month window + still raw_land-scoped-out',
      '٢٤ شهراً' in REP and '٣٦' in REP and "if(d.asset_type!=='raw_land')cData+=" in REP)

# ── A2: the trimmed RCN ladder ──
check('A2 RCN reveals METHODOLOGY + source + range (not the exact coefficients)',
      'تُقدَّر وفق متوسّط أسعار البناء المحليّة السائدة، بسُلَّمٍ يتدرّج من التشطيب العاديّ إلى الفاخر' in REP and
      'estimated from prevailing local construction-cost indices, on a ladder rising from ordinary to luxury finish' in REP)
check('A2 the exact 5-level ladder coefficients are GONE (IP protected)',
      'شِلّ ١٬٢٠٠ · عاديّ ٢٬٢٠٠' not in REP and 'shell 1,200 · ordinary 2,200' not in REP and
      'فاخر ٣٬٥٠٠ ر.ق/م²' not in REP)
check('A2 the APPLIED finish level is still shown (per-property, not the ladder)',
      "_finMap[_aC.finish]" in REP and 'المُطبَّق هنا: ' in REP)
check('A2 the per-property applied RCN rate (cost-breakdown arithmetic) is KEPT (the PO 56/565/21 ask)',
      "BUA '+_cR.bua_m2+' × '+fmt(_cR.rcn_qar_per_m2)+' × '+_cR.retention" in REP)

# ── VALUE-INVARIANT + version ──
check('the register header + standing/cost lines otherwise intact (only the RCN line reworded)',
      'الافتراضات والافتراضات الخاصّة (&lrm;RICS VPS 2 / IVS 102&lrm;)' in REP and
      'خطٌّ مستقيمٌ على عمرٍ نافعٍ ٥٠ سنة' in REP and 'يُفترَض طابقان' in REP)
check('S1 basis-of-value + C-4 + C-7 untouched by b112',
      'أساس القيمة: القيمة السوقية (&lrm;RICS VPS 2 / IVS 102&lrm;)' in REP and
      'هو التعبير الكمّي عن عدم اليقين في هذا التقييم' in REP)
check('EN reveal + b54 locked identity intact', 'var EN_ENABLED=true;' in HTML and 'تقييم سوقيّ آليّ' in HTML)
check('engine is a valid b-series tag (no exact pin — Lesson-2)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb112:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
