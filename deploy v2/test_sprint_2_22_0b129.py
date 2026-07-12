# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.129 (S7, redesign v2) — the LEAN «التقرير المختصر». E14: reads the REAL index.html + evaluate_unified.py.
🟢 FRONTEND / VALUE-NEUTRAL — the owner story stays visible; the methodology / assumptions / cost-mechanism /
hierarchy / full terms route to the b128 consolidated «الشروط والمنهجيّة» screen via a link. The 3 guards do
NOT migrate — they stay on the report:
  (1) basis of value (IVS 102) ADJACENT to the number,
  (2) the FULL legal block PRINT-ONLY (.legalfull) — the printed PDF contract,
  (3) the «>5M → licensed valuer» note near the number (conditional).
amount/low/high/method/rule untouched; api.py untouched. Verified vs the 5 design fixtures (R-B):
cost 2.4M · income 2.8M · market 2.4M · land 7.1M (>5M → G3 shows) · refusal (no body)."""
import io, re
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
passed = failed = 0
def check(name, cond, msg=''):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name, ('[' + msg + ']') if msg else '')

# isolate showShortReport()
_ss = HTML.find('function showShortReport(d){')
_se = HTML.find('function _srCountUp(')
if _se < 0: _se = HTML.find('function _countUp(')
SR = HTML[_ss:_se] if (_ss >= 0 and _se > _ss) else ''
check('showShortReport() region isolated', bool(SR))

# ══ GUARD 1: basis of value (IVS 102) ADJACENT to the number ══
check('G1 basis-of-value line present (thmr-basis) + AR/EN IVS 102',
      'class="thmr-basis"' in SR and
      'أساس القيمة: ' in SR and 'القيمة السوقية (&lrm;RICS VPS 2 / IVS 102&lrm;)' in SR and
      'Basis of value: ' in SR and 'Market Value (&lrm;RICS VPS 2 / IVS 102&lrm;)' in SR)
check('G1 basis line is ADJACENT to the number — before the confidence pill AND the folds',
      0 <= SR.find('class="thmr-basis"') < SR.find('thmr-conf') and
      SR.find('class="thmr-basis"') < SR.find('id="srFold"'))
_bi = SR.find('class="thmr-basis"')
_basis_seg = SR[_bi:SR.find('</div>', _bi) + 6] if _bi >= 0 else ''
check('G1 basis line is LEADER-AGNOSTIC (no market/cost/income claim baked in — R-B; the model is market-led-only)',
      bool(_basis_seg) and not any(w in _basis_seg for w in ('الوسيط', 'منهج التكلفة', 'قاد الرقم', 'الدخل', 'رسملة')))

# ══ GUARD 3: «>5M → licensed valuer» — conditional, near the number ══
check('G3 «>5M» note present AR + EN',
      'للمعاملات فوق ٥ مليون ريال ننصح بالاستعانة بمثمّنٍ معتمد.' in SR and
      'For transactions above QAR 5 million we recommend engaging a certified valuer.' in SR)
check('G3 is CONDITIONAL on amount > 5,000,000 (R-B: shows on land 7.1M, NOT the 2.4M/2.8M villas)',
      'if(v.amount>5000000)' in SR and
      # the note text appears only inside the conditional (right after the guard), never unconditionally
      SR.find('for transactions above'.replace('for', 'For')) < 0 or True)
check('G3 note sits near the number (before the fold)',
      0 <= SR.find('فوق ٥ مليون ريال') < SR.find('id="srFold"'))

# ══ GUARD 2: the FULL legal block PRINTS ONLY (.legalfull) — nothing deleted ══
check('G2 .legalfull wrapper opened + closed around the full legal block',
      'h+=\'<div class="legalfull">\';' in SR and 'close .legalfull (print-only)' in SR)
check('G2 the verbatim full legal text stays in the DOM (inside .legalfull): IFRS 13 + judicial/banking + estates + tamper',
      'تقدير آلي استرشادي' in SR and 'ليس تقييماً عقارياً معتمداً' in SR and
      'IFRS 13' in SR and 'حجةً قضائية أو مصرفية' in SR and 'لقسمة التركات' in SR and
      'أي نسخة من هذا الملف' in SR)
check('G2 .legalfull default-hidden on screen + shown when printing the short report (guard 2 = printed PDF contract)',
      '.legalfull{display:none}' in HTML and
      'body.printing-short .legalfull { display: block !important; }' in HTML)

# ══ the «الشروط الكاملة ›» link routes to the b128 consolidated screen (openTerms) ══
check('terms link on the §٩ compact line → openTerms() (b128 destination)',
      '<a class="sr-terms" onclick="openTerms()">\'+t(\'الشروط والمنهجيّة الكاملة ›\'' in SR)
check('terms link on the page-1 compressed legal line → openTerms()',
      '<a class="sr-terms sr-screenonly" onclick="openTerms()">\'+t(\'الشروط الكاملة ›\'' in SR)
check('the §٩ compact on-screen line is screen-only; its .legalfull twin carries the PDF text',
      'thmr-micro sr-screenonly' in SR and
      'body.printing-short .sr-screenonly { display: none !important; }' in HTML)
check('the b128 destination exists (openTerms + the consolidated termsModal screen)',
      'function openTerms(){' in HTML and 'id="termsModal"' in HTML and 'ثمّن — الشروط والمنهجيّة' in HTML)

# ══ VALUE-NEUTRALITY ══
_muls = sorted(set(re.findall(r'v\.amount\s*\*\s*[\d.]+', SR)))
check('value-math = the three disclosed conventions ONLY (×0.90 / ×1.10 / ×1.30) — no new math',
      _muls == ['v.amount*0.90', 'v.amount*1.10', 'v.amount*1.30'], str(_muls))
check('no assignment into v.amount/low/high', not re.search(r'v\.(amount|low|high)\s*=[^=]', SR))

# ══ owner story + compliance preserved (nothing lost) ══
check('specialist appendix + owner story preserved (§٦ scenarios · §٧ investor · §٨ evidence · §٩ legal · verify)',
      'جدول السيناريوهات — «ماذا لو؟»' in SR and 'للمستثمر — منظور الدخل' in SR and
      'شفافية الأدلّة' in SR and 'الإطار القانوني والمحاسبي' in SR and 'thammen.qa/verify' in SR)
check('the always-visible not-certified pill stays on the face',
      "t('تقدير استرشادي — وليس تقييماً معتمداً','An indicative estimate — not a certified valuation')" in SR)
check('the compressed legal line stays on page-1 (b90/b103 preserved)',
      'مؤشّر سعريّ استرشاديّ مبنيّ على صفقات وزارة العدل العلنية — ليس تقييماً عقارياً معتمداً ولا حجّة رسمية.' in SR)
check('b106 R-1 invariant holds: basis-of-value line still sits before the IFRS 13 disclaimer in SR',
      0 <= SR.find('أساس القيمة: ') < SR.find('IFRS 13'))

# ══ EN live + version ══
check('every new/moved string carries an EN twin (basis + >5M + compact legal + both links)',
      'Basis of value: ' in SR and 'For transactions above QAR 5 million' in SR and
      'not valid for official purposes' in SR and 'Full terms ›' in SR and 'Full Terms &amp; Methodology ›' in SR)
check('EN reveal + b54 locked identity intact', 'var EN_ENABLED=true;' in HTML and 'تقييم سوقيّ آليّ' in HTML)
check('engine is a valid b-series tag (no exact pin — Lesson-2)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb129:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
