# BRIEF — Sprint B-2: built-type/condition MECHANISM + Stage-2 elicitation — **SIGNED + KICKOFF AUDIT (PARKED for n≥20)**

> **Status:** Gate-2 **SIGNED by Anas 2026-06-05**. **PARKED** (Fork #2 = WAIT) — **no build, no ship, no
> push** until the Confirmed-Sales GT-2 corpus reaches **n≥20**. Engine unchanged: **a25 / Heroku v164**
> (byte-identical). Supersedes `BRIEF_SprintB_condition_axis_PROPOSAL_2026-06-03`. Authored: Claude.ai
> (methodology) + CC kickoff audit, 2026-06-05.
> **Handshake (#57):** `/api/health` a25/v164, qars healthy, MoJ 156d, `master` @ `71821ac` (docs only this
> session; no engine drift). **Recon basis:** `docs/PHASE0_B2_condition_recon.md` (commit `ab15a6b`).

---

## A. SIGNED DECISIONS (Anas, 2026-06-05 — Gate 2)

| Decision | Choice | Grounds |
|---|---|---|
| **Fork #1 — Lever 2 (DOWN) re-anchor strength** | **MODERATE** | floor + 0–10% band, fenced by the luxury-finish exception (old + luxury-finish → floor +~20%), wide MUC, provisional till n≥20. Recon-backed: V001 (renovated) → floor 2.46M +~20% ≈ **2.95M**, inside the ~2.63–3.2M clearing band; aggressive would under-value renovated old stock, conservative leaves over-anchor. |
| **Fork #2 — ship timing** | **WAIT for n≥20** | Ship the value-changing levers ONLY when calibrated. Engine stays as-is; B-1 already **discloses** the bias; the beta fills the corpus. Never ship an uncalibrated headline value-change (project's hardest discipline). §4 coupling rule forecloses any "collect-but-don't-move" middle path. |
| **Gate 2 (methodology)** | **SIGNED** — mechanism design approved (as refined by the kickoff audit below). | — |
| **Gate 1 (push)** | **N/A this cycle** — nothing ships (parked). | — |

---

## B. RULE #54 WEB-CHECK (the gate — **PASS**, 2026-06-05)

Primary-source check (rics.org + ivsc.org) of the §5 framing citations for the **2025** edition. **Web-check
GATES multi-AI on numbering** (Rule #54 refinement / a22). GPT+Gemini remain Anas's corroboration lane.

| Citation (brief §5) | 2025 status | Verdict |
|---|---|---|
| **VPS 2** = Bases of value, **assumptions and special assumptions** | RICS 2025: "VPS 4 (prev. edition) is now **VPS 2** (Bases of value, assumptions and special assumptions)" | ✅ correct |
| **VPGA 10** = Material Valuation Uncertainty | RICS 2025: VPGA 10 (MVU) updated, effective 31 Jan 2025 | ✅ correct |
| **IVS 102** = Bases of value + **HBU** premise | IVS 2025: IVS 102 = Bases of Value; HBU described under it (a8 App A90) | ✅ correct |
| **"user-STATED (not inspected) condition → assumption-limitation, NOT a Special Assumption"** | RICS special-assumption test = "factors that do **not apply at the valuation date** / would not be considered by a typical market participant." Stated condition **does** apply at the valuation date → ordinary **assumption + limitation-on-inspection** (VPS 2) carrying **MVU (VPGA 10)**. | ✅ correct — NOT a special assumption |
| **Bonus:** IVS 104 (Data & Inputs, new 2025) — *completeness* criterion | Stated-not-inspected + n<20 fails "completeness" → **independently** mandates the provisional MVU bands | ➕ strengthens §6 provisional discipline |

**No correction needed.** Framing is primary-source-sound. Sources:
[RICS Red Book Global](https://www.rics.org/profession-standards/rics-standards-and-guidance/sector-standards/valuation-standards/red-book/red-book-global) ·
[IVSC IVS 2025](https://ivsc.org/new-edition-of-the-international-valuation-standards-ivs-published/).

---

## C. §5 UI-FIRST KICKOFF AUDIT (read-only, live a25/v164, 2026-06-05)

Subjects: V001 56/647/6 (Maamoura, old premium) · V002 56/565/10 + V003 56/565/12 (Abu Hamour, new luxury,
GT-2 SOLD 4.0M) · 56/565/21 (Abu Hamour clean-bracket control). Browser-UA curl (#61).

### C.1 E4 strata n by class (the decisive Risk-A measurement)

| stratum | Abu Hamour 56/565 (V002/V003) | Maamoura 56/647 (V001) |
|---|---|---|
| land_priced | n=5 @ 4377 | n=0 |
| aging_stock | n=17 @ 5289 | n=1 @ 5234 |
| modern_stock | n=2 @ 5960 | n=4 @ 5811 |
| **luxury_new** | **n=0 (None)** | **n=0 (None)** |
| land floor (Lever-2 dep) | 3778 ppm² **n=33** | 3768 ppm² **n=20** → est **2,456,736** |
| headline | 2.4M `comparison_bracket` | 3.8M `comparison_widened` |

### C.2 Findings

- **🔴 RISK A CONFIRMED + WORSE.** Lever 1's primary data source — a local `luxury_new` MoJ stratum with
  **n≥10** — is **EMPTY (n=0)** in **both** motivating micro-markets. New-luxury sales aren't registered in
  MoJ (yet/sparse). So Lever 1 cannot "price toward the local luxury_new stratum's own ppm²" where it
  matters; it falls **entirely** to the "provisional band" fallback. ⟹ **Lever 1 must be calibrated from the
  cross-area GT-2 Confirmed-Sales corpus** (a pooled new-luxury-vs-plain ppm² premium), NOT a per-area MoJ
  lookup. **This is the single biggest design consequence — and it hard-reinforces Fork #2 = WAIT** (the
  corpus is the *only* viable Lever-1 calibration source).
- **🟢 LEVER 2 IS DATA-READY.** The land floor (Lever 2's dependency) is robust — V001 n=20 (2,456,736),
  Abu Hamour n=33. Independent of the empty strata. So Lever 2 (the DOWN re-anchor) is buildable + reliable
  the moment we ship; the asymmetry is **Lever 2 ready ≫ Lever 1 (corpus-gated)**.
- **🟢 LEVER 2 IS THE RIGHT TOOL FOR V001 (mechanism-confirmed).** V001's widened headline 5828/m² ≈ the
  *modern* stratum (5811, n=4) — the area's thin old-stock comps (aging n=1, land_priced n=0) let the median
  over-credit the building. MODERATE re-anchor → floor +~20% ≈ 2.95M ≈ clearing band. ✓
- **🟡 RISK B (double-count) bounded by WAIT.** `_building_substantiality` measured +16–20% on V002 (driven
  by `floors`→BUA). Lever 1's premium would stack on this → the combined-uplift ceiling matters, but it is
  "set at calibration" (n≥20) — consistent with WAIT; no interim ceiling needed because nothing ships now.
- **Default-path invariance holds:** no-details evals are byte-identical (recon §1); B-2 will move value
  ONLY when the user elicits + the corpus calibrates.

---

## D. DESIGN REFINEMENTS (fold into the build when B-2 fires)

Reconciled with `PHASE0_B2_condition_recon.md` §6 (B2-F1/F2/F3):

1. **B2-F1 (root) — act on the comparison median/anchor, not just a post-hoc bump.** The median is
   condition/built-type-blind; `/details` only stacks on top. (Unchanged.)
2. **B2-F2 → REFINED by Risk A: Lever 1 = a CORPUS-derived premium, not a per-area `luxury_new` lookup.**
   The per-area MoJ luxury_new stratum is n=0 where needed. Calibrate a *cross-area* new-luxury/plain ppm²
   premium from the GT-2 corpus (n≥20), apply to the local plain median, fenced by the combined-uplift
   ceiling + MUC. (This is a sharpening of brief §2 Lever 1 — Anas aware; does not require re-sign, it
   *implements* §2's "else provisional" as the de-facto primary path until the corpus exists.)
3. **B2-F3 → CONFIRMED data-ready: Lever 2 reuses `_villa_value_floor` (a21).** Floor present even under
   Patch-C suppression (recon F1/F2); n=20–33. MODERATE strength (Fork #1), luxury-finish exception.
4. **Elicitation (§4):** 3 inputs (age / finish-tier / physical-condition) already on `/api/evaluate/details`;
   go prominent + guided + revisable **only when the levers are active** (coupling rule — avoids the Stage-1
   over-promise). Until B-2 ships, they stay as the current optional accordion (honest — they already move
   the size axis).

---

## E. CORPUS REQUIREMENTS — what UNPARKS B-2

B-2 resumes (build → Gate-2 re-confirm of the *coefficients* → Gate-1 push) when:

- **Confirmed-Sales GT-2 corpus reaches n≥20** (2.16.16 revival, fed by the beta + Anas). This is the
  **binding constraint** and the **only** viable calibration source for Lever 1 (per Risk A) and for
  tightening Lever 2's MODERATE band.
- **Capture (so the corpus can calibrate both levers), per confirmed sale:** built-type, **finish tier**
  (standard/good/luxury), **building age**, physical condition, plot m², floors/BUA, **confirmed price** +
  the **plain-comp ppm²** at that area/bracket (to derive the new-luxury premium ratio + the old-stock
  land-clearing ratio). Pool **cross-area** (per-area will stay too thin — Risk A).
- Until then: **B-1 keeps disclosing the bias** (condition caveat + land floor); the engine is unchanged;
  every future B-2-adjusted output will carry MUC + honest-range + "indicative, not authoritative" until
  n≥20 (§6, also anchored in IVS 104 completeness per the web-check).

---

## F. NOT in B-2 (held)
Calibrated coefficients (n≥20-gated). Apartment/tower condition (villa/land scope). Stages 3–5 of the
5-stage UX. The authority/finality **VISUAL** calibration (2.23.x — `DESIGN_2p23` §2a/§2b/§2c, separate
Stage-2 design session). Any push (parked).

---
---

## SIGNED BRIEF — verbatim (Claude.ai, 2026-06-05)

> Persisted per Rule #63 (Claude.ai-authored docs auto-persist). The decisions above (§A) resolve §3/§7;
> the kickoff audit (§C) refines §2 Lever 1 (Risk A).

```
BRIEF — Sprint B-2: built-type/condition MECHANISM + Stage-2 elicitation
Status: Claude.ai methodology proposal · Gate-2 (Anas signs) · supersedes
BRIEF_SprintB_condition_axis_PROPOSAL_2026-06-03 (now recon-informed).
Anchor: read /api/health + on-disk FIRST (#57; live a25/v164). METHODOLOGY / valuation-logic
change → HARD GATE 2 (Anas signs THIS) + HARD GATE 1 (push). §5 UI-first audit MANDATORY at kickoff.

§1 — WHY (recon ab15a6b verdict)
Villa comparison headline is condition-blind. Sole spec lever = _building_substantiality (BUA-size,
+25% cap, UPWARD-ONLY; _age_aware_substantiality_multiplier modulates). condition / is_luxury /
building_age_years do NOT reach the headline (disentangle: only floors→BUA moved V002 +0.4M; condition
/luxury/age each = 0). → new-luxury UNDER-anchors (V002/V003 −27.5% even with correct attrs); old-premium
OVER-anchors (V001 immovable — "10-Year Rule" only zeroes a uplift, never re-anchors to land).
R7 = CALIBRATION + MISSING-MECHANISM, not UX-prominence.

§2 — THE MECHANISM (two levers)
LEVER 1 (UP) finish/new-build premium on comparison ppm²:
  - subject elicits new + luxury-finish → price toward the local luxury_new E4 stratum's OWN ppm²
    (MoJ-derived; E1, NO assumed multiplier) where that stratum n≥10; else a PROVISIONAL band + wide MUC.
  - composes WITH _building_substantiality (size bump stays; this adds the finish/new axis). Global
    combined-uplift ceiling to prevent double-count (value set at calibration).
LEVER 2 (DOWN) 10-Year-Rule land re-anchor — make B-1 value_floor LOAD-BEARING:
  - subject elicits age>10 AND NOT luxury-finish AND headline exceeds B-1 value_floor by >the 0–10% band
    → re-anchor headline DOWN toward floor (+0–10%). Reuse B-1 _villa_value_floor.
  - luxury-finish exception: old BUT luxury-finish retains ~20% building value → floor + ~20%, not full.
  - grounds: Qatar 10-Year Rule (documented) + HBU under VPS 2 / IVS 102.

§3 — GENUINE FORK #1 (Anas — risk/positioning): how aggressively Lever 2 re-anchors.
  LEAN = MODERATE (floor + band, fenced by luxury-finish exception, wide MUC, provisional till n≥20).
  Aggressive = accurate for V001 but risks under-valuing genuinely-renovated old stock; conservative =
  safer, leaves some over-anchor. → confirm/adjust at sign.

§4 — STAGE-2 ELICITATION (UX feeding the levers)
3 inputs → levers (all ALREADY on /api/evaluate/details — Stage-2 makes them PROMINENT + guided AND
wires them to the NEW levers):
  1. build age (yrs) → Lever 2 gate + Lever 1 new-build.
  2. finish tier (standard/good/luxury) → Lever 1 premium + Lever 2 luxury-exception.
  3. physical condition (good/avg/poor) → modest separate adj + MUC escalation (3rd axis; can conflict).
Framed REVISABLE/exploratory (authority/finality note §2b — adjustable, conversational re-estimate loop;
NOT a frozen final figure). COUPLING RULE: inputs go prominent ONLY when the levers are active (never
show inputs that don't move the value — that was the falsified Stage-1 gap).

§5 — RICS FRAMING (multi-AI + web-check GATE — Rule #54 / a22)
  - user-STATED (not inspected) condition → VPS 2 assumption-limitation + VPGA 10 material uncertainty
    (LEAN, per B-1 note; NOT Special Assumption). Confirm via GPT+Gemini identical-prompt pass GATED by
    primary-source web-check (2025 Red Book — models revert to pre-2025 numbering; web-check wins).
  - land re-anchor → HBU under VPS 2 / IVS 102 (mandatory consideration, not ad-hoc).

§6 — PROVISIONAL DISCIPLINE (HARD)
  n=3 GT-2 → coefficients PROVISIONAL: bands + wide MUC + "indicative, not authoritative". HARD GATE:
  NO tightening / no calibration claim until n≥20 GT-2 (Confirmed-Sales 2.16.16 corpus — fed by the beta
  + Anas). Every B-2-adjusted output carries MUC + honest-range until then.

§7 — GENUINE FORK #2 (Anas — ship timing): the levers + prominent elicitation ship TOGETHER (coupling,
§4). So:
  (i) SHIP NOW with CONSERVATIVE provisional bands — corrects the systematic bias on the biased cohorts
      (V002/V003 up, V001 down) roughly, bounded by MUC + exception; OR
  (ii) WAIT for n≥20 — engine stays as-is (bias persists but is DISCLOSED via B-1), beta fills the corpus,
       then ship CALIBRATED.
  LEAN = (ii) — honest-by-design: never ship uncalibrated value-changes; the beta discloses the bias and
  its job is to fill n≥20 (likely soon once the cohort is live). (i) is the faster alternative if you want
  the rough correction sooner. → your call at sign.

§8 — KICKOFF (CC, after sign + multi-AI)
  - §5 UI-first audit: ≥3 real props incl. V001/V002/V003 + a clean control; GIS ground truth; live
    /api/evaluate + /details; grep index.html (inputs render + levers wire); mobile 390×844.
  - RECONCILE with PHASE0_B2_condition_recon.md §6 (candidate brief lines) — on disk (ab15a6b).
  - isolated tests 5+ (REAL production path, Rule #40/E14, incl. V001-003 + fallback); CHANGELOG_v{N};
    ENGINE_VERSION bump (B-series).
  - value-impact is INTENTIONAL: smoke must show the INTENDED movements (V002/V003 up, V001 down) AND the
    NON-elicited default path byte-identical (no details = unchanged).

§9 — NOT in B-2: calibrated coefficients (n≥20-gated); apartment/tower condition (villa/land scope);
Stages 3–5 of the 5-stage UX; the authority/finality VISUAL calibration (2.23.x, separate).
```
