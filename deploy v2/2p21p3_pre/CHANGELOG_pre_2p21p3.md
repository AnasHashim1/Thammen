# Pre-Sprint 2.21.3 — T2 Connectors Reachability + URL Discovery

**Date:** 2026-05-24
**Status:** Pre-Sprint diagnostic. NOT a Sprint. Smoke ran from Heroku
v108 (slug-only file, removed at v109 per Rule #34).
**Production baseline:** Sprint 2.21.2 deployed at Heroku v107
(`thammen-sprint2p21p2-hybrid-foundation`).
**Inputs for:** BRIEF_2p21p3 (T2 connectors — arady + PropertyFinder)
to be drafted by Claude.ai.

---

## 1. Why this smoke

Sprint 2.21.2 §5 audit left two gaps that block confident BRIEF_2p21p3
drafting:

- **arady.qa URL pattern** — root reachable from sandbox but the guessed
  `/properties?type=apartment&location=lusail` returned 404. No working
  search endpoint identified.
- **Heroku-IP reachability** — sandbox-IP showed PropertyFinder returning
  142 listing-pattern matches, but the connector will run from Heroku IP.
  Geo/rate filtering possible.

This smoke probes both from Heroku, with 5 falsifiable predictions per
Rule #51.

Out of scope: full scraper, ranking, dedup. That's Sprint 2.21.3 proper.

---

## 2. Predictions ledger

Run from Heroku one-off dyno on 2026-05-24 16:22 UTC. Total wall time
**31.8 s**.

| # | Prediction | Result | Evidence |
|---|---|:---:|---|
| **H1** | PropertyFinder reachable from Heroku (HTTP 200) | ✅ TRUE | HTTP 200 in 0.79 s, body 955,620 chars |
| **H2** | PF Lusail page returns ≥ 30 listing-pattern matches | ❌ FALSE | **24 unique** `/plp/` paths on page 1 (142 raw matches — each link appears ~6× in card/image/meta DOM). See §3 for nuance |
| **H3** | At least one arady search URL pattern returns HTTP 200 with listing content | ✅ TRUE | **`/listings` works** — HTTP 200, 456,066 chars, 70 listing-pattern hits. Also `/sitemap.xml` reachable (4,564 chars, 20 hits) |
| **H4** | Heroku-IP counts match sandbox-IP within ±15 (no geo filtering) | ✅ TRUE | Heroku raw=142 vs sandbox raw=142, Δ=0 — exact match |
| **H5** | At least one PF detail page exposes both price + area extractable | ✅ TRUE | 2 of 2 sampled detail pages had BOTH a `QAR/AED` price token AND an area token (m²/sqm). PF also uses `property-price` CSS class as a stable marker |

**Verdict: 4 of 5 TRUE.** H2 FALSE is a threshold artifact, not a
structural problem (see §3).

---

## 3. H2 honest reading

The threshold was "≥ 30 listing-pattern matches". Heroku returned 142 raw
matches and 24 unique listings on page 1 of the Lusail rent search.

The 142 ≠ 30 sense: each listing appears multiple times in the DOM
(listing card link + image-link + meta-link + breadcrumb link + …),
so raw regex match count overcounts by ~6× the true unique listings.
The 24 unique listings on page 1 sits below the 30 threshold the BRIEF
section §5 wrote.

Three options for the 2.21.3 connector to reach n ≥ 30 unique:

1. **Paginate** — PropertyFinder is fully SSR per Operational §14;
   `?page=2`, `?page=3` should serve page 2/3. 3 pages × ~24 ≈ 72 unique
   listings. Adds ~3 requests per geography.
2. **Widen geography** — search across multiple Lusail sub-areas
   (l=63 currently; PF has separate location codes for Marina, Fox Hills,
   Energy City, etc.). Doha-wide rent search returns thousands.
3. **Lower the threshold** — n=24 on page 1 still exceeds Empirical_Findings §3
   sample-size cutoff for `indicative` (n ≥ 10). Reliable rating requires
   T1 anyway (Rule E3 Constraint 4); `indicative` is the realistic Stage 1
   ceiling for apartments today.

Recommendation for BRIEF_2p21p3: combine **(1) + (2)** — connector hits 2-3
pages × 1-3 location codes; bin per cell; report n per bracket.

This does NOT block the Sprint. PropertyFinder data exists in abundance;
the smoke just confirmed the per-page count math.

---

## 4. arady.qa URL probe — full results

11 candidate URLs probed. 8 returned identical 404 error page (9,334 bytes —
this is arady's canonical "not found" template, useful as a negative
signature). 3 returned HTTP 200:

| URL | HTTP | length | listing hits | working? |
|---|---:|---:|---:|:---:|
| `/properties` | 404 | 9,334 | 0 | no |
| `/properties/lusail` | 404 | 9,334 | 0 | no |
| `/properties/apartments` | 404 | 9,334 | 0 | no |
| **`/listings`** | **200** | **456,066** | **70** | **✓ working** |
| `/search?q=lusail` | 404 | 9,334 | 0 | no |
| `/search?location=lusail&type=apartment` | 404 | 9,334 | 0 | no |
| `/rent` | 404 | 9,334 | 0 | no |
| `/apartments-for-rent` | 404 | 9,334 | 0 | no |
| `/lusail` | 404 | 9,334 | 0 | no |
| **`/sitemap.xml`** | **200** | **4,564** | **20** | **✓ inventory** |
| `/robots.txt` | 200 | 1,868 | 0 | (no listings expected) |

**The `/listings` endpoint is the canonical arady search page.** 70
listing-pattern matches on page 1 already exceeds n ≥ 30 without
pagination tricks. Whether it supports filter parameters (`?city=`,
`?type=`, `?bedrooms=`) is the next discovery item for Sprint 2.21.3
connector — `/sitemap.xml` is the cheapest way to enumerate the actual
URL structure.

---

## 5. PropertyFinder schema signals (for 2.21.3 connector)

From `https://www.propertyfinder.qa/en/search?c=2&t=1&l=63` page-1 body:

| Signal | Count | Connector value |
|---|---:|---|
| `QAR` price tokens | 11 | direct price extraction possible |
| `AED` price tokens | 3 | mixed-currency listings exist; connector must normalize |
| `Lusail` / `لوسيل` mentions | 13 | geography filtering confirmed |
| `sqm` / `m²` tokens | 292 | size data abundant |
| `\bN\s*bed` tokens | 188 | bedroom count extractable |

Detail-page sample (2 listings probed at random):

```
/en/plp/rent/apartment-for-rent-doha-al-messila-1001625.html
  has_price_token: True
  has_area_token: True
  has_price_marker: True (CSS: property-price)
  has_size_marker: False
  extractable: True

/en/plp/rent/apartment-for-rent-doha-al-messila-1021188.html
  has_price_token: True
  has_area_token: True
  has_price_marker: True
  has_size_marker: False
  extractable: True
```

Connector strategy recommendation: use the `property-price` CSS class as
the primary price selector (stable across listings); fall back to regex
`QAR\s*[\d,]+` if the marker is missing. For size, use regex
`(\d[\d,]*(?:\.\d+)?)\s*(?:sqm|m²|m2|sq\s*m)` — the marker class isn't
consistently present per the sample.

**Note:** the detail-sample URLs both land in Al Messila, not Lusail. The
PF location filter (l=63) returns "Lusail OR adjacent areas" rather than
strict Lusail-only. Sprint 2.21.3 connector will need to filter by
`location` string inside each listing detail to enforce Lusail-only when
required.

---

## 6. Inputs for BRIEF_2p21p3 (handed off to Claude.ai)

Concrete data Claude.ai can drop into the BRIEF when drafting Sprint 2.21.3:

1. **PropertyFinder connector spec:**
   - Search URL template: `https://www.propertyfinder.qa/en/search?c=<category>&t=<type>&l=<location>&page=<N>`
   - Lusail location code: `l=63` (returns Lusail + adjacent)
   - Page-1 yields ~24 unique listings; paginate 2-3 pages to reach n ≥ 30
   - Detail URL pattern: `/en/plp/{rent|buy}/<slug>-<id>.html`
   - Primary price selector: CSS class `property-price`
   - Fallback price regex: `\b(?:QAR|AED)\s*[\d,]+`
   - Size regex: `(\d[\d,]*(?:\.\d+)?)\s*(?:sqm|m²|m2|sq\s*m)`
   - Currency normalization: convert AED to QAR (rate ≈ 0.98, periodic refresh)
   - Sub-Lusail filter required at listing-level

2. **arady connector spec:**
   - Search URL: `https://arady.qa/listings`
   - Page-1 yields ~70 listing-pattern hits — more than enough for first cut
   - `/sitemap.xml` (4,564 chars) is the cheapest URL inventory — parse for
     full enumeration BEFORE building any pagination logic
   - Detail-page schema, parameter filters, pagination scheme: **all
     unknown** — connector Sprint should start with sitemap parsing then
     reverse-engineer one detail page

3. **Heroku-IP parity confirmed:** sandbox-side numbers carry directly to
   production. No geo filter, no rate-limit differential observed in this
   smoke (single 31.8 s burst, 11 + 3 requests).

4. **Both sources independent:** PF + arady can be scraped in parallel by
   `concurrent.futures.ThreadPoolExecutor(max_workers=2)` per Rule E19.

---

## 7. Hygiene

- `smoke_t2_connectors.py` was on Heroku slug as v108, removed at v109
  (slug back to v107 engine code state per Rule #34).
- Workspace copy in `2p21p3_pre/smoke_t2_connectors.py` retained for
  re-runs without re-deploy.
- No production code touched. Engine version unchanged
  (`thammen-sprint2p21p2-hybrid-foundation`).
- 2 Heroku releases this Pre-Sprint (v108 push, v109 cleanup). Total
  wall time including push/run/cleanup: ~3 min.

---

## 8. Next move

Hand findings to Claude.ai → draft BRIEF_2p21p3. The data here resolves
both Sprint 2.21.2 §5 gaps (arady URL + Heroku reachability) and surfaces
the schema markers needed for connector design (CSS class + regex
fallbacks for both sides).

*— Anas / Claude Code session, 2026-05-24.*
