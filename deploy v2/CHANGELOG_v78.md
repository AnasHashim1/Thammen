# CHANGELOG v78 — Sprint "Stage-1 input honesty" — CLOSED (premise falsified)

> ## 🛑 STATUS: CLOSED — PREMISE FALSIFIED AT PHASE 0. **NOT SHIPPED.**
> **No engine change. No deploy. No version bump.** Engine stays
> `thammen-sprint2p22p0a25-moj-source-attribution-ccby` / **Heroku v164** (byte-identical).
> The `a26` engine tag was **never consumed**. `index.html` / `api.py` / `evaluate_unified.py` **UNTOUCHED**.
> This file is a **closure record** in the sprint ledger (#21.7: "CHANGELOG_vN = sprint counter"),
> NOT a Heroku release. **Date:** 2026-06-05.

---

## 1. What the sprint was (scoped, then halted)

**Proposed:** a small `index.html` + copy pass to "close the dead-area-field / over-promise gap" — remove
the editable `عدّل المساحة (م²)` field + its instruction, and soften the "entering details may materially
adjust the estimate" copy, deferring the "details change the estimate" promise to a "forthcoming version."

**Premise (from the brief + `DESIGN_2p23_stage_authority_boundary.md` §2b):** the UI promises interactivity
the engine cannot honour — `/api/evaluate` accepts only `zone/street/building` and rejects every other field
with HTTP 422; the `عدّل المساحة` field has no backend path; the recompute that would make details matter is
Stage 2 (B-2), unbuilt.

## 2. Why this matters — and why it was halted

Phase-0 recon (mandatory before edit) **falsified the premise by live measurement** (a25 / v164, browser-UA
curl per Rule #61). The proposed fix would have **removed a working feature and replaced true copy with false
copy** — a regression. So the sprint was **halted at Phase 0**, before any edit, per the brief's own
"report-back, no edit yet" gate.

## 3. Root cause of the false premise (the measured truth)

1. **The `عدّل المساحة` control sends `override_land_area`, not `area`.** That field **is accepted and
   consumed** on both request models (`api.py:349` `EvaluateRequest`, `api.py:388` `EvaluateDetailsRequest`),
   threaded `req.override_land_area` → `evaluate_unified.py:3324` → `plot_area_override` (`:3646`). It is the
   shipped Sprint 2.21.0.9 multi-QARS override.
   - **Live proof:** `POST /api/evaluate {zone:56,street:565,building:21,override_land_area:600}` → **HTTP
     200**, `user_override_applied=true`, **2,400,000 → 4,300,000** (bracket 450→600 m², method
     `comparison_thin`). The field works end-to-end.
2. **The optional-details form posts to `/api/evaluate/details`, not `/api/evaluate`.** `run()`
   ([index.html:673](index.html)) sends floors / annexes / condition / asking_price / rental_income /
   potential_rental / basement / footprint_m2 / external_majlis / building_age_years / is_luxury / unit-pair —
   **all of which are declared** on `EvaluateDetailsRequest` (`api.py:373-406`) and threaded to the engine
   (`api.py:1041-1046`).
   - **Live proof:** `POST /api/evaluate/details {…,condition:"good",floors:2,basement:true}` → **HTTP 200**,
     2,400,000 → **2,800,000**. No 422.
3. **The brief's `{"area":600}→422` tested a field name nothing in the UI ever sends; the `DESIGN_2p23 §2b`
   claim tested the WRONG ENDPOINT** (`/api/evaluate`, where details are not declared — but the form submits
   to `/details`). There is **no reachable 422 from the actual UI.**

## 4. Disposition

- **CLOSED — premise falsified. Nothing shipped.** No files changed in the engine/frontend.
- **The `عدّل المساحة` field stays** (it is a working Stage-1 override).
- **The "details may adjust the estimate" copy stays** (it is **true today** — details are consumed).
- **Surviving valid theme (kept, re-routed):** the *broader* `DESIGN_2p23` concern — an early unsigned
  estimate that **visually feels too final / authoritative** (§2a / §2b-para2 / §2c authority-finality
  calibration) — is legitimate but is a **2.23.x Stage-2 design item**, NOT a dead-field copy fix. Routed to
  the Stage-2 design session. The stale `§2b` "inert engine / dead area" paragraph was **corrected** this
  pass (it had the endpoint + field-name error above).

## 5. Where the work went instead (re-pointed)

Anas re-pointed the session to **Sprint B-2 condition recon** → deliverable
`docs/PHASE0_B2_condition_recon.md` (commit `ab15a6b`). Headline: **R7 is a calibration + missing-mechanism
problem, NOT UX-prominence** — feeding GT-2 confirmed-sale subjects their correct attributes via `/details`
does not close the residual; only `floors`→BUA moves the headline (+25%-capped, upward-only); condition /
luxury / age contribute zero. See that doc + Session_Log §20.26.

## 6. Verification

- **No deploy, no smoke needed** (nothing shipped). Engine remains a25 / v164.
- Recon evidence is the 4+ live probes recorded in `docs/PHASE0_B2_condition_recon.md` §"ADDENDUM origin" and
  Session_Log §20.26(A).
- DoD test matrix **not re-run** (no code touched; production byte-identical).

## 7. What's NOT in this (scope boundary)

- **No `index.html` / `api.py` / engine change.** No field removed, no copy changed.
- **No engine version bump** (a26 unused; next shipped sprint takes the next a-tag + CHANGELOG number).
- **No B-2 build** — B-2 is a separate Gate-2 sprint (signed brief + §5 audit), framed by the recon.
- **No CLAUDE.md #65a / Project_Instructions change** — live state is unchanged (a25 / v164).
