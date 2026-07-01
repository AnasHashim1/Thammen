# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.95 «شارة الفرز المبدئيّ» (م٢, SIGNED §6) — isolated tests (E14).

The preliminary-subdivision indicator on the LAND face — DISPLAY-ONLY, conservative:
- gate: area>=800 + the b10 plot_dims_m broadcast (rectangular);
- corner: both frontages ARE the two dims (adjacent edges) → decidable 12/12;
- non-corner: the street edge is ONE of the dims → claim ONLY when even min(dims)>=24
  (undecidable → NOTHING — no semi-strong claim on a guess);
- frontages NEVER summed (SIGNED §6); N = MIN(floor(area/400), floor(frontage/12)), N>=2;
- the SIGNED §5 cautious microcopy + Arabic dual/plural agreement (linguist persona).
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML = open('index.html', encoding='utf-8').read()
ENG  = open('evaluate_unified.py', encoding='utf-8').read()

i = HTML.index('function showShortReport(d){')
j = HTML.find('\nfunction ', i + 10)
SR = HTML[i:j if j != -1 else len(HTML)]
k = SR.index('const _dims=(v.geometry||{}).plot_dims_m')
SUB = SR[k:k+1800]

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print('PASS |', name)
    else:    failed += 1; print('FAIL |', name)

check('subdiv logic lives in the LAND branch only', SR.index('if(_isLand){') < k < SR.index('}else{', SR.index('if(_isLand){')))
check('area gate >= 800 (SIGNED §6)', '_area>=800' in SUB)
check('requires the b10 rectangular dims broadcast', "_dims&&_dims.length===2" in SUB)
check('corner rule: BOTH frontages >= 12', '_dMax>=12&&_dMin>=12' in SUB)
check('non-corner conservative: claim only when min(dims) >= 24', 'else if(_dMin>=24)_front=_dMin;' in SUB)
check('frontages never summed', '+_dims[0]+_dims[1]' not in SUB.replace(' ','') and '_dMax+_dMin' not in SUB.replace(' ',''))
check('N = MIN(area/400, frontage/12) (SIGNED §6)', 'Math.min(Math.floor(_area/400),Math.floor(_front/12))' in SUB)
check('renders only at N >= 2', 'if(_N>=2){' in SUB)
check('SIGNED §5 cautious microcopy (municipality approval clause)',
      'يخضع لقوانين الارتدادات وموافقة التخطيط العمرانيّ بوزارة البلدية' in SUB)
check('Arabic dual agreement («قطعتين» for N=2)', "(_N===2)?t('قطعتين','2 parcels')" in SUB)
check('plural «قطع» 3..10 / «قطعة» 11+', "_N<=10?t(_N+' قطع'" in SUB and "t(_N+' قطعة'" in SUB)
check('rides under the chips, gated on presence', "if(_subdivLn)h+=_subdivLn;" in SR)
check('.thmr-sub CSS present', '.thmr-sub{' in HTML)

# value-invariance
mults = re.findall(r'v\.amount\s*\*\s*([0-9.]+)', SR)
check('value-math still = ONLY the 3 disclosed conventions', sorted(set(mults)) == ['0.90', '1.10', '1.30'])
check('no assignment into v.amount/low/high', not re.search(r'v\.(amount|low|high)\s*=[^=]', SR))
check('ENGINE_VERSION b-series format (R6)', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+b\d+-", ENG) is not None)

print(f'\n{passed}/{passed+failed} PASS' + ('' if failed == 0 else f' — {failed} FAIL'))
sys.exit(1 if failed else 0)
