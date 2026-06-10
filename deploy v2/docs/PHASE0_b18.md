# PHASE-0 — Sprint 2.22.0b.18 (AGE-BASIS directive + LUXURY-EXIT fix + TD-93317 recalibration) — measured✓

> Per the signed b18 directive (§A–§E, Anas 2026-06-10). READ-ONLY recon on the real engine
> (`.b18_recon.py`, live GIS, baseline b17/v186). Date: 2026-06-10. **VERDICT: BUILD (ii)** —
> all three premises verified; mechanism (i) rejected on the monotonicity rail, exactly as §C predicted.

## §1 — Today's luxury path (the §A2 premise — VERIFIED live-local)

| case | amount | low | high | leads | note |
|---|---|---|---|---|---|
| Marikh 54/541/6 bare | **3,400,000** | 2.4M | 5.4M | `old_stock_reanchor_indicative` | the b16 plain lead |
| Marikh + `is_luxury` | **5,400,000** | 2.7M | 5.5M | `cost_reanchor_down` (b11) | **THE JUMP** — OSR abstains on `user_premium` → the central reverts to the raw thin median (the lux-RCN cost only raises the b11 floor to 2.7M) |
| V001 bare | 3,800,000 | 2.5M | 3.8M | widened (OSR margin 15.2% < 20 → abstain) | — |
| V001 +25+lux+exc | **3,600,000** | 3.6M | 3.7M | `cost_trim_convergent` (b13) | the user-age trim LEADS today → §A1 demotes it to the sensitivity line |

System ages (b9 floors): Marikh 17 · V001 17 · both `vintage_capped` (E24).

## §2 — TD-93317 sheet reproduction (§B mandatory check — PASS)

- **Land basis:** engine `value_floor` = **2,456,736** vs the bank's 652 m² × 350 QAR/ft² = **2,456,345**
  → **+0.016%**. **Recommendation: the DRC family keeps the engine's MoJ-derived land floor** (market-
  sourced, self-updating, reproduces the certified valuer to 2 bp; no hardcoded ft² rate).
- **Retention:** `_cost_retention(18,'high')` = **0.64** = raw 1−18/50 (bank's net 1,900/3,000 ≈ 0.633).
- **BUA:** b10 footprint 391 × built-ratio 0.77 × 2 floors = **602.14** ≈ the sheet's 602 m².
- **Assembly at the sheet's SYSTEM age (18, RAW):** 2,456,736 + 3,000×0.64×602.14 = **3,612,845 =
  +0.35% vs 3,600,145 → WITHIN ±1% ✓** (the mandated reproduction). At our live b9 floor (17, raw):
  +1.36% — the floor reads ~1y younger than the bank's «نحو 18» (E24 floor semantics; conservative).
- **Decisive reconciliation finding:** the valuer prices on the **RAW documented age** — our
  condition-penalty assembly does NOT reproduce (cond=None → −7.68%; cond=excellent → +2.36%) →
  **the §C finish-delta must use RAW system-age retention** (no condition penalty in the delta term).
- **V001 finish re-tiers LUXURY→HIGH** (1,900 net ≈ RCN_high 3,000 × 0.64 — NOT 3,500): the b13
  "exact 3.6M match" at 25y+luxury was **compensating parameters** (3,500×0.50 ≈ 3,000×0.64) → docs
  errata at this sprint's close (PHASE0_age_gap_recon V001 row · §20.45/§20.47/E24 «actual ~25»
  mentions — the 2002 deed says «أرض فضاء» → age 25 was impossible; the bank used SYSTEM age 18).

## §3 — §C bake-off (Marikh, measured)

| mechanism | value | verdict |
|---|---|---|
| (i) pure lux-DRC lead: 1,851,260 + 3,500×0.66×478.94 | **2,957,611** | **< plain 3,412,571 → MONOTONICITY VIOLATION → REJECT** |
| (ii) plain + FINISH-DELTA: 3,412,571 + (3,500−2,200)×0.66×478.94 = +410,931 | **3,823,502** | ∈ **[3.4M, 4.2M]** ✓ · ≤ thin median 5.406M ✓ → **WINNER** |

ret_raw = `_cost_retention(17, lux-keyed)` = 0.66 (the 0.31 lux floor keys but does not bite at 17y).
Expected §D live: Marikh+lux → `_r100k(3,823,502)` = **3,800,000** ∈ band.

## §4 — Build map

A1: the `elif _ct_trim:` LEAD branch is REMOVED; `_ct_trim` (computed unchanged) attaches
`valuation.age_sensitivity` = «حساسية العمر: لو كان العمر الفعلي {N} سنة ≈ {value} ر.ق» (headline/MUC
untouched; b11 system floor + E24 cliff-flag untouched). A2: `_old_stock_reanchor` — `is_luxury` no
longer abstains (new/renovated still do); plain cand + margin gate UNCHANGED, then
`delta = (RCN_finish − RCN_ord) × _cost_retention(sys_age_RAW, finish) × BUA`, railed
max(plain, min(plain+delta, thin median)); no computable delta (no bua/age) → conservative abstain
(today's behavior). Case-A luxury line re-worded (evaluate_unified 1063 + 1542) to promise the delta
pricing, not the pool jump. index.html renders `age_sensitivity.note_ar` (screen-4 TIER-1 honesty
notes + the b17 report notes). §D bands = the hard Gate-1 gate.
