# -*- coding: utf-8 -*-
# Sprint 2.22.0b.55 — Full-report note-clustering «رشاقة التقرير الكامل».
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only).
# Reads the REAL index.html (E14 / Rule #40 for the frontend lane) + asserts the engine bump.
#
# The declutter contract (PO «الكامل الآن، المختصر لاحقاً», §20.84):
#   - The ~12 fine-print notes that used to stack as a FLAT WALL under the DEF-12 block in
#     showReport() are GROUPED into 3 LABELED clusters:
#       «حول الرقم»    (cNum)  — leadership verdict · old-stock re-anchor · cost-triangulation · value-floor
#       «حول العقار»   (cProp) — condition · age-honesty · re-survey · age-sensitivity · HBU
#       «حول البيانات» (cData) — dual-evidence / dispersion pool · moj registered-sales sample
#   - VALUE-INVARIANT: every note string + condition is VERBATIM (a buffer-prefix swap, the b31/b52
#     pattern); nothing deleted, no figure touched, NO compliance line removed.
#   - The SHORT report (showShortReport) is DEFERRED this sprint (untouched — the b55 mockup is not
#     on disk and the short report is governed by the b28 PDF print contract).
import re, pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG  = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

# slice the showReport function so cluster assertions can't accidentally match show()/showShortReport.
REP  = HTML[HTML.index('function showReport(d){'):HTML.index('function printReportA4(')]
SR   = HTML[HTML.index('function showShortReport(d){'):HTML.index('function show(d){')]

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── 1. The 3 labeled clusters exist (buffers + emit helper + labels + CSS) ──
check('cluster buffers declared', "let cNum='', cProp='', cData='';" in REP)
check('_repCl labeled-wrapper helper',
      "const _repCl=(lbl,body)=>body?('<div class=\"rep-cl\"><div class=\"rep-cl-h\">'+lbl+'</div>'+body+'</div>'):'';" in REP)
check('clusters emitted in order number→property→data (b81: labels wired via t())',
      "h+=_repCl(t('حول الرقم','About the number'),cNum)+_repCl(t('حول العقار','About the property'),cProp)+_repCl(t('حول البيانات','About the data'),cData);" in REP)
check('label «حول الرقم»',   "_repCl(t('حول الرقم','About the number'),cNum)" in REP)
check('label «حول العقار»',  "_repCl(t('حول العقار','About the property'),cProp)" in REP)
check('label «حول البيانات»', "_repCl(t('حول البيانات','About the data'),cData)" in REP)
check('.rep-cl / .rep-cl-h CSS present', '.rep-cl{' in HTML and '.rep-cl-h{' in HTML)
check('.rep-cl print page-break protected', '.rep-cl { page-break-inside: avoid; }' in HTML)

# ── 2. «حول الرقم» (cNum): leadership · OSR · cost-triangulation · value-floor ──
check('cNum <- leadership.note_ar', "v.leadership.note_ar){cNum+=" in REP)
check('cNum <- old_stock_reanchor', "v.old_stock_reanchor.note_ar)cNum+=" in REP)
check('cNum <- cost_triangulation', "v.cost_triangulation.note_ar)cNum+=" in REP)
check('cNum <- value_floor land-floor (b81: via pick)',
      "cNum+='<div class=\"rn\" style=\"margin-top:8px;font-size:.76rem\">'+pick(vfR,'land_floor_note')" in REP)

# ── 3. «حول العقار» (cProp): condition · age-honesty · re-survey · age-sensitivity · HBU ──
check('cProp <- condition_note (still folds on scenarios)', "v.scenarios.items.length>1))cProp+=" in REP)
check('cProp <- age_honesty', "v.leadership.age_honesty_note_ar){cProp+=" in REP)
check('cProp <- resurvey', "v.leadership.resurvey_note_ar){cProp+=" in REP)
check('cProp <- age_sensitivity (b18 §A1)', "v.age_sensitivity&&v.age_sensitivity.note_ar)cProp+=" in REP)
check('cProp <- hbu', "v.hbu_note_ar)cProp+=" in REP)

# ── 4. «حول البيانات» (cData): dual-evidence / dispersion pool · moj sample ──
check('cData <- dual-evidence (cost-led) (b81: AR moved into t())',
      "</use></svg> '+t('شواهد السوق: مطابق ','Market evidence: matched ')" in REP)
check('cData <- dispersion (market-led) (b81: AR moved into t())',
      "</use></svg> '+t('حوض المقارنات: وسيط ','Comparables pool: median ')" in REP)
check('cData <- moj sample-size (cite-n) (b81: AR moved into t())',
      "if(d.moj_sample_size)cData+='<div class=\"rn\" style=\"margin-top:8px;font-size:.78rem\">'+t('صفقات البيع المسجلة لعقارات مشابهة: '" in REP)

# ── 5. NO note lost — none of the moved notes still uses the old flat h+= buffer ──
check('age-sensitivity no longer flat h+= (-> cProp)', "v.age_sensitivity&&v.age_sensitivity.note_ar)h+=" not in REP)
check('moj sample-size no longer flat h+= (-> cData)', "if(d.moj_sample_size)h+=" not in REP)
check('old_stock_reanchor no longer flat h+= (-> cNum)', "v.old_stock_reanchor.note_ar)h+=" not in REP)
check('hbu no longer flat h+= (-> cProp)', "v.hbu_note_ar)h+=" not in REP)
check('cost_triangulation no longer flat h+= (-> cNum)', "v.cost_triangulation.note_ar)h+=" not in REP)

# ── 6. Placement: the clusters render AFTER the DEF-12 lead block, BEFORE the one MUC card ──
check('clusters after DEF-12 block opens',
      REP.index("h+=_repCl(t('حول الرقم','About the number'),cNum)") > REP.index("h+='<div class=\"rep-def12\">';"))
check('clusters before the MUC card',
      REP.index("h+=_repCl(t('حول الرقم','About the number'),cNum)") < REP.index('_mucCardHtml(m_ar,m_b,m_r)'))

# ── 7. COMPLIANCE / honesty UNTOUCHED (kept, b26/b51 — one each, never deleted) ──
check('ONE MUC clause after the number (_mucCardHtml)', '_mucCardHtml(m_ar,m_b,m_r)' in REP)
check('source attribution kept (src-credit cloned)', 'src-credit-rep' in REP)
check('«ليس تقييماً معتمداً» footer kept', 'تقييم سوقيّ آليّ وليس تقييماً معتمداً' in REP)
check('forced-sale «ليست تقييم تصفية معتمداً» kept', 'ليست تقييم تصفية معتمداً' in REP)
check('GT hook (info@thammen.qa) kept', 'info@thammen.qa' in REP)
check('DEF-12 three-value block still leads (b51)',
      'rep-def12' in REP and "h+='<div class=\"rep-def12\">';" in REP)
check('RICS/IVS methodology note kept', 'rics_methodology_note_ar' in REP)
check('product identity «تقييم سوقيّ آليّ» kept (b54)', 'تقييم سوقيّ آليّ' in REP)

# ── 8. VALUE-INVARIANCE — showReport does not mutate v.amount/v.low/v.high ──
check('no mutation of v.amount/v.low/v.high in the report', not re.search(r'\bv\.(amount|low|high)\s*=[^=]', REP))

# ── 9. The SHORT report is DEFERRED this sprint (untouched) ──
check('short report still two-page (srPage1 + srPage2)', 'id="srPage1"' in HTML and 'id="srPage2"' in HTML)
check('short report did NOT get clusters (deferred)', 'rep-cl' not in SR)

# ── 10. Engine version (format only — R6 / Lesson-2: no exact pin) ──
check('ENGINE_VERSION format (thammen-sprint…)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('engine at/beyond b55 (b54 tag gone)', 'thammen-sprint2p22p0b54' not in ENG)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
