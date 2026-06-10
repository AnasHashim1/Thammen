# THAMMEN — RISK REGISTER (سجلّ المخاطر — النسخة الموسَّعة)

> **⚠️ STATUS: point-in-time SNAPSHOT (2026-06-09, post-errata) — reference & audit depth, NOT line-maintained.** The living layer = `RISK_SUMMARY.md` (sprint-close cadence) + the canonical `RISK_REGISTER.md` ledger. Re-issued at stage gates only (beta / monetization / apartments / scale).
> **Project:** thammen.qa — Qatar residential real-estate Automated Valuation Model (AVM)
> **Document type:** Enterprise Risk Register (current + forward/emerging). **This is a risk register, not an issues log** — every entry is scored (likelihood × impact), carries explicit controls, a residual rating, an owner, early-warning indicators, and a response/contingency plan. The companion `ISSUES_LOG.md` catalogues *defects/work-items*; this register catalogues *uncertainties that could affect objectives*.
> **Methodology frame:** RICS Red Book Global Standards (effective 31 January 2025) — VPGA 10 (matters that can give rise to material valuation uncertainty) + VPS 6 + IVS 106 · IVS 2025.
> **Product Owner / sole gate & risk authority:** Anas.
> **Review cadence:** each sprint close-out + at every stage-gate (beta launch, monetization, apartment expansion, scale).
> **Provenance:** grounded in a live `GET /api/health` probe (2026-06-09 16:17 UTC) and a read of the governance corpus mirror at `/mnt/project/`. Facts are tagged **measured✓** or **assumed~**.
> **Relationship to the canonical register:** this **extends** `RISK_REGISTER.md` (R1–R15) — those IDs and their wording are **preserved**; new operational risks are appended as **R16–R22**; forward/horizon risks use the **RF-** prefix so they never collide with the canonical numbering.

---

## CONTENTS

- **PART 0 — Front matter, taxonomy & scoring methodology**
  - 0.1 Purpose & scope · 0.2 Provenance · 0.3 Risk taxonomy · 0.4 Scoring (L×I) · 0.5 Risk appetite · 0.6 Controls taxonomy & residual risk · 0.7 Ownership & cadence · 0.8 Legend
- **PART 1 — Executive risk summary**
  - 1.1 Live snapshot · 1.2 Risk heatmap · 1.3 Top risks ranked · 1.4 Direction of travel · 1.5 Concentration analysis · 1.6 The one risk + the one decision
- **PART 2 — Risk-management methodology (the discipline)**
- **PART 3 — THE REGISTER (current/active risks), by category**
  - 3.A Methodology & valuation-accuracy · 3.B Data & dependency · 3.C Technical & infrastructure · 3.D Regulatory & compliance · 3.E Security & privacy · 3.F Product, UX & reputational · 3.G Strategic, commercial & organizational · 3.H Governance & process
- **PART 4 — Emerging & future risks (RF-), horizon-scanned**
  - 4.1 Beta launch · 4.2 Monetization · 4.3 Apartment expansion · 4.4 Scale · 4.5 Regulatory evolution · 4.6 Market & macro · 4.7 Competitive & strategic · 4.8 AI/model-specific · 4.9 Tail / black-swan
- **PART 5 — Risk treatment & action plan**
  - 5.1 Treatment per top risk · 5.2 PO-decision register · 5.3 Control roadmap · 5.4 KRIs (Key Risk Indicators) · 5.5 Escalation & review
- **PART 6 — Closed / retired / accepted risks**
- **PART 7 — Appendices A–J**

---

# PART 0 — FRONT MATTER, TAXONOMY & SCORING METHODOLOGY

## 0.1 Purpose & scope

This register exists to make Thammen's uncertainties **explicit, scored, owned, and monitored** before they become incidents. A small single-founder product carrying a *named regulated activity* (التقييم العقاري), a known bidirectional accuracy defect (R7), and a single external data dependency (MoJ) cannot rely on memory to track its exposure. The register's job is to answer four questions for every risk:

1. **How bad, how likely?** — a defensible inherent score (likelihood × impact).
2. **What are we already doing?** — the controls in place (preventive / detective / corrective).
3. **What's left after those controls?** — the residual score, and whether it is within appetite.
4. **What's the trigger and the plan?** — the early-warning indicator and the response if the risk crystallises.

**In scope:** methodology/accuracy, data & dependencies, technical/infrastructure, regulatory/compliance, security/privacy, product/UX/reputational, strategic/commercial/organizational, governance/process — across the **current** state and the **forward** horizons (beta → monetization → apartments → scale).

**Out of scope (v1 product):** apartment-specific valuation risk is treated as *forward* (RF-10..RF-12) because apartments are out of the v1 scope (blocked on MME authentication); the register flags the risks that *become* live at that expansion rather than treating them as current.

**What this register is NOT:** it is not a brief, it does not authorise any build, and it does not replace any signed brief or any Gate-2 signature. Where a risk's treatment needs a Product-Owner decision, it is marked **«القرار المطلوب»** and routed to Anas (Part 5.2 consolidates these).

## 0.2 Provenance & evidence discipline

Per Rule **#58** (assumed-vs-actual gap) and Rule **#65a** (read live state first at the #57 handshake), the "current state" inputs were **measured**, not recalled:

- **Live probe `GET https://thammen.qa/api/health` (2026-06-09 16:17 UTC):**
  - `version` **3.1.0-sprint2.22.0b.11** · `engine_version` **thammen-sprint2p22p0b11-cost-drc-reanchor**
  - `moj_freshness`: latest_record **2025-12-31**, **days_old 160**, tier **stale**, record_count **25,673**
  - `calibration_freshness`: total_cells **200** (reliable **6** / indicative **10** / fallback **184**), last_updated 2026-06-07, days_old 1, outliers_rejected 27, calibratable_listings_seen 3,458, outlier_rate 0.78%
  - `qars_endpoint`: **healthy** (primary 162,496 / legacy 162,497)
  - `security`: CORS locked, rate-limits **5/s · 30/min · 200/h** keyed on `cf-connecting-ip`, docs locked
  - `moj_db`: available, 8.2 MB
- **Heroku release:** **v180** (per CLAUDE.md #65a; not surfaced on `/api/health`, but the engine tag `…b11-cost-drc-reanchor` confirms the same ship).
- **Corpus** read on disk at `/mnt/project/` (read-only mirror of `C:\Thammen\deploy v2\docs\`): `RISK_REGISTER.md` (R1–R15), `CLAUDE.md` (#65a), `Empirical_Findings.md` (E1–E23), `Operational_Rules.md` (#1–#65), `Session_Log.md`, plus PHASE0 recons, BRIEF_* files and CHANGELOG_v64–v94.

Every fact below is tagged **measured✓** (observed this session) or **assumed~** (reasoned, not measured — the default for forward risks, which are inherently probabilistic).

> **Errata pass (2026-06-09, same day, after a full `Session_Log.md` read).** Two inherited errors were corrected throughout, marked "(errata)": **(1) R9/A16** — the legacy register's OPEN entry was stale; §20.18 (a18, v157, 2026-06-03) had already resolved it as a pool-fix (`area_match_key` wired into `build_reference`; امريخ الجنوبي→مريخ; live Marikh = 5.4M comparison_thin n=15 same-district) — every "A16/R9 root fix / live-trace prerequisite" item is corrected accordingly. **(2) gate #6** — the 2026-06-09 cleanup (ISS-G03) deleted the cohort gate (beta = parallel non-blocking track) while CLAUDE.md #65a still names it; this register now follows ISS-G03 and flags the #65a reconciliation (R-H). Also added: the §20.45 Heroku-auth deploy lesson (R-C bullet).

## 0.3 Risk taxonomy (categories)

Eight categories for the current register, plus a ninth bucket for forward/emerging risks:

| Code | Category | What it covers |
|---|---|---|
| **A** | Methodology & valuation-accuracy | Whether the number is *right* — model bias, pool selection, decomposition, calibration |
| **B** | Data & dependency | The inputs — MoJ, GIS, listings, ground-truth corpus, data hygiene |
| **C** | Technical & infrastructure | The platform — dynos, timeouts, endpoints, state, version integrity |
| **D** | Regulatory & compliance | The licence to operate — Aqarat/Amiri-Decision-28, PDPPL, RICS-claim scope |
| **E** | Security & privacy | Protecting data & the surface — capture, PII, secrets, abuse |
| **F** | Product, UX & reputational | How the number is *received* — authority, anchoring, public perception |
| **G** | Strategic, commercial & organizational | The business — monetization, key-person, competition, runway |
| **H** | Governance & process | How the work is *run* — two-lane discipline, memory, brief integrity |
| **RF** | Forward / emerging | Risks that are not live yet but become material at a named horizon |

## 0.4 Scoring methodology — Likelihood × Impact

Every risk is scored on two 1–5 axes; the **risk score = L × I** (range 1–25). Scoring is over a **rolling 12-month horizon** unless a risk's entry names a different horizon (forward risks are scored over the horizon at which they become live).

### Likelihood (L)

| L | Label | Meaning (over the horizon) |
|---|---|---|
| 1 | Rare | < 10% — would be surprising |
| 2 | Unlikely | 10–30% |
| 3 | Possible | 30–55% — could easily go either way |
| 4 | Likely | 55–80% — expect it more often than not |
| 5 | Almost certain | > 80% — plan as if it will happen |

### Impact (I) — scored as the **maximum across dimensions**

A risk's impact is the **highest** score it reaches on any one dimension (a regulatory shutdown is severe even if its financial line-item is small).

| I | Label | Accuracy / credibility | Regulatory / legal | Financial / commercial | Reputational | Operational |
|---|---|---|---|---|---|---|
| 1 | Negligible | Within MUC band | None | < trivial | None | Self-heals |
| 2 | Minor | One surface mildly off | Informal query | Minor cost | A few users notice | Hours to fix |
| 3 | Moderate | A cohort systematically off | Compliance gap to close | Material cost / delay | Visible to the cohort | Days; manual workaround |
| 4 | Major | Headline materially wrong for a large share | Unlicensed-activity exposure | Blocks monetization / large cost | Public embarrassment | Outage / re-work |
| 5 | Severe | Engine systematically untrustworthy | Cease-and-desist / enforcement | Existential to the model | Lasting brand damage | Data loss / project halt |

### Severity bands (the colour)

| Score (L×I) | Band | Colour | Posture |
|---|---|---|---|
| 1–4 | Low | 🟢 | Accept & monitor |
| 5–9 | Moderate | 🟡 | Manage; control where cheap |
| 10–14 | High | 🟠 | Active treatment; named owner + plan |
| 15–25 | Critical | 🔴 | Treat now or consciously accept at PO level |

**Inherent vs residual.** Each entry shows the **inherent** score (before the controls listed) and the **residual** score (after them). The delta is the *value of the controls*; a high residual means the controls are insufficient and treatment is owed.

> **Note on the legacy register's severities.** `RISK_REGISTER.md` used a single 🔴/🟠/🟡 severity (impact-flavoured, no explicit likelihood). This register **preserves** that flag as the legacy reference and **adds** the L×I decomposition. Where they appear to disagree (e.g. a legacy 🟡 with a high impact but low likelihood), the L×I view is the reconciliation, not a contradiction.

## 0.5 Risk appetite & tolerance (per category)

The PO's stated/implied appetite, used to judge whether a residual score is acceptable:

| Category | Appetite | Rationale |
|---|---|---|
| **A** Accuracy | **Moderate, *disclosed*** | A known defect is tolerable **if** it ships disclosed-as-indicative (§0 standing principle) with wide MUC; an *undisclosed* systematic error is **not** tolerable. |
| **B** Data | **Low for integrity, Moderate for freshness** | A silent data-hygiene corruption (NBSP, article-drop) is intolerable; a *transparent* staleness banner is acceptable. |
| **C** Infrastructure | **Moderate** | Beta-grade availability is acceptable pre-monetization; SPOF must be retired before paid/scale. |
| **D** Regulatory | **Low** | The named-regulated-activity exposure is managed by conservatism (free, invite-only, disclaimed) and a held enquiry; **zero** appetite for operating a *paid* service pre-licence. |
| **E** Security/privacy | **Very low** | Capture stays dormant until the §8.1/§8.2 + security gate clears; PDPPL exposure is not accepted. |
| **F** Reputational | **Low-moderate** | A disclaimed beta absorbs some mis-valuation risk; a public, viral mis-valuation is to be actively avoided. |
| **G** Strategic | **Moderate** | A single-founder build accepts key-person and competitive risk as the cost of the stage; monetization risk is gated. |
| **H** Governance | **Low** | The two-lane model's whole point is to keep drift low; the #57/#58 handshakes are non-negotiable controls. |

## 0.6 Controls taxonomy & residual risk

Controls are classified by *when* they act:

- **Preventive** — stop the risk occurring (e.g. the `if land_value > valuation_amount: return None` guard; the consent gate; the dispersion gate).
- **Detective** — surface it early (e.g. `/api/health` freshness tiers; the `#57` handshake; the broad regression suite; KRIs).
- **Corrective** — limit damage once it occurs (e.g. the primary→legacy QARS fallback; the staleness banner + MUC; the backup-erasure runbook).

**Residual risk** = the exposure that remains *after* the listed controls operate as designed. A control that is *designed but not yet executed* (e.g. a dormant runbook, an un-run KRI) does **not** reduce residual risk until it is live — this register does not credit paper controls (a direct application of Rule #14: "verified" = executed, not reasoned).

## 0.7 Ownership & review cadence

- **Owners:** `PO` (Anas — accountable, holds the gates) · `Claude.ai` (analyst — identifies/scores/formulates) · `CC` (developer — implements controls) · `EXT` (external; we can only monitor + plan around).
- **The two-lane model is itself a control** (separation of "decide/verify" from "implement") *and* a risk (coordination drift — R-H family).
- **Cadence:** every sprint close-out (re-score touched risks; close with date+evidence; never delete — Rule of the legacy register) **+** a full re-score at each stage-gate. KRIs (Part 5.4) are checked at every `#57` handshake.

## 0.8 Legend

**Status:** `OPEN` · `MITIGATED` (reduced, not eliminated) · `PARKED` (blocked on a named trigger) · `ACCEPTED` (consciously held at PO level) · `CLOSED` (resolved, date + evidence) · `MONITOR` (low residual, watch the KRI).
**Severity bands:** 🔴 Critical (15–25) · 🟠 High (10–14) · 🟡 Moderate (5–9) · 🟢 Low (1–4).
**Response strategy (ISO-31000 / COSO vocabulary):** **Avoid** (don't do the thing) · **Reduce/Mitigate** (controls) · **Transfer** (insurance/contract/counsel) · **Accept** (hold, with rationale).
**Direction of travel:** ↑ increasing · → stable · ↓ decreasing.

---

# PART 1 — EXECUTIVE RISK SUMMARY

## 1.1 Live-state snapshot (measured✓ 2026-06-09)

| Dimension | Value | Risk-relevant note |
|---|---|---|
| Engine | `3.1.0-sprint2.22.0b.11` · Heroku v180 | b11 shipped the §20.9 cost-reanchor **down-half** (partial R7 treatment) |
| MoJ data | 2025-12-31 · **160 days stale** · 25,673 records | R4 (staleness) + R21 (single-source) live; MUC clause active |
| Calibration | 200 cells (6 reliable / 10 indicative / **184 fallback**) | 92% of cells are fallback → R19 (GT scarcity) + thin-cell reliance |
| QARS | healthy (162,496 / 162,497) | R5 residual-low *today*; EXT dependency (RF-15) |
| Capture | **DORMANT** (no `DATABASE_URL`, flag off) | R11 residual-low while inert; R20 (no live accuracy gauge) live |
| Security | CORS locked · 5/s·30/min·200/h on cf-connecting-ip · docs locked | R12 mitigated; RF-02 (abuse) + RF-31 (breach) are forward |
| Bugs (live) | Critical **0** · High **0** · Medium **2** (A5, A15) | A16/R9 → **resolved-as-pool-fix at a18** (§20.18, v157); residual = unreachable-name coverage ~0.25% (فريج العسيري) |

## 1.2 Risk heatmap — current risks at **residual** score

Rows = Likelihood (5 top → 1 bottom). Columns = Impact (1 → 5). Cell colour = severity band. IDs are placed at their **residual** (post-control) L×I.

| L ↓ \ I → | **1 Negligible** | **2 Minor** | **3 Moderate** | **4 Major** | **5 Severe** |
|---|---|---|---|---|---|
| **5 Almost certain** | 🟢 | 🟡 | 🟡 — | 🟠 — | 🔴 — |
| **4 Likely** | 🟢 | 🟡 | 🟠 **R7, R19, R20** | 🔴 — | 🔴 — |
| **3 Possible** | 🟢 | 🟡 **R4** | 🟡 **R8, R16** | 🟠 **R17, R21** | 🔴 — |
| **2 Unlikely** | 🟢 | 🟢 **R12** | 🟡 **R1, R3, R5, R14, R18, R22** | 🟡 **R13** | 🟠 — |
| **1 Rare** | 🟢 | 🟢 | 🟢 | 🟢 **R11** | 🟡 — |

**Reading the map.** No current risk sits in the 🔴 *critical* residual cells — that is the *value of the controls already shipped*. The cluster that matters is the **🟠 High band at residual: R7, R19, R20, R17, R21** — five risks the existing controls reduce but do **not** close. Four of those five are *the same underlying story told from different angles*: the engine is **systematically off for the tails of the market (R7)**, we **cannot yet measure how off (R20)**, we **lack the ground-truth to calibrate the fix (R19)**, and our **only truth source is a single frozen feed (R21)**. The fifth, **R17 (key-person)**, is structural to the stage.

> Inherent (pre-control) scores tell a starker story: **R7 = 20🔴**, **R13/R17/R19/R20 = 15🔴**. The controls have pulled all of these out of the critical band — *except* where the control is "ship disclosed, tighten later" (R19/R20), which manages **disclosure** risk but not **measurement** risk.

## 1.3 Top current risks — ranked by residual score

| Rank | ID | Risk (one line) | Inherent | Residual | Owner | Trend |
|---|---|---|---|---|---|---|
| 1 | **R7** | Built-type + condition blindness → bidirectional ±37–40% mis-anchoring | 20🔴 | **12🟠** | PO→CC | → |
| 2 | **R17** | Key-person / bus-factor — single PO, sole router, no succession | 15🔴 | **12🟠** | PO | → |
| 3 | **R19** | Ground-truth corpus scarcity (n<20) gates precision + any accuracy claim | 15🔴 | **12🟠** | PO/EXT | ↓ |
| 4 | **R20** | No live accuracy-measurement instrument (capture dormant) | 15🔴 | **12🟠** | PO→CC | ↓ |
| 5 | **R21** | MoJ single-source systemic dependency & discontinuation | 12🟠 | **12🟠** | EXT | → |
| 6 | **R13** | Regulated-activity self-clearance without counsel (beta) | 15🔴 | **8🟡** | PO | → (↑ at $) |
| 7 | **R8** | Comparable-pool purity + thin-window volatility | 12🟠 | **9🟡** | CC | → |
| 8 | **R16** | Infrastructure SPOF (single Eco dyno / region / ephemeral FS) | 9🟡 | **9🟡** | CC | → (↑ at scale) |
| 9 | **R18** | AI-lane dependency & governance drift | 12🟠 | **6🟡** | PO/Claude.ai | → |
| — | R1, R3, R5, R14, R22 | (state-drift, infra fragility, gate-integrity, DRC-bias) | various | 6🟡 | mixed | → |
| — | R11, R12 | (capture dormant, CC-smoke block) | various | 4🟢 | CC | → |

## 1.4 Forward risks — the ones that bite at the next gates (scored at-horizon)

| ID | Forward risk | Horizon | At-horizon score | Note |
|---|---|---|---|---|
| **RF-09** | Regulated-activity reclassification under a *paid* model | Monetization | **16🔴** | The free-beta self-clearance (R13) does **not** extend to paid |
| **RF-06** | Aqarat licence is a hard gate before any paid access | Monetization | **15🔴** | Denial/delay blocks the business model entirely |
| **RF-07** | Professional liability / indemnity for a relied-upon wrong number | Monetization | **15🔴** | No PI cover noted; reliance ≠ disclaimed-beta |
| **RF-25** | Data-source commoditization — no data moat (MoJ is open to all) | Now→scale | **12🟠** | The moat must be methodology + UX + trust, not data |
| **RF-14** | Model-drift / recalibration debt (no automated recalibration pipeline) | Scale | **12🟠** | Calibration ages as market moves + corpus grows |
| **RF-01** | First public mis-valuation screenshot (R7 made visible) | Beta | **12🟠** | A disclaimed beta absorbs *some* of this, not all |
| **RF-16** | MoJ refresh-resumption shock (a big/biased drop hits the gate) | MoJ resumes | **12🟠** | The multi-factor gate is the control; an undetected bias is the risk |
| **RF-04** | PDPPL operational failure at first real captured data | Beta/capture | **10🟠** | Residency (§8.2) + free-text (§8.1) unresolved |
| **RF-29/30/31** | MoJ permanently dark · cease-and-desist · capture breach | Tail | **10🟠 ea.** | Low likelihood, severe impact — contingency, not prevention |

## 1.5 Risk-concentration analysis

Where the exposure clusters (counting residual 🟠/🔴 + notable 🟡):

- **Category A (accuracy)** carries the densest *current* exposure — R7, R8, R22 — tracing to one surviving root mechanism: **no built-type/condition input** (the second historical root, bracket-path pool starvation, was **closed by a18** — R9 resolved-as-pool-fix, §20.18). This is the product's central technical risk.
- **Category B (data)** is the *foundation* risk — R4, R19, R21 — a single frozen open-data feed with no alternative and an immature ground-truth corpus. Most of Category A's *fix* is gated on Category B's *supply*.
- **Category G (strategic)** carries the heaviest *forward* exposure — RF-06/07/09 (monetization) are all 🔴-at-horizon, plus R17 (key-person) live. The business-model risk is larger than the technical risk *once money is involved*.
- **Category D (regulatory)** is well-controlled *for the beta* (R13 residual 🟡) but is the **trip-wire for the whole forward plan** — it escalates to 🔴 the moment the product is paid (RF-06/09).

**The structural insight:** the current risks are mostly *managed-with-disclosure*; the **un-managed** exposure lives at the **monetization gate**, where the disclaimer stops working and the licence becomes load-bearing. The register's most important forward job is to keep that gate from being crossed accidentally.

## 1.6 The single most important risk — and the single most important decision

- **The risk:** **R7** (residual 12🟠, inherent 20🔴) — the engine is systematically wrong at both tails of the market, and **R20** means we cannot yet *measure* by how much in production. Everything downstream (the polished result, the report, the range-as-lead headline, monetization) renders a number that is still materially off for a large share of real stock. Polishing the presentation of that number does not reduce this risk.
- **The decision:** the highest-leverage lever the PO *personally* holds is the **~0.31 dilapidated-luxury floor coefficient** (reserved to Anas), because it unblocks the **§20.9 convergence + UP-lift** — the only treatment for the *under-anchoring* half of R7 (the −37/−40% on new/premium villas, the more financially dangerous direction, with **zero** current mitigation). *(Correction, post-Session_Log audit: the historical over-anchor source — the A16/R9 pool starve — was already fixed at a18/v157; the surviving over-anchor is pure R7 condition, treated by the §20.9 path and B-2.)* See Part 5.2.

> **Honest framing for the PO.** The forward sequence in `ISSUES_LOG.md` puts *decomposition-coherence* first because it was *ready to sign*, not because it is the *biggest risk*. From a pure risk-reduction standpoint, **R7's under-anchor half (gated on your ~0.31 decision) and R20 (activate a measurement instrument) are the two moves that actually lower the top of this register.**

---

# PART 2 — RISK-MANAGEMENT METHODOLOGY (THE DISCIPLINE)

This register is not a one-time document; it is the output of a standing process. The process is deliberately lightweight because the team is one founder plus two AI lanes — heavyweight risk ceremony would not survive contact with the cadence.

## 2.1 How risks are identified

Four feeds, all already part of the operating model:

1. **Each sprint's recon (`PHASE0_*`)** — the §5 UI-First audit and the recon docs surface risks before code is written (e.g. R8 was *pinned* by Phase-1b measurement; R15 by the Sprint-B recon).
2. **The `#57`/`#58` handshake** — every session start measures live state vs memory; a divergence is logged as a risk-event (R1/R3 were *born* from this).
3. **Validation against ground truth (`VALIDATION_LOG.md`)** — confirmed sales (V001/V002/V003) measure the engine's error and *confirm or refute* a risk's framing (V002/V003 *confirmed* R7's bidirectional bias and *quantified* the under-anchor at −37/−40%).
4. **Horizon scanning** — the forward risks (RF-) are identified by walking the roadmap's *next gates* (beta → monetization → apartments → scale) and asking "what becomes load-bearing here that is slack today?"

## 2.2 How risks are scored & re-scored

- Inherent score is set first (pre-control), then the controls are inventoried, then the residual is set. This ordering prevents the common failure of scoring the residual and back-filling controls to justify it.
- Scores are **defensible, not precise** — the L×I bands are coarse on purpose. The job is to get a risk into the right *band* and the right *rank relative to its peers*, not to argue 11 vs 12.
- A risk is **re-scored** when: (a) a control ships (residual drops — e.g. b11 dropped R7's residual), (b) evidence changes the likelihood/impact (V002/V003 raised R7's inherent), or (c) a horizon is crossed (a forward RF- becomes a current R-).

## 2.3 Escalation & the gate model as a control

The Hard Gates are the register's primary *preventive* control surface:

- **Gate-1 (push):** no production deploy without explicit per-session PO consent — caps the blast radius of any single change (controls C-family + accidental-regression risk).
- **Gate-2 (methodology/UX):** no user-facing or methodology change ships without PO sign-off *before build* — the control for A-family and F-family risk (an unreviewed methodology change is exactly how an accuracy or authority risk would ship silently).
- **Gate-3 (scope):** flag-and-proceed beyond a signed brief — keeps scope-creep (RF-26) visible.
- **gate #11 (capture activation):** the meta-gate that holds R11/E-family/RF-04/RF-31 dormant until §8.1 + §8.2 + a security pass clear.
- **Rule #14 (verified=executed):** the control that keeps the *other* controls honest — a paper control earns no residual-risk credit (R14 is the scar that produced this rule).

Escalation is trivial in a one-PO model: any risk whose residual is 🔴, or whose treatment is blocked on a PO decision, is surfaced in the chat with a **«القرار المطلوب»** and consolidated in Part 5.2.

## 2.4 The ship-disclosed principle and its risk meaning

The 2026-06-09 standing principle (§0.4 of `ISSUES_LOG.md`) is, in risk terms, a deliberate **risk-acceptance-with-disclosure** posture for Category A:

> A value-affecting method may ship **disclosed-as-indicative** — opt-in/rail-governed, wide MUC (VPGA 10), a "calibrated on limited n" label, and a `[land_floor, cost]` rail — and is tightened as the GT corpus grows. n≥20 gates **precision** and any **published accuracy claim**, not **shipping**.

This is sound risk management *for the disclosure dimension* — it converts an *undisclosed systematic error* (intolerable, see appetite §0.5) into a *disclosed indicative estimate* (tolerable). **But it explicitly does not reduce R20** (measurement): shipping disclosed does not tell you how wrong you are. The register therefore treats R19/R20 as the *binding* residual exposure even where R7's disclosure is handled.

## 2.5 What this register does not do

- It does not assign probabilities to two decimal places (the bands are coarse by design).
- It does not credit controls that are designed-but-not-executed (Rule #14).
- It does not make the PO's decisions — it frames them (Part 5.2).
- It does not supersede `RISK_REGISTER.md`; it extends it and will be reconciled back into it (Rule #63, see the closing note).

---

# PART 3 — THE REGISTER (CURRENT / ACTIVE RISKS)

**Entry template.** Each risk carries: a header block (Category · Status · Inherent · Residual · Owner · Response · Direction · Cross-refs · First logged); **Description & mechanism**; **Causes**; **Triggers / early-warning indicators (KRIs)**; **Impact if it crystallises**; **Current controls** (preventive / detective / corrective); **Residual exposure**; **Response strategy & contingency**; **Dependencies**; and **«القرار المطلوب»** where a PO decision is owed.

---

## 3.A — METHODOLOGY & VALUATION-ACCURACY RISKS

### R7 — Built-type + condition blindness is BIDIRECTIONAL (the master accuracy defect)

> **Category** A · **Status** OPEN (partially treated) · **Inherent** 20🔴 (L5×I4) · **Residual** 12🟠 (L4×I3) · **Owner** PO→CC · **Response** Reduce (active) · **Direction** → · **Cross-refs** R8, R22, R9 (closed a18), ISS-A01, E4, E23, §20.9, V001/V002/V003 · **First logged** 2026-05-31 (generalised), legacy 🟠

**Description & mechanism.** `geo_v2._categorize` lumps basic / 2-story+annex / +penthouse / مسكن / مجلس into one `'villa'` class, and **condition (finish / maintenance / lease) is not an input**. The engine therefore returns the comparable **pool's central tendency, blind to where the subject sits within it** — it **over-anchors** below-average-condition subjects and **under-anchors** above-average-condition ones. The defect is **bidirectional** and affects **both** comparison paths (widened *and* bracket). The earlier "widened-only / over-anchor-only" framing was too narrow; "bracket path validated clean" holds **only for average-condition subjects**.

**Causes.** (1) No built-type stratification in the categorizer. (2) No condition/finish/lease input in the flow. (3) The comparison method is a central-tendency estimator with no within-pool position signal.

**Triggers / early-warning indicators (KRIs).**
- **Over-anchor KRI:** a "reliable" bracket cell whose dispersion ≥ 0.30 (E23) — the subject may sit far from the median (Marikh n=29 passes T=20 yet sits +32% over the FULL-window median).
- **Under-anchor KRI:** a confirmed sale of a *new/premium* villa landing ≥ 25% above the engine estimate (V002/V003 = +60–67% vs engine, i.e. engine −37/−40%).
- **Corpus KRI:** `calibration_freshness` shows the `luxury_new` (E4) stratum at n=0 in the subject area → no premium signal available.

**Impact if it crystallises.** **Major (I4):** a large share of real stock — *every* property that is not average-condition for its bracket — receives a materially wrong headline. The **under-anchor** direction is the more financially dangerous (telling an owner a 4.0M villa is worth ~2.4M); the **over-anchor** direction harms buyers and the product's credibility (a 5.4M guess on a ~2.4M parcel). Measured on real sales: **±37–40%**.

**Current controls.**
- *Preventive:* the a10/a14 **dispersion gate** (catches dispersed pools → range-headline + 🟡 indicative + MUC high) — necessary but **not sufficient** (it does not catch the *tight-pool-above-average* under-anchor case, e.g. 56/565/21 dispersion 0.211). The `condition=teardown` / `new`+`is_luxury` levers (b4) handle the **extremes**, opt-in.
- *Corrective:* the **b11 §20.9 cost-reanchor down-half** (shipped v180) raises the floor of an old over-anchored villa to the depreciated-cost figure (Marikh floor 1.9M→2.4M), with the cost as the *informed* floor — but it **raises the floor, not the central estimate** (honest residual).
- *Detective:* the `VALIDATION_LOG.md` confirmed-sales process; the dispersion KRI on `/api/health`-adjacent cell stats.

**Residual exposure (12🟠).** The **over-anchor** half is *partially* treated (dispersion gate + cost floor); the **under-anchor** half is **untreated** — there is no shipped mechanism that lifts a new/premium villa toward its market level. The middle band (good / very-good / renovated) **still over-anchors at the widened value** because the 10-Year-Rule down-re-anchor fires only on explicit `teardown`, not on old-age+good-condition. This is the single largest residual accuracy exposure.

**Response strategy & contingency.** **Reduce**, in two moves (Part 5.1): (1) **§20.9 convergence + UP-lift** (treats the under-anchor half; needs the PO ~0.31 floor + a CGIS-vs-actual age recon); (2) **B-2 condition axis** (the durable bidirectional fix; PARKED on n≥20 GT). *(Errata: the previously-listed "A16/R9 root fix" is removed — a18/v157 already wired `area_match_key` into `build_reference` and resolved the pool starve, §20.18; the surviving Marikh over-anchor — 5.4M comparison_thin n=15 same-district, defensible ~3.0–3.4M plain — is pure condition.)* Contingency if none lands before beta: hold the **ship-disclosed** posture (wide MUC + range-as-lead + the "limited-n" label) so no over-confident point estimate is presented.

**Dependencies.** GT corpus n≥20 (R19) for the durable fix; the PO ~0.31 decision for the UP-lift; a live trace for the root fix.

**«القرار المطلوب» (PO).** احسم معامل أرضية «الفاخر المتهالك ~0.31» لفتح الرفع لأعلى (نصف التبخيس غير المُعالَج). (تصحيح: جذر A16/R9 أُغلق في a18 — لا بريف جذر ولا تتبُّعَ شرطيّاً؛ المتبقّي في امريخ هو الحالة، أي R7 نفسه.)

### R8 — Comparable-pool purity + thin-window volatility

> **Category** A · **Status** PARKED (Phase-2, diagnostics shippable) · **Inherent** 12🟠 (L4×I3) · **Residual** 9🟡 (L3×I3) · **Owner** CC · **Response** Reduce (deferred) · **Direction** → · **Cross-refs** R7, R9, E23, DEF-02 · **First logged** 2026-05-31 (Phase-1b measured), legacy 🟡

**Description & mechanism.** Two measured levers sit behind R7's over-anchor. (1) **Thin-window volatility:** geo_v2's 24-month default over-weights recent high villa sales — the STANDALONE_VILLA stratum runs **+8–11% above the FULL-window** median (Marikh bracket cascade 681 @24mo → 554 @36mo → 517 @FULL). (2) **Pool impurity:** geo_v2 pools by `نوع العقار` with **no residential-usage filter**, lumping HOUSE + STANDALONE_VILLA + penthouse + فيلتان; a usage filter removes ~22% of `cat=villa` and moves the pooled median **−5%**.

**Causes.** A type-based (not usage-based) pooling rule + a fixed 24-month window + thin cells (only **83/787 ≈ 10.5%** of cells reach n≥20 at 24mo).

**Triggers / KRIs.** A cell with n<20 *and* dispersion ≥0.30 (the combination, per E23 — n alone is insufficient); a 24mo→FULL median move >15% (thin cells move that much in 17% of cases vs 4% at n≥20).

**Impact if it crystallises.** **Moderate (I3):** a recency-biased or impure pool produces a median that systematically over- or mis-states a cohort — contributes directly to R7's over-anchor but is **orthogonal** to Marikh's specific over-anchor (the Marikh bracket cascade is flat 517→517→517 at FULL, so window/purity are *not* its driver — that was the R9 starve, closed at a18; the survivor is condition).

**Current controls.** *Detective:* the a10/a14 dispersion gate (the pairing partner for the n-threshold). *Corrective (designed, not yet built):* Phase-2 design inputs are **pinned** — 24mo default, widen to 36mo (preferred) then FULL when n<20; adopt the residential-usage filter (−5%) + compound removal (≤3%); shrinkage essential at 24mo.

**Residual exposure (9🟡).** The full Phase-2 engine is **not implemented** (a separate signed brief). Purity **diagnostics** *can* ship as disclosure (surface "limited comparables quality" in the evidence panel) before the engine lands — that would drop the residual further at low cost.

**Response strategy & contingency.** **Reduce (deferred):** the old "after A16/R9" sequencing is void (a18 fixed the matching); sequence Phase-2 on its own merits after the R7 priorities. Contingency: ship the purity *diagnostic* now (disclosure-only) so the user sees the limitation even before the engine corrects it.

**Dependencies.** None hard (the a18 matching fix removed the old R9 dependency); the dispersion gate (shipped) is the pairing control.

**«القرار المطلوب».** لا قرار جديد — (تصحيح: قيد A16/R9 سقط بإغلاقه في a18)؛ يمكن شحن تشخيص النقاء كإفصاح متى رغبت.

### R9 — Bracket-path area-name under-match (A16) — **RESOLVED-as-pool-fix at a18 (errata)**

> **Category** A · **Status** **CLOSED 2026-06-03 (Sprint a18, Heroku v157)** — corrected from OPEN by the 2026-06-09 errata pass · **Inherent** 12🟠 (L4×I3) · **Residual** — (closed; small monitored residual) · **Owner** CC (shipped) · **Response** Reduce — executed · **Cross-refs** R7, §20.18, CHANGELOG_v70, ISS-A03 · **First logged** A16, legacy 🟠 (the legacy `RISK_REGISTER.md` entry was never updated post-a18 — the source of this register's inherited error)

**What happened (measured✓, §20.18).** Sprint **2.22.0a.18** wired `moj_reference.area_match_key` (NBSP/whitespace collapse + hamza-fold + trailing-zone strip → **sibling aggregation**) into **`build_reference` + `compute_trend`** (the bracket path — previously exact-match) and `resolve_moj_area_name`, with overrides incl. **امريخ الجنوبي→مريخ**. Live smoke v157: Marikh 54/541/6 → **comparison_thin 5,400,000 n=15 same-district «مريخ»** (was comparison_widened 4.5M n=29 cross-district). Session_Log verdict, verbatim: «RISK_REGISTER R9 → resolved-as-pool-fix (condition residual = R7/Sprint B)».

**Why the value went UP, not down.** The same-district pool genuinely sells higher than the old cross-district widened pool — a18 fixed **which pool**, not condition. The surviving Marikh over-anchor (defensible ~3.0–3.4M plain vs the 5.4M thin median) is **pure R7** and is treated by b6 widen_down → b11 cost_reanchor_down (floor 1.9M→2.4M) → the §20.9 GATED slice → B-2.

**Monitored residual (small).** (1) Unreachable names: **فريج العسيري** (26 villa txns — no GIS ANAME contains «العسيري») + thin «المطار» (12) ≈ **0.25%** of villa lookups — they widen/refuse honestly (correct behaviour). (2) The a18 **fast-follow** (optional, never scheduled): one direct live hit on a sub-zone subject (معيذر/نعيجة address) to demonstrate aggregation end-to-end live — no gate, low priority. (3) **Doc-drift:** the legacy `RISK_REGISTER.md` R9 row still reads OPEN — owed a one-line closure edit (R-H / Rule #63).

**«القرار المطلوب».** لا قرار — مُغلق؛ يتبقّى سطر إغلاق R9 في السجلّ القانوني (يطويه CC في أقرب commit توثيقي).

### R22 — Cost-Approach DRC calibration could re-import the R7 bias

> **Category** A · **Status** OPEN (control-by-discipline) · **Inherent** 9🟡 (L3×I3) · **Residual** 6🟡 (L2×I3) · **Owner** CC/Claude.ai · **Response** Reduce (discipline) · **Direction** → · **Cross-refs** R7, §20.9, METHODOLOGY_cost_triangulation_v1, ISS-A04 · **First logged** 2026-06-09 (this register)

**Description & mechanism.** The §20.9 cost-triangulation is the durable R7 fix, but it carries a *self-referential* trap: if the depreciated construction rate is **calibrated to the MoJ median**, the DRC simply **re-imports the very bias (R7) it is meant to correct** — the "independent" second method would not be independent. The discipline (recorded in the methodology seed) is to **build a pure DRC** (land floor + depreciated building from real construction-cost anchors, e.g. the Al Manara bank's ~2,380 ر.ق/م² for a premium build), observe Market-vs-DRC divergence *by segment*, and **not** force a hard ceiling.

**Causes.** The temptation to calibrate the DRC to the data we have (MoJ) rather than to true construction cost (which we have less of).

**Triggers / KRIs.** Any DRC build-rate parameter sourced from `moj_reference` rather than a construction-cost anchor; a DRC output that tracks the Market median too closely across segments (a sign it is not independent).

**Impact if it crystallises.** **Moderate (I3):** the durable R7 fix would *look* like a fix while reproducing the bias — arguably worse than no fix, because it would carry false confidence.

**Current controls.** *Preventive:* the documented discipline (build pure DRC, don't calibrate to median); the `[land_floor, cost]` **rail** as a sanity bound; the b11 down-half already uses cost as an *informed floor*, not a median-derived one.

**Residual exposure (6🟡).** The discipline is documented but the full §20.9 convergence/UP-lift is **not yet built**, so the trap is *latent*. The control is a process rule, not yet code.

**Response strategy & contingency.** **Reduce:** enforce the discipline in the §20.9 brief's §5 audit (Gate-2). Contingency: if a pure construction-cost anchor is unavailable for a segment, ship that segment disclosed-as-indicative rather than calibrating to MoJ.

**Dependencies.** Construction-cost anchors per segment (premium vs ordinary); the §20.9 brief.

**«القرار المطلوب».** لا قرار الآن — يُحسم ضمن تدقيق §5 لبريف §20.9 (بناء DRC مستقلّ، لا معايرة على وسيط MoJ).

---

## 3.B — DATA & DEPENDENCY RISKS

### R4 — MoJ data stale; refresh not self-serving

> **Category** B · **Status** OPEN (external) · **Inherent** 12🟠 (L4×I3) · **Residual** 6🟡 (L3×I2) · **Owner** EXT (monitor) · **Response** Accept + Reduce-via-disclosure · **Direction** → (↑ as it ages) · **Cross-refs** R21, RF-16, ISS-D01, E (MoJ rules) · **First logged** legacy 🟡

**Description & mechanism.** `data.gov.qa` last published **2025-12-31**; the snapshot is **160 days stale** (measured✓). Adopting any new drop is gated on a multi-factor sanity gate (schema / NBSP / volume) before it can replace the snapshot — so the staleness is *transparent* but it does **drift** the engine away from the live market as it ages.

**Causes.** External — the open-data publisher's cadence is outside our control; the freeze began after 2025-12-31.

**Triggers / KRIs.** `/api/health` `moj_freshness.days_old` crossing thresholds (160 today; **>180 = a quarter stale**; **>365 = a year**); the `tier` field flipping further from `fresh`.

**Impact if it crystallises.** **Minor→Moderate (I2/I3):** recent appreciation or a market turn is not reflected; medians lag. Bounded because LAND/HOUSE medians are window-stable (R8/B1 measured) and the MUC clause communicates the limitation. Escalates if the freeze persists for years (the corpus ages out of relevance — see RF-29).

**Current controls.** *Detective:* the `/api/health` freshness tier + the Sprint-2.7 staleness banner. *Corrective:* the **MUC clause** (active since 2026-02-28) on the user-facing surface; the **multi-factor adoption gate** prevents a bad/biased new drop from being silently adopted (this is the control that converts R4's *resumption* into RF-16 rather than a silent shift). Self-healing: when the publisher resumes, `/api/health` recomputes freshness automatically.

**Residual exposure (6🟡).** Manageable *while transparent*; the residual rises monotonically with `days_old`. The real risk is not the staleness itself but the **resumption shock** (RF-16) and the **permanent-dark tail** (RF-29).

**Response strategy & contingency.** **Accept** the staleness (disclosed) + **Reduce** via the MUC and banner. Contingency for resumption: run the multi-factor gate on the new drop *before* adoption and diff every anchor; contingency for permanent-dark: see RF-29 (alternative-source exploration becomes load-bearing).

**Dependencies.** None controllable; monitor `/api/health`.

**«القرار المطلوب».** لا قرار الآن — مراقبة `days_old`؛ عند استئناف النشر، شغِّل بوّابة التبنّي متعدّدة العوامل قبل الاعتماد (RF-16).

### R19 — Ground-truth corpus scarcity (n<20) gates precision & any accuracy claim

> **Category** B · **Status** OPEN · **Inherent** 15🔴 (L5×I3) · **Residual** 12🟠 (L4×I3) · **Owner** PO / EXT · **Response** Reduce (corpus growth) · **Direction** ↓ · **Cross-refs** R7, R20, RF-05, ISS-D07, §0.4 standing principle, Confirmed-Sales-DB (2.16.16) · **First logged** 2026-06-09 (this register; long-standing in substance)

**Description & mechanism.** The project has only a **handful** of parcel-linked confirmed sales (V001/V002/V003 + a few references) against which to *calibrate* coefficients and *validate* accuracy. The §0.4 standing principle is explicit: **only n≥20 parcel-linked confirmed sales calibrate the precise coefficient and license any published accuracy claim.** Until then, every value-affecting method ships *disclosed-as-indicative* (b4 and b11 both shipped on **n=2**). The calibration table reflects this: **184 of 200 cells are fallback** (measured✓) — only 6 reliable + 10 indicative.

**Causes.** No durable confirmed-sales source (the Confirmed-Sales-DB was dropped — no viable internal feed); MoJ records are registration values, not a clean confirmed-sale ground truth with condition/built-type labels.

**Triggers / KRIs.** `calibration_freshness.by_confidence.fallback` share (92% today); the count of parcel-linked confirmed sales in `VALIDATION_LOG.md` (currently single digits) vs the n≥20 bar; the per-stratum n (the `luxury_new` E4 stratum is n=0 in both R7 motivating areas).

**Impact if it crystallises (or rather, persists).** **Moderate (I3):** no method can be *tightened* beyond indicative; no *published* accuracy claim is licensable; the durable R7 fix (B-2) stays PARKED. It caps the product's credibility ceiling and is the **binding constraint on accuracy maturation**.

**Current controls.** *Corrective:* the **ship-disclosed-as-indicative** posture (wide MUC + "calibrated on limited n" label + the `[land_floor, cost]` rail) *decouples shipping from precision* — this is the control that keeps the product moving despite the scarcity. *Preventive (planned):* the corpus grows via **(a)** valuer reports / manual confirmed sales (GT-1/GT-2) and **(b)** organic beta usage.

**Residual exposure (12🟠).** Still high because the corpus is *currently* scarce and the two main growth channels are **not yet flowing** (beta not launched; no steady valuer-report intake). Direction is **↓** — this is the one top-table risk that *improves on its own* once beta launches, which is exactly why the beta go-call is strategically central.

**Response strategy & contingency.** **Reduce:** start the GT-collection track (manual valuer reports + organic use — beta as a parallel non-blocking track per ISS-G03; no cohort gate); stand up a lightweight valuer-report / confirmed-sale intake (manual is fine at this stage). Contingency: continue shipping disclosed-as-indicative; never convert an n<20 method into a point claim.

**Dependencies.** The PO's start-call on GT collection (no cohort gate — ISS-G03) is the primary unlock; R20 (measurement) is the sibling.

**«القرار المطلوب».** بدء مسار جمع الـGT (يدويّ + عضويّ — لا بوّابة كوهورت بعد إعادة التأطير ISS-G03) هو المُحرِّك الأساسي لنموّ الكوربوس — وهو القيد الملزم على نضج الدقّة.

### R20 — No live accuracy-measurement instrument (capture dormant)

> **Category** B · **Status** OPEN · **Inherent** 15🔴 (L5×I3) · **Residual** 12🟠 (L4×I3) · **Owner** PO→CC · **Response** Reduce (activate measurement) · **Direction** ↓ · **Cross-refs** R7, R11, R19, RF-04, ISS-D08, gate #11 · **First logged** 2026-06-09 (this register)

**Description & mechanism.** The engine ships **without a production error-distribution**. The prediction-capture instrument (a15) exists but is **DORMANT** (no `DATABASE_URL`, flag off — measured✓). The only accuracy signals are **four value-invariant anchors** (drift guards, not an error distribution) plus the handful of confirmed sales. In risk terms: the product is **flying without an error gauge** — it cannot quantify *how often* and *by how much* it is wrong in the field.

**Causes.** Capture is held dormant pending the §8.1 (PDPPL fields/retention/consent) + §8.2 (cross-border residency) decisions + a security pass (gate #11) — a *correct* privacy control that has the *side effect* of leaving accuracy unmeasured.

**Triggers / KRIs.** The existence (or not) of a populated capture table; the count of prediction↔outcome pairs; the gap between "anchors stable" (drift guard) and "distribution known" (accuracy) — today only the former exists.

**Impact if it crystallises (persists).** **Moderate (I3):** R7's true field-error is *unknown* — the ±37/40% is from three sales, not a distribution. Without measurement, the team cannot prioritise the R7 fixes by *actual* prevalence, cannot detect a regression in production, and cannot ever substantiate an accuracy claim (compounds R19).

**Current controls.** *Detective (weak):* the four anchors catch *byte-level drift* (a deploy that changes a known value) but say nothing about *accuracy*. *Preventive:* gate #11 keeps the (privacy-risky) capture dormant — protecting E-family/PDPPL risk at the cost of measurement.

**Residual exposure (12🟠).** High — measurement is the prerequisite for *evidence-based* accuracy work, and it is absent. Direction **↓** once gate #11 clears and capture activates (then R20 drops sharply as a distribution accumulates).

**Response strategy & contingency.** **Reduce:** clear gate #11 (the §8.1/§8.2 decisions + the CC security pass) and activate capture *with* the privacy hardening already built (UUID-only key, Fernet-encrypted street/building, 180-day retention, purge/erase). Contingency until then: treat all accuracy statements as *anchored-and-disclosed*, never *measured-and-claimed*; lean on confirmed sales as the interim signal.

**Dependencies.** Gate #11 (R11) — which is itself gated on the PO §8.1/§8.2 decisions.

**«القرار المطلوب».** احسم §8.1 (سياسة الحقول/الاحتفاظ) + §8.2 (إقامة البيانات عبر الحدود) لفتح بوّابة #11 وتفعيل قياس الدقّة — فبدونه يبقى الخطأ الميداني غير مقيس.

### R21 — MoJ single-source systemic dependency & discontinuation

> **Category** B · **Status** OPEN (structural) · **Inherent** 12🟠 (L3×I4) · **Residual** 12🟠 (L3×I4) · **Owner** EXT · **Response** Accept (structural) + plan contingency · **Direction** → · **Cross-refs** R4, RF-16, RF-20, RF-29, E1/E12, ISS-D01 · **First logged** 2026-06-09 (this register)

**Description & mechanism.** MoJ is the **sole** market-truth source by design (E1/E12 — listings appear only in the sentiment panel; the buyer hard ceiling is MoJ × 1.10). The whole valuation inherits MoJ's properties: its coverage, its registration-value convention, its publication cadence, and its licence. There is **no alternative truth source** wired in. This is a *concentration* risk distinct from staleness (R4): even a perfectly *fresh* MoJ feed is a single point of dependence whose **discontinuation, structural bias, schema change, or licence change** would propagate uncapped.

**Causes.** A deliberate methodology choice (MoJ is the only defensible transaction-evidence source in Qatar) with no second source available at comparable quality.

**Triggers / KRIs.** Publisher discontinuation (RF-29); a MoJ schema change at the next drop (RF-16); a licence change away from CC BY 4.0 (RF-20); evidence of a structural registration-value↔transaction-value gap changing over time (RF-22).

**Impact if it crystallises.** **Major (I4):** loss or corruption of the *only* evidence base. A schema change halts ingestion; a licence revocation removes the legal basis for the derivative product; a structural-bias shift silently mis-states every valuation.

**Current controls.** *Detective:* `/api/health` freshness + the multi-factor adoption gate (catches a schema/volume anomaly at the next drop). *Corrective:* the CC BY 4.0 licence is *verified and attributed* (a25) — a stable legal basis *today*. *Structural:* the engine is honest that MoJ is the basis (the attribution + methodology note).

**Residual exposure (12🟠).** Essentially **un-reducible** at this stage — there is no second source to diversify into, and the under-registration hypothesis being *falsified* (E1: villa asking-premium +70% is stock composition, not under-registration) is reassuring but does not remove the single-point dependence. This is an **accepted structural risk** with **contingency planning** rather than prevention.

**Response strategy & contingency.** **Accept** (structural, with eyes open) + **plan**: maintain the multi-factor gate as the schema-change tripwire; keep the licence verification current; if the feed goes permanently dark (RF-29), the contingency is to explore an alternative transaction source (developer data T3, or a future MME/registry feed) — currently not viable, hence a *plan*, not a *control*.

**Dependencies.** External; nothing controllable beyond monitoring + the adoption gate.

**«القرار المطلوب».** لا قرار الآن — خطر بنيويّ مقبول؛ يُدار بالمراقبة + بوّابة التبنّي + تحديث التحقّق من الرخصة. الخطّة البديلة تُفعَّل فقط عند RF-29.

### R-B (monitored) — Data-hygiene & coverage sub-risks

> **Category** B · **Status** MONITOR (controlled, low residual) · **Owner** CC · **Cross-refs** ISS-D02/D03/D04, Rule #45

A cluster of well-controlled data-integrity items kept on the register as *monitored* (each scored 🟢/low — controls are live and effective), because a regression in any of them would silently corrupt the evidence base:

- **NBSP / whitespace duplication (ISS-D03).** MoJ values appear in both NBSP (`\xa0`) and regular-space forms; a direct string match loses ~half the data. **Control (preventive):** mandatory `re.sub(r'\s+', ' ', s).strip()` before *any* string comparison. **Residual 🟢** while the normalisation is applied everywhere; **KRI:** any new string-match site that skips normalisation (code-review trigger). This was *also* a contributing cause of the (now-closed) R9 area-name under-match.
- **Article-drop "ال" (ISS-D04).** MoJ area names often drop the definite article (الدحيل → "دحيل"); naive matching mis-resolves the area. **Control:** the `area_match_key` / hamza-fold + alias logic. **Residual 🟢** (a18 wired `area_match_key` into `build_reference` + `compute_trend` — the bracket-build gap is closed; the only residual is the unreachable-name class — فريج العسيري 26 txns / thin «المطار» 12, ~0.25% — which widens/refuses honestly).
- **No-PIN coverage (ISS-D02 / Rule #45).** Properties without a resolvable PIN cannot be classified/located. **Control:** explicit refusal/insufficient-data path rather than a guess. **Residual 🟢** (honest refusal is the correct behaviour).
- **`curl` hangs on `data.gov.qa`; Cloudflare 1010 on `thammen.qa` for urllib.** **Control:** `urllib` for MoJ, browser-UA `curl` for thammen.qa (Rule #61). **Residual 🟢** (tooling discipline, documented).

**Response.** **Reduce/Monitor** — keep the controls; treat any code-review finding of an un-normalised string match as a risk event. The article-drop item's residual is now 🟢 — its defect surface (R9) was closed at a18; the watch item is the small unreachable-name class.

---

## 3.C — TECHNICAL & INFRASTRUCTURE RISKS

### R5 — QARS / GIS Heroku reachability fragility

> **Category** C · **Status** MITIGATED · **Inherent** 12🟠 (L3×I4) · **Residual** 6🟡 (L2×I3) · **Owner** CC · **Response** Reduce · **Direction** → · **Cross-refs** R21, RF-15, ISS-T01, Rule #11, E7 · **First logged** Sprint 2.22.0a.1, legacy 🟠

**Description & mechanism.** The khazna `QARS_Point` endpoint returned an ArcGIS **auth-error envelope** from the Heroku AWS IP (Sprint 2.22.0a.1); a *silent* envelope-as-empty failure degraded address-tab classification (every address returned `asset_type=unknown` until the v132 hotfix). The dependency is a **government GIS endpoint outside our egress** — reachable from Heroku but not from the Claude.ai sandbox, and subject to auth/WAF behaviour we don't control.

**Causes.** A government endpoint's auth/WAF posture toward a cloud IP + a fallback that treated an error *envelope* as an empty result rather than a failure.

**Triggers / KRIs.** `/api/health` `qars_endpoint.status` ≠ `healthy` (today: healthy, primary 162,496 / legacy 162,497 — measured✓); a spike in `asset_type=unknown` on address evaluations; a primary↔legacy count divergence beyond the usual ±1.

**Impact if it crystallises.** **Moderate (I3):** address-based classification degrades to `unknown`, which cascades into the valuation path; a *silent* version of this (the original bug) is worse than a loud failure because it mis-classifies rather than refuses.

**Current controls.** *Corrective:* `_qars_query()` primary→legacy **fallback on both exceptions AND ArcGIS envelopes** (Rule #11 defensive design, v132). *Detective:* `/api/health` `qars_endpoint` monitor. *Preventive:* the E7 cross-check (QARS subtype × Zoning) guards against a *stale-but-reachable* subtype (a related failure mode — 9.1% of government buildings had stale subtypes, Bug A11).

**Residual exposure (6🟡).** The *silent* failure mode is closed (envelopes now trigger fallback). The residual is a **simultaneous** primary+legacy outage or a breaking schema/auth change (→ RF-15) — low likelihood, but fully external.

**Response strategy & contingency.** **Reduce:** keep the dual-endpoint fallback + the health monitor. Contingency for a breaking change: the address path refuses honestly (insufficient data) rather than guessing; a schema change is treated like RF-15 (endpoint decommission).

**Dependencies.** External GIS availability; nothing controllable beyond the fallback + monitor.

**«القرار المطلوب».** لا قرار — مُخَفَّف؛ مراقبة `qars_endpoint` في `/api/health`.

### R16 — Infrastructure single-point-of-failure (single Eco dyno / region / ephemeral FS)

> **Category** C · **Status** OPEN (beta-acceptable) · **Inherent** 9🟡 (L3×I3) · **Residual** 9🟡 (L3×I3) · **Owner** CC · **Response** Accept (beta) → Reduce (pre-monetization) · **Direction** → (↑ at scale) · **Cross-refs** RF-13, R5, ISS-T02/T07 · **First logged** 2026-06-09 (this register)

**Description & mechanism.** Production runs on a **single Heroku Eco dyno** in a single region, with an **ephemeral filesystem** (state resets on restart) and a **30-second router timeout**. There is no horizontal redundancy, no multi-region failover, and any in-process state is lost on a dyno cycle. For a free invite-only beta this is *acceptable*; for a paid or at-scale service it is not.

**Causes.** A deliberate cost/stage trade-off (Eco dyno) appropriate to a pre-revenue beta.

**Triggers / KRIs.** Dyno cold-start latency creeping toward the 30s wall (the R2 cold-503 was this class, now closed at ~15s with ~15s margin); any feature that *needs* durable local state (none today — state is in git + the MoJ snapshot); concurrency beyond a single dyno's capacity (a beta cohort is fine; a public launch is not).

**Impact if it crystallises.** **Moderate (I3):** a dyno outage = full unavailability (no failover); a cold-start near the timeout = intermittent 503s (the R2 failure mode); an ephemeral-FS assumption baked into a feature would lose data on restart. Bounded today because the app is stateless-per-request and the beta is small.

**Current controls.** *Preventive:* the app is **stateless per request** (no reliance on local durable state); the **≤10s fetch budget** + parallelised GIS I/O (R2 fix) keeps requests well under the 30s wall. *Detective:* `/api/health` latency behaviour; the four-anchor smoke after each deploy.

**Residual exposure (9🟡).** Unchanged from inherent because there is **no HA/redundancy control** — the controls bound *latency* and *statelessness*, not *availability*. This is an **accepted** beta-grade posture that **must be reduced before monetization/scale** (RF-13).

**Response strategy & contingency.** **Accept** for the beta + **Reduce** before paid/scale: provision a larger/redundant dyno tier and (if capture activates) managed Postgres with short backup retention. Contingency: the stateless design means a restart loses nothing but in-flight requests; an outage is a clean unavailability, not data loss.

**Dependencies.** Tied to the monetization/scale gates (RF-13); the capture-DB residency decision (§8.2) interacts here.

**«القرار المطلوب».** لا قرار الآن — مقبول للبيتا؛ يجب رفع البنية (تكرار + قاعدة بيانات مُدارة) قبل التسييل/التوسّع.

### R-C (monitored) — Edge, timeout & tooling sub-risks

> **Category** C · **Status** MONITOR · **Owner** CC · **Cross-refs** R12 (legacy), ISS-T02/T03, Rule #61, E21

- **Heroku 30s router timeout (E21 / ISS-T02).** All fetch operations are budgeted ≤10s with parallelised I/O. **Control (preventive):** the ≤10s budget + the R2 parallelisation. **Residual 🟢** while the budget holds; **KRI:** any new serial GIS chain or a fetch without a timeout.
- **Cloudflare 1010 blocks urllib POST from CC (legacy R12).** A bare urllib POST to thammen.qa is edge-rejected (bot signature). **Control:** Rule #61 — CC post-deploy POST smoke uses **browser-UA curl**, not urllib; GET /api/health is never blocked. **Residual 🟢/4** (mitigated); **KRI:** Cloudflare tightening to a JS challenge (then fall back to PO/Claude.ai-side smoke).
- **Ephemeral filesystem (ISS-T07).** State resets between dyno cycles. **Control:** stateless-per-request design; truth lives in git + the MoJ snapshot, not local FS. **Residual 🟢**; **KRI:** any feature that assumes durable local writes (would need managed storage).

- **Heroku deploy auth (§20.45).** CC's heroku CLI auth can expire mid-arc — the b11 deploy failed twice (`could not read Username`; the GCM username/password fill was rejected, Heroku is token-only) until Anas ran `heroku login` and pushed from his terminal. **Control (procedural):** check `heroku auth:whoami` before any Gate-1 push; if unauthorized, hand the `git subtree push` to the PO's terminal — never request a token in-transcript. **Residual 🟢**.

**Response.** **Monitor** — these are documented scar-tissue controls; the risk is *forgetting* them in a new code path. Treat any violation as a code-review risk event.

---

## 3.D — REGULATORY & COMPLIANCE RISKS

### R13 — Regulated-activity self-clearance without external counsel (beta posture)

> **Category** D · **Status** OPEN (accepted-with-mitigations) · **Inherent** 15🔴 (L3×I5) · **Residual** 8🟡 (L2×I4) · **Owner** PO · **Response** Accept (beta) + Reduce + Transfer-deferred · **Direction** → (↑ to 🔴 at monetization) · **Cross-refs** RF-06, RF-07, RF-09, RF-17, RF-19, R11, ISS-R01 · **First logged** 2026-06-02, legacy 🟠

**Description & mechanism.** التقييم العقاري (real-estate valuation) is a **named regulated activity** under **Amiri Decision No. 28 of 2023, Article 5(7)** (Aqarat) plus a broad catch-all («وغيرها من الأنشطة العقارية»), and the valuer-licensing regime is **tightening** (Peninsula, May 2026: "broker-as-valuer no longer acceptable"). Anas elected (2026-06-02) **not** to engage licensed counsel and to **self-clear conservatively**. Operating even a *free* AVM on internal / AI-derived assumptions therefore carries a **managed-but-real** (a) unlicensed-regulated-activity exposure and (b) PDPPL exposure — neither *fully* curable by conservatism. There is **no AVM-specific binary** in the public sources (an ambiguity, not a clearance).

**Causes.** A named-regulated-activity statute + a tightening regime + a deliberate decision to proceed without counsel + the absence of a dedicated AVM licensing category (the regime did not anticipate AVMs).

**Triggers / KRIs.** Any move from *free* to *paid* (the single biggest trigger — flips this to RF-09 at 🔴); a regulator query or a public complaint; a tightening of the Aqarat regime that names AVMs; a PDPPL enforcement action in the sector.

**Impact if it crystallises.** **Severe (I5):** an unlicensed-regulated-activity finding could force the tool down (cease-and-desist, RF-30) and/or carry penalties; the impact is *capped for the beta* by the free + invite-only + disclaimed posture but is **not eliminated**.

**Current controls.**
- *Preventive:* the beta is **free, invite-only, accuracy-research**, labelled «تقدير سوقي آلي، وليس تقييماً معتمداً» — i.e. it does **not** hold itself out as a regulated valuation; **no paid access pre-licence** (zero appetite, §0.5).
- *Corrective/Transfer-deferred:* the **Aqarat enquiry is drafted and on HOLD** (`Aqarat_Enquiry_DRAFT_hold.md`) — to be sent post-design, pre-monetization; this *defers* the regulatory clarification to the right moment rather than poking the regulator prematurely.
- *Preventive (PDPPL):* self-cleared conservatively (strict opt-in, all records personal data, 180-day retention, full erasure, Qatar/GCC residency — cross-ref R11); the capture stays dormant until that clears.
- *Closed sub-item:* the **MoJ open-data licence** is **CLOSED** — verified **CC BY 4.0** (commercial + derivatives + redistribution permitted with attribution), attribution shipped a25. No longer a paid gate.

**Residual exposure (8🟡 for the beta).** Acceptable *for a free, disclaimed, invite-only beta* under the documented self-clearance (`COMPLIANCE_SELF_CLEARANCE_beta_v1.md` + Honesty #10). The residual **escalates to 🔴** the moment money is involved (RF-06/RF-07/RF-09) — the disclaimer that protects the beta does **not** protect a paid, relied-upon valuation.

**Response strategy & contingency.** **Accept** the beta exposure (mitigated) + **Reduce** (disclaimers, dormant capture, no paid access) + **Transfer-deferred** (send the Aqarat enquiry before monetization; engage counsel/PI insurance at the paid gate). Contingency for a regulator query: the enquiry draft + the self-clearance doc are the prepared response; the tool can be paused if ordered.

**Dependencies.** The monetization decision (the escalation trigger); the Aqarat enquiry timing (PO-reserved).

**«القرار المطلوب».** لا قرار جديد للبيتا — لكن **قبل أي تسييل**: أرسِل استعلام Aqarat، وأعِد تقييم الوضع التنظيمي (يقفز إلى 🔴 عند الانتقال للمدفوع — RF-06/09).

### R-D (monitored) — RICS-claim scope & licensing-category ambiguity

> **Category** D · **Status** MONITOR · **Owner** PO/Claude.ai · **Cross-refs** RF-17, RF-18, ISS-R03/R04, Appendix G

- **RICS-claim-scope (ISS-R03).** The product frames its methodology *to* RICS Red Book / IVS standards; the risk is over-claiming **compliance** (vs *alignment with*). **Control (preventive):** the honest status label «بانتظار مراجعة مُقيِّم مُرخّص (المرحلة الخامسة)» (a20) — `rics_compliant=false` reads as "review pending," not "non-compliant"; the citation map (Appendix G) is primary-source-verified (Rule #54). **Residual 🟢/🟡** while the framing stays *alignment-not-certification*; **KRI:** any copy that asserts certified RICS compliance without a licensed valuer in the loop.
- **No dedicated AVM licensing category (ISS-R04 / RF-17).** The Qatar regime has no AVM category — an *ambiguity* that could resolve as either an opportunity (a clear path) or a burden (a costly new requirement). **Control:** monitor the regime; the held Aqarat enquiry is the probe. **Residual 🟡** (forward — see RF-17).

**Response.** **Monitor** + keep the alignment-not-certification discipline; re-audit citations on any RICS/IVS update (Rule #54, RF-18).

---

## 3.E — SECURITY & PRIVACY RISKS

### R11 — Beta instrumentation shipped DORMANT; must not be activated before counsel

> **Category** E · **Status** OPEN (dormant-pending-activation) · **Inherent** 12🟠 (L3×I4) · **Residual** 4🟢 (L1×I4) · **Owner** PO→CC · **Response** Avoid-until-cleared (gate #11) · **Direction** → (↑ at activation) · **Cross-refs** R20, RF-04, RF-31, gate #11, §8.1/§8.2, ISS-R05 · **First logged** 2026-06-01, legacy 🟡

**Description & mechanism.** Sprint a15 added prediction capture + `POST /api/feedback`; a captured record is **personal / quasi-personal data under PDPPL**, so activating before the data-policy + cross-border ruling would create an **unlawful-processing** risk. The instrument is **DORMANT** — it no-ops unless **both** `EVAL_CAPTURE_ENABLED=true` **and** `DATABASE_URL` are set, and the Postgres add-on is **not** provisioned (measured✓: capture inert, `/api/feedback` → `{accepted, stored:false}`).

**Causes.** A measurement need (R20) that *requires* collecting quasi-personal data, intersecting an unresolved PDPPL policy (§8.1) + cross-border residency (§8.2) + an un-run security pass (gate #11).

**Triggers / KRIs.** Setting the flag *or* provisioning the add-on **before** §8.1 + §8.2 clear (the prohibited action); the Fernet round-trip not yet verified on Heroku; backup-retention not yet set short.

**Impact if it crystallises.** **Major (I4):** activating prematurely = unlawful processing of personal data under PDPPL (regulatory + reputational), plus a breach surface (RF-31). The impact is high; the **likelihood is held to Rare (L1)** *by the dormancy control*.

**Current controls.**
- *Preventive (the key control):* **double-condition dormancy** (flag AND DB) + the add-on un-provisioned — the instrument *cannot* process data until a deliberate two-step activation; gate #11 holds activation behind §8.1 + §8.2 + a security pass.
- *Preventive (surface hardening, a16):* UUID-only key, **no stored `valuation_id`**, street/building **Fernet-encrypted**, the free-text `note` **removed**, 180-day retention + aggregate/purge/erase.
- *Corrective (designed, pre-activation):* verify the Fernet encrypt/decrypt round-trip **on Heroku** before any real data; set Heroku PG backup retention **short**; a **backup-erasure runbook** for an erasure request mid-retention.

**Residual exposure (4🟢 while dormant).** Low **because it is inert** — the residual is almost entirely *latent*, realised only at activation. At activation the residual jumps to the **inherent band** unless the corrective controls (Fernet round-trip, short backups, runbook) are **executed** (Rule #14 — paper controls earn no credit). The activation itself is gated on PO decisions.

**Response strategy & contingency.** **Avoid-until-cleared:** do not set the flag or provision the add-on before §8.1 + §8.2 + the security pass. At activation: execute the three corrective controls first. Contingency for an erasure request: the runbook; for a breach: see RF-31.

**Dependencies.** §8.1 (fields/retention/consent) + §8.2 (residency) — PO + counsel; then the CC gate-11 security pass.

**«القرار المطلوب».** احسم §8.1 + §8.2 قبل أي تفعيل — ولا تُفعّل العلَم أو تُهيّئ قاعدة البيانات قبلهما (هذا أيضاً ما يفتح قياس الدقّة R20).

### R-E (monitored) — Capture-surface, secrets & abuse sub-risks

> **Category** E · **Status** MONITOR (mostly forward) · **Owner** CC · **Cross-refs** RF-02, RF-31, ISS-R06, a24 §4

- **Address logging (a24 §4).** The property address was **scrubbed** from the two `/api/evaluate*` INFO logs to back the DPIA "we don't store the address" (client IP kept for ops). **Control (preventive):** the log-scrub. **Residual 🟢**; **KRI:** any new log line that echoes the address.
- **Secret handling.** `CAPTURE_ENC_KEY` set only at activation; `cryptography` via requirements. **Control:** secrets in Heroku config, not in code. **Residual 🟢**; **KRI:** any secret in the repo.
- **Abuse / scraping (forward → RF-02).** Rate-limits 5/s·30/min·200/h on `cf-connecting-ip` (measured✓). **Control (detective/preventive):** the rate-limit + CORS lock. **Residual 🟡** (the key is per-IP, evadable at scale — a *beta* control, see RF-02).
- **Breach of activated capture (forward → RF-31).** Until capture activates, there is **no PII store to breach** — the dormancy is itself the strongest control. **Residual 🟢 today**, jumps at activation (RF-31).

**Response.** **Monitor** + keep the dormancy as the master control; the abuse/breach items are *forward* (they become live at scale / at capture activation).

---

## 3.F — PRODUCT, UX & REPUTATIONAL RISKS

### R-F1 — Authority / finality miscalibration (the number reads as more certain than it is)

> **Category** F · **Status** OPEN (actively managed) · **Inherent** 12🟠 (L4×I3) · **Residual** 8🟡 (L2×I4) · **Owner** PO→CC · **Response** Reduce · **Direction** ↓ · **Cross-refs** R7, RF-01, ISS-U05, §2b/§2c, DESIGN_2p2x_v4 · **First logged** 2026-06-09 (this register; long-standing in design)

**Description & mechanism.** An AVM headline number carries **unearned authority** — a confident point estimate invites reliance the evidence does not support, especially given R7's known bias. The design principle (§2c) is that **drama/authority attaches to analytical depth and evidence quality, never to hyping the figure**, and that **explanation does not raise confidence**. The risk is that any surface — the headline, the report, the polished result — *reads* as a definitive valuation rather than an indicative estimate.

**Causes.** Human anchoring on a single number + the natural tendency of a polished UI to confer authority + R7's hidden bias making the number wrong in a way the user can't see.

**Triggers / KRIs.** A surface that presents a *point* estimate without the range/MUC; user feedback that treats the number as definitive; a screenshot shared as "the value" rather than "an estimate."

**Impact if it crystallises.** **Major (I4):** a user makes a real decision (lists, buys, negotiates) on an over-confident number that is wrong by R7's margin → financial harm to the user + reputational + (at paid) liability (RF-07). Reputationally this is the channel by which R7 becomes *visible* (RF-01).

**Current controls.**
- *Preventive:* **range-as-lead** headline (b3 — the true low–high range leads, not a point; asymmetry allowed, no invented symmetric ±); the **evidence-quality panel** (b2.2 — four components rated strong/moderate/limited, *derived* from engine fields, with "explanation≠confidence" enforced); the **confirmation gate** (b2.3) and the staged authority that **starts low and rises only with accountability at stage 5**; the persistent **«تقدير سوقي آلي، وليس تقييماً معتمداً»** label; **MUC** (VPGA 10) on uncertain paths.
- *Detective:* user feedback (once beta launches); the dispersion gate's range-headline trigger.

**Residual exposure (8🟡).** Well-managed in *structure* (range-lead + evidence panel + disclaimers), but the **decomposition-coherence** and the **polished-result/report** screens (ISS-U03) are **not yet built to spec** — a coherent, well-calibrated final surface is pending. Residual direction **↓** as those screens land *with* the authority discipline.

**Response strategy & contingency.** **Reduce:** build screens 4–5 *after* decomposition-coherence, carrying the range + MUC + the staged-authority boundary; keep the "indicative, not certified" label everywhere. Contingency: if a public mis-valuation surfaces (RF-01), the disclaimer + range framing is the prepared response.

**Dependencies.** ISS-U03 (the final screens); decomposition-coherence first; R7 treatment reduces the *underlying* error this risk *presents*.

**«القرار المطلوب».** لا قرار جديد — يُدار بتسلسل الشاشات (التماسُك ثم النتيجة المصقولة) مع حدّ السلطة المرحلي + إبقاء وسم «تقدير آلي، ليس تقييماً معتمداً».

### R-F2 (monitored) — Beta-cohort & public-perception sub-risks

> **Category** F · **Status** MONITOR (forward-leaning) · **Owner** PO · **Cross-refs** RF-01, RF-05

- **Cohort reputational (→ RF-05).** The invite cohort's first impressions shape early word-of-mouth; a cohort over-weighted to a segment R7 mis-handles (new/premium or old stock) would generate disproportionate negative signal. **Control:** per ISS-G03 there is no cohort gate — the control is the disclaimer + monitoring who the early users/GT sources are (self-selection, see RF-05). **Residual 🟡** (forward).
- **Public mis-valuation screenshot (→ RF-01).** A wildly-off estimate shared publicly. **Control:** range-lead + disclaimer + invite-only (limits blast radius). **Residual 🟡** (forward — see RF-01).

**Response.** **Monitor** + handle at the beta gate (cohort choice is the lever).

---

## 3.G — STRATEGIC, COMMERCIAL & ORGANIZATIONAL RISKS

### R17 — Key-person / bus-factor concentration (single PO, sole router, no succession)

> **Category** G · **Status** OPEN (structural) · **Inherent** 15🔴 (L3×I5) · **Residual** 12🟠 (L3×I4) · **Owner** PO · **Response** Reduce-partially + Accept · **Direction** → · **Cross-refs** R18, R1, R3, ISS-G06, ROLES_AND_COMMS · **First logged** 2026-06-09 (this register)

**Description & mechanism.** Thammen is a **single-founder** product: Anas is the sole Product Owner, the **sole gate authority** (Gate-1/Gate-2/Gate-3 + gates #6/#11), the **sole router** between the two AI lanes (Claude.ai ↔ CC), and holds all reserved methodology decisions (the ~0.31 floor, land + build-cost methodology, the beta go-call, the Aqarat timing). There is **no second human** — no co-founder, no succession, no redundancy for the decision and routing functions. If the founder is unavailable, the product **cannot progress** (no one can sign a gate or route the lanes) and key undocumented context could be lost.

**Causes.** The stage (a solo founder build) + the deliberate two-lane model that concentrates *all* human judgement in one person.

**Triggers / KRIs.** Founder unavailability (illness, competing demands, burnout); a single point of undocumented knowledge; the breadth of "reserved-to-Anas" decisions (a long list = a wide single-person bottleneck).

**Impact if it crystallises.** **Severe (I5):** total progress halt (no gate signer, no router) + potential loss of undocumented strategic context. At the *organizational* level this is the highest-impact structural risk; its likelihood is *Possible* (L3) over a 12-month horizon for a solo founder.

**Current controls.**
- *Corrective/Preventive (partial):* **git + docs are the durable single source of truth** (ISS-G06) — decisions, briefs, the risk/issue registers, the rules, and the session log are all on disk, so the *recorded* context survives; the two-lane model *forces* decisions to be written down (a brief, a signed gate, a §20.x log entry) rather than living only in the founder's head.
- *Detective:* the `#57`/`#58` handshake re-grounds any new session from the written state (so a *new* operator could in principle pick up from the docs).

**Residual exposure (12🟠).** The **knowledge** risk is *partially* reduced (the docs are good), but the **decision/routing** risk is **un-reduced** — no one else can sign a gate or route the lanes, and the reserved-decision list is broad. The controls preserve *context*, not *continuity of authority*.

**Response strategy & contingency.** **Reduce-partially** (keep the rigorous documentation; consider *narrowing or pre-delegating* some reserved decisions so fewer things block on one person — the "inform-don't-ask, deploy-on-green" delegation already does some of this) + **Accept** the irreducible solo-founder continuity risk as a cost of the stage. Contingency: the comprehensive docs (this register included) are precisely what would let a second person — or a future hire — resume; that is *why* the documentation discipline is treated as a control, not overhead.

**Dependencies.** None external; the lever is the founder's own choice about delegation breadth and documentation depth.

**«القرار المطلوب».** خطر بنيويّ — لا قرار عاجل، لكن فكّر في تضييق/تفويض بعض القرارات المحجوزة وفي توثيق السياق الحرِج (هذا السجلّ جزء من ذلك) كي لا يتوقّف كلّ شيء على شخص واحد.

### R-G (forward) — Commercial & competitive risks (pointer)

> **Category** G · **Status** FORWARD · **Owner** PO · **Cross-refs** RF-06/07/08/09 (monetization), RF-24/25/26 (competitive/strategic)

The commercial and competitive risks are **forward** (they become live at monetization / scale) and are detailed in Part 4: monetization-gated-on-licence (**RF-06**), professional liability (**RF-07**), unit-economics unproven (**RF-08**), regulated-reclassification-when-paid (**RF-09**), competitor entry (**RF-24**), no-data-moat / commoditization (**RF-25**), and strategic scope-creep / roadmap-drift (**RF-26**). They are flagged here so the strategic category is complete on the current register even though their *score* is at-horizon.

---

## 3.H — GOVERNANCE & PROCESS RISKS

### R1 — Cross-chat state divergence → near work-loss

> **Category** H · **Status** MITIGATED · **Inherent** 16🔴 (L4×I4) · **Residual** 6🟡 (L2×I3) · **Owner** PO/Claude.ai/CC · **Response** Reduce · **Direction** → · **Cross-refs** R3, R17, RF-28, Rule #57, Rule #43, ISS-T04 · **First logged** 2026-05-30, legacy 🟠

**Description & mechanism.** Work done in one Claude surface (commits, deploys, decisions) is **invisible** to another that trusts a stale brief/memory → risk of re-doing, overwriting, or "losing" committed work. A 2026-05-30 forensic pass was needed to confirm two commits were real and that origin was **98 commits behind** production.

**Causes.** Two AI lanes + memory + multiple sessions, none of which share live state automatically; a brief/memory can lag the actual git/Heroku state.

**Triggers / KRIs.** A session that routes work *without* a `#57` handshake; an origin↔production commit divergence; a memory claim that contradicts `/api/health`.

**Impact if it crystallises.** **Major (I4):** overwriting or losing committed work, or building on a stale assumption that has to be unwound.

**Current controls.** *Preventive/Detective:* Rule **#57** (session-start ground-truth handshake — `curl /api/health` + `git HEAD/reflog/origin-diff` before routing work; live state outranks memory); Rule **#43** (backup-push as part of the deploy ritual). *This register's own provenance discipline* (§0.2) is an instance of the control.

**Residual exposure (6🟡).** The handshake makes divergence *detectable* at every session start, which is what pulls the residual down — but the risk re-arises every time velocity tempts a skipped handshake (→ RF-28 at higher tempo).

**Response strategy & contingency.** **Reduce:** enforce #57 at every session start (non-negotiable). Contingency: a forensic read-only pass (as in 2026-05-30) reconstructs the true state from git + `/api/health`.

**Dependencies.** Discipline; interacts with R17 (the single router) and R3 (memory-disk drift).

**«القرار المطلوب».** لا قرار — مُخَفَّف؛ التزام #57 في كلّ بداية جلسة غير قابل للتفاوض.

### R3 — Memory-vs-disk operational gap

> **Category** H · **Status** MITIGATED · **Inherent** 12🟠 (L4×I3) · **Residual** 6🟡 (L2×I3) · **Owner** PO/Claude.ai · **Response** Reduce · **Direction** → · **Cross-refs** R1, R6, Rule #58, ISS-G01 · **First logged** 2026-05-30, legacy 🟠

**Description & mechanism.** CLAUDE.md / briefs / chat memory **drift** from the live code, git, and `/api/health`; numbers get *trusted* instead of *measured*. The governance pass found concrete drift: MoJ "139d" (doc) vs 150d (live); "VPS 4" (docs) vs the correct VPGA 10 + VPS 6 + IVS 106; a stale "current sprint" 4 sprints behind; a test-count delta.

**Causes.** Memory + docs are written once and age; live state moves with every sprint.

**Triggers / KRIs.** Any memory/brief number that diverges from a `/api/health` field (e.g. a version pin from memory — the recurring R6 pattern); a citation that doesn't match the primary source (Rule #54).

**Impact if it crystallises.** **Moderate (I3):** a decision or a user-facing claim is made on a stale number (a wrong version, a wrong staleness figure, a wrong standard citation).

**Current controls.** *Preventive:* Rule **#58** (assumed-vs-actual gap — measured wins, the gap is logged); **single-sourcing** critical numbers (the DoD count, the version) so they live in one place; this register's **measured✓/assumed~** tagging. Rule **#65a** makes `/api/health` + CLAUDE.md the single forward source.

**Residual exposure (6🟡).** The discipline catches drift *when applied*; the residual is the human/AI tendency to recite a remembered number without re-measuring (which is exactly the trap Rule #58 names).

**Response strategy & contingency.** **Reduce:** measure-first; single-source critical numbers; log every gap. Contingency: re-probe `/api/health` + re-read the corpus (as this register did).

**Dependencies.** Discipline; the `/api/health` endpoint as the live oracle.

**«القرار المطلوب».** لا قرار — مُخَفَّف؛ القاعدة #58 (المقيس يفوز) + توحيد مصدر الأرقام الحرِجة.

### R14 — Gate integrity (a push-gate report conflated REASONED with EXECUTED)

> **Category** H · **Status** MITIGATED (control adopted) · **Inherent** 9🟡 (L3×I3) · **Residual** 6🟡 (L2×I3) · **Owner** PO/CC · **Response** Reduce · **Direction** → · **Cross-refs** R1, all C-family controls, ISS-T05, Rule #14 · **First logged** 2026-06-02, legacy 🟠

**Description & mechanism.** A brief-MANDATORY pre-deploy check (mobile 390×844) was silently **downgraded** to post-deploy and assumed items were tagged as *measured* → **the gate did not actually gate**. The push-gate report also reported "59/59" when the broad suite was 58/59. Outcome was **benign** (post-hoc real verification passed), but the control failed.

**Causes.** The temptation to *reason* that a check would pass (`.rn`-reuse reasoning) instead of *executing* it; a count reported from memory rather than the run.

**Triggers / KRIs.** Any push-gate report that marks an item "verified" without an execution artifact; a brief-mandatory check deferred to post-deploy; a test count that doesn't match the actual run.

**Impact if it crystallises.** **Moderate (I3):** a real regression ships because the gate that should have caught it was satisfied by reasoning, not execution (this is the *meta-risk* that undermines every other C-family control).

**Current controls.** *Preventive (the adopted control):* "verified" in any push-gate report = **EXECUTED, not reasoned** — tag each item **done / worked-around / not-done**; a brief-mandatory check that cannot run at gate-time **BLOCKS** the push (downgrading it = an explicit PO waiver, never a Fast-lane substitution); briefs authored without the codebase mark code-level claims "CC verify in recon." This is Rule **#14**.

**Residual exposure (6🟡).** The control is adopted and has held since; the residual is recurrence under time pressure (the same human tendency that produced it). It is the control that keeps *all the other controls honest*, so its own integrity matters disproportionately.

**Response strategy & contingency.** **Reduce:** enforce verified=executed; require an execution artifact for every gate item. Contingency: a post-hoc real verification (as on a17) confirms or refutes a benign outcome.

**Dependencies.** Discipline; the test/CI harness as the execution evidence.

**«القرار المطلوب».** لا قرار — مُخَفَّف؛ «مُتحقَّق = مُنفَّذ» (Rule #14)، وأي فحص إلزاميّ لا يمكن تشغيله وقت البوّابة يوقِف الدفع ما لم تُعفِه صراحةً.

### R18 — AI-lane dependency & governance drift

> **Category** H (with strategic flavour) · **Status** OPEN · **Inherent** 12🟠 (L3×I4) · **Residual** 6🟡 (L2×I3) · **Owner** PO/Claude.ai · **Response** Reduce + Accept · **Direction** → · **Cross-refs** R1, R3, R17, RF-27, RF-28 · **First logged** 2026-06-09 (this register)

**Description & mechanism.** Both lanes (Claude.ai analyst + CC developer) depend on a **foundation model** plus a **large memory/instruction governance layer** (custom instructions, the rules register, the session log, the risk/issue registers). Two failure modes: (1) **dependency** — model deprecation / behaviour change / availability could disrupt the build-and-analysis pipeline; (2) **governance drift** — the model's "character," context, or adherence to the governance layer could degrade over long interactions (the standing concern that another instance or a senior reviewer would judge the character to have drifted from the constitution), or the governance layer itself could rot (framing-rot, stale priors — exactly what the 2026-06-09 cleanup addressed).

**Causes.** A single-vendor AI dependency for both lanes + a governance layer that is itself AI-mediated + long-horizon interactions that accumulate drift.

**Triggers / KRIs.** A model version change / deprecation; a session where the analyst recites a stale prior without re-grounding (R3); framing-rot in the docs (the "no-source / blocked" rot the cleanup fixed); a brief/copy that subtly contradicts a primary source (RF-27).

**Impact if it crystallises.** **Major (I4):** a degraded governance layer or a drifted lane could ship a subtly-wrong methodology or copy (RF-27), or the pipeline could be disrupted by a model change — affecting the *integrity* of everything the lanes produce.

**Current controls.** *Preventive/Detective:* the `#57`/`#58` handshakes (re-ground every session against measured state); the **frozen rules register** (#1–#65) as a stable governance anchor; **memory-hygiene** (the standing maintenance cadence — view/classify/update/delete/consolidate); the **two-lane separation** (the analyst's brief is reviewed by the PO before CC builds — a check on any single lane's drift); primary-source adjudication gating multi-AI (Rule #54).

**Residual exposure (6🟡).** The handshakes + frozen rules + PO review bound the drift, but the dependency on the vendor + the AI-mediated nature of the governance layer are **structural** (you cannot fully de-risk an AI dependency with AI controls). The 2026-06-09 cleanup is evidence the framing-rot risk is *real and recurring* — and that it *is* catchable.

**Response strategy & contingency.** **Reduce** (handshakes, frozen rules, memory hygiene, PO review, periodic doc cleanups) + **Accept** the irreducible single-vendor dependency. Contingency for a model change: the governance layer (docs + rules) is portable and re-grounds a new model; for governance drift: a periodic cleanup (as 2026-06-09) + the PO as the human backstop.

**Dependencies.** The vendor's roadmap (external); the discipline of the handshakes + cleanups.

**«القرار المطلوب».** لا قرار — مُدار بالمصافحات (#57/#58) + القواعد المجمّدة + نظافة الذاكرة + مراجعتك للبريفات؛ التنظيف الدوريّ (مثل 2026-06-09) ضابط مُثبَت الفاعليّة.

### R-H (monitored) — Two-lane coordination & doc-source-of-truth

> **Category** H · **Status** MONITOR · **Owner** PO · **Cross-refs** RF-28, ISS-G01/G05/G06, Rule #63/#65a

- **Two-lane coordination drift (→ RF-28).** The Claude.ai ↔ CC ↔ PO relay can accumulate drift faster than the handshake catches at higher tempo. **Control:** #57/#58 + the PO as the single router. **Residual 🟡** (rises with velocity — RF-28).
- **Doc source-of-truth drift (Rule #63 / #65a).** Claude.ai-authored docs must be saved to `docs/` by CC and committed, or git diverges from chat. **Control:** Rule #63 (same-message CC save+commit instruction) + #65a (single forward source). **Residual 🟢/🟡**; **KRI:** any analyst doc that lives only in chat (this register's own delivery includes the #63 instruction precisely to avoid this).
- **Memory-hygiene / framing-rot (ISS-G05 / G02).** Stale priors and "no-source" framing rot. **Control:** the standing memory-maintenance cadence + periodic cleanups. **Residual 🟡** (recurring — the cleanup is the recurring control).

**Response.** **Monitor** + keep the handshake/cleanup cadence; treat any chat-only analyst doc or any recited-stale-prior as a risk event.

---

# PART 4 — EMERGING & FUTURE RISKS (RF-), HORIZON-SCANNED

Forward risks are **not live today** but become material at a named horizon. Each is scored **at the horizon at which it activates** (not today), tagged **assumed~** (forward risks are inherently probabilistic), and carries the *current posture* (what, if anything, is already in place) plus the *treatment to stand up before the horizon*. They are ordered by horizon: **beta → monetization → apartments → scale → regulatory → market → competitive → AI → tail**.

> **How to read the scores.** "12🟠 @beta" means: *if/when the beta launches*, this risk scores L3×I4 over that phase. A forward risk's job is to be **converted into a current R-** (and re-scored) the moment its horizon is crossed.

## 4.1 — At BETA LAUNCH

### RF-01 — First public mis-valuation (R7 made visible)

> **Score @beta** 12🟠 (L3×I4) · **Owner** PO · **Response** Reduce · **Cross-refs** R7, R-F1, RF-05

A beta user shares a wildly-off estimate (R7's ±37/40%) publicly → the known bias becomes a *visible* credibility event. **Current posture:** invite-only (limits blast radius) + range-as-lead + the «تقدير آلي، ليس تقييماً معتمداً» disclaimer + MUC. **Treatment before beta:** ensure the range/MUC/disclaimer are on *every* surface a user could screenshot; brief the cohort that this is accuracy-research. **Contingency:** the disclaimer + range framing is the prepared response; a wrong number is "an indicative estimate we're calibrating," not "the value."

### RF-02 — Beta abuse / scraping / rate-limit evasion

> **Score @beta** 6🟡 (L3×I2) · **Owner** CC · **Response** Reduce · **Cross-refs** R-E, ISS-R06

The rate-limit is keyed on `cf-connecting-ip` (evadable via rotation) — a determined actor could scrape the engine or hammer it. **Current posture:** 5/s·30/min·200/h + CORS lock + invite-only (small surface). **Treatment:** monitor request patterns once live; the invite-only gate is the main limiter for the beta. **Contingency:** tighten Cloudflare (JS challenge) if abuse appears.

### RF-03 — Support & feedback-quality burden on a single PO

> **Score @beta** 6🟡 (L3×I2) · **Owner** PO · **Response** Reduce + Accept · **Cross-refs** R17, R19

The invite cohort generates feedback/support the **single founder** must triage (R17), and the *quality* of ground truth from self-reported beta feedback is uncertain (noisy condition/built-type self-reports). **Current posture:** the feedback UI is not yet wired (Sprint 2); cohort is small by design. **Treatment:** keep the cohort small enough for one person to absorb; design the feedback prompt to capture *structured* signal (not free text — also a privacy win, §8.1). **Contingency:** throttle invites if the burden exceeds capacity.

### RF-04 — PDPPL operational failure at first real captured data

> **Score @beta/capture** 10🟠 (L2×I5) · **Owner** PO→CC · **Response** Avoid-until-cleared · **Cross-refs** R11, R20, gate #11, §8.1/§8.2

The dormant capture is activated **before** §8.1 (fields/retention/consent) + §8.2 (residency) clear, or with the corrective controls (Fernet round-trip, short backups, erasure runbook) **designed but not executed** (Rule #14) → unlawful processing of personal data. **Current posture:** double-condition dormancy + a16 surface hardening (the strongest control is that there is *no live capture*). **Treatment before activation:** clear §8.1 + §8.2 + the CC security pass; **execute** the three corrective controls before any real data. **Contingency:** the erasure runbook; keep capture dormant until *all* of the above are executed.

### RF-05 — Cohort-selection bias skews the GT corpus

> **Score @beta** 6🟡 (L3×I2) · **Owner** PO · **Response** Reduce · **Cross-refs** R19, R7, ISS-G03

A cohort over-weighted to one market segment (new/premium *or* old stock) biases the ground-truth corpus R19 is meant to grow — and could *systematically* mislead R7 calibration (e.g. only old-stock feedback would tune the over-anchor fix but starve the under-anchor fix). **Current posture:** per ISS-G03 there is **no curated cohort and no gate** — GT grows manually + organically, so the bias is **self-selection** (who chooses to use it / which valuer reports arrive). **Treatment:** monitor the strata mix of incoming GT; supplement manually (curated valuer reports) toward the strata R7 needs (land-priced, aging, modern, luxury-new). **Contingency:** weight/stratify the corpus analytically if the mix skews.

## 4.2 — At MONETIZATION

### RF-06 — Aqarat licence is a hard gate before any paid access

> **Score @monetization** 15🔴 (L3×I5) · **Owner** PO · **Response** Avoid + Transfer · **Cross-refs** R13, RF-09, ISS-R01

Monetization is **gated on the Aqarat licence** (or a clear regulatory path) — التقييم العقاري is a named regulated activity; charging for it without a licence is the unlicensed-regulated-activity risk realised. If the licence is **denied or long-delayed**, the business model is **blocked entirely** (existential). **Current posture:** zero appetite for paid pre-licence (§0.5); the Aqarat enquiry is drafted + on HOLD for the right moment. **Treatment before monetization:** send the enquiry; obtain the licence or a written path; engage counsel. **Contingency:** stay free/research-only until cleared; do not cross the paid gate on optimism.

### RF-07 — Professional liability / indemnity for a relied-upon wrong number

> **Score @monetization** 15🔴 (L3×I5) · **Owner** PO · **Response** Transfer + Reduce · **Cross-refs** R7, R-F1, RF-06

A **paid** valuation invites **reliance**; a wrong number (R7's margin) on which a client relies → liability exposure that the disclaimed-beta posture does **not** cover (reliance ≠ "indicative research"). No professional-indemnity (PI) cover is noted. **Current posture:** the disclaimer protects the *free beta*, not a paid product. **Treatment before monetization:** PI insurance; a licensed-valuer-in-the-loop for any product that holds itself out as a valuation; contractual limitation-of-liability; the R7 fixes to reduce the *underlying* error. **Contingency:** keep paid output framed/limited and human-reviewed; do not sell an un-reviewed AVM point estimate as a valuation.

### RF-08 — Unit economics / pricing unproven

> **Score @monetization** 9🟡 (L3×I3) · **Owner** PO · **Response** Reduce · **Cross-refs** R16, RF-13

There is no validated willingness-to-pay, and the cost base (data-refresh dependency, infra scaling R16/RF-13, model/API costs) vs revenue is **untested**. **Current posture:** pre-revenue; monetization deferred behind the licence. **Treatment:** validate pricing with the beta cohort; model unit economics before committing to a paid build. **Contingency:** the free beta de-risks demand before cost is committed.

### RF-09 — Regulated-activity reclassification under a paid model

> **Score @monetization** 16🔴 (L4×I4) · **Owner** PO · **Response** Avoid · **Cross-refs** R13, RF-06

The **free-beta self-clearance (R13) does not extend to a paid model** — the regulatory posture changes *materially* when the product is sold. What is defensible as free, invite-only, disclaimed accuracy-research is a different question as a paid valuation service. This is the **highest-likelihood 🔴 forward risk** because the reclassification is *near-certain* to be material if money is introduced without the licence/path. **Current posture:** the self-clearance is explicitly scoped to the *free beta* (Honesty #10). **Treatment:** treat monetization as a **new** regulatory event — re-run the clearance, send the enquiry, obtain the licence/path *first*. **Contingency:** do not monetize until the regulatory question is *answered*, not assumed.

## 4.3 — At APARTMENT EXPANSION

### RF-10 — MME authentication dependency

> **Score @apartments** 6🟡 (L2×I3) · **Owner** PO/CC/EXT · **Response** Reduce · **Cross-refs** R21, ISS-D05

Apartments are **out of v1 scope, blocked on MME authentication** — an external integration gate. **Current posture:** apartments explicitly deferred; the engine refuses them cleanly. **Treatment before expansion:** the MME auth integration + a Heroku smoke test of the government endpoint (the §21.6 discipline) before building on it. **Contingency:** apartments stay out of scope until the auth + data are real (do not ship apartment valuations on incomplete data).

### RF-11 — Apartment valuation dynamics differ (new R7-class risks)

> **Score @apartments** 9🟡 (L3×I3) · **Owner** PO/CC · **Response** Reduce · **Cross-refs** R7, R8

Apartment value is driven by **strata, service charges, floor/view premiums, and yield** — dynamics the villa/land methodology does **not** capture. Porting the engine naively would create a *new* class of built-type/condition blindness (an R7 analogue for apartments). **Current posture:** deferred; the methodology is villa/land-specific. **Treatment:** a dedicated apartment methodology + recon + its own §5 audit + Gate-2 *before* shipping apartment valuations; tower-aware input handling already exists as a foundation (`unit_count` + `per_unit_rent`). **Contingency:** ship apartments disclosed-as-indicative with wide MUC, exactly as villas were.

### RF-12 — Apartment data sufficiency (the GT bottleneck, new asset class)

> **Score @apartments** 9🟡 (L3×I3) · **Owner** PO/EXT · **Response** Reduce · **Cross-refs** R19, R21

Confirmed apartment sales are scarce (the same R19 bottleneck, a new asset class), and MME apartment data has its own sufficiency thresholds (n≥10 indicative / ≥20 reliable). **Current posture:** deferred. **Treatment:** reach the n thresholds before any apartment reliability claim; grow the apartment GT via the same channels (valuer reports + organic). **Contingency:** disclosed-as-indicative until n≥20 per stratum.

## 4.4 — At SCALE

### RF-13 — Infrastructure scaling beyond the Eco dyno

> **Score @scale** 9🟡 (L3×I3) · **Owner** CC · **Response** Reduce · **Cross-refs** R16, RF-08

Concurrency beyond a single Eco dyno, the 30s timeout under load, and cold-start at volume all bite at scale (R16's escalation). **Current posture:** beta-grade single dyno; stateless-per-request design. **Treatment before scale:** redundant/larger dyno tier; managed Postgres (if capture is live); load testing against the 30s wall. **Contingency:** the stateless design scales horizontally cleanly once the tier is upgraded.

### RF-14 — Model-drift / recalibration debt

> **Score @scale** 12🟠 (L4×I3) · **Owner** CC · **Response** Reduce · **Cross-refs** R7, R8, R19, R4

As the GT corpus grows and the market moves, the calibration **must be re-run**, but there is **no automated recalibration pipeline** — drift accumulates silently (the cap-rate cells, the strata medians, the cost anchors all age). This is **Likely (L4)** at scale because recalibration is a *recurring* need with no current automation. **Current posture:** calibration is rebuilt manually per sprint (the `cap_rates.sqlite` swaps); `/api/health` exposes `calibration_freshness`. **Treatment:** a recalibration cadence/pipeline tied to MoJ refreshes + corpus growth; KRI alerts on `calibration_freshness.days_old`. **Contingency:** the freshness field + the manual rebuild keep it bounded until automated.

### RF-15 — GIS endpoint decommission / breaking schema change

> **Score @scale/anytime** 8🟡 (L2×I4) · **Owner** EXT · **Response** Reduce + plan · **Cross-refs** R5, R21

khazna/QARS is a **government endpoint outside our control**; a decommission or breaking schema/auth change halts address classification (R5's external escalation). **Current posture:** primary→legacy fallback + health monitor + the §21.6 smoke discipline for any new endpoint. **Treatment:** monitor `qars_endpoint`; keep the dual-endpoint fallback; treat any government-endpoint change with a smoke test first. **Contingency:** the address path refuses honestly on a total GIS outage rather than guessing.

### RF-16 — MoJ refresh-resumption shock

> **Score @MoJ-resumes** 12🟠 (L3×I4) · **Owner** EXT/CC · **Response** Reduce (the gate) · **Cross-refs** R4, R21

When MoJ resumes after a 160+-day freeze, a **large delta drop** hits the multi-factor adoption gate; a **bad or biased** drop (schema change, a registration-convention shift, a volume anomaly) could **silently shift every valuation** if adopted without scrutiny. **Current posture:** the multi-factor sanity gate (schema/NBSP/volume) is the control that *prevents silent adoption*. **Treatment at resumption:** run the gate; **diff every anchor** before adoption; check the registration-value convention hasn't shifted (RF-22). **Contingency:** do not adopt a drop that fails the gate or that moves the anchors inexplicably.

## 4.5 — REGULATORY EVOLUTION

### RF-17 — A dedicated AVM licensing category emerges

> **Score @horizon** 6🟡 (L2×I3, two-sided) · **Owner** PO/EXT · **Response** Monitor + adapt · **Cross-refs** R13, RF-06, ISS-R04

Qatar has **no dedicated AVM licensing category** today (an ambiguity, R-D). If the regime introduces one, it could be an **opportunity** (a clear, purpose-built path to licensure) **or** a **burden** (a costly new compliance requirement with capital/insurance/audit conditions). This is a *two-sided* risk — scored moderate because either outcome is *material but adaptable*. **Current posture:** monitor the Aqarat regime; the held enquiry is the probe that could surface this early. **Treatment:** maintain regulatory monitoring; design the product to be *licensable* (the alignment-not-certification discipline keeps the door open). **Contingency:** if a category emerges, the held enquiry + the methodology docs position Thammen to apply.

### RF-18 — RICS / IVS standard updates require a citation re-audit

> **Score @horizon** 6🟡 (L3×I2) · **Owner** Claude.ai/PO · **Response** Reduce · **Cross-refs** R-D, Rule #54, Appendix G

RICS/IVS standards are revised periodically; the **2025 renumbering already bit** (VPS 3→VPS 6, VPS 4→VPS 2, VPS 5 split, IVS 105→IVS 103) and required a primary-source re-audit (multi-AI "fixes" were *rejected* by primary-source adjudication). A future update would again require re-checking every citation in the live copy. **Current posture:** all six citation groups verified against primary sources; Rule #54 (web-check gates multi-AI on standards numbering). **Treatment:** re-audit citations on any announced RICS/IVS update; never trust a model's recollection of a standard number. **Contingency:** the citation map (Appendix G) is the checklist for a re-audit.

### RF-19 — PDPPL enforcement maturation outpaces the conservative self-clearance

> **Score @horizon** 9🟡 (L3×I3) · **Owner** PO · **Response** Reduce + Transfer-deferred · **Cross-refs** R11, R13, RF-04

Qatar's PDPPL enforcement is **maturing**; the conservative self-clearance (strict opt-in, 180-day retention, erasure, Qatar/GCC residency) that suffices today may become **insufficient** as guidance/enforcement tightens — especially once capture activates and real personal data is processed. **Current posture:** conservative self-clearance + dormant capture + a16 hardening. **Treatment:** track PDPPL guidance; at capture activation, re-validate against current enforcement expectations; engage counsel at the paid/scale gate. **Contingency:** the dormancy + the documented controls are the defensible baseline; tighten as guidance evolves.

### RF-20 — MoJ open-data licence change (away from CC BY 4.0)

> **Score @horizon** 10🟠 (L2×I5) · **Owner** EXT · **Response** Monitor + plan · **Cross-refs** R21, R13, ISS-D01

The product's legal basis for a *derivative, commercial* AVM rests on MoJ's **CC BY 4.0** licence (verified, attributed a25). If the publisher **changes the terms** (e.g. to non-commercial, or adds restrictions), the derivative-commercial basis could be **revoked** — striking at the data foundation *and* the monetization path. **Current posture:** the licence is verified CC BY 4.0 *today*; attribution is live. **Treatment:** monitor the open-data catalogue terms (the OpenDataSoft catalog API was the verification source); keep the verification current. **Contingency:** a licence change is an EXT event with no prevention — the plan is to re-assess the legal basis and, if needed, seek explicit permission or an alternative source (which interacts with RF-29).

## 4.6 — MARKET & MACRO

### RF-21 — Qatar real-estate cycle / price shock

> **Score @horizon** 9🟡 (L3×I3) · **Owner** EXT · **Response** Reduce-via-disclosure · **Cross-refs** R4, R8, RF-16

A market downturn or a **supply shock** (e.g. a Lusail-style inventory release — Huzoom Lusail's secondary speculation market is a live example) invalidates recent-window medians; the engine, anchored on historical MoJ data (already 160 days stale), **lags** a turning market. **Current posture:** the staleness banner + MUC communicate that the estimate is historical; LAND/HOUSE medians are window-stable (less whipsaw). **Treatment:** the MUC clause widens uncertainty in volatile conditions; the window logic (24mo→36mo→FULL) damps recency noise. **Contingency:** disclose more aggressively in a turning market; do not present a tight point estimate when the market is moving.

### RF-22 — MoJ registration-behaviour change

> **Score @horizon** 6🟡 (L2×I3) · **Owner** EXT · **Response** Monitor · **Cross-refs** R21, RF-16, E1

If MoJ **registration practices change** — e.g. registered values begin reflecting full transaction prices rather than the current convention — the **historical corpus becomes internally inconsistent** (old rows on one convention, new rows on another), silently biasing comparisons across the boundary. The under-registration hypothesis was *falsified* (E1: the villa asking-premium is stock composition, not under-registration), but a *future* convention shift is a different risk. **Current posture:** the multi-factor gate would catch a gross volume/schema anomaly, but a subtle convention shift might pass. **Treatment:** at each MoJ resumption, check the value distribution for a convention break (RF-16 discipline). **Contingency:** segment the corpus by convention era if a break is detected.

### RF-23 — Interest-rate / yield-environment shift

> **Score @horizon** 9🟡 (L3×I3) · **Owner** EXT · **Response** Reduce · **Cross-refs** R7 (income method), R8, RF-14

The income-triangulation method's **cap rates are calibrated to a yield environment** (villa net yields ~5–6% normal; the calibrated cells at specific brackets). A rate shock dislocates those yields, and the calibrated cap-rate cells become stale (a specific case of RF-14's recalibration debt). **Current posture:** net-yield benchmarks documented (5–6% normal, >6% worth inspecting, <4% weak); income method is bracket-gated + disclosed. **Treatment:** re-calibrate cap-rate cells when the rate environment moves; the `[land_floor, cost]` rail bounds an income figure built on a stale yield. **Contingency:** widen MUC on income-led figures in a moving-rate environment.

## 4.7 — COMPETITIVE & STRATEGIC

### RF-24 — Incumbent / bank in-house AVM or portal-operator entry

> **Score @horizon** 9🟡 (L3×I3) · **Owner** PO · **Response** Reduce (differentiate) · **Cross-refs** RF-25, R17

A well-funded competitor — a bank's in-house AVM, an incumbent valuer going digital, or a property-portal operator (PropertyFinder, dubizzle, etc.) leveraging **proprietary listing data + distribution** — could enter the same space. A portal operator in particular has *both* data and an audience Thammen lacks. **Current posture:** Thammen's edge is methodology rigour + RICS/IVS framing + transparency, not data exclusivity. **Treatment:** differentiate on *trustworthy methodology + honest uncertainty* (the things this register documents) rather than on data; move toward licensure (a moat a portal may not pursue). **Contingency:** a niche, rigorous, licensed AVM can coexist with a portal's rougher estimate.

### RF-25 — Data-source commoditization — no data moat

> **Score @horizon** 12🟠 (L4×I3) · **Owner** PO · **Response** Reduce (build a non-data moat) · **Cross-refs** RF-24, R21

MoJ open data is **available to anyone** (CC BY 4.0) — Thammen has **no data moat**. Any competitor can ingest the same source. This is **Likely (L4)** as a *standing* strategic condition (it is true *now*, not contingent). **Current posture:** the differentiation thesis is methodology + UX + trust + (future) licensure + the accumulated GT corpus (which *is* proprietary once it grows — R19's silver lining). **Treatment:** invest the moat in the things that *aren't* commoditized — the calibrated GT corpus, the methodology, the regulatory standing, the user trust. **Contingency:** accept that the *data* is commodity; compete on everything else.

### RF-26 — Strategic scope-creep / roadmap-drift

> **Score @horizon** 9🟡 (L3×I3) · **Owner** PO · **Response** Reduce · **Cross-refs** R7, R17, Gate-3, ISS-A07/U03

The project carries **many parked/deferred items** (B-2, §20.9 UP-lift, apartments, the final screens, monetization) and a single founder with finite attention (R17). The risk — *visible in this very session* — is **building polish over the core defect**: spending the next sprint on decomposition-coherence/presentation while R7's under-anchor half (the bigger risk) waits on a decision. **Current posture:** Gate-3 (flag-and-proceed beyond a signed brief) keeps scope visible; the forward sequences are documented. **Treatment:** prioritise by *risk reduction*, not by *readiness-to-sign* (Part 1.6 + Part 5.2 make this explicit); revisit the ordering at each sprint close. **Contingency:** this register is itself the corrective — it ranks the risks so attention follows exposure, not convenience.

## 4.8 — AI / MODEL-SPECIFIC (FORWARD)

### RF-27 — Hallucination in user-facing copy / methodology drift

> **Score @horizon** 9🟡 (L3×I3) · **Owner** Claude.ai/PO · **Response** Reduce · **Cross-refs** R18, R-D, Rule #54

An AI-authored brief, methodology note, or user-facing copy introduces a **subtly wrong claim** (a mis-stated standard number, an over-claimed compliance, an incorrect empirical) that **ships** — the governance layer is the control, but it is itself AI-mediated (R18). The 2025 RICS-renumbering near-miss (models proposed *wrong* "fixes") is the canonical example. **Current posture:** Gate-2 (PO reviews methodology/copy before build); Rule #54 (primary-source adjudication gates multi-AI on standards); the alignment-not-certification discipline. **Treatment:** PO review of every user-facing claim; primary-source check for every standard/empirical citation; never ship a model's recollection of a regulated fact unverified. **Contingency:** the citation map + the self-clearance docs are the verification baselines.

### RF-28 — Two-lane coordination failure at higher tempo

> **Score @horizon** 9🟡 (L3×I3) · **Owner** PO · **Response** Reduce · **Cross-refs** R1, R3, R18, R-H, Rule #57/#58

As velocity increases, the **Claude.ai ↔ CC ↔ PO relay** accumulates drift faster than the #57/#58 handshake catches — a stale brief, a divergent commit, a memory recited instead of measured (the R1/R3 failure modes, amplified). **Current posture:** #57/#58 handshakes + the PO as the single router + git/docs as truth. **Treatment:** never skip the handshake under time pressure (the temptation *is* the risk); single-source critical numbers; keep the cadence of one-complete-unit-per-sprint (Rule #64) so drift can't outrun verification. **Contingency:** a forensic read-only re-grounding (as 2026-05-30) reconstructs truth from git + `/api/health`.

## 4.9 — TAIL / BLACK-SWAN

### RF-29 — MoJ permanently dark

> **Score (tail)** 10🟠 (L2×I5) · **Owner** EXT · **Response** Plan (contingency) · **Cross-refs** R4, R21, RF-20

The 160-day freeze **never resolves** — the publisher discontinues the weekly bulletin and the corpus **ages out of relevance** entirely. Low likelihood (Qatar open-data has been stable), severe impact (the *only* evidence source goes permanently stale). **Current posture:** none can *prevent* this (EXT); the corpus is usable while the market is slow. **Treatment (plan, not control):** the contingency is to explore an **alternative transaction source** — developer data (T3, surviving as an independent channel), a future MME/registry feed, or a licensed data agreement — none currently viable, hence a *plan* to activate **only** if this tail crystallises. **Contingency:** disclose the freeze ever more prominently as it ages; explore alternatives if it passes ~1 year.

### RF-30 — Regulator action / cease-and-desist on the free tool

> **Score (tail)** 10🟠 (L2×I5) · **Owner** PO/EXT · **Response** Plan + Reduce · **Cross-refs** R13, RF-06, RF-09

A regulator orders the **free tool** down despite the disclaimed, research-only posture — the government "المثمّن العقاري" approximate-estimate precedent cuts *both* ways (it shows a free estimate tool is tolerated, but also that the state operates in this space). Low likelihood for a clearly-disclaimed free beta, severe impact (forced shutdown). **Current posture:** free + invite-only + disclaimed + the self-clearance doc + the held Aqarat enquiry. **Treatment:** the conservative posture *is* the reduction; the held enquiry is the prepared engagement. **Contingency:** the tool can be paused if ordered; the enquiry draft + self-clearance doc are the prepared response to a regulator query.

### RF-31 — Catastrophic data / security breach (activated capture)

> **Score (at capture activation)** 10🟠 (L2×I5) · **Owner** CC/PO · **Response** Reduce + plan · **Cross-refs** R11, RF-04, a16

Once capture activates, the personal-data store is a **breach surface** — a breach would trigger PDPPL obligations + reputational damage. **The strongest control is that capture is dormant — there is no PII store to breach today.** Low likelihood (small surface, hardened), severe impact (regulated personal data). **Current posture:** dormant capture; a16 hardening (UUID-only key, Fernet-encrypted street/building, no free-text note, 180-day retention/purge/erase). **Treatment before activation:** the Fernet round-trip verified on Heroku, short backup retention, the breach/erasure runbook — all *executed* (Rule #14). **Contingency:** the erasure + backup runbook; breach-notification per PDPPL; keep the surface minimal (the a16 hardening is precisely this).

---

**Forward-risk summary.** The forward register's centre of gravity is **monetization** (RF-06/07/09 all 🔴-at-horizon) and the **standing strategic conditions** (RF-25 no-data-moat 🟠, RF-26 scope-creep 🟡, RF-14 recalibration-debt 🟠). The tail risks (RF-29/30/31) are *contingency-planned, not prevented* — low likelihood, severe impact, EXT or activation-gated. The single most important forward discipline is **not crossing the monetization gate without converting RF-06/07/09 from "assumed-defensible" to "answered."**

---

# PART 5 — RISK TREATMENT & ACTION PLAN

## 5.1 Treatment plan for the top residual risks

Each top risk's treatment, owner, dependency, and the *order* that maximises risk reduction (not readiness-to-sign):

| # | Risk | Treatment (the move that lowers it) | Owner | Blocked on | Effect |
|---|---|---|---|---|---|
| 1 | **R7** under-anchor half | §20.9 **convergence + UP-lift** (lift new/premium villas) | CC | **PO ~0.31 floor** + CGIS-vs-actual age recon | Closes the untreated −37/40% direction |
| 2 | *(removed — errata)* | The "A16/R9 root fix" row is void: a18 already shipped the pool fix (§20.18); the over-anchor residual is condition → rows 1 & 5 | — | — | No separate root sprint exists |
| 3 | **R20** measurement | **Activate capture** (with a16 hardening + executed controls) | CC | **PO §8.1 + §8.2** + CC security pass (gate #11) | Turns on the error gauge; enables evidence-based R7 work |
| 4 | **R19** corpus | **Start the GT-collection track** (manual valuer reports + organic use — beta as a parallel non-blocking track, ISS-G03) | PO | PO start-call (no cohort gate) | Grows GT toward n≥20; unblocks B-2 + accuracy claims |
| 5 | **R7** durable fix | **B-2 condition axis** (bidirectional, the real fix) | CC | **n≥20 GT** (R19) — PARKED | The durable two-direction correction |
| 6 | **R17** key-person | Narrow/pre-delegate reserved decisions; keep docs current | PO | PO choice | Reduces the continuity bottleneck |
| 7 | **R13→RF-06/09** | Send Aqarat enquiry **before** monetization; counsel + PI at paid | PO | PO timing | Keeps the monetization gate from being crossed blind |

**The ordering logic.** Moves **1 and 3** are the highest-leverage because they attack the **untreated** halves of the two top risks (R7-under and R20-measurement) and are each blocked on a **PO decision**, not on external supply. Move **4** (beta) is the *force-multiplier* — it improves R19 *and* R20 *and* feeds the data that unblocks move 5. The presentation work (decomposition-coherence, the final screens) is **not** in this top-risk treatment table — it improves R-F1 (authority) modestly but does **not** reduce the top of the register (see Part 1.6).

## 5.2 PO-decision register (consolidated «القرار المطلوب»)

Every risk whose treatment is **blocked on an Anas decision**, in one place. This is the register's most actionable output for the PO.

| Decision | Unlocks (risk treatment) | Risk(s) reduced | Reserved? | Note |
|---|---|---|---|---|
| **D-1 · ~0.31 dilapidated-luxury floor coefficient** | §20.9 convergence + UP-lift | **R7** (under-anchor half) | **Yes — PO methodology** | The single highest-leverage lever the PO personally holds; the under-anchor half has **zero** current mitigation |
| **D-2 · §8.1 (capture fields/retention/consent) + §8.2 (cross-border residency)** | Activate capture / measurement | **R20**, **R11**, RF-04 | **Yes — PO + counsel** | Turns on the accuracy gauge; do **not** activate before both clear + the CC security pass |
| **D-3 · Beta launch posture (start GT collection)** | Manual + organic GT feed + early measurement | **R19**, R20, RF-05 | PO call | Per the 2026-06-09 cleanup (ISS-G03) the beta is a **parallel non-blocking track — the cohort gate (#6) was deleted**; note CLAUDE.md #65a still names gate #6 → one-line reconciliation owed (R-H) |
| **D-4 · (سقط — errata)** was "approve a live Marikh trace → A16/R9 root brief" | Nothing — R9 closed at a18 (§20.18) | — | — | Optional only: the a18 fast-follow live sub-zone demo (معيذر/نعيجة) — low priority, no gate |
| **D-5 · Aqarat enquiry timing** | Regulatory path before monetization | R13, **RF-06/07/09** | **Yes — PO** | Send post-design, pre-monetization; the monetization gate must not be crossed blind |
| **D-6 · Decomposition-coherence brief signature (Gate-2)** | Final screens (4–5) | R-F1 (modest) | **Yes — Gate-2** | Presentation/credibility, value-invariant; lower risk-reduction than D-1/D-2 — sequence accordingly |

> **The honest priority signal for the PO.** From a pure risk-reduction standpoint the ranking of *your* decisions is **D-1 ≈ D-2 > D-3 > D-5 > D-6** (D-4 dropped — its premise closed at a18). D-6 (the decomposition-coherence brief) is the one currently described as "ready to sign," but it reduces the *least* exposure on this list — it is a presentation/authority improvement, not an accuracy or measurement fix. D-1 and D-2 are the moves that lower the **top** of this register.

## 5.3 Risk-control roadmap (which controls ship when)

| Phase | Controls to stand up | Risks addressed |
|---|---|---|
| **Now (pre-beta)** | §20.9 GATED slice (after D-1); purity *diagnostic* as disclosure; optional a18 fast-follow live sub-zone demo; keep range-lead + MUC + disclaimers | R7, R8, R-F1 |
| **At beta launch** | Activate capture *with* executed a16 controls (after D-2); structured (not free-text) feedback; cohort spanning R7 strata; abuse monitoring | R20, R19, RF-02/04/05 |
| **Pre-monetization** | Aqarat enquiry sent + path obtained; PI insurance; licensed-valuer-in-loop for any held-out valuation; re-run clearance for paid | R13, RF-06/07/09 |
| **Pre-scale** | Redundant/larger dyno tier; managed Postgres; load test vs 30s wall; recalibration cadence/pipeline | R16, RF-13/14 |
| **Standing** | #57/#58 handshakes; memory hygiene; periodic doc cleanups; citation re-audit on RICS/IVS updates; MoJ adoption-gate at every resumption | R1, R3, R18, R-D, R-H, RF-16/18/28 |

## 5.4 Key Risk Indicators (KRIs) — tied to the live oracle

KRIs are checked at every `#57` handshake. Each names its **source**, its **green/amber/red threshold**, and the **risk it tracks**. Most are already exposed by `GET /api/health`.

| KRI | Source | 🟢 Green | 🟡 Amber | 🔴 Red | Tracks |
|---|---|---|---|---|---|
| **MoJ freshness** | `/api/health` `moj_freshness.days_old` | < 90 | 90–365 (**160 today**) | > 365 | R4, RF-29 |
| **Calibration fallback share** | `by_confidence.fallback / total` | < 50% | 50–90% | > 90% (**92% today**) | R19 |
| **Reliable-cell count** | `by_confidence.reliable` | > 50 | 5–50 (**6 today**) | < 5 | R19 |
| **QARS endpoint** | `qars_endpoint.status` | healthy (**today**) | degraded | down | R5, RF-15 |
| **QARS primary↔legacy delta** | `primary_count` vs `legacy_count` | ≤ ±1 (**today**) | small | large/divergent | R5 |
| **Capture state** | `DATABASE_URL` + flag | dormant (**today**) | — | activated-without-D-2 | R11, RF-04, R20 (inverted) |
| **Prediction↔outcome pairs** | capture table (when live) | growing toward n≥20 | single digits (**today**) | none | R19, R20 |
| **Dispersion gate** | per-cell `(p75−p25)/median` | < 0.30 clean | ≥ 0.30 (gated) | ungated dispersed cell | R7, R8, E23 |
| **Under-anchor signal** | `VALIDATION_LOG` confirmed sale vs engine | within MUC | 10–25% under | > 25% under (**−37/40% measured**) | R7 |
| **Anchor drift** | the 4 value-invariant anchors | byte-identical | — | any drift post-deploy | R1, R6, deploy integrity |
| **Security posture** | `security.cors_locked` / `docs_locked` / rate_limits | all locked (**today**) | — | any unlocked | R-E, RF-02 |
| **Origin↔production** | `git HEAD` vs Heroku release | in sync | behind | far behind (was **98**) | R1, RF-28 |

> **What the KRIs say *today* (measured✓):** MoJ freshness **amber** (160d, trending toward red as the freeze persists); calibration fallback **red** (92%) and reliable-cell **amber** (6) — both R19 signals confirming the corpus is the binding constraint; QARS **green**; capture **green-dormant** (which is *also* the R20 red — the measurement gauge is off); security **green**. The KRI dashboard corroborates Part 1's reading: the *data/measurement foundation* (R19/R20) is the amber/red zone, not the infrastructure.

## 5.5 Escalation & review cadence

- **Per `#57` handshake:** check the KRI table; log any amber→red transition as a risk event.
- **Per sprint close-out:** re-score every risk a sprint touched; close resolved risks with date + evidence (never delete); add any new risk the sprint surfaced.
- **Per stage-gate (beta / monetization / apartments / scale):** full re-score; convert the relevant forward RF- risks into current R- risks and re-score them at "live."
- **Escalation:** any residual 🔴, or any risk whose treatment is blocked on a PO decision, is surfaced in-chat with a **«القرار المطلوب»** and carried in Part 5.2 until decided.
- **Owner of the register:** Anas (PO), maintained by the Claude.ai analyst lane; canonicalised to `docs/` via Rule #63 (see the closing note).

---

# PART 6 — CLOSED / RETIRED / ACCEPTED RISKS

Closed risks are **kept, not deleted** (the legacy register's discipline) — a closed risk is evidence the control worked, and a guard against the failure mode silently returning.

## 6.1 Closed (resolved, with date + evidence)

| ID | Risk | Closed | Evidence | Residual watch |
|---|---|---|---|---|
| **R2** | A14 villa cold-503 (warm ~21s vs 30s wall → cold first-try 503) | 2026-05-30 (Heroku v146) | Parallelised `geometric_factors` internals; post-deploy live: 56/565/21 cold 200@14.4s + 15.0s, 56/647/6 200@15.9s — all <30s, ~15s margin, zero 503; byte-identical | If the margin regresses, Lever 1 (overlap) is ready; **KRI:** cold-start latency vs 30s |
| **R6** | Brittle EXACT-version-pin tests (red on every later sprint) | 2026-05-30 (Sprint A14) | 2 pins loosened to version-agnostic FORMAT checks → broad 50/50 (was 48/49); recurred + fixed again in a8 | **KRI:** the pattern recurring in new test files — watch on every new test |
| **R10** | Bracket-SUCCESS path had no dispersion gate | 2026-06-01 (Sprint a14, Heroku v153) | a14 `comparison_bracket` branch in `_stage1_dispersion_gate` (range-headline + 🟡 indicative + MUC + disclosure; presentation-only); 20/37 reliable villa cells dispersed ≥0.30 now gated | **BOUNDARY:** 3 cells within ±0.006 of T=0.30 may flip on a MoJ refresh — expected, not a regression (hysteresis if it bites) |
| **R9** | Bracket-path area-name under-match (A16) — *errata: closed earlier than this register first recorded* | 2026-06-03 (Sprint a18, Heroku v157, `d69d9c0`) | `area_match_key` sibling-aggregation wired into `build_reference` + `compute_trend` + the امريخ الجنوبي→مريخ override; live Marikh → comparison_thin 5.4M n=15 same-district (§20.18) | Residual: unreachable-name class ~0.25% (فريج العسيري / المطار) + the optional fast-follow live sub-zone demo; legacy register row still reads OPEN → one-line closure owed |
| **R15** | `stock_strata.compute_land_median` not a18-aware → land-median divergence | 2026-06-04 (Sprint a23, Heroku v162, `ff483b0`) | `compute_land_median` now pools via `area_match_key`; المعمورة strata land 4,032→3,754 (≈ floor 3,768); headline + value_floor byte-identical; blast radius = strata-card DISPLAY only | The a12 `compute_trend` categorizer-alignment remains the open sibling of this family |

## 6.2 Accepted risks (consciously held at PO level, with rationale)

| ID | Risk | Why accepted | Re-open trigger |
|---|---|---|---|
| **R16** | Infra SPOF (single Eco dyno) | Beta-grade availability is appropriate pre-revenue; the app is stateless-per-request so an outage is clean unavailability, not data loss | Monetization or scale (→ RF-13) — then it must be reduced |
| **R21** | MoJ single-source dependency | No alternative truth source exists at comparable quality; the under-registration hypothesis is falsified; managed by the adoption gate + licence verification | A schema change (RF-16), licence change (RF-20), or permanent-dark (RF-29) |
| **R17** | Solo-founder continuity (the irreducible part) | The decision/routing function cannot be redundant in a solo build; the *knowledge* part is mitigated by rigorous docs | A move to add a co-founder/hire, or a founder-availability event |
| **R13** | Regulated-activity exposure (the beta part) | Managed by free + invite-only + disclaimed + held enquiry + self-clearance doc; the residual is acceptable *for a free beta only* | **Monetization** — the acceptance does **not** extend to paid (→ RF-06/09) |

## 6.3 Failed-path risks (tried, abandoned — now moot, kept for memory)

| Item | What it was | Why it's moot | Lesson retained |
|---|---|---|---|
| **Confirmed-Sales-DB (2.16.16)** | A planned internal confirmed-sales source | Dropped — no viable feed; survives only as the GT-corpus *concept* (R19) fed by valuer reports + beta | Don't gate accuracy on a source that doesn't exist; ship disclosed-as-indicative (§0.4) |
| **MoJ self-calibration (E12 blocked)** | Calibrating the engine to MoJ medians | Blocked — would re-import the very bias being corrected (the R22 trap, generalised) | Independence matters: don't calibrate a corrective method to the biased source |
| **Land-to-median "bidirectional trap"** | A rejected range-as-lead framing | Rejected — thin paths put the median at the high edge; a symmetric ± invents refused upside (b3 recon falsified it) | Verify framing against real path behaviour (R14: verified=executed), don't reason it |
| **"Widened-only / over-anchor-only" R7 framing** | The original narrow R7 description | Superseded — R7 is bidirectional, both paths (generalised 2026-05-31; V002/V003 confirmed the under-anchor) | A defect's framing is a hypothesis; confirmed sales are the test |
| **Stage-1 input-honesty sprint** | A planned input-honesty premise | Premise falsified (CHANGELOG_v78 / §20.26) | A recon can kill a premise before code — that's the recon working |

---

# PART 7 — APPENDICES

## Appendix A — Risk-ID crosswalk

Maps the canonical `RISK_REGISTER.md` IDs, this register's entries, and the related `ISSUES_LOG.md` items (defects/work-items). A risk and an issue are **not** the same: an issue is a thing to *fix*; a risk is an uncertainty to *manage*. Many risks have an issue as their *evidence* or their *fix*.

| This register | Legacy `RISK_REGISTER.md` | Related `ISSUES_LOG` | Category | Residual |
|---|---|---|---|---|
| R1 | R1 (cross-chat divergence) | ISS-T04 | H | 6🟡 |
| R2 | R2 (cold-503) ✅ | — | C | CLOSED |
| R3 | R3 (memory-disk gap) | ISS-G01 | H | 6🟡 |
| R4 | R4 (MoJ stale) | ISS-D01 | B | 6🟡 |
| R5 | R5 (QARS reachability) | ISS-T01 | C | 6🟡 |
| R6 | R6 (version-pin tests) ✅ | — | C | CLOSED |
| R7 | R7 (built-type/condition) | ISS-A01 | A | 12🟠 |
| R8 | R8 (purity/thin-window) | DEF-02 | A | 9🟡 |
| R9 | R9 (A16 area-name) ✅ | ISS-A03, ISS-B03 | A | CLOSED (a18) |
| R10 | R10 (bracket dispersion) ✅ | — | A | CLOSED |
| R11 | R11 (capture dormant) | ISS-R05 | E | 4🟢 |
| R12 | R12 (Cloudflare 1010) | ISS-T03 | C | 4🟢 |
| R13 | R13 (regulatory self-clearance) | ISS-R01 | D | 8🟡 |
| R14 | R14 (gate integrity) | ISS-T05 | H | 6🟡 |
| R15 | R15 (strata land median) ✅ | — | B | CLOSED |
| **R16** | *(new)* | ISS-T02, ISS-T07 | C | 9🟡 |
| **R17** | *(new)* | ISS-G06 | G | 12🟠 |
| **R18** | *(new)* | ISS-G02, ISS-G05 | H | 6🟡 |
| **R19** | *(new)* | ISS-D07 | B | 12🟠 |
| **R20** | *(new)* | ISS-D08 | B | 12🟠 |
| **R21** | *(new)* | ISS-D01 | B | 12🟠 |
| **R22** | *(new)* | ISS-A04 | A | 6🟡 |
| RF-01..31 | *(new — forward)* | ISS-U03/U05, ISS-R01/R04/R06, ISS-D05 | RF | at-horizon |

## Appendix B — Likelihood / Impact rubric (anchored)

**Likelihood anchors (over the scoring horizon):**

| L | Probability | Concrete anchor for this project |
|---|---|---|
| 1 Rare | <10% | A simultaneous primary+legacy QARS outage; the MoJ licence being revoked this year |
| 2 Unlikely | 10–30% | A regulator query on a disclaimed free beta; activating capture prematurely (a deliberate two-step that gate #11 guards) |
| 3 Possible | 30–55% | A solo-founder availability event over 12 months; a competitor entering; a market turn |
| 4 Likely | 55–80% | A new code path forgetting a hygiene control; recalibration debt accruing at scale; R7 mis-anchoring a non-average property |
| 5 Almost certain | >80% | The MoJ data being stale (it *is*); the corpus being n<20 (it *is*); 92% of cells being fallback (they *are*) |

**Impact anchors (the dimension that sets the score):**

| I | Anchor |
|---|---|
| 1 Negligible | A value move within the MUC band; a cosmetic display gap |
| 2 Minor | One surface mildly off; a few users notice; hours to fix |
| 3 Moderate | A *cohort* systematically off; a compliance gap to close; days + manual workaround |
| 4 Major | The headline materially wrong for a *large share*; unlicensed-activity exposure; blocks monetization |
| 5 Severe | The engine systematically untrustworthy; cease-and-desist/enforcement; data loss; existential to the model |

## Appendix C — Full risk matrix (all risks, scored)

**Current risks (R-) — inherent → residual:**

| ID | Risk | Cat | Inherent | Residual | Trend | Status |
|---|---|---|---|---|---|---|
| R7 | Built-type/condition bidirectional | A | 20🔴 | 12🟠 | → | OPEN |
| R17 | Key-person / bus-factor | G | 15🔴 | 12🟠 | → | OPEN |
| R19 | GT corpus scarcity | B | 15🔴 | 12🟠 | ↓ | OPEN |
| R20 | No live accuracy measurement | B | 15🔴 | 12🟠 | ↓ | OPEN |
| R21 | MoJ single-source dependency | B | 12🟠 | 12🟠 | → | ACCEPTED |
| R13 | Regulated-activity self-clearance | D | 15🔴 | 8🟡 | →(↑$) | OPEN |
| R8 | Pool purity / thin-window | A | 12🟠 | 9🟡 | → | PARKED |
| R9 | Area-name under-match (A16) | A | 12🟠 | — | — | CLOSED (a18) |
| R16 | Infra SPOF | C | 9🟡 | 9🟡 | →(↑scale) | ACCEPTED |
| R1 | Cross-chat divergence | H | 16🔴 | 6🟡 | → | MITIGATED |
| R3 | Memory-disk gap | H | 12🟠 | 6🟡 | → | MITIGATED |
| R4 | MoJ stale | B | 12🟠 | 6🟡 | →(↑) | OPEN |
| R5 | QARS reachability | C | 12🟠 | 6🟡 | → | MITIGATED |
| R14 | Gate integrity | H | 9🟡 | 6🟡 | → | MITIGATED |
| R18 | AI-lane dependency / drift | H | 12🟠 | 6🟡 | → | OPEN |
| R22 | DRC calibration-bias import | A | 9🟡 | 6🟡 | → | OPEN |
| R11 | Capture dormant | E | 12🟠 | 4🟢 | →(↑activation) | OPEN |
| R12 | Cloudflare 1010 CC-smoke | C | 6🟡 | 4🟢 | → | MITIGATED |
| R2 | Cold-503 | C | 12🟠 | — | — | CLOSED |
| R6 | Version-pin tests | C | 9🟡 | — | — | CLOSED |
| R10 | Bracket dispersion gate | A | 12🟠 | — | — | CLOSED |
| R15 | Strata land median | B | 9🟡 | — | — | CLOSED |

**Forward risks (RF-) — scored at-horizon:**

| ID | Risk | Horizon | Score | Response |
|---|---|---|---|---|
| RF-09 | Regulated reclassification when paid | Monetization | 16🔴 | Avoid |
| RF-06 | Aqarat licence hard gate | Monetization | 15🔴 | Avoid+Transfer |
| RF-07 | Professional liability / PI | Monetization | 15🔴 | Transfer+Reduce |
| RF-25 | No data moat / commoditization | Now→scale | 12🟠 | Reduce (non-data moat) |
| RF-14 | Model-drift / recalibration debt | Scale | 12🟠 | Reduce |
| RF-01 | First public mis-valuation | Beta | 12🟠 | Reduce |
| RF-16 | MoJ refresh shock | MoJ resumes | 12🟠 | Reduce (gate) |
| RF-04 | PDPPL operational failure | Beta/capture | 10🟠 | Avoid-until-cleared |
| RF-20 | MoJ licence change | Regulatory | 10🟠 | Monitor+plan |
| RF-29 | MoJ permanently dark | Tail | 10🟠 | Plan |
| RF-30 | Cease-and-desist (free tool) | Tail | 10🟠 | Plan+Reduce |
| RF-31 | Capture breach | At activation | 10🟠 | Reduce+plan |
| RF-08 | Unit economics unproven | Monetization | 9🟡 | Reduce |
| RF-11 | Apartment dynamics differ | Apartments | 9🟡 | Reduce |
| RF-12 | Apartment data sufficiency | Apartments | 9🟡 | Reduce |
| RF-13 | Infra scaling | Scale | 9🟡 | Reduce |
| RF-19 | PDPPL enforcement maturation | Regulatory | 9🟡 | Reduce |
| RF-21 | Market / price shock | Market | 9🟡 | Reduce-disclose |
| RF-23 | Interest-rate / yield shift | Market | 9🟡 | Reduce |
| RF-24 | Competitor / portal entry | Competitive | 9🟡 | Reduce |
| RF-26 | Scope-creep / roadmap-drift | Strategic | 9🟡 | Reduce |
| RF-27 | Hallucination in user-facing copy | AI | 9🟡 | Reduce |
| RF-28 | Two-lane coordination failure | AI | 9🟡 | Reduce |
| RF-15 | GIS endpoint decommission | Scale/anytime | 8🟡 | Reduce+plan |
| RF-02 | Beta abuse / scraping | Beta | 6🟡 | Reduce |
| RF-03 | Support / feedback burden | Beta | 6🟡 | Reduce+Accept |
| RF-05 | Cohort-selection bias | Beta | 6🟡 | Reduce |
| RF-10 | MME authentication | Apartments | 6🟡 | Reduce |
| RF-17 | AVM licensing category emerges | Regulatory | 6🟡 | Monitor+adapt |
| RF-18 | RICS/IVS citation re-audit | Regulatory | 6🟡 | Reduce |
| RF-22 | MoJ registration-behaviour change | Market | 6🟡 | Monitor |

## Appendix D — Controls catalog (control → risks mitigated)

| Control | Type | Risks mitigated |
|---|---|---|
| Rule #57 ground-truth handshake (`/api/health` + git) | Detective/Preventive | R1, R3, RF-28 |
| Rule #58 assumed-vs-actual (measured wins) | Preventive | R3, R18 |
| Rule #43 backup-push in the deploy ritual | Corrective | R1 |
| Rule #14 verified=executed (no paper-control credit) | Preventive | R14, R11, RF-04 (the meta-control) |
| Hard Gate-1 (push consent) | Preventive | All C-family, deploy-regression |
| Hard Gate-2 (methodology/UX sign-off pre-build) | Preventive | R7, R-F1, RF-27 (A/F-family) |
| Hard Gate-3 (scope flag-and-proceed) | Detective | RF-26 |
| gate #6 (cohort) — *deleted 2026-06-09 (ISS-G03)* | Historical | RF-05 reframed to self-selection monitoring |
| gate #11 (capture activation) | Preventive | R11, R20(inv), RF-04, RF-31 |
| a10/a14 dispersion gate | Preventive/Detective | R7, R8, R10(closed) |
| `if land_value > valuation_amount: return None` (Patch C) | Preventive | decomposition coherence, MoJ outliers, teardowns |
| b11 §20.9 cost-reanchor down-half (cost-as-floor) | Corrective | R7 (over-anchor), R22 |
| Range-as-lead headline (b3) | Preventive | R-F1, RF-01 |
| Evidence-quality panel + "explanation≠confidence" (b2.2/§2c) | Preventive | R-F1 |
| Confirmation gate + staged authority (b2.3) | Preventive | R-F1 |
| MUC clause (VPGA 10) | Corrective | R4, R7, R-F1, RF-21/23 |
| Staleness banner (Sprint 2.7) | Detective | R4 |
| MoJ multi-factor adoption gate | Detective/Preventive | RF-16, R21, RF-22 |
| MoJ NBSP/whitespace normalisation | Preventive | R-B, R9 (closed) |
| `area_match_key` / hamza-fold + a18 sibling-aggregation | Preventive | R-B; **R9 (closed by this control at a18** — wired into `build_reference` + `compute_trend`) |
| `_qars_query` primary→legacy fallback (Rule #11) | Corrective | R5, RF-15 |
| E7 QARS-subtype × Zoning cross-check | Preventive | R5 (stale-subtype variant) |
| ≤10s fetch budget + parallelised GIS I/O | Preventive | R2(closed), R16, RF-13 |
| Stateless-per-request design | Preventive | R16, RF-13 |
| Rule #61 browser-UA POST smoke | Corrective | R12 |
| a16 capture hardening (UUID-only, Fernet, no note, 180d) | Preventive | R11, RF-31, RF-04 |
| a24 §4 address log-scrub + DPIA | Preventive | R-E (privacy) |
| Disclaimer «تقدير آلي، ليس تقييماً معتمداً» | Preventive | R13, R-F1, RF-01, RF-30 |
| Self-clearance doc + held Aqarat enquiry | Corrective/Transfer-deferred | R13, RF-06, RF-30 |
| CC BY 4.0 verification + attribution (a25) | Corrective | R13 (licence sub-item), RF-20 |
| Rule #54 primary-source gates multi-AI | Preventive | R-D, RF-18, RF-27 |
| Ship-disclosed-as-indicative principle (§0.4) | Corrective | R7, R19 (disclosure dimension) |
| `[land_floor, cost]` rail | Preventive | R7, R22, RF-23 |
| git + docs as durable truth | Corrective | R17 (knowledge), R1, R-H |
| Memory hygiene + periodic doc cleanups | Preventive | R18, R3, R-H |
| Rule #63 doc-canonicalisation | Preventive | R-H (doc-drift) |
| The four value-invariant anchors | Detective | R1, R6, deploy integrity |

## Appendix E — KRI dashboard specification

A single screen the PO can check at each handshake. Suggested layout (each tile = a KRI from Part 5.4):

```
┌──────────────────────── THAMMEN RISK DASHBOARD ────────────────────────┐
│ DATA FOUNDATION                          │ MEASUREMENT                  │
│  MoJ freshness   [160d 🟡 →red @365]     │  Capture        [dormant 🟢] │
│  Fallback share  [92%  🔴]               │  Pred↔outcome   [<10  🟡]    │
│  Reliable cells  [6    🟡]               │  Under-anchor   [−37/40% 🔴] │
│  ─ tracks R4/R19/RF-29                    │  ─ tracks R20/R7             │
├───────────────────────────────────────────────────────────────────────┤
│ INFRA & ENDPOINTS                        │ INTEGRITY & SECURITY         │
│  QARS status     [healthy 🟢]            │  Anchor drift   [0 🟢]       │
│  QARS Δ          [±1 🟢]                 │  CORS/docs lock [locked 🟢]  │
│  Cold latency    [~15s 🟢 /30s wall]     │  Origin↔prod    [sync 🟢]    │
│  ─ tracks R5/RF-15/R16                    │  Dispersion     [gated 🟢]   │
└───────────────────────────────────────────────────────────────────────┘
   GREEN today: QARS, infra, integrity, security.
   AMBER: MoJ freshness (ageing), reliable-cells, pred↔outcome.
   RED: fallback-share 92%, under-anchor −37/40%.  → the R19/R20/R7 cluster.
```

**Data sources:** all "infra & endpoints," "integrity & security," and "data foundation" tiles are live from `GET /api/health`. The "measurement" tiles require the capture table (R20 — off until D-2). The "under-anchor" tile is fed by `VALIDATION_LOG.md` confirmed sales.

## Appendix F — Gate catalog (the gates as risk-controls)

| Gate | What it gates | Primary risk-control role | Failure mode it prevents |
|---|---|---|---|
| **Gate-1** | Production push (per-session PO consent) | Caps blast radius of any deploy | An un-consented change reaching production |
| **Gate-2** | Methodology / user-facing change (sign-off **before** build) | The A/F-family control | A silent accuracy or authority change shipping unreviewed |
| **Gate-3** | Scope beyond a signed brief (flag-and-proceed) | Scope-creep visibility | RF-26 drift going unnoticed |
| **gate #6** | *(deleted by the 2026-06-09 cleanup — ISS-G03; beta = parallel non-blocking track)* | Historical; CLAUDE.md #65a still names it → reconcile (R-H) | — |
| **gate #11** | Capture activation (§8.1+§8.2+security) | The privacy master-gate | R11/RF-04/RF-31 — premature data processing |
| **Rule #14** | "verified" claims in any gate report | Keeps the *other* gates honest | A reasoned/worked-around check masquerading as executed (R14) |

> The gate model is the register's **primary preventive control surface**. Every gate is a deliberate *stop* that converts a silent risk into a *decision* — which is the whole point of a risk register in a fast-moving, AI-assisted, single-founder build.

## Appendix G — Empirical findings (E-series) as a risk-evidence index

The empirical findings (`Empirical_Findings.md`, E1–E23) are the *measured evidence* behind several risk scores. Indexed here by the risk each one informs (the file is the authoritative full text; this is a risk-facing cross-reference, not a restatement).

| Finding | Substance (brief) | Informs risk(s) |
|---|---|---|
| **E1** | Villa asking-premium +70% is **stock composition**, not under-registration; the under-registration hypothesis is **falsified**; MoJ is the sole valuation evidence (listings → sentiment only; buyer ceiling = MoJ × 1.10) | R21, RF-22 |
| **E3** | The eight valuation constraints (T2 caps, confidence ≤ indicative without MoJ, ±20% MUC, etc.) | R7, R-F1, R13 |
| **E4** | Strata / `luxury_new` stratum logic; bracket-matching is by-design (not a sibling-drop bug) | R7, R8, R15(closed), R22 |
| **E7** | QARS subtype requires a Zoning cross-check (stale subtypes can contradict current zoning) | R5 |
| **E8** | Tier weights T1=1.0 / T2=0.7 / T4=0.4 | R21, R-B |
| **E12** | MoJ self-calibration is **BLOCKED** (would re-import the bias) | R22, failed-path |
| **E15** | R1 setbacks (front 5m / side 3 / rear 3) + June-2026 amendments (used by the geometric footprint) | (accuracy inputs) R7 |
| **E16** | Staged valuation | R-F1 (authority arc) |
| **E20** | Compound ≥15,000 m² promotion → clean refusal (the 51/835/17 fix) | decomposition coherence, R7 |
| **E22** | Measure on the **default** flow (not a hand-crafted path) | R14, R20 |
| **E23** | Over-anchor = **dispersion**, not thinness; built-type + condition = the durable fix direction (n alone insufficient — pair with the dispersion gate) | **R7, R8, R9 (closed a18), R10 (closed)** |
| **Yield benchmarks** | Qatar net yields: 5–6% normal / >6% inspect / <4% weak; always compute *net* | RF-23, R7 (income method) |

> The single most risk-load-bearing finding is **E23**: it is the evidence that R7's over-anchor is a *dispersion* phenomenon (hence the dispersion gate as a control) and that the *durable* fix is built-type + condition (hence B-2). The bidirectional confirmation came later from the **V001/V002/V003** confirmed sales (`VALIDATION_LOG.md`), which *quantified* the under-anchor at −37/40% and are the evidence behind R7's inherent 20🔴.

## Appendix H — Glossary

| Term | Meaning |
|---|---|
| **AVM** | Automated Valuation Model |
| **MoJ** | Ministry of Justice (the open-data transaction source; `data.gov.qa`) |
| **QARS / khazna** | The Qatar GIS address/parcel endpoint (`khazna.gisqatar.org.qa`) |
| **MUC** | Material (valuation) Uncertainty Clause — RICS VPGA 10 |
| **HBU** | Highest and Best Use (the land-floor premise) |
| **DRC** | Depreciated Replacement Cost (the cost-approach method, §20.9) |
| **GT** | Ground Truth (parcel-linked confirmed sales — GT-1 valuer, GT-2 manual/confirmed) |
| **n≥20** | The confirmed-sale count that gates *precision* + any *published accuracy claim* (§0.4) |
| **Inherent / Residual** | Risk score before / after the listed controls |
| **L×I** | Likelihood × Impact (the risk score, 1–25) |
| **KRI** | Key Risk Indicator (a monitored metric with thresholds) |
| **NBSP** | Non-breaking space (`\xa0`) — the MoJ data-hygiene hazard |
| **the four anchors** | 54/541/6, 56/565/21, 55/296/13, 52/903/90 — value-invariant deploy guards |
| **two-lane model** | Claude.ai (analyst/verifier) ↔ CC (Claude Code, implementer), routed by Anas (PO) |
| **Gate-1/2/3, gate #11** | The Hard Gates (push / methodology / scope) + capture-activation; the former gate #6 (cohort) was deleted by the 2026-06-09 cleanup (ISS-G03) |
| **§0.4 ship-disclosed** | The standing principle: a value-affecting method may ship disclosed-as-indicative; n≥20 gates precision, not shipping |
| **Amiri Decision 28/2023 Art 5(7)** | The statute naming التقييم العقاري as a regulated activity (Aqarat) |
| **PDPPL** | Qatar's Personal Data Privacy Protection Law |

## Appendix I — Register changelog

| Version | Date | Change |
|---|---|---|
| Legacy | 2026-05-30 | `RISK_REGISTER.md` seeded (R1–R15), governance consolidation |
| Legacy updates | 2026-05-30 → 06-05 | R2/R6 closed (A14); R10 closed (a14); R15 closed (a23); R7/R8/R9 refined; R11–R14 added |
| **v2-errata** | **2026-06-09 (same day, later)** | **Errata pass after a full `Session_Log.md` read:** R9/A16 corrected OPEN→CLOSED (resolved-as-pool-fix at a18/v157, §20.18 — the legacy register row was stale and the error was inherited); all "A16/R9 root fix / live-trace prerequisite" items removed (R7 response, Part 5.1/5.2/5.3, appendices); gate #6 reconciled to the 2026-06-09 cleanup (ISS-G03: cohort gate deleted, beta = parallel non-blocking track) with a CLAUDE.md #65a doc-drift flag; added the §20.45 Heroku-auth deploy lesson (R-C) |
| **v2 (this doc)** | **2026-06-09** | Full risk-register rebuild: L×I scoring methodology + appetite + controls taxonomy; heatmap + concentration analysis; **R16–R22 added** (infra SPOF, key-person, AI-lane drift, GT scarcity, no-measurement, MoJ single-source, DRC-bias); **RF-01..RF-31 forward register** (beta → monetization → apartments → scale → regulatory → market → competitive → AI → tail); treatment plan + **PO-decision register**; KRI dashboard tied to `/api/health`; closed/accepted/failed-path sections; appendices A–J. Grounded in a live probe (16:17 UTC) + the corpus. |

## Appendix J — Assumptions & limitations of this register

1. **Scores are defensible, not precise.** The L×I bands are coarse by design (Part 2.2). The value is the *band* and the *relative rank*, not the exact number — do not over-read an 11 vs a 12.
2. **Forward scores are at-horizon and assumed~.** RF- scores are estimates of exposure *if/when* the horizon is crossed; they are not current exposure and carry more uncertainty than the current R- scores.
3. **The register reflects a point-in-time snapshot.** It is grounded in the 2026-06-09 16:17 UTC `/api/health` probe and the corpus as mirrored at `/mnt/project/`. Live state moves with every sprint; the KRIs (Part 5.4) are the mechanism for keeping it current — re-score at every handshake/sprint-close.
4. **No paper-control credit (Rule #14).** Residual scores assume the listed controls *operate as designed*; a designed-but-unexecuted control (a dormant runbook, an un-run KRI, the §20.9 discipline before it is coded) earns **no** residual reduction until it is live.
5. **Some E-series contents are referenced, not restated.** Appendix G indexes the empirical findings to the risks they inform; `Empirical_Findings.md` is the authoritative full text. Where this register could only *reason* a fact (not measure it this session), it is tagged **assumed~**.
6. **This register does not make decisions.** It frames the PO's decisions (Part 5.2) and ranks the risks; the gate authority and the reserved decisions remain Anas's.
7. **It extends, it does not supersede.** `RISK_REGISTER.md` (R1–R15) remains the canonical seed; this document is the expanded view and is to be reconciled back to the canon (the closing note).

---

## Closing note — canonicalisation (Rule #63)

This register was authored in the **Claude.ai analyst/verifier lane** and exists, at the moment of writing, only as chat output + this file. Per Rule **#63** (Claude.ai-authored docs persist to the repo via a same-message CC save+commit routed by the PO; `docs/` is the source of truth), it must be saved to the repository to become canonical — and a decision is owed on **whether it replaces, or sits beside, the existing `RISK_REGISTER.md`** (analyst recommendation: **sit beside it as `RISK_REGISTER_v2.md`** and treat the legacy R1–R15 file as the *seed* that this expands, rather than overwriting the canonical IDs; later, fold the closed-risk updates back into the seed so the two don't drift — R-H).

Until it is committed to `docs/`, this register is **not** the source of truth — the live `/api/health` + `CLAUDE.md` #65a remain authoritative for forward state (Rule #58: measured wins).

*— End of RISK_REGISTER_v2.md —*
