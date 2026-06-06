# CHANGELOG v79 — Sprint 2.22.0b.1 (Geometry Refinement: zoning-driven footprint + basement excluded)

**Engine:** `thammen-sprint2p22p0b1-geometry-zoning-footprint` · **SPRINT_TAG** `2.22.0b.1`
· api-health `3.1.0-sprint2.22.0b.1`
**Date:** 2026-06-06
**Gate-2:** SIGNED (Anas «افعل الأصوب» ×2 + Claude.ai R14-verified rulings)
**Files changed:** `evaluate_unified.py` · `index.html` · `test_sprint_2_22_0b1.py` (new)
**First sprint of the 2.22.0b staged-input arc.**

---

## 1. Why this matters

The simple user could not steer the **building component** of a villa/house valuation
in a zoning-grounded, honest way. Two concrete gaps:

- The footprint estimate that feeds the comparison was a **flat plot-proportional
  default** (`_typical_footprint`, 45–60%) capped at a **constant `MAX_COVERAGE=0.80`**
  — it ignored the municipal zoning ceiling (R1 60% / R2 50%), so a user-entered large
  footprint could be capped far too generously.
- The **basement** was counted at full weight inside the BUA that drives the
  sales-comparison adjustment (`_building_substantiality`). Measured live on a25 (R14):
  basement=true added **+11.5%** to the headline (350/3 → 2.6M ↔ 2.9M). Comparable villa
  prices already reflect typical basements implicitly and we do not know whether the comps
  have basements → counting the subject's basement as a comparison premium **double-counts**.

## 2. Root cause (recon, read-only, a25/v164)

The geometry-capture machinery **already existed and is live** on `/api/evaluate/details`
(`floors`/`footprint_m2`/`basement` → `_build_smart_bua` → `_building_substantiality`); the
live frontend posts there ([index.html:673](index.html:673)). So the original brief's §6
("add fields to the quick `/api/evaluate`") was **dead-on-arrival** (the quick endpoint is
not the geometry path), and "basement separate / floors above-ground" already held. The
**genuine** deltas were narrower (confirmed by Claude.ai's independent live R14):

- footprint cap + default were **not zoning-aware** (`MAX_COVERAGE=0.80`, `_typical_footprint`);
- basement **was** a comparison driver (`BuaBreakdown.total_bua` includes `basement_m2`,
  [evaluate_property.py:387](evaluate_property.py:387); `_building_substantiality` divides by it);
- the assumed-vs-confirmed footprint basis was not disclosed.

Architecture decision (Rule #39): the clean GIS zoning code is only available **post-factors**
(parsed in `_run_geometric`), not at the `_build_smart_bua` call site. So the zoning-aware
footprint + basement exclusion are applied at the **substantiality stage**, reusing the
already-fetched zoning — **zero extra GIS calls** (A14/E21 latency lesson).

## 3. What this patch does

**Backend (`evaluate_unified.py`):**
- New QNMP table `ZONE_MAX_COVERAGE` (R1=0.60, R2=0.50; `-TYP` variants) + helpers
  `_zone_max_coverage`, `_suggested_footprint`, `_extract_zoning_code`.
- `_suggested_footprint` = plot × 0.8 × zone-ceiling, **capped at the legacy
  `_typical_footprint`** so the assumed default can **never silently inflate** vs prior
  behaviour (Gate-2 §5.2-B; this cap was added after the live E2E caught that 0.8×0.60 >
  0.45 on >800 m² plots). Unknown zoning → legacy default (no regression).
- Substantiality block: builds a dedicated **above-ground comparison BUA** with the
  **zone-aware effective footprint** (confirmed → user value capped at the zone ceiling;
  assumed → the conservative suggestion) and **`basement=False`** (delta ب — basement is
  captured/displayed + a future DRC input, NOT a comparison driver). The unchanged
  `_building_substantiality` is fed this BUA. The **display** `bua_breakdown` (with basement,
  for `qar_per_m2_bua` + DRC + capture) is left untouched.
- Surfaces `valuation.geometry` `{zoning_code, zone_max_coverage_pct, suggested_footprint_m2,
  footprint_basis, basement_in_comparison:false, note_ar}` (additive — does NOT change
  `valuation.amount`).
- Delta ج: when the comparison used an **assumed** footprint, adds a known-unknown to
  Material Uncertainty so confidence/range reflect the assumption.
- `_run_geometric` zoning parse refactored to the shared `_extract_zoning_code` (DRY,
  byte-identical).

**Frontend (`index.html`):**
- Footprint input placeholder hints that it is auto-estimated from zoning.
- New muted `.rc`/`.rn` card surfaces the suggested footprint + zone ceiling + the
  assumed/confirmed basis + the basement disclosure (augment-existing-panel; no auto-prefill,
  so "assumed" stays honest until the user enters a measured value).

**Schema:** none — uses the existing `/api/evaluate/details` fields. The quick
`/api/evaluate` is intentionally NOT changed (the original §6 was superseded by recon).

## 4. Verification — empirical evidence

- `python -m py_compile evaluate_unified.py` → OK.
- Isolated `test_sprint_2_22_0b1.py` → **34/34** (production functions, Rule #40/E14): zoning
  table + legacy fallback; conservative suggestion + **no-inflation invariant** (suggested ≤
  legacy for all plots/zones, incl. the large-plot cap); `_extract_zoning_code`;
  **basement-excluded** lowers the comparison driver; zone-cap tighter than legacy;
  no-building-input → `None` (anchors path untouched); version format (R6).
- DoD (PYTHONIOENCODING=utf-8): aggregator **392/392** · security **15/15** · surface-honesty
  **45/45** · broad auto-walk **67/67** (66→67 = the new test).
- **Local E2E on the REAL engine** (GIS reachable here), 56/565/21 (R1, plot 900):

  | case | amount | basis | subst_adj | bua |
  |---|---|---|---|---|
  | no building input | **2,400,000** (= live a25 anchor) | assumed | — | — |
  | floors=3 | 2,800,000 | assumed | 15% | 1093 |
  | floors=3 + **basement** | **2,800,000** (≡ floors=3) | assumed | **15%** | **1093** |
  | floors=3 + footprint=600 | 2,900,000 | **confirmed** | 20% | 1458 (fp capped 600→540) |

  → anchor byte-identical; **basement no longer moves the headline** (was +11.5% on a25);
  confirmed footprint capped at the zone ceiling (was +25% → now +20%); suggestion **405**
  (capped, no inflation); zoning **R1** parsed live.
- **R14 (real Chromium, EXECUTED):** whole-file JS parses (`show`/`run`/`fmt` defined),
  **0 console errors**, new placeholder live; geometry card at **390×844** →
  `scrollWidth == clientWidth` (no card overflow), page `scrollWidth == clientWidth 390`
  (no horizontal overflow), cardRight 376 < 390.

## 5. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add evaluate_unified.py index.html test_sprint_2_22_0b1.py CHANGELOG_v79.md
git commit -m "Sprint 2.22.0b.1: zoning-driven footprint + basement excluded from comparison"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy, browser-UA per Rule #61)

```
curl -s https://thammen.qa/api/health
curl -s -A "Mozilla/5.0 ... Chrome/... Safari/537.36" -X POST https://thammen.qa/api/evaluate/details ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":56,\"street\":565,\"building\":21,\"floors\":3,\"basement\":true}"
```
Expect: engine `…b1…`; 56/565/21 no-building byte-identical 2.4M; floors=3 == floors=3+basement
(basement excluded); `valuation.geometry` present.

## 7. What's NOT in this patch (scope boundary, Rule #38/#42)

- **Condition / finish / luxury (R7 / Sprint B-2)** — parked on Confirmed-Sales GT-2 n≥20.
- **Full guided staged sequence (§4 UX)** — deferred; augment-existing-panel chosen (§4 was
  built on the now-falsified "capture doesn't exist" premise). Revisit only if the panel
  proves hard for simple users.
- **Quick `/api/evaluate` geometry fields (original §6)** — superseded by recon (dead).
- **Independent DRC / calibrated basement premium** — post-2.22.0b.
- **multi-QARS effective-area into the BUA baseline** — pre-existing (`_typical_bua_for_plot`
  uses full pdarea, not per-villa); the suggestion inherits the same plot basis. Flagged for a
  future follow-up; out of scope here (Rule #38).
- **Display-vs-comparison footprint nuance** — the muted `qar_per_m2_bua` line uses the
  display BUA (with basement); the comparison driver uses the above-ground zone-aware BUA.
  Intentional per §5.5; documented.
