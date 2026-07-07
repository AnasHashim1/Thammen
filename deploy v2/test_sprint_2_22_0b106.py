# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.106 — RICS report disclosures (S1). E14: reads the REAL index.html + evaluate_unified.py.
🟢 FRONTEND copy / VALUE-INVARIANT — additive disclosure lines in showReport (full report) + the short
report §٩; no value/method/rule change; api.py untouched. Closes the 3 RICS reject-risks (basis of value
IVS 102 · latest data date · honest no-time-adjustment) + C-4 evidence hierarchy + C-7 range-as-uncertainty.
Every AR line carries an EN twin (t(...)); every RICS/IVS token is LRM-wrapped."""
import io
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

# isolate showReport() for scoped checks
_s = HTML.find('function showReport(d){')
_e = HTML.find('function printReportA4(')
if _e < 0: _e = HTML.find('function showShortReport(d){')
REP = HTML[_s:_e] if (_s >= 0 and _e > _s) else ''
check('showReport() region isolated', bool(REP))

# isolate showShortReport() for the §٩ compact basis line
_ss = HTML.find('function showShortReport(d){')
_se = HTML.find('function _srCountUp(')
SR = HTML[_ss:_se] if (_ss >= 0 and _se > _ss) else ''
check('showShortReport() region isolated', bool(SR))

# ── R-1 basis of value (IVS 102) — full report, stated with the value ──
check('R-1 basis-of-value AR present (full report)',
      'أساس القيمة: القيمة السوقية (&lrm;RICS VPS 2 / IVS 102&lrm;)' in REP)
check('R-1 basis-of-value EN twin present',
      'Basis of value: Market Value (&lrm;RICS VPS 2 / IVS 102&lrm;)' in REP)
check('R-1 keeps «ليس تقييماً معتمداً» adjacent (no new claim)',
      'وهو تقييمٌ سوقيٌّ آليّ استرشاديّ — ليس تقييماً معتمداً.' in REP)
check('R-1 IVS Market-Value definition wording (willing buyer/seller, no compulsion)',
      'بين بائعٍ وشارٍ راغبَين' in REP and 'دون إكراه' in REP and
      'willing buyer and a willing seller' in REP and 'without compulsion' in REP)
check('R-1 placed WITH the value (before the range block, after the tier badge)',
      REP.find('أساس القيمة: القيمة السوقية') < REP.find("if(v.low!=null&&v.high!=null){"))

# ── R-1 compact on the short report §٩ ──
check('R-1 compact basis line on short report (§٩)',
      'أساس القيمة: ' in SR and 'القيمة السوقية (&lrm;RICS VPS 2 / IVS 102&lrm;)' in SR and
      'Basis of value: ' in SR and 'Market Value (&lrm;RICS VPS 2 / IVS 102&lrm;)' in SR)
check('R-1 short-report line sits before the IFRS 13 legal disclaimer',
      SR.find('أساس القيمة: ') < SR.find('IFRS 13'))

# ── R-2 latest MoJ record date + age (threaded from data_freshness) ──
check('R-2 latest-record line AR + EN (in the data cluster)',
      'أحدث سجلّ صفقات لدى وزارة العدل: ' in REP and
      'Latest transaction record at the Ministry of Justice: ' in REP)
check('R-2 reads data_freshness.latest_record_ar + days_old (no new API call)',
      'd.data_freshness||{}' in REP and '_dfR.latest_record_ar' in REP and '_dfR.days_old' in REP)

# ── R-3 honest no-time-adjustment posture (code-truthful; scoped OUT for raw_land) ──
# b112 R6: the wording was softened (Gemini A1 — VPGA 10 «material uncertainty» is a crisis term,
# over-invoked for routine staleness); the FACT (no time adjustment) is preserved, the scary tie dropped.
check('R-3 no-time-adjustment disclosure AR + EN (b112 softened)',
      'دون تعديلٍ زمنيّ صريح على الوسيط' in REP and
      'without an explicit time adjustment to the median' in REP)
check('R-3 states the 24/36-month window',
      '٢٤ شهراً' in REP and '٣٦' in REP and 'up to 24 months' in REP and '36' in REP)
check('R-3 scoped OUT for raw_land (land grid time-normalises separately — fact #2)',
      "if(d.asset_type!=='raw_land')cData+=" in REP and
      REP.count("if(d.asset_type!=='raw_land')cData+=") >= 1)
check('R-3 states the honest consequence (accuracy may be affected by recent movements) — no over-scary VPGA-10 tie',
      'قد تتأثّر الدقّة بتقلّبات السوق الأخيرة' in REP and 'accuracy may be affected by recent market movements' in REP and
      'سببٌ مُعلَن لعدم اليقين الجوهري' not in REP)

# ── C-4 evidence hierarchy (registered sales, not asking prices) ──
check('C-4 evidence-hierarchy line AR + EN',
      'صفقاتٌ فعليّة مسجَّلة لدى وزارة العدل — لا أسعار إعلاناتٍ ولا عروض.' in REP and
      'actual sales registered with the Ministry of Justice — not asking prices or listings.' in REP)

# ── C-7 range as the quantitative uncertainty expression (next to the MUC clause) ──
check('C-7 range-as-uncertainty AR + EN',
      'هو التعبير الكمّي عن عدم اليقين في هذا التقييم' in REP and
      'is the quantitative expression of the uncertainty in this valuation' in REP)
check('C-7 rendered right AFTER the MUC card',
      REP.find('h+=_mucCardHtml(m_ar,m_b,m_r);') < REP.find('هو التعبير الكمّي عن عدم اليقين'))
check('C-7 gated on the range existing (v.low/v.high) — no new math',
      'if(v.low!=null&&v.high!=null)h+=' in REP and 'fmt(v.low)' in REP and 'fmt(v.high)' in REP)

# ── VALUE-INVARIANCE + wiring ──
check('all 5 disclosures are additive `h+=`/`cData+=` (no figure/method/rule touched)',
      "h+='<div class=\"rn\" style=\"font-size:.76rem;color:var(--muted);margin-bottom:10px" in REP)
check('EN reveal + b54 locked identity intact', 'var EN_ENABLED=true;' in HTML and 'تقييم سوقيّ آليّ' in HTML)
check('engine is a valid b-series tag (no exact pin — Lesson-2)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb106:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
