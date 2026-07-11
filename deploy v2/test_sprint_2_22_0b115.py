# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.115 (frontend — perceived latency: a skeleton screen during the GIS wait). 🟢 FRONTEND-ONLY /
VALUE-INVARIANT (the loading state only; the real result still renders via show()). `api.py` + engine untouched.

The PO chose «زمن الاستجابة أولاً»; b114 removed the compute hotspot, leaving ~7s of network wait. This slice
replaces the bare text spinner with a SHIMMERING SILHOUETTE of the incoming result card (navy hero + range
bar + chips) — the "skeleton screen" pattern reads faster than a spinner + matches the premium brand — while
keeping the honest step narrative + elapsed timer (+ «نفحص كلّ صفقةٍ مسجّلة» — the wait is part of the accuracy,
not a fake progress count). Reduced-motion falls back to a static pulse.
"""
import io, sys

_p = _f = 0
def ck(name, cond, extra=''):
    global _p, _f
    if cond: _p += 1; print(f'  ok  {name}')
    else:    _f += 1; print(f'  FAIL {name}  {extra}')

H = io.open('index.html', encoding='utf-8').read()

# ── (1) the skeleton CSS (shapes + shimmer + reduced-motion fallback) ──
ck('.skl-hero uses the brand navy (var(--primary))', '.skl-hero{background:var(--primary)' in H)
ck('.skl-line shapes present (lbl/big/bar)', '.skl-line.lbl{' in H and '.skl-line.big{' in H and '.skl-line.bar{' in H)
ck('.skl-chip placeholders present', '.skl-chip{' in H)
ck('.skl-sh shimmer + skl-sweep keyframe', '.skl-sh{' in H and '@keyframes skl-sweep{' in H and 'animation:skl-sweep' in H)
ck('reduced-motion fallback: shimmer→static + lbar→static',
   '@media(prefers-reduced-motion:reduce){.skl-sh{animation:none' in H and '.lprog .lbar::after{animation:none' in H)

# ── (2) R6/Lesson-2 (b127, S2): the skeleton loading was SUPERSEDED by the «لحظة الكشف» reveal moment.
#    run() no longer builds .skl / renderLoading / the lprog narrative — the milestone-driven reveal card
#    (.rvl) is the loading UI now (the .skl CSS above is retained dormant). See test_sprint_2_22_0b127.py.
ck('(b127) run() builds the «لحظة الكشف» reveal card (.rvl), not the .skl skeleton',
   'fRes.innerHTML=\'<div class="rvl">' in H and 'class="rvl-card"' in H)
ck('(b127) the 4 milestone stages ARE the honest narrative (record → MoJ sales → estimate → weigh+range)',
   'نقرأ سجلّ العقار' in H and 'نطابق صفقات وزارة العدل' in H and 'نحسب التقدير من الشواهد' in H and 'نوازن الأدلّة ونُحكِم النطاق' in H)

# ── (3) value-invariance: the result still renders via show() + value-neutral loading ──
ck('the result still renders via show(d) then clears the loading (fRes.innerHTML=\'\')',
   'show(d);' in H and "fRes.innerHTML='';" in H)
ck('api.py / engine untouched — the loading is display-only (no fetch/body change)',
   "window._lastSubmit={endpoint:'/api/evaluate'" in H and "body:JSON.stringify(bd)" in H)

print(f'\nb115 (skeleton): {_p} passed, {_f} failed')
sys.exit(1 if _f else 0)
