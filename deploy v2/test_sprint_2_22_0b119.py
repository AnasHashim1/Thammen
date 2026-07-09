# -*- coding: utf-8 -*-
# Sprint 2.22.0b.119 — marketing home slice-2: the deeper sections.
# FRONTEND-ONLY / VALUE-INVARIANT: appends data-sources · why · coverage · FAQ · CTA · footer
# to #homeScreen (after the b118 hero + trust). Bilingual (data-en), zero-emoji (SVG sprite),
# live tokens, all compliance. api.py + the valuation engine UNTOUCHED (2 version lines only) →
# the 5-fixture value byte-gate holds by construction. E14: asserts against the REAL index.html.
import io, re
H = io.open('index.html', encoding='utf-8').read()
_home = H[H.index('id="homeScreen"'):H.index('<!-- Sprint 2.14.0 — Scope modal -->')]

_p=0;_f=0
def check(name, cond):
    global _p,_f
    if cond: _p+=1
    else: _f+=1; print('  FAIL:', name)

# ── 1. all six sections present (inside homeScreen) ──
check('data-sources section', 'أرقامٌ حقيقيّة من صفقاتٍ مسجّلة' in _home and 'class="lp-card j"' in _home and 'class="lp-card g"' in _home)
check('why-thammen (4 pillars)', 'لماذا ثمّن' in _home and _home.count('class="wi"') == 4)
check('coverage section + apartments-not-yet', 'ما نغطّيه الآن' in _home and 'الشقق والأبراج' in _home and 'غير مشمولة بعد' in _home)
check('FAQ (5 items)', 'الأسئلة الشائعة' in _home and _home.count('<details><summary') == 5)
check('CTA section wired to go(form)', 'class="lp-cta"' in _home and "onclick=\"go('form')\"" in _home and 'قيّم عقارك الآن' in _home)
check('marketing footer', 'class="lp-foot"' in _home and 'class="brand">ثمّن' in _home)
check('slice-2 CSS present', '.lp-sec{' in H and '.lp-faq' in H and '.lp-why' in H and '.lp-foot{' in H)

# ── 2. compliance / honesty (the FAQ + attribution carry the honest framing) ──
check('«ليس تقييماً معتمداً» framing (FAQ)', 'ليس تقييماً رسمياً معتمداً من مقيّم مُرخّص' in _home)
check('CC BY 4.0 attribution (data-sources + footer)', _home.count('CC BY 4.0') >= 2)
check('«غير منتسبة لوزارة العدل»', 'غير منتسبة لوزارة العدل' in _home)
check('RICS/IVS named in FAQ', 'RICS/IVS' in _home)
check('condition caveat (may fall to land / exceed)', 'قد ينخفض السعر الفعليّ نحو قيمة الأرض' in _home)
check('data policy (no account/tracking, deletion right)', 'لا حساب ولا تسجيل دخول ولا تتبّع' in _home and 'طلب حذفها' in _home)
# b56 anti-redundancy + b119 PO-directed «مرة واحدة»: the MoJ credibility line appears once.
check('MoJ credibility line not duplicated', _home.count('استناداً إلى صفقات وزارة العدل المسجّلة.') <= 1)

# ── 3. bilingual (EN toggle live) — new sections carry data-en ──
check('data-sources bilingual', 'data-en="Ministry of Justice"' in _home and 'data-en="Real figures from registered transactions"' in _home)
check('why bilingual', 'data-en="Instant"' in _home and 'data-en="Independent"' in _home)
check('coverage bilingual (with &lt;b&gt;)', 'data-en="Apartments and towers — &lt;b&gt;not yet included&lt;/b&gt;"' in _home)
check('FAQ bilingual (Q+A)', 'data-en="Is this a certified valuation?"' in _home and 'not an official valuation certified by a licensed valuer' in _home)
check('footer bilingual (not affiliated)', 'not affiliated with the Ministry of Justice' in _home)

# ── 4. zero TRUE emoji; icons via the SVG sprite ──
check('zero emoji in home', not re.search(r"[\U0001F000-\U0001FAFF]", _home))
check('why icons via sprite (clock/search/scale/key)', all(('href=#ic-'+i) in _home for i in ['clock','search','scale','key']))

# ── 5. value-invariance guardrails ──
# Lesson-2: no exact-version pins — assert the version FORMAT.
check('engine version format valid', "ENGINE_VERSION = 'thammen-sprint2p22p0b" in io.open('evaluate_unified.py',encoding='utf-8').read())
# R6/Lesson-2 (PO-directed 2026-07-09): the b118 illustrative cert card + 3-step band were
# removed (a fabricated number on the front page reads as a real result — against the honesty
# discipline). The b118 elevated home SURVIVES as the centered hero (.lp-top) + trust strip.
check('b118 elevated hero (.lp-top) present; cert/3-step/duplicate-trust-strip superseded',
      'class="lp-top"' in _home
      and 'class="lp-cert"' not in _home and 'نتيجتك فوراً' not in _home
      and 'class="lp-trust"' not in _home)
# b119.1 (PO-directed): the hero recency line #dfSubtitle was removed (moved to Terms §2).
check('start CTA intact; hero recency line removed', "onclick=\"go('form')\"" in _home and 'id="dfSubtitle"' not in _home)

print('b119: %d passed / %d failed' % (_p,_f))
raise SystemExit(1 if _f else 0)
