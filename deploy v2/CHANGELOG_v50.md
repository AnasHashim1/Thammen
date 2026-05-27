# Sprint 2.22.0a "Content + Refusal Templates" — CHANGELOG v50

> **Status:** Drafted 2026-05-27 PM. Awaiting Anas Gate 2B approval. NOT YET DEPLOYED.

-----

## 0. Sprint header

| Field | Value |
|---|---|
| Sprint identifier | **2.22.0a** ("Content + Refusal Templates") |
| Sprint dates | 2026-05-26 (KICKOFF signed) → 2026-05-27 (drafted/pre-deploy) |
| ENGINE_VERSION transition | `thammen-sprint2p21p4-t3-aryan-lusail` → **`thammen-sprint2p22p0a-content-and-refusal-templates`** |
| `SPRINT_TAG` (evaluate_unified.py:45) | `'2.22.0a'` |
| Production baseline (pre-Sprint) | Heroku **v128** (subtree-side hash `044340e`, C:\Thammen-side hash `a903350` — Phase 1 audit findings, pushed docs-only 2026-05-26) |
| Production baseline (post-Sprint) | **TBD post-push** |
| KICKOFF brief | `2p22p0_pre/BRIEF_2p22p0a_KICKOFF.md` (signed commit `33f7e33`, 2026-05-26) |
| Source-of-truth FINAL spec | `2p22p0_pre/BRIEF_2p22p0_FINAL_v3.1.md` (commit `cbb2730`) |
| Total commits since `a903350` | **23** (8 Phase 3 prep + 15 Sprint 2.22.0a sub-sprint commits, including Phase 1.5b citation correction `1a58ed2`) |
| Test progression | 35 baseline regression files → **36** (+1 new `test_sprint_2p22p0a_a2_documentation.py`); **386** isolated assertions in suite |
| Suite aggregator EXPECTED_TOTAL | `374` (post-/10) → **`386`** (post-/11; +12 for A2 doc guard) |
| Coverage gate file | `run_sprint_2p22p0a_suite.py` (Sprint 2.22.0a/10) |
| Test infrastructure manifest | `2p22p0_pre/TESTS_MANIFEST.md` (Sprint 2.22.0a/10) |
| Heroku push status | **NOT YET PUSHED** (Gate 2 lock per Rule #32; Gate 2B = this CHANGELOG approval) |

-----

## 1. Sub-sprint summaries (chronological)

> All hashes + LOC stats verified via `git show --stat <hash>` (Phase 2 R2 verification).

### Sprint 2.22.0a/1 — ENGINE_VERSION + SPRINT_TAG bump

| | |
|---|---|
| Commit | `ce972be` |
| Files | `deploy v2/evaluate_unified.py` (1 file) |
| Stats | 1 file changed, 2 insertions(+), 2 deletions(-) |
| Description | Bumped `ENGINE_VERSION` to `'thammen-sprint2p22p0a-content-and-refusal-templates'`; added `SPRINT_TAG = '2.22.0a'` constant for `/api/health` "3.1.0-sprint{tag}" identifier. |
| Architectural note | KICKOFF §3.4 R2 amendment (commit `5f59cfd`): `api.py:100 version="3.1.0"` stays unchanged — sprint identity is via `SPRINT_TAG` concatenation at the health endpoint, not by re-versioning the FastAPI app. |

### Housekeeping — regression runner

| | |
|---|---|
| Commit | `9107939` |
| Files | `deploy v2/2p22p0_pre/run_regression_2p22p0a.py` (NEW) |
| Stats | 1 file changed, 104 insertions(+) |
| Description | Standalone test runner that walks `deploy v2/` + `deploy v2/tests/` for all `test_*.py` files, subprocess-invokes with `PYTHONIOENCODING=utf-8`, aggregates exit codes. Skips `test_v2_modules.py` (pytest-blocked per Phase 1 audit log). |

### Sprint 2.22.0a/2 — `tier_label` via centralized `_tier_label_for()` (Y3)

| | |
|---|---|
| Commit | `8c16f82` |
| Files | 4 files (evaluate_unified.py + output_briefs.py + index.html + test NEW) |
| Stats | 4 files changed, 249 insertions(+) |
| Description | Added `_TIER_LABEL_BY_METHOD` dict + `_tier_label_for(method)` helper in `evaluate_unified.py`. 8 value-producing methods → `'analytical_range'`; 3 refusal methods → `None`; unknown method → `None` (defensive silent). 7 call sites + 1 def replace what would have been 8 per-site insertions. |
| Architectural pattern | **Pattern 1: Centralized helper (Y3 dispatch)** — single source of truth for method → tier_label mapping. R6 finding during /2 R-protocol: `method` lives nested inside `valuation` block, not at top level, so a literal "add to dict" approach wouldn't work. Y3 centralized dispatch chosen. |
| Test | `test_sprint_2p22p0a_tier_labels.py` (170 LOC, **32 assertions**) |

### Sprint 2.22.0a/3 — `tier_breakdown` section + `n_used` + freshness

| | |
|---|---|
| Commit | `55d9927` |
| Files | 3 files (output_briefs.py + index.html + test NEW) |
| Stats | 3 files changed, 490 insertions(+), 1 deletion(-) |
| Description | New `build_tier_breakdown_section(evaluation)` helper in `output_briefs.py` — returns section dict or `None` for non-hybrid. Renders T1/T2/T3 rows with `weight`, `n`, `value_per_m2_raw`, `value_per_m2_adjusted`. Frontend renders 5-column grid + T3-sources toggle + freshness footer "تقدير مبني على N إعلان كما في YYYY-MM-DD". |
| Architectural pattern | **Pattern 2: Conditional section rendering** — section emitted only when `body.hybrid.tier_breakdown` is present + non-empty (hybrid path only). |
| Test | `test_sprint_2p22p0a_tier_breakdown.py` (286 LOC, **43 assertions**) |

### Sprint 2.22.0a/4 — `use_case_banner` (§6.7 8→3 buckets, refusal-gated)

| | |
|---|---|
| Commit | `d884e34` |
| Files | 4 files (evaluate_unified.py + output_briefs.py + index.html + test NEW) |
| Stats | 4 files changed, 440 insertions(+), 9 deletions(-) |
| Description | `USE_CASE_BANNER` constant in `evaluate_unified.py` per BRIEF v3.1 §6.7. 8 use cases → 3 buckets (5 suitable_for + 2 not_suitable_for + 2 stage5_required_for). Deliberate redundancy per Q2(b) decision. `_use_case_banner_section()` helper refusal-gated via `_tier_label_for(method)` returning `None`. |
| Architectural pattern | **Pattern 3: Output-side gating** — refusal suppression in `output_briefs.py` via existing /2 helper rather than per-builder injection in `evaluate_unified.py` (Anas's architecture refinement per Rule #39 deviation). |
| Test | `test_sprint_2p22p0a_use_case_banner.py` (288 LOC, **64 assertions**) |

### Sprint 2.22.0a/5 — `refusal_reason` + 6 templates + §5.3 precedence chain (/6 MERGED IN)

| | |
|---|---|
| Commit | `b0c62b7` |
| Files | 7 files (refusal_templates.py NEW, district_regimes.json NEW, evaluate_unified.py, output_briefs.py, index.html, test NEW, sample probe NEW) |
| Stats | 7 files changed, 987 insertions(+), 1 deletion(-) |
| Description | New `refusal_templates.py` module — registry of 6 active triggers (5 from §5.1 + 1 NEW `asset_class_out_of_scope` per Q1(d) decision during /5 R-protocol). New `_compute_refusal_reason(method, ...)` 6-level precedence dispatcher in `evaluate_unified.py`. Empty `district_regimes.json` skeleton (`{"events": []}`) per §5.4. `refusal_reason` field injected at 4 refusal sites (lines 1679, 3781, 2415, 2556). New `_refusal_reason_section(evaluation)` helper. `asset_uniqueness` trigger NOT registered (deferred to 2.22.y per §2.3). |
| **`/6` merger note** | Per `2p22p0_pre/BRIEF_2p22p0a_KICKOFF.md` §9.1 row 6 post-shipping annotation: **"`/6` density_gated_district trigger integration — MERGED INTO `/5` per natural precedence chain scope overlap. Implementation shipped within Sprint 2.22.0a/5 (commit `b0c62b7`) — see §5.3 row 1 (`density_gated_district` overrides all). No separate `/6` commit."** No KICKOFF retroactive amendment — engineering precedent per `f00268c` Item 5. |
| Architectural pattern | **Pattern 4: Per-site precedence chain dispatch** — each refusal site calls `_compute_refusal_reason()` with site-specific `method` + `asset_type` + `plot_area_m2` context. Distinct from /7 universal injection pattern because refusal context varies per call site. |
| Test | `test_sprint_2p22p0a_refusal_reason.py` (388 LOC, **109 assertions**) |

### Sprint 2.22.0a/7 — `verification_url` universal injection via `_attach_scope` (R6 architectural finding)

| | |
|---|---|
| Commit | `8de048e` |
| Files | 5 files (verification_url.py NEW, evaluate_unified.py, index.html, test NEW, PHASE3_LOG.md) |
| Stats | 5 files changed, 568 insertions(+), 1 deletion(-) |
| Description | New `verification_url.py` (140 LOC) — SHA-256 → base32 → 12-char token. `THAMMEN_VERIFY_BASE_URL = 'https://thammen.qa/verify'`. URL returns 404 in 2.22.0a (full UI deferred to 2.22.0.1). Universal injection in `evaluate_unified._attach_scope()` — every response (value-producing AND refusal) gets the field, per §5.2 audit-trail requirement. |
| Architectural pattern | **Pattern 5: Universal `_attach_scope` injection** — `_attach_scope` is the single universal gate called on every response (6 call sites: 5 early-exit + 1 main `_build_unified_output`). Both `address` + `valuation_date` are uniformly present BEFORE `_attach_scope` runs. Single-site injection vs hypothetical 6 per-site injections. **Architectural divergence from /5 deliberate**: /5 per-site because context varies; /7 universal because context is uniform. Right pattern matched to actual context requirements (not dogmatic copy of previous sub-sprint). |
| Q1-Q4 design decisions | Q1 — pure deterministic (no salt); Q2 — `valuation_date` directly (local time); Q3 — flat URL (no version prefix); Q4 — falsy address → None (mirror tier_label/refusal_reason pattern). |
| Test | `test_sprint_2p22p0a_verification_url.py` (371 LOC originally — `64` assertions) |

### Sprint 2.22.0a/8 — calc-block visual + adjustment_ledger_directional placeholder

| | |
|---|---|
| Commit | `68738d3` |
| Files | 4 files (output_briefs.py + index.html + test NEW + PHASE3_LOG.md) |
| Stats | 4 files changed, 415 insertions(+), 4 deletions(-) |
| Description | `.calc-block` CSS modifier applied to Stage-3 valuation card: monospace + tabular-nums scoped to `.rv` numeric values, dashed border, `--alt` light-grey background, no box-shadow, line-height 1.6. Arabic labels stay Tajawal (per Q1 refinement). Mobile responsive @media (max-width:480px). `_adjustment_ledger_directional_section()` helper — refusal-gated placeholder at position 4 in section order. Anas Q2(b) refined copy: pure Arabic note_ar (zero Latin chars except "&"), no internal sprint nomenclature, "قريباً" badge (not Latin "Stage 2"). |
| Test | `test_sprint_2p22p0a_calc_visual_and_ledger.py` (292 LOC, **62 assertions**) |

### Sprint 2.22.0a/9 — RICS Red Book Global Standards 2024 + IVS 2024 citation compliance audit

| | |
|---|---|
| Commit | `636c763` |
| Files | 4 files (material_uncertainty.py, test_material_uncertainty.py, test_sprint_2p16p8_muc_enrichment.py, PHASE3_LOG.md) |
| Stats | 4 files changed, 343 insertions(+), 62 deletions(-) |
| Description | Critical citation correction shipped: legacy `"RICS VPS 5"` (×8 sites in `material_uncertainty.py`) replaced. **NOTE: Sprint 2.22.0a/9's verified citation (`VPGA 10 + VPS 3 + IVS 103`, "RICS Red Book Global Standards 2024 / IVS 2024") was ITSELF subsequently corrected by Sprint 2.22.0a/12 Phase 1.5b** (commit `1a58ed2`) — /9 web-search reconnaissance missed the publication-date vs effective-date transition (Red Book published December 2024 but effective 31 January 2025, including VPS 3 → VPS 6 + IVS 103 → IVS 106 renumbering). See §3 two-stage correction and §8 Error 4. |
| R-protocol finding | **Both the KICKOFF brief AND existing code carried incorrect citations**. Anas-verified via authoritative RICS sources (Property Journal + isurv + Lexology + RPC legal commentary + RICS COVID-19 MVU template). |
| Brittle-pin relaxation (Rule #36 anti-pattern) | `test_sprint_2p16p8_muc_enrichment.py:106` pinned literal `'VPS 5'`; relaxed to `'RICS'` substring (Rule #39 deviation justified — same anti-pattern Sprint 2.19.1 corrected across 4 other Sprint test files). |
| Test guards | New `TestRICS2024Compliance` (16 assertions) + `TestShockLayerEnglishMapping` (5) + `TestAssessUncertaintyRecommendation2024` (1) added to `test_material_uncertainty.py`. Total: 35 unit tests, all green. |
| Downstream propagation flagged | 13 sites (`output_briefs.py:565,572,573,580,903,910` + `evaluate_unified.py:338,1807,1814` + `evaluate_v3.py:8,461` + `index.html:709,732`) → propagated in `/12` Phase 1. |

### Sprint 2.22.0a/10 — isolated tests batch consolidation (γ-A hybrid refactor)

| | |
|---|---|
| Commit | `72f5972` |
| Files | 10 files (3 NEW + 6 test refactors + PHASE3_LOG.md) |
| Stats | 10 files changed, 577 insertions(+), 148 deletions(-) |
| Description | Shared `_test_helpers.py` infrastructure across the 6 Sprint 2.22.0a isolated test files (/2-/8). Canonical `Reporter` class + `_check(cond, name, detail)` signature established by /2-/5 Pattern A. `set_stdout_utf8()` boilerplate extracted. NEW `run_sprint_2p22p0a_suite.py` aggregator with pinned `EXPECTED_TOTAL = 374` coverage gate. NEW `2p22p0_pre/TESTS_MANIFEST.md` contract documentation. Mitigation A sequential discipline: each file verified 32/43/64/109/64/62 in isolation before proceeding. |
| Rule #39 deviation (Pattern B adapter) | AST-driven one-shot reorder of 111 callsites in /7+/8 failed on JoinedStr (f-string) positions for Arabic content + arg-span overlap. Fallback: thin file-local `check(name, cond)` adapter wraps `_REPORTER.check(cond, name)`. Reporter convergence achieved; callsite signature drift documented as TD-1 (see §5 below). |
| Anas Q1.5 decision | Generic `_test_helpers.py` (NOT Sprint-suffixed) — infrastructure modules use descriptive purpose names; Sprint nomenclature reserved for test files + CHANGELOGs. |
| Coverage gate result | 374/374 MATCH in 11.0s (budget 30s WITHIN). |

### Sprint 2.22.0a/10 follow-up — TD-1 housekeeping

| | |
|---|---|
| Commit | `011cf47` |
| Files | 1 file (`2p22p0_pre/TESTS_MANIFEST.md`) |
| Stats | 1 file changed, 73 insertions(+), 1 deletion(-) |
| Description | Per Anas course-correction (2026-05-27 PM): Pattern B drift documented as known technical debt §8 TD-1 in `TESTS_MANIFEST.md`, NOT added to /12 final consistency pass list. /12 stays cosmetic + 13-site citation propagation only. Resolution path: Sprint 2.22.y validation hardening OR dedicated tooling Sprint with Arabic-aware AST refactor utility (e.g. libcst). Atomic Sprint discipline preserved (Rule #38) — separate commit before /11. |

### Sprint 2.22.0a/11 — A2 reclassification documentation fix

| | |
|---|---|
| Commit | `d7890ff` |
| Files | 5 files (CHANGELOG_pre_2p22p0_v2.md + test NEW + suite update + manifest + PHASE3_LOG.md) |
| Stats | 5 files changed, 146 insertions(+), 12 deletions(-) |
| Description | KICKOFF F8 cited "BRIEF v3.1 §4.5" but R-protocol caught the typo: v3.1 has no §4.5 row table. Actual mislabel site = `2p22p0_pre/CHANGELOG_pre_2p22p0_v2.md` §4.5 line 143 per `AUDIT_FINDINGS_2p22p0.md` §4.5.a finding #8 + line 379. Applied audit-recommended text verbatim: "Villa" → "apartment_building (DCF refusal — canonical apt-Stage-2 case)". |
| Test guard | NEW `test_sprint_2p22p0a_a2_documentation.py` (118 LOC, **12 assertions**) — prevents silent revert. Reads CHANGELOG file, locates §4.5 row A2, asserts: `apartment_building` present + `Villa` absent + `52/903/90` preserved + full canonical text + `Bug A6 known-safe` + `Safe smoke` preserved + provenance footnote present. |
| Suite update | `EXPECTED_TOTAL: 374 → 386` (+12). `PER_FILE_EXPECTED` gains 7th entry. |
| KICKOFF F8 self-reference correction (3 sites cited by Anas; actual 4) | Deferred to /12 Phase 1 as item 9. |

### Sprint 2.22.0a/12 Phase 1 — 9-item consistency pass batch fix

| | |
|---|---|
| Commit | `f00268c` |
| Files | 7 files |
| Stats | 7 files changed, 79 insertions(+), 43 deletions(-) |
| Items applied | Item 1 (C1 §6.4 H_walk anchors); Item 2 (C2 §5.1 event_name wording clarification); Item 3 (§4.1 use_case_banner parenthetical); **Item 4 (F5 trigger count 5→6) — REVERTED in Phase 1.5**; Item 5 (§9.1 row 6 /6-merger documentation); Item 6 (/7 4 "Pearl A5" labels → "Lusail-as-Pearl-mock" + var rename + comment block); Item 7 (🧮 → 📋 icon collision in `SEC_ICONS['adjustment_ledger_directional']`); Item 8 (RICS citation propagation across **13 sites** — 4 user-facing with verbatim text + 9 internal comments); Item 9 (KICKOFF F8 self-reference — **4 sites** updated; R-protocol found 1 site beyond Anas's spec of 3). |
| R-protocol findings | (1) Item 9 site count = 4 not 3 (line 333 missed in spec); (2) my prior /9 STOP report incorrectly included `evaluate_unified.py:1920/2032/2047/2062` as propagation sites — actual count is exactly 13; (3) Item 4 has 11+ "5 active" references in KICKOFF, only 3 canonical authority sites updated in Phase 1 then reverted in Phase 1.5. |

### Sprint 2.22.0a/12 Phase 1.5 — Item 4 revert: KICKOFF preservation

| | |
|---|---|
| Commit | `cfdc6f1` |
| Files | 2 files (BRIEF_2p22p0a_KICKOFF.md + PHASE3_LOG.md) |
| Stats | 2 files changed, 7 insertions(+), 5 deletions(-) |
| Description | Surgical revert of 3 Item 4 trigger-count edits per Anas decision (signed-historical-contract principle). KICKOFF was signed at Gate 1 (commit `33f7e33`, 2026-05-26) and describes the **plan** at signing time, NOT shipped reality. Sprint 2.22.0a shipped 6 triggers (5 planned + 1 NEW `asset_class_out_of_scope` per /5 Q1d). That delta is a CHANGELOG fact (this document), not a KICKOFF amendment. Engineering precedent within same Sprint: §9.1 row 6 documents /6-merger via post-shipping annotation, not by rewriting original row 6 plan. |
| Items 1+2+3+5+6+7+8+9 from Phase 1 | **PRESERVED** (grep-verified — see §7 below). |
| Result | KICKOFF "5 active" restored to **11 occurrences** (lines 18, 58, 141, 158, 191, 193, 244, 246, 250, 328, 413). KICKOFF "6 active" = **0 hits**. KICKOFF "asset_class_out_of_scope" = **0 hits**. |

### Sprint 2.22.0a/12 Phase 1.5b — Critical RICS/IVS citation correction (multi-AI validation)

| | |
|---|---|
| Commit | `1a58ed2` |
| Files | 7 files (material_uncertainty.py + output_briefs.py + index.html + evaluate_unified.py + evaluate_v3.py + test_material_uncertainty.py + test_sprint_2p16p8_muc_enrichment.py) |
| Stats | 7 files changed, 157 insertions(+), 104 deletions(-) |
| Description | Critical RICS/IVS citation correction. Multi-AI validation (GPT + Gemini independent reviews + Anas web-search verification) caught wrong citations in shipped code BEFORE production push. Sprint 2.22.0a/9 citation (`VPS 3 + IVS 103 + "2024 edition"`) superseded by effective-date-accurate citation (`VPS 6 + IVS 106 + "(effective 31 January 2025)"`). |
| Three-fold error in /9 | (1) **Edition naming**: "2024" → "(effective 31 January 2025)" — Red Book published December 2024 but effective 31 January 2025. (2) **VPS renumbering**: VPS 3 (Valuation Reports, 2022 edition) → **VPS 6** in current effective edition. (3) **IVS renumbering**: IVS 103 (Reporting, IVS 2022) → **IVS 106** (Documentation and Reporting) in IVS effective 31 January 2025. |
| Test guards | `TestRICS2024Compliance` class renamed → **`TestRICS2025Compliance`**; 6 assertion methods renamed (`2024` → `2025_effective_date`, `vps_3` → `vps_6`, `ivs_103` → `ivs_106`); 4 NEW `assertNotIn` regression guards (legacy `VPS 3` + `IVS 103` absent from `muc_clause_ar` + `muc_clause_en`). `TestAssessUncertaintyRecommendation2024` renamed → `TestAssessUncertaintyRecommendation2025`. |
| Multi-AI lesson | Single-AI verification (the /9 web search) missed the publication-date vs effective-date distinction — 2022-era sources read as authoritative for current state. Multi-AI external validation caught it. **Foundational lesson logged**: for evolving regulatory standards (RICS, IVS, QSREB, etc.), multi-AI independent verification is required, not just R-protocol reconnaissance + single-AI web search. Candidate Operational_Rules **#54**. |
| Test results | `test_material_uncertainty.py` unittest: **39/39 PASS** (was 35; +4 new regression guards). Suite aggregator: 386/386 MATCH unchanged. Full regression: 36/36 PASS unchanged. |

-----

## 2. Architectural patterns identified

Five distinct patterns surfaced across sub-sprints `/2`-`/8`. The repeated lesson: **right pattern matched to actual context requirements, not dogmatic copy of previous sub-sprint's strategy**.

| # | Pattern | First instance | Mechanism | When it fits |
|---|---|---|---|---|
| 1 | **Centralized helper (Y3 dispatch)** | /2 `_tier_label_for()` | Single function + lookup dict | Pure function of one input; uniform across call sites |
| 2 | **Conditional section rendering** | /3 `build_tier_breakdown_section()` | Helper returns dict or `None`; caller appends conditionally | Section emitted only for specific path; absent otherwise |
| 3 | **Output-side gating via existing helper** | /4 `_use_case_banner_section()` reusing /2 `_tier_label_for()` | Refusal detection delegated to upstream helper that already encodes the contract | Avoids duplicate refusal-detection logic; preserves single source of truth |
| 4 | **Per-site precedence chain dispatch** | /5 `_compute_refusal_reason()` | Each refusal site calls dispatcher with site-specific context | Context (`method`/`asset_type`/`plot_area_m2`) varies per call site |
| 5 | **Universal `_attach_scope` injection** | /7 `verification_url` | Single inject at universal gate; uniform context | Context (`address`/`valuation_date`) uniform across ALL response paths |

**Architectural divergence between /5 and /7** is deliberate: /5 is per-site because refusal context varies; /7 is universal because verification_url context is uniform. Pattern selection driven by actual context requirements, not by mimicking the prior sub-sprint.

-----

## 3. RICS Red Book Global Standards (effective 31 January 2025) + IVS (effective 31 January 2025) compliance update

### What changed (two-stage correction)

The citation update happened in TWO stages — the second corrected the first:

**Stage 1 — Sprint 2.22.0a/9 (commit `636c763`)**: replaced the legacy 2014/COVID-era `"RICS VPS 5"` citation (which referred to a section that, in the current edition, has been renamed to "Valuation Approaches and Methods" — a different topic) with what was believed to be the verified 2024-edition canonical reference: `"VPGA 10 + VPS 3 + IVS 103"`. Propagated across 13 downstream sites in /12 Phase 1 (commit `f00268c`).

**Stage 2 — Sprint 2.22.0a/12 Phase 1.5b (commit `1a58ed2`)**: multi-AI validation (GPT + Gemini independent reviews + Anas web-search) caught that the Stage-1 citation itself was incorrect — the /9 reconnaissance had treated 2022-edition / intermediate-2024 sources as authoritative for the current effective edition, missing the publication-date vs effective-date transition. Updated to `"VPGA 10 + VPS 6 + IVS 106 (effective 31 January 2025)"`.

The Stage-1 correction was directionally correct (recognised "VPS 5" as outdated) but landed in the wrong sub-section / edition. Stage 2 closed both gaps.

### Final shipped citation

| Component | Section / number | Topic | Edition status |
|---|---|---|---|
| VPGA 10 | (unchanged across editions) | Material Valuation Uncertainty — canonical RICS guidance | Stable |
| **VPS 6** (was VPS 3 in 2022 ed.) | RICS Red Book Global Standards | Valuation Reports — §reporting requirements | **Effective 31 January 2025** |
| **IVS 106** (was IVS 103 in IVS 2022) | International Valuation Standards | Documentation and Reporting | **Effective 31 January 2025** |
| Edition label | "RICS Red Book Global Standards (effective 31 January 2025)" + "IVS (effective 31 January 2025)" | both effective 31 January 2025 | Current |
| Scope-of-uncertainty paragraph (NEW per R3) | Added in /9, preserved in /12 Phase 1.5b | What is affected: value, range, methodology applicability | — |

### Coverage

- **Stage 1 (/9 commit `636c763`)**: `material_uncertainty.py` source-of-truth (~8 sites within the module).
- **/12 Phase 1 (commit `f00268c`)**: downstream propagation across **13 sites** (4 user-facing + 9 internal).
- **Stage 2 (Phase 1.5b commit `1a58ed2`)**: same source-of-truth + downstream sites updated to the effective-date-accurate citation. 7 files touched.

| File | Phase 1.5b sites |
|---|---|
| `material_uncertainty.py` (source-of-truth) | Module docstring, dataclass comment, `regime_muc()` docstring + `muc_clause_ar` + `muc_clause_en` + 2 inline comments + `assess_uncertainty()` recommendation |
| `output_briefs.py` | `title_ar` (line 579), `title_en` (line 580), `title_en` valuer-brief (line 916), 4 comment blocks |
| `index.html` | Arabic banner (line 735), JS comment (lines 709-714) |
| `evaluate_unified.py` | Sample-size threshold comment, `_enrich_material_uncertainty` docstring, MVU fields docstring |
| `evaluate_v3.py` | Module docstring item 3, Sprint 2.14.0 hotfix comment |
| `test_material_uncertainty.py` | Module docstring, class rename + 6 assertion method renames + 4 NEW negative-presence guards, `TestAssessUncertaintyRecommendation2024` rename |
| `test_sprint_2p16p8_muc_enrichment.py` | 1 historical-context comment |

### Verification provenance (Stage 2 — Phase 1.5b)

Final effective-date-accurate citation cross-verified by Anas via:
- **RICS Property Journal** "New Red Book aims to ensure global quality of valuation" (December 2024) — confirmed VPS 3 → VPS 6 renumbering
- **IVSC official IVS 2024** effective 31 January 2025 documentation — confirmed IVS 103 → IVS 106 renumbering
- **Lotus Amity** "2025 International Valuation Standards" — confirmed IVS 106 expanded reporting requirements
- **Property Institute of New Zealand** IVS structure documentation — confirmed current IVS structure
- Multi-AI independent reviews (GPT + Gemini) surfaced the publication-vs-effective-date concern that Stage 1's single-AI verification missed

### R-protocol finds that drove this update

- **/9 R-protocol** (Stage 1): caught the legacy "VPS 5" usage in `material_uncertainty.py` + the KICKOFF brief's original "VPS 1.4.4" claim (no such section). See §8 Errors 1+2.
- **Phase 1.5b multi-AI validation** (Stage 2): caught the /9 citation's own publication-date error before production push. See §8 Error 4.

See §8 below for the four-error transparency log.

-----

## 4. Test infrastructure consolidation (Sprint 2.22.0a/10 + /11)

### Final state

- **6 isolated test files** for sub-sprints /2-/8 (one per /2, /3, /4, /5, /7, /8)
- **1 documentation guard test** added in /11 (`test_sprint_2p22p0a_a2_documentation.py`)
- **Shared `_test_helpers.py` module** at `deploy v2/` root — canonical `Reporter` class + `_check(cond, name, detail)` signature
- **Suite aggregator** `run_sprint_2p22p0a_suite.py` with pinned coverage gate
- **Manifest** `2p22p0_pre/TESTS_MANIFEST.md` documenting the contract for future Sprints

### Coverage gate progression

| Stage | Files | EXPECTED_TOTAL | Notes |
|---|---:|---:|---|
| Post-/10 establishment | 6 | **374** | /2:32 + /3:43 + /4:64 + /5:109 + /7:64 + /8:62 |
| Post-/11 A2 doc fix | **7** | **386** | + /11:12 |

### Helper-signature drift status

| Files | Helper pattern | Status |
|---|---|---|
| /2-/5 (4 files) | Pattern A native (`_check(cond, name)`) | ✅ canonical |
| /7+/8 (2 files) | **Pattern B legacy adapter** (`check(name, cond)` wrapping canonical `_REPORTER.check(cond, name)`) | ⚠️ TD-1 (see §5) |
| /11 (1 file) | Pattern A native | ✅ canonical |

Reporter unified across all 7 files. Drift at callsite signature visibility only. Behavior impact zero (verified by 386/386 coverage gate).

### Wall-time

- Suite aggregator alone: ~11s
- Full regression (36 files): ~58s

-----

## 5. Technical debt documented

### TD-1 — Pattern B callsite signature drift in /7 + /8

**Location:** `2p22p0_pre/TESTS_MANIFEST.md` §8 (commit `011cf47`).

**Files affected:**
- `test_sprint_2p22p0a_verification_url.py` (67 callsites use `check(name, cond)`)
- `test_sprint_2p22p0a_calc_visual_and_ledger.py` (44 callsites use `check(name, cond)`)
- Total: **111 callsites** via file-local thin adapter (NOT 128 — earlier estimate revised to verified count per `\bcheck\(` grep)

**Canonical convention:** `_check(cond, name, detail='')` (Pattern A from /2-/5).

**Behavior impact:** ZERO — adapter routes through canonical `_REPORTER.check(cond, name)`. Coverage gate verifies `386/386` assertions pass through unchanged.

**Why deferred:** AST-driven one-shot reorder script attempted first per Anas Mitigation A's explicit "argument-reorder" instruction. Failed on JoinedStr (f-string) positions for Arabic content + arg-span overlap warning. Manual reorder of 111 callsites (60 multi-line) carries high typo risk + ~60 Edit round-trips.

**Resolution path:** Arabic-aware AST refactor utility (candidate: `libcst` library; not currently a project dependency). Once available: swap args + rename `check` → `_check` across 111 callsites; verify per-file counts (64/64 + 62/62) preserved; drop the file-local adapters.

**Suggested deferral venues** (Anas to decide):
- **Sprint 2.22.y** (validation hardening) — natural fit because /7+/8 are validation-related (verification_url + adjustment_ledger).
- **Dedicated tooling Sprint** — adds `libcst` to `requirements.txt`, builds reusable Arabic-aware refactor utility.
- **Sprint 2.22.0a.1 / .2** — single-purpose follow-up after 2.22.0a ships.

**Rule reference:** Operational_Rules #39 (deviation justification protocol) — the 3-sentence justification appears in Sprint 2.22.0a/10's commit message (`72f5972`).

-----

## 6. F5 acceptance criterion — MET + EXCEEDED

| Metric | KICKOFF §5.1 (signed plan) | Shipped reality |
|---|---:|---:|
| Active refusal triggers | **5** | **6** |
| Deferred triggers | 1 (`asset_uniqueness` per §2.3) | 1 (unchanged) |

**Delta:** +1 NEW `asset_class_out_of_scope` trigger — discovered during Sprint 2.22.0a/5 implementation per Q1(d) design decision, added as engine-capability trigger for the `out_of_scope_v1` refusal path (`evaluate_unified.py` line 2415).

**Status:** **MET + EXCEEDED** (planned 5, shipped 6).

### KICKOFF preservation note

The signed KICKOFF brief (`2p22p0_pre/BRIEF_2p22p0a_KICKOFF.md`) preserves "5 active triggers" phrasing throughout per **signed-historical-contract principle**. The +1 trigger delta is documented HERE in CHANGELOG_v50, NOT by amending the signed brief retroactively. Engineering precedent within the same Sprint: KICKOFF §9.1 row 6 (/6-merger) documents shipped reality via post-shipping annotation, not by rewriting the original row 6 plan.

The Phase 1.5 revert (commit `cfdc6f1`) reversed an incorrect attempt during /12 Phase 1 to retro-amend the KICKOFF to "6 active". See §8 Error 3 below.

-----

## 7. /12 consistency pass — 8 applied + 1 reverted

### 8 items applied (verified by grep — Phase 2 R4)

| # | Item | Site | Verification grep |
|---|---|---|---|
| 1 | C1 §6.4 H_walk anchors | KICKOFF line 320 | "H_walk anchors H1=69/255/75" — 1 hit ✓ |
| 2 | C2 §5.1 event_name wording | KICKOFF line 270 | "When the registry is empty" — 1 hit ✓ |
| 3 | §4.1 single-dimension parenthetical | KICKOFF line 181 | "per §6.7 single-dimension structure" — 1 hit ✓ |
| 5 | §9.1 row 6 /6-merger | KICKOFF line 414 | "MERGED INTO /5" — 1 hit ✓ |
| 6 | /7 Lusail-as-Pearl-mock labels | `test_sprint_2p22p0a_verification_url.py` lines 314, 317, 319, 358 | 4 callsite labels + section header + comment block ✓ |
| 7 | 🧮 → 📋 icon | `index.html` SEC_ICONS line 1251 | `'adjustment_ledger_directional':'📋'` — 1 hit ✓ |
| 8 | RICS citation propagation (13 sites — two-stage correction) | `output_briefs.py` + `evaluate_unified.py` + `evaluate_v3.py` + `index.html` | **Phase 1**: legacy "RICS VPS 5" → `VPGA 10 + VPS 3 + IVS 103` (4 user-facing + 9 internal) ✓. **Phase 1.5b** (multi-AI catch, commit `1a58ed2`): same 13 sites + 7 files total updated again to effective-date-accurate `VPGA 10 + VPS 6 + IVS 106 (effective 31 January 2025)`. See §3 two-stage table + §8 Error 4. |
| 9 | KICKOFF F8 self-reference (4 sites) | KICKOFF lines 144, 198, 333, 419 | 4 sites updated to "BRIEF v2 (`CHANGELOG_pre_2p22p0_v2.md`) §4.5" ✓ |

### 1 item reverted (Phase 1.5)

| # | Item | Sites reverted | Rationale |
|---|---|---|---|
| 4 | F5 trigger count 5 → 6 | KICKOFF lines 141 (F5 row), 244 (§5 header), 246 (§5 intro) | Signed-historical-contract principle (see §6 above + §8 Error 3 below) |

-----

## 8. Four R-protocol + multi-AI error catches — transparency

Engineering transparency section. The R-protocol design intent — "verify each citation by actual file/git inspection BEFORE drafting" — caught Errors 1-3 during this Sprint. **Error 4 escaped single-AI verification entirely and was caught by external multi-AI validation (GPT + Gemini independent reviews + Anas web-search verification)**. Each catch happened BEFORE the error reached production push.

### Error 1 — Caught during Sprint 2.22.0a/9 R-protocol

| Field | Detail |
|---|---|
| Claim | KICKOFF brief F8 + §9.1 cited "VPS 1.4.4 = Material Valuation Uncertainty section" of RICS Red Book |
| Reality | No "VPS 1.4.4" section exists in any RICS Red Book edition. The /9 reconnaissance settled on **VPGA 10 + VPS 3 + IVS 103** as the corrected citation (later itself superseded by Phase 1.5b — see Error 4). |
| Catch mechanism | /9 R-protocol web-search + authoritative source verification |
| Resolution | Verified Stage-1 citation **VPGA 10 + VPS 3 + IVS 103** applied in `material_uncertainty.py` (commit `636c763`) and propagated across 13 downstream sites in /12 Phase 1 (commit `f00268c`). Subsequently superseded by Phase 1.5b effective-date-accurate citation **VPGA 10 + VPS 6 + IVS 106** (see Error 4 below). |
| Lesson | Regulatory citations require web-search verification before signed-brief commitment, regardless of subjective confidence. **Insufficient alone** — see Error 4's multi-AI catch for the stronger requirement. |

### Error 2 — Caught during Sprint 2.22.0a/11 R-protocol

| Field | Detail |
|---|---|
| Claim | KICKOFF F8 cited "BRIEF v3.1 §4.5" as the target for A2 reclassification |
| Reality | v3.1 has NO §4.5 section (its §4 is "H-hypotheses (unchanged from v2)" with no row table). The actual mislabel site is `2p22p0_pre/CHANGELOG_pre_2p22p0_v2.md` §4.5 line 143 — correctly identified in `AUDIT_FINDINGS_2p22p0.md` lines 266 + 379 |
| Catch mechanism | /11 R-protocol file-inspection (grep for "§4.5" across all 2p22p0_pre/ files) |
| Resolution | Data fix applied to actual mislabel site (commit `d7890ff`); KICKOFF F8 self-reference correction at 4 sites (lines 144, 198, 333, 419) shipped as /12 Phase 1 item 9 |
| Lesson | File path + section references require actual file inspection before brief drafting; "v3.1" and "v2" are distinct files and the prior claim conflated them |

### Error 3 — Caught during Sprint 2.22.0a/12 Phase 1 review

| Field | Detail |
|---|---|
| Claim | Item 4 of /12 list — "F5 5 active triggers → 5+1=6 (asset_class_out_of_scope acknowledged)" — would be applied as a /12 consistency-pass amendment to the signed KICKOFF |
| Reality | Misconceived inclusion. Rewriting the signed KICKOFF brief retroactively violates **signed-historical-contract principle**. KICKOFF describes the plan at Gate 1 signing time (commit `33f7e33`, 2026-05-26); the +1 trigger is a CHANGELOG fact about shipped evolution, not a KICKOFF amendment. Engineering precedent within the same Sprint: §9.1 row 6 documents /6-merger via post-shipping annotation, not by rewriting the original row 6 plan |
| Catch mechanism | /12 Phase 1 finding 3 (LOC overrun + 11+ "5 active" references surfaced) + Anas review at Phase 1 STOP |
| Resolution | Phase 1.5 surgical revert (commit `cfdc6f1`) — 3 sites restored to original "5 active" wording. Items 1+2+3+5+6+7+8+9 from Phase 1 PRESERVED. F5 acceptance criterion documented HERE in CHANGELOG_v50 §6 as "MET + EXCEEDED" |
| Lesson | KICKOFF is a frozen historical contract; CHANGELOG documents shipped evolution. Both have distinct temporal scope; do not conflate. /12 list inclusion criteria are: cosmetic + factual-error corrections, NOT plan-vs-reality reconciliation (which belongs in CHANGELOG) |

### Error 4 — Caught during Sprint 2.22.0a/12 Phase 1.5b multi-AI validation

| Field | Detail |
|---|---|
| Claim | Sprint 2.22.0a/9 "verified" citation **`VPGA 10 + VPS 3 + IVS 103` (RICS Red Book Global Standards 2024 + IVS 2024)** — applied uniformly across `material_uncertainty.py` (8 sites) + 13 downstream sites in /12 Phase 1 (commit `f00268c`) + the working-tree CHANGELOG_v50 §§3 + 7 + 8 |
| Reality | The /9 web-search reconnaissance read 2022-edition sources + intermediate-2024 sources as authoritative for the **current effective edition**. Three-fold error: (1) **Edition naming**: the current effective edition is "RICS Red Book Global Standards (effective 31 January 2025)" + "IVS (effective 31 January 2025)" — the Red Book was *published* December 2024 but *effective* 31 January 2025. (2) **VPS renumbering**: Valuation Reports moved from VPS 3 (2022 edition) to **VPS 6** in the current edition. (3) **IVS renumbering**: Documentation and Reporting moved from IVS 103 (2022) to **IVS 106** in IVS effective 31 January 2025; IVS 103 in the current edition is "Valuation Approaches" — a different topic. |
| Catch mechanism | **External multi-AI validation**: GPT raised the broader edition-restructure concern; Gemini caught IVS 103 → IVS 106 specifically; Anas independently web-search-verified via authoritative sources (RICS Property Journal December 2024, IVSC official IVS 2024 docs, Lotus Amity "2025 International Valuation Standards", Property Institute of New Zealand). The /9 single-AI verification missed it — this was a publication-date trap that survived initial review. |
| Resolution | Sprint 2.22.0a/12 Phase 1.5b surgical correction (commit `1a58ed2`) — citation updated across 7 files (`material_uncertainty.py` source + 4 downstream production files + 2 test files). `TestRICS2024Compliance` class renamed → `TestRICS2025Compliance`; 6 assertion methods renamed; 4 NEW `assertNotIn` regression guards added (legacy `VPS 3` + `IVS 103` absent from clauses). `TestAssessUncertaintyRecommendation2024` → `TestAssessUncertaintyRecommendation2025`. Test results: 39/39 unit + 386/386 suite + 36/36 regression — all green. |
| Lesson | **Single-AI web-search verification is insufficient for evolving regulatory standards.** Publication-date ≠ effective-date; both must be verified. Multi-AI independent review (preferably at least one peer-level AI from a different training family) is required for regulatory citations before production push. Candidate Operational_Rules **#54** ("Multi-AI verification for evolving regulatory standards"). |

### Pattern across all four errors

R-protocol reconnaissance happened **before code execution** in Errors 1-3 and caught each one (file-inspection grep + git-show + web-verification). Errors 1-3 were memory/inheritance errors that file inspection exposed.

**Error 4 is qualitatively different.** Single-AI web-search verification in /9 produced a citation that *looked* verified — the search returned authoritative-sounding 2022-era and intermediate-2024 sources that single-AI verification couldn't distinguish from current state. The error survived /9 STOP review, /12 Phase 1 review, and the initial Gate 2B joint review. It was caught only by **multi-AI external validation** (GPT + Gemini + Anas independent web search).

**Foundational lesson logged**: for evolving regulatory standards (RICS Red Book, IVS, QSREB, future RICS Qatar branch publications, etc.), R-protocol reconnaissance + single-AI web search is **necessary but insufficient**. Multi-AI independent verification is required before production push. Operational_Rules **#54 candidate** to capture this — to be drafted in a future Sprint after Anas review.

-----

## 9. Deployment notes

### Push command

Per Operational_Rules #43 (repo root is `C:\Thammen`; app lives in `deploy v2/` subdirectory):

```
git subtree push --prefix "deploy v2" heroku master
```

If subtree split diverges, fall back to named-branch + force push (also per Rule #43):

```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

### Pre-push 6-item checklist (per CLAUDE.md §3 + Project_Instructions §5)

- [ ] `py_compile` on all modified Python files (12 files touched in Sprint 2.22.0a — verified per /1-/12 commits)
- [ ] `node --check` on inline JS extracted from `index.html` (manual verification recommended pre-push since /3+/4+/5+/8 modified renderSection cases)
- [ ] Mobile viewport test 390×844 — calc-block + adjustment_ledger_directional placeholder visual verification by Anas
- [ ] Regression: 36/36 files green (verified post-/12 Phase 1.5 — see §7 above)
- [ ] Suite aggregator: 386/386 MATCH (verified)
- [ ] Smoke test 3 diverse addresses from Heroku post-deploy (see §9 smoke addresses below)

### Smoke addresses (post-deploy)

| Address | Purpose | Expected behavior |
|---|---|---|
| **52/903/90** | A2 audit anchor (apartment_building DCF refusal — canonical apt-Stage-2 case) | HTTP 200; `refusal_reason.trigger_id = 'asset_class_out_of_scope'` or DCF-refusal path; tier_label=None; verification_url present; brief 1-section (`next_steps`) |
| **69/255/75** | Lusail H1 anchor (City Avenues, T3 Aryan hybrid) | HTTP 200; tier_label=`'analytical_range'`; tier_breakdown section present with T2 weight=0.88 + T3 weight=0.12; use_case_banner present; verification_url present |
| **69/329/20** | Lusail H11 anchor (Fox Hills, T2-only) | HTTP 200; tier_label=`'analytical_range'`; tier_breakdown with T2 weight=1.0 (no T3); value_per_m2 ≈ 11,466.08 |

**DO NOT use** `51/835/17` for smoke (triggers compound_large Patch-A flow already exercised in tests + Bug A6 latency 30s timeout risk).

### Cloudflare cache propagation

~5-15 min after Heroku push completes. Verify production via `/api/health` returns the new ENGINE_VERSION:

```bash
curl https://thammen.qa/api/health | grep engine_version
# expected: "thammen-sprint2p22p0a-content-and-refusal-templates"
```

### Carried-forward manual action

Cloudflare Rate Limiting Rule pending from Sprint 2.16.17 scout plan (NOT in Sprint 2.22.0a scope). Anas to action manually post-deploy if desired.

-----

## 10. Rollback procedure (Rule #11)

If post-deploy issues surface:

1. **Heroku CLI** (fastest — instant restore):
   ```
   heroku rollback v128 -a thammen
   ```
   This restores the pre-Sprint baseline.

2. **OR via git** (if Heroku rollback unavailable for some reason):
   - Identify the Heroku-side commit hash for v128 (`044340e` per record).
   - Force-push a deploy v2/ subtree split from `a903350` (Phase 1 baseline on `C:\Thammen`):
     ```
     git subtree split --prefix "deploy v2" a903350 -b heroku-rollback-tmp
     git push heroku heroku-rollback-tmp:master --force
     git branch -D heroku-rollback-tmp
     ```

3. **Verify ENGINE_VERSION** returns to `thammen-sprint2p21p4-t3-aryan-lusail`:
   ```bash
   curl https://thammen.qa/api/health | grep engine_version
   ```

4. **Document the rollback** decision + rationale in the next Sprint log (PHASE3_LOG.md `§D` rollback markers section).

-----

## 11. Looking ahead (out of 2.22.0a scope)

### Sprint 2.22.0b — Stage 2 interactive Q&A flow activation

- Activates `asset_uniqueness` refusal trigger (currently deferred per §2.3; bundled with 3σ compute logic as single logical unit)
- `adjustment_ledger_directional` placeholder → live content (interactive Q&A captures user-confirmed attributes → 3σ inference ledger renders directional adjustments)
- Tower hybrid eligibility expansion
- Stage 2 backend wiring + ReadableStream streaming + bounded adjustment caps (hidden in UI per BRIEF v3.1 §2 row 2)
- Calculator-style visual already shipped in /8; Stage 2 will refine

### Sprint 2.22.y — Validation hardening

- Sensitivity-weighted inference audit (150+ verified inferences, 95%-ile |delta| < 5%, 100%-ile < 15%)
- Density measurement against §1.7 baselines (Pearl, Lusail, West Bay)
- Adversarial simulation
- **TD-1 Pattern B drift cleanup** (Arabic-aware AST refactor of 111 callsites)
- Ship-gate per BRIEF v3.1 §10 #8

### Sprint 2.22.x — PDPPL operational compliance

- Privacy notice
- Consent capture
- RoPA (Record of Processing Activities)
- Breach notification procedure
- Data subject request handling
- Article 15 (general permission) + Article 16 (sensitive data pre-approval)

### Deferred / blocked (NOT in 2.22.0 family)

- **Sprint 2.16.16** — Confirmed Sales DB integration (blocked on secretary data delivery, indefinite delay)
- **Sprint 2.16.17** — Security hardening (slowapi + endpoint lockdown), scout phase complete; carried Cloudflare Rate Limiting Rule pending
- **Sprint 2.21.0.8** — P3 MoJ lstkhdm usage filter, deferred

### Sprint 2.22.0.1 — Post-launch patch (~2 weeks after 2.22.0 ships)

Per BRIEF v3.1 §2:
- Image-embedded watermark engine
- Advanced disclosure mode
- Full verification URL UI (live route at `/verify/<token>` — replaces the 404 from 2.22.0a)
- Lusail Marina §5 audit coverage (deferred from Phase 3 audit)

-----

*Drafted 2026-05-27 PM. Awaiting Anas Gate 2B approval. Phase 3 (Heroku push) follows after Anas signs off on this CHANGELOG.*
