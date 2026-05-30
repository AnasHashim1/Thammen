#!/usr/bin/env python3
"""
test_sprint_2p22p0a8_rics_citation.py — Sprint 2.22.0a.8 (RICS / IVS 2025 citation correctness)

Single-purpose sprint: correct ALL RICS/IVS citation labels to the 2025 edition
(effective 31 January 2025) and ADD the AVM models standard (VPS 5 / IVS 105),
which governs automated valuation models and was previously absent.

Verifies (source-level on the LIVE production files + one runtime exercise):
  [1] Models standard added — VPS 5 / IVS 105 on the new secondary methodology
      surface (rics_methodology_note_ar/en) + the IVS 105 AVM-not-standalone
      disclosure.
  [2] No stale "VPS 4" citation remains in any live production file.
  [3] Remap targets — approaches → VPS 3 / IVS 103; HBU → VPS 2 / IVS 102;
      scope of service → VPS 1.
  [4] Edition label — "effective 31 January 2025" (no bare "...Global Standards 2024").
  [5] LRM-wrapping (U+200E) of Latin standard codes in Arabic user-facing copy.
  [6] The 2.22.0a.4 universal bare methodology_ar line is untouched.
  [7] Runtime production exercise (Rule #40 / E14) — _build_unified_output really
      returns the note fields, and methodology_ar is still the bare line.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a8_rics_citation.py
"""
import os
import sys
import types

ROOT = os.path.dirname(os.path.abspath(__file__))


def _src(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


_passed = 0
_failed = 0


def check(name, cond, detail=''):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  ✓ {name}")
    else:
        _failed += 1
        print(f"  ✗ {name}   {detail}")


LRM = '‎'

EU = _src('evaluate_unified.py')
SCOPE = _src('scope_of_service.py')
GEOM = _src('geometric_factors.py')
CMP = _src('comparable_adjustments.py')
HYB = _src('hybrid_valuation.py')
V3 = _src('evaluate_v3.py')
HTML = _src('index.html')
PF = _src('connectors', 'propertyfinder_apartments_t2_sales.py')

BARE_LINE = 'أساس التقدير هو منهج المقارنة بالمبيعات.'

print("Sprint 2.22.0a.8 — RICS / IVS 2025 citation correctness\n")

# [1] Models standard added on the secondary surface
print("[1] Models standard VPS 5 / IVS 105 added (was absent)")
check("rics_methodology_note_ar field present", 'rics_methodology_note_ar' in EU)
check("rics_methodology_note_en field present", 'rics_methodology_note_en' in EU)
check("note cites VPS 5", 'VPS 5' in EU)
check("note cites IVS 105", 'IVS 105' in EU)
check("AVM-not-standalone disclosure (ar)",
      ('النموذج الآلي' in EU and 'مُقيِّم مُرخّص' in EU and 'المرحلة الخامسة' in EU))
check("AVM-not-standalone disclosure (en)",
      'does not by itself produce a final' in EU and 'licensed valuer' in EU)
check("frontend renders the note on a collapsible surface",
      'rics_methodology_note_ar' in HTML and '<details' in HTML)

# [2] No stale VPS 4 in any live production file
print("\n[2] No stale 'VPS 4' in live production files")
for nm, s in [('evaluate_unified.py', EU), ('scope_of_service.py', SCOPE),
              ('geometric_factors.py', GEOM), ('comparable_adjustments.py', CMP),
              ('hybrid_valuation.py', HYB), ('evaluate_v3.py', V3),
              ('index.html', HTML), ('propertyfinder_apartments_t2_sales.py', PF)]:
    check(f"no 'VPS 4' in {nm}", 'VPS 4' not in s, "still present")

# [3] Remap targets
print("\n[3] Remap targets (approach VPS 3 / HBU VPS 2 / scope VPS 1)")
check("approach labels → VPS 3 / IVS 103", 'RICS VPS 3 / IVS 103' in EU)
check("HBU rics_reference → VPS 2 / IVS 102",
      'RICS VPS 2 / IVS 102 — Highest and Best Use' in EU)
check("HBU evidence (geometric_factors) → VPS 2 / IVS 102", 'VPS 2 / IVS 102' in GEOM)
check("HBU render (index.html) → VPS 2 / IVS 102", 'RICS VPS 2 / IVS 102' in HTML)
check("scope declaration → VPS 1 (no 'VPS 2 requires')",
      'VPS 1' in SCOPE and 'VPS 2 requires' not in SCOPE)
check("index.html scope link comment → VPS 1", 'RICS VPS 1 Scope link' in HTML)
check("service-level copy → VPS 3 (no VPS 4)", 'RICS VPS 3' in SCOPE and 'VPS 4' not in SCOPE)
check("comparable_adjustments → VPS 3", 'VPS 3' in CMP and 'VPS 4' not in CMP)
check("hybrid like-for-like → VPS 3", 'RICS VPS 3' in HYB)
check("connector like-for-like → VPS 3", 'RICS VPS 3' in PF and 'VPS 4' not in PF)
check("MUC comment typo 'VPN 13' fixed → VPGA 10", 'VPN 13' not in EU and 'VPGA 10' in EU)

# [4] Edition label
print("\n[4] Edition label = effective 31 January 2025")
check("'effective 31 January 2025' present", 'effective 31 January 2025' in EU)
check("no bare '...Global Standards 2024'", 'Global Standards 2024' not in EU)

# [5] LRM-wrapping of Latin standard codes in Arabic copy
print("\n[5] LRM-wrapping (U+200E) for bidi safety")
check("note LRM-wraps VPS 5", (LRM + 'VPS 5' + LRM) in EU)
check("note LRM-wraps IVS 105", (LRM + 'IVS 105' + LRM) in EU)
check("method label LRM-wrapped", (LRM + 'RICS VPS 3 / IVS 103' + LRM) in EU)
check("geometric HBU evidence LRM-wrapped", (LRM + 'RICS HBU — VPS 2 / IVS 102' + LRM) in GEOM)
check("index.html summary LRM (&lrm;) around Latin", '&lrm;RICS / IVS&lrm;' in HTML)

# [6] 2.22.0a.4 bare line untouched
print("\n[6] 2.22.0a.4 bare methodology_ar line untouched")
check("bare line present verbatim", ("'methodology_ar': '" + BARE_LINE + "'") in EU)
check("bare line carries no Latin standard code", (LRM not in BARE_LINE and 'VPS' not in BARE_LINE))

# [7] Runtime production exercise (Rule #40 / E14)
print("\n[7] Runtime production exercise")
try:
    import evaluate_unified as eu
    check("ENGINE_VERSION bumped",
          eu.ENGINE_VERSION == 'thammen-sprint2p22p0a8-rics-citation-2025',
          f"got {eu.ENGINE_VERSION!r}")
    check("SPRINT_TAG bumped", eu.SPRINT_TAG == '2.22.0a.8', f"got {eu.SPRINT_TAG!r}")
    # Minimal ev: valuation=None makes the `if ev.valuation` guards skip the
    # valuation block, so the real _build_unified_output runs to completion and
    # returns the actual base dict (incl. the new note) — a genuine production
    # exercise, not a re-implementation (Rule #40 / E14).
    ev = types.SimpleNamespace(
        address=None, valuation_date=None, gis_district_aname=None,
        plot_area_m2=None, asset_type='standalone_villa', valuation=None,
        raw_property_report=None, multi_qars=None)
    out = eu._build_unified_output(ev, None, {}, {}, {}, {}, {}, {}, {},
                                   'investor', {}, None)
    note = out.get('rics_methodology_note_ar', '')
    check("runtime output carries rics_methodology_note_ar", bool(note))
    check("runtime note has VPS 5 + IVS 105", 'VPS 5' in note and 'IVS 105' in note)
    check("runtime note has AVM disclosure", 'مُقيِّم مُرخّص' in note)
    check("runtime note is LRM-wrapped", LRM in note)
    check("runtime methodology_ar is still the bare line",
          out.get('methodology_ar') == BARE_LINE, f"got {out.get('methodology_ar')!r}")
    check("runtime English note present", bool(out.get('rics_methodology_note_en')))
except Exception as e:  # pragma: no cover - surfaces an unexpected integration break
    check("runtime _build_unified_output exercised", False, f"raised {type(e).__name__}: {e}")

print(f"\n{'=' * 52}")
print(f"  Sprint 2.22.0a.8 citation tests — PASSED {_passed} / FAILED {_failed}")
sys.exit(1 if _failed else 0)
