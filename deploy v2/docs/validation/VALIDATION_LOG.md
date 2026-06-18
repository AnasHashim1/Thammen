# Thammen — Real-World Validation Log

Durable ground-truth corpus seeding the **2.22.y** calibration audit
(target metric: ≥95% of verifications produce <5% valuation delta, no case >15%).

**Discipline:** entries are *data points*, not calibration claims. No rule, weight, or
accuracy statement is derived from this log until **n ≥ 20** within a comparable
ground-truth class. An asking-price match is NOT a transaction match — see strength tiers.

**🔴 INTAKE RULE (2026-06-10, PO-mandated — RETRO-APPLIES):** **no case counts toward any n
(GT-1/GT-2) without a DOCUMENT (سند ملكية / عقد بيع / شيت تقييم موقَّع).** Undocumented verbal /
owner-stated reports enter as **T2-aspiration — sentiment context only** (E1/E3: asking/aspiration
prices are NEVER calibration evidence). First retro-application: **V002/V003** (see the errata below).

## Ground-truth strength tiers (weight when aggregating)
| Tier | Source | Strength | Note |
|---|---|---|---|
| GT-1 | Valuer-signed (Stage 5) | gold | rare; the eventual benchmark |
| GT-2 | Confirmed sale (MoJ / secretary DB, 2.16.16) | strong | closed transaction |
| GT-3 | Active listing — asking price | **weak / directional** | asking ≥ sale; upper-bound signal only |
| GT-4 | Broker verbal / informal | weak | unverifiable |

When 2.22.y computes delta, **filter to GT-1/GT-2**; GT-3/GT-4 are directional context, never the calibration basis.

## Per-entry schema
`id` · `date_logged` · `engine` · `pin` · `district` · `area_m2` · `asset_type` ·
`thammen_point` · `thammen_low` · `thammen_high` ·
`gt_value` · `gt_type` (tier) · `gt_source` · `gt_date` ·
`delta_vs_gt_%` · `stratum_used` · `local_n` (aging / land / widened) ·
`confidence_signals` (badge / MUC) · `caveats` · `status`

## Index
| id | pin | district | thammen_point | gt_value | gt_type | delta | status |
|---|---|---|---|---|---|---|---|
| V001 | 56/647/6 | المعمورة 56 | 3,800,000 | 3,800,000 | GT-3 (rejected/sticky asking — unsold ~5y, 4.8M→3.8M since 2020) | 0% vs ask | open — re-verified a20 (2026-06-03): still 3.8M widened n=34, still unsold; + independent structural inspection |
| **V002** | **56/565/10** | بو هامور (Abu Hamour) | **2,500,000** | 4,000,000 **(ASPIRATION)** | **T2-aspiration (ERRATA 2026-06-10 — was mislogged GT-2; owner aspiration, no document)** | **n/a — no transaction** | sentiment context only; awaiting a documented sale |
| **V003** | **56/565/12** | بو هامور (Abu Hamour) | **2,400,000** | 4,000,000 **(ASPIRATION)** | **T2-aspiration (ERRATA 2026-06-10 — was mislogged GT-2; owner aspiration, no document)** | **n/a — no transaction** | sentiment context only; awaiting a documented sale |

---

## V001 — 56/647/6 (المعمورة 56)

- **date_logged:** 2026-05-28
- **engine:** v139 · sprint2p22p0a3-arabic-surface-honesty
- **pin / district / area / type:** 56/647/6 · المعمورة 56 · 652 m² · فيلا منفردة (standalone villa)
- **Thammen:** point **3,800,000** · range **2,900,000 – 4,400,000** QAR (range brackets ground truth)
- **Ground truth:** **3,800,000 QAR asking** · **GT-3 (active listing)** · property = 5BR + maid, 6 bath, private pool, jacuzzi, semi-furnished, "modern high-quality interior," **building age 25y (renovated)**
- **delta_vs_gt:** **0% vs asking** — point estimate equals the ask exactly.
- **stratum_used:** mid-age building (1.15–1.5×), dominant (80% of sample). The "good-modern" stratum (1.5–2.2×) sat higher at ~5.3M but n=1.
- **local_n:** aging stratum n=4 · land ref n=13 · widened total 41
- **confidence_signals:** badge `🟢 شواهد كافية` / score 78 / tier high (built on the **widened 41**) · MUC level `moderate` (live, STABLE across 5 runs) · `rics_compliant: False` (Bug A7)
- **corroboration:** Thammen auto-detected `قرب مسجد` from landmark analysis — matches the listing's `مسجد آل سعد ~200م`.

### Honest read (do not over-claim)
- **Strong directional calibration**, but it's **GT-3 (asking)**: asking ≥ sale, so 3.8M is the **top of the realistic sale zone**, not the midpoint. The true transaction delta is unknown and likely positive (Thammen ≥ sale).
- The hit came from the **conservative mid-age median on a thin local sample (n=4)** — right tier for a 25-year structure, and the ask agreed. A single fortunate-or-good hit; **n=1**, not evidence of systematic accuracy.
- **Status: open.** Upgrade to GT-2 if/when a confirmed sale price for this PIN (or the actual close of this listing) becomes available — that converts this from directional to calibration-grade.

### Cross-reference
- Surfaced the **confidence-signal coherence bug** (badge keys the widened 41 while body discloses local n=4) → routed to **2.22.y GPT-B evidence-adequacy gate** + `DESIGN_2p23_stage_authority_boundary §1`. This entry is the concrete motivating case.
- Full methodology reframe (sticky-ask history, land-value buyer behaviour, falsifiable hypotheses H-A/B/C) → `docs/learnings/LEARNING_2026-05-28_maamoura_old_premium.md`.

### 2026-06-03 update (new data point + a20 re-verification)

- **NEW ground-truth — independent structural inspection (~late May 2026):** a qualified
  engineer from the **buyer side** (not the owner) inspected the building and judged it
  **structurally very good**. Strengthens **H-C** (premium-finish / sound-structure exception):
  the building is NOT a teardown on structural grounds. **Caveat:** structural soundness ≠ market
  willingness to pay a building premium — a sound 25-y villa still faces the age-discount in a
  market that prefers new builds. Source confirms photos: travertine in/out, columned marble
  lobby, jacuzzi, pool, owner-engineer-built. (Source = buyer-side family; still **GT-3**, not a sale.)
- **Status:** **still UNSOLD as of 2026-06-03** (ask 3.8M since ~2020; 4.8M originally). The
  sticky/market-rejected-ask read holds (now ~5–6 years on market).
- **Engine re-run (a20 / Heroku v159, 2026-06-03):** point **3,800,000** · method
  **comparison_widened** · **n=34** (was 41 at v139 — the pool changed via a11 usage-filter +
  a12 built-type + a18 area-name reconciliation) · tier high/78 · MUC `moderate` · now carries
  the a20 honesty label **«بانتظار مراجعة مُقيِّم مُرخّص (المرحلة الخامسة)»** (A7). The point
  **still equals the sticky ask** → R7 condition-blindness persists; this remains the canonical
  **Sprint B** motivating case.
- **CORRECTION (2026-06-03, same day):** an earlier note here claimed the a17/a19 caveat did NOT
  attach on this widened path — that was an **extraction artifact** (I queried top-level
  `condition_note_ar`; the field lives at **`valuation.condition_note_ar`**). **Verified:** the
  caveat **DOES fire** on this widened path (and on the bracket path, V002/V003). a17/a19 works as
  designed — no B-0 bug. (Rule #36: re-examined, corrected.)
- **Analyst read (decision-support, not a verdict):** clearing band ≈ **land (~2.63M) → ~3.0–3.2M**
  for a live-in buyer who values the ready premium finishes; **not** the 3.8M ask (5+ years unsold).
  Owner redirects buyers to an **adjacent empty plot** → reveals the real fork: pay a real-but-modest
  ready-home premium over land for the villa, **or** buy the plot and build new. Strong buyer leverage.

---

## V002 / V003 — 56/565/10 + 56/565/12 (بو هامور / Abu Hamour) — ~~FIRST GT-2 (confirmed sales)~~ **T2-ASPIRATION (errata)**

> **🔴 ERRATA (2026-06-10, PO disclosure):** the «SOLD 4,000,000 each» entries below were **OWNER
> ASPIRATION (asking)**, NOT completed transactions — no document exists. **Every in-section claim
> that depends on a sale is SUPERSEDED:** «FIRST GT-2» → false (the corpus has **ZERO** documented
> confirmed sales of new-premium stock); «delta −37.5/−40.0%» → **n/a, UNMEASURED** (a delta vs an
> ask is not an under-anchor measurement — E1/E3); «new-premium ≈ +67% over the bracket» → an
> ASK-premium, consistent with the Empirical §3 asking-premium bands (+30–60% new-build), not a
> measured market premium; «breaks the 2.16.16 blocker» → it did not. What REMAINS measured:
> the engine outputs (2.5M/2.4M, bracket n=37), the PIN-path reality-stop, the a17/a19 caveat
> firing, and the composition estimate ≈ **3.35M** (RCN_lux 3,500 × ~470 BUA + land 3,778 × 450,
> n=33) — vs the **ASK 4.0M**. The §20.47 Lever-2 drop **stands on different grounds**: a cost
> approach must never chase ASK prices (E25 rewritten). The historical text below is kept
> as-written for the audit trail; read it through this errata.

- **date_logged:** 2026-06-03 · **engine:** a20 · sprint2p22p0a20 (Heroku v159)
- **What:** two **adjacent, identical-spec NEW villas**, **450 m²** each, **built ~1 month ago**
  (empty land ~1 year ago), modern build — elevator, G+1+penthouse (3rd floor sharing the roof),
  modern marble / doors / smart-home tech. Same **Street 565** as the V-anchor 56/565/21.
- **Ground truth:** **SOLD 4,000,000 QAR each** · **GT-2 (confirmed sale)** · source: buyer-side /
  brokerage knowledge (Anas). Two independent confirmations at the same price → tight anchor.
- **Thammen (a20, by address):** 56/565/10 → **2,500,000** · 56/565/12 → **2,400,000** ·
  method **comparison_bracket** n=37 (36mo window) · tier high · MUC moderate ·
  `valuation.condition_note_ar` **present** (a17/a19 fired).
- **delta_vs_gt:** **−37.5% / −40.0%** (engine UNDER-anchors). The engine gives **~2.4M to all three
  Street-565 villas** (V002, V003, and the old anchor 21) — **blind to built type / age / condition**.
- **PIN-path note:** entered by PIN (56099695/96) the engine correctly **reality-stops**
  (`building_present`, qars_in_polygon=1, "use the Address tab") — Sprint 2.21.0.7 guard working.
- **per-m²:** confirmed **8,889 QAR/m²** (4.0M / 450) vs the engine bracket ≈ **5,333/m²** (2.4M / 450)
  → **new-premium ≈ +67% over the age/condition-blind bracket median.**

### Why these are the most valuable cases yet (project benefit)
- **FIRST GT-2 (confirmed-sale) data** — breaks the project's #1 calibration blocker (Confirmed
  Sales 2.16.16 had **no source**). Anas is now feeding confirmed sales → **revive 2.16.16 as an
  Anas/broker-fed workstream** (the binding constraint for H-A, the condition premium, D5/D6).
- **MEASURED bidirectional R7, same micro-market:** V002/V003 (new premium → engine **−37–40%**,
  under-anchor) + V001 Maamoura (old premium → engine matches the rejected ask, over-anchor toward
  the land-clearing signal). Same Zone 56 / Abu Hamour. Exactly the §20.10.2 thesis, now with real
  + confirmed data.
- **VALIDATES a17/a19:** the `condition_note_ar` correctly warned "a better-than-average property
  may sit ABOVE this point" — and these sat **+60–67% above**. The honesty surface was right; what's
  missing is the **quantification** (Sprint B).
- **Discipline:** n = **2 confirmed + 1 asking** → still **n < 20**. **No rule, no weight, no
  calibration** yet (the −37–40% is a data point, not a coefficient). These **motivate + seed** the
  corpus; calibration waits for n≥20 GT-2.
- **status:** open — first GT-2 anchors; grow the corpus before any calibration.

---

## 2026-06-18 — Ashghal government BoQ → §20.9 DRC RCN ladder cross-check (VALIDATION-only)
- **Source:** priced Qatar government BoQ, **water tank TN-06** (Ashghal, QCS 2014; total 66.06M QAR).
  Structural unit rates: RC concrete 700–800 QAR/m³ · rebar B500B **4,000 QAR/tonne** · formwork
  140–225 QAR/m² · excavation 45 QAR/m³.
- **QS build-up (villa 56/565/10, BUA ~450 m²):** structure from the BoQ rates (~870 QAR/m²) +
  finishes/MEP/blockwork/external from **QS standards (NOT in the BoQ)** + ~15% prelims/OH&P →
  **all-in ~2,500 QAR/m²** (band ~2,200 ordinary → ~3,500 luxury); building-only **≈ 1.1M QAR**.
  DRC(new) ≈ land 1.71M + building 1.1–1.7M ≈ **2.9–3.4M** vs AVM market **2.5M**.
- **Result:** the build-up falls **inside** the §20.9 RCN ladder and the structure (independent
  Ashghal rates) lands on a ladder whose sole anchor is TD-93317 → **two independent sources
  triangulate → CONFIRMS the ladder, does NOT change it.**
- **Discipline (RICS valuer persona — verdict DOCUMENT_VALIDATION, IVS 104):** validation-only,
  **effective n still = 1** (TD-93317 alone); a wrong-building-type single BoQ fails "sufficiency" for
  recalibration. **NOT counted toward B-2 n≥20** (not a documented sale). Caveats: project-type (tank,
  structure only) · prelims/MEP/finishes excluded + supplied from QS · escalation date unfixed ·
  unmeasured infra→villa trade-transfer. **value-invariant — engine + RCN ladder UNTOUCHED.**
- **E25:** DRC > market **supports** the new-stock under-anchor direction; **supporting, not
  calibrating** (56/565/10 is an existing villa, not a documented new-stock sale → does not unlock B-2).
- **status:** filed as a confirmatory cross-check; see `docs/VALIDATION_DRC_RCN_ashghal_boq_2026.md`.
  No engine/methodology change. NEXT (PO): collect building-type-appropriate **villa** cost evidence
  for a future Gate-2 RCN calibration.
