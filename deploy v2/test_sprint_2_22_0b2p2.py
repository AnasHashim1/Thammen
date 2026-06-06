# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.2.2 — Evidence-quality diagnosis panel (frontend-only, DESIGN_2p2x §3).

Two layers (E14 / Rule #40):
  (A) STATIC structure — reads the REAL index.html and asserts the refactor invariants
      (panel functions present, binary badge removed, panel rendered, the four component
      labels, «explanation≠confidence» footer, the colour-coded "ما معنى ذلك؟" block gone),
      AND pins the governing JS expressions so the Python mapping-mirror below cannot
      silently drift from the shipped JS.
  (B) MAPPING LOGIC — a faithful Python mirror of _evidenceRatings(d) asserted against the
      four CC-recon live-case field-shapes + edges, plus the «explanation≠confidence» proof
      (explanatory fields move NO rating; a rating moves ONLY when its governing field does).

Live DOM/nav + value-invariance are covered by R14 Chromium + the live smoke. Backend is
UNCHANGED (version-string bump only).

Run:  set PYTHONIOENCODING=utf-8 & python test_sprint_2_22_0b2p2.py
"""
import os
import re
import sys

import evaluate_unified as EU

_fail = 0
_pass = 0


def check(name, cond):
    global _fail, _pass
    if cond:
        _pass += 1
        print(f"  PASS  {name}")
    else:
        _fail += 1
        print(f"  FAIL  {name}")


HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "index.html"), encoding="utf-8") as fh:
    HTML = fh.read()


# ── (B) faithful Python mirror of the shipped JS _evidenceRatings(d) ──
S, M, L, NA = 'قوي', 'متوسط', 'محدود', '—'


def ev(d):
    v = d.get('valuation', {}); g = v.get('geometry', {})
    ui = d.get('user_inputs', {}); fr = d.get('data_freshness', {})
    confirmed = (g.get('footprint_basis') == 'confirmed')
    n = v.get('n_transactions'); meth = v.get('method'); ft = (fr.get('tier') or '').lower()
    c1 = L
    if confirmed and ui.get('condition'): c1 = S
    elif confirmed: c1 = M
    c2 = L
    if n and n >= 20 and meth == 'comparison_bracket': c2 = S
    elif n and n >= 10: c2 = M
    c3 = L
    if ft and ft != 'stale':
        c3 = S if ('fresh' in ft or 'current' in ft) else M
    if d.get('asset_type') == 'raw_land': c4 = NA
    elif confirmed: c4 = M
    else: c4 = L
    return [c1, c2, c3, c4]


def case(method=None, n=None, basis='assumed', asset='standalone_villa', tier='stale', condition=None, **extra):
    d = {'asset_type': asset, 'data_freshness': {'tier': tier},
         'valuation': {'method': method, 'n_transactions': n, 'geometry': {'footprint_basis': basis}},
         'user_inputs': ({'condition': condition} if condition else {})}
    d.update(extra)
    return d


print("=" * 64)
print("T1 — STATIC structure (the real index.html)")
check("panel deriver _evidenceRatings present", "function _evidenceRatings(d)" in HTML)
check("panel renderer evidencePanelHtml present", "function evidencePanelHtml(d,acc)" in HTML)
check("panel rendered in show()", "h+=evidencePanelHtml(d,acc);" in HTML)
check("binary confidence badge REMOVED (bc/bt gone)",
      "bc='rb" not in HTML and "bt=acc.label" not in HTML and 'class="rb \'+bc+\'"' not in HTML)
check("tier-coloured «ما معنى ذلك؟» RENDER block REMOVED (binary confidence visual gone)",
      "tierColor=acc.tier==='high'" not in HTML and "<strong>ما معنى ذلك؟</strong>" not in HTML)
check("the four component labels present",
      all(lbl in HTML for lbl in
          ['اكتمال بيانات العقار', 'جودة المقارنات', 'حداثة بيانات السوق', 'جودة توصيف المبنى']))
check("«explanation≠confidence» footer note present",
      "لا بالشرح" in HTML)
check("panel header is جودة الأدلّة (not a confidence %)", "جودة الأدلّة" in HTML)

print("=" * 64)
print("T2 — JS governing-expression pins (bind the mirror to the shipped JS)")
check("c2: n>=20 & comparison_bracket -> قوي", "n>=20&&meth==='comparison_bracket'" in HTML)
check("c2: n>=10 -> متوسط", "else if(n&&n>=10)" in HTML)
check("c3: stale guard", "ft!=='stale'" in HTML)
check("c4: raw_land -> N/A", "d.asset_type==='raw_land'" in HTML)
check("confirmed = footprint_basis confirmed", "g.footprint_basis==='confirmed'" in HTML)
check("c1 bonus reads ui.condition", "ui.condition" in HTML)

print("=" * 64)
print("T3 — MAPPING against the 4 CC-recon live cases (bare evals, MoJ stale)")
check("bare-villa bracket n37 -> [محدود,قوي,محدود,محدود]",
      ev(case('comparison_bracket', 37)) == [L, S, L, L])
check("thin-villa n15 -> [محدود,متوسط,محدود,محدود]",
      ev(case('comparison_thin', 15)) == [L, M, L, L])
check("raw-land bracket n73 -> [محدود,قوي,محدود,N/A]",
      ev(case('comparison_bracket', 73, asset='raw_land')) == [L, S, L, NA])
check("bracket n=18 (10-19) -> comparables متوسط",
      ev(case('comparison_bracket', 18))[1] == M)
check("n<10 -> comparables محدود",
      ev(case('comparison_bracket', 7))[1] == L and ev(case(None, None))[1] == L)

print("=" * 64)
print("T4 — refine improves ONLY the user-input axes (the «explanation≠confidence» core)")
refined = case('comparison_bracket', 37, basis='confirmed', condition='good')
check("refined (confirmed+condition) -> [قوي,قوي,محدود,متوسط]", ev(refined) == [S, S, L, M])
check("confirmed geometry, NO condition -> completeness متوسط",
      ev(case('comparison_bracket', 37, basis='confirmed'))[0] == M)
check("characterization caps at متوسط (condition never verified -> never قوي)",
      ev(refined)[3] == M and ev(case('comparison_bracket', 37, basis='confirmed', condition='good'))[3] != S)

print("=" * 64)
print("T5 — explanation≠confidence: explanatory fields move NO rating; freshness governs recency")
base = case('comparison_bracket', 37)
withexpl = case('comparison_bracket', 37,
                value_floor={'land_floor': 1}, geometric_factors={'hbu': 1}, trend={'slope': 5},
                reasoning_trace={'x': 1})
check("adding decomposition/GIS/trend leaves all 4 ratings unchanged", ev(base) == ev(withexpl))
check("recency rises ONLY when MoJ freshness improves (stale->fresh => قوي)",
      ev(case('comparison_bracket', 37, tier='stale'))[2] == L
      and ev(case('comparison_bracket', 37, tier='fresh'))[2] == S)

print("=" * 64)
print("T6 — version format (R6; backend untouched)")
check("ENGINE_VERSION dotted-sprint format",
      re.match(r'^thammen-sprint\d+p\d+p\d+', EU.ENGINE_VERSION) is not None)
check("SPRINT_TAG dotted-numeric prefix",
      re.match(r'^\d+\.\d+\.\d+', EU.SPRINT_TAG) is not None)

print("=" * 64)
print(f"RESULT: {_pass} passed, {_fail} failed")
sys.exit(1 if _fail else 0)
