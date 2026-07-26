# CHANGELOG v220 — Sprint 2.22.0b.149 «الوسيط الأعمى عن المساحة في الأراضي»

**Engine:** `thammen-sprint2p22p0b149-land-size-aware-fallback` · **SPRINT_TAG** `2.22.0b.149`
**Date:** 2026-07-26 · **Class:** 🔴 **Gate-2 VALUE-AFFECTING** (raw_land, empty-bracket subjects only)
**Files:** `evaluate_property.py` (+41/−0) · `evaluate_unified.py` (+13/−3, incl. the 2 version lines)
· `test_sprint_2_22_0b149.py` (new) · `test_sprint_2_22_0b148.py` (R6 re-point)
**UNTOUCHED (git-confirmed):** `api.py` · `index.html` → **R14 N/A by construction** (§20.18 / b59 / b139 precedent)

---

## 1. Why this matters

A land subject whose **size bracket has no registered sale** was valued at the area's
**median SALE PRICE** — a size-blind number dominated by the common 400–900 m² plots —
and that number became the headline.

Measured live on b147, **PIN 70312306 (سميسمة/الظعاين, plot 1500 m²)**:

| | value | ر.ق/قدم² |
|---|---|---|
| shown (b147) | **1,500,000** | **93** |
| the same pool's ppm² median × the plot | **4,681,500** | **290** (p75 = 311, max = 327) |

The owner of a 1500 m² plot was shown roughly **one third** of what his own evidence implies.

**It also split the basis of the displayed range.** The endpoints already used
`plot × category ppm² quartiles` (size-aware) while the headline read the blind total, so:
- ceiling 5,000,000 = ppm²-p75 × 1500 — size-aware,
- floor (pre-clamp) 4,255,500 = ppm²-p25 × 1500 → **greater than the headline = an inverted range**,
- the **b59 clamp** then dragged `low` down onto 1,500,000 — **masking the contradiction, not fixing it.**

## 2. Root cause

`evaluate_property.apply_moj_strategy` — the empty-bracket fallback:

```python
else:  # Fall back to overall category
    per_m2      = cat_data['price_per_m2']['median']   # size-normalised
    total_median = cat_data['total_price']['median']   # ← SIZE-BLIND, and this is what the headline reads
```

`evaluate_unified._select_primary_comparison` (Case 1, `:1393`) then does
`bracket_value = fair_price_total or moj_median_total` for the **value**, while taking
`low`/`high` from `estimated_value_*` — which the same function had already computed
**size-aware** (`plot_area × cat ppm² quartiles`). `estimated_value_median` was likewise
already correct and simply unused.

This also violated **our own Rule E3 constraint 7** (like-for-like unit of comparison,
normalised for size bracket *before* entering the calculation): a raw sale price is not
size-normalised.

## 3. What this patch does

1. **Size-aware fallback total (LAND).** In the empty-bracket branch, when
   `moj_cat == 'land'`: `total_median = plot_area_m2 × per_m2`. The headline now shares
   **one basis** with its own range and equals `estimated_value_median` exactly, so
   `low ≤ value ≤ high` holds **without** the b59 clamp.
2. **`MoJValuation.bracket_fallback`** (new, default `False`) — an explicit signal that the
   subject's size bracket was empty.
3. **Source honesty (JSON surface).** Case 1's `source_ar` no longer claims
   «وسيط N معاملة **في نفس الشريحة** والمنطقة» when the bracket was empty; it now states
   «وسيط سعر المتر في المنطقة (N معاملة) مطبَّقاً على مساحة العقار — لا صفقات مسجَّلة في شريحة مساحته».
   (`valuation.source_ar` has **no render site today** — measured, b139 dead-field discipline —
   so this is a payload-correctness fix, not a UI change.)

### Scope: LAND ONLY — measured, not preferred
The villa pool has the **same** defect (**95 of 288** (area,bracket) probes fall back, up to
**7.07×**). It is deliberately **not** fixed here: land is market-only (b20 emits
DRC ≡ land value), so the land fix is self-contained, whereas a villa market median feeds the
**b20 leadership gate + the E25 rail** and needs its own signed blast-radius. Deferred, not ignored (#42).

## 4. Verification — empirical evidence

### 4.1 Blast radius (real `moj_weekly.csv`, 24-month window, residential-filtered)
**41 of 112** land areas (37%) have **no** registered 1500+ sale → a 1500 m² subject there hits
the fallback. All 41 move **upward** (the fix removes an understatement); median **1.68×**,
range **1.16×–8.43×**. Full table: `docs/GATE2_b149_land_size_aware_blast_radius.md`.

### 4.2 Is `ppm² × area` defensible for big plots? (the RICS question — measured)
- **Per-area, against the nearest big-plot evidence:** across the 14 affected areas that *do*
  have a populated 900–1500 bracket, `ppm²(900-1500) ÷ ppm²(category)` = **0.96 median**
  (range 0.71–1.12) → the category ppm² is a **~4%-optimistic** proxy, versus today's
  **−50% to −70%** understatement.
- **National size gradient (24mo, residential):** 0-400 3,084 · 400-600 3,196 · 600-900 2,833 ·
  900-1500 2,792 · **1500+ 2,528 (0.79× the 400-600)** — a mild gradient, not a 3× cliff.

### 4.3 Byte-identity controls (real data)
| control | result |
|---|---|
| land fixture **الوعب 1219 m²** (b118, 5.7M) | bracket populated → **byte-identical** (5,326,000) |
| land fixture **الخور 900 m²** (1.2M) | bracket populated → **byte-identical** (2,195,266) |
| **سميسمة 500 m²** (same area, populated bracket) | **byte-identical** (1,406,000) |
| villa fixtures **مريخ 613 · المعمورة 652 · المعراض 900 · بو هامور 450** | **byte-identical** (5,100,000 / 3,741,176 / 2,432,778 / 2,357,895) |
| villa **المطار 2000 m²** (empty bracket, deferred) | flag fires, value **byte-identical** → scope discipline OK |

### 4.4 Gates
- `py_compile` (evaluate_property / evaluate_unified / api) **OK**
- isolated `test_sprint_2_22_0b149.py` **37/37** (E14 — real `apply_moj_strategy` +
  real `_select_primary_comparison` + the real MoJ CSV pool)
- DoD aggregator **395/395 ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45**
- broad walk **201/201 ALL FILES GREEN** (249.9s)
- **1 R6/Lesson-2 re-point:** `test_sprint_2_22_0b148.py` V4 pinned its own exact version
  (`SPRINT_TAG == '2.22.0b.148'`) → version-agnostic FORMAT check. Test-only; b148 **47/47**;
  **zero value/security/methodology/compliance assertion weakened.**
- **R14 N/A by construction** — `index.html` + `api.py` git-confirmed unchanged; the payload
  shape is unchanged (same fields, corrected number).

### 4.5 Personas (standing PO directive)
- **RICS valuer — APPROVE with a documented residual.** `ppm² × area` is the correct unit of
  comparison (VPS 3 / IVS 103; IVS 104 data quality) and restores compliance with our own
  E3-7. Residual: no explicit size-gradient adjustment (national 1500+ = 0.79×); measured
  per-area proxy error is only −4%, and VPGA-10 uncertainty is carried by the range.
- **Lawyer — APPROVE.** Correcting a systematic 1.16×–8.43× **under**-statement reduces
  exposure (an owner could act on a 3×-low figure); dropping the false «نفس الشريحة» claim
  raises defensibility. No disclaimer weakened; «ليس تقييماً معتمداً» + range + confidence pill intact.
- **Linguist — APPROVE** (one note applied: «لـ26 معاملة» → «(26 معاملة)» for فصحى flow).

## 5. Deployment

```
git push origin master
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
```
Ships together with the already-verified, not-yet-deployed **b148**.

## 6. Post-deploy verification

`/api/health` → `3.1.0-sprint2.22.0b.149`. Then (browser-UA, #61; body from a file, #62):
- **the reported case** `{"pin":"70312306"}` → amount ≈ **4.7M** (was 1.5M), and `low ≤ amount ≤ high`
  with all three on one basis.
- **land controls** `{"pin":"55010236"}` → **5,700,000** unchanged · الخور PIN → **1.2M** unchanged.
- **the 5-fixture villa gate** → byte-identical to v311 (54/541/6 **2,400,000** cost_led ·
  56/647/6 **3,800,000** · 55/296/13 **2,600,000** · 56/565/21 **2,400,000** · 52/903/90 refusal).
- **b148** (rides along) → refusal carries `note_en` + `options_en`; matched carries `window_used_en`.

## 7. What is NOT in this patch

- **The villa empty-bracket fallback** (95 probes, up to 7.07×) — needs a b20-leadership +
  E25-rail blast-radius; its own signed sprint.
- **A size-gradient (0.79×) adjustment** — a separate calibration question; note that the
  project already measured within-bracket size as a weak predictor (R²≈0.05, Sprint 2.20).
- **The confidence tier on a fallback.** The pill can still read «شواهد كافية» when the
  *category* n ≥ 20 although the subject's own bracket is empty. Basis validity is measured
  (−4%) and the source line now discloses it, but whether an out-of-bracket subject should
  cap at «إرشادي» is a signed copy/tier decision → deferred, flagged by the lawyer persona.
- Any frontend change (`index.html` untouched) and any villa/apartment/refusal behaviour.
