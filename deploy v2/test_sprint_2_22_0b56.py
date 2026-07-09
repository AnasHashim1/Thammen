# -*- coding: utf-8 -*-
# Sprint 2.22.0b.56 — «تشذيب اللغة والواجهة» (language + interface polish).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only).
# Reads the REAL index.html (E14 / Rule #40 for the frontend lane) + asserts the engine bump.
#
# The polish contract (PO directive: "نفذ الاصلاحات على التقرير المختصر والمفصل وعلى الواجهة"
# + the lawyer/أديب/لغوي language review + the gate/«العدل» screenshots):
#   GATE   — drop the beta sub-line + the «اعرف المزيد عن النسخة التجريبية» fold; the
#            «ما ليس هذا» + «غير منتسبة» disclosures MOVE to Terms (preserved, not lost).
#   HOME   — «العدل» reduced from the redundant repeats (hsub + step-2) → the two legitimate
#            credits kept (the hcred trust line + the engine recency line).
#   SHORT  — formal register: الزبدة→الخلاصة · سعر عادل→التقدير المركزي · وش لو→ماذا لو ·
#            شيت→كشف تقييم · «أخذ نصيبه»→«مُهلَك» · «لك وعليك» deleted.
#   FULL   — forced-sale label guarded + Arabic-Indic «×٠٫٩٠» + تشكيل.
#   VALUE-INVARIANT: copy/display only; the ×0.90 math + every figure untouched; NO
#   compliance line removed (relocated to Terms where moved).
import re, pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG  = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

# slices so report/gate assertions can't cross-match.
GATE = HTML[HTML.index('id="betaGate"'):HTML.index('English summary')]
SR   = HTML[HTML.index('function showShortReport(d){'):HTML.index('function show(d){')]
REP  = HTML[HTML.index('function showReport(d){'):HTML.index('function printReportA4(')]
TERMS= HTML[HTML.index('tmodal-body'):]

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── 1. GATE trim — beta sub-line + «اعرف المزيد» fold removed ──
check('beta sub-line removed', 'نسخة تجريبية مجّانيّة بالدعوة' not in HTML)
check('«اعرف المزيد» fold removed', 'اعرف المزيد عن النسخة التجريبية' not in HTML)
check('bg-more <details> removed', 'class="bg-more"' not in HTML)
check('gate dialog + consent affirmation KEPT (compliance)',
      'id="betaGate"' in HTML and 'وليست تقييماً معتمداً' in GATE and 'أُقرّ بأنني فهمت' in GATE)
check('gate CTA + Terms link KEPT', 'ackBeta()' in GATE and 'openTerms()' in GATE)
check('gate points to Terms for the full limits',
      'التفاصيل الكاملة وحدود الخدمة في «الشروط وإشعار الخصوصية»' in GATE)

# ── 2. Moved disclosures PRESERVED in Terms ──
check('«غير منتسبة لوزارة العدل» now in Terms (moved from gate)',
      'غير منتسبة لوزارة العدل' in TERMS and 'تستخدم بياناتها المفتوحة فقط' in TERMS)
check('coverage + condition limits preserved in Terms (AR)',
      'الفلل والأراضي فقط في هذه المرحلة' in TERMS and 'لا يأخذ بعدُ حالة العقار الداخلية' in TERMS)
check('coverage + not-affiliated preserved in Terms (EN)',
      'not affiliated with the Ministry of Justice' in TERMS and 'apartments and towers are not yet included' in TERMS)

# ── 3. HOME «العدل» reduced — redundant repeats dropped, legitimate credits kept ──
check('home hsub no longer «مبنيّ على بيانات وزارة العدل»',
      'class="hsub"' in HTML and 'تقييم سوقيّ آليّ للفلل والأراضي في قطر</div>' in HTML
      and 'مبنيّ على بيانات وزارة العدل المفتوحة</div>' not in HTML)  # b79: data-en attr added to the hsub tag
# b56 reduced the home «العدل» repeats: step-2 «نحلّل صفقات العدل» → «نحلّل الصفقات المسجّلة».
# b119 (PO-directed 2026-07-09) then removed the whole 3-step band from the simplified hero, so
# «العدل» is reduced even further. b56's REAL intent — no «صفقات العدل» repeat on home — survives.
check('home has no «نحلّل صفقات العدل» العدل-repeat (b56 reduction; b119 dropped the 3-step band)',
      'نحلّل صفقات العدل' not in HTML)
# b119 (PO-directed 2026-07-09): the credibility line is refined to a premium voice (drops the
# casual «— لا أسعار إعلانات») and stays the ONE legitimate «العدل» credit above the fold.
check('home MoJ credibility line KEPT (the one legitimate العدل credit, refined b119)',
      'استناداً إلى صفقات وزارة العدل المسجّلة.' in HTML)
# b119 (full marketing home): the home is now a full landing (data-sources + FAQ + footer +
# attribution) that legitimately DISCUSSES the open-data source — naming «وزارة العدل» is the
# credibility story, not the b56 minimal-home redundancy. The raw «≤N» count is obsolete for a
# marketing landing; b56's REAL intent survives as the ANTI-REDUNDANCY check below (the specific
# duplicated sentence/repeats it removed stay gone). R6/Lesson-2 re-point: count-cap → no-duplicate.
_homeBlock = HTML[HTML.index('id="homeScreen"'):HTML.index('id="formScreen"')]
check('home MoJ credibility line not duplicated (b56 anti-redundancy + b119 «مرة واحدة»)',
      _homeBlock.count('استناداً إلى صفقات وزارة العدل المسجّلة.') <= 1)

# ── 4. SHORT report — formal register ──
check('الزبدة → الخلاصة (head + §3 + legal caveat)',
      'الخلاصة في صفحة واحدة' in SR and 'الخلاصة العملية' in SR and 'الزبدة' not in SR)
check('§2 «سعر عادل» → «التقدير المركزي لبيتك اليوم»',
      'التقدير المركزي لبيتك اليوم' in SR and 'سعر عادل لبيتك' not in SR)
check('§6 «وش لو؟» → «ماذا لو؟»', 'ماذا لو؟' in SR and 'وش لو' not in SR)
check('neigh «أخذ نصيبه» → «مُهلَك» + «لك وعليك» dropped + «غير منصِفة»',
      'بعد إنقاص استهلاكه بحسب عمره' in SR and 'لك وعليك' not in SR  # b105 R6: owner surface softened «مُهلَكاً»→«بعد إنقاص استهلاكه»
      and 'أخذ نصيبه' not in SR and 'مقارنةٌ غير منصِفة' in SR)
check('شيت → كشف تقييم (land calibration line)',
      'كشوف تقييم موثَّقة محدودة' in SR and 'كلّ كشفٍ جديد يدقّقها' in SR
      and 'شيت' not in SR)

# ── 5. DETAILED report — forced-sale label guarded + Arabic-Indic ──
check('forced-sale row = guarded label + Arabic-Indic ×٠٫٩٠',
      'قيمة البيع الجبريّ الإرشاديّة (×٠٫٩٠ — ليست تصفية معتمدة)' in REP)
check('forced-sale note = «×٠٫٩٠» + تشكيل + «ليست تقييم تصفية معتمداً» kept',
      'قيمة بيعٍ جبريٍّ إرشاديّة (عُرفٌ سوقيٌّ ×٠٫٩٠) — ليست تقييم تصفية معتمداً.' in REP
      and 'الأساس: القيمة التقديريّة المركزيّة × ٠٫٩٠.' in REP)
check('old Latin «×<span dir="ltr">0.90</span>» label gone from the forced-sale row',
      '<span>قيمة البيع الجبري الإرشادية (×<span dir="ltr">0.90</span>)</span>' not in REP)

# ── 6. VALUE-INVARIANCE — the ×0.90 math + figures untouched ──
check('forced-sale math unchanged (display-only)', 'Math.round((v.amount||0)*0.90)' in REP)
check('no mutation of v.amount/v.low/v.high', not re.search(r'\bv\.(amount|low|high)\s*=[^=]', HTML))

# ── 7. COMPLIANCE / honesty UNTOUCHED on the results path (non-negotiable) ──
check('CC BY 4.0 MoJ attribution kept on results (legal mandate)',
      'CC BY 4.0' in HTML and 'creativecommons.org/licenses/by/4.0' in HTML)
check('«ليس تقييماً معتمداً» kept (results + report)', 'ليس تقييماً معتمداً' in HTML)
check('product identity «تقييم سوقيّ آليّ» kept (b54)', 'تقييم سوقيّ آليّ' in HTML)
check('b55 note-clusters still present (no regression)',
      'rep-cl-h' in HTML and 'حول الرقم' in REP)

# ── 8. Engine version (format only — R6 / Lesson-2: no exact pin) ──
check('ENGINE_VERSION format (thammen-sprint…)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('engine at/beyond b56 (b55 tag gone)', 'thammen-sprint2p22p0b55' not in ENG)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
