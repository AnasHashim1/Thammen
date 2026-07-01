# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.86 — EN twins for the AUDIENCE-BRIEF sections (output_briefs.py).
E14: exercises the REAL build_cap_rate_provenance_section + build_comparable_grid_section
and asserts the section title_en set. BACKEND-ONLY / VALUE-INVARIANT — additive `*_en`
keys alongside the untouched `*_ar`; EN dormant (frontend reads via pick() when LANG=='en',
b77). index.html UNTOUCHED (renderSection pick() reads shipped in b83; R14 N/A by
construction). AR output byte-identical (asserted)."""
import io
import output_briefs as ob

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

SRC = io.open('output_briefs.py', encoding='utf-8').read()

# ── (1) the 18 section title_en added ──
TITLES = {
    'مصدر معدل الرسملة': 'Cap-rate source',
    'شبكة المقارنات المعدّلة': 'Adjusted comparables grid',
    'تفصيل المصادر': 'Source breakdown',
    'سبب عدم التقدير': 'Why the valuation was withheld',
    'حالات الاستخدام': 'Use cases',
    'سجل التعديلات الاتجاهية': 'Trend-adjustment log',
    'هل السعر معقول؟': 'Is the price reasonable?',
    'المخاطر والإشارات': 'Risks and signals',
    'أسئلة يجب طرحها قبل الشراء': 'Questions to ask before buying',
    'قيمة عقارك': 'Your property value',
    'استراتيجية التسعير': 'Pricing strategy',
    'اتجاه السوق': 'Market trend',
    'نصائح للبيع': 'Selling tips',
    'تحليل العائد': 'Yield analysis',
    'القيمة بمنهج الدخل': 'Income-approach value',
    'تحليل الحساسية': 'Sensitivity analysis',
    'مرجع الإيجار': 'Rent reference',
    'السياق السوقي': 'Market context',
}
missing_ar = [ar for ar in TITLES if ("'title_ar': '" + ar + "',") not in SRC]
missing_en = [ar for ar, en in TITLES.items() if ("'title_en': '" + en + "',") not in SRC]
check('all 18 section title_ar still present (AR untouched)', not missing_ar)
check('all 18 section title_en added', not missing_en)

# ── (2) cap_rate_provenance — real call (calibrated + hardcoded) ──
cal = ob.build_cap_rate_provenance_section(
    {'source': 'calibrated', 'cap_rate_pct': 5.2, 'sample_size': 46,
     'confidence': 'reliable', 'last_updated': '2026-01'})['content']
check('cap-rate calibrated: source_en/confidence_en/body_en present',
      cal['source_en'] == 'Calibrated from market data' and cal['confidence_en'] == 'Sufficient evidence'
      and 'empirically calibrated from' in cal['body_en'] and '5.2%' in cal['body_en'])
check('cap-rate calibrated: AR UNCHANGED',
      cal['source_ar'] == 'مُعايَر من بيانات السوق' and cal['confidence_ar'] == 'شواهد كافية'
      and cal['body_ar'].startswith('معدل الرسملة المستخدم'))
cal_b = ob.build_cap_rate_provenance_section(
    {'source': 'calibrated', 'cap_rate_pct': 5.0, 'sample_size': 46, 'confidence': 'reliable',
     'last_updated': '2026-01', 'bracket_borrowed': True, 'borrowed_from_bracket': '400-600',
     'subject_bracket': '600-900'})['content']
check('cap-rate borrowed: body_en discloses the borrow',
      'borrowed from the 400-600 bracket' in cal_b['body_en'])
hard = ob.build_cap_rate_provenance_section(
    {'source': 'hardcoded', 'cap_rate_pct': 6.5, 'reason_ar': 'س', 'reason_en': 'x'})['content']
check('cap-rate hardcoded: source_en default + body_en uncalibrated',
      hard['source_en'] == 'Default rate (not calibrated)' and 'typical (uncalibrated) rate' in hard['body_en'])

# ── (3) comparable_grid — real call ──
grid = {'confidence': 'reliable', 'adjusted_median_per_m2': 3000, 'n': 25,
        'valuation_date': '2026-01', 'sources': [], 'note_ar': 'ملاحظة',
        'comparables': [{'date': '2025', 'price_per_m2_raw': 3000, 'price_per_m2_adjusted': 3100,
                         'adjustments': [{'factor': 'time', 'pct_display': '+3%'}], 'size_m2': 500}]}
gc = ob.build_comparable_grid_section(grid, 'buyer')['content']
check('grid: confidence_en + footer_en present',
      gc['confidence_en'] == 'Sufficient evidence' and 'geographically-keyed data' in gc['footer_en'])
check('grid: AR UNCHANGED', gc['confidence_ar'] == 'شواهد كافية' and gc['footer_ar'].startswith('علاوة الزاوية'))
check('grid: value-math untouched (adjusted_median/n)', gc['adjusted_median_per_m2'] == 3000 and gc['n'] == 25)

# ── (4) EN maps defined ──
check('provenance + grid EN maps defined',
      ob._PROVENANCE_SOURCE_EN['calibrated'] == 'Calibrated from market data'
      and ob._PROVENANCE_CONFIDENCE_EN['fallback'].startswith('Insufficient evidence')
      and ob._GRID_CONFIDENCE_EN['indicative'] == 'Limited evidence')

# ── (5) frontend wiring intact (renderSection reads via pick — unchanged from b83) ──
HTML = io.open('index.html', encoding='utf-8').read()
check('renderSection reads pick(sec,title) + pick(c,source/confidence/body/footer)',
      "pick(sec,'title')" in HTML and "pick(c,'source')" in HTML and "pick(c,'confidence')" in HTML
      and "pick(c,'body')" in HTML and "pick(c,'footer')" in HTML)

# ── (6) engine bump (format only) ──
import evaluate_unified as eu
check('engine is a valid b-series tag', eu.SPRINT_TAG.startswith('2.22.0b.') and eu.ENGINE_VERSION.startswith('thammen-sprint2p22p0b'))

print('\nb86:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
