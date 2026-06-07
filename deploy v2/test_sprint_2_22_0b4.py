# -*- coding: utf-8 -*-
# Sprint 2.22.0b.4 (B-2a) — teardown demolition down-anchor.
# Tests the PRODUCTION constants + the _villa_value_floor reuse (E14) + the teardown
# math (down-anchor) + the index.html surfaces + version bump. The live engine
# INJECTION (4263-block) is covered by the local E2E (.td_e2e.py) + post-deploy smoke.
import pathlib
import evaluate_unified as E

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
results = []
def check(n, c):
    results.append((n, bool(c)))

# 1. demolition constant present + within the documented 40-100 band
check('DEMO_QAR_PER_M2 in [40,100]', 40 <= E.DEMO_QAR_PER_M2 <= 100)
# 2. teardown scope = villa/house only
check('_TEARDOWN_ASSET_TYPES = villa/house', set(E._TEARDOWN_ASSET_TYPES) >= {'standalone_villa', 'house', 'villa'})
check('teardown excludes apartment/land', 'apartment_building' not in E._TEARDOWN_ASSET_TYPES and 'raw_land' not in E._TEARDOWN_ASSET_TYPES)
# 3. bilingual notes formattable
ar = E.TEARDOWN_NOTE_AR.format(land='1,700,000', demo='24,000')
en = E.TEARDOWN_NOTE_EN.format(land='1,700,000', demo='24,000')
check('TEARDOWN_NOTE_AR: الأرض + هدم + value', ('الأرض' in ar) and ('هدم' in ar) and ('1,700,000' in ar))
check('TEARDOWN_NOTE_EN: land + demolition', ('land' in en.lower()) and ('demolition' in en.lower()))
# 4. _villa_value_floor (PRODUCTION, E14) yields a land floor to re-anchor on (F1 path)
moj = {'categories': {'land': {'price_per_m2': {'median': 3800}, 'n': 25, 'reliable': True, 'window_months': 24}}}
vf = E._villa_value_floor(2400000, 450, moj, None)
check('_villa_value_floor returns land_floor', bool(vf and vf.get('land_floor')))
lf = (vf or {}).get('land_floor') or 0
# 5. teardown math — DOWN-anchor below the comparison median, ≥ 0
bua = 405
demo = round(E.DEMO_QAR_PER_M2 * bua)
central = max(lf - demo, 0)
check('demo = 60 × BUA', demo == 60 * 405)
check('teardown re-anchors DOWN (< 2.4M median)', 0 < central < 2400000)
check('central = land_floor − demo (≥0)', central == max(lf - demo, 0))
# 6. condition→reno: teardown safe default (no renovation premium, no crash)
check('teardown reno = (False,False)', E._condition_to_reno('teardown') == (False, False))
# 7. CLI accepts teardown
check('CLI --condition includes teardown', "'fair', 'poor', 'teardown'" in ENG)
# 8. index.html dropdown option + disclosure render
check('dropdown «آيل للسقوط / يجب هدمه» value=teardown', 'value="teardown">آيل للسقوط' in HTML)
check('teardown disclosure render (v.teardown.note_ar)', ('v.teardown' in HTML) and ('v.teardown.note_ar' in HTML))
# 9. version present + well-formed (R6 / Lesson-2 — format, NOT an exact pin that breaks on the next bump)
check('ENGINE_VERSION format (thammen-sprint…)', E.ENGINE_VERSION.startswith('thammen-sprint'))
check('SPRINT_TAG dotted-numeric format', len(E.SPRINT_TAG.split('.')) >= 3 and E.SPRINT_TAG.replace('.', '').isalnum())

passed = sum(1 for _, ok in results if ok)
for n, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', n)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
