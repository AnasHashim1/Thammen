"""
test_sprint_2p22p0a_tier_labels.py — Sprint 2.22.0a/2 tier_label emission tests

Tests _tier_label_for() helper + _TIER_LABEL_BY_METHOD registry per Y3
centralized-helper design (Anas decision 2026-05-26 + KICKOFF §4.3 + F1).

Test cohort:
  - 8 value-producing methods → 'analytical_range'
  - 3 refusal methods → None
  - 1 unknown-method default → None (defensive)
  - 1 negative test: asset_uniqueness NOT registered (defer to 2.22.y per §2.3)
  - 1 edge case: comparison_preliminary (n<5 borderline) → 'analytical_range'
  - 1 determinism test: same input → same output

Standalone test runner per CLAUDE.md convention (no pytest dependency).
Run: python test_sprint_2p22p0a_tier_labels.py
"""
import sys
import os

# Add deploy v2/ to path so we can import evaluate_unified
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from evaluate_unified import _tier_label_for, _TIER_LABEL_BY_METHOD


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
# 1. 8 value-producing methods → 'analytical_range'
# ─────────────────────────────────────────────────────────────────────
print("\n[1] 8 value-producing methods → 'analytical_range'")
_value_producing_methods = [
    'comparison_bracket',
    'comparison_widened',
    'comparison_widened_indicative',
    'comparison_thin',
    'comparison_preliminary',
    'hybrid_t2',
    'listing_only_implied_rent',
    'income_approach_only',
]
for method in _value_producing_methods:
    result = _tier_label_for(method)
    _check(result == 'analytical_range',
           f"_tier_label_for({method!r}) == 'analytical_range'",
           f"got {result!r}")


# ─────────────────────────────────────────────────────────────────────
# 2. 3 refusal methods → None
# ─────────────────────────────────────────────────────────────────────
print("\n[2] 3 refusal methods → None (refusal_reason in /5 will carry signal)")
_refusal_methods = [
    'insufficient_data',
    'out_of_scope_v1',
    'asset_type_reality_stop',
]
for method in _refusal_methods:
    result = _tier_label_for(method)
    _check(result is None,
           f"_tier_label_for({method!r}) is None",
           f"got {result!r}")


# ─────────────────────────────────────────────────────────────────────
# 3. Unknown method → None (defensive default per dict.get())
# ─────────────────────────────────────────────────────────────────────
print("\n[3] Unknown method → None (defensive default)")
for unknown in ['nonexistent_method_xyz', '', None]:
    result = _tier_label_for(unknown)
    _check(result is None,
           f"_tier_label_for({unknown!r}) is None",
           f"got {result!r}")


# ─────────────────────────────────────────────────────────────────────
# 4. NEGATIVE TEST — asset_uniqueness NOT in registry (deferred to 2.22.y per §2.3)
# ─────────────────────────────────────────────────────────────────────
print("\n[4] NEGATIVE: asset_uniqueness NOT in _TIER_LABEL_BY_METHOD (deferred to 2.22.y per §2.3)")
_check('asset_uniqueness' not in _TIER_LABEL_BY_METHOD,
       "'asset_uniqueness' NOT in _TIER_LABEL_BY_METHOD",
       "asset_uniqueness was added before 2.22.y — KICKOFF §2.3 says defer until 3σ compute lands")
_check(_tier_label_for('asset_uniqueness') is None,
       "_tier_label_for('asset_uniqueness') is None (deferred trigger)",
       f"got {_tier_label_for('asset_uniqueness')!r}")


# ─────────────────────────────────────────────────────────────────────
# 5. Edge case — comparison_preliminary (n<5 borderline) per R4 decision
# ─────────────────────────────────────────────────────────────────────
print("\n[5] Edge case: comparison_preliminary (R4 Anas decision — analytical_range)")
_check(_tier_label_for('comparison_preliminary') == 'analytical_range',
       "comparison_preliminary → 'analytical_range' per R4 Option A consistency",
       "accuracy_score carries the strength warning; tier_label = TYPE only")


# ─────────────────────────────────────────────────────────────────────
# 6. Determinism — same input → same output
# ─────────────────────────────────────────────────────────────────────
print("\n[6] Determinism (same input → same output across 100 calls)")
import random
random.seed(2022)
sample_inputs = ['hybrid_t2', 'insufficient_data', 'comparison_thin', None, 'unknown_xyz']
for _ in range(100):
    method = random.choice(sample_inputs)
    first = _tier_label_for(method)
    second = _tier_label_for(method)
    if first != second:
        _check(False, f"NON-DETERMINISTIC on {method!r}: {first!r} vs {second!r}")
        break
else:
    _check(True, "100 random calls — deterministic")


# ─────────────────────────────────────────────────────────────────────
# 7. Registry completeness — every method in _TIER_LABEL_BY_METHOD must
# map to one of the 4 allowed tier_label values (or None)
# ─────────────────────────────────────────────────────────────────────
print("\n[7] Registry value-set discipline (4 allowed tier_label values + None)")
_ALLOWED_VALUES = {'indicative_estimate', 'analytical_range',
                   'broker_verified_range', 'signed_valuation', None}
for method, label in _TIER_LABEL_BY_METHOD.items():
    _check(label in _ALLOWED_VALUES,
           f"_TIER_LABEL_BY_METHOD[{method!r}] = {label!r} ∈ allowed set",
           f"unexpected tier_label value")


# ─────────────────────────────────────────────────────────────────────
# 8. 'indicative_estimate' / 'broker_verified_range' / 'signed_valuation'
# are NOT yet assigned to any method in 2.22.0a (reserved for future sprints)
# ─────────────────────────────────────────────────────────────────────
print("\n[8] Future tier values reserved (no 2.22.0a method maps to them)")
_reserved_values = {'indicative_estimate', 'broker_verified_range', 'signed_valuation'}
for reserved in _reserved_values:
    methods_using = [m for m, v in _TIER_LABEL_BY_METHOD.items() if v == reserved]
    _check(len(methods_using) == 0,
           f"No method in 2.22.0a maps to {reserved!r}",
           f"these methods used the reserved value: {methods_using}")


# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────
total = _passed + _failed
print("\n" + "=" * 60)
print(f"  PASSED: {_passed}/{total}")
print(f"  FAILED: {_failed}/{total}")
print("=" * 60)
sys.exit(0 if _failed == 0 else 1)
