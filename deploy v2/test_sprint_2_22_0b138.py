# -*- coding: utf-8 -*-
# Sprint 2.22.0b.138 — EN result-screen fossils (frontend, value-neutral)
# E14: reads the REAL index.html + evaluate_unified.py.
# Contract: every hardcoded Arabic literal in show()/the re-eval helpers/the
# financing calc is now t('<AR-verbatim>','<EN>') -> AR mode is byte-identical
# (t returns arg1), EN mode renders English. No engine/api logic change.
import re, sys

H = open('index.html', encoding='utf-8').read()
EV = open('evaluate_unified.py', encoding='utf-8').read()
AP = open('api.py', encoding='utf-8').read()

fails = []
def ck(cond, msg):
    if not cond: fails.append(msg)

# 1. version bump (format-agnostic per R6/Lesson-2 elsewhere, exact here for the new tag)
ck("thammen-sprint2p22p0b138-en-result-fossils" in EV, "ENGINE_VERSION not b138")
ck("SPRINT_TAG = '2.22.0b.138'" in EV, "SPRINT_TAG not b138")

# 2. i18n infra intact -> value-neutral (t returns arg1 when AR; EN live but AR default)
ck("function t(ar,en){return (LANG==='en'&&en!=null)?en:ar;}" in H, "t() def changed")
ck("var EN_ENABLED=true;" in H, "EN_ENABLED missing")

# 3. api.py + engine logic untouched (only the 2 version-string lines changed in EV)
ck("b138" not in AP, "api.py mentions b138 (should be untouched)")

# 4. every fossil is now a t() first-arg (AR verbatim => AR byte-identical).
#    Checks the AR-arg PREFIX only (not the EN wording) to avoid brittle copy pins.
WRAPS = [
  "t('يرجى إدخال مساحة صحيحة بين 1 و 10,000 م²',",
  "t('حدث خطأ',",
  "t('جاري إعادة التقييم بمساحة ',",
  "t('يرجى إدخال المساحة الجديدة',",
  "t('جاري تحسين التقييم...',",
  "t('(حصة الوحدة في قطعة مشتركة',",
  "t('الحدّ الأقصى المُقدَّر ',",
  "t('ℹ المنهجية ومعايير &lrm;RICS / IVS&lrm;',",
  "t('تناقض في تصنيف العقار',",
  "t('ملاحظة:',",
  "t('التوصية:',",
  "t('تنبيه على تصنيف الأرض',",
  "t('القطعة عليها مبنى',",
  "t('خارج نطاق التقييم',",
  "t('قطعة مشتركة (',",
  "t('تقييم مبدئي بقسمة الأرض بالتساوي (',",
  "t('الفيلات الأخرى على نفس الـ PIN: ',",
  "t('تم استخدام المساحة التي حدّدتها يدوياً (',",
  "t('المرحلة ',",
  "t('عدّل المساحة (م²):',",
  "t('إعادة التقييم',",
  "t('ثمّن يدعم <strong>الفلل والأراضي</strong> فقط حالياً.',",
  "t('يتطلب:',",
  "t('مساحة البناء الأرضي (مؤكَّد ',",
  "t('حسّن التقييم (المرحلة 2)',",
  "t('اعتُمدت مساحة البناء الأرضية: ',",
  "t('حُدِّدت مساحة البناء إلى ',",
  "t('قطعتك ≈ ',",
  "t('هذه القطعة مشتركة بين ',",
  "t('لوحدتك',",
  "t('الحدّ الأقصى المسموح للبناء ≈ ',",
  "t('هذا تقدير مبدئي يفترض بناءً نموذجياً (المقترح ',",
  "t(' · حدّ التغطية النظامي ',",
  "t('عدّل التفاصيل',",
  "t('السرداب (إن وُجد) يُعرض ويُلتقَط لكنه لا يُحرّك تقدير المقارنة.',",
  "t('ℹ التقييم يفترض بناءً نموذجياً',",
  "t('قد يؤدي إدخال التفاصيل الفعلية للعقار",
  "t('⤴ توسيع النطاق الأعلى (+',",
  "t('النقطة المركزية محافظة (وسيط المقارنات).",
  "t('تعديل النقطة المركزية ',",
  "t('اتجاه السوق: ',",
  "t('اتجاه تاريخي: ',",
  "t('ر.ق/م²',",
  "t('معاملة',",
  "t(' (يُمشى)',",
  "t(' (مختلط) — ',",
  "t('ما اكتشفه النظام آلياً',",
  "t('معلومات اكتُشفت من تحليل polygon القطعة",
  "t('مساحة محقّقة من Cadastre: ',",
  "t('مميزات الموقع',",
  "t('ما لا نعرفه (يحتاج فحص ميداني)',",
  "t('تحقّق من التقدير ←',",
  "t(' ر.ق/شهر',",
]
for w in WRAPS:
    ck(w in H, "missing wrap: " + w[:48])

# 5. bare pre-wrap forms GONE (fossil text now ONLY inside t()) -> value-neutral proof
BARE_GONE = [
  "||'حدث خطأ')",
  "</svg> تناقض في تصنيف العقار</div>",
  "margin-bottom:10px\">مميزات الموقع</div>",
  "</use></svg> ما اكتشفه النظام آلياً</div>",
  "+' ر.ق/شهر')",
  ">تحقّق من التقدير ←</a>",
]
for b in BARE_GONE:
    ck(b not in H, "bare fossil still present: " + b[:48])

# 6. COMPLETENESS GUARD — the show()+re-eval region carries NO unwrapped Arabic
#    display literal beyond the known-safe set (the trend-label CSS classifier
#    regex + two already-localized t()-arg concatenation fragments).
blocks = [m.group(2) for m in re.finditer(r'<script([^>]*)>(.*?)</script>', H, re.S)
          if 'src=' not in m.group(1)]
app = max(blocks, key=len)
nc = re.sub(r'/\*.*?\*/', '', app, flags=re.S)
nc = re.sub(r'(?m)//.*$', '', nc)
i0 = nc.find('async function thammenReEvalOverride')
i1 = nc.find('function _loadPulse')
reg = nc[i0:i1]
AR = re.compile(r'[؀-ۿ]')
misses = [m.group(0) for m in re.finditer(r"'[^']*'", reg)
          if AR.search(m.group(0)) and reg[max(0, m.start()-2):m.start()] != 't(']
SAFE = ("' فقط)'", "' سنة'")
real = [tk for tk in misses if 'test(_tl)' not in tk and tk not in SAFE]
ck(len(real) == 0, "UNWRAPPED display fossils remain: " + repr(real[:5]))

total = 5 + len(WRAPS) + len(BARE_GONE) + 1
if fails:
    print("b138 FAIL %d/%d" % (total - len(fails), total))
    for f in fails: print("  -", f)
    sys.exit(1)
print("b138 PASS %d/%d" % (total, total))
