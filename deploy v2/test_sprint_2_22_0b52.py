# -*- coding: utf-8 -*-
# Sprint 2.22.0b.52 — Result-screen LEAN (PO-signed «A + B: full lean»).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only).
# Reads the REAL index.html (E14 / Rule #40 for the frontend lane) + asserts the engine bump.
#
# The lean contract (PO directive: "make the website lean + methodological; the DETAILED
# report stays detailed"):
#   - KEEP always-visible on TIER-1 (decision-relevant): the figure + range-as-lead + the MUC
#     LEVEL chip + «ليس تقييماً معتمداً» + the evidence one-row + the condition note.
#   - MOVE the appraiser fine-print OFF always-visible TIER-1 into the «كيف وصلنا» fold (`how`):
#     age-sensitivity + moj sample-size (cite-n) + the methodology bare line.
#   - FOLD the FULL MUC legal clause behind its chip (_mucFold) instead of always-visible —
#     the clause is STILL BUILT (not deleted), one click away.
#   - The full/detailed REPORT (showReport) is untouched by this lean pass.
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── 1. Appraiser fine-print moved OFF always-visible TIER-1 → into the «كيف وصلنا» fold (`how`) ──
check('age-sensitivity → how (NOT t1)',
      'v.age_sensitivity&&v.age_sensitivity.note_ar){how+=' in HTML
      and 'v.age_sensitivity&&v.age_sensitivity.note_ar){t1+=' not in HTML)
check('moj sample-size (cite-n) → how (NOT always-visible)',
      "how+='<div class=\"rn\" style=\"margin-top:8px;font-size:.78rem\">صفقات البيع المسجلة لعقارات مشابهة:" in HTML)
check('methodology bare line → how (NOT always-visible)',
      "margin:10px 0 0;font-size:.78rem;color:#666;line-height:1.5\">'+d.methodology_ar" in HTML)

# ── 2. The FULL MUC legal clause folds behind its chip via _mucFold (was always-visible) ──
check('_mucFold collapses the full clause via _acc(…, muc, false)',
      'const _mucFold = muc ? _acc(' in HTML and ', muc, false) : \'\';' in HTML)
check('valued assembly folds MUC: head+alerts+t1+_mucFold+t2+t3+foot',
      'h=head+alerts+t1+_mucFold+t2+t3+foot;' in HTML)
check('full MVU clause STILL built via _mucCardHtml (not deleted)',
      'muc+=_mucCardHtml(muc_ar,muc_basis,muc_review);' in HTML)

# ── 3. The DECISION-relevant compliance signposts STAY always-visible in TIER-1 ──
check('MUC level chip STAYS in TIER-1 (amber token + level text)',
      "t1+='<div style=\"display:inline-block;padding:3px 10px;background:var(--warn-bg);color:var(--warn);" in HTML
      and " تحفظ مادي: '+MUC_LEVEL_AR[mu.level]+'</div>';" in HTML)
check('«ليس تقييماً معتمداً» STAYS in TIER-1 (a20 status appended)',
      "t1+='<div class=\"rn\" style=\"margin-top:10px;font-size:.82rem;color:#8a6d3b;background:#fcf8e3" in HTML
      and 'تقييم سوقيّ آليّ — ليس تقييماً معتمداً' in HTML  # b54 R6: تقدير→تقييم (identity lock)
      and '_statusAr' in HTML)
check('evidence one-row STAYS in TIER-1', 't1+=_evOneRow(d);' in HTML)
check('condition note STAYS on TIER-1 (decision-relevant)', 'if(v.condition_note_ar){t1+=' in HTML)
check('range-as-lead headline retained', 'النطاق التقديري السوقي' in HTML)

# ── 4. The DETAILED report (showReport) still renders the detail — b55 R6: the fine-print notes
#       moved from the flat h+= wall into LABELED clusters (cProp/cData); nothing deleted, just grouped.
check('report still renders age-sensitivity (b55: «حول العقار» cluster, cProp+=)',
      "v.age_sensitivity&&v.age_sensitivity.note_ar)cProp+=" in HTML)
check('report still renders moj sample-size (b55 cluster cData+=; b81: AR in t())',
      "if(d.moj_sample_size)cData+='<div class=\"rn\" style=\"margin-top:8px;font-size:.78rem\">'+t('صفقات البيع المسجلة لعقارات مشابهة: '" in HTML)

# ── 5. VALUE-INVARIANCE — show() does not touch v.amount/v.low/v.high ──
check('no mutation of v.amount/v.low/v.high', not re.search(r'\bv\.(amount|low|high)\s*=[^=]', HTML))

# ── 6. Engine version (format only — R6 / Lesson-2: no exact pin) ──
check('ENGINE_VERSION format (thammen-sprint…)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format',
      re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('engine at/beyond b52 (b50 tag gone)', 'thammen-sprint2p22p0b50' not in ENG)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
