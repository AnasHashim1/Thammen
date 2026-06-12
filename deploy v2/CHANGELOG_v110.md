# CHANGELOG v110 — Sprint 2.22.0b.27 «هوية الشاشات الأولى» (م4 — the first-screens thm-report identity)

**Engine:** `thammen-sprint2p22p0b27-first-screens-identity` · **Date:** 2026-06-12
**Files:** `index.html` · `evaluate_unified.py` (version strings ONLY) · `test_sprint_2_22_0b27.py` (new)
**Program:** م4 (the final build phase) of «الواجهة والتقريران» — the signed directive: dress screens 1–5 in the thm-report components per the v3 contract + regroup the refine screen into the three tagged groups + the setbacks equation under the building area. 🟢 **FRONTEND-ONLY / VALUE-INVARIANT** — engine diff = the 2 version lines; `api.py` UNTOUCHED; zero field-id changes (the re-eval JS reads by id).

## 1. Why this matters
The refine screen threw 12 fields at the user in one wall with no effect-honesty; the journey screens carried none of the report identity; the auto building-footprint showed a number without its legal derivation. The v3 contract fixes all three: grouped inputs TAGGED by their REAL effect (أبو محمد sees one group; المثمّن sees the methodological separation), one visual identity, and the E15 setbacks equation disclosed.

## 2–3. What this patch does
- **The thmr identity on the five journey screens** (home · the consent gate · form · confirm · refine get the `.thmr` scope — the م2 IBM Plex font + tokens; the results screen stays per the signed 1–5 scope).
- **The refine three-group regroup (v3):** `<details class="thmr-grp">` ×3 — **١ الهندسة** [open · «يحرّك التقدير»]: floors/basement/penthouse/annexes/majlis/footprint+hint · **٢ العمر والحالة** [«يدقّق مرتكز التكلفة»]: age (+ the E24 floor micro)/condition/is_luxury · **٣ معلومات مالية** [«اختياري للإثراء»]: actual rent (+ the income-lead gold hint)/expected rent/asking price (+ the E1 «لا يؤثّر — الأسعار المعلنة ليست أدلّة» micro). **`towerRentSection` stays UNGROUPED** above the groups (the 2.16.10/b22 tower reveal+focus flow untouched). **The focus helper now opens a closed `<details>` ancestor** (the b13 age-nudge + rent CTAs keep working — caught in the R14 walk, fixed pre-ship).
- **The setbacks equation (E15)** under the building area on BOTH sites — the refine hint + the confirm basis row: «بعد الارتدادات القانونية (أمامي 5 · جانبي 3 · خلفي 3) وضمن سقف تغطية 60%» — **setback-envelope plots only** (the coverage-cap/shared methods make no setbacks claim).

## 4. Backend / frontend / schema
Frontend only. No schema. No engine logic.

## 5. Verification — empirical evidence
- Isolated `test_sprint_2_22_0b27.py` **23/23** (the five thmr screens · exactly 3 groups + tags + the open default · EVERY field id unchanged · group assignment order · towerRentSection ungrouped · the details-opening focus fix · the two equation sites + the honest gating · version format).
- Siblings green **WITHOUT re-points** (the ids/flows held): b2p1 26 · b13 37 · b22 63 · b2p3 32 · b15 49 · b24 58 · b25 74 · b26 33 · b9 29 · b10 31. DoD aggregator **392 MATCH** · security **15/15** · surface **45/45** · broad walk → the close-out.
- **R14 real-Chromium 390×844:** the 3 groups render (١ open, the tags verbatim) · all 14 field ids resolvable · the tower flow proven (visible on tower + ungrouped) · closed-group values still readable by the re-eval reader · the focus logic opens group ٢ · IBM Plex applied on the refine summaries · the equation in both JS sites · **0 console errors** · docScrollW 390==390.

## 6–7. Deployment + verification
```
git subtree push --prefix "deploy v2" heroku master ; git push origin master
curl -s https://thammen.qa/api/health | findstr "b27"
curl -s https://thammen.qa/ -A "Mozilla/5.0" | findstr /C:"يحرّك التقدير" /C:"يدقّق مرتكز التكلفة" /C:"بعد الارتدادات القانونية"
```

## 8. What's NOT in this patch
- No value change; no field renamed/removed; the bare-eval and `/details` payload mapping untouched.
- The app-shell global font stays Tajawal outside the five screens + the reports (a site-wide identity = the plan's D7 «سبرنت مستقل لاحق» — the PO's call).
- The results screen (b15) keeps its current identity — its future relationship to the D6 short-report-first flow is a product question outside م4's signed text.
- Live evaluate smoke → the deferred basket (khazna R5).
