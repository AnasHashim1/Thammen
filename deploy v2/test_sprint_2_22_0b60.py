# -*- coding: utf-8 -*-
# Sprint 2.22.0b.60 — «شرح تعذّر التصنيف» (A5: explain asset_type='unknown').
# FRONTEND-ONLY, VALUE-INVARIANT (engine = the 2 version-string lines; api.py UNTOUCHED).
#
# A5 (the last open Medium bug) recon (Rule #58, measured live v230/b58): a `classifier_failure`
# 'unknown' case (e.g. 70/300/25, 53/240/12) returns the SPECIFIC explanation at top-level
# `d.refusal_reason.message_ar` («…قد يكون العنوان غير مفهرس… نوصي بالتحقّق/التواصل») + a
# `recommendation_ar`, BUT the result-screen refusal card used only `v.reason_ar` (=None for
# classifier_failure) → it fell back to the GENERIC «لا تتوفر بيانات كافية» AND showed a
# MISLEADING «→ أضف الإيجار أو سعر الإعلان» CTA (rent/price can't classify an unindexed
# address). The §5 trap: the explanation was in the JSON but not surfaced on screen.
#
# b60 surfaces it (display-only, value-invariant): the refusal card now PREFERS
# `d.refusal_reason.message_ar` for the reason, gives an honest title for 'unknown'
# («تعذّر تحديد نوع العقار»), shows the `recommendation_ar` as the actionable next step, and
# SUPPRESSES the misleading rent CTA for 'unknown'. Known-type refusals (compound needs rent,
# etc.) are UNCHANGED. The reality-stop path (also 'unknown', but with `v.reason_ar`=_msg +
# the asset_type_reality panel) keeps showing its own message via the v.reason_ar precedence.
import re, pathlib
import refusal_templates as rt

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG  = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── 1. the refusal-card reason now prefers the specific refusal_reason explanation ──
check('reason prefers d.refusal_reason.message_ar (then generic fallback)',
      "const reason=pick(v,'reason')||(d.refusal_reason&&pick(d.refusal_reason,'message'))||t('لا تتوفر بيانات كافية" in HTML)
check('generic fallback string still present (last resort)',
      'لا تتوفر بيانات كافية لتقييم هذا العقار حالياً.' in HTML)

# ── 2. honest title for the unclassifiable case (not the misleading «needs more data») ──
check('unknown → honest h2 «تعذّر تحديد نوع العقار»',
      "d.asset_type==='unknown'?t('تعذّر تحديد نوع العقار','Could not determine the property type'):t('التقييم يحتاج بيانات إضافية','The valuation needs more data')" in HTML)
check('known-type refusal keeps «التقييم يحتاج بيانات إضافية»',
      'التقييم يحتاج بيانات إضافية' in HTML)
check('b36 apartment/tower title untouched',
      'غير مدعومة بعد — للفلل والأراضي فقط' in HTML)

# ── 3. recommendation surfaced + misleading rent CTA suppressed FOR UNKNOWN ──
check('unknown branch exists (before the known-type CTA)',
      "if(!_ux3NotReady&&d.asset_type==='unknown'){" in HTML)
check('recommendation rendered from refusal_reason.recommendation_ar (reuses .rr-recommendation)',
      "class=\"rr-recommendation\"" in HTML and 'd.refusal_reason&&d.refusal_reason.recommendation_ar' in HTML
      and "<strong>'+t('التوصية:'" in HTML)  # b138: t()-wrapped, AR arg verbatim
check('known-type refusals KEEP their input-unlock CTA (else-if branch)',
      '}else if(!_ux3NotReady){' in HTML)
# the rent CTA must live ONLY in the else-if (known-type) branch, not the unknown branch.
_unknown_branch = HTML.split("if(!_ux3NotReady&&d.asset_type==='unknown'){",1)[1].split('}else if(!_ux3NotReady){',1)[0]
check('NO «أضف الإيجار» CTA inside the unknown branch',
      'أضف الإيجار' not in _unknown_branch and 'insuf-cta' not in _unknown_branch)
_known_branch = HTML.split('}else if(!_ux3NotReady){',1)[1][:600]
check('the rent CTA IS in the known-type else-if branch',
      'insuf-cta' in _known_branch and 'أضف الإيجار أو سعر الإعلان' in _known_branch)

# ── 4. value-invariance: no headline mutation; engine = version-string only ──
check('no mutation of v.amount/v.low/v.high in index.html',
      not re.search(r'\bv\.(amount|low|high)\s*=[^=]', HTML))
check('ENGINE_VERSION format (thammen-sprint…)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('engine at/beyond b60 (b59 tag gone)', 'thammen-sprint2p22p0b59' not in ENG)

# ── 5. the explanation SOURCE exists (the classifier_failure template, the A5 surface) ──
tpl = rt.get_refusal_template('classifier_failure', asset_type='unknown')
check('classifier_failure template has a clear message_ar (the «why»)',
      isinstance(tpl.get('message_ar'), str) and 'لم نتمكّن من تحديد نوع العقار' in tpl['message_ar'])
check('classifier_failure template has a recommendation_ar (the action)',
      isinstance(tpl.get('recommendation_ar'), str) and len(tpl['recommendation_ar']) > 5)
# b60 linguist-persona refinement: message_ar = WHY only (the action sentence was
# trimmed — it duplicated recommendation_ar on the screen), and «QARS» is clarified.
check('linguist: message_ar de-duped (no «نوصي بالتحقّق» action duplicate)',
      'نوصي بالتحقّق' not in tpl['message_ar'])
check('linguist: «QARS» clarified to «سجلّ العناوين الحكوميّ (QARS)»',
      'سجلّ العناوين الحكوميّ' in tpl['message_ar'] and 'QARS' in tpl['message_ar'])
check('a2.b phrase contract still holds (key phrases intact)',
      'لم نتمكّن من تحديد نوع العقار' in tpl['message_ar'] and 'القاعدة الحكومية' not in tpl['message_ar']
      and 'تحقّق من بيانات العنوان' in tpl['recommendation_ar'])
# spatial_ambiguity (the reality-stop 'unknown' sibling) also carries an explanation
tpl2 = rt.get_refusal_template('spatial_ambiguity', asset_type='unknown')
check('spatial_ambiguity template also carries message_ar + recommendation_ar',
      bool(tpl2.get('message_ar')) and bool(tpl2.get('recommendation_ar')))

# ── 6. the early-return for unknown still assembles head+muc+a8acc+alerts+flat ──
check('unknown refusal early-return intact (renders the insuf card)',
      "if(d.asset_type==='unknown'||!d.asset_type){o.innerHTML=head+muc+a8acc+alerts+flat;return}" in HTML)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
