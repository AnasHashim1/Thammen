# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.151 — «درجة الثقة على مسار الرجوع» (fallback-path evidence tier).

Two defects, one path (the b149/b150 size-bracket fallback):
  (1) FACTUAL — accuracy.explanation_ar claimed the comparables are close «في النوع
      والمساحة» while the same payload's source_ar said «لا صفقات مسجَّلة في شريحة
      مساحته». The explanation IS rendered (hero meter + evidence panel); source_ar
      is not. Corrected for EVERY fallback, capped or not.
  (2) TIER — «شواهد كافية» (85) on an out-of-bracket subject. Capped per the MEASURED
      basis error (PO-signed «ج مُصحَّحة»): kept only for 400-600 / 600-900.

E14/#40: exercises the PRODUCTION `_evidence_capped` + the real `apply_moj_strategy`
over the real MoJ CSV — not a replica.
"""
import io, sys, csv, re, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import evaluate_unified as EU
import evaluate_property as EP
import moj_reference as MR

P, F = 0, 0
def ck(cond, label):
    global P, F
    if cond: P += 1; print('  PASS', label)
    else:    F += 1; print('  FAIL', label)

SRC = io.open('evaluate_unified.py', encoding='utf-8').read()
HTML = io.open('index.html', encoding='utf-8').read()
# Adjacent f-string literals are wrapped across lines in the source; join them so a
# phrase check tests the AUTHORED SENTENCE, not the source's line breaks.
FLAT = re.sub(r"'\s*\n\s*f'", "", SRC)

# ── A. the measured-tight bracket set ─────────────────────────────────────────
print('\nA. tight-bracket constant (derived from the GATE2_b150 §B back-test)')
ck(EU._FALLBACK_TIGHT_BRACKETS == ('400-600', '600-900'),
   'A1 exactly the two brackets whose measured error sits below the 0.135/0.188 cliff')
ck('0-400' not in EU._FALLBACK_TIGHT_BRACKETS,
   'A2 0-400 is NOT tight (0.272) — the handoff\'s «small only» framing was inverted')
ck('1500-99999' not in EU._FALLBACK_TIGHT_BRACKETS,
   'A3 1500+ is NOT tight (land 0.448 / villa 0.869) — the worst-served class is capped')

# ── B. the PRODUCTION predicate, full matrix ──────────────────────────────────
print('\nB. _evidence_capped — production predicate')
ck(EU._evidence_capped({'bracket_fallback': False, 'size_bracket': '0-400'}) is False,
   'B1 populated bracket never caps (untouched path)')
ck(EU._evidence_capped({'bracket_fallback': False, 'size_bracket': '1500-99999'}) is False,
   'B2 populated bracket never caps even in a wide bracket')
ck(EU._evidence_capped({'bracket_fallback': True, 'size_bracket': '400-600'}) is False,
   'B3 fallback + 400-600 KEEPS the tier (measured 0.073/0.104)')
ck(EU._evidence_capped({'bracket_fallback': True, 'size_bracket': '600-900'}) is False,
   'B4 fallback + 600-900 KEEPS the tier (measured 0.106/0.135)')
ck(EU._evidence_capped({'bracket_fallback': True, 'size_bracket': '0-400'}) is True,
   'B5 fallback + 0-400 CAPS (0.272)')
ck(EU._evidence_capped({'bracket_fallback': True, 'size_bracket': '900-1500'}) is True,
   'B6 fallback + 900-1500 CAPS (0.188/0.347)')
ck(EU._evidence_capped({'bracket_fallback': True, 'size_bracket': '1500-99999'}) is True,
   'B7 fallback + 1500+ CAPS (0.448/0.869) — incl. the live 70312306 anchor')
ck(EU._evidence_capped({'bracket_fallback': True, 'size_bracket': None}) is True,
   'B8 fail-safe: unknown bracket on a fallback CAPS (never claim unmeasured tightness)')
ck(EU._evidence_capped(None) is False and EU._evidence_capped('x') is False,
   'B9 non-dict input is safe (no raise, no cap)')
ck(EU._evidence_capped({}) is False,
   'B10 an empty primary (no fallback key) does not cap')

# ── C. the FALSE claim is gone from the fallback path ─────────────────────────
print('\nC. the rendered explanation — factual correction')
ck('لا صفقات مسجَّلة في شريحة مساحة عقارك' in SRC,
   'C1 the honest basis sentence is authored')
ck('فطُبِّق وسيط سعر المتر في المنطقة على مساحته' in FLAT,
   'C2 it states what WAS applied (area ppm² × the subject area)')
ck('_fb_ar if _bfb else' in SRC,
   'C3 the «قريبة في النوع والمساحة» claim is gated on NOT-fallback')
ck("no registered transactions in your property\\'s size bracket" in FLAT
   or "no registered transactions in your property's size bracket" in FLAT.replace("\\'", "'"),
   'C4 EN twin carries the same disclosure (EN is live since b88)')
# the old claim must still exist for the untouched populated-bracket path
ck('قريبة في النوع والمساحة' in SRC,
   'C5 the original sentence is PRESERVED for the populated-bracket path (byte-identical)')

# ── D. the tier cap is wired ahead of the 85 branch ───────────────────────────
print('\nD. accuracy-block wiring')
i_cap = SRC.find("and n >= 20 and _cap:")
i_85  = SRC.find("'score': 85,")
ck(i_cap != -1, 'D1 the capped branch exists')
ck(i_cap != -1 and i_85 != -1 and i_cap < i_85,
   'D2 the capped branch is evaluated BEFORE the score-85 branch')
ck("'label': 'شواهد محدودة'" in SRC and "'tier': 'medium'" in SRC,
   'D3 the cap reuses the EXISTING tier taxonomy (no new tier invented)')
ck("_cap = _evidence_capped(primary)" in SRC,
   'D4 the block calls the production predicate (single source of truth)')

# ── E. broadcast (one engine decision, no JS re-derivation) ───────────────────
print('\nE. broadcast + frontend consumption')
ck("'bracket_fallback': bool(primary.get('bracket_fallback'))" in SRC,
   'E1 valuation.bracket_fallback broadcast')
ck("'evidence_capped':  _evidence_capped(primary)" in SRC,
   'E2 valuation.evidence_capped broadcast (the tier decision itself)')
ck("'bracket_fallback': _bfb," in SRC,
   'E3 Case 1 threads the flag onto primary')
ck("'size_bracket': (getattr(ev.valuation, 'size_bracket', None)" in SRC,
   'E4 Case 1 threads the SUBJECT size bracket onto primary')
ck("meth==='comparison_bracket'&&!v.evidence_capped" in HTML,
   'E5 index.html evidence axis-2 reads the broadcast decision')
ck("n&&n>=20&&meth==='comparison_bracket'){c2=S;}" not in HTML,
   'E6 the old ungated axis-2 rule is gone (no duplicated rule to drift)')

# ── F. value invariance ───────────────────────────────────────────────────────
print('\nF. value invariance (b151 is display/tier only)')
b151 = SRC[SRC.find('Sprint 2.22.0b.151: the size-bracket FALLBACK path'):][:3000]
ck("output['valuation']['amount']" not in b151 and "'amount':" not in b151,
   'F1 the b151 accuracy block assigns no amount')
for k in ("primary['value']", "['low']", "['high']"):
    ck(f"{k} =" not in b151, f'F2 no assignment to {k}')
ck('_evidence_capped' in SRC and 'def _evidence_capped(primary):' in SRC,
   'F3 the predicate is pure (takes primary, returns bool)')

# ── G. REAL DATA: the fallback flag + subject bracket on the production path ──
print('\nG. real MoJ data through the production apply_moj_strategy')
rows = list(csv.DictReader(io.open('moj_weekly.csv', encoding='utf-8-sig')))
ref = datetime.datetime(2025, 12, 31)
rf = MR.build_reference(rows, 'سميسمة', ref)
v_fb = EP.apply_moj_strategy('raw_land', 1500.0, rf)      # the live 70312306 shape
ck(v_fb.bracket_fallback is True, 'G1 سميسمة/1500 m² land IS a fallback (live-matching)')
ck(v_fb.size_bracket == '1500-99999',
   'G2 size_bracket is the SUBJECT bracket even when empty')
ck(EU._evidence_capped({'bracket_fallback': v_fb.bracket_fallback,
                        'size_bracket': v_fb.size_bracket}) is True,
   'G3 → the live anchor is CAPPED (was «شواهد كافية» score 85)')
ck((v_fb.bracket_n or 0) >= 20,
   'G4 …and it did reach n>=20, which is exactly why the badge over-claimed')

# a populated-bracket control: must NOT cap, must NOT change
v_ok = EP.apply_moj_strategy('raw_land', 500.0, rf)
ck(v_ok.bracket_fallback is False, 'G5 populated-bracket control is not a fallback')
ck(EU._evidence_capped({'bracket_fallback': v_ok.bracket_fallback,
                        'size_bracket': v_ok.size_bracket}) is False,
   'G6 → control keeps its tier (no collateral downgrade)')

# a TIGHT-bracket fallback control: fallback, but kept
# The KEEP side of the signed rule must be proven on REAL data, not asserted vacuously:
# find a pool that IS a fallback in a TIGHT bracket and confirm it is NOT capped.
_PROBE = [('villa', 'standalone_villa', '400-600', 500.0), ('villa', 'standalone_villa', '600-900', 700.0),
          ('land',  'raw_land',        '400-600', 500.0), ('land',  'raw_land',        '600-900', 700.0)]
tight = None
for a in sorted({MR.area_match_key(r.get('اسم المنطقة', '')) for r in rows} - {''}):
    if tight: break
    r2 = MR.build_reference(rows, a, ref)
    for cat, at, br, area_m2 in _PROBE:
        cd = (r2.get('categories') or {}).get(cat) or {}
        sb = cd.get('size_brackets') or {}
        if (cd.get('n') or 0) >= 20 and (sb.get(br) or {}).get('n', 0) == 0:
            tight = (a, cat, br, EP.apply_moj_strategy(at, area_m2, r2)); break
ck(tight is not None,
   'G7 a real TIGHT-bracket fallback pool exists in the corpus (the keep side is reachable)')
if tight:
    a, cat, br, vt = tight
    ck(vt.bracket_fallback is True and vt.size_bracket == br,
       f'G8 {a}/{cat}/{br} IS a fallback in a tight bracket')
    ck(EU._evidence_capped({'bracket_fallback': vt.bracket_fallback,
                            'size_bracket': vt.size_bracket}) is False,
       f'G9 → and it KEEPS «شواهد كافية» (measured error <=0.135) — the cap is targeted, not blanket')
else:
    ck(False, 'G8 unreachable'); ck(False, 'G9 unreachable')

# ── H. version ────────────────────────────────────────────────────────────────
print('\nH. version')
ck(EU.ENGINE_VERSION.startswith('thammen-sprint2p22p0b'), 'H1 engine version format')
ck(EU.SPRINT_TAG.startswith('2.22.0b.'), 'H2 sprint tag format')

print(f'\n{"="*56}\n  b151: {P} passed, {F} failed\n{"="*56}')
sys.exit(1 if F else 0)
