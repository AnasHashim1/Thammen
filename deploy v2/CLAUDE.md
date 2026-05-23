# Thammen — Claude Code Workspace Configuration

> **Project:** thammen.qa — Qatar real-estate AVM (RICS VPS 4)
> **User:** Anas (Qatari, Windows, Heroku deploy)
> **Working directory:** `C:\Thammen\deploy v2`
> **Last update:** 2026-05-23 evening (after Sprint 2.18.0 — parallel property_factors)

## Quick orientation

Read these files in order before any technical work:

@./docs/Project_Instructions.md
@./docs/Session_Log.md
@./docs/Empirical_Findings.md
@./docs/Custom_Instructions.md
@./docs/Session_Update_2026-05-19.md
@./docs/Operational_Rules.md

**Most recent state = `Session_Log.md` §14 (2026-05-23 evening, Sprint 2.18.0 —
parallel property_factors fan-out).** §13 covered Sprint 2.21.0.9 Stage 1 earlier
the same day; §11-12 covered the Land Arc through Sprint 2.21.0.7.1. The
`Session_Update_2026-05-19.md` file is an older delta (Bug A11 era) kept for
history. Newest operational rules: `Operational_Rules.md` #43–#51. Newest empirical
rules: `Empirical_Findings.md` E13–E19.

-----

## Current production state (snapshot)

```
Engine version deployed:  thammen-sprint2p18p0-parallel-property-factors  (Heroku v99)
Latest CHANGELOG:         CHANGELOG_v44.md (2.18.0 Parallel property_factors fan-out)
Latest Sprint:            2.18.0 (Parallel property_factors — A6 latency Phase 1 of 2)
Tests passing:            11/11 new (3 functions, including wall-clock concurrency
                          proof) + 269+ prior across 21 standalone files (all exit 0).
                          test_v2_modules.py needs pytest — not installed; skip.
Critical bugs open:       0
High bugs open:           1  (A6 latency: villa/raw_land paths cut −4s by 2.18.0
                          (26.8s→22.8s, 25.1s→21.2s, measured). compound_small extent
                          expansion still ~89s → HTTP 503 class still present.
                          Sprint 2.18.1 = parallel BFS in _expand_extent will close.)
                          A8 closed by 2.20.
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
A6 latency (2.18.0):      ✅ PHASE 1 LIVE — 5 of 6 independent property_factors GIS
                          calls now fan out in parallel via ThreadPoolExecutor
                          (max_workers=5 == task count, E19). Audit-derived −4s
                          delivered on villa/raw_land (audit_a6_2026-05-23.md →
                          CHANGELOG_v44 §5 prediction matched measurement within
                          ±2%, Rule #51). Methodology unchanged. Phase 2 = Sprint
                          2.18.1 (parallel BFS in _expand_extent → kills 503 class).
Mthamen integration:      ⏸️ Deferred indefinitely (see Project_Instructions §20.8)
Roadmap (next):           2.18.1 = parallel BFS in _expand_extent (kill 503 class on
                          compound_small; ~89s→~5-8s on 51/835/17) · 2.21.0.10 = Stage 2
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
| "بيانات السكرتيرة جاهزة" | Begin Sprint 2.16.16 (Confirmed Sales — renumbered from 2.16.15) |
| "راجع EMPIRICAL_FINDINGS" | Audit rules E1-E19 |
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
