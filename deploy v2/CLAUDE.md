# Thammen — Claude Code Workspace Configuration

> **Project:** thammen.qa — Qatar real-estate AVM (RICS Red Book Global Standards, effective 31 January 2025 — VPGA 10 + VPS 6 + IVS 106)
> **User:** Anas (Qatari, Windows, Heroku deploy)
> **Working directory:** `C:\Thammen\deploy v2`
> **Last update:** 2026-05-30 (Sprint 2.22.0a.9 deployed — widened-path age/quality elasticity, facet a; CHANGELOG_v61 + Session_Log §20.10). **LIVE: engine `thammen-sprint2p22p0a9-widened-elasticity` · api/health 3.1.0-sprint2.22.0a.9 · Heroku v148 · commits `acb1e40`+`dda656b` · CHANGELOG_v61** (the `geo_value` widened headline [Cases 2 & 3 of `_select_primary_comparison`] now applies the age/quality slice [building_age + plot_shape] of the property-factor adjustment, clamped ±0.10; location factors excluded [geo_v2 inter-district-normalizes]; bracket/thin/preliminary byte-stable; facet (b) tier/MVU reframe DROPPED [principled RICS VPS 3]; live Marikh 54/541/6 = 4.6/4.4/4.3M across age 0/20/45 [was flat 4.5M], control 56/565/21 = 2.5M, apt insufficient; external MoJ 681≈682/ft² cross-check [**later OVERTURNED 2026-05-31: coincidence — built-type-blind size-bracketed median; 54/541/6 RE-OPENED/over-anchored, NOT validated; see §20.10.1 + RISK_REGISTER R7**]; isolated 28/28 + DoD 392/15/45/52; R6 a8 version-pin relaxed to format). Prior: Sprint 2.22.0a.8 — RICS/IVS 2025 citation correctness (Heroku v147, commit `1e07a2a`, CHANGELOG_v60): added the AVM models standard VPS 5 / IVS 105 + AVM-not-standalone disclosure on a secondary collapsible surface [the 2.22.0a.4-deferred surface]; remapped ALL stale citations — approaches VPS 4→VPS 3 / IVS 103, HBU→VPS 2 / IVS 102 [genus, triple-confirmed], scope→VPS 1, VPN 13→VPGA 10 [D5 widened]; bare `methodology_ar` untouched; copy-only — valuations unchanged [villa 56/565/21 = 2.5M = v101]; regression 392/15/45/51 + 43/43; origin in sync `b560920..1e07a2a`). Prior: Sprint A14 lever 2 — geometric_factors parallelized, **A14 CLOSED** (Heroku v146, CHANGELOG_v59, cold villa 200 @~15s, was 503@31s; lever 1 deferred + H_A-cleared/ready). The production-state snapshot block below + Session_Log §20 are authoritative. Prior: 2026-05-29 Sprint 2.22.0a.4 — Disclosure & Framing Honesty (Heroku **v140**, commit `f7870a3`, CHANGELOG_v55; engine `thammen-sprint2p22p0a4-disclosure-framing-honesty`). `methodology_ar` → universal bare line «أساس التقدير هو منهج المقارنة بالمبيعات.» (dropped «توفيق ثلاثي الطرق» + Latin); main-path Layer A fold (6→5, 5 genuine caveats preserved); D/C4 canonical from 2.22.0a.2 untouched. Multi-AI Rule #54 (GPT-5+Gemini) Path A bare-line. Live smoke villa 56/565/21 (200 on A6 retry @22s) + apt 52/903/90 PASS. **Arabic-Surface arc since 2.21.4:** 2.22.0a (v50) → a.1 QARS fallback (v51/Heroku v132) → a.2 content fixes (v52) → 2.16.17 security (v53) → a.3 honesty (v54/v139) → a.4 framing (v55/v140). Full bridge + deferred items in Session_Log §18. **NOTE:** the production-state snapshot block below predates the 2.22.0a arc — trust the four updated lines there + Session_Log §17–§18 over the older body until a full snapshot rewrite.)

## Quick orientation

Read these files in order before any technical work:

@./docs/Project_Instructions.md
@./docs/Session_Log.md
@./docs/Empirical_Findings.md
@./docs/Custom_Instructions.md
@./docs/Session_Update_2026-05-19.md
@./docs/Operational_Rules.md

**Most recent state = Sprint 2.21.4 T3 developer-inventory deployed Heroku
v125 on 2026-05-25 evening. Full hybrid arc complete:** Sprint 2.21.2
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
for history. Newest operational rules: `Operational_Rules.md` #43–#60
(latest written = #60 "measure-gate for lever sequencing"; #55/#56 reserved-pending).
Newest empirical rules: `Empirical_Findings.md` E13–E21 (Rule E3 itself
expanded to 8 numbered constraints by Sprint 2.21.2 — listings now allowed
tier-weighted entry via `hybrid_valuation_v1()`).

-----

## Current production state (snapshot)

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
Engine version deployed:  thammen-sprint2p22p0a9-widened-elasticity
                          (Heroku v148, 2026-05-30, commits acb1e40 [facet a] + dda656b
                          [deploy-prep]; Sprint 2.22.0a.9 — widened-path age/quality
                          elasticity. Methodology: headline changes on the two geo_value
                          widened paths only — success-path bracket unchanged
                          [villa 56/565/21 = 2.5M = v101])
api/health version:       3.1.0-sprint2.22.0a.9
Latest CHANGELOG:         CHANGELOG_v61.md  (Sprint 2.22.0a.9 — widened age/quality
                          elasticity, facet a: _select_primary_comparison Cases 2 & 3 now
                          apply the age/quality slice [building_age + plot_shape] of the
                          property-factor adj to the geo_value headline, clamped ±0.10;
                          location factors excluded [geo_v2 inter-district-normalizes];
                          bracket/thin/preliminary byte-stable. Facet (b) tier/MVU reframe
                          DROPPED [principled RICS VPS 3]. Live: Marikh 54/541/6 4.6/4.4/4.3M
                          across age 0/20/45 [was flat 4.5M], control 2.5M, apt insufficient.
                          External MoJ 681≈682/ft² cross-check [later OVERTURNED 2026-05-31:
                          COINCIDENCE — built-type-blind size-bracketed median; 54/541/6
                          RE-OPENED/over-anchored, NOT validated — see §20.10.1 + RISK_REGISTER
                          R7]. R6 a8 version-pin relaxed to format. Full
                          narrative Session_Log §20.10. Prior: v60=2.22.0a.8 RICS/IVS 2025
                          citation correctness [v147])
A14 (CLOSED 2026-05-30):  villa cold-dyno first-try 503 — FIXED by Sprint A14 lever 2 (v146).
                          Live post-deploy H_lat: 56/565/21 cold first-try 200@14.4s + 200@15.0s
                          (×2) · 56/647/6 cold 200@15.9s — all <30s, margin ~15s, ZERO 503
                          (baseline was 503@31s). Lever 1 (overlap, H_A-cleared) DEFERRED —
                          unneeded (lever-2 margin huge). Bug A15 (silent-HBU-drop) still OPEN
                          (§20.5, separate sprint). NOT the closed A6 case (#53).
Latest Sprint:            2.22.0a.9 Widened-Path Age/Quality Elasticity (facet a)
                          - _age_quality_adj() sums building_age + plot_shape from
                            factors_detail, clamped ±0.10 (property_factors.MAX_ADJUSTMENT);
                            applied to geo_value/range_low/range_high in
                            _select_primary_comparison Cases 2 & 3 ONLY
                            (comparison_widened + comparison_widened_indicative)
                          - signed asymmetry: bracket = full adj; widened = age/quality-only
                            (geo_v2 owns location); empty factor detail → aq=0 → byte-stable
                          - facet (b) [accuracy-tier :4226 + MVU-downgrade :4569] DROPPED
                            (not deferred) — widening-to-healthy-n is the principled VPS 3 remedy
                          - backend-only (no index.html); no new user strings / input fields
                          - isolated 28/28; DoD 392/15/45/52 (aggregator/security/surface/broad);
                            a8 citation 43/43 (pin relaxed to format, R6)
                          - external MoJ 681≈682/ft² cross-check later OVERTURNED 2026-05-31:
                            COINCIDENCE (built-type-blind median); 54/541/6 RE-OPENED — §20.10.1 / R7
                          (full narrative: Session_Log §20.10; CHANGELOG_v61; deferred items there)

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
Medium bugs open:         4  (A5 asset_type unknown, A7 rics_compliant false,
                          A15 silent-HBU-drop [§20.5], A16 MoJ-bracket under-match [§20.10.1])

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

Roadmap (priority order — **AUTHORITATIVE ROADMAP = Project_Instructions §11 "Deferred Sprints"; the list below is a convenience copy, §11 wins on any drift**):
  1. Sprint 2.21.5 — UI tier breakdown + MUC surfacing for hybrid outputs.
                     Both 2.21.3 (T2) + 2.21.4 (T3) shipped → 2.21.5 is now
                     UNBLOCKED. Owns rendering of sources[] (per-row T3
                     7-field shape) + H10 visual verification (deferred
                     from 2.21.4 H_WALK §5).
  2. Sprint 2.21.4.1/.2/… — Data-only expansion Sprints adding more
                     developers/projects (UDC, Qetaifan, Qatari Diar,
                     Msheireb, Dar Al-Arkan) to developer_inventory.sqlite.
                     Pure data Sprints — no code change; CSV import
                     workflow per 2p21p4_brief/README.md.
  3. Sprint 2.21.3.2 candidate — arady connector (deferred from 2.21.3 per
                     BRIEF §12 single-purpose; needs __NEXT_DATA__ probe
                     OR headless-browser infra to handle JS-hydrated content).
  4. Sprint 2.21.0.11/.12 — Cosmetic UX (rent-input deep-link;
                     negotiation-range box hide when val=None).
  5. Sprint 2.18.2 candidate — lite/full GIS dedup (Stage-1 ≤5s for
                     compound_small). Needs §5 audit first.
  6. Sprint 2.22.0 — 3-stage architecture, DEFERRED. Evidence in
                     2p22p0_pre/. Revisit after 2.21.5 (hybrid UI may
                     benefit from staged UX).
  7. Sprint 2.21.0.10 — Stage 2 wall-to-wall (E18). Needs Building
                     Footprint layer probe.
  8. Sprint 2.21.1 — MME apartments. Awaits authenticated session.
  9. Sprint 2.16.16 — Confirmed Sales DB. DEFERRED INDEFINITELY (2026-05-30):
                     NO viable internal source — both candidate feeds are
                     closed (secretary source 2026-05-24 + Anas's brokerage,
                     Gardenia). Confirmed Sales is NOT a data source,
                     dependency, or pillar. Do NOT re-add closed-feed framing
                     (no broker-supplied pipeline; no awaiting-secretary dep). Revive only if a genuinely
                     PIN-keyed T1 sale source ever appears. NOT a blocker for
                     anything else.

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
2. `git push heroku master` + `heroku run python smoke_<endpoint>.py`
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
4. Regression — **DoD TEST MATRIX (SINGLE SOURCE; other docs reference this), measured 2026-05-30, run with `PYTHONIOENCODING=utf-8`:** aggregator `run_sprint_2p22p0a_suite.py` = **392/392** · security `test_sprint_2p16p17_security.py` = **15/15** · `test_sprint_2p22p0a3_surface_honesty.py` = **45/45** · broad `2p22p0_pre/run_regression_2p22p0a.py` = **48/49** (1 known fail = `test_sprint_2p22p0a5_request_budget.py`, 2 brittle EXACT-version-pin assertions broken by the a6 bump — RISK_REGISTER R6, relax in next code sprint). `test_v2_modules.py` is **formally EXCLUDED** (needs pytest; not in requirements.txt; already in the broad runner's `SKIP_FILES`).
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
| "راجع EMPIRICAL_FINDINGS" | Audit rules E1-E20 |
| "اقرأ القسم X" | Activate self-correction trigger from section X |
| "ركذت قاعدة الدفع" أو "تذكر #32" | Push & Commit discipline — Operational_Rules #32 |
| "هل أدفع؟" أو "should I push?" | يُفعّل #32 checklist، أعطِ status report قبل الإجابة |

-----

## Deployment workflow (Windows cmd)

```
cd /d "C:\Thammen\deploy v2"
copy /Y <file>.py <file>.py.bak_<prev_sprint>
git add <files>
git commit -m "<Sprint X.Y.Z>: <description>"
git push heroku master
```

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
