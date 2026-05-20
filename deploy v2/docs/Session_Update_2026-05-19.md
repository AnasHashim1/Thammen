# Session Update — 2026-05-19 (Tuesday afternoon)

> **Type:** Append-only delta file. Does NOT replace the 3 main project files
> (`__Thammen__thammen_qa____Project_Instructions.md`,
> `__Session_Log___2026-05-17_to_19.md`,
> `__EMPIRICAL_FINDINGS___Methodology_Validation_2026-05.md`).
>
> **Why a separate file:** Today's session added one new bug discovery and
> one Sprint deployment. Rewriting 1700 lines of stable docs to inject ~50
> new lines is high-risk and token-expensive. This file appends the delta.
>
> **Reading order for future Claude sessions:** Read the 3 main files first
> for stable context, then this file for the most recent state (2026-05-19
> afternoon onward). When the next quiet period arrives (post-Thursday data
> arrival is a natural moment), consolidate this delta back into the main
> files.

-----

## 1. What happened today (2026-05-19 afternoon)

### 1.1 Mthamen defer decision — confirmed in morning

Already captured in main Project Instructions §20.8 and Session Log §5.
No changes to that decision.

### 1.2 Bug A11 discovered (afternoon)

User submitted a real evaluation of address `61/875/20` (the **Public Works
Authority** — هيئة الأشغال العامة, a clearly governmental/commercial tower
in الدفنة). thammen.qa returned `asset_type: "apartment_building"` and
offered an Income Approach valuation.

**GIS inspection revealed**:

```
QARS_Point.BUILDING_NO_SUBTYPE = 6  (Building with Flats)
QARS_Point.SURVEYED_DATE        = 2010-01-26   ← 16 years old
QARS_Point.DATE_LUPD            = 2012-02-20   ← last updated 14 years ago
Vector/Zoning.ZONING            = CCC  (Central Commercial Core)
Vector/Landmarks within 100m    = GOVERNMENT × 2 + FINANCE + GENERAL SERVICES
PIN                             = 61050014
GPS                             = 25.32070, 51.53189
```

Root cause: Sprint 2.16.6 Branch 0 (classifier in `qatar_gis.py`) trusts
QARS_Point `BUILDING_NO_SUBTYPE` as authoritative — correct in 91% of
cases, but stale 2010-2012 data for buildings whose use changed silently.
The classifier did not cross-check against zoning.

### 1.3 Pre-Sprint Audit (§5 compliance)

Quick GIS audit on 22 commercial landmarks (BUSINESS, FINANCE, GOVERNMENT):

| Category    | Total | Mismatch | Rate |
|-------------|------:|---------:|-----:|
| BUSINESS    |     6 |        0 |   0% |
| FINANCE     |     8 |        0 |   0% |
| GOVERNMENT  |     8 |        2 |  25% |
| **Total**   |    22 |        2 | 9.1% |

Two more confirmed cases beyond 61/875/20:
- `63/864/26` — Tower in CCC zone
- `61/820/84` — ApartBldg in CCC zone

Both had QARS_Point surveys dated 2010. Pattern: government buildings whose
use changed post-2010.

**Severity calibration**: 9.1% rate on GOVERNMENT category only, 0% on
Business/Finance → **Medium severity, not High**. The system already
handled this case with transparency (returned "تقييم مشروط — تحتاج بيانات
إضافية" instead of a wrong number), so the fix is additive (warning panel)
rather than corrective (reclassification).

### 1.4 Sprint 2.16.14 built, deployed, verified

Built end-to-end in the same session:
- `qatar_gis.py`: +80 lines (helpers + Branch 0 enhancement)
- `evaluate_unified.py`: +35 lines (4 injection points + scope-safe init + ENGINE_VERSION bump)
- `index.html`: +18 lines (warning panel, mirrors Sprint 2.16.9 MUC pattern)
- `test_sprint_2p16p14_zoning_mismatch.py`: new file, 21 tests, all pass
- `CHANGELOG_v35.md`: full documentation

**Tests**: 67/67 passing (46 regression + 21 new).

**Deploy verification (curl post-deploy)**:
```
engine_version: "thammen-sprint2p16p14-zoning-cross-check"  ✓
subtype_zoning_mismatch: { kind, message_ar, qars_subtype: 6,
                           classified_as: "apartment_building",
                           recommendation_ar, data_age_note_ar }  ✓
```

UI panel rendering: deferred to user browser confirmation (Cloudflare blocks
the Claude container from reaching thammen.qa directly).

-----

## 2. Edits to merge into main files (next consolidation pass)

### 2.1 → `Project_Instructions.md` §11 (Completed Sprints) table

Add this row before "Mthamen Analysis":

```
|2.16.14|v35|Zoning cross-check (Bug A11) — flag stale QARS subtypes|
```

### 2.2 → `Project_Instructions.md` §11 Deferred Sprints table

**Remove** the row for "2.16.14" if it was added (it wasn't — A11 was
discovered today and went straight to Sprint).

### 2.3 → `Project_Instructions.md` §18 (Known Bugs Catalogue)

Under 🟢 Resolved:
```
A11, ... → Sprints 2.16.6–2.16.14
```
Change "(11 bugs)" → "(12 bugs)" if counting precisely.

Under 🟠 High: A11 is NOT here (it was Medium, never High after audit).

Reaffirm: **Critical = 0**.

### 2.4 → `Project_Instructions.md` §22 (Self-Correction Triggers)

Add to the bulleted list:
```
- I trust QARS_Point subtype as single source without cross-checking
  Zoning → STOP, run the Sprint 2.16.14 cross-check pattern (§19 + Rule E7)
```

Add to recall phrases table:
```
| "تذكر Bug A11" | Zoning/Subtype contradiction discovery 2026-05-19 PM + Sprint 2.16.14 fix |
| "تذكر أشغال 61/875/20" | The reference case for Bug A11 |
```

### 2.5 → `EMPIRICAL_FINDINGS.md` — new Rule E7

Add after Rule E6 (Cost Approach reference):

```markdown
### 🆕 Rule E7 — QARS subtype requires Zoning cross-check for residential codes

✓ **Discovered 2026-05-19 PM** via field case (61/875/20 = Public Works
Authority) and 22-landmark audit.

**The empirical finding**: QARS_Point `BUILDING_NO_SUBTYPE` was last
surveyed 2010-2012 for most parcels. ~9.1% of GOVERNMENT-category
buildings have a residential subtype (1=Villa, 6=Flats, 11=Tower) but
sit in a clearly non-residential zone (CCC, COM, CF, SCZ, MU*, etc.)
because their use changed silently after the original survey.

**The rule** (deployed in Sprint 2.16.14, qatar_gis.py):
- Residential subtypes {1, 6, 11} + non-residential zone → emit
  `subtype_zoning_mismatch` flag, downgrade confidence to medium,
  add COMMERCIAL to alternative_types
- Do NOT change asset_type — surface the contradiction, let user decide
- Non-residential zone tokens: CCC, COM, CF, SCZ, TU, LFR, LInd, IND
- Any code starting with "MU" (Mixed Use) also counts as non-residential
- 0% false-positive on Business/Finance landmarks (validated)
```

### 2.6 → `Session_Log.md` — new section after §5

Add §6 with the timeline of 2026-05-19 afternoon (the build of 2.16.14).
Key content: PDF received → GIS audit → Bug A11 confirmed → 22-landmark
scope measurement → Sprint 2.16.14 build → 67/67 tests → deploy →
post-deploy curl confirms flag.

-----

## 3. Production state (end of 2026-05-19)

```
Engine version deployed:  thammen-sprint2p16p14-zoning-cross-check
Latest CHANGELOG:         CHANGELOG_v35.md
Latest Sprint:            2.16.14 (Zoning cross-check, Bug A11)
Tests passing:            67/67 (46 regression + 21 new)
Critical bugs open:       0
High bugs open:           2 (A6 latency, A8 comparable adjustments)
Medium bugs open:         3 (A2, A5, A7)
```

-----

## 4. What's coming this week (unchanged from Session Log §7)

### Thursday 2026-05-21 — Secretary delivers historical sales

- **Sprint 2.16.15** (renumbered from 2.16.13 since A11 took the 2.16.14 slot):
  Confirmed Sales DB Integration. Mthamen still excluded per §20.8 decision.

### Backlog (post-secretary)

| Order | Sprint | Description |
|-------|--------|-------------|
| 1 | 2.16.15 | Confirmed Sales DB integration |
| 2 | 2.17 | QARS local snapshot |
| 3 | 2.18 | A6 latency + async landmarks + BUA-aware sanity |
| 4 | 2.20 | A8 Comparable adjustments grid |
| 5 | 2.29 | MME apartments integration |

> NOT in backlog: Mthamen integration (deferred per §20.8).

-----

## 5. New self-correction triggers (effective immediately)

For any Claude session reading this file:

- **"تذكر Bug A11"** → Zoning/Subtype contradiction discovery 2026-05-19 PM,
  fixed in Sprint 2.16.14, qatar_gis.py `_is_non_residential_zone` +
  `_fetch_zoning_at_point` helpers + Branch 0 cross-check
- **"تذكر أشغال 61/875/20"** → The reference case (Public Works Authority)
- **"تذكر Rule E7"** → QARS subtype requires Zoning cross-check (in this file §2.5)
- **"تذكر Sprint 2.16.14"** → Bug A11 fix, deployed 2026-05-19 PM,
  CHANGELOG_v35

If any new session proposes treating QARS `BUILDING_NO_SUBTYPE` as a
single source of truth without zoning verification → STOP, this is the
exact pattern Bug A11 fixed.

-----

## 6. Open questions for Thursday

1. Will secretary's confirmed sales include any commercial transactions?
   If yes, we can validate cap rates for Bug A11 reclassifications (when
   user confirms "this is actually commercial, not residential").
2. Should the warning panel CTA include a "reclassify as commercial" button
   that re-submits with `asset_type_override=commercial`? Deferred — would
   require new pydantic field. Discuss after Thursday.
3. Long-term: should Thammen build its own snapshot of GIS Districts +
   Zoning + Landmarks layers? Sprint 2.17 was about QARS only; broader
   snapshot deferred.

-----

*This file appends to but does not supersede the 3 main project files.
When merging back: the §2 edits above are the canonical change list.
Last updated: 2026-05-19, ~18:00 Doha time.*
