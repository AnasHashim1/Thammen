# Multi-AI Validation Batch — Sprint B-1 (2.22.0a.21: land-floor / HBU decomposition + condition surfacing)

> **Document type:** DECISION-RECORD (authored by CC, 2026-06-04, from the **signed** B-1 brief). The
> multi-AI round itself was run in the **Claude.ai lane**; the LOCKED, convergent outcomes are reproduced
> below verbatim from the brief §2 D3 and as-shipped in `evaluate_unified.py` (a21).
> **Rule #54 status:** REQUIRED (Sprint touches RICS/methodology framing — a land-value-floor disclosure
> on a single-approach AVM).
> **Models:** GPT-5 + Gemini — reported **CONVERGENT** (per the signed brief).
> **Production baseline at decision time:** `thammen-sprint2p22p0a20-rics-compliant-status-label` (Heroku v159).
> **Shipped as:** Sprint 2.22.0a.21 (Heroku v160, commit `62f902a`, CHANGELOG_v73, Session_Log §20.21).

---

## ⚠️ Honesty note (Rule #36 / #63)
The **raw GPT-5 / Gemini transcript was NOT delivered to the CC lane** with the brief. This file therefore
records the **LOCKED outcomes** (citations, discipline, copy) exactly as signed in the brief — it does **not**
reproduce a verbatim model exchange, and none is fabricated. If a verbatim record is wanted, **Anas appends
the transcript under "§ Verbatim responses" below** (the Claude.ai lane holds it). The shipped engine copy +
citations are fully determined by the locked outcomes recorded here; nothing downstream depends on the
missing transcript.

---

## The question (framing)
For a single-approach (Sales Comparison) AVM, B-1 surfaces a **land-value floor** + **implied-building**
decomposition + a **land-anchored** disclosure next to the existing condition caveat. The multi-AI round
validated: (1) the correct RICS/IVS **citations** for each element against the **in-force 2025 edition**;
(2) the **discipline** that keeps the land floor an analytical decomposition (not a second valuation basis);
(3) the **Arabic copy** for the three new disclosure strings.

## Engine reality (load-bearing context)
- The headline value is `primary['value']` = Sales Comparison alone (100% of cases); cost/income are
  convergence checks only (per `MULTI_AI_VALIDATION_BATCH_2p22p0a4.md` Phase-0 finding). The land floor is a
  **decomposition of that one number**, never an independent valuation.
- Phase-0 §5 (`docs/PHASE0_SprintB_condition_axis.md`): the floor is `value_decomposition.land`
  (a18-aware `moj_reference`); Patch C suppresses it for the land-priced cohort (F1) → B-1 recomputes it
  INDEPENDENTLY. Condition is unassessed on every comparison path (R7).

---

## LOCKED outcomes (convergent GPT-5 + Gemini — verbatim from the signed brief §2 D3)

### A. Citations (validated vs the in-force 2025 edition)
| Element | Citation |
|---|---|
| Decomposition (Sales Comparison) | **VPS 3 / IVS 103** |
| Single-basis discipline | **VPS 2 / IVS 102** |
| HBU land floor | **VPS 2 / IVS 102** (Highest-and-Best-Use) |
| Not-inspected assumption-limitation | **VPS 2 + VPS 4** (+ scope **VPS 1 / IVS 101**) |
| Uncertainty | **VPGA 10 + VPS 6 / IVS 106** |
| Model-derived / not-a-written-valuation | **VPS 5 / IVS 105** |
| Comparable-data quality | **IVS 104** |

### B. Discipline (both models)
- The **land floor = ANALYTICAL DECOMPOSITION**, never a standalone "land market value" / second basis.
- **Condition = material uncertainty + assumption-limitation**, NOT a special assumption, NOT "assumed
  standard condition."
- **Land-anchored = a MODEL inference**, never "the market prices it as land."

### C. Arabic copy (synthesized from both models — shipped VERBATIM in a21)
- **`[land_floor]`** — «تفكيك تحليلي ضمن نموذج المقارنة — قيمة الأرض: ~X ر.ق (وفق صفقات أراضٍ مماثلة؛ يعكس الاستخدام الأمثل للأرض، وليس قيمة سوقية مستقلة).»
- **`[implied_bldg]`** — «القيمة الضمنية للمبنى (ناتج حسابي: التقدير ناقص الأرض): ~Y ر.ق — غير مُتحقَّقة ميدانياً (نوع البناء والعمر والحالة غير معروفة).»
- **`[land_anchored]`** — «يشير النموذج إلى أن القيمة المقارنة لا تتجاوز قيمة الأرض المجردة؛ القيمة الضمنية للمبنى ≈ صفر (قد يُعتبر عقاراً للتطوير).»
- Bidirectional condition disclosure = the LIVE `condition_note_ar` (a17/a19), **REUSED** — NOT re-added.
- EN brief surface mirrors the AR (analytical land baseline / implied building value (computational, not
  field-verified) / model land-anchored inference).

---

## Resolution — how it shipped (a21)
- Copy constants `LAND_FLOOR_NOTE_AR/EN`, `IMPLIED_BLDG_NOTE_AR/EN`, `LAND_ANCHORED_NOTE_AR/EN` +
  `_VALUE_FLOOR_CITATION_AR/EN` (`evaluate_unified.py`), AR numbers LRM-wrapped (U+200E, Operational #25).
  `X` = land floor, `Y` = implied building (rounded to nearest 10,000 for display; structured fields exact).
- Citation tag on the block: «منهج المقارنة بالمبيعات (VPS 3 / IVS 103)؛ قيمة الأرض تعكس الاستخدام الأمثل
  (VPS 2 / IVS 102)» — i.e. decomposition basis + HBU, the two load-bearing citations from §A.
- Discipline §B enforced by the wording itself ("تفكيك تحليلي … وليس قيمة سوقية مستقلة" = analytical, not
  standalone; "ناتج حسابي … غير مُتحقَّقة ميدانياً" = computational + uncertainty; "يشير النموذج" = model
  inference). Condition caveat reused (a17/a19), not duplicated.
- **Isolated test guards the copy verbatim** (`test_sprint_2_22_0a21.py`: "AR …copy verbatim" ×3 +
  "no Latin in the 3 AR notes") → a future drift fails loudly. DoD 392/15/45/64; live v160 zero value drift.

## Open / parallel (non-blocking — brief §7)
- **PDF-prominence check** (Gemini flag): confirm in the RICS Red Book / IVS **PDF** the precise clause +
  required **PROMINENCE** of uncertainty/variance disclosures in an AVM/automated interface (candidate
  **IVS 105 / IVS 106**). Does NOT block ship; if the PDF demands greater prominence → fast-follow.
- The §A citations are at **genus level** for the in-force 2025 edition; the PDF lookup would add sub-clause
  specificity (same discipline as the a4 "Citation status — OPEN" parallel track).

## § Verbatim responses (GPT-5 / Gemini) — TO BE APPENDED BY ANAS (Claude.ai lane)
*(empty — the raw transcript was not delivered to CC; paste it here for a verbatim record. The LOCKED
outcomes above are authoritative for what shipped.)*

---

## Cross-references
- `docs/BRIEF_SprintB1_land_floor_decomposition.md` (signed brief — §2 D3 is the source of the locked copy).
- `docs/PHASE0_SprintB_condition_axis.md` (Phase-0 §5 recon — F1 / F2 / land-number provenance).
- `CHANGELOG_v73.md` + `docs/Session_Log.md` §20.21 (as-shipped).
- `docs/MULTI_AI_VALIDATION_BATCH_2p22p0a4.md` (prior batch — the citation-prominence parallel-track pattern).
- `docs/Operational_Rules.md` #54 (multi-AI sprint-open) + #63 (Claude.ai-authored docs auto-persist).
