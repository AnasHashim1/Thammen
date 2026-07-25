# -*- coding: utf-8 -*-
# Sprint 2.22.0b.124 (S4a, redesign v2) — the RESULT-SCREEN white value card (design handoff).
# FRONTEND-ONLY / VALUE-INVARIANT: the result hero moves from a navy band to a clean WHITE card
# with a bronze top-rule — figure in navy, count-up animated, a REAL confidence meter from
# accuracy.score. The class name .rhero is KEPT (calc_visual pins it) — only its skin changes.
# The navy luxury chrome (b93) now lives ONLY on the report hero (.thmr-hero.lux). ALL honesty
# lines preserved verbatim (b3 range-as-lead, b92 tiered bracket, b64 cost-led, b72 e25, condition/
# teardown/luxury, MUC chip, «ليس تقييماً معتمداً», _evOneRow). No value math. E14: real index.html.
import io
H = io.open('index.html', encoding='utf-8').read()

_p = _f = 0
def check(name, cond):
    global _p, _f
    if cond: _p += 1
    else: _f += 1; print('  FAIL:', name)

# ── 1. WHITE card skin (the .rhero name kept, calc_visual-safe) ──
check('.rhero is now WHITE (var(--surface)), not navy',
      '.rhero{text-align:center;background:var(--surface);border:1px solid var(--border)' in H)
check('.rhero carries a bronze top-rule (::before)',
      ".rhero::before{content:'';position:absolute;top:0;right:0;left:0;height:3px;background:linear-gradient(90deg,transparent,var(--bronze),transparent)}" in H)
check('.rhero .num is NAVY (var(--primary)), figure-scale',
      '.rhero .num{font-size:clamp(44px,7vw,52px);font-weight:700;color:var(--primary)' in H)
check('.calc-block NOT applied (hero superseded it — calc_visual contract)', 'class="rc calc-block"' not in H)
check('the result hero opens with plain .rc then .rhero',
      "t1+='<div class=\"rc\">';" in H and "t1+='<div class=\"rhero\">" in H)

# ── 2. luxury chrome MOVED off the white card → report hero only (b93 evolution) ──
check('luxury watermark/sheen now on .thmr-hero.lux ONLY (not .rhero)',
      '.thmr-hero.lux{position:relative;overflow:hidden}' in H and
      '.rhero,.thmr-hero.lux{position:relative;overflow:hidden}' not in H)
check('luxsheen keyframes still present (report hero)', '@keyframes luxsheen' in H)
check('cadastral watermark kept (report hero, zero CDN)', '.thmr-hero.lux::before' in H and 'data:image/svg+xml' in H)

# ── 3. count-up on the figure (value-invariant) ──
check('hero figure wrapped in <span data-countup> (still fmt(v.amount))',
      "<span data-countup=\"'+(v.amount||0)+'\">'+fmt(v.amount)+'</span>" in H)
check('count-up driven after o.innerHTML (data-countup → _countUp)',
      "o.querySelectorAll('[data-countup]').forEach(function(el){_countUp(el,parseFloat(el.getAttribute('data-countup')),1300);});" in H)
check('_countUp exists (from S0) + lands on fmt(target)',
      'function _countUp(el,target,dur)' in H and 'const final=fmt(Math.round(target));' in H)

# ── 4. the CONFIDENCE METER — from the REAL accuracy fields, honest (hidden if absent) ──
check('confidence meter gated on a NUMERIC accuracy.score (no invented number)',
      "if(acc&&typeof acc.score==='number'&&isFinite(acc.score)){" in H)
check('score clamped 0..100', 'var _cscore=Math.max(0,Math.min(100,Math.round(acc.score)));' in H)
check('label read from the bare acc.label via pickBare (b146: attach_en emits label_en beside the bare key)',
      "var _clbl=pickBare(acc,'label');" in H)
check('explanation via pick (explanation_ar + _en when it lands)', "var _cexp=pick(acc,'explanation')||'';" in H)
check('explanation escaped (b57 XSS insurance)', "<div class=\"cnote\">'+esc(_cexp)+'</div>" in H)
check('score also counts up (data-countup on the /100 figure)',
      '<span class="cscore"><span data-countup="\'+_cscore+\'">' in H)
check('.rconf meter CSS present (bar + score + note)',
      '.rconf{' in H and '.rconf .cbar{' in H and '.rconf .cnote{' in H)
check('.rconf reduced-motion respected', '.rconf .cbar>i{animation:none}' in H)

# ── 5. b3 range-as-lead + b92 tiered bracket PRESERVED verbatim ──
check('range-as-lead kept — «النطاق التقديري السوقي»', 'النطاق التقديري السوقي' in H)
check('tiered-bracket skew gate kept (b92)', 'if(_hpct<20||_hpct>80){' in H)
check('floor/ceiling labels kept', "t('الأرضية السعرية','Price floor')" in H and "t('السقف السوقي','Market ceiling')" in H)
check('central rbar branch kept', "t1+='<div class=\"rbar\"><div class=\"track\"><span class=\"dot c\"" in H)

# ── 6. honesty lines PRESERVED verbatim (the designer's key ask) ──
check('b64 cost-led «اعتمدنا كلفةَ البناء» kept',
      "v.leadership&&v.leadership.leader==='cost'" in H and 'اعتمدنا كلفةَ البناء' in H)
check('b72 e25 «كلفةُ إعادة بناء بيتك … أعلى» kept',
      "rule==='e25_capped'" in H and 'كلفةُ إعادة بناء بيتك' in H)
check('condition / teardown / luxury notes kept',
      'if(v.condition_note_ar)' in H and 'v.teardown&&v.teardown.note_ar' in H and 'v.luxury_new_premium' in H)

# ── 7. compliance surfaces PRESERVED ──
check('MUC level chip kept («عدم اليقين الجوهري»)', 'عدم اليقين الجوهري: ' in H)
check('«ليس تقييماً معتمداً» line kept (t1, amber)',
      'ليس تقييماً معتمداً' in H and 'color:#8a6d3b;background:#fcf8e3' in H)
check('evidence one-row kept', 't1+=_evOneRow(d);' in H)
check('the b54 identity label «التقييم السوقي» kept on the hero',
      "<span class=\"lbl\">'+t('التقييم السوقي','Market valuation')+'</span>" in H)
check('.src-credit (report clone source) untouched in #resultsScreen',
      'class="src-credit"' in H)

# ── 8. VALUE-INVARIANCE: no new amount math; only display multipliers remain ──
check('no accuracy-derived value math (score is display-only)', 'acc.score*' not in H)
check('_srPayment (the one allowed value-math) untouched', 'function _srPayment(P,downPct,years,ratePct)' in H)

print('b124 (S4a): %d passed, %d failed' % (_p, _f))
raise SystemExit(1 if _f else 0)
