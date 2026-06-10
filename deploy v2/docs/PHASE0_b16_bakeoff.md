# PHASE-0 — Sprint 2.22.0b.16 BAKE-OFF (B-2 early slice) — M1-M4 measured, HALT band judged

> Per `BRIEF_Sprint2p22p0b16_B2_early_slice_SIGNED.md` §3/§4. **Measured✓** on the REAL engine (local
> `evaluate_thammen`, live GIS) + the REAL MoJ CSV with the production comp filters (`area_match_key` +
> `_bt_matches` villa + `_is_residential_usage` + bracket) — E14. Scripts: `.b16_bakeoff.py` +
> `.b16_m1_variants.py` (scratch, regenerable); raw table `.b16_bakeoff_results.json`. Date: 2026-06-10.
> **VERDICT: HALT BAND PASS — proceed to build** (winner = M4 ≡ M1c-led with M3 floor, the brief's
> suspected winner, under the two resolutions documented in §3 below).

## §1 — The candidate mechanisms, measured

**Cohort:** Marikh 54/541/6 (trigger) · V001 56/647/6 · the 3 control anchors (Abu Hamour 56/565/21
clean-bracket · Maraad 55/296/13 land-anchored thin · Apt 52/903/90 refusal) · **8 discovered old villas**
(QARS subtype-1, zones 51/53/54/55, `SURVEYED_DATE ≤ 2012` — the E24 cliff; distinct streets):
51/833/37 · 51/825/22 · 53/736/4 · 53/541/48 · 54/793/92 · 54/788/10 · 55/1056/60 · 55/1044/63.

**M1 required an estimator disambiguation (measured, decisive).** The brief's parenthetical pins the
Marikh expectation to «≈ 517/ft² ⇒ ~3.0–3.4M» — that is the **§20.10.1 estimator**: the FULL-window
**ppm² median over the subject's GEO bracket [plot×0.8, plot×1.2]**, × the effective plot. Three variants
measured (production filters; Marikh plot 613 → geo [490,736] / size [600,900]):

| estimator | Marikh | V001 (plot 652) | Abu Hamour (ctl) |
|---|---|---|---|
| M1a — SIZE-bracket FULL **total-price** median | 5,000,000 (n=22) | **3,600,000** (n=15 — the certified valuer's figure) | 2,380,000 (n=61) |
| M1b — SIZE-bracket FULL ppm² × plot | 4,842,087 (7,899/m², n=22) | 2,854,456 | 2,380,050 |
| **M1c — GEO-bracket FULL ppm² × plot (the brief's)** | **3,412,571 (5,567/m² ≈ 517/ft², n=51)** | 3,297,816 (470/ft², n=22) | 2,335,050 (n=54) |

M1c reproduces the brief's cited 517/ft² **exactly** on Marikh, on the largest pool (n=51 vs 22). M1a/M1b
stay distorted on Marikh (the 600-900 size cell is dominated by the same premium stock the slice corrects
for — total-price medians don't normalize size). **M1 := M1c.** Drift context (E23): Marikh geo ppm²
24mo=7,333 (n=29) → 36mo=5,567 (n=36) → FULL=5,567 — the 24mo window carries the premium cluster.

**M2 (matching-stratum, n≥10):** Marikh aging n=2 / land_priced n=1 → ABSTAINS (as the brief predicted);
V001 aging n=1 → ABSTAINS; Abu Hamour aging n=17 (control — path-excluded anyway). M2 = the supersession
ladder's first rung (build wires: stratum n≥10 → M2 precedence).

**M3 (system-age DRC, the engine's own `_cost_approach_value`):** Marikh 2,378,094 (= the live b11 cost) ·
V001 3,119,090 · Abu Hamour 2,194,070. Under-shoots plain-villa market as expected → a FLOOR, not a central.

**M4 (hybrid = min(max(M3, M1c), thin median)):** Marikh **3,412,571** · V001 3,297,816 · (controls n/a).

## §2 — Materiality margin (the brief leaves it to Phase-0)

Margin := (thin median − M4) / M4. Measured: **Marikh +58.2%** · **V001 +15.2%** · others n/a.
**T = 20%** — anchored on the project's own empirical clean-stock asking-premium ceiling (8–20%,
Empirical_Findings §3): a thin median within 20% of the re-anchor is inside normal market noise →
no correction (the §1 honesty frame: V001's old-luxury premium ≈ 0 → CONVERGED, nothing to fix);
beyond 20% = the Marikh-class distortion. Consequence: **Marikh fires; V001 abstains** (comfortably —
not a borderline flip, E23 hysteresis-safe). The mechanism still **reproduces the valuer's band on V001
in the table** (M4 = 3.30M, M1a = 3.60M — brackets the certified 3.6M): the calibration claim holds
without churning a live central that already sits in-band.

## §3 — Two premise resolutions (documented, flag-and-proceed)

1. **«NOT b11-reanchor zones already leading» (§2) read as: zones where another mechanism already LEADS
   the central.** Marikh — THE motivating case with a signed HALT band [2.8M, 3.6M] — is live in the b11
   `cost_reanchor_down` zone (undercut 128%). b11 BY DESIGN sets only the floor/range and leaves the
   central UN-led (the muted thin median — «no invented central», §20.45); income_led and the b13 trim DO
   lead the central. Under the literal exclude-b11 reading the signed band is unsatisfiable (Marikh's
   central could never move) — the band itself disambiguates the brief. **b16 therefore UPGRADES the b11
   zone's un-led central on the stratum-mismatch subset; income_led and b13-trim zones stay excluded
   (precedence: income_led > b13-trim > THIS > b11-floor/widen_down for the central; b11's cost floor is
   INHERITED as this slice's range-low).**
2. **M1 estimator = the §20.10.1 geo-bracket ppm²-FULL** (above) — the brief's own cited expectation,
   not the size-bracket total-price variant.

## §4 — Expected-moves table vs the HALT band (the build's EXACT contract)

| subject | today (b14/b15 live) | b16 expected | band | verdict |
|---|---|---|---|---|
| **Marikh 54/541/6** | thin **5.4M**, range [2.4M, 5.5M], rih, ct=`cost_reanchor_down`, MUC high | **`old_stock_reanchor_indicative`: amount (central) = 3,412,571 → _r100k → 3.4M**, range **[2.4M … 5.4M]** (low = max(land 1,851,260, cost 2,378,094) → 2.4M; high = the thin median, muted), rih=True, MUC high + the verbatim §4 label, b14 Case-A narrative KEPT | **[2.8M, 3.6M]** | **IN ✓** |
| V001 56/647/6 | widened 3.8M [2.5M, 3.8M] | **byte-identical** (margin 15.2% < T=20% → ABSTAIN; converged per §1) | [3.3M, 3.9M] | **IN ✓ (3.8M)** |
| Abu Hamour 56/565/21 | bracket 2.4M | byte-identical (clean-bracket path excluded) | byte-identical | ✓ |
| Maraad 55/296/13 | thin 2.6M, land 2.67M ≥ amount | byte-identical (land-anchored → not over-anchored) | byte-identical | ✓ |
| Apt 52/903/90 | refusal | byte-identical | byte-identical | ✓ |
| 51/833/37 · 51/825/22 · 53/736/4 | `comparison_bracket` (dispersion-gated, rih) | byte-identical (path-excluded) | — | ✓ |
| 53/541/48 · 54/793/92 | refusals | byte-identical | — | ✓ |
| 54/788/10 · 55/1056/60 | thin + b11 fired, **strata absent (dom=None)** | byte-identical (**ABSTAIN — dominant-stratum signal absent**; stay b11) | — | ✓ |
| 55/1044/63 | preliminary, strata absent | byte-identical (abstain) | — | ✓ |

**HALT VERDICT: PASS.** 0 spurious firings on the 8-villa discovered cohort; the live firing surface is
genuinely surgical (the Marikh class: thin/widened + strata data resolving a premium-dominant stratum
≥40% + margin > 20% + old + over-anchored + no user luxury/new/renovated).

## §5 — Build notes (measured call-site facts)

- `evaluate_thammen` (3631) calls `_build_unified_output` at **4223**; the b4-region (4690+) runs AFTER on
  the complete output → **`output['stock_strata']` + `property_basis` ARE available to the b16 branch**
  (the b14 line-number illusion checked and cleared).
- M1c needs the rows → computed in `evaluate_property` Step 2 (where the CSV rows live) on the EFFECTIVE
  plot area and threaded additively (`moj_ref_dict['subject_geo_full']` = {ppm2_median_full, n_full,
  value_full}) — the a13/a14 additive-threading precedent.
- **index.html renders NO `cost_triangulation` note today** (grep = 0) — b11/b13 notes are JSON-only. The
  §4 rail «the old thin median stays visible muted» mandates a UI line → b16 adds ONE muted `.rn` renderer
  for `v.cost_triangulation.note_ar` in the TIER-1 block (which also surfaces the b11/b13 sibling notes —
  same field, honest improvement) → **R14 required** (the brief's §5 anticipated this).
- Supersession ladder to wire + document: stratum n≥10 → M2 precedence (auto) · n≥20 → the indicative
  label upgrades · every GT intake logs `engine_estimate_at_intake` (the kit's §3 — manual channel, no
  engine change).
- **Pre-existing observation (deferred, Rule #42 — NOT b16 scope):** b11's emitted range can INVERT
  (low > high) when `primary.high < cost` — live on 54/788/10 ([1.1M, 1.0M]) + 55/1056/60 ([1.7M, 1.6M]).
  b16's own emissions are immune (high = thin median ≥ comp > cost). Fast-follow micro-fix candidate.

## §6 — Honest residuals (to restate at close)

Calibration = ONE certified appraisal (V001) + the FULL-window MoJ pool — the label says so verbatim; the
GT kit (D-3) is the tightening channel (targets ≥8 luxury_new + ≥6 old-plain + ≥6 valuer reports). The
slice fires ONLY where the strata panel resolves a dominant premium stratum (measured: 0/8 of the random
old-villa cohort) — surgical by design, self-superseding as GT arrives.
