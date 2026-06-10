# PHASE-0 RECON — Sprint 2.22.0b.14 (decomposition coherence + report-voice) — ISS-A07

> **Baseline:** b13/v182 · live probe Marikh **54/541/6** buyer (browser-UA curl, HTTP 200 @15.7s, 2026-06-10).
> **Verdict:** ✅ core premises HOLD → BUILD. **1 premise CORRECTION** (no basis divergence — brief typo) + **1 architecture re-shape** (post-pass, not signature-thread). No full HALT.

## 1 — Site map (all 6 located, measured✓)

| # | Concern | Site | Note |
|---|---|---|---|
| 1 | Decomposition narrative (the §2 core) | `evaluate_unified.py:1452-1456` (`_decompose_value`, `building_dominant` branch) | «البناء يساهم بنسبة عالية (X%) … يتسق مع بناء جديد أو فاخر أو ذو BUA كبيرة.» — the Case-B line, fired for the 17y Marikh subject. |
| 2 | 10-Year / stratum panel | `evaluate_unified.py:4249` (`regime_label_ar`) + `stock_strata.py:84/91/104` (`land_priced` «بسعر الأرض» / «نمط سوقي: غلبة قيمة الأرض…») + frontend panel `index.html:1344` («قاعدة الـ 10 سنوات») | The cross-line target. |
| 3 | Location-feature «بناء قديم نسبياً» | `property_factors.py:468` (`building_age` factor `label_ar`) | The «✗ بناء قديم نسبياً» mark the narrative contradicts. |
| 4 | Service-charge MUC factor (leak #1) | `material_uncertainty.py:372` (`'رسوم الخدمات تقديرية — ليست مُتحقَّقة لهذا المبنى'`, in the **building** branch, score 1) | Fires for a standalone villa (no service charges). |
| 5 | Cap-rate label (leak #2) | `output_briefs.py:167` (`"…لنفس المنطقة والشريحة —"`) | The brief-section[3] body claims same-bracket; `cap_rate_provenance.method_ar` ALREADY discloses the **borrow from 400-600** correctly → the leak is the brief body only. |
| 6 | Ad-empty-state (leak #3) | `index.html:1790` (`'…في وصف الإعلان (لم يُقدَّم وصف).'`) — **frontend** empty-state | Source confirmed = frontend (NOT backend copy); `reasoning_trace.py:342-360` only emits when flags EXIST. |

## 2 — Live evidence (Marikh 54/541/6, b13/v182)

```
amount 5,400,000 · low 2,400,000 (b11 cost_reanchor floor) · high 5,500,000 · method comparison_thin
value_decomposition.land.estimated_qar   = 1,851,260 (n=34, 24mo, reliable)
value_decomposition.building_implied.qar = 3,548,740 · as_pct_of_total = 65.7 · status building_dominant
  → interpretation_ar = «…يتسق مع بناء جديد أو فاخر أو ذو BUA كبيرة.»   ← the contradiction
stock_strata.dominant_stratum.label_ar   = «فاخر / حديث البناء» (luxury_new)
material_uncertainty.factors[4]           = «رسوم الخدمات تقديرية — ليست مُتحقَّقة لهذا المبنى»   ← leak #1
cap_rate_provenance.method_ar             = «…معدل مُستعار من شريحة 400-600 م²…» (CORRECT borrow disclosure)
brief.sections[3].content.body_ar         = «…لنفس المنطقة والشريحة — عيّنة n=46…»                 ← leak #2 (claims same bracket)
```

## 3 — 🔴 PREMISE CORRECTION (HALT-and-report, §5) — the basis divergence does NOT exist

The brief §2 states: *«live shows 1,851,260 + 3,448,740 = 5,300,000 vs headline 5,400,000 — Phase-0 finds the basis divergence and unifies; the % recomputes»*.

**Measured live:** building_implied = **3,548,740** (not 3,448,740) → 1,851,260 + 3,548,740 = **5,400,000 = the headline EXACTLY.** The decomposition basis **already equals the page central**; there is **no 5.3M/5.4M divergence** (the brief's `3,448,740`/`5,300,000` is a 100,000 transcription typo of `3,548,740`/`5,400,000`).

**Consequence (per §4):** the "basis unification" sub-fix is a confirmed **NO-OP**; `as_pct_of_total` stays **65.7** byte-identical — there is **nothing to report at Gate-3** on that axis, and the whitelist is *cleaner* (the implied-building % is now in the **must-stay-byte-identical** set, not the may-change set). **The core sprint (narrative + 3 leaks) is UNAFFECTED and proceeds.**

## 4 — 🔧 ARCHITECTURE re-shape (vs the brief's implicit thread-into-`_decompose_value`)

`_decompose_value` (sig: `valuation_amount, plot_area_m2, bua_m2, moj_ref_dict`) is called at **`:4493`**, but `output['property_basis']` (`:5510`, carries `building_age_estimate.age_basis=vintage_capped`) and `output['stock_strata']` (`:5593`, carries `dominant_stratum`) are attached **AFTER** it. So the Case A/B/C signals are NOT available inside `_decompose_value`.

**Decision:** keep `_decompose_value` UNTOUCHED (it produces the default building_dominant line); add a pure **post-pass `_reconcile_decomposition_narrative(output, ev)`** near the end of `_build_unified_output` (after `:5593`) that — when `value_decomposition.building_implied.status == 'building_dominant'` AND asset ∈ {standalone_villa, house, villa} — selects Case A/B/C from `stock_strata.dominant_stratum` + `property_basis.building_age_estimate.age_basis` (+ sys age) + `ev` user inputs (`is_luxury` / `condition` / new/renovated) and **overwrites only `interpretation_ar`** (+ adds the decomposition↔10-Year cross-line). **Value-invariant — text only.** Lower risk than reordering the 4.5k-line builder.

## 5 — §4 whitelist → exact change sites (text-only)

| May change (TEXT) | Site |
|---|---|
| decomposition narrative + its cross-line | `evaluate_unified.py` new `_reconcile_decomposition_narrative` (overwrites `value_decomposition.building_implied.interpretation_ar`) |
| 10-Year panel cross-line | same post-pass (a one-line note onto the stratum/regime surface) |
| MUC service-charge factor line | `material_uncertainty.py:372` (villa/house → soften/drop) |
| cap-rate source label | `output_briefs.py:167` (disclose the borrow, matching `cap_rate_provenance`) |
| ad-empty-state line | `index.html:1790` (frontend) |

**Must stay byte-identical (asserted by the test):** `amount`, `range_*`, `method`, `value_floor`, all floors/levers, strata numbers, cap-rate VALUE (5.16%/n=46), land value (1,851,260), **implied-building VALUE *and its 65.7%*** (no basis change), all 4 anchors + V001 numeric fields.

## 6 — Build plan (per §6 DoD)

1. `_reconcile_decomposition_narrative(output, ev)` (Case A/B/C verbatim per §2) + call after `:5593`.
2. `material_uncertainty.py` villa/house service-charge softening (leak #1).
3. `output_briefs.py:167` borrow disclosure (leak #2) — align with the already-correct `cap_rate_provenance`.
4. `index.html:1790` ad-empty-state copy (leak #3).
5. isolated ≥20 (A/B/C table + Marikh→Case-A + leak fixes + the §4 byte-identity contract).
6. DoD aggregator 392 / security 15 / surface 45 / broad 82; local E2E (4 anchors + V001 numeric-identical, Marikh narrative = Case-A verbatim); R14 Chromium 390×844.
7. Deploy: `heroku auth:whoami` → subtree push (or hand to Anas, §20.45) → live smoke → CHANGELOG_v97 + Session_Log §20.48 + ENGINE→b14.

**NOT in scope (§7):** any value/method change · two-values display (DEF-12) · strata thresholds · apartment surfaces.
