# Sprint 2.20 — Land Comparable Adjustments Grid (v1) — DRAFT for review

**Status:** DRAFT for review. **No code until approved** (Project_Instructions §5).
**Baseline:** Sprint 2.19.1 (`thammen-sprint2p19p1-polish-and-fixes`, Heroku v78)
**Target:** Sprint 2.20 (`thammen-sprint2p20p0-land-adjustment-grid`)
**Type:** New RICS Market-Comparison transparency section — **complement, not replace**.
**Scope:** LAND asset type. v1 coefficient = **T1 (MoJ) Time only**. **Size deferred
to 2.20.1** (data-driven: §8 scan = 28.4% stable < 40% gate). **No corner in v1.**
The framework still models Size/corner so they slot in later without refactor.

---

## 0. Why this scope (decision trail — both premise failures caught pre-build, §5)

1. **Villa attributes** — arady `number_of_roads` flat=1, `land_front_direction`
   null for villas → no villa adjustment signal → villa grid deferred to 2.20.1.
   Order flipped to **Land-first**.
2. **MoJ self-calibration for corner** — proposed deriving a corner premium by
   tagging every MoJ sale via `detect_corner`. **Blocked by data reality**: MoJ
   rows carry an opaque property hash (`PN…`, 0/26,719 numeric), **no PIN / no
   coordinates / no street** → MoJ sales cannot be geo-located to parcels →
   `detect_corner` cannot tag them. Arady asking would be the only corner source
   (T2, sentiment) → violates the spirit of E1 if applied to the main value.
3. **Decision: Option B** — ship a clean **T1-only** land grid (Time + Size +
   stratification fallback). Corner deferred until a **PIN-keyed sale source**
   (Confirmed Sales, indefinitely delayed) exists. This builds the reusable
   AdjustmentGrid framework + E8/E10/E11 with zero methodology caveats.

---

## 1. What the grid does

For a LAND subject (area_token, bracket):
- Pull MoJ land comparables (same area_token + bracket, 24-month window; 36-month
  fallback when n<20 — existing reference rules).
- **Time adjustment** (T1): age each comparable's price/m² to the valuation date
  using the area's existing MoJ annual trend (`slope_annual_pct`).
- ~~Size adjustment~~ — **DEFERRED to 2.20.1** (§8 scan: within-bracket
  size→price/m² is too weak/noisy; median R²≈0.05). v1 ships Time-only.
- Report the **adjusted median price/m²** + per-comparable cards (RICS transparency).
- **Headline value is unchanged** — the grid is a complementary section
  ("شبكة المقارنات المعدّلة"); it shows the work behind the comparison.

**Value over the existing stratified median (2.16.0):** explicit per-comparable
transparency + time-normalisation of each sale to the valuation date (the plain
median does not age individual sales). Pure RICS Market Comparison, T1-defensible.

---

## 2. AdjustmentGrid framework (`adjustment_grid.py` — new, reusable)

```python
@dataclass
class Adjustment:
    factor: str           # 'time' | 'size'
    pct: float
    source: str; tier: int; tier_weight: float   # E8: T1=1.0 (T2=0.7 reserved)
    n: int; confidence: str; rationale_ar: str

@dataclass
class Comparable:
    price_per_m2_raw: float; date; size_m2: float
    adjustments: list[Adjustment]
    adjusted_price_per_m2: float          # raw × Π(1+adj.pct)

@dataclass
class AdjustmentGrid:
    subject: dict
    comparables: list[Comparable]
    adjusted_median_per_m2: float; n: int
    confidence: str        # E11: gated by min tier + n
    sources: list          # E10 per-tier attribution
    fallback_used: bool    # True → 2.16.0 stratification, no grid
```

Reusable for 2.20.1 (villa) / 2.20.3 (commercial). The `Adjustment.tier`/
`tier_weight` metadata is wired now (E8) even though v1 uses only T1 — so a later
T2 factor (e.g., corner) slots in without refactoring.

---

## 3. Confidence model (E8 / E10 / E11)

- **E8 — Tier weighting:** weighted_median across tiers (T1=1.0; T2=0.7, T4=0.4
  reserved for later factors). v1 is all-T1.
- **E10 — Attribution:** every grid output lists sources + tiers + n per factor.
- **E11 — Tier floor:** grid `reliable` requires n≥20 MoJ comparables AND ≥T1
  (always true in v1). `indicative` at 10–19. n<10 → **fallback** to 2.16.0
  stratification (no grid shown).

---

## 4. Size adjustment — DEFERRED to 2.20.1 (data-driven, §8 scan)

The §8 pre-build scan settled this empirically: the within-bracket
size→price/m² relationship is **not stable enough** to ship.
- Criterion **(c) CoV(slope)<0.50** (Anas-recommended): **28.4% stable < 40% gate**.
- Mathematically **(a) |t|≥2.0 ≡ (c)** (CoV = 1/|t|) → identical 28.4%.
- **(b) R²>0.30: 8.1%** — even more damning; median R²≈0.046 means size explains
  ~5% of within-bracket price/m² variance. Applying it would inject noise.

**Decision (Anas's pre-set rule, <40% → time-only):** v1 = **Time-only +
stratification fallback**. Size adjustment **deferred to Sprint 2.20.1**. The
`Adjustment` class still supports `factor='size'` so 2.20.1 wires it without a
refactor (e.g. once larger samples or cross-bracket modelling improve stability).

---

## 5. Display (Q5)

- **Mobile 390×844:** card-per-comparable (vertical scroll); each card: raw
  price/m², **time chip only** (`تعديل الزمن: +X.X%/سنة (مرجع MoJ منطقة كذا)`),
  adjusted price/m². No horizontal grid.
- **Audience (§16):** engineer = full cards + coefficient + tier + n; manager =
  adjusted median + n + tier summary (no coefficients); **secretary = hidden**.
- **Graceful degradation:** any cell n<10 → fall back to 2.16.0 stratification;
  **no empty grid**.
- **UX honesty (Anas):** corner/size sections are **absent** in v1 (do NOT render
  "غير متاح", do NOT hint at corner). Single footer:
  `علاوة الزاوية والحجم ستُضاف لاحقاً عند توفّر بيانات geographically-keyed.`

---

## 6. Files

| File | Change |
|---|---|
| `adjustment_grid.py` | **new** — Adjustment/Comparable/AdjustmentGrid + build logic (**Time only emitted in v1**; Size supported structurally for 2.20.1; tier metadata) |
| `property_geo.py` | **new** — `detect_corner()` **SAVED FOR FUTURE, NOT WIRED** into the valuation flow (docstring: "for future Sprint 2.20.x corner integration; needs PIN-keyed sale source") |
| `evaluate_unified.py` | wire grid for `asset_type` land; ENGINE_VERSION/SPRINT_TAG bump; **no per-request GIS** (latency-neutral) |
| `output_briefs.py` | grid section builder (Arabic, audience-aware, E10 attribution) |
| `index.html` | `case 'comparable_grid'` renderer (mobile cards) |
| `docs/Empirical_Findings.md` | add **E8–E12** (E12 marked **BLOCKED**) |
| `docs/Operational_Rules.md` | add **Rule #45** (verify data-linking before batch processing) |
| `tests/test_sprint_2p20_*.py` | new (≥6) |
| `CHANGELOG_v39.md` | new |

No new SQLite snapshot needed (Time uses existing trends; Size computed from
existing MoJ reference at request time, in-process, no extra I/O).

---

## 7. Docs to add

**E8–E11** (as previously specified). **E12 — MoJ Self-Calibration for Attribute
Premiums (PRINCIPLE, status: BLOCKED):**
> When an attribute can be batch-detected on a **PIN-keyed / geocoded** sale
> dataset (T1), the resulting premium is T1-T1 and may be applied to the main
> value (n_with ≥20 AND n_without ≥20 per area×bracket; detection ≥10/10
> validated; documented per E10). **Status 2026-05-20: BLOCKED — the MoJ weekly
> bulletin is NOT geocoded (opaque `PN…` ref, no PIN/coords). Activates only when
> a PIN-keyed sale source exists (Confirmed Sales, or verified MME geocoding).**

**Rule #45 — Verify data-linking schema before proposing batch processing:**
> "Has field X / can dataset A join to B?" must be **measured on the actual
> data**, not assumed from descriptions. Lesson (2026-05-20): assumed MoJ
> `رقم العقار المرجعي` was a GIS PIN; it is an opaque `PN…` hash (0/26,719
> numeric). Cost: ~1h on an impossible plan. Pairs with #33 (empirical-first).

---

## 8. Pre-build measurement — DONE (results below)

1. **Coverage (done):** 100/339 land cells n≥10 (49 reliable ≥20, 51 indicative).
2. **Size-stability scan (done, `audit_size_stability.py`, local, no GIS):**
   74 land cells with n≥15. Chosen criterion **(c) CoV(slope)<0.50** (precision of
   the slope; ≡ (a) |t|≥2.0 since CoV=1/|t|). Results:
   - (a)|t|≥2.0 = **28.4%** · (b)R²>0.30 = **8.1%** · (c)CoV<0.5 = **28.4%**.
   - median R² **0.046**, median CoV **0.97**; slope sign 51 neg / 23 pos.
   - **28.4% < 40% gate → size DEFERRED to 2.20.1; v1 = Time-only.** Robust under
     all three criteria.

(No corner gate — `detect_corner` is not wired in v1.)

---

## 9. Pre-deploy 6-item checklist (§5)

1. `py_compile` all modified Python. 2. `node --check` index.html JS (⚠️ Node not
installed locally → browser-verify on a land address like الوكير + screenshot).
3. Mobile 390×844 (cards). 4. Full standalone suite green (current: all 15 files
exit 0). 5. ≥6 new isolated tests. 6. Smoke 3 land addresses from Heroku
(NOT 51/835/17 — A6).

---

## 10. Tests (≥6)

- Time adjustment ages a comparable correctly (sign + magnitude vs valuation date).
- AdjustmentGrid: adjusted_median computed; **confidence gating** (E11 reliable
  ≥20 / indicative 10–19); **fallback** when n<10 (no grid).
- Framework supports `factor='size'` structurally (an Adjustment with size applies
  in the math) **even though v1 never emits one** — guards the 2.20.1 path.
- E8 weighted_median.
- output_briefs: Arabic grid render + **secretary hidden** (§16) + footer present.
- Two-layer (Rule #40): one test exercises the real `evaluate_unified` land path.

---

## 11. Decisions recap (final)

1. **E1/E3:** N/A in v1 (no corner). Principle preserved; future T1 path via E12.
2. **Grid threshold:** tiered, show at **n≥10**, label reliable at n≥20.
3. **Size adjustment:** **DEFERRED to 2.20.1** — §8 scan = 28.4% stable < 40%
   gate (criterion (c) CoV<0.5, Anas-recommended; ≡ (a) |t|; (b) R² worse at 8.1%).
   v1 = Time-only.
4. **A6 latency:** N/A — no per-request GIS; latency-neutral.

---

## 12. CHANGELOG_v39 structure
Mirror v38: Why · What (framework / time / size) · **Decisions made** (Option B
rationale; corner deferred + why; size stability result) · Empirical evidence
(coverage + size-stability %) · Deployment (subtree) · Verification curl · NOT in
patch.

---

## 13. Out of scope (2.20) / saved for future

- **Corner adjustment** — deferred until a PIN-keyed sale source (Confirmed Sales
  or verified MME geocoding). `detect_corner` (4/4 validated) saved in
  `property_geo.py`, **not wired**; its 10/10 gate is **not** required for 2.20.
- Direction / sorting / zoning / off-plan (null or N/A in arady land data).
- Villa (2.20.1, after Confirmed Sales) · Apartments (2.20.2 / 2.29 MME) ·
  Commercial (2.20.3).
- arady corner *sentiment panel* — possible future micro-Sprint (separate from
  the adjustment grid, like the cap-rate display), never feeding the main value.
- Mthamen (§20.8 — do not propose).

---

## 14. Status / sign-off
- Option-B scope **signed** (Anas). §8 size-stability scan **done** → size
  **deferred to 2.20.1** (28.4% < 40%). Criterion **(c) CoV<0.5** chosen +
  documented (≡ (a)|t|; (b)R² reported worse).
- **v1 final scope:** AdjustmentGrid framework (E8/E10/E11) + **Time** adjustment
  + stratification fallback + 3-tier display + mobile cards + §16 audience +
  UX footer. Size/corner structurally supported, **not emitted**.
- **Awaiting:** Anas approval to begin code wiring (§5). No code until then.
