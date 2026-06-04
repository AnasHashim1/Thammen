# BRIEF — Sprint B-1: land-floor / HBU decomposition + condition surfacing (Gate-2)

> **Status:** Gate-2 methodology brief — **SIGNED by Anas** (this brief = the sign-off). Class:
> presentation/disclosure — **VALUE-INVARIANT (D4)**. Phase-0 §5 recon DONE
> (`docs/PHASE0_SprintB_condition_axis.md`). Multi-AI #54 DONE — GPT-5 + Gemini **CONVERGENT** (copy
> LOCKED). Pre-build live tip: a20 / Heroku v159 / master == origin.
> **Note (CC, 2026-06-04):** the separate `docs/MULTI_AI_VALIDATION_BATCH_SprintB1.md` (the GPT-5/Gemini
> transcript) was NOT delivered with this brief — pending Anas's paste; the LOCKED outcomes are recorded
> in §2 D3 below. **Shipped as Sprint 2.22.0a.21 / Heroku — see CHANGELOG_v73 + Session_Log §20.21.**

## 1. WHY
56/647/6 (V001): engine returns 3.8M (comparison_widened) = a ~5yr market-rejected ask; real clearing
signal is land (~2.46M, a18-aware) + a modest premium. Condition/age/built-type blind on every comparison
path (R7). Phase-0 F1: the engine ALREADY computes a land floor but SUPPRESSES it (Patch-C) exactly in the
land-priced/old-stock cohort (~10% of valued villa cells, 0% of reliable, all large-plot old-stock) — the
case that needs it most. B-1 surfaces the land floor (grounded in Highest-and-Best-Use, VPS 2/IVS 102 — a
MANDATORY consideration, not an ad-hoc add) + the implied-building decomposition + the land-anchored
disclosure. Presentation-only.

## 2. SIGNED DECISIONS
- **D4 value-invariance:** headline value byte-identical. Presentation-only. CONFIRMED.
- **D2 gate (a):** ride the existing `_condition_note_applies` scope (villa/house + the 5 value-bearing
  comparison methods + amount) ≈ ~100% villa lookups, age-input-free (E22-safe). The decomposition block +
  the live condition_note = ONE coherent surface.
- **D1 hybrid decomposition:** KEEP the existing headline (point + current range). ADD a block: land floor
  [X] + implied building value [Y = headline − floor]. Floor sits below the comp band in some cases (V001)
  and above it in others (land-priced) — the decomposition absorbs both. REJECTED: a land→median RANGE
  headline (bidirectional trap).
- **F1 (Patch-C carve-out) — LOAD-BEARING:** compute the land-floor number INDEPENDENTLY (villa-scoped) so
  it surfaces even when `_decompose_value` returns None (land ≥ value). Do NOT touch Patch-C's
  anti-negative-building guard; do NOT change any amount. When floor ≥ value → implied building ≈ 0
  (land_anchored), NEVER a negative number.
- **F2 field path:** read `valuation.value_decomposition.land.{estimated_qar, per_m2_qar, n_transactions,
  reliable}` when present; for the F1 case recompute `land_ppm² × plot` from the SAME `moj_reference` land
  category. NOT any `land_value`/`cost` key (Cost-approach crosscheck, legitimately None for villas).
- **F5 land number:** use the a18-aware `moj_reference` figure (V001 = 3,768 × 652 = 2,456,736). The
  `stock_strata` 4,032 twin is pre-a18 → R15 (separate cleanup, out of scope).
- **D3 (RICS framing + copy) — MULTI-AI LOCKED:**
  - Citations (validated by GPT-5 + Gemini vs the in-force 2025 edition): decomposition → VPS 3/IVS 103 ·
    single-basis discipline → VPS 2/IVS 102 · HBU land floor → VPS 2/IVS 102 · not-inspected
    assumption-limitation → VPS 2 + VPS 4 (+ scope VPS 1/IVS 101) · uncertainty → VPGA 10 + VPS 6/IVS 106 ·
    model-derived/not-a-written-valuation → VPS 5/IVS 105 · comparable-data quality → IVS 104.
  - Discipline (both AIs): land floor = ANALYTICAL DECOMPOSITION, never a standalone "land market value"/
    second basis. Condition = material uncertainty + assumption-limitation, NOT a special assumption, NOT
    "assumed standard condition." Land-anchored = a MODEL inference, never "the market prices it as land."
  - NEW Arabic strings (synthesized from both AIs):
    - `[land_floor]`    «تفكيك تحليلي ضمن نموذج المقارنة — قيمة الأرض: ~X ر.ق (وفق صفقات أراضٍ مماثلة؛ يعكس الاستخدام الأمثل للأرض، وليس قيمة سوقية مستقلة).»
    - `[implied_bldg]`  «القيمة الضمنية للمبنى (ناتج حسابي: التقدير ناقص الأرض): ~Y ر.ق — غير مُتحقَّقة ميدانياً (نوع البناء والعمر والحالة غير معروفة).»
    - `[land_anchored]` «يشير النموذج إلى أن القيمة المقارنة لا تتجاوز قيمة الأرض المجردة؛ القيمة الضمنية للمبنى ≈ صفر (قد يُعتبر عقاراً للتطوير).»
  - Bidirectional condition disclosure = the LIVE `condition_note_ar` (a17/a19), REUSED — NOT re-added.
    Age + built-type are added in `[implied_bldg]`. No change to live copy.
  - EN brief surface (output_briefs): mirror the AR (analytical land baseline / implied building value
    (computational, not field-verified) / model land-anchored inference).

## 3. B-0 — DROPPED
Phase-0 Q3: condition is disclosed on every villa surface (condition_note ⊕ range_disclosure). No gap.

## 4. BUILD (CC)
**Backend (`evaluate_unified.py`):** a villa-scoped `land_floor` helper returning `{land_floor,
floor_ge_value}` from `value_decomposition.land` when present, else recomputing `land_ppm² × plot` from the
`moj_reference` land category — INDEPENDENT of `_decompose_value`'s Patch-C suppression. Never alters the
amount; never touches the Patch-C guard. Attach a `value_floor` block `{land_floor, implied_building_value
= max(amount − land_floor, 0), land_anchored, the 3 new AR strings + EN, citation tag}` under the gate (a)
predicate; error-swallowed; fail-safe to disclosure. Surface on root + brief MU/decomposition section
(output_briefs buyer+valuer), per the a20 pattern.
**Frontend (`index.html`):** render the block under the headline (muted, reuse a proven class). index.html
IS TOUCHED → node --check + mobile 390×844 EXECUTED (R14: verified = executed, not reasoned). ENGINE_VERSION
+ SPRINT_TAG bump. CHANGELOG_v{N}.

## 5. VERIFICATION / DoD
py_compile; node --check (extracted JS); mobile 390×844 EXECUTED. Isolated test (production path, E14): ≥5
cases — bracket/widened/thin floor present; F1 land-priced (55/296/13-class) → floor present + implied
building ≈ 0 + land_anchored=true [LOAD-BEARING GUARD]; modern villa → positive implied building;
apt/refusal → no block; VALUE-INVARIANCE: headline byte-identical; verbatim AR string guards; no-Latin/bidi
check. DoD matrix 392/15/45/N. Live two-lane smoke (browser-UA, #61), ZERO value drift. /api/health = new
engine, qars healthy, anchors byte-identical.

## 6. GATES & DEPLOY
Gate 2 = THIS brief (Anas signature). Gate 1 = deploy: report branch + tests + ENGINE_VERSION + CHANGELOG
before `git subtree push --prefix "deploy v2" heroku master` (+ `git push origin master`); deploy on
consent / standing deploy-on-green. Commit the multi-AI batch as `docs/MULTI_AI_VALIDATION_BATCH_SprintB1.md`
and this brief as `docs/`.

## 7. FLAGS (parallel, NOT blocking)
PDF-verification (parallel citation discipline, per a4): confirm in the Red Book / IVS PDF the precise
clause + required PROMINENCE of uncertainty/variance disclosures in an AVM/automated interface (Gemini flag:
IVS 105 / IVS 106). Does NOT block ship; if the PDF demands greater prominence → fast-follow. R15
(stock_strata not a18-aware, ~7% land-median divergence) — separate cleanup, out of scope.

## 8. OUT OF SCOPE
Any calibrated condition/age ADJUSTMENT (→ B-2 / 2.22.0b, user input). Age auto-detection. Land-path changes
(villa-only). stock_strata a18-alignment (R15). Confirmed-sales sourcing (2.16.16). Changing the headline.
