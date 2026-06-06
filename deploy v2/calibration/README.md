# Calibration Pipeline (Sprint B-2 prep — INTERIM, built while B-2 is PARKED)

> **Status:** internal tooling. **Engine UNCHANGED** (a25 / Heroku v164). **B-2 active
> mechanism stays PARKED** (Gate-2 SIGNED, Fork#2 = WAIT-for-n≥20 — see
> `docs/BRIEF_SprintB2_mechanism_elicitation_SIGNED.md`). Nothing here ships to Heroku,
> changes a value, or builds the B-2 mechanism. This is the **plumbing** so that when real
> ground-truth (GT) files arrive, the B-2 calibration is fast and disciplined.
>
> **Boundary:** ②③ below are **read-only / no gate** (internal). ① (the in-app capture form)
> is **user-facing** → needs Anas's copy (Gate 2) + a push (Gate 1) and is **not built yet**.

## Why this exists

R7 (built-type / age / condition over-/under-anchor) is a **calibration + missing-mechanism**
problem, not a UX-prominence one (`docs/PHASE0_B2_condition_recon.md`). The fix (B-2) cannot be
calibrated until the **Confirmed-Sales GT-2 corpus reaches n≥20** (the binding constraint). This
pipeline turns "GT files arrive" into "run one command → see the residual + bias + Lever-2
what-if," with the n<20 discipline baked in.

## The three parts

| # | What | Gate | Built? |
|---|---|---|---|
| **②** | **GT corpus** — canonical, multi-source, B-2-ready schema (`corpus_schema.py` + data). Tags sale-GT vs opinion-GT distinctly. Seeded V001/V002/V003. | none (internal) | ✅ this session |
| **③** | **Validation harness + Lever-2 what-if** (`residual_harness.py`, `lever2_simulation.py`) — runs the REAL live engine over the corpus → residual per property + per E4 stratum + systematic bias; **read-only Lever-2 simulation** (down-re-anchor toward the a21 land floor) to de-risk Lever 2. | none (read-only) | ✅ this session |
| **①** | **Light capture form** — in-app fields (actual price + reservation) → paste-ready corpus line via WhatsApp/clipboard. **NO server storage** (capture stays DORMANT; no PII in URL). | **Gate 2 copy (Anas) + Gate 1 push** | ⏳ awaiting Anas's copy |

## Ground-truth tiers + the discipline (from `docs/validation/VALIDATION_LOG.md`)

| Tier | Source | Calibration-eligible? |
|---|---|---|
| **GT-1** `valuer_opinion` | valuer-signed (Stage 5) | ✅ (gold benchmark, esp. `luxury_new`) |
| **GT-2** `confirmed_sale` | closed transaction (cohort / 2.16.16 / cited by a valuer) | ✅ |
| **GT-3** `asking` | active listing — asking ≥ sale | ❌ directional only |
| **GT-4** `broker` | broker verbal / informal | ❌ directional only |

**HARD discipline:** entries are *data points*, not calibration claims. **No rule / weight /
coefficient** is derived until **n ≥ 20 within GT-1∪GT-2**. The harness filters to GT-1/GT-2 for
the bias read; GT-3/GT-4 are reported as directional context only. (E-rules + brief §6 + IVS 104
completeness.) **Don't conflate** confirmed sales with valuer opinions.

## Privacy / PDPPL

The corpus holds **privately-sourced transactional data** (confirmed-sale prices tied to PINs).
It is **internal reference data only** — never exposed via the product (Heroku/API), and **flagged
for the pending PDPPL counsel review**. The real-data file `gt_corpus.local.json` is **gitignored
(local-only)**, consistent with `docs/validation/VALIDATION_LOG.md` being untracked. Only the
code + the structure-only `gt_corpus.template.json` are committed.

## Use

```bash
# seed / inspect the local corpus (already seeded V001-V003 on this machine)
python calibration/corpus_schema.py            # prints a summary of the loaded corpus

# run the residual + bias + Lever-2 what-if report against the LIVE engine (read-only HTTP)
python calibration/residual_harness.py         # writes calibration/reports/residual_report_*.md

# pure self-check (no network): loader round-trip + Lever-2 simulation math
python calibration/selfcheck_calibration_pipeline.py
```

`thammen_estimate` + `residual` are **computed live at run time**, never stored stale (engine
values drift across sprints — storing them would mislead). When GT files arrive: add rows to the
corpus (confirmed transactions → `confirmed_sale`; valuer final figures → `valuer_opinion`), then
re-run the harness.

## Boundaries (do not cross without a gate)
- **No engine / method change.** No Heroku for ②③.
- **No calibrated coefficient** until n≥20 GT-2 (this tooling *measures*; it does not *fit*).
- ① is **frontend-only, no server storage** — do NOT build the stored-DB capture (gated:
  PDPPL + gate-11 security pass; that is the separate a15 ACTIVATION track, R11).
