# BRIEF — Geometric-footprint sprint (floors-first → auto-footprint → confirm)

> **Status:** DRAFT (Anas-requested 2026-06-08, after b9 shipped). Awaiting Gate-2 sign-off on the
> methodology framing (the footprint compute itself is value-invariant; the cost-VALUE wiring is a
> separate later Gate-2 — see §6). **Next sprint = 2.22.0b.10** (proposed slug `geometric-footprint`).
> **Class:** value-invariant surfacing (the BUA estimate is displayed/confirmed, NOT yet fed into the
> headline value). Extends b1 (zoning footprint) + b2 (staged confirm).

## 1. Motivation (born this session)

The Al Manara bank report (TD 93317) values via **Cost Approach = land + depreciated building**. For an
ordinary old villa like **54/541/6** (Marikh, ≥17y, G+1, internal garden + garage), the engine's
condition-blind **5.4M** comparison is a **~+80% over-anchor**; the cost-approach value is **~2.8–3.0M**
(≈ Anas's «clears ~2.9M»). The missing ingredient is the **building area (BUA)**. We hand-computed it this
session: GIS polygon → plot **35.0×17.5 m** → minus setbacks → footprint **~238 m²** → BUA **~400–475 m²**.
Anas's idea: **automate this** — ask the user the number of floors, then show an auto-computed building area
for the user to confirm/correct (E17: Thammen estimates, the user corrects).

## 2. The flow (staged-input, E16)

1. **Stage 2a — ask floors** (`floors`, already an input). Default G+1 (2) for villas.
2. **Stage 2b (next page) — show the auto-computed area + ask «is this correct?»**:
   - auto **footprint** (ground floor) from plot geometry − legal setbacks (capped at the 60% coverage).
   - auto **BUA** = footprint × floors.
   - the user confirms or **corrects** (a single number); honest label: **«تقدير الحدّ الأقصى — صحّحه»**
     (NOT «مساحة بنائك»), because the legal-max ≠ the actual built area (see §4).

## 3. The footprint computation

Inputs already in hand: the **plot polygon** (`get_plot(pin).polygon_2932`, projected metres) + the
**legal R1 setbacks** (Empirical E15, corrected this session: front **5** / side **3** / rear **3** m,
coverage **60%**).

- **Plot dimensions:** the polygon is a clean rectangle for villas → derive edge lengths (W × D) from the
  2932 ring (done for 54/541/6 = 35.0×17.5). Sanity: shoelace area ≈ `pdarea`.
- **Footprint (max buildable):** `min( coverage_cap , setback_envelope )` where
  `coverage_cap = 0.60 × plot_area` and `setback_envelope = (depth − front − rear) × (width − sideL − sideR)`.
- **🔴 Orientation problem (the one real complication):** per-side setbacks need to know **which edge faces
  the street** (front 5 ≠ side 3). We have road geometry (`ROADFlowln` / `geometric_factors`) but it adds
  complexity. **Recommended robust default: the orientation-free `coverage_cap` (60% × plot)** as the
  headline auto-estimate — it is often the binding constraint and needs no edge detection. Offer the precise
  setback-envelope as a refinement ONLY when the street edge is confidently detected (or ask the user which
  side is the street). Decide in recon (§5).

## 4. 🔴 Honesty: the auto number is a CEILING, not the actual building

The setback/coverage calc gives the **legal MAXIMUM** footprint. The ACTUAL building is usually **smaller**
(internal courtyard/garden, the owner didn't max out). Measured: 54/541/6 legal-max ~310 m² (5/3/3) vs
actual ~238 m² (his real 7/3/3/5 + garden). **So the confirm step is where the user corrects DOWN to the
actual** — this is the heart of Anas's idea, and the copy must say so («الحدّ الأقصى المسموح — عدّله لواقع
مبناك»), never imply the auto number IS the building.

## 5. Recon (Phase 0, before build — mandatory)

- Edge-length extraction from `polygon_2932` across **non-rectangular** plots (L-shapes, >4 vertices) — does
  the W×D model degrade gracefully? (fallback: coverage-cap only.)
- Street-edge detection feasibility/cost (ROADFlowln per-edge) — decides §3's orientation question.
- Where b1's `_suggested_footprint` lives + how to upgrade it to the geometry calc WITHOUT changing the
  no-building-input anchors (b1 is value-invariant on those — must stay).
- The confirm-area UI: reuse the b2 `refineScreen` footprint field + the `effective_footprint_m2` surface.

## 6. Gate split (critical)

- **THIS sprint = footprint compute + display + confirm = VALUE-INVARIANT** (extends b1/b2; the BUA is shown
  + corrected, NOT fed into the headline). No Gate-2. Verify the 4 anchors stay byte-identical.
- **The §20.9 cost-triangulation = a SEPARATE later Gate-2 sprint:** BUA × depreciated construction rate +
  land floor → an independent Cost-Approach value (the ~2.9M that breaks the R7 over-anchor). Needs a
  calibrated construction rate (the bank's ~2,380 ر.ق/م² for V001's premium build is the anchor; ordinary <
  premium) — own §5 audit + Gate-2 sign-off. **NOT in this sprint.**

## 7. Verification plan

- Isolated test: the footprint helper (edge extraction, setback envelope, coverage cap, `min(...)`,
  non-rectangular fallback, value-invariance — the BUA never touches `valuation.amount`).
- DoD 392/15/45/broad. Local E2E: 4 anchors byte-identical + 54/541/6 → footprint ≈ 238–310 m² band, BUA shown.
- R14 (real Chromium): the floors→confirm-area flow renders, 390×844 no overflow, 0 console errors.

## 8. What's already shipped (so this is mostly assembly)

b1 (zoning footprint `_suggested_footprint` + zone-coverage table) · b2 (staged `refineScreen` + footprint
field + `effective_footprint_m2`) · the GIS plot polygon · E15 legal setbacks (corrected) · `floors` input.
The new work = (a) upgrade the footprint from heuristic to setback-geometry, (b) floors-first → area-confirm
ordering, (c) the honest «max — correct it» framing.
