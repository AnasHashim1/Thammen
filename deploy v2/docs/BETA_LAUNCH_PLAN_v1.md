# BETA_LAUNCH_PLAN — Thammen (v1 draft)

> **Tier:** BETA — locked by Anas. This is the beta instantiation of `LAUNCH_READINESS_GATES_v1.md` (which gate applies, in beta terms).
> **Status:** Claude.ai-formulated · awaiting Anas confirm (§4) · CC commits + executes the engineering items on sign.
> **Core posture:** a controlled, known-imperfect, honest-by-design tool. The beta's *job* is to gather the real-world accuracy data (gate 4) and surface PDPPL in practice (gate 3) — the two things you cannot close from a desk.

---

## §0 — Beta definition (locked)

- **Scope:** villas + land only. Apartments already **refuse** (`52/903/90` → `insufficient_data`) → gracefully excluded; just confirm the refusal copy reads well for a beta.
- **Cohort:** small, invited, trusted (Anas picks — brokers / valuer contacts / known users).
- **Framing:** "decision-support tool, **not** a certified valuation" — explicit on the result surface + in onboarding.
- The honest ranges + MUC you already ship **disclose** the condition-blindness (Abu Hamour ~10% under-anchor, Marikh wide range) — beta does not pretend otherwise.

---

## §1 — MINIMUM GATES TO GO LIVE (the short list)

| # | Item | Type | Owner | Status | Note |
|---|---|---|---|---|---|
| 1 | **Decision-support framing in UI** | content | Anas + Claude.ai drafts | not started | A clear "what this is / isn't" + the not-certified line on the result surface. |
| 2 | **Basic ToS + disclaimer + privacy/consent notice** | legal-light | Anas + **counsel** (Claude.ai drafts a starting point) | not started | Limitation of liability + PDPPL consent for the cohort. **Draft + get review — not lawyer-authoritative from me.** Proportionate to a small consented cohort. |
| 3 | **A7 fix** (`rics_compliant` always false) | sprint (S) | CC | open bug | Shouldn't ship even to a beta cohort that might check. Small. |
| 4 | **Beta instrumentation — prediction log + feedback** | sprint (S) | CC | **shipped-dormant (a15 / Heroku v154), pending activation** | SHIPPED 2026-06-01 (CHANGELOG_v67 / §20.15): NET-NEW durable capture + `POST /api/feedback`, backend-only, **flag-off + no-op without `DATABASE_URL`** → zero data footprint. Two-lane post-deploy smoke BYTE-IDENTICAL; isolated 27/27, DoD 392/15/45/58. **ACTIVATION** (provision Postgres → `DATABASE_URL` + `EVAL_CAPTURE_ENABLED=true`) gated on **§8.1 PDPPL + §8.2 cross-border** (counsel, R11) **+ the a15 capture-surface security pass** (#7 below / LAUNCH_READINESS gate 11). This is what closes gate 4 over time. |
| 5 | **Scope + banner confirm** | audit | CC / Claude.ai | mostly done | Villas/land only; apt-refusal copy beta-appropriate; stale-data banner prominent. |
| 6 | **Cohort + access setup** | business/ops | Anas | not started | Who's in, how they get access, how feedback reaches you. |
| 7 | **Security review of the a15 capture surface** (pre-activation) | sprint (S) + legal | CC + counsel | PENDING | Sequenced WITH the PDPPL §8.1/§8.2 track (= LAUNCH_READINESS gate 11). Rate-limit `/api/feedback` (V18 DoS cap was `/api/evaluate`-only — confirm slowapi + Cloudflare cover it); free-text `note` safety (length-capped ✓ / render-safe for the UI); at-rest + credential security for the quasi-PII store; confirm 2.16.17 SECURITY_AUDIT §5 Cloudflare toggles (rate-limit + HSTS) live. **Gates a15 ACTIVATION, not beta-go-live of the tool itself.** |

---

## §2 — What beta is NOT blocked on (explicit, so it doesn't creep)

- **B (condition)** — fast-follow, runs *in parallel*, improves accuracy *during* beta. NOT a beta blocker.
- **2.22.0b 5-stage UX** — post-beta (it's the public value prop).
- **Full PDPPL clearance** — beta runs on consent + a limited cohort; full clearance is a *public* gate.
- **MoJ freshness / apartments** — disclosed (banner) / excluded (refusal); both *public* gates.
- **A measured error distribution** — beta *generates* the data for it; not a precondition.

---

## §3 — Critical path to beta-live (honest)

- **Engineering:** A7 (#3) + instrumentation (#4) ≈ **1–2 small sprints** (each gets its own §5 UI-first audit at kickoff). #4 is NET-NEW durable capture — recon (2026-06-01) measured that nothing persists today — so scope it as standing up the first persistent store (Postgres) + feedback endpoint behind a flag, not a small extension.
- **Parallel, Anas-owned:** framing + ToS + privacy (#1, #2) with counsel review; cohort setup (#6).
- **Net:** beta-live ≈ a couple of small sprints + one legal/content pass + your cohort decision — **weeks on the engineering side**, gated mostly by the legal-light pass and the cohort, both your calls.
- **B** starts as a parallel fast-follow whenever you want — its own measure-first kickoff (recon: do age + E4 stock-strata actually *explain* the anchor residuals, before designing the adjustment).

---

## §4 — القرار المطلوب (Anas)

1. **Cohort shape** — confirm villas+land, ~N invited users, and roughly *who* (brokers / valuer contacts / known users). This is the main thing gating beta-live.
2. **Sequence** — A7 + instrumentation first (engineering) with framing/ToS in parallel, or a different order?
3. **B fast-follow** — start its kickoff now (parallel), or after beta-live?
4. **ToS/privacy starting point** — want me to draft one for your counsel to review, or do you have this covered?

> On your confirm I'll: (a) scope the first engineering sprint (A7 or instrumentation — single-purpose, §5 audit, brief for sign), and (b) draft whichever of the framing / ToS / B-kickoff you green-light. CC executes the engineering on Gate-1 as usual.

---

*v1 draft. Claude.ai formulates; Anas confirms scope/cohort + signs each sprint brief; CC commits this doc and executes the engineering items. Pairs with `LAUNCH_READINESS_GATES_v1.md` (the full tier register) and ROLES_AND_COMMS (mission = optimal public launch via honest quality gates — a sound beta is the first leg).*
