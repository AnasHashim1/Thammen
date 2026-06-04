# BRIEF — R15 §5 audit: stock_strata not a18-aware (land-median divergence)
Status: Phase-0 audit (no edit, no deploy). Fix + Gate-1 deferred until results.
Why now: B-1 surfaced the land floor to users; the land-median behind it must be sound.

## Hypothesis (CC's flag, to verify)
`stock_strata` computes its land-median WITHOUT the a18 sibling-area aggregation the rest of
the engine uses → ~7% divergence in affected areas. Verify magnitude, DIRECTION (does it
under- or over-count by dropping siblings?), and blast radius.

## Audit steps
1. Pick 3-5 real properties in areas WITH sibling-name variants (start with the a18/A16
   Marikh امريخ↔مريخ case; add 2-3 more zones that have sub-zone or alias siblings per GIS).
2. For each, compute the land-median TWO ways: (a) current stock_strata path, (b) a18-aware
   sibling-aggregated pool. Record both + the delta% and sign.
3. Trace consumers: does stock_strata's land-median feed value_floor.land_floor, the strata
   CLASSIFICATION (land_priced/aging/modern/luxury_new, Rule E4), the headline, or only a
   label? This sets the blast radius.
4. grep index.html for any rendered stock_strata field (desktop + 390×844).
5. Quantify scope via GIS: how many zones/areas have sibling variants where this bites.

## Deliverable
Numbers (per-prop delta + sign), the consumer map, the scope count, and a go/no-go +
proposed surgical fix (most likely: route stock_strata through the same a18 aggregation).
If the fix changes any headline → Gate-1 (consent + tests + CHANGELOG + smoke), NOT
value-invariant. Anchors to re-smoke: 56/565/21, 54/541/6, 55/296/13, 56/647/6.

---
*Authored by Anas (Claude.ai lane), 2026-06-04. Audit results → `docs/PHASE0_R15_stock_strata_a18.md`.*
