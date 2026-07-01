# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.24 — م0 «حزمة R13 النصية» (R13 first-screens text bundle).

Isolated checks against the REAL production files (Rule #40 / E14):
  1. Home surface: تقدير (not تقييم) on the hero tag + CTA button.
  2. Data-recency line: signed static default + the production _render_subtitle
     emits the same صيغة («بيانات وزارة العدل حتى {الشهر}»).
  3. Audience selector: signed label («من أنت؟ … الرقم واحد للجميع») + «مالك»
     restored as the DEFAULT first option; api boundary ACCEPTS owner/مالك; the
     engine normalizes owner→buyer (presentation only — zero value axis).
  4. Confirm screen: leadership-aware central-value label (cost → «مرتكز التكلفة
     (أرض + بناء مُهلَك)»; «الوسيط» only on a true comparison median; neutral
     «التقدير المركزي» otherwise) + the dual evidence line on cost leadership.
  5. Scope window: the Rule-#47 alias no longer DUPLICATES the «أرض سكنية» card
     (enumeration deduped by object identity; the alias itself intact) + the
     villa term unified to the app-canonical «فيلا منفردة».
  6. Numbering: live first-screens carry zero stale citations (2025 map guarded
     by the standing a8/a22 tests; re-asserted here for index.html).

Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b24.py
"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  PASS  {name}')
    else:
        FAIL += 1
        print(f'  FAIL  {name}  {detail}')


with open('index.html', encoding='utf-8') as f:
    HTML = f.read()

# showConfirm body, scoped (the b2p3 extraction pattern)
_m = re.search(r'function showConfirm\(d\)\{.*?function confirmProceed', HTML, re.S)
SHOWCONFIRM = _m.group(0) if _m else ''

print('\n[1] Home surface — تقييم (identity) not تقدير')  # b54 R6: تقدير→تقييم (identity lock)
check('hero tag = «تقييم عقارك في قطر»', 'تقييم عقارك في قطر' in HTML)  # b54 R6: تقدير→تقييم (identity lock)
check('old hero «تقدير عقارك في قطر» gone', 'تقدير عقارك في قطر' not in HTML)  # b54 R6: تقدير→تقييم (identity lock)
check('CTA = «ابدأ التقييم»', 'ابدأ التقييم' in HTML)  # b54 R6: تقدير→تقييم (identity lock)
check('old CTA «ابدأ التقدير» gone', 'ابدأ التقدير' not in HTML)  # b54 R6: تقدير→تقييم (identity lock)

print('\n[2] Data-recency line (signed صيغة)')
check('static default = «بيانات وزارة العدل حتى ديسمبر 2025»',
      'بيانات وزارة العدل حتى ديسمبر 2025' in HTML)
from data_freshness import _render_subtitle  # production fn (E14)
check("_render_subtitle('ديسمبر 2025') == the signed line",
      _render_subtitle('ديسمبر 2025') == 'بيانات وزارة العدل حتى ديسمبر 2025',
      repr(_render_subtitle('ديسمبر 2025')))
check('dynamic refresh keeps the same صيغة (no «آخر تحديث» drift)',
      'آخر تحديث' not in _render_subtitle('ديسمبر 2025'))

print('\n[3] Audience unification (b89 Option A — the «من أنت؟» role selector was REMOVED)')
# b89 R6 re-point: the 5-role selector was removed → one neutral entry. The number is
# audience-invariant (b24 doctrine), the hero label is neutral (b54/b88), so the upfront role
# step was pure friction (Gemini r6 + PO 2026-07-01). `audience` stays 'owner' by default (the
# engine normalizes owner→buyer → value-invariant); the routing guard + the input tab stay intact.
check('the ftitle «من أنت؟» role-grid header is REMOVED (no rendered role selector)',
      '<span data-en="Who are you?">من أنت؟</span>' not in HTML)
check('the role-grid label «(يحدّد طريقة العرض فقط — الرقم واحد للجميع)» is REMOVED',
      'يحدّد طريقة العرض فقط — الرقم واحد للجميع' not in HTML)
check('old label «نوع التقرير» still absent', 'نوع التقرير' not in HTML)
check('the «مالك» role button is REMOVED', "selAud(this,'owner')" not in HTML)
check('the «مشتري» role button is REMOVED', "selAud(this,'buyer')" not in HTML)
check('NO role button carries the default sel class (selAud role buttons gone)',
      re.search(r'<div class="aud-btn sel" onclick="selAud\(this,\'owner\'\)"', HTML) is None)
check('no buyer default-selected role button',
      re.search(r'selAud\(this,\'buyer\'\)', HTML) is None)
check("JS default audience = 'owner' (engine normalizes owner→buyer → value-invariant)",
      "let audience='owner'" in HTML)
check('none of the 5 role options remain', all(
    f"selAud(this,'{a}')" not in HTML for a in ('owner', 'buyer', 'seller', 'investor', 'valuer')))
check('the valuer skip-routing guard is intact (now always owner → short report)', "audience!=='valuer'" in HTML)

print('\n[4] api boundary accepts owner/مالك (production validator, E14)')
import api  # the real FastAPI module
check("'owner' in _AUDIENCE_ACCEPTED", 'owner' in api._AUDIENCE_ACCEPTED)
check("'مالك' in _AUDIENCE_ACCEPTED", 'مالك' in api._AUDIENCE_ACCEPTED)
check("_check_audience('owner') passes", api._check_audience('owner') == 'owner')
check("_check_audience('مالك') passes", api._check_audience('مالك') == 'مالك')
check("_check_audience('buyer') still passes", api._check_audience('buyer') == 'buyer')
try:
    api._check_audience('landlord_bogus')
    check("_check_audience rejects unknown ('landlord_bogus')", False)
except ValueError:
    check("_check_audience rejects unknown ('landlord_bogus')", True)

print('\n[5] engine normalizes owner→buyer (presentation only, E14)')
from evaluate_unified import _normalize_audience
check("_normalize_audience('owner') == 'buyer' (default view)",
      _normalize_audience('owner') == 'buyer')
check("_normalize_audience('مالك') == 'buyer'", _normalize_audience('مالك') == 'buyer')
check("_normalize_audience('valuer') untouched", _normalize_audience('valuer') == 'valuer')

print('\n[6] Confirm screen — leadership-aware central label')
check('cost-led label verbatim «مرتكز التكلفة (أرض + بناء مُهلَك)»',
      'مرتكز التكلفة (أرض + بناء مُهلَك)' in SHOWCONFIRM)
check("reads leadership.leader==='cost'", "_ld.leader==='cost'" in SHOWCONFIRM)
check("«الوسيط» only via leader==='market' or a comparison method",
      "_ld.leader==='market'" in SHOWCONFIRM
      and "indexOf('comparison')===0" in SHOWCONFIRM)
check('neutral fallback «التقدير المركزي» present', 'التقدير المركزي' in SHOWCONFIRM)
check('income_led guard on the method fallback (tri.mode read)',
      "income_triangulation||{}).mode==='income_led'" in SHOWCONFIRM
      and '!_ildC' in SHOWCONFIRM)
check("BLIND literal «الوسيط ≈ <b>» gone from showConfirm",
      'الوسيط ≈ <b>' not in SHOWCONFIRM)
check('range label «تقدير مبدئي (نطاق)» retained (b2.3)',
      'تقدير مبدئي (نطاق)' in SHOWCONFIRM)

print('\n[7] Confirm screen — dual evidence line on cost leadership')
check('evidence line marker «شواهد السوق: مطابق»', 'شواهد السوق: مطابق' in SHOWCONFIRM)
check('reads matched_n from the broadcast', '_ld.matched_n' in SHOWCONFIRM)
check('reads geo_full_n + geo_full_dispersion', '_ld.geo_full_n' in SHOWCONFIRM
      and '_ld.geo_full_dispersion' in SHOWCONFIRM)
check('thresholds read from the broadcast (no hardcoded-only)',
      '_ld.thresholds' in SHOWCONFIRM)
check('LTR islands on the numeric runs', SHOWCONFIRM.count('dir="ltr"') >= 2)
check('escaped comparators (&lt;/&gt;) — no raw < in text', '(&lt;' in SHOWCONFIRM and '(&gt;' in SHOWCONFIRM)

print('\n[8] JS label-decision mirror (the b2.2 governing-expression pattern)')
def js_mid_label(leadership, method, tri_mode=None):
    """Python mirror of the showConfirm label decision (incl. the income_led guard —
    income_led keeps the comparison METHOD string while the amount is the income
    value, so the method fallback alone would mislabel it «الوسيط»)."""
    lbl = 'التقدير المركزي'
    income_led = (tri_mode == 'income_led')
    if leadership and leadership.get('leader') == 'cost':
        lbl = 'مرتكز التكلفة (أرض + بناء مُهلَك)'
    elif leadership and leadership.get('leader') == 'market':
        lbl = 'الوسيط'
    elif (not leadership and not income_led
          and str(method or '').startswith('comparison')):
        lbl = 'الوسيط'
    return lbl

check('cost_led → «مرتكز التكلفة …»',
      js_mid_label({'leader': 'cost', 'rule': 'cost_led'}, 'comparison_thin')
      == 'مرتكز التكلفة (أرض + بناء مُهلَك)')
check('matched → «الوسيط»',
      js_mid_label({'leader': 'market', 'rule': 'matched'}, 'comparison_bracket') == 'الوسيط')
check('geo_full → «الوسيط»',
      js_mid_label({'leader': 'market', 'rule': 'geo_full'}, 'comparison_widened') == 'الوسيط')
check('e25_capped → «الوسيط» (market keeps the lead = the comparison median)',
      js_mid_label({'leader': 'market', 'rule': 'e25_capped'}, 'comparison_thin') == 'الوسيط')
check('income-led villa (REAL shape: comparison method + tri.mode) → neutral, NOT «الوسيط»',
      js_mid_label(None, 'comparison_thin', tri_mode='income_led') == 'التقدير المركزي')
check('apartment income-only (no leadership) → neutral, NOT «الوسيط»',
      js_mid_label(None, 'income_approach_only') == 'التقدير المركزي')
check('raw_land comparison (no leadership) → «الوسيط» (a true median)',
      js_mid_label(None, 'comparison_bracket') == 'الوسيط')

print('\n[9] Scope window — alias dedup + villa-term unification (E14)')
from scope_of_service import classify_asset_scope, service_scope_summary
_sum = service_scope_summary()
_sup_labels = [e['label_ar'] for e in _sum['supported']]
check('«أرض سكنية» appears EXACTLY ONCE', _sup_labels.count('أرض سكنية') == 1,
      str(_sup_labels))
check('supported count back to 3 (villa/land/compound_small)',
      len(_sum['supported']) == 3, str(len(_sum['supported'])))
check('villa card = the app-canonical «فيلا منفردة»', 'فيلا منفردة' in _sup_labels)
check('colloquial «فلة» gone from the scope table',
      all('فلة' not in e['label_ar'] for e in
          _sum['supported'] + _sum['limited'] + _sum['unsupported']))
check("Rule #47 alias INTACT (classify_asset_scope('raw_land') still the land scope)",
      classify_asset_scope('raw_land').label_ar == 'أرض سكنية'
      and classify_asset_scope('raw_land') is classify_asset_scope('land'))
check('summary counts coherent (3 supported in the text)',
      '3 فئات' in _sum['summary_ar'].replace('يدعم 3', '3 فئات')
      or 'يدعم 3' in _sum['summary_ar'], _sum['summary_ar'])

print('\n[10] Numbering — live first screens conform to the 2025 map (measured)')
check('zero stale VPS 4 in index.html', 'VPS 4' not in HTML)
check('zero stale VPN 13 in index.html', 'VPN 13' not in HTML)
check('the 2025 MUC tokens intact (VPGA 10 + VPS 6 + IVS 106)',
      'VPGA 10' in HTML and 'VPS 6' in HTML and 'IVS 106' in HTML)
check('HBU citation intact (VPS 2 / IVS 102)', 'VPS 2 / IVS 102' in HTML)

print('\n[11] Version strings (format only — R6 / Lesson 2)')
with open('evaluate_unified.py', encoding='utf-8') as f:
    ENG = f.read()
check('ENGINE_VERSION format', re.search(r"ENGINE_VERSION = 'thammen-sprint\d+p\d+p\d+", ENG) is not None)
check('SPRINT_TAG dotted-numeric', re.search(r"SPRINT_TAG = '\d+\.\d+\.\d+", ENG) is not None)

print(f'\n=== {PASS} passed, {FAIL} failed ===')
sys.exit(1 if FAIL else 0)
