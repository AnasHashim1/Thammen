"""
test_sprint_2p22p0a_use_case_banner.py — Sprint 2.22.0a/4 use_case_banner
section emission tests.

Tests `_use_case_banner_section()` helper + `USE_CASE_BANNER` constant
per Anas Q1+Q2+Q3+Q4 decisions 2026-05-26 + architecture refinement
(no per-builder injection; refusal-gating via _tier_label_for reuse).

Coverage:
  - Positive: 8 value-producing methods → banner present
  - Negative: 3 refusal methods → banner absent (via _tier_label_for None)
  - Negative: missing/unknown method → banner absent
  - Content: investment_underwriting in suitable_for (Q1 §6.7 canonical)
  - Content: bank-aware disclaimer embedded (Q4)
  - Content: Portfolio NOT in any bucket (Q3)
  - Content: 5+2+2=9 items (Q2 deliberate redundancy preserved)
  - Audience integration: 4 audiences include banner uniformly
  - Section ordering: index[0] non-hybrid, index[1] hybrid (after
    tier_breakdown)

Standalone test runner per CLAUDE.md convention.
Run: python test_sprint_2p22p0a_use_case_banner.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from evaluate_unified import USE_CASE_BANNER, _tier_label_for
from output_briefs import _use_case_banner_section, generate_brief


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
# Fixtures
# ─────────────────────────────────────────────────────────────────────
def _eval_with_method(method):
    """Construct a minimal evaluation dict with the given valuation.method."""
    return {
        'address': 'X/Y/Z',
        'asset_type': 'apartment_building',
        'valuation_date': '2026-05-26',
        'valuation': {'method': method},
        'blended': {'blended_value': 1000000},
    }


_HYBRID_EVAL = {
    'address': '69/255/75',
    'asset_type': 'apartment_building',
    'valuation_date': '2026-05-26',
    'valuation': {'method': 'hybrid_t2'},
    'hybrid': {
        'n_used': 79,
        'tier_breakdown': [
            {'tier': 'T2', 'weight': 0.88, 'n': 79,
             'raw_value': 13117.28, 'discounted_value': 11477.62,
             'discount_applied': -0.125},
            {'tier': 'T3', 'weight': 0.12, 'n': 4,
             'raw_value': 13382.48, 'discounted_value': 11040.54,
             'discount_applied': -0.175,
             'sources': [{'developer': 'Aryan', 'project': 'City Avenues',
                          'status': 'under_construction',
                          'value_per_m2_raw': 13372.09,
                          'value_per_m2_adjusted': 11031.97,
                          'discount_applied': -0.175,
                          'freshness_status': 'fresh'}]},
        ],
    },
    'blended': {'blended_value': None},
}


_NON_HYBRID_EVAL = {
    'address': '31/918/99',
    'asset_type': 'standalone_villa',
    'valuation_date': '2026-05-26',
    'valuation': {'method': 'comparison_thin'},
    'blended': {'blended_value': 3200000},
}


# ─────────────────────────────────────────────────────────────────────
# 1. Positive: 8 value-producing methods → banner present
# ─────────────────────────────────────────────────────────────────────
print("\n[1] 8 value-producing methods → banner section present")
_value_methods = [
    'comparison_bracket', 'comparison_widened',
    'comparison_widened_indicative', 'comparison_thin',
    'comparison_preliminary', 'hybrid_t2',
    'listing_only_implied_rent', 'income_approach_only',
]
for m in _value_methods:
    ev = _eval_with_method(m)
    sec = _use_case_banner_section(ev)
    _check(sec is not None, f"_use_case_banner_section(method={m!r}) is not None")
    if sec:
        _check(sec.get('id') == 'use_case_banner',
               f"  [{m}] id == 'use_case_banner'")


# ─────────────────────────────────────────────────────────────────────
# 2. Negative: 3 refusal methods → banner absent
# ─────────────────────────────────────────────────────────────────────
print("\n[2] 3 refusal methods → banner absent (refusal-gated via _tier_label_for)")
_refusal_methods = ['insufficient_data', 'out_of_scope_v1', 'asset_type_reality_stop']
for m in _refusal_methods:
    ev = _eval_with_method(m)
    sec = _use_case_banner_section(ev)
    _check(sec is None,
           f"_use_case_banner_section(method={m!r}) is None (refusal-gated)",
           f"got {sec}")


# ─────────────────────────────────────────────────────────────────────
# 3. Negative: missing/unknown/None method → banner absent
# ─────────────────────────────────────────────────────────────────────
print("\n[3] Missing/unknown method → banner absent (defensive)")
_check(_use_case_banner_section({'valuation': {}}) is None,
       "missing method key → None")
_check(_use_case_banner_section({}) is None,
       "empty evaluation → None")
_check(_use_case_banner_section(None) is None,
       "None evaluation → None")
_check(_use_case_banner_section(_eval_with_method('nonexistent_method_xyz')) is None,
       "unknown method → None (no tier_label registered)")


# ─────────────────────────────────────────────────────────────────────
# 4. Content (Q1) — investment_underwriting in suitable_for per §6.7
# ─────────────────────────────────────────────────────────────────────
print("\n[4] Q1 — investment_underwriting in suitable_for (§6.7 canonical, not line 96)")
suit_joined = ' '.join(USE_CASE_BANNER['suitable_for'])
_check('الاستثمار' in suit_joined,
       "'الاستثمار' appears in suitable_for")
notsuit_joined = ' '.join(USE_CASE_BANNER['not_suitable_for'])
_check('الاستثمار' not in notsuit_joined,
       "'الاستثمار' NOT in not_suitable_for (Q1 §6.7 wins over line 96)",
       f"investment_underwriting incorrectly classified as not_suitable")


# ─────────────────────────────────────────────────────────────────────
# 5. Content (Q4) — bank-aware disclaimer embedded
# ─────────────────────────────────────────────────────────────────────
print("\n[5] Q4 — bank-aware disclaimer embedded inline (suitable_for entry)")
_check(any('تحفظات بنكية' in entry for entry in USE_CASE_BANNER['suitable_for']),
       "'تحفظات بنكية' embedded in a suitable_for entry (mortgage pre-qualification)")
_check(any('رهن' in entry and 'تحفظات' in entry
           for entry in USE_CASE_BANNER['suitable_for']),
       "mortgage pre-qualification entry includes disclaimer phrase ('رهن' root + 'تحفظات' caveat)")


# ─────────────────────────────────────────────────────────────────────
# 6. Content (Q3) — Portfolio NOT in any bucket
# ─────────────────────────────────────────────────────────────────────
print("\n[6] Q3 — Portfolio (B2B Basel) OMITTED from all 3 buckets")
all_entries = (USE_CASE_BANNER['suitable_for']
               + USE_CASE_BANNER['not_suitable_for']
               + USE_CASE_BANNER['stage5_required_for'])
all_text = ' '.join(all_entries)
_check('Portfolio' not in all_text and 'محفظة' not in all_text and 'Basel' not in all_text,
       "Portfolio/محفظة/Basel NOT mentioned in any bucket entry",
       f"all entries: {all_entries}")


# ─────────────────────────────────────────────────────────────────────
# 7. Content (Q2) — 5+2+2=9 items, deliberate redundancy preserved
# ─────────────────────────────────────────────────────────────────────
print("\n[7] Q2 — 5+2+2=9 items, deliberate redundancy between buckets 2 and 3")
_check(len(USE_CASE_BANNER['suitable_for']) == 5,
       f"suitable_for has 5 items",
       f"got {len(USE_CASE_BANNER['suitable_for'])}")
_check(len(USE_CASE_BANNER['not_suitable_for']) == 2,
       f"not_suitable_for has 2 items",
       f"got {len(USE_CASE_BANNER['not_suitable_for'])}")
_check(len(USE_CASE_BANNER['stage5_required_for']) == 2,
       f"stage5_required_for has 2 items",
       f"got {len(USE_CASE_BANNER['stage5_required_for'])}")

# Deliberate redundancy: bucket 2 and bucket 3 mention the SAME use cases
# (mortgage origination + court/inheritance) — different framings
notsuit = USE_CASE_BANNER['not_suitable_for']
stage5 = USE_CASE_BANNER['stage5_required_for']
_check(any('الرهن العقاري الرسمي' in e for e in notsuit) and
       any('الرهن العقاري الرسمي' in e for e in stage5),
       "Mortgage origination appears in BOTH not_suitable_for and stage5_required_for (Q2 redundancy)")
_check((any('النزاعات' in e or 'الميراث' in e for e in notsuit)) and
       (any('النزاعات' in e or 'الميراث' in e for e in stage5)),
       "Court/dispute/inheritance appears in BOTH buckets (Q2 redundancy)")


# ─────────────────────────────────────────────────────────────────────
# 8. Audience integration — 4 audiences include banner uniformly
# ─────────────────────────────────────────────────────────────────────
print("\n[8] 4 audience briefs include banner uniformly (single-dimension §6.7)")
for audience in ['buyer', 'seller', 'investor', 'valuer']:
    brief = generate_brief(_NON_HYBRID_EVAL, audience=audience, rent_data=None,
                           adjustments=None, uncertainty=None, income_value=None)
    sections = brief.get('sections') or []
    has_banner = any(s.get('id') == 'use_case_banner' for s in sections)
    _check(has_banner,
           f"[{audience}] non-hybrid brief includes use_case_banner")
    # Content identical across audiences (no per-audience customization)
    banners = [s for s in sections if s.get('id') == 'use_case_banner']
    if banners:
        content = banners[0].get('content') or {}
        _check(content == USE_CASE_BANNER,
               f"[{audience}] banner content == USE_CASE_BANNER constant (no audience customization)")


# ─────────────────────────────────────────────────────────────────────
# 9. Section ordering — banner index in sections list
# ─────────────────────────────────────────────────────────────────────
print("\n[9] Section ordering per Anas: tier_breakdown then use_case_banner then rest")

# Non-hybrid: banner at index[0] (no tier_breakdown precedes it)
for audience in ['buyer', 'seller', 'investor', 'valuer']:
    brief = generate_brief(_NON_HYBRID_EVAL, audience=audience, rent_data=None,
                           adjustments=None, uncertainty=None, income_value=None)
    sections = brief.get('sections') or []
    if sections:
        _check(sections[0].get('id') == 'use_case_banner',
               f"[non-hybrid/{audience}] sections[0].id == 'use_case_banner'",
               f"got {sections[0].get('id')}")

# Hybrid: banner at index[1] (tier_breakdown at index[0] precedes it)
for audience in ['buyer', 'seller', 'investor', 'valuer']:
    brief = generate_brief(_HYBRID_EVAL, audience=audience, rent_data=None,
                           adjustments=None, uncertainty=None, income_value=None)
    sections = brief.get('sections') or []
    if len(sections) >= 2:
        _check(sections[0].get('id') == 'tier_breakdown' and
               sections[1].get('id') == 'use_case_banner',
               f"[hybrid/{audience}] sections[0]=tier_breakdown, sections[1]=use_case_banner",
               f"got [{sections[0].get('id')}, {sections[1].get('id')}]")


# ─────────────────────────────────────────────────────────────────────
# 10. Refusal-gating via _tier_label_for — cross-check consistency
# ─────────────────────────────────────────────────────────────────────
print("\n[10] Refusal-gating consistency: every method where _tier_label_for returns None should also yield banner=None")
_all_methods_under_test = _value_methods + _refusal_methods + ['unknown_method_xyz']
for m in _all_methods_under_test:
    tier = _tier_label_for(m)
    sec = _use_case_banner_section(_eval_with_method(m))
    if tier is None:
        _check(sec is None,
               f"method={m!r}: _tier_label_for=None ⇒ banner=None (gating consistency)")
    else:
        _check(sec is not None,
               f"method={m!r}: _tier_label_for={tier!r} ⇒ banner present (gating consistency)")


# ─────────────────────────────────────────────────────────────────────
# 11. Content (Q1) — line 96 paraphrasing artifact NOT followed
# ─────────────────────────────────────────────────────────────────────
print("\n[11] Q1 confirm — pre-listing + mortgage pre-qual + investment underwriting all in suitable_for")
suit_joined = ' '.join(USE_CASE_BANNER['suitable_for'])
_check('التسعير قبل الإعلان' in suit_joined, "pre-listing pricing guidance in suitable_for")
_check('التأهيل المسبق للرهن' in suit_joined, "mortgage pre-qualification in suitable_for")
_check('الاستثمار' in suit_joined, "investment underwriting in suitable_for (§6.7 canonical)")


# Summary
total = _passed + _failed
print("\n" + "=" * 60)
print(f"  PASSED: {_passed}/{total}")
print(f"  FAILED: {_failed}/{total}")
print("=" * 60)
sys.exit(0 if _failed == 0 else 1)
