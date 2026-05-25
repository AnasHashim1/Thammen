# Field-Level Confidence Feasibility Map — Sprint 2.22.0 BRIEF v2 §4.2

**Audit date:** 2026-05-25 evening
**Production baseline:** `thammen-sprint2p21p4-t3-aryan-lusail` (Heroku v127)
**Method:** static code inspection of `evaluate_unified.py`, `api.py`, `qatar_gis.py`, `property_factors.py`, `building_age_cache.py` + cross-reference with response JSONs from `latency_profile_2p22p0_v2.json`.

For each of the 7 candidate Stage 2 fields (D-stage2-1):

| # | Field | Current data source | Confidence baseline today | Currently exposed in `/api/evaluate`? | Stage 2 question feasibility |
|---|---|---|---|---|---|
| 1 | **Floor number** (apt/tower) | NONE. Z/S/B identifies the *building*, not the unit. No floor input wired. | **0 (zero)** — engine has no signal. | NO — neither input nor output. | **HIGH.** Add `floor: Optional[int]` to `EvaluateDetailsRequest` (Pydantic, `extra='forbid'` already enforced — Bug A2 / #31). Bounded multiplier per floor band (e.g., 0–3, 4–7, 8–12, 13+) consistent with Pearl/Lusail premium-floor convention. Cap at ±5% per D-stage2-1 spec. |
| 2 | **Interior condition** | EXISTS as `condition: Optional[str]` in `EvaluateDetailsRequest` (`'new'\|'good'\|'maintenance'\|'renovated'`) — see [api.py:316](api.py:316). Mapped to `(major_renovation, structural_change)` via `CONDITION_TO_RENOVATION` ([api.py:353](api.py:353)). | **0 (zero)** when unset; AVM has no visual signal. **User-supplied** is the only path. | INPUT yes, but rendering as Stage 2 question would require new "I don't know" handling (currently the schema treats missing as null). | **HIGHEST.** Already wired into `EvaluateDetailsRequest`. Stage 2 Q&A would prompt "How is the interior condition?" with 4 bounded options + "I don't know" (D-stage2-3 widens MUC). No backend change beyond rendering UX. |
| 3 | **Recent renovations (last 3 years)** | DERIVED from `condition='renovated'` (overlap with field #2). Boolean `(major_renovation, structural_change)` returned by `CONDITION_TO_RENOVATION` map. No standalone field. | **0 (zero)** independent of condition. | NO independent surface. Conflated with #2. | **MEDIUM.** Either (a) collapse with field #2 into one question ("Is the interior recently renovated?"); or (b) add `renovated_within_3yr: Optional[bool]`. Recommend (a) — fewer questions, less cognitive load (cf. D-stage2-6 = 3 questions/screen max). |
| 4 | **Primary view** (sea / golf / city / interior) | NONE. `LANDMARK_WEIGHTS` ([property_factors.py:54](property_factors.py:54)) captures *proximity* to mosques/schools/malls/hospitals — NOT view orientation. `aspect_ratio` field in `GeometricFactors` ([qatar_gis.py:173](qatar_gis.py:173)) is plot shape, not orientation. | **~0.0** — engine has zero view signal. GIS provides plot centroid + neighbors, but inferring "facing X" from a polygon is non-trivial (would need wall orientation analysis + landmark direction vector). | NO — neither input nor output. | **MEDIUM-LOW.** As a Stage 2 question: trivial to ask, hard to validate. AVM cannot fact-check user's "sea view" claim from GIS alone. D-stage2-5 ("accept claim, record as unverified") handles this gracefully. Bounded multiplier (e.g., sea view = +5%, golf = +3%, interior = 0%) within ±5% cap. **BRIEF default 0.3 confidence is OPTIMISTIC for the AVM side — empirical baseline is 0.0.** |
| 5 | **Building age (GIS ±N years)** | EXISTS — `qatar_gis.smart_estimate_construction_year` reads `building_age_cache.sqlite` (Sprint 2.15.1 cache, 62 PINs prefilled) or falls back to imagery analysis (CACHE-ONLY mode in production). Returns `(earliest_built_year, latest_vacant_year, confidence_years)`. Surfaced as `building_age_years` + `age_source` ∈ {`'user'`, `'gis_imagery'`, `'unknown'`} + `age_confidence_years` at [evaluate_unified.py:3106](evaluate_unified.py:3106). | **HIGH when cached, MEDIUM when imagery hits, ZERO when neither.** The `age_confidence_years` field IS a per-field confidence signal (±3y vs ±7y vs unknown) — H6 supporting evidence. | YES — `age_source` and `age_confidence_years` are both in the response root. Inspect via §4.5 review. | **HIGHEST + LANDMARK.** This is the ONE field where Thammen ALREADY emits a per-field confidence signal. Stage 2 question would: (a) skip if `age_confidence_years <= 3` (high), (b) ask if 4–7y (medium — "GIS says ~2010–2017; do you know the exact year?"), (c) require if unknown. Mirrors D-stage2-2 threshold logic cleanly. |
| 6 | **Exact unit size** (vs. building GIS area) | EXISTS as `footprint_m2: Optional[float]` ([api.py:343](api.py:343)) + `floors: Optional[int]` → `_build_bua_breakdown()` ([api.py:363](api.py:363)) generates BUA breakdown. For apartments specifically, no per-unit-area field; engine assumes BUA ÷ unit_count. | **0 (zero) for apartment unit specifically.** GIS gives the *plot* PDAREA, never per-unit interior area. | INPUT for villas (BUA via floors+footprint). OUTPUT `plot_area_m2` always (the building plot, not unit). | **HIGH for apartments.** Add `unit_area_m2: Optional[float]` to `EvaluateDetailsRequest`. Already pairs with Sprint 2.16.10 `unit_count + per_unit_rent` pattern. Bounded multiplier (per-unit area × tier-median QAR/m²) replaces the building-share estimate when supplied. |
| 7 | **Occupancy status** (vacant / tenanted / owner) | NONE. `rental_income: Optional[float]` ([api.py:323](api.py:323)) accepts a number but no enum for status. The engine infers tenanted ⇔ rent>0, but cannot distinguish "owner-occupied" from "vacant" from "tenanted-but-low-rent". | **0 (zero).** Engine has no occupancy signal. | NO independent surface. Implicit from rental_income presence. | **MEDIUM.** Add `occupancy: Optional[str]` ∈ {`'vacant'`, `'tenanted'`, `'owner_occupied'`}. Bounded multiplier (vacant = baseline, tenanted = small −% for handover friction, owner = 0). RICS-compliant since RICS VPS 4 requires disclosure of "tenure assumed" in the brief — Stage 2 question makes this explicit. |

---

## Summary statistics (for H6 falsification)

**H6 hypothesis:** ≥4 of 7 candidate Stage 2 fields have *measurable per-field confidence* (GIS + MoJ data has per-field metadata).

**Strict count (per-field confidence signal exists in code TODAY):**

| Field | Per-field confidence exists today? | Notes |
|---|:---:|---|
| 1. Floor number | NO | No floor input in schema |
| 2. Interior condition | NO | Input exists but no confidence — user-supplied bool, not measured |
| 3. Recent renovations | NO | Derived from #2 |
| 4. Primary view | NO | No view signal in engine |
| 5. Building age | **YES** | `age_source` + `age_confidence_years` exposed today |
| 6. Exact unit size | PARTIAL | `footprint_m2` exists for villas; not for apartment units |
| 7. Occupancy status | NO | Implicit from rental_income presence |

**Count: 1 strict, 2 loose (counting field #6 partial) of 7.** → **H6 FALSE** under strict reading; **H6 PARTIALLY TRUE** under loose reading.

**Practical implication (D-stage2-2 refactor):**

The BRIEF's `confidence ≥0.85 don't ask · 0.50–0.85 ask · <0.50 critical` threshold logic **assumes a measurable confidence per field** that doesn't exist for 6 of 7 fields. Two options:

1. **Per-asset-type heuristics** (recommended): instead of per-field confidence, derive per-field "should we ask?" from the *asset_type* class. E.g., for `apartment_building`, ALWAYS ask floor + unit_size + occupancy; for `standalone_villa`, ALWAYS ask condition + building_age (if `age_source='unknown'`). This sidesteps the missing-confidence problem and aligns with E17 (1-field minimum input — fields surface contextually post-classification).
2. **Backfill confidence scoring** (more work): add a `field_confidence: dict[str, float]` block to the response, computed at end of Stage 1 per the BRIEF's logic. This is a Sprint 2.22.0 scope expansion — adds ~7 backend changes (one per field) and adds the per-field reasoning code.

**Recommendation: option 1.** Saves ~5-7 days of work and stays true to the actual data signal Thammen has.

---

## D-stage2-1 final field set recommendation (refined from BRIEF v2)

Pre-classification per asset_type — fields shown only when relevant:

| asset_type | Stage 2 fields shown (in order) |
|---|---|
| `apartment_building`, `tower` | floor, unit_area_m2, condition, occupancy, view, building_age (if unknown) |
| `standalone_villa` | condition, occupancy, building_age (if unknown — high signal here per #5) |
| `compound_small`, `compound_large` | n_units (already wired Sprint 2.16.10), per_unit_rent (wired), n_floors_per_unit, occupancy |
| `raw_land` | (skip Stage 2 entirely — D-stage2-4 path; land has no interior/floor/view fields) |
| `commercial`, `industrial` | condition, occupancy (lease status), building_age, floors |

**Per-screen layout (D-stage2-6):** 3 questions × max 2 screens. For apartments: screen 1 = floor, unit_area, condition; screen 2 = occupancy, view, building_age (if asked). Matches the BRIEF's 3 × max-2 default.

---

## Audit verdict — §4.2 deliverable

1. **H6 result:** FALSE under strict reading (1 of 7 have measured confidence). Per-asset-type heuristics recommended instead of per-field confidence.
2. **Field set in D-stage2-1 is FEASIBLE** as user-supplied claims, but `D-stage2-3` ("I don't know" handling) becomes the dominant UX pattern for 6 of 7 fields — there is no AVM "best guess" to fall back on because the engine never had a guess to begin with.
3. **Backend changes required:** add 3 new optional fields to `EvaluateDetailsRequest` — `floor`, `unit_area_m2`, `occupancy` — and surface 1 existing field (`view`) to the input layer. Other 3 fields already wired (`condition`, `building_age_years`, `renovated` via condition).
4. **Pattern to reuse:** the `age_source` + `age_confidence_years` pair (field #5) is the architectural template. Each of the 6 new fields needs an analogous `<field>_source` ∈ `{'user', 'avm_inference', 'unknown'}` so Stage 3 brief can render the adjustment ledger transparently per Rule E10 (source attribution).
