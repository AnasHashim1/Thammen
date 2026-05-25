# Pre-Sprint 2.22.0 BRIEF v2 — 5-Stage Architecture with Interactive Stage 2

**Date drafted:** 2026-05-25 evening
**Replaces:** Pre-Sprint 2.22.0 BRIEF v1 (chat 5b5bd8ae, 2026-05-24) — supersedes; do not act on v1
**Status:** **DRAFT — awaiting Anas sign-off**. Phase 1 (audit) blocked until signed.
**Author:** Claude.ai (methodology lane)
**Implementation:** Claude Code (Phase 1 audit only, no Sprint code yet)
**Production baseline at entry:** `thammen-sprint2p21p4-t3-aryan-lusail` · Heroku v127 · T3 active
**Visualization reference:** `thammen_5_stage_ux_with_qa` (rendered in chat 2026-05-25)

---

## §0 One-paragraph summary

Sprint 2.22.0 implements a **5-stage valuation lifecycle** with an interactive uncertainty-driven Q&A between AVM quick analysis and final valuation. The architecture replaces the 3-stage model from BRIEF v1 (which treated Stage 2 as passive AVM deepening) with a model where Stage 2 is **a dialogue of doubt** — Thammen explicitly asks the user to confirm fields where its internal confidence is low, narrowing MUC from ±20% (Stage 1) to ±12% (Stage 3) based on user-provided ground truth. Stages 4 (broker field verification) and 5 (licensed valuer partner sign-off) are documented in this brief for architectural coherence but deferred to subsequent Sprints. Sprint 2.22.0 ships Stages 0+1+2+3 only — the AVM product with interactive Q&A.

---

## §1 What changed since BRIEF v1 (2026-05-24)

Five material deltas. Each affects scope or defaults:

| # | Delta | Impact |
|---|---|---|
| 1 | **Production baseline:** v1 written against 2.18.1 / v100. Current = 2.21.4 / v127, T3 active. | Hybrid foundation is SHIPPED, not paused. H5 reformulated below. |
| 2 | **Architecture evolved from 3-stage to 5-stage.** v1 had Stage 1+2+3. v2 has Stage 0/Input + Stage 1/AVM-quick + Stage 2/Interactive-Q&A + Stage 3/Valuation + Stage 4/Broker + Stage 5/Valuer. | New D-decisions added (D-stage2-1 through D-stage2-6 + D-strategy-1 through D-strategy-3). Audit plan expanded. |
| 3 | **Stage 2 is interactive, not passive.** v1's Stage 2 = "AVM deepens analysis." v2's Stage 2 = "AVM asks user to confirm uncertain fields." Different UX, different backend, different test plan. | Sprint scope expands ~30-50%. May split into 2.22.0 + 2.22.0.1 (see D12 below). |
| 4 | **Stage 5 partnership strategy documented.** v1 mentioned RICS sign-off vaguely. v2 names the actual Qatar reality: no RICS RVs in Qatar; partnership with locally-licensed valuers (currently charging ~2,000 QAR/report, underutilized) as a business development track. | Stage 5 deferred but with explicit go/no-go criteria. Not built in 2.22.0. |
| 5 | **UI mockup exists.** v1's D10 = "Claude Code drafts mockup in 2.22.0." v2: mockup rendered as `thammen_5_stage_ux_with_qa` in chat 2026-05-25 — iterate from there. | D10 effort reduced. Audit checks frontend feasibility of the mockup specifically. |

---

## §2 The 5-stage architecture

Documented here as the architectural reference. Sprint 2.22.0 ships only Stages 0-3.

### Stage 0 — Input (instant)
User provides identifier: Zone/Street/Building triple, MoJ PIN, or map pin coordinates. No backend work.

### Stage 1 — AVM quick analysis (~5s, ≤5s hard ceiling)
**Backend:** Lite-path classifier + district resolution + MoJ baseline + T2/T3 connector summary if applicable.
**Output to user:**
- Building identified (district, subtype, approximate age)
- Market reference (median QAR/m², n)
- **Per-field internal confidence indicators** (visual: 3-dot ramp green/amber/red)
- Initial valuation range with MUC **±20%** (per E3)
- Statement: "I need to confirm N details about your specific unit"

**Critical design property:** Stage 1 NEVER returns terminal "insufficient_data" (per D11 from v1, ratified). Minimum output is asset_type + confidence + (quick value OR explicit "computing more").

### Stage 2 — Interactive uncertainty-driven Q&A (user time: 30-60s typical)
**Backend:** confidence scoring per field. Fields below threshold trigger questions.
**UX:** 3-5 structured questions on 1-2 screens, each with bounded multiple-choice answers (not free text).
**User submits answers.** AVM updates internal state.

**Default field set (D-stage2-1):**
1. Floor number (for apartments/towers) — confidence usually 0 if Zone/Street/Building points to a building, not a unit
2. Interior condition — confidence always 0 (AVM can't see inside)
3. Recent renovations (last 3 years) — confidence 0
4. Primary view — confidence ~0.3 (GIS can infer from orientation but not actual)
5. Building age (if GIS ±3 years uncertainty matters) — confidence ~0.7 typical
6. Exact unit size (if GIS area is for the whole building, not unit) — confidence variable
7. Occupancy status (vacant/tenanted/owner) — confidence 0

**Critical design property:** Each answer maps to a **bounded adjustment** within Stage 3 (e.g., "floor 8-12" = +5% max for premium apartments). User cannot move value arbitrarily — only refine within calibrated multipliers.

### Stage 3 — Final valuation (10-25s)
**Backend:** Full evaluation with user-confirmed inputs replacing AVM guesses.
**Output:**
- Final value per m² and total
- **Narrowed MUC ±12%** (was ±20% at Stage 1)
- Tier breakdown (T1/T2/T3 with weights and n)
- Adjustment ledger ("Floor 8-12: +5%, Condition Good: ±0%, View Golf: +3%, Total: +8.3%")
- Confidence label: **~90%**

### Stage 4 — Broker field verification (Sprint 2.22.1, post-launch)
Structured field checklist filled by partner broker (initially Thammen's own brokerage staff). 10-12 items, each bounded ±X%, total cap ±15%. MUC narrows from ±12% (Stage 3) to **±8%** with completed verification. Out of scope for 2.22.0; documented here for architectural continuity.

### Stage 5 — Licensed valuer sign-off (Sprint 2.23+, business-dev-gated)
Partnership with Qatar-licensed valuer who reviews Stage 1-4 output, performs independent field verification, and signs the legally-valid report. MUC narrows to **±5%**. Pricing model: 600-800 QAR/report to user, revenue split with partner valuer. Requires business development (partnership contracts, liability framework, QC protocols) before any engineering work. See D-strategy-1 below.

---

## §3 Sprint scope decomposition

| Sprint | Scope | Status |
|---|---|---|
| **2.22.0** | Stage 0 + 1 + 2 + 3 (AVM with interactive Q&A) | THIS BRIEF |
| 2.22.0.1 (optional) | If 2.22.0 too large, split = passive 1+3 first, interactive 2 follow-on | See D12 below |
| 2.22.1 | Stage 4 (broker field verification) | Sprint after 2.22.0 ships and stabilizes |
| 2.22.2 | Telemetry refresh (Stage 1 p95, Stage 2 completion rate, Stage 1 abandonment) | After 2.22.1 |
| 2.23+ | Stage 5 (licensed valuer partnership) | Gated on business development, not engineering readiness |

---

## §4 Pre-Sprint Audit (§5 per Rule #51)

Phase 1 = audit. Claude Code executes; produces `AUDIT_FINDINGS_2p22p0.md` for Claude.ai BRIEF refresh in Phase 2.

### 4.1 Latency profiling (most critical — falsifies H1, H2, H3, H5)

For each of 7 asset_types — villa, compound_small, compound_large, apartment_building (Pearl), apartment_building (Lusail), tower, land — pick 3 production PINs and measure:

- End-to-end `/api/evaluate` p50 + p95
- Per-pipeline-step latency: classifier, GIS resolution, MoJ lookup, T2 connector, T3 connector, brief generation, tier_breakdown computation
- Identify which steps fit a ≤5s Stage 1 budget vs which can't

Output: `latency_profile_2p22p0.json` + a markdown summary table.

### 4.2 Field-level confidence feasibility (falsifies H6)

For each of the 7 candidate Stage 2 fields (D-stage2-1), measure:

- Current data source (GIS field? MoJ field? inferred? guessed?)
- Confidence baseline (high if GIS-canonical, low if inferred, zero if not known)
- Whether the field is currently exposed in `/api/evaluate` response — if not, surface plan

Output: `field_confidence_map_2p22p0.md`.

### 4.3 Brief template structural seams (falsifies H4)

Read `output_briefs.py` (or wherever brief assembly happens) and identify:

- Is the brief assembled in monolithic flow or modular sections?
- Can the assembly be split into "Stage 1 header" + "Stage 3 body" without rewriting?
- What does Stage 2 add (Q&A summary, adjustment ledger) — does this need template support?

### 4.4 Frontend state management capacity (new for v2)

Current `deploy v2/index.html` — is it capable of:

- Multi-screen flow (Stage 1 → Q&A screens → Stage 3) without page reload?
- Holding partial state across SSE chunks?
- Handling user interaction during a streaming response (Stage 2 questions arrive, user answers, response continues)?

If the answer is "needs significant refactor," Sprint 2.22.0 scope expands and must split (D12).

### 4.5 Audit PINs (for end-to-end manual review)

| # | PIN | Asset | Why |
|---|---|---|---|
| A1 | 31/918/99 | Villa Umm Lekhba | Established baseline (CHANGELOG_v37) |
| A2 | 52/903/90 | Villa | Safe smoke (Bug A6 known-safe) |
| A3 | 69/329/20 | Apt Fox Hills (غار ثعيلب) | Apartment T2-only, no T3 — Stage 2 questions feasibility check |
| A4 | 69/255/75 | Apt City Avenues (لوسيل 69) | Full T1+T2+T3 mix — Stage 2 + tier_breakdown rendering |
| A5 | (Claude Code selects) | Low-n PIN | MUC trigger, confidence band testing |

Each PIN: capture current response JSON, identify which fields would trigger Stage 2 questions, and screenshot current UI.

### 4.6 Audit deliverable

`AUDIT_FINDINGS_2p22p0.md` with sections matching §4.1-§4.5 + a synthesis that answers:

1. Is the ≤5s Stage 1 budget achievable for all asset types? Which need refactor?
2. Are the 7 Stage 2 fields all addressable (data source + bounded multiplier) or do some need to wait?
3. Does the brief template need refactor to support staged assembly?
4. Does the frontend need refactor to support multi-screen Q&A flow?
5. Recommendation: ship 2.22.0 monolithic or split into 2.22.0 + 2.22.0.1?

---

## §5 D-decisions (full ratified set)

### Ratified from v1 (no change)

| # | Decision | Resolution |
|---|---|---|
| D1 | Transport for staged response | **SSE (Server-Sent Events)** — modern, simple, no WebSocket overhead, native browser. |
| D2 | Stage 1 latency target | **≤5s hard ceiling, ≤3s typical.** Hard fail above this. |
| D4 | Backward compatibility | **Single endpoint, dual-mode.** `/api/evaluate` continues working as synchronous. `Accept: text/event-stream` triggers staged. |
| D5 | Stage 2 cancellation | **Continue computing, cache result.** User reconnects within 5min → serve cached. Heroku impact low. |
| D6 | Brief structure across stages | **Stage 3 appends to Stage 1.** Stage 1 brief = header (classification + quick value + MUC). Stage 3 brief = body (full valuation + tier_breakdown + adjustments). UI shows them as one progressive document. |
| D7 | Stage 1 confidence labeling | **"تقدير سريع — التحليل العميق جاري"** with explicit MUC ±20%. No "preliminary" badge. |
| D8 | Asset types bypass logic | **No bypass** — always staged even if redundant. Simpler architecture, predictable UX. |
| D11 | Stage 1 minimum output | **asset_type + classifier confidence + (quick value OR explicit "computing").** Never empty, never "insufficient_data" terminal. |

### Reframed from v1

| # | v1 Decision | v2 Resolution |
|---|---|---|
| D3 | Stage 3 scope in MVP | **REFRAMED:** v1 said "Stage 3 deferred to 2.22.1." v2: Stage 3 IS the final valuation (now in 2.22.0). The old "Stage 3 = broker overrides" is now **Stage 4**, deferred to 2.22.1. |
| D10 | UI mockup | **DONE.** Visualization `thammen_5_stage_ux_with_qa` (2026-05-25) is the design reference. Implementation iterates from it. |
| D12 | Sprint decomposition | **REFRAMED:** v1 = 2.22.0 (Stage 1+2 MVP), 2.22.1 (Stage 3 broker), 2.22.2 (telemetry). v2 = 2.22.0 (Stages 0-3 with interactive Q&A), 2.22.1 (Stage 4 broker), 2.22.2 (telemetry), 2.23 (Stage 5 valuer, biz-dev-gated). **Splitting 2.22.0 into 2.22.0 + 2.22.0.1 is contingent on audit findings (§4.4).** |
| D9 | Telemetry refresh | **Ratified, deferred to 2.22.2.** New metrics: Stage 1 p95, Stage 2 completion rate, Stage 1 abandonment rate, Stage 2 average questions answered, Stage 2 "I don't know" rate. |

### New for v2 (Stage 2 specifics)

| # | Decision | Default proposal |
|---|---|---|
| D-stage2-1 | Stage 2 field set | **7 fields:** floor, interior condition, recent renovations, view, building age (if GIS uncertain), exact unit size (if GIS uncertain), occupancy status. Apartments use all 7; villas skip floor + occupancy; land skips most. |
| D-stage2-2 | Confidence threshold for triggering question | **≥0.85 don't ask · 0.50-0.85 ask · <0.50 ask with "critical" flag.** Per-field confidence computed at end of Stage 1. |
| D-stage2-3 | "I don't know" handling | **AVM uses best guess + flags field as "claimed_unconfirmed".** Flag appears in Stage 3 report. MUC widens by per-field unknown-multiplier (e.g., unknown floor = +2% MUC, unknown condition = +3% MUC). |
| D-stage2-4 | Skip Stage 2 entirely | **Yes, with widened MUC ±25-30%.** UI button: "أعطني التقدير الأوّلي مباشرةً". Goes from Stage 1 directly to a Stage-1-confidence final number. |
| D-stage2-5 | User lying / unverified claims | **Accept claim, record with timestamp + "unverified" flag.** Stage 4 broker check catches inconsistencies later. Discrepancies surface in Stage 4 report with MUC adjustment. |
| D-stage2-6 | Questions per screen / UX layout | **3 questions per screen, max 2 screens, visible progress bar.** Plus a "skip remaining" link on screen 2 (returns to Stage 1 confidence). |

### New for v2 (product strategy)

| # | Decision | Resolution |
|---|---|---|
| D-strategy-1 | Stage 5 partnership model | **Locally-licensed Qatar valuers, not RICS RVs.** Partnership with 3-5 valuers initially. Revenue split TBD. Business development separate track from engineering. Not in 2.22.0 scope; tracked as parallel work. |
| D-strategy-2 | Stage 5 go/no-go criteria | **All three required:** (a) 3+ valuers contractually agreed, (b) Qatar regulatory framework researched and clear (MoJ / Qatar Central Bank acceptance criteria), (c) estimated volume ≥120 reports/year per valuer (their break-even). |
| D-strategy-3 | Internal documentation | **E22-bis added to `docs/EMPIRICAL_FINDINGS.md`** documenting the 5-stage architecture + valuer partnership model. Internal only. No public roadmap commitment. |

---

## §6 Falsifiable predictions

These predictions test whether 2.22.0 is the right Sprint and which D-defaults hold. Some predictions being FALSE changes the path.

| # | Hypothesis | Falsified by | Implication if false |
|---|---|---|---|
| **H1** | Current `/api/evaluate` p95 exceeds 5s for at least 3 of 7 asset_types | All asset_types ≤5s | Stage 1 architecture is over-engineering for latency. Use progressive disclosure UI only, skip staged backend. **Sprint 2.22.0 scope reduced to UI work.** |
| **H2** | At least 30% of response fields can be classified as Stage-1-fast (no GIS query beyond cached, no DCF, no comparable grid) | <30% fast fields | Stage 1 budget unrealistic without backend refactor. Sprint 2.22.0 needs prerequisite Sprint 2.21.6 (fast-path optimization) before staged architecture. |
| **H3** | At least one asset_type meets ≤5s naturally today | All exceed 5s | Stage 1 budget itself is too tight — must raise to ≤10s, which weakens UX claim. Renegotiate D2. |
| **H4** | Brief template has structural seams matching Stage 1 / Stage 3 split | Brief is monolithic | Sprint 2.22.0 must include template refactor. Adds 1-2 days. |
| **H5** | (REFRAMED post-hybrid) After Sprint 2.21.4 hybrid, apartment failures are latency-driven, not data-driven | Failures still data-driven | 3-stage architecture isn't the apartment fix — more data sources needed. Reactivate data-expansion Sprints 2.21.4.1+. |
| **H6** | At least 4 of 7 candidate Stage 2 fields have measurable per-field confidence (GIS + MoJ data has per-field metadata) | Confidence is per-record only, not per-field | D-stage2-2 needs different threshold logic — maybe per-asset-type heuristics instead of per-field confidence. Stage 2 design refactored. |
| **H7** | The 5-stage UX mockup flows naturally — 3 users walking through it complete Stage 0-3 in 60-90s without confusion | Users get stuck OR Stage 2 takes >2 min | UI mockup needs redesign before code. Possibly fewer Stage 2 questions (5 instead of 7). |
| **H8** | Frontend `deploy v2/index.html` can support multi-screen flow with state preservation across SSE chunks without major rewrite | Major rewrite needed | Sprint 2.22.0 splits: 2.22.0 = backend staged response, 2.22.0.1 = frontend multi-screen. |

**H5 deserves special note:** Now that hybrid foundation has shipped (2.21.3 + 2.21.4), the apartment data problem is partly solved. If apartments still fail post-hybrid, it's likely latency-driven (Stage 1 helps) OR a data-density problem (more T1/T2/T3 sources needed). The audit answers this empirically.

---

## §7 Test plan (preliminary — locked by audit findings)

**Regression target:** 29/29 from 2.21.4 must remain green.

**New isolated tests for 2.22.0** (estimated 18-25 tests):
- Stage 1 latency ceiling per asset_type (≤5s) — 7 tests
- Per-field confidence scoring — 7 tests (one per Stage 2 field)
- Stage 2 question triggering logic — 5 tests (threshold boundaries)
- Stage 2 "I don't know" handling — 3 tests
- Stage 2 skip path — 2 tests
- SSE streaming integrity — 3 tests

**Usability proxy** (not code-tested, but documented):
- 3 walk-throughs of the 5 audit PINs using the mockup, timing recorded
- Anas reviews recordings, flags friction points

**Post-deploy H-walk:** H1-H8 verified on production after 2.22.0 ships.

---

## §8 What this brief is NOT

- Not a Sprint. No engine version bump. No Heroku push.
- Not a commitment to all 5 stages now. Only Stages 0-3 in 2.22.0.
- Not a commitment to Stage 5. That's contingent on business development outcomes.
- Not implementation guidance for Claude Code beyond Phase 1 audit.
- Not a brief for Sprint 2.22.0 implementation itself — that's Phase 2 (post-audit BRIEF refresh).
- Not a cancellation of any deferred Sprints. 2.21.4.1+ (data expansion) remains a parallel track.

---

## §9 Hand-off and phasing

**Phase 1 — Audit (Claude Code, ~45-90 min):**
1. Read this brief.
2. Execute §4.1-§4.5 captures.
3. Produce `2p22p0_pre/AUDIT_FINDINGS_2p22p0.md`.
4. Return findings to Anas.

**Phase 2 — BRIEF refresh and lock (Claude.ai):**
1. Read AUDIT_FINDINGS.
2. Ratify or amend D-decisions based on findings.
3. Lock H1-H8 with concrete pass criteria.
4. Produce `BRIEF_2p22p0_FINAL.md` (this brief's successor).

**Phase 3 — Implementation (Claude Code):**
1. Read BRIEF_FINAL.
2. Implement per D-decisions.
3. Run regression + new isolated tests.
4. Deploy to Heroku, verify health.

**Phase 4 — Post-deploy H-walk (Claude Code + Anas):**
1. H1-H8 verification on production.
2. Anas visual closure on UX flow.
3. Sprint close: memory hygiene on both layers (Claude.ai userMemories + Claude Code docs).

**Parallel track — Business development (Anas-led):**
1. Exploratory conversations with 3-5 Qatar valuers (D-strategy-1).
2. Legal/regulatory research on Qatar valuation framework (D-strategy-2).
3. Documentation in E22-bis as the path matures (D-strategy-3).

---

## §10 Open questions for Anas before audit begins

| # | Question | Default if no answer |
|---|---|---|
| Q1 | Sprint splitting: 2.22.0 monolithic (all of Stages 0-3 + interactive Q&A in one Sprint) vs 2.22.0 + 2.22.0.1 split? | **Decide after audit (§4.4).** If frontend needs major rewrite, split. Otherwise monolithic. |
| Q2 | Stage 2 field set in D-stage2-1: ratify the 7 fields proposed, or different set? | **7 fields as proposed.** Audit may suggest removing fields with no data source. |
| Q3 | Stage 2 layout in D-stage2-6: 3 questions/screen × max 2 screens, or different layout? | **3 × 2 as proposed.** Adjust based on H7 usability outcome. |
| Q4 | Start business development conversations with valuers in parallel with Phase 1 audit, or wait for 2.22.0 to ship? | **Start in parallel.** Conversations don't block engineering. Insights inform D-strategy-1. |
| Q5 | Should the mockup be tested with 2-3 real users (brokers or property owners) before audit completes? | **Defer to Phase 2.** Audit findings may change the mockup. |

---

## §11 Sign-off

Anas reviews this brief and either:

- **Signs as-is** → Phase 1 audit begins. Brief enters `2p22p0_pre/CHANGELOG_pre_2p22p0_v2.md` in repo.
- **Marks specific points of disagreement** → Claude.ai revises, re-presents, re-signs.

Disagreements are inline; full rewrites should be unnecessary given v1 was already exhaustively reviewed on 2026-05-24.

---

*Sprint 2.21.4 closed 2026-05-25 evening. This brief is the gateway to Sprint 2.22.0. No code change until signed.*
