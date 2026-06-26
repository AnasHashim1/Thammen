# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.75 — «طريقة»→«منهج» synonym-unify (the deferred b61 item).
E14: reads the REAL evaluate_unified.py. Value-invariant (method labels, never values)."""
import io
ENG = io.open('evaluate_unified.py', encoding='utf-8').read()

passed = failed = 0
def check(name, cond):
    global passed, failed
    passed += cond; failed += (not cond)
    print(('  ok  ' if cond else '  FAIL'), name)

# ---- (1) unify complete: no «طريقة/بطريقة/الطريقة» (the root) remains ----
check('no «طريقة» remains (fully unified to منهج)', 'طريقة' not in ENG)

# ---- (2) the «منهج» forms are present + agreement-correct (masc) ----
for s in ['منهج الدخل', 'منهج التكلفة الإحلالية', 'هو المنهج الأنسب لهذه الفئة',
          'الدخل هو المنهج المعياريّ', '(المنهج المعياريّ لهذه الفئة)',
          'منهج واحد معتمد', 'تقدير بمنهج واحد']:
    check('present (masc agreement): %s' % s, s in ENG)

# ---- (3) the 1972 reword (verb fem->masc, no منهج/منهجي root-repeat) ----
check('1972 reworded: «منهج الدخل هنا للتأكيد فقط، ولا يدخل في القيمة»',
      'منهج الدخل هنا للتأكيد فقط، ولا يدخل في القيمة' in ENG)
check('old 1972 «طريقة الدخل هنا تأكيد منهجي ولا تدخل» gone',
      'طريقة الدخل هنا تأكيد منهجي' not in ENG)

# ---- (4) the cross-reference matches the section title (consistency) ----
check('cross-ref «انظر قسم "منهج الدخل"» matches the section title',
      'انظر قسم "منهج الدخل"' in ENG)

# ---- (5) value-invariance + version guards ----
check('engine version is a valid b-series tag (version-agnostic, R6)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)
check('b72/b74 markers intact (no-invented-central line; no swept emoji)',
      'لا رقم مركزيّ مُخترَع' in ENG and '⚠️' not in ENG)

print('\nb75:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
