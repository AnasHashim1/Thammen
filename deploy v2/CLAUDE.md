# Thammen — Claude Code Workspace Configuration

> **Project:** thammen.qa — Qatar real-estate AVM (RICS VPS 4)
> **User:** Anas (Qatari, Windows, Heroku deploy)
> **Working directory:** `C:\Thammen\deploy v2`
> **Last update:** 2026-05-22 (after Sprint 2.21.0.7.1 — Land Arc complete)

## Quick orientation

Read these files in order before any technical work:

@./docs/Project_Instructions.md
@./docs/Session_Log.md
@./docs/Empirical_Findings.md
@./docs/Custom_Instructions.md
@./docs/Session_Update_2026-05-19.md
@./docs/Operational_Rules.md

**Most recent state = `Session_Log.md` §12 (2026-05-22, Land Arc through
Sprint 2.21.0.7.1).** The `Session_Update_2026-05-19.md` file is an older delta
(Bug A11 era) kept for history. Newest operational rules: `Operational_Rules.md`
#43–#49. Newest empirical rules: `Empirical_Findings.md` E13–E14.

-----

## Current production state (snapshot)

```
Engine version deployed:  thammen-sprint2p21p0p7p1-hotfix-removed  (Heroku v91)
Latest CHANGELOG:         CHANGELOG_v42.md (2.21.0.7 + 2.21.0.7.1 + hotfix removal)
Latest Sprint:            2.21.0.7.1 (Asset Type Reality Check micro-follow-up)
Tests passing:            69/69 (2.21.0.7 suite); full standalone suite exit 0
                          (test_v2_modules.py needs pytest — not installed; skip)
Critical bugs open:       0
High bugs open:           1  (A6 latency P95 ~25-31s; target 2.18). A8 closed by 2.20.
Medium bugs open:         2  (A5 asset_type unknown, A7 rics_compliant false)
Land Arc:                 ✅ COMPLETE — PIN input (2.21.0) + output polish (2.21.0.5)
                          + Asset Type Reality Check (QARS-in-polygon + General_Landuse
                          RULEID, 2.21.0.7/.7.1). Built→stop/reject; bare→value/reject
                          by authoritative RULEID; precedence QARS>RULEID>geometry.
Mthamen integration:      ⏸️ Deferred indefinitely (see Project_Instructions §20.8)
Roadmap (next):           2.21.0.8 = P3 MoJ lstkhdm usage filter (Arabic NBSP/hamza
                          normalization, ~3% comparables) · 2.21.1 = apartments
                          (MME smoke first, §21.6) · 2.22.x = Map UI (pin-drop → GPS
                          → PIN via CadastrePlots)
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
| "بيانات السكرتيرة جاهزة" | Begin Sprint 2.16.16 (Confirmed Sales — renumbered from 2.16.15) |
| "راجع EMPIRICAL_FINDINGS" | Audit rules E1-E7 |
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
