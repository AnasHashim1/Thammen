#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isolated copy/compliance test — Sprint 2.22.0b.68 (T0-1): privacy-notice truthfulness.

The live a24 Terms §3/§6 (AR + EN) claimed «الأداة لا تُخزّن أي بيانات» / «The tool stores
nothing … not retained» / «we do not store the [address]». That became FALSE once the operator
report-copy went LIVE (b42.1): every report (incl. the property ADDRESS + parcel data, with the
Kahramaa utility account numbers SCRUBBED per b43) is emailed to the operator's records (Resend +
inbox). A false «stores nothing» is the worst compliance posture. b68 makes the notice TRUTHFUL —
it discloses the retained report copy + the cross-border processing + that no personal CONTACT data
is collected + the deletion right, WITHOUT reapplying the rejected heavy address-redaction (b43 keeps
the address by PO decision). Lawyer + linguist personas applied (PO standing directive).

FRONTEND-ONLY / VALUE-INVARIANT (index.html Terms copy + the DPIA backing doc; engine = 2 version
lines). Per E14 this reads the REAL index.html + DPIA.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b68.py
"""
import re
import sys
from pathlib import Path

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f'  PASS  {name}')
    else:
        _failed += 1
        print(f'  FAIL  {name}')


root = Path(__file__).parent
html = root.joinpath('index.html').read_text(encoding='utf-8')
dpia = root.joinpath('docs/DPIA_AI_impact_beta_v1.md').read_text(encoding='utf-8')

# ── 1. The FALSE storage claims are GONE (AR + EN Terms §3/§6) ──
FALSE_CLAIMS = [
    'الأداة لا تُخزّن أي بيانات',
    'لا نُخزّنه ولا نربطه بك',
    'تُعالَج استعلاماتك هناك مؤقتاً ولا تُحفَظ',
    'بما أن الأداة لا تُخزّن بيانات شخصية',
    'The tool stores nothing',
    'we therefore do not store it or link it to you',
    'processed there transiently and are not retained',
    'Because the tool stores no personal data',
]
for c in FALSE_CLAIMS:
    check(f'false claim removed: "{c[:42]}"', c not in html)

# ── 2. The TRUTHFUL disclosure is PRESENT (AR) ──
check('AR: keeps a copy of the report (incl. address + parcel data)',
      'نحتفظ بنسخة من تقرير تقييمك' in html and 'عنوان العقار وبياناته العقاريّة' in html)
check('AR: no personal contact data collected',
      'لا نجمع بيانات تواصل شخصيّة' in html)
check('AR: utility account numbers scrubbed from the copy (b43)',
      'تُزال أرقام حسابات الكهرباء والماء من النسخة المحفوظة' in html)
check('AR: cross-border hosting names Resend',
      'Heroku وCloudflare وResend' in html)
check('AR: deletion right on the retained copy',
      'حذف نسخة تقريرك من سجلّاتنا' in html)
check('AR §6 risk surface = the retained copy (not "stores nothing")',
      'سطح الخطر محدود بنسخة التقرير المحفوظة في سجلّاتنا' in html)

# ── 3. The TRUTHFUL disclosure is PRESENT (EN) ──
check('EN: keeps a copy of the report',
      "We keep a copy of your valuation report" in html
      and 'cadastral PIN, district, location, and the estimate' in html)
check('EN: no personal contact data collected',
      'We do not collect personal contact data' in html
      and 'electricity/water account numbers are removed from the retained copy' in html)
check('EN: cross-border names Resend',
      'Heroku, Cloudflare and Resend' in html)
check('EN: deletion right on the retained copy',
      'delete your report copy from our records' in html)
check('EN §6 risk surface = the retained copy',
      'limited to the report copy retained in our records' in html)

# ── 4. The 72-hour breach commitment is KEPT (both languages) ──
check('AR 72h breach kept', 'نلتزم بإبلاغك خلال' in html and '72' in html)
check('EN 72h breach kept', 'notifying you within 72 hours' in html)

# ── 5. The REAL COVER is preserved (NOT weakened) ──
check('«ليس تقييماً معتمداً» preserved (×count)', html.count('ليس تقييماً معتمداً') >= 1)
check('NOT an official/certified valuation (EN) preserved',
      'NOT an official or certified valuation' in html)
check('free service framing preserved', 'هذه خدمة مجانية' in html and 'A free service' in html)
check('not-affiliated-with-MoJ preserved', 'غير منتسبة لوزارة العدل' in html)
check('disclaimer §5 preserved (AR)', 'التقييم لأغراض الدعم والمعلومة فقط' in html)

# ── 6. The CONSENT GATE mechanism «stores nothing» claims are UNTOUCHED ──
#       (those describe the sessionStorage consent flag — frontend-only, TRUE — NOT the data claim)
check('gate "stores nothing" (sessionStorage consent flag) preserved',
      html.count('stores nothing') >= 2)   # the gate + Terms-modal mechanism comments
check('affirmative consent line preserved',
      'أُقرّ بأنني فهمت أن ثمّن تقييم سوقيّ آليّ' in html)

# ── 7. The Latin tokens in the AR notice are bidi-safe (inside a dir=ltr island) ──
#       the only Latin in the new AR §3 copy is the hosting names — they MUST be in a dir=ltr span.
check('AR Latin (Heroku/Cloudflare/Resend) wrapped in a dir=ltr island',
      '<span dir="ltr">Heroku وCloudflare وResend</span>' in html)
# the AR retained-copy + contact + deletion sentences are pure-Arabic (no bare Latin authored).
# bound each window to its OWN closing </p> so it can't overshoot into a later Latin token.
for _frag in ['نحتفظ بنسخة من تقرير تقييمك', 'لا نجمع بيانات تواصل شخصيّة',
              'حذف نسخة تقريرك من سجلّاتنا']:
    _i = html.find(_frag)
    _end = html.find('</p>', _i)
    _seg = html[_i:_end] if (_i != -1 and _end != -1) else 'X'
    check(f'AR sentence pure-Arabic (no bare Latin): "{_frag[:24]}"',
          re.search(r'[A-Za-z]', _seg) is None)

# ── 8. DPIA backing doc is consistent (no «nothing stored» / WhatsApp staleness) ──
check('DPIA: no "nothing stored"', 'nothing stored' not in dpia and 'NOT stored by the app' not in dpia)
check('DPIA: report copy retained in operator records',
      'RETAINED in the OPERATOR' in dpia or 'retained in operator records' in dpia)
check('DPIA: feedback channel is email (WhatsApp number dropped)',
      'info@thammen.qa' in dpia and '70177761' not in dpia)
check('DPIA: utility numbers scrubbed noted', 'SCRUBBED' in dpia or 'scrubbed' in dpia)

# ── 9. Version format (version-agnostic — R6: no exact-version pins) ──
ev = root.joinpath('evaluate_unified.py').read_text(encoding='utf-8')
check('ENGINE_VERSION has the valid sprint format',
      re.search(r"ENGINE_VERSION\s*=\s*'thammen-sprint\d+p\d+p\d+", ev) is not None)

print()
print(f'Sprint 2.22.0b.68 isolated: {_passed} passed, {_failed} failed')
sys.exit(0 if _failed == 0 else 1)
