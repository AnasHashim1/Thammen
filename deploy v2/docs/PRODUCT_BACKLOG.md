# PRODUCT_BACKLOG — Thammen (الفهرس المرتّب الواحد)

> **ما هذا:** قائمة **واحدة مرتّبة** (Scrum Product Backlog) تجمع شظايا الـbacklog المبعثرة في فهرس واحد.
> أُنشئ 2026-06-14 (تدقيق Agile) لإغلاق ثغرة «الـbacklog مجزّأ عبر §11 + §4ب + RISK + NEXT».
>
> **⚠️ هذا فهرس/عرض — ليس مصدر الحالة الحيّة.** الحالة الحيّة لكلّ sprint + الخطوة التالية الفعليّة =
> **`CLAUDE.md` «⚡ LIVE NOW» + `Session_Log §20.x`** (Rule #58 — الحيّ/المقيس يفوز). هذه الصفحة **تربط**
> الأجزاء بسطر واحد لكلّ بند ولا **تكرّر** التفاصيل المتغيّرة (حتى لا تصير شظيّة رابعة تنجرف). عند التعارض:
> `/api/health` الحيّ + `CLAUDE.md` يفوزان.
>
> **الحيّ الآن:** b40 / Heroku **v211** / `master==origin @9cb4887` (2026-06-14).

## Product Goal
إطلاق **بيتا مدعوّة** (فلل + أرض) لـ AVM صادق وفق RICS Red Book 2025 — يصل لرقم قابل للدفاع + يكشف أدلّته،
ويُفعّل حلقة تغذية راجعة حقيقيّة (GT) تُحرّك الدقّة. **القيد الحاكم = قرار الإطلاق/جمع-GT (D-3).**

## القائمة المرتّبة (أعلى قيمة أولاً)

| # | البند | النوع / البوّابة | الحالة | التفصيل يعيش في |
|---|---|---|---|---|
| **1** | **إطلاق البيتا المدعوّة + بدء جمع GT (D-3)** — حلقة المستخدم الحقيقيّ؛ كلّ تحسينات الدقّة محجوبة على بيانات لا يُنتجها إلا الإطلاق | 🔴 **قرار PO** (ليس sprint هندسيًّا) | **مفتوح — القيد** | `BETA_LAUNCH_PLAN_v1.md` · `LAUNCH_READINESS_GATES_v1.md` · `GT_INTAKE_KIT_v1.md` · CLAUDE.md #65a |
| **2** | **b41 — صفوف الجيران الجغرافيّة** (شقيقة §20.70 «الحوض الجغرافيّ الكامل»: `accepted_areas` بعمود اسم منطقة + ×تعديل) | 🟢 frontend/value-invariant (deploy-on-green) | NEXT (الشريحة 🟢 المتبقّية) | `PHASE0_DEF_UX1.2_keystone_enrichment_recon.md` §3 · CLAUDE.md «⚡ LIVE NOW» |
| **3** | **DEF-UX8 — حواجز القدرة/LTV** على حاسبة b35 | 🟡 NET-NEW (يحتاج مدخل دخل + قرار منتج) | مؤجَّل | `ISSUES_LOG §4ب-2` |
| **4** | **بنود §4ب الخفيفة** — UX4 (بانر حداثة + slider) · UX6 (delta التحسين) | 🟢/🟡 display | مؤجَّل | `ISSUES_LOG §4ب` |
| **5** | **مسار الدقّة (R7)** — B-2 (طبقة `luxury_new` المعايَرة) · §6 v2 (Fork C + age-rent) | 🔴 Gate-2 | **PARKED على n≥20 موثَّقة** (مفكوك بالبند #1) | `BRIEF_SprintB2_*_SIGNED.md` · `RISK_REGISTER` R7/E25 |
| **6** | **تفعيل الالتقاط a15 (D-2)** — feedback UI + الالتقاط الخامل → حيّ | 🔴 counsel + gate-11 | مؤجَّل (مفكوك بالبند #1) | `RISK_REGISTER` R11 · `DPIA_AI_impact_beta_v1.md` |
| **7** | **DEF-UX5 — توطين EN** | 🔴 مشروع Gate-2 (ليس شريحة 🟢) | مؤجَّل | `PHASE0_DEF_UX5_en_toggle_recon.md` |
| **8** | **«بوابة بيانات الأنواع»** — compound GAI · buildings value_stack/leadership · types-tab · buildings cap-rate | 🔴 كلّ منها Gate-2 | مؤجَّل (بيانات الأنواع) | `ISSUES_LOG` (بوابة الأنواع) · `PHASE0_income_types_exposure.md` |
| **9** | **DEF-UX15 — autocomplete** | محجوب | BLOCKED (تفريغ QARS) | `ISSUES_LOG §4ب-2` |
| — | **deferred-indefinite** — Confirmed Sales (لا مصدر) · Mthamen (§20.8) · MME apartments (auth) · 2.21.5 hybrid UI | — | deferred-indefinite | `Project_Instructions §11` |

## أين تعيش شظايا الـbacklog (خريطة الفهرس)
- **الـbacklog الاستراتيجيّ/المؤجَّل + behind-beta + deferred-indefinite** → `Project_Instructions §11` (مرجع، يتأخّر عن الحيّ).
- **شخصيّات §4ب (DEF-UX*) + أخطاء A-ids + بوابة الأنواع** → `ISSUES_LOG.md`.
- **المخاطر (R-ids) + KRI + الخريطة الحراريّة** → `RISK_REGISTER.md` (كامل) + `RISK_SUMMARY.md` (حيّ).
- **بوّابات الإطلاق + خطّة البيتا** → `LAUNCH_READINESS_GATES_v1.md` + `BETA_LAUNCH_PLAN_v1.md`.
- **الخطوة التالية الحيّة لكلّ sprint** → `CLAUDE.md` «⚡ LIVE NOW» + `Session_Log §20.x` (المصدر الحيّ).

## الصيانة
يُحدَّث عند تغيّر **الترتيب/الأولويّة** (قرار PO) أو إغلاق/إضافة بند — لا عند كلّ sprint (الحالة الحيّة في CLAUDE.md).
الترتيب أعلاه = توصية تدقيق Agile (2026-06-14): القيد #1 = الإطلاق؛ الفريق يشحن #2 بينما #1 قرار PO.
