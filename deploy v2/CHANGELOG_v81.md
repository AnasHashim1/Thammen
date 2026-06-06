# CHANGELOG v81 — Sprint 2.22.0b.2.1 (Separate input screens, structural)

**Engine:** `thammen-sprint2p22p0b2p1-separate-input-screens` · **SPRINT_TAG** `2.22.0b.2.1` ·
api-health `3.1.0-sprint2.22.0b.2.1`
**Date:** 2026-06-06
**Files changed:** `index.html` (frontend restructure) · `evaluate_unified.py` (version-string bump ONLY) ·
`test_sprint_2_22_0b2p1.py` (new, 26 checks) · `CHANGELOG_v81.md` ·
`docs/BRIEF_Sprint2p22p0b2p1_separate_input_screens_SIGNED.md`
**Lane:** Gate-2 SIGNED brief (Claude.ai) → CC §5 recon (reshaped the first draft) → CC build. **Frontend-only;
engine logic UNTOUCHED.** Gate-1 (Heroku push) = separate explicit consent.

---

## 1. Why this matters
The optional property details (`dSec` — floors/footprint/basement/condition/age/luxury/annexes/majlis +
asking/rent) sat on the SAME page as the identification inputs, behind a toggle. b2 then added an in-results
"Stage-2 confirm" *card* with its own duplicate geometry inputs. Two input surfaces, one page. This sprint
gives the staged flow a clean structural skeleton: **identification on its own screen, the optional details on
their own screen, and the results card reduced to a display + a button** that navigates to the details screen.
It fixes the same-page crowding and makes "Stage 1 → Stage 2" an explicit screen transition (E16). **No value,
no report content, no methodology changes** — only WHERE the user enters inputs.

## 2. Root cause (structure being changed)
- `formScreen` (`index.html:366`) held identification **and** the collapsible `dSec` details block
  (`id="dSec"`@410, toggled by `tog()`@611). `run()` read `dSec` (when open) and **always** POSTed
  `/api/evaluate/details`.
- The b2 in-results staging card (~1204–1231) carried its OWN inputs (`b2Floors`/`b2Footprint`/`b2Basement`)
  and submitted inline via `thammenReEvalGeometry()`@742.
- `go(n)`@498 is a clean screen-switcher (`.screen` → `#{n}Screen`) — adding a 4th screen is trivial.

## 3. What this patch does (frontend only, `index.html`)
1. **`formScreen` → identification-only.** Removed the `dSec` fcard + the `tog()` toggle + `dOpen`. `run()` now
   POSTs the **bare `/api/evaluate`** and sets `window._lastSubmit.endpoint='/api/evaluate'` (both endpoints
   accept `override_land_area`, so the multi-QARS override path is unaffected — §20.26).
2. **NEW `refineScreen`** (4th `.screen`, `go('refine')`): the relocated `dSec` inputs (same IDs), always
   visible, financial group marked secondary, with a «احسب التقدير المُحسَّن» submit + a «→ رجوع للنتيجة» back
   button.
3. **`thammenReEvalGeometry()` rewritten** to read the relocated full detail set (mirrors run()'s prior
   mapping, with `else delete` so re-refining never carries a stale field), POST `/api/evaluate/details`, then
   `go('results')`.
4. **Results staging card → DISPLAY-ONLY.** Kept the F2 gate (`_b2IsBuilding`), the assumed/confirmed footprint
   note, the F3 zone-cap disclosure, and the verbatim F4 basement copy. Removed the in-card inputs; the button
   now navigates `go('refine')` (label «حسّن التقدير (المرحلة 2)» / «عدّل التفاصيل» when confirmed).
5. **Tower/apartment path preserved (Rule #39 deviation, flagged).** `dSec` also hosted `towerRentSection`
   (the tower/apartment rent split reached by the insufficient-data CTA `goForm()`). The whole optional-details
   block moved to `refineScreen`, and `goForm()` was redirected `go('form')`→`go('refine')`. F2 still gates only
   the villa/house geometry card/button; tower/apartment reach `refine` via their own CTA, exactly as before.
6. `evaluate_unified.py`: ENGINE_VERSION/SPRINT_TAG bump only (diff = 2 lines). `api.py` UNTOUCHED.

## 4. Verification — empirical evidence
- **py_compile** OK (`evaluate_unified.py` + `api.py`).
- **Isolated** `test_sprint_2_22_0b2p1.py` — **26/26** (reads the REAL `index.html`, E14: refineScreen exists +
  go() switcher; every detail input relocated to refine / none left on the form / no duplication; run() →
  bare `/api/evaluate`, `if(dOpen)` gone; card display-only + `go('refine')`, F2 intact, b2* inputs gone, F3/F4
  retained; thammenReEvalGeometry reads relocated inputs + `/details` + `go('results')`; tower CTA → refine;
  tog()/dOpen removed; version format).
- **DoD regression** (PYTHONIOENCODING=utf-8): aggregator `run_sprint_2p22p0a_suite.py` = **392** (ALL COUNTS
  MATCH) · security = **15/15** · surface-honesty = **45/45** · broad auto-walk = **69/69** (176.6s, no flake;
  68→69 with the new test). `test_sprint_2_22_0b2.py` (backend F3 + helpers) still green — it asserts no
  frontend structure, so the restructure doesn't touch it.
- **Value-invariance — engine diff is version-string ONLY** (2 lines) → output byte-identical by construction.
  Corroborated live (v166, browser-UA curl, Rule #61) on the **new identification endpoint** `/api/evaluate`
  (bare): 56/565/21 = **2,400,000** (comparison_bracket) · 54/541/6 = **5,400,000** (comparison_thin) ·
  55/296/13 = **2,600,000** (comparison_thin) · 52/903/90 = **None** (apartment refusal). All match the v166
  anchors → `/api/evaluate` ≡ `/api/evaluate/details`-empty proven across all 4 anchors. `/details` fp600 =
  **2,900,000** + `effective_footprint_m2:540` (confirmed) — unchanged.
- **R14 real-Chromium** (served `index.html`, real-payload mocks routed same-origin to avoid CORS; Claude_Preview):
  all 9 inline functions defined, **0 console errors** (load + full flow). **390×844:** `form` (identification-
  only, scrollW 390, no overflow, no detail-input leak) → bare eval → `results` (2.4M, geometry card «المرحلة 2»,
  button → `go('refine')`, NO b2 inputs, no overflow) → `refine` (all inputs present incl. tower split, scrollW
  390, no overflow) → submit fp600 → `results` refined (**2.9M**, «مؤكَّد ✓» + «اعتُمدت مساحة البناء الأرضية ٥٤٠
  م²» [F3] + F4 basement note + «عدّل التفاصيل»). Tower CTA: `goForm('rentalIncome')` → `refineScreen` +
  `towerRentSection` visible + tower-mode rental label. **Desktop 1280×800:** form/refine/results all no overflow.
  (A pre-existing ~625px intermediate-band 7px overflow on the form's unchanged `.fr3` identification row is NOT a
  b2.1 regression — the change removed content vertically, not horizontally.)

## 5. Deployment (Gate-1 — PENDING Anas's explicit in-session consent)
```
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
> Not yet executed. The post-deploy live smoke (below) is recorded here only after the Gate-1 push.

## 6. Verification curl (post-deploy)
```
curl -s https://thammen.qa/api/health
:: expect "version":"3.1.0-sprint2.22.0b.2.1" + engine ...b2p1 + qars healthy
curl -s -X POST https://thammen.qa/api/evaluate -A "Mozilla/5.0 ... Chrome" -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21}"
:: expect valuation.amount 2,400,000 + valuation.geometry.footprint_basis "assumed"
curl -s -X POST https://thammen.qa/api/evaluate/details -A "Mozilla/5.0 ... Chrome" -H "Content-Type: application/json" -d "{\"zone\":56,\"street\":565,\"building\":21,\"floors\":3,\"footprint_m2\":600}"
:: expect valuation.amount 2,900,000 + valuation.geometry.effective_footprint_m2 540
```

## 7. What's NOT in this patch (scope boundary)
- **No** authority/finality dial-down (range-as-lead, recalibrate «🟢 شواهد كافية») — the open §2b strategic fork
  (`DESIGN_2p23` §4), Anas's deliberate decision. Candidate **b.3** (own brief + multi-AI).
- **No** permanent honest frame, component diagnosis, decision-framed acts, or uncertainty re-sequencing
  (the deferred staged-reveal vision).
- **No** backend / valuation / report-content change. **No** `api.py` change.
- **No** B-2 (R7 condition mechanism) — PARKED on n≥20.
