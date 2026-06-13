# PHASE-0 RECON — DEF-UX5 «تبديل إنجليزيّ AR|EN» — PREMISE FALSIFIED (read-only, NOT shipped)

> **Date:** 2026-06-13. **Engine UNCHANGED — live stays b37 / Heroku v208 (byte-identical).**
> No engine/frontend change, no deploy. This is a measurement artifact (Rule #42 deferred-work
> documentation + #63 docs-persist) so no future session re-attempts DEF-UX5 on the false
> «الـbackend جاهز» premise. #57 handshake at start: b37/v208, `master==origin @ e198320`, qars
> healthy (162,516), MoJ 164d — matched the snapshot exactly.

## 0. The question

The #65 handoff routed DEF-UX5 (AR|EN UI language toggle) as the next unit, framed as
**«🟢 أخفّ شريحة أمامية (الخلفية `_en` مبثوثة جاهزة)»** — a deploy-on-green frontend slice because
the engine allegedly already broadcasts `_en` twins. The §4ب persona-review ledger itself tags it
**🟠 amber / NET-NEW**: *«تبديل إنجليزيّ AR|EN (5/10؛ الصحفي = فتح السوق الدوليّ) | زر لغة يستعمل حقول
`_en` المبثوثة (يبدأ READ-ONLY) + R14 bidi | NET-NEW frontend (الـbackend جاهز)»*. Both rest on one
load-bearing claim: **the backend `_en` broadcast is ready and the frontend can just flip to it.**
Recon measured that claim.

## 1. Method

Direct grep/measurement (CC) + a 4-reader parallel workflow (Explore agents over the engine modules,
`index.html`, the spec, and the test surface). All read-only; no GIS needed (pure code/docs).

## 2. Findings — the premise is FALSE

### 2.1 Engine `_en` coverage = PARTIAL (32.6%), not «ready»

| Field family | `_ar` emitted | `_en` twin | Coverage |
|---|---|---|---|
| `note_*` | 29 | 10 (`note_en`) | partial |
| `label_*` | 11 | 4 | partial |
| `banner_*` | 12 | 2 | partial |
| `title_*` (briefs) | 23 | ~7 (brief titles only) | partial |
| `method_label_ar` | 19 | **0** | none |
| `message_ar` | 12 | **0** | none |
| `source_ar` | 11 | **0** | none |
| `role_ar` | 11 | **0** | none |
| `methodology_*`/`known_unknowns_ar`/`explanation_ar`/`asset_type_ar`/`evidence_ar`/`reason_ar`/`cap_rate_label_ar`/`disclaimer_ar`/`assumptions_ar` (scenarios+cost stack)/market-regime shock layers | many | **0** | none |

**Workflow verdict (corroborated):** **28 field-types carry both `_ar`/`_en` = 32.6% of 86 unique
`_ar` fields; 58 user-facing `_ar` fields (67.4%) have NO `_en` twin.** `output_briefs.py` = 70 `_ar`
vs 19 `_en` (~15% at the section level). **COMPLETE-EN surfaces** (the strength): the MUC clause
(`muc_clause_ar/en`), the RICS methodology note (`rics_methodology_note_ar/en`), scope-of-service
(`service_level_ar/en` + `methodology_ar/en`), `rics_compliant_status_ar/en`, scenario labels
(`SCENARIO_LABELS`), and the 4 brief **titles** — i.e. the **compliance/methodology** strings.
**AR-ONLY** (the gap): the core result descriptors (`method_label`, `source`, `role`, `reason`,
`cap_rate_label`, `known_unknowns`, `explanation`, `asset_type`), the brief **section bodies**
(due-diligence questions, seller tips, investor market-context benchmarks), and the
**narrative-rich short-report copy** (the «بيتك عمره فوق X سنة…» story, the «وش لو؟» scenarios text,
the cost-led story) — value-bearing, expert-authored copy, not find-replace-translatable.

### 2.2 Frontend consumes ZERO `_en` today — the broadcast is DEAD

`grep` for any `_en` consumption in `index.html` = **empty**. `show()` / `showConfirm()` /
`showReport()` / `showShortReport()` read `_ar` fields **directly** from the response; the same
response object carries no `_en` sibling at the render sites. The ~28 engine `_en` fields that DO
exist are **dead-broadcast** (computed, never rendered). So even the 32.6% is not wired — a toggle
would have to add the consumption AND fall back gracefully where the `_en` is missing (67.4%).

### 2.3 ~80 client-authored Arabic labels + Terms ~800w + bidi flip — no EN source at all

`index.html` = 3072 lines, **740 bearing Arabic**. Client-authored AR strings a real toggle must
also flip (no backend field exists for these): the b31 «🔍 كيف وصلنا لهذا الرقم؟» accordion title,
the b35 «حاسبة التمويل التقريبية» calculator labels (+ the short-report `_srPayment` variant), the
b37 «🔧 آليّة الكلفة» label, screen headers/buttons («ابدأ التقدير», «تابِع بهذه البيانات»,
«التقرير الكامل», «التفاصيل الكاملة», «طباعة / PDF»), accordion titles, form validation errors, the
4 loading-step labels, the multi-QARS alert template, the a24 consent/entry gate (~8 lines), and the
**Terms & Privacy modal (~800 words)**. `<html lang="ar" dir="rtl">` is hard-wired; an EN/LTR mode
must flip `dir`, border-right→left, padding/margin semantics, text-align, font fallback — while
**preserving** the intentional `dir=ltr` numeric inputs (line 58). **Existing scaffolding** (real but
static): a `<details>` «English summary» in the beta gate, a static EN Terms section, and `.bg-en`
LTR CSS — proof the concept exists, but **unused/read-only static**, not a toggle.

## 3. Verdict — DEF-UX5 is a Gate-2 localization PROJECT, not a deploy-on-green slice

A **coherent** AR|EN toggle requires, at minimum:
1. **Engine (Gate-2 copy):** author EN twins for the ~58 `_ar` fields that lack them (incl. the
   value-bearing narrative copy — expert translation, not mechanical), across `evaluate_unified.py`,
   `output_briefs.py`, `material_uncertainty.py`, `scope_of_service.py`, `geometric_factors.py`,
   `market_regime.py`.
2. **Frontend:** add `_en` consumption + missing-field fallback to all 4 render fns; a client-side EN
   string map for ~80 labels; a language-state mechanism; the `dir`/LTR/bidi flip (R14 re-measure).
3. **Discipline:** value-invariant (the number never changes) — but the copy is **user-facing →
   HARD GATE 2**, and a «READ-ONLY start» that flips only the 32.6% covered fields would render an
   **incoherent ~⅓-English screen** (worse UX than full AR, and dishonest «English» that isn't).

**There is no honest narrow first slice that ships clean this session:** no single user-facing screen
is fully EN-covered (even the figure's surrounding notes — condition/leadership/cost-mechanics — are
mixed coverage). The «backend جاهز» premise is the §20.26/§20.29/§20.32 pattern: a handoff plan
overturned by measurement.

## 4. Re-route landscape (the 🟢 frontend backlog is EXHAUSTED)

The shipped 🟢 slices (§4ب-2: UX11/12/13/14/16; §4ب: UX3/UX9) consumed the easy frontend value.
Every remaining item now needs a signed brief or a product decision:

| Item | State | Why not deploy-on-green |
|---|---|---|
| **DEF-UX1** keystone comparables | 🔴 Gate-2 + recon | highest §4ب value; needs a signed brief; the «built-free» claim was falsified → needs a data recon first |
| **DEF-UX5** AR|EN toggle | 🟠→ Gate-2 project | THIS recon — localization project (engine `_en` + client dict + bidi) |
| **DEF-UX8** affordability/LTV guards | 🟡 net-new | needs an income input + financial-guidance copy (light Gate-2) |
| **DEF-UX4** freshness | banner ✅ already shipped (Sprint 2.7); the market-adj **slider is value-affecting (Gate-2)** |
| **DEF-UX6** improvement-delta | net-new display | brushes b13/b18 age-sensitivity; needs design |
| **DEF-UX15** autocomplete | ⛔ BLOCKED | QARS data-drain (recon b35) |
| **DEF-UX17** heirs/bank · **DEF-UX18** smart field · map-pin | 🟡/🔴 | Gate-2 copy/scope or new engine |
| accuracy backlog | parked | B-2 (n≥20) · §6 v2 remainder · **GT-collection D-3** (the binding decision per RISK_SUMMARY) |

## 5. Recommendation

1. **Do NOT ship DEF-UX5 as a 🟢 slice.** Re-classify it in `ISSUES_LOG §4ب` from «🟠 / backend جاهز»
   to **«Gate-2 EN-localization project — backend 32.6% covered / frontend consumes 0 / 740 client-AR
   lines; needs a signed multi-file brief»** (planning-lane ledger edit).
2. **Next unit = a recon, not a build.** The highest-value path is **DEF-UX1 (keystone comparables)**:
   CC runs the read-only §5 recon (is the driving MoJ comparable-transaction set surfaceable per the
   existing response? what does the «built-free» falsification actually leave?) → de-risks the brief →
   Claude.ai drafts the Gate-2 brief. (Alternatively: route DEF-UX5 localization to a Gate-2 brief, or
   pivot to the accuracy track / GT-collection D-3.)

**Carried forward (Rule #42):** the dead-broadcast `_en` fields (~28) are latent assets a future
localization sprint reuses; the static EN Terms/«English summary» scaffolding + `.bg-en` CSS are the
seed. The «التقدير السوقي» term remains PROVISIONAL.
