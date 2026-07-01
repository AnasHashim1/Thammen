# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.96 «الشامل البنكيّ» (م٣, first slice) — isolated tests (E14).

Bank-grade full report: the report identity (ref + content fingerprint) on the COVER
(page 1, where a bank looks), + a PRINT-VISIBLE verification QR in the footer (the b25
short-report QR pattern brought to the full report; local qrcode lib — zero CDN), gated
on the broadcast _verifyUrl (server HMAC key). Print hardening: page-break-inside:avoid
on the QR + the comparables proof table. VALUE-INVARIANT (display + print CSS).
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML = open('index.html', encoding='utf-8').read()
ENG  = open('evaluate_unified.py', encoding='utf-8').read()

i = HTML.index('function showReport(d){')
j = HTML.find('\nfunction ', i + 10)
RP = HTML[i:j if j != -1 else len(HTML)]

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('PASS |', name)
    else:    failed += 1; print('FAIL |', name)

# ── cover identity ──
check('cover carries the report reference', "t('المرجع: ','Reference: ')" in RP and "d.report_ref" in RP)
check('cover carries the content fingerprint (gated on report_fp)',
      "if(d.report_fp)h+='<span>'+t('بصمة المحتوى: '" in RP)

# ── footer QR ──
check('_repVu hoisted (single _verifyUrl call, shared with the QR)', 'let _repVu=null;' in RP and '_repVu=_verifyUrl(d);' in RP)
check('print-visible QR block gated on _repVu', 'if(_repVu){' in RP and 'id="repQr"' in RP)
check('QR caption «امسح للتحقّق»', "t('امسح للتحقّق من أصالة هذا التقرير'" in RP)
check('QR rendered post-injection with the LOCAL lib (no CDN)',
      "new QRCode(document.getElementById('repQr')" in RP and "typeof QRCode!=='undefined'" in RP)
check('QR render wrapped in try/catch (never throws)', 'try{new QRCode(document.getElementById(\'repQr\')' in RP and '}catch(e){}' in RP)
check('the verify link + GT hook still present (not regressed)',
      "تحقّق من صحّة التقرير" in RP and 'info@thammen.qa' in RP)

# ── print hardening ──
check('.rep-qrwrap CSS present', '.rep-qrwrap{' in HTML and '.rep-qrwrap #repQr{' in HTML)
check('page-break-inside:avoid on QR + comparables table',
      '.rep-def12, .rep-cover, .rep-foot, .rep-qrwrap, .rep-comp { page-break-inside: avoid; }' in HTML)

# ── value-invariance ──
check('no v.amount arithmetic added (only the ×0.90 forced-sale stays)',
      sorted(set(re.findall(r'v\.amount\s*\)?\s*\*\s*([0-9.]+)', RP))) in ([], ['0.90']))
check('no assignment into v.amount/low/high', not re.search(r'v\.(amount|low|high)\s*=[^=]', RP))
check('ENGINE_VERSION b-series format (R6)', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+b\d+-", ENG) is not None)

print(f'\n{passed}/{passed+failed} PASS' + ('' if failed == 0 else f' — {failed} FAIL'))
sys.exit(1 if failed else 0)
