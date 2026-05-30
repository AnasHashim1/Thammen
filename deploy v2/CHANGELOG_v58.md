# CHANGELOG v58 — Governance Consolidation (2026-05-30)

> **Type:** docs-only. **No `ENGINE_VERSION` bump, no code change, no test change.** ONE
> commit, TWO labeled scopes (A: accuracy reconciliation; B: process hardening).
> **NOT pushed** (Rule #32) — batches into the next code sprint's push.
> **Engine unchanged:** `thammen-sprint2p22p0a6-seed-getplot-dedup` (Heroku v145).
> **Brief:** `docs/BRIEF_governance_consolidated_2026-05-30.md`.

## 1. Why this matters
A "MEASURE, do not trust the brief" pass found multiple memory-vs-disk drifts in the live
governance docs (RISK_REGISTER R3): MoJ "139d" vs live **150d**; "RICS VPS 4" vs the code's
actual **VPGA 10 + VPS 6 + IVS 106**; "Current latest = Sprint 2.16.12" (4 sprints stale); and
"brokerage-fed / pending-secretary" framing for Confirmed Sales that no longer reflects
reality (both internal sale-data feeds are closed). Stale governance docs mislead the next
session — the exact R1/R3 risk this pass also hardens against.

## 2. Definition of Ready — measured (see brief §0 for the full table)
- Live engine `thammen-sprint2p22p0a6-seed-getplot-dedup` / health `3.1.0-sprint2.22.0a.6` / Heroku v145.
- MoJ **150 days** stale (2025-12-31). Latest CHANGELOG on disk = v57 → this = **v58**.
- Operational_Rules highest in-file = **#53**; **#54 was memory-only** (Multi-AI) → written in.
  Empirical **E15–E20 all present**. RICS code surface = VPGA 10 + VPS 6 + IVS 106 (+ residual
  "VPS 4" method-labels in ~12 .py sites = deferred code cleanup).
- **Tests (exact):** aggregator 392/392 · security 15/15 · surface-honesty 45/45 · broad
  **48/49** (1 brittle EXACT-version-pin fail in `test_sprint_2p22p0a5_request_budget.py` —
  RISK_REGISTER R6; deterministic, not a functional regression; relax in next code sprint).
  Self-correction (Rule #36): the 2.22.0a.6 "broad 49/49" was measured *before* the version
  bump; post-bump = 48/49. `test_v2_modules.py` formally **excluded** (pytest not installed /
  not in requirements; already in the broad runner's `SKIP_FILES`).

## 3. Scope A — accuracy reconciliation
- **RICS scrub:** `VPS 4` removed from the **runtime** governance docs (CLAUDE.md ×2,
  Custom_Instructions, Project_Instructions, Empirical_Findings ×3) → code-emitted surface
  ("RICS Red Book Global Standards, effective 31 January 2025 — VPGA 10 + VPS 6 + IVS 106"
  for the standards framing; "RICS Red Book" for generic method/approach context).
- **Measured-value refresh** (engine / Heroku v145 / latest sprint / CHANGELOG / 150d MoJ /
  last-updated) in CLAUDE.md, Project_Instructions, Custom_Instructions headers.
- **Custom_Instructions:** "Current latest = Sprint 2.16.12" removed (→ single-source pointer);
  §3 test count + §5 MoJ days corrected to measured.
- **DoD test matrix single-sourced** in CLAUDE.md (pre-deploy checklist item 4); other docs
  reference it.
- **Roadmap** marked authoritative at **Project_Instructions §11**; CLAUDE.md points at it.
- **Rule #54** (Multi-AI consult at sprint open) written into Operational_Rules.
- **Brokerage scrub:** all "brokerage-fed Confirmed Sales pipeline" / "recalibration via
  brokerage closings" / "pending secretary" framing neutralized in runtime docs. **Sprint
  2.16.16 / Confirmed Sales = deferred INDEFINITELY (no viable internal source — secretary +
  brokerage both closed); NOT a data source / dependency / pillar.** T2 "broker" = ad-hoc
  only; Stage-4 field check = broker-agnostic.

## 4. Scope B — process hardening
- **`docs/RISK_REGISTER.md`** created — 6 seeded risks (5 from the brief + R6 brittle-pin).
- **Rule #43** amended in place: backup-push-to-origin is now a **standing part of the deploy
  ritual** (not a per-time manual confirmation) — origin had silently fallen 98 commits behind.
- **New rules #57** (session-start ground-truth handshake) **+ #58** (assumed-vs-actual gap →
  measured wins, log to RISK_REGISTER). **#55** (ENV-VAR override audit) **+ #56** (Branch B
  measure-dominant-cost) **RESERVED** with a documented note (collision surfaced, not reused).

## 5. Verification — DoD (measured)
- `VPS 4` / `brokerage-fed` / `pending secretary` / `Current latest = Sprint 2.16.12` →
  **ZERO** hits across the **runtime** governance docs (CLAUDE.md, Project_Instructions,
  Custom_Instructions, Empirical_Findings). Grep-verified.
- Residual literal hits are **intentional**: (a) historical artifacts NOT rewritten —
  CHANGELOG_v3/v8/v55, README_SPRINT1B.md, PHASE0_2p22p0a4_DISCLAIMER_MAP.md (audit-trail
  integrity, Rule #36/#53); (b) this governance set (brief / RISK_REGISTER / Operational #58)
  that **documents** the scrub by naming the old token.
- `RISK_REGISTER.md` exists (R1–R6). Rule #43 backup clause present; #57 + #58 present;
  #55/#56 reserved.

## 6. What's NOT in this commit (scope boundary)
- **No code / test / ENGINE_VERSION change.** The brittle version-pin in
  `test_sprint_2p22p0a5_request_budget.py` (RISK_REGISTER R6) and the residual code-side
  "VPS 4" method-labels (~12 .py sites) are **deferred to the next code sprint** (this is
  docs-only).
- **Historical CHANGELOGs / READMEs / Phase-0 analyses are NOT rewritten** (deliberate —
  preserve the audit trail). The literal DoD "ZERO `VPS 4` in *.md" is met for runtime docs;
  history is preserved by design.
- **Not pushed.** Rides the next code sprint's `heroku` + `origin` push (Rule #43 ritual).
