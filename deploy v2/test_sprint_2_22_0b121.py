# -*- coding: utf-8 -*-
# Sprint 2.22.0b.121 (S1, redesign v2) — the landing hero from the design handoff.
# FRONTEND-ONLY / VALUE-INVARIANT: rebuilds ONLY the .lp-top hero — transparent logo_t.png,
# a bronze kicker, an inline acknowledgement line (with the Terms link), and trust chips.
# The title + sub are PRESERVED verbatim (b24); the lower marketing sections (data-sources,
# why, coverage, FAQ, CTA, footer) are UNTOUCHED. The consent gate is UNCHANGED (S3 decides).
# api.py + the valuation engine untouched (2 version lines) → the 5-fixture byte-gate holds.
# E14: asserts against the REAL index.html.
import io
H = io.open('index.html', encoding='utf-8').read()
_home = H[H.index('id="homeScreen"'):H.index('<!-- Sprint 2.14.0 — Scope modal -->')]
_top = _home[_home.index('class="lp-top"'):_home.index('<!-- /lp-top -->')]

_p = _f = 0
def check(name, cond):
    global _p, _f
    if cond: _p += 1
    else: _f += 1; print('  FAIL:', name)

# ── 1. transparent logo in the hero (the design's key ask) ──
check('hero uses logo_t.png (transparent), not logo.png', 'src="logo_t.png"' in _top and 'src="logo.png"' not in _top)
check('logo_t.png asset present on disk', __import__('os').path.exists('logo_t.png'))

# ── 2. bronze kicker (above the title) ──
check('kicker present + verbatim copy', 'class="hkick"' in _top and 'تقييم عقاريّ استرشاديّ · قطر' in _top)
check('kicker bilingual', 'data-en="Indicative property valuation · Qatar"' in _top)
check('kicker CSS uses bronze + type-scale token', '.lp-top .hkick{' in H and 'color:var(--bronze)' in H and 'font-size:var(--fs-12)' in H)

# ── 3. title + sub PRESERVED verbatim (no regression, b24 lock) ──
check('title preserved verbatim', 'class="htag" data-en="Value your property in Qatar">تقييم عقارك في قطر' in _top)
check('sub preserved verbatim', 'تقييم سوقيّ آليّ للفلل والأراضي في قطر' in _top)

# ── 4. inline acknowledgement line under the CTA ──
check('acknowledgement line present', 'class="hack"' in _top)
check('ack: «تقديرٌ استرشاديّ … لا تقييمٌ معتمد»', 'تقديرٌ استرشاديّ' in _top and 'لا تقييمٌ معتمد' in _top)
check('ack carries the Terms link (openTerms)', 'class="hack"' in _top and 'openTerms()' in _top and 'الشروط والخصوصية' in _top)
check('ack bilingual (indicative estimate / not a certified valuation)',
      'indicative estimate' in _top and 'not a certified valuation' in _top)

# ── 5. trust chips (free / no account / no tracking) ──
check('trust chips block present', 'class="hchips"' in _top)
check('three trust chips', _top.count('<use href=#ic-check>') == 3)
check('trust chips copy', 'مجاني' in _top and 'بلا حساب' in _top and 'بلا تتبّع' in _top)
check('trust chips bilingual', 'data-en="Free"' in _top and 'data-en="No account"' in _top and 'data-en="No tracking"' in _top)
check('trust-chip icons use --ok (green check)', '.lp-top .hchips .ic{' in H and 'color:var(--ok)' in H)

# ── 6. CTA still wired to the form (navigation preserved) ──
check('hero CTA still goes to form', "onclick=\"go('form')\"" in _top and 'ابدأ التقييم' in _top)

# ── 7. the consent gate is UNCHANGED (S1 does not touch it — S3 decides) ──
check('betaGate markup still present (untouched)', 'id="betaGate"' in H)
check('ackBeta() still defined', 'function ackBeta()' in H)

# ── 8. compliance surfaces on the whole home PRESERVED (lower sections untouched) ──
check('CC BY 4.0 attribution kept (data-sources + footer)', _home.count('CC BY 4.0') >= 2)
check('«غير منتسبة لوزارة العدل» kept (footer)', 'غير منتسبة لوزارة العدل' in _home)
check('«ليس تقييماً رسمياً معتمداً» kept (FAQ)', 'ليس تقييماً رسمياً معتمداً من مقيّم مُرخّص' in _home)
check('the lower sections are still present (not clobbered)',
      'أرقامٌ حقيقيّة من صفقاتٍ مسجّلة' in _home and 'لماذا ثمّن' in _home and
      'ما نغطّيه الآن' in _home and 'الأسئلة الشائعة' in _home and 'class="lp-foot"' in _home)

# ── 9. VALUE-INVARIANCE: S1 is markup/CSS only — no value math introduced ──
check('no amount arithmetic in the hero', 'amount' not in _top.lower())

print('b121 (S1): %d passed, %d failed' % (_p, _f))
raise SystemExit(1 if _f else 0)
