"""
test_sprint_2p22p0a_tier_breakdown.py — Sprint 2.22.0a/3 tier_breakdown
section emission tests.

Tests `build_tier_breakdown_section()` helper + audience-brief integration
per Anas Q1+Q2+R3+R5 decisions 2026-05-26.

Positive cases:
  - Hybrid response (A1-equivalent City Avenues T2+T3) → section present
    with T2+T3 rows, n_used, valuation_date
  - T3 sources count matches input (4 sources for A1)
  - Section schema matches contract (id, title_ar, content with rows
    + n_used + valuation_date)
  - 4 audience briefs all prepend the section first when hybrid present

Negative cases:
  - Non-hybrid response (A3 villa equivalent — no hybrid block) → section
    absent; helper returns None
  - Empty tier_breakdown array → section absent
  - Missing hybrid.tier_breakdown key → section absent
  - None evaluation → helper returns None defensively

Toggle interaction (JS-side per Q1 Option b) NOT tested here — manual
verification on thammen.qa post-deploy.

Standalone test runner per CLAUDE.md convention (no pytest dependency).
Run: python test_sprint_2p22p0a_tier_breakdown.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from output_briefs import (
    build_tier_breakdown_section,
    _use_case_banner_section,
    generate_brief,
)


# ─────────────────────────────────────────────────────────────────────
# Test infrastructure
# ─────────────────────────────────────────────────────────────────────
_passed = 0
_failed = 0


def _check(condition, name, detail=""):
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        print(f"  FAIL  {name}  {detail}")


# ─────────────────────────────────────────────────────────────────────
# Fixtures (drawn from Phase 1 A1 City Avenues response shape)
# ─────────────────────────────────────────────────────────────────────
_T2_ROW = {
    'tier': 'T2', 'weight': 0.88, 'raw_value': 13117.28,
    'discounted_value': 11477.62, 'discount_applied': -0.125, 'n': 79,
}

_T3_SOURCES = [
    {'developer': 'Aryan', 'project': 'City Avenues',
     'status': 'under_construction', 'value_per_m2_raw': 13372.09,
     'discount_applied': -0.175, 'value_per_m2_adjusted': 11031.97,
     'freshness_status': 'fresh'},
    {'developer': 'Aryan', 'project': 'City Avenues',
     'status': 'under_construction', 'value_per_m2_raw': 13380.00,
     'discount_applied': -0.175, 'value_per_m2_adjusted': 11038.50,
     'freshness_status': 'fresh'},
    {'developer': 'Aryan', 'project': 'City Avenues',
     'status': 'under_construction', 'value_per_m2_raw': 13390.00,
     'discount_applied': -0.175, 'value_per_m2_adjusted': 11046.75,
     'freshness_status': 'fresh'},
    {'developer': 'Aryan', 'project': 'City Avenues',
     'status': 'under_construction', 'value_per_m2_raw': 13387.83,
     'discount_applied': -0.175, 'value_per_m2_adjusted': 11045.96,
     'freshness_status': 'fresh'},
]

_T3_ROW = {
    'tier': 'T3', 'weight': 0.12, 'raw_value': 13382.48,
    'discounted_value': 11040.54, 'discount_applied': -0.175,
    'n': 4, 'n_effective': 4.0, 'shape': 'dict_new',
    'sources': _T3_SOURCES,
}

_HYBRID_EVAL = {
    'address': '69/255/75',
    'asset_type': 'apartment_building',
    'tier_label': 'analytical_range',
    'valuation_date': '2026-05-26',
    'hybrid': {
        'case': 'B', 'confidence': 'indicative',
        'muc_range_pct': 0.2, 'muc_required': True,
        'n_used': 79, 'sample_size_band': 'reliable',
        'rule_e3_compliance': 'case_B_T2_plus_T3',
        'tier_breakdown': [_T2_ROW, _T3_ROW],
    },
    'blended': {'blended_value': None, 'blended_low': None, 'blended_high': None},
}

_NON_HYBRID_EVAL = {
    'address': '31/918/99',
    'asset_type': 'standalone_villa',
    'tier_label': 'analytical_range',
    'valuation_date': '2026-05-26',
    'blended': {'blended_value': 3200000, 'blended_low': 2880000, 'blended_high': 3520000},
    # no 'hybrid' key — Umm Lekhba villa, comparison_thin path
}


# ─────────────────────────────────────────────────────────────────────
# 1. Positive: hybrid response → section present with full schema
# ─────────────────────────────────────────────────────────────────────
print("\n[1] Hybrid response → section present with T2+T3 rows + n_used + valuation_date")
sec = build_tier_breakdown_section(_HYBRID_EVAL)
_check(sec is not None, "section is not None")
_check(isinstance(sec, dict), "section is dict")
_check(sec.get('id') == 'tier_breakdown', "id == 'tier_breakdown'",
       f"got {sec.get('id')!r}")
_check(sec.get('title_ar') == 'تفصيل المصادر',
       "title_ar == 'تفصيل المصادر'",
       f"got {sec.get('title_ar')!r}")
content = sec.get('content') or {}
rows = content.get('rows') or []
_check(len(rows) == 2, "content.rows length == 2 (T2 + T3)",
       f"got {len(rows)}")
_check(rows[0].get('tier') == 'T2', "rows[0].tier == 'T2'")
_check(rows[1].get('tier') == 'T3', "rows[1].tier == 'T3'")
_check(content.get('n_used') == 79, "content.n_used == 79",
       f"got {content.get('n_used')}")
_check(content.get('valuation_date') == '2026-05-26',
       "content.valuation_date == '2026-05-26'",
       f"got {content.get('valuation_date')}")


# ─────────────────────────────────────────────────────────────────────
# 2. T3 sources count matches input (4 sources per A1 City Avenues)
# ─────────────────────────────────────────────────────────────────────
print("\n[2] T3 sources count + content passes through unchanged")
t3 = rows[1]
sources = t3.get('sources') or []
_check(len(sources) == 4, "T3 sources length == 4",
       f"got {len(sources)}")
_check(sources[0].get('developer') == 'Aryan',
       "sources[0].developer == 'Aryan'")
_check(sources[0].get('project') == 'City Avenues',
       "sources[0].project == 'City Avenues'")
_check(sources[0].get('status') == 'under_construction',
       "sources[0].status == 'under_construction' (raw English, UI maps)")
_check(sources[0].get('freshness_status') == 'fresh',
       "sources[0].freshness_status == 'fresh' (raw English, UI maps)")
_check(abs(sources[0].get('value_per_m2_adjusted') - 11031.97) < 0.01,
       "sources[0].value_per_m2_adjusted ≈ 11031.97")


# ─────────────────────────────────────────────────────────────────────
# 3. T2 row carries no sources (asymmetric shape per R1)
# ─────────────────────────────────────────────────────────────────────
print("\n[3] T2 row asymmetric shape — no sources sub-array")
t2 = rows[0]
_check('sources' not in t2 or t2.get('sources') is None,
       "T2 row has no 'sources' key (or it's None) — pass-through preserves shape")
_check(abs(t2.get('weight') - 0.88) < 0.001, "T2 weight == 0.88")
_check(t2.get('n') == 79, "T2 n == 79")


# ─────────────────────────────────────────────────────────────────────
# 4. Negative: non-hybrid response → section absent
# ─────────────────────────────────────────────────────────────────────
print("\n[4] Non-hybrid response (A3 villa) → section absent (helper returns None)")
sec_none = build_tier_breakdown_section(_NON_HYBRID_EVAL)
_check(sec_none is None, "helper returns None for non-hybrid",
       f"got {sec_none!r}")


# ─────────────────────────────────────────────────────────────────────
# 5. Negative: empty tier_breakdown array → section absent
# ─────────────────────────────────────────────────────────────────────
print("\n[5] Empty tier_breakdown array → section absent")
empty_hybrid = {
    'address': 'X/Y/Z', 'asset_type': 'apartment_building',
    'valuation_date': '2026-05-26',
    'hybrid': {'n_used': 0, 'tier_breakdown': []},
}
_check(build_tier_breakdown_section(empty_hybrid) is None,
       "empty tier_breakdown → None")


# ─────────────────────────────────────────────────────────────────────
# 6. Negative: missing tier_breakdown key → section absent
# ─────────────────────────────────────────────────────────────────────
print("\n[6] Missing tier_breakdown key in hybrid → section absent")
missing_tb = {
    'address': 'X/Y/Z', 'asset_type': 'apartment_building',
    'valuation_date': '2026-05-26',
    'hybrid': {'n_used': 79, 'case': 'B'},  # no tier_breakdown key
}
_check(build_tier_breakdown_section(missing_tb) is None,
       "missing tier_breakdown → None")


# ─────────────────────────────────────────────────────────────────────
# 7. Negative: None evaluation
# ─────────────────────────────────────────────────────────────────────
print("\n[7] None evaluation → helper returns None defensively")
_check(build_tier_breakdown_section(None) is None,
       "build_tier_breakdown_section(None) is None")
_check(build_tier_breakdown_section({}) is None,
       "build_tier_breakdown_section({}) is None (no hybrid key)")


# ─────────────────────────────────────────────────────────────────────
# 8. 4 audience briefs prepend tier_breakdown FIRST in sections (when hybrid)
# ─────────────────────────────────────────────────────────────────────
print("\n[8] All 4 audience briefs prepend tier_breakdown FIRST in sections list")
for audience in ['buyer', 'seller', 'investor', 'valuer']:
    brief = generate_brief(_HYBRID_EVAL, audience=audience, rent_data=None,
                           adjustments=None, uncertainty=None, income_value=None)
    sections = brief.get('sections') or []
    has_section = len(sections) > 0
    _check(has_section, f"[{audience}] brief has at least one section")
    if has_section:
        first = sections[0]
        _check(first.get('id') == 'tier_breakdown',
               f"[{audience}] FIRST section id == 'tier_breakdown'",
               f"got {first.get('id')!r}")
        first_content = first.get('content') or {}
        _check(len(first_content.get('rows') or []) == 2,
               f"[{audience}] tier_breakdown has 2 rows")


# ─────────────────────────────────────────────────────────────────────
# 9. Non-hybrid audience briefs do NOT include tier_breakdown
# ─────────────────────────────────────────────────────────────────────
print("\n[9] Non-hybrid (villa) audience briefs do NOT include tier_breakdown")
for audience in ['buyer', 'seller', 'investor', 'valuer']:
    brief = generate_brief(_NON_HYBRID_EVAL, audience=audience, rent_data=None,
                           adjustments=None, uncertainty=None, income_value=None)
    sections = brief.get('sections') or []
    has_tb = any(s.get('id') == 'tier_breakdown' for s in sections)
    _check(not has_tb,
           f"[{audience}] non-hybrid brief has NO tier_breakdown section")


# ─────────────────────────────────────────────────────────────────────
# 10. _use_case_banner_section stub returns None (placeholder for /4)
# ─────────────────────────────────────────────────────────────────────
print("\n[10] _use_case_banner_section stub returns None (deferred to /4)")
_check(_use_case_banner_section(_HYBRID_EVAL) is None,
       "_use_case_banner_section returns None (placeholder)")
_check(_use_case_banner_section(_HYBRID_EVAL, audience='buyer') is None,
       "_use_case_banner_section(buyer) returns None")


# ─────────────────────────────────────────────────────────────────────
# 11. Discount values pass through unchanged (UI formats; not backend)
# ─────────────────────────────────────────────────────────────────────
print("\n[11] discount_applied passes through as raw decimal (UI formats)")
sec = build_tier_breakdown_section(_HYBRID_EVAL)
rows = (sec.get('content') or {}).get('rows') or []
_check(abs(rows[0].get('discount_applied') - (-0.125)) < 1e-6,
       "T2 discount_applied passes through as -0.125 (UI converts to '−12.5%')")
_check(abs(rows[1].get('discount_applied') - (-0.175)) < 1e-6,
       "T3 discount_applied passes through as -0.175 (UI converts to '−17.5%')")


# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────
total = _passed + _failed
print("\n" + "=" * 60)
print(f"  PASSED: {_passed}/{total}")
print(f"  FAILED: {_failed}/{total}")
print("=" * 60)
sys.exit(0 if _failed == 0 else 1)
