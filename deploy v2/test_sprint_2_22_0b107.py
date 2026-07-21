# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.107 — 3 UI bug fixes (S2, the b64-precedent bundle). E14: reads the REAL index.html +
evaluate_unified.py. 🟢 FRONTEND / VALUE-INVARIANT — a display key-name fix + EN t()-wrapping + modal a11y;
no value/method/rule change; api.py untouched.
  (1) dead §٤ short-report rows: .value → .estimated_qar / .qar (the engine's real keys, :1708/:1716).
  (2) run() loading steps + error messages t()-wrapped (EN reveal since b88).
  (3) map modal gains role=dialog / aria-modal / aria-label + Escape-to-close (the one modal b70 missed)."""
import io
HTML = io.open('index.html', encoding='utf-8').read()
ENG  = io.open('evaluate_unified.py', encoding='utf-8').read()
passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

# ── (1) the dead §٤ rows now read the engine's real keys ──
check('§٤ land row reads land.estimated_qar (was the dead .value)',
      "if(vd.land&&vd.land.estimated_qar!=null)h+=" in HTML and 'fmt(vd.land.estimated_qar)' in HTML)
check('§٤ building row reads building_implied.qar (was the dead .value), negative-safe',
      "if(vd.building_implied&&vd.building_implied.qar!=null)h+=" in HTML and
      "(vd.building_implied.qar<0?'−':'')+fmt(Math.abs(vd.building_implied.qar))" in HTML)
check('the DEAD .value keys are GONE from the §٤ block',
      'vd.land.value' not in HTML and 'vd.building_implied.value' not in HTML)
check('the engine actually emits estimated_qar / qar (E14 — the key the fix now reads)',
      "'estimated_qar': land_value" in ENG and "'qar': bld_implied" in ENG)
check('§٤ labels keep their EN twins (bilingual)',
      "t('مكوّن الأرض الاسترشادي','Indicative land component')" in HTML and
      "t('مساهمة البناء الضمنية','Implied building contribution')" in HTML)

# ── (2) run() loading steps + errors t()-wrapped ──
check('pin-format error t()-wrapped',
      "t('يرجى إدخال رقم قطعة صحيح (7 إلى 9 أرقام)','Please enter a valid plot number (7 to 9 digits)')" in HTML)
check('zone/street/building error t()-wrapped',
      "t('يرجى إدخال رقم المنطقة والشارع والمبنى','Please enter the zone, street and building numbers')" in HTML)
# b127 R6/Lesson-2 (S2): the loading steps + elapsed line were superseded by the «لحظة الكشف» reveal —
# its 4 milestone stages + headline + reassurance are ALL t()-wrapped (the EN-reveal intent preserved).
check('the 4 reveal-moment stages t()-wrapped (b127 honesty: generic, true for every leader/asset)',
      "t('نقرأ سجلّ العقار…','Reading the property record…')" in HTML and
      "t('نطابق صفقات وزارة العدل…','Matching Ministry of Justice sales…')" in HTML and
      "t('نحسب التقدير من الشواهد…','Computing the estimate from the evidence…')" in HTML and
      "t('نوازن الأدلّة ونُحكِم النطاق…','Weighing the evidence and finalizing the range…')" in HTML)
check('reveal headline + reassurance t()-wrapped', "t('القيمة السوقيّة التقديريّة','Estimated market value')" in HTML and "t('ما زلنا نطابق…','Still matching…')" in HTML)
check('the button label + valuing state t()-wrapped',
      "btn.innerHTML=t('جاري التقييم...','Valuing...')" in HTML and "btn.innerHTML=t('ثمّن','Value it')" in HTML)
check('server-error throw t()-wrapped (all 3 eval paths)',
      "t('خطأ من السيرفر — رقم ','Server error — code ')+r.status" in HTML and
      HTML.count("t('خطأ من السيرفر — رقم ','Server error — code ')") == 3)
# b127 R6/Lesson-2 (S2): run()'s old catch + steps array were replaced by the reveal's failure state
# (the _fail() card) — its strings are t()-wrapped too.
check('reveal failure state t()-wrapped (title + retry + try-later)',
      "t('تعذّر إكمال الحساب الآن','Could not complete the valuation now')" in HTML and
      "t('أعِد المحاولة','Retry')" in HTML and "t('جرّب لاحقاً','Try later')" in HTML)
check('the old bare-literal loading is gone (no steps=[ array; reveal uses t() throughout)',
      "steps=['نتحقق" not in HTML and "steps=[t(" not in HTML)

# ── (3) map modal a11y ──
_ms = HTML.find('function openMapPicker(lat,lon){')
_me = HTML.find('function copyResult(')
MAP = HTML[_ms:_me] if (_ms >= 0 and _me > _ms) else ''
check('openMapPicker() region isolated', bool(MAP))
check('map modal gets role=dialog + aria-modal',
      "m.setAttribute('role','dialog')" in MAP and "m.setAttribute('aria-modal','true')" in MAP)
check('map modal aria-label (bilingual)',
      "m.setAttribute('aria-label',t('اختر تطبيق الخرائط','Choose a maps app'))" in MAP)
check('map modal Escape-to-close (the b70 pattern) + listener cleanup',
      "if(e.key==='Escape')" in MAP and "document.addEventListener('keydown',_mapEsc)" in MAP and
      "document.removeEventListener('keydown',_mapEsc)" in MAP)
check('map modal strings t()-wrapped (header/label/cancel)',
      "t('اختر التطبيق','Choose the app')" in MAP and "t('موقع العقار','Property location')" in MAP and
      "t('إلغاء','Cancel')" in MAP)
check('map links + backdrop-close preserved',   # b136 R6: backdrop still closes, now via the unified _mapClose (adds focus-restore)
      'maps.apple.com' in MAP and 'google.com/maps' in MAP and 'waze.com' in MAP and
      'if(e.target===m)_mapClose()' in MAP)

# ── value-invariance + version ──
check('EN reveal + b54 locked identity intact', 'var EN_ENABLED=true;' in HTML and 'تقييم سوقيّ آليّ' in HTML)
check('engine is a valid b-series tag (no exact pin — Lesson-2)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb107:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
