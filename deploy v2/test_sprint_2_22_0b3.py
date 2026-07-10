# -*- coding: utf-8 -*-
# Sprint 2.22.0b.3 — range-as-lead (§2b authority/finality dial-down).
# FRONTEND-ONLY, value-invariant (engine = version-string bump only). Reads the REAL
# index.html (E14 / Rule #40 for the frontend lane) + asserts the engine version bump.
# Verifies: the market RANGE is the results headline; the median is a MUTED central-
# estimate marker beneath it; the engine's TRUE (asymmetric-allowed) low/high are shown
# (NOT a forced symmetric ±, PHASE0 recon §1); point FALLBACK when no range; and the
# value-invariant neighbours (condition note, value_floor, evidence panel, showConfirm)
# are untouched. Anchors are unique full-file substrings (verified counts), no fragile
# block-splitting.
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# 1. range headline label is the new lead (unique — count 1).
check('range headline label «النطاق التقديري السوقي»', 'النطاق التقديري السوقي' in HTML)
# 2. headline shows the TRUE low–high ending in ' ر.ق' (distinct from showConfirm's cg-unit span).
check("headline = fmt(v.low) – fmt(v.high) ر.ق", "+fmt(v.low)+' – '+fmt(v.high)+' ر.ق" in HTML)
# 3. range-as-lead semantics KEPT-but-evolved (Sprint 2.22.0b.47 result-screen HERO): the
# market RANGE is presented as the lead range line on the navy hero band (the old big
# .rv hl 1.5rem result-screen headline was superseded by the hero — the report keeps its own).
check('range presented on the result HERO (.rng low–high)',
      "النطاق التقديري السوقي','Estimated market range')+' <b>'+fmt(v.low)+' – '+fmt(v.high)+'</b> '+t('ر.ق','QAR')" in HTML
      and 'class="rhero"' in HTML)
# 4. the central estimate (median = v.amount) is the CONFIDENT LEAD FIGURE in the hero .num
# band (b47 evolves the muted-marker form of b3 → a lead figure; the SHORT/FULL report keeps
# the «الوسيط (التقدير المركزي)» marker, asserted unchanged below).
# b124 (S4a redesign) re-point (R6/Lesson-2): the hero figure is now count-up-animated — the
# central number is wrapped in <span data-countup="…"> for the reveal, but STILL renders
# fmt(v.amount) as the lead hero figure. Same «figure leads» assertion, new wrapper; zero
# value/compliance weakened (fmt(v.amount) still leads .num on .rhero; the report marker below is
# unchanged). _NUM = the exact new emit shape.
_NUM = '<div class="num"><span data-countup="\'+(v.amount||0)+\'">\'+fmt(v.amount)+\'</span> <small>\'+t(\'ر.ق\',\'QAR\')+\'</small></div>'
check('central figure leads the result HERO (.num = fmt(v.amount), count-up-wrapped)',
      _NUM in HTML
      and 'الوسيط (التقدير المركزي)' in HTML)
# 5. asymmetry-safe gate (low!=null && high!=null) — matches the showConfirm prototype.
check('gate v.low!=null&&v.high!=null', 'if(v.low!=null&&v.high!=null){' in HTML)
# 6. point FALLBACK retained: the hero figure (.num) is ALWAYS present (b47 — fmt(v.amount)
# leads unconditionally), and the range line is the conditional part (gate v.low!=null). So a
# no-range result still shows the figure as the headline. (The report's «القيمة التقديرية»
# point-fallback line persists in showReport, asserted via the leadership-aware _def12R below.)
check('point fallback — figure always leads the hero, range conditional',
      _NUM in HTML
      and 'if(v.low!=null&&v.high!=null){' in HTML)
# 7. the b3 range-as-lead intent landed and is documented as KEPT-but-evolved (b47 superseded
# the original b3 comment when it restructured the result figure into the hero — R6/Lesson-2:
# pin the evolved-b3 semantics, not the volatile original comment literal).
check('b3 range-as-lead semantics present (kept-but-evolved by b47)', 'Evolves the signed b3' in HTML)
# 8. the OLD two-box .rg headline range is GONE. «الحد الأدنى» was UNIQUE to that block
# (grep count 0 now); «الحد الأعلى» is NOT checked here — it legitimately persists in the
# range_expansion card («الحد الأعلى يَتسع…»), unrelated to the removed headline two-box.
check('old headline two-box removed («الحد الأدنى» gone)', 'الحد الأدنى' not in HTML)

# Value-invariant neighbours UNTOUCHED:
check('condition_note_ar still rendered', 'condition_note_ar' in HTML)
check('value_floor (B-1) secondary, still rendered', 'value_floor' in HTML and 'land_floor_note_ar' in HTML)
check('evidence panel (b2.2) still called', 'evidencePanelHtml(d,acc)' in HTML)
# Sprint 2.22.0b.24 (م0) re-point: the showConfirm median marker became LEADERSHIP-AWARE
# (cost-led → «مرتكز التكلفة»; «الوسيط» only on a true comparison median), so the literal
# 'الوسيط ≈' concatenation is gone — pin the behavior markers instead (range + mid marker
# + the median label still present as a conditional value).
check('showConfirm (b2.3) still range-led', 'cg-range' in HTML and 'cg-mid' in HTML and "'الوسيط'" in HTML)

# Engine version present + well-formed — R6 / Lesson-2: NOT an exact pin (an exact b3
# pin here broke when the b4 teardown sprint bumped the version; scope to FORMAT only).
check('ENGINE_VERSION format (thammen-sprint…)', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
