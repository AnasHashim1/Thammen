# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.14 — decomposition coherence + report-voice (ISS-A07).
Isolated tests on the PRODUCTION helpers (Rule #40 / E14). VALUE-INVARIANT contract
(§4) is the spine: the post-pass rewrites ONLY narrative TEXT — never amount/range/
method/floor/% /strata-numbers. Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b14.py
"""
import sys
from evaluate_unified import _reconcile_decomposition_narrative
from material_uncertainty import assess_uncertainty
from output_briefs import build_cap_rate_provenance_section

P = F = 0
def ck(name, cond):
    global P, F
    if cond: P += 1; print(f"  ok  {name}")
    else:    F += 1; print(f"FAIL  {name}")

def marikh():
    return {
        'asset_type': 'standalone_villa',
        'valuation': {
            'amount': 5400000, 'low': 2400000, 'high': 5500000, 'method': 'comparison_thin',
            'user_inputs': {'condition': None, 'is_luxury': None, 'age_source': None, 'building_age_years': None},
            'value_decomposition': {
                'land': {'estimated_qar': 1851260, 'per_m2_qar': 3020},
                'building_implied': {'qar': 3548740, 'as_pct_of_total': 65.7,
                    'status': 'building_dominant',
                    'interpretation_ar': 'البناء يساهم بنسبة عالية (65.7%) من القيمة — يتسق مع بناء جديد أو فاخر أو ذو BUA كبيرة.'},
            },
        },
        'stock_strata': {'dominant_stratum': {'name': 'luxury_new', 'label_ar': 'فاخر / حديث البناء',
                                              'share_pct': 51.7, 'note_ar': 'الفئة المسيطرة على عينة المنطقة.'}},
        'property_basis': {'building_age_estimate': {'age_floor_years': 17, 'age_basis': 'vintage_capped'}},
    }

# ── Case A (the Marikh case) ──
o = marikh()
bi0 = dict(o['valuation']['value_decomposition']['building_implied'])
_reconcile_decomposition_narrative(o)
bi = o['valuation']['value_decomposition']['building_implied']
interp = bi['interpretation_ar']
ck("A: narrative_case == 'A'", bi.get('narrative_case') == 'A')
ck("A: pct interpolated (65.7%)", '65.7%' in interp)
ck("A: dominant label «فاخر / حديث البناء»", 'فاخر / حديث البناء' in interp)
ck("A: share 51.7% من العيّنة", '51.7% من العيّنة' in interp)
ck("A: «لا قيمةَ بناءٍ فعليّة لعقارٍ بهذا العمر»", 'لا قيمةَ بناءٍ فعليّة لعقارٍ بهذا العمر' in interp)
ck("A: cross-refs «قاعدة الـ10 سنوات»", 'قاعدة الـ10 سنوات' in interp)
ck("A: CTA «اختر «بناء فاخر» وأعد التقدير»", 'اختر «بناء فاخر» وأعد التقدير' in interp)
ck("A: line CHANGED from default", interp != bi0['interpretation_ar'])
ck("A: reverse cross-line on dom note_ar", 'يرفع نسبة «البناء الضمني»' in o['stock_strata']['dominant_stratum']['note_ar'])
# §4 value-invariance — numeric fields byte-identical
ck("A§4: amount unchanged", o['valuation']['amount'] == 5400000)
ck("A§4: low/high unchanged", o['valuation']['low'] == 2400000 and o['valuation']['high'] == 5500000)
ck("A§4: method unchanged", o['valuation']['method'] == 'comparison_thin')
ck("A§4: land value unchanged", o['valuation']['value_decomposition']['land']['estimated_qar'] == 1851260)
ck("A§4: building VALUE unchanged", bi['qar'] == 3548740)
ck("A§4: as_pct_of_total unchanged (no basis shift)", bi['as_pct_of_total'] == 65.7)

# ── Case A via modern_stock + age_floor>10 (not vintage_capped) ──
o = marikh(); o['stock_strata']['dominant_stratum'] = {'name': 'modern_stock', 'label_ar': 'بناء حديث جيد', 'share_pct': 40.0, 'note_ar': ''}
o['property_basis']['building_age_estimate'] = {'age_floor_years': 14, 'age_basis': 'qars_survey'}
_reconcile_decomposition_narrative(o)
ck("A2: modern_stock + age 14 → Case A", o['valuation']['value_decomposition']['building_implied'].get('narrative_case') == 'A')

# ── Case B: user luxury ──
o = marikh(); o['valuation']['user_inputs']['is_luxury'] = True
_reconcile_decomposition_narrative(o)
biB = o['valuation']['value_decomposition']['building_implied']
ck("B: is_luxury → narrative_case 'B'", biB.get('narrative_case') == 'B')
ck("B: keeps the «بناء جديد أو فاخر» line", 'يتسق مع بناء جديد أو فاخر' in biB['interpretation_ar'])

# ── Case B: condition renovated ──
o = marikh(); o['valuation']['user_inputs']['condition'] = 'renovated'
_reconcile_decomposition_narrative(o)
ck("B: condition renovated → Case B", o['valuation']['value_decomposition']['building_implied'].get('narrative_case') == 'B')

# ── Case B: genuinely new (age 3, survey basis) ──
o = marikh(); o['property_basis']['building_age_estimate'] = {'age_floor_years': 3, 'age_basis': 'qars_survey'}
_reconcile_decomposition_narrative(o)
ck("B: age 3 non-vintage → Case B", o['valuation']['value_decomposition']['building_implied'].get('narrative_case') == 'B')

# ── Case C: old but NOT premium pool ──
o = marikh(); o['stock_strata']['dominant_stratum'] = {'name': 'aging_stock', 'label_ar': 'بناء قديم', 'share_pct': 60.0, 'note_ar': ''}
_reconcile_decomposition_narrative(o)
biC = o['valuation']['value_decomposition']['building_implied']
ck("C: aging_stock → narrative_case 'C'", biC.get('narrative_case') == 'C')
ck("C: «حدّ أعلى استدلاليّ»", 'حدّ أعلى استدلاليّ' in biC['interpretation_ar'])

# ── Guards ──
o = marikh(); o['valuation']['value_decomposition']['building_implied']['status'] = 'normal'
b4 = o['valuation']['value_decomposition']['building_implied']['interpretation_ar']
_reconcile_decomposition_narrative(o)
ck("guard: status!=building_dominant → untouched", o['valuation']['value_decomposition']['building_implied']['interpretation_ar'] == b4)

o = marikh(); o['asset_type'] = 'apartment_building'
b5 = o['valuation']['value_decomposition']['building_implied']['interpretation_ar']
_reconcile_decomposition_narrative(o)
ck("guard: non-villa asset → untouched", o['valuation']['value_decomposition']['building_implied']['interpretation_ar'] == b5)

ck("guard: no value_decomposition → no crash", (_reconcile_decomposition_narrative({'asset_type':'standalone_villa','valuation':{}}) is None))
ck("guard: malformed/None → no crash", (_reconcile_decomposition_narrative(None) is None) and (_reconcile_decomposition_narrative({}) is None))

# ── Leak #1: service-charge MUC factor (villa softened, strata kept; LEVEL invariant) ──
uv = assess_uncertainty(moj_n=15, rent_n=0, trend_n_years=6, service_charge_confidence='estimated', asset_type='standalone_villa')
ua = assess_uncertainty(moj_n=15, rent_n=0, trend_n_years=6, service_charge_confidence='estimated', asset_type='apartment_building')
fv = ' | '.join(getattr(uv, 'factors', []) or [])
fa = ' | '.join(getattr(ua, 'factors', []) or [])
ck("leak1: villa → «مصاريف تشغيل تقديريّة ضمن الفحص الدخليّ»", 'مصاريف تشغيل تقديريّة ضمن الفحص الدخليّ' in fv)
ck("leak1: villa drops «رسوم الخدمات … لهذا المبنى»", 'رسوم الخدمات تقديرية — ليست مُتحقَّقة لهذا المبنى' not in fv)
ck("leak1: strata KEEPS «رسوم الخدمات … لهذا المبنى»", 'رسوم الخدمات تقديرية — ليست مُتحقَّقة لهذا المبنى' in fa)
ck("leak1: MUC level value-invariant (villa == strata)", getattr(uv, 'level', None) == getattr(ua, 'level', None))

# ── Leak #2: cap-rate borrow disclosure ──
prov_b = {'source': 'calibrated', 'cap_rate_pct': 5.16, 'sample_size': 46, 'confidence': 'reliable',
          'last_updated': '2026-06-07', 'bracket_borrowed': True, 'borrowed_from_bracket': '400-600', 'subject_bracket': '600-900'}
sb = build_cap_rate_provenance_section(prov_b)
body_b = (sb or {}).get('content', {}).get('body_ar', '') if isinstance(sb, dict) else ''
# fall back: some builders return the body at top level
body_b = body_b or (sb.get('body_ar', '') if isinstance(sb, dict) else '')
ck("leak2: borrowed → discloses «مُستعار من الشريحة 400-600»", 'مُستعار من الشريحة 400-600' in body_b)
ck("leak2: borrowed → «شريحة العقار 600-900 بلا عيّنة كافية»", 'شريحة العقار 600-900 بلا عيّنة كافية' in body_b)
ck("leak2: borrowed → drops bare «لنفس المنطقة والشريحة»", 'وزارة العدل لنفس المنطقة والشريحة —' not in body_b)

prov_s = dict(prov_b); prov_s['bracket_borrowed'] = False
ss = build_cap_rate_provenance_section(prov_s)
body_s = (ss or {}).get('content', {}).get('body_ar', '') if isinstance(ss, dict) else ''
body_s = body_s or (ss.get('body_ar', '') if isinstance(ss, dict) else '')
ck("leak2: same-bracket → keeps «لنفس المنطقة والشريحة» (byte-identical)", 'لنفس المنطقة والشريحة' in body_s and 'مُستعار' not in body_s)

print(f"\n{P} passed, {F} failed")
sys.exit(1 if F else 0)
