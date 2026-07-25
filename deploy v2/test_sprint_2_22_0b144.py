# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.144 — «إنجليزيّة الأدلّة الهندسيّة» (EN twins for the corner/HBU geometric evidence).

Isolated E14 test — exercises the REAL geometric_factors functions (GIS stubbed) + reads the real
evaluate_unified geo_section passthrough + index.html.
Sprint B slice 3: the result-screen Geometric Findings card reads `pick(ca,'evidence')` /
`pick(hbu,'evidence')` since b140, but the engine emitted only `evidence_ar` — and these are
INTERPOLATED sentences (street numbers / zone codes) so the constant CATALOG cannot cover them →
engine-emit `evidence_en` beside `evidence_ar` (detect_corner + analyze_adjacent_zoning) + the
`geo_section` passthrough copies (`evaluate_unified.py` rebuilds the corner/hbu dicts and previously
copied only `evidence_ar`). VALUE-NEUTRAL — display strings only; potential_pct / is_corner / the
range-expansion inputs untouched; `_ar` untouched; frontend UNTOUCHED.

  (1) REAL detect_corner (GIS stubbed empty) → the no-street branch emits BOTH evidence_ar + evidence_en.
  (2) REAL analyze_adjacent_zoning (GIS stubbed with fixture zoning) → mixed-use / commercial /
      higher-density / industrial branches each emit an English evidence_en with the SAME interpolations.
  (3) STRUCTURAL — every rendered corner `evidence =` assignment has a paired `evidence_en =`;
      the corner return carries `'evidence_en'`; the geo_section copies BOTH passthroughs.
  (4) VALUE-NEUTRAL — `_ar` byte-identical to the pre-b144 wording; numeric keys unchanged;
      frontend untouched (pick already there, b140); no b144 marker in index.html.
  (5) engine version format (no exact pin — Lesson-2).
"""
import io, sys, importlib

ROOT = r"C:\Thammen\deploy v2"
HTML = io.open(ROOT + r"\index.html", encoding="utf-8").read()
ENG  = io.open(ROOT + r"\evaluate_unified.py", encoding="utf-8").read()
GEO_SRC = io.open(ROOT + r"\geometric_factors.py", encoding="utf-8").read()

sys.path.insert(0, ROOT)
gf = importlib.import_module("geometric_factors")

passed = failed = 0
def ck(name, cond):
    global passed, failed
    if cond: passed += 1; print("  PASS", name)
    else:    failed += 1; print("  FAIL", name)

print("Sprint 2.22.0b.144 — EN twins for the corner/HBU geometric evidence\n")

# ── (1) REAL detect_corner — GIS stubbed empty → the no-street branch ────────
print("[detect_corner — real function, GIS stubbed]")
_orig_http = gf._http_get_json
try:
    gf._http_get_json = lambda *a, **k: {}
    rect = {'rings': [[[0.0, 0.0], [30.0, 0.0], [30.0, 20.0], [0.0, 20.0], [0.0, 0.0]]]}
    res = gf.detect_corner(rect)
finally:
    gf._http_get_json = _orig_http
ck("corner returns evidence_ar (AR intact)", res.get('evidence_ar') == 'لم يُكتشف شارع مجاور — قطعة داخلية محتملة')
ck("corner returns evidence_en (the EN twin)", res.get('evidence_en') == 'No adjacent street detected — possibly an interior plot')
ck("corner numeric/flag keys unchanged", ('is_corner' in res) and ('main_road_adjacent' in res) and ('confidence' in res))

# ── (2) REAL analyze_adjacent_zoning — fixture zoning per branch ─────────────
print("\n[analyze_adjacent_zoning — real function, fixture zoning]")
def _zone_fixture(codes):
    return {'features': [{'attributes': {'ZONING': c, 'CODE': c}} for c in codes]}

def _run(codes, current='R1'):
    _o = gf._http_get_json
    try:
        gf._http_get_json = lambda *a, **k: _zone_fixture(codes)
        return gf.analyze_adjacent_zoning(25.3, 51.5, current)
    finally:
        gf._http_get_json = _o

# mixed-use branch
r_mu = _run(['R1', 'MU'])
ck("MU branch: hbu fires + evidence_en English", r_mu.get('hbu_potential') is True and 'adjacent mixed use (MU)' in (r_mu.get('evidence_en') or ''))
ck("MU branch: evidence_ar intact (إمكانية تعديل رخصة)", 'إمكانية تعديل رخصة' in (r_mu.get('evidence_ar') or ''))
ck("MU branch: +20% interpolated in BOTH", ('+20%' in r_mu['evidence_ar']) and ('+20%' in r_mu['evidence_en']))
ck("MU branch: RICS citation in EN", 'RICS HBU — VPS 2 / IVS 102' in r_mu['evidence_en'])
# commercial branch
r_c = _run(['R1', 'C2'])
ck("commercial branch: evidence_en carries the codes", 'adjacent commercial (C2)' in (r_c.get('evidence_en') or '') and '+25%' in r_c['evidence_en'])
# higher-density branch
r_hd = _run(['R1', 'R3'])
ck("higher-density branch: evidence_en", 'adjacent higher-density zoning' in (r_hd.get('evidence_en') or '') and '+10%' in r_hd['evidence_en'])
# industrial branch (negative — industrial_adjacency renders)
r_ind = _run(['R1', 'IND'])
ck("industrial branch: evidence_en negative wording", r_ind.get('industrial_adjacency') is True and 'Adjacent industrial zoning (IND)' in (r_ind.get('evidence_en') or '') and 'may reduce the value' in r_ind['evidence_en'])
ck("industrial branch: evidence_ar intact", 'تصنيف صناعي مجاور' in (r_ind.get('evidence_ar') or ''))
ck("industrial branch: potential_pct unchanged (-0.10)", r_ind.get('potential_pct') == -0.10)
# gated-out branches deliberately NOT localized (b139 dead-field discipline)
r_same = _run(['R1'])
ck("same-zoning branch (gated out of geo_section) has NO evidence_en", 'evidence_en' not in r_same)

# ── (3) STRUCTURAL — paired assignments + return + geo_section passthrough ───
print("\n[structural]")
ck("all 5 corner branches have paired evidence_en =", GEO_SRC.count("evidence_en = ") + GEO_SRC.count("evidence_en=") >= 5)
ck("corner return carries evidence_en", "'evidence_en': evidence_en" in GEO_SRC)
ck("geo_section corner passthrough", "'evidence_en': corner.get('evidence_en')" in ENG)
ck("geo_section hbu passthrough", "'evidence_en': hbu.get('evidence_en')" in ENG)

# ── (4) VALUE-NEUTRAL + frontend untouched ───────────────────────────────────
print("\n[value-neutral + frontend untouched]")
ck("AR corner strings byte-identical (all 5)", all(s in GEO_SRC for s in (
    "زاوية مع شارع رئيسي", "زاوية على شوارع داخلية متعددة", "مطل على شارع رئيسي",
    "مطل على شارع داخلي", "لم يُكتشف شارع مجاور — قطعة داخلية محتملة")))
ck("AR hbu strings byte-identical", ("إمكانية تعديل رخصة" in GEO_SRC) and ("تصنيف صناعي مجاور" in GEO_SRC))
ck("frontend pick(ca,'evidence') present (b140, untouched)", "pick(ca,'evidence')" in HTML)
ck("frontend pick(hbu,'evidence') present (b140, untouched)", "pick(hbu,'evidence')" in HTML)
ck("index.html has NO b144 marker (frontend untouched)", "b144" not in HTML)

# ── (5) version ──────────────────────────────────────────────────────────────
print("\n[version]")
ck("ENGINE_VERSION format (b-series)", "thammen-sprint2p22p0b" in ENG)
ck("SPRINT_TAG format (2.22.0b)", "SPRINT_TAG = '2.22.0b." in ENG)

print(f"\n{'='*54}\n  {passed} passed, {failed} failed\n{'='*54}")
sys.exit(1 if failed else 0)
