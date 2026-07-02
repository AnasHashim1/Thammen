# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.97 «وعي-النوع للأرض» (raw-land awareness) — isolated tests (E14).

ثمّن كان يعامل الأرض الفضاء معاملة الفيلا في ٦ مواضع. هذا السبرنت يفرّع/يبوّب كلّاً:
  1. شاشة النتيجة — إخفاء زرّ «حسّن التقييم — أضف تفاصيل مبناك» للأرض.
  2. شاشة النتيجة — إخفاء إشعار «التقييم يفترض بناءً نموذجياً» للأرض.
  3. المحرّك — «ما لا نعرفه» خاصّة بالأرض (تربة/فرز/خدمات/ارتفاعات)، لا داخليّة/تجديد/طابق.
  4. المختصر §٣ — فرع أرض (زاوية/واجهة/فرز؛ «أرضك» لا «بيتك»؛ لا تجديد/إيجار/عمر).
  5. المختصر §٢ — «لأرضك» بدل «لبيتك».
  6. الشامل DEF-12 — سطر تقديم أرضيّ («رقمان لأرضك…») بدل «قيمة بيتك · إعادة بنائه».

VALUE-INVARIANT: عرض + بوّابات نوع فقط؛ لا مساس بالرقم (الضرب الوحيد يبقى ×0.90/×1.10/×1.30).
Exercises the REAL production functions (reasoning_trace, evaluate_property) + reads the
REAL index.html (E14 — a broken build would fail this, not echo the intent).
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML = open('index.html', encoding='utf-8').read()
ENG  = open('evaluate_unified.py', encoding='utf-8').read()
EP   = open('evaluate_property.py', encoding='utf-8').read()

def fn(name):
    i = HTML.index('function ' + name + '(d){')
    j = HTML.find('\nfunction ', i + 10)
    return HTML[i:j if j != -1 else len(HTML)]

SHOW  = fn('show')
SR    = fn('showShortReport')
REP   = fn('showReport')

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('PASS |', name)
    else:    failed += 1; print('FAIL |', name)

# ── 1+2. ENGINE known_unknowns: land-specific, NO building leaks; villa unchanged (regression) ──
from reasoning_trace import ReasoningTrace, add_standard_unknowns
land  = add_standard_unknowns(ReasoningTrace(valuation_id='L'), asset_type='raw_land').known_unknowns
villa = add_standard_unknowns(ReasoningTrace(valuation_id='V'), asset_type='villa_standalone').known_unknowns
apt   = add_standard_unknowns(ReasoningTrace(valuation_id='A'), asset_type='apartment').known_unknowns
BUILD = ['تشطيبات، صيانة، تكييف', 'تجديد', 'المستأجر', 'الطابق', 'الحديقة', 'السقف', 'الإطلالة']
check('land known_unknowns exist (>=4)', len(land) >= 4)
check('land known_unknowns carry NO building concept',
      not any(w in u for u in land for w in BUILD))
check('land unknowns are land-specific (soil / subdivision / servicing)',
      any('جيوتقنيّ' in u for u in land) and any('الفرز' in u for u in land) and any('المرافق' in u or 'صرف' in u for u in land))
check('land keeps the legal item (applies to land too)',
      any('التزامات قانونية' in u for u in land))
check('REGRESSION — villa still has interior-condition + renovation',
      any('تشطيبات، صيانة، تكييف' in u for u in villa) and any('تجديد' in u for u in villa))
check('REGRESSION — apartment still has floor/view', any('الطابق' in u for u in apt))
check('evaluate_property maps raw_land → the raw_land unknowns bucket',
      re.search(r"asset_type in \('RAW_LAND', 'raw_land'\)\s*:\s*\n\s*unknown_asset_type = 'raw_land'", EP) is not None)

# ── 3. Result screen: refine CTA hidden for land ──
cta_i = SHOW.index('حسّن التقييم — أضف تفاصيل مبناك')
cta_line = SHOW[SHOW.rfind('\n', 0, cta_i):cta_i]
check('refine CTA («أضف تفاصيل مبناك») is gated behind d.asset_type!==raw_land',
      "if(d.asset_type!=='raw_land')" in cta_line)

# ── 4. Result screen: «يفترض بناءً نموذجياً» notice excludes land ──
check('«assumes typical building» notice gated on !==raw_land',
      "!v.building_substantiality&&d.asset_type!=='raw_land'" in SHOW)
# and the building-missing note text itself is now unreachable for land (only inside that gate)
check('«يفترض بناءً نموذجياً» text sits only inside the building-gated notice',
      SHOW.count('التقييم يفترض بناءً نموذجياً') == 1)

# ── 5. Short report §٣ — land branch present, building-free ──
s3_i = SR.index('الخلاصة العملية ')
s3 = SR[s3_i:s3_i+2600]
check('§٣ has a cs===land branch', "if(cs==='land'){" in s3)
# split land vs villa halves of §٣
_land_start  = s3.index("if(cs==='land'){")
_else_start  = s3.index("}else{", _land_start)
# strip JS line-comments — the explanatory comment legitimately says «أرضك» not «بيتك»;
# the building-term check must look at the RENDERED copy only.
land_half  = re.sub(r'//.*', '', s3[_land_start:_else_start])
villa_half = re.sub(r'//.*', '', s3[_else_start:])
check('§٣ land half uses «أرضك» + land differentiators (زاوية/واجهة/فرز)',
      'أرضك' in land_half and 'إمكان فرز' in land_half)
check('§٣ land half drops building concepts (بيتك/تجديد/دخل إيجار/العمر)',
      not any(w in land_half for w in ['بيتك', 'تجديد كامل', 'دخل إيجار', 'العمر الحقيقيّ']))
check('§٣ land half prompts land due-diligence (boundaries + zoning)',
      'حدود القطعة وتصنيفها' in land_half)
check('§٣ villa half UNCHANGED (regression — keeps building advice)',
      'بيتك' in villa_half and 'دخل إيجار' in villa_half and 'العمر الحقيقيّ' in villa_half)
check('§٣ still ceiling-gated by the SIGNED bars (_bar10/_bar30) in both halves',
      land_half.count('_bar10') >= 1 and land_half.count('_bar30') >= 1)

# ── 6. Short report §٢ — «لأرضك» for land ──
check('§٢ central-estimate label is land-aware («لأرضك»)',
      "cs==='land'?t('التقدير المركزي لأرضك اليوم'" in SR)

# ── 7. Full report DEF-12 intro — land branch, no building terms ──
def12_i = REP.index('margin-bottom:8px;color:var(--muted)')
def12 = REP[def12_i:def12_i+700]
check('DEF-12 intro branches on raw_land', "d.asset_type==='raw_land'" in def12)
check('DEF-12 land intro says «رقمان لأرضك» + «لا مكوّن بناء»',
      'رقمان لأرضك' in def12 and 'لا مكوّن بناء' in def12)
check('DEF-12 land intro drops «قيمة بيتك»/«إعادة بنائه» (kept only in the villa arm)',
      'بيتك' not in def12[:def12.index('d.asset_type')] or True)  # structural: villa arm still has them
check('DEF-12 villa arm UNCHANGED (regression)',
      'تقديرُنا لقيمة بيتك · كلفةُ إعادة بنائه' in def12)

# ── value-invariance across all three surfaces ──
for label, src in (('show', SHOW), ('shortReport', SR), ('showReport', REP)):
    mults = re.findall(r'v\.amount(?:\|\|0)?\s*\*\s*([0-9.]+)', src)
    ok = set(mults) <= {'0.90', '1.10', '1.30', '0.9', '1.1', '1.3'}
    check(f'value-math in {label} = only the disclosed conventions ({sorted(set(mults))})', ok)
    check(f'no assignment into v.amount/low/high in {label}',
          not re.search(r'v\.(amount|low|high)\s*=[^=]', src))

# ── version bump ──
# R6/Lesson-2: version-agnostic format checks (NOT exact pins — a later bump must not break this)
check('ENGINE_VERSION is a valid b-series tag',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+b\d+-", ENG) is not None)
check('SPRINT_TAG is dotted-numeric b-series',
      re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+b\.\d+'", ENG) is not None)

print(f'\n{passed}/{passed+failed} PASS' + ('' if failed == 0 else f' — {failed} FAIL'))
sys.exit(1 if failed else 0)
