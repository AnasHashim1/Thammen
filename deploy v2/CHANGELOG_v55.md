# CHANGELOG v55 — Sprint 2.22.0a.4: Disclosure & Framing Honesty

**Sprint:** 2.22.0a.4
**Engine version:** `thammen-sprint2p22p0a4-disclosure-framing-honesty`
**Sprint tag:** `2.22.0a.4`
**Production baseline before this Sprint:** `thammen-sprint2p22p0a3-arabic-surface-honesty` (Heroku v139)
**Files touched:**
- `evaluate_unified.py` — ENGINE_VERSION + SPRINT_TAG bump; `methodology_ar`
  headline collapsed to a single honest basis line; main-path
  `methodology_disclaimer_ar` (Layer A) removed (A→D fold).
- `test_sprint_2p22p0a4_disclosure_framing.py` — NEW, 17 assertions.
- `docs/PHASE0_2p22p0a4_DISCLAIMER_MAP.md` — NEW, the P0.1 + P0.2 read-only audit.
- `docs/MULTI_AI_VALIDATION_BATCH_2p22p0a4.md` — pre-existing (Question E re-use
  + Question F resolved 2026-05-28); referenced, not modified this session.
- `.smoke_2p22p0a4_villa.json` / `.smoke_2p22p0a4_apt.json` — local smoke captures.

**Push status:** **STOP** — push consent reserved for Anas (Rule #32). Not pushed.
**KICKOFF sign-off:** still pending Anas (`.kickoff_2p22p0a4/KICKOFF_2p22p0a4.md`).

---

## Why this matters

Direct continuation of 2.22.0a.3's epistemic-honesty line, one surface up: the
tool must not over-state its **authority/scope**. Two specific over-claims on
the user-facing methodology surface:

1. **The methodology headline claimed a method the engine does not run.** The
   live string read `AVM مبني على Sales Comparison Approach مع توفيق ثلاثي الطرق`
   ("…with three-way reconciliation"). Phase 0 (P0.2) proved the engine never
   blends the three approaches — the value is Sales Comparison alone, 100% of
   cases; cost/income are *convergence checks only*. "توفيق ثلاثي الطرق"
   overstated the mechanics. It also embedded Latin (`AVM`, `Sales Comparison
   Approach`) inside Arabic user text — a copy-standard violation.

2. **Redundant disclaimer layering.** The main-path `methodology_disclaimer_ar`
   (Layer A) duplicated the top-level `disclaimer` (Layer D, the canonical
   not-a-formal-valuation C4 string).

---

## Phase 0 — verify-first audits (read-only, before any edit)

Both documented in `docs/PHASE0_2p22p0a4_DISCLAIMER_MAP.md`.

### P0.1 — Disclaimer rendering map
Source-of-truth grep on `evaluate_unified.py` / `api.py` / `reasoning_trace.py`
/ `scope_of_service.py` (definition) × `index.html` (render). Result:

| Layer | Field | Renders in UI brief? |
|---|---|---|
| A | `methodology_disclaimer_ar` | **NO — JSON-only** (never referenced in index.html) |
| B | `muc_clause_ar` (formal VPGA 10/VPS 6/IVS 106) | YES (722–730) |
| C | vernacular MUC banner | YES |
| D | top-level `disclaimer` (short C4) | YES (1253) |
| D′ | `reasoning_trace.disclaimer` (long C4) | **NO — explicitly skipped** |
| E | `service_scope.disclaimer_ar` | YES (831) |

**Decisive finding:** in the *rendered* brief, A and D′ never show. The "4→2
disclaimer consolidation" is therefore mostly JSON hygiene, not user-visible
de-cluttering — which both narrows T2.8 and lowers its UI risk.

### P0.2 — Reconciliation-weighting documentation check
`val = primary['value']` (Sales Comparison alone). `_analyze_reconciliation`
(`:1688`) is a *status reporter*, not a blender — cost/income only produce a
convergence label (`spread_pct`), never enter the headline number. Module
docstring is explicit: the equal-weight three-way blend was a Sprint-1.a bug,
removed. **There is no weighting because there is no blend** → the bare
Sales-Comparison statement is the honest methodology line (KICKOFF branch
"undocumented weighting → plain language").

---

## What this patch does

### T-method (a + b) — methodology_ar headline honesty
`methodology_ar` (main path, `_build_unified_output`) →
```
'أساس التقدير هو منهج المقارنة بالمبيعات.'
```
A single honest basis-of-estimate line. Drops the misleading
`توفيق ثلاثي الطرق` reconciliation claim (a) AND the embedded Latin (b) — both
issues lived on the one string. Matches the completed multi-AI Resolution
(Path A / Amendment: universal bare line, dispatcher removed).

**Audit-trail correction (record accuracy):** the "three-branch dispatcher"
(status-aware `methodology_ar` off `reconciliation['status']`) was **never live
code**. It existed ONLY as the *proposed* shape in the Question F batch table
(`docs/MULTI_AI_VALIDATION_BATCH_2p22p0a4.md`) and was mistakenly treated as
production in methodology-side handoffs. Recon against `fc2d7da` confirmed the
actual code was a **single old string** (`'AVM مبني على Sales Comparison
Approach مع توفيق ثلاثي الطرق'`). So the Amendment was even cleaner than
described: single old string → single bare line (no dispatcher to collapse).

### T2.8 — disclaimer consolidation (JSON-merge-only, premise-corrected)
Per the completed multi-AI Resolution (A = JSON-only cleanup, fold into D; E
untouched). A **premise-check** before editing revealed the 6
`methodology_disclaimer_ar` sites are **heterogeneous** — only the main-path
site (`_build_unified_output`) duplicated D. The other 5 carry genuine
per-path methodology caveats (unsupported-category, hybrid-T2, asking-price
tool, income-path, first-version scope) and are **NOT** duplicates of D.
Action: removed the redundant **main-path** Layer A only; left the other 5
intact. A-site count 6 → 5. (Had the kickoff's "delete A from 6 sites" been
executed literally, it would have destroyed 5 legitimate caveats and broken
test c3.)

**T2.8 scope delta vs the original plan (documented for record):** the planned
T2.8 was "canonical D (C4) across 9 sentence-form sites + A/C JSON cleanup."
The executed T2.8 is a **deliberate subset** — only the Layer-A cleanup
(6→5) ran. Reasons:
- **Layer D (C4, 9 sites): already canonical** from Sprint 2.22.0a.2 (the C4
  reframe). This session made **zero** edits to D-sites — the diff touches only
  `methodology_ar` + the main-path A block in `evaluate_unified.py`; no
  `disclaimer`/C4 strings changed (the C4-lock×5 regression pin passes
  unchanged). Nothing to do here.
- **Layer C (`banner_ar`): cleanup found unnecessary** — per the batch doc's
  Question E (Option α), `banner_ar` at index.html:496 is the *data-freshness*
  banner (name collision), NOT a vernacular MUC layer. No frontend surface to
  remove. Not touched this session.
- `index.html` was **not edited** this session (confirmed: not in the
  tracked-changed set).

### Provenance handling — corrected mid-session (Rule #36 / #39)
The "automated AVM per RICS VPS 4" provenance previously lived inside Layer A
(JSON-only, never visible). It is **dropped from the visible headline**, NOT
promoted — honoring the Resolution's "reduce, not add" theme. (An interim edit
this session added it as a 2nd headline sentence on a mistaken recommendation;
on reading the completed multi-AI Resolution it was reverted. RICS framing still
surfaces in the MUC card; a VPS-4 provenance on a secondary expandable surface
is deferred — see the batch doc's "Deferred — secondary-surface variants".)

### Unchanged (scope discipline)
- **Layer D** (top-level `disclaimer`, short C4) — canonical not-a-formal-
  valuation, **C4 verbatim lock preserved** (≥5 sites).
- **Layer E** (`service_scope.disclaimer_ar`) — rename to a methodology field
  **DEFERRED** (Rule #47: rename is its own pass; render-coupled at index.html:831).
- D′ / api.py disclaimer variants (own endpoints) — out of brief-path scope.
- Latin in *other* methodology strings (GIS/MoJ/PropertyFinder/Cap Rate/RICS
  Income Approach) — out of single-purpose scope (Rule #38); future copy pass.

---

## Verification — empirical evidence

**4 harnesses + new isolated test, all GREEN:**

| Harness | Result |
|---|---|
| `run_sprint_2p22p0a_suite.py` (pinned 392 aggregator) | **392/392 PASS** |
| `test_sprint_2p16p17_security.py` | **15/15 PASS** |
| `test_sprint_2p22p0a3_surface_honesty.py` (standalone) | **45/45 PASS** (C4 lock count=5) |
| `2p22p0_pre/run_regression_2p22p0a.py` (broad sweep) | **48/48 files PASS** (auto-picked up new test) |
| `test_sprint_2p22p0a4_disclosure_framing.py` (NEW) | **17/17 PASS** |
| `test_sprint_2p22p0a2_c3` / `_c5` (the A-referencing tests) | **8/8 + 5/5 PASS** |

The 392 aggregator pin was **not** bumped — the new test runs standalone (same
convention as the 2.22.0a.3 test), and assertions in the 7 pinned files were
not changed.

**Local in-process smoke (engine 2.22.0a.4):**

| Address | Path | Result |
|---|---|---|
| 56/565/21 villa | main `_build_unified_output` | `methodology_ar` = bare line; main-path Layer A **absent** (fold confirmed live); D + C4 intact |
| 52/903/90 apartment | early-return (unsupported class) | preserved Layer A (@1932) + D render correctly; engine 2.22.0a.4 |

Captures: `.smoke_2p22p0a4_villa.json`, `.smoke_2p22p0a4_apt.json`.

---

## Multi-AI validation (Rule #54)
- **Question E** (disclaimer consolidation): re-used the 2.22.0a.3 batch answer.
- **Question F** (methodology phrase): resolved 2026-05-28 (GPT-5 + Gemini,
  verbatim in `docs/MULTI_AI_VALIDATION_BATCH_2p22p0a4.md`). Outcome: universal
  bare line, "reduce not add", silence on approaches not applied. This Sprint
  ships exactly that.
- **Citation status:** OPEN — both models cited VPS 3 (not VPS 6); code-comment
  cites the genus only (RICS Red Book 2024 / IVS 106) pending a targeted PDF
  lookup. Outcome unaffected; only comment specificity is.

---

## Deployment (when Anas signs + consents — Rule #32 / #43)

Stage **only** this Sprint's files (NOT the pre-existing unrelated tracked
changes — `backtest/README.md`, `probe_burst_baseline.py`,
`probe_docs_exposure.py`, and the 3 deletions — which predate 2.22.0a.4 and
should be handled separately, per Rule #32 "add specific files by name"):
```
git add "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2p22p0a4_disclosure_framing.py" "deploy v2/docs/PHASE0_2p22p0a4_DISCLAIMER_MAP.md" "deploy v2/docs/MULTI_AI_VALIDATION_BATCH_2p22p0a4.md" "deploy v2/CHANGELOG_v55.md" "deploy v2/.smoke_2p22p0a4_villa.json" "deploy v2/.smoke_2p22p0a4_apt.json"
git commit -m "Sprint 2.22.0a.4: Disclosure & Framing Honesty"
git subtree push --prefix "deploy v2" heroku master
```

**Commit-message body must record two on-record facts:**
1. **Bundled scope** — T-method + T2.8 shipped together. This is a deviation
   from the methodology-side T-method-only recommendation, but it **matches the
   original KICKOFF scope** (both items were in `KICKOFF_2p22p0a4.md`). Bundle
   is justified: both are the same single-purpose framing-honesty theme, both
   touch the same `methodology_ar`/Layer-A region of `_build_unified_output`
   (Rule #38 — legitimate same-region bundle, not unrelated fixes).
2. **Amendment per Rule #39** — `methodology_ar` collapsed to a constant bare
   line (vs the KICKOFF's proposed status-aware branches), justified in
   `docs/MULTI_AI_VALIDATION_BATCH_2p22p0a4.md` §Rule #39.

Kickoff to sign = on-disk `.kickoff_2p22p0a4/KICKOFF_2p22p0a4.md` (v1) + the
Amendment via Rule #39 in the batch doc. The chat-held "v2" kickoff is gone and
is superseded by the batch-doc Amendment endpoint.

## Verification curl (post-deploy)
```
curl -s -X POST https://thammen.qa/api/evaluate -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}" > out.json
findstr /C:"أساس التقدير هو منهج المقارنة بالمبيعات" out.json
```

## What's NOT in this patch
- E (`service_scope.disclaimer_ar`) field rename → deferred (Rule #47).
- VPS-4 provenance on a secondary expandable surface → deferred sub-sprint.
- Latin in non-headline methodology strings → future copy-standard pass.
- GPT-B multi-factor evidence gate, 2.23.x stage/authority work, Bug A7 → own tracks.
