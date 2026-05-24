"""
hybrid_valuation.py — Sprint 2.21.2 — Hybrid Valuation Foundation

Tier-weighted multi-source valuation aggregator.

This module exposes the `hybrid_valuation_v1()` function and its
configuration object `HYBRID_TIER_CONFIG`. It does NOT integrate with any
production source — connectors land in Sprint 2.21.3 (arady_apartments_t2,
propertyfinder_rents_t2) and Sprint 2.21.4 (developer_inventory_t3). This
Sprint ships the foundation only: the function exists, is tested, and is
imported nowhere from `evaluate_unified.py`. Behaviour on thammen.qa is
identical to v101 until 2.21.3 wires the first call site.

Governing rules:
  - Rule E3 (updated 2026-05-24, Sprint 2.21.2) — 8 constraints.
    See docs/Empirical_Findings.md §2 Rule E3.
  - Rule E1 (unchanged) — no MoJ uplift. T1 values are NOT inflated by
    asking-tier evidence; they enter the weighted average at their own
    measured median.
  - RICS VPS 4 — like-for-like unit-of-comparison enforced by Constraint 7.

Author: Sprint 2.21.2 (Claude Code), 2026-05-24.
BRIEF: 2p21p2_pre/BRIEF_2p21p2.md (Anas-signed D1–D6).
"""

from __future__ import annotations

import statistics
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Configuration object (provisional — see BRIEF D5/D6 derivation in CHANGELOG_v47.md)
# ---------------------------------------------------------------------------

HYBRID_TIER_CONFIG: dict[str, Any] = {
    # T1 (MoJ + Confirmed Sales) — dominance constraint
    "T1_weight_floor_when_present": 0.45,
    "T1_n_threshold_for_reliable": 20,
    "T1_n_threshold_for_indicative": 10,

    # T2 (arady, PropertyFinder, broker listings) — D3 + D5
    "T2_weight_cap_with_T1": 0.40,
    "T2_discount_midpoint": -0.125,                # D5: midpoint of [-0.15, -0.10]
    "T2_discount_range": (-0.15, -0.10),           # for future per-broker override
    "T2_evidence_strength_full_cap_at_n": 10,      # linear ramp from n=0 to n=10

    # T3 (developer-direct off-plan) — D4 + D6
    "T3_weight_cap": 0.15,
    "T3_discount_midpoint": -0.175,                # D6: midpoint of [-0.20, -0.15]
    "T3_discount_range": (-0.20, -0.15),
    "T3_evidence_strength_full_cap_at_n": 5,       # smaller — T3 is single-developer

    # MUC when T1 absent (Constraint 5)
    "muc_range_pct_when_T1_absent": 0.20,

    # Contract-7 sanity bounds for value_per_m2 (Qatar real estate, QAR/m²)
    # These are unit-consistency *signal* checks, not market-band checks.
    # A value far outside this range almost certainly indicates a wrong unit
    # (QAR/ft², or whole-property QAR rather than per-m²).
    "value_per_m2_sanity_min": 100.0,
    "value_per_m2_sanity_max": 100_000.0,

    # Provenance tags for transparency / future recalibration
    "calibration_status": "provisional_broker_experience_grounded",
    "calibration_basis": "EMPIRICAL_FINDINGS §3 asking premium ranges + broker experience (D5/D6)",
    "recalibration_trigger": "Confirmed Sales pipeline produces >=30 (asking, close) pairs",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_tier_input(
    tier_values: Optional[list[dict[str, Any]]],
    tier_label: str,
    config: dict[str, Any],
) -> tuple[list[float], int]:
    """Validate Constraint 7 (unit normalization) and return (values, n).

    Returns ([], 0) when the input is None or [] — these are valid "tier
    absent" signals, not errors.

    Raises ValueError when:
      - input is not a list of dicts
      - a dict lacks the `value_per_m2` key
      - a value is not a positive finite number
      - a value falls outside the sanity band (likely a unit mismatch)

    Note: the function trusts that callers have already normalized for size
    bracket / area before calling. Constraint 7 cannot fully verify like-for-
    like beyond the unit dimension — the sanity band is a tripwire for the
    "wrong unit entirely" case (QAR/ft², or whole-property QAR).
    """
    if tier_values is None:
        return [], 0
    if not isinstance(tier_values, list):
        raise ValueError(
            f"{tier_label}_values must be a list[dict] or None, "
            f"got {type(tier_values).__name__}. (Constraint 7)"
        )

    out: list[float] = []
    for i, entry in enumerate(tier_values):
        if not isinstance(entry, dict):
            raise ValueError(
                f"{tier_label}_values[{i}] is not a dict; "
                f"got {type(entry).__name__}. (Constraint 7)"
            )
        if "value_per_m2" not in entry:
            raise ValueError(
                f"{tier_label}_values[{i}] missing 'value_per_m2' key. "
                f"(Constraint 7 — like-for-like normalization)"
            )
        v = entry["value_per_m2"]
        if not isinstance(v, (int, float)):
            raise ValueError(
                f"{tier_label}_values[{i}]['value_per_m2'] = {v!r} "
                f"is not a number. (Constraint 7)"
            )
        v = float(v)
        if not (v > 0 and v < float("inf")):
            raise ValueError(
                f"{tier_label}_values[{i}]['value_per_m2'] = {v} "
                f"is not a positive finite number. (Constraint 7)"
            )
        lo = config["value_per_m2_sanity_min"]
        hi = config["value_per_m2_sanity_max"]
        if not (lo <= v <= hi):
            raise ValueError(
                f"{tier_label}_values[{i}]['value_per_m2'] = {v} "
                f"falls outside QAR/m² sanity band [{lo}, {hi}]. "
                f"Likely a unit mismatch (QAR/ft² or whole-property QAR). "
                f"(Constraint 7)"
            )
        out.append(v)
    return out, len(out)


def _evidence_strength(n: int, cap: float, full_cap_at_n: int) -> float:
    """Linear ramp: weight grows from 0 at n=0 toward `cap` as n approaches
    `full_cap_at_n`. Stays at `cap` for n >= full_cap_at_n.

    Documented choice (Rule #39 deviation justification): BRIEF §4 algorithm
    step 3 uses `evidence_strength(n)` without defining its shape. A linear
    ramp is the simplest defensible choice — it's continuous, monotonic,
    bounded, and makes the cap reachable with realistic sample sizes
    (T2 full at n=10, T3 full at n=5 per HYBRID_TIER_CONFIG defaults).

    Alternative considered: log curve (slower ramp). Rejected because it
    keeps weights low for moderate n in a way that doesn't match how brokers
    treat evidence — 10 listings DO inform meaningfully, log(10) = 2.3
    underweights them. Linear is more honest given current calibration
    state. Can be replaced with a smarter curve in a future Sprint once
    Confirmed Sales data lets us measure the actual marginal-value curve.
    """
    if n <= 0:
        return 0.0
    if n >= full_cap_at_n:
        return cap
    return cap * (n / full_cap_at_n)


def _apply_tier_caps(
    t1_n: int,
    t2_n: int,
    t3_n: int,
    config: dict[str, Any],
) -> tuple[float, float, float, str]:
    """Compute per-tier weights and route to one of Cases A/B/C/D.

    Returns (t1_weight, t2_weight, t3_weight, case_label).
    case_label ∈ {"A", "B", "C", "D"} — one of BRIEF §4 algorithm cases.

    Implements:
      - Constraint 3 (T1 dominance, floor 0.45)
      - Constraint 4 enforcement via case_label (caller maps "B" → indicative)
      - Constraint 8 enforcement via case "C" returning (0, 0, 0, "C")
      - D3 (T2 cap 0.40 with T1)
      - D4 (T3 cap 0.15 always)
    """
    t1_present = t1_n >= config["T1_n_threshold_for_indicative"]
    t2_present = t2_n > 0
    t3_present = t3_n > 0

    if t1_present:
        # Case A — T1 dominates
        t2_w = _evidence_strength(
            t2_n,
            cap=config["T2_weight_cap_with_T1"],
            full_cap_at_n=config["T2_evidence_strength_full_cap_at_n"],
        )
        t3_w = _evidence_strength(
            t3_n,
            cap=config["T3_weight_cap"],
            full_cap_at_n=config["T3_evidence_strength_full_cap_at_n"],
        )
        # T1 absorbs the remainder, but never below floor
        t1_w = max(
            config["T1_weight_floor_when_present"],
            1.0 - t2_w - t3_w,
        )
        # If the floor binds, t2_w + t3_w + t1_w may exceed 1.0; rescale
        total = t1_w + t2_w + t3_w
        if total > 1.0:
            t1_w /= total
            t2_w /= total
            t3_w /= total
        return t1_w, t2_w, t3_w, "A"

    if t2_present:
        # Case B — T1 absent, T2 present (T3 optional)
        t3_w = _evidence_strength(
            t3_n,
            cap=config["T3_weight_cap"],
            full_cap_at_n=config["T3_evidence_strength_full_cap_at_n"],
        )
        t2_w = 1.0 - t3_w  # absorbs the remainder; can reach 0.85+ when T3 absent
        return 0.0, t2_w, t3_w, "B"

    if t3_present:
        # Case C — T3 alone refused (Constraint 8)
        return 0.0, 0.0, 0.0, "C"

    # Case D — everything absent
    return 0.0, 0.0, 0.0, "D"


def _normalize_t1_absent_case(
    t1_n: int,
    t2_present: bool,
    t3_present: bool,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Edge-case helper for the T1-absent branches. Returns a partial
    output dict with MUC fields already populated when T1 is absent and
    at least one alternative tier is present. Returns {} otherwise.
    """
    t1_absent = t1_n < config["T1_n_threshold_for_indicative"]
    if t1_absent and (t2_present or t3_present):
        return {
            "muc_required": True,
            "muc_range_pct": config["muc_range_pct_when_T1_absent"],
        }
    return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hybrid_valuation_v1(
    t1_values: Optional[list[dict[str, Any]]],
    t1_n_total: int,
    t2_values: Optional[list[dict[str, Any]]],
    t3_values: Optional[list[dict[str, Any]]],
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Tier-weighted hybrid valuation.

    Inputs are pre-normalized lists of {"value_per_m2": float, ...} dicts
    (typically from AdjustmentGrid for T1; raw asking for T2/T3 — the
    function applies the configured discount internally for T2/T3).

    `t1_n_total` is the size of the underlying T1 sample (BRIEF §4 uses
    this for confidence thresholds, not necessarily equal to
    `len(t1_values)` because the caller may have downsampled).

    Returns a dict in the BRIEF §4 output shape.

    Raises ValueError on Constraint 7 violations (mixed units / wrong key /
    non-positive / out-of-band values). Never raises on missing tiers —
    those go through Case B/C/D.

    See:
      docs/Empirical_Findings.md §2 Rule E3 (8 constraints)
      2p21p2_pre/BRIEF_2p21p2.md §4 (function spec)
    """
    if config is None:
        config = HYBRID_TIER_CONFIG

    # --- Step 1: validate inputs (Constraint 7) ---
    t1_vals, _t1_n_normalized = _normalize_tier_input(t1_values, "T1", config)
    t2_vals, t2_n = _normalize_tier_input(t2_values, "T2", config)
    t3_vals, t3_n = _normalize_tier_input(t3_values, "T3", config)

    # t1_n_total is authoritative for "T1 dominance" logic per BRIEF §4
    # (caller knows the true T1 sample size; values list may be a digest).
    if not isinstance(t1_n_total, int) or t1_n_total < 0:
        raise ValueError(
            f"t1_n_total must be a non-negative int; got {t1_n_total!r}. "
            f"(Constraint 7 sample-size contract)"
        )

    # --- Step 2-6: route to a case + compute weights ---
    t1_w, t2_w, t3_w, case = _apply_tier_caps(t1_n_total, t2_n, t3_n, config)

    # --- Case C — T3 alone refused (Constraint 8) ---
    if case == "C":
        return {
            "value_per_m2": None,
            "confidence": "fallback",
            "tier_breakdown": [],
            "muc_required": False,
            "muc_range_pct": None,
            "fallback_reason": "T3 alone insufficient (Rule E3 Constraint 8)",
            "rule_e3_compliance": "compliant",
            "case": case,
        }

    # --- Case D — all absent ---
    if case == "D":
        return {
            "value_per_m2": None,
            "confidence": "fallback",
            "tier_breakdown": [],
            "muc_required": False,
            "muc_range_pct": None,
            "fallback_reason": "No tier data provided",
            "rule_e3_compliance": "compliant",
            "case": case,
        }

    # --- Step 7: apply discounts to T2/T3 raw values ---
    t2_disc = config["T2_discount_midpoint"]
    t3_disc = config["T3_discount_midpoint"]
    t2_discounted = [v * (1.0 + t2_disc) for v in t2_vals]
    t3_discounted = [v * (1.0 + t3_disc) for v in t3_vals]

    # --- Step 8: per-tier representative value (median) + weighted average ---
    t1_median = statistics.median(t1_vals) if t1_vals else None
    t2_raw_median = statistics.median(t2_vals) if t2_vals else None
    t2_disc_median = statistics.median(t2_discounted) if t2_discounted else None
    t3_raw_median = statistics.median(t3_vals) if t3_vals else None
    t3_disc_median = statistics.median(t3_discounted) if t3_discounted else None

    # weighted sum of contributing tiers' (discounted, where applicable) medians
    contributions = []
    if t1_w > 0 and t1_median is not None:
        contributions.append((t1_w, t1_median))
    if t2_w > 0 and t2_disc_median is not None:
        contributions.append((t2_w, t2_disc_median))
    if t3_w > 0 and t3_disc_median is not None:
        contributions.append((t3_w, t3_disc_median))

    if not contributions:
        # Defensive: should not happen given the case routing, but guard anyway.
        return {
            "value_per_m2": None,
            "confidence": "fallback",
            "tier_breakdown": [],
            "muc_required": False,
            "muc_range_pct": None,
            "fallback_reason": "No contributing tier values after normalization",
            "rule_e3_compliance": "compliant",
            "case": case,
        }

    weight_sum = sum(w for w, _ in contributions)
    weighted_value = sum(w * v for w, v in contributions) / weight_sum

    # --- Step 9: emit tier_breakdown (Constraint 6 transparency) ---
    tier_breakdown: list[dict[str, Any]] = []
    if t1_vals:
        tier_breakdown.append({
            "tier": "T1",
            "weight": round(t1_w, 4),
            "value_per_m2": round(t1_median, 2),
            "n": t1_n_total,
            "n_values_used": len(t1_vals),
        })
    if t2_vals:
        tier_breakdown.append({
            "tier": "T2",
            "weight": round(t2_w, 4),
            "raw_value": round(t2_raw_median, 2),
            "discounted_value": round(t2_disc_median, 2),
            "discount_applied": t2_disc,
            "n": t2_n,
        })
    if t3_vals:
        tier_breakdown.append({
            "tier": "T3",
            "weight": round(t3_w, 4),
            "raw_value": round(t3_raw_median, 2),
            "discounted_value": round(t3_disc_median, 2),
            "discount_applied": t3_disc,
            "n": t3_n,
        })

    # --- Confidence ---
    if case == "A":
        # T1 present + n>=10 threshold; reliable if n>=20
        if t1_n_total >= config["T1_n_threshold_for_reliable"]:
            confidence = "reliable"
        else:
            confidence = "indicative"
    else:  # case "B" — T1 absent (or below indicative threshold), T2 present
        # Constraint 4 ceiling: cannot exceed indicative
        confidence = "indicative"

    # --- MUC fields (Constraint 5) ---
    muc_extras = _normalize_t1_absent_case(t1_n_total, bool(t2_n), bool(t3_n), config)
    muc_required = muc_extras.get("muc_required", False)
    muc_range_pct = muc_extras.get("muc_range_pct", None)

    return {
        "value_per_m2": round(weighted_value, 2),
        "confidence": confidence,
        "tier_breakdown": tier_breakdown,
        "muc_required": muc_required,
        "muc_range_pct": muc_range_pct,
        "fallback_reason": None,
        "rule_e3_compliance": "compliant",
        "case": case,
    }


# ---------------------------------------------------------------------------
# Module-level dunder for callers
# ---------------------------------------------------------------------------

__all__ = [
    "hybrid_valuation_v1",
    "HYBRID_TIER_CONFIG",
]
