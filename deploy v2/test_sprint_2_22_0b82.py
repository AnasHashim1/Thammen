# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.82 — EN wiring of the CONFIRMATION screen (showConfirm, #cgOut).
E14: reads the REAL index.html + evaluate_unified.py. FRONTEND-ONLY / VALUE-INVARIANT —
the EN render is dormant behind EN_ENABLED (b77); in AR mode t() returns the first (AR)
arg and pick() returns the *_ar field, so the AR output is byte-identical (asserted by the
verbatim-AR-literal checks + the scoped no-bare-insertion check below). Runtime render =
R14 Chromium (AR byte-identical + forced EN: dir-flip on #cgOut only, short report #srOut +
full report #repOut + result screen unaffected, no overflow, 0 console).

SCOPE (b82): showConfirm's OWN body (literals -> t(); the single engine *_ar read,
d.asset_type_ar, routed through t(ASSET_AR..||asset_type_ar.., ASSET_EN..||asset_type_ar..)
preserving the EXACT confirm fallback chain so AR is byte-identical) + the scoped #cgOut LTR
CSS. The SHARED result-family builder pbRows is DEFERRED to the b83/show pass — it stays
AR-fallback in EN; this test asserts it remains CALLED. (b32 already dropped the evidence
panel from the confirm screen, so evidencePanelHtml is correctly absent here.)"""
import io
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

# isolate the showConfirm region for the scoped checks (confirm body only; the same
# patterns legitimately remain in the not-yet-wired show()/b83 and the static screens).
_s = HTML.find('function showConfirm(d){'); _e = HTML.find('function confirmProceed(')
CG = HTML[_s:_e] if (_s >= 0 and _e > _s) else ''
check('showConfirm region isolated for scoped checks', bool(CG))

# ---- (1) preliminary-range block wired (label / unit / sub) ----
check('preliminary-range label + sub wired',
      "t('تقدير مبدئي (نطاق)','Preliminary estimate (range)')" in CG and
      "t('تقدير أوّليّ قابل للتغيّر بعد التأكيد والتحسين.','A preliminary estimate, subject to change after confirmation and refinement.')" in CG)
check('QAR currency unit wired (cg-unit x2 + cg-mid)',
      CG.count("t('ر.ق','QAR')") == 3)

# ---- (2) leader-aware central label (b24/m0) wired — cost / market / central / median ----
check('leader-aware central labels wired',
      "_midLbl=t('التقدير المركزي','Central estimate')" in CG and
      "t('مرتكز التكلفة (أرض + بناء مُهلَك)','Cost basis (land + depreciated building)')" in CG and
      CG.count("t('الوسيط','Median')") == 2)
check('cost-led dual-evidence line wired (matched / geographic)',
      "t('شواهد السوق: مطابق ','Market evidence: matched ')" in CG and
      "t(' · جغرافي ',' · geographic ')" in CG)

# ---- (3) review card title + GIS sub-note wired ----
check('review-card title + GIS sub-note wired',
      "t('راجِع بيانات العقار','Review property data')" in CG and
      "t('هذه البيانات مجلوبة من نظام المعلومات الجغرافية (GIS). راجِعها قبل المتابعة.','This data is drawn from the Geographic Information System (GIS). Review it before continuing.')" in CG)

# ---- (4) basis-review ri() row labels wired ----
check('ri row labels wired (address / property-type / district / zoning)',
      "ri(t('العنوان','Address')" in CG and
      "ri(t('نوع العقار','Property type')" in CG and
      "ri(t('المنطقة','District')" in CG and
      "ri(t('المنطقة التنظيمية','Zoning')" in CG)
check('plot-area label + m2 unit wired (verified-vs-cadastral)',
      "t('المساحة المعتمدة في التقدير','Area used in the estimate')" in CG and
      "t('مساحة القسيمة','Plot area')" in CG and
      CG.count("t(' م²',' m²')") == 2)

# ---- (5) the SINGLE engine *_ar read (asset_type) — fallback chain preserved in BOTH t() args ----
check('asset-type label routed through t(ASSET_AR..,ASSET_EN..) preserving the confirm fallback chain',
      "t(ASSET_AR[d.asset_type]||d.asset_type_ar||d.asset_type,ASSET_EN[d.asset_type]||d.asset_type_ar||d.asset_type)" in CG)
check('unknown branch keeps backend AR label (mirrors b81)',
      "(d.asset_type==='unknown'&&d.asset_type_ar)?d.asset_type_ar:" in CG)
check('ASSET_EN map (b80) defined + in scope', "const ASSET_EN={" in HTML and "'standalone_villa':'Standalone villa'" in HTML)

# ---- (6) footprint tooltip + max-buildable row wired ----
check('footprint setbacks tooltip wired (both methods)',
      "t('من أبعاد القطعة ‎','From the plot dimensions ‎')" in CG and
      "t('‎ م بعد الارتدادات القانونية (أمامي 5 · جانبي 3 · خلفي 3) وضمن سقف تغطية 60%'," in CG and
      "t('حصة الوحدة في قطعة مشتركة','The unit" in CG and
      "t(' بين ',' among ')" in CG and "t(' وحدات',' units')" in CG)
check('max-buildable row label + refine-CTA wired',
      "ri(t('مساحة البناء الأرضي (تقدير أقصى)','Ground building area (max estimate)')" in CG and
      "t('عدّله في خطوة التحسين','adjust it in the refine step')" in CG)

# ---- (7) confirm CTA + full-report escape (arrow flips ◂ -> ▸ in EN) ----
check('confirm button + escape link wired (arrow flips for EN)',
      "t('تابِع بهذه البيانات','Continue with this data')" in CG and
      "t('التقرير الكامل الآن ◂','Full report now ▸')" in CG)

# ---- (8) VALUE-INVARIANCE: AR literals kept verbatim + no bare un-wrapped insertion ----
check('AR confirm literals kept verbatim (byte-identical AR render)',
      'تقدير مبدئي (نطاق)' in CG and 'راجِع بيانات العقار' in CG and
      'تابِع بهذه البيانات' in CG and 'مساحة القسيمة' in CG)
check('no bare un-wrapped literal insertion remains in showConfirm',
      'cg-lbl">تقدير مبدئي' not in CG and
      '</use></svg> راجِع بيانات العقار</div>' not in CG and
      '>تابِع بهذه البيانات</button>' not in CG and
      'cg-unit">ر.ق<' not in CG)

# ---- (9) shared builder pbRows STILL CALLED (AR until b83); evidence panel correctly absent (b32) ----
check('pbRows still called in confirm (shared builder, AR until b83)',
      'pbRows(d.property_basis,true)' in CG)
check('evidencePanelHtml NOT called in confirm (b32 dropped it — no regression)',
      'evidencePanelHtml(' not in CG)

# ---- (10) CSS dir-flip scoped to #cgOut ONLY; #srOut/#repOut + result screen unaffected ----
check('#cgOut LTR override present (scoped)',
      'body.lang-en #cgOut{direction:ltr;text-align:left}' in HTML)
check('prior #srOut / #repOut blocks intact + no result-screen / global .thmr flip',
      'body.lang-en #srOut{direction:ltr;text-align:left}' in HTML and
      'body.lang-en #repOut{direction:ltr;text-align:left}' in HTML and
      'body.lang-en #resultsScreen' not in HTML and
      'body.lang-en .thmr{direction' not in HTML)

# ---- (11) plumbing + dormant flag + locked identity intact ----
check('_rerenderForLang routes confirmScreen -> showConfirm', "id==='confirmScreen')showConfirm(d)" in HTML)
check('EN revealed (EN_ENABLED=true, b88) + b77 primitives intact',
      'var EN_ENABLED=true;' in HTML and 'function t(ar,en)' in HTML and 'function pick(o,base)' in HTML)
check('b54 locked identity intact (تقييم سوقيّ آليّ)', 'تقييم سوقيّ آليّ' in HTML)

# ---- (12) engine = a valid b-series tag (version-agnostic, R6) ----
check('engine is a valid b-series tag (no exact pin)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb82:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
