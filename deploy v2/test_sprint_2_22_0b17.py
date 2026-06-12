# -*- coding: utf-8 -*-
# Sprint 2.22.0b.17 — Screen 5: the full report + DEF-12. FRONTEND-ONLY, value-invariant
# (engine = the 2 version-string lines). Reads the REAL index.html (E14 / Rule #40 frontend lane).
# Verifies: the report screen + §3 structure order, DEF-12 math/label (report-only), the shared
# builders (one b14-coherent voice with screen 4), attribution/footer/GT-hook presence, the A4
# print path, and that screen 4 lost nothing in the extraction.
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── the screen + entry ──
check('reportScreen markup present (screen 5)', 'id="reportScreen"' in HTML and 'التقرير الكامل</div>' in HTML)
check('openReport() renders from window._lastResult (no re-fetch)',
      'function openReport(){const d=window._lastResult; if(!d)return; showReport(d); go(\'report\');}' in HTML)
# Sprint 2.22.0b.25 (م2/D6) re-point: the TIER-3 CTA now opens the SHORT report FIRST
# (openShortReport); the full report stays one click away INSIDE it (its «التقرير
# الكامل» button → openReport). The b17 invariant becomes: openReport remains wired
# and reachable, and the dead printReport CTA never returns.
check('TIER-3 report CTA → short-first (D6), full report one click away (b17 path intact)',
      'onclick="openShortReport()">📄 التقرير المختصر' in HTML
      and 'onclick="openReport()">التقرير الكامل' in HTML
      and 't3-secondary" onclick="printReport()"' not in HTML)

# ── shared builders: ONE voice across screens 4 + 5 (b14 coherence) ──
for fn in ['_mucFields', '_mucCardHtml', '_decompHtml', '_substHtml', '_strataHtml']:
    check('shared builder %s defined once' % fn, HTML.count('function %s(' % fn) == 1)
check('show() uses the shared decomposition builder', 'h+=_decompHtml(d,v,hasValuation);' in HTML)
check('show() uses the shared substantiality builder', 'h+=_substHtml(d,v,hasValuation);' in HTML)
check('show() uses the shared strata builder', 'h+=_strataHtml(d);' in HTML)
check('show() uses the shared MUC builder', 'muc+=_mucCardHtml(muc_ar,muc_basis,muc_review);' in HTML)
# screen 4 lost nothing: the builders carry the original inner content verbatim.
check('decomposition inner content intact (builder)', 'تفكيك القيمة (أرض + بناء)' in HTML
      and 'قيمة البناء الضمنية' in HTML)
check('strata inner content intact (builder)', 'تصنيف المخزون (Stock Stratification)' in HTML
      and 'الفئة المسيطرة:' in HTML)
check('10-Year regime inner content intact (builder)', 'قاعدة الـ 10 سنوات (السوق القطري)' in HTML)

# ── report structure order — Sprint 2.22.0b.26 (م3/D8 — signed) re-point: the MUC
#    block MOVED to AFTER the number (ص1+ص9 merged into ONE block after the headline);
#    the rest of the b17 spine holds (cover → headline/DEF-12 → MUC → evidence →
#    decomp → strata → basis → methodology/sources → audience → footer). ──
rep = HTML[HTML.index('function showReport(d){'):HTML.index('function printReportA4(){')]
order = ['rep-cover', 'القيمة السوقية (MV)', 'rep-def12', '_mucCardHtml(m_ar',
         'evidencePanelHtml(d,acc)', '_decompHtml(d,v,hasValuation)', '_strataHtml(d)',
         'بيانات العقار الأساسية', 'src-credit', 'renderSection(sec)', 'rep-foot']
idx = [rep.find(t) for t in order]
check('report §3 structure order correct (D8: MUC after the number)',
      all(i >= 0 for i in idx) and idx == sorted(idx))

# ── DEF-12 (report-only; display math ×0.90; verbatim label) ──
check('DEF-12 math = Math.round(amount*0.90)', 'Math.round((v.amount||0)*0.90)' in rep)
check('DEF-12 two rows (MV + forced-sale)', 'القيمة السوقية (الوسيط)' in rep
      and 'قيمة البيع الجبري الإرشادية' in rep)
check('DEF-12 verbatim convention label', 'قيمة بيع جبري إرشادية (عُرف سوقي ×<span dir="ltr">0.90</span>) — ليست تقييم تصفية معتمداً.' in rep)
check('DEF-12 is REPORT-ONLY (not in show())',
      'البيع الجبري' not in HTML[HTML.index('function show(d){'):HTML.index('// Sprint D: Section renderer')])

# ── compliance + footer ──
check('report clones the a25 attribution at runtime (no copy duplication)',
      "document.querySelector('.src-credit')" in rep and '_srcNode.innerHTML' in rep)
check('report footer: not-certified + a20 status appended', 'تقدير سوقي آلي وليس تقييماً معتمداً' in rep
      and 'rics_compliant_status_ar' in rep)
check('report footer: engine version + timestamp', "d.engine_version||''" in rep and 'toISOString()' in rep)
check('GT hook line + the Terms WhatsApp channel', 'شاركه لتحسين الدقّة' in rep and '+974 70177761' in rep)
check('staleness banner on the cover', 'data_freshness' in rep and 'dfc s-' in rep)
check('b16 OSR + cost notes carried into the report', 'old_stock_reanchor' in rep and 'cost_triangulation' in rep)
check('refusal path: honest reason, no value report', 'لا يصدر تقرير قيمة' in rep)

# ── A4 print path ──
check('@page A4 rule present', '@page { size: A4; margin: 12mm; }' in HTML)
check('printing-report class shows the report screen alone',
      'body.printing-report .screen { display: none !important; }' in HTML
      and 'body.printing-report #reportScreen { display: block !important; }' in HTML)
check('printReportA4 adds/removes the class', "classList.add('printing-report')" in HTML
      and "classList.remove('printing-report')" in HTML)
check('DEF-12/cover/footer page-break protected', '.rep-def12, .rep-cover, .rep-foot { page-break-inside: avoid; }' in HTML)

# ── engine version (format only — R6/Lesson-2) ──
check('ENGINE_VERSION format', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
