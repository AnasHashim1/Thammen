# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.22 — tower-pair fence: isolated tests.

Exercises the PRODUCTION `_derive_rent_from_unit_pair` (E14/#40 — the real
function, no replica) + the signed contract enumeration:
  - villa/house/land + (unit_count × avg) ⇒ pair IGNORED + verbatim disclosure,
    rental untouched (b6 bare-rent path preserved).
  - tower/apartment/compound (large AND small — the address-entry compound is
    quick-classified compound_small) + pair ⇒ BYTE-IDENTICAL derivation to the
    pre-b22 strings.
  - incomplete pair ⇒ legacy behaviour byte-identical.
Plus wiring pins: call-site gated, scope-safe init, both attach sites, the
verbatim AR constant, and the index.html fence (syncTowerPair + clear +
requires-line gate + disclosure chip).

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b22.py
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from evaluate_unified import (  # noqa: E402  (production imports — E14)
    _derive_rent_from_unit_pair,
    _TOWER_PAIR_ASSETS,
    _TOWER_PAIR_IGNORED_AR,
    _TOWER_PAIR_IGNORED_EN,
)

PASS = []
FAIL = []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(('  PASS  ' if cond else '  FAIL  ') + name + (('  | ' + detail) if (detail and not cond) else ''))


print('— §1 membership (the signed allowlist) —')
check('1.1 tower in allowlist', 'tower' in _TOWER_PAIR_ASSETS)
check('1.2 apartment_building in allowlist', 'apartment_building' in _TOWER_PAIR_ASSETS)
check('1.3 compound_large in allowlist', 'compound_large' in _TOWER_PAIR_ASSETS)
check('1.4 compound_small in allowlist (address-entry large compound is quick-classified compound_small — contract byte-identity)',
      'compound_small' in _TOWER_PAIR_ASSETS)
check('1.5 commercial_building in allowlist (the literal §19 list)', 'commercial_building' in _TOWER_PAIR_ASSETS)
check('1.6 villa NOT in allowlist', 'standalone_villa' not in _TOWER_PAIR_ASSETS)
check('1.7 house NOT in allowlist', 'house' not in _TOWER_PAIR_ASSETS)
check('1.8 raw_land NOT in allowlist', 'raw_land' not in _TOWER_PAIR_ASSETS)

print('— §2 tower-like + pair ⇒ byte-identical derivation —')
for qt in ('tower', 'apartment_building', 'compound_large', 'compound_small'):
    rent, src, ign = _derive_rent_from_unit_pair(qt, 12, 5000, None)
    check(f'2.x {qt}: derived 60000', rent == 60000, f'rent={rent}')
    check(f'2.x {qt}: kind derived_from_units', (src or {}).get('kind') == 'derived_from_units')
    check(f'2.x {qt}: no ignored flag', ign is None)
# the exact pre-b22 note string (byte-identity of the provenance label)
rent, src, ign = _derive_rent_from_unit_pair('apartment_building', 12, 5000, None)
check('2.9 note_ar byte-identical to pre-b22',
      src['note_ar'] == 'محسوب من 12 وحدة × 5,000 ر.ق/شهر = 60,000 ر.ق/شهر إجمالي',
      repr(src['note_ar']))
check('2.10 derived_monthly_total carried', src['derived_monthly_total'] == 60000)
# pair wins over bare rental on tower-like (pre-b22 precedence preserved)
rent, src, ign = _derive_rent_from_unit_pair('tower', 80, 12000, 30000)
check('2.11 tower: pair WINS over bare rental (pre-b22 precedence)', rent == 960000 and src['kind'] == 'derived_from_units')

print('— §3 non-tower + pair ⇒ ignored + disclosure; b6 bare path untouched —')
for qt in ('standalone_villa', 'house', 'raw_land'):
    rent, src, ign = _derive_rent_from_unit_pair(qt, 12, 5000, None)
    check(f'3.x {qt}: rent NOT derived (None)', rent is None, f'rent={rent}')
    check(f'3.x {qt}: no rent_source', src is None)
    check(f'3.x {qt}: ignored flag present', isinstance(ign, dict))
    check(f'3.x {qt}: verbatim AR disclosure', (ign or {}).get('note_ar') == 'مدخل برجي على أصل غير برجي — تم تجاهله')
    check(f'3.x {qt}: flag carries the pair + asset', (ign or {}).get('unit_count') == 12 and (ign or {}).get('asset_type') == qt)
# villa + pair + bare rental: the bare (b6-legitimate) rent proceeds; pair disclosed-ignored
rent, src, ign = _derive_rent_from_unit_pair('standalone_villa', 12, 5000, 9000)
check('3.13 villa+pair+bare: bare rent survives (b6 untouched)', rent == 9000)
check('3.14 villa+pair+bare: user_total provenance', (src or {}).get('kind') == 'user_total')
check('3.15 villa+pair+bare: user_total note byte-identical', (src or {}).get('note_ar') == 'إفادة العميل: 9,000 ر.ق/شهر إجمالي')
check('3.16 villa+pair+bare: ignored flag still disclosed', isinstance(ign, dict))
# the EN twin exists and mentions ignored
check('3.17 EN disclosure present', 'ignored' in _TOWER_PAIR_IGNORED_EN)
# unknown/None qtype → fail-safe to IGNORE (never invent income on an unknown asset)
rent, src, ign = _derive_rent_from_unit_pair(None, 12, 5000, None)
check('3.18 qtype=None: pair ignored (fail-safe)', rent is None and isinstance(ign, dict))
rent, src, ign = _derive_rent_from_unit_pair('unknown', 12, 5000, None)
check('3.19 qtype=unknown: pair ignored (fail-safe)', rent is None and isinstance(ign, dict))

print('— §4 incomplete pair / bare-only ⇒ legacy byte-identical —')
rent, src, ign = _derive_rent_from_unit_pair('standalone_villa', 12, None, 9000)
check('4.1 unit_count only: falls to bare rental, NO ignored flag (legacy)', rent == 9000 and ign is None and src['kind'] == 'user_total')
rent, src, ign = _derive_rent_from_unit_pair('apartment_building', None, 5000, None)
check('4.2 avg only, no bare: nothing derived, no flag', rent is None and src is None and ign is None)
rent, src, ign = _derive_rent_from_unit_pair('standalone_villa', None, None, 15000)
check('4.3 bare-only villa: user_total (b6) byte-identical', rent == 15000 and src['kind'] == 'user_total' and ign is None)
rent, src, ign = _derive_rent_from_unit_pair('standalone_villa', None, None, None)
check('4.4 nothing in: nothing out', rent is None and src is None and ign is None)
rent, src, ign = _derive_rent_from_unit_pair('apartment_building', 0, 5000, None)
check('4.5 unit_count=0 falsy: not derived (legacy truthiness)', rent is None and src is None and ign is None)

print('— §5 wiring pins (source-level; behaviour-scoped, no version pins) —')
src_text = io.open(os.path.join(HERE, 'evaluate_unified.py'), encoding='utf-8').read()
check('5.1 call site uses the fenced helper',
      re.search(r'rental_income, _rent_source, _tower_pair_ignored = \(\s*\n\s*_derive_rent_from_unit_pair\(', src_text) is not None)
check('5.2 the old unconditional multiply is GONE',
      'rental_income = _derived_total' not in src_text.replace('return _derived_total', ''))
check('5.3 scope-safe init present', '_tower_pair_ignored = None' in src_text)
check('5.4 full-path attach present', "output['tower_pair_ignored'] = _tower_pair_ignored" in src_text)
check('5.5 fast-route (Gate-3) attach present', "result['tower_pair_ignored'] = _tower_pair_ignored" in src_text)
check('5.6 AR constant verbatim in source', 'مدخل برجي على أصل غير برجي — تم تجاهله' in src_text)

print('— §6 index.html fence (real file) —')
html = io.open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
check('6.1 syncTowerPair defined', 'function syncTowerPair(' in html)
check('6.2 syncTowerPair clears the pair on non-tower', re.search(r"if\(!towerLike\)\{[^}]*uc\.value='';", html, re.S) is not None)
check('6.3 show() calls syncTowerPair', re.search(r'function show\(d\)\{[\s\S]{0,800}syncTowerPair\(d&&d\.asset_type\);', html) is not None)
check('6.4 requires-line gated on !hasValuation', 'ss.requires_user_input_ar&&!hasValuation' in html)
check('6.5 disclosure chip renders note_ar', 'd.tower_pair_ignored&&d.tower_pair_ignored.note_ar' in html)
check('6.6 towerRentSection markup intact', 'id="towerRentSection"' in html and 'id="unitCount"' in html and 'id="avgRentPerUnit"' in html)
check('6.7 payload builder still sends the pair only when both present', 'bd.unit_count=+uc;bd.avg_monthly_rent_per_unit=+apu;' in html)

print('=' * 60)
print(f'{len(PASS)} passed / {len(FAIL)} failed')
if FAIL:
    print('FAILED:', FAIL)
    sys.exit(1)
sys.exit(0)
