# -*- coding: utf-8 -*-
# Sprint 2.22.0b.54 — «تقدير» → «تقييم» identity/process term-lock (PO-signed).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only).
# Reads the REAL index.html (E14 / Rule #40 for the frontend lane) + asserts the engine bump.
#
# The term-lock contract (PO directive):
#   - PRODUCT IDENTITY + the PROCESS of producing it = «تقييم» (flipped FROM «تقدير»).
#   - The resulting VALUE / RANGE the tool gives = STAYS «تقديريّ» (honestly an *estimated* value).
#   - Purely TECHNICAL estimates = STAY «تقدير».
#   - HARD INVARIANTS (untouched): «ليس تقييماً معتمداً» / «تقييماً رسمياً» distinction lines;
#     «وزارة العدل» mentions + the CC BY 4.0 source credit.
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# ── 1. NEW identity/process strings PRESENT + their OLD «تقدير» form ABSENT ──
check('gate title flipped → تقييم سوقيّ آليّ (old absent)',
      'ثمّن — تقييم سوقيّ آليّ للفلل والأراضي في قطر' in HTML
      and 'ثمّن — تقدير سوقي آلي للفلل والأراضي في قطر' not in HTML)
check('«ما هذا؟» gate card removed (b56 gate trim) — old «تقدير سوقي آلي» identity still absent',
      'ما هذا؟</strong> تقييم سوقيّ آليّ مبني على' not in HTML  # b56: the bg-more fold removed
      and 'ما هذا؟</strong> تقدير سوقي آلي مبني على' not in HTML)  # b54 lock holds
check('consent affirmation → ثمّن تقييم سوقيّ آليّ للدعم (old absent)',
      'أن ثمّن تقييم سوقيّ آليّ للدعم وليس تقييماً معتمداً' in HTML
      and 'أن ثمّن تقدير سوقي آلي للدعم' not in HTML)
check('home htag → تقييم عقارك في قطر (old absent)',
      'class="htag"' in HTML and 'تقييم عقارك في قطر</div>' in HTML
      and 'تقدير عقارك في قطر' not in HTML)  # b79: data-en attr added to the htag tag
check('share line → تقييم سوقيّ آليّ، وليس تقييماً معتمداً (old absent)',
      "'تقييم سوقيّ آليّ، وليس تقييماً معتمداً.'" in HTML
      and "'تقدير سوقيّ آليّ، وليس تقييماً معتمداً.'" not in HTML)
check('report brand → تقييم سوقيّ آليّ للعقار locked (b81: now wired in t(); old تقدير absent)',
      "t(' — تقييم سوقيّ آليّ للعقار',' — Automated market property valuation')" in HTML
      and ' — تقدير سوقي آليّ للعقار' not in HTML)
check('report footer pin-line → تقييم سوقيّ آليّ وليس تقييماً معتمداً locked (b81: in t(); old تقدير absent)',
      "t('تقييم سوقيّ آليّ وليس تقييماً معتمداً'," in HTML
      and 'تقدير سوقي آلي وليس تقييماً معتمداً' not in HTML)
check('short-report subhead → تقييم سوقيّ آليّ · ليس تقييماً معتمداً (old absent)',
      'تقييم سوقيّ آليّ · ليس تقييماً معتمداً' in HTML  # b80 R6: subhead literal now the t() first-arg (no longer bare in <small>)
      and 'تقدير سوقي آلي · ليس تقييماً معتمداً' not in HTML)
check('short-report micro b → تقييم سوقيّ آليّ + ليصير تقييمنا (old absent)',
      '<b>تقييم سوقيّ آليّ وليس تقييماً معتمداً</b>' in HTML
      and 'ليصير تقييمنا أدقّ للجميع' in HTML
      and '<b>تقدير سوقي آلي وليس تقييماً معتمداً</b>' not in HTML)
check('result not-certified line → تقييم سوقيّ آليّ — ليس تقييماً معتمداً (old absent)',
      "</use></svg> '+t('تقييم سوقيّ آليّ — ليس تقييماً معتمداً" in HTML
      and 'تقدير سوقيّ آليّ — ليس تقييماً معتمداً' not in HTML)
check('terms intro → ثمّن تقييم سوقيّ آليّ للفلل والأراضي (old absent)',
      '<p>ثمّن تقييم سوقيّ آليّ للفلل والأراضي مبني على' in HTML
      and '<p>ثمّن تقدير سوقي آلي للفلل والأراضي مبني على' not in HTML)
check('EN terms → automated market valuation (old estimate-phrase absent)',
      'Thammen is an automated market valuation for villas and land' in HTML
      and 'Thammen is an automated market estimate for villas and land' not in HTML)
check('top-bar status → نتيجة التقييم السوقي (old absent)',
      'نتيجة التقييم السوقي</div>' in HTML
      and 'نتيجة التقدير السوقي' not in HTML)  # b79: data-en attr added to the tbar-st tag
check('hero label → التقييم السوقي (old absent)',
      '<span class="lbl">\'+t(\'التقييم السوقي\',\'Market valuation\')+\'</span>' in HTML
      and '<span class="lbl">التقدير السوقي</span>' not in HTML)
check('share value line → قيمة التقييم السوقي (old absent)',
      "'قيمة التقييم السوقي: '+fmt(v.amount)" in HTML
      and "'قيمة التقدير السوقي: '+fmt(v.amount)" not in HTML)
check('home CTA → ابدأ التقييم (old absent)',
      '>ابدأ التقييم</button>' in HTML and '>ابدأ التقدير</button>' not in HTML)
check('refine top-bar → تحسين التقييم (old absent)',
      'تحسين التقييم</div>' in HTML
      and 'تحسين التقدير' not in HTML)  # b79: data-en attr added to the tbar-st tag
check('refine submit → احسب التقييم المُحسَّن (old absent)',
      '>احسب التقييم المُحسَّن</button>' in HTML
      and '>احسب التقدير المُحسَّن</button>' not in HTML)
check('refine spinner → جاري تحسين التقييم (old absent)',
      "'جاري تحسين التقييم...'" in HTML and "'جاري تحسين التقدير...'" not in HTML)
check('home footer disclaimer → هذا التقييم السوقيّ الآليّ إرشاديّ (old absent)',
      'هذا التقييم السوقيّ الآليّ إرشاديّ ومبنيّ على بيانات وزارة العدل المتاحة للعموم.' in HTML
      and 'هذا التقدير إرشاديّ ومبنيّ على بيانات وزارة العدل المتاحة للعموم.' not in HTML)
check('refine group tag → يحرّك التقييم (old absent)',
      '<span class="tagfx move">يحرّك التقييم</span>' in HTML
      and '<span class="tagfx move">يحرّك التقدير</span>' not in HTML)
check('refine-feature name → حسّن التقييم (rendered, old rendered absent)',
      'حسّن التقييم — أضف تفاصيل مبناك' in HTML
      and 'حسّن التقييم (المرحلة 2)' in HTML
      and 'زر «حسّن التقييم» في الموقع' in HTML
      and 'حسّن التقدير — أضف تفاصيل مبناك' not in HTML
      and 'حسّن التقدير (المرحلة 2)' not in HTML)

# ── 1b. consent gate + Terms modal — the 5 product/process spots (adversarial-verify catch) ──
check('condition-limit moved gate→Terms (b56) — «تقييم» wording, old «تقدير» absent',
      'لا يأخذ بعدُ حالة العقار الداخلية' in HTML  # b56: gate «حدود» bullet relocated to Terms §2
      and 'والتقدير لا يأخذ بعد حالة العقار الداخلية' not in HTML)  # b54 lock holds
check('gate «دورك» bullet removed (b56 gate trim) — old «جرّب التقدير» still absent',
      'جرّب التقييم، وشاركنا' not in HTML and 'جرّب التقدير، وشاركنا' not in HTML)
check('Terms §1 reworded by b58 (beta framing dropped) — old «تقدير» still absent',
      'هذه خدمة مجانية. باستخدامك' in HTML  # b58: «نسخة تجريبية مجانية بالدعوة لقياس دقّة التقييم» → «خدمة مجانية»
      and 'بالدعوة لقياس دقّة التقدير. باستخدامك' not in HTML)  # b54 terminology lock holds
check('Terms §4 → دقّة التقييم (old absent)',
      'لقياس وتحسين دقّة التقييم — لا تُباع' in HTML
      and 'لقياس وتحسين دقّة التقدير — لا تُباع' not in HTML)
check('Terms §5 disclaimer → التقييم لأغراض الدعم (old absent)',
      '<p>التقييم لأغراض الدعم والمعلومة فقط' in HTML
      and '<p>التقدير لأغراض الدعم والمعلومة فقط' not in HTML)

# ── 2. KEEP-list — the VALUE/RANGE + technical estimates STAY «تقدير» ──
check('range-as-lead value term STAYS — النطاق التقديري السوقي', 'النطاق التقديري السوقي' in HTML)
check('central-estimate value term STAYS — الوسيط (التقدير المركزي)', 'الوسيط (التقدير المركزي)' in HTML)
check('value adjective STAYS — القيمة التقديرية', 'القيمة التقديرية' in HTML)
check('short-report hero value term STAYS «تقديريّ» (b90 neutralized the label → «القيمة السوقية التقديرية»)', 'القيمة السوقية التقديرية' in HTML)
check('short-report pill STAYS — تقدير استرشادي', 'تقدير استرشادي' in HTML)
check('technical estimate STAYS — مساحة البناء الأرضي (تقدير أقصى)', 'مساحة البناء الأرضي (تقدير أقصى)' in HTML)
check('technical estimate STAYS — تقدير مبدئي', 'تقدير مبدئي' in HTML)
check('technical estimate STAYS — تقديراً موثوقاً (refusal)', 'تقديراً موثوقاً' in HTML)
check('tier label STAYS — تقدير إرشادي', 'تقدير إرشادي' in HTML)

# ── 3. HARD INVARIANTS — distinction lines + source credit untouched ──
check('«ليس تقييماً معتمداً» distinction PRESENT', 'ليس تقييماً معتمداً' in HTML)
check('«تقييماً رسمياً» distinction PRESENT', 'تقييماً رسمياً' in HTML)
check('وزارة العدل source PRESENT', 'وزارة العدل' in HTML)
check('CC BY 4.0 source credit PRESENT', 'CC BY 4.0' in HTML)

# ── 4. VALUE-INVARIANCE — no mutation of v.amount/v.low/v.high in index.html ──
check('no mutation of v.amount/v.low/v.high', not re.search(r'\bv\.(amount|low|high)\s*=[^=]', HTML))

# ── 5. Engine version (format only — R6 / Lesson-2: no exact pin) ──
check('ENGINE_VERSION format (thammen-sprint…)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format',
      re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('engine at/beyond b54 (b52 tag gone)', 'thammen-sprint2p22p0b52' not in ENG)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
