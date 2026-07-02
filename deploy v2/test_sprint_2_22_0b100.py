# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.100 «العرض الصادق: شرائح سعريّة» — isolated tests (E14).

Value-invariant honesty reframe of the cost-led / stratification display (Gemini r9 convergence):
  A) stock_strata: strata LABELS are now PRICE-POSITION (measured ratio band), NOT asserted
     age/finish. The (soft) age/finish inference moved to the descriptions, flagged
     «استدلالاً بالسعر / inferred from price». methodology says «مؤشّر استدلاليّ … لا معاينة».
  B) index.html short-report §١ (cost-led): «كان فللاً جديدة فاخرة» → price-position; the
     «قيمته العادلة» claim → an honest conservative estimate «قد تعلو إن كان مُصاناً».
  C) index.html §٦ higher-tier row: «الفلل الجديدة الفاخرة حولك» → «الشريحة الأعلى سعراً».
  D) index.html result-screen cost-led subline: adds the honest floor line
     «حدٌّ أدنى محافظ (تعذّر تأكيد حالة البناء) … أدخل حالتها في حسّن التقييم».
  E) engine OSR note «طبقة فاخرة» → «شريحة أعلى سعراً» (hygiene; dormant under b20).

VALUE-INVARIANT: only labels/copy change; the ratio thresholds (1.15/1.50/2.20) + all
valuation math are UNTOUCHED. The engine is condition/built-type BLIND (R7), so a
price-ratio label must never assert an unmeasured finish/age as fact.
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import stock_strata as S
HTML = open('index.html', encoding='utf-8').read()
ENG  = open('evaluate_unified.py', encoding='utf-8').read()
SS   = open('stock_strata.py', encoding='utf-8').read()

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('PASS |', name)
    else:    failed += 1; print('FAIL |', name)

# ── A. price-position labels (no asserted finish/age) ──
check('luxury_new label = «الشريحة الأعلى سعراً» (no «فاخر»)', S.STRATUM_LABELS_AR['luxury_new'] == 'الشريحة الأعلى سعراً')
check('modern_stock label = «الشريحة المتوسّطة سعراً»',       S.STRATUM_LABELS_AR['modern_stock'] == 'الشريحة المتوسّطة سعراً')
check('aging_stock label = «قريبة من سعر الأرض»',             S.STRATUM_LABELS_AR['aging_stock'] == 'قريبة من سعر الأرض')
check('land_priced label kept «بسعر الأرض»',                  S.STRATUM_LABELS_AR['land_priced'] == 'بسعر الأرض')
check('NO AR label asserts «فاخر»/«حديث»/«متوسط العمر»',
      not any(('فاخر' in v) or ('حديث البناء' in v) or ('متوسط العمر' in v) for v in S.STRATUM_LABELS_AR.values()))
check('EN labels price-position (Top/Mid price tier · Near land price)',
      S.STRATUM_LABELS_EN['luxury_new']=='Top price tier' and S.STRATUM_LABELS_EN['modern_stock']=='Mid price tier'
      and S.STRATUM_LABELS_EN['aging_stock']=='Near land price')

# ── descriptions carry the explicit price-inference disclaimer ──
check('luxury_new desc: «استدلالاً بالسعر، لا معاينةً» + no bare «فلل جديدة (1-3 سنوات) مع تشطيب فاخر»',
      'استدلالاً بالسعر' in S.STRATUM_DESC_AR['luxury_new'] and 'لا معاينةً' in S.STRATUM_DESC_AR['luxury_new']
      and 'مع تشطيب فاخر' not in S.STRATUM_DESC_AR['luxury_new'])
check('modern_stock desc: «استدلالاً بالسعر» (soft, غير مؤكَّد)', 'استدلالاً بالسعر' in S.STRATUM_DESC_AR['modern_stock'])
check('aging_stock desc: «استدلالاً بالسعر»',                    'استدلالاً بالسعر' in S.STRATUM_DESC_AR['aging_stock'])
check('EN descs carry «inferred from price»',
      all('inferred from price' in S.STRATUM_DESC_EN[k] for k in ('aging_stock','modern_stock','luxury_new')))

# ── VALUE-INVARIANCE: the classification ratio thresholds are UNTOUCHED ──
check('ratio band luxury_new ≥2.20 intact', "('luxury_new',   2.20, None)" in SS)
check('ratio band modern 1.50-2.20 intact', "('modern_stock', 1.50, 2.20)" in SS)
check('ratio band aging 1.15-1.50 intact',  "('aging_stock',  1.15, 1.50)" in SS)

# ── methodology note: price-inference framing, not «تفصل بين فئات العمر» ──
check('methodology_ar: «مؤشّرٌ استدلاليّ (من السعر)» + «لا معاينةٌ لهما»',
      'مؤشّرٌ استدلاليّ (من السعر)' in SS and 'لا معاينةٌ لهما' in SS)
check('methodology_ar: old «تفصل بين فئات العمر والتشطيب» + «فيلا فاخرة جديدة» GONE',
      'تفصل بين فئات العمر والتشطيب' not in SS and 'فيلا فاخرة جديدة' not in SS)
check('methodology_en: «inferred about age and finish»/«INFERENCE» framing',
      'not an inspection of them' in SS)

# ── E. engine OSR note (hygiene; dormant under b20) ──
check('OSR_NOTE_AR: «شريحةٍ أعلى سعراً مسيطرة» (no «طبقة فاخرة»)',
      'مدفوع بشريحةٍ أعلى سعراً مسيطرة' in ENG and 'طبقة فاخرة' not in ENG)

# ── B. short-report §1 (cost-led) reframed ──
check('§1: «بيعت بأعلى بكثير من قيمة الأرض (شريحةٌ أعلى سعراً» + «استدلالاً بالسعر لا معاينةً»',
      'بيعت بأعلى بكثير من قيمة الأرض (شريحةٌ أعلى سعراً' in HTML and 'استدلالاً بالسعر لا معاينةً' in HTML)
check('§1: old «كان فللاً جديدة فاخرة» GONE', 'كان فللاً جديدة فاخرة' not in HTML)
check('§1: «قيمته العادلة تقترب من قيمة أرضه» claim GONE', 'تقترب قيمته العادلة من قيمة أرضه' not in HTML)
check('§1: honest conservative estimate «اعتمدنا تقديراً محافظاً» + «قد تعلو قيمته إن كان بناؤه مُصاناً»',
      'اعتمدنا تقديراً محافظاً' in HTML and 'قد تعلو قيمته إن كان بناؤه مُصاناً' in HTML)
check('§1: «مقارنة … بأسعار الشريحة الأعلى» (not «الفلل الجديدة»)',
      'بأسعار الشريحة الأعلى مقارنةٌ غير منصِفة' in HTML)

# ── C. §6 higher-tier row ──
check('§6 row: «الشريحة الأعلى سعراً حولك — فئة أعلى، غالباً ليست فئة بيتك»',
      'ما تبيعه الشريحة الأعلى سعراً حولك — فئة أعلى، غالباً ليست فئة بيتك' in HTML)
check('§6 row: old «الفلل الجديدة الفاخرة حولك» GONE', 'الفلل الجديدة الفاخرة حولك' not in HTML)

# ── D. result-screen cost-led subline: the honest FLOOR + refine CTA ──
check('subline: «حدٌّ أدنى محافظ (تعذّر تأكيد حالة البناء)»', 'حدٌّ أدنى محافظ (تعذّر تأكيد حالة البناء)' in HTML)
check('subline: «فيلا مُصانة قد تعلو قيمتها — أدخل حالتها في «حسّن التقييم»»',
      'وفيلا مُصانة قد تعلو قيمتها — أدخل حالتها في «حسّن التقييم»' in HTML)
check('subline: the honest sparse-comparables reason kept', 'لأنّ الصفقات المماثلة القريبة كانت قليلة' in HTML)

# ── regression: the user's OWN finish inputs (legit «فاخر») are UNTOUCHED ──
check('refine field «تشطيب فاخر (للمباني القديمة)» kept', 'تشطيب فاخر (للمباني القديمة)' in HTML)
check('subject-upgrade note «التشطيب الفاخر» (subject what-if) kept', 'التشطيب الفاخر' in HTML)

# ── version (R6/Lesson-2: format-agnostic, NOT an exact pin) ──
check('ENGINE_VERSION b-series format', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+b\d+-", ENG) is not None)
check('SPRINT_TAG b-series format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+b\.\d+'", ENG) is not None)

print(f'\n{passed}/{passed+failed} PASS' + ('' if failed == 0 else f' — {failed} FAIL'))
sys.exit(1 if failed else 0)
