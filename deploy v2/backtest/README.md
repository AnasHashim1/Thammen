# Thammen Backtest Suite

Two complementary measurement tools. Sprint 2.13 expanded Sprint 2.12 by
adding **market-side** measurement on top of the engine-side reliability
test.

## The pivot from 2.12 → 2.13

Sprint 2.12 (`backtest.py`) was designed to measure Thammen against
**confirmed sale prices**. We don't have those. EMPIRICAL_FINDINGS (2026-05)
established that:

- **Villa** asking prices are contaminated by non-economic premiums
  (proximity to family, sentimental value). Asking premium for villas is
  +70.2% — far too noisy to use as truth.
- **Land** asking premium is +13.6% globally, with a narrow per-area
  band documented in EMPIRICAL_FINDINGS. Land is fungible — no one pays
  extra to own a specific vacant plot. So **land listings ARE a valid
  truth source** with a documented, narrow premium expectation.

Sprint 2.13 keeps the engine harness (still works for any test row you add)
and adds a separate market-side tool that compares current arady land
listings against MoJ over the EMPIRICAL_FINDINGS bands.

This honors EMPIRICAL_FINDINGS Rule E3: listings stay diagnostic. They
inform our confidence in the engine; they never become engine input.

## The two tools

### `backtest.py` — engine reliability (Sprint 2.12)

Calls `/api/evaluate/details` on the 6 rows in `golden_set.csv` and
measures:
- pipeline success rate
- mean / p95 latency
- asset_type / district correctness
- accuracy (only if a row has confirmed `sale_price_qar` — currently none do)

Use this to catch regressions: every time the engine changes (Sprints 2.15+),
re-run and compare to the prior baseline.

```cmd
cd /d "C:\Thammen\deploy v2\backtest"
python backtest.py
```

### `backtest_market.py` — market vs MoJ (Sprint 2.13)

Reads `arady_lands_*.csv` + the local `moj_weekly.csv`, computes the asking
premium per listing, and buckets results against EMPIRICAL_FINDINGS bands:

| Bucket | Band | Meaning |
|---|---|---|
| ✅ normal | 0–20% | within documented asking-premium norm |
| ⚠️ investigate | 20–25% | borderline — check for premium features |
| 🔴 red flag | >25% | stock mismatch suspected (Rule E5) |
| 🟦 below MoJ | <0% | unusual — motivated seller or noise |
| ⚪ insufficient MoJ | — | no comparable transactions; **coverage gap** |

```cmd
cd /d "C:\Thammen\deploy v2\backtest"
python seed_from_arady.py
python backtest_market.py
```

Default paths:
- arady CSV: latest `arady_lands_*.csv` in this dir
- MoJ CSV: `..\moj_weekly.csv` (one level up — your deploy v2 root)

Override:
```cmd
python backtest_market.py --moj path\to\moj.csv --arady path\to\arady.csv
```

## What "good" looks like

The first 2026-05-13 baseline:
- Overall median premium = **+14.4%** ✓ (EMPIRICAL_FINDINGS baseline: +13.6%)
- 12/23 measurable listings in ✅ normal band (52%)
- 7/30 in ⚪ insufficient MoJ — coverage gaps to investigate
- 7/30 in 🔴 red flag — concentrated in الرويس (3) and الصخامة (2)

Future Sprints that improve coverage or methodology should move:
- 🔴 red_flag count **down** (if our handling of corner/landmark plots improves)
- ⚪ insufficient_moj count **down** (Sprint 2.29 MME integration helps here)
- Overall median premium **stay near 14%** (it's a market property, not a Thammen property)

## Files in this folder

```
backtest.py                  Engine reliability harness (Sprint 2.12)
golden_set.csv               6 known-good addresses for engine harness
backtest_market.py           Market-vs-MoJ comparison (Sprint 2.13)
seed_from_arady.py           Refresh arady listings from the web
arady_lands_YYYY-MM-DD.csv   Snapshot of current arady listings
reports/                     Output reports + raw CSVs (gitignored)
README.md                    This file
.gitignore                   Excludes individual reports from VCS
```

## Refresh cadence

| Tool | When to re-run |
|---|---|
| `backtest.py` | After every engine Sprint (2.15+) to catch regressions |
| `seed_from_arady.py` | Weekly or monthly — listings change |
| `backtest_market.py` | After every `seed_from_arady` refresh + whenever MoJ data updates |

If MoJ stops publishing (currently 133 days stale), the market report
becomes stale too. The window stays 24 months from today so until the
gap exceeds ~24 months, results are still meaningful.

## Coverage gaps revealed by 2026-05-13 baseline

The 7 "insufficient MoJ" listings in the first run highlight districts
where the engine has **no MoJ comparables** in the last 24 months:

- ام العمد (zone 71) — only one bracket covered
- اسلطة الجديدة (zone 40) — no land transactions
- نعيجة (zone 44)
- الجريان (zone 70)
- لوسيل (zone 69) — apartments dominate; raw land scarce
- المعمورة (zone 56)
- الريان القديم (zone 52) — large-bracket gap

For these, Thammen will rely on:
- Building approach + cost data when available
- Fallback to broader brackets or area-aggregated data
- Or return "insufficient data" (Sprint 2.11 behavior)

These gaps are **measured**, not assumed. That's the value of the harness.
