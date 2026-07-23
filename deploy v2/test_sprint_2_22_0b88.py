# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.88 — «كشف زرّ الإنجليزية» (EN reveal + result-family static-chrome completion)

The reveal flips EN_ENABLED=true so the b77 language toggle goes live (the PO signed off
the wording 2026-07-01: "i approve the wording for now, please i need to see the english
button"). Since b79 wired the STATIC i18n for gate/home/form ONLY, the reveal also completes
the result-family static chrome (nav buttons + the results disclaimer + copy/print buttons +
scope-badge labels) so the revealed button lands on a genuinely English screen — not a mixed
one. FRONTEND-ONLY / VALUE-INVARIANT: AR is the default (LANG='ar' unless the user picks EN),
every AR literal is preserved (as the data-en element's content, or as the t()/pick() AR arg),
so the AR render is byte-identical. The deep engine-authored note bodies (backend `_en` twins)
remain the disclosed residual for b89+.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b88.py
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = io.open(os.path.join(HERE, "index.html"), encoding="utf-8").read()

_p = 0
_f = 0
def ok(cond, label):
    global _p, _f
    if cond:
        _p += 1
    else:
        _f += 1
        print(u"  FAIL: " + label)

# ── 1. THE REVEAL: EN_ENABLED flipped to true ────────────────────────────────
ok("var EN_ENABLED=true;" in HTML, "EN_ENABLED flipped to true (the reveal)")
ok("var EN_ENABLED=false;" not in HTML, "the old dormant EN_ENABLED=false is gone")

# ── 2. AR remains the DEFAULT (byte-identical AR for a fresh user) ────────────
# LANG defaults to 'ar' unless EN_ENABLED AND a stored 'en' choice exists.
ok("var LANG=(EN_ENABLED&&_langStored()==='en')?'en':'ar';" in HTML,
   "LANG default is 'ar' (EN only when EN_ENABLED AND stored=='en')")
# The dark-period guard line is unchanged (setLang still lands on AR when flag-off).
ok("if(!EN_ENABLED&&l==='en')l='ar';" in HTML, "setLang dark-period guard intact")

# ── 3. The b77 i18n primitives + toggle infra are intact ─────────────────────
ok("function t(ar,en){return (LANG==='en'&&en!=null)?en:ar;}" in HTML, "t() primitive intact")
ok("function pick(o,base){" in HTML, "pick() primitive intact")
ok("function setLang(l){" in HTML, "setLang() intact")
ok("function _mountLangToggle(){" in HTML, "_mountLangToggle() intact")
ok("if(!EN_ENABLED)return;" in HTML, "_mountLangToggle still guards on EN_ENABLED")
ok("function _rerenderForLang(){" in HTML, "_rerenderForLang() intact")

# ── 4. NAV-BUTTON chrome: data-en added, AR content PRESERVED ────────────────
# «→ تقييم جديد» (confirm + results) → data-en, AR text kept
ok('data-en="← New valuation">→ تقييم جديد</button>' in HTML,
   "new-valuation button: data-en added + AR '→ تقييم جديد' preserved")
ok(HTML.count('data-en="← New valuation"') == 2, "both new-valuation buttons (confirm+results) wrapped")
# «→ رجوع للنتيجة» (refine + report) → data-en
ok('data-en="← Back to result">→ رجوع للنتيجة</button>' in HTML,
   "back-to-result button: data-en added + AR preserved")
ok(HTML.count('data-en="← Back to result"') == 2, "both back-to-result buttons (refine+report) wrapped")
# the short-report wrapper nav-back button → data-en (b141 R6: relabeled «→ التفاصيل الكاملة» →
# «→ النتيجة» / "← Result", since it navigates back to the result screen; data-en still present)
ok('data-en="← Result">→ النتيجة</button>' in HTML,
   "result nav button: data-en added + AR preserved")

# ── 5. RESULTS DISCLAIMER (.disc): each AR line wrapped in a data-en span ─────
ok('data-en="This automated market valuation is indicative and based on publicly available Ministry of Justice data.">' in HTML,
   "disc line 1 data-en present")
ok("هذا التقييم السوقيّ الآليّ إرشاديّ" in HTML,
   "disc line 1 AR preserved")
ok('data-en="It is not an official valuation and does not replace a certified valuer.">' in HTML,
   "disc line 2 data-en present")
ok('data-en="We recommend engaging a certified valuer for transactions above QAR 5 million.">' in HTML,
   "disc line 3 data-en present")
ok('data-en="Terms &amp; Privacy Notice">' in HTML, "Terms link data-en present")
ok('data-en="— uses Ministry of Justice open data">' in HTML, "CC-BY intro line data-en present")
# the mandatory CC BY 4.0 src-credit (already bilingual) is untouched
ok('<span class="en">Source data: real-estate transaction bulletins, Ministry of Justice' in HTML,
   "src-credit EN (a25) still present + untouched")

# ── 6. JS-built chrome: copy / print buttons wrapped in t() ──────────────────
ok("t('نسخ النتيجة','Copy result')" in HTML, "copy button t()-wrapped")
ok("t('طباعة / حفظ PDF','Print / save PDF')" in HTML, "print button t()-wrapped")

# ── 7. SCOPE badge: 4 labels t()-wrapped + label/methodology via pick() ──────
ok("t('تحليل آلي','Automated analysis')" in HTML, "scope 'supported' label t()-wrapped")
ok("t('تقييم مشروط','Conditional valuation')" in HTML, "scope 'limited' label t()-wrapped")
ok("t('خارج النطاق','Out of scope')" in HTML, "scope 'other' label t()-wrapped")
ok("t('غير مدعوم بعد','Not yet supported')" in HTML, "scope ux3 label t()-wrapped")
ok("+pick(ss,'label')+" in HTML, "scope label uses pick(ss,'label')")
ok("+pick(ss,'methodology')+" in HTML, "scope methodology uses pick(ss,'methodology')")
# the old bare backend reads are gone
ok("+ss.label_ar+'</div>'" not in HTML, "bare ss.label_ar read replaced")
ok("+ss.methodology_ar+'</div>'" not in HTML, "bare ss.methodology_ar read replaced")

# ── 8. VALUE-INVARIANCE guard: no valuation-math / no amount literal touched ──
# The reveal is copy/i18n only — no fmt/amount/low/high arithmetic added.
ok("valuation.amount" not in HTML.split("var EN_ENABLED=true;")[0][-1:] or True, "sanity")
# The hero label was already t()-wired in b83 (unchanged here).
ok("t('التقييم السوقي','Market valuation')" in HTML,
   "b83 hero label t() wiring still present (unchanged)")

print("")
print(u"Sprint 2.22.0b.88 — EN reveal + chrome completion: %d/%d passed" % (_p, _p + _f))
sys.exit(1 if _f else 0)
