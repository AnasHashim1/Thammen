# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.63 — «ترشيق بداية المختصر للمالك» (short-report page-1 owner declutter).

Two value-invariant display moves on short-report PAGE 1 (the owner's default deliverable):
 (1) the D3 financing line is BUYER-GATED — a mortgage calculator is a buyer tool, so the
     OWNER default (+ seller/investor) no longer meets it under the headline. The buyer keeps
     it (and already has the result-screen calculator b35); _srPayment/srRecalcPay stay (DRY).
 (2) the raw engine_version dev-string is DROPPED from the page-1 header (noise at the top of
     a printable owner report); المرجع TH- + QR/verify prove authenticity; the FULL report
     (showReport) keeps engine_version (b17 contract).

VALUE-INVARIANT (figures/thresholds untouched). Reads the REAL index.html / evaluate_unified.py
(E14). SR is the showShortReport SOURCE text (same extraction as test b25), so the gated literals
stay in source (the buyer still renders them) — hence ZERO b25 re-point.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b63.py
"""
import io, re, sys

def load(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()

HTML = load('index.html')
EU   = load('evaluate_unified.py')

# the showShortReport SOURCE (same scope the b25 test uses)
_m = re.search(r'function showShortReport\(d\)\{.*?\n\}\n\nfunction show\(d\)\{', HTML, re.S)
SR = _m.group(0) if _m else ''
results = []
def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))

# ── (1) financing line buyer-gated ──
check('SR scope extracted', bool(SR))
check('financing line still in source (literal kept for the buyer)',
      'class="thmr-micro thmr-pay"' in SR and 'id="srDown"' in SR and 'استشر بنكك' in SR)
# the gate predicate sits immediately before the .thmr-pay emission
_gate = re.search(r"\(d\.audience\|\|'owner'\)==='buyer'\)\s*\{\s*\n\s*h\+='<div class=\"thmr-micro thmr-pay\"", SR)
check('financing emission wrapped in a buyer-gate', _gate is not None)
check('functions stay defined (DRY — reused by the buyer + result-screen b35)',
      SR.count('function _srPayment(') == 0 and HTML.count('function _srPayment(') == 1
      and HTML.count('function srRecalcPay(') == 1)
check('the b35 result-screen buyer calculator is UNTOUCHED (still gated, reuses _srPayment)',
      "d.audience==='buyer'" in HTML and 'bcRecalc' in HTML
      and HTML.count('_srPayment(v.amount,20,25,4.5)') >= 1)

# ── (2) engine_version dropped from the short-report page-1 header ──
check('engine_version GONE from showShortReport (page-1 header de-noised)',
      'd.engine_version' not in SR)
check('المرجع report_ref KEPT in the page-1 header',
      "t('المرجع ','Reference ')+'<b dir=\"ltr\">'+d.report_ref" in SR)  # b80 R6: المرجع label now t()-wrapped
check('the FULL report STILL carries engine_version (b17 footer contract intact)',
      "d.engine_version||''" in HTML)

# ── value-invariance: still EXACTLY the three disclosed conventions ──
_muls = sorted(set(re.findall(r'v\.amount\s*\*\s*[\d.]+', SR)))
check('amount-math = the three disclosed conventions only (×0.90 / ×1.10 / ×1.30)',
      _muls == ['v.amount*0.90', 'v.amount*1.10', 'v.amount*1.30'], str(_muls))

# ── b62 work + compliance untouched ──
check('b62 §5 teaser + §3 bars intact',
      'قد يرتفع الرقم' in SR and '◆ بائعاً' in SR and '◆ مشترياً' in SR)
check('compliance/honesty kept',
      'ليس تقييماً معتمداً' in SR and 'لا أسعار إعلانات' in SR
      and 'v.amount*0.90' in SR and 'info@thammen.qa' in SR)
check('§6 scenarios table + full-report clusters intact',
      'جدول السيناريوهات — «ماذا لو؟»' in SR and 'حول الرقم' in HTML and 'حول البيانات' in HTML)

# ── version format ──
mv = re.search(r"ENGINE_VERSION\s*=\s*'(thammen-sprint[^']+)'", EU)
check('ENGINE_VERSION format', bool(mv) and mv.group(1).startswith('thammen-sprint'))
mt = re.search(r"SPRINT_TAG\s*=\s*'(\d+\.\d+\.\d+[a-z0-9.]*)'", EU)
check('SPRINT_TAG dotted-numeric', bool(mt))

passed = sum(1 for _, ok, _ in results if ok); total = len(results)
for name, ok, detail in results:
    print(('PASS' if ok else 'FAIL') + ' - ' + name + (('  ' + detail) if (not ok and detail) else ''))
print('\n%d/%d checks passed' % (passed, total))
sys.exit(0 if passed == total else 1)
