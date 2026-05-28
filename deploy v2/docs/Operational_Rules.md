# Operational Rules — Cross-Session Memory

> **Purpose:** This file is the migration of the 30 memory slots from the
> previous Claude.ai session into a persistent format for Claude Code.
> Read it alongside Project_Instructions, Session_Log, and Empirical_Findings.
>
> **Status:** Last extracted from memory 2026-05-19 PM. Items marked ✅ are
> resolved bugs; items marked ⚠️ are active constraints; unmarked items are
> reference rules.

-----

## 1. Net rental yield in Qatar — user-corrected

Net yield (not gross) for residential apartments in Qatar:
- **5–6%** = normal
- **>6% net** = bargain (worth inspecting)
- **<4% net** = weak, avoid

**Never present gross without net.** Gross is misleading.

Net yield formula:
```
net = (annual_rent − service_charges − vacancy − maintenance − management) / value
```

Documented references:
- Global Property Guide Q1 2025: Pearl 4.57%
- hapondo Q4 2023: Pearl 1BR 6.4% gross
- FGREALTY: 6-7% gross corresponds to 4.5-5.5% net

-----

## 2. Qatar GIS — useful layers

| Layer | Purpose |
|---|---|
| `QARS_Point/FeatureServer/0` (khazna) | Address → GPS, PIN, BUILDING_NO_SUBTYPE |
| `QARS_Search/MapServer/0` (legacy) | Same as above, fallback only |
| `CadastrePlots/MapServer/0` | Polygons + PDAREA + PD_NO |
| `Districts/MapServer/0` | Area names (ANAME, ENAME, DIST_NO, CODE) |
| `Zoning/MapServer/0` | R1/R2/R3/CCC/COM/MU*/etc. |
| `Imagery_1995..2024` | Historical building age detection |
| `Landmarks/MapServer/0` | Landmarks with CATEGORY (GOVERNMENT/BUSINESS/etc.) |
| `Commercial_StreetsA/MapServer/0` | Officially designated commercial streets |
| `General_Landuse/MapServer/0` | BUILDING_HEIGHT permitted |
| `ROADFlowlnA/MapServer/0` | ROAD_CLASS (L1=Local, L2=Main) |
| `NewParcelsPricing1` | Practically empty, ignore |

GIS deep link discovered from Mthamen APK (optional UI sweetener):
```
http://geoportal.gisqatar.org.qa/searchpin/?pin=<PIN>
```

-----

## 3. PD_NO=0 signature

`PD_NO=0` in CadastrePlots is **not** an error — it means "single un-subdivided
cadastral parcel". This is the strong signature of large compounds in areas
like Izghawa/Al-Gharafa. Use it early to distinguish a compound from a
standalone villa.

-----

## 4. Compound boundaries ≠ single cadastral polygon

Large compounds may consist of **multiple adjacent cadastral parcels**
(different PINs, sometimes different PD_NO values) that form a single
architectural compound. Definition is visual (uniform building pattern),
not by single PIN.

Detection: check adjacent large parcels (≥10,000 m²) within 500m radius,
then verify on aerial imagery for architectural unity.

-----

## 5. Visual unit counting unreliable

Visual unit counting in townhouse compounds is **unreliable** — can be off
by 100%. Reason: closely-built small villas (~200 m²) merge visually.
Use visual count as indicative range only; request actual number from
owner or municipality maps before final valuation.

-----

## 6. Building age from historical imagery

GIS Qatar imagery is more reliable than owner statements and independently
verifiable. Available services:
- QatarOrtho_1995, QatarOrtho_2004
- QatarSatelitte_2003/2010/2012/2017/2019/2021
- QatarSatelitte2024

Accuracy: ±3 years between any two consecutive images.

-----

## 7. Valuation methodology by asset type

1. **Standalone subdivided villa** → MoJ comparison (same bracket, same district)
2. **Small compound ≤15,000 m²** → MoJ "مجمع فلل" comparison
3. **Large compound ≥50,000 m²** → yield-only (no MoJ comparable; largest
   recorded "مجمع فلل" is 15,027 m²)
4. **Raw land** → MoJ comparison by similar size bracket

Applying MoJ comparison to a large compound produces badly wrong numbers.

-----

## 8. Compound yield valuation standards (Class B residential)

Operating expenses: **23% of income**
- 10% maintenance
- 5% management
- 5% insurance/utilities
- 3% standard vacancy reserve (even at full occupancy)

Cap rates (Class B):
- 7.0% strategic buyer
- 7.5% fair value
- 8.0% conservative market
- 8.5% distressed sale

Every 0.5% change in cap rate = ~18-20M QAR difference on a 300M compound.

-----

## 9. When user data conflicts with my estimate

If user says "275 units" and I estimated "120-140": the correct response is
to **re-examine foundational assumptions** (especially asset boundary
assumptions), not defend the original estimate.

User challenge typically reveals a methodological error in assumptions,
not a challenge to truth.

-----

## 10. QARS as completion proof

In Qatar, a QARS building number is **only assigned after construction
completion**. Having a complete address (Zone+Street+Building) is
conclusive evidence the villa exists and is habitable — even without
site inspection.

-----

## 11. ⚠️ GIS Qatar — 2026-05-17 endpoint migration

Old `services.gisqatar.org.qa/Vector/QARS_Search/MapServer/0` was replaced
by `khazna.gisqatar.org.qa/fed/rest/services/QARS/QARS_Point/FeatureServer/0`
(same schema + bonus BUILDING_NO_SUBTYPE).

Heroku can reach khazna (89.211.33.46) but Claude container cannot
(outside allowlist). Legacy came back online 2026-05-18 but Thammen uses
khazna primary with safe fallback. Query pattern unchanged:
```
where=ZONE_NO=X+AND+STREET_NO=Y+AND+BUILDING_NO=Z
```

-----

## 12. MoJ — automatic download

JSON API: `data.gov.qa/api/explore/v2.1/.../records?limit=100&offset=N`

⚠️ **`curl` hangs** but Python `urllib` works.

Pagination workaround for the 10K offset limit:
```python
where=registration_date  # filter by 18-month windows
```

API fields: registration_date, sm_lmntq (district), nw_l_qr (type),
price_per_square_meter, area_square_meters, property_value.

Result: ~26,719 transactions, ~100 seconds to download. No more manual.

-----

## 13. MoJ — 14 column schema

```
رقم المعامله المرجعي
رقم العقار المرجعي
تاريخ التثبيت              ← contains NBSP \xa0
اسم البلدية
اسم المنطقة
نوع العقار
الاستخدام
المساحة بالمتر المربع
مساحة الحصص المباعة
سعر القدم المربع
سعر المتر المربع
عدد الحصص المباعة (2400)
قيمة الحصص المباعة
قيمة العقار
```

Dates: YYYY-MM-DD. Prices and areas: decimal numbers.

-----

## 14. ⚠️ Critical MoJ data issue — NBSP duplication

Same value appears in two versions — with NBSP (`\xa0`) and with regular
space (`\x20`). Examples:
- "أرض فضاء" 8499 transactions with NBSP + 5656 with regular space
- "بيت للسكن" 1730 with NBSP + 1381 with regular space
- "أم صلال" with NBSP + "أم صلال" with regular space

**The column name "تاريخ التثبيت" itself contains NBSP.**

Solution: never match strings directly. Always normalize first:
```python
re.sub(r'\s+', ' ', s).strip()
```

Without this, you lose ~50% of data.

-----

## 15. MoJ — municipality distribution

| Municipality | Transactions |
|---|---|
| Doha | 6,811 |
| Al-Rayyan | 6,543 |
| Al-Daayen | 4,899 |
| Al-Wakra | 3,013 |
| Umm Salal | 2,623 |
| Al-Khor & Al-Dhakira | 1,528 |
| Al-Shamal | 1,229 |
| Al-Shahaniya | 73 |

Common asset types (after NBSP merge):
- أرض فضاء: 14,155
- فيلا: 3,032
- بيت للسكن: 3,111
- فيلا من طابقين وملحق: 1,461

Rare but useful: مجمع فلل, عمارة سكنية, برج سكني, قصر, مزرعة.

-----

## 16. MoJ reference building rules

1. Area name may be split by zone number ("ازغوى 51", "ازغوى 71") or
   without ("ازغوى") — merge all variants and filter by municipality
   to disambiguate.
2. Reference window: **24 months default**, 36-month fallback if n<20.
3. Thresholds: n≥20 reliable, 10-19 indicative, 5-9 boundary only,
   <5 produce no median.
4. Size brackets: 0-400 / 400-600 / 600-900 / 900-1500 / 1500+ m².
5. Use **median, not mean** (mean is distorted by outliers).

-----

## 17. ⚠️ Compound detection — irregular shape warning

Qatari plots are almost always rectangular or square. Any polygon with
**irregular shape** (>5 vertices, non-convex, L-shape, internal voids)
is a strong warning sign of a **missing adjacent plot**.

Example from Izghawa session: PIN 51500109 appeared with irregular
shape in the SW corner because PIN 51500120 (3,752 m², PD_NO=0) was
part of the compound but not captured.

**Rule:** When drawing a non-rectangular polygon, stop and check
adjacent small plots before finalizing asset boundaries.

-----

## 18. detect_compound_extent — algorithm fix

`detect_compound_extent` must **not** use `min_area=10,000` as a hard
filter — it would drop small connected pieces (2,000-5,000 m²) that
belong to the compound with `PD_NO=0`.

Correct algorithm:
1. Find all parcels connected to seed by shared boundary (min_area=200 to skip noise)
2. Include if `area ≥ 10,000` OR (`PD_NO=0` AND connected to discovered compound member)
3. Exclude if `PD_NO≠0` AND `area<5,000` (individual subdivided residential plot)

-----

## 19. BUILDING_NO_SUBTYPE from QARS_Point (Sprint 2.16.5/6)

Subtype codes used in classifier Branch 0:

| Code | Type | AssetType mapping |
|---|---|---|
| 1 | Villa/House | STANDALONE_VILLA |
| 2 | Compound with Villas | COMPOUND_SMALL |
| 3 | Compound with Villas+Flats | COMPOUND_SMALL |
| 4 | Shopping Complex | COMMERCIAL |
| 6 | Building with Flats | APARTMENT_BUILDING |
| 11 | Tower | TOWER (A1 fix) |
| 13 | Commercial | COMMERCIAL |

Fallback to legacy area heuristic when subtype = None/0/unmapped.

Sprint 2.16.6 fix scope: 15,881 polygons (3K-10K m²) previously
misclassified as "palace" including all Lusail/West Bay towers.

DCF-supported types: tower, apartment_building, compound_large.

-----

## 20. ✅ Bug A11 — Resolved Sprint 2.16.14 (CHANGELOG_v35, 2026-05-19 PM)

QARS_Point subtype is stale 2010-2012 for buildings that changed use
(example: أشغال 61/875/20 — subtype=6 "Flats" but Zoning=CCC).

Audit result: 9.1% mismatch on 22 government/business landmarks
(GOVERNMENT 25%, BUSINESS 0%, FINANCE 0%).

Now Branch 0 cross-checks:
```
subtype ∈ {1, 6, 11} AND zoning ∈ {CCC, COM, CF, SCZ, TU, LFR, LInd, IND, MU*}
→ emit subtype_zoning_mismatch flag (non-blocking)
→ downgrade confidence to 'medium'
→ add COMMERCIAL to alternative_types
```

asset_type is NOT changed — user decides.

-----

## 21. District naming — GIS is sole authority

When determining area name for a property, **GIS is the only reference**
and cannot be overridden. No aliases, no "the market calls it X",
no geographic-proximity guessing.

Example: Even if locals call a Gharafa property "Izghawa", the system
uses GIS name only and builds the MoJ reference accordingly.

This rule came from user correcting a previous attempt to add an
aliases table.

-----

## 22. PIN 51500109 — reference case

- Location: Z51/S835/B17, GPS 25.346°/51.454°
- **GIS district = الغرافة** (DIST_NO=47)
- Market commonly calls it "ازغوى" — this is colloquial, not administrative
- When building MoJ reference for this compound, use "الغرافة" exclusively

(This corrects a previous memory linking it to Izghawa.)

-----

## 23. Zone ≠ administrative district

Zone in GIS Qatar is NOT a synonym for administrative district.
Zone 70 contains ≥6 different GIS districts (لعبيب, الصخامة, العب,
أم قرن, سميسمة, الخيسة).

The zone number organizes addressing, not boundaries.

To get accurate district name from address:
1. First fetch GPS coordinates from QARS_Search
2. Then query `Vector/Districts/MapServer/0` spatially on that point

**Do not assume a fixed Zone→Area mapping.**

-----

## 24. ⚠️ Arabic tables in docx + LibreOffice

With `visuallyRightToLeft:true` (translated to `<w:bidiVisual/>`),
the correct cell order in array is `[right, left] = [label_arabic, value]`.

`array[0]` appears on the right (natural for Arabic reading); `array[N-1]`
appears on the left. **Do not try to reverse or "flip" it.**

Write data in the reading order (right→left) directly in the array.

Example: headerRow `["البند", "القيمة"]` → "البند" right, "القيمة" left.
Applies to both LibreOffice and MS Word.

-----

## 25. ⚠️ docx — numbers/Latin inside Arabic text — bidi reversal risk

Text like "31 / 918 / 99" or "PD/4298/2010" inside a cell with
`rightToLeft:true` may visually reverse to "99 / 918 / 31".

Solution: wrap text with U+200E (LRM) on both sides:
```javascript
`\u200E${text}\u200E`
```

Set `rightToLeft: false` on TextRun if text is purely Latin/numeric.

Text detector:
```javascript
/[A-Za-z0-9]/.test(t) && /[\/.,:°²×\-–]/.test(t)  // needs LRM (Sprint 2.22.0a.3: added EN-DASH)
/[\u0600-\u06FF]/.test(t)                          // pure Arabic, keep rightToLeft:true
```

**Separator class history.** Sprint 2.22.0a.3 added EN-DASH (the
"range dash", U+2013) to the class. Without it, year-range tokens
embedded in Arabic (such as the suppressed-trend headline that
emits the Arabic word for "window" followed by `2020`, EN-DASH,
`2025`) would not trigger the detector and would ship unwrapped.
Same bidi-reversal class as the `31/918/99` reversal. Hyphen-minus
(`-`, U+002D) was already in the class for ISO date tokens such
as `2025-12-31`; the EN-DASH addition catches range expressions.
EM-DASH (U+2014) is NOT in the class: it typically separates
Arabic clauses on both sides, so the `/[A-Za-z0-9]/` test fails
on both sides and no LRM is needed.

-----

## 26. ⚠️ docx-js v9.6 bug in pBdr (paragraph borders)

Generates (top, bottom, left, right) order but OOXML schema requires
(top, left, bottom, right). `validate.py` fails with
"Element w:left not expected".

Solution: post-process on `document.xml` after generation — regex on
`<w:pBdr>...</w:pBdr>` and reorder children. Does not happen in
table borders.

Every docx containing a paragraph border needs this fix before pack.py.

-----

## 27. evaluate_property.py v2 — BUA breakdown

Component-aware BUA parameters:
- `--main-footprint`
- `--basement-area`
- `--upper-floors-area` (+ count)
- `--annexes-area` (+ count)
- `--external-area`

Cost ratios relative to base tier:
- Basement ×1.17
- Ground floor ×1.0
- Upper floors ×0.93
- Annexes ×0.73
- External ×0.67

Annexes are always single-story ground level and cheaper to build.

**Lesson:** Equal-component approximation errs by ±10% vs detailed
breakdown. Also supports `--listing-bua` as flat number (backward compat).

-----

## 28. MME API — third government data source

Authentication:
```
GET qrepcms.aqarat.gov.qa/flows/trigger/412A3B92-16F9-437D-AAFC-BBE5E25ED9F5
→ returns JWT (verified reachable from Heroku 2026-05-24, HTTP 200 in ~0.9s)
```

⚠️ **Auth scope** (verified 2026-05-24, smoke v1+v2): this public
flow-trigger issues an **anonymous Directus token** —
`{role: null, app_access: false, admin_access: false, iss: "directus"}`.
With this token, kpi29 returns HTTP 200 + `{count:0, transactionList:[]}`
for every propertyType / areaCode / window combination. The authenticated
session token (the one used by the mme.gov.qa web app after user login)
is required for actual data; capture via browser DevTools is the only
known path today.

Sales endpoint:
```
POST qrepbe.aqarat.gov.qa/mme-services/kpi/sell/kpi29/transactions
Params: issueDateYear, StartMonth, EndMonth, municipalityId, areaCode, propertyTypeList

Response schema (verified 2026-05-24 — extractor key is transactionList,
NOT data/transactions/result/records):
{
  "count": <int>,
  "transactionList": [ <row>, … ]
}
```

Rentals — **paths verified dead 2026-05-24, needs re-discovery**:
```
POST .../kpi/rent/kpi30           → 404
POST .../kpi/rent/kpi30/transactions → 404   (mirroring sell path shape)
POST .../kpi/rent/kpi30/list      → 404
POST .../kpi/rent/kpi30/data      → 404
POST .../kpi/rents/kpi30/...      → 404      (plural)
POST .../kpi/lease/kpi30/...      → 404
POST .../kpi/rental/kpi30/...     → 404
GET  .../kpi/rent                 → 404      (directory listing)
```
Tested 7 path variants + 1 GET — all 404. The kpi30/31/32 endpoint
shape from a now-unknown reference must be rediscovered via DevTools
on the rental KPIs page of mme.gov.qa.

Property types: 1=villas, 5=apartments, 6=land.

**Apartments are exclusively here** (MoJ does not contain individual
apartment units). Pearl Qatar areaCode=765, Lusail areaCode=812.

`mme_reference.py` tool referenced in older docs is **not in the live
codebase** (verified by grep 2026-05-24); any client built on top of MME
must use the auth-scope-aware pattern documented above.

-----

## 29. ⚠️ Service charges for Pearl/Lusail apartments — FGRealty verified

**Use FGRealty individual listings**, not their blog.

Pearl Qatar:
- 14-15 QAR/sqm/month = 168-180 QAR/year
- Qanat Quartier 14, Porto Arabia 15

Lusail:
- 10-14 QAR/sqm/month = 120-168 QAR/year
- Fox Hills 10, Marina/Place Vendome 14

Planning averages: Pearl ~200/year, Lusail ~100-150/year.

Pattern in FGRealty individual listings: `"Service Charge QAR XX/sqm"`
(scrapeable).

⚠️ FGRealty blog says 60-120 — outdated/misleading. Use individual
listings only.

-----

## 30. ⚠️ 2026-05-19 Decision — Mthamen integration deferred indefinitely

Evidence:
- `smoke_mthamen.py` from Heroku → HTTP 200 + F5 BIG-IP ASM rejection
- `smoke_mthamen_v2.py` from Heroku → 0/6 profile bypass, 6/6 WAF rejected
  (even bare site root)
- Anas's iPhone (Qatar SIM): 1 attempt → "لقد تخطيت الحد الأقصى للمحاولات"
  (daily quota ≈ 1/day)

The DRC methodology (Land 9 premiums + Building 4 layers - Depreciation)
remains a documented reference in Project_Instructions §20.
`mthamen_reference.py` is archive only — never deployed.

**Generalized rule:**
```
smoke_<endpoint>.py from Heroku BEFORE any Qatar government
endpoint integration. 15 minutes saves 3+ hours.
```

Three conditions for revival:
1. WAF block mitigated (verify with smoke tests from Heroku)
2. Daily quota >10/day demonstrated
3. (Preferred) Official MoJ Qatar API access

**Without all three, any revival proposal must be rejected.**

-----

## 31. ⚠️ Pydantic schema lenience — Bug A2, Sprint 2.16.15 (2026-05-19 evening)

**Discovered**: Cataloged as Medium open Bug A2 since the Sprint 2.16.7
housekeeping pass. **Resolved**: Sprint 2.16.15 (CHANGELOG_v36), deployed
2026-05-19 evening — first Sprint shipped from Claude Code.

**Root cause**: Pydantic v2's default model config is `extra='ignore'`
(matching v1). That means any field not explicitly declared on a `BaseModel`
is **silently dropped** before reaching application code. For
`EvaluateRequest` / `EvaluateDetailsRequest`, this turned the canonical typo
into a silent confidence gap:

```http
POST /api/evaluate
{"zone":51, "street":835, "building":17, "rental_inome": 30000}
                                          ^^^^^^^^^^^^ typo
```

Pydantic accepted the payload, dropped `rental_inome`, called
`evaluate_thammen(..., rental_income=None)` → engine took
`insufficient_data` fast path → user saw "بيانات غير كافية" while believing
their 30K rent was in the calculation.

Same hazard covered: UI ↔ API drift (e.g. UI sends `listing_price` while API
expects `asking_price`), Arabic field names accidentally posted, fields meant
for `/api/evaluate/details` posted to `/api/evaluate` (e.g. `floors`,
`condition`, `basement` were all silently dropped if sent to the quick
endpoint).

**The rule** (mandatory for every HTTP-facing Pydantic model):

```python
from pydantic import BaseModel, ConfigDict, Field

class MyRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')   # ← first line in the class
    zone: int
    ...
```

Pydantic then returns HTTP 422 with this structured detail:

```json
{"detail": [{
    "type": "extra_forbidden",
    "loc":  ["body", "rental_inome"],
    "msg":  "Extra inputs are not permitted",
    "input": 30000
}]}
```

The bad field name lives in `loc[-1]`, so a future Arabic-localized client
can render "حقل غير معروف: rental_inome" instead of a generic "validation
error".

**Where it does NOT apply**:
- `evaluate_unified.py:main()` CLI path — argparse doesn't go through
  Pydantic. CLI users who pass `--rental -1000` get a different defense
  layer (`_check_input_sanity` warning).
- Internal scripts that call `evaluate_thammen(**kwargs)` directly — Python's
  default `TypeError: unexpected keyword argument` handles that case.
- `evaluate_unified.py` itself has no Pydantic models; this rule is API-only.

**Verification pattern** (use for any future request model):
```python
try:
    Model(zone=51, street=835, building=17, bogus_field=1)
    assert False, "should have rejected"
except ValidationError as e:
    err = e.errors()[0]
    assert err['type'] == 'extra_forbidden'
    assert err['loc'][-1] == 'bogus_field'
```

**Why this earns a rule slot**: The defect was *silent* — no 4xx, no 5xx,
no log line. The user got a coherent-but-wrong fast-path response. This is
the worst class of boundary failure: indistinguishable from "no data
provided" both visually and in telemetry. The rule prevents the next FastAPI
model from re-introducing it.

-----

## 32. ⚠️ Push & Commit Discipline — متى تدفع، متى تمتنع

**Discovered**: 2026-05-19 evening, Sprint 2.16.17 scouting session.
Pattern observed: Claude Code in worktree branch (`claude/<name>`) attempted
`git commit` and was on path toward `git push heroku master`. كلاهما كان
يكسر discipline:
- Worktree branch commits don't reach master without explicit merge
- Push from worktree branch can target wrong git ref
- Push during scouting bypasses §3 pre-deploy 6-item checklist
- Docs-only push triggers Heroku rebuild + log churn for zero behavior change

### Push decision tree (الأكثر صرامة)

**NEVER push to Heroku unless ALL of these are TRUE:**

1. **Branch check**: على `master`, ليس worktree/feature branch.
   تحقّق: `git rev-parse --abbrev-ref HEAD` → must return `master`

2. **§3 Pre-deploy 6-item checklist** نُفِّذ في هذه الجلسة:
   - py_compile على كل ملف Python معدَّل ✓
   - node --check على JS من index.html (لو تغيّرت) ✓
   - Mobile viewport test 390×844 (لو index.html تغيّرت) ✓
   - Regression tests تنجح (current baseline من CLAUDE.md) ✓
   - Isolated logic tests للكود الجديد (5+ cases مع fallback) ✓
   - Smoke test plan جاهز لـ 3 عناوين متنوعة (NOT 51/835/17 — Bug A6) ✓

3. **Sprint integrity:**
   - ENGINE_VERSION + SPRINT_TAG bumped في evaluate_unified.py لو behavior تغيّر
   - CHANGELOG_v{N}.md موجود، يتبع نمط v33/v34/v35/v36
   - Single-purpose Sprint (لا bundling مع Sprints أخرى)

4. **Explicit user consent** في الرسالة الحالية أو السابقة مباشرة:
   - الكلمات الصريحة: "push", "deploy", "ship", "نشر", "ادفع", "deploy it now"
   - أو: documented final step من Sprint plan معتمد سابقاً في الجلسة

### ALWAYS refuse to push (حتى مع consent ظاهري)

- Branch الحالي = worktree branch (commits معزولة)
- أي test فاشل (regression أو جديد)
- User قال: "scout only", "plan only", "no push", "لا تنشر", "review", "للمراجعة"
- api.py لم يُلمس و ENGINE_VERSION لم يتغيّر = deploy = no-op churn
- Commit يخلط Sprint X + Sprint Y work غير مترابط
- git status فيه untracked files تنتمي لنفس الـ logical commit لكن لم تُراجَع

### Commit decision tree (منفصل عن push)

**Commit when:**
- Work-unit متماسك انتهى (Sprint patch، scouting doc، audit، 4-file batch)
- الملفات استقرّت (لا تعديلات متوقعة في الجلسة الحالية)
- User قال "commit", "save", "احفظ", "نفّذ الـ commit"
- Worktree branch أنهت نطاقها (commits تبقى في branch — fine، لكن أبلغ user)

**Do NOT commit when:**
- Mid-iteration: ملفات قد تتغيّر بعد
- User قال "no commit", "don't save", "لا تلتزم", "scout only"
- Untracked sibling files تنتمي للـ commit المنطقي نفسه لكن لم تُراجَع
- في worktree branch + User يتوقع التغييرات في master → بدل commit،
  قل صراحة: "الملفات في worktree path X. لإحضارها لـ master، شغّل من
  master terminal: `git checkout <branch> -- <path>` أو `copy /Y`"

### When in doubt — DEFAULT: لا تدفع، اسأل صراحة

السؤال للـ user: "Should I push to Heroku now? Currently: branch=X, tests=Y/Z,
ENGINE_VERSION bumped: yes/no, CHANGELOG: present/absent."

التكلفة المقارنة:
- عدم الدفع: 30 ثانية ينفّذ Anas `git push heroku master` بنفسه
- الدفع الخاطئ: production deploy، log churn، regression محتملة، Sprint atomicity مكسورة

### Reminders محددة

- **Worktree branches معزولة**. Commit في worktree لا يصل master إلا بـ merge.
- **Docs-only push**: ملفات `.md` و `.gitignore` لا تغيّر runtime، لكن Heroku
  يُعيد البناء + يقلّب dynos. Batch docs commits مع Sprint كود التالي بدل
  push منفصل.
- **`git push heroku master`** يتطلّب local master يحتوي الـ commits. لو
  commits على branch منفصل، merge to master أولاً.

-----

## 33. Empirical-First Audits — قِسْ قبل أن تقرأ

**Discovered**: Sprint 2.16.17 scouting, 2026-05-19. أول مسودة أرادت قراءة
api.py لاكتشاف slowapi config. الواقع: curl × 25 على /api/health كشف فوراً
"لا rate limit موجود" — دون فتح أي ملف.

**القاعدة**: قبل قراءة كود في أي audit، نفّذ القياسات التي تختبر السلوك
الإنتاجي الفعلي:
- curl burst → ما هو السلوك الحقيقي؟
- `heroku logs --num=N | head/tail` → ما الإطار الزمني والـ patterns؟
- `git log --all -- <path>` → هل الملف موجود في التاريخ؟
- `curl -I` → ما الـ headers الفعلية؟

**ترتيب الـ audit الإلزامي:**
1. Empirical baseline (5-10 دقائق)
2. ثم قراءة الكود لفهم "لماذا"
3. ثم خطة Sprint بناءً على فجوة (المُقاس) − (المُنتظَر)

**Anti-pattern**: قراءة `api.py` لاستنتاج "rate limit موجود لأنه import slowapi"
بدون تأكيد أنه فعلاً يَحجب. الـ import وحده لا يعني التفعيل.

-----

## 34. File-Based Scripts for External Endpoints — لا تشغّل inline

**Discovered**: 2026-05-19 evening. محاولة `heroku run python -c "import
urllib...; for i in range(30): ..."` كسرت Windows cmd بسبب escaping للـ `&`،
`=`، `+`، quotes. النتيجة: انحراف لـ sandbox مع تبرير ضعيف.

**القاعدة**: لكل اختبار شبكي أو سكربت multi-line يستهدف endpoint خارجي
أو يحتاج Heroku dyno:

1. اكتب ملف Python كامل (مثل `probe_X.py`، `smoke_X.py`)
2. ادفعه ضمن repo (مؤقتاً)
3. `heroku run python probe_X.py`
4. اقرأ الناتج

**ممنوع**:
- `heroku run python -c "..."` مع أي argument يحوي `&`, `=`, `+`, `'`, `"`
- `heroku run python -c "..."` مع أكثر من 3 أسطر منطق
- "حلّ مكانه" تشغيل من sandbox/container لأن heroku run "متعب"

**سوابق ناجحة**: smoke_mthamen.py + smoke_mthamen_v2.py (Session_Log §1،
2026-05-19). نفس النمط ينطبق على أي endpoint قطري حكومي أو probe خارجي.

**حالة استثناء**: استعلام بسيط جداً بلا quotes/specials، مثل
`heroku config:get DATABASE_URL`. هذه أوامر CLI نظيفة، ليست Python inline.

-----

## 35. Library Version Verification — تحقّق على Heroku، ليس requirements فقط

**Discovered**: Sprint 2.16.15 — Pydantic 2.x ConfigDict syntax. Sprint
2.16.17 — slowapi list vs string syntax. كلا الـ Sprints احتاج تحقق فعلي
قبل كتابة syntax. requirements.txt قد يكون pinned، lock-free، أو يحتوي
نطاقاً (`>=0.1.0`). الحقيقة على Heroku قد تختلف.

**القاعدة**: قبل استخدام أي syntax من مكتبة، تحقّق من نسختين:

1. **requirements.txt** (declared intent):
   `findstr /I "slowapi" requirements.txt`

2. **Heroku installed reality** (file-based per #34):

```python
   # check_version.py
   import slowapi, pydantic, fastapi
   print('slowapi:', slowapi.__version__)
   print('pydantic:', pydantic.VERSION)
   print('fastapi:', fastapi.__version__)
```

   `heroku run python check_version.py`

لو الاثنين مختلفان → ذكِّر user بالاختلاف قبل المتابعة.

**ممنوع**:
- كتابة decorator/import syntax بناءً على معرفة عامة بدون تأكيد النسخة
- الافتراض أن Pydantic v1 syntax يعمل في Pydantic 2 (أو العكس)
- استخدام syntax مهجور (deprecated) دون التحقق من warning في النسخة الحالية

**سابقة ناجحة**: Sprint 2.16.17 scouting — تأكيد slowapi 0.1.9 قبل اختيار
`@limiter.limit([...])` list form. لو افترضنا الـ string form، Sprint كان
سيفشل عند التنفيذ.

-----

## 36. Observed-vs-Expected Reporting — اذكر العيّنة الفعلية لا المتوقَّعة

**Discovered**: Sprint 2.16.17 audit v2 ادّعى "0 × 429 in 5000 lines of
logs". إعادة التحقّق كشفت أن Heroku capped عند 1500 سطر، تغطّي ~33.75
ساعة. الادعاء "5000 lines" خطأ، لكن الاستنتاج "0 × 429" ما زال صحيحاً
ضمن العيّنة الحقيقية.

**القاعدة**: عند تقديم أي finding empirical، اذكر:

| العنصر | مثال صحيح | مثال خاطئ |
|---|---|---|
| Sample size الفعلي | "1500 سطر" | "5000 lines" (افتراض) |
| Time window الفعلي | "33.75 ساعة، 2026-05-18 08:42 → 2026-05-19 18:28" | "آخر أيام" |
| ما لم يُرَ | "لا تغطّي ما قبل 2026-05-18 08:42 UTC" | (يُحذف) |
| Failure modes الفعلية | "8×200 + 2×503 (Heroku 30s router timeout)" | "20% فشل" |

**صياغة جيدة**: "في **1500 سطر** من Heroku logs تغطّي **33.75 ساعة** بين
2026-05-18 08:42 و 2026-05-19 18:28 UTC، **0** × 429 ظهر."

**صياغة سيّئة**: "logs نظيفة، لا rate limit triggers."

**Anti-pattern**: استخدام أرقام مدوّرة أو متوقَّعة بدون قياس. لو افترضت
"5000" لأنه القيمة الـ default، صحّحها فور اكتشاف العدد الحقيقي.

**تصحيح ذاتي شجاع**: لو نشرت رقماً ثم اكتشفت أنه خطأ، صحّحه صراحةً في نفس
الرسالة (لا تطمسه). راجع Session_Log §4 corrections pattern.

-----

## 37. Time-Boxed Scouting — السقف الزمني قبل البدء

**Discovered**: Sprint 2.16.17 scouting v1 → v2 → v3. كل re-iteration كشف
شيئاً، الـ user (Claude) أضاف، الـ user (Anas) راجع، إعادة، إعادة. بدون
سقف زمني صريح، scouting يمتد بلا توقّف.

**القاعدة**: كل scouting task يحصل على سقف زمني صريح **قبل** البدء:

- Quick audit: 15-30 دقيقة
- Deep audit: 45-60 دقيقة
- Empirical baseline + light reading: 20-30 دقيقة

عند بلوغ السقف:
1. توقّف عمّا تفعل
2. اكتب ما لديك في الـ output (ولو ناقص)
3. أعطِ user list صريحة: "ما أنجزته" + "ما لم يُغطَّ" + "تقدير زمن لإكماله"

**ممنوع**:
- "أحتاج 10 دقائق إضافية" مرتين متتاليتين
- iteration على نفس الملف بعد بلوغ السقف لإضافة "ملاحظة أخيرة"
- البدء بدون سقف ثم اكتشاف أن العمل اتسع

**القرار في حالة بلوغ السقف وعمل غير مكتمل**:
- ✅ "هنا ما أنجزت في 30 دقيقة. الناقص: A, B, C. لو أردتني أكمل، أعطني
  سقف جديد."
- ❌ "دعني أكمل بسرعة..." → ينتهي بـ 60 دقيقة بدلاً من 30

**Sprint vs Scouting**:
- Scouting = استكشاف، سقف صارم
- Sprint = تنفيذ، يأخذ الوقت اللازم لإنجاز checklist §3 كاملة

-----

## 38. Single-Purpose Sprint Scope — Bundle يحتاج إذناً صريحاً

**Discovered**: Sprint 2.16.15 evaluation, 2026-05-19. الـ audit حدّد 3
bugs (Pydantic A2 + rental_use validation + mega try-block). الميل الطبيعي:
"دعنا نصلحهم كلهم في Sprint واحد". القرار الصحيح: A2 وحده.

**Lesson from 2026-05-18 marathon** (Sprint 2.16.6 → 2.16.12): 7 Sprints
متتالية، كل واحد single-purpose، 46/46 regression تنجح بين كل اثنين. لو
bundled إلى Sprint كبير واحد → fault isolation مستحيل.

**القاعدة**: Default = **Sprint واحد = bug واحد أو ميزة واحدة**.

Bundling يتطلّب:
1. إذن user صريح ("اعمل A و B معاً")
2. تبرير: لماذا لا يمكن فصلهما؟ (تبعية كود، نفس endpoint، نفس test)
3. اعتراف بـ المخاطر: regression لو فشل أحدهما يكسر الآخر

**أنواع bundling مشروعة (بدون إذن)**:
- نفس Bug في عدة ملفات (مثل #6 Sprint 2.16.12: B1 dead import + B3 audience)
- Housekeeping bundle موصوف صراحة (مثل Sprint 2.16.7: A3 + B2 + A4 + A10)
- Sprint cascade pattern (marathon) — لكن كل Sprint cascade ينتهي بـ deploy
  مستقل قبل Sprint التالي

**أنواع bundling ممنوعة**:
- "ما دمنا في api.py، لنصلح هذا أيضاً..."
- "هذا 2 سطر إضافي، يكفي" بدون CHANGELOG واضح
- مزج bug مكتشف حديثاً مع Sprint مخطط له سابقاً

**Signal للتوقف**: لو CHANGELOG_v{N} يحتاج أكثر من section واحد "Why this
matters"، أنت bundling. افصل.

-----

## 39. Deviation Justification Protocol — انحراف بـ 3 جمل صريحة

**Discovered**: Sprint 2.16.17 scouting v2 — التعليمات قالت "شغّل probe
من Heroku". الـ implementation شغّله من sandbox مع تبرير سريع "هذا الـ
threat model الحقيقي". الانحراف ربما مبرَّر، لكن user لم يُمنح كل المعلومات
لتقييمه.

**القاعدة**: لو قرّرت تنفيذ Y بدلاً من X المطلوب، اذكر صراحةً **3 أشياء**:

1. **لماذا Y ضرورياً** (ليس "أسهل" — ضرورياً):
   - مثال جيد: "heroku run python -c يكسر بسبب escaping للـ `=` في URL"
   - مثال سيّئ: "أسرع لو شغّلته من هنا"

2. **ما يُفقد بعدم تنفيذ X**:
   - مثال جيد: "من sandbox = IP غير معروف، Cloudflare قد يعامله
     بـ rate limit مختلف. نتيجة 25/25=200 قد لا تعكس IP عادي."
   - مثال سيّئ: (حذف هذا البند كاملاً)

3. **ما يحتاج user معرفته لتفسير النتائج**:
   - مثال جيد: "للتأكيد، أعد probe من جهازك (IP عادي) قبل الاعتماد على هذا"
   - مثال سيّئ: "النتائج موثوقة"

**ممنوع**:
- انحراف صامت (تنفيذ Y بدون ذكر أنه ليس X)
- تبرير من سطر واحد كـ check-box
- الادعاء أن الانحراف "أفضل" للـ user دون إعطائه فرصة الموافقة

**Pattern مقبول**:
> "التعليمات: شغّل من Heroku. ما فعلت: من sandbox. السبب: cmd escaping.
> المفقود: IP origin verification. اقتراحي: شغّل من جهازك بعد ذلك للتأكيد."

**Pattern مرفوض**:
> "شغّلت من sandbox (لأن heroku run معقّد). النتيجة: 25/25=200."

-----

## 40. Replica + Production Verification — اختبار replica لا يكفي

**Discovered**: Sprint 2.16.15 — `test_sprint_2p16p15_extra_forbid.py`
استخدم `_EvaluateRequest` replica لاختبار سلوك `extra='forbid'`. كان كافياً
نظرياً، لكن الـ post-script verification (exec block على الـ class الإنتاجي
الفعلي من api.py) كشف أن production class يطابق replica فعلاً. لو لم نفعل
الخطوة الثانية، replica قد drift بصمت.

**القاعدة**: عند بناء isolated tests لـ Sprint، استخدم نمط طبقتين:

**الطبقة 1** — Replica tests (سريع، معزول):
- يبني class/function يحاكي production
- يختبر سيناريوهات edge cases
- مكسب: لا يحتاج تحميل dependencies كاملة

**الطبقة 2** — Production verification (مرة واحدة، حاسم):
- يستورد production class/function فعلياً (مع stub للـ heavy deps لو ضروري)
- يجري **سيناريو واحد على الأقل** يطابق الـ replica
- يؤكّد أن النتيجة من production = النتيجة من replica

**القاعدة الذهبية**: لا تنشر Sprint بدون **سطر واحد على الأقل** يستدعي
الكود الإنتاجي ويتحقّق من نتيجته.

**سابقة ناجحة**: Sprint 2.16.15 — replica passes 14/14، ثم exec block
يستدعي ER من api.py الفعلي ويتأكّد `extra_forbidden on ['rental_inome']`.
لو الـ replica drift، الخطوة الثانية كانت ستكشف.

**Anti-pattern**:
- replica يمرّ، production لم يُختبر → drift صامت محتمل
- "production مماثل، لا داعي" → لا داعي حتى يحدث الـ drift

**استثناء**: Sprints docs-only (لا behavior change) → لا حاجة للطبقة 2.

-----

<!-- NOTE: Item #41 (Session-End Git Hygiene) pending — its drill prompt was
     truncated and never supplied in full. Slot it here, between #40 and #42,
     when the complete text arrives. -->

## 42. Deferred-Work Documentation — وثّق التخلّي في الـ docs

**Discovered**: 2026-05-19 — قرار التخلّي عن Mthamen integration. النموذج
الذهبي: Project_Instructions §20.8 (4 أسباب + 3 شروط إحياء). بدون توثيق
صريح، جلسة Claude Code لاحقة قد تكتشف Mthamen في Operational_Rules أو
session log وتعيد محاولة الـ integration.

**القاعدة**: أي قرار بـ **تأجيل / تخلّي / استبعاد** عمل يحصل على entry
في الـ docs المناسب (ليس في chat فقط)، بـ 4 أقسام:

1. **ما جُرّب**: السكربتات/الاختبارات/الـ approaches الفعلية
2. **لماذا فشل/أُجِّل**: السبب التقني + الـ evidence
3. **شروط الإحياء**: ما الذي يجب أن يتغيّر لإعادة المحاولة (عددها صريح،
   عادة 3)
4. **توجيه قاطع لجلسات لاحقة**: "بدون الـ 3 شروط، أي اقتراح إحياء **يُرفض**"

**المكان المناسب**:
- قرار يتعلّق بـ endpoint/integration → Project_Instructions §XX
- قرار يتعلّق بـ Sprint مؤجَّل → Project_Instructions §11 deferred Sprints
- قرار منهجي عام → Operational_Rules.md
- قرار empirical → EMPIRICAL_FINDINGS.md Rule

**سابقة ذهبية**: Project_Instructions §20.8 (Mthamen):
- جُرّب: smoke_mthamen.py + smoke_mthamen_v2.py (6 profiles)
- فشل: 6/6 WAF rejected + iPhone quota 1/يوم
- شروط: WAF mitigated + quota >10/يوم + (مفضّل) MoJ approval
- توجيه: "أي اقتراح بإحياء يجب أن يُرفض"

**ممنوع**:
- تأجيل عمل دون توثيق في docs → "ذاكرة شفهية" تضيع بين الجلسات
- توثيق ناقص بدون شروط الإحياء → الجلسة القادمة تجرّب من الصفر
- "مؤجَّل مؤقتاً" دون موعد أو شرط — هذا في الواقع abandoned

**Recall mechanism**: أضف recall phrase في الـ doc المعني:
- "تذكر قرار 19 مايو" → §20.8
- "تذكر Bug A11" → SECURITY_AUDIT
- "تذكر #34" → Operational_Rules #34

## 43. ⚠️ Heroku deploy = `git subtree push` (app lives in `deploy v2/` subdir)

**Discovered**: 2026-05-20, Sprint 2.19 §8 git diagnosis. A `git push heroku
master` "من جذر deploy v2/" was rejected. Root cause found by measurement, not
guessing.

**The structure** (verified 2026-05-20):
- `git rev-parse --show-toplevel` → **`C:/Thammen`** (NOT `deploy v2`).
- All Heroku-critical files (`Procfile`, `requirements.txt`, `runtime.txt`,
  `api.py`, every engine module) are tracked under the **`deploy v2/`** prefix.
- **Zero** tracked files at the repo root (`git ls-files | grep -vE "/"` empty).
- Heroku buildpack = `heroku/python` **only**. No monorepo/subdir buildpack,
  no `PROJECT_PATH`/`SUBDIR`/`MONOREPO` config var (verified via
  `heroku buildpacks --app thammen-app-123` + `heroku config`).
- `Procfile` = `web: uvicorn api:app ...` → expects `api.py` at the **slug root**.

**Why plain push fails**: `git push heroku master` ships the whole `C:\Thammen`
tree. The python buildpack looks for `requirements.txt` at the slug root, finds
none (it's under `deploy v2/`), and **rejects the build**. This is exactly the
2026-05-20 failure.

**The mechanism that works** (the only one consistent with this structure — this
is how Sprint 2.16.15 shipped):

```
git subtree push --prefix "deploy v2" heroku master
```

**Divergence handling (added Sprint 2.19.1, 2026-05-20).** After repeated
`git subtree push`, the synthetic split commits diverge from Heroku's ref and a
plain `git subtree push` is *rejected* ("Updates were rejected"). This is a
consequence of the subtree mechanism, not a separate topic — so it lives here in
#43, not in a new rule (decision logged in CHANGELOG_v38 §"Decisions made"; the
brief had called it "#44"). The recommended, self-cleaning procedure uses a
named temporary branch + a force push (safe because Heroku is a *deployment
target*, not a historical repo — confirm with Anas first per #32):
```
git subtree split --prefix "deploy v2" -b heroku-deploy-tmp
git push heroku heroku-deploy-tmp:master --force
git branch -D heroku-deploy-tmp
```
The older one-liner form is equivalent but leaves no temp branch to inspect:
```
git push heroku `git subtree split --prefix "deploy v2" master`:refs/heads/master --force
```

**Key distinctions**:
- **Commits** are normal full-tree commits at repo root (they carry the
  `deploy v2/` prefix). Nothing special about committing.
- Only the **push-to-Heroku** step needs the `--prefix`. GitHub backup
  (`git push origin master`) uses the normal full push.
- `deploy v2/deploy.sh` is **STALE** — an old DigitalOcean VPS guide
  (systemd + nginx + certbot). It is NOT the Heroku mechanism. Do not follow it.
- Push discipline #32 still fully applies: branch=master + §3 6-item checklist +
  Sprint integrity + explicit consent BEFORE any push.

**Read-only verification trio**:
```
git rev-parse --show-toplevel                # → C:/Thammen
git ls-files | grep Procfile                 # → deploy v2/Procfile
heroku buildpacks --app thammen-app-123      # → heroku/python only
```

-----

## 45. ⚠️ Verify data-linking schema BEFORE proposing batch processing

**Discovered**: 2026-05-20, Sprint 2.20 audit. A "MoJ self-calibration" plan
(tag every MoJ sale as corner/non-corner via `detect_corner`, then derive a T1-T1
corner premium) was proposed and discussed for ~1h before measurement killed it.

**The rule**: before proposing any **batch join / batch tagging / cross-dataset
enrichment**, *measure* the linking key on the **actual data** — never assume it
from a field name or a prose description. "Can dataset A join to B?" and "does
field X carry a usable key?" are empirical questions.

**The lesson (concrete)**: MoJ `رقم العقار المرجعي` was assumed to be a GIS PIN.
Measured: it is an opaque `PN…` hash — **0/26,719 numeric**, no PIN, no
coordinates, no street. So MoJ sales **cannot** be geo-located to parcels →
`detect_corner` cannot tag them → the entire plan (and Empirical_Findings E12 for
corner) is **BLOCKED** until a PIN-keyed sale source exists.

**Pairs with**: #33 (empirical-first audits — measure before reading) and the §5
pre-Sprint discipline. The cost of skipping this is building on an impossible
premise. (Note: there is no Rule #44 — the subtree-push divergence procedure was
folded into #43 to avoid sprawl; see CHANGELOG_v38 §"Decisions made".)

-----

## 46. ⚠️ Pre-Sprint frontend input-flow audit must validate classifier output for the NEW path

**Discovered**: 2026-05-20→22, Sprint 2.21.0. The Land Grid (2.20) was deployed
(v79) but **unreachable** by users, and the classifier would have mislabelled the
new input.

Two distinct checks are required before scoping any Sprint that adds a new input
path or activates a deployed-but-unreachable feature:

- **(a) Backend feature exists ≠ user can reach it** (Anas's discovery): the UI
  only accepted Z/S/B (QARS, post-construction → villas/buildings); bare lands
  have a Cadastre PIN but no QARS address, so the Land Grid never fired.
- **(b) Classifier exists ≠ classifier returns the correct asset_type for the new
  input mode** (audit discovery): `classify_asset` had **no branch returning
  land** — a bare land PIN was classified `standalone_villa` (high confidence!),
  confirmed live: **0/5 known land PINs triggered the grid** before the fix.

**The rule**: when adding an input path, audit the *full* chain end-to-end —
input field → API → engine → **classifier output asset_type** → feature trigger —
on real data, before scoping. Pairs with #33 (measure first), #45 (verify
data-linking before batch), and §5.

**Fix pattern used**: `input_mode='land'` hint (set when the user enters via the
land/PIN tab) threaded api → evaluate_thammen → evaluate_property →
full_property_lookup → classify_asset, where a new branch returns RAW_LAND for
typical sizes with geometric guards (≥50K compound_large, ≥15K compound_small).
Additive (`input_mode=None` = legacy behaviour unchanged). Note: the engine value
is **`raw_land`** (the only AssetType with full downstream MoJ-category support;
`'land'` has no `ASSET_TYPE_TO_MOJ_CATEGORY` key and would break valuation —
the grid trigger accepts both, so `raw_land` satisfies the goal).

**Expansion (Sprint 2.21.0.5):** the audit must also cover the **template/output
layer** for the new mode, not just the classifier. «backend produces raw_land» ≠
«output template handles raw_land». Post-deploy visual verification of a bare-land
report found 5 template contradictions (scope said "نوع غير معروف", address
"None/None/None", a negative "building value", building-assumption uncertainty
factors, and tenant/tower due-diligence questions) — none of which the backend or
unit tests surfaced. **Rule:** for any new asset_type/input mode, do a post-deploy
E2E *visual* read of the user-facing output, section by section, before declaring
the Sprint user-facing-complete.

**Expansion #2 (Sprint 2.21.0.7 / 2.21.0.7.1):** the end-to-end audit must also
(a) **validate the classifier's output asset_type against authoritative GIS/data
signals for the new path**, not just trust the input hint (→ Rule #49 — PIN "land"
hint was wrong for 2/5 fixtures: built + governmental), and (b) re-run the
**post-deploy visual read after every behaviour change**, because it keeps
catching what unit tests miss. 2.21.0.7's offline tests were green, yet the live
smoke + Anas's visual pass surfaced: a UX dead-end (built non-residential → "use
address tab" when the address tab also rejects → changed to reject in 2.21.0.7.1),
a stale display field ("نوع العقار: غير محدد" despite a known type → discovered
label), and a pre-existing downstream crash (`_expand_extent` int/str sort, only
hit because a no-LANDUSE PIN classified as a compound). None were visible offline.

-----

## 47. ⚠️ New asset_type → ALIAS in every lookup dict, never rename (outside a refactor Sprint)

**Discovered**: Sprint 2.21.0.5. The classifier emits `raw_land`, but several
module-level lookup dicts were keyed on `'land'` (`scope_of_service._ASSET_SCOPE`),
while others had `raw_land` (`ASSET_TYPE_TO_MOJ_CATEGORY`). The mismatch silently
mislabelled bare-land reports ("نوع غير معروف / خارج النطاق").

**The rule**: when a new asset_type value enters circulation, add an **alias** in
every module's lookup dict (`_DICT['raw_land'] = _DICT['land']`) rather than
renaming existing keys. Renaming/normalising the literal across the codebase is a
*dedicated refactor Sprint*, not a polish change — it touches memory, docs, tests,
and every consumer at once. Aliasing is surgical and regression-safe.

**Audit aid**: `grep -rn "asset_type" --include=*.py` to find every lookup dict /
membership test, then confirm each handles the new value (alias or `.lower()`
membership). Pairs with #45/#46.

-----

## 48. ⚠️ GIS GET requests must fall back to POST when the URL > 2000 chars

**Discovered**: 2026-05-22, Sprint 2.21.0.7 audit (Anas flagged it as the "#50
candidate"; numbered sequentially as #48 to avoid empty 48/49 gaps).

A many-vertex ESRI geometry sent as a GET query string overflows the URL length
limit → **HTTP 414 Request-URI Too Long**. Hit on a Pearl master plot when
`_project_4326_to_2932` passed the full polygon ring to the Geometry server; the
future QARS-in-polygon (P1) query has the same shape.

**The rule**: `qatar_gis._http_get_json` now builds the GET URL, and **only when
`len(url) > 2000`** sends the params as a form-encoded **POST** instead (ESRI
`/query` and the Geometry server accept POST for the same params). Small queries
stay GET → **zero behaviour change**; large geometries stop silently failing.
This is a defensive fix that also stabilises production (Pearl/Lusail master
plots previously errored). Pairs with §21.6 (probe before integrate) — the probe
`_get` was switched to POST first (audit-only), then this production guard added
with Anas's explicit approval.

**Update 2026-05-22 (Sprint 2.21.0.7):** this fallback was *exercised in
production* by the new QARS-in-polygon query (P1) — many-vertex parcel rings
(Pearl/Lusail) routinely exceed 2000 chars and now POST automatically. Confirmed
working in the 15-PIN Heroku smoke. (So Anas's "#50 POST-fallback candidate" =
this rule #48; no separate #50 created — avoids a numbering gap.)

-----

## 49. ⚠️ An identifier is NOT an asset_type — verify the real type via authoritative GIS/data lookups

**Discovered**: 2026-05-20→22, Sprint 2.21.0 → 2.21.0.7. The PIN/land tab told the
engine "this is land", and `probe_land_pins.py` "confirmed" 5/5 PINs as land — but
it only **echoed the user's hint**, never querying ground truth. The live Asset
Type Reality Check then proved **2 of those 5 were wrong**: `90040668` has a
building on it (QARS-in-polygon=1 → BUILT), `52060090` is governmental (RULEID=12).

**The rule**: a user-supplied identifier (PIN, address, tab choice) is an *input
hint*, **not** the asset's true type. Before trusting it for a valuation path,
cross-check against authoritative GIS/data signals:
- **QARS-in-polygon** — is there a surveyed building inside the parcel? (built ≠ bare)
- **General_Landuse RULEID** — official land-use class (residential vs commercial/
  governmental/special/mixed). Pull the code→label map from the layer's
  **coded-value domain**, never guess (see Empirical_Findings **E13**).
- Precedence: building-present > land-use class > geometry. *Surface* the
  contradiction (stop/reject screens), never silently value the wrong type.

This is the PIN-path sibling of Rule E7 (QARS subtype needs a Zoning cross-check)
and Bug A11. Pairs with #33 (measure first), #45 (verify data-linking before
batch), #46 (audit the new path end-to-end), and **E14** (validation scripts must
exercise production logic, not echo the input).

-----

## 50. ⚠️ Staged-Sprint Discipline — every Sprint reviewed through the Stage 1/2/3 lens

**Discovered**: 2026-05-23, Sprint 2.21.0.9. The original Sprint brief proposed
a GPS-centroid threshold (`<15m → attached`) plus a "value whole structure"
toggle, plus classification UI variants for attached/separate/ambiguous. After
two rounds of deploys (v93 with 18m, v96 with 15m), Anas overturned the design
entirely: 56/565/21 + 19 are physically separate villas with full setbacks
despite the 15.2m centroid — GPS centroid distance alone CANNOT discriminate
attached from separate at the 10-20m range (E15). The right signal is wall-to-
wall via Building Footprint geometry (E18), which we don't have yet. The
re-framing: ship **Stage 1** (detect + split + manual override, ~70%
confidence) without classification; **pre-specify Stage 2** (the wall-to-wall
rule) for a future Sprint conditional on the footprint probe.

**The rule**: every Sprint proposal must answer:

1. **Which stage does this contribute to?** (Stage 1 = minimum data, ≤5s, ~70%;
   Stage 2 = richer data, ~90%; Stage 3 = on-site overrides, ~95%+. See E16.)
2. **Can Stage 1 ship independently** (without Stage 2/3 data)? If not,
   re-scope or split.
3. **If a more-precise stage is deferred, is its logic pre-specified** in
   EMPIRICAL_FINDINGS or the CHANGELOG addendum so the next session doesn't
   re-debate the design? (Sprint 2.21.0.9's E18 is the model: deferred Stage 2
   logic pinned to Qatar building code, no re-debate needed.)

**Anti-pattern from Sprint 2.21.0.9** (don't repeat):
- Building a classifier + UI for an A/B distinction whose signal is unreliable.
- Trusting a data-derived threshold (audit clustering at 15.2m → "raise to 18m")
  when domain knowledge says the threshold can't work at all (E15).
- Shipping Stage 1+2 hybrid where Stage 1 is correct but Stage 2 is wrong;
  splitting into pure-Stage-1 was the fix.

**Pairs with**: **E16** (staged-valuation pattern), **E17** (1-field minimum
input), **E18** (Stage 2 wall-to-wall rule), **#42** (deferred-work
documentation — pre-specify the deferred logic, not just the deferral).

**Recall**: "تذكر #50" / "Staged Sprint discipline" / "تذكر Stage 1".

-----

## 51. ⚠️ Audit-driven Sprint pattern — the canonical performance-Sprint loop

**Discovered**: 2026-05-23 evening, Sprint 2.18.0. Empirically validated:
the CHANGELOG_v44 §5 pre-deploy table predicted per-case post-deploy timings
to **within ±2% on every measured path** (predicted −4 000 ms / measured −4 003 ms
on multi_qars_56; predicted −4 000 ms / measured −3 887 ms on khor_land; all
fast-paths predicted 0 / measured ±60 ms = sub-noise).

**The rule**: any Sprint whose primary goal is performance (latency, throughput,
resource use) MUST follow this 3-stage loop:

1. **Pre-Sprint §5 audit (mandatory before any code).** Write a standalone
   profiling probe (Rule #34, file-based), deploy to Heroku, run against a
   *diverse* cohort (Rule §5 — at least one of: known regression case, fast
   path, slow path, edge case). Output: per-phase timings + per-call counts +
   a written audit report with a decision-gate section.
2. **Audit-derived patch (single-purpose per Rule #38).** Patch only what the
   audit identified as the dominant bottleneck. CHANGELOG.md MUST include a
   "Success criteria" section with **predicted post-deploy timings**, per case,
   so post-deploy measurement is a falsifiable test of the hypothesis.
3. **Post-deploy audit comparison.** Re-run the same probe on the same cohort
   from the same Heroku slug type (one-off dyno, same GIS network). Compare
   actual vs predicted per case. Report deviation. If actual ≥ 2× predicted
   delta in either direction → STOP and investigate (the bottleneck model was
   wrong, or the patch has a side effect).

**Why this works**: it converts performance work from craft to engineering.
The pre-deploy table forces you to commit to a falsifiable claim. The
post-deploy comparison gives a measurement-backed pass/fail.

**Why this beats benchmarks alone**: a benchmark answers "how fast?", an
audit answers "*why* this fast and what's *next* to fix". Sprint 2.18.0
shipped knowing exactly which 4 seconds it would kill; Sprint 2.18.1 ships
knowing exactly which ~85 seconds it should kill (and which it should NOT —
the lite-baseline 4.1 s is Sprint 2.18.2 territory).

**Anti-patterns this rule prevents**:
- "I'll just parallelize this loop, looks slow" → measure first; the loop
  may not be the bottleneck.
- "Performance is unpredictable, ship and see" → no. The audit gives a
  prediction. If the prediction was wrong, the model is wrong, and the
  next Sprint needs a different audit.
- Bundling multiple performance fixes into one Sprint → splits the
  measurement signal. Rule #38 + #51 together force single-purpose
  performance Sprints with traceable wins.

**When this rule does NOT apply**: feature Sprints (Land Arc, multi-QARS,
asset-type reality check), correctness fixes (Bug A11, Bug A2), and
methodology changes. For those, the §5 audit is qualitative (find affected
landmarks/PINs/edge cases) and the success criterion is "behaviour
matches spec", not "latency Δ matches prediction".

**Recall**: "تذكر #51" / "تذكر audit-driven Sprint" / "تذكر prediction-vs-measurement".

-----

## 52. ⚠️ Latency Sprints unmask methodology bugs — post-deploy verification must include the now-reachable response content

**Discovered**: 2026-05-24 morning, Sprint 2.18.1.1. Sprint 2.18.1 (latency)
shipped successfully — 51/835/17 went from HTTP 503×3 in 30s router timeout
to HTTP 200×3 in 28.9s. Latency goal met, success criteria met, regression
clean. But Anas's visual verification step on thammen.qa (CLAUDE.md §3 last
item: "smoke test 3 diverse addresses post-deploy") caught what the 503
timeout had been hiding: the *content* of the now-reachable response
contained silent arithmetic failure (land=218M vs total=6.8M, building=
−211M, pct=−3,107%). The bug pre-existed Sprint 2.18.1 but was masked by
the router timeout for weeks — invisible until the latency fix made the
response path reachable.

**The rule**: when a Sprint converts 5xx → 2xx on a path that was previously
timeout-blocked (or routinely-failing), the response *content* on that path
becomes verifiable for the first time. Post-deploy verification scope must
explicitly include:

1. **Latency / HTTP status** (the stated Sprint goal — measure this).
2. **Methodology of the response content** (the newly-reachable response
   may itself have latent bugs that were timeout-masked — *measure this too*).
3. **Anas's visual verification on thammen.qa** is the canonical step. It
   catches what unit tests + isolated audits + offline regression can't:
   the user-visible report rendered end-to-end with real GIS data + real
   MoJ comparables + real brief composition.

**The mechanism**: a request that times out at HTTP 503 returns the
WAF/router error page, not application data. So no application-level
assertion can fire against its content. The instant the latency fix makes
the path complete in under 30s, the engine renders whatever it would have
been rendering all along — which may itself be wrong. Sprint 2.18.1.1 is
the first documented case of this pattern in the project's history; it
will not be the last.

**Pairs with**:
- **Rule #51** (audit-driven Sprint pattern) — extends step 3 (post-deploy
  comparison) to explicitly cover content verification, not just timings.
- **Rule §5** (UI-First Audit) — the 6th item ("Smoke test 3 diverse
  addresses from Heroku post-deploy") is what catches this. #52 names the
  pattern so future Sprints can reference it explicitly.

**Anti-pattern this rule prevents**:
- "Sprint X shipped successfully — latency reduced from N to M, all tests
  pass, deploy is done" without checking what the response now *contains*.
- Treating "HTTP 200" as equivalent to "correct response". 200 only means
  the engine returned a JSON document; the document's *content* may still
  be broken.

**Recall**: "تذكر #52" / "تذكر latency unmasks methodology" /
"تذكر 2.18.1 → 2.18.1.1".

-----

## 53. ⚠️ Closed cases stay closed — including as comparison anchors

Rules derived from a deferred/closed case remain in force. The originating
case itself does not get cited as a foil, precedent, or comparison when
documenting new work. Findings stand on their own terms. Cite §X (the rule),
not the case that produced §X.

**Pairs with** Project Instructions §22 ("treating closed case as Sprint
candidate → STOP"). This rule extends that discipline from "don't propose
reviving" to "don't drag back as a comparison anchor."

**Self-check**: if a sentence in new documentation contains
"unlike [closed case]" or "mirror [closed case] pattern" or similar —
delete it. The finding doesn't need the contrast to be understood.

**Discovered**: 2026-05-24, MME smoke session (pre-Sprint 2.21.1). The MME
diagnosis was technically accurate but kept getting framed against the
2026-05-19 closed Qatar government endpoint case across four+ sites:
script docstring, two ledger interpretations, and a multi-choice question
option. Each reference reopened a settled decision unnecessarily.

**Recall**: "تذكر #53" / "تذكر closed cases stay closed".

-----

*End of Operational Rules. 30 items migrated from session memory on
2026-05-19. Item #31 added 2026-05-19 evening after Sprint 2.16.15
deployment (first Sprint shipped from Claude Code). Item #32 added
2026-05-19 evening during Sprint 2.16.17 scouting session (push & commit
discipline crystallized after worktree-vs-master confusion). Item #33
added 2026-05-19 same session (empirical-first audits — measure before
read, crystallized after slowapi import-vs-active confusion). Item #34
added 2026-05-19 same session (file-based scripts for external endpoints —
crystallized after inline `heroku run python -c` broke on Windows cmd
escaping). Item #35 added 2026-05-19 same session (library version
verification — verify installed version on Heroku, not just requirements.txt,
crystallized after Pydantic 2.x + slowapi syntax checks). Item #36 added
2026-05-19 same session (observed-vs-expected reporting — cite actual
sample/window, crystallized after the "5000 lines" vs actual 1500-line
Heroku log cap correction). Item #37 added 2026-05-19 same session
(time-boxed scouting — set an explicit cap before starting, crystallized
after the Sprint 2.16.17 v1→v2→v3 re-iteration creep). Item #38 added
2026-05-19 same session (single-purpose Sprint scope — bundling needs
explicit consent, crystallized from the 2026-05-18 marathon
2.16.6→2.16.12 single-purpose cascade). Item #39 added 2026-05-19 same
session (deviation justification protocol — state why/what-is-lost/what-user-
needs in 3 explicit sentences, crystallized after the Sprint 2.16.17 v2
sandbox-vs-Heroku silent deviation). Item #40 added 2026-05-19 same session
(replica + production verification — at least one line must exercise the
real production class, crystallized after the Sprint 2.16.15 extra='forbid'
two-layer test pattern). Item #41 (Session-End Git Hygiene) PENDING — drill
prompt truncated, placeholder left between #40 and #42. Item #42 added
2026-05-19 same session (deferred-work documentation — record abandonment
in docs with revival conditions, modeled on Project_Instructions §20.8
Mthamen defer). Item #43 added 2026-05-20 during Sprint 2.19 §8 git diagnosis
(Heroku deploy = `git subtree push --prefix "deploy v2"` because the repo root
is `C:\Thammen` and the app lives in the `deploy v2/` subdir; plain
`git push heroku master` is rejected by the python buildpack — no
requirements.txt at slug root). Item #50 added 2026-05-23 during Sprint 2.21.0.9
(staged-Sprint discipline — every Sprint reviewed through Stage 1/2/3 lens,
crystallized after the 18m-threshold reversal). Item #51 added 2026-05-23
evening during Sprint 2.18.0 closeout (audit-driven performance-Sprint pattern —
crystallized after the §5 audit / pre-deploy prediction table / post-deploy
measurement loop landed within ±2% across all 7 measured paths; the first
measurement-validated performance Sprint in the project's history). Item #52
added 2026-05-24 morning during Sprint 2.18.1.1 closeout (latency Sprints
unmask methodology bugs — crystallized after Sprint 2.18.1 successfully cut
89s→29s on 51/835/17, converting HTTP 503×3 to 200×3, only for Anas's visual
verification on thammen.qa to catch that the now-reachable response
contained silent arithmetic failure: land=218M, total=6.8M, building=−211M,
pct=−3,107%; the first documented "latency unmasks methodology bug" case in
project history). Item #53 added 2026-05-24 during pre-Sprint 2.21.1 MME
smoke session (closed cases stay closed — including as comparison anchors;
crystallized after the MME diagnosis kept getting framed against a closed
endpoint case in four+ documentation sites, each technically accurate but
each reopening a settled decision unnecessarily). When new operational
invariants emerge in future Claude Code sessions, append them here.*
