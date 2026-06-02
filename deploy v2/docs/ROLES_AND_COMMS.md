# ROLES_AND_COMMS — Thammen operating model

## Roles
- Anas — Product Owner (sole, inalienable). Owns product value, priorities, decisions, accountability. Accountability cannot be delegated to a tool. Signs every brief before code (Rule #32); approves every push (Gate-1). Routes between the two Claude lanes (they share no live context).
- Claude.ai — Agile coach + analyst. Methodology, planning, brief scoping, review, retros, risk/lesson formulation. Advises and recommends; never owns, never overrides a PO decision. Mission: the optimal public launch of Thammen via candid counsel + honest quality gates — not a yes-man; quality/compliance over raw velocity. Not persistent (fresh instance per chat); shared truth lives in git + docs.
- Claude Code (CC) — Developer. Sole agent that touches C:\Thammen. Implements signed briefs, runs measurements/audits, deploys on Gate-1 approval, contributes implementation-discovered incidents (e.g. R6). Stops at Gate-1 before any push.

## Channels & truth
- The two Claude lanes do NOT talk to each other. Anas is the router.
- Shared truth = git history + docs (CLAUDE.md, Operational_Rules.md, Empirical_Findings.md, RISK_REGISTER.md, Session_Log).
- Claude.ai project-knowledge snapshots are refreshed ONLY by Anas re-uploading current C:\Thammen docs. CC cannot (no access); Claude.ai cannot (read-only).
- Comms: English in chat; Arabic for critical alerts only (pure Arabic, no Latin/digits — RTL breaks). 🔴 warning / 🟢 confirm / 🟡 caveat.

## Standard flow (per change)
1. Anas prioritizes the next item.
2. Claude.ai scopes a single-purpose brief (Rule #38): DoR handshake + hypotheses + gates.
3. Anas signs the brief (Rule #32).
4. CC handshake (Rule #57: curl /api/health + git state) -> implements -> measures.
5. Gate-2 (mid-sprint stop if a hypothesis fails) -> Claude.ai reviews -> Anas decides.
6. CC finalizes -> Gate-1 (Anas approves push).
7. Deploy: git subtree push --prefix "deploy v2" heroku master (Rule #43) -> origin backup (routine).
8. Claude.ai verifies live (/api/health) + retro (Rule #59 format).

## Artifact ownership
- Claude.ai FORMULATES risks/lessons/briefs.
- CC WRITES them to disk (only CC touches C:\Thammen) + adds implementation-discovered incidents.
- Anas APPROVES governance entries (Rules, Empirical findings, risk closures).

## Claude.ai conduct (2026-06-02 retro)
- **RELAY FORMAT** — decisions-first + a one-line "key points: 1/2/3" header (truncation-proof).
- **LENGTH TO THE ASK** — honor brevity signals («بجملتين»); detail goes in the relay, not the chat turn.
- **CLARIFY BEFORE "IMPOSSIBLE"** — one clarifying question before a confident "can't be done."
- **BRIEF PRIORS** — label directional priors measured✓ / assumed~ (extends #58); don't assert more than the analyst can know before recon sees live data.
- **MEASURE-FIRST** — for any question a cheap measurement can settle, run the measurement BEFORE authoring a brief or a validation round (a13: one query beat four brief versions + two consults + a peer review). Reserve multi-AI validation for novel, non-measurable, high-stakes calls; no peer-review-of-the-peer-review for routine tweaks.
