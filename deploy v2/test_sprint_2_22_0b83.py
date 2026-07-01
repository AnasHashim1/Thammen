# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.83 — EN wiring of the RESULT SCREEN (show, #rOut) + the 6 shared result-family
builders (evidencePanelHtml + _evidenceRatings/_evPill/_evOneRow · pbRows · _decompHtml · _substHtml
· _strataHtml · renderSection). E14: reads the REAL index.html + evaluate_unified.py. FRONTEND-ONLY /
VALUE-INVARIANT — EN dormant behind EN_ENABLED (b77); in AR mode t() returns the AR arg and pick()
returns *_ar, so AR is byte-identical (asserted by the verbatim-AR checks + the scoped no-bare-insertion
check). Runtime = R14 Chromium (AR byte-identical + forced EN: #rOut dir-flip only, value-invariant,
no overflow, 0 console). The PO directed the b83+b84 bundle into one push (#39 flag)."""
import io
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

# isolate show() for scoped checks (the body wiring; builders are before show())
_s=HTML.find('function show(d){'); _e=HTML.find('// Sprint D: Section renderer')
SHOW=HTML[_s:_e] if (_s>=0 and _e>_s) else ''
check('show() region isolated', bool(SHOW))

# ---- (1) EN maps / LANG selectors ----
check('EV_RATING_EN map (rating words; AR token stays the color key)',
      "var EV_RATING_EN={'قوي':'Strong','متوسط':'Moderate','محدود':'Limited'};" in HTML)
check('MUC_LEVEL_EN map + show() selects by LANG',
      "const MUC_LEVEL_EN=" in HTML and "(LANG==='en'?MUC_LEVEL_EN:MUC_LEVEL_AR)[mu.level]" in SHOW)
check('TIER_LABEL selected by LANG in show()',
      "(LANG==='en'?TIER_LABEL_EN:TIER_LABEL_AR)[d.tier_label]" in SHOW)
check('STATUS_EN / FRESHNESS_EN maps (tier_breakdown) defined',
      "const STATUS_EN={" in HTML and "const FRESHNESS_EN={" in HTML)
check('posLabels / levelLabels are LANG-aware (verdict / material_uncertainty)',
      "const posLabels=(LANG==='en')?{" in HTML and "const levelLabels=(LANG==='en')?{" in HTML)
check('qarFmt currency wired (centralizes renderSection QAR)',
      "function qarFmt(n){return n==null?'—':fmt(n)+t(' ر.ق',' QAR')}" in HTML)

# ---- (2) builders: evidence group ----
check('_evidenceRatings labels via t()',
      "[t('اكتمال بيانات العقار','Property completeness'),c1]" in HTML and
      "[t('جودة المقارنات','Comparables'),c2]" in HTML)
check('_evPill displays t(rt,EV_RATING_EN) + N/A wired',
      "t(rt,EV_RATING_EN[rt]||rt)" in HTML and "t('غير منطبق — أرض','N/A — land')" in HTML)
check('evidencePanelHtml title + explanation via pick',
      "t('جودة الأدلّة','Evidence quality')" in HTML and "pick(acc,'explanation')" in HTML)
check('_evOneRow label wired', "t('جودة الأدلّة:','Evidence:')" in HTML)

# ---- (3) builders: pbRows ----
check('pbRows labels wired (cadastral/electricity/water/age) + vintage via pick',
      "ri(t('الرقم المساحي','Cadastral no.'),pb.pin)" in HTML and
      "ri(t('رقم الكهرباء','Electricity no.')" in HTML and
      "ri(t('عمر البناء التقديري','Estimated building age')" in HTML and
      "pick(b,'vintage_note')" in HTML)

# ---- (4) builders: _decompHtml / _substHtml / _strataHtml ----
check('_decompHtml wired (title + land/building + pick notes)',
      "t('تفكيك القيمة (أرض + بناء)','Value breakdown (land + building)')" in HTML and
      "t('قيمة الأرض','Land value')" in HTML and "pick(bd,'interpretation')" in HTML and
      "pick(vd,'methodology_note')" in HTML and "pick(ld,'confidence')" in HTML)
check('_substHtml wired (regime titles + age + pick notes)',
      "t('قاعدة الـ 10 سنوات (السوق القطري)','10-Year Rule (Qatari market)')" in HTML and
      "t('عمر البناء: ','Building age: ')" in HTML and "pick(bs,'rationale')" in HTML and
      "pick(bs,'methodology_note')" in HTML)
check('_strataHtml wired (title + land-ref + classification + pick notes)',
      "t('تصنيف المخزون (Stock Stratification)','Stock stratification')" in HTML and
      "t('مرجع الأرض:','Land reference:')" in HTML and "pick(stockStrata,'methodology')" in HTML and
      "pick(s,'label')" in HTML and "pick(stockStrata.dominant_stratum,'note')" in HTML)

# ---- (5) builder: renderSection (labels + content + section title) ----
check('renderSection row labels via t()',
      "row(t('العائد الإجمالي','Gross yield')," in HTML and
      "row(t('معدّل الرسملة','Cap rate')," in HTML and
      "row(t('القيمة التقديرية','Estimated value')," in HTML)
check('renderSection content via pick + section title via pick',
      "pick(c,'cap_rate_label')" in HTML and "pick(c,'description')" in HTML and
      "</span>'+pick(sec,'title')+" in HTML)
check('renderSection tier_breakdown headers wired',
      "t('المصدر','Source')" in HTML and "t('الخصم','Discount')" in HTML)
check('renderSection comparable_grid local `t` renamed to t2 (no t() shadow)',
      "const t2=cp.time_pct!=null?" in HTML and "+t2+')</span>" in HTML)

# ---- (6) show() body: hero / chip / leadership / financing / not-certified / accordions ----
check('hero label + range wired',
      "t('التقييم السوقي','Market valuation')" in SHOW and
      "t('النطاق التقديري السوقي','Estimated market range')" in SHOW)
check('MUC chip label wired', "t('تحفظ مادي: ','Material uncertainty: ')" in SHOW)
check('cost-led basis note (b64) wired + e25 divergence (b72) wired',
      "t('اعتمدنا كلفةَ البناء (الأرض + المبنى بعد خصم الإهلاك) لأنّ الصفقات المماثلة القريبة كانت قليلة؛ وقد بِيعت بيوتٌ في منطقتك بنحو '," in SHOW and
      "t('كلفةُ إعادة بناء بيتك (','The cost to rebuild your home (')" in SHOW)
check('condition/teardown/luxury/leadership notes via pick',
      "pick(v,'condition_note')" in SHOW and "pick(v.teardown,'note')" in SHOW and
      "pick(v.leadership,'note')" in SHOW and "pick(v,'hbu_note')" in SHOW and
      "pick(v.old_stock_reanchor,'note')" in SHOW)
check('financing calculator wired (buyer)',
      "t('حاسبة التمويل التقريبية: ','Approximate financing calculator: ')" in SHOW and
      "t('% دفعة أولى · ','% down · ')" in SHOW)
check('not-certified TIER-1 line wired',
      "t('تقييم سوقيّ آليّ — ليس تقييماً معتمداً','An automated market valuation — not a certified valuation')" in SHOW)
check('the two TIER-2 accordion titles wired',
      "t('كيف وصلنا لهذا الرقم؟','How we got to this number')" in SHOW and
      "t('بيانات العقار الأساسية','Property basics')" in SHOW)
check('keystone + considered comparables wired',
      "t('صفقات في منطقتك ضمن حوض المقارنة الموسَّع جغرافياً','Transactions in your area within the geographically widened comparison pool')" in SHOW and
      "t('صفقات السوق في منطقتك — اطّلعنا عليها ولم تقُد الرقم','Market transactions in your area — we reviewed them but they did not set the number')" in SHOW)
check('refusal path wired (h2 + facts + CTA)',
      "t('تعذّر تحديد نوع العقار','Could not determine the property type')" in SHOW and
      "t('العنوان:','Address:')" in SHOW and
      "t('→ أضف الإيجار أو سعر الإعلان','→ Add the rent or the listing price')" in SHOW)
check('asset label via t(ASSET_AR,ASSET_EN) in show() (info + refusal)',
      "t(ASSET_AR[d.asset_type]||d.asset_type,ASSET_EN[d.asset_type]||d.asset_type)" in SHOW and
      "ASSET_EN[d.asset_type]||d.asset_type_ar||d.asset_type||'this property'" in SHOW)

# ---- (7) VALUE-INVARIANCE: AR verbatim + scoped no-bare-insertion + value-math untouched ----
check('AR result literals kept verbatim',
      'التقييم السوقي' in SHOW and 'النطاق التقديري السوقي' in SHOW and
      'ليس تقييماً معتمداً' in SHOW and 'كيف وصلنا لهذا الرقم؟' in SHOW)
check('show(): no bare engine *_ar insertion remains (guards still read .*_ar)',
      "'+v.leadership.note_ar+'" not in SHOW and "'+v.condition_note_ar+'" not in SHOW and
      "'+v.hbu_note_ar+'" not in SHOW and "'+d.methodology_ar+'" not in SHOW and
      "'+v.old_stock_reanchor.note_ar+'" not in SHOW)
check('show(): truthiness guards still READ .*_ar (AR byte-identical)',
      'if(v.condition_note_ar)' in SHOW and 'if(v.hbu_note_ar)' in SHOW and
      'if(d.methodology_ar)' in SHOW)
check('value-math untouched (b35 _srPayment + b3 range marker present)',
      "_srPayment(v.amount,20,25,4.5)" in SHOW and "(v.amount-v.low)/(v.high-v.low)" in SHOW)

# ---- (8) CSS scoped to #rOut; siblings intact; no global .thmr flip ----
check('#rOut LTR override present (scoped) + hero stays centered',
      'body.lang-en #rOut{direction:ltr;text-align:left}' in HTML and
      'body.lang-en #rOut .rhero{text-align:center}' in HTML)
check('prior #srOut/#repOut/#cgOut blocks intact + no global .thmr flip',
      'body.lang-en #srOut{direction:ltr;text-align:left}' in HTML and
      'body.lang-en #repOut{direction:ltr;text-align:left}' in HTML and
      'body.lang-en #cgOut{direction:ltr;text-align:left}' in HTML and
      'body.lang-en .thmr{direction' not in HTML)

# ---- (9) plumbing + dormant + identity + version ----
check('_rerenderForLang routes resultsScreen -> show', "id==='resultsScreen')show(d)" in HTML)
check('EN revealed (EN_ENABLED=true, b88) + b77 primitives intact',
      'var EN_ENABLED=true;' in HTML and 'function t(ar,en)' in HTML and 'function pick(o,base)' in HTML)
check('b54 locked identity intact (تقييم سوقيّ آليّ)', 'تقييم سوقيّ آليّ' in HTML)
check('engine is a valid b-series tag (no exact pin)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb83:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
