# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.117 — EN completion for the ALWAYS-VISIBLE report note bodies that fell back to
Arabic in EN mode (the b78 catalog can't match dynamic notes with interpolated numbers/dates).
🟢 VALUE-INVARIANT — additive `_en` only; every `_ar` value + amount/method/rule untouched.

Scope (always-visible on every valued report): material_uncertainty.muc_basis + muc_review_recommendation
(engine-authored, dynamic date/days) · accuracy.explanation ×5 tiers (engine, dynamic n) · the very_stale
data-freshness caveat (b78 catalog, static date). E14: exercises the REAL functions.
"""
import io, re, sys, importlib

_p = _f = 0
def ck(name, cond, extra=''):
    global _p, _f
    if cond: _p += 1; print('  ok  ' + name)
    else:    _f += 1; print('  FAIL ' + name + ('  ' + extra if extra else ''))

# ── (1) material_uncertainty.regime_muc — muc_basis_en + muc_review_recommendation_en ──
import material_uncertainty as mu
d = mu.regime_muc()
ck('regime_muc emits muc_basis_en', bool(d.get('muc_basis_en')))
ck('muc_basis_en is English + faithful (Ministry of Justice)',
   'Ministry of Justice' in (d.get('muc_basis_en') or ''))
ck('muc_basis_ar UNCHANGED (still Arabic)', 'وزارة العدل' in (d.get('muc_basis_ar') or ''))
ck('regime_muc emits muc_review_recommendation_en',
   bool(d.get('muc_review_recommendation_en')) and 'Ministry of Justice' in d['muc_review_recommendation_en'])
ck('muc_review_recommendation_ar UNCHANGED', 'وزارة العدل' in (d.get('muc_review_recommendation_ar') or ''))
ck('the pre-existing muc_clause_en is intact (not broken)', bool(d.get('muc_clause_en')))
# value-invariance: no _ar key got an EN value / clobbered
ck('every *_ar value is still Arabic (additive-only)',
   all(re.search(r'[؀-ۿ]', v) for k, v in d.items() if k.endswith('_ar') and isinstance(v, str)))
# valued-path threading (the b117-fix): assess_uncertainty -> UncertaintyLevel carries the EN twins,
# so the main valued path (evaluate_v3 reads uncertainty.muc_basis_en) surfaces it — not just the fast/_enrich path.
_u = mu.assess_uncertainty(moj_n=37, asset_type='standalone_villa')
ck('UncertaintyLevel.muc_basis_en threaded (valued path)',
   bool(getattr(_u, 'muc_basis_en', None)) and 'Ministry of Justice' in (_u.muc_basis_en or ''))
ck('UncertaintyLevel.muc_review_recommendation_en threaded', bool(getattr(_u, 'muc_review_recommendation_en', None)))
ck('UncertaintyLevel muc_basis_ar UNCHANGED (AR)', bool(_u.muc_basis_ar) and re.search(r'[؀-ۿ]', _u.muc_basis_ar))

# ── (2) accuracy.explanation — 5 EN tiers beside the 5 AR tiers ──
EU = io.open('evaluate_unified.py', encoding='utf-8').read()
n_ar = len(re.findall(r"'explanation_ar':", EU))
n_en = len(re.findall(r"'explanation_en':", EU))
ck('accuracy: an explanation_en beside EVERY explanation_ar (n_ar==n_en, all 6 tiers)',
   n_ar == n_en and n_ar == 6)
ck('accuracy EN tiers keep the honest caveats (deviate / certified valuer / No valuation produced)',
   'may deviate' in EU and 'certified valuer' in EU and 'No valuation was produced' in EU)
ck('accuracy EN tiers use {n} where the AR does (dynamic — not a static string)',
   "'explanation_en': f'Based on {n}" in EU)

# ── (3) data-freshness very_stale caveat — via the b78 catalog ──
import en_localize; importlib.reload(en_localize)
_very_stale_ar = ("المرجع مبني على بيانات وزارة العدل المتاحة حتى 31 ديسمبر 2025. "
                  "الحكومة لم تنشر بيانات أحدث. النتائج إرشادية ولا تعكس بالضرورة الأسعار الحالية.")
obj = {'data_freshness': {'caveat_ar': _very_stale_ar}}
en_localize.attach_en(obj)
ce = obj['data_freshness'].get('caveat_en')
ck('freshness very_stale caveat gets an _en via the catalog', bool(ce))
ck('freshness caveat_en is faithful (indicative / not current prices)',
   'indicative' in (ce or '') and 'current prices' in (ce or ''))
ck('freshness caveat_ar UNCHANGED (additive)', obj['data_freshness']['caveat_ar'] == _very_stale_ar)
# never clobber an engine-authored _en
obj2 = {'x_ar': 'المخاطر والإشارات', 'x_en': 'PRESET'}
en_localize.attach_en(obj2)
ck('attach_en never clobbers an existing _en', obj2['x_en'] == 'PRESET')

# ── (4) version ──
ck('engine version is b117', "SPRINT_TAG = '2.22.0b.117'" in EU)

print('\nb117 (EN report notes): %d passed, %d failed' % (_p, _f))
sys.exit(1 if _f else 0)
