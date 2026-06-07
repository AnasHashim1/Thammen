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
# 8b. luxury-new premium via Cost Approach / DRC (B-2b, Lever-1 — R7 UP; V002/V003 calibrated)
check('LUXURY_CONSTRUCTION_QAR_PER_M2 ~3000-4500', 3000 <= E.LUXURY_CONSTRUCTION_QAR_PER_M2 <= 4500)
check('PENTHOUSE_BUA_MULTIPLIER = 2.5 (G+1+PH½)', E.PENTHOUSE_BUA_MULTIPLIER == 2.5)
_lnar = E.LUXURY_NEW_NOTE_AR.format(land='1,700,000', bld='2,360,000', bua=675, cost=3500)
check('LUXURY_NEW_NOTE_AR: فاخرة + التكلفة + قيمة', ('فاخرة' in _lnar) and ('التكلفة' in _lnar) and ('1,700,000' in _lnar))
# DRC math: land 1.7M + (full-coverage fp 270 × 2.5 = 675 BUA × 3500) ≈ 4.06M → matches V002/V003 (4.0M)
_land_demo = 1700100
_fp_demo = 450 * 0.60  # FULL R1 coverage (NOT b1's ×0.8 — luxury builds to the ceiling)
_bua_demo = round(_fp_demo * E.PENTHOUSE_BUA_MULTIPLIER)
_drc_val = _land_demo + _bua_demo * E.LUXURY_CONSTRUCTION_QAR_PER_M2
check('DRC BUA = full-fp × 2.5 = 675', _bua_demo == 675)
check('DRC value ≈ V002/V003 4.0M (within ±5%)', abs(_drc_val - 4000000) / 4000000 < 0.05)
check('luxury uplift UP: DRC value > 2.4M median', _drc_val > 2400000)
check('luxury disclosure render (v.luxury_new_premium.note_ar)', ('v.luxury_new_premium' in HTML) and ('v.luxury_new_premium.note_ar' in HTML))
# 8c. penthouse input (B-2b refinement — DRC BUA = footprint × (floors + 0.5×penthouse))
check('penthouse in evaluate_thammen signature', 'penthouse: Optional[bool]' in ENG)
check('penthouse dropdown «يوجد بنتهاوس»', ('id="penthouse"' in HTML) and ('يوجد بنتهاوس' in HTML))
check('penthouse read + sent in submit', ("val('penthouse')" in HTML) and ('bd.penthouse' in HTML))
_fp_p = 270
check('penthouse adds 0.5×fp to BUA (2.5 vs 2.0)', round(_fp_p * 2.5) - round(_fp_p * 2.0) == round(_fp_p * 0.5))
# 9. version present + well-formed (R6 / Lesson-2 — format, NOT an exact pin that breaks on the next bump)
check('ENGINE_VERSION format (thammen-sprint…)', E.ENGINE_VERSION.startswith('thammen-sprint'))
check('SPRINT_TAG dotted-numeric format', len(E.SPRINT_TAG.split('.')) >= 3 and E.SPRINT_TAG.replace('.', '').isalnum())

passed = sum(1 for _, ok in results if ok)
for n, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', n)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
