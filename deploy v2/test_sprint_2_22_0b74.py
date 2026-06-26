# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.74 — engine emoji sweep: strip emoji from engine-emitted USER-FACING
display labels (⚠️/✓/🟢/🟡/🟠/❌/📡-note). Comments/box-drawing/arrows untouched.
E14: reads the REAL evaluate_unified.py. Value-byte-gate identical (labels, never values)."""
import io
ENG = io.open('evaluate_unified.py', encoding='utf-8').read()
LINES = ENG.splitlines()
NONCOMMENT = [l for l in LINES if not l.lstrip().startswith('#')]
NC = '\n'.join(NONCOMMENT)

passed = failed = 0
def check(name, cond):
    global passed, failed
    passed += cond; failed += (not cond)
    print(('  ok  ' if cond else '  FAIL'), name)

# ---- (1) no swept emoji left in any NON-comment (string/docstring) line ----
for e in ['⚠️', '✓', '🟢', '🟡', '🟠', '❌']:
    check('no %s in engine string/label lines' % e, e not in NC)

# ---- (2) the de-emoji'd labels survive (text intact, just no emoji) ----
for lbl in ['تقارب قوي بين الطرق', 'تباين كبير', 'بيانات غير كافية',
            'شواهد كافية', 'شواهد محدودة', 'تقدير تقريبي',
            'تحفّظ مادي متوسط', 'تحفّظ مادي مرتفع', 'اتجاه استثنائي']:
    check('label preserved (text intact): %s' % lbl, lbl in ENG)

# ---- (3) comments / structure NOT over-stripped ----
check('comment 🔴 markers preserved (not over-swept)', ENG.count('🔴') >= 4)
check('box-drawing section separators preserved', '═' in ENG)

# ---- (4) value-invariance + version guards ----
check('engine version is a valid b-series tag (version-agnostic, R6)',
      "SPRINT_TAG = '2.22.0b." in ENG and 'thammen-sprint2p22p0b' in ENG)
check('b72 value-clarity engine note intact (no-invented-central line)',
      'لا رقم مركزيّ مُخترَع' in ENG)
check('b72 e25 floor wording intact', 'أرضيةٌ لا سقفٌ' in ENG)

print('\nb74:', passed, 'passed,', failed, 'failed')
raise SystemExit(1 if failed else 0)
