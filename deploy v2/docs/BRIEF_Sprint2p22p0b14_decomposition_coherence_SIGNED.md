# BRIEF — Sprint 2.22.0b.14 — Decomposition coherence + report-voice reconciliation (ISS-A07)

> **Gate-2: SIGNED BY DELEGATION («افعل الأصوب», Anas, 2026-06-10 — D-6).** Gate-1: deploy-on-green.
> **VALUE-INVARIANT** — amounts/ranges/methods/floors NEVER move; only DESIGNATED TEXT fields change (whitelist §4).
> **Evidence (measured✓ live, 2026-06-10, b13/v182, Marikh 54/541/6 buyer):** the report contradicts itself —
> decomposition says building = 65.1% «يتسق مع بناء جديد أو فاخر» while the 10-Year panel (same page) says the
> 17y property «يتداول قرب قيمة الأرض» and location-features marks «✗ بناء قديم نسبياً»; the strata card shows the
> pool dominated by فاخر/حديث 51.7% (the R7 over-anchor made visible). Plus three copy leaks (§3).
> **Baseline:** b13/v182. **Authority:** ISS-A07 + this live probe + DESIGN_2p2x_v4 (§2c: explanation ≠ confidence).

## §1 — Principle

The implied-building residual (`central − land`) **inherits** any R7 over-anchor; the narrative must therefore
**never rationalize** a high building share as real building value when the evidence says otherwise — it must
*explain the gap honestly* (pool-stratum premium) and **agree with the 10-Year panel**. One report, one voice.

## §2 — The narrative decision table (the core fix)

Inputs already in the output: `stock_strata` (dominant stratum + share), `building_age_estimate`
(sys age + b13 `age_basis=vintage_capped`), the 10-Year-rule applied flag, user condition/finish inputs.
Select the implied-building narrative:

| Case | Condition | Verbatim AR narrative |
|---|---|---|
| **A — old subject, premium-dominated pool** (the Marikh case) | (age>10 OR vintage_capped) AND dominant stratum ∈ {فاخر/حديث, بناء حديث جيد} AND no user luxury/new/renovated input | «النسبة المرتفعة للبناء الضمني (X%) تعكس وسيط منطقةٍ تهيمن عليه فئة «{الفئة المسيطرة}» ({share}% من العيّنة) — **لا قيمةَ بناءٍ فعليّة لعقارٍ بهذا العمر**؛ يتّسق هذا مع قاعدة الـ10 سنوات أدناه. إن كان عقارك بتشطيب فاخر فعليّ، اختر «بناء فاخر» وأعد التقدير.» |
| **B — genuinely new/luxury** | user `new`/`luxury`/`renovated` OR sys_age<5 (non-re-survey) | the current line stays: «يتسق مع بناء جديد أو فاخر أو ذو BUA كبيرة.» |
| **C — neutral/middle** | otherwise | «البناء الضمني محسوب كفرقٍ عن قيمة الأرض — وهو **حدّ أعلى استدلاليّ** لا قياس مباشر لقيمة البناء.» |

Plus: the 10-Year panel and the decomposition must reference each other (one cross-line each), and the
decomposition **basis must equal the page's central** (live shows 1,851,260+3,448,740=5,300,000 vs headline
5,400,000 — Phase-0 finds the basis divergence and unifies; the % recomputes from the unified basis).

## §3 — The three copy leaks (all confirmed live)

1. **Service-charge MUC factor on a standalone villa** («رسوم الخدمات تقديرية — ليست متحقَّقة لهذا المبنى»):
   villa/house → replace with «مصاريف تشغيل تقديريّة ضمن الفحص الدخليّ» OR drop the factor line for
   non-strata assets — Phase-0 locates the factor builder and picks the minimal edit.
2. **Cap-rate source label** («معدل رسملة 5.16% … لنفس المنطقة والشريحة», n=46): the 5.16/n=46 calibrated cell
   is the **400-600** cell; the subject (613م²) is **600-900**. Phase-0 verifies which cell the panel consumed:
   if borrowed/neighboring → the label must disclose it: «معايَر من الشريحة المجاورة (400-600) لنفس المنطقة —
   استعارة مُفصَح عنها»; if genuinely same-bracket → leave + document. NEVER claim same-bracket when borrowed.
3. **Ad-description empty state on an address evaluation** (PDF: «لم يُكتشف أي علم… في وصف الإعلان (لم يُقدَّم
   وصف)»): when no listing/description exists → «لا يوجد إعلان مرتبط بهذا التقييم — التحليل على العنوان مباشرةً»
   (or suppress the panel). Phase-0 locates whether it's backend copy or frontend empty-state.

## §4 — Value-invariance contract (the test's whitelist)

May change (TEXT ONLY): decomposition narrative + its cross-line · 10-Year panel cross-line · the MUC
service-charge factor line · cap-rate source label · the ad-empty-state line. **Must stay byte-identical:**
`amount`, `range_*`, `method`, `value_floor`, all floors/levers, strata numbers, cap-rate VALUE, land value,
implied-building VALUE (only its % if the basis unifies — if unification changes the displayed %, report it
at Gate-3 BEFORE shipping). All 4 anchors + V001: numeric fields identical; text diffs ⊆ the whitelist.

## §5 — Phase-0 recon FIRST (HALT on premise break)

Locate: the decomposition builder + its basis (the 5.3M vs 5.4M divergence) · the narrative template site ·
the MUC factor builder (service charges) · the cap-rate panel's consumed cell + the b7 borrow flag · the
ad-description panel source · the render sites (results + report). Deliver `PHASE0_2p22p0b14_coherence.md`.

## §6 — DoD (EXECUTED)

py_compile · isolated ≥20 (table cases A/B/C + Marikh-case selection + leak fixes + whitelist contract) ·
aggregator/security/surface + broad (82 baseline) · local E2E: 4 anchors + V001 numeric-identical, Marikh
narrative = case A verbatim · **R14 Chromium 390×844** (new copy renders, 0 console errors, no overflow) ·
live smoke post-deploy (numeric-identical + case-A text live) · `heroku auth:whoami` pre-push ·
CHANGELOG_v97 · Session_Log §20.48 · ENGINE_VERSION → b14.

## §7 — NOT in scope
Any value/method change (R7 central stays — that is B-2's job) · two-values display (DEF-12, screen-5) ·
strata thresholds · apartment surfaces.
