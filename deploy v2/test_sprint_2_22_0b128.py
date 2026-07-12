# -*- coding: utf-8 -*-
# Sprint 2.22.0b.128 «شاشة الشروط والأسئلة + كلفة-تقود» (S8ب, redesign v2) — isolated test (E14).
# 🟢 FRONTEND-ONLY / VALUE-NEUTRAL: expands the existing #termsModal into the consolidated
# «الشروط والمنهجيّة» accordion (the lean-report destination). The b68 truthful Terms/Privacy
# is PRESERVED VERBATIM inside a «الشروط الكاملة» accordion; 4 methodology accordions + a pinned
# disclaimer are ADDED (bilingual data-en). No engine/api valuation change (version lines only).
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HTML = open('index.html', encoding='utf-8').read()
ENG  = open('evaluate_unified.py', encoding='utf-8').read()
API  = open('api.py', encoding='utf-8').read()

# isolate the #termsModal region (so strings are asserted where they belong)
_i = HTML.index('id="termsModal"')
_j = HTML.index('</body>')
MODAL = HTML[_i-40:_j]

checks = []
def ok(name, cond):
    checks.append((name, bool(cond)))

# ── the 4 NEW methodology accordions (correct 2025 citations) ──
ok('acc1 المنهجيّة summary',            'كيف نحسب القيمة؟ (المنهجيّة)' in MODAL)
ok('acc1 VPS 3 / IVS 103',             'RICS VPS 3 / IVS 103' in MODAL and 'منهج المقارنة بالمبيعات' in MODAL)
ok('acc2 أساس القيمة summary',          'أساس القيمة (تعريف IVS)' in MODAL)
ok('acc2 VPS 2 / IVS 102 market value', 'RICS VPS 2 / IVS 102' in MODAL and 'القيمة السوقيّة' in MODAL)
ok('acc3 آليّة الكلفة summary',          'آليّة الكلفة وسجلّ الافتراضات' in MODAL)
ok('acc3 cost formula',                'قيمة الكلفة = المساحة المبنيّة' in MODAL)
ok('acc4 حدود التقدير summary',          'حدود التقدير ومصدر البيانات' in MODAL)
ok('acc4 VPGA 10 / IVS 106 desktop',   'RICS VPGA 10 / IVS 106' in MODAL and 'دون فحصٍ ميدانيّ' in MODAL)

# ── the pinned essential disclaimer (always-visible core compliance) ──
ok('pinned tm-pinned present',         'class="tm-pinned"' in MODAL)
ok('pinned: not certified',            'وليس تقييماً رسمياً' in MODAL)
ok('pinned: IFRS 13',                  'IFRS 13' in MODAL)
ok('pinned: CC BY 4.0',                'CC BY 4.0' in MODAL)
ok('pinned: not affiliated MoJ',       'غير منتسبةٍ لوزارة العدل' in MODAL)

# ── assumptions register table (VPS 2 / cost) ──
ok('assumptions table present',        'class="tm-astbl"' in MODAL)
ok('assumptions: built ratio 0.77',    'نسبة البناء المفترضة' in MODAL and '0.77' in MODAL)
ok('assumptions: depreciation curve',  'منحنى الإهلاك' in MODAL)
ok('assumptions: age basis GIS floor', 'مسح GIS (حدٌّ أدنى)' in MODAL)
ok('assumptions: V001 calibration',    'V001' in MODAL and 'تقييم معتمد واحد' in MODAL)

# ── the honesty / limits guards that MUST survive ──
ok('«فوق ٥ مليون» → certified valuer',  'فوق ٥ مليون ريال' in MODAL and 'مثمّنٍ معتمد' in MODAL)
ok('«استدلالاً بالسعر لا معاينةً»',      'استدلالاً بالسعر المسجَّل لا معاينةً' in MODAL)
ok('evidence hierarchy stated',        'هرميّة الأدلّة' in MODAL)

# ── b68 truthful Terms/Privacy PRESERVED VERBATIM inside «الشروط الكاملة» accordion ──
ok('«الشروط الكاملة» accordion',        'الشروط الكاملة وإشعار الخصوصية' in MODAL)
ok('b68 §3 retains report copy',       'نحتفظ بنسخة من تقرير تقييمك' in MODAL)
ok('b68 §3 parcel-data disclosed',     'الرقم المساحيّ والمنطقة والموقع والتقدير' in MODAL)
ok('b68 §3 Resend cross-border',       'Heroku وCloudflare وResend' in MODAL)
ok('b68 §3 utility numbers removed',   'تُزال أرقام حسابات الكهرباء والماء' in MODAL)
ok('b68 deletion right',               'حذف نسخة تقريرك من سجلّاتنا' in MODAL)
ok('b68 §6 72h breach commitment',     '72' in MODAL and 'ساعة' in MODAL)
ok('b68 EN block preserved',           'We keep a copy of your valuation report' in MODAL and 'Thammen team — info@thammen.qa' in MODAL)
ok('b58 no beta re-introduced',        ('تجريبية' not in MODAL) and ('بالدعوة' not in MODAL))
ok('b54 term-lock: automated market',  'تقييم سوقيّ آليّ' in MODAL)

# ── the modal shell + a11y preserved (a24/b46/b70) ──
ok('modal role=dialog + aria-modal',   'id="termsModal"' in HTML and 'role="dialog"' in MODAL and 'aria-modal="true"' in MODAL)
ok('openTerms / closeTerms intact',    'function openTerms()' in HTML and 'function closeTerms()' in HTML)
ok('b70 Escape closer intact',         "getElementById('scopeModal')" in HTML and "getElementById('termsModal')" in HTML)

# ── EN arms present (b88 live) for the new accordions ──
ok('EN: methodology summary data-en',  'data-en="How do we compute the value? (Methodology)"' in MODAL)
ok('EN: basis-of-value data-en',       'data-en="Basis of value (IVS definition)"' in MODAL)
ok('EN: pinned disclaimer data-en',    'Thammen is an independent service, not affiliated with the Ministry of Justice.' in MODAL)
ok('EN: «الشروط الكاملة» data-en',      'data-en="Full Terms &amp; Privacy Notice"' in MODAL)

# ── scoped accordion CSS (does not leak to other <details>) ──
ok('scoped CSS #termsModal details.tm-acc', '#termsModal details.tm-acc{' in HTML)
ok('scoped +/- marker',                '#termsModal details.tm-acc[open]>summary::after' in HTML)

# ── structural: 5 tm-acc accordions, balanced ──
ok('exactly 5 tm-acc accordions',      MODAL.count('class="tm-acc"') == 5)
ok('5 tm-acc-body wrappers',           MODAL.count('tm-acc-body') == 5)
ok('details balanced in modal',        len(re.findall(r'<details\b', MODAL)) == MODAL.count('</details>'))

# ── VALUE-NEUTRAL: engine change = version lines only; api.py carries no terms-accordion logic ──
ok('engine is a valid b-series tag (no exact pin — Lesson-2; b128 shipped, later sprints keep this modal)',
                                       "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)
ok('api.py untouched by accordion',    'tm-acc' not in API and 'tm-pinned' not in API)

passed = sum(1 for _, c in checks if c)
for n, c in checks:
    print(('PASS' if c else 'FAIL'), '·', n)
print('----')
print(f'{passed}/{len(checks)}')
sys.exit(0 if passed == len(checks) else 1)
