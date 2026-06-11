# BRIEF — Evidence-Conditional Leadership + three-value stack (🔴 Gate-2 VALUE-AFFECTING)

> **STATUS: DRAFT — UNSIGNED.** Build is HELD until Anas signs Gate-2 over the Phase-0 flip-rate numbers
> (`PHASE0_conditional_leadership.md` §2: **69% cost-led variant A / 85% variant B / 8-9 of 13 live villa
> headlines move**). Encodes the PO directive of 2026-06-11. Companion Phase-0 = the measured basis; every
> open fork is in §11 with its measured Δ.

## §1 Premise (signed direction, this brief = the encoding)

The engine's headline today is market-led by default; cost (DRC) leads/floors only on narrow gated slices
(b11/b13/b16). The PO direction: **the three-value stack renders everywhere; leadership is decided by
EVIDENCE QUALITY, not by path history**. A market median earns the headline only when its pool is deep,
tight, and stratum-matched; otherwise the disclosed-indicative DRC leads. The legacy anchors' recorded
expectations are retired as methodology truth (re-baseline post-ship); **V001/TD-93317 is the sole
calibration anchor** (±1% standing test).

## §2 Three-value stack (display contract — every valued villa/house response)

1. **Market Comparison** — pool median + n + window + the numeric dispersion (newly EMITTED — Phase-0 G2)
   + dominant stratum + share.
2. **Cost (DRC)** — land floor + depreciated building (defaults §6) + the full component breakdown
   (already returned by `_cost_approach_value`; today discarded on most paths — Phase-0 G1). Label verbatim:
   «منهج التكلفة (إحلال مُهلَك) — استرشاديّ، مُعايَر على تقييم معتمد واحد (V001)».
3. **Income** — unchanged (renders when it computes; leads when it fires — §3).

Paths: villa/house = full stack · **raw_land = market + (DRC ≡ قيمة الأرض — مذكورة كسطر واحد، لا حساب
منفصل)** · apartments/towers/compounds = unchanged DCF/hybrid surfaces (no RCN basis — Phase-0 G3) ·
refusals stay refusals (no stack — G4).

## §3 Leadership gates (the core change)

Precedence: **income_led (unchanged, §20.40 circularity guard intact) → evidence-conditional market/cost →
refusal**. Within the market/cost decision, for villa/house with a computed market value:

```
market LEADS  iff  [matched-stratum effective n >= 10]
              AND  [pool ppm² dispersion (36mo) < 0.30]
              AND  [stratum match: dominant pool stratum ∈ the subject's E26 system-age band]
else COST LEADS — disclosed-indicative:
              range = [land_floor … cost]   (fork §11-F3)
              MUC = high · label «قيادة كلفة استرشادية — السوق المطابق غير كافٍ (n={n}, تشتت={d})»
              market median still DISPLAYED in the stack (never hidden) + cite-n
```

**Hard rails (non-negotiable, from the Phase-0 findings):**
- **E25 rail — cost never leads UPWARD:** if `cost >= market median` (the المعراض inversion, Phase-0 §2.5-2)
  → market keeps the lead + the land-anchored disclosure (today's treatment). Cost is a floor, never a proxy.
- **E26 rail:** every LEADING retention uses the SYSTEM age; user age stays a sensitivity line (b18 §A1 intact).
- **E24 rail:** vintage-capped ages are floors; the cliff-flag disclosure stays mandatory.
- **No invented central** (brief §7#2 lineage): the cost-led figure is the computed DRC, never a blend point.
- Fail-safes: strata absent / dispersion incomputable / band unknown → **cost leads** (fail-safe-to-
  disclosure direction) — forks §11-F2/F5 can soften this with a signature.

**Subsumption:** b6 widen_down, b11 cost_reanchor_down, b13 trim(-sensitivity), and b16 OSR become special
cases of (or are replaced by) the single evidence-conditional rule — exact mapping per branch is build-scope;
the مريخ Δ (OSR 3.4M vs strict-gate cost 2.38M) is fork §11-F1.

## §4 Reconcile, not blend

The three values are never averaged. One leads (per §3), the others render as disclosed cross-checks with
their own n/confidence. Divergence > 30% between displayed values ⇒ MUC ≥ high + an explicit divergence
line (the RICS reconciliation duty — VPS 3/IVS 103). `reconciliation` stays a status reporter.

## §5 Depreciation set (LOCKED — the calibrated numbers, no re-tuning in this brief)

| element | value | basis |
|---|---|---|
| age basis | **SYSTEM (CGIS) lead — E26**; user age = sensitivity only | b18 §A1, TD-93317 |
| curve | **50-year straight line**, retention = clamp(1 − age/50, floor, 0.98) | METHODOLOGY_DRC §5 |
| condition ladder | excellent **−2** · renovated **−3** · new 0 · good +5 · **default avg +8** · fair +15 · poor/teardown +25 | b13 §4.2 |
| residual floors | **0.27** ordinary · **0.31** high/luxury (D-1) | b13 |
| RCN ladder (QAR/m² BUA) | shell **1200** · ordinary **2200** · good **2500** · high **3000** · luxury **3500** | PO web-validated §3 |
| BUA | confirmed footprint × floors, else max-buildable × **0.77** × floors (default floors 2) | b11/b10 |
| soil/geotech | **1.0 default**; sabkha/karst +5–15% = **v2 (GIS layer)** — NOT in this build | directive |

## §6 Universal DRC computation + defaults

Compute the DRC on **every valued villa/house** (it already computes — emission is the change, Phase-0 G1)
with the §5 defaults (ordinary + average + system age) when inputs are absent, and EMIT it in the stack with
its assumptions disclosed («افتراضات: تشطيب عادي · حالة متوسطة · عمر النظام {N}») + the refine CTA. When the
DRC is input-starved (no land floor / no system age / no footprint — Phase-0 §1.3) the stack shows
«منهج التكلفة غير متاح — {السبب}» rather than silence.

## §7 Calibration — V001 sole anchor (±1% standing test)

The TD-93317 reproduction stays the ONLY value-anchored test: land 2,456,345 (350/ft²) ≈ engine MoJ floor
2,456,736 (+0.016%) · building 602×1,900 ≡ RCN_high 3,000 × retention(18,'high')=0.64 · MV 3,600,145 ±1%
(measured this pass: **+0.35% / +0.34% PASS**). ⚠ Basis = **RAW system age + finish=high + penalty 0**
(E26/b18) — NOT the §6 display defaults; the test pins the basis explicitly (`test_sprint_2_22_0b18.py`
§B carried verbatim). n=1 calibration disclosed on every cost-led surface; the GT kit (D-3) is the
tightening channel.

## §8 Honesty rails

cite-n everywhere · cost-led = «استرشادي» + MUC high, never «معتمد» · E1/E3 intact (no listing uplift; cost
never chases ASK — E25 as rewritten 2026-06-10) · «📌 تقدير سوقيّ آليّ — ليس تقييماً معتمداً» unchanged ·
a17/a19 condition caveat + b12 HBU + B-1 floor surfaces preserved · the dispersion numeric + gate verdict
EMITTED (auditability) · refusal honesty unchanged.

## §9 Legacy-anchor retirement + re-baseline

Per Phase-0 §4: scratch live-expectation files RETIRED; offline input-fixtures survive; the precedence-chain
isolated tests (b6/b7/b8/b11/b13/b16/b18) re-pointed at build time; post-ship the SAME 22-case cohort is
re-captured and fresh byte-identical guards are written, labeled **engineering fixtures only**. V001 ±1% =
the only surviving value anchor.

## §10 Out of scope

apartments/towers/compounds RCN basis (G3) · soil v2 GIS layer · the GT-collection track itself (D-3,
parallel) · b19 (separately signed; executes regardless) · any threshold re-tuning (the numbers in §3/§5
ship as-is; revisions = a future signed pass) · frontend redesign beyond the stack rendering (screens 4/5
absorb the stack — copy-level edits only).

## §11 Open forks — REQUIRE the Gate-2 signature (each with its measured Δ)

| # | fork | options | measured Δ (Phase-0) |
|---|---|---|---|
| **F1** | مريخ/OSR subsumption: does the b16 geo-full pool (n=51, unstratified) count as «matched»? | (a) strict matched-stratum only → cost leads · (b) geo-full counts → OSR-style central survives | (a) 2,378,094 vs (b) ~3,400,000 — **Δ≈1.0M على الحالة الرائدة** |
| **F2** | subject-band for re-surveyed (sys-age<2) stock | (A) band from raw age → market (تظل V002/V003 سوقية) · (B) unknown → fail-safe cost | **A: 69% / B: 85% cost-led** |
| **F3** | cost-led range shape | (a) `[land_floor … cost]` (الموجَّه) · (b) b11-style `[cost … market-muted]` | على 54/788/10: (a) [0.96M…1.10M] vs (b) [1.10M…3.0M] |
| **F4** | a14 dispersed-bracket cohort: flip to cost-led or keep the honest-range treatment? | flip / keep | 3/13 حالات — keep يخفض المعدل 69%→46% مع F5 |
| **F5** | strata-absent fail-safe | cost-led (الافتراضي الموجَّه) / keep today's treatment | 3/13 حالات |
| **F6** | acceptance of the headline flip-rate itself | sign / re-scope | **8-9 من 13 فيلا حيّة تتحرك؛ المنقلبات تنخفض 0.3–1.9M لكل حالة** |

## §12 Build-sprint DoD (when signed)

Isolated tests for the gate fn (matrix: each gate × fail-safe × rails, incl. the E25 inversion case from
المعراض) · siblings re-pointed (§9) · the V001 ±1% test green · DoD aggregator/security/surface/broad walk ·
local E2E on the 22-case cohort (expected-moves table authored from THIS Phase-0) · R14 Chromium 390×844
(the stack renders, no overflow) · two-lane live smoke · post-ship re-snapshot per Phase-0 §4.2 · docs-close.

> **القرار المطلوب:** توقيع Gate-2 على أرقام الانقلاب (§11-F6) + حسم F1–F5. بدون التوقيع لا يُبنى شيء.
