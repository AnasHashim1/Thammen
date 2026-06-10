# CHANGELOG v99 — Sprint 2.22.0b.16 — B-2 EARLY slice: V001-anchored old-stock central re-anchor (n=1, disclosed)

**Engine:** `thammen-sprint2p22p0b16-b2-early-oldstock-reanchor` · **SPRINT_TAG** `2.22.0b.16` ·
**api/health** `3.1.0-sprint2.22.0b.16` · **Files:** `evaluate_unified.py`, `evaluate_property.py`,
`moj_reference.py`, `index.html` (2 note-renderer lines), `test_sprint_2_22_0b16.py` (new) ·
**Baseline:** b15 / Heroku v184 · **Date:** 2026-06-10 · **🔴 Gate-2 VALUE-AFFECTING — SIGNED BY
DELEGATION** (brief `docs/BRIEF_Sprint2p22p0b16_B2_early_slice_SIGNED.md`; PO: «دعنا نبني على تقييم
المعمورة… ثم نعدّل مستقبلاً») · **Gate-1: deploy-on-green AFTER the Phase-0 HALT band passed**
(`docs/PHASE0_b16_bakeoff.md` — PASS).

---

## 1. Why this matters

Old villas in stratum-mismatched comparable pools carry a thin median driven by a DOMINANT premium
stratum — Marikh 54/541/6 (plain ~20y villa) prints a **5.4M** central because 51.7% of its pool is
«فاخر / حديث البناء». b11 (v180) honestly re-anchored the RANGE down to the cost floor but — by design —
left the central UN-led («no invented central»). b13's trim leads the central only with a USER actual age
(dormant on live no-age traffic). **This slice re-anchors the CENTRAL itself on the Marikh class**, using
the one certified appraisal we hold (V001/TD-93317 — our DRC reproduces the valuer to ~1%) + the FULL
Ministry-of-Justice window, **with the n=1 calibration disclosed verbatim** and a self-supersession ladder
as GT arrives (the B-2 n≥20 park is lifted for THIS disclosed early slice only, per the signed brief §0.4:
n gates the *label*, not the shipping).

## 2. The Phase-0 BAKE-OFF decided the mechanism (no pre-pick)

`docs/PHASE0_b16_bakeoff.md` measured M1-M4 on Marikh + V001 + 3 control anchors + **8 discovered old
villas** (QARS subtype-1, zones 51-55, survey ≤2012). Decisive findings:
- **M1 estimator disambiguated:** the brief's cited «≈517/ft²» is the **§20.10.1 estimator** — the
  FULL-window **ppm² median over the subject GEO bracket [plot×0.8, plot×1.2]** (measured on Marikh:
  **5,567/m² ≈ 517/ft² exact, n=51** → 3,412,571). The size-bracket total-price variant (5.0M, n=22) is
  distorted by the same premium stratum the slice corrects for — rejected.
- **Winner = M4** (the brief's suspected winner): central = min(max(M3 system-age DRC cost, M1c/M2), thin
  median); range = [max(land_floor, cost) … thin median].
- **Materiality T = 20%** (Phase-0's to set): anchored on the project's own clean-stock asking-premium
  ceiling (8–20%, Empirical_Findings §3). Marikh margin +58.2% → fires; **V001 +15.2% → ABSTAINS**
  (converged — the §1 honesty frame: V001's old-luxury premium ≈ 0; its 3.8M already sits in the band;
  the mechanism still reproduces the valuer's 3.6M in the table: M4(V001)=3.30M, M1a(V001)=3.60M).
- **HALT band (§4, hard Gate-1): PASS** — Marikh 3.4M ∈ [2.8M, 3.6M]; V001 3.8M ∈ [3.3M, 3.9M]; the
  non-old anchors + refusal byte-identical; **0/8 spurious firings** on the discovered cohort.
- **Premise resolution (documented §3):** «NOT b11-reanchor zones already leading» = zones whose CENTRAL
  is already led (income_led / b13-trim). b11 leaves the central un-led → this slice UPGRADES it on the
  stratum-mismatch subset and INHERITS b11's cost floor as its range-low (the signed band requires this
  reading — otherwise Marikh's central could never reach [2.8M, 3.6M]).

## 3. What this patch does

- **`moj_reference.subject_geo_full_ppm2(rows, area, plot_area_m2)`** (new, pure): the M1c estimator with
  the SAME villa-pool filters as `build_reference` (a18 sibling key + A2 built-type + A1 usage); returns
  None below n=5 (cite-n) → the re-anchor abstains.
- **`evaluate_property.py`**: threads it additively as `moj_ref_dict['subject_geo_full']` right after
  `build_reference` (Step 2) on the EFFECTIVE plot area (multi-QARS share — set at line ~1470 before this
  site) — the a13/a14 additive-threading precedent; reaches `evaluate_unified` via `ev.moj_reference`.
- **`evaluate_unified.py`**: new pure **`_old_stock_reanchor`** + constants (T=0.20 · dominant ∈
  {luxury_new, modern_stock} share ≥40 · M2 stratum-precedence at n≥10 · the verbatim signed label).
  Fires iff villa/house · thin/widened/widened_indicative · NOT dispersion-gated · OLD (age ≥10 or
  `vintage_capped`, E24) · NO user luxury/new/renovated · over-anchored (land < market) · basis exists ·
  margin > 20%. **Emission** (new `elif _osr` branch): the re-anchored central LEADS
  (`old_stock_reanchor.status='old_stock_reanchor_indicative'`), range = [max(land, cost) … thin median],
  `range_is_headline`, **MUC high**, verbatim label + «وسيط العيّنة الخام — مدفوع بطبقة فاخرة مسيطرة
  ({share}%)» + basis n. **Precedence:** `income_led > b13 cost_trim > THIS > b11 cost_reanchor
  (floor-only, now gated `and not _osr`) > widen_down`. **ISS-A07 coherence:** the branch RECOMPUTES
  `value_decomposition` + the B-1 `value_floor` on the new central and re-runs the b14
  `_reconcile_decomposition_narrative` post-pass (measured: land 1,851,260 + implied 1,548,740 =
  3,400,000 exactly).
- **Supersession ladder (§4, documented in-code):** GT intakes log `engine_estimate_at_intake`
  (GT_INTAKE_KIT_v1 §3 — manual channel) → matching-stratum n≥10 → M2 takes precedence automatically
  (wired) → n≥20 → the «indicative» label upgrades (a FUTURE signed-copy step, not invented here).
- **`index.html`** (2 lines, TIER-1): renders `v.old_stock_reanchor.note_ar` (the §4-mandated visible
  muted disclosure) + `v.cost_triangulation.note_ar` — the latter retroactively surfaces the b11/b13
  signed notes that were JSON-only until now (measured: grep `cost_triangulation` in index.html = 0
  pre-b16).

## 4. Verification — empirical evidence

- py_compile 3/3. Isolated `test_sprint_2_22_0b16.py` **38/38** (firing matrix + abstentions incl. the
  V001-shaped convergence + exact-20% boundary + rails + M2 ladder + purity + verbatim copy + REAL-CSV
  M1c reproduction (resolved-area path) + threading/precedence/UI pins). Sibling zone suites: b11
  **52/52** · b13 **37/37** · b15 **49/49** (after relaxing b15's own exact-version pin — the R6/Lesson-2
  anti-pattern, caught by the b16 bump).
- DoD: aggregator **392/392 (ALL COUNTS MATCH)** · security **15/15** · surface-honesty **45/45** ·
  broad auto-walk **85/85** (84→85, + the new test).
- **Local E2E (real engine, live GIS) — the expected-moves table EXACT:** Marikh 54/541/6 →
  `old_stock_reanchor_indicative` **amount 3,400,000**, range **[2,400,000 … 5,400,000]**, basis geo_full
  ppm²=5,567 n=51, margin 59.2%, dom=luxury_new 51.7%, MUC high, decomposition coherent; V001 3.8M /
  Abu Hamour 2.4M / Maraad 2.6M / Apt refusal — **byte-identical, no osr leak**.
- **R14 Chromium 390×844 (EXECUTED):** the OSR note renders in TIER-1 (outside accordions), «وسيط العيّنة
  الخام» visible, central 3.4M, MUC chip «مرتفع», note right-edge 350<390, no overflow, **0 console errors**.

## 5. Deployment

```
heroku auth:whoami
git add evaluate_unified.py evaluate_property.py moj_reference.py index.html test_sprint_2_22_0b16.py CHANGELOG_v99.md
git commit -m "Sprint 2.22.0b.16: B-2 early slice — V001-anchored old-stock central re-anchor (n=1 disclosed, VALUE-AFFECTING)"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```

## 6. Verification curl (post-deploy — the same table LIVE)

```
curl -s https://thammen.qa/api/health
curl -s -A "Mozilla/5.0 ... Chrome/120" -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" -d "{\"zone\":54,\"street\":541,\"building\":6}"
```
Expect: health b16; **Marikh amount 3,400,000 + old_stock_reanchor.status present + range [2.4M, 5.4M]**;
56/565/21 = 2.4M · 56/647/6 = 3.8M · 55/296/13 = 2.6M · 52/903/90 = refusal (byte-identical).

## 7. Honest residual (state verbatim per the brief §5)

**Calibration = one certified appraisal (V001) + the full-window MoJ pool; the label says so verbatim;
the GT kit (D-3) is the tightening channel — target ≥8 luxury_new + ≥6 old-plain sales + ≥6 valuer
reports.** The slice fires only where the strata panel resolves a premium-dominant stratum (0/8 of the
random old-villa cohort) — surgical by design, self-superseding as GT arrives.

## 8. What's NOT in this patch (scope boundary)

The new-stock UNDER-anchor (B-2-proper, needs luxury_new GT — E25) · clean-bracket paths · apartments ·
the report slice (b17) · the n≥20 label-upgrade WORDING (future signed copy) · the pre-existing b11
low>high range inversion on `primary.high < cost` subjects (observed on 54/788/10 + 55/1056/60 — deferred
micro-fix, Rule #42; b16's own emissions are immune) · recomputing the decomposition on the income_led /
b13-trim branches (pre-existing sibling gap; both are input-gated → no live exposure; logged).
