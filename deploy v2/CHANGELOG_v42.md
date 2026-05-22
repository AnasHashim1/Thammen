# CHANGELOG v42 — Sprint 2.21.0.7: Asset Type Reality Check

**Engine version:** `thammen-sprint2p21p0p7-asset-type-reality-check`
**Date:** 2026-05-22
**Baseline:** Sprint 2.21.0.5 (`thammen-sprint2p21p0p5-land-output-polish`, deployed v82)
**Type:** Classifier hardening for the PIN/land path + one template-polish carry-over.
**All new logic gated on `input_mode='land'` → address/villa/building flows byte-for-byte unchanged (regression-safe).**

**Files changed:**
- `qatar_gis.py` — RULEID coded-value map + `RULEID_*` sets; `_qars_count_in_polygon`
  (P1), `_landuse_at` (P2), `_reality_flag` helpers; `ENDPOINTS['landuse']`;
  land-branch reality logic (precedence: QARS > RULEID > geometric guard)
- `evaluate_unified.py` — parse `asset_type_reality:` flag; GATE 0 stop/reject;
  `_build_reality_stop_response`; attach warn result; P4 guard; version bump
- `index.html` — `asset_type_reality` panel (warn=yellow, reject/stop=red)
- `tests/test_sprint_2p21p0p7_reality_check.py` — new (41 checks)
- `CHANGELOG_v42.md` — new

---

## Why this matters
Sprint 2.21.0 trusts the user's "this is land" hint plus a single geometric guard
(≥50K→compound, ≥15K→compound, else raw_land). The audit proved that hint is
wrong often enough to matter:
- A PIN the user calls "land" may already have a **building** on it (probe:
  `90040668`, supplied as a bare-land fixture, has QARS=1 building **inside** the
  polygon → it is BUILT, not bare).
- A PIN may be **governmental / commercial / special-use** (probe: `52060090`
  RULEID=12 Governmental; `66200396` RULEID=21 Special Use) — must not be valued
  as residential raw land.

We already own two authoritative GIS signals the classifier ignored on the land
path: **QARS-in-polygon** (is a surveyed building inside the parcel?) and
**General_Landuse RULEID** (the official land-use class).

## RULEID map (P2) — authoritative
Fetched from the layer's own coded-value domain (`probe_ruleid_domain.py`), **not
guessed** (this killed an earlier wrong "Pearl=22/23" guess — Pearl is 21=Special
Use). Residential = {1, 2, 20}; agricultural = {19}; mixed-use = {23};
warn = {3, 4, 22}; reject = {5–18, 21}; no-signal = {24, −1, None}.

## What this patch does (precedence: QARS > RULEID > geometry — DECISION 4)
- **P1 (QARS-in-polygon > 0):** building present → `action='stop'`, asset_type
  UNKNOWN, no valuation. Surfaces discovery (area, RULEID label, permitted height,
  building present) and tells the user to use the address tab (DECISION 5). The
  system does **not** auto-pivot — deliberate, for user awareness.
- **P2 reject {5–18, 21}:** «هذه الأرض مصنّفة {name} — خارج النطاق الحالي لـ
  Thammen. استشر مُقيِّم متخصّص.» (DECISION 1).
- **P2 mixed-use {23}:** «هذه قطعة ضمن تطوير عقاري مختلط … خارج نطاق التقييم.»
  (DECISION 2 — master-planned, not individual lots).
- **P2 warn {3, 4, 22}:** value as raw_land **with a bold disclaimer** («السعر
  الفعلي قد يختلف 2-5 أضعاف …») (DECISION 1).
- **P2 agricultural {19}:** → `AssetType.AGRICULTURAL` (existing out-of-scope).
- **Residential {1, 2, 20} / no-signal {24, −1, None}:** trust the hint → legacy
  geometric guard (raw_land / compound). Non-residential RULEID **overrides** the
  geometric guard so a large governmental/commercial parcel is not silently a
  "compound" (DECISION 4).
- **P4 carry-over:** the building-assumption MUC factor («التقييم يفترض بناءً
  نموذجياً») was still injected for bare land (`bua_breakdown is None` always true
  for land) at a second injection point 2.21.0.5 missed — now guarded for
  raw_land/land.

All GIS calls are defensive: a failed/empty response → fall through to the
geometric guard with no flag (graceful, e.g. parcels with no General_Landuse
coverage — fixture `63090035`). Large polygon rings use the POST fallback (Rule #48).

## Decisions baked in (Anas, 2026-05-22)
1. Reject 5–18 + 21; warn 3/4/22. 2. Mixed-use 23 out of scope. 3. **P3 (MoJ
lstkhdm usage filter) DEFERRED to Sprint 2.21.0.8.** 4. RULEID > geometric guard.
5. Built PIN → stop with guidance + partial discovery (no auto-pivot).

## Verification
- New `tests/test_sprint_2p21p0p7_reality_check.py`: **41 checks** — P1 stop, P2
  reject/mixed/agri/warn/residential, no-signal fallback, DECISION 4 (RULEID >
  geometry), input_mode=None regression, Rule #40 production line
  (`_build_reality_stop_response`), P4 guard. **Full standalone suite: all files
  exit 0** (the lone `test_v2_modules.py` failure is pre-existing — it imports
  `pytest`, not installed; the suite uses standalone runners). `py_compile` clean.
- Signals pre-supplied via `location_metadata` so the suite runs **offline**;
  values mirror the live-probe ground truth.
- ⚠️ `node --check`: Node not installed locally → **browser-verify gate** post-deploy.
- Live E2E (needs GIS) → run the fixture PINs from Heroku post-deploy (see below).

## Post-deploy fixture smoke (12-PIN library, from Heroku)
| RULEID | PIN | expect |
|---|---|---|
| 1 built | 90040668 | stop (building present) |
| 1 bare | 74328443 / 74430180 / 90421755 | clean raw_land + grid |
| 2 | 69050029 | raw_land |
| 4 | 63090011 | warn (built→stop if QARS>0) |
| 10 | 56391498 | reject |
| 12 | 52060090 | reject |
| 15 | 69051939 / 63090021 | reject |
| 21 | 66200396 / 66200323 / 52598101 | reject |
| 23 | 69051981 | reject (mixed-use) |
| no LANDUSE | 63090035 | graceful (geometric guard, no crash) |

## Deployment
> Awaiting explicit consent (#32). From `C:\Thammen` per #43:
```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```
Rollback target (2.21.0.5) on Heroku = prior release → `heroku rollback`.
Verify: `curl -s https://thammen.qa/api/health | findstr /C:"sprint2p21p0p7"` +
the 12-PIN smoke + browser visual on one stop (90040668) + one clean land (74328443).

## What's NOT in this patch
- **P3 MoJ lstkhdm usage filter → Sprint 2.21.0.8** (drops only ~3% of comparables;
  11+ Arabic spelling variants need a normalization surface; 27% empty rows need
  separate handling — kept single-purpose per Rule #38).
- Auto-pivot built-land → building flow (DECISION 5b, future).
- Per-use pricing models (commercial/agricultural land medians).
- `detect_corner` wiring (still parked from 2.20).

---

# 2.21.0.7.1 — micro-follow-up (post-deploy of v89)

**Engine version:** `thammen-sprint2p21p0p7p1-micro-followup`
**Trigger:** the v89 12-PIN Heroku smoke (12/15 logic PASS; 3 fails all orthogonal)
+ Anas's visual verification (4/4 PASS) surfaced 1 UX issue + confirmed 2 decisions.

**Q1 — built non-residential → reject (not stop).** Previously *any* built parcel
returned `stop` ("use the address tab"). But for a **non-residential** built
parcel the address tab is a dead-end (it also rejects non-residential), so the
user just wastes time. New split in `classify_asset` P1:
- built + residential `{1,2}` / vacant `{20}` / unknown `{24,−1,None}` → **stop**
  (the address/villa flow can value it; vacant/unknown are *not* confirmed
  non-residential, so we don't hard-reject — resolves the two edge cases flagged
  at brief time).
- built + **confirmed non-residential** (`3–19, 21, 22, 23`) → **reject**, reason
  `non_residential_built`, with the discovery block + "consult a specialist valuer
  for {category} properties".

**Q2 — `_expand_extent` defensive sort.** `sorted(included.keys())` raised
`TypeError: '<' not supported between int and str` for a compound whose PIN keys
mix int (seed) and str (GIS attrs) — exposed by fixture `63090035` (no LANDUSE →
geometric guard → compound). Fixed: `sorted(included.keys(), key=str)`. Pure
crash-prevention, no behaviour change for uniform keys. Pre-existing bug (would
have crashed in 2.21.0 too); not introduced by 2.21.0.7.

**Q3 — discovered asset-type label in reports.** stop/reject responses kept
`asset_type='unknown'` (so the scope badge stays "unsupported"), which made the
prominent "نوع العقار" field show "غير محدد" even though we know the type.
Option A (decouple display from logic): `asset_type_ar` now carries a
RULEID+built-derived Arabic label (e.g. built RULEID=4 → «مبنى خدمات/مكاتب»;
bare RULEID=12 → «أرض حكومية»), and the frontend prefers `asset_type_ar` when
`asset_type==='unknown'` (3 display sites). Normal responses unchanged
(`asset_type!=='unknown'`).

**Files:** `qatar_gis.py` (P1 split + `_nonres_category_ar` + Q2 sort),
`evaluate_unified.py` (`_DISCOVERED_LABEL_AR` + `_discovered_label_ar` + builder
title/label + version), `index.html` (3 display sites), `CHANGELOG_v42.md`,
`tests/test_sprint_2p21p0p7_reality_check.py` (+28 checks → **69 total**),
`smoke_sprint2p21p0p7.py` (expectations updated for the new logic).

**Verification:** 69/69 isolated; full standalone suite exit 0. Re-smoke from
Heroku (post-deploy): 63090011 / 69051939 / 69051981 / 21-set → **reject**;
90040668 → **stop**; 52060090 → reject with «أرض حكومية»; 63090035 → graceful
(no crash). Rollback target = v89 (`thammen-sprint2p21p0p7-asset-type-reality-check`).

**Hotfix warning:** still **kept** until this micro-follow-up is re-verified by Anas.

---

# 2.21.0.7.1 — hotfix-warning removal (post re-verification)

**Engine version:** `thammen-sprint2p21p0p7p1-hotfix-removed`
After Anas's visual re-verification (3/3 PASS: 63090011 reject + «مبنى خدمات/مكاتب»;
52060090 reject + «أرض حكومية»; 90040668 stop + «فيلا سكنية»; Arabic/RTL/emoji/mobile
clean), the interim PIN-tab warning ("تبويب PIN يعمل حالياً للأراضي السكنية الفضاء
فقط") added in 2.21.0.5.1 is **removed** — the Asset Type Reality Check now handles
built / non-residential / governmental / commercial / mixed-use PINs with clear
stop/reject screens, so the caveat is superseded. Single-file change
(`index.html`), no logic touched. Rollback target = v90.
