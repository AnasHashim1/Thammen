# PHASE 0 — Sprint 2.22.0a.4 — Disclaimer Rendering Map (P0.1)

**Status:** read-only audit, complete. Hard prerequisite for T2.8.
**Method:** source-of-truth grep on `evaluate_unified.py`, `api.py`,
`reasoning_trace.py`, `scope_of_service.py` for definition sites + on
`index.html` for the render path. Cross-checked against `.smoke_p0_villa.json`
+ `.smoke_p0_apt.json` (live captures).

---

## The 5 candidate layers — definition vs UI render

| Layer | Field | Defined where | Renders in UI brief? | index.html line |
|---|---|---|---|---|
| **A** | `methodology_disclaimer_ar` | `evaluate_unified.py` (1932, 2354, 2585, 2703, 4065) | **NO — JSON-only** | *(never referenced)* |
| **B** | `muc_clause_ar` (formal VPGA 10 / VPS 6 / IVS 106) | `material_uncertainty.py` + `evaluate_unified.py` | **YES** | 722–730 |
| **C** | vernacular MUC banner | MUC section body | **YES** | (within MUC section) |
| **D** | `disclaimer` (top-level, SHORT C4) | `evaluate_unified.py` (2005, 2449, 2663, 2769, 2902) | **YES** | 1253–1254 (`d.disclaimer`) |
| **D′** | `reasoning_trace.disclaimer` (LONG C4) | `reasoning_trace.py:117` | **NO — explicitly skipped** (`k==='disclaimer' return` in the `reasoning_trace` case) | 1494-block |
| **E** | `service_scope.disclaimer_ar` | `scope_of_service.py` + `evaluate_unified.py` | **YES** | 831 (`ss.disclaimer_ar`) |

### Adjacent fields that already render (not disclaimers, but relevant to T2.8 + T-method)
| Field | index.html line | Note |
|---|---|---|
| `methodology_ar` | 675, 903–904, 1164 | T-method(a) already collapsed this to `أساس التقدير هو منهج المقارنة بالمبيعات.` |
| `methodology_note_ar` | 987, 1036 | already exists at top-level (1229), v3 detail (3792), brief-section (4498) |
| `service_scope.methodology_ar` | 828 | renders directly above `ss.disclaimer_ar` |

---

## Other (non-brief) C4 emission sites — separate endpoints, NOT the evaluate brief
- `api.py:845` — `disclaimer_ar` (LONG C4), the `/api/disclaimer`-style payload.
- `api.py:904` — `what_thammen_does_not[0]` (`لا يُصدر تقرير تثمين رسمي…`), the `/api/about` payload.
These surface only on their own dedicated pages/endpoints, not in the main
report brief. Out of scope for the brief-path consolidation, but listed so the
"pick one canonical D" decision stays consistent across the codebase.

---

## Decisions this map locks for T2.8

1. **Folding A → D is render-invisible.** `methodology_disclaimer_ar` (A) never
   reaches the UI, so removing it / relocating its `AVM وفق VPS 4` provenance to
   the methodology surface changes **zero** user-visible pixels. Only JSON
   consumers (if any) are affected. Safe.
2. **E renders.** Reclassifying `service_scope.disclaimer_ar` → a methodology
   field requires an `index.html` line-831 update (or it disappears from the UI).
   Decision: **leave the rendered text in place; rename the JSON key only if we
   also update line 831.** Lowest-risk path = keep `service_scope.disclaimer_ar`
   rendering as-is (it is methodology content, but it is the SOLE asset-class
   methodology line the user sees) and document it as methodology, not a
   disclaimer, via a code comment — defer a field-rename to a dedicated refactor
   (Rule #47: alias/rename = its own pass).
3. **D is the one true rendered "not-a-formal-valuation" layer** in the brief
   (top-level `disclaimer`, short C4). D′ (reasoning_trace, long) is dead in the
   UI. The canonical D wording = the SHORT C4 already live at the 5 evaluate
   sites. The LONG variant (D′, api.py, reasoning_trace) stays for its own
   endpoints but is not the brief's canonical D.
4. **C4 lock holds.** The verbatim string
   `ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS`
   is present and must stay (regression pin in T5 tests).

---

---

## P0.2 — Reconciliation-weighting documentation check

**Question:** is the "three-way reconciliation" (market + cost + income)
weighting logic documented (the basis the methodology phrase rests on)?

**Finding: there is NO weighting, because there is NO blend.**

- `evaluate_unified.py:1581` / `:1693`: `val = primary['value']` — the headline
  valuation is **Sales Comparison alone in 100% of cases**.
- `_analyze_reconciliation(primary, cost, income)` (`:1688`) uses cost/income
  **only** to compute a convergence/divergence *status* from `spread_pct`
  (`strong_convergence` <15% / `moderate_convergence` <30% / `divergence` ≥30%).
  Cost/income values **never enter the headline number** — no weighted average,
  no documented weights, no blend.
- Module docstring (`:14–21`) is explicit: Sprint 1.a's equal-weight three-way
  blend was **wrong** (produced 2.9M for Marikh vs ~4.5M truth) and was removed.
  Sprint 1.b keeps comparison as primary per **IVS 105**; cost/income are
  "reconciliation transparency only."

### Consequence for T-method(a) — CONFIRMED CORRECT
- The retired string `… مع توفيق ثلاثي الطرق` (three-way reconciliation) was
  **misleading**: it implied a blend that does not happen.
- Per KICKOFF branch logic: *"If reconciliation weighting is not documented →
  plain language and drop the formal-sounding label."* T-method(a) already did
  exactly this: `أساس التقدير هو منهج المقارنة بالمبيعات.`
- **No IVS 105 anchor needed in the headline** (we no longer claim reconciliation
  there). The reconciliation *status* that stays in JSON IS a legitimate IVS 105
  convergence check — keep it as analytics/secondary surface, do not promote it
  to the headline.
- Question F (Appendix A) can be answered from this finding: option (2) applies
  — undocumented weighting → plain descriptive language required, which is what
  shipped. The multi-AI batch confirms, does not gate, the choice.

---

*Authored 2026-05-28→29 during Sprint 2.22.0a.4 Phase 0. Pairs with KICKOFF
P0.1 + P0.2. Read-only — no production code changed by this audit.*
