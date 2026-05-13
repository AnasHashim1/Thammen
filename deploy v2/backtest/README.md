# Thammen Backtest Harness

Measures Thammen's reliability and accuracy by running a curated set of
properties through the live API and comparing results to known truths.

Sprint 2.12 deliverable. Engine unchanged; this is **measurement infrastructure**
that every Sprint after 2.12 will use to prove its claims.

## What this measures

Two complementary modes coexist in `golden_set.csv`:

| Mode | Trigger | Measures |
|---|---|---|
| **Pipeline** | row has no `sale_price_qar` | reliability, latency, asset_type/district correctness |
| **Accuracy** | row has `sale_price_qar` filled | MAE, MAPE, %within±10%, %within±20%, actual-within-range |

The seed `golden_set.csv` ships with **6 pipeline-only rows** from the
Sprint 2.11 field audit. Accuracy mode unlocks the moment you add a real
sale.

## Targets (RICS-aligned aspirations)

| Metric | Goal |
|---|---|
| MAPE | < 10% (RICS-aligned AVMs) |
| % within ±10% | > 70% |
| % within ±20% | > 90% |
| Type match rate | > 95% |
| Mean latency | < 15s |
| Success rate | > 98% |

These are **directional**, not contractual. The first run establishes a
baseline; every Sprint after 2.12 should move the needle in one direction.

## Usage

```cmd
cd /d "C:\Thammen\deploy v2\backtest"
python backtest.py
```

By default, hits `https://thammen.qa`. Override with an env var to test a
local server:

```cmd
set THAMMEN_API=http://localhost:8000
python backtest.py
```

Outputs to `backtest/reports/`:
- `backtest_YYYYMMDD_HHMMSS.csv` — raw per-row data
- `backtest_YYYYMMDD_HHMMSS.md` — rendered report (open in any editor)

The script is idempotent; re-running creates fresh timestamped reports.
It does not touch `golden_set.csv` or any other file outside `reports/`.

## Growing the golden set

The single most impactful thing you can do post-Sprint-2.12 is **add real
sales** to `golden_set.csv`. Even 5 confirmed sales unlock real accuracy
measurement. 30+ gives statistically meaningful confidence intervals.

**Required columns for a real-sale row:**
- `zone`, `street`, `building` — full QARS address
- `sale_date` — YYYY-MM-DD
- `sale_price_qar` — confirmed price (not asking price)
- `actual_asset_type` — one of `standalone_villa`, `palace`, `compound_small`,
  `compound_large`, `tower`, `apartment_building`, `raw_land`, `commercial`,
  `industrial`, `agricultural` (matches Thammen's vocabulary)
- `evidence_source` — *where* you got the price (e.g. "MoJ_PIN_X",
  "FGRealty_listing_sold_2025", "personal_knowledge", "broker_report")

**Optional columns** (improve test depth):
- `rental_income` — actual monthly rent (if known)
- `asking_price` — listing price before sale (to test gap analysis)
- `floors`, `building_age_years`, `basement` — sent to
  `/api/evaluate/details` for a deeper test

Leave non-applicable cells empty. The parser handles missing fields.

### Where to source real sales

In rough order of reliability:

1. **MoJ records you can geolocate** — When you have a MoJ record AND you
   know which specific property it refers to (via personal knowledge, broker
   confirmation, or imagery match). High quality.
2. **FGRealty / PropertyFinder "sold" listings** — When platforms publish
   final sale prices. Lower volume but high quality.
3. **Personal investment knowledge** — Anas's own transactions or those of
   his network. Highest quality if the sale price was actually confirmed.
4. **Public auction records** — Some Qatar auctions publish final prices.
   Quality varies.

**Do NOT use asking prices as actual prices.** That biases the test toward
matching listings, not transactions. Use them only in the `asking_price`
column.

## Stratification

The report breaks down metrics by:
- `asset_type_returned` (what Thammen classified it as)
- `district_returned`

This is how you find **systematic** errors. If MAPE is 8% overall but 35%
in lusail_marina, that's the next Sprint target.

## What this Sprint does NOT do

- It does not measure inspection-related accuracy (we cannot inspect)
- It does not compare against certified-valuer reports (we don't have any)
- It does not run automatically on schedule — manual invocation only
  (CI integration is a future Sprint)
- It does not change any engine behavior — engine remains at Sprint 2.11

## Privacy / data handling

`golden_set.csv` may contain identifying information about specific
transactions. It is checked into the repo but **should not be shared
externally**. Treat it as confidential. The `reports/` folder is
gitignored (see `.gitignore` in this directory) so individual reports
stay local unless explicitly committed.

## Troubleshooting

**`HTTP 403: Forbidden`** — the API rejects requests without a proper
`User-Agent`. The harness already sends one (`Thammen-Backtest/2.12`), so
this shouldn't happen on production. If it does, check Cloudflare/WAF
rules on the production host.

**`HTTP 429: Too Many Requests`** — the rate limiter triggered. The harness
already throttles to 0.5s/request. If you have >100 rows, raise
`THROTTLE_S` in `backtest.py` to 1.0.

**Latency > 30s on some rows** — full pipeline borderline-overruns
Heroku's timeout. Tracked as bug A6 in Sprint 2.11 audit; a future Sprint
will async-ify the slow paths.

**`status: error` with timeout** — same as above. The row is recorded as
failed so success rate reflects reality.
