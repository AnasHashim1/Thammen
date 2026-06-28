# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.81 — EN wiring of the FULL report (showReport, #repOut).
E14: reads the REAL index.html + evaluate_unified.py. FRONTEND-ONLY / VALUE-INVARIANT —
the EN render is dormant behind EN_ENABLED (b77); in AR mode t() returns the first (AR)
arg and pick() returns the *_ar field, so the AR output is byte-identical (asserted by the
verbatim-AR-literal checks below). Runtime render = R14 Chromium (AR byte-identical + forced
EN: dir-flip on #repOut only, short report #srOut + result screen unaffected, no overflow,
0 console).

SCOPE (b81): showReport's OWN body (literals -> t(), engine *_ar -> pick()) + the legal
block (_mucFields/_mucCardHtml, handoff-named) + the inline map reads (TIER_LABEL/ASSET) +
the scoped #repOut LTR CSS. The big SHARED result-family builders (_decompHtml/_substHtml/
_strataHtml/evidencePanelHtml/renderSection/pbRows) are DEFERRED to the b83/show pass — they
stay AR-fallback in EN (byte-identical AR regardless); this test asserts they remain CALLED."""
import io
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

# ---- (1) TIER_LABEL_EN map (EN tier labels; AR build never reads it) + showReport selects it ----
check('TIER_LABEL_EN map defined (dormant EN tier labels)',
      "const TIER_LABEL_EN={" in HTML and
      "'indicative_estimate':   'Indicative estimate'" in HTML and
      "'signed_valuation':      'Signed valuation'" in HTML)
check('showReport selects TIER_LABEL by LANG',
      "(LANG==='en'?TIER_LABEL_EN:TIER_LABEL_AR)[d.tier_label]" in HTML)

# ---- (2) wiring structure: representative t('<AR>','<EN>') pairs (pins AR byte-identity) ----
check('cover brand + subtitle wired',
      "t('ثمّن','Thammen')" in HTML and
      "t(' — تقييم سوقيّ آليّ للعقار',' — Automated market property valuation')" in HTML)
check('cover meta labels wired (cadastral / district / date)',
      "t('الرقم المساحي: ','Cadastral no.: ')" in HTML and
      "t('المنطقة: ','District: ')" in HTML and
      "t('التاريخ: ','Date: ')" in HTML)
check('headline labels wired (MV title / range / estimated value)',
      "t('القيمة السوقية (MV)','Market value (MV)')" in HTML and
      "t('النطاق التقديري السوقي','Estimated market range')" in HTML and
      "t('القيمة التقديرية','Estimated value')" in HTML)
check('leader-aware central labels wired (cost / market / central)',
      "t('مرتكز التكلفة (أرض + بناء مُهلَك)','Cost anchor (land + depreciated building)')" in HTML and
      "t('الوسيط (التقدير المركزي)','Median (central estimate)')" in HTML and
      "t('التقدير المركزي','Central estimate')" in HTML)
check('DEF-12 three-numbers bridge wired',
      "estimate of your home" in HTML and
      "t('ثلاثة أرقام: تقديرُنا لقيمة بيتك" in HTML)
check('b55 cluster labels wired',
      "t('حول الرقم','About the number')" in HTML and
      "t('حول العقار','About the property')" in HTML and
      "t('حول البيانات','About the data')" in HTML)
check('cost-led decomposition card + scenarios title wired',
      "t('تفكيك المرتكز (أرقام DRC مباشرة)','Anchor breakdown (direct DRC figures)')" in HTML and
      "t('سيناريوهات الحالة والتشطيب','Condition and finish scenarios')" in HTML)
check('property-basics section + labels wired',
      "t('بيانات العقار الأساسية','Property basics')" in HTML and
      "ri(t('العنوان','Address')" in HTML and
      "ri(t('مساحة الأرض','Plot area')" in HTML)
check('asset label routed through ASSET_AR/ASSET_EN via t() (b80 map reused)',
      "t(ASSET_AR[d.asset_type]||d.asset_type,ASSET_EN[d.asset_type]||d.asset_type)" in HTML)
check('m2 unit + QAR currency wired',
      "t(' م²',' m²')" in HTML and "t(' ر.ق',' QAR')" in HTML)
check('methodology annex + RICS note header wired',
      "t('المنهجية والمعايير','Methodology and standards')" in HTML and
      "t('ℹ معايير &lrm;RICS / IVS&lrm;','ℹ &lrm;RICS / IVS&lrm; standards')" in HTML)
check('footer not-certified + report-no + verify-link + GT hook wired',
      "t('تقييم سوقيّ آليّ وليس تقييماً معتمداً','An automated market valuation, not a certified valuation')" in HTML and
      "t('رقم التقرير: ','Report no.: ')" in HTML and
      "t('تحقّق من صحّة التقرير ','Verify this report ')" in HTML and
      "share a documented sale price or a certified valuation for this property — email " in HTML)
check('appendix label wired (_ax)', "t('ملحق ','Appendix ')" in HTML)

# ---- (3) engine *_ar reads swapped to pick() in showReport (guards still read .*_ar -> AR byte-identical) ----
for label, needle in [
    ('leadership note',          "pick(v.leadership,'note')"),
    ('old-stock note',           "pick(v.old_stock_reanchor,'note')"),
    ('cost-triangulation note',  "pick(v.cost_triangulation,'note')"),
    ('value-floor land note',    "pick(vfR,'land_floor_note')"),
    ('condition note',           "pick(v,'condition_note')"),
    ('age-honesty note',         "pick(v.leadership,'age_honesty_note')"),
    ('resurvey note',            "pick(v.leadership,'resurvey_note')"),
    ('age-sensitivity note',     "pick(v.age_sensitivity,'note')"),
    ('hbu note',                 "pick(v,'hbu_note')"),
    ('cost value label',         "pick(v.value_stack.cost,'label')"),
    ('cost sub note',            "pick(v.value_stack.cost,'sub')"),
    ('scenarios note',           "pick(_scn,'note')"),
    ('methodology bare line',    "pick(d,'methodology')"),
    ('rics methodology note',    "pick(d,'rics_methodology_note')"),
    ('refusal reason',           "pick(v,'reason')"),
    ('data-freshness caveat',    "pick(d.data_freshness,'caveat')"),
    ('rics-compliant status',    "pick(d.material_uncertainty,'rics_compliant_status')"),
    ('brief title',              "pick(_brR,'title')"),
]:
    check('pick(): '+label, needle in HTML)

# the OLD bare `.X_ar` INSERTION patterns must be gone WITHIN showReport (guard-reads `.X_ar`
# stay; the same patterns legitimately remain in the not-yet-wired show()/b83 — so scope the
# absence check to the showReport region only).
_s = HTML.find('function showReport(d){'); _e = HTML.find('function printReportA4(')
RPT = HTML[_s:_e] if (_s >= 0 and _e > _s) else ''
check('showReport region isolated for scoped checks', bool(RPT))
check('showReport: every engine *_ar is inserted via pick() (no bare +X_ar+ insertion)',
      '+v.leadership.note_ar+' not in RPT and '+d.methodology_ar+' not in RPT and
      '+v.condition_note_ar+' not in RPT and '+v.hbu_note_ar+' not in RPT and
      '+v.cost_note_ar+' not in RPT and '+d.rics_methodology_note_ar+' not in RPT)
check('showReport: guards still READ .*_ar (truthiness preserved -> AR byte-identical)',
      'if(v.leadership&&v.leadership.note_ar)' in RPT and
      'if(v.hbu_note_ar)' in RPT and 'if(d.methodology_ar)' in RPT)

# ---- (4) legal block (_mucFields/_mucCardHtml) — handoff-named; lawyer/linguist ----
check('_mucFields LANG-aware via pick (clause/basis/review)',
      "muc_ar=pick(mu,'muc_clause')" in HTML and
      "muc_basis=pick(mu,'muc_basis')" in HTML and
      "muc_review=pick(mu,'muc_review_recommendation')" in HTML)
check('_mucCardHtml header + labels wired',
      "Material uncertainty under" in HTML and
      "t('الأساس:','Basis:')" in HTML and
      "t('التوصية:','Recommendation:')" in HTML)

# ---- (5) compliance preserved in BOTH languages (lawyer/linguist focus) ----
check('forced-sale row both langs (×0.90, not a certified liquidation)',
      "t('قيمة البيع الجبريّ الإرشاديّة (×٠٫٩٠ — ليست تصفية معتمدة)','Indicative forced-sale value (×0.90 — not a certified liquidation)')" in HTML and
      'not a certified liquidation valuation. Basis: the central estimated value × 0.90.' in HTML)
check('AR compliance kept verbatim (not-certified footer + forced-sale clause)',
      'تقييم سوقيّ آليّ وليس تقييماً معتمداً' in HTML and
      'ليست تقييم تصفية معتمداً' in HTML)

# ---- (6) CSS dir-flip scoped to #repOut ONLY; short report + result screen unaffected ----
check('#repOut LTR override present (scoped)',
      'body.lang-en #repOut{direction:ltr;text-align:left}' in HTML and
      'body.lang-en #repOut .rep-foot{text-align:center}' in HTML)
check('#srOut block (b80) intact + no result-screen flip / no global .thmr flip',
      'body.lang-en #srOut{direction:ltr;text-align:left}' in HTML and
      'body.lang-en #resultsScreen' not in HTML and
      'body.lang-en .thmr{direction' not in HTML)

# ---- (7) VALUE-INVARIANCE: AR literals verbatim + deferred shared builders still CALLED + dormant flag ----
check('AR report literals kept verbatim (byte-identical AR render)',
      'القيمة السوقية (MV)' in HTML and 'النطاق التقديري السوقي' in HTML and
      'حول الرقم' in HTML and 'حول البيانات' in HTML and
      'بيانات العقار الأساسية' in HTML and 'المنهجية والمعايير' in HTML)
check('deferred shared builders STILL CALLED in showReport (render AR until b83)',
      '_decompHtml(d,v,hasValuation)' in HTML and '_substHtml(d,v,hasValuation)' in HTML and
      '_strataHtml(d)' in HTML and 'evidencePanelHtml(d,acc)' in HTML and
      'pbRows(d.property_basis)' in HTML and 'h+=renderSection(sec)' in HTML)
check('EN dormant (EN_ENABLED=false) + b77 primitives intact',
      'var EN_ENABLED=false;' in HTML and 'function t(ar,en)' in HTML and 'function pick(o,base)' in HTML)
check('b54 locked identity intact (تقييم سوقيّ آليّ)', 'تقييم سوقيّ آليّ' in HTML)
check('_rerenderForLang routes reportScreen -> showReport (b80 plumbing)',
      "id==='reportScreen')showReport(d)" in HTML)

# ---- (8) engine = a valid b-series tag (version-agnostic, R6) ----
check('engine is a valid b-series tag (no exact pin)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb81:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
