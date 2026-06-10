# Thammen (thammen.qa) — Project Instructions

> **Scope:** هذا المشروع مخصص حصرياً لتطوير وصيانة موقع تقييم العقارات القطري `thammen.qa`. أي مهمة خارج هذا النطاق (تقارير عقارية مستقلة، أبحاث سوق، تقييم عقار معين بدون لمس المنصة) **لا** تنتمي لهذا المشروع.

> **هذه الوثيقة = مرجع منهجي ثابت** (version-agnostic؛ governance-consolidated، انظر `docs/BRIEF_governance_consolidated_2026-05-30.md`). **الحالة الحيّة للإنتاج (engine / sprint / Heroku vN): راجع CLAUDE.md production snapshot + `/api/health` — المصدر الوحيد (Rule #58).** أرقام النسخ/الـ Sprints/Heroku **لا تُكرَّر هنا** (تنجرف). الـ **ROADMAP المعتمد = §11 (Deferred Sprints)** أدناه. قواعد منذ الإصدار 8: Operational #50-#58 (#54 Multi-AI، #57 ground-truth handshake، #58 measured-wins؛ #55/#56 محجوزان)، Empirical E15-E20.

-----

## 1. Product Identity

**Thammen** هو نموذج تقييم آلي (AVM) للسوق العقاري القطري، يعمل وفق RICS Red Book Global Standards (إصدار 31 يناير 2025 — VPGA 10 + VPS 6 + IVS 106) مع تكييفات للظروف القطرية. مصادر البيانات:

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

> **النموذج ثنائي المسار** (منذ هجرة Claude Code 2026-05-19؛ lean منذ 2026-06-02): **Claude.ai** يكتب الـ **brief الموقَّع** (تأطير منهجي + multi-AI عند الحاجة + توقيع Gate-2) — **لا** zips. **Claude Code** ينفّذ: يحرّر الملفات **مباشرة** في `C:\Thammen\deploy v2`، يشغّل الاختبارات، ينشر، ويُغلق الوثائق. **لا** `present_files` / `/mnt/user-data/outputs/` / `sprint*.zip` بعد الآن (كان نموذج claude.ai-chat قبل الهجرة).

1. **مخرجات كل Sprint (Claude Code، على القرص):** تحرير مباشر للملفات + **`CHANGELOG_v{N}.md`** (إلزامي، بنية الـ8 أقسام) + **اختبار معزول** يستدعي المسار الإنتاجي الفعلي (Rule #40 / E14) + رفع **ENGINE_VERSION + SPRINT_TAG** في `evaluate_unified.py` (يُغذّي `/api/health`).
2. **انضباط الأوامر:** **أمر واحد لكل سطر** (لا `&&` على نفس السطر). صياغة Windows shell (PowerShell / `cmd`): `cd /d "C:\Thammen\deploy v2"`، `copy /Y file file.bak` (وليس `cp`)، `findstr /C:"..." file.py` (وليس `grep`)، `$null` لا `/dev/null`.
3. **النشر:** `git subtree push --prefix "deploy v2" heroku master` (Rule #43 — التطبيق تحت `deploy v2/`؛ `git push heroku master` المجرّد يُرفض من الـ buildpack) **+** `git push origin master` (نسخة احتياطية).
4. **CHANGELOG_vN.md** مع كل Sprint — البنية ذات الـ8 أقسام (Custom_Instructions §2).
5. **أرقام الـ Sprints متسلسلة** ولا تتكرر أبداً. **الحالة الحيّة (engine / sprint / Heroku vN) = CLAUDE.md snapshot + `/api/health` (المصدر الوحيد، Rule #58)** — لا تُكرَّر هنا (تنجرف).

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

- `POST /api/evaluate` — تقييم سريع (عنوان zone/street/building **أو** `pin` للأرض — Sprint 2.21.0)
- `POST /api/evaluate/details` — مع تفاصيل المبنى (يقبل أيضاً `pin`)
- **Dual input flow (Sprint 2.21.0):** كل من الـ endpoints يقبل **إما** العنوان (zone+street+building، مسار QARS للفيلات/المباني) **أو** `pin` (مسار CadastrePlots للأراضي الخام — لا QARS). XOR إلزامي (422 عربية لو كلاهما/لا شيء). `pin` → `input_mode='land'` يُمرَّر للمُصنِّف فيُنتج `raw_land` (مع حُرّاس: ≥50K compound_large، ≥15K compound_small) → تُفعَّل شبكة المقارنات (2.20).
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

- **آخر تحديث `data.gov.qa`:** 2025-12-31 (مقيس 2026-05-30: **150 يوم** قديمة)
- Sprint 2.7 أضاف banner شفاف
- Self-healing: `/api/health` يستدعي `refresh_freshness()` تلقائياً
- بدائل:
  - **MME API** — Sprint 2.29
  - ~~**المثمن**~~ — deferred 2026-05-19 (§20.8)
  - ~~**Confirmed sales**~~ — Sprint 2.16.16 **مؤجَّل لأجل غير مسمى** (لا مصدر داخلي صالح: مصدر السكرتيرة مغلق 2026-05-24 + brokerage/Gardenia مغلق). ليس مصدر بيانات أو dependency.
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
|**2.21.0**|**v40**|**PIN Input for Lands — dual input (address \| PIN); classifier `input_mode='land'`→`raw_land`; geo_v2 PIN-centroid so the 2.20 grid fires for bare lands; Rule #46**|
|**2.18.0**|**v44**|**🆕 Parallel `property_factors` fan-out — `ThreadPoolExecutor(max_workers=5)` over the 5 independent GIS layer calls in `analyze_property`. Audit-derived (audit_a6_2026-05-23.md) and audit-validated: predicted Δ −4 000 ms on villa/raw_land cases, measured −4 003 ms / −3 887 ms (deviation ±2%). Fast-paths unchanged; HTTP 503 class on compound_small UNCHANGED (Sprint 2.18.1 territory). New rules: Operational #51 (audit-driven Sprint pattern) + EMPIRICAL E19 (max_workers = task count). Deployed Heroku v99.**|
|**2.18.1**|**v45**|**🆕 Parallel `_expand_extent` BFS upfront-prefetch — `ThreadPoolExecutor(max_workers=min(N,20))` pre-fetches all eligible plot polygons before the serial BFS loop. §5 mini-audit CORRECTED the original audit's "5-8s" prediction (eligibles miscounted ×2, get_plot's internal cadastre+geometry serial chain missed) to honest 22-27s. Post-deploy measured 28.9s in-process (15% over corrected prediction; documented per Rule #51). HTTP 503×3 → **200×3** on 51/835/17 (THE WIN). Wider cohort failure rate 19%→0%. Deployed Heroku v100. **Latency goal delivered; visual verification by Anas unmasked pre-existing methodology bug** → Sprint 2.18.1.1.**|
|**2.18.1.1**|**v46**|**🆕 Compound-misroute fix — Patches A + C. Bug discovered by Anas's visual verification: 51/835/17 (67,536 m² compound) was classified compound_small via QARS subtype + assigned MoJ valuation 6.8M + land_value=218M (= 67,536 × 3,229), producing building=−211M / pct=−3,107% silent arithmetic failure. The bug existed before 2.18.1 but was masked by HTTP 503; 2.18.1's latency fix unmasked it. **Patch A** (qatar_gis.full_property_lookup): when classification.asset_type==COMPOUND_SMALL and extent.total_area_m2 ≥ 15,000 (EMPIRICAL E20 — MoJ "مجمع فلل" sampling max = 15,027 m²), promote both classification + extent to COMPOUND_LARGE. Routes via ASSET_TYPE_TO_MOJ_CATEGORY['compound_large']=None → MoJ skipped → valuation_amount=None → clean Income Approach refusal. **Patch C** (evaluate_unified._decompose_value): universal `if land_value > valuation_amount: return None` (Anas decision #4 — applies to all asset_types; catches premium-land villa teardowns + MoJ outliers). Post-deploy probe + Anas's visual verification 9/9 ✓. New rules: Operational #52 (latency unmasks methodology) + EMPIRICAL E20 (15K MoJ compound boundary). Deployed Heroku v101.**|
|**2.21.0.9**|**v43**|**🆕 Multi-QARS Detection — STAGE 1. One cadastral PIN with 2+ QARS-addressed villas (Bou Hamour 56/565/21 trigger case): `is_shared = n_qars≥2` (after compound_large + apartments carve-outs); bracket selection uses `PDAREA/n_qars` (no title discount); single unified UI flag + mandatory manual user override. NO classification (attached vs separate) — 15m/18m GPS-centroid thresholds rejected after domain confirmation that physically-separate villas can have 15.2m centroids (MME 3m setback × 2 → centroids ≥16m, E15). Stage 2 pre-specified (wall-to-wall ≥6m → separate, <1m → attached, E18). Staged-valuation pattern adopted platform-wide (E16) + 1-field minimum input principle (E17) + Operational_Rules #50. Deployed Heroku v97.**|
|**2.21.0.7.1**|**v42**|**Micro-follow-up (v90→v91): built non-residential→reject (not stop; address tab is a dead-end); `_expand_extent` defensive `sorted(…,key=str)` (pre-existing int/str crash); discovered asset-type Arabic label (fixes "نوع العقار: غير محدد"); PIN-tab hotfix warning removed (superseded)**|
|**2.21.0.7**|**v42**|**Asset Type Reality Check — PIN/land path consults QARS-in-polygon (P1, building present→stop) + General_Landuse RULEID (P2, authoritative coded-value map: residential 1/2/20→value, reject 5-18/21/23, warn 3/4/22, agri 19) + P4 building-factor guard; precedence QARS>RULEID>geometry; deployed v89**|
|**2.21.0.5**|**v41**|**Land Output Polish — conditional `raw_land` rendering: scope=supported, PIN address, skip building decomposition, land-aware MUC factors/known-unknowns + due-diligence; Rule #47 (alias pattern)**|
|**2.21.0**|**v40**|**PIN Input for Lands — dual input (address \| PIN); classifier `input_mode='land'` branch (raw_land + geometric guards) so bare-land PINs reach the 2.20 grid; Rule #46**|
|**Mthamen Analysis**|*standalone*|🆕 **2026-05-18 reverse engineering مكتمل. 2026-05-19 deferred indefinitely** — see §20.8|
|**2.21.2**|**v47**|**🆕 Hybrid Valuation Foundation — `hybrid_valuation.py` ships with `HYBRID_TIER_CONFIG` + `hybrid_valuation_v1()` (Cases A/B/C/D + Constraints 7+8). Rule E3 expanded to 8 numbered constraints. T2 cap 0.40, T3 cap 0.15, T1 floor 0.45, mandatory MUC when T1 absent, T3-alone refused. Function exists but no engine path calls it. 22 tests / 67 sub-checks PASS, regression 27/27. Deployed Heroku v107.**|
|**2.21.3**|**v48**|**🆕 T2 PropertyFinder Lusail apartments hybrid path. First live coupling of hybrid framework. Two audit-driven loops post-deploy: (a) v118 D10 sub-district whitelist (added `'غار ثعيلب'` token after PIN 69/329/20 returned that GIS ANAME rather than the `'لوسيل'` literal); (b) v121 list-page-only connector refactor after detail-fetch overran the 30 s Heroku router. Rule #11 rollback executed at v119 between the two loops. New methodology pattern documented in CHANGELOG_v48 §12: methodology fix unmasks latency (inverse #52 case). Engine `thammen-sprint2p21p3-t2-apartments-lusail`, Heroku v124 = v121 code. H1 PASS at v122 on PIN 69/329/20: value_per_m2=11,571.88 T2-only, n=79 PF listings.**|
|**2.21.4**|**v49**|**🆕 T3 developer-inventory (Aryan, City Avenues, Lusail). Status-aware discount map (`T3_status_discount_map`) replaces scalar `T3_discount_midpoint`: off_plan / under_construction → −17.5%; ready → −10%. Per-row freshness `'stale'` annotation + 0.5× evidence multiplier (D7). Three-shape T3 detection (dict_new / dict_legacy / float / empty). 7-field per-row sources in tier_breakdown (Rule E10 / D12 axis 18). `developer_inventory.sqlite` committed to git pre-deploy per ephemeral-FS workflow (building_age_cache.sqlite pattern, Sprint 2.15.1). 4 Aryan/City Avenues rows seeded, status=under_construction post-Anas pre-deploy correction §5.8 (was inferred `ready`). PIN 69/255/75 = H1 anchor: T3 weight=0.12 (=0.15 cap × 4/5, BRIEF §9 architectural seal verified live). H_WALK PASS for H1 + H11 (live partial-population) + H2 (live kill switch). 26 isolated + 29-file regression PASS. Engine `thammen-sprint2p21p4-t3-aryan-lusail`, Heroku v125 (v127 config).**|

### Deferred Sprints

> **AUTHORITATIVE ROADMAP (single source), updated 2026-06-01.** CLAUDE.md's roadmap
> block is a convenience copy that points here; when they drift, **this table wins**.

**Launch posture (locked, 2026-06-01):** tier = **BETA-FIRST** (Anas). Beta scope = **villas + land only**
(apartments already refuse → gracefully excluded). Full tier register: `docs/LAUNCH_READINESS_GATES_v1.md`;
beta plan: `docs/BETA_LAUNCH_PLAN_v1.md`.

**Shipped since this list was last sequenced (2.22.0a/b arc — Session_Log §20.8–§20.32):** a.8 RICS/IVS-2025
citations · a.9 widened age/quality · a.10 Stage-1 honest-range · a.11 A1 usage filter · a.12 A2 built-type ·
a.13 thin-cell credibility · a.14 bracket honest-range · a.15 beta instrumentation (DORMANT) · a.16 capture
privacy-hardening · a.17 clean-bracket condition caveat · a.18 R9 area-name reconciliation · a.19 thin-path
condition caveat · a.20 A7 rics_compliant status label · a.21 B-1 land-floor/HBU · a.22 B-1.1 framing · a.23
R15 strata-land a18 · a.24 beta-launch entry gate + Terms/Privacy + DPIA · a.25 CC BY 4.0 MoJ source
attribution (Heroku v164) · **2.22.0b.1 Geometry Refinement — zoning-driven footprint + basement excluded
from the comparison driver (Heroku v165, §20.29; value-invariant on no-building-input anchors; FIRST sprint
of the 2.22.0b staged-input arc)** · **2.22.0b.2 guided staged-input flow WRAP (Heroku v166, §20.31)** · **2.22.0b.2.1 separate input screens (Heroku v167, §20.32 — frontend WRAP, value-invariant)** · **2.22.0b.2.2 evidence-quality diagnosis panel (Heroku v168, §20.33 — frontend, value-invariant: the binary confidence badge → a 4-component evidence-quality panel [اكتمال · مقارنات · حداثة · توصيف — قوي/متوسط/محدود] each DERIVED from its engine field §2c, «explanation≠confidence» enforced, component 4 «N/A أرض» for raw_land; implements DESIGN_2p2x §3 Phase 2 of the suspense-reveal arc; the first value-decomposition draft misapplied §3 → withdrawn, signed parent design persisted [Rule #63])** · **2.22.0b.2.3 Confirmation Gate (Screen 2) (Heroku v169, §20.34 — frontend, value-invariant: a NEW confirmScreen between identification and the result, from the SAME response — muted preliminary range + READ-ONLY review [no pencils, plot-area honesty label] + b.2.2 evidence panel reused + «تابِع بهذه البيانات»→refine + «التقرير الكامل الآن»→results; valuer/refusals skip to results [v4 two-path]; first step of the v4 «thinnest-flow» sequence)** · **2.22.0b.3 range-as-lead (Heroku v170, §20.35 — frontend, value-invariant: the results headline becomes the market RANGE [true low–high, asymmetry-ALLOWED — **NOT** a forced symmetric ±; CC recon falsified «symmetric»: thin paths put the median at the high edge so a symmetric bar would invent refused upside] + a muted central-estimate median marker «الوسيط (التقدير المركزي)», point fallback when no range; old two-box removed; value_floor stays SECONDARY [NOT land-to-median]; 4 anchors byte-identical; second step of the «thinnest-flow» sequence)** · **2.22.0b.4 condition/value axis (Heroku v171, §20.36 — R7 OPT-IN levers: `condition=teardown` ↓ land−demolition · `new`+`is_luxury` DRC/Cost-Approach ↑ · explicit `penthouse` ×2.5 BUA; standard `/api/evaluate` value-invariant [4 anchors byte-identical — levers fire only via `/details`]; HONEST RESIDUAL EXTREMES-ONLY — the good/very-good MIDDLE still over-anchors, the 10-Year-Rule DOWN re-anchor is wired only to explicit `teardown`)** · **2.22.0b.5 R7 villa-yield calibration DATA ship (Heroku v172, §20.39 — Gate-2 villa income cross-check but **HEADLINE value-invariant**: swapped `cap_rates.sqlite` → per-area DB [villa reliable 1→6 / indicative 2→10, incl. امريخ الجنوبي 400-600 5.16% net n=46]; the villa income cross-check uses calibrated per-area net yields [vs the flat 4% fallback] when income fires + a usable (area,bracket) cell matches — **BRACKET-GATED** [most cells 400-600; standard anchors in 600-900 stay 4% — CORRECT; B confirmed LIVE Marikh@400-600 → «معدل رسملة معايَر 5.2% n=46 reliable»]; 4 anchors byte-identical; the §9/§10 "ship yield-data" STANDALONE branch; +Soft-Gate-3 stale 2.19.1 mock repair)** · **2.22.0b.6 §6 income-triangulation (Heroku v173, §20.40 — 🔴 Gate-2, the villa headline MOVES [first non-opt-in value move since b4]: new PURE `_income_triangulation` — income_led [a GROUNDED subject rent + a calibrated reliable/indicative cap-rate cell → income LEADS, comparison DEMOTED; circularity guard — only a subject-specific rent leads] + widen_down [a no-rent condition-blind THIN over-anchored villa `land_floor < comparison` → range widens DOWN to the land floor + range_is_headline + MUC high; EXCLUDES clean reliable bracket / dispersion-gated / land-anchored; no invented midpoint]; villa/house; live smoke 54/541/6 → widen_down 1.9M–5.5M↓ [un-anchors Marikh's 5.4M], @400-600+rent → income_led 2.7M, 56/565/21 → byte-identical, 55/296/13 → unchanged [land-anchored], 52/903/90 → refusal; isolated 23/23 + DoD 392/15/45/broad 75; HONEST RESIDUAL income_led BRACKET-GATED 400-600 → Marikh/villa-6 live 600-900 = widen_down only; DEFERRED v2 = Fork C + opex 0.20 + (ii) age-rent + 600-900 cells)** · **2.22.0b.7 §6 v2 cross-bracket yield-borrowing (Heroku v174, §20.41 — `_lookup_calibrated_cap_rate` now BORROWS the area's usable 400-600 cell when the subject's exact plot bracket has none [disclosure + MUC-high + the [land_floor,cost] clamp]; a recon proved the deferred "calibrate 600-900 yield cells" data-infeasible [0/187 usable villa cells at 600-900]; a 600-900 villa + a subject rent now income-LEADs [Marikh 54/541/6 default + rent 15k → income_led 2.7M, was widen_down]; value-invariant on live no-rent traffic [4 anchors byte-identical]; isolated 22/22 + DoD 392/15/45/broad 76; commit `731f864` split `c77302e`, CHANGELOG_v88)** · **2.22.0b.8 §6 v2 income OPEX alignment (Heroku v175, §20.42 — NOI opex now matches the calibration opex when the cap rate is calibrated [villa 0.20, was the flat 0.23] → closes the -3.75% villa-calibrated income understatement [income_led headline + displayed cross-check]; compound/fallback keep 0.23 byte-identical; value-invariant on live no-rent traffic [4 anchors byte-identical]; found PRE-BUILT in the tree by a parallel session, CC independently re-verified + re-measured DoD/E2E before push; isolated 19/19 + DoD 392/15/45/broad 77; live smoke income_led 2.7M→2.8M; commit `f01704b` split `7d1f7fa`, CHANGELOG_v89)** · **2.22.0b.9 QARS property-basis panel (Heroku v176, §20.43 — DISPLAY-ONLY / value-invariant: surfaces PIN + رقم الكهرباء + water + building-age FLOOR [from QARS `SURVEYED_DATE`] on every eval, zero new GIS; the age NEVER feeds `building_age_years` [no Gate-2]; 56/647/6 reproduces the Al Manara bank report TD 93317 LIVE; CHANGELOG_v90)** · **2.22.0b.10 geometric footprint (Heroku v177, §20.44 — DISPLAY/CONFIRM-only / value-invariant: max-buildable ground footprint from plot dims − legal R1 setbacks [5/3/3] bounded by the 60% coverage cap [edge-pairing on the 4-vertex ring, rotation-safe NOT bbox; non-rect → coverage cap; V001 56/647/6 5-vertex → cov-cap 391]; the footprint→BUA→headline wiring is the §20.9 cost-triangulation Gate-2; zero new GIS [reuses the plot polygon]; isolated 24/24 + DoD 392/15/45/broad 79 + R14 + live smoke v177 [3 villas byte-identical, 54/541/6 → 311]; framing F-1..F-4 Anas-signed; commit `c1c92fe` split `588a3b6`, CHANGELOG_v91)** · **2.22.0b.10.1 building-area on the confirm/basis review (Heroku v178, §20.44 follow-up — DISPLAY-only / value-invariant: the auto max-buildable building footprint now shows on Screen 2 (the confirm basis review) alongside plot area + PIN + electricity + age, closing a gap Anas caught [b10 had it on the results card + refine hint only]; aggregator 392 + R14 + live smoke v178 [54/541/6 5.4M byte-identical]; commit `f554900` split `09faac4`, CHANGELOG_v92)** · **2.22.0b.10.2 multi-QARS-aware geometry footprint (Heroku v179, §20.44 follow-up — DISPLAY-only / value-invariant: a villa on a SHARED 2+-villa parcel now gets the footprint of its per-villa share (effective_per_villa), not the whole cadastral parcel; 56/565/21 (900m² shared by 2 villas) 528→270 + «حصة الوحدة في قطعة مشتركة» disclosure; value byte-identical (2.4M — the value side already brackets on the effective share); Anas-caught; isolated 31/31 + DoD 392/15/45/broad 79 + R14 + live smoke v179; commit `e26680f` split `90a4efb`, CHANGELOG_v93)** · **2.22.0b.11 §20.9 Cost-Approach DRC down-re-anchor — SHIP-NOW slice (Heroku v180, §20.45 — 🔴 Gate-2 VALUE-AFFECTING, SIGNED «وقّع وانشر الآن»: an independent RICS DRC [land_floor + depreciated building, b9 SYSTEM age + b10 footprint × built-ratio 0.77] re-anchors a thin/widened OLD over-anchored villa DOWN with the COST as the informed floor [replaces §6 widen_down's bare land]; SHIP-NOW = the down-re-anchor ONLY [§11 Gate-2 SPLIT], precedence income_led > cost_reanchor > widen_down; b9 system age = a FLOOR → conservative/IMMUNE [V001 at 17 +22% no-fire, at actual 25 +30.6% would-fire]; age-gate ≥10, >30% undercut, MUC high, NO invented central; backend-only [api.py/index.html UNTOUCHED]; live smoke v180 Marikh 54/541/6 floor 1.9M→2.4M cost_reanchor_down [cost 2,378,094, undercut 128%], V001/Abu Hamour/apartment byte-identical; isolated 52/52 + DoD 392/15/45/broad 80 [broad caught + fixed a real a2.p9 precision regression]; commit `6e93d16` split `f7c3990`, CHANGELOG_v94)**. **§6 income-LEAD reach ✅ SHIPPED v174, opex-aligned ✅ SHIPPED v175; the geometric footprint ✅ SHIPPED v177–v179; the §20.9 SHIP-NOW down-re-anchor ✅ SHIPPED v180 [the durable R7 over-anchor fix, first slice]; the §20.9 GATED slice ✅ SHIPPED b13/v182 [Lever-1 convergent-TRIM, user-age-gated — V001+25y→3.6M = the certified-valuer figure; D-1 0.31 lux finish-floor ✅; **Lever-2 UP-lift DROPPED → B-2** per **E25** (V002/V003 sold ABOVE replacement cost → the under-anchor is a market premium, NOT cost-reachable); §20.47]; A15 ✅ CLOSED b12/v181 [HBU-not-evaluated disclosure, §20.46]. NEXT engineering = **§6 v2 remainder** [Fork C robustness + (ii) age-rent — **opex 0.20 ✅ SHIPPED b8/v175**] **OR B-2 condition axis** [the durable **under-anchor** fix — a calibrated `luxury_new` comparable stratum, R7/E25, PARKED **n≥20**] **OR the GT-collection track** [**D-3** — the binding decision now (RISK_SUMMARY §3); beta = a parallel non-blocking GT-collection track, **no cohort gate**, ISS-G03]. The live payoff of ALL income work stays UX-gated [income_led needs a subject rent → live no-rent Marikh/villa-6 stay widen_down]; **GT collection (D-3), not a "gate #6", is the binding unlock + rent source.** The v4 «thinnest-flow» UX remainder: (1) confirmation gate ✅ v169 · (2) range-as-lead ✅ v170 · **(3) condition-sensitivity** [B-2 PARKED n≥20] · (4) decomposition in the polished result + report refinement. **Beta
pre-use consent layer + source attribution are now LIVE → the free
invite-only villas/land beta is invite-ready (beta = a **parallel, non-blocking GT-collection track** — **no cohort gate** (ISS-G03); a24/a25 = the preserved R13 cover;
the **Aqarat enquiry is a pre-MONETIZATION gate** [held until design done; sent before paid access] — **not a
pre-invite blocker**; MoJ open-data licence gate ✅ CLOSED a25 — CC BY 4.0; in-beta feedback → Anas's WhatsApp
per the notice, so the in-app feedback UI [Sprint 2] is not required for the beta). Launch-gating canonical =
CLAUDE.md #65a.**

**PRIORITY QUEUE (confirmed-current — this is the authoritative "next"):**

|#|Item|What / why|Blocker|
|---|---|---|---|
|~~**1**~~|**A7 — `rics_compliant` honest status label** ✅ **SHIPPED a20** (Heroku v159, §20.20, CHANGELOG_v72)|DONE — neutral `rics_compliant_status_ar/en` («بانتظار مراجعة مُقيِّم مُرخّص (المرحلة الخامسة)» / "Pending licensed-valuer review (Stage 5)") added next to the bool on every JSON surface so bare `false` reads "review pending," not "non-compliant"; display/label only, zero value drift. Bool stays by-design (gated on `has_field_inspection`); field-rename NOT done (Rule #47 — its own pass if ever wanted). **A7 → CLOSED.**|—|
|**2**|**Sprint 2 — feedback UI prompt**|`index.html` (390×844) consuming `POST /api/feedback`, echoing the `valuation_id` already in the client JSON. Meaningful **at/after** a15 ACTIVATION.|a15 activation (#3)|
|**3**|**ACTIVATION of a15 instrumentation**|Flip the dormant capture/feedback live. Counsel-gated **§8.1 PDPPL** + **§8.2 cross-border** (RISK_REGISTER **R11**) **+** the a15 capture-surface **security pass** (`LAUNCH_READINESS_GATES_v1` gate 11). Then provision Postgres → `DATABASE_URL` + `EVAL_CAPTURE_ENABLED=true`.|counsel + security pass|
|~~**4**~~|**B — condition sprint · B-1 ✅ SHIPPED a21**|R7 built-type / **condition** axis. **B-1 SHIPPED** (Heroku v160, §20.21, CHANGELOG_v73) — land-floor / HBU decomposition + condition surfacing on every villa comparison output; presentation-only / value-invariant; **DISCLOSES** R7. **NEXT = B-2** (the durable fix — Stage-2 built-type/condition elicitation; B-1 discloses, **B-2 SOLVES**).|B-2 gated on 2.22.0b|
|**5**|**2.22.0b — 5-stage UX + Stage-2 elicitation**|Consumer value prop (staged Q&A; built-type/condition input). Gated on B.|B (#4)|
|~~**6**~~|**Cost-triangulation (independent DRC) — §20.9 ✅ PARTLY SHIPPED**|Own from-scratch DRC as a **secondary** method (§20.9 + `METHODOLOGY_DRC_qatar_v1.md`) — **NOT** the barred Mthamen API/formula (§20.8). **SHIPPED:** the **down-re-anchor** (b11/v180) + the **convergent-TRIM** (b13/v182, user-age-gated) = the R7 **over-anchor** half (D-1 0.31 lux floor ✅). **DROPPED:** the UP-lift (E25 — premium-above-cost, not cost-reachable) → the **under-anchor** half is **B-2** (`luxury_new` stratum, PARKED n≥20). **Remaining (minor, deferred):** the report two-values display (MV + forced-sale) + the soil/geotech v2 factor.|n≥20 (B-2) for the under-anchor; rest minor|

**Open mediums (backlog):** A5 (`asset_type unknown`) · ~~A15~~ (silent-HBU-drop ✅ CLOSED Sprint 2.22.0b.12 / v181, §20.46) ·
~~A16~~ (bracket area-name under-match = **R9 ✅ CLOSED a18, §20.18** — resolved-as-pool-fix; residual فريج العسيري ~0.25% → R7). **Open mediums now = A5 only.**

**Older detail table below — all verified UNSHIPPED (2026-06-01), kept, ordering SUPERSEDED:** behind-beta =
2.21.5 (hybrid UI), 2.21.4.1/.2 (data expansion), 2.21.3.2 (arady), 2.21.0.11/.12 (cosmetic), 2.18.2 (GIS
dedup), 2.17 (QARS snapshot), 2.20 (A8 grid — size R²≈0.05 + corner BLOCKED by E12); **villa Stage-2** =
**2.21.0.10** (wall-to-wall E18, footprint-probe-gated — was missing from the table below); **deferred-
indefinite** = 2.16.16 Confirmed Sales · Mthamen (§20.8) · MME apartments (tagged 2.21.1 / 2.29, auth).

### Older backlog detail (kept for reference; the Order column below is SUPERSEDED by the priority queue above)

|Order|Sprint|Description|Blocker|
|---|---|---|---|
|**1**|**2.21.5**|**UI tier breakdown + MUC surfacing for hybrid outputs.** Both 2.21.3 (T2) + 2.21.4 (T3) shipped → 2.21.5 is now UNBLOCKED. Owns rendering of `tier_breakdown.sources[]` (per-row T3 7-field shape: developer / project / status / value_per_m2_raw / discount_applied / value_per_m2_adjusted / freshness_status) + the H10 visual verification deferred from Sprint 2.21.4 H_WALK §5. Needs BRIEF from Claude.ai (lane discipline).|none|
|**2**|**2.21.4.1 / .2 / …**|**Data-only expansion Sprints** — add more developers/projects to `developer_inventory.sqlite` via CSV import (UDC Lusail Marina + Pearl, Qetaifan Islands, Qatari Diar, Msheireb, Dar Al-Arkan, etc.). Pure data Sprints — no code change. Workflow per `2p21p4_brief/README.md`.|developer inventory data availability|
|**3**|**2.21.3.2 candidate**|**arady connector** — deferred from Sprint 2.21.3 per BRIEF §12 single-purpose. arady detail content is JS-hydrated; sitemap.xml has only 5 category URLs. Two viable paths: (a) probe Next.js `__NEXT_DATA__` script tag for inline data; (b) headless-browser infrastructure (Playwright/Selenium). Decision via separate §5 audit.|design decision|
|**4**|**2.16.16**|**Confirmed Sales DB — DEFERRED INDEFINITELY (2026-05-30): NO viable internal source.** Both candidate feeds are closed — the secretary source (permanently, 2026-05-24) AND Anas's brokerage (Gardenia). Confirmed Sales is **not** a data source, dependency, or pillar. Do NOT re-add closed-feed framing (no broker-supplied pipeline; no awaiting-secretary dependency). Revive ONLY if a genuinely PIN-keyed T1 sale source ever appears (none exists; the MoJ `PN…` hash is permanently closed per Empirical E12). NOT a blocker for anything.|no viable source (both feeds closed)|
|**2**|**2.18.2 candidate**|**Lite/full GIS deduplication + boundary-test optimization** — closes Stage-1 (≤5s) gap for compound_small (the ~15s of non-parallelizable Python overhead remaining after Sprint 2.18.1.1's Patch A MoJ-skip). Three candidate optimizations: (a) lite/full GIS-call dedup, (b) `_polygons_share_boundary` via spatial index (e.g. shapely STRtree, kills ~882 pairwise tests), (c) async DCF/MoJ overlap with BFS prefetch. Decision via separate §5 audit.|none|
|3|**2.21.0.11 candidate** (cosmetic)|UX: deep-link rent input field from the "بيانات غير كافية" box when compound_large refuses for lack of income. Anas observation post-2.18.1.1 visual verification.|none|
|4|**2.21.0.12 candidate** (cosmetic)|UX: hide or replace "نطاق التفاوض المقترح" box when valuation=None (replace with "نطاق التفاوض غير متاح حتى تقديم الإيجار السنوي"). Anas observation post-2.18.1.1 visual verification.|none|
|5|2.17|QARS local snapshot|priorities post-Thursday|
|6|~~2.18~~|~~A6 latency + async landmarks + BUA-aware sanity~~ — **SUPERSEDED** by Sprint 2.18.0 (v99, CHANGELOG_v44) + 2.18.1 (v100, CHANGELOG_v45) + 2.18.1.1 (v101, CHANGELOG_v46). Original 2.18 was a bundle; split into single-purpose Sprints per Rule #38. **A6 latency CLOSED** as of 2.18.1.1 — wider cohort 0% HTTP failure across 21 reps.|—|
|7|2.20|A8 Comparable adjustments grid (full size + corner). Time-only grid shipped Sprint 2.20.0; size deferred (R²≈0.05); corner BLOCKED by E12.|design + confirmed sales|
|8|2.29|MME apartments integration|MME auth flow|

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

### 🟠 High: لا توجد. ✅ (A6 CLOSED Sprint 2.18.1, A8 CLOSED Sprint 2.20)

**A6 closure note (2026-05-24)**: Latency arc complete in 3 Sprints. (1) 2.18.0
Phase 1: parallel `property_factors` 5-layer fan-out → −4s villa/raw_land.
(2) 2.18.1: parallel BFS upfront-prefetch in `_expand_extent` → −60s
compound_small (89s→28.9s); HTTP 503×3 → 200×3 on 51/835/17 (THE WIN). Wider
21-rep cohort: 19% HTTP failure → 0%. (3) 2.18.1.1: Patches A+C close the
methodology bug that 2.18.1 unmasked (compound_small extent ≥ 15K m² →
promote to compound_large → clean Income Approach refusal). Stage-1 (≤5s)
for compound_small remains queued as Sprint 2.18.2 candidate.

### 🟡 Medium

|ID|Bug|Target|
|---|---|---|
|A5|`asset_type: unknown` بدون شرح|backlog|
|A7|`rics_compliant` دائماً false|backlog|
|A15|HBU silently dropped when the zoning hint is absent (reachable under QARS degradation) — `geometric_factors.py:638` + the consumer. **✅ CLOSED 2026-06-10 (Sprint 2.22.0b.12, Heroku v181, §20.46 / CHANGELOG_v95)** — `hbu_note_ar/en` discloses «HBU not evaluated» when the zoning layer is unavailable (value-invariant, villa/house, muted `.rn` near the value_floor).|CLOSED|
|A16|MoJ-bracket matcher under-matches: `apply_moj_strategy` n=1 vs geo_v2 n=42 for the SAME area+bracket (54/541/6) — مريخ ↔ امريخ الجنوبي alias/NBSP normalization gap. **✅ CLOSED 2026-06-03 (= RISK_REGISTER R9; Sprint 2.22.0a.18 `area_match_key` sibling-aggregation + امريخ الجنوبي→مريخ override, §20.18) — residual فريج العسيري ~0.25% → R7**|CLOSED|

### 🟢 Deferred

- BUA-aware sanity check → 2.18+
- Visual building assessment → 2.22+
- Per-stratum cap rate calibration → **لا مصدر داخلي صالح** (السكرتيرة + brokerage مغلقان) — مؤجَّل لأجل غير مسمى

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

`LANDS_CAP_RATE_PRIMARY = 0.04` محل شك. لا مصدر تحقّق داخلي (السكرتيرة + brokerage مغلقان) — يبقى تقديرياً حتى يظهر مصدر T1 مفتاحه PIN (لا يوجد).

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

### 🆕 20.9 Decision Log 2026-05-31 — بناء Cost Approach (DRC) مستقلّ خاصّ بنا

> **لا يلغي §20.8** ولا يغيّر شروط إحياء الـAPI الثلاثة (مذكورة صراحةً أدناه).

**التاريخ:** 2026-05-31 (الأحد)
**القرار:** نبني **Cost Approach (DRC) خاصّاً بنا** كـ**طريقة تقييم ثانية مستقلّة** — السوق يبقى أساسياً. هذا **مختلف جوهرياً** عن integration المثمن المؤجَّل في §20.8.
**البوّابة:** Hard Gate 2 (تغيير منهجي) — وافق عليه أنس (PO) اتجاهاً؛ التفاصيل والقرارات المفتوحة في سجلّ التصميم.

#### لماذا هذا ليس نقضاً لـ§20.8

1. **§20.8 أجّل استدعاء API لـ`sak.gov.qa`** (WAF block 6/6 · quota ~1/يوم · هشاشة بنية F5 ASM). أسبابه **كلّها عن الـAPI نفسه** — غير ذات صلة هنا: **لا نستدعي أيّ API.**
2. **لا نُعيد بناء معادلة المثمن المعكوسة** (9 طبقات أرض + 4 طبقات بناء — هيكلهم الخاصّ من الـAPK). نبني **DRC مستقلّاً من مدخلات عامّة**: أسعار أرض العدل + تكاليف بناء قطرية منشورة + منحنى إهلاك خاصّ بنا. وهذا **هيكل DRC المدرسي المعترَف به في RICS، لا ملكيتهم الفكرية.**
3. §20.4 و§20.7 **توقّعتا أصلاً استخدام المنهجية** ("valuer brief يشير لـCost Approach وفق منهجية المثمن/MoJ بدون استدعاء API"). هذا القرار **يُضفي الطابع الرسمي** عليها كمحرّك خاصّ بنا.

#### السند الإيجابي في RICS/IVS 2025 (ليس «مسموحاً» فقط — بل مُسانَد صراحةً)

- **IVS 104 (Data and Inputs — جديد 2025):** البيانات يجب أن تكون مكتملة (Complete). بيانات العدل **تفشل الاكتمال** (لا BUA · لا حالة · لا تشطيب) → **مُلزَمون** بطلب بيانات/مناهج مكمِّلة.
- **VPS 3 / IVS 103 (Approaches):** المثمّن يختار المناهج المناسبة ويوفّق بينها — سوق أساسي + تكلفة ثانوية = ممارسة أرثوذكسية.
- **VPS 5 / IVS 105 (Valuation Models — جديد):** مخرج الـAVM يُعدّ «تقييماً مكتوباً» فقط إذا طبّق مثمّن حكمه المهني عليه → **هذا هو دور مرحلتنا الخامسة (توقيع المثمّن المرخّص).**

#### ما الذي يبقى من §20.8 دون تغيير

**شروط إحياء integration المثمن الثلاثة تبقى نافذة كما هي:**
1. إثبات reachability لـ`sak.gov.qa` من Heroku (تشغيل `smoke_mthamen.py` + `smoke_mthamen_v2.py`).
2. إثبات تغيّر الـdaily quota بما يسمح بالاستخدام المهني (>10/يوم).
3. موافقة رسمية من MoJ Qatar (مفضّلة).

هذا الـaddendum **لا يحيي الـAPI** — يبني طريقة مستقلّة **بدلاً منه**. أيّ اقتراح لاحق باستدعاء `sak.gov.qa` لا يزال **يُرفض دون الشروط الثلاثة**.

#### التصميم الكامل

انظر `METHODOLOGY_cost_triangulation_v1.md` — تصميم التثليث (سوق أساسي + تكلفة ثانوية مستقلّة) + الطبقات المُتحقَّقة تجريبياً + الاستشهادات المُتحقَّقة من المصدر + انضباط المعايرة + القرارات المفتوحة.

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
|"تذكر إغلاق Confirmed Sales" | Sprint 2.16.16 مؤجَّل لأجل غير مسمى — لا مصدر داخلي صالح (مصدر السكرتيرة + brokerage/Gardenia مغلقان) |
|"راجع EMPIRICAL_FINDINGS" | قواعد E1-E7 |
|"اقرأ القسم X" | تفعيل self-correction trigger |

-----

*Bound to every Thammen session. Version-agnostic methodology reference — for current production state (engine / sprint / Heroku vN) see the CLAUDE.md production snapshot + `/api/health` (single source, Rule #58); for edit history see git log.*
