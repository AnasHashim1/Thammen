"""
Shared test helpers — established in Sprint 2.22.0a/10, intended for all
sub-sprint test files going forward.

Canonical `_check(cond, name, detail="")` signature established by /2-/5
conventions. Sprint 2.22.0a/7 + /8 (Pattern B) drift resolved via this
module — all isolated test files now share one helper.

Usage:

    from _test_helpers import Reporter, set_stdout_utf8
    set_stdout_utf8()
    R = Reporter()
    _check = R.check

    _check(condition, 'test name', 'optional detail when failing')
    ...
    sys.exit(R.report())   # prints summary + returns 0/1 exit code

Naming rationale (Anas Q1.5 decision 2026-05-26):
  - Infrastructure modules use descriptive purpose names
    (evaluate_unified.py, output_briefs.py, material_uncertainty.py,
    verification_url.py, refusal_templates.py). Sprint nomenclature is
    reserved for test files + CHANGELOGs, NOT infrastructure modules.
  - Future-Sprint adoption: 2.22.0b / 2.22.y authors import naturally
    without "wrong-Sprint" coupling or duplicate helper modules.
"""
from __future__ import annotations

import sys
from typing import Any


def set_stdout_utf8() -> None:
    """Reconfigure stdout to UTF-8 for Arabic + emoji output.

    Required for Sprint 2.21.2+ test files containing Arabic strings
    + emoji icons (per CLAUDE.md regression discipline). Silent no-op
    on platforms where stdout.reconfigure() is unavailable.
    """
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


class Reporter:
    """Test assertion counter + summary reporter.

    Replaces the per-file module-level `_passed`/`_failed` globals (Pattern A,
    /2-/5) and `PASS`/`FAIL` globals (Pattern B, /7-/8) with a single
    instance-scoped counter. Eliminates cross-test global state pollution
    + makes nested test scenarios safe.

    Canonical assertion signature: `R.check(condition, name, detail='')`
    — same order as Pattern A (`_check(cond, name, detail)`). Pattern B
    files (/7 + /8) refactored to this order in /10.

    Exit code contract via `report()`:
      - 0 if all assertions passed
      - 1 if any failed (prints FAILED ASSERTIONS list to stdout)
    """

    def __init__(self, name: str = '') -> None:
        self.name = name
        self.passed = 0
        self.failed = 0
        self._failed_names: list[str] = []

    def check(self, condition: Any, name: str, detail: str = '') -> None:
        """Record one assertion. Prints PASS / FAIL line immediately."""
        if condition:
            self.passed += 1
            print(f'  PASS  {name}')
        else:
            self.failed += 1
            self._failed_names.append(name)
            tail = f'  {detail}' if detail else ''
            print(f'  FAIL  {name}{tail}')

    def report(self) -> int:
        """Print summary block + return exit code (0 if all passed).

        Output format is canonical across Sprint 2.22.0a test files; the
        Sprint suite aggregator (`run_sprint_2p22p0a_suite.py`) parses
        the `"PASSED: X/X"` line to verify per-file counts against
        `PER_FILE_EXPECTED`.
        """
        total = self.passed + self.failed
        print()
        print('=' * 60)
        print(f'  PASSED: {self.passed}/{total}')
        print(f'  FAILED: {self.failed}/{total}')
        print('=' * 60)
        if self.failed:
            print()
            print('FAILED ASSERTIONS:')
            for n in self._failed_names:
                print(f'  - {n}')
            return 1
        return 0
