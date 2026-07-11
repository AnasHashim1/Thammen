# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.91 — «الشامل proof-first» (full-report cold-evidence surfacing).

Surfaces, in the printable full report (`showReport`), the proof the bank/valuer wants FIRST
(Gemini r5 #9-11): the actual MoJ comparable transactions (b38-b41 keystone `comparables` /
`considered_comparables` + the geo `neighbours` adjustment rows) · the LAND `comparable_grid`
(with its time-normalization percentages) · the area `trend` chart — inserted right after the
DEF-12 numbers, BEFORE the fine-print clusters (proof-first reorder). #10: the unit «م²» lives in
the column HEADER (bare number cells = scannability). #11: adjustment %/×factor in dir=ltr islands
(Rule #25). VALUE-INVARIANT — pure display of the broadcast rows; graceful-absent for thin/non-
attached leaders. Reads the REAL index.html / evaluate_unified.py (E14).

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b91.py
"""
import io, re, sys

def load(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()

HTML = load('index.html')
EU   = load('evaluate_unified.py')

# showReport source region
_m = re.search(r'function showReport\(d\)\{.*?\n\}\n// A4 print path', HTML, re.S)
SR = _m.group(0) if _m else ''
results = []
def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))

# ── (1) the three proof helpers defined + graceful-absent guards ──
check('_repComparables / _repLandGrid / _repTrend defined',
      'function _repComparables(v){' in HTML and 'function _repLandGrid(d){' in HTML and
      'function _repTrend(d){' in HTML)
check('graceful-absent guards (thin/non-attached → render nothing)',
      "const c=v.comparables||v.considered_comparables; if(!c||!(c.rows&&c.rows.length))return '';" in HTML and
      "const g=d.comparable_grid; if(!g||!(g.comparables&&g.comparables.length))return '';" in HTML and
      "const tr=d.trend; if(!tr)return '';" in HTML)

# ── (2) proof-first: the three called in showReport right after DEF-12, before the b55 clusters ──
_order = re.search(r"h\+='</div>';\s*\n\s*// ════ Sprint 2\.22\.0b\.91[^\n]*\n[^\n]*\n[^\n]*\n\s*h\+=_repComparables\(v\);\s*\n\s*h\+=_repLandGrid\(d\);\s*\n\s*h\+=_repTrend\(d\);\s*\n\s*// ════ Sprint 2\.22\.0b\.55", SR)
check('proof-first: repComparables+repLandGrid+repTrend inserted after DEF-12, before the clusters', _order is not None)

# ── (3) #10 — the unit «م²» in the column HEADER (not repeated per cell) ──
check('#10: «م²» + «ر.ق/م²» live in the <th> header (bare number cells)',
      "<th class=\"n\">'+t('المساحة (م²)','Area (m²)')" in HTML and
      "<th class=\"n\">'+t('ر.ق/م²','QAR/m²')" in HTML and
      "<th class=\"n\">'+t('السعر (ر.ق)','Price (QAR)')" in HTML)
check('comparable cells are bare fmt() numbers in dir=ltr',
      "<td class=\"n\" dir=\"ltr\">'+fmt(r.area_m2)+'</td><td class=\"n\" dir=\"ltr\">'+fmt(r.total_price)" in HTML)

# ── (4) #11 — adjustments in dir=ltr islands (geo neighbours ×factor + land-grid %) ──
check('#11: geo neighbours ×factor rendered in a dir=ltr island',
      "<td class=\"n\" dir=\"ltr\">×'+r.adjustment_factor+'</td>" in HTML and
      "const nb=c.neighbours;" in HTML)
check('#11: land-grid time-adjustment % in a dir=ltr island (pct_display, +/− signed)',
      "r.adjustments.map(a=>(a.pct_display>=0?'+':'')+a.pct_display+'%').join(' ')" in HTML and
      "<td class=\"n\" dir=\"ltr\">'+adj+'</td>" in HTML)

# ── (5) trend chart (reliably broadcast) reuses the .trend-row markup + honest suppressed path ──
check('trend chart: .trend-col bars from tr.years + labels + suppressed/label note',
      "const ys=tr.years||[];" in HTML and 'class="trend-col"' in HTML and
      "if(tr.suppressed_reason_ar)" in HTML and "esc(tr.label)" in HTML)

# ── (6) CSS + CC BY attribution + de-emoji ──
check('.rep-comp table CSS present (header unit, bare-number columns)',
      '.rep-comp{' in HTML and '.rep-comp th{' in HTML and '.rep-comp th.n,.rep-comp td.n{text-align:left' in HTML)
check('CC BY 4.0 attribution on both new proof tables (E10)',
      'المصدر: وزارة العدل عبر بوابة قطر للبيانات المفتوحة — ' in HTML and
      'المصدر: وزارة العدل — ' in HTML and
      HTML.count('<span dir="ltr">CC BY 4.0</span>') >= 5)  # 3 existing + the 2 new proof tables
check('de-emoji: proof surfaces use <use href=#ic-clipboard|#ic-chart>, no emoji',
      '#ic-clipboard' in HTML and '#ic-chart' in HTML)

# ── (7) VALUE-INVARIANCE: the helpers add no v.amount math; DEF-12 3 conventions untouched ──
# b125 R6: the S4b section builders (_s4bEvidence/_s4bViz/…) were inserted between _repTrend and
# showReport; the b91 proof helpers end at the first S4b helper. The _s4bViz estimate-position bar
# derives a DISPLAY ppm² (v.amount / area) — a broadcast-field ratio, NOT a value mutation — so it is
# legitimately outside this slice. Narrow the slice to the b91 proof helpers as intended.
_help = HTML[HTML.find('function _repComparables(v){'):HTML.find('function _s4bTrendSpark(d){')]
check('the proof helpers introduce NO v.amount arithmetic (pure display of broadcast rows)',
      'v.amount' not in _help)
_sr_muls = sorted(set(re.findall(r'v\.amount(?:\|\|0)?\)?\s*\*\s*[\d.]+', SR)))
check('showReport amount-math unchanged (only the ×0.90 forced-sale convention; helpers add none)',
      _sr_muls == ['v.amount||0)*0.90'], str(_sr_muls))

# ── (8) EN + version ──
check('proof strings are bilingual (t() wrapped)',
      "'Comparable transactions (Ministry of Justice)')" in HTML and
      "'Area trend')" in HTML and "'Comparable land sales + adjustments')" in HTML)
mv = re.search(r"ENGINE_VERSION\s*=\s*'(thammen-sprint[^']+)'", EU)
check('ENGINE_VERSION is a b-series tag (R6, version-agnostic)', bool(mv) and mv.group(1).startswith('thammen-sprint2p22p0b'))
mt = re.search(r"SPRINT_TAG\s*=\s*'(\d+\.\d+\.\d+[a-z0-9.]*)'", EU)
check('SPRINT_TAG is a 2.22.0b-series tag (R6)', bool(mt) and mt.group(1).startswith('2.22.0b.'))

passed = sum(1 for _, ok, _ in results if ok); total = len(results)
for name, ok, detail in results:
    print(('PASS' if ok else 'FAIL') + ' - ' + name + (('  ' + detail) if (not ok and detail) else ''))
print('\n%d/%d checks passed' % (passed, total))
sys.exit(0 if passed == total else 1)
