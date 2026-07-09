# -*- coding: utf-8 -*-
# Sprint 2.22.0b.118 — «الرئيسيّة الفاخرة» / elevated marketing home.
# FRONTEND-ONLY / VALUE-INVARIANT: elevates #homeScreen into a 2-col marketing hero
# (pitch + range-as-lead certificate-preview card) + a source-attribution trust strip.
# Reuses live tokens + local IBM Plex + zero-emoji + the b3 range-as-lead + bilingual (data-en).
# api.py + the valuation engine UNTOUCHED (only the 2 version-string lines change) → the
# 5-fixture value byte-gate holds by construction. E14: asserts against the REAL index.html.
import io, re
H = io.open('index.html', encoding='utf-8').read()
_home = H[H.index('id="homeScreen"'):H.index('<!-- Sprint 2.14.0 — Scope modal -->')]

_p=0;_f=0
def check(name, cond):
    global _p,_f
    if cond: _p+=1
    else: _f+=1; print('  FAIL:', name)

# ── 1. elevated structure present ──
check('lp-hero 2-col wrapper', 'class="lp-hero"' in _home and 'class="lp-hero-l"' in _home and 'class="lp-hero-r"' in _home)
check('certificate-preview card', 'class="lp-cert"' in _home)
check('source-attribution trust strip', 'class="lp-trust"' in _home)
check('lp- CSS block present', '.lp-hero{' in H and '.lp-cert{' in H and '.lp-trust{' in H)

# ── 2. range-as-lead (b3), NOT a bare point ──
check('range headline element (.lp-rng)', 'class="lp-rng"' in _home)
check('muted median marker (.lp-med)', 'class="lp-med"' in _home and 'الوسيط' in _home)
check('confidence bar', 'class="lp-cbar"' in _home)
check('range low+high shown', '٢٬٦٠٠٬٠٠٠' in _home and '٢٬٢٠٠٬٠٠٠' in _home)

# ── 3. pinned live home strings PRESERVED (no regression) ──
check('htag preserved',  'تقييم عقارك في قطر' in _home)
check('hsub preserved',  'تقييم سوقيّ آليّ للفلل والأراضي في قطر' in _home)
check('3-step trust band preserved', 'أدخل العنوان' in _home and 'نحلّل الصفقات المسجّلة' in _home and 'نتيجتك فوراً' in _home)
check('hcred preserved (verbatim)', 'من صفقات وزارة العدل المسجّلة — لا أسعار إعلانات.' in _home)
check('«ابدأ التقييم» wired to go(form)', "onclick=\"go('form')\"" in _home and 'ابدأ التقييم' in _home)
check('#dfSubtitle id preserved (freshness wiring)', 'id="dfSubtitle"' in _home)
check('scope link preserved', 'openScope()' in _home)
check('terms link preserved', 'openTerms()' in _home)

# ── 4. compliance / honesty preserved ──
check('«ليس تقييماً معتمداً» on the card', 'ليس تقييماً معتمداً' in _home)
check('data sources named (وزارة العدل + GIS)', 'وزارة العدل' in _home and 'نظم المعلومات الجغرافية' in _home)
check('sample card labelled illustrative (honest)', 'مثال توضيحيّ' in _home)
check('home العدل count ≤ 3 (b56 anti-redundancy honored)', _home.count('العدل') <= 3)

# ── 5. bilingual (EN toggle live, b88) — new card carries data-en ──
check('cert title bilingual', 'data-en="Villa — Bu Hamour"' in _home)
check('range bilingual', 'QAR' in _home)
check('notcert bilingual', 'not a certified valuation' in _home)
check('trust strip bilingual', 'data-en="Ministry of Justice"' in _home and 'data-en="Qatar GIS"' in _home)

# ── 6. zero TRUE emoji (b48/b74/b76); icons via the SVG sprite ──
check('zero emoji in home', not re.search(r"[\U0001F000-\U0001FAFF]", _home))
check('scale icon via sprite (not emoji)', 'href=#ic-scale' in _home)

# ── 7. value-invariance guardrails ──
check('version bumped to b118', "thammen-sprint2p22p0b118" in io.open('evaluate_unified.py',encoding='utf-8').read())
check('home still uses the .home screen class (screen system intact)', 'class="home screen active thmr" id="homeScreen"' in H)

print('b118: %d passed / %d failed' % (_p,_f))
raise SystemExit(1 if _f else 0)
