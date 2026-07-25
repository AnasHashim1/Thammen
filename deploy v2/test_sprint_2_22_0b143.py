# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.143 — «إنجليزيّة إفصاحات النطاق» (EN twins for the scope-of-service disclaimers/requires).

Isolated E14 test — reads the REAL en_localize / scope_of_service / evaluate_unified / index.html.
Sprint B, slice 2: the scope-of-service `disclaimer_ar` + `requires_user_input_ar` (both already
`pick()`-read on the result screen since b140) leaked in EN — the villa disclaimer renders on EVERY
valued villa result (the catalog key mismatched «صفقات آخر 24 شهراً» vs «نافذة 24 شهراً»), and the
compound_small / tower / palace / commercial / industrial / agricultural scopes had no `_en`. These are
all CONSTANT strings → 9 additive CATALOG entries let the scalar attach_en rule fill
`service_scope.disclaimer_en` / `requires_user_input_en`. FRONTEND UNTOUCHED (pick already there, b140) →
value-neutral, additive-only, AR mode byte-identical, amount/method/rule never touched.

  (1) COVERAGE — every scope (all asset types + the unknown fallback) gets `disclaimer_en` after
      attach_en on the REAL scope_to_dict output; `requires_user_input_en` when requires_ar is set
      (guards future drift — a scope-string edit that breaks the catalog match fails here).
  (2) the villa disclaimer (the main valued-path leak) is localized + on the locked termbase.
  (3) the 9 new CATALOG entries are present, and the retired «MoJ» abbreviation is expanded.
  (4) VALUE-INVARIANT — attach_en never mutates an `_ar`, never clobbers an engine `_en`, and the
      scope_to_dict builder + the frontend pick are UNTOUCHED (index.html has no new b143 marker).
  (5) engine version b143.
"""
import io, sys, importlib

ROOT = r"C:\Thammen\deploy v2"
HTML = io.open(ROOT + r"\index.html", encoding="utf-8").read()
ENG  = io.open(ROOT + r"\evaluate_unified.py", encoding="utf-8").read()
SCOPE_SRC = io.open(ROOT + r"\scope_of_service.py", encoding="utf-8").read()
EN_SRC = io.open(ROOT + r"\en_localize.py", encoding="utf-8").read()

sys.path.insert(0, ROOT)
en_localize = importlib.import_module("en_localize"); importlib.reload(en_localize)
scope_of_service = importlib.import_module("scope_of_service")
_norm, CATALOG, attach_en = en_localize._norm, en_localize.CATALOG, en_localize.attach_en

passed = failed = 0
def ck(name, cond):
    global passed, failed
    if cond: passed += 1; print("  PASS", name)
    else:    failed += 1; print("  FAIL", name)

print("Sprint 2.22.0b.143 — EN twins for the scope-of-service disclaimers/requires\n")

# ── (1) COVERAGE: every scope gets disclaimer_en + requires_en (drift guard) ──
print("[coverage — attach_en localizes every real scope]")
_seen = set(); _miss = []
for at, sc in scope_of_service._ASSET_SCOPE.items():
    if id(sc) in _seen:
        continue
    _seen.add(id(sc))
    d = scope_of_service.scope_to_dict(sc)   # the REAL response builder
    attach_en(d)                             # the REAL post-pass
    if not d.get('disclaimer_en'):
        _miss.append((at, 'disclaimer_en'))
    if sc.requires_user_input_ar and not d.get('requires_user_input_en'):
        _miss.append((at, 'requires_user_input_en'))
ck("all distinct scopes checked (>=10)", len(_seen) >= 10)
ck("every scope gets disclaimer_en (no leak)", not [m for m in _miss if m[1] == 'disclaimer_en'])
ck("every requires_user_input gets _en", not [m for m in _miss if m[1] == 'requires_user_input_en'])
# unknown fallback
_u = scope_of_service.classify_asset_scope('zzz_unrecognised')
_du = scope_of_service.scope_to_dict(_u); attach_en(_du)
ck("unknown-type fallback gets disclaimer_en", bool(_du.get('disclaimer_en')))

# ── (2) the villa disclaimer — the main valued-path leak ──────────────────────
print("\n[villa — the main valued-path leak]")
_v = scope_of_service.scope_to_dict(scope_of_service._ASSET_SCOPE['standalone_villa'])
attach_en(_v)
_ven = _v.get('disclaimer_en') or ''
ck("villa disclaimer_en present", bool(_ven))
ck("villa disclaimer_en is English (standalone villas)", 'standalone villas' in _ven)
ck("villa disclaimer_en uses the 24-month window phrasing", '24 months' in _ven)
ck("villa disclaimer_en — termbase Ministry of Justice", 'Ministry of Justice' in _ven and 'MoJ' not in _ven)

# ── (3) the 9 new CATALOG entries present + termbase ─────────────────────────
print("\n[9 new CATALOG entries + termbase]")
_new_ar = [
    scope_of_service._ASSET_SCOPE['standalone_villa'].disclaimer_ar,
    scope_of_service._ASSET_SCOPE['compound_small'].disclaimer_ar,
    scope_of_service._ASSET_SCOPE['tower'].disclaimer_ar,
    scope_of_service._ASSET_SCOPE['tower'].requires_user_input_ar,
    scope_of_service._ASSET_SCOPE['palace'].disclaimer_ar,
    scope_of_service._ASSET_SCOPE['palace'].requires_user_input_ar,
    scope_of_service._ASSET_SCOPE['commercial'].disclaimer_ar,
    scope_of_service._ASSET_SCOPE['industrial'].disclaimer_ar,
    scope_of_service._ASSET_SCOPE['agricultural'].disclaimer_ar,
]
ck("all 9 new scope strings resolve in CATALOG", all(CATALOG.get(_norm(s)) is not None for s in _new_ar))
ck("tower requires_en correct", CATALOG.get(_norm(scope_of_service._ASSET_SCOPE['tower'].requires_user_input_ar)) == "The tower's gross annual rent")
# the retired «MoJ» abbreviation is expanded in the new EN (palace)
_pal_en = CATALOG.get(_norm(scope_of_service._ASSET_SCOPE['palace'].disclaimer_ar)) or ''
ck("palace disclaimer_en expands MoJ → Ministry of Justice", 'Ministry of Justice' in _pal_en and 'MoJ' not in _pal_en)
ck("commercial disclaimer_en keeps «Thammen's scope»", "Thammen's scope" in (CATALOG.get(_norm(scope_of_service._ASSET_SCOPE['commercial'].disclaimer_ar)) or ''))

# ── (4) VALUE-INVARIANT — additive only, builder + frontend UNTOUCHED ─────────
print("\n[value-invariant — additive only, no code touch]")
_d = scope_of_service.scope_to_dict(scope_of_service._ASSET_SCOPE['standalone_villa'])
_before = dict(_d)
attach_en(_d)
ck("disclaimer_ar NOT mutated", _d['disclaimer_ar'] == _before['disclaimer_ar'])
ck("methodology_ar NOT mutated", _d.get('methodology_ar') == _before.get('methodology_ar'))
# attach_en never clobbers an engine-authored _en
_probe = {'x_ar': 'أرض فضاء', 'x_en': 'ENGINE-SET'}
attach_en(_probe)
ck("attach_en never clobbers an engine _en", _probe['x_en'] == 'ENGINE-SET')
# scope_to_dict is unchanged (still emits methodology_en, no new engine key)
ck("scope_to_dict unchanged — no disclaimer_en added in the builder", "'disclaimer_en'" not in SCOPE_SRC)
# frontend untouched — the b140 pick reads still there, no b143 marker
ck("frontend pick(ss,'disclaimer') present (b140, untouched)", "pick(ss,'disclaimer')" in HTML)
ck("frontend pick(ss,'requires_user_input') present (b140, untouched)", "pick(ss,'requires_user_input')" in HTML.replace(" ", "") or "requires_user_input'):null" in HTML.replace(" ", "") or "pick(d.service_scope,'requires_user_input')" in HTML.replace(" ", ""))
ck("index.html has NO b143 marker (frontend untouched)", "b143" not in HTML and "b.143" not in HTML)

# ── (5) engine version ───────────────────────────────────────────────────────
print("\n[version]")
ck("ENGINE_VERSION format (b-series)", "thammen-sprint2p22p0b" in ENG)
ck("SPRINT_TAG format (2.22.0b)", "SPRINT_TAG = '2.22.0b." in ENG)

print(f"\n{'='*54}\n  {passed} passed, {failed} failed\n{'='*54}")
sys.exit(1 if failed else 0)
