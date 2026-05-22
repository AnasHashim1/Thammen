# Sprint 2.21.0.7 — Asset Type Reality Check — DRAFT for review

**Status:** DRAFT for review. **No Sprint code written yet** (§5). Audit complete.
**Baseline:** Sprint 2.21.0.5 (`thammen-sprint2p21p0p5-land-output-polish`, deployed v82)
**Target:** `thammen-sprint2p21p0p7-asset-type-reality-check` · CHANGELOG_v42
**Type:** Classifier hardening for the PIN/land path + one template-polish carry-over.
**Effort:** 4–6h.

---

## 0. The problem this Sprint fixes

Sprint 2.21.0 made bare-land PINs reachable, but the land branch trusts the
user's "this is land" hint **plus a single geometric guard** (≥50K→compound,
≥15K→compound, else raw_land). The audit proved that hint is wrong often enough
to matter:

- **A PIN the user calls "land" may already have a building on it** (probe:
  `90040668` — user-supplied as a bare-land fixture — has QARS=1 building **on the
  polygon**, RULEID=1 residential → it is BUILT, not bare).
- **A PIN may be governmental / commercial / special-use**, which we must not
  value as residential raw land (probe: `52060090` RULEID=12 Governmental;
  `66200396` RULEID=21 Special Use).

We already own two authoritative GIS signals that the classifier currently
ignores on the land path:

1. **QARS-in-polygon** — is there a surveyed building *inside* this parcel? (P1)
2. **General_Landuse RULEID** — the parcel's official land-use class. (P2)

Plus a MoJ-side refinement (P3) and one template factor that 2.21.0.5 missed (P4).

**Design principle (unchanged from Bug A11 / Rule E7):** we *surface* the
contradiction and adjust confidence — we do **not** silently override the user.
Where the signals are decisive (a building exists; a non-residential RULEID), we
reclassify; where they merely disagree, we flag.

---

## 1. Authoritative RULEID map (P2) — fetched from the layer's coded-value domain

`probe_ruleid_domain.py` pulled the **published coded-value domain** of
`Vector/General_Landuse/MapServer/0` (not guessed — this killed an earlier wrong
guess of "Pearl=22/23"; Pearl is actually 21=Special Use):

| RULEID | Official label | Thammen treatment |
|---:|---|---|
| 1 | Single-Family Residential | `raw_land` (residential) — **valuation path** |
| 2 | Multi-Family Residential | `raw_land` (residential, multi-family) — valuation path |
| 3 | Retail / Commercial | non-residential → flag + out-of-scope (see §5 Q) |
| 4 | Services / Offices | non-residential → flag |
| 5 | Wholesale | non-residential → flag |
| 6–9 | Industry (light→heavy) | non-residential → flag |
| 10 | Educational | non-residential → flag |
| 11 | Health | non-residential → flag |
| 12 | Governmental | non-residential → flag |
| 13 | Community / Cultural | non-residential → flag |
| 14 | Religious | non-residential → flag |
| 15 | Open Space / Recreation | non-residential → flag |
| 16 | Sports | non-residential → flag |
| 17 | Transportation | non-residential → flag |
| 18 | Utilities | non-residential → flag |
| 19 | Agricultural | → `AGRICULTURAL` (already an AssetType) |
| 20 | Vacant Land | `raw_land` — **cleanest land signal** |
| 21 | Special Use | non-residential → flag |
| 22 | Tourism | non-residential → flag |
| 23 | Mixed Use | residential+commercial → flag (pricing question, §5) |
| 24 | Unknown | no signal — fall back to geometry |
| -1 | Free Representation | no signal — fall back to geometry |

**Residential-land RULEIDs = {1, 2, 20}.** Everything 3–18, 21, 22 is
non-residential. 19→agricultural. 23→mixed. 24/-1→no signal.

---

## 2. lstkhdm (MoJ usage) audit (P3) — distribution on أرض فضاء

`probe_lstkhdm_audit.py` on the local `moj_weekly.csv` (26,719 rows; 14,155 are
أرض فضاء):

| n | الاستخدام (normalized) | → class |
|---:|---|---|
| 9,715 (68.6%) | فلل او بيوت سكنية | residential (RULEID 1) |
| 3,837 (27.1%) | (empty) | unspecified |
| 378 | عمارات او مجمعات سكنية | multi-family (RULEID 2) |
| 40 | مسكن | residential |
| 37 | مزارع | agricultural (RULEID 19) |
| 21 | مكاتب تجارية | offices (RULEID 4) |
| ~70 | اراض/أراضي تجارية متعددة الأستخدام (11 spellings) | mixed/commercial (23/3) |
| 13 | أماكن ترفيهية | recreation (15) |
| 10 | مرافق | utilities (18) |
| 7 | مناطق خاصة | special use (21) |
| 7 | مساكن كبار الموظفين | residential |
| ~13 | مدارس / مدارس ومعاهد حكومي | educational (10) |
| 5 | أسواق ومحال | retail (3) |
| 3 | مساجد | religious (14) |

**Two findings:**
1. **95.7% of vacant-land sales are residential or empty.** The non-residential
   tail is ~3%. So a residential-land subject already draws an overwhelmingly
   residential comparable pool — the filter's job is to *exclude the ~3% noise*,
   not to rebuild the pool.
2. **The commercial bucket is shattered across 11+ spellings** (`الأستخدام` /
   `الآستخدام` / `الاستخدام` / `الأستخدم`; `اراض` / `أراضي` / `أراض`). Plus the
   column name `تاريخ التثبيت` carries NBSP. **Any exact-match filter is wrong.**
   Filtering must normalize (NBSP + alef/hamza folding) and match on a residential
   *whitelist*, not a non-residential blacklist.

**P3 filter (recommended):** when the subject is residential land (RULEID 1/2/20
or geometry-only fallback), restrict MoJ land comparables to usage ∈
{`فلل او بيوت سكنية`, `عمارات او مجمعات سكنية`, `مسكن`, `مساكن كبار الموظفين`}
**OR empty** (empty kept — 27% of the pool, and 95% of land is residential). The
~3% explicit non-residential usages are dropped. **Scope question for Anas:** is
P3 worth shipping in this Sprint, or deferred? It changes comparable medians
slightly (drops ~3% outliers) but adds normalization surface. See §5 Q3.

---

## 3. Verified fixture library (from probe rounds — ground-truth, not guessed)

Each fixture = (PIN, RULEID, QARS-in-polygon, BUILT/BARE), confirmed live from
Heroku. These become the Sprint's regression fixtures:

| RULEID | class | PIN | QARS-in-poly | state |
|---:|---|---|---:|---|
| 1 | residential | `90040668` | 1 | **BUILT** (was mislabeled "bare") |
| 1 | residential | `74328443` | 0 | BARE ✓ |
| 1 | residential | `74430180` | 0 | BARE ✓ |
| 1 | residential | `90421755` | 0 | BARE ✓ |
| 2 | multi-family | `69050029` | 0 | BARE |
| 4 | offices | `63090011` | ≥1 | BUILT |
| 10 | educational | `56391498` | 0 | BARE |
| 12 | governmental | `52060090` | 0 | BARE |
| 15 | recreation | `69051939` / `63090021` | ≥1 / 0 | BUILT / BARE |
| 21 | special use | `66200396` `66200323` `52598101` | ≥1 | BUILT |
| 23 | mixed use | `69051981` | ≥1 | BUILT |
| (none) | no-LANDUSE coverage | `63090035` | — | graceful fallback |

**Only 3 of the user's original 5 "land" PINs are truly residential bare land**
(74328443, 74430180, 90421755). 90040668 is built; 52060090 is governmental.
Baseline contamination is why probe_land_pins.py's earlier "5/5 land" was wrong —
it never queried QARS or RULEID, it only echoed the input hint.

---

## 4. Proposed implementation (P1–P4)

### P1 — QARS-in-polygon building detection
New helper in `qatar_gis.py`: `_qars_count_in_polygon(ring) -> int` — POST
(Rule #48; large rings exceed the 2000-char GET limit, already hit on the Pearl
polygon) a polygon-intersect `returnCountOnly` query to `ENDPOINTS['qars']`. In
`full_property_lookup`'s PIN path, compute the count once and pass it into
`classify_asset` via `location_metadata` (or a new `qars_in_polygon` kwarg).

In the `input_mode == 'land'` branch of `classify_asset`: **if `qars_in_polygon
> 0` → the parcel is BUILT.** Do not return `raw_land`. Emit
`asset_type_reality_flag` (kind=`land_hint_but_building_present`, non-blocking),
downgrade confidence, and recommend the address/QARS flow. (Mirrors Bug A11
pattern: surface, don't silently re-value — but here the signal is decisive
enough that we should *not* run the land grid on a built parcel.)

### P2 — RULEID classification
New helper: `_landuse_ruleid_at(lon, lat) -> Optional[int]` — point-intersect
query to `Vector/General_Landuse/MapServer/0` (add to `ENDPOINTS`). In the land
branch:
- RULEID ∈ {1, 2, 20} → proceed as `raw_land` (residential), confidence high.
- RULEID = 19 → `AGRICULTURAL`.
- RULEID = 23 → `raw_land` + `mixed_use` flag (pricing caveat).
- RULEID ∈ non-residential set → emit `asset_type_reality_flag`
  (kind=`non_residential_landuse`, RULEID + official label in message), keep
  geometry result but mark out-of-scope per §5 Q1.
- RULEID 24/-1/None (no coverage, e.g. 63090035) → **graceful fallback** to the
  existing geometric guard. No crash, no flag.

**Precedence:** P1 (building present) > P2 (land-use) > geometric guard.

### P3 — MoJ usage filter (optional, see §5 Q3)
In the land comparable builder, add a `usage_whitelist` filter with NBSP +
alef/hamza normalization (reuse the `norm()` from probe). Residential subject →
keep residential + empty usages, drop explicit non-residential.

### P4 — template carry-over from 2.21.0.5
`evaluate_unified.py:~2954` injects the building-assumption MUC factor
(«تفاصيل البناء غير مُقدَّمة … التقييم يفترض بناءً نموذجياً») whenever
`bua_breakdown is None` — which is **always** true for bare land, so it still
leaks onto raw_land reports. Guard the block: skip when
`_out_at in ('raw_land','land')`. (2.21.0.5 fixed the `assess_uncertainty`
factors but not this separate injection point.)

---

## 5. Batch business questions for Anas (need answers before/at approval)

**Q1 — Out-of-scope handling for non-residential RULEID.** When a PIN resolves to
RULEID 3–18/21/22 (commercial, governmental, special use, etc.), should Thammen:
(a) refuse with a clear "هذه القطعة غير سكنية — خارج نطاق التقييم السكني" message,
or (b) still produce a land-value estimate **with a prominent caveat**? My
recommendation: **(a) refuse** for governmental/special/utilities/transport
(no meaningful residential comparable), **(b) caveat** for commercial/offices/
retail (a land value exists, just not residential). Confirm.

**Q2 — RULEID 23 (Mixed Use) pricing.** Mixed-use land trades differently from
pure residential. Value it as residential raw_land with a flag, or out-of-scope?

**Q3 — Ship P3 (MoJ usage filter) now or defer?** It only removes ~3% of
comparables and adds normalization surface. Defer to keep this Sprint
single-purpose (Rule #38), or include?

**Q4 — Large non-residential parcels & the geometric guard.** Today ≥50K→
compound_large regardless of use. If RULEID says governmental/special at 60K m²,
RULEID should win (out-of-scope) over the compound guard. Confirm precedence
P2 > geometric guard for non-residential.

**Q5 — "Built parcel" UX.** When P1 finds a building on a "land" PIN, do we
(a) hard-stop and tell the user to use the address/villa tab, or (b) auto-pivot
to the building flow using the QARS data? Recommendation: **(a) hard-stop with
guidance** this Sprint (auto-pivot is a bigger change).

---

## 6. Files / version / changelog (proposed)
| File | Change |
|---|---|
| `qatar_gis.py` | `ENDPOINTS['landuse']`; `_qars_count_in_polygon`; `_landuse_ruleid_at`; land-branch P1+P2 logic + flag; thread into `full_property_lookup` PIN path |
| `evaluate_unified.py` | parse `asset_type_reality_flag` into response; P4 guard at ~2954; version bump |
| `evaluate_property.py` | pass qars_in_polygon / ruleid through if needed |
| `output_briefs.py` + `index.html` | render `asset_type_reality_flag` panel (mirror A11 `subtype_zoning_mismatch` panel) |
| MoJ comparable builder | (P3, if approved) usage whitelist + normalization |
| `tests/test_sprint_2p21p0p7_reality_check.py` | new — fixtures from §3 |
| `CHANGELOG_v42.md` | new |
ENGINE_VERSION → `thammen-sprint2p21p0p7-asset-type-reality-check`.

---

## 7. Test plan
- **Unit (replica + ≥1 production line, Rule #40):** RULEID map → treatment;
  QARS>0 → BUILT not raw_land; RULEID non-residential → flag; RULEID 24/None →
  graceful geometric fallback (no crash); P4 guard removes building factor for
  land, keeps it for villa.
- **Post-deploy E2E (Rule #46):** run the §3 fixture PINs from Heroku — confirm
  90040668→BUILT flag, 52060090→non-residential flag, 74328443→clean raw_land +
  grid fires, 63090035→graceful (no LANDUSE, no crash). Browser visual on one
  built-flag + one clean-land report.

## 8. Pre-deploy checklist (§5)
py_compile · node --check on index.html JS (Node still unavailable locally →
browser-verify gate) · full suite green · ≥5 new tests · smoke §3 fixtures from
Heroku · GIS reachability already proven (probes ran from Heroku).

## 9. Out of scope (explicit)
- Auto-pivot built-land → building flow (Q5b) — bigger change, future Sprint.
- Per-use pricing models (commercial/agricultural land medians) — needs its own
  comparable strata.
- Wiring `detect_corner` (still parked from 2.20).
