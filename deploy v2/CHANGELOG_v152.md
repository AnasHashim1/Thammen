# CHANGELOG v152 — Sprint 2.22.0b.71 «بنية محور الحالة القابلة للتكيّف» (condition-axis adaptable infrastructure)

**Engine:** `thammen-sprint2p22p0b71-condition-axis-infra` · **SPRINT_TAG** `2.22.0b.71` · **Date:** 2026-06-26
**Files:** `condition_calibrator.py` (NEW, offline build tool) · `condition_adjustments.sqlite` (NEW, committed read-only seed) · `evaluate_unified.py` (`_COND_ADJ_DB` const + `_lookup_condition_penalty` + the 1-line seam at the DRC penalty site + 2 version lines) · `test_sprint_2_22_0b71.py` (NEW) · `CHANGELOG_v152.md` · `docs/Session_Log.md`
**Class:** 🟢 BACKEND-ONLY / **VALUE-INVARIANT** (the seed penalties EQUAL the hardcoded ladder → byte-identical; `api.py` + `index.html` UNTOUCHED). 🔴 Gate-2 by class (touches the value path) — **SIGNED** (PO «وقّع المعمارية الآن وابن»).

## 1. Why this matters — the PO's binding architectural directive
The condition axis (B-2 / R7) is the durable over/under-anchor fix. The PO's directive: **build it NOW with the data we have (V001 = the bank's certified appraisal, our benchmark #1) — but architected so that when confirmed-sale data arrives, the SITE STRUCTURE and CODE do NOT change, only the NUMBERS change.** «الرقم يتغيّر لا الكود.» The infrastructure must be ready + ADAPTABLE, never rebuilt from scratch.

This sprint ships **B2-1: the adaptable calibration infrastructure** — the first of the signed slices (the design brief, workflow `wf_36d291d8-0cb`). It separates the **STABLE MECHANISM** (code) from the **DATA-DRIVEN CALIBRATION** (a swappable DB), on the EXISTING `cap_rates.sqlite` precedent.

## 2. What this patch does
- **`condition_adjustments.sqlite`** (NEW, committed read-only — the `cap_rates.sqlite` / Operational_Rules #43 precedent): holds the per-grade effective-age PENALTIES the DRC reads. Columns: `area_match_key · built_type_stratum · condition · penalty_years · sample_size · confidence · source · last_updated · notes`. **Seeded n=1 from the V001 ladder** (source=`v001_seed`, confidence=`indicative` — n=1 is disclosed-indicative, NEVER `reliable`).
- **`_lookup_condition_penalty(condition, area_name=None, built_type_stratum=None)`** (NEW in `evaluate_unified.py`, twin of `_lookup_calibrated_cap_rate`): read-only (`mode=ro`), confidence-gated (`reliable`/`indicative` only), **safe-fail `(None,None)`** on any missing-DB / schema-drift / exception. Future-proof signature: at n=1 only GLOBAL rows exist (so area/stratum don't yet matter — the global penalty wins); when the corpus emits per-(area,stratum,condition) cells, the SAME code PREFERS them (sorts, never filters → a global row always survives). Integer seed → returned as `int` (byte-identical emit); calibrated non-integer medians stay `float`.
- **The seam** (`_cost_approach_value`, the DRC penalty site): `_cp,_ = _lookup_condition_penalty(condition); penalty = _cp if _cp is not None else COST_CONDITION_PENALTY.get(...)`. The hardcoded dict stays the guaranteed fallback. `is not None` keeps `new`=0 and the negative trims (excellent −2 / renovated −3) honored. **NOTHING else in `_cost_approach_value` changes** — the returned dict is byte-identical.
- **`condition_calibrator.py`** (NEW, offline, pure stdlib): `build_seed_db()` seeds n=1 from `_SEED_PENALTIES` (a sync-guarded mirror of `COST_CONDITION_PENALTY`); `calibrate_from_corpus(corpus)` re-fits per-(area,stratum,condition) penalties from the GT-2 documented-sale corpus, gates confidence on n (≥20 reliable / 10-19 indicative / <10 → seed stands), and DROP+recreates the DB — **engine code UNCHANGED, only the DB swaps**.

## 3. Verification — empirical evidence
- isolated `test_sprint_2_22_0b71.py` **18/18**: the sync-guard (`_SEED_PENALTIES == COST_CONDITION_PENALTY`) · lookup==dict for every grade · negative/zero penalties honored + int-typed · provenance (v001_seed/indicative) · unknown/empty → (None,None) · **safe-fail** (missing DB → fallback) · **VALUE NO-OP** (`_cost_approach_value` byte-identical DB-present-seed vs DB-absent-hardcoded, 9 conditions incl. none/average/teardown) · `new`=0 distinct from the +8 default · **CALIBRATOR ROUND-TRIP** (synthetic n=22 corpus → a `reliable` `gt_corpus` row → the engine reads the calibrated penalty 30 with ZERO code change; n=5 cell gated out → the seed stands) · seed DB indicative-only.
- DoD: aggregator **395/395 MATCH** · security **16/16** · surface **45/45** · broad walk **127/127** (126→127, +b71).
- **VALUE-INVARIANCE — proven by construction:** the isolated DB-present-vs-absent test IS the old-behavior-vs-new-behavior comparison (absent = the old hardcoded path); they are byte-identical. The 5-fixture value byte-gate is byte-identical because (a) the seed == the hardcoded ladder and (b) the 5 fixtures supply no user condition → the no-input default (+8) path, unchanged.
- **R14: N/A** — backend-only, `index.html` git-confirmed UNTOUCHED → the served page renders identically (the §20.18 backend-only precedent).

## 4. The adaptability contract (the PO's «الرقم يتغيّر لا الكود»)
When the GT-2 confirmed-sale corpus reaches n≥20 in an (area, stratum, condition) cell: run `condition_calibrator.calibrate_from_corpus(gt_corpus.local.json)` → it DROP+recreates `condition_adjustments.sqlite` with the re-fitted, `reliable` numbers → commit the new DB → deploy. **The engine code does not change.** The round-trip test proves this end-to-end today. Per-stratum threading at the call-site (so a luxury_new villa reads a different penalty than an aging_stock one) is a documented later slice — the GLOBAL penalties already auto-update with zero code change.

## 5. Deployment
```
git add "deploy v2/condition_calibrator.py" "deploy v2/condition_adjustments.sqlite" "deploy v2/evaluate_unified.py" "deploy v2/test_sprint_2_22_0b71.py" "deploy v2/CHANGELOG_v152.md" "deploy v2/docs/Session_Log.md"
git commit -m "Sprint 2.22.0b.71: condition-axis adaptable calibration infra (DB+lookup+seam, seeded n=1 from V001); value-invariant"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health   # → engine thammen-sprint2p22p0b71-condition-axis-infra
# 5-fixture value byte-gate identical (no user condition → the +8 default path, byte-identical).
```

## 7. What's NOT in this patch (the next signed slices)
- **B2-3 (RICS disclosure reword, value-invariant):** user-supplied condition → "stated Assumption, not inspected" + limitation-on-inspection + Material Uncertainty (VPGA 10 / VPS 2). Lawyer + linguist personas.
- **Per-stratum activation (data-gated):** thread area_name/built_type_stratum into the call-site so the engine reads per-stratum cells; materializes when the corpus has them.
- **The numbers recalibrate (data-gated):** `calibrate_from_corpus` re-fits at n≥20 — no new sprint code, the DB swaps. The RICS condition-standards + global-AVM-practice web research (2 of 4 tracks) were rate-limited and are owed before the disclosure-reword sign-off (Rule #54), though the disclosure reuses our already-in-production a17/a19/a20 VPS 2 / VPGA 10 posture.
- No `index.html` / `api.py` change; no methodology number invented (the b16/E25 discipline — re-sourced from V001, disclosed indicative).
