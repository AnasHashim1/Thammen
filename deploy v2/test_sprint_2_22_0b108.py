# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.108 — the unified assumptions register (S3, RICS VPS 2 / IVS 102). E14: reads the REAL
index.html. 🟢 FRONTEND copy / VALUE-INVARIANT — one numbered annex in the FULL report (showReport), Layer 3,
assembled from already-broadcast fields + the disclosed engine constants (built-ratio 0.77, floors-default,
50-yr straight-line depreciation, the RCN ladder, E26 age basis) + an actionable floors nudge on the cost row.
No value/method/rule change; api.py untouched. Bilingual (t()); RICS/IVS tokens LRM-wrapped."""
import io
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

# isolate showReport()
_s = HTML.find('function showReport(d){')
_e = HTML.find('function printReportA4(')
if _e < 0: _e = HTML.find('function showShortReport(d){')
REP = HTML[_s:_e] if (_s >= 0 and _e > _s) else ''
check('showReport() region isolated', bool(REP))

# ── the register annex header (VPS 2 / IVS 102, LRM-wrapped) ──
check('register annex header AR + EN (RICS VPS 2 / IVS 102, LRM-wrapped)',
      "t('الافتراضات والافتراضات الخاصّة (&lrm;RICS VPS 2 / IVS 102&lrm;)','Assumptions and special assumptions (&lrm;RICS VPS 2 / IVS 102&lrm;)')" in REP)
check('register is a NUMBERED annex (uses _ax())',
      REP.find('h+=_ax();\n    h+=\'<div class="rc"><div class="rt" style="margin-bottom:8px">\'+t(\'الافتراضات') >= 0 or
      ("الافتراضات والافتراضات الخاصّة" in REP and "h+=_ax();" in REP))

# ── standing assumptions (always) ──
check('standing: condition-not-inspected (references «حول العقار», not duplicated)',
      '<b>الحالة والتشطيب:</b> افتراضٌ قائم — لم يُعايَن العقار ميدانياً' in REP and
      '<b>Condition and finish:</b> an assumption — the property was not inspected on site' in REP)
check('standing: HBU residential-use assumption',
      '<b>الاستخدام:</b> أعلى وأفضل استخدامٍ سكنيّ ضمن التنظيم القائم' in REP and
      '<b>Use:</b> residential highest-and-best-use under the current zoning' in REP)
check('standing: evidence-window assumption (cross-ref S1, no time adjustment)',
      '<b>نافذة الأدلّة:</b> صفقاتٌ مسجَّلة حتى ٢٤ شهراً' in REP and 'no explicit time adjustment to the median' in REP)

# ── cost-led additions (scoped to leader==='cost') ──
check('cost additions gated on leader===cost + value_stack.cost',
      "if(v.leadership&&v.leadership.leader==='cost'&&v.value_stack&&v.value_stack.cost){" in REP)
check('C-3: BUA + built-ratio 0.77 justification (reads broadcast bua_m2)',
      '<b>مساحة البناء (BUA):</b> مُقدَّرة ≈ ' in REP and '_aC.bua_m2' in REP and
      'نسبة صافٍ-إلى-إجماليّ ٠٫٧٧ × عدد الطوابق' in REP and 'a net-to-gross ratio of 0.77 × the number of floors' in REP)
check('the FLOORS-default assumption (2 floors, the 56/565/21 case) — only when floors not provided',
      "if(!(d.user_inputs&&d.user_inputs.floors))h+='• '+t('<b>عدد الطوابق:</b> يُفترَض طابقان" in REP and
      "<b>Number of floors:</b> two floors (ground + first) are assumed unless you enter the count" in REP)
check('C-2: RCN ladder + finish-level (reads broadcast finish)',
      '<b>كلفة الإحلال (RCN):</b> سُلَّمٌ بحسب مستوى التشطيب (شِلّ ١٬٢٠٠ · عاديّ ٢٬٢٠٠' in REP and
      '_finMap[_aC.finish]' in REP)
check('C-2: 50-yr straight-line depreciation combining physical/functional/economic obsolescence',
      'خطٌّ مستقيمٌ على عمرٍ نافعٍ ٥٠ سنة، يجمع التقادم الماديّ والوظيفيّ والاقتصاديّ' in REP and
      'straight-line over a 50-year useful life, combining physical, functional and economic obsolescence' in REP)
check('retention basis reads broadcast retention',
      'نسبة القيمة المتبقية للبناء ' in REP and "'<span dir=\"ltr\">'+_aC.retention+'</span>'" in REP)
check('E26 age-basis (system CGIS age; user age = sensitivity)',
      '<b>أساس العمر:</b> العمر الموثَّق في النظام (CGIS) هو أساس الاحتساب (المعيار E26)' in REP and
      'the system-documented (CGIS) age is the basis of calculation (E26)' in REP)
check('C-6 cost calibration n=1 (V001 ±1%) — verify-first restated concisely',
      'مُعايَرة على تقييمٍ معتمدٍ واحدٍ حتى الآن (V001، ضمن ±١٪)' in REP and
      'calibrated on one certified valuation so far (V001, within ±1%)' in REP)

# ── income-led addition (C-5 cap-rate source) ──
check('C-5: cap-rate source when income leads',
      "const _ildAsm=((v.income_triangulation||{}).mode==='income_led')||v.method==='income_approach_only';" in REP and
      "'<b>معدّل الرسملة:</b> من خليّة '" in REP and "'<b>Cap rate:</b> from the '" in REP)

# ── the actionable floors nudge on the cost breakdown row ──
check('actionable floors nudge on the «تفكيك المرتكز» cost row (floors not provided)',
      "if(!(d.user_inputs&&d.user_inputs.floors))h+='<div class=\"rn\" style=\"font-size:.72rem;margin-top:4px;color:var(--bronze)\">" in REP and
      'يفترض هذا الرقم طابقين؛ إن كان لبيتك بنتهاوس أو طابقٌ إضافيّ' in REP and
      'This figure assumes two floors; if your home has a penthouse or an extra floor' in REP)

# ── VALUE-INVARIANCE + placement + version ──
check('register is inside hasValuation (before the refusal card)',
      REP.find('الافتراضات والافتراضات الخاصّة') < REP.find("pick(v,'reason')||t('لا تتوفر بيانات كافية"))
check('register comes AFTER property-basics (Layer 3 order)',
      REP.find('بيانات العقار الأساسية') < REP.find('الافتراضات والافتراضات الخاصّة'))
check('EN reveal + b54 locked identity intact', 'var EN_ENABLED=true;' in HTML and 'تقييم سوقيّ آليّ' in HTML)
check('engine is a valid b-series tag (no exact pin — Lesson-2)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb108:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
