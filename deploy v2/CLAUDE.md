# Thammen — Claude Code Workspace Configuration

> **Project:** thammen.qa — Qatar real-estate AVM (RICS VPS 4)
> **User:** Anas (Qatari, Windows, Heroku deploy)
> **Working directory:** `C:\Thammen\deploy v2`
> **Last update:** 2026-05-24 morning (after unified closeout for Sprints 2.18.1 + 2.18.1.1 — parallel BFS upfront-prefetch + compound-misroute fix; first documented "latency-unmasks-methodology-bug" case; Operational #52 + EMPIRICAL E20 codified)

## Quick orientation

Read these files in order before any technical work:

@./docs/Project_Instructions.md
@./docs/Session_Log.md
@./docs/Empirical_Findings.md
@./docs/Custom_Instructions.md
@./docs/Session_Update_2026-05-19.md
@./docs/Operational_Rules.md

**Most recent state = `Session_Log.md` §15 (2026-05-23 evening → 2026-05-24
morning, unified narrative for Sprints 2.18.1 + 2.18.1.1 — parallel BFS
upfront-prefetch + compound-misroute fix).** §14 covered Sprint 2.18.0 earlier
that day; §13 covered Sprint 2.21.0.9 Stage 1; §11-12 covered the Land Arc
through Sprint 2.21.0.7.1. The `Session_Update_2026-05-19.md` file is an older
delta (Bug A11 era) kept for history. Newest operational rules:
`Operational_Rules.md` #43–#52. Newest empirical rules:
`Empirical_Findings.md` E13–E20.

-----

## Current production state (snapshot)

```
Engine version deployed:  thammen-sprint2p18p1p1-compound-misroute-fix  (Heroku v101)
Latest CHANGELOG:         CHANGELOG_v46.md (2.18.1.1 Compound-misroute fix; v45 = 2.18.1)
Latest Sprint:            2.18.1.1 (Patches A + C — closes unmasked methodology bug)
Tests passing:            19/19 new (7 functions: promotion 15K/50K, Patch C guard,
                          Lusail premium-land edge case) + 332 prior = 351 across
                          16 standalone files (all exit 0). Run with PYTHONIOENCODING=utf-8.
Critical bugs open:       0
High bugs open:           0  (A6 latency ✅ CLOSED: 89s→28.9s on compound_small,
                          HTTP 503 class eliminated. compound_small extents ≥15K m²
                          now route to clean Income Approach refusal via Patch A
                          promotion to compound_large. Wider cohort: 19% HTTP failure
                          → 0% across 21 reps. A8 closed by 2.20.)
Medium bugs open:         2  (A5 asset_type unknown, A7 rics_compliant false)
Land Arc:                 ✅ COMPLETE — PIN input (2.21.0) + output polish (2.21.0.5)
                          + Asset Type Reality Check (QARS-in-polygon + General_Landuse
                          RULEID, 2.21.0.7/.7.1). Built→stop/reject; bare→value/reject
                          by authoritative RULEID; precedence QARS>RULEID>geometry.
Multi-QARS (2.21.0.9):    ✅ STAGE 1 LIVE — one cadastral PIN with 2+ QARS-addressed
                          villas detected; bracket selection switched from raw PDAREA
                          to PDAREA/n_qars (fixes Bou Hamour 56/565/21 ~30-40% land
                          over-valuation). NO classification (attached vs separate) —
                          GPS centroid alone cannot tell them apart (15.2m can mean
                          either, per MME setback code E15). Stage 2 pre-specified
                          (wall-to-wall rule, E18) for Sprint 2.21.0.10 candidate.
A6 latency arc:           ✅ COMPLETE in 3 Sprints. (1) 2.18.0 Phase 1: 5 parallel
                          property_factors → −4s villa/raw_land (audit prediction
                          ±2%, Rule #51). (2) 2.18.1: parallel BFS upfront-prefetch
                          → −60s compound_small (89s→29s, kills 503 class). (3)
                          2.18.1.1: Patches A+C — promote compound_small→compound_large
                          when extent ≥ 15K m² (E20); universal _decompose_value
                          guard when land>valuation. Sprint 2.18.2 candidate
                          (lite/full GIS dedup, ~−15s) remains queued for Stage-1
                          compliance on compound_small (≤5s target).
Compound-misroute        ✅ CLOSED 2026-05-24 (Sprint 2.18.1.1, v101). Anas's
(unmasked bug):           visual verification 9/9 ✓ — "مجمع فلل كبير" displays,
                          no broken numbers, Income Approach refusal correct,
                          critical material reservation, 6 explicit limitation
                          factors, RICS Red Book recommendations. First documented
                          "latency unmasks methodology" case → Operational #52.
Mthamen integration:      ⏸️ Deferred indefinitely (see Project_Instructions §20.8)
Roadmap (next):           2.18.2 candidate = lite/full GIS dedup + boundary-test
                          optimization (closes Stage-1 ≤5s for compound_small) ·
                          2.21.0.11/.12 candidates = cosmetic UX (rent-input deep-link,
                          negotiation-range box hide when val=None) · 2.21.0.10 = Stage 2
                          wall-to-wall classification (probe Building Footprint layer
                          first) · 2.21.0.8 = P3 MoJ lstkhdm usage filter · 2.21.1 =
                          apartments (MME smoke first, §21.6) · 2.22.x = Map UI
                          (pin-drop → GPS → PIN via CadastrePlots)
Confirmed Sales (2.16.16): still pending the secretary's data
Deploy:                   git subtree push --prefix "deploy v2" (Operational_Rules #43)
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
| "بيانات السكرتيرة جاهزة" | Begin Sprint 2.16.16 (Confirmed Sales — renumbered from 2.16.15) |
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
