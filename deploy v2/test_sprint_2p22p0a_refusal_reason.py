"""
test_sprint_2p22p0a_refusal_reason.py — Sprint 2.22.0a/5 refusal_reason
emission tests + precedence chain dispatch tests.

Tests:
  - refusal_templates.REFUSAL_TEMPLATES (6 trigger registry)
  - refusal_templates.get_refusal_template() (lookup + .format substitution)
  - evaluate_unified._compute_refusal_reason() (§5.3 precedence chain)
  - evaluate_unified._DENSITY_GATED_DISTRICTS (Pearl-only Q2 (α))
  - evaluate_unified._load_district_regimes() (empty registry skeleton)
  - output_briefs._refusal_reason_section() (section helper)
  - Audience brief integration (4 audiences prepend refusal_reason FIRST
    when refusal path)
  - Cross-check consistency with /2 + /4 (mutual exclusion: tier_label
    is None ⇔ refusal_reason is not None — except defensive None case
    for unknown methods)

Standalone test runner per CLAUDE.md convention.
Run: python test_sprint_2p22p0a_refusal_reason.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from refusal_templates import (
    REFUSAL_TEMPLATES, get_refusal_template, is_registered,
)
from evaluate_unified import (
    _tier_label_for, _compute_refusal_reason,
    _DENSITY_GATED_DISTRICTS, _load_district_regimes,
)
from output_briefs import _refusal_reason_section, generate_brief


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
# 1. REFUSAL_TEMPLATES registry — 6 active triggers per Anas Q1 (d)
# ─────────────────────────────────────────────────────────────────────
print("\n[1] REFUSAL_TEMPLATES registry — 6 active triggers (5 §1.6 + 1 §1.6-ext)")
_expected_triggers = {
    'comp_density_sparse', 'spatial_ambiguity', 'regime_shift',
    'asset_scale_extreme', 'density_gated_district',
    'asset_class_out_of_scope',  # NEW per Q1 (d)
}
_check(set(REFUSAL_TEMPLATES.keys()) == _expected_triggers,
       f"REFUSAL_TEMPLATES has exactly 6 expected trigger_ids",
       f"got {sorted(REFUSAL_TEMPLATES.keys())}")
_check(len(REFUSAL_TEMPLATES) == 6, "len(REFUSAL_TEMPLATES) == 6",
       f"got {len(REFUSAL_TEMPLATES)}")

# All templates have 3 required Arabic+English+recommendation fields
print("\n[1.b] All 6 templates have {message_ar, message_en, recommendation_ar}")
for tid, tpl in REFUSAL_TEMPLATES.items():
    _check('message_ar' in tpl and len(tpl['message_ar']) > 10,
           f"[{tid}] message_ar present and non-trivial")
    _check('message_en' in tpl and len(tpl['message_en']) > 10,
           f"[{tid}] message_en present and non-trivial")
    _check('recommendation_ar' in tpl and len(tpl['recommendation_ar']) > 5,
           f"[{tid}] recommendation_ar present and non-trivial")


# ─────────────────────────────────────────────────────────────────────
# 2. NEGATIVE — asset_uniqueness NOT registered (deferred per §2.3)
# ─────────────────────────────────────────────────────────────────────
print("\n[2] NEGATIVE — asset_uniqueness NOT in REFUSAL_TEMPLATES (deferred to 2.22.y)")
_check('asset_uniqueness' not in REFUSAL_TEMPLATES,
       "asset_uniqueness NOT registered (Anas §2.3 deferral)")
_check(not is_registered('asset_uniqueness'),
       "is_registered('asset_uniqueness') == False")


# ─────────────────────────────────────────────────────────────────────
# 3. get_refusal_template() — basic lookup
# ─────────────────────────────────────────────────────────────────────
print("\n[3] get_refusal_template() basic lookup for 6 triggers")
for tid in _expected_triggers:
    r = get_refusal_template(tid)
    _check(r['trigger_id'] == tid, f"trigger_id == {tid!r}")
    _check('message_ar' in r and 'message_en' in r and 'recommendation_ar' in r,
           f"[{tid}] has all 3 message fields")
    _check('context' in r and isinstance(r['context'], dict),
           f"[{tid}] context is dict (Q3 (ii))")


# ─────────────────────────────────────────────────────────────────────
# 4. get_refusal_template() — context substitution for regime_shift
# ─────────────────────────────────────────────────────────────────────
print("\n[4] regime_shift {event_name} substitution")
# Default empty event_name → no substring leak
r = get_refusal_template('regime_shift')
_check('{event_name}' not in r['message_ar'],
       "regime_shift with no event_name → no leftover placeholder in message_ar")
_check('{event_name}' not in r['message_en'],
       "regime_shift with no event_name → no leftover placeholder in message_en")

# Populated event_name
r2 = get_refusal_template('regime_shift', event_name=' — إعلان مشروع X')
_check('إعلان مشروع X' in r2['message_ar'],
       "regime_shift with event_name populated → text appears in message_ar")


# ─────────────────────────────────────────────────────────────────────
# 5. get_refusal_template() — explicit ValueError on unknown trigger_id
# ─────────────────────────────────────────────────────────────────────
print("\n[5] get_refusal_template() raises ValueError on unknown trigger_id")
try:
    get_refusal_template('nonexistent_trigger_xyz')
    _check(False, "ValueError NOT raised — registry NOT source of truth!")
except ValueError as e:
    _check('nonexistent_trigger_xyz' in str(e),
           "ValueError raised with offending trigger_id in message")


# ─────────────────────────────────────────────────────────────────────
# 6. _compute_refusal_reason — defensive None cases
# ─────────────────────────────────────────────────────────────────────
print("\n[6] _compute_refusal_reason defensive symmetry with /2 + /4")
# Unknown method → None
_check(_compute_refusal_reason('nonexistent_method_xyz') is None,
       "unknown method → None (mirrors /2 + /4 silent)")
_check(_compute_refusal_reason(None) is None,
       "None method → None (defensive)")

# Value-producing methods → None (8 from /2)
print("\n[6.b] Value-producing methods → None (mutual exclusion with tier_label)")
for vm in ['comparison_bracket', 'comparison_widened',
           'comparison_widened_indicative', 'comparison_thin',
           'comparison_preliminary', 'hybrid_t2',
           'listing_only_implied_rent', 'income_approach_only']:
    _check(_compute_refusal_reason(vm) is None,
           f"method={vm!r} → None (tier_label='analytical_range' fires instead)")


# ─────────────────────────────────────────────────────────────────────
# 7. _compute_refusal_reason — §5.3 precedence chain dispatch
# ─────────────────────────────────────────────────────────────────────
print("\n[7] §5.3 precedence chain dispatch — 6 trigger paths")

# Row 1: density_gated_district (Pearl override — Q2 (α))
r = _compute_refusal_reason(
    method='insufficient_data',
    asset_type='tower',
    district_ar='جزيرة اللؤلؤة',  # Pearl
    plot_area_m2=1500,
)
_check(r is not None and r['trigger_id'] == 'density_gated_district',
       "Pearl (district='جزيرة اللؤلؤة') → density_gated_district",
       f"got {r.get('trigger_id') if r else None}")

# Row 2: spatial_ambiguity (asset_type_reality_stop)
r = _compute_refusal_reason(
    method='asset_type_reality_stop',
    asset_type='unknown',
    district_ar='عنيزة 66',
)
_check(r is not None and r['trigger_id'] == 'spatial_ambiguity',
       "asset_type_reality_stop → spatial_ambiguity",
       f"got {r.get('trigger_id') if r else None}")

# Row 3: asset_scale_extreme (compound_large + ≥15K m²)
r = _compute_refusal_reason(
    method='insufficient_data',
    asset_type='compound_large',
    district_ar='الغرافة',
    plot_area_m2=67000,  # 51/835/17 extent — beyond E20 boundary
)
_check(r is not None and r['trigger_id'] == 'asset_scale_extreme',
       "compound_large + 67K m² → asset_scale_extreme",
       f"got {r.get('trigger_id') if r else None}")

# Row 3b: compound_large + just at 15K (boundary)
r = _compute_refusal_reason(
    method='insufficient_data',
    asset_type='compound_large',
    district_ar='الدفنة',
    plot_area_m2=15000,  # exactly at boundary
)
_check(r is not None and r['trigger_id'] == 'asset_scale_extreme',
       "compound_large + exactly 15K m² → asset_scale_extreme (>= boundary)")

# Row 4: asset_class_out_of_scope (NEW Q1 (d))
r = _compute_refusal_reason(
    method='out_of_scope_v1',
    asset_type='commercial',
    district_ar='الدفنة',
)
_check(r is not None and r['trigger_id'] == 'asset_class_out_of_scope',
       "out_of_scope_v1 (commercial) → asset_class_out_of_scope")

# Row 5: regime_shift (empty registry — never fires in 2.22.0a)
r = _compute_refusal_reason(
    method='insufficient_data',
    asset_type='standalone_villa',
    district_ar='الدحيل',
    plot_area_m2=900,
)
_check(r is not None and r['trigger_id'] != 'regime_shift',
       "Sprint 2.22.0a: regime_shift NEVER fires (empty registry per §5.4)",
       f"got {r['trigger_id']}")

# Row 6: comp_density_sparse (default fallback)
r = _compute_refusal_reason(
    method='insufficient_data',
    asset_type='standalone_villa',
    district_ar='الدحيل',
    plot_area_m2=900,
)
_check(r is not None and r['trigger_id'] == 'comp_density_sparse',
       "insufficient_data + non-Pearl + non-compound_large → comp_density_sparse fallback")


# ─────────────────────────────────────────────────────────────────────
# 8. _DENSITY_GATED_DISTRICTS — Pearl only per Q2 (α)
# ─────────────────────────────────────────────────────────────────────
print("\n[8] _DENSITY_GATED_DISTRICTS — Pearl only (Q2 α)")
_check('جزيرة اللؤلؤة' in _DENSITY_GATED_DISTRICTS,
       "'جزيرة اللؤلؤة' (Pearl) IN _DENSITY_GATED_DISTRICTS")
_check('لوسيل 69' not in _DENSITY_GATED_DISTRICTS,
       "'لوسيل 69' NOT in (Lusail covered via D10 gate, not density-gated)")
_check('الدفنة' not in _DENSITY_GATED_DISTRICTS,
       "'الدفنة' (West Bay) NOT in (uses comp_density_sparse instead)")
_check(len(_DENSITY_GATED_DISTRICTS) == 1,
       "len(_DENSITY_GATED_DISTRICTS) == 1 (Pearl only in 2.22.0a)",
       f"got {len(_DENSITY_GATED_DISTRICTS)} items")


# ─────────────────────────────────────────────────────────────────────
# 9. _load_district_regimes — empty skeleton
# ─────────────────────────────────────────────────────────────────────
print("\n[9] _load_district_regimes — empty events skeleton per §5.4")
regimes = _load_district_regimes()
_check(isinstance(regimes, dict), "regimes is dict")
_check('events' in regimes, "'events' key present")
_check(isinstance(regimes['events'], list), "regimes['events'] is list")
_check(len(regimes['events']) == 0,
       "regimes['events'] is EMPTY (2.22.0a per §5.4)",
       f"got {len(regimes['events'])} events — should be 0")


# ─────────────────────────────────────────────────────────────────────
# 10. Context propagation (Q3 (ii) standard fields)
# ─────────────────────────────────────────────────────────────────────
print("\n[10] Q3 (ii) standard context propagation")
r = _compute_refusal_reason(
    method='asset_type_reality_stop',
    asset_type='unknown',
    district_ar='عنيزة 66',
    plot_area_m2=59501,
)
ctx = r.get('context') or {}
_check(ctx.get('asset_type') == 'unknown', "context.asset_type propagated")
_check(ctx.get('district_ar') == 'عنيزة 66', "context.district_ar propagated")
_check(ctx.get('plot_area_m2') == 59501, "context.plot_area_m2 propagated")


# ─────────────────────────────────────────────────────────────────────
# 11. _refusal_reason_section() helper
# ─────────────────────────────────────────────────────────────────────
print("\n[11] _refusal_reason_section() helper")
eval_with_rr = {
    'refusal_reason': {
        'trigger_id': 'spatial_ambiguity',
        'message_ar': 'تعذّر ربط عقارك...',
        'recommendation_ar': 'تقييم متخصص...',
    },
}
sec = _refusal_reason_section(eval_with_rr)
_check(sec is not None, "section present when refusal_reason in evaluation")
_check(sec.get('id') == 'refusal_reason', "id == 'refusal_reason'")
_check(sec.get('content', {}).get('trigger_id') == 'spatial_ambiguity',
       "content carries trigger_id")

# Negative — refusal_reason absent
_check(_refusal_reason_section({}) is None,
       "empty evaluation → section None")
_check(_refusal_reason_section({'refusal_reason': None}) is None,
       "refusal_reason=None → section None")
_check(_refusal_reason_section(None) is None,
       "None evaluation → section None")


# ─────────────────────────────────────────────────────────────────────
# 12. Audience brief integration — refusal_reason FIRST when refusal
# ─────────────────────────────────────────────────────────────────────
print("\n[12] 4 audience briefs prepend refusal_reason FIRST when present")
_REFUSAL_EVAL = {
    'address': '66/140/6',
    'asset_type': 'tower',
    'valuation_date': '2026-05-26',
    'valuation': {'method': 'insufficient_data'},
    'refusal_reason': {
        'trigger_id': 'density_gated_district',
        'message_ar': 'بيانات هذه المنطقة في طور الاكتمال.',
        'recommendation_ar': 'نوصي بتقييم متخصص.',
    },
    'blended': {'blended_value': None},
}
for audience in ['buyer', 'seller', 'investor', 'valuer']:
    brief = generate_brief(_REFUSAL_EVAL, audience=audience, rent_data=None,
                           adjustments=None, uncertainty=None, income_value=None)
    sections = brief.get('sections') or []
    _check(len(sections) > 0,
           f"[{audience}] brief has at least one section")
    if sections:
        _check(sections[0].get('id') == 'refusal_reason',
               f"[{audience}] sections[0].id == 'refusal_reason' (FIRST)")
    # use_case_banner + tier_breakdown should NOT appear (refusal-gated)
    has_ucb = any(s.get('id') == 'use_case_banner' for s in sections)
    has_tb = any(s.get('id') == 'tier_breakdown' for s in sections)
    _check(not has_ucb,
           f"[{audience}] NO use_case_banner on refusal (gated)")
    _check(not has_tb,
           f"[{audience}] NO tier_breakdown on refusal (gated)")


# ─────────────────────────────────────────────────────────────────────
# 13. Cross-check mutual exclusion: tier_label vs refusal_reason
# ─────────────────────────────────────────────────────────────────────
print("\n[13] CROSS-CHECK: _tier_label_for None ⇔ _compute_refusal_reason non-None (within known methods)")
# All known methods (12 in _TIER_LABEL_BY_METHOD via /2 dict)
_known_methods = [
    'comparison_bracket', 'comparison_widened', 'comparison_widened_indicative',
    'comparison_thin', 'comparison_preliminary', 'hybrid_t2',
    'listing_only_implied_rent', 'income_approach_only',
    'insufficient_data', 'out_of_scope_v1', 'asset_type_reality_stop',
]
for m in _known_methods:
    tl = _tier_label_for(m)
    rr = _compute_refusal_reason(m, asset_type='standalone_villa',
                                  district_ar='الدحيل', plot_area_m2=900)
    if tl is not None:
        # Value-producing: refusal_reason should be None
        _check(rr is None,
               f"[{m}] value-producing → tier_label={tl!r}, refusal_reason=None")
    else:
        # Refusal: refusal_reason should be non-None
        _check(rr is not None,
               f"[{m}] refusal → tier_label=None, refusal_reason={rr['trigger_id'] if rr else None}")


# ─────────────────────────────────────────────────────────────────────
# 14. Non-refusal evaluation → no refusal_reason in audience brief
# ─────────────────────────────────────────────────────────────────────
print("\n[14] Non-refusal evaluation → refusal_reason section ABSENT")
_VAL_EVAL = {
    'address': '31/918/99',
    'asset_type': 'standalone_villa',
    'tier_label': 'analytical_range',
    'valuation_date': '2026-05-26',
    'valuation': {'method': 'comparison_thin', 'amount': 3200000},
    # no refusal_reason key — non-refusal path
    'blended': {'blended_value': 3200000},
}
for audience in ['buyer', 'seller', 'investor', 'valuer']:
    brief = generate_brief(_VAL_EVAL, audience=audience, rent_data=None,
                           adjustments=None, uncertainty=None, income_value=None)
    sections = brief.get('sections') or []
    has_rr = any(s.get('id') == 'refusal_reason' for s in sections)
    _check(not has_rr,
           f"[{audience}] non-refusal evaluation has NO refusal_reason section")


# Summary
total = _passed + _failed
print("\n" + "=" * 60)
print(f"  PASSED: {_passed}/{total}")
print(f"  FAILED: {_failed}/{total}")
print("=" * 60)
sys.exit(0 if _failed == 0 else 1)
