# BRIEF — Confirmation Gate (v4 owner-journey, Screen 2) — **SIGNED (Gate-2)**

> **Status:** Gate-2 **SIGNED** by Anas (sub-decisions resolved below). **Frontend-only · value-invariant (logic).**
> **Grounding:** `DESIGN_2p2x_v4_owner_journey.md` (binding) + `CLAUDE.md #65a` + methodology guardrails.
> **Recon:** `PHASE0_confirmation_gate_recon.md` (frontend-only CONFIRMED — range already in `/api/evaluate`).
> **Multi-AI (Rule #54):** not required (presentation + flow only; no evolving-standard / citation / methodology change).
> **Slug/engine:** Sprint **2.22.0b.2.3** · `thammen-sprint2p22p0b2p3-confirmation-gate`. **SHIPPED → CHANGELOG_v83, §20.34.**

## 1. Why (user problem)
Owner flow jumps from identification straight to a result — no checkpoint to validate the GIS-fetched basis before
the engine values it, and no early de-emphasised range. Exposures: **trust** (number lands without basis affirmation)
+ **correctness** (stale GIS `asset_type`/subtype — E7 / A11, ~9.1% of government buildings — silently changes the
basis). Screen 2 inserts the checkpoint + a muted preliminary **range** early (authority low early, rises with
accountability at Stage 5).

## 2. What this sprint does
Insert **Screen 2 (تأكيد البيانات)** into the v4 flow, after identification (Screen 1) and before enrichment
(Screen 3, تحسين). **Review** (read-only) the GIS-fetched attributes; **explicit confirmation** to proceed (no
auto-advance); surface the estimate **as a muted range early** (minimal treatment — the symmetric-± headline is a
later thin-flow step). Renders from the **same** `/api/evaluate` response (no second fetch).

## 3. Presentation guardrails (core axis)
Value-invariant logic (`api.py` + `evaluate_unified.py` UNTOUCHED — recon-confirmed the range/attrs are already in the
response). Authority low early (range muted, explicitly preliminary; never a confident point). Explanation ≠ confidence
(Screen 2 verifies, doesn't persuade). B-1 / decomposition stays OUT of Screen 2 (it lives in the polished result/report
— the corrected b.2.2 first-error, not regressed). RICS/IVS citations + `methodology_ar` UNCHANGED.

## 4. Out of scope
Condition input / B-2 (PARKED n≥20) · range-headline ±-bar (next step) · decomposition surfacing (later step) ·
inline correction of fetched attributes (deferred micro-sprint, §5.2) · capture/instrumentation activation (DORMANT).

## 5. Gate-2 sub-decisions — **SIGNED**
- **5.1 — Preliminary range: ALONGSIDE the review card, MUTED** (matches mockup). Render `valuation.low–high` as the
  range, labelled preliminary.
- **5.2 — READ-ONLY this sprint.** Drop the mockup's ✏ pencils + «✎ صحّح» — review + confirm only. Inline correction
  (esp. `asset_type` → E7/A11) = a separate future micro-sprint (value-affecting input → its own scope + tests, #38).
- **5.3 — Copy.** Frame kept «تقدير مبدئي (نطاق)». **Confirm CTA CHANGED → «تابِع بهذه البيانات»** (read-only honesty —
  don't make the user certify data they can't fix), NOT the DRAFT's «البيانات صحيحة — تابِع». Explicit affirmative
  action / no auto-advance preserved.

### Copy (Arabic-primary · English mirror) — as shipped
- Heading: «راجِع بيانات العقار» / *Review the property details*
- Subtext: «هذه البيانات مجلوبة من نظام المعلومات الجغرافية (GIS). راجِعها قبل المتابعة.» / *fetched from Qatar GIS — review before continuing.*
- Range label: «تقدير مبدئي (نطاق)» / *Preliminary estimate (range)*
- Range subtext: «تقدير أوّليّ قابل للتغيّر بعد التأكيد والتحسين.» / *Initial estimate, subject to change after confirmation and refinement.*
- Confirm CTA: «تابِع بهذه البيانات» / *Continue with these details*
- Permanent escape: «التقرير الكامل الآن» / *Full report now* — straight to the results render (no 2nd fetch).
- **Plot-area label (honesty):** show the engine-used `plot_area_m2` (450 for 56/565/21, post multi-QARS); when it
  differs from the raw cadastral (900) label it **«المساحة المعتمدة في التقدير»**, else «مساحة القسيمة».
- Use existing AR labels for `asset_type`/`district` (`ASSET_AR` → «فيلا منفردة»).

## 6. As-built (Rule #39 flag)
**Valuer + refusals skip the gate → results** (v4 two-path «مُقيّم → التقرير الكامل مباشرة»; refusals have no valuation).
The gate fires only for a **valued, non-valuer** journey. The Stage-2 inputs route to the existing `refineScreen`
(confirm → refine) — same endpoint/pattern. `confirmScreen` is a new `.screen`; `showConfirm()`/`confirmProceed()`
are new render/nav fns; `run()` gained the one routing intercept.

## 7. Verification (R14 + DoD — EXECUTED)
Engine diff = 2 version lines (value-invariant). Isolated 32/32. DoD 392 / 15 / 45 / **71**. R14 real-Chromium: 9 fns
defined, **0 console errors**, full live flow (buyer → confirm; CTA → refine; full-report → results; valuer → results),
**no overflow at 390 / 375 / 1265**. (Full evidence: CHANGELOG_v83 §5, Session_Log §20.34.)

## 8. Gates
ENGINE_VERSION + SPRINT_TAG bumped; CHANGELOG_v83 (8-section); this SIGNED brief saved. **Gate-1: STOP for Anas's
explicit in-session push consent** before `git subtree push --prefix "deploy v2" heroku master` + `git push origin master`.
