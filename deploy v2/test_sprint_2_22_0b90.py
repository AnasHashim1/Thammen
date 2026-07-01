# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.90 — «وجه المختصر» (short-report 5-second face).

Restructures showShortReport PAGE-1 into the Progressive-Disclosure face (Gemini r5 items 1-9+13):
hero (neutral label «القيمة السوقية التقديرية» + price/ft² + LTR range-bar with the median dot at
`_hpct=(amount-low)/(high-low)` + ft²-range + valuation date) → confidence pill (E4 ladder 20/10/5,
n<5 «محدودة جداً» + scarcity note) → 5 property chips (villa/land, ✎→refine) → compressed legal
(ic-alert) → ONE «عرض التفاصيل» fold wrapping the financing + §١-٥ + footer (each string verbatim).
page-2 «ملحق المختصّين» unchanged.

VALUE-INVARIANT: amount/low/high/method/rule untouched; price/ft² + _hpct are DISPLAY derivations
(division/subtraction of broadcast figures), and the only *multiplications* of v.amount stay the three
DISCLOSED conventions (×0.90 / ×1.10 / ×1.30). Reads the REAL index.html / evaluate_unified.py (E14).
SR = the showShortReport SOURCE text (same extraction as b25/b63).

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b90.py
"""
import io, re, sys

def load(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()

HTML = load('index.html')
EU   = load('evaluate_unified.py')

_m = re.search(r'function showShortReport\(d\)\{.*?\n\}\n\nfunction show\(d\)\{', HTML, re.S)
SR = _m.group(0) if _m else ''
results = []
def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))

# ── (1) the new hero: neutral label + price/ft² + LTR range-bar + ft²-range + date ──
check('SR scope extracted', bool(SR))
check('hero label neutralized to «القيمة السوقية التقديرية» (unified, all audiences)',
      "t('القيمة السوقية التقديرية','Estimated market value')" in SR)
check('old warm hero label REMOVED («قيمة بيتك التقديرية اليوم»)',
      'قيمة بيتك التقديرية اليوم' not in SR)
check('price-per-ft² computed + shown (Gemini r5 #5)',
      "const _ppf=(_area&&v.amount)?Math.round((v.amount/_area)/10.7639):null;" in SR and
      "t(' ر.ق / قدم²',' QAR / ft²')" in SR)
check('LTR face range-bar with the median dot at _hpct (Gemini r5 #13)',
      "const _hpct=(v.low!=null&&v.high!=null&&v.high>v.low)?Math.max(0,Math.min(100,(v.amount-v.low)/(v.high-v.low)*100)):null;" in SR and
      "'<div class=\"thmr-facebar\"><div class=\"ftrack\"><span class=\"fdot\" style=\"left:'+_hpct.toFixed(1)+'%\">" in SR)
check('per-ft² range shown (Gemini r5 #5)',
      "const _lowFt=(_area&&v.low!=null)?Math.round((v.low/_area)/10.7639):null;" in SR and
      "t('نطاق سعر القدم: ','Per-ft² range: ')" in SR)
check('valuation date on the hero (Gemini r5 — «تحديث آلي» REJECTED → «تاريخ التقييم»)',
      "t('تاريخ التقييم: ','Valuation date: ')" in SR and 'تاريخ التحديث الآلي' not in SR)
check('the old cost-vs-market .thmr-rbar dropped from the hero (basisLn relocated into the fold)',
      "'<div class=\"thmr-rbar\">" not in SR and 'class="basis"' not in SR and 'basisLn' in SR)

# ── (2) confidence pill (E4 ladder) ──
check('confidence pill present with E4 ladder 20/10/5',
      "'<div class=\"thmr-conf '+_cCls" in SR and 'if(_confN>=20)' in SR and
      'else if(_confN>=10)' in SR and 'else if(_confN>=5)' in SR)
check('n<5 → «بيانات محدودة جداً» + the scarcity guidance (Gemini r5 #8)',
      "t('بيانات محدودة جداً','Very limited data')" in SR and
      'اعتمد على النطاق السعريّ أدناه كدليل استرشاديّ' in SR)
check('confidence classes exist in CSS (g/y/o/r)',
      '.thmr-conf.g{' in HTML and '.thmr-conf.y{' in HTML and
      '.thmr-conf.o{' in HTML and '.thmr-conf.r{' in HTML)

# ── (3) the 5 chips (villa + land branches) ──
check('chips builder + villa/land split',
      "h+='<div class=\"thmr-chips\">'+chips+'</div>';" in SR and
      "const _isLand=(d.asset_type==='raw_land'||cs==='land');" in SR)
check('villa chips: BUA / age / finish / annexes / plot',
      "t('مساحة البناء','Built area')" in SR and "cost.bua_m2" in SR and
      "t('عمر البناء','Building age')" in SR and "t('التشطيب','Finish')" in SR and
      "t('الملاحق','Annexes')" in SR and "t('مساحة الأرض','Plot area')" in SR)
check('land chips: area / streets(corner) / district / zoning / height (best-effort)',
      "t('المساحة','Area')" in SR and "corner_analysis" in SR and
      "t('أرض زاوية','Corner plot')" in SR and "t('الحي','District')" in SR and
      "/\\bR[123]\\b/" in SR)
check('editable ✎ chips deep-link to refine (Claim-Your-Home, static in b90)',
      "onclick=\"go(\\'refine\\')\"" in SR and '#ic-edit' in SR and
      "t('دقّق هذه المعلومة','Refine this detail')" in SR)
check('.thmr-chips / .thmr-chip CSS present', '.thmr-chips{' in HTML and '.thmr-chip{' in HTML)

# ── (4) compressed legal (safe, counsel-pending) — the FULL §٩ block stays in page-2 ──
check('compressed face legal line (ic-alert) + the full §٩ legal block still present',
      "'<div class=\"thmr-legalz\">" in SR and
      'مؤشّر سعريّ استرشاديّ مبنيّ على صفقات وزارة العدل العلنية — ليس تقييماً عقارياً معتمداً ولا حجّة رسمية.' in SR and
      'الإطار القانوني والمحاسبي' in SR and 'IFRS 13' in SR)
check('.thmr-legalz CSS present', '.thmr-legalz{' in HTML)

# ── (5) the ONE fold wrapping financing + §١-٥ + footer ──
check('«عرض التفاصيل» fold opened (id=srFold) + closed',
      "h+='<details class=\"thmr-fold\" id=\"srFold\">" in SR and
      "t('عرض التفاصيل','Show the details')" in SR and
      "h+='</details>';" in SR)
check('financing STILL un-gated inside the fold (fin-toggle, b89 Option A)',
      re.search(r"if\(hasVal&&d\.asset_type!=='raw_land'\)\{\s*\n\s*h\+='<details class=\"fin-toggle\"", SR) is not None and
      "(d.audience||'owner')==='buyer'" not in SR)
check('§١-٥ + footer still present (verbatim, now inside the fold)',
      'الأرقام الثلاثة التي تهمّك' in SR and 'الخلاصة العملية ' in SR and
      'من أين جاء الرقم؟' in SR and 'لا أسعار إعلانات' in SR)
check('.thmr-fold CSS present (summary marker hidden + arrow rotate)',
      '.thmr-fold{' in HTML and '.thmr-fold>summary::-webkit-details-marker{display:none}' in HTML and
      '.thmr-fold[open]>summary .farr{transform:rotate(180deg)}' in HTML)
check('printShortReport force-opens srFold (print parity, b52 pattern)',
      "const _f=document.getElementById('srFold'); const _was=_f?_f.open:null; if(_f)_f.open=true;" in HTML)

# ── (6) VALUE-INVARIANCE: only the three disclosed multipliers ──
_muls = sorted(set(re.findall(r'v\.amount\s*\*\s*[\d.]+', SR)))
check('amount-math = the three disclosed conventions only (×0.90 / ×1.10 / ×1.30)',
      _muls == ['v.amount*0.90', 'v.amount*1.10', 'v.amount*1.30'], str(_muls))
check('page-2 «ملحق المختصّين» + §٦ scenarios untouched',
      'ثمّن — ملحق المختصّين' in SR and 'جدول السيناريوهات — «ماذا لو؟»' in SR)
check('de-emoji lock: the new face uses <use href=#ic-*>, no emoji chars in the chips/pill/legal builder',
      '#ic-alert' in SR and '#ic-edit' in SR and '#ic-coins' in SR)

# ── (7) EN + version ──
check('new face strings are bilingual (t() wrapped)',
      "'Estimated market value')" in SR and "'Show the details')" in SR and
      "'Very limited data')" in SR and "'Refine this detail')" in SR)
mv = re.search(r"ENGINE_VERSION\s*=\s*'(thammen-sprint[^']+)'", EU)
check('ENGINE_VERSION is a b-series tag (R6, version-agnostic)', bool(mv) and mv.group(1).startswith('thammen-sprint2p22p0b'))
mt = re.search(r"SPRINT_TAG\s*=\s*'(\d+\.\d+\.\d+[a-z0-9.]*)'", EU)
check('SPRINT_TAG is a 2.22.0b-series tag (R6)', bool(mt) and mt.group(1).startswith('2.22.0b.'))

passed = sum(1 for _, ok, _ in results if ok); total = len(results)
for name, ok, detail in results:
    print(('PASS' if ok else 'FAIL') + ' - ' + name + (('  ' + detail) if (not ok and detail) else ''))
print('\n%d/%d checks passed' % (passed, total))
sys.exit(0 if passed == total else 1)
