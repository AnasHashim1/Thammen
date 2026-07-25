# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.145 — «إنجليزيّة عوامل وتوصيات التحفّظ» (EN twins for the MUC factors/recommendations arrays).

Isolated E14 test — exercises the REAL assess_uncertainty + the REAL attach_en + reads the real
evaluate_unified/index.html. Sprint B slice 4 (the LAST rendered result-screen EN leak): the brief
material_uncertainty section renders `c.factors` / `c.recommendations` raw — Arabic in EN mode.
Recon RESHAPED the anticipated dataclass-threading design (§20.140): the factors are MUTATED at
3 post-assembly engine sites (:4900 insert(0) · :7401 interpolated replace · :7616 append), so
parallel-list threading would be alignment-fragile — instead the en_localize ARRAY rule is extended
('factors'/'recommendations' keys + a _TEMPLATES regex table for the interpolated n=X shapes); the
api.py:262 attach_en post-pass sees the FINAL arrays → index-aligned `_en` twins that can never
drift. VALUE-NEUTRAL — additive `_en` only; `_ar` arrays untouched; amount/method/rule untouched;
the render decision still reads the AR array (`c.factors&&c.factors.length` guards unchanged).

  (1) COVERAGE (drift guard) — every factor/recommendation the REAL assess_uncertainty emits across
      a representative input matrix resolves via CATALOG-or-TEMPLATE; + the 3 evaluate_unified
      site literals (:4893 building-unknown · :7407 widening replacement · :7617 dispersion).
  (2) attach_en on a REAL UncertaintyLevel dict → index-aligned, fully-English factors_en +
      recommendations_en; interpolated n survives; `_ar` untouched.
  (3) the LIVE fixtures' factor arrays fully resolve (r1 villa cost-led).
  (4) the b142 arrays (known_unknowns/content) unaffected; unresolvable-only arrays don't fire;
      never clobbers an engine `_en`.
  (5) frontend: the 2 pickArr swaps; the render guards still read the AR array.
  (6) engine version format (no exact pin — Lesson-2).
"""
import io, sys, json, importlib

ROOT = r"C:\Thammen\deploy v2"
HTML = io.open(ROOT + r"\index.html", encoding="utf-8").read()
ENG  = io.open(ROOT + r"\evaluate_unified.py", encoding="utf-8").read()

sys.path.insert(0, ROOT)
en_localize = importlib.import_module("en_localize"); importlib.reload(en_localize)
mu_mod = importlib.import_module("material_uncertainty")
_norm, attach_en, _item_en = en_localize._norm, en_localize.attach_en, en_localize._item_en

passed = failed = 0
def ck(name, cond):
    global passed, failed
    if cond: passed += 1; print("  PASS", name)
    else:    failed += 1; print("  FAIL", name)

print("Sprint 2.22.0b.145 — EN twins for the MUC factors/recommendations arrays\n")

# ── (1) COVERAGE — the real assess_uncertainty across a representative matrix ─
print("[coverage — every emitted factor/recommendation resolves]")
all_factors, all_recs = set(), set()
matrix = []
for at in ('standalone_villa', 'apartment_building', 'raw_land'):
    for moj_n in (None, 3, 7, 15, 40):
        for rent_n in (None, 5):
            for svc in (None, 'estimated', 'reported'):
                matrix.append(dict(asset_type=at, moj_n=moj_n, rent_n=rent_n,
                                   service_charge_confidence=svc,
                                   has_field_inspection=False,
                                   building_condition_known=False,
                                   building_age_known=False, bua_known=False,
                                   trend_n_years=None))
for kw in matrix:
    u = mu_mod.assess_uncertainty(**kw)
    all_factors.update(u.factors); all_recs.update(u.recommendations)
_unres_f = [f for f in all_factors if _item_en(_norm(f)) is None]
_unres_r = [r for r in all_recs if _item_en(_norm(r)) is None]
ck(f"matrix ran ({len(matrix)} cases; {len(all_factors)} distinct factors)", len(all_factors) >= 8)
ck("every emitted FACTOR resolves (catalog or template)", not _unres_f)
ck("every emitted RECOMMENDATION resolves", not _unres_r)
if _unres_f: print("   unresolved factors:", _unres_f)
if _unres_r: print("   unresolved recs:", _unres_r)
# the 3 evaluate_unified site literals
_site1 = 'قد يؤدي إدخال التفاصيل الفعلية للعقار — كالحالة والمساحة الدقيقة والتشطيبات — إلى تعديل جوهري في التقدير.'
_site2 = 'الشريحة المباشرة ضعيفة (n=1) — تم التعويض بالتوسيع الجغرافي (n=42 معاملة بعد التوسيع، ‎RICS VPS 3 / IVS 103‎)'
_site3 = 'تشتت المقارنات مرتفع (نوع البناء والحالة غير مؤكدين) — اعتمد النطاق المعروض لا الرقم المفرد'
_site4 = 'أدنل'  # placeholder guard below uses the real rec
_rec_site = 'أدخل تفاصيل العقار (طوابق، سرداب، حالة) للحصول على تقييم أدق'
ck("site :4893 building-unknown factor resolves", _item_en(_norm(_site1)) is not None)
ck("site :7407 widening replacement resolves (template, n interpolated)",
   (_item_en(_norm(_site2)) or '').startswith('The direct bracket is weak (n=1)') and 'n=42' in (_item_en(_norm(_site2)) or ''))
ck("site :7617 dispersion factor resolves", _item_en(_norm(_site3)) is not None)
ck("site :4909 recommendation resolves", _item_en(_norm(_rec_site)) is not None)

# ── (2) attach_en on a REAL UncertaintyLevel → aligned English twins ─────────
print("\n[attach_en — real assess_uncertainty output]")
u = mu_mod.assess_uncertainty(asset_type='standalone_villa', moj_n=15, rent_n=None,
                              has_field_inspection=False, building_condition_known=False,
                              building_age_known=False, bua_known=False,
                              trend_n_years=None, service_charge_confidence='estimated')
mu = {'level': u.level, 'factors': list(u.factors), 'recommendations': list(u.recommendations)}
# simulate the :4900 insert(0) — attach_en runs AFTER it (api.py:262) → covered
mu['factors'].insert(0, _site1)
before_f, before_r = list(mu['factors']), list(mu['recommendations'])
attach_en(mu)
ck("factors_en emitted", 'factors_en' in mu)
ck("factors_en index-aligned", len(mu.get('factors_en') or []) == len(mu['factors']))
ck("factors_en fully English (no Arabic residue)",
   all(not any('؀' <= ch <= 'ۿ' for ch in f) for f in (mu.get('factors_en') or [])))
ck("interpolated n=15 survives into EN", any('(n=15)' in f for f in (mu.get('factors_en') or [])))
ck("recommendations_en emitted + aligned", len(mu.get('recommendations_en') or []) == len(mu['recommendations']))
ck("recommendations_en fully English",
   all(not any('؀' <= ch <= 'ۿ' for ch in r) for r in (mu.get('recommendations_en') or [])))
ck("factors _ar array NOT mutated", mu['factors'] == before_f)
ck("recommendations _ar array NOT mutated", mu['recommendations'] == before_r)

# ── (3) the LIVE fixture (r1 villa cost-led) fully resolves ──────────────────
print("\n[live fixture — r1 villa]")
try:
    _d = json.load(io.open(
        r'C:/Users/ans_h/AppData/Local/Temp/claude/C--Thammen-deploy-v2/10958cd2-1cda-4971-8ed4-ab3761017b3f/scratchpad/r1.json',
        encoding='utf-8'))
    _fx = (_d.get('material_uncertainty') or {}).get('factors') or []
    _un = [f for f in _fx if _item_en(_norm(f)) is None]
    ck(f"live r1 factors ({len(_fx)}) ALL resolve", bool(_fx) and not _un)
    if _un: print("   unresolved:", [x[:60] for x in _un])
except FileNotFoundError:
    print("  SKIP live fixture (not on this machine)")

# ── (4) b142 semantics preserved + safety ────────────────────────────────────
print("\n[b142 semantics + safety]")
p1 = {'known_unknowns': ['حالة العقار الداخلية الفعلية (تشطيبات، صيانة، تكييف)']}
attach_en(p1)
ck("b142 known_unknowns rule unaffected", (p1.get('known_unknowns_en') or [''])[0].startswith('The property'))
p2 = {'factors': ['نص غير مفهرس إطلاقاً 12345']}
attach_en(p2)
ck("all-unresolvable array does NOT fire", 'factors_en' not in p2)
p3 = {'factors': [_site3], 'factors_en': ['ENGINE-SET']}
attach_en(p3)
ck("never clobbers an engine factors_en", p3['factors_en'] == ['ENGINE-SET'])
p4 = {'factors': [_site3, 'غير مفهرس زائف']}
attach_en(p4)
ck("mixed array: unresolvable item falls back to Arabic (aligned)",
   p4.get('factors_en') and p4['factors_en'][1] == 'غير مفهرس زائف' and len(p4['factors_en']) == 2)

# ── (5) frontend swaps ───────────────────────────────────────────────────────
print("\n[frontend]")
ck("pickArr(c,'factors') swap present", "pickArr(c,'factors').forEach" in HTML)
ck("pickArr(c,'recommendations') swap present", "pickArr(c,'recommendations').forEach" in HTML)
ck("render guard still reads the AR array (decision unchanged)", "if(c.factors&&c.factors.length)" in HTML)
ck("raw c.factors.forEach GONE", "c.factors.forEach" not in HTML.replace("pickArr(c,'factors').forEach", ""))

# ── (6) version ──────────────────────────────────────────────────────────────
print("\n[version]")
ck("ENGINE_VERSION format (b-series)", "thammen-sprint2p22p0b" in ENG)
ck("SPRINT_TAG format (2.22.0b)", "SPRINT_TAG = '2.22.0b." in ENG)

print(f"\n{'='*54}\n  {passed} passed, {failed} failed\n{'='*54}")
sys.exit(1 if failed else 0)
