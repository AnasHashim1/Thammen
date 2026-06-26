# BRIEF — Sprint B-2: محور الحالة كبنية قابلة للتكيّف (condition axis, data-adaptable)

> **Status:** 🔴 **Gate-2 — PENDING Anas signature** (value-affecting on the opt-in path; the infra slice is value-invariant). Read-only design — NO code, NO deploy until signed.
> **Date:** 2026-06-26 · **Author:** Claude Code (research + design) · **Live state at authoring:** engine `thammen-sprint2p22p0b70-modal-a11y` / Heroku v242 / qars healthy / MoJ 177d.
> **Origin:** the PO directive — «نعمل على ما لدينا من بيانات بأقصى سرعة وقوة وجودة؛ وحين تأتي البيانات الموثَّقة، الهيكل لا يتغيّر وإنّما الرقم وحده يتغيّر — البنية يجب أن تكون جاهزة وقابلة للتكيّف، لا أن يُبنى كلّ شيء من الصفر فور وصول البيانات.»
> **Method:** a read-only research+design workflow (`wf_36d291d8-0cb`): codebase-inventory + value-impact agents succeeded; the RICS + global-AVM web tracks were rate-limited twice and **completed by direct web research** (this brief, §7).

---

## 0. The PO directive, made into an architecture principle

**MECHANISM ≠ CALIBRATION — two layers on two clocks.**

| Layer | What it is | Changes when data arrives? |
|---|---|---|
| **Stable mechanism** | CODE: condition grade → shifts effective-age → the V001-calibrated DRC curve prices it → disclosed (RICS assumption + MUC) → emitted (`value_stack.cost`). | **NEVER** |
| **Data-driven calibration** | A swappable read-only source (`condition_adjustments.sqlite`) holding the per-grade NUMBERS the mechanism reads — seeded from V001 (n=1) now, rebuilt from the GT corpus (n≥20) later. | **Only the numbers** |

This is **byte-for-byte the existing `cap_rates.sqlite` precedent**: `_lookup_calibrated_cap_rate` reads a read-only SQLite snapshot, safe-fails `(None,None)` → a hardcoded fallback; `cap_rate_calibrator.py` rebuilds it offline; the engine code never changes (Operational #43, §20.39/b5). **Condition is the income approach's twin:** a calibrated coefficient with a hardcoded fallback, gated on `n`.

> When confirmed sales arrive, we run `condition_calibrator.py` → it DROP+recreates `condition_adjustments.sqlite` with the new numbers. **The engine code, the site, the reports — all unchanged.** Exactly the directive.

---

## 1. The stable mechanism (code — byte-identical across data updates)

**(A) Pricing flow (reuses the existing DRC — no new layer):**
`grade → penalty_years → eff_age = age_years + penalty → _cost_retention(eff_age, finish) → building = bua × rcn × retention`.
Condition **only shifts the effective age**; it never touches the retention curve, the RCN ladder, the built-ratio, economic life, or the residual floors → **preserves the V001/TD-93317-validated curve** (E26, reproduced to +0.35%). *(This is the "reuse the depreciation formula" option — no parallel condition model.)*

**(B) Grade→penalty indirection — the ONE seam:** the penalty is read at a single site. Permanent call shape:
```
penalty = _lookup_condition_penalty(grade, area, stratum)   # calibrated, or None
          or COST_CONDITION_PENALTY.get(grade, COST_DEFAULT_PENALTY)   # hardcoded fallback
```
The lookup TARGET swaps numbers; **the call shape never changes.**

**(C) Disclosure:** every condition-affected output carries the RICS triad (§6) via the existing `_condition_note` machinery — reworded from "condition NOT assessed" (caveat) to "condition STATED by user, treated as an Assumption (not inspected)" + MUC.

**(D) Emission:** condition rides `value_stack.cost.{condition_penalty, effective_age, condition_source, condition_confidence}` + the b23 scenarios. **`leadership` is UNCHANGED** — condition is transparent inside the cost decomposition, not a leadership signal.

---

## 2. The data-driven calibration (the swappable source)

**`condition_adjustments.sqlite`** — a new read-only DB, sibling of `cap_rates.sqlite`. Columns mirror it:

| col | meaning |
|---|---|
| `area_match_key` | a18-pooled area key (NULL = any) |
| `built_type_stratum` | E4: luxury_new / modern_stock / aging_stock / land_priced (NULL = any) |
| `condition` | the taxonomy key (§5) |
| `penalty_years` | the years-delta added to age (option-c unit, so the V001 curve is reused unchanged) |
| `sample_size` · `confidence` | `reliable` n≥20 / `indicative` n≥10 / `fallback` n<10 (not returned) |
| `source` · `last_updated` · `notes` | provenance |

- **Engine read:** `_lookup_condition_penalty(grade, area, stratum)` mirrors `_lookup_calibrated_cap_rate` exactly (mode=ro, confidence-gated, area-key pooled, stratum-prefer-then-any, highest-n wins, safe-fail `(None,None)`).
- **Seed NOW (n=1, V001):** one row per grade with the CURRENT `COST_CONDITION_PENALTY` numbers, `source='v001_seed'`, `confidence='indicative'` (NOT reliable — n=1 is disclosed-indicative). **Seed == hardcoded → live byte-identical, but now sourced + disclosed.**
- **GT pipeline (already exists):** `validate_gt_sheet.py` ingests documented sheets (`--condition`; intake rule: no row without a document) → `calibration/gt_corpus.local.json` (`corpus_schema.py` CONDITIONS already 1:1 with the API). A NEW offline `condition_calibrator.py` (analogue of `cap_rate_calibrator.py`) bins by `(area_key, stratum, condition)`, fits `penalty_years` from matched GT-2 residuals, gates confidence on `n`, DROP+recreates the DB. `residual_harness.py` already measures per-stratum residuals → the calibrator's validation loop.

---

## 3. The exact seam (build on the existing, do not rebuild)

| Component | Design | File |
|---|---|---|
| `condition_adjustments.sqlite` | NEW read-only DB (sibling of cap_rates); rebuilt offline, never written in-engine (E1); seeded n=1 from V001 | NEW `deploy v2/condition_adjustments.sqlite` (committed read-only; ephemeral-FS precedent #43) |
| `_lookup_condition_penalty()` | NEW pure fn mirroring `_lookup_calibrated_cap_rate`; safe-fail `(None,None)` | `evaluate_unified.py` (next to the cap-rate lookup) + a module const next to `_CAP_RATES_DB` |
| **the ONE-LINE call-site** | `penalty = lookup(...) if _COND_OK else None; penalty = penalty if penalty is not None else COST_CONDITION_PENALTY.get(grade, COST_DEFAULT_PENALTY)`. The hardcoded dict stays as the guaranteed fallback. **NOTHING else in `_cost_approach_value` changes.** | `evaluate_unified.py` (the single penalty read) + thread `area`/`stratum` into the call |
| `condition_calibrator.py` | NEW offline tool (analogue of `cap_rate_calibrator.py`): reads the corpus, bins, fits `penalty_years`, gates `n`, DROP+recreate | NEW `deploy v2/condition_calibrator.py` |
| `_condition_note` / RICS disclosure | EXTEND the existing note machinery: user-supplied condition → the §6 Assumption + limitation + MUC triad; no-input keeps the "not assessed" caveat | `evaluate_unified.py` (the existing note fn) |
| provenance in `value_stack`/brief | EXTEND `value_stack.cost` with `condition_source` + `condition_confidence` + `sample_size` (mirrors `cap_rate_provenance`) so the report discloses "indicative, n=1" | `evaluate_unified.py` + `output_briefs.py` |

> **Line numbers from the codebase recon are anchors — re-confirm exact lines at build time (they drift).**

---

## 4. The condition taxonomy (RICS / Fannie-Mae-UAD aligned — §7 research)

8 grades, 1:1 with the global UAD C1–C6 standard + our existing engine keys (so live stays byte-identical):

| Grade (AR / EN) | UAD | penalty_years (V001 seed) |
|---|---|---|
| ممتاز / excellent (no wear, near-new) | C1 | −2 |
| مُجدَّد / renovated (recent refurbishment) | C2 | −3 |
| جديد / new (newly built / unoccupied) | C1–C2 | 0 |
| جيّد / good (well-maintained, normal wear) | C3 | +5 |
| **وسطيّ / average = THE BASELINE** (no-input default) | C4 | **+8** (`COST_DEFAULT_PENALTY`) |
| مقبول / fair (visible wear, deferred maintenance) | C5 | +15 |
| رديء / poor (significant deterioration) | C6 | +25 |
| للهدم / teardown (no economic building value) | — | the b4 demolition valve (land − demolition) — a separate path |

> The taxonomy SHAPE is now standards-anchored (UAD C1–C6, §7). The penalty NUMBERS are the **existing hardcoded ladder re-sourced from V001 (n=1), disclosed-indicative** — they recalibrate from the corpus at n≥20 with **zero code change**.

---

## 5. RICS compliance — the mandatory disclosure (verified, §7)

- Condition stated-but-not-inspected = an **ordinary ASSUMPTION** (VPS 2 / IVS 104) — *verified*: the RICS textbook example of an assumption is literally "an assumption about tenure, **property condition** or services." It is **NOT** a Special Assumption (that requires a state that does NOT apply at the valuation date). → matches our a8/a17/a20 production framing.
- Every condition-affected output MUST state the **triad**: (1) the **Assumption** («الحالة مُصرَّح بها من المالك، غير مُتحقَّق منها بالفحص»); (2) the **limitation-on-inspection** («لم يُجرَ فحص فيزيائيّ/داخليّ»); (3) the **Material Uncertainty** (VPGA 10 — `rics_compliant` stays `false`, «بانتظار مراجعة مُقيِّم مُرخّص»).
- At **n=1** the calibration is disclosed as **INDICATIVE** (`confidence='indicative'`, the V001-only basis named) — the b16 honest-residual precedent.
- The no-input default keeps the existing bidirectional "condition NOT assessed" caveat (R7) unchanged.
- **Personas (PO standing directive):** the disclosure reword goes to the lawyer + linguist personas before ship.

---

## 6. Buildable NOW vs data-gated LATER

**NOW (with V001 n=1 + the user's condition input):**

| Slice | What | Value impact | Gate |
|---|---|---|---|
| **B2-1 — calibration infra** | the DB + `_lookup_condition_penalty` + the guarded one-line seam + `_COND_OK` guard, seeded n=1 from V001 with the CURRENT numbers | **ZERO** (seed == hardcoded → 5-fixture byte-gate identical by construction) | Gate-2 (touches the value path though value-invariant) + deploy-on-green |
| **B2-3 — RICS disclosure reword** | `_condition_note` → the Assumption + limitation + MUC triad for user-supplied condition | **ZERO** (copy only) | Gate-2 + lawyer/linguist personas |
| **B2-2 — user-condition pricing** | switch on the eff-age pricing for supplied conditions → the cost-led headline MOVES (opt-in `/details` only), disclosed-indicative | moves cost-led ONLY when condition supplied; **MEASURE the exact live %-spread (poor vs excellent) before sign-off** | Gate-2 (value-affecting, opt-in) + the disclosure mandatory |

**LATER (data-gated — SAME code, only the DB swaps):**
- B2-2 numbers recalibrate per `(area, stratum, condition)` cell when GT-2 reaches **n≥20** → `confidence='reliable'`, MUC may relax.
- Per-stratum condition elasticity (luxury_new vs aging_stock) at n≥20 per stratum.
- Demolition-cost calibration for teardown (replaces the hardcoded `DEMO_QAR_PER_M2`).

---

## 7. Research basis (Rule #54 — confidence-flagged)

- **VERIFIED — UAD condition taxonomy (C1–C6):** C1 excellent/near-new · C2 like-new/renovated · C3 well-maintained (normal wear) · C4 adequately maintained (modest wear, functional) · C5 deferred maintenance (significant repairs, still livable) · C6 poor (safety/soundness deficiencies). Sources: [Fannie Mae Selling Guide B4-1.3-06](https://selling-guide.fanniemae.com/sel/b4-1.3-06/property-condition-and-quality-construction-improvements) · [Fannie Mae condition/quality definitions PDF](https://singlefamily.fanniemae.com/media/document/pdf/condition-and-quality-rating-definitions-pdf) · [McKissock — UAD 3.6 C1–C6](https://www.mckissock.com/blog/appraisal/understanding-appraisal-condition-ratings-c1-to-c6/).
- **VERIFIED — RICS: condition = ordinary assumption + MUC:** "an assumption is something reasonable for the valuer to accept without specific investigation — for example, an assumption about tenure, **property condition** or services"; a special assumption requires a state that does not apply at the valuation date. Source: [isurv — VPS 2 bases, assumptions & special assumptions](https://www.isurv.com/info/1605/red_book_guide/12539/valuation_bases_assumptions_and_special_assumptions_%E2%80%93_vps_2) + the [RICS Red Book Global 2024/25 PDF](https://www.rics.org/content/dam/ricsglobal/documents/standards/Red-Book-Global-Standards-incorporating-IVS.pdf). *(The exact VPS number for "bases/assumptions" in the 2025 edition = VPS 2 per our a8 primary-source verification; the substance — condition is an ordinary assumption — is unambiguous.)*
- **VERIFIED — calibration needs a corpus, a benchmark calibrates the curve:** hedonic models assign a per-characteristic coefficient summed across a property; AVM calibration is validated on a **holdout/cross-validation** sample; accuracy target 3–5% of sale price. Per-condition coefficients therefore require a **population** of sales; a single benchmark calibrates the depreciation **curve**, not per-grade coefficients. → **validates our n=1→curve / n≥20→coefficients split.** Sources: [IAAO Standard on AVMs](https://www.iaao.org/wp-content/uploads/Standard_on_Automated_Valuation_Models.pdf) · [Lushbinary — Build an AVM (2026)](https://lushbinary.com/blog/build-ai-property-valuation-avm-automated-cma-guide/).
- **OUR-CONVENTION — n≥20:** grounded in Thammen's existing sample-size rule (RICS-aligned: n≥20 reliable / 10–19 indicative / 5–9 context / <5 insufficient), not a universal AVM constant.

---

## 8. Value-invariance contract

No-condition-input traffic stays **BYTE-IDENTICAL** — the 5-fixture gate (54/541/6 cost_led 2.4M · 56/647/6 geo_full 3.8M · 55/296/13 e25 2.6M · 56/565/21 matched 2.4M · 52/903/90 refusal) reproduces exactly, because (a) the seed penalties EQUAL the current `COST_CONDITION_PENALTY`, and (b) condition enters the value ONLY when the user supplies it (or the corpus later calibrates a stratum). The safe-fail fallback (missing/corrupt/schema-drift DB → `(None,None)` → hardcoded dict) guarantees the engine never regresses below today's behaviour.

---

## 9. Test plan

1. **5-fixture value byte-gate** — byte-identical to live (no-condition traffic).
2. **Seed-equals-hardcoded** — `_lookup_condition_penalty(grade) == COST_CONDITION_PENALTY[grade]` for every grade at n=1 (proves B2-1 is a value no-op).
3. **Safe-fail** — missing/corrupt DB → `(None,None)` → hardcoded fallback → value unchanged (mirrors the cap-rate safe-fail tests).
4. **Opt-in move** — `/details` condition=poor vs excellent on a cost-led villa → headline moves by the expected eff-age spread; no-condition → unchanged.
5. **RICS disclosure** — condition-supplied output carries the Assumption + limitation + MUC strings; no-input keeps the "not assessed" caveat.
6. **Calibrator round-trip** — `condition_calibrator.py` on a synthetic n≥20 corpus → DB rebuilt, confidence='reliable', engine reads the new numbers with ZERO code change. *(This is the proof the architecture is adaptable.)*
7. **R14** real-Chromium 390×844 — the condition control + the disclosure render, no overflow, 0 console errors.

---

## 10. Honest residual

At n=1 the per-grade penalties are NOT empirically calibrated — they are the existing hardcoded ladder **re-sourced from the single V001 certified sheet**, disclosed as INDICATIVE (MUC high, V001-only basis named). **The MECHANISM is production-grade and adaptable NOW; the NUMBERS are provisional until GT-2 reaches n≥20 per `(area, stratum, condition)` cell**, at which point `condition_calibrator.py` re-fits them with ZERO code change. The exact %-move of poor-vs-excellent on a live cost-led villa MUST be measured before B2-2 sign-off. Per-stratum elasticity is data-gated. This is the b16/E25 discipline: ship the honest indicative mechanism; calibrate when documented data arrives; never invent a coefficient; never chase asking prices (E1/E25).

---

## 11. Recommended sequence (each its own signed Gate-2, deploy-on-green)

1. **B2-1** (infra, value-invariant) — the DB + lookup + the guarded seam + the guard, seeded n=1 from V001 → live byte-identical. **Ships the adaptable infrastructure first, zero value risk.**
2. **B2-3** (RICS disclosure reword, value-invariant) — sequenced BEFORE B2-2 so the disclosure exists the moment value can move.
3. **B2-2** (user-condition pricing, value-affecting opt-in, disclosed-indicative) — MEASURE the live %-spread first, sign Gate-2 on the measured table.
4. **LATER (no new sprint code)** — `condition_calibrator.py` re-fits the numbers when GT-2 reaches n≥20; per-stratum + teardown-demo follow as the corpus grows — same code, only `condition_adjustments.sqlite` swaps.

---

## 12. What Anas signs (Gate-2 decisions)

1. **The architecture** — mechanism-vs-calibration split, the `condition_adjustments.sqlite` seam (cap_rates precedent), V001-seed n=1 → GT n≥20, numbers-not-code. ☐
2. **The taxonomy** — the 8 grades + the +8y "average" baseline (UAD C1–C6 aligned). ☐
3. **The penalty unit** — `penalty_years` (condition shifts effective-age, reusing the V001 curve). ☐
4. **The sequence** — B2-1 (infra, value-invariant) → B2-3 (disclosure) → B2-2 (pricing, measure-then-sign). ☐
5. **The disclosure** — the RICS Assumption + limitation + MUC triad, indicative at n=1 (lawyer/linguist personas). ☐

> On signature: build **B2-1 only** first (value-invariant infra), full DoD + R14 + live 5-fixture byte-gate, deploy-on-green. B2-2 (the value-moving slice) is signed separately on its measured table. **This is post-launch work — it does not block the invited launch.**
