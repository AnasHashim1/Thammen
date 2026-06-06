# Phase-0 / §5 recon — Sprint 2.22.0b.2 (guided 3-stage input flow)

> **Status:** READ-ONLY recon. **NOT shipped.** Engine UNCHANGED = a-arc tip
> `thammen-sprint2p22p0b1-geometry-zoning-footprint` / Heroku **v165** / `/api/health`
> `3.1.0-sprint2.22.0b.1`, qars healthy. No `index.html`/`api.py`/engine edit, no Heroku push.
> **Brief = Gate-2 DRAFT awaiting Anas's signature**, and is **NOT on disk** (Rule #63) — this recon
> is the brief-independent §5 groundwork (it measures the LIVE input flow + b1 geometry surface, which
> the replace-vs-wrap decision turns on regardless of final brief wording).
> **Date:** 2026-06-06. **Method:** empirical-first (#33) — live browser-UA curl (#61), `.b2_probe.py`
> (untracked scratch, regenerable).

---

## 1. The one question §5 must answer: REPLACE vs WRAP

Does the guided 3-stage flow **replace** the current input UI with a multi-step wizard, or **wrap** a
staging layer onto the existing single-screen form + results?

**Verdict: WRAP** — settled by both the live architecture and the design intent (DESIGN_2p23 §2b).

### 1.1 The live input flow is already a staged recompute loop

`index.html` today (the "single-screen progressive-disclosure form"):

- **Entry gate** `#betaGate` (a24, session-only consent) — `index.html:298`.
- **Identification** (always visible): address tabs (zone/street/building) XOR land PIN — the
  E17 1-field minimum / Stage-1 identification — `index.html:374-394`.
- **Audience** selector (buyer/seller/investor/valuer) — `index.html:398-403`.
- **Optional details** behind a collapsible toggle `dSec` (`tog()`): floors / basement / annexes /
  external-majlis / condition / **footprint_m2** / building_age / is_luxury / asking / rental /
  tower-rent-pair — `index.html:410-430`. **These ARE the Stage-2 geometry/condition inputs.**
- **Submit** (`index.html:639-679`): if the details toggle is open it packs the fields into `bd` and
  POSTs **`/api/evaluate/details`**; else bare identification → `show(data)` → `go('results')`.
- **Proven re-eval loop**: `window._lastSubmit` (the last body) + `thammenReEvalOverride(area)` re-POST
  the modified body — shipped for the multi-QARS `override_land_area` toggle — `index.html:669-698`.
- **b1 geometry already on results**: the `v.geometry` card "📐 مساحة البناء الأرضي (تقديري — عدّل)"
  renders at `index.html:1157-1169`, gated `hasValuation && v.geometry && v.geometry.suggested_footprint_m2`.

So the primitives b2 needs — a Stage-1 estimate, a footprint/basement input set, and a **revisable
recompute** — **already exist**. b2 = generalise `thammenReEvalOverride` to also carry
`footprint_m2`/`basement`/`floors`, and stage the UI around the existing form + the b1 results card.

### 1.2 The live wrap loop WORKS (measured)

`/api/evaluate` (bare) → `/api/evaluate/details` (confirmed geometry) on 56/565/21:

| call | amount | footprint_basis |
|---|---|---|
| bare `/api/evaluate` | 2,400,000 | assumed (suggested 405) |
| `/details` floors=3, footprint_m2=600 | **2,900,000** | **confirmed** |
| `/details` + basement=true | **2,900,000** (identical) | confirmed — **basement excluded ✓** |

The exact Stage-1→confirm→Stage-2 recompute b2 wants is proven on the live engine **with zero backend
change**. WRAP confirmed empirically.

### 1.3 Why NOT replace

A full wizard rebuild would still reuse the same two endpoints, but would risk regressing **8+ shipped
surfaces**: the a24 consent gate, the multi-QARS `override_land_area` override, the tower-rent
post-classification reveal, the audience selector, and every a17/a19/a21/a24/a25/b1 results surface —
a large, high-risk change inconsistent with "frontend-only, no-backend, consumes b1's geometry surface."

---

## 2. Live geometry-surface behaviour by property class (the Stage-2 trigger map)

Stage-1 bare `/api/evaluate`, `valuation.geometry`:

| property | method | amount | geometry |
|---|---|---|---|
| 56/565/21 Abu Hamour villa | comparison_bracket | 2,400,000 | fp 405 · **assumed** · R1 · 60% · basement_in_comparison=False |
| 54/541/6 Marikh | comparison_thin | 5,400,000 | fp 294 · assumed · R1 · 60% |
| 55/296/13 house→villa | comparison_thin | 2,600,000 | fp 472 · assumed · R1 · 60% |
| 52/903/90 apartment | insufficient_data | None | **(none)** |
| PIN 74328443 raw_land | comparison_bracket | 1,200,000 | fp 276 · assumed · **zone=None** · **80%** |

**The Stage-2 footprint/basement-confirm step must be GATED.** It is meaningful only for **building**
asset-types (villa / house). Today the geometry block surfaces a footprint even on **raw_land** (a bare
plot — fp 276, zone=None, 80% legacy default), where a "ground building footprint" is conceptually
empty; refusals carry no geometry. A naïve "show confirm when `v.geometry` present" rule would wrongly
prompt a building-footprint confirm on bare land.

- **Recommended gate (frontend-only):** show the Stage-2 geometry-confirm step iff the method is a
  `comparison_*` building path AND the subject is villa/house. `v.geometry.zoning_code` presence is a
  convenient proxy — **R1** for the three villa/house cases, **null** for the sampled land — but this
  is n=1 on land; **confirm across more land PINs before relying on `zoning_code` alone**, else gate on
  asset_type explicitly (exclude `raw_land`).
- Pre-existing note: the b1 results card (`index.html:1158`) already renders on raw_land — a minor b1
  display quirk that b2 should tighten (out of b1's villa/house scope).

---

## 3. Findings the brief must resolve (BEFORE the signature)

### F1 — WRAP, frontend-staging only (recommended scope = "A")
Graft the staging onto the existing form + results; reuse `/api/evaluate/details` + the
`window._lastSubmit` re-eval pattern + the b1 geometry results card as the Stage-2 confirm surface.
Reversible, low-risk, no backend.

### F2 — Gate the Stage-2 geometry-confirm to building asset-types
Exclude raw_land + refusal (see §2). Frontend-only.

### F3 — ⚠️ Effective (capped) confirmed footprint is NOT surfaced → frontend-only-vs-tiny-backend FORK
When the user confirms footprint_m2=600, the engine **caps it to the zone ceiling (540)** and the value
moves to 2.9M — but `suggested_footprint_m2` stays at the **assumption (405)**, and there is **no
`effective_footprint_m2`** in the JSON (geometry fields = `{zoning_code, zone_max_coverage_pct,
suggested_footprint_m2, footprint_basis, basement_in_comparison, note_ar}`). So a faithful Stage-2
"you confirmed **X** م²" display must choose:
- **(a) echo the user's raw input (600)** — but the comparison used 540 → mild *derive-don't-author*
  violation (DESIGN_2p23 §2c); OR
- **(b) surface a 1-field backend `effective_footprint_m2`** (the capped value the engine actually
  used) → **b2 is then NOT purely frontend-only** (a tiny additive backend field; still value-invariant);
  OR
- **(c) strictly frontend-only + honest**: the Stage-2 confirm shows **no echoed m²** — just
  "تم اعتماد قيمتك" + the recomputed estimate (no number it cannot stand behind).
**Recommendation:** (b) if a tiny additive field is acceptable (most honest + clearest UX); else (c).
**This is a Gate-2 / scope call for the brief.**

### F4 — basement copy is honest (confirmed live)
floors3+fp600 == floors3+fp600+basement (2.9M) → "السرداب يُعرض/يُلتقَط لكنه لا يُحرّك تقدير المقارنة"
is accurate (b1 §5.5). Keep verbatim.

### F5 — §2b authority/finality dial-down = a SEPARATE Gate-2 (A-vs-B fork)
DESIGN_2p23 §2b's surviving theme ("an early unsigned estimate that visually *feels* final") wants the
**results card** dialled down (lead with a *range* not a point, recalibrate the `🟢 شواهد كافية` badge,
less Stage-1 decomposition). That touches **success-path output = a bigger Gate-2**.
- **Option A** — wrap the *flow* only (Stage-1 "مبدئي" framing + a "حسّن التقدير (Stage 2)" affordance
  around the same results). Smaller, lower-risk, frontend-only.
- **Option B** — A **plus** the §2b visual authority/finality dial-down on the results card.
**Recommendation:** **A now**, defer **B to a separate b.3** with multi-AI on the badge/range copy
(avoid bundling, #38; keeps b2 "frontend-only" clean). Anas's signature resolves A-vs-B.

---

## 4. Mobile (390×844)
b2 = WRAP reuses the proven `.rc`/`.rn`/`.aud-btn` classes (b1 R14 already verified the geometry card at
390×844, no overflow). The added Stage-2 affordance (a button + a confirm step) must be re-measured under
R14 (real Chromium) at build time — not assumed.

## 5. Dependency to proceed to full build
The signed DRAFT must be **saved into `docs/`** (Rule #63) so the build is scoped to the *actual* brief
(esp. the F3 frontend-vs-backend call + the F5 A-vs-B fork). Until then: **HOLD on build** (Gate 2 —
b2 changes what the user sees/does). B-2 (R7) stays **PARKED** on GT-2 n≥20 — untouched.

---

*Phase-0 §5 recon, 2026-06-06. Engine UNCHANGED (b1 / Heroku v165). Read-only; committed origin-only.*
