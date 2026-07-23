# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.103 — «شاشة نتيجة التقييم: البطاقة المختصرة» (R1 — the card landing).

The 10-page landing was: the b90 5-second face + ONE «عرض التفاصيل» fold, BUT then a 4-button row
+ the ENTIRE page-2 «ملحق المختصّين» (§٦-٩ + QR) UNFOLDED by default. b103 FOLDS page-2 into the
exact b90 thmr-fold pattern (srFold2) — nothing deleted, everything one tap away — and simplifies
the button row to ONE primary «حفظ / مشاركة PDF» + ONE secondary «حسّن التقييم» + compact links.
Print force-opens ALL folds so the full two-page report still prints.

VALUE-INVARIANT: pure presentation/layering of the broadcast figures; amount/low/high/method/rule
untouched. Reads the REAL index.html / evaluate_unified.py (E14). SR = the showShortReport SOURCE.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b103.py
"""
import io, re, sys

def load(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()

HTML = load('index.html')
EU   = load('evaluate_unified.py')

_m = re.search(r'function showShortReport\(d\)\{.*?_srCountUp\(\);  // b104.*?\n\}', HTML, re.S)
SR = _m.group(0) if _m else ''
results = []
def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))

check('SR scope extracted', bool(SR))

# ── (1) page-2 «ملحق المختصّين» is now FOLDED by default (the b90 thmr-fold pattern) ──
check('srFold2 wraps the specialist appendix (collapsed <details class="thmr-fold">)',
      "h+='<details class=\"thmr-fold\" id=\"srFold2\"><summary>" in SR)
check('srFold2 summary carries the plain title + a content-hint (r10 #4)',
      "t('ملحق المختصّين','Specialist appendix')" in SR and
      'للبنك والمثمّن والمحامي' in SR)
check('srFold2 is CLOSED by default (no open attr on the appendix fold)',
      '<details class="thmr-fold" id="srFold2" open' not in SR)
check('srFold2 is closed at the end of page-2 (after the QR/fingerprint line)',
      "h+='</details>';  // b103" in SR)
# structural: the appendix content (§٦-٩) sits BETWEEN the srFold2 open and its close
_o = SR.find('id="srFold2"'); _c = SR.find("</details>';  // b103")
check('§٦ scenarios + §٩ legal live INSIDE srFold2', _o != -1 and _c != -1 and _o < _c and
      SR.find('جدول السيناريوهات', _o) < _c and SR.find('الإطار القانوني والمحاسبي', _o) < _c)

# ── (2) the button row: ONE primary PDF + ONE secondary refine + compact links ──
check('PRIMARY CTA = «حفظ / مشاركة PDF» (PO-picked) → printShortReport',
      "<button class=\"thmr-btn no-print\" onclick=\"printShortReport()\">'+t('حفظ / مشاركة PDF'" in SR)
check('SECONDARY = «حسّن التقييم» (alt) → refine',
      "<button class=\"thmr-btn alt\" onclick=\"go(\\'refine\\')\">'+t('حسّن التقييم'" in SR)
check('the old 4-button row is GONE (scroll-to-srPage2 button + «الملحق المتخصص ↓» removed)',
      "scrollIntoView({behavior:'smooth'})" not in SR and 'الملحق المتخصص ↓' not in SR)
# b141 R6: the go('results') link was relabeled «التفاصيل الكاملة» → «النتيجة» (it navigates
# BACK to the result screen; the old label collided with «التقرير الكامل» + the result-screen fold).
check('the demoted actions are compact text links (thmr-links: full report + result)',
      "h+='<div class=\"thmr-links no-print\">" in SR and
      "<a onclick=\"openReport()\">'+t('التقرير الكامل'" in SR and
      "<a onclick=\"go(\\'results\\')\">'+t('النتيجة'" in SR)
check('.thmr-links CSS present', '.thmr-links{' in HTML and '.thmr-links a{' in HTML)
check('.fnote content-hint CSS present', '.thmr-fold>summary .fnote{' in HTML)
check('closed-fold hide rule present (the Chromium <details> quirk fix, b46 precedent, scoped)',
      '.thmr-fold:not([open])>*:not(summary){display:none}' in HTML)

# ── (3) the always-visible compliance line stays OUTSIDE all folds (b52 precedent) ──
check('the not-certified line is on the face, outside any fold (istirshadi pill)',
      "t('تقدير استرشادي — وليس تقييماً معتمداً','An indicative estimate — not a certified valuation')" in SR)
check('the compressed legal line stays on page-1 (outside srFold2)',
      'ليس تقييماً عقارياً معتمداً ولا حجّة رسمية' in SR)

# ── (4) print parity: force-open ALL folds, restore after ──
check('printShortReport force-opens ALL #srOut details (srFold + srFold2 + fin-toggle)',
      "document.querySelectorAll('#srOut details')" in HTML and
      '_ds.forEach(x=>{x.open=true;})' in HTML and
      '_ds.forEach((x,i)=>{x.open=_st[i];})' in HTML)
check('the old single-fold print path is REPLACED (no bare srFold-only force-open left)',
      "const _f=document.getElementById('srFold'); const _was=_f?_f.open:null; if(_f)_f.open=true;" not in HTML)

# ── (5) VALUE-INVARIANCE: still only the three disclosed multipliers; page-2 content intact ──
_muls = sorted(set(re.findall(r'v\.amount\s*\*\s*[\d.]+', SR)))
check('amount-math = the three disclosed conventions only (×0.90 / ×1.10 / ×1.30)',
      _muls == ['v.amount*0.90', 'v.amount*1.10', 'v.amount*1.30'], str(_muls))
check('page-2 content preserved verbatim (§٦ scenarios + §٧ investor + §٨ evidence + §٩ legal + QR)',
      'جدول السيناريوهات — «ماذا لو؟»' in SR and 'للمستثمر — منظور الدخل' in SR and
      'شفافية الأدلّة' in SR and 'الإطار القانوني والمحاسبي' in SR and 'thammen.qa/verify' in SR)  # b104 R6: §٨ header «شفافية الدليل — بلا تجميل» → «شفافية الأدلّة»
check('both QR canvases still rendered post-injection (srQr1 page-1 + srQr2 in the fold)',
      "document.getElementById('srQr1')" in SR and "document.getElementById('srQr2')" in SR)

# ── (6) EN + version ──
check('the new strings are bilingual (t() wrapped)',
      "'Save / share PDF')" in SR and "'Specialist appendix')" in SR and "'Full report')" in SR)
mv = re.search(r"ENGINE_VERSION\s*=\s*'(thammen-sprint[^']+)'", EU)
check('ENGINE_VERSION is a b-series tag (R6)', bool(mv) and mv.group(1).startswith('thammen-sprint2p22p0b'))
mt = re.search(r"SPRINT_TAG\s*=\s*'(\d+\.\d+\.\d+[a-z0-9.]*)'", EU)
check('SPRINT_TAG is a 2.22.0b-series tag (R6)', bool(mt) and mt.group(1).startswith('2.22.0b.'))

passed = sum(1 for _, ok, _ in results if ok); total = len(results)
for name, ok, detail in results:
    print(('PASS' if ok else 'FAIL') + ' - ' + name + (('  ' + detail) if (not ok and detail) else ''))
print('\n%d/%d checks passed' % (passed, total))
sys.exit(0 if passed == total else 1)
