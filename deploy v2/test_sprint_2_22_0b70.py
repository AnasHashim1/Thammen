#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isolated a11y test — Sprint 2.22.0b.70: modal accessibility (role/aria-modal/label + Escape).

The two DISMISSABLE modals (scopeModal «نطاق الخدمة», termsModal «الشروط وإشعار الخصوصية») lacked
role=dialog / aria-modal / an accessible label, and could not be closed with the keyboard (Escape).
b70 adds them — additive HTML attributes + one global Escape handler that closes ONLY the two
dismissable modals. The betaGate consent dialog is intentionally NOT Escape-closable (affirmative
consent is required) and is left untouched (it already had role=dialog + aria-modal from b46/b27).

FRONTEND-ONLY / VALUE-INVARIANT (index.html attributes + one keydown listener; engine = 2 version
lines). Per E14 this reads the REAL index.html.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b70.py
"""
import re
import sys
from pathlib import Path

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f'  PASS  {name}')
    else:
        _failed += 1
        print(f'  FAIL  {name}')


html = Path(__file__).parent.joinpath('index.html').read_text(encoding='utf-8')


def _open_tag(el_id):
    """Return the opening <div ...> tag for id=el_id."""
    i = html.find(f'id="{el_id}"')
    if i == -1:
        return ''
    start = html.rfind('<div', 0, i)
    end = html.find('>', i)
    return html[start:end + 1] if (start != -1 and end != -1) else ''


# ── 1. scopeModal a11y ──
sm = _open_tag('scopeModal')
check('scopeModal role=dialog', 'role="dialog"' in sm)
check('scopeModal aria-modal=true', 'aria-modal="true"' in sm)
check('scopeModal aria-label present', 'aria-label="نطاق خدمة ثمّن"' in sm)

# ── 2. termsModal a11y ──
tm = _open_tag('termsModal')
check('termsModal role=dialog', 'role="dialog"' in tm)
check('termsModal aria-modal=true', 'aria-modal="true"' in tm)
check('termsModal aria-label present', 'aria-label="الشروط والمنهجيّة وإشعار الخصوصية"' in tm)  # b128 R6/Lesson-2: modal now covers Terms + methodology; aria-label present (a11y intent preserved)

# ── 3. Escape handler closes the two dismissable modals ──
# locate the b70 keydown listener block, bounded to ITS OWN closing }); (so the window
# can't overshoot into the following betaGate code).
i = html.find("Sprint 2.22.0b.70 (a11y)")
j = html.find("addEventListener('keydown'", i) if i != -1 else -1
k = html.find('});', j) if j != -1 else -1
blk = html[i:k + 3] if (i != -1 and k != -1) else ''
check('b70 Escape keydown listener present', i != -1 and "addEventListener('keydown'" in blk)
check('Escape gate on e.key===Escape', "e.key!=='Escape'" in blk)
check('Escape closes scopeModal (closeScope)', 'closeScope()' in blk and 'scopeModal' in blk)
check('Escape closes termsModal (closeTerms)', 'closeTerms()' in blk and 'termsModal' in blk)

# ── 4. The Escape handler's EXECUTABLE body closes ONLY scope+terms — never the betaGate
#       consent dialog (mandatory consent). Check the code (from addEventListener), not the comment. ──
code = html[j:k + 3] if (j != -1 and k != -1) else ''
check('Escape handler executable body does NOT touch betaGate (consent stays mandatory)',
      'betaGate' not in code and code.count('close') == 2)  # exactly closeScope + closeTerms

# ── 5. betaGate keeps its OWN dialog a11y (b46/b27) — untouched ──
bg = _open_tag('betaGate')
check('betaGate still role=dialog + aria-modal (untouched)',
      'role="dialog"' in bg and 'aria-modal="true"' in bg)

# ── 6. The modals' onclick-backdrop-close is preserved (no regression) ──
check('scopeModal backdrop-close preserved', 'if(event.target===this)closeScope()' in sm)
check('termsModal backdrop-close preserved', 'if(event.target===this)closeTerms()' in tm)

# ── 7. Version format (version-agnostic — R6) ──
ev = Path(__file__).parent.joinpath('evaluate_unified.py').read_text(encoding='utf-8')
check('ENGINE_VERSION has the valid sprint format',
      re.search(r"ENGINE_VERSION\s*=\s*'thammen-sprint\d+p\d+p\d+", ev) is not None)

print()
print(f'Sprint 2.22.0b.70 isolated: {_passed} passed, {_failed} failed')
sys.exit(0 if _failed == 0 else 1)
