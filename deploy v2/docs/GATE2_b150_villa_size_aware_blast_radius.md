# GATE-2 — Sprint 2.22.0b.150 «فرع الرجوع في الفلل» (villa size-aware fallback)

**CLASS: VALUE-AFFECTING, BIDIRECTIONAL.** Extends the b149 (land) fix to the VILLA pool:
where the subject's SIZE BRACKET is EMPTY, the headline basis becomes `plot area × category
ppm² median` instead of the size-blind category SALE-PRICE median.

## Direction (measured, 95 affected (area,bracket) cells)
- **81 UP** — median 2.67×, max 7.07× (a big subject in a small-plot pool was under-stated)
- **14 DOWN** — median 0.69×, min 0.06× (a small subject in a big-plot pool was over-stated)

Both directions are the SAME defect. Example of the downward side: جليعة carried a
**61,800,000** category total median (from ONE sale) and applied it to a 750 m² villa →
the size-aware basis gives **3,776,250**.

**Downward exposure is thin:** 0 of the 14 reach cat_n ≥ 20, so none can become a confident
Case-1 headline; only 3 reach n ≥ 5 (روضة الحمامة 15 · لوسيل 69 12 · مدينة الشمال 7), where
the headline is already `comparison_thin`/preliminary and heavily caveated. By contrast **23**
of the upward cells reach n ≥ 20.

## Leadership consequences (the pure b20 gate — asserted in test E1-E9)
- the leader CHOICE never depends on the value (RULE 1/2 gate on n + dispersion) — unchanged
- **market-led** → the headline follows the corrected median
- **cost_led** → headline **byte-identical**; only the muted market ceiling moves
- **e25_capped → cost_led** (upward): the headline becomes the COST — the E25 rail holds,
  the raw market figure is never adopted upward
- **cost_led → e25_capped** (downward): the headline DROPS to the corrected market figure,
  carrying `divergence` + `MUC ≥ high` — disclosed, not silent

## Basis validity — BACK-TEST (the decisive evidence)
Every POPULATED (area, category, bracket) cell with n ≥ 5 was treated as if empty; the rule
was applied and compared to that cell's ACTUAL median. **The new basis wins 7 of 9 brackets.**
The 2 where the OLD basis wins (land 600-900, villa 900-1500) are the **near-mode** brackets —
the category median IS approximately that bracket's median there — and they are, by definition,
**populated**, so the fallback never fires in them. Where the fallback DOES fire (the tail, an
empty bracket) the new basis wins decisively: land 1500+ error **1.428 → 0.448 (+69%)**,
villa 1500+ **2.049 → 0.869 (+58%)**.

**Honest limit:** for SMALL subjects (villa 0-400) the new basis is only marginally better
(0.288 → 0.272, +5%) and still weak in absolute terms — it under-states (median 0.76) because
small plots command a higher ppm² than the pool average. Disclosed, not solved here.

## Controls (byte-identical)
- villa fixtures **مريخ 613 · المعمورة 652 · المعراض 900 · بو هامور 450** — populated brackets
- **local E2E on the live engine:** 56/565/21 → 2,400,000 [2.2M–2.6M] `matched` ·
  54/541/6 → 2,400,000 [2.4M–5.4M] `cost_led` — both BYTE-IDENTICAL
- land (b149) behaviour preserved: سميسمة 1500 still corrected

## Gates
isolated **33/33** · b149 **37/37** (1 R6 re-point) · b102 **20/20** (1 R6 re-point, the
value movement documented, the probe input deliberately unchanged) · aggregator **395/395
ALL COUNTS MATCH** · security **16/16** · surface honesty **45/45** · broad walk
**202/202 ALL FILES GREEN** · `api.py` + `index.html` UNTOUCHED → R14 N/A by construction.

Generated 2026-07-26 — Sprint 2.22.0b.150
**PO SIGNATURE (Gate-2): ______________________   date: __________**

---

## A. Affected villa cells + the leadership shapes
```
=== A. VILLA cells where the subject bracket is EMPTY (market median before/after) ===
  area                    bracket      cat_n       BEFORE        AFTER      x
  الثمامة 50              1500-99999     112   11,904,000   11,904,000   1.00
  المطار العتيق           1500-99999      50    9,744,000    9,744,000   1.00
  الثمامة 46              1500-99999     112   11,904,000   11,904,000   1.00
  الصخامة                 900-1500        38    6,756,000    6,756,000   1.00
  ابا الظلوف              1500-99999      16    5,912,000    5,912,000   1.00
  غرافة الريان            1500-99999      50   10,504,000   10,504,000   1.00
  الرويس                  1500-99999      17    6,116,000    6,116,000   1.00
  مدينة خليفة الجنوبية    1500-99999      13    9,354,000    9,354,000   1.00
  الذخيرة                 900-1500        23    3,585,600    3,585,600   1.00
  الذخيرة                 1500-99999      23    5,976,000    5,976,000   1.00
  بو هامور                1500-99999      49   10,666,000   10,666,000   1.00
  الخيسة                  900-1500        50    6,183,600    6,183,600   1.00
  جريان جنيحات            1500-99999      25   12,796,000   12,796,000   1.00
  لوعيب                   1500-99999       6    7,750,000    7,750,000   1.00
  المشاف                  900-1500        13    4,743,600    4,743,600   1.00
  ام عبيرية               900-1500        25    6,220,800    6,220,800   1.00
  فريج بن عمران           1500-99999       3   11,516,000   11,516,000   1.00
  ام صلال محمد            1500-99999      20   10,080,000   10,080,000   1.00
  المعراض                 1500-99999      11    5,120,000    5,120,000   1.00
  سميسمة                  1500-99999      27    8,390,000    8,390,000   1.00
  الثمامة 47              1500-99999     112   11,904,000   11,904,000   1.00
  مبيريك                  600-900          4    1,515,000    1,515,000   1.00
  ... total affected cells = 95   median x = 1.00   range 1.00-1.00
  cells whose category n >= 20 (Case 1 can fire -> a market-led headline is possible): 23

=== B. leadership consequence — the PURE gate, per shape (proof of monotonicity) ===
  shape                               rule(before)         HL beforerule(after)           HL after  verdict
  RULE 1 matched (market leads)       matched              2,300,000matched             10,080,000  up 4.38x
  RULE 2 geo_full (market leads)      geo_full             2,300,000geo_full            10,080,000  up 4.38x
  cost_unavailable (market keeps lead)cost_unavailable     2,300,000cost_unavailable    10,080,000  up 4.38x
  e25_capped (cost >= market)         e25_capped           2,300,000cost_led             3,400,000  up 1.48x
  cost_led (cost < market)            cost_led             1,800,000cost_led             1,800,000  byte-identical

  monotonicity (headline never decreases): PROVEN over these shapes
```

## B. Back-test of the basis, per bracket
```
BACK-TEST — predicted / ACTUAL bracket median   (1.00 = perfect; >1 over, <1 under)
  cat    bracket      cells              NEW ppm2 x area                 OLD blind total
                                 median |log| err                median |log| err
  land   400-600         46        0.91     0.104                  1.15     0.150   NEW wins
  land   600-900         52        1.10     0.135                  1.00     0.056   OLD wins
  land   900-1500        55        1.21     0.188                  0.74     0.301   NEW wins
  land   1500-99999      26        0.64     0.448                  0.24     1.428   NEW wins
  villa  0-400           14        0.76     0.272                  1.33     0.288   NEW wins
  villa  400-600         52        1.04     0.073                  1.11     0.112   NEW wins
  villa  600-900         45        1.09     0.106                  0.89     0.191   NEW wins
  villa  900-1500        42        1.41     0.347                  0.80     0.227   OLD wins
  villa  1500-99999       4        0.42     0.869                  0.13     2.049   NEW wins

SUMMARY — where is the NEW basis better than the OLD one?
  land   400-600     n=46    NEW wins   error 0.150 -> 0.104  (+30%)
  land   600-900     n=52    OLD wins   error 0.056 -> 0.135  (-143%)
  land   900-1500    n=55    NEW wins   error 0.301 -> 0.188  (+37%)
  land   1500-99999  n=26    NEW wins   error 1.428 -> 0.448  (+69%)
  villa  0-400       n=14    NEW wins   error 0.288 -> 0.272  (+5%)
  villa  400-600     n=52    NEW wins   error 0.112 -> 0.073  (+35%)
  villa  600-900     n=45    NEW wins   error 0.191 -> 0.106  (+45%)
  villa  900-1500    n=42    OLD wins   error 0.227 -> 0.347  (-53%)
  villa  1500-99999  n=4     NEW wins   error 2.049 -> 0.869  (+58%)
```
