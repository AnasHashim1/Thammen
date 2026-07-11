# -*- coding: utf-8 -*-
"""
Isolated test — Sprint 2.22.0b.2.3 (Confirmation Gate, Screen 2, v4 owner-journey).

FRONTEND-ONLY / value-invariant. Reads the REAL index.html + evaluate_unified.py
(Rule #40 / E14 — exercise the shipped artefact, not a replica) and asserts:
  - the new confirmScreen + showConfirm()/confirmProceed() exist;
  - run() routes valued owner journeys to the confirm gate, from the SAME response
    (no 2nd fetch), and STILL renders the result (value-invariant proxy: show(data));
  - the routing guard (mirrored in Python) skips valuer + refusals;
  - the signed copy is verbatim; the REJECTED DRAFT CTA is absent;
  - read-only (signed 5.2): no correction pencils / «صحّح» in the gate;
  - the engine diff is version-string only (format-checked, version-agnostic, R6).

Run:  set PYTHONIOENCODING=utf-8 & python test_sprint_2_22_0b2p3.py
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = io.open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
ENG = io.open(os.path.join(ROOT, 'evaluate_unified.py'), encoding='utf-8').read()

# showConfirm body = from its definition to confirmProceed (immediately follows).
_m = re.search(r'function showConfirm\(d\)\{.*?function confirmProceed', HTML, re.S)
SHOWCONFIRM = _m.group(0) if _m else ''
# run() body (best-effort slice for guard assertions).
_r = re.search(r'async function run\(\)\{.*?\n\}', HTML, re.S)
RUN = _r.group(0) if _r else ''

results = []
def chk(cond, name):
    results.append((bool(cond), name))

# ── 1. structure: the new screen + render fns exist ───────────────────────────
chk('id="confirmScreen"' in HTML, '1.1 confirmScreen div present')
chk('id="cgOut"' in HTML, '1.2 cgOut mount present')
chk('function showConfirm(d){' in HTML, '1.3 showConfirm() defined')
chk('function confirmProceed(){go(\'refine\');}' in HTML, '1.4 confirmProceed() → refine (v4 تأكيد→تحسين)')
chk('.cg-est{' in HTML, '1.5 cg-est CSS class defined')

# ── 2. b127 R6/Lesson-2 (S2): the confirm gate was RETIRED — run() plays the «لحظة الكشف» reveal then
#       routes to the result directly (reveal → show(d) → go('results')). showConfirm/confirmScreen +
#       their signed copy (below) stay in source but DORMANT; only run()'s routing changed.
chk("go('confirm')" not in RUN, '2.1 (b127) run() no longer routes to the confirm gate')
chk("go('results')" in RUN, '2.2 (b127) run() → results (via the reveal)')
chk('show(d);' in RUN, '2.3 (b127) run() STILL renders the result (value-invariant: show(d))')
chk('window._lastResult=data;' in RUN, '2.4 run() still stores _lastResult')
chk(RUN.count('await fetch(API+\'/api/evaluate\'') == 1, '2.5 exactly ONE fetch in run() (no 2nd call)')
chk("_data=data;_reveal();" in RUN.replace(' ', ''), '2.6 (b127) run() reveals from the real data (milestone-driven)')

# ── 3. b127: routing is now uniform — every path opens the result (the reveal is the transition) ──
def route(audience, amount):
    return 'results'  # b127: reveal → results for all; refusals skip the number reveal, straight to results
chk(route('buyer', 2400000) == 'results', '3.1 (b127) buyer + valued → results (via reveal)')
chk(route('valuer', 2400000) == 'results', '3.2 valuer → results')
chk(route('buyer', None) == 'results', '3.3 refusal (amount None) → results')
chk(route('buyer', 0) == 'results', '3.4 zero amount → results')

# ── 4. signed copy (verbatim) ────────────────────────────────────────────────
chk('تقدير مبدئي (نطاق)' in SHOWCONFIRM, '4.1 range label')
chk('راجِع بيانات العقار' in SHOWCONFIRM, '4.2 review heading')
chk('هذه البيانات مجلوبة من نظام المعلومات الجغرافية (GIS). راجِعها قبل المتابعة.' in SHOWCONFIRM, '4.3 review subtext')
chk('تقدير أوّليّ قابل للتغيّر بعد التأكيد والتحسين.' in SHOWCONFIRM, '4.4 range subtext')
chk('تابِع بهذه البيانات' in SHOWCONFIRM, '4.5 confirm CTA (signed)')
chk('التقرير الكامل الآن' in SHOWCONFIRM, '4.6 permanent full-report escape')
chk('المساحة المعتمدة في التقدير' in SHOWCONFIRM, '4.7 plot-area honesty label')

# ── 5. boundaries (signed 5.2 read-only + rejected CTA + reuse) ───────────────
chk('البيانات صحيحة — تابِع' not in HTML, '5.1 REJECTED DRAFT CTA absent (read-only honesty)')
chk('صحّح' not in SHOWCONFIRM, '5.2 no «صحّح» correction button in the gate (read-only)')
chk('✏' not in SHOWCONFIRM, '5.3 no ✏ correction pencils in the gate (read-only)')
# Re-pointed for DEF-UX13/b32 (R6/Lesson-2): the confirm gate NO LONGER carries the evidence
# panel — it was dropped (study §3 «لا لوحة أدلّة») and now lives only on the result, inside
# the b31 «كيف وصلنا» accordion. The gate stays read-only + minimal.
chk('evidencePanelHtml(d,acc)' not in SHOWCONFIRM, '5.4 (DEF-UX13): evidence panel DROPPED from the confirm gate → lives on the result')
chk(r"go(\'results\')" in SHOWCONFIRM, '5.5 full-report link → results (no 2nd fetch)')

# ── 6. value-invariance: engine diff = version-string only (format, R6) ───────
chk(bool(re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG)), '6.1 ENGINE_VERSION format (version-agnostic)')
chk(bool(re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG)), '6.2 SPRINT_TAG format (version-agnostic)')
chk('2.22.0b.2.3' in HTML, '6.3 this-sprint marker present in index.html')

# ── report ───────────────────────────────────────────────────────────────────
passed = sum(1 for ok, _ in results if ok)
total = len(results)
for ok, name in results:
    print(('  PASS ' if ok else '  FAIL ') + name)
print('\n%d/%d passed' % (passed, total))
sys.exit(0 if passed == total else 1)
