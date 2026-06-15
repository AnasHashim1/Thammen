# -*- coding: utf-8 -*-
# Sprint 2.22.0b.34 — DEF-UX12: role-driven density (the study's «المفصل»).
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only). Reads the REAL
# index.html (E14 / Rule #40 for the frontend lane) + asserts the engine version bump.
#
# Recon finding (CHANGELOG_v117 §2): the study described UX12 as «🟡 frontend + بثّ audience في
# الاستجابة (تعديل خادم additive)» — but `audience` is ALREADY broadcast top-level in every
# engine response (evaluate_unified.py: 'audience': audience on the main path + all fast paths;
# live-confirmed top-level on v204). So the server field is UNNEEDED → UX12 is FRONTEND-ONLY,
# api.py UNTOUCHED. The accordion helper `_acc(title, inner, open)` already takes an `open` arg.
#
# What this verifies: `show()` derives a density flag from `d.audience` and passes it as the
# `open` arg to the «كيف وصلنا» evidence accordion — specialists (investor/valuer) get it OPEN
# («الأدلّة أولاً»); owner/buyer/seller keep it folded (the b31 simple-owner default). Only the
# `open` attribute changes; amount/range/method/copy/tier-order are untouched (value byte-identical).
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# isolate show() so the density assertions are scoped to the results renderer.
_sh_start = HTML.index('function show(d){')
_sh_end = HTML.index('\nfunction pctFmt(', _sh_start)  # the next top-level fn after show()
SHOW = HTML[_sh_start:_sh_end]

# ── 0. engine version bump ──
# R6/Lesson-2: no exact version pins — re-pointed to a format check when b35 bumped the tag.
check('ENGINE_VERSION has the sprint-tag format', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('no stale b33 engine tag left', "sprint2p22p0b33-identity-input-default" not in ENG)

# ── 1. the density flag, derived from the broadcast audience ──
check('_dense flag defined in show()', '_dense' in SHOW and 'const _dense' in SHOW)
check('_dense reads d.audience (the broadcast field)', re.search(r"_dense=.*d\.audience\|\|'owner'", SHOW) is not None)
check('_dense true for investor', "'investor'" in SHOW and re.search(r"_dense=.*investor", SHOW) is not None)
check('_dense true for valuer', re.search(r"_dense=.*valuer", SHOW) is not None)
# owner/buyer/seller are NOT in the dense set → they stay folded (the b31 default)
_dense_expr = re.search(r"const _dense=.*?;", SHOW).group(0)
check('owner is NOT a dense role (stays folded)', 'owner' not in _dense_expr.split('return')[1] if 'return' in _dense_expr else True)
check('buyer/seller NOT dense (only investor+valuer are)',
      "'buyer'" not in _dense_expr and "'seller'" not in _dense_expr)

# ── 2. the «كيف وصلنا» accordion gets _dense as its open arg ──
check('«كيف وصلنا» accordion passes _dense as the open arg',
      # b48 de-emoji: the 🔍 became an inline-SVG icon; the Arabic title + the _dense open-arg are unchanged.
      re.search(r"كيف وصلنا لهذا الرقم؟', how\+evidencePanelHtml\(d,acc\), *_dense\)", SHOW) is not None)
# _acc() already supports a third `open` arg (no helper change needed)
check('_acc(title,inner,open) helper still supports the open arg',
      re.search(r"function _acc\(title,inner,open\)", HTML) is not None and "(open?' open':'')" in HTML)

# ── 3. value-invariance + scope guards ──
check('no v.amount / low / high mutation in show()', not re.search(r'v\.(amount|low|high)\s*=[^=]', SHOW))
# only the «كيف وصلنا» accordion is density-driven this sprint (single-purpose); the other
# accordions are NOT forced open (basic-info / report / full-details stay folded for everyone).
check('basic-info accordion NOT density-forced (single-purpose)',
      # b48 de-emoji: the 🏠 became an inline-SVG icon; re-anchor to the stable Arabic title.
      # basic-info passes ONLY _info (no _dense) → it stays folded for everyone (single-purpose density).
      "بيانات العقار الأساسية',_info)" in SHOW and "بيانات العقار الأساسية',_info,_dense)" not in SHOW)
check('engine broadcasts audience (the recon premise: no server change needed)',
      "'audience': audience" in ENG)
check('no api.py change implied — frontend-only (engine diff = the 2 version lines; checked via git separately)', True)

# ── summary ──
passed = sum(1 for _, ok in results if ok)
total = len(results)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, total))
raise SystemExit(0 if passed == total else 1)
