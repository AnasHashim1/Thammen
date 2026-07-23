# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.61 — «تنقية اللغة» (language purge) — isolated tests.

Value-invariant copy fixes surfaced by the مثمّن + لغوي full-site tour:
  - 🔴 stock_strata: عامية «هذي»→«هذه» · Latin «median»→«الوسيط» · «لـ»→«إلى»
  - 🟡 Latin «Cap Rate»→«معدّل الرسملة» (engine + frontend) + plain gloss
  - 🟡 «MoJ»→«وزارة العدل» · «غير معروفة»→«غير معلومة» · «جاري»→«جارٍ»
       · dual «طابقان/ملحقان» · home credit-line top margin
DEFERRED (flagged): «طريقة»→«منهج» synonym-unification (both فصيح).
Reads the REAL files (E14). Copy-only → value-invariant by construction.
"""
import io, re, sys

def load(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()

HTML = load('index.html')
EU   = load('evaluate_unified.py')
SS   = load('stock_strata.py')
MU   = load('material_uncertainty.py')
OB   = load('output_briefs.py')

def arabic(line):
    return any('؀' <= ch <= 'ۿ' for ch in line)

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── 🔴 stock_strata: عامية + median (user-facing) ──
check('SS: no «median المدمج»',          'median المدمج' not in SS)
check('SS: no «median لها»',             'median لها' not in SS)
check('SS: no «هذي»',                    'هذي' not in SS)
check('SS: «الوسيط المدمج» >=4',         SS.count('الوسيط المدمج') >= 4)
check('SS: methodology Arabic ratio wording (b100 reworded «هذه النسبة تفصل»→«مؤشّر استدلاليّ»)', 'مؤشّرٌ استدلاليّ (من السعر)' in SS)
check('SS: «إلى وسيط أراضي المنطقة»',    'إلى وسيط أراضي المنطقة' in SS)
check('SS: no «سعرها لـ وسيط»',          'سعرها لـ وسيط' not in SS)
check('SS: C2 native-Arabic transparency line intact (b100: فئات→شرائح)', 'التصنيف بحسب الشرائح' in SS)  # a2-C2 invariant (native Arabic, no code-switch)

# ── material_uncertainty ──
check('MU: «غير معلومة» present', 'المساحة المبنية غير معلومة' in MU)
check('MU: no «غير معروفة»',      'المساحة المبنية غير معروفة' not in MU)

# ── output_briefs: MoJ + Cap Rate ──
check('OB: «وسيط وزارة العدل + 10-15%»', 'وسيط وزارة العدل + 10-15%' in OB)
check('OB: no «وسيط MoJ + 10-15%»',      'وسيط MoJ + 10-15%' not in OB)
check('OB: «تغيّر معدّل الرسملة»',        'تغيّر معدّل الرسملة' in OB)
check('OB: no user-facing «Cap Rate»',   'Cap Rate' not in OB)

# ── evaluate_unified: Cap Rate (only English code comments survive) ──
eu_caprate_ar = [ln for ln in EU.split('\n') if 'Cap Rate' in ln and arabic(ln)]
check('EU: 0 user-facing «Cap Rate» (Arabic lines)', len(eu_caprate_ar) == 0)
check('EU: «الرسملة» present',            'الرسملة' in EU)
check('EU: «عمر غير معلوم» present',      'عمر غير معلوم — تطبيق افتراضي' in EU)
check('EU: no «عمر غير معروف»',          'عمر غير معروف' not in EU)
check('EU: «رسملة 7-8%» reordered',      'رسملة 7-8%' in EU)

# ── index.html: Cap Rate + gloss + جارٍ + duals + لـ + hcred margin ──
check('HTML: 0 «Cap Rate»',              'Cap Rate' not in HTML)
check('HTML: «الرسملة المستخدم»',        'الرسملة المستخدم' in HTML)
check('HTML: cap-rate plain gloss',      'نسبة صافي الدخل' in HTML)
check('HTML: «جارٍ الاتصال»',            'جارٍ الاتصال' in HTML)
check('HTML: no «جاري الاتصال»',         'جاري الاتصال' not in HTML)
check('HTML: dual «طابقان (أرضي + أول)»', 'طابقان (أرضي + أول)' in HTML)
check('HTML: dual «ملحقان» option',      'value="2"' in HTML and '>ملحقان</option>' in HTML)  # b137 R6: option got data-en; dual form preserved
check('HTML: «نسبتها إلى الأرض»',        'نسبتها إلى الأرض' in HTML)
check('HTML: hcred margin-top:18px',     re.search(r'\.hcred\{[^}]*margin-top:18px', HTML) is not None)

# ── value-invariance spot-checks (copy-only sprint) ──
check('HTML: keeps «النطاق التقديري»',    'النطاق التقديري' in HTML)
check('HTML: keeps «ليس تقييماً معتمداً»', 'ليس تقييماً معتمداً' in HTML)
check('HTML: keeps «وزارة العدل»',        'وزارة العدل' in HTML)

# ── version format (R6/Lesson-2: no exact pin) ──
mv = re.search(r"ENGINE_VERSION\s*=\s*'(thammen-sprint[^']+)'", EU)
check('ENGINE_VERSION format', bool(mv) and mv.group(1).startswith('thammen-sprint'))
mt = re.search(r"SPRINT_TAG\s*=\s*'(\d+\.\d+\.\d+[a-z0-9.]*)'", EU)
check('SPRINT_TAG dotted-numeric', bool(mt))

passed = sum(1 for _, ok in results if ok)
total = len(results)
for name, ok in results:
    print(('PASS' if ok else 'FAIL') + ' - ' + name)
print('\n%d/%d checks passed' % (passed, total))
sys.exit(0 if passed == total else 1)
