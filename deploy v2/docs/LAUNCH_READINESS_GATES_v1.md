# LAUNCH_READINESS_GATES — Thammen (v1 draft)

> **Status:** Claude.ai-formulated · **tier locked = BETA (Anas, 2026-06-01)** · gate sign-off in progress (§4) · CC maintains. a15 instrumentation shipped-dormant → new **gate 11** (capture-surface security review).
> **Why this exists:** "How many sprints to launch?" has no answer in the current docs — the roadmap (Project_Instructions §11) is a list of *feature* sprints, not *launch gates*. This is the first explicit launch-readiness register. It separates the four gate **types** — sprint-work / legal / external-dependency / validation — so the launch date is set by the real blockers, not the feature backlog.
> **Live state at drafting (Rule #57 verified):** engine `2.22.0a.14` / Heroku v153 / MoJ 152d stale / qars healthy.

---

## §0 — FIRST DECISION: launch tier (Anas)

The sprint count and the binding gates are wildly different across three tiers. Nothing below can be sequenced until this is picked.

**→ DECIDED (2026-06-01): tier = BETA-FIRST (Anas).** The BETA column is the active scope (villas + land only); PUBLIC / B2B are later milestones.

| Tier | Scope | Framing |
|---|---|---|
| **BETA** | Villas + land only · small invited cohort | Explicit "decision-support tool, **not** a certified valuation" |
| **PUBLIC** | Open consumer · marketed | Full public product |
| **B2B** | Banks / institutions (Basel 3.1) | Heaviest validation + regulatory |

→ **Each gate in §1 is tagged with the tier(s) it blocks.** A gate that blocks PUBLIC may be acceptable-as-a-disclosed-limitation at BETA.

---

## §1 — GATE REGISTER

Type legend: **S** = sprint-work · **L** = legal/regulatory · **X** = external dependency (not in your hands) · **V** = validation. "In hands?" = can you close it yourself.

| # | Gate | Type | Status | In hands? | Blocks | Note |
|---|---|---|---|---|---|---|
| 1 | **Apartment coverage** | X | BLOCKED (MME auth-session capture) | ❌ | PUBLIC, B2B | A large segment (Pearl, Lusail towers) returns "insufficient data" today. Drops for BETA **only if** villas/land-only is an accepted v1 scope. |
| 2 | **MoJ data freshness** | X | DEGRADED — 152d frozen since 2025-12-31 | ❌ | PUBLIC, B2B | Depends on govt resuming or MME coming online. BETA: acceptable *with* the stale-data banner + decision-support framing. Public credibility/liability risk. |
| 3 | **PDPPL compliance** | L | UNKNOWN / unstarted | ⚠️ partly (you initiate; regulator's clock) | PUBLIC, B2B (likely BETA too) | Public handling of citizens' transaction data almost certainly requires it. **Possible long pole.** Needs legal counsel, not a sprint. |
| 4 | **Accuracy — measured** | V | NOT MEASURED — anchors + broker judgment only | ⚠️ partly | PUBLIC, B2B | No error distribution exists, AND a rigorous study is itself blocked by the PIN-keyed-sale gap (Rule #45 — MoJ sales can't be located to parcels). BETA: expert spot-check + honest framing may suffice, and beta *generates* real-world accuracy data. **The responsible-to-ship gate.** |
| 5 | **Public ToS / liability / disclaimer** | L | unstarted | ✅ (with counsel) | PUBLIC, B2B | "Not a certified valuation" framing + limitation of liability. Light at BETA, formal at PUBLIC. |
| 6 | **Condition model (Branch B)** | S | designed, not built | ✅ | (accuracy-relevant; fixes anchor residuals) | Sprint-countable. Improves Abu Hamour under-anchor / Marikh over-anchor. Engine prerequisite for 2.22.0b Stage 2. |
| 7 | **5-stage UX (2.22.0b)** | S | not started, gated on B | ✅ | PUBLIC (the consumer value prop) | A sprint *cluster*, not one. Stages 4/5 (broker/valuer) depend on gate 8. |
| 8 | **Broker / valuer partner agreements (Stage 4/5)** | L/biz | exploratory | ⚠️ partly | PUBLIC (if the funnel is in v1), B2B | The monetization stages of the 5-stage vision. |
| 9 | **A7 + open mediums (A5, A15)** | S | open | ✅ | PUBLIC (A7 is a RICS-claim credibility bug — `rics_compliant` always false) | Small. A7 should not ship public. |
| 10 | **RICS-claim scope** | L/decision | unresolved | ✅ | PUBLIC, B2B | What you may publicly *claim*: "RICS-aligned methodology" vs "RICS Red Book-compliant valuation." The latter implies a registered valuer (Stage 5). Define before any marketed claim. |
| 11 | **Security review of the a15 capture surface** | S + L | shipped-dormant (a15/v154); **review PENDING** | ✅ | BETA-ACTIVATION (sequence WITH PDPPL gate 3) | Pre-ACTIVATION of prediction capture + `POST /api/feedback`. Scope: **rate-limit `/api/feedback`** (the V18 DoS cap was `/api/evaluate`-only — confirm slowapi + Cloudflare cover feedback) · **free-text `note`** (parameterized writes ✓ / length cap `max_length=2000` ✓ / render-safety for the later UI) · **at-rest + credential security** for the quasi-PII store · confirm the 2.16.17 SECURITY_AUDIT §5 Cloudflare toggles (rate-limit rule + HSTS) are live. Gates a15/a16 ACTIVATION (with §8.1/§8.2, R11), not beta-go-live of the tool itself. **a16 already hardened the surface** (UUID-only key, no stored `valuation_id`, street/building Fernet-encrypted, `note` removed, 180d retention/purge/erase — §20.16 / CHANGELOG_v68) → this gate now = the remaining **rate-limit/render-safety/at-rest** review **+ 3 pre-activation steps:** verify the Fernet round-trip on Heroku before any real data · set PG backup retention short · backup-erasure runbook. |

---

## §2 — WHAT THE REGISTER SAYS

- **The sprint-countable gates (6, 7, 9) are the *smallest* part of the timeline** and your `(vi)→B→2.22.0b` ordering for them is correct. They will be ready long before the rest.
- **Your launch date is set by the non-sprint gates** — apartments (1), data freshness (2), PDPPL (3), accuracy (4), ToS (5), partner agreements (8), RICS-claim (10). Most are external or legal, not engineering.
- **BETA is reachable soonest** — most PUBLIC/B2B gates relax under a controlled, villa/land, decision-support framing — *and* a beta is the only realistic way to start closing gate 4 (real-world accuracy data) and to scope gate 3 (PDPPL) in practice.

---

## §3 — RECOMMENDED SEQUENCE (analyst lean — Anas decides)

**If BETA (my lean as the first milestone):**
1. Finish **B** (gate 6) — tightens accuracy where it's weakest.
2. Fix **A7** + mediums (gate 9).
3. Lock the **"decision-support, not certified valuation" framing + a basic ToS/disclaimer** (gate 5, light).
4. Keep the stale-data banner (gate 2 disclosed, not closed).
→ Beta-ready in a small number of sprints + one legal-framing pass. Then *use the beta* to gather real accuracy data (gate 4) and surface PDPPL scope (gate 3).

**If PUBLIC:**
- Beta first, **then** resolve data freshness (gates 1+2: apartments via MME, MoJ refresh), **PDPPL** with counsel (gate 3), a **real accuracy validation or an honestly published error band** (gate 4), **RICS-claim scope** (gate 10), and **2.22.0b** (gate 7). The non-sprint gates dominate the calendar.

**If B2B:**
- Public-grade + **adversarial validation hardening** + **regulatory (Basel 3.1)** — a separate, much longer track. Not a near-term target.

---

## §4 — القرار المطلوب (Anas)

1. **Pick the launch tier** (§0) — BETA / PUBLIC / B2B.
2. For that tier, confirm **which gates you commit to closing** vs which you accept as **disclosed limitations** (e.g. at BETA, gate 2 stays disclosed-not-closed).
3. **Beta-first** (analyst lean) or straight-to-target?

> On your tier-pick I'll turn this into a tier-specific, sequenced plan and — only then — say whether B is even on the critical path to *that* launch, and what the honest sprint range is for the engineering portion.

---

*v1 draft. Claude.ai formulates; Anas signs the tier + gate commitments; CC commits the doc and maintains status. Pairs with: ROLES_AND_COMMS (mission = optimal public launch via honest quality gates) · RISK_REGISTER · Project_Instructions §11 (feature roadmap — note: §11 is 2.21.x-era and predates the 2.22.0a arc; treat live + git + memory as authoritative for forward state).*
