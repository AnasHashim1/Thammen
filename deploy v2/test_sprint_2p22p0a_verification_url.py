"""Sprint 2.22.0a/7 — isolated tests for verification_url.

Coverage:
  [1] generate_token determinism (same input → same token)
  [2] generate_token uniqueness (different inputs → different tokens)
  [3] generate_token day rollover (same identifier, different days)
  [4] generate_token output format ([A-Z2-7]{12})
  [5] generate_token TypeError on non-str inputs
  [6] generate_token UTF-8 identifier (Arabic addresses — PIN mode)
  [7] is_valid_token_format positive + negative cases
  [8] build_verification_url happy path
  [9] build_verification_url falsy-handling (None / empty / '—' / whitespace)
 [10] build_verification_url URL prefix correctness
 [11] _attach_scope integration — universal injection (value-producing + refusal)
 [12] cross-check orthogonality with /2 tier_label
 [13] cross-check orthogonality with /5 refusal_reason
 [14] cross-check Pearl A5 + Lusail A1 sample shape
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Sprint 2.22.0a/10 — shared test infrastructure (Anas Q1.5: generic name).
from _test_helpers import Reporter, set_stdout_utf8

set_stdout_utf8()

# Module under test
from verification_url import (
    THAMMEN_VERIFY_BASE_URL,
    TOKEN_LENGTH,
    generate_token,
    build_verification_url,
    is_valid_token_format,
)

# Sprint 2.22.0a/10 — Pattern B legacy adapter (Rule #39 deviation, see
# §10 commit message). 67 callsites use the `check(name, cond)` order
# established in /7 (Sprint 2.22.0a/7). AST-driven reorder attempted
# but failed on f-string positions for Arabic content (Rule #34 file-
# based script artifacts removed pre-commit). The adapter wrapper routes
# through the canonical `_REPORTER.check(cond, name, detail)` → Reporter
# shared with all 6 isolated test files. Callsite signature drift
# FLAGGED for /12 final consistency pass.
_REPORTER = Reporter()


def check(name, cond):
    _REPORTER.check(cond, name)


# ──────────────────────────────────────────────────────────────────────
# [1] generate_token determinism
# ──────────────────────────────────────────────────────────────────────
print('\n[1] generate_token determinism (same input → same token)')
t1 = generate_token('61/875/20', '2026-05-26')
t2 = generate_token('61/875/20', '2026-05-26')
t3 = generate_token('61/875/20', '2026-05-26')
check('generate_token deterministic across 3 calls', t1 == t2 == t3)
check('determinism token has length 12', len(t1) == TOKEN_LENGTH)

# ──────────────────────────────────────────────────────────────────────
# [2] generate_token uniqueness across distinct inputs
# ──────────────────────────────────────────────────────────────────────
print('\n[2] generate_token uniqueness (distinct identifiers → distinct tokens)')
addrs = ['61/875/20', '52/903/90', '53/240/12', '69/255/75', '69/329/20',
         '70/300/25', '51/835/17', '56/565/21', '66/030/258', '74/328/443']
day = '2026-05-26'
tokens = {addr: generate_token(addr, day) for addr in addrs}
check('10 distinct identifiers → 10 distinct tokens',
      len(set(tokens.values())) == 10)
check('Lusail PIN tokens differ from Pearl PIN tokens',
      tokens['69/255/75'] != tokens['69/329/20'])

# ──────────────────────────────────────────────────────────────────────
# [3] generate_token day rollover
# ──────────────────────────────────────────────────────────────────────
print('\n[3] generate_token day rollover (same identifier, different days)')
addr = '61/875/20'
t_2026_05_26 = generate_token(addr, '2026-05-26')
t_2026_05_27 = generate_token(addr, '2026-05-27')
t_2027_05_26 = generate_token(addr, '2027-05-26')
t_2026_01_01 = generate_token(addr, '2026-01-01')
check('same identifier, 2026-05-26 vs 2026-05-27 → distinct',
      t_2026_05_26 != t_2026_05_27)
check('same identifier, 2026-05-26 vs 2027-05-26 → distinct',
      t_2026_05_26 != t_2027_05_26)
check('same identifier, 2026-05-26 vs 2026-01-01 → distinct',
      t_2026_05_26 != t_2026_01_01)
check('4 distinct (identifier, day) pairs → 4 distinct tokens',
      len({t_2026_05_26, t_2026_05_27, t_2027_05_26, t_2026_01_01}) == 4)

# ──────────────────────────────────────────────────────────────────────
# [4] generate_token output format [A-Z2-7]{12}
# ──────────────────────────────────────────────────────────────────────
print('\n[4] generate_token output format ([A-Z2-7]{12})')
sample_tokens = [generate_token(a, day) for a in addrs]
import re
fmt_re = re.compile(r'^[A-Z2-7]{12}$')
fmt_ok = all(fmt_re.match(t) for t in sample_tokens)
check('all 10 generated tokens match [A-Z2-7]{12} regex', fmt_ok)
check('no token contains lowercase', not any(any(c.islower() for c in t) for t in sample_tokens))
check('no token contains 0 / 1 / 8 / 9 (base32 alphabet exclusion)',
      all(not any(c in '0189' for c in t) for t in sample_tokens))

# ──────────────────────────────────────────────────────────────────────
# [5] generate_token TypeError on non-str inputs
# ──────────────────────────────────────────────────────────────────────
print('\n[5] generate_token TypeError on non-str inputs')
try:
    generate_token(123, '2026-05-26')
    check('integer identifier raises TypeError', False)
except TypeError:
    check('integer identifier raises TypeError', True)
try:
    generate_token('61/875/20', None)
    check('None day raises TypeError', False)
except TypeError:
    check('None day raises TypeError', True)
try:
    generate_token(None, None)
    check('None,None raises TypeError', False)
except TypeError:
    check('None,None raises TypeError', True)

# ──────────────────────────────────────────────────────────────────────
# [6] generate_token UTF-8 identifier (Arabic addresses — PIN mode)
# ──────────────────────────────────────────────────────────────────────
print('\n[6] generate_token UTF-8 identifier (Arabic — PIN mode)')
arabic_addr = 'أرض في الدفنة — PIN 12345'
t_ar = generate_token(arabic_addr, '2026-05-26')
check('Arabic identifier produces valid token', is_valid_token_format(t_ar))
check('Arabic identifier deterministic',
      generate_token(arabic_addr, '2026-05-26') == t_ar)
arabic_addr2 = 'أرض في لوسيل — PIN 99999'
t_ar2 = generate_token(arabic_addr2, '2026-05-26')
check('two distinct Arabic identifiers → distinct tokens', t_ar != t_ar2)

# ──────────────────────────────────────────────────────────────────────
# [7] is_valid_token_format positive + negative
# ──────────────────────────────────────────────────────────────────────
print('\n[7] is_valid_token_format positive + negative')
check('valid token K3HBNZ2L5MQR-shape passes', is_valid_token_format('AAAAAAAAAAAA'))
check('actual generated token passes', is_valid_token_format(t1))
check('lowercase rejects', not is_valid_token_format('aaaaaaaaaaaa'))
check('length 11 rejects', not is_valid_token_format('AAAAAAAAAAA'))
check('length 13 rejects', not is_valid_token_format('AAAAAAAAAAAAA'))
check('contains 0 (excluded from base32) rejects', not is_valid_token_format('AAAAAAAAAAA0'))
check('contains 1 (excluded from base32) rejects', not is_valid_token_format('AAAAAAAAAAA1'))
check('contains 8 (excluded from base32) rejects', not is_valid_token_format('AAAAAAAAAAA8'))
check('contains 9 (excluded from base32) rejects', not is_valid_token_format('AAAAAAAAAAA9'))
check('empty string rejects', not is_valid_token_format(''))
check('None rejects', not is_valid_token_format(None))
check('integer rejects', not is_valid_token_format(123456789012))

# ──────────────────────────────────────────────────────────────────────
# [8] build_verification_url happy path
# ──────────────────────────────────────────────────────────────────────
print('\n[8] build_verification_url happy path')
url = build_verification_url('61/875/20', '2026-05-26')
check('happy path returns non-None URL', url is not None)
check('URL starts with THAMMEN_VERIFY_BASE_URL',
      url.startswith(THAMMEN_VERIFY_BASE_URL + '/'))
check('URL token suffix valid format',
      is_valid_token_format(url.split('/')[-1]))
check('URL length = base + 1 (slash) + 12 (token)',
      len(url) == len(THAMMEN_VERIFY_BASE_URL) + 1 + TOKEN_LENGTH)

# ──────────────────────────────────────────────────────────────────────
# [9] build_verification_url falsy-handling (Q4 (a))
# ──────────────────────────────────────────────────────────────────────
print('\n[9] build_verification_url falsy-handling (Q4 (a))')
check('address=None → None', build_verification_url(None, '2026-05-26') is None)
check('address="" → None', build_verification_url('', '2026-05-26') is None)
check('address="—" → None (em-dash sentinel)',
      build_verification_url('—', '2026-05-26') is None)
check('address="   " → None (whitespace)',
      build_verification_url('   ', '2026-05-26') is None)
check('valuation_date=None → None',
      build_verification_url('61/875/20', None) is None)
check('valuation_date="" → None',
      build_verification_url('61/875/20', '') is None)
check('both None → None', build_verification_url(None, None) is None)

# ──────────────────────────────────────────────────────────────────────
# [10] build_verification_url URL prefix correctness
# ──────────────────────────────────────────────────────────────────────
print('\n[10] build_verification_url URL prefix correctness')
check('THAMMEN_VERIFY_BASE_URL is exactly https://thammen.qa/verify',
      THAMMEN_VERIFY_BASE_URL == 'https://thammen.qa/verify')
url = build_verification_url('52/903/90', '2026-05-26')
check('URL contains thammen.qa', 'thammen.qa' in url)
check('URL uses https', url.startswith('https://'))
check('URL has no double-slashes after https://',
      '//' not in url.split('://', 1)[1])

# ──────────────────────────────────────────────────────────────────────
# [11] _attach_scope integration — universal injection
# ──────────────────────────────────────────────────────────────────────
print('\n[11] _attach_scope integration — universal injection (R6)')
from evaluate_unified import _attach_scope

# Value-producing response
resp_val = {
    'status': 'ok',
    'asset_type': 'standalone_villa',
    'address': '52/903/90',
    'valuation_date': '2026-05-26',
    'valuation': {'amount': 5_000_000, 'method': 'comparison_bracket'},
}
_attach_scope(resp_val)
check('[value-producing] verification_url key present',
      'verification_url' in resp_val)
check('[value-producing] verification_url is non-None',
      resp_val['verification_url'] is not None)
check('[value-producing] URL well-formed',
      resp_val['verification_url'].startswith(THAMMEN_VERIFY_BASE_URL + '/'))

# Refusal response
resp_ref = {
    'status': 'ok',
    'asset_type': 'compound_large',
    'address': '51/835/17',
    'valuation_date': '2026-05-26',
    'valuation': {'amount': None, 'method': 'insufficient_data'},
    'refusal_reason': {'trigger_id': 'asset_scale_extreme'},
}
_attach_scope(resp_ref)
check('[refusal] verification_url key present',
      'verification_url' in resp_ref)
check('[refusal] verification_url is non-None (NOT gated)',
      resp_ref['verification_url'] is not None)
check('[refusal] URL well-formed',
      resp_ref['verification_url'].startswith(THAMMEN_VERIFY_BASE_URL + '/'))

# Falsy-address response (e.g. asset_type_reality_stop with no district/PIN)
resp_falsy = {
    'status': 'ok',
    'asset_type': 'unknown',
    'address': '—',
    'valuation_date': '2026-05-26',
}
_attach_scope(resp_falsy)
check('[falsy-address] verification_url key present',
      'verification_url' in resp_falsy)
check('[falsy-address] verification_url is None (Q4 (a))',
      resp_falsy['verification_url'] is None)

# Missing-date response
resp_no_date = {
    'status': 'ok',
    'asset_type': 'standalone_villa',
    'address': '70/300/25',
    'valuation_date': None,
}
_attach_scope(resp_no_date)
check('[no-date] verification_url key present',
      'verification_url' in resp_no_date)
check('[no-date] verification_url is None (Q4 (a))',
      resp_no_date['verification_url'] is None)

# ──────────────────────────────────────────────────────────────────────
# [12] Cross-check orthogonality with /2 tier_label
# ──────────────────────────────────────────────────────────────────────
print('\n[12] Cross-check orthogonality with /2 tier_label')
from evaluate_unified import _tier_label_for

# tier_label='analytical_range' (value-producing) AND verification_url present
resp_a = {
    'status': 'ok',
    'asset_type': 'standalone_villa',
    'address': '52/903/90',
    'valuation_date': '2026-05-26',
    'tier_label': _tier_label_for('comparison_bracket'),
}
_attach_scope(resp_a)
check('[value-producing] tier_label="analytical_range" AND verification_url present',
      resp_a['tier_label'] == 'analytical_range' and resp_a['verification_url'] is not None)

# tier_label=None (refusal) AND verification_url present
resp_b = {
    'status': 'ok',
    'asset_type': 'compound_large',
    'address': '51/835/17',
    'valuation_date': '2026-05-26',
    'tier_label': _tier_label_for('insufficient_data'),
}
_attach_scope(resp_b)
check('[refusal] tier_label=None AND verification_url present (orthogonal)',
      resp_b['tier_label'] is None and resp_b['verification_url'] is not None)

# ──────────────────────────────────────────────────────────────────────
# [13] Cross-check orthogonality with /5 refusal_reason
# ──────────────────────────────────────────────────────────────────────
print('\n[13] Cross-check orthogonality with /5 refusal_reason')
from evaluate_unified import _compute_refusal_reason

# refusal_reason populated AND verification_url present (concurrent)
resp_pearl = {
    'status': 'ok',
    'asset_type': 'apartment_building',
    'address': '69/255/75',
    'valuation_date': '2026-05-26',
    'refusal_reason': _compute_refusal_reason(
        method='insufficient_data',
        asset_type='apartment_building',
        district_ar='جزيرة اللؤلؤة',
    ),
}
_attach_scope(resp_pearl)
check('[Pearl A5] refusal_reason populated (density_gated_district)',
      resp_pearl['refusal_reason'] is not None
      and resp_pearl['refusal_reason']['trigger_id'] == 'density_gated_district')
check('[Pearl A5] verification_url ALSO present (NOT gated)',
      resp_pearl['verification_url'] is not None)
check('[Pearl A5] both fields populated simultaneously — orthogonal',
      resp_pearl['refusal_reason'] is not None
      and resp_pearl['verification_url'] is not None)

# refusal_reason=None AND verification_url present (concurrent)
resp_villa = {
    'status': 'ok',
    'asset_type': 'standalone_villa',
    'address': '52/903/90',
    'valuation_date': '2026-05-26',
    'refusal_reason': _compute_refusal_reason(
        method='comparison_bracket',
        asset_type='standalone_villa',
        district_ar='الغرافة',
    ),
}
_attach_scope(resp_villa)
check('[value-producing villa] refusal_reason=None',
      resp_villa['refusal_reason'] is None)
check('[value-producing villa] verification_url present (concurrent)',
      resp_villa['verification_url'] is not None)

# ──────────────────────────────────────────────────────────────────────
# [14] Sample shape — Pearl A5 + Lusail A1 + day-rollover for same identifier
# ──────────────────────────────────────────────────────────────────────
print('\n[14] Sample shape — Pearl A5 + Lusail A1 + day-rollover')
url_pearl_a5 = build_verification_url('69/255/75', '2026-05-26')
url_lusail_a1 = build_verification_url('69/255/75', '2026-05-26')  # same identifier
check('Pearl 69/255/75 same day same URL (determinism)',
      url_pearl_a5 == url_lusail_a1)
url_lusail_different_addr = build_verification_url('69/329/20', '2026-05-26')
check('Different identifier (69/329/20) → distinct URL',
      url_pearl_a5 != url_lusail_different_addr)
url_pearl_next_day = build_verification_url('69/255/75', '2026-05-27')
check('Same identifier, next day → distinct URL (day rollover)',
      url_pearl_a5 != url_pearl_next_day)

# Print actual sample URLs (for the STOP report)
print('\n  SAMPLE URLs:')
print(f'    Pearl A5 / 2026-05-26: {url_pearl_a5}')
print(f'    Lusail next-day:        {url_pearl_next_day}')
print(f'    Different identifier:   {url_lusail_different_addr}')

# ──────────────────────────────────────────────────────────────────────
# Summary — Sprint 2.22.0a/10 unified via _test_helpers.Reporter
# ──────────────────────────────────────────────────────────────────────
sys.exit(_REPORTER.report())
