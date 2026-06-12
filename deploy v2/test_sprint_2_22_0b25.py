# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.25 — م2 «المختصر + نظام التصميم thm-report».

Isolated checks against the REAL files (Rule #40 / E14):
  1. The thm-report design system: signed tokens (navy #16324F · bronze #A4814A ·
     paper #FBF8F2), IBM Plex Sans Arabic hosted LOCALLY (4 woff2 weights, OFL,
     no CDN), scoped to the reports only (D7 — the .thmr namespace).
  2. The short-report surface (screens ٦/٧ of the v3 contract): two pages
     (الزبدة + ملحق المختصين) composed from the BROADCAST only.
  3. The signed copy matrix (docs/MATRIX_short_report_copy_SIGNED.md): the four
     hero labels + neighbor paragraphs + evidence rows + the four constants
     (جبري ×0.90 · D3 financing editable-inline + «استشر بنكك» · ref/fp/QR ·
     the verbatim legal block incl. IFRS 13 · the D-3 calibration hook).
  4. D6: the short report opens FIRST; the full report is one click away.
  5. The local QR lib (MIT, vendored — no CDN) + the shared _verifyUrl builder.
  6. Print: the printing-short A4 path rules.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b25.py
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  PASS  {name}')
    else:
        FAIL += 1
        print(f'  FAIL  {name}  {detail}')


with open('index.html', encoding='utf-8') as f:
    HTML = f.read()

_m = re.search(r'function showShortReport\(d\)\{.*?\n\}\n\nfunction show\(d\)\{', HTML, re.S)
SR = _m.group(0) if _m else ''

print('\n[1] thm-report design system (D7-scoped, signed tokens, local fonts)')
check('signed tokens present (navy/bronze/paper)',
      '#16324F' in HTML and '#A4814A' in HTML and '#FBF8F2' in HTML)
check('tokens live on the .thmr scope (D7 — reports only)',
      '--thmr-navy:#16324F' in HTML and '--thmr-bronze:#A4814A' in HTML
      and '--thmr-paper:#FBF8F2' in HTML)
check('IBM Plex Sans Arabic @font-face x4 (400/500/600/700)',
      all(f"url('fonts/IBMPlexSansArabic-{w}.woff2')" in HTML
          for w in ('Regular', 'Medium', 'SemiBold', 'Bold')))
check('font applied INSIDE .thmr only (no global swap)',
      re.search(r"\.thmr\{[^}]*IBM Plex Sans Arabic", HTML) is not None
      and re.search(r"^body\{[^}]*IBM Plex", HTML, re.M) is None)
# The plan's no-CDN rule (D7) covers the THM-REPORT assets: IBM Plex + the QR lib.
# (The pre-existing app-shell Tajawal Google-Fonts link predates م2 and is out of
# its scope — touching the global shell font is م4-adjacent, its own decision.)
check('NO CDN for the b25 assets (IBM Plex local-only + QR local-only)',
      'IBM+Plex' not in HTML and 'ibm-plex' not in HTML.lower().replace('ibmplex', 'KEEP')
      and 'cdn.jsdelivr' not in HTML and 'unpkg.com' not in HTML and 'cdnjs' not in HTML
      and 'qrcode' not in HTML.replace('qrcode.local.js', ''))
for w in ('Regular', 'Medium', 'SemiBold', 'Bold'):
    p = f'fonts/IBMPlexSansArabic-{w}.woff2'
    ok = os.path.exists(p) and os.path.getsize(p) > 50000
    check(f'{p} on disk (>50KB, real woff2)', ok)
    if ok:
        with open(p, 'rb') as fh:
            check(f'{w} carries the wOF2 magic', fh.read(4) == b'wOF2')
check('OFL license shipped alongside', os.path.exists('fonts/LICENSE-IBM-Plex-Sans-Arabic.txt'))

print('\n[2] local QR lib (vendored, MIT, no CDN)')
check('qrcode.local.js on disk', os.path.exists('qrcode.local.js'))
with open('qrcode.local.js', encoding='utf-8') as fh:
    QRS = fh.read()
check('MIT attribution header present', 'MIT License' in QRS and 'davidshimjs' in QRS)
check('included locally in index.html', '<script src="qrcode.local.js"></script>' in HTML)

print('\n[3] the short-report surface (screen + functions + D6)')
check('shortReportScreen markup', 'id="shortReportScreen"' in HTML and 'id="srOut"' in HTML)
check('srOut carries the .thmr scope', '<div id="srOut" class="thmr">' in HTML)
for fn in ('showShortReport', 'openShortReport', 'printShortReport',
           '_verifyUrl', '_srCase', '_srPayment', 'srRecalcPay'):
    check(f'{fn}() defined once', HTML.count(f'function {fn}(') == 1)
check('openShortReport renders from window._lastResult (b2.3 pattern, no re-fetch)',
      "function openShortReport(){const d=window._lastResult; if(!d)return; showShortReport(d); go('shortReport');}" in HTML)
check('D6 — TIER-3 CTA opens the SHORT report first',
      'onclick="openShortReport()">📄 التقرير المختصر' in HTML)
check('D6 — the FULL report one click away inside the short report',
      'onclick="openReport()">التقرير الكامل</button>' in HTML)
check('the b23 verify link now shares _verifyUrl (one builder, no drift)',
      HTML.count('function _verifyUrl(') == 1 and '_verifyUrl(d)' in HTML
      and HTML.count("'&rule='+encodeURIComponent") == 1)

# Sprint 2.22.0b.28 re-point (the PO delivered the GOVERNING print contract
# docs/ثمن_التقرير_المختصر_v2_امريخ.pdf — م2's anticipated copy-tweak pass):
# the cost-led surface re-rendered to the PDF's two-page copy; the matrix's
# conditional SKELETON survives as the basis lines for the non-cost leaders.
print('\n[4] the PDF-contract hero + the matrix skeleton in the basis lines')
check('the PDF hero (universal, warm)', 'قيمة بيتك التقديرية اليوم' in SR)
check('the PDF hero pill', 'تقدير استرشادي — وليس تقييماً معتمداً' in SR)
check('cost basis = the PDF sentence, matched_n-bound',
      'محسوبة من قيمة الأرض + قيمة البناء بعد عمره' in SR
      and 'مثل بيتك في المنطقة قليلة' in SR)
check('market basis keeps the matrix label «وسيط شريحتك»', 'وسيط شريحتك:' in SR)
check('income basis keeps the matrix label «متّسقة مع إيجارك الفعلي»',
      'متّسقة مع إيجارك الفعلي' in SR)
check('land basis keeps the matrix label «قيمة الأرض»', 'قيمة الأرض:' in SR)

print('\n[5] the PDF/matrix stories + evidence (broadcast-bound)')
check('cost neighbor = the PDF story, share/market/age-bound',
      'أغلب ما بيع غالياً في منطقتك' in SR and 'فللاً جديدة فاخرة' in SR
      and '_domShare' in SR and 'مقارنةٌ غير عادلة — لك وعليك' in SR)
check('market neighbor (matrix verbatim core)',
      'صفقات مثل بيتك كافية وواضحة' in SR and 'وسيطها مرجعك' in SR)
check('income neighbor (matrix verbatim core)',
      'والدخل أصدق مرجع لعقار مُدِرّ' in SR)
check('land neighbor (matrix verbatim core)',
      'الأرض تُقاس بسعر المتر في منطقتك' in SR)
check('the PDF §٢ three-numbers row (fair / quick-sale / the other-class card)',
      'الأرقام الثلاثة التي تهمّك' in SR and 'لو احتجت بيعاً سريعاً' in SR
      and 'فئة أخرى، ليست فئة بيتك' in SR)
check('the PDF §٣ practical-essence advice (the SIGNED hard-ceiling bars, disclosed)',
      'الزبدة العملية' in SR and 'إن كنت بائعاً' in SR and 'إن كنت مشترياً' in SR
      and 'v.amount*1.10' in SR and 'v.amount*1.30' in SR
      and 'هامش تفاوض +10%' in SR and 'سقف +30%' in SR)
check('the PDF §٤ sources (no-listings disclosure)',
      'من أين جاء الرقم؟' in SR and 'لا أسعار إعلانات ولا «كلام سوق»' in SR)
check('cost evidence (§٨): matched-tells-the-story + geo dispersion + thresholds',
      'تشبه بيتك فعلاً' in SR and 'قادت الكلفةُ الرقمَ' in SR
      and 'الجغرافي الكامل' in SR and 'ld.thresholds' in SR or 'ld&&ld.thresholds' in SR)
check('land evidence row (n + window)',
      'صفقات الأرض' in SR and 'vf.window_months' in SR)

print('\n[6] the four constants')
check('D2 — الجبري ×0.90 with the honesty label',
      'v.amount*0.90' in SR and 'ليست تقييم تصفية' in SR)
check('D3 — the three assumptions EDITABLE INLINE (20/25/4.5 defaults)',
      'id="srDown"' in SR and 'id="srYears"' in SR and 'id="srRate"' in SR
      and 'value="20"' in SR and 'value="25"' in SR and 'value="4.5"' in SR)
check('D3 — «استشر بنكك» line', 'استشر بنكك' in SR)
check('ref + fp + QR on the surface',
      'd.report_ref' in SR and 'd.report_fp' in SR and 'srQr1' in SR and 'srQr2' in SR
      and "new QRCode(" in SR)
check('the GT hook (the D-3 WhatsApp channel — the PDF wording)',
      'شاركه يصير تقديرنا أدق للجميع' in SR and '+974 70177761' in SR)
check('the legal block = the PDF FULL text incl. IFRS 13',
      'تقدير آلي استرشادي' in SR and 'ليس تقييماً عقارياً معتمداً' in SR
      and 'IFRS 13' in SR and 'حجةً قضائية أو مصرفية' in SR)
check('the D-3 calibration hook (the PDF §٨ wording; generic for land)',
      'معايرة الكلفة' in SR and 'V001 ±1%' in SR and 'شاركنا تقييمك' in SR
      and 'كل شيت جديد يدقّقها' in SR)
check('the PDF §٥ raise-invitations bound to the scenarios broadcast (no sweep figures)',
      'أشياء قد ترفع الرقم — أخبرنا بها' in SR and 'الإيجار أقوى معلومة' in SR
      and 'حسّن التقدير' in SR and '1.9M' not in SR and '4.7M' not in SR)
check('the §٦ scenarios table bound to the b23 broadcast (scn.items + the idea column)',
      'v.scenarios' in SR and 'scn.items.forEach' in SR and 'it.label_ar' in SR
      and 'وش لو؟' in SR and 'الفكرة' in SR)
check('the tamper line (the PDF §٩)', 'ليست النسخة الصادرة بهذا التاريخ' in SR)
check('the FULL PDF legal block (التركات + المنصة + الزبدة العملية caveat)',
      'لقسمة التركات دون تراضي الأطراف' in SR
      and 'ولا ينشئ أي التزام أو مسؤولية على المنصة' in SR
      and 'إرشادٌ تفاوضي عام لا توصية فردية' in SR)

print('\n[7] zero JS value-math except the DECLARED conventions')
check('price-per-m² is the division on plot area (declared exception)',
      'Math.round(v.amount/d.plot_area_m2)' in SR)
check('the payment formula is the amortized D3 exception',
      'principal*r/(1-Math.pow(1+r,-n))' in HTML)
_muls = sorted(set(re.findall(r'v\.amount\s*\*\s*[\d.]+', SR)))
check('amount-math = EXACTLY the three disclosed conventions (×0.90 D2 · ×1.10/×1.30 the signed hard ceilings)',
      _muls == ['v.amount*0.90', 'v.amount*1.10', 'v.amount*1.30'], str(_muls))

print('\n[8] _srPayment mirror (D3 math)')
def payment(P, down, years, rate):
    pr = P * (1 - down / 100.0)
    r = (rate / 100.0) / 12
    n = years * 12
    return int(pr * r / (1 - (1 + r) ** (-n)) + 0.5)
check('2.4M @ 20%/25y/4.5% → ≈10,672 (matches the mockup ≈10,670)',
      payment(2400000, 20, 25, 4.5) == 10672, str(payment(2400000, 20, 25, 4.5)))
check('30% down lowers the payment (interactivity-proven live in R14: 9,338)',
      payment(2400000, 30, 25, 4.5) == 9338, str(payment(2400000, 30, 25, 4.5)))

print('\n[9] _srCase mirror (leader-case routing, same semantics as م0)')
def sr_case(asset_type, leadership, tri_mode, method):
    if asset_type == 'raw_land':
        return 'land'
    if tri_mode == 'income_led' or method == 'income_approach_only':
        return 'income'
    if leadership and leadership.get('leader') == 'cost':
        return 'cost'
    return 'market'
check('cost_led → cost', sr_case('standalone_villa', {'leader': 'cost'}, None, 'comparison_thin') == 'cost')
check('income_led REAL shape (comparison method + tri.mode) → income',
      sr_case('standalone_villa', None, 'income_led', 'comparison_thin') == 'income')
check('apartment income-only → income',
      sr_case('apartment_building', None, None, 'income_approach_only') == 'income')
check('matched → market', sr_case('standalone_villa', {'leader': 'market'}, None, 'comparison_bracket') == 'market')
check('raw_land → land', sr_case('raw_land', None, None, 'comparison_bracket') == 'land')
check('the JS routing reads the same fields',
      "tri.mode==='income_led'" in SR or "tri.mode==='income_led'" in HTML)

print('\n[10] print path (A4, the short report alone)')
check('printing-short rules present',
      'body.printing-short .screen { display: none !important; }' in HTML
      and 'body.printing-short #shortReportScreen { display: block !important; }' in HTML)
check('page-break between the two pages',
      'body.printing-short .thmr-page { border: none !important' in HTML
      and 'page-break-after: always' in HTML)
check('printShortReport toggles the class around window.print',
      "document.body.classList.add('printing-short')" in HTML
      and "document.body.classList.remove('printing-short')" in HTML)

print('\n[11] api serves the local assets (whitelisted routes — the live-smoke catch)')
import api as _api  # the real FastAPI module (E14)
_routes = {getattr(r, 'path', '') for r in _api.app.routes}
check('/qrcode.local.js route registered', '/qrcode.local.js' in _routes)
check('/fonts/{fname} route registered', '/fonts/{fname}' in _routes)
check('font whitelist = exactly the 4 weights + the OFL license',
      _api._THMR_FONT_WHITELIST == frozenset({
          'IBMPlexSansArabic-Regular.woff2', 'IBMPlexSansArabic-Medium.woff2',
          'IBMPlexSansArabic-SemiBold.woff2', 'IBMPlexSansArabic-Bold.woff2',
          'LICENSE-IBM-Plex-Sans-Arabic.txt'}))
check('no blanket StaticFiles mount (the 2.16.17 lockdown posture holds)',
      'StaticFiles(' not in open('api.py', encoding='utf-8').read())

print('\n[12] refusal honesty + version format')
check('refusal path: no value → honest line + full-report escape (no DEF-12/scenarios)',
      'لم يصدر تقدير لهذا العقار' in SR)
with open('evaluate_unified.py', encoding='utf-8') as fh:
    ENG = fh.read()
check('ENGINE_VERSION format', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)

print(f'\n=== {PASS} passed, {FAIL} failed ===')
sys.exit(1 if FAIL else 0)
