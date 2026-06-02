# Thammen — Operating Model v2 (Lean Value-Flow)

> **Status:** **ADOPTED** — Anas (PO), 2026-06-02. Supersedes `OPERATING_MODEL_v2_lean_PROPOSAL.md` and the process-flow content of `ROLES_AND_COMMS.md` (the §"Standard flow" block). The **Roles / Conduct / Channels-&-truth** content of `ROLES_AND_COMMS.md` is **retained**.
> **Scope:** consolidates the procedural sprawl in `Operational_Rules` / `Empirical_Findings` / `RISK_REGISTER` into a small working set.
> **It changes *how we work*, not *what we value*.** The empirical core (measure-first, honest gates) is preserved and sharpened.
> **Self-test (§0):** adopting this must *net-reduce* process weight. If it ever stops earning its keep, prune it too.
>
> **Amendments folded at sign-off (C1–C5):**
> - **C1** — closes the §7 write-lag hole: *doc-delta commit precedes build routing* (the decision-write ordering across the CC write-access boundary).
> - **C2** — keep a **deploy fingerprint** in `/api/health` (the #57/#58 live-truth anchor) even after dropping the semantic `2.22.0a.N` slug + CHANGELOG-per-micro.
> - **C3** — the **capture-activation** surface is **GATED**, not Full — even when self-cleared by the PO rather than external counsel.
> - **C4** — **beta cold-start bridge**: the audit + known-defect list stay the interim prioritizer until beta-n is usable.
> - **C5** — **conservative pruning** + **execute the full supersession surface** (incl. `Custom_Instructions §2` + recall phrases), or §0 is violated.

---

## 0. North Star — the one optimization target
**Flow of validated value to a real user.**
Every rule, doc, gate, and change is justified only by how much it (a) speeds our learning of what users actually value, or (b) prevents a serious defect. If it does neither, it is waste — cut it.

## 1. Operating principles (the whole philosophy in six lines)
1. **Measure first** — any question a cheap measurement can settle, settle it *before* theorizing, briefing, or validating. (The A7 audit is the model: one probe killed a wrong sprint.)
2. **Smallest batch** — one change, one purpose, smallest diff that ships value.
3. **Ship to learn** — real usage beats internal inference; put the smallest thing in front of real users and let them set priorities.
4. **One truth** — git + docs. *A decision is not done until it is written there.* (The structural fix for the R1 divergence — see §7.)
5. **Scale ceremony to risk** — reversible work moves fast and light; irreversible / user-facing / methodology / personal-data work earns the full gate.
6. **Honest gates are sacred** — safety, child-safety, compliance, valuation-honesty, regulatory/data. Never trimmed. *Everything else is trimmable.*

## 2. The three lanes (kept — they work)
- **Anas — Product Owner** (sole, inalienable). Owns value, priorities, decisions, accountability. Signs Full/Gated work; routes between the two Claude lanes. *Design goal: minimize his routing load — it is the bottleneck and the bus-factor-1.*
- **Claude.ai — coach + analyst.** Methodology, audits, brief authoring, candid counsel, honest gates. Advises; never owns. Fresh per chat; truth lives in git + docs.
- **Claude Code (CC) — developer.** Sole agent on `C:\Thammen`. Implements, measures, deploys, self-corrects reversible work. Stops at gates.

## 3. The board — Kanban, not Scrum
We do not run time-boxed sprints; we run **continuous flow**. Drop the "sprint" framing (it implies time-boxes we don't use). A unit of work = a **change** pulled from a queue.
- **One visible backlog**, ordered by value-to-user. Priorities are *pulled from the top*, never invented. ("Check completed work first" → "pull the top of the board.")
- **WIP = 1 build change in flight** (this constraint is on CC's build pipeline — Claude.ai may audit/scope the next item in parallel). Finish before starting.
- **Columns:** Backlog → Ready → In-flight → Measuring → Done.

## 4. Classes of service — *this is the weight cut*
Route each change by risk/reversibility:

| Class | What | Process |
|---|---|---|
| **Fast** | reversible, no user-facing change, no production state (refactors, test fixes, doc edits, local probes) | CC drives autonomously. No brief, no CHANGELOG, no multi-AI. Do → test → commit (origin) → one-line note. |
| **Full** | user-facing **OR** methodology **OR** irreversible | UI-First Audit → signed brief (#32) → implement → measure → docs+CHANGELOG → Gate-1 push → live verify. |
| **Gated** | safety / compliance / valuation-honesty / regulatory / **personal-data** | Human gate, never skipped, regardless of size. |

> **C3 — personal-data is Gated even when small, and even when self-cleared by the PO** rather than by external counsel. "Self-clearance" is *Anas's explicit human gate*; it is Gated by definition, not a Full-lane shortcut. (This is the exact slip the Gated class exists to catch — see §11.5.)

**Multi-AI validation:** Full/Gated and *novel + non-measurable + high-stakes* only. Never as peer-review-of-a-peer-review for routine tweaks.
*Evidence:* most "bugs" are settled by a cheap audit and never need the full machine — A7 today, a13 earlier.

## 5. Work-item lifecycle (lightweight DoR / DoD)
- **Definition of Ready** (Full lane): the **UI-First Audit** done — 3–5 real properties (incl. a **tower/apartment_building** for coverage-honesty), khazna GIS ground-truth vs `/api/evaluate` **field-by-field**, the field confirmed **rendered to the user** (grep `index.html`), **mobile 390×844** check, scope counts — *and* a one-page brief signed (#32).
- **Definition of Done:** tests green (DoD matrix) + 3-address Heroku smoke + **a bumped deploy fingerprint in `/api/health`** *(C2 — short commit SHA or build number is fine; this is the #57/#58 live-truth anchor, distinct from the dropped semantic slug)* + **docs updated incl. `CLAUDE.md` NEXT STEP** + one `measured-win` line. *Not done until NEXT STEP reflects reality.*

## 6. The learning loop — how we choose what to build
Build → Measure → Learn, around the **free invited beta**:
1. Invite a handful of real users (villas / land).
2. Capture predictions + feedback (consented, conservative PDPPL config — Gated, §11.5).
3. Measure estimate vs real outcome → find the **largest real error**.
4. Fix it (a Full-lane change). Re-measure. Repeat.

**The beta — not the anchors — sets the engine roadmap.** Anchors (Marikh, Abu Hamour) stay as regression guards, *not* as the source of priorities.

> **C4 — cold-start bridge.** A handful of invited users yields **weak signal for the first weeks** (small-n). Until the beta produces statistically usable signal, the **interim prioritizer stays** the UI-First Audit + the known-defect list (A15 silent-fail; the **R7/R8 bidirectional condition residual** — Abu Hamour under-anchor / Marikh over-anchor). Hand the wheel to the loop **once beta-n is usable**; the anchors never become the priority source.

## 7. Anti-divergence — the R1 fix, made structural (C1)
**A decision is not done until it is in the docs.** Because **only CC can write to `C:\Thammen`**, the lane that *makes* a decision is often not the lane that can *write* it. So the mechanism is a strict **ordering**, not a single turn:

1. **Claude.ai emits the doc-delta in the same turn it advises the decision** — the relay copy-paste block: the change to state / posture / **`CLAUDE.md` NEXT STEP** + the right register.
2. **Anas has CC commit the doc-delta.**
3. **Only then does Anas route the build to CC.** → **Doc-delta commit precedes build routing.**

Until the delta is committed, the live **kickoff/handoff token carries the decision and outranks the docs** (#57: *live state > any doc or memory*). **R1 happened precisely because a decision lived only in chat while CC read stale docs** — this ordering closes it.

- **Lane transitions use a standard token:** the Claude.ai *kickoff* block (in) and the CC *handshake* block (in). Both open with a live **#57** ground-truth check (git tip + `/api/health`).
- Anas routes by *handing over the current docs*, not by re-explaining.

## 8. Prune the process — the cleanup that makes this real
Today: 65 rules + 23 empirical findings + 13 risks + several heavy docs. Most are *history*, not *load-bearing*. Tier everything:
- **ACTIVE** — the small set (~≤15) that currently prevents a real defect or defines a gate. Lives at the top of each register; this is the working memory the AIs must hold.
- **ARCHIVE** — everything else (closed risks ✅, superseded rules, one-off lessons) moves to an `*_archive` appendix: searchable, not loaded.

> **C5a — prune conservatively.** The **first pass archives only the mechanically-closed**: closed risks (✅), superseded/folded rules (e.g. #44-folded-#43), and reserved/unused placeholders (#41, #55, #56). **Everything requiring judgment ages out via the lifecycle rule, one item at a time** — a single big-bang re-tiering of all ~101 items risks archiving a still-load-bearing rule.

- **Lifecycle of a rule:** added only when a defect *recurs* that a rule would have prevented; retired when it no longer prevents a live defect. (Freezing at #65 was the right instinct; this makes pruning continuous.)
- **Target working set:** ≤15 active rules · a ≤1-page `CLAUDE.md` snapshot.

## 9. Session discipline (keep — it works)
- **In:** paste the kickoff/handshake token → run #57.
- **Out:** hard-stop before context compaction (#64); write the handoff token (#65) so the next session is zero-ask.
- Substantial new work starts in a *fresh* session, never the tail of a long one.

## 10. From → To (what actually changes)
| Today | → | Proposed |
|---|---|---|
| 8-step flow for *every* change | → | 8 steps only for **Full** lane; Fast lane = CC autonomous |
| sprint versioning per micro-change (`2.22.0a.16`) | → | git commits + CHANGELOG for **user-facing releases only** — but a **deploy fingerprint** (SHA / build-no.) stays in `/api/health` (the #57 live anchor, C2) |
| multi-AI validation routinely | → | only when **novel + non-measurable + high-stakes** |
| 65 rules / 23 E / 13 R all "active" | → | **≤15 active** + archive the rest (conservatively, C5a) |
| priorities from anchors / inference | → | priorities **pulled from the beta learning loop** (with the §6 cold-start bridge) |
| a decision can live in chat | → | **decision not done until in docs** (doc-delta commit precedes build routing, C1) |

## 11. First moves (adopt incrementally, no big-bang)
1. **PO sign-off — DONE (Anas, 2026-06-02).** Committing *this* doc-delta closes it — and models C1 (the adoption decision is written to the docs before the next build is routed).
2. **Conservative pruning pass (C5a)** — archive only the mechanically-closed; lifecycle-age the rest. CC, docs-only (**Fast** lane).
3. **Reconcile the full supersession surface (C5b)** — amend `Custom_Instructions §2` (one-zip-per-Sprint → release-only CHANGELOG; drop sprint numbering; reconcile the "تذكر Sprint …" recall phrases) and replace `ROLES_AND_COMMS §"Standard flow"` with a pointer to §4–5 here. A **Full**-lane doc task — *without it, two conflicting delivery contracts coexist and §0 is violated.*
4. **Stand up the backlog** — seed from the real open work (beta-enablement, B/condition, A5/A15…), ordered by value-to-user.
5. **Top item = beta-enablement, correctly classed (C3):**
   - non-PII plumbing (invite mechanics; the capture *code*, already shipped-dormant) = **Full**;
   - **capture activation** (PDPPL self-clear §8.1/§8.2 + the gate-11 security pass: Fernet round-trip verified on Heroku · short PG-backup retention · backup-erasure runbook) = **GATED** — Anas's explicit human gate.
   - *This is the single move that ends the "no users" gap.*
6. **Run the loop** (with the §6 cold-start bridge until beta-n is usable).

---
> Bound by §0: if this document ever stops earning its keep, prune it too.
