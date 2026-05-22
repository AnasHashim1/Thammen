# CHANGELOG v41 — Sprint 2.21.0.5: Land Output Polish

**Engine version:** `thammen-sprint2p21p0p5-land-output-polish`
**Date:** 2026-05-22
**Baseline:** Sprint 2.21.0 (`thammen-sprint2p21p0-pin-input-lands`, deployed)
**Type:** Output-template polish — conditional rendering for `raw_land`. Backend
already correct; this fixes 5 user-facing template issues found by post-deploy
visual verification (الخور PIN 74328443). **All fixes conditional on asset_type →
buildings/villas/etc. unchanged (regression-safe).**

**Files changed:**
- `scope_of_service.py` — Issue 1: `raw_land` alias of supported `land` scope
- `evaluate_property.py` — Issue 2: PIN-aware display address
- `evaluate_unified.py` — Issue 3: skip land/building decomposition for land; note; version bump
- `material_uncertainty.py` — Issues 4+5: `asset_type`-aware factors + known_unknowns
- `evaluate_v3.py` — thread `asset_type` into `assess_uncertainty`
- `output_briefs.py` — Issue 5: raw_land due-diligence questions
- `tests/test_sprint_2p21p0p5_land_polish.py` — new (21 checks)
- `CHANGELOG_v41.md` — new

---

## Why this matters
Sprint 2.21.0 made the Land Grid reachable (PIN → raw_land → grid, verified). But
the **output template still assumed a building**, producing 5 contradictions in
the user-facing report for a bare land plot:
1. "❌ خارج النطاق — نوع غير معروف" beside "أرض فضاء / 🟢 موثوق".
2. `address: None/None/None` (PIN mode has no Z/S/B).
3. Negative "building value −3.5%" in the land/building decomposition.
4. "يفترض بناءً نموذجياً" / BUA + service-charge uncertainty factors.
5. Tenant/tower/building due-diligence questions + known-unknowns.

Root cause (Rule #46 expansion): «backend produces raw_land» ≠ «template handles
raw_land». Recurring `land`↔`raw_land` naming mismatch (classifier emits
`raw_land`; `scope_of_service` keyed `land`).

## What this patch does
- **Issue 1:** `_ASSET_SCOPE['raw_land'] = _ASSET_SCOPE['land']` → raw_land is
  `supported` ("أرض سكنية"), not "نوع غير معروف". (Alias pattern, not rename.)
- **Issue 2:** for PIN entry, display address = «أرض في {district} — PIN {pin}»
  (fallback «PIN {pin}»). Z/S/B entry unchanged.
- **Issue 3:** for `asset_type ∈ {raw_land, land}` skip the value decomposition;
  emit `valuation.value_decomposition_note_ar` = «هذه قطعة أرض فضاء — التقييم على
  قيمة الأرض المنفصلة فقط…». Buildings keep decomposition.
- **Issue 4:** `assess_uncertainty(asset_type=…)` skips BUA + service-charge
  factors for land (keeps "لم يُفحص ميدانياً", market/MoJ factors).
- **Issue 5:** land swaps building/tenant known-unknowns + due-diligence for
  land-specific items (zoning R1/R2/R3, MoJ deed, site services, permitted
  height, legal restrictions, site grading منسوب, infrastructure).

## Decisions (per Operational_Rules #39)
- **Alias not normalize** (Anas-approved): surgical, regression-safe; a future
  refactor Sprint can unify the literal. → proposed Rule #47.
- Due-diligence land list = 7 questions (Anas-approved; top 5 are the minimum).

## Verification
- New `tests/test_sprint_2p21p0p5_land_polish.py`: **21 checks** (scope, MUC
  factors/unknowns land-vs-building, due-diligence land-vs-building) + explicit
  villa regression checks. **Full standalone suite: all 18 files exit 0.**
  `py_compile` clean on all 6 modified modules.
- Issues 2 + 3 live in the engine output path (need live GIS) → verified
  **post-deploy** on the 5 land PINs (90040668, 74328443, 74430180, 90421755,
  52060090): expect no "نوع غير معروف", address «أرض في {district} — PIN …», no
  negative building value, no building-assumption factor, land-only questions.
- ⚠️ `node --check`: N/A — **index.html not touched** this Sprint.

## Deployment
> Awaiting explicit consent (#32). From `C:\Thammen` per #43:
```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```
Rollback target (2.21.0) on Heroku = the prior release → `heroku rollback`.
Verify: `curl -s https://thammen.qa/api/health | findstr /C:"sprint2p21p0p5"` +
re-run the 5-PIN API smoke + browser visual on الخور 74328443.

## What's NOT in this patch
- Apartment/commercial input (2.21.1 / 2.21.2). Size/corner adjustments (2.20.1 /
  E12). Deferred docs (Project_Instructions §11, Rules #46-expansion/#47,
  Session_Log) → updated after deploy success per plan.
