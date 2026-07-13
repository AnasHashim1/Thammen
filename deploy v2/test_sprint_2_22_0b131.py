# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.131 — «التقرير الكامل اللين» (S8, redesign v2): the FULL report (showReport) leaned
like the short report — 🟢 FRONTEND / VALUE-NEUTRAL (api.py + engine untouched; only the 2 version lines).
Four measured lean items (§20.127 carry-forward + plan line 99):
  (1) GUARD 3 (>5M → licensed valuer) note near the number (mirrors the b129 short-report guard),
  (2) the §10 assumptions register FOLDS (was a flat, always-open .rc wall) — «المفصّل يبقى مفصّلاً»:
      every bullet VERBATIM, only the card becomes a <details class="thmr-fold rep-fold">,
  (3) a de-dup POINTER to the b128 consolidated «الشروط والمنهجيّة» screen (a «الشروط والمنهجيّة الكاملة ›»
      link → openTerms()) in the Methodology & standards annex,
  (4) print self-sufficiency: printReportA4 force-opens #repOut details before window.print() (the b125
      pattern) so the folded register still prints (F1 print parity).
GUARD 1 (basis of value, VPS 2 / IVS 102) already present + KEPT; all compliance kept; nothing deleted.
E14: reads the REAL index.html + evaluate_unified.py."""
import io
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
passed = failed = 0
def check(name, cond, msg=''):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name, ('[' + msg + ']') if msg else '')

# ── isolate showReport() (the full report) and printReportA4() ──
_rs = HTML.find('function showReport(d){')
_re = HTML.find('function printReportA4(){')
RP = HTML[_rs:_re] if (_rs >= 0 and _re > _rs) else ''
PA = HTML[_re:_re + 700] if _re >= 0 else ''
check('showReport() region isolated', bool(RP))
check('printReportA4() region isolated', bool(PA))

# also isolate showShortReport() to prove we did NOT touch the short-report guards
_ss = HTML.find('function showShortReport(d){')
_sse = HTML.find('function _srCountUp(')
if _sse < 0: _sse = HTML.find('function _countUp(')
SR = HTML[_ss:_sse] if (_ss >= 0 and _sse > _ss) else ''

# ═══ (1) GUARD 3 — the >5M → licensed valuer note near the number, in the FULL report ═══
check('>5M guard: if(v.amount>5000000) in showReport', 'if(v.amount>5000000)' in RP)
check('>5M guard uses thmr-legalz box', 'if(v.amount>5000000)h+=\'<div class="thmr-legalz"' in RP)
check('>5M guard AR verbatim', 'للمعاملات فوق ٥ مليون ريال ننصح بالاستعانة بمثمّنٍ معتمد.' in RP)
check('>5M guard EN twin', 'For transactions above QAR 5 million we recommend engaging a certified valuer.' in RP)
# placed near the number (before the DEF-12 reorder block)
check('>5M guard placed before the DEF-12 reorder block',
      RP.find('if(v.amount>5000000)') < RP.find('DEF-12 three-value block leads here')
      and RP.find('if(v.amount>5000000)') > RP.find('النطاق التقديري السوقي'))

# ═══ (2) the §10 assumptions register FOLDS ═══
check('assumptions register is now a <details class="thmr-fold rep-fold">',
      '<details class="thmr-fold rep-fold"><summary>' in RP)
check('fold summary = the assumptions title + chevron',
      "<summary>'+t('الافتراضات والافتراضات الخاصّة (&lrm;RICS VPS 2 / IVS 102&lrm;)" in RP
      and "<span class=\"farr\">▾</span></summary>" in RP)
check('fold closes with </div></details>', '</div></details>' in RP)
# the old always-open flat card wrapper for the register is GONE
check('old flat .rc assumptions card wrapper removed',
      "<div class=\"rc\"><div class=\"rt\" style=\"margin-bottom:8px\">'+t('الافتراضات والافتراضات الخاصّة" not in RP)
# «المفصّل يبقى مفصّلاً» — every bullet stays VERBATIM (nothing deleted)
for phrase in [
    '<b>الحالة والتشطيب:</b>', '<b>الاستخدام:</b>', '<b>نافذة الأدلّة:</b>',
    '<b>مساحة البناء (BUA):</b>', '<b>كلفة الإحلال (RCN):</b>', '<b>الإهلاك:</b>',
    '<b>أساس العمر:</b>', '<b>معايرة الكلفة:</b>', '<b>معدّل الرسملة:</b>']:
    check('assumptions bullet retained: ' + phrase, phrase in RP)

# ═══ (3) the b128 de-dup POINTER (link → openTerms()) in the Methodology annex ═══
check('b128 link «الشروط والمنهجيّة الكاملة ›» present in showReport',
      'الشروط والمنهجيّة الكاملة ›' in RP)
check('b128 link EN twin', 'Full Terms &amp; Methodology ›' in RP)
check('b128 link uses sr-terms + openTerms()',
      "<a class=\"sr-terms\" onclick=\"openTerms()\">'+t('الشروط والمنهجيّة الكاملة ›'" in RP)
check('b128 link sits in the Methodology & standards annex (after the rics-note)',
      RP.find('الشروط والمنهجيّة الكاملة ›') > RP.find('المنهجية والمعايير'))

# ═══ (4) print self-sufficiency — printReportA4 force-opens #repOut details (b125 pattern) ═══
check('printReportA4 queries #repOut details', "querySelectorAll('#repOut details')" in PA)
check('printReportA4 force-opens them (a.open=true)', 'a.open=true' in PA)
check('printReportA4 remembers prior open-state (_wasOpen)', '_wasOpen' in PA)
check('printReportA4 restores after print', 'a.open=_wasOpen[i]' in PA)

# ═══ CSS — the .rep-fold restyle (fold looks like a .rc report card) ═══
check('.rep-fold CSS defined (surface + shadow)',
      '.rep-fold{background:var(--surface)' in HTML and 'box-shadow:var(--sh)' in HTML.split('.rep-fold{')[1][:200])
check('.rep-fold>summary restyled to .rt size (navy 1.1rem)',
      '.rep-fold>summary{color:var(--primary);font-weight:800;font-size:1.1rem' in HTML)

# ═══ GUARD 1 (basis of value) already present + KEPT (not weakened) ═══
check('GUARD 1 basis-of-value kept: «أساس القيمة: القيمة السوقية (RICS VPS 2 / IVS 102)»',
      'أساس القيمة: القيمة السوقية (&lrm;RICS VPS 2 / IVS 102&lrm;)' in RP)

# ═══ COMPLIANCE / VALUE-NEUTRALITY — nothing weakened (R6/Lesson-2) ═══
check('MUC card still rendered (_mucCardHtml)', '_mucCardHtml(' in RP)
check('«ليس تقييماً معتمداً» kept', 'وليس تقييماً معتمداً' in RP)
check('forced-sale «×٠٫٩٠ — ليست تصفية معتمدة» kept',
      'قيمة البيع الجبريّ الإرشاديّة (×٠٫٩٠ — ليست تصفية معتمدة)' in RP)
check('CC BY src-credit clone kept (.src-credit)', "document.querySelector('.src-credit')" in RP)
check('QR verification kept (repQr / _verifyUrl)', 'repQr' in RP and '_verifyUrl(d)' in RP)
# value-neutral: showReport is display-only — it never assigns amount/low/high
check('VALUE-NEUTRAL: no assignment to v.amount in showReport',
      'v.amount=' not in RP)
check('VALUE-NEUTRAL: no assignment to v.low/v.high in showReport',
      'v.low=' not in RP and 'v.high=' not in RP)

# ═══ short report UNTOUCHED — its own b129 guards still there (no bleed) ═══
check('short-report b129 GUARD 1 thmr-basis still present', '<div class="thmr-basis">' in SR)
check('short-report b129 GUARD 3 >5M still present', 'if(v.amount>5000000)' in SR)
check('short-report .legalfull print-only block still present', '<div class="legalfull">' in SR)

# ═══ version bump ═══
check('ENGINE_VERSION -> b131', 'thammen-sprint2p22p0b131-full-report-lean' in ENG)
check('SPRINT_TAG -> 2.22.0b.131', "'2.22.0b.131'" in ENG)

print('\n%d passed, %d failed' % (passed, failed))
import sys; sys.exit(1 if failed else 0)
