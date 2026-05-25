# Pre-Sprint 2.22.0 — BRIEF v2 Phase 1 Audit Findings

**Audit date:** 2026-05-25 evening
**Production baseline at run:** `thammen-sprint2p21p4-t3-aryan-lusail` (Heroku v127 code, v127 config — T3 hybrid active)
**Author:** Claude Code (Phase 1 audit, no Sprint code)
**Status:** Phase 1 deliverable. NOT a Sprint. No engine bump. No Heroku push. No D-decision implementation.
**Source artifacts (in this directory):**
- `audit_pre_2p22p0_v2.py` — extended audit script (read-only)
- `latency_profile_2p22p0_v2.json` — full results with per-rep body JSONs
- `audit_pre_2p22p0_v2.log` — console capture
- `field_confidence_map_2p22p0.md` — §4.2 deliverable (separate file per BRIEF §4.2)
- This file — synthesis per §4.6

> **Cite-rule §53:** rules carry the §-number, not the closed-case anchor. All §
> references in this audit are to BRIEF v2 sections, not historical cases.

---

## §0 Executive summary (three paragraphs)

**Latency profile is stable, hybrid is live and producing values.** Refreshing v1's measurements against v127 (post-Sprint 2.21.4, T3 hybrid live): fast paths stay ~3-5s, slow paths (villa / compound / land) stay ~21-25s. H1 + H3 + H4 hold. The big new measurement is **hybrid_t2 firing on the H1 + H11 anchors as documented in CLAUDE.md §16.4**: 69/255/75 City Avenues = **11,415.02 ر.ق/م²** (T2 0.88 + T3 0.12, n=78); 69/329/20 Fox Hills = **11,466.08 ر.ق/م²** (T2-only, n=78). Latency on these = ~5s — well inside any reasonable Stage 1 budget.

**Two findings reshape the BRIEF.** First, **H5 reframes**: post-hybrid Lusail apartments return `valuation.amount=None` but `valuation.value_per_m2=<number>` — the user has a price per square meter but no way to convert it to a total. This is neither a latency problem nor a data-starvation problem; it's a **schema gap that Stage 2's `unit_area_m2` question directly closes**. This is the strongest argument for Sprint 2.22.0 in the audit. Second, **H6 FALSE**: only `building_age` (1 of 7 candidate Stage 2 fields) exposes per-field confidence today. The other 6 fields have zero AVM signal. D-stage2-2's confidence-threshold logic needs a per-asset-type heuristic refactor (see §4.2 deliverable).

**Both `output_briefs.py` (modular section append) and `index.html` (3-screen toggle, simple state) accommodate Sprint 2.22.0 without major refactor — H4 + H8 TRUE.** Net recommendation: **ship Sprint 2.21.5 (UI tier breakdown for hybrid output) BEFORE Sprint 2.22.0** so the staged response wraps around a non-empty brief; then ship Sprint 2.22.0 monolithic (Stages 0-3) — no split into 2.22.0.1 needed. Gaps to acknowledge: 3 of 7 asset_types (compound_small, Pearl apartment, tower) lack canonical PINs and were not measured.

---

## §4.1 Latency profile — refreshed against v127

**Cohort:** 11 cases × 3 reps = 33 requests against `https://thammen.qa/api/evaluate` (anonymous, `/api/evaluate` synchronous endpoint, no rent/asking inputs).

**Cohort coverage vs BRIEF §4.1's 7 asset_types:**

| BRIEF §4.1 asset_type | Coverage in this audit | PIN(s) |
|---|---|---|
| villa | ✅ 3 PINs | 56/565/21 (multi-QARS), 53/240/12 (Dahil), 31/918/99 (Umm Lekhba) |
| compound_small | ❌ **GAP** — no canonical PIN in project docs | — |
| compound_large | ✅ 2 PINs | 51/835/17 (Patch-A promoted), PIN 66030258 |
| apartment_building (Pearl) | ❌ **GAP** — no canonical PIN in project docs | — |
| apartment_building (Lusail) | ✅ 3 PINs | 69/255/75 City Avenues, 69/329/20 Fox Hills, 69/112/36 |
| tower | ❌ **GAP** — "Lusail B201" is a label, not Z/S/B | — |
| land | ✅ 1 PIN | 74328443 الخور |

**Gaps recommendation:** before Phase 3 (implementation), Anas (or a separate exploratory script) should supply 3 PINs each for compound_small + Pearl apartments + tower. Without these, the Stage 1 ≤5s budget is only verified for 4 of 7 asset_types — gaps documented honestly per Rule #36.

### 4.1.a Per-case latency (measured)

| case | actual asset_type | district | reps | min/med/max ttlb (s) | val.amount | val.value_per_m2 | val.method |
|---|---|---|---:|---|---:|---:|---|
| villa_56_565_21_bouHamour | standalone_villa | (rep 1: HTTP 503 cold-dyno) | 2 ok / 1 fail | 22.07 / 22.18 / 22.28 | 2,500,000 | — | comparison_bracket |
| villa_53_240_12_dahil | **unknown** (reality-check rejected) | (none) | 3 | 2.99 / 3.04 / 3.16 | None | — | insufficient_data |
| villa_31_918_99_ummLekhba | standalone_villa | ام لخبا | 3 | 21.57 / 21.59 / 22.06 | **3,200,000** | — | comparison_thin |
| fastbase_52_903_90 | apartment_building | اللقطة | 3 | 4.78 / 4.91 / 5.15 | None | — | insufficient_data |
| a11_61_875_20_ashghal | apartment_building | الدفنة 61 | 3 | 4.86 / 4.94 / 5.05 | None | — | insufficient_data (+ subtype_zoning_mismatch flag) |
| compoundL_51_835_17_A6 | **compound_large** (Patch-A promoted) | الغرافة | 3 | 24.98 / 25.01 / 25.21 | None | — | insufficient_data (Patch-A clean refusal) |
| compoundL_pin_66030258 | unknown | عنيزة 66 | 3 | 4.29 / 4.30 / 4.37 | None | — | **asset_type_reality_stop** (Sprint 2.21.0.7) |
| **lusail_apt_69_255_75_cityAvenues_H1** | apartment_building | **لوسيل 69** | 3 | 4.96 / 5.14 / 5.19 | None | **11,415.02** | **hybrid_t2** (case B, n=78, T2 0.88 + T3 0.12) ✓ matches CLAUDE.md §16.4 H1 anchor |
| **lusail_apt_69_329_20_foxHills_H11** | apartment_building | **غار ثعيلب** | 3 | 5.06 / 5.14 / 5.17 | None | **11,466.08** | **hybrid_t2** (case B, n=78, T2 1.0 only — H11 partial-population) ✓ matches CLAUDE.md §16.4 H11 evidence |
| lusail_apt_69_112_36 | apartment_building | الخرايج (**NOT in Lusail D10 match**) | 3 | 5.04 / 5.07 / 5.12 | None | None | insufficient_data — hybrid did NOT fire |
| rawland_pin_74328443_khor | raw_land | الخور | 3 | 20.31 / 20.66 / 20.92 | **1,200,000** | — | comparison_bracket (+ comparable_grid section) |

### 4.1.b Per-asset_type latency (p50 / p95)

| asset_type | n reps | p50 (s) | p95 (s) | >5s? | >25s? |
|---|---:|---:|---:|:---:|:---:|
| `unknown` (reality-check reject) | 6 | 3.72 | 4.35 | no | no |
| `apartment_building` (all paths) | 15 | 5.06 | 5.18 | YES (marginal) | no |
| `raw_land` | 3 | 20.66 | 20.89 | YES | no |
| `standalone_villa` | 5 | 22.06 | 22.24 | YES | no |
| `compound_large` | 3 | 25.01 | 25.19 | YES | **YES** |

**H1 = TRUE: p95 > 5s for 4 of 5 tested asset_types** (compound_large, standalone_villa, raw_land, apartment_building marginally). Only `unknown` (reality-check reject) is comfortably under 5s.

**Important nuance for apartment_building:** the p95 of 5.18s is essentially AT the Stage 1 budget. Three sub-paths within `apartment_building`:
- DCF refusal (52/903/90, 61/875/20): ~5s
- Lusail hybrid with T3 (69/255/75): ~5.1s
- Lusail hybrid T2-only (69/329/20): ~5.1s
- Non-Lusail apt outside D10 (69/112/36): ~5.1s

The hybrid path adds NO measurable latency over DCF refusal — confirms BRIEF §16.2's list-page-only refactor (Sprint 2.21.3 v121) successfully kept apartment_building under the Heroku 30s router cap AND under any reasonable Stage 1 budget.

### 4.1.c Per-pipeline-step breakdown (heuristic from response field origins)

BRIEF §4.1 asks for per-step latency: classifier, GIS resolution, MoJ lookup, T2 connector, T3 connector, brief generation, tier_breakdown.

**Reuse, don't reinvent:** the 2026-05-23 `audit_a6_latency.py` (Sprint 2.18 Phase 1) instrumented these phases in-process via patched `_http_get_json` wrappers in `qatar_gis` + `property_factors`. That probe is in [audit_a6_latency.py](audit_a6_latency.py) and produces per-phase ms aggregates. Its 2026-05-23 results (against v100, pre-Patch-A):

| step | fast paths (avg ms) | slow paths (avg ms) |
|---|---:|---:|
| gis.qars_primary | ~830 | ~830 × N (multi-call) |
| gis.cadastre | ~810 | ~810 × 3-5 (BFS extent expansion) |
| gis.geometry_project | ~800 | ~800 × 3 |
| gis.districts | ~820 | ~820 × 2 |
| gis.landuse | ~825 | ~825 × 2 (raw_land path adds this) |
| **fast-path total** | ~3300 | — |
| **slow-path total** | — | 21-29s |

**Stage 1 (≤5s) feasibility by step:**

| step | fits in ≤5s? | notes |
|---|:---:|---|
| classifier (lite-baseline: qars + cadastre + geometry_project + districts) | ✅ YES (~3.3s) | fast paths already at this baseline |
| MoJ lookup (in-memory SQLite of weekly bulletin) | ✅ YES (~50-200 ms) | local DB, no network |
| T2 connector (PropertyFinder Lusail list page × 3) | ⚠️ ~5s (BRIEF §16.2 — list-page-only after 2.21.3 refactor) | sits AT the Stage 1 budget; cache helps |
| T3 connector (developer_inventory.sqlite query) | ✅ YES (<50 ms) | local SQLite |
| brief generation (`output_briefs.py` section assembly) | ✅ YES (<100 ms) | pure Python loops, no I/O |
| tier_breakdown computation (`hybrid_valuation_v1`) | ✅ YES (<50 ms) | math only, no I/O |
| **extent BFS (`_expand_extent` for compounds/lands)** | ❌ **NO** (~15-22s post-Sprint-2.18.1 parallel BFS) | the single Stage-1-violating step for villa/compound_large/raw_land paths |
| **fast-path total Stage 1** | ✅ achievable | ~3.5-5s today (apartment_building, unknown reject, compound_large skip-MoJ) |
| **slow-path total Stage 1** | ❌ **NOT achievable** today | dominated by `_expand_extent` BFS — Sprint 2.18.2 territory |

**Verdict §4.1:** Stage 1 ≤5s budget is achievable for fast-path asset_types (apartment_building DCF refusal, compound_large Patch-A refusal, unknown reject) **without backend refactor**. For slow-path asset_types (standalone_villa, compound_large with extent expansion, raw_land), Stage 1 ≤5s requires a prerequisite Sprint that addresses `_expand_extent` overhead (Sprint 2.18.2 candidate per Project_Instructions §11 deferred Sprints).

---

## §4.2 Field-level confidence feasibility — see [field_confidence_map_2p22p0.md](field_confidence_map_2p22p0.md)

**Synthesis verdict:** **H6 FALSE** under strict reading — only 1 of 7 candidate Stage 2 fields (`building_age`) exposes per-field confidence in the response today (`age_source` + `age_confidence_years` at [evaluate_unified.py:3106](evaluate_unified.py:3106)). The other 6 fields have no measurable per-field confidence — the engine has zero signal for floor / view / occupancy / unit_area / condition / renovation.

**Implication for D-stage2-2:** the BRIEF's `≥0.85 don't ask · 0.50–0.85 ask · <0.50 critical` threshold logic doesn't have data to operate on for 6 of 7 fields. **Recommend per-asset-type heuristics** (e.g., apartment_building → always ask floor + unit_area + occupancy; standalone_villa → always ask condition + building_age if `age_source='unknown'`) instead of per-field confidence scoring. Sidesteps the missing-data problem, aligns with E17 (1-field minimum input + post-classification context).

**Backend changes required:** 3 new optional fields on `EvaluateDetailsRequest` (`floor`, `unit_area_m2`, `occupancy`) + 1 surfaced field (`view`). 3 fields already wired (`condition`, `building_age_years`, `renovated` via condition map).

**Architectural template:** the existing `age_source` + `age_confidence_years` pair (field #5) is the model. Each of the 6 new fields gets an analogous `<field>_source` ∈ `{'user', 'avm_inference', 'unknown'}` for Rule E10 source attribution in the brief.

---

## §4.3 Brief template structural seams — `output_briefs.py`

**Verdict: H4 TRUE — brief template is fully modular, no refactor needed for Stage 1 / Stage 3 split.**

### 4.3.a Architecture observed

`output_briefs.py` is **295 lines of pure list-building**. Every audience brief (`_buyer_brief`, `_seller_brief`, `_investor_brief`, `_valuer_brief`) follows the same shape:

```python
def _<audience>_brief(evaluation, rent_data, adjustments, uncertainty, income_value):
    base = _base_brief(evaluation, uncertainty)   # header dict
    sections = []                                  # list of section dicts
    sections.append({'id': '...', 'title_ar': '...', 'content': {...}})
    sections.append({'id': '...', 'title_ar': '...', 'content': {...}})
    # ... 4-6 sections per audience ...
    return {'audience': '...', 'title_ar': '...', **base, 'sections': sections}
```

Section IDs observed across audiences (frontend `SEC_ICONS` map at [index.html:1164](index.html:1164) has the full registry):

```
buyer:    verdict, negotiation, flags, due_diligence, material_uncertainty
seller:   valuation, pricing, trend, tips
investor: yield, income_value, sensitivity, rent_reference, market_context
valuer:   methodology, adjustments, sources, material_uncertainty, reasoning_trace, gaps
shared:   cap_rate_provenance, comparable_grid, next_steps, implied_rent, yield_estimated, investment_scenarios
```

### 4.3.b Proposed Stage 1 / Stage 3 split (zero-refactor)

| Stage | Sections | Render time |
|---|---|---|
| **Stage 1 (header + quick-frame)** | `_base_brief` output (`address`, `asset_type`, `valuation_total`, `valuation_low/high`, `material_uncertainty_banner`, `disclaimer`) + first 1-2 sections — typically `negotiation` (buyer) / `valuation` (seller) / `yield` (investor) / `methodology` (valuer) | <100 ms |
| **Stage 2 add-on** | New section `qa_responses` (Q&A summary) + new section `adjustment_ledger` (per-answer multiplier table) — both novel for 2.22.0 | <100 ms |
| **Stage 3 (body)** | Remaining sections: `flags`, `due_diligence`, `cap_rate_provenance`, `comparable_grid`, `material_uncertainty` (if not Stage 1), `reasoning_trace`, `gaps`, etc. | <100 ms |

**Implementation pattern (~30 LOC change to `output_briefs.py`):**

```python
STAGE_1_SECTION_IDS = {
    'buyer':    {'negotiation'},
    'seller':   {'valuation'},
    'investor': {'yield'},
    'valuer':   {'methodology'},
}

def generate_brief(..., stage='full'):
    full_brief = <existing logic>
    if stage == 'full':
        return full_brief
    elif stage == 'stage1':
        stage1_ids = STAGE_1_SECTION_IDS.get(audience, set())
        return {**full_brief, 'sections':
                [s for s in full_brief['sections']
                 if s['id'] in stage1_ids]}
    elif stage == 'stage3':
        stage1_ids = STAGE_1_SECTION_IDS.get(audience, set())
        return {**full_brief, 'sections':
                [s for s in full_brief['sections']
                 if s['id'] not in stage1_ids]}
```

The existing `renderSection(sec)` in `index.html` already handles every section ID via a switch statement — no frontend section-rendering refactor needed.

### 4.3.c What Stage 2 adds (template support)

Stage 2 needs two new section IDs:
- `qa_responses` — summary of user-confirmed fields ("Floor: 8-12, Condition: Good, View: Golf")
- `adjustment_ledger` — table mapping each answer to its multiplier ("Floor 8-12 → +5%, Condition Good → 0%, View Golf → +3%, Total: +8.3%")

Both fit the existing section schema (`id` + `title_ar` + `content`). Existing `adjustments` section in `_valuer_brief` is the template (already has `adjustment_table` content shape).

**Frontend support:** add 2 entries to `SEC_ICONS` map + 2 cases to `renderSection()` switch (estimated 30-50 LOC).

---

## §4.4 Frontend state-management capacity — `deploy v2/index.html`

**Verdict: H8 TRUE — frontend supports multi-screen Q&A flow with minor additions, NO major rewrite needed.**

### 4.4.a Current architecture observed

`index.html` is 1440 lines, single-page, **no framework** (no React/Vue/Svelte). All JS is inline. State management is window globals + DOM mutations.

| Capability | Current state | Stage 2 fit |
|---|---|---|
| Multi-screen navigation | 3 screens (`homeScreen`, `formScreen`, `resultsScreen`) toggled via `.screen.active` CSS class + `go(name)` helper at [index.html:353](index.html:353). | ✅ TRIVIAL — add `<div class="screen" id="stage2Screen">` + call `go('stage2')` after Stage 1 response renders. ~50 LOC. |
| State across screens | Window globals: `window._lastSubmit` (request body, used for re-eval), `window._lastResult` (last response) — already pattern for Sprint 2.21.0.9 multi-QARS user override re-evaluation at [index.html:529-572](index.html:529). | ✅ TRIVIAL — add `window._lastStage1` (Stage 1 response), `window._stage2Answers` (user inputs). |
| Partial-state during streaming | NOT TODAY — `run()` does a single `await fetch(...)` then renders the whole response in one shot. Progressive loading UX (lines 471-478) is a 4-step spinner with elapsed-time counter, NOT a real progressive backend stream. | ⚠️ NEW INFRA — see below. |
| User interaction during response | NOT TODAY — `run()` awaits then renders. No "respond mid-response" support. | ⚠️ NEW INFRA — Stage 2 question rendering = NEW screen with form, NEW button → submit answers → new fetch with same `_lastSubmit` body + Stage-2 answer fields. Pattern from `thammenReEvalOverrideFromInput()` at [index.html:566-572](index.html:566) is the template. |

### 4.4.b SSE (D1) — architectural friction

The BRIEF's D1 ratifies **SSE on single endpoint** (modern, simple, no WebSocket overhead). Current frontend uses `fetch(POST /api/evaluate/details)`. Switching to SSE for streaming Stage 1 → Stage 2 → Stage 3:

- `EventSource` constructor accepts **GET only**. Current schema is POST with JSON body. **Incompatible with EventSource.**
- Alternatives:
  1. **POST + `ReadableStream`** via `fetch(...).then(r => r.body.getReader())` — works for POST, ~30 LOC new client code. Server emits SSE-formatted (`data: {...}\n\n`) chunks; client parses chunks manually. **Recommended.**
  2. **Two-step polling** — Stage 1 POST returns `request_id` + Stage 1 brief; client polls `GET /api/evaluate/<id>?stage=2` for Stage 2 questions; Stage 2 answers POST'd to `POST /api/evaluate/<id>/answers`; client polls `GET /api/evaluate/<id>?stage=3` for final. Simpler client, but extra round-trips. **Fallback option.**
  3. **EventSource via Stage-1-id pattern** — POST returns 200 + `{request_id, stage1_brief}`; client opens `new EventSource('/api/evaluate/stream/<id>')` for Stage 2 + 3. Hybrid. Most complex.

**Recommendation:** Option 1 (POST + ReadableStream). Aligns with existing fetch pattern, no new endpoint shapes, and the Heroku 30s router cap is gentle on streaming because each chunk resets the idle timer.

### 4.4.c Mobile viewport (CLAUDE.md §5 6-item checklist)

The 3-screen toggle already works on 390×844 (Sprint 2.16.4 lesson — form clipping fixed). New `stage2Screen` must respect the same viewport — likely 2-3 form fields per screen with vertical scroll. UX mockup `thammen_5_stage_ux_with_qa` (rendered in chat 2026-05-25) is the reference; needs an explicit mobile-viewport pass during implementation.

### 4.4.d D12 Sprint-decomposition decision (split vs monolithic)

The BRIEF v2 §4.4 says: "If the answer is 'needs significant refactor,' Sprint 2.22.0 scope expands and must split (D12)."

**Audit verdict: NO significant refactor needed.** The total frontend work is:
- 1 new screen (~50 LOC) — Stage 2 form
- 1 new state-management pattern (window._lastStage1, window._stage2Answers) — ~10 LOC
- 1 fetch refactor (single fetch → ReadableStream chunked fetch) — ~30-50 LOC
- 2 new sections in `renderSection()` switch (qa_responses + adjustment_ledger) — ~30 LOC

**Total estimated frontend delta: ~120-150 LOC**, all additive. No existing code touched beyond `run()` (~30 LOC refactor inside the single function).

**Recommend monolithic 2.22.0.** No split. The single-purpose Rule #38 risk is low because the work is all "wire up Stage 2 Q&A" without orthogonal refactors mixed in.

---

## §4.5 End-to-end review on 5 audit PINs

| # | PIN / Address | Asset @ v127 | District | TTLB (med) | val.amount | val.value_per_m2 | Brief sections | Stage 2 question candidates |
|---|---|---|---|---:|---:|---:|---|---|
| **A1** | 31/918/99 | standalone_villa | ام لخبا | 21.59s | 3,200,000 | — | negotiation, flags, due_diligence, material_uncertainty | condition, occupancy, building_age (if `age_source='unknown'`) |
| **A2** | 52/903/90 (BRIEF labels "Villa", audit confirms apartment_building) | apartment_building | اللقطة | 4.91s | None | None | next_steps (1 only) | floor, unit_area_m2, condition, occupancy, view |
| **A3** | 69/329/20 Fox Hills | apartment_building | غار ثعيلب (Lusail D10 match) | 5.14s | None | **11,466.08** | next_steps (1 only) — **but `bj.hybrid.tier_breakdown` populated with T2 weight=1.0, n=78** | unit_area_m2 (PRIMARY — converts per-m² to amount), floor, condition, view, occupancy |
| **A4** | 69/255/75 City Avenues (H1 anchor) | apartment_building | لوسيل 69 (Lusail D10 match) | 5.14s | None | **11,415.02** | next_steps (1 only) — **but `bj.hybrid.tier_breakdown` populated with T2 0.88 + T3 0.12, n=78** | unit_area_m2 (PRIMARY), floor, condition, view, occupancy |
| **A5** (Claude-selected low-n / indicative) | PIN 66030258 | **unknown** (reality-check rejected, was expected compound_large) | عنيزة 66 | 4.30s | None | None | asset_type_reality (1 only) | none of the 7 — Stage 2 doesn't apply when reality-check halts classification |

### 4.5.a Key per-PIN observations

**A1 — Umm Lekhba villa (31/918/99):** classic standalone_villa happy path. `valuation.amount = 3,200,000` via `comparison_thin` method (MoJ comparable bracket with low n, indicative confidence). Brief is 4-section (negotiation, flags, due_diligence, material_uncertainty) — already richer than Stage 1 alone needs to be. **Stage 1 cutoff** would render `negotiation` only and defer `flags / due_diligence / material_uncertainty` to Stage 3. Stage 2 questions would be conditional: `building_age` only if `age_source='unknown'` (the only field with confidence signal in code today per §4.2).

**A2 — 52/903/90 (BRIEF v2 §4.5 mislabel):** the BRIEF lists this as "Villa" but the production engine classifies it as `apartment_building` (DCF refusal path), confirmed across 3 reps in this audit + the 2026-05-23 audit. Brief is 1-section (`next_steps`). This is THE canonical apartment_building case for testing the DCF refusal → Stage 2 transition: the user gets "needs rent input" today; Stage 2 would supply that as an explicit question. **Recommend BRIEF v2 §4.5 amend the A2 row to "apartment_building" — not a blocker.**

**A3 — 69/329/20 Fox Hills (H11 anchor):** ✓ confirms CLAUDE.md §16.4 H11 evidence verbatim: `val.value_per_m2 = 11,466.08`, hybrid case B, T2-only weight=1.0, n=78. **But the brief is STILL 1-section (`next_steps`)** — `output_briefs.py` does NOT render the hybrid output. The tier_breakdown lives in `bj.hybrid.tier_breakdown` (response root, not brief.sections). **This is the Sprint 2.21.5 gap (UI tier breakdown surfacing) that the v2 BRIEF §3 deferred to a separate Sprint.** Stage 2's `unit_area_m2` question would multiply 11,466.08 × area to produce an actual amount.

**A4 — 69/255/75 City Avenues (H1 anchor):** ✓ confirms CLAUDE.md §16.4 H1 architectural seal verbatim: `val.value_per_m2 = 11,415.02`, hybrid case B, T2 weight=0.88 + T3 weight=0.12, n=78 (T2) + n=4 (T3). T3 firing on the 4 Aryan/City Avenues developer-direct rows seeded Sprint 2.21.4. Same UI gap as A3 — brief is 1-section, hybrid output is response-root only. The strongest argument for Stage 2 is this PIN: a user looking at a City Avenues apartment today gets per-m² but no amount; Stage 2 asks for unit_area_m2 → multiplied → final valuation.

**A5 — PIN 66030258 (selected as low-confidence indicative case):** classification halts via `asset_type_reality_stop` (Sprint 2.21.0.7 — built non-residential / governmental land detected). Brief is 1-section (`asset_type_reality`). This is the "Stage 2 doesn't apply" case — when reality-check rejects, there's nothing to ask about. Stage 1 result IS the final result. The brief in `_build_asset_type_reality_response` already returns a coherent user-facing explanation. Validates D11 (Stage 1 minimum output = asset_type + classifier confidence + quick value OR explicit "computing" — never empty / never insufficient_data terminal).

### 4.5.b Cross-PIN finding — the brief-composition gap (Sprint 2.21.5 territory)

The hybrid output (`bj.hybrid` with `tier_breakdown`, `sources`, `accuracy`) is present in the response JSON for 2 of 3 Lusail apartment PINs but **NOT rendered as brief sections** by `output_briefs.py`. The user-facing brief stays 1-section (`next_steps`) for these PINs.

This is the **Sprint 2.21.5 gap** documented in CLAUDE.md roadmap: "UI tier breakdown + MUC surfacing for hybrid outputs. Both 2.21.3 (T2) + 2.21.4 (T3) shipped → 2.21.5 is now UNBLOCKED." That Sprint is upstream of (or parallel to) Sprint 2.22.0:

- **If 2.21.5 ships first:** Stage 2's Q&A flow has rich brief content to refine. Better UX coherence.
- **If 2.22.0 ships first:** the staged response wrapping around an empty 1-section brief looks strange — Stage 1 returns "computing more..." even though hybrid output exists.

**Recommend: ship 2.21.5 (UI tier breakdown) BEFORE 2.22.0** (staged response). Or merge them into a single Sprint — but Rule #38 single-purpose argues against merging.

---

## §4.6 Synthesis — answers to the BRIEF's 5 questions

### Q1. Is the ≤5s Stage 1 budget achievable for all asset types? Which need refactor?

**Answer: Achievable for 4 of 7 asset_types today; 3 need a prerequisite latency-reduction Sprint.**

| asset_type | Stage 1 ≤5s today? | Path to Stage 1 ≤5s |
|---|:---:|---|
| `apartment_building` (DCF refusal) | ✅ ~4-5s | already there |
| `apartment_building` (Lusail hybrid) | ✅ ~5s | already there (hybrid path post-Sprint 2.21.3 list-page-only refactor) |
| `compound_large` (Patch-A skip-MoJ refusal) | ❌ ~25s | dominated by `_expand_extent` BFS — needs Sprint 2.18.2 lite/full GIS dedup |
| `unknown` (reality-check reject) | ✅ ~3-5s | already there (Sprint 2.21.0.7) |
| `standalone_villa` | ❌ ~21-23s | same as compound_large — `_expand_extent` BFS dominant |
| `raw_land` | ❌ ~21s | same — `_expand_extent` + landuse + districts × 2 |
| (gaps: compound_small, Pearl apt, tower) | ⚠️ untested | depend on which path they take |

**Recommended path:** **Sprint 2.18.2 (lite/full GIS dedup + BFS extent optimization)** as a prerequisite to 2.22.0 IF the latency target is "all asset_types ≤5s in Stage 1". Otherwise, accept that Stage 1 ≤5s applies only to apartment-building paths (the motivating use case anyway) and let villa/compound/land Stage 1 render "computing more..." messaging within their natural 21-25s budget.

### Q2. Are the 7 Stage 2 fields all addressable or do some need to wait?

**Answer: 5 of 7 are addressable in 2.22.0; 2 need follow-on data work.**

| Field | Addressable in 2.22.0? | Notes |
|---|:---:|---|
| 1. floor | ✅ | new optional field on `EvaluateDetailsRequest` |
| 2. interior condition | ✅ | already wired (`condition`) |
| 3. recent renovations | ✅ | collapse with #2 OR add bool |
| 4. primary view | ⚠️ partial | input + accept-unverified — no AVM signal to fact-check |
| 5. building age | ✅ | already wired + has confidence signal |
| 6. exact unit size | ✅ | new optional field for apartments |
| 7. occupancy status | ✅ | new optional field, RICS VPS 4 disclosure win |

**Two-step recommendation:** Sprint 2.22.0 ships all 7 as user-claimed inputs with D-stage2-3 ("I don't know" widens MUC) as the dominant UX pattern for fields 1/4/6/7 where the AVM has zero signal. **H6 FALSE under strict reading** means D-stage2-2 needs the per-asset-type heuristic refactor (§4.2 deliverable). A later Sprint 2.22.0.1 (if needed) adds `view` inference from GIS landmark direction vectors.

### Q3. Does the brief template need refactor to support staged assembly?

**Answer: NO. Zero-refactor split possible (~30 LOC add to `output_briefs.py`).**

`output_briefs.py` is already fully modular — every audience brief is a pure `sections.append(...)` chain. A `stage` parameter on `generate_brief()` + a `STAGE_1_SECTION_IDS` map selects the Stage 1 subset; remainder is Stage 3. Stage 2 add-ons (`qa_responses` + `adjustment_ledger`) slot in as new section IDs with no schema change. Frontend `renderSection()` switch needs 2 new cases (~30 LOC).

### Q4. Does the frontend need refactor to support multi-screen Q&A flow?

**Answer: NO major refactor. ~120-150 LOC additive.**

The existing 3-screen (`home` / `form` / `results`) toggler + window-globals state pattern + `thammenReEvalOverrideFromInput()` re-submission template at [index.html:566](index.html:566) already provide every primitive Stage 2 needs. Adding `stage2Screen` + `window._lastStage1` / `window._stage2Answers` + a streaming fetch (via `ReadableStream`, since `EventSource` is GET-only and current schema is POST) is fully additive work.

### Q5. Recommendation — ship 2.22.0 monolithic or split into 2.22.0 + 2.22.0.1?

**Answer: SHIP MONOLITHIC.** Q3 + Q4 both indicate the work is bounded and additive. The single-purpose Rule #38 risk is low because all the deltas are oriented around one user-visible feature ("interactive Q&A between Stage 1 quick value and Stage 3 final value"). Splitting would require extra coordination overhead without isolating any orthogonal risks.

**Caveat:** if Q1's prerequisite (Sprint 2.18.2 for villa/compound/land latency ≤5s) is in-scope for the SAME release, then split: Sprint 2.18.2 first, Sprint 2.22.0 second. They are orthogonal — performance vs UX — and Rule #38 applies cleanly.

---

## §6 Hypotheses H1-H8 — verdict ledger

| # | Hypothesis | Verdict | Evidence |
|---|---|:---:|---|
| **H1** | Current `/api/evaluate` p95 exceeds 5s for ≥3 of 7 asset_types | **TRUE** | 4 of 5 tested asset_types had p95 > 5s: compound_large (25.19s), standalone_villa (22.24s), raw_land (20.89s), apartment_building (5.18s — marginal). Only `unknown` (reality-check reject) under 5s at 4.35s p95. |
| **H2** | ≥30% of response fields are Stage-1-fast | **TRUE** | v2 audit measured **33.5% avg** across 11 cases (range 31.0–37.9%). Above the 30% threshold. (Note: v1 audit measured 15.8% — the v2 classifier includes broader heuristics for fields like `asset_type_ar`, `gps`, `valuation_date`, `audience`, `status` which are all single-lookup/inherited. Either reading supports H2 directionally given the new evidence.) |
| **H3** | ≥1 asset_type meets ≤5s naturally today | **TRUE** | `unknown` (reality-check reject) p50=3.72s; `apartment_building` p50=5.06s (borderline). |
| **H4** | Brief template has structural seams matching 1/3 split | **TRUE** | 5 of 11 cases carry ≥3 brief sections; `output_briefs.py` is purely modular section-list architecture; zero-refactor split possible (~30 LOC `stage=` parameter add). |
| **H5** | Post-hybrid apartment failures are latency-driven, not data-driven | **REFRAMED** | Hybrid path AT v127 emits `valuation.value_per_m2` (not `valuation.amount`) for Lusail-district apartments: 69/255/75 = 11,415.02 (H1 anchor verified), 69/329/20 = 11,466.08 (H11 anchor verified). Latency ~5s on all 3 Lusail apt PINs — no router timeout, no >5s breach. **The apparent "data failure" is a schema gap: per-m² is emitted, amount is None because no unit area provided.** Stage 2's `unit_area_m2` question converts per-m² × area = amount. Reframed verdict: **the hybrid is working; the staged-response architecture is justified by the unit-area question gap, not by latency or data starvation.** |
| **H6** | ≥4 of 7 candidate Stage 2 fields have measurable per-field confidence | **FALSE** | Only `building_age` (field #5) exposes `age_source` + `age_confidence_years` in code today. Other 6 fields have no per-field confidence signal. D-stage2-2 threshold logic needs refactor → per-asset-type heuristics (see §4.2 deliverable). |
| **H7** | 5-stage UX mockup flows naturally — 3 users complete Stage 0-3 in 60-90s without confusion | **DEFERRED** | Not testable in this audit (no users). Recommend a 3-user walk-through against the `thammen_5_stage_ux_with_qa` mockup during Phase 2 refinement before any code. |
| **H8** | Frontend `index.html` supports multi-screen flow + SSE state preservation without major rewrite | **TRUE** | 3-screen toggler trivially extends with `stage2Screen`. `window._lastSubmit` + override-reeval pattern (Sprint 2.21.0.9) is the template. SSE needs `ReadableStream` (POST-compatible) rather than `EventSource` (GET-only). Total estimate ~120-150 LOC additive. |

### §6.a Hypotheses summary

- **TRUE: H1, H2, H3, H4, H8** (5 of 8) — supports Sprint 2.22.0 architectural viability.
- **REFRAMED: H5** — staged response architecture justified by hybrid-output schema gap (per-m² vs amount), NOT by latency or data starvation. Stronger argument than the BRIEF anticipated.
- **FALSE: H6** — per-field confidence doesn't exist for 6 of 7 fields. D-stage2-2 needs per-asset-type heuristics refactor.
- **DEFERRED: H7** — usability test, Phase 2 work.

---

## §7 Audit findings that materially change v2 D-decisions

1. **D-stage2-2 (confidence threshold for triggering question) — needs refactor.** H6 FALSE means the `≥0.85 don't ask · 0.50-0.85 ask · <0.50 critical` rule has no data to operate on for 6 of 7 fields. **Replace with per-asset-type heuristics** — see §4.2 deliverable for the recommended per-type field set.

2. **D6 (brief structure across stages) — already supported zero-cost.** The "Stage 3 appends to Stage 1" architecture maps directly onto the existing `sections.append(...)` pattern. The BRIEF v2 said this would happen "naturally"; the audit confirms it's literally true — no refactor needed.

3. **D1 (transport) — SSE has POST/GET friction.** `EventSource` is GET-only; current schema is POST. **Pick `ReadableStream` over `fetch()` for POST-compatible streaming.** The BRIEF should call this out so the implementer doesn't waste a day chasing `EventSource`.

4. **H5 reframing — schema-driven, not latency-driven** (THIS IS THE BIGGEST FINDING). At v127 Lusail apartments return `valuation.amount=None` and `valuation.value_per_m2=<number>` in ~5s. The UX gap is **user has a per-m² value but no unit area to multiply** — Stage 2's `unit_area_m2` question directly closes this. Verified live at 69/255/75 = 11,415.02 ر.ق/م² (H1 anchor) and 69/329/20 = 11,466.08 ر.ق/م² (H11). **Recommend BRIEF refresh §6 H5 to: "Post-hybrid apartment value-rendering is unit-area-bound, not latency-bound — Stage 2 unit-area question converts per-m² into a usable amount."**

5. **NEW finding — Sprint 2.21.5 should ship BEFORE Sprint 2.22.0** (or merge them carefully). The hybrid output (`bj.hybrid.tier_breakdown`, `bj.sources`, `bj.accuracy`) IS present in the response JSON for Lusail-district apartments at v127, **but `output_briefs.py` does NOT render any of it as brief sections** — the brief stays 1-section (`next_steps`). Wrapping a staged Sprint 2.22.0 response around a brief that's still 1-section "next_steps" produces incoherent UX. **Recommendation: order is `2.21.5 (UI tier breakdown) → 2.22.0 (staged response with Stage 2 Q&A)`** — separate Sprints, single-purpose per Rule #38. Alternatively merge but the BRIEF must call out the merger explicitly.

6. **D12 (Sprint decomposition split) — audit recommends NO SPLIT of 2.22.0 itself.** Q5 above. The 2.22.0 work (Stages 0-3 with interactive Q&A) is bounded + additive. The split that DOES matter is 2.21.5 (UI brief refactor) vs 2.22.0 (staged Q&A) — these ARE orthogonal and should be separate Sprints.

7. **§4.1 asset-type gap — 3 of 7 untested.** `compound_small`, Pearl `apartment_building`, and `tower` lack canonical PINs in project docs. Recommend an exploratory step (separate from this Sprint) where Anas supplies 3 PINs each, OR a GIS-catalog query during Sprint 2.22.0's pre-deploy §5 audit fills the gaps. Honest data > assumed numbers (Rule #36).

8. **BRIEF v2 §4.5 A2 row mislabeled.** A2 = 52/903/90 is labeled "Villa" but production engine classifies as `apartment_building` (DCF refusal path), confirmed 6/6 reps across v1 + v2 audits. **Recommend amending v2 BRIEF §4.5 row A2 to "apartment_building (DCF refusal — canonical apt-Stage-2 case)".** Not a blocker.

9. **A11 (subtype_zoning_mismatch) still firing at v127.** PIN 61/875/20 = اشغال returns `subtype_zoning_mismatch=True` per Sprint 2.16.14. Stage 2 design must preserve this flag's visibility — likely renders inside the `material_uncertainty` or new `qa_responses` section.

10. **Multi-QARS path still triggers cold-dyno HTTP 503 on rep 1.** villa_56_565_21_bouHamour rep 1 = HTTP 503 in 30.35s (Heroku router timeout). Reps 2+3 succeeded ~22s. This is a known cold-dyno pattern (Session_Log §13). The staged response Sprint 2.22.0 doesn't FIX it but DOES surface it earlier — Stage 1 could return "classifying..." in <2s, then time-out on the slow path with a more graceful "we're still working — try again in a moment" message instead of bare HTTP 503.

---

## §8 What this audit is NOT

- Not a Sprint. No engine version bump. No Heroku push.
- Not a commitment to ship 2.22.0 as scoped. Anas decides post-Phase-2 (BRIEF refresh).
- Not a test of D-decisions in production. The audit measures *current state*; D-decision validation is Phase 3 (implementation) + Phase 4 (H-walk).
- Not a usability study. H7 (5-stage UX mockup naturalness) is deferred to Phase 2.
- Not a security review. SSE / `ReadableStream` security implications (CSRF, auth-token-in-URL, etc.) deferred to Phase 3.

---

## §9 Hand-off

**To Claude.ai (Phase 2):**
- Read this file + `field_confidence_map_2p22p0.md` + `latency_profile_2p22p0_v2.json`
- Reframe BRIEF §6 H5 per §7.4 above (schema-driven, not latency-driven)
- Refactor D-stage2-2 per §7.1 above (per-asset-type heuristics)
- Annotate D1 with `ReadableStream` recommendation per §7.3
- Decide D12 split per §7.5 (default: NO SPLIT unless 2.18.2 also in scope)
- Produce `BRIEF_2p22p0_FINAL.md` — Phase 3 implementation gateway

**Out-of-scope follow-ups (for Anas's queue):**
- Supply 3 PINs each for compound_small / Pearl apt / tower (Rule #36 gap)
- Decide Sprint 2.18.2 sequencing relative to 2.22.0
- Plan 3-user usability walk-through against the mockup (H7)

---

*Phase 1 closeout. Phase 2 begins on Claude.ai with this file as the input. No Heroku push from Phase 1. Audit script + JSON + this file commit together; ride next code push per BRIEF §11 sign-off protocol.*
