# CHANGELOG v200 — Sprint 2.22.0b.120 «أساس إعادة التصميم» (S0, redesign v2 foundation)

**Engine:** `thammen-sprint2p22p0b120-redesign-foundation` · **api-health:** `3.1.0-sprint2.22.0b.120`
**Files:** `index.html` · `api.py` · `evaluate_unified.py` (version lines) · `logo_t.png` (new) · `test_sprint_2_22_0b120.py` (new) · `test_sprint_2_22_0b104.py` (R6 re-point)
**Date:** 2026-07-10

🟢 **FRONTEND + one static route / VALUE-INVARIANT.** The valuation engine is untouched; `api.py` gains only one static asset route. No render function changed markup; no new value math. The 5-fixture byte-gate holds by construction.

---

## 2) لماذا يهمّ

مالك المنتج سلّم حزمة تصميمٍ عالية الدقّة (`design_handoff_thammen/` — 8 شاشات `.dc.html` + أصول + أجوبة مصمّم) لإعادة تصميم الواجهة، معالجةً لشكوى «ثابت، ممل، والتقارير مزدحمة». إعادة التصميم برنامجٌ من ~12 سبرنتاً (شاشةً بشاشة — 40 ملف اختبار يقفل 793 مقطعاً حرفياً، فالتسلسل ضرورة لا تفضيل). **S0** هو الأساس المشترك الذي تبني عليه كل الشاشات: رموز التصميم الناقصة، الشعار الشفّاف، وبدائيّات الحركة — دون أي تغييرٍ بصريّ للمستخدم.

## 3) الجذر

- **`--sh-lg` عيبٌ قائم:** مُستخدَم في `index.html:634` (`.lp-card:hover{box-shadow:var(--sh-lg)}`) لكنّه **غير معرَّف** في أي `:root` → القيمة تسقط والظلّ لا يظهر. (وثّقته خريطة الإنتاج §2.5.)
- **الرموز الجديدة ناقصة:** الكحليّ الأغمق للتذييل، الورقيّ الأغمق للوحة، الثانويّ، والسلّم النوعيّ السباعيّ — كلّها في النماذج inline، بلا مصدرٍ موحّد في الإنتاج.
- **`_srCountUp` مقفلٌ على `#srHeroNum`:** حركة تصاعد الرقم موجودة لكنّها خاصّة بالتقرير المختصر — الشاشات الجديدة (النتيجة، لحظة الكشف) تحتاجها عامّة.

## 4) ماذا يفعل هذا الـpatch

**backend (`api.py`):** مسار ثابت واحد `GET /logo_t.png` (يخدم الشعار الشفّاف؛ غير مُقيَّد المعدّل — نفس وضع `/logo.png`؛ اختبار الأمن يستثني الثوابت صراحةً). المحرّك و`/api/evaluate*` **لم يُلمسا**.

**frontend (`index.html`):**
1. **الرموز** في `:root` (س8، إضافةٌ للقائمة القائمة، بلا حذف): `--sh-lg` (يُصلِح العيب) · `--sh-hero` · `--navy-d:#0E2438` · `--paper-d:#E6DFD2` · `--text2:#5B6670` · `--ok2:#22C55E` + السلّم `--fs-12…--fs-52`.
2. **بدائيّات الحركة** (JS، عرضٌ محض): `_countUp(el,target,dur)` (تعميم `_srCountUp` — **تنتهي دائماً على `fmt(target)`**، لا على قيمةٍ محسوبة؛ reduced-motion يقفز للنهائيّ فوراً) + `_revealOnScroll(sel)` (IntersectionObserver؛ reduced-motion يُظهر الكلّ بلا مراقب). `_srCountUp` صار غلافاً رفيعاً حولها (DRY).
3. **CSS** لـ `.rv`/`.rv-in` (ظهورٌ عند التمرير، محروسٌ بـ `prefers-reduced-motion`).

**`logo_t.png`:** أصلٌ جديد (200KB، RGBA، شفافيّة ~94%) — الشعار بلا الصندوق الكريميّ الذي يظهر على الأسطح غير الكريميّة.

## 5) التحقّق — الدليل التجريبيّ

- **معزول** `test_sprint_2_22_0b120.py` = **42/42** (E14: يقرأ الملفّات الحقيقيّة — الرموز الثمانية · إصلاح `--sh-lg` · الشعار + المسار غير المُقيَّد · البدائيّتان + محايدة القيمة [تنتهي على `fmt(target)`] · `_srCountUp` غلافاً · صفر رياضيّة جديدة).
- **DoD:** المجمّع **395/395 MATCH** · الأمن **16/16** · صدق السطح **45/45** · **المشية العريضة 174/174 ALL GREEN**.
- **R6 re-point (Lesson-2):** `test_sprint_2_22_0b104.py` كان يثبّت البنية الداخليّة القديمة لـ `_srCountUp` (`const dur=800`, `el.textContent=fmt(target)`) التي انتقلت إلى `_countUp` → أُعيد توجيهه ليؤكّد **السلوك نفسه** عبر البنية الجديدة (~800ms · reduced-motion · easeOutCubic · `fmt(target)` النهائيّ). **صفر تأكيدات امتثال/قيمة/منهجيّة أُضعفت** — كل ضمانٍ سلوكيّ لا يزال مُثبَتاً. b104 = 20/20.
- **py_compile** (evaluate_unified.py + api.py) + **node --check** (JS المضمّن) = PASS.
- **R14 (Chromium 375×812، 7 حقن حقيقيّة):** كلفة `.en_gap_probe` · سوق `.q_abuhamour` · جغرافي `.b41_v001` · دخل `.b69_income` · أرض `.q_land` · رفض `.gate_refusal` · التقرير الكامل — **صفر أخطاء console · لا فيضان أفقيّ · القيمة مطابقة بايت** (2.4M/2.4M/3.8M/2.8M/7.1M/رفض) عبر كل حالات القيادة (matched/cost_led/geo_full/income_led/land) · «ليس تقييماً معتمداً» + MUC + CC BY 4.0 حاضرة · `.src-credit` تُستنسَخ في التقرير بنجاح.

## 6) النشر

```
git push origin master
git -C "C:/Thammen" subtree push --prefix "deploy v2" heroku master
```

## 7) تحقّق curl (بعد النشر)

```
curl -s -A "Mozilla/5.0" https://thammen.qa/api/health | findstr b120
curl -s -A "Mozilla/5.0" -I https://thammen.qa/logo_t.png | findstr "200"
```
+ بوّابة البايت الخماسيّة: 54/541/6=2.4M · 56/647/6=3.8M · 55/296/13=2.6M · 56/565/21=2.4M · 52/903/90=رفض.

## 8) ما ليس في هذا الـpatch (حدود النطاق)

- **لا تغيير بصريّ للمستخدم** — الرموز والبدائيّات أساسٌ للشاشات القادمة، لا تُستهلَك بعد. (الاستثناء الوحيد: ظلّ `.lp-card:hover` يظهر الآن بعد إصلاح `--sh-lg`.)
- الشاشات نفسها (الهبوط، النتيجة، التقارير، الإدخال، لحظة الكشف) = سبرنتات S1→S11 اللاحقة.
- بوابة الموافقة (S3، حجبٌ على قرار المالك) · نبض السوق `/api/pulse` (S2) · الإنجليزيّة (S11) · مواصفة ARIA (S10) — كلّها لاحقة.
