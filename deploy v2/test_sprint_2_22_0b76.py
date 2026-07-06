# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.76 — complete the engine emoji sweep (the response-bound modules
b74 didn't cover: material_uncertainty + market_regime + geometric_factors + qatar_gis
reality-check). Measured: these are the only user-facing-RESPONSE emoji left; print()/CLI
emoji are preserved. E14: reads the REAL modules. Value-invariant (display strings)."""
import io
def rd(p): return io.open(p, encoding='utf-8').read()
MU = rd('material_uncertainty.py'); MR = rd('market_regime.py')
GF = rd('geometric_factors.py');   QG = rd('qatar_gis.py'); ENG = rd('evaluate_unified.py')

passed = failed = 0
def check(name, cond):
    global passed, failed
    passed += cond; failed += (not cond)
    print(('  ok  ' if cond else '  FAIL'), name)

# ---- material_uncertainty: 0 emoji left; the 4 level TEXTS + clause preserved ----
for e in ['⚠️', '⛔', 'ℹ️', '✅']:
    check('material_uncertainty: no %s' % e, e not in MU)
for txt in ['عدم اليقين الجوهري: حرج —', 'عدم اليقين الجوهري: مرتفع —', 'عدم اليقين الجوهري: متوسط —',
            'مستوى اليقين جيد —', 'عدم اليقين الجوهري في التقييم وفق']:
    check('MUC level/clause text preserved: %s' % txt, txt in MU)
for txt_en in ['CRITICAL Material Uncertainty', 'HIGH Material Uncertainty',
               'MODERATE Material Uncertainty', 'LOW Material Uncertainty',
               'Material Valuation Uncertainty per RICS']:
    check('MUC EN text preserved: %s' % txt_en, txt_en in MU)

# ---- market_regime: recency note de-emoji'd ----
check('market_regime: recency note text preserved', 'آخر معاملة في وزارة العدل' in MR)
check('market_regime: no ⚠️', '⚠️' not in MR)

# ---- geometric_factors: adjacency evidence de-emoji'd ----
check('geometric_factors: evidence text preserved', 'تصنيف صناعي مجاور' in GF and 'إمكانية تعديل رخصة' in GF)
check('geometric_factors: no ⚠ in evidence', '⚠ ' not in GF)

# ---- qatar_gis: reality-check de-emoji'd; the 2 print() ⚠ PRESERVED ----
check('qatar_gis: reality-check «هذه القطعة (PIN» preserved', 'هذه القطعة (PIN' in QG)
check('qatar_gis: «البناء: موجود» (no trailing ✓)', 'البناء: موجود' in QG and 'موجود ✓' not in QG)
check('qatar_gis: leading «⚠ هذه» gone', '⚠ هذه' not in QG)
check('qatar_gis: the 2 print(⚠) CLI lines PRESERVED (not over-swept)', QG.count('⚠') == 2)

# ---- version + value-invariance guards ----
check('engine version is a valid b-series tag (version-agnostic, R6)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)
check('b75 منهج unify intact (no «طريقة» regressed)', 'طريقة' not in ENG)

print('\nb76:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
