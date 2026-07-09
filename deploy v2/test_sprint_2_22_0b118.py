# -*- coding: utf-8 -*-
# Sprint 2.22.0b.118 — «الرئيسيّة الفاخرة» / elevated marketing home.
# FRONTEND-ONLY / VALUE-INVARIANT: elevates #homeScreen into a marketing landing. Reuses live
# tokens + local IBM Plex + zero-emoji + bilingual (data-en). api.py + the valuation engine
# UNTOUCHED (the value byte-gate holds by construction). E14: asserts against the REAL index.html.
#
# R6 / Lesson-2 SUPERSESSION (b119, PO-directed 2026-07-09): the b118 above-the-fold hero
# originally carried an illustrative range-as-lead CERTIFICATE-PREVIEW card («مثال توضيحيّ»
# fabricated number) + a 3-step trust band + a source-attribution TRUST STRIP. On live review the
# PO asked to: (1) drop the fabricated number from the first page (it reads as a real result —
# against the honesty discipline); (2) remove the 3-step band; (3) reduce «وزارة العدل» to ONE
# mention above the fold (the credibility line), removing the duplicate trust strip (its content is
# fully repeated by the dedicated «مصادر البيانات» section below); and (4) drop the casual
# «لا أسعار إعلانات» (unrefined for a premium site) — refined to «استناداً إلى صفقات وزارة العدل
# المسجّلة.». b119 does all four (.lp-hero 2-col → .lp-top centered). This test asserts the
# SURVIVING b118 contribution (an elevated, value-invariant, centered marketing home) + the
# removals. b118's real intent is preserved; the superseded assertions are dropped.
import io, re
H = io.open('index.html', encoding='utf-8').read()
_home = H[H.index('id="homeScreen"'):H.index('<!-- Sprint 2.14.0 — Scope modal -->')]
_fold = _home[:_home.index('b119 slice-2: data sources')]   # the hero, above the deeper sections

_p=0;_f=0
def check(name, cond):
    global _p,_f
    if cond: _p+=1
    else: _f+=1; print('  FAIL:', name)

# ── 1. elevated centered home present ──
check('centered hero wrapper (.lp-top)', 'class="lp-top"' in _home)
check('.lp-top CSS present', '.lp-top{' in H)

# ── 2. cert card + 3-step band + duplicate trust strip SUPERSEDED (b119, PO-directed) ──
check('illustrative sample card REMOVED (no fabricated number on the front page)',
      'class="lp-cert"' not in _home and 'مثال توضيحيّ' not in _home)
check('3-step band REMOVED', 'class="htrust"' not in _home and 'نتيجتك فوراً' not in _home)
check('duplicate source trust strip REMOVED (source kept once + in the Sources section)',
      'class="lp-trust"' not in _home and '.lp-trust{' not in H)
check('casual «لا أسعار إعلانات» removed from home (premium voice)', 'لا أسعار إعلانات' not in _home)

# ── 3. pinned live home strings PRESERVED ──
check('htag preserved',  'تقييم عقارك في قطر' in _home)
check('hsub preserved',  'تقييم سوقيّ آليّ للفلل والأراضي في قطر' in _home)
check('refined MoJ credibility line present', 'استناداً إلى صفقات وزارة العدل المسجّلة.' in _home)
check('«ابدأ التقييم» wired to go(form)', "onclick=\"go('form')\"" in _home and 'ابدأ التقييم' in _home)
check('#dfSubtitle id preserved (freshness wiring)', 'id="dfSubtitle"' in _home)
check('scope link preserved', 'openScope()' in _home)
check('terms link preserved', 'openTerms()' in _home)

# ── 4. «وزارة العدل» = exactly ONCE above the fold (PO-directed) ──
check('MoJ named exactly once above the fold', _fold.count('وزارة العدل') == 1)
check('data sources still named in the Sources section',
      'وزارة العدل' in _home and ('نظم المعلومات الجغرافية' in _home or 'GIS' in _home))
check('«ليس تقييماً معتمداً» framing present (FAQ)', 'ليس تقييماً رسمياً معتمداً' in _home)

# ── 5. bilingual (EN toggle live, b88) ──
check('htag bilingual', 'data-en="Value your property in Qatar"' in _home)
check('credibility line bilingual', 'data-en="Based on registered Ministry of Justice transactions."' in _home)

# ── 6. zero TRUE emoji (b48/b74/b76); icons via the SVG sprite ──
check('zero emoji in home', not re.search(r"[\U0001F000-\U0001FAFF]", _home))
check('icons via sprite (not emoji)', 'href=#ic-' in _home)

# ── 7. value-invariance guardrails ──
# Lesson-2: no exact-version pins — assert the version FORMAT.
check('engine version format valid', "ENGINE_VERSION = 'thammen-sprint2p22p0b" in io.open('evaluate_unified.py',encoding='utf-8').read())
check('home still uses the .home screen class (screen system intact)', 'class="home screen active thmr" id="homeScreen"' in H)

print('b118: %d passed / %d failed' % (_p,_f))
raise SystemExit(1 if _f else 0)
