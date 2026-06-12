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

print('\n[4] the signed matrix — hero labels (verbatim)')
check('cost hero', 'القيمة التقديرية — مرتكز التكلفة (أرض + بناء مُهلَك)' in SR)
check('market hero', 'القيمة التقديرية — وسيط شريحتك' in SR)
check('income hero', 'القيمة التقديرية — متّسقة مع إيجارك الفعلي' in SR)
check('land hero', "'قيمة الأرض'" in SR)

print('\n[5] the signed matrix — basis + neighbor + evidence (broadcast-bound)')
check('cost basis = the b19/b20 broadcast label (cost.label_ar, with the verbatim fallback)',
      'cost.label_ar' in SR and 'قيمة التكلفة (أرض + بناء مُهلَك) — نهج DRC' in SR)
check('market basis bound to matched_n + dispersion_36',
      'صفقة مطابقة لنوعك وعمرك، تشتت' in SR and '_mn' in SR and '_d36' in SR)
check('income basis bound to cap_rate + provenance n + the borrow disclosure',
      'رسملة معايَرة' in SR and '_capPct' in SR and '_capN' in SR
      and 'مُستعار من شريحة مجاورة' in SR)
check('land basis bound to value_floor ppm2 × plot',
      'وسيط أراضي منطقتك' in SR and 'vf.land_per_m2_qar' in SR and 'd.plot_area_m2' in SR)
check('cost neighbor (matrix verbatim core)',
      'فالأصدق كلفة الإحلال: أرضك + بناؤك بعد الإهلاك' in SR
      and 'أكثر صفقات منطقتك حديثة وفاخرة' in SR)
check('market neighbor (matrix verbatim core)',
      'صفقات مثل بيتك كافية وواضحة' in SR and 'وسيطها مرجعك' in SR)
check('income neighbor (matrix verbatim core)',
      'والدخل أصدق مرجع لعقار مُدِرّ' in SR)
check('land neighbor (matrix verbatim core)',
      'الأرض تُقاس بسعر المتر في منطقتك' in SR)
check('cost dual-evidence row (matched vs geo, thresholds from the broadcast)',
      'المطابق لشريحتك (نوع/عمر)' in SR and 'الجغرافي الكامل' in SR
      and 'ld.thresholds' in SR)
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
check('the GT hook (the D-3 WhatsApp channel)',
      'أرسل سعراً فعلياً تعرفه: واتساب' in SR and '+974 70177761' in SR)
check('the legal block VERBATIM incl. IFRS 13',
      'هذا تحليل معلوماتي آلي لدعم القرار، وليس تقييماً رسمياً ولا تقريراً صادراً عن مُقيِّم مرخَّص' in SR
      and 'IFRS 13' in SR and 'القرارات المتخذة بناءً عليه على مسؤولية متخذها' in SR)
check('the D-3 calibration hook (retention for buildings, generic for land)',
      'معايرة منحنى الاحتفاظ' in SR and 'V001 ±1%' in SR and 'شيتك يدقّقها' in SR
      and 'كل شيت جديد يدقّقها' in SR)
check('the rent-axis hint is NUMBER-FREE (no fabricated sweep figures)',
      'ولو أُجّرت: أدخل إيجارك الفعلي' in SR and '1.9M' not in SR and '4.7M' not in SR)
check('scenarios table bound to the b23 broadcast (scn.items, no literals)',
      'v.scenarios' in SR and 'scn.items.forEach' in SR and 'it.label_ar' in SR)

print('\n[7] zero JS value-math except D3 + price-per-m² (the declared pair)')
check('price-per-m² is the division on plot area (declared exception)',
      'Math.round(v.amount/d.plot_area_m2)' in SR)
check('the payment formula is the amortized D3 exception',
      'principal*r/(1-Math.pow(1+r,-n))' in HTML)
_muls = re.findall(r'v\.amount\s*[*/]\s*[\d.]+', SR)
check('the ONLY amount-math on the surface = ×0.90 (D2) [+ /plot for per-m²]',
      _muls == ['v.amount*0.90'], str(_muls))

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

print('\n[11] refusal honesty + version format')
check('refusal path: no value → honest line + full-report escape (no DEF-12/scenarios)',
      'لم يصدر تقدير لهذا العقار' in SR)
with open('evaluate_unified.py', encoding='utf-8') as fh:
    ENG = fh.read()
check('ENGINE_VERSION format', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)

print(f'\n=== {PASS} passed, {FAIL} failed ===')
sys.exit(1 if FAIL else 0)
