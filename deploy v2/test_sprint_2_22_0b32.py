# -*- coding: utf-8 -*-
# Sprint 2.22.0b.32 — DEF-UX13: simplify the confirmation screen.
# FRONTEND-ONLY, value-invariant (engine = the 2 version-string lines only). Reads the REAL
# index.html (E14 / Rule #40 for the frontend lane) + asserts the engine version bump.
#
# What this verifies (study §3 «من التأكيد» kill-list 17-20 + «يبقى على التأكيد» line):
#   (17) the E15 setbacks equation → a hover tooltip; the max-buildable NUMBER + «عدّله» CTA stay.
#   (18) the full evidence panel is DROPPED from the confirm screen (it lives on the result,
#        inside the b31 «كيف وصلنا لهذا الرقم؟» accordion). No pill substitute.
#   (19) the survey-vintage age moves out of the confirm view (the message already lives at
#        the refine «عمر البناء» field — the move is a move, not a loss).
#   (20) the utility numbers (electricity/water) move out of the confirm default view.
#   KEEP on confirm: basis review (address/zone/area + cadastral id) + muted preliminary range
#        + confirm button + the full-report escape.
# Value-invariant by construction: only the confirm-screen presentation changed; pbRows stays
# byte-identical on its other (results/report) call-sites; no v.amount/low/high is touched.
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
ENG = (ROOT / 'evaluate_unified.py').read_text(encoding='utf-8')

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# Helper: isolate the showConfirm() body (between its `function showConfirm(d){` and the next
# top-level `function confirmProceed(`), so panel-removal assertions are scoped to the screen.
_sc_start = HTML.index('function showConfirm(d){')
_sc_end = HTML.index('function confirmProceed(', _sc_start)
SHOWCONFIRM = HTML[_sc_start:_sc_end]

# ── 0. engine version follows the sprint-tag format (R6/Lesson-2: no exact version
#       pins — b32's literal pin was re-pointed to a format check when b33 bumped the
#       tag; b32 is a frontend/value-invariant sprint, so any later tag is valid here) ──
check('ENGINE_VERSION has the sprint-tag format', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric format', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)
check('no stale b31 engine tag left in evaluate_unified.py', "sprint2p22p0b31-tier1-howfold" not in ENG)

# ── (18) full evidence panel DROPPED from the confirm screen ──
check('showConfirm() no longer calls evidencePanelHtml', 'evidencePanelHtml' not in SHOWCONFIRM)
check('no pill substitute injected on confirm (study §3 «لا لوحة أدلّة»)', '_evOneRow' not in SHOWCONFIRM)
# the panel function itself MUST survive — it is still used on the result + the report.
check('evidencePanelHtml() function still defined', 'function evidencePanelHtml(d,acc){' in HTML)
check('evidence panel still on the RESULT (b31 «كيف وصلنا» accordion)',
      # b34 (DEF-UX12) added a 3rd `open` arg (role density) — match without the trailing `);`
      "t2+=_acc('🔍 كيف وصلنا لهذا الرقم؟', how+evidencePanelHtml(d,acc)" in HTML)
check('evidence panel still in the full REPORT (numbered annex)',
      '_axWrap(evidencePanelHtml(d,acc))' in HTML)

# ── (17) setbacks equation → tooltip; number + «عدّله» CTA stay ──
check('confirm: max-buildable NUMBER stays', "'≈ '+fmt(geo.max_buildable_footprint_m2)+' م²'" in SHOWCONFIRM)
check('confirm: «عدّله» CTA stays', 'عدّله في خطوة التحسين' in SHOWCONFIRM)
check('confirm: setbacks formula moved to a title tooltip', 'class="cg-tip"' in SHOWCONFIRM and 'title="' in SHOWCONFIRM)
check('confirm: tooltip carries the E15 setbacks formula',
      'بعد الارتدادات القانونية (أمامي 5 · جانبي 3 · خلفي 3) وضمن سقف تغطية 60%' in SHOWCONFIRM)
# the OLD inline form (dims as an on-screen dir=ltr span + inline «بعد الارتدادات») is gone.
check('confirm: OLD inline setbacks span removed',
      "</span> م بعد الارتدادات القانونية:" not in SHOWCONFIRM)
check('confirm: shared-parcel detail also tooltip-only (no inline parenthetical)',
      "' (حصة الوحدة في قطعة مشتركة'" not in SHOWCONFIRM)
# LRM (U+200E) wraps the dims expression inside the tooltip string (Rule #25 bidi).
check('confirm: dims wrapped in LRM inside the tooltip', SHOWCONFIRM.count('‎') >= 2)

# ── (19)+(20) survey-age + utilities move out of the confirm view; PIN stays ──
check('pbRows() gains the basisOnly param', 'function pbRows(pb, basisOnly){' in HTML)
# the cadastral id (PIN) is printed BEFORE the basisOnly early-return → it survives on confirm.
_pb_start = HTML.index('function pbRows(pb, basisOnly){')
_pb_body = HTML[_pb_start:_pb_start+700]
_pin_at = _pb_body.index("ri('الرقم المساحي'")
_ret_at = _pb_body.index('if(basisOnly)return h;')
_elec_at = _pb_body.index("ri('رقم الكهرباء'")
check('pbRows: PIN printed BEFORE the basisOnly early-return (stays on confirm)', _pin_at < _ret_at)
check('pbRows: utilities + age AFTER the early-return (hidden on confirm)', _ret_at < _elec_at)
check('pbRows: age-estimate row is after the early-return too',
      _ret_at < _pb_body.index('building_age_estimate'))
check('confirm calls pbRows in basis-only mode', 'pbRows(d.property_basis,true)' in SHOWCONFIRM)
# the OTHER call-sites stay full (no flag) → byte-identical pbRows there.
check('results pbRows call-site unchanged (full panel)', HTML.count('pbRows(d.property_basis)') >= 2)
check('refine carries the age hint (so (19) is a MOVE, not a loss)',
      'العمر المسجَّل في النظام حدٌّ أدنى' in HTML)

# ── KEEP-list: the confirm screen still has its four owner essentials ──
check('confirm keeps: basis review card', 'راجِع بيانات العقار' in SHOWCONFIRM)
check('confirm keeps: address row', "ri('العنوان'" in SHOWCONFIRM)
check('confirm keeps: zoning/area rows', "ri('المنطقة'" in SHOWCONFIRM and ('المساحة المعتمدة في التقدير' in SHOWCONFIRM or 'مساحة القسيمة' in SHOWCONFIRM))
check('confirm keeps: muted preliminary range', 'تقدير مبدئي (نطاق)' in SHOWCONFIRM)
check('confirm keeps: confirm button', 'تابِع بهذه البيانات' in SHOWCONFIRM)
check('confirm keeps: full-report escape', "go('results')" in SHOWCONFIRM.replace("\\'","'"))

# ── value-invariance guard: the confirm changes touch NO value-building expression ──
check('no v.amount / low / high mutation in showConfirm', not re.search(r'v\.(amount|low|high)\s*=', SHOWCONFIRM))

# ── summary ──
passed = sum(1 for _, ok in results if ok)
total = len(results)
for name, ok in results:
    print(('PASS' if ok else 'FAIL'), '-', name)
print('\n%d/%d passed' % (passed, total))
raise SystemExit(0 if passed == total else 1)
