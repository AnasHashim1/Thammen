# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.104 — «تفاصيل تُفتح بنقرة + لغة أوضح» (R2 — the skeptic's proof + clarity).

Inside «عرض التفاصيل» (srFold), b104 adds:
  (1) THE SKEPTIC'S PROOF — the anonymized MoJ keystone comparables (the b38-b41 broadcast rows,
      previously only on the old result screen) rendered in a thmr mini-table right after §١,
      leader-aware header (market «هي مرجع الرقم» / cost-led «اطّلعنا عليها ولم تقُد الرقم»).
  (2) §٧ investor reframe (RICS: a valuer estimates, never advises) — the directive «يستحق التدقيق لا
      الفرح» neutralized to benchmark language + «ليست توصيةً استثماريّة».
  (3) §٨ header register fix «شفافية الدليل — بلا تجميل» → «شفافية الأدلّة».
  (4) hero value count-up micro-delight (~800ms, reduced-motion safe).

VALUE-INVARIANT: display-only; amount/low/high/method/rule untouched; the count-up ends on fmt(amount);
the proof rows are the SAME broadcast v.comparables/v.considered_comparables the engine already gates.
Reads the REAL index.html / evaluate_unified.py (E14). SR = the showShortReport SOURCE.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b104.py
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

# ── (1) the skeptic's proof: keystone comparables inside srFold, after §١ ──
check('proof block reuses the broadcast v.comparables/v.considered_comparables (no new methodology)',
      'const _kc=v.comparables||v.considered_comparables;' in SR and
      'if(_kc&&_kc.rows&&_kc.rows.length&&!_isCondLead){' in SR)   # b113 R6: gated off for a condition-led card (stale cost-led framing); the proof block otherwise unchanged
check('proof header is leader-aware (market «مرجع الرقم» / cost-led «لم تقُد الرقم»)',
      'صفقاتٌ مسجّلة مثل بيتك — هي مرجع الرقم' in SR and
      'اطّلعنا عليها — ولم تقُد الرقم' in SR)
check('proof rows: date · area · price, anonymized, dir=ltr, capped at 6, newest-first',
      "_kc.rows.slice(0,6).forEach(r=>{h+='<tr><td dir=\"ltr\">'+r.date" in SR and
      "class=\"thmr-ptab\"" in SR)
check('proof source line = MoJ + CC BY 4.0 (evidence hierarchy)',
      'المصدر: وزارة العدل' in SR and 'CC BY 4.0' in SR)
check('proof sits inside srFold (after §١, before §٢) — one tap into «عرض التفاصيل»',
      SR.find('id="srFold"') < SR.find('const _kc=v.comparables') < SR.find('الأرقام الثلاثة التي تهمّك'))
check('.thmr-proof / .thmr-ptab CSS present',
      '.thmr-proof{' in HTML and '.thmr-ptab{' in HTML)

# ── (2) §٧ investor reframe (a valuer estimates, never advises) ──
check('§٧ directive tail «يستحق التدقيق لا الفرح» REMOVED',
      'يستحق التدقيق لا الفرح' not in SR)
check('§٧ net-yield 5–6% benchmark KEPT (factual market data)',
      '5–6% صافياً' in SR and 'صافي العائد بعد المصاريف' in SR)
check('§٧ «ليست توصيةً استثماريّة» stated (lawyer persona)',
      'وليست توصيةً استثماريّة' in SR)

# ── (3) §٨ header register fix ──
check('§٨ header = «شفافية الأدلّة» (formal); «— بلا تجميل» dropped',
      "t('شفافية الأدلّة','Evidence transparency')" in SR and 'شفافية الدليل — بلا تجميل' not in SR)

# ── (4) count-up micro-delight ──
check('hero value carries data-countup + id srHeroNum',
      'id="srHeroNum" data-countup="' in SR)
check('_srCountUp defined: ~800ms, reduced-motion no-op, ends on fmt(target)',
      'function _srCountUp(){' in HTML and 'prefers-reduced-motion: reduce' in HTML and
      "el.textContent=fmt(target);" in HTML and 'const dur=800' in HTML)
check('_srCountUp invoked after the QR render in showShortReport',
      '_srCountUp();' in SR)
check('the scarce (n<5) range-only hero keeps its two static figures (no count-up on the range)',
      "data-countup=\"'+v.low" not in SR)

# ── (5) VALUE-INVARIANCE + version ──
_muls = sorted(set(re.findall(r'v\.amount\s*\*\s*[\d.]+', SR)))
check('amount-math = the three disclosed conventions only (×0.90 / ×1.10 / ×1.30)',
      _muls == ['v.amount*0.90', 'v.amount*1.10', 'v.amount*1.30'], str(_muls))
check('the proof + §٧ + §٨ strings are bilingual (t() wrapped)',
      "'Registered sales like yours — the reference behind the number')" in SR and
      "'Indicative market metrics — not an investment recommendation.')" in SR and
      "'Evidence transparency')" in SR)
mv = re.search(r"ENGINE_VERSION\s*=\s*'(thammen-sprint[^']+)'", EU)
check('ENGINE_VERSION is a b-series tag (R6)', bool(mv) and mv.group(1).startswith('thammen-sprint2p22p0b'))
mt = re.search(r"SPRINT_TAG\s*=\s*'(\d+\.\d+\.\d+[a-z0-9.]*)'", EU)
check('SPRINT_TAG is a 2.22.0b-series tag (R6)', bool(mt) and mt.group(1).startswith('2.22.0b.'))

passed = sum(1 for _, ok, _ in results if ok); total = len(results)
for name, ok, detail in results:
    print(('PASS' if ok else 'FAIL') + ' - ' + name + (('  ' + detail) if (not ok and detail) else ''))
print('\n%d/%d checks passed' % (passed, total))
sys.exit(0 if passed == total else 1)
