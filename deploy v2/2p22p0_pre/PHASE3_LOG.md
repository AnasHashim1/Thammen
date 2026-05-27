# Phase 3 Worklog — Sprint 2.22.0

> **Initialized:** 2026-05-26 PM (Phase 3 kickoff)
> **Scope:** Sprint 2.22.0 = 2.22.0a (3-5d) → 2.22.0b (7-10d) + parallel 2.22.x (3-5d PDPPL) + 2.22.y (8-12d validation, ship-gate).
> **Single source of truth:** [`BRIEF_2p22p0_FINAL_v3.1.md`](BRIEF_2p22p0_FINAL_v3.1.md) (signed 2026-05-26)
> **Production baseline at Phase 3 entry:** `thammen-sprint2p21p4-t3-aryan-lusail` · Heroku v127 → v128 (docs-only push, runtime unchanged)
>
> This file is the **operational worklog** for Phase 3 — appends as work progresses. Sprint-level commits + decisions land here so that future sessions reading Phase 3 archaeology see the actual sequence + rationale + rollback markers.

-----

## §A — Entry conditions per BRIEF v3.1 §10

| # | Condition | Status | Evidence |
|---|---|:---:|---|
| 1 | Anas signs BRIEF FINAL v3.1 | ✅ | Phase 3 kickoff message 2026-05-26 PM |
| 2 | Commit `a903350` (Phase 1 audit) pushed to Heroku | ✅ | Heroku v128 released 2026-05-26, engine_version unchanged |
| 3 | 2.22.0a scope confirmed | ✅ | BRIEF v3.1 §2 row 1 |
| 4 | 2.22.0b scope confirmed | ✅ | BRIEF v3.1 §2 row 2 |
| 5 | 2.22.x parallel scope confirmed | ✅ | BRIEF v3.1 §2 row 6 |
| 6 | 2.22.y parallel scope confirmed | ✅ | BRIEF v3.1 §2 row 7 |
| 7 | Phase 3 worklog initialized at `2p22p0_pre/PHASE3_LOG.md` | ✅ | This file |
| 8 | Density baselines confirmed achievable OR density-gating accepted as launch posture | ⏸️ | Pending Step 4 §5 audit + 2.22.y density measurement Sprint |

-----

## §B — Chronological event log

### 2026-05-25 evening — Phase 1 closeout

- `a903350` — BRIEF v2 (CHANGELOG_pre_2p22p0_v2.md) + Phase 1 audit findings + field_confidence_map + audit script + log + latency_profile JSON (33 runs, ~720KB). Committed but NOT pushed.

### 2026-05-26 PM — Phase 3 kickoff

- **Phase 3 kickoff message** received from Anas (Claude.ai BRIEF v3.1 signed; scope decomposition for 2.22.0a/b + 2.22.x + 2.22.y confirmed; commit `a903350` push approved; §5 audit address list proposed)
- Anas approves audit list A1-A4 (Pearl A5 initially deferred, later re-introduced — see §C below)
- Anas adds: Huzoom learning record housekeeping (HYPOTHESIS_REGISTER + SOURCE_EXCLUSIONS + Δ2 backlog entry)

### 2026-05-26 evening — Approved sequence execution

| Step | Action | Commit / Result |
|---|---|---|
| 1 | `git subtree push --prefix "deploy v2" heroku master` per Rule #43 | Heroku v128 released, engine_version unchanged (docs-only push of `a903350`) |
| 2 | Housekeeping commit — `docs/HYPOTHESIS_REGISTER.md` (NEW) | `45bd20f` — 127 insertions, 3 n=1 hypotheses (H_huzoom_1/2/3) |
| 3 | Housekeeping commit — `docs/SOURCE_EXCLUSIONS.md` (NEW) | `791a67a` — 91 insertions, 3 permanent exclusions (bayut + mzadqatar + huzoom.lusail.com) |
| — | Anas reviews + approves both housekeeping commits | 2026-05-26 PM |
| — | Anas amends scope: A5 Pearl re-introduced (ship-gate per BRIEF §1.7 — not deferrable) | Step 4 expanded to 5 cases + Pearl PIN self-discovery upstream |
| 3.5 | Phase 3 worklog initialized — this file | ✅ `9a1c0a1` |
| 4 | §5 audit run — Pearl PIN discovery + 5 cases A1-A5 | ✅ 5/5 cases consistent with Phase 1 baseline. Pearl PIN 66200197 self-extracted via GIS (Districts ANAME=جزيرة اللؤلؤة, DIST_NO=765) + arady T2 fallback (FGRealty/PF/Steps/QatarSale unreachable). 3 critical findings surfaced. |
| 5 | `PHASE3_AUDIT_pre_2p22p0a.md` report | ✅ `53cace0` — 9 audit artifacts bundled (PHASE3_AUDIT report + 4 scripts + 4 JSONs + smoke logs) |
| 6 | STOP and await Anas approval for 2.22.0a implementation | ✅ Anas reviewed `cbb2730` (BRIEF v3.1 housekeeping commit) + `53cace0` (audit artifacts) → green-lit Phase 3 Step 7 |
| 7 | KICKOFF brief drafted + reviewed + signed | ✅ `33f7e33` "Housekeeping: BRIEF_2p22p0a_KICKOFF.md (signed) — 2.22.0a contract". Draft passed 5 mandatory + 4 minor edit rounds (E1-E5 + M1-M4); 2 cosmetic items (C1+C2) deferred to sub-sprint 2.22.0a/12 final consistency pass. **Gate 1 of 3 approval gates passed.** |
| Next | Sub-sprint 2.22.0a/1 — ENGINE_VERSION bump + Pydantic schema additions | ⏸ About to start. Single-purpose commit per Rule #38; ~30 LOC; `api.py` + `evaluate_unified.py`. NO Heroku push (Gate 2 lock). STOP after this sub-sprint, report diff + tests-green, await Anas signal before 2.22.0a/2. |
| 8 | Sub-sprint 2.22.0a/1 — ENGINE_VERSION + SPRINT_TAG bumped | ✅ `ce972be` — single-purpose, 30 LOC. `thammen-sprint2p22p0a-content-and-refusal-templates`. Tests green. |
| 9 | Sub-sprint 2.22.0a/2 — `tier_label` field via centralized `_tier_label_for` dispatch (Y3 helper pattern) | ✅ `8c16f82` — 32 isolated tests PASS. 8 value-producing methods → `'analytical_range'`; 3 refusal methods → `None` (silent unknown). |
| 10 | Sub-sprint 2.22.0a/3 — `tier_breakdown` block + Y3 helper `build_tier_breakdown_section` | ✅ `55d9927` — 43 isolated tests; hybrid_t2 outputs render per-tier evidence + freshness footer. |
| 11 | Sub-sprint 2.22.0a/4 — `use_case_banner` (§6.7 8 use cases → 3 buckets, refusal-gated) | ✅ `d884e34` — 64 isolated tests; banner prepended after tier_breakdown in 4 audience briefs. |
| 12 | Sub-sprint 2.22.0a/5 — `refusal_reason` + 6 §5.3 precedence chain triggers | ✅ `b0c62b7` — 109 isolated tests + 33/33 regression. **/6 merged into /5** (density_gated_district trigger integration absorbed by §5.3 precedence chain implementation — KICKOFF §9.1 row 6 update flagged for /12 final consistency pass). |
| 13 | Sub-sprint 2.22.0a/7 — `verification_url` universal injection via `_attach_scope` | ✅ `8de048e` — R6 architectural finding: `_attach_scope` is the universal gate called on every response (6 call sites). Both `address` + `valuation_date` are uniformly populated before `_attach_scope` runs → single-site injection (1 location in `_attach_scope`) replaces hypothetical 6 per-site injections. Symmetric with existing `service_scope` pattern. Architectural divergence from /5 deliberate: /5 is per-site because refusal context varies; /7 is universal because verification_url is orthogonal to method/tier_label/refusal_reason gating. 64 isolated tests + 34/34 regression. |
| 14 | Sub-sprint 2.22.0a/8 — calculator-style visual + adjustment_ledger_directional placeholder | ✅ `68738d3` — Q1 confirmed-with-refinement (monospace + tabular-nums scoped to `.rv` numeric values only; Arabic labels stay Tajawal); Q2 (b) with Anas copy refinement (pure Arabic, no Latin inline, no internal sprint nomenclature); Q3 confirmed (helper backend touch in `output_briefs.py`, position 4 after use_case_banner); Q4 (α) with badge refinement (Arabic `قريباً` not Latin `Stage 2`). `_adjustment_ledger_directional_section` helper added; 4 audience briefs prepend at position 4 (refusal-gated identical to /4). `.calc-block` CSS modifier applied to valuation card line 892. 62 isolated tests + 35/35 regression. |
| 15 | Sub-sprint 2.22.0a/9 — RICS Red Book 2024 + IVS 2024 citation audit on `material_uncertainty.py` | ✅ `636c763` — Critical citation correction shipped: `"RICS VPS 5"` (×8 sites) replaced with verified 2024-edition canonical citation **VPGA 10 + VPS 3 + IVS 103**. R6 web-verified by Anas after R-protocol caught both the brief's "VPS 1.4.4" error and the current code's "VPS 5" error. R3 element-3 scope-of-uncertainty paragraph strengthened (explicit "value / range / methodology" disclosure). `_shock_layer_name_en()` helper + `_SHOCK_LAYER_NAME_EN_BY_AR` translation dict added (no `name_en` on `ShockLayer` — /9 stays surgical, /12 ScopeNote: market_regime.py untouched). `test_material_uncertainty.py` brittle "VPS 5" pins replaced with structural assertions (Rule #36 anti-pattern correction); new `TestRICS2024Compliance` class + `TestShockLayerEnglishMapping` class + `TestAssessUncertaintyRecommendation2024` class added (35 unit tests total, all green). `test_sprint_2p16p8_muc_enrichment.py:106` brittle "VPS 5" pin relaxed to 'RICS' substring (minimal Rule #39 deviation — same anti-pattern Sprint 2.19.1 corrected across 4 other Sprint test files; relaxation logically part of /9 citation work). Downstream propagation flagged for /12: **13 sites** (`output_briefs.py:572,573,580,903,910`, `evaluate_unified.py:338,1807,1814,1920,2032,2047,2062`, `evaluate_v3.py:8,461`, `index.html:709,732`); **4 user-facing** (output_briefs.py:572,573,903 + index.html:732). /12 list now **9 items** (was 8). Regression 35/35 green. |
| 16 | Sub-sprint 2.22.0a/10 — isolated tests batch consolidation (γ-A hybrid refactor) | ✅ `72f5972` — `_test_helpers.py` NEW (90 LOC, Anas Q1.5 generic name): canonical `Reporter` class + `_check(cond, name, detail)` signature established by /2-/5 + `set_stdout_utf8()` boilerplate extracted. 6 isolated test files refactored to import shared helper. **Pattern A (4 files /2-/5)** trivially refactored — already-canonical signature → just drop module-globals + import. **Pattern B (2 files /7-/8)** uses thin file-local `check(name, cond)` adapter routing through canonical `_REPORTER.check(cond, name)` — Rule #39 deviation justified: AST-based one-shot reorder script of 111 callsites failed on JoinedStr (f-string) positions for Arabic content; fall-back adapter preserves Reporter convergence without 111 typo-risk callsite edits. `run_sprint_2p22p0a_suite.py` NEW (180 LOC): subprocess-invokes 6 files, parses `PASSED: X/Y`, pins `EXPECTED_TOTAL = 374` + `PER_FILE_EXPECTED` dict, fails-loud on coverage drift (Mitigation C). `2p22p0_pre/TESTS_MANIFEST.md` NEW (~290 LOC): contract documentation for future Sprints. Mitigation A sequential discipline executed — each file verified 32/43/64/109/64/62 in isolation before proceeding. Final: aggregator 374/374 MATCH in 11.0s (budget 30s WITHIN). Full regression 35/35 green in 51.5s. |
| 16.5 | Sprint 2.22.0a/10 follow-up — TESTS_MANIFEST.md §8 TD-1 housekeeping | ✅ `011cf47` — Per Anas course-correction from /10 review (2026-05-27 PM): Pattern B drift documented as known technical debt §8 TD-1 (~74 LOC addition) in `TESTS_MANIFEST.md`, NOT added to /12 final consistency pass. /12 stays cosmetic + 13-site RICS citation propagation only. Resolution path: Sprint 2.22.y OR dedicated tooling Sprint with Arabic-aware AST refactor utility (libcst). Atomic Sprint discipline preserved (Rule #38). |
| 17 | Sub-sprint 2.22.0a/11 — A2 reclassification documentation fix | ✅ `d7890ff` — KICKOFF F8 cited "BRIEF v3.1 §4.5" but R-protocol caught the typo: v3.1 has no §4.5 row table. Actual mislabel site = `CHANGELOG_pre_2p22p0_v2.md` §4.5 line 143 per `AUDIT_FINDINGS_2p22p0.md` §4.5.a finding #8 + line 379. **Q1 (β)** confirmed — applied audit-recommended text verbatim: "Villa" → "apartment_building (DCF refusal — canonical apt-Stage-2 case)". Amendment provenance footnote added below the audit-PIN table. **Q2 (i)** confirmed — `test_sprint_2p22p0a_a2_documentation.py` NEW (12 assertions, ~120 LOC including helper boilerplate; covers 4 audit-spec invariants + 2 preservation invariants + 3 provenance-note invariants). **Q3 (ii)** confirmed — TD-1 housekeeping landed in separate atomic commit `011cf47` before this commit. **Rule #39 LOC overrun**: KICKOFF F8 estimated <10 LOC; actual ~40 LOC; overrun justified by test file boilerplate (KICKOFF estimate didn't account for it). KICKOFF F8 self-reference correction (3 sites: lines 144, 198, 419) deferred to /12 as item 9. /12 list now **9 items** (was 8). Suite aggregator updated: `EXPECTED_TOTAL = 386` (374 + 12). Regression: 12/12 new + 386/386 suite + 36/36 full regression green. |
| 18 | Sub-sprint 2.22.0a/12 Phase 1 — 9-item consistency pass batch fix | ✅ `f00268c` — Single atomic commit covering all 9 cosmetic + functional items: C1 §6.4 H_walk anchor reference (lines 320: "Phase 3 §5 audit cases A1+A3-equivalent" → "H_walk anchors H1=69/255/75 + H11=69/329/20"); C2 §5.1 event_name wording clarification (line 270 verbosity reformulated for empty-registry semantics); §4.1 use_case_banner parenthetical (line 181: "per asset_type/audience" → "per §6.7 single-dimension structure"); F5 trigger count 5 → 6 (line 141 F5 row + line 244 §5 header + line 246 §5 intro all updated; +1 NEW asset_class_out_of_scope acknowledged) **[REVERTED IN /12 PHASE 1.5 — see row 18.5]**; §9.1 row 6 documentation (line 414: "(absorbed into /5)"); /7 sample case labeling correction (test_sprint_2p22p0a_verification_url.py — 4 "Pearl A5" labels → "Lusail-as-Pearl-mock" with comment block explaining mock-fixture nature); /8 🧮 → 📋 icon collision resolved (index.html SEC_ICONS line 1251); /9 RICS citation propagation across **13 sites** (4 user-facing: output_briefs.py:572,573,903 + index.html:732 with full verified text "RICS Red Book Global Standards 2024 (VPGA 10 + VPS 3) و IVS 2024 (IVS 103)"; 9 internal comments: output_briefs.py:565,580,910 + evaluate_unified.py:338,1807,1814 + evaluate_v3.py:8,461 + index.html:709 all updated to consistent VPGA 10 + VPS 3 + IVS 103 reference); KICKOFF F8 self-reference (4 sites: lines 144, 198, 333, 419 — discovered 1 additional site beyond Anas's spec of 3, all 4 corrected for consistency). **R-protocol findings**: (1) F8 self-reference site count = 4 not 3; (2) my prior /9 STOP report incorrectly included evaluate_unified.py lines 1920/2032/2047/2062 as propagation sites — actually they are per-property "تحفظ مادي" banners without VPS citation, the real count is exactly 13 hits as Anas specified. Suite aggregator 386/386 MATCH preserved (no assertion count change). Full regression 36/36 green. |
| 18.5 | Sub-sprint 2.22.0a/12 Phase 1.5 — Item 4 revert: KICKOFF preservation | ✅ (next commit) — Per Anas decision 2026-05-27 PM: Item 4 trigger-count edits reverted to preserve signed-historical-contract principle. KICKOFF was signed at Gate 1 (commit `33f7e33`); it describes the PLAN at signing time, NOT shipped reality. Sprint 2.22.0a shipped 6 triggers (5 planned + 1 NEW `asset_class_out_of_scope` per /5 Q1 d). That delta is a CHANGELOG fact (to be documented in Phase 2 `CHANGELOG_v50.md`), NOT a KICKOFF amendment. Engineering precedent within same Sprint: §9.1 row 6 documents /6-merger via post-shipping annotation, not by rewriting original row 6 plan. Item 4 inclusion in /12 list was misconceived. **Surgical revert**: 3 sites restored to original wording (line 141 F5 row "5 active" + line 244 §5 header "5 active + 1 deferred" + line 246 §5 intro "5 active triggers"). Items 1+2+3+5+6+7+8+9 from Phase 1 PRESERVED (verified by grep). KICKOFF "5 active" count restored to 11 occurrences (lines 18, 58, 141, 158, 191, 193, 244, 246, 250, 328, 413). F5 acceptance criterion status to be documented in `CHANGELOG_v50.md` Phase 2 as: "MET + EXCEEDED (planned 5, shipped 6)". Suite aggregator 386/386 MATCH unchanged. Full regression 36/36 green. |

### Verification side-checks (per Anas review note 3 items)

| # | Check | Result |
|---|---|---|
| V1 | `Operational_Rules.md` §42 cross-reference exists | ✅ PASS — Rule #42 "Deferred-Work Documentation" at line 969. Cross-reference in SOURCE_EXCLUSIONS valid. |
| V2 | PHASE3_LOG.md exists + Δ2 backlog entry | ❌ FAIL → this file fixes it |
| V3 | Huzoom syndication claim verifiable on T2 substitutes (FGRealty + 3 others) | ⚠️ PARTIAL PASS — arady confirmed Huzoom syndication via token `'huzoom'` in Pearl listings page. FGRealty/PropertyFinder/Steps/QatarSale all unreachable from sandbox today (404 + DNS fail). SOURCE_EXCLUSIONS substitute list update (add arady) deferred to next docs wave per Q3 — see §G follow-up below. |

-----

## §C — Decision log (Phase 3)

| Date | Decision | Rationale | Reversal cost |
|---|---|---|---|
| 2026-05-26 | Push `a903350` to Heroku as standalone docs-only deploy | BRIEF §10 entry condition #2; runtime unchanged; safe per Rule #32 docs-only carve-out; Anas explicit consent | Trivial — `heroku rollback` to v127 |
| 2026-05-26 | A5 Pearl re-introduced into §5 audit cohort after initial deferral | Pearl is ship-gate target zone per BRIEF v3.1 §1.7 — density baselines + heartbeat metric. Cannot defer Pearl coverage AND keep 2.22.0 retail launch path open. | Negligible — adds ~6-8min wall time |
| 2026-05-26 | Lusail Marina + tower + compound_small remain deferred to 2.22.0.1 | Single-purpose Sprint discipline (Rule #38). These zones serve §11 90-day monitoring heartbeat, not 2.22.0a/b runtime paths. Including them = scope creep on MVP. | Documented as "deferred coverage" gap in PHASE3_AUDIT report; tracked in §F below. |
| 2026-05-26 | Δ2 corner verification via ROADFlowlnA filed as backlog (NOT 2.22.0a) | Methodology change (verify before adjust), not empirical rate claim — different track from H_huzoom_1 (which IS empirical, n=1). Filed as post-2.22.0a sprint candidate per §F. | None — pure docs filing |
| 2026-05-26 | Initialize PHASE3_LOG.md at `2p22p0_pre/PHASE3_LOG.md` (not `deploy v2/`) | BRIEF v3.1 §10 #7 specifies this canonical path. Anas's verification check at `deploy v2\PHASE3_LOG.md` interpreted as oversight — the brief governs. | Trivial — file is single-source-of-truth for Phase 3 worklog, location stable |
| 2026-05-26 | **Defer `asset_uniqueness` refusal trigger + 3σ outlier compute to 2.22.y** (single logical unit) | Anas's "no dead code in production" discipline applied to §1.6 BRIEF v3.1 trigger #4: dead code = smell + test burden on inactive path + §1.6 contract promises active triggers + accidental activation risk on refactor. Cleaner partition: 2.22.0a ships 5 active triggers (4 inherited + 1 NEW `density_gated_district`); `asset_uniqueness` bundled with 3σ compute, both ship in 2.22.y. | Negligible — re-enabling later is additive (insert into §5.3 precedence chain between rows 3 and 4). |
| 2026-05-26 | **Sign BRIEF_2p22p0a_KICKOFF.md as 2.22.0a contract** (commit `33f7e33`) | Gate 1 of 3 approval gates passed. Brief survived 5 mandatory + 4 minor edit rounds via Anas review (E1-E5 covering Marina inconsistency / Heroku app name placeholder concern / R1 ambiguity / 81-test count consistency / LOC reconciliation; M1-M4 covering calculator visual concreteness / format syntax / Pearl risk LOW→MEDIUM / extent magnitude strip). 2 cosmetic items C1+C2 deferred to sub-sprint 2.22.0a/12. | Trivial — brief revisions are docs-only; reverting the contract is a follow-up docs commit. |

-----

## §D — Rollback markers

| Marker | Heroku version | Engine | Description |
|---|---|---|---|
| **PHASE3_ENTRY** | v127 → v128 | `thammen-sprint2p21p4-t3-aryan-lusail` | Phase 3 entry baseline; docs-only push only |
| `ce972be` /1 | NOT YET PUSHED (Gate 2 lock) | `thammen-sprint2p22p0a-content-and-refusal-templates` | ENGINE_VERSION + SPRINT_TAG bumped; first 2.22.0a code commit |
| `8c16f82` /2 | NOT YET PUSHED | (same) | `tier_label` field via Y3 helper `_tier_label_for` |
| `55d9927` /3 | NOT YET PUSHED | (same) | `tier_breakdown` block + Y3 helper `build_tier_breakdown_section` |
| `d884e34` /4 | NOT YET PUSHED | (same) | `use_case_banner` §6.7 8→3 buckets, refusal-gated |
| `b0c62b7` /5 | NOT YET PUSHED | (same) | `refusal_reason` + 6 §5.3 precedence chain triggers (/6 merged in) |
| `8de048e` /7 | NOT YET PUSHED | (same) | `verification_url` universal injection via `_attach_scope` (R6) |
| `68738d3` /8 | NOT YET PUSHED | (same) | calculator-style visual + adjustment_ledger_directional placeholder |
| `636c763` /9 | NOT YET PUSHED | (same) | RICS Red Book 2024 + IVS 2024 citation audit — VPGA 10 + VPS 3 + IVS 103 |
| `72f5972` /10 | NOT YET PUSHED | (same) | isolated tests batch consolidation — shared `_test_helpers.py` + suite aggregator + manifest |
| `011cf47` /10.follow | NOT YET PUSHED | (same) | TESTS_MANIFEST.md §8 TD-1 housekeeping (Pattern B drift documented) |
| `d7890ff` /11 | NOT YET PUSHED | (same) | A2 reclassification doc fix — CHANGELOG_pre_2p22p0_v2.md §4.5 row A2 |
| `f00268c` /12.P1 | NOT YET PUSHED | (same) | /12 Phase 1 — 9-item consistency pass batch fix (cosmetic + UX + RICS propagation 13 sites) |
| `(pending)` /12.P1.5 | NOT YET PUSHED | (same) | /12 Phase 1.5 — Item 4 revert (KICKOFF preservation of signed "5 active" wording) |

Future code-change commits land here with `git log -1 --oneline` snapshot + Heroku release number for rapid rollback.

-----

## §E — Sprint sequence + status

| Sprint | Scope | Status | Owner / Branch |
|---|---|---|---|
| **2.22.0a** | Brief content + tier_breakdown UI + RICS Red Book audit + A2 reclassification + use-case banner + dynamic refusal triggers + mandatory refusal reasons + tier renaming + verification URL generation | ⏸️ Awaiting §5 audit completion + Anas approval | Claude Code / master (single-purpose commits) |
| **2.22.0b** | 5-stage UX (Stages 0-3) + ReadableStream streaming + bounded adjustment caps (hidden in UI) + silent recompute + calculator-style visual + density gating logic | ⏸️ Sequential after 2.22.0a | Claude Code / master |
| **2.22.x** | PDPPL operational compliance (privacy notice, consent capture, RoPA, breach notification, data subject request handling) | ⏸️ Parallel to 2.22.0b | Claude Code / master |
| **2.22.y** | Validation hardening + sensitivity-weighted inference audit + density measurement + adversarial simulation | ⏸️ Parallel to 2.22.0b, ship-gate per BRIEF §10 #8 | Claude Code + methodology research / master |
| 2.22.0.1 | Image-embedded watermark + advanced disclosure mode + full verification URL UI | ⏸️ Post-launch patch (~2 weeks after 2.22.0 ships) | TBD |

-----

## §F — Backlog spotted during Phase 3 kickoff (not in 2.22.0a)

These are work-items surfaced during Phase 3 setup that do **NOT** belong in 2.22.0a per Rule #38 single-purpose discipline. Filed here for future Sprint planning.

### Δ2 — Corner verification via ROADFlowlnA layer

```
Status            Backlog — post-2.22.0a Sprint candidate (suggest 2.23.0
                  or first available post-2.22.0a slot)
Type              Methodology change (verify before adjust). NOT an
                  empirical rate claim — so does NOT need n>=10 validation.
                  Different track from H_huzoom_1 (which IS empirical).
First proposed    2026-05-26 (Claude.ai Huzoom Lusail learning session
                  outcome)

Spec
  - Stage-1 new output field:
      corner_status ∈ {
        mid_block, corner_standard, corner_T, corner_X,
        highway_adjacent, flag_lot, ambiguous
      }
  - Method:
      ROADFlowlnA segments intersecting CadastrePlots polygon with 5m
      buffer. Distinct segment count + per-segment ROADCLASS.
  - Edge cases:
      * roundabout / cul-de-sac (1 ring) → mid_block
      * flag lot (0 segments inside polygon)   → manual review
      * L2-adjacent (ROADCLASS=L2)             → highway_adjacent
                                                  (NOT corner)
  - Stage 2 premium gate:
      Corner premium applies only when
        corner_status ∈ {corner_standard, corner_T, corner_X}
  - Replaces:
      Any current reliance on listing-text "corner" claims when applying
      premium adjustments.

Sprint dependencies
  - Builds on existing CadastrePlots + ROADFlowlnA GIS layers (no new
    data sources)
  - Stage 1 output schema needs a corner_status field (engine response
    addition)
  - Stage 2 D-stage2-7 bounded caps must check corner_status before
    applying the corner premium

Acceptance criteria
  - 5 known reference cases produce expected corner_status (positives +
    negatives + edge)
  - Listing-text "corner" claim that contradicts corner_status surfaces
    in the adjustment ledger as "claim unverified — premium NOT applied"
  - End-to-end test: 56/565/21 (multi-QARS villa, known mid-block)
    → corner_status = mid_block → no corner premium
```

### (other backlog items will append here as Phase 3 progresses)

-----

## §G — Open audit items (Phase 3-level, distinct from Sprint-level)

| Item | Owner | Status / Trigger |
|---|---|---|
| Pearl PIN discovery (FGRealty → GIS Districts → QARS_Point) | Claude Code (Step 4) | ✅ DONE — PIN 66200197 verified; commit `53cace0` artifacts |
| Huzoom syndication FGRealty cross-check (incidental to Pearl) | Claude Code (Step 4) | ✅ PARTIAL DONE — arady confirms; FGRealty unreachable today |
| Lusail Marina, tower-elsewhere, compound_small PIN discovery | TBD | Sprint 2.22.0.1 §5 audit |
| Property graph density measurement against §1.7 baselines | 2.22.y engineering | Ship-gate validation |
| Sensitivity-weighted inference audit (150+ identity verifications) | 2.22.y engineering | Ship-gate validation |
| **C1 — §6.4 wording fix in KICKOFF brief** | Sub-sprint 2.22.0a/12 (final consistency pass) | Replace "(Phase 3 §5 audit cases A1+A3-equivalent)" with **"(per H_walk anchors H1=69/255/75 + H11=69/329/20)"** — Anas review feedback 2026-05-26. A3 = Umm Lekhba villa not Fox Hills; canonical anchors are H1+H11 from H_walk. |
| **C2 — §5.1 footer wording fix in KICKOFF brief** | Sub-sprint 2.22.0a/12 (final consistency pass) | Replace `"Default event_name='' so the trigger fires correctly even with empty registry"` with **"Default event_name='' handles events without an event_name attribute without breaking template substitution. When registry is empty, the trigger doesn't fire (no event to match)."** — Anas review feedback 2026-05-26. Original phrasing was ambiguous about trigger activation semantics under empty-registry. |
| **arady inclusion in `SOURCE_EXCLUSIONS.md` substitute list** | Next docs wave (NOT 2.22.0a per Q3 decision) | V3 PARTIAL PASS surfaced that `SOURCE_EXCLUSIONS.md` substitute list (FGRealty/PF/Steps/QatarSale) was incomplete — arady actually carries Huzoom syndication today; documented for future docs commit. |

-----

*Worklog initialized 2026-05-26 PM as Phase 3 entry condition #7 per BRIEF v3.1 §10. Appends as work progresses. NOT a Sprint. No engine version bump. Pure docs.*
