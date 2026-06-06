# Thammen — Claude Code Workspace Configuration

> **Project:** thammen.qa — Qatar real-estate AVM (RICS Red Book Global Standards, effective 31 January 2025 — VPGA 10 + VPS 6 + IVS 106)
> **User:** Anas (Qatari, Windows, Heroku deploy)
> **Working directory:** `C:\Thammen\deploy v2`
> **Last update:** 2026-06-01 (Sprint 2.22.0a.16 deployed — pre-activation capture privacy-hardening: UUID-only key [address-embedding valuation_id NOT stored], street/building Fernet-encrypted [gated on `CAPTURE_ENC_KEY`], 180-day retention + dormant aggregate/purge/erase, free-text `note` removed, output label «التقدير السوقي» [provisional]. Capture STILL DORMANT; additive, NO valuation-logic change; ACTIVATION counsel-gated [§8.1 PDPPL + §8.2 cross-border + gate-11 security pass]. CHANGELOG_v68 + Session_Log §20.16). **LIVE: engine `thammen-sprint2p22p0a16-precapture-privacy-hardening` · api/health 3.1.0-sprint2.22.0a.16 · Heroku v155 · commit `94075f2` · CHANGELOG_v68** (DORMANT, privacy-hardened — UUID-only key [valuation_id NOT stored; active mode returns it as capture_id; feedback FK via prediction_id], street/building Fernet-encrypted [gated on `CAPTURE_ENC_KEY`], 180d retention + dormant aggregate/purge/erase, `note` removed, label «التقدير السوقي» [provisional]. SHA-of-enumerable REJECTED → Operational #62. Two-lane smoke v155 BYTE-IDENTICAL on the 4 anchors [2.4M/4.5M/2.6M/refusal; NO capture_id → dormant]; `/api/feedback {prediction_id}` → {accepted, stored:false}; `note`/`valuation_id` → 422. ACTIVATION counsel-gated [§8.1 PDPPL + §8.2 cross-border + gate-11 security pass: verify Fernet round-trip on Heroku + short PG backup retention + backup-erasure runbook]. Isolated 26/26 + DoD 392/15/45/58; origin in sync `94075f2`. **Prior: Sprint 2.22.0a.15 — beta instrumentation (DORMANT)** (DORMANT — capture writes NOTHING until BOTH `EVAL_CAPTURE_ENABLED=true` AND a counsel-cleared Postgres exist; two-lane post-deploy smoke [CC browser-UA curl + Anas] BYTE-IDENTICAL on the 4 anchors: 56/565/21 = 2,400,000, 54/541/6 = 4,500,000, 55/296/13 = 2,600,000 comparison_thin n=8, 52/903/90 = refusal; `/api/feedback` dormant → {accepted, stored:false}; extra field → 422. ADDITIVE BACKEND — NO valuation-logic change. ACTIVATION counsel-gated [§8.1 PDPPL + §8.2 cross-border]; add-on NOT provisioned [RISK_REGISTER R11]. Tooling: CC POST smoke = browser-UA curl, Cloudflare 1010 blocks urllib [Operational #61 / R12]. Isolated 27/27 + DoD 392/15/45/58; origin in sync `8d6f304`. **Prior: Sprint 2.22.0a.14 (vi) — bracket honest-range + window disclosure** (USER-VISIBLE: 20 of 37 reliable villa bracket cells [7 a13-rescued + 13 pre-existing] were dispersed yet showed as clean reliable points — they now get the honest-range/🟡 indicative/MUC treatment; anchors stay clean [Abu Hamour disp 0.208, Marikh 0.197 < 0.30]. Live smoke v153 4/4: Abu Hamour 56/565/21 = 2,400,000 [value IDENTICAL, NOW «(نافذة 36 شهراً)» + window_used «37 معاملة، منها 28 خلال 24 شهراً» → CHECK-3 closed on the anchor], Marikh 54/541/6 = 4,500,000 [unchanged, widened range-headline], 55/296/13 = 2,600,000 comparison_thin n=8 [unchanged, not gated], 52/903/90 = refusal. **R10 generalized → CLOSED-by-a14** [bracket path had no dispersion gate; 20 dispersed reliable cells = 7+13]. Boundary: 3 cells within ±0.006 of T=0.30 may flip on a MoJ refresh [expected, not a regression — hysteresis if it bites]. Known-minor: window suffix fires on `comparison_bracket` only, not `comparison_thin` [thin already caveated]. Fast-follow: a DIRECT live hit on a gated bracket cell [الغرافة/العب 600-900] — gate DECISION proven offline e2e + threading/application proven live. Isolated 19/19 + DoD 392/15/45/57; origin in sync `78ffd9b`. **Prior: Sprint 2.22.0a.13** — thin-cell credibility (Heroku v152, `c366d66`, CHANGELOG_v65; USER-VISIBLE: thin villa bracket cells now borrow their OWN 36mo comps via credibility shrinkage instead of the dispersion-prone widened path — +10 cells upgrade thin→reliable, reliable cells move ~0% [max 2.2%], <5 floor preserved, ppm² untouched. Live smoke v152 4/4: Abu Hamour 56/565/21 = 2,400,000 [IDENTICAL to a12; comp count 28→37 via n36 tiering], Marikh 54/541/6 = 4,500,000 [byte-identical — A16-starved bracket → geo path, NOT shrunk], 55/296/13 = 2,600,000 comparison_thin n=8 [no upgrade, gentle ~−4%], 52/903/90 = refusal; api/health a13/v152. **OPEN — R10 temporary honesty gap:** 7/10 rescued cells are dispersed [ppm² ≥0.30] yet present as clean `comparison_bracket` reliable points with no honest-range; AND CHECK-3-live: the bracket SUCCESS `source_ar` discloses NO window for ANY villa cell [Abu Hamour «وسيط 37 معاملة» spans up to 36mo, undisclosed]. **NEXT = (vi) URGENT** [bracket-success surface only, presentation/copy, NO value change: (a) extend the a10 dispersion honest-range to the bracket path → closes R10; (b) disclose 24-vs-36mo window basis in source_ar when n is a 36mo count → closes CHECK 3, Gate-2 copy sub-decision]. Isolated 16/16 + DoD 392/15/45/56; origin in sync `2bfec00`. A16 = still the only Marikh lever [R9, own sprint after a live trace]; A7 still open; LAND bracket path unchanged [villa-only]. **Prior: Sprint 2.22.0a.12** — A2 built-type stratification (Heroku v151, `9fa375c`, CHANGELOG_v64; USER-VISIBLE: villa comparable pool is now PURE-villa — house [بيت/مسكن], فيلتان [−6 to −10% discount product], and compound rows removed → pooled villa ppm2 median ~+9.7%; net A1+A2 ~+4.5% above the original contaminated median. HEADLINE effect VARIABLE: reference anchors STABLE [Abu Hamour 56/565/21 = 2.4M, Marikh 54/541/6 = 4.5M] because the bracket headline uses the robust TOTAL-PRICE median [removed house rows weren't at the median position]; anchors' under/over-valuation = CONDITION → Sprint B, not stratification. **Subject side CANNOT distinguish HOUSE from VILLA** [QARS subtype 1 = "Villa/House", no HOUSE AssetType] → house subjects pool as standalone_villa [live-confirmed 55/296/13]; house-subject fix DEFERS to B. DRY `built_type.py` at both comp sites, composes with A1 usage filter; `categorize`/`_categorize` KEPT for the out-of-scope `compute_trend` + geo non-villa categories [Rule #39]. Isolated 28/28 + DoD 392/15/45/55; live smoke 4/4 [incl. `comparison_thin n=8` proving graceful thinning]; origin in sync `9fa375c`. **NEXT = window-fallback 36mo-cap + light shrinkage** [recon F: 36mo captures ~half the +8-13% staleness drift]. Prior: Sprint 2.22.0a.11 — A1 residential-usage filter on the villa comparable pool (Heroku v150, commit `ec0d1b9`, CHANGELOG_v63; villa headlines shed non-residential-usage comps [~+101%] → villa median ~−4.75%; 56/565/21 → 2.4M [contamination removal, condition-blind, ~2.5–2.8M with-condition pending B]; isolated 13/13 + DoD 392/15/45/54; §20.11). Prior: Sprint 2.22.0a.10 — Stage-1 honest range (USER-VISIBLE: widened villas with a dispersed comp pool now show an indicative P25–P75 range + lowered tier + widened MVU + AR/EN disclosure, the median retained as the central estimate; `_stage1_dispersion_gate` T=0.30 on the geo_value widened paths — live Marikh 54/541/6 → 3.3–5.4M indicative, Maamoura 56/647/6 → 2.9–4.4M indicative, Abu Hamour 56/565/21 bracket = 2.5M unchanged; backend-only, no index.html; isolated 16/16 + DoD 392/15/45/53; origin in sync `21c5fe3`. **Built-type/condition blindness [RISK_REGISTER R7] is BIDIRECTIONAL & affects BOTH paths** — over-anchors below-avg-condition [54/541/6 widened, RE-OPENED], under-anchors above-avg-condition [56/565/21 bracket → defensible ~2.5–2.8M, NOT the 2.5M point]; a10 = necessary-NOT-sufficient, real fix = Gate-2 (c) built-type stratification via 2.22.0b Stage-2 Q&A). Prior: Sprint 2.22.0a.9 — widened-path age/quality elasticity, facet a (Heroku v148, CHANGELOG_v61; the geo_value widened headline applies the age/quality slice clamped ±0.10; the a9 ship-time 681≈682/ft² "match" was **later OVERTURNED** — coincidence, 54/541/6 RE-OPENED, §20.10.1 / R7). Prior: Sprint 2.22.0a.8 — RICS/IVS 2025 citation correctness (Heroku v147, commit `1e07a2a`, CHANGELOG_v60): added the AVM models standard VPS 5 / IVS 105 + AVM-not-standalone disclosure on a secondary collapsible surface [the 2.22.0a.4-deferred surface]; remapped ALL stale citations — approaches VPS 4→VPS 3 / IVS 103, HBU→VPS 2 / IVS 102 [genus, triple-confirmed], scope→VPS 1, VPN 13→VPGA 10 [D5 widened]; bare `methodology_ar` untouched; copy-only — valuations unchanged [villa 56/565/21 = 2.5M = v101]; regression 392/15/45/51 + 43/43; origin in sync `b560920..1e07a2a`). Prior: Sprint A14 lever 2 — geometric_factors parallelized, **A14 CLOSED** (Heroku v146, CHANGELOG_v59, cold villa 200 @~15s, was 503@31s; lever 1 deferred + H_A-cleared/ready). The production-state snapshot block below + Session_Log §20 are authoritative. Prior: 2026-05-29 Sprint 2.22.0a.4 — Disclosure & Framing Honesty (Heroku **v140**, commit `f7870a3`, CHANGELOG_v55; engine `thammen-sprint2p22p0a4-disclosure-framing-honesty`). `methodology_ar` → universal bare line «أساس التقدير هو منهج المقارنة بالمبيعات.» (dropped «توفيق ثلاثي الطرق» + Latin); main-path Layer A fold (6→5, 5 genuine caveats preserved); D/C4 canonical from 2.22.0a.2 untouched. Multi-AI Rule #54 (GPT-5+Gemini) Path A bare-line. Live smoke villa 56/565/21 (200 on A6 retry @22s) + apt 52/903/90 PASS. **Arabic-Surface arc since 2.21.4:** 2.22.0a (v50) → a.1 QARS fallback (v51/Heroku v132) → a.2 content fixes (v52) → 2.16.17 security (v53) → a.3 honesty (v54/v139) → a.4 framing (v55/v140). Full bridge + deferred items in Session_Log §18. **NOTE:** the production-state snapshot block below predates the 2.22.0a arc — trust the four updated lines there + Session_Log §20.x (current: §20.15) over the older body until a full snapshot rewrite.)

## Quick orientation

Read these files in order before any technical work:

@./docs/Project_Instructions.md
@./docs/Session_Log.md
@./docs/Empirical_Findings.md
@./docs/Custom_Instructions.md
@./docs/Session_Update_2026-05-19.md
@./docs/Operational_Rules.md

**Most recent state: see the LIVE header (top) + the production-snapshot block + Session_Log §20.15 — current = a15 / Heroku v154; the 2.21.x notes below are historical. Full hybrid arc complete:** Sprint 2.21.2
(foundation, v107) → Sprint 2.21.3 (T2 PF Lusail apartments, v124) →
Sprint 2.21.4 (T3 Aryan/City Avenues + status-aware hybrid, v125). Live
H_WALK PASS for H1 + H11 + H2 (kill switch). H10 UI rendering deferred
to Sprint 2.21.5. Session_Log §15 still holds the most recent NARRATIVE
(Sprints 2.18.1 + 2.18.1.1); §16 (the hybrid arc 2.21.2 → 2.21.3 →
2.21.4) added 2026-05-25. Pre-Sprint artifacts since:

- `2p21p1_pre/CHANGELOG_pre_2p21p1.md` — MME smoke (anonymous Directus
  token, kpi29 schema discovered, rent paths verified dead). Sprint 2.21.1
  deferred pending DevTools capture.
- `2p22p0_pre/CHANGELOG_pre_2p22p0.md` — 3-stage architecture exploration
  audit. H5 FALSE: apartments are a data problem, not latency. Sprint
  2.22.0 deferred. H1+H3+H4 evidence preserved for future UX-refactor Sprint.
- `2p21p2_pre/` — Sprint 2.21.2 §5 audit probes (MoJ Lusail apt count = 0,
  PropertyFinder reachable, arady root only). Sprint 2.21.2 then shipped.
- `2p21p3_pre/CHANGELOG_pre_2p21p3.md` — T2 connector smoke from Heroku.
  4 of 5 TRUE. arady canonical search = `/listings`. PropertyFinder DOM
  duplicates listing nodes ~6× (raw 142 → 24 unique on Lusail page 1) —
  connector MUST deduplicate by canonical URL or listing ID.

§14 covered Sprint 2.18.0 earlier that morning; §13 covered Sprint 2.21.0.9
Stage 1; §11-12 covered the Land Arc through Sprint 2.21.0.7.1. The
`Session_Update_2026-05-19.md` file is an older delta (Bug A11 era) kept
for history. Newest operational rules: `Operational_Rules.md` #43–#61
(latest written = #61 "CC post-deploy POST smoke = browser-UA curl, not urllib"; #55/#56 reserved-pending).
Newest empirical rules: `Empirical_Findings.md` E13–E23 (Rule E3 itself
expanded to 8 numbered constraints by Sprint 2.21.2 — listings now allowed
tier-weighted entry via `hybrid_valuation_v1()`).

-----

## Current production state (snapshot)

> **🧭 CURRENT STATE + NEXT STEP (Rule #65a — CC maintains; read first at the #57 handshake):**
> - **Live:** Heroku **v165** · engine `thammen-sprint2p22p0b1-geometry-zoning-footprint` (b1 = zoning-driven ground-footprint suggestion + **basement excluded from the comparison driver** [geometry §5.2/§5.5, **value-invariant on no-building-input anchors**]; a25 = CC BY 4.0 MoJ source-attribution footer credit; a24 = beta consent **entry gate** + Terms/Privacy + DPIA; a23 = R15 strata-land a18) · capture **DORMANT** · `master == origin` but **AHEAD of Heroku** (b2 built + committed origin-only, **Gate-1 push pending**; Heroku still **v165 / b1** `4b39ba2`; read live via #57).
> - **Operating Model v2 (lean) ADOPTED 2026-06-02** → `docs/OPERATING_MODEL_v2_lean.md` (classes-of-service Fast/Full/Gated; C1 = doc-delta committed before build routing).
> - **Engineering = ACTIVE on signed briefs (#32)** — last shipped **b1** (Sprint 2.22.0b.1 — zoning-driven ground-footprint suggestion [QNMP R1=60/R2=50, ×0.8, **capped at the legacy default → no silent inflation**] + **basement EXCLUDED from the comparison driver** [§5.5 — captured/displayed + future-DRC input, NOT a sales-comp premium; was +11.5% on a25] + assumed-vs-confirmed MVU labelling; **value-invariant on no-building-input anchors — only changes when the user supplies geometry**; recon RESHAPED the signed brief [§6 /quick-add was dead: the frontend posts to `/details`; basement-separate + floors-above-ground already held] → **3 deltas + augment-existing-panel**; backend localized to the substantiality stage [zone-aware `subst_bua` with `basement=False`, reuses already-fetched zoning → **zero extra GIS**]; `api.py` UNTOUCHED; Heroku **v165**, commit `4b39ba2`, CHANGELOG_v79, §20.29; isolated 34/34 + DoD 392/15/45/67 + R14 real-Chromium [0 console errors, 390×844 no overflow] + **local E2E on the real engine** [caught & fixed a §5.2 large-plot inflation edge]; live smoke v165 **4 anchors byte-identical** [2.4M/5.4M/2.6M/refusal] + **basement-excluded LIVE** [fl3 ≡ fl3+basement = 2.8M] + fp-cap [600→540 → 2.9M] + geometry surfaced). Prior **a25** (CC BY 4.0 **source attribution** for MoJ data — a persistent verbatim AR+EN credit [+ licence link → creativecommons.org/licenses/by/4.0/] in the results footer where derived MoJ figures appear; **user-facing copy / compliance hygiene — NO methodology/valuation change, value-invariant, every headline + B-1 `value_floor` byte-identical**; bidi `dir="ltr"` islands on `data.gov.qa`/`4.0`/`CC BY 4.0` per a24; confirmed the engine ingests `weekly-real-estates-sales-bulletin`; **closes COMPLIANCE Q13 + the open-data sub-item of RISK_REGISTER R13** [licence verified CC BY 4.0 = commercial+derivatives+redistribution OK w/ attribution]; `api.py` UNTOUCHED; Heroku **v164**, commit `d9d148a`, CHANGELOG_v77, §20.25; R14 real-Chromium [credit renders, 390×844 + desktop no-overflow, dir rtl/ltr islands measured, JS unchanged/0 console errors] + DoD 392/15/45/66; live v164 **ZERO value drift** [2.4M/5.4M/2.6M/refusal] + credit live in served HTML). Prior **a24** (beta-launch onboarding + affirmative-consent **entry gate** + **Terms/Privacy notice** + **DPIA** — content/frontend + a doc, **NO valuation logic, every headline + B-1 `value_floor` byte-identical**; gate is session-only [`sessionStorage` + in-memory fallback, **no cookie, no server write, stores nothing**; returning-within-session skips it, new session re-shows], Terms modal verbatim [7 AR + 7 EN] linked from gate/home/results-footer; **§4: scrubbed the property address from the two `/api/evaluate*` INFO logs** to back the DPIA "we don't store the address" [client IP kept for ops]; `docs/DPIA_AI_impact_beta_v1.md` committed verbatim; Heroku **v163**, commit `d538e93`, CHANGELOG_v76, §20.24; R14 **real-Chromium** [0 console errors, 390×844 + desktop no-overflow, RICS/IVS + 2025 + phone + Heroku-وCloudflare bidi all measured correct] + DoD 392/15/45/66; live v163 **ZERO value drift** [2.4M/5.4M/2.6M/refusal] + apartment refusal renders clean). Prior **a23** (R15 — `stock_strata.compute_land_median` now pools areas via a18 `area_match_key` like the floor → strata-card land **sibling-drop removed** [المعمورة 4032→3754 ≈ floor 3768]; **Gate-2 DISPLAY, HEADLINE value-invariant** — every headline + the B-1 `value_floor` byte-identical, bracket-matched anchors unchanged [E4 by-design, not sibling-drop — Rule #36 refinement]; `api.py`+`index.html` UNTOUCHED [R14 N/A]; Heroku **v162**, commit `ff483b0`, CHANGELOG_v75; a23 12/12 + DoD 392/15/45/66; audit `docs/PHASE0_R15_stock_strata_a18.md`; **RISK_REGISTER R15 → RESOLVED**). Prior **a22** (B-1.1 multi-AI-validated framing tweaks — **value-invariant, RICS/IVS citations UNCHANGED**: land floor → «indicative land component on an HBU premise», implied building → «contribution / mathematical allocation», widened `method_label` → «منهج المقارنة بالمبيعات (مجموعة موسَّعة جغرافياً)»; the models' 2025-renumbering "fixes" were REJECTED by Claude.ai primary-source adjudication [→ Rule #54 refinement: web-check GATES multi-AI on standards numbering]; `api.py`+`index.html` UNTOUCHED; Heroku **v161**, commit `2d401b5`, CHANGELOG_v74; a21 33/33 + a22 15/15 + DoD 392/15/45/65; R14 Chromium 390×844 re-measure clean; live v161 ZERO value drift + citations VPS 3/IVS 103/VPS 2/IVS 102 unchanged). Prior **a21** (B-1 land-floor / HBU decomposition + condition surfacing — **PRESENTATION ONLY, NO valuation logic, every value byte-identical**; surfaces a villa/house `value_floor` block [land-value FLOOR + implied-building residual + land-anchored disclosure] next to the a17/a19 condition caveat via new `evaluate_unified._villa_value_floor` [F2-prefer `value_decomposition.land`; F1-recompute `land_ppm²×plot` from the `moj_reference` land category **INDEPENDENT of Patch-C** → surfaces for the land-priced cohort ~10%/0%-reliable where `_decompose_value` returns None, implied clamped ≥0]; rides the `_condition_note_applies` gate [Rule #39: placed at the decomposition site, not the literal a14 block]; brief MU + muted `.rn` render; `api.py` UNTOUCHED; Heroku **v160**, commit `62f902a`, CHANGELOG_v73, §20.21; isolated 33/33 + DoD 392/15/45/64; **R14 EXECUTED** [real Chromium whole-file JS syntax + 390×844 overflow, node absent]; live smoke v160 **ZERO value drift** [56/565/21 2.4M, 54/541/6 5.4M, 55/296/13 2.6M land_anchored, 56/647/6 3.8M floor 2.46M, 52/903/90 refusal]). Prior **a20** (A7 `rics_compliant` honest status label — DISPLAY/LABEL ONLY, **NO valuation logic, every value byte-identical**; adds a neutral companion `rics_compliant_status_ar/en` = «بانتظار مراجعة مُقيِّم مُرخّص (المرحلة الخامسة)» / «Pending licensed-valuer review (Stage 5)» next to the `rics_compliant` bool on every JSON surface [root MU via `_enrich_material_uncertainty` + main-path 4714; brief MU section via output_briefs 595/933] so bare `false` reads "review pending," not "non-compliant"; emitted ONLY when bool is False [True/hybrid → no status; None → pending fail-safe]; bool + the `if not rics_compliant` recommendation [material_uncertainty.py:385] UNTOUCHED; recon: the bool **renders nowhere** in index.html [MU case ignores it; generic dumps skip booleans] → **backend-only**, `api.py`+`index.html` UNTOUCHED [R14]; wording verbatim-matches the live `rics_methodology_note`; Heroku v159, CHANGELOG_v72, §20.20; isolated 20/20 + DoD 392/15/45/63; live smoke v159: 56/565/21 = 2.4M, 54/541/6 = comparison_thin 5.4M, 52/903/90 refusal — all byte-identical + status_ar PRESENT). **Engineering NEXT (canonical):** Sprint **2.22.0b.2** (guided 3-stage input flow — **frontend only, NO backend change**; consumes b1's geometry surface) = **Gate-2 DRAFT awaiting Anas's signature** (Gate-2 **SIGNED** + saved `docs/BRIEF_Sprint2p22p0b2_staged_input_flow_SIGNED.md` `21f2e53`; **BUILT + DoD-GREEN, HELD at Gate-1 push** [awaiting Anas's consent] — WRAP staging of the existing form into an explicit revisable Stage-2 confirm [«حسّن التقدير (المرحلة 2)» inline floors/footprint/basement → re-POST `/details` via `window._lastSubmit`] + backend `effective_footprint_m2` [brief F3 — the post-cap footprint the comparison used, value-invariant; F2 gates the confirm to villa/house, excludes raw_land/refusal]; isolated 22/22 + b1 34/34 + DoD 392/15/45/**broad 68/68 clean** + local E2E value-invariant [2.4M/2.9M, effective 540] + R14 390×844 0-errors/no-overflow; CHANGELOG_v80, §20.31; **engine code = b2 but Heroku still v165/b1 until the push**; F5 §2b authority/finality dial-down → separate **b.3** [multi-AI], **B-2 PARKED**). Other near-term: (a) Anas's beta go-call (cohort + 6/2 path); (b) instrumentation activation — gated on Anas's DB-residency (Q3/Q4) + free-text (Art-16) decisions, then CC's gate-11 capture-surface security pass. Sprint **B-2** (R7 built-type/condition mechanism) is **Gate-2 SIGNED 2026-06-05** — two levers [UP finish/new-build premium on comp ppm² · DOWN 10-Year-Rule land re-anchor reusing the a21 `_villa_value_floor`], **Fork#1=MODERATE** (Lever-2 re-anchor: floor +0–10%, luxury-finish exception → floor +~20%, wide MUC), **Fork#2=WAIT-for-n≥20**; framing Rule-#54 web-checked (VPS 2 / VPGA 10 / IVS 102 ✓; stated condition = assumption+MVU, NOT a Special Assumption; +IVS 104) + §5-audited [DECISIVE: local `luxury_new` E4 stratum **n=0** in BOTH motivating areas → Lever 1 must be **corpus-calibrated** (cross-area GT-2), NOT a per-area MoJ lookup; Lever 2 **data-ready** (land floor n=20–33)]. **PARKED — resume trigger = Confirmed-Sales GT-2 corpus n≥20** (2.16.16, beta-fed). Brief `docs/BRIEF_SprintB2_mechanism_elicitation_SIGNED.md` · recon `docs/PHASE0_B2_condition_recon.md` · §20.27. (B-1 disclose-only already shipped; **Stage-1 input-honesty sprint CLOSED — premise falsified**, CHANGELOG_v78/§20.26.) **MULTI_AI batch decision-record COMMITTED** (`docs/MULTI_AI_VALIDATION_BATCH_SprintB1.md` — LOCKED outcomes from brief §2 D3; only the optional raw GPT-5/Gemini transcript pending Anas paste); non-blocking flags = PDF-prominence (brief §7) + R15 + a18 sub-zone live hit. **Bidirectional R7 now MEASURED + CONFIRMED:** **V002/V003** = project's FIRST **GT-2 confirmed sales** (56/565/10+12 Abu Hamour, NEW premium villas **SOLD 4.0M** each, engine 2.4–2.5M = **−37/−40% UNDER-anchor**) + **V001** Maamoura 56/647/6 (old premium, OVER-anchors the rejected 3.8M ask) — `docs/validation/VALIDATION_LOG.md`. **Confirmed-sales corpus (2.16.16) REVIVING (Anas-fed)** = the calibration unblock. Discipline: n<20 → motivates, NOT calibrates; B-1 = presentation-only; a17/a19 caveat VALIDATED by V002/V003. A7 → CLOSED (label shipped; bool by-design, no rename per #47). Prior: a19 (thin-path condition caveat, v158, §20.19). Monetization still gated on the regulatory enquiry (MoJ open-data licence ✅ CLOSED a25 — CC BY 4.0 verified + attribution live).
> - **Rule-count = FROZEN** — no new Operational rules beyond #65; lean defaults live as `ROLES_AND_COMMS` conduct, not rules.
> - **Launch gating (canonical, 2026-06-05 — SINGLE SOURCE; close-out "Carried forward" sections reference THIS):** the free invited beta launches under the **2026-06-02 conservative self-clearance**. **Pre-invite requirements:** (1) decision-support framing + consent layer — **a24 ✓**; (2) CC-BY source attribution — **a25 ✓**; (3) cohort + access setup — **gate #6 (Anas), OPEN**. The **Aqarat regulator enquiry is a pre-MONETIZATION gate** (held until product design/build complete; sent before any paid access) — **NOT a pre-invite / beta blocker** (التقييم العقاري is regulated, Decision 28/2023 — licence BEFORE any paid access). **Open-data licence gate: ✅ CLOSED** (CC BY 4.0, a25). In-beta feedback flows to Anas's WhatsApp per the notice → the in-app feedback UI (Sprint 2) is **not required for the beta**. Pointers: Aqarat draft `docs/Aqarat_Enquiry_DRAFT_hold.md`; PDPPL self-clear = R11; checklist `docs/COMPLIANCE_SELF_CLEARANCE_beta_v1.md`; decision = R13. Earned gates (safety / compliance / valuation-honesty) stay; only delivery ceremony is trimmed.

> **Operating Mode (Autonomous Lead) — adopted 2026-05-29.** Supersedes the
> implicit "Claude.ai drafts → Anas signs every step → Claude Code implements"
> loop for **reversible** work only. The two hard gates below are unchanged from
> Rule #32 and the §"Self-correction triggers" STOP list — this block does not
> relax them, it scopes everything *else* to autonomous lead.

### Operating Mode — Claude Code leads

**Default: Claude Code drives the whole process and self-corrects.** Run recon,
instrument, refactor, write/fix tests, iterate locally, run smoke probes, and
**correct what is wrong as you find it** — without round-tripping to Claude.ai or
waiting for a sign-off — for anything **reversible**. "Reversible" = revertable by
a single local edit or redeploy, with no change to user-facing output and no
production state left behind.

Three gates remain. They are not velocity drag; each has documented scar tissue.

#### 🔴 HARD GATE 1 — Production push to Heroku
Never `git subtree push --prefix "deploy v2" heroku master` without **explicit
Anas consent in that session**. Unchanged from Rule #32 / STOP list. A wrong push
= deploy + log churn + regression + broken Sprint atomicity — irreversible at low
cost. Before asking: state branch, tests pass (actual numbers), ENGINE_VERSION
bumped y/n, CHANGELOG present y/n.

#### 🔴 HARD GATE 2 — Methodology / user-facing output change
Any change to *what the engine returns to a user* — valuation logic, confidence
tiering, MUC, refusal/scope decisions, disclaimers, Arabic copy semantics — stops
for an Anas sign-off **before** it lands. Reason is audit, not quality: "Anas signs
all methodology decisions for auditability." An unsigned methodology change = a
broken RICS audit trail. The §9 degraded-QARS fail-soft is the live example: it
looked like "perf" but invents a new output → gated. **Test for this gate:** "would
the JSON/UI a user sees differ?" If yes → gate. If the change only moves
*when/how fast/whether-it-503s* with identical success-path output → reversible,
no gate.

#### 🟡 SOFT GATE 3 — Scope beyond the signed brief
Single-purpose discipline holds (Rule #38), but does not require a stop.
**Flag-and-proceed:** if a fix needs to step outside the signed brief, state in one
line *what* and *why* (Rule #39: why / what-is-lost / what-Anas-needs-to-know), then
proceed unless Anas objects. New genuinely-separate work → log to the deferred list
(Rule #42), don't fold it in silently.

#### Multi-AI (GPT-5 / Gemini) — sprint open only
Invoke at the **start of a sprint when needed** (evolving-standard checks,
effective-date traps, methodology framing) — this is exactly Rule #54. Not part of
the per-change loop; Claude Code does not pause mid-execution for it.

#### What this changes vs. before
- **Gone:** Claude.ai brief-review ping-pong as a precondition for routine
  reversible work, and per-step "may I?" on recon / instrumentation / refactor / tests.
- **Kept:** the two 🔴 gates (push, methodology/output), the soft 🟡 scope flag, the
  full STOP list (#33–#42, E7, A2, 51/835/17, etc. — *correctness* triggers, not
  approval gates, and Claude Code self-applies them).
- **Claude.ai role now:** sprint-open methodology framing + multi-AI when asked;
  available for review on request; not a mandatory gate on reversible work.

```
Engine version deployed:  thammen-sprint2p22p0a16-precapture-privacy-hardening
                          (Heroku v155, 2026-06-01, commits 03a4fb8 [code] + 94075f2 [label tweak]; Sprint
                          2.22.0a.16 — pre-activation PRIVACY HARDENING of the a15 dormant capture. ADDITIVE/
                          structural, NO valuation-logic change; capture STILL DORMANT. (Q1) UUID id = SOLE
                          key + join target; address-embedding valuation_id NEVER stored (display-only in
                          the response); active mode returns it as capture_id; feedback FK via prediction_id.
                          SHA-256(valuation_id) REJECTED (enumerable -> brute-forceable; Operational #62).
                          (Q2) zone PLAINTEXT; street/building Fernet-encrypted, gated on CAPTURE_ENC_KEY
                          (NULL — never plaintext — without a key). (Q3) created_at + 180d expires_at; dormant
                          aggregate_and_purge_expired -> prediction_zone_agg + DROP per-record rows;
                          erase_prediction row-level; backup erasure = activation runbook. (Q4/D1) free-text
                          note REMOVED (note OR valuation_id -> 422). (D3) 4 output labels «التقييم» ->
                          «التقدير السوقي» [provisional; mobile-shortened]. +cryptography (lazy). Two-lane
                          post-deploy smoke v155 BYTE-IDENTICAL on the 4 anchors (56/565/21=2.4M, 54/541/6=
                          4.5M, 55/296/13=2.6M, 52/903/90=refusal; NO capture_id -> dormant); /api/feedback
                          {prediction_id} dormant -> {accepted, stored:false}; note/valuation_id -> 422.
                          ACTIVATION counsel-gated (§8.1 PDPPL + §8.2 cross-border + gate-11 security pass)
                          [RISK_REGISTER R11]. origin in sync 94075f2.)
api/health version:       3.1.0-sprint2.22.0a.16
Latest CHANGELOG:         CHANGELOG_v68.md  (Sprint 2.22.0a.16 — pre-activation capture privacy-hardening.
                          instrumentation.py rewritten [UUID-only key, no stored valuation_id, street/
                          building Fernet-enc gated on CAPTURE_ENC_KEY, 180d retention, aggregate/purge/
                          erase, no note]; api.py capture_id active-only + FeedbackRequest prediction_id
                          [drops valuation_id + note]; index.html 4 labels -> «التقدير السوقي»;
                          +cryptography. Isolated 26/26; DoD 392/15/45/58 [broad 58/58 on re-run].)
Latest Sprint:            2.22.0a.16 — pre-activation capture privacy-hardening (Session_Log §20.16)
                          - capture STILL DORMANT (flag-off + no DB + no key -> zero footprint); additive, NO valuation change
                          - UUID-only key + valuation_id NOT stored (Q1); street/building Fernet-enc gated on key (Q2)
                          - 180d retention + dormant aggregate/purge/erase (Q3); free-text note removed (Q4/D1)
                          - output label «التقدير السوقي» provisional (D3); SHA-of-enumerable REJECTED -> Operational #62
                          - two-lane smoke v155: 4 anchors byte-identical; /api/feedback 200 dormant; note/valuation_id -> 422
                          - ACTIVATION gated on §8.1 PDPPL + §8.2 cross-border + gate-11 security pass (R11)
                          (full narrative: Session_Log §20.16; CHANGELOG_v68)

--- prev (2.22.0a.15, kept for reference — full detail in Session_Log §20.15 / CHANGELOG_v67) ---
Engine version deployed:  thammen-sprint2p22p0a15-eval-capture-feedback
                          (Heroku v154, 2026-06-01, sprint commit 8d6f304; Sprint 2.22.0a.15 — beta
                          instrumentation: prediction capture + POST /api/feedback. ADDITIVE BACKEND,
                          NO valuation-logic change. Shipped DORMANT: new instrumentation.py + guarded
                          capture call in both /api/evaluate* handlers + /api/feedback (FeedbackRequest,
                          extra=forbid). Capture writes NOTHING unless BOTH EVAL_CAPTURE_ENABLED=true AND
                          DATABASE_URL set -> zero data footprint; +psycopg2-binary (lazy, unused while
                          dormant). Field set data-minimized (§3): UUID id PK + valuation_id + address
                          SEPARATE/redactable (§8.3); refusals captured (§8.4); IP NOT stored. Two-lane
                          post-deploy smoke (CC browser-UA curl + Anas) BYTE-IDENTICAL on the 4 anchors:
                          56/565/21=2.4M, 54/541/6=4.5M, 55/296/13=2.6M comparison_thin n=8, 52/903/90=
                          refusal; /api/feedback dormant -> {accepted, stored:false}; extra -> 422.
                          ACTIVATION counsel-gated (§8.1 PDPPL + §8.2 cross-border) — add-on NOT
                          provisioned [RISK_REGISTER R11]. First beta-track sprint. origin in sync 8d6f304.)
api/health version:       3.1.0-sprint2.22.0a.15
Latest CHANGELOG:         CHANGELOG_v67.md  (Sprint 2.22.0a.15 — beta instrumentation. NEW
                          instrumentation.py (dormant capture/feedback, Postgres target, lazy psycopg2);
                          api.py +capture seam x2 + POST /api/feedback (extra=forbid); +psycopg2-binary;
                          ENGINE/SPRINT_TAG -> a15. Isolated 27/27; DoD 392/15/45/58.)
Latest Sprint:            2.22.0a.15 — beta instrumentation: prediction capture + feedback (Session_Log §20.15)
                          - DORMANT (flag-off + no-op without DATABASE_URL); additive, NO valuation change
                          - capture {id(UUID PK), valuation_id, zone/street/building, value, range, method,
                            tier, muc, ts}; feedback {id, valuation_id, outcome, price?, note?, ts}; IP NOT stored
                          - H1/H2/H3 verified; 4 anchors byte-identical (two lanes); /api/feedback 200 dormant
                          - ACTIVATION gated on §8.1 PDPPL + §8.2 cross-border (counsel); add-on NOT provisioned (R11)
                          - lesson: CC post-deploy POST smoke = browser-UA curl (Cloudflare 1010 blocks urllib) — #61
                          (full narrative: Session_Log §20.15; CHANGELOG_v67)

--- prev (2.22.0a.14, kept for reference — full detail in Session_Log §20.14 / CHANGELOG_v66) ---
Engine version deployed:  thammen-sprint2p22p0a14-bracket-honest-range
                          (Heroku v153, 2026-06-01, sprint commit 78ffd9b; Sprint 2.22.0a.14 — (vi)
                          bracket honest-range + window disclosure. PRESENTATION/COPY ONLY — no median/
                          value change. (a) _stage1_dispersion_gate extended to comparison_bracket (36mo
                          ppm2 >=0.30); the a10 application block reuses UNCHANGED (range_is_headline +
                          indicative tier + MUC high + AR/EN disclosure). (b) source_ar appends «(نافذة
                          36 شهراً)» + the Methodology brief shows «{n36} معاملة، منها {n24} خلال 24
                          شهراً» when n is a 36mo count; pure-24mo unchanged. Scope: all 20 dispersed
                          reliable villa cells gated (7 a13-rescued + 13 pre-existing); anchors clean
                          (Abu 0.208, Marikh 0.197). Live smoke v153 4/4: 56/565/21=2.4M [value IDENTICAL
                          + «(نافذة 36 شهراً)» + window split — CHECK-3 closed], 54/541/6=4.5M unchanged,
                          55/296/13 comparison_thin n=8 unchanged, 52/903/90 refusal. origin in sync 78ffd9b.)
api/health version:       3.1.0-sprint2.22.0a.14
Latest CHANGELOG:         CHANGELOG_v66.md  (Sprint 2.22.0a.14 (vi) — bracket honest-range + window
                          disclosure; additive ppm2_dispersion_36 + 2 MoJValuation fields + gate branch;
                          isolated 19/19; DoD 392/15/45/57. R10 generalized -> CLOSED-by-a14.)
Latest Sprint:            2.22.0a.14 (vi) — bracket honest-range + window disclosure (Session_Log §20.14)
                          - (a) comparison_bracket dispersion gate (36mo ppm2 vs 0.30) reusing the a10
                            block; (b) window disclosure on source_ar + Methodology brief
                          - scope ALL 20 dispersed reliable cells (7 a13 + 13 pre-existing); anchors clean
                          - PRESENTATION/COPY ONLY — central estimate byte-identical to a13
                          - boundary: 3 cells ±0.006 of T=0.30 may flip on a MoJ refresh (expected)
                          - fast-follow: direct live hit on a gated bracket cell (الغرافة/العب 600-900)
                          (full narrative: Session_Log §20.14; CHANGELOG_v66)

--- prev (2.22.0a.13, kept for reference — full detail in Session_Log §20.13 / CHANGELOG_v65) ---
Engine version deployed:  thammen-sprint2p22p0a13-thincell-credibility
                          (Heroku v152, 2026-06-01, sprint commit c366d66 [docs ->2bfec00]; Sprint
                          2.22.0a.13 — thin-cell credibility. Per-cell 36mo-capped fallback as continuous
                          P2 shrinkage of the surfaced TOTAL-PRICE median toward the cell's OWN 36mo
                          [w=n24/(n24+10), k=10], VILLA bracket only, n24>=5 floor, cap 36mo, range from
                          raw 24mo [gate-before-shrink]; ppm2 untouched. +10 thin->reliable; reliable
                          cells ~0% [max 2.2%, none >5%]; 154 <5-floor cells no-rescue. Live smoke v152
                          4/4: 56/565/21=2.4M [IDENTICAL, comp 28->37], 54/541/6=4.5M [byte-identical,
                          geo/A16-starved], 55/296/13=2.6M comparison_thin n=8 [no upgrade, ~-4%],
                          52/903/90=refusal. origin in sync 2bfec00.)
api/health version:       3.1.0-sprint2.22.0a.13
Latest CHANGELOG:         CHANGELOG_v65.md  (Sprint 2.22.0a.13 — thin-cell credibility. moj_reference
                          additive per-bracket n_24/n_36/total_price_median_24/36 + 24mo quartiles
                          [existing fields untouched]; apply_moj_strategy villa-only P2 blend + tier on
                          n36 + range from raw 24mo + trace note. Isolated 16/16; DoD 392/15/45/56.)
Latest Sprint:            2.22.0a.13 — thin-cell credibility (full narrative: Session_Log §20.13)
                          - 10 thin->reliable upgrades; reliable-move guard PASS; anchors 2.4M/4.5M
                            unchanged; 55/296/13 stays comparison_thin n=8 (gentle ~-4%)
                          - OPEN R10: 7/10 rescued cells dispersed >=0.30 present as clean reliable w/o
                            honest-range (a10 gate is widened-only); CHECK-3-live: bracket-success
                            source_ar discloses NO window for ANY villa cell
                          - NEXT=(vi) URGENT [bracket-success surface only, no value change]:
                            (a) a10 honest-range -> bracket path; (b) 24-vs-36mo window disclosure
                          - A16 = only Marikh lever (R9, own sprint); A7 open; LAND path deferred (villa-only)

--- prev (2.22.0a.12, kept for reference — full detail in Session_Log §20.12 / CHANGELOG_v64) ---
Engine version deployed:  thammen-sprint2p22p0a12-builttype-stratification
                          (Heroku v151, 2026-05-31, commit 9fa375c; Sprint 2.22.0a.12 — A2
                          built-type stratification of the villa comparable pool. USER-VISIBLE:
                          villa pool now PURE-villa [house بيت/مسكن + فيلتان + compound removed] →
                          pooled villa ppm2 median ~+9.7%; reference anchors STABLE [56/565/21 =
                          2.4M, 54/541/6 = 4.5M — robust total-price median]. origin in sync 9fa375c)
api/health version:       3.1.0-sprint2.22.0a.12
Latest CHANGELOG:         CHANGELOG_v64.md  (Sprint 2.22.0a.12 — A2 built-type stratification,
                          backend only. New shared built_type.py [built_type(row) → LAND / HOUSE /
                          STANDALONE_VILLA / None] applied at the two comp-selection sites
                          [moj_reference.build_reference bracket + geo_reference_v2.
                          _get_area_transactions geo], composes with A1's usage filter. LOCKS:
                          فيلتان EXCLUDED [measured −6 to −10% discount, distinct product — overturned
                          the earlier "fold"]; بنت هاوس FOLDED into villa [villa-range +18%, far from
                          APT ~827]; compound EXCLUDED by LABEL [مجمع/فلل/count-words]; بيت+مسكن →
                          HOUSE [resolved the مسكن categorizer split], removed from the villa pool.
                          Impact: villa ppm2 +9.7% pooled [pure-villa, H1]; net A1+A2 ~+4.5% above the
                          original contaminated median. Subject side CANNOT distinguish HOUSE from
                          VILLA → house subjects pool as standalone_villa → fix DEFERS to B. categorize/
                          _categorize KEPT for compute_trend + geo non-villa [Rule #39]. Isolated 28/28;
                          DoD 392/15/45/55; live smoke 4/4. Prior: v63=2.22.0a.11 A1 usage filter
                          [villa median −4.75%, §20.11])
A14 (CLOSED 2026-05-30):  villa cold-dyno first-try 503 — FIXED by Sprint A14 lever 2 (v146).
                          Live post-deploy H_lat: 56/565/21 cold first-try 200@14.4s + 200@15.0s
                          (×2) · 56/647/6 cold 200@15.9s — all <30s, margin ~15s, ZERO 503
                          (baseline was 503@31s). Lever 1 (overlap, H_A-cleared) DEFERRED —
                          unneeded (lever-2 margin huge). Bug A15 (silent-HBU-drop) still OPEN
                          (§20.5, separate sprint). NOT the closed A6 case (#53).
Latest Sprint:            2.22.0a.12 A2 — built-type stratification of the villa comparable pool
                          - built_type.py: built_type(row) → LAND / HOUSE / STANDALONE_VILLA / None
                            (NBSP-normalized نوع العقار) + matches_category; DRY, like usage_filter
                          - applied at BOTH comp sites (villa→STANDALONE_VILLA pool, land→LAND);
                            composes with A1 usage filter (a row must pass BOTH)
                          - LOCKS: فيلتان→None (measured −6 to −10% discount); بنت هاوس→villa (fold,
                            +18% villa-range); مجمع/فلل/count-words→None (LABEL-based); بيت/مسكن→HOUSE
                            (resolves the مسكن split), removed from villa
                          - impact: pooled villa ppm2 +9.7% FULL/+11.6% 24mo (H1; removed 41.5%:
                            house@350 + فيلتان/compound); reference anchors STABLE (56/565/21 2.4M,
                            54/541/6 4.5M — robust total-price median; anchors' valuation = CONDITION→B)
                          - subject side UNCHANGED: engine can't distinguish HOUSE from VILLA (QARS
                            subtype 1 = "Villa/House") → house subjects pool as standalone_villa
                            (live 55/296/13) → house-subject fix DEFERS to B (2.22.0b)
                          - thinning HONEST-not-broken: reliable cells 20%→12%, insufficient 48%→56%,
                            absorbed by 36mo fallback + a10 gate (live proof 55/296/13 = comparison_thin
                            n=8); a10 gate share ~unchanged 37%→39%
                          - Rule #39: categorize/_categorize KEPT for compute_trend + geo non-villa
                          - py_compile 4/4; isolated 28/28; DoD 392/15/45/55; live smoke 4/4
                          - CORRECTION to §20.11: compound exclusion is LABEL-based (نوع العقار), NOT
                            "via E20 area" — E20 is a SUBJECT-side guard, never touches comp rows
                          - NEXT: window-fallback 36mo-cap + light shrinkage (recon F: 36mo ≈ half the
                            +8-13% staleness drift); compute_trend categorizer alignment; methodology
                            doc §4 (3 strata + فيلتان excluded + compound label-based)
                          (full narrative: Session_Log §20.12; CHANGELOG_v64)

--- snapshot block below is PRE-2.22.0a (2.21.4-era), kept for reference ---
Engine (pre-arc):         thammen-sprint2p21p4-t3-aryan-lusail  (Heroku v125 code,
                          v127 config — T3_INVENTORY_ENABLED unset, default true)
prev api/health version:  3.1.0-sprint2.21.4
prev Latest Sprint:       2.21.4 T3 Developer-Inventory (Aryan, Lusail)
                          - HYBRID_TIER_CONFIG: T3_status_discount_map dict
                            (off_plan / under_construction → −17.5%; ready → −10%)
                            + T3_discount_default scalar + T3_stale_evidence_multiplier=0.5
                            + T3_discount_midpoint preserved as back-compat alias
                          - hybrid_valuation._process_t3_input — 3-shape detection
                            (dict_new with status / dict_legacy 2.21.2 / float / empty)
                            + per-row status discount + 0.5× stale freshness multiplier
                            + 7-field tier_breakdown sources per Rule E10
                          - developer_inventory.sqlite (17 cols, idempotent migration,
                            committed pre-deploy per ephemeral-FS workflow)
                          - 4 Aryan/City Avenues rows seeded (status=under_construction
                            post Anas pre-deploy correction §5.8; was inferred 'ready')
                          - T3 weight ceiling 0.12 = 0.15 cap × 4/5 evidence_strength
                            (BRIEF §9 architectural seal verified live)
                          - D10 flag T3_INVENTORY_ENABLED (mirrors HYBRID_APARTMENTS_ENABLED)
                          - H_WALK PASS: H1 canary + H11 live + H2 kill-switch live;
                            H3-H9 cited from 26/26 isolated + 29/29 regression;
                            H10 UI deferred to Sprint 2.21.5
Tests passing:            29 standalone files (28 pre-existing + new
                          test_sprint_2p21p4_t3_inventory.py @ 26 functions / 26 PASS).
                          Full regression 29/29 in 35.0s.
                          Sprint 2.21.2 tests (67/67) preserved via T3_discount_midpoint
                          back-compat alias. Run with PYTHONIOENCODING=utf-8.
Critical bugs open:       0
High bugs open:           0  (A6 latency ✅ CLOSED via 2.18.0 + 2.18.1 + 2.18.1.1;
                          A8 closed by 2.20)
Medium bugs open:         3  (A5 asset_type unknown, A15 silent-HBU-drop [§20.5],
                          A16 MoJ-bracket under-match [§20.10.1];
                          A7 rics_compliant ✅ CLOSED a20 — honest status label, §20.20)

Recent Sprints (chronological):
  2.18.0   Parallel property_factors fan-out (−4s villa/raw_land, v99)
  2.18.1   Parallel BFS upfront-prefetch (−60s compound_small, v100, kills 503)
  2.18.1.1 Compound-misroute fix Patches A+C (v101)
  2.21.2   Hybrid Foundation: Rule E3 → 8 constraints + hybrid_valuation.py (v107)
  2.21.3   T2 PF Lusail apartments hybrid path (v124 = v121 code; first live
           hybrid evaluation; Heroku v110→v118→v121 audit-driven loop; D10
           Lusail sub-district whitelist; list-page-only connector refactor
           after detail-fetch latency overran 30s router)
  2.21.4   T3 Aryan/City Avenues + status-aware discount + freshness (v125;
           4 seed rows under_construction; T3 weight 0.12 = 0.15 × 4/5)
  → all live; engine version reflects the most recent (2.21.4).

Hybrid arc (Sprints 2.21.2/2.21.3/2.21.4): full T2+T3 weighted evaluation
                          path live for Lusail apartments. PIN 69/255/75 = H1
                          anchor (City Avenues, district='لوسيل 69', T3 fires).
                          PIN 69/329/20 = H11 anchor (Fox Hills, district='غار
                          ثعيلب', T2-only — natural partial-population test).

Pre-Sprints since (no engine change, diagnostic only):
  2.21.1 pre-MME smoke v1+v2 — Heroku reaches MME (P1 TRUE), but JWT is
         anonymous Directus token (role=null) → kpi29 returns count:0 for
         all queries. Rent paths (kpi30/31/32) verified DEAD. Sprint 2.21.1
         deferred pending DevTools capture of authenticated session.
         (Operational §28 annotated 2026-05-24 with the auth-scope caveat
         + the real {count, transactionList} response schema.)
  2.22.0 audit — H5 FALSE: apartment failures are DATA-driven, not
         latency-driven (3/3 reps on 52/903/90: HTTP 200 + val=None +
         4.7s). 3-stage architecture does NOT solve apartments;
         BRIEF_2p21p2 (hybrid foundation) returned to top of queue and
         shipped as Sprint 2.21.2. H1+H3+H4 evidence preserved.
  2.21.3 smoke — T2 connector reachability + URL discovery (Heroku-IP).
         4 of 5 TRUE. arady canonical search URL = /listings (HTTP 200,
         70 hits page 1); /sitemap.xml available. PropertyFinder reachable
         (Heroku-sandbox parity exact). H5 confirmed PF detail pages
         expose both price + area extractable tokens (CSS class
         property-price + regex fallbacks). DOM duplication finding:
         PF raw matches inflate ~6× over unique listing count — connector
         in 2.21.3 MUST deduplicate by canonical URL or listing ID.

Land Arc:                 ✅ COMPLETE — PIN input (2.21.0) + output polish (2.21.0.5)
                          + Asset Type Reality Check (2.21.0.7/.7.1).
Multi-QARS (2.21.0.9):    ✅ STAGE 1 LIVE (n_qars≥2 detection + bracket adjust).
                          Stage 2 wall-to-wall (E18) pre-specified for 2.21.0.10.
A6 latency arc:           ✅ COMPLETE in 3 Sprints (2.18.0 / 2.18.1 / 2.18.1.1).

Rule E3 (Empirical_Findings): EXPANDED 2026-05-24 by Sprint 2.21.2.
                          Now 8 numbered constraints permitting tier-weighted
                          listing entry via hybrid_valuation_v1(). E1 (no MoJ
                          uplift) preserved. T2 cap 0.40, T3 cap 0.15, T1 floor
                          0.45, MUC mandatory when T1 absent, no T3-alone valuation.

Operational rules added 2026-05-24:
  #53  Closed cases stay closed — including as comparison anchors. Cite
       §X / Rule #N, never the originating closed case as foil/precedent.

Mthamen integration:      ⏸️ Deferred indefinitely (Project_Instructions §20.8)
MME apartments (2.21.1):  ⏸️ Deferred — awaits DevTools auth capture on
                          mme.gov.qa (see 2p21p1_pre/CHANGELOG)

Roadmap:                  **AUTHORITATIVE = Project_Instructions §11 ("Deferred Sprints",
                          refreshed 2026-06-01, BETA-FIRST). The numbered convenience-copy that
                          used to live here was removed so §11 is the SOLE source (it kept drifting).**
                          §11 now leads with the confirmed priority queue:
                            1. A7 (rics_compliant — beta-credibility quick-win)
                            2. Sprint 2 — feedback UI prompt (index.html; consumes /api/feedback)
                            3. ACTIVATION of a15 — counsel §8.1 PDPPL + §8.2 cross-border (R11)
                               + a15 capture-surface security pass; then DATABASE_URL + flag
                            4. B — condition sprint (R7; prereq for 2.22.0b Stage-2)
                            5. 2.22.0b — 5-stage UX + Stage-2 elicitation
                            6. cost-triangulation (independent DRC, §20.9) — POST-2.22.0b
                          + behind-beta backlog (2.21.5 hybrid UI, 2.21.4.1/.2 data, 2.21.3.2 arady,
                          2.21.0.10 Stage-2 E18, 2.21.0.11/.12 cosmetic, 2.18.2 GIS dedup, 2.17, 2.20)
                          + deferred-indefinite (2.16.16 Confirmed Sales, Mthamen §20.8, MME apartments
                          [2.21.1/2.29, auth]). Open mediums: A5, A15, A16.

D5/D6 calibration:        provisional, broker-experience-grounded — and remain
                          so INDEFINITELY. NO viable recalibration source: both
                          the secretary feed (closed 2026-05-24) and the
                          brokerage (Gardenia, closed) are gone. Recalibration
                          would need a future genuinely-PIN-keyed T1 sale source
                          (none exists). NOT a blocker (discounts ship with the
                          MUC clause). Empirical basis (interim): EMPIRICAL_FINDINGS
                          §3 asking-premium ranges + broker negotiation
                          experience.

Deploy:                   git subtree push --prefix "deploy v2" (Operational #43)
```

-----

## Non-negotiable rules (recite verbatim)

### Pre-Sprint Audit (§5 of Project Instructions)

Before ANY Sprint proposal:
1. Pick 3–5 diverse properties (varied zone/age/asset type, include tower or apartment_building)
2. Pull ground truth from Qatar GIS (`khazna.gisqatar.org.qa` primary, Sprint 2.16.5)
3. Hit `https://thammen.qa/api/evaluate` for each
4. Compare GIS vs thammen field-by-field including BUILDING_NO_SUBTYPE
5. Open `index.html` and grep for the field name — confirm visible to user
6. Test mobile viewport (390×844) — Sprint 2.16.4 lesson
7. Quantify scope via GIS counts
8. Only then propose Sprint

For external endpoints (especially Qatar government):
1. Write `smoke_<endpoint>.py` as standalone file
2. `git subtree push --prefix "deploy v2" heroku master` (Rule #43 — not plain `git push heroku master`) + `heroku run python smoke_<endpoint>.py`
3. Verify reachability + content type + WAF response
4. Only then build integration

### Delivery format (§2)

- One zip per Sprint via `present_files` (when in chat) or direct file edits (when in Claude Code)
- `CHANGELOG_vN.md` mandatory per Sprint
- Sprint numbers sequential, never reused
- Windows `cmd` syntax (`cd /d`, `copy /Y`, `tar -xf`, `findstr`)
- **One command per line. Never use `&&`.**
- Engine version format: `thammen-sprint{Major}p{Minor}p{Patch}-{slug}`

### Pre-deploy 6-item checklist

1. `python -m py_compile` on every modified Python file
2. `node --check` on extracted inline JS from index.html
3. Mobile viewport test 390×844
4. Regression — **DoD TEST MATRIX (SINGLE SOURCE; other docs reference this), measured 2026-06-01 (Sprint 2.22.0a.13), run with `PYTHONIOENCODING=utf-8`:** aggregator `run_sprint_2p22p0a_suite.py` = **392/392** · security `test_sprint_2p16p17_security.py` = **15/15** · `test_sprint_2p22p0a3_surface_honesty.py` = **45/45** · broad `2p22p0_pre/run_regression_2p22p0a.py` = **56/56** (measured 2026-06-01; the prior known fail — `test_sprint_2p22p0a5_request_budget.py`'s EXACT-version-pin — was relaxed to a version-agnostic FORMAT check [verified in-code 2026-06-01: `startswith('thammen-sprint')` + dotted-numeric `SPRINT_TAG`], so RISK_REGISTER R6 ✅ resolved; +1 file vs the old 55 = the new `test_sprint_2p22p0a13_thincell_credibility.py`). `test_v2_modules.py` is **formally EXCLUDED** (needs pytest; not in requirements.txt; already in the broad runner's `SKIP_FILES`).
5. Isolated logic tests for new code (5+ cases including fallback)
6. Smoke test 3 diverse addresses from Heroku post-deploy

### Methodology (§3)

|Source|Role|Production?|
|---|---|---|
|MoJ (data.gov.qa)|Market truth (primary)|✅|
|DCF/Yield|Income (primary for income-producing assets)|✅|
|~~Mthamen (sak.gov.qa)~~|Cost (DRC) reference only|❌ deferred 2026-05-19|
|Listings|Sentiment only|⚠️ display only|

- **Median, not mean.** Always cite n.
- Sample size: n≥20 reliable, 10-19 indicative, 5-9 context, <5 insufficient
- 24-month window default, 36-month fallback when n<20
- Size brackets: 0-400 / 400-600 / 600-900 / 900-1500 / 1500+ m²
- Net yield: 5-6% normal, >6% bargain, <4% weak. Never gross without net.

### Stock stratification (Rule E4, Empirical_Findings)

- `land_priced` (<1.15) → 10-Year Rule
- `aging_stock` (1.15-1.50)
- `modern_stock` (1.50-2.20)
- `luxury_new` (≥2.20)

### Hard ceilings

- Buyer: never above MoJ median + 10%
- Seller: never insist above MoJ median + 30%

### Tower-aware input handling (Sprint 2.16.10)

For asset_type ∈ {tower, compound_large, apartment_building, commercial_building}:
- UI shows `unit_count` + `per_unit_rent` (not standalone `rental_income`)
- Backend: `rental_income_monthly = unit_count * per_unit_rent`
- Skip plot-based sanity check (Sprint 2.16.11 carve-out)
- MUC clause mandatory

### Zoning/Subtype cross-check (Sprint 2.16.14 — Bug A11)

QARS_Point.BUILDING_NO_SUBTYPE was last surveyed 2010-2012. Now classifier
checks against Zoning. If subtype ∈ {1, 6, 11} AND zoning ∈ {CCC, COM, CF,
SCZ, TU, LFR, LInd, IND, MU*} → emit `subtype_zoning_mismatch` flag.
9.1% of GOVERNMENT-category landmarks affected. 0% of Business/Finance.

-----

## Self-correction triggers (full list in §22 + Session_Update §5)

STOP if I:
- Propose a Sprint without running the audit → run §5 first
- Claim a bug based on memory → verify in browser (desktop + mobile)
- Write `&&`-chained command → split per line
- Cite a median without n → add n
- Rationalize MoJ staleness → acknowledge instead
- Treat Mthamen DRC as primary → methodology reference only (Project_Instructions §20.8)
- Try to "correct" Thammen value using Mthamen reasoning → gap is diagnostic
- Rebuild Mthamen's formula in our codebase → IP concern + brittleness
- Use 51/835/17 as timing baseline → A6 catalogued, use 52/903/90
- Propose `rental_income` for tower without `unit_count + per_unit_rent` → Sprint 2.16.10
- Bundle 3+ fixes into one Sprint → prefer single-purpose (marathon 2026-05-18 pattern)
- Propose reviving Mthamen live integration → §20.8, need 3 conditions met
- Propose integration with Qatar government endpoint without Heroku smoke test → §21.6
- Treat Mthamen as Sprint candidate → archived reference only
- Trust QARS_Point subtype as single source without Zoning cross-check → Sprint 2.16.14 / Rule E7
- Add a new FastAPI request model without `model_config = ConfigDict(extra='forbid')` → Sprint 2.16.15 / Bug A2 — silent typo-drop creates user confidence gap
- Attempt `git push heroku master` بدون التحقق من branch + §3 checklist + Sprint integrity + explicit user consent → STOP. راجع Operational_Rules.md #32 (Push & Commit Discipline). Default: لا تدفع، اسأل user صراحة.
- أبدأ audit بقراءة الكود بدل القياس → STOP، راجع Operational_Rules.md #33 (Empirical-First Audits). قِس أولاً (curl/logs/git log)، اقرأ الكود ثانياً.
- أكتب `heroku run python -c "..."` بـ argument معقّد (`&`/`=`/`+`/quotes أو >3 أسطر) → STOP، راجع Operational_Rules.md #34 (File-Based Scripts). اكتب ملف `probe_X.py` منفصل بدلاً منه.
- أكتب syntax مكتبة بدون التحقق من الإصدار على Heroku → STOP، راجع Operational_Rules.md #35 (Library Version Verification). تحقّق requirements.txt + `heroku run python check_version.py` أولاً.
- أذكر رقم empirical بدون التحقق من العيّنة الفعلية → STOP، راجع Operational_Rules.md #36 (Observed-vs-Expected Reporting). اذكر sample size + time window الفعليين، وما لم يُرَ.
- أتجاوز السقف الزمني للـ scouting بدون إذن user → STOP، راجع Operational_Rules.md #37 (Time-Boxed Scouting). أعطِ ما لديك + الناقص + تقدير زمن، واطلب سقفاً جديداً.
- أبني Sprint يخلط 2+ bugs غير مترابطين → STOP، راجع Operational_Rules.md #38 (Single-Purpose Sprint Scope). اقترح Sprints منفصلة، أو اطلب إذن bundling صريحاً مع تبرير التبعية.
- أنفّذ Y بدل X المطلوب بدون 3-جمل justification → STOP، راجع Operational_Rules.md #39 (Deviation Justification Protocol). اذكر: لماذا Y ضروري + ما يُفقد بترك X + ما يحتاج user معرفته لتفسير النتائج.
- أعتمد على replica tests فقط بدون verification ضد production class → STOP، راجع Operational_Rules.md #40 (Replica + Production Verification). أضِف سطراً واحداً على الأقل يستدعي الكود الإنتاجي الفعلي.
- أؤجّل/أستبعد عمل بدون توثيق في الـ docs + شروط إحياء → STOP، راجع Operational_Rules.md #42 (Deferred-Work Documentation). وثّق: ما جُرّب + لماذا أُجِّل + شروط الإحياء + توجيه قاطع للجلسات اللاحقة.
- أقترح Sprint بدون مراجعته خلال عدسة Stage 1/2/3 (E16) → STOP، راجع Operational_Rules.md #50 (Staged-Sprint Discipline). كل Sprint جديد يجاوب: أي stage يخدم؟ هل Stage 1 يمكنه الشحن مستقلاً عن Stage 2 data؟
- أرفع threshold مستنتج من بيانات صغيرة بدون مراجعة domain knowledge → STOP، Sprint 2.21.0.9 رفض ذلك (15.2m clustering أوحى بـ 18m، لكن Anas أكّد أن الفيلات منفصلة فعلياً مع ارتداد كامل — E15). data-driven inference لا تتغلّب على domain confirmation.
- أصمّم تصنيف GPS-centroid-based دون فحص MME setback code → STOP، راجع EMPIRICAL E15. فيلتين منفصلتين code-compliant على نفس قطعة لهما centroid ≥16m؛ أي threshold تحت ذلك false-positive محتمل. استخدم wall-to-wall (E18) بدلاً.
- أطلب من broker إدخال حقل يمكن جلبه آلياً من GIS/MoJ → STOP، راجع EMPIRICAL E17 (1-field minimum input). property identification فقط مطلوب من broker؛ كل شيء آخر auto-fetched ومرئي لمراجعته. Thammen verifies، broker corrects، أبداً العكس.
- أُعلن Sprint مكتمل بمجرد نجاح الـ deploy + الاختبارات دون فحص الـ response content على المسار الذي أصبح متاحاً للمستخدم → STOP، راجع Operational_Rules.md #52 (Latency Unmasks Methodology). كل Sprint يحول 5xx→2xx على مسار كان timeout سابقاً = response content على هذا المسار قابل للفحص لأول مرة → فحص methodology إلزامي post-deploy. Sprint 2.18.1 → 2.18.1.1 هو السابقة الأولى.
- أُصنّف compound_small بناءً على QARS subtype فقط دون فحص extent.total_area_m2 → STOP، راجع EMPIRICAL E20. compound > 15K m² لا يملك MoJ comparable (المسجَّل الأكبر 15,027 m²). Sprint 2.18.1.1 Patch A تروّج تلقائياً إلى compound_large عند extent ≥ 15K → Income Approach refusal pattern نظيف.
- أضيف decomposition (land + building) بدون guard ضد `land_value > valuation_amount` → STOP، راجع Sprint 2.18.1.1 Patch C. القاعدة: في أي function يحسب land_value × area للأصول السكنية، يجب return None لو النتيجة > valuation_amount. الـ guard universal (يلتقط premium-land villa teardowns + MoJ outliers + future bug classes).
- أكتب جملة جديدة تحوي "unlike [closed case]" أو "mirror [closed case] pattern" أو "precedent: [closed case]" → STOP، راجع Operational_Rules.md #53 (Closed cases stay closed — including as comparison anchors). احذف الجملة. الـ finding يقف بذاته. اذكر §X (القاعدة)، ليس الحالة التي أنتجتها.

-----

## Recall phrases (user shortcuts)

| Arabic | Meaning |
|---|---|
| "تذكر Sprint 2.16.X" (X=6..15) | Specific marathon/post-marathon Sprint |
| "تذكر Sprint 2.16.15" | Pydantic extra='forbid' / Bug A2 fix, deployed 2026-05-19 evening |
| "تذكر Bug A2" | Pydantic schema lenience — unknown fields silently dropped |
| "تذكر khazna" | GIS Qatar migration 2026-05-17 |
| "تذكر outage 17 مايو" | GIS outage timeline |
| "تذكر Lusail B201" | Tower Input Disambiguation example |
| "تذكر المثمن" | Mthamen reverse engineering + defer decision (§20.8) |
| "تذكر قرار 19 مايو" | Mthamen defer decision specifically |
| "تذكر Bug A11" | Zoning/Subtype contradiction discovery 2026-05-19 PM |
| "تذكر أشغال 61/875/20" | The reference case for Bug A11 |
| "تذكر Rule E7" | QARS subtype requires Zoning cross-check |
| "تذكر Sprint 2.21.0.9" أو "تذكر Stage 1" | Multi-QARS detection — staged-valuation pattern, no GPS-distance classification, 18m threshold rejected, wall-to-wall (E18) deferred to 2.21.0.10 |
| "تذكر Bou Hamour" أو "تذكر 56/565/21" | The Sprint 2.21.0.9 trigger case — 2 villas on PIN 56090294 (PDAREA=900), physically separate despite 15.2m centroid (full ارتداد + حوش per MME code E15) |
| "تذكر E15" أو "تذكر ارتداد البلدية" | Qatar MME 3m setback code → code-compliant separate villas have centroids ≥16m |
| "تذكر E16" أو "تذكر staged valuation" | Stage 1 (≤5s, ~70%) → Stage 2 (~90%) → Stage 3 (~95%+); every Sprint reviewed through this lens |
| "تذكر E17" أو "تذكر 1-field minimum" | Broker supplies property identification only; everything else auto-fetched; Thammen verifies, broker corrects |
| "تذكر E18" أو "تذكر قاعدة 6 متر" | Stage 2 wall-to-wall classification rule (wall<1m → attached; ≥6m → separate; 1-6m → sub_minimum). Replaces rejected GPS-centroid threshold |
| "تذكر #50" أو "Staged Sprint" | Operational_Rules #50 — every Sprint reviewed through Stage 1/2/3 lens |
| "تذكر Sprint 2.18.0" أو "تذكر parallel factors" | 5-way parallel `property_factors.analyze_property` via `ThreadPoolExecutor(max_workers=5)`. Deployed Heroku v99 (2026-05-23 evening, CHANGELOG_v44). −4s on villa/raw_land paths (multi_qars_56 26.8s→22.8s, khor_land 25.1s→21.2s); fast-paths unchanged; HTTP 503 class still present on compound_small (Sprint 2.18.1 territory). Audit prediction matched measurement within ±2% — first validation of Rule #51 + E19. |
| "تذكر E19" أو "تذكر max_workers" | I/O-bound parallelization of N independent fixed tasks → `max_workers = N`. More workers = idle overhead. Discovered Sprint 2.18.0 §5 mini-audit; pattern applies platform-wide. |
| "تذكر #51" أو "تذكر audit-driven Sprint" | Operational_Rules #51 — canonical performance-Sprint pattern: pre-Sprint §5 audit → audit-derived patch (measured bottleneck, scoped fix) → post-deploy audit comparison. Sprint 2.18.0 proved prediction accuracy ≤±2% across all measured paths. |
| "تذكر Sprint 2.18.1" أو "تذكر parallel BFS" | Parallel `_expand_extent` upfront-prefetch via `ThreadPoolExecutor(max_workers=min(N,20))`. Deployed Heroku v100 (2026-05-23 evening, CHANGELOG_v45). −60s on compound_small (51/835/17 89s→28.9s); HTTP 503×3 → 200×3 (THE WIN). §5 mini-audit corrected the original audit's "5-8s" prediction to honest 22-27s (off by ~3x). Latency goal delivered, but post-deploy visual verification unmasked methodology bug → Sprint 2.18.1.1. |
| "تذكر Sprint 2.18.1.1" أو "تذكر compound misroute" أو "تذكر Patches A+C" | Compound-misroute fix (Anas's verification discovered silent failure on 51/835/17: land=218M vs total=6.8M, building=−211M, pct=−3,107%). Patch A in qatar_gis.full_property_lookup: when classification.asset_type==COMPOUND_SMALL and extent.total_area_m2 >= 15000, promote both to COMPOUND_LARGE → routes via ASSET_TYPE_TO_MOJ_CATEGORY['compound_large']=None → valuation=None → clean Income Approach refusal. Patch C in _decompose_value: universal `if land_value > valuation_amount: return None` (catches premium-land villa teardowns + MoJ outliers too). Deployed Heroku v101 (2026-05-24 morning, CHANGELOG_v46). Anas visual verify 9/9. Threshold = E20. |
| "تذكر #52" أو "تذكر latency unmasks methodology" | Operational_Rules #52 — when a latency Sprint converts 5xx→2xx on a previously-unreachable path, the response *content* on that path is newly verifiable and may have latent bugs. Post-deploy verification scope must include the now-reachable response content, not just the latency metric. First documented case: Sprint 2.18.1 unmasked the compound_small >15K methodology bug; Sprint 2.18.1.1 closed it. |
| "تذكر E20" أو "تذكر 15K compound" | EMPIRICAL_FINDINGS E20 — MoJ "مجمع فلل" sampling max = **15,027 m²**. Compounds with extent ≥ 15K m² have no MoJ comparable; Income Approach with rent input is the only valid methodology. The 15K threshold drives Sprint 2.18.1.1 Patch A. |
| "تذكر #53" أو "تذكر closed cases stay closed" | Operational_Rules #53 — rules derived from a deferred/closed case remain in force, but the originating case itself is not cited as a foil, precedent, or comparison in new documentation. Cite §X (the rule), not the case that produced §X. Self-check: delete any sentence containing "unlike [closed case]" or "mirror [closed case] pattern". Crystallized 2026-05-24, pre-Sprint 2.21.1 MME smoke session. |
| "تذكر Sprint 2.21.2" أو "تذكر Hybrid Foundation" أو "تذكر hybrid_valuation_v1" | Sprint 2.21.2 (CHANGELOG_v47.md, Heroku v107, deployed 2026-05-24 evening). Foundation Sprint — Rule E3 expanded from "MUST NOT enter calculation" sentence to **8 numbered constraints** permitting tier-weighted listing entry via `hybrid_valuation_v1()`. New module `hybrid_valuation.py` exposes `HYBRID_TIER_CONFIG` (D5 T2 discount −12.5%, D6 T3 −17.5%, both provisional) + the function (Cases A/B/C/D + Constraint 7 unit-norm + Constraint 8 T3-alone refusal). Function exists, no engine path calls it yet — production behavior identical to 2.18.1.1. Connectors land in 2.21.3 (T2) + 2.21.4 (T3). 22 test functions / 67 sub-checks (H1+H2+H3+H4+H6 all TRUE); H5 verified 27/27 files pass. |
| "تذكر Rule E3 v2" أو "تذكر 8 constraints" | Rule E3 in `docs/Empirical_Findings.md` was rewritten 2026-05-24 by Sprint 2.21.2. Now 8 numbered constraints: (1) T2 cap 0.40 with T1 + D5 discount; (2) T3 cap 0.15 + D6 discount; (3) T1 floor 0.45 when present; (4) no T1 → indicative ceiling; (5) mandatory MUC ±20% when T1 absent; (6) source-level transparency (E10); (7) like-for-like unit normalization (RICS Red Book); (8) T3 alone insufficient. E1 (no MoJ uplift) preserved. |
| "تذكر Pre-Sprint 2.22.0" أو "تذكر H5 FALSE" | Pre-Sprint 2.22.0 audit (2p22p0_pre/CHANGELOG, 2026-05-24). Tested whether 3-stage UX architecture solves the apartments gap. H5 FALSE was decisive: 52/903/90 apartment_building returns HTTP 200 + valuation_amount=None + 4.7s — failure is data-driven, not latency-driven. 3-stage would just rename "insufficient data" across two stages. Sprint 2.22.0 deferred; BRIEF_2p21p2 (hybrid foundation) returned to top of queue and shipped. H1 TRUE + H3 TRUE + H4 TRUE evidence preserved for future UX-refactor Sprint after 2.21.5. |
| "تذكر Pre-Sprint 2.21.3" أو "تذكر DOM duplication" أو "تذكر arady /listings" | Pre-Sprint 2.21.3 smoke (2p21p3_pre/CHANGELOG, 2026-05-24 evening). 4 of 5 TRUE. arady canonical search URL = **`/listings`** (HTTP 200, 70 listing hits page 1, sitemap.xml available for full inventory). PropertyFinder reachable from Heroku (exact parity with sandbox; raw=142 = sandbox=142). H2 FALSE was a threshold artifact: PropertyFinder DOM duplicates listing nodes ~6× (142 raw → 24 unique on Lusail page 1). **Sprint 2.21.3 connector MUST deduplicate by canonical URL or listing ID.** Detail-page schema confirmed extractable: CSS class `property-price` + regex fallback for QAR/AED + regex for m²/sqm. |
| "تذكر D5/D6" أو "تذكر calibration provisional" | `HYBRID_TIER_CONFIG` ships with D5 T2 discount midpoint −12.5% (range −10%/−15%) and D6 T3 discount midpoint −17.5% (range −15%/−20%), both tagged `provisional, broker-experience-grounded`. Empirical basis: EMPIRICAL_FINDINGS §3 asking-premium ranges (+8% to +20% inverted). Recalibration has NO viable source (secretary feed closed 2026-05-24 + brokerage/Gardenia closed) → D5/D6 stay provisional **indefinitely**; not a blocker (ship with the MUC clause). Do NOT re-add closed-feed framing (no broker-supplied pipeline / no awaiting-secretary dependency). |
| "تذكر إغلاق Confirmed Sales" أو "تذكر no viable source" | BOTH internal sale-data feeds are closed: the secretary source (permanently, 2026-05-24) AND Anas's brokerage (Gardenia). Confirmed Sales DB (Sprint 2.16.16) therefore has **NO viable internal source** → deferred **indefinitely**; it is NOT a data source, dependency, or pillar. Do NOT re-add closed-feed framing (no broker-supplied pipeline; no awaiting-secretary dependency). Revive only if a genuinely PIN-keyed T1 sale source ever appears (none exists). T2 "broker" listings are ad-hoc only (not a stable feed); the Stage-4 field check is broker-agnostic (any vetted broker). |
| "راجع EMPIRICAL_FINDINGS" | Audit rules E1-E23 |
| "اقرأ القسم X" | Activate self-correction trigger from section X |
| "ركذت قاعدة الدفع" أو "تذكر #32" | Push & Commit discipline — Operational_Rules #32 |
| "هل أدفع؟" أو "should I push?" | يُفعّل #32 checklist، أعطِ status report قبل الإجابة |

-----

## Deployment workflow (Windows cmd)

```
cd /d "C:\Thammen\deploy v2"
git add <files>
git commit -m "<Sprint X.Y.Z>: <description>"
git subtree push --prefix "deploy v2" heroku master
git push origin master
```
> **Rule #43:** the app lives in the `deploy v2/` subdir → deploy is `git subtree push --prefix "deploy v2" heroku master`, **not** plain `git push heroku master` (rejected by the buildpack — no `requirements.txt` at slug root). `git push origin master` keeps the GitHub backup current (R1 deploy ritual).

### Post-deploy verification

```
curl -s -X POST https://thammen.qa/api/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"zone\":61,\"street\":875,\"building\":20}" > out.json
findstr /C:"<expected_field>" out.json
```

-----

## File structure conventions

```
C:\Thammen\deploy v2\
├── CLAUDE.md                     ← this file
├── docs/                         ← Project Knowledge (read first)
│   ├── Project_Instructions.md
│   ├── Session_Log.md
│   ├── Empirical_Findings.md
│   ├── Custom_Instructions.md
│   ├── Session_Update_2026-05-19.md
│   └── Operational_Rules.md
├── api.py
├── evaluate_unified.py           ← main engine, ENGINE_VERSION at top
├── qatar_gis.py                  ← classifier (Sprint 2.16.6/14)
├── index.html                    ← frontend (RTL, Tajawal)
├── *.bak_<sprint>                ← backups before each Sprint
├── CHANGELOG_v<N>.md             ← one per Sprint
├── test_sprint_<X>_<Y>.py        ← isolated tests per Sprint
└── moj_weekly.csv                ← MoJ data
```

-----

## Audience calibration (§16)

|Audience|English code labels?|Methodology jargon?|Open decisions?|
|---|---|---|---|
|Anas (engineer)|yes|yes|yes|
|Manager|no|light|yes|
|Secretary|**never**|**never**|**never**|

-----

## Final notes

- Reply in Arabic unless code or technical detail makes English clearer
- Be direct about uncertainty and tradeoffs
- Prefer surgical fixes (2-10 lines) over rewrites
- When user says "افعل الأصوب" — exercise engineering judgment, don't ask
- When user challenges a result, re-examine evidence before defending
- Document failed paths as clearly as successful ones (e.g., Mthamen §20.8)

> Reading this file means you've inherited the work of 15+ Sprints, 2 major
> decisions, and a 22-landmark audit. Honor the methodology. Don't reinvent.
