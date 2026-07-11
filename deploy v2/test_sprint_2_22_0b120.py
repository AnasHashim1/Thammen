# -*- coding: utf-8 -*-
# Sprint 2.22.0b.120 (S0, redesign v2) — the foundation slice for the design-handoff rebuild.
# FRONTEND + one static route / VALUE-INVARIANT: adds the missing design tokens, deposits the
# transparent logo (logo_t.png + its api.py route), and generalises the count-up into shared
# motion primitives (_countUp + _revealOnScroll) — both reduced-motion-guarded, display-only.
# No render function changes; no value math; the 5-fixture byte-gate holds by construction.
# E14: asserts against the REAL index.html + api.py.
import io, os, re
H = io.open('index.html', encoding='utf-8').read()
A = io.open('api.py', encoding='utf-8').read()

_p = _f = 0
def check(name, cond):
    global _p, _f
    if cond: _p += 1
    else: _f += 1; print('  FAIL:', name)

_root = H[H.index(':root{'):H.index('}', H.index(':root{')) + 1]

# ── 1. tokens: the undefined --sh-lg bug is fixed + new tokens present ──
check('--sh-lg now DEFINED (was used at .lp-card:hover, undefined)', '--sh-lg:' in _root)
check('--sh-lg is still consumed (no orphan)', 'var(--sh-lg)' in H)
check('--sh-hero (navy hero shadow) defined', '--sh-hero:' in _root)
check('--navy-d (footer navy) defined', '--navy-d:#0E2438' in _root)
check('--paper-d (darker panel bg) defined', '--paper-d:#E6DFD2' in _root)
check('--text2 (secondary ink) defined', '--text2:#5B6670' in _root)
check('--ok2 (bright success) defined', '--ok2:#22C55E' in _root)
# ── 2. the 7-step type scale, all eight rungs present ──
for rung in ('12','14','16','20','25','31','44','52'):
    check('type-scale --fs-%s defined' % rung, ('--fs-%s:%spx' % (rung, rung)) in _root)
check('type scale sits in :root (single source)', _root.count('--fs-') == 8)

# ── 3. existing :root tokens PRESERVED verbatim (no regression) ──
for tok in ('--bg:#FBF8F2', '--primary:#16324F', '--bronze:#A4814A', '--gold:#E8C99A',
            '--muted:#6B7280', '--light:#9CA3AF', '--r:12px', '--sh:0 2px 10px rgba(22,50,79,.07)'):
    check('preserved token %s' % tok.split(':')[0], tok in _root)

# ── 4. logo_t.png asset + route ──
check('logo_t.png deposited on disk', os.path.exists('logo_t.png'))
check('logo_t.png is a real PNG (magic bytes)', open('logo_t.png', 'rb').read(8) == b'\x89PNG\r\n\x1a\n')
check('logo.png UNCHANGED (still present)', os.path.exists('logo.png'))
check('GET /logo_t.png route in api.py', '@app.get("/logo_t.png")' in A)
check('route serves logo_t.png as image/png', 'FileResponse("logo_t.png", media_type="image/png")' in A)
check('route is UNRATED (no @limiter — static posture like /logo.png)',
      '@limiter' not in A[A.index('/logo_t.png'):A.index('/logo_t.png') + 260])
check('/logo.png route still present (not clobbered)', '@app.get("/logo.png")' in A)

# ── 5. motion primitives (display-only, value-invariant) ──
check('_countUp(el,target,dur) defined', 'function _countUp(el,target,dur)' in H)
check('_countUp ALWAYS lands on fmt(target) (value-invariant)',
      'const final=fmt(Math.round(target));' in H and 'el.textContent=final;' in H)
check('_countUp honours reduced-motion (snaps to final)',
      "(prefers-reduced-motion: reduce)').matches){el.textContent=final;return;}" in H)
check('_countUp uses easeOutCubic', 'e=1-Math.pow(1-p,3)' in H)
check('_revealOnScroll(sel) defined w/ IntersectionObserver', 'function _revealOnScroll(sel)' in H and 'new IntersectionObserver' in H)
# b126 R6/Lesson-2: _revealOnScroll gained a `const show=el=>el.classList.add('rv-in')` helper + a
# defensive in-view-immediate + safety-net path; the reduced-motion branch still reveals ALL at once with
# no observer (`els.forEach(show); return;`). Behaviour preserved; re-anchor off the literal.
check('_revealOnScroll reduced-motion → reveal all, no observer',
      "els.forEach(show); return;" in H and "const show=el=>el.classList.add('rv-in');" in H)
# b126 R6: the reveal primitive was SCOPED from a bare `.rv` (which collided with the info-row VALUE class
# `.ri .rv`, hiding real content) to `.rs-sec.rv`; still reduced-motion-guarded.
check('reveal CSS scoped to .rs-sec.rv + reduced-motion-guarded',
      '.rs-sec.rv{opacity:0' in H and '.rs-sec.rv.rv-in{opacity:1' in H
      and '@media(prefers-reduced-motion:no-preference)' in H)
# ── 6. _srCountUp is now a THIN WRAPPER (DRY) — behaviour preserved ──
_sr = H[H.index('function _srCountUp()'):H.index('function _srCountUp()') + 220]
check('_srCountUp delegates to _countUp (DRY)', '_countUp(el,parseFloat(el.getAttribute(\'data-countup\')),800)' in _sr)
check('_srCountUp still reads #srHeroNum + data-countup', "getElementById('srHeroNum')" in _sr)

# ── 7. VALUE-INVARIANCE contract: S0 introduced no new amount math ──
# the only frontend arithmetic remains the disclosed ×0.90 / ×1.10 / ×1.30 / _srPayment.
check('no new v.amount multiplication in the primitives',
      'target*e' in H and H.count('function _countUp') == 1)
check('_srPayment (the one allowed value-math) untouched', 'function _srPayment(P,downPct,years,ratePct)' in H)

print('b120 (S0): %d passed, %d failed' % (_p, _f))
raise SystemExit(1 if _f else 0)
