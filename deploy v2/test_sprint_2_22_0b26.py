# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.26 — م3 «التقرير الكامل v2» (the D8 surgery + D4 + the PDF-audit fixes).

Isolated checks against the REAL files (Rule #40 / E14):
  D4  — the MUC clause/basis drop the event-dated «اضطراب» anchoring for the
        banner-tied data-recency wording (production regime_muc()).
  D8  — merges: ONE MUC block AFTER the number (ص1+ص9) · ONE «المنهجية والمعايير»
        annex (ص2+ص9) · cost-led decomposition = DIRECT DRC rows (ص3+ص4).
        folds: the empty-ad section · the «حالة أفضل/أدنى» prose when the
        scenarios table answers it · ONE DECLARED rounding.
        keeps: the SIGNED six as NUMBERED annexes.
  PDF — the two blind «الوسيط» labels become leader-aware · the MUC panel reads
        the BROADCAST level · the mixed-pool line becomes the dual-evidence line.

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b26.py
"""
import io
import re
import sys
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  PASS  {name}')
    else:
        FAIL += 1
        print(f'  FAIL  {name}  {detail}')


with open('index.html', encoding='utf-8') as f:
    HTML = f.read()
REP = HTML[HTML.index('function showReport(d){'):HTML.index('function printReportA4(){')]

print('\n[1] D4 — the disruption clause → banner-tied recency (production fns, E14)')
from material_uncertainty import regime_muc
_muc = regime_muc()
_cl = _muc['muc_clause_ar'] or ''
_ba = _muc['muc_basis_ar'] or ''
check('event-dated anchoring GONE from the clause («وما بعده»)', 'وما بعده' not in _cl)
check('«الاضطراب الحالي» GONE from the basis', 'الاضطراب الحالي' not in _ba)
check('the clause anchors on the MoJ latest record (banner basis)',
      'بيانات وزارة العدل المسجَّلة حتى' in _cl and '2025-12-31' in _cl)
check('the neutral verifiable-constraint posture holds (C1)',
      'قيوداً جوهرية على شواهد السوق' in _cl)
check('the basis carries the SAME days-old figure the banner renders',
      str((date.today() - date(2025, 12, 31)).days) in _ba and 'يوماً' in _ba)
check('the basis names the banner («شريط حداثة البيانات»)', 'شريط حداثة البيانات' in _ba)
check('EN mirror anchors on the record date, no event date',
      'records published up to' in (_muc['muc_clause_en'] or '')
      and 'onwards' not in (_muc['muc_clause_en'] or ''))

print('\n[2] PDF fix — leader-aware labels (the two blind «الوسيط»)')
check('label decision present (_midR/_def12R) (b81: labels via t())', "_midR=t('مرتكز التكلفة (أرض + بناء مُهلَك)'," in REP
      and "_def12R=t('القيمة السوقية (الوسيط)'," in REP)
check('the median marker renders the decision, not the literal',
      "'+_midR+' ≈ <strong>'" in REP and 'الوسيط (التقدير المركزي) ≈ <strong>' not in REP)
check('DEF-12 row 1 renders the decision', "'+_def12R+'</span><strong>" in REP)
check('neutral fallback «التقدير المركزي» + the income guard',
      "_midR=t('التقدير المركزي'," in REP and "income_triangulation||{}).mode==='income_led'" in REP)
check('forced-sale basis line de-blinded', 'الأساس: القيمة التقديريّة المركزيّة ×' in REP  # b56 R6: تشكيل
      and 'القيمة السوقية المركزية (الوسيط)' not in REP)

print('\n[3] D8 — ONE MUC block AFTER the number (+ refusal keeps its clause)')
_i_val = REP.find('القيمة السوقية (MV)')
_i_muc = REP.find('_mucCardHtml(m_ar')
check('the MUC card renders AFTER the headline block', 0 <= _i_val < _i_muc)
check('exactly TWO call sites (valued-after-number + refusal)',
      REP.count('_mucCardHtml(m_ar,m_b,m_r)') == 2)
check('the brief MU section is SKIPPED in the report loop (the ص9 merge)',
      "if(sec.id==='material_uncertainty')return;" in REP)

print('\n[4] D8 — ONE «المنهجية والمعايير» annex (ص2+ص9)')
check('the annex header rendered ONCE (comments excluded) (b81: title via t())',
      REP.count("<div class=\"rt\" style=\"margin-bottom:8px\">'+t('المنهجية والمعايير','Methodology and standards')+'</div>") == 1)
check('the a8 standards note lives INSIDE the annex (no early standalone card)',
      REP.find('المنهجية والمعايير') < REP.find('rics_methodology_note_ar'))
check('the brief methodology section captured into the annex + skipped in the loop',
      "find(s=>s&&s.id==='methodology')" in REP and "if(sec.id==='methodology')return;" in REP)

print('\n[5] D8 — cost-led decomposition = DIRECT DRC rows (ص3+ص4)')
check('_decompHtml gated off on cost leadership',
      "if(!(v.leadership&&v.leadership.leader==='cost'))h+=_decompHtml(d,v,hasValuation);" in REP)
check('the direct DRC card on cost-led (land + depreciated building, no residual)',
      'تفكيك المرتكز (أرقام DRC مباشرة)' in REP and '_cR.land_floor' in REP
      and '_cR.building_value' in REP)

print('\n[6] D8 — folds')
check('the empty-ad section folds in the report (screen 4 untouched)',
      "if(sec.id==='flags'&&!(d.active_listings&&d.active_listings.length))return;" in REP
      and 'لا يوجد إعلان مرتبط بهذا التقييم' in HTML)
check('the «حالة أفضل/أدنى» prose folds when the scenarios table answers it',
      'v.condition_note_ar&&!(v.scenarios&&v.scenarios.items' in REP)
check('ONE DECLARED rounding line', 'تدوير موحَّد من المصدر، لا تقريب إضافي في العرض' in REP)

print('\n[7] PDF fix — the mixed-pool line → the dual-evidence line')
check('cost-led → the SIGNED dual line (matched n vs geo n/dispersion + thresholds)',
      'شواهد السوق: مطابق' in REP and '_ldR.matched_n' in REP
      and '_ldR.geo_full_dispersion' in REP and '_tR.matched_min_n' in REP)
check('market-led pool line carries ITS OWN n (bracket_n_36 — no n=3-beside-0.165)',
      'bracket_n_36' in REP)

print('\n[8] PDF fix — the MUC panel reads the BROADCAST level')
check('renderSection MU level prefers material_uncertainty.level from the broadcast',
      "(((window._lastResult||{}).material_uncertainty)||{}).level||c.level" in HTML)

print('\n[9] D8 — the SIGNED six as NUMBERED annexes + the thmr identity')
check('the annex counter defined', "let _axN=0;" in REP and 'ملحق ' in REP)
check('evidence + strata wrapped (skip-safe numbering)',
      '_axWrap(evidencePanelHtml(d,acc))' in REP and '_axWrap(_strataHtml(d))' in REP)
check('known-unknowns + attribution numbered', REP.count('h+=_ax();') >= 2)
check('due_diligence + cap_rate_provenance numbered in the loop',
      "if(sec.id==='due_diligence'||sec.id==='cap_rate_provenance')h+=_ax();" in REP)
check('the report carries the thm-report identity', "o.classList.add('thmr');" in REP)

print('\n[10] version format (R6 / Lesson 2)')
with open('evaluate_unified.py', encoding='utf-8') as fh:
    ENG = fh.read()
check('ENGINE_VERSION format', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)

print(f'\n=== {PASS} passed, {FAIL} failed ===')
sys.exit(1 if FAIL else 0)
