# Pre-Sprint 2.21.1 — Audit + MME Smoke Results

**Date:** 2026-05-24
**Status:** Pre-Sprint diagnostic, not a Sprint. No engine bump, no
CHANGELOG_v{N}. Two scripts ran, results captured below, Sprint 2.21.1
decision documented at §3.

---

## 1. Audit (Step 3 of PROMPT) — `audit_post_2p18p1p1.py`

Engine live: `thammen-sprint2p18p1p1-compound-misroute-fix` (Heroku v101)
API version field: `3.1.0-sprint2.18.1.1`

Sample: 3 active cases × 1 rep, run from local Windows against
`https://thammen.qa/api`, 2026-05-24 ~14:00 Doha. 3 cases skipped
(TODO placeholders: PIN-tab built-PIN, Pearl apartment Z/S/B, Lusail
apartment Z/S/B).

| # | Body | asset_type | valuation_amount | latency | verdict |
|---|---|---|---|---|---|
| 1 | `{zone:52, street:903, building:90}` | `apartment_building` | `None` | 4.54 s | PASS — DCF fast-path refusal (no rent input) |
| 2 | `{zone:51, street:835, building:17}` | **`compound_large`** | **`None`** | 26.48 s | PASS — **Sprint 2.18.1.1 Patches A+C intact**, no 218 M / −211 M arithmetic |
| 6 | `{pin:"74328443"}` | `raw_land` | `None` | 21.79 s | PASS — Sprint 2.21.0.5 polish intact, no template leak |

**Observed-vs-expected notes (per Rule #36):**

- Case 1 expectation initially called for `standalone_villa` based on the
  CLAUDE.md `safe_villa_52` label. Production has been returning
  `apartment_building` for this address since at least Sprint 2.18.0
  (§14.1 categorises it under "DCF fast-path (apartment_building,
  compound_large→unknown reject) | ~4.1 s, 4 events"). The label is
  historical mis-naming, not a regression. CLAUDE.md / SECURITY_AUDIT.md
  carry "villa" against this address in a few places — candidate
  docs-hygiene cleanup, not a Sprint.

- Case 6 (`PIN 74328443`) first attempt was **HTTP 503 in 30.43 s**
  (Cloudflare router timeout); retry was **HTTP 200 in 21.79 s**.
  Single-rep flaky behaviour, consistent with cold-dyno on first request.
  Session_Log §15.1 wider 21-rep cohort post-2.18.1 shows 0 % failure;
  this single 503 does not establish a new latency class. If it recurs
  consistently on bare-land PINs in future audits, it would justify
  Sprint 2.18.2-candidate scope (lite/full GIS dedup) being expanded to
  cover bare-land BFS — currently it is scoped to `compound_small` only.

- 3 cases skipped: PIN-tab on built-address PIN (needs `52/903/90`
  centroid PIN), Pearl apartment baseline, Lusail apartment baseline.
  Cases 4 + 5 left intentionally pending; their values cannot be
  predicted today and they will be captured once Sprint 2.21.1 cell
  schema is defined.

**Verdict: AUDIT PASS** — 5-release marathon (v97 → v101) shows no visible
regression on the active sample. Engine version matches expected v101.
Critical Sprint 2.18.1.1 fix (compound-misroute) verified intact on the
reference address 51/835/17.

---

## 2. MME Smoke (Step 4 of PROMPT) — `smoke_mme.py` + `smoke_mme_v2.py`

Both files were deployed to Heroku temporarily (v102 + v103), executed
via `heroku run`, and are scheduled for removal in the next commit per
Operational_Rules #34.

### Predictions ledger

Sample: 2026-05-24, two Heroku one-off dyno runs, 11:10 UTC (v1) and
11:56 UTC (v2). Scope: 12 × kpi29 calls across Pearl (areaCode 765) +
Lusail (areaCode 812) over windows 2024-11 → 2026-05; 7 × rent-path
variants; 6 × propertyTypeList variants on kpi29 (Pearl 2025);
1 × browser-mimic call.

| # | Prediction | Result | Evidence |
|---|---|---|---|
| **P1** | Heroku reaches MME (flow-trigger HTTP 200) | **TRUE** | 200 in 0.88 s and 0.91 s on two independent runs |
| **P2** | JWT survives subsequent kpi calls (no 401) | **TRUE** | 12 × kpi29 calls held the bearer token, 0 × 401 |
| **P3** | Pearl (765) n ≥ 30 apartment sales / 18 mo | **FALSE — but see §3** | n = 0 across 6 windows × propertyType variants × Origin-headers |
| **P4** | Lusail (812) n ≥ 30 apartment sales / 18 mo | **FALSE — but see §3** | n = 0, same coverage |
| **P5** | Per-transaction schema (one row per sale, with size + price) | **UNDETERMINED — schema known, rows absent** | Schema is `{count: int, transactionList: list}`; transactionList stayed `[]` for every variant |
| **P6** | kpi30/31/32 are three distinct rent slices | **FALSE — paths stale** | 7 path variants tested (`/kpi/rent/kpi30`, `…/kpi30/transactions`, `…/kpi30/list`, `…/kpi30/data`, `…/rents/kpi30/transactions`, `…/lease/kpi30/transactions`, `…/rental/kpi30/transactions`) — all 404. GET `/kpi/rent` also 404 |
| **P7** | Per-unit rent is monthly (FGRealty convention) | **UNDETERMINED** | No rent rows obtainable; cannot compute QAR/m²/month |
| **P8** | areaCode alone is sufficient (no municipalityId) | **TRUE — weak signal** | Both with and without `municipalityId:1` returned 200; both also returned `count:0`, so the test does not separate the two cases under current auth |

### Diagnosis

Heroku reaches MME (P1 ✓). The JWT mechanism works mechanically — token
issued, accepted on the bearer header, survived 12 kpi calls across
both runs (P2 ✓). The public `/flows/trigger/<UUID>` endpoint, however,
issues an **anonymous Directus token**:

```
JWT payload: {"role": null, "app_access": false, "admin_access": false,
              "iat": …, "iss": "directus"}
Response header: X-Powered-By: Directus
```

`role: null` + `app_access: false` is the Directus convention for an
unauthenticated public user. Permissions to read collections must be
explicitly granted to the `public` role on the Directus instance,
otherwise queries return `count:0` with HTTP 200. The kpi29 schema is
now known (`{count, transactionList}`), and for every propertyType
variant (`[5]`, `[1]`, `[6]`, `[1,5,6]`, `[]`, omitted) and Origin /
Referer / X-Requested-With browser-mimic the response was identical:
`{"count":0,"transactionList":[]}`. The filter is auth scope, not
propertyType, not areaCode, not Origin.

The rent paths from Operational §28 (`/kpi/rent/kpi30`, `kpi31`, `kpi32`)
are verified dead — 7/7 variants returned 404. Their correct shape is
currently unknown.

**Bottom line:** MME requires an authenticated session that the public
flow-trigger does not currently provide. Sprint 2.21.1 cannot be drafted
on top of this auth scope; the next required step is capturing the real
authenticated session on mme.gov.qa (or qrep.aqarat.gov.qa) via browser
DevTools — log into the official MME web app, watch the Network tab for
the kpi calls fired by the apartment KPIs page, copy the `Authorization`
header (and any session cookies) used by those calls, and verify with a
small `smoke_mme_v3.py` whether that captured token decodes with a
non-null `role` and returns transactionList rows for Pearl/Lusail.

---

## 3. Decision

**Sprint 2.21.1 deferred** pending DevTools capture of the real
authenticated MME session.

This is **not** an "MME impossible" verdict. The plumbing is reachable
and the JWT mechanism works. The blocker is auth scope — fixable with a
~10–30 minute manual capture on Anas's side (or whoever has MME login
credentials).

### Alternatives if DevTools capture is impractical

- **(a) FGRealty T2 cut** for Pearl + Lusail apartments — lower-confidence
  cell (Rule E11 floor: T2 caps confidence at `indicative`, not
  `reliable`), but ships Stage 1 (E16) for apartments without MME.
- **(b) Defer 2.21.1 indefinitely** until secretary's confirmed sales
  (Sprint 2.16.16, currently still pending) cover apartments — then
  re-evaluate whether MME calibration is needed at all.

Both alternatives are documented; decision deferred until Anas
chooses a path.

### Open follow-ups (not blocking 2.21.1 decision)

1. **CLAUDE.md / SECURITY_AUDIT.md** carry "safe_villa_52" against
   `52/903/90` in a few places — the address is actually
   `apartment_building` in production since at least 2.18.0. Candidate
   docs-hygiene one-liner.

2. **Operational §28** lists MME rent paths
   (`/kpi/rent/kpi30`, `kpi31`, `kpi32`). Verified dead 2026-05-24,
   needs re-discovery. Recommend annotating those lines with
   `# verified dead 2026-05-24, needs re-discovery` rather than
   removing — preserves history.

3. **kpi29 response schema** (`{count, transactionList}`) is now known
   and should be recorded somewhere durable (Operational §28 or a new
   §28a). The previous extractor heuristic in `smoke_mme.py` (and any
   future MME client) should key off `transactionList`, not
   `data/transactions/result`.

---

## 4. Hygiene

Per Operational_Rules #34:

- `smoke_mme.py` + `smoke_mme_v2.py` were temporarily on slug
  (Heroku v102 + v103). Cleanup commit removes both from slug; workspace
  copies in `2p21p1_pre/` remain off-slug for re-runs without re-deploy.
- No production code (`api.py`, `evaluate_unified.py`,
  `qatar_gis.py`, etc.) was modified by this work.
- The BRIEF.md and PROMPT.md that prompted this work live in
  `2p21p1_pre/` as workspace files; not committed.

Total wall time (audit + 2 smoke runs + write-up): ~70 min.

*— Anas / Claude Code session, 2026-05-24*
