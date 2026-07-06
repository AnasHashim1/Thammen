# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.80 — EN wiring of the SHORT report (showShortReport).
E14: reads the REAL index.html + evaluate_unified.py. FRONTEND-ONLY / VALUE-INVARIANT —
the EN render is dormant behind EN_ENABLED (b77); in AR mode t() returns the first (AR)
arg and pick() returns the *_ar field, so the AR output is byte-identical (asserted by the
verbatim-AR-literal checks below). Runtime render = R14 Chromium (AR byte-identical + forced
EN: dir-flip on #srOut only, full report #repOut stays RTL, no overflow, 0 console)."""
import io
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

# ---- (1) ASSET_EN map (EN asset labels; AR build never reads it) ----
check('ASSET_EN map defined (dormant EN asset labels)',
      "const ASSET_EN={'standalone_villa':'Standalone villa'" in HTML and
      "'raw_land':'Vacant land'" in HTML and "'unknown':'Unspecified'" in HTML)

# ---- (2) wiring structure: representative t('<AR>','<EN>') pairs (pins AR byte-identity) ----
check('page-1 head wired (title + one-page subtitle)',
      "t('ثمّن — التقرير المختصر','Thammen — Short Report')" in HTML and
      "t('الخلاصة في صفحة واحدة','Summary on one page')" in HTML)
check('section titles wired (§1 cost story / §2 / §4 / §9 / §8)',
      "t('لماذا أقل مما تسمعه عن بيوت حولك؟','Why is this lower than what you hear about homes around you?')" in HTML and
      "t('الأرقام الثلاثة التي تهمّك','The three numbers that matter to you')" in HTML and
      "t('من أين جاء الرقم؟','Where did the number come from?')" in HTML and
      "t('الإطار القانوني والمحاسبي','Legal and accounting framework')" in HTML and
      "t('شفافية الأدلّة','Evidence transparency')" in HTML)  # b104 R6: §٨ register fix «— بلا تجميل» dropped
check('asset label routed through ASSET_AR/ASSET_EN via t()',
      "t(ASSET_AR[d.asset_type]||'عقار',ASSET_EN[d.asset_type]||'Property')" in HTML)
check('section number chips wired (Arabic-Indic ١..٩ -> 1..9)',
      "t('١','1')" in HTML and "t('٥','5')" in HTML and "t('٩','9')" in HTML)

# ---- (3) the 4 engine *_ar reads swapped to pick() (graceful AR fallback) ----
check('refusal reason via pick()',  "pick(d.refusal_reason,'message')" in HTML)
check('rent source via pick()',     "pick(inc,'rent_source')" in HTML)
check('scenario label via pick()',  "pick(it,'label')" in HTML)
check('cap-rate district via pick()',"pick(d.cap_rate_provenance,'district')" in HTML)

# ---- (4) §9 compliance preserved in BOTH languages (lawyer/linguist focus) ----
check('AR legal kept verbatim (not certified + IFRS 13 + estates + forced-sale x0.90)',
      'ليس تقييماً عقارياً معتمداً' in HTML and 'IFRS 13' in HTML and
      'لقسمة التركات' in HTML and '×0.90' in HTML)
check('EN legal authored (not a certified RE valuation + no-liability + estates)',
      'not a certified real-estate valuation' in HTML and
      'creates no obligation or liability on the platform' in HTML and
      'dividing an estate' in HTML)
check('forced-sale / quick-sale row both langs (x0.90, not a liquidation valuation)',
      'ليست تقييم تصفية' in HTML and 'not a liquidation valuation' in HTML)
check('honesty + GT footer both langs (not a certified valuation + Ministry of Justice + info@thammen.qa)',
      'تقييم سوقيّ آليّ وليس تقييماً معتمداً' in HTML and
      'An automated market valuation, not a certified valuation' in HTML and
      'Ministry of Justice data via Qatar Open Data' in HTML and 'info@thammen.qa' in HTML)

# ---- (5) CSS dir-flip scoped to #srOut ONLY (short report); NOT the full report / result ----
check('#srOut LTR override present',
      'body.lang-en #srOut{direction:ltr;text-align:left}' in HTML and
      'body.lang-en #srOut .thmr-row .v{text-align:right}' in HTML and
      'body.lang-en #srOut .thmr-sctab th{text-align:left}' in HTML and
      'body.lang-en #srOut .thmr-rbar .dot.c{right:auto;left:0' in HTML)
check('NO bleed: result (#resultsScreen) NOT EN-flipped; no global .thmr flip (b81 adds #repOut intentionally, scoped)',
      'body.lang-en #resultsScreen' not in HTML and
      'body.lang-en .thmr{direction' not in HTML)

# ---- (6) representative EN coverage across page 1 + page 2 ----
check('EN coverage markers (page 1 + page 2)',
      'Thammen — Specialist Appendix' in HTML and
      'For the investor — the income view' in HTML and
      'Where you sit in the per-metre range' in HTML and
      'Matched to your bracket' in HTML and
      'Verify the integrity of this report' in HTML and
      'Scenario table' in HTML)

# ---- (7) VALUE-INVARIANCE: AR literals verbatim + locked identity + dormant flag ----
check('AR report literals kept verbatim (byte-identical AR render)',
      'القيمة السوقية التقديرية' in HTML and 'الأرقام الثلاثة التي تهمّك' in HTML and  # b90 R6: hero label neutralized «قيمة بيتك التقديرية اليوم»→«القيمة السوقية التقديرية»
      'المصدر: وزارة العدل — صفقات مسجلة حتى ديسمبر 2025' in HTML and
      'ملحق المختصّين' in HTML and 'موقعك في نطاق المتر' in HTML)  # b103 R6: the «الملحق المتخصص ↓» scroll-button became the srFold2 «ملحق المختصّين» summary
check('b54 locked identity intact (التقييم السوقي)', 'التقييم السوقي' in HTML)
check('EN revealed (EN_ENABLED=true, b88) + b77 primitives intact',
      'var EN_ENABLED=true;' in HTML and 'function t(ar,en)' in HTML and 'function pick(o,base)' in HTML)

# ---- (8) engine = a valid b-series tag (version-agnostic, R6) ----
check('engine is a valid b-series tag (no exact pin)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb80:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
