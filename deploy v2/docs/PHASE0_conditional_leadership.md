# PHASE-0 — Evidence-Conditional Leadership (universality inventory + flip-rate measurement + calibration gate + anchor retirement)

> **Date:** 2026-06-11 · **Mode:** READ-ONLY recon — **zero engine/frontend edits** (b19 executes separately as signed).
> **PO directive (2026-06-11):** three-value stack everywhere · leadership by evidence quality · universal DRC ·
> legacy anchors' recorded expectations RETIRED (re-baseline post-ship) · **V001 = SOLE calibration anchor**.
> **Status (updated 2026-06-11):** Gate-2 **F6 SIGNED** (`SESSION_CLOSE_2026-06-11_F6_SIGNED.md` §1) over the §2.7
> FINAL numbers. The companion brief = `BRIEF_conditional_leadership_SIGNED.md` (the normative reference).
> Build sprint 2.22.0b.20 proceeds; **Gate-1 (Heroku push) = a separate later consent.**

## §0 — #57 ground-truth handshake (measured 2026-06-11)

| item | measured |
|---|---|
| `/api/health` | `3.1.0-sprint2.22.0b.18` · engine `thammen-sprint2p22p0b18-age-basis-finish-delta` (b18/v187 lineage) |
| qars | healthy (primary khazna alive, 162,514) |
| MoJ freshness | 2025-12-31 → **162 days** stale (tier: stale) |
| git | branch `master` @ `cf9704c` · **master == origin/master** (no drift) |
| working tree | scratch/untracked only (`.p0_*`, `.b*` probe families — regenerable) |

---

## §1 — Universality inventory: where `_cost_approach_value` computes vs skips (measured✓ from code)

### §1.1 Call sites + the block guard

`_cost_approach_value` is called at exactly **two sites**, both inside the §6-triangulation block
(`evaluate_unified.py:4705–4948`), which runs only when **all three** hold (`:4706-4708`):
`valuation.amount` exists **AND** not `teardown` **AND** not `luxury_new_premium`.

- **Site 1 (`:4727`)** — system-age cost: `land_floor=_lf_tri` (from `_villa_value_floor`) ·
  `footprint_max_m2` (b10 geometry) · `floors` (user; default G+1=2 inside the fn) ·
  `finish = 'luxury' if is_luxury else 'ordinary'` · `age = _age_ct` (b9 SYSTEM age) ·
  `condition` (user; default avg +8 inside the fn) · `footprint_actual` only when basis=='confirmed'.
- **Site 2 (`:4742`)** — actual-age cost for the (b18-demoted) trim sensitivity:
  fires only on `age_source=='user'`, with `eff = max(user, system)` (`:4741`).

**The decisive nuance (corrects one recon-agent claim):** within the guarded block the cost value is
**computed for EVERY valued villa/house regardless of method** — including the clean bracket — but it is
**EMITTED into the response only when a branch fires** (`cost_triangulation` on b11 · `cost_floor` inside
`old_stock_reanchor` on b16 · `age_sensitivity` on the demoted trim). On a clean-bracket villa the DRC is
computed and **discarded silently**. "Universal three-value display" is therefore mostly an **emission**
change on villa/house, not a computation change.

### §1.2 Per-path matrix (computed? emitted? why)

| path | DRC computed? | DRC emitted? | guarding condition (measured✓) |
|---|---|---|---|
| villa/house clean bracket (`comparison_bracket`) | ✅ (site 1) | ❌ | `method not in _COST_REANCHOR_METHODS` (`:5511`) — all cost branches skip; figure discarded |
| villa/house thin / widened / widened_indicative / preliminary | ✅ | ⚠️ only if a branch fires | b11 needs age≥10 + over-anchored + undercut>30% (`:5508-5516`); b16 needs dominant-stratum mismatch + margin>20%; else discarded |
| villa/house dispersion-GATED (a10/a14) | ✅ | ❌ | `dispersion_gated=True` → `_cost_triangulation`/`_cost_trim`/`_osr` all return None (`:5511, :5570, :5659`) |
| villa/house income_led | ✅ | ❌ | income wins the chain (`:4775`) — cost computed then discarded |
| villa/house teardown / luxury-new (b4 opt-in) | ❌ | ❌ | block guard `:4707-4708` (mutually exclusive explicit statements) |
| villa/house refusal (`insufficient_data`) | ❌ | ❌ | block guard `:4706` — no `amount` → never computed (no land floor either) |
| **raw_land** | ❌ (by design) | n/a | **DRC ≡ land value — CONFIRMED** (`:4543-4548`): no building component; value = comparable grid / land floor; `_cost_approach_value` never invoked. Live check: PIN 74328443 → raw_land 1.2M n=73 grid ✓ |
| apartment_building / tower / compound_large (DCF/hybrid) | ❌ | ❌ | DCF fast paths (`:3840-3901`) — no RCN ladder exists for these types (villa-construction tiers only) |

### §1.3 Input gates that can silence the cost even on eligible paths (`:5455-5466`)

The cost returns **None** (silently) when ANY of: land floor unavailable (`_villa_value_floor` → None) ·
**system age None** (b9 `age_floor_years` missing) · **footprint missing** (no b10 geometry AND no confirmed
footprint). These are the real-world universality holes for a "DRC on every villa" promise.

### §1.4 Defaults policy today (matches METHODOLOGY_DRC §9 — measured✓)

| input | default | where |
|---|---|---|
| finish | **ordinary → RCN 2200** | `:5467, :5413` (caller passes 'luxury' only on `is_luxury`) |
| condition | **average → penalty +8** | `:5468, :5426` |
| floors | **2 (G+1)** | `:5460, :5429` |
| BUA | max-buildable × **0.77** (built-ratio) | `:5464, :5427` (user-confirmed footprint bypasses the ratio) |
| age | **SYSTEM (CGIS) age — E26**; user age never leads (b18 §A1) | `:4724, :4740-4741, :4930-4947` |

### §1.5 Villa/house routes that today complete WITHOUT a cost figure in the JSON

1. Clean bracket (computed, never emitted) — the largest cohort (~all reliable-bracket villas).
2. Dispersion-gated bracket/widened (a10/a14) — excluded by design.
3. Thin/widened failing a b11/b16 gate (age<10 · not over-anchored · undercut≤30% · stratum signal absent).
4. income_led (cost discarded).
5. Input-starved (no land floor / no system age / no footprint) — §1.3.
6. Refusals (never computed; also no land floor exists to display).
7. teardown / luxury-new b4 branches (block-guarded out).

### §1.6 Gaps a universal three-value stack must close (build-scope facts, no tuning)

- **G1:** emission gap (§1.1) — surface the already-computed DRC on every valued villa/house.
- **G2:** the numeric **dispersion is NOT in the response JSON** (grep of 5 live dumps = 0 keys; the
  `_stage1_dispersion_gate` dict is internal `:5115-5138`, only its effects surface). The leadership gate
  is unauditable client-side until the numeric is emitted.
- **G3:** apartments/towers/compounds have **no RCN basis** — universal DRC for them is out of scope of the
  current ladder (villa construction tiers); the directive's "universal" = villa/house + land (land ≡ DRC).
- **G4:** refusals carry no land floor — a three-value stack on refusal screens has nothing to show; keep refusals refusals.
- **G5:** `subject_property` in `stock_strata` is **null** (R7 — subject stratum unclassified); stratum-match
  needs the E26 system-age band as the subject-side proxy (operationalized in §2.2).

---

## §2 — Flip-rate measurement (the decisive number)

### §2.1 Cohort + method

**22 live cases** (POST `/api/evaluate`, browser-UA curl per #61, 45s timeout, ≥7s spacing, zero retries needed;
**51/835/17 excluded** per the standing rule). Stratified: the 4 legacy anchors + V001 + the 8-villa b16 old-stock
cohort (zones 51/53/54/55, E24 cliff) + V002/V003 (new-premium, re-surveyed) + 56/565/19 (multi-QARS sibling) +
4 diverse (70/300/25 · 53/240/12 · 61/875/20 · Lusail 69/255/75 + 69/329/20) + raw land PIN 74328443.
Raw dumps: `.p0_cases/*.json` (untracked, regenerable). One probe defect found+fixed: `pin` must be a **string**
(int → 422) — the land case was re-run correctly.

Outcome mix: **13 valued villa/house** + 1 valued land + 2 hybrid-apartment (amount=None) + 6 refusals.
The flip percentages below are over the 13 valued villa/house cases.

### §2.2 Operationalization (stated so the numbers are reproducible)

- **today's leader** = from the live response (income_triangulation / old_stock_reanchor / cost_triangulation
  / else market-`method`). measured✓
- **matched-stratum effective n** = `stock_strata.strata[expected_band].n` from the live response, where the
  subject's expected band derives from the **E26 system age**: ≥10y (or vintage_capped at ≥10y) → OLD
  (= `land_priced`+`aging_stock` pooled n) · 2–10y → `modern_stock` · <2y → `luxury_new`. measured✓ (live) + assumed~ (the band mapping itself — G5).
- **dispersion** = the production `build_reference(...)` → subject-bracket `ppm2_dispersion_36` computed
  locally over `moj_weekly.csv` through `resolve_moj_area_name` (a18 sibling pooling + overrides) — the same
  metric the a14 gate uses. measured✓-local (E14: production functions, not re-implementations).
- **stratum match** = dominant pool stratum (`stock_strata.dominant_stratum`) ∈ the subject's expected band;
  strata absent / dominant None → **unknown → fail-safe to cost-led** (per the directive's else-branch).
- **proposed leader** = market iff [matched n ≥ 10] AND [disp < 0.30] AND [stratum match] ; else COST
  (income precedence unchanged — no live case was income_led, the no-rent reality).

### §2.3 The flip table (13 valued villa/house + land; refusals/hybrid listed for path coverage)

| case | district | sys-age (basis) | method today | amount | matched-n | disp36 | dominant (share%) | match | **today's leader** | **proposed** | cost-led figure (default DRC: ord+avg+sys-age) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 56/565/21 أبو هامور | بو هامور | 15 (vintage) | bracket | 2,400,000 | 22 | 0.208 | aging (70.8) | ✓ | market | **market** | (cost 2,194,070 — context) |
| 56/565/19 (شقيقة) | بو هامور | 15 (vintage) | bracket | 2,400,000 | 22 | 0.208 | aging (70.8) | ✓ | market | **market** | (2,194,070) |
| V002 56/565/10 | بو هامور | 0 (re-survey) | bracket | 2,500,000 | 22* | 0.208 | aging (70.8) | ✓* | market | **market**\* | (2,263,592) |
| V003 56/565/12 | بو هامور | 0 (re-survey) | bracket | 2,400,000 | 22* | 0.208 | aging (70.8) | ✓* | market | **market**\* | (2,263,592) |
| مريخ 54/541/6 | مريخ | 17 (vintage) | thin→**OSR** | 3,400,000 | 3 | 0.165 | luxury_new (51.7) | ✗ | **OSR central (3.4M)** | **cost** | **2,378,094** |
| المعراض 55/296/13 | المعراض | 17 (vintage) | thin | 2,600,000 | 7 | 0.492 | land_priced (62.5) | ✓ | market | **cost** | **3,741,570 ⚠ فوق السوق** |
| V001 56/647/6 | المعمورة | 17 (vintage) | widened | 3,800,000 | 1 | 0.440 | modern (80.0) | ✗ | market | **cost** | **3,119,090** |
| 51/825/22 | الغرافة | 17 (vintage) | bracket (a14-gated) | 2,800,000 | 22 | 0.346 | modern (45.0) | ✗ | market (honest-range) | **cost** | ~2,755,482 † |
| 51/833/37 | الغرافة | 16 (vintage) | bracket (a14-gated) | 4,100,000 | 14 | 0.428 | modern (38.7) | ✗ | market (honest-range) | **cost** | ~2,996,906 † |
| 53/736/4 | معيذر 53 | 16 (vintage) | bracket (a14-gated) | 3,000,000 | 14 | 0.446 | aging (36.4) | ✓ | market (honest-range) | **cost** (disp) | ~2,501,384 † |
| 54/788/10 | مريخ-class | 17 (vintage) | thin + b11 floor | 3,000,000 | 0 (absent) | n/a | absent | ? | market central + cost floor | **cost** | **1,103,260 ⚠ هبوط كامل** |
| 55/1056/60 | — | 17 (vintage) | thin + b11 floor | 2,700,000 | 0 (absent) | n/a | absent | ? | market central + cost floor | **cost** | 1,674,798 |
| 55/1044/63 | — | 17 (vintage) | preliminary | 2,700,000 | 0 (absent) | 0.132 | absent | ? | market | **cost** | 2,079,723 |
| أرض PIN 74328443 | الخور | n/a | bracket (land) | 1,200,000 | n/a | n/a | n/a | n/a | market (grid n=73) | **market (DRC≡land)** | ≡ land |
| 52/903/90 · 61/875/20 · 69/255/75 · 69/329/20 · 70/300/25 · 53/240/12 · 53/541/48 · 54/793/92 | — | — | refusal / hybrid(None) | None | — | — | — | — | refusal | **refusal (unchanged)** | none (no land floor) |

\* variant-sensitive — see §2.4-B. † land floor absent from the response (a14-gated path skips the a17 gate →
no `value_floor`); land floor recomputed locally via the production land-category medians (F1 logic), tagged ~.

### §2.4 Headline numbers + threshold sensitivity (numbers only — no tuning)

| classification | cost-led | flip vs today |
|---|---|---|
| **T (n≥10, disp<0.30) — the directive's gates** | **9/13 = 69%** | **8/13 = 62%** flip market→cost (المعراض، V001، 51/825/22، 51/833/37، 53/736/4، 54/788/10، 55/1056/60، 55/1044/63) + مريخ OSR→cost |
| sensitivity n≥8 (disp<0.30) | 9/13 = 69% | identical set |
| sensitivity disp<0.35 (n≥10) | 9/13 = 69% | identical set |
| sensitivity n≥8 + disp<0.35 | 9/13 = 69% | identical set |
| **variant B — re-survey fail-safe** (vintage_capped + sys-age<2 → band unknown → cost): V002/V003 flip | **11/13 = 85%** | +2 flips |

**The sensitivity is FLAT**: every cost-led case fails ≥2 gates simultaneously (or fails stratum-match, which
thresholds don't touch), and every market-led case passes all three with margin. The classification is robust
to ±2 n / +0.05 disp perturbation. The ONLY moving fork is the **subject-band operationalization** (variant
A 69% vs variant B 85%) — a Gate-2 wording decision, not a threshold decision.

### §2.5 What the flip table exposes (decision-relevant, with numbers)

1. **مريخ subsumption fork.** Today b16-OSR leads at 3.4M (basis = geo-full estimator 5,567/m², n=51 —
   an UNSTRATIFIED full-window pool). Under the strict "matched-stratum n" gate this pool does NOT count
   (matched aging n=3) → cost leads at **2,378,094**. If the geo-full pool is accepted as "matched", مريخ
   stays ~3.4M. **Δ ≈ 1.0M on the flagship case** — must be signed explicitly.
2. **⚠ المعراض inversion (E25 rail breach).** Cost 3,741,570 **> market 2,600,000** (land-anchored case:
   land floor 2.67M ≥ median). A cost-LED range `[land_floor … cost]` would sit **ABOVE** the market median —
   cost would act as an upward proxy, violating E25 (*cost is a FLOOR, never a market proxy*). The brief adds
   a hard rail: **cost never leads UPWARD** (when cost ≥ market median → keep market lead + land-anchored
   disclosure, today's behavior).
3. **54/788/10-class full down-re-anchor.** Proposed range [964,352 … 1,103,260] vs today's muted-market
   [1.1M … 3.0M]. The proposed `[land_floor … cost]` range shape **drops the market median entirely** —
   a much stronger move than b11 (which keeps market as the muted high). Range-shape = signed fork §11-F3.
4. **a14-honest-range cohort flips.** Today dispersed bracket pools show the honest P25–P75 range with the
   market median retained; the proposal **inverts** the current `dispersion_gated` exclusion (dispersed →
   cost-led instead of market-honest-range). 3/13 cases are this class.
5. **Strata-absent cohort** (54/788/10, 55/1056/60, 55/1044/63): no dominant-stratum signal → fail-safe
   cost-led. If the PO prefers "strata absent → keep today's treatment", the rate drops 9/13 → 6/13 = 46%.

### §2.7 — FINAL recompute under the SIGNED rule-set (adjudication v2, 2026-06-11 — local arithmetic, zero live calls)

Anas signed (partial): E25 rail + double-weak clause · F1 = amended unified rule (RULE 1 matched n≥10/disp<0.30/match
→ market; RULE 2 unmatched geo-full at the reliable bar n≥20 AND disp(geo-full)<0.30 → market + disclosure + MUC+1 +
cost floor; else cost) · F2=B · F3=(b) · F4=FLIP · F5=fail-safe COST. **F6 (the binding number) reserved.**
Geo-full pool stats computed via the production filters of `subject_geo_full_ppm2` (a18 key + A2 built-type + A1
usage + geo bracket [0.8,1.2], FULL window) + `quartile_stats` — measured✓-local (E14). Script: `.p0_final_recompute.py`.

| case | amount | matched-n / disp36 / match | **geo-full n / median / disp** | cost (default DRC) | today | **FINAL leader** | via |
|---|---|---|---|---|---|---|---|
| 56/565/21 أبو هامور | 2,400,000 | 22 / 0.208 / ✓ | 54 / 5,189 / 0.212 | 2,194,070 | market | **market** | RULE 1 (matched) |
| 56/565/19 | 2,400,000 | 22 / 0.208 / ✓ | 54 / 5,189 / 0.212 | 2,194,070 | market | **market** | RULE 1 (matched) |
| V002 56/565/10 | 2,500,000 | re-survey (F2=B → untestable) | 54 / 5,189 / **0.212** | 2,263,592 | market | **market** | RULE 2 (geo-full + disclosure + MUC+1 + cost floor) |
| V003 56/565/12 | 2,400,000 | re-survey (F2=B → untestable) | 54 / 5,189 / **0.212** | 2,263,592 | market | **market** | RULE 2 |
| V001 56/647/6 | 3,800,000 | 1 / 0.440 / ✗ | **22 / 5,058 / 0.203** | 3,119,090 | market (widened) | **market** | RULE 2 (geo-full RESCUE) |
| **مريخ 54/541/6** | 3,400,000 (OSR) | 3 / 0.165 / ✗ | **51 / 5,567 / 0.620 → FAILS** | **2,378,094** | OSR central | **cost** | else — the OSR basis pool fails its own reliability test |
| المعراض 55/296/13 | 2,600,000 | 7 / 0.492 / ✓ | 22 / 2,644 / 0.409 | 3,741,570 | market (thin) | **market (capped)** | **E25 rail** (cost≥market) + divergence line + MUC≥high |
| 51/825/22 | 2,800,000 | 22 / **0.346** / ✗ | 75 / 4,761 / **0.385** | ~2,755,482 | market (a14-gated) | **cost** | else (F4) |
| 51/833/37 | 4,100,000 | 14 / **0.428** / ✗ | 47 / 4,441 / **0.569** | ~2,996,906 | market (a14-gated) | **cost** | else (F4) |
| 53/736/4 | 3,000,000 | 14 / **0.446** / ✓ | 113 / 4,114 / **0.356** | ~2,501,384 | market (a14-gated) | **cost** | else (F4) |
| 54/788/10 | 3,000,000 | strata absent | 0 / — / — | 1,103,260 | market + b11 floor | **cost** | else (F5 — untestable) |
| 55/1056/60 | 2,700,000 | strata absent | 3 / — / — | 1,674,798 | market + b11 floor | **cost** | else (F5) |
| 55/1044/63 | 2,700,000 | strata absent (disp36 0.132 = «وسيط خادع», n tiny) | 1 / — / — | 2,079,723 | market (preliminary) | **cost** | else (F5) |

**FINAL headline (pending the F6 signature): cost-led 7/13 = 54%** — market via RULE 1: 2 · rescued by the
geo-full clause (RULE 2): 3 (V001 · V002 · V003) · E25-rail-capped: 1 (المعراض) · cost-led: 7.
Leadership moves vs today: **4 pure flips** (51/825/22 · 51/833/37 · 53/736/4 · 55/1044/63) + **امريخ OSR→cost
(3.4M → 2,378,094, −30%)** + 2 floor→lead upgrades (54/788/10 · 55/1056/60, already cost-floored today).

**The امريخ answer (the F1 question):** the geo-full pool b16's OSR was built on = **n=51, median 5,567/m²,
dispersion 0.620** — more than double the 0.30 reliable bar → under the signed unified doctrine that pool's
MEDIAN cannot anchor a headline; the cost leads at 2,378,094 with the F3(b) range [2.38M … 5.4M-muted].

**F4/F5 interaction (one line each, as asked):** F4 — subsumed by F1 (the 3 a14-dispersed cases fail RULE 1 on
disp36 AND their geo-full pools also fail: 0.385/0.569/0.356); no separate mechanism. F5 — subsumed by F1's
else-branch («untestable»: strata absent + geo-full n=0/3/1 < 5); the F2 precedent generalizes.

---

## §3 — Calibration gate (V001 / TD-93317) — **PASS** (production functions, E14)

| check | value | vs sheet | verdict |
|---|---|---|---|
| `_cost_retention(18,'high')` | **0.64** | sheet net 1,900/3,000 = 0.6333 | ✓ (the b18 basis) |
| MV @ engine MoJ land floor 2,456,736 | **3,612,845** (bldg 1,156,109 · BUA 602.1) | 3,600,145 → **+0.35%** | **PASS ±1%** |
| MV @ bank land 2,456,345 (350/ft²) | **3,612,454** | → **+0.34%** | **PASS ±1%** |

⚠ **Standing-test basis (must be pinned in the build):** the sheet reproduces at **RAW system age 18 +
finish=high + condition penalty 0** (the E26/b18 basis — the valuer led on the CGIS age, «بحالة ممتازة»).
Through `_cost_approach_value` with the **default** condition (avg +8) the figure is **3,323,818 (−7.7%)** —
i.e. the universal-display default DRC and the calibration figure are **different bases by design**. The
standing validation test = the b18 §B reproduction exactly (already in `test_sprint_2_22_0b18.py:24-34`),
carried forward verbatim.

---

## §4 — Anchor retirement plan (the four legacy anchors + V001)

**PO directive:** the recorded expectations of the four legacy anchors are RETIRED as methodology truth;
post-ship they re-baseline as **engineering fixtures only** (fresh byte-identical guards captured AFTER ship).

### §4.1 Pin inventory (classification: [A] breaks on re-baseline · [B] input-fixture, survives · [C] calibration, KEEP · [D] doc-only)

| file | what is pinned | class | action |
|---|---|---|---|
| `.b8_smoke.py` / `.b8_e2e.py` / `.b9_e2e.py` / `.b10_e2e.py` / `.b12_e2e.py` / `.b18_e2e.py` / `.b18_recon.py` (untracked scratch) | LIVE expectations 2.4M / 5.4M / 3.4M / 2.6M / 3.8M / refusal | **[A]** | **RETIRE** (delete or regenerate post-ship — untracked, zero repo cost) |
| `test_sprint_2_22_0b18.py:24-34,67-75` | **TD-93317 sheet reproduction ±1%** + OSR synthetic math | **[C]** | **KEEP verbatim — the standing calibration test** (V001 sole anchor) |
| `test_sprint_2_22_0b14.py:19-60` | Marikh OFFLINE fixture (5.4M/1,851,260/3,548,740) + §4 invariance | [B] | survives (pure-function fixture); its premise becomes historical — rename note only |
| `test_sprint_2_22_0a17.py` / `a19.py` | 2.4M/5.4M/2.6M as predicate INPUT fixtures | [B] | survive untouched |
| `test_sprint_2p22p0a16_precapture_hardening.py:55,107` | capture fixtures (2.4M bracket · 52/903/90 refusal) | [B] | survive untouched |
| `test_sprint_2p22p0a14_bracket_honest_range.py:69` | bracket fixture 2.4M | [B] | survives |
| `test_sprint_2_22_0a21.py:53-62` | `_villa_value_floor` unit math (Maraad 2,674,350 · V001 2,456,736) | [B] | survives (pure fn) |
| `test_sprint_2_22_0b4.py:28-41` | value-floor/teardown unit math on 2.4M | [B] | survives |
| isolated chain tests `test_sprint_2_22_0b6/b7/b8/b11/b13/b16/b18` | **the CURRENT precedence-branch semantics** (income_led > ct > osr > widen + gates) | **[A-build]** | **REPURPOSE at build time** — the conditional-leadership rewire supersedes branch eligibility; each file is re-pointed to the new chain in the build sprint (not before) |
| `run_sprint_2p22p0a_suite.py` (EXPECTED_TOTAL=392) | suite count | [B] | adjust mechanically when files change |
| docs (CLAUDE.md cascade, Session_Log) | anchor narratives | [D] | historical; superseded by the post-ship close-out |

### §4.2 Post-ship re-snapshot procedure (engineering fixtures only)

1. Ship the signed methodology (its own Gate-1/Gate-2 cycle, NOT this pass).
2. Run the standard two-lane live smoke on the SAME 22-case cohort (`.p0_flip_probe.py` is the harness) →
   capture fresh per-case JSON.
3. Write the new byte-identical guard set from those captures (a fresh `.bNN_e2e.py` + smoke expectations) —
   explicitly labeled "engineering regression fixtures, NOT methodology truth".
4. The ONLY value-anchored test that survives unchanged = the V001 TD-93317 ±1% reproduction ([C]).
5. Docs-close maps old→new per anchor (one table in the build CHANGELOG).

---

## §5 — Gaps / risks carried to the brief (Rule #42)

- **R-a:** the E25 upward-inversion rail (§2.5-2) — REQUIRED before any build.
- **R-b:** subject-band operationalization (variant A vs B) moves the headline rate 69%↔85% — needs signing.
- **R-c:** the مريخ geo-full-pool question (§2.5-1) — Δ1.0M on the flagship.
- **R-d:** range shape `[land_floor … cost]` vs b11-style `[cost … market-muted]` (§2.5-3).
- **R-e:** dispersion numeric not in the response JSON (G2) — emission required for auditability.
- **R-f:** strata-absent fail-safe (§2.5-5) — 3 cases ride on it.
- **R-g:** cohort size: 13 valued villa/house cases (stratified but modest); the flip % is **indicative of
  the live mix**, not a population estimate — n cited per Rule #10/#36.
- **R-h:** the b16-cohort overlap — 8/13 valued villas come from the E24 old-stock discovery cohort (by
  design: that IS the affected segment) + the 4 bracket-clean cases (one shared cell). Municipality spread
  beyond Doha/Rayyan produced refusals (coverage gaps), so the measured mix under-represents reliable
  non-Doha cells.

*Probe artifacts: `.p0_flip_probe.py` · `.p0_flip_extract.py` · `.p0_cases/` (all untracked scratch, regenerable).*
