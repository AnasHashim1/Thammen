#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isolated logic tests — Sprint 2.22.0a.20 (A7): rics_compliant honest status label.

Display/label ONLY. The `rics_compliant` BOOL and every valuation value are
untouched; this sprint only ADDS a neutral companion status string
(`rics_compliant_status_ar`/`_en`) next to the bool wherever it surfaces in the
JSON, so `false` reads "review pending (Stage 5)" rather than "non-compliant".

Per Rule #40 / E14 these tests import and exercise the PRODUCTION functions
(`material_uncertainty.rics_compliant_status_fields` +
`evaluate_unified._enrich_material_uncertainty`), not replicas.

Run:  PYTHONIOENCODING=utf-8 python test_sprint_2_22_0a20.py
"""
import sys

from material_uncertainty import (
    rics_compliant_status_fields,
    RICS_COMPLIANT_STATUS_PENDING_AR,
    RICS_COMPLIANT_STATUS_PENDING_EN,
)

# Signed copy (Claude.ai, Sprint A7) — asserted verbatim so a future edit that
# drifts the wording fails loudly.
SIGNED_AR = 'بانتظار مراجعة مُقيِّم مُرخّص (المرحلة الخامسة)'
SIGNED_EN = 'Pending licensed-valuer review (Stage 5)'

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


# ── 1. Helper: pending (False) case returns both signed keys ──
def test_false_returns_both_keys():
    out = rics_compliant_status_fields(False)
    check('false → exactly the 2 status keys',
          set(out.keys()) == {'rics_compliant_status_ar', 'rics_compliant_status_en'})
    check('false → ar == signed copy', out.get('rics_compliant_status_ar') == SIGNED_AR)
    check('false → en == signed copy', out.get('rics_compliant_status_en') == SIGNED_EN)


# ── 2. Helper: compliant (True) → empty (no unsigned "compliant" string) ──
def test_true_returns_empty():
    check('true → {} (no status emitted)', rics_compliant_status_fields(True) == {})


# ── 3. Helper: None / falsy → pending (fail-safe to disclosure) ──
def test_none_is_pending():
    out = rics_compliant_status_fields(None)
    check('None → pending (fail-safe discloses)',
          out.get('rics_compliant_status_ar') == SIGNED_AR)


# ── 4. Module constants ARE the signed verbatim copy ──
def test_constants_verbatim():
    check('AR constant verbatim', RICS_COMPLIANT_STATUS_PENDING_AR == SIGNED_AR)
    check('EN constant verbatim', RICS_COMPLIANT_STATUS_PENDING_EN == SIGNED_EN)


# ── 5. AR copy is bidi-safe: no ASCII letters → no LRM wrapping needed ──
def test_ar_no_latin():
    has_latin = any(('a' <= c <= 'z') or ('A' <= c <= 'Z') for c in SIGNED_AR)
    check('AR status has zero Latin letters (no LRM/bidi risk)', not has_latin)


# ── 6. _enrich_material_uncertainty (fast-path root): False → status added,
#       bool + level preserved (zero value drift) ──
def test_enrich_false_adds_status_preserves_bool():
    from evaluate_unified import _enrich_material_uncertainty
    src = {'level': 'high', 'banner_ar': 'x', 'rics_compliant': False}
    out = _enrich_material_uncertainty(src)
    check('enrich(False) → status_ar present', out.get('rics_compliant_status_ar') == SIGNED_AR)
    check('enrich(False) → status_en present', out.get('rics_compliant_status_en') == SIGNED_EN)
    check('enrich(False) → bool UNCHANGED (False)', out.get('rics_compliant') is False)
    check('enrich(False) → level UNCHANGED', out.get('level') == 'high')
    check('enrich does not mutate the input dict',
          'rics_compliant_status_ar' not in src)


# ── 7. _enrich: True → NO status, bool preserved ──
def test_enrich_true_no_status():
    from evaluate_unified import _enrich_material_uncertainty
    out = _enrich_material_uncertainty({'level': 'low', 'rics_compliant': True})
    check('enrich(True) → no status_ar', 'rics_compliant_status_ar' not in out)
    check('enrich(True) → bool UNCHANGED (True)', out.get('rics_compliant') is True)


# ── 8. _enrich: setdefault never clobbers a caller-set status ──
def test_enrich_no_clobber():
    from evaluate_unified import _enrich_material_uncertainty
    out = _enrich_material_uncertainty(
        {'rics_compliant': False, 'rics_compliant_status_ar': 'CALLER'})
    check('enrich preserves caller-set status_ar',
          out.get('rics_compliant_status_ar') == 'CALLER')


# ── 9. Brief content (production output_briefs): False → section carries status ──
def test_buyer_brief_section_carries_status():
    from output_briefs import generate_brief
    evaluation = {
        'address': 'PIN 0/0/0', 'asset_type': 'standalone_villa',
        'plot_area_m2': 500, 'gis_district_aname': 'اختبار',
        'valuation': {'amount': 2_400_000, 'method': 'comparison_bracket'},
    }
    uncertainty = {
        'level': 'moderate', 'banner_ar': 'x', 'banner_en': 'x',
        'factors': [], 'known_unknowns': [], 'recommendations': [],
        'rics_compliant': False,
    }
    try:
        brief = generate_brief(evaluation=evaluation, audience='buyer',
                               uncertainty=uncertainty)
        secs = brief.get('sections', [])
        mu = next((s for s in secs if s.get('id') == 'material_uncertainty'), None)
        content = (mu or {}).get('content', {})
        check('buyer brief MU section carries status_ar',
              content.get('rics_compliant_status_ar') == SIGNED_AR)
        check('buyer brief MU section keeps bool False',
              content.get('rics_compliant') is False)
    except Exception as e:  # production shape changed — surface, don't silently pass
        check(f'buyer brief generated without error ({e!r})', False)


# ── 10. Brief content: True → section omits the pending status ──
def test_valuer_brief_true_omits_status():
    from output_briefs import generate_brief
    evaluation = {
        'address': 'PIN 0/0/0', 'asset_type': 'apartment_building',
        'plot_area_m2': 1000, 'gis_district_aname': 'لوسيل',
        'valuation': {'amount': 5_000_000, 'method': 'hybrid_t2'},
    }
    uncertainty = {
        'level': 'moderate', 'banner_ar': 'x', 'banner_en': 'x',
        'factors': [], 'known_unknowns': [], 'recommendations': [],
        'rics_compliant': True,
    }
    try:
        brief = generate_brief(evaluation=evaluation, audience='valuer',
                               uncertainty=uncertainty)
        secs = brief.get('sections', [])
        mu = next((s for s in secs if s.get('id') == 'material_uncertainty'), None)
        content = (mu or {}).get('content', {})
        check('valuer brief MU section omits status when compliant',
              'rics_compliant_status_ar' not in content)
        check('valuer brief MU section keeps bool True',
              content.get('rics_compliant') is True)
    except Exception as e:
        check(f'valuer brief generated without error ({e!r})', False)


def main():
    for t in (
        test_false_returns_both_keys,
        test_true_returns_empty,
        test_none_is_pending,
        test_constants_verbatim,
        test_ar_no_latin,
        test_enrich_false_adds_status_preserves_bool,
        test_enrich_true_no_status,
        test_enrich_no_clobber,
        test_buyer_brief_section_carries_status,
        test_valuer_brief_true_omits_status,
    ):
        t()
    print(f'\n{_passed} passed, {_failed} failed')
    sys.exit(1 if _failed else 0)


if __name__ == '__main__':
    main()
