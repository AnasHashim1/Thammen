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
# 3. range headline uses the big .rv hl 1.5rem class (unique pairing with the new label).
check('range in .rv hl 1.5rem',
      'النطاق التقديري السوقي</div><div class="rv hl" style="font-size:1.5rem">' in HTML)
# 4. median is a MUTED .rn marker, labelled as the central estimate.
check('median muted .rn marker «الوسيط (التقدير المركزي)»',
      'font-size:.84rem">الوسيط (التقدير المركزي) ≈ <strong>' in HTML)
# 5. asymmetry-safe gate (low!=null && high!=null) — matches the showConfirm prototype.
check('gate v.low!=null&&v.high!=null', 'if(v.low!=null&&v.high!=null){' in HTML)
# 6. point FALLBACK retained (else branch keeps «القيمة التقديرية» as the point headline).
check('point fallback «القيمة التقديرية» + fmt(v.amount)',
      "القيمة التقديرية</div><div class=\"rv hl\" style=\"font-size:1.5rem\">'+fmt(v.amount)+' ر.ق</div></div>'" in HTML)
# 7. reference comment present (confirms the swap block landed as a unit).
check('b3 reference comment present', 'Sprint 2.22.0b.3 (range-as-lead' in HTML)
# 8. the OLD two-box .rg headline range is GONE. «الحد الأدنى» was UNIQUE to that block
# (grep count 0 now); «الحد الأعلى» is NOT checked here — it legitimately persists in the
# range_expansion card («الحد الأعلى يَتسع…»), unrelated to the removed headline two-box.
check('old headline two-box removed («الحد الأدنى» gone)', 'الحد الأدنى' not in HTML)

# Value-invariant neighbours UNTOUCHED:
check('condition_note_ar still rendered', 'condition_note_ar' in HTML)
check('value_floor (B-1) secondary, still rendered', 'value_floor' in HTML and 'land_floor_note_ar' in HTML)
check('evidence panel (b2.2) still called', 'evidencePanelHtml(d,acc)' in HTML)
check('showConfirm (b2.3) still range-led', 'cg-range' in HTML and 'الوسيط ≈' in HTML)

# Engine version present + well-formed — R6 / Lesson-2: NOT an exact pin (an exact b3
# pin here broke when the b4 teardown sprint bumped the version; scope to FORMAT only).
check('ENGINE_VERSION format (thammen-sprint…)', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)

passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, len(results)))
assert passed == len(results), '%d FAILED' % (len(results) - passed)
