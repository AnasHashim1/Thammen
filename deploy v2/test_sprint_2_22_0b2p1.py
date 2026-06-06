# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.2.1 — Separate input screens (structural, frontend-only).

Isolated tests that exercise the REAL shipped artifact (index.html) — they read
the actual file and assert the refactor's structural invariants (E14 / Rule #40:
verify the production artifact, do not echo an assumption). The LIVE DOM/nav
behaviour is covered by the R14 real-Chromium pass; the value-invariance is
covered by the live-engine smoke. This file pins the structure so a later edit
cannot silently regress the screen split.

Backend is UNCHANGED this sprint (version-string bump only); the engine-side
contract (effective_footprint_m2 + the F2 gate + version format) stays asserted
by test_sprint_2_22_0b2.py.

Run:  set PYTHONIOENCODING=utf-8 & python test_sprint_2_22_0b2p1.py
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

# Region boundaries (screens render in this DOM order: home < form < refine < results).
i_form = HTML.find('id="formScreen"')
i_refine = HTML.find('id="refineScreen"')
i_results = HTML.find('id="resultsScreen"')
form_region = HTML[i_form:i_refine] if (i_form >= 0 and i_refine > i_form) else ""
refine_region = HTML[i_refine:i_results] if (i_refine >= 0 and i_results > i_refine) else ""

# Optional property-detail input ids that must MOVE from the form to #refineScreen.
DETAIL_IDS = [
    'floors', 'basement', 'annexes', 'externalMajlis', 'condition', 'footprintM2',
    'buildingAge', 'isLuxury', 'askingPrice', 'rentalIncome', 'potentialRental',
    'unitCount', 'avgRentPerUnit',
]

print("=" * 64)
print("T1 — #refineScreen exists as a 4th .screen reached by go('refine')")
check("refineScreen present", i_refine >= 0)
check("DOM order home<form<refine<results",
      0 <= i_form < i_refine < i_results)
check("go(n) screen-switcher targets {n}Screen (so go('refine')->#refineScreen)",
      "function go(n)" in HTML and "n+'Screen'" in HTML)
check("refine has its own submit button -> thammenReEvalGeometry()",
      'id="refineBtn"' in refine_region and 'thammenReEvalGeometry()' in refine_region)

print("=" * 64)
print("T2 — optional details RELOCATED off the form, onto #refineScreen")
check("every detail input lives in the refine region",
      all(('id="%s"' % i) in refine_region for i in DETAIL_IDS))
check("no detail input remains in the form region",
      not any(('id="%s"' % i) in form_region for i in DETAIL_IDS))
check("old collapsible dSec block removed (no id=\"dSec\")", 'id="dSec"' not in HTML)
check("each relocated input id appears exactly once (no duplication)",
      all(HTML.count('id="%s"' % i) == 1 for i in DETAIL_IDS))

print("=" * 64)
print("T3 — run() is identification-only -> bare /api/evaluate")
check("run() remembers the bare endpoint",
      "window._lastSubmit={endpoint:'/api/evaluate', body:" in HTML)
check("run() POSTs the bare /api/evaluate (not /details)",
      "fetch(API+'/api/evaluate',{method:'POST'" in HTML)
check("run() no longer reads the details toggle (if(dOpen) gone)",
      "if(dOpen)" not in HTML)

print("=" * 64)
print("T4 — results card is DISPLAY-ONLY; button navigates to #refineScreen")
check("F2 gate preserved on the card (villa/house only)",
      "_b2IsBuilding(d.asset_type)" in HTML)
check("card button navigates to refine (go('refine'))", r"go(\'refine\')" in HTML)
check("old in-card inputs removed (b2Floors/b2Footprint/b2Basement)",
      'b2Floors' not in HTML and 'b2Footprint' not in HTML and 'b2Basement' not in HTML)
check("F3 effective-footprint disclosure retained on the card",
      'effective_footprint_m2' in HTML and 'footprint_basis' in HTML)
check("F4 basement copy retained (display)",
      'لا يُحرّك تقدير المقارنة' in HTML)

print("=" * 64)
print("T5 — refine submit reads the relocated inputs + POSTs /details")
# thammenReEvalGeometry now reads the relocated form ids and upgrades to /details.
g0 = HTML.find('async function thammenReEvalGeometry()')
g1 = HTML.find('\n}\n', g0)
gbody = HTML[g0:g1] if g0 >= 0 and g1 > g0 else ""
check("reads relocated footprint input (val('footprintM2'))", "val('footprintM2')" in gbody)
check("reads relocated floors input (val('floors'))", "val('floors')" in gbody)
check("submits to /api/evaluate/details", "/api/evaluate/details" in gbody)
check("navigates to results after refine (go('results'))", "go('results')" in gbody)

print("=" * 64)
print("T6 — tower path preserved + dead-code cleanup")
check("tower rent CTA goForm() now navigates to refine",
      "function goForm(focusId){" in HTML and "go('refine')" in HTML)
check("towerRentSection relocated onto refine",
      'id="towerRentSection"' in refine_region)
check("tog() removed (toggle gone)", "function tog(" not in HTML)
check("dOpen declaration removed", "let dOpen" not in HTML and "dOpen=!dOpen" not in HTML)

print("=" * 64)
print("T7 — version (R6 format check; backend untouched this sprint)")
check("ENGINE_VERSION dotted-sprint format",
      re.match(r'^thammen-sprint\d+p\d+p\d+', EU.ENGINE_VERSION) is not None)
check("SPRINT_TAG dotted-numeric prefix",
      re.match(r'^\d+\.\d+\.\d+', EU.SPRINT_TAG) is not None)

print("=" * 64)
print(f"RESULT: {_pass} passed, {_fail} failed")
sys.exit(1 if _fail else 0)
