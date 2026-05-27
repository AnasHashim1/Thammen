# BRIEF Sprint 2.22.0a KICKOFF — Implementation Spec

**Date drafted:** 2026-05-26 PM
**Status:** **DRAFT — awaiting Anas sign-off.** No code, no git commit, no Heroku push until signed (Rule #32: Anas signs briefs before code).
**Author:** Claude Code (Phase 3 Step 7 deliverable)
**Spec source-of-truth:** `BRIEF_2p22p0_FINAL_v3.1.md` (commit `cbb2730`) — §2 row 1 "2.22.0a"
**Audit basis:** `PHASE3_AUDIT_pre_2p22p0a.md` (commit `53cace0`) — 5/5 cases consistent vs Phase 1
**Production baseline:** `thammen-sprint2p21p4-t3-aryan-lusail` (Heroku v128 code, runtime unchanged from v127 — docs-only push of `a903350`)

> **What this brief is:** a derivation of the 2.22.0a scope cut from BRIEF v3.1 §2 row 1, with Q1-Q4 decisions integrated, acceptance criteria explicit, and architecture impact bounded. **This file becomes the contract for 2.22.0a code work — any drift from this spec during implementation requires a follow-up signed amendment.**
>
> **What this brief is NOT:** Sprint 2.22.0b/x/y design (those are separate kickoff briefs). Not a usability/UX spec for Stage 2 Q&A (deferred). Not a security spec for verification URL DB (deferred to 2.22.0.1).

---

## §0 One-paragraph summary

Sprint 2.22.0a delivers the **content + UX surface** half of Sprint 2.22.0, leaving the **architectural staging** half (streaming, multi-screen, density-gating logic) to 2.22.0b. Touches `evaluate_unified.py` + `output_briefs.py` + `index.html` + new `refusal_templates.py` + new `verification_url.py`. Ships: §1.6 dynamic refusal triggers with mandatory reason text (**5 active templates** — 4 inherited from BRIEF v3.1 + a NEW "density-gated district" for Pearl/non-D10 zones; `asset_uniqueness` trigger deferred to 2.22.y per §2.3 single-logical-unit decision), hybrid `tier_breakdown` UI rendering with `n_used` + freshness, tier renaming (`indicative_estimate` / `analytical_range` / `broker_verified_range` / `signed_valuation` — Stage-5 vocabulary even though Stage-5 isn't shipped), A2 reclassification documentation fix (52/903/90 labeled `apartment_building` per production reality), use-case banner per §6.7, verification URL generation (URL token only; full UI defers to 2.22.0.1), calculator-style visual differentiation for Stage-3 output, RICS Red Book 2024 / IVS 2024 text compliance pass on `material_uncertainty.py` wording. **No new endpoints. No schema breaks. ENGINE_VERSION bumps to `thammen-sprint2p22p0a-content-and-refusal-templates` (or short slug per existing convention).** Rollback target: Heroku v128 (current docs-only push state).

---

## §1 Scope — Stage-by-stage cuts in 2.22.0a

### §1.1 Stage 0 — Input (no change)
- (existing path preserved — PIN / Zone-Street-Building / map pin via Pydantic schemas with `extra='forbid'`)
- **Acceptance:** Pydantic validation unchanged. Phase 1 + Phase 3 §5 audit input cohort continues to work.

### §1.2 Stage 1 — Rapid context surface
Per BRIEF v3.1 §1 asymmetric latency ceiling:
- `apartment_building`, `unknown` → ≤5s p50
- `standalone_villa`, `compound_large`, `raw_land` → ≤10s p50

Backend in 2.22.0a (no new logic):
- Existing lite-path classifier + district resolution + MoJ baseline + T2/T3 connector summary

Frontend additions in 2.22.0a (content + tier labels):
- **ADD `tier_label = 'indicative_estimate'`** to Stage-1 response (when value present)
- **ADD per-field internal confidence indicators surfaced** as 3-dot ramp on UI (when `age_confidence_years` or similar already in response — wire existing data, no new computation)
- Statement copy: "تقدير سريع — التحليل العميق جاري" (per D7 ratified in BRIEF v3.1 §3) — text already exists, verify Arabic register

**Critical design property (D11 ratified):** Stage 1 NEVER returns terminal `insufficient_data`. Minimum output = `asset_type + classifier_confidence + (quick value OR refusal zone trigger per §1.6 OR explicit "computing more")`. **2.22.0a renders the refusal-zone-trigger case via §1.6 templates** (§5 of this kickoff brief). The "computing more" case is 2.22.0b streaming work.

**Acceptance §1.2:** Phase 3 §5 audit cases A1-A5 continue producing coherent Stage 1 surface output. A4 (PIN 66030258 reality-check) and A5 (Pearl tower 66/140/6) hit §1.6 refusal templates instead of generic `insufficient_data` copy.

### §1.3 Stage 2 — Full valuation surface
Per BRIEF v3.1 §1 latency 10-25s acceptable. Backend paths preserved (hybrid_t2 / comparison_thin / income_approach / multi-QARS villa / Patch-A compound_large refusal).

Frontend additions in 2.22.0a:
- **ADD `tier_label = 'analytical_range'`** for Stage-2 outputs
- **ADD `tier_breakdown` brief section** — renders existing `hybrid.tier_breakdown` array (T1/T2/T3 rows with weights, n, value_per_m2). Data already in response root; needs rendering hookup in `output_briefs.py` + `renderSection()` switch in `index.html`
- **ADD `n_used` + freshness timestamp surfacing** — per Finding §3.2 (PF connector n=78→79 daily variance). Source: `hybrid.n_used` + current date. Wording: "تقدير مبني على {n} إعلان كما في {YYYY-MM-DD}"
- **ADD `use_case_banner` section** per BRIEF v3.1 §6.7:
  ```
  Suitable for: [list per use case mapping]
  NOT suitable for: [list]
  → Stage 5 required for: [list]
  ```
- **ADD §1.6 mandatory reason text** for every refusal — §5 of this kickoff brief details the **5 active templates** (`asset_uniqueness` trigger deferred to 2.22.y per §2.3)
- **ADD `verification_url` field** to response — URL token only (e.g., `https://thammen.qa/verify/<token>`); full UI defers to 2.22.0.1 per BRIEF v3.1 §0 deferred items

**Acceptance §1.3:** Phase 3 §5 audit cases:
- A1 (Lusail H1 hybrid): `tier_breakdown` renders 2 rows (T2 0.88 n=79 + T3 0.12 n=4), `tier_label='analytical_range'`, `n_used=79` + freshness shown, `use_case_banner` present, `verification_url` non-null
- A2 (compound_large Patch-A refusal): `refusal_reason` = "Asset scale extreme" template (extent ≥ 15K m² per E20)
- A3 (Umm Lekhba villa with valuation): `tier_label='analytical_range'`, no tier_breakdown (no hybrid), use_case_banner present
- A4 (reality-check unknown): `refusal_reason` = "Spatial ambiguity" or "Asset type uncertain" template (new mapping per §5)
- A5 (Pearl tower density-gated): `refusal_reason` = "Density-gated district" template (NEW per §5 trigger #5 — was #6 in original v3.1 numbering before asset_uniqueness deferral)

### §1.4 Stage 3 — Output content surface (PARTIAL)
Per BRIEF v3.1 §1 Stage 3 output spec. 2.22.0a delivers **content + visual** changes only. The **architecture** (streaming, multi-screen, silent recompute) is 2.22.0b.

Frontend additions in 2.22.0a:
- **ADD calculator-style visual** (typography + layout differentiation) for Stage-3 final output — signals "tool output, not formal document" (per v3-6 BRIEF v3.1). Implementation: new CSS class on results screen + alternate font/spacing/border treatment. NOT a structural change. **Concrete styling guidance:** monospaced font family for numeric values (e.g., `font-family: 'JetBrains Mono', 'Courier New', monospace`), increased `line-height: 1.6` for readability, outlined dashed border on container (`border: 1px dashed var(--muted)` per existing theme variables), light-grey background (`var(--alt)`) for the final-value cell, and remove `box-shadow` / drop-shadows that imply formal-document aesthetic. Maintain RTL layout per existing index.html convention.
- **ADD directional adjustment ledger** — "Floor 8-12: increased value" / "View: premium adjustment applied" — NO exact percentages (per v3-4 hidden caps). 2.22.0a renders empty placeholder if Stage 2 adjustments aren't wired yet; full population happens in 2.22.0b when Stage 2 Q&A lands.
- **ADD verification URL UI hook** — partial: a small "verify this estimate" link rendering the URL from §1.3. Full verification page UI is 2.22.0.1.

**Does NOT implement** (Stage 3 architecture — 2.22.0b):
- ReadableStream streaming wrapper
- Multi-screen Stage 1 → Q&A → Stage 3 flow
- Silent recompute on Q&A submission
- D12 sprint-split logic (single-screen vs multi-screen)

**Acceptance §1.4:** Stage 3 final-output screen visually distinct from formal-report aesthetic. `verification_url` link present (clicks: 2.22.0.1 — clicking shows placeholder "coming soon" page or 404 — acceptable in 2.22.0a per §0 deferred items).

---

## §2 Non-goals (explicit out-of-scope)

### §2.1 Deferred to Sprint 2.22.0b (sequential)
- ReadableStream streaming infrastructure
- 5-stage UX multi-screen flow (Stage 0 → 1 → 2 Q&A → 3)
- Stage 2 interactive Q&A (7 fields per D-stage2-1)
- Silent recompute (no real-time value jumps per D-stage2-2)
- Property graph density gating **logic** implementation (3 baselines + heartbeat metric measurement)
- Bounded asymmetric adjustment caps (D-stage2-7 backend) — full caps with answer mapping
- D10 Lusail gate extension to Pearl (Q1 decision)
- Tower asset_type hybrid eligibility expansion (Q2 decision)

### §2.2 Deferred to Sprint 2.22.0.1 (post-launch patch)
- Image-embedded watermark engine
- Advanced disclosure mode (numeric ranges for opted-in sophisticated users)
- Full verification URL UI (page rendering, issuance timestamp display, current tier status, expiration logic)
- DB-backed verification URL persistence (2.22.0a uses deterministic hash; 2.22.0.1 may persist tokens)

### §2.3 Deferred to Sprint 2.22.y (validation, parallel)
- Tail-error analysis
- Temporal backtesting (2021-2024 train / 2025 test)
- Stratified validation
- Sensitivity-weighted inference audit (≥95% delta<5%, no case>15% per D-validation-1)
- Drift monitoring
- Adversarial market simulation (fake listings, synthetic clusters, broker spam, distressed poisoning)
- Property graph density measurement against §1.7 baselines
- A1 latency multi-rep p50/p95/p99 baseline (Q4 decision)
- **`asset_uniqueness` refusal trigger + 3σ outlier compute logic** (single logical unit per Anas decision 2026-05-26 — activation requires compute logic, so trigger ships together with compute or not at all). Originally enumerated as §1.6 trigger #4 in BRIEF v3.1; deferred from 2.22.0a kickoff per Anas's "no dead code in production" discipline (dead code = smell, test burden on inactive path, §1.6 contract promises active triggers, accidental activation risk on refactor).

### §2.4 Deferred to Sprint 2.22.x (PDPPL, parallel)
- Privacy notice + consent capture + consent versioning
- RoPA (Record of Processing Activities)
- Breach notification protocol
- Data subject request handling

### §2.5 Deferred beyond Sprint 2.22.0
- Stage 4 broker field verification → 2.22.1
- Stage 5 licensed valuer sign-off → 2.23+ (business-dev gated)
- Confirmed Sales DB integration → 2.16.16 (brokerage-pipeline-only path, 6-18 months timeline)
- Lusail Marina / tower-elsewhere / compound_small §5 audit coverage → 2.22.0.1 §5 audit
- arady in SOURCE_EXCLUSIONS substitute list (Q3 decision) → next docs wave (not 2.22.0a)
- Compound methodology research (>30K m² assets) → Sprint 2.25+ research-track

---

## §3 Acceptance criteria + ship-gate

### §3.1 Per-feature acceptance (functional, testable)

| # | Feature | Acceptance criterion |
|---|---|---|
| F1 | Tier renaming | `tier_label` field present on every non-refusal response. Values restricted to `{'indicative_estimate', 'analytical_range', 'broker_verified_range', 'signed_valuation'}`. UI maps to Arabic display strings. |
| F2 | `tier_breakdown` UI rendering | When `body.hybrid.tier_breakdown` is present and non-empty (Lusail hybrid path), brief includes a `tier_breakdown` section that renders T1/T2/T3 rows with `weight`, `n`, `value_per_m2_raw`, `value_per_m2_adjusted`. |
| F3 | `n_used` + freshness | When `body.hybrid.n_used` is present, brief surfaces it with a date stamp. Format: "تقدير مبني على N إعلان كما في YYYY-MM-DD". |
| F4 | Use-case banner | Every non-refusal response includes `use_case_banner` with `suitable_for[]`, `not_suitable_for[]`, `stage5_required_for[]`. Content per BRIEF v3.1 §6.7 table. |
| F5 | §1.6 dynamic refusal templates (6 active) | Every refusal response includes `refusal_reason = {trigger_id, message_ar, message_en, recommendation_ar}`. **6 active trigger_ids** in 2.22.0a (4 inherited + 1 NEW `density_gated_district` [BRIEF v3.1 §1.6 + Finding §3.1] + 1 NEW `asset_class_out_of_scope` [engine-capability for `out_of_scope_v1`, added Sprint 2.22.0a/5 per Q1 d decision]). The 6 are enumerated in §5 of this brief. `asset_uniqueness` trigger deferred to 2.22.y per §2.3 (single logical unit with 3σ compute). |
| F6 | Density-gated district refusal (NEW) | Pearl (`district == 'جزيرة اللؤلؤة'`) returns `refusal_reason.trigger_id = 'density_gated_district'`. Lusail D10 zones continue hybrid path (no density-gating). |
| F7 | Verification URL generation | Every Stage-2/Stage-3 response includes `verification_url = '<base>/verify/<token>'` where `<token>` is a deterministic hash of (PIN OR Z/S/B) + day-date. URL itself returns 404 in 2.22.0a (UI deferred to 2.22.0.1) — that's documented behaviour, not a bug. |
| F8 | A2 reclassification | BRIEF v2 (`CHANGELOG_pre_2p22p0_v2.md`) §4.5 row A2 updated to read "apartment_building (DCF refusal — canonical apt-Stage-2 case)" instead of "Villa". No production logic change. (Self-reference corrected /12 Phase 1 — original KICKOFF text cited v3.1 in error; v3.1 has no §4.5 row table.) |
| F9 | Calculator-style visual (Stage 3 output) | Results-screen final output visually distinct from formal-report aesthetic. Typography + spacing + border treatment differentiated. (No new fields; pure CSS + HTML class change.) |
| F10 | Directional adjustment ledger | When Stage 2 adjustments are present (post-2.22.0b — placeholder in 2.22.0a), brief renders "Factor: increased/decreased/unchanged" — NO percentages. 2.22.0a empty placeholder acceptable. |
| F11 | RICS Red Book 2024 / IVS 2024 text audit | `material_uncertainty.py` MUC clause text reviewed and updated where current copy diverges from RICS Red Book 2024 / IVS 2024 standards. Specific text changes recorded in commit message. |

### §3.2 Regression gates (mandatory before deploy)
- All existing **81 standalone tests across 29 files** remain green (per Phase 1 audit baseline + CLAUDE.md production state).
- Phase 3 §5 audit's 5 cases (A1-A5) re-run post-deploy:
  - A1: `val.value_per_m2` within ±0.5% of 11,425.17 (cbb2730 baseline, accounts for PF daily variance)
  - A2-A4: exact match on `val.method`, `val.amount`, `brief.sections` ID list
  - A5: `refusal_reason.trigger_id == 'density_gated_district'` (NEW expected)
- All 5 cases must return HTTP 200 (no 503 cold-dyno on retry).

### §3.3 Ship-gate per BRIEF v3.1 §11 (90-day monitoring — applicable subset for 2.22.0a)
- **5 active refusal triggers cover all 2.22.0a refusal paths.** Every refusal observed in Phase 3 §5 audit (A2 compound_large, A4 reality-check, A5 Pearl, plus future production hits on `comp_density_sparse` / `regime_shift`) maps to exactly one of the 5 enumerated trigger_ids in §5. No production refusal hits an unhandled trigger_id (verifiable via post-deploy smoke audit on A1-A5).
- **Refusal trigger rate:** must be measurable post-deploy. 2.22.0a hooks up the metric source (refusal_reason.trigger_id) but the dashboard is 2.22.2 territory.
- **User input churn at Stage 3:** not applicable in 2.22.0a (Stage 2 Q&A not shipped).
- **Inferred identity drift:** 2.22.y owns measurement; 2.22.0a doesn't gate on it.
- **Broker routing skew:** not applicable (Stage 4 not shipped).
- **Heartbeat metric drift:** 2.22.0b owns; 2.22.0a renders the result if density-gated.
- **Screenshot propagation patterns:** 2.22.0.1 owns; 2.22.0a generates verification URL token to enable.

### §3.4 ENGINE_VERSION + SPRINT_TAG bump (R2 amendment 2026-05-26)
- **`ENGINE_VERSION` slug** (`evaluate_unified.py:44`): `'thammen-sprint2p21p4-t3-aryan-lusail'` → `'thammen-sprint2p22p0a-content-and-refusal-templates'`
- **`SPRINT_TAG`** (`evaluate_unified.py:45`): `'2.21.4'` → `'2.22.0a'`
- **`api.py:100` `version="3.1.0"` UNCHANGED** — this is the FastAPI app spec version, NOT sprint-tagged. The sprint identifier is concatenated at `/api/health` response time via the existing line-45 comment convention: `"3.1.0-sprint" + SPRINT_TAG`.
- KICKOFF original draft assumed `api.py` `version` bumps each Sprint to `"3.2.0-sprint2.22.0a"`; **R2 reconnaissance (2026-05-26) found this contradicts existing project convention** — the FastAPI `version` field has stayed at `"3.1.0"` across multiple sprints. Amendment per R2: do not touch `api.py:100`.
- `/api/health` returns `version: "3.1.0-sprint2.22.0a"` on deploy via the existing concatenation logic — no `api.py` change needed.

---

## §4 Architecture impact

### §4.1 Files touched (modify-only, no architectural restructure)

| File | Changes | Risk |
|---|---|---|
| `evaluate_unified.py` | • ENGINE_VERSION bump<br>• Add `tier_label` to response (per asset_type / valuation path)<br>• Add `use_case_banner` injection (helper function emits per §6.7 single-dimension structure — single banner across all 4 audiences)<br>• Add `refusal_reason` injection on all refusal paths (insufficient_data, asset_type_reality_stop, Patch-A skip-MoJ)<br>• Add `verification_url` generation call<br>• Detect `district == 'جزيرة اللؤلؤة'` (and other non-D10 non-empty districts where appropriate) → trigger `density_gated_district` refusal | **MEDIUM** (Pearl detection adds a NEW classification branch — behaviour change, not pure additive. Before: Pearl falls to generic `insufficient_data`. After: Pearl returns `refusal_reason.trigger_id='density_gated_district'`. All other listed changes are additive but the Pearl branch warrants MEDIUM. Mitigation: §7.3 smoke audit case A5 covers Pearl behaviour change explicitly; Rule #11 rollback target = Heroku v128.) |
| `output_briefs.py` | • Add new section builders: `_tier_breakdown_section`, `_use_case_banner_section`, `_refusal_reason_section`, `_adjustment_ledger_directional_section`<br>• Add tier_label rendering across all 4 audience briefs (`_buyer_brief`, `_seller_brief`, `_investor_brief`, `_valuer_brief`)<br>• Update `_base_brief()` to surface `tier_label` + `verification_url` + `use_case_banner` in the header dict | LOW (pure additive section appends; existing sections preserved) |
| `index.html` | • Add `SEC_ICONS` entries for new section IDs (`tier_breakdown`, `use_case_banner`, `refusal_reason`, `adjustment_ledger_directional`)<br>• Add `renderSection()` switch cases for the 4 new sections<br>• Add calculator-style CSS class + apply to Stage-3 results screen container<br>• Surface `data.tier_label` + `data.verification_url` in the results header rendering<br>• NO new screens (multi-screen flow is 2.22.0b)<br>• NO SSE / ReadableStream wiring (2.22.0b) | LOW (additive renderSection cases + CSS — does not touch existing logic) |
| `api.py` | • ENGINE_VERSION/version string bump<br>• Pydantic response schemas: add `tier_label: Optional[str]`, `verification_url: Optional[str]`, `refusal_reason: Optional[dict]`, `use_case_banner: Optional[dict]` (with `extra='forbid'` schemas unchanged per Bug A2 / Sprint 2.16.15)<br>• A2 reclassification: documentation comment update only — production behaviour unchanged | LOW (Pydantic additions backward-compatible; old clients ignoring new fields work) |
| `material_uncertainty.py` | • RICS Red Book 2024 / IVS 2024 compliance text audit: update `muc_clause_ar` + `muc_clause_en` wording where divergent from current RICS standards. Specific text changes proposed for Anas review before commit. | LOW (text-only; no logic) |

### §4.2 New files (small, single-responsibility)

| File | Purpose | Size estimate |
|---|---|---|
| `refusal_templates.py` | Centralised registry of **5 active** §1.6 refusal templates (`asset_uniqueness` deferred to 2.22.y per §2.3). `get_refusal_template(trigger_id, **context) → dict` returns `{trigger_id, message_ar, message_en, recommendation_ar}`. Templates parameterise on optional context (e.g., regime-shift event name, comp count). | ~130-170 LOC |
| `verification_url.py` | Deterministic URL token generation. `generate_token(pin_or_zsb, day) → str`. Hash-based (SHA-256 truncated to 12 chars, base32-encoded). No DB in 2.22.0a (DB-backed in 2.22.0.1). | ~50-80 LOC |
| `test_sprint_2p22p0a_refusal_templates.py` | Isolated tests per §1.6 trigger. **5 active templates** × 3-5 contexts each. | ~200 LOC |
| `test_sprint_2p22p0a_tier_labels.py` | Tier label emission per asset_type / valuation path. ~10 cases. | ~150 LOC |
| `test_sprint_2p22p0a_use_case_banner.py` | Banner content per audience × asset_type. | ~120 LOC |
| `test_sprint_2p22p0a_verification_url.py` | URL token determinism + idempotency. | ~80 LOC |
| `test_sprint_2p22p0a_density_gated_district.py` | Pearl → density_gated_district refusal trigger. | ~80 LOC |
| `test_sprint_2p22p0a_a2_documentation.py` | Verify BRIEF v2 (`CHANGELOG_pre_2p22p0_v2.md`) §4.5 A2 row updated (text assertion). | ~30 LOC |

**Total new code estimate (per §9.1 sub-sprint breakdown):**

- **Production code (Python core logic):** ~580 LOC across sub-sprints /1, /2, /5, /6, /7, /9 (adjusted from ~610 pre-amendment after /1 shrunk from ~30 to ~3 LOC per R2+R3 reconnaissance)
- **Frontend rendering (`index.html` CSS + `renderSection()` switch cases):** ~400 LOC across sub-sprints /3, /4, /8 (+ shares of /2, /5)
- **Tests:** ~700 LOC (sub-sprint /10 batch — 6+ new test files)
- **Docs / CHANGELOG / PHASE3_LOG appends:** ~160 LOC across sub-sprints /11, /12
- *(Schema additions line removed — per A2 amendment, response fields are dict-key additions embedded in /2-/9 logic, not a separate Pydantic-declaration count)*

**Total: ~1670-1870 LOC including production + frontend + tests + docs (per §9.1 sub-sprint breakdown — adjusted from ~1700-1900 pre-amendment after sub-sprint /1 scope shrinkage).** Earlier "~1030 LOC" figure undercounted by omitting frontend `index.html` work (~400 LOC) and docs sub-sprints (~160 LOC); revised here for honesty. Production-only delta is ~580 LOC (per Anas observed-vs-expected discipline Rule #36 + #51).

### §4.3 Response field additions (R3 amendment 2026-05-26)

**`api.py` contains Pydantic models for REQUESTS only** (`EvaluateRequest` at line 263, `EvaluateDetailsRequest` at line 304). **NO Pydantic response models exist** in the codebase as of v128. `/api/evaluate` and `/api/evaluate/details` return raw `dict` payloads (via `evaluate_thammen()` → `_simplify_evaluation()` → `_attach_freshness()`). FastAPI serialises the dict directly without schema enforcement.

**R3 reconnaissance (2026-05-26)** uncovered this. KICKOFF original draft assumed Pydantic response schema additions, which is not actionable as written.

**Amendment §4.3:** the 4 new response fields are **dict-key additions emitted in sub-sprints /2-/9** as the corresponding logic lands:

| Field | Emitted in sub-sprint | Source files |
|---|---|---|
| `tier_label: str` | 2.22.0a/2 | `evaluate_unified.py` + `output_briefs.py` |
| `tier_breakdown` (renders existing `hybrid.tier_breakdown` block) | 2.22.0a/3 | `output_briefs.py` + `index.html` |
| `n_used` (int) + `freshness_date` (str, YYYY-MM-DD) | 2.22.0a/3 | `evaluate_unified.py` + `output_briefs.py` — emitted alongside tier_breakdown rendering; `n_used` mirrors `body.hybrid.n_used` (already present in response root per Phase 3 audit); `freshness_date` is NEW (engine emits current UTC date at evaluation time) |
| `use_case_banner: dict` | 2.22.0a/4 | `evaluate_unified.py` + `output_briefs.py` |
| `refusal_reason: dict` | 2.22.0a/5 | `refusal_templates.py` + `evaluate_unified.py` |
| `verification_url: str` | 2.22.0a/7 | `verification_url.py` + `evaluate_unified.py` |

`tier_label` allowed values: `'indicative_estimate' | 'analytical_range' | 'broker_verified_range' | 'signed_valuation'`. Backend emits English; UI maps to Arabic. UI layer (`index.html` `renderSection()` switch) reads `data.tier_label` defensively (`?.` optional-chaining for missing field) per existing pattern.

**Pydantic response model enforcement deferred** as a separate future concern (potential "API schema hardening" Sprint, post-2.22.0). Adding `EvaluateResponse(BaseModel)` would require declaring ~50+ existing response fields and could break current ad-hoc dict shapes under FastAPI strict mode — out of 2.22.0a scope per Rule #38 single-purpose discipline.

### §4.4 No new endpoints
- No new `POST /api/...` or `GET /api/...` routes
- No SSE endpoint (2.22.0b)
- No verification URL backing endpoint (2.22.0.1)

### §4.5 Backward compatibility
- All response additions optional (Pydantic schemas)
- Existing fields unchanged in shape and meaning
- Old clients ignoring new fields continue working
- `/api/health` engine_version bump is the only observable change for non-rendering clients

---

## §5 §1.6 Dynamic refusal templates (6 active + 1 deferred)

Per BRIEF v3.1 §1.6 + Finding §3.1 (Pearl density-gating) + Sprint 2.22.0a/5 Q1 d decision (`asset_class_out_of_scope` engine-capability trigger). **6 active triggers** ship in 2.22.0a; `asset_uniqueness` deferred to 2.22.y per §2.3 (single logical unit — trigger + 3σ compute ship together or not at all per Anas decision 2026-05-26). Each refusal output emits:

```python
refusal_reason = {
    "trigger_id": "<id>",           # one of 5 active enumerated below
    "message_ar": "<Arabic copy>",  # mandatory reason text
    "message_en": "<English copy>", # for B2B / sophisticated clients
    "recommendation_ar": "<Arabic recommendation>",
    "context": {...}                # optional trigger-specific data
}
```

### §5.1 Template registry

| # | trigger_id | Condition (engine logic) | message_ar | recommendation_ar |
|---|---|---|---|---|
| 1 | `comp_density_sparse` | MoJ comp count `n<5` in 24mo window AND `n<10` in 36mo fallback within size_bracket × district | "هذه المنطقة فيها أقل من 5 صفقات بيع مقارنة خلال آخر 6 أشهر لعقارات بهذا الحجم والنوع. التقدير الآلي لا يصل إلى مستوى الموثوقية المطلوب." | "نوصي بتقييم متخصص لعقارك من خلال مُقيِّم معتمد." |
| 2 | `spatial_ambiguity` | Multiple GIS parcels of compatible size/type for unmapped MoJ transaction, ambiguity score `>0.7` OR `asset_type_reality_stop` | "تعذّر ربط عقارك بمبنى أو قطعة وحيدة في نظامنا. لإصدار تقدير موثوق، نوصي بتقييم متخصص مع تحقّق ميداني." | "تقييم متخصص مع تحقّق ميداني موصى به." |
| 3 | `regime_shift` | District has had infrastructure announcement / major developer launch / freehold rule change in last 90 days (data source: `district_regimes.json` empty skeleton in 2.22.0a per §5.4; populated in 2.22.0b operational track) | "هذه المنطقة شهدت تغيّرات سوقية كبيرة خلال آخر 90 يوماً{event_name}. الصفقات المقارنة في فترة انتقالية. نوصي بتقييم متخصص حتى يستقرّ السوق." | "تقييم متخصص موصى به حتى استقرار السوق." |
| 4 | `asset_scale_extreme` | Property is `5×` larger than largest comparable transaction in database, OR `compound_small` extent `≥15,000 m²` (E20 Patch-A boundary) | "حجم عقارك يتجاوز أي صفقة مقارنة في قاعدة بياناتنا. التقدير الآلي لا يستطيع التعميم بأمان. تقييم متخصص مطلوب لأصل بهذا الحجم." | "تقييم متخصص مطلوب." |
| 5 | `density_gated_district` (NEW per Finding §3.1) | `district NOT IN {covered_districts_set}` — for 2.22.0a, the covered set is the existing D10 Lusail token set; Pearl (`'جزيرة اللؤلؤة'`) and other zones outside D10 fall here | "بيانات هذه المنطقة في طور الاكتمال. لا نوفّر حالياً تقديراً آلياً لعقارات في هذا الموقع. نوصي بتقييم متخصص." | "نوصي بتقييم متخصص أثناء عملنا على توسيع التغطية." |

**Deferred (NOT in 2.22.0a per §2.3):** `asset_uniqueness` trigger (3σ outlier check) — bundled with compute logic as a single logical unit, both ship in 2.22.y. Originally BRIEF v3.1 §1.6 trigger #4.

**Template substitution syntax (M2 clarification):** template strings use Python `.format()` substitution with named placeholders. For trigger #3 specifically: `template.format(event_name=" — إعلان مشروع X" if event else "")`. Default `event_name=""` handles events without an `event_name` attribute without breaking template substitution. When the registry is empty (`{"events": []}` skeleton per §5.4), the trigger doesn't fire at all (no event to match) — the default value only matters once the registry is populated by the 2.22.0b operational track. The trigger-id, message_ar, and message_en strings are constants in `refusal_templates.py`; only `{event_name}` (trigger #3) and potentially `{comp_count}` (trigger #1, future enhancement) accept context substitution.

### §5.2 Refusal output also includes:
- `soft_indicative_range` (optional) — wide MUC indicative range labeled "rough orientation only, not for any transactional use" — may be empty for `density_gated_district` and `spatial_ambiguity`
- `connect_specialist_cta` — link/anchor text per Stage 5 Path C framework
- `verification_url` — even refusals get a URL (audit trail for what was refused and why)

### §5.3 Logic precedence (when multiple triggers could fire)
1. `density_gated_district` (overrides all — if district uncovered, no estimation attempted)
2. `spatial_ambiguity` / `asset_type_reality_stop` (Sprint 2.21.0.7 path)
3. `asset_scale_extreme` (E20 Patch-A path)
4. `regime_shift` — when district matches a flagged regime event
5. `comp_density_sparse` (fallback for sparse MoJ data)

First-match wins. Engine emits exactly one `trigger_id` per refusal.

> `asset_uniqueness` (3σ check) deferred to 2.22.y per §2.3 — **not in this precedence chain** for 2.22.0a. When 2.22.y ships, the chain will insert it between rows 3 and 4 (after `asset_scale_extreme`, before `regime_shift`).

### §5.4 What 2.22.0a does NOT do (deferred)
- **`asset_uniqueness` trigger + 3σ outlier compute logic** (single logical unit per §2.3 / Anas decision 2026-05-26 — activation requires compute logic; trigger ships together with compute or not at all). Whole bundle deferred to 2.22.y.
- **`regime_shift` registry population** — 2.22.0a ships `district_regimes.json` as an **empty registry skeleton** (`{"events": []}`). Trigger logic reads it on every refusal-eligible request; with zero events, no `regime_shift` refusals fire. The trigger is **live, not inert** — it correctly returns "no match" on empty data, and populating the registry in 2.22.0b activates real refusals without code change. This is the same "live path, unfed data" pattern as e.g. Sprint 2.15.1 `building_age_cache.sqlite` (62 PINs pre-filled; cache miss is a live path that returns None).
- Connect "specialist CTA" to actual partner valuer routing — 2.22.1 (Stage 4). The CTA *anchor text* ships in 2.22.0a (live path returning a copy string); the link target is 2.22.1.

---

## §6 §1.7 Density-gating posture in 2.22.0a

> **Critical distinction:** 2.22.0b owns the density-gating **logic** (3 baselines measurement + heartbeat metric computation). 2.22.0a renders the **outcome** for districts currently known to fall outside coverage.

### §6.1 What 2.22.0a does
- Detect zones outside the existing D10 Lusail gate (`_is_lusail_district()` returns False) → trigger `density_gated_district` refusal template
- Pearl (`district == 'جزيرة اللؤلؤة'`) → density-gated refusal
- Lusail 69 / غار ثعيلب → already covered by D10 → hybrid path (unchanged)
- West Bay (`district == 'الدفنة 61'` etc.) / Doha / other districts → at present, fall through to existing `insufficient_data` paths. **2.22.0a does NOT auto-density-gate these** — would require listing every uncovered district. Instead, the existing `insufficient_data` paths get the new `comp_density_sparse` template (which is the truthful trigger for those zones).

### §6.2 Lusail 69 / Fox Hills / Marina handling
- Lusail 69 (`'لوسيل 69'`) → covered by D10 → hybrid path (no change)
- Fox Hills (`'غار ثعيلب'`) → covered by D10 → hybrid T2-only (no change)
- Marina (likely `'لوسيل 70'` per CLAUDE.md §16, untested in Phase 3) → if D10 matches via `'لوسيل'` substring, covered. If not, falls into `density_gated_district`. **Auditable post-deploy via §5 audit reverify.**

### §6.3 What 2.22.0a does NOT do (handed off to 2.22.0b)
- Compute Tower Coverage Floor (≥85% of active residential towers mapped to municipal plot IDs)
- Compute Transaction Linking Floor (≥75% of unmapped historical MoJ transactions linked)
- Compute Condition Fingerprint Density (≥5 user-verified condition updates per 1,000 m²)
- Compute heartbeat metric ("% valuation variance attributable to unresolved identity ambiguity")
- Auto-density-gate based on baseline failure
- Implement weekly recomputation of density per district

### §6.4 What this means for ship gate (BRIEF v3.1 §10 #8)
- **Pearl is explicitly density-gated in 2.22.0a** (refusal template renders correctly). Ship gate per §10 #8: "Density baselines confirmed achievable in target zones (Pearl, Lusail Fox Hills + Marina, West Bay) OR density-gating accepted as launch posture for failing zones" — **2.22.0a accepts density-gating as Pearl's launch posture**.
- **Lusail Fox Hills + Lusail 69 covered by D10 verified** (per H_walk anchors H1=69/255/75 + H11=69/329/20 confirming hybrid path produces value with n=78-79). **Lusail Marina coverage expected via `'لوسيل'` substring match, auditable post-deploy** (gap in Phase 3 §5 audit — no Marina PIN tested; §2.5 lists "Lusail Marina §5 audit coverage" as deferred to 2.22.0.1).
- West Bay coverage partial (61/875/20 confirmed via A11 Sprint 2.16.14). For 2.22.0a, West Bay falls through to existing `insufficient_data` paths → renders as `comp_density_sparse` template. 2.22.y validation work measures whether West Bay meets baselines or stays density-gated.

---

## §7 Testing strategy

### §7.1 Isolated tests (new for 2.22.0a)
- `test_sprint_2p22p0a_refusal_templates.py` — **5 active templates** × 3-5 contexts (parameter substitution, edge cases) ≈ 20-25 tests. Also asserts `asset_uniqueness` trigger_id is NOT registered (negative test — defers correctly to 2.22.y).
- `test_sprint_2p22p0a_tier_labels.py` — 4 tier values × asset_type cross-product ≈ 10-12 tests
- `test_sprint_2p22p0a_use_case_banner.py` — banner content per audience (buyer/seller/investor/valuer) × asset_type ≈ 8-10 tests
- `test_sprint_2p22p0a_verification_url.py` — token determinism (same input → same token), idempotency (multiple calls → same output), input-shape variants (PIN vs Z/S/B) ≈ 6-8 tests
- `test_sprint_2p22p0a_density_gated_district.py` — Pearl trigger, D10 Lusail bypass, fallback chain ≈ 5-7 tests
- `test_sprint_2p22p0a_a2_documentation.py` — text assertion on BRIEF v2 (`CHANGELOG_pre_2p22p0_v2.md`) §4.5 row A2 ≈ 1-2 tests

**Target:** ~50-65 new isolated tests, all standalone (no pytest framework dependency per CLAUDE.md). Run with `PYTHONIOENCODING=utf-8`.

### §7.2 Regression (mandatory before deploy)
- Run all existing **81 standalone tests across 29 files** (per Phase 1 audit baseline). All must remain green.
- ENGINE_VERSION bump must be detected by version-pinning tests (relaxed per Sprint 2.19.1 anti-pattern fix — `startswith('thammen-sprint')` discipline).

### §7.3 Smoke (post-deploy)
Re-run Phase 3 §5 audit (`audit_step4_5cases.py`) against the new engine:
- A1: `val.value_per_m2` within ±0.5% of 11,425.17 baseline; **NEW expected** `tier_label='analytical_range'`, `tier_breakdown` section present, `n_used + freshness` rendered, `use_case_banner` present, `verification_url` non-null
- A2: `refusal_reason.trigger_id = 'asset_scale_extreme'` (Patch-A compound_large, extent > 15K m² per EMPIRICAL_FINDINGS E20 trigger; exact magnitude not asserted here to avoid figure drift if extent changes post-survey-update)
- A3: `val.amount=3,200,000` exact (warm dyno), `tier_label='analytical_range'`, `use_case_banner` present
- A4: `refusal_reason.trigger_id ∈ {'spatial_ambiguity'}` (asset_type_reality_stop path)
- A5 (Pearl): `refusal_reason.trigger_id = 'density_gated_district'` (NEW expected per Finding §3.1)

### §7.4 Manual verification (Anas on thammen.qa)
- Visit thammen.qa (or post-deploy preview) for 1-2 cases with full UI
- Verify calculator-style visual differentiation on Stage-3 output
- Verify Arabic copy register on refusal templates (peer review)
- Verify use_case_banner Arabic copy is clear and non-redundant
- Verify verification_url link present (404 acceptable in 2.22.0a per §0)

---

## §8 Risk register + rollback plan (Rule #11)

### §8.1 Known risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Tier renaming breaks downstream clients parsing tier labels (none documented externally, but possible) | LOW | LOW | `tier_label` is purely additive. No existing field renamed or removed. Old clients ignore unknown field per §4.5 backward compatibility (Pydantic schemas keep `extra='forbid'` only on inbound requests per Bug A2; response is additive). Confidence labels currently embedded in `accuracy.label` Arabic strings (per Phase 3 audit) remain unchanged; `tier_label` is a NEW machine-readable companion. |
| R2 | §1.6 refusal Arabic templates have register mismatch with Anas's voice | MEDIUM | LOW | Peer review by Anas before deploy (manual verification §7.4); easy text edit if mismatch |
| R3 | `verification_url` token non-deterministic (e.g., timestamp drift across calls) | LOW | MEDIUM | Determinism tests in `test_sprint_2p22p0a_verification_url.py`; hash-based logic explicitly day-bucketed |
| R4 | Density-gated refusal fires on covered Lusail districts (false positive) | LOW | HIGH | Test cases enumerate D10 token set; smoke audit reverifies A1 (Lusail) post-deploy |
| R5 | `tier_breakdown` UI rendering fails on edge cases (T3 absent, n=0) | LOW | LOW | Defensive rendering in `renderSection()` switch; tests cover all 4 cases (T1/T2/T3/none) |
| R6 | RICS Red Book 2024 / IVS 2024 text changes diverge from intent | LOW | MEDIUM | Specific text changes itemized in commit message + peer review by Anas |
| R7 | `use_case_banner` content controversial (e.g., declaring "NOT suitable for mortgage origination" may alienate bank partners) | MEDIUM | MEDIUM | Anas signs the banner copy before commit; banner can be updated in 2.22.0.1 |
| R8 | ENGINE_VERSION bump unmasks pre-existing methodology issues (Rule #52 — latency unmasks methodology) | LOW | HIGH | Smoke audit reverifies 5 cases; any drift > acceptance criterion triggers Rule #11 rollback |
| R9 | Pearl tower classification (`asset_type='tower'`) interacts unexpectedly with density-gated refusal template | LOW | LOW | Test A5 covers this case specifically; logic precedence (§5.3) defaults to district check before asset_type |

### §8.2 Rollback plan (Rule #11)
- **Rollback target:** Heroku v128 (current state, pre-2.22.0a deploy)
- **Trigger conditions** (any one triggers immediate rollback):
  - 5-case smoke audit shows drift >0.5% on any non-Pearl case
  - Engine `/api/health` non-200 or `engine_version` mismatch
  - Any of the 81 existing regression tests fail
  - Anas visually identifies wrong refusal message or wrong tier label
- **Rollback command:**
  ```
  heroku rollback v128 --app thammen-app-123
  ```
  (`thammen-app-123` is the actual Heroku app name, NOT a placeholder — verified via `git remote -v` showing `https://git.heroku.com/thammen-app-123.git` and live response at `https://thammen-app-123-227a7106a67a.herokuapp.com/`. Or `git push heroku heroku-deploy-tmp:master --force` per Rule #43 self-cleaning procedure if subtree split diverged.)
- **Post-rollback action:**
  1. Capture failure mode (logs + audit output)
  2. Open follow-up commit on master fixing the issue
  3. Re-deploy

### §8.3 Pre-deploy 6-item checklist (§5 of Project Instructions)
Before final deploy:
1. ☐ `python -m py_compile` on every modified Python file
2. ☐ `node --check` on extracted inline JS from `index.html` (if JS changed)
3. ☐ Mobile viewport test 390×844 (manual on Anas's device or browser DevTools)
4. ☐ Regression tests: 29+ standalone files all exit 0
5. ☐ Isolated logic tests for new code (~50-65 new tests per §7.1 target, all green)
6. ☐ Smoke test 3-5 diverse addresses post-deploy (A1-A5 + 1-2 extra if Anas chooses)

---

## §9 Sequencing + commit boundaries

### §9.1 Sub-sprints within 2.22.0a (commit cadence)
Each is a single-purpose commit per Rule #38. Same disciplined commit pattern (msg tmp file → add → status → commit -F → log → rm tmp).

| Sub-sprint | Description | Files | LOC estimate |
|---|---|---|---|
| 2.22.0a/1 | **ENGINE_VERSION + SPRINT_TAG bump only** (per R2+R3 amendments 2026-05-26: `api.py:100 version="3.1.0"` UNCHANGED — sprint identifier via SPRINT_TAG concatenation; no Pydantic response model exists, so "schema additions" reinterpreted as dict-key additions emitted in /2-/9 as logic lands) | `evaluate_unified.py:44-45` only | ~3 LOC |
| 2.22.0a/2 | Tier renaming + `tier_label` emission per asset_type / valuation path | `evaluate_unified.py` + `output_briefs.py` | ~80 LOC |
| 2.22.0a/3 | `tier_breakdown` UI section + `n_used` + freshness rendering | `output_briefs.py` + `index.html` | ~150 LOC |
| 2.22.0a/4 | `use_case_banner` per BRIEF v3.1 §6.7 + Arabic copy review | `output_briefs.py` + `index.html` | ~100 LOC |
| 2.22.0a/5 | `refusal_templates.py` NEW (**5 active templates** — `asset_uniqueness` deferred per §2.3) + `district_regimes.json` empty skeleton + integration in `evaluate_unified.py` refusal paths | `refusal_templates.py` + `district_regimes.json` + `evaluate_unified.py` + `output_briefs.py` + `index.html` | ~250 LOC |
| 2.22.0a/6 | `density_gated_district` trigger integration — **MERGED INTO /5** per natural precedence chain scope overlap. Implementation shipped within Sprint 2.22.0a/5 (commit `b0c62b7`) — see §5.3 row 1 (`density_gated_district` overrides all). No separate /6 commit. | (absorbed) | (absorbed into /5) |
| 2.22.0a/7 | `verification_url.py` NEW + integration | `verification_url.py` + `evaluate_unified.py` + `index.html` | ~120 LOC |
| 2.22.0a/8 | Calculator-style visual + directional adjustment ledger placeholder | `index.html` (CSS + new section render) | ~150 LOC |
| 2.22.0a/9 | RICS Red Book 2024 / IVS 2024 compliance text audit on `material_uncertainty.py` | `material_uncertainty.py` | ~50 LOC |
| 2.22.0a/10 | Isolated tests batch (all 6+ new test files) | 6+ new `test_sprint_2p22p0a_*.py` files | ~700 LOC |
| 2.22.0a/11 | A2 documentation fix in BRIEF v2 §4.5 row | `2p22p0_pre/CHANGELOG_pre_2p22p0_v2.md` | <10 LOC (data) + ~30 LOC (test guard) |
| 2.22.0a/12 | Final regression + smoke audit + CHANGELOG_v50.md | `CHANGELOG_v50.md` + `PHASE3_LOG.md` update | ~150 LOC |

**Total estimated commits:** 12 (one per sub-sprint). **Estimated days:** 3-5 per BRIEF v3.1 §2 row 1. ~2-3 commits per day.

### §9.2 Deploy timing
- **First runtime push** to Heroku since v128 (docs-only) happens at **end of 2.22.0a/12** (last commit before deploy).
- The push carries: 5 docs commits (45bd20f, 791a67a, 9a1c0a1, 53cace0, cbb2730) + this kickoff brief commit (signed) + 12 code commits = **18 commits in a single Heroku release**.
- Single `git subtree push --prefix "deploy v2" heroku master` (Rule #43).
- If subtree split diverged (likely after 18+ commits since last subtree push), execute the self-cleaning procedure:
  ```
  git -C "C:\Thammen" subtree split --prefix "deploy v2" -b heroku-deploy-tmp
  git -C "C:\Thammen" push heroku heroku-deploy-tmp:master --force
  git -C "C:\Thammen" branch -D heroku-deploy-tmp
  ```
- Each step a separate Bash call per command discipline (no `&&`).

### §9.3 Anas approval gates
- **Gate 1 (now):** Anas signs this KICKOFF brief. No code begins until signed.
- **Gate 2 (pre-deploy):** Anas reviews `CHANGELOG_v50.md` + smoke audit output. Approves deploy.
- **Gate 3 (post-deploy):** Anas visually verifies on thammen.qa. Approves Sprint 2.22.0a as closed.

Between gates 1 and 2, sub-sprint commits happen in master without per-commit Anas approval (single-purpose discipline + tests as the per-commit safety net). Sprint 2.22.0a stays in master only — no Heroku push until gate 2.

### §9.4 Branch posture
- All work on `master`. No worktree / feature branch per project convention.
- Each sub-sprint commit follows the disciplined commit msg tmp pattern.

---

## §10 Sign-off

```
Anas:           ______________________  Date: __________
Claude Code:    BRIEF_2p22p0a_KICKOFF.md drafted 2026-05-26 PM (Phase 3 Step 7)
Spec authority: BRIEF_2p22p0_FINAL_v3.1.md (commit cbb2730)
Audit basis:    PHASE3_AUDIT_pre_2p22p0a.md (commit 53cace0)
```

**On Anas signing this KICKOFF:**
1. Commit this brief as housekeeping (Commit 6): `Housekeeping: BRIEF_2p22p0a_KICKOFF.md (signed) — 2.22.0a implementation contract`
2. Begin sub-sprint 2.22.0a/1 (ENGINE_VERSION bump + Pydantic schema additions)
3. Subsequent sub-sprints 2.22.0a/2 through 2.22.0a/12 follow per §9.1 sequence
4. PHASE3_LOG.md gets a §B chronological entry per completed sub-sprint
5. Pre-deploy gate 2: final regression + smoke + CHANGELOG_v50 + Anas approval

**No code, no commit, no push until Anas signs above.**

---

## Appendix A — Q1-Q4 decisions integration map

| Q | Decision | Where it lands in this brief |
|---|---|---|
| Q1 Pearl density-gating posture | 2.22.0a renders Pearl as density_gated_district; 2.22.0b decides D10 extension | §5 trigger #5 (NEW; was #6 in v3.1 numbering before asset_uniqueness deferral), §6 density-gating posture, §1.3 acceptance criterion A5 |
| Q2 Tower hybrid eligibility | Defer to 2.22.0b investigation (MME area code 765 feasibility) | §2.1 non-goals |
| Q3 arady in SOURCE_EXCLUSIONS substitute | Defer to next docs wave; document in PHASE3_LOG follow-up list | §2.5 non-goals; PHASE3_LOG §G update post-sign |
| Q4 A1 latency multi-rep baseline | Defer to 2.22.y validation backlog ("multi-rep p50/p95/p99") | §2.3 non-goals; PHASE3_LOG §G update post-sign |

## Appendix B — Acceptance criteria one-liner cross-reference

For Phase 4 H-walk post-deploy:

| Phase 3 §5 case | Expected 2.22.0a behaviour change vs commit cbb2730 baseline |
|---|---|
| A1 (Lusail H1 hybrid) | Brief now includes tier_breakdown + n_used + freshness + use_case_banner + verification_url. val.value_per_m2 ±0.5% drift (PF variance) |
| A2 (compound_large 51/835/17) | refusal_reason.trigger_id='asset_scale_extreme' (was: generic insufficient_data copy) |
| A3 (Umm Lekhba villa) | tier_label='analytical_range' + use_case_banner present. val.amount=3,200,000 exact |
| A4 (PIN 66030258 reality-check) | refusal_reason.trigger_id='spatial_ambiguity' (was: generic asset_type_reality_stop copy) |
| A5 (Pearl tower 66/140/6) | refusal_reason.trigger_id='density_gated_district' (was: generic insufficient_data copy) |

---

*Phase 3 Step 7 deliverable. Drafted 2026-05-26 PM. No engine version bump. No code change. No git commit. No Heroku push. Awaiting Anas sign-off per Rule #32 (Anas signs briefs before code).*
