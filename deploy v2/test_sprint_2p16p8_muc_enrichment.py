"""
Sprint 2.16.8 — Isolated tests for MUC enrichment + tower UX backend.

Covers:
- _enrich_material_uncertainty helper (4 unit tests)
- Sync check: confirms all 4 _build_fast_* response builders in
  evaluate_unified.py wrap material_uncertainty through the helper.

Run from project root: python test_sprint_2p16p8_muc_enrichment.py
"""
import sys
import re
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def extract_helper():
    """Extract _enrich_material_uncertainty from evaluate_unified.py."""
    with open('evaluate_unified.py', encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'(def _enrich_material_uncertainty.*?)(?=\n\ndef )', src, re.DOTALL)
    if not m:
        return None, src
    ns = {}
    exec(m.group(1), ns)
    return ns['_enrich_material_uncertainty'], src


def verify_wraps(src):
    """Confirm all 4 _build_fast_* + _build_out_of_scope functions wrap
    their material_uncertainty dict through _enrich_material_uncertainty.
    """
    builders = [
        '_build_fast_insufficient_data_response',
        '_build_fast_listing_only_response',
        '_build_fast_income_only_response',
        '_build_out_of_scope_response',
    ]
    failures = []
    for name in builders:
        m = re.search(rf'def {re.escape(name)}\b.*?(?=\n\ndef |\Z)', src, re.DOTALL)
        if not m:
            failures.append(f"  - function {name} not found")
            continue
        body = m.group(0)
        if "'material_uncertainty': _enrich_material_uncertainty({" not in body:
            failures.append(f"  - {name}: material_uncertainty NOT wrapped through helper")

    if failures:
        print("\u2717 wrap verification FAILED:")
        for f in failures:
            print(f)
        return False
    print(f"\u2713 all 4 fast-path builders wrap material_uncertainty through helper")
    return True


def verify_version_bump(src):
    """Confirm engine version constants exist in sprint-tag format.

    Sprint 2.19.1: relaxed from the stale literal '2.16.8' pin (which fails by
    design once the version advances) to a version-agnostic format check.
    """
    import re as _re
    if not _re.search(r"SPRINT_TAG\s*=\s*'\d+\.\d+", src):
        print("\u2717 SPRINT_TAG missing or not in sprint-tag format")
        return False
    if not _re.search(r"ENGINE_VERSION\s*=\s*'thammen-sprint\d+p\d+", src):
        print("\u2717 ENGINE_VERSION missing or not in sprint format")
        return False
    print("\u2713 version constants present in sprint format")
    return True


def test_helper(helper):
    """Unit tests on the extracted helper."""
    passed = 0
    failed = 0

    # T1: tower-style mu gets all 4 MUC fields injected
    tower_mu = {
        'level': 'high',
        'banner_ar': 'tower banner test',
        'known_unknowns_ar': ['x'],
        'rics_compliant': False,
    }
    out = helper(tower_mu)
    added = set(out.keys()) - set(tower_mu.keys())
    expected_added = {'muc_clause_ar', 'muc_clause_en', 'muc_basis_ar', 'muc_review_recommendation_ar'}
    if expected_added.issubset(added):
        print("  \u2713 T1: 4 MUC fields injected on tower-style mu")
        passed += 1
    else:
        print(f"  \u2717 T1: missing fields {expected_added - added}")
        failed += 1

    # T2: original keys preserved
    if out['level'] == 'high' and out['banner_ar'] == 'tower banner test':
        print("  \u2713 T2: original mu keys preserved")
        passed += 1
    else:
        print("  \u2717 T2: original mu keys lost")
        failed += 1

    # T3: muc_clause_ar carries a RICS citation
    # Sprint 2.22.0a/9 \u2014 relaxed from brittle 'VPS 5' literal pin (same anti-
    # pattern Sprint 2.19.1 corrected across 4 other Sprint test files,
    # Operational_Rules #36). The 2024-edition citation is "VPGA 10 + VPS 3";
    # 'RICS' substring covers any future edition rename too.
    if 'RICS' in (out.get('muc_clause_ar') or ''):
        print("  \u2713 T3: muc_clause_ar contains RICS citation")
        passed += 1
    else:
        print("  \u2717 T3: muc_clause_ar missing RICS citation")
        failed += 1

    # T4: caller-set muc_clause_ar NOT overwritten
    prior = {'level': 'high', 'muc_clause_ar': 'CALLER-WROTE'}
    out2 = helper(prior)
    if out2.get('muc_clause_ar') == 'CALLER-WROTE':
        print("  \u2713 T4: existing muc_clause_ar preserved (no overwrite)")
        passed += 1
    else:
        print("  \u2717 T4: existing muc_clause_ar was overwritten")
        failed += 1

    # T5: input dict not mutated
    orig = {'level': 'high'}
    helper(orig)
    if 'muc_clause_ar' not in orig:
        print("  \u2713 T5: caller's dict not mutated")
        passed += 1
    else:
        print("  \u2717 T5: caller's dict was mutated")
        failed += 1

    # T6: exception safety (import failure)
    import builtins
    _real = builtins.__import__
    def fail_import(name, *a, **k):
        if name == 'material_uncertainty':
            raise ImportError("simulated")
        return _real(name, *a, **k)
    builtins.__import__ = fail_import
    try:
        out6 = helper({'level': 'x'})
    finally:
        builtins.__import__ = _real
    if out6 == {'level': 'x'}:
        print("  \u2713 T6: exception safety — returns input on ImportError")
        passed += 1
    else:
        print(f"  \u2717 T6: returned {out6} instead of input")
        failed += 1

    return passed, failed


if __name__ == "__main__":
    print()
    helper, src = extract_helper()
    if helper is None:
        print("\u2717 _enrich_material_uncertainty not found in evaluate_unified.py")
        sys.exit(1)
    print("\u2713 _enrich_material_uncertainty extracted from evaluate_unified.py")

    ok1 = verify_version_bump(src)
    ok2 = verify_wraps(src)

    print()
    print("=" * 70)
    print("Helper unit tests")
    print("=" * 70)
    p, f = test_helper(helper)
    print()
    print(f"Results: {p} passed, {f} failed (helper)")
    print(f"Sync checks: version={'pass' if ok1 else 'FAIL'}, wraps={'pass' if ok2 else 'FAIL'}")

    sys.exit(0 if (f == 0 and ok1 and ok2) else 1)
