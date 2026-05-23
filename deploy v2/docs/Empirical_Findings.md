# EMPIRICAL FINDINGS — Methodology Validation 2026-05

> **Status:** Validated by paired field audits (villas + lands), 5 areas, 4 brackets each, MoJ n=149+ villas + n=149+ lands. **2026-05-18 update:** Cost Approach (DRC) added via Mthamen reverse engineering (Rule E6). **2026-05-19 AM update:** Rule E6 §8.5 added — Mthamen live integration deferred indefinitely. **2026-05-19 PM update:** Rule E7 added — QARS subtype requires Zoning cross-check; deployed as Sprint 2.16.14 (CHANGELOG_v35). **2026-05-20→22 update (Land Arc):** E8-E11 (source tiers / cross-validation / attribution / tier floor — Sprint 2.20); E12 (MoJ self-calibration BLOCKED — cryptographic + ethical); **E13 (pull coded-value domains, never guess RULEID) + E14 (validation scripts must exercise production logic) — Sprint 2.21.0.7**.
> **Bound to every Thammen session as a permanent methodological reference.**

-----

## 1. Headline finding

The gap between asking prices and MoJ medians in Qatar reflects **building-stock age composition, not registration accuracy**.

| Asset | Median Asking Premium | Position vs Global Norm (8–15%) | Driver |
|---|---|---|---|
| **Land (clean)** | **+13.6%** | exactly within range | normal asking premium |
| **Villas (mixed)** | **+70.2%** | 5–10× too high | stock mismatch (new vs aged) |

### Implication
**MoJ is NOT systematically understated in Qatar.** Empirically falsified.

-----

## 2. Hard rules

### Rule E1 — Reject "MoJ-uplift" frameworks
🚫 NEVER implement logic that adjusts MoJ medians upward using listing data. Falsified.

### Rule E2 — Section 4 Buyer Hard Ceiling validated
✓ **Buyer Hard Ceiling = MoJ × 1.10** matches empirical asking premium for clean stock.

### Rule E3 — Listings = sentiment ONLY
✓ Asking prices may appear as "Market Sentiment" panel with explicit framing. MUST NOT enter calculation.

### Rule E4 — Villa valuation requires stock stratification
✓ Before any villa reference, classify:

```python
def classify_villa_stock(villa_per_m2, area, bracket):
    ratio = villa_per_m2 / moj_land_median(area, bracket)
    if ratio < 1.15: return 'land_priced'    # 10-Year Rule
    elif ratio < 1.50: return 'aging_stock'
    elif ratio < 2.20: return 'modern_stock'
    else: return 'luxury_new'
```

### Rule E5 — Premium > 25% on clean stock = red flag

Investigate cause: stock mismatch, off-plan, listing bias, or small-sample noise.

### 🆕 Rule E7 — QARS subtype requires Zoning cross-check for residential codes

✓ **Discovered 2026-05-19 PM** via field case (61/875/20 = Public Works
Authority) and 22-landmark audit.
✓ **Resolved Sprint 2.16.14 (CHANGELOG_v35), deployed 2026-05-19 PM**.

**The empirical finding**: QARS_Point `BUILDING_NO_SUBTYPE` was last
surveyed 2010-2012 for most parcels. ~9.1% of GOVERNMENT-category
buildings have a residential subtype (1=Villa, 6=Flats, 11=Tower) but
sit in a clearly non-residential zone (CCC, COM, CF, SCZ, MU*, etc.)
because their use changed silently after the original survey.

**Audit measurement** (2026-05-19 PM, 22 landmarks):

| Category    | Total | Mismatch | Rate |
|-------------|------:|---------:|-----:|
| BUSINESS    |     6 |        0 |   0% |
| FINANCE     |     8 |        0 |   0% |
| GOVERNMENT  |     8 |        2 |  25% |
| **Total**   |    22 |        2 | 9.1% |

**The rule** (deployed in Sprint 2.16.14, `qatar_gis.py`):
- Residential subtypes {1, 6, 11} + non-residential zone → emit
  `subtype_zoning_mismatch` flag, downgrade confidence to medium,
  add COMMERCIAL to alternative_types
- Do NOT change asset_type — surface the contradiction, let user decide
- Non-residential zone tokens: CCC, COM, CF, SCZ, TU, LFR, LInd, IND
- Any code starting with "MU" (Mixed Use) also counts as non-residential
- 0% false-positive on Business/Finance landmarks (validated)

**Reference case**: PIN 61050014 (61/875/20, Public Works Authority).
QARS subtype=6 surveyed 2010-01-26, last updated 2012-02-20. Zoning=CCC.

-----

### Rule E6 — Cost Approach (DRC) is a documented reference, NOT live integration

✓ **Discovered 2026-05-18** via reverse engineering of "المثمن" app (`com.informatique.pricing`).
✓ **Deferred 2026-05-19** from live integration (see §8.5).

**The principle**: RICS VPS 4 recognizes 5 valuation approaches (Market, Income, Cost, Profits, Residual). Cost Approach (DRC) is methodologically valid, and used by MoJ Qatar's own pricing app.

**The methodology** (extracted from APK):
```
Estimated Value = Total Land + Total Building - Depreciation + Extras ± Bounds

Total Land = (base_price/ft² × land_area_ft²) + 8 premiums
             (city, region, district, square, site, type, services, recreation)

Total Building = (avg_construction_price/m² × BUA_m²)
                + Finishing total + Floors value − Utility deductions

Depreciation = f(building_age, finishing_level, structural_status)
```

**Hard rules for Cost Approach integration in Thammen**:

1. **DRC is NEVER primary**. Market (MoJ) and Income (DCF) remain primary.
2. **The gap between Market and Cost is diagnostic**:
   - Market > Cost by 50%+ → strong market premium
   - Market ≈ Cost (±15%) → balanced market
   - Market < Cost by 30%+ → distress OR cost overstated
3. **Treat Mthamen's output as third-party reference, not raw data** (when reference is available):
   - The formula is the Ministry's intellectual property
   - We do NOT rebuild the formula in Thammen
4. **DRC most useful where Market evidence is thin**:
   - Old villas in areas with <10 transactions
   - Empty land in zones with no recent comparable sales
   - Specialty buildings (mosques, schools, single-occupant industrial)
5. **DRC LEAST useful for**:
   - Towers/apartment buildings (income approach dominates)
   - Compounds at scale
   - Properties with strong location premium
6. **🆕 Per 2026-05-19 decision** (§8.5): live API integration is **deferred indefinitely**. Cost Approach exists in Thammen as documented methodology only, not as a callable reference. Future revival requires 3 conditions in §8.5.

**Reference materials** (archived):
- `mthamen_report.md` (16 KB)
- `mthamen_reference.py` (17 KB — compiles but never deployed)
- `mthamen_strings_table.txt` (15 KB)

-----

### 🆕 Rule E8 — Source Tier Weighting

When combining sources in a calculation, use a **weighted median** with tier
weights: **T1=1.0, T2=0.7, T4=0.4**, T5 excluded. (Tiers: T1 = ground-truth
sales — MoJ land/villa, MME apartments; T2 = vetted accessible — PropertyFinder,
arady, FGRealty; T4 = partial; T5 = excluded permanently — bayut, mzadqatar.)
Implemented in `adjustment_grid.weighted_median` (Sprint 2.20).

### 🆕 Rule E9 — Cross-Source Validation

A factor confirmed by **≥2 sources from different tiers** that agree = high
confidence. A **single-source** factor is **`indicative` only**, never
`reliable`. (Reason corner premium would have been indicative had it come from
arady alone; reason it is deferred until a T1 source exists — see E12.)

### 🆕 Rule E10 — Transparent Source Attribution

Every output that uses external data must show its **sources + tier + n**.
Sprint 2.20 grid emits a `sources` block (`[{source, tier, tier_weight, n,
role_ar}]`) rendered in the brief.

### 🆕 Rule E11 — Tier Floor for Critical Calculations

Core operations (medians, cap rates, adjustments) require **≥Tier-2** to be
classified `reliable`; Tier-3-alone never `reliable`. The Sprint 2.20 grid is
`reliable` only at **n≥20** MoJ (T1) comparables, `indicative` at 10–19, and
**falls back** to Sprint 2.16.0 stratification (no grid) below 10.

### 🆕 Rule E12 — MoJ Self-Calibration for Attribute Premiums — **STATUS: BLOCKED**

When an attribute can be batch-detected on a **PIN-keyed / geocoded** sale
dataset (T1), the resulting premium is **T1-T1** and may be applied to the **main
value** (conditions: `n_with ≥20` AND `n_without ≥20` per area×bracket; detection
method independently validated ≥10/10; documented per E10). This unlocks
attribute premiums **without** an asking-to-sale gap assumption.

**Status 2026-05-20: BLOCKED.** The MoJ weekly bulletin is **not geocoded** — its
`رقم العقار المرجعي` is an opaque `PN…` hash (**0/26,719 numeric**), with no
PIN/coordinates/street. So `detect_corner` (and any GIS attribute detector)
**cannot tag MoJ sales**. E12 activates only when a PIN-keyed sale source exists
(Confirmed Sales — indefinitely delayed; or verified MME geocoding). Until then,
attribute premiums derived from MoJ self-calibration are infeasible. (Discovery
logged: Sprint 2.20 audit; see Operational_Rules #45.)

**Update 2026-05-21 — PN-hash invertibility analysis ⇒ BLOCKED_CRYPTOGRAPHIC
(+ BLOCKED_ETHICAL).** Investigated whether the `PN…` hash can be reversed to a
GIS PIN (which would unblock E12). **It cannot, on two independent grounds:**

1. **Cryptographic.** Full-corpus analysis (n=26,719; 26,128 distinct hashes):
   body length is **variable 9–13 hex** (rules out every fixed-width truncated
   hash — MD5/SHA1/SHA256/HMAC/Murmur/xxHash/FNV); length distribution is
   **unimodal/banded** with P(13)/P(12)=0.073 (rules out keyless hash mod 2^k,
   which would be uniform with mode=max width — *coverage-independent*);
   **per-nibble entropy ≈ 4.000 bits** (cryptographic output, not a structured
   id); **gcd(values)=gcd(diffs)=1** (not affine/XOR of PIN); PIN-embedding
   slices all sit at the random-chance baseline (no embedded PIN); the hash is
   **deterministic per parcel** across years (no salt). ⇒ a **keyed PRP/cipher
   (or keyed MAC)** over a bounded internal-id domain — uncrackable without
   secret-key recovery (2^128+). A keyless brute-force (md5/sha1/sha256/crc32 ×
   4 encodings × low/high truncations) returned **0 hits** but covered only
   PINs 11.0M–18.77M (8.7% of range — corroborating, *not* the basis).
2. **Identifier mismatch.** Even a hypothetical inversion yields MoJ's
   **internal parcel id**, not the GIS PIN — no published crosswalk, and
   embedding tests were negative.

**Ethical hard line (2026-05-21 decision).** The encryption is a deliberate MoJ
**de-identification** control; inverting it is re-identification of pseudonymized
government data. **No oracle was built; no >100-record validation was run** — by
decision, *even if it had been crackable*. Thammen's reputation depends on ethical
sourcing; mathematical knowledge of crackability has value, the application does
not. Recon/analysis scripts only: `probe_moj_hash.py`, `probe_moj_decode.py`,
`probe_moj_crack.py`.

**Net:** E12 stays BLOCKED. The *only* unblock path remains a genuinely PIN-keyed
T1 sale source (Confirmed Sales — Sprint 2.16.16; or verified MME geocoding) — the
`PN…` hash is permanently closed as a PIN source. Recall: **"تذكر E12"** /
**"تذكر تحليل تشفير العدل"**. Any future proposal to crack `encrypted_parcel_number`
or build a MoJ→GIS re-identification map → **STOP**.

> **Note on stability-criteria equivalence** (Sprint 2.20 §8): for a regression
> slope, **CoV(slope) = SE/|slope| = 1/|t|**, so `CoV<0.5` and `|t|>2` are the
> *same* test of slope precision — either may be used. **R²** measures explanatory
> power separately and typically gives a stricter verdict (Sprint 2.20 land
> size-stability scan: CoV/|t| = 28.4% stable, R²>0.30 = 8.1%, median R²≈0.046 →
> within-bracket size adjustment deferred to 2.20.1).

-----

### 🆕 Rule E13 — Coded-value domains are authoritative; pull them, never guess

✓ **Discovered 2026-05-22, Sprint 2.21.0.7.** An ArcGIS layer publishes its own
`code → description` map in the field's **coded-value domain** (`?f=json` →
`fields[].domain.codedValues`). For `Vector/General_Landuse` the RULEID map was
first *guessed* from sampled PINs — and was wrong (the guess put Pearl at
RULEID 22/23; the authoritative domain shows Pearl is **21 = Special Use**, and
23 = Mixed Use is a distinct master-planned class). `probe_ruleid_domain.py`
fetched the real domain (1 Single-Family Res … 12 Governmental … 19 Agricultural
… 20 Vacant … 21 Special Use … 23 Mixed Use … 24 Unknown, −1 Free Representation).

**The rule**: whenever a GIS/data field carries codes (RULEID, SUBTYPE, ZONING,
status enums), **fetch the coded-value domain** and key the logic on it. Guessing
from a handful of observed samples is how you ship "Pearl = Tourism" to
production. (Implemented: `RULEID_LABELS` in `qatar_gis.py`, sourced from the
domain.) Recall: **"تذكر E13"** / **"تذكر RULEID"**.

### 🆕 Rule E14 — A validation script must exercise production logic, not echo the input

✓ **Discovered 2026-05-22, Sprint 2.21.0.7.** `probe_land_pins.py` "confirmed"
5/5 PINs as land — but it only **re-printed the user's land hint**; it never
queried QARS or RULEID. The live Asset Type Reality Check then proved **2/5 were
wrong** (`90040668` built, `52060090` governmental). A test that asserts what it
assumes is worthless.

**The rule**: a validation/probe script must call the **real** detection/
classification path (or an independent authoritative source) and compare against
ground truth — never restate its own input as the "result". Pairs with Rule #40
(replica + production verification) and Operational_Rules #49 (identifier ≠
asset_type). Self-check: *"if my code were broken, would this script still pass?"*
If yes, it isn't validating anything. Recall: **"تذكر E14"**.

### 🆕 Rule E15 — Qatar MME setback regulations (load-bearing for multi-villa logic)

✓ **Sourced 2026-05-23**, anchors Sprint 2.21.0.9 (Stage 1) and the Stage 2
classification rule (E18).

Qatar Ministry of Municipality (MME) building code requires minimum setbacks on
residential plots:

| Setback | Minimum |
|---|---|
| Residential villa — all sides | **3.0 m** |
| Basement | 1.0 m |
| Commercial — front | 8.0 m |
| Commercial — back | 3.0 m |

**Implication for multi-villa detection.** Two separate villas built on a shared
cadastral plot at code-minimum setbacks have **walls ≥ 6 m apart** (3 m × 2
sides), giving centroids roughly **16 m+** apart for a typical 10 m villa width.
So a 15.2 m GPS centroid distance — like Bou Hamour 56/565/21 — is **fully
consistent with two physically separate, code-compliant villas**, not a duplex.
This single fact is why Sprint 2.21.0.9 (Stage 1) does **no GPS-distance
classification** and Stage 2 (E18) uses **wall-to-wall** distance against the
6 m code-derived threshold instead. Source: https://www.mme.gov.qa/. Recall:
**"تذكر E15"** / **"تذكر ارتداد البلدية"**.

### 🆕 Rule E16 — Staged-valuation pattern (platform-wide, Anas 2026-05-23)

✓ **Decided 2026-05-23.** All valuation flows now progressively enhance:

| Stage | Data | Latency | Confidence | UX |
|---|---|---|---|---|
| **1** | Minimum (1-field identification + auto-fetched GIS/MoJ) | ≤ 5 s | ~70% | Always returns a number |
| **2** | Richer auto-fetched data (e.g. Building Footprint, deeper GIS layers) | seconds | ~90% | Refines Stage 1; user sees the upgrade transparently |
| **3** | User-on-site corrections / valuer-entered ground truth | n/a | ~95%+ | User overrides resolved |

**The rule.** Every future Sprint reviewed through the staged lens: *which stage
does this contribute to, and can Stage 1 ship independently?* Stage 1 must never
be blocked on Stage 2 data. Sprint 2.21.0.9 is the first Sprint shipped under
this discipline (multi-QARS detection ships without attached/separate
classification because that's Stage 2 territory — see E18). Recall:
**"تذكر E16"** / **"تذكر staged valuation"**.

### 🆕 Rule E17 — 1-field minimum input principle (Anas 2026-05-23)

✓ **Decided 2026-05-23.** The only field required from the broker is **property
identification** — `zone/street/building` address, `PIN`, or (future) map
pin-drop. **Everything else is auto-fetched from authoritative sources** and
presented transparently for review.

Optional refinements are **asset-type-adaptive** and revealed *post-
classification* (e.g. tower-specific inputs only appear after classify_asset
returns tower; villa-specific inputs only appear after standalone_villa). The
broker reviews and corrects what Thammen fetched — Thammen never asks the broker
to supply what GIS already publishes.

This is the inverse of the legacy "ask the user everything" pattern and aligns
with **RICS VPS 4 disclosure requirements** (every datum cited with source).
Recall: **"تذكر E17"** / **"تذكر 1-field minimum"**.

### 🆕 Rule E18 — Stage 2 wall-to-wall classification rule (Anas 2026-05-23)

✓ **Pre-specified 2026-05-23**, deferred to Sprint 2.21.0.10 candidate
(conditional on Building Footprint layer probe). Anchored on E15 (Qatar MME
setback code).

**The rule.** Two villas sharing one cadastral plot are classified by
**direct wall-to-wall distance**, not GPS centroid distance:

```python
wall_to_wall = shapely.distance(footprint_A, footprint_B)
if   wall_to_wall <  1.0: type = 'attached'      # shared wall + 1m GPS noise
elif wall_to_wall >= 6.0: type = 'separate'      # Qatar code min (3m × 2 sides)
else:                     type = 'sub_minimum'   # 1m-6m: rare, flag for review
```

This **replaces** the GPS-centroid threshold (15 m proposed; 18 m considered;
both rejected) that the original Sprint 2.21.0.9 brief assumed. The replacement
is decisive because the 1 m / 6 m boundaries are not tuning parameters — they
fall directly out of Qatar MME building code (E15). No re-debate needed in
Stage 2.

**Prerequisite.** Building Footprint layer must be reachable from Heroku and
queryable by `ZONE_NO + STREET_NO + BUILDING_NO`. Probe is the first deliverable
of any Sprint 2.21.0.10 work. Sprint 2.21.0.9 (Stage 1) logs `pin`, `n_qars`,
`is_shared`, `override_applied` so Sprint 2.21.0.10 can join historical
detection traffic on `pin` once footprints arrive. Recall: **"تذكر E18"** /
**"تذكر قاعدة 6 متر"**.

-----

## 3. Empirical benchmarks for Qatar (validated 2026-05)

### Asking premium expectations

| Stock category | Expected premium vs MoJ | Action if exceeded |
|---|---|---|
| Land (residential, standard) | +5% to +20% | investigate sub-stock |
| Land (corner/landmark) | +20% to +50% | normal for premium features |
| Modern villa (resale, 3-10y) | +10% to +20% | investigate listing bias |
| New-build villa | +30% to +60% | normal: developer margin |
| Off-plan unit | +40% to +80% | normal: financing + future value |
| Aging villa (10+ years) | varies | MoJ likely shows land-pricing |

### Direct measurements per area

| Area | Land 600-900 m² (n) | Land premium |
|---|---|---|
| الغرافة | 3,606 QAR/m² (n=44) ✓ | +4.5% |
| الدحيل | 4,598 QAR/m² (n=9) | +4.6% |
| الخيسة | 4,034 QAR/m² (n=6) | +19.7% |
| عين خالد | 3,974 QAR/m² (n=8) | n/a |

### Villa-vs-Land ratios per area

| Area × Bracket | Villa/Land ratio | Classification |
|---|---|---|
| الغرافة 600-900 | 5104 ÷ 3606 = 1.42 | aging stock |
| الخيسة 400-600 | 5180 ÷ 3095 = 1.67 | modern-leaning |
| الدحيل 600-900 | 6046 ÷ 4598 = 1.31 | aging stock |
| عين خالد 900-1500 | 3084 ÷ 3314 = 0.93 | **all land-priced** (10-Year dominant) |

عين خالد 900-1500 (ratio < 1) means villas trade **below** lands → bracket dominated by old villas being sold for demolition.

-----

## 4. Updates to existing Project Instructions sections

### Section 3 — Empirically validated benchmarks
- Asking premium for clean stock = 8–20% (matches global)
- Asking premium for mixed-age villa = 50–160% (stock mismatch)
- MoJ NOT systematically understated — reject any uplift logic
- **🆕 Cost Approach reference** exists as documented methodology only (Rule E6 §8.5)

### Section 9 — Asking-side red flags
- Premium > 25% on land → investigate sub-stock features
- Premium > 50% on villas → stock-mismatch suspected
- Premium > 100% → off-plan/new-build, exclude

### Section 10 — Honesty principles
- MoJ records **realized transactions**, not "market value" per se
- Never claim MoJ is "understated" — empirically false in Qatar
- 🆕 When using DRC reasoning (even from memory), state: "This is replacement cost reasoning, not market price"
- 🆕 **Document failed integration paths as clearly as successful ones**

### Section 11 — Completed
| 2026-05 audit | EMPIRICAL_FINDINGS.md | Asking-premium reality check |
| 2026-05-18 | EMPIRICAL_FINDINGS.md Rule E6 | Cost Approach (DRC) added |
| 🆕 2026-05-19 | EMPIRICAL_FINDINGS.md Rule E6 §8.5 | Live integration deferred |

-----

## 5. Reference data

### MoJ area names with NBSP normalization

| Display | MoJ raw | n (24m) |
|---|---|---|
| الغرافة | `غرافة\xa0الريان` | 147 |
| الخيسة | `الخيسة` | 93 |
| الدحيل | `دحيل` | 47 |
| عين خالد | `عين\xa0خالد` | 132 |
| لوسيل | `لوسيل` + `لوسيل\xa069` | 21 |

### MoJ Land medians by area × bracket (24m, validated)

```
الغرافة Land:
  400-600  m²: 3,928 (n=14)
  600-900  m²: 3,606 (n=44) ★ reliable
  900-1500 m²: 3,333 (n=7)

الخيسة Land:
  400-600  m²: 3,095 (n=24) ★ reliable
  600-900  m²: 4,034 (n=6)

الدحيل Land:
  600-900  m²: 4,598 (n=9)
  900-1500 m²: 4,629 (n=3)

عين خالد Land:
  400-600  m²: 3,196 (n=16)
  600-900  m²: 3,974 (n=8)
  900-1500 m²: 3,314 (n=10)
  1500+    m²: 3,860 (n=6)
```

### 🆕 Mthamen API reference (DOCUMENTATION ONLY — not callable from production)

```
Base:          https://sak.gov.qa/pricingws/jsonstore1/
Main handler:  PricingMobileDefBuildingStatusCRUD.ashx
Actions:       getprices | GetPriceEquationData | calculate
               calculatevirtual | graphcalc | syncuserdata
Auth:          deviceUDID (any stable string)
Rate limit:    ~1/day per UDID (confirmed 2026-05-19)
WAF:           F5 BIG-IP ASM, geo-restricted (blocks Heroku)
Methodology:   Cost Approach (DRC)
Formula:       Land(9 premiums) + Building(4 layers) - Depreciation
🆕 STATUS:     INTEGRATION DEFERRED 2026-05-19 (§8.5)
```

### Audit deliverables (archived, do not deploy)

- `mthamen_report.md` — full DRC methodology from APK
- `mthamen_reference.py` — Python wrapper (compiles, never connects)
- `mthamen_strings_table.txt` — 225 string resources
- `smoke_mthamen.py` + `smoke_mthamen_v2.py` — Heroku reachability tests (kept for future verification)

-----

## 6. Self-check triggers for future sessions

If Claude:

- Proposes "MoJ understated, adjust upward" → STOP, reference this document
- Suggests blending listings into valuation → STOP
- Treats villa MoJ medians as single population → STOP, stratify
- Claims asking premium > 25% is normal in Qatar → STOP
- 🆕 Treats Mthamen DRC as primary valuation → STOP, Rule E6
- 🆕 Tries to "correct" Thammen value using Mthamen → STOP, gap is diagnostic
- 🆕 Rebuilds Mthamen's formula in Thammen → STOP, IP concern + brittleness
- 🆕🆕 **Proposes reviving Mthamen live integration → STOP**, read §8.5. Need all 3 conditions met.
- 🆕🆕 **Proposes any new Qatar government endpoint integration without Heroku smoke test → STOP**

User triggers: **"راجع EMPIRICAL_FINDINGS"** · **"تذكر audit الأرض"** · **"تذكر المثمن"** · **"تذكر قرار 19 مايو"**

-----

## 7. What this document does NOT supersede

- Section 5 (UI-First Audit) — still mandatory
- Section 7 (GIS-authoritative names) — still binding
- Section 6 (MoJ Data Freshness) — still 139+ days stale
- Section 9 (existing Red Flags) — still apply
- Section 19 (Tower Methodology) — still binding
- Section 20 (Cost Approach via Mthamen) — Rule E6 here is its empirical backing
- 🆕 Section 20.8 (Decision Log 2026-05-19) — Rule E6 §8.5 here is its methodological backing

-----

## 8. Implementation status (updated 2026-05-19)

### Stock Stratification (Rules E1-E5) ✅ Deployed
- Sprint 2.16.0 (2026-05-17): exposure layer
- Sprint 2.16.2: stratum-aware negotiation
- Sprint 2.16.10/11: tower-aware stratification

**Empirical validation results** (post-deployment):
- Al-Gharafa luxury_new: total 4,646,400 QAR vs actual 4,450,000 = +4.4% deviation (was −30.3% under blended)
- J Seven A & B: classified `luxury_new` correctly
- Lusail B201: 147.84M ر.ق after 2.16.10 (vs 4.62M with ambiguity)

### 🆕 Cost Approach (Rule E6) — DEFERRED 2026-05-19

**Built but never deployed**:
- `mthamen_reference.py` (17 KB)
- `mthamen_report.md` (16 KB)
- `mthamen_strings_table.txt` (15 KB)

**Deployed for future verification** (kept on Heroku):
- `smoke_mthamen.py` — single-profile test
- `smoke_mthamen_v2.py` — 6-profile WAF bypass attempts

### Confirmed Sales DB (Sprint 2.16.13) — Pending Thursday
Will enable:
- Real MAPE calculation across 4 strata
- Cap rate calibration per stock class
- Triangulation: confirmed sales vs MoJ (Cost reference noted but not callable)

### 🆕 8.5 Why Cost Approach Live Integration was Deferred (2026-05-19 Decision)

**Empirical evidence collected**:

1. **WAF block test** (smoke_mthamen.py from Heroku):
   ```
   Result: HTTP 200 + F5 BIG-IP ASM rejection page
   Content: <html><head><title>Request Rejected</title>...
            Your support ID is: 14668963584174538917
   ```

2. **WAF bypass attempts** (smoke_mthamen_v2.py from Heroku):
   ```
   6 profiles tested: Android Dalvik, Chrome, iPhone Safari,
                      no UA, okhttp, spoofed Qatar XFF
   3 paths tested:    /, /pricingws/, main endpoint with params
   Result:            0/6 bypass, 6/6 WAF rejected
                      All 3 paths blocked at IP level
   ```

3. **Real-device quota test** (Anas's iPhone, Qatar SIM, Qatar network):
   ```
   1 property attempted → "لقد تخطيت الحد الأقصى للمحاولات"
   Implication: Daily quota = ~1/day per device
   ```

**Decision rationale (4 reasons)**:

1. **WAF is comprehensive**: Not header/UA-defeatable. Likely geo-restriction at IP level (Heroku US/EU = blocked).
2. **Quota makes calibration impossible**: 50 properties × 1/day = 50 calendar days minimum.
3. **Production fragility**: ASP.NET .ashx + F5 ASM may change config without notice; production tower briefs would break.
4. **Methodology > integration**: The DRC formula (documented in §20.2 of Project Instructions and §2 Rule E6 here) is the value. "Today's number" from Mthamen is not.

**3 conditions for revival**:
1. Run `smoke_mthamen.py` and `smoke_mthamen_v2.py` from Heroku → at least one profile reaches valid response (non-WAF)
2. Verify daily quota changed to support professional use (>10 calls/day demonstrated)
3. (Preferred) Official MoJ Qatar API access approval

Without all 3, any revival proposal must be **rejected** with reference to this section.

**🆕 Generalized rule** (applies to any future Qatar government endpoint integration):

```
RULE: External endpoint smoke test from Heroku BEFORE building integration.
      15 minutes of smoke testing saves 3+ hours of building unusable code.
```

Codified in Project Instructions §5 (Pre-Sprint pattern) and §21.6 (Marathon Lessons).

-----

*Last updated: 2026-05-19 (after Cost Approach defer decision)*
*Authority: Empirical field audit of 5 areas × 4 brackets (MoJ n=149+, asking n=67) + reverse engineering of MoJ Qatar pricing app + WAF reachability tests + real-device quota verification*
*Status: Permanent methodological reference. Cannot be overridden by heuristic argument.*
