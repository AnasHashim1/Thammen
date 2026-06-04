# PHASE 0 — Sprint B-1 §5 Recon (condition / land-floor axis) — READ-ONLY

> **Status:** Phase-0 empirical recon for **Sprint B-1** (old-stock / condition honest surfacing).
> **READ-ONLY** — no source edits, no deploy, production byte-identical (Heroku **v159** / a20).
> Triggers **no gate**. Answers Q1–Q5 with measured numbers; **reports, does not fix.** Any edit
> needed = a scope line for the B-1 signed brief (flag-and-HOLD, #38).
> **Authored:** CC, 2026-06-04. **Handshake (Rule #57):** `/api/health` = engine
> `thammen-sprint2p22p0a20-rics-compliant-status-label`, version `3.1.0-sprint2.22.0a.20`, qars
> `healthy`, MoJ `155d` stale, `master == origin` (f73ef3d). **No drift.**
> **Method:** live `POST /api/evaluate` (browser-UA curl, Rule #61) on 11 addresses + code trace of
> `evaluate_unified._decompose_value` / `_stage1_dispersion_gate` / `_condition_note_applies`,
> `moj_reference.build_reference`, `stock_strata.compute_land_median`. Scratch: `.p0x.py`, `.r_*.json`
> (dot-prefixed → gitignored).

---

## TL;DR — verdicts

| Q | Verdict | One-line |
|---|---|---|
| **Q1** [BLOCKER] | 🟢 **available — with one carve-out** | The land floor **IS** surfaced today at `valuation.value_decomposition.land.estimated_qar` on bracket/widened/thin (reliable, n≥20). The "None" was a **wrong-field-path artifact** (queried a `cost`-keyed `land_value`, not `value_decomposition`). **Carve-out:** Patch C suppresses the **whole** decomposition when `land_value > comp value` — i.e. the **land-priced/old-stock case** (55/296/13: land 2,547/m² → floor **2.67M > 2.6M value**, measured✓), exactly where B-1 wants the floor. **B-1 = re-surface, recompute only for the Patch-C case.** |
| **Q2** [→D2] | 🟢 recommend gate (a) | Reuse the **existing a17/a19 `_condition_note_applies` scope** (villa/house + the 5 value-bearing comparison methods + amount present). Age-input-free (E22-safe), method-agnostic, ≈100% of valued villa lookups. |
| **Q3** [=B-0] | 🟢 **COVERED — no gap** | Every value-bearing villa surface discloses condition: non-gated → `condition_note_ar` (proven live ×5); dispersion-gated → `range_disclosure_ar` which explicitly says «لم يُؤكَّد بعد نوع بناء هذا العقار وحالته» (code-verified). **No B-0 bug** — confirms the proposer's same-day correction. |
| **Q4** [scope] | 🟢 **measured✓** | B-1 trigger ≈ **~100%** of valued villa lookups (a17/a19 scope, unconditional). Floor **suppressed by Patch-C in ~10.0% of valued villa cells / ~5.2% tx-weighted** (**0%** of reliable n≥20 cells) — **all large-plot old-stock** (900-1500+), the B-1 land-priced target cohort. E4 land_priced band (ratio<1.15) ≈ 26% cells / 13.5% tx. |
| **Q5** [land #] | 🟢 reconciled | **3,768** (n=20, `value_decomposition` ← `moj_reference`, **a18-aware**) vs **4,032** (n=13, `stock_strata.land_reference` ← `_norm` exact, **a18-NOT-applied**). Different modules, different area-pooling. **Use 3,768** for the floor (it's already the surfaced number). The 4,032/strata path is a **latent inconsistency** to flag — not B-1's job. |

---

## Live measurement table (6 resolved subjects + spread)

All via `POST https://thammen.qa/api/evaluate`, a20 / v159, 2026-06-04. `FLOOR` = `valuation.value_decomposition.land.estimated_qar`. `vd` = value_decomposition; `strata` = stock_strata.land_reference.

| PIN | district | plot m² | method | amount | low / high | **FLOOR present?** | FLOOR (QAR) | vd land ppm² (n) | strata ppm² (n, bracket) | cond. disclosure |
|---|---|---|---|---|---|---|---|---|---|---|
| **56/647/6** (V001) | المعمورة 56 | 652 | **comparison_widened** | 3,800,000 | 3.1M / 3.8M | ✅ **YES** | **2,456,736** | 3768 (20) | 4032 (13, area-wide) | `condition_note_ar` ✓ |
| 56/565/21 (anchor) | بو هامور | 450 | comparison_bracket | 2,400,000 | 2.2M / 2.6M | ✅ YES | 1,700,100 | 3778 (33) | 3875 (20, 400-600) | `condition_note_ar` ✓ |
| 56/650/4 | المعمورة 56 | 375 | comparison_bracket | 3,300,000 | 1.6M / 3.3M | ✅ YES | 1,413,000 | 3768 (20) | 4032 (13, area-wide) | `condition_note_ar` ✓ |
| 54/541/6 (Marikh) | امريخ الجنوبي | 613 | comparison_thin | 5,400,000 | 4.9M / 5.5M | ✅ YES | 3020 (34) → 1,851,260 | 3020 (34) | 3212 (18, 600-900) | `condition_note_ar` ✓ |
| **55/296/13** | المعراض | 1050 | comparison_thin | 2,600,000 | 2.0M / 2.6M | ❌ **NO (Patch C)** | — *(suppressed)* | — *(decomp None)* | 2607 (11, 900-1500) | `condition_note_ar` ✓ |
| 52/903/90 (refusal) | اللقطة | 467 | insufficient_data (apt) | None | — | N/A | — | — | — | absent (refusal) |

**Probe yield (Rule #36 honesty):** 11 addresses POSTed; **5 resolved to valued villas**, 1 apartment refusal, **5 QARS-empty** (`asset unknown / district None`, fast ~3s — blind Z/S/B rarely hits a surveyed villa). Only **1 live widened** resolved (المعمورة 600–900 is the thin bracket that widens; same district's 0–400 / 400–600 brackets stay `comparison_bracket`). A 2nd live widened was not hit blind — **but Q1 is method-independent by construction** (see below), so the widened path is proven by 56/647/6 + code generality.

---

## Q1 — Is the land FLOOR available on the widened (and thin) path today? [BLOCKER]

**Verdict: 🟢 YES on every villa comparison path — EXCEPT the Patch-C carve-out. B-1 re-surfaces an existing number; recompute is needed ONLY for the land-priced case.**

### 1a. The floor is present and reliable (not None)
The live field is **`valuation.value_decomposition.land`** (nested under `valuation`):
```
56/647/6 widened → land: { per_m2_qar 3768, n_transactions 20, window_months 24,
                           reliable true, confidence "reliable", estimated_qar 2456736,
                           plot_area_m2 652 }
```
Confirmed present + `reliable:true` on **widened (56/647/6), bracket (56/565/21, 56/650/4), thin (54/541/6)** — n = 20–34. The refusal (52/903/90) correctly has none.

### 1b. The "None" was a wrong-field-path artifact (same class as the B-0 miss)
The proposal cited `decomposition.land_value = None`. There is **no top-level `decomposition`** and **no `land_value`** on the live valuation. The only `land_value` keys in code are the **Cost-approach crosscheck**:
- `evaluate_unified.py:1324` `'land_value': getattr(rc, 'land_value', None)` (in `_build_cost_crosscheck`, `rc = ev.replacement_cost`)
- `evaluate_unified.py:4340` `'land_value': cost.get('land_value')`

For a **villa the Cost approach is not run** (`replacement_cost` is None / "cost is a reference, never primary for residential") → that `land_value` is legitimately None. The **real floor** lives at `value_decomposition.land.estimated_qar`. Same lesson as B-0: the field was there, the query path was wrong.

### 1c. The floor is METHOD-INDEPENDENT (code, not luck)
`_decompose_value(valuation_amount, plot_area_m2, bua_m2, moj_ref_dict)` (`evaluate_unified.py:1130`) receives the **same** `moj_ref_dict.categories.land` regardless of whether the headline came from bracket / widened / thin. The floor depends on **only** the MoJ land category + the subject plot — **not** the comparison method. So "available on the widened path" generalises from 56/647/6 + the 4 other paths to all villa comparison methods.

### 1d. THE CARVE-OUT (key scope finding) — Patch C suppresses the floor when land > value
`evaluate_unified.py:1204` (Sprint 2.18.1.1 Patch C):
```python
if land_value > valuation_amount:
    return None          # suppresses the ENTIRE value_decomposition block
```
`_decompose_value` returns None (whole block gone) when **any** of: no value / no plot / no `moj_ref` / `land_per_m2` ≤ 0 / `land_n < 3` / **`land_value > valuation_amount`**.

**Live proof — 55/296/13 (المعراض, plot 1050, value 2.6M):** `value_decomposition` is **absent**, yet it is a valued villa with land comps (strata found land n=11 @ 2607). The other None-triggers are excluded (value present, plot present, land comps exist) → **the only remaining trigger is Patch C**. Its `dominant_stratum = land_priced (62.5%)` — i.e. **the textbook old-stock case** (building barely credited, clears toward land).

**Confirmed offline against production `moj_reference.build_reference` (E14, measured✓):** المعراض `categories.land.price_per_m2.median` = **2,547/m²** (n=25, 36mo) → floor = 2,547 × 1050 = **2,674,350 > 2,600,000 → Patch-C TRIP = True**, definitively (the exact land number the live API hides when it suppresses the block). The **same** offline build reproduces Maamoura's land = **3,768 → 2,456,736**, **byte-identical to the live `value_decomposition.land`** — validating the floor source end-to-end.

> ⚠️ **This is the crux for B-1.** Patch C exists to kill the *negative-building* compound bug (51/835/17: land 218M vs total 6.8M). But it ALSO suppresses the **legitimate land floor** for ordinary **land-priced villas** — exactly the Maamoura-class case B-1 is built to serve. When the market clears toward land, the engine currently shows **no land number at all**.

**B-1 scope consequence (report, don't fix):** B-1 cannot simply "surface `value_decomposition.land`" — in the land-priced case it's absent. Options for the brief: **(i)** compute the land-floor number on its own (independent of `_decompose_value`, so Patch C's anti-negative-building guard is untouched) and surface it as the floor even when land ≥ value; **(ii)** keep `_decompose_value` for the building split but split out a always-available `land_floor` sub-number. Either is a small, presentation-scoped recompute — **flag for the brief**, do not build here.

---

## Q2 — What gate fires the surface with NO age input? [→ D2]

E22: building age is **not auto-detected** → any age-gated rule is **inert** on the default flow. Condition has **no input at all** until B-2. So the gate must key on what's available at evaluate time. Candidates + incidence:

| # | Candidate gate | Fires on | Incidence (villa lookups) | Assessment |
|---|---|---|---|---|
| **(a)** ⭐ | **villa/house + value-bearing comparison method + amount present** (= the existing `_condition_note_applies` scope: `comparison_{bracket, thin, widened, widened_indicative, preliminary}`) | every valued villa output | **≈100%** measured✓ (unconditional — condition never assessed) | **Cleanest.** Already live + proven (a17/a19). Age-free. Co-locates the land floor with the condition caveat that already fires. |
| (b) | `_stage1_dispersion_gate` (dispersed pools only) | dispersed bracket/widened | ~37–39% of villa **cells** (a13/a14 measured✓) | **Too narrow as sole gate** — would **miss 56/647/6 itself** (non-dispersed widened) and 56/565/21/V002/V003 (clean bracket, the under-anchor cases). |
| (c) | method label (widened/thin only) | widened + thin | minority of villa lookups | **Too narrow** — misses clean **bracket** (the V002/V003 +67% under-anchor + 56/650/4). |
| (d) | E4 stratum (`land_priced` etc.) | land_priced subset | strata n usually <5 (56/647/6 dominant n=4; 55/296/13 n=5) | **Unreliable** — strata cells are thin; not a robust trigger. Useful as a *signal within* the surface, not as the gate. |

**CC recommendation (NEUTRAL options above; #59):** **gate (a)** — reuse `_condition_note_applies`. Rationale: the land floor + the bidirectional condition disclosure are **the same honesty surface**; bolting B-1 onto the predicate that already governs the condition caveat makes B-1 and a17/a19 **one coherent surface**, inherits proven incidence + tests, and needs no new gate logic. (Stratum (d) can *enrich* the copy — e.g. "this area's villas tend to clear toward land" when `land_priced` dominates — but should not *gate*.)

---

## Q3 — Does dispersed-widened actually disclose condition, or slip through? [= B-0]

**Verdict: 🟢 COVERED — no gap. Confirms the proposer's same-day B-0 correction; B-0 is obsolete.**

Two complementary mechanisms in `_build_unified_output` (`evaluate_unified.py:4896–4956`), mutually exclusive via `gate.get('gated')`:

1. **NON-dispersed (gated=False, or thin/preliminary where the gate returns None)** → `_condition_note_applies` = True → attaches **`valuation.condition_note_ar`** (verbatim, live on 56/647/6 + all 5 villas):
   > «لم تُؤخذ حالة العقار (تجديد أو تهالك) في الحسبان. عقار في حالة أفضل من المتوسط قد يقع أعلى هذه النقطة، وعقار في حالة أدنى قد يقع تحتها.»

2. **DISPERSED (gated=True)** → `condition_note` is **excluded by design** (avoid duplication), and instead `range_is_headline=True` + **`valuation.range_disclosure_ar`** carries the condition wording (`evaluate_unified.py:4904–4909`, code-verified):
   > «النطاق المعروض هو التقدير الأصدق لهذا العقار في هذه المرحلة. الصفقات المقارنة المتاحة تشمل أنواع بناء وحالات متفاوتة (فيلا عادية، ملحق، بنتهاوس)، **ولم يُؤكَّد بعد نوع بناء هذا العقار وحالته** — لذلك القيمة المركزية إرشادية ضمن النطاق. تأكيد نوع البناء والحالة بالمعاينة الميدانية أو عبر الوسيط (المرحلة الثانية) يضيّق النطاق.»

The 5 value-bearing villa methods are exactly `_CONDITION_NOTE_METHODS`; the gated set (dispersed bracket/widened) is a subset that gets mechanism #2. **Union = every villa value-bearing surface discloses condition.** 56/647/6 is **non-dispersed widened** → mechanism #1 (condition_note present, observed live) — so the proposer's earlier "didn't attach on the widened path" was the extraction artifact (`valuation.condition_note_ar` vs top-level), now corrected.

> **Honest caveat (Rule #36):** none of the 6 live subjects this pass were **dispersion-GATED** (all `range_is_headline=None`), so mechanism #2 is **code-verified, not re-observed live** this pass (it was live-smoked in a14 §20.14). 54/541/6, once a gated widened, is now `comparison_thin` (n=15) post-a18, so it takes mechanism #1. **Fast-follow (optional):** a direct live hit on a dispersed bracket/widened cell (e.g. الغرافة/العب 600–900) to re-observe `range_disclosure_ar` end-to-end — not blocking.

---

## Q4 — Incidence in the beta cohort (villas + land) [scope]

- **B-1 surface trigger** under the recommended gate (a) = **the a17/a19 scope = every valued villa/house comparison output.** Incidence among villa lookups that return a value ≈ **~100%** (measured✓: the predicate is unconditional on condition, which is never assessed). The condition disclosure already fires there today.
- **Land-FLOOR sub-availability** within that = ~100% **minus** the **Patch-C share**. **Measured✓** — offline scan over **all valued villa cells in `moj_weekly.csv` via production `build_reference`** (ratio = villa_ppm² ÷ area land_ppm²; Patch-C trips when ratio < ~1.0):

  | villa cells (n≥5): **110 cells / 1,936 tx** | by cell | tx-weighted |
  |---|---|---|
  | **ratio < 1.00 — floor SUPPRESSED (Patch-C)** | **10.0%** | **5.2%** |
  | ratio < 1.15 — E4 land_priced band | 26.4% | 13.5% |
  | ratio ≥ 1.15 — floor present | 73.6% | 86.5% |
  | **reliable cells (n≥20): 25 cells** | **0% suppressed** | 0% |

  The suppressed cohort is **entirely large-plot old-stock** (900-1500 & 1500+): الوعب, المرخية, معيذر, لقطيفية, دحيل, عين خالد, المعراض, بو سدرة, حزم المرخية… all **n=5–18** (never reliable n≥20). So Patch-C suppression is **small in volume (~5% tx) but is exactly the land-priced cohort B-1 exists for** — not a rare edge.
- **Proxy note (honesty):** ratio<1.0 ≈ the Patch-C trip (`land_ppm²×plot > villa_total`); the live engine's +~4.5% GIS adjustment makes the *actual* trip marginally rarer, so ~5–10% is a slight upper bound. Widened-path cells (local n<5) aren't in this count but behave identically by ratio.

**Beta relevance:** an old-premium-villa buyer (V001) and a new-premium-villa buyer (V002/V003) are **both core beta users**; the surface fires for essentially all of them. The land-priced subset is precisely where the floor matters most **and** is currently missing — so Q1d's recompute is the load-bearing B-1 decision, not an edge case.

---

## Q5 — Reconcile the two land ppm² (4,032 vs 3,768) [land-floor number]

**Verdict: 🟢 reconciled — two independent land medians from two modules with different area-pooling. Use 3,768 (the surfaced floor). The 4,032/strata path is a latent inconsistency to flag.**

| | **`value_decomposition.land`** (the FLOOR) | **`stock_strata.land_reference`** (ratio ref) |
|---|---|---|
| المعمورة 56/647/6 | **3,768** · n=**20** · 24mo · reliable | **4,032** · n=**13** · area-wide · bracket_match=False |
| source function | `moj_reference.build_reference` → `categories.land` | `stock_strata.compute_land_median` |
| area resolution | `area_match_key()` — **a18 R9 sibling aggregation + hamza-fold** (`moj_reference.py:84`) | `_norm()` exact-area set membership (`stock_strata.py:249`) — **a18 NOT applied** |
| effect | pools «المعمورة» + «المعمورة 56» (+ siblings) → **more comps (20)** | narrower exact match → **fewer comps (13)**, different median |

**Root cause:** the same district's land median is computed **twice**, by two modules, and **a18's area-name reconciliation was wired into `moj_reference` but never into `stock_strata.compute_land_median`.** So `moj_reference` sees the a18-pooled set (n=20, 3,768) while `stock_strata` sees the pre-a18 `_norm` set (n=13, 4,032).

**This also explains the v139→a20 floor shift** (the LEARNING doc's "4,032 → ~2.63M" vs today's 3,768 → 2.46M): at v139 (pre-a11/a18) the decomposition's land matched strata (4,032); a11 (usage filter) + a18 (area aggregation) changed `moj_reference`'s land pool to 3,768/n=20, while `stock_strata` was left on 4,032/n=13. The floor moved **−6.6%** (2.63M → 2.46M) — a real, explainable change, not a bug.

**For B-1:** the floor = **3,768 × 652 = 2,456,736** (n=20, reliable, a18-aware) — **already the surfaced `estimated_qar`.** Trustworthy; use it. The **4,032/strata figure is the stale-area-matching twin** used only for stratum ratio classification.

> 🟡 **Latent inconsistency (flag, not B-1):** two "المعمورة land medians" disagree by ~7% because `stock_strata.compute_land_median` predates a18. Harmonising it onto `area_match_key` would align the ratio classifier with the floor (and is the same family as the a12 "compute_trend categorizer alignment" debt). **Route to RISK_REGISTER / a future cleanup sprint** — out of B-1 scope, no value drift expected on the floor itself.

---

## Findings that become B-1 brief lines (flag-and-HOLD, #38)

1. **F1 (Q1d) — Patch-C land-floor suppression.** B-1 must surface the land floor **even in the land-priced case** (`land ≥ comp value`), where `_decompose_value` currently returns None. Needs a small, presentation-scoped recompute of the land number that **does not touch** Patch C's anti-negative-building guard. Incidence **~10% of valued villa cells / ~5% tx-weighted (measured✓), 0% of reliable cells — all large-plot old-stock.** **Load-bearing decision for the brief.**
2. **F2 (Q1b) — field path.** B-1 reads `valuation.value_decomposition.land.{estimated_qar, per_m2_qar, n_transactions, reliable}` — **not** any `land_value`/`cost` key (those are the Cost-approach crosscheck, legitimately None for villas).
3. **F3 (Q2) — gate.** Recommend reusing `_condition_note_applies` (gate a) so the floor + bidirectional disclosure ride the same predicate as the live condition caveat → one coherent surface.
4. **F4 (Q3) — B-0 is obsolete.** Condition is disclosed on every villa surface (condition_note ⊕ range_disclosure). No bug to fix. Drop B-0 from the plan.
5. **F5 (Q5) — use 3,768 (the surfaced floor); the strata 4,032 is the pre-a18 twin** → route the `stock_strata` a18-alignment to RISK_REGISTER (separate cleanup).
6. **F6 (range observation) — the land floor sits BELOW the current range low.** 56/647/6: floor 2.46M < current low 3.1M < point/high 3.8M. So surfacing the floor **extends the honest downside** below today's range — material to **D1 (headline shape)**: a "land floor → as-is" span is wider (and more honest) than the current 3.1–3.8M band.

## Forward-risk + decisions this feeds

- **D2 (gate):** Q2 → recommend gate (a). **Anas signs.**
- **D1 (headline shape):** F6 shows the floor is well below the current low → the dual-number / land-floor-anchored-range options are materially different from today's band. **Claude.ai frames; Anas signs.**
- **D3 (RICS framing + copy):** the land-floor + "old stock tends toward land; condition not assessed" disclosure → **multi-AI (#54) candidate** (methodology framing). Pairs with `rics_methodology_note` (VPS 3 / IVS 103 basis).
- **Q1d/F1 is the gating build decision** — without resolving the Patch-C case, B-1 would show the floor for new/mid stock but **hide it for the land-priced stock that needs it most.** 🔮 forward-risk: if F1 is descoped, B-1 silently helps the wrong cohort. Guard: make F1 explicit in the brief's DoD ("floor present on a land-priced subject, e.g. 55/296/13-class").

## Out of scope (held)
Any calibrated condition/age **adjustment** (→ B-2). Age auto-detection. Land-path changes (villa-only). `stock_strata` a18-alignment (→ RISK_REGISTER). Confirmed-sales sourcing (→ 2.16.16).

---

## RISK_REGISTER candidate (from this pass)
- 🟡 **`stock_strata.compute_land_median` is not a18-aware** → its land median (used for E4 ratio classification) diverges ~7% from the a18-pooled `moj_reference` land median (the floor). No live value drift on the floor; classification may mis-stratify near a ratio boundary. **Route to RISK_REGISTER; fix in a future cleanup (same family as the a12 compute_trend categorizer-alignment debt).**

---

*Phase-0 recon, READ-ONLY. Production byte-identical (v159). Hand back to Claude.ai: Q1/Q2/Q5 →
D2 (gate) + D3 (copy, multi-AI #54) + the F1 Patch-C decision → Anas signs the B-1 brief → B-1 builds
(B-0 dropped: Q3 covered).*
