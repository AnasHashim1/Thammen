# Source Exclusions — Permanent and Conditional Bars

> **Purpose:** catalogue every external data source the engine **does not** call (or no longer calls), with reason and substitute. Complements `Empirical_Findings.md` Rule E8 (tier weighting — T5 excluded) by recording *which* sources are T5 and *why*.
>
> **Scope:** real-estate market data sources only (listings, transactions, rentals). Government endpoints (MoJ, MME, sak.gov.qa Mthamen) are governed separately via `Project_Instructions.md sec 20-21` (smoke-test discipline, decision logs).
>
> **Promotion to Rule:** when an exclusion is empirically derived (e.g., a source shows ≥10% systematically wrong data), the rationale also lives in `Empirical_Findings.md`. This file is the **operational ledger** — what to NOT call from production code — while empirical findings are the **methodological evidence**.

-----

## Permanent exclusions (T5 — never call from production)

### `bayut.qa`

```
Status      Permanent exclusion (Rule E8 T5)
Reason      Listing aggregator with mixed Qatar/Saudi/UAE inventory. Many Qatar
            listings are syndicated copies of arady / PropertyFinder content
            with delayed timestamps, occasional price corruption, and no
            authoritative seller-of-record. Mixing this stream with vetted T2
            sources would contaminate the median.
Substitute  PropertyFinder + arady + FGRealty + Steps + QatarSale as T2
            sources (see Empirical_Findings.md Rule E8 tier mapping).
First logged 2026-05 audit pass (Sprint 2.10 stratification work).
```

### `mzadqatar.com`

```
Status      Permanent exclusion (Rule E8 T5)
Reason      Auction-listing site dominated by speculative aspirational prices
            and bid sniping artifacts. Median is structurally inflated and
            statistically incompatible with the realised-transaction MoJ
            baseline. Including it in the T2 mix biases medians upward
            without adding signal.
Substitute  PropertyFinder + arady + FGRealty + Steps + QatarSale.
First logged 2026-05 audit pass (Sprint 2.10 stratification work).
```

### `huzoom.lusail.com`

```
Status      Permanent exclusion
Reason      Next.js 13+ Single-Page Application served via Cloudflare with a
            bot deny-list that blocks every common-crawl / LLM-research user
            agent: ClaudeBot, GPTBot, CCBot, Amazonbot, Applebot-Extended,
            Google-Extended, meta-externalagent, CloudflareBrowserRenderingCrawler.
            Direct HTTP fetch returns the SPA skeleton (HTML shell + JS
            bundle pointers), not rendered listings. No public read API.
Headless    A Playwright/Selenium runtime *could* render the SPA, but:
runtime       1. Heroku Python buildpack has no headless-browser support
                 (would require a separate dyno/runtime).
              2. The bot deny-list applies at the Cloudflare edge — even a
                 real browser session from a Heroku IP would be screened.
              3. The huzoom.lusail.com inventory is **already carried** by
                 FGRealty / PropertyFinder / Steps / QatarSale as syndicated
                 listings, so the marginal coverage gain is approximately
                 zero.
Substitute  FGRealty + PropertyFinder + Steps + QatarSale as T2/T3 sources
            (Huzoom inventory is syndicated to all four).
First logged 2026-05-26 (Claude.ai Huzoom Lusail learning session, PIN
            69052748).
Revival     Two conditions both required:
              (a) huzoom.lusail.com publishes a public read API with a
                  documented terms-of-use clause permitting machine access
                  for valuation/research, AND
              (b) the inventory coverage diverges materially from the four
                  syndication sources above (i.e., Huzoom-only inventory
                  becomes a non-trivial slice of the Lusail/Huzoom market).
            Without both, any revival proposal must be rejected (Operational
            Rule sec 42 deferred-work documentation pattern).
```

-----

## Conditional / case-by-case bars

(none currently)

-----

## How to add a new exclusion entry

1. Use the same 6-field block above: `Status` / `Reason` / `Substitute` / `First logged` / (optional `Headless`) / (optional `Revival`).
2. If the exclusion is rooted in empirical evidence (sampling, false-positive measurement), cross-reference `Empirical_Findings.md` Rule E# in the `Reason` block.
3. If the exclusion is infrastructure-based (WAF, geo-restriction, bot deny-list), describe the technical barrier in `Reason` and document any **conditions for revival** in a `Revival` block per Operational Rule sec 42 (deferred-work documentation pattern). The revival block prevents future Claude sessions from re-attempting an integration that was already characterised and rejected.
4. Government endpoints (`sak.gov.qa` Mthamen, `mme.gov.qa`, etc.) do **NOT** belong here — they live in `Project_Instructions.md sec 20-21` with their own smoke-test + decision-log discipline.

-----

*Created 2026-05-26 as docs-only housekeeping during Phase 3 kickoff of Sprint 2.22.0. Three permanent exclusions seeded: two T5 entries (bayut, mzadqatar) lifted from Rule E8; one new entry (huzoom.lusail.com) from Claude.ai Huzoom Lusail learning session. No engine version bump. No runtime change. No code path touches any of these endpoints today.*
