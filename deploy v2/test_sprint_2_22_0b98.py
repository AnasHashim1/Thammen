# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.98 «سطر العقار + مضيف التحقّق» — isolated tests (E14).

Two value-invariant frontend fixes (the small pass after b97):
  1. Short-report property strip — dedup the district: raw_land's address is already
     «أرض في {district} — PIN …», so the trailing « · {district}» repeated it. Append
     only when the address does NOT already contain the district (villa «56/565/21» still appends).
  2. `_verifyUrl` — the printed QR + «thammen.qa/verify» link now resolve to thammen.qa,
     not the raw herokuapp API base (proven: GET thammen.qa/verify?ref=…&fp=… → «تقرير أصليّ»).
     `API` (the /api call base) is UNTOUCHED.
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML = open('index.html', encoding='utf-8').read()
ENG  = open('evaluate_unified.py', encoding='utf-8').read()

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('PASS |', name)
    else:    failed += 1; print('FAIL |', name)

# ── 1. property strip district dedup ──
strip_i = HTML.index('border-bottom:1px solid var(--thmr-line);padding-bottom:8px;margin-bottom:12px')
strip = HTML[strip_i-80:strip_i+400]
check('property strip appends district only when address lacks it',
      "(d.district&&(d.address||'').indexOf(d.district)===-1)?(' · '+esc(d.district)):''" in strip)
check('the old unconditional « · district» append is gone',
      "'</b>'+(d.district?(' · '+esc(d.district)):'')" not in HTML)

# ── 2. _verifyUrl on the branded host ──
vf_i = HTML.index('function _verifyUrl(d){')
vf = HTML[vf_i:vf_i+1100]
check('_verifyUrl builds on https://thammen.qa/verify', "'https://thammen.qa/verify?ref='" in vf)
check('_verifyUrl no longer uses the herokuapp API base', "API+'/verify?ref='" not in vf)
check('the query form (ref/fp/basis) is preserved (proven-working path)',
      'ref=' in vf and 'fp=' in vf and 'addr=' in vf and 'rule=' in vf)
check('the API const (for /api calls) is UNTOUCHED (still herokuapp)',
      "const API='https://thammen-app-123-227a7106a67a.herokuapp.com';" in HTML)
check('displayed link text «thammen.qa/verify» now matches the href host',
      'thammen.qa/verify</a>' in HTML)

# ── value-invariance: this sprint touches display only, no valuation math ──
# (b98 changes are 1 conditional + 1 URL host; assert no v.amount arithmetic was introduced here)
check('no v.amount/low/high assignment introduced (display-only)',
      HTML.count("'https://thammen.qa/verify?ref='") == 1)

# ── version bump ──
# R6/Lesson-2: version-agnostic format checks (NOT exact pins — a later bump must not break this)
check('ENGINE_VERSION is a valid b-series tag',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+b\d+-", ENG) is not None)
check('SPRINT_TAG is dotted-numeric b-series',
      re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+b\.\d+'", ENG) is not None)

# ── b97 regression: the raw-land awareness gates must still be present ──
check('b97 land gates still intact (CTA + notice + DEF-12 land)',
      "if(d.asset_type!=='raw_land') t3+=" in HTML
      and "!v.building_substantiality&&d.asset_type!=='raw_land'" in HTML
      and 'رقمان لأرضك' in HTML)

print(f'\n{passed}/{passed+failed} PASS' + ('' if failed == 0 else f' — {failed} FAIL'))
sys.exit(1 if failed else 0)
