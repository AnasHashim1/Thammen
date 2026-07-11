# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.105 — «توحيد وتثبيت لغة التطبيق» (R3 — the register lock, Gemini r11 flip-list).

A PO-signed, deterministic term-flip across the user-facing surfaces (the b54 pattern applied to
REGISTER). Adjudicated per Rule #54 (14 accept · 8 accept-modified · 5 reject).

SIGNED (PO-signed this session, amends earlier signed copy):
  • «تحفظ مادي» / «التحفظ المادي» → «عدم اليقين الجوهري» (RICS VPGA 10 «Material Valuation Uncertainty»
    read as financial stinginess by the ordinary owner) — the MUC banner + chip + clause + notes. The
    banner level words unified to حرج/مرتفع/متوسط.
  • «البناء المُهلَك / مُهلَكاً» SOFTENED on the OWNER short-report surfaces («بعد الإهلاك») — the DRC
    professional basis line (full report / result screen) KEEPS «مُهلَك».
ACCEPTED replaces:
  • «معامل الاحتفاظ» → «نسبة القيمة المتبقية للبناء»
  • «حوض المقارنة الموسَّع» → «نطاق المقارنة الموسَّع»
  • «مؤشّر مزامنة البيانات» → «تاريخ تحديث بيانات وزارة العدل»
  • «الاستخدام الأمثل» → «أعلى وأفضل استخدام» (RICS Highest-and-Best-Use)
  • «نافذة N شهراً» → «صفقات آخر N شهراً»
KEEP (rejected Gemini renames / signed locks): «مرتكز» (بطل العقد) · «شريحة» · «الجبريّ» · «معدّل الرسملة»
gloss ours (keeps صافي + 5–6%) · «بصمة المحتوى» (Gemini's «رمز أمني» misleading).

VALUE-INVARIANT: copy/register only; amount/low/high/method/rule untouched. Reads the REAL files (E14).
Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b105.py
"""
import io, re, sys

def load(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()

HTML = load('index.html')
EU   = load('evaluate_unified.py')
MU   = load('material_uncertainty.py')
DF   = load('data_freshness.py')
SC   = load('scope_of_service.py')

results = []
def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))

# ── (1) MUC term «تحفظ مادي» → «عدم اليقين الجوهري» everywhere user-facing ──
check('material_uncertainty banners use «عدم اليقين الجوهري» (3 levels)',
      MU.count('عدم اليقين الجوهري: حرج') == 1 and MU.count('عدم اليقين الجوهري: مرتفع') == 1 and
      MU.count('عدم اليقين الجوهري: متوسط') == 1)
check('material_uncertainty formal clause reframed (English standard name rides it)',
      'عدم اليقين الجوهري في التقييم وفق' in MU and 'Material Valuation Uncertainty' in MU)
check('NO «تحفظ مادي» / «التحفظ المادي» left in material_uncertainty.py',
      not re.search(r'تحفظ مادي|التحفظ المادي', MU))
check('NO «تحفظ مادي» / «التحفظ المادي» left in evaluate_unified.py',
      not re.search(r'تحفظ مادي|التحفظ المادي', EU))
check('index.html MUC chip = «عدم اليقين الجوهري: »',
      "t('عدم اليقين الجوهري: ','Material uncertainty: ')" in HTML)
# b125 R6: the b52 «عدم اليقين الجوهري والمعايير» _mucFold accordion became the flat LIMITS section
# (_s4bLimits, «حدود هذا التقدير»); the full MUC clause folds inside it and its RICS line uses the
# b105 term «عدم اليقين الجوهريّ». Same term-lock (NOT «تحفظ مادي»), bilingual.
check('index.html LIMITS section uses the «عدم اليقين الجوهريّ» term (bilingual)',
      "t('عدم اليقين الجوهريّ وفق ','Material uncertainty per ')" in HTML
      and "t('عدم اليقين الجوهري: ','Material uncertainty: ')" in HTML)
check('the level lexicon (chip) intact: critical→حرج',
      "'critical':'حرج'" in HTML)

# ── (2) «مُهلَك» register split: owner short-report softened, specialist kept ──
_sr = (re.search(r'function showShortReport\(d\)\{.*?_srCountUp\(\);  // b104.*?\n\}', HTML, re.S) or [None,''])
SR = _sr.group(0) if hasattr(_sr,'group') else ''
check('OWNER short-report §١ story softened («بعد إنقاص استهلاكه» not «مُهلَكاً»)',
      'بناءً مُهلَكاً' not in SR and 'بعد إنقاص استهلاكه' in SR)
check('OWNER short-report tiered-legend softened («قيمة البناء بعد الإهلاك»)',
      'مرتكز الكلفة (أرض + قيمة البناء بعد الإهلاك)' in SR and
      '(أرض + بناء مُهلَك)' not in SR)  # not in the short report anymore
_rep = (re.search(r'function showReport\(d\)\{.*?\n\}', HTML, re.S) or [None,''])
REP = _rep.group(0) if hasattr(_rep,'group') else ''
check('SPECIALIST full report KEEPS «البناء المُهلَك» (register split)',
      'البناء المُهلَك' in REP)
check('«مرتكز» kept everywhere it appears (بطل العقد — signed)',
      'مرتكز التكلفة' in HTML or 'مرتكز الكلفة' in HTML)

# ── (3) the accepted clean replaces ──
check('«معامل الاحتفاظ» → «نسبة القيمة المتبقية للبناء»',
      'نسبة القيمة المتبقية للبناء' in HTML and 'معامل الاحتفاظ ' not in HTML)
check('«حوض المقارنة» → «نطاق المقارنة»',
      'نطاق المقارنة الموسَّع جغرافياً' in HTML and 'حوض المقارنة' not in HTML)
check('«مؤشّر مزامنة البيانات» → «تاريخ تحديث بيانات وزارة العدل» (no double وزارة العدل)',
      'تاريخ تحديث بيانات وزارة العدل: آخر سجلّ رسميّ' in DF and 'مؤشّر مزامنة' not in DF)
check('«الاستخدام الأمثل» → «أعلى وأفضل استخدام» (HBU)',
      'أعلى وأفضل استخدام' in EU and 'الاستخدام الأمثل' not in EU)
check('«نافذة N شهراً» → «صفقات آخر N شهراً» (engine + scope)',
      'صفقات آخر 36 شهراً' in EU and 'صفقات آخر 24 شهراً' in SC and
      'نافذة 36 شهراً' not in EU and 'نافذة 24 شهراً' not in SC)

# ── (4) rejected renames NOT applied (locks held) ──
check('REJECTED «فئة» rename NOT applied — «شريحة» lexicon kept',
      'شريحة' in HTML)
check('REJECTED «القسري» NOT applied — «الجبريّ» kept (b56 signed)',
      'الجبريّ' in HTML)
check('cap-rate gloss OURS kept (صافي + 5–6%) — Gemini gloss rejected',
      '5–6% صافياً' in HTML)

# ── (5) version ──
mv = re.search(r"ENGINE_VERSION\s*=\s*'(thammen-sprint[^']+)'", EU)
check('ENGINE_VERSION is a b-series tag (R6)', bool(mv) and mv.group(1).startswith('thammen-sprint2p22p0b'))
mt = re.search(r"SPRINT_TAG\s*=\s*'(\d+\.\d+\.\d+[a-z0-9.]*)'", EU)
check('SPRINT_TAG is a 2.22.0b-series tag (R6)', bool(mt) and mt.group(1).startswith('2.22.0b.'))

passed = sum(1 for _, ok, _ in results if ok); total = len(results)
for name, ok, detail in results:
    print(('PASS' if ok else 'FAIL') + ' - ' + name + (('  ' + detail) if (not ok and detail) else ''))
print('\n%d/%d checks passed' % (passed, total))
sys.exit(0 if passed == total else 1)
