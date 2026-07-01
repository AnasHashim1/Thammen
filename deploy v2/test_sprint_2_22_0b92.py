# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.92 «حاضنة النطاق + الصدق + n<5» — isolated tests (E14: reads the REAL files).

The Gemini r7 range-display overhaul on the short-report face, VALUE-INVARIANT:
(a) edge-pinned median dot (skew <20%/>80%) -> the tiered-bracket metaphor (labeled value
    chip over a 3-block track + floor/ceiling endpoint labels);
(b) HONEST anchors legend for cost/geo leaders (floor = DRC cost anchor, ceiling = market
    median) — Gemini's false floor attribution + fabricated frontage reason REJECTED (#54);
(c) SIGNED §3 n<5 -> range-only face («القيمة المتوقّعة بين X و Y», central figure hidden);
(d) the central-dot facebar KEPT verbatim for the non-skewed case (b90 pin survives).
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML = open('index.html', encoding='utf-8').read()
ENG  = open('evaluate_unified.py', encoding='utf-8').read()

# scope to showShortReport
i = HTML.index('function showShortReport(d){')
j = HTML.find('\nfunction ', i + 10)
SR = HTML[i:j if j != -1 else len(HTML)]

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('PASS |', name)
    else:    failed += 1; print('FAIL |', name)

# ── (a) the tiered bracket ──
check('tiers container rendered', '.thmr-tiers' in HTML and 'class="thmr-tiers"' in SR)
check('skew gate = _hpct<20 || _hpct>80', '_hpct<20||_hpct>80' in SR.replace(' ', ''))
check('labeled value chip (not a naked dot) in the skewed case',
      't(\'القيمة التقديرية\',\'Estimated value\')' in SR and 'class="tchip"' in SR)
check('3-block track', SR.count('<span></span></div>') >= 0 and '"ttrack"><span></span><span></span><span></span>' in SR)
check('floor endpoint label «الأرضية السعرية»', "t('الأرضية السعرية','Price floor')" in SR)
check('ceiling endpoint label «السقف السوقي»', "t('السقف السوقي','Market ceiling')" in SR)
check('marker clamped away from the edges (18..82)', 'Math.max(18,Math.min(82,_hpct))' in SR)
check('tiers CSS block present', '.thmr-tiers .tmk .tchip' in HTML and '.thmr-tiers .ttrack' in HTML)

# ── (b) honesty (#54 adjudications) ──
check('HONEST legend: floor = the DRC cost anchor, ceiling = the market median',
      "t('الأرضية = مرتكز الكلفة (أرض + بناء مُهلَك) · السقف = وسيط صفقات السوق'" in SR)
check('legend gated to the leaders where it is TRUE (cost / geo_full)',
      "cs==='cost'||(ld&&ld.rule==='geo_full')" in SR.replace(' ', ''))
_nc = '\n'.join(l for l in HTML.splitlines() if not l.strip().startswith('//'))  # rendered code only (comments excluded — the b29 lesson)
check("REJECTED Gemini floor attribution «بناءً على الصفقات» absent from rendered strings", 'بناءً على الصفقات' not in _nc)
check('REJECTED fabricated frontage/street wide-range reason absent',
      'الفروقات الهندسية للواجهات' not in HTML and 'وعرض الشوارع' not in SR)

# ── (c) SIGNED §3 n<5 range-only face ──
check('scarce gate = _confN<5 with a valid range', '_confN!=null&&_confN<5&&v.low!=null&&v.high!=null' in SR.replace(' ', ''))
check('scarce hero label «القيمة المتوقّعة بين»', "t('القيمة المتوقّعة بين','Expected value between')" in SR)
_sc = SR[SR.index('if(_scarce){'):SR.index('}else{', SR.index('if(_scarce){'))]
check('scarce branch renders low+high, NOT the central amount',
      'fmt(v.low)' in _sc and 'fmt(v.high)' in _sc and 'fmt(v.amount)' not in _sc)
check('scarce case shows no value chip (range IS the message)', "if(!_scarce)h+='<div class=\"tmk\"" in SR)
check('scarcity guidance retained (b90 #8)', 'لقلّة الصفقات المسجّلة في هذه الشريحة' in SR)

# ── (d) the b90 central-dot facebar survives for the non-skewed case ──
check('facebar kept verbatim in the else branch (b90 pin)',
      '\'<div class="thmr-facebar"><div class="ftrack"><span class="fdot" style="left:\'+_hpct.toFixed(1)+\'%">' in SR)

# ── value-invariance ──
mults = re.findall(r'v\.amount\s*\*\s*([0-9.]+)', SR)
check('value-math = ONLY the 3 disclosed conventions (×0.90/×1.10/×1.30)',
      sorted(set(mults)) == ['0.90', '1.10', '1.30'])
check('no assignment into v.amount/low/high', not re.search(r'v\.(amount|low|high)\s*=[^=]', SR))

# ── version ──
check('ENGINE_VERSION bumped to b92 (format-agnostic)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+b92-", ENG) is not None)
check('SPRINT_TAG dotted-numeric', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+b?\.?\d*", ENG) is not None)

print(f'\n{passed}/{passed+failed} PASS' + ('' if failed == 0 else f' — {failed} FAIL'))
sys.exit(1 if failed else 0)
