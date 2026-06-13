# CHANGELOG v116 — Sprint 2.22.0b.33 (DEF-UX14): identity-input default

**Engine:** `thammen-sprint2p22p0b33-identity-input-default` · **SPRINT_TAG** `2.22.0b.33` · api-health `3.1.0-sprint2.22.0b.33`
**Date:** 2026-06-13 · **Files changed:** `index.html` (+42/−1), `evaluate_unified.py` (the 2 version-string lines), `test_sprint_2_22_0b33.py` (new), `test_sprint_2_22_0b32.py` (R6 format re-point, test-only)
**Class:** 🟢 FRONTEND-ONLY / VALUE-INVARIANT (`api.py` UNTOUCHED; the value axis is byte-identical — مبدأ b24 «الرقم واحد للجميع»).
**Gate-2:** signed by delegation (the study `docs/STUDY_persona_simplicity_and_entry_v1.md` §4 + `ISSUES_LOG §4ب-2` route DEF-UX14 as 🟢 value-invariant frontend; the study §5 states Gate-2 applies only to UX17/UX18/B). **Gate-1:** deploy-on-green (PO handoff).

---

## 1. Why this matters

The simple owner (the study's persona) meets **identity-entry friction** before the tool even runs: the address group shows **three bare number fields** (رقم المنطقة / رقم الشارع / رقم المبنى) with **no source hint** — while the PIN field already had one («أدخل رقم القطعة من شهادة الملكية أو خرائط GIS», `index.html:508`). A first-time Qatari owner does not necessarily know *where* the national address comes from. And a returning owner / agent retypes the same identity every visit (E17 «حقل-واحد-أدنى» friction). DEF-UX14 = the study §4 **option D** («افتراضيّ + سطر مساعدة») — the cheapest entry improvement (no GIS, frontend-only).

## 2. Root cause

- `index.html` `grpAddr` (the zone/street/building fields) carried **no `.br-note` help line**; only `grpLand` (PIN) did.
- There was **no client-side memory** of the last identity, so every visit started from empty — fine for the first-time owner, but pure friction for the returning owner / agent.

## 3. What this patch does (frontend, value-invariant)

**(a) Help line on the address input** (nieuwe `.br-note`, visual parity with the PIN hint), placed AFTER the three fields inside `grpAddr`:
> «هذه الأرقام على لوحة عنوان المبنى أو فاتورة كهرماء (المنطقة، ثم الشارع، ثم رقم المبنى).»

It names the two places a Qatari finds the national address (the building address plate + the Kahramaa bill) in the engine's own field order (zone → street → building). The pre-existing PIN hint is untouched.

**(b) Reasonable default = local identity memory.** New pure helpers `_identGet/_identPut/_identDel` (localStorage with an **in-memory fallback** `_identMem`, matching the a24 sessionStorage-gate pattern) + `_saveIdentity` / `_restoreIdentity` / `clearIdentity`:
- `_saveIdentity()` is called inside `run()` **after `bd` is built and validated** — it persists `{tab, zone, street, building, pin}` (NOT `audience` — single-purpose «identity»; the b24 «مالك» default + the role selector are untouched).
- `_restoreIdentity()` is wired to `DOMContentLoaded`: on a return visit it pre-fills the fields, re-selects the land tab when saved, and reveals a small «مسح ✕» link in the form title. **First visit = empty** (`if(!o)return;`) → zero first-time clutter for the new owner.
- `clearIdentity()` empties the four fields, removes the store, and hides the link.

**Privacy:** local-only (no cookie, no server write, the address never leaves the device) — consistent with the a24 sessionStorage gate + the DPIA «we don't store the address» (which is a **server-side** statement; localStorage is the user's own device, exactly like the existing beta-gate flag).

**Value-invariance (structural):** `run()` reads zone/street/building OR pin and builds `bd` **exactly as before**; the identity store only PRE-FILLS the fields. The engine diff is the 2 version-string lines.

## 4. Backend / frontend / schema

- **Backend:** ENGINE_VERSION + SPRINT_TAG bump only. `api.py` UNTOUCHED.
- **Frontend:** the help line + the identity-memory helpers + the «مسح» link + the `run()`/`DOMContentLoaded` wiring.
- **Schema:** none. `/api/evaluate` request body unchanged.

## 5. Verification — empirical evidence

- **py_compile** `evaluate_unified.py` OK.
- **Isolated** `test_sprint_2_22_0b33.py` **33/33** (reads the REAL index.html — E14: the verbatim help line inside grpAddr after the building field + `.br-note` parity + the PIN hint untouched · the store persists tab+4 fields, NOT audience · in-memory fallback · first-visit early-return · land-tab re-select · «مسح» reveal-on-value · DOMContentLoaded + run() wiring · the value-invariance guard that `bd` is built unchanged and the store never feeds `bd`).
- **Sibling re-point (R6/Lesson-2, test-only):** `test_sprint_2_22_0b32.py` pinned `ENGINE_VERSION == b32` literally → re-pointed to a format check (the b19-precedent for the project's own «no exact version pins» rule). b32 = **29/29** after.
- **DoD:** aggregator `run_sprint_2p22p0a_suite.py` **392 ALL COUNTS MATCH** · security `test_sprint_2p16p17_security.py` **15/15** · surface `test_sprint_2p22p0a3_surface_honesty.py` **45/45** · broad auto-walk `2p22p0_pre/run_regression_2p22p0a.py` **101/101 ALL GREEN** (217.6s; the new b33 test joined the walk, 100→101).
- **R14 real-Chromium 390×844** (node absent → Chromium is the JS gate, EXECUTED): first visit → help line verbatim AFTER the building field, within 390 (left 39 / right 351), «مسح» hidden, fields empty · fill 54/541/6 → `_saveIdentity` stores `{tab:address, zone:54, street:541, building:6}` (no audience) · reload → `_restoreIdentity` pre-fills the three fields + «مسح ✕» shown · land flow: PIN 74328443 → reload → inputTab=land, grpLand visible / grpAddr hidden, PIN restored · `clearIdentity` empties + removes the store + hides the link · **no horizontal overflow (docScrollW 390 == clientW 390)** · **0 console errors/warnings**.
- **api.py untouched** — `git diff --name-only` = `index.html`, `evaluate_unified.py` only (the test files are untracked-new / test-only).

## 6. Deployment

```
cd /d "C:\Thammen\deploy v2"
git add index.html evaluate_unified.py test_sprint_2_22_0b33.py test_sprint_2_22_0b32.py CHANGELOG_v116.md docs
git commit -m "Sprint 2.22.0b.33 (DEF-UX14): identity-input default ..."
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 7. Verification curl (post-deploy)

```
curl -s https://thammen.qa/api/health
# expect engine_version: thammen-sprint2p22p0b33-identity-input-default
curl -s https://thammen.qa/ | findstr /C:"لوحة عنوان المبنى"     # help line in the served HTML
curl -s https://thammen.qa/ | findstr /C:"_IDENT_KEY"             # identity store present
```
Plus the 5-anchor value byte-gate (browser-UA curl, #61) — value identical to v203 (frontend/value-invariant).

## 8. What's NOT in this patch

- The other entry-redesign options (study §4): C (autocomplete dropdowns = DEF-UX15), A (smart single field = DEF-UX18), B (map pin = backlog) — each its own sprint.
- `audience` is NOT remembered (single-purpose «identity»; the role default stays the b24 «مالك»).
- **NEXT = DEF-UX12** (the role-driven density hinge — broadcast `audience` in the response → fold-state مالك→مطويّ / متخصّص→مفتوح; the ONE additive server field; study §5).
