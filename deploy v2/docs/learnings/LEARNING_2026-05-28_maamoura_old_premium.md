# LEARNING — 2026-05-28 — Maamoura old-premium villa (56/647/6)

**Type:** methodology stress-test case study (parallel to `LEARNING_huzoom_case`).
**Discipline:** hypotheses below are *falsifiable and unproven*. No rule, weight, or
stratum reassignment is derived until **n ≥ 20** comparable cases. This is one
ground-truth case — owner-disclosed, not a confirmed transaction.
**Linked data point:** `docs/validation/VALIDATION_LOG.md` V001 (same PIN).

---

## 1. The case

Property `56/647/6`, المعمورة 56 — standalone villa, 652 m² (Cadastre-verified
PD/3169/2001), building age ~25 years, premium finishes (owner is an engineer;
high-grade wood, full renovation, pool + jacuzzi, semi-furnished).

**Owner-disclosed market history** (source: family knowledge, owner-side):
- Listed by the same seller since ~2020 (Corona) at **4.8M QAR**.
- Unsold for ~5 years; ask later dropped to **3.8M** (current listing).
- Repeated buyer behaviour: prospective buyers offered **land value**, citing the
  building age. The owner refused and redirected them to an **adjacent empty plot**.
- Owner believes the building carries real value (engineering effort, premium
  finishes) — the market, so far, does not pay for it.

**Thammen output (v139, Sprint 2.22.0a.3):**
- Point estimate **3.8M** (range 2.9M–4.4M), from 41 widened MoJ comps.
- Land value ~2.63M (4,032 QAR/m² × 652); building credited **30.8%** (~1.17M).
- Stratum used: **mid-age (1.15–1.5×) dominant median** — NOT the land-value (~1.0×) stratum.
- MUC `moderate`; accuracy badge `🟢 شواهد كافية` (built on widened 41; local stratum n=4).

## 2. What the case actually tells us (corrected read)

The initial read — "estimate = ask, 0% delta, strong calibration" — was **too quick**
and is corrected here. The 3.8M ask is a **sticky, market-rejected ask**, not a
validated value:
- It has not transacted in ~5 years (4.8M → 3.8M, still unsold).
- Revealed buyer behaviour prices the property at **land value (~2.63M)** — roughly
  **31% below** Thammen's estimate.
- So Thammen matched a number the market has rejected, while the clearing signal
  points toward land.

**Honest counter-weights (why this is NOT a clean "Thammen over-values"):**
- The ~5-year freeze overlaps a genuinely disrupted, illiquid market (the report's
  own MUC: post-Mundial correction, regional conflict, Hormuz, transaction collapse).
- A finish-valuing buyer might pay above land; the right buyer may simply not have
  appeared in a thin market.
- True clearing price is **uncertain** — somewhere between land (~2.63M) and ask
  (3.8M), with strong buyer-side pull toward land for old stock.

## 3. Falsifiable hypotheses (require n ≥ 20 before any rule)

- **H-A (building over-credit on old stock):** for buildings older than ~20y, the
  combined/dominant-stratum median over-credits the building versus the price the
  market actually clears at — which trends toward the land-value stratum.
  *Test:* collect old-building (≥20y) cases with confirmed sale prices; compare
  Thammen point vs sale; measure whether residual is systematically positive.
- **H-B (stratum mis-assignment by age):** stratification keys on transaction
  price-to-land ratio, not age directly; an old premium-renovated villa may land in
  mid-age stratum when market behaviour says land-value stratum. *Test:* for old
  cases, does the land-value stratum predict clearing price better than the
  dominant median?
- **H-C (premium-finish exception):** does premium renovation on an old structure
  ever recover the market's age discount? (The owner's thesis.) *Test:* old +
  premium-finish confirmed sales vs old + standard.

**Do not** act on any of these from n=1. This case motivates the data collection,
it does not justify a stratum change.

## 4. Validates the T1.4 decision

Sprint 2.22.0a.3 **de-ruled** the "10-Year Rule" into an *observed tendency* (old
buildings trade toward land value) rather than a named rule, and rather than
deleting it. This case is that tendency happening live — buyers literally pricing a
25-year building at land. Keeping it as a real-but-not-absolute tendency was
correct: H-C (premium-finish exception) is exactly why it must NOT be an absolute rule.

## 5. Cross-references / routing

- **Stratification / GPT-B evidence gate (2.22.y):** H-A/H-B feed the
  evidence-adequacy work — the accuracy badge here (`🟢` on widened 41) already
  contradicts the thin local stratum (n=4); building-credit calibration is the
  same family.
- **Confirmed Sales DB (2.16.16):** when it lands, this PIN's eventual sale (if it
  sells) upgrades V001 from GT-3 (asking) to GT-2 (confirmed) and becomes the first
  real test of H-A.
- **VALIDATION_LOG V001:** to be updated with the 4.8M→3.8M history + land-value
  buyer behaviour + this reframe.

---

*Logged 2026-05-28. Status: open — awaiting confirmed clearing price to test H-A.
One case; not a rule.*
