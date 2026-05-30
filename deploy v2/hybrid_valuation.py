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
  - RICS VPS 3 — like-for-like unit-of-comparison enforced by Constraint 7.

Author: Sprint 2.21.2 (Claude Code), 2026-05-24.
BRIEF: 2p21p2_pre/BRIEF_2p21p2.md (Anas-signed D1–D6).
"""

from __future__ import annotations

import logging
import statistics
from typing import Any, Optional

# Module-scoped logger. WARN-level for T3 row-level data integrity issues
# (unrecognised status, missing/non-positive value_per_m2_raw). Library
# convention — embedding apps configure handlers.
logger = logging.getLogger("hybrid_valuation")


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

    # T3 (developer-direct off-plan) — D4 + D6 amended Sprint 2.21.4
    # Status-aware discount map replaces the scalar T3_discount_midpoint.
    # Tier classification stays T3 in all status cases — tier reflects
    # source independence, not occupiability (BRIEF §2 D6).
    "T3_weight_cap": 0.15,
    "T3_status_discount_map": {
        "off_plan":           -0.175,              # ≈10% nego + ≈7.5% off-plan-to-resale (D6)
        "under_construction": -0.175,              # same — partial completion doesn't eliminate delivery risk
        "ready":              -0.100,              # negotiation component only; no off-plan-to-resale gap
    },
    "T3_discount_default": -0.175,                 # back-compat: legacy float/dict shapes use this scalar
    # Sprint 2.21.2 → 2.21.4 back-compat alias. Sprint 2.21.2 callers
    # (tests + downstream code) may read this key directly. Same value as
    # T3_discount_default by construction. Per Step 7 §7 — no caller
    # modification required.
    "T3_discount_midpoint": -0.175,
    "T3_discount_range": (-0.20, -0.15),
    "T3_evidence_strength_full_cap_at_n": 5,       # smaller — T3 is single-developer
    "T3_stale_evidence_multiplier": 0.5,           # D7: stale rows contribute half-weight to n_effective

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


def _process_t3_input(
    t3_values: Optional[list[Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Sprint 2.21.4 — shape-aware T3 input processor (replaces uniform discount path).

    Detects three input shapes and dispatches:

      1. **dict_new** (Sprint 2.21.4+): each entry has `status` and/or
         `value_per_m2_raw` keys. Per-row status-mapped discount via
         `T3_status_discount_map`. Per-row freshness via `freshness_status`
         field; `'stale'` rows contribute `T3_stale_evidence_multiplier`
         (0.5×) to `n_effective`. Emits per-row 7-field breakdown entries
         (D12 axis 18, Rule E10).

      2. **dict_legacy** (Sprint 2.21.2): each entry has `value_per_m2`
         only (no status/freshness). Uniform `T3_discount_default`,
         freshness assumed fresh. No per-row breakdown emitted —
         aggregate-only at the caller layer (back-compat).

      3. **float** (BRIEF §3.2 anticipated): bare numeric list.
         Uniform `T3_discount_default`, freshness assumed fresh.
         No per-row breakdown emitted.

    Detection rules (in order):
      - empty list / None → return empty result, shape='empty'.
      - first element is int/float (not bool) → shape='float'.
      - first element is dict → 'dict_new' if any of {'status',
        'value_per_m2_raw'} in keys, else 'dict_legacy'.
      - any other type → ValueError (Constraint 7).

    Per-row data-integrity recovery (Rule #39 deviation justification):
      - Missing/non-positive value_per_m2_raw → skip row + log WARN.
        Row count NOT decremented; n_effective excludes the skipped row.
      - Unrecognised status (not in T3_status_discount_map) → use
        T3_discount_default + log WARN. Row INCLUDED in n_effective.

    Returns dict:
      {
        "adjusted_values":  list[float],    # per-row discounted
        "raw_values":       list[float],    # per-row raw value_per_m2 (pre-discount)
        "n_count":          int,            # number of rows that survived validation
        "n_effective":      float,          # fresh=1.0, stale=0.5 sum
        "breakdown_rows":   list[dict],     # per-row 7-field shape; [] for legacy/float
        "shape":            str,            # 'dict_new'|'dict_legacy'|'float'|'empty'
        "applied_discounts": list[float],   # per-row discount that was applied
      }
    """
    empty_result = {
        "adjusted_values": [],
        "raw_values": [],
        "n_count": 0,
        "n_effective": 0.0,
        "breakdown_rows": [],
        "shape": "empty",
        "applied_discounts": [],
    }
    if t3_values is None:
        return empty_result
    if not isinstance(t3_values, list):
        raise ValueError(
            f"T3_values must be a list or None, got {type(t3_values).__name__}. "
            f"(Constraint 7)"
        )
    if not t3_values:
        return empty_result

    discount_default = config.get("T3_discount_default", -0.175)
    discount_map = config.get("T3_status_discount_map", {})
    stale_multiplier = config.get("T3_stale_evidence_multiplier", 0.5)
    sanity_lo = config["value_per_m2_sanity_min"]
    sanity_hi = config["value_per_m2_sanity_max"]

    first = t3_values[0]

    # ── Shape detection ──────────────────────────────────────────────
    if isinstance(first, bool):
        # Defensive: bool is a subtype of int in Python, exclude explicitly.
        raise ValueError(
            f"T3_values[0]={first!r} is bool; expected dict or float. (Constraint 7)"
        )
    if isinstance(first, (int, float)):
        shape = "float"
    elif isinstance(first, dict):
        has_new_marker = ("status" in first) or ("value_per_m2_raw" in first)
        shape = "dict_new" if has_new_marker else "dict_legacy"
    else:
        raise ValueError(
            f"T3_values[0] type {type(first).__name__} not supported; "
            f"expected dict or float. (Constraint 7)"
        )

    raw_values: list[float] = []
    adjusted_values: list[float] = []
    applied_discounts: list[float] = []
    n_effective: float = 0.0
    breakdown_rows: list[dict[str, Any]] = []

    for i, entry in enumerate(t3_values):
        # ── Shape consistency (no mid-list shape switches) ──
        if shape == "float":
            if isinstance(entry, bool) or not isinstance(entry, (int, float)):
                raise ValueError(
                    f"T3_values[{i}] shape switched mid-list "
                    f"(expected float, got {type(entry).__name__}). (Constraint 7)"
                )
        else:  # dict_new or dict_legacy
            if not isinstance(entry, dict):
                raise ValueError(
                    f"T3_values[{i}] shape switched mid-list "
                    f"(expected dict, got {type(entry).__name__}). (Constraint 7)"
                )

        # ── Extract raw value ──
        if shape == "float":
            v_raw: Optional[float] = float(entry)
        elif shape == "dict_new":
            # Prefer value_per_m2_raw; fall back to value_per_m2 for partial-shape rows
            v_candidate = entry.get("value_per_m2_raw")
            if v_candidate is None:
                v_candidate = entry.get("value_per_m2")
            v_raw = v_candidate
        else:  # dict_legacy
            v_raw = entry.get("value_per_m2")

        # ── Per-row data-integrity check (data issue → skip, not crash) ──
        if v_raw is None or isinstance(v_raw, bool) or not isinstance(v_raw, (int, float)):
            if shape != "float":   # float shape guarded by mid-list check above
                logger.warning(
                    "T3 row[%d] missing or non-numeric value_per_m2(_raw)=%r — "
                    "skipped (developer=%r, project=%r)",
                    i, v_raw,
                    entry.get("developer") if isinstance(entry, dict) else None,
                    entry.get("project") if isinstance(entry, dict) else None,
                )
                continue
        v_raw = float(v_raw)
        if v_raw <= 0:
            logger.warning(
                "T3 row[%d] non-positive value_per_m2(_raw)=%s — skipped "
                "(developer=%r, project=%r)",
                i, v_raw,
                entry.get("developer") if isinstance(entry, dict) else None,
                entry.get("project") if isinstance(entry, dict) else None,
            )
            continue

        # Sanity band (Constraint 7 — unit mismatch tripwire). Hard error
        # because a value 100× off is almost certainly a unit error, not
        # a one-row anomaly.
        if not (sanity_lo <= v_raw <= sanity_hi):
            raise ValueError(
                f"T3_values[{i}] value={v_raw} outside QAR/m² sanity band "
                f"[{sanity_lo}, {sanity_hi}]. Likely a unit mismatch. (Constraint 7)"
            )

        # ── Determine per-row discount ──
        status_val: Optional[str] = None
        if shape == "dict_new" and "status" in entry:
            status_val = entry.get("status")
            if status_val in discount_map:
                discount = discount_map[status_val]
            else:
                logger.warning(
                    "T3 row[%d] unrecognised status=%r — using T3_discount_default "
                    "(developer=%r, project=%r)",
                    i, status_val, entry.get("developer"), entry.get("project"),
                )
                discount = discount_default
        else:
            discount = discount_default

        v_adj = v_raw * (1.0 + discount)

        # ── Determine per-row freshness (only meaningful for dict_new) ──
        if shape == "dict_new":
            freshness_raw = entry.get("freshness_status", "fresh")
            if freshness_raw == "stale":
                row_n_weight = stale_multiplier
                freshness = "stale"
            else:
                row_n_weight = 1.0
                freshness = "fresh"   # normalise unrecognised values to fresh
        else:
            row_n_weight = 1.0
            freshness = "fresh"

        # ── Accumulate ──
        raw_values.append(v_raw)
        adjusted_values.append(v_adj)
        applied_discounts.append(discount)
        n_effective += row_n_weight

        # Per-row breakdown only for new shape (Rule E10 transparency, D12 axis 18)
        if shape == "dict_new":
            breakdown_rows.append({
                "developer": entry.get("developer", "") or "",
                "project": entry.get("project", "") or "",
                "status": status_val if status_val in discount_map else (status_val or "unknown"),
                "value_per_m2_raw": round(v_raw, 2),
                "discount_applied": discount,
                "value_per_m2_adjusted": round(v_adj, 2),
                "freshness_status": freshness,
            })

    return {
        "adjusted_values": adjusted_values,
        "raw_values": raw_values,
        "n_count": len(raw_values),
        "n_effective": n_effective,
        "breakdown_rows": breakdown_rows,
        "shape": shape,
        "applied_discounts": applied_discounts,
    }


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
    t3_n: float,
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

    Sprint 2.21.4: `t3_n` accepts float (effective n with stale-row 0.5×
    multiplier per D7). int still works via Python numeric promotion.
    `t3_present = t3_n > 0` still semantically correct on float.
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

    # T3 uses shape-aware processor (Sprint 2.21.4) — handles dict_new
    # (status + freshness + per-row breakdown), dict_legacy (Sprint 2.21.2,
    # value_per_m2-only), and float (BRIEF §3.2 anticipated). Per-row
    # status discount + stale freshness 0.5× evidence multiplier.
    t3_proc = _process_t3_input(t3_values, config)
    t3_vals = t3_proc["raw_values"]
    t3_adjusted = t3_proc["adjusted_values"]
    t3_n = t3_proc["n_count"]
    t3_n_effective = t3_proc["n_effective"]
    t3_shape = t3_proc["shape"]
    t3_breakdown_rows = t3_proc["breakdown_rows"]
    t3_applied_discounts = t3_proc["applied_discounts"]

    # t1_n_total is authoritative for "T1 dominance" logic per BRIEF §4
    # (caller knows the true T1 sample size; values list may be a digest).
    if not isinstance(t1_n_total, int) or t1_n_total < 0:
        raise ValueError(
            f"t1_n_total must be a non-negative int; got {t1_n_total!r}. "
            f"(Constraint 7 sample-size contract)"
        )

    # --- Step 2-6: route to a case + compute weights ---
    # Use t3_n_effective (float; fresh=1.0 + stale=0.5 per D7) for the
    # evidence-strength ramp so stale rows under-contribute to T3 weight.
    # Presence check `t3_n_effective > 0` still works on float.
    t1_w, t2_w, t3_w, case = _apply_tier_caps(
        t1_n_total, t2_n, t3_n_effective, config,
    )

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

    # --- Step 7: apply discounts to T2 / T3 raw values ---
    # T2: uniform discount (unchanged from Sprint 2.21.2).
    t2_disc = config["T2_discount_midpoint"]
    t2_discounted = [v * (1.0 + t2_disc) for v in t2_vals]
    # T3: per-row discount already applied by `_process_t3_input` (Sprint
    # 2.21.4 D6 — status-aware map). `t3_adjusted` is the post-discount
    # list; `t3_vals` is the raw pre-discount list for breakdown
    # transparency. Aggregate representative discount = median of the
    # per-row discounts actually applied (matches the median row's status).
    t3_disc_aggregate: Optional[float] = (
        statistics.median(t3_applied_discounts) if t3_applied_discounts else None
    )

    # --- Step 8: per-tier representative value (median) + weighted average ---
    t1_median = statistics.median(t1_vals) if t1_vals else None
    t2_raw_median = statistics.median(t2_vals) if t2_vals else None
    t2_disc_median = statistics.median(t2_discounted) if t2_discounted else None
    t3_raw_median = statistics.median(t3_vals) if t3_vals else None
    t3_disc_median = statistics.median(t3_adjusted) if t3_adjusted else None

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
        # Sprint 2.21.4: tier_breakdown T3 entry carries the aggregate
        # row (back-compat with 2.21.3 consumers reading {tier, weight,
        # raw_value, discounted_value, discount_applied, n}) PLUS a
        # `sources` array of per-row 7-field entries (D12 axis 18 +
        # Rule E10 transparency). `sources=[]` for legacy / float input
        # shapes; the aggregate fields fully describe those uniform-
        # discount cases.
        t3_entry: dict[str, Any] = {
            "tier": "T3",
            "weight": round(t3_w, 4),
            "raw_value": round(t3_raw_median, 2),
            "discounted_value": round(t3_disc_median, 2),
            "discount_applied": (
                round(t3_disc_aggregate, 4) if t3_disc_aggregate is not None else None
            ),
            "n": t3_n,
            "n_effective": round(t3_n_effective, 4),
            "shape": t3_shape,
            "sources": t3_breakdown_rows,
        }
        tier_breakdown.append(t3_entry)

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
