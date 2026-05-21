# Thammen (thammen.qa) — Project Instructions

> **Scope:** هذا المشروع مخصص حصرياً لتطوير وصيانة موقع تقييم العقارات القطري `thammen.qa`. أي مهمة خارج هذا النطاق (تقارير عقارية مستقلة، أبحاث سوق، تقييم عقار معين بدون لمس المنصة) **لا** تنتمي لهذا المشروع.

> **آخر تحديث:** 2026-05-19 evening (الإصدار 6) — بعد Sprint 2.16.15 (Bug A2 fix). يدمج التطورات منذ Sprint 2.9 شاملاً ماراثون 2026-05-17/18 + كشف منهجية المثمن + قرار التخلّي 2026-05-19 + Bug A11 deployment + Pydantic extra='forbid' boundary tightening.

-----

## 1. Product Identity

**Thammen** هو نموذج تقييم آلي (AVM) للسوق العقاري القطري، يعمل وفق RICS VPS 4 مع تكييفات للظروف القطرية. مصادر البيانات:

- **وزارة العدل القطرية** (data.gov.qa) — الصفقات المسجلة (**الحقيقة**)
- **MME / qrep** — صفقات الشقق والإيجارات
- **GIS قطر** — الحدود الإدارية، التصنيف، المعالم
  - **`khazna.gisqatar.org.qa/fed/rest/services/QARS/QARS_Point`** (الـ primary منذ Sprint 2.16.5)
  - **`services.gisqatar.org.qa/server/rest/services/Vector/`** للطبقات الأخرى
- **إعلانات السوق** (FGRealty, PropertyFinder, arady, Mzad) — **التطلعات**
- ~~**المثمن (sak.gov.qa)**~~ — **deferred 2026-05-19** (WAF block + 1/day quota). المنهجية تبقى reference في القسم 20

`thammen.qa` **ليس** سوقاً للإعلانات و**ليس** بديلاً عن مُقيِّم معتمد. هو أداة دعم قرار تستخدم **منهجيتي RICS متباعدتين** (Market + Income) — المنهج الثالث (Cost) **مرجعي فقط**.

-----

## 2. Collaboration Style (memorize verbatim)

### The user

- **أنس** — مواطن قطري، يعمل على Windows، ينشر على Heroku
- مجلد العمل: `C:\Thammen\deploy v2`
- يفضل العربية في المحادثة، الإنجليزية في الكود حين تكون أوضح
- لا يريد التدخل اليدوي في جلب البيانات: "لا أريد أن أتدخل"
- يقدّر تحليل الـ tradeoff الصادق فوق الاستنتاجات المطمئنة

### Delivery format — fixed rules

1. **ملف zip واحد** لكل Sprint، يُسلَّم عبر `present_files` إلى `/mnt/user-data/outputs/`
2. **prompt command** = code block منفصل، **أمر واحد لكل سطر** (لا `&&` على نفس السطر)
3. **Shell flavor:** Windows `cmd` (وليس bash):
   - `cd /d "C:\Thammen\deploy v2"`
   - `copy /Y file file.bakN` (وليس `cp`)
   - `tar -xf "%USERPROFILE%\Downloads\<sprint>.zip"`
   - `findstr /C:"Sprint X.Y.Z" file.py` (وليس `grep`)
   - `git push heroku master`
4. **CHANGELOG_vN.md** مع كل Sprint، يتبع نمط `CHANGELOG_v33.md`, `v34.md`
5. **أرقام الـ Sprints متسلسلة** ولا تتكرر أبداً. آخر إصدار → انظر `CHANGELOG_v34.md` (Sprint 2.16.12).

### RTL conventions

- كل نص عربي في docx يستخدم `<div dir="rtl">`, RTL paragraphs, `visuallyRightToLeft:true` على الجداول
- النص المختلط عربي+لاتيني يُلفّ بـ `\u200E...\u200E` لمنع انعكاس الـ bidi

-----

## 3. Mandatory Methodology Principles

### Core distinction (RICS triangulation — Two-Method Active, Cost Reference)

|Source|Role|Method|Active in production?|
|---|---|---|---|
|Ministry of Justice|**الحقيقة السوقية** (صفقات بيع مسجلة)|Market Comparison|✅ Primary|
|DCF / Yield models|**Income Approach**|للأبراج/الكومباوندات/الشقق|✅ Primary للأصول المُؤجَّرة|
|~~المثمن (sak.gov.qa)~~|**Cost Approach (DRC)**|تكلفة الإحلال - الإهلاك|❌ Reference only (deferred 2026-05-19)|
|arady, PropertyFinder, Mzad|**التطلعات** (أسعار بائعين)|sentiment|⚠️ Display only, never input|

**RICS standard**: تقييم محترف يستخدم على الأقل **طريقتين**. Thammen يستخدم Market + Income في production. منهجية Cost (DRC) موجودة كـ **reference موثّق** في القسم 20، لكن **لا** تُستدعى live (انظر القسم 20.8).

### Math discipline

- **الوسيط، لا المتوسط** — المتوسط يتشوّه بالقصور والاستثناءات
- **انضباط حجم العينة:**
  - n ≥ 20 → موثوق
  - 10–19 → إرشادي
  - 5–9 → سياق فقط
  - < 5 → "بيانات غير كافية"
- **نافذة 24 شهر** افتراضياً، fallback لـ 36 شهر عند n < 20
- **شرائح الحجم:** 0–400 / 400–600 / 600–900 / 900–1500 / 1500+ م²

### Net yield benchmarks (Qatar)

- 5–6% = طبيعي · >6% صافي = لقطة · <4% صافي = ضعيف
- **لا تقدّم gross بدون net**

### Cap rates للكومباوندات (Class B residential)

- 7.0% مشتري استراتيجي / 7.5% قيمة عادلة / 8.0% سوق محافظ / 8.5% بيع تحت ضغط

### The Qatar 10-Year Rule

- فلل > 10 سنوات وليست فاخرة → سعر السوق ≈ قيمة الأرض + 0–10%
- المشتري ينوي الهدم؛ المبنى عبء لا قيمة مضافة
- في `evaluate_unified.py`: `age_regime='qatar_10_year_rule'`

### Stock stratification within MoJ (Rule E4)

- وسيط فيلا MoJ في شريحة واحدة هو **مزيج** (جديد + متهالك + قديم)
- 4 تصنيفات: `land_priced` (<1.15) · `aging_stock` (1.15-1.50) · `modern_stock` (1.50-2.20) · `luxury_new` (≥2.20)
- منذ Sprint 2.16.0 الـ AVM يُنتج 4 strata cards كشفافية

### Empirically validated benchmarks (2026-05 audit)

- علاوة الإعلان للـ stock النظيف = 8–20% (يطابق العالمي)
- علاوة الإعلان للفيلات المختلطة = 50–160% (stock mismatch، ليس under-registration)
- MoJ **ليس** ناقص التسجيل بنظام — ارفض أي uplift logic

### Hard ceilings

- **المشترون:** لا تدفع فوق MoJ median + 10%
- **البائعون:** لا تُصرّ فوق MoJ median + 30%
- **اذكر دائماً n** خلف كل وسيط

-----

## 4. Thammen Architecture & Key Files

```
api.py                  ── FastAPI backend (Sprint 2.16.12: B3 audience whitelist)
evaluate_unified.py     ── Main engine
                         Sprint 2.16.10: unit_count + per_unit_rent
                         Sprint 2.16.11: tower carve-out في _check_input_sanity
                         Sprint 2.16.12: B3 _AUDIENCE_ACCEPTED frozenset
evaluate_v3.py          ── Sprint 2.16.12: B1 dead sales_merge import removed
data_freshness.py       ── Sprint 2.7
moj_db.py               ── SQLite + queries
moj_reference.py        ── MoJ reference by size bracket
property_factors.py     ── GIS factors (Sprint 2.16.7: A10 typo fix)
qatar_gis.py            ── Classifier
                         Sprint 2.16.5: KHAZNA_BASE
                         Sprint 2.16.6: Branch 0 subtype-aware
stock_strata.py         ── Sprint 2.16.0
material_uncertainty.py ── Sprint 2.16.8: Tower MUC backend
output_briefs.py        ── Sprint 2.16.9: MUC frontend display
index.html              ── Frontend (RTL, Tajawal)
                         Sprint 2.16.10: unit_count + per_unit_rent inputs
moj_weekly.csv          ── ~25,673 MoJ transactions
building_age_cache.sqlite ── Sprint 2.15.1: 62 PINs imagery cache
mthamen_reference.py    ── ⏸️ ARCHIVE ONLY (2026-05-19 decision)
                         Never deployed. NO production dependency on sak.gov.qa
```

### Endpoint structure (api.py)

- `POST /api/evaluate` — تقييم سريع (عنوان فقط)
- `POST /api/evaluate/details` — مع تفاصيل المبنى
- `GET /api/health` — status + freshness + qars_endpoint
- `GET /api/freshness` — banner data
- `GET /api/disclaimer` — تحذير المسؤولية
- `GET /api/about` — معلومات المنتج

### Theme variables in index.html

`--bronze: #A68252` · `--primary: #12344D` · `--ok/--ok-bg` · `--warn/--warn-bg` · `--bad/--bad-bg` · `--alt: #F3F0EB` · `--muted: #6B7280` · `--light: #9CA3AF`

CSS جديد يستخدم هذه المتغيرات حصرياً.

-----

## 5. Mandatory Pattern Before Any New Sprint (UI-First Audit)

> **هذا أهم قسم في الوثيقة.**

### Mandatory methodology (60 دقيقة قبل أي patch)

1. **اختر 3–5 عقارات متنوعة** (varied zone، age، asset type، include **tower or apartment_building**)
2. **استخرج ground truth مباشرة من Qatar GIS** (انظر القسم ١٢)
3. **اتصل بـ thammen.qa واستخرج الحقول الفعلية**
4. **قارن الحقول حقلاً بحقل** بما فيها **BUILDING_NO_SUBTYPE**
5. **افتح `index.html` وافحص العرض الفعلي** قبل ادعاء أي شيء
6. **افتح على mobile viewport (390×844)** — Sprint 2.16.4 lesson
7. **قِس نطاق الـ bug** عبر GIS counts
8. **بعد كل ما سبق فقط**، اقترح Sprint

### 🆕 External endpoint integrations — Heroku smoke test FIRST

**Lesson from 2026-05-18/19**: قبل بناء أي Sprint يعتمد على endpoint حكومي قطري:

```
heroku run python smoke_<endpoint>.py
```

اختبر **reachability + content type + WAF response** قبل ساعة واحدة من البناء.
الحكومة القطرية تستخدم F5 BIG-IP ASM WAF بـ geo-restriction على عدة endpoints. Heroku على US/EU = يُحجب.

سوابق:
- `sak.gov.qa` (المثمن) — WAF rejected كل الطلبات (2026-05-19، 6 profiles).
- `geoportal.gisqatar.org.qa` — timeout من Claude container (لكن Heroku يصل).
- `khazna.gisqatar.org.qa` — يعمل من Heroku، لكن خارج Claude container.

### Production timing baseline requires diversity

- اختبر 5+ عناوين متنوعة، **لا** واحدا
- baseline نموذجي: ~2.5s. استثناءات: 24-30s
- ⚠️ **لا تستخدم 51/835/17 كـ regression test** — A6 timeout. استخدم 52/903/90 بدلاً عنه.

### Pre-deploy mandatory 6-item checklist

١. `py_compile` على كل ملف Python معدّل
٢. `node --check` على JS من index.html (Sprint 2.16.1 lesson)
٣. Mobile viewport test 390×844 (Sprint 2.16.4 lesson)
٤. Regression tests: 46/46 تنجح
٥. Isolated logic tests للكود الجديد (5+ مع fallback)
٦. Smoke test على 3 عناوين متنوعة من Heroku بعد deploy (Sprint 2.16.10 lesson)

### Absolute prohibitions

- 🚫 لا تدّعِ "Critical Bug" بدون دليل مرئي
- 🚫 لا تعيد تدوير audits قديمة بدون إعادة تحقق
- 🚫 لا تخلط "موجود في JSON" مع "مرئي للمستخدم"
- 🚫 لا تنتج Sprint بدون `CHANGELOG_vN.md`
- 🚫 لا تستخدم 51/835/17 كـ baseline timing
- 🆕 🚫 **لا تقترح live integration مع endpoint حكومي قطري بدون smoke test من Heroku أولاً**

-----

## 6. MoJ Data Freshness — Permanent Reality

- **آخر تحديث `data.gov.qa`:** 2025-12-31 (>139 يوم قديمة)
- Sprint 2.7 أضاف banner شفاف
- Self-healing: `/api/health` يستدعي `refresh_freshness()` تلقائياً
- بدائل:
  - **MME API** — Sprint 2.29
  - ~~**المثمن**~~ — deferred 2026-05-19 (§20.8)
  - **Confirmed sales** — السكرتيرة الخميس → Sprint 2.16.16 (renumbered from 2.16.13 → 2.16.15 → 2.16.16 as A11 + A2 took intermediate slots)
- **منذ 2026-02-28**: MUC clause active

**لا تدّعِ "أسبوعياً"** — حُذفت في Sprint 2.7.

-----

## 7. Area Names — Strict GIS Rule

- **`Vector/Districts/MapServer/0`** هو المصدر **الوحيد** المعتمد
- لا aliases سوقية، لا استنتاج جغرافي
- مثال: PIN 51500109 → GIS = **الغرافة**. السوق يقول "ازغوى" لكن غير رسمي.
- Zone ≠ المنطقة الإدارية. Zone 70 = 6+ مناطق إدارية

### MoJ naming normalizations

|إعلانات|MoJ|
|---|---|
|الدحيل|دحيل|
|أبو هامور|بو هامور|
|أم قرن|ام قرن|

-----

## 8. Interpreting PD_NO and CadastrePlots

- **PD_NO=0** = قطعة غير مفروزة → كومباوند محتمل
- **PD_NO ≠ 0** = مفروزة رسمياً
- PIN رقمي: `where=PIN={pin}` بدون quotes

### Qatar zoning distribution

|Code|Count|Share|
|---|---|---|
|R1 / R1-TYP|120,779|~84.0%|
|R2|19,050|~13.2%|
|R3|3,947|~2.7%|

### BUILDING_NO_SUBTYPE (Sprint 2.16.5)

|Code|Type|Asset mapping|
|---|---|---|
|1|Villa/House|standalone_villa|
|2|Compound with Villas|compound_small|
|4|Shopping Complex|commercial|
|6|Building with Flats|apartment_building|
|11|Tower|tower (Sprint 2.16.6 fix)|
|13|Commercial|commercial|

-----

## 9. Red Flags

في وصف الإعلان:

|الجملة|المعنى|
|---|---|
|`بسعر الأرض` / `للهدم`|البناء بقيمة صفر|
|`قديم`|بائع يعترف بالقدم|
|`تنازل` / `أقساط متبقية`|السعر الفعلي ≠ المعلن|
|`بدون فرز` / `خلاف`|تعقيدات قانونية|

### Green flags

`حديث البناء` · `لم تُسكن` · `تشطيب جديد` · `زاوية`

### Asking-side red flags

- علاوة > 25% على أرض → افحص ميزات فرعية
- علاوة > 50% على فيلا → stock-mismatch
- علاوة > 100% → off-plan/new-build

-----

## 10. Honesty & Decision Principles

1. عند نقص البيانات، صرّح. **اذكر n.**
2. MoJ = صفقات منجزة، ليس "قيمة سوقية". لا تدّعِ أنها "ناقصة التسجيل" — مفنّد.
3. لـ n < 10 = "إرشادي، غير معتمد"
4. اعترف بالخطأ، لا تدافع
5. اكشف الإشارات السلبية
6. **لا تتخذ قرار المستخدم**
7. عند تحدي المستخدم، **أعد فحص الأدلة**
8. 🆕 **عند توثيق قرار تخلّي**، اكتب الأسباب صراحة. الصدق في توثيق الفشل أهم من توثيق النجاح.

-----

## 11. Completed Sprints

|Sprint|CHANGELOG|Content|
|---|---|---|
|≤ 2.6|v2–v12|Core engine, RICS, 10-Year Rule|
|2.7|v13|Data Freshness Transparency|
|2.9|v14|Neutral Direction Fix|
|2.10|—|Stock Stratification validation|
|2.14|—|Service scope tiers|
|2.15|v15|L4 Building Age — rolled back|
|2.15.1|v16|L4 via prefilled offline cache|
|2.16.0|v21|Stock Stratification exposure|
|2.16.1|v23|HOTFIX — JS identifier collision|
|2.16.2|v24|Stratum-aware negotiation|
|2.16.3|v25|Mobile header fix|
|2.16.4|v26|Mobile form clipping fix|
|2.16.5|v27|QARS migration to khazna|
|2.16.6|v28|Classifier v2 subtype-aware|
|2.16.7|v29|Housekeeping (A3+B2+A4+A10)|
|2.16.8|v30|Tower CTA + MUC backend|
|2.16.9|v31|MUC frontend display|
|2.16.10|v32|Tower input ambiguity — flagship fix|
|2.16.11|v33|Tower sanity carve-out|
|2.16.12|v34|B1 + B3 housekeeping|
|**2.16.14**|**v35**|**Zoning cross-check (Bug A11) — flag stale QARS subtypes**|
|**2.16.15**|**v36**|**Pydantic extra='forbid' (Bug A2) — reject unknown fields at API boundary**|
|**2.19**|**v37**|**Cap Rate Calibration v1 — villas + compounds from PropertyFinder rentals ÷ MoJ sale medians (Al-Ebb 4.7% reliable)**|
|**2.19.1**|**v38**|**Polish & Fixes — Arabic provenance labels, villa 4% rationale, stratification null-guard (A12), rent/m² outlier guard (A13)**|
|**2.20.0**|**v39**|**Land Comparable Adjustments Grid (time-only) — RICS time-normalisation + AdjustmentGrid framework (E8/E10/E11); size deferred 2.20.1 (R²≈0.05), corner deferred (E12 BLOCKED, A8 partial)**|
|**Mthamen Analysis**|*standalone*|🆕 **2026-05-18 reverse engineering مكتمل. 2026-05-19 deferred indefinitely** — see §20.8|

### Deferred Sprints

|Order|Sprint|Description|Blocker|
|---|---|---|---|
|**1**|**2.16.16**|**Confirmed Sales DB integration** (renumbered 2.16.13 → 2.16.15 → 2.16.16 — A11 and A2 took intermediate slots)|بيانات السكرتيرة (الخميس 2026-05-21)|
|2|2.17|QARS local snapshot|priorities post-Thursday|
|3|2.18|A6 latency + async landmarks + BUA-aware sanity|priorities post-Thursday|
|4|2.20|A8 Comparable adjustments grid|design + confirmed sales|
|5|2.29|MME apartments integration|MME auth flow|

> **🆕 NOT in deferred list**: Mthamen integration. Decision 2026-05-19 (§20.8) — موقّف لأجل غير مسمى. أي إحياء لاحق يحتاج الثلاث شروط في §20.8.

-----

## 12. Qatar GIS — Quick Reference

```python
KHAZNA_BASE = "https://khazna.gisqatar.org.qa/fed/rest/services"
QARS_POINT_URL = f"{KHAZNA_BASE}/QARS/QARS_Point/FeatureServer/0/query"

where=f"ZONE_NO={z} AND STREET_NO={s} AND BUILDING_NO={b}"
outFields="*"   # PIN, QARS, BUILDING_NO_SUBTYPE, etc.

GIS_BASE = "https://services.gisqatar.org.qa/server/rest/services"

CadastrePlots/MapServer/0/query
   where=f"PIN={pin}"
   outFields=PIN,PDAREA,PD_NO
   returnGeometry=true, outSR=4326

# Spatial queries
   geometry={'x':cx,'y':cy,'spatialReference':{'wkid':4326}}
   geometryType=esriGeometryPoint, inSR=4326

# Layers
Vector/Districts/MapServer/0     ANAME, ENAME, DIST_NO
Vector/Zoning/MapServer/0        ZONING
Vector/Commercial_StreetsA/0     شوارع تجارية
Vector/ROADFlowlnA/MapServer/0   ROAD_CLASS
Vector/Landmarks/MapServer/0     معالم (CATEGORY)

# 🆕 GIS deep link (من تحليل المثمن — قابل للإضافة في output_briefs)
http://geoportal.gisqatar.org.qa/searchpin/?pin=<PIN>
```

-----

## 13. MoJ Data — Quick Reference

```python
https://www.data.gov.qa/api/explore/v2.1/catalog/datasets/
   weekly-real-estates-sales-bulletin/exports/csv?
   lang=ar&timezone=Asia/Qatar&use_labels=true&delimiter=,

# ⚠️ NBSP في "تاريخ التثبيت" — normalize:
# raw = re.sub(r'\s+', ' ', cell_value).strip()
```

**MME API** (للمستقبل):
```
Auth: GET qrepcms.aqarat.gov.qa/flows/trigger/[token] → JWT
Sales: POST qrepbe.aqarat.gov.qa/mme-services/kpi/sell/kpi29/transactions
Rentals: POST .../kpi/rent/kpi30,31,32
propertyType: 1=villas, 5=apartments, 6=land
```

-----

## 14. Operational Notes

- **curl يعلّق** على `data.gov.qa` — استخدم Python `urllib`
- **arady.qa pages 2–3** غير قابلة للوصول (Next.js JS)
- **PropertyFinder** SSR — pagination يعمل
- **Heroku timeout** = 30s
- **Heroku rate limit** = 10/min في الـ audits أضف `time.sleep(7)`
- 🆕 **sak.gov.qa** — F5 ASM WAF يحجب Heroku. لا live calls. (§20.8)

-----

## 15. Overall Philosophy

> **"المحرك جاهز 80%، لكن المحرك ليس المنتج."**

كل Sprint يخدم: **هل المستخدم العادي يستفيد؟**

**الصدق في التشخيص يفوق السرعة في التسليم.** هذا يشمل **توثيق قرارات التخلّي** بنفس وضوح توثيق النجاح (مثال: §20.8).

-----

## 16. Audience Calibration

|Audience|English codes?|Methodology jargon?|Open decisions?|
|---|---|---|---|
|أنس (engineer)|نعم|نعم|نعم|
|المدير|لا|خفيف|نعم|
|السكرتيرة|**أبداً**|**أبداً**|**أبداً**|

-----

## 17. Scope expansion mid-session

عند تقديم نوع أصل أو مصدر جديد، عاملها **إشارة توسّع نطاق**:
- توقف، أبرز التوسّع، اقترح بنية
- تمييزات منهجية قد تحتاج حدود ملفات جديدة

-----

## 18. Known Bugs Catalogue (2026-05-19 evening)

### 🟢 Resolved (15 bugs)

A1, A3, A4, A10, B1, B2, B3, Tower CTA, MUC display, Tower input, Tower sanity → Sprints 2.16.6–2.16.12

**A11** (Zoning/Subtype contradiction) → **Sprint 2.16.14** (CHANGELOG_v35, deployed 2026-05-19 PM)
- Reference case: أشغال 61/875/20 (subtype=6 in Zoning=CCC)
- Audit: 9.1% on 22 government/business landmarks
- Fix: Branch 0 cross-checks zoning, emits non-blocking flag
- Severity: Medium (system already returned "تقييم مشروط" instead of wrong value)

**A2** (Pydantic schema accepts unknown fields silently) → **Sprint 2.16.15** (CHANGELOG_v36, deployed 2026-05-19 evening)
- Reference case: `rental_inome` typo silently dropped → engine sees `rental_income=None` → "insufficient data" fast path while user believes input was honored
- Fix: `model_config = ConfigDict(extra='forbid')` on both EvaluateRequest and EvaluateDetailsRequest
- Now returns HTTP 422 with `type=extra_forbidden` and the bad field name in `loc[-1]`
- Severity: Medium (no wrong value produced; the cost was methodological silence)

**A12** (Stratification gap — villa cap-rate rows with no MoJ land median) → **Sprint 2.19.1** (CHANGELOG_v38, 2026-05-20)
- Reference case: Pearl/Lqateefiya villa cells with large rent samples but `stock_class=null` (Pearl is reclaimed land — almost no raw-land sales to compute the villa/land ratio)
- Fix: Rule E4 hard guard in `cap_rate_calibrator.py` — a villa cell with no land median is forced to `confidence='fallback'` (note `stratification_unavailable:no_moj_land_median`), so it can never silently promote to reliable/indicative
- Severity: Medium (rows were already `fallback`; the risk was *future* silent promotion)

**A13** (Rent/m² outliers reaching calibration) → **Sprint 2.19.1** (CHANGELOG_v38, 2026-05-20)
- Reference case: Pearl 1500+ villa @ 0.67, معيذر compound @ 183.33, الخريطيات @ 101 (all n=1)
- Fix: `is_plausible_listing()` rejects rent/m² outside [5, 200] QAR/m²/month before binning; rejections counted + persisted (`calibration_meta`) + surfaced in `/api/calibration`; `>10%` rate emits a WARN
- Severity: Low (all n=1 → fallback; the value is preventing median contamination at scale)

### 🔴 Critical: لا توجد. ✅

### 🟠 High

|ID|Bug|Target|
|---|---|---|
|A6|Latency P95 ~25s (reproduced live 2026-05-19 evening on 51/835/17 — 31s timeout)|2.18|
|A8|Comparable adjustments grid|2.20|

### 🟡 Medium

|ID|Bug|Target|
|---|---|---|
|A5|`asset_type: unknown` بدون شرح|backlog|
|A7|`rics_compliant` دائماً false|backlog|

### 🟢 Deferred

- BUA-aware sanity check → 2.18+
- Visual building assessment → 2.22+
- Per-stratum cap rate calibration → بعد بيانات السكرتيرة

-----

## 19. Tower Methodology

> **Trigger**: Sprint 2.16.10 — Lusail B201 (3,378م² plot، ~20 طابق). أنس أدخل `rental_income: 30,000` → 4.62M ر.ق (~32× خطأ).

### القاعدة 1 — Input Disambiguation

أنواع تتطلب `unit_count` + `per_unit_rent`:
- `tower` · `compound_large` · `apartment_building` · `commercial_building`

```python
if asset_type in TOWER_LIKE_TYPES and unit_count and per_unit_rent:
    rental_income_monthly = unit_count * per_unit_rent
elif rental_income:
    rental_income_monthly = rental_income
```

### القاعدة 2 — BUA ≠ Plot (Sprint 2.16.11)

- Lusail B201: plot=3,378، BUA≈67,560
- rent/plot²m = 285 ← مرتفع
- rent/BUA²m = 14.2 ← الحقيقي

Carve-out tuple يستثني tower/compound_large/apartment_building.

### القاعدة 3 — MUC مزيد للأبراج

- MUC clause **إلزامي**
- نطاق التقدير ±15% (مقابل ±10% للفلل)
- إشارة لـ stress test على cap rate

### القاعدة 4 — Cap Rate verify (deferred 2.20+)

`LANDS_CAP_RATE_PRIMARY = 0.04` محل شك. بيانات السكرتيرة الخميس قد تُظهر 7-8%.

-----

## 20. Cost Approach (DRC) — منهجية مرجعية، **ليست active**

> **🆕 2026-05-18: Reverse engineering كامل. 2026-05-19: deferred indefinitely (§20.8).**

### 20.1 ما هو المثمن؟

تطبيق رسمي من وزارة العدل القطرية يقدّم **قيمة تقديرية** باستخدام **Cost Approach (DRC = Depreciated Replacement Cost)** — إحدى 5 طرق RICS.

- **Package**: `com.informatique.pricing` (v3 build 25)
- **Backend**: `https://sak.gov.qa/pricingws/jsonstore1/`
- **Status (Thammen)**: ⏸️ **archived reference only**, never integrated

### 20.2 المنهجية المكشوفة (من string resources الـ APK)

```
القيمة التقديرية = إجمالي الأرض + إجمالي قيمة البناء - الإهلاك + إضافات
                  ± هامش (سقف أدنى/أعلى)
```

**إجمالي الأرض (9 طبقات)**:
```
= (سعر_الأساس_للقدم² × مساحة_الأرض_بالقدم²)
+ قيمة تمييز المدينة
+ قيمة تمييز المنطقة
+ قيمة تمييز الحي
+ قيمة تمييز المربع
+ قيمة تمييز موقع العقار (شارع رئيسي/فرعي)
+ قيمة تمييز نوع العقار (سكني/استثماري/إداري/تجاري)
+ قيمة تمييز منطقة الخدمات
+ قيمة تمييز الخدمات الترفيهية
```

**إجمالي قيمة البناء (4 طبقات)**:
```
= سعر البناء (متوسط × مساحة)
+ إجمالي قيمة التشطيبات
+ قيمة الأدوار المتاحة     ← مهم للأبراج
- إجمالي قيمة المرافق المخصومة
```

**الإهلاك**: دالة(عمر، تشطيب، حالة)

### 20.3 الـ API Endpoints (مرجع توثيقي فقط)

**Base**: `https://sak.gov.qa/pricingws/jsonstore1/`

| Endpoint | الغرض |
|---|---|
| `?action=getprices&squarid=X` | سعر الأساس لمربع |
| `?action=GetPriceEquationData&BuildingNo=X&PinNo=Y` | معادلة لـ PIN |
| `?action=calculate&PinNo&deviceUDID&...` | حساب PIN-based |
| `?action=calculatevirtual&...` | حساب من inputs |
| `?action=graphcalc&...` | رسم بياني |
| `?action=syncuserdata&deviceUDID` | rate limit tracking |

### 20.4 لماذا المثمن قيّم منهجياً (حتى بدون integration)

| Dimension | المثمن | Thammen |
|---|---|---|
| **المنهجية** | Cost (DRC) | Market (MoJ) + Income (DCF) |
| **يجيب على** | "كم تكلّف بناؤه؟" | "بكم يُباع/يُؤجَّر؟" |
| **يدعم Income؟** | ❌ | ✅ |
| **cap rates؟** | ❌ | ✅ |
| **web؟** | ❌ Android/iOS فقط | ✅ |
| **Rate limit؟** | ✅ ~1/يوم | ❌ B2B-ready |

**القيمة المنهجية المتبقّية**:
- تأكيد رسمي قطري أن **Cost Approach** جزء من إطار التقييم الحكومي
- منهجية DRC الكاملة موثّقة بالعربية في Thammen
- valuer brief يمكن أن يشير لـ "Cost Approach وفق منهجية المثمن (MoJ)" بدون استدعاء API
- اكتشاف `geoportal.gisqatar.org.qa` كـ deep link مفيد

### 20.5 الـ APK reverse engineering — Deliverables (Archived)

ملفات في `/mnt/user-data/outputs/` (لا تُنشر):
- `mthamen_report.md` — 16 KB report
- `mthamen_reference.py` — 17 KB Python wrapper (compiles، لا يعمل)
- `mthamen_strings_table.txt` — 225 string resources

### 20.6 الحماية المكتشفة

- **F5 BIG-IP ASM WAF** — HTML rejection page مع support ID لكل طلب
- **Daily rate limit per deviceUDID** — `"لقد تجاوزت الحد المسموح..."`
- **Root detection** — يرفض الأجهزة rooted
- **Geo-restriction (مفترض)** — Heroku US/EU = WAF يرفض. iPhone قطري على شبكة قطرية = يُقبل (تحت quota).

### 20.7 ملخص ما تعلّمناه

**فوائد محققة (5 — تبقى)**:
1. تأكيد منهجي على RICS triangulation (Cost Approach معتمد قطرياً)
2. منهجية DRC موثّقة بالعربية (9 land + 4 building)
3. اكتشاف geoportal.gisqatar.org.qa (deep link اختياري)
4. تأكيد أن MoJ هو المصدر الوحيد (المثمن يستخدم MoJ DB)
5. درس هندسي: smoke test من Heroku أولاً قبل أي endpoint حكومي

**خسائر صريحة (3)**:
1. 2-3 ساعات بناء `mthamen_reference.py` لن يُنشر
2. Calibration workflow على iPhone مستحيل (1/يوم × 50 عقار = 50 يوم)
3. لم نستخرج cap rates (المثمن لا يستخدم Income)

**النتيجة الصافية**: ✅ إيجابية — التعلّم > الخسارة.

### 🆕 20.8 Decision Log 2026-05-19 — لماذا تخلّينا

**التاريخ**: 2026-05-19 (الثلاثاء)
**القرار**: deferred indefinitely. Mthamen integration **ليس** Sprint مستقبلي.
**الأسباب (4)**:

1. **WAF block قاطع**: `smoke_mthamen_v2.py` من Heroku:
   ```
   Profiles bypassing WAF: 0/6
   Profiles WAF-rejected:  6/6
   ```
   كل profile (Dalvik، Chrome، iPhone Safari، no UA، okhttp، Qatar XFF spoofed) → HTTP 200 + F5 ASM rejection. حتى `https://sak.gov.qa/` root محجوب.

2. **Daily quota = ~1/يوم على iPhone قطري حقيقي**: أنس اختبر **محاولة واحدة** فقط على هاتفه (iPhone قطري، شبكة قطرية)، وحصل على "لقد تخطيت الحد الأقصى للمحاولات". هذا يعني calibration workflow **غير ممكن** حتى يدوياً — 50 عقار = 50 يوم بـ device واحد.

3. **Infrastructure fragility**: `sak.gov.qa` يعمل على ASP.NET `.ashx` legacy + F5 ASM. أي تحديث WAF config قد يكسر integration. ربط Thammen production بـ endpoint يمكن أن يموت بلا إشعار = مخاطرة غير مقبولة.

4. **منهجية > integration**: قيمة المثمن في **منهجيتها المنشورة** (DRC = Land 9 + Building 4 - Depreciation)، ليست في "كم يقول السعر اليوم؟". المنهجية الآن موثّقة بالكامل في §20.2-20.6.

**ما الذي يتطلبه إحياء هذا القرار**:
- إثبات أن `sak.gov.qa` reachable من Heroku (شغّل `smoke_mthamen.py` و `smoke_mthamen_v2.py` — قارن الناتج)
- إثبات أن الـ daily quota تغيّر بما يسمح بالاستخدام المهني (>10 محاولات/يوم على الأقل)
- موافقة رسمية من MoJ Qatar (مفضّلة، ليست شرطاً)
- **بدون هذه الثلاث**، أي اقتراح بإحياء Mthamen integration **يجب أن يُرفض**

-----

## 21. Marathon Lessons — 2026-05-18

### 21.1 Sprint Cascade Pattern (7×)

Sprint 2.16.6 → 2.16.12 في يوم واحد. كل Sprint = **fix جراحي واحد** + test + smoke test.

### 21.2 المختبر الذهبي: Lusail B201

**input ambiguity** أخطر من crash. User أدخل 30K معتقداً أنه إيجار البرج؛ النظام أنتج 4.62M بدون أي error.

**Rule**: لأي حقل numeric، اسأل **"هل هناك >1 تفسير معقول؟"**

### 21.3 6-item Pre-Deploy Checklist (اعتُمدت في §5)

### 21.4 4-Layer MUC Flow

Backend → Response → Frontend priority → Display. canonical root > brief.

### 21.5 User Collaboration in DevTools

عند استعصاء container على endpoint، طلب فحص DevTools من user يفوق ساعات تخمين.

### 🆕 21.6 External Endpoint Smoke Test First

**درس 2026-05-19**: قبل بناء integration مع endpoint حكومي:
```
1. اكتب smoke_<endpoint>.py
2. push to Heroku
3. heroku run python smoke_<endpoint>.py
4. قرار: reachable → integrate. WAF/blocked → defer.
```
15 دقيقة → يوفّر 3 ساعات بناء يُرمى.

### 21.7 Numbering Discipline

أرقام Sprints لا تتكرر. CHANGELOG_vN = Sprint counter.

-----

## 22. Self-Correction Triggers

لو في أي نقطة من الجلسة:

- أقترح Sprint بدون audit → STOP، شغّله
- أدّعي bug بناءً على ذاكرة → STOP، تحقق في المتصفح
- أكتب أمر بـ `&&` → STOP، افصل
- أستشهد بوسيط بدون n → STOP، أضف n
- أرشّن MoJ staleness → STOP، اعترف
- أقترح uplift على MoJ من listings → STOP، Rule E1
- أعالج وسطاء فيلا كـ population واحد → STOP، Rule E4
- ادعاء أن MoJ "ناقص التسجيل" → STOP، falsified
- أستخدم 51/835/17 كـ baseline → STOP، A6، use 52/903/90
- أدمج tower input كـ `rental_income` فردي → STOP، use `unit_count + per_unit_rent`
- 🆕 **أقترح إحياء Mthamen live integration → STOP**، فُحص 2026-05-19 وفشل قاطعاً. راجع §20.8. الثلاث شروط صريحة.
- 🆕 **أقترح integration مع endpoint حكومي قطري بدون smoke test → STOP**، §21.6
- 🆕 **أعالج المثمن كـ Sprint candidate → STOP**، Mthamen **ليس** في deferred Sprints. هو **archived reference**.
- 🆕 **أثق في QARS_Point subtype كمصدر وحيد دون cross-check مع Zoning → STOP**، Bug A11 (Sprint 2.16.14) أثبت أن 9.1% من المباني الحكومية لها subtype قديم. استخدم نمط Sprint 2.16.14: `_is_non_residential_zone()` + `_fetch_zoning_at_point()`. راجع Rule E7 في EMPIRICAL_FINDINGS.
- 🆕 **أضيف FastAPI request model جديد بدون `model_config = ConfigDict(extra='forbid')` → STOP**، Bug A2 (Sprint 2.16.15) أثبت أن default `extra='ignore'` يُسقط الحقول المُخطئة كتابياً بصمت — المستخدم يعتقد إدخاله صحيح بينما المحرّك يستلم `None`. كل FastAPI model يُلامس HTTP boundary يجب أن يبدأ بـ `model_config = ConfigDict(extra='forbid')` كأول سطر داخل الـ class.

المستخدم يُفعِّل أياً منها بـ **"اقرأ القسم X"**.

### Recall phrases

| العبارة | المعنى |
|---|---|
|"تذكر Sprint 2.16.X" | Sprint X من الماراثون (6 → 12) أو ما بعده (14، 15) |
|"تذكر khazna" | GIS Qatar migration 2026-05-17 |
|"تذكر outage 17 مايو" | GIS outage timeline |
|"تذكر Lusail B201" | Tower Input Disambiguation |
|"تذكر المثمن" | Reverse engineering 2026-05-18 + قرار 2026-05-19 (§20.8) |
|"تذكر قرار 19 مايو" | قرار التخلّي عن Mthamen |
|🆕 "تذكر Bug A11" | Zoning/Subtype contradiction discovery + Sprint 2.16.14 fix |
|🆕 "تذكر أشغال 61/875/20" | الـ reference case لـ Bug A11 |
|🆕 "تذكر Rule E7" | QARS subtype requires Zoning cross-check |
|🆕 "تذكر Sprint 2.16.14" | A11 fix deployed 2026-05-19 PM, CHANGELOG_v35 |
|🆕 "تذكر Sprint 2.16.15" | Bug A2 (Pydantic extra='forbid') deployed 2026-05-19 evening, CHANGELOG_v36 |
|🆕 "تذكر Bug A2" | Pydantic schema lenience — unknown fields silently dropped; fix = `model_config = ConfigDict(extra='forbid')` |
|"بيانات السكرتيرة جاهزة" | Sprint 2.16.16 (renumbered 2.16.13 → 2.16.15 → 2.16.16) |
|"راجع EMPIRICAL_FINDINGS" | قواعد E1-E7 |
|"اقرأ القسم X" | تفعيل self-correction trigger |

-----

*Bound to every Thammen session. Last updated 2026-05-19 evening (بعد Sprint 2.16.15 — Bug A2 / Pydantic extra='forbid' deployment).*
