"""
Lever-2 what-if SIMULATION (Sprint B-2 prep, INTERIM) — READ-ONLY.

Part of ③. Computes what the proposed Sprint B-2 **Lever 2** (the DOWN re-anchor for
OLD non-luxury stock toward the a21 land floor) WOULD produce for a given engine output.

It SHIPS NOTHING. No engine change, no value change. It exists to de-risk Lever 2 so it is
shovel-ready the moment a few old-stock confirmed sales land. The numbers are PROVISIONAL
(n<20) — bands, not point claims.

Mechanism (from docs/BRIEF_SprintB2_mechanism_elicitation_SIGNED.md §A + §2 LEVER 2):
  - Fork#1 = MODERATE: re-anchor an over-anchored OLD (age>10) NON-luxury villa DOWN toward
    the land floor + a 0-10% band. Reuse the a21 land floor (valuation.value_floor.land_floor).
  - Luxury-finish EXCEPTION: OLD but luxury-finish retains ~20% building value -> floor + ~20%
    (NOT all the way to floor).
  - Fires only when the headline EXCEEDS the upper band (else it is already at/below floor+band).
  - Grounds: Qatar 10-Year Rule + HBU under VPS 2 / IVS 102.

This is the un-implemented INTENT on the comparison path today (PHASE0_B2_condition_recon.md §3:
age_mult=0 only zeroes a size uplift; it never pulls down). Lever 1 (the UP finish/new-build
premium) is NOT simulated here — it is corpus-gated (luxury_new MoJ stratum is n=0 locally;
must be calibrated cross-area from n>=20 GT-2), so there is nothing reliable to simulate yet.
"""

# MODERATE band + luxury exception (Fork#1, signed). Provisional until n>=20 GT-2.
DEFAULT_BAND_LO = 0.00
DEFAULT_BAND_HI = 0.10
DEFAULT_LUXURY_PREMIUM = 0.20
AGE_THRESHOLD = 10  # Qatar 10-Year Rule


def simulate_lever2_reanchor(
    headline_amount,
    land_floor,
    building_age_years,
    is_luxury_finish,
    band_lo=DEFAULT_BAND_LO,
    band_hi=DEFAULT_BAND_HI,
    luxury_premium=DEFAULT_LUXURY_PREMIUM,
    age_threshold=AGE_THRESHOLD,
):
    """
    Return a dict describing the simulated Lever-2 re-anchor (no side effects):

      {applies, rule, reanchored_low, reanchored_point, reanchored_high,
       delta_point_pct, reason}

    `applies=False` carries a `reason` (gate not met / floor missing / already at floor).
    All re-anchored figures are PROVISIONAL.
    """
    out = {
        "applies": False, "rule": None,
        "reanchored_low": None, "reanchored_point": None, "reanchored_high": None,
        "delta_point_pct": None, "reason": None,
    }

    if headline_amount is None or land_floor is None or land_floor <= 0:
        out["reason"] = "no headline or no reliable land floor (Lever-2 dependency absent)"
        return out
    if building_age_years is None:
        out["reason"] = "building_age unknown (Lever-2 gates on age>threshold)"
        return out
    if building_age_years <= age_threshold:
        out["reason"] = f"not old (age {building_age_years} <= {age_threshold}) — Lever-2 does not fire"
        return out

    if is_luxury_finish:
        # Luxury-finish exception: retain ~20% building value over the land floor.
        rule = "luxury_finish_exception"
        point = land_floor * (1 + luxury_premium)
        low = high = point
    else:
        # MODERATE band: floor + 0..10%.
        rule = "moderate_band"
        low = land_floor * (1 + band_lo)
        high = land_floor * (1 + band_hi)
        point = land_floor * (1 + (band_lo + band_hi) / 2.0)

    # Fire only if the headline sits ABOVE the band's upper edge (i.e. it is over-anchored
    # relative to the land floor); otherwise it is already at/below the re-anchor target.
    if headline_amount <= high:
        out["reason"] = ("headline already within/below floor+band "
                         f"(headline {headline_amount:.0f} <= upper {high:.0f}) — no re-anchor")
        out["rule"] = rule
        out["reanchored_low"] = round(low)
        out["reanchored_point"] = round(point)
        out["reanchored_high"] = round(high)
        return out

    out.update({
        "applies": True,
        "rule": rule,
        "reanchored_low": round(low),
        "reanchored_point": round(point),
        "reanchored_high": round(high),
        "delta_point_pct": round((point - headline_amount) / headline_amount * 100, 1),
        "reason": "OK",
    })
    return out


if __name__ == "__main__":
    # V001 (real seed): old 25y, luxury finish, floor 2,456,736, headline 3.8M -> ~2.95M
    demo = simulate_lever2_reanchor(3_800_000, 2_456_736, 25, True)
    print("V001 luxury-exception:", demo["rule"], "->",
          demo["reanchored_point"], f"({demo['delta_point_pct']}%)")
    # synthetic old non-luxury over-anchor
    demo2 = simulate_lever2_reanchor(2_600_000, 1_800_000, 20, False)
    print("old non-luxury moderate band:", demo2["reanchored_low"], "-",
          demo2["reanchored_high"], "pt", demo2["reanchored_point"], f"({demo2['delta_point_pct']}%)")
    # not old -> no fire
    print("new (age 2):", simulate_lever2_reanchor(2_500_000, 1_700_000, 2, True)["reason"])
