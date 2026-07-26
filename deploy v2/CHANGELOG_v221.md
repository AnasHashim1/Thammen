# CHANGELOG v221 — Sprint 2.22.0b.150 «فرع الرجوع في الفلل»

**Engine:** `thammen-sprint2p22p0b150-villa-size-aware-fallback` · **SPRINT_TAG** `2.22.0b.150`
**Date:** 2026-07-26 · **Class:** 🔴 **Gate-2 VALUE-AFFECTING, BIDIRECTIONAL — PO-signed**
**Files:** `evaluate_property.py` (the category gate dropped + rationale) · `evaluate_unified.py`
(2 version lines) · `test_sprint_2_22_0b150.py` (new) · `test_sprint_2_22_0b149.py` +
`test_sprint_2_22_0b102_land_residential.py` (R6 re-points)
**UNTOUCHED (git-confirmed):** `api.py` · `index.html` → **R14 N/A by construction**

---

## 1. Why this matters

b149 fixed the size-blind empty-bracket fallback for **LAND** and explicitly deferred the
**VILLA** pool pending its own blast-radius, because a villa market median feeds the b20
leadership gate + the E25 rail. b150 measured that radius and closes the sibling.

## 2. Root cause (identical to b149)

In `apply_moj_strategy`, when the subject's size bracket is EMPTY, the fallback took the
area's **median SALE PRICE** (`total_price.median`) — a size-blind figure — while the
displayed range endpoints already used the size-aware `plot × ppm² quartiles`.

## 3. What this patch does

Drops the `moj_cat == 'land'` gate so the size-aware basis (`plot_area × ppm² median`)
applies to **both** pools. One line; the rationale block documents the measured radius.

## 4. Verification — empirical evidence

### 4.1 Direction — BIDIRECTIONAL (95 affected (area,bracket) villa cells)
- **81 UP** — median 2.67×, max 7.07× (big subject in a small-plot pool: under-stated)
- **14 DOWN** — median 0.69×, min 0.06× (small subject in a big-plot pool: over-stated)

Both are the SAME defect. The downward side is a correction, not a regression: **جليعة**
carried a **61,800,000** category total median (from ONE sale) applied to a 750 m² villa →
the size-aware basis gives **3,776,250**.

**Downward exposure is thin:** **0 of 14** reach cat_n ≥ 20 (none can become a confident
Case-1 headline); only **3** reach n ≥ 5 (روضة الحمامة 15 · لوسيل 69 12 · مدينة الشمال 7),
where the headline is already `comparison_thin`/preliminary and heavily caveated. **23** of
the upward cells reach n ≥ 20.

### 4.2 Leadership consequences (the pure b20 gate — asserted E1–E9)
- the leader CHOICE is value-independent (RULE 1/2 gate on n + dispersion) — unchanged
- **market-led** → the headline follows the corrected median
- **cost_led** → headline **byte-identical**; only the muted market ceiling moves
- **e25_capped → cost_led** (upward): the headline becomes the **COST** — the E25 rail holds,
  the raw market figure is never adopted upward
- **cost_led → e25_capped** (downward): the headline drops to the corrected market figure,
  carrying `divergence` + `MUC ≥ high` — disclosed, not silent

### 4.3 Basis validity — BACK-TEST (the decisive evidence)
Every POPULATED (area, category, bracket) cell with n ≥ 5 was treated as if empty; the rule
was applied and compared to that cell's ACTUAL median. **The new basis wins 7 of 9 brackets.**

| bracket | OLD err | NEW err | |
|---|---|---|---|
| land 1500+ | 1.428 | **0.448** | **+69%** |
| villa 1500+ | 2.049 | **0.869** | +58% |
| villa 600-900 | 0.191 | **0.106** | +45% |
| land 900-1500 | 0.301 | **0.188** | +37% |
| villa 400-600 | 0.112 | **0.073** | +35% |
| land 400-600 | 0.150 | **0.104** | +30% |
| villa 0-400 | 0.288 | **0.272** | +5% |
| land 600-900 | **0.056** | 0.135 | OLD wins |
| villa 900-1500 | **0.227** | 0.347 | OLD wins |

The two OLD-wins cells are the **near-mode** brackets (the category median IS approximately
that bracket's median there) and are **populated by definition** — so the fallback never fires
in them. Where the fallback DOES fire (an empty bracket = the tail) the new basis wins decisively.

**Honest limit (disclosed, not solved):** for SMALL subjects (villa 0-400) the gain is only
+5% and the basis stays weak in absolute terms (median 0.76 → it under-states, because small
plots command a higher ppm² than the pool average).

### 4.4 Controls
- villa fixtures **مريخ 613 · المعمورة 652 · المعراض 900 · بو هامور 450** — byte-identical
- **local E2E on the live engine:** 56/565/21 → **2,400,000** [2.2M–2.6M] `matched` ·
  54/541/6 → **2,400,000** [2.4M–5.4M] `cost_led` — both BYTE-IDENTICAL
- land (b149) preserved: سميسمة 1500 still corrected

### 4.5 Gates
py_compile OK · isolated `test_sprint_2_22_0b150.py` **33/33** · aggregator **395/395 ALL
COUNTS MATCH** · security **16/16** · surface honesty **45/45** · broad walk **202/202 ALL
FILES GREEN**.

**2 R6 re-points:**
- `test_sprint_2_22_0b149.py` — its C-block asserted the villa did NOT move (b149 was
  land-only by design); b150 is the signed sibling that inverts that scope. b149's own LAND
  assertions untouched → **37/37**.
- `test_sprint_2_22_0b102_land_residential.py` — its المعراض probe uses plot **300**, whose
  villa 0-400 bracket is EMPTY in that area, so it lands on the corrected fallback:
  **2,572,445** (= 8,575 ر.ق/م² for a 300 m² villa) → **768,000**. **The probe INPUT was
  deliberately left unchanged** — moving it to a populated bracket would have hidden a real
  value movement. b102's own intent (the residential-usage filter left villa values untouched)
  is unaffected: the other three probes sit in populated brackets and stay byte-identical → **20/20**.

**Zero value/security/methodology/compliance assertion weakened.**

## 5. Deployment
```
git push origin master
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
```

## 6. Post-deploy verification
`/api/health` → `3.1.0-sprint2.22.0b.150`; the 5-fixture villa gate byte-identical to v312;
the b149 land case still corrected.

## 7. What is NOT in this patch
- **A size-gradient model.** The basis ignores that ppm² falls with plot size (national
  1500+ = 0.79× the 400-600). It is ~4% optimistic for big subjects and under-states small
  ones — the villa 0-400 weakness above. A calibrated gradient is a separate sprint (note
  Sprint 2.20 measured *within-bracket* size as a weak predictor, R²≈0.05).
- **The confidence tier on a fallback** — the pill can still read «شواهد كافية» when the
  category n ≥ 20 while the subject's own bracket is empty (lawyer-flagged, signed copy decision).
- **R7 condition/built-type blindness (B-2)** — the largest remaining accuracy gap; data-gated
  on documented GT (n ≥ 20), not code-gated.
- Any frontend change; any apartment/tower/refusal behaviour.
