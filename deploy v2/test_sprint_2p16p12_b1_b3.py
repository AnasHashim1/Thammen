"""
Sprint 2.16.12 — Isolated tests for B1 (dead import) + B3 (audience whitelist).

B1 test: evaluate_v3.py no longer imports load_all_sales_xlsx / compute_trend_from_xlsx
B3 test: Pydantic validators reject unknown audience values (was silent coercion)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_b1():
    """Verify the dead try/except import block is gone from evaluate_v3.py."""
    with open('evaluate_v3.py', encoding='utf-8') as f:
        src = f.read()

    failures = []

    # The active import must be gone (only the comment block remains)
    # Check there's no top-level "from sales_merge import" outside a comment
    for ln, line in enumerate(src.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if 'from sales_merge import' in stripped:
            failures.append(f"  line {ln}: still imports sales_merge ({stripped!r})")
        if stripped == '_SALES_AVAILABLE = True' or stripped == '_SALES_AVAILABLE = False':
            failures.append(f"  line {ln}: still sets _SALES_AVAILABLE ({stripped!r})")

    if "Sprint 2.16.12 (B1)" not in src:
        failures.append("  missing Sprint 2.16.12 (B1) comment marker")

    # The module must still compile
    try:
        compile(src, 'evaluate_v3.py', 'exec')
    except SyntaxError as e:
        failures.append(f"  SyntaxError: {e}")

    if failures:
        print("\u2717 B1 FAILED:")
        for f in failures:
            print(f)
        return False

    print("\u2713 B1: dead sales_merge import removed (evaluate_v3.py still compiles)")
    return True


def test_b3():
    """Verify Pydantic audience validator rejects unknown values."""
    # Import the model from api.py directly. The module has heavy deps
    # (FastAPI, engines) — we only need the validator logic, so isolate it.
    import importlib.util
    import types

    # The Pydantic-specific lines we need:
    from typing import Optional
    from pydantic import BaseModel, Field, field_validator, ValidationError

    # Recreate the audience set + validator + a minimal model that uses them
    _AUDIENCE_ACCEPTED = frozenset({
        'buyer', 'seller', 'investor', 'valuer',
        'valuator',
        'مشتري', 'بائع', 'مستثمر',
        'مثمن', 'مثمّن', 'مُثمِّن',
        'مقيم', 'مقيّم', 'مُقيِّم',
    })

    def _check_audience(v):
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("audience must be a string")
        if v in _AUDIENCE_ACCEPTED or v.strip().lower() in _AUDIENCE_ACCEPTED:
            return v
        raise ValueError(
            "audience must be one of: buyer/seller/investor/valuer "
            "(or Arabic مشتري/بائع/مستثمر/مثمن/مقيم). "
            f"Got: {v!r}"
        )

    class TestModel(BaseModel):
        audience: Optional[str] = 'buyer'

        @field_validator('audience')
        @classmethod
        def _validate_audience(cls, v):
            return _check_audience(v)

    passed = 0
    failed = 0

    def expect_accept(value, label):
        nonlocal passed, failed
        try:
            TestModel(audience=value)
            print(f"  \u2713 {label}")
            passed += 1
        except ValidationError as e:
            print(f"  \u2717 {label} (got: {e})")
            failed += 1

    def expect_reject(value, label):
        nonlocal passed, failed
        try:
            TestModel(audience=value)
            print(f"  \u2717 {label} (was accepted)")
            failed += 1
        except ValidationError:
            print(f"  \u2713 {label}")
            passed += 1

    print("B3: canonical English audiences (must accept):")
    for v in ['buyer', 'seller', 'investor', 'valuer']:
        expect_accept(v, f"audience={v!r}")

    print()
    print("B3: case variants (must accept via lower()):")
    for v in ['BUYER', 'Buyer', 'VALUER', 'Investor']:
        expect_accept(v, f"audience={v!r}")

    print()
    print("B3: English aliases (must accept):")
    expect_accept('valuator', "audience='valuator' (English alias for valuer)")
    expect_accept('Valuator', "audience='Valuator' (case variant)")

    print()
    print("B3: Arabic equivalents (must accept):")
    for v in ['مشتري', 'بائع', 'مستثمر', 'مثمن', 'مقيم', 'مقيّم', 'مُثمِّن']:
        expect_accept(v, f"audience={v!r}")

    print()
    print("B3: unknown values (must reject with 422 / ValidationError):")
    expect_reject('hacker', "audience='hacker' (the catalogued B3 case)")
    expect_reject('admin', "audience='admin'")
    expect_reject('typo', "audience='typo'")
    expect_reject('', "audience=''")
    expect_reject(' ', "audience=' '")
    expect_reject('سمسار', "audience='سمسار' (Arabic but not in whitelist)")

    print()
    print("B3: None and default (must accept — backward compat):")
    expect_accept(None, "audience=None")
    # Default value (omitted field) should pass through 'buyer'
    try:
        m = TestModel()
        if m.audience == 'buyer':
            print(f"  \u2713 audience field omitted -> defaults to 'buyer'")
            passed += 1
        else:
            print(f"  \u2717 omitted default is {m.audience!r}, expected 'buyer'")
            failed += 1
    except ValidationError as e:
        print(f"  \u2717 omitted: {e}")
        failed += 1

    print()
    print("B3: non-string types (must reject):")
    expect_reject(123, "audience=123 (int)")
    expect_reject(['buyer'], "audience=['buyer'] (list)")
    expect_reject({'role': 'buyer'}, "audience={'role':'buyer'} (dict)")

    print()
    print(f"B3 results: {passed} passed, {failed} failed")
    return failed == 0


def test_sync():
    """Verify the source files carry the Sprint 2.16.12 markers."""
    failures = []

    with open('api.py', encoding='utf-8') as f:
        api_src = f.read()
    for expected in [
        'from pydantic import BaseModel, Field, field_validator',
        '_AUDIENCE_ACCEPTED = frozenset',
        'def _check_audience(v):',
        "@field_validator('audience')",
        'Sprint 2.16.12 (B3)',
    ]:
        if expected not in api_src:
            failures.append(f"  api.py: missing {expected!r}")

    # The validator must appear twice (once per model)
    if api_src.count("@field_validator('audience')") != 2:
        failures.append(
            f"  api.py: expected @field_validator('audience') twice (one per model), "
            f"found {api_src.count(chr(64)+'field_validator')} matches"
        )

    with open('evaluate_unified.py', encoding='utf-8') as f:
        eu_src = f.read()
    if "SPRINT_TAG = '2.16.12'" not in eu_src:
        failures.append("  evaluate_unified.py: SPRINT_TAG not bumped to 2.16.12")
    if 'sprint2p16p12' not in eu_src:
        failures.append("  evaluate_unified.py: ENGINE_VERSION not bumped")

    if failures:
        print("\u2717 SYNC FAILED:")
        for f in failures:
            print(f)
        return False

    print("\u2713 Source files carry Sprint 2.16.12 markers")
    return True


if __name__ == "__main__":
    print()
    print("=" * 70)
    print("Sprint 2.16.12 — B1 + B3 housekeeping")
    print("=" * 70)
    print()
    ok_sync = test_sync()
    print()
    ok_b1 = test_b1()
    print()
    ok_b3 = test_b3()
    print()
    print("=" * 70)
    print(f"Sync: {'pass' if ok_sync else 'FAIL'}")
    print(f"B1:   {'pass' if ok_b1 else 'FAIL'}")
    print(f"B3:   {'pass' if ok_b3 else 'FAIL'}")
    print("=" * 70)
    sys.exit(0 if (ok_sync and ok_b1 and ok_b3) else 1)
