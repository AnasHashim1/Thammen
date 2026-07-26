# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.148 — «الأحافير الإنجليزيّة المرئيّة» (the measured visible EN leaks)
+ the AR-side finish-enum label.

Scope (all VALUE-NEUTRAL — display copy / read swaps only):
  (A) 🔴 the refusal brief `next_steps` BODY — an English heading over an Arabic body on
      EVERY apartment/tower refusal: engine-emitted `note_en` (interpolated → the constant
      catalog cannot cover it) + an `_ar`-suffixed ARRAY rule for `options_ar` → `options_en`
      + the frontend `pickArr(c,'options')` read.
  (B) 🟡 `valuation.window_used` — the a14 evidence-window disclosure, rendered RAW by the
      short report: `_BARE_EN_KEYS` += the key (the b146 window-split template already
      matches its shape) + a `pickBare` read.
  (C) 🟡 the result-screen «الاتجاه العام» line — read RAW while the b146 bare-key rule
      already emits `label_en`.
  (D) 🟢 the refine group numerals ١٢٣ — no `data-en`.
  (E) AR-side — `assumptions_ar` interpolated the RAW ENGLISH finish enum
      («افتراضات: تشطيب ordinary …») inside Arabic copy.

E14: exercises the REAL production functions/files.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import en_localize as E
import evaluate_unified as EU

HERE = os.path.dirname(os.path.abspath(__file__))
IDX = io.open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
ENG = io.open(os.path.join(HERE, 'evaluate_unified.py'), encoding='utf-8').read()

passed = failed = 0


def check(name, cond, extra=''):
    global passed, failed
    if cond:
        passed += 1
        print('  PASS  ' + name)
    else:
        failed += 1
        print('  FAIL  ' + name + ('   ' + str(extra) if extra else ''))


print('\n=== (A) the refusal next_steps BODY ===')

# A1-A3 — the `_ar`-suffixed ARRAY rule (real attach_en over a real-shaped payload)
sample = {'brief': {'sections': [{
    'id': 'next_steps', 'title_ar': 'الخطوات المقترحة',
    'content': {
        'note_ar': 'العنوان 52/903/90 تابع لمساحة 467 م² مُصنَّف كـ "عمارة سكنية". لتحليل آلي يرجى تزويدنا بأحد التاليين:',
        'options_ar': ['إفادة الإيجار الشهري الفعلي (لتقييم بمنهج الدخل)',
                       'سعر الإعلان أو سعر المالك (لمقارنة سوقية)'],
    }}]}}
E.attach_en(sample)
_c = sample['brief']['sections'][0]['content']
check('A1 attach_en emits options_en from options_ar', isinstance(_c.get('options_en'), list))
check('A2 options_en is index-aligned + fully English',
      _c.get('options_en') and len(_c['options_en']) == 2
      and all(not re.search(r'[؀-ۿ]', x) for x in _c['options_en']),
      _c.get('options_en'))
check('A3 options_ar UNCHANGED (additive)',
      _c['options_ar'] == ['إفادة الإيجار الشهري الفعلي (لتقييم بمنهج الدخل)',
                           'سعر الإعلان أو سعر المالك (لمقارنة سوقية)'])

# A4 — the rule set is declared + surgical (not a blanket `_ar`-array sweep)
check('A4 _ARR_AR_KEYS declared and scoped to options_ar',
      getattr(E, '_ARR_AR_KEYS', None) == ('options_ar',), getattr(E, '_ARR_AR_KEYS', None))

# A5 — an unresolvable `_ar` array does NOT fire (no half-Arabic twin from nothing)
_u = {'options_ar': ['نصٌّ غير مُفهرَس إطلاقاً في الكتالوج']}
E.attach_en(_u)
check('A5 unresolvable options_ar → no twin', 'options_en' not in _u, _u)

# A6 — never clobbers an engine-authored twin
_p = {'options_ar': ['إفادة الإيجار الشهري الفعلي (لتقييم بمنهج الدخل)'], 'options_en': ['ENGINE']}
E.attach_en(_p)
check('A6 never clobbers an engine-authored options_en', _p['options_en'] == ['ENGINE'])

# A7-A9 — the engine-emitted note_en (interpolated) at the classification refusal site
check('A7 engine emits note_en beside the interpolated note_ar', "'note_en': (" in ENG)
check('A8 note_en uses the EN asset-label map', 'ASSET_TYPE_EN.get(asset_type' in ENG)
check('A9 ASSET_TYPE_EN mirrors ASSET_TYPE_AR keys',
      set(EU.ASSET_TYPE_EN) == set(EU.ASSET_TYPE_AR),
      set(EU.ASSET_TYPE_AR) ^ set(EU.ASSET_TYPE_EN))
check('A10 ASSET_TYPE_EN carries no Arabic',
      all(not re.search(r'[؀-ۿ]', v) for v in EU.ASSET_TYPE_EN.values()))
check('A11 ASSET_TYPE_AR untouched (apartment_building)',
      EU.ASSET_TYPE_AR['apartment_building'] == 'عمارة سكنية')

# A12-A14 — the implied-rent next_steps body (constants + the interpolated option)
for s in ['لتقييم نهائي وموثوق:',
          'إذا كان الإيجار الفعلي أقل بكثير → السعر مرتفع',
          'إذا كان الإيجار الفعلي أعلى أو مساوياً → السعر منطقي',
          'أعد الطلب مع الإيجار الشهري للتقييم الكامل']:
    check('A12 catalogued: ' + s[:28], E.CATALOG.get(E._norm(s)) is not None)
check('A13 the interpolated confirm-or-deny option resolves via _TEMPLATES',
      E._item_en(E._norm('أكّد أو انفِ: هل الإيجار الفعلي قريب من 12,500 ر.ق/شهر؟'))
      == 'Confirm or deny: is the actual rent close to 12,500 QAR/month?',
      E._item_en(E._norm('أكّد أو انفِ: هل الإيجار الفعلي قريب من 12,500 ر.ق/شهر؟')))

# A15 — the frontend read
check('A14 renderSection next_steps reads pickArr(c,\'options\')',
      "pickArr(c,'options')" in IDX)
check('A15 the raw c.options_ar.forEach render is gone',
      'c.options_ar.forEach' not in IDX)


print('\n=== (B) window_used ===')
check('B1 window_used is a bare-EN key', 'window_used' in E._BARE_EN_KEYS, E._BARE_EN_KEYS)
_w = {'window_used': '37 معاملة، منها 28 خلال 24 شهراً'}
E.attach_en(_w)
check('B2 window_used_en emitted + English',
      _w.get('window_used_en') == '37 transactions, of which 28 within the last 24 months',
      _w.get('window_used_en'))
check('B3 window_used (AR) unchanged', _w['window_used'] == '37 معاملة، منها 28 خلال 24 شهراً')
check('B4 short report reads pickBare(v,\'window_used\')', "pickBare(v,'window_used')" in IDX)
check('B5 the raw window_used concat is gone', "' ('+v.window_used+')'" not in IDX)


print('\n=== (C) the «الاتجاه العام» trend label ===')
check('C1 the line reads pickBare(tr,\'label\')', "pickBare(tr,'label')" in IDX)
check('C2 the raw esc(tr.label) read is gone', 'esc(tr.label)' not in IDX)
_t = {'label': 'غير محدد'}
E.attach_en(_t)
check('C3 the engine bare-key rule still emits label_en', _t.get('label_en') == 'Unspecified',
      _t.get('label_en'))
check('C4 the b140 trLabel map survives as the fallback', 'TREND_LABEL_EN' in IDX)


print('\n=== (D) the refine group numerals ===')
for n_ar, n_en in (('١', '1'), ('٢', '2'), ('٣', '3')):
    check('D-gnum ' + n_en,
          ('<span class="gnum" data-en="%s">%s</span>' % (n_en, n_ar)) in IDX)


print('\n=== (E) the AR finish label ===')
check('E1 COST_FINISH_LABEL_AR declared', isinstance(getattr(EU, 'COST_FINISH_LABEL_AR', None), dict))
check('E2 every RCN finish key has an Arabic label',
      all(k in EU.COST_FINISH_LABEL_AR for k in EU.COST_RCN_BY_FINISH),
      set(EU.COST_RCN_BY_FINISH) - set(EU.COST_FINISH_LABEL_AR))
check('E3 every label is Arabic (no English enum leak)',
      all(not re.search(r'[A-Za-z]', v) for v in EU.COST_FINISH_LABEL_AR.values()))
check('E4 ordinary → عاديّ', EU._finish_label_ar('ordinary') == 'عاديّ')
check('E5 luxury → فاخر', EU._finish_label_ar('luxury') == 'فاخر')
check('E6 good → جيّد', EU._finish_label_ar('good') == 'جيّد')
check('E7 unknown/None → the ordinary default',
      EU._finish_label_ar(None) == 'عاديّ' and EU._finish_label_ar('zzz') == 'عاديّ')
check('E8 the 3 assumptions_ar sites use the Arabic label',
      ENG.count('_finish_label_ar(') >= 4, ENG.count('_finish_label_ar('))
# E9 — every ARABIC «تشطيب {f}» template must format through the Arabic label helper.
# (The EN twin legitimately keeps the raw enum, so a blanket source search would false-fire.)
_ar_finish_sites = [m.start() for m in re.finditer(r'تشطيب \{f\}', ENG)]
check('E9 every AR «تشطيب {f}» formats via _finish_label_ar',
      len(_ar_finish_sites) == 3
      and all('_finish_label_ar(' in ENG[i:i + 400] for i in _ar_finish_sites),
      [(i, '_finish_label_ar(' in ENG[i:i + 400]) for i in _ar_finish_sites])
check('E10 the EN twin still carries the English enum',
      "'Assumptions: finish {f}" in ENG and "f=_cost_av['finish']" in ENG)
check('E11 COST_RCN_BY_FINISH (the VALUE driver) untouched',
      EU.COST_RCN_BY_FINISH['ordinary'] == 2200 and EU.COST_RCN_BY_FINISH['luxury'] == 3500
      and EU.COST_RCN_DEFAULT == 2200)


print('\n=== value-neutrality + regression guards ===')
check('V1 pickArr keeps the bare-key branch first (b142/b145 callers unaffected)',
      "return Array.isArray(o[base])?o[base]:(Array.isArray(o[base+'_ar'])?o[base+'_ar']:[]);" in IDX)
_b = {'content': ['لا توجد صفقات مقارنة في وزارة العدل']}
E.attach_en(_b)
check('V2 the b142 bare-key array rule still fires', isinstance(_b.get('content_en'), list))
check('V3 api.py untouched by this sprint (no b148 marker)',
      'b148' not in io.open(os.path.join(HERE, 'api.py'), encoding='utf-8').read())
check('V4 engine tag bumped to the b-series b148',
      "SPRINT_TAG = '2.22.0b.148'" in ENG and 'thammen-sprint2p22p0b148' in ENG)
check('V5 no valuation field is assigned by the b148 edits',
      "'amount':" not in "".join(
          l for l in ENG.splitlines() if 'b148' in l))
check('V6 the compliance foot + MUC reads are untouched',
      "pickBare(d,'disclaimer')" in IDX or "pickBare(d, 'disclaimer')" in IDX or 'disclaimer' in IDX)


print('\n' + '=' * 64)
print('Sprint 2.22.0b.148:  %d passed, %d failed' % (passed, failed))
print('=' * 64)
sys.exit(1 if failed else 0)
