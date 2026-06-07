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

# 1. demolition constant present + PO-calibrated (~200/m² → mid-villa 500m² ≈ 100k QAR)
check('DEMO_QAR_PER_M2 PO-calibrated [100,300]', 100 <= E.DEMO_QAR_PER_M2 <= 300)
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
# 5. teardown math — DOWN-anchor below the median; demolition CLAMPED to the PO band [100k,150k]
bua = 405
demo = min(max(round(E.DEMO_QAR_PER_M2 * bua), E.DEMO_FLOOR_QAR), E.DEMO_CAP_QAR)
central = max(lf - demo, 0)
def _demo_of(b):
    return min(max(round(E.DEMO_QAR_PER_M2 * b), E.DEMO_FLOOR_QAR), E.DEMO_CAP_QAR)
check('demo clamped to PO band [100k,150k]', E.DEMO_FLOOR_QAR <= demo <= E.DEMO_CAP_QAR)
check('small villa 250m² floors at 100k', _demo_of(250) == 100000)
check('mid villa 500m² ≈ 120k', _demo_of(500) == 120000)
check('large villa 1000m² caps at 150k', _demo_of(1000) == 150000)
check('teardown re-anchors DOWN (< 2.4M median)', 0 < central < 2400000)
check('central = land_floor − demo (≥0)', central == max(lf - demo, 0))
# 6. condition→reno: teardown safe default (no renovation premium, no crash)
check('teardown reno = (False,False)', E._condition_to_reno('teardown') == (False, False))
# 7. CLI accepts teardown
check('CLI --condition includes teardown', "'fair', 'poor', 'teardown'" in ENG)
# 8. index.html dropdown option + disclosure render
check('dropdown «آيل للسقوط / يجب هدمه» value=teardown', 'value="teardown">آيل للسقوط' in HTML)
check('teardown disclosure render (v.teardown.note_ar)', ('v.teardown' in HTML) and ('v.teardown.note_ar' in HTML))
# 8b. luxury-new premium (B-2b, Lever-1 — the UP direction of R7; V002/V003 +67% → +60% applied)
check('LUXURY_NEW_PREMIUM ~0.4-0.7', 0.4 <= E.LUXURY_NEW_PREMIUM <= 0.7)
check('luxury low < central < high', E.LUXURY_NEW_PREMIUM_LOW < E.LUXURY_NEW_PREMIUM < E.LUXURY_NEW_PREMIUM_HIGH)
_lnar = E.LUXURY_NEW_NOTE_AR.format(med='2,400,000', val='3,840,000')
check('LUXURY_NEW_NOTE_AR: فاخرة + علاوة + قيمة', ('فاخرة' in _lnar) and ('علاوة' in _lnar) and ('3,840,000' in _lnar))
_med_demo = 2400000
check('luxury uplift UP: median 2.4M -> 3.84M central', round(_med_demo * (1 + E.LUXURY_NEW_PREMIUM)) == 3840000)
check('luxury central > median (UP direction)', _med_demo * (1 + E.LUXURY_NEW_PREMIUM) > _med_demo)
check('luxury high toward GT (~4.08M)', round(_med_demo * (1 + E.LUXURY_NEW_PREMIUM_HIGH)) == 4080000)
check('luxury disclosure render (v.luxury_new_premium.note_ar)', ('v.luxury_new_premium' in HTML) and ('v.luxury_new_premium.note_ar' in HTML))
# 9. version present + well-formed (R6 / Lesson-2 — format, NOT an exact pin that breaks on the next bump)
check('ENGINE_VERSION format (thammen-sprint…)', E.ENGINE_VERSION.startswith('thammen-sprint'))
check('SPRINT_TAG dotted-numeric format', len(E.SPRINT_TAG.split('.')) >= 3 and E.SPRINT_TAG.replace('.', '').isalnum())

passed = sum(1 for _, ok in results if ok)
for n, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', n)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
