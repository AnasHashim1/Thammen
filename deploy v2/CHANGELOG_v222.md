# CHANGELOG v222 — Sprint 2.22.0b.151 «درجة الثقة على مسار الرجوع»
### (fallback-path evidence tier + the false size-match claim)

**Engine:** `thammen-sprint2p22p0b151-fallback-evidence-tier` · **SPRINT_TAG** `2.22.0b.151`
**Date:** 2026-07-27 · **Files:** `evaluate_unified.py` · `index.html` ·
`test_sprint_2_22_0b151.py` (new) · `test_sprint_2_22_0b117.py` (R6 re-point)
**Class:** 🟡 **DISPLAY + TIER / VALUE-INVARIANT** — `api.py` + the valuation engine
UNTOUCHED; `amount/low/high/method/rule/leadership` byte-identical (measured, §5).
**Gate-2:** PO-SIGNED 2026-07-27 — option **«ج مُصحَّحة»**.
**Gate-1:** PO «انشر» → **SHIPPED Heroku v314** (commit `a87c548`, origin in sync).

---

## 1. Why this matters

The b149/b150 fix made the *number* right when a subject's size bracket is empty
(`plot_area × ppm² median` instead of a size-blind sale-price median). It did **not**
touch what the screen *says about the evidence*. Measured live on the land anchor
**70312306** (1500 m², n=26), the SAME payload carried two contradictory statements:

| field | text | rendered? |
|---|---|---|
| `accuracy.explanation_ar` | «مبني على 26 صفقة … لعقارات قريبة في النوع **والمساحة** ضمن نفس المنطقة» | ✅ **yes** — hero confidence meter (`.cnote`) + evidence panel («المقارنات:») |
| `valuation.source_ar` (b149) | «… **لا صفقات مسجَّلة في شريحة مساحته**» | ❌ no (dead field, b139-class) |

**The rendered one was the false one.** The engine asserted size-closeness that its own
data denied — the same class as b135's false «قاد التقديرَ منهجُ الكلفة» basis frame and
b148's «تشطيب ordinary». On top of that the badge read **«شواهد كافية» score 85 / tier
high**, because on the fallback `n` counts the whole category.

**Exposure (measured, `.b151_scale.py` over the real MoJ corpus, 133 areas):**
**80 (area,bracket) combos** — 36 villa + 44 land — across 55 pools reach `cat_n ≥ 20`
with the subject's own bracket empty.

---

## 2. Root cause

`evaluate_property.apply_moj_strategy` (:637-645) falls back to the category when the
bracket is empty: `n = cat_data['n']` and `reliable = n >= 20`. That `n` then flows to
`_select_primary_comparison` Case 1 → `output['moj_sample_size']` → the accuracy block
(`evaluate_unified.py` :7100), which keyed **only** on `method == 'comparison_bracket'
and n >= 20`. Neither the tier nor the sentence knew the pool was area-wide.

---

## 3. What this patch does

### (a) The false claim — corrected for EVERY fallback (defect, not a preference)
A new honest basis sentence replaces it on the fallback path only:

> «مبني على {n} صفقة بيع فعلية مسجلة في وزارة العدل لعقارات **من نفس النوع** في المنطقة —
> **لا صفقات مسجَّلة في شريحة مساحة عقارك**، فطُبِّق وسيط سعر المتر في المنطقة على مساحته.»

Because `explanation_ar` renders on the **always-visible hero meter**, this doubles as the
signed *rendered disclosure* — no new render site was needed, and the dead `source_ar`
is no longer the only place the truth lives. EN twin authored (EN live since b88).
The original sentence is **preserved byte-identical** for the populated-bracket path.

### (b) The tier — capped by MEASURED basis error (the signed «ج مُصحَّحة»)
New pure `_evidence_capped(primary)` + `_FALLBACK_TIGHT_BRACKETS = ('400-600','600-900')`.
The threshold is **derived from the GATE2_b150 §B back-test**, at the real cliff in the data
(0.135 → 0.188), not authored:

```
villa 400-600 0.073 │ land 400-600 0.104 │ villa 600-900 0.106 │ land 600-900 0.135   KEEP
──────────────────────────── measured cliff ────────────────────────────
land 900-1500 0.188 │ villa 0-400 0.272 │ villa 900-1500 0.347
land 1500+    0.448 │ villa 1500+ 0.869                                                CAP
```

Capped → the **existing** «شواهد محدودة» / score 60 / tier medium (no new tier invented).
Fail-safe: an unknown bracket on a fallback **caps** (never claim unmeasured tightness).

> **🔴 The signed option INVERTED the handoff's proposal.** The handoff asked for
> «إرشادي للقطع الصغيرة فقط، حيث الأساس ضعيف». The back-test shows the error is **U-shaped**
> and the **large** tail is far worse (villa 1500+ **0.869** vs villa 0-400 **0.272**). The
> «+5%» that suggested "small is weakest" measures the basis's **IMPROVEMENT**, not its
> **ACCURACY** — the two were conflated. Capping "small only" would have downgraded the
> better tail while leaving score 85 on an 87 %-error class. Corrected before building.

### (c) One decision, broadcast — no duplicated rule in JS
`valuation.bracket_fallback` + `valuation.evidence_capped` are emitted; `index.html`
`_evidenceRatings` axis-2 («جودة المقارنات») reads `!v.evidence_capped` instead of
re-deriving the bracket rule in JS (the b135 drift class).

---

## 4. What is NOT in this patch

- No change to `amount` / `low` / `high` / `method` / `rule` / `leadership` — structurally:
  `primary` is read by key and never spread, and `_leadership_gate` takes explicit scalars.
- The populated-bracket path (the overwhelming majority) is untouched in text and tier.
- No new tier, no new render site, no `api.py` change.
- **R7 condition-blindness untouched** — data-gated (documented GT n≥20), not a code fix.

---

## 5. Verification — empirical evidence

| gate | result |
|---|---|
| `py_compile` (engine + api + evaluate_property) | OK |
| `node --check` — all 4 inline scripts | OK |
| isolated `test_sprint_2_22_0b151.py` | **44/44** (production predicate + real MoJ corpus) |
| DoD aggregator | **395/395 ALL COUNTS MATCH** |
| security | **16/16** |
| surface honesty | **45/45** |
| broad walk | **203/203 ALL FILES GREEN** (202→203) |
| siblings b148 / b149 / b150 | 47 / 37 / 33 — green, **no re-point** |

**R6/Lesson-2 re-point (1, test-only):** `test_sprint_2_22_0b117.py` pinned
`n_ar == n_en and n_ar == 6` — an exact **count** of accuracy tiers that b151 legitimately
grows to 7. Re-pointed to **parity + a floor** (`n_ar == n_en and n_ar >= 6`); parity is the
assertion that actually protects the EN surface. **Zero value/security/methodology/compliance
assertion weakened.**

**Local E2E (real engine, live GIS) — value byte-gate 6/6 byte-identical:**

| case | amount | low/high | tier change |
|---|---|---|---|
| 54/541/6 villa cost_led | **2,400,000** | 2.4M–5.4M | — |
| 56/647/6 villa geo_full | **3,800,000** | 3.1M–3.8M | — |
| 55/296/13 villa e25 | **2,600,000** | 2.0M–2.6M | — |
| 56/565/21 villa matched | **2,400,000** | 2.2M–2.6M | — (control: 85 kept, claim kept) |
| 52/903/90 apt | **refusal** | — | — |
| **PIN 70312306 land** | **4,800,000** | 4.3M–5.0M | **85 → 60**, false claim GONE |

**R14 real-Chromium 390×844** (both payloads × AR/EN): capped case → «شواهد محدودة», 60/100,
honest line present, **false claim absent**, axis-2 «متوسط», amount ٤٬٨٠٠٬٠٠٠ unchanged ·
control → «شواهد كافية», 85/100, original claim **present**, honest line absent, axis-2 «قوي»,
amount ٢٬٤٠٠٬٠٠٠ unchanged · EN → "size bracket" / "median price per m²" render, **"close in
type and size" absent**, `dir=ltr` · AR restored byte-identical · **0 console errors** ·
**no overflow** (390 == 390) throughout.

**Personas (standing PO directive).**
**Lawyer APPROVE** — removing a rendered claim the same payload contradicts is the single
highest-exposure fix available here; the tier moves only downward on the weakest class. No
disclaimer touched («ليس تقييماً معتمداً» · MUC clause · CC BY 4.0 intact); no new promise.
**Linguist APPROVE, one note APPLIED** — «صُنِّفت الشواهد محدودة» required the accusative;
switched to the codebase's established house phrasing «وُضِع التقدير في فئة "شواهد محدودة"»
(cf. the MU notes), which also names the exact badge the user sees.
**RICS valuer APPROVE with a disclosed residual** — comparability (VPS 3 / IVS 103) and
uncertainty disclosure (VPGA 10) both support disclosing an unmatched pool and capping the
reliability claim. **Residual, stated honestly:** even in the KEEP zone the pool is not
size-matched; the tier there rests on the measured 7–14 % error, and the new sentence
discloses the basis, so the user is not misled about what produced the number.

---

## 6. Deployment

```
git push origin master
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
```

## 6b. Live smoke v314 (browser-UA #61, body-via-file #62) — PASS

**6-fixture value byte-gate BYTE-IDENTICAL to v313:** 54/541/6 **2,400,000** [2.4M–5.4M] ·
56/647/6 **3,800,000** [3.1M–3.8M] · 55/296/13 **2,600,000** [2.0M–2.6M] · 56/565/21
**2,400,000** [2.2M–2.6M] · 52/903/90 **refusal** · **PIN 70312306 4,800,000** [4.3M–5.0M].

**The fix live:** land 70312306 → `evidence_capped=true`, «شواهد محدودة» / 60, the false
size-match claim **ABSENT**, the honest line **PRESENT**. Control 56/565/21 (populated
bracket) → `evidence_capped=false`, «شواهد كافية» / 85, its original sentence **preserved**
(there the size match is TRUE, so it correctly stays). Rule #52 closed MEASURED.

*(56/565/21 attempt 1 returned an empty body — the documented cold-dyno H12 pattern on the
heavy multi-QARS path, not a defect; the warm retry was byte-identical.)*

## 7. Verification curl

```
curl -s --compressed -X POST https://thammen.qa/api/evaluate \
  -H "Content-Type: application/json" -A "Mozilla/5.0 ... Chrome/120.0 Safari/537.36" \
  -d '{"pin":"70312306"}'
# expect: valuation.amount = 4800000  ·  evidence_capped = true
#         accuracy.label = «شواهد محدودة» · score 60
#         accuracy.explanation_ar contains «لا صفقات مسجَّلة في شريحة مساحة عقارك»
#         and does NOT contain «قريبة في النوع والمساحة»
```

## 8. Carried forward (Rule #42)

- **R7 / B-2 condition-blindness** — the largest remaining accuracy gap. Infrastructure is
  LIVE and calibrated **n=1** (b71 + S7/b113); the binding constraint is **documented GT
  (n≥20)**, a data decision, not code («الرقم يتغيّر لا الكود»).
- **Size gradient not modelled** — the fallback basis ignores that ppm² falls with plot size
  (national 1500+ ≈ 0.79× the 400-600). Separate calibration (2.20 measured *within-bracket*
  size as a weak predictor, R² ≈ 0.05).
- Apartments/towers («بوّابة بيانات الأنواع») · folded-annex EN residue · a11y Tier-3 ·
  S3 consent (PDPPL) · server-side PDF — unchanged.
