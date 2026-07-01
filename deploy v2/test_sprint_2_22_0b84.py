# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.84 — EN twins for the VALUE-DECOMPOSITION note bodies
(`_decompose_value` + `_reconcile_decomposition_narrative`). E14: exercises the
REAL production functions in evaluate_unified.py. BACKEND-ONLY / VALUE-INVARIANT —
additive `*_en` keys alongside the untouched `*_ar`; EN dormant (frontend reads
them via pick() only when LANG=='en', b77). AR output byte-identical (asserted).
The frontend already consumes pick(bd,'interpretation') / pick(vd,'methodology_note')
/ pick(ld,'confidence') since b81/b83 → index.html UNTOUCHED (R14 N/A by construction)."""
import io
import evaluate_unified as eu

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('  ok  ', name)
    else:    failed += 1; print('  FAIL', name)

def _ref(median, n, reliable=False):
    return {'categories': {'land': {'price_per_m2': {'median': median},
            'n': n, 'window_months': 24, 'reliable': reliable}}}

# ── (1) _decompose_value emits the _en twins, per status branch ──
# building_dominant: plot 500 × 2000 = land 1,000,000 ; value 2,000,000 → bld 50%
d_dom = eu._decompose_value(2000000, 500, 300, _ref(2000, 25, True))
check('building_dominant: dict returned', bool(d_dom))
ld = d_dom['land']; bi = d_dom['building_implied']
check('land.confidence_en present + reliable→Sufficient',
      ld.get('confidence_en') == 'Sufficient evidence' and ld.get('confidence_ar') == 'شواهد كافية')
check('building_implied.interpretation_en present (high share) + carries the pct',
      'high share' in bi.get('interpretation_en', '') and '50.0%' in bi.get('interpretation_en', ''))
check('methodology_note_en present + cites RICS Red Book',
      'RICS Red Book' in d_dom.get('methodology_note_en', '') and 'implied building value' in d_dom.get('methodology_note_en', ''))
# AR byte-identical (value-invariance of the AR surface)
check('AR interpretation UNCHANGED (building_dominant)',
      bi.get('interpretation_ar') == ('البناء يساهم بنسبة عالية (50.0%) من القيمة — '
                                      'يتسق مع بناء جديد أو فاخر أو ذو BUA كبيرة.'))
check('AR methodology_note UNCHANGED', d_dom['methodology_note_ar'].startswith('يفصل ثمّن قيمة الأرض'))

# normal (0.15–0.35): value 1,300,000 land 1,000,000 → 23.1%
d_nrm = eu._decompose_value(1300000, 500, 300, _ref(2000, 12))
check('normal: interpretation_en "within the typical range" + pct',
      'within the' in d_nrm['building_implied']['interpretation_en'] and '23.1%' in d_nrm['building_implied']['interpretation_en'])
check('normal n=12 → indicative→Limited evidence',
      d_nrm['land']['confidence_en'] == 'Limited evidence')

# building_modest (0.05–0.15): value 1,120,000 → 10.7%
d_mod = eu._decompose_value(1120000, 500, 300, _ref(2000, 6))
check('building_modest: interpretation_en "limited share"',
      'limited share' in d_mod['building_implied']['interpretation_en'])
check('modest n=6 → thin→Insufficient evidence',
      d_mod['land']['confidence_en'] == 'Insufficient evidence')

# land_dominant (<0.05): value 1,040,000 → 3.8%
d_lnd = eu._decompose_value(1040000, 500, 300, _ref(2000, 25))
check('land_dominant: interpretation_en "very small share"',
      'very small share' in d_lnd['building_implied']['interpretation_en'])

# ── (2) value-math untouched (additive keys only) ──
check('land estimated_qar = plot×per_m2 (unchanged formula)', d_dom['land']['estimated_qar'] == 1000000)
check('building_implied.qar = value − land (unchanged)', d_dom['building_implied']['qar'] == 1000000)
check('as_pct_of_total unchanged (50.0)', d_dom['building_implied']['as_pct_of_total'] == 50.0)

# ── (3) _reconcile_decomposition_narrative sets interpretation_en (Case A + C) ──
def _out(dom_name, dom_label_ar, dom_label_en, share, age):
    dd = eu._decompose_value(2000000, 500, 300, _ref(2000, 25, True))  # building_dominant
    return {'asset_type': 'standalone_villa',
            'valuation': {'value_decomposition': dd, 'user_inputs': {}},
            'stock_strata': {'dominant_stratum': {'name': dom_name, 'label_ar': dom_label_ar,
                             'label_en': dom_label_en, 'share_pct': share, 'note_ar': 'ملاحظة الفئة.'}},
            'property_basis': {'building_age_estimate': {'age_floor_years': age, 'age_basis': 'surveyed'}}}

oA = _out('luxury_new', 'فاخر جديد', 'Luxury new', 52, 20)  # old + premium pool → Case A
eu._reconcile_decomposition_narrative(oA)
biA = oA['valuation']['value_decomposition']['building_implied']
check('Case A: narrative_case A', biA.get('narrative_case') == 'A')
check('Case A: interpretation_ar overwritten (pool artifact)', 'لا قيمةَ بناءٍ فعليّة' in biA.get('interpretation_ar', ''))
check('Case A: interpretation_en overwritten + consistent (no real building value / luxury build / share)',
      'no real building' in biA.get('interpretation_en', '') and 'luxury build' in biA.get('interpretation_en', '')
      and '52% of the sample' in biA.get('interpretation_en', '') and 'Luxury new' in biA.get('interpretation_en', ''))
check('Case A: EN is NOT the stale un-reconciled building_dominant line',
      'consistent with a new, luxury, or large-BUA building' not in biA.get('interpretation_en', ''))

oC = _out('aging_stock', 'مخزون متقادم', 'Aging stock', 40, 20)  # old but NOT premium pool → Case C
eu._reconcile_decomposition_narrative(oC)
biC = oC['valuation']['value_decomposition']['building_implied']
check('Case C: narrative_case C', biC.get('narrative_case') == 'C')
check('Case C: interpretation_en set (indicative upper bound)',
      'indicative upper bound' in biC.get('interpretation_en', '') and 'not a direct measurement' in biC.get('interpretation_en', ''))

# ── (4) frontend wiring intact (index.html reads these via pick — unchanged from b81/b83) ──
HTML = io.open('index.html', encoding='utf-8').read()
check('frontend reads pick(bd,interpretation) + pick(vd,methodology_note) + pick(ld,confidence)',
      "pick(bd,'interpretation')" in HTML and "pick(vd,'methodology_note')" in HTML and "pick(ld,'confidence')" in HTML)

# ── (5) engine bump (format only — R6 / Lesson-2: no exact pin) ──
check('engine is a valid b-series tag', eu.SPRINT_TAG.startswith('2.22.0b.') and eu.ENGINE_VERSION.startswith('thammen-sprint2p22p0b'))

print('\nb84:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
