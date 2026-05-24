"""
tests/test_sprint_2p21p2_hybrid_foundation.py
=============================================
Sprint 2.21.2 — Hybrid Valuation Foundation.

Run: python tests/test_sprint_2p21p2_hybrid_foundation.py

Covers BRIEF §6 falsifiable predictions H1-H4 + H6.
H5 (regression — all existing standalone tests still pass) is covered
by the §9.7 regression run, not this file.

H1 — function passes own unit tests covering Cases A/B/C/D + Constraint
     7/8 violations (this file)
H2 — T1=None + T2=[X×3] + T3=None → indicative, muc_required=True,
     T2_weight reaches 0.85+
H3 — T1 n=30 + T2 n=3 → T1 weight ≥0.7
H4 — T1=None + T2=None + T3=[X×2] → fallback citing Rule E3 §8
H6 — Empirical_Findings.md Rule E3 has exactly 8 numbered constraints
     and no occurrence of "MUST NOT enter calculation"

Rule #40 production verification: imports `hybrid_valuation_v1` and
`HYBRID_TIER_CONFIG` from the actual production module at repo root.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hybrid_valuation import hybrid_valuation_v1, HYBRID_TIER_CONFIG  # noqa: E402

_passed = 0
_failed = 0


def check(name, cond, detail=None):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  ok  {name}")
    else:
        _failed += 1
        msg = f"  XX  {name}"
        if detail is not None:
            msg += f"  -- {detail}"
        print(msg)


# ====================================================================
# Case A — T1 present (dominance)
# ====================================================================

def test_01_case_A_strong_T1_T2_T3():
    """Case A: T1 n=30 + T2 n=5 + T3 n=2. Expect reliable."""
    r = hybrid_valuation_v1(
        t1_values=[{"value_per_m2": 14000.0}] * 5,
        t1_n_total=30,
        t2_values=[{"value_per_m2": 16000.0}] * 5,
        t3_values=[{"value_per_m2": 17000.0}] * 2,
    )
    check("case A returns numeric value", isinstance(r["value_per_m2"], float))
    check("case A confidence is reliable (T1 n>=20)", r["confidence"] == "reliable")
    check("case A case label is 'A'", r.get("case") == "A")
    check("case A no MUC required when T1 dominant", r["muc_required"] is False)
    check("case A no fallback_reason", r["fallback_reason"] is None)
    check("case A rule_e3_compliance present", r["rule_e3_compliance"] == "compliant")
    # T2 cap math: evidence_strength(5, 0.40, full_cap_at_n=10) = 0.20
    t2_entry = next(t for t in r["tier_breakdown"] if t["tier"] == "T2")
    check("case A T2 weight respects evidence ramp (n=5 -> 0.20)",
          abs(t2_entry["weight"] - 0.20) < 0.001,
          detail=f"got {t2_entry['weight']}")
    # T3 cap math: evidence_strength(2, 0.15, full_cap_at_n=5) = 0.06
    t3_entry = next(t for t in r["tier_breakdown"] if t["tier"] == "T3")
    check("case A T3 weight respects evidence ramp (n=2 -> 0.06)",
          abs(t3_entry["weight"] - 0.06) < 0.001,
          detail=f"got {t3_entry['weight']}")


def test_02_case_A_marginal_T1():
    """Case A: T1 n=10 (just above indicative threshold). Expect indicative
    (because n<20 reliable threshold), not reliable."""
    r = hybrid_valuation_v1(
        t1_values=[{"value_per_m2": 14000.0}] * 5,
        t1_n_total=10,
        t2_values=None,
        t3_values=None,
    )
    check("marginal T1 n=10 -> indicative",
          r["confidence"] == "indicative",
          detail=f"got {r['confidence']}")
    check("marginal T1 alone -> T1_weight=1.0",
          abs(r["tier_breakdown"][0]["weight"] - 1.0) < 0.001)


def test_03_case_A_T1_dominance_floor():
    """Case A: even with heavy T2 (n=20) and T3 (n=10), T1 must stay >=0.45.
    With T2 at full cap 0.40 and T3 at full cap 0.15, raw sum is 0.55 -> T1
    would be 0.45 (exactly the floor)."""
    r = hybrid_valuation_v1(
        t1_values=[{"value_per_m2": 14000.0}] * 5,
        t1_n_total=20,
        t2_values=[{"value_per_m2": 16000.0}] * 20,
        t3_values=[{"value_per_m2": 17000.0}] * 10,
    )
    t1_entry = next(t for t in r["tier_breakdown"] if t["tier"] == "T1")
    check("T1 dominance floor (>=0.45)",
          t1_entry["weight"] >= 0.45 - 0.001,
          detail=f"T1 weight = {t1_entry['weight']}")
    # weights still sum to ~1.0
    total = sum(t["weight"] for t in r["tier_breakdown"])
    check("tier weights sum to 1.0",
          abs(total - 1.0) < 0.01,
          detail=f"sum = {total}")


# ====================================================================
# Case B — T1 absent
# ====================================================================

def test_04_case_B_T2_only():
    """Case B: T1=None + T2 n=3. Expect indicative, T2_w=1.0, MUC required."""
    r = hybrid_valuation_v1(
        t1_values=None,
        t1_n_total=0,
        t2_values=[{"value_per_m2": 16000.0}] * 3,
        t3_values=None,
    )
    check("case B case label is 'B'", r.get("case") == "B")
    check("case B confidence ceiling is indicative",
          r["confidence"] == "indicative")
    check("case B muc_required True", r["muc_required"] is True)
    check("case B muc_range_pct = 0.20",
          r["muc_range_pct"] == HYBRID_TIER_CONFIG["muc_range_pct_when_T1_absent"])
    # H2 prediction: T2_weight reaches 0.85+ (in fact 1.0 when T3 absent)
    t2_entry = next(t for t in r["tier_breakdown"] if t["tier"] == "T2")
    check("H2: T2_weight >= 0.85 when T1 absent + T3 absent",
          t2_entry["weight"] >= 0.85,
          detail=f"T2_weight = {t2_entry['weight']}")
    # T2 discount applied: 16000 -> 14000
    check("T2 discount math (16000 * 0.875 = 14000)",
          abs(t2_entry["discounted_value"] - 14000.0) < 0.5,
          detail=f"discounted = {t2_entry['discounted_value']}")


def test_05_case_B_T2_and_T3():
    """Case B: T1=None + T2 n=5 + T3 n=2. T3 takes ~0.06, T2 takes ~0.94."""
    r = hybrid_valuation_v1(
        t1_values=None,
        t1_n_total=0,
        t2_values=[{"value_per_m2": 16000.0}] * 5,
        t3_values=[{"value_per_m2": 17000.0}] * 2,
    )
    check("case B with T3 still indicative", r["confidence"] == "indicative")
    t2_e = next(t for t in r["tier_breakdown"] if t["tier"] == "T2")
    t3_e = next(t for t in r["tier_breakdown"] if t["tier"] == "T3")
    check("case B T3 weight respects evidence ramp (n=2 -> 0.06)",
          abs(t3_e["weight"] - 0.06) < 0.001)
    check("case B T2 absorbs remainder (~0.94)",
          abs(t2_e["weight"] - 0.94) < 0.01,
          detail=f"T2={t2_e['weight']}")
    check("case B muc_required True", r["muc_required"] is True)


# ====================================================================
# Case C — T3 alone (Constraint 8)
# ====================================================================

def test_06_case_C_T3_alone_refused():
    """H4: Case C — T3 alone must refuse with Rule E3 Constraint 8 reason."""
    r = hybrid_valuation_v1(
        t1_values=None,
        t1_n_total=0,
        t2_values=None,
        t3_values=[{"value_per_m2": 17000.0}] * 2,
    )
    check("case C case label is 'C'", r.get("case") == "C")
    check("case C value is None", r["value_per_m2"] is None)
    check("case C confidence is fallback", r["confidence"] == "fallback")
    check("case C tier_breakdown empty", r["tier_breakdown"] == [])
    check("case C no MUC required (no valuation produced)",
          r["muc_required"] is False)
    # H4: explicit Rule E3 §8 citation in fallback_reason
    reason = r["fallback_reason"] or ""
    check("H4: fallback_reason cites Rule E3",
          "Rule E3" in reason,
          detail=f"reason = {reason!r}")
    check("H4: fallback_reason cites Constraint 8",
          "Constraint 8" in reason or "section 8" in reason or "§8" in reason,
          detail=f"reason = {reason!r}")


# ====================================================================
# Case D — all absent
# ====================================================================

def test_07_case_D_all_absent():
    r = hybrid_valuation_v1(None, 0, None, None)
    check("case D case label is 'D'", r.get("case") == "D")
    check("case D value is None", r["value_per_m2"] is None)
    check("case D confidence is fallback", r["confidence"] == "fallback")
    check("case D explains no data",
          "No tier data" in (r["fallback_reason"] or ""))


# ====================================================================
# Constraint 7 — unit normalization / sanity violations
# ====================================================================

def test_08_constraint_7_missing_value_per_m2_key():
    raised = False
    try:
        hybrid_valuation_v1(
            t1_values=[{"wrong_key": 14000.0}],
            t1_n_total=30,
            t2_values=None,
            t3_values=None,
        )
    except ValueError as e:
        raised = True
        check("constraint 7 error mentions 'value_per_m2'",
              "value_per_m2" in str(e))
    check("constraint 7 missing key raises ValueError", raised)


def test_09_constraint_7_negative_value():
    raised = False
    try:
        hybrid_valuation_v1(
            t1_values=[{"value_per_m2": -14000.0}],
            t1_n_total=30,
            t2_values=None,
            t3_values=None,
        )
    except ValueError as e:
        raised = True
        check("constraint 7 error mentions positive finite",
              "positive" in str(e) or "Constraint 7" in str(e))
    check("constraint 7 negative raises ValueError", raised)


def test_10_constraint_7_unit_mismatch_low():
    """Below sanity band (likely QAR/ft² mistake)."""
    raised = False
    try:
        hybrid_valuation_v1(
            t1_values=[{"value_per_m2": 50.0}],  # < 100 lower bound
            t1_n_total=30,
            t2_values=None,
            t3_values=None,
        )
    except ValueError as e:
        raised = True
        check("constraint 7 low-band error mentions sanity",
              "sanity" in str(e) or "unit" in str(e).lower())
    check("constraint 7 below-band raises ValueError", raised)


def test_11_constraint_7_unit_mismatch_high():
    """Above sanity band (likely whole-property QAR mistake)."""
    raised = False
    try:
        hybrid_valuation_v1(
            t1_values=[{"value_per_m2": 5_000_000.0}],  # > 100K upper bound
            t1_n_total=30,
            t2_values=None,
            t3_values=None,
        )
    except ValueError as e:
        raised = True
    check("constraint 7 above-band raises ValueError", raised)


def test_12_constraint_7_wrong_input_type():
    """tier_values is not a list (e.g. dict, str)."""
    raised = False
    try:
        hybrid_valuation_v1(
            t1_values={"value_per_m2": 14000.0},  # dict not list
            t1_n_total=30,
            t2_values=None,
            t3_values=None,
        )
    except ValueError as e:
        raised = True
    check("constraint 7 wrong-type raises ValueError", raised)


def test_13_constraint_7_negative_t1_n_total():
    raised = False
    try:
        hybrid_valuation_v1(None, t1_n_total=-1, t2_values=None, t3_values=None)
    except ValueError:
        raised = True
    check("constraint 7 negative t1_n_total raises", raised)


# ====================================================================
# Discount math + evidence-strength caps
# ====================================================================

def test_14_t2_discount_math():
    """Raw 16000 -> discounted 16000 * (1 - 0.125) = 14000."""
    r = hybrid_valuation_v1(
        None, 0,
        [{"value_per_m2": 16000.0}] * 3,
        None,
    )
    t2 = r["tier_breakdown"][0]
    check("T2 raw_value=16000", abs(t2["raw_value"] - 16000.0) < 0.5)
    check("T2 discounted_value = 16000 * 0.875 = 14000",
          abs(t2["discounted_value"] - 14000.0) < 0.5)
    check("T2 discount_applied = -0.125",
          t2["discount_applied"] == HYBRID_TIER_CONFIG["T2_discount_midpoint"])


def test_15_t3_discount_math():
    """Raw 20000 -> discounted 20000 * (1 - 0.175) = 16500.
    But Case C refuses T3 alone, so wrap with T2 present to actually
    exercise the discount path."""
    r = hybrid_valuation_v1(
        None, 0,
        [{"value_per_m2": 16000.0}] * 3,
        [{"value_per_m2": 20000.0}] * 3,
    )
    t3 = next(t for t in r["tier_breakdown"] if t["tier"] == "T3")
    check("T3 raw_value=20000", abs(t3["raw_value"] - 20000.0) < 0.5)
    check("T3 discounted_value = 20000 * 0.825 = 16500",
          abs(t3["discounted_value"] - 16500.0) < 0.5)
    check("T3 discount_applied = -0.175",
          t3["discount_applied"] == HYBRID_TIER_CONFIG["T3_discount_midpoint"])


def test_16_t2_evidence_strength_cap():
    """T2 n=100 (way above ramp threshold) -> weight should hit cap 0.40
    (when T1 is also present so Case A applies)."""
    r = hybrid_valuation_v1(
        [{"value_per_m2": 14000.0}] * 5, 20,
        [{"value_per_m2": 16000.0}] * 100,
        None,
    )
    t2 = next(t for t in r["tier_breakdown"] if t["tier"] == "T2")
    check("T2 weight caps at 0.40 (Case A)",
          abs(t2["weight"] - 0.40) < 0.001,
          detail=f"T2={t2['weight']}")


def test_17_t3_evidence_strength_cap():
    """T3 n=50 -> weight should hit cap 0.15."""
    r = hybrid_valuation_v1(
        [{"value_per_m2": 14000.0}] * 5, 20,
        [{"value_per_m2": 16000.0}] * 5,
        [{"value_per_m2": 17000.0}] * 50,
    )
    t3 = next(t for t in r["tier_breakdown"] if t["tier"] == "T3")
    check("T3 weight caps at 0.15",
          abs(t3["weight"] - 0.15) < 0.001,
          detail=f"T3={t3['weight']}")


# ====================================================================
# H2 — explicit BRIEF prediction
# ====================================================================

def test_18_h2_t2_weight_when_t3_absent():
    """BRIEF H2 (explicit): t1=None, t2=[X*3], t3=None
    -> indicative + muc_required True + T2_weight >= 0.85."""
    r = hybrid_valuation_v1(None, 0, [{"value_per_m2": 16000.0}] * 3, None)
    check("H2: confidence == indicative", r["confidence"] == "indicative")
    check("H2: muc_required True", r["muc_required"] is True)
    t2 = next(t for t in r["tier_breakdown"] if t["tier"] == "T2")
    check("H2: T2_weight reaches 0.85+ (got 1.0 when T3 absent)",
          t2["weight"] >= 0.85,
          detail=f"T2={t2['weight']}")


# ====================================================================
# H3 — explicit BRIEF prediction
# ====================================================================

def test_19_h3_t1_dominance_with_weak_t2():
    """BRIEF H3: strong T1 (n=30) + weak T2 (n=3) -> T1 weight >= 0.7."""
    r = hybrid_valuation_v1(
        [{"value_per_m2": 14000.0}] * 5, 30,
        [{"value_per_m2": 16000.0}] * 3,
        None,
    )
    t1 = next(t for t in r["tier_breakdown"] if t["tier"] == "T1")
    check("H3: T1 weight >= 0.7 with weak T2",
          t1["weight"] >= 0.7,
          detail=f"T1={t1['weight']}")
    check("H3: confidence reliable (T1 n>=20)",
          r["confidence"] == "reliable")


# ====================================================================
# H6 — Rule E3 text invariant
# ====================================================================

def test_20_h6_rule_e3_eight_constraints():
    """BRIEF H6: Empirical_Findings.md Rule E3 contains exactly 8 numbered
    constraints AND no occurrence of 'MUST NOT enter calculation'."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "Empirical_Findings.md",
    )
    with open(path, encoding="utf-8") as f:
        full = f.read()
    # Slice from Rule E3 heading to Rule E4 heading
    m = re.search(
        r"###\s*Rule\s+E3.*?(?=###\s*Rule\s+E4)",
        full,
        re.DOTALL,
    )
    check("H6: Rule E3 section locatable", m is not None)
    if m is None:
        return
    e3_text = m.group(0)
    # Count numbered constraints: lines starting with "1.", "2.", ..., "8."
    # The pattern is "N. **...**" per the BRIEF replacement text.
    numbered = re.findall(r"(?m)^(\d+)\.\s+\*\*", e3_text)
    check(f"H6: Rule E3 has exactly 8 numbered constraints (found {len(numbered)})",
          len(numbered) == 8,
          detail=f"numbers = {numbered}")
    # Check consecutive 1..8
    check("H6: numbered 1..8 in order",
          numbered == ["1", "2", "3", "4", "5", "6", "7", "8"],
          detail=f"got {numbered}")
    # Forbidden literal
    check("H6: 'MUST NOT enter calculation' literal absent",
          "MUST NOT enter calculation" not in e3_text)
    # Positive signals
    check("H6: section mentions hybrid_valuation_v1",
          "hybrid_valuation_v1" in e3_text)
    check("H6: section preserves E1 ban",
          "MoJ uplift" in e3_text)


# ====================================================================
# Other invariants
# ====================================================================

def test_21_tier_breakdown_only_includes_used_tiers():
    """Case A with all three tiers -> tier_breakdown has 3 entries.
    Case B with T2 only -> 1 entry. Case C/D -> 0 entries."""
    rA = hybrid_valuation_v1(
        [{"value_per_m2": 14000.0}] * 5, 30,
        [{"value_per_m2": 16000.0}] * 3,
        [{"value_per_m2": 17000.0}] * 2,
    )
    check("Case A breakdown has 3 entries", len(rA["tier_breakdown"]) == 3)
    rB = hybrid_valuation_v1(None, 0, [{"value_per_m2": 16000.0}] * 3, None)
    check("Case B (T2 only) breakdown has 1 entry",
          len(rB["tier_breakdown"]) == 1)


def test_22_rule_e3_compliance_field_always_set():
    cases = [
        hybrid_valuation_v1([{"value_per_m2": 14000.0}], 30, None, None),
        hybrid_valuation_v1(None, 0, [{"value_per_m2": 16000.0}], None),
        hybrid_valuation_v1(None, 0, None, [{"value_per_m2": 17000.0}]),
        hybrid_valuation_v1(None, 0, None, None),
    ]
    for i, r in enumerate(cases):
        check(f"case {i}: rule_e3_compliance == 'compliant'",
              r["rule_e3_compliance"] == "compliant")


# ====================================================================
# main
# ====================================================================

def main():
    print("=" * 72)
    print("Sprint 2.21.2 — Hybrid Valuation Foundation tests")
    print("=" * 72)

    tests = [
        test_01_case_A_strong_T1_T2_T3,
        test_02_case_A_marginal_T1,
        test_03_case_A_T1_dominance_floor,
        test_04_case_B_T2_only,
        test_05_case_B_T2_and_T3,
        test_06_case_C_T3_alone_refused,
        test_07_case_D_all_absent,
        test_08_constraint_7_missing_value_per_m2_key,
        test_09_constraint_7_negative_value,
        test_10_constraint_7_unit_mismatch_low,
        test_11_constraint_7_unit_mismatch_high,
        test_12_constraint_7_wrong_input_type,
        test_13_constraint_7_negative_t1_n_total,
        test_14_t2_discount_math,
        test_15_t3_discount_math,
        test_16_t2_evidence_strength_cap,
        test_17_t3_evidence_strength_cap,
        test_18_h2_t2_weight_when_t3_absent,
        test_19_h3_t1_dominance_with_weak_t2,
        test_20_h6_rule_e3_eight_constraints,
        test_21_tier_breakdown_only_includes_used_tiers,
        test_22_rule_e3_compliance_field_always_set,
    ]
    for fn in tests:
        print(f"\n-- {fn.__name__} --")
        try:
            fn()
        except Exception as e:
            global _failed
            _failed += 1
            print(f"  XX  {fn.__name__} raised {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n=== {_passed} passed / {_failed} failed ===")
    sys.exit(0 if _failed == 0 else 1)


if __name__ == "__main__":
    main()
