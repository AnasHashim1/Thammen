# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.137 (S11, redesign v2) — «ملء إنجليزيّة شاشتي الإدخال والتحسين».

E14: reads the REAL index.html + evaluate_unified.py.

Scope (measured, R-B): the t() layer is complete (757 two-arm, 0 real single-arm);
pulse (b134) + rs-cond (b135) + home/gate (b79) are fully EN. The remaining EN gaps
were the two v2 screens b79/the live layer never reached:
  1. formScreen .ent-type had data-en on the PARENT (innerHTML=data-en would wipe
     the svg + .etn + .etm in EN) → moved to .etn.
  2. refineScreen static text lacked data-en (~30 strings) → added.
  3. rentalIncomeLabel dynamic label (applyAssetToForm) → t().
  4. #refineScreen missing from body.lang-en LTR overrides → added.

VALUE-NEUTRAL: api.py + engine untouched (2 version lines only); translation only.
"""
import io, re, sys
sys.stdout.reconfigure(encoding='utf-8')

HTML = io.open("index.html", encoding="utf-8").read()
ENG  = io.open("evaluate_unified.py", encoding="utf-8").read()

# slice the two screens so "present" checks are scoped
def _slice(s, start_marker, end_marker):
    a = s.index(start_marker); b = s.index(end_marker, a); return s[a:b]

FORM   = _slice(HTML, '<div class="ent-card">', '<!-- REFINE')
REFINE = _slice(HTML, 'id="refineScreen"', '<!-- CONFIRM')

results = []
def chk(name, cond):
    results.append((name, bool(cond)))

# ── A. formScreen .ent-type fix (data-en moved parent→.etn) ──────────────────
chk("A1 tabAddr .ent-type has NO data-en on parent",
    'id="tabAddr" onclick="selTab(\'address\')">' in FORM
    and 'id="tabAddr" onclick="selTab(\'address\')" data-en' not in FORM)
chk("A2 tabLand .ent-type has NO data-en on parent",
    'id="tabLand" onclick="selTab(\'land\')">' in FORM
    and 'id="tabLand" onclick="selTab(\'land\')" data-en' not in FORM)
chk("A3 .etn villa carries data-en",
    '<div class="etn" data-en="Villa / building">فيلا أو مبنى</div>' in FORM)
chk("A4 .etn land carries data-en",
    '<div class="etn" data-en="Land / plot">أرض / قطعة</div>' in FORM)
chk("A5 svg icon + .etm preserved inside ent-type (not wiped)",
    '<svg class="eti" aria-hidden="true"><use href="#ic-home"></use></svg>' in FORM
    and 'data-en="by address">بالعنوان' in FORM)

# ── B. refineScreen static data-en ──────────────────────────────────────────
B = [
  ("ftitle",        'data-en="Property details (Stage 2)">تفاصيل العقار (المرحلة 2)'),
  ("intro",         "data-en=\"Answer only what you know"),
  ("tower disc",    'data-en="&lt;strong&gt;For towers and large compounds:&lt;/strong&gt;'),
  ("unitCount",     'data-en="Number of units in the tower">عدد الوحدات في البرج'),
  ("unitCount ph",  'data-en-ph="e.g. 80"'),
  ("avgRent",       'data-en="Average monthly rent per unit (QAR)">متوسط الإيجار'),
  ("grp1 title",    'data-en="Geometry">الهندسة'),
  ("grp1 tag",      'data-en="Moves the valuation">يحرّك التقييم'),
  ("floors lbl",    'data-en="Floors above ground">عدد الطوابق فوق الأرض'),
  ("floors o1",     'data-en="One floor (ground)">طابق واحد (أرضي)'),
  ("floors o3",     'data-en="Three (ground + first + second)">ثلاثة'),
  ("basement lbl",  'data-en="Basement (below ground)">سرداب'),
  ("basement o",    'data-en="Has a basement">يوجد سرداب'),
  ("penthouse lbl", 'data-en="Penthouse (half upper floor)">بنتهاوس'),
  ("annexes lbl",   'data-en="Number of annexes">عدد الملاحق'),
  ("annexes o1",    'data-en="One annex">ملحق واحد'),
  ("annexes o2",    'data-en="Two annexes">ملحقان'),
  ("majlis lbl",    'data-en="Separate external majlis">مجلس خارجي منفصل'),
  ("majlis present",'data-en="Present">يوجد'),
  ("footprint lbl", 'data-en="Estimated ground floor area (m²)">تقدير مساحة البناء الأرضي'),
  ("footprint ph",  'data-en-ph="optional — auto-estimated from the plot dimensions"'),
  ("grp2 title",    'data-en="Age and condition">العمر والحالة'),
  ("grp2 tag",      'data-en="Refines the cost anchor">يدقّق مرتكز التكلفة'),
  ("age lbl",       'data-en="Estimated building age (years)">عمر البناء التقديري'),
  ("age hint",      'data-en="The age recorded in the system is a lower bound (GIS survey)'),
  ("cond lbl",      'data-en="Property condition">حالة العقار'),
  ("cond new",      'data-en="New / unoccupied">جديد / لم يُسكن'),
  ("cond good",     'data-en="Good">جيدة'),
  ("cond renov",    'data-en="Renovated">مُرمّم'),
  ("cond maint",    'data-en="Needs maintenance">يحتاج صيانة'),
  ("cond teardown", 'data-en="Dilapidated / must be demolished">آيل للسقوط'),
  ("lux lbl",       'data-en="Luxury finish (for older buildings)">تشطيب فاخر'),
  ("lux yes",       'data-en="Yes — high-end finish + recent full renovation">نعم'),
  ("grp3 title",    'data-en="Financial information">معلومات مالية'),
  ("grp3 tag",      'data-en="Optional enrichment">اختياري للإثراء'),
  ("rental lbl",    'id="rentalIncomeLabel" data-en="Current monthly rent (QAR)">الإيجار الشهري الحالي'),
  ("rental hint",   'data-en="Actual rent + a calibrated capitalization rate for your area'),
  ("potential lbl", 'data-en="Expected monthly rent (QAR)">الإيجار الشهري المتوقع'),
  ("asking lbl",    'data-en="Asking price (QAR)">السعر المطلوب'),
  ("refineBtn",     'data-en="Calculate the refined valuation">احسب التقييم المُحسَّن'),
]
for name, marker in B:
    chk("B "+name, marker in REFINE)

# choose/none repeat across selects — assert EVERY Arabic original got its EN twin
chk("B every «— اختر —» got a twin (choose parity)",
    REFINE.count('— اختر —') == REFINE.count('data-en="— choose —">— اختر —') == 7)
chk("B every «لا يوجد» got a twin (none parity)",
    REFINE.count('>لا يوجد<') == REFINE.count('data-en="None">لا يوجد') == 4)

# ── C. b113 note EN twin — signed honesty PRESERVED (lawyer) ─────────────────
chk("C1 b113 note has EN data-en",
    'data-en="◆ Your condition changes the figure:' in REFINE)
chk("C2 b113 EN keeps <strong>indicative</strong> (escaped)",
    'the figure remains &lt;strong&gt;indicative&lt;/strong&gt;' in REFINE)
chk("C3 b113 EN keeps the field-inspection / banks-or-buyers deterrent",
    'renders it invalid under a field inspection by banks or buyers' in REFINE)
chk("C4 b113 AR body preserved verbatim",
    'والرقم يبقى <strong>استرشاديّاً</strong>' in REFINE
    and 'غير صالحٍ عند الفحص الميدانيّ من البنوك أو المشترين' in REFINE)

# ── D. asking-price EN keeps E1/E3 (advertised prices are not evidence) ──────
chk("D asking hint EN — advertised prices are not evidence",
    'data-en="Does not affect the estimate — shown for comparison in your report only (advertised prices are not evidence)."' in REFINE)

# ── E. closing indicative line EN (compliance «not a certified valuation») ───
chk("E closing line EN — not make it a certified valuation",
    'data-en="The result stays an indicative estimate — details improve its accuracy, they do not make it a certified valuation."' in HTML)

# ── F. rentalIncomeLabel dynamic → t() (not a bare Arabic literal) ───────────
chk("F1 tower label via t()",
    "t('إجمالي الإيجار الشهري للبرج (ر.ق)','Gross monthly rent for the tower (QAR)')" in HTML)
chk("F2 villa label via t()",
    "t('الإيجار الشهري الحالي (ر.ق)','Current monthly rent (QAR)')" in HTML)
chk("F3 no bare Arabic literal left for the tower label",
    "? 'إجمالي الإيجار الشهري للبرج (ر.ق)'" not in HTML)

# ── G. LTR overrides for #refineScreen ──────────────────────────────────────
chk("G1 #refineScreen direction:ltr",
    'body.lang-en #refineScreen{direction:ltr}' in HTML)
chk("G2 #refineScreen input/select text-align:left",
    'body.lang-en #refineScreen input,body.lang-en #refineScreen select{text-align:left}' in HTML)
chk("G3 #refineScreen label/summary/br-note text-align:left",
    'body.lang-en #refineScreen summary,body.lang-en #refineScreen label{text-align:left}' in HTML)

# ── H. NO regression — b134/b135/b88/b79 EN intact ──────────────────────────
chk("H1 pulse months bilingual (b134 t(AR,EN)) intact",
    "t(AR[m]||'',EN[m]||'')" in HTML)
chk("H2 rs-cond flag bilingual (b135) intact",
    "t('حالة مُصرَّحة','Declared condition')" in HTML)
chk("H3 EN_ENABLED live (b88)", 'var EN_ENABLED=true;' in HTML)
chk("H4 t() definition intact",
    "function t(ar,en){return (LANG==='en'&&en!=null)?en:ar;}" in HTML)
chk("H5 _applyStaticI18n swaps data-en via innerHTML",
    "el.innerHTML=(LANG==='en')?el.dataset.en:el.dataset.ar0;" in HTML)
chk("H6 formScreen data-en (b79) intact — ent-h2",
    'data-en="Which property are we valuing?"' in HTML)

# ── I. tone / termbase (catalog b78): QAR, capitalization rate, Ministry ─────
chk("I1 EN uses QAR (not ر.ق) in the new labels",
    'Current monthly rent (QAR)' in HTML and 'Asking price (QAR)' in HTML)
chk("I2 EN uses 'capitalization rate' (catalog), not 'cap rate'",
    'a calibrated capitalization rate' in HTML)

# ── J. value-neutrality: engine bumped to b137, api untouched ────────────────
chk("J1 ENGINE_VERSION → b137",
    "ENGINE_VERSION = 'thammen-sprint2p22p0b137-en-input-refine-screens'" in ENG)
chk("J2 SPRINT_TAG → 2.22.0b.137", "SPRINT_TAG = '2.22.0b.137'" in ENG)
api = io.open("api.py", encoding="utf-8").read()
chk("J3 api.py has no b137 marker (untouched)", '2.22.0b.137' not in api)

# ── report ──────────────────────────────────────────────────────────────────
passed = sum(1 for _, ok in results if ok)
total  = len(results)
for name, ok in results:
    print(("PASS " if ok else "FAIL ")+name)
print(f"\n{passed}/{total} PASS")
sys.exit(0 if passed == total else 1)
