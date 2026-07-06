# CONSULT — Gemini r11 «وضوح المصطلح» (term clarity) — 2026-07-06

**Round:** r11. **Lane:** PO paste-lane (Chrome MCP). **Adjudication:** Rule #54 (locks + standards precision + honesty win).
**Applied in:** Sprint 2.22.0b.105 (R3 — the register lock). **Verdict:** 14 accept · 8 accept-modified · 5 reject.

## The prompt (two roles + owner archetype)
Gemini was asked as an Arabic UX-writer + plain-language financial editor to rate, for the non-technical
owner («أم خالد»): (Section A) 20 report terms — keep / keep+gloss / replace, with AR then EN wording; and
(Section B) 10 dev-plan phase names. Hard rules: locked terms (تقييم سوقيّ آليّ · ليس تقييماً معتمداً · منهج
المقارنة بالمبيعات · معدّل الرسملة) keep-only; RICS/IVS terms explained not replaced-with-anything-less-precise.

## Section A adjudication (report terms)

| Term | Gemini | CC verdict (#54) | Shipped (b105) |
|---|---|---|---|
| الحاضنة السعرية المدرّجة | replace → النطاق السعري التقديري | ACCEPT-MOD (must not collide with the locked «النطاق التقديري السوقي») | deferred to a b92-face pass (not in b105) |
| مرتكز الكلفة (أرض + بناء مُهلَك) | replace → التكلفة الأساسية | GLOSS-ONLY — «مرتكز» is PO-signed «بطل العقد» | KEPT + owner gloss softened «مُهلَك» |
| **التحفظ المادي: متوسط/مرتفع** | replace → عدم اليقين الجوهري + gloss | **ACCEPT (PO-signed)** | **«عدم اليقين الجوهري» — banner + chip + clause + notes** |
| الوسيط (التقدير المركزي) | keep+gloss → الوسيط السعري | ACCEPT-MOD | deferred (a face/label pass) |
| التشتّت | replace → تفاوت الأسعار (owner) | ACCEPT owner-surface-only (specialist annex keeps التشتّت) | deferred (owner §٨ pass) |
| كلفة الإحلال | keep+gloss | KEEP + gloss «(كلفة بنائه جديداً اليوم)» | deferred gloss (term kept) |
| **معامل الاحتفاظ** | replace → نسبة القيمة المتبقية للبناء | **ACCEPT** | **«نسبة القيمة المتبقية للبناء»** |
| **البناء المُهلَك** | replace → قيمة البناء الحالية | **ACCEPT owner-only (PO-signed register split)** | **owner short report softened; specialist keeps «مُهلَك»** |
| قيمة البيع الجبريّ | keep+gloss; «القسري» | GLOSS-ONLY — «الجبريّ» b56-signed; «القسري» REJECTED | KEPT |
| **حوض المقارنة الموسَّع** | replace → نطاق البحث الجغرافي | **ACCEPT-MOD → نطاق المقارنة الموسَّع** (keep «المقارنة») | **«نطاق المقارنة الموسَّع جغرافياً»** |
| شريحة مساحتك | replace → فئة | **REJECT** — locked lexicon (size brackets + b100 strata; rated clear) | KEPT «شريحة» |
| بصمة المحتوى | replace → الرمز الأمني | **REJECT** — «رمز أمني» misleading (it is tamper-evidence) | KEPT + gloss planned |
| **الاستخدام الأمثل** | keep+gloss → الأفضل والأعلى | **ACCEPT → أعلى وأفضل استخدام** (RICS HBU order) | **«أعلى وأفضل استخدام»** |
| مساحة البناء BUA | keep | KEEP | KEPT |
| **نافذة 36 شهراً** | replace → الإطار الزمني | **ACCEPT-MOD → صفقات آخر 36 شهراً** | **«صفقات آخر 36/24 شهراً»** |
| **مؤشّر مزامنة البيانات** | replace → تاريخ تحديث بيانات وزارة العدل | **ACCEPT-MOD (avoid double «وزارة العدل»)** | **«تاريخ تحديث بيانات وزارة العدل: آخر سجلّ رسميّ»** |
| سجلّ العناوين (QARS) | «نظام» | **REJECT** — rated clear; no gain | KEPT |
| الشريحة الأعلى/المتوسطة/قريبة | keep | KEEP | KEPT |
| استرشاديّ | keep | KEEP | KEPT |
| صفقات مسجّلة vs أسعار إعلانات | keep | KEEP | KEPT |
| معدّل الرسملة (gloss) | Gemini gloss | **REJECT gloss** — OURS keeps «صافي» + Qatar 5–6% (b61) | KEPT ours |

**Accepted additions (Gemini):** تاريخ التقييم vs تاريخ الفحص distinction (→ S1 R-2; note: we have NO inspection
date — disclose that) · «العمر الاقتصادي المتبقي» gloss · «التهالك المادي» plain rendering (→ S3 depreciation
disclosure).

## Section B (dev-plan phase names) — ACCEPTED wholesale → the plan-naming lexicon
21 «إصلاح 3 أخطاء في واجهة العرض» · 22 «توحيد قسم الافتراضات في صفحة واحدة» · 23 «توحيد معايير النطاق الجغرافي
لصفقات الأراضي» · 24 «ضبط مؤشر اتجاه الأسعار ليقتصر على مبيعات الفلل» · 25 «نافذة أسئلة حالة العقار (الرقم يتكيف
مع الحالة)» · 26 «شاشة عرض نتيجة التقييم (البطاقة المختصرة)» · 27 «توحيد وتثبيت لغة التطبيق» · 28 «استكمال
متطلبات معايير RICS في نموذج التقرير» · 29 «إصدار وثيقة التقييم المهنية الكاملة (PDF)» · 30 «تحديث تقني لا
يؤثر على قيمة التقييم النهائية».

## Deferred from b105 (own passes)
The owner-surface glosses (الوسيط/التشتّت/كلفة الإحلال/بصمة المحتوى/الحاضنة) + the S1 tar-adjacent items (basis
date, inspection-date distinction) — b105 shipped the SIGNED items (MUC + مُهلَك) + the clean replaces; the
glosses ride the S1 RICS-disclosure sprint or a later face pass.
