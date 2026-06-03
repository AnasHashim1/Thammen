# Thammen — Real-World Validation Log

Durable ground-truth corpus seeding the **2.22.y** calibration audit
(target metric: ≥95% of verifications produce <5% valuation delta, no case >15%).

**Discipline:** entries are *data points*, not calibration claims. No rule, weight, or
accuracy statement is derived from this log until **n ≥ 20** within a comparable
ground-truth class. An asking-price match is NOT a transaction match — see strength tiers.

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
- **Sprint-B flag (verify):** the a17/a19 `condition_note_ar` did **not** attach on this widened
  path (`condition_note=None`); confirm whether the dispersed-widened **a10 honest-range** is
  carrying the condition disclosure instead, or whether this premium-condition case is slipping
  through both — i.e. the property that most needs the condition disclosure may not be getting it.
- **Analyst read (decision-support, not a verdict):** clearing band ≈ **land (~2.63M) → ~3.0–3.2M**
  for a live-in buyer who values the ready premium finishes; **not** the 3.8M ask (5+ years unsold).
  Owner redirects buyers to an **adjacent empty plot** → reveals the real fork: pay a real-but-modest
  ready-home premium over land for the villa, **or** buy the plot and build new. Strong buyer leverage.
