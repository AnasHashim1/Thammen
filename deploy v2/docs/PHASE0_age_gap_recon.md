# PHASE-0 RECON — CGIS-vs-actual building-age gap (§11 ج, the §20.9 GATED-slice prerequisite)

> **🔴 ERRATA (2026-06-10, Sprint 2.22.0b.18 / TD-93317 sheet verification — Anas-verified from the bank
> PDF):** the **V001 "actual ~25 (bank TD 93317)" attribution below is WRONG.** The bank report states
> «بحالة ممتازة نحو 18 سنة … إسترشاداً بموقع CGIS» — i.e. **the certified valuer USED THE SYSTEM AGE
> (18)**, and the 2002 deed says «أرض فضاء» (vacant land) → an age of 25 in 2026 was **impossible** (≤24
> max). The V001 row's "gap ~8y" is therefore NOT a measured V001 gap; V001 is NOT evidence of the cliff
> magnitude (the cliff itself stays measured✓ on the n=737 cohort). The b13 "exact 3.6M match at 25y +
> luxury" was **compensating parameters** (3,500×0.50 ≈ 3,000×0.64 — PHASE0_b18 §2); the sheet reproduces
> at **RAW system age 18 + finish=high (RCN 3,000 × 0.64) → +0.35%**. Forward rule (b18 §A1, E26): the
> LEAD basis = the system-documented age; a user-claimed age renders as disclosed sensitivity only.

> **READ-ONLY recon. No engine change, no deploy.** Engine stays **b11 / Heroku v180** (byte-identical).
> **Goal:** define the *actual-age handling rule* the §20.9 **GATED** slice (convergent-confirm + UP-lift)
> needs — because the b11 SHIP-NOW immunity **inverts** on convergent cases (system age **over-states** the
> cost there, so it would mis-trim). Pairs with `METHODOLOGY_DRC_qatar_v1.md` §11 (the Gate-2 SPLIT) +
> Session_Log §20.45.
> **Provenance:** live khazna `QARS_Point` GET probe (`.age_recon.py`, 2026-06-10) — **n=737** villa parcels
> (`BUILDING_NO_SUBTYPE=1`, ≤200/zone × zones 52-56, deduped by PIN) + 7 known-GT parcels. Facts tagged
> **measured✓** or **inferred~**. Reference "now" = 2026-06-10.

---

## 1 — Why this matters (the inversion)

The §20.9 DRC cost = `land_floor + RCN(finish) × retention(effective_age) × BUA`, retention =
`clamp(1 − eff_age/50, 0.27, 0.98)`. **System age (from `SURVEYED_DATE`) is ≤ actual age** → retention is
**higher** → cost is **higher** than the truth.

| §20.9 slice half | direction of a too-high cost | verdict |
|---|---|---|
| **DOWN-re-anchor (b11, SHIPPED)** — cost is the *floor* | a higher cost = a **higher floor** = a **less aggressive** down-move + a **harder** >30%-undercut trip | **CONSERVATIVE / IMMUNE** — system age is correct here (measured✓ b11: V001 sys≈17 → +22% < 30% → no-fire; actual 25 → +30.6% → would-fire — so the floor is *protected* by using system age) |
| **convergent-TRIM (GATED)** — cost should pull an OLD over-anchor DOWN to ~cost | a too-high cost ⇒ **under-trims** (leaves the over-anchor; §20.45: production system-age cost on V001 ≈ **3,805 = +5.7%**, not the valuer's 3,600 ⇒ no trim) | **NEEDS ACTUAL AGE** |
| **UP-lift (GATED)** — cost lifts an under-anchored NEW villa UP | NEW stock → small absolute age → retention ≈ 0.94-0.96 either way → bounded error | **safe on system age for genuinely-new stock** |

So the GATED slice cannot just reuse the b11 system-age path; it needs an actual-age rule.

---

## 2 — Distribution (measured✓, n=737 villas, zones 52-56)

| stat (system age, y) | value |
|---|---|
| min / p10 / p25 | 0.0 / 8.3 / 12.4 |
| **median** | **16.3** |
| p75 / p90 | 16.6 / 16.9 |
| **max (hard ceiling)** | **17.0** |
| mean | 14.2 |

| bucket | n | share |
|---|---|---|
| 0-5y | 40 | 5% |
| 5-10y | 70 | 9% |
| 10-15y | 136 | 18% |
| **15-20y** (really 15-17) | **491** | **67%** |
| 20-25y | 0 | 0% |
| **25+y** | **0** | **0%** |

**The smoking gun:** **ZERO** villas read older than **17.0y**, and **65% were surveyed in 2009-2010**
(measured✓ year clusters: 2009=359, 2010=119, then 2014=64, 2012=40, 2016=24…). **62% sit at sys_age ≥16y**
(the cliff). `SURVEYED_DATE` is the **GIS survey vintage, not the construction date** — a mass QARS survey
campaign ran ~2009-2012 (cross-ref Bug A11 / Rule E7: "QARS subtype last surveyed 2010-2012"). Any building
that already existed in 2009 is **floored at ~17y regardless of true age** (a 40-year-old villa and a
17-year-old villa both read ~17).

---

## 3 — Known-GT calibration (measured✓ system age vs known/estimated actual)

| parcel | PIN | subtype | surveyed | **sys age** | **actual** | gap | mechanism |
|---|---|---|---|---|---|---|---|
| **V001** Maamoura 56/647/6 | 56101583 | 1 | 2009-08-09 | **16.8** | ~~25 (bank TD 93317)~~ **ERRATA b18: the bank USED system age 18; deed 2002 = أرض فضاء → 25 impossible** | ~~8y~~ **n/a (see errata)** | survey-vintage cliff (2009) |
| **V002** Abu Hamour 56/565/10 | 56099695 | 1 | **2026-03-26** | **0.2** | ~2-4 NEW (sold 4.0M) | ~2-4y | **transaction re-survey** (zeroed at sale) |
| **V003** Abu Hamour 56/565/12 | 56099696 | 1 | **2026-03-26** | **0.2** | ~2-4 NEW (sold 4.0M) | ~2-4y | **transaction re-survey** |
| anchor Abu Hamour 56/565/21 | 56090294 | 1 | 2011-04-25 | 15.1 | established G+1 (govt lease) | ≥0 | early survey |
| anchor Marikh 54/541/6 | 54360025 | 1 | 2009-10-28 | 16.6 | ~20 (plain 2story+annex) | ~3y | survey-vintage cliff (2009) |
| anchor Maraad 55/296/13 | 55744587 | 1 | 2009-12-27 | 16.5 | house/villa | ≥0 | survey-vintage cliff (2009) |
| anchor apt 52/903/90 | 52200100 | **6** | 2009-06-18 | 17.0 | apartment_building | n/a | (not a villa — subtype 6) |

**Every GT parcel demonstrates `sys_age ≤ actual_age`** — system age is never an over-estimate (a survey
cannot predate construction). The gap is **NOT a constant offset and NOT proportional** — it is **two
discrete events**:

1. **Survey-vintage CLIFF (~2009-2012):** pre-2009 stock floored at ≤17y; actual age **unbounded above**,
   unrecoverable from `SURVEYED_DATE`. (V001: 16.8 → 25; Marikh: 16.6 → ~20.)
2. **Transaction re-survey:** a sale re-stamps `SURVEYED_DATE` to ~now → sys_age ≈ 0 on a 2-4y building
   (V002/V003). **This is exactly the "re-registration zeroes the date" the brief flagged** — and it makes
   even *new* stock read younger than it is.

⇒ **`SURVEYED_DATE → system age is a guaranteed LOWER BOUND (FLOOR) on actual building age, and at the
2009-2010 cliff it is uninformative for any stock older than ~17y.**

---

## 4 — RECOMMENDED RULE for the GATED slice (measured✓)

**R1 — Precedence: user-supplied `building_age_years` (already accepted on `/details`) > system age.**
When the owner/broker supplies an actual age, the GATED slice (convergent-trim + UP-lift) **uses it**.
The engine already threads `building_age_years` (b4) — no new input plumbing.

**R2 — Conservative direction, per slice half (no user age supplied):**

| slice half | rule | why (measured✓) |
|---|---|---|
| **DOWN-re-anchor (b11)** | **keep SYSTEM age as a FLOOR** — already shipped, **do not change** | system age → higher cost → higher floor → conservative; the >30% gate is *harder* to trip → immune (b11) |
| **UP-lift, genuinely-new stock** (`sys_age < ~5y`) | **fire on system age** | absolute age small → retention error ≤ ~0.04 → bounded; new villas are exactly where the survey date is freshest |
| **convergent-TRIM, OLD stock** (`sys_age ≥ ~10y`, i.e. at/near the cliff) | **GATE on a user-supplied actual age**; absent it, the cost stays a **disclosed FLOOR only (no central trim)** | the 2009 cliff makes system age uninformative above ~17y → a system-age cost **under-trims** (V001: leaves +5.7%); firing the trim on system age would silently fail to fix the over-anchor. No-harm but no-fix ⇒ keep b11's floor-only behaviour until an actual age exists |

**R3 — A cliff-flag the engine can compute for free** (no new GIS): treat `sys_age ≥ 15` **AND**
`SURVEYED_DATE` year ∈ {2009, 2010, 2011, 2012} as **"vintage-capped — actual age unknown, ≥ system age."**
This lets the GATED slice *disclose* "age is a floor" and **withhold the convergent-trim** rather than
mis-fire. (62% of villas fall here — measured✓.) The transaction-re-survey case (`sys_age < 2` on stock the
market treats as several years old) is the inverse flag — also "age is a floor," handled by R2's new-stock row.

**Net:** the GATED slice is **safe to build now for (a) the DOWN-half [shipped] and (b) the UP-lift on new
stock**; the **convergent-TRIM on old stock must wait for a user-supplied actual age** (or a future
imagery-vintage age detector — §6). This is the actual-age handling rule §11 ج asked for.

---

## 5 — What the ~0.31 PO floor plugs into

The retention clamp `clamp(1 − eff_age/50, **0.27**, 0.98)` (b11 shipped the locked global **0.27**). The PO
**dilapidated-luxury floor (~0.31)** is a **finish-tier-conditional minimum retention**: for `high`/`luxury`
finish, retention floors at **~0.31** instead of 0.27 — a premium structure retains more residual value even
when dilapidated (its RCN is 3000-3500 ر.ق/م², so over-depreciating it understates the building). It plugs
into `_cost_retention` as a per-finish floor. **It does NOT affect ship-now** (the b11 DOWN-half is
system-age-immune and uses 0.27); it bites only on the **convergent-TRIM of old LUXURY stock with a supplied
actual age** — preventing that trim from over-depreciating a premium build (e.g. an aged V001-class villa).
**Still PO-pending** (exact value finish-dependent).

---

## 6 — Residual / NOT covered (inferred~)

- **No imagery-based actual-age detector.** The 2.15 imagery age-detector was rolled back (median ~11s,
  precise ±5y only 27%, 42% undetermined — §20.43). So above the 2009 cliff there is **no cheap automatic
  actual age** → the convergent-trim's actual-age input is **user-supplied today**. A future option: infer a
  build-vintage band from QatarOrtho/Satellite imagery presence (1995/2004/2010/2017…) — a *band*, not a
  point — which would let the trim fire disclosed-as-indicative without user input. Separate sprint.
- **Broad sample has no per-parcel ground-truth actual age** — the cliff + the FLOOR property are proven from
  the hard 17.0y ceiling, the 2009-2010 cluster (65%), and the 3 GT parcels with known actual age; the
  per-parcel gap *magnitude* above the cliff is unmeasured (and unmeasurable from `SURVEYED_DATE` — that is
  the whole point).
- **Apartment/compound subtypes not sampled** (villa subtype=1 only — the §20.9 scope).
- This recon defines the **rule**; it ships **no code**. The GATED-slice build is a separate Gate-2 sprint
  (this rule + the CGIS-cliff flag R3 + the PO 0.31 floor are its inputs).

---

*Recon 2026-06-10. READ-ONLY (`.age_recon.py`, regenerable). Engine UNCHANGED b11/v180. Owner: Anas.*
