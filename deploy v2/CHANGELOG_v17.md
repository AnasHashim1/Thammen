# CHANGELOG — Sprint 2.12: Backtest Harness

**Engine version:** `thammen-sprint2p11-context-preservation` (unchanged)
**Date:** 2026-05-13
**Files changed:** **none** in deployed engine; adds new `backtest/` folder
**Builds on:** Sprint 2.11 (v16)

---

## Why this matters

Every Sprint from 2.7 through 2.11 made claims about user benefit — Sprint 2.7
"surfaces data staleness", 2.9 "fixes R2 zoning render", 2.11 "preserves
context in 15-25% of addresses". None of these claims came with a measurement.

A field audit on 2026-05-13 (the Sprint 2.11 work session) surfaced 10
concrete bugs, but more importantly revealed that **Thammen has no way to
answer the most basic question**: how accurate are its predictions?

Without a baseline, every future improvement is faith-based. The Phase 1
roadmap (Sprint 2.15 classifier rewrite, Sprint 2.20 comparable adjustment
grid, etc.) needs a yardstick or its outcomes are unmeasurable. Phase 0
must come first.

This Sprint is the yardstick.

## Root cause

There is no root cause to fix — this Sprint adds capability, not a fix. The
"cause" is structural: AVM development without backtesting is conjecture.
RICS-aligned AVMs in mature markets (Zoopla, Zillow Zestimate, Property
Monitor) publish quarterly accuracy reports for exactly this reason —
calibration is the discipline.

## What this patch does

### New folder: `backtest/`

```
backtest/
├── README.md          (~140 lines: usage, target metrics, growth guidance)
├── golden_set.csv     (6 seed rows from Sprint 2.11 audit)
├── backtest.py        (~330 lines: harness + report renderer)
├── reports/           (gitkeep — outputs go here, gitignored)
│   └── .gitkeep
└── .gitignore         (excludes individual reports — they may hold real sales data)
```

### Two-mode design

The harness supports two complementary measurement modes that coexist in
one CSV:

| Mode | CSV trigger | Measures |
|---|---|---|
| Pipeline | row has no `sale_price_qar` | reliability, latency, type-match rate, district-resolved rate |
| Accuracy | row has `sale_price_qar` filled | MAE, MAPE, %within±10%, %within±20%, actual-within-predicted-range |

Pipeline mode runs immediately on the seed. Accuracy mode unlocks the
moment a row with a confirmed sale price is added.

### Seeded with 6 properties from the Sprint 2.11 audit

All six are **pipeline-test rows** (no `sale_price_qar` yet):

| # | Address | Why |
|---|---|---|
| 1 | 52/903/90 | Al-Luqta R2 villa — Sprint 2.9 reference, main pipeline |
| 2 | 51/835/17 | Al-Gharafa large compound — DCF fast path |
| 3 | 70/1278/34 | Roudat Al Hamama villa — sparse-MoJ district |
| 4 | 27/220/53 | Umm Ghuwailina commercial — out_of_scope path |
| 5 | 69/305/201 | Lusail "palace" — known classifier bug A1 |
| 6 | 55/290/10 | Al-Maradh villa — standard pipeline |

This is the **minimum viable regression set**. Every Sprint after 2.12
should run this and ensure no regression in the pipeline metrics.

### Report rendering

Each run emits two files in `backtest/reports/`:

1. **`backtest_YYYYMMDD_HHMMSS.csv`** — raw per-row data (all fields)
2. **`backtest_YYYYMMDD_HHMMSS.md`** — Markdown report with sections:
   - Pipeline reliability (success rate, latency mean/p95, type-match)
   - Accuracy (only if rows with `sale_price_qar` present)
   - Stratification by `asset_type_returned`
   - Stratification by `district_returned`
   - Outliers (worst pct_error)
   - Per-record detail table

### No engine change

`evaluate_unified.py`, `api.py`, `index.html`, `qatar_gis.py` — all
unchanged. `ENGINE_VERSION` remains `thammen-sprint2p11-context-preservation`.
This is intentional: the engine is the system under test; the engine must
not change in the same Sprint as the measurement instrument is introduced.

The Sprint 2.10 rule "bump version with each Sprint" is **not violated**
because Sprint 2.12 is a tooling addition, not an engine release. Section 3
of the Custom Instructions is updated separately to clarify this carve-out.

---

## Verification — empirical evidence

Live run against `https://thammen.qa/api/evaluate/details` on 2026-05-13
15:54 UTC, immediately after Sprint 2.11 deploy:

```
Loaded 6 entries from golden_set.csv
API: https://thammen.qa/api/evaluate/details
------------------------------------------------------------------------------
[ 1/6] 52/903/90    ✓ [standalone_villa] pred=2,000,000  (24.72s)
[ 2/6] 51/835/17    ✓ [compound_large]  no_val (insufficient_data)  (3.28s)
[ 3/6] 70/1278/34   ✓ [standalone_villa] pred=9,700,000  (25.42s)
[ 4/6] 27/220/53    ✓ [commercial]      no_val (out_of_scope_v1)   (3.27s)
[ 5/6] 69/305/201   ✓ [palace]          no_val (insufficient_data) (4.10s)
[ 6/6] 55/290/10    ✓ [standalone_villa] pred=2,700,000  (23.22s)
------------------------------------------------------------------------------
SUMMARY
Records:     6 (success: 6, errors: 0)
Valuations:  3 returned, 3 no-value (fast/oos)
Latency:     mean=14.0s  p95=25.42s
Type match:  100.0%
```

This is now the **baseline**:

| Metric | Baseline value (2026-05-13) | Target |
|---|---|---|
| Pipeline success rate | 100% (6/6) | maintain |
| Type-match rate | 100% (6/6) | maintain |
| Mean latency | 14.0s | < 15s (Sprint 2.18 target) |
| P95 latency | 25.4s | < 20s |
| Records returning valuation | 50% (3/6) | Sprint 2.29 (apartments) raises this |
| MAPE | — (n=0) | unlock by adding real sales |
| %within ±10% | — | > 70% (long-term, Phase 2) |

### Confirmed bugs that the baseline already exposes

- **Bug A6 (latency near Heroku timeout)** — P95 is 25.4s, only 4.6s
  below the 30s timeout. Two of three full-pipeline cases (52/903/90 and
  70/1278/34) ran in 24.7s and 25.4s respectively. Any property with a
  few extra landmarks could push past the cap. Confirms the urgency of
  Sprint 2.18.

- **Pipeline coverage observation** — 50% of the seed (3/6) returned no
  valuation. For the full Qatar market this share is much smaller, but
  the seed is intentionally biased toward edge cases (compound, palace,
  commercial). After Sprint 2.29 (MME apartment integration), this
  number should improve materially.

- **Spread between districts** — Roudat Al Hamama predicted 9.7M QAR
  for a 1,152 m² plot (~8,400 QAR/m²); Al-Luqta predicted 2.0M for
  467 m² (~4,280 QAR/m²); Al-Maradh predicted 2.7M for 900 m²
  (~3,000 QAR/m²). The 2.5× per-m² premium for Roudat Al Hamama is
  worth a sanity audit — is it real, or a small-n MoJ artifact?
  Captured as a Phase 1 finding rather than a 2.12 issue.

---

## Deployment

Engine code is unchanged. The Sprint can be deployed (to keep the repo
synchronized) OR kept local. Either works.

```cmd
cd /d "C:\Thammen\deploy v2"
tar -xf "%USERPROFILE%\Downloads\sprint2p12-backtest-harness.zip"
dir backtest
```

```cmd
git add backtest CHANGELOG_v17.md
git commit -m "Sprint 2.12: Backtest harness (baseline measurement infrastructure)"
git push heroku master
```

The `git push heroku master` line is **optional** — the backtest tooling
runs against the production API, not from inside Heroku. Skipping the push
saves a redeploy cycle. Keep the local commit for traceability.

## First run

```cmd
cd /d "C:\Thammen\deploy v2\backtest"
python backtest.py
```

Expected: 6 properties, ~90 seconds total, 0 errors. Look at the
generated `reports/backtest_YYYYMMDD_HHMMSS.md` — that's your baseline.

## What's NOT in this patch (intentional Sprint 2.12 scope)

- **Real accuracy measurement** — requires populating `golden_set.csv`
  with confirmed sale prices. Out of scope for this Sprint; the
  README explains how to add them. This is the most impactful follow-up
  any non-Sprint contributor can do.

- **Engine fixes from the Sprint 2.11 audit** — bugs A1–A10 catalogued in
  the audit are tracked for Phase 1 Sprints (2.15–2.19). They are NOT
  fixed here because they should each be measured against this baseline
  to prove their effect.

- **Continuous integration** — the harness runs manually. CI integration
  (run automatically on push) is a future Sprint, conditional on the
  golden set growing past ~20 records.

- **Imagery-based ground truth** — comparing predicted condition/age vs
  historical imagery is its own discipline. Phase 5 (Sprint 2.39).

- **Project document update** — shipped alongside this Sprint as a
  separate deliverable (the user replaces it in the Claude Project
  knowledge manually). The `.md` is at the top of the zip outside
  `backtest/` because it doesn't belong in the deploy folder.

## Methodological note

This is the **first Sprint that doesn't change user-facing behavior**.
Section 15 of the Project Instructions asks: "Does the regular user
benefit from this change?" The honest answer here is *not directly,
not immediately*. The user benefits **transitively** from every future
Sprint being measurable. Skipping Phase 0 means every future claim of
improvement is unverifiable — which is the bigger user-harm.

The trap to avoid: never let Phase 0 expand into Phase 0.5 with no
shipping. The harness here is intentionally minimal — 6 seed rows, no CI,
no dashboard. It works. Ship it. Use it as the baseline for Sprint 2.15
and onward. Grow the golden set in parallel; do not block Phase 1 on it.
