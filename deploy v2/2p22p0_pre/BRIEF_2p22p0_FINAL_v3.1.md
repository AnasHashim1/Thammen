# Pre-Sprint 2.22.0 BRIEF FINAL v3.1 — Ship-Ready

**Date locked:** 2026-05-26 PM (third iteration)
**Replaces:** BRIEF FINAL v2 (`BRIEF_2p22p0_FINAL_v2.md`, earlier today). v2 superseded; do not act on it.
**Status:** **FINAL v3.1 — awaiting Anas sign-off.** Phase 3 (implementation) blocked until signed.
**Author:** Claude.ai (methodology lane)
**Implementation:** Claude Code (Phase 3)
**Production baseline at entry:** `thammen-sprint2p21p4-t3-aryan-lusail` · Heroku v127 · T3 active
**Audit basis:** `AUDIT_FINDINGS_2p22p0.md` (Phase 1, 2026-05-26, commit `a903350`, unpushed)
**Visualization reference:** `thammen_5_stage_ux_with_qa` (2026-05-25)
**Adversarial review:** Three rounds (two AI models in parallel, independent sessions). Round 3 reached convergent shippable verdict.

---

## §0 Changelog — three-iteration map

### v1 → v2 deltas (eight, documented in superseded v2 brief)
Q5 phase-split, Q1 asymmetric ceiling, H5 reframe, H6 falsification, D1 swap, A2 reclassification, Stage 5 three-path framework, D-strategy refresh.

### v2 → v3 deltas (six, from round 2 convergent review)

| # | Delta | Round 2 source |
|---|---|---|
| **v3-1** | **Soften refusal language**: "we refuse" / "exceeds boundaries" → "this property requires enhanced review" / "specialized assessment recommended". Same backend triggers, different user-facing language. | Both AIs converged |
| **v3-2** | **Dynamic refusal thresholds, not hard cutoffs**: previously refused at >15M QAR / n<5 / >30,000 m². Now context-aware: refusal triggers only when comp density genuinely sparse OR estimated value >3 standard deviations from district median. Hard floors preserved only for extreme cases. | Both AIs converged |
| **v3-3** | **Soften public-facing precision claims**: drop "±12%", "±8%", "±5%", "confidence ~90%" from retail UI. Keep numeric precision internally for engineering, calibration, B2B partner contracts under NDA. Replace with qualitative tier language (see §1 + v3.1-1 below). | Both AIs converged |
| **v3-4** | **Hide adjustment cap percentages from user UI**: backend logic unchanged. User-facing ledger shows directional effect ("Floor 8-12: increased value") not exact percentage. Prevents reverse-engineering and gaming. | Gemini explicit + second AI partial |
| **v3-5** | **Adversarial market simulation + ground-truth verification in 2.22.y**: sample 150+ inferred property identities, verify against title deeds / physical visits / completion certificates. Plus adversarial inputs: coordinated fake listings, synthetic pricing clusters, broker spam, distressed transaction poisoning. | Both AIs converged |
| **v3-6** | **Visual differentiation for non-Stage-5 outputs**: Stage 3 output gets calculator-style visual (not "report" visual). Signals "tool output, not formal document". Mitigates WhatsApp-screenshot weaponization risk. | My synthesis of Gemini's screenshot risk |

### v3 → v3.1 deltas (five, from round 3 convergent review)

| # | Delta | Round 3 source |
|---|---|---|
| **v3.1-1** | **Tier renaming**: "institutional-grade range" → **"signed valuation"** (Stage 5 only). Stage 4 tier renamed to **"broker-verified range"**. Stage 3 tier renamed to **"analytical range"**. Stage 1-2 tier remains **"indicative estimate"**. Removes premature institutional endorsement signaling. | Second AI explicit; Gemini implicit |
| **v3.1-2** | **Mandatory reason text on every refusal**: refusal output must state the specific trigger, not euphemism. Soft tone preserved, specificity mandated. Five enumerated reasons (see §1.6). | Both AIs converged |
| **v3.1-3** | **Property Graph Density KPIs as v3.1 deliverable** (NOT post-launch). Three baselines (tower coverage, transaction linking, condition fingerprint density) + heartbeat metric ("% valuation variance attributable to unresolved identity ambiguity"). See §1.7. | Both AIs converged |
| **v3.1-4** | **Inference gate reframed**: was "≥95% inference accuracy". Now "≥95% of verified inferences produce valuation delta <5% vs correct identity, with no individual case >15%". Measures what actually matters: valuation sensitivity to inference error. | Second AI explicit (heartbeat metric concept) |
| **v3.1-5** | **90-day post-launch monitoring matrix as ship gate** (§11 NEW). Specific thresholds for refusal trigger rate, user churn at Stage 3, inferred identity drift, broker routing skew, plus weekly human audit sampling + embarrassment dashboard + screenshot propagation monitoring. | Both AIs converged |

### Items deferred to 2.22.0.1 post-launch patch (acknowledged risks)

- **Image-embedded watermark engine** (Gemini round 3 spec). Defeats simple screenshot cropping but vulnerable to OCR/edit. ~3-4d engineering. Ship in 2.22.0.1.
- **Advanced disclosure mode** for sophisticated users (opt-in to see numeric ranges). ~2d engineering. Ship in 2.22.0.1.
- **Verification URL system** (`thammen.qa/verify/XXXX`) — each Stage 3 output has unique verification URL showing issuance timestamp, current status, upgrade tier. Partial implementation in 2.22.0a (URL generation), full UI in 2.22.0.1.

---

## §1 Five-stage architecture

Sprint 2.22.0 ships Stages 0+1+2+3 with refusal zones (§1.6) + property graph density gating (§1.7). Stages 4 and 5 documented for coherence.

### Stage 0 — Input (instant)
PIN / Zone-Street-Building / map pin coordinates. No backend.

### Stage 1 — AVM quick analysis
**Backend:** Lite-path classifier + district resolution + MoJ baseline + T2/T3 connector summary.
**Output:** building identification, market reference, per-field internal confidence indicators (3-dot ramp), **indicative estimate** (qualitative tier label — no numeric MUC in retail UI), statement "I need to confirm N details about your specific unit."

**Latency ceiling (asymmetric, per Q1 Option ii):**

| Asset type | p50 ceiling |
|---|---|
| `apartment_building`, `unknown` | ≤5s |
| `standalone_villa`, `compound_large`, `raw_land` | ≤10s |

**Critical design property (D11 ratified):** Stage 1 NEVER returns terminal `insufficient_data`. Minimum output = asset_type + confidence + (quick value OR refusal zone trigger per §1.6 OR explicit "computing more").

### Stage 2 — Interactive uncertainty-driven Q&A
**User time:** 30-60s typical.
**Backend:** Per-asset-type heuristics (D-stage2-2 revised).
**UX:** 3-5 structured questions on 1-2 screens, bounded multiple-choice, **silent recompute** (no real-time value jumps).

**Default field set (D-stage2-1):**

| # | Field | 2.22.0 disposition |
|---|---|---|
| 1 | Floor number | Always ask for apartment/tower. Skip for villa/land. |
| 2 | Interior condition | Always ask. Controlled vocabulary: `original` / `partially updated` / `fully renovated within 5 years`. |
| 3 | Recent renovations | "What year was kitchen last replaced?" (evidence-linked) |
| 4 | Primary view | Input only — no fact-check in 2.22.0. |
| 5 | Building age | Per-asset-type heuristic. |
| 6 | Exact unit area m² | Per-asset-type heuristic. |
| 7 | Occupancy status | Always ask. |

**Backend wiring rule (D-stage2-7):** Each answer maps to bounded asymmetric adjustment in Stage 3. **Caps invisible in user UI** (per v3-4) — adjustment ledger shows directional effect only.

### Stage 3 — Final valuation
**Backend:** Full evaluation with user-confirmed inputs replacing AVM guesses.
**Latency:** 10-25s acceptable.
**Output:**
- Final value per m² and total (only if not in refusal zone per §1.6 OR density-gated per §1.7)
- **Analytical range** (qualitative tier — numeric MUC internal only)
- Tier breakdown (T1/T2/T3 with weights and n)
- **Adjustment ledger** with directional effect only ("Floor 8-12: increased value", "View: premium adjustment applied" — NO exact percentages)
- **Use-case banner** per §6.7: "Suitable for: [pre-listing guidance, mortgage pre-qualification]. NOT suitable for: [mortgage origination, court/dispute, investment underwriting]. → Stage 5 required for those use cases."
- **Calculator-style visual** (per v3-6): different typography, layout, watermark from a formal-document visual. Signals "tool output, not formal report."

### Stage 4 — Broker field verification
Sprint 2.22.1. Tier label: **"broker-verified range"** (was: ±8%). Out of 2.22.0 scope.

### Stage 5 — Licensed valuer sign-off
Sprint 2.23+ OR Path A trigger. Tier label: **"signed valuation"** (was: ±5%, was: "institutional-grade range"). Out of 2.22.0 scope.

### §1.6 — Refusal zones architecture (refined)

The AVM explicitly **declines automated estimation** in certain regimes. Deliberate product property, not a bug.

**Dynamic refusal triggers** (per v3-2):

| Trigger | Condition |
|---|---|
| Comp density sparse | MoJ comp count n<5 in 24mo window AND n<10 in 36mo fallback in this size bracket + district |
| Spatial ambiguity | Multiple GIS parcels of compatible size/type for unmapped MoJ transaction, ambiguity score >0.7 |
| Regime shift | District has had infrastructure announcement / major developer launch / freehold rule change in last 90 days |
| Asset uniqueness | Estimated value >3 standard deviations from district median (3σ outlier check) |
| Asset scale extreme | Property is 5× larger than largest comparable transaction in our database |
| **Density-gated district** | See §1.7 — if density below floor for this district, refuse here too |

**Mandatory reason text (per v3.1-2):** Every refusal output specifies the trigger. No euphemism. Five reasons enumerated:

| Trigger | User-facing message template |
|---|---|
| Comp density sparse | "This district has fewer than 5 comparable transactions in the past 6 months for properties of this size and type. An automated estimate cannot reach reliable confidence. A specialized assessment is recommended." |
| Spatial ambiguity | "Your property could not be uniquely linked to a single building or parcel in our system. To produce a confident valuation, we recommend a specialized assessment with on-site verification." |
| Regime shift | "This district has experienced significant market changes in the past 90 days [optional: name the event]. Comparable transactions are in transition. A specialized assessment is recommended until the market stabilizes." |
| Asset uniqueness | "This property's profile is statistically distinctive within its district. An automated estimate cannot fully capture properties this unusual. A specialized assessment is recommended." |
| Asset scale extreme | "This property's scale exceeds any comparable transaction in our database. An automated estimate cannot extrapolate reliably. A specialized assessment is required for an asset of this magnitude." |

**Refusal output also includes:**
- Soft optional indicative range (with much wider implicit MUC) — labeled clearly as "rough orientation only, not for any transactional use"
- "Connect to a specialized valuer" CTA (per Path C/Stage 5 framework)
- Verification URL (post-2.22.0.1)

🟢 **Why refusal zones are a moat, not a weakness:** They signal competence to sophisticated users (banks, institutional valuers, lawyers), reduce tail-error exposure, and align with the §6.6 "authoritative while wrong" risk lens.

### §1.7 NEW — Property graph density gating

Per v3.1-3. The property graph moat thesis (D-strategy-2) is empirically unproven and depends on data accumulation. v3.1 makes the data-density floor measurable and operational.

**Three density baselines** (initial values; recalibrate against telemetry in first 30 days):

| KPI | Baseline | Target zones (initial scope) |
|---|---|---|
| **Tower Coverage Floor** | ≥85% of active residential towers mapped to municipal plot IDs | Pearl, Lusail (Fox Hills + Marina), West Bay |
| **Transaction Linking Floor** | ≥75% of unmapped historical MoJ transactions in target zones linked to inferred physical structure with confidence ≥90% | Same target zones |
| **Condition Fingerprint Density** | ≥5 user-verified condition updates per 1,000 m² residential space | ≥3 target districts must hit this floor |

**Heartbeat metric** (per v3.1-3, second AI insight):
- **"% valuation variance attributable to unresolved identity ambiguity"** — measures how much of the model's output uncertainty is caused by not knowing which building we're looking at.
- **Target: ≤5% of total variance.** If above this, the property graph is contributing more noise than signal in that district.

**Density-gating rule (auto-refusal):** If a district falls below ANY baseline OR the heartbeat metric exceeds 5%, that district is **density-gated** — automatic refusal zone per §1.6 until density recovers. Density is recomputed weekly.

**Ship gate (v3.1-3 + v3.1-4):** All three target zones must meet baselines AND inference gate (v3.1-4) before 2.22.0 retail launch:

- **Inference gate (revised):** ≥95% of verified inferences (from 2.22.y audit) produce valuation delta <5% vs correct identity, with no individual case producing delta >15%. Measures sensitivity-weighted accuracy, not raw accuracy.

If any target zone fails, 2.22.0 ships with that zone density-gated (auto-refusal) until density recovers in subsequent sprints.

---

## §2 Sprint scope decomposition

| Phase | Scope | Estimate | Notes |
|---|---|---|---|
| **2.22.0a** | Brief content fix + tier_breakdown UI + RICS Red Book 2024 / IVS 2024 compliance audit + A2 reclassification + use-case banner + dynamic refusal triggers + **mandatory refusal reason text** + tier renaming + **verification URL generation** (URL only, full UI in 2.22.0.1) | ~3-5d | Folds in scrapped 2.21.5 work. Prerequisite for 2.22.0b. |
| **2.22.0b** | 5-stage UX (Stages 0+1+2+3): frontend, Stage 2 backend, ReadableStream streaming, bounded adjustment caps (backend only, hidden in UI), silent recompute, calculator-style visual, property graph density gating logic | ~7-10d | Main Sprint body. |
| 2.22.0.1 | Image-embedded watermark engine + advanced disclosure mode + full verification URL UI | ~5-6d | Post-launch patch (~2 weeks after 2.22.0 ships) |
| 2.22.1 | Stage 4 (broker field verification) | TBD | After 2.22.0 stabilizes |
| 2.22.2 | Telemetry refresh + monitoring matrix dashboard (§11) | ~2-3d | After 2.22.1 |
| **2.22.x (parallel)** | PDPPL operational compliance: privacy notice, consent capture, consent versioning, RoPA, breach notification, data subject request handling | ~3-5d | Runs parallel to 2.22.0b |
| **2.22.y (parallel)** | Validation hardening: tail-error analysis, temporal backtesting, stratified validation, **sensitivity-weighted inference audit (≥95% / <5% delta / no case >15%)**, drift monitoring, adversarial market simulation (fake listings + synthetic clusters + broker spam + distressed poisoning), property graph density measurement against baselines | ~8-12d | Required before retail launch. Ship-gate per §1.7. |
| 2.23+ | Stage 5 (Path C) | Business-dev-gated | OR Path A trigger |
| 2.25+ (research) | Compound methodology research (>30K m² assets) | Research-track | Open question per v2 §6 |

**Total 2.22.0 engineering (a+b):** ~10-15 days.
**Plus 2.22.x:** ~3-5d parallel (PDPPL).
**Plus 2.22.y:** ~8-12d parallel (validation + density).
**Plus 2.22.0.1:** ~5-6d post-launch patch.

---

## §3 D-decisions — v3.1 final state

### Ratified from v1/v2 (8)
D1 (REVISED to ReadableStream), D2-D7, D11 per prior briefs.

### Stage 2 Q&A (D-stage2-1 through D-stage2-7)

| ID | Decision |
|---|---|
| D-stage2-1 | 7-field default set per §1 (controlled vocabularies) |
| D-stage2-2 | Per-asset-type heuristics, silent recompute, no real-time value jumps |
| D-stage2-3 | "I don't know" → AVM uses best guess + flags "unverified" |
| D-stage2-4 | User can skip Stage 2 entirely → indicative tier stays |
| D-stage2-5 | User lies → Stage 4 broker catches it; D-stage2-7 caps prevent damage |
| D-stage2-6 | 3-5 questions per screen, max 2 screens |
| D-stage2-7 | Bounded asymmetric adjustment caps. **Backend logic active; UI shows directional effect only, not percentages.** |

### Strategy (D-strategy-1 through D-strategy-6)

| ID | Decision |
|---|---|
| D-strategy-1 | Path C partner pool broadened: 3+ individual valuers OR 1 mid-tier RICS firm |
| D-strategy-2 | **Property graph as defensible moat**, now with measurable density baselines (§1.7) + heartbeat metric. v3.1 makes this thesis operationally testable, not aspirational. |
| D-strategy-3 | Pricing reanchored to ValuStrat residential fee benchmark |
| D-strategy-4 | CoI protocol with escalated rigor (compensation isolation, no auto-routing to own brokerage, immutable snapshots, override logging) |
| D-strategy-5 | Basel 3.1 B2B path with on-premise/private cloud container deployment |
| D-strategy-6 | PII allocation per RICS PS 1.6 |

### NEW v3.1 (D-validation-1, D-monitoring-1)

| ID | Decision |
|---|---|
| **D-validation-1** | Inference gate is sensitivity-weighted, not accuracy-alone. Audit produces: per-verification, recompute valuation as-if wrong inference had been used, measure delta. Gate = ≥95% verifications produce delta <5%, no case >15%. |
| **D-monitoring-1** | 90-day post-launch monitoring matrix (§11) is a ship-readiness gate, not optional. Dashboard exists at launch; thresholds trigger specific recalibration actions. |

---

## §4 H-hypotheses (unchanged from v2)

H1-H8 status per v2 §4.

---

## §5 Audit findings absorbed (unchanged from v2)

Per FINAL v1/v2 §5.

---

## §6 Due diligence findings

### §6.1 - §6.5 (unchanged from v2)

Memory corrections, strategic positives, risks 1-5 per v2.

### §6.6 — Existential risk: "Authoritative while wrong" (unchanged from v2)

The primary existential risk frame. All downstream choices serve this principle.

### §6.7 — Use-case segmentation (unchanged from v2, refined tier naming)

| Use case | Required stage |
|---|---|
| Curiosity / market discovery | Stage 1 (indicative estimate) |
| Pre-listing pricing guidance | Stage 1+2 (refined indicative) |
| Buyer offer reference | Stage 1+2 |
| Mortgage pre-qualification | Stage 1+2+3 (analytical range) with bank-aware disclaimer |
| **Mortgage origination collateral** | **Stage 5 required (signed valuation)** |
| **Court / divorce / inheritance / dispute** | **Stage 5 required (signed valuation)** |
| Investment underwriting | Stage 3 sufficient with caveats |
| Portfolio revaluation (B2B Basel 3.1) | D-strategy-5 dedicated track |

### §6.8 — PDPPL correction (unchanged from v2)

Article 15 (general permission) + Article 16 (sensitive data pre-approval). Heroku US compliant with operational measures in 2.22.x.

### §6.9 NEW — Visual + verification authenticity layer

Per v3-6 + v3.1 deferred items + round 3 convergent finding.

**Three-tier authenticity layering for Stage 3 outputs:**

1. **In 2.22.0a:** Calculator-style visual (typography, layout, no formal-report aesthetic) + verification URL generated per output (URL only; full UI deferred).
2. **In 2.22.0.1 patch (~2 weeks post-launch):** Image-embedded disclaimer watermark (diagonal text overlay across rendered numbers, structurally embedded; cropping defeats only with OCR/edit, not casual screenshot) + full verification URL UI showing issuance timestamp, current tier status, expiration if any.
3. **Future (2.22.1+):** Stage 4 / Stage 5 outputs get visually distinct presentation (formal-document aesthetic) — clearly differentiated from Stage 3.

🟡 **Honest caveat:** None of these defeats a determined user who screenshots, OCRs, and edits. They are **friction layers**, not security. The verification URL is the most durable defense — a counterparty receiving a screenshot can verify whether the output is current and what tier it actually is, defeating stale or out-of-context circulation.

### §6.10 NEW — Sensitivity-weighted inference metric

Per v3.1-4 + round 3 second AI insight.

The shift from "inference accuracy" to "valuation sensitivity to inference error" is a fundamental measurement reframe:

- **Old framing**: did we map the MoJ transaction to the right tower? (binary; accuracy %)
- **New framing**: when we mapped wrong, how badly did the valuation suffer? (continuous; sensitivity-weighted)

The new metric catches the catastrophic failure mode round 3 surfaced: **internally coherent but externally wrong** — the system reasons sophisticatedly about the wrong building, producing outputs that look deeply reasoned but are anchored incorrectly.

If wrong-tower inference moves the final valuation by 2%, the error is recoverable and within MUC. If it moves the valuation by 18%, the error is catastrophic-and-coherent — much more dangerous than random noise because the user has no way to detect it.

**Operational gate** (per D-validation-1):
- Audit produces sensitivity distribution across 150+ verified inferences
- 95%-ile of |delta| < 5%
- 100%-ile of |delta| < 15%
- Districts that fail this gate are density-gated per §1.7 until fixed

### §6.11 NEW — "Soft authority drift" risk

Per round 3 second AI insight + Gemini's "vague front / precise back" framing (same concern, two framings).

**The risk:** v3 deliberately softened public-facing precision (qualitative tiers instead of "±12%") to address v2's "authoritative while wrong" risk. But softening creates a new failure mode: **the same output gets interpreted differently by different audiences.**

- Retail seller sees "analytical range" → "rough estimate"
- Broker sees the same → "strong pricing anchor"
- Bank officer sees informally → "credible enough"
- Developer sees → "market benchmark"
- Lawyer sees → "not formal"

Same artifact. Polymorphic social authority. **More flexible interpretation = more potential misuse.**

**v3.1 mitigations** (partial — this risk is not fully solvable, only managed):
1. Use-case banner makes interpretation explicit per use case (per v2 §6.7)
2. Verification URL grounds any screenshot to a specific tier identity (per §6.9)
3. Watermark disclaimer embedded in output image (post-2.22.0.1) reduces context loss in informal sharing
4. **Acknowledge openly** in T&Cs that Stage 3 output is not equivalent to Stage 4/5 in any use case — institutional partners audit T&Cs

**Residual risk:** Even with all mitigations, this is the most likely v3.1 failure mode in the first 18 months. Monitor via screenshot propagation tracking (§11).

---

## §7 Stage 5 strategic paths (unchanged from v2)

Path A (Anas-as-Valuer), Path B (Hybrid), Path C (Partnership, current default). Per v2 §7.

---

## §8 Carry-overs (unchanged from v2)

H10 visual closure, E21 formalization, Rule #54.

---

## §9 Action items outside Sprint engineering

Per v2 + new v3.1 items:

| # | Item | Owner | Trigger |
|---|---|---|---|
| 1-9 | Per v2 (Path A DD, pricing validation, partner pool, CoI lawyer, Basel 3.1 scoping, PII quote, marketing claim audit, PDPPL compliance) | Anas + engineering | Per v2 |
| 10 | Confidence calibration + tail-error + temporal backtest | 2.22.y engineering | Parallel |
| 11 | Compound methodology research (>30K m²) | Claude.ai methodology research | Sprint 2.25+ |
| 12 | Use-case segmentation legal review | Qatar real estate lawyer (#5 bundle) | Before Stage 5 launch |
| 13 | Property graph data architecture spec | Claude.ai + Claude Code | Sprint 2.23+ |
| **14 NEW v3.1** | **Property graph density measurement against baselines** (§1.7) — ship-gate validation | 2.22.y engineering | Before retail launch |
| **15 NEW v3.1** | **Sensitivity-weighted inference audit** — 150+ identity verifications, recompute as-if-wrong, measure delta distribution | 2.22.y engineering | Before retail launch |
| **16 NEW v3.1** | **90-day monitoring matrix dashboard built and live at launch** (§11) | 2.22.0b → 2.22.2 engineering | Day 1 of launch |

---

## §10 Phase 3 (Claude Code) implementation entry conditions

1. ✅ Anas signs this BRIEF FINAL v3.1
2. ✅ Commit `a903350` (Phase 1 audit) pushed to Heroku
3. ✅ 2.22.0a scope confirmed: brief content + tier_breakdown + Red Book audit + A2 fix + use-case banner + dynamic refusal triggers + mandatory reason text + tier renaming + verification URL generation
4. ✅ 2.22.0b scope confirmed: Stages 0+1+2+3 + ReadableStream + bounded caps (hidden in UI) + silent recompute + calculator-style visual + density gating logic
5. ✅ 2.22.x parallel scope confirmed: PDPPL operational compliance
6. ✅ 2.22.y parallel scope confirmed: validation hardening + sensitivity-weighted inference audit + property graph density measurement + adversarial market simulation
7. ✅ Phase 3 worklog initialized at `2p22p0_pre/PHASE3_LOG.md`
8. ✅ Density baselines confirmed achievable in target zones (Pearl, Lusail Fox Hills + Marina, West Bay) OR density-gating accepted as launch posture for failing zones

---

## §11 NEW — 90-day post-launch monitoring matrix

Per v3.1-5 + round 3 convergent finding. **Ship-readiness gate, not optional.** Dashboard exists at launch; specific thresholds trigger specific recalibration actions.

| Metric class | Trigger threshold | Mandatory action |
|---|---|---|
| **Refusal zone trigger rate** | >35% of total user queries in a single week | Adjust dynamic sigma limits (§1.6); audit refusal distribution by segment — if clustering in high-value segments, recalibrate thresholds |
| **User input churn rate at Stage 3** | >50% drop-off at upload requirements | Simplify Q&A layout OR relax photo/document upload demands OR re-evaluate D-stage2-7 receipt gate strictness |
| **Inferred identity drift** | Any new MoJ transaction mapping at <90% confidence in target zones | Roll back target zone's model to district averages until cleaner data available; investigate inference engine for that district |
| **Broker lead routing skew** | >40% of Stage 4 field checks routing to a single agency | Audit routing scripts for systemic allocation bias; pause auto-routing until protocol verified neutral |
| **Heartbeat metric drift** | "% valuation variance attributable to unresolved identity ambiguity" exceeds 5% in any district | Density-gate that district (auto-refusal) until property graph density recovers |
| **Screenshot propagation patterns** | Any externally-circulating screenshot detected via brand monitoring | Investigate context of circulation; if pattern is misuse (informal financing without Stage 5), strengthen use-case banner copy or visual differentiation |
| **5-10% weekly human audit** | Random sample of Stage 3 outputs reviewed by Anas + 1 valuer | Track patterns: which towers are unstable, which districts produce escalating overrides — feeds into "embarrassment dashboard" |
| **Embarrassment dashboard** | Largest valuation misses, user disputes, repeated correction patterns | Reviewed weekly by Anas; informs sprint priorities for 2.22.1+ |

**First-30-day intensified monitoring:** All thresholds halved during first 30 days (e.g., refusal trigger rate >17.5% triggers recalibration, not >35%). Acknowledges that initial thresholds are estimates; live telemetry will refine them.

---

## §12 Sign-off

```
Anas: ______________________  Date: __________
Claude.ai: BRIEF_2p22p0_FINAL_v3.1.md authored 2026-05-26 PM (third iteration)
Claude Code: Phase 1 audit complete (a903350); Phase 3 ready on sign
```

---

## Appendix A — Document map

```
2p22p0_pre/
├── CHANGELOG_pre_2p22p0_v2.md         (SUPERSEDED — May 25 v2 draft)
├── BRIEF_2p22p0_FINAL.md              (SUPERSEDED — May 26 v1 of FINAL)
├── BRIEF_2p22p0_FINAL_v2.md           (SUPERSEDED — May 26 v2 of FINAL)
├── AUDIT_FINDINGS_2p22p0.md           (Phase 1 deliverable, authoritative)
├── field_confidence_map_2p22p0.md     (Phase 1 supporting)
├── latency_profile_2p22p0_v2.json     (Phase 1 supporting)
├── audit_pre_2p22p0_v2.py             (Phase 1 reproducible script)
├── audit_pre_2p22p0_v2.log            (Phase 1 execution log)
└── BRIEF_2p22p0_FINAL_v3.1.md         (THIS FILE — Phase 2 sign-off doc)
```

## Appendix B — Why v3.1 supersedes v2 and v3 (one-paragraph summary for future Anas)

v2 absorbed Phase 1 audit findings and integrated round 1 adversarial review (Gemini + second AI). v2 was engineering-ready but exposed v2 to round 2 adversarial review, which surfaced convergent concerns: refusal zones too rigid linguistically, public precision claims pseudo-precise, adjustment caps gameable, property graph thesis empirically unproven, screenshot weaponization risk. v3 (described in chat to AIs but never written as a standalone brief) made six refinements: softened refusal language, dynamic refusal thresholds, qualitative tier UI, hidden cap percentages, adversarial validation, calculator-style visual. Round 3 adversarial review confirmed v3 shippable but converged on five further patches: "institutional-grade" wording premature, refusal language needed specific reasons not euphemism, property graph density needed measurable KPIs before launch (not post), inference accuracy alone insufficient (needed sensitivity-weighted), 90-day monitoring matrix mandatory not optional. v3.1 absorbs all five patches as Option B (the convergent must-haves). Items deferred to 2.22.0.1 (image-embedded watermark engine, advanced disclosure mode, full verification URL UI) are documented but non-blocking. v3.1 is ship-ready. After three rounds of adversarial AI review across two independent models, both reached "ship" verdict with monitoring matrix in place. No fourth round warranted; diminishing returns confirmed.

## Appendix C — One-line summary of each round's primary contribution

- **Round 0 (BRIEF v1):** Phase 1 audit findings absorbed; Stage 5 three-path framework; due diligence corrections.
- **Round 1 (BRIEF v2):** "Authoritative while wrong" reframe; refusal zones architecture; use-case segmentation; property graph moat thesis; bounded adjustment caps; silent recompute.
- **Round 2 (v3 changes):** Softened refusal language; dynamic refusal thresholds; qualitative tier UI; hidden cap percentages; adversarial validation; calculator-style visual.
- **Round 3 (v3.1 patches):** Tier renaming; mandatory refusal reason text; property graph density KPIs; sensitivity-weighted inference metric; 90-day monitoring matrix.

Three rounds, eleven total changes on top of v1. Engineering scope: ~10-15d core + ~3-5d PDPPL + ~8-12d validation. Ship-ready.
