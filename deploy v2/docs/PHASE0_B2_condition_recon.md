# PHASE 0 — Sprint B-2 Recon (condition / age axis) — READ-ONLY

> **Status:** Phase-0 empirical recon for **Sprint B-2** (the durable R7 fix — built-type / age /
> condition axis). **READ-ONLY** — no source edits, no deploy, production byte-identical (Heroku
> **v164** / a25). Triggers **no gate**. **Reports, does not fix.**
> **Authored:** CC, 2026-06-05.
> **Handshake (Rule #57):** `/api/health` = engine `thammen-sprint2p22p0a25-moj-source-attribution-ccby`,
> version `3.1.0-sprint2.22.0a.25`, qars `healthy`, MoJ **156d** stale, `master == origin` (`1eeb948`,
> 0 ahead/0 behind). **No drift** (live a25/v164 == brief).
> **Method:** live `POST /api/evaluate` + `POST /api/evaluate/details` (browser-UA curl, Rule #61) on the
> 3 ground-truth subjects (V001/V002/V003 from `docs/validation/VALIDATION_LOG.md`) + single-axis
> disentangle + code trace of `evaluate_unified._age_aware_substantiality_multiplier` /
> `_building_substantiality` (the only headline age/size lever) + `api.EvaluateDetailsRequest`.

> **ADDENDUM origin (this session):** the *Stage-1 input-honesty* sprint that opened this session was
> **halted at Phase 0** — its premise (a "dead `area` field" + an "inert engine" that "rejects every
> field") was **falsified by measurement**: the `عدّل المساحة` control sends `override_land_area`
> (accepted + consumed — 56/565/21 2.4M → **4.3M** at override 600 m²), and the optional-details form
> posts to `/api/evaluate/details`, where **every** field is declared and consumed. The
> `DESIGN_2p23 §2b` "completely inert engine" claim tested the **wrong endpoint** (`/api/evaluate`) with
> the **wrong field name** (`area`, not `override_land_area`). Anas then re-pointed the task to **this**
> B-2 recon. **Consequence for B-2:** the condition/age input plumbing is **NOT greenfield** — it exists
> and partially fires. The central question is therefore re-framed below.

---

## CENTRAL QUESTION

**Is R7 (the condition/built-type over/under-anchor) a UX-PROMINENCE problem** (the adjustment exists,
but the default flow is blind because users don't fill the optional details) **or a CALIBRATION problem**
(the `/details` adjustment is mis-sized) **— or a mix?**

## TL;DR — VERDICT

🔴 **R7 is a CALIBRATION + MISSING-MECHANISM problem. It is decisively NOT a UX-prominence problem.**

Feeding the GT-2 confirmed-sale subjects their **correct attributes** through the existing
`/api/evaluate/details` path **does NOT close the residual** on any of the three:

| subject | GT (tier) | default flow (no details) | best with FULL correct attrs | residual after /details | gap closed |
|---|---|---|---|---|---|
| **V002** 56/565/10 | **4.0M sold (GT-2)** | 2.50M (**−37.5%**) | **2.90M** (−27.5%) | **still −27.5% under** | ~27% |
| **V003** 56/565/12 | **4.0M sold (GT-2)** | 2.40M (**−40.0%**) | **2.90M** (−27.5%) | **still −27.5% under** | ~31% |
| **V001** 56/647/6 | ~2.9M clears (GT-3 ask 3.8M) | 3.80M (**+31% over**) | **3.70M** (+28% over) | **~immovable** | ~3% |

And the disentangle shows the small movement that *does* occur comes from the **wrong axis**: only
**building SIZE** (floors→BUA) moves the headline. **Condition, finish/luxury, age, and new-ness have
ZERO independent effect.** So making elicitation more prominent would change **nothing** for these cases —
the engine does not price the axes R7 is about.

**Per the brief's own decision rule:** "*If /details does NOT close → adjustments mis-calibrated →
recalibration is the core work.*" → **confirmed**, with the sharper finding that it is not merely
mis-sized coefficients but a **missing mechanism** (no condition/finish premium tied to the comparable
ppm²; no down-re-anchor toward land for old non-luxury stock).

---

## 1. The decisive probe (per property)

All live, a25 / v164, 2026-06-05, browser-UA curl. "best attrs" = `condition` + `is_luxury` + `building_age_years` + `floors` set to the subject's reality.

### V002 56/565/10 — NEW luxury, 450 m², G+1+penthouse, **SOLD 4.0M (GT-2)** → per-m² 8,889
- baseline `{zone,street,building}` → **2,500,000** · `comparison_bracket` · land ppm² **3778 (n=33)** · `condition_note_ar` present
- `+ condition:new, is_luxury:true, building_age_years:2, floors:3` → **2,900,000** · `comparison_bracket` · land ppm² **3778 (n=33, unchanged)**
- **Movement +0.40M (+16%). Target +1.5M (+60%). Residual −27.5% UNCLOSED.** per-m² 5,556 → 6,444 vs GT 8,889.

### V003 56/565/12 — adjacent identical twin, **SOLD 4.0M (GT-2)**
- baseline → **2,400,000** · `comparison_bracket`
- `+ full attrs` → **2,900,000**. **Movement +0.50M (+21%). Residual −27.5% UNCLOSED.**

### V001 56/647/6 — OLD (~25y) renovated/high-finish, 652 m², **ask 3.8M (GT-3, unsold ~5-6y, clears ~2.63–3.2M)**
- baseline → **3,800,000** · `comparison_widened` · land ppm² **3768 (n=20)**
- `+ condition:renovated, building_age_years:25, is_luxury:false` → **3,700,000**
- `+ ... is_luxury:true` → **3,700,000** (luxury flag = **no difference**)
- **Movement −0.10M (−2.6%). The over-anchor is immovable downward. UNCLOSED.**

> Note (Rule #36): V001's GT is **GT-3 (asking)** — directional only; the clearing band (~2.63–3.2M) is
> the analyst read (VALIDATION_LOG V001), not a confirmed sale. V002/V003 are **GT-2 (confirmed sales)** —
> strong. The over-anchor direction is sound; its magnitude is the soft number.

---

## 2. Three-axis disentangle (single-axis, V002 baseline 2.5M / GT 4.0M)

| input set (alone) | amount | Δ vs baseline | axis |
|---|---|---|---|
| `floors=3` | **2,900,000** | **+0.40M** | **PHYSICAL/SIZE — the ONLY live lever** |
| `floors=3 + footprint_m2=300` | **3,000,000** | +0.50M | PHYSICAL/SIZE (bigger BUA → bigger bump) |
| `condition=new` | 2,500,000 | **0** | FINISH — inert |
| `condition=renovated` | 2,500,000 | **0** | FINISH — inert |
| `is_luxury=true` | 2,500,000 | **0** | FINISH — inert |
| `building_age_years=2` | 2,500,000 | **0** | AGE — inert |
| `footprint_m2=300` (alone) | 2,500,000 | **0** | (no extra floors → BUA ≈ typical → 0) |

V001 (old, baseline 3.8M): `building_age_years=25` alone → 3.70M (−0.1M, negligible); `condition=maintenance` alone → 3.80M (**0**).

**Reading:** the estimate responds **only to declared building SIZE** (floors / footprint → BUA). The
**age** and **finish/condition** axes are mechanically **inert on the headline** — they are *modulators of
a size uplift*, not independent price drivers, and `condition` is not even an input to the lever (§3).

---

## 3. WHY — the mechanism trace (the load-bearing finding)

The **only** place building specs/age/luxury touch the headline `amount` is the Age-Aware Substantiality
Adjustment (`evaluate_unified.py:3925–3944`), and it has three structural properties that explain every
result above:

**(a) It is a BUA-SIZE bump, capped at +25%** (`_building_substantiality`, `evaluate_unified.py:746–815`).
Tiers run **+5% → +25%** on `index = actual_BUA / typical_BUA` (≥2.0→+25%, ≥1.7→+20%, ≥1.45→+15%…). It
measures *how big the building is vs a typical G+1 villa* — **not** finish, condition, or new-ness. So
V002's +16% came from declaring the **penthouse 3rd floor** (index ≈ 1.5), capped well below the **+60%**
the market actually paid for the new premium.

**(b) It is UPWARD-ONLY in the unified pipeline.** Verbatim (`:774`): *"Downward adjustments are NOT
applied in the unified pipeline (only upward)."* `adj_pct = max(0, raw_bua_adj) × age_mult ≥ 0`, then
`amount = base × (1 + adj_pct)`. **There is no path by which any input pushes the value DOWN toward land.**
That is why V001 (over-anchored at the condition-blind widened median) is immovable: the engine can only
*add* a size premium or *suppress* it — never re-anchor down.

**(c) Age / luxury only MODULATE the size bump** (`_age_aware_substantiality_multiplier`, `:835–861`):
`age_mult ∈ {<5: 1.0, 5–10: 0.85, ≥10 luxury: 0.50, ≥10 std: 0.0}`. With **no size bump to modulate**
(no extra floors declared), age/luxury do nothing — exactly the disentangle result. And the "Qatar
10-Year Rule" is implemented as `age_mult = 0.0` — i.e. it **zeroes a size uplift**, it does **NOT** pull
an old villa's value to land. The intent (old non-luxury → ≈ land value) is **un-implemented on the
comparison path**.

`condition` never reaches this lever at all — it maps via `CONDITION_TO_RENOVATION` (`evaluate_unified.py:~620`)
to a renovation flag whose headline effect measured **zero** across `new`/`renovated`/`maintenance`.

> **The comparable MEDIAN is condition-blind at source and unchanged by `/details`:** land ppm² stayed
> **3778 (V002)** / **3768 (V001)** with and without attrs; method stayed bracket/widened. So `/details`
> only stacks a capped, size-only, upward-only bump **on top of** a blind median (R7 root — §20.10.2,
> a17/a19, `PHASE0_SprintB_condition_axis`). Even a perfect size input cannot fix a blind median.

> **Null honesty (Rule #36):** `valuation.age_regime` read `None` across every probe — a **wrong-field-path
> artifact**: the regime is at `valuation.building_substantiality.age_regime` (`:3998`). Not load-bearing
> (the value movements are decisive). `valuation.value_floor.land` also read `None` via this session's
> extractor — the a21 floor surfaces under `valuation.value_decomposition.land.estimated_qar` instead
> (1,700,100 for V002; 2,456,736 for V001 — present, reliable), per `PHASE0_SprintB_condition_axis` F2.

---

## 4. Per-property interpretation (the brief's decision rule, applied)

| subject | does /details close it? | diagnosis |
|---|---|---|
| **V002 / V003** (new premium, under-anchor) | **NO** (~⅓ of gap, wrong axis) | **CALIBRATION + MISSING MECHANISM.** Only the size lever fires (+16–21%, and *only* if the user declares the extra floor); the market premium is +60% and lives in **finish/new-ness**, which the engine doesn't price. Needs a *new-build / finish premium tied to comparable ppm²*, not a +25%-capped size bump. |
| **V001** (old premium, over-anchor) | **NO** (~immovable) | **MISSING MECHANISM.** The over-anchor is in the condition-blind *widened median*; the only age lever (`age_mult=0`) merely suppresses a size uplift the median doesn't carry. Needs a **down-re-anchor toward land** for old non-luxury stock — the 10-Year-Rule *intent*, currently absent on the comparison path. |

**Mix verdict:** a *trace* of UX-prominence is real — the size lever exists but is buried in the optional
"إضافة تفاصيل العقار" accordion, so the default flow never fires it. But that trace is **a small minority
of the gap and the wrong axis**. Surfacing/guiding elicitation (the assumed Stage-2 UX move) would, on
these three cases, move **nothing** for condition/finish/age, and at most re-expose the size lever (which
still leaves V002/V003 −27.5% under and V001 unchanged). **UX-prominence is a necessary companion to B-2,
not its substance.**

---

## 5. "KEEP from Brief ②" — items carried + answered

- **DEFAULT-flow residual (E22 — measure on the default flow):** measured — V002 **−37.5%**, V003
  **−40.0%**, V001 **+31%** (over). These are the default-flow residuals; the `/details` flow barely
  changes them (§1). E22 sharpened: the age axis isn't just "inert because not auto-detected" — it is
  inert **even when supplied**, because the mechanism is modulate-a-size-uplift, not price-the-age.
- **Three-axis disentangle (age / finish / physical):** done (§2) — **only physical/size is wired to the
  value**; age + finish/condition are mechanically inert on the headline.
- **n < 20 → motivates, NOT calibrates:** n = **2 GT-2 + 1 GT-3** (VALIDATION_LOG). **No coefficient, no
  weight, no rule** is derived here. These three **motivate + scope** B-2; calibration waits for n≥20 GT-2
  (the Anas/broker-fed Confirmed-Sales revival, 2.16.16).
- **MoJ = truth / listings = weak:** V002/V003 = **GT-2 confirmed sales** (strong, two independent
  confirmations @ 4.0M); V001 = **GT-3 asking** (weak/directional, upper bound). Built on a25 comparable
  pools: V002/V003 bracket land n=33; V001 widened land n=20.
- **Document nulls:** done (§3 null-honesty block — `age_regime`, `value_floor.land` field-path
  artifacts; `condition` → zero headline movement).

---

## 6. What B-2 actually needs (scope signal — report, do not build)

Three findings become candidate B-2 brief lines (flag-and-HOLD, #38; **all Gate-2 methodology** — Anas
signs):

1. **B2-F1 — the comparable median is condition/built-type-blind (the R7 root).** No subject input
   re-selects or re-weights comps; `/details` stacks on top of a blind median. The durable fix has to act
   on the **median/anchor**, not only a post-hoc bump. (Pairs with the a11/a12 built-type pool work and
   §20.10.2's bidirectional R7.)
2. **B2-F2 — replace the size-only, +25%-capped, upward-only lever with a calibrated condition/finish/
   new-build premium tied to ppm²** (the +60% new-premium reality), gated on the elicited inputs. Today
   `condition`/`is_luxury` contribute **0**; that is the core mis-calibration.
3. **B2-F3 — add the missing DOWN-re-anchor for old non-luxury stock** (10-Year-Rule *intent*): old +
   non-luxury should converge toward the **land floor** (already surfaced via `value_decomposition.land` /
   the a21 `value_floor`), not sit at the condition-blind comparison median. Currently `age_mult=0` only
   suppresses an uplift — it never pulls down.

**Calibration discipline:** every coefficient above is **BLOCKED on n≥20 GT-2** per E-rules. B-2 may build
the *mechanism + the input UX*, but the *numbers* stay provisional / broker-experience-grounded until the
Confirmed-Sales corpus reaches n≥20 (2.16.16 revival). The three subjects here **motivate**; they do not
**calibrate**.

---

## 7. Forward-risk + decisions this feeds

- 🔮 **If B-2 is scoped as "make elicitation prominent + recalibrate the gaps," it will under-deliver** —
  this recon shows the gaps are *mechanism-shaped*, not coefficient-shaped (no finish premium, no
  down-anchor). **Guard:** the B-2 brief DoD must name a *down-anchored* old-stock case (V001-class) **and**
  a *finish-premium* new-stock case (V002/V003-class), and require movement on **finish/age inputs alone**,
  not just declared floors.
- 🔮 **Calibration-without-data risk:** with n<20 the temptation is to fit coefficients to V002/V003's −37%.
  **Guard:** mechanism now, coefficients provisional, locked to the 2.16.16 corpus. (This is exactly why
  Confirmed-Sales revival is the binding constraint — VALIDATION_LOG §"project benefit".)
- **Decision for Anas (B-2 direction):** confirm B-2 = *built-type/condition mechanism + Stage-2 elicitation
  UX*, with the median-level R7 root (B2-F1) as the spine — **not** a prominence-only UX pass. Then the
  signed B-2 brief (Gate 2) + §5 audit.

## 8. Out of scope (held)
Any calibrated coefficient (n<20 — motivates only). Age auto-detection. Land-path changes (villa-only).
The Stage-1 input-honesty sprint (premise falsified — closed; optional docs fix to `DESIGN_2p23 §2b`'s
stale "inert engine" claim is a separate trivial docs edit, Anas's call). `stock_strata` a18-alignment
(R15-family, separate). Confirmed-sales sourcing (→ 2.16.16, the binding calibration constraint).

---

*Phase-0 recon, READ-ONLY. Production byte-identical (a25 / v164). The Stage-1 sprint that opened the
session was halted (premise falsified by measurement); this B-2 recon is the re-pointed deliverable. Hands
back to Anas: the central question is answered — **R7 is calibration + missing-mechanism, not
UX-prominence** — feeding the B-2 direction decision (Gate 2) before any build.*
