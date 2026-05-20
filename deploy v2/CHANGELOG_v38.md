# CHANGELOG v38 — Sprint 2.19.1: Polish & Fixes

**Engine version:** `thammen-sprint2p19p1-polish-and-fixes`
**Date:** 2026-05-20
**Baseline:** Sprint 2.19 (`thammen-sprint2p19p0-cap-rate-calibration`)
**Sprint type:** Polish + bug fixes + documentation hygiene. **No new methodology.**

**Files changed:**
- `evaluate_unified.py` — ENGINE_VERSION + SPRINT_TAG bump; villa cap-rate rationale (Fix #3)
- `output_briefs.py` — Arabic labels + translated source/confidence (Fixes #1, #2)
- `index.html` — dedicated `cap_rate_provenance` brief-section renderer (Fixes #1, #2)
- `cap_rate_calibrator.py` — stratification null-guard (Fix #4); outlier filter + counter + meta table (Fix #5)
- `propertyfinder_client.py` — `is_plausible_listing()` + rent/m² band (Fix #5)
- `api.py` — surface `outliers_rejected_total` in `/api/calibration` + `/api/health` (Fix #5)
- `tests/test_sprint_2p19p1_polish.py` — new, 41 isolated checks
- `test_sprint_2p16p11_tower_sanity.py` — relaxed 2 stale version-literal pins
- `docs/Operational_Rules.md` — #43 expanded with subtree-push divergence procedure
- `docs/Session_Log.md`, `docs/Project_Instructions.md` — §11 + §18 + 2026-05-20 timeline

---

## Why this matters

A real user-facing report for villa **56/565/21 (Bou Hamour, 900 m²)** plus the
`/api/calibration` output surfaced six polish issues from Sprint 2.19:

1. English schema field names (`Source · Cap Rate Pct · Confidence · Body Ar`)
   leaking into an otherwise-Arabic report.
2. Untranslated technical values (`hardcoded`, `fallback`).
3. A `Cap Rate Pct: 4.0` for the villa with no explanation — looked like a bug.
4. Several villa calibration rows with `stock_class=null` (Rule E4 not enforced
   on the row, though correctly left at `fallback`).
5. Impossible rent/m² values (0.67, 250+) reaching the calibration unchecked.
6. Sprint 2.19 operational rules not fully written to disk.

All non-blocking — production was safe — but accumulating and visible to users.

---

## What this patch does

### Display (`output_briefs.py` + `index.html`)
- **Fix #1/#2**: `build_cap_rate_provenance_section` now adds `source_ar` and
  `confidence_ar` display strings (English `source`/`confidence` retained for
  machines). `index.html` gained a dedicated `case 'cap_rate_provenance'` in
  `renderSection` — previously the section fell through to the generic dump,
  which `prettify()`-ed the keys into English labels. The brief assumed
  `output_briefs.py` alone; the actual leak was the frontend renderer, so both
  were needed.

  | Internal | Arabic display |
  |---|---|
  | `source: calibrated` | المصدر: مُعايَر من بيانات السوق |
  | `source: hardcoded` | المصدر: معدل افتراضي (غير مُعايَر) |
  | `confidence: reliable` | درجة الثقة: موثوقة |
  | `confidence: indicative` | درجة الثقة: إرشادية |
  | `confidence: fallback` | درجة الثقة: غير كافية — استُخدم معدل افتراضي |

### Engine (`evaluate_unified.py`)
- **Fix #3** — *investigation result: intentional, not a bug.* The hardcoded
  villa cap rate is **4.0% by design** (owner-occupied residential trades at low
  yields because location/lifestyle dominate rent; the income approach for a
  villa is a methodological cross-check that does not drive the final value).
  The brief's premise that "villa=6.5%, land=4.0%" was incorrect against the
  code: `villa=4.0%`, `apartment_building=6.5%`, `land=None`. No 10-Year-Rule
  land-dominance switch exists in the income cross-check. Change is
  documentation only: the hardcoded provenance now carries `asset_type` and an
  asset-aware `reason_ar` that explains *why* 4% was used, so the user does not
  read it as an error. Valuation output unchanged (no escalation trigger met).

### Calibration (`cap_rate_calibrator.py` + `propertyfinder_client.py`)
- **Fix #4** (Rule E4 hard guard, option (a)): a `villa` cell with no MoJ land
  median cannot be stratified, so it is forced to `confidence='fallback'`
  regardless of rent sample size, with note
  `stratification_unavailable:no_moj_land_median`. Prevents a growing rental
  sample from silently promoting an unstratified villa cell.
- **Fix #5**: `is_plausible_listing()` rejects rent/m² outside **[5, 200]**
  QAR/m²/month *before* binning. Rejections are counted, the rate is logged, a
  `>10%` rate emits a `[WARN]`, and counters persist to a new `calibration_meta`
  table. `api` surfaces `outliers_rejected_total` (and `calibratable_listings_seen`,
  `outlier_rejection_rate`) in `/api/calibration` and `/api/health`.

---

## Decisions made (deviations from the brief — logged per Operational_Rules #39)

1. **Fix #3 = intentional, documented (not a code fix).** The brief's "villa
   should be 6.5%" premise was wrong (6.5% is `apartment_building`). 4% is the
   deliberate residential rate. Kept the rate; added the rationale. The §5 test
   "villa hardcoded selects 6.5%" was rewritten to assert the real **4.0%**.

2. **Rule "#44" → expanded #43 instead of a new rule.** The subtree-push
   divergence procedure (split → temp branch → force push → delete branch) is a
   *consequence* of #43's subtree mechanism, and the divergence fallback already
   lived in #43. Per Anas's guidance (avoid rule sprawl), #43 was expanded with
   the explicit `heroku-deploy-tmp` procedure rather than creating a duplicative
   #44. Brief success-criterion #8 ("contains #44") is intentionally not met
   literally; the *content* is present in #43.

3. **Outlier ceiling kept at 200, not lowered.** The brief flagged 183.33 as
   "impossibly high" yet set MAX=200. 183 is within reach of genuine luxury
   rents (Pearl/Lusail premium ~150-180), so lowering the ceiling would silently
   bias premium-area medians down — worse than passing a lone n=1 value that is
   `fallback` and median-robust anyway. The firm band [5, 200] rejects only the
   physically impossible (0.67, 250+).

4. **Pre-existing brittle test assertions relaxed (4 files).** The baseline was
   *not* green: several historical Sprint tests asserted exact, frozen source
   strings that legitimately changed later — they had been failing silently (the
   `tail` summaries said "0 failed" while the process exited non-zero):
   - `test_sprint_2p16p8` / `2p16p10` / `2p16p11` / `2p16p12` pinned
     `SPRINT_TAG == '2.16.X'` literally → fail for every later Sprint. Relaxed to
     version-agnostic format checks (feature-marker checks retained).
   - `test_sprint_2p16p12` also pinned the *exact* `from pydantic import ...`
     line, which Sprint 2.16.15 broke by inserting `ConfigDict`. Relaxed to check
     the needed symbols are imported (order/extra-agnostic).
   None of these were caused by Sprint 2.19.1; they were masked baseline debt.

---

## Verification — empirical evidence

- **Test baseline (measured 2026-05-20, Rule #36):** the full standalone suite
  (14 files) had **4 files exiting non-zero** from the pre-existing brittle
  assertions described above — *not* "140/140" (an older, narrower accounting),
  and not the "282 pass / 2 fail" first reported this session (that initial pass
  under-counted the masked failures — corrected here).
- **After this Sprint:** all **15 test files exit 0**; the new
  `tests/test_sprint_2p19p1_polish.py` adds **41 checks, all green**. No
  pre-existing *behavioural* test regressed (only brittle string pins relaxed).
- `py_compile` clean on all 5 modified Python files + the new test.
- ⚠️ **`node --check` could NOT be run — Node is not installed on this machine.**
  Mitigation: the `index.html` JS edit is a localized `switch` case + one object
  literal entry, balanced and following the existing in-`case` `const` pattern;
  reviewed by hand. Recommend running `node --check` (or eyeballing in a browser)
  before/after deploy.
- New-counter behaviour proven against the **real** `api._calibration_freshness`
  with a fixture DB (Operational_Rules #40, two-layer): counter surfaces when
  present, returns `None` (no crash) on a pre-2.19.1 snapshot.

> **Note:** the committed `cap_rates.sqlite` snapshot predates the
> `calibration_meta` table, so `outliers_rejected_total` reads **null** until the
> next `run_calibration.py` crawl repopulates it. The field is exposed
> regardless; the number appears after the next recalibration.

---

## Deployment

> **Not deployed in this session.** Awaiting explicit consent (Operational_Rules
> #32). When approved, from `C:\Thammen` (NOT `C:\Thammen\deploy v2`) per
> Operational_Rules #43 divergence procedure:

```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```

Wait ~60s for dyno restart.

## Verification curl

```
curl -s https://thammen.qa/api/health | findstr /C:"sprint2p19p1"
curl -s https://thammen.qa/api/calibration | findstr /C:"outliers_rejected"
```

Post-deploy smoke (3 diverse addresses — NOT 51/835/17, Bug A6):
- Al-Ebb 400-600 villa → still `calibrated` with Arabic labels
- Bou Hamour 56/565/21 → 4.0% with Arabic rationale (no English labels)
- Pearl 600-900 villa → still `fallback`, stratification note in `notes`

---

## What's NOT in this patch

- Sprint 2.20 (Comparable Adjustments Grid) — separate
- Sprint 2.29 (MME apartments) — separate
- `runtime.txt` → `.python-version` migration — deferred to Sprint 2.19.2
- A6 latency optimization — deferred to Sprint 2.19.2
- Live recalibration to populate `outliers_rejected_total` — runs at next
  `run_calibration.py`
