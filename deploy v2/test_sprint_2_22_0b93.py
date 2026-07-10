# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.93 «الفخامة + مرآة الحاضنة» — isolated tests (E14: reads the REAL files).

(a) luxury hero chrome (Gemini r7 #3): a LOCAL data-URI cadastral watermark (~4% opacity —
    zero CDN, the b45 lock) + a champagne-gold hairline ring with a slow sheen, on BOTH navy
    heroes (.rhero + .thmr-hero.lux) — one نسق; reduced-motion respected;
(b) the b92 tiered-bracket mirrored onto the result-screen rhero range bar (same edge-pinned
    dot defect); the b48 rbar is KEPT VERBATIM for the central case (pins survive);
(c) VALUE-INVARIANT (CSS + a display branch; amount/low/high/method/rule untouched).
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

# ── (a) luxury chrome ──
# b124 (S4a redesign) re-point (R6/Lesson-2): the RESULT hero moved from a navy band to a WHITE
# value card (design handoff, PO-signed) → the navy luxury chrome (cadastral watermark + champagne
# sheen) no longer fits it and now lives ONLY on the navy REPORT hero (.thmr-hero.lux). The white
# card carries a bronze top-rule instead. Zero value/compliance weakened — this is a deliberate
# design evolution, not a removal (the chrome is intact on .thmr-hero.lux, asserted below at 25-30).
check('luxury chrome selector on the navy REPORT hero (.thmr-hero.lux)', '.thmr-hero.lux{position:relative;overflow:hidden}' in HTML)
check('white result card carries a bronze top-rule instead of navy chrome',
      '.rhero::before{content:\'\';position:absolute;top:0;right:0;left:0;height:3px;background:linear-gradient(90deg,transparent,var(--bronze),transparent)}' in HTML)
check('cadastral watermark = LOCAL data-URI SVG (no CDN)', 'background-image:url("data:image/svg+xml,' in HTML)
check('watermark subtle (opacity .04)', 'pointer-events:none;opacity:.04;background-image' in HTML)
check('champagne hairline ring (gradient border, gold rgba)', 'rgba(232,201,154,.7)' in HTML and 'mask-composite:exclude' in HTML)
check('slow sheen animation', '@keyframes luxsheen' in HTML and 'animation:luxsheen 9s linear infinite' in HTML)
check('reduced-motion respected', 'prefers-reduced-motion:reduce' in HTML and 'animation:none' in HTML)
check('short-report hero carries the lux class', '\'<div class="thmr-hero lux" style="background:var(--thmr-navy);border:none">\'' in HTML)

# ── (b) rhero tiers mirror ──
i = HTML.index("t1+='<div class=\"rng\">'")
SEG = HTML[i-200:i+2600]
check('rhero skew gate mirrors b92 (_hpct<20||_hpct>80)', '_hpct<20||_hpct>80' in SEG.replace(' ', ''))
check('rhero marker clamped 18..82', 'Math.max(18,Math.min(82,_hpct))' in SEG)
check('rhero tiers carry the floor/ceiling labels', "t('الأرضية السعرية','Price floor')" in SEG and "t('السقف السوقي','Market ceiling')" in SEG)
check('rhero honest legend gated to cost/geo_full',
      "_ldr2.leader==='cost'||_ldr2.rule==='geo_full'" in SEG.replace(' ', ''))
check('the b48 rbar KEPT VERBATIM in the else branch',
      't1+=\'<div class="rbar"><div class="track"><span class="dot c" style="right:\'+_hpct+\'%"></span></div>\';' in HTML)

# ── (c) value-invariance ──
check('no new v.amount multiplication introduced by the mirror', 'v.amount*' not in SEG.replace(' ', '').replace('v.amount*0.90','').replace('v.amount*1.10','').replace('v.amount*1.30',''))
check('no assignment into v.amount/low/high in the mirror', not re.search(r'v\.(amount|low|high)\s*=[^=]', SEG))

# ── version ──
check('ENGINE_VERSION b-series format (R6 — no exact version pin)',
      re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+b\d+-", ENG) is not None)

print(f'\n{passed}/{passed+failed} PASS' + ('' if failed == 0 else f' — {failed} FAIL'))
sys.exit(1 if failed else 0)
