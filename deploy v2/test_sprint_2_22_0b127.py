# -*- coding: utf-8 -*-
"""
Sprint 2.22.0b.127 (S2, redesign v2) — «لحظة الكشف» the animated reveal moment.

🟢 FRONTEND-ONLY / VALUE-NEUTRAL. run()'s loading state (the b115 skeleton) is replaced by the designer's
milestone-driven reveal (`design_handoff_thammen/ثمّن - الإدخال والكشف والتحسين.dc.html` + ANSWERS Q15/Q16):
a navy computing card (4 stages with checkmarks + progress + spinner) → a number count-up + range bar → auto-
opens the result. The number reveals ONLY from the real response (count-up → v.amount, range from v.low/high,
«N صفقة» from v.n_transactions) — never an invented number. >15s → reassurance; failure → retry/try-later;
reduced-motion → instant. This RETIRES the confirm gate (reveal → show(d) → results); showConfirm/confirmScreen
stay in source but DORMANT. `api.py` + the valuation engine untouched (version lines only).

E14: reads the REAL index.html + evaluate_unified.py.
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
H = io.open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
ENG = io.open(os.path.join(ROOT, 'evaluate_unified.py'), encoding='utf-8').read()

# run() body slice (up to the final \n} at column 0 — nested arrows are indented so they don't match).
_r = re.search(r'async function run\(\)\{.*?\n\}', H, re.S)
RUN = _r.group(0) if _r else ''
RUNc = RUN.replace(' ', '')

_p = _f = 0
def ck(name, cond, extra=''):
    global _p, _f
    if cond: _p += 1; print(f'  ok  {name}')
    else:    _f += 1; print(f'  FAIL {name}  {extra}')

# ── (1) reveal-moment CSS (navy card + spinner + result + failure + keyframes + reduced-motion) ──
ck('.rvl-card is the navy hero card (var(--primary))', '.rvl-card{background:var(--primary)' in H)
ck('.rvl-spin / .rvl-core / .rvl-ring present (computing spinner)', '.rvl-spin{' in H and '.rvl-core{' in H and '.rvl-ring{' in H)
ck('.rvl-step / .rvl-dot present (milestone checkmark rows)', '.rvl-step{' in H and '.rvl-dot{' in H and '.rvl-dot.done{' in H)
ck('.rvl-num uses the 7-step scale clamp (44–52) tabular-nums', '.rvl-num{font-size:clamp(38px,8vw,52px)' in H and 'tabular-nums' in H)
ck('.rvl-range + .rvl-rfill (range bar, scaleX)', '.rvl-range{' in H and '.rvl-rfill{' in H and 'transform:scaleX(0)' in H)
ck('.rvl-err failure card present', '.rvl-err{' in H and '.rvl-err .retry{' in H and '.rvl-err .later{' in H)
ck('keyframes thSpin / thRing / thPop', '@keyframes thSpin{' in H and '@keyframes thRing{' in H and '@keyframes thPop{' in H)
ck('reduced-motion guard on the reveal animations', '@media(prefers-reduced-motion:reduce){.rvl-ring{animation:none' in H)

# ── (2) run() builds the reveal card + the 4 milestone stages (t()-wrapped) ──
ck('run() builds the «لحظة الكشف» reveal card (.rvl / .rvl-card / .rvl-body)',
   'fRes.innerHTML=\'<div class="rvl">' in RUN and 'class="rvl-card"' in RUN and 'class="rvl-body"' in RUN)
ck('the 4 milestone stages are t()-wrapped (bilingual) — honest for EVERY leader/asset',
   "t('نقرأ سجلّ العقار…','Reading the property record…')" in RUN and
   "t('نطابق صفقات وزارة العدل…','Matching Ministry of Justice sales…')" in RUN and
   "t('نحسب التقدير من الشواهد…','Computing the estimate from the evidence…')" in RUN and
   "t('نوازن الأدلّة ونُحكِم النطاق…','Weighing the evidence and finalizing the range…')" in RUN)
ck('honesty (owner-caught): stages do NOT claim a cost/income cross-check nor a bracket-median lead '
   '(false for cost-led 54% / land / refusal)',
   'نتحقّق بالتكلفة والدخل' not in RUN and 'الوسيط الشريحيّ' not in RUN)
ck('the identity line is value-neutral (from the submitted address/PIN, esc-wrapped)',
   'esc(_ident)' in RUN and 'bd.pin?' in RUNc)  # _ident derives from bd (zone/street/building or PIN)

# ── (3) VALUE-NEUTRAL: the number reveals ONLY from the real response, never an invented literal ──
ck('the reveal count-up target is v.amount (a broadcast field), via the b120 _countUp (lands on fmt(target))',
   'data-countup="\'+v.amount+\'"' in RUN and '_countUp(el,v.amount,1400)' in RUNc)
ck('the range is bound to v.low / v.high (no invented range)', 'fmt(v.low)' in RUN and 'fmt(v.high)' in RUN)
ck('the «N صفقة» chip is bound to v.n_transactions (fallback d.moj_sample_size), shown only when present',
   'v.n_transactions' in RUN and 'صفقة مسجّلة' in RUN)
ck('no hardcoded reveal amount (the designer demo 2400000 is NOT copied)', '2400000' not in RUN)

# ── (4) milestone-driven (designer Q15/Q16): reveal only when BOTH stages done AND data arrived ──
ck('the reveal fires only when the stages AND the real data are both ready',
   'if(_revealed||_failed||!_stagesDone||!_data)return;' in RUN)
ck('run() reveals from the real data (data → _data → _reveal)', '_data=data;_reveal();' in RUNc)
ck('the stages advance while the fetch is in flight (_adv started before the fetch resolves)',
   '_adv();' in RUN and RUN.index('_adv();') < RUN.index("await fetch(API+'/api/evaluate'"))
ck('milestone hold: the last stage waits (no fake full-then-frozen bar) — >15s reassurance line',
   "t('ما زلنا نطابق…','Still matching…')" in RUN and 'setTimeout(' in RUN)

# ── (5) explicit failure state (retry / try-later) ──
ck('failure state: honest title + retry(run()) + try-later',
   "t('تعذّر إكمال الحساب الآن','Could not complete the valuation now')" in RUN and
   'onclick="run()"' in RUN and "t('جرّب لاحقاً','Try later')" in RUN)

# ── (6) reduced-motion safety ──
ck('run() reads prefers-reduced-motion (_rd) and paces the stages accordingly',
   "matchMedia('(prefers-reduced-motion:reduce)').matches" in RUN and '_rd?150:900' in RUNc)

# ── (7) RETIRE the confirm gate — reveal → results; refusal → results ──
ck('run() no longer routes to the confirm gate', "go('confirm')" not in RUN)
ck('run() → results (the reveal is the transition)', "go('results')" in RUN)
ck('refusal / no amount → straight to results (no number reveal)',
   "if(v.amount==null||!(v.amount>0)){show(d);fRes.innerHTML='';go('results');return;}" in RUN)

# ── (8) value-invariance: the real result still renders via show(); showConfirm kept DORMANT ──
ck('the real result screen still renders via show(d)', 'show(d);' in RUN)
ck('exactly ONE fetch in run() (no 2nd call)', RUN.count("await fetch(API+'/api/evaluate'") == 1)
ck('showConfirm / confirmScreen kept in source but dormant (content tests stay green)',
   'function showConfirm(d){' in H and 'id="confirmScreen"' in H)

# ── (9) version ──
ck('ENGINE_VERSION bumped to b127', "thammen-sprint2p22p0b127" in ENG and "'2.22.0b.127'" in ENG)

print(f'\nb127 (reveal moment): {_p} passed, {_f} failed')
sys.exit(1 if _f else 0)
