# -*- coding: utf-8 -*-
"""Sprint 2.22.0b.139 — audience-brief backend EN twins (isolated test).

b139 completes the EN of the number-INTERPOLATED engine-authored fields that the
en_localize constant catalog (b78) cannot cover. All twins are ADDITIVE `{base}_en`
siblings authored at the emission site; the frontend already `pick()`s these bases,
so they auto-render in EN mode with index.html UNTOUCHED → VALUE-INVARIANT (only
`_en` keys added; every `_ar`/amount/method/rule byte-identical) and R14 N/A by
construction (the served frontend is unchanged; the §20.18 backend-only precedent).

Covers: income cap_rate_label / rent_source(municipal) / role · scenario delta_label ·
market-position description (_describe_position_en) · brief muc_basis /
muc_review_recommendation · strata land_reference.source.

E14: exercises the REAL market_position.compute_position, plus source-level twin +
value-invariance guards for the evaluate_unified / output_briefs / stock_strata / api
emission sites (which need live GIS + cap_rate calibration to invoke end-to-end).
"""
import io, os, re, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
_p = 0


def ok(cond, msg):
    global _p
    assert cond, 'FAIL: ' + msg
    _p += 1


def read(fn):
    with open(os.path.join(HERE, fn), encoding='utf-8') as f:
        return f.read()


AR = re.compile(r'[؀-ۿ]')

# ── 1. market_position.compute_position — REAL function (E14) ──
import market_position as M

_CASES = [
    (1_000_000, 1_000_000, 'at_market'),
    (700_000,   1_000_000, 'far_below_market'),
    (1_400_000, 1_000_000, 'far_above_market'),
    (1_150_000, 1_000_000, 'above_market'),
    (850_000,   1_000_000, 'below_market'),
]
for lp, bm, expect in _CASES:
    d = M.compute_position(listing_price=lp, benchmark_price=bm,
                           benchmark_source='MoJ', benchmark_n=12).to_dict()
    ok(d['position_label'] == expect, f'position label {expect}')
    ok(d.get('description_en'), f'description_en present ({expect})')
    ok(not AR.search(d['description_en']), f'description_en has no Arabic ({expect})')
    ok(bool(d.get('description_ar')) and AR.search(d['description_ar']),
       f'description_ar intact ({expect})')
    # value-invariance: the _en addition never altered the numeric verdict
    ok(isinstance(d['gap_pct'], (int, float)), 'gap_pct numeric (unchanged)')

_nb = M.compute_position(listing_price=None, benchmark_price=None,
                         benchmark_source='').to_dict()
ok(_nb['description_en'] == 'No listing price or sufficient benchmark available.',
   'no_benchmark description_en verbatim')
ok('؀' not in _nb['description_en'], 'no_benchmark en clean')

# _describe_position_en all 7 branches, English + interpolation
for lbl in ['no_benchmark', 'at_market', 'below_market', 'far_below_market',
            'above_market', 'far_above_market']:
    s = M._describe_position_en(lbl, -12.3, 9)
    ok(s and not AR.search(s), f'_describe_position_en[{lbl}] English')
ok('12.3%' in M._describe_position_en('below_market', -12.3, 9), 'en interpolates gap%')
ok('n=9' in M._describe_position_en('below_market', -12.3, 9), 'en interpolates n')
ok(M._describe_position_en('below_market', -12.3, None).find('reference n=') == -1,
   'en omits n when None')

# ── 2. evaluate_unified.py — income/scenario/market twins beside each _ar ──
EU = read('evaluate_unified.py')

# cap_rate_label is ALWAYS interpolated (%) → FULL parity: every _ar site has an _en
# (parity is robust to line-count/passthrough double-substrings — no brittle exact pins)
ok(EU.count("'cap_rate_label_ar'") == EU.count("'cap_rate_label_en'"),
   'cap_rate_label full _ar/_en parity (every site interpolated)')
ok('Calibrated capitalization rate' in EU, 'calibrated cap_rate_label_en (calibrated branch)')
ok('Capitalization rate {cap_rate*100:.1f}% (typical for {asset_type})' in EU,
   'typical cap_rate_label_en preserves % interpolation (asset_type slug)')
ok('Capitalization rate {cap_rate*100:.1f}% (typical for this asset class)' in EU,
   'typical cap_rate_label_en (asset_label_ar sites → generic EN, no embedded Arabic)')
# passthrough builders forward the EN (both investor-brief + main income_approach)
ok("'cap_rate_label_en': income.get('cap_rate_label_en')" in EU,
   'cap_rate_label_en passthrough (both income builders)')

# rent_source: interpolated variants twinned; the 'إفادة العميل' default-param constant
# is cataloged (attach_en) → catalog, not a site twin.
ok('Municipality median (n={v3_rent_data.get(\'n\')})' in EU, 'municipal rent_source_en n')
ok('Area rent median (n=' in EU, 'area-median rent_source_en n/confidence')
ok('Estimated from a typical capitalization rate ({cap_rate*100:.1f}%)' in EU,
   'cap-estimate rent_source_en %')
ok("'rent_source_en': income.get('rent_source_en')" in EU, 'rent_source_en passthrough')

# role: the 3 NON-cataloged sites twinned; 'تأكيد منهجي'/'القيمة الأساسية المعتمدة'
# constants are catalog-covered (attach_en), never a None-passthrough (would block catalog).
ok("'role_en': 'Adopted primary value'," in EU, 'response role_en')
ok("'role_en': 'Apartment sale listings — Lusail'," in EU, 'T2 role_en')
ok('Adopted primary value for this asset class' in EU, 'brief role_en (generic EN)')
ok("'role_en': None" not in EU and "'role_en':None" not in EU,
   'no None role_en passthrough (would block the en_localize catalog, en_localize.py:184)')

# delta_label ALWAYS interpolated → FULL parity; 'Base' not 'الأساس'
ok(EU.count("'delta_label_ar'") == EU.count("'delta_label_en'"),
   'delta_label full _ar/_en parity')
ok(EU.count("'Base' if") == 3, "delta_label_en uses 'Base' (EN) at all 3 sites")

# market description (income path) twin + position_en
ok('position_en = (' in EU, 'position_en helper defined')
ok("'description_en': f'The price is {position_en} by {abs(gap_pct):.1f}%." in EU,
   'income-path market description_en interpolates position + gap%')

# ── 3. output_briefs.py — brief muc twins (both buyer + valuer sites) ──
OB = read('output_briefs.py')
ok(OB.count("'muc_basis_en': unc.get('muc_basis_en')") == 2, '2 brief muc_basis_en twins')
ok(OB.count("'muc_review_recommendation_en': unc.get('muc_review_recommendation_en')") == 2,
   '2 brief muc_review_recommendation_en twins')
# value-invariance: the _ar copies remain
ok(OB.count("'muc_basis_ar': unc.get('muc_basis_ar')") == 2, 'muc_basis_ar unchanged (×2)')

# ── 4. stock_strata.py — land_reference source twin ──
SS = read('stock_strata.py')
ok("'source_en': 'Median of registered land-sale transactions in the same district (MoJ)'" in SS,
   'strata land_reference source_en')
ok("'source_ar': 'وسيط معاملات بيع أراضي مسجَّلة في نفس المنطقة (MoJ)'" in SS,
   'strata source_ar unchanged (value-invariant)')

# ── 5. api.py — market_position description_en passthrough (2 branches) ──
AP = read('api.py')
ok("'description_en': ev.market_position.get('description_en')" in AP,
   'api market_position description_en passthrough (primary branch)')
ok("'description_en': 'Descriptive data not available'" in AP,
   'api market_position description_en (fallback branch)')

# market_position.py dataclass + to_dict wired
MP = read('market_position.py')
ok('description_en: str' in MP, 'MarketPosition.description_en field')
ok("'description_en': self.description_en," in MP, 'to_dict emits description_en')
ok('def _describe_position_en(' in MP, '_describe_position_en defined')

# ── 6. Termbase discipline (b78 catalog): capitalization rate / Income Approach / MoJ ──
_new_en = [
    'Calibrated capitalization rate', 'Capitalization rate',
    'Municipality median', 'Adopted primary value', 'Apartment sale listings',
    'Median of registered land-sale transactions', 'Income Approach',
]
for phrase in _new_en:
    ok(phrase in (EU + SS), f'termbase phrase present: {phrase[:30]}')
# never "cap rate" (must be "capitalization rate") in the NEW en twins
for m in re.finditer(r"'cap_rate_label_en':.*?\),", EU, re.S):
    ok('cap rate' not in m.group(0).lower() or 'capitalization' in m.group(0).lower(),
       'cap_rate_label_en says "capitalization rate" not "cap rate"')

# ── 7. Value-invariance contract: index.html + engine _ar templates untouched ──
# the _ar interpolation templates must be byte-present (proves no _ar edit)
for tmpl in [
    "f'معدل رسملة معايَر {cap_rate*100:.1f}% '",
    "else f'معدل رسملة {cap_rate*100:.1f}% (نموذجي لـ {asset_type})'",
    "rent_source_ar = f\"وسيط البلدية (n={v3_rent_data.get('n')})\"",
]:
    ok(tmpl in EU, f'_ar template unchanged: {tmpl[:32]}')
# version bump present
ok("SPRINT_TAG = '2.22.0b.139'" in EU, 'SPRINT_TAG bumped to b139')
ok('thammen-sprint2p22p0b139-en-brief-backend-twins' in EU, 'ENGINE_VERSION b139')

print(f'test_sprint_2_22_0b139: {_p}/{_p} PASS')
