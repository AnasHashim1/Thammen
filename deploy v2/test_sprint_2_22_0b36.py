# -*- coding: utf-8 -*-
# Sprint 2.22.0b.36 — DEF-UX3: honest apartment/tower refusal (result screen).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only). Reads the REAL
# index.html (E14 / Rule #40 for the frontend lane) + asserts the engine version bump + that the
# engine scope contract (scope_of_service.py) is UNTOUCHED (the income product is the deferred
# «بوابة الأنواع» (أ) — we only change the UI framing, never the computation).
#
# What this verifies (ISSUES_LOG §4ب-2 DEF-UX3; the 8/10-persona «بطاقة أضف الإيجار مُضلِّلة»):
#   On the refusal (no value) for apartment_building + tower (the income-only types whose product
#   is the DEFERRED «بوابة الأنواع» (أ)), the result screen presents them as honestly NOT-YET-
#   SUPPORTED («ثمّن للفلل والأراضي فقط») instead of «⚠️ تقييم مشروط · منهج الدخل · يتطلب الإيجار»,
#   AND the misleading «→ أدخل: الإيجار» income deep-link CTA is SUPPRESSED. Other refusals
#   (compound_large = the methodologically-correct Income path per E20, palace = Cost) are
#   UNCHANGED. The with-value income case (a power user supplied rent → hasValuation) is byte-
#   identical (both surfaces gate on !hasValuation). Anas signed: scope = apartment+tower; remove
#   the rent CTA (recon-reshaped: spec parts «client-side pre-API detect» + «disable types in tab»
#   are infeasible/deferred — no client-side asset type [E17], no asset-type tab).
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')
SCOPE = (ROOT / 'scope_of_service.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# isolate show() so the refusal-surface assertions are scoped to the results renderer.
_sh_start = HTML.index('function show(d){')
_sh_end = HTML.index('\nfunction pctFmt(', _sh_start)
SHOW = HTML[_sh_start:_sh_end]

# isolate the scope-badge block (surface 1) and the insufficient-data box (surface 2)
_ss_start = SHOW.index('const ss=d.service_scope;')
_ss_end = SHOW.index('// ── Sprint 2.22.0b.22: ignored tower pair', _ss_start)
BADGE = SHOW[_ss_start:_ss_end]
_insuf_start = SHOW.index("flat+='<div class=\"insuf\">'")
_insuf_end = SHOW.index('// For unknown/no district', _insuf_start)
INSUF = SHOW[_insuf_start:_insuf_end]

# ── 0. engine version bump (frontend-only → version strings are the only engine diff) ──
# R6/Lesson-2 re-point (b37): the exact-version pin broke the broad walk on the next bump —
# the project's own «no exact version pins» rule. The behavior checks below still prove b36 shipped.
check('ENGINE_VERSION is a valid thammen-sprint tag', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG is dotted-numeric', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('no stale b35 engine tag left', "sprint2p22p0b35-buyer-financing-calc" not in ENG)

# ── 1. the predicate: apartment_building + tower, ONLY on the refusal (no value) ──
check('_ux3NotReady = (apartment_building || tower) && !hasValuation',
      re.search(r"_ux3NotReady=\(d\.asset_type==='apartment_building'\|\|d\.asset_type==='tower'\)&&!hasValuation", SHOW) is not None)
check('_ux3Noun: tower→الأبراج else الشقق',
      re.search(r"_ux3Noun=\(d\.asset_type==='tower'\)\?'الأبراج':'الشقق'", SHOW) is not None)
# scope = apartment+tower ONLY — compound_large / palace are NOT in the predicate (they keep
# their own honest CTA: compound Income is the correct method per E20, palace = Cost).
check('compound_large NOT folded into _ux3NotReady', "compound_large'||d.asset_type==='tower" not in SHOW.replace("_ux3NotReady=(d.asset_type==='apartment_building'||d.asset_type==='tower')",""))
check('predicate names exactly apartment_building + tower (2 types)',
      SHOW.count("_ux3NotReady=(d.asset_type==='apartment_building'||d.asset_type==='tower')") == 1)

# ── 2. surface 1 — scope badge reframed honest, «يتطلب» dropped, methodology dropped ──
# b48 de-emoji (R6/Lesson-2): the 🚧 emoji became an inline-SVG icon (<use href=#ic-alert>).
# Pin the BEHAVIOUR (not-ready → bad styling + «غير مدعوم بعد» label, NOT «تقييم مشروط»), with the
# icon as an inline svg <use> rather than the literal emoji.
check('badge: _ux3NotReady → svg-icon «غير مدعوم بعد» (bad styling, not «تقييم مشروط»)',  # b88 R6: label now t()-wrapped (AR arg preserved)
      re.search(r"if\(_ux3NotReady\)\{scopeBg='var\(--bad-bg\)';scopeColor='var\(--bad\)';scopeIcon='<svg [^']*?<use href=#ic-[^>]*></use></svg>';scopeLabel=t\('غير مدعوم بعد','Not yet supported'\);\}", BADGE) is not None)
check('badge: methodology line («منهج الدخل») gated OFF for not-ready',  # b88 R6: ss.methodology_ar → pick(ss,'methodology'); gating unchanged
      "if(!_ux3NotReady)alerts+='<div style=\"font-size:.82rem;color:var(--muted)\">'+pick(ss,'methodology')+'</div>'" in BADGE)
check('badge: honest sub «ثمّن يدعم الفلل والأراضي فقط حالياً»',
      'ثمّن يدعم <strong>الفلل والأراضي</strong> فقط حالياً.' in BADGE)
# the «يتطلب» line now lives in the ELSE branch (NOT shown when _ux3NotReady)
_if_idx = BADGE.index('if(_ux3NotReady){')
_else_idx = BADGE.index('}else{', _if_idx)
_yt_idx = BADGE.index("<strong>'+t('يتطلب:'")  # b138: t()-wrapped, AR arg verbatim
check('badge: «يتطلب: الإيجار» line is INSIDE the else branch (suppressed for not-ready)',
      _yt_idx > _else_idx)
check('badge: the original disclaimer (ss.disclaimer_ar) only renders in the else branch',
      BADGE.index('ss.disclaimer_ar') > _else_idx)

# ── 3. surface 2 — insufficient-data box: honest header/why + CTA suppressed ──
# b48 de-emoji (R6/Lesson-2): the 🚧 emoji became an inline-SVG icon (<use href=#ic-alert>);
# the ⓘ (U+24D8) is unchanged. Pin the type-aware BEHAVIOUR (not-ready → svg-icon, else ⓘ).
check('insuf icon type-aware (svg-icon for not-ready, ⓘ otherwise)',
      re.search(r'<div class="insuf-icon">\'\+\(_ux3NotReady\?\'<svg [^\']*?<use href=#ic-[^>]*></use></svg>\':\'ⓘ\'\)\+\'</div>', INSUF) is not None)
check('insuf header: «{الشقق|الأبراج} غير مدعومة بعد — للفلل والأراضي فقط»',
      "_ux3Noun+' غير مدعومة بعد — للفلل والأراضي فقط'" in INSUF and 'التقييم يحتاج بيانات إضافية' in INSUF)
check('insuf why: «وزارة العدل لا تسجّل وحدات … فردياً … نعمل على دعم هذا النوع لاحقاً»',
      'وزارة العدل لا تسجّل وحدات ' in INSUF and 'نعمل على دعم هذا النوع لاحقاً' in INSUF)
# CTA suppression — the goForm income deep-link is gated behind if(!_ux3NotReady)
check('insuf: the «→ أدخل: الإيجار» CTA (goForm) is GATED behind if(!_ux3NotReady)',
      INSUF.index('if(!_ux3NotReady){') < INSUF.index("goForm(\\'") )
check('insuf: exactly one goForm CTA in the box, and it is the gated one (no unconditional lure)',
      INSUF.count("goForm(\\'") == 1)
check('insuf: other refusals keep the dynamic input CTA (focusTarget incl. compound_large)',
      "d.asset_type==='tower'||d.asset_type==='compound_large'" in INSUF)

# ── 4. value-invariance + frontend-only guards ──
check('both surfaces gate on !hasValuation → the with-value income case is untouched',
      '&&!hasValuation' in SHOW)
check('no v.amount / low / high mutation in show()', not re.search(r'v\.(amount|low|high)\s*=[^=]', SHOW))
# engine scope contract UNTOUCHED — apartment_building is STILL tier='limited' in the engine
# (we reframe the UI only; the income computation = the deferred «بوابة الأنواع» (أ)).
check('scope_of_service.py: apartment_building still tier=limited (engine income product untouched)',
      re.search(r"'apartment_building':\s*AssetScope\([^)]*?tier='limited'", SCOPE, re.S) is not None)
check('the income path artifacts still present (refine rent inputs + goForm fn intact)',
      'id="towerRentSection"' in HTML and 'function goForm(' in HTML)

# ── summary ──
passed = sum(1 for _, ok in results if ok)
total = len(results)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, total))
raise SystemExit(0 if passed == total else 1)
