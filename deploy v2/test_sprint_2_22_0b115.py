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

# ── (2) renderLoading renders the skeleton + keeps the honest narrative ──
ck('renderLoading builds the .skl block (hero + chips)',
   "fRes.innerHTML='<div class=\"skl\">'" in H and 'skl-hero' in H and 'skl-chips' in H)
ck('the honest step narrative + elapsed are KEPT under the skeleton',
   "'<div class=\"lprog\" style=\"margin-top:12px\"><div class=\"lstep\">'+steps[Math.min(stepIdx,steps.length-1)]" in H)
ck('the honest «نفحص كلّ صفقةٍ مسجّلة» line (bilingual — the wait is the accuracy, not fake progress)',
   'نفحص كلّ صفقةٍ مسجّلة' in H and 'we check every registered sale' in H)
ck('the 4 honest GIS steps are unchanged (GIS/MoJ/location/report)',
   'نتحقق من العنوان في خرائط GIS' in H and 'نبحث في سجل وزارة العدل عن صفقات مماثلة' in H)

# ── (3) value-invariance: the result path + clear are untouched ──
ck('the result still renders via show(data) then clears the loading (fRes.innerHTML=\'\')',
   'show(data);' in H and "fRes.innerHTML='';" in H)
ck('api.py / engine untouched is a backend claim — here we only assert the loading is display-only (no fetch/body change)',
   "window._lastSubmit={endpoint:'/api/evaluate'" in H and "body:JSON.stringify(bd)" in H)

print(f'\nb115 (skeleton): {_p} passed, {_f} failed')
sys.exit(1 if _f else 0)
