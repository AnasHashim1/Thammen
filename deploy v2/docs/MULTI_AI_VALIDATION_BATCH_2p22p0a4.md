# Multi-AI Validation Batch — Sprint 2.22.0a.4 (Disclosure & Framing Honesty)

**Drafted:** 2026-05-28 (after Phase 0 + P0.1 confirmation pass on v139).
**Rule #54 status:** REQUIRED (Sprint touches regulatory/methodology framing).
**Models:** GPT-5 + Gemini (current default per #54 mechanism).
**Production baseline:** `thammen-sprint2p22p0a3-arabic-surface-honesty` (Heroku v139).

---

## Question E — Disclaimer consolidation 4 → 2 (Option α)

**Status:** RE-USE the 2.22.0a.3 batch answer (per Rule #54 §Re-use protocol).

Both GPT-5 and Gemini endorsed 4→2 in `docs/MULTI_AI_VALIDATION_BATCH_2p22p0a3.md` under the explicit guardrail that the MUC reservation bucket and the not-a-formal-valuation provenance bucket stay **distinct** (do NOT merge). 2.22.0a.4 T2.8 implements exactly that under Option α (reduce, never add):

- **Bucket 1** = B (red MUC card, RICS clause at index.html:738) — kept verbatim.
- **Bucket 2** = D (C4 verbatim, canonical wording across 9 sentence-form emission sites; `api.py:904` list-item variant `NEW_LIST_ITEM` stays as Gate-3-documented divergence).
- **A** (`methodology_disclaimer_ar`) = JSON-only cleanup (no UI surface; fold into D semantically).
- **C** (vernacular `banner_ar`) = JSON-only cleanup (no frontend surface added — Option α; the `banner_ar` field at index.html:496 is the *data-freshness* banner, name collision — NOT layer C).
- **E** (`service_scope.disclaimer_ar`) = UNTOUCHED (UI-rendered at index.html:831 as methodology scope, not a disclaimer; rename to `methodology_note_ar` collides at index.html:987/1036).

No re-run for Question E.

---

## Question F — Methodology phrase: "basis + check" vs "single-approach only"

### Engine reality (load-bearing context)

Phase 0 traced `evaluate_unified._analyze_reconciliation` (line 1688). It is a **status reporter**, not a blender. The valuation always equals `primary['value']` (Sales Comparison Approach alone), 100% of cases. The cost and income approaches are computed independently and used **only as convergence checks** on the primary number; they never blend, weight, or otherwise contribute to the value itself.

The engine's internal docstrings have always been honest about this (`# Primary valuation (from comparison approach only)`, `# Cross-checks (explicitly labeled as such, NOT in valuation)`). The user-facing Arabic methodology line drifted — it claimed `توفيق ثلاثي الطرق` (three-way reconciliation), a blending verb the code does not back. This is the canonical instance of the §2c "derive-don't-author" failure class (`docs/DESIGN_2p23_stage_authority_boundary.md`).

### Proposed status-aware replacement (single edit at evaluate_unified.py:4051)

The replacement is derived from `reconciliation['status']` at render time:

| `status` | Shipped string (final wording = Anas sign-off) |
|---|---|
| `comparison_only` | `أساس التقدير هو منهج المقارنة بالمبيعات.` (no check clause — no check actually ran on this property) |
| `strong_convergence` / `moderate_convergence` | `أساس التقدير هو منهج المقارنة بالمبيعات، مع فحص اتساقه مع منهجَي التكلفة والدخل (تحقّق تقارب وفق RICS).` |
| `divergence` | `أساس التقدير هو منهج المقارنة بالمبيعات. فحص التقارب مع منهجَي التكلفة والدخل أظهر تبايناً جوهرياً — مراجعة موصى بها.` |

*Note: This table represents the pre-Amendment scope. See Resolution § for the Amendment outcome (universal bare line, dispatcher removed).*

Plus de-Latinization on the same string: `AVM` → `نموذج تقييم آلي`, `Sales Comparison Approach` → `منهج المقارنة بالمبيعات`.

### The question

1. Is the framing **"X is the basis, checked against Y and Z"** — i.e. the convergence shapes above — an accurate and RICS-defensible description of an AVM whose value is Sales Comparison alone and whose cost/income runs are *only* post-hoc convergence checks?

2. Or does naming cost/income at all (even as explicit "checks") over-imply a three-method process to the average non-expert reader, such that the honest user-facing line should **omit** cost/income entirely and state only the Sales Comparison basis (i.e., ship the bare `comparison_only` shape universally and drop the convergence-status sub-shapes)?

3. For the `comparison_only` shape specifically (where no convergence check actually ran on this property — typically because cost or income inputs were unavailable): **weigh both directions before answering; do not pre-tilt toward either.**

   (a) **Reading of the bare line** *"أساس التقدير هو منهج المقارنة بالمبيعات."* — does the silence on cost/income risk being read by a non-expert as implicit confirmation that those approaches *were* considered (and silently consistent), when in fact they were never run on this property? Or is silence the honest default when an approach was not applied?

   (b) **Reading of an explicit "no convergence check was run" clause** — e.g., `لم يُجرَ فحص تقارب لعدم توفّر بيانات` — does adding this risk implying a methodological *deficiency* or omission on the report, when single-approach with no convergence check is in fact a fully standard and defensible path under RICS for cases where other approaches are not applicable or supportable? Or is the explicit acknowledgement the more transparent reporting practice?

   Recommend the shape that is more honest to the average non-expert reader AND defensible under the standard. If the two criteria diverge for this sub-question, surface the divergence explicitly. The drafted "bare line" is the current default; do not treat it as the preferred answer.

4. Any regulatory exposure in Qatar — given Thammen publishes under RICS Red Book Global Standards (effective 31 January 2025) framing in the MUC card (VPGA 10 / VPS 6 / IVS 106) — from naming the three approaches in a single-approach AVM's methodology line, even with the "checks-only" qualifier?

### Out of scope for this question
- **IVS 105 anchor**: rejected upstream by Phase 0 — there is no reconciliation of the value to anchor; the engine is single-approach. Do not propose IVS 105 framing in your answers.
- **`AVM` Latin token**: handled separately as the de-Latinization step (b) of T-method, not asked here.
- **Disclaimer buckets**: Question E above, already resolved via re-use.

### Expected response format (each model, independently)
- ≤ 300 words.
- Distinguish "accurate/defensible under the standard" from "honest by average-reader comprehension" if those diverge.
- Cite the specific RICS / IVS provision relied on (if any) — clause name + current effective-edition number, not just topic.
- If you disagree with the proposed status-aware shape, propose a concrete alternative (a string), not just a critique.
- Flag any inter-model disagreement for third-party resolution (RICS Red Book PDF, IVS standards site, MoJ Qatar publication).

---

## Responses (verbatim — captured 2026-05-28)

### GPT-5

1. **Accurate/defensible under RICS:** Yes, if the wording explicitly distinguishes the derived value from the cross-checks. Under RICS Red Book Global Standards 2024 VPS 3 and IVS 106 (Valuation Reporting), reporting must describe the approach(es) applied and the basis for conclusions, but does not require every computed approach to contribute numerically to the final value. "Basis + consistency check" is therefore defensible. However, "توفيق" / "reconciliation" materially overstates the mechanics because no weighting or anchoring occurs.

2. **Average-reader honesty diverges somewhat from formal defensibility.** Even with "checks-only" wording, many non-experts will still infer a blended three-method valuation. Therefore, I would *not* surface cost/income in the primary methodology line unless a convergence event is materially informative. Safest default:
   `أساس التقدير هو منهج المقارنة بالمبيعات.`

Optional secondary disclosure:
`تم إجراء فحوص اتساق إضافية عند توافر بيانات داعمة.`

3(a). Silence is normally honest where approaches were not applied. Under IVS 106 / VPS 3, omitted approaches need not be affirmatively narrated unless omission affects user understanding. The bare line does not inherently imply cost/income were run.

3(b). An explicit "no convergence check was run" clause increases technical transparency but risks communicating methodological weakness to ordinary users, despite single-approach valuation being fully acceptable under RICS where other inputs are unavailable or unreliable. Recommended compromise:
Do not place the omission in the headline methodology line. If needed, place it in expandable methodology detail:
`لم تتوافر بيانات داعمة كافية لإجراء فحوص اتساق إضافية.`

4. **Yes, some exposure exists** if "three-way reconciliation" remains. Given the engine is mechanically single-approach, describing it as "توفيق ثلاثي الطرق" risks being viewed as overstating methodology under VPS 6 / IVS 106 principles requiring clear and non-misleading reporting. "Cross-check" / "فحص اتساق" materially reduces that risk.

### Gemini

**1. Defensibility of the "Checked" Framing**
It is accurate and defensible under **IVS 106.30(d)** (requires explaining the approach and reasoning) and **RICS VPGA 10.4** (AVM transparency). Disclosing secondary cross-checks is standard practice, provided the report does not obscure the sole quantitative basis of the estimate.

**2. Over-implication to Non-Experts**
*Divergence:* **IVS 106** encourages full disclosure of analytical checks, but for the average reader, naming three approaches risks implying a blended calculation. You should retain the check for convergence shapes to build trust, but emphasize exclusivity.
*Alternative Draft:* `أساس التقدير هو منهج المقارنة بالمبيعات حصراً. استُخدم منهجَا التكلفة والدخل لاختبار التقارب فقط ولا يؤثران على القيمة.` (The estimate is based exclusively on the Sales Comparison approach. Cost and Income approaches were used solely to test convergence and do not affect the value.)

**3. The `comparison_only` Shape**
*(a)* Under **RICS VPS 3.2(l)**, you must state the principal approach used; silence is the standard for approaches *not* applied. Silence does not legally or practically imply inclusion.
*(b)* Adding a "no check" clause implies a methodological deficiency to non-experts, despite a single-approach valuation being fully standard when data is limited.
*Recommendation:* Use the bare line (`أساس التقدير هو منهج المقارنة بالمبيعات.`). Silence is compliant with the standard and prevents consumer misinterpretation.

**4. Regulatory Exposure**
Exposure exists under **RICS VPS 3.1(a)** (reports must not be ambiguous or misleading) and **VPGA 10**. If a user assumes Thammīn (ثَمِّن) triangulates value like a fully commissioned human valuer, it risks misrepresentation. Using strictly restrictive language (e.g., "حصراً" / exclusively) directly mitigates this exposure by severing any implied mathematical link between the convergence tests and the final AVM output.

---

## Resolution — Path A / Amendment (universal bare line, dispatcher removed)

**Decision date:** 2026-05-28  
**Decision authority:** Anas (Rule #32 signature pending commit-prep)  
**Methodology track:** claude.ai session

### Per-question read

| Q | Verdict | Notes |
|---|---|---|
| Q1 (basis+check defensible?) | **Convergent YES with conditions.** Both endorse "X basis, Y/Z checks" framing as defensible under IVS 106 + VPGA 10. GPT-5 explicit: verb must shift `reconciliation/توفيق` → `consistency/اتساق`; `تحقّق تقارب وفق RICS` suboptimal. Gemini: defensible "provided report does not obscure sole quantitative basis." | Informs language hygiene; does not bind shape (Q2 decides). |
| Q2 (does naming cost/income over-imply three-method?) | **Divergent on convergence-shape, convergent on the rest.** Both: current `توفيق ثلاثي الطرق` is wrong; proposed `تحقّق تقارب` draft also risks over-implying. Both: bare line is right for `comparison_only`. Fork — GPT-5: bare headline universally, checks only in expandable-detail surface. Gemini: keep three-branch headline with `حصراً` + `لا يؤثران على القيمة` exclusivity markers. | **Resolved to Path A / Amendment: universal bare line.** See synthesis below. |
| Q3 (comparison_only: bare vs explicit "no check ran"?) | **Convergent — bare.** Both: silence is the honest default for approaches not applied; explicit `لم يُجرَ فحص تقارب` "implies methodological deficiency" to non-experts. Both anchor on VPS 3.2(l)-equivalent reasoning. | Aligns with Path A. No `لم يُجرَ` clause in headline. |
| Q4 (Qatar regulatory exposure?) | **Convergent on existence.** Mitigations complementary, not opposed — GPT-5 (verb fix: reconciliation→cross-check) + Gemini (exclusivity markers). | Path A satisfies both mitigations: bare line removes the problematic verb AND the three-method enumeration in one collapse. |

### Path A / Amendment synthesis

Four load-bearing points justify the decision:

1. **Comparison_only is the majority case in production** (residential typically lacks rental comparables and current build-cost inputs). Both models endorse bare line here.
2. **GPT-5 endorses bare universally.** Its convergence-case preference is also bare-headline + checks-in-expandable-detail-surface (deferred); bare-everywhere meets this fully.
3. **Gemini's reservation is satisfied by surface separation, not by headline placement.** Gemini's rationale for retaining checks in the headline (`build trust`) is not standards-required. Gemini's own VPS 3.2(l) reasoning — "silence is the standard for approaches not applied" — generalizes from `comparison_only` to all status values. Gemini's exclusivity-marked language is preserved on the deferred secondary-surface roadmap, not lost.
4. **Engine simplification.** Collapsing removes the `reconciliation['status']` dispatcher at the wording layer entirely. Status remains computed and stored in JSON (analytics + native secondary surface via the existing `reconciliation` object: `status` + `label_ar` + `message_ar` + `spread_pct` + `gaps_pct`). Single edit; single regression invariant.

### Implementation — Amendment (deviation from kickoff)

T-method spec at `evaluate_unified.py:4051`:
```python
methodology_ar = 'أساس التقدير هو منهج المقارنة بالمبيعات.'
```

Constant. No status switch at wording layer. Universal across all `reconciliation['status']` values.

De-Latinization (b): `AVM` → `نموذج تقييم آلي`, `Sales Comparison Approach` → `منهج المقارنة بالمبيعات`.

**Code-comment citation at edit site:** "RICS Red Book Global Standards 2024 / IVS 106 (Valuation Reporting), effective 31 January 2025." No specific VPS sub-clause until parallel citation discipline (see below) resolves.

### Rule #39 — kickoff deviation justification

The kickoff (on disk: `.kickoff_2p22p0a4/KICKOFF_2p22p0a4.md`; plus a chat-held v2 update that closed Phase 0 and locked scope, which was lost with a previous CC session) spec'd a status-aware methodology_ar with three branches (`comparison_only` / convergence / divergence). The on-disk Question F three-branch table (above in this doc) reflects that pre-Amendment scope.

Amendment collapses this to a constant: `أساس التقدير هو منهج المقارنة بالمبيعات.` for all status values.

Justification:

1. Phase 0 mechanical audit: `_analyze_reconciliation` is a status reporter, not a blender; `primary['value']` = Sales Comparison alone in 100% of cases.
2. Question F multi-AI validation (this batch): GPT-5 + Gemini converged on bare-line for `comparison_only` (majority case); divergence only on convergence-case shape; GPT-5 explicitly endorsed bare universally; Gemini's restrictive-language alternative satisfied by silence under VPS 3.2(l)-equivalent reasoning.
3. Existing `reconciliation` JSON object is the native secondary surface; no new dispatcher needed at the methodology_ar layer.
4. Sprint theme alignment: reduce, not add.

Status remains computed + JSON-stored for analytics + frontend rendering at frontend's discretion.

### Deferred — secondary-surface variants

For future sub-sprint consideration (2.22.0a.5 / 2.22.0b). Both variants land on a non-headline expandable disclosure surface when (and if) added:

- **GPT-5 lighter:** `تم إجراء فحوص اتساق إضافية عند توافر بيانات داعمة.`
- **Gemini stronger (with GPT-5 verb fix):** `استُخدم منهجَا التكلفة والدخل لاختبار اتساق التقدير فقط، ولا يؤثران على القيمة.`

### Citation status — OPEN, parallel discipline

**Both GPT-5 and Gemini cited VPS 3 (not VPS 6).** GPT-5: "VPS 3 and IVS 106 require disclosure of the valuation approach(es) actually applied." Gemini sub-paragraph specificity: VPS 3.2(l) ("state the principal approach used; silence is the standard for approaches not applied"), VPS 3.1(a) ("reports must not be ambiguous or misleading"), VPGA 10.4, IVS 106.30(d).

**Context:** Sprint 2.22.0a Phase 1.5b /12 correction was VPS 3 → VPS 6 for the **MUC card** framing. May be surface-specific:
- VPS 6 may be correct for material-uncertainty disclosure (MUC card at `index.html:738`).
- VPS 3 may be correct for methodology-line disclosure (the T-method edit surface).

**Pending: targeted Red Book Global Standards 2024 PDF lookup.** Until resolved, T-method code comment cites the standard genus only (RICS Red Book 2024 / IVS 106), no specific VPS sub-clause. The Resolution outcome (Amendment) is unaffected by citation outcome; only code-comment specificity is.

Routing:
- **Branch X — VPS 3 correct for T-method surface:** update T-method code comment to cite VPS 3; document as surface-specific citation discipline finding; candidate amendment to Rule #54 or new rule.
- **Branch Y — VPS 6 correct on both surfaces:** /12 audit holds across surfaces; document as Rule #54 strengthening case (both models drew on outdated training).
- **Branch Z — Inconclusive after PDF read:** defer specific-VPS citation; T-method ships genus-only; re-attempt in future sprint.

### Cross-references

- `docs/Operational_Rules.md` — Rule #54 (multi-AI validation; origin Sprint 2.22.0a Phase 1.5b /12; this batch is the production re-application).
- `docs/MULTI_AI_VALIDATION_BATCH_2p22p0a3.md` — Question E answer (re-used).
- `.kickoff_2p22p0a4/KICKOFF_2p22p0a4.md` — original sprint kickoff (v1). The chat-held v2 update (Phase 0 closed + scope lock) was held by a previous CC session and is lost; the Amendment endpoint documented here supersedes both v1 and the lost v2 chat-held draft.
- `docs/DESIGN_2p23_stage_authority_boundary.md` §2c (derive-don't-author — Q F resolution is the first production instance).

