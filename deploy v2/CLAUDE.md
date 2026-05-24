# Thammen — Claude Code Workspace Configuration

> **Project:** thammen.qa — Qatar real-estate AVM (RICS VPS 4)
> **User:** Anas (Qatari, Windows, Heroku deploy)
> **Working directory:** `C:\Thammen\deploy v2`
> **Last update:** 2026-05-24 evening (after Sprint 2.21.2 Hybrid Foundation deployed Heroku v107; Pre-Sprint 2.22.0 audit refuted 3-stage premise via H5 FALSE — apartments problem is data not latency; Pre-Sprint 2.21.3 smoke discovered arady `/listings` URL pattern + PropertyFinder DOM-duplication finding; Operational #53 codified; Rule E3 expanded to 8 constraints — see Empirical_Findings.md)

## Quick orientation

Read these files in order before any technical work:

@./docs/Project_Instructions.md
@./docs/Session_Log.md
@./docs/Empirical_Findings.md
@./docs/Custom_Instructions.md
@./docs/Session_Update_2026-05-19.md
@./docs/Operational_Rules.md

**Most recent state = Sprint 2.21.2 Hybrid Foundation deployed Heroku v107
on 2026-05-24 evening + two Pre-Sprint diagnostics flanking it.** Session_Log
§15 still holds the most recent NARRATIVE entry (Sprints 2.18.1 + 2.18.1.1,
parallel BFS + compound-misroute fix). Pre-Sprint artifacts since:

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
for history. Newest operational rules: `Operational_Rules.md` #43–#53
(latest = #53 "Closed cases stay closed — including as comparison anchors").
Newest empirical rules: `Empirical_Findings.md` E13–E20 (Rule E3 itself
expanded to 8 numbered constraints by Sprint 2.21.2 — listings now allowed
tier-weighted entry via `hybrid_valuation_v1()`).

-----

## Current production state (snapshot)

```
Engine version deployed:  thammen-sprint2p21p2-hybrid-foundation  (Heroku v107 code)
                          Heroku slug now at v109 (v107 engine + smoke files removed).
api/health version:       3.1.0-sprint2.21.2
Latest CHANGELOG:         CHANGELOG_v47.md  (2.21.2 Hybrid Foundation; slot drift
                          v43 → v47 documented per Rule #53 spirit)
Latest Sprint:            2.21.2 Hybrid Valuation Foundation
                          - Rule E3 expanded to 8 constraints
                          - hybrid_valuation.py module: HYBRID_TIER_CONFIG +
                            hybrid_valuation_v1() (Cases A/B/C/D + Constraint 7/8)
                          - D5 T2 discount midpoint −12.5%,
                            D6 T3 discount midpoint −17.5%,
                            both `provisional, broker-experience-grounded`
                          - Function exists; NO engine path calls it yet — production
                            behavior identical to 2.18.1.1 (Bou Hamour 56/565/21
                            re-evaluated post-deploy: identical output)
                          - Connectors land in 2.21.3 (T2) + 2.21.4 (T3)
Tests passing:            27 standalone files, all exit 0. Latest counts where
                          reported: 11+12+19+37+67 = 146 sub-checks measured (older
                          files don't print numeric summary). Sprint 2.21.2 added
                          22 functions / 67 sub-checks (H1+H2+H3+H4+H6 all TRUE);
                          H5 (no regression) verified via 27/27 pass.
                          Run with PYTHONIOENCODING=utf-8.
Critical bugs open:       0
High bugs open:           0  (A6 latency ✅ CLOSED via 2.18.0 + 2.18.1 + 2.18.1.1;
                          A8 closed by 2.20)
Medium bugs open:         2  (A5 asset_type unknown, A7 rics_compliant false)

Recent Sprints (chronological):
  2.18.0   Parallel property_factors fan-out (−4s villa/raw_land, v99)
  2.18.1   Parallel BFS upfront-prefetch (−60s compound_small, v100, kills 503)
  2.18.1.1 Compound-misroute fix Patches A+C (v101)
  2.21.2   Hybrid Foundation: Rule E3 → 8 constraints + hybrid_valuation.py (v107)
  → all live; engine version reflects the most recent (2.21.2).

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

Roadmap (priority order, post-2.21.2):
  1. Sprint 2.21.3 — T2 connectors (arady /listings + PropertyFinder).
                     Inputs ready in 2p21p3_pre/. Needs BRIEF from Claude.ai
                     (lane discipline). Connector MUST deduplicate per
                     DOM finding above.
  2. Sprint 2.21.4 — T3 schema (developer_inventory.sqlite + Aryan manual
                     entry). Function is null-safe for T3 absence.
  3. Sprint 2.21.5 — UI tier breakdown + MUC surfacing for hybrid outputs.
                     Needs 2.21.3 + 2.21.4 shipped.
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
  9. Sprint 2.16.16 — Confirmed Sales DB. Secretary data uncertain
                     (per Anas 2026-05-24); recalibration of D5/D6
                     shifts to brokerage-pipeline-only path (≥30 (asking,
                     close) pairs as the trigger). NOT a blocker for 2.21.2
                     or anything depending on it.

D5/D6 calibration:        provisional, broker-experience-grounded.
                          Recalibration trigger = brokerage Confirmed Sales
                          pipeline produces ≥30 (asking, close) pairs.
                          Empirical basis: EMPIRICAL_FINDINGS §3 asking-
                          premium ranges + broker negotiation experience.

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
4. Regression tests: 81/81 must pass (post-2.16.15 baseline)
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
| "تذكر Rule E3 v2" أو "تذكر 8 constraints" | Rule E3 in `docs/Empirical_Findings.md` was rewritten 2026-05-24 by Sprint 2.21.2. Now 8 numbered constraints: (1) T2 cap 0.40 with T1 + D5 discount; (2) T3 cap 0.15 + D6 discount; (3) T1 floor 0.45 when present; (4) no T1 → indicative ceiling; (5) mandatory MUC ±20% when T1 absent; (6) source-level transparency (E10); (7) like-for-like unit normalization (RICS VPS 4); (8) T3 alone insufficient. E1 (no MoJ uplift) preserved. |
| "تذكر Pre-Sprint 2.22.0" أو "تذكر H5 FALSE" | Pre-Sprint 2.22.0 audit (2p22p0_pre/CHANGELOG, 2026-05-24). Tested whether 3-stage UX architecture solves the apartments gap. H5 FALSE was decisive: 52/903/90 apartment_building returns HTTP 200 + valuation_amount=None + 4.7s — failure is data-driven, not latency-driven. 3-stage would just rename "insufficient data" across two stages. Sprint 2.22.0 deferred; BRIEF_2p21p2 (hybrid foundation) returned to top of queue and shipped. H1 TRUE + H3 TRUE + H4 TRUE evidence preserved for future UX-refactor Sprint after 2.21.5. |
| "تذكر Pre-Sprint 2.21.3" أو "تذكر DOM duplication" أو "تذكر arady /listings" | Pre-Sprint 2.21.3 smoke (2p21p3_pre/CHANGELOG, 2026-05-24 evening). 4 of 5 TRUE. arady canonical search URL = **`/listings`** (HTTP 200, 70 listing hits page 1, sitemap.xml available for full inventory). PropertyFinder reachable from Heroku (exact parity with sandbox; raw=142 = sandbox=142). H2 FALSE was a threshold artifact: PropertyFinder DOM duplicates listing nodes ~6× (142 raw → 24 unique on Lusail page 1). **Sprint 2.21.3 connector MUST deduplicate by canonical URL or listing ID.** Detail-page schema confirmed extractable: CSS class `property-price` + regex fallback for QAR/AED + regex for m²/sqm. |
| "تذكر D5/D6" أو "تذكر calibration provisional" | `HYBRID_TIER_CONFIG` ships with D5 T2 discount midpoint −12.5% (range −10%/−15%) and D6 T3 discount midpoint −17.5% (range −15%/−20%), both tagged `provisional, broker-experience-grounded`. Empirical basis: EMPIRICAL_FINDINGS §3 asking-premium ranges (+8% to +20% inverted). Recalibration trigger: brokerage Confirmed Sales pipeline produces ≥30 (asking, close) pairs. Secretary data may never arrive (per Anas 2026-05-24) — recalibration is on the brokerage-pipeline-only path; not a blocker for 2.21.2 or anything depending on it. |
| "بيانات السكرتيرة جاهزة" | Begin Sprint 2.16.16 (Confirmed Sales — renumbered from 2.16.15). NOTE 2026-05-24: per Anas this data may never arrive; D5/D6 recalibration migrated to brokerage-pipeline-only path. |
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
