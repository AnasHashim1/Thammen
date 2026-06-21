# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.62 — «رشاقة المختصر صفحة١» (real short-report page-1 leanness).

PO authorized amending the signed PDF print contract («عدّل العقد») for real leanness.
The full report stays untouched (already lean b51/b55, long-by-design). Short-report
page-1 (cost-led, the densest): §٥ «أشياء قد ترفع الرقم» CARD → a one-line teaser (the
full upside table already lives in §٦ page-2 → drops duplicate figures); §٣ advice bars
COMPRESSED. KEEPS the SIGNED ceilings (×1.10/×1.30), «بيان وزارة العدل», «حسّن التقييم»,
«الإيجار أقوى معلومة», «ليس معتمداً». VALUE-INVARIANT (figures unchanged). Reads the REAL
index.html (E14).
"""
import io, re, sys

def load(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()

HTML = load('index.html')
EU   = load('evaluate_unified.py')
results = []
def check(name, cond): results.append((name, bool(cond)))

# ── §٣ compressed (tight labels in, verbose out) — SIGNED ceilings kept ──
check('§3 «◆ بائعاً:» tight',              '<b>◆ بائعاً:</b>' in HTML)
check('§3 «◆ مشترياً:» tight',             '<b>◆ مشترياً:</b>' in HTML)
check('§3 old «إن كنت بائعاً» gone',       'إن كنت بائعاً' not in HTML)
check('§3 header «الخلاصة العملية» kept',   'الخلاصة العملية' in HTML)
check('§3 ceiling +10% kept',              'سقف +10%' in HTML)
check('§3 ceiling +30% kept',              'فوق +30%' in HTML)
check('§3 ceiling math kept (×1.10/×1.30)', 'v.amount*1.10' in HTML and 'v.amount*1.30' in HTML)
check('§3 due-diligence «بيان وزارة العدل» kept', 'اطلب بيان وزارة العدل' in HTML)

# ── §٥ cost CARD → teaser (real page-1 leanness; full table stays in §٦) ──
check('§5 teaser «◆ قد يرتفع الرقم»',       '<b>◆ قد يرتفع الرقم:</b>' in HTML)
check('§5 old card header gone',           'أشياء قد ترفع الرقم — أخبرنا بها' not in HTML)
check('§5 keeps «الإيجار أقوى معلومة»',     'الإيجار أقوى معلومة' in HTML)
check('§5 keeps «حسّن التقييم» (GT invite)', 'حسّن التقييم' in HTML)
check('§5 points to «ماذا لو؟» (§6 table)',  'جدول «ماذا لو؟» بالأسفل' in HTML)
check('§5 dropped the orphan _scnBy const', '_scnBy' not in HTML)
check('§6 full scenarios table still present', 'جدول السيناريوهات — «ماذا لو؟»' in HTML)

# ── compliance / honesty kept ──
check('keeps «ليس تقييماً معتمداً»',        'ليس تقييماً معتمداً' in HTML)
check('keeps GT footer email',             'info@thammen.qa' in HTML)
check('keeps DEF-12 forced-sale ×0.90',    'v.amount*0.90' in HTML and 'ليست تقييم تصفية' in HTML)
check('keeps «لا أسعار إعلانات»',           'لا أسعار إعلانات' in HTML)

# ── full report UNTOUCHED (already lean) ──
check('full-report clusters intact',       'حول الرقم' in HTML and 'حول البيانات' in HTML and HTML.count('rep-cl-h') >= 1)

# ── version format ──
mv = re.search(r"ENGINE_VERSION\s*=\s*'(thammen-sprint[^']+)'", EU)
check('ENGINE_VERSION format', bool(mv) and mv.group(1).startswith('thammen-sprint'))
mt = re.search(r"SPRINT_TAG\s*=\s*'(\d+\.\d+\.\d+[a-z0-9.]*)'", EU)
check('SPRINT_TAG dotted-numeric', bool(mt))

passed = sum(1 for _, ok in results if ok); total = len(results)
for name, ok in results:
    print(('PASS' if ok else 'FAIL') + ' - ' + name)
print('\n%d/%d checks passed' % (passed, total))
sys.exit(0 if passed == total else 1)
