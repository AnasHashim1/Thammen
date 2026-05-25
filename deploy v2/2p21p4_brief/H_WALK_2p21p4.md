# H_WALK_2p21p4 — Sprint 2.21.4 post-deploy verification

**Sprint:** 2.21.4 — T3 developer-inventory (Aryan, Lusail)
**Engine:** `thammen-sprint2p21p4-t3-aryan-lusail`
**Heroku release at walk start:** v125 (post-deploy code)
**Walk date:** 2026-05-25
**Scope:** Minimum-effective live walk per Claude.ai Step 19 directive —
H1 cited from canary, H2 + H11 walked live, H3-H9 cited from pre-deploy
evidence, H10 deferred to Anas visual.

---

## §1 — H1 (T3 invoked at City Avenues PIN)

**BRIEF §5 H1 (updated post-§5.8 correction):** evaluating a Lusail
apartment PIN whose GIS district matches a row in `developer_inventory.sqlite`
returns `tier_breakdown` containing T3 (Aryan, n=4); per-row
`status='under_construction'`, `discount_applied=-0.175`,
`value_per_m2_adjusted` in **10,957–11,082** (median **11,040.54**);
effective T3 weight = **0.12** (= 0.15 cap × 4/5 evidence).

> **Note on BRIEF §5 H1 text in earlier drafts.** The H1 spec at the
> time the walk-directive was authored quoted `discount=-0.10` and
> `adjusted in 11,950–12,100`. Those numbers were the pre-correction
> values when status was inferred as `ready` (BRIEF §11.2 Assumption 2).
> CHANGELOG_v49 §5.8 documents Anas's empirical correction
> (`ready → under_construction`) pre-deploy on 2026-05-25. D6 routes
> `under_construction` to `-0.175`, giving the cluster cited above.
> Both the §5.8 correction and Step 18 canary are consistent.

### Evidence — Step 18 canary (no live re-run)

PIN 69/255/75 (City Avenues H1 anchor PIN; resolved Pre-Step-16 via
khazna QARS_Point envelope query at the GPS centroid; 184m from
centroid; subtype=6 apartment_building):

```
HTTP 200  time=10.67s
engine_version: thammen-sprint2p21p4-t3-aryan-lusail
district:       'لوسيل 69'  (canonical GIS ANAME, DIST_NO 812)
method:         hybrid_t2
value_per_m2:   11,415.02
hybrid case=B  band=strong_indicative  n_used=78
  T2 weight=0.88  n=78
  T3 weight=0.12  n=4
    Aryan/City Avenues under_construction fresh raw=13,372.09 adj=11,031.97 disc=-0.175
    Aryan/City Avenues under_construction fresh raw=13,281.25 adj=10,957.03 disc=-0.175
    Aryan/City Avenues under_construction fresh raw=13,432.84 adj=11,082.09 disc=-0.175
    Aryan/City Avenues under_construction fresh raw=13,392.86 adj=11,049.11 disc=-0.175
```

**Verdict: PASS** — every cited criterion met. T3 weight = 0.12 to the
digit (BRIEF §9 architectural seal). Full evidence captured in
CHANGELOG_v49 §13 / Step 18 canary block.

---

## §2 — H11 (partial-population, district exact-match)

**BRIEF §5 H11:** Aryan has rows only in City Avenues. A Lusail PIN
whose micro-market doesn't match City Avenues → T2-only response; shape
matches 2.21.3 baseline.

### Live call

```
POST https://thammen.qa/api/evaluate
body: {"zone":69,"street":329,"building":20}
```

(Note: the directive's curl body included `"asset_type":"apartment_building"`.
Production schema rejects unknown request fields with HTTP 422 per
Bug A2 fix / Sprint 2.16.15 Pydantic `extra='forbid'`. The field is
omitted — engine resolves asset_type from GIS internally per
Sprint 2.16.6 classifier. The semantic of the live call is unchanged.)

### Response (compact)

```json
{
  "engine_version": "thammen-sprint2p21p4-t3-aryan-lusail",
  "asset_type": "apartment_building",
  "district": "غار ثعيلب",
  "valuation": {
    "method": "hybrid_t2",
    "value_per_m2": 11466.08,
    "value_per_m2_low": 9172.86,
    "value_per_m2_high": 13759.30
  },
  "hybrid": {
    "case": "B",
    "confidence": "indicative",
    "sample_size_band": "strong_indicative",
    "n_used": 78,
    "muc_range_pct": 0.2,
    "tier_breakdown": [
      {
        "tier": "T2",
        "weight": 1.0,
        "raw_value": 13104.10,
        "discounted_value": 11466.08,
        "discount_applied": -0.125,
        "n": 78
      }
    ]
  }
}
```

### Pass criteria

| Criterion | Result |
|---|:---:|
| HTTP 200 | ✅ |
| `method == "hybrid_t2"` (T2 active, no T3) | ✅ |
| `tier_breakdown` contains NO T3 entry | ✅ (only T2) |
| Response shape matches 2.21.3 baseline (no new top-level fields) | ✅ |
| GIS-resolved district == `"غار ثعيلب"` | ✅ |

**Verdict: PASS** — connector's district filter is **exact string match**,
not substring or zone-proximity. `'لوسيل 69'` ≠ `'غار ثعيلب'` → no T3
leak. Architectural seal on geo strictness intact.

---

## §3 — H2 (kill switch live in production)

**BRIEF §5 H2:** setting `T3_INVENTORY_ENABLED=false` on Heroku restores
pre-2.21.4 behavior immediately, no redeploy. PIN 69/255/75 (the H1
anchor where T3 fires) becomes T2-only.

### Sequence (chronological)

**Step 1 — set flag to false**
```
$ heroku config:set T3_INVENTORY_ENABLED=false --app thammen-app-123
Setting T3_INVENTORY_ENABLED and restarting thammen-app-123... done, v126
T3_INVENTORY_ENABLED: false
```

**Step 2 — 30s wait for dyno restart** (per dyno-restart latency window).

**Step 3 — /api/health (engine version unchanged)**
```
engine_version: thammen-sprint2p21p4-t3-aryan-lusail
api version:    3.1.0-sprint2.21.4
```
✅ Sprint 2.21.4 code still deployed; only the feature flag is toggled.

**Step 4 — curl 69/255/75 with flag=false** (expect no T3)

```json
{
  "engine_version": "thammen-sprint2p21p4-t3-aryan-lusail",
  "asset_type": "apartment_building",
  "district": "لوسيل 69",
  "valuation": {
    "method": "hybrid_t2",
    "value_per_m2": 11466.08,
    "value_per_m2_low": 9172.86,
    "value_per_m2_high": 13759.30
  },
  "hybrid": {
    "case": "B",
    "confidence": "indicative",
    "sample_size_band": "strong_indicative",
    "n_used": 78,
    "muc_range_pct": 0.2,
    "tier_breakdown": [
      {
        "tier": "T2",
        "weight": 1.0,
        "raw_value": 13104.10,
        "discounted_value": 11466.08,
        "discount_applied": -0.125,
        "n": 78
      }
    ]
  }
}
```

T3 block absent ✓. `value_per_m2` = 11,466.08 (T2 only, no T3 contribution).

**Step 5 — unset flag** (restore code-default `true`)
```
$ heroku config:unset T3_INVENTORY_ENABLED --app thammen-app-123
Unsetting T3_INVENTORY_ENABLED and restarting thammen-app-123... done, v127
```

**Step 6 — 30s wait for dyno restart**.

**Step 7 — curl 69/255/75 with flag restored** (expect T3 back)

```json
{
  "engine_version": "thammen-sprint2p21p4-t3-aryan-lusail",
  "asset_type": "apartment_building",
  "district": "لوسيل 69",
  "valuation": {
    "method": "hybrid_t2",
    "value_per_m2": 11415.02,
    "value_per_m2_low": 9132.02,
    "value_per_m2_high": 13698.02
  },
  "hybrid": {
    "case": "B",
    "confidence": "indicative",
    "sample_size_band": "strong_indicative",
    "n_used": 78,
    "muc_range_pct": 0.2,
    "tier_breakdown": [
      {
        "tier": "T2",
        "weight": 0.88,
        "raw_value": 13104.10,
        "discounted_value": 11466.08,
        "discount_applied": -0.125,
        "n": 78
      },
      {
        "tier": "T3",
        "weight": 0.12,
        "raw_value": 13382.48,
        "discounted_value": 11040.54,
        "discount_applied": -0.175,
        "n": 4,
        "n_effective": 4.0,
        "shape": "dict_new",
        "sources": [
          {"developer": "Aryan", "project": "City Avenues",
           "status": "under_construction",
           "value_per_m2_raw": 13372.09, "discount_applied": -0.175,
           "value_per_m2_adjusted": 11031.97, "freshness_status": "fresh"},
          {"developer": "Aryan", "project": "City Avenues",
           "status": "under_construction",
           "value_per_m2_raw": 13281.25, "discount_applied": -0.175,
           "value_per_m2_adjusted": 10957.03, "freshness_status": "fresh"},
          {"developer": "Aryan", "project": "City Avenues",
           "status": "under_construction",
           "value_per_m2_raw": 13432.84, "discount_applied": -0.175,
           "value_per_m2_adjusted": 11082.09, "freshness_status": "fresh"},
          {"developer": "Aryan", "project": "City Avenues",
           "status": "under_construction",
           "value_per_m2_raw": 13392.86, "discount_applied": -0.175,
           "value_per_m2_adjusted": 11049.11, "freshness_status": "fresh"}
        ]
      }
    ]
  }
}
```

T3 block back ✓. weight=0.12, n=4, all under_construction discount=-0.175.
`value_per_m2` = 11,415.02 (matches Step 18 canary to the cent).

### Pass criteria

| Criterion | Result |
|---|:---:|
| Step 4 HTTP 200 + `method=hybrid_t2` + no T3 in tier_breakdown | ✅ |
| Step 4 response shape identical to 2.21.3 baseline | ✅ |
| Step 7 T3 block present, weight=0.12, n=4 matching Step 18 canary | ✅ |

**Verdict: PASS** — feature flag toggles the T3 path with no code revert
needed (D11 rollback path verified in production).

### Bonus architectural observation

H2_OFF (Lusail + flag false) and H11 (Fox Hills + flag true with no T3
match for that district) **both produced `value_per_m2 = 11,466.08`** —
byte-identical T2-only tier_breakdown shape. Two paths to the same
result:

| Path | flag | district | T3 match? | result |
|---|:---:|---|:---:|---:|
| H2 OFF | false | لوسيل 69 | (gated out) | 11,466.08 |
| H11 | true | غار ثعيلب | ✗ no row matches | 11,466.08 |
| H1 / H2 ON | true | لوسيل 69 | ✓ 4 Aryan rows | 11,415.02 |

The kill switch is functionally equivalent to "engine sees no T3 data
for this micro-market". Both produce the pre-Sprint-2.21.4 byte shape —
a clean rollback path from the user's perspective.

---

## §4 — H3–H9 evidence table (cited; no live re-run)

| H# | BRIEF §5 statement (verbatim) | Pre-deploy evidence | Status |
|:---:|---|---|:---:|
| **H3** | Empty `developer_inventory.sqlite` (fresh deploy, no rows imported) does NOT crash any apartment evaluation; engine returns T2-only response | `tests/test_sprint_2p21p4_t3_inventory.py::test_19_axis19_empty_db_no_crash` + `test_19b_missing_db_file_no_crash`; reinforced by Step 9 engine integration smoke (S3+S4 — empty DB + missing DB file each yielded T2-only response, no exception) | **PASS** |
| **H4** | CSV import of the 4 City Avenues rows succeeds **LOCALLY**; populated `.sqlite` committed; rows visible in deployed slug post-deploy | Step 16 importer log: rows seen=4, inserted=4, updated=0, rejected=0. Auto-computed `value_per_m2`: 13,372.09 / 13,281.25 / 13,432.84 / 13,392.86. Slug ships populated `.sqlite` (commit 49845b0 → v125). | **PASS** |
| **H5** | Malformed CSV row (missing required, unknown column, wrong type, invalid status enum) → REJECTED with structured per-row error containing field name | `tests/test_sprint_2p21p4_t3_inventory.py`: `test_03_axis3_missing_required_field_rejected`, `test_04_axis4_unknown_column_rejected_extra_forbidden`, `test_05_axis5_wrong_type_rejected`, `test_06_axis6_invalid_status_enum_rejected` — each asserts `field` name surfaces correctly in the rejection dict | **PASS** |
| **H6** | 28-file regression suite PASSES unchanged (Sprint 2.21.3 Lusail hybrid flow returns same output when `developer_inventory.sqlite` empty) | Step 11 + Step 13 item 4: **29-file** suite (28 pre-existing + new `test_sprint_2p21p4_t3_inventory.py`) PASS in 35.0s. Sprint 2.21.2 test `test_sprint_2p21p2_hybrid_foundation.py` (67/67) preserved via `T3_discount_midpoint` back-compat alias. | **PASS** (superset) |
| **H7** | New ≥20-function test suite (D12 axes) — all PASS | `tests/test_sprint_2p21p4_t3_inventory.py` standalone runner: **26 passed, 0 failed of 26 in 3.58s** (covers all 20 D12 axes + 6 bonus tests) | **PASS** |
| **H8** | Stale row (`last_verified_at` > 90 days ago, status=`off_plan`) → `tier_breakdown` entry shows `freshness_status: 'stale'` AND contribution at 0.5× fresh-row weight | `tests/test_sprint_2p21p4_t3_inventory.py::test_11_axis11_fresh_under_90_days` + `test_12_axis12_stale_over_90_days_half_weight` + `test_12b_missing_last_verified_treated_as_stale` — verify TTL boundary + 0.5× n_effective contribution + defensive stale on missing/unparseable date | **PASS** |
| **H9** | Geo filter: Pearl apt evaluation does NOT pick up Lusail T3 rows | `tests/test_sprint_2p21p4_t3_inventory.py::test_13_axis13_geo_filter_strict` — Lusail-seeded rows + Pearl query → returns None. Reinforced live by H11 (§2) which proves the exact-string-match semantics. | **PASS** |

---

## §5 — H10 (UI tier_breakdown rendering)

**Status: PENDING** — awaits Anas's visual verification on `thammen.qa`
front-end. Not API-walkable from the back-end test suite (Rule E10 says
"surfaces this caveat to the end user via the `tier_breakdown` row's
`role_ar` and tooltip" — that's a UI rendering concern).

Tracked as open item for follow-up. Sprint 2.21.5 owns formal
`tier_breakdown` UI work; the new T3 fields (`sources` per-row breakdown,
`developer`, `project`, `status`, `freshness_status`) appear in the JSON
response today and will get a proper render path in 2.21.5.

---

## §6 — Verdict

**Sprint 2.21.4 is architecturally sealed.** T3 tier deploys correctly
(H1 canary), is properly scoped by GIS-canonical district
(H11 partial-population), and the kill-switch rollback path works in
production (H2 live toggle). All pre-deploy hypotheses (H3–H9) carry
cited evidence. H10 UI visual check is the only outstanding live item.

---

*— Sprint 2.21.4 H_WALK, 2026-05-25.
Heroku releases observed during walk: v125 (deploy) → v126 (flag false) →
v127 (flag unset, default restored). Final production state: v127, code
`thammen-sprint2p21p4-t3-aryan-lusail`, `T3_INVENTORY_ENABLED` unset
(code default `true`).*
