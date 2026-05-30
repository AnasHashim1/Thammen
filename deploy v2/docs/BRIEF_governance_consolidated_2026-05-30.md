# BRIEF — Governance Consolidation (2026-05-30)

> **Type:** docs-only (no `ENGINE_VERSION` bump, no code change). **ONE commit, TWO labeled
> scopes:** A = artifact-accuracy reconciliation; B = process hardening. **Not pushed** —
> Rule #32; batches into the next code sprint's push.
> **Governing principle:** MEASURE, do not trust any number in the brief — every value
> below was verified against the live engine / git / code at execution time.

---

## §0 · Definition of Ready — MEASURED (2026-05-30)

| Fact | MEASURED value | Source |
|---|---|---|
| Live engine | `thammen-sprint2p22p0a6-seed-getplot-dedup` | `curl /api/health` |
| api/health version | `3.1.0-sprint2.22.0a.6` | `/api/health` |
| Heroku release | **v145** | deploy log (this session) |
| Latest sprint | **2.22.0a.6** (Branch B lever 3, seed get_plot dedup) | ENGINE_VERSION |
| Latest CHANGELOG on disk | **v57** → this commit adds **v58** | `ls CHANGELOG_v*.md` |
| MoJ staleness | **150 days** (latest record 2025-12-31) | `/api/health` moj_freshness |
| git HEAD | `c77460f` (a6 deploy closeout), ahead of origin by 1 | `git log` / `status` |
| Operational_Rules highest in-file | **#53** (#41 placeholder, #44 folded into #43) | grep headers |
| Empirical E15–E20 | **all present in-file** | grep headers |
| RICS surface the CODE emits | MVU/standards = **VPGA 10 + VPS 6 + IVS 106** (RICS Red Book Global Standards, effective 31 January 2025); method labels still cite "VPS 4 §7/§3.4" in ~12 .py sites | grep `*.py` |

### Test suites — EXACT counts (measured this session, post-2.22.0a.6)
- aggregator `run_sprint_2p22p0a_suite.py`: **392 / 392** ✓
- security `test_sprint_2p16p17_security.py`: **15 / 15** ✓
- `test_sprint_2p22p0a3_surface_honesty.py`: **45 / 45** ✓
- broad `2p22p0_pre/run_regression_2p22p0a.py`: **48 / 49** — 1 file fails:
  `test_sprint_2p22p0a5_request_budget.py` (2 of its 17 assertions are **brittle EXACT-version
  pins** `ENGINE_VERSION==2p22p0a5` / `SPRINT_TAG==2.22.0a.5`, broken by the 2.22.0a.6 bump —
  the same anti-pattern Sprint 2.19.1 relaxed elsewhere). **Deterministic, NOT flaky; NOT a
  functional regression** (engine verified live on v145). Fix = relax the pins in a **future
  code sprint** (this commit is docs-only). Logged to `RISK_REGISTER.md`.
- **Self-correction (Rule #36):** the 2.22.0a.6 "broad 49/49 green" reported earlier was
  measured *before* the ENGINE_VERSION bump (regression ran one step before the bump);
  post-bump the brittle a5 pin fails → true post-bump count is **48/49**.

### `test_v2_modules.py` — formally OUT of the DoD (not a silent skip)
Requires `pytest`, which is **not installed** and **not in `requirements.txt`** (= requests,
beautifulsoup4, tabulate, fastapi, uvicorn, slowapi) and not used by the engine. It is
already formally excluded by the broad runner (`SKIP_FILES = {"test_v2_modules.py"}`,
"pytest-blocked"). Decision: **OUT** — no install, exclusion documented in CLAUDE.md DoD.

---

## §A · Artifact-accuracy reconciliation (executed)
1. **RICS scrub (live docs):** `VPS 4` removed from the 4 live governance docs (CLAUDE.md ×2,
   Custom_Instructions, Project_Instructions, Empirical_Findings ×3) → replaced with the
   code-emitted surface (standards framing → **RICS Red Book Global Standards, effective
   31 January 2025 — VPGA 10 + VPS 6 + IVS 106**; generic method/approach context → **RICS
   Red Book**). **Historical artifacts NOT rewritten** (audit-trail integrity, Rule #36/#53):
   CHANGELOG_v3/v8/v55, README_SPRINT1B.md, PHASE0_2p22p0a4_DISCLAIMER_MAP.md retain their
   point-in-time `VPS 4` text. ⟹ the literal DoD "ZERO hits in *.md" is met for **live docs**;
   ~10 historical hits are deliberately preserved (see §C deviation). Residual code-side
   `VPS 4` method-labels (~12 .py sites) = deferred **code** cleanup (Gate 2 / next code sprint).
2. **Measured-value refresh** of engine / Heroku vN / latest sprint / latest CHANGELOG /
   last-updated across the live headers.
3. **Custom_Instructions:** removed "Current latest = Sprint 2.16.12"; §3 test count +
   §5 MoJ-staleness updated to measured values.
4. **DoD test count single-sourced** in CLAUDE.md; other docs reference it.
5. **Roadmap** consolidated into one authoritative ROADMAP section (Project_Instructions);
   CLAUDE.md points at it.
6. **Rule #54 written in** (was memory-only "Multi-AI consult at sprint open").
7. **BROKERAGE SCRUB:** Anas's brokerage (Gardenia) is effectively **closed** — NOT a data
   source/dependency/pillar. All "brokerage-fed Confirmed Sales" / "brokerage pipeline" /
   "recalibration via brokerage closings" / "pending secretary" framing neutralized.
   **Sprint 2.16.16 / Confirmed Sales = DEFERRED INDEFINITELY (no viable internal source:
   secretary closed + brokerage closed).** T2 "broker" = ad-hoc only (not a stable feed);
   Stage-4 field check = broker-agnostic (any vetted broker).

---

## §B · Process hardening (executed)
1. **`docs/RISK_REGISTER.md`** created with 5 seeds.
2. **Rule #43 amended in place:** backup-push-to-origin made a standing part of the deploy
   ritual (not a per-time manual confirmation).
3. **New rules** (numbering reconciled — see §C): **#57** session-start ground-truth
   handshake; **#58** assumed-vs-actual operational-gap rule.

---

## §C · Numbering reconciliation (surfaced, not silently overwritten)
In-file highest before this pass = **#53**. Pending/reserved candidates collided with the
naive "next free":
- **#54** = Multi-AI consult at sprint open — was memory-only → **written in** this pass.
- **#55** = "ENV-VAR override audit pre-close" — **RESERVED / pending** (flagged in the brief);
  NOT written here, NOT reused.
- **#56** = "measure the dominant cost before committing scope" (Branch B brief §7) —
  **RESERVED / pending** Branch B full closeout; NOT written here.
- **#57**, **#58** = the two new rules this pass adds (first genuinely-free numbers after the
  reservations). A "Reserved numbers" note is added to Operational_Rules so #55/#56 are not
  silently reused.

---

## §D · Definition of Done
- `VPS 4` → zero hits in **live** docs (historical artifacts preserved by design, §C).
- No "Current latest = Sprint 2.16.12".
- No "brokerage-fed" / "pending secretary"; Sprint 2.16.16 = deferred indefinitely (no source).
- `RISK_REGISTER.md` exists with 5 seeds.
- Rule #43 has the backup-in-ritual clause; #57 + #58 present; #55/#56 reserved.
- ONE docs-only commit; next `CHANGELOG_v58.md`; **no push**.
