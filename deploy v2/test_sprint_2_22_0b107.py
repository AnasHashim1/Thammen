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
check('the 4 loading steps t()-wrapped',
      "t('نتحقق من العنوان في خرائط GIS...','Verifying the address on the GIS maps...')" in HTML and
      "t('نبحث في سجل وزارة العدل عن صفقات مماثلة...','Searching the Ministry of Justice registry for comparable sales...')" in HTML and
      "t('نحلّل الموقع والمعالم القريبة...','Analysing the location and nearby landmarks...')" in HTML and
      "t('نُجهّز التقرير...','Preparing the report...')" in HTML)
check('elapsed-time line t()-wrapped', "t('منذ ','')+el+t(' ثانية',' s')" in HTML)
check('the button label + valuing state t()-wrapped',
      "btn.innerHTML=t('جاري التقييم...','Valuing...')" in HTML and "btn.innerHTML=t('ثمّن','Value it')" in HTML)
check('server-error throw t()-wrapped (all 3 eval paths)',
      "t('خطأ من السيرفر — رقم ','Server error — code ')+r.status" in HTML and
      HTML.count("t('خطأ من السيرفر — رقم ','Server error — code ')") == 3)
check('catch generic error + retry sub-line t()-wrapped',
      "e.message||t('حدث خطأ','An error occurred')" in HTML and
      "t('لو استمرت المشكلة، تأكد من الاتصال أو حاول بعد دقيقة.','If the problem persists, check your connection or try again in a minute.')" in HTML)
check('the run() steps array no longer holds bare literals (uses t() throughout)',
      "steps=['نتحقق" not in HTML and "steps=[t(" in HTML)

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
check('map links + backdrop-close preserved',
      'maps.apple.com' in MAP and 'google.com/maps' in MAP and 'waze.com' in MAP and
      'if(e.target===m)m.remove()' in MAP)

# ── value-invariance + version ──
check('EN reveal + b54 locked identity intact', 'var EN_ENABLED=true;' in HTML and 'تقييم سوقيّ آليّ' in HTML)
check('engine is a valid b-series tag (no exact pin — Lesson-2)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)

print('\nb107:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
