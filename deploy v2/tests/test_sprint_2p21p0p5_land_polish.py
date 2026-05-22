"""
tests/test_sprint_2p21p0p5_land_polish.py — Sprint 2.21.0.5 isolated tests.

Run: python tests/test_sprint_2p21p0p5_land_polish.py

Covers the 5 land-output-polish fixes (all conditional on asset_type; buildings
unaffected = regression-safe):
  1. scope_of_service: raw_land is 'supported' (was "نوع غير معروف")
  4. material_uncertainty: land excludes building/BUA/service-charge factors
  5. material_uncertainty: land known_unknowns swap building items for land items
  5b. output_briefs due_diligence: land questions (no tenant/building) for raw_land
Issues 2 (PIN address) + 3 (skip decomposition) live in the engine output path
and are verified post-deploy via the 5 land PINs (need live GIS).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scope_of_service as sos          # noqa: E402
import material_uncertainty as mu       # noqa: E402
import output_briefs as ob              # noqa: E402

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  ok  {name}")
    else:
        _failed += 1
        print(f"  XX  {name}")


# ---- Issue 1: scope ----

def test_scope_raw_land_supported():
    check("raw_land -> supported", sos.classify_asset_scope('raw_land').tier == 'supported')
    check("raw_land label is land (not 'unknown')",
          sos.classify_asset_scope('raw_land').label_ar == sos.classify_asset_scope('land').label_ar)
    check("land still supported", sos.classify_asset_scope('land').tier == 'supported')
    check("villa unchanged (supported)",
          sos.classify_asset_scope('standalone_villa').tier == 'supported')
    check("genuinely unknown still unsupported",
          sos.classify_asset_scope('spaceship').tier == 'unsupported')


# ---- Issues 4 + 5: material uncertainty ----

def test_muc_land_excludes_building():
    land = mu.assess_uncertainty(moj_n=73, asset_type='raw_land')
    # No BUA / service-charge factors for land
    check("land: no BUA factor",
          not any('المساحة المبنية' in f for f in land.factors))
    check("land: no service-charge factor",
          not any('رسوم الخدمات' in f for f in land.factors))
    # known_unknowns: building condition/age/BUA removed
    check("land: no building-condition unknown",
          not any('حالة المبنى' in u for u in land.known_unknowns))
    check("land: no exact-building-age unknown",
          not any(u == 'عمر البناء الدقيق' for u in land.known_unknowns))
    check("land: no BUA unknown",
          not any('المساحة المبنية الفعلية' in u for u in land.known_unknowns))
    # land-specific unknowns present
    check("land: has site-grading unknown",
          any('منسوب الأرض' in u for u in land.known_unknowns))
    check("land: has zoning/height unknown",
          any('ارتفاع البناء المسموح' in u for u in land.known_unknowns))


def test_muc_building_regression():
    villa = mu.assess_uncertainty(moj_n=46, asset_type='standalone_villa')
    check("villa: keeps BUA factor",
          any('المساحة المبنية' in f for f in villa.factors))
    check("villa: keeps building-condition unknown",
          any('حالة المبنى' in u for u in villa.known_unknowns))
    check("villa: no land-grading unknown",
          not any('منسوب الأرض' in u for u in villa.known_unknowns))


# ---- Issue 5b: due-diligence list ----

def _due_diligence_for(asset_type):
    """Build a minimal buyer brief and return the due_diligence content list."""
    ev = {
        'asset_type': asset_type,
        'address': 'PIN 74328443' if asset_type == 'raw_land' else '52/903/90',
        'district': 'الخور',
        'valuation': {'amount': 1200000, 'low': 1100000, 'high': 1400000},
        'plot_area_m2': 502.0,
    }
    brief = ob.generate_brief(ev, audience='buyer')
    for sec in brief.get('sections', []):
        if sec.get('id') == 'due_diligence':
            c = sec.get('content')
            return c if isinstance(c, list) else (c or {}).get('questions_ar', [])
    return []


def test_due_diligence_land_vs_building():
    land_q = _due_diligence_for('raw_land')
    bld_q = _due_diligence_for('standalone_villa')
    check("land due-diligence non-empty", len(land_q) >= 5)
    check("land: no tenant question",
          not any('مؤجر' in q or 'المستأجر' in q for q in land_q))
    check("land: no building-age question",
          not any('عمر البناء' in q for q in land_q))
    check("land: has zoning question",
          any('تصنيف المنطقة' in q for q in land_q))
    check("land: has site-grading question (Qatar-specific)",
          any('منسوب الأرض' in q for q in land_q))
    check("building: keeps tenant question (regression)",
          any('مؤجر' in q for q in bld_q))


if __name__ == "__main__":
    print("Sprint 2.21.0.5 — Land Output Polish isolated tests")
    print("=" * 70)
    test_scope_raw_land_supported()
    test_muc_land_excludes_building()
    test_muc_building_regression()
    test_due_diligence_land_vs_building()
    print("=" * 70)
    print(f"Sprint 2.21.0.5 tests: {_passed} passed, {_failed} failed")
    sys.exit(0 if _failed == 0 else 1)
